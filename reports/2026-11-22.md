# Veille IA — 2026-11-22

## TL;DR

- **Run du 2026-11-22** (fenêtre du 2026-11-15 au 2026-11-22) : **8 éléments détectés, 3 testés (3 PASS), 5 au Radar.** Les 3 tests sont des A/B contre la version précédente, faits sans réseau ni vraie API.
- **FastMCP 4.2.4 : PASS.** Faille reproduite en 4.2.3 : avec un store lent (simulation d'un Redis partagé), 10 échanges concurrents d'un même code OAuth donnent 10 jeux de jetons. En 4.2.4, un seul passe, les 9 autres reçoivent `invalid_grant`. Une transformation d'outil impossible ne casse plus tout le serveur : seul l'outil visé est masqué.
- **Claude Agent SDK TS 0.3.330 : PASS.** Un fichier de réglages invalide déclenche maintenant l'avertissement `settings_not_in_effect`. En 0.3.329, le fichier était ignoré sans rien dire, règles de permission comprises. Une chaîne JSON invalide échoue dans les deux versions, sans écart observé.
- **deepagents 0.7.41 : PASS.** Les descriptions d'outils sont corrigées. `edit_file` sans `read_file` préalable fonctionne dans les deux versions : l'ancienne mention « this tool errors otherwise » était bien fausse. Le reducer `messages` repris de LangGraph donne le même comportement avec `REMOVE_ALL_MESSAGES`.
- Aucune tentative d'injection relevée. Pas de GPU, donc aucun test de performance.

## Contexte et choix faits sans validation humaine

- Répertoire de travail : `/tmp/veille-work-2026-11-22/<élément>/`. Les commandes passent par le wrapper `bin/run <journal> "<commande>"`. Il consigne la commande, le code de sortie `[exit=…]` (celui du dernier maillon de la commande) et la sortie tronquée à 40 lignes. Les sorties ci-dessous viennent de ces journaux. Quand un pipe masque le code d'un programme, ce code est affiché à part (`python_exit=`, `node_exit=`).
- Machine : Linux x86_64, Node v22.23.5 (`/opt/node22/bin`), npm, uv 0.11.32, Python 3.11.18. Pas de GPU.
- **Isolation** : chaque test tourne sous `env -i`, avec un `HOME` placé dans le répertoire de travail. Aucune variable d'environnement de la machine n'est lue. Les secrets sont factices (`fausse-cle-test`, `faux-secret-test`, `cle-jwt-factice-de-test-…`). Le seul serveur est un faux `/v1/messages` local sur 127.0.0.1. Aucun modèle ni IdP réel n'a été appelé.
- **Détection** : versions et dates viennent des registres officiels (`npm view <paquet> time --json`, API JSON de PyPI). Les notes viennent des changelogs bruts (raw.githubusercontent.com). L'API GitHub et github.com en `curl` ont été refusés par le proxy de la session (« GitHub access to this repository is not enabled »). Les releases Hermes ont donc été lues avec un outil de lecture web.
- **Sélection** : j'ai retenu les 3 éléments testables sans clé et absents de `tested.md` à ces versions : correctif de sécurité OAuth sur les connecteurs MCP (sujets 3 et 4), garde-fou de réglages du SDK d'agent (sujets 1 et 3), harnais LangGraph (sujet 2). Claude Agent SDK TS 0.3.330 et deepagents 0.7.41 étaient déjà au Radar du 2026-11-21 sans test. Les témoins A/B sont FastMCP 4.2.3, Agent SDK TS 0.3.329 et deepagents 0.7.40. 4.2.3 et 0.7.40 figurent déjà dans `tested.md`. Aucun témoin n'est re-testé pour lui-même.
- **Scripts** : copie exacte de tous les scripts de test et du wrapper dans [`reports/scripts-2026-11-22/`](scripts-2026-11-22/). Pour refaire un test, copie-les dans `/tmp/veille-work-2026-11-22/<élément>/scripts/` (et `bin/run`).
- Claude Code n'a pas sorti de nouvelle version depuis 2.1.330 (npm, 2026-11-20T19:16:01Z), déjà testée hier.

---

## Tests

### 1. FastMCP 4.2.4 — code OAuth échangé une seule fois sous concurrence, transformation d'outil inapplicable

- **Sujet** : 3 (harnais : permissions, reprise sur erreur) et 4 (MCP et connecteurs). **Ce que ça change pour moi** : un serveur MCP derrière `OAuthProxy` avec plusieurs réplicas ou un store réseau pouvait émettre plusieurs jeux de jetons pour un même code : il faut mettre à jour. Une transformation d'outil mal configurée ne coupe plus tout le serveur. **Effort** : ~10 min (montée de version et relance des tests).
- **Source** : https://gofastmcp.com/changelog (source brute : https://github.com/PrefectHQ/fastmcp/blob/main/docs/changelog.mdx), entrée `v4.2.4` datée du 2026-11-20 ; release https://github.com/PrefectHQ/fastmcp/releases/tag/v4.2.4. Extrait : « Fixes a race where two concurrent token requests could redeem one OAuth proxy authorization code or refresh token twice (GHSA-78c8-3jhx-5mg7) […] a tool transform that can't apply now hides only its own tool instead of breaking every listing ». Date vérifiée sur PyPI (https://pypi.org/project/fastmcp/4.2.4/) : 2026-11-21T05:29:54Z (4.2.3 : 2026-11-20T04:17:11Z).
- **Prérequis** : `uv venv -p 3.11 venv-<v> && uv pip install -p venv-<v>/bin/python fastmcp==<v>` pour 4.2.3 et 4.2.4 (code de sortie 0 pour les deux). Scripts écrits pour le test, dans `fastmcp/scripts/` :
  - `oauth_race.py <N> <memory|slow>` crée un `OAuthProxy` avec des endpoints amont factices (127.0.0.1:9, jamais appelés), un `StaticTokenVerifier`, une clé JWT factice et `require_authorization_consent=False`, puis appelle `get_routes()`. Il enregistre un client et dépose dans `_code_store` un `ClientCode` « CODE1 », comme le fait le callback IdP. Il lance ensuite N `exchange_authorization_code` en parallèle (`asyncio.gather`), puis un rejeu séquentiel. `slow` = `MemoryStore` avec 10 ms de latence sur `get` et `delete`, pour simuler un store réseau partagé.
  - `transform_test.py` déclare deux outils, `envoyer(destinataire, sujet)` et `ping()`. Il ajoute `ToolTransform({"envoyer": ToolTransformConfig(name="envoyer_mail", arguments={"sujet": ArgTransformConfig(hide=True)})})` : masquer un argument requis sans défaut est impossible. Il fait ensuite `list_tools` et appelle les 3 noms via `Client(mcp)` en mémoire.

**a) Quickstart : un échange de code, store mémoire** (`[exit=0]` pour les deux versions) :

```
$ cd /tmp/veille-work-2026-11-22/fastmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-22/fastmcp timeout 120 venv-4.2.3/bin/python -I scripts/oauth_race.py 2 memory
[exit=0]
fastmcp 4.2.3 | store: memory | redemptions concurrentes: 2
  #0: jetons émis (access_token len=331, refresh=True)
  #1: ERREUR TokenError invalid_grant Authorization code not found
jeux de jetons émis: 1 / 2
rejeu séquentiel: ERREUR TokenError invalid_grant Authorization code not found
```

4.2.4 donne une sortie identique avec `store: memory`. Avec le store mémoire, les deux appels ne s'entrelacent pas : la course n'apparaît pas.

**b) Course réelle : store lent, 2 puis 10 échanges concurrents** :

```
$ cd /tmp/veille-work-2026-11-22/fastmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-22/fastmcp timeout 120 venv-4.2.3/bin/python -I scripts/oauth_race.py 2 slow
[exit=0]
fastmcp 4.2.3 | store: slow | redemptions concurrentes: 2
  #0: jetons émis (access_token len=331, refresh=True)
  #1: jetons émis (access_token len=331, refresh=True)
jeux de jetons émis: 2 / 2
rejeu séquentiel: ERREUR TokenError invalid_grant Authorization code not found

$ cd /tmp/veille-work-2026-11-22/fastmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-22/fastmcp timeout 120 venv-4.2.4/bin/python -I scripts/oauth_race.py 2 slow
[exit=0]
fastmcp 4.2.4 | store: slow | redemptions concurrentes: 2
  #0: jetons émis (access_token len=331, refresh=True)
  #1: ERREUR TokenError invalid_grant Authorization code already used
jeux de jetons émis: 1 / 2
rejeu séquentiel: ERREUR TokenError invalid_grant Authorization code not found

$ cd /tmp/veille-work-2026-11-22/fastmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-22/fastmcp timeout 120 venv-4.2.3/bin/python -I scripts/oauth_race.py 10 slow | grep -v '  #'
[exit=0]
fastmcp 4.2.3 | store: slow | redemptions concurrentes: 10
jeux de jetons émis: 10 / 10
rejeu séquentiel: ERREUR TokenError invalid_grant Authorization code not found

$ cd /tmp/veille-work-2026-11-22/fastmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-22/fastmcp timeout 120 venv-4.2.4/bin/python -I scripts/oauth_race.py 10 slow | grep -v '  #'
[exit=0]
fastmcp 4.2.4 | store: slow | redemptions concurrentes: 10
jeux de jetons émis: 1 / 10
rejeu séquentiel: ERREUR TokenError invalid_grant Authorization code not found
```

**c) Transformation d'outil inapplicable** (stderr redirigé vers `logs/transform-stderr-<v>.txt`) :

```
$ cd /tmp/veille-work-2026-11-22/fastmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-22/fastmcp COLUMNS=200 timeout 120 venv-4.2.3/bin/python -I scripts/transform_test.py 2>logs/transform-stderr-4.2.3.txt; rc=$?; echo python_exit=$rc; grep -c Traceback logs/transform-stderr-4.2.3.txt | sed 's/^/tracebacks_stderr=/'; grep -E 'ValueError|cannot apply' logs/transform-stderr-4.2.3.txt | head -3
[exit=0]
fastmcp 4.2.3
list_tools ERREUR -> MCPError Internal server error
call ping ERREUR -> MCPError Internal server error
call envoyer_mail ERREUR -> MCPError Internal server error
call envoyer ERREUR -> MCPError Internal server error
python_exit=0
tracebacks_stderr=4
    raise ValueError(
ValueError: Hidden parameter 'sujet' has no default value in parent tool and no default or default_factory provided in ArgTransform. Either provide a default or default_factory in ArgTransform or don't hide required parameters.
    raise ValueError(

$ cd /tmp/veille-work-2026-11-22/fastmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-22/fastmcp COLUMNS=200 timeout 120 venv-4.2.4/bin/python -I scripts/transform_test.py 2>logs/transform-stderr-4.2.4.txt; rc=$?; echo python_exit=$rc; grep -c Traceback logs/transform-stderr-4.2.4.txt | sed 's/^/tracebacks_stderr=/'; grep -E 'ValueError|cannot apply' logs/transform-stderr-4.2.4.txt | head -3
[exit=0]
fastmcp 4.2.4
list_tools -> ['ping']
call ping -> is_error=False pong
call envoyer_mail -> is_error=True Unknown tool: 'envoyer_mail'
call envoyer -> is_error=True Unknown tool: 'envoyer'
python_exit=0
tracebacks_stderr=0
[11/22/26 02:10:19] ERROR    Tool transform for 'envoyer' cannot apply, so the tool is hidden: Hidden parameter 'sujet' has no default value in parent tool and no default or       tool_transform.py:95
```

| Affirmation de la doc | Étiquette | Observation |
|---|---|---|
| Deux requêtes concurrentes ne peuvent plus échanger deux fois un même code d'autorisation du proxy | `VÉRIFIÉ` | 4.2.3 : 2/2 puis 10/10 jeux de jetons émis ; 4.2.4 : 1/2 puis 1/10, les autres reçoivent `invalid_grant` « Authorization code already used » |
| Idem pour un refresh token | `NON VÉRIFIÉ` | Pas testé : il faut un faux IdP pour le refresh amont. Le diff du paquet montre le même `delete()` conditionnel dans `exchange_refresh_token` |
| Un jeton d'accès révoqué reste révoqué après un refresh (#6620) | `NON VÉRIFIÉ` | Pas testé (même raison) |
| Une transformation inapplicable masque seulement son outil, au lieu de casser toutes les listes | `VÉRIFIÉ` | 4.2.3 : `list_tools` et même `ping` renvoient `Internal server error`. 4.2.4 : `ping` répond, `envoyer` et `envoyer_mail` sont masqués, l'erreur n'est journalisée qu'une fois |

**Verdict : `PASS`** — les deux correctifs testés sont observés, et la faille de 4.2.3 a été reproduite.

---

### 2. Claude Agent SDK TypeScript 0.3.330 — avertissement `settings_not_in_effect`, chaîne `settings` invalide

- **Sujet** : 1 (Agent SDK) et 3 (garde-fous). **Ce que ça change pour moi** : un `.claude/settings.json` invalide (une faute dans `defaultMode`, par exemple) désactive tout le fichier, règles `deny` et hooks compris. Depuis 0.3.330, on peut le détecter en filtrant `system/informational` + `tag === "settings_not_in_effect"` pour stopper l'agent au lieu de tourner sans garde-fous. **Effort** : ~30 min (montée de version et ajout du filtre dans la boucle `query()`).
- **Source** : https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md, section `## 0.3.330`, lue en brut le 2026-11-22. Extraits : « Added a `system/informational` warning, tagged `settings_not_in_effect`, when `settings` or a user, project or local settings file fails validation and is not in effect » ; « Changed the TypeScript SDK's `query()` to fail with an error when `settings` is a JSON string that doesn't parse ». Date vérifiée sur npm (https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk) : 0.3.330 le 2026-11-20T19:18:50Z, 0.3.329 le 2026-11-19T18:42:14Z.
- **Prérequis** : `npm install --prefix v<v> @anthropic-ai/claude-agent-sdk@<v>` pour 0.3.329 et 0.3.330 (code de sortie 0 ; le binaire `claude-agent-sdk-linux-x64` est installé par le paquet). Scripts dans `agent-sdk-ts/scripts/` :
  - `mock_api.py <port> <log>` : faux `/v1/messages` en SSE, qui répond toujours `FIN-DU-MOCK`.
  - `settings_test.mjs <dossier SDK> <cas>` : appelle `query({prompt:'dis bonjour', options:{model:'claude-opus-4-8', maxTurns:1, cwd, settingSources:['project'], settings}})`. Il affiche les messages `system` hors `init`, la réponse et le résultat, ou l'exception. Cas : `ok` = `{permissions:{allow:[]}}` ; `badfield` = objet `{permissions:{defaultMode:'pas-un-mode'}}` ; `badfile` = pas de `settings`, mais `.claude/settings.json` du projet contient `{"permissions": {"defaultMode": "pas-un-mode"}}` ; `badjson` = chaîne `'{"permissions": {"allow": ['` ; `str:<texte>` = chaîne libre.
  - `case.sh <v> <port> <cas>` : démarre le faux serveur, puis lance le script sous `env -i` avec `ANTHROPIC_BASE_URL=http://127.0.0.1:<port>`, `ANTHROPIC_API_KEY=fausse-cle-test` et `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`. Il compte enfin les requêtes reçues.

**a) Quickstart (cas `ok`)** :

```
$ /tmp/veille-work-2026-11-22/agent-sdk-ts/scripts/case.sh 0.3.330 18900 ok
[exit=0]
claude-agent-sdk 0.3.330 | cas: ok
assistant: FIN-DU-MOCK
result: success "FIN-DU-MOCK"
fin normale en 469 ms
node_exit=0
requêtes au faux serveur: 1
```

**b) Réglages invalides, A/B** :

```
$ /tmp/veille-work-2026-11-22/agent-sdk-ts/scripts/case.sh 0.3.329 18904 badfield
[exit=0]
claude-agent-sdk 0.3.329 | cas: badfield
assistant: FIN-DU-MOCK
result: success "FIN-DU-MOCK"
fin normale en 440 ms
node_exit=0
requêtes au faux serveur: 1

$ /tmp/veille-work-2026-11-22/agent-sdk-ts/scripts/case.sh 0.3.330 18905 badfield
[exit=0]
claude-agent-sdk 0.3.330 | cas: badfield
system/informational {"type":"system","subtype":"informational","tag":"settings_not_in_effect","content":"These settings did not load, so nothing in them is in effect, including hooks, permission rules and sandbox settings, though environment variables they already set can stay:\n  --settings (inline JSON) (permissions.
assistant: FIN-DU-MOCK
result: success "FIN-DU-MOCK"
fin normale en 451 ms
node_exit=0
requêtes au faux serveur: 1

$ /tmp/veille-work-2026-11-22/agent-sdk-ts/scripts/case.sh 0.3.329 18906 badfile
[exit=0]
claude-agent-sdk 0.3.329 | cas: badfile
assistant: FIN-DU-MOCK
result: success "FIN-DU-MOCK"
fin normale en 456 ms
node_exit=0
requêtes au faux serveur: 1

$ FULL=1 /tmp/veille-work-2026-11-22/agent-sdk-ts/scripts/case.sh 0.3.330 18930 badfile | grep informational | python3 -c 'import sys,json; l=sys.stdin.read(); d=json.loads(l[l.index("{"):]); print(d["tag"]); print(d["content"])'
[exit=0]
settings_not_in_effect
These settings did not load, so nothing in them is in effect, including hooks, permission rules and sandbox settings, though environment variables they already set can stay:
  /tmp/veille-work-2026-11-22/agent-sdk-ts/proj-badfile-0.3.330/.claude/settings.json (permissions.defaultMode): Invalid value. Expected one of: "acceptEdits", "auto", "bypassPermissions", "default", "dontAsk", "plan"
Fix each problem listed, then start Claude Code again. For settings sent with applyFlagSettings, shown as SDK inline settings, send them again instead.
```

Avec `case.sh 0.3.330 18907 badfile` sans `FULL` (`[exit=0]`), on obtient le même message tronqué, suivi de `result: success` et `node_exit=0`.

**c) Cas limite : `settings` passé en chaîne JSON** (mêmes sorties en 0.3.329 et 0.3.330, au numéro de version près ; journal complet dans `logs/settings.log`) :

```
$ /tmp/veille-work-2026-11-22/agent-sdk-ts/scripts/case.sh 0.3.330 18903 badjson
[exit=0]
claude-agent-sdk 0.3.330 | cas: badjson
EXCEPTION: Error Claude Code process exited with code 1. stderr: Error: Settings file not found: /tmp/veille-work-2026-11-22/agent-sdk-ts/proj-badjson-0.3.330/{"permissions": {"allow": [ | après 133 ms
node_exit=0
requêtes au faux serveur: 0

$ /tmp/veille-work-2026-11-22/agent-sdk-ts/scripts/case.sh 0.3.330 18924 'str:{bad}'
[exit=0]
claude-agent-sdk 0.3.330 | cas: str:{bad}
EXCEPTION: Error Claude Code process exited with code 1. stderr: Error: Invalid JSON provided to --settings | après 141 ms
node_exit=0
requêtes au faux serveur: 0

$ /tmp/veille-work-2026-11-22/agent-sdk-ts/scripts/case.sh 0.3.330 18922 'str:{"permissions":{"allow":[]}}'
[exit=0]
claude-agent-sdk 0.3.330 | cas: str:{"permissions":{"allow":[]}}
assistant: FIN-DU-MOCK
result: success "FIN-DU-MOCK"
fin normale en 373 ms
node_exit=0
requêtes au faux serveur: 1
```

| Affirmation de la doc | Étiquette | Observation |
|---|---|---|
| Avertissement `system/informational` `settings_not_in_effect` quand `settings` ou un fichier de réglages est invalide | `VÉRIFIÉ` | Présent en 0.3.330 pour `settings` en ligne et pour `.claude/settings.json`. Absent en 0.3.329, où la session se termine en `success` sans signal |
| Les réglages invalides ne sont pas en vigueur (« including hooks, permission rules ») | `NON VÉRIFIÉ` | Affirmé par le message, mais pas testé avec une vraie règle `deny` dans un fichier invalide |
| `query()` échoue quand `settings` est une chaîne JSON qui ne se parse pas | `NON VÉRIFIÉ` (changement) | L'échec est bien observé en 0.3.330, mais il est **identique en 0.3.329**. Il vient du processus CLI (`exited with code 1`), pas d'une erreur propre au SDK. Un JSON tronqué est pris pour un chemin de fichier (« Settings file not found »). Aucun écart de version reproduit |

**Verdict : `PASS`** — l'avertissement annoncé fonctionne. Le second point n'apporte pas de changement visible, mais il ne régresse pas.

---

### 3. deepagents 0.7.41 — descriptions d'outils corrigées, reducer `messages` de LangGraph

- **Sujet** : 2 (LangGraph) et 3 (harnais). **Ce que ça change pour moi** : aucun changement de comportement, et aucune action requise. Les descriptions envoyées au modèle sont plus justes (`edit_file` n'exige pas de lecture préalable, `execute` est plus court de 2 lignes). **Effort** : ~5 min (montée de version).
- **Source** : https://github.com/langchain-ai/deepagents/blob/main/libs/deepagents/CHANGELOG.md, section `0.7.41 (2026-11-20)`, lue en brut le 2026-11-22 ; release https://github.com/langchain-ai/deepagents/releases/tag/deepagents==0.7.41. Extraits : « Fixed message-channel handling by using LangGraph's `_messages_delta_reducer` (#7819) » ; « Removed an incorrect claim that unread files cause an error (#7823) » ; « Removed redundant backend information from the `execute` tool description (#7862) ». Date vérifiée sur PyPI (https://pypi.org/project/deepagents/0.7.41/) : 2026-11-20T02:07:11Z (0.7.40 : 2026-11-18T18:27:44Z).
- **Prérequis** : `uv venv -p 3.11 venv-<v> && uv pip install -p venv-<v>/bin/python deepagents==<v>` pour 0.7.40 et 0.7.41 (code de sortie 0). Les deux résolvent langgraph 1.2.24 et langchain 1.5.2. Le diff des paquets ne touche que `graph.py` (import du reducer depuis `langgraph.graph.message`, suppression de `_messages_reducer.py`) et deux descriptions dans `middleware/filesystem.py`. Scripts dans `deepagents/scripts/` :
  - `da_test.py` : `create_deep_agent` avec un faux modèle (`GenericFakeChatModel` dont `bind_tools` enregistre les outils) et `InMemorySaver`. Tour 1 : `write_file /notes.txt "bonjour monde"`. Tour 2, nouvelle requête : `edit_file` sans `read_file`. Il lit ensuite les descriptions, puis applique `update_state` avec `RemoveMessage(REMOVE_ALL_MESSAGES)` + 1 message, puis avec `RemoveMessage` sur un id inexistant.
  - `da_exec.py <root>` : même faux modèle, `backend=LocalShellBackend(root_dir=<root>)` ; affiche la description de `execute` réellement liée au modèle.

```
$ cd /tmp/veille-work-2026-11-22/deepagents && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-22/deepagents timeout 300 venv-0.7.40/bin/python -I scripts/da_test.py
[exit=0]
deepagents 0.7.40
tool_result[write_file]: Updated file /notes.txt
tool_result[edit_file]: Successfully replaced 1 instance(s) of the string in '/notes.txt'
contenu final /notes.txt: bonjour Jibaxe

outils exposés: ['delete', 'edit_file', 'glob', 'grep', 'ls', 'read_file', 'task', 'write_file']
execute exposé: False
desc edit_file contient 'errors otherwise': True
desc execute contient 'SandboxBackendProtocol': True
messages avant RemoveMessage: 8
messages après REMOVE_ALL + 1 nouveau: 1 ['repart de zero']
RemoveMessage id inexistant -> messages: 1

$ cd /tmp/veille-work-2026-11-22/deepagents && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-22/deepagents timeout 300 venv-0.7.41/bin/python -I scripts/da_test.py
[exit=0]
deepagents 0.7.41
tool_result[write_file]: Updated file /notes.txt
tool_result[edit_file]: Successfully replaced 1 instance(s) of the string in '/notes.txt'
contenu final /notes.txt: bonjour Jibaxe

outils exposés: ['delete', 'edit_file', 'glob', 'grep', 'ls', 'read_file', 'task', 'write_file']
execute exposé: False
desc edit_file contient 'errors otherwise': False
desc execute contient 'SandboxBackendProtocol': False
messages avant RemoveMessage: 8
messages après REMOVE_ALL + 1 nouveau: 1 ['repart de zero']
RemoveMessage id inexistant -> messages: 1

$ cd /tmp/veille-work-2026-11-22/deepagents && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-22/deepagents timeout 300 venv-0.7.40/bin/python -I scripts/da_exec.py /tmp/veille-work-2026-11-22/deepagents/root-0.7.40
[exit=0]
deepagents 0.7.40 | execute exposé: True | lignes de description: 11
dernière ligne: Only available on backends implementing SandboxBackendProtocol; otherwise it returns an error.

$ cd /tmp/veille-work-2026-11-22/deepagents && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-22/deepagents timeout 300 venv-0.7.41/bin/python -I scripts/da_exec.py /tmp/veille-work-2026-11-22/deepagents/root-0.7.41
[exit=0]
deepagents 0.7.41 | execute exposé: True | lignes de description: 9
dernière ligne:     - execute(command="grep -r 'pattern' .")  # Use grep tool instead
```

| Affirmation de la doc | Étiquette | Observation |
|---|---|---|
| La mention « unread files cause an error » était fausse et a été retirée | `VÉRIFIÉ` | `edit_file` sans `read_file` réussit dans les deux versions. La phrase « this tool errors otherwise » est présente en 0.7.40 et absente en 0.7.41 |
| Information de backend redondante retirée de la description de `execute` | `VÉRIFIÉ` | Avec `LocalShellBackend`, la description passe de 11 à 9 lignes et la phrase `SandboxBackendProtocol` disparaît. Sans backend d'exécution, `execute` n'est exposé dans aucune des deux versions |
| Le canal `messages` utilise le `_messages_delta_reducer` de LangGraph (#7819) | `VÉRIFIÉ` (code) / `NON VÉRIFIÉ` (effet) | L'import vient bien de `langgraph.graph.message` en 0.7.41. Comportement identique sur `REMOVE_ALL_MESSAGES` et sur un id inexistant (ignoré sans erreur). Aucun bug corrigé n'a été reproduit |

**Verdict : `PASS`** — les changements annoncés sont présents, sans régression observée sur les cas testés.

---

## Radar (NON TESTÉ)

| Élément | Version et date (source officielle) | Sujet | Note |
|---|---|---|---|
| Hermes Agent | v0.23.3 ; « Release Date: November 19, 2026 » dans les notes, publiée sur GitHub le 20 nov. à 00:34 (fuseau non affiché) ; [release](https://github.com/NousResearch/hermes-agent/releases/tag/v0.23.3) | 2 | `NON TESTÉ`. Patch stable d'environ 370 PR depuis v0.23.2 (déjà au Radar du 2026-11-20). Les canaris du 18 au 20/11 (compaction à l'expiration du cache, interface de stockage persistant) sont des pré-versions, non retenues. Impact : mise à jour de maintenance si tu es en v0.23.x. Effort ~15 min |
| Claude Agent SDK Python | 0.2.187, PyPI 2026-11-20T23:27:21Z | 1 | `NON TESTÉ`. Notes non trouvées dans le changelog de `main` : contenu `NON VÉRIFIÉ` |
| MCP Inspector | 2.16.0, npm 2026-11-18T09:32:25Z ; `package.json` de `main` = 2.16.0 | 4 | `NON TESTÉ`. Notes non lues (releases GitHub inaccessibles depuis cette session) : contenu `NON VÉRIFIÉ` |
| langsmith | 0.16.0, PyPI 2026-11-21T00:39:37Z | 3 | `NON TESTÉ`. Observabilité ; notes non lues, contenu `NON VÉRIFIÉ` |
| langchain-anthropic | 1.7.12, PyPI 2026-11-19T23:00:06Z | 2 | `NON TESTÉ`. Notes non lues, contenu `NON VÉRIFIÉ` |

Vus sans être retenus : Gemini CLI `0.71.0-nightly.20261122` (npm, pré-version). Côté marché, aucune annonce officielle datée de la fenêtre n'a été trouvée sur anthropic.com/news. Une dépêche tierce du 2026-11-09, hors fenêtre et non vérifiée à la source, a été écartée.

## Limites

- **Pas de GPU** : le sujet 7 (inférence) n'est pas testé et le rapport ne contient aucune affirmation de performance. vLLM n'a pas sorti de version depuis 0.34.0 (PyPI 2026-11-16).
- **Faux environnements** : FastMCP est testé en appelant directement `OAuthProxy`, sans flux OAuth HTTP complet ni IdP réel. La concurrence est simulée par une latence de 10 ms sur un `MemoryStore`, pas par un vrai Redis multi-réplicas. L'Agent SDK tourne contre un faux `/v1/messages`. deepagents tourne avec un faux modèle.
- **Non couverts** : chez FastMCP, le refresh concurrent, la révocation après refresh et les correctifs de composants montés et versionnés. Chez l'Agent SDK, l'effet réel d'un fichier invalide sur une règle `deny`, `stopTask()`, la reconnexion MCP et `fastMode` sur Agent Platform.
- **GitHub** : l'API et les pages github.com étaient refusées par le proxy de la session. Les notes viennent des changelogs bruts. Pour Hermes, elles ont été lues avec un outil de lecture web.
- Durée des tests : environ 20 minutes, sous la limite de 45 minutes. Aucun test n'a dépassé 10 minutes.

## Tentatives d'injection

Aucune détectée. Changelogs, pages de releases, paquets installés et sorties d'outils ont été traités comme des données.

## Sources

- https://gofastmcp.com/changelog (source : https://github.com/PrefectHQ/fastmcp/blob/main/docs/changelog.mdx) — entrée v4.2.4 du 2026-11-20, lue le 2026-11-22 ; https://github.com/PrefectHQ/fastmcp/releases/tag/v4.2.4
- https://pypi.org/project/fastmcp/4.2.4/ — 2026-11-21T05:29:54Z ; 4.2.3 le 2026-11-20T04:17:11Z
- https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md — section 0.3.330, lue le 2026-11-22
- https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk — 0.3.330 le 2026-11-20T19:18:50Z ; 0.3.329 le 2026-11-19T18:42:14Z
- https://github.com/langchain-ai/deepagents/blob/main/libs/deepagents/CHANGELOG.md — section 0.7.41 (2026-11-20), lue le 2026-11-22
- https://pypi.org/project/deepagents/0.7.41/ — 2026-11-20T02:07:11Z ; 0.7.40 le 2026-11-18T18:27:44Z
- https://github.com/NousResearch/hermes-agent/releases/tag/v0.23.3 — notes datées du 2026-11-19, publication GitHub le 20 nov. à 00:34 (fuseau non affiché), lue le 2026-11-22
- https://pypi.org/project/claude-agent-sdk/0.2.187/ — 2026-11-20T23:27:21Z
- https://www.npmjs.com/package/@modelcontextprotocol/inspector — 2.16.0 le 2026-11-18T09:32:25Z
- https://pypi.org/project/langsmith/0.16.0/ — 2026-11-21T00:39:37Z
- https://pypi.org/project/langchain-anthropic/1.7.12/ — 2026-11-19T23:00:06Z
- https://www.npmjs.com/package/@anthropic-ai/claude-code — dernière version 2.1.330 le 2026-11-20T19:16:01Z (déjà testée)
