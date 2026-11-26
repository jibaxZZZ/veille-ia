from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, HookContext
async def cb(inp: dict, tid: str | None, ctx: HookContext) -> dict: return {}
opts = ClaudeAgentOptions(hooks={"PreSkillShellCommand": [HookMatcher(hooks=[cb])]})
