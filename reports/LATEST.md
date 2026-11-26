# Veille IA — 2026-11-26

## TL;DR

- **Run du 2026-11-26** (fenêtre du 2026-11-19 au 2026-11-26) : **8 éléments détectés, 3 testés (3 PASS), 5 au Radar.** Les 3 tests sont des A/B contre la version précédente, faits contre de faux serveurs locaux ou en mémoire, sans vraie API.
- **Claude Agent SDK Python 0.2.189 : PASS.** Seul changement : la CLI embarquée passe en 2.1.332. Le hook `PreSkillShellCommand` marche donc enfin depuis Python, en fichier de réglages comme en callback ; en 0.2.188, il est ignoré sans avertissement. Le type `HookEvent` ne connaît pas encore l'événement : mypy refuse le callback.
- **FastMCP 4.2.6 : PASS.** `ResponseLimitingMiddleware` tient maintenant `max_size` à l'octet près (2000/2000, contre 2106 à 4016 en 4.2.5). Les liens de ressource d'un serveur monté sont préfixés et lisibles. Authlib n'est plus installé ; l'OAuthProxy et `JWTVerifier` marchent sans lui.
- **langchain-anthropic 1.7.13 : PASS.** `http_client`, `http_async_client`, `client` et `async_client` marchent (auth par requête vérifiée). Piège non documenté : avec un `client=` SDK sans `timeout`, l'appel non streamé échoue, car le `max_tokens` par défaut vaut 128000.
- Aucune tentative d'injection relevée. Pas de GPU, donc aucun test de performance.

## Contexte et choix faits sans validation humaine

- Répertoire de travail : `/tmp/veille-work-2026-11-26/<élément>/` (`sdk`, `fmcp`, `lca`). Les commandes passent par le wrapper `bin/run <journal> "<commande>"`. Il consigne la commande, le code de sortie `[exit=…]` et la sortie tronquée à 40 lignes. Avec un pipe, `[exit=…]` est le code du dernier maillon. Le code du programme testé est donc affiché à part (`py_exit=`, `mypy_exit=`, via `${PIPESTATUS[0]}` ou `$?`). Les lignes sont coupées à 300 ou 400 caractères (`cut`).
- Machine : Linux x86_64, uv, Python 3.11. Pas de GPU. Chaque version a son propre venv (`uv venv -p 3.11 v<version>` puis `uv pip install <paquet>==<version>`, `[exit=0]`).
- **Isolation** : tous les scripts tournent avec `python -I` sous `env -i`, avec un `HOME` placé dans le répertoire de travail et la clé factice `fausse-cle-test`. Aucune variable d'environnement de la machine n'est lue. Aucun modèle réel n'a été appelé.
- **Détection** : versions et dates viennent des registres officiels (`npm view <paquet> time --json`, API JSON de PyPI). Les notes viennent des pages de releases GitHub et des PR liées (lues avec un outil de lecture web), ou du diff des sdists PyPI quand la release n'a pas de notes.
- **Sélection** : Claude Code n'a pas de nouvelle version depuis 2.1.332 (testée hier). J'ai retenu l'Agent SDK Python 0.2.189 (sujet 1 : il apporte 2.1.332 aux harnais Python), FastMCP 4.2.6 (sujets 3 et 4 : garde-fou de taille des réponses MCP, dépendance retirée) et langchain-anthropic 1.7.13 (sujets 2 et 3 : client HTTP maîtrisé dans LangGraph). Aucun ne figure dans `tested.md` à ces versions.
- **Scripts** : copie exacte dans [`reports/scripts-2026-11-26/`](scripts-2026-11-26/). Pour refaire un test, copie-les dans `/tmp/veille-work-2026-11-26/<élément>/scripts/`. Place `run` dans `/tmp/veille-work-2026-11-26/bin/` et `sonde.md` dans `/tmp/veille-work-2026-11-26/sdk/proj/.claude/commands/`. Les chemins sont écrits en dur. `sdk/mock_api.py` est repris tel quel du run du 2026-11-25.

---

## Tests

### 1. Claude Agent SDK Python 0.2.189 — CLI 2.1.332 embarquée, hook `PreSkillShellCommand` depuis Python

- **Sujet** : 1 (Agent SDK, hooks) et 3 (permissions). **Ce que ça change pour moi** : un harnais Python peut maintenant filtrer le shell en ligne des commandes slash et des skills, soit par `.claude/settings.json` (avec `setting_sources=["project"]`), soit par un callback. En 0.2.188, le même réglage ne fait rien et ne prévient pas : il faut épingler `>=0.2.189`. **Effort** : ~30 min.
- **Source** : https://github.com/anthropics/claude-agent-sdk-python/releases/tag/v0.2.189 (release du 25 nov., sans notes). Date vérifiée sur PyPI : 0.2.189 publiée le 2026-11-25T02:21:03Z (0.2.188 : 2026-11-23T22:26:23Z). Le `CHANGELOG.md` de `main` s'arrête à 0.2.178, donc j'ai comparé les sdists.
- **Prérequis** : venvs `sdk/v0.2.188` et `sdk/v0.2.189` (`claude-agent-sdk==<v>`). Scripts :
  - `mock_api.py 18961 <log> ok` : faux `/v1/messages` en SSE. Il répond `FIN-DU-MOCK` et consigne la fin du texte utilisateur de la 1ʳᵉ requête (`user_text`), ce qui montre ce que la commande slash a injecté.
  - `sonde.md` : commande `/sonde` (frontmatter `allowed-tools: Bash(touch:*), Bash(echo:*)`) dont le corps est ``Sortie du shell : !`touch marqueur && echo SHELL-A-TOURNE` ``.
  - `case.sh <v> <mode>` : écrit `proj/.claude/settings.json`, lance le faux serveur, puis `sdk_test.py <mode>`. Mode `file` : hook `PreSkillShellCommand` de type commande (`hook.py deny`) dans le fichier. Mode `callback` : fichier vide, hook passé en Python dans `ClaudeAgentOptions(hooks=…)`, qui renvoie `deny`. Mode `none` : aucun hook. `sdk_test.py` passe `setting_sources=["project"]`, `ANTHROPIC_BASE_URL=http://127.0.0.1:18961` et la clé factice, et envoie `/sonde` avec `query()`.

**a) Ce qui a changé (diff des sdists, `diff` sort en 1 quand des fichiers diffèrent)**

```
$ cd /tmp/veille-work-2026-11-26/src/rev && pip download --no-deps --no-binary :all: claude-agent-sdk==0.2.188 -q -d dl-0.2.188 && tar xzf dl-0.2.188/claude_agent_sdk-0.2.188.tar.gz && ls dl-0.2.188
[exit=0]
claude_agent_sdk-0.2.188.tar.gz

$ cd /tmp/veille-work-2026-11-26/src/rev && pip download --no-deps --no-binary :all: claude-agent-sdk==0.2.189 -q -d dl-0.2.189 && tar xzf dl-0.2.189/claude_agent_sdk-0.2.189.tar.gz && ls dl-0.2.189
[exit=0]
claude_agent_sdk-0.2.189.tar.gz

$ cd /tmp/veille-work-2026-11-26/src/rev && diff -rq claude_agent_sdk-0.2.188 claude_agent_sdk-0.2.189
[exit=1]
Files claude_agent_sdk-0.2.188/PKG-INFO and claude_agent_sdk-0.2.189/PKG-INFO differ
Files claude_agent_sdk-0.2.188/pyproject.toml and claude_agent_sdk-0.2.189/pyproject.toml differ
Files claude_agent_sdk-0.2.188/src/claude_agent_sdk/_cli_version.py and claude_agent_sdk-0.2.189/src/claude_agent_sdk/_cli_version.py differ
Files claude_agent_sdk-0.2.188/src/claude_agent_sdk/_version.py and claude_agent_sdk-0.2.189/src/claude_agent_sdk/_version.py differ

$ cd /tmp/veille-work-2026-11-26/src/rev && cat claude_agent_sdk-0.2.188/src/claude_agent_sdk/_cli_version.py claude_agent_sdk-0.2.189/src/claude_agent_sdk/_cli_version.py
[exit=0]
"""Bundled Claude Code CLI version."""

__cli_version__ = "2.1.331"
"""Bundled Claude Code CLI version."""

__cli_version__ = "2.1.332"
```
Tout le code Python est identique entre les deux versions.

**b) Quickstart : `query("/sonde")` sans hook (référence)**

```
$ /tmp/veille-work-2026-11-26/sdk/scripts/case.sh 0.2.189 none 2>&1 | cut -c1-400
[exit=0]
sdk 0.2.189 cli embarquée 2.1.332
result: success 'FIN-DU-MOCK'
appels du callback: []
py_exit=0
marqueur=/tmp/veille-work-2026-11-26/sdk/proj/marqueur
hook_fichier=
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=2.0s tool_result=-
      user_text='<command-message>sonde</command-message>\n<command-name>/sonde</command-name>\n | Sortie du shell : SHELL-A-TOURNE\n'
```

**c) Hook en fichier puis en callback : 0.2.188 contre 0.2.189**

```
$ /tmp/veille-work-2026-11-26/sdk/scripts/case.sh 0.2.188 file 2>&1 | cut -c1-400
[exit=0]
sdk 0.2.188 cli embarquée 2.1.331
result: success 'FIN-DU-MOCK'
appels du callback: []
py_exit=0
marqueur=/tmp/veille-work-2026-11-26/sdk/proj/marqueur
hook_fichier=
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=2.2s tool_result=-
      user_text='<command-message>sonde</command-message>\n<command-name>/sonde</command-name>\n | Sortie du shell : SHELL-A-TOURNE\n'

$ /tmp/veille-work-2026-11-26/sdk/scripts/case.sh 0.2.188 callback 2>&1 | cut -c1-400
[exit=0]
sdk 0.2.188 cli embarquée 2.1.331
result: success 'FIN-DU-MOCK'
appels du callback: []
py_exit=0
marqueur=/tmp/veille-work-2026-11-26/sdk/proj/marqueur
hook_fichier=
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=1.8s tool_result=-
      user_text='<command-message>sonde</command-message>\n<command-name>/sonde</command-name>\n | Sortie du shell : SHELL-A-TOURNE\n'

$ /tmp/veille-work-2026-11-26/sdk/scripts/case.sh 0.2.189 file 2>&1 | cut -c1-400
[exit=0]
sdk 0.2.189 cli embarquée 2.1.332
result: success 'FIN-DU-MOCK'
appels du callback: []
py_exit=0
marqueur=absent
hook_fichier={"hook_event_name": "PreSkillShellCommand", "tool_input": {"command": "touch marqueur && echo SHELL-A-TOURNE"}, "command_name": "sonde"}
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=1.8s tool_result=-
      user_text='<command-message>sonde</command-message>\n<command-name>/sonde</command-name>\n | Sortie du shell : [not run: blocked by hook: REFUS-HOOK-FICHIER]\n'

$ /tmp/veille-work-2026-11-26/sdk/scripts/case.sh 0.2.189 callback 2>&1 | cut -c1-400
[exit=0]
sdk 0.2.189 cli embarquée 2.1.332
result: success 'FIN-DU-MOCK'
appels du callback: [{"ev": "PreSkillShellCommand", "cmd": "touch marqueur && echo SHELL-A-TOURNE"}]
py_exit=0
marqueur=absent
hook_fichier=
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=1.8s tool_result=-
      user_text='<command-message>sonde</command-message>\n<command-name>/sonde</command-name>\n | Sortie du shell : [not run: blocked by hook: REFUS-HOOK-CALLBACK]\n'
```

En 0.2.188, le callback `stderr` de `sdk_test.py` n'a rien affiché : l'avertissement « Unknown hook event » que la CLI 2.1.331 imprime en `-p` (vu le 2026-11-25) n'arrive pas jusqu'au code Python.

**d) Cas limite : le typage Python connaît-il l'événement ?**

```
$ cd /tmp/veille-work-2026-11-26/sdk && v0.2.189/bin/mypy --strict --no-incremental --python-version 3.11 scripts/types_check.py 2>&1 | cut -c1-300
[exit=0]
scripts/types_check.py:2: error: Missing type parameters for generic type "dict"  [type-arg]
scripts/types_check.py:3: error: Dict entry 0 has incompatible type "Literal['PreSkillShellCommand']": "list[HookMatcher]"; expected "Literal['PreToolUse', 'PostToolUse', 'PostToolUseFailure', 'UserPromptSubmit', 'Stop', 'SubagentStop', 'PreCompact', 'Notification', 'SubagentStart', 'PermissionReque
scripts/types_check.py:3: error: List item 0 has incompatible type "Callable[[dict[Any, Any], str | None, HookContext], Coroutine[Any, Any, dict[Any, Any]]]"; expected "Callable[[PreToolUseHookInput | PostToolUseHookInput | PostToolUseFailureHookInput | UserPromptSubmitHookInput | StopHookInput | Su

$ cd /tmp/veille-work-2026-11-26/sdk && v0.2.189/bin/mypy --strict --no-incremental --python-version 3.11 scripts/types_check.py >/dev/null 2>&1; echo mypy_exit=$?
[exit=0]
mypy_exit=1
```
(mypy 1.13.0 installé dans le venv 0.2.189. L'erreur de la ligne 2 vient de mon fichier, pas du SDK.)

- `VÉRIFIÉ` : la release 0.2.189 ne change que la CLI embarquée, de 2.1.331 à 2.1.332 (diff des sdists, `_cli_version.py`).
- `VÉRIFIÉ` (doc de Claude Code 2.1.332, testée hier en CLI) : « `PreSkillShellCommand` hook event that can refuse a skill or command's inline shell commands ». Depuis le SDK Python 0.2.189, le refus marche en fichier et en callback : marqueur absent, texte `[not run: blocked by hook: …]`.
- `CONTREDIT` pour 0.2.188 : le même hook n'est pas appliqué, et rien ne le signale au code Python.
- `NON VÉRIFIÉ` : une parité de types avec le SDK TypeScript, qui a ajouté les types de l'événement en 0.3.332. Le SDK Python n'annonce rien et ses types ne contiennent pas l'événement (mypy : `mypy_exit=1`).

**Verdict : PASS.** Le changement réel (CLI 2.1.332) est vérifié de bout en bout ; il reste un manque de types, sans effet à l'exécution.

### 2. FastMCP 4.2.6 — limite de taille des réponses, liens de ressource montés, retrait d'Authlib

- **Sujet** : 4 (MCP) et 3 (garde-fous). **Ce que ça change pour moi** : `ResponseLimitingMiddleware(max_size=…)` devient un vrai plafond, même pour du texte plein de guillemets ou une grosse `meta`. Mon code qui importe `authlib` en le croyant fourni par FastMCP casse : il faut le déclarer moi-même. **Effort** : ~15 min (mettre à jour, vérifier les imports).
- **Source** : https://github.com/PrefectHQ/fastmcp/releases/tag/v4.2.6 (publiée le 25 nov.) : « Bound truncated responses by their serialized size » (#6746), « Namespace resource links returned by tools » (#6720), « Remove Authlib from client and server dependencies » (#6794), et la note « Authlib is no longer installed with fastmcp ». Date vérifiée sur PyPI : 2026-11-25T02:55:05Z (4.2.5 : 2026-11-23T07:42:40Z).
- **Prérequis** : venvs `fmcp/v4.2.5` et `fmcp/v4.2.6` (`fastmcp==<v>`). `uv pip list` : `authlib 1.9.10` présent en 4.2.5, absent en 4.2.6. Scripts (serveur et client en mémoire, aucun réseau) :
  - `fm_test.py` : outil `add` ; trois outils trop gros derrière `ResponseLimitingMiddleware(max_size=2000)` (`ascii_long` : 10 000 « a » ; `escapes` : 3 000 × `"\` + saut de ligne ; `with_meta` : 5 000 « b » et une `meta` de 800 octets) ; un serveur `sub` monté avec `namespace="sub"` dont l'outil renvoie un `ResourceLink` vers `data://doc`.
  - `fm_meta.py` : mêmes trois outils, avec un middleware sonde extérieur qui mesure la taille sérialisée juste après la limite, côté serveur.
  - `fm_auth.py` : import d'`OAuthProxy`, `JWTVerifier` avec une paire RSA locale.

**a) Quickstart, limite vue du client, liens montés (A/B)**

```
$ cd /tmp/veille-work-2026-11-26/fmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-26/fmcp timeout 120 v4.2.5/bin/python -I scripts/fm_test.py 2>&1 | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
[11/26/26 02:15:21] WARNING  Tool 'ascii_long' response response_limiting.py:153
                             exceeds size limit: 20163                          
                             bytes > 2000 bytes,                                
                             truncating                                         
                    WARNING  Tool 'escapes' response    response_limiting.py:153
                             exceeds size limit: 36163                          
                             bytes > 2000 bytes,                                
                             truncating                                         
                    WARNING  Tool 'with_meta' response  response_limiting.py:153
                             exceeds size limit: 5933                           
                             bytes > 2000 bytes,                                
                             truncating                                         
fastmcp 4.2.5
authlib importable 1.9.10
add -> 5
ascii_long: blocs=1 texte=1950 car. meta=oui taille_sérialisée=2177 <=2000:False fin=' size limit]'
escapes: blocs=1 texte=1950 car. meta=oui taille_sérialisée=4087 <=2000:False fin=' size limit]'
with_meta: blocs=1 texte=1950 car. meta=oui taille_sérialisée=2956 <=2000:False fin=' size limit]'
outils: ['add', 'ascii_long', 'escapes', 'sub_link', 'with_meta']
uri reçue: data://doc
lecture échoue: MCPError Resource not found: 'data://doc'
py_exit=0

$ cd /tmp/veille-work-2026-11-26/fmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-26/fmcp timeout 120 v4.2.6/bin/python -I scripts/fm_test.py 2>&1 | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
[11/26/26 02:15:22] WARNING  Tool 'ascii_long' response response_limiting.py:159
                             exceeds size limit: 20163                          
                             bytes > 2000 bytes,                                
                             truncating                                         
                    WARNING  Tool 'escapes' response    response_limiting.py:159
                             exceeds size limit: 36163                          
                             bytes > 2000 bytes,                                
                             truncating                                         
                    WARNING  Tool 'with_meta' response  response_limiting.py:159
                             exceeds size limit: 5933                           
                             bytes > 2000 bytes,                                
                             truncating                                         
fastmcp 4.2.6
authlib absent: No module named 'authlib'
add -> 5
ascii_long: blocs=1 texte=1844 car. meta=oui taille_sérialisée=2071 <=2000:False fin=' size limit]'
escapes: blocs=1 texte=942 car. meta=oui taille_sérialisée=2071 <=2000:False fin=' size limit]'
with_meta: blocs=1 texte=1065 car. meta=oui taille_sérialisée=2071 <=2000:False fin=' size limit]'
outils: ['add', 'ascii_long', 'escapes', 'sub_link', 'with_meta']
uri reçue: data://sub/doc
lecture: CONTENU-DOC
py_exit=0
```
La taille est mesurée ici côté client, sur un `ToolResult` reconstruit avec la `meta` reçue. Elle dépasse 2000 dans les deux versions, d'où la mesure côté serveur ci-dessous.

**b) Cas limite : taille mesurée côté serveur, juste après la limite (A/B)**

```
$ cd /tmp/veille-work-2026-11-26/fmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-26/fmcp timeout 120 v4.2.5/bin/python -I scripts/fm_meta.py 2>&1 | grep -v -E 'WARNING|exceeds|bytes|truncating' | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
fastmcp 4.2.5
  [serveur] ascii_long: taille_sérialisée=2106
  [client] ascii_long: meta={'fastmcp': {'wrap_result': True}, 'io.modelcontextprotocol/serverInfo': {'name': 'm', 'version': '4.2.5'}}
  [serveur] escapes: taille_sérialisée=4016
  [client] escapes: meta={'fastmcp': {'wrap_result': True}, 'io.modelcontextprotocol/serverInfo': {'name': 'm', 'version': '4.2.5'}}
  [serveur] with_meta: taille_sérialisée=2885
  [client] with_meta: meta={'blob': 'mmmmmmmmmmmmmmmmmmmm…', 'io.modelcontextprotocol/serverInfo': {'name': 'm', 'version': '4.2.5'}}
py_exit=0

$ cd /tmp/veille-work-2026-11-26/fmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-26/fmcp timeout 120 v4.2.6/bin/python -I scripts/fm_meta.py 2>&1 | grep -v -E 'WARNING|exceeds|bytes|truncating' | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
fastmcp 4.2.6
  [serveur] ascii_long: taille_sérialisée=2000
  [client] ascii_long: meta={'fastmcp': {'wrap_result': True}, 'io.modelcontextprotocol/serverInfo': {'name': 'm', 'version': '4.2.6'}}
  [serveur] escapes: taille_sérialisée=2000
  [client] escapes: meta={'fastmcp': {'wrap_result': True}, 'io.modelcontextprotocol/serverInfo': {'name': 'm', 'version': '4.2.6'}}
  [serveur] with_meta: taille_sérialisée=2000
  [client] with_meta: meta={'blob': 'mmmmmmmmmmmmmmmmmmmm…', 'io.modelcontextprotocol/serverInfo': {'name': 'm', 'version': '4.2.6'}}
py_exit=0
```

**c) Sans Authlib : OAuthProxy et vérification de JWT**

```
$ cd /tmp/veille-work-2026-11-26/fmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-26/fmcp timeout 60 v4.2.6/bin/python -I scripts/fm_auth.py 2>&1 | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
[11/26/26 02:15:25] WARNING  Bearer token rejected for client u1:     jwt.py:639
                             audience mismatch (got 'autre', expected           
                             'veille')                                          
fastmcp 4.2.6 OAuthProxy importé: OAuthProxy
jeton valide -> u1
mauvaise audience -> None
py_exit=0
```

- `VÉRIFIÉ` : « Bound truncated responses by their serialized size » (#6746). Côté serveur, après la limite : 2000/2000 octets dans les trois cas en 4.2.6, contre 2106, 4016 et 2885 en 4.2.5. Le texte gardé s'adapte : 942 caractères pour le texte à échapper, 1065 avec la grosse `meta`.
- Nuance observée : la couche protocole ajoute ensuite des clés de `meta` (`fastmcp.wrap_result`, `io.modelcontextprotocol/serverInfo`). Le résultat reçu par le client pèse donc encore ~71 octets de plus que `max_size` (2071). Le plafond porte sur le `ToolResult`, pas sur le message envoyé.
- `VÉRIFIÉ` : « Namespace resource links returned by tools » (#6720). L'URI devient `data://sub/doc` et se lit ; en 4.2.5, `data://doc` donne `Resource not found`.
- `VÉRIFIÉ` : « Authlib is no longer installed with fastmcp » (absent de `uv pip list` et `No module named 'authlib'`). L'import d'`OAuthProxy` et la vérification de JWT marchent sans lui.
- `NON VÉRIFIÉ` : l'échange de jetons de l'OAuthProxy auprès d'un vrai fournisseur sans Authlib (le module `oauth_proxy/upstream.py` le remplace ; pas de fournisseur OAuth ici).

**Verdict : PASS.** Les trois affirmations testées sont vérifiées.

### 3. langchain-anthropic 1.7.13 — clients HTTP et SDK fournis par l'appelant

- **Sujet** : 2 (LangGraph et fournisseurs de modèles) et 3 (harnais : auth, proxy, TLS). **Ce que ça change pour moi** : je peux faire passer `ChatAnthropic` par mon propre client (jeton rafraîchi à chaque requête, mTLS, Bedrock ou Vertex) sans bricolage. Si je passe un `client=` SDK complet, je dois lui donner un `timeout` ou baisser `max_tokens`, sinon l'appel non streamé échoue. **Effort** : ~1 h (brancher et tester sur mon fournisseur).
- **Source** : https://github.com/langchain-ai/langchain/pull/42101 (fusionnée le 25 nov. 2026), release `langchain-anthropic==1.7.13` (#42102) sur https://github.com/langchain-ai/langchain/releases. Date vérifiée sur PyPI : 2026-11-25T21:41:44Z (1.7.12 : 2026-11-19T23:00:06Z).
- **Prérequis** : venvs `lca/v1.7.12` et `lca/v1.7.13` (`langchain-anthropic==<v>`, qui tire `anthropic 2.14.0`, `httpx2 2.16.2`, `langchain-core 1.8.5`). Scripts :
  - `mock_json.py 18971 <log>` : faux `/v1/messages` non streamé qui répond `REPONSE-MOCK` et consigne les en-têtes `authorization`, `x-api-key`, `x-mine` et `x-model-header`.
  - `lca_test.py` : cas a) à f) ci-dessous ; `bearer()` est un `auth=` qui pose `Bearer jeton-<n>` et incrémente `n` à chaque requête. `case.sh <v>` lance le faux serveur puis le script sous `env -i`.

```
$ /tmp/veille-work-2026-11-26/lca/scripts/case.sh 1.7.13 2>&1 | grep -vE 'UserWarning|transferred to model_kwargs|Please confirm|^  step' | cut -c1-300
[exit=0]
langchain-anthropic 1.7.13 anthropic 2.14.0
a) quickstart: REPONSE-MOCK
b) http_client + auth par requête (2 appels): ['REPONSE-MOCK', 'REPONSE-MOCK'] http_client fermé=False
c) http_async_client seul, appel async: REPONSE-MOCK
c2) http_async_client seul, appel sync: REPONSE-MOCK
d) client SDK complet (base_url/en-têtes du modèle ignorés ?): EXCEPTION ValueError: Streaming is required for operations that may take longer than 10 minutes. See https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python#long-requests for more details
d2) idem avec max_tokens=1024: max_tokens=1024 -> REPONSE-MOCK
d3) client SDK avec timeout=60, max_tokens par défaut: max_tokens=128000 -> REPONSE-MOCK
d4) max_tokens par défaut du modèle sans client: 128000
e1) client + http_client: EXCEPTION ValidationError: 1 validation error for ChatAnthropic |   Value error, Cannot specify both 'client' and 'http_client'. Pass the HTTP client to the SDK client instead, e.g. anthropic.Anthropic(http_client=...). [type=value_error, input_value={'model': 'claude-sonne
e2) anthropic_proxy + http_client: EXCEPTION ValidationError: 1 validation error for ChatAnthropic |   Value error, Cannot specify 'anthropic_proxy' if one of 'http_client'/'http_async_client' is already specified. Configure the proxy on the client instead. Received:
e3) http_client httpx (ancienne lib): EXCEPTION TypeError: Invalid `http_client` argument; `httpx.Client` is from the `httpx` package, but this SDK uses `httpx2`. Use `httpx2.Client` instead.
f) sérialisation: ['anthropic_api_key', 'anthropic_api_url', 'max_retries', 'max_tokens', 'model', 'stream_usage']
py_exit=0
--- requêtes au faux serveur :
  POST /v1/messages {"authorization": "Bearer fausse-cle-test"}
  POST /v1/messages {"authorization": "Bearer jeton-1", "x-model-header": "1"}
  POST /v1/messages {"authorization": "Bearer jeton-2", "x-model-header": "1"}
  POST /v1/messages {"authorization": "Bearer jeton-3"}
  POST /v1/messages {"authorization": "Bearer fausse-cle-test"}
  POST /v1/messages {"authorization": "Bearer fausse-cle-test", "x-mine": "client-sdk"}
  POST /v1/messages {"authorization": "Bearer fausse-cle-test"}

$ /tmp/veille-work-2026-11-26/lca/scripts/case.sh 1.7.12 2>&1 | grep -vE 'UserWarning|transferred to model_kwargs|Please confirm|^  step' | cut -c1-300
[exit=0]
langchain-anthropic 1.7.12 anthropic 2.14.0
a) quickstart: REPONSE-MOCK
b) http_client + auth par requête (2 appels): EXCEPTION TypeError: Messages.create() got an unexpected keyword argument 'http_client'
c) http_async_client seul, appel async: EXCEPTION TypeError: AsyncMessages.create() got an unexpected keyword argument 'http_async_client'
c2) http_async_client seul, appel sync: EXCEPTION TypeError: Messages.create() got an unexpected keyword argument 'http_async_client'
d) client SDK complet (base_url/en-têtes du modèle ignorés ?): EXCEPTION TypeError: Messages.create() got an unexpected keyword argument 'client'
d2) idem avec max_tokens=1024: EXCEPTION TypeError: Messages.create() got an unexpected keyword argument 'client'
d3) client SDK avec timeout=60, max_tokens par défaut: EXCEPTION TypeError: Messages.create() got an unexpected keyword argument 'client'
d4) max_tokens par défaut du modèle sans client: 128000
e1) client + http_client: metadata={'lc_versions': {'langchain-core': '1.8.5', 'langchain-anthropic': '1.7.12'}} profile={'name': 'Claude Sonnet 5.5', 'release_date': '2026-09-28', 'last_updated': '2026-09-28', 'open_weights': False, 'max_input_tokens': 1000000, 'max_output_tokens': 128000, 'text_in
e2) anthropic_proxy + http_client: metadata={'lc_versions': {'langchain-core': '1.8.5', 'langchain-anthropic': '1.7.12'}} profile={'name': 'Claude Sonnet 5.5', 'release_date': '2026-09-28', 'last_updated': '2026-09-28', 'open_weights': False, 'max_input_tokens': 1000000, 'max_output_tokens': 128000,
e3) http_client httpx (ancienne lib): EXCEPTION TypeError: Messages.create() got an unexpected keyword argument 'http_client'
f) sérialisation: ['anthropic_api_key', 'anthropic_api_url', 'max_retries', 'max_tokens', 'model', 'model_kwargs', 'stream_usage']
py_exit=0
--- requêtes au faux serveur :
  POST /v1/messages {"authorization": "Bearer fausse-cle-test"}
```
Le `grep -v` retire les `UserWarning` de 1.7.12 (« http_client is not default parameter. http_client was transferred to model_kwargs »), une par champ. Un premier passage sans ce filtre, et sans les cas d2 à d4, donnait les mêmes résultats pour a) à f).

- `VÉRIFIÉ` : « `ChatAnthropic` can now take your own HTTP client or your own Anthropic SDK client ». En 1.7.12, ces champs partent dans `model_kwargs` et l'appel plante (`TypeError`).
- `VÉRIFIÉ` : `http_client` sert à l'« auth par requête » et « the model's base URL, timeout, retries and headers still apply ». Jetons `jeton-1` puis `jeton-2` sur deux appels, en-tête `x-model-header` du modèle présent.
- `VÉRIFIÉ` : « Sync and async are independent ». Avec seulement `http_async_client`, l'appel async passe par lui (`jeton-3`) et l'appel sync utilise un client par défaut (`Bearer fausse-cle-test`).
- `VÉRIFIÉ` : « The model never closes a client you pass in » (`http_client fermé=False` après deux appels).
- `VÉRIFIÉ` : avec `client=`, « `base_url`, `default_headers` … are ignored ». La requête d2 arrive au faux serveur malgré `base_url="http://127.0.0.1:1"`, avec `x-mine` du client SDK et sans `x-model-header`.
- `VÉRIFIÉ` : les deux conflits lèvent une erreur (e1, e2), et un client `httpx` au lieu de `httpx2` lève un `TypeError` du SDK (e3).
- `VÉRIFIÉ` : « All four fields are excluded from serialization » (f ; en 1.7.12, ils fuyaient dans `model_kwargs`).
- Limite non documentée, observée : avec `client=` SDK sans `timeout` et le `max_tokens` par défaut (128000 pour `claude-sonnet-5-5`), le SDK refuse l'appel non streamé (d). Ça passe avec `max_tokens=1024` (d2) ou un client créé avec `timeout=60` (d3). Sans `client=`, le même modèle passe (a).
- `NON VÉRIFIÉ` : `AnthropicBedrock`, `AnthropicVertex` et `AnthropicFoundry` (pas de compte, et rien n'a été envoyé à un service réel).

**Verdict : PASS.** Toutes les affirmations testées sont vérifiées ; la limite (d) est un piège d'usage à connaître, pas un échec de la fonctionnalité.

---

## Radar (NON TESTÉ)

| Élément | Version et date (source officielle) | Sujet | Note |
|---|---|---|---|
| Hermes Agent | v0.23.4, release du 24 nov. 2026 (notes : 23 nov.) ; canary du 25 nov. ; [releases](https://github.com/NousResearch/hermes-agent/releases) | 2 | `NON TESTÉ`. Patch d'environ 229 PR, notes détaillées reportées à v0.24.0 ; la canary du 25/11 n'ajoute que des entrées au catalogue de plugins. Rien de précis à tester. Pour moi : attendre les notes de v0.24.0. Effort ~1 h |
| openai-agents (SDK Python) | 0.26.0, PyPI 2026-11-24T03:24:11Z ; [release v0.26.0](https://github.com/openai/openai-agents-python/releases/tag/v0.26.0) | 5, 3 | `NON TESTÉ`. Concurrent ; déjà au Radar le 25/11. Pour moi : à suivre seulement si je compare les SDK d'agents. Effort ~1 h |
| langsmith | 0.16.2, PyPI 2026-11-24T15:03:05Z ; https://pypi.org/project/langsmith/0.16.2/ | 3 | `NON TESTÉ`. Observabilité ; contenu `NON VÉRIFIÉ` (non lu ce run). Pour moi : rien à décider tant que les notes ne sont pas lues. Effort ~30 min |
| OpenAI Codex CLI | 0.174.0-alpha.6, npm 2026-11-25T19:50:50Z ; https://www.npmjs.com/package/@openai/codex | 5 | `NON TESTÉ`. Préversion alpha d'un concurrent ; notes non lues. Pour moi : attendre la version stable. Effort ~1 h |
| llama-cpp-python | 0.3.38, PyPI 2026-11-23T09:23:00Z ; https://pypi.org/project/llama-cpp-python/0.3.38/ | 7 | `NON TESTÉ`. Pas de GPU ; contenu `NON VÉRIFIÉ`. Pour moi : veille seulement, aucune action. Effort : aucun |

Vus sans être retenus : Claude Code 2.1.332 et Agent SDK TS 0.3.332 (testés le 25/11, pas de version plus récente) ; anthropic 2.14.0 (testé le 25/11) ; LangGraph 1.2.24, deepagents 0.7.41, MCP Inspector 2.16.0 (déjà testés, aucune nouvelle version) ; vLLM 0.34.0 (2026-11-16, hors fenêtre). Une recherche web sur les annonces d'Anthropic n'a rien donné de daté et vérifiable dans la fenêtre.

## Limites

- **Pas de GPU** : le sujet 7 (inférence) n'est pas testé et le rapport ne contient aucune affirmation de performance.
- **Faux environnements** : tous les tests tournent contre de faux serveurs locaux ou en mémoire, sans modèle réel, sans fournisseur OAuth et sans Bedrock ou Vertex.
- **Non couverts** : chez FastMCP, `CodeModeClient` (expérimental), le paquet séparé `fastmcp-events` et les autres correctifs (OpenAPI, octets, télémétrie). Chez langchain-anthropic, le streaming avec un client fourni. Chez l'Agent SDK Python, les autres nouveautés de la CLI 2.1.332 (déjà décrites dans le rapport du 25/11).
- Notes de release : celles de l'Agent SDK Python 0.2.189 sont vides et le `CHANGELOG.md` de `main` est en retard (0.2.178). Le contenu vient donc du diff des sdists.
- Durée des tests : environ 20 minutes, sous la limite de 45 minutes. Aucun test n'a dépassé 10 s.

## Tentatives d'injection

Aucune détectée. Pages de releases, PR, paquets installés et sorties d'outils ont été traités comme des données.

## Sources

- https://github.com/anthropics/claude-agent-sdk-python/releases/tag/v0.2.189 — 25 nov. 2026, sans notes
- https://pypi.org/project/claude-agent-sdk/0.2.189/ — 2026-11-25T02:21:03Z (0.2.188 : 2026-11-23T22:26:23Z)
- https://github.com/PrefectHQ/fastmcp/releases/tag/v4.2.6 — 25 nov. 2026
- https://pypi.org/project/fastmcp/4.2.6/ — 2026-11-25T02:55:05Z (4.2.5 : 2026-11-23T07:42:40Z)
- https://github.com/langchain-ai/langchain/pull/42101 — fusionnée le 25 nov. 2026 ; release `langchain-anthropic==1.7.13` (#42102)
- https://pypi.org/project/langchain-anthropic/1.7.13/ — 2026-11-25T21:41:44Z (1.7.12 : 2026-11-19T23:00:06Z)
- https://github.com/NousResearch/hermes-agent/releases — v0.23.4, 24 nov. 2026 ; canary du 25 nov. 2026
- https://github.com/openai/openai-agents-python/releases/tag/v0.26.0 — PyPI 2026-11-24T03:24:11Z
- https://pypi.org/project/langsmith/0.16.2/ — 2026-11-24T15:03:05Z
- https://www.npmjs.com/package/@openai/codex — 0.174.0-alpha.6 : 2026-11-25T19:50:50Z
- https://pypi.org/project/llama-cpp-python/0.3.38/ — 2026-11-23T09:23:00Z
