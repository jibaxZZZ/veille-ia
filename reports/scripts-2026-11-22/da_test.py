# deepagents : edit_file sans read_file préalable, outils exposés au modèle, RemoveMessage(REMOVE_ALL_MESSAGES) sur le canal messages.
import deepagents, json
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, RemoveMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from deepagents import create_deep_agent
print("deepagents", deepagents.__version__)
SEEN = {}
class Fake(GenericFakeChatModel):
    def bind_tools(self, tools, **kw):
        SEEN["tools"] = tools
        return self
def ai_tool(name, args, i):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": f"c{i}", "type": "tool_call"}])
msgs = iter([
    ai_tool("write_file", {"file_path": "/notes.txt", "content": "bonjour monde\n"}, 1),
    AIMessage(content="ecrit"),
    ai_tool("edit_file", {"file_path": "/notes.txt", "old_string": "monde", "new_string": "Jibaxe"}, 2),
    AIMessage(content="FIN"),
])
agent = create_deep_agent(model=Fake(messages=msgs), checkpointer=InMemorySaver())
cfg = {"configurable": {"thread_id": "t1"}}
# Tour 1 : write_file ; tour 2 (nouvelle requête) : edit_file sans aucun read_file
agent.invoke({"messages": [HumanMessage("ecris")]}, cfg)
r = agent.invoke({"messages": [HumanMessage("modifie sans lire")]}, cfg)
for m in r["messages"]:
    if m.type == "tool": print(f"tool_result[{m.name}]:", str(m.content)[:120].replace("\n", " | "))
files = r.get("files", {})
f = files.get("/notes.txt")
print("contenu final /notes.txt:", (f["content"] if isinstance(f, dict) and isinstance(f.get("content"), str) else json.dumps(f)[:120]))
names = sorted(getattr(t, "name", None) or t.get("name") for t in SEEN["tools"])
print("outils exposés:", names)
print("execute exposé:", "execute" in names)
from deepagents.middleware import filesystem as fs
print("desc edit_file contient 'errors otherwise':", "errors otherwise" in fs.EDIT_FILE_TOOL_DESCRIPTION)
print("desc execute contient 'SandboxBackendProtocol':", "SandboxBackendProtocol" in fs.EXECUTE_TOOL_DESCRIPTION)
print("messages avant RemoveMessage:", len(agent.get_state(cfg).values["messages"]))
agent.update_state(cfg, {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), HumanMessage("repart de zero", id="h-new")]})
after = agent.get_state(cfg).values["messages"]
print("messages après REMOVE_ALL + 1 nouveau:", len(after), [m.content for m in after])
agent.update_state(cfg, {"messages": [RemoveMessage(id="id-inexistant")]})
print("RemoveMessage id inexistant -> messages:", len(agent.get_state(cfg).values["messages"]))
