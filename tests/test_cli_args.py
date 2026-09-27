"""CLI subprocess contract for the selected executable; no GUI or GDI claim.

The caller is responsible for compiling GEOMETRY_TEST_CORE from current sources.
"""
import os
import math
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

CORE = os.environ.get('GEOMETRY_TEST_CORE')


@unittest.skipUnless(CORE, 'set GEOMETRY_TEST_CORE to a freshly compiled executable')
class CliArgs(unittest.TestCase):
    def run_core(self, args, ok):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.svg'
            result = subprocess.run([CORE, '--no-window', '--out', str(output), *args],
                                    cwd=directory, capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 0 if ok else 1,
                             result.stderr.decode('utf-8', errors='replace'))
            return result, output.read_bytes() if output.exists() else None

    def test_unknown_option(self):
        for option in ('--bogus', '--scen', 'stray.scene'):
            with self.subTest(option=option):
                result, content = self.run_core([option], False)
                self.assertIn(option.encode(), result.stderr)
                self.assertIsNone(content)

    def test_help_has_all_options_without_output(self):
        result, content = self.run_core(['--help'], True)
        for flag in ('--scene', '--out', '--no-window', '--bench', '--help'):
            self.assertIn(flag.encode(), result.stdout)
        self.assertIsNone(content)

    def test_invalid_bench_does_not_write_output(self):
        for value in ('', 'abc', '1x', '1.5', '-5', '0', '1000001', '9' * 60, ' 10', '+10'):
            with self.subTest(value=value):
                result, content = self.run_core(['--bench', value], False)
                self.assertIn(b'--bench', result.stderr)
                self.assertIsNone(content)
        result, output = self.run_core(['--bench', '1000001', '--help'], False)
        self.assertIn(b'--bench', result.stderr)
        self.assertIsNone(output)

    def test_missing_option_values(self):
        for flag in ('--scene', '--out', '--bench'):
            with self.subTest(flag=flag):
                result, output = self.run_core([flag], False)
                self.assertIn(flag.encode(), result.stderr)
                self.assertIsNone(output)

    def test_valid_bench(self):
        for value in ('1', '10'):
            with self.subTest(value=value):
                _, content = self.run_core(['--bench', value], True)
                self.assertIsNotNone(content)
                root = ET.fromstring(content)
                self.assertEqual(root.tag, '{http://www.w3.org/2000/svg}svg')
                # The default world has geometry in all three orthographic views.
                groups = root.findall('{http://www.w3.org/2000/svg}g')
                self.assertEqual(len(groups), 3)
                for group in groups:
                    polygons = group.findall('{http://www.w3.org/2000/svg}polygon')
                    self.assertTrue(polygons)
                    for polygon in polygons:
                        points = [tuple(map(float, point.split(',')))
                                  for point in polygon.attrib.get('points', '').split()]
                        self.assertGreaterEqual(len(points), 3)
                        self.assertTrue(all(len(point) == 2 and all(map(math.isfinite, point))
                                            for point in points))
        # Validate the upper boundary without executing a million GDI paints.
        _, content = self.run_core(['--bench', '1000000', '--help'], True)
        self.assertIsNone(content)

    @unittest.skipUnless(os.name == 'posix' and Path('/dev/full').exists(), 'requires POSIX full device')
    def test_svg_write_failure_is_reported_without_unlinking_device(self):
        import stat
        original = Path('/dev/full').stat()
        self.run_core(['--out', '/dev/full'], False)
        after = Path('/dev/full').stat()
        self.assertTrue(stat.S_ISCHR(after.st_mode))
        self.assertEqual(original.st_ino, after.st_ino)


if __name__ == '__main__':
    unittest.main()
