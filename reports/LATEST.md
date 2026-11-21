# Veille IA — 2026-11-21

## TL;DR

- **Run du 2026-11-21** (fenêtre du 2026-11-14 au 2026-11-21) : **8 éléments détectés, 3 testés (3 PASS), 5 au Radar.** Les 3 tests sont des A/B contre la version précédente, faits contre de faux serveurs locaux.
- **Claude Code 2.1.330 : PASS.** La relance automatique sur erreur `max_tokens`, supprimée en 2.1.329, est rétablie : derrière une passerelle plafonnée à 32000, la requête repasse sans réglage. Garde `rm` : 13 variantes refusées dans les deux versions, même avec `Bash(rm:*)` autorisé ou en `bypassPermissions`. Aucun écart reproduit sur ce point.
- **SDK Python anthropic 2.12.0 : PASS.** `AnthropicBedrock` déplace `anthropic-user-profile-id` de l'en-tête vers `user_profile_id` dans le corps. Le cas est vérifié en sync et en async, et un `user_profile_id` déjà présent dans le corps reste prioritaire.
- **FastMCP 4.2.3 : PASS.** Quand un outil OpenAPI est appelé sans son paramètre de chemin requis, le serveur journalise un avertissement de validation et non plus une exception avec traceback. `user_id=""` part toujours vers `/users/` dans les deux versions : c'est un cas limite à surveiller.
- Aucune tentative d'injection relevée. Pas de GPU, donc aucun test de performance.

## Contexte et choix faits sans validation humaine

- Répertoire de travail : `/tmp/veille-work-2026-11-21/<élément>/`. Les commandes passent par un wrapper `bin/run <journal> "<commande>"`. Il consigne la commande, le code de sortie `[exit=…]` (celui de la commande complète, donc du dernier maillon) et la sortie tronquée à 40 lignes dans `<élément>/logs/`. Les sorties ci-dessous sont copiées de ces journaux. Le code propre de `claude` est affiché à part (`claude_exit=`).
- Machine : Linux x86_64, utilisateur root, Node v22.23.5, npm, uv 0.11.32 (venvs Python 3.11.18). Pas de GPU.
- **Isolation** : chaque outil tourne sous `env -i`, avec un environnement vide et `HOME` placé dans le répertoire de travail. Aucune variable d'environnement de la machine n'est lue. Les clés sont factices (`fausse-cle-test`, `AKIAFAUSSECLETEST`, `fausse-cle-secrete-test`). Les serveurs sont des faux locaux sur 127.0.0.1 ou des `MockTransport`. Aucun modèle ni service AWS réel n'a été appelé.
- **Détection** : versions et dates viennent des registres officiels (`npm view <paquet> time --json`, API JSON de PyPI). Les notes viennent des `CHANGELOG.md` bruts (raw.githubusercontent.com) et du changelog de la doc FastMCP (`docs/changelog.mdx`).
- **Sélection** : les 3 éléments sont testables sans clé, absents de `tested.md` à ces versions, et touchent une décision : passerelle et limite de sortie, garde-fous de permissions, accès Claude via Bedrock, connecteurs MCP générés depuis OpenAPI. Les témoins A/B sont Claude Code 2.1.329 (déjà dans `tested.md`), anthropic 2.11.0 (déjà dans `tested.md`) et FastMCP 4.2.2 (déjà dans `tested.md`). Ils ne sont pas re-testés pour eux-mêmes.
- Un dossier de premier niveau factice `/veillecanari-21329` puis `/veillecanari-21330` a été créé hors du dépôt pour tester le cas « dossier de premier niveau » de la garde `rm`, puis supprimé.

---

## Tests

### 1. Claude Code 2.1.330 — retour de la relance `max_tokens`, garde `rm`, hook SessionStart avec `--continue`

- **Sujet** : 1 (limites Claude Code) et 3 (permissions, reprise sur erreur). **Ce que ça change pour moi** : derrière une passerelle qui plafonne la sortie, 2.1.330 se rattrape de nouveau tout seul. Le contournement `CLAUDE_CODE_MAX_OUTPUT_TOKENS` conseillé hier n'est plus obligatoire, mais il évite une requête refusée à chaque tour. La garde `rm` tient déjà face à une règle `Bash(rm:*)` large ou au mode bypass. **Effort** : ~5 min (mise à jour) ; aucun changement de config requis.
- **Source** : https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md, section `## 2.1.330`, lue en brut le 2026-11-21. Extraits : « Reverted 2.1.329's removal of the automatic retry when `max_tokens` exceeds a model's or gateway's limit » ; « Changed more `rm` commands aimed at the root, home, a top-level folder or the working folder to ask for approval; where nobody can answer, they're refused » ; « Fixed environment variables written by a SessionStart hook being lost with `claude -p --continue` ». Date vérifiée sur npm (https://www.npmjs.com/package/@anthropic-ai/claude-code) : 2.1.330 publiée le 2026-11-20T19:16:01Z, 2.1.329 le 2026-11-19T18:40:25Z.
- **Prérequis** : `npm install --prefix v<v> @anthropic-ai/claude-code@<v>` pour 2.1.329 et 2.1.330 (code de sortie 0 pour les deux). Scripts écrits pour le test, dans `claude-code/scripts/` :
  - `mock_api.py <port> <log> <scénario> [commande]` : faux `/v1/messages`. Si `max_tokens` > 32000, il renvoie l'erreur 400 au texte exact de l'API. En scénario `text`, il répond `FIN-DU-MOCK`. En scénario `tool`, il renvoie d'abord un `tool_use` Bash avec la commande donnée, puis recopie le `tool_result` reçu en `RESULTAT-OUTIL: …`. Il consigne `max_tokens` et le `tool_result`.
  - `case.sh <v> <port> <scénario> <commande> <cwd> [VAR=val…] -- <args claude>` : lance `claude -p --model claude-opus-4-8 <args>` sous `env -i` avec `ANTHROPIC_BASE_URL=http://127.0.0.1:<port>`, `ANTHROPIC_API_KEY=fausse-cle-test` et `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`.
  - `rm_variants.sh` / `rm_variants2.sh <v>` : pour chaque variante, recréent `cible-<v>/` (avec `canari.txt` et `sous/`), un `HOME` avec `canari-home.txt` et `/veillecanari-<v>`. Ils lancent ensuite `case.sh … -- 'nettoie' --max-turns 3 --allowedTools 'Bash(rm:*)'` avec `cwd` = `cible-<v>`, puis vérifient la présence des canaris.
  - `env_continue.sh <v>` : crée un projet dont `.claude/settings.json` a un hook `SessionStart` qui écrit `export MA_VAR=bonjour-hook` dans `$CLAUDE_ENV_FILE`. Il fait ensuite (a) une session neuve avec Bash `printenv MA_VAR`, (b) une session texte, (c) `--continue` avec la même commande Bash.

**a) Relance `max_tokens`, sans réglage** :

```
$ scripts/case.sh 2.1.329 18809 text x /tmp/veille-work-2026-11-21/claude-code -- --max-turns 1 'dis bonjour'
[exit=0]
API Error: 400 max_tokens: 64000 > 32000, which is the maximum allowed number of output tokens for claude-opus-4-8
claude_exit=1
journal du faux serveur :
  POST /v1/messages?beta=true max_tokens=64000 tools=True
  POST /v1/messages?beta=true max_tokens=64000 tools=True
  POST /v1/messages?beta=true max_tokens=64000 tools=True
  POST /v1/messages?beta=true max_tokens=64000 tools=True
  POST /v1/messages?beta=true max_tokens=64000 tools=True
  POST /v1/messages?beta=true max_tokens=64000 tools=True

$ scripts/case.sh 2.1.330 18800 text x /tmp/veille-work-2026-11-21/claude-code -- --max-turns 1 'dis bonjour'
[exit=0]
FIN-DU-MOCK
claude_exit=0
journal du faux serveur :
  POST /v1/messages?beta=true max_tokens=64000 tools=True
  POST /v1/messages?beta=true max_tokens=32000 tools=True
```

**b) Garde `rm`, `--allowedTools 'Bash(rm:*)'`, cwd = `cible-<v>`** (un test unitaire `rm -rf <cible absolue>` a aussi été refusé dans les deux versions avec `Dangerous rm operation detected`, voir `logs/rm.log`) :

```
$ scripts/rm_variants.sh 2.1.329
[exit=0]
[rm -rf "$PWD"] -> RESULTAT-OUTIL: Quoted text in this command can't be checked before it runs | canari cible: présent | canari HOME: présent
[rm -rf ./*] -> RESULTAT-OUTIL: Dangerous rm operation detected: '/tmp/veille-work-2026-11-21/claude-code/cible-2.1.329/*' | canari cible: présent | canari HOME: présent
[rm -rf ./] -> RESULTAT-OUTIL: Dangerous rm operation detected: '/tmp/veille-work-2026-11-21/claude-code/cible-2.1.329' | canari cible: présent | canari HOME: présent
[rm -rf "$HOME"] -> RESULTAT-OUTIL: Dangerous rm operation detected: '/tmp/veille-work-2026-11-21/claude-code/home-2.1.329' | canari cible: présent | canari HOME: présent
[rm -rf sous] -> RESULTAT-OUTIL: (Bash completed with no output) | canari cible: présent | canari HOME: présent
[/bin/rm -rf "$PWD"] -> RESULTAT-OUTIL: Quoted text in this command can't be checked before it runs | canari cible: présent | canari HOME: présent

$ scripts/rm_variants2.sh 2.1.329
[exit=0]
[rm -rf *] -> RESULTAT-OUTIL: Dangerous rm operation detected: '/tmp/veille-work-2026-11-21/claude-code/cible-2.1.329/* | cible: ok home: ok top: ok
[rm -rf ../cible-2.1.329] -> RESULTAT-OUTIL: Dangerous rm operation detected: '/tmp/veille-work-2026-11-21/claude-code/cible-2.1.329' | cible: ok home: ok top: ok
[rm --recursive --force /tmp/veille-work-2026-11-21/claude-code/cible-2.1.329] -> RESULTAT-OUTIL: Dangerous rm operation detected: '/tmp/veille-work-2026-11-21/claude-code/cible-2.1.329' | cible: ok home: ok top: ok
[rm -rf /tmp/veille-work-2026-11-21/claude-code/cible-2.1.329/sous/..] -> RESULTAT-OUTIL: Dangerous rm operation detected: '/tmp/veille-work-2026-11-21/claude-code/cible-2.1.329/s | cible: ok home: ok top: ok
[rm -rf ~] -> RESULTAT-OUTIL: Dangerous rm operation detected: '/tmp/veille-work-2026-11-21/claude-code/home-2.1.329' | cible: ok home: ok top: ok
[rm -rf /veillecanari-21329] -> RESULTAT-OUTIL: Dangerous rm operation detected: '/veillecanari-21329' | cible: ok home: ok top: ok
```

Avec `rm_variants.sh 2.1.330` et `rm_variants2.sh 2.1.330` (`[exit=0]`), les sorties sont identiques ligne à ligne, au numéro de version près dans les chemins, et tous les canaris restent présents (journal complet dans `logs/rm.log`). Le témoin `rm -rf sous` passe dans les deux versions, ce qui est attendu.

**b') Même garde en `--permission-mode bypassPermissions`** (`IS_SANDBOX=1`, nécessaire en root) :

```
$ scripts/case.sh 2.1.329 18869 tool 'rm -rf /tmp/veille-work-2026-11-21/claude-code/cible-2.1.329/*' /tmp/veille-work-2026-11-21/claude-code/cible-2.1.329 CLAUDE_CODE_MAX_OUTPUT_TOKENS=32000 IS_SANDBOX=1 -- 'nettoie' --max-turns 3 --permission-mode bypassPermissions | cut -c1-200; ls -A /tmp/veille-work-2026-11-21/claude-code/cible-2.1.329
[exit=0]
RESULTAT-OUTIL: Dangerous rm operation detected: '/tmp/veille-work-2026-11-21/claude-code/cible-2.1.329/*'

This command would remove a workspace directory (the working directory, an additional working directory, or one of their parent directories). This requires explicit approval and cannot be auto-allowed
claude_exit=0
[…]
canari.txt
sous
```

Pour 2.1.330, la sortie est identique (`[exit=0]`, même message, `canari.txt` et `sous` présents).

**c) Hook SessionStart avec `-p --continue`** :

```
$ scripts/env_continue.sh 2.1.329
[exit=0]
a) session neuve :
RESULTAT-OUTIL: bonjour-hook
claude_exit=0
b) session texte :
FIN-DU-MOCK
claude_exit=0
c) --continue :
RESULTAT-OUTIL: bonjour-hook
claude_exit=0

$ scripts/env_continue.sh 2.1.330
[exit=0]
a) session neuve :
RESULTAT-OUTIL: bonjour-hook
claude_exit=0
b) session texte :
FIN-DU-MOCK
claude_exit=0
c) --continue :
RESULTAT-OUTIL: bonjour-hook
claude_exit=0
```

(La première version du script utilisait `echo VAL=$MA_VAR`, que les deux versions refusent : « A variable in this command can't be checked before it runs ». Elle a été remplacée par `printenv MA_VAR`.)

**Doc contre réalité** :

| Affirmation (changelog 2.1.330) | Étiquette |
|---|---|
| La suppression de la relance automatique (2.1.329) est annulée | `VÉRIFIÉ` (2.1.329 : 6 requêtes à 64000, 400, code 1 ; 2.1.330 : 64000 puis 32000, succès, code 0) |
| Davantage de commandes `rm` visant la racine, le home, un dossier de premier niveau ou le dossier de travail demandent une approbation, et sont refusées quand personne ne peut répondre | `NON VÉRIFIÉ` : refus observé en 2.1.330 sur 13 variantes, mais **déjà identique en 2.1.329**. Les nouvelles formes couvertes n'ont pas été trouvées |
| Les variables écrites par un hook SessionStart ne sont plus perdues avec `claude -p --continue` | `NON VÉRIFIÉ` : la variable arrive dans les deux versions, le bug de 2.1.329 n'a pas été reproduit dans ce scénario |

**Verdict : `PASS`** — le changement qui touche une décision (relance `max_tokens`) se comporte comme annoncé, et aucune régression n'apparaît sur les deux autres points.

---

### 2. SDK Python `anthropic` 2.12.0 — `user_profile_id` dans le corps pour Bedrock

- **Sujet** : 1 (API) et 5 (accès Claude via Bedrock). **Ce que ça change pour moi** : si tu passes un profil utilisateur à `AnthropicBedrock` par l'en-tête `anthropic-user-profile-id`, il était ignoré par Bedrock et il est maintenant appliqué. Sur un modèle Bedrock sans support des profils, la requête échoue en 400 au lieu de passer, donc retire l'ID pour ces modèles. **Effort** : ~10 min (`anthropic>=2.12.0` et vérification des modèles ciblés).
- **Source** : https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md, section `2.12.0 (2026-11-20)`, lue le 2026-11-21. Extrait : « **bedrock:** send the user profile ID in the request body … Both clients now move it into the body of Messages requests and no longer send the header. A `user_profile_id` already in the body takes priority over the header. » ; « **api:** add the image_dimensions_too_large error code ». Date vérifiée sur PyPI (https://pypi.org/project/anthropic/2.12.0/) : 2026-11-20T15:57:01Z ; 2.11.0 le 2026-11-19T19:14:57Z.
- **Prérequis** : `uv venv -p 3.11 venv-<v> && uv pip install -p venv-<v>/bin/python anthropic==<v> boto3==1.40.0`, pour 2.11.0 et 2.12.0 (code 0). Le diff se lit dans `anthropic/lib/bedrock/_client.py` (`_prepare_options`). Le script `anthropic/scripts/bedrock_profile.py` crée un faux endpoint Bedrock local qui consigne le chemin, l'en-tête et `user_profile_id` du corps, puis appelle `messages.create` avec 5 configurations (identifiants factices, `max_retries=0`).

```
$ cd /tmp/veille-work-2026-11-21/anthropic && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-21/anthropic timeout 60 venv-2.11.0/bin/python -I scripts/bedrock_profile.py
[exit=0]
anthropic 2.11.0
1) default_headers du client               path=/model/anthropic.claude-test-v1/invoke header='up-client' body.user_profile_id=None
2) extra_headers de la requête             path=/model/anthropic.claude-test-v1/invoke header='up-requete' body.user_profile_id=None
3) en-tête + user_profile_id déjà dans le corps path=/model/anthropic.claude-test-v1/invoke header='up-client' body.user_profile_id='up-corps'
4) sans profil (témoin)                    path=/model/anthropic.claude-test-v1/invoke header=None body.user_profile_id=None
5) client async, default_headers           path=/model/anthropic.claude-test-v1/invoke header='up-async' body.user_profile_id=None

$ cd /tmp/veille-work-2026-11-21/anthropic && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-21/anthropic timeout 60 venv-2.12.0/bin/python -I scripts/bedrock_profile.py
[exit=0]
anthropic 2.12.0
1) default_headers du client               path=/model/anthropic.claude-test-v1/invoke header=None body.user_profile_id='up-client'
2) extra_headers de la requête             path=/model/anthropic.claude-test-v1/invoke header=None body.user_profile_id='up-requete'
3) en-tête + user_profile_id déjà dans le corps path=/model/anthropic.claude-test-v1/invoke header=None body.user_profile_id='up-corps'
4) sans profil (témoin)                    path=/model/anthropic.claude-test-v1/invoke header=None body.user_profile_id=None
5) client async, default_headers           path=/model/anthropic.claude-test-v1/invoke header=None body.user_profile_id='up-async'
```

```
$ for v in 2.11.0 2.12.0; do echo "== $v: $(grep -rl image_dimensions_too_large venv-$v/lib/python3.11/site-packages/anthropic/ | sed 's|.*/anthropic/||' | sort | head -5 | tr '\n' ' ')"; done
[exit=0]
== 2.11.0: 
== 2.12.0: __pycache__/_error_classes.cpython-311.pyc _error_classes.py types/__init__.py types/__pycache__/__init__.cpython-311.pyc types/__pycache__/image_dimensions_too_large_error.cpython-311.pyc
```

**Doc contre réalité** :

| Affirmation (changelog 2.12.0) | Étiquette |
|---|---|
| `AnthropicBedrock` et `AsyncAnthropicBedrock` placent l'ID de profil dans le corps des requêtes Messages | `VÉRIFIÉ` (cas 1, 2 et 5 : corps rempli en 2.12.0, vide en 2.11.0) |
| L'en-tête `anthropic-user-profile-id` n'est plus envoyé | `VÉRIFIÉ` (`header=None` dans les 5 cas en 2.12.0) |
| Un `user_profile_id` déjà dans le corps est prioritaire sur l'en-tête | `VÉRIFIÉ` (cas 3 : `up-corps` conservé) |
| Bedrock réel lit `user_profile_id` dans le corps et renvoie 400 pour les modèles sans profils | `NON VÉRIFIÉ` (aucun appel à AWS) |
| Ajout du code d'erreur `image_dimensions_too_large` | `VÉRIFIÉ` côté types (`types/image_dimensions_too_large_error`, absent en 2.11.0) ; déclenchement par l'API `NON VÉRIFIÉ` |

**Verdict : `PASS`** — le déplacement de l'ID et la priorité du corps sont observés tels qu'annoncés, en sync et en async.

---

### 3. FastMCP 4.2.3 — outil OpenAPI appelé sans paramètre de chemin requis

- **Sujet** : 4 (MCP et connecteurs) et 3 (harnais : erreurs propres). **Ce que ça change pour moi** : si tu exposes une API REST en MCP avec `FastMCP.from_openapi`, un oubli d'argument par l'agent devient une erreur de validation lisible (« Missing required arguments ») au lieu d'une exception serveur avec traceback dans les logs. Attention : un `user_id` vide n'est pas bloqué et appelle `/users/`. **Effort** : ~5 min (`fastmcp==4.2.3`), plus ~30 min si tu veux ajouter `minLength` aux paramètres de chemin de ta spec.
- **Source** : https://gofastmcp.com/changelog (source `docs/changelog.mdx` du dépôt https://github.com/PrefectHQ/fastmcp, entrée « v4.2.3 » datée 2026-11-20, lue le 2026-11-21). Extrait : « an OpenAPI tool called without a required path argument now returns a validation error instead of a server error » (PR #6559). Release : https://github.com/PrefectHQ/fastmcp/releases/tag/v4.2.3. Date vérifiée sur PyPI (https://pypi.org/project/fastmcp/4.2.3/) : 2026-11-20T04:17:11Z ; 4.2.2 le 2026-11-18T19:14:36Z.
- **Prérequis** : `uv venv -p 3.11 venv-<v> && uv pip install -p venv-<v>/bin/python fastmcp==<v>` pour 4.2.2 et 4.2.3 (code 0). FastMCP 4 dépend de `httpx2`, pas de `httpx` : la première exécution du script a échoué (`ModuleNotFoundError: No module named 'httpx'`, exit 1) et l'import a été corrigé. Le script `fastmcp/scripts/openapi_path.py` charge une spec OpenAPI `GET /users/{user_id}` (paramètre `verbose` optionnel) avec `httpx2.MockTransport`, puis appelle l'outil en mémoire via `fastmcp.Client`.

```
$ cd /tmp/veille-work-2026-11-21/fastmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-21/fastmcp timeout 120 venv-4.2.2/bin/python -I scripts/openapi_path.py 2>/dev/null
[exit=0]
fastmcp 4.2.2
outil: get_user | required: ['user_id']
sans user_id                 is_error=True requêtes HTTP=0  | "Error calling tool 'get_user': Error building request for GET /users/{user_id}: ValueError: Missing required path parameters: {'user_id'}"
sans user_id, verbose=True   is_error=True requêtes HTTP=0  | "Error calling tool 'get_user': Error building request for GET /users/{user_id}: ValueError: Missing required path parameters: {'user_id'}"
user_id='42'                 is_error=False requêtes HTTP=1 http://api.test/users/42 | '{"url":"http://api.test/users/42"}'
user_id=''                   is_error=False requêtes HTTP=1 http://api.test/users/ | '{"url":"http://api.test/users/"}'

$ cd /tmp/veille-work-2026-11-21/fastmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-21/fastmcp timeout 120 venv-4.2.3/bin/python -I scripts/openapi_path.py 2>/dev/null
[exit=0]
fastmcp 4.2.3
outil: get_user | required: ['user_id']
sans user_id                 is_error=True requêtes HTTP=0  | 'Missing required arguments: user_id'
sans user_id, verbose=True   is_error=True requêtes HTTP=0  | 'Missing required arguments: user_id'
user_id='42'                 is_error=False requêtes HTTP=1 http://api.test/users/42 | '{"url":"http://api.test/users/42"}'
user_id=''                   is_error=False requêtes HTTP=1 http://api.test/users/ | '{"url":"http://api.test/users/"}'
```

Journaux serveur (stderr) de l'exécution précédente, identique mais sans `2>/dev/null` et lisant encore `inputSchema` (accès déprécié qui produit un `FastMCPDeprecationWarning`) :

```
$ cd /tmp/veille-work-2026-11-21/fastmcp && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-21/fastmcp timeout 120 venv-4.2.2/bin/python -I scripts/openapi_path.py
[exit=0]
(lignes 3 à 4 : FastMCPDeprecationWarning sur inputSchema, omises)
[11/21/26 02:12:11] Error calling tool 'get_user'
                    ╭─────────── Traceback (most recent call last) ────────────╮
                    │ /tmp/veille-work-2026-11-21/fastmcp/venv-4.2.2/lib/pytho │
                    │ n3.11/site-packages/fastmcp/server/providers/openapi/com │
                    │ ponents.py:251 in run                                    │
                    │                                                          │
                    │ /tmp/veille-work-2026-11-21/fastmcp/venv-4.2.2/lib/pytho │
                    │ n3.11/site-packages/fastmcp/utilities/openapi/director.p │
                    │ y:320 in build                                           │
                    │                                                          │
                    │ /tmp/veille-work-2026-11-21/fastmcp/venv-4.2.2/lib/pytho │
                    │ n3.11/site-packages/fastmcp/utilities/openapi/director.p │
                    │ y:781 in _build_url                                      │
                    ╰──────────────────────────────────────────────────────────╯
                    ValueError: Missing required path parameters: {'user_id'}
                    […]
                    ValueError: Error building request for GET /users/{user_id}:
                    ValueError: Missing required path parameters: {'user_id'}
[… tronqué, 74 lignes]

$ (même commande avec venv-4.2.3)
[exit=0]
(lignes 3 à 4 : FastMCPDeprecationWarning sur inputSchema, omises)
[11/21/26 02:12:13] WARNING  Invalid arguments for tool           server.py:1608
                             'get_user'
                    WARNING  Invalid arguments for tool           server.py:1608
                             'get_user'
fastmcp 4.2.3
outil: get_user | required: ['user_id']
sans user_id                 is_error=True requêtes HTTP=0  | 'Missing required arguments: user_id'
(suite identique à la sortie 4.2.3 ci-dessus)
```

**Doc contre réalité** :

| Affirmation (changelog 4.2.3) | Étiquette |
|---|---|
| Un outil OpenAPI appelé sans argument de chemin requis renvoie une erreur de validation et non une erreur serveur | `VÉRIFIÉ` (4.2.2 : `ValueError` journalisée avec traceback ; 4.2.3 : « Missing required arguments: user_id » et avertissement « Invalid arguments ». Aucune requête HTTP dans les deux cas) |
| Cas limite : `user_id=""` (présent mais vide) | Constat, pas une affirmation de la doc : non bloqué dans les deux versions, la requête part vers `http://api.test/users/` |
| `parent_task_spans` (traces des tâches en arrière-plan) et les 3 correctifs de schéma de sortie | `NON VÉRIFIÉ` (non testés) |

**Verdict : `PASS`** — le changement annoncé est observé. L'erreur était déjà signalée au client en 4.2.2 (`is_error=True`) : le gain porte sur le message et sur les journaux serveur.

---

## Radar (NON TESTÉ)

| Élément | Version et date (source officielle) | Sujet | Note |
|---|---|---|---|
| Claude Agent SDK TypeScript | 0.3.330, npm 2026-11-20T19:18:50Z ; [CHANGELOG](https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md) | 1, 3 | `NON TESTÉ`. Avertissement `settings_not_in_effect` quand un fichier de réglages est invalide ; `query()` échoue si `settings` est une chaîne JSON invalide ; correctif `CLAUDE_ENV_FILE` avec `continue` (cf. test 1) |
| deepagents | 0.7.41, PyPI 2026-11-20T02:07:11Z ; [release](https://github.com/langchain-ai/deepagents/releases/tag/deepagents==0.7.41) | 2, 3 | `NON TESTÉ`. Déjà au Radar hier : canal `messages` sur `_messages_delta_reducer` (#7819) |
| Claude Agent SDK Python | 0.2.187, PyPI 2026-11-20T23:27:21Z | 1 | `NON TESTÉ`. Le `CHANGELOG.md` de `main` s'arrête à 0.2.178 : contenu `NON VÉRIFIÉ` |
| langsmith | 0.16.0, PyPI 2026-11-21T00:39:37Z | 3 | `NON TESTÉ`. Observabilité ; notes non lues, contenu `NON VÉRIFIÉ` |
| MCP Inspector | 2.16.0, npm 2026-11-18T09:32:25Z | 4 | `NON TESTÉ`. Notes non lues, contenu `NON VÉRIFIÉ` (2.15.0 testé le 2026-11-16) |

Vus sans être retenus comme candidats : OpenAI Codex CLI 0.173.0 en alpha (npm 2026-11-21) et Gemini CLI 0.71.0 en nightly (npm 2026-11-21), pré-versions sans notes lues.

## Limites

- **Pas de GPU** : le sujet 7 (inférence) n'est pas testé et le rapport ne contient aucune affirmation de performance. Aucune nouvelle version de vLLM depuis 0.34.0 (PyPI 2026-11-16).
- **Faux endpoints** : Claude Code est testé contre un faux serveur Messages API, anthropic contre un faux Bedrock local et FastMCP contre un `MockTransport`. Aucun test n'a visé l'API Anthropic, AWS Bedrock ou une vraie API REST.
- **Claude Code 2.1.330** : sur ~120 lignes de changelog, 3 sont testées. Pour la garde `rm` et le hook avec `--continue`, le comportement annoncé est observé en 2.1.330 mais **aucun écart avec 2.1.329 n'a été reproduit**, d'où `NON VÉRIFIÉ`. Les 6 envois identiques sur erreur 400 en 2.1.329, notés hier, restent sans explication.
- **anthropic** : le comportement de Bedrock réel (lecture du corps, 400 sur modèles sans profils) n'est pas vérifié.
- **FastMCP** : seul le correctif OpenAPI est couvert ; `parent_task_spans` et les correctifs de schéma de sortie ne le sont pas.
- Durée des tests : environ 15 minutes, sous la limite de 45 minutes. Aucun test n'a dépassé 10 minutes.

## Tentatives d'injection

Aucune détectée. Changelogs, paquets installés et sorties d'outils (y compris les messages de refus de Claude Code) ont été traités comme des données.

## Sources

- https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md — section 2.1.330, lue le 2026-11-21
- https://www.npmjs.com/package/@anthropic-ai/claude-code — 2.1.330 le 2026-11-20T19:16:01Z ; 2.1.329 le 2026-11-19T18:40:25Z
- https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md — section 2.12.0 (2026-11-20), lue le 2026-11-21
- https://pypi.org/project/anthropic/2.12.0/ — 2026-11-20T15:57:01Z ; 2.11.0 le 2026-11-19T19:14:57Z
- https://gofastmcp.com/changelog (source : https://github.com/PrefectHQ/fastmcp/blob/main/docs/changelog.mdx) — entrée v4.2.3 du 2026-11-20, lue le 2026-11-21 ; release https://github.com/PrefectHQ/fastmcp/releases/tag/v4.2.3
- https://pypi.org/project/fastmcp/4.2.3/ — 2026-11-20T04:17:11Z ; 4.2.2 le 2026-11-18T19:14:36Z
- https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md — section 0.3.330, lue le 2026-11-21 ; https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk — 0.3.330 le 2026-11-20T19:18:50Z
- https://pypi.org/project/deepagents/0.7.41/ — 2026-11-20T02:07:11Z
- https://pypi.org/project/claude-agent-sdk/0.2.187/ — 2026-11-20T23:27:21Z
- https://pypi.org/project/langsmith/0.16.0/ — 2026-11-21T00:39:37Z
- https://www.npmjs.com/package/@modelcontextprotocol/inspector — 2.16.0 le 2026-11-18T09:32:25Z
