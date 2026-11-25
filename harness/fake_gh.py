#!/usr/bin/env python3
"""重演用的假 gh：只支援 workflow 用到的 `gh api` 形式。GET 讀 $FAKE_GH_DIR/get/ 夾具；POST／DELETE 記到 posted.jsonl。"""
import json, os, subprocess, sys

d = os.environ["FAKE_GH_DIR"]
args = sys.argv[1:]
assert args and args[0] == "api", args
args = args[1:]
method, jq, fields, path = "GET", None, {}, None
i = 0
while i < len(args):
    a = args[i]
    if a == "--method":
        method = args[i + 1]; i += 2
    elif a == "--jq":
        jq = args[i + 1]; i += 2
    elif a == "-F":
        k, v = args[i + 1].split("=", 1)
        fields[k] = open(v[1:], encoding="utf-8").read() if v.startswith("@") else v
        i += 2
    elif a == "--paginate":
        i += 1
    else:
        path = a; i += 1
if method == "GET":
    f = os.path.join(d, "get", path.replace("/", "__") + ".json")
    if not os.path.exists(f):
        print("gh: Not Found (HTTP 404)", file=sys.stderr); sys.exit(1)
    data = open(f, encoding="utf-8").read()
    if jq:
        sys.exit(subprocess.run(["jq", "-r", jq], input=data.encode()).returncode)
    sys.stdout.write(data); sys.exit(0)
with open(os.path.join(d, "posted.jsonl"), "a", encoding="utf-8") as f:
    f.write(json.dumps({"method": method, "path": path, "body": fields.get("body")}, ensure_ascii=False) + "\n")
if method == "POST":
    print(f"https://github.com/{path}#issuecomment-fake")
