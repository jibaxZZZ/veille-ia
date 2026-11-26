#!/bin/bash
# usage: case.sh <version> <mode> ; mode file|callback|none. Lance le faux serveur, écrit settings.json, lance sdk_test.py sous env -i.
D=/tmp/veille-work-2026-11-26/sdk; v=$1; mode=$2; log=$D/logs/mock-$v-$mode.log; : > $log
rm -f $D/proj/marqueur $D/logs/hook-input.log
if [ "$mode" = file ]; then printf '{"hooks":{"PreSkillShellCommand":[{"hooks":[{"type":"command","command":"python3 -I %s/scripts/hook.py deny"}]}]}}\n' $D > $D/proj/.claude/settings.json; else echo '{}' > $D/proj/.claude/settings.json; fi
python3 -I $D/scripts/mock_api.py 18961 $log ok & mp=$!; sleep 1
cd $D && env -i PATH=/usr/bin:/bin HOME=$D/home timeout ${T:-120} $D/v$v/bin/python -I $D/scripts/sdk_test.py $mode; echo "py_exit=$?"
kill $mp; echo "marqueur=$(ls $D/proj/marqueur 2>/dev/null || echo absent)"; echo "hook_fichier=$(cat $D/logs/hook-input.log 2>/dev/null)"
echo "--- requêtes au faux serveur :"; sed 's/^/  /' $log
