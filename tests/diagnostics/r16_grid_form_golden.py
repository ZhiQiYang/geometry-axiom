"""Import P4541's official Chromium artifact; never guess count or cost.

The existing importer verifies GitHub artifact provenance, source identity,
count and real elapsed time. This wrapper preserves every inherited fragment
byte and emits the aggregate projection outside the checkout for review.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
FRAGMENTS = ROOT / "geometry-web/cdp_sections.d"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error("use an external artifact directory")
    output.mkdir(parents=True, exist_ok=False)
    inherited = {p.name: p.read_bytes() for p in FRAGMENTS.glob("*.json") if p.name != "P4541.json"}
    cmd = ["node", "geometry-web/canvas_registry.js", "import-cost", "--id", "P4541",
           "--artifact", str(args.artifact.resolve()), "--artifact-id", args.artifact_id]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True)
    (output / "import.stdout.log").write_bytes(result.stdout)
    (output / "import.stderr.log").write_bytes(result.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)
    current = {p.name: p.read_bytes() for p in FRAGMENTS.glob("*.json") if p.name != "P4541.json"}
    if current != inherited:
        raise SystemExit("R16GF_INHERITED_FRAGMENTS_CHANGED")
    row = json.loads((FRAGMENTS / "P4541.json").read_bytes())
    golden = subprocess.run(["node", "geometry-web/canvas_registry.js", "golden"], cwd=ROOT, capture_output=True)
    (output / "golden.stderr.log").write_bytes(golden.stderr)
    if golden.returncode:
        # Other still-pending independent sections must also be measured; do
        # not relax the aggregate reader to manufacture a partial acceptance.
        raise SystemExit(golden.returncode)
    (output / "golden.json").write_bytes(golden.stdout)
    receipt = {"section": "P4541", "assertions": row["assertions"], "cost": row["cost"],
               "provenance": row["provenance"], "inheritedFragmentsUnchanged": True,
               "goldenBytes": len(golden.stdout), "goldenSha256": hashlib.sha256(golden.stdout).hexdigest(),
               "acceptance": False, "note": "Official measurement import; full two-shard acceptance remains required."}
    (output / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
