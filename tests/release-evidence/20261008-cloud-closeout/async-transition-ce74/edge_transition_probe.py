"""Private supplemental #173 probe; see source-plan.md for the fixed oracle.

Browser execution requires the integration owner's exclusive slot. This script
does not start/restart a server or edit repository files.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
import traceback
import urllib.error
import urllib.request

from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path('/workspace/geometry-axiom')
SCRIPTS = ['edge_transition_probe.py', 'edge_transition_instrumentation.js',
           'run_edge_transition_probe.py', 'source-plan.md']
A_INITIAL = 'boundary 731 outline 0,0 4000,0 4000,3000 0,3000 hole 3000,1000 3500,1000 3500,1500 3000,1500'
A_EXPECTED = 'boundary 731 outline 0,0 4200,0 4200,3000 0,3000 hole 3000,1000 3500,1000 3500,1500 3000,1500'
B_OUTLINE = [[0, 0], [4000, 0], [4000, 3000], [0, 3000]]
parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:18971/')
parser.add_argument('--out', required=True)
parser.add_argument('--width', type=int, choices=[1400, 390])
parser.add_argument('--scope', choices=['main', 'face'])
parser.add_argument('--mode', choices=['success-control', 'held-success-to-B'])
args = parser.parse_args()
args.url = args.url.rstrip('/') + '/'
OUT = pathlib.Path(args.out)
OUT.mkdir(parents=True, exist_ok=False)
records = []


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(label):
    commands = []
    for cmd in [['pwd'], ['git', 'status', '--short'], ['git', 'rev-parse', 'HEAD'],
                ['git', 'diff', '--binary'], ['git', 'diff', '--cached', '--binary'],
                ['git', 'rev-parse', 'origin/main']]:
        result = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=15)
        commands.append({'argv':cmd, 'stdout':result.stdout, 'stderr':result.stderr,
                         'exitCode':result.returncode})
    data = {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'commands':commands,
            'sourceSha256':{str(p.relative_to(REPO)):sha(p) for p in sorted(
                [REPO/'geometry-web/app.js', REPO/'geometry-web/space-workspace.js',
                 REPO/'geometry-web/index.html', *REPO.glob('geometry-web/*.css')])},
            'scriptSha256':{name:sha(BASE/name) for name in SCRIPTS}}
    try:
        with urllib.request.urlopen(args.url+'runtime', timeout=10) as response:
            raw = response.read()
            (OUT/(label+'-runtime.raw.json')).write_bytes(raw)
            data.update(runtime=json.loads(raw), runtimeHttp=response.status,
                        runtimeBodySha256=hashlib.sha256(raw).hexdigest())
    except Exception as error:
        data['runtimeError'] = str(error)
        if isinstance(error, urllib.error.HTTPError):
            raw = error.read()
            (OUT/(label+'-runtime-error.raw')).write_bytes(raw)
            data.update(runtimeHttp=error.code, runtimeErrorBodySha256=hashlib.sha256(raw).hexdigest())
    save(label+'.json', data)
    return data


def evaluate_async(page, expression, arg=None):
    # A deadline only fails the harness; it never declares product completion.
    # The original callback remains the awaited value and is not cancelled or
    # replaced. This also bounds an unexpected API preview/dialog during setup.
    return page.evaluate("""async arg=>{let timer;try{return await Promise.race([
      ("""+expression+""")(arg),new Promise((_,reject)=>{timer=setTimeout(
        ()=>reject(new Error('Probe async observation deadline (60000 ms)')),60000);})
      ]);}finally{clearTimeout(timer);}}""", arg)


def wait(page, expression):
    page.wait_for_function(expression, timeout=15000)


def click(page, selector):
    page.locator(selector).click(timeout=7000)


def close_drawers(page):
    if page.evaluate("document.body.classList.contains('drawer-left-open') || document.body.classList.contains('drawer-right-open')"):
        page.keyboard.press('Escape')
        wait(page, "!document.body.classList.contains('drawer-left-open') && !document.body.classList.contains('drawer-right-open')")


def open_drawer(page, side, face=False):
    if page.viewport_size['width'] > 900:
        return
    if page.evaluate('(s)=>document.body.classList.contains("drawer-"+s+"-open")', side):
        return
    close_drawers(page)
    trigger = ('#workspaceToggle' if face else '#toggle') + side.title()
    if side == 'right' and not face and not page.locator(trigger).is_visible() and page.locator('#inspectorContent').is_visible():
        return  # Main inspector is inline in this composition layout.
    click(page, trigger)
    wait(page, f'document.body.classList.contains("drawer-{side}-open")')


def world(page, name, stage):
    value = evaluate_async(page, "async()=>{const r=await api('dump');if(!r.ok)throw Error(JSON.stringify(r));return r.text;}")
    (OUT/f'{name}-world-{stage}.scene').write_text(value)
    return value


def audit(page):
    return page.evaluate('__edgeTransitionAudit.read()')


def state(page):
    return page.evaluate('__edgeTransitionAudit.state()')


def read_input(page, selector):
    return page.evaluate('''s=>{const e=document.querySelector(s);return e ? {
      value:e.value, model:e.defaultValue, connected:e.isConnected,
      visible:!!(e.getClientRects().length && getComputedStyle(e).visibility!=='hidden')
    }:null;}''', selector)


def setup(page, scope):
    # Setup is explicitly native API + renderer, not a claimed product route.
    initial = page.evaluate('({view3,ocOn:oc.on,focus:oc.focus})')
    if initial != {'view3':False, 'ocOn':True, 'focus':None}:
        raise RuntimeError('Fresh context did not start at object canvas: '+json.dumps(initial))
    lines = [
        'surface 731 origin 0 0 2500 u +x v +y outline '+A_INITIAL.split(' outline ', 1)[1],
        'surface 732 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
        'canvas-pos boundary 731 30 30', 'canvas-pos boundary 732 310 30'
    ]
    fixture = evaluate_async(page, '''async lines=>{const out=[await api('reset')];
      for(const line of lines)out.push(await api('line '+line));
      await renderObjects();return out;}''', lines)
    if any(item.get('ok') is not True for item in fixture):
        raise RuntimeError('Fixture refused: '+json.dumps(fixture))
    wait(page, "connection.phase==='ready' && !oc.busy && oc.faces.some(x=>x.id===731) && oc.faces.some(x=>x.id===732)")
    open_drawer(page, 'left')
    click(page, '.object-row[data-kind="boundary"][data-id="731"]')
    close_drawers(page)
    open_drawer(page, 'right')
    if scope == 'face':
        click(page, '#inspEnter')
        wait(page, "oc.edit?.bid===731 && oc.focus?.t==='face' && oc.focus?.id===731")
        open_drawer(page, 'right', face=True)
        click(page, '#faceInspectorTabs [data-fi-tab="prop"]')
    selector = '#edgeLength0' if scope == 'face' else '#mainEdgeLength0'
    page.locator(selector).wait_for(state='visible', timeout=15000)
    if read_input(page, selector) != {'value':'4000', 'model':'4000', 'connected':True, 'visible':True}:
        raise RuntimeError('Initial edge input is not the 4000 mm fixture')
    return selector, {'commands':lines, 'results':fixture, 'initialPresentation':initial}


def run_case(page, name, scope, mode):
    selector, fixture = setup(page, scope)
    before = world(page, name, 'before')
    if before.splitlines().count(A_INITIAL) != 1:
        raise RuntimeError('Fixture dump lacks unique exact A boundary')
    expected = before.replace(A_INITIAL, A_EXPECTED, 1)
    (OUT/f'{name}-world-expected.scene').write_text(expected)
    held = mode == 'held-success-to-B'
    page.evaluate('(hold)=>__edgeTransitionAudit.arm(731,hold)', held)
    click(page, selector)
    page.keyboard.press('Control+A')
    page.keyboard.insert_text('4200')
    page.keyboard.press('Tab')
    wait(page, "__edgeTransitionAudit.gate.phase==='"+('held' if held else 'returned')+"'")
    native = page.evaluate('__edgeTransitionAudit.gate.nativeReply')
    if native.get('ok') is not True or native.get('preview'):
        raise RuntimeError('Legal 4200 fixture did not yield native commit: '+json.dumps(native))
    result = {'scope':scope, 'mode':mode, 'fixture':fixture, 'nativeReply':native}
    if held:
        gate_world = world(page, name, 'gate')
        result['atGate'] = {'state':state(page), 'input':read_input(page, selector)}
        close_drawers(page)
        if scope == 'face':
            click(page, '#workspaceBackButton')
            wait(page, "oc.focus===null && oc.edit===null && document.querySelector('#objectWorkspace').hidden")
        click(page, '#btnObj')
        wait(page, "view3===true && oc.on===false && workSurfaces.length===2 && !!layout")
        open_drawer(page, 'left')
        if page.locator('#workSurf').input_value() != '731':
            raise RuntimeError('Expected initial work surface A before real keyboard selection of B')
        click(page, '#workSurf')
        page.keyboard.press('Home')
        page.keyboard.press('ArrowDown')
        page.keyboard.press('Enter')
        wait(page, "document.querySelector('#workSurf').value==='732'")
        close_drawers(page)
        click(page, '[data-v3-tool="edit"]')
        wait(page, "__edgeTransitionAudit.gate.phase==='held' && editBid===732 && editDrag===null && __edgeTransitionAudit.draws.some(x=>x.bid===732 && x.token===editToken && x.phase==='settled') && __edgeTransitionAudit.draws.every(x=>x.phase==='settled')")
        b_before = state(page)
        if b_before['handles'] <= 0 or not b_before['editLoops'] or b_before['editLoops'][0]['verts'] != B_OUTLINE:
            raise RuntimeError('B did not finish drawing its independent 4000x3000 handles')
        ready_world = world(page, name, 'B-ready')
        page.screenshot(path=str(OUT/f'{name}-B-ready.png'))
        page.evaluate('__edgeTransitionAudit.gate.release()')
        wait(page, "__edgeTransitionAudit.gate.phase==='released' && __edgeTransitionAudit.changes.length>0 && __edgeTransitionAudit.changes.every(x=>x.phase==='settled') && __edgeTransitionAudit.draws.every(x=>x.phase==='settled')")
        b_after = state(page)
        after_world = world(page, name, 'released')
        page.screenshot(path=str(OUT/f'{name}-released.png'))
        owner_keys = ['workSurf', 'view3', 'tool', 'editBid', 'editToken', 'ocOn', 'ocEdit', 'ocFocus']
        visible_keys = ['groups', 'handles', 'handleShapes', 'groupShapes', 'canvasVisible', 'workspaceHidden', 'inspectorHidden']
        model_keys = ['editLoops', 'editDrag']
        owner_changes = [key for key in owner_keys if b_before[key] != b_after[key]]
        visible_changes = [key for key in visible_keys if b_before[key] != b_after[key]]
        model_changes = [key for key in model_keys if b_before[key] != b_after[key]]
        result.update(beforeB=b_before, afterB=b_after, ownershipChangedFields=owner_changes,
                      visibleChangedFields=visible_changes, editModelChangedFields=model_changes,
                      ownershipTokenOnlyChange=owner_changes == ['editToken'] and not visible_changes and not model_changes,
                      gateWorldIsOnlyExpectedAChange=gate_world == expected,
                      BReadyWorldEqualsGate=ready_world == gate_world,
                      releasedWorldEqualsGate=after_world == gate_world,
                      ok=gate_world == expected and ready_world == gate_world and after_world == gate_world
                         and not owner_changes and not visible_changes and not model_changes)
    else:
        wait(page, "__edgeTransitionAudit.changes.length>0 && __edgeTransitionAudit.changes.every(x=>x.phase==='settled') && __edgeTransitionAudit.draws.every(x=>x.phase==='settled')")
        actual_input = read_input(page, selector)
        after_world = world(page, name, 'completed')
        page.screenshot(path=str(OUT/f'{name}-completed.png'))
        result.update(inputAfter=actual_input, stateAfter=state(page), worldIsOnlyExpectedAChange=after_world == expected,
                      ok=actual_input == {'value':'4200','model':'4200','connected':True,'visible':True} and after_world == expected)
    observed = audit(page)
    changes = observed['changes']
    single_trusted_change = len(changes) == 1 and changes[0]['trusted'] is True and changes[0]['id'] == selector[1:] and changes[0]['value'] == '4200' and changes[0]['phase'] == 'settled'
    expected_command = observed['gate']['command'] == 'line '+A_EXPECTED
    nav = observed['navigation']
    required = [('click', 'btnObj'), ('change', 'workSurf'), ('click', None)]
    if scope == 'face':
        required.insert(0, ('click', 'workspaceBackButton'))
    route = [item for item in nav if item.get('id') in ['workspaceBackButton', 'btnObj', 'workSurf'] or item.get('tool') == 'edit']
    route_ok = not held or ([(item['type'], item.get('id')) for item in route] == required and
                           all(item['trusted'] for item in route) and
                           next(item for item in route if item.get('id') == 'workSurf')['value'] == '732')
    result.update(audit=observed, singleTrusted4200Change=single_trusted_change,
                  exactNativeCommand=expected_command, realNavigationRoute=route_ok)
    result['ok'] = result['ok'] and single_trusted_change and expected_command and route_ok
    return result


exit_code = 2
fatal_error = None
initial = None
after_identity = None
try:
    initial = identity('before')
    if initial.get('runtime', {}).get('fresh') is not True or initial.get('runtimeHttp') != 200:
        raise RuntimeError('Runtime not proven fresh; stop before browser launch')
    for source in SCRIPTS:
        (OUT/('executed-'+source)).write_bytes((BASE/source).read_bytes())
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True, chromium_sandbox=True)
        save('browser.json', {'version':browser.version, 'executable':'/usr/bin/chromium',
                              'executableSha256':sha(pathlib.Path('/usr/bin/chromium')),
                              'sandbox':True, 'launchArgumentsRequested':[]})
        try:
            for width in ([args.width] if args.width else [1400, 390]):
                for scope in ([args.scope] if args.scope else ['main', 'face']):
                    for mode in ([args.mode] if args.mode else ['success-control', 'held-success-to-B']):
                        name = f'edge-transition-{width}-{scope}-{mode}'
                        ctx = browser.new_context(viewport={'width':width, 'height':900 if width > 900 else 844})
                        page = ctx.new_page()
                        errors = []
                        page.on('pageerror', lambda error:errors.append(str(error)))
                        ctx.tracing.start(screenshots=True, snapshots=True, sources=True)
                        row = {'name':name, 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
                        try:
                            response = page.goto(args.url, wait_until='domcontentloaded', timeout=30000)
                            if response.status != 200:
                                raise RuntimeError('Product entry HTTP '+str(response.status))
                            wait(page, "typeof api==='function' && connection.phase==='ready'")
                            page.evaluate((BASE/'edge_transition_instrumentation.js').read_text())
                            row.update(run_case(page, name, scope, mode))
                            row['pageErrors'] = errors
                            if errors:
                                row['ok'] = False
                        except Exception as error:
                            row.update(ok=False, preconditionOrHarnessError=str(error),
                                       traceback=traceback.format_exc(), pageErrors=errors)
                            try:
                                row.update(audit=audit(page), failureState=state(page))
                                page.screenshot(path=str(OUT/f'{name}-error.png'))
                            except Exception as capture_error:
                                row['failureCaptureError'] = str(capture_error)
                        finally:
                            try:
                                ctx.tracing.stop(path=str(OUT/f'{name}-trace.zip'))
                            except Exception as trace_error:
                                row.update(ok=False, traceCaptureError=str(trace_error))
                            finally:
                                ctx.close()
                            records.append(row)
                            save(name+'.json', row)
                            save('results.json', records)
                        print(json.dumps({'name':name,'ok':row['ok'], 'harnessError':row.get('preconditionOrHarnessError')}, ensure_ascii=False), flush=True)
        finally:
            browser.close()
    exit_code = 1 if any(not row.get('ok') for row in records) else 0
except Exception as error:
    fatal_error = {'error':str(error), 'traceback':traceback.format_exc()}
    save('fatal-error.json', fatal_error)
    print(fatal_error['traceback'], file=sys.stderr, flush=True)
finally:
    try:
        after_identity = identity('after')
        stable = initial is not None and all(initial.get(key) == after_identity.get(key) for key in
                                             ['commands', 'sourceSha256', 'scriptSha256', 'runtime'])
        save('identity-comparison.json', {'stable':stable,
             'comparedFields':['commands', 'sourceSha256', 'scriptSha256', 'runtime']})
        if not stable or after_identity.get('runtime', {}).get('fresh') is not True:
            exit_code = 2
    except Exception as error:
        save('after-identity-error.json', {'error':str(error)})
        exit_code = 2
    save('receipt.json', {'argv':sys.argv, 'exitCode':exit_code, 'tests':len(records),
         'fatalError':fatal_error, 'scope':'Private synthetic #173 successful-edge control and held native-success reply across actual Back/three-view/B Edit routes. Not direct three-view edge editing or full product acceptance.'})
sys.exit(exit_code)
