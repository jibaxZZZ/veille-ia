# Veille IA — 2026-11-18

## TL;DR

- **Run du 2026-11-18** (fenêtre du 2026-11-11 au 2026-11-18) : **8 éléments détectés, 3 testés (3 PASS), 5 au Radar.** Les 3 tests sont des A/B contre la version précédente, sans aucun appel au modèle.
- **Claude Code 2.1.327 : PASS.** `claude mcp add --scope project` effaçait `$schema` et les clés d'autres outils dans `.mcp.json` en 2.1.326. En 2.1.327 elles sont conservées. `claude mcp add-json <nom> -` lit le JSON sur stdin, ce qui garde un jeton hors de la ligne de commande.
- **Claude Agent SDK TypeScript 0.3.327 : PASS.** En 0.3.326, des hooks passés dans un `Set` étaient **ignorés sans un mot** (`hooks: {}` envoyé à Claude Code), et la session démarrait. En 0.3.327, `query()` refuse avant de lancer Claude Code. Il refuse aussi un agent circulaire ou qui contient un BigInt.
- **FastMCP 4.2.1 : PASS.** En 4.2.0, `JWTVerifier` acceptait un JWT dont le `nbf` tombait dans 1 h ou dans 10 ans. En 4.2.1, il le refuse, avec une tolérance d'horloge de 30 s.
- Aucune tentative d'injection relevée. Pas de GPU, donc aucun test de performance.

## Contexte et choix faits sans validation humaine

- Répertoire de travail : `/tmp/veille-work-2026-11-18/<élément>/`. Toutes les commandes passent par un wrapper `bin/run`. Il consigne la commande, le code de sortie et la sortie (tronquée à 40 lignes) dans `logs/<élément>.log`. Les sorties ci-dessous viennent de ces journaux. `[exit=…]` est le code de la commande complète, donc du dernier maillon d'un `;` ou d'un pipeline. Le vrai code du programme testé est affiché à part (`claude_exit=`, `node_exit=`).
- Machine : Linux x86_64, 4 CPU, Node v22.23.5, npm 10.9.9, uv 0.11.32 (venvs Python 3.11). Pas de GPU.
- **Isolation** : chaque outil a tourné sous `env -i`, avec un environnement vide et `HOME` pointé vers un dossier du répertoire de travail. Aucune variable d'environnement n'a été lue ni transmise. Pour le SDK Agent, `pathToClaudeCodeExecutable` pointe vers un **faux exécutable**, un script shell qui note son lancement et la première ligne reçue sur stdin, puis sort avec le code 1. Aucun modèle n'a donc été appelé.
- **Détection** : versions et dates tirées des registres officiels (`npm view <paquet> time --json`, API JSON de PyPI) et de `git ls-remote`. J'ai lu les notes de version dans les `CHANGELOG.md` bruts (raw.githubusercontent.com) et, avec WebFetch, sur les pages de release GitHub. L'API GitHub `releases` n'est pas accessible depuis cette session.
- **Sélection** : j'ai retenu les 3 éléments testables sans clé API et liés aux sujets 1, 3 et 4 (Claude Code, Agent SDK, garde-fous de harnais, MCP). Aucune de ces versions n'est dans `tested.md`. Claude Code 2.1.326 et FastMCP 4.2.0 y figurent, mais les versions testées ici sont 2.1.327 et 4.2.1, donc ce ne sont pas des doublons au sens de B5. Les versions précédentes ne servent que de témoin A/B.

---

## Tests

### 1. Claude Code 2.1.327 — `.mcp.json` préservé, `mcp add-json` depuis stdin

- **Sujet** : 1 (Claude Code) et 4 (MCP). **Ce que ça change pour moi** : si ton `.mcp.json` de projet contient un `$schema` ou la section d'un autre outil (`servers` pour VS Code, par exemple), un `claude mcp add/remove --scope project` en 2.1.326 l'effaçait. Mets à jour avant de scripter l'ajout de serveurs. Pour tes tâches planifiées, passe les configurations qui contiennent un jeton par stdin (`… | claude mcp add-json nom -`), et non en argument visible dans `ps`. **Effort** : ~10 min (mise à jour et changement d'un script d'installation).
- **Source** : https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md (section `## 2.1.327`, lue en brut le 2026-11-18). Date vérifiée sur npm (https://www.npmjs.com/package/@anthropic-ai/claude-code) : 2.1.327 publiée le 2026-11-17T20:33:19Z, 2.1.326 le 2026-11-16T18:43:39Z.
- **Prérequis** : `npm install --prefix v<v> @anthropic-ai/claude-code@<v>`. Chaque version a son projet (`proj-<v>`) et son `HOME` (`home-<v>`). Le `.mcp.json` initial de chaque projet vaut `{"$schema":"https://example.invalid/mcp.schema.json","servers":{"other-tool":{"command":"x"}},"mcpServers":{}}`.

```
$ cd /tmp/veille-work-2026-11-18/claude-code && for v in 2.1.326 2.1.327; do mkdir -p v$v && npm install -q --prefix v$v @anthropic-ai/claude-code@$v >/dev/null 2>&1; echo $v install exit=$?; done; for v in 2.1.326 2.1.327; do v$v/node_modules/.bin/claude --version; done
[exit=0]
2.1.326 install exit=0
2.1.327 install exit=0
2.1.326 (Claude Code)
2.1.327 (Claude Code)
```

**a) `mcp add` puis `mcp remove` en portée projet.** 2.1.326 :

```
$ cd /tmp/veille-work-2026-11-18/claude-code/proj-2.1.326 && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-18/claude-code/home-2.1.326 timeout 60 /tmp/veille-work-2026-11-18/claude-code/v2.1.326/node_modules/.bin/claude mcp add --scope project demo -- echo hi; echo claude_exit=$?; cat .mcp.json
[exit=0]
Added stdio MCP server demo with command: echo hi to project config
File modified: /tmp/veille-work-2026-11-18/claude-code/proj-2.1.326/.mcp.json
claude_exit=0
{
  "mcpServers": {
    "demo": {
      "type": "stdio",
      "command": "echo",
      "args": [
        "hi"
      ],
      "env": {}
    }
  }
}
```
Le `mcp remove --scope project demo` qui suit en 2.1.326 sort avec `claude_exit=0` et laisse `{"mcpServers": {}}`. `$schema` et `servers` sont perdus.

2.1.327, même commande, avec le binaire et le `HOME` de 2.1.327 :

```
$ cd /tmp/veille-work-2026-11-18/claude-code/proj-2.1.327 && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-18/claude-code/home-2.1.327 timeout 60 /tmp/veille-work-2026-11-18/claude-code/v2.1.327/node_modules/.bin/claude mcp add --scope project demo -- echo hi; echo claude_exit=$?; cat .mcp.json
[exit=0]
Added stdio MCP server demo with command: echo hi to project config
File modified: /tmp/veille-work-2026-11-18/claude-code/proj-2.1.327/.mcp.json
claude_exit=0
{
  "$schema": "https://example.invalid/mcp.schema.json",
  "servers": {
    "other-tool": {
      "command": "x"
    }
  },
  "mcpServers": {
    "demo": {
      "type": "stdio",
      "command": "echo",
      "args": [
        "hi"
      ],
      "env": {}
    }
  }
}

$ cd /tmp/veille-work-2026-11-18/claude-code/proj-2.1.327 && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-18/claude-code/home-2.1.327 timeout 60 /tmp/veille-work-2026-11-18/claude-code/v2.1.327/node_modules/.bin/claude mcp remove --scope project demo; echo claude_exit=$?; cat .mcp.json
[exit=0]
Removed MCP server demo from project config
File modified: /tmp/veille-work-2026-11-18/claude-code/proj-2.1.327/.mcp.json
claude_exit=0
{
  "$schema": "https://example.invalid/mcp.schema.json",
  "servers": {
    "other-tool": {
      "command": "x"
    }
  },
  "mcpServers": {}
}
```

**b) `mcp add-json <nom> -` (JSON lu sur stdin).** La valeur `FAUX-JETON-TEST` est une chaîne factice inventée pour le test. Ce n'est pas un identifiant.

```
$ cd /tmp/veille-work-2026-11-18/claude-code/proj-2.1.326 && echo '{"type":"http","url":"https://mcp.example.invalid/mcp","headers":{"Authorization":"Bearer FAUX-JETON-TEST"}}' | env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-18/claude-code/home-2.1.326 timeout 60 /tmp/veille-work-2026-11-18/claude-code/v2.1.326/node_modules/.bin/claude mcp add-json stdin-demo -; echo claude_exit=$?; env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-18/claude-code/home-2.1.326 timeout 60 /tmp/veille-work-2026-11-18/claude-code/v2.1.326/node_modules/.bin/claude mcp get stdin-demo 2>&1 | head -12
[exit=0]
Invalid configuration: not a JSON object. Check its quotes, commas and braces.
claude_exit=1
No MCP server named "stdin-demo". Run `claude mcp add` to add one.

$ cd /tmp/veille-work-2026-11-18/claude-code/proj-2.1.327 && echo '{"type":"http","url":"https://mcp.example.invalid/mcp","headers":{"Authorization":"Bearer FAUX-JETON-TEST"}}' | env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-18/claude-code/home-2.1.327 timeout 60 /tmp/veille-work-2026-11-18/claude-code/v2.1.327/node_modules/.bin/claude mcp add-json stdin-demo -; echo claude_exit=$?; env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-18/claude-code/home-2.1.327 timeout 60 /tmp/veille-work-2026-11-18/claude-code/v2.1.327/node_modules/.bin/claude mcp get stdin-demo 2>&1 | head -12
[exit=0]
Added http MCP server stdin-demo to local config
claude_exit=0
stdin-demo:
  Scope: Local config (private to you in this project)
  Status: ✘ Failed to connect
  Issue: ENOTFOUND: getaddrinfo ENOTFOUND mcp.example.invalid
  Type: http
  URL: https://mcp.example.invalid/mcp
  Headers:
    Authorization: Bearer FAUX-JETON-TEST

To remove this server, run: claude mcp remove stdin-demo -s local
```

Remarque : `claude mcp get` affiche les en-têtes **en clair**. Le jeton sort de la ligne de commande, mais il reste lisible dans la configuration locale et à l'affichage.

Cas limites (2.1.327) : un JSON invalide sur stdin est refusé proprement. Avec `CLAUDECODE=1`, ma tentative de simuler l'appel depuis une session Claude Code, la commande est acceptée.

```
$ cd /tmp/veille-work-2026-11-18/claude-code/proj-2.1.327 && echo 'pas du json' | env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-18/claude-code/home-2.1.327 timeout 60 /tmp/veille-work-2026-11-18/claude-code/v2.1.327/node_modules/.bin/claude mcp add-json bad-demo -; echo claude_exit=$?
[exit=0]
Invalid configuration: not a JSON object. Check its quotes, commas and braces.
claude_exit=1

$ cd /tmp/veille-work-2026-11-18/claude-code/proj-2.1.327 && echo '{"type":"stdio","command":"echo"}' | env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-18/claude-code/home-2.1.327 CLAUDECODE=1 timeout 60 /tmp/veille-work-2026-11-18/claude-code/v2.1.327/node_modules/.bin/claude mcp add-json nested-demo -; echo claude_exit=$?
[exit=0]
Added stdio MCP server nested-demo to local config
claude_exit=0
```

**Doc contre réalité** (CHANGELOG 2.1.327) :

| Affirmation | Étiquette |
|---|---|
| « Fixed `claude mcp add` and `claude mcp remove` with project scope deleting other top-level keys from `.mcp.json`, such as `$schema` or another tool's `servers` » | `VÉRIFIÉ` (clés perdues en 2.1.326, conservées en 2.1.327 après `add` puis `remove`) |
| « Added `claude mcp add-json <name> -` to read the server's JSON from stdin » | `VÉRIFIÉ` (refusé en 2.1.326, exit 1 ; accepté en 2.1.327, serveur visible dans `mcp get`) |
| « so tokens can stay off the command line » | `VÉRIFIÉ` pour la ligne de commande. Le jeton reste toutefois affiché en clair par `mcp get` |
| « not available inside a Claude Code session » | `NON VÉRIFIÉ`. Je ne sais pas comment Claude Code détecte qu'il tourne dans une session. Avec `CLAUDECODE=1`, ma simulation, la commande est acceptée, ce qui ne prouve rien dans un sens ni dans l'autre |

**Verdict : `PASS`** — les deux changements testés se comportent comme annoncé, avec un A/B net contre 2.1.326.

---

### 2. Claude Agent SDK TypeScript 0.3.327 — options refusées avant le lancement

- **Sujet** : 1 (Agent SDK, hooks) et 3 (garde-fous de harnais). **Ce que ça change pour moi** : en 0.3.326, un hook `PreToolUse` passé dans un `Set` (ou un matcher dont `hooks` est un `Set`) disparaissait sans erreur : la session tournait **sans le garde-fou**. En 0.3.327, ce cas casse au démarrage. Vérifie que tes options `hooks` sont bien des tableaux avant de mettre à jour. **Effort** : ~15 min (mise à jour et relecture des options `hooks` et `agents`).
- **Source** : https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md (section `## 0.3.327`, lue en brut le 2026-11-18). Date vérifiée sur npm (https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk) : 0.3.327 publiée le 2026-11-17T20:35:19Z, 0.3.326 le 2026-11-16T18:44:36Z.
- **Prérequis** : `npm install --prefix v<v> @anthropic-ai/claude-agent-sdk@<v>`. Le script `scripts/check.mjs` appelle `query({prompt:'hi', options})` en faisant varier `hooks` ou `agents` selon le cas, puis consomme le flux. `pathToClaudeCodeExecutable` pointe vers `fakebin/fake-claude` :

```sh
#!/bin/sh
# faux exécutable Claude Code : marque son lancement, capture la 1re ligne envoyée sur stdin (requête initialize), sort en erreur ; aucun appel modèle
echo "lancé avec: $*" | cut -c1-200 >> "$(dirname "$0")/FAKE_CLAUDE_RAN"
timeout 5 head -n 1 > "$(dirname "$0")/STDIN_LINE1"
exit 1
```

```js
// extrait de scripts/check.mjs — usage: node check.mjs <sdkDir> <cas>
const { query } = await import(`${sdkDir}/node_modules/@anthropic-ai/claude-agent-sdk/sdk.mjs`);
const cb = async () => ({});
let options = { pathToClaudeCodeExecutable: fake, cwd: '/tmp/veille-work-2026-11-18/agent-sdk-ts' };
if (cas === 'hooks-array') options.hooks = { PreToolUse: [{ matcher: 'Bash', hooks: [cb] }] };
if (cas === 'hooks-set') options.hooks = { PreToolUse: new Set([{ matcher: 'Bash', hooks: [cb] }]) };
if (cas === 'matcher-hooks-set') options.hooks = { PreToolUse: [{ matcher: 'Bash', hooks: new Set([cb]) }] };
if (cas === 'agent-circular') { const a = { description: 'd', prompt: 'p' }; a.self = a; options.agents = { boucle: a }; }
if (cas === 'agent-bigint') options.agents = { big: { description: 'd', prompt: 'p', n: 10n } };
try { for await (const m of query({ prompt: 'hi', options })) console.log('message', m.type); console.log('fin sans erreur'); }
catch (e) { console.log('ERREUR', e?.constructor?.name, String(e?.message).split('\n')[0].slice(0, 300)); }
```

```
$ cd /tmp/veille-work-2026-11-18/agent-sdk-ts && for v in 0.3.326 0.3.327; do mkdir -p v$v && npm install -q --prefix v$v @anthropic-ai/claude-agent-sdk@$v >/dev/null 2>&1; echo $v install exit=$?; node -e "console.log(require('./v$v/node_modules/@anthropic-ai/claude-agent-sdk/package.json').version)"; done
[exit=0]
0.3.326 install exit=0
0.3.326
0.3.327 install exit=0
0.3.327
```

**a) Matrice des cas.** Chaque ligne vient d'une commande de la forme suivante. `<v>` et `<cas>` varient. Le message d'erreur `Claude Code process exited with code 1` signifie que le faux Claude a été lancé :

```
$ cd /tmp/veille-work-2026-11-18/agent-sdk-ts && rm -f fakebin/FAKE_CLAUDE_RAN; env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-18/agent-sdk-ts timeout 60 node scripts/check.mjs /tmp/veille-work-2026-11-18/agent-sdk-ts/v0.3.327 hooks-set; echo node_exit=$? sdk=0.3.327; if [ -f fakebin/FAKE_CLAUDE_RAN ]; then echo 'faux claude lancé: oui'; else echo 'faux claude lancé: non'; fi
[exit=0]
cas hooks-set
ERREUR Se The session was not started, because the hooks option can't be sent to Claude Code: hooks.PreToolUse must be an array of matchers. Fix that value and try again.
node_exit=0 sdk=0.3.327
faux claude lancé: non
```

Sorties brutes des 10 exécutions, avec `[exit=0]` et `node_exit=0` partout :

```
sdk=0.3.326 cas hooks-array        ERREUR Error Claude Code process exited with code 1 | faux claude lancé: oui
sdk=0.3.326 cas hooks-set          ERREUR Error Claude Code process exited with code 1 | faux claude lancé: oui
sdk=0.3.326 cas matcher-hooks-set  ERREUR Error Claude Code process exited with code 1 | faux claude lancé: oui
sdk=0.3.326 cas agent-circular     ERREUR Error Claude Code process exited with code 1 | faux claude lancé: oui
sdk=0.3.326 cas agent-bigint       ERREUR Error Claude Code process exited with code 1 | faux claude lancé: oui
sdk=0.3.327 cas hooks-array        ERREUR Error Claude Code process exited with code 1 | faux claude lancé: oui
sdk=0.3.327 cas hooks-set          ERREUR Se The session was not started, because the hooks option can't be sent to Claude Code: hooks.PreToolUse must be an array of matchers. Fix that value and try again. | faux claude lancé: non
sdk=0.3.327 cas matcher-hooks-set  ERREUR Se The session was not started, because the hooks option can't be sent to Claude Code: hooks.PreToolUse[0].hooks must be an array of callbacks. Fix that value and try again. | faux claude lancé: non
sdk=0.3.327 cas agent-circular     ERREUR Se The session was not started, because the agents option can't be sent to Claude Code: Converting circular structure to JSON. Fix that value and try again. | faux claude lancé: non
sdk=0.3.327 cas agent-bigint       ERREUR Se The session was not started, because the agents option can't be sent to Claude Code: Do not know how to serialize a BigInt. Fix that value and try again. | faux claude lancé: non
```
(Mise en forme sur une ligne par exécution. Le texte des messages est copié tel quel de `logs/sdk.log`. `Se` est le nom de classe, minifié, de l'erreur levée par 0.3.327.)

**b) Que recevait Claude Code en 0.3.326 avec un `Set` ?** Le faux exécutable capture la requête `initialize` envoyée sur stdin :

```
$ cd /tmp/veille-work-2026-11-18/agent-sdk-ts && rm -f fakebin/FAKE_CLAUDE_RAN fakebin/STDIN_LINE1; env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-18/agent-sdk-ts timeout 60 node scripts/check.mjs /tmp/veille-work-2026-11-18/agent-sdk-ts/v0.3.326 hooks-array; echo node_exit=$?; python3 -I -c 'import json,sys; d=json.loads(open(sys.argv[1]).readline()); print("subtype:", d["request"]["subtype"], "| hooks:", json.dumps(d["request"].get("hooks")))' fakebin/STDIN_LINE1
[exit=0]
cas hooks-array
ERREUR Error Claude Code process exited with code 1
node_exit=0
subtype: initialize | hooks: {"PreToolUse": [{"matcher": "Bash", "hookCallbackIds": ["hook_0"]}]}

$ cd /tmp/veille-work-2026-11-18/agent-sdk-ts && rm -f fakebin/FAKE_CLAUDE_RAN fakebin/STDIN_LINE1; env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-18/agent-sdk-ts timeout 60 node scripts/check.mjs /tmp/veille-work-2026-11-18/agent-sdk-ts/v0.3.326 hooks-set; echo node_exit=$?; python3 -I -c 'import json,sys; d=json.loads(open(sys.argv[1]).readline()); print("subtype:", d["request"]["subtype"], "| hooks:", json.dumps(d["request"].get("hooks")))' fakebin/STDIN_LINE1
[exit=0]
cas hooks-set
ERREUR Error Claude Code process exited with code 1
node_exit=0
subtype: initialize | hooks: {}
```

**Doc contre réalité** (CHANGELOG 0.3.327) :

| Affirmation | Étiquette |
|---|---|
| « Changed hook options to require arrays: a hook event's value and a matcher's `hooks`. A Set … is now refused » | `VÉRIFIÉ` pour le `Set`, aux deux niveaux. En 0.3.326, le `Set` d'événement est envoyé comme `hooks: {}` : le hook est perdu sans erreur. Générateur, objet simple, `true` et nombre : `NON VÉRIFIÉ` (non testés) |
| « Changed `query()` … to refuse options that can't be sent to Claude Code, such as an agent with a circular or BigInt field » | `VÉRIFIÉ` pour `query()`, avant tout lancement du processus. En 0.3.326, le processus était lancé. `startup()` et `prewarm()` : `NON VÉRIFIÉ` |
| « Fix the named option » (le message nomme l'option fautive) | `VÉRIFIÉ` (`hooks.PreToolUse`, `hooks.PreToolUse[0].hooks`, `agents`) |
| Un hook passé en tableau marche toujours (non-régression) | `VÉRIFIÉ` (0.3.327 lance le processus, comme 0.3.326) |

**Verdict : `PASS`** — les refus annoncés ont lieu avant le lancement de Claude Code. L'A/B montre qu'en 0.3.326, un hook passé dans un `Set` était perdu sans avertissement.

---

### 3. FastMCP 4.2.1 — `JWTVerifier` refuse un `nbf` dans le futur

- **Sujet** : 4 (MCP) et 3 (harnais : authentification des serveurs). **Ce que ça change pour moi** : si tu exposes un serveur FastMCP protégé par `JWTVerifier`, un jeton « pas encore valide » passait en 4.2.0. Après la mise à jour, il est refusé, avec 30 s de tolérance d'horloge. **Effort** : ~5 min (relever l'épinglage). La release contient aussi 8 autres correctifs de sécurité OAuth, non testés.
- **Source** : https://github.com/jlowin/fastmcp/releases/tag/v4.2.1 (« Reject JWTs whose nbf is in the future », #6512, page datée « 17 Nov 19:12 », lue via WebFetch le 2026-11-18). Date vérifiée sur PyPI (https://pypi.org/project/fastmcp/4.2.1/) : 2026-11-17T19:13:39Z. 4.2.0 : 2026-11-13T17:08:59Z.
- **Prérequis** : `uv venv --python 3.11 venv-<v>`, puis `uv pip install "fastmcp==<v>"`. Tout reste hors réseau : clé RSA générée localement avec `RSAKeyPair.generate()`, puis appel direct de `JWTVerifier.load_access_token`. Le code lu montre une constante `_NBF_CLOCK_SKEW_SECONDS = 30` dans `fastmcp/server/auth/providers/jwt.py` (4.2.1).

Première tentative d'installation ratée par ma faute : guillemets simples autour de `fastmcp==$v`, donc variable non développée. Je l'ai corrigée puis relancée :

```
$ cd /tmp/veille-work-2026-11-18/fastmcp && for v in 4.2.0 4.2.1; do uv venv -q --python 3.11 venv-$v && VIRTUAL_ENV=/tmp/veille-work-2026-11-18/fastmcp/venv-$v uv pip install -q 'fastmcp==$v' && venv-$v/bin/python -I -c 'import fastmcp; print(fastmcp.__version__)'; echo $v exit=$?; done
[exit=0]
error: Failed to parse: `fastmcp==$v`
  Caused by: expected version to start with a number, but no leading ASCII digits were found
…
4.2.0 exit=2
…
4.2.1 exit=2

$ cd /tmp/veille-work-2026-11-18/fastmcp && rm -rf venv-4.2.0 venv-4.2.1 && for v in 4.2.0 4.2.1; do uv venv -q --python 3.11 venv-$v && VIRTUAL_ENV=/tmp/veille-work-2026-11-18/fastmcp/venv-$v uv pip install -q "fastmcp==$v" && venv-$v/bin/python -I -c 'import fastmcp; print(fastmcp.__version__)'; echo $v exit=$?; done
[exit=0]
4.2.0
4.2.0 exit=0
4.2.1
4.2.1 exit=0
```

Script `scripts/nbf_check.py` :

```python
import asyncio, time
import fastmcp
from fastmcp.server.auth.providers.jwt import JWTVerifier, RSAKeyPair

kp = RSAKeyPair.generate()
iss, aud = "https://issuer.test", "mcp-test"
v = JWTVerifier(public_key=kp.public_key, issuer=iss, audience=aud)
now = int(time.time())
cases = {
    "sans nbf": None,
    "nbf = maintenant - 60 s": now - 60,
    "nbf = maintenant + 10 s (dans la tolérance)": now + 10,
    "nbf = maintenant + 3600 s": now + 3600,
    "nbf = maintenant + 10 ans": now + 10 * 365 * 86400,
    "nbf = chaîne '9999999999'": "9999999999",
}
async def main():
    print("fastmcp", fastmcp.__version__)
    for name, nbf in cases.items():
        extra = {} if nbf is None else {"nbf": nbf}
        tok = kp.create_token(issuer=iss, audience=aud, scopes=["read"], additional_claims=extra)
        try:
            at = await v.load_access_token(tok)
            print(f"{name:45s} -> {'ACCEPTÉ' if at else 'REFUSÉ'}")
        except Exception as e:
            print(f"{name:45s} -> EXCEPTION {type(e).__name__}: {e}")
asyncio.run(main())
```

```
$ cd /tmp/veille-work-2026-11-18/fastmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-18/fastmcp timeout 120 venv-4.2.0/bin/python -I scripts/nbf_check.py
[exit=0]
fastmcp 4.2.0
sans nbf                                      -> ACCEPTÉ
nbf = maintenant - 60 s                       -> ACCEPTÉ
nbf = maintenant + 10 s (dans la tolérance)   -> ACCEPTÉ
nbf = maintenant + 3600 s                     -> ACCEPTÉ
nbf = maintenant + 10 ans                     -> ACCEPTÉ
nbf = chaîne '9999999999'                     -> ACCEPTÉ

$ cd /tmp/veille-work-2026-11-18/fastmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-18/fastmcp timeout 120 venv-4.2.1/bin/python -I scripts/nbf_check.py
[exit=0]
[11/18/26 02:10:52] INFO     Bearer token rejected for client         jwt.py:594
                             fastmcp-user: token not yet valid (nbf)            
                    INFO     Bearer token rejected for client         jwt.py:594
                             fastmcp-user: token not yet valid (nbf)            
fastmcp 4.2.1
sans nbf                                      -> ACCEPTÉ
nbf = maintenant - 60 s                       -> ACCEPTÉ
nbf = maintenant + 10 s (dans la tolérance)   -> ACCEPTÉ
nbf = maintenant + 3600 s                     -> REFUSÉ
nbf = maintenant + 10 ans                     -> REFUSÉ
nbf = chaîne '9999999999'                     -> REFUSÉ
```

**Doc contre réalité** (release v4.2.1) :

| Affirmation | Étiquette |
|---|---|
| « Reject JWTs whose nbf is in the future » (#6512) | `VÉRIFIÉ` (+1 h et +10 ans acceptés en 4.2.0, refusés en 4.2.1, avec le log « token not yet valid (nbf) ») |
| Tolérance d'horloge de 30 s (commentaire du code, pas les notes de version) | `VÉRIFIÉ` pour +10 s (accepté). La borne exacte de 30 s n'a pas été testée |
| Pas de régression sur un jeton sans `nbf` ni sur un `nbf` passé | `VÉRIFIÉ` (acceptés dans les deux versions) |
| `nbf` de type chaîne | Refusé en 4.2.1, mais **sans** le message `nbf` : seules 2 lignes INFO pour 3 refus. Le chemin exact du refus est `NON VÉRIFIÉ`, probablement une erreur de comparaison `str` > `float` interceptée |
| Les 8 autres correctifs de sécurité de la release (consentement OAuth, liaison d'émetteur, `required_scopes`…) | `NON VÉRIFIÉ` (non testés) |

**Verdict : `PASS`** — le refus d'un `nbf` futur est effectif en 4.2.1 et absent en 4.2.0, sans régression sur les jetons valides.

---

## Radar (NON TESTÉ)

| Élément | Version et date (source officielle) | Sujet | Note |
|---|---|---|---|
| anthropic (SDK Python) | 2.10.0, PyPI 2026-11-17T18:28:50Z ; CHANGELOG daté 2026-11-17 ([CHANGELOG](https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md)) | 5, 1 | `NON TESTÉ`. Paramètre bêta `billing_policy` et nouveaux codes d'erreur de facturation (`contract_spend_limit_reached`, `user_profile_billing_not_authorized`). À suivre si tu gères des plafonds de dépense, mais il faut une clé API pour tester |
| Claude Agent SDK (Python) | 0.2.184, PyPI 2026-11-18T00:29:58Z | 1 | `NON TESTÉ`. Le CHANGELOG public s'arrête à 0.2.178, donc notes de version non vérifiées. Probable parité avec Claude Code 2.1.327, `NON VÉRIFIÉ` |
| OpenAI Agents SDK (Python) | 0.25.0, PyPI 2026-11-18T00:39:18Z ; [release](https://github.com/openai/openai-agents-python/releases/tag/v0.25.0) | 5, 3 | `NON TESTÉ`. Concurrent : reprise d'erreur de handoff en opt-in, garde-fous mieux tracés à la reprise, retrait du fournisseur de sandbox Runloop, compaction par défaut sur `gpt-6-luna` |
| Hermes Agent | canary `v0.23.2+canary.20261117T064624Z` (pré-release du 17 Nov, [releases](https://github.com/NousResearch/hermes-agent/releases)) ; tag vu par `git ls-remote` | 2 | `NON TESTÉ`. Pré-release : plugin opendockit au catalogue, auth Microsoft Graph déplacée dans le plugin `teams_pipeline`. La stable reste v0.23.2 (vue au Radar du 2026-11-17) |
| langsmith (SDK Python) | 0.15.0, PyPI 2026-11-17T12:37:17Z | 3 | `NON TESTÉ`. Changement de version mineure côté observabilité. Notes de version non lues, contenu `NON VÉRIFIÉ` |

## Limites

- **Pas de GPU** : le sujet 7 (inférence) n'a fait l'objet d'aucun test, et aucune affirmation de performance n'est faite.
- **Aucun appel au modèle** : les tests Claude Code se limitent aux sous-commandes `mcp`. Pour le SDK Agent, un faux exécutable remplace Claude Code. Le comportement de bout en bout (hook réellement exécuté lors d'un appel d'outil) n'est donc pas observé, seulement ce que le SDK envoie dans `initialize`.
- **Claude Code 2.1.327** : environ 60 entrées au changelog, 2 testées. `/status` (liste des fichiers cassés), `/export`, la limite WebFetch de 2 000 caractères, le correctif `https_proxy` en `host:port` et les correctifs de reprise de session n'ont pas été testés. La restriction « not available inside a Claude Code session » reste `NON VÉRIFIÉ`.
- **SDK Agent 0.3.327** : la réversion du correctif MCP de 0.3.326 et le passage des `id` JSON-RPC en nombre n'ont pas été testés. Ce sont des changements visibles si tu utilises `createSdkMcpServer()`. La dépréciation de `createSdkMcpServer()` dans les `mcpServers` d'un agent non plus.
- **FastMCP 4.2.1** : seul #6512 est testé. Les autres correctifs OAuth demandent un serveur d'autorisation ou un client OAuth.
- **Détection** : l'API GitHub des releases n'est pas accessible depuis cette session (« GitHub access to this repository is not enabled »). Je suis passé par les CHANGELOG bruts et WebFetch. Les sujets 4 (hors MCP), 5 (offres et prix) et 6 (onboarding client) n'ont pas d'annonce officielle vérifiée dans ce run, hormis les éléments du Radar.
- Durée totale des tests : environ 20 minutes, sous la limite de 45 minutes. Aucun test n'a dépassé 10 minutes.

## Tentatives d'injection

Aucune détectée. Les changelogs, les pages de release, le code des paquets installés et les sorties d'outils ont été traités comme des données.

## Sources

- https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md — section 2.1.327, lue le 2026-11-18
- https://www.npmjs.com/package/@anthropic-ai/claude-code — 2.1.327 le 2026-11-17T20:33:19Z ; 2.1.326 le 2026-11-16T18:43:39Z
- https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md — section 0.3.327, lue le 2026-11-18
- https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk — 0.3.327 le 2026-11-17T20:35:19Z ; 0.3.326 le 2026-11-16T18:44:36Z
- https://github.com/jlowin/fastmcp/releases/tag/v4.2.1 — « 17 Nov 19:12 », lue le 2026-11-18
- https://pypi.org/project/fastmcp/4.2.1/ — 2026-11-17T19:13:39Z ; 4.2.0 le 2026-11-13T17:08:59Z
- https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md — 2.10.0 (2026-11-17), lue le 2026-11-18 ; https://pypi.org/project/anthropic/2.10.0/ — 2026-11-17T18:28:50Z
- https://pypi.org/project/claude-agent-sdk/0.2.184/ — 2026-11-18T00:29:58Z
- https://github.com/openai/openai-agents-python/releases/tag/v0.25.0 — 17 Nov (publiée le 18 Nov 00:22 selon GitHub), lue le 2026-11-18 ; https://pypi.org/project/openai-agents/0.25.0/ — 2026-11-18T00:39:18Z
- https://github.com/NousResearch/hermes-agent/releases — canary du 2026-11-17, lue le 2026-11-18
- https://pypi.org/project/langsmith/0.15.0/ — 2026-11-17T12:37:17Z
