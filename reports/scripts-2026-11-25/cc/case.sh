#!/bin/bash
# usage: [T=<délai s>] [P=<chemin pour le mode read>] case.sh <version> <mode> <commande claude...> ; lance le faux serveur (port 18931) puis claude sous env -i
D=/tmp/veille-work-2026-11-25/cc; v=$1; mode=$2; shift 2; mkdir -p $D/logs; log=$D/logs/mock-$v-$mode.log; : > $log
python3 -I $D/scripts/mock_api.py 18931 $log $mode "$P" & mp=$!; sleep 1
mkdir -p $D/home-$v $D/proj
s=$(date +%s.%N)
cd $D/proj && env -i PATH=/opt/node22/bin:/usr/bin:/bin HOME=$D/home-$v ANTHROPIC_BASE_URL=http://127.0.0.1:18931 ANTHROPIC_API_KEY=fausse-cle-test \
  CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 timeout ${T:-120} $D/v$v/node_modules/.bin/claude "$@" < /dev/null; echo "cli_exit=$? duree=$(python3 -c "print(round($(date +%s.%N)-$s,1))")s"
kill $mp; echo "--- requêtes au faux serveur :"; sed 's/^/  /' $log
