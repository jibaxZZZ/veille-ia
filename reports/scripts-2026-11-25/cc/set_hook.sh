#!/bin/bash
# usage: set_hook.sh deny|allow|none ; écrit proj/.claude/settings.json
D=/tmp/veille-work-2026-11-25/cc
if [ "$1" = none ]; then echo '{}' > $D/proj/.claude/settings.json; else
printf '{"hooks":{"PreSkillShellCommand":[{"hooks":[{"type":"command","command":"python3 -I %s/scripts/hook.py %s"}]}]}}\n' $D $1 > $D/proj/.claude/settings.json; fi
cat $D/proj/.claude/settings.json; rm -f $D/proj/marqueur $D/logs/hook-input.log
