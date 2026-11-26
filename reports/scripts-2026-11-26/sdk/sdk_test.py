# usage: python sdk_test.py <mode>  ; mode = file (hook dans .claude/settings.json, setting_sources=["project"])
#                                   ; mode = callback (hook Python passé dans options.hooks) ; mode = none (aucun hook)
# Envoie le prompt '/sonde' à la CLI embarquée, qui parle au faux serveur 127.0.0.1:18961.
import sys, json, anyio, claude_agent_sdk as s
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher
mode = sys.argv[1]
P = "/tmp/veille-work-2026-11-26/sdk/proj"
calls = []
async def cb(inp, tool_use_id, ctx):
    calls.append({"ev": inp.get("hook_event_name"), "cmd": (inp.get("tool_input") or {}).get("command")})
    return {"hookSpecificOutput": {"hookEventName": "PreSkillShellCommand", "permissionDecision": "deny", "permissionDecisionReason": "REFUS-HOOK-CALLBACK"}}
async def main():
    env = {"ANTHROPIC_BASE_URL": "http://127.0.0.1:18961", "ANTHROPIC_API_KEY": "fausse-cle-test", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "HOME": "/tmp/veille-work-2026-11-26/sdk/home"}
    hooks = {"PreSkillShellCommand": [HookMatcher(hooks=[cb])]} if mode == "callback" else None
    opts = ClaudeAgentOptions(cwd=P, env=env, model="claude-opus-4-8", setting_sources=["project"], hooks=hooks, stderr=lambda l: print("stderr:", l[:300]))
    print("sdk", s.__version__, "cli embarquée", __import__("claude_agent_sdk._cli_version", fromlist=["x"]).__cli_version__)
    try:
        async for m in query(prompt="/sonde", options=opts):
            if type(m).__name__ == "ResultMessage": print("result:", m.subtype, repr(m.result)[:200])
    except Exception as e:
        print("EXCEPTION:", type(e).__name__, str(e)[:300])
    print("appels du callback:", json.dumps(calls))
anyio.run(main)
