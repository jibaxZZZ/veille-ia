# Veille IA — 2026-11-20

## TL;DR

- **Run du 2026-11-20** (fenêtre du 2026-11-13 au 2026-11-20) : **8 éléments détectés, 3 testés (3 PASS), 5 au Radar.** Les 3 tests sont des A/B contre la version précédente.
- **Claude Code 2.1.329 : PASS.** La relance automatique à la limite citée dans une erreur `max_tokens` (ajoutée en 2.1.326) a disparu : derrière une passerelle qui plafonne la sortie, la requête échoue (`API Error: 400`, code 1) au lieu de réussir. `CLAUDE_CODE_MAX_OUTPUT_TOKENS` corrige, comme annoncé.
- **SDK Python anthropic 2.11.0 : PASS.** Un espace dans la query string part en `%20` et non plus en `+`. Avec un vérificateur SigV4 local au comportement de serveur AWS, la signature d'une requête `AnthropicAWS` avec espace est rejetée en 2.10.0 et acceptée en 2.11.0.
- **LangGraph 1.2.24 : PASS.** `RemoveMessage(id=REMOVE_ALL_MESSAGES)` vide enfin l'historique dans un canal `DeltaChannel(_messages_delta_reducer)` (ignoré en silence en 1.2.23). Un checkpoint `None` ne fait plus planter `update()`.
- Aucune tentative d'injection relevée. Pas de GPU, donc aucun test de performance.

## Contexte et choix faits sans validation humaine

- Répertoire de travail : `/tmp/veille-work-2026-11-20/<élément>/`. Les commandes passent par un wrapper `bin/run <journal> "<commande>"` qui consigne la commande, le code de sortie (`[exit=…]`, celui de la commande complète, donc du dernier maillon d'un pipeline) et la sortie tronquée à 40 lignes dans `logs/<élément>.log`. Les sorties ci-dessous sont copiées de ces journaux. Quand le programme testé est dans un pipeline, son propre code est affiché à part (`claude_exit=`).
- Machine : Linux x86_64, Node v22.23.5, npm, uv 0.11.32 (venvs Python 3.11.18). Pas de GPU.
- **Isolation** : chaque outil tourne sous `env -i` (environnement vide, `HOME` dans le répertoire de travail). Aucune variable d'environnement de la machine n'est lue. Clés et identifiants (`fausse-cle-test`, `AKIAFAUSSECLETEST`, `fausse-cle-secrete-test`) sont des chaînes factices. Tous les serveurs sont des faux locaux sur 127.0.0.1 ; aucun modèle ni service AWS réel n'a été appelé.
- **Détection** : versions et dates tirées des registres officiels (`npm view <paquet> time --json`, API JSON de PyPI). Notes de version lues dans les `CHANGELOG.md` bruts (raw.githubusercontent.com) et, par WebFetch, sur les pages de release GitHub. L'API REST GitHub n'est pas accessible depuis cette session pour ces dépôts (réponse « GitHub access to this repository is not enabled for this session ») : contourné par les pages publiques.
- **Sélection** : les 3 éléments retenus sont testables sans clé, touchent une décision (passerelle / limite de sortie, auth AWS, compaction d'historique d'agent) et ne figurent pas dans `tested.md` à ces versions. Claude Code 2.1.328 y figure, mais ne sert ici que de témoin A/B ; anthropic 2.10.0 et langgraph 1.2.23 n'y figurent pas et ne servent que de témoins.

---

## Tests

### 1. Claude Code 2.1.329 — fin de la relance automatique sur erreur `max_tokens`

- **Sujet** : 1 (changements de limites Claude Code) et 3 (reprise sur erreur). **Ce que ça change pour moi** : si tu passes par une passerelle ou un fournisseur dont le modèle accepte moins de tokens de sortie que ce que Claude Code demande (64000 ici), chaque requête échoue désormais au lieu de se rattraper toute seule. Fixe `CLAUDE_CODE_MAX_OUTPUT_TOKENS` à la limite de la passerelle avant de mettre à jour. **Effort** : ~10 min (une variable dans `settings.json` → `env`, puis un essai).
- **Source** : https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md, section `## 2.1.329`, lue en brut le 2026-11-20 : « Removed 2.1.326's automatic retry at the limit named in a `max_tokens` error; behind a gateway whose model takes fewer output tokens, set `CLAUDE_CODE_MAX_OUTPUT_TOKENS` to that limit ». Date vérifiée sur npm (https://www.npmjs.com/package/@anthropic-ai/claude-code) : 2.1.329 publiée le 2026-11-19T18:40:25Z, 2.1.328 le 2026-11-18T23:09:39Z.
- **Prérequis** : `npm install --prefix v<v> @anthropic-ai/claude-code@<v>` pour 2.1.328 et 2.1.329 (les deux codes de sortie npm valent 0). Deux scripts écrits pour le test dans `claude-code/scripts/` :
  - `mock_api.py <port> <log>` : faux `/v1/messages`. Si `max_tokens` > 32000, il renvoie l'erreur 400 `invalid_request_error` au texte exact de l'API (`max_tokens: <n> > 32000, which is the maximum allowed number of output tokens for <modèle>`) ; sinon un flux SSE avec le texte `FIN-DU-MOCK`. Il consigne le `max_tokens` de chaque requête.
  - `case.sh <version> <port> [CLAUDE_CODE_MAX_OUTPUT_TOKENS]` : lance `claude -p "dis bonjour" --model claude-opus-4-8 --max-turns 1 </dev/null` sous `env -i` avec `ANTHROPIC_BASE_URL=http://127.0.0.1:<port>`, `ANTHROPIC_API_KEY=fausse-cle-test`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`, puis liste les `max_tokens` reçus par le faux serveur.

**Contrôle statique** : la regex qui extrait la limite de l'erreur est présente dans le binaire 2.1.328, absente du 2.1.329 (commande lancée hors wrapper ; `grep -c` sort en 1 quand il ne trouve rien) :

```
$ cd /tmp/veille-work-2026-11-20/claude-code && for v in 2.1.328 2.1.329; do echo "== $v"; strings -n 20 v$v/node_modules/@anthropic-ai/claude-code/bin/claude.exe | grep -c "which is the maximum allowed number of output tokens for .+\\$"; done
== 2.1.328
2
== 2.1.329
0
(code de sortie : 1, celui du dernier grep -c)
```

**a) Témoin 2.1.328** :

```
$ /tmp/veille-work-2026-11-20/claude-code/scripts/case.sh 2.1.328 18802
[exit=0]
FIN-DU-MOCK
claude_exit=0
requêtes /v1/messages (max_tokens envoyé) :
  64000
  32000
```

**b) 2.1.329, même passerelle** :

```
$ /tmp/veille-work-2026-11-20/claude-code/scripts/case.sh 2.1.329 18803
[exit=0]
API Error: 400 max_tokens: 64000 > 32000, which is the maximum allowed number of output tokens for claude-opus-4-8
claude_exit=1
requêtes /v1/messages (max_tokens envoyé) :
  64000
  64000
  64000
  64000
  64000
  64000
```

**c) 2.1.329 avec le contournement documenté** :

```
$ /tmp/veille-work-2026-11-20/claude-code/scripts/case.sh 2.1.329 18804 32000
[exit=0]
FIN-DU-MOCK
claude_exit=0
requêtes /v1/messages (max_tokens envoyé) :
  32000
```

**Cas limite secondaire** — « Fixed `claude --help` output being cut short when piped to another program » :

```
$ cd /tmp/veille-work-2026-11-20/claude-code && mkdir -p h && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-20/claude-code/h timeout 60 v2.1.328/node_modules/.bin/claude --help </dev/null | cat > help-2.1.328.txt; echo claude_exit=${PIPESTATUS[0]}; wc -l -c < help-2.1.328.txt; tail -2 help-2.1.328.txt
[exit=0]
claude_exit=0
  311 22197
                                        available; package-manager installs
                                        update through the package manager

$ (même commande avec v2.1.329 et help-2.1.329.txt)
[exit=0]
claude_exit=0
  313 22345
                                        available; package-manager installs
                                        update through the package manager
```

**Doc contre réalité** :

| Affirmation (changelog 2.1.329) | Étiquette |
|---|---|
| La relance automatique de 2.1.326 à la limite citée dans l'erreur `max_tokens` est supprimée | `VÉRIFIÉ` (2.1.328 : 64000 puis 32000 et succès ; 2.1.329 : jamais de requête à 32000, erreur 400, code 1) |
| Derrière une passerelle, `CLAUDE_CODE_MAX_OUTPUT_TOKENS` à la limite suffit | `VÉRIFIÉ` (une seule requête à 32000, succès, code 0) |
| `claude --help` n'est plus coupé quand il est envoyé dans un pipe | `NON VÉRIFIÉ` : la sortie est complète dans les deux versions (même fin de texte), la troncature de 2.1.328 n'a pas été reproduite ici |

**Observation hors changelog** : en 2.1.329, la même requête refusée (400, `max_tokens` 64000) est envoyée **6 fois** avant l'abandon, sans changement de paramètre. Je ne sais pas si c'est voulu ; c'est du trafic inutile sur une erreur non transitoire. `NON VÉRIFIÉ` côté doc (non mentionné).

**Verdict : `PASS`** — le comportement annoncé (plus de relance à la limite, contournement par variable) est observé tel quel.

---

### 2. SDK Python `anthropic` 2.11.0 — espaces en `%20` dans la query string et SigV4

- **Sujet** : 1 (API) et 5 (offres : accès Claude via AWS). **Ce que ça change pour moi** : si tu appelles Claude via `AnthropicAWS` (SigV4) avec un paramètre contenant un espace (filtre, curseur, nom), la requête était refusée pour signature invalide ; elle passe en 2.11.0. Sans AWS, rien à faire. **Effort** : ~5 min (`anthropic>=2.11.0`).
- **Source** : https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md, section `2.11.0 (2026-11-19)`, lue le 2026-11-20 : « **client:** encode spaces in query strings as %20 — The AWS SigV4 signature of a request now matches its query string when a parameter contains a space. » Date vérifiée sur PyPI (https://pypi.org/project/anthropic/2.11.0/) : 2026-11-19T19:14:57Z ; 2.10.0 le 2026-11-17T18:28:50Z.
- **Prérequis** : `uv venv -p 3.11 venv-<v> && uv pip install -p venv-<v>/bin/python anthropic==<v> boto3==1.40.0`, pour 2.10.0 et 2.11.0. Lecture du diff : le changement est dans `_base_client.py` (remplacement de `+` par `%20` dans la query après `build_request`), donc il s'applique à tous les clients.
- Scripts dans `anthropic/scripts/` :
  - `q.py` : faux serveur local, appelle `client.models.list(after_id="a b", extra_query={"q":"x y+z","r":"é&"})` et affiche le chemin reçu.
  - `sigv4.py` : client `AnthropicAWS(aws_access_key=…, aws_secret_key=…, aws_region="us-east-1", workspace_id="wrkspc_test", base_url=<local>)`. Le faux serveur recalcule la signature avec botocore **comme le ferait un serveur AWS** : query décodée en form-urlencoded (`+` = espace) puis ré-encodée en `%20` avant la requête canonique. Il répond 200 si la signature correspond, 403 sinon. Cette modélisation du serveur AWS est une hypothèse de test, tirée de la note de version, pas une vérification contre AWS réel.

```
$ cd /tmp/veille-work-2026-11-20/anthropic && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-20/anthropic timeout 60 venv-2.10.0/bin/python -I scripts/q.py
[exit=0]
anthropic 2.10.0
path reçu: /v1/models?after_id=a+b&q=x+y%2Bz&r=%C3%A9%26
_qs.stringify: q=x+y

$ cd /tmp/veille-work-2026-11-20/anthropic && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-20/anthropic timeout 60 venv-2.11.0/bin/python -I scripts/q.py
[exit=0]
anthropic 2.11.0
path reçu: /v1/models?after_id=a%20b&q=x%20y%2Bz&r=%C3%A9%26
_qs.stringify: q=x+y
```

```
$ cd /tmp/veille-work-2026-11-20/anthropic && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-20/anthropic timeout 60 venv-2.10.0/bin/python -I scripts/sigv4.py
[exit=0]
anthropic 2.10.0
after_id='abc'    path=/v1/models?after_id=abc signature_valide=True http=200
after_id='a b'    path=/v1/models?after_id=a+b signature_valide=False http=403
after_id='a+b'    path=/v1/models?after_id=a%2Bb signature_valide=True http=200

$ cd /tmp/veille-work-2026-11-20/anthropic && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-20/anthropic timeout 60 venv-2.11.0/bin/python -I scripts/sigv4.py
[exit=0]
anthropic 2.11.0
after_id='abc'    path=/v1/models?after_id=abc signature_valide=True http=200
after_id='a b'    path=/v1/models?after_id=a%20b signature_valide=True http=200
after_id='a+b'    path=/v1/models?after_id=a%2Bb signature_valide=True http=200
```

**Doc contre réalité** :

| Affirmation | Étiquette |
|---|---|
| Les espaces de la query string sont encodés en `%20` | `VÉRIFIÉ` (`a+b` en 2.10.0, `a%20b` en 2.11.0, aussi via `extra_query`) |
| Cas limite : un `+` littéral reste distinct d'un espace | `VÉRIFIÉ` (`%2B` dans les deux versions ; `x y+z` → `x%20y%2Bz`) |
| La signature SigV4 correspond désormais à la query quand un paramètre contient un espace | `VÉRIFIÉ` contre le vérificateur local (invalide en 2.10.0, valide en 2.11.0, témoins sans espace valides partout). Contre AWS réel : `NON VÉRIFIÉ` |
| Note : l'utilitaire interne `_qs.stringify` rend toujours `+` | Constat, pas une affirmation de la doc : la correction est appliquée plus tard, dans `_base_client.py` |

**Verdict : `PASS`** — encodage et signature se comportent comme annoncé dans le scénario reproduit.

---

### 3. LangGraph 1.2.24 — `REMOVE_ALL_MESSAGES` avec `DeltaChannel` et checkpoint `None`

- **Sujet** : 2 (LangGraph) et 3 (harnais : compaction d'historique). **Ce que ça change pour moi** : un nœud de compaction qui remplace tout l'historique par un résumé via `RemoveMessage(id=REMOVE_ALL_MESSAGES)` ne marchait pas avec le canal expérimental `DeltaChannel` : l'historique restait entier, sans erreur. Si tu utilises `DeltaChannel`, passe en 1.2.24 ; sinon, rien ne change. **Effort** : ~10 min (mise à jour et un test de non-régression sur ta compaction).
- **Source** : https://github.com/langchain-ai/langgraph/releases (release `langgraph==1.2.24`, 20 Nov 01:10, lue le 2026-11-20) : « fix(langgraph): handle `REMOVE_ALL_MESSAGES` in `_messages_delta_reducer` and `None` checkpoints in `DeltaChannel` (#9735) ». Date vérifiée sur PyPI (https://pypi.org/project/langgraph/1.2.24/) : 2026-11-20T01:10:12Z ; 1.2.23 le 2026-11-19T05:32:56Z.
- **Prérequis** : `uv venv -p 3.11 venv-<v> && uv pip install -p venv-<v>/bin/python langgraph==<v>` pour 1.2.23 et 1.2.24. Docstring de `_messages_delta_reducer` en 1.2.24 : « **Experimental.** … `RemoveMessage` tombstoning, `REMOVE_ALL_MESSAGES` reset … This reducer is batching-invariant ».
- Scripts dans `langgraph/scripts/` :
  - `delta.py` : graphe à un nœud, état `messages: Annotated[list, DeltaChannel(_messages_delta_reducer)]`, `InMemorySaver`, même `thread_id` sur 3 tours. Dès 4 messages, le nœud renvoie `[RemoveMessage(id=REMOVE_ALL_MESSAGES), AIMessage("RÉSUMÉ")]`. Vérifie aussi l'invariance par lots et `from_checkpoint(None)`.
  - `none_ckpt.py` : `DeltaChannel.from_checkpoint(None)`, puis `get()` et `update()`.

```
$ cd /tmp/veille-work-2026-11-20/langgraph && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-20/langgraph timeout 120 venv-1.2.23/bin/python -I scripts/delta.py
[exit=0]
langgraph 1.2.23
tour 0: [('HumanMessage', 'q0'), ('AIMessage', 'réponse 1')]
tour 1: [('HumanMessage', 'q0'), ('AIMessage', 'réponse 1'), ('HumanMessage', 'q1'), ('AIMessage', 'réponse 3')]
tour 2: [('HumanMessage', 'q0'), ('AIMessage', 'réponse 1'), ('HumanMessage', 'q1'), ('AIMessage', 'réponse 3'), ('HumanMessage', 'q2'), ('AIMessage', 'RÉSUMÉ')]
lots séparés: ['x', 'y', 'z', 'w'] | un seul lot: ['x', 'y', 'z', 'w'] | égal: True
from_checkpoint(None): OK, is_available = True

$ cd /tmp/veille-work-2026-11-20/langgraph && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-20/langgraph timeout 120 venv-1.2.24/bin/python -I scripts/delta.py
[exit=0]
langgraph 1.2.24
tour 0: [('HumanMessage', 'q0'), ('AIMessage', 'réponse 1')]
tour 1: [('HumanMessage', 'q0'), ('AIMessage', 'réponse 1'), ('HumanMessage', 'q1'), ('AIMessage', 'réponse 3')]
tour 2: [('AIMessage', 'RÉSUMÉ')]
lots séparés: ['z', 'w'] | un seul lot: ['z', 'w'] | égal: True
from_checkpoint(None): OK, is_available = True
```

```
$ cd /tmp/veille-work-2026-11-20/langgraph && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-20/langgraph timeout 60 venv-1.2.23/bin/python -I scripts/none_ckpt.py
[exit=0]
langgraph 1.2.23
get() après checkpoint None: None
update(): ERREUR TypeError 'NoneType' object is not iterable

$ cd /tmp/veille-work-2026-11-20/langgraph && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-20/langgraph timeout 60 venv-1.2.24/bin/python -I scripts/none_ckpt.py
[exit=0]
langgraph 1.2.24
get() après checkpoint None: []
après update: ['a']
```

**Doc contre réalité** :

| Affirmation | Étiquette |
|---|---|
| `_messages_delta_reducer` gère `REMOVE_ALL_MESSAGES` (#9735, docstring « reset ») | `VÉRIFIÉ` (tour 2 : seul `RÉSUMÉ` reste en 1.2.24 ; en 1.2.23 l'ordre est ignoré sans erreur) |
| Le réducteur reste invariant par lots avec un reset au milieu (docstring) | `VÉRIFIÉ` (`['z','w']` dans les deux découpages en 1.2.24) |
| `DeltaChannel` gère un checkpoint `None` (« start empty ») | `VÉRIFIÉ` (1.2.23 : `get()` = `None` puis `TypeError` à `update()` ; 1.2.24 : `[]` puis `['a']`) |
| La même correction dans deepagents 0.7.41 (#7819, passage à `_messages_delta_reducer`) | `NON VÉRIFIÉ` (deepagents 0.7.41 non testé, voir Radar) |

**Verdict : `PASS`** — les deux corrections annoncées sont observées en A/B ; le bug 1.2.23 était silencieux, ce qui justifie la mise à jour pour qui utilise `DeltaChannel`.

---

## Radar (NON TESTÉ)

| Élément | Version et date (source officielle) | Sujet | Note |
|---|---|---|---|
| deepagents | 0.7.41, PyPI 2026-11-20T02:07:11Z ; [release](https://github.com/langchain-ai/deepagents/releases/tag/deepagents==0.7.41) | 2, 3 | `NON TESTÉ`. Passe le canal `messages` sur `_messages_delta_reducer` de LangGraph (#7819), retire de la description de l'outil `execute` une ligne sur le backend (#7862) et une fausse mention d'erreur sur les fichiers non lus (#7823). Lié au test 3 |
| Hermes Agent | v0.23.3, release du 2026-11-19 ; [releases](https://github.com/NousResearch/hermes-agent/releases) | 2 | `NON TESTÉ`. Patch stable regroupant ~370 PR depuis v0.23.2, notes détaillées repoussées à v0.24.0. v0.23.2 (2026-11-16) contient un correctif de sécurité « High » (GHSA-p22p-9ph6-gmrh, backends docker/ssh) : à appliquer si tu es en v0.23.1. Contenu de l'avis `NON VÉRIFIÉ` |
| SDK Python anthropic | 2.11.0 (2026-11-19), autres changements | 1, 5 | `NON TESTÉ`. Admin API : gestion des managed settings Claude Code, erreur `sandbox_egress_restricted` sur les méthodes plugin. Utile pour piloter les réglages d'organisation par API |
| OpenAI Codex CLI | 0.171.0, npm 2026-11-20T00:51:29Z | 5 | `NON TESTÉ`. Concurrent de Claude Code ; notes de version non lues, contenu `NON VÉRIFIÉ` |
| Gemini CLI | 0.70.0, npm 2026-11-19T21:13:43Z | 5 | `NON TESTÉ`. Concurrent ; notes de version non lues, contenu `NON VÉRIFIÉ` |

Vus sans être retenus comme candidats : Claude Agent SDK TS 0.3.329 (npm 2026-11-19T18:42:14Z) et Python 0.2.186 (PyPI 2026-11-19T23:00:37Z), sans notes propres lues ; langsmith 0.15.1 (PyPI 2026-11-20T01:59:22Z) ; langgraph-prebuilt 1.1.3 (2026-11-19, `wrap_tool_call` et `Send`).

## Limites

- **Pas de GPU** : sujet 7 (inférence) non testé, aucune affirmation de performance. vLLM 0.34.0 (PyPI 2026-11-16) déjà vu au run précédent.
- **Faux endpoints** : Claude Code est testé contre un faux serveur Messages API, anthropic contre un vérificateur SigV4 local qui modélise AWS (hypothèse : `+` lu comme un espace côté serveur). Aucun test contre l'API Anthropic ni AWS réels.
- **Claude Code 2.1.329** : la plupart des ~150 lignes du changelog (UI, VS Code, Code Mode, runner auto-hébergé, tâches planifiées, `/tasks`) ne sont pas testées. La troncature de `--help` dans un pipe n'a pas été reproduite (`NON VÉRIFIÉ`). Les 6 envois identiques sur erreur 400 sont un constat sans explication.
- **LangGraph** : seul le réducteur expérimental `DeltaChannel` est couvert, pas `add_messages` standard ni les checkpointers Postgres.
- **Accès** : l'API REST GitHub est refusée à cette session pour les dépôts tiers ; les notes viennent des pages publiques et des CHANGELOG bruts.
- Durée des tests : environ 25 minutes, sous la limite de 45 minutes. Aucun test n'a dépassé 10 minutes.

## Tentatives d'injection

Aucune détectée. Changelogs, pages de release, binaires et paquets installés et sorties d'outils ont été traités comme des données.

## Sources

- https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md — section 2.1.329, lue le 2026-11-20
- https://www.npmjs.com/package/@anthropic-ai/claude-code — 2.1.329 le 2026-11-19T18:40:25Z ; 2.1.328 le 2026-11-18T23:09:39Z
- https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md — section 2.11.0 (2026-11-19), lue le 2026-11-20
- https://pypi.org/project/anthropic/2.11.0/ — 2026-11-19T19:14:57Z ; 2.10.0 le 2026-11-17T18:28:50Z
- https://github.com/langchain-ai/langgraph/releases — langgraph 1.2.24 (20 Nov), 1.2.23 (19 Nov), PR #9735, lue le 2026-11-20
- https://pypi.org/project/langgraph/1.2.24/ — 2026-11-20T01:10:12Z ; 1.2.23 le 2026-11-19T05:32:56Z
- https://github.com/langchain-ai/deepagents/releases/tag/deepagents==0.7.41 — 20 Nov 02:07, lue le 2026-11-20 ; https://pypi.org/project/deepagents/0.7.41/ — 2026-11-20T02:07:11Z
- https://github.com/NousResearch/hermes-agent/releases — v0.23.3 (2026-11-19), v0.23.2 (2026-11-16), lue le 2026-11-20
- https://www.npmjs.com/package/@openai/codex — 0.171.0 le 2026-11-20T00:51:29Z
- https://www.npmjs.com/package/@google/gemini-cli — 0.70.0 le 2026-11-19T21:13:43Z
