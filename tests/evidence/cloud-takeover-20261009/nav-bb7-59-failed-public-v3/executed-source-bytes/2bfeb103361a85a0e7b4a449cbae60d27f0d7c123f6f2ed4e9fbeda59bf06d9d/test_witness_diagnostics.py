"""Reject witnesses must identify the actual source command and failure rule."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'geometry-guide'))
import axiom_examples as examples
import witness


class WitnessDiagnostics(unittest.TestCase):
    def test_internal_line_zero_does_not_hide_real_scene_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            scene = Path(tmp) / 'fixture.scene'
            scene.write_text('surface 1\nvalid application\ninvalid grid\n', encoding='utf-8')
            stderr = f'engineering:0: I35: bad range\n{scene}:3: I35: bad range\n'
            seen = []
            def run(_exe, path, _tmp):
                seen.append(Path(path).read_text(encoding='utf-8'))
                return {'rc': 0, 'err': '', 'svg': '<g transform="translate(' * 3 + '<path class="surface"/>', 'out': ''}
            with patch.object(examples, 'run_scene', run):
                svg, note, why = examples.before_failure('unused', scene, stderr, tmp)
            self.assertTrue(svg)
            self.assertEqual(why, '')
            self.assertIn('第 3 行之前', note)
            self.assertEqual(seen, ['surface 1\nvalid application\n'])

    def test_rejection_for_wrong_rule_is_not_a_witness(self):
        with tempfile.TemporaryDirectory() as tmp:
            scene = Path(tmp) / 'fixture.scene'
            scene.write_text('# I35\nsurface 1\nengineering grid invalid\n', encoding='utf-8')
            entry = {'scene': str(scene), 'expect': 'reject', 'view': 'bottom',
                     'gist': 'range guard', 'error_contains': 'I35: effective dimension violates'}
            with patch.object(examples, 'run_scene', return_value={'rc': 1, 'err': 'unknown engineering command', 'svg': None, 'out': ''}):
                with self.assertRaisesRegex(witness.WitnessError, '拒絕原因不符預期'):
                    witness.render_one('unused', 'I35', entry, tmp)


if __name__ == '__main__':
    unittest.main(verbosity=2)
