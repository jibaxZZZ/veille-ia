# usage: hdr_test.py <mode> ; mode = default | false | list
# Faux backend HTTP (127.0.0.1:18941) qui consigne les en-têtes reçus ; serveur FastMCP from_openapi en HTTP
# (127.0.0.1:18942) ; client FastMCP qui envoie X-Tenant et X-Secret-Client puis appelle l'outil.
import asyncio, json, sys, threading
import httpx2 as httpx  # fastmcp 4.2.x dépend de httpx2, pas de httpx
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import fastmcp
from fastmcp import FastMCP, Client
from fastmcp.client.transports import StreamableHttpTransport
mode = sys.argv[1]
seen = []
class B(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        seen.append({k.lower(): v for k, v in self.headers.items()})
        self.send_response(200); self.send_header("content-type", "application/json"); self.end_headers(); self.wfile.write(b'{"ok":true}')
threading.Thread(target=ThreadingHTTPServer(("127.0.0.1", 18941), B).serve_forever, daemon=True).start()
spec = {"openapi": "3.0.0", "info": {"title": "t", "version": "1"}, "servers": [{"url": "http://127.0.0.1:18941"}],
        "paths": {"/ping": {"get": {"operationId": "ping", "responses": {"200": {"description": "ok"}}}}}}
kw = {} if mode == "default" else {"forward_client_headers": False if mode == "false" else ["x-tenant"]}
print("fastmcp", fastmcp.__version__, "| mode", mode, "| kwargs", kw)
try:
    srv = FastMCP.from_openapi(spec, client=httpx.AsyncClient(base_url="http://127.0.0.1:18941"), **kw)
except TypeError as e:
    print("TypeError:", e); sys.exit(3)
async def main():
    task = asyncio.create_task(srv.run_http_async(host="127.0.0.1", port=18942, show_banner=False, log_level="error"))
    await asyncio.sleep(1.5)
    tr = StreamableHttpTransport("http://127.0.0.1:18942/mcp", headers={"X-Tenant": "acme", "X-Secret-Client": "ne-pas-transmettre"})
    async with Client(tr) as c:
        r = await c.call_tool("ping", {})
        print("résultat outil:", r.data if r.data is not None else r.content)
    task.cancel()
asyncio.run(main())
h = seen[-1] if seen else {}
print("en-têtes reçus par le backend:", json.dumps({k: v for k, v in sorted(h.items()) if k.startswith(("mcp", "x-"))}))
