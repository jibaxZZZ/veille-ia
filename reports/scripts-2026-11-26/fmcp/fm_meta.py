# Affiche la meta reçue par le client pour ascii_long et with_meta, et la taille sérialisée du ToolResult
# mesurée côté serveur, juste après ResponseLimitingMiddleware (middleware « sonde » ajouté avant, donc extérieur).
import asyncio, importlib.metadata as md, pydantic_core
from fastmcp import FastMCP, Client
from fastmcp.tools.base import ToolResult
from fastmcp.server.middleware import Middleware
from fastmcp.server.middleware.response_limiting import ResponseLimitingMiddleware
from mcp_types import TextContent
class Sonde(Middleware):
    async def on_call_tool(self, ctx, call_next):
        r = await call_next(ctx); print(f"  [serveur] {ctx.message.name}: taille_sérialisée={len(pydantic_core.to_json(r, fallback=str))}"); return r
m = FastMCP("m"); m.add_middleware(Sonde()); m.add_middleware(ResponseLimitingMiddleware(max_size=2000))
@m.tool
def ascii_long() -> str: return "a" * 10000
@m.tool
def escapes() -> str: return '"\\\n' * 3000
@m.tool
def with_meta() -> ToolResult: return ToolResult(content=[TextContent(type="text", text="b" * 5000)], meta={"blob": "m" * 800})
async def go():
    print("fastmcp", md.version("fastmcp"))
    async with Client(m) as c:
        for t in ("ascii_long", "escapes", "with_meta"):
            r = await c.call_tool(t, {}); print(f"  [client] {t}: meta={ {k: (v if len(str(v))<60 else str(v)[:20]+'…') for k,v in (r.meta or {}).items()} }")
asyncio.run(go())
