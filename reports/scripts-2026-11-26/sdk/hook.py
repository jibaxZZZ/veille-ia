# Hook PreSkillShellCommand (commande) : consigne l'entrée puis refuse (deny) ou ne dit rien (allow).
import json, sys
mode = sys.argv[1]; d = json.load(sys.stdin)
open("/tmp/veille-work-2026-11-26/sdk/logs/hook-input.log", "a").write(json.dumps({k: d.get(k) for k in ("hook_event_name","tool_input","command_name")}, ensure_ascii=False) + "\n")
if mode == "deny":
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreSkillShellCommand", "permissionDecision": "deny", "permissionDecisionReason": "REFUS-HOOK-FICHIER"}}))
