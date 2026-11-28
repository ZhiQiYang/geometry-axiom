"""Verify/extract X2's frozen Git originals; never regenerate them with a writer."""
import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "tests/fixtures/project-save-history.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-history", action="store_true", help="Require the recorded Git commits locally; never fetch implicitly")
    parser.add_argument("--extract", type=Path, help="Write original .gcanvas bytes to a new directory for manual cold-open checks")
    args = parser.parse_args()
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    rows = data["fixtures"] + [data["futureFixture"]]
    if args.extract:
        args.extract.mkdir(parents=True, exist_ok=False)
    result = []
    for row in rows:
        source = row["source"]
        assert re.fullmatch(r"[a-f0-9]{40}", source["commit"])
        assert re.fullmatch(r"[a-z0-9-]+", row["id"])
        raw = gzip.decompress(base64.b64decode(row["gzipBase64"], validate=True))
        assert len(raw) == source["bytes"], row["id"] + ":bytes"
        assert hashlib.sha256(raw).hexdigest() == source["sha256"], row["id"] + ":sha256"
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        assert blob == source["blob"], row["id"] + ":blob"
        if args.verify_history:
            historical = subprocess.run(
                ["git", "show", source["commit"] + ":" + source["path"]],
                cwd=ROOT, env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
                check=True, capture_output=True, timeout=30,
            ).stdout
            assert historical == raw, row["id"] + ":historical-git-bytes"
        if args.extract:
            (args.extract / (row["id"] + ".gcanvas")).write_bytes(raw)
        result.append({"id": row["id"], "format": row["format"], "bytes": len(raw),
                       "gitBlob": blob, "historyVerified": args.verify_history})
    print(json.dumps({"verified": len(result), "historyVerified": args.verify_history, "files": result}, indent=2))


if __name__ == "__main__":
    main()
