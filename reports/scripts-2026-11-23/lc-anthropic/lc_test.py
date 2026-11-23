# usage: lc_test.py <port> <cas>  cas: finish | stream | loops | caller
import asyncio, sys, time, logging, importlib.metadata as m
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage
port, cas = sys.argv[1], sys.argv[2]
print("langchain-anthropic", m.version("langchain-anthropic"), "| cas:", cas)
def mk(): return ChatAnthropic(model="claude-opus-4-8", api_key="fausse-cle-test", base_url=f"http://127.0.0.1:{port}", max_retries=2)
keys = ("stop_reason", "finish_reason", "normalized_finish_reason", "finish_state")
if cas == "finish":
    for s in ["end_turn", "max_tokens", "tool_use", "pause_turn", "refusal", "model_context_window_exceeded", "inconnu_xyz"]:
        r = mk().invoke(f"STOP={s}")
        print(f"invoke STOP={s:31s} ->", {k: r.response_metadata.get(k) for k in keys})
elif cas == "stream":
    for s in ["end_turn", "max_tokens", "pause_turn"]:
        acc = None
        for c in mk().stream(f"STOP={s}"): acc = c if acc is None else acc + c
        print(f"stream STOP={s:11s} ->", {k: acc.response_metadata.get(k) for k in keys})
elif cas == "loops":
    logging.basicConfig(level=logging.WARNING)
    a, b = mk(), mk()
    print("même client httpx async pour 2 modèles :", a._async_client._client is b._async_client._client)
    for i, mdl in enumerate([a, b]):
        t = time.monotonic()
        try:
            r = asyncio.run(mdl.ainvoke("STOP=end_turn"))
            print(f"boucle {i+1} (modèle {'ab'[i]}): {r.content} en {time.monotonic()-t:.2f} s")
        except Exception as e:
            print(f"boucle {i+1}: ERREUR {type(e).__name__}: {e}")
elif cas == "caller":
    from langchain_anthropic.chat_models import _format_messages
    for caller in [{"type": "code_execution_20250825", "tool_id": "srvtoolu_x"}, {"type": "direct"}, None]:
        blk = {"type": "tool_search_tool_result", "tool_use_id": "srvtoolu_1", "index": 3,
               "content": {"type": "tool_search_tool_search_result", "tool_references": [{"type": "tool_reference", "tool_name": "meteo"}]}}
        if caller is not None: blk["caller"] = caller
        _, msgs = _format_messages([HumanMessage("q"), AIMessage(content=[blk])], model="claude-opus-4-8")
        out = msgs[1]["content"][0]
        print(f"caller entrée={caller} -> clés sorties={sorted(out)} caller={out.get('caller')}")
