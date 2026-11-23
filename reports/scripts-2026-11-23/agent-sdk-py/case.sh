#!/bin/bash
# usage: case.sh <version> <port> <plafond>
D=/tmp/veille-work-2026-11-23/agent-sdk-py; v=$1; port=$2; cap=$3; log=$D/logs/mock-$v-$cap.log; : > $log
python3 -I $D/scripts/mock_api.py $port $log $cap & mp=$!; sleep 1; mkdir -p $D/home-$v $D/proj
cd $D/proj && env -i PATH=/usr/bin:/bin HOME=$D/home-$v ANTHROPIC_BASE_URL=http://127.0.0.1:$port ANTHROPIC_API_KEY=fausse-cle-test \
  CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 timeout 180 $D/venv-$v/bin/python -I $D/scripts/sdk_test.py; echo "python_exit=$?"
kill $mp; echo "requêtes au faux serveur :"; sed 's/^/  /' $log
