"""Run the existing GEO-246 assertions, recording all 32 pins even when messages regress.

Use --expect-generic with a deliberately compiled message-only mutant. The existing
reject() still checks refusal, confirmation and rollback before checking the reason.
Each reason failure becomes a unittest cleanup failure so later inputs also run;
other failures are raised immediately. This is an explicit audit, not run_all coverage.
"""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests import _bridge, test_grid_system_contract as finite  # noqa: E402
from tests import test_infinite_grid_contract as infinite, test_subgrid_contract as subgrid  # noqa: E402

CASES = [
    (finite.GridSystemContract, 'test_invalid_definitions_limits_and_missing_sources_are_atomic'),
    (infinite.InfiniteGridContract, 'test_fraction_reduction_invalid_fractions_and_one_axis_cannot_make_cell'),
    (infinite.InfiniteGridContract, 'test_keyed_vertex_move_tracks_anchor_and_ambiguous_identity_is_rejected'),
    (infinite.InfiniteGridContract, 'test_query_input_limits_and_signed_overflow_never_mutate_world'),
    (subgrid.SubgridContract, 'test_s03_exact_divisions_one_axis_empty_and_64_line_limit'),
    (subgrid.SubgridContract, 'test_s09_boundary_growth_cannot_change_panel_count_behind_children'),
]


def is_target(why):
    if not isinstance(why, tuple):
        return False
    return (why[0] in ('D29/I37', '重宣告後有物件失效')
            or (why[0] == 'D30/I37' and why[1].startswith(('anchor u ', 'cell u=')))
            or (why[0] == 'D19/I25' and any('divisions u=' in text for text in why)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bridge', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--expect-generic', action='store_true')
    args = parser.parse_args()
    bridge = args.bridge.resolve(strict=True)
    records = []

    def traced(original):
        def reject(self, command, why=None):
            if not is_target(why):
                return original(self, command, why)
            caller = inspect.currentframe().f_back
            record = {'test': self.id(), 'file': str(Path(caller.f_code.co_filename).relative_to(ROOT)),
                      'line': caller.f_lineno, 'input': command, 'expected': list(why)}
            try:
                result = original(self, command, why)
            except AssertionError as exc:
                if 'was refused for a different reason:' not in str(exc):
                    raise
                record.update(outcome='reason-failure', failure=str(exc))
                records.append(record)
                # Every original assertion remains a real red unittest failure.
                self.addCleanup(self.fail, str(exc))
                return None
            record['outcome'] = 'pass'
            records.append(record)
            return result
        return reject

    with patch.object(_bridge, 'find_bridge', return_value=str(bridge)):
        with patch.object(finite.GridSystemContract, 'reject', traced(finite.GridSystemContract.reject)), \
             patch.object(infinite.InfiniteGridContract, 'reject', traced(infinite.InfiniteGridContract.reject)), \
             patch.object(subgrid.SubgridContract, 'reject', traced(subgrid.SubgridContract.reject)):
            suite = unittest.TestSuite(cls(method) for cls, method in CASES)
            result = unittest.TextTestRunner(verbosity=2).run(suite)
    failures = sum(row['outcome'] == 'reason-failure' for row in records)
    receipt = {'schema': 'geo246-weak-pin-probe/1', 'bridge_sha256': hashlib.sha256(bridge.read_bytes()).hexdigest(),
               'mode': 'generic-message-mutant' if args.expect_generic else 'baseline',
               'pins': len(records), 'reason_failures': failures, 'test_failures': len(result.failures),
               'errors': len(result.errors), 'skips': len(result.skipped), 'records': records}
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    expected_failures = 32 if args.expect_generic else 0
    ok = (len(records) == 32 and failures == expected_failures
          and len(result.failures) == expected_failures and not result.errors and not result.skipped)
    print(f'GEO-246 {receipt["mode"]}: pins={len(records)}, reason failures={failures}, audit={"PASS" if ok else "FAIL"}')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
