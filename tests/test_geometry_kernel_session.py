"""Source-graph replacement through the same candidate cell used by the host."""
from dataclasses import replace
import importlib.util
from pathlib import Path
import sys
import unittest

if importlib.util.find_spec("geometry_kernel") is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "geometry-core"))

from geometry_kernel import (CandidateError, EvaluationError, EvaluationRequest,
    ExportRoot, ExtrusionDef, PlacedRegionDef, ProgramBuilder, ProgramSession,
    ProvenanceTemplate, Quantity, QuantityType, RegionDef, SourceContext,
    SourceDescriptor, SourceKey, SourceRef, SourceStatus, Unit, ValueType, frame)


STAMP = ("fixture-evaluator", 1)


def fixture(height=20, status=SourceStatus.COMPLETE, partial=False):
    key = SourceKey("dimension", (1, "height"))
    value = None if height is None else Quantity(QuantityType.DIMENSION, height, 1, Unit.MM)
    source = SourceDescriptor(key, ValueType.QUANTITY, SourceContext(), (), value, status)
    p = ProgramBuilder((source,))
    origin = ProvenanceTemplate(("part", 1), (1,))
    region = p.add(PlacedRegionDef(frame((0, 0, 0), (1, 0, 0), (0, 1, 0)),
                                  RegionDef(((0, 0), (20, 0), (20, 20), (0, 20))), origin))
    solid = p.add(ExtrusionDef(region, 0, SourceRef(key, ValueType.QUANTITY), origin))
    return p.freeze(), EvaluationRequest((ExportRoot(solid),), partial)


class KernelSessionTests(unittest.TestCase):
    def test_confirm_recalculates_source_volume_and_is_single_use(self):
        program, request = fixture()
        session = ProgramSession(program, request)
        token, candidate = session.preview(fixture(30)[0], evaluator_stamp=STAMP)
        self.assertEqual("12000", candidate.result.records[0].mesh["volume_mm3"])
        self.assertEqual("8000", session.snapshot.result.records[0].mesh["volume_mm3"])
        candidate.result.records[0].mesh["volume_mm3"] = "broken caller copy"
        accepted = session.confirm(token, evaluator_stamp=STAMP)
        self.assertEqual("12000", accepted.result.records[0].mesh["volume_mm3"])
        self.assertEqual(1, session.revision)
        with self.assertRaises(CandidateError):
            session.confirm(token, evaluator_stamp=STAMP)

    def test_invalid_preview_clears_old_token_and_preserves_committed_graph(self):
        program, request = fixture()
        session = ProgramSession(program, request)
        token, _ = session.preview(fixture(30)[0], evaluator_stamp=STAMP)
        with self.assertRaises(EvaluationError):
            session.preview(fixture(-1)[0], evaluator_stamp=STAMP)
        with self.assertRaises(CandidateError):
            session.confirm(token, evaluator_stamp=STAMP)
        self.assertEqual(program, session.snapshot.program)
        self.assertEqual(0, session.revision)

    def test_cancel_replace_and_changed_evaluator_keep_previous_result(self):
        session = ProgramSession(*fixture())
        first, _ = session.preview(fixture(30)[0], evaluator_stamp=STAMP)
        second, _ = session.preview(fixture(40)[0], evaluator_stamp=STAMP)
        with self.assertRaises(CandidateError):
            session.confirm(first, evaluator_stamp=STAMP)
        session.cancel(second)
        with self.assertRaises(CandidateError):
            session.confirm(second, evaluator_stamp=STAMP)
        third, _ = session.preview(fixture(50)[0], evaluator_stamp=STAMP)
        with self.assertRaises(CandidateError) as caught:
            session.confirm(third, evaluator_stamp=("fixture-evaluator", 2))
        self.assertEqual("EVALUATOR_CHANGED", caught.exception.code)
        self.assertEqual("8000", session.snapshot.result.records[0].mesh["volume_mm3"])
        self.assertEqual(0, session.revision)

    def test_explicit_partial_snapshot_owns_its_diagnostics(self):
        session = ProgramSession(*fixture())
        program, request = fixture(None, SourceStatus.INCOMPLETE, True)
        token, pending = session.preview(program, request, evaluator_stamp=STAMP)
        self.assertEqual("INCOMPLETE", pending.result.status)
        self.assertEqual((), pending.result.records)
        accepted = session.confirm(token, evaluator_stamp=STAMP)
        self.assertEqual("SOURCE_UNAVAILABLE", accepted.result.diagnostics[0].code)
        accepted.result.diagnostics[0].message = "caller mutation"
        self.assertNotEqual("caller mutation", session.snapshot.result.diagnostics[0].message)


if __name__ == "__main__":
    unittest.main()
