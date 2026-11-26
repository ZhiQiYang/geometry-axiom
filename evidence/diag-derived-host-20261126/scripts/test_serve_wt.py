"""只測啟停身分核對；以暫存工作樹模擬 start_local 以同一 PID exec 成 serve。"""
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).with_name('serve-wt.sh').resolve()


class OwnedServiceTest(unittest.TestCase):
    def test_only_stop_recorded_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            wt, fb = Path(tmp) / 'wt', Path(tmp) / 'fb'
            web = wt / 'geometry-web'
            web.mkdir(parents=True)
            (web / 'start_local.py').write_text(
                "import os, sys\nfrom pathlib import Path\n"
                "if '--build-only' not in sys.argv:\n"
                "    os.execv(sys.executable, [sys.executable, '-u', str(Path(__file__).with_name('serve.py')), sys.argv[-1]])\n")
            (web / 'serve.py').write_text(
                "import os, time\nfrom pathlib import Path\nPath('ready').write_text(str(os.getpid()))\ntime.sleep(30)\n")
            (web / 'runtime_version.py').write_text(
                "import json\nfrom pathlib import Path\nprint(json.dumps({'pid': int(Path('ready').read_text()), 'session': 'test-session', 'version': 'test-version'}))\n")

            def run(*opts, port, ok, contains=''):
                r = subprocess.run([SCRIPT, *opts, wt, str(port), fb], text=True, capture_output=True,
                                   env={**os.environ, 'TMPDIR': tmp}, timeout=15)
                self.assertEqual(r.returncode == 0, ok, r.stdout + r.stderr)
                self.assertIn(contains, r.stdout + r.stderr)
                return r.stdout

            with socket.socket() as listener:
                listener.bind(('127.0.0.1', 0))
                listener.listen()
                port = listener.getsockname()[1]
                run(port=port, ok=False)  # 已占用，連建置與 PID 紀錄都不該開始。
                self.assertFalse(fb.exists())
                run('--stop', port=port, ok=False, contains='找不到本次測試')
            pid = json.loads(run(port=port, ok=True))['pid']
            state = fb / 'server-pid.json'
            original = json.loads(state.read_text())
            self.assertEqual(pid, original['pid'])
            try:
                self.assertEqual((original['session'], original['version']), ('test-session', 'test-version'))
                for bad in [dict(original, startTicks=original['startTicks'] + 1),
                            dict(original, port=1024 if port != 1024 else 1025)]:
                    state.write_text(json.dumps(bad))
                    run('--stop', port=bad['port'], ok=False, contains='未送出停止訊號')
            finally:
                state.write_text(json.dumps(original))
                run('--stop', port=port, ok=True, contains=f'已停止本次測試服務 PID {pid}')
            run('--stop', port=port, ok=False)  # 不從其他行程補找已退出的 PID。


if __name__ == '__main__':
    unittest.main()
