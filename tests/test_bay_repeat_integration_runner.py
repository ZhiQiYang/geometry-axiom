"""R06I required browser increment: missing any owned assertion is failure."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bay_repeat_mutation_check as runner


class BayRepeatIntegrationRunner(unittest.TestCase):
    def test_browser_integration_section_cannot_be_omitted_from_green_baseline(self):
        manifest = runner.load_manifest()
        required = ['R06_INT_OWNER', 'R06_INT_SOURCE', 'R06_INT_SAVE',
                    'R06_INT_COLD', 'R06_INT_STRIPPED', 'R06_INT_ERRORS']
        self.assertTrue(set(required).issubset(manifest['browserTags']))
        footer = dict(scope=dict(filters=['GEOMETRY_ASSEMBLY_ONLY']), completed=True,
                      failedAssertions=0, apiTransportTraceComplete=True, apiTransportFailures=[])
        def observe(omit=None):
            lines = ['P77 R06 ' + tag + ' completed ✓ true' for tag in manifest['browserTags'] if tag != omit]
            return runner.browser_observation(0, False, '\n'.join(lines) + '\nCDP_RESULT ' + json.dumps(footer), manifest)
        self.assertEqual(('pass', 'green'), runner.oracle.judge_pass(observe(), ['formal-cdp-assembly'], manifest['browserTags']))
        for tag in required:
            with self.subTest(omitted=tag):
                self.assertEqual(('fail', 'killer-not-reached'), runner.oracle.judge_pass(observe(tag), ['formal-cdp-assembly'], manifest['browserTags']))

if __name__ == '__main__':
    unittest.main()
