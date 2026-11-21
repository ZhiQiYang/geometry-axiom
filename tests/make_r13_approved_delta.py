#!/usr/bin/env python3
"""Derive tests/fixtures/r13-approved-delta.json from the approved R13 C/D text.

Inputs are independent of the adopted file: the exact GitHub comment body of
#43 comment 6932710590 (candidate full text, sections 2-5) and the released
R03 axiom blob.  The two words approved in #43 comment 7057035577 are the only
substitutions.  The script refuses to write unless applying the derived blocks
to the R03 blob reproduces the adopted R13 blob byte for byte and reversing
them restores the R03 blob.

    python3 tests/make_r13_approved_delta.py --comment-json <6932710590.json>

The comment JSON is the GitHub REST response for that comment; only its
``body`` field is read and its SHA-256 is pinned below.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests/fixtures/r13-approved-delta.json"
BODY_SHA256 = "ccf70e3efb152004e7f3cb71c01548d89bac55a2774a7745d69e6da5467d1803"
BEFORE_COMMIT = "73f31618a84d4feb6fdb526a9f419c24270a0d90"
BEFORE_BLOB = "8666ea7765415eba4dd9927fd36a3575f9cf1cdc"
AMENDMENTS = (
    ("R13 補資料與核對擴充的作用域：", "GEO-198 補資料與核對擴充的作用域："),
    ("本包不替 R09b 作決定", "本包不替 #44 未採納的身分帳擴充作決定"),
)


def require(condition, message):
    if not condition:
        raise SystemExit("R13_DELTA: " + message)


def git_blob(spec):
    return subprocess.run(["git", "-C", str(ROOT), "cat-file", "blob", spec],
                          check=True, capture_output=True).stdout


def blob_id(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def section(body, start, end):
    i = body.index(start)
    return body[i:body.index(end, i)]


def quotes(text):
    groups, current = [], []
    for line in text.split("\n"):
        if line.startswith("> "):
            current.append(line[2:])
        elif current:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def clause(text):
    marker = "新增全文：**"
    i = text.index(marker) + len(marker)
    return text[i:text.index("**白話", i)].strip()


def derive(body, before):
    s21 = quotes(section(body, "### 2.1", "### 2.2"))
    s22 = quotes(section(body, "### 2.2", "### 2.3"))
    s23 = quotes(section(body, "### 2.3", "### 2.4"))
    s24 = quotes(section(body, "### 2.4", "## 三"))
    require([len(g) for g in s21] == [1, 1, 1] and [len(g) for g in s22] == [1, 1]
            and [len(g) for g in s23] == [1, 1] and len(s24) == 2, "unexpected candidate layout")
    index_add = s21[2][0]
    require(index_add.count(AMENDMENTS[0][0]) == 1, "first amendment anchor")
    index_add = index_add.replace(*AMENDMENTS[0])
    names = ("D51a", "D51b", "D51c", "I63a", "I63b", "I63c", "R58a", "R58b")
    ends = ("### D51b", "### D51c", "## 四", "### I63b", "### I63c", "## 五", "### R58b", "## 六")
    added = {name: clause(section(body, "### " + name, end)) for name, end in zip(names, ends)}
    require(added["R58b"].count(AMENDMENTS[1][0]) == 1, "second amendment anchor")
    added["R58b"] = added["R58b"].replace(*AMENDMENTS[1])
    text = before.decode("utf-8")
    r58_old = "\n".join(("    " if k else "") + line for k, line in enumerate(s24[0]))
    blocks = [
        ("2.1 分層索引導句", s21[0][0], s21[1][0]),
        ("2.1 分層索引新增段", "R58、R59、R60。\n\n## 一、定義（公理）",
         "R58、R59、R60。\n\n" + index_add + "\n\n## 一、定義（公理）"),
        ("2.2 D51 專案層資料句", s22[0][0], s22[1][0]),
        ("3 D51a／D51b／D51c", "不隨專案保存。\n\nD⟨FT1⟩ 模板生成配方",
         "不隨專案保存。\n\n" + "\n\n".join(added[n] for n in names[:3]) + "\n\nD⟨FT1⟩ 模板生成配方"),
        ("2.3 D63 末段", s23[0][0] + "\n\n", s23[0][0] + "\n\n" + s23[1][0] + "\n\n"),
        ("4 I63a／I63b／I63c", "\n\nI64 首房起步交易",
         "\n\n" + "\n\n".join(added[n] for n in names[3:6]) + "\n\nI64 首房起步交易"),
        ("2.4 R58 替代全文＋5 R58a／R58b", r58_old,
         "\n".join(s24[1]) + "\n\n" + added["R58a"] + "\n\n" + added["R58b"]),
    ]
    for label, old, new in blocks:
        require(text.count(old) == 1, "before anchor not unique: " + label)
        text = text.replace(old, new, 1)
    return [{"item": n + 1, "label": label, "old": old, "new": new}
            for n, (label, old, new) in enumerate(blocks)], text.encode("utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-json", required=True)
    parser.add_argument("--approved-commit", required=True)
    args = parser.parse_args()
    body = json.loads(Path(args.comment_json).read_bytes())["body"]
    require(hashlib.sha256(body.encode("utf-8")).hexdigest() == BODY_SHA256, "comment body changed")
    before = git_blob(BEFORE_BLOB)
    approved = git_blob(args.approved_commit + ":公理層.md").replace(b"\r\n", b"\n")
    blocks, forward = derive(body, before)
    require(forward == approved, "approved text applied to R03 blob does not equal the adopted file")
    text = approved.decode("utf-8")
    for block in reversed(blocks):
        require(text.count(block["new"]) == 1, "after anchor not unique: " + block["label"])
        text = text.replace(block["new"], block["old"], 1)
    require(text.encode("utf-8") == before, "reversal does not restore the R03 blob")
    delta = {
        "schema": "r13-approved-delta/1",
        "beforeCommit": BEFORE_COMMIT,
        "approvedCommit": args.approved_commit,
        "beforeBlob": BEFORE_BLOB,
        "approvedBlob": blob_id(approved),
        "beforeSha256": hashlib.sha256(before).hexdigest(),
        "approvedSha256": hashlib.sha256(approved).hexdigest(),
        "sourceComment": "https://github.com/ZhiQiYang/geometry-axiom/issues/43#issuecomment-6932710590",
        "sourceCommentBodySha256": BODY_SHA256,
        "scopeComment": "https://github.com/ZhiQiYang/geometry-axiom/issues/43#issuecomment-6938368110",
        "amendmentComment": "https://github.com/ZhiQiYang/geometry-axiom/issues/43#issuecomment-7057035577",
        "amendments": [list(pair) for pair in AMENDMENTS],
        "blocks": blocks,
    }
    OUT.write_bytes((json.dumps(delta, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"out": str(OUT.relative_to(ROOT)), "blocks": len(blocks),
                      "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
                      "approvedBlob": delta["approvedBlob"], "approvedSha256": delta["approvedSha256"]}))


if __name__ == "__main__":
    sys.exit(main())
