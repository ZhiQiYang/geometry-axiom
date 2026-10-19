"""Bind a parent reader-only comparison to its checkout, HEAD and tree.

No native binary is consumed by test_axiom_reader; this receipt deliberately
does not imply a complete parent/head product comparison or byte-identical HTML.
"""
import argparse
from pathlib import Path
import subprocess
import sys

from identity import capture, sha, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', type=Path, required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = args.checkout.resolve(strict=True)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    before = capture(root)
    assert before['head'] == args.head and not before['tracked_diff']
    write(out / 'checkout-before.json', before)
    argv = [sys.executable, str(root / 'tests/_unittest_runner.py'),
            str(root / 'tests/test_axiom_reader.py'), '--json-out',
            str(out / 'reader.json'), '--log', str(out / 'reader.log')]
    result = subprocess.run(argv, cwd=root)
    after = capture(root)
    assert before == after
    write(out / 'checkout-after.json', after)
    write(out / 'command.json', {'argv': argv, 'exit_code': result.returncode,
          'head': before['head'], 'tree': before['tree'],
          'executor': str(Path(__file__).resolve()),
          'executor_sha256': sha(Path(__file__).read_bytes()),
          'scope': 'Parent reader suite only; not a full parent/head comparison.',
          'required_binaries': []})
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
