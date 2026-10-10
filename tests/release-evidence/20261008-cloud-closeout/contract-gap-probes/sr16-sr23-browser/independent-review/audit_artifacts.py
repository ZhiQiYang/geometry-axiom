#!/usr/bin/env python3
"""Read-only independent post-run artifact comparisons; launches no product."""
import copy
import hashlib
import json
from pathlib import Path
import zipfile
from urllib.parse import urlsplit

RAW = Path('/workspace/closure-evidence/sr16-sr23-browser-r1')
OUT = Path(__file__).resolve().parent
checks = []
def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def check(name, condition, detail=None):
    checks.append({'name':name, 'passed':bool(condition), 'detail':detail})
def native(snapshot, revision=True):
    result=copy.deepcopy({key:snapshot[key] for key in ('dump','objects','references','assembly-read')})
    if not revision:
        for key in ('dump','assembly-read'): result[key].pop('revision',None)
    return result
def payload(snapshot):
    return {key:snapshot['project'][key] for key in ('id','name','manifest','sources','models','assemblyDrafts','engineeringDrafts')}
def empty(snapshot):
    return (snapshot['dump']['text']=='' and not snapshot['canvasCards']
        and all(value==[] for key,value in snapshot['objects'].items() if key!='ok')
        and all(snapshot['references'][key]==[] for key in ('guides','grids','timbers','specs','datums'))
        and all(snapshot['assembly-read']['state'][key]==[] for key in ('rules','bindings','instances'))
        and all(snapshot['project'][key]==[] for key in ('sources','models','assemblyDrafts','engineeringDrafts')))

receipt=read(RAW/'receipt.json')
gate=read(Path('/workspace/closure-evidence/gates/sr16-sr23-browser-r1/receipt.json'))
check('script execution is the reviewed frozen bytes',sha(RAW/'executed-probe.py')==receipt['scriptSha256']=='b694cd73cdd53d50dff49eb907a3faea1a96834772f6a1b4cb891690512eda8c')
check('command and gate terminated successfully without timeout',receipt['exitCode']==gate['execution']['exitCode']==gate['gateExitCode']==0 and not gate['execution']['timedOut'] and not gate['execution']['interrupted'])
check('command log hash',sha(Path(gate['log']['path']))==gate['log']['sha256'])
check('identity endpoints clean exact candidate',all(receipt[side]['git']['head']=='d8642b2e684038cbb8e24aba057c44e7aac1b231' and receipt[side]['git']['status']=='' and receipt[side]['problems']==[] for side in ('before','after')) and receipt['identityDifferences']==[])
check('runtime same fresh version/session',receipt['before']['runtime']==receipt['after']['runtime'] and receipt['before']['runtime']['fresh'] and receipt['before']['runtime']['version']=='82b45ea9cf53c10b2c4fd6591ce0dd45d055a9d8f0e7e4fb5765eeaf64075200')
check('actual service child exe pinned at both ends',all(any(row['executable']=='/tmp/geometry-tests/bridge' and row['sha256']=='b76a6da590512722d6eda64cfc946392ccc2636f82ab187ef822c1e1606d68b5' for row in read(RAW/(side+'-live-children.json'))) for side in ('before','after')))
details=[]
for width in ('1400','390'):
    directory=RAW/width
    def snap(name):return read(directory/(name+'.json'))
    ids=read(directory/'authored-identities.json'); recs=ids['records']
    http=[json.loads(line) for line in (directory/'http-raw.jsonl').read_text().splitlines()]
    commands=[]
    for line,row in enumerate(http,1):
        try:
            body=json.loads(row['requestBody'] or '{}')
            cmd=body.get('cmd') if isinstance(body,dict) else None
        except ValueError:cmd=None
        if cmd:commands.append((line,cmd,row))
    ordering=[]
    for rec in recs:
        guide=next(x for x in commands if x[1]==f"line guide {rec['guide']} {rec['face']} v {rec['expression']}")
        direct=next(x for x in commands if x[1]==f"line place {rec['timber']} on {rec['face']} {rec['anchor']} {rec['selector']} +u +n")
        binding=next(x for x in commands if x[1].startswith(f"line preview grid-binding {rec['binding']} "))
        ordering.append({'face':rec['face'],'bindingHttpLine':binding[0],'guideHttpLine':guide[0],'directHttpLine':direct[0]})
        check(width+f' face{rec["face"]} formal guide/direct HTTP success',json.loads(guide[2]['responseBody'])['ok'] and json.loads(direct[2]['responseBody'])['ok'])
    edit=next(x for x in commands if x[1].startswith('line preview grid-system ') and 'u repeat 0 300' in x[1])
    check(width+' first reference creation precedes second binding then source edit',ordering[0]['bindingHttpLine']<ordering[0]['guideHttpLine']<ordering[0]['directHttpLine']<ordering[1]['bindingHttpLine']<ordering[1]['guideHttpLine']<ordering[1]['directHttpLine']<edit[0],ordering)
    first=snap('face1-refs-authored');both=snap('face2-refs-authored')
    check(width+' intermediate snapshots prove sequential ownership',len(first['objects']['gridBindings'])==1 and len(both['objects']['gridBindings'])==2 and recs[0]['anchor'] in first['dump']['text'] and recs[1]['anchor'] not in first['dump']['text'] and all(r['anchor'] in both['dump']['text'] for r in recs))
    bad=snap('sr16-native-preview')['preview'];ui=snap('sr16-ui-preview')
    check(width+' SR16 exact second component diagnostic and disabled Confirm',bad['valid'] is False and len(bad['violations'])==1 and bad['violations'][0]['timber']==recs[1]['timber'] and bad['violations'][0]['clause']=='R6/I5/I6' and bad['violations'][0]['actual']=='between 指名的兩端之間沒有合法跨距（被實體擋住，或兩端座標相同）' and ui['confirmDisabled'] is True and set(ui['bindings'])=={r['binding'] for r in recs},bad['violations'])
    check(width+' SR16 first timber stays legal while only second after is null',next(t for t in bad['timbers'] if t['id']==recs[0]['timber'])['after'] is not None and next(t for t in bad['timbers'] if t['id']==recs[1]['timber'])['after'] is None)
    unchanged=snap('sr16-before-preview')
    check(width+' SR16 full raw data including revision unchanged pending/cancel',all(native(snap(n))==native(unchanged) and snap(n)['history']==unchanged['history'] for n in ('sr16-pending','sr16-cancelled')))
    check(width+' positive Cancel full raw data and captured history unchanged',native(snap('sr23-cancelled'))==native(snap('sr23-before-preview')) and snap('sr23-cancelled')['history']==snap('sr23-before-preview')['history'])
    baseline=snap('before-source-edit');changed=snap('after-source-edit')
    check(width+' serialized change exactly two existing pitch literals',baseline['dump']['text'].count('u repeat 0 600 v repeat 0 400')==1 and changed['dump']['text']==baseline['dump']['text'].replace('u repeat 0 600 v repeat 0 400','u repeat 0 900 v repeat 0 600'))
    for rec in recs:
        oldg=next(g for g in baseline['references']['guides'] if g['id']==rec['guide']);newg=next(g for g in changed['references']['guides'] if g['id']==rec['guide'])
        oldt=next(t for t in baseline['references']['timbers'] if t['id']==rec['timber']);newt=next(t for t in changed['references']['timbers'] if t['id']==rec['timber'])
        check(width+f' face{rec["face"]} unchanged formal tuple both descendants move',oldg['expression']==newg['expression']==rec['expression'] and (oldg['off'],newg['off'])==(300,400) and oldt['definition']==newt['definition'] and oldt['definition']['anchor']==rec['anchor'] and (oldt['geometry']['centerline'],newt['geometry']['centerline'])==(400,500) and oldt['geometry']['length']==newt['geometry']['length']==rec['length'])
        q=snap('after-source-edit-face'+str(rec['face'])+'-query')
        check(width+f' face{rec["face"]} full cell and three literal line coordinates',q['bounds']==[100,200,1000,800] and {(r['axis'],r['innerIndex']):r['coordinate'] for r in q['lines']}=={('u',0):400,('u',1):700,('v',0):500})
        displayed=snap('after-face'+str(rec['face'])+'-rendered-lines')
        check(width+f' face{rec["face"]} actual display matches complete native lines',len(displayed)==3 and all(r['ref']['appliedGridId']==rec['grid'] and r['ref']['systemId']==ids['source'] for r in displayed) and sorted(json.dumps(r['segments']) for r in displayed)==sorted(json.dumps(r['segments']) for r in q['lines']))
    check(width+' one Undo/Redo complete native definitions and refs',native(snap('undone'),False)==native(baseline,False) and native(snap('redone'),False)==native(changed,False))
    before=snap('before-save');saved=snap('saved')
    archive=directory/'sr23-project.gcanvas'
    with zipfile.ZipFile(archive) as z:
        members=z.namelist();scene=z.read('world.scene');manifest=json.loads(z.read('manifest.json'))
    expect={'projectId':before['project']['id'],'name':before['project']['name'],'sources':[],'faces':[],
            'format':'geometry-canvas/11','sceneHash':hashlib.sha256(before['dump']['text'].encode()).hexdigest(),
            'requiredCapabilities':['grid-subdivision-rules/1'],'models':[],'faceProjections':[]}
    check(width+' downloaded ZIP complete independent bounded manifest and scene',sorted(members)==['manifest.json','world.scene'] and manifest==expect and scene==before['dump']['text'].encode() and sha(archive)==snap('result')['archiveSha256'])
    check(width+' Save leaves native and full project payload unchanged',native(saved,False)==native(before,False) and payload(saved)==payload(before))
    check(width+' real New, fresh-profile state and Open-Undo are all empty',all(empty(snap(n)) for n in ('new-empty','fresh-profile-empty','open-undone')))
    check(width+' fresh context distinct from saved context',saved['project']['id']!=snap('new-empty')['project']['id'] and saved['project']['id']!=snap('fresh-profile-empty')['project']['id'])
    check(width+' formal Open restores full native and project payload',native(snap('project-reopened'),False)==native(saved,False) and payload(snap('project-reopened'))==payload(saved))
    check(width+' post-Open Undo and Redo exact full payloads',native(snap('open-undone'),False)==native(snap('fresh-profile-empty'),False) and payload(snap('open-undone'))==payload(snap('fresh-profile-empty')) and native(snap('open-redone'),False)==native(snap('project-reopened'),False) and payload(snap('open-redone'))==payload(snap('project-reopened')))
    check(width+' real reset and upload confirm HTTP success',any(urlsplit(r['url']).path=='/upload' and r['requestBody']=='reset\n' and r['status']==200 and json.loads(r['responseBody'])['ok'] for r in http) and any(urlsplit(r['url']).path=='/upload/confirm' and r['phase']=='SR23-formal-open' and r['status']==200 and json.loads(r['responseBody'])['ok'] for r in http))
    inputs=read(directory/'inputs-first-browser.json');reopened=read(directory/'inputs-reopened-browser.json')
    # Programmatically dispatched change events may coexist; real entry clicks
    # and keyboard activity must independently be trusted.
    check(width+' Save/New/Open entry events genuinely trusted',all(any(e['type']=='click' and e['id']==key and e['trusted'] for e in rows) for key,rows in [('btnSaveProject',inputs),('btnNewProject',inputs),('btnOpenProject',reopened)]))
    result=snap('result')
    check(width+' cleanup included in terminal outcome',result['passed'] and not result['errors'] and not result['networkErrors'] and not result['cleanupErrors'] and not result.get('cleanupError'))
    details.append({'width':int(width),'sourceId':ids['source'],'records':recs,'httpSequence':ordering,'invalidSourcePreviewLine':edit[0],'manifest':manifest,'tracePrivateHashes':[{'file':p.name,'sha256':sha(p)} for p in sorted(directory.glob('trace-*.zip'))]})
report={'schema':'geometry-sr16-sr23-independent-artifact-audit/1','reviewer':'/root/remote_inventory',
        'rawRoot':str(RAW),'productExecutionByReviewer':False,'passed':all(c['passed'] for c in checks),
        'checks':checks,'widths':details,'rawFiles':[{'path':str(p.relative_to(RAW)),'sha256':sha(p)} for p in sorted(RAW.rglob('*')) if p.is_file()],
        'limits':['History object reference equality needs execution trace eval returns in addition to serialized snapshots; independently examined separately.',
                  'Actual archive format is /11 in both widths; source support for /13 is not an exercised /13 result.',
                  'Actual SR16 refusal is R6/I5/I6 on the second timber; do not relabel it an I25a/CELL_SCOPE diagnostic.',
                  'Synthetic fixture, Chromium viewport 390, explicit download fallback; no physical-phone/IME/native-save-dialog or service-restart claim.']}
(OUT/'artifact-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'failed':[c for c in checks if not c['passed']],'comparisons':len(checks)},ensure_ascii=False))
