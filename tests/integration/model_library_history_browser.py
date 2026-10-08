"""Bounded #159/#161 real-browser history acceptance; never historical receipts.

Run against an explicitly isolated fresh start_local.py service. Example:
  GEOMETRY_VERIFY_ROOT=$PWD GEOMETRY_TEST_URL=http://127.0.0.1:8801/ \
  GEOMETRY_MODEL_HISTORY_OUT=/tmp/geometry-model-history \
  python tests/integration/model_library_history_browser.py

Real model producer, native undo, trusted browser controls and real Web Locks.
Negative races hold delivery of a real native response. Foreign context/session
identity fault injection is explicitly identified below. The readonly tab seeds
actual producer metadata and nonempty ContextHistory fixtures because readonly
startup does not import attachments; no lease/guard/response is synthesized.
GEOMETRY_ACCEPT_DIRTY=1 is development-only and is recorded in the receipt.
"""
import hashlib
from contextlib import contextmanager
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright


ROOT = Path(os.environ['GEOMETRY_VERIFY_ROOT']).resolve()
URL = os.environ['GEOMETRY_TEST_URL'].rstrip('/') + '/'
OUT = Path(os.environ['GEOMETRY_MODEL_HISTORY_OUT']).resolve()
address = urllib.parse.urlparse(URL)
assert address.scheme == 'http' and address.hostname == '127.0.0.1'
assert address.port not in (None, 8765), 'Use an isolated test service.'
assert OUT.is_absolute() and not OUT.is_relative_to(ROOT) and OUT != Path('/')
assert not OUT.exists() or not any(OUT.iterdir()), 'Evidence output must be new or empty.'
OUT.mkdir(parents=True, exist_ok=True)


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


runtime = json.load(urllib.request.urlopen(URL + 'runtime'))
assert runtime['fresh'] and Path(runtime['root']).resolve() == ROOT
dirty = git('status', '--porcelain')
assert not dirty or os.environ.get('GEOMETRY_ACCEPT_DIRTY') == '1', dirty
checks, browser_errors, console_errors, downloads = [], [], [], []
EXPECTED_CASES = {'MH00': 1, 'MH01-1382': 6, 'MH01-390': 6, 'MH02': 3, 'MH03': 1,
                  'MH03-cross-project': 2, 'MH04-context': 1, 'MH04-session': 1, 'MH04-source': 1,
                  'MH05-zero-calibration': 1, 'MH05-face-outline': 1, 'MH05-parameter': 1, 'MH05-room': 1,
                  'MH06': 2, 'MH07': 5, 'MH08': 1, 'MH09': 1}
receipt = {
    'schema': 'geometry-model-library-history-browser/1',
    'head': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'),
    'runtime': runtime, 'gitStatus': dirty,
    'development': bool(dirty),
    'harnessSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'command': [sys.executable, *sys.argv],
    'environment': {key: os.environ.get(key) for key in ('GEOMETRY_VERIFY_ROOT', 'GEOMETRY_TEST_URL', 'GEOMETRY_MODEL_HISTORY_OUT', 'GEOMETRY_ACCEPT_DIRTY', 'GEOMETRY_CHROME')},
    'expectedCases': EXPECTED_CASES, 'expectedAssertions': sum(EXPECTED_CASES.values()),
    'limitations': [
        'New bounded acceptance only; does not recreate missing historical 10/155-case evidence.',
        'Chromium Linux; no Windows, physical phone, OS picker or IME certification.',
        'Foreign context/session cases inject transitions after native history observation but before native command completion returns to doUndoRedo; the separate nativePending cases hold real response JSON before observation.',
        'Readonly tab uses real Web Locks contention plus actual producer metadata and nonempty ContextHistory fixtures; no readonly import claim.',
        'Native commands and archive import use public APIs for fixture setup. Zero-point calibration and face-outline guard fixtures seed raw draft state; the parameter editor and room picker use actual UI entry/actions, with public-API image/calibration fixture setup.',
    ],
}


def js(page, body):
    return page.evaluate('async()=>{' + body + '}')


def check(case, label, value, detail=None):
    entry = {'case': case, 'label': label, 'pass': value is True}
    if detail is not None:
        entry['detail'] = detail
    checks.append(entry)
    print(('PASS ' if value is True else 'FAIL ') + case + ' ' + label, flush=True)
    assert value is True, case + ': ' + label


def idle(page):
    page.wait_for_function("!oc.busy&&!ReferenceWorkspace.busy&&!WorkspaceShell.historyBusy($('smWorkspace'))")


def state(page):
    # Raw read avoids observing a newer native revision while delivery is held.
    return js(page, """const response=await fetch('/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd:'dump'})});
      const dump=await response.json();if(!dump.ok)throw Error(JSON.stringify(dump));
      return {world:dump.text,models:ReferenceWorkspace.getSpaceModels(),
        context:ReferenceWorkspace.context().id,undo:ReferenceWorkspace.history.undo.length,
        redo:ReferenceWorkspace.history.redo.length,project:ReferenceWorkspace.getProjectState(),
        operation:ReferenceWorkspace.getModelOperationState(),evidence:ReferenceWorkspace.getEvidenceState()};""")


def durable(value):
    result = {key: value[key] for key in ('world', 'models', 'context', 'undo', 'redo', 'project')}
    # Existing product-owned opaque identities detect equal-length replacement
    # of the current frame/top entries. blocked is deliberately transient while
    # a response is held; successful Undo/Redo use separate transition assertions.
    result['historyOwner'] = {key: value['operation'][key]
                              for key in ('context', 'frame', 'undo', 'redo', 'group')}
    return result


def native(page, command):
    return page.evaluate("""async command=>{let r=await apiRequest('line '+command);
      if(r.preview?.valid)r=await apiRequest('line confirm '+r.preview.token);
      if(!r.ok)throw Error(JSON.stringify(r));return r;}""", command)


def open_library(page):
    js(page, 'SpaceModelWorkspace.openLibrary();')
    page.wait_for_function("$('smWorkspace').open&&!$('smLibraryPanel').hidden&&!SpaceModelWorkspace.snapshot().viewerLoading")


def restore(page):
    js(page, "SpaceModelWorkspace.close();await ReferenceWorkspace.importBytes(__mh.archive,'model-history-real-fixture.gcanvas');")
    idle(page)
    open_library(page)
    page.wait_for_function("!$('btnUndo').disabled")


def prepare_native_undo(page):
    restore(page)
    before = state(page)
    native(page, 'spec model_history_marker 314')
    # Explicit opening captures the new owner after the intentional native edit.
    open_library(page)
    page.wait_for_function("!$('btnUndo').disabled")
    return before, state(page)


def arm(page, after_observation=False):
    js(page, """const original=window.fetch;const g=window.__mhGate={held:false,released:false,commands:[],mutations:[],native:null};
      const gate=new Promise(resolve=>g.release=resolve);g.original=original;
      window.fetch=async(...args)=>{let body={};try{body=JSON.parse(args[1]?.body||'{}')}catch(_){}
        if(String(args[0])==='/api'&&body.cmd){g.commands.push(body.cmd);if(/^(line |drag |reset$|default$|loadfile |engineering-confirm |assembly-confirm )/.test(body.cmd))g.mutations.push(body.cmd);}
        const response=await original(...args);
        if(!g.afterObservation&&String(args[0])==='/api'&&body.cmd==='line undo'&&!g.held){const json=response.json.bind(response);
          response.json=async()=>{const result=await json();g.native=result;g.held=true;await gate;g.released=true;return result;};}
        return response;};""")
    if after_observation:
        js(page, """const g=__mhGate;g.afterObservation=true;g.originalApi=window.apiRequest;
          window.apiRequest=async(...args)=>{const result=await g.originalApi(...args);
            if(args[0]==='line undo'){g.native=result;g.held=true;await new Promise(resolve=>g.release=resolve);g.released=true;}return result;};""")
    page.locator('#btnUndo').click()
    page.wait_for_function('__mhGate.held')


def release(page):
    js(page, '__mhGate.release();')
    idle(page)
    page.wait_for_function('__mhGate.released')
    js(page, 'window.fetch=__mhGate.original;if(__mhGate.originalApi)window.apiRequest=__mhGate.originalApi;')


def click_disabled(page, selector):
    # Actual trusted input, including a disabled button, with no forced JS click.
    node = page.locator(selector)
    node.scroll_into_view_if_needed()
    box = node.bounding_box()
    assert box, selector
    page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)


def denied_controls(page, case, model_id):
    remove = '[data-sm-remove-model="' + model_id + '"]'
    check(case, 'Undo/Redo/remove/Save are disabled while native Undo is pending',
          all(page.locator(s).is_disabled() for s in ('#btnUndo', '#btnRedo', remove, '#projectBar [data-project-action="save"]')))
    for selector in ('#btnUndo', '#btnRedo', remove, '#projectBar [data-project-action="save"]'):
        click_disabled(page, selector)
    page.keyboard.press('Control+z')
    page.keyboard.press('Control+y')
    page.keyboard.press('Control+Shift+z')


def screenshot(page, name):
    page.screenshot(path=str(OUT / (name + '.png')), full_page=True)


def record(name, value):
    (OUT / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2))


@contextmanager
def evidence_playwright():
    driver = sync_playwright().start()
    try:
        yield driver
    except Exception:
        if page is not None:
            try:
                screenshot(page, 'failure')
                (OUT / 'failure-state.json').write_text(json.dumps(state(page), ensure_ascii=False, indent=2))
                (OUT / 'failure-ui.json').write_text(json.dumps(js(page, "return {space:SpaceModelWorkspace.snapshot(),status:$('smStatus').textContent,connection};"), ensure_ascii=False, indent=2))
            except Exception:
                pass
        raise
    finally:
        driver.stop()


page = None
try:
    with evidence_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=os.environ.get('GEOMETRY_CHROME', '/usr/bin/chromium'),
                                             headless=True, args=['--no-sandbox'])
        receipt.update(browserVersion=browser.version, platform=sys.platform,
                       browserExecutable=os.environ.get('GEOMETRY_CHROME', '/usr/bin/chromium'),
                       browserProfile='Playwright-owned isolated temporary profile; no existing user profile')
        context = browser.new_context(viewport={'width': 1382, 'height': 804}, accept_downloads=True)
        page = context.new_page()
        page.on('pageerror', lambda error: browser_errors.append(str(error)))
        page.on('console', lambda message: console_errors.append(message.text) if message.type == 'error' else None)
        page.on('dialog', lambda dialog: dialog.accept())
        page.on('download', lambda download: downloads.append(download.suggested_filename))
        page.goto(URL)
        page.wait_for_function("connection.phase==='ready'&&!ReferenceWorkspace.busy")
        js(page, 'await ReferenceWorkspace.newProject();')
        idle(page)
        js(page, 'SpaceModelWorkspace.openExample();')
        page.wait_for_function("SpaceModelWorkspace.snapshot().phase==='preview'")
        page.locator('#smModelName').fill('20261008 真實模型庫驗收')
        page.locator('#smPreview').click()
        page.wait_for_function("SpaceModelWorkspace.snapshot().phase==='preview'")
        page.locator('#smConfirmFaces').check()
        page.locator('#smCreate').click()
        page.wait_for_function('!!SpaceModelWorkspace.snapshot().createdId')
        model_id = js(page, 'return SpaceModelWorkspace.snapshot().createdId;')
        page.locator('#smClose').click()
        for command in ('boundary 1 outline 0,0 4000,0 4000,3000 0,3000 kind room_plan',
                        'placement 1 on boundary 1 origin 0 0 2500 u +x v +y',
                        'canvas-pos boundary 1 60 60'):
            native(page, command)
        js(page, 'await renderObjects();window.__mh={archive:await ReferenceWorkspace.exportBytes()};')
        fixture = state(page)
        (OUT / 'fixture-world.scene').write_text(fixture['world'])
        (OUT / 'fixture-models.json').write_text(json.dumps(fixture['models'], ensure_ascii=False, indent=2))
        (OUT / 'fixture.gcanvas').write_bytes(bytes(js(page, 'return Array.from(__mh.archive);')))
        check('MH00', 'actual preview/confirmation produces a model over a nonempty native fixture',
              len(fixture['models']) == 1 and fixture['models'][0]['id'] == model_id and
              'canvas-pos boundary 1 60 60' in fixture['world'])

        for width, height in ((1382, 804), (390, 844)):
            case = 'MH01-' + str(width)
            page.set_viewport_size({'width': width, 'height': height})
            before, marked = prepare_native_undo(page)
            check(case, 'fixture pins a distinct real native top history entry',
                  before['world'] != marked['world'] and marked['undo'] == before['undo'] + 1)
            arm(page)
            held = state(page)
            check(case, 'server Undo completed but frontend history is still pending',
                  held['world'] == before['world'] and held['undo'] == marked['undo'] and
                  held['evidence']['blocked'] and js(page, 'return __mhGate.native.ok===true;'))
            denied_controls(page, case, model_id)
            check(case, 'trusted reentry sends exactly one native Undo and creates no download',
                  js(page, "return JSON.stringify(__mhGate.mutations)===JSON.stringify(['line undo']);") and
                  durable(state(page)) == durable(held) and downloads == [])
            screenshot(page, case + '-pending')
            release(page)
            finished = state(page)
            record(case + '-states', {'before': before, 'marked': marked, 'held': held, 'finished': finished,
                                     'nativeGate': js(page, 'return {commands:__mhGate.commands,mutations:__mhGate.mutations,native:__mhGate.native};')})
            check(case, 'released Undo restores exact World/models and consumes one fixed entry',
                  finished['world'] == before['world'] and finished['models'] == before['models'] and
                  finished['undo'] == before['undo'] and finished['redo'] == marked['redo'] + 1 and
                  not page.locator('#btnRedo').is_disabled())
            page.locator('#btnRedo').click()
            idle(page)
            check(case, 'real Redo remains operable and restores exact pre-Undo native World',
                  state(page)['world'] == marked['world'])

        page.set_viewport_size({'width': 1382, 'height': 804})
        before, marked = prepare_native_undo(page)
        arm(page)
        # The existing oc-busy CSS blocks pointer buttons. Native Escape and
        # keyboard activation exercise the close/reopen lifecycle without
        # disabling the application's pointer gate.
        page.keyboard.press('Escape')
        page.wait_for_function("!$('smWorkspace').open")
        page.locator('#btnSpaceModels').focus()
        page.keyboard.press('Enter')
        page.wait_for_function("$('smWorkspace').open&&!$('smLibraryPanel').hidden")
        check('MH02', 'close/reopen is a new library owner while old delivery is held',
              page.locator('#btnUndo').is_disabled() and page.locator('#btnRedo').is_disabled())
        release(page)

        after = state(page)
        check('MH02', 'late reply cannot renew reopened owner or remove saved models',
              page.locator('#btnUndo').is_disabled() and page.locator('#btnRedo').is_disabled() and
              after['world'] == before['world'] and after['models'] == before['models'])
        screenshot(page, 'MH02-reopened-stale-owner')
        page.locator('#smClose').click()
        open_library(page)
        check('MH02', 'an explicit fresh opening after completion restores history availability',
              not page.locator('#btnRedo').is_disabled())

        before, marked = prepare_native_undo(page)
        arm(page)
        rejected = js(page, "try{await ReferenceWorkspace.importBytes(__mh.archive,'foreign.gcanvas');return null}catch(error){return error.message}")
        check('MH03', 'real project switch is refused during pending Undo with no extra mutation',
              isinstance(rejected, str) and '完成' in rejected and
              js(page, "return JSON.stringify(__mhGate.mutations)===JSON.stringify(['line undo']);") and
              state(page)['context'] == before['context'])
        release(page)

        restore(page)
        prior = state(page)
        js(page, 'SpaceModelWorkspace.close();await ReferenceWorkspace.newProject();')
        idle(page)
        empty = state(page)
        open_library(page)
        page.locator('#btnUndo').click()
        idle(page)
        restored = state(page)
        check('MH03-cross-project', 'Undo New inside library restores the pinned nonempty World/models/context in exactly one step',
              restored['world'] == prior['world'] and restored['models'] == prior['models'] and
              restored['context'] == prior['context'] and restored['undo'] == empty['undo'] - 1 and
              restored['redo'] == empty['redo'] + 1 and not page.locator('#btnRedo').is_disabled() and
              js(page, "return $('smWorkspace').open&&!$('smLibraryPanel').hidden;"))
        page.keyboard.press('Control+y')
        idle(page)
        redone = state(page)
        check('MH03-cross-project', 'retained library focus permits real Ctrl+Y back to the exact new project',
              redone['world'] == empty['world'] and redone['models'] == empty['models'] and
              redone['context'] == empty['context'] and redone['undo'] == empty['undo'] and
              redone['redo'] == empty['redo'] and not page.locator('#btnUndo').is_disabled())
        record('MH03-cross-project', {'prior': prior, 'empty': empty, 'restored': restored, 'redone': redone})

        # Deliberate identity transitions exercise stale-owner guards; these are
        # negative fault injections, not claims of reachable concurrent UI edits.
        for mode in ('context', 'session'):
            case = 'MH04-' + mode
            before, marked = prepare_native_undo(page)
            arm(page, after_observation=True)
            if mode == 'context':
                js(page, "__mh.savedFrame=ReferenceWorkspace.history.frame;ReferenceWorkspace.history.frame={context:{...ReferenceWorkspace.context(),id:crypto.randomUUID()},ids:new Map(ReferenceWorkspace.history.frame.ids)};WorkspaceShell.refresh();")
            else:
                js(page, "__mh.savedSession=connection.session;connection.session='injected-foreign-session-'+crypto.randomUUID();WorkspaceShell.refresh();")
            injected = state(page)
            release(page)
            completed = state(page)
            check(case, 'late native completion cannot renew or overwrite a foreign ' + mode + ' owner',
                  page.locator('#btnUndo').is_disabled() and page.locator('#btnRedo').is_disabled() and
                  js(page, "return JSON.stringify(__mhGate.mutations)===JSON.stringify(['line undo']);") and
                  durable(completed) == durable(injected) and completed['operation']['frame'] == injected['operation']['frame'] and
                  completed['world'] == before['world'] and completed['models'] == before['models'])
            record(case + '-states', {'before': before, 'marked': marked, 'injected': injected, 'completed': completed})
            screenshot(page, case + '-invalidated')
            if mode == 'session':
                js(page, "connection.session=__mh.savedSession;await recoverConnection();")
                page.wait_for_function("connection.phase==='ready'&&!document.body.classList.contains('connection-blocked')")

        before, marked = prepare_native_undo(page)
        arm(page)
        page.locator('#smTryLShape').focus()
        page.keyboard.press('Enter')
        page.wait_for_function("SpaceModelWorkspace.snapshot().phase==='preview'")
        source = js(page, "return {phase:SpaceModelWorkspace.snapshot().phase,summary:SpaceModelWorkspace.snapshot().resultSummary,name:$('smModelName').value,bottom:$('smBottom').value,height:$('smHeight').value};")
        release(page)
        check('MH04-source', 'trusted source switch survives late native Undo without reviving the previous model view',
              js(page, "return {phase:SpaceModelWorkspace.snapshot().phase,summary:SpaceModelWorkspace.snapshot().resultSummary,name:$('smModelName').value,bottom:$('smBottom').value,height:$('smHeight').value};") == source and
              js(page, "return !$('smMain').hidden&&$('smLibraryPanel').hidden&&SpaceModelWorkspace.snapshot().createdId===null&&JSON.stringify(__mhGate.mutations)===JSON.stringify(['line undo']);") and
              state(page)['world'] == before['world'] and state(page)['models'] == before['models'])
        record('MH04-source-state', {'source': source, 'after': state(page)})
        # The newly chosen example is intentionally an unsaved builder. Leave
        # it explicitly through the existing saved-model entry before resetting
        # the next case; do not bypass its draft/history guard.
        page.locator('#smLibrary').click()
        page.locator('[data-sm-open-model]').click()
        page.locator('#smLibrary').click()

        restore(page)
        baseline = state(page)
        # Both zero-point calibration and raw outline data are real global draft
        # records. They are seeded without geometry to isolate the history gate.
        for kind, setup, capture, cleanup in (
            ('zero-calibration', "fe.ulCalib={pts:[],mode:'two-point',raw:' 0 '};", 'fe.ulCalib', 'fe.ulCalib=null;'),
            ('face-outline', "fe.draft.pts=[{x:0,y:0},{x:120,y:0}];", 'fe.draft', 'fe.draft.pts=[];'),
        ):
            case = 'MH05-' + kind
            raw = js(page, setup + 'WorkspaceShell.refresh();return JSON.stringify(' + capture + ');')
            page.keyboard.press('Control+z')
            page.keyboard.press('Control+y')
            check(case, 'blocked library history preserves raw draft and complete World/models/history',
                  page.locator('#btnUndo').is_disabled() and page.locator('#btnRedo').is_disabled() and
                  durable(state(page)) == durable(baseline) and js(page, 'return JSON.stringify(' + capture + ');') == raw)
            js(page, cleanup + 'WorkspaceShell.refresh();')

        page.locator('#smClose').click()
        js(page, 'await ParameterUI.create();')
        page.locator('#paramName').fill('  保留原始參數名稱  ')
        parameter_raw = js(page, "return [...document.querySelectorAll('#parameterEditor input,#parameterEditor select')].map(e=>[e.id,e.getAttribute('data-input'),e.value]);")
        baseline = state(page)
        open_library(page)
        page.keyboard.press('Control+z')
        page.keyboard.press('Control+y')
        check('MH05-parameter', 'actual pending parameter editor retains raw values and unchanged project history',
              js(page, 'return ParameterUI.pending;') and page.locator('#btnUndo').is_disabled() and
              durable(state(page)) == durable(baseline) and
              js(page, "return [...document.querySelectorAll('#parameterEditor input,#parameterEditor select')].map(e=>[e.id,e.getAttribute('data-input'),e.value]);") == parameter_raw)
        page.locator('#smClose').click()
        js(page, 'ParameterUI.discard();')
        # Construct a disposable image source through the existing reference
        # importer, then start the actual room picker without selecting a room.
        # Calibration is public fixture setup; no candidate result is invented.
        js(page, """await enterFocus('face',1);fiShowTab('underlay');
          const c=document.createElement('canvas');c.width=280;c.height=190;const ctx=c.getContext('2d');
          ctx.fillStyle='#fff';ctx.fillRect(0,0,280,190);ctx.strokeStyle='#000';ctx.lineWidth=4;ctx.strokeRect(30,30,200,130);
          const blob=await new Promise(resolve=>c.toBlob(resolve));
          __mh.roomSource=await ReferenceWorkspace.sourceFromFile(new File([blob],'model-history-public-room.png',{type:'image/png'}));
          await ReferenceWorkspace.openSource(__mh.roomSource,1);""")
        page.locator('#refApply').click()
        page.wait_for_function("!$('referenceDialog').open&&!!ReferenceWorkspace.active(1)")
        js(page, "ReferenceWorkspace.active(1).mmPerPx=10;ReferenceWorkspace.calibrated(1,[[30,30],[230,30]],2000);ReferenceWorkspace.changed(1);renderFaceInspector();")
        if not js(page, "return $('refOutlineDetails').open;"):
            page.locator('#refOutlineDetails > summary').click()
        page.locator('#refRoomPick').click()
        page.wait_for_function('RoomOutlineWorkspace.hasWork&&RoomOutlineWorkspace.isPicking()')
        room_raw = js(page, 'return {page:ReferenceWorkspace.active(1),draft:fe.draft,tool:fe.tool};')
        baseline = state(page)
        open_library(page)
        page.keyboard.press('Control+z')
        page.keyboard.press('Control+y')
        check('MH05-room', 'actual pending room picker retains source calibration/raw draft and complete history',
              js(page, 'return RoomOutlineWorkspace.hasWork&&RoomOutlineWorkspace.isPicking();') and
              page.locator('#btnUndo').is_disabled() and page.locator('#btnRedo').is_disabled() and
              durable(state(page)) == durable(baseline) and js(page, 'return {page:ReferenceWorkspace.active(1),draft:fe.draft,tool:fe.tool};') == room_raw)
        page.locator('#smClose').click()
        js(page, 'RoomOutlineWorkspace.cancel();resetSceneFocus();')
        restore(page)
        baseline = state(page)

        # A real nested HTML modal with editable text owns native Ctrl+Z.
        js(page, "const d=document.createElement('dialog');d.id='mhNested';const input=document.createElement('input');input.id='mhNestedInput';d.append(input);document.body.append(d);d.showModal();WorkspaceShell.refresh();")
        page.locator('#mhNestedInput').fill('保留文字')
        page.locator('#mhNestedInput').press('End')
        page.keyboard.type('ABC')
        page.keyboard.press('Control+z')
        check('MH06', 'nested modal keeps native text Undo and leaves project history unchanged',
              page.locator('#mhNestedInput').input_value() == '保留文字' and
              durable(state(page)) == durable(baseline) and page.locator('#btnUndo').is_disabled())
        page.keyboard.press('Escape')
        check('MH06', 'Escape closes only the nested modal and preserves the library',
              js(page, "return !$('mhNested').open&&$('smWorkspace').open&&!$('smLibraryPanel').hidden;"))
        js(page, "$('mhNested').remove();WorkspaceShell.refresh();")

        readonly = context.new_page()
        readonly.on('pageerror', lambda error: browser_errors.append(str(error)))
        readonly.on('console', lambda message: console_errors.append(message.text) if message.type == 'error' else None)
        readonly.on('dialog', lambda dialog: dialog.accept())
        readonly.on('download', lambda download: downloads.append(download.suggested_filename))
        readonly.goto(URL)
        readonly.wait_for_function("connection.phase==='ready'&&!ReferenceWorkspace.busy&&ReferenceWorkspace.getProjectInfo().editingBlocked")
        locks = js(readonly, 'return await navigator.locks.query();')
        session = js(page, 'return connection.session;')
        check('MH07', 'second real tab has a genuine readonly editor lease under Web Locks contention',
              any(lock['name'] == 'geometry-canvas-service-editor-' + session for lock in locks['held']) and
              js(readonly, "return ReferenceWorkspace.getProjectInfo().recovery.state==='readonly';"), locks)
        readonly.evaluate("""records=>{const h=ReferenceWorkspace.history;
          ReferenceWorkspace.context().models=structuredClone(records);
          h.changeModels([]);h.changeModels(records);h.changeModels([]);h.tryLocal('line undo');ReferenceWorkspace.sync();
          const original=window.fetch;window.__mhReadonlyMutations=[];window.fetch=(...args)=>{let b={};try{b=JSON.parse(args[1]?.body||'{}')}catch(_){}
            if(String(args[0]).startsWith('/upload')||String(args[0])==='/api'&&/^(line |drag |reset$|default$|loadfile |engineering-confirm |assembly-confirm )/.test(b.cmd||''))__mhReadonlyMutations.push([String(args[0]),b.cmd]);
            return original(...args);};}""", fixture['models'])
        open_library(readonly)
        readonly.wait_for_function("!!document.querySelector('[data-sm-open-model]')")
        baseline = state(readonly)
        check('MH07', 'readonly fixture has meaningful nonempty Undo and Redo stacks',
              baseline['undo'] > 0 and baseline['redo'] > 0 and baseline['models'] == fixture['models'])
        check('MH07', 'real readonly lease disables original Undo/Redo/remove but permits saved 3D entry',
              all(readonly.locator(s).is_disabled() for s in ('#btnUndo', '#btnRedo', '[data-sm-remove-model]')) and
              not readonly.locator('[data-sm-open-model]').is_disabled())
        for selector in ('#btnUndo', '#btnRedo', '[data-sm-remove-model]'):
            click_disabled(readonly, selector)
        readonly.keyboard.press('Control+z')
        readonly.keyboard.press('Control+y')
        rejection = readonly.evaluate("id=>{try{ReferenceWorkspace.removeSpaceModel(id);return null}catch(error){return error.message}}", model_id)
        check('MH07', 'trusted shortcuts/clicks and direct mutation API all preserve readonly data',
              isinstance(rejection, str) and durable(state(readonly)) == durable(baseline) and
              js(readonly, 'return __mhReadonlyMutations.length===0;'))
        readonly.locator('[data-sm-open-model]').click()
        readonly.wait_for_function("!$('smMain').hidden&&SpaceModelWorkspace.snapshot().viewer.objectCount>0")
        check('MH07', 'readonly opens the actual saved 3D mesh without modifying World or metadata',
              js(readonly, 'return SpaceModelWorkspace.snapshotRecord().id;') == model_id and
              durable(state(readonly)) == durable(baseline) and js(readonly, 'return __mhReadonlyMutations.length===0;'))
        record('MH07-readonly-states', {'before': baseline, 'after': state(readonly), 'locks': locks})
        screenshot(readonly, 'MH07-genuine-readonly-3d')
        readonly.close()
        check('MH08', 'no unexpected downloads, console errors or uncaught browser exceptions', downloads == [] and browser_errors == [] and console_errors == [], {'page': browser_errors, 'console': console_errors})
        final_runtime = json.load(urllib.request.urlopen(URL + 'runtime'))
        final_source = {'head': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'), 'gitStatus': git('status', '--porcelain'),
                        'harnessSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        receipt.update(runtimeAfter=final_runtime, sourceAfter=final_source)
        check('MH09', 'source, harness and fresh runtime identity are unchanged through the complete run',
              final_runtime == runtime and all(final_source[key] == receipt[key] for key in final_source))
        assert dict(Counter(entry['case'] for entry in checks)) == EXPECTED_CASES, 'Incomplete planned acceptance census.'
        browser.close()
    receipt.update(completed=True)
except Exception as error:
    receipt.update(completed=False, error=str(error), traceback=traceback.format_exc())
    if page is not None:
        try:
            screenshot(page, 'failure')
            (OUT / 'failure-state.json').write_text(json.dumps(state(page), ensure_ascii=False, indent=2))
        except Exception:
            pass
    raise
finally:
    if 'runtimeAfter' not in receipt:
        try:
            receipt['runtimeAfter'] = json.load(urllib.request.urlopen(URL + 'runtime', timeout=10))
            receipt['sourceAfter'] = {'head': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'),
                                      'gitStatus': git('status', '--porcelain'), 'harnessSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        except Exception as error:
            receipt['afterIdentityError'] = str(error)
    receipt.update(checks=checks, passed=sum(c['pass'] for c in checks), failed=sum(not c['pass'] for c in checks),
                   browserErrors=browser_errors, consoleErrors=console_errors, downloads=downloads)
    (OUT / 'result.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2))
    print('MODEL_LIBRARY_HISTORY_RESULT ' + json.dumps({key: receipt[key] for key in ('schema', 'expectedAssertions', 'completed', 'passed', 'failed', 'head', 'development')}, ensure_ascii=False), flush=True)
