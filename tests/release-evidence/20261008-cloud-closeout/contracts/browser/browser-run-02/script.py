"""Private bounded browser acceptance. Launch only after the browser owner grants the slot.

Fixtures are seeded through apiRequest('loadfile ...') using the previously
verified synthetic native scenes. This is explicitly API fixture setup, not UI
authoring. Export/Save/New/Open use trusted Playwright clicks and file choosers.
showSaveFilePicker is disabled before page load to select the real download
fallback; no OS save dialog, physical mobile, IME or unrelated model gate claim.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import traceback
from urllib.parse import urlsplit
from urllib.request import urlopen
import zipfile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def stamp():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/workspace/geometry-axiom'))
    parser.add_argument('--url', required=True, help='Explicit isolated loopback service; default product port forbidden')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--chrome', default='/usr/bin/chromium')
    parser.add_argument('--bridge', type=Path, default=Path('/tmp/geometry-tests/bridge'))
    parser.add_argument('--width', type=int, choices=(1400, 390), action='append')
    parser.add_argument('--only', choices=('all', 'grid', 'assembly'), default='all')
    parser.add_argument('--grid-scene', type=Path, default=Path(__file__).parent / 'grid-final/grid-rule-timber.scene')
    parser.add_argument('--assembly-scene', type=Path, default=Path(__file__).parent / 'assembly-final/reopened-owned.scene')
    parser.add_argument('--accept-dirty', action='store_true', help='Explicitly retain dirty diff in receipt; default is clean only')
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    sys.path.insert(0, str(root / 'tests'))
    import binaries
    address = urlsplit(args.url)
    assert address.scheme == 'http' and address.hostname in ('127.0.0.1', 'localhost'), 'Isolated loopback HTTP required'
    assert address.port not in (None, 8765) and address.path == '/' and not any((address.query, address.fragment, address.username, address.password))
    assert not out.is_relative_to(root) and out != Path('/'), 'Evidence must stay outside the repo'
    out.mkdir(parents=True, exist_ok=False)
    receipt = {'schema': 'geometry-contract-browser-reopen/1', 'started': stamp(),
               'argv': [sys.executable, *sys.argv], 'cwd': str(Path.cwd()), 'script_sha256': sha(__file__),
               'python': sys.version, 'playwright': importlib.metadata.version('playwright'),
               'sandbox': True, 'launch_arguments_requested': [], 'accept_dirty': args.accept_dirty,
               'limits': ['API fixture setup; no UI geometry authoring claim',
                          'Real download fallback and Playwright file chooser; no OS save dialog claim',
                          'Native World/reference/assembly fixtures only; no model, PDF, image or unpublished draft fixture',
                          'Viewport 390 is desktop Chromium emulation; no physical-device or IME claim',
                          'Successful reopen may advance native revision; all raw revisions are retained',
                          'Rejected owned delete must preserve raw dump and assembly-read including revision'],
               'cases': [], 'exit_code': 1}
    phase = 'preflight'
    page = context = browser = None

    def identity(label):
        records = []
        for command in (['pwd'], ['git', 'rev-parse', 'HEAD'], ['git', 'rev-parse', 'HEAD^{tree}'],
                        ['git', 'rev-parse', 'origin/main'], ['git', 'rev-parse', 'origin/docs/save-reopen-contract-20261008'],
                        ['git', 'status', '--short'], ['git', 'diff', '--binary']):
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            records.append({'command': command, 'stdout': result.stdout, 'stderr': result.stderr, 'exit_code': result.returncode})
            assert result.returncode == 0, records[-1]
        runtime_bytes = urlopen(args.url + 'runtime', timeout=15).read()
        (out / (label + '-runtime.raw.json')).write_bytes(runtime_bytes)
        runtime = json.loads(runtime_bytes)
        bridge = args.bridge.resolve()
        bridge_info = binaries.inspect_one(binaries.BY_NAME['bridge'], path=bridge)
        assert bridge_info.state == 'fresh', bridge_info.as_dict()
        sidecar = bridge.with_name(bridge.name + binaries.SIDECAR_SUFFIX)
        (out / (label + '-bridge.fingerprint.json')).write_bytes(sidecar.read_bytes())
        process_list = subprocess.run(['ps', '-eo', 'pid=,ppid='], capture_output=True, text=True)
        write(out / (label + '-process-parent-list.json'), {
            'command': ['ps', '-eo', 'pid=,ppid='], 'stdout': process_list.stdout,
            'stderr': process_list.stderr, 'exit_code': process_list.returncode})
        assert process_list.returncode == 0, process_list.stderr
        parent_rows = [tuple(map(int, line.split())) for line in process_list.stdout.splitlines() if line.strip()]
        assert any(pid == runtime['pid'] for pid, parent in parent_rows), 'Runtime process is not live'
        descendants = []
        pending = [runtime['pid']]
        while pending:
            parent = pending.pop()
            for child, child_parent in parent_rows:
                if child_parent != parent:
                    continue
                executable = Path(f'/proc/{child}/exe')
                resolved = executable.resolve()
                descendants.append({'pid': child, 'executable': str(resolved),
                                    'running_sha256': sha(executable) if resolved == bridge else None})
                pending.append(child)
        active_bridges = [process for process in descendants if process['executable'] == str(bridge)]
        assert len(active_bridges) == 1 and active_bridges[0]['running_sha256'] == sha(bridge), 'Runtime process does not own the expected live bridge binary'
        value = {'checked_at': stamp(), 'commands': records, 'runtime': runtime,
                 'head': records[1]['stdout'].strip(), 'tree': records[2]['stdout'].strip(),
                 'bridge': {'registry': bridge_info.as_dict(), 'sha256': sha(bridge), 'service_descendants': descendants},
                 'status': records[5]['stdout'], 'dirty_diff_sha256': hashlib.sha256(records[6]['stdout'].encode()).hexdigest(),
                 'sources': {name: sha(root / name) for name in ('geometry-web/app.js', 'geometry-web/reference-workspace.js',
                             'geometry-web/project-store.js', 'geometry-web/serve.py', 'tests/test_assembly_generation.py',
                             'tests/test_grid_subdivision_oracle.py')}}
        write(out / (label + '-identity.json'), value)
        assert runtime.get('fresh') is True and Path(runtime['root']).resolve() == root, runtime
        assert args.accept_dirty or value['status'] == '', value['status']
        return value

    def ready():
        page.wait_for_function("connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy&&pendingApiResults.size===0", timeout=30000)

    def native(command):
        result = page.evaluate('async command => await apiRequest(command)', command)
        with (case_out / 'explicit-native-commands.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'time': stamp(), 'phase': phase, 'command': command, 'result': result}, ensure_ascii=False) + '\n')
        return result

    def snapshot(label):
        result = {command: native(command) for command in ('dump', 'objects', 'references', 'assembly-read')}
        assert all(value.get('ok') is True for value in result.values()), result
        result['project'] = page.evaluate('''async()=>{
            const c=ReferenceWorkspace.context();
            return {id:c.id,name:c.name,manifest:await ReferenceWorkspace.manifest(),
              sources:[...c.sources].map(([id,v])=>[id,Array.from(v.bytes)]),
              dirty:c.dirty,saved:c.saved,downloaded:c.downloaded};
        }''')
        result['canvas_cards'] = page.locator('.ocard[data-kind][data-id]').evaluate_all("nodes=>nodes.map(n=>n.dataset.kind+':'+n.dataset.id).sort()")
        write(case_out / (label + '.json'), result)
        (case_out / (label + '.scene')).write_text(result['dump']['text'], encoding='utf-8')
        return result

    def world_semantic(value):
        # Revision counts successful transactions; it is not serialized identity.
        # Every other field, including definition SHA and reference fingerprints,
        # remains in the equality comparison. Raw responses are always retained.
        return {key: ({k: v for k, v in value[key].items() if k != 'revision'}
                      if key in ('dump', 'assembly-read') else value[key])
                for key in ('dump', 'objects', 'references', 'assembly-read')}

    def project_semantic(value):
        return {key: value['project'][key] for key in ('id', 'name', 'manifest', 'sources')}

    def menu(selector):
        page.locator('#fileMenuBtn').click(timeout=10000)
        page.locator(selector).click(timeout=10000)

    def response_matches(response, endpoint):
        return response.request.method == 'POST' and urlsplit(response.url).path == endpoint

    def new_project(label):
        before_id = page.evaluate('ReferenceWorkspace.context().id')
        draw = page.evaluate('ocDrawCount')
        with page.expect_response(lambda response: response_matches(response, '/upload') and response.request.post_data == 'reset\n', timeout=30000) as received:
            menu('#btnNewProject')
        response = received.value
        assert response.status == 200 and response.json().get('ok') is True, response.text()
        page.wait_for_function('''arg=>ReferenceWorkspace.context().id!==arg.id && ocDrawCount>arg.draw &&
            document.querySelector('#status').textContent.startsWith('✓ 已建立空白新專案') &&
            !ReferenceWorkspace.busy && !oc.busy''', arg={'id': before_id, 'draw': draw}, timeout=30000)
        ready()
        value = snapshot(label)
        assert value['dump']['text'] == '', value['dump']
        assert all(not value['objects'][key] for key in ('faces', 'spaces', 'columns', 'beams', 'gridSystems',
                   'parameters', 'assemblyRules', 'assemblyBindings', 'gridBindings', 'timbers')), value['objects']
        assert value['assembly-read']['state']['instances'] == [], value['assembly-read']
        assert value['canvas_cards'] == [], value['canvas_cards']
        assert value['project']['manifest'].get('models', []) == []
        assert value['project']['manifest'].get('assemblyDrafts', {}).get('records', []) == []
        return value

    def open_file(path, project, label, expected_cards):
        draw = page.evaluate('ocDrawCount')
        endpoint = '/upload/confirm' if project else '/upload'
        with page.expect_response(lambda response: response_matches(response, endpoint), timeout=30000) as received:
            with page.expect_file_chooser(timeout=10000) as choosing:
                menu('#btnOpenProject' if project else '#btnOpen')
            choosing.value.set_files(str(path))
        response = received.value
        assert response.status == 200 and response.json().get('ok') is True, response.text()
        predicate = '''arg=>ocDrawCount>arg.draw && !ReferenceWorkspace.busy && !oc.busy &&
            document.querySelector(arg.input).value==='' &&
            (arg.project ? document.querySelector('#status').textContent.startsWith('✓ 已開啟專案') :
              document.querySelector('#status').textContent==='✓ 已載入 '+arg.filename)'''
        page.wait_for_function(predicate, arg={'draw': draw, 'project': project, 'filename': path.name,
                                             'input': '#projectFile' if project else '#file'}, timeout=30000)
        page.wait_for_function("expected=>JSON.stringify([...document.querySelectorAll('.ocard[data-kind][data-id]')].map(n=>n.dataset.kind+':'+n.dataset.id).sort())===JSON.stringify(expected)", arg=expected_cards, timeout=30000)
        ready()
        return snapshot(label)

    def reject_owned(snapshot_before, label):
        if fixture_name != 'assembly':
            return
        members = snapshot_before['assembly-read']['state']['instances'][0]['members']
        assert len(members) == 3
        rows = []
        for member in members:
            refused = native('line delete timber ' + str(member['timberId']))
            assert refused.get('ok') is False and refused.get('preview', {}).get('valid') is False, refused
            reasons = [violation.get('actual', '') for violation in refused['preview']['violations']]
            assert any('I42: delete the owning assembly instance' in reason for reason in reasons), refused
            after = snapshot(label + '-member-' + str(member['memberId']))
            assert after['dump'] == snapshot_before['dump'], 'Owned refusal changed exact dump/revision'
            assert after['assembly-read'] == snapshot_before['assembly-read'], 'Owned refusal changed assembly/revision'
            assert after['objects'] == snapshot_before['objects'] and after['references'] == snapshot_before['references']
            rows.append({'member_id': member['memberId'], 'timber_id': member['timberId'], 'refusal': refused})
            cancelled = native('line cancel-preview')
            assert cancelled.get('ok') is True, cancelled
        write(case_out / (label + '-ownership.json'), rows)

    try:
        receipt['before'] = identity('before')
        fixture_files = {'grid': (args.grid_scene.resolve(), '1ee0d9b49b37b29d00921c285201d18974c842c50446e39bb5982ee465ec14e8'),
                         'assembly': (args.assembly_scene.resolve(), 'd96abc77b028e805b5cb68b4ba648cc60ac89f46320c1143f1cc911d8168c54f')}
        selected = ('grid', 'assembly') if args.only == 'all' else (args.only,)
        for name in selected:
            source, expected_hash = fixture_files[name]
            assert source.is_file() and sha(source) == expected_hash, 'Synthetic fixture missing/changed: ' + str(source)
            (out / (name + '-fixture.scene')).write_bytes(source.read_bytes())
        receipt['fixtures'] = {name: {'source': str(fixture_files[name][0]), 'sha256': fixture_files[name][1],
                                     'setup': 'apiRequest loadfile of verified synthetic scene, then awaited renderObjects'} for name in selected}
        write(out / 'receipt.json', receipt)
        from playwright.sync_api import sync_playwright
        phase = 'browser-launch'
        with sync_playwright() as driver:
            try:
                # No --no-sandbox or policy workarounds. If launch is rejected, record
                # the actual error and terminate this browser action without retry.
                browser = driver.chromium.launch(executable_path=args.chrome, headless=True, chromium_sandbox=True)
                receipt['browser_version'] = browser.version
                for width in args.width or (1400, 390):
                    for fixture_name in selected:
                        case_out = out / (fixture_name + '-' + str(width))
                        case_out.mkdir()
                        row = {'fixture': fixture_name, 'width': width, 'started': stamp(), 'passed': False}
                        receipt['cases'].append(row)
                        errors, network_errors, cleanup_errors = [], [], []
                        context = browser.new_context(viewport={'width': width, 'height': 1000 if width == 1400 else 844}, accept_downloads=True)
                        context.add_init_script("window.__originalSavePicker=typeof window.showSaveFilePicker;Object.defineProperty(window,'showSaveFilePicker',{configurable:true,writable:true,value:undefined});")
                        context.tracing.start(screenshots=True, snapshots=True, sources=True)
                        page = context.new_page()
                        page.on('pageerror', lambda error: errors.append(str(error)))

                        def dialog_handler(dialog):
                            allowed = dialog.type == 'confirm' and (
                                dialog.message.startswith('建立一份空白新專案，切換為新的專案識別及「未命名專案」。') or
                                dialog.message == '目前專案有尚未保存的變更。要離開目前專案嗎？')
                            with (case_out / 'dialogs.jsonl').open('a', encoding='utf-8') as stream:
                                stream.write(json.dumps({'time': stamp(), 'type': dialog.type, 'message': dialog.message,
                                                         'action': 'accept-known-confirm' if allowed else 'dismiss-unexpected'}, ensure_ascii=False) + '\n')
                            if allowed:
                                dialog.accept()
                            else:
                                errors.append('Unexpected browser dialog: ' + dialog.type + ': ' + dialog.message)
                                dialog.dismiss()

                        def capture_request(request):
                            if urlsplit(request.url).path not in ('/api', '/upload', '/upload/prepare', '/upload/confirm', '/upload/cancel', '/runtime'):
                                return
                            try:
                                response = request.response()
                                data = {'time': stamp(), 'phase': phase, 'url': request.url, 'method': request.method,
                                        'request_body': request.post_data, 'http_status': response.status,
                                        'response_headers': response.all_headers(), 'response_body': response.body().decode('utf-8')}
                                with (case_out / 'http-raw.jsonl').open('a', encoding='utf-8') as stream:
                                    stream.write(json.dumps(data, ensure_ascii=False) + '\n')
                            except Exception:
                                network_errors.append(traceback.format_exc())

                        page.on('dialog', dialog_handler)
                        page.on('requestfinished', capture_request)
                        try:
                            phase = fixture_name + '-entry'
                            entry = page.goto(args.url, wait_until='domcontentloaded', timeout=30000)
                            assert entry.status == 200
                            ready()
                            assert page.evaluate('oc.on===true'), 'Probe expects the actual object canvas'
                            row['save_picker'] = page.evaluate("({original:window.__originalSavePicker,selected:typeof window.showSaveFilePicker,mode:'explicit product download fallback'})")
                            empty = new_project('initial-empty')
                            phase = fixture_name + '-api-fixture'
                            seeded = native('loadfile ' + str((out / (fixture_name + '-fixture.scene')).resolve()))
                            assert seeded.get('ok') is True, seeded
                            rendered = page.evaluate('async()=>await renderObjects()')
                            assert rendered is True
                            ready()
                            baseline = snapshot('fixture-ready')
                            assert baseline['dump']['text'] and baseline['dump']['text'] != empty['dump']['text']
                            if fixture_name == 'grid':
                                assert 'at-line rule 10 0 1 -2 1 v 0' in baseline['dump']['text']
                                timber = next(t for t in baseline['references']['timbers'] if t['id'] == 10)
                                assert timber['geometry']['centerline'] == 500 and timber['geometry']['length'] == 540, timber
                            else:
                                assert len(baseline['assembly-read']['state']['instances'][0]['members']) == 3

                            phase = fixture_name + '-ui-scene-export'
                            with page.expect_download(timeout=30000) as downloading:
                                menu('#btnExport')
                            download = downloading.value
                            scene_path = case_out / 'ui-export.scene'
                            download.save_as(scene_path)
                            assert download.failure() is None
                            page.wait_for_function("document.querySelector('#status').textContent==='✓ 已匯出 canvas_export.scene'", timeout=30000)
                            assert scene_path.read_text() == baseline['dump']['text'], 'UI scene export differs from complete World'
                            phase = fixture_name + '-scene-clear'
                            cleared = new_project('before-scene-open-empty')
                            assert world_semantic(cleared) == world_semantic(empty), 'Scene reopen predecessor is not the initial empty World'
                            phase = fixture_name + '-ui-scene-open'
                            reopened = open_file(scene_path, False, 'scene-reopened', baseline['canvas_cards'])
                            assert world_semantic(reopened) == world_semantic(baseline), 'UI scene reopen lost full native data/references'
                            reject_owned(reopened, 'scene-reopened')
                            page.screenshot(path=str(case_out / 'scene-reopened.png'), full_page=True)

                            phase = fixture_name + '-ui-project-save'
                            before_save = snapshot('before-project-save')
                            with page.expect_download(timeout=30000) as downloading:
                                menu('#btnSaveProject')
                            download = downloading.value
                            project_path = case_out / 'ui-save.gcanvas'
                            download.save_as(project_path)
                            assert download.failure() is None
                            page.wait_for_function("!ReferenceWorkspace.busy&&ReferenceWorkspace.context().downloaded===true&&document.querySelector('#status').textContent.startsWith('已產生專案下載')", timeout=30000)
                            saved = snapshot('project-saved')
                            assert world_semantic(saved) == world_semantic(before_save)
                            with zipfile.ZipFile(project_path) as package:
                                manifest = json.loads(package.read('manifest.json'))
                                packaged_scene = package.read('world.scene').decode('utf-8')
                            write(case_out / 'archive-manifest.json', manifest)
                            assert packaged_scene == saved['dump']['text'], 'Real ZIP world differs from saved native World'
                            assert manifest['projectId'] == saved['project']['id'] and manifest['name'] == saved['project']['name']
                            expected_caps = {'grid-subdivision-rules/1'} if fixture_name == 'grid' else {'assembly-rule-authoring/1', 'assembly-timber-generation/1'}
                            assert expected_caps.issubset(saved['dump']['required_capabilities']), 'Fixture lost its independently required capabilities'
                            assert set(saved['dump']['required_capabilities']).issubset(manifest['requiredCapabilities']), 'Archive omitted required native capabilities'
                            phase = fixture_name + '-project-clear'
                            cleared = new_project('before-project-open-empty')
                            assert world_semantic(cleared) == world_semantic(empty), 'Project reopen predecessor is not empty'
                            assert cleared['project']['id'] != saved['project']['id'], 'New did not change project identity'
                            phase = fixture_name + '-ui-project-open'
                            reopened = open_file(project_path, True, 'project-reopened', saved['canvas_cards'])
                            assert world_semantic(reopened) == world_semantic(saved), 'UI project reopen lost native closure'
                            assert project_semantic(reopened) == project_semantic(saved), 'UI project reopen lost identity/manifest/source bytes'
                            reject_owned(reopened, 'project-reopened')
                            page.screenshot(path=str(case_out / 'project-reopened.png'), full_page=True)
                            assert errors == [], errors
                            assert network_errors == [], network_errors
                            row.update(passed=True, scene_sha256=sha(scene_path), project_sha256=sha(project_path))
                        except BaseException:
                            row.update(error=traceback.format_exc(), failed_phase=phase)
                            try:
                                snapshot('failed-state')
                                page.screenshot(path=str(case_out / 'failed.png'), full_page=True)
                            except Exception:
                                row['failure_capture_error'] = traceback.format_exc()
                            raise
                        finally:
                            active_error = sys.exc_info()[0] is not None
                            try:
                                context.tracing.stop(path=str(case_out / 'trace.zip'))
                            except BaseException:
                                cleanup_errors.append(traceback.format_exc())
                            try:
                                context.close()
                            except BaseException:
                                cleanup_errors.append(traceback.format_exc())
                            if cleanup_errors or errors or network_errors:
                                row['passed'] = False
                            row.update(finished=stamp(), page_errors=errors, network_capture_errors=network_errors,
                                       cleanup_errors=cleanup_errors)
                            write(case_out / 'result.json', row)
                            context = page = None
                            write(out / 'receipt.json', receipt)
                            if (cleanup_errors or errors or network_errors) and not active_error:
                                raise RuntimeError('Browser case evidence or cleanup failed; see preserved case errors')
            finally:
                active_error = sys.exc_info()[0] is not None
                if browser is not None:
                    try:
                        browser.close()
                    except BaseException:
                        receipt.setdefault('browser_cleanup_errors', []).append(traceback.format_exc())
                        receipt['exit_code'] = 1
                        if not active_error:
                            raise RuntimeError('Owned browser cleanup failed; see browser_cleanup_errors')
                    finally:
                        browser = None
        receipt['after'] = identity('after')
        assert {key: receipt['after'][key] for key in ('head', 'tree', 'status', 'dirty_diff_sha256', 'sources')} == {key: receipt['before'][key] for key in ('head', 'tree', 'status', 'dirty_diff_sha256', 'sources')}
        for key in ('version', 'pid', 'session'):
            assert receipt['after']['runtime'][key] == receipt['before']['runtime'][key], 'Runtime identity changed: ' + key
        receipt['exit_code'] = 0
    except BaseException:
        receipt.update(error=traceback.format_exc(), failed_phase=phase, exit_code=1)
        # Browser policy rejection is terminal for this action; never retry with
        # relaxed flags, another sandbox setting, or a public tunnel.
    finally:
        receipt['finished'] = stamp()
        write(out / 'receipt.json', receipt)
    print(json.dumps({'out': str(out), 'exit_code': receipt['exit_code'],
                      'cases': [{'fixture': row['fixture'], 'width': row['width'], 'passed': row['passed']} for row in receipt['cases']]}))
    return receipt['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
