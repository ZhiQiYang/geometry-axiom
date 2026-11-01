"""R06 judge adapters: real assertion/error/skip outcomes must stay distinct."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bay_repeat_mutation_check as runner


class BayRepeatMutationCheck(unittest.TestCase):
    def test_manifest_has_complete_br_coverage_live_anchors_and_assertions(self):
        self.assertEqual([], runner.static_problems())

    def test_inherited_strict_judge_rejects_every_negative_control(self):
        self.assertEqual([], runner.oracle.selftest())

    def test_partial_patch_failure_does_not_leave_the_first_file_mutated(self):
        with tempfile.TemporaryDirectory(prefix='r06-patch-control-') as directory:
            root = Path(directory)
            (root / 'a.c').write_bytes(b'keep\r\n')
            patches = [dict(file='a.c', before='keep', after='changed'), dict(file='a.c', before='absent', after='bad')]
            with self.assertRaises(ValueError):
                runner.apply_patches(root, patches)
            self.assertEqual(b'keep\r\n', (root / 'a.c').read_bytes())

    def test_browser_adapter_requires_exact_controlled_first_red_and_footer(self):
        name = 'R06_BR14_OMIT'
        footer = dict(scope=dict(filters=['GEOMETRY_ASSEMBLY_ONLY']), completed=False, failedAssertions=1,
                      fatal='P77 R06 assertion failed: ' + name + ' details')
        log = 'P77 R06 ' + name + ' correct controlled name ✗ false\nCDP_RESULT ' + json.dumps(footer) + '\n'
        obs = runner.browser_observation(1, False, log, {})
        self.assertEqual(('killed', 'exact-assertion'), runner.oracle.judge_mutant(obs, ['formal-cdp-assembly'], 'formal-cdp-assembly', name))
        self.assertEqual(('not-killed', 'wrong-assertion'), runner.oracle.judge_mutant(obs, ['formal-cdp-assembly'], 'formal-cdp-assembly', 'R06_BR14_NATIVE_MATRIX'))
        for changed in [log.split('\n', 1)[1], log + 'CDP_RESULT ' + json.dumps(footer) + '\n',
                        log.replace('"failedAssertions": 1', '"failedAssertions": 2'),
                        '[EXCEPTION] TypeError\n' + log,
                        log.replace('"completed": false', '"firstTransportFailure": {"status": 500}, "completed": false')]:
            result = runner.browser_observation(1, False, changed, {})
            self.assertEqual('not-killed', runner.oracle.judge_mutant(result, ['formal-cdp-assembly'], 'formal-cdp-assembly', name)[0])

    def test_browser_zero_checks_or_bootstrap_failure_cannot_pass(self):
        footer = dict(scope=dict(filters=['GEOMETRY_ASSEMBLY_ONLY']), completed=True, failedAssertions=0)
        obs = runner.browser_observation(0, False, 'CDP_RESULT ' + json.dumps(footer), {})
        self.assertEqual(('fail', 'killer-not-reached'), runner.oracle.judge_pass(obs, ['formal-cdp-assembly'], ['R06_FORMAL_SAVE_FILE']))
        self.assertIsNone(runner.browser_observation(1, False, 'Chrome missing', {})['result'])

    @unittest.skipUnless(shutil.which('node'), 'Node is required for the actual adapter controls')
    def test_node_adapter_records_real_tests_assertions_errors_skips_and_zero_selection(self):
        with tempfile.TemporaryDirectory(prefix='r06-node-controls-') as directory:
            root = Path(directory)
            test_file, result_file = root / 'control.cjs', root / 'result.json'
            header = "const {test}=require('node:test'),assert=require('node:assert/strict');\n"
            tests = {
                'good': "test('good',()=>assert.equal(1,1,'KILLER[control:target]'));",
                'assertion': "test('assertion',()=>assert.equal(1,2,'KILLER[control:target]'));",
                'wrong': "test('wrong',()=>assert.equal(1,2,'KILLER[control:other]'));",
                'error': "test('error',()=>{throw TypeError('KILLER[control:target]');});",
                'skip': "test('skip',{skip:true},()=>assert.equal(1,2,'KILLER[control:target]'));",
            }
            test_file.write_text(header + '\n'.join(tests.values()), encoding='utf-8')
            for name, expected in [('good', ('pass', 'green')), ('assertion', ('killed', 'exact-assertion')),
                                   ('wrong', ('not-killed', 'wrong-assertion')), ('error', ('not-killed', 'error')),
                                   ('skip', ('not-killed', 'skipped')), ('absent', ('not-killed', 'error'))]:
                with self.subTest(name=name):
                    process = subprocess.run(['node', str(runner.ROOT / runner.NODE_ADAPTER), str(result_file), str(test_file), '^' + name + '$'],
                                             capture_output=True, text=True, timeout=15)
                    value = json.loads(result_file.read_text())
                    obs = dict(exit=process.returncode, timeout=False, result=value)
                    actual = (runner.oracle.judge_pass(obs, [name], ['control:target']) if name == 'good' else
                              runner.oracle.judge_mutant(obs, [name], name, 'control:target'))
                    self.assertEqual(expected, actual, value)


if __name__ == '__main__':
    unittest.main()
