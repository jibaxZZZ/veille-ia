#!/bin/bash
# usage: case.sh <version>
D=/tmp/veille-work-2026-11-26/lca; v=$1; log=$D/mock-$v.log; : > $log
python3 -I $D/scripts/mock_json.py 18971 $log & mp=$!; sleep 1
cd $D && env -i PATH=/usr/bin:/bin HOME=$D timeout 120 $D/v$v/bin/python -I $D/scripts/lca_test.py; echo "py_exit=$?"
kill $mp; echo "--- requêtes au faux serveur :"; sed 's/^/  /' $log
