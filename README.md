# veille-ia

Dépôt d'une veille IA quotidienne qui teste au lieu de seulement lire, exécutée par une tâche planifiée cloud Claude Code.

## Mise en place (10 minutes)

1. **Dépôt GitHub privé.** Depuis ce dossier :
   ```
   git init -b main
   git add . && git commit -m "init veille"
   git remote add origin <url-de-ton-repo-prive>
   git push -u origin main
   ```
2. **Accès GitHub.** Sur claude.ai/code, connecte ton compte GitHub et autorise ce dépôt.
3. **Environnement.** Crée un environnement cloud dédié :
   - accès réseau : **Full** (ou Custom avec les domaines voulus) ;
   - aucune variable d'environnement, aucun secret (la veille n'en a pas besoin) ;
   - pas de script d'installation.
4. **Nouvelle tâche planifiée** (claude.ai/code/routines, bouton « New task » ou « New routine ») :
   - prompt : contenu de `PROMPT.md` ;
   - dépôt : celui-ci ; environnement : celui de l'étape 3 ;
   - déclencheur : planifié, quotidien, à une heure qui ne tombe pas pile (par exemple 05:07), pour éviter les départs en retard ;
   - **connecteurs : retire-les tous** (Gmail, Notion et les autres), la veille n'en a pas besoin ;
   - modèle : commence par Sonnet 5.5 puis compare avec un modèle plus fort si la qualité des tests te déçoit.
5. **Autorise les pushes sur `main`.** Dans les paramètres du dépôt de la tâche, active *Allow unrestricted branch pushes*. Sans cela, Claude pousse sur une branche `claude/…` : `tested.md` n'est alors jamais vu par le run suivant et les tests se répètent.
6. **Premier essai : « Run now ».** Ouvre la session et lis la transcription : actions bloquées, installations qui échouent, temps passé, consommation sur claude.ai/settings/usage. Ajuste `topics.md`, `rubric.md` ou le prompt avant de laisser tourner la nuit.

## Lire les résultats

- `reports/LATEST.md` : dernier rapport ; `reports/<date>.md` : historique.
- `tested.md` : ce qui a déjà été testé.
- La session de chaque run est dans l'historique de la tâche (transcription complète).

## Points de vigilance

- Les runs cloud démarrent en *auto mode* : après plusieurs actions bloquées, un run peut attendre une validation humaine. Si l'historique montre un run bloqué, ouvre-le et regarde ce qui a été refusé.
- Réseau Full et contenu web non fiable : la protection repose sur l'absence de secrets et de connecteurs et sur les règles de `CLAUDE.md`. Garde cette séparation.
- La tâche consomme ton abonnement comme une session interactive ; une veille qui installe et lance des outils consomme nettement plus qu'une simple lecture.
