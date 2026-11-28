"""Tests hors réseau de pydantic-ai(-harness) : détecteur de secrets et compaction qui échoue."""
import sys, importlib.metadata as md
from pydantic_ai import Agent
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel, AgentInfo

print("pydantic-ai-slim", md.version("pydantic-ai-slim"), "| harness", md.version("pydantic-ai-harness"))
mode = sys.argv[1]

if mode == "secrets":
    from pydantic_ai_harness.guardrails import detectors
    det = detectors.secret_data(only=["google_api_key"])
    cle50 = "AQ." + "Ab3_d-" * 8 + "Zz"          # 50 caractères après AQ.
    cas = {
        "AIza legacy (35)": "cle=AIza" + "B" * 35,
        "AQ. 50 car.": "cle=" + cle50,
        "AQ. 40 car. (plancher)": "cle=AQ." + "x" * 40,
        "AQ. 39 car. (sous le plancher)": "cle=AQ." + "x" * 39,
        "AQ. 200 car. (plafond)": "cle=AQ." + "y" * 200,
        "AQ. 201 car. (au-delà)": "cle=AQ." + "y" * 201,
        "nom pointé AQ.average_response_time": "metrique AQ.average_response_time ok",
        "dans du JSON": '{"key": "%s"}' % cle50,
    }
    for nom, texte in cas.items():
        r = det(texte)
        sortie = r.replacement if r.action == "replace" else "(inchangé)"
        print(f"  {nom:38} -> {r.action:7} | {str(sortie)[:60]}")
    sys.exit(0)

# --- compaction : le modèle principal appelle 6 fois un outil, puis répond ---
from pydantic_ai_harness.compaction import SummarizingCompaction, FallbackCompaction, SlidingWindowCompaction

appels_resume = {"n": 0}
def resumeur(messages, info: AgentInfo):
    appels_resume["n"] += 1
    return ModelResponse(parts=[TextPart("")])   # résumé vide : le modèle se comporte mal

tours = {"n": 0}
def principal(messages, info: AgentInfo):
    # compteur propre au faux modèle : ne dépend pas de l'historique, que la compaction peut couper
    nb_outils = tours["n"]; tours["n"] += 1
    if nb_outils < 6:
        return ModelResponse(parts=[ToolCallPart("lire", {"n": nb_outils}, tool_call_id=f"c{nb_outils}")])
    return ModelResponse(parts=[TextPart(f"FIN après {nb_outils} outils, {len(messages)} messages vus")])

summ = SummarizingCompaction(model=FunctionModel(resumeur), max_messages=6, keep_messages=2, retries=1)
if mode == "summarizing":
    caps = [summ]
elif mode == "fallback":
    caps = [FallbackCompaction([SummarizingCompaction(model=FunctionModel(resumeur), keep_messages=2, retries=1),
                                SlidingWindowCompaction(keep_messages=2)], max_tokens=150)]
agent = Agent(FunctionModel(principal), capabilities=caps)

@agent.tool_plain
def lire(n: int) -> str:
    return f"contenu {n} " + "bla " * 40

try:
    r = agent.run_sync("lis tout")
    print("  run terminé :", r.output)
    print("  messages dans l'historique final :", len(r.all_messages()))
except Exception as e:
    print("  RUN TUÉ :", type(e).__name__, str(e)[:200])
print("  appels au résumeur :", appels_resume["n"])
