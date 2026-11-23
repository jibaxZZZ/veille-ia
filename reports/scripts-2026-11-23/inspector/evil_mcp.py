# Faux serveur MCP Streamable HTTP. Chemin /<mode>/mcp. mode ok : réponses normales en SSE.
# giant : réponse SSE à initialize = une ligne "data:" de <MiB> Mio sans fin de ligne.
# bigevent : un événement de <MiB> Mio fait de lignes "data:" courtes sans ligne vide finale.
# usage: evil_mcp.py <port> <MiB> <log>
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
port, mib, logp = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
def log(s): open(logp, "a").write(s + "\n")
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def do_GET(self):
        # mode giantsse (transport sse historique) : GET /giantsse/sse = événement endpoint puis ligne "data:" sans fin
        if self.path.startswith("/giantsse/sse"):
            log(f"GET {self.path}")
            self.send_response(200); self.send_header("content-type", "text/event-stream"); self.send_header("connection", "close"); self.end_headers()
            try:
                self.wfile.write(b"event: endpoint\ndata: /giantsse/messages\n\nevent: message\ndata: ")
                for i in range(mib): self.wfile.write(b"A" * (1 << 20))
                log(f"giantsse: {mib} Mio envoyés sans fin de ligne sur le flux GET")
            except (BrokenPipeError, ConnectionResetError) as e:
                log(f"giantsse: client a fermé la connexion ({type(e).__name__})")
            self.close_connection = True; return
        self.send_response(405); self.send_header("content-length", "0"); self.end_headers()
    def do_DELETE(self): self.do_GET()
    def do_POST(self):
        mode = self.path.strip("/").split("/")[0]
        n = int(self.headers.get("content-length", 0)); req = json.loads(self.rfile.read(n) or b"{}")
        log(f"POST {self.path} method={req.get('method')}")
        if "id" not in req:
            self.send_response(202); self.send_header("content-length", "0"); self.end_headers(); return
        if req["method"] == "initialize":
            res = {"protocolVersion": req["params"]["protocolVersion"], "capabilities": {"tools": {}}, "serverInfo": {"name": "faux", "version": "0"}}
        elif req["method"] == "tools/list":
            res = {"tools": [{"name": "echo", "description": "x" * (1 << 20), "inputSchema": {"type": "object"}}]}
        else:
            res = {}
        self.send_response(200); self.send_header("content-type", "text/event-stream"); self.send_header("connection", "close"); self.end_headers()
        try:
            if mode == "ok" or req["method"] != "initialize":
                self.wfile.write(b"event: message\ndata: " + json.dumps({"jsonrpc": "2.0", "id": req["id"], "result": res}).encode() + b"\n\n")
            elif mode == "giant":
                self.wfile.write(b"event: message\ndata: ")
                for i in range(mib): self.wfile.write(b"A" * (1 << 20))
                log(f"giant: {mib} Mio envoyés sans fin de ligne")
            elif mode == "bigevent":
                for i in range(mib * 16): self.wfile.write(b"data: " + b"B" * 65530 + b"\n")
                log(f"bigevent: {mib} Mio en lignes courtes sans ligne vide")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError) as e:
            log(f"{mode}: client a fermé la connexion ({type(e).__name__})")
        self.close_connection = True
ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
