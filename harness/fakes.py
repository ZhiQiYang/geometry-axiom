"""假 GitHub REST API 與假 OpenAI Responses API（同一個行程內的兩個 HTTP 伺服器）。"""
import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

REPO = "ZhiQiYang/geometry-axiom"
OWNER = {"login": "ZhiQiYang", "id": 59477728, "type": "User"}
BOT = {"login": "github-actions[bot]", "id": 41898282, "type": "Bot"}
OTHER = {"login": "mallory", "id": 1234567, "type": "User"}


class GitHubState:
    def __init__(self):
        self.lock = threading.Lock()
        self.comments = []       # {id, user, body, created_at, issue}
        self.branches = {"main": "a" * 40}
        self.runs = {"openai-worker.yml": [], "api-worker.yml": []}  # {id, status, display_title}
        self.artifacts = {}      # run_id -> [{id, name}]
        self.deleted_artifacts = []
        self.log = []
        self.next_id = 7300000000
        self.clock = 0

    def add_comment(self, issue, user, body):
        with self.lock:
            self.next_id += 1
            self.clock += 1
            c = {"id": self.next_id, "user": dict(user), "body": body, "issue": int(issue),
                 "created_at": f"2026-11-28T{12 + self.clock // 3600:02d}:{(self.clock // 60) % 60:02d}:{self.clock % 60:02d}Z",
                 "updated_at": None,
                 "html_url": f"https://github.com/{REPO}/issues/{issue}#issuecomment-{self.next_id}",
                 "issue_url": f"https://api.github.com/repos/{REPO}/issues/{issue}"}
            c["updated_at"] = c["created_at"]
            self.comments.append(c)
            return c


class GHHandler(BaseHTTPRequestHandler):
    state = None

    def log_message(self, *a):
        pass

    def send(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        st = self.state
        u = urlparse(self.path)
        q = parse_qs(u.query)
        per = int(q.get("per_page", ["30"])[0])
        page = int(q.get("page", ["1"])[0])
        st.log.append(("GET", u.path + ("?" + u.query if u.query else "")))
        if not self.headers.get("Authorization", "").startswith(("Bearer ", "token ")):
            return self.send(401, {"message": "no token"})
        m = re.fullmatch(rf"/repos/{REPO}/issues/(\d+)/comments", u.path)
        if m:
            items = [c for c in st.comments if c["issue"] == int(m.group(1))]
            return self.send(200, items[(page - 1) * per: page * per])
        m = re.fullmatch(rf"/repos/{REPO}/issues/comments/(\d+)", u.path)
        if m:
            for c in st.comments:
                if c["id"] == int(m.group(1)):
                    return self.send(200, c)
            return self.send(404, {"message": "Not Found"})
        m = re.fullmatch(rf"/repos/{REPO}/branches/(.+)", u.path)
        if m:
            sha = st.branches.get(m.group(1))
            return self.send(200, {"name": m.group(1), "commit": {"sha": sha}}) if sha else self.send(404, {"message": "Branch not found"})
        m = re.fullmatch(rf"/repos/{REPO}/actions/workflows/([^/]+)/runs", u.path)
        if m:
            status = q.get("status", [None])[0]
            runs = [r for r in st.runs.get(m.group(1), []) if status is None or r["status"] == status]
            return self.send(200, {"total_count": len(runs), "workflow_runs": runs[(page - 1) * per: page * per]})
        m = re.fullmatch(rf"/repos/{REPO}/actions/runs/(\d+)/artifacts", u.path)
        if m:
            arts = st.artifacts.get(m.group(1), [])
            return self.send(200, {"total_count": len(arts), "artifacts": arts[(page - 1) * per: page * per]})
        return self.send(404, {"message": f"fake: {u.path}"})

    def do_POST(self):
        st = self.state
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(n) or b"{}")
        st.log.append(("POST", u.path))
        m = re.fullmatch(rf"/repos/{REPO}/issues/(\d+)/comments", u.path)
        if m:
            c = st.add_comment(m.group(1), BOT, body.get("body", ""))
            return self.send(201, c)
        return self.send(404, {"message": "fake"})

    def do_DELETE(self):
        st = self.state
        u = urlparse(self.path)
        st.log.append(("DELETE", u.path))
        m = re.fullmatch(rf"/repos/{REPO}/actions/artifacts/(\d+)", u.path)
        if m:
            st.deleted_artifacts.append(int(m.group(1)))
            for arts in st.artifacts.values():
                arts[:] = [a for a in arts if a["id"] != int(m.group(1))]
            self.send_response(204)
            self.end_headers()
            return
        return self.send(404, {"message": "fake"})


class OpenAIState:
    def __init__(self):
        self.credit_left = 10 ** 9   # 還能成功的請求數；0 之後回 429 credit_balance_exhausted
        self.requests = 0


class OAHandler(BaseHTTPRequestHandler):
    state = None

    def log_message(self, *a):
        pass

    def do_POST(self):
        st = self.state
        n = int(self.headers.get("Content-Length", "0"))
        req = json.loads(self.rfile.read(n) or b"{}")
        st.requests += 1
        if st.credit_left <= 0:
            data = json.dumps({"error": {"message": "You have run out of credits.", "type": "insufficient_quota",
                                         "param": None, "code": "credit_balance_exhausted"}}).encode()
            self.send_response(429)
        else:
            st.credit_left -= 1
            data = json.dumps({
                "id": f"resp_{st.requests}", "object": "response", "created_at": int(time.time()),
                "model": req.get("model"), "status": "completed", "service_tier": "default",
                "parallel_tool_calls": True, "tool_choice": "auto", "tools": [],
                "reasoning": {"effort": (req.get("reasoning") or {}).get("effort")},
                "output": [{"type": "message", "id": f"msg_{st.requests}", "role": "assistant", "status": "completed",
                            "content": [{"type": "output_text", "text": "## 結論\n重演用的假報告：沒有改檔。", "annotations": []}]}],
                "usage": {"input_tokens": 1000, "input_tokens_details": {"cached_tokens": 0},
                          "output_tokens": 50, "output_tokens_details": {"reasoning_tokens": 10}, "total_tokens": 1050},
            }).encode()
            self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def serve(handler_cls, state):
    h = type("H", (handler_cls,), {"state": state})
    srv = ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"
