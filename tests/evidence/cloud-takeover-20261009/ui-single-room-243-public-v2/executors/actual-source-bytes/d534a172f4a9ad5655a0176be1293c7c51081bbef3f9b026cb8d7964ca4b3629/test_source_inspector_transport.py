"""Failure paths clean real server-owned temporary files before propagating."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'snapshot_transport_cleanup', Path(__file__).parents[1] /
    'geometry-web/source_inspector_transport.py')
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)


class SnapshotCleanup(unittest.TestCase):
    def test_partial_write_failure_removes_created_file_without_bridge_call(self):
        original = tempfile.NamedTemporaryFile
        paths, commands = [], []

        class PartialWrite:
            def __init__(self, *args, **kwargs):
                self.stream = original(*args, **kwargs)
                self.name = self.stream.name
                paths.append(Path(self.name))

            def __enter__(self):
                return self

            def write(self, body):
                self.stream.write(body[:2])
                self.stream.flush()
                raise OSError('synthetic partial write failure')

            def __exit__(self, *unused):
                self.stream.close()

        try:
            with patch.object(transport.tempfile, 'NamedTemporaryFile', PartialWrite):
                with self.assertRaisesRegex(OSError, 'partial write'):
                    transport.snapshot_request(b'reset', commands.append)
            self.assertEqual(len(paths), 1)
            self.assertFalse(paths[0].exists())
            self.assertEqual(commands, [])
        finally:
            for path in paths:
                path.unlink(missing_ok=True)

    def test_bridge_failure_removes_closed_file_and_preserves_original_exception(self):
        paths = []

        def failing_bridge(command):
            path = Path(command.split(' ', 1)[1])
            paths.append(path)
            self.assertEqual(path.read_bytes(), b'reset')
            raise OSError('synthetic bridge read failure')

        try:
            with self.assertRaisesRegex(OSError, 'bridge read'):
                transport.snapshot_request(b'reset', failing_bridge)
            self.assertEqual(len(paths), 1)
            self.assertFalse(paths[0].exists())
        finally:
            for path in paths:
                path.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
