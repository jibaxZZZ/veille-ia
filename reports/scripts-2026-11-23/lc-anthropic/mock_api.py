# Faux /v1/messages HTTP/1.1 keep-alive, JSON ou SSE. Le stop_reason est lu dans le dernier message
# utilisateur sous la forme "STOP=<raison>" (défaut end_turn). usage: mock_api.py <port> <log>
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
port, logp = int(sys.argv[1]), sys.argv[2]
def ev(t, d): return f"event: {t}\ndata: {json.dumps(d)}\n\n".encode()
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def send(self, ctype, data):
        self.send_response(200); self.send_header("content-type", ctype); self.send_header("content-length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        n = int(self.headers.get("content-length", 0)); body = json.loads(self.rfile.read(n) or b"{}")
        last = body["messages"][-1]["content"]; text = last if isinstance(last, str) else json.dumps(last)
        stop = text.split("STOP=")[1].split()[0].strip('"') if "STOP=" in text else "end_turn"
        open(logp, "a").write(f"POST {self.path} client_port={self.client_address[1]} stream={body.get('stream')} stop={stop}\n")
        msg = {"id":"msg_mock","type":"message","role":"assistant","model":body.get("model"),"content":[],"stop_reason":None,"stop_sequence":None,"usage":{"input_tokens":10,"output_tokens":1}}
        if not body.get("stream"):
            msg["content"]=[{"type":"text","text":"FIN-DU-MOCK"}]; msg["stop_reason"]=stop
            return self.send("application/json", json.dumps(msg).encode())
        out = ev("message_start",{"type":"message_start","message":msg})
        out += ev("content_block_start",{"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}})
        out += ev("content_block_delta",{"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"FIN-DU-MOCK"}})
        out += ev("content_block_stop",{"type":"content_block_stop","index":0})
        out += ev("message_delta",{"type":"message_delta","delta":{"stop_reason":stop,"stop_sequence":None},"usage":{"output_tokens":3}})
        out += ev("message_stop",{"type":"message_stop"})
        self.send("text/event-stream", out)
ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
