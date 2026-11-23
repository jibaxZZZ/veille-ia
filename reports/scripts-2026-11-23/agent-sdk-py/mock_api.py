# Faux /v1/messages (SSE) : répond "FIN-DU-MOCK". Si <plafond> > 0 et max_tokens > plafond, renvoie l'erreur 400
# au format de l'API. usage: mock_api.py <port> <log> <plafond>
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
port, logp, cap = int(sys.argv[1]), sys.argv[2], int(sys.argv[3])
def ev(t, d): return f"event: {t}\ndata: {json.dumps(d)}\n\n".encode()
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(b"{}")
    def do_POST(self):
        n = int(self.headers.get("content-length", 0)); body = json.loads(self.rfile.read(n) or b"{}")
        if "count_tokens" in self.path:
            self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(b'{"input_tokens":10}'); return
        mt = body.get("max_tokens"); open(logp, "a").write(f"POST {self.path} max_tokens={mt}\n")
        if cap and mt and mt > cap:
            err = {"type":"error","error":{"type":"invalid_request_error","message":f"max_tokens: {mt} > {cap}, which is the maximum allowed number of output tokens for {body.get('model')}"}}
            self.send_response(400); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(json.dumps(err).encode()); return
        msg = {"id":"msg_mock","type":"message","role":"assistant","model":body.get("model"),"content":[],"stop_reason":None,"stop_sequence":None,"usage":{"input_tokens":10,"output_tokens":1}}
        self.send_response(200); self.send_header("content-type","text/event-stream"); self.end_headers()
        self.wfile.write(ev("message_start",{"type":"message_start","message":msg}))
        self.wfile.write(ev("content_block_start",{"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}))
        self.wfile.write(ev("content_block_delta",{"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"FIN-DU-MOCK"}}))
        self.wfile.write(ev("content_block_stop",{"type":"content_block_stop","index":0}))
        self.wfile.write(ev("message_delta",{"type":"message_delta","delta":{"stop_reason":"end_turn","stop_sequence":None},"usage":{"output_tokens":3}}))
        self.wfile.write(ev("message_stop",{"type":"message_stop"}))
ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
