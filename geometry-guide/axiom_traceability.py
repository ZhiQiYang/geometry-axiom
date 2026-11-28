#!/usr/bin/env python3
"""Rebuild the axiom / implementation / judge index without inventing coverage.

Status fragments are reviewed source inputs, not receipts. Text references are
only candidates. This tool never runs a test, imports product code, edits an
axiom, fills a missing status, or promotes a candidate to reviewed evidence.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

from axiom_matrix import parse_clauses

STATUS_SCHEMA = "geometry-axiom-status/1"
REPORT_SCHEMA = "geometry-axiom-triad/1"
STATES = {"unreviewed", "implemented", "partial", "unimplemented", "not_applicable"}
KINDS = {"implementation", "test", "mutation", "unsupported", "context"}
ROOTS = ("geometry-core", "geometry-app", "geometry-templates", "geometry-web", "tests")
SUFFIXES = {".c", ".h", ".inc", ".py", ".js", ".cjs", ".mjs", ".html", ".scene"}
EXCLUDED_PARTS = {"node_modules", "vendor", "evidence", "release-evidence", "__pycache__", ".git"}


class Invalid(ValueError):
    pass


def reject(code, detail):
    raise Invalid(code + ": " + str(detail))


def normalized(path):
    return path.read_bytes().replace(b"\r\n", b"\n")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def text(path):
    return normalized(path).decode("utf-8")


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def unique_keys(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            reject("X4_STATUS_SCHEMA", "duplicate JSON key " + key)
        out[key] = value
    return out


def read_json(path):
    try:
        return json.loads(text(path), object_pairs_hook=unique_keys)
    except (UnicodeError, json.JSONDecodeError) as exc:
        reject("X4_STATUS_SCHEMA", str(path.name) + ": " + str(exc))


def safe_file(root, relative):
    if (not isinstance(relative, str) or not relative or "\\" in relative
            or PurePosixPath(relative).is_absolute()
            or any(p in ("", ".", "..") for p in relative.split("/"))
            or ":" in relative):
        reject("X4_PATH_UNSAFE", relative)
    path = root
    for part in relative.split("/"):
        path = path / part
        if path.is_symlink():
            reject("X4_PATH_UNSAFE", relative)
    if not path.is_file():
        reject("X4_INPUT_MISSING", relative)
    return path


def clauses(root):
    source = text(safe_file(root, "公理層.md"))
    parsed = parse_clauses(source)
    result = {}
    for cid, line, title, body in parsed:
        if cid in result:
            reject("X4_CLAUSE_DUPLICATE", cid)
        result[cid] = {"id": cid, "line": line, "title": title,
                       "body_sha256": digest(body.encode("utf-8"))}
    if not result:
        reject("X4_CLAUSE_EMPTY", "公理層.md")
    return result


def evidence(root, raw):
    required = {"kind", "path", "anchor", "source_sha256"}
    if (not isinstance(raw, dict) or set(raw) != required
            or not isinstance(raw["kind"], str) or raw["kind"] not in KINDS
            or not isinstance(raw["anchor"], str) or not raw["anchor"].strip()
            or not isinstance(raw["source_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", raw["source_sha256"])):
        reject("X4_STATUS_SCHEMA", "evidence requires kind/path/anchor/source_sha256")
    path = safe_file(root, raw["path"])
    body = text(path)
    anchor = raw["anchor"]
    if body.count(anchor) != 1:
        reject("X4_EVIDENCE_ANCHOR", raw["path"] + ": anchor must occur exactly once")
    actual = digest(body.encode("utf-8"))
    return dict(raw, line=body.count("\n", 0, body.index(anchor)) + 1,
                current_source_sha256=actual, fresh=actual == raw["source_sha256"])


def status_markers(root, ax):
    folder = root / "geometry-guide/axiom-status.d"
    if folder.is_symlink() or (root / "geometry-guide").is_symlink():
        reject("X4_PATH_UNSAFE", "geometry-guide/axiom-status.d")
    result = {}
    for path in sorted(folder.glob("*.json")):
        relative = path.relative_to(root).as_posix()
        data = read_json(safe_file(root, relative))
        if (not isinstance(data, dict) or set(data) != {"schema", "entries"}
                or data["schema"] != STATUS_SCHEMA or not isinstance(data["entries"], list)):
            reject("X4_STATUS_SCHEMA", relative)
        for item in data["entries"]:
            required = {"id", "body_sha256", "status", "reason", "evidence"}
            if (not isinstance(item, dict) or set(item) != required
                    or not isinstance(item["id"], str)
                    or not isinstance(item["status"], str) or item["status"] not in STATES
                    or not isinstance(item["reason"], str) or not item["reason"].strip()
                    or not isinstance(item["evidence"], list)):
                reject("X4_STATUS_SCHEMA", relative)
            cid = item["id"]
            if cid not in ax:
                reject("X4_STATUS_UNKNOWN_CLAUSE", cid)
            if cid in result:
                reject("X4_STATUS_DUPLICATE", cid)
            if item["body_sha256"] != ax[cid]["body_sha256"]:
                reject("X4_STATUS_STALE_CLAUSE", cid)
            links = [evidence(root, row) for row in item["evidence"]]
            kinds = {row["kind"] for row in links}
            if item["status"] in {"implemented", "partial"} and "implementation" not in kinds:
                reject("X4_STATUS_SCHEMA", cid + ": implementation evidence required")
            if item["status"] == "unimplemented" and (
                    "implementation" in kinds or not kinds.intersection({"unsupported", "context"})):
                reject("X4_STATUS_SCHEMA", cid + ": unimplemented requires scoped absence evidence")
            result[cid] = dict(item, evidence=links, marker=relative)
    missing = sorted(set(ax) - set(result))
    if missing:
        reject("X4_STATUS_MISSING", ", ".join(missing))
    return result


def selected_path(relative):
    parts = PurePosixPath(relative).parts
    if any(part in EXCLUDED_PARTS for part in parts):
        return False
    if len(parts) > 2 and parts[0] == "geometry-web" and parts[1] == "docs":
        return False
    return (PurePosixPath(relative).suffix in SUFFIXES and
            (parts[0] in ROOTS or relative == "current_geometry.c"
             or (len(parts) == 1 and relative.endswith(".scene"))))


def inventory(root):
    """Include new unstaged source files too; sparse missing sources are errors."""
    try:
        proc = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--cached",
                               "--others", "--exclude-standard"], capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        reject("X4_INVENTORY_FAILED", str(exc))
    if proc.returncode == 0:
        paths = proc.stdout.decode("utf-8").split("\0")
        method = "git-tracked-and-unignored-new-files"
    else:
        # Standalone exported trees and small test fixtures remain usable. The
        # report records this weaker inventory; no Git provenance is invented.
        paths = [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()]
        method = "filesystem-export"
    paths = sorted({p for p in paths if p and selected_path(p)})
    return [(p, text(safe_file(root, p))) for p in paths], method


def role(path):
    parts = PurePosixPath(path).parts
    name = parts[-1]
    if ("mutation" in name or "mutant" in name or "withdrawal" in name
            or name == "mutate.py" or name.startswith("mutate_")):
        return "mutation"
    if (path.endswith(".scene") or "tests" in parts or "oracle" in parts or "canvas_sections" in parts
            or "card-reference" in parts or name.startswith(("test_", "cdp_test"))
            or name.endswith(("_test.js", "_harness.c", "_browser_check.js", "_browser_test.py"))):
        return "test"
    return "implementation"


def python_scopes(body):
    try:
        tree = ast.parse(body)
    except SyntaxError:
        return [], None
    scopes = [(node.lineno, node.end_lineno, node.name) for node in ast.walk(tree)
              if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    return scopes, tree


def symbol_at(scopes, line):
    matches = [row for row in scopes if row[0] <= line <= row[1]]
    return min(matches, key=lambda row: row[1] - row[0])[2] if matches else "(file)"


def javascript_scopes(body):
    """Conservative lexical labels, not execution or assertion coverage.

    Only a literal test/it name followed on the same line by a braced callback
    is labelled. Other JavaScript remains a path/line candidate with (file).
    """
    scopes = []
    lines = body.splitlines()
    for offset, line in enumerate(lines):
        match = re.search(r"\b(?:test|it)\(\s*(['\"])(.*?)\1[^\n]*?=>\s*\{", line)
        if not match:
            continue
        depth = 1
        end = offset
        # Limit the label to a balanced block. Literals and comments on later
        # lines can make this ambiguous; ambiguity falls back to file scope.
        first = line[match.end():]
        for end in range(offset, len(lines)):
            value = first if end == offset else lines[end]
            value = re.sub(r"(['\"])(?:\\.|(?!\1).)*?\1|//.*", "", value)
            depth += value.count("{") - value.count("}")
            if depth <= 0:
                scopes.append((offset + 1, end + 1, match.group(2)))
                break
    return scopes


def dict_constants(node):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
        pairs = [(kw.arg, kw.value) for kw in node.keywords if kw.arg]
    elif isinstance(node, ast.Dict):
        pairs = [(key.value, value) for key, value in zip(node.keys, node.values)
                 if isinstance(key, ast.Constant) and isinstance(key.value, str)]
    else:
        return {}
    result = {}
    for key, value in pairs:
        try:
            result[key] = ast.literal_eval(value)
        except (ValueError, TypeError):
            pass
    return result


def candidate_index(sources, ids):
    pattern = re.compile(r"(?<![A-Za-z0-9_])(?:" + "|".join(map(re.escape, ids)) + r")(?![A-Za-z0-9_])")
    hits = {cid: {kind: [] for kind in ("implementation", "test", "mutation")} for cid in ids}
    unbased, scene_owners = [], {}
    for path, body in sources:
        kind = role(path)
        scopes, tree = python_scopes(body) if path.endswith(".py") else ([], None)
        if path.endswith((".js", ".cjs", ".mjs")):
            scopes = javascript_scopes(body)
        file_ids = set()
        for line, value in enumerate(body.splitlines(), 1):
            for cid in sorted(set(pattern.findall(value))):
                file_ids.add(cid)
                hits[cid][kind].append({"path": path, "line": line,
                                       "symbol": symbol_at(scopes, line),
                                       "basis": "token-reference-unreviewed"})
        if kind == "implementation" and not file_ids:
            unbased.append({"path": path, "classification": "no-direct-axiom-reference",
                            "review_required": True})
        if tree is None:
            continue
        for node in ast.walk(tree):
            item = dict_constants(node)
            if (isinstance(item.get("id"), str) and isinstance(item.get("desc"), str)
                    and ("old" in item or "retired" in item)):
                for cid in sorted(set(pattern.findall(item["desc"]))):
                    hits[cid]["mutation"].append({"path": path, "line": node.lineno,
                                                 "symbol": item["id"], "target": item.get("file", "current_geometry.c"),
                                                 "basis": "mutation-definition-unrun"})
            if path == "tests/run_tests.py" and isinstance(item.get("scene"), str):
                scene_owners.setdefault(item["scene"], []).append(
                    {"path": path, "line": node.lineno, "symbol": "run_one(" + item["scene"] + ")",
                     "basis": "registered-scene-judge-unrun", "expected": item.get("expect")})
    for kinds in hits.values():
        for item in list(kinds["test"]):
            if item["path"] in scene_owners:
                kinds["test"].extend(scene_owners[item["path"]])
        for key, rows in kinds.items():
            unique = {json.dumps(row, sort_keys=True): row for row in rows}
            kinds[key] = sorted(unique.values(), key=lambda row: (row["path"], row["line"], row["symbol"], row["basis"]))
    return hits, unbased


def load_findings(root, ax):
    relative = "geometry-guide/axiom-review-findings.json"
    if not (root / relative).exists():
        return []
    data = read_json(safe_file(root, relative))
    if (not isinstance(data, dict) or set(data) != {"schema", "findings"}
            or data["schema"] != "geometry-axiom-findings/1" or not isinstance(data["findings"], list)):
        reject("X4_FINDING_SCHEMA", relative)
    seen, result = set(), []
    for row in data["findings"]:
        if (not isinstance(row, dict) or set(row) != {"id", "clauses", "clause_sha256", "kind", "decision", "state", "reason", "evidence"}
                or not isinstance(row["id"], str) or not row["id"] or row["id"] in seen
                or not isinstance(row["clauses"], list) or not row["clauses"]
                or any(not isinstance(cid, str) or cid not in ax for cid in row["clauses"])
                or not isinstance(row["clause_sha256"], dict) or set(row["clause_sha256"]) != set(row["clauses"])
                or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
                       for value in row["clause_sha256"].values())
                or not isinstance(row["kind"], str)
                or row["kind"] not in {"test_spec_mismatch", "implementation_spec_mismatch", "traceability_defect"}
                or not isinstance(row["decision"], str)
                or row["decision"] not in {"change_test", "change_implementation", "change_tool", "spec_candidate"}
                or not isinstance(row["state"], str)
                or row["state"] not in {"open", "fixed_in_this_slice", "legacy_scope_pending_new_capability"}
                or not isinstance(row["reason"], str) or not row["reason"].strip()
                or not isinstance(row["evidence"], list)):
            reject("X4_FINDING_SCHEMA", relative)
        seen.add(row["id"])
        links = [evidence(root, ev) for ev in row["evidence"]]
        clause_fresh = all(row["clause_sha256"][cid] == ax[cid]["body_sha256"] for cid in row["clauses"])
        current = clause_fresh and all(link["fresh"] for link in links)
        result.append(dict(row, declared_state=row["state"], clause_fresh=clause_fresh,
                           state=row["state"] if current else "review_required", evidence=links))
    return result


def report(root):
    ax = clauses(root)
    markers = status_markers(root, ax)
    sources, method = inventory(root)
    hits, unbased = candidate_index(sources, ax)
    findings = load_findings(root, ax)
    rows = []
    for cid, clause in ax.items():
        marker = markers[cid]
        fresh = all(row["fresh"] for row in marker["evidence"])
        effective = marker["status"] if fresh else "unreviewed"
        kinds = {row["kind"] for row in marker["evidence"] if row["fresh"]}
        gaps = []
        if effective == "unimplemented":
            gaps.append("axiom_without_implementation")
        if effective == "partial":
            gaps.append("partial_implementation")
        if effective == "unreviewed":
            gaps.append("semantic_review_pending")
        if not fresh:
            gaps.append("stale_review_evidence")
        if "implementation" in kinds and "test" not in kinds:
            gaps.append("implementation_without_reviewed_test")
        if hits[cid]["implementation"] and not hits[cid]["test"] and "test" not in kinds:
            gaps.append("implementation_reference_without_test_reference")
        if not hits[cid]["implementation"] and "implementation" not in kinds:
            gaps.append("no_implementation_reference")
        if not hits[cid]["test"] and "test" not in kinds:
            gaps.append("no_test_reference")
        if not hits[cid]["mutation"] and "mutation" not in kinds:
            gaps.append("no_mutation_reference")
        own_findings = [row["id"] for row in findings if cid in row["clauses"]]
        gaps.extend(row["kind"] for row in findings if cid in row["clauses"] and row["state"] != "fixed_in_this_slice")
        rows.append(dict(clause, declared_status=marker["status"], effective_status=effective,
                         reason=marker["reason"], marker=marker["marker"], reviewed_evidence=marker["evidence"],
                         candidates=hits[cid], gaps=sorted(set(gaps)), findings=own_findings))
    input_hashes = {path: digest(body.encode("utf-8")) for path, body in sources}
    for path in [root / "公理層.md", *sorted((root / "geometry-guide/axiom-status.d").glob("*.json")),
                 *list((root / "geometry-guide").glob("axiom-review-findings.json"))]:
        input_hashes[path.relative_to(root).as_posix()] = digest(normalized(path))
    # Reviewed documents and tools may intentionally lie outside the automatic
    # candidate inventory. They still affect the result and belong to its hash.
    for record in [*markers.values(), *findings]:
        for link in record["evidence"]:
            input_hashes[link["path"]] = link["current_source_sha256"]
    counts = {state: sum(row["effective_status"] == state for row in rows) for state in sorted(STATES)}
    generators = {name: digest(normalized(Path(__file__).with_name(name)))
                  for name in ("axiom_matrix.py", "axiom_traceability.py")}
    return {"schema": REPORT_SCHEMA, "clauses": len(rows), "counts": counts, "rows": rows,
            "source_digest": digest(json_bytes({"inputs": input_hashes, "generators": generators})),
            "input_sha256": input_hashes, "generator_sha256": generators,
            "scan_scope": {"inventory": method, "roots": list(ROOTS), "root_files": ["current_geometry.c", "*.scene"],
                           "suffixes": sorted(SUFFIXES), "excluded_path_parts": sorted(EXCLUDED_PARTS),
                           "excluded_subtrees": ["geometry-web/docs"], "scanned_files": len(sources),
                           "limits": ["token references do not establish semantic coverage",
                                      "no test or mutation result is inferred from a definition",
                                      "source without a direct reference is a review candidate, not a violation",
                                      "absence of a reference is not evidence of L0",
                                      "only explicit reviewed status may classify product implementation",
                                      "this report does not assign product L4 or L5"]},
            "unbased_implementation_candidates": unbased, "findings": findings}


def markdown(data):
    def escape(value):
        return str(value).replace("|", "\\|").replace("\n", " ")

    def links(rows):
        # Full references, no silent truncation. JSON also preserves the symbol
        # and each candidate's weaker basis instead of calling it coverage.
        return "; ".join(escape(row["path"] + ":" + str(row["line"]) + " " + row.get("symbol", "")
                                + (" [來源已變]" if row.get("fresh") is False else ""))
                         for row in rows) or "—"

    out = ["# 公理條文 × 實作 × 測試／突變", "", "由 axiom_traceability.py 產生；不得手改。",
           "文字候選 ≠ 已實作／已測到。表中的狀態來自明列的人工審查來源；unreviewed 不等於 L0。",
           "沒有文字依據的檔案只列為待審；不能據此宣稱違反公理。未執行測試、未產生突變收據。", "",
           "來源閉包 SHA-256：`" + data["source_digest"] + "`；條文數：" + str(data["clauses"]), "",
           "| 條文 | 狀態／缺口 | 已審來源與理由 | 實作文字候選 | 測試文字候選 | 突變定義／文字候選 |",
           "|---|---|---|---|---|---|"]
    for row in data["rows"]:
        reviewed = "; ".join(ev["kind"] + " " + ev["path"] + ":" + str(ev["line"])
                              + (" [來源已變]" if not ev["fresh"] else "") for ev in row["reviewed_evidence"])
        out.append("| " + " | ".join([escape(row["id"] + " L" + str(row["line"]) + " " + row["title"]),
                                      escape(row["effective_status"] + ": " + ", ".join(row["gaps"])),
                                      escape(row["reason"] + " / " + reviewed),
                                      *(links(row["candidates"][kind]) for kind in ("implementation", "test", "mutation"))]) + " |")
    out.extend(["", "## 實作檔沒有直接條號的待審名單", "", "這不是『實作違反公理』的清單；包括一般宿主與呈現程式。", ""])
    out.extend("- " + row["path"] for row in data["unbased_implementation_candidates"])
    out.extend(["", "## 已核對的不一致與裁定", ""])
    for row in data["findings"]:
        out.extend(["### " + row["id"], "", ", ".join(row["clauses"]) + " · " + row["kind"] + " · " + row["state"],
                    "", row["decision"] + "：" + row["reason"],
                    "" if row["clause_fresh"] else "條文已變，舊裁定須重新核對。", "", links(row["evidence"]), ""])
    out.extend(["## 掃描限制", "", *("- " + limit for limit in data["scan_scope"]["limits"]), ""])
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--format", choices=("json", "md"), default="md")
    parser.add_argument("--check-status", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.check_status:
            ax = clauses(root)
            markers = status_markers(root, ax)
            data = {"schema": "geometry-axiom-status-check/1", "clauses": len(ax),
                    "markers": len(markers), "missing": []}
            sys.stdout.buffer.write(json_bytes(data))
        else:
            data = report(root)
            sys.stdout.buffer.write(json_bytes(data) if args.format == "json" else markdown(data).encode("utf-8"))
        return 0
    except (Invalid, OSError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
