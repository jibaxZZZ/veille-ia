# usage: python lca_test.py ; faux serveur sur 127.0.0.1:18971 (lancé par case.sh). Aucune vraie API.
import asyncio, importlib.metadata as md, anthropic, httpx2
from langchain_anthropic import ChatAnthropic
from langchain_core.load import dumpd
U = "http://127.0.0.1:18971"; K = "fausse-cle-test"; M = "claude-sonnet-5-5"
print("langchain-anthropic", md.version("langchain-anthropic"), "anthropic", anthropic.__version__)
def step(nom, f):
    try: print(f"{nom}: {f()}")
    except Exception as e:
        ls = [l for l in str(e).splitlines() if l.strip()]; print(f"{nom}: EXCEPTION {type(e).__name__}: {' | '.join(ls[:2])[:260]}")
n = {"i": 0}
def bearer(req):  # jeton « rafraîchi » à chaque requête
    n["i"] += 1; req.headers["authorization"] = f"Bearer jeton-{n['i']}"; return req
step("a) quickstart", lambda: ChatAnthropic(model=M, base_url=U, api_key=K, max_retries=0).invoke("salut").content)
hc = anthropic.DefaultHttpxClient(auth=bearer)
def b():
    m = ChatAnthropic(model=M, base_url=U, api_key=K, max_retries=0, http_client=hc, default_headers={"x-model-header": "1"})
    r = [m.invoke("x").content, m.invoke("y").content]
    return f"{r} http_client fermé={hc.is_closed}"
step("b) http_client + auth par requête (2 appels)", b)
def c():
    ac = anthropic.DefaultAsyncHttpxClient(auth=bearer)
    m = ChatAnthropic(model=M, base_url=U, api_key=K, max_retries=0, http_async_client=ac)
    return asyncio.run(m.ainvoke("z")).content
step("c) http_async_client seul, appel async", c)
def c2():
    ac = anthropic.DefaultAsyncHttpxClient(auth=bearer)
    m = ChatAnthropic(model=M, base_url=U, api_key=K, max_retries=0, http_async_client=ac)
    return m.invoke("sync").content
step("c2) http_async_client seul, appel sync", c2)
def d():
    cl = anthropic.Anthropic(base_url=U, api_key=K, default_headers={"x-mine": "client-sdk"}, max_retries=0)
    m = ChatAnthropic(model=M, base_url="http://127.0.0.1:1", api_key="autre", client=cl, default_headers={"x-model-header": "1"})
    return m.invoke("d").content
step("d) client SDK complet (base_url/en-têtes du modèle ignorés ?)", d)
def d2():
    cl = anthropic.Anthropic(base_url=U, api_key=K, default_headers={"x-mine": "client-sdk"}, max_retries=0)
    m = ChatAnthropic(model=M, base_url="http://127.0.0.1:1", api_key="autre", client=cl, default_headers={"x-model-header": "1"}, max_tokens=1024)
    return f"max_tokens={m.max_tokens} -> {m.invoke('d2').content}"
step("d2) idem avec max_tokens=1024", d2)
def d3():
    cl = anthropic.Anthropic(base_url=U, api_key=K, max_retries=0, timeout=60)
    m = ChatAnthropic(model=M, client=cl, api_key=K)
    return f"max_tokens={m.max_tokens} -> {m.invoke('d3').content}"
step("d3) client SDK avec timeout=60, max_tokens par défaut", d3)
step("d4) max_tokens par défaut du modèle sans client", lambda: ChatAnthropic(model=M, api_key=K).max_tokens)
step("e1) client + http_client", lambda: ChatAnthropic(model=M, api_key=K, client=anthropic.Anthropic(api_key=K), http_client=hc))
step("e2) anthropic_proxy + http_client", lambda: ChatAnthropic(model=M, api_key=K, anthropic_proxy="http://127.0.0.1:9", http_client=hc))
step("e3) http_client httpx (ancienne lib)", lambda: ChatAnthropic(model=M, base_url=U, api_key=K, max_retries=0, http_client=__import__("httpx").Client()).invoke("e3").content)
step("f) sérialisation", lambda: sorted(k for k in dumpd(ChatAnthropic(model=M, api_key=K, http_client=hc, client=None))["kwargs"]))
