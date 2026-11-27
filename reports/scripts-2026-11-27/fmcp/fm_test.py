# usage: python -I fm_test.py <racine_skills> ; tout en mémoire.
# a) quickstart : backend SkillsDirectoryProvider + proxy ProxyProvider(skills=True), list_skills via le proxy
# b) backend qui renvoie en plus une entrée invalide (nom en majuscules) : ce que voit le client du proxy
# c) URI avec %2F dans le préfixe (accepté ?) et %2F dans un segment de fichier (refusé ?)
import asyncio, sys, logging, importlib.metadata as md
from fastmcp import FastMCP, Client
from fastmcp.server.providers.proxy import ProxyProvider
from fastmcp.skills.provider import SkillsDirectoryProvider
from fastmcp.skills import SkillsClientExtension, MCPSkill, ListSkillsResult, SkillFrontmatter
from fastmcp.skills.extension import SkillsExtension
logging.basicConfig(level=logging.WARNING, format="LOG %(levelname)s %(name)s: %(message)s", stream=sys.stdout)
print("fastmcp", md.version("fastmcp"))
INJECT = {"on": False}
orig = SkillsExtension._handle_list
async def patched(self, context, params):
    res = await orig(self, context, params)
    print("   [handler skills/list du serveur", self.server.name, "inject=", INJECT["on"], "]")
    if INJECT["on"] and self.server.name == "backend":
        bad = MCPSkill.model_construct(uri="skill://Bad/SKILL.md", frontmatter=SkillFrontmatter.model_construct(root={"name": "Bad", "description": "x"}), resources="dynamic")
        return ListSkillsResult.model_construct(skills=[*res.skills, bad], next_cursor=None)
    return res
SkillsExtension._handle_list = patched  # avant la création des serveurs : methods() capture le handler
backend = FastMCP("backend"); backend.add_provider(SkillsDirectoryProvider(sys.argv[1]))
proxy = FastMCP("proxy"); proxy.add_provider(ProxyProvider(lambda: Client(backend), skills=True))
async def listing(label):
    try:
        async with Client(proxy, extensions=[SkillsClientExtension()]) as c:
            sk = await c.list_skills()
            print(f"{label}: protocole={c.protocol_version} skills={[s.uri for s in sk]}")
    except Exception as e:
        print(f"{label}: EXCEPTION {type(e).__name__}: {str(e)[:200]}")
async def go():
    await listing("a) quickstart via proxy")
    INJECT["on"] = True
    await listing("b) backend + entrée invalide")
    INJECT["on"] = False
    for label, uri, files in [
        ("c1) %2F dans le préfixe", "skill://org/acme%2Fteam/review/SKILL.md", ["skill://org/acme%2Fteam/review/SKILL.md"]),
        ("c2) %2F dans un segment de fichier", "skill://acme/review/SKILL.md", ["skill://acme/review/SKILL.md", "skill://acme/review/a%2Fb.md"]),
        ("c3) .. encodé %2E%2E", "skill://acme/%2E%2E/review/SKILL.md", ["skill://acme/%2E%2E/review/SKILL.md"])]:
        d = {"uri": uri, "frontmatter": {"name": "review", "description": "d"}, "resources": [{"uri": f, "digest": "sha256:" + "0"*64, "size": 1} for f in files]}
        try: MCPSkill.model_validate(d); print(label, "-> accepté")
        except Exception as e: print(label, "-> refusé:", [l.strip() for l in str(e).splitlines() if "Value error" in l][:1])
asyncio.run(go())
