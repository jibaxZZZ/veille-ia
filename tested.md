# Journal des éléments testés

Une ligne par test : `date | élément | version | verdict | rapport`. L'agent ajoute ses lignes à la fin à chaque run.

<!-- Exemple : 2026-11-16 | claude-subscription-directsdk | 0.3.5 | PASS | reports/2026-11-16.md -->
2026-11-15 | hermes-agent (catalogue de plugins, plafond 16 Mio) | v0.23.1 | PASS | reports/2026-11-15.md
2026-11-15 | langgraph (flux des sous-graphes sur thread propre, #9698) | 1.2.22 | PASS | reports/2026-11-15.md
2026-11-15 | claude-code (plugin eval --output-dir, teammateMode, plugin validate ; hors modèle) | 2.1.325 | PASS | reports/2026-11-15.md
2026-11-16 | deepagents (liens symboliques hors périmètre dans ls/glob) | 0.7.38 | PASS | reports/2026-11-16.md
2026-11-16 | fastmcp (skills servies par MCP, read_skill/to_directory, API 4.1 dépréciée) | 4.2.0 | PASS | reports/2026-11-16.md
2026-11-16 | mcp-inspector (garde de fetch : adresses de métadonnées, test hors réseau) | 2.15.0 | PASS | reports/2026-11-16.md
