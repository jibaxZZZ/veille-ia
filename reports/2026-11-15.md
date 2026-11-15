# Veille IA — 2026-11-15

## TL;DR

- **Date du run** : 2026-11-15, fenêtre de détection du 2026-11-08 au 2026-11-15. **8 éléments détectés, 3 testés, 5 au Radar.**
- **Hermes Agent v0.23.1 : PASS.** En v0.23.0, le catalogue de plugins en ligne est refusé (« payload too large ») ; en v0.23.1, il est accepté. Le catalogue pèse 4,6 Mo mesurés aujourd'hui (2,1 Mo le 9/11 selon un commentaire du code amont, `NON VÉRIFIÉ`) : mets Hermes à jour.
- **LangGraph 1.2.22 : PASS.** Le flux `subgraphs=True` d'un sous-graphe lancé sur son propre `thread_id`, perdu de 1.2.19 à 1.2.21, est rétabli (A/B 1.2.18 / 1.2.19 / 1.2.20 / 1.2.21 / 1.2.22).
- **Claude Code 2.1.325 : PASS (périmètre hors modèle).** 2 affirmations sont `VÉRIFIÉ` en A/B contre 2.1.323, 4 sont `NON VÉRIFIÉ`, dont les changements sur le sandbox et les tâches planifiées (il faut une session connectée).
- Aucune tentative d'injection n'a été relevée. Aucun test GPU n'a été fait (pas de GPU sur cette machine).

## Contexte et choix faits sans validation humaine

- Répertoire de travail : `/tmp/veille-work-2026-11-15/`, avec un sous-dossier par élément. Chaque commande passe par un wrapper qui consigne la commande, le code de sortie et la sortie (tronquée à 40 lignes) dans `logs/*.log`. Les sorties ci-dessous sont copiées de ces journaux.
- Outils de la machine : macOS arm64, Node v24.22.1, npm 11.21.1, uv 0.13.6, Python des venv : 3.13.
- Isolation : chaque binaire testé est lancé avec `env -i` et un `HOME` (et `CLAUDE_CONFIG_DIR` / `HERMES_HOME`) jetable dans `/tmp`. Aucune variable d'environnement ni aucun identifiant de la machine n'est transmis.
- `tested.md` était vide : aucun doublon possible (B5).
- Pour 2.1.325, la référence est **2.1.323** et non 2.1.324. Le CHANGELOG n'a pas de section 2.1.324 : la section « 2.1.325 » couvre aussi 2.1.324, publiée le même jour (vérifié : en-têtes `## 2.1.325` puis `## 2.1.323`).

---

## Tests

### 1. Hermes Agent v0.23.1 — plafond du catalogue de plugins (2 Mio → 16 Mio)

- **Sujet** : 2 (Hermes Agent). **Ce que ça change pour moi** : en v0.23.0, le chargement du catalogue en ligne échoue sans message visible (observé ici ; les versions antérieures et l'effet sur `hermes plugins install` sont `NON VÉRIFIÉ`). Il faut passer en v0.23.1, et surveiller la croissance du catalogue vers le nouveau plafond de 16 Mio (projection plus bas). **Effort** : ~15 min (mise à jour d'une instance).
- **Source** : https://github.com/NousResearch/hermes-agent/releases/tag/v0.23.1. Publiée le 2026-11-10T01:42:15Z selon `published_at` de l'API GitHub ; les notes indiquent « Release Date: November 9, 2026 ».
- **Méthode** : clone des tags officiels v0.23.0 et v0.23.1, puis appel direct de `hermes_cli.plugin_catalog.fetch_live_catalog(force=True)` de chaque version. Le venv minimal contient `httpx==0.28.1` et `ruamel.yaml==0.18.16`, épinglés comme dans le `pyproject.toml` de v0.23.1. Aucun installeur n'est lancé et `~/.hermes` n'est pas touché. Le script de test est `/tmp/veille-work-2026-11-15/hermes/scripts/fetch_test.py`, reproduit ci-dessous.

```python
import sys, os, logging
src = sys.argv[1]
sys.path.insert(0, src)
logging.basicConfig(level=logging.DEBUG, format="%(name)s %(levelname)s %(message)s")
for n in ("httpx", "httpcore"): logging.getLogger(n).setLevel(logging.WARNING)
from hermes_cli import plugin_catalog as pc
print("HERMES_HOME =", os.environ.get("HERMES_HOME"))
print("_MAX_LIVE_BYTES =", pc._MAX_LIVE_BYTES)
data = pc.fetch_live_catalog(force=True)
print("live catalog used:", data is not None)
if data is not None:
    print("entries:", len(data["entries"]))
```

**Commandes et sorties** (répertoire `/tmp/veille-work-2026-11-15/hermes`) :

```
$ git -c advice.detachedHead=false clone -q --depth 1 --branch v0.23.1 https://github.com/NousResearch/hermes-agent.git src-v0.23.1 && git -C src-v0.23.1 log -1 --format='%H %cI'
[exit=0]
warning: refs/tags/v0.23.1 b65acf3fdc1d43bd889211ea8e37032974b395a5 is not a commit!
3b421578588243f920886e6fe79a6faa87ea026e 2026-11-09T16:24:33-08:00
```
(Même commande pour v0.23.0 : exit 0, commit `2bd378ed1b8d6bf2192cb26e0a55ff3091e6bd19`. Le commit de v0.23.1 correspond au « Measured at commit `3b421578588` » des notes de version.)

```
$ diff src-v0.23.0/hermes_cli/plugin_catalog.py src-v0.23.1/hermes_cli/plugin_catalog.py
[exit=1]
41c41,44
< _MAX_LIVE_BYTES = 2 * 1024 * 1024
---
> # The published doc passed 2 MiB on 2026-11-09 (2,109,306 bytes for 1,268 entries, about 1.7 KB each), and a
> # client that refuses it silently installs its own in-tree pins and misses newer removals. 16 MiB leaves
> # room for roughly 9,000 entries while still bounding a hostile or broken response.
> _MAX_LIVE_BYTES = 16 * 1024 * 1024
```

```
$ cd /tmp/veille-work-2026-11-15/hermes/live && curl -sS -L -o plugin-catalog.json -w 'http=%{http_code} size_download=%{size_download}\n' https://hermes-agent.nousresearch.com/docs/api/plugin-catalog.json && python3 -I -c 'import json; d=json.load(open("plugin-catalog.json")); print("entries=",len(d["entries"]),"removed=",len(d.get("removed",[])), "bytes>2MiB:", __import__("os").path.getsize("plugin-catalog.json")>2*1024*1024)'
[exit=0]
http=200 size_download=4604432
entries= 2379 removed= 1 bytes>2MiB: True
```

```
$ cd /tmp/veille-work-2026-11-15/hermes && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-15/hermes/home2-v0.23.0 HERMES_HOME=/tmp/veille-work-2026-11-15/hermes/home2-v0.23.0/.hermes venv/bin/python -I scripts/fetch_test.py /tmp/veille-work-2026-11-15/hermes/src-v0.23.0
[exit=0]
hermes_cli.plugin_catalog DEBUG Plugin catalog: live fetch failed: live catalog payload too large
HERMES_HOME = /tmp/veille-work-2026-11-15/hermes/home2-v0.23.0/.hermes
_MAX_LIVE_BYTES = 2097152
live catalog used: False

$ cd /tmp/veille-work-2026-11-15/hermes && env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-15/hermes/home2-v0.23.1 HERMES_HOME=/tmp/veille-work-2026-11-15/hermes/home2-v0.23.1/.hermes venv/bin/python -I scripts/fetch_test.py /tmp/veille-work-2026-11-15/hermes/src-v0.23.1
[exit=0]
HERMES_HOME = /tmp/veille-work-2026-11-15/hermes/home2-v0.23.1/.hermes
_MAX_LIVE_BYTES = 16777216
live catalog used: True
entries: 2379

$ ls -la /tmp/veille-work-2026-11-15/hermes/home2-v0.23.0/.hermes/cache/ /tmp/veille-work-2026-11-15/hermes/home2-v0.23.1/.hermes/cache/ 2>&1
[exit=1]
ls: /tmp/veille-work-2026-11-15/hermes/home2-v0.23.0/.hermes/cache/: No such file or directory
/tmp/veille-work-2026-11-15/hermes/home2-v0.23.1/.hermes/cache/:
total 9200
drwxr-xr-x@ 3 jib  wheel       96 Nov 15 23:52 .
drwxr-xr-x@ 3 jib  wheel       96 Nov 15 23:52 ..
-rw-r--r--@ 1 jib  wheel  4706911 Nov 15 23:52 plugin-catalog.json
```
(Ces commandes sont lancées sans tube : le code de sortie est celui de Python ou de `ls`. Un premier passage identique, filtré par `| grep -v '^httpx\|^httpcore'`, avait donné les mêmes lignes.)

**Doc contre réalité :**

| Affirmation (notes v0.23.1) | Étiquette |
|---|---|
| Le `plugin-catalog.json` publié dépasse le plafond de 2 Mio | `VÉRIFIÉ` (4 604 432 octets le 2026-11-15) |
| v0.23.0 et antérieures se rabattent silencieusement sur le catalogue embarqué | `VÉRIFIÉ` pour v0.23.0 : `fetch_live_catalog` renvoie `None`, la cause n'apparaît qu'en DEBUG, aucun cache n'est écrit. Versions antérieures : `NON VÉRIFIÉ` |
| v0.23.1 relève le plafond à 16 Mio et utilise de nouveau le catalogue en ligne | `VÉRIFIÉ` (`_MAX_LIVE_BYTES = 16777216`, 2379 entrées chargées) |
| Effet de bout en bout sur `hermes plugins install <name>` | `NON VÉRIFIÉ` (CLI complète non installée, seule la fonction de chargement a été testée) |

**Projection (calcul, pas un fait vérifié)** : d'après le commentaire de v0.23.1, le catalogue faisait 2 109 306 octets le 2026-11-09. Il en fait 4 604 432 le 2026-11-15, soit ×2,2 en 6 jours. 16 Mio (16 777 216 octets) seraient atteints vers le 2026-11-25 si la croissance reste multiplicative, ou vers le 2026-12-14 si elle est linéaire (~416 Ko/jour). À surveiller : un nouveau dépassement referait tomber les clients dans le même mode dégradé silencieux.

**Verdict : `PASS`** — le correctif fonctionne en A/B réel sur le catalogue publié aujourd'hui.

---

### 2. LangGraph 1.2.22 — flux d'un sous-graphe lancé sur son propre thread (#9698)

- **Sujet** : 2 (LangGraph). **Ce que ça change pour moi** : un graphe parent qui appelle un sous-graphe avec un autre `thread_id` (le cas d'un agent délégué qui a sa propre mémoire) ne voyait plus les messages de ce sous-graphe dans `stream(..., subgraphs=True)` de 1.2.19 à 1.2.21 (testé). Si tu épingles une de ces versions, passe en 1.2.22. **Effort** : ~10 min (relever l'épinglage et relancer les tests).
- **Source** : https://github.com/langchain-ai/langgraph/releases/tag/1.2.22. Publiée le 2026-11-14T01:43:55Z (API GitHub) ; PyPI `langgraph==1.2.22` le 2026-11-14T01:43:42Z. Correctif : https://github.com/langchain-ai/langgraph/pull/9698
- **Prérequis** : `uv venv --python 3.13 venv-<v>` puis `uv pip install 'langgraph==<v>'` pour 1.2.18, 1.2.19, 1.2.20, 1.2.21 et 1.2.22. Versions résolues : langchain-core 1.8.1, langgraph-checkpoint 4.3.2. Aucune clé ni aucun LLM n'est nécessaire.

```
$ cd /tmp/veille-work-2026-11-15/langgraph && uv venv -q --python 3.13 venv-1.2.22 && VIRTUAL_ENV=/tmp/veille-work-2026-11-15/langgraph/venv-1.2.22 uv pip install -q 'langgraph==1.2.22' && venv-1.2.22/bin/python -I -c 'from importlib.metadata import version as v; print(v("langgraph"), v("langchain-core"), v("langgraph-checkpoint"))'
[exit=0]
1.2.22 1.8.1 4.3.2
```
(Identique pour 1.2.18, 1.2.19, 1.2.20 et 1.2.21 : exit 0, avec `<version> 1.8.1 4.3.2`.)

Script `scripts/test_subgraph_stream.py`. Le sous-graphe a un checkpointer ; `own-thread` l'appelle avec `{"configurable": {"thread_id": "child-thread"}}` et `inherited` sans config. Le 2ᵉ argument `nosubgraphs` passe `subgraphs=False`.

```python
import operator, sys
from typing import Annotated, TypedDict
import langgraph
from importlib.metadata import version
from langchain_core.messages import AIMessage, AnyMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class S(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def child_node(state):
    return {"messages": [AIMessage(content="hello-from-child", id="child-msg")]}

child = StateGraph(S).add_node("child_node", child_node).add_edge(START, "child_node").add_edge("child_node", END).compile(checkpointer=InMemorySaver())

mode = sys.argv[1]
subg = (sys.argv[2] if len(sys.argv)>2 else "subgraphs") == "subgraphs"
def parent_node(state, config):
    if mode == "own-thread":
        out = child.invoke({"messages": []}, {"configurable": {"thread_id": "child-thread"}})
    else:
        out = child.invoke({"messages": []})
    return {"messages": [AIMessage(content="parent-done", id="parent-msg")]}

parent = StateGraph(S).add_node("parent_node", parent_node).add_edge(START, "parent_node").add_edge("parent_node", END).compile(checkpointer=InMemorySaver())

print("langgraph", version("langgraph"), "| mode", mode, "| subgraphs", subg)
seen = []
for item in parent.stream({"messages": []}, {"configurable": {"thread_id": "p1"}}, stream_mode="messages", subgraphs=subg):
    ns, (msg, meta) = item if subg else ((), item)
    seen.append(msg.content)
    print("ns=", ns, "node=", meta.get("langgraph_node"), "content=", msg.content)
print("child message streamed:", "hello-from-child" in seen)
```

**Sorties** (toutes lancées depuis `/tmp/veille-work-2026-11-15/langgraph`) :

```
$ venv-1.2.18/bin/python -I scripts/test_subgraph_stream.py own-thread
[exit=0]
langgraph 1.2.18 | mode own-thread | subgraphs True
ns= () node= child_node content= hello-from-child
ns= () node= parent_node content= parent-done
child message streamed: True

$ venv-1.2.19/bin/python -I scripts/test_subgraph_stream.py own-thread
[exit=0]
langgraph 1.2.19 | mode own-thread | subgraphs True
ns= () node= parent_node content= parent-done
child message streamed: False

$ venv-1.2.20/bin/python -I scripts/test_subgraph_stream.py own-thread
[exit=0]
langgraph 1.2.20 | mode own-thread | subgraphs True
ns= () node= parent_node content= parent-done
child message streamed: False

$ venv-1.2.21/bin/python -I scripts/test_subgraph_stream.py own-thread
[exit=0]
langgraph 1.2.21 | mode own-thread | subgraphs True
ns= () node= parent_node content= parent-done
child message streamed: False

$ venv-1.2.22/bin/python -I scripts/test_subgraph_stream.py own-thread
[exit=0]
langgraph 1.2.22 | mode own-thread | subgraphs True
ns= () node= child_node content= hello-from-child
ns= () node= parent_node content= parent-done
child message streamed: True

$ venv-1.2.21/bin/python -I scripts/test_subgraph_stream.py inherited
[exit=0]
langgraph 1.2.21 | mode inherited | subgraphs True
ns= ('parent_node:2e496b9c-bf98-e564-657d-f5c855b0e0a0',) node= child_node content= hello-from-child
ns= () node= parent_node content= parent-done
child message streamed: True

$ venv-1.2.22/bin/python -I scripts/test_subgraph_stream.py inherited
[exit=0]
langgraph 1.2.22 | mode inherited | subgraphs True
ns= ('parent_node:d31066f3-79ce-3377-881f-83c56e3a3ef7',) node= child_node content= hello-from-child
ns= () node= parent_node content= parent-done
child message streamed: True
```

Cas limite, appelant **sans** `subgraphs=True` :

```
$ venv-1.2.18/bin/python -I scripts/test_subgraph_stream.py own-thread nosubgraphs
[exit=0]
langgraph 1.2.18 | mode own-thread | subgraphs False
ns= () node= child_node content= hello-from-child
ns= () node= parent_node content= parent-done
child message streamed: True

$ venv-1.2.22/bin/python -I scripts/test_subgraph_stream.py own-thread nosubgraphs
[exit=0]
langgraph 1.2.22 | mode own-thread | subgraphs False
ns= () node= parent_node content= parent-done
child message streamed: False
```

**Doc contre réalité** (description de la PR #9698) :

| Affirmation | Étiquette |
|---|---|
| Depuis 1.2.19, un sous-graphe lancé avec son propre `thread_id` perd ses messages pour un appelant en `subgraphs=True` | `VÉRIFIÉ` (1.2.18 : `True` ; 1.2.19, 1.2.20 et 1.2.21 : `False`) |
| 1.2.22 les rétablit pour un appelant en `subgraphs=True` | `VÉRIFIÉ` |
| Les événements gardent l'espace de noms propre au sous-graphe, `()` | `VÉRIFIÉ` (`ns= ()` en 1.2.22) |
| Un appelant sans `subgraphs=True` ne reçoit pas ces événements (comportement voulu depuis 1.2.19) | `VÉRIFIÉ` pour 1.2.22. En 1.2.18, l'appelant les recevait : c'est bien un changement de comportement, à connaître si tu montes de ≤1.2.18 |
| Le sous-graphe à config héritée n'est pas affecté | `VÉRIFIÉ` (1.2.21 et 1.2.22 : `True`, espace de noms `parent_node:<id>`) |
| Les 5 optimisations `perf(...)` de 1.2.22 | `NON VÉRIFIÉ` (pas mesurées) |

**Verdict : `PASS`** — régression reproduite en 1.2.21 et corrigée en 1.2.22, avec le comportement annoncé.

---

### 3. Claude Code 2.1.325 (hors session modèle)

- **Sujet** : 1 (Claude Code, plugins, tâches planifiées) et 3 (harnais, permissions). **Ce que ça change pour moi** : selon le CHANGELOG (`NON VÉRIFIÉ` ici), les tâches planifiées et `/loop` demandent confirmation avant une skill qui déclare `allowed-tools` ou des hooks, et le sandbox Bash ne s'auto-approuve plus par défaut. Une routine sans surveillance pourrait donc se bloquer ; le CHANGELOG indique comme parades `Skill(name)` dans `permissions.allow` et `sandbox.autoAllowBashIfSandboxed: true`. **Effort** : ~15 min pour relire les réglages de la routine.
- **Source** : https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md (section `## 2.1.325`). Dates npm (`npm view @anthropic-ai/claude-code time`) : 2.1.323 le 2026-11-12T20:29:28Z, 2.1.324 le 2026-11-13T18:42:36Z, 2.1.325 le 2026-11-13T20:07:25Z.
- **Installation** (commandes exactes ; l'exit affiché est celui de `tail`, et la ligne `added 2 packages` confirme l'installation) :

```
$ cd /tmp/veille-work-2026-11-15/claude-code && npm install --prefix ./v2.1.325 --no-audit --no-fund @anthropic-ai/claude-code@2.1.325 2>&1 | tail -5
[exit=0]
added 2 packages in 9s
npm warn install-scripts 1 package has install scripts not yet covered by allowScripts:
npm warn install-scripts   @anthropic-ai/claude-code@2.1.325 (postinstall: node install.cjs)
npm warn install-scripts
npm warn install-scripts Run `npm install-scripts ls` to review, or `npm install-scripts approve <pkg>` to allow.

$ cd /tmp/veille-work-2026-11-15/claude-code && npm install --prefix ./v2.1.323 --no-audit --no-fund --ignore-scripts @anthropic-ai/claude-code@2.1.323 2>&1 | tail -2
[exit=0]

added 2 packages in 9s
```
  2.1.324 utilise la même commande que 2.1.325 et donne la même sortie. Pour 2.1.324 et 2.1.325, npm 11 n'a pas lancé le `postinstall` (avertissement ci-dessus) ; pour 2.1.323, il a été ignoré avec `--ignore-scripts`. `install.cjs` a été lu : il ne fait que copier le binaire du paquet de plateforme. Le binaire `node_modules/@anthropic-ai/claude-code-darwin-arm64/claude` est donc appelé directement. Dans la suite, `$C<v>` désigne `env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-15/claude-code/home-<v> CLAUDE_CONFIG_DIR=<HOME>/.claude /tmp/veille-work-2026-11-15/claude-code/v<v>/node_modules/@anthropic-ai/claude-code-darwin-arm64/claude`.

```
$ $C2.1.325 --version
[exit=0]
2.1.325 (Claude Code)
```
(2.1.323 : exit 0, `2.1.323 (Claude Code)` ; 2.1.324 : exit 0, `2.1.324 (Claude Code)`.)

**a) `plugin eval --output-dir ''`.** Le plugin de test `fixture-clean` contient un manifeste, une skill et `evals/basic/prompt.md`. La commande est lancée depuis un dossier vide `evalcwd-<v>`.

```
$ cd evalcwd-2.1.323 && $C2.1.323 plugin eval ../fixture-clean --output-dir '' --trust-plugin --ablation none
[exit=1]
✗ /private/tmp/veille-work-2026-11-15/claude-code/fixture-clean/evals/basic: invalid case.yaml:   graders: Required

CASE  SCORE PASS% RUNS COST    NOTES

0 case(s) · 0s · $0.00

1 case file(s) failed to load — see above.

$ cd evalcwd-2.1.325 && $C2.1.325 plugin eval ../fixture-clean --output-dir '' --trust-plugin --ablation none
[exit=1]
Error: --output-dir was given an empty path; pass a directory, or omit it to use the default results directory

$ cd evalcwd-2.1.325 && ls -A | head; echo "entries=$(ls -A | wc -l)"
[exit=0]
entries=       0
```
2.1.324 donne exactement la même erreur que 2.1.325 (exit 1). Aucun fichier n'est écrit dans le dossier courant, quelle que soit la version.

**b) `teammateMode` non reconnu signalé par `claude doctor`.** Le fichier `settings.json` du `CLAUDE_CONFIG_DIR` jetable contient `{"teammateMode":"bogus-value"}`. `ANTHROPIC_API_KEY=invalid-test-key` est une valeur volontairement invalide (ce n'est pas un secret), passée pour qu'aucun identifiant réel ne soit cherché.

Le code de sortie affiché est celui du pipeline (`head`), pas celui de `claude doctor`.

```
$ cd /tmp/veille-work-2026-11-15/claude-code && perl -e 'alarm 45; exec @ARGV' env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-15/claude-code/home-tm-2.1.323 CLAUDE_CONFIG_DIR=/tmp/veille-work-2026-11-15/claude-code/home-tm-2.1.323/.claude ANTHROPIC_API_KEY=invalid-test-key /tmp/veille-work-2026-11-15/claude-code/v2.1.323/node_modules/@anthropic-ai/claude-code-darwin-arm64/claude doctor < /dev/null 2>&1 | grep -i -n 'teammate\|skipped\|invalid\|setting' | head -15
[exit=0]
12:Managed settings (remote): fetch failed — no policy applied (authentication rejected (401))

$ cd /tmp/veille-work-2026-11-15/claude-code && perl -e 'alarm 45; exec @ARGV' env -i PATH=/usr/bin:/bin HOME=/tmp/veille-work-2026-11-15/claude-code/home-tm-2.1.325 CLAUDE_CONFIG_DIR=/tmp/veille-work-2026-11-15/claude-code/home-tm-2.1.325/.claude ANTHROPIC_API_KEY=invalid-test-key /tmp/veille-work-2026-11-15/claude-code/v2.1.325/node_modules/@anthropic-ai/claude-code-darwin-arm64/claude doctor < /dev/null 2>&1 | grep -i -n 'teammate\|skipped\|invalid\|setting' | head -15
[exit=0]
12:Managed settings (remote): fetch failed — no policy applied (authentication rejected (401))
15:Invalid settings
16:- /tmp/veille-work-2026-11-15/claude-code/home-tm-2.1.325/.claude/settings.json › teammateMode: "teammateMode" must be one of "auto", "tmux", "iterm2", "in-process"; received "bogus-value". This value is ignored and teammates use the mode from your other settings or the default ("in-process"); change it to one of the values above.
```

**c) `plugin validate` et liens dangereux.** `fixture-plugin` contient `skills/etc-link -> /etc` et `skills/hello/outside-link.txt -> ../../../outside/data.txt` (un fichier factice hors du plugin).

```
$ cd /tmp/veille-work-2026-11-15/claude-code && $C2.1.325 plugin validate ./fixture-plugin
[exit=0]
Validating plugin manifest: /private/tmp/veille-work-2026-11-15/claude-code/fixture-plugin/.claude-plugin/plugin.json

⚠ Found 1 warning:

  ❯ author: No author information provided. Consider adding author details for plugin attribution

Validating skill: /private/tmp/veille-work-2026-11-15/claude-code/fixture-plugin/skills

⚠ Found 1 warning:

  ❯ directory: 1 entry here is a symlink and was not read — components are read without following symlinks. A session started with --plugin-dir on this plugin follows a symlink here. [...]
[... 20 lignes suivantes tronquées : contrôles README/LICENSE/icône de l'annuaire, puis « ✔ Validation passed with warnings »]
```
2.1.324 (exit 0) produit la même sortie, avertissement « 1 entry here is a symlink and was not read » et « Validation passed with warnings » compris. Pour 2.1.323, la sortie a été lue via `| sed -n '1,12p'` (le code de sortie affiché est donc celui de `sed`) : ses 12 premières lignes contiennent le même avertissement. Aucune version ne signale le lien imbriqué `skills/hello/outside-link.txt`.

**Doc contre réalité** (CHANGELOG 2.1.325) :

| Affirmation | Étiquette |
|---|---|
| `claude plugin eval --output-dir ''` « now exits with an error » | `VÉRIFIÉ` (2.1.325 : exit 1 avec message explicite ; 2.1.323 ne valide pas l'argument). Le comportement était déjà présent en 2.1.324 |
| `--output-dir ''` écrivait auparavant le rapport dans le dossier courant | `NON VÉRIFIÉ` (en 2.1.323, mon cas d'éval n'a pas été chargé, `graders: Required`, donc aucun rapport n'a été produit) |
| Un `teammateMode` non reconnu est listé par `claude doctor` (« still not applied ») | `VÉRIFIÉ` (absent en 2.1.323, présent en 2.1.325 avec « This value is ignored ») |
| `plugin validate` signale « some unsafe paths and links » | `NON VÉRIFIÉ` (aucune différence avec 2.1.323 sur mes deux liens ; l'affirmation dit « some » sans préciser lesquels) |
| Sandbox Bash soumis au flux de permissions normal par défaut (`sandbox.autoAllowBashIfSandboxed`) | `NON VÉRIFIÉ` (il faut une session avec modèle) |
| Les tâches planifiées et `/loop` demandent confirmation avant une skill qui déclare `allowed-tools` ou des hooks | `NON VÉRIFIÉ` (il faut une session planifiée) |

**Verdict : `PASS`** sur le périmètre testable sans session connectée. Deux affirmations sont vérifiées en A/B, aucune n'est contredite. Les changements de permissions, qui sont les plus importants pour toi, restent à tester.

---

## Radar (NON TESTÉ)

| Élément | Version et date (source officielle) | Sujet | Pourquoi pas testé |
|---|---|---|---|
| MCP Inspector | 2.15.0, 2026-11-12T00:46:29Z ([release](https://github.com/modelcontextprotocol/inspector/releases/tag/2.15.0)) ; 1.0.5, 2026-11-11T21:39:41Z | 4 | `NON TESTÉ`. 4 correctifs de sécurité (garde de fetch contre les adresses de métadonnées cloud, flux non bornés). Mets à jour si tu l'utilises. Écarté au profit de tests plus liés aux décisions de topics.md |
| Anthropic Python SDK : modèles `claude-fable-5-2` et `claude-mythos-5-2` | v2.7.0, 2026-11-09T18:52:17Z ([release](https://github.com/anthropics/anthropic-sdk-python/releases/tag/v2.7.0)) ; v2.8.0, 2026-11-10 | 5 | `NON TESTÉ`. Demande des appels API payants avec une clé, ce qui est exclu ici. Aucune annonce sur anthropic.com trouvée dans les résultats de recherche ; seul un média tiers (Silicon Report) en parle, à titre de piste |
| Claude Agent SDK (Python 0.2.180 → 0.2.182, TS 0.3.321 → 0.3.325) | 0.2.182, 2026-11-13T21:44:32Z ([release](https://github.com/anthropics/claude-agent-sdk-python/releases/tag/v0.2.182)) | 1 | `NON TESTÉ`. Notes de version vides (suivent Claude Code) ; le correctif `applyFlagSettings()` figure dans le CHANGELOG de Claude Code |
| langgraph-cli | 0.4.43, 2026-11-12T16:20:16Z ([release](https://github.com/langchain-ai/langgraph/releases/tag/cli%3D%3D0.4.43)) | 2 | `NON TESTÉ`. Changement mineur : flags Agent Server, retrait de l'image de debugger locale abandonnée |
| Hermes Agent canary | v0.23.1+canary.20261115T064406Z, 2026-11-15T07:52:37Z ([release](https://github.com/NousResearch/hermes-agent/releases/tag/v0.23.1%2Bcanary.20261115T064406Z)) | 2 | `NON TESTÉ`. Build canary quotidien (nouveaux plugins au catalogue), pas une version stable |

## Limites

- **Pas de GPU** sur cette machine : le sujet 7 (inférence LLM en production) n'a été ni testé ni recherché ce run. Aucune affirmation de performance GPU.
- **Claude Code** : rien n'a été testé dans une session avec modèle (ni connexion ni facturation). Les changements de permissions (sandbox, tâches planifiées, « Always allow ») restent `NON VÉRIFIÉ`.
- **Hermes** : seule la fonction `fetch_live_catalog` a été testée, pas la CLI complète (`hermes plugins install`), pour ne pas lancer d'installeur ni toucher `~/.hermes`.
- **Sujets 5 et 6** (marché, onboarding client) : les recherches web n'ont donné que des sources tierces non datées ou contradictoires, et aucune annonce officielle n'a pu être vérifiée dans la fenêtre. Rien n'est retenu.
- `@langchain/langgraph` JS 1.7.2 (2026-11-07T00:07Z) est hors fenêtre (< 2026-11-08) et a été écarté. Les versions JS 1.7.3 et 1.7.4 n'ont pas été examinées.

## Tentatives d'injection

Aucune détectée. Les changelogs, notes de version, la PR #9698 et le code cloné ont été traités comme des données.

## Sources

- https://github.com/NousResearch/hermes-agent/releases/tag/v0.23.1 — 2026-11-10T01:42:15Z (« Release Date: November 9, 2026 »)
- https://github.com/NousResearch/hermes-agent/releases/tag/v0.23.0 — 2026-11-05T21:32:33Z (référence A/B)
- https://hermes-agent.nousresearch.com/docs/api/plugin-catalog.json — téléchargé le 2026-11-15
- https://github.com/langchain-ai/langgraph/releases/tag/1.2.22 — 2026-11-14T01:43:55Z
- https://github.com/langchain-ai/langgraph/releases/tag/1.2.21 — 2026-11-12T18:06:43Z
- https://github.com/langchain-ai/langgraph/pull/9698 — correctif décrit, lu le 2026-11-15
- https://pypi.org/project/langgraph/1.2.22/ — 2026-11-14T01:43:42Z
- https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md — section 2.1.325, lu le 2026-11-15
- https://www.npmjs.com/package/@anthropic-ai/claude-code — 2.1.325 le 2026-11-13T20:07:25Z, 2.1.324 le 2026-11-13T18:42:36Z, 2.1.323 le 2026-11-12T20:29:28Z
- https://github.com/modelcontextprotocol/inspector/releases/tag/2.15.0 — 2026-11-12T00:46:29Z
- https://github.com/anthropics/anthropic-sdk-python/releases/tag/v2.7.0 — 2026-11-09T18:52:17Z
- https://github.com/anthropics/claude-agent-sdk-python/releases/tag/v0.2.182 — 2026-11-13T21:44:32Z
- https://github.com/langchain-ai/langgraph/releases/tag/cli%3D%3D0.4.43 — 2026-11-12T16:20:16Z
- https://github.com/NousResearch/hermes-agent/releases/tag/v0.23.1%2Bcanary.20261115T064406Z — 2026-11-15T07:52:37Z
