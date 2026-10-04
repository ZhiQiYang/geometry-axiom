r"""Windows function integration, not native-window E2E.

In a VS Developer Prompt, compile current repo source to TEMP (never the repo):
  cl /nologo /utf-8 /Od /W3 /TC /I. /Fe:%TEMP%\geometry-tests\gdi-contract.exe ^
     /Fo:%TEMP%\geometry-tests\gdi-contract.obj tests\gdi_contract_harness.c ^
     /link /STACK:16777216 user32.lib gdi32.lib comdlg32.lib
Set GEOMETRY_TEST_GDI_HARNESS to that exe and run this test. Rebuild with
/DAUDIT_DISABLE_FAILURES to verify the failure-hit assertion rejects a broken
injector. The source includes the current core through /I., not a stale copy.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
try:
    from tests import binaries
except ModuleNotFoundError:
    import binaries

HARNESS = os.environ.get('GEOMETRY_TEST_GDI_HARNESS')


@unittest.skipUnless(os.name == 'nt' and HARNESS, 'requires compiled Windows GDI contract harness')
class GdiContract(unittest.TestCase):
    def test_confirmed_failures_release_real_resources(self):
        harness = binaries.require_fresh('gdi', HARNESS)
        with tempfile.TemporaryDirectory(prefix='geometry-gdi-contract-') as directory:
            result = subprocess.run([harness], cwd=directory, capture_output=True, timeout=30)
            log = result.stdout.decode('utf-8', errors='replace')
            self.assertEqual(result.returncode, 0, log + result.stderr.decode('utf-8', errors='replace'))
            failures = [line for line in log.splitlines() if line.startswith('PASS bench injected-failure ')]
            self.assertEqual(len(failures), 11)
            self.assertTrue(all(line.endswith('hits=1') for line in failures))
            self.assertEqual(log.count('PASS bench success '), 2)
            self.assertEqual(log.count('PASS bench no-op '), 1)
            self.assertIn('PASS actual Windows GDI count unchanged;', log)
            self.assertIn('PASS SVG ferror/fclose partial cleanup;', log)
            root = ET.parse(Path(directory) / 'complete.svg').getroot()
            self.assertEqual(root.tag, '{http://www.w3.org/2000/svg}svg')
            self.assertFalse((Path(directory) / 'partial-ferror.svg').exists())
            self.assertFalse((Path(directory) / 'partial-close.svg').exists())


if __name__ == '__main__':
    unittest.main()
