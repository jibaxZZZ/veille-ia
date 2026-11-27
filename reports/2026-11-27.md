# Veille IA — 2026-11-27

## TL;DR

- **Run du 2026-11-27** (fenêtre du 2026-11-20 au 2026-11-27) : **8 éléments détectés, 3 testés (3 PASS), 5 au Radar.** Les tests sont des A/B contre la version précédente, avec des modèles factices et des serveurs en mémoire. Aucune vraie API n'a été appelée.
- **deepagents 0.7.42 : PASS.** Un surrogate isolé écrit par `write_file` faisait planter le run au `ls` suivant en 0.7.41 (`UnicodeEncodeError`). En 0.7.42, il devient U+FFFD et la paire coupée est recollée. Un `interrupt()` levé dans `glob` met maintenant le run en pause (sync et async) au lieu de revenir au modèle comme « glob failed ».
- **langchain-core 1.8.5 : PASS.** Quand le fournisseur ne donne son id de message qu'au 1ᵉʳ chunk, tous les chunks gardent cet id en `stream`, `astream`, `astream_events` v2 et en LangGraph `stream_mode="messages"`. En 1.8.4, il y avait deux ids, donc un message affiché en double.
- **FastMCP 4.2.7a1 (préversion) : PASS.** Une entrée de skill invalide côté backend vidait toute la liste vue à travers le proxy en 4.2.6. En 4.2.7a1, seule l'entrée invalide saute, et l'avertissement ne cite plus son contenu. Un `%2F` dans le préfixe d'URI est accepté, et reste refusé dans un nom de fichier.
- Aucune tentative d'injection relevée. Pas de GPU, donc aucun test de performance.

## Contexte et choix faits sans validation humaine

- Répertoire de travail : `/tmp/veille-work-2026-11-27/<élément>/` (`da`, `lcc`, `fmcp`). Les commandes passent par le wrapper `bin/run <journal> "<commande>"`. Il consigne la commande, le code de sortie `[exit=…]` et la sortie tronquée à 40 lignes. Avec un pipe, `[exit=…]` est le code du dernier maillon. Le code du programme Python est donc affiché à part (`py_exit=${PIPESTATUS[0]}`). Les lignes sont coupées à 300 à 400 caractères (`cut`).
- Machine : Linux x86_64, uv, Python 3.11, sans GPU. Chaque version a son propre venv : `uv venv -p 3.11 v<version>`, puis `uv pip install <paquet>==<version>`.
- **Isolation** : tous les scripts tournent avec `python -I` sous `env -i HOME=<répertoire de travail> PATH=/usr/bin:/bin`. Aucune variable d'environnement de la machine n'est lue et aucune clé n'est utilisée.
- **Détection** : versions et dates viennent des registres officiels (API JSON de PyPI, `npm view <paquet> time --json`). Les notes viennent des pages de releases GitHub et des PR liées (lues avec un outil de lecture web), recoupées avec le diff des paquets installés.
- **Sélection** : Claude Code (2.1.332), les Agent SDK TS (0.3.332) et Python (0.2.189), anthropic (2.14.0) et langchain-anthropic (1.7.13) n'ont pas de version plus récente que celles déjà testées. J'ai retenu :
  - deepagents 0.7.42 (sujets 2 et 3 : interruption humaine dans un outil, robustesse) ;
  - langchain-core 1.8.5 (sujet 2 : flux de messages de LangGraph) ;
  - FastMCP 4.2.7a1 (sujets 3 et 4 : skills servies par un proxy MCP).

  FastMCP 4.2.7a1 est une **préversion**, retenue parce que c'est la seule nouveauté de la semaine sur les skills MCP. Le verdict ne vaut que pour cette alpha. Aucun de ces éléments ne figure dans `tested.md` à ces versions.
- **Scripts** : copie exacte dans [`reports/scripts-2026-11-27/`](scripts-2026-11-27/). Pour refaire un test, copie `run` dans `/tmp/veille-work-2026-11-27/bin/`, chaque script dans `/tmp/veille-work-2026-11-27/<élément>/scripts/` et `fmcp/skills/` dans `/tmp/veille-work-2026-11-27/fmcp/skills/`. Crée ensuite les venvs avec les commandes de la section « Installation ».

### Installation (les trois éléments)

```
$ cd /tmp/veille-work-2026-11-27/da && uv venv -q -p 3.11 v0.7.41 && uv venv -q -p 3.11 v0.7.42 && VIRTUAL_ENV=v0.7.41 uv pip install -q deepagents==0.7.41 && VIRTUAL_ENV=v0.7.42 uv pip install -q deepagents==0.7.42; echo da=$?
da=0
$ cd /tmp/veille-work-2026-11-27/lcc && uv venv -q -p 3.11 v1.8.4 && uv venv -q -p 3.11 v1.8.5 && VIRTUAL_ENV=v1.8.4 uv pip install -q langchain-core==1.8.4 && VIRTUAL_ENV=v1.8.5 uv pip install -q langchain-core==1.8.5; echo lcc=$?
lcc=0
$ cd /tmp/veille-work-2026-11-27/lcc && for v in 1.8.4 1.8.5; do VIRTUAL_ENV=v$v uv pip install -q langgraph==1.2.24 langchain-core==$v; done; v1.8.4/bin/python -c 'import importlib.metadata as m;print(m.version("langchain-core"),m.version("langgraph"))'; v1.8.5/bin/python -c '…même chose…'
1.8.4 1.2.24
1.8.5 1.2.24
$ cd /tmp/veille-work-2026-11-27/fmcp && VIRTUAL_ENV=v4.2.6 uv pip install -q fastmcp==4.2.6 && VIRTUAL_ENV=v4.2.7a1 uv pip install -q fastmcp==4.2.7a1; echo fm=$?
  × No solution found when resolving dependencies:
  ╰─▶ Because there is no version of fastmcp-slim[client]==4.2.7a1 and
      fastmcp>=4.2.7a1 depends on fastmcp-slim[client]==4.2.7a1, we can
      conclude that fastmcp>=4.2.7a1 cannot be used.
hint: `fastmcp-slim` was requested with a pre-release marker (e.g., fastmcp-slim==4.2.7a1), but pre-releases weren't enabled (try: `--prerelease=allow`)
fm=1
$ cd /tmp/veille-work-2026-11-27/fmcp && VIRTUAL_ENV=v4.2.7a1 uv pip install -q --prerelease=allow fastmcp==4.2.7a1; echo fm=$?
fm=0
```
(4.2.6 s'était installée dans la première commande ; l'échec ne concernait que l'alpha. Avec uv, il faut `--prerelease=allow` même quand la version est épinglée.)

---

## Tests

### 1. deepagents 0.7.42 — surrogates isolés dans les fichiers, `glob` qui laisse passer les interruptions

- **Sujet** : 2 (LangGraph et harnais) et 3 (permissions, reprise sur erreur). **Ce que ça change pour moi** : on peut maintenant brancher une approbation humaine (`interrupt()`) dans le `glob` d'un backend sur mesure, et le texte venu de code JS mal découpé ne tue plus le run. Les autres outils (`ls`, `grep`, `read_file`…) n'ont pas reçu ce correctif : la PR a été restreinte à `glob`, donc n'y mets pas encore d'approbation. **Effort** : ~15 min pour passer en `>=0.7.42`, ~1 h pour une approbation sur `glob`.
- **Source** : https://github.com/langchain-ai/deepagents/releases (release `deepagents==0.7.42` du 26 nov. 2026), PR [#7972](https://github.com/langchain-ai/deepagents/pull/7972) et [#7820](https://github.com/langchain-ai/deepagents/pull/7820), fusionnées le 25 nov. 2026. Date vérifiée sur PyPI : 0.7.42 publiée le 2026-11-26T06:07:18Z (0.7.41 : 2026-11-20T02:07:11Z).
- **Diff des paquets installés** (`diff -ru v0.7.41/… v0.7.42/…`) : nouvelle fonction `_encodable_text` dans `backends/utils.py`, appelée par `create_file_data` et `update_file_data`. `except GraphBubbleUp: raise` est ajouté avant le `except Exception` des deux chemins (sync et async) de `glob` dans `middleware/filesystem.py`. Le reste n'est que de la doc et une réorganisation de la divulgation d'outils des skills.
- **Scénario** : `da_test.py <scénario>` crée un agent `create_deep_agent` avec un modèle factice (`GenericFakeChatModel`) qui enchaîne des appels d'outils écrits d'avance, et un `InMemorySaver`.
  - `surrogates` : écrit `/seul.txt` (`"avant \ud83d apres"`, un surrogate isolé) et `/paire.txt` (`"rire 😀 fin"`, U+1F600 en deux points de code), puis appelle `ls /`, `glob *.txt` et `read_file`.
  - `interrupt`, `interrupt-non` et `interrupt-async` : le backend `Gardé(StateBackend)` appelle `interrupt({"question": …})` dans `glob`, puis lève `PermissionError` si la réponse n'est pas `oui`. Le script reprend avec `Command(resume=…)`.

**a) Quickstart et cas limite : surrogates**

```
$ cd /tmp/veille-work-2026-11-27/da && env -i HOME=/tmp/veille-work-2026-11-27/da PATH=/usr/bin:/bin v0.7.41/bin/python -I scripts/da_test.py surrogates 2>&1 | grep -v Warning | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
deepagents 0.7.41
  RUN INTERROMPU: UnicodeEncodeError 'utf-8' codec can't encode character '\ud83d' in position 6: surrogates not allowed
  tool_result[write_file]: 'Updated file /seul.txt'
  tool_result[write_file]: 'Updated file /paire.txt'
py_exit=0

$ cd /tmp/veille-work-2026-11-27/da && env -i HOME=/tmp/veille-work-2026-11-27/da PATH=/usr/bin:/bin v0.7.42/bin/python -I scripts/da_test.py surrogates 2>&1 | grep -v Warning | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
deepagents 0.7.42
  tool_result[write_file]: 'Updated file /seul.txt'
  tool_result[write_file]: 'Updated file /paire.txt'
  tool_result[ls]: "['/paire.txt', '/seul.txt']"
  tool_result[glob]: "['/paire.txt', '/seul.txt']"
  tool_result[read_file]: '@@ lines 1-1 of 1 @@\nrire \U0001f600 fin'
  dernier message: FIN
  stocké /seul.txt: 'avant � apres'
  stocké /paire.txt: 'rire \U0001f600 fin'
py_exit=0
```
(`py_exit=0` en 0.7.41 parce que le script intercepte l'exception pour l'afficher. Le run de l'agent, lui, s'arrête au `ls`.)

**b) Interruption dans `glob` : sync, refus, async**

```
$ cd /tmp/veille-work-2026-11-27/da && env -i HOME=/tmp/veille-work-2026-11-27/da PATH=/usr/bin:/bin v0.7.41/bin/python -I scripts/da_test.py interrupt 2>&1 | grep -v Warning | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
deepagents 0.7.41
  interruption en attente: aucune | next = ()
  tool_result[write_file]: 'Updated file /finance/board.md'
  tool_result[glob]: "Error: glob failed: (Interrupt(value={'question': 'autoriser glob **/*.md sur /finance ?'}, id='a8a7e37137395742e2b59540d0ceecec', response_schema=None),)"
  dernier message: FIN
py_exit=0

$ cd /tmp/veille-work-2026-11-27/da && env -i HOME=/tmp/veille-work-2026-11-27/da PATH=/usr/bin:/bin v0.7.42/bin/python -I scripts/da_test.py interrupt 2>&1 | grep -v Warning | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
deepagents 0.7.42
  interruption en attente: [{'question': 'autoriser glob **/*.md sur /finance ?'}] | next = ('tools',)
  tool_result[write_file]: 'Updated file /finance/board.md'
  dernier message: 
  après reprise resume='oui':
  tool_result[write_file]: 'Updated file /finance/board.md'
  tool_result[glob]: "['/finance/board.md']"
  dernier message: FIN
py_exit=0

$ cd /tmp/veille-work-2026-11-27/da && env -i HOME=/tmp/veille-work-2026-11-27/da PATH=/usr/bin:/bin v0.7.42/bin/python -I scripts/da_test.py interrupt-non 2>&1 | grep -v Warning | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
deepagents 0.7.42
  interruption en attente: [{'question': 'autoriser glob **/*.md sur /finance ?'}] | next = ('tools',)
  tool_result[write_file]: 'Updated file /finance/board.md'
  dernier message: 
  après reprise resume='non':
  tool_result[write_file]: 'Updated file /finance/board.md'
  tool_result[glob]: "Error: glob failed: refus\xe9 par l'humain"
  dernier message: FIN
py_exit=0

$ cd /tmp/veille-work-2026-11-27/da && env -i HOME=/tmp/veille-work-2026-11-27/da PATH=/usr/bin:/bin v0.7.41/bin/python -I scripts/da_test.py interrupt-async 2>&1 | grep -v Warning | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
deepagents 0.7.41
  interruption en attente: aucune | next = ()
  tool_result[write_file]: 'Updated file /finance/board.md'
  tool_result[glob]: "Error: glob failed: (Interrupt(value={'question': 'autoriser glob **/*.md sur /finance ?'}, id='fb03253e4e171f1a4dfe2dac01fc2633', response_schema=None),)"
  dernier message: FIN
py_exit=0

$ cd /tmp/veille-work-2026-11-27/da && env -i HOME=/tmp/veille-work-2026-11-27/da PATH=/usr/bin:/bin v0.7.42/bin/python -I scripts/da_test.py interrupt-async 2>&1 | grep -v Warning | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
deepagents 0.7.42
  interruption en attente: [{'question': 'autoriser glob **/*.md sur /finance ?'}] | next = ('tools',)
  tool_result[write_file]: 'Updated file /finance/board.md'
  dernier message: 
  après reprise resume='oui':
  tool_result[write_file]: 'Updated file /finance/board.md'
  tool_result[glob]: "['/finance/board.md']"
  dernier message: FIN
py_exit=0
```
En 0.7.41, `interrupt-non` ne fait pas de pause non plus :

```
$ cd /tmp/veille-work-2026-11-27/da && env -i HOME=/tmp/veille-work-2026-11-27/da PATH=/usr/bin:/bin v0.7.41/bin/python -I scripts/da_test.py interrupt-non 2>&1 | grep -v Warning | cut -c1-300; echo py_exit=${PIPESTATUS[0]}
[exit=0]
deepagents 0.7.41
  interruption en attente: aucune | next = ()
  tool_result[write_file]: 'Updated file /finance/board.md'
  tool_result[glob]: "Error: glob failed: (Interrupt(value={'question': 'autoriser glob **/*.md sur /finance ?'}, id='dd7789c771694f5163a6f9953fdbe20e', response_schema=None),)"
  dernier message: FIN
py_exit=0
```

- `VÉRIFIÉ` : « the next `ls` or `glob` … raised `UnicodeEncodeError` and ended the run » (comportement d'avant). Reproduit en 0.7.41 : le run s'arrête après les deux `write_file`.
- `VÉRIFIÉ` : « A lone surrogate is replaced with U+FFFD » (`'avant � apres'`) et « Two halves of a surrogate pair … are rejoined » (`\U0001f600`). `ls`, `glob` et `read_file` passent en 0.7.42.
- `VÉRIFIÉ` : `glob` « re-raises `GraphBubbleUp` » : l'interruption met le run en pause (`next = ('tools',)`), sync comme async. La reprise `oui` renvoie le résultat.
- `VÉRIFIÉ` : « Real search failures still return to the model as tool errors ». Après `non`, `PermissionError` revient au modèle sous la forme `Error: glob failed: …`.
- `NON VÉRIFIÉ` : la propagation de `ParentCommand` (sous-graphe vers graphe parent), non testée. Le `StoreBackend` et le backend context hub, cités par la PR, ne sont pas testés non plus (seul le `StateBackend` l'est).

**Verdict : PASS.** Les deux correctifs annoncés se reproduisent en A/B, sur les chemins sync et async.

### 2. langchain-core 1.8.5 — même id fournisseur sur tous les chunks streamés

- **Sujet** : 2 (LangGraph) et 3 (observabilité). **Ce que ça change pour moi** : une UI ou un journal qui regroupe les chunks par id (LangGraph `messages`, `useStream`, Agent Server) n'affiche plus deux fois le même message quand le fournisseur ne met son id que sur le 1ᵉʳ chunk, comme l'API Responses d'OpenAI. Avec Anthropic, ce cas n'a pas été testé. **Effort** : ~10 min (passer en `langchain-core>=1.8.5`).
- **Source** : https://github.com/langchain-ai/langchain/releases/tag/langchain-core%3D%3D1.8.5 (25 nov. 2026), PR [#42050](https://github.com/langchain-ai/langchain/pull/42050), fusionnée le 23 nov. 2026. Date vérifiée sur PyPI : 1.8.5 publiée le 2026-11-25T21:52:24Z (1.8.4 : 2026-11-19T22:35:41Z).
- **Scénario** : `lcc_test.py` définit un `BaseChatModel` factice dont `_stream` et `_astream` renvoient 3 chunks. Seul le premier porte `id="resp_abc"`. Le script affiche l'id de chaque chunk et du message final dans 6 cas : a) `stream`, b) `astream`, c) `invoke` avec un callback ordinaire, d) aucun id fournisseur, e) `astream_events` v2, f) graphe LangGraph 1.2.24 dont le nœud appelle `model.invoke()`, lu avec `stream_mode="messages"`.

```
$ cd /tmp/veille-work-2026-11-27/lcc && env -i HOME=/tmp/veille-work-2026-11-27/lcc PATH=/usr/bin:/bin v1.8.4/bin/python -I scripts/lcc_test.py 2>&1 | cut -c1-400; echo py_exit=${PIPESTATUS[0]}
[exit=0]
langchain-core 1.8.4
a) stream: ids des chunks=['resp_abc', 'lc_run--01a21ac6-b5fe-775f-b1c2-a50108fa38f8', 'lc_run--01a21ac6-b5fe-775f-b1c2-a50108fa38f8', 'lc_run--01a21ac6-b5fe-775f-b1c2-a50108fa38f8'] positions=[None, None, None, 'last'] | id final=resp_abc | ids distincts=['lc_run--01a21ac6-b5fe-775f-b1c2-a50108fa38f8', 'resp_abc']
b) astream: ids des chunks=['resp_abc', 'lc_run--01a21ac6-b600-71e3-a8fc-97b791c47f6e', 'lc_run--01a21ac6-b600-71e3-a8fc-97b791c47f6e', 'lc_run--01a21ac6-b600-71e3-a8fc-97b791c47f6e'] positions=[None, None, None, 'last'] | id final=resp_abc | ids distincts=['lc_run--01a21ac6-b600-71e3-a8fc-97b791c47f6e', 'resp_abc']
c) invoke + callback de streaming: ids vus par le callback=[] | id du message renvoyé=resp_abc
d) aucun id fournisseur: ids des chunks=['lc_run--01a21ac6-b601-77ee-84a4-81f228ac915b', 'lc_run--01a21ac6-b601-77ee-84a4-81f228ac915b', 'lc_run--01a21ac6-b601-77ee-84a4-81f228ac915b', 'lc_run--01a21ac6-b601-77ee-84a4-81f228ac915b'] positions=[None, None, None, 'last'] | id final=lc_run--01a21ac6-b601-77ee-84a4-81f228ac915b | ids distincts=['lc_run--01a21ac6-b601-77ee-84a4-81f228ac915b']
e) astream_events v2, ids des chunks: ['resp_abc', 'lc_run--01a21ac6-b602-7614-a3ec-51da1ce7446b', 'lc_run--01a21ac6-b602-7614-a3ec-51da1ce7446b', 'lc_run--01a21ac6-b602-7614-a3ec-51da1ce7446b']
f) LangGraph messages: ids streamés=['resp_abc', 'lc_run--01a21ac6-e873-7647-ac51-f8eb8da892bb', 'lc_run--01a21ac6-e873-7647-ac51-f8eb8da892bb', 'lc_run--01a21ac6-e873-7647-ac51-f8eb8da892bb'] | id du message dans l'état=resp_abc | ids distincts=['lc_run--01a21ac6-e873-7647-ac51-f8eb8da892bb', 'resp_abc']
py_exit=0

$ cd /tmp/veille-work-2026-11-27/lcc && env -i HOME=/tmp/veille-work-2026-11-27/lcc PATH=/usr/bin:/bin v1.8.5/bin/python -I scripts/lcc_test.py 2>&1 | cut -c1-400; echo py_exit=${PIPESTATUS[0]}
[exit=0]
langchain-core 1.8.5
a) stream: ids des chunks=['resp_abc', 'resp_abc', 'resp_abc', 'resp_abc'] positions=[None, None, None, 'last'] | id final=resp_abc | ids distincts=['resp_abc']
b) astream: ids des chunks=['resp_abc', 'resp_abc', 'resp_abc', 'resp_abc'] positions=[None, None, None, 'last'] | id final=resp_abc | ids distincts=['resp_abc']
c) invoke + callback de streaming: ids vus par le callback=[] | id du message renvoyé=resp_abc
d) aucun id fournisseur: ids des chunks=['lc_run--01a21ac6-bb37-7671-a7e4-ad4d8ee795aa', 'lc_run--01a21ac6-bb37-7671-a7e4-ad4d8ee795aa', 'lc_run--01a21ac6-bb37-7671-a7e4-ad4d8ee795aa', 'lc_run--01a21ac6-bb37-7671-a7e4-ad4d8ee795aa'] positions=[None, None, None, 'last'] | id final=lc_run--01a21ac6-bb37-7671-a7e4-ad4d8ee795aa | ids distincts=['lc_run--01a21ac6-bb37-7671-a7e4-ad4d8ee795aa']
e) astream_events v2, ids des chunks: ['resp_abc', 'resp_abc', 'resp_abc', 'resp_abc']
f) LangGraph messages: ids streamés=['resp_abc', 'resp_abc', 'resp_abc', 'resp_abc'] | id du message dans l'état=resp_abc | ids distincts=['resp_abc']
py_exit=0
```
(Première exécution : `SyntaxError` dans mon script, à la ligne 44 (compréhension async hors fonction), sur les deux versions avec `py_exit=1`. J'ai supprimé la ligne, puis ajouté le cas f) et relancé. Les sorties ci-dessus sont celles de ce dernier passage.)

- `VÉRIFIÉ` : « later chunks got a fallback `lc_run--*` id, but the final merged message kept `resp_*` » (comportement d'avant). Reproduit en 1.8.4 : deux ids distincts en a), b), e) et f).
- `VÉRIFIÉ` : « The v1 stream paths (`stream`, `astream`, and the invoke-with-streaming-callback paths) reuse the first provider id ». En 1.8.5, un seul id en a), b) et e), et en f), qui est le chemin `invoke` sous le callback de streaming de LangGraph.
- `VÉRIFIÉ` : « The synthetic `chunk_position="last"` chunk uses that same provider id » (4ᵉ chunk, `last`, `resp_abc`).
- `VÉRIFIÉ` (cas limite) : sans id fournisseur, le comportement ne change pas : un seul `lc_run--*` partout (d).
- `NON VÉRIFIÉ` : c) un callback ordinaire ne déclenche pas le streaming sous `invoke` (0 token vu, sur les deux versions), donc ce cas ne prouve rien. Le « v2 protocol path is unchanged » n'est pas testé non plus, ni le comportement avec les vrais `ChatOpenAI` et `ChatAnthropic` (aucun appel réseau).

**Verdict : PASS.** Le doublon d'id est reproduit en 1.8.4 et disparu en 1.8.5 sur les quatre chemins testés, LangGraph compris.

### 3. FastMCP 4.2.7a1 (préversion) — skills servies par un proxy : entrées invalides, `%2F` dans les URI

- **Sujet** : 3 (garde-fous) et 4 (MCP et connecteurs). **Ce que ça change pour moi** : un proxy FastMCP qui agrège les skills d'un backend tiers ne perd plus toute la liste à cause d'une seule entrée mal formée, et ses journaux ne recopient plus le contenu du backend. C'est une alpha : à tester, pas à déployer. **Effort** : ~30 min pour essayer, à reprendre à la version stable.
- **Source** : https://github.com/PrefectHQ/fastmcp/releases (v4.2.7a1 « Slashdance », préversion du 26 nov. 2026 ; PR #6828, #6827, #6830). Date vérifiée sur PyPI : 4.2.7a1 publiée le 2026-11-26T03:30:30Z (4.2.6 : 2026-11-25T02:55:05Z).
- **Diff des paquets installés** : seuls `skills/_proxy.py` et `skills/models.py` changent. Dans `_proxy.py`, chaque entrée de `skills/list` est validée à part, et le proxy ne demande plus rien à un backend si le protocole n'est pas dans `MODERN_PROTOCOL_VERSIONS` (`("2026-07-28",)`). Dans `models.py`, un segment décodé contenant `/` n'est plus refusé dans le préfixe, mais il l'est toujours dans le chemin du fichier.
- **Scénario** : `fm_test.py skills`, tout en mémoire.
  - Backend : `FastMCP("backend")` avec `fastmcp.skills.provider.SkillsDirectoryProvider` sur `skills/review/SKILL.md`.
  - Proxy : `FastMCP("proxy")` avec `ProxyProvider(lambda: Client(backend), skills=True)`.
  - Client : `Client(proxy, extensions=[SkillsClientExtension()])`, qui appelle `list_skills()`.
  - Cas b) : le script remplace `SkillsExtension._handle_list` avant de créer les serveurs. Côté backend seulement, la réponse reçoit en plus une entrée invalide (`name: "Bad"`, majuscule interdite), construite avec `model_construct`.
  - Cas c) : `MCPSkill.model_validate` sur trois URI.
  - `COLUMNS=400` sert à garder les journaux de rich sur une ligne, et `sed` compacte les espaces.

```
$ cd /tmp/veille-work-2026-11-27/fmcp && env -i HOME=/tmp/veille-work-2026-11-27/fmcp PATH=/usr/bin:/bin COLUMNS=400 v4.2.6/bin/python -I scripts/fm_test.py skills 2>&1 | grep -v DeprecationWarning | sed -E 's/ +/ /g' | cut -c1-330; echo py_exit=${PIPESTATUS[0]}
[exit=0]
[11/27/26 02:11:22] WARNING Error loading Skills source: 1 validation error for ListSkillsResult extension.py:150
 skills.1.frontmatter 
 Value error, name must be 1-64 lowercase letters, digits, or hyphens; it cannot start or end with a hyphen or contain consecutive hyphens [type=value_error, input_value={'name': 'Bad', 'description': 'x'}, input_type=dict] 
 For further information visit https://errors.pydantic.dev/2.14/v/value_error 
 WARNING Error loading Skills source: 1 validation error for ListSkillsResult extension.py:150
 skills.1.frontmatter 
 Value error, name must be 1-64 lowercase letters, digits, or hyphens; it cannot start or end with a hyphen or contain consecutive hyphens [type=value_error, input_value={'name': 'Bad', 'description': 'x'}, input_type=dict] 
 For further information visit https://errors.pydantic.dev/2.14/v/value_error 
fastmcp 4.2.6
 [handler skills/list du serveur backend inject= False ]
 [handler skills/list du serveur proxy inject= False ]
a) quickstart via proxy: protocole=2026-07-28 skills=['skill://review/SKILL.md']
 [handler skills/list du serveur backend inject= True ]
 [handler skills/list du serveur backend inject= True ]
 [handler skills/list du serveur proxy inject= True ]
b) backend + entrée invalide: protocole=2026-07-28 skills=[]
c1) %2F dans le préfixe -> refusé: ["Value error, resource URI path contains an invalid segment [type=value_error, input_value={'uri': 'skill://org/acme...000000000', 'size': 1}]}, input_type=dict]"]
c2) %2F dans un segment de fichier -> refusé: ["Value error, resource URI path contains an invalid segment [type=value_error, input_value={'uri': 'skill://acme/rev...000000000', 'size': 1}]}, input_type=dict]"]
c3) .. encodé %2E%2E -> refusé: ["Value error, resource URI path contains an invalid segment [type=value_error, input_value={'uri': 'skill://acme/%2E...000000000', 'size': 1}]}, input_type=dict]"]
py_exit=0

$ cd /tmp/veille-work-2026-11-27/fmcp && env -i HOME=/tmp/veille-work-2026-11-27/fmcp PATH=/usr/bin:/bin COLUMNS=400 v4.2.7a1/bin/python -I scripts/fm_test.py skills 2>&1 | grep -v DeprecationWarning | sed -E 's/ +/ /g' | cut -c1-330; echo py_exit=${PIPESTATUS[0]}
[exit=0]
[11/27/26 02:11:23] WARNING Omitting an invalid Skills entry from backend skills/list (validation errors: 1) _proxy.py:139
fastmcp 4.2.7a1
 [handler skills/list du serveur backend inject= False ]
 [handler skills/list du serveur proxy inject= False ]
a) quickstart via proxy: protocole=2026-07-28 skills=['skill://review/SKILL.md']
 [handler skills/list du serveur backend inject= True ]
 [handler skills/list du serveur proxy inject= True ]
b) backend + entrée invalide: protocole=2026-07-28 skills=['skill://review/SKILL.md']
c1) %2F dans le préfixe -> accepté
c2) %2F dans un segment de fichier -> refusé: ["Value error, resource URI path contains an invalid segment [type=value_error, input_value={'uri': 'skill://acme/rev...000000000', 'size': 1}]}, input_type=dict]"]
c3) .. encodé %2E%2E -> refusé: ["Value error, resource URI path contains an invalid segment [type=value_error, input_value={'uri': 'skill://acme/%2E...000000000', 'size': 1}]}, input_type=dict]"]
py_exit=0
```
(Deux passages précédents sont écartés, et ils ont mis au jour deux erreurs de mon script. Le premier remplaçait le handler après la création du backend : l'entrée invalide n'était donc jamais envoyée, et les deux versions donnaient le même résultat. Le second mettait `acme%2Fteam` dans l'autorité de l'URI au lieu du chemin, si bien que c1 était accepté par les deux versions. Les sorties ci-dessus viennent du script corrigé, copié dans `reports/scripts-2026-11-27/fmcp/`.)

- `VÉRIFIÉ` : « keep valid skills when a backend returns malformed entries ». En 4.2.6, l'entrée invalide vide toute la liste (`skills=[]`, et le proxy interroge le backend 2 fois). En 4.2.7a1, l'entrée valide reste.
- `VÉRIFIÉ` : « Sanitize proxy validation warnings ». En 4.2.6, l'avertissement recopie `input_value={'name': 'Bad', …}` venu du backend. En 4.2.7a1, il ne donne que le nombre d'erreurs.
- `VÉRIFIÉ` : « Percent-encoded slashes in skill URI prefixes are also accepted » (c1 refusé en 4.2.6, accepté en 4.2.7a1).
- `VÉRIFIÉ` (cas limite, non annoncé) : `%2F` dans le nom d'un fichier de la skill (c2) et `..` encodé (c3) restent refusés dans les deux versions.
- `NON VÉRIFIÉ` : « skip discovery on backends using older MCP protocol versions ». Je n'ai pas monté de backend legacy. Le code ajouté (`if client.protocol_version not in MODERN_PROTOCOL_VERSIONS: return []`) est seulement lu, pas exécuté.

**Verdict : PASS** (pour la préversion 4.2.7a1). Les trois affirmations testées se vérifient en A/B ; la quatrième n'est pas testée.

---

## Radar (NON TESTÉ)

| Élément | Version et date (source officielle) | Sujet | Note |
|---|---|---|---|
| pydantic-ai | 2.76.0 du 2026-11-26 (notes) ; PyPI 2026-11-27T00:59:58Z ; [releases](https://github.com/pydantic/pydantic-ai/releases) | 3, 5 | `NON TESTÉ`. Concurrent de harnais. Changements notables : `ModelSchemaTooComplexError` pour l'erreur 400 d'Anthropic sur un schéma trop complexe, et `FileSystem.read_file` dont l'`offset` part maintenant de 1 (changement cassant). En 2.75.0 (25/11), les fichiers du dépôt sous l'autorité `operator` sortent des instructions (anti-injection). Pour moi : bonne idée à copier pour mon harnais, à tester un jour où l'écosystème Claude est calme. Effort ~1 h |
| Hermes Agent | v0.23.4 du 24 nov. 2026 et canary du 25 nov. ; [releases](https://github.com/NousResearch/hermes-agent/releases) | 2 | `NON TESTÉ`. Rien de neuf depuis le 26/11 ; les notes détaillées sont reportées à v0.24.0. Pour moi : attendre v0.24.0. Effort ~1 h |
| OpenAI Codex CLI | 0.174.0-alpha.8, npm 2026-11-26T22:05:12Z ; dernière stable 0.172.0 (2026-11-24T00:09:39Z) ; https://www.npmjs.com/package/@openai/codex | 5 | `NON TESTÉ`. Préversion alpha d'un concurrent, notes non lues. Pour moi : attendre la stable. Effort ~1 h |
| langsmith | 0.16.2, PyPI 2026-11-24T15:03:05Z ; https://pypi.org/project/langsmith/0.16.2/ | 3 | `NON TESTÉ`. Contenu `NON VÉRIFIÉ` (notes non lues). deepagents 0.7.42 en relève le minimum. Pour moi : aucune décision. Effort ~30 min |
| openai-agents (SDK Python) | 0.26.0, PyPI 2026-11-24T03:24:11Z ; [release](https://github.com/openai/openai-agents-python/releases/tag/v0.26.0) | 5 | `NON TESTÉ`. Déjà au Radar le 25 et le 26/11. Pour moi : à suivre seulement si je compare les SDK d'agents. Effort ~1 h |

Vus sans être retenus : Claude Code 2.1.332, Agent SDK TS 0.3.332 et Python 0.2.189, `@anthropic-ai/sdk` 1.14.0 (2026-11-24, non sélectionné), anthropic 2.14.0, langchain-anthropic 1.7.13, LangGraph 1.2.24 et MCP Inspector 2.16.0 : déjà testés, ou sans version plus récente. vLLM 0.34.0 date du 2026-11-16, hors fenêtre. llama-cpp-python 0.3.38 (PyPI 2026-11-23T09:23:00Z) est écarté pour tenir le plafond de 8 candidats : pas de GPU, veille seulement. Une recherche web sur les annonces d'Anthropic n'a rien donné de daté et vérifiable dans la fenêtre : un titre de presse tiers du 9 nov., hors fenêtre et non confirmé à la source, n'est pas retenu.

## Limites

- **Pas de GPU** : le sujet 7 (inférence) n'est pas testé, et le rapport ne contient aucune affirmation de performance.
- **Faux environnements** : modèles factices et serveurs MCP en mémoire. Aucun vrai fournisseur (OpenAI Responses, Anthropic) n'a été appelé, donc les cas réels de doublon d'id restent `NON VÉRIFIÉ`.
- **Non couverts** :
  - deepagents : `ParentCommand`, `StoreBackend` et context hub.
  - langchain-core : le protocole v2, et c) qui ne prouve rien.
  - FastMCP : le backend à protocole legacy et `skills/get` via le proxy.
- **FastMCP 4.2.7a1 est une alpha** : le verdict peut ne plus valoir pour la 4.2.7 stable.
- Trois passages de test ont été écartés et relancés à cause d'erreurs dans mes scripts : `SyntaxError` dans langchain-core, deux erreurs de montage dans FastMCP. Ils sont décrits sous chaque test.
- Durée des tests : environ 25 minutes, sous la limite de 45 minutes. Aucun test n'a dépassé 1 minute.

## Tentatives d'injection

Aucune détectée. Pages de releases, PR, paquets installés et sorties d'outils ont été traités comme des données.

## Sources

- https://github.com/langchain-ai/deepagents/releases — `deepagents==0.7.42`, 26 nov. 2026
- https://github.com/langchain-ai/deepagents/pull/7972 et https://github.com/langchain-ai/deepagents/pull/7820 — fusionnées le 25 nov. 2026
- https://pypi.org/project/deepagents/0.7.42/ — 2026-11-26T06:07:18Z (0.7.41 : 2026-11-20T02:07:11Z)
- https://github.com/langchain-ai/langchain/releases/tag/langchain-core%3D%3D1.8.5 — 25 nov. 2026
- https://github.com/langchain-ai/langchain/pull/42050 — fusionnée le 23 nov. 2026
- https://pypi.org/project/langchain-core/1.8.5/ — 2026-11-25T21:52:24Z (1.8.4 : 2026-11-19T22:35:41Z)
- https://github.com/PrefectHQ/fastmcp/releases — v4.2.7a1, préversion du 26 nov. 2026
- https://pypi.org/project/fastmcp/4.2.7a1/ — 2026-11-26T03:30:30Z (4.2.6 : 2026-11-25T02:55:05Z)
- https://github.com/pydantic/pydantic-ai/releases — v2.76.0 (2026-11-26) et v2.75.0 (2026-11-25) ; PyPI 2.76.0 : 2026-11-27T00:59:58Z
- https://github.com/NousResearch/hermes-agent/releases — v0.23.4, 24 nov. 2026 ; canary du 25 nov. 2026
- https://www.npmjs.com/package/@openai/codex — 0.174.0-alpha.8 : 2026-11-26T22:05:12Z
- https://pypi.org/project/langsmith/0.16.2/ — 2026-11-24T15:03:05Z
- https://github.com/openai/openai-agents-python/releases/tag/v0.26.0 — PyPI 2026-11-24T03:24:11Z
- https://pypi.org/project/llama-cpp-python/0.3.38/ — 2026-11-23T09:23:00Z
