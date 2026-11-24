# Veille IA — 2026-11-24

## TL;DR

- **Run du 2026-11-24** (fenêtre du 2026-11-17 au 2026-11-24) : **8 éléments détectés, 3 testés (3 PASS), 5 au Radar.** Les 3 tests sont des A/B contre la version précédente. Ils tournent contre de faux serveurs locaux, sans vraie API.
- **Claude Code 2.1.331 : PASS.** Un `tool_use` sans clé `name` fait planter la session en 2.1.330 (`TypeError … I.name.startsWith`, `session_crash`, sortie 1). En 2.1.331, l'appel échoue proprement et la session continue (`success`, sortie 0). `claude doctor` gagne une section « API connectivity » (HTTP 200 / ECONNREFUSED / « Not tested »), mais son code de sortie reste 0 même quand l'API est injoignable.
- **FastMCP 4.2.5 : PASS.** Les outils OpenAPI ne transmettent plus `mcp-protocol-version`, `mcp-method` ni `mcp-name` au backend. `forward_client_headers=False` ou une liste filtre bien les en-têtes du client. Les URI de redirection OAuth sont plus strictes : 3 cas acceptés en 4.2.4 sont refusés en 4.2.5.
- **anthropic (SDK Python) 2.13.0 : PASS.** `claude-opus-4-5` déclenche maintenant un `DeprecationWarning` (fin de vie : 22 janvier 2027). Les modèles retirés (`claude-3-opus-20240229`, `claude-opus-4-0`) n'en déclenchent plus. `claude-mythos-preview` (fin de vie : 30 juin 2026, date passée) en déclenche encore.
- Aucune tentative d'injection relevée. Pas de GPU, donc aucun test de performance.

## Contexte et choix faits sans validation humaine

- Répertoire de travail : `/tmp/veille-work-2026-11-24/<élément>/` (`cc`, `fmcp`, `anth`). Les commandes passent par le wrapper `bin/run <journal> "<commande>"`. Il consigne la commande, le code de sortie `[exit=…]` (celui du dernier maillon d'un pipe) et la sortie tronquée à 40 lignes. Quand un script masque le code d'un programme, ce code est affiché à part (`cli_exit=`).
- Machine : Linux x86_64, Node v22 (`/opt/node22/bin`), npm, uv, Python 3.11. Pas de GPU.
- **Isolation** : Claude Code tourne sous `env -i`, avec un `HOME` placé dans le répertoire de travail et la clé factice `fausse-cle-test`. Les scripts Python tournent avec `python -I` et s'adressent uniquement à des serveurs sur 127.0.0.1. Aucune variable d'environnement de la machine n'est lue. Aucun modèle réel n'a été appelé.
- **Détection** : versions et dates viennent des registres officiels (`npm view <paquet> time --json`, API JSON de PyPI). Les notes viennent des changelogs bruts sur raw.githubusercontent.com et de la page des releases Hermes (lue avec un outil de lecture web). Les requêtes `curl` vers github.com reçoivent un 403 du proxy.
- **Sélection** : j'ai retenu les 3 éléments à la fois pertinents pour `topics.md` et testables sans clé. Ce sont Claude Code 2.1.331 (sujet 1), FastMCP 4.2.5 (sujets 3 et 4 : sécurité OAuth/OpenAPI) et le SDK Python d'Anthropic 2.13.0 (sujet 5 : dépréciation d'Opus 4.5, qui touche une décision de modèle). Aucun ne figure dans `tested.md` à ces versions. L'Agent SDK TS 0.3.331 et l'Agent SDK Python 0.2.188 suivent la CLI 2.1.331 ; ils vont au Radar pour éviter de tester deux fois la même chose.
- **Scripts** : copie exacte dans [`reports/scripts-2026-11-24/`](scripts-2026-11-24/). Pour refaire un test, copie-les dans `/tmp/veille-work-2026-11-24/<élément>/scripts/` (et `run` dans `/tmp/veille-work-2026-11-24/bin/`) : les chemins sont écrits en dur.

---

## Tests

### 1. Claude Code 2.1.331 — tool_use sans nom, section API de `claude doctor`

- **Sujet** : 1 (Claude Code) et 3 (reprise sur erreur). **Ce que ça change pour moi** : derrière une passerelle ou un modèle tiers qui renvoie un `tool_use` mal formé, une tâche planifiée ne plante plus. Elle continue avec une erreur d'outil. `claude doctor` sert à diagnostiquer la connectivité, mais il ne peut pas servir de garde en CI : il sort en 0 même quand l'API est injoignable. **Effort** : ~5 min (mise à jour).
- **Source** : https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md, section 2.1.331. Date vérifiée sur npm : 2.1.331 publiée le 2026-11-23T18:36:26Z (2.1.330 : 2026-11-20T19:16:01Z).
- **Prérequis** : `npm install --prefix v<v> --no-audit --no-fund @anthropic-ai/claude-code@<v>` pour 2.1.330 et 2.1.331 (`[exit=0]`, « added 2 packages »). Scripts :
  - `mock_api.py <port> <log> <mode>` : faux `/v1/messages` en SSE. En mode `ok`, il répond `FIN-DU-MOCK`. En mode `nokey`, la 1ʳᵉ réponse est un `tool_use` **sans clé `name`** ; en mode `noname`, le `name` est `""`. Dès que la requête contient un `tool_result`, le serveur répond `FIN-DU-MOCK`. Il consigne chaque requête et le `tool_result` reçu.
  - `case.sh <v> <mode> <args…>` : lance le faux serveur sur 127.0.0.1:18931, puis `claude <args>` sous `env -i` avec `ANTHROPIC_BASE_URL`, une clé factice, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` (retiré si `NT=` est passé) et `timeout ${T:-120}`. En mode `down`, aucun serveur n'est lancé.

**a) Quickstart : `claude -p` sur le faux serveur**

```
$ /tmp/veille-work-2026-11-24/cc/scripts/case.sh 2.1.330 ok -p 'dis bonjour' --model claude-opus-4-8
[exit=0]
FIN-DU-MOCK
cli_exit=0
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 tool_result=-

$ /tmp/veille-work-2026-11-24/cc/scripts/case.sh 2.1.331 ok -p 'dis bonjour' --model claude-opus-4-8
[exit=0]
FIN-DU-MOCK
cli_exit=0
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 tool_result=-
```

**b) « Fixed a crash when a custom API endpoint returned a tool call with no tool name; the call now fails with an error and the session continues »**. Le filtre `result_filter.py` (copié dans `reports/scripts-2026-11-24/cc/`) garde 5 champs du JSON de résultat et coupe les autres lignes à 300 caractères :

```
$ T=30 /tmp/veille-work-2026-11-24/cc/scripts/case.sh 2.1.330 nokey -p 'dis bonjour' --model claude-opus-4-8 --output-format json 2>&1 | python3 -I /tmp/veille-work-2026-11-24/cc/scripts/result_filter.py
[exit=0]
{'subtype': 'error_during_execution', 'is_error': True, 'num_turns': 0, 'result': None, 'errors': ["undefined is not an object (evaluating 'I.name.startsWith')", '[session_crash] error_name=TypeError api_error_status=none cause_name=none']}
cli_exit=1
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 tool_result=-
  POST /v1/messages?beta=true n=2 tool_result=[{"type": "tool_result", "content": "<tool_use_error>Error: No such tool available: undefined</tool_use_error>", "is_error": true, "tool_use_id": "toolu_mock1"}]

$ T=30 /tmp/veille-work-2026-11-24/cc/scripts/case.sh 2.1.331 nokey -p 'dis bonjour' --model claude-opus-4-8 --output-format json 2>&1 | python3 -I /tmp/veille-work-2026-11-24/cc/scripts/result_filter.py
[exit=0]
{'subtype': 'success', 'is_error': False, 'num_turns': 2, 'result': 'FIN-DU-MOCK', 'errors': None}
cli_exit=0
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 tool_result=-
  POST /v1/messages?beta=true n=2 tool_result=[{"type": "tool_result", "content": "<tool_use_error>Error: No such tool available: tool_name_missing. The call arrived with no tool name; tool_name_missing is a placeholder for it. Call the tool you
```

Cas limite, `name: ""` (chaîne vide), mode `noname` : **pas d'écart**, aucune des deux versions ne plante.

```
$ T=30 /tmp/veille-work-2026-11-24/cc/scripts/case.sh 2.1.330 noname -p 'dis bonjour' --model claude-opus-4-8 --output-format json 2>&1 | python3 -I /tmp/veille-work-2026-11-24/cc/scripts/result_filter.py
[exit=0]
{'subtype': 'success', 'is_error': False, 'num_turns': 2, 'result': 'FIN-DU-MOCK', 'errors': None}
cli_exit=0
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 tool_result=-
  POST /v1/messages?beta=true n=2 tool_result=[{"type": "tool_result", "content": "<tool_use_error>Error: No such tool available: </tool_use_error>", "is_error": true, "tool_use_id": "toolu_mock1"}]

$ T=30 /tmp/veille-work-2026-11-24/cc/scripts/case.sh 2.1.331 noname -p 'dis bonjour' --model claude-opus-4-8 --output-format json 2>&1 | python3 -I /tmp/veille-work-2026-11-24/cc/scripts/result_filter.py
[exit=0]
{'subtype': 'success', 'is_error': False, 'num_turns': 2, 'result': 'FIN-DU-MOCK', 'errors': None}
cli_exit=0
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 tool_result=-
  POST /v1/messages?beta=true n=2 tool_result=[{"type": "tool_result", "content": "<tool_use_error>Error: No such tool available: </tool_use_error>", "is_error": true, "tool_use_id": "toolu_mock1"}]
```

Ligne d'avertissement de 2.1.331 dans le journal de débogage :

```
$ T=8 /tmp/veille-work-2026-11-24/cc/scripts/case.sh 2.1.331 nokey -p 'dis bonjour' --model claude-opus-4-8 --debug-file /tmp/veille-work-2026-11-24/cc/logs/debug-2.1.331.log >/dev/null 2>&1; grep -m1 -o 'WARN.*' /tmp/veille-work-2026-11-24/cc/logs/debug-2.1.331.log
[exit=0]
WARN] the API host sent a tool_use block with no string name; stored it as tool_name_missing, so the call will fail with "No such tool available"
```

*Incident sur mon propre script* : au premier lancement, mon faux serveur ne cherchait le `tool_result` que dans le dernier bloc du dernier message. Il renvoyait donc le `tool_use` à chaque requête, et les deux versions bouclaient jusqu'au `timeout` (`cli_exit=124`, 1 763 requêtes en 120 s pour 2.1.330). Ce comportement venait de mon serveur, pas de Claude Code. Après correction (recherche dans tous les messages `user`), on obtient les résultats ci-dessus. Les quatre cas `nokey`/`noname` ont été relancés une seconde fois avec le filtre enregistré en script, et ont donné une sortie identique.

**c) « Added an API connectivity section to `claude doctor` that reports whether the API can be reached, with the HTTP status or the error, or says why it wasn't tested »**

```
$ T=40 /tmp/veille-work-2026-11-24/cc/scripts/case.sh 2.1.331 ok doctor 2>&1 | grep -v '^\s*$' | cut -c1-200
[exit=0]
Claude Code doctor
Running: npm-global (2.1.331)
Commit: 3c6b6136f768
Platform: linux-x64
Path: /tmp/veille-work-2026-11-24/cc/v2.1.331/node_modules/@anthropic-ai/claude-code/bin/claude.exe
Config install method: unknown
Search: OK (bundled)
Auto-updates: disabled (set by env: CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC)
Auto-update channel: latest
Last update attempt: none recorded
Managed settings (remote): not fetched — not available with a custom ANTHROPIC_BASE_URL
Organization policy: not fetched with a custom ANTHROPIC_BASE_URL
API connectivity
- Not tested: CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC is set
Remote Control
Remote Control is only available when using Claude via api.anthropic.com. ANTHROPIC_BASE_URL is set and does not point at api.anthropic.com, so this session is using a custom endpoint — unset it (or
- Not connected to the Anthropic API (api.anthropic.com)
- claude.ai subscription auth not active
- Sign-in is missing the user:profile scope
- Organization not found
- Feature-flag evaluation disabled (disabled by CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC)
- Remote Control availability could not be verified (no server response this session)
No installation issues found.
For a full setup checkup that can also fix issues, run /doctor in a Claude Code session.
cli_exit=0
--- requêtes au faux serveur :

$ NT= T=60 /tmp/veille-work-2026-11-24/cc/scripts/case.sh 2.1.331 ok doctor 2>&1 | grep -v '^\s*$' | sed -n '/API connectivity/,/Remote Control/p;/cli_exit/,$p' | cut -c1-200
[exit=0]
API connectivity
- API (custom host): answered HTTP 200 in 2 ms
- ANTHROPIC_BASE_URL: set to a custom host · NODE_EXTRA_CA_CERTS: not set · CLAUDE_CODE_CLIENT_CERT: not set
Remote Control
cli_exit=0
--- requêtes au faux serveur :
  HEAD /api/hello
  GET /api/hello

$ NT= T=60 /tmp/veille-work-2026-11-24/cc/scripts/case.sh 2.1.331 down doctor 2>&1 | grep -v '^\s*$' | sed -n '/API connectivity/,/Remote Control/p;/cli_exit/,$p' | cut -c1-200
[exit=0]
API connectivity
- API (custom host): failed after 1 ms: Connection refused — a firewall or proxy may be blocking it (ECONNREFUSED)
- ANTHROPIC_BASE_URL: set to a custom host · NODE_EXTRA_CA_CERTS: not set · CLAUDE_CODE_CLIENT_CERT: not set
  A proxy, firewall, VPN or security software between this machine and the host can cause these results. See https://code.claude.com/docs/en/network-config
Remote Control
cli_exit=0
--- requêtes au faux serveur :

$ NT= T=60 /tmp/veille-work-2026-11-24/cc/scripts/case.sh 2.1.330 down doctor 2>&1 | grep -ciE 'API connectivity|custom host'
[exit=1]
0
```

(Dernière commande : avec 2.1.330, `grep -c` ne compte aucune ligne « API connectivity » ou « custom host », d'où `exit=1`.)

| Affirmation (changelog 2.1.331) | Statut |
|---|---|
| Crash sur un tool call sans nom corrigé ; l'appel échoue avec une erreur, la session continue | `VÉRIFIÉ` (clé `name` absente : crash en 2.1.330, succès en 2.1.331 ; `name: ""` : pas de crash, même en 2.1.330) |
| `claude doctor` indique si l'API est joignable, avec le statut HTTP | `VÉRIFIÉ` (HTTP 200 en 2 ms) |
| … ou l'erreur | `VÉRIFIÉ` (ECONNREFUSED) |
| … ou la raison de l'absence de test | `VÉRIFIÉ` (« Not tested: CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC is set ») |
| Code de sortie de `claude doctor` selon la connectivité | Non promis par la doc ; observé : 0 dans les trois cas |

**Verdict : PASS** — les deux changements testés se comportent comme annoncé ; A/B net contre 2.1.330 sur le crash.

### 2. FastMCP 4.2.5 — en-têtes transmis par les outils OpenAPI, URI de redirection OAuth

- **Sujet** : 3 (harnais, permissions) et 4 (MCP). **Ce que ça change pour moi** : si j'expose une API REST via `FastMCP.from_openapi`, les en-têtes du client MCP (par exemple un jeton maison) partent encore par défaut vers le backend. `forward_client_headers=["…"]` permet maintenant d'en restreindre la liste. Côté OAuth, un motif `https://hôte/` ne couvre plus les sous-chemins : il faut ajouter `/*`. **Effort** : ~30 min pour relire ses motifs de redirection et poser `forward_client_headers`.
- **Source** : changelog https://github.com/PrefectHQ/fastmcp/blob/main/docs/changelog.mdx (bloc `v4.2.5`, `description="2026-11-23"`), release https://github.com/PrefectHQ/fastmcp/releases/tag/v4.2.5. Date vérifiée sur PyPI (https://pypi.org/project/fastmcp/4.2.5/) : 2026-11-23T07:42:40Z (4.2.4 : 2026-11-21T05:29:54Z).
- **Prérequis** : `uv venv -q venv-<v> --python 3.11 && uv pip install -q --python venv-<v>/bin/python fastmcp==<v>` pour 4.2.4 et 4.2.5. Code `[exit=0]` dans les deux cas, et `fastmcp.__version__` affiche bien `4.2.4` et `4.2.5`. Scripts :
  - `hdr_test.py <mode>` : faux backend HTTP sur 127.0.0.1:18941, qui consigne les en-têtes reçus. Il est exposé par `FastMCP.from_openapi` (une route `GET /ping`), servi en HTTP sur 127.0.0.1:18942. Un `fastmcp.Client` l'appelle avec `X-Tenant: acme` et `X-Secret-Client: ne-pas-transmettre`. Le paramètre `mode` vaut `default` (aucun argument), `false` (`forward_client_headers=False`) ou `list` (`["x-tenant"]`). Le script affiche les en-têtes `mcp-*` et `x-*` reçus par le backend. Le stderr part dans `logs/` : on y trouve seulement une trace `CancelledError` à l'arrêt volontaire du serveur.
  - `redirect_test.py` : appelle `fastmcp.server.auth.redirect_validation.matches_allowed_pattern(uri, motif)` sur 7 cas tirés des notes.

**a) Quickstart et en-têtes transmis (comportement par défaut)**

```
$ cd /tmp/veille-work-2026-11-24/fmcp && timeout 60 venv-4.2.4/bin/python -I scripts/hdr_test.py default 2>logs/stderr-4.2.4-default.log
[exit=0]
fastmcp 4.2.4 | mode default | kwargs {}
résultat outil: {'ok': True}
en-têtes reçus par le backend: {"mcp-method": "tools/call", "mcp-name": "ping", "mcp-protocol-version": "2026-07-28", "x-secret-client": "ne-pas-transmettre", "x-tenant": "acme"}

$ cd /tmp/veille-work-2026-11-24/fmcp && timeout 60 venv-4.2.5/bin/python -I scripts/hdr_test.py default 2>logs/stderr-4.2.5-default.log
[exit=0]
fastmcp 4.2.5 | mode default | kwargs {}
résultat outil: {'ok': True}
en-têtes reçus par le backend: {"x-secret-client": "ne-pas-transmettre", "x-tenant": "acme"}
```

**b) Option `forward_client_headers`**

```
$ cd /tmp/veille-work-2026-11-24/fmcp && timeout 60 venv-4.2.4/bin/python -I scripts/hdr_test.py false 2>logs/stderr-4.2.4-false.log
[exit=3]
fastmcp 4.2.4 | mode false | kwargs {'forward_client_headers': False}
TypeError: FastMCP() got unexpected keyword argument(s): 'forward_client_headers'

$ cd /tmp/veille-work-2026-11-24/fmcp && timeout 60 venv-4.2.5/bin/python -I scripts/hdr_test.py false 2>logs/stderr-4.2.5-false.log
[exit=0]
fastmcp 4.2.5 | mode false | kwargs {'forward_client_headers': False}
résultat outil: {'ok': True}
en-têtes reçus par le backend: {}

$ cd /tmp/veille-work-2026-11-24/fmcp && timeout 60 venv-4.2.5/bin/python -I scripts/hdr_test.py list 2>logs/stderr-4.2.5-list.log
[exit=0]
fastmcp 4.2.5 | mode list | kwargs {'forward_client_headers': ['x-tenant']}
résultat outil: {'ok': True}
en-têtes reçus par le backend: {"x-tenant": "acme"}
```

```
$ cd /tmp/veille-work-2026-11-24/fmcp && timeout 60 venv-4.2.4/bin/python -I scripts/hdr_test.py list 2>logs/stderr-4.2.4-list.log
[exit=3]
fastmcp 4.2.4 | mode list | kwargs {'forward_client_headers': ['x-tenant']}
TypeError: FastMCP() got unexpected keyword argument(s): 'forward_client_headers'
```

**c) Cas limite : validation des URI de redirection OAuth**

```
$ cd /tmp/veille-work-2026-11-24/fmcp && venv-4.2.4/bin/python -I scripts/redirect_test.py
[exit=0]
fastmcp 4.2.4
True   uri=https://app.example/             motif=https://app.example/
True   uri=https://app.example/callback     motif=https://app.example/
True   uri=https://app.example/callback     motif=https://app.example/*
True   uri=https://app.example/cb?x=1       motif=https://app.example/cb?x=1
True   uri=https://app.example/cb?x=2       motif=https://app.example/cb?x=1
True   uri=https://app.example/cb#frag      motif=https://app.example/cb
True   uri=http://localhost:5555/cb         motif=http://localhost/cb

$ cd /tmp/veille-work-2026-11-24/fmcp && venv-4.2.5/bin/python -I scripts/redirect_test.py
[exit=0]
fastmcp 4.2.5
True   uri=https://app.example/             motif=https://app.example/
False  uri=https://app.example/callback     motif=https://app.example/
True   uri=https://app.example/callback     motif=https://app.example/*
True   uri=https://app.example/cb?x=1       motif=https://app.example/cb?x=1
False  uri=https://app.example/cb?x=2       motif=https://app.example/cb?x=1
False  uri=https://app.example/cb#frag      motif=https://app.example/cb
True   uri=http://localhost:5555/cb         motif=http://localhost/cb
```

| Affirmation (notes v4.2.5) | Statut |
|---|---|
| Les outils OpenAPI ne transmettent plus les en-têtes de transport MCP (`mcp-protocol-version`…) | `VÉRIFIÉ` (`mcp-method`, `mcp-name` et `mcp-protocol-version` présents en 4.2.4, absents en 4.2.5) |
| `forward_client_headers=False` ne transmet aucun en-tête client | `VÉRIFIÉ` |
| Une liste ne transmet que les en-têtes nommés | `VÉRIFIÉ` (`x-tenant` seul) |
| Par défaut, les autres en-têtes du client restent transmis | `VÉRIFIÉ` (`x-secret-client` transmis en 4.2.5 par défaut) |
| Un motif exact à la racine d'un hôte ne couvre que ce chemin ; `/*` pour tout chemin | `VÉRIFIÉ` |
| La query d'un motif exact doit correspondre | `VÉRIFIÉ` |
| Une URI avec fragment est refusée | `VÉRIFIÉ` |
| Les motifs loopback sans port sont inchangés | `VÉRIFIÉ` (localhost:5555 accepté dans les deux versions) |
| Flux `subscriptions/listen`, `UsageMiddleware`, rotation de refresh token, CIMD, Azure | `NON VÉRIFIÉ` (non testés) |

**Verdict : PASS** — 8 affirmations testées, toutes vérifiées, avec écart A/B net contre 4.2.4.

### 3. anthropic (SDK Python) 2.13.0 — avertissements de dépréciation des modèles

- **Sujet** : 5 (marché, modèles) et 1 (API). **Ce que ça change pour moi** : Opus 4.5 atteint sa fin de vie le 22 janvier 2027, et le SDK le signale désormais à chaque appel. Tout script épinglé sur `claude-opus-4-5` est à migrer avant cette date. **Effort** : ~15 min pour chercher `claude-opus-4-5` dans les projets et le remplacer.
- **Source** : https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md, section `2.13.0 (2026-11-23)`. Extraits : « mark Claude Opus 4.5 as deprecated (end-of-life January 22, 2027) » ; « read deprecated models from generated data and stop warning on retired ones ». Date vérifiée sur PyPI (https://pypi.org/project/anthropic/2.13.0/) : 2026-11-23T18:35:01Z (2.12.0 : 2026-11-20T15:57:01Z).
- **Prérequis** : `uv venv -q venv-<v> --python 3.11 && uv pip install -q --python venv-<v>/bin/python anthropic==<v>` pour 2.12.0 et 2.13.0. Code `[exit=0]`, et `anthropic.__version__` affiche bien `2.12.0` et `2.13.0`. Script `depr_test.py` : un faux `/v1/messages` local (127.0.0.1:18951) répond « ok ». `messages.create` est appelé sur 7 modèles. Le script affiche le 1er `DeprecationWarning` émis.

```
$ cd /tmp/veille-work-2026-11-24/anth && timeout 60 venv-2.12.0/bin/python -I scripts/depr_test.py
[exit=0]
anthropic 2.12.0
claude-opus-4-5              réponse=ok avertissement=aucun
claude-opus-4-5-20251101     réponse=ok avertissement=aucun
claude-sonnet-4-5            réponse=ok avertissement=The model 'claude-sonnet-4-5' is deprecated and will reach end-of-life on November 30th, 2026.
claude-3-opus-20240229       réponse=ok avertissement=The model 'claude-3-opus-20240229' is deprecated and will reach end-of-life on January 5th, 2026.
claude-opus-4-0              réponse=ok avertissement=The model 'claude-opus-4-0' is deprecated and will reach end-of-life on June 15th, 2026.
claude-mythos-preview        réponse=ok avertissement=The model 'claude-mythos-preview' is deprecated and will reach end-of-life on June 30th, 2026.
claude-opus-4-8              réponse=ok avertissement=aucun

$ cd /tmp/veille-work-2026-11-24/anth && timeout 60 venv-2.13.0/bin/python -I scripts/depr_test.py
[exit=0]
anthropic 2.13.0
claude-opus-4-5              réponse=ok avertissement=The model 'claude-opus-4-5' is deprecated and will reach end-of-life on January 22nd, 2027.
claude-opus-4-5-20251101     réponse=ok avertissement=The model 'claude-opus-4-5-20251101' is deprecated and will reach end-of-life on January 22nd, 2027.
claude-sonnet-4-5            réponse=ok avertissement=The model 'claude-sonnet-4-5' is deprecated and will reach end-of-life on November 30th, 2026.
claude-3-opus-20240229       réponse=ok avertissement=aucun
claude-opus-4-0              réponse=ok avertissement=aucun
claude-mythos-preview        réponse=ok avertissement=The model 'claude-mythos-preview' is deprecated and will reach end-of-life on June 30th, 2026.
claude-opus-4-8              réponse=ok avertissement=aucun
```

Contrôle du paquet : la liste vient de `anthropic/_data/deprecated_models.py` (nouveau module) en 2.13.0, et du dictionnaire `DEPRECATED_MODELS` de `resources/messages/messages.py` en 2.12.0.

```
$ cd /tmp/veille-work-2026-11-24/anth && venv-2.13.0/bin/python -I -c 'from anthropic._data import DEPRECATED_MODELS as D; print(len(D)); print(sorted(D))' && venv-2.12.0/bin/python -I -c 'from anthropic.resources.messages.messages import DEPRECATED_MODELS as D; print(len(D))'
[exit=0]
5
['claude-mythos-preview', 'claude-opus-4-5', 'claude-opus-4-5-20251101', 'claude-sonnet-4-5', 'claude-sonnet-4-5-20250929']
20
```

| Affirmation (changelog 2.13.0) | Statut |
|---|---|
| Opus 4.5 marqué déprécié, fin de vie le 22 janvier 2027 | `VÉRIFIÉ` (avertissement avec cette date pour l'alias et l'ID daté) |
| Modèles dépréciés lus depuis des données générées | `VÉRIFIÉ` (nouveau module `_data/deprecated_models.py`) |
| Plus d'avertissement pour les modèles retirés | `VÉRIFIÉ` pour `claude-3-opus-20240229` et `claude-opus-4-0`. Pour `claude-mythos-preview`, la date du 30 juin 2026 est passée mais l'avertissement reste ; je n'ai pas pu vérifier si ce modèle est officiellement retiré (`NON VÉRIFIÉ`) |
| « build the right class for tool results with unknown values » | `NON VÉRIFIÉ` (non testé) |

**Verdict : PASS** — les comportements annoncés et testés sont observés, avec écart A/B net contre 2.12.0.

---

## Radar (NON TESTÉ)

| Élément | Version et date (source officielle) | Sujet | Note |
|---|---|---|---|
| Claude Agent SDK TypeScript | 0.3.331, npm 2026-11-23T18:35:23Z ; [CHANGELOG](https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md) | 1 | `NON TESTÉ`. Parité avec la CLI 2.1.331 (testée plus haut). `rewindFiles()` refuse de tourner quand `fileCheckpointingEnabled: false` est imposé ; `listSessions()` n'ouvre plus tous les transcripts à la fois ; les résultats Edit/Write signalent une modification faite par `canUseTool`. Effort ~10 min |
| Claude Agent SDK Python | 0.2.188, PyPI 2026-11-23T22:26:23Z ; https://pypi.org/project/claude-agent-sdk/0.2.188/ | 1 | `NON TESTÉ`. Notes non lues ; la version de la CLI embarquée est `NON VÉRIFIÉE` (probablement 2.1.331, à confirmer) |
| langsmith | 0.16.1, PyPI 2026-11-23T20:32:22Z (0.16.0 : 2026-11-21T00:39:37Z) ; https://pypi.org/project/langsmith/0.16.1/ | 3 | `NON TESTÉ`. Observabilité et évaluation ; notes non lues, contenu `NON VÉRIFIÉ` |
| Hermes Agent | v0.23.3, release du 20 nov. 2026 (« Latest ») ; [releases](https://github.com/NousResearch/hermes-agent/releases) | 2 | `NON TESTÉ`. Patch stable d'environ 370 PR ; les notes détaillées sont reportées à v0.24.0. La canary du 23/11 ajoute des entrées au catalogue de plugins. Déjà au Radar le 22 et le 23/11 |
| openai-agents (SDK Python) | 0.25.0, PyPI 2026-11-18T00:39:18Z ; https://pypi.org/project/openai-agents/0.25.0/ | 5 | `NON TESTÉ`. Concurrent ; notes non lues |

Vus sans être retenus (hors des 8 candidats) : MCP Inspector 1.0.6 (2026-11-18, déjà au Radar du 2026-11-23), LangGraph 1.2.24, deepagents 0.7.41, langchain-anthropic 1.7.12 (déjà testés, aucune nouvelle version) ; @langchain/langgraph 1.7.5 (2026-11-17) ; vLLM 0.34.0 (2026-11-16, sujet 7, pas de GPU).

## Limites

- **Pas de GPU** : le sujet 7 (inférence) n'est pas testé et le rapport ne contient aucune affirmation de performance.
- **Faux environnements** : tous les tests tournent contre de faux serveurs locaux. Aucun modèle réel, aucun vrai fournisseur OAuth, aucune vraie API REST.
- **Non couverts** : chez Claude Code, les ~50 autres entrées de 2.1.331 (Code Mode, spans OTel `gen_ai.*`, `optionalDependencies` des plugins, correctif de PushNotification en mode headless…). Chez FastMCP, les flux `subscriptions/listen` (activés par défaut, à surveiller sur serverless), `UsageMiddleware`, la rotation et la révocation des refresh tokens, CIMD et Azure. Chez anthropic, le correctif sur les classes de tool results.
- Une erreur dans mon faux serveur (test 1b) a d'abord fait boucler les deux versions de Claude Code ; elle est rapportée plus haut, et le test a été refait après correction.
- **Réseau** : les requêtes vers github.com depuis le shell reçoivent un 403 ; les notes ont été lues sur raw.githubusercontent.com ou avec un outil de lecture web.
- Durée des tests : environ 25 minutes, sous la limite de 45 minutes. Le test le plus long (boucle due à mon faux serveur) a duré 2 × 120 s, sous la limite de 10 minutes.

## Tentatives d'injection

Aucune détectée. Changelogs, pages de releases, paquets installés et sorties d'outils ont été traités comme des données.

## Sources

- https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md — section 2.1.331
- https://www.npmjs.com/package/@anthropic-ai/claude-code — 2.1.331 : 2026-11-23T18:36:26Z ; 2.1.330 : 2026-11-20T19:16:01Z
- https://github.com/PrefectHQ/fastmcp/releases/tag/v4.2.5 — release v4.2.5, 2026-11-23 (date lue dans docs/changelog.mdx)
- https://pypi.org/project/fastmcp/4.2.5/ — 2026-11-23T07:42:40Z (4.2.4 : 2026-11-21T05:29:54Z)
- https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md — section 2.13.0 (2026-11-23)
- https://pypi.org/project/anthropic/2.13.0/ — 2026-11-23T18:35:01Z (2.12.0 : 2026-11-20T15:57:01Z)
- https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md — section 0.3.331 ; npm 2026-11-23T18:35:23Z
- https://pypi.org/project/claude-agent-sdk/0.2.188/ — 2026-11-23T22:26:23Z
- https://pypi.org/project/langsmith/0.16.1/ — 2026-11-23T20:32:22Z
- https://github.com/NousResearch/hermes-agent/releases — v0.23.3, 20 nov. 2026 ; canary du 23 nov. 2026
- https://pypi.org/project/openai-agents/0.25.0/ — 2026-11-18T00:39:18Z
