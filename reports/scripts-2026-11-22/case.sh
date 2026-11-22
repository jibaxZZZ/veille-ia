#!/bin/bash
# usage: case.sh <version> <port> <cas> ; lance settings_test.mjs sous env -i contre le faux serveur
v=$1; port=$2; cas=$3; W=/tmp/veille-work-2026-11-22/agent-sdk-ts
proj=$W/proj-$cas-$v; rm -rf $proj $W/home-$v; mkdir -p $proj/.claude $W/home-$v
if [ "$cas" = badfile ]; then echo '{"permissions": {"defaultMode": "pas-un-mode"}}' > $proj/.claude/settings.json; fi
python3 -I $W/scripts/mock_api.py $port $W/logs/mock-$cas-$v.log & mp=$!; sleep 0.5
env -i PATH=/opt/node22/bin:/usr/bin:/bin HOME=$W/home-$v PROJ=$proj FULL=$FULL ANTHROPIC_BASE_URL=http://127.0.0.1:$port ANTHROPIC_API_KEY=fausse-cle-test CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
  timeout 120 node $W/scripts/settings_test.mjs $W/v$v/node_modules/@anthropic-ai/claude-agent-sdk $cas; echo node_exit=$?
kill $mp 2>/dev/null; echo "requêtes au faux serveur: $(grep -c POST $W/logs/mock-$cas-$v.log 2>/dev/null || echo 0)"
