"""Import P1236's real official measurement and emit its deterministic golden.

First run Canvas section measurement with section=P1236 on the applied head.
Download the original artifact ZIP; this wrapper delegates provenance/source
verification, cost and assertion extraction to canvas_registry.js. It never
accepts a guessed count or modifies an existing section's declared count.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / "geometry-web/cdp_sections.d"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    prior = {p.name: p.read_bytes() for p in DIRECTORY.glob("*.json") if p.name != "P1236.json"}
    command = ["node", "geometry-web/canvas_registry.js", "import-cost", "--id", "P1236",
               "--artifact", str(args.artifact.resolve()), "--artifact-id", args.artifact_id]
    result = subprocess.run(command, cwd=ROOT, capture_output=True)
    (args.out / "import.stdout.log").write_bytes(result.stdout)
    (args.out / "import.stderr.log").write_bytes(result.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)
    if any((DIRECTORY / name).read_bytes() != data for name, data in prior.items()):
        raise SystemExit("D06 golden import changed an inherited section")
    result = subprocess.run(["node", "geometry-web/canvas_registry.js", "golden"], cwd=ROOT, capture_output=True)
    (args.out / "golden.stderr.log").write_bytes(result.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)
    # Artifact projection only, not the retired aggregate golden in the repo.
    (args.out / "golden.json").write_bytes(result.stdout)
    row = json.loads((DIRECTORY / "P1236.json").read_bytes())
    report = {"section": "P1236", "assertions": row["assertions"], "cost": row["cost"],
              "provenance": row["provenance"], "inheritedFragmentsUnchanged": True,
              "goldenBytes": len(result.stdout), "goldenSha256": hashlib.sha256(result.stdout).hexdigest(),
              "acceptance": False, "note": "Count/cost capture only; full two-shard acceptance remains required."}
    (args.out / "receipt.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
