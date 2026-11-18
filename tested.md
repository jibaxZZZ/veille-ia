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
