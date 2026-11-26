# usage: python fm_test.py ; serveur FastMCP en mémoire.
# 1) quickstart : outil add ; 2) ResponseLimitingMiddleware(max_size=2000) sur 3 réponses trop grosses,
#    taille sérialisée du ToolResult reconstruit côté client ; 3) lien de ressource renvoyé par un outil d'un serveur monté
#    avec namespace "sub" : URI reçue et lecture de cette URI.
import asyncio, json, importlib.metadata as md, pydantic_core
from fastmcp import FastMCP, Client
from fastmcp.tools.base import ToolResult
from fastmcp.server.middleware.response_limiting import ResponseLimitingMiddleware
from mcp_types import TextContent, ResourceLink
print("fastmcp", md.version("fastmcp"))
try: import authlib; print("authlib importable", authlib.__version__)
except ImportError as e: print("authlib absent:", e)
main = FastMCP("main"); main.add_middleware(ResponseLimitingMiddleware(max_size=2000))
@main.tool
def add(a: int, b: int) -> int: return a + b
@main.tool
def ascii_long() -> str: return "a" * 10000
@main.tool
def escapes() -> str: return '"\\\n' * 3000
@main.tool
def with_meta() -> ToolResult: return ToolResult(content=[TextContent(type="text", text="b" * 5000)], meta={"blob": "m" * 800})
sub = FastMCP("sub")
@sub.resource("data://doc")
def doc() -> str: return "CONTENU-DOC"
@sub.tool
def link() -> ToolResult: return ToolResult(content=[ResourceLink(type="resource_link", uri="data://doc", name="doc")])
main.mount(sub, namespace="sub")
async def go():
    async with Client(main) as c:
        r = await c.call_tool("add", {"a": 2, "b": 3}); print("add ->", r.data)
        for t in ("ascii_long", "escapes", "with_meta"):
            r = await c.call_tool(t, {})
            tr = ToolResult(content=r.content, meta=r.meta)
            n = len(pydantic_core.to_json(tr, fallback=str))
            print(f"{t}: blocs={len(r.content)} texte={len(r.content[0].text)} car. meta={'oui' if r.meta else 'non'} taille_sérialisée={n} <=2000:{n<=2000} fin={r.content[0].text[-12:]!r}")
        names = sorted(t.name for t in await c.list_tools()); print("outils:", names)
        r = await c.call_tool([n for n in names if n.endswith("link")][0], {})
        uri = str(r.content[0].uri); print("uri reçue:", uri)
        try: rr = await c.read_resource(uri); print("lecture:", rr[0].text)
        except Exception as e: print("lecture échoue:", type(e).__name__, str(e)[:150])
asyncio.run(go())
