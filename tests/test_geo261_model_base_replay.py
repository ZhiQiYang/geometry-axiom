"""GEO-261 cost: model-base reads its scene through the owned file replay (B).

The adapter opens one H candidate and replays the file with app_scene_replay_file,
the frame the bridge's scene import already uses; it also keeps one fingerprint
buffer for both --neutral-sources digests and reuses H candidate blocks. All
witnesses use the actual adapter source linked to the product objects:

* cost: lines the frame admits share the owner, so a definition-only scene
  opens exactly one H candidate; every line outside the frame keeps its own
  inner candidate; sequential inner candidates reuse one block; both
  fingerprints read one buffer. Restoring the original adapter turns each red.
* equivalence: the original adapter (per-line parse_scene_file, one freed
  fingerprint buffer per digest, no block reuse), rebuilt from the same source,
  returns byte-identical stdout and stderr, including the I8a preview text, in
  both output modes. Raw World bytes are compared out of suite (gcc -O2): under
  MSVC the original adapter already leaves stack bytes in WoodMember padding,
  so a raw World digest differs between two runs of one build.
"""
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native  # noqa: E402

FLAGS = ['GEOMETRY_KERNEL_EXTERNAL=1', 'GEOMETRY_WOODWORKING_EXTERNAL=1',
         'GEOMETRY_HOST_HISTORY_EXTERNAL=1', 'GEOMETRY_HOST_CANDIDATE_EXTERNAL=1']
MODEL = ROOT / 'geometry-core/model_base.c'
HARNESS = ROOT / 'tests/geo261_model_base_replay_harness.c'
MAIN = 'int main(int argc, char **argv)'
# (current adapter, original adapter) for the three GEO-261 cost changes.
ORIGINAL = (
    ('if (!model_parse_scene(path, &world)) {', 'if (!parse_scene_file(path, &world)) {'),
    ('    static unsigned char *bytes;\n    FILE *in=fopen(path,"rb");if(!in)return false;\n'
     '    size_t limit=1024u*1024u;if(!bytes)bytes=malloc(limit+1);\n',
     '    FILE *in=fopen(path,"rb");if(!in)return false;\n'
     '    size_t limit=1024u*1024u;unsigned char *bytes=malloc(limit+1);\n'),
    ('    if(ok)geo_sha256(bytes,size,hash);\n    fclose(in);return ok;\n',
     '    if(ok)geo_sha256(bytes,size,hash);\n    free(bytes);fclose(in);return ok;\n'),
    ('    g_app_world_candidate_pool_enabled=true;\n', ''),
)
ADMITTED = """boundary 1 outline 0,0 4000,0 4000,3000 0,3000
placement 1 on boundary 1 origin 0 0 2500 u +x v +y
spec main_x 2000
guide 1 1 v spec:main_x
timber 1 27 33 role boundary
timber 2 27 33 role boundary
timber 3 27 33 role primary
place 1 on 1 at-face e0 +u +n
place 2 on 1 at-face e2 +u +n
place 3 on 1 at-line guide 1 +v +n
"""
# Placed timbers exist, so these three definitions may affect references and
# stay outside the frame with their own inner candidate each.
OUTSIDE = """boundary 2 outline 0,0 1000,0 1000,1000 0,1000
placement 2 on boundary 2 origin 0 0 0 u +x v +z
spec other 500
"""
FIXTURES = (
    'room_a.scene', 'ceiling-a.scene', '_demo_ceiling.scene', '_wit_d31_parameters.scene',
    '_ax_i9_forward_ref.scene', '_ax_i4_duplicate_boundary.scene', '_edge_grid_locked.scene',
    '_edge_between_conflict.scene', '_edge_i19_place_order.scene', '_edge_straddle.scene',
)


def remap(text, original, replacements):
    def include(match):
        path = (original.parent / match.group(1)).resolve()
        return '#include "' + str(replacements.get(path, path)).replace('\\', '/') + '"'
    return re.sub(r'^#include "([^"]+)"', include, text, flags=re.MULTILINE)


class ModelBaseOwnedReplay(unittest.TestCase):
    @classmethod
    def harness(cls, name, original=False):
        build = native()
        originals = [MODEL, HARNESS]
        saved = {p: p.read_bytes() for p in originals}
        texts = {p: b.replace(b'\r\n', b'\n').decode('utf-8') for p, b in saved.items()}
        model = texts[MODEL]
        for anchor in (MAIN, *(current for current, _ in ORIGINAL)):
            if model.count(anchor) != 1:
                raise AssertionError('Actual adapter anchor must occur exactly once: ' + anchor.strip())
        model = model.replace(MAIN, 'int replay_model_command_main(int argc, char **argv)')
        if original:
            for current, before in ORIGINAL:
                model = model.replace(current, before)
        texts[MODEL] = model
        paths = {p.resolve(): build.work / ('model-base-replay-' + name + '-' + p.name) for p in originals}
        for p in originals:
            paths[p.resolve()].write_text(remap(texts[p], p, paths), encoding='utf-8')
        client = build.compile(paths[HARNESS.resolve()], 'model-base-replay-' + name, FLAGS)
        exe = build.link('model-base-replay-' + name, [client, *build.product_objects()])
        for p, data in saved.items():
            if p.read_bytes() != data:
                raise AssertionError('Witness edited production source')
        return exe

    @classmethod
    def setUpClass(cls):
        cls.current = cls.harness('current')
        cls.original = cls.harness('original', original=True)
        work = native().work
        cls.scenes = {}
        for name, text in (('admitted', ADMITTED), ('outside', ADMITTED + OUTSIDE)):
            path = work / ('model-base-replay-' + name + '.scene')
            path.write_text(text, encoding='utf-8')
            cls.scenes[name] = path
        with zipfile.ZipFile(ROOT / 'geometry-web/examples/engineering-spec-v1.gcanvas') as archive:
            manifest = json.loads(archive.read('manifest.json'))
        path = work / 'model-base-replay-engineering.scene'
        path.write_text(manifest['models'][0]['input']['base_scene'], encoding='utf-8')
        cls.scenes['engineering'] = path
        for name in FIXTURES:
            cls.scenes[name] = ROOT / name

    def run_adapter(self, exe, scene, neutral=False):
        command = [str(exe), *(['--neutral-sources'] if neutral else []), str(scene)]
        run = subprocess.run(command, capture_output=True, timeout=120)
        self.assertIn(run.returncode, (0, 1), 'crash is not a verdict: ' + run.stderr.decode('utf-8', 'replace'))
        # The witness line is last; text-mode stderr ends it with CRLF on Windows.
        match = re.search(rb'(?:^|\n)(COST (\d+) (\d+) (\d+)\r?\n)\Z', run.stderr)
        self.assertIsNotNone(match, run.stderr)
        cost = tuple(int(value) for value in match.groups()[1:])
        return run.returncode, run.stdout, run.stderr[:len(run.stderr) - len(match.group(1))], cost

    def test_admitted_definition_lines_share_one_owner_candidate(self):
        for neutral in (False, True):
            with self.subTest(neutral=neutral):
                status, stdout, stderr, (candidates, _, _) = self.run_adapter(self.current, self.scenes['admitted'], neutral)
                self.assertEqual(0, status, stdout + stderr)
                self.assertEqual(1, candidates, 'owned replay keeps every admitted line in the owner')

    def test_lines_outside_the_frame_keep_inner_candidates_in_one_reused_block(self):
        status, stdout, stderr, (candidates, blocks, _) = self.run_adapter(self.current, self.scenes['outside'])
        self.assertEqual(0, status, stdout + stderr)
        inner = OUTSIDE.count('\n')
        self.assertEqual(1 + inner, candidates)
        self.assertEqual(2, blocks, 'the owner and one block reused by every sequential inner candidate')

    def test_both_source_fingerprints_read_one_buffer(self):
        self.assertEqual(1, self.run_adapter(self.current, self.scenes['admitted'], True)[3][2])
        self.assertEqual(0, self.run_adapter(self.current, self.scenes['admitted'], False)[3][2])

    def test_restoring_the_original_adapter_is_red_at_every_cost_witness(self):
        lines = ADMITTED.count('\n')
        current = self.run_adapter(self.current, self.scenes['outside'], True)[3]
        original = self.run_adapter(self.original, self.scenes['outside'], True)[3]
        self.assertEqual((1 + OUTSIDE.count('\n'), 2, 1), current)
        self.assertGreater(original[0], lines + OUTSIDE.count('\n'), 'one candidate per line plus closing checks')
        self.assertEqual(original[0], original[1], 'without reuse every candidate allocates its own block')
        self.assertEqual(2, original[2], 'without the kept buffer each digest allocates one')

    def test_current_adapter_matches_the_original_byte_for_byte(self):
        accepted = rejected = 0
        for name, scene in sorted(self.scenes.items()):
            for neutral in (False, True):
                with self.subTest(scene=name, neutral=neutral):
                    expected = self.run_adapter(self.original, scene, neutral)[:3]
                    actual = self.run_adapter(self.current, scene, neutral)[:3]
                    self.assertEqual(expected, actual)
                    if expected[0] == 0:
                        accepted += 1
                        self.assertIn(b'"ok":true', expected[1])
                    else:
                        rejected += 1
                        self.assertIn(b'"ok":false', expected[1])
        self.assertGreaterEqual(accepted, 8)
        self.assertGreaterEqual(rejected, 8)


if __name__ == '__main__':
    unittest.main()
