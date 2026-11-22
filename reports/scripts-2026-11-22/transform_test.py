# Transformation d'outil inapplicable : cacher un argument requis sans défaut.
import asyncio, logging, fastmcp
from fastmcp import FastMCP, Client
from fastmcp.server.transforms.tool_transform import ToolTransform
from fastmcp.tools.tool_transform import ToolTransformConfig, ArgTransformConfig
logging.getLogger("fastmcp").setLevel(logging.ERROR)
print("fastmcp", fastmcp.__version__)
mcp = FastMCP("t")
@mcp.tool
def envoyer(destinataire: str, sujet: str) -> str:
    return f"envoye a {destinataire}: {sujet}"
@mcp.tool
def ping() -> str:
    return "pong"
# 'sujet' est requis et sans défaut : la transformation ne peut pas s'appliquer
mcp.add_transform(ToolTransform({"envoyer": ToolTransformConfig(name="envoyer_mail", arguments={"sujet": ArgTransformConfig(hide=True)})}))
async def main():
    async with Client(mcp) as c:
        try:
            tools = await c.list_tools(); print("list_tools ->", sorted(t.name for t in tools))
        except Exception as e:
            print("list_tools ERREUR ->", type(e).__name__, str(e)[:160])
        for name, args in [("ping", {}), ("envoyer_mail", {"destinataire": "x"}), ("envoyer", {"destinataire": "x", "sujet": "s"})]:
            try:
                r = await c.call_tool(name, args, raise_on_error=False)
                print(f"call {name} -> is_error={r.is_error}", (r.content[0].text if r.content else "")[:140])
            except Exception as e:
                print(f"call {name} ERREUR ->", type(e).__name__, str(e)[:140])
asyncio.run(main())
