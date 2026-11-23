# usage: sdk_test.py ; query() minimal contre le faux serveur (ANTHROPIC_BASE_URL fourni par case.sh)
import anyio, importlib.metadata as m
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage, TextBlock
from claude_agent_sdk._cli_version import __cli_version__
async def main():
    print("claude-agent-sdk", m.version("claude-agent-sdk"), "| CLI embarqué", __cli_version__)
    try:
        async for msg in query(prompt="dis bonjour", options=ClaudeAgentOptions(model="claude-opus-4-8", max_turns=1)):
            if isinstance(msg, AssistantMessage):
                print("assistant:", " ".join(b.text for b in msg.content if isinstance(b, TextBlock)))
            elif isinstance(msg, ResultMessage):
                print(f"result: subtype={msg.subtype} is_error={msg.is_error} result={msg.result!r}")
    except Exception as e:
        print("EXCEPTION", type(e).__name__, str(e)[:300])
anyio.run(main)
