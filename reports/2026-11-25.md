# Veille IA — 2026-11-25

## TL;DR

- **Run du 2026-11-25** (fenêtre du 2026-11-18 au 2026-11-25) : **8 éléments détectés, 3 testés (3 PASS), 5 au Radar.** Les 3 tests sont des A/B contre la version précédente, faits contre de faux serveurs locaux, sans vraie API.
- **Claude Code 2.1.332 : PASS.** Le nouveau hook `PreSkillShellCommand` bloque bien le shell en ligne (`` !`…` ``) d'une commande slash (deny, ask, exit 2). Mais un hook qui plante (exit 1) laisse passer la commande. Lire un tube nommé sans écrivain échoue maintenant en 20 s ; en 2.1.331, la session bloque jusqu'au délai de 60 s.
- **anthropic (SDK Python) 2.14.0 : PASS.** `proxy=` et `trust_env=False` passent enfin avant `HTTP_PROXY`, en sync et en async (en 2.13.0, la variable gagnait). Changement de comportement confirmé : avec `proxy=`, `NO_PROXY` n'est plus lu. Il faut passer par `mounts`.
- **Claude Agent SDK TypeScript 0.3.332 : PASS.** `setPermissionMode()` renvoie `{mode}` (en 0.3.331 : `undefined`). Le code qui type la promesse en `Promise<void>` ne compile plus. Le hook `PreSkillShellCommand` marche en callback SDK ; en 0.3.331, il est ignoré sans avertissement.
- Aucune tentative d'injection relevée. Pas de GPU, donc aucun test de performance.

## Contexte et choix faits sans validation humaine

- Répertoire de travail : `/tmp/veille-work-2026-11-25/<élément>/` (`cc`, `anth`, `sdk`). Les commandes passent par le wrapper `bin/run <journal> "<commande>"`. Il consigne la commande, le code de sortie `[exit=…]` (celui du dernier maillon d'un pipe) et la sortie tronquée à 40 lignes. Quand un script masque le code d'un programme, ce code est affiché à part (`cli_exit=`, `node_exit=`). Les lignes trop longues sont coupées à 400 caractères (`cut -c1-400`).
- Machine : Linux x86_64, Node v22 (`/opt/node22/bin`), npm, uv, Python 3.11. Pas de GPU.
- **Isolation** : Claude Code et l'Agent SDK tournent sous `env -i`, avec un `HOME` placé dans le répertoire de travail et la clé factice `fausse-cle-test`. Les scripts Python tournent avec `python -I` sous `env -i`. Les variables `*_PROXY` du test 2 sont posées par le script avec des adresses locales de test. Aucune variable d'environnement de la machine n'est lue. Aucun modèle réel n'a été appelé.
- **Détection** : versions et dates viennent des registres officiels (`npm view <paquet> time --json`, API JSON de PyPI). Les notes viennent des changelogs bruts sur raw.githubusercontent.com et des pages de releases GitHub (lues avec un outil de lecture web).
- **Sélection** : j'ai retenu Claude Code 2.1.332 (sujets 1 et 3 : nouveau hook de permission), le SDK Python d'Anthropic 2.14.0 (sujet 3 : le trafic d'un harnais passe-t-il par le bon proxy) et l'Agent SDK TS 0.3.332 (sujet 1 : changement de type cassant). Aucun ne figure dans `tested.md` à ces versions. Pour ne pas tester deux fois la même chose, le test 3 porte sur ce qui est propre au SDK : la valeur de retour de `setPermissionMode` et le hook en callback, pas en commande.
- **Scripts** : copie exacte dans [`reports/scripts-2026-11-25/`](scripts-2026-11-25/). Pour refaire un test, copie-les dans `/tmp/veille-work-2026-11-25/<élément>/scripts/` (`run` dans `/tmp/veille-work-2026-11-25/bin/`, `sonde.md` dans `/tmp/veille-work-2026-11-25/cc/proj/.claude/commands/`) : les chemins sont écrits en dur.

---

## Tests

### 1. Claude Code 2.1.332 — hook `PreSkillShellCommand`, lecture d'un tube nommé

- **Sujet** : 1 (hooks Claude Code) et 3 (permissions). **Ce que ça change pour moi** : je peux enfin filtrer le shell en ligne des skills et commandes slash, qui jusqu'ici s'exécutait avant tout hook PreToolUse. Mais le filtre laisse passer en cas d'échec : un hook qui plante (exit 1) ne protège rien, il doit sortir en 2 ou renvoyer `deny`. **Effort** : ~30 min (écrire et tester le hook).
- **Source** : https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md, section 2.1.332. Date vérifiée sur npm : 2.1.332 publiée le 2026-11-24T22:06:38Z (2.1.331 : 2026-11-23T18:36:26Z).
- **Prérequis** : `npm install --prefix /tmp/veille-work-2026-11-25/cc/v<v> --no-audit --no-fund @anthropic-ai/claude-code@<v>` pour 2.1.331 et 2.1.332 (`[exit=0]`, « added 2 packages »). Scripts :
  - `mock_api.py <port> <log> <mode> [chemin]` : faux `/v1/messages` en SSE. En mode `ok`, il répond `FIN-DU-MOCK`. En mode `read`, la 1ʳᵉ réponse est un `tool_use` Read sur `[chemin]`. Il consigne chaque requête, son instant `t` et la fin du texte utilisateur de la 1ʳᵉ requête (`user_text`), ce qui montre ce que la commande slash a injecté.
  - `case.sh <v> <mode> <args…>` : lance le faux serveur sur 127.0.0.1:18931, puis `claude <args>` depuis `cc/proj` sous `env -i`, avec `ANTHROPIC_BASE_URL`, une clé factice, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` et `timeout ${T:-120}`.
  - `proj/.claude/commands/sonde.md` : frontmatter `allowed-tools: Bash(touch:*), Bash(echo:*)` et corps ``Sortie du shell : !`touch marqueur && echo SHELL-A-TOURNE` ``.
  - `set_hook.sh <mode>` : écrit `proj/.claude/settings.json` avec un hook `PreSkillShellCommand` de type `command` qui lance `hook.py <mode>`, ou `{}` (`none`). Il efface aussi le marqueur et le journal du hook. `hook.py` consigne l'entrée JSON, puis selon le mode : `deny` ou `ask` (JSON `hookSpecificOutput`), `exit2`, `crash` (exit 1), `allow` (rien).

**a) Quickstart : `claude -p` sur le faux serveur**

```
$ /tmp/veille-work-2026-11-25/cc/scripts/case.sh 2.1.332 ok -p 'dis bonjour' --model claude-opus-4-8
[exit=0]
FIN-DU-MOCK
cli_exit=0 duree=0.4s
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=1.4s tool_result=-
      user_text='dis bonjour'
```
(Même résultat en 2.1.331.)

**b) « Added a `PreSkillShellCommand` hook event that can refuse a skill or command's inline shell commands as it loads; on 2.1.331 and older, a settings file naming it opens a dialog at start »**

Sans hook, le shell en ligne tourne dans les deux versions (référence) :

```
$ /tmp/veille-work-2026-11-25/cc/scripts/set_hook.sh none >/dev/null; T=60 /tmp/veille-work-2026-11-25/cc/scripts/case.sh 2.1.332 ok -p '/sonde' --model claude-opus-4-8 2>&1 | cut -c1-400; echo marqueur=$(ls /tmp/veille-work-2026-11-25/cc/proj/marqueur 2>/dev/null || echo absent); echo hook_input=$(cat /tmp/veille-work-2026-11-25/cc/logs/hook-input.log 2>/dev/null)
[exit=0]
FIN-DU-MOCK
cli_exit=0 duree=0.5s
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=1.4s tool_result=-
      user_text='<command-message>sonde</command-message>\n<command-name>/sonde</command-name>\n | Sortie du shell : SHELL-A-TOURNE\n'
marqueur=/tmp/veille-work-2026-11-25/cc/proj/marqueur
hook_input=
```

Hook `deny`, 2.1.331 puis 2.1.332 :

```
$ /tmp/veille-work-2026-11-25/cc/scripts/set_hook.sh deny >/dev/null; T=60 /tmp/veille-work-2026-11-25/cc/scripts/case.sh 2.1.331 ok -p '/sonde' --model claude-opus-4-8 2>&1 | cut -c1-400; echo marqueur=$(ls /tmp/veille-work-2026-11-25/cc/proj/marqueur 2>/dev/null || echo absent); echo hook_input=$(cat /tmp/veille-work-2026-11-25/cc/logs/hook-input.log 2>/dev/null)
[exit=0]
These settings entries were skipped; the rest of each source is in effect:
  /tmp/veille-work-2026-11-25/cc/proj/.claude/settings.json (hooks.PreSkillShellCommand): Unknown hook event "PreSkillShellCommand" was ignored. Valid events: PreToolUse, PostToolUse, PostToolUseFailure, PostToolBatch, Notification, UserPromptSubmit, UserPromptExpansion, SessionStart, SessionEnd, Stop, StopFailure, SubagentStart, SubagentStop, PreCompact, PostCompact, PreModelSwitch, PostModelSwit
Fix each problem listed, then start Claude Code again. For settings sent with applyFlagSettings, shown as SDK inline settings, send them again instead.
FIN-DU-MOCK
cli_exit=0 duree=0.5s
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=1.4s tool_result=-
      user_text='<command-message>sonde</command-message>\n<command-name>/sonde</command-name>\n | Sortie du shell : SHELL-A-TOURNE\n'
marqueur=/tmp/veille-work-2026-11-25/cc/proj/marqueur
hook_input=

$ /tmp/veille-work-2026-11-25/cc/scripts/set_hook.sh deny >/dev/null; T=60 /tmp/veille-work-2026-11-25/cc/scripts/case.sh 2.1.332 ok -p '/sonde' --model claude-opus-4-8 2>&1 | cut -c1-400; echo marqueur=$(ls /tmp/veille-work-2026-11-25/cc/proj/marqueur 2>/dev/null || echo absent); echo hook_input=$(cat /tmp/veille-work-2026-11-25/cc/logs/hook-input.log 2>/dev/null)
[exit=0]
FIN-DU-MOCK
cli_exit=0 duree=0.8s
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=1.7s tool_result=-
      user_text='<command-message>sonde</command-message>\n<command-name>/sonde</command-name>\n | Sortie du shell : [not run: blocked by hook: REFUS-PAR-HOOK-VEILLE]\n'
marqueur=absent
hook_input={"hook_event_name": "PreSkillShellCommand", "tool_name": "Bash", "tool_input": {"command": "touch marqueur && echo SHELL-A-TOURNE"}, "command_name": "sonde", "command_source": "projectSettings", "invoked_by": "user"}
```

Hook `allow` (2.1.332) : le hook est appelé avec la même entrée, la commande tourne :

```
$ /tmp/veille-work-2026-11-25/cc/scripts/set_hook.sh allow >/dev/null; T=60 /tmp/veille-work-2026-11-25/cc/scripts/case.sh 2.1.332 ok -p '/sonde' --model claude-opus-4-8 2>&1 | cut -c1-400; echo marqueur=$(ls /tmp/veille-work-2026-11-25/cc/proj/marqueur 2>/dev/null || echo absent); echo hook_input=$(cat /tmp/veille-work-2026-11-25/cc/logs/hook-input.log 2>/dev/null)
[exit=0]
FIN-DU-MOCK
cli_exit=0 duree=0.5s
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=1.4s tool_result=-
      user_text='<command-message>sonde</command-message>\n<command-name>/sonde</command-name>\n | Sortie du shell : SHELL-A-TOURNE\n'
marqueur=/tmp/veille-work-2026-11-25/cc/proj/marqueur
hook_input={"hook_event_name": "PreSkillShellCommand", "tool_name": "Bash", "tool_input": {"command": "touch marqueur && echo SHELL-A-TOURNE"}, "command_name": "sonde", "command_source": "projectSettings", "invoked_by": "user"}
```

Cas limites (2.1.332) : hook `ask`, `exit2` (sortie 2), `crash` (sortie 1) :

```
$ /tmp/veille-work-2026-11-25/cc/scripts/set_hook.sh ask >/dev/null; T=60 /tmp/veille-work-2026-11-25/cc/scripts/case.sh 2.1.332 ok -p '/sonde' --model claude-opus-4-8 2>&1 | cut -c1-400; echo marqueur=$(ls /tmp/veille-work-2026-11-25/cc/proj/marqueur 2>/dev/null || echo absent)
[exit=0]
FIN-DU-MOCK
cli_exit=0 duree=0.5s
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=1.4s tool_result=-
      user_text='<command-message>sonde</command-message>\n<command-name>/sonde</command-name>\n | Sortie du shell : [not run: blocked by hook: DEMANDE-PAR-HOOK]\n'
marqueur=absent

$ /tmp/veille-work-2026-11-25/cc/scripts/set_hook.sh exit2 >/dev/null; T=60 /tmp/veille-work-2026-11-25/cc/scripts/case.sh 2.1.332 ok -p '/sonde' --model claude-opus-4-8 2>&1 | cut -c1-400; echo marqueur=$(ls /tmp/veille-work-2026-11-25/cc/proj/marqueur 2>/dev/null || echo absent)
[exit=0]
FIN-DU-MOCK
cli_exit=0 duree=0.5s
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=1.4s tool_result=-
      user_text='<command-message>sonde</command-message>\n<command-name>/sonde</command-name>\n | Sortie du shell : [not run: blocked by hook: STDERR-EXIT2]\n'
marqueur=absent

$ /tmp/veille-work-2026-11-25/cc/scripts/set_hook.sh crash >/dev/null; T=60 /tmp/veille-work-2026-11-25/cc/scripts/case.sh 2.1.332 ok -p '/sonde' --model claude-opus-4-8 2>&1 | cut -c1-400; echo marqueur=$(ls /tmp/veille-work-2026-11-25/cc/proj/marqueur 2>/dev/null || echo absent)
[exit=0]
FIN-DU-MOCK
cli_exit=0 duree=0.6s
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=1.5s tool_result=-
      user_text='<command-message>sonde</command-message>\n<command-name>/sonde</command-name>\n | Sortie du shell : SHELL-A-TOURNE\n'
marqueur=/tmp/veille-work-2026-11-25/cc/proj/marqueur
```

Constat annexe : un premier essai avec `touch /tmp/veille-work-2026-11-25/cc/marqueur` (hors du dossier du projet) a été refusé dans les deux versions **avant** l'appel du hook : `touch in '…/cc/marqueur' needs approval. The path is outside the working directories for this session`. Le marqueur a donc été placé dans le projet.

- `VÉRIFIÉ` : le hook refuse le shell en ligne au chargement de la commande. Avec deny, ask et exit 2, la commande ne tourne pas, et le modèle reçoit `[not run: blocked by hook: <raison>]`.
- `VÉRIFIÉ` (source : les chaînes du binaire, pas la doc publique) : l'entrée contient `tool_name`, `tool_input.command`, `command_name`, `command_source` et `invoked_by`. Une décision `ask` est traitée comme un blocage.
- `CONTREDIT` (en `-p`) : « on 2.1.331 … opens a dialog at start ». En mode non interactif, 2.1.331 n'ouvre pas de dialogue : elle affiche « Unknown hook event … was ignored », ignore l'entrée et exécute le shell. Le mode interactif est `NON VÉRIFIÉ`.
- Constat non documenté : un hook qui sort en 1 (plantage) laisse la commande s'exécuter. L'échec est ouvert, comme pour les autres hooks non bloquants.

**c) « Fixed Read … hanging on a named pipe that nothing writes to … the read now fails after 20 seconds »**

```
$ T=60 P=/tmp/veille-work-2026-11-25/cc/proj/tube.env /tmp/veille-work-2026-11-25/cc/scripts/case.sh 2.1.331 read -p 'lis tube.env' --model claude-opus-4-8 --allowedTools Read 2>&1 | cut -c1-400
[exit=0]
cli_exit=124 duree=60.0s
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=1.3s tool_result=-
      user_text='lis tube.env'

$ T=60 P=/tmp/veille-work-2026-11-25/cc/proj/tube.env /tmp/veille-work-2026-11-25/cc/scripts/case.sh 2.1.332 read -p 'lis tube.env' --model claude-opus-4-8 --allowedTools Read 2>&1 | cut -c1-400
[exit=0]
FIN-DU-MOCK
cli_exit=0 duree=20.5s
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=1.4s tool_result=-
      user_text='lis tube.env'
  POST /v1/messages?beta=true n=2 t=21.5s tool_result=[{"type": "tool_result", "content": "Nothing is writing to this pipe. Check that the app serving it is running and unlocked.", "is_error": true, "tool_use_id": "toolu_mock1"}]
```
(Tube créé avant le test avec `mkfifo /tmp/veille-work-2026-11-25/cc/proj/tube.env`.)

- `VÉRIFIÉ` : en 2.1.332, Read échoue après environ 20 s (outil appelé à t≈1,4 s, résultat à t=21,5 s) avec une erreur explicite, et la session continue. En 2.1.331, la session reste bloquée jusqu'au `timeout` de 60 s (code 124).
- `NON VÉRIFIÉ` : @-mentions et compaction sur un tube nommé.

**Verdict : PASS.** Les deux correctifs testés se comportent comme annoncé, en A/B contre 2.1.331. Seule nuance : l'absence de dialogue en `-p` sur 2.1.331.

### 2. anthropic (SDK Python) 2.14.0 — `proxy=` et `trust_env` contre les variables `*_PROXY`

- **Sujet** : 3 (harnais : sortie réseau maîtrisée) et 4. **Ce que ça change pour moi** : un harnais qui force `proxy=` ou `trust_env=False` est enfin respecté, alors qu'avant un `HTTP_PROXY` hérité redirigeait l'API ailleurs sans le dire. Avec `proxy=`, `NO_PROXY` ne sert plus : il faut lister les exceptions dans `mounts`. **Effort** : ~10 min (mise à jour, puis relecture des `NO_PROXY`).
- **Source** : https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md, section 2.14.0 (2026-11-24). Date vérifiée sur PyPI : 2026-11-24T21:01:46Z (2.13.0 : 2026-11-23T18:35:01Z).
- **Prérequis** : `uv venv -q -p 3.11 /tmp/veille-work-2026-11-25/anth/venv<v> && uv pip install -q -p …/venv<v>/bin/python anthropic==<v>` pour 2.13.0 et 2.14.0. Dans les deux, la dépendance HTTP est `httpx2==2.16.2` et `httpcore2==2.16.2` (`[exit=0]`). Une première commande d'import a échoué (`ModuleNotFoundError: No module named 'httpx'`, `[exit=1]`) : le SDK 2.x dépend de `httpx2`, pas de `httpx`.
- **Script** `proxy_test.py` : trois faux serveurs locaux répondent directement, sans relayer. Ce sont CIBLE (`base_url`, port 18941), PROXY-ENV (`HTTP_PROXY`, 18942) et PROXY-ARG (`proxy=`, 18943). Chaque cas construit `Anthropic(..., http_client=DefaultHttpxClient(**kw))` (ou la version async), appelle `messages.create` et affiche le serveur qui a répondu, avec le chemin reçu (forme absolue = requête vue comme proxy).

```
$ env -i PATH=/usr/bin:/bin /tmp/veille-work-2026-11-25/anth/venv2.13.0/bin/python -I /tmp/veille-work-2026-11-25/anth/scripts/proxy_test.py
[exit=0]
anthropic 2.13.0
A défaut, HTTP_PROXY posé                               -> PROXY-ENV (chemin=http://127.0.0.1:18941/v1/messages)
B proxy=PROXY-ARG, HTTP_PROXY posé                      -> PROXY-ENV (chemin=http://127.0.0.1:18941/v1/messages)
C trust_env=False, HTTP_PROXY posé                      -> PROXY-ENV (chemin=http://127.0.0.1:18941/v1/messages)
D proxy=PROXY-ARG, NO_PROXY=127.0.0.1                   -> CIBLE (chemin=/v1/messages)
E proxy=PROXY-ARG + mounts all://127.0.0.1:18941=None   -> CIBLE (chemin=/v1/messages)
F async proxy=PROXY-ARG, HTTP_PROXY posé                -> PROXY-ENV (chemin=http://127.0.0.1:18941/v1/messages)
G async trust_env=False, HTTP_PROXY posé                -> PROXY-ENV (chemin=http://127.0.0.1:18941/v1/messages)

$ env -i PATH=/usr/bin:/bin /tmp/veille-work-2026-11-25/anth/venv2.14.0/bin/python -I /tmp/veille-work-2026-11-25/anth/scripts/proxy_test.py
[exit=0]
anthropic 2.14.0
A défaut, HTTP_PROXY posé                               -> PROXY-ENV (chemin=http://127.0.0.1:18941/v1/messages)
B proxy=PROXY-ARG, HTTP_PROXY posé                      -> PROXY-ARG (chemin=http://127.0.0.1:18941/v1/messages)
C trust_env=False, HTTP_PROXY posé                      -> CIBLE (chemin=/v1/messages)
D proxy=PROXY-ARG, NO_PROXY=127.0.0.1                   -> PROXY-ARG (chemin=http://127.0.0.1:18941/v1/messages)
E proxy=PROXY-ARG + mounts all://127.0.0.1:18941=None   -> CIBLE (chemin=/v1/messages)
F async proxy=PROXY-ARG, HTTP_PROXY posé                -> PROXY-ARG (chemin=http://127.0.0.1:18941/v1/messages)
G async trust_env=False, HTTP_PROXY posé                -> CIBLE (chemin=/v1/messages)
```

J'ai ensuite ajouté le cas E2 au script (mount sans port, la forme donnée par le changelog) :

```
$ env -i PATH=/usr/bin:/bin /tmp/veille-work-2026-11-25/anth/venv2.14.0/bin/python -I /tmp/veille-work-2026-11-25/anth/scripts/proxy_test.py | grep -E '^(anthropic|E)'
[exit=0]
anthropic 2.14.0
E proxy=PROXY-ARG + mounts all://127.0.0.1:18941=None   -> CIBLE (chemin=/v1/messages)
E2 proxy=PROXY-ARG + mounts all://127.0.0.1=None (forme de la doc) -> CIBLE (chemin=/v1/messages)
```

- `VÉRIFIÉ` : « the variables won » en 2.13.0 (cas B, C, F, G vers PROXY-ENV).
- `VÉRIFIÉ` : « `proxy=` is used for every request and the variables are not read » (cas B et F, sync et async), et « `trust_env=False` ignores them » (cas C et G).
- `VÉRIFIÉ` : « with `proxy=` set, a host listed in `NO_PROXY` … now goes through your proxy » (cas D : CIBLE en 2.13.0, PROXY-ARG en 2.14.0).
- `VÉRIFIÉ` : `mounts={"all://that.host": None}` garde l'hôte hors du proxy (E et E2).
- Comportement par défaut (cas A) inchangé : `HTTP_PROXY` reste suivi quand rien n'est passé.

**Verdict : PASS.** Les 4 affirmations testées sont vérifiées en A/B, en sync comme en async.

### 3. Claude Agent SDK TypeScript 0.3.332 — `setPermissionMode()` et hook `PreSkillShellCommand` en callback

- **Sujet** : 1 (Agent SDK). **Ce que ça change pour moi** : un harnais SDK peut enregistrer le mode réellement appliqué (`r?.mode`) au lieu de supposer le mode demandé. Le code typé `Promise<void>` doit être corrigé avant la mise à jour, sinon la compilation casse. **Effort** : ~15 min (mise à jour et correction des types).
- **Source** : https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md, section 0.3.332. Date vérifiée sur npm : 2026-11-24T22:09:06Z (0.3.331 : 2026-11-23T18:35:23Z).
- **Prérequis** : `npm install --prefix /tmp/veille-work-2026-11-25/sdk/v<v> --no-audit --no-fund @anthropic-ai/claude-agent-sdk@<v> typescript@5.9.3` pour 0.3.331 et 0.3.332 (`[exit=0]`, « added 106 packages »). Le binaire embarqué de 0.3.332 répond `2.1.332 (Claude Code)` à `--version` (`[exit=0]`).
- **Scripts** : `perm.mjs <dossier>` lance `query()` en mode streaming contre le faux serveur du test 1 (port 18951, mode `ok`), avec `cwd` = le projet `cc/proj` (commande `/sonde`), `settingSources: ['project']`, un `env` minimal explicite et un hook `PreSkillShellCommand` en callback qui renvoie `deny`. Il appelle `setPermissionMode` sur 4 modes, puis attend le `result`. `sdk_case.sh <v>` lance le tout sous `env -i`, avec un `settings.json` projet vide (le refus vient donc du seul callback). `types_check.mts` tient la promesse en `Promise<void>` et lit `r?.mode`.

```
$ /tmp/veille-work-2026-11-25/sdk/scripts/sdk_case.sh 0.3.331 2>&1 | cut -c1-400
[exit=0]
setPermissionMode(plan) -> résolu undefined
setPermissionMode(acceptEdits) -> résolu undefined
setPermissionMode(bypassPermissions) -> rejeté: Cannot set permission mode to bypassPermissions because the session was not launched with --dangerously-skip-permissions
setPermissionMode(bogus) -> rejeté: Cannot set permission mode: must be one of acceptEdits, auto, bypassPermissions, default, dontAsk, plan
result: subtype=success result="FIN-DU-MOCK"
appels du hook SDK: []
node_exit=0
marqueur=/tmp/veille-work-2026-11-25/cc/proj/marqueur
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=1.9s tool_result=-
      user_text='<command-message>sonde</command-message>\n<command-name>/sonde</command-name>\n | Sortie du shell : SHELL-A-TOURNE\n'

$ /tmp/veille-work-2026-11-25/sdk/scripts/sdk_case.sh 0.3.332 2>&1 | cut -c1-400
[exit=0]
setPermissionMode(plan) -> résolu {"mode":"plan"}
setPermissionMode(acceptEdits) -> résolu {"mode":"acceptEdits"}
setPermissionMode(bypassPermissions) -> rejeté: Cannot set permission mode to bypassPermissions because the session was not launched with --dangerously-skip-permissions
setPermissionMode(bogus) -> rejeté: Cannot set permission mode: must be one of acceptEdits, auto, bypassPermissions, default, dontAsk, plan
result: subtype=success result="FIN-DU-MOCK"
appels du hook SDK: [{"ev":"PreSkillShellCommand","cmd":"touch marqueur && echo SHELL-A-TOURNE","name":"sonde"}]
node_exit=0
marqueur=absent
--- requêtes au faux serveur :
  POST /v1/messages?beta=true n=1 t=1.5s tool_result=-
      user_text='<command-message>sonde</command-message>\n<command-name>/sonde</command-name>\n | Sortie du shell : [not run: blocked by hook: REFUS-SDK-VEILLE]\n'
```

Vérification des types (le 1ᵉʳ essai en `.ts` donnait en plus `TS1309`, l'`await` de haut niveau étant refusé en CommonJS ; refait en `.mts`) :

```
$ cd /tmp/veille-work-2026-11-25/sdk/v0.3.331 && node_modules/.bin/tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --skipLibCheck types_check.mts
[exit=2]
types_check.mts(6,34): error TS2339: Property 'mode' does not exist on type 'never'.

$ cd /tmp/veille-work-2026-11-25/sdk/v0.3.332 && node_modules/.bin/tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --skipLibCheck types_check.mts
[exit=2]
types_check.mts(4,7): error TS2322: Type 'Promise<SDKControlSetPermissionModeResponse | undefined>' is not assignable to type 'Promise<void>'.
  Type 'SDKControlSetPermissionModeResponse | undefined' is not assignable to type 'void'.
    Type 'SDKControlSetPermissionModeResponse' is not assignable to type 'void'.
```

- `VÉRIFIÉ` : « `Query.setPermissionMode()` resolves with `{ mode }` » (plan, acceptEdits). En 0.3.331, le résultat est `undefined`.
- `VÉRIFIÉ` : « code that holds its promise as `Promise<void>` no longer compiles » (TS2322 en 0.3.332, ligne 4 acceptée en 0.3.331).
- `VÉRIFIÉ` (doc de `sdk.d.ts`) : « Rejects where the mode is refused » : `bypassPermissions` sans `--dangerously-skip-permissions` et un mode inconnu sont rejetés, dans les deux versions.
- `NON VÉRIFIÉ` : un mode résolu différent du mode demandé (« which is not always the mode asked for ») ; je n'ai pas trouvé de cas qui le provoque.
- `VÉRIFIÉ` : « Added the `PreSkillShellCommand` hook event with its input and output types ». Le callback reçoit l'événement, et son `deny` bloque la commande. En 0.3.331, le callback n'est jamais appelé et la commande s'exécute, sans avertissement dans la sortie.
- `VÉRIFIÉ` : « parity with Claude Code v2.1.332 » (binaire embarqué en 2.1.332).

**Verdict : PASS.** Les 4 affirmations testées sont vérifiées. Une est `NON VÉRIFIÉE` faute de cas déclencheur.

---

## Radar (NON TESTÉ)

| Élément | Version et date (source officielle) | Sujet | Note |
|---|---|---|---|
| Hermes Agent | v0.23.4 « Latest », release du 24 nov. 2026 (notes : 23 nov.) ; [releases](https://github.com/NousResearch/hermes-agent/releases) | 2 | `NON TESTÉ`. Patch d'environ 229 PR, notes détaillées reportées à v0.24.0 ; canary du 24/11 : fournisseur mémoire « neocore » au catalogue de plugins. Pas de nouveauté précise à tester. Effort ~1 h |
| openai-agents (SDK Python) | 0.26.0, PyPI 2026-11-24T03:24:11Z ; [release v0.26.0](https://github.com/openai/openai-agents-python/releases/tag/v0.26.0) | 5, 3 | `NON TESTÉ`. Concurrent. Un chemin de fichier fourni par le modèle ne donne plus accès aux images locales (outil Codex) ; le déclenchement d'un garde-fou d'entrée arrête les outils en file ; liens relatifs sûrs dans les snapshots de sandbox |
| langsmith | 0.16.2, PyPI 2026-11-24T15:03:05Z ; https://pypi.org/project/langsmith/0.16.2/ | 3 | `NON TESTÉ`. Observabilité ; la page des releases lue ne montrait pas cette version, contenu `NON VÉRIFIÉ` |
| Claude Agent SDK Python | 0.2.188, PyPI 2026-11-23T22:26:23Z ; https://pypi.org/project/claude-agent-sdk/0.2.188/ | 1 | `NON TESTÉ`. Déjà au Radar le 24/11 ; pas de version alignée sur 2.1.332 à ce jour |
| vLLM | 0.34.0, PyPI 2026-11-16T23:51:51Z ; https://pypi.org/project/vllm/0.34.0/ | 7 | `NON TESTÉ`. Pas de GPU ; publiée il y a 9 jours, gardée pour mémoire |

Vus sans être retenus : LangGraph 1.2.24, deepagents 0.7.41, langchain-anthropic 1.7.12, FastMCP 4.2.5, MCP Inspector 2.16.0 (déjà testés, aucune nouvelle version) ; @langchain/langgraph 1.7.5 (2026-11-17) ; SDK MCP TS 1.32.2 et Python 2.3.0 (anciens).

## Limites

- **Pas de GPU** : le sujet 7 (inférence) n'est pas testé et le rapport ne contient aucune affirmation de performance.
- **Faux environnements** : tous les tests tournent contre de faux serveurs locaux, sans modèle réel ni vrai proxy. Au test 2, les « proxys » répondent eux-mêmes : le test montre qui reçoit la requête, pas un vrai relais HTTPS ou CONNECT.
- **Non couverts** : chez Claude Code, les ~80 autres entrées de 2.1.332 (skills servies par MCP, hooks qui inondent la sortie, reprise des serveurs MCP en SSE, Code Mode, Bedrock et Foundry…). Le mode interactif de 2.1.331 face au hook inconnu n'est pas testé. Chez anthropic, les nouvelles API (data controls Google, compliance review). Chez l'Agent SDK, `tool_result_meta[].rewritten_by_plugin` et le correctif du mode auto.
- Erreurs de ma part, rapportées plus haut : un marqueur placé hors du projet (refusé par la vérification de permission de Claude Code), un import de `httpx` au lieu de `httpx2`, et un fichier `.ts` au lieu de `.mts`. Chaque test a été refait après correction.
- Durée des tests : environ 20 minutes, sous la limite de 45 minutes. Le test le plus long a duré 60 s (délai volontaire sur 2.1.331).

## Tentatives d'injection

Aucune détectée. Changelogs, pages de releases, paquets installés et sorties d'outils ont été traités comme des données.

## Sources

- https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md — section 2.1.332
- https://www.npmjs.com/package/@anthropic-ai/claude-code — 2.1.332 : 2026-11-24T22:06:38Z ; 2.1.331 : 2026-11-23T18:36:26Z
- https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md — section 2.14.0 (2026-11-24)
- https://pypi.org/project/anthropic/2.14.0/ — 2026-11-24T21:01:46Z (2.13.0 : 2026-11-23T18:35:01Z)
- https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md — section 0.3.332
- https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk — 0.3.332 : 2026-11-24T22:09:06Z ; 0.3.331 : 2026-11-23T18:35:23Z
- https://github.com/NousResearch/hermes-agent/releases — v0.23.4, 24 nov. 2026 ; canary du 24 nov. 2026
- https://github.com/openai/openai-agents-python/releases/tag/v0.26.0 — 2026-11-24 ; PyPI 2026-11-24T03:24:11Z
- https://pypi.org/project/langsmith/0.16.2/ — 2026-11-24T15:03:05Z
- https://pypi.org/project/claude-agent-sdk/0.2.188/ — 2026-11-23T22:26:23Z
- https://pypi.org/project/vllm/0.34.0/ — 2026-11-16T23:51:51Z
