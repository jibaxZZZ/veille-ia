# usage: python -I da_test.py <scenario> ; modèle factice (GenericFakeChatModel), aucun appel réseau.
# surrogates : write_file avec un surrogate isolé et une paire coupée, puis ls, glob, read_file (StateBackend par défaut)
# interrupt / interrupt-non / interrupt-async : backend dont glob appelle langgraph interrupt() (demande d'approbation), puis reprise Command(resume=...)
import sys, deepagents
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from deepagents import create_deep_agent
from deepagents.backends import StateBackend
print("deepagents", deepagents.__version__)
class Fake(GenericFakeChatModel):
    def bind_tools(self, tools, **kw): return self
def call(name, args, i): return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": f"c{i}", "type": "tool_call"}])
def tools_out(msgs):
    for m in msgs:
        if m.type == "tool": print(f"  tool_result[{m.name}]:", ascii(str(m.content))[:200])
cfg = {"configurable": {"thread_id": "t1"}}
if sys.argv[1] == "surrogates":
    seul, paire = "avant \ud83d apres", "rire 😀 fin"   # surrogate isolé ; paire U+1F600 coupée en 2 points de code
    msgs = iter([call("write_file", {"file_path": "/seul.txt", "content": seul}, 1),
                 call("write_file", {"file_path": "/paire.txt", "content": paire}, 2),
                 call("ls", {"path": "/"}, 3), call("glob", {"pattern": "*.txt"}, 4),
                 call("read_file", {"file_path": "/paire.txt"}, 5), AIMessage(content="FIN")])
    agent = create_deep_agent(model=Fake(messages=msgs), checkpointer=InMemorySaver())
    try:
        r = agent.invoke({"messages": [HumanMessage("ecris")]}, cfg)
        tools_out(r["messages"]); print("  dernier message:", r["messages"][-1].content)
        for p in ("/seul.txt", "/paire.txt"): print(f"  stocké {p}:", ascii(r["files"][p]["content"]))
    except Exception as e:
        print("  RUN INTERROMPU:", type(e).__name__, str(e)[:160])
        tools_out(agent.get_state(cfg).values.get("messages", []))
elif sys.argv[1].startswith("interrupt"):
    REP = "non" if sys.argv[1] == "interrupt-non" else "oui"
    class Gardé(StateBackend):
        def glob(self, pattern, path=None):
            ok = interrupt({"question": f"autoriser glob {pattern} sur {path} ?"})
            if ok != "oui": raise PermissionError("refusé par l'humain")
            return super().glob(pattern, path)
    msgs = iter([call("write_file", {"file_path": "/finance/board.md", "content": "x"}, 1),
                 call("glob", {"pattern": "**/*.md", "path": "/finance"}, 2), AIMessage(content="FIN")])
    agent = create_deep_agent(model=Fake(messages=msgs), backend=Gardé(), checkpointer=InMemorySaver())
    import asyncio
    if sys.argv[1] == "interrupt-async":   # chemin asynchrone : ainvoke -> aglob
        inv = lambda x: asyncio.run(agent.ainvoke(x, cfg))
    else:
        inv = lambda x: agent.invoke(x, cfg)
    r = inv({"messages": [HumanMessage("cherche")]})
    st = agent.get_state(cfg)
    print("  interruption en attente:", [i.value for i in st.interrupts] if st.interrupts else "aucune", "| next =", st.next)
    tools_out(r["messages"]); print("  dernier message:", r["messages"][-1].content)
    if st.interrupts:
        r = inv(Command(resume=REP))
        print(f"  après reprise resume={REP!r}:"); tools_out(r["messages"]); print("  dernier message:", r["messages"][-1].content)
