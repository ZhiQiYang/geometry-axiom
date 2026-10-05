from pathlib import Path
import datetime, hashlib, json, os, subprocess, time
from urllib.request import urlopen

root = Path('/workspace/geometry-axiom')
out = Path('/tmp/geometry-issue123-gates')
out.mkdir(exist_ok=True)
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
receipts, running, services = {}, {}, []

def stamp(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

try:
    for index, (label, flag) in enumerate([('grid', 'GEOMETRY_GRID_SYSTEM_ONLY'), ('parameters', 'GEOMETRY_PARAMETERS_ONLY'), ('composition', 'GEOMETRY_COMPOSITION_ONLY'), ('uiux', 'GEOMETRY_UIUX_FIX_ONLY')]):
        port = 8875 + index
        feedback = str(out / (label + '-feedback'))
        env = dict(os.environ, GEOMETRY_BRIDGE=str(root / '.build/web_bridge'), GEOMETRY_MODEL_BASE=str(root / '.build/model_base'), GEOMETRY_FEEDBACK_DIR=feedback)
        with (out / (label + '-server.log')).open('wb') as log:
            server = subprocess.Popen(['python3', 'geometry-web/serve.py', str(port)], cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
        services.append(server)
        url = f'http://127.0.0.1:{port}/'
        for attempt in range(100):
            try:
                runtime = json.load(urlopen(url + 'runtime', timeout=1))
                break
            except Exception:
                if server.poll() is not None: raise RuntimeError(label + ' server failed')
                time.sleep(.1)
        else: raise RuntimeError(label + ' server timed out')
        assert runtime['fresh'] and Path(runtime['root']).resolve() == root
        env.update(GEOMETRY_TEST_URL=url, GEOMETRY_CHROME='/usr/bin/chromium', GEOMETRY_CHROME_FLAGS='--no-sandbox', GEOMETRY_CDP_PORT=str(9475 + index), GEOMETRY_CHROME_PROFILE=str(out / (label + '-chrome')), GEOMETRY_GRID_TRIAL_SCREENSHOT_DIR=str(out / (label + '-screens')))
        env[flag] = '1'
        command = ['node', 'geometry-web/cdp_test.js']
        with (out / (label + '.log')).open('wb') as log:
            process = subprocess.Popen(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
        receipts[label] = {'head': head, 'command': command, 'scopeFlag': flag, 'url': url, 'feedbackDirectory': feedback, 'runtime': runtime, 'startedAtUTC': stamp(), 'pid': process.pid}
        running[label] = process
        print('START ' + label, flush=True)
    started = time.monotonic()
    while running:
        for label, process in list(running.items()):
            status = process.poll()
            if status is None: continue
            receipts[label].update(exitCode=status, finishedAtUTC=stamp())
            result = next((line.removeprefix('CDP_RESULT ') for line in (out / (label + '.log')).read_text().splitlines() if line.startswith('CDP_RESULT ')), None)
            if result: receipts[label]['result'] = json.loads(result)
            print('DONE ' + label + ' ' + str(status), flush=True)
            del running[label]
        (out / 'receipts.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + '\n')
        if time.monotonic() - started > 1200: raise RuntimeError('Gate timeout')
        if running: time.sleep(.5)
finally:
    for process in running.values():
        process.terminate()
        process.wait(timeout=10)
    for server in services:
        server.terminate()
        server.wait(timeout=10)

raise SystemExit(any(r.get('exitCode', 1) != 0 for r in receipts.values()))
