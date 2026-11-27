# usage: python -I lcc_test.py ; modèle de chat factice dont seul le 1er chunk porte l'id fournisseur "resp_abc"
# (comme l'API Responses d'OpenAI). On regarde l'id de chaque chunk et du message final.
import asyncio, importlib.metadata as md
from typing import Any, Iterator, AsyncIterator
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessageChunk, AIMessage
from langchain_core.outputs import ChatGenerationChunk, ChatResult, ChatGeneration
from langchain_core.callbacks import BaseCallbackHandler
print("langchain-core", md.version("langchain-core"))
PARTS = [("Bon", "resp_abc"), ("jour", None), (" Jibaxe", None)]
class Fake(BaseChatModel):
    first_id: str | None = "resp_abc"
    @property
    def _llm_type(self): return "fake-resp"
    def _generate(self, messages, stop=None, run_manager=None, **kw):
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Bonjour Jibaxe", id=self.first_id))])
    def _stream(self, messages, stop=None, run_manager=None, **kw) -> Iterator[ChatGenerationChunk]:
        for i, (t, _) in enumerate(PARTS):
            c = ChatGenerationChunk(message=AIMessageChunk(content=t, id=self.first_id if i == 0 else None))
            if run_manager: run_manager.on_llm_new_token(t, chunk=c)
            yield c
    async def _astream(self, messages, stop=None, run_manager=None, **kw) -> AsyncIterator[ChatGenerationChunk]:
        for i, (t, _) in enumerate(PARTS):
            c = ChatGenerationChunk(message=AIMessageChunk(content=t, id=self.first_id if i == 0 else None))
            if run_manager: await run_manager.on_llm_new_token(t, chunk=c)
            yield c
class Tokens(BaseCallbackHandler):
    def __init__(self): self.ids = []
    def on_llm_new_token(self, token, *, chunk=None, **kw): self.ids.append(getattr(getattr(chunk, "message", None), "id", None))
def show(label, chunks):
    ids = [c.id for c in chunks]; pos = [getattr(c, "chunk_position", None) for c in chunks]
    final = chunks[0]
    for c in chunks[1:]: final = final + c
    print(f"{label}: ids des chunks={ids} positions={pos} | id final={final.id} | ids distincts={sorted(set(map(str, ids)))}")
m = Fake()
show("a) stream", list(m.stream("salut")))
async def a(): return [c async for c in m.astream("salut")]
show("b) astream", asyncio.run(a()))
h = Tokens(); r = Fake().invoke("salut", config={"callbacks": [h]})
print(f"c) invoke + callback de streaming: ids vus par le callback={h.ids} | id du message renvoyé={r.id}")
m2 = Fake(first_id=None)
show("d) aucun id fournisseur", list(m2.stream("salut")))
try:
    async def ev2():
        out = []
        async for e in m.astream_events("salut", version="v2"):
            if e["event"] == "on_chat_model_stream": out.append(e["data"]["chunk"].id)
        return out
    print("e) astream_events v2, ids des chunks:", asyncio.run(ev2()))
except Exception as e: print("e) EXCEPTION", type(e).__name__, str(e)[:150])
# f) LangGraph stream_mode="messages" : le nœud appelle model.invoke() (chemin invoke + callback de streaming de LangGraph)
from langgraph.graph import StateGraph, MessagesState, START
g = StateGraph(MessagesState)
g.add_node("llm", lambda s: {"messages": [m.invoke(s["messages"])]})
g.add_edge(START, "llm"); app = g.compile()
seen = [msg.id for msg, meta in app.stream({"messages": [("user", "salut")]}, stream_mode="messages")]
final = app.invoke({"messages": [("user", "salut")]})["messages"][-1].id
print(f"f) LangGraph messages: ids streamés={seen} | id du message dans l'état={final} | ids distincts={sorted(set(map(str, seen)))}")
