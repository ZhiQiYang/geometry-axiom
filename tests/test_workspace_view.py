"""H-116-VIEW/1: real native typed drawing/picking and closed read transport.

GEOMETRY_TEST_BRIDGE selects the exact compiled source under test. The named
assertions are also the mutation oracles; no rendering or geometry is mocked.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.test_timber_edit import Session


class WorkspaceViewNative(unittest.TestCase):
    FIXTURE = (
        'boundary 71 outline 0,0 4000,0 4000,3000 0,3000 hole 1600,1200 2200,1200 2200,1800 1600,1800',
        'placement 19 on boundary 71 origin 100 200 300 u +x v +y',
        'spec 偏移 400', 'guide 0 19 v spec:偏移',
        'timber 71 27 33 role boundary', 'place 71 on 19 at-face e0 +u +n',
        'column 71 at 6000 800 size 200 200 z 0 600',
        'column 0 at 6300 800 size 200 200 z 0 600',
    )

    @classmethod
    def setUpClass(cls):
        cls.executable = os.environ.get('GEOMETRY_TEST_BRIDGE')
        if not cls.executable:
            raise unittest.SkipTest('GEOMETRY_TEST_BRIDGE is required')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='workspace-view-')
        self.addCleanup(self.temp.cleanup)
        self.session = Session(self.executable)
        self.addCleanup(self.finish)
        self.command('reset')
        for line in self.FIXTURE:
            reply = self.command('line ' + line)
            if 'preview' in reply:
                self.assertTrue(reply['preview']['valid'], reply)
                reply = self.command('line confirm ' + str(reply['preview']['token']))
            self.assertTrue(reply['ok'], (line, reply))
        self.revision = str(self.command('engineering-read')['revision'])

    def finish(self):
        output = os.environ.get('GEOMETRY_VIEW_RECEIPTS')
        if output:
            path = Path(output); path.mkdir(parents=True, exist_ok=True)
            (path / (self._testMethodName + '.json')).write_text(json.dumps({
                'case': self.id(), 'binary_sha256': hashlib.sha256(Path(self.executable).read_bytes()).hexdigest(),
                'receipts': self.session.receipts}, ensure_ascii=False, indent=2), encoding='utf-8')
        self.session.stop()

    def command(self, text):
        return self.session.command(text)

    def packet(self, command, data):
        path = Path(self.temp.name) / 'request.json'
        path.write_bytes(data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode())
        return self.command(command + ' ' + str(path))

    def request(self, focus=None, hidden=(), layers=('face', 'guide', 'timber', 'rc')):
        return {'schema': 'workspace-view/1', 'expectedRevision': self.revision,
                'scope': {'kind': 'project'},
                'presentation': {'mode': 'focus' if focus else 'three', 'focus': focus},
                'layers': list(layers), 'hidden': list(hidden)}

    def read(self, **kwargs):
        reply = self.packet('view-read', self.request(**kwargs))
        self.assertEqual(reply.get('status'), 'READY', 'KILLER[view_read_entry] ' + repr(reply))
        self.assertEqual(reply['schema'], 'workspace-view-result/1')
        return reply

    def pick(self, read, view, x, y, radius=4):
        return self.packet('view-pick', {'schema': 'workspace-view-pick/1',
                           'expectedRevision': self.revision, 'viewKey': read['viewKey'],
                           'viewId': view, 'point': {'x': x, 'y': y}, 'radius': radius})

    def test_native_typed_roots_owner_and_holes(self):
        before = self.command('dump')
        legacy_render, legacy_pick = self.command('render'), self.command('pick 2 6100 900 4')
        read = self.read(focus='top')
        self.assertTrue(all('owner' in op for op in read['ops']), 'KILLER[draw_owner]')
        owners = {(op['owner']['kind'], op['owner']['id']) for op in read['ops'] if op['owner']}
        self.assertTrue({('boundary', 71), ('timber', 71), ('column', 71), ('column', 0), ('guide', 0)} <= owners,
                        'KILLER[typed_root_ids] ' + repr(owners))
        face = self.pick(read, 'top', 1100, -1100)
        self.assertEqual(face['target'], {'root': {'kind': 'boundary', 'id': 71},
                         'placementId': 19, 'boundaryId': 71, 'memberFace': None}, 'KILLER[boundary_not_index]')
        hole = self.pick(read, 'top', 2000, -1700)
        self.assertEqual(hole['status'], 'NONE', 'KILLER[hole_not_bbox]')
        column = self.pick(read, 'top', 6100, -900)
        self.assertEqual(column['target'], {'root': {'kind': 'column', 'id': 71},
                         'placementId': None, 'boundaryId': None, 'memberFace': None}, 'KILLER[column_typed]')
        timber = self.pick(read, 'top', 1000, -210)
        self.assertEqual(timber['target']['root'], {'kind': 'timber', 'id': 71}, 'KILLER[painter_timber]')
        self.assertEqual(timber['target']['boundaryId'], 71)
        self.assertEqual(timber['target']['placementId'], 19)
        self.assertIn(timber['target']['memberFace'], ('A0', 'A1', 'B0', 'B1', 'START', 'END'))
        self.assertEqual(self.command('dump'), before, 'KILLER[readonly_world]')
        self.assertEqual(self.command('render'), legacy_render, 'KILLER[legacy_render_unchanged]')
        self.assertEqual(self.command('pick 2 6100 900 4'), legacy_pick, 'KILLER[legacy_pick_unchanged]')
        self.assertEqual(column['hoverOps'][0]['op'], 'begin')
        self.assertEqual(column['hoverOps'][0]['viewId'], 'top')
        self.assertEqual(column['hoverOps'][0]['tx'], read['layout']['views'][0]['tx'])
        self.assertEqual(column['hoverOps'][-1]['op'], 'end')

    def test_top_bottom_and_degenerate_face_use_same_native_frames(self):
        top, bottom = self.read(focus='top'), self.read(focus='bottom')
        self.assertEqual(top['layout']['views'][0]['right'], [1, 0, 0])
        self.assertEqual(top['layout']['views'][0]['down'], [0, -1, 0], 'KILLER[top_is_not_bottom]')
        self.assertEqual(bottom['layout']['views'][0]['down'], [0, 1, 0])
        for read, view, y in ((top, 'top', -1100), (bottom, 'bottom', 1100)):
            self.assertEqual(self.pick(read, view, 1100, y)['target']['root'], {'kind': 'boundary', 'id': 71},
                             'KILLER[draw_pick_same_frame]')
            self.assertEqual(self.pick(read, view, 1100, -y)['status'], 'NONE')
        front = self.read(focus='front', layers=('face',))
        self.assertEqual(self.pick(front, 'front', 1000, -300)['target']['root'], {'kind': 'boundary', 'id': 71},
                         'KILLER[degenerate_surface_line]')
        self.assertEqual(self.pick(front, 'front', 1000, -400)['status'], 'NONE')

    def test_hide_one_root_filters_drawing_and_pick_without_hiding_class_or_dependencies(self):
        hidden = ({'kind': 'column', 'id': 71},)
        read = self.read(focus='top', hidden=hidden)
        owners = [op['owner'] for op in read['ops']]
        self.assertNotIn({'kind': 'column', 'id': 71}, owners, 'KILLER[hidden_drawing]')
        self.assertIn({'kind': 'column', 'id': 0}, owners, 'KILLER[hide_single_root]')
        self.assertEqual(self.pick(read, 'top', 6100, -900)['status'], 'NONE', 'KILLER[hidden_pick]')
        self.assertEqual(self.pick(read, 'top', 6400, -900)['target']['root'], {'kind': 'column', 'id': 0})
        face_hidden = self.read(focus='top', hidden=({'kind': 'boundary', 'id': 71},))
        self.assertEqual(self.pick(face_hidden, 'top', 1100, -1100)['status'], 'NONE')
        self.assertEqual(self.pick(face_hidden, 'top', 1000, -210)['target']['root'], {'kind': 'timber', 'id': 71},
                         'KILLER[hide_not_dependencies]')
        self.assertEqual(self.pick(face_hidden, 'top', 500, -1100)['target']['root'], {'kind': 'guide', 'id': 0})
        duplicates = self.read(focus='top', hidden=hidden * 2)
        self.assertEqual(duplicates['ops'], read['ops'])
        no_rc = self.read(focus='top', layers=('face', 'guide', 'timber'))
        self.assertEqual(self.pick(no_rc, 'top', 6400, -900)['status'], 'NONE', 'KILLER[layer_pick_intersection]')

    def test_key_scope_session_revision_and_readonly(self):
        a, b = self.read(focus='top'), self.read(focus='bottom')
        self.assertNotEqual(a['viewKey'], b['viewKey'])
        self.assertEqual(self.pick(a, 'top', 1100, -1100)['status'], 'HIT', 'KILLER[multiple_views]')
        wrong = self.pick(a, 'bottom', 1100, 1100)
        self.assertEqual(wrong['status'], 'INVALID', 'KILLER[key_frame_scope]')
        other = Session(self.executable); self.addCleanup(other.stop)
        other.command('reset')
        for line in self.FIXTURE:
            result = other.command('line ' + line)
            if 'preview' in result:
                result = other.command('line confirm ' + str(result['preview']['token']))
            self.assertTrue(result['ok'], result)
        self.assertEqual(str(other.command('engineering-read')['revision']), self.revision)
        self.read(focus='top')
        other_read = other.command('view-read ' + str(Path(self.temp.name) / 'request.json'))
        self.assertEqual(other_read['status'], 'READY')
        self.assertNotEqual(other_read['viewKey'], a['viewKey'], 'KILLER[session_key_guard]')
        self.pick(a, 'top', 1100, -1100)
        self.assertEqual(other.command('view-pick ' + str(Path(self.temp.name) / 'request.json'))['status'],
                         'STALE', 'KILLER[session_key_guard]')
        self.command('line spec 變更 1')
        stale = self.pick(a, 'top', 1100, -1100)
        self.assertEqual(stale['status'], 'STALE', 'KILLER[revision_pick_guard]')
        self.assertIsNone(stale.get('viewKey'))
        stale_read = self.packet('view-read', self.request())
        self.assertEqual(stale_read['status'], 'STALE')
        self.revision = str(self.command('engineering-read')['revision'])
        missing = self.request()
        missing['scope'] = {'kind': 'space', 'id': 999}
        self.assertEqual(self.packet('view-read', missing)['status'], 'INVALID')

    def test_capabilities_placement_zero_and_pending_candidate_remain_authoritative(self):
        state = self.command('view-capabilities')
        self.assertEqual(state['schema'], 'workspace-view-capabilities/1')
        self.assertIn('workspace-view/1', state['capabilities'], 'KILLER[view_capability]')
        cap = state['workspace_view']
        self.assertEqual(cap, {'schema': 'workspace-view/1', 'frames': ['front', 'side', 'top', 'bottom'],
                              'maxHiddenRoots': 608, 'maxOps': 131072, 'maxRequestBytes': 1048576},
                         'KILLER[view_capacity_matches_root_limits]')
        self.assertTrue(self.command('line placement 0 origin 9000 200 300 u +x v +y rect 0 0 300 500')['ok'])
        self.revision = str(self.command('engineering-read')['revision'])
        before = self.command('dump')['text']
        pending = self.command('line preview spec 保留候選 2')['preview']
        read = self.read(focus='top')
        self.assertEqual(self.pick(read, 'top', 9100, -400)['target'],
                         {'root': {'kind': 'placement', 'id': 0}, 'placementId': 0, 'boundaryId': None, 'memberFace': None},
                         'KILLER[placement_zero_not_fake_boundary]')
        hidden = self.read(focus='top', hidden=({'kind': 'placement', 'id': 0},))
        self.assertEqual(self.pick(hidden, 'top', 9100, -400)['status'], 'NONE')
        alias = self.request(hidden=({'kind': 'placement', 'id': 19},))
        self.assertEqual(self.packet('view-read', alias)['status'], 'INVALID', 'KILLER[no_root_alias]')
        self.read(focus='top', hidden=({'kind': 'column', 'id': 71},) * 608)
        too_many = self.request(hidden=({'kind': 'column', 'id': 71},) * 609)
        self.assertEqual(self.packet('view-read', too_many)['status'], 'INVALID', 'KILLER[hidden_capacity]')
        self.assertTrue(self.command('line confirm ' + str(pending['token']))['ok'], 'KILLER[view_keeps_candidate]')
        self.assertTrue(self.command('line undo')['ok'])
        self.assertEqual(self.command('dump')['text'], before, 'KILLER[view_keeps_history]')

    def test_concave_outline_is_not_its_projected_bounding_box(self):
        for line in ('boundary 84 outline 0,0 2000,0 2000,600 600,600 600,2000 0,2000',
                     'placement 85 on boundary 84 origin 10000 0 0 u +x v +y'):
            self.assertTrue(self.command('line ' + line)['ok'])
        self.revision = str(self.command('engineering-read')['revision'])
        read = self.read(focus='top')
        self.assertEqual(self.pick(read, 'top', 10300, -1500)['target']['root'], {'kind': 'boundary', 'id': 84})
        self.assertEqual(self.pick(read, 'top', 11000, -1000)['status'], 'NONE', 'KILLER[outline_not_bbox]')

    def test_closed_native_json_rejects_malformed_unknown_and_out_of_range(self):
        self.read()
        before = self.command('dump')
        invalid = []
        for field, value in [('schema', 'other/1'), ('expectedRevision', 3), ('expectedRevision', '18446744073709551616'),
                             ('layers', ['face', 'unknown']), ('hidden', [{'kind': 'column', 'id': 4294967296}]),
                             ('hidden', [{'kind': 'guide', 'id': 987654}]), ('scope', {'kind': 'project', 'id': 1}),
                             ('presentation', {'mode': 'three', 'focus': 'top'})]:
            request = self.request(); request[field] = value; invalid.append(request)
        request = self.request(); request['path'] = '/tmp/injected'; invalid.append(request)
        raw = json.dumps(self.request()).encode()
        invalid.extend((raw.replace(b'"schema":', b'"schema":"workspace-view/1","schema":', 1),
                        raw.replace(b'"project"', b'"pro\\u0000ject"'), b'{}\x00',
                        raw.replace(b'"hidden": []', b'"hidden": [NaN]'), b'{}' * 600000,
                        raw.replace(b'"project"', b'"pro\\ud800ject"')))
        for request in invalid:
            with self.subTest(request=repr(request)[:150]):
                reply = self.packet('view-read', request)
                self.assertEqual(reply.get('status'), 'INVALID', 'KILLER[closed_native_input] ' + repr(reply))
                self.assertIsNone(reply.get('viewKey'))
        read = self.read(focus='top')
        for x, radius in ((True, 1), (1.5, 1), (400000001, 1), (0, -1), (0, 400000001)):
            self.assertEqual(self.pick(read, 'top', x, 0, radius).get('status'), 'INVALID')
        self.assertEqual(self.command('dump'), before)


class WorkspaceViewTransport(unittest.TestCase):
    def module(self):
        path = ROOT / 'geometry-web/workspace_view_transport.py'
        self.assertTrue(path.is_file(), 'KILLER[view_transport_entry]')
        spec = importlib.util.spec_from_file_location('workspace_view_transport', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module

    def test_declared_root_capacity_supports_512_timber_world(self):
        module = self.module()
        paths = []
        for count in (161, 608):
            request = {'schema': 'workspace-view/1', 'expectedRevision': '0', 'scope': {'kind': 'project'},
                       'presentation': {'mode': 'three', 'focus': None}, 'layers': ['timber'],
                       'hidden': [{'kind': 'timber', 'id': 71}] * count}
            body = json.dumps(request).encode()
            def bridge(command):
                name, path = command.split(' ', 1)
                self.assertEqual(name, 'view-read')
                paths.append(Path(path))
                self.assertEqual(paths[-1].read_bytes(), body)
                return b'{"ok":true}'
            self.assertEqual(module.file_request(body, bridge), b'{"ok":true}',
                             'KILLER[transport_root_capacity]')
            self.assertFalse(paths[-1].exists())
        request['hidden'] = [{'kind': 'timber', 'id': 71}] * 609
        result = json.loads(module.file_request(json.dumps(request).encode(),
                            lambda _: self.fail('KILLER[transport_over_capacity]')))
        self.assertEqual(result['status'], 'INVALID')

    def test_bounded_closed_server_generated_path_and_cleanup(self):
        module = self.module()
        request = {'schema': 'workspace-view/1', 'expectedRevision': '0', 'scope': {'kind': 'project'},
                   'presentation': {'mode': 'three', 'focus': None}, 'layers': ['face'], 'hidden': []}
        body = json.dumps(request).encode(); paths = []
        def bridge(command):
            name, path = command.split(' ', 1)
            self.assertEqual(name, 'view-read')
            paths.append(Path(path)); self.assertEqual(paths[-1].read_bytes(), body)
            return b'{"ok":true}'
        self.assertEqual(module.file_request(body, bridge), b'{"ok":true}')
        self.assertFalse(paths[-1].exists())
        bad = deepcopy(request); bad['path'] = '/tmp/arbitrary'
        for data in (json.dumps(bad).encode(), b'{}' * 600000,
                     body.replace(b'"schema":', b'"schema":"x","schema":', 1),
                     body.replace(b'"project"', b'"pro\\u0000ject"'),
                     body.replace(b'"hidden": []', b'"hidden": [Infinity]')):
            result = json.loads(module.file_request(data, lambda _: self.fail('KILLER[transport_reject_before_bridge]')))
            self.assertEqual(result['status'], 'INVALID')

    def test_pick_is_closed_and_tempfile_removed_after_bridge_failure(self):
        module = self.module()
        request = {'schema': 'workspace-view-pick/1', 'expectedRevision': '18446744073709551615',
                   'viewKey': 'a' * 64, 'viewId': 'top', 'point': {'x': -400000000, 'y': 400000000}, 'radius': 0}
        paths = []
        def bridge(command):
            name, path = command.split(' ', 1)
            self.assertEqual(name, 'view-pick'); paths.append(Path(path))
            raise OSError('deliberate bridge failure')
        with self.assertRaises(OSError):
            module.file_request(json.dumps(request).encode(), bridge, pick=True)
        self.assertFalse(paths[-1].exists(), 'KILLER[transport_cleanup]')
        for key, value in (('point', {'x': 0, 'y': 0, 'path': '/tmp/file'}), ('point', {'x': True, 'y': 0}),
                           ('radius', float('inf')), ('radius', -1), ('viewId', 'unknown'), ('viewKey', 'b'),
                           ('expectedRevision', '18446744073709551616')):
            bad = dict(request); bad[key] = value
            result = json.loads(module.file_request(json.dumps(bad).encode(),
                                lambda _: self.fail('KILLER[transport_reject_before_bridge]'), pick=True))
            self.assertEqual(result['status'], 'INVALID')


if __name__ == '__main__':
    program = unittest.main(exit=False, verbosity=2)
    receipt = os.environ.get('GEOMETRY_VIEW_ORACLES')
    if receipt:
        Path(receipt).write_text(json.dumps({'tests': program.result.testsRun,
            'failures': len(program.result.failures), 'errors': len(program.result.errors),
            'skipped': len(program.result.skipped)}, indent=2), encoding='utf-8')
    raise SystemExit(not program.result.wasSuccessful())
