"""Check the real R14-only CDP receipt without inventing a golden count.

This is an independent browser gate; it does not alter or certify the existing
full-canvas golden. The browser process exit status is supplied by PIPESTATUS.
"""
import argparse
import hashlib
import json
from pathlib import Path


FLAG = "GEOMETRY_R14_PANEL_ONLY"


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError("non-finite JSON value: " + value)


def check_log(raw, exit_code):
    problems, result = [], None
    receipt = {"schema": "geometry-r14-browser-receipt/1", "passed": False,
               "exitCode": exit_code, "logSha256": hashlib.sha256(raw).hexdigest(),
               "problems": problems}
    if type(exit_code) is not int or exit_code != 0:
        problems.append("Browser process did not exit 0")
    lines = [line[len(b"CDP_RESULT "):] for line in raw.splitlines()
             if line.startswith(b"CDP_RESULT ")]
    if len(lines) != 1:
        problems.append("Expected exactly one CDP_RESULT")
    else:
        try:
            result = json.loads(lines[0], object_pairs_hook=unique_object,
                                parse_constant=invalid_constant)
        except (ValueError, UnicodeError) as error:
            problems.append("Invalid CDP_RESULT JSON: " + str(error))
    if not isinstance(result, dict):
        problems.append("CDP_RESULT must be an object")
        return receipt
    receipt["observed"] = result
    if result.get("schema") != "geometry-cdp-result/1":
        problems.append("Unexpected CDP result schema")
    if result.get("completed") is not True or "fatal" in result:
        problems.append("Browser run did not complete successfully")
    scope = result.get("scope")
    if (not isinstance(scope, dict) or scope.get("mode") != "partial"
            or scope.get("filters") != [FLAG] or scope.get("modifiers") != []):
        problems.append("Scope must be the single R14-only partial run")
    if result.get("goldenCompare") != "not compared (partial mode)":
        problems.append("R14-only receipt must not claim full-canvas golden coverage")
    sections = result.get("sections")
    count = sections.get("P381") if isinstance(sections, dict) else None
    if (not isinstance(sections, dict) or set(sections) != {"P381"}
            or type(count) is not int or count <= 0):
        problems.append("Exactly the P381 section must contain real positive assertions")
    if result.get("sectionOrder") != ["P381"]:
        problems.append("P381 must be the only executed section")
    passed = result.get("passedAssertions")
    if type(passed) is not int or passed <= 0 or passed != count:
        problems.append("Passing assertion total must equal the observed P381 count")
    for field in ("failedAssertions", "uncaughtBrowserExceptions", "unexpectedBrowserExceptions"):
        if type(result.get(field)) is not int or result[field] != 0:
            problems.append(field + " must be an explicit zero")
    if result.get("skipped") != []:
        problems.append("No skipped groups are allowed")
    if result.get("sectionsFailed", {}) != {}:
        problems.append("No failed sections are allowed")
    receipt["passed"] = not problems
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--exit-code", type=int, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = check_log(args.log.read_bytes(), args.exit_code)
    except OSError as error:
        receipt = {"schema": "geometry-r14-browser-receipt/1", "passed": False,
                   "exitCode": args.exit_code, "problems": ["Cannot read browser log: " + str(error)]}
    receipt["sourceHead"] = args.commit
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
