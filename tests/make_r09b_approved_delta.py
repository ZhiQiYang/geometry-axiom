#!/usr/bin/env python3
"""Apply / freeze the approved R09b text (issue #44 comment 7064656541).

Inputs are independent of the adopted file: the exact GitHub comment body of
#44 comment 7064656541 (ChatGPT, "R09b r2 Q1-A + Q2-A, seven format
alignments, complete landing candidate"; approved by the user in #44 comment
7073161164 with the words "核可 R09b") and the released R13 axiom blob
2b2fda3f.  Sections 4-6 of the comment contain exactly eleven ```text fences;
they are the complete text to write (17 normative changes).  Section 3 gives
the operation and base position of each fence and the LF rule:

* replacements replace exactly the listed base lines (line terminators kept);
* the five appended segments of existing clauses follow the original last
  line after one LF;
* the three new clause groups follow the original last line after two LFs;
* the separators that already follow those lines are kept.

Fence text is used byte for byte; nothing outside the fences is written.

    # write 公理層.md from the R13 blob (refuses unless section 7 fingerprints match)
    python3 tests/make_r09b_approved_delta.py --comment-json <7064656541.json> --write-axiom
    # freeze tests/fixtures/r09b-approved-delta.json against the clause commit
    python3 tests/make_r09b_approved_delta.py --comment-json <7064656541.json> --approved-commit <sha>

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
AXIOM = ROOT / "公理層.md"
OUT = ROOT / "tests/fixtures/r09b-approved-delta.json"
BODY_SHA256 = "17703c53c158611acce0eff54d8743a2f84c4425ff35b56a3214e973105f3ef3"
BEFORE_COMMIT = "883e68688f6480a5f1de6e86e6a056cc20339cb9"
BEFORE_BLOB = "2b2fda3f6450707a6aea998d255079dd40b0dd85"
BEFORE_SHA256 = "3628b16ba37fc84e193a57fb8523a6290882c8e4a005382beb74faba392645a0"
BEFORE_BYTES = 368061
# Section 7 of the comment: fingerprints of the complete in-memory candidate.
AFTER_SHA256 = "480708e9b2547b31bd29164bc0310cb69007d9112d6b3bc4376d5c9a7b1bcecd"
AFTER_BYTES = 387655
AFTER_BLOB = "3d30411cc29bd7d0b86a82bcb62d3639388f89bc"
KEPT_BYTES = 366207
KEPT_SHA256 = "768783193c0d0122f537a2ab94e9ccc7fd4cdc1da7a38d9e32c6a4d6c733bf7f"

# Section 3 position table: (label, fence index, op, base first line, base last line,
# expected start of first line, expected end of last line, expected start of the
# line that follows the edited region / next clause).
#   op "replace": base lines first..last are replaced by the fence.
#   op "append":  fence follows base line `last` after one LF.
#   op "new":     fence follows base line `last` after two LFs.
PLAN = (
    ("R57", 0, "replace", 2725, 2733, "R57 身分比對：", "不提交，即使五態名稱仍相同亦然。",
     2734, "R58 外部觀察值的採用："),
    ("D60", 1, "replace", 1154, 1154, "  R8 拆出的新片、匯入的新卡片均為新存在期",
     "本層不記錄「由誰拆出／複製」的衍生關係。", None, None),
    ("D62", 2, "append", 1178, 1178,
     "同一份專案經保留專案身分的複製或分支後，複製當下已存在的記號是兩邊共享的存在期；",
     "其後各自新配的記號不相同（D61）。", 1180, "**D63 保存的空間模型"),
    ("D63", 3, "append", 1193, 1193, None,
     "之後來源資料改變，只使核對紀錄過期或缺失，不改寫模型的來源快照或結果包。",
     1195, "**D64 網格卡片引用"),
    ("I72", 4, "append", 2043, 2043,
     "    核對完整專案或其方案快照本身的程序（例如方案的隔離驗證）",
     "其結果只用於核對該專案，不得寫入交換格式或模型來源快照。", 2045, "I73 空間模型納入拉伸件守門"),
    ("R53", 5, "append", 2670, 2670, "    本條只定首版三種型別的配號；",
     "D28 字串 id）的配號另案。", 2672, "R54 網格草稿生命週期"),
    ("R58", 6, "append", 2740, 2740, None, "兩種入口的確認均不能互相冒充。",
     2742, "**R58a 補資料的明示採用與原子提交（宿主契約 H）**："),
    ("§四身分帳排除項", 7, "replace", 2892, 2894, "- 身分帳（D59–R58）第一版只涵蓋七種身分鍵",
     "以及停用身分帳，均未定案，不得據此實作。", None, None),
    ("D65／D66／D67", 8, "new", 1201, 1201, None,
     "對調只交換兩個 fieldId 的軸對應，不交換其他軸設定、線索引、cell 錨點或世界框架。",
     1203, "## 二、構造保證的不變量（入口守門員；非法物件建不出來）"),
    ("I75／I76／I77", 9, "new", 2062, 2062, None,
     "只有重建、只有刪除前的宣告，或只處理部分引用者，均按 I38 整包拒絕並指名未處理者。",
     2064, "## 三、推演規則（寫死的行為，不靠測試）"),
    ("R61／R62／R63", 10, "new", 2799, 2799, None,
     "舊直接值、ParameterRef 及 legacy-finite 定義原樣可讀，不以兩個引用碰巧同卡就自動合成整卡來源。",
     2801, "## 四、明確不在本層"),
)
FENCE_HEADS = ("R57 身分比對：", "  R8 拆出的新片", "D62 附加段：", "D63 附加段：",
               "    I72 附加段：", "    R53 附加段：", "    R58 附加段：", "- 身分帳（D59–R58）",
               "**D65 來源使用項（SourceSlot）**：", "I75 重新關聯證據守門：",
               "R61 非延續來源的重新關聯：")
# Normative changes per fence: R57, D60, five appended segments, the exclusion item
# and three new clauses in each of the three groups.
CHANGES = (1, 1, 1, 1, 1, 1, 1, 1, 3, 3, 3)


def require(condition, message):
    if not condition:
        raise SystemExit("R09B_DELTA: " + message)


def git_blob(spec):
    return subprocess.run(["git", "-C", str(ROOT), "cat-file", "blob", spec],
                          check=True, capture_output=True).stdout


def blob_id(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fences(body):
    """The ```text fences of sections 4-6, verbatim (no trailing LF)."""
    lo = body.index("\n## 四、")
    hi = body.index("\n## 七、")
    require(body.count("\n## 四、") == 1 and body.count("\n## 七、") == 1, "section headings")
    lines = body[lo:hi].split("\n")
    out, cur = [], None
    for line in lines:
        if cur is None:
            if line == "```text":
                cur = []
            else:
                require(not line.startswith("```"), "unexpected fence opener: " + line)
        elif line == "```":
            out.append("\n".join(cur))
            cur = None
        else:
            require(not line.startswith("```"), "nested fence")
            cur.append(line)
    require(cur is None, "unterminated fence")
    require(len(out) == 11, "expected 11 text fences in sections 4-6, got %d" % len(out))
    for n, (text, head) in enumerate(zip(out, FENCE_HEADS)):
        require(text.startswith(head), "fence %d does not start with %r" % (n + 1, head))
        require(text and not text.endswith("\n") and "\r" not in text, "fence %d edges" % (n + 1))
    return out


def derive(body, before):
    boxes = fences(body)
    text = before.decode("utf-8")
    require("\r" not in text and text.endswith("\n"), "base must be LF text")
    lines = text.split("\n")  # lines[k-1] is base line k; last element is '' after final LF
    checks, blocks = [], []
    used = set()
    for label, fi, op, first, last, start, end, nxt, nxt_start in PLAN:
        require(fi not in used, "fence reused")
        used.add(fi)
        pre = lines[first - 1:last]
        if start is not None:
            require(pre[0].startswith(start), "%s: base line %d starts %r" % (label, first, pre[0][:40]))
        require(pre[-1].endswith(end), "%s: base line %d ends %r" % (label, last, pre[-1][-40:]))
        if nxt is not None:
            require(lines[nxt - 1].startswith(nxt_start),
                    "%s: base line %d starts %r" % (label, nxt, lines[nxt - 1][:40]))
            gap = lines[last:nxt - 1]
            require(all(g == "" for g in gap), "%s: lines between %d and %d not blank" % (label, last, nxt))
        if op == "replace" and label == "R57":
            require(len(pre) == 9, "R57 must be nine lines")
        if op == "replace" and label.startswith("§四"):
            require(len(pre) == 3, "exclusion item must be three lines")
        checks.append({"label": label, "fence": fi + 1, "op": op, "baseLines": [first, last],
                       "firstLine": pre[0], "lastLine": pre[-1],
                       "nextLine": nxt, "nextLineText": lines[nxt - 1] if nxt else None})
    # apply bottom-up so earlier line numbers stay valid
    for label, fi, op, first, last, *_ in sorted(PLAN, key=lambda p: -p[3]):
        box = boxes[fi]
        if op == "replace":
            lines[first - 1:last] = box.split("\n")
        elif op == "append":
            lines[last:last] = box.split("\n")
        else:
            lines[last:last] = [""] + box.split("\n")
    after = "\n".join(lines)
    # string blocks for the frozen delta: old/new with enough context to be unique
    base_lines = text.split("\n")
    for label, fi, op, first, last, start, end, nxt, nxt_start in PLAN:
        box = boxes[fi]
        if op == "replace":
            old = "\n".join(base_lines[first - 1:last])
            new = box
            if label == "D60":  # keep the neighbouring lines so the line is unique
                old = "\n".join(base_lines[first - 2:last + 1])
                new = "\n".join([base_lines[first - 2], box, base_lines[last]])
        else:
            sep = "\n" if op == "append" else "\n\n"
            ctx = "\n".join(base_lines[last - 1:nxt])
            old = ctx
            new = base_lines[last - 1] + sep + box + "\n" + "\n".join(base_lines[last:nxt])
        require(text.count(old) == 1, "before anchor not unique: " + label)
        blocks.append({"label": label, "fence": fi + 1, "op": op, "old": old, "new": new})
    replay = text
    for b in blocks:
        replay = replay.replace(b["old"], b["new"], 1)
    require(replay == after, "string blocks do not reproduce the line-based application")
    for b in blocks:
        require(after.count(b["new"]) == 1, "after anchor not unique: " + b["label"])
    return boxes, checks, blocks, after.encode("utf-8")


def reverse(after, blocks):
    text = after.decode("utf-8")
    for b in reversed(blocks):
        require(text.count(b["new"]) == 1, "reverse anchor not unique: " + b["label"])
        text = text.replace(b["new"], b["old"], 1)
    return text.encode("utf-8")


def load(args):
    raw = Path(args.comment_json).read_bytes()
    body = json.loads(raw)["body"]
    require(sha(body.encode("utf-8")) == BODY_SHA256, "comment body changed")
    before = git_blob(BEFORE_BLOB)
    require(blob_id(before) == BEFORE_BLOB and sha(before) == BEFORE_SHA256
            and len(before) == BEFORE_BYTES, "base blob fingerprint")
    boxes, checks, blocks, forward = derive(body, before)
    require(len(forward) == AFTER_BYTES and sha(forward) == AFTER_SHA256
            and blob_id(forward) == AFTER_BLOB, "result does not match section 7 fingerprints: %d %s %s"
            % (len(forward), sha(forward), blob_id(forward)))
    require(reverse(forward, blocks) == before, "reversal does not restore the base blob")
    kept = preserved(before)
    require(len(kept) == KEPT_BYTES and sha(kept) == KEPT_SHA256,
            "preserved content outside the edited regions does not match section 7")
    return body, before, boxes, checks, blocks, forward


def preserved(before):
    """Base text outside the three replaced regions, in order (terminators kept)."""
    text = before.decode("utf-8")
    lines = text.split("\n")

    def offset(line):
        return sum(len(x) + 1 for x in lines[:line - 1])

    out, pos = [], 0
    for _label, _fi, op, first, last, *_ in sorted(PLAN, key=lambda p: p[3]):
        if op != "replace":
            continue
        start, end = offset(first), offset(last) + len(lines[last - 1])
        out.append(text[pos:start])
        pos = end
    out.append(text[pos:])
    return "".join(out).encode("utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-json", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write-axiom", action="store_true")
    mode.add_argument("--approved-commit")
    args = parser.parse_args()
    body, before, boxes, checks, blocks, forward = load(args)
    if args.write_axiom:
        current = AXIOM.read_bytes().replace(b"\r\n", b"\n")
        require(current in (before, forward), "公理層.md is neither the base nor the approved result")
        AXIOM.write_bytes(forward)
        print(json.dumps({"wrote": "公理層.md", "bytes": len(forward), "sha256": sha(forward),
                          "blob": blob_id(forward), "fences": len(boxes),
                          "changes": sum(CHANGES), "checks": checks}, ensure_ascii=False, indent=1))
        return 0
    approved = git_blob(args.approved_commit + ":公理層.md").replace(b"\r\n", b"\n")
    require(forward == approved, "approved text applied to the R13 blob does not equal the adopted file")
    delta = {
        "schema": "r09b-approved-delta/1",
        "beforeCommit": BEFORE_COMMIT,
        "approvedCommit": args.approved_commit,
        "beforeBlob": BEFORE_BLOB,
        "approvedBlob": blob_id(approved),
        "beforeSha256": sha(before),
        "approvedSha256": sha(approved),
        "sourceComment": "https://github.com/ZhiQiYang/geometry-axiom/issues/44#issuecomment-7064656541",
        "sourceCommentBodySha256": BODY_SHA256,
        "approvalComment": "https://github.com/ZhiQiYang/geometry-axiom/issues/44#issuecomment-7073161164",
        "draftApprovalComment": "https://github.com/ZhiQiYang/geometry-axiom/issues/44#issuecomment-7057035938",
        "normativeChanges": sum(CHANGES),
        "blocks": [dict(item=n + 1, **b) for n, b in enumerate(blocks)],
    }
    OUT.write_bytes((json.dumps(delta, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"out": str(OUT.relative_to(ROOT)), "blocks": len(blocks),
                      "sha256": sha(OUT.read_bytes()),
                      "approvedBlob": delta["approvedBlob"], "approvedSha256": delta["approvedSha256"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
