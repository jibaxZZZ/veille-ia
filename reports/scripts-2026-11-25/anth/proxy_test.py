# A/B anthropic 2.13.0 vs 2.14.0 : quel serveur reçoit la requête selon proxy=, trust_env et les variables *_PROXY.
# Trois faux serveurs locaux répondent directement (aucun relais) : CIBLE (base_url), PROXY-ENV (HTTP_PROXY), PROXY-ARG (proxy=).
# Les variables *_PROXY sont posées par ce script avec des valeurs de test (lancé sous env -i).
import json, os, sys, threading, asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import anthropic
from anthropic import DefaultHttpxClient, DefaultAsyncHttpxClient
PORTS = {"CIBLE": 18941, "PROXY-ENV": 18942, "PROXY-ARG": 18943}
def mk(name):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_POST(self):
            self.rfile.read(int(self.headers.get("content-length", 0)))
            body = json.dumps({"id":"msg_x","type":"message","role":"assistant","model":"m","content":[{"type":"text","text":f"{name} (chemin={self.path[:45]})"}],"stop_reason":"end_turn","stop_sequence":None,"usage":{"input_tokens":1,"output_tokens":1}}).encode()
            self.send_response(200); self.send_header("content-type","application/json"); self.send_header("content-length",str(len(body))); self.end_headers(); self.wfile.write(body)
    return H
for n, p in PORTS.items():
    threading.Thread(target=ThreadingHTTPServer(("127.0.0.1", p), mk(n)).serve_forever, daemon=True).start()
ENVP, ARGP, BASE = "http://127.0.0.1:18942", "http://127.0.0.1:18943", "http://127.0.0.1:18941"
def setenv(no_proxy=None):
    for k in ("HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","NO_PROXY","http_proxy","https_proxy","all_proxy","no_proxy"): os.environ.pop(k, None)
    os.environ["HTTP_PROXY"] = ENVP
    if no_proxy: os.environ["NO_PROXY"] = no_proxy
def call(kw):
    c = anthropic.Anthropic(api_key="fausse-cle-test", base_url=BASE, max_retries=0, http_client=DefaultHttpxClient(**kw))
    return c.messages.create(model="m", max_tokens=5, messages=[{"role":"user","content":"x"}]).content[0].text
async def acall(kw):
    c = anthropic.AsyncAnthropic(api_key="fausse-cle-test", base_url=BASE, max_retries=0, http_client=DefaultAsyncHttpxClient(**kw))
    r = await c.messages.create(model="m", max_tokens=5, messages=[{"role":"user","content":"x"}]); return r.content[0].text
CASES = [
    ("A défaut, HTTP_PROXY posé", {}, None, False),
    ("B proxy=PROXY-ARG, HTTP_PROXY posé", {"proxy": ARGP}, None, False),
    ("C trust_env=False, HTTP_PROXY posé", {"trust_env": False}, None, False),
    ("D proxy=PROXY-ARG, NO_PROXY=127.0.0.1", {"proxy": ARGP}, "127.0.0.1", False),
    ("E proxy=PROXY-ARG + mounts all://127.0.0.1:18941=None", {"proxy": ARGP, "mounts": {"all://127.0.0.1:18941": None}}, None, False),
    ("E2 proxy=PROXY-ARG + mounts all://127.0.0.1=None (forme de la doc)", {"proxy": ARGP, "mounts": {"all://127.0.0.1": None}}, None, False),
    ("F async proxy=PROXY-ARG, HTTP_PROXY posé", {"proxy": ARGP}, None, True),
    ("G async trust_env=False, HTTP_PROXY posé", {"trust_env": False}, None, True),
]
print("anthropic", anthropic.__version__)
for label, kw, np, is_async in CASES:
    setenv(np)
    try: r = asyncio.run(acall(dict(kw))) if is_async else call(dict(kw))
    except Exception as e: r = f"ERREUR {type(e).__name__}: {str(e)[:120]}"
    print(f"{label:55s} -> {r}")
