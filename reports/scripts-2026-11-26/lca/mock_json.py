# Faux /v1/messages non streamé : répond "REPONSE-MOCK" et consigne certains en-têtes de chaque requête.
# usage: mock_json.py <port> <log>
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
port, logp = int(sys.argv[1]), sys.argv[2]
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))) or b"{}")
        h = {k: self.headers.get(k) for k in ("authorization", "x-api-key", "x-mine", "x-model-header")}
        open(logp, "a").write(f"POST {self.path} {json.dumps({k: v for k, v in h.items() if v})}\n")
        out = {"id": "msg_mock", "type": "message", "role": "assistant", "model": body.get("model"), "content": [{"type": "text", "text": "REPONSE-MOCK"}],
               "stop_reason": "end_turn", "stop_sequence": None, "usage": {"input_tokens": 5, "output_tokens": 2}}
        b = json.dumps(out).encode(); self.send_response(200); self.send_header("content-type", "application/json"); self.send_header("content-length", str(len(b))); self.end_headers(); self.wfile.write(b)
ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
