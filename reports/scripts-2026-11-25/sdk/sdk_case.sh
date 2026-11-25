#!/bin/bash
# usage: sdk_case.sh <version> ; lance le faux serveur (mode ok) puis perm.mjs sous env -i ; marqueur = commande shell exécutée
D=/tmp/veille-work-2026-11-25; v=$1; log=$D/sdk/mock-$v.log; : > $log; rm -f $D/cc/proj/marqueur
echo '{}' > $D/cc/proj/.claude/settings.json
python3 -I $D/cc/scripts/mock_api.py 18951 $log ok & mp=$!; sleep 1
cd $D/sdk && env -i PATH=/opt/node22/bin:/usr/bin:/bin HOME=$D/sdk/home timeout 120 node $D/sdk/scripts/perm.mjs $D/sdk/v$v; echo "node_exit=$?"
kill $mp; echo "marqueur=$(ls $D/cc/proj/marqueur 2>/dev/null || echo absent)"; echo "--- requêtes au faux serveur :"; sed 's/^/  /' $log
