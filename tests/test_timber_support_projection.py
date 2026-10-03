"""Exact native support projection: identities, local faces and read purity."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tests._bridge import BridgeSession
from tests._timber_support_bridge import ROOT, _reference_with_projection, build
from tests.test_assembly_rules import binding, rule


class TimberSupports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build_directory = tempfile.TemporaryDirectory(prefix='timber-support-build-')
        cls.addClassCleanup(cls.build_directory.cleanup)
        cls.binary = build(cls.build_directory.name)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='timber-support-')
        self.addCleanup(self.directory.cleanup)
        self.bridge = BridgeSession(self.binary, cwd=self.directory.name)
        self.addCleanup(self.bridge.stop)
        self.bridge.command('reset')

    def command(self, command):
        return self.bridge.command(command)

    def line(self, command):
        result = self.command('line ' + command)
        if result.get('preview', {}).get('valid'):
            result = self.command('line confirm ' + str(result['preview']['token']))
        self.assertTrue(result.get('ok'), result)
        return result

    def scene(self, lines):
        for line in lines:
            self.line(line)

    def dump(self):
        return self.command('dump')['text']

    def test_build_hooks_accept_owner_integrated_reference_without_duplication(self):
        projection = ROOT / 'geometry-web/timber_support_projection.inc'
        source = (ROOT / 'geometry-web/reference_bridge.inc').read_text()
        injected = _reference_with_projection(source, projection)
        integrated = injected.replace(f'#include "{projection.as_posix()}"',
                                      '#include "timber_support_projection.inc"')
        self.assertEqual(injected, _reference_with_projection(integrated, projection))
        mutant = Path(self.directory.name) / 'face_mutant.inc'
        redirected = _reference_with_projection(integrated, mutant)
        self.assertEqual(1, redirected.count(f'#include "{mutant.as_posix()}"'))
        self.assertEqual(1, redirected.count('json_timber_supports(&g_world,fingerprint);'))

    def supports(self):
        references = self.command('references')
        projection = references['timberSupports']
        self.assertEqual('native-timber-supports/1', projection['schema'])
        self.assertEqual(references['sourceFingerprint'], projection['sourceFingerprint'])
        self.assertEqual(len(references['timbers']), len(projection['entries']))
        self.assertEqual(len(projection['entries']), len({e['id'] for e in projection['entries']}))
        return {e['id']: e for e in projection['entries']}

    def rectangle(self, frame='origin 0 0 2500 u +x v +y', surface=1, hole=''):
        self.line(f'surface {surface} {frame} outline 0,0 4000,0 4000,3000 0,3000{hole}')

    def primary(self, direction='+v', depth='+n', support_dirs=('+u', '+u'), selector='', surface=1):
        self.scene([f'timber 0 20 33 role boundary', f'place 0 on {surface} at-face e0 {support_dirs[0]} {depth}',
                    'timber 91 20 33 role boundary', f'place 91 on {surface} at-face e2 {support_dirs[1]} {depth}',
                    'spec center 500', f'guide 0 {surface} v spec:center',
                    'timber 7 27 33 role primary', f'place 7 on {surface} at-line guide 0 {selector} {direction} {depth}'])

    def assert_face(self, endpoint, timber, face, at, normal):
        self.assertEqual('exact', endpoint['status'])
        relation = endpoint['relation']
        self.assertEqual({'kind': 'timber', 'id': timber}, relation['source'])
        self.assertEqual(face, relation['localFace'])
        self.assertEqual(at, endpoint['at'])
        self.assertEqual(normal, relation['normalWorld'])

    def test_auto_supports_preserve_zero_id_and_odd_integer_width(self):
        self.rectangle()
        self.primary()
        entry = self.supports()[7]
        self.assert_face(entry['start'], 0, 'B1', 20, [0, 1, 0])
        self.assert_face(entry['finish'], 91, 'B0', 2980, [0, -1, 0])
        self.assertEqual([487, 514], entry['start']['crossRange'])
        self.assertEqual([0, 4000], entry['start']['relation']['stop']['range'])
        self.assertIsNone(entry['owner'])

    def test_negative_direction_and_depth_change_physical_end_and_local_face(self):
        self.rectangle()
        self.primary(direction='-v', depth='-n')
        entry = self.supports()[7]
        self.assert_face(entry['start'], 91, 'B1', 2980, [0, -1, 0])
        self.assert_face(entry['finish'], 0, 'B0', 20, [0, 1, 0])
        self.assertEqual([487, 514], entry['finish']['crossRange'])

    def test_support_direction_changes_face_labels_without_changing_relations(self):
        self.rectangle()
        self.primary(support_dirs=('-u', '-u'))
        entry = self.supports()[7]
        self.assert_face(entry['start'], 0, 'B0', 20, [0, 1, 0])
        self.assert_face(entry['finish'], 91, 'B1', 2980, [0, -1, 0])

    def test_rotated_vertical_frame_retains_world_normals(self):
        self.rectangle('origin 100 -200 300 u -y v +z')
        self.primary()
        entry = self.supports()[7]
        self.assert_face(entry['start'], 0, 'B1', 20, [0, 0, 1])
        self.assert_face(entry['finish'], 91, 'B0', 2980, [0, 0, -1])

    def test_between_selector_order_is_not_physical_end_order(self):
        self.rectangle()
        self.primary(selector='between t91 t0')
        entry = self.supports()[7]
        self.assert_face(entry['start'], 0, 'B1', 20, [0, 1, 0])
        self.assert_face(entry['finish'], 91, 'B0', 2980, [0, -1, 0])

    def test_outline_and_hole_edges_are_typed_and_d11_deduped(self):
        self.rectangle(hole=' hole 3300,500 3800,500 3800,800 3300,800 hole 3300,2200 3800,2200 3800,2500 3300,2500')
        self.scene(['timber 0 27 33 role boundary', 'place 0 on 1 at-face e0 +u +n',
                    'spec center 3500', 'guide 0 1 v spec:center',
                    'timber 7 27 33 role primary', 'place 7 on 1 at-line guide 0 between h1e0 h0e2 +v +n'])
        entries = self.supports()
        # The boundary timber's footprint lies on e0; its own ends are e3/e1,
        # never its own face or a second representation of the same edge.
        for end, edge in [('start', 3), ('finish', 1)]:
            r = entries[0][end]['relation']
            self.assertEqual('outline-edge', r['kind'])
            self.assertEqual({'kind': 'boundary', 'id': 1}, r['source'])
            self.assertEqual(edge, r['edgeIndex'])
            self.assertIsNone(r['holeIndex'])
        for end, hole, edge, at in [('start', 0, 2, 800), ('finish', 1, 0, 2200)]:
            r = entries[7][end]['relation']
            self.assertEqual(('hole-edge', hole, edge, at), (r['kind'], r['holeIndex'], r['edgeIndex'], r['stop']['at']))

    def test_embedded_rectangle_edges_belong_to_placement_zero(self):
        self.scene(['placement 0 origin 0 0 0 u +x v +y rect 0 0 4000 3000',
                    'timber 0 27 33 role boundary', 'place 0 on 0 at-face e0 -u +n'])
        entry = self.supports()[0]
        self.assertEqual({'kind': 'placement', 'id': 0}, entry['start']['relation']['source'])
        self.assertEqual(1, entry['start']['relation']['edgeIndex'])
        self.assertEqual(3, entry['finish']['relation']['edgeIndex'])

    def assembly_request(self, operations, generation=False):
        read = self.command('assembly-read')
        schema = 'assembly-generation-transaction/1' if generation else 'assembly-transaction/1'
        path = Path(self.directory.name) / 'transaction.json'
        path.write_text(json.dumps({'schema': schema, 'expectedRevision': read['revision'], 'operations': operations}))
        response = self.command(('assembly-generation-preview ' if generation else 'assembly-preview ') + str(path))
        self.assertTrue(response.get('ok'), response)
        self.assertTrue(response['preview']['valid'], response)
        return response['preview']

    def generate(self):
        self.rectangle()
        self.scene(['timber 90 20 20 role boundary', 'place 90 on 1 at-face e0 +u +n',
                    'timber 91 20 20 role boundary', 'place 91 on 1 at-face e2 +u +n',
                    'spec pos1 500', 'guide 1 1 v spec:pos1', 'spec pos2 2500', 'guide 2 1 v spec:pos2',
                    'spec pos3 1500', 'guide 3 1 u spec:pos3'])
        b = binding()
        for slot in b['slots']:
            slot['orientation'] = 'A'
        preview = self.assembly_request([{'op': 'publish-rule', 'value': rule()}, {'op': 'create-binding', 'value': b}])
        self.assertTrue(self.command('assembly-confirm ' + str(preview['token']))['ok'])
        state = self.command('assembly-read')['state']
        source = {'id': 1, 'name': 'native source', 'bindingId': 1,
                  'rule': {'id': 1, 'version': 1, 'fingerprint': state['rules'][0]['fingerprint']}, 'surfaceId': 1,
                  'members': [{'memberId': m, 'role': 'primary' if m < 3 else 'secondary', 'guideId': m,
                               'dir': '+v' if m < 3 else '+u', 'depthSide': '+n',
                               'ends': {'start': {'kind': 'timber', 'id': 91}, 'finish': {'kind': 'timber', 'id': 90}} if m < 3 else
                               {'start': {'kind': 'member', 'memberId': 1}, 'finish': {'kind': 'member', 'memberId': 2}}}
                              for m in [1, 2, 3]]}
        preview = self.assembly_request([{'op': 'create-instance', 'value': source,
                                         'expectedBindingFingerprint': state['bindings'][0]['fingerprint']}], True)
        self.assertTrue(self.command('assembly-confirm ' + str(preview['token']))['ok'])

    def test_owned_mapping_and_fixed_source_versions_match_real_native_assembly(self):
        self.generate()
        refs = self.command('references')
        instance = refs['assembly']['instances'][0]
        mapping = {m['memberId']: m['timberId'] for m in instance['members']}
        entries = self.supports()
        secondary = entries[mapping[3]]
        self.assert_face(secondary['start'], mapping[1], 'B0', 514, [1, 0, 0])
        self.assert_face(secondary['finish'], mapping[2], 'B1', 2487, [-1, 0, 0])
        for member, timber in mapping.items():
            o = entries[timber]['owner']
            self.assertEqual((1, member, 1, 1, 1), tuple(o[k] for k in ['instanceId', 'memberId', 'bindingId', 'ruleId', 'ruleVersion']))
            self.assertEqual(instance['fingerprint'], o['instanceFingerprint'])
            self.assertEqual(refs['assembly']['rules'][0]['fingerprint'], o['ruleFingerprint'])
            self.assertEqual(refs['assembly']['bindings'][0]['fingerprint'], o['bindingFingerprint'])
        self.assertEqual(entries[mapping[1]]['owner'], secondary['start']['relation']['owner'])
        self.assertEqual(entries[mapping[2]]['owner'], secondary['finish']['relation']['owner'])
        self.assertEqual(90, entries[mapping[1]]['start']['relation']['source']['id'])

    def test_projection_is_read_only_and_does_not_consume_pending_token_or_history(self):
        self.rectangle()
        self.primary()
        before = self.dump()
        refs = self.command('references')
        pending = self.command('line spec center 600')['preview']
        self.assertTrue(pending['valid'])
        for _ in range(3):
            self.assertEqual(refs, self.command('references'))
        self.assertEqual(before, self.dump())
        self.assertTrue(self.command('line confirm ' + str(pending['token']))['ok'])
        changed = self.command('references')
        self.assertNotEqual(refs['sourceFingerprint'], changed['sourceFingerprint'])
        self.assertEqual([587, 614], changed['timberSupports']['entries'][2]['start']['crossRange'])
        self.line('undo')
        undone = self.command('references')
        self.assertEqual(refs['sourceFingerprint'], undone['sourceFingerprint'])
        self.assertEqual(refs['timberSupports']['entries'], undone['timberSupports']['entries'])
        self.line('redo')
        self.assertEqual(changed['timberSupports']['entries'], self.command('references')['timberSupports']['entries'])

    def test_projection_roundtrips_from_saved_scene_in_fresh_native_process(self):
        self.generate()
        before = self.command('references')
        path = Path(self.directory.name) / 'saved.scene'
        path.write_text(self.dump())
        with BridgeSession(self.binary, cwd=self.directory.name) as fresh:
            self.assertTrue(fresh.command('loadfile ' + str(path))['ok'])
            after = fresh.command('references')
        self.assertEqual(before['sourceFingerprint'], after['sourceFingerprint'])
        self.assertEqual(before['timberSupports']['entries'], after['timberSupports']['entries'])

    def test_missing_ambiguous_and_free_facts_stay_unknown_without_modifying_world(self):
        self.rectangle()
        self.primary()
        before, references = self.dump(), self.command('references')
        # Invalid input is fault-injected only into a test-local read copy.
        missing = self.command('__support_missing')['entries'][0]
        self.assertEqual(7, missing['id'])
        for end in ['start', 'finish']:
            self.assertEqual('unknown', missing[end]['status'])
            self.assertIsNone(missing[end]['relation'])
        for command in ['__support_ambiguous', '__support_free']:
            value = self.command(command)
            self.assertEqual('unknown', value['status'])
            self.assertIsNone(value['relation'])
        self.assertEqual(before, self.dump())
        self.assertEqual(references, self.command('references'))

    def test_real_reference_projection_schedule_adapter_and_csv_count_each_native_placement_once(self):
        self.generate()
        references = self.command('references')
        script = """
          const fs=require('node:fs'),assert=require('node:assert/strict');
          const core=require('./geometry-web/timber-schedule.js');
          const s=require('./geometry-web/timber-supports.js')(core);
          const refs=JSON.parse(fs.readFileSync(0,'utf8')),snapshot=s.derive(refs,1);
          assert.equal(snapshot.rows.length,5);
          assert.equal(new Set(snapshot.ids).size,5);
          assert.equal(snapshot.rows.filter(r=>r.assembly).length,3);
          assert(snapshot.rows.every(r=>r.supports.start.status==='exact'&&r.supports.finish.status==='exact'));
          const row=snapshot.rows.find(r=>r.assembly?.memberId===3);
          assert.equal(row.L,1973);
          assert.equal(row.supports.start.relation.localFace,'B0');
          assert.equal(row.supports.start.relation.owner.memberId,1);
          assert(s.sourceText(row).includes('B0'));
          assert(s.csv(snapshot).includes('start_support_provenance'));
          assert(s.csv(snapshot).includes('instanceFingerprint'));
          assert.deepEqual(s.derive(refs,1,[row.id]).ids,[row.id]);
        """
        result = subprocess.run(['node', '-e', script], input=json.dumps(references), cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
