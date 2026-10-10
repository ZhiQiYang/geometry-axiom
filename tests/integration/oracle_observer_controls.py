"""Bounded A/B/C controls for the two release-candidate browser observers.

Run on an explicitly owned isolated native service; no product files are changed.
The controls extract the observers/stubs from the current harnesses, replace one
in-memory object/flag at a time, then restore the exact original. Their expected
old misses and new catches are deliberate oracle faults, not product defects.
Full legal flows remain the separate 35/33-assertion browser gates.
"""
import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import traceback
from urllib.parse import urlparse
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

BASE = 'bc1f6fea2f1d10b29d1e6db1917b2781377d8864'
EXPECTED = ['fixture', 'A-top-undo', 'A-saved', 'A-downloaded', 'A-dirty',
            'C-top-undo', 'C-top-redo', 'C-group', 'C-owner-fields', 'C-blocked-transient',
            'B-inactive-cancel', 'B-active-cancel', 'A-legal-cancel',
            'B-active-write-error', 'A-legal-write-error', 'source-runtime-stable']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--url', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    address = urlparse(args.url)
    assert address.scheme == 'http' and address.hostname == '127.0.0.1'
    assert address.port not in (None, 8765) and address.path in ('', '/')
    assert not out.is_relative_to(root) and not out.exists()
    out.mkdir(parents=True)
    url = args.url.rstrip('/') + '/'
    model_path = 'tests/integration/model_library_history_browser.py'
    save_path = 'tests/integration/save_roundtrip_acceptance.cjs'
    model_source = (root / model_path).read_text()
    save_source = (root / save_path).read_text()

    def git(*parts):
        return subprocess.check_output(['git', '-C', str(root), *parts], text=True).strip()

    old_model = git('show', BASE + ':' + model_path)
    old_save = git('show', BASE + ':' + save_path)

    def function(source, name):
        node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)
        namespace = {}
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<extracted-' + name + '>', 'exec'), namespace)
        return namespace[name]

    old_durable, new_durable = function(old_model, 'durable'), function(model_source, 'durable')
    state_body = next(n for n in ast.parse(model_source).body if isinstance(n, ast.FunctionDef) and n.name == 'state').body[-1].value.args[1].value
    project_expr = re.search(r'async function snap\(\).*?project:await read\(`(.*?)`\)', save_source, re.S).group(1)
    old_semantic = re.search(r'function semantic\(s\)\{.*?\n', old_save).group(0).strip()
    cancel_stub = re.search(r'await read\(`(window\.__cancelCalled=.*?;void 0)`\)', save_source).group(1)
    write_stub = re.search(r'await read\(`(window\.__saveAborted=.*?;void 0)`\)', save_source).group(1)
    assert 'navigator.userActivation.isActive' in cancel_stub and 'navigator.userActivation.isActive' in write_stub
    checks, errors = [], []

    def write(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

    def identity():
        runtime = json.load(urlopen(url + 'runtime'))
        assert runtime['fresh'] and Path(runtime['root']).resolve() == root
        return {'head': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'),
                'status': git('status', '--porcelain'), 'runtime': runtime,
                'harnesses': {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in (model_path, save_path)}}

    before = identity()
    receipt = {'schema': 'geometry-bounded-oracle-controls/1', 'baseline': BASE,
               'command': [sys.executable, *sys.argv], 'startedAt': datetime.now(timezone.utc).isoformat(),
               'before': before, 'expected': EXPECTED, 'harnessSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'limits': ['Deliberate in-memory oracle faults, not product bugs.',
                          'Opaque owner covers current context/frame/top Undo/top Redo/group, not full history.',
                          'Actual transient activation with injected picker responses; no OS picker certification.',
                          'Browser plugin not available; installed Python Playwright and Chromium.']}
    write('run.json', receipt)

    def check(name, passed, detail):
        checks.append({'name': name, 'pass': bool(passed), 'detail': detail})
        write('checks.partial.json', checks)
        print(('PASS ' if passed else 'FAIL ') + name, flush=True)
        assert passed, name

    page = None
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1382, 'height': 804})
            page.on('dialog', lambda dialog: dialog.accept())
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            page.wait_for_function("connection.phase==='ready'&&!ReferenceWorkspace.busy")

            def js(code):
                # Fixture/observation helper; the activation-negative path below
                # uses explicit CDP userGesture:false with no intervening reads.
                return page.evaluate('async()=>{' + code + '}')

            def idle():
                page.wait_for_function('!ReferenceWorkspace.busy&&!oc.busy')

            def model_state():
                return js(state_body)

            def save_state():
                project = page.evaluate(project_expr)
                return {'world': model_state()['world'], 'project': project}

            def semantic(snapshot):
                return page.evaluate('(s)=>{' + old_semantic + ';return semantic(s)}', snapshot)

            js('await ReferenceWorkspace.newProject();SpaceModelWorkspace.openExample();')
            page.wait_for_function("SpaceModelWorkspace.snapshot().phase==='preview'")
            page.locator('#smPreview').click()
            page.wait_for_function("SpaceModelWorkspace.snapshot().phase==='preview'")
            page.locator('#smConfirmFaces').check()
            page.locator('#smCreate').click()
            page.wait_for_function('!!SpaceModelWorkspace.snapshot().createdId')
            page.locator('#smClose').click()
            for command in ('boundary 991 outline 0,0 4000,0 4000,3000 0,3000', 'spec oracle_first 17', 'spec oracle_second 23'):
                page.evaluate("async command=>{const r=await apiRequest('line '+command);if(!r.ok)throw Error(JSON.stringify(r));}", command)
            page.locator('#btnUndo').click()
            idle()
            initial = save_state()
            check('fixture', initial['project']['undo'] > 0 and initial['project']['redo'] > 0 and len(initial['project']['models']) == 1 and 'boundary 991' in initial['world'], initial)
            write('fixture.json', initial)
            (out / 'fixture.gcanvas').write_bytes(bytes(js('return Array.from(await ReferenceWorkspace.exportBytes());')))
            page.screenshot(path=str(out / 'fixture.png'))

            for name, mutate in [('A-top-undo', "const h=ReferenceWorkspace.history;__oracleRestore={kind:'undo',value:h.undo.at(-1)};h.undo[h.undo.length-1]={...h.undo.at(-1)};"),
                                 *[(f'A-{key}', f"const c=ReferenceWorkspace.context();__oracleRestore={{kind:'flag',key:'{key}',descriptor:Object.getOwnPropertyDescriptor(c,'{key}')}};c.{key}=!c.{key};") for key in ('saved', 'downloaded', 'dirty')]]:
                original = save_state()
                js('window.__oracleRestore=null;' + mutate)
                try:
                    changed = save_state()
                    detail = {'before': original, 'mutated': changed, 'oldMisses': semantic(original) == semantic(changed), 'newCatches': original != changed}
                    check(name, detail['oldMisses'] and detail['newCatches'], detail)
                finally:
                    js("const r=__oracleRestore;if(r.kind==='undo')ReferenceWorkspace.history.undo[ReferenceWorkspace.history.undo.length-1]=r.value;else if(r.descriptor)Object.defineProperty(ReferenceWorkspace.context(),r.key,r.descriptor);else delete ReferenceWorkspace.context()[r.key];")
                assert save_state() == original, 'exact fault restoration: ' + name

            for key in ('undo', 'redo', 'group'):
                original = model_state()
                js("const h=ReferenceWorkspace.history;window.__oracleOriginal=" + (f'h.{key}.at(-1);h.{key}[h.{key}.length-1]={{...__oracleOriginal}};' if key != 'group' else 'h.group;h.group={base:h.snapshot(),dirty:false};'))
                try:
                    changed = model_state()
                    detail = {'before': original, 'mutated': changed, 'oldMisses': old_durable(original) == old_durable(changed), 'newCatches': new_durable(original) != new_durable(changed)}
                    check('C-top-' + key if key != 'group' else 'C-group', detail['oldMisses'] and detail['newCatches'], detail)
                finally:
                    js(f'ReferenceWorkspace.history.{key}' + (f'[ReferenceWorkspace.history.{key}.length-1]' if key != 'group' else '') + '=__oracleOriginal;')
                assert new_durable(model_state()) == new_durable(original), 'exact owner fault restoration: ' + key

            original = model_state()
            sensitivities = {}
            for key in ('context', 'frame', 'undo', 'redo', 'group'):
                changed = copy.deepcopy(original)
                changed['operation'][key] = 'synthetic-observation-only-' + key
                sensitivities[key] = {'oldMisses': old_durable(original) == old_durable(changed), 'newCatches': new_durable(original) != new_durable(changed)}
            check('C-owner-fields', all(v['oldMisses'] and v['newCatches'] for v in sensitivities.values()), {'kind': 'pure observation mutation, not browser object mutation', 'fields': sensitivities})
            changed = copy.deepcopy(original)
            changed['operation']['blocked'] = not original['operation']['blocked']
            check('C-blocked-transient', new_durable(changed) == new_durable(original), {'kind': 'pure observation transient control', 'before': original['operation'], 'after': changed['operation']})

            js(cancel_stub)
            inactive_before = save_state()
            page.wait_for_function('navigator.userActivation.isActive===false', timeout=15000)
            # Explicit CDP false prevents test transport from fabricating activation.
            cdp = page.context.new_cdp_session(page)
            response = cdp.send('Runtime.evaluate', {'expression': 'ReferenceWorkspace.save()', 'awaitPromise': True, 'returnByValue': True, 'userGesture': False})
            assert 'exceptionDetails' not in response, response
            inactive = js('return {called:__cancelCalled,active:__cancelActivation};')
            check('B-inactive-cancel', inactive['called'] and not inactive['active'] and save_state() == inactive_before, {'callback': inactive, 'oldCalledOnlyPasses': inactive['called'], 'newActivationRejects': not inactive['active'], 'CDP': response})
            js(cancel_stub)
            legal_before = save_state()
            page.locator('#projectBar [data-project-action="save"]').click()
            idle()
            activation = js('return {called:__cancelCalled,active:__cancelActivation};')
            check('B-active-cancel', activation['called'] and activation['active'], activation)
            legal_after = save_state()
            check('A-legal-cancel', legal_after == legal_before, {'before': legal_before, 'after': legal_after})
            js(write_stub)
            legal_before = save_state()
            page.locator('#projectBar [data-project-action="save"]').click()
            idle()
            activation = js('return {active:__writeActivation,aborted:__saveAborted};')
            check('B-active-write-error', activation['active'] and activation['aborted'], activation)
            legal_after = save_state()
            check('A-legal-write-error', legal_after == legal_before, {'before': legal_before, 'after': legal_after})
            js('window.showSaveFilePicker=undefined;')
            page.screenshot(path=str(out / 'completed.png'))
            after = identity()
            check('source-runtime-stable', before == after and not errors, {'before': before, 'after': after, 'pageErrors': errors})
            browser.close()
    except Exception:
        receipt['error'] = traceback.format_exc()
        print(receipt['error'], file=sys.stderr)
    finally:
        receipt.update(finishedAt=datetime.now(timezone.utc).isoformat(), checks=checks,
                       passed=sum(c['pass'] for c in checks), failed=sum(not c['pass'] for c in checks),
                       completed=[c['name'] for c in checks] == EXPECTED)
        receipt['ok'] = receipt['completed'] and not receipt['failed'] and 'error' not in receipt
        receipt['exit'] = 0 if receipt['ok'] else 1
        write('result.json', receipt)
        print('ORACLE_CONTROLS_RESULT ' + json.dumps({k: receipt[k] for k in ('passed', 'failed', 'completed', 'ok', 'exit')}))
    return receipt['exit']


if __name__ == '__main__':
    sys.exit(main())
