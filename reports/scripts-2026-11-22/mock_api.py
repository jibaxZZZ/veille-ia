# Faux /v1/messages (SSE) : répond toujours "FIN-DU-MOCK". usage: mock_api.py <port> <log>
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
port, logp = int(sys.argv[1]), sys.argv[2]
def ev(t, d): return f"event: {t}\ndata: {json.dumps(d)}\n\n".encode()
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(b"{}")
    def do_POST(self):
        n = int(self.headers.get("content-length", 0)); body = json.loads(self.rfile.read(n) or b"{}")
        open(logp, "a").write(f"POST {self.path} model={body.get('model')} stream={body.get('stream')}\n")
        if "count_tokens" in self.path:
            self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(b'{"input_tokens":10}'); return
        msg = {"id":"msg_mock","type":"message","role":"assistant","model":body.get("model"),"content":[],"stop_reason":None,"stop_sequence":None,"usage":{"input_tokens":10,"output_tokens":1}}
        if not body.get("stream"):
            msg["content"]=[{"type":"text","text":"FIN-DU-MOCK"}]; msg["stop_reason"]="end_turn"
            self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(json.dumps(msg).encode()); return
        self.send_response(200); self.send_header("content-type","text/event-stream"); self.end_headers()
        self.wfile.write(ev("message_start",{"type":"message_start","message":msg}))
        self.wfile.write(ev("content_block_start",{"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}))
        self.wfile.write(ev("content_block_delta",{"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"FIN-DU-MOCK"}}))
        self.wfile.write(ev("content_block_stop",{"type":"content_block_stop","index":0}))
        self.wfile.write(ev("message_delta",{"type":"message_delta","delta":{"stop_reason":"end_turn","stop_sequence":None},"usage":{"output_tokens":3}}))
        self.wfile.write(ev("message_stop",{"type":"message_stop"}))
ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
