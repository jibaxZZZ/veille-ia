# Hook PreSkillShellCommand : consigne l'entrée JSON reçue puis refuse (mode deny) ou laisse passer (mode allow).
import json, sys
mode = sys.argv[1]; d = json.load(sys.stdin)
open("/tmp/veille-work-2026-11-25/cc/logs/hook-input.log", "a").write(json.dumps({k: d.get(k) for k in ("hook_event_name","tool_name","tool_input","command_name","command_source","invoked_by")}, ensure_ascii=False) + "\n")
if mode == "deny":
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreSkillShellCommand", "permissionDecision": "deny", "permissionDecisionReason": "REFUS-PAR-HOOK-VEILLE"}}))
elif mode == "ask":
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreSkillShellCommand", "permissionDecision": "ask", "permissionDecisionReason": "DEMANDE-PAR-HOOK"}}))
elif mode == "exit2":
    sys.stderr.write("STDERR-EXIT2\n"); sys.exit(2)
elif mode == "crash":
    sys.stderr.write("STDERR-CRASH\n"); sys.exit(1)
