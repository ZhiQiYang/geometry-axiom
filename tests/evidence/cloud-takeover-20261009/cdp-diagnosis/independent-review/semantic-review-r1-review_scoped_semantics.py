"""Read existing bytes only. Independent actor verification of seven scoped gates.

Does not execute a browser, mutate source/tests/services, or infer a full pass.
"""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

BASE = Path('<original-evidence-root>/after-known-four-cb8d4e7-20261009')
OUT = Path(__file__).resolve().parent
HEAD = 'cb8d4e70d1659458017658d52139e2843cc5ba72'
REPO = Path('<takeover-repository-root>')
A0 = 'boundary 731 outline 0,0 4000,0 4000,3000 0,3000 hole 3000,1000 3500,1000 3500,1500 3000,1500'
A1 = 'boundary 731 outline 0,0 4200,0 4200,3000 0,3000 hole 3000,1000 3500,1000 3500,1500 3000,1500'
AREJECT = 'boundary 731 outline 0,0 2000,0 2000,3000 0,3000 hole 3000,1000 3500,1000 3500,1500 3000,1500'
B0 = 'boundary 732 outline 0,0 4000,0 4000,3000 0,3000'
B1 = 'boundary 732 outline 200,100 4000,100 4000,3000 200,3000'
B2 = 'boundary 732 outline 300,200 4000,200 4000,3000 300,3000'
BH = B0 + ' hole 100,100 400,100 400,400 100,400'
CHECKS = []
OBSERVED_FILES = {}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def raw(path):
    path = Path(path)
    data = path.read_bytes()
    OBSERVED_FILES[str(path)] = {'sha256':sha(data), 'bytes':len(data)}
    return data


def load(path):
    return json.loads(raw(path))


def check(condition, label):
    CHECKS.append({'label':label, 'passed':condition is True})


def fixed_replace(before, old, new, label):
    check(before.splitlines().count(old) == 1, label + ' exact unique initial line')
    return before.replace(old, new, 1)


def network(trace):
    data = raw(trace)
    rows = []
    with zipfile.ZipFile(trace) as z:
        for line in z.read('trace.network').decode().splitlines():
            r = json.loads(line).get('snapshot', {})
            req = r.get('request', {})
            if req.get('method') != 'POST' or not req.get('url', '').endswith('/api'):
                continue
            p = req.get('postData', {})
            request_bytes = z.read('resources/' + p['_sha1']) if p.get('_sha1') else p.get('text', '').encode()
            request = json.loads(request_bytes)
            resource = r.get('response', {}).get('content', {}).get('_sha1')
            if not resource:
                continue
            response_bytes = z.read('resources/' + resource)
            rows.append({'cmd':request.get('cmd'), 'reply':json.loads(response_bytes),
                         'responseResource':resource, 'responseSha256':sha(response_bytes),
                         'started':r['startedDateTime'], 'status':r['response']['status']})
    return sorted(rows, key=lambda r:r['started'])


def audit_settled(d, label, keys):
    for key in keys:
        check(all(r['phase'] == 'settled' for r in d['audit'][key]), label + ' ' + key + ' callbacks terminal')


def real_gate(d, trace_rows, label, command):
    gate = d['audit']['gate']
    check(gate['command'] == command, label + ' exact native command')
    check(gate['phase'] in ['released','returned'], label + ' held response released/returned')
    matches = [r for r in trace_rows if r['cmd'] == command]
    check(bool(matches), label + ' command exists in raw network trace')
    check(any(r['reply'] == gate['nativeReply'] and r['status'] == 200 for r in matches), label + ' held payload equals actual network response bytes')


def scene(directory, name, stage):
    return raw(directory / f'{name}-world-{stage}.scene').decode()


def replacement(directory, rows):
    for d in rows:
        name, mode = d['name'], d['mode']
        trace = network(directory / (name + '-trace.zip'))
        dumps = [r['reply']['text'] for r in trace if r['cmd'] == 'dump']
        check(len(dumps) >= 2, name + ' raw pre/post dumps available')
        before, after = dumps[-2:]
        wanted = fixed_replace(before, A0, A1, name) if mode == 'success-sibling' else before
        check(after == wanted, name + ' exact complete World bytes')
        real_gate(d, trace, name, 'line ' + (A1 if mode == 'success-sibling' else AREJECT))
        check(d['audit']['gate']['nativeReply']['ok'] is (mode == 'success-sibling'), name + ' genuine native success/refusal')
        if mode == 'success-sibling':
            check(d['after']['input'] == {'value':'4200','model':'4200'}, name + ' committed model and field')
            check(d['after']['sibling'] == {'value':'4242','model':'3000'}, name + ' newer sibling kept unsent')
        else:
            wanted_field = '4000' if mode == 'replacement-rejected-value' else '5151'
            check(d['after']['input'] == {'value':wanted_field,'model':'4000'}, name + ' rejection reconciliation/new input preserved')
            check(d['after']['sibling'] == {'value':'3000','model':'3000'}, name + ' sibling model unchanged')
        if mode.startswith('replacement'):
            check(d['before']['originalConnected'] is False, name + ' original DOM actually replaced before release')
        if mode != 'replacement-rejected-value':
            check(d['after']['focus'] == d['before']['focus'], name + ' newer input focus retained')
        changes = d['audit']['changes']
        check(bool(changes) and changes[0]['trusted'] is True and changes[0]['value'] == ('4200' if mode == 'success-sibling' else '2000'), name + ' original trusted change')
        check(all(r['trusted'] is True for r in changes), name + ' all observed changes trusted')
        audit_settled(d, name, ['changes','draws'])


def cross_b(directory, rows):
    for d in rows:
        name = d['name']
        before = scene(directory,name,'before')
        expected = fixed_replace(before,A0,A1,name)
        check(scene(directory,name,'expected') == expected, name + ' expected artifact equals independent fixed replacement')
        if d['mode'] == 'held-success-to-B':
            for stage in ['gate','B-ready','released']:
                check(scene(directory,name,stage) == expected,name + ' World ' + stage)
            # Full recorded snapshot is stricter than the author's selected fields.
            check(d['beforeB'] == d['afterB'], name + ' entire recorded B ownership/model/DOM/status snapshot unchanged')
            b = d['beforeB']
            check(b['editBid'] == 732 and b['workSurf'] == '732' and b['tool'] == 'edit' and b['handles'] > 0 and b['editDrag'] is None, name + ' B active editor established')
            route = [r for r in d['audit']['navigation'] if r.get('id') in ['workspaceBackButton','btnObj','workSurf'] or r.get('tool') == 'edit']
            wanted = [('click','btnObj'),('change','workSurf'),('click',None)]
            if d['scope'] == 'face':wanted.insert(0,('click','workspaceBackButton'))
            check([(r['type'],r.get('id')) for r in route] == wanted and all(r['trusted'] for r in route), name + ' actual trusted navigation route')
            check(next(r for r in route if r.get('id') == 'workSurf')['value'] == '732',name + ' actual B selection')
        else:
            check(scene(directory,name,'completed') == expected, name + ' success control exact World')
            check(d['inputAfter'] == {'value':'4200','model':'4200','connected':True,'visible':True}, name + ' success control displayed model')
        trace = network(directory/(name+'-trace.zip'))
        real_gate(d,trace,name,'line '+A1)
        changes = d['audit']['changes']
        check(len(changes) == 1 and changes[0]['trusted'] is True and changes[0]['value'] == '4200',name + ' one trusted A submission')
        check(d['nativeReply'] == {'ok':True},name + ' genuine A successful native commit')
        audit_settled(d,name,['changes','draws'])


def held(directory, rows, projection=False):
    for d in rows:
        name = d['name']
        check(d['before'] == d['after'],name + ' complete recorded B snapshot preserved')
        b = d['before']
        check(b['editBid'] == 712 and b['tool'] == 'edit' and b['handles'] > 0 and b['groups'] > 0,name + ' B handles established')
        trace = network(directory/(name+'-trace.zip'))
        dumps = [r['reply']['text'] for r in trace if r['cmd'] == 'dump']
        check(len(dumps) >= 2 and dumps[-2] == dumps[-1],name + ' exact World trace response bytes unchanged')
        cmd = d['audit']['gate']['command']
        check(cmd == 'proj 0 0 0 711' if projection else cmd.startswith('bhit 711 0 0 '),name + ' original A query')
        real_gate(d,trace,name,cmd)
        audit_settled(d,name,['draws','changes'] if projection else ['draws','downs','ups'])
        if not projection:
            downs, ups = d['audit']['downs'], d['audit']['ups']
            check(len(downs) == len(ups) == 1 and downs[0]['trusted'] is True and ups[0]['trusted'] is True,name + ' one real pointer down and up')
            check(d['before']['editDrag'] is None and d['after']['editDrag'] is None,name + ' old drag does not revive')
            check([r['type'] for r in d['audit']['pointers']] == ['pointerdown','pointerup'] and all(r['trusted'] for r in d['audit']['pointers']),name + ' trusted pointer events')
        else:
            check('drawEditHandles' in d['audit']['gate']['stack'],name + ' retained original held-proj regression')


def complete_b(directory, d, before, old_line=B0, new_line=B1):
    name = d['name']
    expected = fixed_replace(before,old_line,new_line,name)
    check(scene(directory,name,'B-live-after-move') == before,name + ' B preview did not mutate World')
    check(scene(directory,name,'B-finished-expected') == expected,name + ' B expected artifact matches independent fixed change')
    check(scene(directory,name,'B-finished') == expected,name + ' B actual completion exact full World')
    draft = d['BCompletion']['draftState']
    if new_line == BH:
        check(draft['rectStart'] == {'u':100,'v':100} and draft['tool'] == 'hole',name + ' B hole draft active')
    else:
        uv = [[300,200],[4000,200],[4000,3000],[300,3000]] if new_line == B2 else [[200,100],[4000,100],[4000,3000],[200,3000]]
        check(draft['editBid'] == 732 and draft['editDrag']['bid'] == 732 and draft['editDrag']['loops'][0]['verts'] == uv,name + ' fixed intended B draft')


def formal_race(directory, rows):
    for d in rows:
        name, mode, audit = d['name'],d['mode'],d['audit']
        trace = network(directory/(name+'-trace.zip'))
        if mode == 'zoom':
            check(scene(directory,name,'before-zoom') == scene(directory,name,'after-zoom'),name + ' exact World unchanged')
            check(sum(r['type'] == 'click' and r['id'] == 'btnZoom' and r['trusted'] is True for r in audit['events']) == 1,name + ' actual one trusted zoom click')
            check(all(abs(d['after'][k]-d['expectedFit'][k]) < 1e-7 for k in ['zoom','panX','panY']),name + ' genuine fit effect')
            check(any(abs(d['after'][k]-d['before'][k]) > 1e-7 for k in ['zoom','panX','panY']),name + ' normal click was not swallowed')
            check(d['after']['focus'] is None and d['after']['selection'] == d['before']['selection'] and d['after']['consumed'] is None and d['after']['opening'] is False,name + ' zoom did not open workspace')
            continue
        gate = audit['gate']
        check(gate['nativeReply']['ok'] is True and not gate['nativeReply'].get('preview'),name + ' actual successful native response')
        real_gate(d,trace,name,gate['command'])
        audit_settled(d,name,['downs','moves','ups','draws','changes'])
        check(all(r['trusted'] is True for k in ['downs','moves','ups','changes'] for r in audit[k]),name + ' all recorded input callbacks trusted')
        if mode in ['same-edit-up','bhit-active-B']:
            original = scene(directory,name,'before')
            check(d['before'] == d['after'],name + ' entire owner/gesture/model/DOM snapshot unchanged')
            for stage in ['before-release','released']:
                check(scene(directory,name,stage) == original,name + ' exact World '+stage)
            check(gate['command'].startswith('bhit 731 0 0 '),name + ' A bhit original query')
            check(len(audit['downs']) == len(audit['ups']) == (2 if mode == 'bhit-active-B' else 1),name + ' exact gesture callback census')
            if mode == 'bhit-active-B':
                check(d['before']['editBid'] == 732 and d['before']['editDrag']['bid'] == 732,name + ' newer B gesture present during stale A release')
                complete_b(directory,d,original)
            else:
                check(d['before']['editDrag'] is None and d['after']['editDrag'] is None,name + ' early up cannot resurrect A')
        elif mode.startswith('cross-B-'):
            original = scene(directory,name,'before')
            expected = fixed_replace(original,A0,A1,name)
            for stage in ['A-expected','A-held','B-live','A-released']:
                check(scene(directory,name,stage) == expected,name + ' exact A World '+stage)
            check(d['beforeB'] == d['afterB'],name + ' entire live B owner/gesture/model/DOM snapshot unchanged')
            changes = audit['changes']
            check(len(changes) == 1 and changes[0]['trusted'] is True and changes[0]['value'] == '4200',name + ' one trusted A submission')
            check(gate['command'] == 'line '+A1,name + ' fixed A commit')
            if mode.endswith('hole'):
                check(d['beforeB']['rectStart'] == {'u':100,'v':100} and d['beforeB']['tool'] == 'hole',name + ' B live hole during A release')
                complete_b(directory,d,expected,new_line=BH)
            else:
                check(d['beforeB']['editDrag']['bid'] == 732,name + ' B live drag during A release')
                complete_b(directory,d,expected)
        elif mode in ['pointercancel','lostcapture']:
            check(d['before'] == d['after'] and d['before']['editDrag'] is None and d['before']['rectStart'] is None,name + ' cancellation state preserved')
            check(scene(directory,name,'before') == scene(directory,name,'released'),name + ' cancellation exact World unchanged')
            etype = 'pointercancel' if mode == 'pointercancel' else 'lostpointercapture'
            events = [r for r in audit['events'] if r['type'] == etype and r['id'] == 'cv']
            check(bool(events) and all(r['trusted'] is True for r in events),name + ' actual UA cancellation event')
            check(any(r['type'] == 'gotpointercapture' and r['id'] == 'cv' and r['trusted'] is True and r['pointerId'] == events[-1]['pointerId'] for r in audit['events']),name + ' real captured pointer before cancellation')
        elif mode == 'old-up-new-gesture':
            original = scene(directory,name,'before')
            first = fixed_replace(original,B0,B1,name)
            for stage in ['first-B-expected','old-up-held','old-up-released']:
                check(scene(directory,name,stage) == first,name + ' exact first B World '+stage)
            check(d['beforeNewGesture'] == d['afterOldUp'],name + ' old up preserved entire newer same-editor gesture snapshot')
            check(d['beforeNewGesture']['editDrag']['bid'] == 732,name + ' newer same-editor gesture exists')
            check(gate['command'] == 'line '+B1,name + ' first B up exact native command')
            check(len(audit['downs']) == len(audit['ups']) == 2,name + ' two real complete gestures')
            complete_b(directory,d,first,old_line=B1,new_line=B2)
        else:
            check(False,name+' unknown mode')


def card(directory, receipt):
    for d in receipt['cases']:
        name = d['case']+'-'+str(d['width'])
        path = directory/name
        gesture = load(path/'space-entry-gesture.json')
        downs = gesture['downs']
        check(len(downs) == 2 and all(e['trusted'] is True and e['button'] == 0 for e in downs),name+' two real primary pointerdowns')
        first, second = downs
        check(first['card'] == 'space' and first['cardId'] == '1',name+' first hit original card')
        check(second['region'] is True and second['focus'] is None and second['selection'] == [{'kind':'space','id':1}] and second['selected'] == {'kind':'space','id':1},name+' second down recognized selection despite reflow')
        check(first['context'] == second['context'] and bool(first['context']) and first['pointerId'] == second['pointerId'] and first['pointerType'] == second['pointerType'] == 'mouse',name+' same context and real pointer')
        check(0 <= second['timeStamp']-first['timeStamp'] <= 450 and all(abs(second[k]-first[k]) <= 6 for k in ['x','y']),name+' two same-location clicks inside bounded doubleclick time')
        check(second['id'] != 'btnZoom',name+' second down not zoom button')
        check(gesture['reached'] == {'focus':{'t':'space','id':1},'workspaceHidden':False},name+' entered actual workspace')
        before = load(path/'before.json')
        if d['case'] == 'beam':
            style = load(path/'computed-style.json')
            check(style['beamCount'] == style['iconCount'] == 1 and style['listLabel'] == '樑 1',name+' one beam and label')
            check(style['stroke'] == style['color'] == 'rgb(72, 105, 135)' and style['fill'] == style['background'] == 'rgb(237, 243, 248)',name+' adopted beam colors agree between geometry/icon')
            check(style['display'] != 'none' and style['visibility'] == 'visible' and all(style[k]['width'] > 0 and style[k]['height'] > 0 for k in ['beamRect','iconRect']),name+' rendered beam/icon visible')
            check(load(path/'after.json') == before,name+' full native snapshot unchanged')
            check(raw(path/'before.scene') == raw(path/'after.scene'),name+' exact saved World bytes unchanged')
        else:
            slots = load(path/'initial-nonhover-slots.json')
            check(len(slots) == 4,name+' four missing wall slots')
            check(all(r['aria'] == '放置'+r['label'] and r['text'] == '＋放置' and r['actionDisplay'] != 'none' and r['idleDisplay'] == 'none' and r['visibility'] == 'visible' and r['rect']['width'] > 0 and r['rect']['height'] > 0 and not r['hover'] and not r['focus'] for r in slots),name+' all slot labels visible without hover/focus')
            for how in ['pointer','keyboard']:
                state = load(path/(how+'-opened.json'))
                check(state['u'] == state['preset']['u'] == '+x' and state['v'] == state['preset']['v'] == '+z' and state['pending'] == {'space':1,'bid':3,'label':'前牆','presetName':'y=0 牆'},name+' '+how+' existing preset opened')
                check(load(path/('after-'+how+'.json')) == before,name+' '+how+' full native snapshot unchanged')
                check(raw(path/'before.scene') == raw(path/('after-'+how+'.scene')),name+' '+how+' exact World bytes unchanged')
            events = load(path/'browser-input-events.json')
            check(any(e['type']=='pointerdown' and e['slot']=='前牆' and e['trusted'] is True for e in events),name+' actual trusted slot pointer')
            check(any(e['type']=='keydown' and e['key']=='Tab' and e['trusted'] is True for e in events) and any(e['type']=='keydown' and e['key']=='Enter' and e['slot']=='前牆' and e['trusted'] is True for e in events),name+' actual trusted Tab/Enter slot route')


def identities(gate, receipt):
    before, after = receipt['before'], receipt['after']
    for label, s in [('before',before),('after',after)]:
        check(s['git']['head'] == HEAD and s['git']['status'] == '',gate+' '+label+' exact clean tested HEAD')
        check(s['problems'] == [],gate+' '+label+' identity no problems')
        check(all(n['state'] == 'fresh' for n in s['native'].values()),gate+' '+label+' configured native freshness')
    check(before['git'] == after['git'] and before['sourceVersion'] == after['sourceVersion'],gate+' source identity unchanged')
    check(receipt['execution']['exitCode'] == 0 and not receipt['execution']['timedOut'] and not receipt['execution']['interrupted'],gate+' successful complete execution')
    check(receipt['executionVerified'] is True and receipt['problems'] == [],gate+' execution verification distinct from release approval')
    log = receipt['log']
    data = raw(log['path'])
    check(sha(data) == log['sha256'] and len(data) == log['bytes'],gate+' exact original log bytes')
    sources = before.get('sources',receipt.get('sourceSha256',{}))
    for name, digest in sources.items():
        data = subprocess.check_output(['git','-C',str(REPO),'show',HEAD+':'+name])
        check(sha(data) == digest,gate+' '+name+' recorded bytes match actual commit')
    if 'sources' in before:
        check(before['sources'] == after['sources'],gate+' all recorded sources stable')
        check(before['executionFiles'] == after['executionFiles'],gate+' recorded executor files stable')
        for path, digest in before['executionFiles'].items():
            check(sha(raw(path)) == digest,gate+' current retained executor bytes match recorded '+path)
        for label, s in [('before',before),('after',after)]:
            rt=s['runtime']
            check(rt['fresh'] is True and rt['version'] == s['sourceVersion'] and rt['root'] == str(REPO),gate+' '+label+' runtime version matches source')
            check(len(s['liveBridge']) == 1 and s['liveBridge'][0]['parent'] == rt['pid'] and s['liveBridge'][0]['exe'] == s['native']['bridge']['path'] and s['liveBridge'][0]['sha256'] == s['native']['bridge']['sha256'],gate+' '+label+' actual running child native identity')
        check(before['runtime'] == after['runtime'],gate+' runtime remained same process/session')
    else:
        owned = receipt['ownedFormalServer']
        check(bool(receipt['actualFormalNativeBindings']),gate+' owned formal server actual native binding captured')
        for binding in receipt['actualFormalNativeBindings']:
            rt = binding['runtime']
            bridges = binding['liveBridge']
            check(rt['fresh'] is True and rt['version'] == before['sourceVersion'] and rt['pid'] == owned['pid'],gate+' owned formal runtime identity')
            check(len(bridges) == 1 and bridges[0]['parent'] == rt['pid'] and bridges[0]['sha256'] == before['native']['bridge']['sha256'],gate+' owned formal actual child native identity')


def main():
    reviewed=[]
    executor_index=load(BASE/'scoped-executor-byte-review.json')
    original_index=load(BASE/'scoped-independent-byte-review.json')
    check({k:v for k,v in executor_index.items() if k != 'reviewerRole'} == original_index,'old named independent index equals executor index except role')
    for gate, expected_count, verify in [('card-r3',4,card),('replacement',16,replacement),('cross-b',8,cross_b),('held-bhit',2,held),('held-proj',2,lambda p,r:held(p,r,True)),('formal-race',20,formal_race),('formal-edge',38,None)]:
        start=len(CHECKS)
        receipt_path=BASE/(gate+'-gate')/'receipt.json'
        receipt=load(receipt_path)
        index=next(g for g in executor_index['gates'] if g['gate'] == gate+'-gate')
        check(sha(raw(receipt_path)) == index['receiptSha256'],gate+' original indexed receipt hash matches')
        identities(gate,receipt)
        if verify:
            census=receipt['probeCensus']
            rows=load(census['resultsPath'])
            check(sha(raw(census['resultsPath'])) == census['resultsSha256'],gate+' raw result bytes match receipt')
            cases=rows['cases'] if gate == 'card-r3' else rows
            check(len(cases) == expected_count == census['expectedCases'] == census['actualCases'] and census['completed'] is True,gate+' exact declared separate case census')
            check(all(r.get('ok',r.get('passed')) is True and not r.get('pageErrors',r.get('page_errors')) and not r.get('preconditionOrHarnessError') for r in cases),gate+' all cases no harness/page error')
            verify(BASE/(gate+'-artifacts'),rows)
        else:
            original=load(receipt['originalResult']['copyPath'])
            check(sha(raw(receipt['originalResult']['copyPath'])) == receipt['originalResult']['sha256'],gate+' retained original result exact bytes')
            check(original['passed'] == expected_count and original['failed'] == 0 and len(original['results']) == expected_count and all(r['ok'] is True for r in original['results']),gate+' original 38 named assertion records')
            text=raw(receipt['log']['path']).decode()
            passed=[line[5:] for line in text.splitlines() if line.startswith('PASS ')]
            check(passed == [r['name'] for r in original['results']],gate+' log agrees with every original assertion name/result')
            check('EDGE_RESULT {"passed":38,"failed":0,"completed":true}' in text and 'EDGE_FATAL ' not in text and '\nFAIL ' not in text,gate+' original completion and no fatal')
            names=[r['name'] for r in original['results']]
            for width in [1400,390]:
                check(sum(n.startswith(str(width)+'px ') for n in names) == 18,gate+' all 18 expected edge assertions at '+str(width))
                for scope in ['main','face']:
                    for retype in ['unchanged','620','100000001']:
                        check(any(n.startswith(f'{width}px {scope} {retype} rejection reconciles') for n in names),gate+' replacement generation case '+str(width)+' '+scope+' '+retype)
            check(names[-2:] == ['no uncaught browser exceptions','no browser console errors'],gate+' browser fatal/error controls')
        checks=CHECKS[start:]
        reviewed.append({'gate':gate,'testedSHA':HEAD,'dirty':False,'declaredCases':expected_count,'semanticChecks':len(checks),'semanticPassed':all(c['passed'] for c in checks),'failedChecks':[c['label'] for c in checks if not c['passed']], 'receipt':str(receipt_path),'receiptSha256':sha(raw(receipt_path)),'originalLog':receipt['log']})
    report={'actor':'/root/race_review','checkedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'testedSHA':HEAD,'dirty':False,'scope':'Read-only verification of seven separate existing scoped gates; no browser run, full CDP, Windows, golden, or release approval claim.',
      'independence':'Distinct from executor /root/evidence_harness. Reviewer authored the initial formal-race supplemental probe, so independent execution evidence review does not mean independent oracle authorship for that gate. Other six original gates were not authored by this actor.',
      'result':all(c['passed'] for c in CHECKS),'gates':reviewed,'checks':CHECKS,'observedFiles':OBSERVED_FILES,
      'limitations':['Formal EDGE logs/name/census/source assertions checked, but its result only retains per-assertion booleans, not successful field/model value snapshots. External replacement/Cross-B traces carry independent raw World checks.','held-bhit/proj old original observations preserve token/counts and exact World; old probes do not retain full handle-shape DOM or active-B gestures. Formal-race supplies richer ownership/DOM/live-work checks.','formal-edge receipt records Node command and harness source bytes, not actual Node executable/version/hash. Executor confirmed absent; current Node must not be rebound to historical run. Configured and actual child native executable identities are complete.','The old scoped-independent-byte-review filename does not establish independence: it was executor-produced, identical to scoped-executor-byte-review except reviewerRole. Original retained.','No scoped pass totals summed into full suite. No Windows raw originals or golden comparison reviewed.'],
      'script':{'path':str(Path(__file__).resolve()),'sha256':sha(raw(Path(__file__).resolve()))}}
    report_path=OUT/'independent-actor-scoped-semantics-review.json'
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for r in reviewed:print(r['gate'],r['declaredCases'],'cases;',r['semanticChecks'],'checks;', 'PASS' if r['semanticPassed'] else 'FAIL',r['failedChecks'])
    print('report',report_path,sha(report_path.read_bytes()))
    return 0 if report['result'] else 1


if __name__ == '__main__':
    sys.exit(main())
