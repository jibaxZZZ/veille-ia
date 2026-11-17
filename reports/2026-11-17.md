# Veille IA — 2026-11-17

## TL;DR

- **Run du 2026-11-17** (fenêtre du 2026-11-10 au 2026-11-17) : **8 éléments détectés, 3 testés (3 PASS), 5 au Radar.** Tous les tests sont des A/B contre la version précédente.
- **Claude Code 2.1.326 : PASS.** Un fichier de réglages imbriqué à 5 000 niveaux faisait planter 2.1.325 (« Maximum call stack size exceeded », exit 1). En 2.1.326, la valeur est ignorée avec un avertissement. `--allowedTools 'Bash(git status'` déclenche enfin un avertissement, et `mcp add-json` dit quel champ manque.
- **anthropic (SDK Python) 2.9.0 : PASS.** Avec 2.8.0, un faux `rg` placé dans le `workdir` et présent sur `PATH` était **exécuté** par l'outil `grep` de l'agent toolset. En 2.9.0, il est ignoré. Une FIFO bloquait la recherche intégrée en 2.8.0 (tuée après 30 s), plus en 2.9.0. Le listing `/memories` ne montre plus un lien symbolique vers l'extérieur. Mets à jour si tu utilises ces outils.
- **deepagents 0.7.39 : PASS.** `StoreBackend.upload_files` stocke désormais en base64 un contenu UTF-8 qui contient un octet NUL, au lieu d'un texte avec `\u0000`, que Postgres JSONB refuse. L'aller-retour reste identique.
- Aucune tentative d'injection relevée. Pas de GPU, donc aucun test de performance. Les tests Claude Code `-p` ont fait de vrais appels au modèle (voir Limites).

## Contexte et choix faits sans validation humaine

- Répertoire de travail : `/tmp/veille-work-2026-11-17/<élément>/`. Toutes les commandes passent par un wrapper `bin/run`, qui consigne la commande, le code de sortie et la sortie (tronquée à 40 lignes) dans `logs/<élément>.log`. Les sorties ci-dessous sont copiées de ces journaux. `[exit=…]` est le code de la commande complète (le dernier maillon d'un pipeline ou d'un `echo`). Quand cela compte, le vrai code du programme testé est affiché à part (`claude_exit=`, `python_exit=`, `case … exit=`).
- Machine : Linux x86_64, 4 CPU, Node v22.23.4, npm 10.9.9, uv 0.11.32 (venvs Python 3.11), ripgrep présent dans `/usr/bin/rg`. Pas de GPU.
- **Isolation** : Claude Code et le SDK `anthropic` ont été lancés avec `env -i` (environnement vide, `HOME` pointé vers un dossier du répertoire de travail). Aucune variable d'environnement n'a été lue ni transmise.
- **Détection** : versions et dates tirées des registres officiels (`npm view … time`, PyPI JSON) et de `git ls-remote` ; notes de version lues dans le `CHANGELOG.md` brut de Claude Code et, via WebFetch, sur les pages de release GitHub.
- **Sélection** : j'ai retenu les 3 éléments testables sans clé API et liés aux sujets 1 et 3 (Claude Code, harnais, permissions et sandboxes). Hermes v0.23.2 n'a pas été retenu : ses notes listent surtout des correctifs Desktop et TUI, et le détail est renvoyé à v0.24.0. Aucune des 3 versions testées n'est dans `tested.md` (Claude Code 2.1.325 et deepagents 0.7.38 y figurent : ici ce sont 2.1.326 et 0.7.39, donc pas de doublon au sens de B5).

---

## Tests

### 1. Claude Code 2.1.326 — garde-fous sur les réglages et les règles de permission

- **Sujet** : 1 (Claude Code) et 3 (permissions). **Ce que ça change pour moi** : une faute de frappe dans `--allowedTools` (parenthèse manquante) est maintenant signalée au lieu d'être appliquée sans un mot, et un fichier de réglages pathologique ne fait plus tomber la session. Dans tes tâches planifiées, mets à jour et regarde la sortie d'erreur au démarrage. **Effort** : ~10 min (mise à jour, puis relecture de tes listes `--allowedTools`).
- **Source** : https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md (section `## 2.1.326`, lue en brut le 2026-11-17). Date vérifiée sur npm : https://www.npmjs.com/package/@anthropic-ai/claude-code , 2.1.326 publiée le 2026-11-16T18:43:39Z (2.1.325 : 2026-11-13T20:07:25Z).
- **Prérequis** : `npm install --prefix v<v> @anthropic-ai/claude-code@<v>` ; commandes lancées depuis `/tmp/veille-work-2026-11-17/claude-code/proj` avec `env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=<dossier vide>`.

```
$ cd /tmp/veille-work-2026-11-17/claude-code && for v in 2.1.325 2.1.326; do mkdir -p v$v && npm install -q --prefix v$v @anthropic-ai/claude-code@$v >/dev/null 2>&1; echo $v install exit=$?; done; for v in 2.1.325 2.1.326; do v$v/node_modules/.bin/claude --version; done
[exit=0]
2.1.325 install exit=0
2.1.326 install exit=0
2.1.325 (Claude Code)
2.1.326 (Claude Code)
```

**a) `claude mcp add-json` avec une configuration invalide** (stdio sans `command`) :

```
$ cd /tmp/veille-work-2026-11-17/claude-code/proj && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-17/claude-code/home-2.1.325 timeout 60 /tmp/veille-work-2026-11-17/claude-code/v2.1.325/node_modules/.bin/claude mcp add-json demo '{"type":"stdio"}'
[exit=1]
Invalid configuration: : Invalid input

$ cd /tmp/veille-work-2026-11-17/claude-code/proj && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-17/claude-code/home-2.1.326 timeout 60 /tmp/veille-work-2026-11-17/claude-code/v2.1.326/node_modules/.bin/claude mcp add-json demo '{"type":"stdio"}'
[exit=1]
Invalid configuration: command: expected string, received undefined
```

Cas limite : une URL invalide pour un serveur HTTP est acceptée par les **deux** versions.

```
$ cd /tmp/veille-work-2026-11-17/claude-code/proj && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-17/claude-code/home-2.1.326 timeout 60 /tmp/veille-work-2026-11-17/claude-code/v2.1.326/node_modules/.bin/claude mcp add-json demo2 '{"type":"http","url":"not a url"}'
[exit=0]
Added http MCP server demo2 to local config
```
(2.1.325 : exit 0, même sortie.)

**b) `--allowedTools` avec une règle incomplète** :

```
$ cd /tmp/veille-work-2026-11-17/claude-code/proj && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-17/claude-code/home-2.1.325 timeout 60 /tmp/veille-work-2026-11-17/claude-code/v2.1.325/node_modules/.bin/claude -p 'say hi' --allowedTools 'Bash(git status' 'Read' < /dev/null
[exit=0]
Hi! What can I help you with today?

$ cd /tmp/veille-work-2026-11-17/claude-code/proj && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-17/claude-code/home-2.1.326 timeout 60 /tmp/veille-work-2026-11-17/claude-code/v2.1.326/node_modules/.bin/claude -p 'say hi' --allowedTools 'Bash(git status' 'Read' < /dev/null
[exit=0]
--allowedTools: "Bash(git status" doesn't look like a complete rule, so this list may allow more or less than you meant. A rule looks like Bash or Bash(git *). Check for a missing ")", a space before "(", or text after ")". If a ")" belongs inside your rule, the list may have split there and the quoted text is only part of it: move the whole rule to permissions.allow in settings this session reads.
Hi! What can I help you with today?
```

**c) Réglages imbriqués au-delà de 64 niveaux** : `deep-<n>.json` = `{"cleanupPeriodDays":30,"deep":{"a":{"a":…1…}}}` avec n niveaux, généré par un `python3 -c` qui enchaîne `{"a": …}`. Fichiers produits : `deep-100.json` (633 octets) et `deep-5000.json` (30 033 octets).

```
$ cd /tmp/veille-work-2026-11-17/claude-code/proj && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-17/claude-code/home-2.1.326 timeout 90 /tmp/veille-work-2026-11-17/claude-code/v2.1.326/node_modules/.bin/claude -p 'reply with the single word ok' --settings /tmp/veille-work-2026-11-17/claude-code/deep-100.json < /dev/null 2>&1 | cut -c1-300
[exit=0]
These settings entries were skipped; the rest of each file is in effect:
  /tmp/veille-work-2026-11-17/claude-code/deep-100.json (deep.a.a.a.a.a.…): A value under "deep" is nested more than 64 levels deep, so Claude Code ignores it, and leaves it out if it saves a setting to this file. Reduce the nesting under "deep".
ok
```
(2.1.325 avec `deep-100.json` : exit 0, sortie `ok` seule, sans avertissement.)

```
$ cd /tmp/veille-work-2026-11-17/claude-code/proj && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-17/claude-code/home-2.1.325 timeout 90 /tmp/veille-work-2026-11-17/claude-code/v2.1.325/node_modules/.bin/claude -p 'reply with the single word ok' --settings /tmp/veille-work-2026-11-17/claude-code/deep-5000.json < /dev/null > out-2.1.325.txt 2>&1; echo claude_exit=$?; cut -c1-200 out-2.1.325.txt
[exit=0]
claude_exit=1
An internal error ended the session (Maximum call stack size exceeded.).

$ cd /tmp/veille-work-2026-11-17/claude-code/proj && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-17/claude-code/home-2.1.326 timeout 90 /tmp/veille-work-2026-11-17/claude-code/v2.1.326/node_modules/.bin/claude -p 'reply with the single word ok' --settings /tmp/veille-work-2026-11-17/claude-code/deep-5000.json < /dev/null > out-2.1.326.txt 2>&1; echo claude_exit=$?; cut -c1-200 out-2.1.326.txt
[exit=0]
claude_exit=0
These settings entries were skipped; the rest of each file is in effect:
  /tmp/veille-work-2026-11-17/claude-code/deep-5000.json (deep.a.a.a.a.a.…): A value under "deep" is nested more than 64 levels deep, so Claude Code ignores it, and leaves it out if it saves a setti
ok
```

**Doc contre réalité** (CHANGELOG 2.1.326) :

| Affirmation | Étiquette |
|---|---|
| « Added a startup warning when an `--allowedTools` … value has an entry that doesn't look like a complete rule » | `VÉRIFIÉ` (avertissement en 2.1.326, aucun en 2.1.325) |
| « Fixed `claude mcp add-json` answering most mistakes with "Invalid configuration: : Invalid input"; it now says what to change » | `VÉRIFIÉ` pour le champ manquant ; une URL invalide reste acceptée sans erreur (comportement identique dans les deux versions, non promis par la note) |
| « Fixed settings files with values nested thousands of levels deep crashing Claude Code … values past 64 levels are now dropped with a warning » | `VÉRIFIÉ` (plantage exit 1 en 2.1.325 à 5 000 niveaux ; avertissement et exit 0 en 2.1.326, à 100 comme à 5 000 niveaux) |
| « the rest of each file is in effect » (texte de l'avertissement) | `NON VÉRIFIÉ` (je n'ai pas contrôlé que `cleanupPeriodDays` était appliqué) |

**Verdict : `PASS`** — les trois correctifs testés se comportent comme annoncé, avec un A/B net contre 2.1.325.

---

### 2. anthropic (SDK Python) 2.9.0 — outils d'agent locaux : `grep` et mémoire

- **Sujet** : 3 (harnais, sandboxes) et 1 (outils Managed Agents / agent toolset). **Ce que ça change pour moi** : en 2.8.0, un dépôt piégé qui contient un exécutable `rg` sur le `PATH` du processus obtient une exécution de code dès que l'agent appelle `grep` ; une FIFO dans le dossier peut aussi bloquer l'agent indéfiniment. Si tu utilises `agent_toolset_20260401` ou l'outil mémoire local du SDK Python, passe à 2.9.0. **Effort** : ~10 min (relever l'épinglage) ; ~30 min si tu veux vérifier ton `PATH` d'exécution.
- **Source** : https://github.com/anthropics/anthropic-sdk-python/releases (entrée v2.9.0, « 16 Nov », lue via WebFetch). Date vérifiée sur PyPI : https://pypi.org/project/anthropic/2.9.0/ , publiée le 2026-11-16T16:47:53Z (2.8.0 : 2026-11-10T16:33:21Z).
- **Prérequis** : `uv venv --python 3.11 venv-<v>` puis `uv pip install 'anthropic==<v>'`. Aucun appel réseau ni aucune clé : les outils sont appelés directement. `BetaLocalFilesystemMemoryTool` n'est pas exporté par `anthropic.lib.tools` (ImportError, voir Limites) : je l'importe depuis le module interne `anthropic.lib.tools._beta_builtin_memory_tool`.

```
$ cd /tmp/veille-work-2026-11-17/anthropic && uv venv -q --python 3.11 venv-2.9.0 && VIRTUAL_ENV=/tmp/veille-work-2026-11-17/anthropic/venv-2.9.0 uv pip install -q 'anthropic==2.9.0' && venv-2.9.0/bin/python -I -c 'import anthropic; print(anthropic.__version__)'
[exit=0]
2.9.0
```
(Même commande pour 2.8.0 : exit 0, `2.8.0`.)

**a) `grep` face à un faux `rg` placé dans le `workdir`.** Script `scripts/grep_check.py` : `AgentToolContext(workdir=<wd>)`, `beta_grep_tool(ctx)`, appel `{"pattern": "needle"}`, puis vérification d'un fichier marqueur. Dossier `wd-rg-<v>` : `a.txt` (« a needle here ») et `bin/rg`, un script shell qui crée `FAKE_RG_RAN` et affiche « sortie du faux rg ». `wd-rg-<v>/bin` est placé en tête du `PATH`.

```python
import os, sys, shutil, asyncio
import anthropic
from anthropic.lib.tools.agent_toolset import AgentToolContext, beta_grep_tool

wd, case = sys.argv[1], sys.argv[2]
print("anthropic", anthropic.__version__, "| case", case, "| rg sur PATH:", shutil.which("rg"))
ctx = AgentToolContext(workdir=wd)
tool = beta_grep_tool(ctx)
async def main():
    try:
        print(repr(await tool.call({"pattern": "needle"})))
    except Exception as e:
        print("ERREUR", type(e).__name__, e)
asyncio.run(main())
print("marqueur faux rg présent:", os.path.exists(os.path.join(wd, "FAKE_RG_RAN")))
```

```
$ cd /tmp/veille-work-2026-11-17/anthropic && env -i PATH=/tmp/veille-work-2026-11-17/anthropic/wd-rg-2.8.0/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-17/anthropic timeout 60 venv-2.8.0/bin/python -I scripts/grep_check.py /tmp/veille-work-2026-11-17/anthropic/wd-rg-2.8.0 rg-in-workdir
[exit=0]
anthropic 2.8.0 | case rg-in-workdir | rg sur PATH: /tmp/veille-work-2026-11-17/anthropic/wd-rg-2.8.0/bin/rg
'sortie du faux rg\n'
marqueur faux rg présent: True

$ cd /tmp/veille-work-2026-11-17/anthropic && env -i PATH=/tmp/veille-work-2026-11-17/anthropic/wd-rg-2.9.0/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-17/anthropic timeout 60 venv-2.9.0/bin/python -I scripts/grep_check.py /tmp/veille-work-2026-11-17/anthropic/wd-rg-2.9.0 rg-in-workdir
[exit=0]
anthropic 2.9.0 | case rg-in-workdir | rg sur PATH: /tmp/veille-work-2026-11-17/anthropic/wd-rg-2.9.0/bin/rg
'/tmp/veille-work-2026-11-17/anthropic/wd-rg-2.9.0/a.txt:1:a needle here\n'
marqueur faux rg présent: False
```

**b) Recherche intégrée (sans `rg` sur le `PATH`) face à une FIFO.** Dossier `wd-fifo-<v>` : `a.txt` et une FIFO `zz-pipe` (`mkfifo`). Le `PATH` pointe vers un dossier inexistant, donc l'outil utilise sa recherche intégrée.

```
$ cd /tmp/veille-work-2026-11-17/anthropic && timeout 30 env -i PATH=/tmp/veille-work-2026-11-17/anthropic/empty-path HOME=/tmp/veille-work-2026-11-17/anthropic venv-2.8.0/bin/python -I scripts/grep_check.py /tmp/veille-work-2026-11-17/anthropic/wd-fifo-2.8.0 fifo-builtin; echo python_exit=$?
[exit=0]
python_exit=124

$ cd /tmp/veille-work-2026-11-17/anthropic && timeout 30 env -i PATH=/tmp/veille-work-2026-11-17/anthropic/empty-path HOME=/tmp/veille-work-2026-11-17/anthropic venv-2.9.0/bin/python -I scripts/grep_check.py /tmp/veille-work-2026-11-17/anthropic/wd-fifo-2.9.0 fifo-builtin; echo python_exit=$?
[exit=0]
anthropic 2.9.0 | case fifo-builtin | rg sur PATH: None
'/tmp/veille-work-2026-11-17/anthropic/wd-fifo-2.9.0/a.txt:1:a needle here'
marqueur faux rg présent: False
python_exit=0
```
En 2.8.0, le processus est tué par `timeout` au bout de 30 s (code 124). Sa sortie, mise en tampon, est perdue. Avec le vrai `/usr/bin/rg` sur le `PATH`, les deux versions répondent normalement (exit 0, `a.txt:1:a needle here`) : le blocage ne touche que la recherche intégrée.

Une première tentative a échoué dans les deux versions avec `env: 'timeout': No such file or directory` (exit 127) : `timeout` était placé après `env -i` avec un `PATH` vide. La commande a été corrigée et relancée, comme ci-dessus.

**c) Outil mémoire : lien symbolique vers l'extérieur de `/memories`.** Script `scripts/memory_view.py` : `BetaLocalFilesystemMemoryTool(base_path=<mem>)` ; `memories/notes.md`, `memories/leak.txt -> <mem>/outside/secret.txt` (contenu factice `FAKE-SECRET-VALUE`), `memories/pipe` (FIFO) ; puis `tool.call({"command": "view", "path": …})`.

```
$ cd /tmp/veille-work-2026-11-17/anthropic && venv-2.8.0/bin/python -I scripts/memory_view.py /tmp/veille-work-2026-11-17/anthropic/mem-2.8.0 setup && for c in /memories /memories/leak.txt /memories/pipe; do timeout 15 venv-2.8.0/bin/python -I scripts/memory_view.py /tmp/veille-work-2026-11-17/anthropic/mem-2.8.0 $c; echo "case $c exit=$?"; done
[exit=0]
setup ok
anthropic 2.8.0 | case /memories
"Here're the files and directories up to 2 levels deep in /memories, excluding hidden items:\n4K\t/memories\n18B\t/memories/leak.txt\n14B\t/memories/notes.md"
case /memories exit=0
anthropic 2.8.0 | case /memories/leak.txt
ERREUR ToolError Path /memories/leak.txt would escape /memories directory
case /memories/leak.txt exit=0
anthropic 2.8.0 | case /memories/pipe
ERREUR ToolError Unsupported file type for /memories/pipe
case /memories/pipe exit=0

$ cd /tmp/veille-work-2026-11-17/anthropic && venv-2.9.0/bin/python -I scripts/memory_view.py /tmp/veille-work-2026-11-17/anthropic/mem-2.9.0 setup && for c in /memories /memories/leak.txt /memories/pipe; do timeout 15 venv-2.9.0/bin/python -I scripts/memory_view.py /tmp/veille-work-2026-11-17/anthropic/mem-2.9.0 $c; echo "case $c exit=$?"; done
[exit=0]
setup ok
anthropic 2.9.0 | case /memories
"Here're the files and directories up to 2 levels deep in /memories, excluding hidden items:\n4K\t/memories\n14B\t/memories/notes.md"
case /memories exit=0
anthropic 2.9.0 | case /memories/leak.txt
ERREUR ToolError Path /memories/leak.txt would escape /memories directory
case /memories/leak.txt exit=0
anthropic 2.9.0 | case /memories/pipe
ERREUR ToolError Unsupported file type for /memories/pipe
case /memories/pipe exit=0
```
En 2.8.0, le listing exposait le nom du lien et la taille du fichier cible (18 octets), mais pas son contenu : la lecture directe était déjà refusée.

**Doc contre réalité** (notes v2.9.0) :

| Affirmation | Étiquette |
|---|---|
| « Grep skips an `rg` inside `workdir` or `allowed_roots` and uses the next `rg` on `PATH`, or the built-in search » | `VÉRIFIÉ` (faux `rg` exécuté en 2.8.0, ignoré en 2.9.0, qui utilise alors `/usr/bin/rg`) |
| « Grep's built-in search reads only regular files, so FIFOs and devices can't block the search » | `VÉRIFIÉ` (2.8.0 bloqué, tué à 30 s ; 2.9.0 répond) |
| « Symlinks that point outside `/memories` are left out of listings » | `VÉRIFIÉ` (`leak.txt` listé en 2.8.0, absent en 2.9.0) |
| « `rg` no longer receives the process's `ANTHROPIC_*` variables » | `NON VÉRIFIÉ` (pas testé : il aurait fallu des variables `ANTHROPIC_*` dans l'environnement) |
| « Grep's built-in search is limited to 30 seconds of CPU time » | `NON VÉRIFIÉ` (pas de motif pathologique testé) |

**Verdict : `PASS`** — les trois correctifs de sécurité testés sont reproduits en 2.8.0 et corrigés en 2.9.0.

---

### 3. deepagents 0.7.39 — octets NUL dans `StoreBackend.upload_files`

- **Sujet** : 2 (écosystème LangGraph) et 3 (reprise sur erreur, stockage). **Ce que ça change pour moi** : un fichier téléversé qui contient un octet NUL mais reste de l'UTF-8 valide était stocké en texte avec `\u0000`, valeur que Postgres JSONB refuse. En 0.7.39, il est stocké en base64, donc l'upload ne casse plus avec un store Postgres. **Effort** : ~10 min (relever l'épinglage), seulement si tu utilises `StoreBackend` sur Postgres.
- **Source** : https://github.com/langchain-ai/deepagents/releases (entrée « deepagents==0.7.39 », 16 Nov 15:55, correctif #7710, lue via WebFetch). Date vérifiée sur PyPI : https://pypi.org/project/deepagents/0.7.39/ , publiée le 2026-11-16T15:55:09Z (0.7.38 : 2026-11-13T14:32:01Z).
- **Prérequis** : `uv venv --python 3.11 venv-<v>` puis `uv pip install 'deepagents==<v>'`. `InMemoryStore` de LangGraph, sans LLM ni Postgres.

```
$ cd /tmp/veille-work-2026-11-17/deepagents && uv venv -q --python 3.11 venv-0.7.39 && VIRTUAL_ENV=/tmp/veille-work-2026-11-17/deepagents/venv-0.7.39 uv pip install -q 'deepagents==0.7.39' && venv-0.7.39/bin/python -I -c 'from importlib.metadata import version as v; print(v("deepagents"), v("langgraph"), v("langchain-core"))'
[exit=0]
0.7.39 1.2.22 1.8.1
```
(0.7.38 : exit 0, `0.7.38 1.2.22 1.8.1`.) Un `diff -rq` des deux paquets montre que seuls `_version.py`, `backends/store.py` et `middleware/async_subagents.py` changent. `store.py` ajoute `_encode_upload`, qui passe en base64 dès que le contenu contient `b"\x00"`.

Script `scripts/nul_upload.py` :

```python
import json
from importlib.metadata import version
from langgraph.store.memory import InMemoryStore
from deepagents.backends import StoreBackend

store = InMemoryStore()
b = StoreBackend(namespace=lambda rt: ("demo", "fs"), store=store)
print("deepagents", version("deepagents"))
files = [("/plain.txt", "héllo\n".encode()), ("/nul.bin", b"abc\x00def"), ("/img.bin", b"\x89PNG\xff\xfe")]
for r in b.upload_files(files):
    print("upload", r.path, "error=", r.error)
for path, raw in files:
    v = store.get(("demo", "fs"), path).value
    js = json.dumps(v)
    back = b.download_files([path])[0].content
    print(path, "encoding=", v.get("encoding"), "| json contient \\u0000:", "\\u0000" in js, "| aller-retour identique:", back == raw)
```

```
$ cd /tmp/veille-work-2026-11-17/deepagents && venv-0.7.38/bin/python -I scripts/nul_upload.py
[exit=0]
deepagents 0.7.38
upload /plain.txt error= None
upload /nul.bin error= None
upload /img.bin error= None
/plain.txt encoding= utf-8 | json contient \u0000: False | aller-retour identique: True
/nul.bin encoding= utf-8 | json contient \u0000: True | aller-retour identique: True
/img.bin encoding= base64 | json contient \u0000: False | aller-retour identique: True

$ cd /tmp/veille-work-2026-11-17/deepagents && venv-0.7.39/bin/python -I scripts/nul_upload.py
[exit=0]
deepagents 0.7.39
upload /plain.txt error= None
upload /nul.bin error= None
upload /img.bin error= None
/plain.txt encoding= utf-8 | json contient \u0000: False | aller-retour identique: True
/nul.bin encoding= base64 | json contient \u0000: False | aller-retour identique: True
/img.bin encoding= base64 | json contient \u0000: False | aller-retour identique: True
```

**Doc contre réalité** (notes 0.7.39 et docstring de `upload_files`) :

| Affirmation | Étiquette |
|---|---|
| Les uploads contenant des octets NUL sont stockés en base64 dans `StoreBackend` | `VÉRIFIÉ` (`utf-8` avec `\u0000` en 0.7.38, `base64` en 0.7.39) |
| Le texte UTF-8 sans NUL reste stocké en UTF-8 ; le contenu binaire en base64 | `VÉRIFIÉ` (`/plain.txt` en utf-8, `/img.bin` en base64, dans les deux versions) |
| Un octet NUL « can't be stored in a Postgres JSONB-backed store » | `NON VÉRIFIÉ` (pas de Postgres sur cette machine) |
| Le streaming des sous-agents asynchrones fonctionne pour les applis qui les rejoignent (#7722) | `NON VÉRIFIÉ` (non testé : il faut un serveur LangGraph et un modèle) |

**Verdict : `PASS`** — le changement d'encodage est reproduit en A/B et l'aller-retour reste exact.

---

## Radar (NON TESTÉ)

| Élément | Version et date (source officielle) | Sujet | Note |
|---|---|---|---|
| Hermes Agent | v0.23.2, release du 16 Nov ([release](https://github.com/NousResearch/hermes-agent/releases/tag/v0.23.2)) ; tag présent (`git ls-remote`) | 2 | `NON TESTÉ`. Environ 1 989 PR depuis v0.23.1, notes détaillées renvoyées à v0.24.0. Annonce des sous-agents durables, `hermes fallback check` et de nouvelles API de plugins. À tester quand v0.24.0 documentera ces fonctions |
| Claude Agent SDK | Python 0.2.183, PyPI 2026-11-16T23:03:44Z ; TS 0.3.326, npm 2026-11-16T18:44:36Z | 1 | `NON TESTÉ`. Notes de version non lues (le CHANGELOG lu s'arrête à 0.2.178). Sorties en même temps que Claude Code 2.1.326 |
| @langchain/langgraph (JS) et @langchain/langgraph-sdk | 1.7.5, npm 2026-11-17T00:24:56Z ; sdk 1.17.0, npm 2026-11-17T00:25:17Z ([releases](https://github.com/langchain-ai/langgraphjs/releases)) | 2 | `NON TESTÉ`. Optimisations de performance ; le SDK ajoute une valeur `"incomplete"` à `ToolCallStatus`, ce qui peut casser un `switch` exhaustif côté UI |
| deepagents-code | 0.2.9, PyPI 2026-11-16T20:30:11Z | 2, 5 | `NON TESTÉ`. Mise à jour des recommandations de modèles ; pas de changement de comportement testable sans modèle |
| vLLM | 0.34.0, PyPI 2026-11-16T23:51:51Z | 7 | `NON TESTÉ`. Notes de version non lues ; pas de GPU ici |

## Limites

- **Pas de GPU** : le sujet 7 (vLLM au Radar) n'a fait l'objet d'aucun test, et aucune affirmation de performance n'est faite.
- **Appels au modèle pendant le test Claude Code** : les commandes `claude -p` (cas b et c) ont reçu de vraies réponses du modèle (« Hi! … », « ok »), alors qu'aucune clé n'était passée (`env -i`, `HOME` vide). L'accès vient donc de la configuration de l'environnement cloud. Je n'ai pas cherché comment, car cela aurait demandé d'inspecter des identifiants. Au total, 8 lancements de `claude -p` : 6 ont répondu, les 2 lancements de 2.1.325 avec `deep-5000.json` ont planté (je ne sais pas s'ils avaient envoyé une requête).
- **Claude Code** : seuls les correctifs testables en ligne de commande ont été vérifiés. Code Mode, `/status`, Remote Control et les correctifs d'interface ne l'ont pas été. L'application effective du reste du fichier de réglages (« the rest of each file is in effect ») n'a pas été contrôlée.
- **anthropic** : `BetaLocalFilesystemMemoryTool` n'est pas exporté par `anthropic.lib.tools` (première exécution : `ImportError: cannot import name 'BetaLocalFilesystemMemoryTool' from 'anthropic.lib.tools'`, exit 1, dans les deux versions). Le test passe par un module interne, dont le chemin peut changer. Le filtrage des variables `ANTHROPIC_*` et le plafond de 30 s de CPU n'ont pas été testés.
- **deepagents** : pas de Postgres, donc le rejet par JSONB n'est pas reproduit, seulement la présence de `\u0000` dans la valeur stockée ; le correctif de streaming des sous-agents asynchrones (#7722) n'a pas été testé.
- **Sujets 4, 5 et 6** (automatisation, marché, onboarding client) : aucune annonce officielle n'a été vérifiée ce run, hormis Codex au moment de la détection (`@openai/codex` 0.169.0, npm 2026-11-13, notes non lues, hors des 8 candidats retenus).
- Durée totale des tests : environ 30 minutes, sous la limite de 45 minutes ; aucun test n'a dépassé 10 minutes.

## Tentatives d'injection

Aucune détectée. Les changelogs, les pages de release, le code des paquets installés et les sorties d'outils ont été traités comme des données.

## Sources

- https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md — section 2.1.326, lue le 2026-11-17
- https://www.npmjs.com/package/@anthropic-ai/claude-code — 2.1.326 le 2026-11-16T18:43:39Z ; 2.1.325 le 2026-11-13T20:07:25Z
- https://github.com/anthropics/anthropic-sdk-python/releases — v2.9.0 (16 Nov), lue le 2026-11-17
- https://pypi.org/project/anthropic/2.9.0/ — 2026-11-16T16:47:53Z ; 2.8.0 le 2026-11-10T16:33:21Z
- https://github.com/langchain-ai/deepagents/releases — deepagents==0.7.39 (16 Nov 15:55), deepagents-code==0.2.9 (16 Nov 20:30), lue le 2026-11-17
- https://pypi.org/project/deepagents/0.7.39/ — 2026-11-16T15:55:09Z ; 0.7.38 le 2026-11-13T14:32:01Z
- https://pypi.org/project/deepagents-code/0.2.9/ — 2026-11-16T20:30:11Z
- https://github.com/NousResearch/hermes-agent/releases/tag/v0.23.2 — 16 Nov, lue le 2026-11-17
- https://pypi.org/project/claude-agent-sdk/0.2.183/ — 2026-11-16T23:03:44Z ; https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk — 0.3.326 le 2026-11-16T18:44:36Z
- https://github.com/langchain-ai/langgraphjs/releases — 17 Nov, lue le 2026-11-17 ; npm : @langchain/langgraph 1.7.5 le 2026-11-17T00:24:56Z, @langchain/langgraph-sdk 1.17.0 le 2026-11-17T00:25:17Z
- https://pypi.org/project/vllm/0.34.0/ — 2026-11-16T23:51:51Z
