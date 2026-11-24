# Faux /v1/messages (SSE). Mode "noname" : 1er appel renvoie un tool_use dont le nom est vide,
# appels suivants renvoient le texte "FIN-DU-MOCK". Mode "nokey" : idem mais sans clé "name". Mode "ok" : toujours le texte.
# usage: mock_api.py <port> <log> <mode>
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
port, logp, mode = int(sys.argv[1]), sys.argv[2], sys.argv[3]
state = {"n": 0}
def ev(t, d): return f"event: {t}\ndata: {json.dumps(d)}\n\n".encode()
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        open(logp, "a").write(f"GET {self.path}\n")
        self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(b'{"data":[]}')
    def do_HEAD(self):
        open(logp, "a").write(f"HEAD {self.path}\n"); self.send_response(200); self.end_headers()
    def do_POST(self):
        n = int(self.headers.get("content-length", 0)); body = json.loads(self.rfile.read(n) or b"{}")
        if "count_tokens" in self.path:
            self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(b'{"input_tokens":10}'); return
        msgs = body.get("messages", [])
        last = msgs[-1]["content"] if msgs else ""
        tr = [b for m in msgs if m.get("role") == "user" and isinstance(m.get("content"), list) for b in m["content"] if isinstance(b, dict) and b.get("type") == "tool_result"]
        state["n"] += 1
        open(logp, "a").write(f"POST {self.path} n={state['n']} tool_result={json.dumps(tr)[:200] if tr else '-'}\n")
        msg = {"id":"msg_mock","type":"message","role":"assistant","model":body.get("model"),"content":[],"stop_reason":None,"stop_sequence":None,"usage":{"input_tokens":10,"output_tokens":1}}
        self.send_response(200); self.send_header("content-type","text/event-stream"); self.end_headers()
        self.wfile.write(ev("message_start",{"type":"message_start","message":msg}))
        if mode in ("noname", "nokey") and not tr:
            blk = {"type":"tool_use","id":"toolu_mock1","name":"","input":{}}
            if mode == "nokey": del blk["name"]
            self.wfile.write(ev("content_block_start",{"type":"content_block_start","index":0,"content_block":blk}))
            self.wfile.write(ev("content_block_delta",{"type":"content_block_delta","index":0,"delta":{"type":"input_json_delta","partial_json":"{}"}}))
            self.wfile.write(ev("content_block_stop",{"type":"content_block_stop","index":0}))
            self.wfile.write(ev("message_delta",{"type":"message_delta","delta":{"stop_reason":"tool_use","stop_sequence":None},"usage":{"output_tokens":3}}))
        else:
            self.wfile.write(ev("content_block_start",{"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}))
            self.wfile.write(ev("content_block_delta",{"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"FIN-DU-MOCK"}}))
            self.wfile.write(ev("content_block_stop",{"type":"content_block_stop","index":0}))
            self.wfile.write(ev("message_delta",{"type":"message_delta","delta":{"stop_reason":"end_turn","stop_sequence":None},"usage":{"output_tokens":3}}))
        self.wfile.write(ev("message_stop",{"type":"message_stop"}))
ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
