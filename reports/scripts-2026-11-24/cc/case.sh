#!/bin/bash
# usage: [T=<délai s>] [NT= (vide : ne pas poser DISABLE_NONESSENTIAL_TRAFFIC)] case.sh <version> <mode> <commande claude...> ; lance le faux serveur (port 18931) puis claude sous env -i
D=/tmp/veille-work-2026-11-24/cc; v=$1; mode=$2; shift 2; log=$D/logs/mock-$v-$mode.log; : > $log
if [ "$mode" != "down" ]; then python3 -I $D/scripts/mock_api.py 18931 $log $mode & mp=$!; sleep 1; fi
mkdir -p $D/home-$v $D/proj
cd $D/proj && env -i PATH=/opt/node22/bin:/usr/bin:/bin HOME=$D/home-$v ANTHROPIC_BASE_URL=http://127.0.0.1:18931 ANTHROPIC_API_KEY=fausse-cle-test \
  ${NT-CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1} timeout ${T:-120} $D/v$v/node_modules/.bin/claude "$@" < /dev/null; echo "cli_exit=$?"
[ -n "$mp" ] && kill $mp; echo "--- requêtes au faux serveur :"; sed 's/^/  /' $log
