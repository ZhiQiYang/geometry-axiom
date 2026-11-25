#!/usr/bin/env python3
"""假 Anthropic Messages API（只供本機重演，不連外、不花錢）。

情境檔（JSON）：{"steps": ["bash 指令", ...], "report": "最終報告文字", "hang_at": 整數或 null}
每收到一個帶 tools 的請求，依對話裡已有的 tool_result 數決定回第幾步：
  i < len(steps)  → 回一個 Bash tool_use
  i == hang_at    → 不回應（模擬卡住，供「CLI 被中斷」）
  否則            → 回最終報告文字
所有請求記到 log 檔（只記路徑、模型、tool_result 數與 x-api-key 前 8 字）。
"""
import json, sys, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

port, scenario_path, log_path = int(sys.argv[1]), sys.argv[2], sys.argv[3]


def sse(events):
    return "".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events).encode()


def last_tool_output(msgs):
    for m in reversed(msgs):
        for b in (m.get("content") if isinstance(m.get("content"), list) else []):
            if isinstance(b, dict) and b.get("type") == "tool_result":
                c = b.get("content")
                if isinstance(c, list):
                    c = "".join(x.get("text", "") for x in c if isinstance(x, dict))
                return str(c)[:2000]
    return None


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        self.send_response(404); self.end_headers()

    def do_POST(self):
        n = int(self.headers.get("content-length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        sc = json.load(open(scenario_path, encoding="utf-8"))
        msgs = body.get("messages") or []
        results = sum(1 for m in msgs if isinstance(m.get("content"), list)
                      for b in m["content"] if isinstance(b, dict) and b.get("type") == "tool_result")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"path": self.path, "model": body.get("model"), "tools": len(body.get("tools") or []), "tool_names": [t.get("name") for t in (body.get("tools") or [])],
                                "tool_results": results, "key8": (self.headers.get("x-api-key") or "")[:8],
                                "last_tool_output": last_tool_output(msgs)}, ensure_ascii=False) + "\n")
        if not self.path.startswith("/v1/messages") or "count_tokens" in self.path:
            self.send_response(200); self.send_header("content-type", "application/json"); self.end_headers()
            self.wfile.write(b'{"input_tokens": 10}'); return
        steps = sc.get("steps") or []
        if not body.get("tools"):
            block = {"type": "text", "text": "ok"}; stop = "end_turn"
        elif sc.get("hang_at") is not None and results == sc["hang_at"]:
            time.sleep(3600); return
        elif results < len(steps):
            block = {"type": "tool_use", "id": f"toolu_{uuid.uuid4().hex[:20]}", "name": "Bash",
                     "input": {"command": steps[results], "description": "replay step"}}
            stop = "tool_use"
        else:
            block = {"type": "text", "text": sc.get("report", "done")}; stop = "end_turn"
        mid = f"msg_{uuid.uuid4().hex[:20]}"
        usage = {"input_tokens": 100, "output_tokens": 20, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
        if not body.get("stream"):
            msg = {"id": mid, "type": "message", "role": "assistant", "model": body.get("model"), "content": [block],
                   "stop_reason": stop, "stop_sequence": None, "usage": usage}
            data = json.dumps(msg).encode()
            self.send_response(200); self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(data))); self.end_headers(); self.wfile.write(data); return
        start = dict(block)
        if block["type"] == "tool_use":
            start["input"] = {}; delta = {"type": "input_json_delta", "partial_json": json.dumps(block["input"])}
        else:
            start["text"] = ""; delta = {"type": "text_delta", "text": block["text"]}
        ev = [{"type": "message_start", "message": {"id": mid, "type": "message", "role": "assistant", "model": body.get("model"),
                                                     "content": [], "stop_reason": None, "stop_sequence": None, "usage": usage}},
              {"type": "content_block_start", "index": 0, "content_block": start},
              {"type": "content_block_delta", "index": 0, "delta": delta},
              {"type": "content_block_stop", "index": 0},
              {"type": "message_delta", "delta": {"stop_reason": stop, "stop_sequence": None}, "usage": {"output_tokens": 20}},
              {"type": "message_stop"}]
        data = sse(ev)
        self.send_response(200); self.send_header("content-type", "text/event-stream"); self.end_headers()
        self.wfile.write(data); self.wfile.flush()


ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
