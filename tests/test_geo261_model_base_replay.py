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
  both output modes, and the same final World. The World is compared field by
  field: every byte except WoodMember padding, which is rebuilt from the
  member's declared fields (parsed from members.h). Two runs of one build give
  identical raw bytes, but under MSVC the two paths leave different stack bytes
  in that padding (for example 15 bytes for room_a), so the raw World digest is
  compared as well only where the compiler is not MSVC.
* diagnostics: when the owner itself fails after a successful replay, the
  adapter reports the per-line path's I8 text, never the generic one.
"""
import json
import os
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
MEMBERS = ROOT / 'geometry-templates/woodworking/native/members.h'
MAIN = 'int main(int argc, char **argv)'
WORLD_HOOK = '    world.app.canvas_pos_count = 0;  /* D12: presentation never enters source identity. */\n'
OWNER_SEAL = 'if(ok&&!(app_world_candidate_seal(owner)&&'
OWNER_SEAL_FAULT = 'if(ok&&!(!getenv("REPLAY_FAIL_OWNER_SEAL")&&app_world_candidate_seal(owner)&&'
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


def member_fields():
    """Declared WoodMember fields, from the header the adapter compiles."""
    text = MEMBERS.read_bytes().replace(b'\r\n', b'\n').decode('utf-8')
    body = re.search(r'typedef struct \{([^{}]*)\} WoodMember;', text)
    if body is None:
        raise AssertionError('WoodMember declaration not found in ' + str(MEMBERS))
    body = re.sub(r'/\*.*?\*/', '', body.group(1), flags=re.S)
    fields = []
    for declaration in body.split(';'):
        declaration = declaration.strip()
        if declaration:
            fields += [re.findall(r'[A-Za-z_]\w*', part)[-1] for part in declaration.split(',')]
    if not {'id', 'length', 'placed', 'origin'} <= set(fields):
        raise AssertionError('WoodMember fields not parsed: ' + repr(fields))
    return fields


def world_digests():
    """C that prints a padding-free World digest and the raw World digest on stderr."""
    copies = ''.join('clean.%s=from->%s;' % (name, name) for name in member_fields())
    return ('    {static World replay_fields;memcpy(&replay_fields,&world,sizeof world);\n'
            '     for(size_t i=0;i<sizeof world.wood.timbers/sizeof world.wood.timbers[0];++i){\n'
            '         const WoodMember *from=&world.wood.timbers[i];WoodMember clean;memset(&clean,0,sizeof clean);\n'
            '         ' + copies + '\n'
            '         memcpy(&replay_fields.wood.timbers[i],&clean,sizeof clean);}\n'
            '     char fields[65],raw[65];geo_sha256(&replay_fields,sizeof replay_fields,fields);\n'
            '     geo_sha256(&world,sizeof world,raw);fprintf(stderr,"WORLD-FIELDS %s\\nWORLD-RAW %s\\n",fields,raw);}\n')


class ModelBaseOwnedReplay(unittest.TestCase):
    @classmethod
    def harness(cls, name, original=False):
        build = native()
        originals = [MODEL, HARNESS]
        saved = {p: p.read_bytes() for p in originals}
        texts = {p: b.replace(b'\r\n', b'\n').decode('utf-8') for p, b in saved.items()}
        model = texts[MODEL]
        for anchor in (MAIN, WORLD_HOOK, OWNER_SEAL, *(current for current, _ in ORIGINAL)):
            if model.count(anchor) != 1:
                raise AssertionError('Actual adapter anchor must occur exactly once: ' + anchor.strip())
        model = model.replace(MAIN, 'int replay_model_command_main(int argc, char **argv)')
        model = model.replace(WORLD_HOOK, world_digests() + WORLD_HOOK)
        if original:
            for current, before in ORIGINAL:
                model = model.replace(current, before)
        else:
            model = model.replace(OWNER_SEAL, OWNER_SEAL_FAULT)
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
        cls.msvc = native().windows
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

    def run_adapter(self, exe, scene, neutral=False, env=None):
        """(status, stdout, stderr without witness lines, cost, World-fields digest, raw World digest)."""
        command = [str(exe), *(['--neutral-sources'] if neutral else []), str(scene)]
        run = subprocess.run(command, capture_output=True, timeout=120, env=env)
        self.assertIn(run.returncode, (0, 1), 'crash is not a verdict: ' + run.stderr.decode('utf-8', 'replace'))
        # The witness lines are last; text-mode stderr ends them with CRLF on Windows.
        match = re.search(rb'(?:^|\n)((?:WORLD-FIELDS (\w+)\r?\nWORLD-RAW (\w+)\r?\n)?COST (\d+) (\d+) (\d+)\r?\n)\Z',
                          run.stderr)
        self.assertIsNotNone(match, run.stderr)
        cost = tuple(int(value) for value in match.groups()[3:])
        stderr = run.stderr[:len(run.stderr) - len(match.group(1))]
        return run.returncode, run.stdout, stderr, cost, match.group(2), match.group(3)

    def test_admitted_definition_lines_share_one_owner_candidate(self):
        for neutral in (False, True):
            with self.subTest(neutral=neutral):
                status, stdout, stderr, (candidates, _, _), _, _ = self.run_adapter(self.current, self.scenes['admitted'], neutral)
                self.assertEqual(0, status, stdout + stderr)
                self.assertEqual(1, candidates, 'owned replay keeps every admitted line in the owner')

    def test_lines_outside_the_frame_keep_inner_candidates_in_one_reused_block(self):
        status, stdout, stderr, (candidates, blocks, _), _, _ = self.run_adapter(self.current, self.scenes['outside'])
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

    def test_current_adapter_matches_the_original_byte_for_byte_and_field_for_field(self):
        accepted = rejected = 0
        for name, scene in sorted(self.scenes.items()):
            for neutral in (False, True):
                with self.subTest(scene=name, neutral=neutral):
                    expected = self.run_adapter(self.original, scene, neutral)
                    actual = self.run_adapter(self.current, scene, neutral)
                    self.assertEqual(expected[:3], actual[:3])
                    self.assertEqual(expected[4], actual[4], 'final World fields differ')
                    if not self.msvc:
                        self.assertEqual(expected[5], actual[5], 'final raw World bytes differ')
                    if expected[0] == 0:
                        accepted += 1
                        self.assertIn(b'"ok":true', expected[1])
                        self.assertIsNotNone(expected[4])
                    else:
                        rejected += 1
                        self.assertIn(b'"ok":false', expected[1])
                        self.assertIsNone(expected[4])
        # 13 scenes x 2 modes. _demo_ceiling.scene is accepted from an LF checkout and
        # rejected (line 18) from a CRLF one, by both adapters alike.
        self.assertEqual(26, accepted + rejected)
        self.assertGreaterEqual(accepted, 12)
        self.assertGreaterEqual(rejected, 12)

    def test_a_failed_owner_seal_reports_the_per_line_i8_text(self):
        env = dict(os.environ, REPLAY_FAIL_OWNER_SEAL='1')
        status, stdout, stderr, (candidates, _, _), fields, _ = self.run_adapter(
            self.current, self.scenes['admitted'], False, env)
        self.assertEqual(1, status, stdout + stderr)
        self.assertEqual(1, candidates)
        self.assertIsNone(fields)
        error = json.loads(stdout.decode('utf-8'))
        self.assertEqual(('INVALID', 'BASE_INVALID', 'I9'), (error['status'], error['code'], error['clause']))
        self.assertEqual('line 0: I8: candidate seal failed; World unchanged', error['message'])


if __name__ == '__main__':
    unittest.main()
