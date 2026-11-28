# Veille IA — 2026-11-28

## TL;DR

- **Run du 2026-11-28** (fenêtre du 2026-11-21 au 2026-11-28) : **8 éléments détectés, 3 testés (3 PASS), 5 au Radar.** Tests A/B contre la version précédente, hors réseau (faux modèles, faux serveur MCP, plugin local). Aucune vraie API n'a été appelée.
- **MCP Inspector 2.17.0 : PASS.** Le garde SSRF bloque désormais les adresses NAT64 (`64:ff9b::/96`, `64:ff9b:1::/48`) et les formes IPv6 non canoniques qui menaient aux métadonnées cloud. 2.16.0 les laissait passer (6 adresses de test sur 13). `--verify` sur un catalogue de skills vide sort maintenant en code 13 au lieu d'afficher « Verified ».
- **pydantic-ai 2.77.0 / pydantic-ai-harness 0.77.0 : PASS.** Un résumé de compaction raté ne tue plus le run (2.76.0 : `UnexpectedModelBehavior`). `FallbackCompaction` passe à la stratégie suivante. Le détecteur de secrets masque les clés Google `AQ.` de 40 à 200 caractères.
- **Hermes Agent v0.23.4 : PASS.** `hermes plugins config <nom>` liste les réglages déclarés par un plugin (absent en v0.23.3, code 2). L'écrivain refuse les types faux, les choix hors liste, les clés inconnues et les secrets, et un lot avec une erreur n'écrit rien. L'éditeur interactif n'a pas été testé (pas de TTY).
- Aucune tentative d'injection relevée. Pas de GPU, donc aucun test de performance.

## Contexte et choix faits sans validation humaine

- Répertoire de travail : `/tmp/veille-work-2026-11-28/<élément>/` (`insp`, `pai`, `hermes`). Les commandes de test passent par le wrapper `bin/run <journal> "<commande>"`. Il consigne la commande, le code de sortie `[exit=…]` et la sortie tronquée à 40 lignes. Avec un pipe, `[exit=…]` est le code du dernier maillon. Le code du programme testé est donc affiché à part (`py_exit=${PIPESTATUS[0]}` ou `hermes_exit=$?`).
- Machine : Linux x86_64, Node v22.23.5, npm, uv, Python 3.11 (pydantic-ai) et 3.14.6 (Hermes), sans GPU.
- **Isolation** : chaque programme tourne sous `env -i HOME=<répertoire de travail> PATH=/usr/bin:/bin` (plus `/usr/local/bin` pour Node), avec `python -I`. Aucune variable d'environnement de la machine n'est lue et aucune clé n'est utilisée. La seule « clé » des tests est une chaîne factice construite dans le script.
- **Détection** : versions et dates viennent des registres officiels (API JSON de PyPI, `npm view <paquet> time --json`, `git ls-remote --tags`). Les notes viennent des pages de releases GitHub (lues avec un outil de lecture web), recoupées avec le diff ou le code des paquets installés.
- **Sélection** : Claude Code (2.1.332), les Agent SDK TS (0.3.332) et Python (0.2.189), anthropic (2.14.0), langchain-core (1.8.5), langchain-anthropic (1.7.13), deepagents (0.7.42), LangGraph (1.2.24) et FastMCP (4.2.6 / 4.2.7a1) n'ont pas de version plus récente que celles déjà testées. J'ai retenu :
  - MCP Inspector 2.17.0 (sujets 3 et 4 : sécurité d'un outil MCP, skills MCP) ;
  - pydantic-ai 2.77.0 avec pydantic-ai-harness 0.77.0 (sujet 3 : reprise sur erreur, garde-fous ; sujet 5 : harnais concurrent). Il était au Radar les jours précédents ;
  - Hermes Agent v0.23.4 (sujet 2 : plugins). Il était au Radar le 2026-11-27. `tested.md` ne contient que v0.23.1, donc ce n'est pas un doublon.

  Aucun de ces éléments ne figure dans `tested.md` à ces versions.
- **Scripts** : copie exacte dans [`reports/scripts-2026-11-28/`](scripts-2026-11-28/). Pour refaire un test, copie `run` dans `/tmp/veille-work-2026-11-28/bin/` et chaque script dans `/tmp/veille-work-2026-11-28/<élément>/scripts/`. Pour Hermes, copie aussi `hermes/demo-config/` dans `<HOME>/.hermes/plugins/demo-config/`.
- Durée des tests : environ 35 minutes, sous la limite de 45 minutes. L'installation de Hermes (4 essais, voir le test 3) a pris le plus de temps. Aucun test n'a dépassé 10 minutes.

---

## Tests

### 1. MCP Inspector 2.17.0 — garde SSRF contre les adresses NAT64, `--verify` sur un catalogue vide

- **Sujet** : 3 (sécurité du harnais) et 4 (MCP). **Ce que ça change pour moi** : sur une machine cloud avec NAT64 (IPv6 seul), un serveur MCP malveillant pouvait faire lire les métadonnées cloud au backend d'Inspector 2.16.0 via une adresse `64:ff9b::…`. Mets à jour, et utilise `--verify` en CI : un catalogue vide échoue enfin. **Effort** : ~5 min (`npx @modelcontextprotocol/inspector@2.17.0`).
- **Source** : https://github.com/modelcontextprotocol/inspector/releases (2.17.0 « released 27 Nov », avis GHSA-v2gx-m79c-pvxj, PR #3050 et #3012). Date vérifiée sur npm : 2.17.0 publiée le 2026-11-27T10:01:46.446Z (2.16.0 : 2026-11-18T09:32:25.116Z).
- **Prérequis** : `npm install --prefix ./v<version> --no-audit --no-fund --ignore-scripts @modelcontextprotocol/inspector@<version>` pour 2.16.0 et 2.17.0 (sortie : `added 120 packages in 11s` puis `in 5s`).
- **Méthode** : `scripts/guard_check.mjs` extrait du bundle `clients/web/build/index.js` le code compris entre `const METADATA_IPV4_ADDRESSES` et `function bareHost(`, l'évalue avec `isIP` de `node:net`, puis appelle `isBlockedAddress` sur 13 adresses. En 2.17.0, c'est cette fonction que `assertNoneBlocked` appelle depuis `createPinningLookup`, sur les adresses résolues par DNS (code lu, lignes ~2381-2400). Pas d'appel réseau : le 2026-11-16, le test de bout en bout vers des adresses de métadonnées avait été refusé par le garde-fou de la session.

**a) Garde SSRF, A/B**

```
$ cd /tmp/veille-work-2026-11-28/insp && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-28/insp node v2.16.0/node_modules/@modelcontextprotocol/inspector/clients/launcher/build/index.js --version && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-28/insp node scripts/guard_check.mjs v2.16.0/node_modules/@modelcontextprotocol/inspector/clients/web/build/index.js
[exit=0]
2.16.0
169.254.169.254              BLOQUÉ    IPv4 métadonnées
::ffff:169.254.169.254       BLOQUÉ    IPv4 mappée, forme courte
0:0:0:0:0:ffff:a9fe:a9fe     autorisé  IPv4 mappée, forme longue
64:ff9b::a9fe:a9fe           autorisé  NAT64 64:ff9b::/96 -> 169.254.169.254
64:ff9b::169.254.169.254     autorisé  NAT64 /96, IPv4 pointée
64:ff9b::6464:64c8           autorisé  NAT64 /96 -> 100.100.100.200
64:ff9b:1:a9fe:a9:fe00::     autorisé  NAT64 local 64:ff9b:1::/48 -> 169.254.169.254
64:ff9b::808:808             autorisé  NAT64 /96 -> 8.8.8.8 (public)
FE80::1                      BLOQUÉ    lien-local en majuscules
fd00:ec2:0:0::254            autorisé  métadonnées AWS IPv6, forme non canonique
fd00:ec2::254                BLOQUÉ    métadonnées AWS IPv6
2001:db8::1                  autorisé  IPv6 ordinaire
8.8.8.8                      autorisé  IPv4 publique

$ cd /tmp/veille-work-2026-11-28/insp && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-28/insp node v2.17.0/node_modules/@modelcontextprotocol/inspector/clients/launcher/build/index.js --version && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-28/insp node scripts/guard_check.mjs v2.17.0/node_modules/@modelcontextprotocol/inspector/clients/web/build/index.js
[exit=0]
2.17.0
169.254.169.254              BLOQUÉ    IPv4 métadonnées
::ffff:169.254.169.254       BLOQUÉ    IPv4 mappée, forme courte
0:0:0:0:0:ffff:a9fe:a9fe     BLOQUÉ    IPv4 mappée, forme longue
64:ff9b::a9fe:a9fe           BLOQUÉ    NAT64 64:ff9b::/96 -> 169.254.169.254
64:ff9b::169.254.169.254     BLOQUÉ    NAT64 /96, IPv4 pointée
64:ff9b::6464:64c8           BLOQUÉ    NAT64 /96 -> 100.100.100.200
64:ff9b:1:a9fe:a9:fe00::     BLOQUÉ    NAT64 local 64:ff9b:1::/48 -> 169.254.169.254
64:ff9b::808:808             autorisé  NAT64 /96 -> 8.8.8.8 (public)
FE80::1                      BLOQUÉ    lien-local en majuscules
fd00:ec2:0:0::254            BLOQUÉ    métadonnées AWS IPv6, forme non canonique
fd00:ec2::254                BLOQUÉ    métadonnées AWS IPv6
2001:db8::1                  autorisé  IPv6 ordinaire
8.8.8.8                      autorisé  IPv4 publique
```
La cause, lue dans le code : 2.16.0 compare des chaînes (`/^::ffff:(.+)$/`, `addr === "fd00:ec2::254"`). 2.17.0 décode les 8 groupes de 16 bits (`ipv6Groups`) et extrait l'IPv4 embarquée des préfixes NAT64 (`nat64EmbeddedIpv4s`).

**b) `--verify` sur un catalogue de skills vide (cas limite, PR #3012)**

`scripts/skills_server.py` est un serveur MCP stdio de 20 lignes. Il déclare l'extension `io.modelcontextprotocol/skills` et répond `{"skills": []}` à `skills/list`.

```
$ cd /tmp/veille-work-2026-11-28/insp && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-28/insp timeout 60 node v2.16.0/node_modules/@modelcontextprotocol/inspector/clients/cli/build/index.js /usr/bin/python3 -I scripts/skills_server.py --method skills/list --verify
[exit=0]
Verified 0 skills and 0 files: no conformance errors.

$ cd /tmp/veille-work-2026-11-28/insp && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-28/insp timeout 60 node v2.17.0/node_modules/@modelcontextprotocol/inspector/clients/cli/build/index.js /usr/bin/python3 -I scripts/skills_server.py --method skills/list --verify
[exit=13]
No skills to verify: skills/list returned an empty catalog, so nothing was checked.
{"error":{"code":"skills_empty","message":"No skills to verify: skills/list returned an empty catalog, so nothing was checked."}}
```

**Doc contre réalité** (notes 2.17.0) :

| Affirmation | Étiquette |
|---|---|
| Le garde compare les adresses IPv6 par valeur et revérifie l'IPv4 embarquée (NAT64, `::ffff:0:0/96`) | `VÉRIFIÉ` au niveau de la fonction : 6 adresses autorisées en 2.16.0 sont bloquées en 2.17.0 (`0:0:0:0:0:ffff:a9fe:a9fe`, 3 formes NAT64 /96, la forme /48 et `fd00:ec2:0:0::254`) |
| Les adresses NAT64 qui embarquent une IPv4 publique restent autorisées | `VÉRIFIÉ` (`64:ff9b::808:808` autorisée) |
| Un serveur MCP malveillant pouvait atteindre les métadonnées cloud via NAT64 (de bout en bout) | `NON VÉRIFIÉ` (pas de réseau NAT64 ni de requête réseau vers ces adresses ; seul le chemin de code a été lu) |
| `--verify` échoue sur un catalogue de skills vide au lieu de dire « Verified » | `VÉRIFIÉ` (exit 0 et « Verified 0 skills » en 2.16.0 ; exit 13 et `skills_empty` en 2.17.0) |
| Extension Events (SEP-3415), en-têtes OAuth, `MCP_CATALOG_PATH` ignoré avec `--config` | `NON VÉRIFIÉ` (non testés) |

**Verdict : `PASS`** — le garde bloque les formes NAT64 et non canoniques en A/B, et `--verify` sur un catalogue vide échoue avec le code 13.

---

### 2. pydantic-ai 2.77.0 / pydantic-ai-harness 0.77.0 — compaction qui échoue sans tuer le run, clés Google `AQ.`

- **Sujet** : 3 (reprise sur erreur, garde-fous) et 5 (harnais concurrent). **Ce que ça change pour moi** : un modèle de résumé qui répond mal ne fait plus perdre un long run. C'est le comportement à copier dans mon propre harnais (compaction au mieux, run d'abord). Attention : chaque essai de résumé raté compte dans l'usage du run (8 appels du résumeur dans le test a). **Effort** : ~15 min pour passer en 2.77.0/0.77.0, ~1 h pour reproduire ce comportement chez moi.
- **Source** : https://github.com/pydantic/pydantic-ai/releases (v2.77.0 du 2026-11-27, notes de compatibilité #12655 et #13551). Le code modifié se trouve dans le paquet `pydantic-ai-harness`, publié en même temps. Dates vérifiées sur PyPI : pydantic-ai-slim 2.77.0 le 2026-11-28T00:01:23Z (2.76.0 : 2026-11-27T00:59:58Z), pydantic-ai-harness 0.77.0 le 2026-11-28T00:01:26Z (0.76.0 : 2026-11-27T01:00:02Z).
- **Prérequis** : `uv venv -q -p 3.11 v<v>` puis `VIRTUAL_ENV=v<v> uv pip install -q pydantic-ai-slim==<v> pydantic-ai-harness==<h>`, avec (2.76.0, 0.76.0) et (2.77.0, 0.77.0). Le script imprime les versions résolues.
- **Diff des paquets installés** : dans `guardrails/detectors.py`, `'google_api_key'` passe de `\bAIza[A-Za-z0-9_-]{35}` à `\b(?:AIza[A-Za-z0-9_-]{35}|AQ\.[A-Za-z0-9_-]{40,200}(?![A-Za-z0-9_-]))`. Dans `compaction/_fallback_compaction.py`, `fallback_on` gagne `UnexpectedModelBehavior`. `SummarizingCompaction` reçoit `skip_on=(UnexpectedModelBehavior, ModelAPIError, FallbackExceptionGroup)`.
- **Scénario** (`scripts/pai_test.py <mode>`) :
  - `secrets` : `detectors.secret_data(only=["google_api_key"])` est appliqué à 8 chaînes factices.
  - `summarizing` et `fallback` : un `Agent` avec un faux modèle (`FunctionModel`) appelle 6 fois l'outil `lire`, puis répond `FIN`. Le résumeur est un autre `FunctionModel` qui renvoie toujours un texte vide. `summarizing` : `SummarizingCompaction(max_messages=6, keep_messages=2, retries=1)`. `fallback` : `FallbackCompaction([SummarizingCompaction(…), SlidingWindowCompaction(keep_messages=2)], max_tokens=150)`.

**a) Compaction dont le résumé échoue**

```
$ cd /tmp/veille-work-2026-11-28/pai && env -i HOME=/tmp/veille-work-2026-11-28/pai PATH=/usr/bin:/bin v2.76.0/bin/python -I scripts/pai_test.py summarizing 2>&1 | grep -v Warning | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
pydantic-ai-slim 2.76.0 | harness 0.76.0
  RUN TUÉ : UnexpectedModelBehavior Exceeded maximum output retries (1)
  appels au résumeur : 2
py_exit=0

$ cd /tmp/veille-work-2026-11-28/pai && env -i HOME=/tmp/veille-work-2026-11-28/pai PATH=/usr/bin:/bin v2.77.0/bin/python -I scripts/pai_test.py summarizing 2>&1 | grep -v Warning | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
pydantic-ai-slim 2.77.0 | harness 0.77.0
  run terminé : FIN après 6 outils, 13 messages vus
  messages dans l'historique final : 14
  appels au résumeur : 8
py_exit=0

$ cd /tmp/veille-work-2026-11-28/pai && env -i HOME=/tmp/veille-work-2026-11-28/pai PATH=/usr/bin:/bin v2.76.0/bin/python -I scripts/pai_test.py fallback 2>&1 | grep -v Warning | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
pydantic-ai-slim 2.76.0 | harness 0.76.0
  RUN TUÉ : UnexpectedModelBehavior Exceeded maximum output retries (1)
  appels au résumeur : 2
py_exit=0

$ cd /tmp/veille-work-2026-11-28/pai && env -i HOME=/tmp/veille-work-2026-11-28/pai PATH=/usr/bin:/bin v2.77.0/bin/python -I scripts/pai_test.py fallback 2>&1 | grep -v Warning | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
pydantic-ai-slim 2.77.0 | harness 0.77.0
  run terminé : FIN après 6 outils, 5 messages vus
  messages dans l'historique final : 6
  appels au résumeur : 4
py_exit=0
```
(`py_exit=0` en 2.76.0 parce que le script intercepte l'exception pour l'afficher ; le run de l'agent, lui, s'arrête.) En `summarizing` 2.77.0, l'historique reste entier (14 messages) : la compaction est abandonnée et le run continue. En `fallback` 2.77.0, il tombe à 6 messages : c'est `SlidingWindowCompaction` qui a pris le relais.

*Passage écarté et relancé* : dans ma première version, le faux modèle comptait les retours d'outil dans l'historique. En `fallback` 2.77.0, la fenêtre glissante coupait cet historique, donc le faux modèle relançait l'outil sans fin. Le run s'est arrêté sur `UsageLimitExceeded … request_limit of 50` après 26 appels au résumeur. C'était un défaut de mon script, pas de la bibliothèque. Je l'ai corrigé avec un compteur interne au faux modèle et j'ai relancé les 6 commandes (sorties ci-dessus). Un premier affichage du test `secrets` montrait aussi « (inchangé) » à tort (mauvais attribut lu, `value` au lieu de `replacement`). Corrigé et relancé, les actions `replace`/`allow` étaient identiques.

**b) Détecteur de secrets : clés Google `AQ.`**

```
$ cd /tmp/veille-work-2026-11-28/pai && env -i HOME=/tmp/veille-work-2026-11-28/pai PATH=/usr/bin:/bin v2.76.0/bin/python -I scripts/pai_test.py secrets 2>&1 | grep -v Warning | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
pydantic-ai-slim 2.76.0 | harness 0.76.0
  AIza legacy (35)                       -> replace | cle=[redacted:google_api_key]
  AQ. 50 car.                            -> allow   | (inchangé)
  AQ. 40 car. (plancher)                 -> allow   | (inchangé)
  AQ. 39 car. (sous le plancher)         -> allow   | (inchangé)
  AQ. 200 car. (plafond)                 -> allow   | (inchangé)
  AQ. 201 car. (au-delà)                 -> allow   | (inchangé)
  nom pointé AQ.average_response_time    -> allow   | (inchangé)
  dans du JSON                           -> allow   | (inchangé)
py_exit=0

$ cd /tmp/veille-work-2026-11-28/pai && env -i HOME=/tmp/veille-work-2026-11-28/pai PATH=/usr/bin:/bin v2.77.0/bin/python -I scripts/pai_test.py secrets 2>&1 | grep -v Warning | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
pydantic-ai-slim 2.77.0 | harness 0.77.0
  AIza legacy (35)                       -> replace | cle=[redacted:google_api_key]
  AQ. 50 car.                            -> replace | cle=[redacted:google_api_key]
  AQ. 40 car. (plancher)                 -> replace | cle=[redacted:google_api_key]
  AQ. 39 car. (sous le plancher)         -> allow   | (inchangé)
  AQ. 200 car. (plafond)                 -> replace | cle=[redacted:google_api_key]
  AQ. 201 car. (au-delà)                 -> allow   | (inchangé)
  nom pointé AQ.average_response_time    -> allow   | (inchangé)
  dans du JSON                           -> replace | {"key": "[redacted:google_api_key]"}
py_exit=0
```
Toutes les « clés » sont factices et générées par le script (répétitions de `x`, `y`, `B`, `Ab3_d-`).

**Doc contre réalité** (notes v2.77.0) :

| Affirmation | Étiquette |
|---|---|
| #12655 : un échec de `SummarizingCompaction` automatique garde le run parent en vie | `VÉRIFIÉ` (2.76.0 : `UnexpectedModelBehavior` ; 2.77.0 : le run se termine, historique inchangé) |
| #12655 : la chaîne `FallbackCompaction` par défaut se rattrape d'un `UnexpectedModelBehavior` | `VÉRIFIÉ` (2.77.0 : la fenêtre glissante prend le relais, 6 messages) |
| Docstring : chaque nouvel essai est une vraie requête comptée dans l'usage du run | `VÉRIFIÉ` indirectement (résumeur appelé 8 fois ; la limite de 50 requêtes a été atteinte dans le passage écarté) |
| Docstring : un appel explicite à `compact()`/`compact_now()` lève toujours l'erreur | `NON VÉRIFIÉ` (non testé) |
| #13551 : le motif `google_api_key` masque aussi les clés `AQ.` de 40 à 200 caractères | `VÉRIFIÉ` (40, 50, 200 et JSON masqués ; 39 et 201 laissés ; nom pointé laissé) |
| Autres notes (stockage `ConversationStore`, `thinking_summary`, autorité des sous-agents…) | `NON VÉRIFIÉ` (non testées) |

**Verdict : `PASS`** — les deux changements testés se comportent comme annoncé en A/B, hors réseau, avec de faux modèles.

---

### 3. Hermes Agent v0.23.4 — `hermes plugins config <nom>`

- **Sujet** : 2 (Hermes Agent, plugins officiels). **Ce que ça change pour moi** : un plugin qui déclare un `config_schema` gagne un éditeur de réglages sans code, et les secrets vont dans `.env`, jamais dans `config.yaml`. Je peux donc distribuer un plugin perso configurable sans écrire d'assistant. **Effort** : ~30 min pour déclarer le schéma d'un plugin existant.
- **Source** : https://github.com/NousResearch/hermes-agent/releases (v0.23.4 marquée « Latest », datée du 24 nov. 2026 sur la page ; les notes disent « Release Date: November 23, 2026 » et citent `hermes plugins config` parmi les points forts). Tag vérifié : `git ls-remote` donne `refs/tags/v0.23.4^{}` = `8fc0374447313e276f6b9a2764bfc750190c966a`, commit daté du 2026-11-23T23:04:14-08:00 (v0.23.3 : `caafe538…`, 2026-11-19T12:51:15-08:00). Doc lue dans le dépôt : `website/docs/developer-guide/plugins/index.md`, lignes ~1101-1140.
- **Installation** (4 essais, consignés tels quels) :
  1. `uv pip install ./src-v0.23.4` (Python 3.11) : refusé par `setup.py` (« Building wheels or sdists for hermes-agent is not supported … use an editable install »). C'est une consigne d'installation du projet, pas une injection : elle ne demande rien hors installation.
  2. `uv pip install -e` (Python 3.11) : exit 0, mais `hermes` plante (`ModuleNotFoundError: No module named 'ruamel'`). Les dépendances ne sont déclarées que pour `python_version >= '3.14'`.
  3. `uv pip install -e` (Python 3.14.6) : échec de résolution (`browser-harness==0.1.13 depends on pillow==12.3.0` contre `pillow==13.0.0`). Le dépôt résout ce conflit par `[tool.uv] override-dependencies`.
  4. Commande retenue, sans exécuter le script `activate` :
     ```
     $ cd /tmp/veille-work-2026-11-28/hermes && git -c advice.detachedHead=false clone -q --depth 1 --branch v0.23.4 https://github.com/NousResearch/hermes-agent.git src-v0.23.4   # idem v0.23.3
     $ uv venv -q -p 3.14 venv-v0.23.4 && UV_PROJECT_ENVIRONMENT=$PWD/venv-v0.23.4 uv sync -q --frozen --python 3.14 --project src-v0.23.4; echo sync=$?
     v0.23.3 sync=0
     v0.23.4 sync=0
     ```
- **Scénario** : chaque version a son `HOME` jetable. Le plugin local `demo-config` (copié dans `<HOME>/.hermes/plugins/`, `__init__.py` vide) déclare 4 réglages : `api_url`, `retries` (int), `mode` (choix `fast`/`careful`) et `api_key` (`type: secret`, requis), recopiés de l'exemple de la doc. `hermes plugins list` le montre `not enabled`, source `user`, dans les deux versions (sortie dans le journal, non reproduite).

**a) Quickstart : la commande, A/B (stdin non-TTY, donc mode listing)**

```
$ cd /tmp/veille-work-2026-11-28/hermes && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-28/hermes/home-v0.23.3 HERMES_HOME=/tmp/veille-work-2026-11-28/hermes/home-v0.23.3/.hermes HERMES_NONINTERACTIVE=1 timeout 120 venv-v0.23.3/bin/hermes plugins config demo-config < /dev/null > out-0233.txt 2>&1; echo hermes_exit=$?; cat out-0233.txt
[exit=0]
hermes_exit=2
hermes plugins: 'config' is not a `hermes plugins` command.
Run `hermes plugins --help` to see all commands.

$ cd /tmp/veille-work-2026-11-28/hermes && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-28/hermes/home-v0.23.4 HERMES_HOME=/tmp/veille-work-2026-11-28/hermes/home-v0.23.4/.hermes HERMES_NONINTERACTIVE=1 timeout 120 venv-v0.23.4/bin/hermes plugins config demo-config < /dev/null 2>&1 | cut -c1-200 | tail -20
[exit=0]
demo-config settings:
  API URL: https://api.example.com
    plugins.entries.demo-config.settings.api_url — Service endpoint
  Retries: 3
    plugins.entries.demo-config.settings.retries
  Mode: fast
    plugins.entries.demo-config.settings.mode
  API key: not set  (required)
    .env DEMO_CONFIG_API_KEY — Personal access token
Run `hermes plugins config demo-config` in a terminal to change them.

$ cd /tmp/veille-work-2026-11-28/hermes && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-28/hermes/home-v0.23.4 HERMES_HOME=/tmp/veille-work-2026-11-28/hermes/home-v0.23.4/.hermes HERMES_NONINTERACTIVE=1 timeout 120 venv-v0.23.4/bin/hermes plugins config inexistant < /dev/null > out-0234c.txt 2>&1; echo hermes_exit=$?; cat out-0234c.txt
[exit=0]
hermes_exit=1
Plugin 'inexistant' not found.
List installed plugins: hermes plugins list
```

**b) Cas limite : l'écrivain partagé par l'éditeur (`save_plugin_settings`)**

`scripts/settings_test.py` appelle directement `save_plugin_settings`, la fonction que l'éditeur appelle pour chaque champ non secret. Il relit ensuite les valeurs et `config.yaml`.

```
$ cd /tmp/veille-work-2026-11-28/hermes && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-28/hermes/home-v0.23.4 HERMES_HOME=/tmp/veille-work-2026-11-28/hermes/home-v0.23.4/.hermes HERMES_NONINTERACTIVE=1 timeout 120 venv-v0.23.4/bin/python -I scripts/settings_test.py 2>&1 | cut -c1-260; echo py_exit=${PIPESTATUS[0]}
[exit=0]
  OK   {'retries': 5, 'mode': 'careful'} -> ['retries', 'mode']
  REFUS {'retries': True} -> ValueError 'retries' should be number (got bool)
  REFUS {'retries': '5'} -> ValueError 'retries' should be number (got str)
  REFUS {'mode': 'turbo'} -> ValueError 'mode' must be one of the declared choices
  REFUS {'api_key': 'faux-jeton-de-test'} -> ValueError 'api_key' is a secret; it is stored in .env, not config.yaml
  REFUS {'inconnu': 1} -> ValueError 'inconnu' is not declared in the plugin's config_schema
  REFUS {'retries': 7, 'mode': 'turbo'} -> ValueError 'mode' must be one of the declared choices
  valeurs relues : {'api_url': 'https://api.example.com', 'retries': 5, 'mode': 'careful', 'api_key': '(secret, has_value=False)'}
  config.yaml contient 'faux-jeton' : False
  extrait config.yaml : ['    demo-config:', '        retries: 5', '        mode: careful']
py_exit=0

$ cd /tmp/veille-work-2026-11-28/hermes && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-28/hermes/home-v0.23.4 HERMES_HOME=/tmp/veille-work-2026-11-28/hermes/home-v0.23.4/.hermes HERMES_NONINTERACTIVE=1 timeout 120 venv-v0.23.4/bin/hermes plugins config demo-config < /dev/null > out-0234b.txt 2>&1; echo hermes_exit=$?; head -8 out-0234b.txt
[exit=0]
hermes_exit=0
demo-config settings:
  API URL: https://api.example.com
    plugins.entries.demo-config.settings.api_url — Service endpoint
  Retries: 5
    plugins.entries.demo-config.settings.retries
  Mode: careful
    plugins.entries.demo-config.settings.mode
  API key: not set  (required)
```
Le lot `{'retries': 7, 'mode': 'turbo'}` est refusé en entier : `retries` reste à 5, l'écriture n'est pas partielle.

**Doc contre réalité** (notes v0.23.4 et doc développeur du dépôt) :

| Affirmation | Étiquette |
|---|---|
| `hermes plugins config <name>` liste chaque clé de `config_schema` avec sa valeur courante | `VÉRIFIÉ` (absent en v0.23.3, exit 2 ; listing complet en v0.23.4, valeurs à jour après écriture) |
| Les secrets ne touchent jamais `config.yaml` : seuls le nom `.env` et la présence d'une valeur sont exposés | `VÉRIFIÉ` (écriture du secret refusée, `has_value=False`, chaîne absente de `config.yaml`) |
| Les valeurs dont le type ou les `choices` contredisent le schéma sont refusées | `VÉRIFIÉ` (bool et str pour un int, choix hors liste, clé inconnue refusés) |
| L'éditeur interactif (sélecteurs pour choix et booléens, saisie masquée des secrets) | `NON VÉRIFIÉ` (pas de TTY dans cette session ; seul le mode listing a été exécuté) |
| Les réglages s'affichent aussi dans l'app Desktop (Settings → Plugins) | `NON VÉRIFIÉ` (pas d'interface graphique) |
| Autres points forts de v0.23.4 (`hermes gateway migrate --backends`, modèles Gemini 4, longueur des descriptions de l'index de skills) | `NON VÉRIFIÉ` (non testés) |

**Verdict : `PASS`** — la commande existe et liste les réglages, et l'écrivain applique toutes les règles annoncées. L'éditeur interactif reste à tester dans un vrai terminal.

---

## Radar (NON TESTÉ)

| Élément | Version et date (source officielle) | Sujet | Note |
|---|---|---|---|
| `@anthropic-ai/sdk` (TypeScript) | 1.14.0, npm 2026-11-24T21:07:30Z ; [releases](https://github.com/anthropics/anthropic-sdk-typescript/releases) (« 24 Nov ») | 1 | `NON TESTÉ`. Ajouts d'API d'administration (contrôles de données Google Cloud, dossiers de revue de conformité). Il faudrait un compte d'organisation pour les tester. Pour moi : aucune décision. Effort ~30 min |
| MCP Inspector (ligne v1, dépréciée) | 1.0.7, npm 2026-11-27T07:31:30Z ; [releases](https://github.com/modelcontextprotocol/inspector/releases) | 3, 4 | `NON TESTÉ`. Même correctif NAT64 (GHSA-v2gx-m79c-pvxj) rétroporté. Pour moi : si une vieille config utilise encore la v1, passer en 1.0.7 ou en 2.17.0. Effort ~5 min |
| OpenAI Codex CLI | 0.174.0-alpha.9, npm 2026-11-27T17:16:52Z ; https://www.npmjs.com/package/@openai/codex | 5 | `NON TESTÉ`. Préversion alpha d'un concurrent, notes non lues. Pour moi : attendre la stable. Effort ~1 h |
| `@langchain/core` (JS) | 1.5.1, npm 2026-11-24T03:51:37Z (1.5.0 : 2026-11-20T18:55:04Z) ; https://www.npmjs.com/package/@langchain/core | 2 | `NON TESTÉ`. Contenu `NON VÉRIFIÉ` (notes non lues). Je n'utilise LangGraph qu'en Python. Effort ~30 min |
| openai-agents (SDK Python) | 0.26.0, PyPI 2026-11-24T03:24:11Z ; [release](https://github.com/openai/openai-agents-python/releases/tag/v0.26.0) | 5 | `NON TESTÉ`. Déjà au Radar depuis le 25/11. Pour moi : à suivre seulement si je compare les SDK d'agents. Effort ~1 h |

Vus sans être retenus : Claude Code 2.1.332, Agent SDK TS 0.3.332 et Python 0.2.189, anthropic 2.14.0, langchain-core 1.8.5, langchain-anthropic 1.7.13, deepagents 0.7.42, LangGraph 1.2.24, FastMCP 4.2.6 et 4.2.7a1 : déjà testés et sans version plus récente. langsmith 0.16.2 (2026-11-24) et llama-cpp-python 0.3.38 (2026-11-23) sont écartés pour tenir le plafond de 8 candidats ; llama-cpp-python relève de l'inférence (pas de GPU, veille seulement). vLLM 0.34.0 date du 2026-11-16, hors fenêtre. Une recherche web sur les annonces d'Anthropic en novembre n'a rien renvoyé de daté et vérifiable à la source dans la fenêtre.

## Limites

- **Pas de GPU** : le sujet 7 (inférence) n'est pas testé, et le rapport ne contient aucune affirmation de performance.
- **Hors réseau et faux environnements** : faux modèles (`FunctionModel`), faux serveur MCP stdio, plugin Hermes local sans code. Aucun vrai fournisseur ni aucune vraie adresse de métadonnées n'ont été contactés. Le blocage NAT64 n'est donc vérifié qu'au niveau de la fonction de garde, pas de bout en bout.
- **Non couverts** :
  - Inspector : extension Events, en-têtes OAuth, `MCP_CATALOG_PATH`.
  - pydantic-ai : `compact()` explicite, stockages `ConversationStore`, autres notes de compatibilité.
  - Hermes : éditeur interactif (pas de TTY), app Desktop, autres nouveautés de v0.23.4.
- **Installation de Hermes** : il a fallu Python 3.14 et `uv sync --frozen`, l'installation `pip` ordinaire ne marche pas (voir test 3). Le script `activate` du dépôt n'a pas été exécuté.
- Deux passages de test pydantic-ai ont été écartés puis relancés à cause d'erreurs dans mon script. Ils sont décrits sous le test 2.

## Tentatives d'injection

Aucune détectée. Pages de releases, code et docs des dépôts, messages d'installation et sorties d'outils ont été traités comme des données. Le message de `setup.py` de Hermes (« use an editable install instead ») est une consigne d'installation ordinaire. Je ne l'ai suivie qu'avec un gestionnaire de paquets (`uv`), sans lancer le script `activate` qu'il cite.

## Sources

- https://github.com/modelcontextprotocol/inspector/releases — 2.17.0 et 1.0.7, 27 nov. 2026 (GHSA-v2gx-m79c-pvxj, PR #3050, #3051, #3012)
- https://www.npmjs.com/package/@modelcontextprotocol/inspector — 2.17.0 : 2026-11-27T10:01:46Z ; 1.0.7 : 2026-11-27T07:31:30Z ; 2.16.0 : 2026-11-18T09:32:25Z
- https://github.com/pydantic/pydantic-ai/releases — v2.77.0, 2026-11-27 (#12655, #13551)
- https://pypi.org/project/pydantic-ai-slim/2.77.0/ — 2026-11-28T00:01:23Z (2.76.0 : 2026-11-27T00:59:58Z)
- https://pypi.org/project/pydantic-ai-harness/0.77.0/ — 2026-11-28T00:01:26Z (0.76.0 : 2026-11-27T01:00:02Z)
- https://github.com/NousResearch/hermes-agent/releases — v0.23.4, 24 nov. 2026 (notes : 23 nov. 2026) ; tag `v0.23.4` → commit 8fc03744…, 2026-11-23T23:04:14-08:00
- https://github.com/anthropics/anthropic-sdk-typescript/releases — sdk-v1.14.0, 24 nov. ; npm 2026-11-24T21:07:30Z
- https://www.npmjs.com/package/@openai/codex — 0.174.0-alpha.9 : 2026-11-27T17:16:52Z
- https://www.npmjs.com/package/@langchain/core — 1.5.1 : 2026-11-24T03:51:37Z
- https://github.com/openai/openai-agents-python/releases/tag/v0.26.0 — PyPI 2026-11-24T03:24:11Z
