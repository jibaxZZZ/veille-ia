# Veille IA — 2026-11-16

## TL;DR

- **Run du 2026-11-16** (fenêtre du 2026-11-09 au 2026-11-16) : **8 éléments détectés, 3 testés (3 PASS), 5 au Radar.** Rien de nouveau côté Claude Code / Agent SDK depuis 2.1.325 / 0.2.182.
- **deepagents 0.7.38 : PASS.** Un lien symbolique placé dans un dossier autorisé n'expose plus, via `ls`/`glob`, un fichier protégé par une règle `interrupt` (A/B contre 0.7.37). Mets à jour si tu utilises `permissions=`.
- **FastMCP 4.2.0 : PASS.** Un serveur MCP sert un dossier de skills ; `Client.read_skill()` les récupère avec contrôle des empreintes et `to_directory()` les installe à l'identique. L'ancienne API 4.1 marche encore, avec un avertissement : elle disparaît en 4.3.
- **MCP Inspector 2.15.0 : PASS (test unitaire hors réseau).** Le garde de fetch bloque désormais les adresses de métadonnées 100.100.100.200 et 192.0.0.192, que 2.14.0 laissait passer. Mets Inspector à jour.
- Aucune tentative d'injection relevée. Pas de GPU, donc aucun test de performance. Un test réseau vers les adresses de métadonnées a été refusé par le garde-fou de la session (voir Limites).

## Contexte et choix faits sans validation humaine

- Répertoire de travail : `/tmp/veille-work-2026-11-16/<élément>/`. Toutes les commandes passent par un wrapper `bin/run`, qui consigne la commande, le code de sortie et la sortie (tronquée à 40 lignes) dans `logs/<élément>.log`. Les sorties ci-dessous sont copiées de ces journaux.
- Machine : Linux x86_64, Node v22.23.4, npm 10.9.9, uv (venv Python 3.11.18). Pas de GPU.
- **Détection** : l'API GitHub (`api.github.com`) et les pages `github.com` sont bloquées par le proxy de la session (réponse « GitHub access to this repository is not enabled » / HTTP 403). Les versions et les dates viennent donc des registres officiels (PyPI JSON, `npm view … time`) et de `git ls-remote`. Les notes de version ont été lues via WebFetch sur les pages de release GitHub.
- **Sélection** : j'ai retenu les 3 éléments testables sans clé API et liés aux sujets 3 et 4 (permissions d'agents, MCP). MCP Inspector était au Radar le 2026-11-15 (`NON TESTÉ`), il n'est pas dans `tested.md` : ce n'est pas un doublon (B5). Aucun des 3 n'apparaît dans `tested.md`.

---

## Tests

### 1. deepagents 0.7.38 — liens symboliques hors du périmètre approuvé

- **Sujet** : 3 (harnais : permissions, sandboxes) et 2 (écosystème LangGraph). **Ce que ça change pour moi** : avec 0.7.37, un agent qui liste un dossier autorisé voit, à travers un lien symbolique, un fichier qu'une règle `interrupt` réservait à une approbation humaine ; en 0.7.38, ce fichier est retiré des résultats. Si tu utilises les `permissions` de deepagents comme garde-fou, passe en 0.7.38. **Effort** : ~10 min (relever l'épinglage).
- **Source** : https://github.com/langchain-ai/deepagents/releases (entrée « deepagents 0.7.38 », 13 Nov). Date vérifiée sur PyPI : https://pypi.org/project/deepagents/0.7.38/ , publiée le 2026-11-13T14:32:01Z (0.7.37 : 2026-11-12T20:03:32Z).
- **Prérequis** : `uv venv --python 3.11 venv-<v>` puis `uv pip install 'deepagents==<v>'`. Aucun LLM ni aucune clé. Les outils `ls`/`glob`/`grep` du `FilesystemMiddleware` sont appelés directement, avec un `ToolRuntime` construit à la main.

```
$ cd /tmp/veille-work-2026-11-16/deepagents && uv venv -q --python 3.11 venv-0.7.38 && VIRTUAL_ENV=/tmp/veille-work-2026-11-16/deepagents/venv-0.7.38 uv pip install -q 'deepagents==0.7.38' && venv-0.7.38/bin/python -I -c 'from importlib.metadata import version as v; print(v("deepagents"), v("langgraph"), v("langchain-core"))'
[exit=0]
0.7.38 1.2.22 1.8.1
```
(Même commande pour 0.7.37 : exit 0, `0.7.37 1.2.22 1.8.1`.)

```
$ cd /tmp/veille-work-2026-11-16/deepagents && diff -rq -x '*.pyc' -x __pycache__ venv-0.7.37/lib/python3.11/site-packages/deepagents venv-0.7.38/lib/python3.11/site-packages/deepagents
[exit=1]
Files venv-0.7.37/lib/python3.11/site-packages/deepagents/_version.py and venv-0.7.38/lib/python3.11/site-packages/deepagents/_version.py differ
Files venv-0.7.37/lib/python3.11/site-packages/deepagents/middleware/filesystem.py and venv-0.7.38/lib/python3.11/site-packages/deepagents/middleware/filesystem.py differ
```
(exit 1 = des différences existent.) Le diff détaillé de `filesystem.py`, lu mais non reproduit ici, ajoute un paramètre `scope` et une fonction `_bulk_scope`.

Script `scripts/symlink_scope.py` : `FilesystemBackend(root_dir=<fs>, virtual_mode=True)`, une règle `FilesystemPermission(operations=["read"], paths=["/secrets/**"], mode="interrupt")`, un fichier `/secrets/key.txt` (contenu factice `FAKE-SECRET-VALUE`), et deux liens dans `/work` : `link -> /secrets` (dossier) et `key-link.txt -> /secrets/key.txt` (fichier).

```python
import sys, os, shutil
from importlib.metadata import version
from deepagents.backends import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemMiddleware, FilesystemPermission
from langchain.tools import ToolRuntime

root = sys.argv[1]
shutil.rmtree(root, ignore_errors=True)
os.makedirs(f"{root}/work"); os.makedirs(f"{root}/secrets")
open(f"{root}/work/notes.txt","w").write("public notes\n")
open(f"{root}/secrets/key.txt","w").write("FAKE-SECRET-VALUE\n")
os.symlink(f"{root}/secrets", f"{root}/work/link")
os.symlink(f"{root}/secrets/key.txt", f"{root}/work/key-link.txt")

backend = FilesystemBackend(root_dir=root, virtual_mode=True)
perms = [FilesystemPermission(operations=["read"], paths=["/secrets/**"], mode="interrupt")]
mw = FilesystemMiddleware(backend=backend, permissions=perms)
tools = {t.name: t for t in mw.tools}
rt = ToolRuntime(state={"messages": [], "files": {}}, context=None, config={}, stream_writer=lambda *_: None, tool_call_id="t1", store=None)
print("deepagents", version("deepagents"))
for name, args in [("ls", {"path": "/work/link"}), ("ls", {"path": "/work"}), ("glob", {"pattern": "**/*.txt", "path": "/work"}), ("grep", {"pattern": "FAKE-SECRET", "path": "/work"})]:
    msg = tools[name].func(runtime=rt, **args)
    print(f"{name}{args} ->", repr(msg.content))
```

```
$ cd /tmp/veille-work-2026-11-16/deepagents && venv-0.7.37/bin/python -I scripts/symlink_scope.py /tmp/veille-work-2026-11-16/deepagents/fs-0.7.37
[exit=0]
deepagents 0.7.37
ls{'path': '/work/link'} -> "['/secrets/key.txt']"
ls{'path': '/work'} -> "['/work/key-link.txt', '/work/link/', '/work/notes.txt']"
glob{'pattern': '**/*.txt', 'path': '/work'} -> "['/work/key-link.txt', '/work/notes.txt']"
grep{'pattern': 'FAKE-SECRET', 'path': '/work'} -> 'No matches found'

$ cd /tmp/veille-work-2026-11-16/deepagents && venv-0.7.38/bin/python -I scripts/symlink_scope.py /tmp/veille-work-2026-11-16/deepagents/fs-0.7.38
[exit=0]
deepagents 0.7.38
ls{'path': '/work/link'} -> "['/secrets/key.txt']"
ls{'path': '/work'} -> "['/work/notes.txt']"
glob{'pattern': '**/*.txt', 'path': '/work'} -> "['/work/notes.txt']"
grep{'pattern': 'FAKE-SECRET', 'path': '/work'} -> 'No matches found'
```

Contrôle de `grep` au niveau du backend (`scripts/grep_check.py`, appelle `FilesystemBackend.grep(pattern, path="/work")`) :

```
$ cd /tmp/veille-work-2026-11-16/deepagents && venv-0.7.38/bin/python -I scripts/grep_check.py /tmp/veille-work-2026-11-16/deepagents/fs-0.7.38
[exit=0]
public -> [{'path': '/work/notes.txt', 'line': 1, 'text': 'public notes'}] None
FAKE-SECRET -> [] None
```
(0.7.37 : exit 0, sortie identique.) Le `grep` de ce backend ne suit pas les liens, ni en 0.7.37 ni en 0.7.38 : il n'y avait pas de fuite à corriger dans ce cas.

**Doc contre réalité** (notes 0.7.38 : « Exclude results from `ls`, `grep`, and `glob` when a symlink resolves outside the approved search scope ») :

| Affirmation | Étiquette |
|---|---|
| `ls` exclut une entrée dont le lien sort du périmètre approuvé | `VÉRIFIÉ` (`/work/key-link.txt` et `/work/link/` listés en 0.7.37, absents en 0.7.38) |
| `glob` exclut ces résultats | `VÉRIFIÉ` (`/work/key-link.txt` présent en 0.7.37, absent en 0.7.38) |
| `grep` exclut ces résultats | `NON VÉRIFIÉ` (le `grep` de `FilesystemBackend` ne suit pas les liens dans mon cas, même en 0.7.37 ; je n'ai pas testé d'autre backend) |
| Un `ls` explicite sur le lien (`/work/link`) reste possible, car l'approbation couvre la cible résolue | `VÉRIFIÉ` en tant que comportement observé (identique dans les deux versions) ; l'étape d'approbation humaine elle-même (HITL) est `NON VÉRIFIÉ` (pas d'agent ni de modèle lancés) |

**Verdict : `PASS`** — la fuite par lien symbolique est reproduite en 0.7.37 et corrigée en 0.7.38 pour `ls` et `glob`.

---

### 2. FastMCP 4.2.0 — skills servies par le serveur MCP

- **Sujet** : 4 (MCP et connecteurs) et 1 (skills Claude Code). **Ce que ça change pour moi** : tu peux publier tes skills (format `SKILL.md`) depuis un seul serveur MCP, et chaque agent client les récupère avec contrôle de taille et de SHA-256 au lieu de copier des dossiers à la main. Si tu utilises déjà l'API skills de 4.1, prévois la migration avant 4.3. **Effort** : ~1 h pour un premier serveur de skills ; ~15 min pour migrer un import 4.1.
- **Source** : https://github.com/PrefectHQ/fastmcp/releases/tag/v4.2.0 (page lue via WebFetch : « 13 Nov 17:07 »). Date vérifiée sur PyPI : https://pypi.org/project/fastmcp/4.2.0/ , publiée le 2026-11-13T17:08:59Z. Référence A/B : 4.1.8 (PyPI, 2026-11-10T20:44:54Z).
- **Prérequis** : `uv venv --python 3.11 venv-<v>` puis `uv pip install 'fastmcp==<v>'`. Le client se connecte au serveur en mémoire (`Client(mcp)`), sans réseau.

```
$ cd /tmp/veille-work-2026-11-16/fastmcp && uv venv -q --python 3.11 venv-4.2.0 && VIRTUAL_ENV=/tmp/veille-work-2026-11-16/fastmcp/venv-4.2.0 uv pip install -q 'fastmcp==4.2.0' && venv-4.2.0/bin/python -I -c 'from importlib.metadata import version as v; print(v("fastmcp"), v("mcp"))'
[exit=0]
4.2.0 2.3.0
```
(4.1.8 : exit 0, `4.1.8 2.3.0`.)

**a) Quickstart** — `scripts/skills_quickstart.py` crée `skills/hello-world/` (`SKILL.md` avec `name: hello-world` et une `description`, plus `scripts/hello.sh`), le sert avec `fastmcp.skills.provider.SkillsDirectoryProvider`, puis appelle `list_resources()`, `read_skill("skill://hello-world/SKILL.md")`, `skill.to_directory(<base>/installed/hello-world)` (deux fois) et compare les octets avec `filecmp.cmp(shallow=False)`.

```
$ cd /tmp/veille-work-2026-11-16/fastmcp && venv-4.2.0/bin/python -I scripts/skills_quickstart.py /tmp/veille-work-2026-11-16/fastmcp/case-qs
[exit=0]
fastmcp 4.2.0
resources: ['skill://hello-world/SKILL.md', 'skill://hello-world/_manifest', 'skill://hello-world/scripts/hello.sh']
read_skill name: hello-world
installed to installed/hello-world | identical bytes: True
second to_directory: FileExistsError

$ cd /tmp/veille-work-2026-11-16/fastmcp && venv-4.1.8/bin/python -I scripts/skills_quickstart.py /tmp/veille-work-2026-11-16/fastmcp/case-qs-418
[exit=1]
Traceback (most recent call last):
  File "/tmp/veille-work-2026-11-16/fastmcp/scripts/skills_quickstart.py", line 5, in <module>
    from fastmcp.skills.provider import SkillsDirectoryProvider
ModuleNotFoundError: No module named 'fastmcp.skills.provider'
```

**b) Cas limite : dossier invalide** — `scripts/skills_invalid.py` crée `skills/bad-folder/SKILL.md` avec `name: other-name` et construit le provider.

```
$ cd /tmp/veille-work-2026-11-16/fastmcp && venv-4.2.0/bin/python -I scripts/skills_invalid.py /tmp/veille-work-2026-11-16/fastmcp/case-invalid
[exit=0]
ValueError : 1 skill folder(s) are not valid Agent Skills (https://agentskills.io/specification):
- /tmp/veille-work-2026-11-16/fastmcp/case-invalid/skills/bad-folder: Skill folder 'bad-folder' must match its SKILL.md name 'other-name'. Fix: start SKILL.md with '---\nname: bad-folder\ndescription: <what it does and when to use it>\n---'
```
(Exit 0 parce que le script attrape l'exception et l'affiche.)

**c) Compatibilité de l'API 4.1** — `scripts/skills_legacy.py` importe `from fastmcp.server.providers.skills import SkillsDirectoryProvider` (API 4.1), enregistre les avertissements, puis lit `skill://hello-world/SKILL.md`.

```
$ cd /tmp/veille-work-2026-11-16/fastmcp && venv-4.1.8/bin/python -I scripts/skills_legacy.py /tmp/veille-work-2026-11-16/fastmcp/case-legacy-4.1.8
[exit=0]
fastmcp 4.1.8 | warnings: []
resources: ['skill://hello-world/SKILL.md', 'skill://hello-world/_manifest']
SKILL.md readable: True

$ cd /tmp/veille-work-2026-11-16/fastmcp && venv-4.2.0/bin/python -I scripts/skills_legacy.py /tmp/veille-work-2026-11-16/fastmcp/case-legacy-4.2.0
[exit=0]
fastmcp 4.2.0 | warnings: ['FastMCPDeprecationWarning: `SkillsDirectoryProvider` is deprecated and will be removed in FastMCP 4.3. Replace it with `from fastmcp.skills.provider import SkillsDirectoryProvid']
resources: ['skill://hello-world/SKILL.md', 'skill://hello-world/_manifest']
SKILL.md readable: True
```
(Le message d'avertissement est tronqué à 150 caractères par mon script.)

**d) Contrôle de taille et d'empreinte** — `scripts/skills_tamper.py` sert la même skill, puis remplace côté client la méthode interne `Client._read_skill_file` pour altérer `scripts/hello.sh` à la réception. Cela simule un fichier modifié en transit ou par un proxy : un octet ajouté (« size »), puis `hello` remplacé par `HELLO`, même taille (« digest »).

```python
async with Client(mcp) as c:
    orig = c._read_skill_file
    for label, alter in [("size", lambda b: b + b"X"), ("digest", lambda b: b.replace(b"hello", b"HELLO"))]:
        async def patched(uri, _a=alter):
            data = await orig(uri)
            return _a(data) if uri.endswith("hello.sh") else data
        c._read_skill_file = patched
        try:
            await c.read_skill("skill://hello-world/SKILL.md"); print(label, "-> accepted")
        except Exception as e:
            print(label, "->", type(e).__name__, ":", e)
```

```
$ cd /tmp/veille-work-2026-11-16/fastmcp && venv-4.2.0/bin/python -I scripts/skills_tamper.py /tmp/veille-work-2026-11-16/fastmcp/case-tamper
[exit=0]
size -> ValueError : Skill file 'scripts/hello.sh' is 22 bytes; the manifest promised 21
digest -> ValueError : Skill file 'scripts/hello.sh' does not match its manifest digest
```

**e) Python minimal**

```
$ grep -i requires-python /tmp/veille-work-2026-11-16/fastmcp/venv-4.1.8/lib/python3.11/site-packages/fastmcp-4.1.8.dist-info/METADATA /tmp/veille-work-2026-11-16/fastmcp/venv-4.2.0/lib/python3.11/site-packages/fastmcp-4.2.0.dist-info/METADATA
[exit=0]
/tmp/veille-work-2026-11-16/fastmcp/venv-4.1.8/lib/python3.11/site-packages/fastmcp-4.1.8.dist-info/METADATA:Requires-Python: >=3.10
/tmp/veille-work-2026-11-16/fastmcp/venv-4.2.0/lib/python3.11/site-packages/fastmcp-4.2.0.dist-info/METADATA:Requires-Python: >=3.11
```

**Doc contre réalité** (notes de v4.2.0) :

| Affirmation | Étiquette |
|---|---|
| Les skills sont lisibles comme des ressources MCP ordinaires | `VÉRIFIÉ` (`skill://hello-world/SKILL.md`, `scripts/hello.sh` et `_manifest` listés) |
| `Client.read_skill()` vérifie la taille et l'empreinte SHA-256 de chaque fichier | `VÉRIFIÉ` (test d : un fichier altéré est rejeté par `ValueError`, pour la taille comme pour l'empreinte ; l'altération est simulée côté client, pas par un vrai serveur malveillant) |
| `to_directory()` installe la skill localement | `VÉRIFIÉ` (octets identiques ; une 2ᵉ installation est refusée par `FileExistsError` sans `overwrite`) |
| Un dossier invalide fait échouer le démarrage avec une erreur qui indique la correction (docstring du provider) | `VÉRIFIÉ` |
| L'API skills 4.1 reste utilisable mais émet un avertissement ; retrait en 4.3 | `VÉRIFIÉ` (avertissement `FastMCPDeprecationWarning` en 4.2.0, absent en 4.1.8 ; lecture OK dans les deux). Le retrait en 4.3 est une annonce, `NON VÉRIFIÉ` |
| Python 3.11 ou plus est requis | `VÉRIFIÉ` (`Requires-Python: >=3.11`) |
| `skills/list` pour les clients qui négocient l'extension expérimentale Skills | `NON VÉRIFIÉ` (non testé) |
| ~11 correctifs de sécurité (SSRF/DNS, OAuth, sandbox CodeMode…) | `NON VÉRIFIÉ` (non testés) |

**Verdict : `PASS`** — la distribution de skills par MCP fonctionne de bout en bout en local, et la migration depuis 4.1 est progressive.

---

### 3. MCP Inspector 2.15.0 — garde de fetch contre les adresses de métadonnées cloud

- **Sujet** : 3 (harnais, sécurité) et 4 (MCP). **Ce que ça change pour moi** : en 2.14.0, le backend web d'Inspector (proxy `/api/fetch`, découverte OAuth) pouvait atteindre les points de métadonnées Alibaba Cloud (100.100.100.200) et 192.0.0.192 ; un serveur MCP malveillant pouvait s'en servir pour lire des identifiants sur une VM cloud. Mets à jour si tu lances Inspector sur une machine cloud. **Effort** : ~5 min (`npx @modelcontextprotocol/inspector@2.15.0`).
- **Source** : https://github.com/modelcontextprotocol/inspector/releases/tag/2.15.0 (page lue via WebFetch : publiée le « 12 Nov 00:46 »). Dates npm (`npm view @modelcontextprotocol/inspector time`) : 2.15.0 le 2026-11-12T01:24:25Z, 2.14.0 le 2026-11-05T00:17:31Z.
- **Méthode** : installation npm avec `--ignore-scripts`. Mon test de bout en bout (lancer le backend web en local et envoyer à `/api/fetch` des URL vers les adresses de métadonnées) a été **refusé par le garde-fou de la session** avant toute exécution : avec 2.14.0, la requête serait réellement partie vers ces adresses. Repli sans réseau : `scripts/guard_check.mjs` extrait du bundle `clients/web/build/index.js` le code compris entre `const METADATA_IPV4_ADDRESSES` (ou `function isBlockedAddress(` en 2.14.0) et `function assertNoneBlocked(`, l'évalue avec `isIP` de `node:net`, puis l'appelle sur une liste d'adresses.

```
$ cd /tmp/veille-work-2026-11-16/inspector && npm install --prefix ./v2.15.0 --no-audit --no-fund --ignore-scripts @modelcontextprotocol/inspector@2.15.0 2>&1 | tail -2 && npm ls --prefix ./v2.15.0 @modelcontextprotocol/inspector 2>&1 | head -3
[exit=0]

added 120 packages in 7s
v2.15.0@ /tmp/veille-work-2026-11-16/inspector/v2.15.0
`-- @modelcontextprotocol/inspector@2.15.0

$ cd /tmp/veille-work-2026-11-16/inspector && env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/veille-work-2026-11-16/inspector/home node v2.15.0/node_modules/@modelcontextprotocol/inspector/clients/launcher/build/index.js --version
[exit=0]
2.15.0
```
(2.14.0 : mêmes commandes, exit 0, `added 120 packages in 14s` et `2.14.0`.)

```javascript
// scripts/guard_check.mjs
import { readFileSync } from "node:fs";
import { isIP } from "node:net";
const file = process.argv[2];
const src = readFileSync(file, "utf8");
const start = src.indexOf("const METADATA_IPV4_ADDRESSES") >= 0 ? src.indexOf("const METADATA_IPV4_ADDRESSES") : src.indexOf("function isBlockedAddress(");
const end = src.indexOf("function assertNoneBlocked(");
const code = src.slice(start, end).replace("/* @__PURE__ */ ", "");
const isBlockedAddress = new Function("isIP", code + "\nreturn isBlockedAddress;")(isIP);
for (const ip of ["169.254.169.254", "100.100.100.200", "192.0.0.192", "::ffff:100.100.100.200", "::ffff:6464:64c8", "fd00:ec2::254", "8.8.8.8", "100.100.100.201", "10.0.0.1"])
  console.log(ip.padEnd(24), isBlockedAddress(ip) ? "BLOQUÉ" : "autorisé");
```

```
$ cd /tmp/veille-work-2026-11-16/inspector && node scripts/guard_check.mjs /tmp/veille-work-2026-11-16/inspector/v2.14.0/node_modules/@modelcontextprotocol/inspector/clients/web/build/index.js
[exit=0]
169.254.169.254          BLOQUÉ
100.100.100.200          autorisé
192.0.0.192              autorisé
::ffff:100.100.100.200   autorisé
::ffff:6464:64c8         autorisé
fd00:ec2::254            BLOQUÉ
8.8.8.8                  autorisé
100.100.100.201          autorisé
10.0.0.1                 autorisé

$ cd /tmp/veille-work-2026-11-16/inspector && node scripts/guard_check.mjs /tmp/veille-work-2026-11-16/inspector/v2.15.0/node_modules/@modelcontextprotocol/inspector/clients/web/build/index.js
[exit=0]
169.254.169.254          BLOQUÉ
100.100.100.200          BLOQUÉ
192.0.0.192              BLOQUÉ
::ffff:100.100.100.200   BLOQUÉ
::ffff:6464:64c8         BLOQUÉ
fd00:ec2::254            BLOQUÉ
8.8.8.8                  autorisé
100.100.100.201          autorisé
10.0.0.1                 autorisé
```
Le bundle 2.15.0 appelle cette fonction depuis `createPinningLookup`, c'est-à-dire sur les adresses résolues par DNS au moment de la connexion (code lu, lignes ~2208-2250 de `clients/web/build/index.js`).

**Doc contre réalité** (notes 2.15.0) :

| Affirmation | Étiquette |
|---|---|
| Le garde de fetch bloque les adresses de métadonnées cloud hors 169.254.0.0/16 | `VÉRIFIÉ` au niveau de la fonction (100.100.100.200, 192.0.0.192 et leurs formes IPv6 mappées bloquées en 2.15.0, autorisées en 2.14.0) |
| Ce blocage protège le proxy `/api/fetch` et la découverte OAuth de bout en bout | `NON VÉRIFIÉ` (test réseau refusé par le garde-fou de la session ; seul le chemin de code a été lu) |
| Les versions 2.0.0 à 2.14.0 sont affectées | `VÉRIFIÉ` pour 2.14.0 seulement ; autres versions `NON VÉRIFIÉ` |
| Plafond du corps de réponse enregistré pour les flux event-stream, aperçu `server.json`, vérification du démon `mcpdo` | `NON VÉRIFIÉ` (non testés) |

**Verdict : `PASS`** — sur le périmètre testé (logique de blocage en A/B). Le test de bout en bout reste à faire.

---

## Radar (NON TESTÉ)

| Élément | Version et date (source officielle) | Sujet | Note |
|---|---|---|---|
| langchain : `ModelRouterMiddleware` et mode auto (beta) | 1.5.0, PyPI 2026-11-11T15:47:07Z ([releases](https://github.com/langchain-ai/langchain/releases)) | 2, 5 | `NON TESTÉ`. Routage entre modèles par middleware : peut réduire le coût d'un agent. Il faut des appels LLM pour l'évaluer |
| langchain-core : fin de Python 3.10, `langsmith_gateway` | 1.8.0, PyPI 2026-11-11T15:21:52Z ; 1.8.1, PyPI 2026-11-15T14:56:58Z ([releases](https://github.com/langchain-ai/langchain/releases)) | 2 | `NON TESTÉ`. Si un projet tourne encore en Python 3.10, il reste bloqué en 1.7.x |
| @langchain/langgraph-sdk (JS) : panneaux de subagents, exécutions durables | 1.16.0, npm 2026-11-12T18:08:11Z ([releases](https://github.com/langchain-ai/langgraphjs/releases)) | 2 | `NON TESTÉ`. Côté UI ; `@langchain/langgraph` 1.7.4 ne fait que monter cette dépendance |
| @google/gemini-cli | 0.68.0, npm 2026-11-10T21:22:49Z | 5 | `NON TESTÉ`. Notes de version non lues ; concurrent des agents de code |
| llama-cpp-python | 0.3.37, PyPI 2026-11-15T09:14:07Z | 7 | `NON TESTÉ`. Inférence locale ; pas de GPU ici |

## Limites

- **Pas de GPU** : le sujet 7 n'a fait l'objet d'aucun test, et aucune affirmation de performance n'est faite.
- **MCP Inspector** : le test de bout en bout de `/api/fetch` vers les adresses de métadonnées a été refusé par le garde-fou de la session (« Unauthorized Access »), avant toute exécution. Seule la fonction de blocage a été testée hors réseau. Deux tentatives intermédiaires ont échoué avec `Cannot find module …/guard_check.mjs` (le dossier `scripts/` n'avait pas été créé, car la commande précédente avait été refusée), puis le test a été relancé.
- **deepagents** : l'approbation humaine (HITL) n'a pas été déclenchée (pas d'agent ni de modèle) ; `grep` n'a pas pu être mis en défaut avec `FilesystemBackend`. Le journal contient aussi une première exécution de `symlink_scope.py`, faite avant l'ajout du lien fichier `key-link.txt` et du cas `ls /work` : elle donnait les mêmes résultats en 0.7.37 et en 0.7.38, car elle ne testait que `ls /work/link`, `glob` et `grep`.
- **FastMCP** : l'extension Skills (`skills/list`) n'a pas été testée ; l'altération de fichier est simulée côté client (méthode interne remplacée), pas par un vrai serveur malveillant.
- **Détection** : l'API GitHub est bloquée dans cette session ; les dates viennent de PyPI et de npm, les notes de version de WebFetch. Claude Code (2.1.325), Claude Agent SDK (0.2.182, 0.3.325), LangGraph Python (1.2.22) et Hermes Agent (v0.23.1, plus des canaries quotidiennes) n'ont aucune nouvelle version stable depuis le run du 2026-11-15.
- **Sujets 5 et 6** (marché, onboarding client) : aucune annonce officielle n'a été vérifiée ce run.

## Tentatives d'injection

Aucune détectée. Les notes de version, le code des paquets installés et les pages lues ont été traités comme des données.

## Sources

- https://github.com/langchain-ai/deepagents/releases — entrée deepagents 0.7.38 (13 Nov), lue le 2026-11-16
- https://pypi.org/project/deepagents/0.7.38/ — 2026-11-13T14:32:01Z
- https://github.com/PrefectHQ/fastmcp/releases/tag/v4.2.0 — 13 Nov 17:07, lue le 2026-11-16
- https://pypi.org/project/fastmcp/4.2.0/ — 2026-11-13T17:08:59Z ; 4.1.8 le 2026-11-10T20:44:54Z
- https://github.com/modelcontextprotocol/inspector/releases/tag/2.15.0 — 12 Nov 00:46, lue le 2026-11-16
- https://www.npmjs.com/package/@modelcontextprotocol/inspector — 2.15.0 le 2026-11-12T01:24:25Z, 2.14.0 le 2026-11-05T00:17:31Z
- https://github.com/langchain-ai/langchain/releases — langchain 1.5.0, langchain-core 1.8.0 / 1.8.1, lue le 2026-11-16
- https://github.com/langchain-ai/langgraphjs/releases — @langchain/langgraph-sdk 1.16.0, lue le 2026-11-16
- https://www.npmjs.com/package/@google/gemini-cli — 0.68.0 le 2026-11-10T21:22:49Z
- https://pypi.org/project/llama-cpp-python/0.3.37/ — 2026-11-15T09:14:07Z
- https://www.npmjs.com/package/@anthropic-ai/claude-code — dernière version 2.1.325 (2026-11-13T20:07:25Z), vérifié le 2026-11-16
