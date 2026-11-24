# usage: depr_test.py ; faux /v1/messages local (127.0.0.1:18951), puis messages.create sur plusieurs modèles :
# affiche les DeprecationWarning émis par le SDK et le modèle reçu par le serveur.
import json, threading, warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import anthropic
got = []
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        b = json.loads(self.rfile.read(int(self.headers["content-length"]))); got.append(b["model"])
        r = {"id": "msg_mock", "type": "message", "role": "assistant", "model": b["model"], "content": [{"type": "text", "text": "ok"}],
             "stop_reason": "end_turn", "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}}
        self.send_response(200); self.send_header("content-type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(r).encode())
threading.Thread(target=ThreadingHTTPServer(("127.0.0.1", 18951), H).serve_forever, daemon=True).start()
c = anthropic.Anthropic(api_key="fausse-cle-test", base_url="http://127.0.0.1:18951", max_retries=0)
print("anthropic", anthropic.__version__)
for m in ["claude-opus-4-5", "claude-opus-4-5-20251101", "claude-sonnet-4-5", "claude-3-opus-20240229", "claude-opus-4-0", "claude-mythos-preview", "claude-opus-4-8"]:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        r = c.messages.create(model=m, max_tokens=8, messages=[{"role": "user", "content": "x"}])
    dw = [str(x.message).splitlines()[0] for x in w if issubclass(x.category, DeprecationWarning)]
    print(f"{m:28} réponse={r.content[0].text} avertissement={dw[0] if dw else 'aucun'}")
