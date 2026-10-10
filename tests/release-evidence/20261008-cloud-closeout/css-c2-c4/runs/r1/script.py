"""Private #123 C2/C4 UI acceptance. Requires the sole browser slot.

P12/P19 synthetic native fixtures are API setup. Space entry, drawers, slot clicks
and Tab/Enter are trusted browser input; no programmatic focus/click or force.
This is not UI geometry authoring, physical-mobile or private-design comparison.
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


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


BEAM = [
    'boundary 1 outline 0,0 4000,0 4000,3000 0,3000',
    'placement 1 on boundary 1 origin 0 0 2500 u +x v +y',
    'boundary 2 outline 0,0 3000,0 3000,4000 0,4000',
    'placement 2 on boundary 2 origin 0 0 0 u +y v +x',
    'boundary 3 outline 0,0 4000,0 4000,2500 0,2500',
    'placement 3 on boundary 3 origin 0 0 0 u +x v +z',
    'boundary 4 outline 0,0 2500,0 2500,4000 0,4000',
    'placement 4 on boundary 4 origin 0 3000 0 u +z v +x',
    'boundary 5 outline 0,0 2500,0 2500,3000 0,3000',
    'placement 5 on boundary 5 origin 0 0 0 u +z v +y',
    'boundary 6 outline 0,0 3000,0 3000,2500 0,2500',
    'placement 6 on boundary 6 origin 4000 0 0 u +y v +z',
    'space 1 boundary 1 2 3 4 5 6',
    'column 1 in 1 at 1000 1000 size 400 400',
    'beam 1 in 1 along y from 0 to 3000 at 2000 width 300 depth 500',
]
SLOTS = [
    'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'surface 2 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000',
    'space 1 boundary 1 2',
    'column 1 in 1 at 1000 800 size 400 400 z 0 2500',
    'column 2 at 5000 5000 size 400 400 z 0 2000',
    'boundary 3 outline 0,0 500,0 500,400 0,400',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/workspace/geometry-axiom'))
    parser.add_argument('--url', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--bridge', type=Path, default=Path('/tmp/geometry-tests/bridge'))
    parser.add_argument('--chrome', default='/usr/bin/chromium')
    parser.add_argument('--width', choices=(1400, 390), type=int, action='append')
    parser.add_argument('--only', choices=('all', 'beam', 'slots'), default='all')
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    address = urlsplit(args.url)
    assert address.scheme == 'http' and address.hostname in ('127.0.0.1', 'localhost')
    assert address.port not in (None, 8765) and address.path == '/' and not any((address.query, address.fragment, address.username, address.password))
    assert not out.is_relative_to(root) and out != Path('/')
    out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(root / 'tests'))
    import binaries
    receipt = {'schema': 'geometry-issue123-c2-c4/1', 'started': stamp(), 'argv': [sys.executable, *sys.argv],
               'script_sha256': sha(__file__), 'python': sys.version, 'playwright': importlib.metadata.version('playwright'),
               'sandbox': True, 'launch_arguments_requested': [], 'cases': [], 'exit_code': 1,
               'scope': ['P12/P19 API fixture setup; no UI authoring claim', 'Actual pointer/double-click and Tab/Enter inputs',
                         'Beam token slice only; no column/grid/preview palette claim',
                         'Existing slot action discoverability and existing preset/navigation; no geometry placement submission',
                         '390 viewport, not physical-device or IME; no private ZIP visual comparison']}
    browser = page = context = None
    phase = 'preflight'

    def identity(label):
        commands = []
        for command in (['pwd'], ['git', 'rev-parse', 'HEAD'], ['git', 'rev-parse', 'HEAD^{tree}'],
                        ['git', 'rev-parse', 'origin/main'], ['git', 'status', '--short'], ['git', 'diff', '--binary']):
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            commands.append({'command': command, 'stdout': result.stdout, 'stderr': result.stderr, 'exit_code': result.returncode})
            assert result.returncode == 0, commands[-1]
        runtime_bytes = urlopen(args.url + 'runtime', timeout=15).read()
        (out / (label + '-runtime.raw.json')).write_bytes(runtime_bytes)
        runtime = json.loads(runtime_bytes)
        assert runtime.get('fresh') is True and Path(runtime['root']).resolve() == root
        bridge = args.bridge.resolve()
        binary = binaries.inspect_one(binaries.BY_NAME['bridge'], path=bridge)
        assert binary.state == 'fresh', binary.as_dict()
        process_list = subprocess.run(['ps', '-eo', 'pid=,ppid='], capture_output=True, text=True)
        write(out / (label + '-process-parents.json'), {'command': process_list.args, 'stdout': process_list.stdout,
              'stderr': process_list.stderr, 'exit_code': process_list.returncode})
        assert process_list.returncode == 0
        parents = [tuple(map(int, line.split())) for line in process_list.stdout.splitlines() if line.strip()]
        assert any(pid == runtime['pid'] for pid, _ in parents)
        owned = []
        for pid, parent in parents:
            if parent == runtime['pid'] and Path(f'/proc/{pid}/exe').resolve() == bridge:
                owned.append({'pid': pid, 'live_sha256': sha(f'/proc/{pid}/exe')})
        assert len(owned) == 1 and owned[0]['live_sha256'] == sha(bridge)
        (out / (label + '-bridge.fingerprint.json')).write_bytes(bridge.with_name(bridge.name + binaries.SIDECAR_SUFFIX).read_bytes())
        value = {'checked_at': stamp(), 'commands': commands, 'head': commands[1]['stdout'].strip(),
                 'tree': commands[2]['stdout'].strip(), 'status': commands[4]['stdout'],
                 'dirty_diff_sha256': hashlib.sha256(commands[5]['stdout'].encode()).hexdigest(),
                 'runtime': runtime, 'bridge': {'registry': binary.as_dict(), 'sha256': sha(bridge), 'owned_direct_child': owned},
                 'sources': {name: sha(root / name) for name in ('geometry-web/app.css', 'geometry-web/app.js',
                             'geometry-web/index.html', 'geometry-web/workspace-shell.js', 'geometry-web/serve.py')}}
        write(out / (label + '-identity.json'), value)
        assert value['status'] == '', 'Clean integration candidate required'
        return value

    def ready():
        page.wait_for_function("connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy&&pendingApiResults.size===0", timeout=30000)

    def native(command):
        result = page.evaluate('async command=>await apiRequest(command)', command)
        with (case_out / 'native-commands.jsonl').open('a') as stream:
            stream.write(json.dumps({'time': stamp(), 'phase': phase, 'command': command, 'result': result}, ensure_ascii=False) + '\n')
        assert result.get('ok') is True, result
        return result

    def snapshot(label):
        result = {key: native(key) for key in ('dump', 'objects', 'references')}
        write(case_out / (label + '.json'), result)
        (case_out / (label + '.scene')).write_text(result['dump']['text'])
        return result

    def drawer(side, opened):
        if width > 680:
            return
        state = page.evaluate('(side)=>document.body.classList.contains("drawer-"+side+"-open")', side)
        if state != opened:
            if opened:
                page.locator('#workspaceToggle' + side.capitalize()).click()
            else:
                page.locator('#spaceWorkspaceLayout [data-close-panel="' + side + '"]').click()
            page.wait_for_function('([side,opened])=>document.body.classList.contains("drawer-"+side+"-open")===opened', arg=[side, opened])

    def enter_space():
        # The established F shortcut fits the cards; this is actual key input.
        for _ in range(6):
            lesson = page.locator('[data-guidance-dismiss]:visible')
            if lesson.count() == 0:
                break
            lesson.first.click()
        assert page.locator('[data-guidance-dismiss]:visible').count() == 0, 'Unexpected number of tool lessons'
        page.keyboard.press('f')
        page.locator('.ocard[data-kind="space"][data-id="1"] .ocard-frame').dblclick(timeout=15000)
        page.wait_for_function("oc.focus?.t==='space'&&oc.focus.id===1&&!document.querySelector('#spaceWorkspaceLayout').hidden", timeout=30000)
        ready()

    def setup(lines):
        native('reset')
        for line in lines:
            native('line ' + line)
        assert page.evaluate('async()=>await renderObjects()') is True
        ready()
        enter_space()

    def styles():
        return page.evaluate('''()=>{
          const beam=document.querySelector('#spacePlanSvg .space-plan-beam');
          const icon=document.querySelector('#spaceRcList .type-icon.beam');
          const b=getComputedStyle(beam),i=getComputedStyle(icon);
          const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};};
          return {beamCount:document.querySelectorAll('#spacePlanSvg .space-plan-beam').length,
            iconCount:document.querySelectorAll('#spaceRcList .type-icon.beam').length,
            listLabel:icon.closest('.space-boundary-button').querySelector('strong').textContent,
            stroke:b.stroke,fill:b.fill,color:i.color,background:i.backgroundColor,
            beamRect:rect(beam),iconRect:rect(icon),display:b.display,visibility:b.visibility};
        }''')

    def check_beam():
        setup(BEAM)
        # openSpaceWorkspace publishes focus/layout before awaited rendering.
        # Wait for the actual beam/list artifacts, not that early navigation flag.
        page.wait_for_function("""()=>{const b=document.querySelector('#spacePlanSvg .space-plan-beam');
          const r=b?.getBoundingClientRect();return document.querySelectorAll('#spacePlanSvg .space-plan-beam').length===1
          &&document.querySelectorAll('#spaceRcList .type-icon.beam').length===1&&r.width>0&&r.height>0;}""", timeout=30000)
        baseline = snapshot('before')
        assert len(baseline['objects']['beams']) == 1 and baseline['objects']['beams'][0]['id'] == 1
        drawer('left', True)
        result = styles()
        write(case_out / 'computed-style.json', result)
        assert result['beamCount'] == result['iconCount'] == 1 and result['listLabel'] == '樑 1', result
        assert result['stroke'] == result['color'] == 'rgb(72, 105, 135)', result
        assert result['fill'] == result['background'] == 'rgb(237, 243, 248)', result
        assert result['display'] != 'none' and result['visibility'] == 'visible' and result['beamRect']['width'] > 0 and result['beamRect']['height'] > 0
        assert result['iconRect']['width'] > 0 and result['iconRect']['height'] > 0
        page.screenshot(path=str(case_out / 'beam-list.png'), full_page=True)
        drawer('left', False)
        page.locator('#spacePlanSvg .space-plan-beam').wait_for(state='visible')
        page.screenshot(path=str(case_out / 'beam-plan.png'), full_page=True)
        assert snapshot('after') == baseline, 'CSS/read-only UI navigation changed native World/references/revision'

    def slot_button():
        return page.locator('#spaceInspectorContent .slot-empty[data-slot-label="前牆"]')

    def assert_slot_open(label):
        page.wait_for_function("""oc.focus?.t==='face'&&oc.focus.id===3&&oc.edit?.bid===3
          &&document.querySelector('#placeU')&&document.querySelector('#placeV')
          &&pendingSlot?.space===1&&pendingSlot.bid===3&&pendingSlot.label==='前牆'
          &&document.querySelector('#status').textContent.includes('前牆')
          &&document.querySelector('#status').textContent.includes('面 3')""", timeout=30000)
        ready()
        actual = page.evaluate('''()=>({u:document.querySelector('#placeU').value,v:document.querySelector('#placeV').value,
            preset:PLACE_PRESETS['y=0 牆'],status:document.querySelector('#status').textContent,
            pending:pendingSlot&&{space:pendingSlot.space,bid:pendingSlot.bid,label:pendingSlot.label,presetName:pendingSlot.presetName}})''')
        write(case_out / (label + '-opened.json'), actual)
        assert actual['u'] == actual['preset']['u'] == '+x' and actual['v'] == actual['preset']['v'] == '+z', actual
        assert actual['pending'] == {'space': 1, 'bid': 3, 'label': '前牆', 'presetName': 'y=0 牆'}, actual
        assert '前牆' in actual['status'] and '面 3' in actual['status'], actual
        page.screenshot(path=str(case_out / (label + '-opened.png')), full_page=True)

    def check_slots():
        setup(SLOTS)
        page.wait_for_function("""document.querySelectorAll('#spaceInspectorContent .slot-empty').length===4
          &&!!document.querySelector('#spaceInspectorContent .slot-empty[data-slot-label="前牆"]')""", timeout=30000)
        baseline = snapshot('before')
        drawer('right', True)
        page.mouse.move(0, 0)
        measurement = page.locator('#spaceInspectorContent .slot-empty').evaluate_all('''buttons=>buttons.map(b=>{
          const a=b.querySelector('.slot-action'),i=b.querySelector('.slot-idle'),r=a.getBoundingClientRect();
          const c=getComputedStyle(a);return {label:b.dataset.slotLabel,aria:b.getAttribute('aria-label'),text:a.textContent,
            actionDisplay:c.display,idleDisplay:getComputedStyle(i).display,visibility:c.visibility,
            rect:{x:r.x,y:r.y,width:r.width,height:r.height},hover:b.matches(':hover'),focus:b.matches(':focus-visible')};})''')
        write(case_out / 'initial-nonhover-slots.json', measurement)
        assert len(measurement) == 4, measurement
        for row in measurement:
            assert row['aria'] == '放置' + row['label'] and row['text'] == '＋放置', row
            assert row['actionDisplay'] != 'none' and row['idleDisplay'] == 'none' and row['visibility'] == 'visible', row
            assert row['rect']['width'] > 0 and row['rect']['height'] > 0 and not row['hover'] and not row['focus'], row
        page.screenshot(path=str(case_out / 'initial-nonhover.png'), full_page=True)
        slot_button().click()
        assert_slot_open('pointer')
        assert snapshot('after-pointer') == baseline, 'Opening the existing preset must not commit geometry'
        page.locator('#workspaceBackButton').click()
        page.wait_for_function("oc.focus?.t==='space'&&oc.focus.id===1&&!document.querySelector('#spaceWorkspaceLayout').hidden")
        ready()
        drawer('right', True)
        page.mouse.move(0, 0)
        focus_path = []
        found = False
        for _ in range(120):
            page.keyboard.press('Tab')
            current = page.evaluate('''()=>{const e=document.activeElement;return {tag:e.tagName,id:e.id,
                cls:e.className,slot:e.dataset.slotLabel||null,text:e.textContent?.slice(0,100),
                target:e.matches('#spaceInspectorContent .slot-empty[data-slot-label="前牆"]')};}''')
            focus_path.append(current)
            if current['target']:
                found = True
                break
        write(case_out / 'tab-focus-path.json', focus_path)
        assert found, 'Existing front-wall slot not reachable in 120 real Tab key presses'
        page.screenshot(path=str(case_out / 'tab-focused.png'), full_page=True)
        page.keyboard.press('Enter')
        assert_slot_open('keyboard')
        assert snapshot('after-keyboard') == baseline, 'Tab/Enter preset navigation must not commit geometry'

    try:
        receipt['before'] = identity('before')
        (out / 'script.py').write_bytes(Path(__file__).read_bytes())
        write(out / 'fixtures.json', {'beam': BEAM, 'slots': SLOTS, 'origin': 'geometry-web/cdp_test.js P12/P19; API setup explicitly recorded'})
        from playwright.sync_api import sync_playwright
        with sync_playwright() as driver:
            try:
                phase = 'browser-launch'
                browser = driver.chromium.launch(executable_path=args.chrome, headless=True, chromium_sandbox=True)
                receipt['browser_version'] = browser.version
                for width in args.width or (1400, 390):
                    for kind in ('beam', 'slots') if args.only == 'all' else (args.only,):
                        case_out = out / (kind + '-' + str(width));case_out.mkdir()
                        row = {'case': kind, 'width': width, 'started': stamp(), 'passed': False};receipt['cases'].append(row)
                        errors, capture_errors, cleanup_errors = [], [], []
                        context = browser.new_context(viewport={'width': width, 'height': 1000 if width == 1400 else 844})
                        context.add_init_script('''window.__cssProbeInputs=[];
                          for(const type of ['pointerdown','click','dblclick','keydown'])document.addEventListener(type,e=>{
                            const target=e.target.closest?.('.slot-empty,.ocard,button')||e.target;
                            window.__cssProbeInputs.push({type,key:e.key||null,trusted:e.isTrusted,id:target.id||null,
                              tag:target.tagName,slot:target.dataset?.slotLabel||null,card:target.dataset?.kind||null,
                              cardId:target.dataset?.id||null});
                          },true);''')
                        context.tracing.start(screenshots=True, snapshots=True, sources=True)
                        page = context.new_page()
                        page.on('pageerror', lambda error: errors.append(str(error)))
                        page.on('dialog', lambda dialog: (errors.append('Unexpected dialog: '+dialog.type+': '+dialog.message), dialog.dismiss()))
                        def capture(request):
                            if urlsplit(request.url).path not in ('/api', '/runtime'):
                                return
                            try:
                                response = request.response()
                                entry = {'time': stamp(), 'phase': phase, 'method': request.method, 'url': request.url,
                                         'request_body': request.post_data, 'http_status': response.status,
                                         'response_headers': response.all_headers(), 'response_body': response.body().decode('utf-8')}
                                with (case_out / 'http-raw.jsonl').open('a') as f:
                                    f.write(json.dumps(entry, ensure_ascii=False)+'\n')
                            except Exception:
                                capture_errors.append(traceback.format_exc())
                        page.on('requestfinished', capture)
                        try:
                            phase = kind + '-' + str(width)
                            response = page.goto(args.url, wait_until='domcontentloaded', timeout=30000)
                            assert response.status == 200
                            ready()
                            assert page.evaluate('oc.on===true')
                            if kind == 'beam':check_beam()
                            else:check_slots()
                            inputs = page.evaluate('window.__cssProbeInputs')
                            write(case_out/'browser-input-events.json',inputs)
                            assert any(e['type']=='dblclick' and e['card']=='space' and e['cardId']=='1' and e['trusted'] for e in inputs)
                            if kind == 'slots':
                                assert any(e['type']=='pointerdown' and e['slot']=='前牆' and e['trusted'] for e in inputs)
                                assert any(e['type']=='keydown' and e['key']=='Tab' and e['trusted'] for e in inputs)
                                assert any(e['type']=='keydown' and e['key']=='Enter' and e['slot']=='前牆' and e['trusted'] for e in inputs)
                            assert not errors and not capture_errors, [errors, capture_errors]
                            row['passed'] = True
                        except BaseException:
                            row.update(error=traceback.format_exc(),failed_phase=phase)
                            try:
                                snapshot('failed-state');write(case_out/'browser-input-events.json',page.evaluate('window.__cssProbeInputs'));page.screenshot(path=str(case_out/'failed.png'),full_page=True)
                            except Exception:row['failure_capture_error']=traceback.format_exc()
                            raise
                        finally:
                            active_error = sys.exc_info()[0] is not None
                            try:context.tracing.stop(path=str(case_out/'trace.zip'))
                            except BaseException:cleanup_errors.append(traceback.format_exc())
                            try:context.close()
                            except BaseException:cleanup_errors.append(traceback.format_exc())
                            if errors or capture_errors or cleanup_errors:row['passed']=False
                            row.update(finished=stamp(),page_errors=errors,network_capture_errors=capture_errors,cleanup_errors=cleanup_errors)
                            write(case_out/'result.json',row);write(out/'receipt.json',receipt)
                            context=page=None
                            if (errors or capture_errors or cleanup_errors) and not active_error:
                                raise RuntimeError('Case evidence/cleanup failure; see raw errors')
            finally:
                active_error = sys.exc_info()[0] is not None
                if browser is not None:
                    try:browser.close()
                    except BaseException:
                        receipt.setdefault('browser_cleanup_errors',[]).append(traceback.format_exc())
                        if not active_error:raise RuntimeError('Browser cleanup failed')
                    finally:browser=None
        receipt['after']=identity('after')
        for key in ('head','tree','status','dirty_diff_sha256','sources'):
            assert receipt['after'][key]==receipt['before'][key], 'Source changed during browser run: '+key
        for key in ('version','pid','session'):
            assert receipt['after']['runtime'][key]==receipt['before']['runtime'][key], 'Runtime changed: '+key
        receipt['exit_code']=0
    except BaseException:
        receipt.update(error=traceback.format_exc(),failed_phase=phase,exit_code=1)
    finally:
        receipt['finished']=stamp();write(out/'receipt.json',receipt)
    print(json.dumps({'out':str(out),'exit_code':receipt['exit_code'],'cases':[{'case':r['case'],'width':r['width'],'passed':r['passed']} for r in receipt['cases']]}))
    return receipt['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
