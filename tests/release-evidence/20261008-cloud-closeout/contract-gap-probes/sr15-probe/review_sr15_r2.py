#!/usr/bin/env python3
"""Independent read-only review of already-recorded SR15 r2 evidence."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
E=Path('/workspace/closure-evidence'); R=Path('/workspace/geometry-axiom')
raw=E/'sr15-parameter-anchor-r2'; prepared=E/'inventory/final-contract-mapping/sr15-probe'
result=json.loads((raw/'result.json').read_text()); snapshots=result['snapshots']
wire=[json.loads(line) for line in (raw/'wire.jsonl').read_text().splitlines()]
responses=[json.loads(row['stdoutLine']) for row in wire]
receipt=json.loads((E/'gates/sr15-parameter-anchor-r2/receipt.json').read_text())
driver=json.loads((E/'integration/sr15-native-driver-r2.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert result['successful'] and result['testsRun']==1 and not result['failures'] and not result['errors']
assert len(result['checks'])==14 and all(x['ok'] for x in result['checks'])
assert result['bridgeCleanup']=={'exitCode':0,'forcedOwnedProcessStop':False}
assert result['bridge']['liveExeSHA256']==result['bridge']['sha256']=='b76a6da590512722d6eda64cfc946392ccc2636f82ab187ef822c1e1606d68b5'
for path,expected in result['sourceSHA256'].items():assert sha(path)==expected,path
assert sha(prepared/'sr15_probe.py')=='29bc34b4dec9cb9b434a16e50553b2dd9197f5487a02d29cb49857cdb7356338'
head='d8642b2e684038cbb8e24aba057c44e7aac1b231'
assert result['head']==result['headAfter']==head and result['dirtyBefore']==result['dirtyAfter']==''
assert driver['exit_code']==receipt['execution']['exitCode']==0
assert not receipt['execution']['timedOut'] and not receipt['execution']['interrupted'] and not receipt['problems']
for phase in ['before','after']:
    assert receipt[phase]['git']['head']==head and receipt[phase]['git']['status']==''
for old,new in [('parameter600','parameter900-preview-live'),('parameter600','parameter900-cancel'),('parameter-update-redo','nondivisible-parameter-refused'),('before-anchor-edit','anchor-preview-live'),('before-anchor-edit','anchor-cancel'),('binding-anchor-update-redo','invalid-anchor-refused')]:
    assert snapshots[old]==snapshots[new],(old,new)
for phase in ['parameter600','parameter900','anchor-third']:
    assert snapshots[phase]==snapshots[phase+'-after-readonly-queries']
for before,after,label in [('parameter600','parameter900','parameter-update'),('before-anchor-edit','anchor-third','binding-anchor-update')]:
    for desired,actual in [(before,label+'-undo'),(after,label+'-redo')]:
        assert snapshots[desired]['world']==snapshots[actual]['world']
        assert snapshots[desired]['definitionSHA256']==snapshots[actual]['definitionSHA256']
    assert snapshots[label+'-redo']['revision']>snapshots[label+'-undo']['revision']>snapshots[after]['revision']>snapshots[before]['revision']
preview_indices=[i for i,row in enumerate(wire) if row['command'].endswith('vertex-key 1 cell -2 1 anchor 1 3 1 2')]
assert len(preview_indices)==2
anchor_previews=[]
for i in preview_indices:
    pv=responses[i]['preview']; assert pv['valid']
    rows=pv['gridBindings']; assert len(rows)==2 and {r['id'] for r in rows}=={0,1}
    by={r['id']:r for r in rows}; live={r['id']:r for r in snapshots['before-anchor-edit']['world']['objects']['gridBindings']}
    assert by[0]['before']==by[0]['after']
    for identifier in [0,1]:assert {k:v for k,v in by[identifier]['before'].items() if k!='preview'}==live[identifier]
    old,new=by[1]['before'],by[1]['after']
    assert old['anchor']==[{'num':1,'den':2},{'num':1,'den':2}]
    assert new['anchor']==[{'num':1,'den':3},{'num':1,'den':2}]
    assert old['translation']==[1450,-400] and new['translation']==[1600,-400]
    assert old['translationExact']==['1450','-400'] and new['translationExact']==['1600','-400']
    assert old['preview']['axes']['v']==new['preview']['axes']['v']
    for p,coords in [(old['preview'],[550,1450]),(new['preview'],[700,1600])]:
        assert p['rect']==[100,200,2100,1800] and p['ok']
        lines=p['axes']['u']['lines']; assert [l['index'] for l in lines]==['-1','0']
        assert [l['coordinate'] for l in lines]==coords
        assert [l['segments'] for l in lines]==[[{'a':[x,200],'b':[x,1800]}] for x in coords]
    anchor_previews.append({'wireLine':i+1,'binding0CompleteBeforeAfterEqual':True,'binding1Anchors':[old['anchor'],new['anchor']],'binding1Translations':[old['translation'],new['translation']]})
phases={}
for phase,pitch,offsets in [('parameter600',600,[300,200]),('parameter900',900,[400,250]),('anchor-third',900,[400,400])]:
    world=snapshots[phase]['world']; owner=world['objects']['gridSystems'][0]
    assert owner['uDefinition']['step']==pitch and owner['uDefinition']['parameterRefs']['step']=={'kind':'parameter','parameterId':1,'fieldId':1}
    assert 'u repeat 0 param:1:1 v repeat 0 400' in world['dump']
    refs=world['references']; guides={g['id']:g for g in refs['guides']}
    assert [guides[i]['off'] for i in [9,29]]==offsets
    timbers={t['id']:t for t in refs['timbers']}
    for tid,y,length,tuple_ in [(3,400,540,'at-line rule 10 0 1 -2 1 v 0'),(23,600,240,'at-line rule 20 0 1 -2 2 v 0')]:
        t=timbers[tid]; assert t['geometry']['centerline']==y and t['geometry']['length']==length
        assert t['role']=='secondary' and t['definition']['anchor'].startswith(tuple_)
    phases[phase]={'pitch':pitch,'guideOffsets':offsets,'directCenterlines':[400,600],'directLengths':[540,240],'revision':snapshots[phase]['revision']}
bad_indices=[i for i,row in enumerate(wire) if row['command'].endswith('parameter-04.json')]
assert len(bad_indices)==1
bad=responses[bad_indices[0]]['preview']; assert not bad['valid'] and 'DIVISION_NOT_EXACT' in json.dumps(bad)
bad_anchor_indices=[i for i,row in enumerate(wire) if row['command'].endswith('anchor 4 3 1 2')]
assert len(bad_anchor_indices)==1
bad_anchor=responses[bad_anchor_indices[0]]; assert 'I37' in json.dumps(bad_anchor) and not bad_anchor.get('preview',{}).get('valid',True)
binding_src=(R/'geometry-web/grid_binding_bridge.inc').read_text()
assert 'for (size_t i=0;i<g_preview.before.grid_binding_count;++i)' in binding_src
assert 'json_grid_binding_preview();' in (R/'geometry-web/reference_bridge.inc').read_text()
review={'schema':'sr15-independent-result-review/1','reviewer':'/root/report_finalize (probe author /root/report_finalize/room_efficiency; executor root)','reviewedAt':datetime.now(timezone.utc).isoformat(),'scope':'Source, immutable recorded wire/snapshots and command receipts only. No product execution by reviewer.','testedHead':head,'scriptSHA256':sha(prepared/'sr15_probe.py'),'verdict':'bounded-native-pass','r1Disposition':'Keep exit1/raw/original executed source; failed assertion demanded changed-only binding transport, contrary to existing full-preview serializer. Not a product failure.','r2CorrectionBasis':{'ssot':'I37 公理層.md:793–803 and R32:1070–1087 require complete candidate validation and atomic re-evaluation; no unchanged-record omission requirement.','serializer':'geometry-web/grid_binding_bridge.inc:219–237 enumerates all before bindings and newly added bindings; reference_bridge.inc:123 invokes it.','change':'Exact {0,1}, each before matches live, complete A unchanged, B literal anchor/translation/main-line endpoints, unchanged V and identity fields. Not a superset-only relaxation.','portability':'Explicit --repo parsed before importing repository helpers.'},'execution':{'testMethods':1,'namedChecks':14,'methodChecksAreNotUserScenarios':True,'probeExit':receipt['execution']['exitCode'],'driverExit':driver['exit_code'],'nativeCleanup':result['bridgeCleanup'],'liveBinarySHA256':result['bridge']['liveExeSHA256'],'beforeAfterClean':True},'phases':phases,'anchorPreviews':anchor_previews,'rejectedParameter':{'value':902,'reason':'DIVISION_NOT_EXACT','wireLine':bad_indices[0]+1,'completeWorldAndRevisionPreserved':True},'rejectedAnchor':{'fraction':'4/3','reason':'D30/I37','wireLine':bad_anchor_indices[0]+1,'completeWorldAndRevisionPreserved':True},'limits':['Native-only, no browser/physical device/OS-flow claim.','Direct V-line positions remain unchanged by the U-only changes; their stable typed refs and legality are checked, not falsely reported as moved.','Recorded before/after source hashes and receipt identities do not prove absence of transient source changes.'],'inputs':[{'path':str(p),'sha256':sha(p)} for p in [raw/'result.json',raw/'wire.jsonl',raw/'bridge.stderr',prepared/'sr15_probe.py',prepared/'r1-to-r2.patch',E/'gates/sr15-parameter-anchor-r2/receipt.json',E/'integration/sr15-native-driver-r2.json',R/'geometry-web/grid_binding_bridge.inc',R/'geometry-web/reference_bridge.inc',R/'公理層.md']]}
output=E/'inventory/final-contract-mapping/sr15-r2-independent-review.json'
output.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'path':str(output),'sha256':sha(output),'verdict':review['verdict']}))
