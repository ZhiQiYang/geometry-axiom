import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'geometry-web'))
import engineering_transport as transport


class EngineeringTransport(unittest.TestCase):
    def test_server_owned_exact_bytes_and_cleanup(self):
        payload = json.dumps({'schema':'engineering-transaction/1','operations':[{'op':'publish-material'}],
                              'expectedRevision':3}, ensure_ascii=False).encode()
        paths = []
        def bridge(command):
            self.assertTrue(command.startswith('engineering-preview '))
            path = Path(command.split(' ', 1)[1]); paths.append(path)
            self.assertEqual(path.read_bytes(), payload)
            return b'{"ok":true}'
        self.assertEqual(transport.file_request(payload, bridge), b'{"ok":true}')
        self.assertFalse(paths[0].exists())

    def test_generation_schema_dispatch_preserves_exact_payload_and_cleans_file(self):
        payload=json.dumps({'schema':'assembly-generation-transaction/1','expectedRevision':3,'operations':[{'op':'create-instance','value':{'name':'來源'}}]},ensure_ascii=False).encode()
        paths=[]
        def bridge(command):
            self.assertTrue(command.startswith('assembly-generation-preview '));path=Path(command.split(' ',1)[1]);paths.append(path);self.assertEqual(payload,path.read_bytes());return b'{"ok":true}'
        self.assertTrue(json.loads(transport.file_request(payload,bridge,generation=True))['ok']);self.assertFalse(paths[0].exists())
        self.assertFalse(json.loads(transport.file_request(payload,lambda _:self.fail('wrong schema dispatched'),assembly=True))['ok'])

    def test_panel_fill_schema_dispatch_preserves_exact_payload_and_cleans_file(self):
        payload=json.dumps({'schema':'panel-fill-transaction/1','expectedRevision':4,'operations':[{'op':'put-finish-surface','value':{'name':'天花'}}]},ensure_ascii=False).encode()
        paths=[]
        def bridge(command):
            self.assertTrue(command.startswith('panel-fill-preview '));path=Path(command.split(' ',1)[1]);paths.append(path);self.assertEqual(payload,path.read_bytes());return b'{"ok":true}'
        self.assertTrue(json.loads(transport.file_request(payload,bridge,panel_fill=True))['ok']);self.assertFalse(paths[0].exists())
        self.assertFalse(json.loads(transport.file_request(payload,lambda _:self.fail('wrong schema dispatched'),section_profile=True))['ok'])
        self.assertFalse(json.loads(transport.file_request(payload,lambda _:self.fail('wrong schema dispatched')))['ok'])

    def test_cleanup_after_bridge_failure(self):
        paths = []
        def bridge(command):
            paths.append(Path(command.split(' ',1)[1])); raise OSError('test')
        with self.assertRaises(OSError):
            transport.file_request(b'requires engineering-spec/1\n', bridge, validate_scene=True)
        self.assertFalse(paths[0].exists())

    def test_invalid_envelopes_never_reach_core(self):
        base = {'schema':'engineering-transaction/1','operations':[{}],'expectedRevision':0}
        cases = [b'', b'\xff', b'{}', b'{"schema":"x","schema":"y"}', b'\0', b'x' * (transport.MAX_BYTES+1)]
        # Keep the envelope otherwise valid. Two invalid schema values would
        # still reject even if duplicate-key detection were accidentally removed.
        valid = json.dumps(base).encode()
        cases.extend([
            valid.replace(b'"schema":', b'"schema":"engineering-transaction/1","schema":'),
            valid.replace(b'[{}]', b'[{"value":{"width":915,"width":910}}]'),
            valid.replace(b'[{}]', b'[{"value":{"width":NaN}}]'),
        ])
        for patch in ({'expectedRevision':True},{'expectedRevision':-1},{'operations':[]},
                      {'operations':[{}]*257},{'path':'/user/file'}, {'schema':'unknown'}):
            cases.append(json.dumps(dict(base,**patch)).encode())
        for data in cases:
            with self.subTest(data=data[:80]):
                def forbidden(_):
                    self.fail('invalid input reached core')
                self.assertFalse(json.loads(transport.file_request(data, forbidden))['ok'])

    def test_scene_validation_forwards_exact_bytes_to_the_validate_command(self):
        payload = 'requires engineering-spec/1\n# 面材\n'.encode()
        def bridge(command):
            self.assertTrue(command.startswith('engineering-validate '))
            self.assertEqual(Path(command.split(' ',1)[1]).read_bytes(), payload)
            return b'{"ok":false,"code":"SCENE_ERROR"}'
        self.assertFalse(json.loads(transport.file_request(payload, bridge, validate_scene=True))['ok'])

    def test_empty_world_with_only_unpublished_drafts_is_validatable(self):
        def bridge(command):
            self.assertTrue(command.startswith('engineering-validate '))
            self.assertEqual(Path(command.split(' ', 1)[1]).read_bytes(), b'')
            return b'{"ok":true,"required_capabilities":[]}'
        self.assertTrue(json.loads(transport.file_request(b'', bridge, validate_scene=True))['ok'])


if __name__ == '__main__':
    unittest.main()
