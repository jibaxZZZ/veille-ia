# Veille IA — 2026-11-19

## TL;DR

- **Run du 2026-11-19** (fenêtre du 2026-11-12 au 2026-11-19) : **8 éléments détectés, 3 testés (3 PASS), 5 au Radar.** Les 3 tests sont des A/B contre la version précédente.
- **Claude Code 2.1.328 : PASS.** Un hook `mcp_tool` avec `"onFailure": "block"` bloque désormais la commande Bash quand son outil MCP échoue ou que son serveur n'existe pas. En 2.1.327, la commande s'exécutait quand même. Testé de bout en bout avec un **faux endpoint API local**, sans clé ni modèle réel.
- **deepagents 0.7.40 : PASS.** Une commande shell qui dépasse le délai renvoie la sortie produite avant l'arrêt, au lieu d'un simple message d'erreur. Une commande annulée (`aexecute` + `cancel()`) ne continue plus à tourner en arrière-plan, contrairement à la 0.7.39.
- **FastMCP 4.2.2 : PASS.** Avec un transform `ResourcesAsTools` ou `PromptsAsTools`, `list_skills()` renvoyait `[]` en 4.2.1. En 4.2.2, il liste les skills. Un transform `Namespace` les masque toujours, comme prévu.
- Aucune tentative d'injection relevée. Pas de GPU, donc aucun test de performance.

## Contexte et choix faits sans validation humaine

- Répertoire de travail : `/tmp/veille-work-2026-11-19/<élément>/`. Toutes les commandes passent par un wrapper `bin/run`. Il consigne la commande, le code de sortie et la sortie (tronquée à 40 lignes) dans `logs/<élément>.log`. Les sorties ci-dessous viennent de ces journaux. `[exit=…]` est le code de la commande complète, donc du dernier maillon d'un pipeline. Le vrai code du programme testé est affiché à part (`claude_exit=`, `python_exit=`, `version_exit=`).
- Machine : Linux x86_64, Node v22.23.5, npm, uv (venvs Python 3.11). Pas de GPU.
- **Isolation** : chaque outil a tourné sous `env -i`, avec un environnement vide et `HOME` pointé vers un dossier du répertoire de travail. Aucune variable d'environnement de la machine n'a été lue ni transmise. Pour Claude Code, `ANTHROPIC_BASE_URL` pointe vers un **faux serveur Messages API** local (`scripts/mock_api.py`, 127.0.0.1). Il répond d'abord par un `tool_use` Bash scripté, puis par le texte `FIN-DU-MOCK`. La clé `fausse-cle-test` est une chaîne factice. Aucun modèle réel n'a été appelé.
- **Détection** : versions et dates tirées des registres officiels (`npm view <paquet> time --json`, API JSON de PyPI) et de `git ls-remote --tags`. J'ai lu les notes de version dans les `CHANGELOG.md` bruts (raw.githubusercontent.com) et, avec WebFetch, sur les pages de release et de PR GitHub.
- **Sélection** : j'ai retenu les 3 éléments testables sans clé API qui touchent les garde-fous de harnais (sujet 3), Claude Code (sujet 1) et MCP (sujet 4). Aucune de ces versions n'est dans `tested.md`. Claude Code 2.1.327, deepagents 0.7.39 et FastMCP 4.2.1 y figurent, mais ils ne servent ici que de témoins A/B.

---

## Tests

### 1. Claude Code 2.1.328 — `onFailure: "block"` pour les hooks `mcp_tool`

- **Sujet** : 1 (hooks Claude Code) et 3 (garde-fous de harnais). **Ce que ça change pour moi** : un hook de politique servi par un serveur MCP peut maintenant bloquer l'action quand ce serveur plante ou n'est pas lancé, au lieu de tout laisser passer. Ajoute `"onFailure": "block"` à tes hooks `mcp_tool` de sécurité, car sans ce champ l'action passe toujours. **Effort** : ~15 min (mise à jour et ajout du champ dans `settings.json`).
- **Source** : https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md (section `## 2.1.328`, lue en brut le 2026-11-19). Date vérifiée sur npm (https://www.npmjs.com/package/@anthropic-ai/claude-code) : 2.1.328 publiée le 2026-11-18T23:09:39Z, 2.1.327 le 2026-11-17T20:33:19Z.
- **Prérequis** : `npm install --prefix v<v> @anthropic-ai/claude-code@<v>` pour 2.1.327 et 2.1.328. Deux scripts écrits pour le test, dans `claude-code/scripts/` :
  - `mock_api.py <port> <log> <commande>` : faux endpoint `/v1/messages` (SSE). Il renvoie un `tool_use` Bash qui exécute `touch <run>/MARKER`, puis du texte une fois le `tool_result` reçu. Il consigne chaque requête.
  - `guard_mcp.py <log>` : serveur MCP stdio minimal en JSON-RPC, sans dépendance. Son outil `guard` répond toujours `isError: true` et consigne ses appels.
  - `case.sh <version> <mode> <port>` lance `claude -p "lance la commande" --settings settings.json --mcp-config mcp.json --strict-mcp-config --allowedTools Bash`, avec `env -i`, `ANTHROPIC_BASE_URL=http://127.0.0.1:<port>`, `ANTHROPIC_API_KEY=fausse-cle-test` et `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`. Il vérifie ensuite si `MARKER` existe, autrement dit si la commande Bash a tourné.

`settings.json` du mode `block` (le mode `unset` retire `onFailure` ; le mode `block-missing-server` remplace `"server":"guard"` par `"server":"absent"`) :

```
{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"mcp_tool","server":"guard","tool":"guard","input":{"cmd":"${tool_input.command}"},"onFailure":"block"}]}]}}
```

```
$ cd /tmp/veille-work-2026-11-19/claude-code && for v in 2.1.327 2.1.328; do mkdir -p v$v && npm install -q --prefix v$v @anthropic-ai/claude-code@$v >/dev/null 2>&1; echo $v $?; v$v/node_modules/.bin/claude --version; done
2.1.327 0
2.1.327 (Claude Code)
2.1.328 0
2.1.328 (Claude Code)

$ cd /tmp/veille-work-2026-11-19/claude-code && for v in 2.1.327 2.1.328; do v$v/node_modules/.bin/claude --version; echo version_exit=$?; done
[exit=0]
2.1.327 (Claude Code)
version_exit=0
2.1.328 (Claude Code)
version_exit=0
```
(La première commande, l'installation, a été lancée hors du wrapper : la deuxième colonne de `2.1.32x 0` est le code de sortie de `npm install`.)

**a) Outil du hook en erreur, `onFailure: "block"`.** 2.1.327 puis 2.1.328 :

```
$ /tmp/veille-work-2026-11-19/claude-code/scripts/case.sh 2.1.327 block 18731
[exit=0]
FIN-DU-MOCK
claude_exit=0
MARKER créé: OUI
appels mcp guard: 1 {"name": "guard", "arguments": {"cmd": "touch /tmp/veille-work-2026-11-19/claude-code/run-2.1.327-block/MARKER"}}
requêtes API: 2 ; tool_result renvoyé au modèle: 1
{"path": "/v1/messages?beta=true", "tools_has_bash": true, "has_tool_result": true, "last": "[{\"tool_use_id\": \"toolu_01\", \"type\": \"tool_result\", \"content\": \"(Bash completed with no output)\", \"is_error\": false, \"cache_control\": {\"type\": \"ephemeral\"}}]"}

$ /tmp/veille-work-2026-11-19/claude-code/scripts/case.sh 2.1.328 block 18732
[exit=0]
FIN-DU-MOCK
claude_exit=0
MARKER créé: NON
appels mcp guard: 1 {"name": "guard", "arguments": {"cmd": "touch /tmp/veille-work-2026-11-19/claude-code/run-2.1.328-block/MARKER"}}
requêtes API: 2 ; tool_result renvoyé au modèle: 1
{"path": "/v1/messages?beta=true", "tools_has_bash": true, "has_tool_result": true, "last": "[{\"type\": \"tool_result\", \"content\": \"PreToolUse:Bash hook error: [guard/guard]: failed; blocking because onFailure is \\\"block\\\" and the hook got no usable answer from its MCP server. The user needs to fix the cause (in a session, /mcp shows the server's state) or ask whoever manages the hook; Cl
```
(La dernière ligne est coupée à 300 caractères par le journal du faux serveur.)

**b) Même hook sans `onFailure`** (comportement par défaut) :

```
$ /tmp/veille-work-2026-11-19/claude-code/scripts/case.sh 2.1.327 unset 18733
[exit=0]
FIN-DU-MOCK
claude_exit=0
MARKER créé: OUI
appels mcp guard: 1 {"name": "guard", "arguments": {"cmd": "touch /tmp/veille-work-2026-11-19/claude-code/run-2.1.327-unset/MARKER"}}
requêtes API: 2 ; tool_result renvoyé au modèle: 1
{"path": "/v1/messages?beta=true", "tools_has_bash": true, "has_tool_result": true, "last": "[{\"tool_use_id\": \"toolu_01\", \"type\": \"tool_result\", \"content\": \"(Bash completed with no output)\", \"is_error\": false, \"cache_control\": {\"type\": \"ephemeral\"}}]"}

$ /tmp/veille-work-2026-11-19/claude-code/scripts/case.sh 2.1.328 unset 18734
[exit=0]
FIN-DU-MOCK
claude_exit=0
MARKER créé: OUI
appels mcp guard: 1 {"name": "guard", "arguments": {"cmd": "touch /tmp/veille-work-2026-11-19/claude-code/run-2.1.328-unset/MARKER"}}
requêtes API: 2 ; tool_result renvoyé au modèle: 1
{"path": "/v1/messages?beta=true", "tools_has_bash": true, "has_tool_result": true, "last": "[{\"tool_use_id\": \"toolu_01\", \"type\": \"tool_result\", \"content\": \"(Bash completed with no output)\", \"is_error\": false, \"cache_control\": {\"type\": \"ephemeral\"}}]"}
```

**c) Cas limite : serveur du hook inexistant (`"server":"absent"`), `onFailure: "block"`** :

```
$ /tmp/veille-work-2026-11-19/claude-code/scripts/case.sh 2.1.327 block-missing-server 18735
[exit=0]
FIN-DU-MOCK
claude_exit=0
MARKER créé: OUI
appels mcp guard: 0 
requêtes API: 2 ; tool_result renvoyé au modèle: 1
{"path": "/v1/messages?beta=true", "tools_has_bash": true, "has_tool_result": true, "last": "[{\"tool_use_id\": \"toolu_01\", \"type\": \"tool_result\", \"content\": \"(Bash completed with no output)\", \"is_error\": false, \"cache_control\": {\"type\": \"ephemeral\"}}]"}

$ /tmp/veille-work-2026-11-19/claude-code/scripts/case.sh 2.1.328 block-missing-server 18736
[exit=0]
FIN-DU-MOCK
claude_exit=0
MARKER créé: NON
appels mcp guard: 0 
requêtes API: 2 ; tool_result renvoyé au modèle: 1
{"path": "/v1/messages?beta=true", "tools_has_bash": true, "has_tool_result": true, "last": "[{\"type\": \"tool_result\", \"content\": \"PreToolUse:Bash hook error: [absent/guard]: failed; blocking because onFailure is \\\"block\\\" and the hook got no usable answer from its MCP server. The user needs to fix the cause (in a session, /mcp shows the server's state) or ask whoever manages the hook; C
```

**d) Correctif annexe : crash au démarrage avec `FORCE_COLOR` négatif.** Sorties ANSI conservées telles quelles (les codes d'échappement s'affichent `[0m…`) :

```
$ cd /tmp/veille-work-2026-11-19/claude-code && env -i PATH=/usr/local/bin:/usr/bin:/bin:/opt/node22/bin HOME=/tmp/veille-work-2026-11-19/claude-code/fc-home-2.1.327 FORCE_COLOR=-1 ANTHROPIC_BASE_URL=http://127.0.0.1:9 ANTHROPIC_API_KEY=fausse-cle-test timeout 60 /tmp/veille-work-2026-11-19/claude-code/v2.1.327/node_modules/.bin/claude mcp list </dev/null 2>&1 | tail -6; echo claude_exit=${PIPESTATUS[0]}
[exit=0]
[0m[31merror[0m[2m:[0m [1mThe `level` option should be an integer from 0 to 3[0m
[0m      [2mat [0m[0m[1m[3mH[0m[2m ([0m[0m[36m/$bunfs/root/chunk-5p3pe6mv.js[0m[2m:[0m[33m8[0m[2m:[33m279[0m[2m)[0m
[0m      [2mat [0m[0m[1m[3mw[0m[2m ([0m[0m[36m/$bunfs/root/chunk-5p3pe6mv.js[0m[2m:[0m[33m8[0m[2m:[33m473[0m[2m)[0m
[0m      [2mat [0m[0m[36m/$bunfs/root/chunk-5p3pe6mv.js[0m[2m:[0m[33m9[0m[2m:[33m94[0m
[0m
[2mBun v1.4.4 (Linux x64)[0m
claude_exit=1

$ cd /tmp/veille-work-2026-11-19/claude-code && env -i PATH=/usr/local/bin:/usr/bin:/bin:/opt/node22/bin HOME=/tmp/veille-work-2026-11-19/claude-code/fc-home-2.1.328 FORCE_COLOR=-1 ANTHROPIC_BASE_URL=http://127.0.0.1:9 ANTHROPIC_API_KEY=fausse-cle-test timeout 60 /tmp/veille-work-2026-11-19/claude-code/v2.1.328/node_modules/.bin/claude mcp list </dev/null 2>&1 | tail -6; echo claude_exit=${PIPESTATUS[0]}
[exit=0]
No MCP servers configured. Use `claude mcp add` to add a server.
claude_exit=0
```

**Doc contre réalité** :

| Affirmation | Étiquette |
|---|---|
| CHANGELOG 2.1.328 : « Added `"onFailure": "block"` for `mcp_tool` hooks, as for command and HTTP hooks: a hook whose call fails blocks the action » | `VÉRIFIÉ` (outil en erreur et serveur absent : commande exécutée en 2.1.327, bloquée en 2.1.328 avec le message « blocking because onFailure is "block" » renvoyé au modèle) |
| Champ non renseigné : l'action continue malgré l'échec du hook (page hooks, « On most events, when a hook fails… Claude Code still carries out the action ») | `VÉRIFIÉ` (mode `unset` : `MARKER` créé dans les deux versions) |
| Page https://code.claude.com/docs/en/hooks lue le 2026-11-19 : « set `"onFailure": "block"` on a `command` or `http` hook », et le tableau des champs `mcp_tool` ne liste pas `onFailure` | `CONTREDIT` par le comportement de 2.1.328 : la doc n'est pas encore à jour, le champ fonctionne sur `mcp_tool` |
| Substitution `${tool_input.command}` dans `input` d'un hook `mcp_tool` (page hooks) | `VÉRIFIÉ` (le serveur reçoit `{"cmd": "touch …/MARKER"}`) |
| CHANGELOG : « Fixed a crash at startup when `FORCE_COLOR` is set to a negative number » | `VÉRIFIÉ` (`FORCE_COLOR=-1` : erreur Bun et exit 1 en 2.1.327 ; exit 0 en 2.1.328) |
| Les ~150 autres entrées de 2.1.328 (Code Mode, self-hosted runner, `CLAUDE_CODE_DISABLE_DEFERRED_TOOL_RESUME`, zsh et `=`…) | `NON VÉRIFIÉ` (non testées) |

**Verdict : `PASS`** — `onFailure: "block"` sur un hook `mcp_tool` bloque l'action en 2.1.328 (outil en erreur et serveur absent), ce que 2.1.327 ne faisait pas, et le défaut reste permissif.

---

### 2. deepagents 0.7.40 — sortie conservée au timeout, nettoyage à l'annulation

- **Sujet** : 3 (sandboxes, reprise sur erreur) et 2 (écosystème LangGraph). **Ce que ça change pour moi** : avec `LocalShellBackend`, un agent dont la commande expire voit désormais ce qu'elle avait produit, ce qui l'aide à reprendre au lieu de relancer à l'aveugle. Une commande annulée ou expirée ne laisse plus de processus qui continue d'écrire sur le disque. **Effort** : ~5 min (montée de version, sans changement d'API).
- **Source** : https://github.com/langchain-ai/deepagents/releases/tag/deepagents==0.7.40 (lue le 2026-11-19, « 18 November », 18:27). Date vérifiée sur PyPI (https://pypi.org/project/deepagents/0.7.40/) : 2026-11-18T18:27:44Z ; 0.7.39 le 2026-11-16T15:55:09Z.
- **Prérequis** : `uv venv -p 3.11 venv-<v> && uv pip install -p venv-<v>/bin/python deepagents==<v>` pour 0.7.39 et 0.7.40. Le script `deepagents/scripts/timeout_test.py <root>` crée `LocalShellBackend(root_dir=<root>, timeout=2)` et enchaîne 3 cas : (1) `echo AVANT-TIMEOUT; echo ERR-AVANT >&2; sleep 30; echo APRES` ; (2) `echo DEBUT; (sleep 30; touch <root>/ORPHELIN) & sleep 30`, un petit-enfant en arrière-plan ; (3) `aexecute("echo PID-$$ > <root>/pid; sleep 40; touch <root>/APRES-ANNULATION", timeout=60)`, annulée après 1,5 s.

```
$ cd /tmp/veille-work-2026-11-19/deepagents && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-19/deepagents timeout 300 venv-0.7.39/bin/python -I scripts/timeout_test.py /tmp/veille-work-2026-11-19/deepagents/root-0.7.39
[exit=0]
deepagents 0.7.39
cas1 duree=2.0s exit_code=124
cas1 output= 'Error: Command timed out after 2 seconds. For long-running commands, re-run using the timeout parameter.'
cas2 duree=2.0s exit_code=124 output='Error: Command timed out after 2 seconds. For long-running commands, re-run using the timeout parameter.'
cas3 tâche annulée
cas3 shell 1052 encore vivant 1 s après annulation: False

$ cd /tmp/veille-work-2026-11-19/deepagents && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-19/deepagents timeout 300 venv-0.7.40/bin/python -I scripts/timeout_test.py /tmp/veille-work-2026-11-19/deepagents/root-0.7.40
[exit=0]
deepagents 0.7.40
cas1 duree=2.0s exit_code=124
cas1 output= 'Error: Command timed out after 2 seconds. For long-running commands, re-run using the timeout parameter.\n\nOutput before the timeout:\nAVANT-TIMEOUT\n\n[stderr] ERR-AVANT'
cas2 duree=2.0s exit_code=124 output='Error: Command timed out after 2 seconds. For long-running commands, re-run using the timeout parameter.\n\nOutput before the timeout:\nDEBUT\n'
cas3 tâche annulée
cas3 shell 1084 encore vivant 1 s après annulation: False
```

Contrôle des effets de bord, plus de 40 s après les deux runs (à 02:12 UTC) :

```
$ ls /tmp/veille-work-2026-11-19/deepagents/root-0.7.39 /tmp/veille-work-2026-11-19/deepagents/root-0.7.40; pgrep -af 'sleep (30|40)' || echo 'aucun sleep 30/40 restant'
[exit=0]
/tmp/veille-work-2026-11-19/deepagents/root-0.7.39:
APRES-ANNULATION
ORPHELIN
pid

/tmp/veille-work-2026-11-19/deepagents/root-0.7.40:
pid
1101 /bin/bash /tmp/veille-work-2026-11-19/bin/run deepagents ls /tmp/veille-work-2026-11-19/deepagents/root-0.7.39 /tmp/veille-work-2026-11-19/deepagents/root-0.7.40; pgrep -af 'sleep (30|40)' || echo 'aucun sleep 30/40 restant'
1102 /bin/bash /tmp/veille-work-2026-11-19/bin/run deepagents ls /tmp/veille-work-2026-11-19/deepagents/root-0.7.39 /tmp/veille-work-2026-11-19/deepagents/root-0.7.40; pgrep -af 'sleep (30|40)' || echo 'aucun sleep 30/40 restant'
1103 bash -c ls /tmp/veille-work-2026-11-19/deepagents/root-0.7.39 /tmp/veille-work-2026-11-19/deepagents/root-0.7.40; pgrep -af 'sleep (30|40)' || echo 'aucun sleep 30/40 restant'
```
Les 3 lignes de `pgrep` sont la commande de contrôle elle-même, dont le texte contient « sleep 30|40 ». Aucun vrai processus `sleep` ne reste.

En 0.7.39, la commande annulée (cas 3) a continué jusqu'au bout et créé `APRES-ANNULATION`. Le petit-enfant du cas 2 a survécu au timeout et créé `ORPHELIN`. En 0.7.40, aucun des deux fichiers n'existe. Mon contrôle « shell encore vivant » est faux dans les deux versions : le PID noté par `$$` n'était pas celui du processus qui a survécu en 0.7.39. Ce contrôle ne prouve donc rien, seuls les fichiers témoins comptent.

**Doc contre réalité** (release 0.7.40) :

| Affirmation | Étiquette |
|---|---|
| « Preserve output from timed-out shell commands. » (#6349) | `VÉRIFIÉ` (stdout et stderr d'avant le timeout présents en 0.7.40, absents en 0.7.39) |
| « Clean up cancelled shell commands. » (#5907) | `VÉRIFIÉ` (après `cancel()`, la commande allait au bout en 0.7.39, et plus en 0.7.40) |
| Petit-enfant en arrière-plan tué au timeout (pas dans les notes, observé) | `VÉRIFIÉ` en observation A/B (`ORPHELIN` créé en 0.7.39, pas en 0.7.40) |
| « Avoid warning-filter race conditions in `warn_deprecated`. » (#7749) et scan unique des plugins de profil (#7755) | `NON VÉRIFIÉ` (non testés) |

**Verdict : `PASS`** — sortie conservée au timeout et commandes annulées réellement arrêtées en 0.7.40, contrairement à 0.7.39.

---

### 3. FastMCP 4.2.2 — découverte des skills avec un transform d'outils

- **Sujet** : 4 (MCP) et 1 (skills). **Ce que ça change pour moi** : si tu sers des skills par MCP avec `ResourcesAsTools` (la recette du blog 4.2), `list_skills()` renvoyait `[]` sans erreur en 4.2.1, donc passe en 4.2.2. Évite `Namespace` sur ce serveur, qui masque toujours les skills. **Effort** : ~5 min (montée de version).
- **Source** : https://github.com/jlowin/fastmcp/releases/tag/v4.2.2 (« 18 Nov, 19:12 », lue le 2026-11-19) et PR https://github.com/PrefectHQ/fastmcp/pull/6548 (fusionnée le 18 Nov 2026). Date vérifiée sur PyPI (https://pypi.org/project/fastmcp/4.2.2/) : 2026-11-18T19:14:36Z ; 4.2.1 le 2026-11-17T19:13:39Z.
- **Prérequis** : `uv venv -p 3.11 venv-<v> && uv pip install -p venv-<v>/bin/python fastmcp==<v>` pour 4.2.1 et 4.2.2. Skill de test `data/skills/bonjour/SKILL.md` (frontmatter `name: bonjour`, `description`). Le script `fastmcp/scripts/skills_test.py <dir>` crée `FastMCP("Team Skills", providers=[SkillsDirectoryProvider(dir)])` avec un outil `ping`. Il ajoute un transform (aucun, `ResourcesAsTools(mcp)`, `PromptsAsTools(mcp)` ou `Namespace("ns")`), puis appelle `list_skills()`, `list_resources()` et `list_tools()` en mémoire via `Client(mcp, extensions=[SkillsClientExtension()])`.

```
$ cd /tmp/veille-work-2026-11-19/fastmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-19/fastmcp timeout 120 venv-4.2.1/bin/python -I scripts/skills_test.py /tmp/veille-work-2026-11-19/fastmcp/data/skills 2>&1 | grep -v '^\s*$'; echo python_exit=${PIPESTATUS[0]}
[exit=0]
fastmcp 4.2.1
transform=aucun             list_skills=['skill://bonjour/SKILL.md'] resources=['skill://bonjour/SKILL.md', 'skill://bonjour/_manifest'] tools=['ping']
transform=ResourcesAsTools  list_skills=[] resources=['skill://bonjour/SKILL.md', 'skill://bonjour/_manifest'] tools=['ping', 'list_resources', 'read_resource']
transform=PromptsAsTools    list_skills=[] resources=['skill://bonjour/SKILL.md', 'skill://bonjour/_manifest'] tools=['ping', 'list_prompts', 'get_prompt']
transform=Namespace         list_skills=[] resources=['skill://ns/bonjour/SKILL.md', 'skill://ns/bonjour/_manifest'] tools=['ns_ping']
python_exit=0

$ cd /tmp/veille-work-2026-11-19/fastmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-19/fastmcp timeout 120 venv-4.2.2/bin/python -I scripts/skills_test.py /tmp/veille-work-2026-11-19/fastmcp/data/skills 2>&1 | grep -v '^\s*$'; echo python_exit=${PIPESTATUS[0]}
[exit=0]
fastmcp 4.2.2
transform=aucun             list_skills=['skill://bonjour/SKILL.md'] resources=['skill://bonjour/SKILL.md', 'skill://bonjour/_manifest'] tools=['ping']
transform=ResourcesAsTools  list_skills=['skill://bonjour/SKILL.md'] resources=['skill://bonjour/SKILL.md', 'skill://bonjour/_manifest'] tools=['ping', 'list_resources', 'read_resource']
transform=PromptsAsTools    list_skills=['skill://bonjour/SKILL.md'] resources=['skill://bonjour/SKILL.md', 'skill://bonjour/_manifest'] tools=['ping', 'list_prompts', 'get_prompt']
transform=Namespace         list_skills=[] resources=['skill://ns/bonjour/SKILL.md', 'skill://ns/bonjour/_manifest'] tools=['ns_ping']
python_exit=0
```

Essais préalables, journalisés à part : sans `extensions=[SkillsClientExtension()]`, chaque appel de `list_skills()` lève `RuntimeError: This client did not opt into the Skills extension; pass SkillsClientExtension() in Client(extensions=[...])`, dans les deux versions. Les entrées renvoyées (`MCPSkill`) n'ont pas d'attribut `name` (`AttributeError`). On les identifie par `uri`.

**Doc contre réalité** (release v4.2.2 et PR #6548) :

| Affirmation | Étiquette |
|---|---|
| « Keep skills discovery on with tool-only server transforms » (#6548) : avec `ResourcesAsTools`, `client.list_skills()` renvoie les skills et non `[]` | `VÉRIFIÉ` (`[]` en 4.2.1, `['skill://bonjour/SKILL.md']` en 4.2.2, aussi avec `PromptsAsTools`) |
| PR : les ressources `skill://` restaient lisibles malgré le bug | `VÉRIFIÉ` (listées dans `list_resources()` en 4.2.1) |
| PR : un transform `Namespace` qui renomme les URI laisse « correctement » la skill de côté | `VÉRIFIÉ` (`list_skills=[]` dans les deux versions, URI réécrites en `skill://ns/…`) |
| Extrait de la PR (`# client.list_skills() now returns the directory's skills`) utilisable tel quel | `CONTREDIT` en partie : le client doit d'abord activer `SkillsClientExtension()`, sinon `RuntimeError`. L'extrait ne montre pas le client |
| Le chemin explicite `SkillsExtension(providers=...)` levait une erreur avec un transform (PR) | `NON VÉRIFIÉ` (non testé) |

**Verdict : `PASS`** — `list_skills()` fonctionne en 4.2.2 avec un transform qui ne touche que les outils, ce qui n'était pas le cas en 4.2.1.

---

## Radar (NON TESTÉ)

| Élément | Version et date (source officielle) | Sujet | Note |
|---|---|---|---|
| Claude Agent SDK (TypeScript) | 0.3.328, npm 2026-11-18T23:13:27Z ; [CHANGELOG](https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md) | 1, 3 | `NON TESTÉ`. Parité avec Claude Code 2.1.328 (`onFailure` sur `mcp_tool` dans le type `Settings`, `CLAUDE_CODE_DISABLE_DEFERRED_TOOL_RESUME` via `env`). Corrige aussi l'option `agent` : une définition inline gagne maintenant sur un agent de projet du même nom. Utile si tu définis des agents en code |
| MCP Inspector | 2.16.0, npm 2026-11-18T09:32:25Z ; [release](https://github.com/modelcontextprotocol/inspector/releases/tag/2.16.0) | 4, 3 | `NON TESTÉ`. Plafond de taille des lignes et événements SSE sur tous les transports (#2993/#2997), jar de cookies HTTP par serveur en opt-in (#2976), `acceptLanguage` SEP-2792 |
| langchain | 1.5.2, PyPI 2026-11-18T22:30:28Z (1.5.1 le 2026-11-18T15:44:56Z) | 2 | `NON TESTÉ`. Deux patchs le même jour ; notes de version non lues, contenu `NON VÉRIFIÉ` |
| Gemini CLI | 0.69.0, npm 2026-11-19T01:51:24Z | 5 | `NON TESTÉ`. Concurrent de Claude Code ; notes de version non lues, contenu `NON VÉRIFIÉ` |
| OpenAI Codex CLI | 0.172.0-alpha.1, npm 2026-11-18T18:09Z | 5 | `NON TESTÉ`. Pré-version alpha ; contenu `NON VÉRIFIÉ` |

## Limites

- **Pas de GPU** : le sujet 7 (inférence) n'a fait l'objet d'aucun test, et aucune affirmation de performance n'est faite. vLLM 0.34.0 (PyPI 2026-11-16) a été vu mais n'est pas retenu.
- **Faux endpoint API** : le test Claude Code passe par un serveur local qui imite l'API Messages. Il valide le chemin hook → blocage → `tool_result` renvoyé au modèle, mais pas le comportement d'un vrai modèle face au refus. Seul l'événement `PreToolUse` a été testé, avec deux types d'échec (outil `isError`, serveur absent). Le timeout d'un hook `mcp_tool` n'a pas été testé.
- **Claude Code 2.1.328** : le correctif zsh (`=` en début de mot) n'est pas testable, zsh n'est pas installé. Les correctifs des tâches planifiées (fichier illisible ou faute de frappe) et de Code Mode n'ont pas été testés.
- **deepagents 0.7.40** : seul `LocalShellBackend` a été testé, pas les sandboxes distantes.
- **Détection** : une recherche web sur les annonces Anthropic n'a renvoyé que des médias tiers, avec des événements du 9 novembre, hors fenêtre et non vérifiés à la source. Rien n'a été retenu. Les sujets 5 (offres et prix) et 6 (onboarding client) n'ont pas d'annonce officielle vérifiée dans ce run.
- Durée totale des tests : environ 25 minutes, sous la limite de 45 minutes. Aucun test n'a dépassé 10 minutes.

## Tentatives d'injection

Aucune détectée. Les changelogs, les pages de release et de PR, les résultats de recherche, le code des paquets installés et les sorties d'outils ont été traités comme des données.

## Sources

- https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md — section 2.1.328, lue le 2026-11-19
- https://www.npmjs.com/package/@anthropic-ai/claude-code — 2.1.328 le 2026-11-18T23:09:39Z ; 2.1.327 le 2026-11-17T20:33:19Z
- https://code.claude.com/docs/en/hooks — sections `mcp_tool` et « Block the action when a hook fails », lues le 2026-11-19
- https://github.com/langchain-ai/deepagents/releases/tag/deepagents==0.7.40 — 18 Nov 18:27, lue le 2026-11-19
- https://pypi.org/project/deepagents/0.7.40/ — 2026-11-18T18:27:44Z ; 0.7.39 le 2026-11-16T15:55:09Z
- https://github.com/jlowin/fastmcp/releases/tag/v4.2.2 — 18 Nov 19:12, lue le 2026-11-19 ; https://github.com/PrefectHQ/fastmcp/pull/6548 — fusionnée le 2026-11-18
- https://pypi.org/project/fastmcp/4.2.2/ — 2026-11-18T19:14:36Z ; 4.2.1 le 2026-11-17T19:13:39Z
- https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md — section 0.3.328, lue le 2026-11-19 ; https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk — 0.3.328 le 2026-11-18T23:13:27Z
- https://github.com/modelcontextprotocol/inspector/releases/tag/2.16.0 — 18 Nov, lue le 2026-11-19 ; https://www.npmjs.com/package/@modelcontextprotocol/inspector — 2.16.0 le 2026-11-18T09:32:25Z
- https://pypi.org/project/langchain/1.5.2/ — 2026-11-18T22:30:28Z
- https://www.npmjs.com/package/@google/gemini-cli — 0.69.0 le 2026-11-19T01:51:24Z
- https://www.npmjs.com/package/@openai/codex — 0.172.0-alpha.1 le 2026-11-18T18:09Z
