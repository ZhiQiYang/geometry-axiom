"""Launch-only adapter; no fixture, action, expectation or floor changes."""
import json
import sys
from playwright.sync_api import BrowserType

for _method in ('launch', 'launch_persistent_context'):
    _original = getattr(BrowserType, _method)
    def _wrap(original):
        def wrapped(self, *args, **kwargs):
            kwargs['chromium_sandbox'] = True
            kwargs['args'] = [x for x in kwargs.get('args', []) if x not in ('--no-sandbox', '--disable-setuid-sandbox', '--no-proxy-server')]
            print('CLOSEOUT_BROWSER_LAUNCH '+json.dumps({'sandbox': True, 'args': kwargs['args']}), file=sys.stderr)
            return original(self, *args, **kwargs)
        return wrapped
    setattr(BrowserType, _method, _wrap(_original))
