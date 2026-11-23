#!/bin/bash
# usage: case.sh <version> <mode> ; lance le CLI de l'Inspector contre le faux serveur (port 18921), mesure la RSS max
W=/tmp/veille-work-2026-11-23/inspector; v=$1; mode=$2; : > $W/logs/evil.log
cd $W && env -i PATH=/opt/node22/bin:/usr/bin:/bin HOME=$W/home-$v python3 -I /tmp/veille-work-2026-11-23/inspector/scripts/measure.py timeout 120 \
  v$v/node_modules/.bin/mcp-inspector --cli --transport ${T:-http} --server-url http://127.0.0.1:18921/$mode/${EP:-mcp} --method tools/list > logs/out-$v-$mode.txt 2>&1
rc=$?; echo "cli_exit=$rc"; head -c 600 logs/out-$v-$mode.txt | cut -c1-300 | head -8; echo; tail -1 logs/out-$v-$mode.txt
echo "--- journal du faux serveur"; cat $W/logs/evil.log
