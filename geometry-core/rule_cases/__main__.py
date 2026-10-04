"""Run only the six built-in cases, retain receipts in a host-selected output file."""
import argparse
import json
from pathlib import Path

from .catalog import cases
from .executor import NativeExecutor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--case", action="append", dest="selected")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    definitions = cases()
    known = {c["caseId"] for c in definitions}
    if args.selected and (set(args.selected) - known or len(args.selected) != len(set(args.selected))):
        parser.error("Select distinct built-in case IDs")
    selected = [c for c in definitions if not args.selected or c["caseId"] in args.selected]
    executor = NativeExecutor(args.binary)
    receipts = [executor.run(c, project_id="standalone-rule-cases", generation=0) for c in selected]
    args.output.write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for receipt in receipts:
        print(receipt["caseId"], receipt["status"], receipt.get("reason", ""))
    return 0 if all(r["status"] == "passed" for r in receipts) else 2


if __name__ == "__main__":
    raise SystemExit(main())
