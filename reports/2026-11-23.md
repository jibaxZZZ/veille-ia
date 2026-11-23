# Veille IA — 2026-11-23

## TL;DR

- **Run du 2026-11-23** (fenêtre du 2026-11-16 au 2026-11-23) : **7 éléments détectés, 3 testés (3 PASS), 4 au Radar.** Les 3 tests sont des A/B contre la version précédente, faits contre de faux serveurs locaux, sans vraie API.
- **MCP Inspector 2.16.0 : PASS.** Correctif GHSA-3xgv-mvj6-g78r reproduit. Face à un serveur MCP qui envoie une ligne SSE sans fin, la mémoire de 2.15.0 suit le flux (351 Mio pour 200 Mio envoyés, 792 Mio pour 600 Mio, 869 Mio en transport `sse`). 2.16.0 coupe le flux et reste entre 142 et 189 Mio.
- **langchain-anthropic 1.7.12 : PASS.** Avec 1.7.11, deux modèles partagent le client HTTP async. Dans une 2ᵉ boucle d'événements, la requête part sur une connexion morte : le serveur la reçoit **deux fois**, avec 0,43 s de délai. En 1.7.12 : un client par modèle, une seule requête. Les champs `finish_reason`/`normalized_finish_reason`/`finish_state` et la conservation de `caller` sont vérifiés.
- **Claude Agent SDK Python 0.2.187 : PASS.** Seul changement : il embarque la CLI 2.1.330 au lieu de 2.1.329. Via `query()` derrière une passerelle plafonnée à 32 000 jetons de sortie, 0.2.186 échoue après 6 requêtes. 0.2.187 se rattrape en 2 requêtes (64000 → 32000).
- Aucune tentative d'injection relevée. Pas de GPU, donc aucun test de performance.

## Contexte et choix faits sans validation humaine

- Répertoire de travail : `/tmp/veille-work-2026-11-23/<élément>/`. Les commandes passent par le wrapper `bin/run <journal> "<commande>"`. Il consigne la commande, le code de sortie `[exit=…]` (celui du dernier maillon) et la sortie tronquée à 40 lignes. Les sorties ci-dessous viennent de ces journaux. Quand un script masque le code d'un programme, ce code est affiché à part (`cli_exit=`, `python_exit=`).
- Machine : Linux x86_64, Node v22.23.5 (`/opt/node22/bin`), npm, uv 0.11.32, Python 3.11. Pas de GPU.
- **Isolation** : chaque test tourne sous `env -i`, avec un `HOME` placé dans le répertoire de travail. Aucune variable d'environnement de la machine n'est lue. La seule clé est factice (`fausse-cle-test`). Les seuls serveurs sont de faux serveurs sur 127.0.0.1. Aucun modèle réel n'a été appelé. Les `npm install` tournent hors `env -i` : sous `env -i`, ils échouent avec `SELF_SIGNED_CERT_IN_CHAIN`, car le certificat du proxy de la session n'est plus pris en compte.
- **Détection** : versions et dates viennent des registres officiels (`npm view <paquet> time --json`, API JSON de PyPI). Les notes viennent des pages de release GitHub (lues avec un outil de lecture web) et des changelogs bruts. L'API GitHub a répondu 403 depuis le shell.
- **Sélection** : j'ai retenu les 3 éléments testables sans clé et absents de `tested.md` à ces versions. Ce sont un correctif de sécurité MCP (sujets 3 et 4), le client Anthropic de LangChain/LangGraph (sujet 2) et le SDK d'agent Python (sujet 1). Les trois étaient au Radar du 2026-11-22 sans test. Les témoins A/B sont Inspector 2.15.0 (déjà dans `tested.md`, utilisé ici seulement comme témoin), langchain-anthropic 1.7.11 et Agent SDK Python 0.2.186.
- **Scripts** : copie exacte de tous les scripts et du wrapper dans [`reports/scripts-2026-11-23/`](scripts-2026-11-23/). Pour refaire un test, copie-les dans `/tmp/veille-work-2026-11-23/<élément>/scripts/` (et `bin/run`). Les chemins sont écrits en dur.
- Claude Code n'a pas sorti de version depuis 2.1.330 (npm, 2026-11-20T19:16:01Z, testée le 2026-11-21). L'Agent SDK TypeScript n'a pas sorti de version depuis 0.3.330 (testée le 2026-11-22).

---

## Tests

### 1. MCP Inspector 2.16.0 — plafond de taille des lignes et événements SSE (GHSA-3xgv-mvj6-g78r)

- **Sujet** : 3 (harnais, sandboxes) et 4 (MCP). **Ce que ça change pour moi** : brancher l'Inspector sur un serveur MCP non fiable pouvait faire grossir sa mémoire sans limite, jusqu'au crash. En 2.16.0, le flux est coupé à 16 Mio. **Effort** : ~5 min (`npx @modelcontextprotocol/inspector@2.16.0`).
- **Source** : release https://github.com/modelcontextprotocol/inspector/releases/tag/2.16.0, publiée le 18 nov. (heure 09:08, année non affichée). Extraits : « Cap SSE line and event size on every SDK transport stream (GHSA-3xgv-mvj6-g78r) (#2997) » et « fix(core): cap SSE line length and event size on every SDK transport stream (v2) (#2993) ». Avis : https://github.com/modelcontextprotocol/inspector/security/advisories/GHSA-3xgv-mvj6-g78r, publié le 18 nov. 2026, sévérité modérée (CVSS 6.5), versions touchées >= 2.7.0 et <= 2.15.0, corrigé en 2.16.0. Date vérifiée sur npm (https://www.npmjs.com/package/@modelcontextprotocol/inspector) : 2.16.0 le 2026-11-18T09:32:25Z (2.15.0 : 2026-11-12T01:24:25Z).
- **Prérequis** : `npm install --prefix v<v> --no-audit --no-fund @modelcontextprotocol/inspector@<v>` pour 2.15.0 et 2.16.0 (`[exit=0]`, « added 120 packages » pour chacune). Dans le paquet 2.16.0, `clients/cli/build/index.js` contient `SSE_MAX_LINE_BYTES = 16777216` et `createSseLineCapStream`. Aucune de ces deux chaînes n'apparaît en 2.15.0. Scripts dans `inspector/scripts/` :
  - `evil_mcp.py <port> <Mio> <log>` : faux serveur MCP sur `/<mode>/mcp`. `ok` répond normalement en SSE, avec un outil dont la description fait 1 Mio. `giant` répond à `initialize` par une ligne `data:` de <Mio> Mio sans fin de ligne. `bigevent` envoie <Mio> Mio de lignes `data:` courtes, sans ligne vide finale. `giantsse` (GET `/giantsse/sse`, transport `sse` historique, le cas de l'avis) envoie l'événement `endpoint`, puis une ligne `data:` sans fin.
  - `case.sh <v> <mode>` (variables optionnelles `T=<transport>`, `EP=<chemin>`) : lance `mcp-inspector --cli --transport ${T:-http} --server-url http://127.0.0.1:18921/<mode>/${EP:-mcp} --method tools/list` sous `env -i` et `timeout 120`, via `measure.py`. `measure.py` affiche la RSS max du processus enfant (`rss_max_kio`, en Kio) et la durée. Le script affiche ensuite le journal du faux serveur.

**a) Quickstart : `tools/list` sur un serveur sain** (réponse SSE avec une ligne de 1 Mio, sous le plafond). Serveur lancé avec `python3 -I scripts/evil_mcp.py 18921 200 logs/evil.log` :

```
$ /tmp/veille-work-2026-11-23/inspector/scripts/case.sh 2.15.0 ok
[exit=0]
cli_exit=0
{
  "tools": [
    {
      "name": "echo",
      "description": "xxxxxxxx… (1 Mio, coupé ici)
rss_max_kio=117576 duree_s=0.4
--- journal du faux serveur
POST /ok/mcp method=initialize
POST /ok/mcp method=notifications/initialized
POST /ok/mcp method=tools/list

$ /tmp/veille-work-2026-11-23/inspector/scripts/case.sh 2.16.0 ok
[exit=0]
cli_exit=0
{
  "tools": [
    {
      "name": "echo",
      "description": "xxxxxxxx… (1 Mio, coupé ici)
rss_max_kio=120040 duree_s=0.3
--- journal du faux serveur
POST /ok/mcp method=initialize
POST /ok/mcp method=notifications/initialized
POST /ok/mcp method=tools/list
```

**b) Ligne SSE sans fin puis événement géant, transport Streamable HTTP, 200 Mio** (lignes de sortie coupées à 200 caractères ; la ligne `rss_max_kio` est affichée deux fois par `case.sh`, une seule copie est gardée) :

```
$ /tmp/veille-work-2026-11-23/inspector/scripts/case.sh 2.15.0 giant
[exit=0]
cli_exit=4
{"error":{"code":"unreachable","message":"Connection timed out after 15000 ms. To accommodate a slower server, pass a larger --connect-timeout <ms>, or set connectionTimeout on the server's catalog or
rss_max_kio=351496 duree_s=15.3
--- journal du faux serveur
POST /giant/mcp method=initialize
giant: 200 Mio envoyés sans fin de ligne

$ /tmp/veille-work-2026-11-23/inspector/scripts/case.sh 2.16.0 giant
[exit=0]
cli_exit=4
{"error":{"code":"unreachable","message":"Connection timed out after 15000 ms. …
rss_max_kio=142512 duree_s=15.3
--- journal du faux serveur
POST /giant/mcp method=initialize
giant: client a fermé la connexion (ConnectionResetError)

$ /tmp/veille-work-2026-11-23/inspector/scripts/case.sh 2.15.0 bigevent
[exit=0]
cli_exit=4
{"error":{"code":"unreachable","message":"Connection timed out after 15000 ms. …
rss_max_kio=443536 duree_s=15.3
--- journal du faux serveur
POST /bigevent/mcp method=initialize
bigevent: 200 Mio en lignes courtes sans ligne vide

$ /tmp/veille-work-2026-11-23/inspector/scripts/case.sh 2.16.0 bigevent
[exit=0]
cli_exit=4
{"error":{"code":"unreachable","message":"Connection timed out after 15000 ms. …
rss_max_kio=141992 duree_s=15.3
--- journal du faux serveur
POST /bigevent/mcp method=initialize
bigevent: client a fermé la connexion (ConnectionResetError)
```

**c) Croissance avec la taille du flux : serveur relancé avec 600 Mio**, puis le cas de l'avis (transport `sse`, flux GET) :

```
$ /tmp/veille-work-2026-11-23/inspector/scripts/case.sh 2.15.0 giant
[exit=0]
cli_exit=4
{"error":{"code":"unreachable","message":"Connection timed out after 15000 ms. …
rss_max_kio=792408 duree_s=15.3
--- journal du faux serveur
POST /giant/mcp method=initialize
giant: 600 Mio envoyés sans fin de ligne

$ /tmp/veille-work-2026-11-23/inspector/scripts/case.sh 2.16.0 giant
[exit=0]
cli_exit=4
{"error":{"code":"unreachable","message":"Connection timed out after 15000 ms. …
rss_max_kio=141980 duree_s=15.3
--- journal du faux serveur
POST /giant/mcp method=initialize
giant: client a fermé la connexion (ConnectionResetError)

$ T=sse EP=sse /tmp/veille-work-2026-11-23/inspector/scripts/case.sh 2.15.0 giantsse
[exit=0]
cli_exit=4
{"error":{"code":"unreachable","message":"Connection timed out after 15000 ms. …
rss_max_kio=868916 duree_s=15.4
--- journal du faux serveur
GET /giantsse/sse
POST /giantsse/messages method=initialize
giantsse: client a fermé la connexion (ConnectionResetError)

$ T=sse EP=sse /tmp/veille-work-2026-11-23/inspector/scripts/case.sh 2.16.0 giantsse
[exit=0]
cli_exit=4
{"error":{"code":"unreachable","message":"Connection timed out after 15000 ms. …
rss_max_kio=189244 duree_s=15.3
--- journal du faux serveur
GET /giantsse/sse
POST /giantsse/messages method=initialize
giantsse: client a fermé la connexion (ConnectionResetError)
GET /giantsse/sse
giantsse: client a fermé la connexion (ConnectionResetError)
GET /giantsse/sse
giantsse: client a fermé la connexion (ConnectionResetError)
GET /giantsse/sse
giantsse: client a fermé la connexion (ConnectionResetError)
GET /giantsse/sse
giantsse: client a fermé la connexion (ConnectionResetError)
```

| Affirmation de la doc | Étiquette | Observation |
|---|---|---|
| La taille des lignes SSE est plafonnée sur les flux des transports | `VÉRIFIÉ` | 2.15.0 : RSS 351 Mio (200 Mio envoyés), 792 Mio (600 Mio), 869 Mio (`sse`, 600 Mio). 2.16.0 : 142 à 189 Mio, le client coupe la connexion avant la fin du flux |
| La taille des événements SSE est plafonnée | `VÉRIFIÉ` | `bigevent` : 2.15.0 lit les 200 Mio (RSS 444 Mio) ; 2.16.0 coupe (RSS 142 Mio) |
| Le cas de l'avis (transport `sse`, flux GET de longue durée) est corrigé | `VÉRIFIÉ` pour la CLI | Testé avec la CLI, qui partage le module `core`. Le backend du mode web (`watchLongLivedStream`), cité par l'avis, n'est pas lancé : `NON VÉRIFIÉ` pour le web |
| Le message `SseLineTooLongError` explique la coupure (texte présent dans le paquet) | `NON VÉRIFIÉ` | Non affiché par la CLI : dans les deux versions, elle répond seulement `Connection timed out after 15000 ms` (`cli_exit=4`). En `sse`, 2.16.0 se reconnecte 4 fois avant le délai |

**Verdict : `PASS`** — la consommation mémoire non bornée est reproduite en 2.15.0 et disparaît en 2.16.0, sur les 3 chemins testés. Un défaut reste : l'erreur affichée (« timeout ») ne dit pas pourquoi le flux a été coupé.

---

### 2. langchain-anthropic 1.7.12 — client HTTP async par modèle, `finish_reason` normalisé, `caller` conservé

- **Sujet** : 2 (LangGraph, fournisseurs de modèles) et 3 (reprise sur erreur). **Ce que ça change pour moi** : un service qui crée des `ChatAnthropic` dans des boucles d'événements successives (workers, tests, `asyncio.run` répétés) renvoyait silencieusement une requête : double envoi, donc double facturation possible, plus un délai. Les nouveaux champs `normalized_finish_reason`/`finish_state` permettent de détecter `max_tokens` et `pause_turn` sans code propre à Anthropic. **Effort** : ~10 min (montée de version) ; ~30 min pour brancher `finish_state == "suspended"` dans un graphe.
- **Source** : release https://github.com/langchain-ai/langchain/releases/tag/langchain-anthropic%3D%3D1.7.12, publiée le 19 nov. à 23:00 (année non affichée). Extraits : « fix(anthropic): don't share the async HTTP client between models (#41946) » ; « fix(anthropic): preserve `caller` on `tool_search_tool_result` blocks (#41958) » ; « feat(core): standardize finish reason on message-finish events (#41926) ». Date vérifiée sur PyPI (https://pypi.org/project/langchain-anthropic/1.7.12/) : 2026-11-19T23:00:06Z (1.7.11 : 2026-11-18T15:20:04Z).
- **Prérequis** : `uv venv -q -p 3.11 venv-<v> && uv pip install -q -p venv-<v>/bin/python langchain-anthropic==<v>` (`[exit=0]` ; sortie : `1.7.11 2.12.0 1.8.4` et `1.7.12 2.12.0 1.8.4`, soit langchain-anthropic, anthropic, langchain-core). Le diff des deux paquets confirme : `@lru_cache` est retiré de `_get_default_async_httpx_client`, `_finish_reason_fields` est ajouté, et le filtre `caller` porte sur les blocs `tool_search_tool_result`. Scripts dans `lc-anthropic/scripts/` :
  - `mock_api.py <port> <log>` : faux `/v1/messages` HTTP/1.1 keep-alive, en JSON ou SSE. Le `stop_reason` est lu dans le message utilisateur (`STOP=<raison>`). Il consigne le port client de chaque requête.
  - `lc_test.py <port> <cas>` : `ChatAnthropic(model="claude-opus-4-8", api_key="fausse-cle-test", base_url=http://127.0.0.1:<port>, max_retries=2)`. Cas : `finish` (`invoke`), `stream`, `loops` (modèles `a` et `b` dans deux `asyncio.run` successifs), `caller` (appel direct de `_format_messages`).
- Serveur lancé avec `python3 -I scripts/mock_api.py 18911 logs/mock.log`.

**a) Quickstart `invoke`, champs de fin** :

```
$ cd /tmp/veille-work-2026-11-23/lc-anthropic && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-23/lc-anthropic timeout 120 venv-1.7.11/bin/python -I scripts/lc_test.py 18911 finish
[exit=0]
langchain-anthropic 1.7.11 | cas: finish
invoke STOP=end_turn                        -> {'stop_reason': 'end_turn', 'finish_reason': None, 'normalized_finish_reason': None, 'finish_state': None}
invoke STOP=max_tokens                      -> {'stop_reason': 'max_tokens', 'finish_reason': None, 'normalized_finish_reason': None, 'finish_state': None}
(… mêmes valeurs None pour tool_use, pause_turn, refusal, model_context_window_exceeded, inconnu_xyz)

$ cd /tmp/veille-work-2026-11-23/lc-anthropic && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-23/lc-anthropic timeout 120 venv-1.7.12/bin/python -I scripts/lc_test.py 18911 finish
[exit=0]
langchain-anthropic 1.7.12 | cas: finish
invoke STOP=end_turn                        -> {'stop_reason': 'end_turn', 'finish_reason': 'end_turn', 'normalized_finish_reason': 'stop', 'finish_state': 'complete'}
invoke STOP=max_tokens                      -> {'stop_reason': 'max_tokens', 'finish_reason': 'max_tokens', 'normalized_finish_reason': 'length', 'finish_state': 'complete'}
invoke STOP=tool_use                        -> {'stop_reason': 'tool_use', 'finish_reason': 'tool_use', 'normalized_finish_reason': 'tool_call', 'finish_state': 'complete'}
invoke STOP=pause_turn                      -> {'stop_reason': 'pause_turn', 'finish_reason': 'pause_turn', 'normalized_finish_reason': 'other', 'finish_state': 'suspended'}
invoke STOP=refusal                         -> {'stop_reason': 'refusal', 'finish_reason': 'refusal', 'normalized_finish_reason': 'refusal', 'finish_state': 'complete'}
invoke STOP=model_context_window_exceeded   -> {'stop_reason': 'model_context_window_exceeded', 'finish_reason': 'model_context_window_exceeded', 'normalized_finish_reason': 'context_exceeded', 'finish_state': 'complete'}
invoke STOP=inconnu_xyz                     -> {'stop_reason': 'inconnu_xyz', 'finish_reason': 'inconnu_xyz', 'normalized_finish_reason': 'other', 'finish_state': 'complete'}
```

En `stream` (même commande, cas `stream`, `[exit=0]`), 1.7.11 donne `None` pour les 3 champs. 1.7.12 donne `end_turn → stop/complete`, `max_tokens → length/complete` et `pause_turn → other/suspended`.

**b) Deux modèles dans deux boucles d'événements successives** (journal du faux serveur vidé avant chaque version) :

```
$ cd /tmp/veille-work-2026-11-23/lc-anthropic && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-23/lc-anthropic timeout 120 venv-1.7.11/bin/python -I scripts/lc_test.py 18911 loops; echo "requêtes reçues par le faux serveur:"; cat logs/mock.log
[exit=0]
langchain-anthropic 1.7.11 | cas: loops
même client httpx async pour 2 modèles : True
boucle 1 (modèle a): FIN-DU-MOCK en 0.06 s
boucle 2 (modèle b): FIN-DU-MOCK en 0.43 s
requêtes reçues par le faux serveur:
POST /v1/messages client_port=59914 stream=None stop=end_turn
POST /v1/messages client_port=59914 stream=None stop=end_turn
POST /v1/messages client_port=59920 stream=None stop=end_turn

$ cd /tmp/veille-work-2026-11-23/lc-anthropic && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-23/lc-anthropic timeout 120 venv-1.7.12/bin/python -I scripts/lc_test.py 18911 loops; echo "requêtes reçues par le faux serveur:"; cat logs/mock.log
[exit=0]
langchain-anthropic 1.7.12 | cas: loops
même client httpx async pour 2 modèles : False
boucle 1 (modèle a): FIN-DU-MOCK en 0.06 s
boucle 2 (modèle b): FIN-DU-MOCK en 0.00 s
requêtes reçues par le faux serveur:
POST /v1/messages client_port=59936 stream=None stop=end_turn
POST /v1/messages client_port=59942 stream=None stop=end_turn
```

En 1.7.11, la 2ᵉ requête part sur la connexion ouverte dans la 1ʳᵉ boucle (même port 59914). Le serveur la reçoit et répond, mais le client ne peut pas lire la réponse et renvoie la requête sur une nouvelle connexion (port 59920).

**c) `caller` sur `tool_search_tool_result`** (premier lancement : `[exit=1]` pour les deux versions, `TypeError: _format_messages() missing 1 required keyword-only argument: 'model'`. C'était une erreur de mon script, corrigée en ajoutant `model="claude-opus-4-8"`, puis relancée) :

```
$ cd /tmp/veille-work-2026-11-23/lc-anthropic && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-23/lc-anthropic timeout 120 venv-1.7.11/bin/python -I scripts/lc_test.py 18911 caller
[exit=0]
langchain-anthropic 1.7.11 | cas: caller
caller entrée={'type': 'code_execution_20250825', 'tool_id': 'srvtoolu_x'} -> clés sorties=['content', 'tool_use_id', 'type'] caller=None
caller entrée={'type': 'direct'} -> clés sorties=['content', 'tool_use_id', 'type'] caller=None
caller entrée=None -> clés sorties=['content', 'tool_use_id', 'type'] caller=None

$ cd /tmp/veille-work-2026-11-23/lc-anthropic && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-23/lc-anthropic timeout 120 venv-1.7.12/bin/python -I scripts/lc_test.py 18911 caller
[exit=0]
langchain-anthropic 1.7.12 | cas: caller
caller entrée={'type': 'code_execution_20250825', 'tool_id': 'srvtoolu_x'} -> clés sorties=['caller', 'content', 'tool_use_id', 'type'] caller={'type': 'code_execution_20250825', 'tool_id': 'srvtoolu_x'}
caller entrée={'type': 'direct'} -> clés sorties=['content', 'tool_use_id', 'type'] caller=None
caller entrée=None -> clés sorties=['content', 'tool_use_id', 'type'] caller=None
```

| Affirmation de la doc | Étiquette | Observation |
|---|---|---|
| Le client HTTP async n'est plus partagé entre modèles | `VÉRIFIÉ` | `même client … : True` en 1.7.11, `False` en 1.7.12 |
| (docstring du paquet) Partagé, il fait échouer une tentative puis relance après un délai | `VÉRIFIÉ` | 1.7.11 : 3 requêtes reçues pour 2 appels, 0,43 s sur le 2ᵉ appel ; 1.7.12 : 2 requêtes, ~0 s. L'erreur `Event loop is closed` n'est pas affichée (relance silencieuse) : son texte reste `NON VÉRIFIÉ` |
| Raison de fin standardisée sur les événements de fin de message | `VÉRIFIÉ` | `finish_reason`, `normalized_finish_reason` et `finish_state` sont présents en `invoke` et en `stream` en 1.7.12, absents en 1.7.11 |
| `caller` est conservé sur les blocs `tool_search_tool_result` | `VÉRIFIÉ` | Un `caller` non `direct` est conservé en 1.7.12 et perdu en 1.7.11. `direct` reste omis dans les deux versions. Effet côté API réelle : `NON VÉRIFIÉ` |

**Verdict : `PASS`** — les trois changements sont observés, et le double envoi de 1.7.11 a été reproduit.

---

### 3. Claude Agent SDK Python 0.2.187 — CLI embarquée 2.1.330 (relance `max_tokens`) via `query()`

- **Sujet** : 1 (Agent SDK, limites). **Ce que ça change pour moi** : un agent Python derrière une passerelle qui plafonne la sortie échouait avec 0.2.186 (CLI 2.1.329). Avec 0.2.187, il se rattrape tout seul, sans réglage. Il n'y a aucun autre changement de code Python. **Effort** : ~5 min (`pip install -U claude-agent-sdk==0.2.187`).
- **Source** : release https://github.com/anthropics/claude-agent-sdk-python/releases/tag/v0.2.187, publiée le 20 nov. à 23:28 (année non affichée). Le corps de la release ne s'est pas chargé, et le CHANGELOG de `main` s'arrête à 0.2.178 : il n'y a donc pas de note écrite. Contenu établi par le diff des paquets installés : seuls `_cli_version.py` (`__cli_version__ = "2.1.329"` → `"2.1.330"`), `_version.py` et `_bundled/` changent. Date vérifiée sur PyPI (https://pypi.org/project/claude-agent-sdk/0.2.187/) : 2026-11-20T23:27:21Z (0.2.186 : 2026-11-19T23:00:37Z). Comportement attendu, d'après le changelog Claude Code 2.1.330 (https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) : « Reverted 2.1.329's removal of the automatic retry when `max_tokens` exceeds a model's or gateway's limit ».
- **Prérequis** : `uv venv -q -p 3.11 venv-<v> && uv pip install -q -p venv-<v>/bin/python claude-agent-sdk==<v>` (`[exit=0]`). La CLI embarquée répond `2.1.329 (Claude Code)` pour 0.2.186 et `2.1.330 (Claude Code)` pour 0.2.187. Scripts dans `agent-sdk-py/scripts/` :
  - `mock_api.py <port> <log> <plafond>` : faux `/v1/messages` en SSE (`FIN-DU-MOCK`). Si `max_tokens` dépasse le plafond (> 0), il renvoie une erreur 400 au format de l'API. Il consigne `max_tokens`.
  - `sdk_test.py` : `query(prompt="dis bonjour", options=ClaudeAgentOptions(model="claude-opus-4-8", max_turns=1))`, puis affiche les messages et les exceptions.
  - `case.sh <v> <port> <plafond>` : démarre le faux serveur, puis lance le script sous `env -i` avec `ANTHROPIC_BASE_URL=http://127.0.0.1:<port>`, `ANTHROPIC_API_KEY=fausse-cle-test` et `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`.

**a) Quickstart sans plafond** :

```
$ /tmp/veille-work-2026-11-23/agent-sdk-py/scripts/case.sh 0.2.186 18931 0
[exit=0]
claude-agent-sdk 0.2.186 | CLI embarqué 2.1.329
assistant: FIN-DU-MOCK
result: subtype=success is_error=False result='FIN-DU-MOCK'
python_exit=0
requêtes au faux serveur :
  POST /v1/messages?beta=true max_tokens=64000

$ /tmp/veille-work-2026-11-23/agent-sdk-py/scripts/case.sh 0.2.187 18932 0
[exit=0]
claude-agent-sdk 0.2.187 | CLI embarqué 2.1.330
assistant: FIN-DU-MOCK
result: subtype=success is_error=False result='FIN-DU-MOCK'
python_exit=0
requêtes au faux serveur :
  POST /v1/messages?beta=true max_tokens=64000
```

**b) Passerelle plafonnée à 32 000 jetons de sortie** :

```
$ /tmp/veille-work-2026-11-23/agent-sdk-py/scripts/case.sh 0.2.186 18933 32000
[exit=0]
claude-agent-sdk 0.2.186 | CLI embarqué 2.1.329
assistant: API Error: 400 max_tokens: 64000 > 32000, which is the maximum allowed number of output tokens for claude-opus-4-8
result: subtype=success is_error=True result='API Error: 400 max_tokens: 64000 > 32000, which is the maximum allowed number of output tokens for claude-opus-4-8'
EXCEPTION ResultError Claude Code returned an error result: API Error: 400 max_tokens: 64000 > 32000, which is the maximum allowed number of output tokens for claude-opus-4-8 (exit code: 1)
python_exit=0
requêtes au faux serveur :
  POST /v1/messages?beta=true max_tokens=64000
  POST /v1/messages?beta=true max_tokens=64000
  POST /v1/messages?beta=true max_tokens=64000
  POST /v1/messages?beta=true max_tokens=64000
  POST /v1/messages?beta=true max_tokens=64000
  POST /v1/messages?beta=true max_tokens=64000

$ /tmp/veille-work-2026-11-23/agent-sdk-py/scripts/case.sh 0.2.187 18934 32000
[exit=0]
claude-agent-sdk 0.2.187 | CLI embarqué 2.1.330
assistant: FIN-DU-MOCK
result: subtype=success is_error=False result='FIN-DU-MOCK'
python_exit=0
requêtes au faux serveur :
  POST /v1/messages?beta=true max_tokens=64000
  POST /v1/messages?beta=true max_tokens=32000
```

| Affirmation de la doc | Étiquette | Observation |
|---|---|---|
| 0.2.187 embarque la CLI 2.1.330 (release sans note : constaté par diff) | `VÉRIFIÉ` | `_cli_version.py` et `claude --version` du binaire embarqué |
| (changelog CLI 2.1.330) La relance automatique est rétablie quand `max_tokens` dépasse la limite de la passerelle | `VÉRIFIÉ` via le SDK Python | 0.2.186 : 6 requêtes à 64000 puis `ResultError`. 0.2.187 : 64000 refusé, puis 32000 accepté, `success` |

Observation sans affirmation de doc : en 0.2.186, l'erreur arrive d'abord comme `ResultMessage` avec `subtype=success` mais `is_error=True`, puis `query()` lève `ResultError`. Un code qui ne regarde que `subtype` se tromperait.

**Verdict : `PASS`** — la nouvelle CLI embarquée est bien présente, et la relance `max_tokens` marche via `query()`.

---

## Radar (NON TESTÉ)

| Élément | Version et date (source officielle) | Sujet | Note |
|---|---|---|---|
| Hermes Agent | v0.23.3, release GitHub du 20 nov. 2026 (notes : « November 19 ») ; [release](https://github.com/NousResearch/hermes-agent/releases/tag/v0.23.3) | 2 | `NON TESTÉ`. Déjà au Radar du 2026-11-22. Patch stable d'environ 370 PR. Les canaris du 17 au 20/11 (support de « GPT-6.2 Astra et Sol », compaction à l'expiration du cache) sont des pré-versions, non retenues. Effort de mise à jour ~15 min |
| langsmith | 0.16.0, PyPI 2026-11-21T00:39:37Z ; https://pypi.org/project/langsmith/0.16.0/ | 3 | `NON TESTÉ`. Observabilité ; notes non lues, contenu `NON VÉRIFIÉ` |
| openai-agents (SDK Python) | 0.25.0, PyPI 2026-11-18T00:39:18Z ; https://pypi.org/project/openai-agents/0.25.0/ | 5 | `NON TESTÉ`. Concurrent du SDK d'agent ; notes non lues, contenu `NON VÉRIFIÉ` |
| MCP Inspector 1.0.6 (branche v1) | npm 2026-11-18T08:20:46Z | 4 | `NON TESTÉ`. Même correctif GHSA-3xgv-mvj6-g78r pour la branche 1.x (avis : versions <= 1.0.5 touchées). Si tu utilises encore la v1, mets à jour |

Vus sans être retenus : Claude Code (dernière version 2.1.330, déjà testée), Agent SDK TS (0.3.330, déjà testé), FastMCP 4.2.4, LangGraph 1.2.24 et deepagents 0.7.41 (déjà testés), vLLM 0.34.0 (2026-11-16, sujet 7, pas de GPU).

## Limites

- **Pas de GPU** : le sujet 7 (inférence) n'est pas testé et le rapport ne contient aucune affirmation de performance.
- **Faux environnements** : tous les tests tournent contre de faux serveurs locaux. Aucun modèle réel, aucun serveur MCP réel, aucune vraie passerelle. Les mesures de RSS sont prises sur une seule exécution, avec un délai de connexion de 15 s ; elles servent d'ordre de grandeur, pas de benchmark.
- **Non couverts** : chez l'Inspector, le backend du mode web (le composant cité par l'avis), le mode TUI et le texte de l'erreur `SseLineTooLongError` (jamais affiché par la CLI). Chez langchain-anthropic, l'effet de `caller` sur une vraie API, et le cas d'un seul modèle réutilisé dans deux boucles (non concerné par le correctif, qui porte sur des modèles distincts). Chez l'Agent SDK Python, les autres changements de la CLI 2.1.330 (garde `rm`, hook SessionStart), déjà testés directement le 2026-11-21.
- **Notes manquantes** : la release Agent SDK Python 0.2.187 n'a pas de note lisible (corps non chargé, CHANGELOG arrêté à 0.2.178). Son contenu a été établi par diff des paquets.
- **Réseau** : sous `env -i`, `npm install` échoue (certificat du proxy de la session). Les installations npm ont donc été faites avec l'environnement par défaut ; seuls les tests tournent sous `env -i`. L'API GitHub répond 403 depuis le shell.
- Une erreur dans mon propre script (`caller`, test 2c) a fait échouer le premier lancement. Elle est rapportée plus haut.
- Durée des tests : environ 25 minutes, sous la limite de 45 minutes. Aucun test n'a dépassé 10 minutes.

## Tentatives d'injection

Aucune détectée. Pages de releases, avis de sécurité, paquets installés et sorties d'outils ont été traités comme des données.

## Sources

- https://github.com/modelcontextprotocol/inspector/releases/tag/2.16.0 — release 2.16.0, 18 nov. 2026
- https://github.com/modelcontextprotocol/inspector/security/advisories/GHSA-3xgv-mvj6-g78r — avis publié le 18 nov. 2026
- https://www.npmjs.com/package/@modelcontextprotocol/inspector — 2.16.0 : 2026-11-18T09:32:25Z ; 2.15.0 : 2026-11-12T01:24:25Z ; 1.0.6 : 2026-11-18T08:20:46Z
- https://github.com/langchain-ai/langchain/releases/tag/langchain-anthropic%3D%3D1.7.12 — release du 19 nov. 2026
- https://pypi.org/project/langchain-anthropic/1.7.12/ — 2026-11-19T23:00:06Z (1.7.11 : 2026-11-18T15:20:04Z)
- https://github.com/anthropics/claude-agent-sdk-python/releases/tag/v0.2.187 — release du 20 nov. 2026
- https://pypi.org/project/claude-agent-sdk/0.2.187/ — 2026-11-20T23:27:21Z (0.2.186 : 2026-11-19T23:00:37Z)
- https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md — section 2.1.330 (npm 2026-11-20T19:16:01Z)
- https://github.com/NousResearch/hermes-agent/releases/tag/v0.23.3 — 20 nov. 2026
- https://pypi.org/project/langsmith/0.16.0/ — 2026-11-21T00:39:37Z
- https://pypi.org/project/openai-agents/0.25.0/ — 2026-11-18T00:39:18Z
