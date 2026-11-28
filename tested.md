# Journal des éléments testés

Une ligne par test : `date | élément | version | verdict | rapport`. L'agent ajoute ses lignes à la fin à chaque run.

<!-- Exemple : 2026-11-16 | claude-subscription-directsdk | 0.3.5 | PASS | reports/2026-11-16.md -->
2026-11-15 | hermes-agent (catalogue de plugins, plafond 16 Mio) | v0.23.1 | PASS | reports/2026-11-15.md
2026-11-15 | langgraph (flux des sous-graphes sur thread propre, #9698) | 1.2.22 | PASS | reports/2026-11-15.md
2026-11-15 | claude-code (plugin eval --output-dir, teammateMode, plugin validate ; hors modèle) | 2.1.325 | PASS | reports/2026-11-15.md
2026-11-16 | deepagents (liens symboliques hors périmètre dans ls/glob) | 0.7.38 | PASS | reports/2026-11-16.md
2026-11-16 | fastmcp (skills servies par MCP, read_skill/to_directory, API 4.1 dépréciée) | 4.2.0 | PASS | reports/2026-11-16.md
2026-11-16 | mcp-inspector (garde de fetch : adresses de métadonnées, test hors réseau) | 2.15.0 | PASS | reports/2026-11-16.md
2026-11-17 | claude-code (avertissement --allowedTools, réglages >64 niveaux, erreurs mcp add-json ; A/B 2.1.325) | 2.1.326 | PASS | reports/2026-11-17.md
2026-11-17 | anthropic SDK Python (agent toolset : faux rg dans workdir, FIFO, liens hors /memories ; A/B 2.8.0) | 2.9.0 | PASS | reports/2026-11-17.md
2026-11-17 | deepagents (StoreBackend : octets NUL stockés en base64 ; A/B 0.7.38) | 0.7.39 | PASS | reports/2026-11-17.md
2026-11-18 | claude-code (.mcp.json préservé par mcp add/remove projet, mcp add-json depuis stdin ; A/B 2.1.326) | 2.1.327 | PASS | reports/2026-11-18.md
2026-11-18 | claude-agent-sdk TypeScript (hooks en Set et agents circulaire/BigInt refusés avant lancement ; A/B 0.3.326) | 0.3.327 | PASS | reports/2026-11-18.md
2026-11-18 | fastmcp (JWTVerifier refuse un nbf futur, tolérance 30 s ; A/B 4.2.0) | 4.2.1 | PASS | reports/2026-11-18.md
2026-11-19 | claude-code (onFailure:block sur hooks mcp_tool via faux endpoint API, FORCE_COLOR négatif ; A/B 2.1.327) | 2.1.328 | PASS | reports/2026-11-19.md
2026-11-19 | deepagents (sortie conservée au timeout shell, commande annulée réellement arrêtée ; A/B 0.7.39) | 0.7.40 | PASS | reports/2026-11-19.md
2026-11-19 | fastmcp (list_skills avec ResourcesAsTools/PromptsAsTools, Namespace masque ; A/B 4.2.1) | 4.2.2 | PASS | reports/2026-11-19.md
2026-11-20 | claude-code (relance auto sur erreur max_tokens supprimée, CLAUDE_CODE_MAX_OUTPUT_TOKENS via faux endpoint API ; A/B 2.1.328) | 2.1.329 | PASS | reports/2026-11-20.md
2026-11-20 | anthropic SDK Python (espaces en %20 dans la query, signature SigV4 AnthropicAWS vérifiée localement ; A/B 2.10.0) | 2.11.0 | PASS | reports/2026-11-20.md
2026-11-20 | langgraph (REMOVE_ALL_MESSAGES dans _messages_delta_reducer, DeltaChannel avec checkpoint None ; A/B 1.2.23) | 1.2.24 | PASS | reports/2026-11-20.md
2026-11-21 | claude-code (relance max_tokens rétablie via faux endpoint, garde rm sur 13 variantes, hook SessionStart avec -p --continue ; A/B 2.1.329) | 2.1.330 | PASS | reports/2026-11-21.md
2026-11-21 | anthropic SDK Python (user_profile_id déplacé de l'en-tête vers le corps pour AnthropicBedrock sync/async ; A/B 2.11.0) | 2.12.0 | PASS | reports/2026-11-21.md
2026-11-21 | fastmcp (outil OpenAPI sans paramètre de chemin requis : erreur de validation, user_id vide non bloqué ; A/B 4.2.2) | 4.2.3 | PASS | reports/2026-11-21.md
2026-11-22 | fastmcp (code OAuth proxy échangé une seule fois sous concurrence : 10/10 → 1/10 avec store lent ; transformation inapplicable masque seulement son outil ; A/B 4.2.3) | 4.2.4 | PASS | reports/2026-11-22.md
2026-11-22 | claude-agent-sdk TypeScript (avertissement settings_not_in_effect pour settings en ligne et fichier projet invalides ; chaîne JSON invalide : pas d'écart ; A/B 0.3.329) | 0.3.330 | PASS | reports/2026-11-22.md
2026-11-22 | deepagents (edit_file sans lecture préalable OK, descriptions edit_file/execute corrigées, reducer messages LangGraph ; A/B 0.7.40) | 0.7.41 | PASS | reports/2026-11-22.md
2026-11-23 | mcp-inspector (plafond SSE GHSA-3xgv-mvj6-g78r : ligne sans fin, événement géant, transport sse ; RSS 2.15.0 351→869 Mio vs 2.16.0 ≤189 Mio ; A/B 2.15.0) | 2.16.0 | PASS | reports/2026-11-23.md
2026-11-23 | langchain-anthropic (client async non partagé : double envoi reproduit en 1.7.11, finish_reason normalisé invoke/stream, caller conservé ; A/B 1.7.11) | 1.7.12 | PASS | reports/2026-11-23.md
2026-11-23 | claude-agent-sdk Python (CLI embarquée 2.1.330, relance max_tokens via query() derrière passerelle plafonnée ; A/B 0.2.186) | 0.2.187 | PASS | reports/2026-11-23.md
2026-11-24 | claude-code (tool_use sans clé name : crash 2.1.330 → session continue ; name "" sans écart ; section API connectivity de doctor, code de sortie 0 même API injoignable ; A/B 2.1.330) | 2.1.331 | PASS | reports/2026-11-24.md
2026-11-24 | fastmcp (en-têtes mcp-* plus transmis aux backends OpenAPI, forward_client_headers False/liste ; URI de redirection : racine exacte, query, fragment ; A/B 4.2.4) | 4.2.5 | PASS | reports/2026-11-24.md
2026-11-24 | anthropic SDK Python (DeprecationWarning pour claude-opus-4-5, EOL 22/01/2027 ; plus d'avertissement pour modèles retirés, mythos-preview encore averti ; A/B 2.12.0) | 2.13.0 | PASS | reports/2026-11-24.md
2026-11-25 | claude-code (hook PreSkillShellCommand : deny/ask/exit 2 bloquent, exit 1 laisse passer, 2.1.331 ignore en -p ; Read sur tube nommé : échec en 20 s au lieu d'un blocage ; A/B 2.1.331) | 2.1.332 | PASS | reports/2026-11-25.md
2026-11-25 | anthropic SDK Python (proxy= et trust_env=False passent avant HTTP_PROXY en sync/async, NO_PROXY ignoré avec proxy=, mounts None ; A/B 2.13.0) | 2.14.0 | PASS | reports/2026-11-25.md
2026-11-25 | claude-agent-sdk TypeScript (setPermissionMode résout {mode}, Promise<void> ne compile plus, hook PreSkillShellCommand en callback ; A/B 0.3.331) | 0.3.332 | PASS | reports/2026-11-25.md
2026-11-26 | claude-agent-sdk Python (CLI embarquée 2.1.332 : hook PreSkillShellCommand en fichier et en callback appliqué, ignoré sans avertissement en 0.2.188 ; HookEvent sans l'événement, mypy refuse ; A/B 0.2.188) | 0.2.189 | PASS | reports/2026-11-26.md
2026-11-26 | fastmcp (ResponseLimitingMiddleware : 2000/2000 octets côté serveur contre 2106–4016 en 4.2.5, meta protocole ajoutée après ; liens de ressource montés préfixés ; Authlib retiré, OAuthProxy/JWTVerifier OK ; A/B 4.2.5) | 4.2.6 | PASS | reports/2026-11-26.md
2026-11-26 | langchain-anthropic (http_client/http_async_client/client/async_client, auth par requête, conflits refusés, sérialisation exclue ; client= sans timeout + max_tokens 128000 : refus non streamé ; A/B 1.7.12) | 1.7.13 | PASS | reports/2026-11-26.md
2026-11-27 | deepagents (surrogate isolé → U+FFFD et paire recollée, ls/glob ne plantent plus ; interrupt() dans glob met en pause en sync/async, refus renvoyé au modèle ; A/B 0.7.41) | 0.7.42 | PASS | reports/2026-11-27.md
2026-11-27 | langchain-core (id fournisseur du 1er chunk repris sur tous les chunks : stream, astream, astream_events v2, LangGraph stream_mode messages ; sans id inchangé ; A/B 1.8.4) | 1.8.5 | PASS | reports/2026-11-27.md
2026-11-27 | fastmcp préversion (proxy de skills : entrée invalide du backend ignorée au lieu de vider la liste, avertissement sans contenu ; %2F accepté dans le préfixe, refusé dans un fichier ; backend legacy non testé ; A/B 4.2.6) | 4.2.7a1 | PASS | reports/2026-11-27.md
2026-11-28 | mcp-inspector (garde SSRF : 6 formes NAT64/IPv6 non canoniques bloquées, NAT64 vers IP publique autorisée ; --verify sur catalogue de skills vide → exit 13 ; A/B 2.16.0) | 2.17.0 | PASS | reports/2026-11-28.md
2026-11-28 | pydantic-ai + pydantic-ai-harness (résumé de compaction raté : run conservé, FallbackCompaction passe à la fenêtre glissante ; clés Google AQ. 40–200 car. masquées ; A/B 2.76.0/0.76.0) | 2.77.0 / 0.77.0 | PASS | reports/2026-11-28.md
2026-11-28 | hermes-agent (hermes plugins config : listing non-TTY, absent en v0.23.3 ; écrivain refuse types/choix/clés inconnues/secrets, lot atomique ; éditeur interactif non testé ; A/B v0.23.3) | v0.23.4 | PASS | reports/2026-11-28.md
