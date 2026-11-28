# Serveur MCP stdio minimal : déclare l'extension skills et renvoie un catalogue vide.
import sys, json
for line in sys.stdin:
    msg = json.loads(line)
    if "id" not in msg:
        continue
    m = msg.get("method")
    if m == "initialize":
        res = {"protocolVersion": msg["params"]["protocolVersion"],
               "capabilities": {"extensions": {"io.modelcontextprotocol/skills": {}}},
               "serverInfo": {"name": "vide", "version": "0"}}
    elif m == "skills/list":
        res = {"skills": []}
    elif m == "ping":
        res = {}
    else:
        out = {"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32601, "message": "unknown " + str(m)}}
        print(json.dumps(out), flush=True); continue
    print(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": res}), flush=True)
