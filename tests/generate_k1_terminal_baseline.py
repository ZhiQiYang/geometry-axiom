"""以獨立 main bridge 重建 K1 非 terminal 基線，絕不使用待測產品回覆。"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.test_engineering_terminal import EngineeringTerminal

MAIN_SHA = "405f8c5e1a637a16cbe47470faf5ae1fa02b8676"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge", required=True, type=Path)
    parser.add_argument("--source-sha", required=True, choices=[MAIN_SHA])
    parser.add_argument("--out", type=Path, default=ROOT / "tests/fixtures/k1_terminal_legacy_replies.json")
    args = parser.parse_args()
    case = EngineeringTerminal()
    case.exe = str(args.bridge.resolve())
    try:
        case.setUp()
        case.apply(case.seed())
        replies = {cmd: case.command(cmd) for cmd in ("references", "engineering-read", "assembly-read")}
        def assert_legacy(value):
            if isinstance(value, dict):
                assert "terminal" not in value, "必須使用未加入 terminal 的獨立 main bridge"
                for item in value.values():
                    assert_legacy(item)
            elif isinstance(value, list):
                for item in value:
                    assert_legacy(item)
        assert_legacy(replies)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(replies, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"sourceSha": args.source_sha, "bridgeSha256": hashlib.sha256(args.bridge.read_bytes()).hexdigest(),
                          "fixtureSha256": hashlib.sha256(args.out.read_bytes()).hexdigest()}, sort_keys=True))
    finally:
        case.doCleanups()


if __name__ == "__main__":
    main()
