"""ModelWorld compatibility and provider-pin behavior through the shared cell."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "geometry-core"))
import modeling
from geometry_app.model_common import ModelError
from geometry_app.model_world import ModelWorld
from geometry_app.source_closure import binary_identity, source_inventory
from geometry_kernel.transactions import CandidateCell


def package(definitions, request, **options):
    if definitions.get("invalid"):
        raise ModelError("INVALID", "fixture-invalid", "I30", "Fixture source rejected")
    return {"definitions": deepcopy(definitions), "request": deepcopy(request),
            "derived": {"status": "COMPLETE", "objects": []}, "diagnostics": []}


class HostWorldTests(unittest.TestCase):
    def world(self, *, verify=None, reader=None):
        return ModelWorld({"value": 1}, {"roots": []}, build=package,
            verify=verify or (lambda value, **options: deepcopy(value)),
            stamp_reader=reader or (lambda: ("loaded", 1)), options={})

    def test_public_facade_uses_host_cell_and_facade_build_verify(self):
        with (mock.patch.object(modeling, "build_package", side_effect=package) as build,
             mock.patch.object(modeling, "verify_package", side_effect=lambda value, **options: deepcopy(value)) as verify,
             mock.patch("geometry_app.model_world.runtime_stamp", return_value=("fixture", 1))):
            world = modeling.ModelWorld({"value": 1}, {"roots": []})
            preview = world.preview({"value": 2})
            accepted = world.confirm(preview["token"])
        self.assertIsInstance(world._cell, CandidateCell)
        self.assertEqual(2, accepted["definitions"]["value"])
        self.assertEqual(2, build.call_count)
        self.assertEqual(1, verify.call_count)

    def test_legacy_cancel_and_confirm_messages_remain_distinct(self):
        world = self.world()
        token = world.preview({"value": 2})["token"]
        for operation, expected in ((lambda: world.cancel("wrong"), "Preview token does not match"),
                                    (lambda: world.confirm("wrong"), "Preview is absent, cancelled, replaced or stale")):
            with self.assertRaises(ModelError) as caught:
                operation()
            self.assertEqual(("INVALID", "STALE_PREVIEW", "I30", expected),
                             (caught.exception.status, caught.exception.code, caught.exception.clause, caught.exception.message))
        self.assertEqual(2, world.confirm(token)["definitions"]["value"])

    def test_invalid_preview_replaces_token_without_committing(self):
        world = self.world()
        token = world.preview({"value": 2})["token"]
        with self.assertRaises(ModelError):
            world.preview({"invalid": True})
        with self.assertRaises(ModelError):
            world.confirm(token)
        self.assertEqual({"value": 1}, world.definitions)

    def test_verify_failure_consumes_preview_but_keeps_original(self):
        def reject(value, **options):
            raise ModelError("INVALID", "SNAPSHOT_MISMATCH", "I31", "Fixture verification failed")
        world = self.world(verify=reject)
        token = world.preview({"value": 2})["token"]
        with self.assertRaises(ModelError) as caught:
            world.confirm(token)
        self.assertEqual("SNAPSHOT_MISMATCH", caught.exception.code)
        with self.assertRaises(ModelError) as caught:
            world.confirm(token)
        self.assertEqual("STALE_PREVIEW", caught.exception.code)
        self.assertEqual({"value": 1}, world.definitions)

    def test_runtime_change_before_or_during_verification_is_atomic(self):
        stamp = [("runtime", 1)]
        world = self.world(reader=lambda: stamp[0])
        token = world.preview({"value": 2})["token"]
        stamp[0] = ("runtime", 2)
        with self.assertRaises(ModelError) as caught:
            world.confirm(token)
        self.assertEqual("MODEL_RUNTIME_CHANGED", caught.exception.code)
        self.assertEqual({"value": 1}, world.definitions)
        stamp[0] = ("runtime", 1)
        with self.assertRaises(ModelError):
            world.confirm(token)
        def change_during(value, **options):
            stamp[0] = ("runtime", 2)
            return value
        world = self.world(reader=lambda: stamp[0], verify=change_during)
        token = world.preview({"value": 3})["token"]
        with self.assertRaises(ModelError) as caught:
            world.confirm(token)
        self.assertEqual("MODEL_RUNTIME_CHANGED", caught.exception.code)
        self.assertEqual({"value": 1}, world.definitions)

    def test_runtime_read_failure_cannot_revive_a_matching_preview(self):
        fail = [False]
        def reader():
            if fail[0]:
                raise ModelError("INVALID", "MODEL_RUNTIME_CHANGED", "I30", "Fixture changed")
            return ("runtime", 1)
        world = self.world(reader=reader)
        token = world.preview({"value": 2})["token"]
        fail[0] = True
        with self.assertRaises(ModelError):
            world.confirm(token)
        fail[0] = False
        with self.assertRaises(ModelError) as caught:
            world.confirm(token)
        self.assertEqual("STALE_PREVIEW", caught.exception.code)
        self.assertEqual({"value": 1}, world.definitions)

    def test_source_inventory_detects_add_remove_and_same_size_content_change(self):
        with tempfile.TemporaryDirectory(prefix="geo261-source-pins-") as directory:
            root = Path(directory)
            source = root / "geometry-templates/woodworking/geometry_woodworking/provider.py"
            source.parent.mkdir(parents=True)
            source.write_text("alpha\n", encoding="utf-8")
            before = source_inventory(root)
            source.write_text("omega\n", encoding="utf-8")
            self.assertNotEqual(before, source_inventory(root))
            source.write_text("alpha\n", encoding="utf-8")
            self.assertEqual(before, source_inventory(root))
            added = source.with_name("added.py")
            added.write_text("pass\n", encoding="utf-8")
            self.assertNotEqual(before, source_inventory(root))
            added.unlink()
            source.unlink()
            self.assertNotEqual(before, source_inventory(root))

    def test_binary_identity_reads_bytes_and_does_not_normalize_them(self):
        with tempfile.TemporaryDirectory(prefix="geo261-binary-pins-") as directory:
            path = Path(directory) / "adapter.bin"
            path.write_bytes(b"a\r\nb")
            before = binary_identity(path)
            path.write_bytes(b"a\n\nb")
            self.assertNotEqual(before, binary_identity(path))


if __name__ == "__main__":
    unittest.main()
