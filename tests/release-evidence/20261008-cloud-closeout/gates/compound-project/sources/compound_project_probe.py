#!/usr/bin/env python3
"""Bounded private compound-project Save/New/fresh-browser/Open acceptance.

Preparation only: --help. Execute only after the sole browser owner yields its slot.
API fixture setup combines a pinned synthetic assembly World, one real historical
model record (revalidated by current model endpoints), and one typed unpublished
assembly rule draft. This is not a UI authoring or cross-project merge test.
Save, New, scene Export, and both Open paths use normal clicks/file choosers.
The browser sandbox is explicitly enabled. There is no service restart claim.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import traceback
from urllib.parse import urlsplit
import zipfile

sys.dont_write_bytecode = True
ASSEMBLY_SHA = 'd96abc77b028e805b5cb68b4ba648cc60ac89f46320c1143f1cc911d8168c54f'
MODEL_ARCHIVE = 'tests/release-evidence/20261008-phase3-formal/projects/model-save.gcanvas'
MODEL_SHA = '49e05ad13914e62de974072abf7e904018e13c91052d7718404aa53b13b11edb'
DRAFT = {'id': 'compound-unpublished-rule', 'kind': 'rule', 'base_ref': None,
         'data': {'id': 99, 'version': 1, 'name': 'Compound unpublished rule',
                  'slots': [], 'members': [], 'joints': []},
         'updated_at': '2026-10-08T00:00:00.000Z'}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def world(value):
    # Revision is a transaction counter, not a serialized World field.
    # Full unmodified responses remain in every snapshot beside this comparison.
    return {name: ({k: v for k, v in value[name].items() if k != 'revision'}
                   if name in ('dump', 'assembly-read') else value[name])
            for name in ('dump', 'objects', 'references', 'assembly-read')}


def project(value):
    return {k: value['project'][k] for k in
            ('id', 'name', 'manifest', 'sources', 'models', 'assemblyDrafts', 'engineeringDrafts')}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('/workspace/geometry-axiom'))
    p.add_argument('--url', required=True)
    p.add_argument('--head', required=True, help='Exact reviewed clean 40-character SHA')
    p.add_argument('--out', required=True, type=Path, help='Fresh directory outside checkout')
    p.add_argument('--chrome', default='/usr/bin/chromium')
    p.add_argument('--bridge', type=Path, default=Path('/tmp/geometry-tests/bridge'))
    p.add_argument('--model-base', type=Path, default=Path('/tmp/geometry-tests/model-base'))
    p.add_argument('--assembly-scene', type=Path,
                   default=Path('/workspace/closure-evidence/contracts/assembly-final/reopened-owned.scene'))
    p.add_argument('--width', type=int, choices=(1400, 390), action='append',
                   help='Default both widths; repeated values are rejected')
    a = p.parse_args()
    root, out = a.root.resolve(), a.out.resolve()
    address = urlsplit(a.url)
    if (address.scheme != 'http' or address.hostname not in ('127.0.0.1', 'localhost')
            or address.port in (None, 8765) or address.path != '/'
            or any((address.query, address.fragment, address.username, address.password))):
        p.error('--url must be explicit isolated loopback HTTP, trailing /, not port 8765')
    if not re.fullmatch('[0-9a-f]{40}', a.head):
        p.error('--head must be a full lowercase SHA')
    widths = a.width or [1400, 390]
    if len(widths) != len(set(widths)):
        p.error('duplicate width')
    if out == root or out.is_relative_to(root) or out == Path('/'):
        p.error('output must be outside the checkout')
    out.mkdir(parents=True, exist_ok=False)
    receipt = {'schema': 'geometry-compound-project-reopen/1', 'started': now(),
               'argv': [sys.executable, *sys.argv], 'cwd': str(Path.cwd()),
               'scriptSha256': sha(__file__), 'expectedHead': a.head, 'python': sys.version,
               'sandbox': True, 'cases': [], 'exitCode': 1,
               'limits': ['API fixture seeding; no UI authoring or cross-project merge claim',
                          'Current model endpoint verification; historical model record used only as fixture',
                          'New Chromium process/profile per reopen; HTTP/native service is intentionally unchanged',
                          'Explicit download fallback and automated real chooser; no OS save picker/IME/physical-device claim',
                          'Successful import revision counters may advance; all other World fields are compared',
                          'Scene-only import follows New and does not assert a nonempty-project merge policy']}
    browser = context = page = None
    phase = 'preflight'
    case_out = out
    row = None
    errors, network_errors = [], []
    launch_index = 0

    def identity(label):
        commands = []
        for command in (['pwd'], ['git', 'rev-parse', 'HEAD'], ['git', 'rev-parse', 'HEAD^{tree}'],
                        ['git', 'rev-parse', 'origin/main'],
                        ['git', 'status', '--porcelain=v1', '--untracked-files=all'],
                        ['git', 'diff', '--binary', 'HEAD']):
            r = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=20)
            commands.append({'command': command, 'stdout': r.stdout, 'stderr': r.stderr, 'exitCode': r.returncode})
        write(out / (label + '-commands.json'), commands)
        assert all(r['exitCode'] == 0 for r in commands), commands
        assert commands[1]['stdout'].strip() == a.head and commands[4]['stdout'] == '', commands
        env = dict(os.environ, GEOMETRY_TEST_BRIDGE=str(a.bridge.resolve()),
                   GEOMETRY_BRIDGE=str(a.bridge.resolve()), GEOMETRY_MODEL_BASE=str(a.model_base.resolve()))
        snap = release.snapshot(root, a.url, env)
        write(out / (label + '-identity.json'), snap)
        assert not snap['problems'], snap['problems']
        assert snap['git']['head'] == a.head
        # Unlike /runtime alone, this binds the service's live native child to
        # the receipt-backed executable. It never signals or starts a process.
        ps = subprocess.run(['ps', '-eo', 'pid=,ppid='], capture_output=True, text=True, timeout=20)
        write(out / (label + '-processes.json'), {'command': ps.args, 'stdout': ps.stdout,
              'stderr': ps.stderr, 'exitCode': ps.returncode})
        assert ps.returncode == 0
        parents = [tuple(map(int, line.split())) for line in ps.stdout.splitlines() if line.strip()]
        descendants, pending = [], [snap['runtime']['pid']]
        while pending:
            parent = pending.pop()
            for pid, ppid in parents:
                if ppid != parent:
                    continue
                pending.append(pid)
                executable = Path('/proc', str(pid), 'exe')
                if executable.resolve() == a.bridge.resolve():
                    descendants.append({'pid': pid, 'executable': str(executable.resolve()),
                                        'runningSha256': sha(executable)})
        write(out / (label + '-live-bridge.json'), descendants)
        assert len(descendants) == 1 and descendants[0]['runningSha256'] == sha(a.bridge), descendants
        return snap

    def ready():
        page.wait_for_function("connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy&&pendingApiResults.size===0", timeout=30000)

    def native(command):
        r = page.evaluate('async command=>await apiRequest(command)', command)
        with (case_out / 'explicit-native.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps({'at': now(), 'phase': phase, 'command': command, 'result': r}, ensure_ascii=False) + '\n')
        return r

    def snap(label):
        value = {name: native(name) for name in ('dump', 'objects', 'references', 'assembly-read')}
        assert all(v.get('ok') is True for v in value.values()), value
        value['project'] = page.evaluate('''async()=>{const c=ReferenceWorkspace.context();return {
            id:c.id,name:c.name,manifest:await ReferenceWorkspace.manifest(),
            sources:[...c.sources].map(([id,v])=>[id,Array.from(v.bytes)]),
            models:ReferenceWorkspace.getSpaceModels(),assemblyDrafts:ReferenceWorkspace.getAssemblyDrafts(),
            engineeringDrafts:ReferenceWorkspace.getEngineeringDrafts(),dirty:c.dirty,saved:c.saved,downloaded:c.downloaded};}''')
        value['canvasCards'] = page.locator('.ocard[data-kind][data-id]').evaluate_all("nodes=>nodes.map(n=>n.dataset.kind+':'+n.dataset.id).sort()")
        write(case_out / (label + '.json'), value)
        (case_out / (label + '.scene')).write_text(value['dump']['text'], encoding='utf-8')
        return value

    def check(name, condition):
        item = {'name': name, 'passed': condition is True, 'at': now()}
        row['checks'].append(item)
        write(case_out / 'result.json', row)
        print(('PASS ' if item['passed'] else 'FAIL ') + name, flush=True)
        assert item['passed'], name

    def menu(selector):
        page.locator('#fileMenuBtn').click(timeout=10000)
        page.locator(selector).click(timeout=10000)

    def matching(response, endpoint):
        return response.request.method == 'POST' and urlsplit(response.url).path == endpoint

    def empty_assert(value):
        assert value['dump']['text'] == '' and value['canvasCards'] == [], value
        assert all(not value['objects'][k] for k in ('faces', 'spaces', 'columns', 'beams', 'gridSystems',
                   'parameters', 'assemblyRules', 'assemblyBindings', 'gridBindings', 'timbers')), value['objects']
        assert all(value['assembly-read']['state'][k] == [] for k in ('rules', 'bindings', 'instances'))
        assert all(value['project'][k] == [] for k in ('models', 'assemblyDrafts', 'engineeringDrafts', 'sources'))
        manifest = value['project']['manifest']
        assert all(manifest.get(k, []) == [] for k in ('models', 'sources', 'faces', 'faceProjections'))
        assert all(manifest.get(k, {}).get('records', []) == [] for k in
                   ('assemblyDrafts', 'engineeringDrafts', 'featureAttachments'))

    def new_project(label):
        old_id, draw = page.evaluate('[ReferenceWorkspace.context().id,ocDrawCount]')
        with page.expect_response(lambda r: matching(r, '/upload') and r.request.post_data == 'reset\n', timeout=30000) as response:
            menu('#btnNewProject')
        assert response.value.status == 200 and response.value.json().get('ok') is True
        page.wait_for_function('''v=>ReferenceWorkspace.context().id!==v.id&&ocDrawCount>v.draw&&
            document.querySelector('#status').textContent.startsWith('✓ 已建立空白新專案')&&
            !ReferenceWorkspace.busy&&!oc.busy''', arg={'id': old_id, 'draw': draw}, timeout=30000)
        ready()
        value = snap(label)
        empty_assert(value)
        return value

    def open_file(path, is_project, label, cards):
        draw = page.evaluate('ocDrawCount')
        endpoint = '/upload/confirm' if is_project else '/upload'
        with page.expect_response(lambda r: matching(r, endpoint), timeout=60000) as response:
            with page.expect_file_chooser(timeout=10000) as chooser:
                menu('#btnOpenProject' if is_project else '#btnOpen')
            selected = chooser.value
            assert selected.element.get_attribute('id') == ('projectFile' if is_project else 'file')
            selected.set_files(str(path))
        assert response.value.status == 200 and response.value.json().get('ok') is True, response.value.text()
        page.wait_for_function('''v=>ocDrawCount>v.draw&&!ReferenceWorkspace.busy&&!oc.busy&&
            document.querySelector(v.input).value===''&&(v.project?
            document.querySelector('#status').textContent.startsWith('✓ 已開啟專案'):
            document.querySelector('#status').textContent==='✓ 已載入 '+v.filename)''',
            arg={'draw': draw, 'project': is_project, 'input': '#projectFile' if is_project else '#file', 'filename': path.name}, timeout=60000)
        page.wait_for_function("expected=>JSON.stringify([...document.querySelectorAll('.ocard[data-kind][data-id]')].map(n=>n.dataset.kind+':'+n.dataset.id).sort())===JSON.stringify(expected)", arg=cards, timeout=30000)
        ready()
        return snap(label)

    def close_browser():
        nonlocal browser, context, page
        active_error = sys.exc_info()[0] is not None
        cleanup = []
        if context is not None:
            try:
                context.tracing.stop(path=str(case_out / ('trace-' + str(launch_index) + '.zip')))
            except BaseException:
                cleanup.append(traceback.format_exc())
            try:
                context.close()
            except BaseException:
                cleanup.append(traceback.format_exc())
        if browser is not None:
            try:
                browser.close()
            except BaseException:
                cleanup.append(traceback.format_exc())
        browser = context = page = None
        if cleanup:
            receipt.setdefault('cleanupErrors', []).extend(cleanup)
            if not active_error:
                raise RuntimeError('Owned browser cleanup failed; see receipt')

    def launch(driver, width):
        nonlocal browser, context, page, launch_index
        launch_index += 1
        browser = driver.chromium.launch(executable_path=a.chrome, headless=True, chromium_sandbox=True)
        context = browser.new_context(viewport={'width': width, 'height': 1000 if width == 1400 else 844}, accept_downloads=True)
        context.add_init_script("window.__compoundOriginalPicker=typeof window.showSaveFilePicker;Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true,writable:true});")
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        page.set_default_timeout(30000)
        page.on('pageerror', lambda error: errors.append(str(error)))

        def dialog(dialog):
            allow = dialog.type == 'confirm' and (dialog.message.startswith('建立一份空白新專案，切換為新的專案識別及「未命名專案」。')
                     or dialog.message == '目前專案有尚未保存的變更。要離開目前專案嗎？')
            with (case_out / 'dialogs.jsonl').open('a', encoding='utf-8') as f:
                f.write(json.dumps({'at': now(), 'type': dialog.type, 'message': dialog.message, 'accepted': allow}, ensure_ascii=False) + '\n')
            if allow:
                dialog.accept()
            else:
                errors.append('Unexpected dialog: ' + dialog.message)
                dialog.dismiss()

        def network(request):
            path = urlsplit(request.url).path
            if path not in ('/api', '/runtime', '/upload', '/upload/prepare', '/upload/confirm', '/upload/cancel', '/model/verify', '/model/space-replay'):
                return
            try:
                response = request.response()
                data = {'at': now(), 'phase': phase, 'url': request.url, 'method': request.method,
                        'requestBody': request.post_data, 'status': response.status,
                        'headers': response.all_headers(), 'responseBody': response.body().decode('utf-8')}
                with (case_out / 'http-raw.jsonl').open('a', encoding='utf-8') as f:
                    f.write(json.dumps(data, ensure_ascii=False) + '\n')
            except (KeyboardInterrupt, InterruptedError):
                raise
            except Exception:
                network_errors.append(traceback.format_exc())

        page.on('dialog', dialog)
        page.on('requestfinished', network)
        response = page.goto(a.url, wait_until='domcontentloaded', timeout=30000)
        assert response.status == 200
        ready()
        assert page.title() == '構形 Canvas · 工程規格與空間建模' and page.evaluate('oc.on===true')
        receipt.setdefault('launches', []).append({'index': launch_index, 'version': browser.version,
             'width': width, 'sandbox': True, 'requestedArguments': [],
             'profile': 'new Playwright-owned browser process and temporary profile',
             'savePicker': page.evaluate("({original:window.__compoundOriginalPicker,selected:typeof window.showSaveFilePicker})")})

    try:
        spec = importlib.util.spec_from_file_location('compound_release_gate', root / 'tests/release_gate.py')
        release = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(release)
        receipt['playwright'] = importlib.metadata.version('playwright')
        receipt['before'] = identity('before')
        assembly_path = a.assembly_scene.resolve()
        model_path = root / MODEL_ARCHIVE
        assert sha(assembly_path) == ASSEMBLY_SHA and sha(model_path) == MODEL_SHA, 'Pinned fixture missing or changed'
        (out / 'assembly-fixture.scene').write_bytes(assembly_path.read_bytes())
        with zipfile.ZipFile(model_path) as package:
            archived = json.loads(package.read('manifest.json'))
        assert len(archived['models']) == 1
        model = archived['models'][0]
        # Independent fixture facts, not values learned from the new runtime.
        assert model['input']['settings']['height'] == 3000
        assert model['input']['settings']['bottom'] == 0
        assert model['result']['summary']['volume_mm3'] == '36000000000'
        assert model['result']['summary']['wall_volume_mm3'] == '4320000000'
        assert model['source']['scene_hash'] == hashlib.sha256(model['input']['base_scene'].encode()).hexdigest()
        write(out / 'model-fixture.json', model)
        write(out / 'draft-fixture.json', DRAFT)
        receipt['fixtures'] = {'assembly': {'path': str(assembly_path), 'sha256': ASSEMBLY_SHA},
                               'modelArchive': {'path': str(model_path), 'sha256': MODEL_SHA},
                               'draft': {'source': 'tests/test_assembly_project_store.js rule draft shape; id99 avoids native id1', 'value': DRAFT}}
        from playwright.sync_api import sync_playwright
        with sync_playwright() as driver:
            for width in widths:
                case_out = out / str(width)
                case_out.mkdir()
                errors, network_errors = [], []
                row = {'width': width, 'started': now(), 'checks': [], 'passed': False}
                receipt['cases'].append(row)
                try:
                    phase = 'initial-entry'
                    launch(driver, width)
                    empty = new_project('initial-empty')
                    phase = 'api-fixture-seeding'
                    loaded = native('loadfile ' + str(out / 'assembly-fixture.scene'))
                    assert loaded.get('ok') is True, loaded
                    assert page.evaluate('async()=>await renderObjects()') is True
                    ready()
                    before_metadata = snap('native-fixture')
                    state = before_metadata['assembly-read']['state']
                    assert len(state['instances']) == 1 and len(state['instances'][0]['members']) == 3
                    assert not any(x['value']['id'] == 99 for x in state['rules'])
                    verified = page.evaluate('''async model=>{
                        const verified={packages:{}};
                        for(const name of ['space','volume','clearance','walls']){
                          const pkg=model.result[name];if(pkg===null){verified.packages[name]=null;continue;}
                          const response=await fetch('/model/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(pkg),signal:AbortSignal.timeout(30000)});
                          if(!response.ok)throw Error('model verify HTTP '+response.status);
                          const value=await response.json();GeometryProject.validateModelPackage(value);verified.packages[name]=value;
                        }
                        const response=await fetch('/model/space-replay',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({input:model.input,result:model.result}),signal:AbortSignal.timeout(30000)});
                        if(!response.ok)throw Error('model replay HTTP '+response.status);
                        verified.replay=await response.json();return verified;
                    }''', model)
                    write(case_out / 'current-model-verification.json', verified)
                    rebuilt = verified['replay']
                    assert rebuilt.get('ok') is True and rebuilt['schema'] == model['result']['schema']
                    assert rebuilt['source_sha256'] == model['result']['source_sha256']
                    for key in ('space', 'volume', 'clearance', 'walls'):
                        old, actual = model['result'][key], rebuilt[key]
                        assert (old is None) == (actual is None)
                        if old is not None:
                            for field in ('definitions', 'request', 'derived'):
                                assert actual[field] == old[field], (key, field)
                    assert {k: v for k, v in rebuilt['summary'].items() if k != 'wall_diagnostics'} == {k: v for k, v in model['result']['summary'].items() if k != 'wall_diagnostics'}
                    page.evaluate('''({model,draft})=>{
                        ReferenceWorkspace.addSpaceModel(model);
                        ReferenceWorkspace.setAssemblyDraft(draft,ReferenceWorkspace.getProjectState().contextToken);
                    }''', {'model': model, 'draft': DRAFT})
                    baseline = snap('compound-fixture')
                    check('API fixture contains one exact model, one unpublished rule draft and three owned members',
                          baseline['project']['models'] == [model] and baseline['project']['assemblyDrafts'] == [DRAFT]
                          and world(baseline) == world(before_metadata))
                    phase = 'formal-save'
                    with page.expect_download(timeout=60000) as downloading:
                        menu('#btnSaveProject')
                    downloaded = downloading.value
                    archive_path = case_out / 'compound.gcanvas'
                    downloaded.save_as(archive_path)
                    assert downloaded.failure() is None
                    page.wait_for_function("!ReferenceWorkspace.busy&&ReferenceWorkspace.context().downloaded===true&&document.querySelector('#status').textContent.startsWith('已產生專案下載')", timeout=30000)
                    saved = snap('saved')
                    with zipfile.ZipFile(archive_path) as package:
                        manifest = json.loads(package.read('manifest.json'))
                        archived_world = package.read('world.scene').decode('utf-8')
                    write(case_out / 'archive-manifest.json', manifest)
                    check('real downloaded ZIP retains exact model/draft/native World and both native assembly capabilities',
                          manifest['models'] == [model] and manifest['assemblyDrafts']['records'] == [DRAFT]
                          and archived_world == saved['dump']['text']
                          and {'assembly-rule-authoring/1', 'assembly-timber-generation/1'}.issubset(manifest['requiredCapabilities']))
                    check('Save preserves compound source and project payload', world(saved) == world(baseline) and project(saved) == project(baseline))
                    phase = 'clear-before-fresh-browser'
                    cleared = new_project('before-fresh-browser-empty')
                    check('trusted New clears native World, model, drafts, instances and changes project identity',
                          world(cleared) == world(empty) and cleared['project']['id'] != saved['project']['id'])
                    close_browser()
                    phase = 'fresh-browser-profile'
                    launch(driver, width)
                    fresh = snap('fresh-profile-empty')
                    empty_assert(fresh)
                    check('second browser process with fresh profile starts empty before Open',
                          world(fresh) == world(empty) and fresh['project']['id'] != saved['project']['id'])
                    phase = 'formal-project-open'
                    reopened = open_file(archive_path, True, 'project-reopened', saved['canvasCards'])
                    check('fresh-profile formal chooser restores complete World, references, instances, model and draft bytes',
                          world(reopened) == world(saved) and project(reopened) == project(saved))
                    phase = 'reopened-ownership-refusal'
                    member = reopened['assembly-read']['state']['instances'][0]['members'][0]
                    refused = native('line delete timber ' + str(member['timberId']))
                    reason = '\n'.join([str(refused.get('error') or '')] + [str(v.get('actual') or v.get('message') or '') for v in (refused.get('preview') or {}).get('violations', [])])
                    refused_after = snap('after-owned-refusal')
                    check('reopened instance ownership rejects direct member deletion with I42 and changes no full snapshot',
                          refused.get('ok') is False and 'I42: delete the owning assembly instance' in reason
                          and refused_after == reopened)
                    assert native('line cancel-preview').get('ok') is True
                    page.screenshot(path=str(case_out / 'compound-reopened.png'), full_page=True)
                    phase = 'formal-scene-export'
                    with page.expect_download(timeout=30000) as downloading:
                        menu('#btnExport')
                    scene_download = downloading.value
                    scene_path = case_out / 'compound-world.scene'
                    scene_download.save_as(scene_path)
                    assert scene_download.failure() is None
                    page.wait_for_function("document.querySelector('#status').textContent==='✓ 已匯出 canvas_export.scene'", timeout=30000)
                    check('formal scene Export contains exact native World only', scene_path.read_text() == saved['dump']['text'])
                    phase = 'clear-before-scene-open'
                    scene_empty = new_project('before-scene-open-empty')
                    check('scene Open predecessor has no residual project payload', world(scene_empty) == world(empty))
                    phase = 'formal-scene-open'
                    scene_opened = open_file(scene_path, False, 'scene-reopened', saved['canvasCards'])
                    check('scene chooser restores full native instance closure without model or unpublished project draft',
                          world(scene_opened) == world(saved) and scene_opened['project']['models'] == []
                          and scene_opened['project']['assemblyDrafts'] == [] and scene_opened['project']['engineeringDrafts'] == [])
                    page.screenshot(path=str(case_out / 'scene-only-reopened.png'), full_page=True)
                    check('no page or raw-network capture errors', errors == [] and network_errors == [])
                    row.update(passed=True, archiveSha256=sha(archive_path), sceneSha256=sha(scene_path))
                except BaseException:
                    row.update(error=traceback.format_exc(), failedPhase=phase)
                    if page is not None:
                        try:
                            snap('failed-state')
                            page.screenshot(path=str(case_out / 'failed.png'), full_page=True)
                        except BaseException:
                            row['failureCaptureError'] = traceback.format_exc()
                    raise
                finally:
                    try:
                        close_browser()
                    finally:
                        row.update(finished=now(), pageErrors=errors, networkCaptureErrors=network_errors)
                        if errors or network_errors or receipt.get('cleanupErrors'):
                            row['passed'] = False
                        write(case_out / 'result.json', row)
                        write(out / 'receipt.json', receipt)
        receipt['after'] = identity('after')
        identity_problems = release.compare_snapshots(receipt['before'], receipt['after'])
        assert not identity_problems, identity_problems
        assert all(case['passed'] for case in receipt['cases']) and len(receipt['cases']) == len(widths)
        receipt['exitCode'] = 0
    except BaseException:
        receipt.update(error=traceback.format_exc(), failedPhase=phase, exitCode=1)
    finally:
        receipt['finished'] = now()
        write(out / 'receipt.json', receipt)
    print(json.dumps({'out': str(out), 'exitCode': receipt['exitCode'],
                      'cases': [{'width': r['width'], 'passed': r['passed'], 'checks': len(r['checks'])} for r in receipt['cases']]}, ensure_ascii=False))
    return receipt['exitCode']


if __name__ == '__main__':
    def interrupted(signum, _frame):
        raise InterruptedError('received signal ' + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    raise SystemExit(main())
