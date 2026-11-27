"""跑真撤回入口（含 T24 的 undo／redo），不以模擬 TAP 代替全套基線。"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class R13WithdrawalBaseline(unittest.TestCase):
    def test_t24_green_suite_reaches_named_withdrawal(self):
        case = 'R13_UI_IMPLICIT_MM_RESTORED'
        with tempfile.TemporaryDirectory() as out:
            proc = subprocess.run([sys.executable, 'tests/mutation_r13_ui.py', '--out', out,
                                   '--only', case], cwd=ROOT, capture_output=True, text=True, timeout=60)
            baseline = json.loads((Path(out) / 'full-baseline.json').read_text())
            self.assertEqual(baseline['counts'], {'tests': 33, 'pass': 33, 'fail': 0,
                             'cancelled': 0, 'skipped': 0, 'todo': 0})
            self.assertEqual(proc.returncode, 0, 'R13_T24_GREEN_BASELINE_REACHES_WITHDRAWAL\n' + proc.stderr)
            rows = json.loads((Path(out) / 'summary.json').read_text())['results']
            self.assertEqual([(r['name'], r['exits']) for r in rows], [(case, [0, 1, 0])])


if __name__ == '__main__':
    unittest.main()
