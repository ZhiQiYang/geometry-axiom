"""HTTP handler wiring and path boundary; geometry runs in the native suite."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests import test_serve as serve_fixture


class WorkspaceViewServer(unittest.TestCase):
    def setUp(self):
        # Compose the existing transport fixture without inheriting its suites.
        self.host = serve_fixture.BridgeServerTests(); self.host.setUp()
        self.addCleanup(self.host.tearDown)

    def test_client_cannot_supply_view_paths_through_api_or_receipt_shortcuts(self):
        module = self.host.server_module
        with patch.object(module.RUNTIME, 'fresh', return_value=True):
            for command in ('view-read /tmp/client.json', 'view-pick /tmp/client.json', '\tview-read\t/tmp/client.json'):
                for receipt in ({}, {'receipt': None}, {'receipt': '00000000-0000-0000-0000-000000000000'}):
                    handler = self.host.post_handler('/api', json.dumps({'cmd': command, **receipt}).encode())
                    with patch.object(module, 'recorded_api', return_value=b'{"ok":true}') as recorded:
                        handler.do_POST()
                    self.assertFalse(recorded.called, 'KILLER[no_client_view_path]')
                    self.assertFalse(json.loads(handler._send.call_args.args[0])['ok'])

    def test_two_routes_use_bounded_server_files_and_only_the_matching_command(self):
        module = self.host.server_module
        read = {'schema': 'workspace-view/1', 'expectedRevision': '0', 'scope': {'kind': 'project'},
                'presentation': {'mode': 'three', 'focus': None}, 'layers': [], 'hidden': []}
        pick = {'schema': 'workspace-view-pick/1', 'expectedRevision': '0', 'viewKey': 'a' * 64,
                'viewId': 'top', 'point': {'x': 0, 'y': 0}, 'radius': 12}
        with patch.object(module.RUNTIME, 'fresh', return_value=True):
            for route, request, command in (('/view/read', read, 'view-read'), ('/view/pick', pick, 'view-pick')):
                handler = self.host.post_handler(route, length=1048577)
                handler.do_POST(); handler.send_error.assert_called_once_with(413)
                handler.rfile.read.assert_not_called()
                body = json.dumps(request).encode(); paths = []
                def native(value):
                    kind, path = value.split(' ', 1); self.assertEqual(kind, command)
                    paths.append(Path(path)); self.assertEqual(paths[-1].read_bytes(), body)
                    return b'{"ok":true}'
                handler = self.host.post_handler(route, body)
                with patch.object(module, 'ask_bridge', side_effect=native):
                    handler.do_POST()
                self.assertEqual(len(paths), 1, 'KILLER[view_http_route]')
                self.assertFalse(paths[0].exists())
                handler._send.assert_called_once_with(b'{"ok":true}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
