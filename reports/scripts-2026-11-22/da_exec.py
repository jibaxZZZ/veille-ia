# Description de l'outil execute réellement envoyée au modèle avec un backend shell local.
import sys, deepagents
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
SEEN = {}
class Fake(GenericFakeChatModel):
    def bind_tools(self, tools, **kw):
        SEEN["tools"] = tools; return self
agent = create_deep_agent(model=Fake(messages=iter([AIMessage(content="ok")])), backend=LocalShellBackend(root_dir=sys.argv[1]))
agent.invoke({"messages": [HumanMessage("x")]})
ex = [t for t in SEEN["tools"] if (getattr(t, "name", None) or t.get("name")) == "execute"][0]
d = getattr(ex, "description", None) or ex.get("description")
print("deepagents", deepagents.__version__, "| execute exposé: True | lignes de description:", len(d.splitlines()))
print("dernière ligne:", d.strip().splitlines()[-1][:150])
