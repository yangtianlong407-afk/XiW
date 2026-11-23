"""开发辅助：本地假模型，用来在没 key 时把 ask.py 整条链路跑通。

启动：python tools/mock_llm.py 8801
模式：MOCK_MODE = normal | flaky | fail | empty
    normal 正常返回一句话
    flaky  第一次 500，第二次 200（测重试）
    fail   一直 500（测重试后失败）
    empty  200 但 content 为空（测空返回）
然后：
    $env:LLM_API_KEY="test"
    $env:LLM_BASE_URL="http://127.0.0.1:8801"
    python ask.py ask "技术答疑找谁？"
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

MODE = os.environ.get("MOCK_MODE", "normal")
_hits = {"n": 0}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 路径第一段可以指定模式：/flaky/chat/completions
        parts = [p for p in self.path.split("/") if p]
        mode = parts[0] if parts and parts[0] in {"normal", "flaky", "fail", "empty", "auth"} else MODE

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        _hits["n"] += 1
        print(f"[mock:{mode}] 第 {_hits['n']} 次请求，问题片段：{body.get('messages', [{}])[-1].get('content', '')[:30]}...", flush=True)

        if mode == "auth":
            self._send(401, {"error": "invalid api key"})
            return
        if mode == "fail" or (mode == "flaky" and _hits["n"] == 1):
            self._send(500, {"error": "mock server error"})
            return
        if mode == "empty":
            self._send(200, {"choices": [{"message": {"content": ""}}], "usage": {"prompt_tokens": 10, "completion_tokens": 0}})
            return

        self._send(200, {
            "choices": [{"message": {"content": "（模拟回答）技术答疑是蔡僮、蔡凯、饶宇轩。来源：docs/FAQ.md:4"}}],
            "usage": {"prompt_tokens": 123, "completion_tokens": 45},
        })

    def _send(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8801
    print(f"mock LLM on http://127.0.0.1:{port}  mode={MODE}", flush=True)
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()

