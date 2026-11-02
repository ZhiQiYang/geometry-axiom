"""Normal own-branch publication, reusing existing c387 and lossless tar pattern."""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tarfile

R=Path('/tmp/geo324-faces-work-20261024');D=Path('/tmp/geo324-faces-prbody-work-20261024')
M='1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599';E='dcdf22655e0cf8ed47cd0b7f66d89f3a7beca694';DH='2aacfaf1ca49694446599158978ad47b776be83d'
BR='codex/geo324-faces-20261024';P='evidence/geo339-final-1f0ebd3e';ART='geometry-core/domain-decoupling'
CHECKS=Path('/tmp/geo339-light-gates-M1f0ebd3e-preflight');FOUR=Path('/tmp/geo339-architecture-four-M1f0ebd3e')
INDEX=Path('/tmp/geo339-M-light-checks-and-architecture-INDEX.json');TEMPLATE=Path('/tmp/geo339-light-check-publication-preparation/PR_BODY.template.md')
O=Path('/tmp/geo339-light-check-publication-20261024')
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');HPIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
H=lambda raw:hashlib.sha256(raw).hexdigest()
def save(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
ap=argparse.ArgumentParser();ap.add_argument('--peer',type=Path,required=True);ap.add_argument('--peer-sha256',required=True);ap.add_argument('--peer-extra',type=Path,action='append',default=[]);a=ap.parse_args()
assert not O.exists() and H(CAP.read_bytes())==HPIN
assert H(a.peer.read_bytes())==a.peer_sha256
peer=json.loads(a.peer.read_bytes());assert peer.get('findings')==[],'Peer final report must have no findings'
original=json.loads((CHECKS/'FOUR_ORIGINAL_CHECKS.json').read_bytes());fresh=json.loads((FOUR/'RESULT.json').read_bytes())
assert original['executionSHA']==M and {row['gate']:row['originalExit'] for row in original['rows']}=={'architecture-tests':0,'architecture-contract':0,'product-architecture-tests':0,'mutation-check':1}
assert fresh['sourceSHA']==M and fresh['originalGateExits']==[0,0,0] and fresh['manifestProofExits']==[0,1,0] and fresh['sourceCheckoutModified'] is False
assert H(INDEX.read_bytes())=='88e82ff782a09615c538ced03d407790ecc447e4ade10b65e41495337a8e8616'
index=json.loads(INDEX.read_bytes())
for item in index['members']:
    raw=Path(item['source']).read_bytes();assert len(raw)==item['bytes'] and H(raw)==item['sha256'],item['source']
O.mkdir();spec=importlib.util.spec_from_file_location('cap339publication',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None);env['PYTHONDONTWRITEBYTECODE']='1'
rec=cap.Recorder(O,env,M);context={str(R):M,str(D):DH}
report={'role':'Own source/evidence/body normal publication; original mutation-check RED retained','executionM':M,'sourceF':None,'evidenceE':None,'bodyD':None,'peerReport':str(a.peer),'peerSha256':a.peer_sha256,'errors':[],'exitCode':None}
def run(parts,cwd=R):
    return rec.run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*parts],cwd=cwd,timeout=180,source_sha=context[str(cwd)],source_variant='own339-normal-publication-only')
try:
    for repo,head in ((R,M),(D,DH)):
        _,actual,_=run(['rev-parse','HEAD'],repo);_,status,_=run(['status','--porcelain=v1','--untracked-files=all'],repo)
        assert actual.decode().strip()==head and not status,'Owner checkout changed'
    _,remote,_=run(['ls-remote','--exit-code','origin','refs/heads/'+BR]);assert remote.decode().split()[0]==E
    run(['switch',BR]);context[str(R)]=E
    _,head,_=run(['rev-parse','HEAD']);assert head.decode().strip()==E
    for name in ('product-architecture.json','product-architecture-scan.json','PRODUCT-ARCHITECTURE.md','product-architecture-receipt.json'):
        shutil.copyfile(FOUR/'new'/name,R/ART/name)
    run(['add','--',ART+'/product-architecture.json',ART+'/product-architecture-scan.json',ART+'/PRODUCT-ARCHITECTURE.md',ART+'/product-architecture-receipt.json'])
    _,staged,_=run(['diff','--cached','--name-only','-z'])
    assert set(staged.decode().strip('\0').split('\0'))=={ART+'/PRODUCT-ARCHITECTURE.md',ART+'/product-architecture-receipt.json'}
    run(['diff','--cached','--check']);run(['commit','-m','docs(geo339): refresh architecture receipts for face validation'])
    _,head,_=run(['rev-parse','HEAD']);F=head.decode().strip();context[str(R)]=F;report['sourceF']=F
    product_inputs=[item for item in json.loads((CHECKS/'M_INPUT_IDENTITY_BEFORE.json').read_bytes()) if item['productArchitectureInput']]
    assert len(product_inputs)==604
    for item in product_inputs:assert H((R/item['path']).read_bytes())==item['sha256']
    run(['push','origin','refs/heads/'+BR+':refs/heads/'+BR]);_,remote,_=run(['ls-remote','--exit-code','origin','refs/heads/'+BR]);assert remote.decode().split()[0]==F
    target=R/P;assert not target.exists();(target/'raw').mkdir(parents=True);(target/'receipts').mkdir();(target/'peer').mkdir();(target/'tools').mkdir()
    shutil.copyfile(Path(__file__),target/'tools'/Path(__file__).name)
    shutil.copyfile(TEMPLATE,target/'tools/PR_BODY.template.md')
    shutil.copyfile(a.peer,target/'peer/ACTUAL_PEER.json')
    for extra in a.peer_extra:shutil.copyfile(extra,target/'peer'/extra.name)
    originals={item['member']:Path(item['source']) for item in index['members']}
    archive=target/'raw/original-light-checks-and-architecture-M1f0ebd3e.tar.gz';members=[]
    with archive.open('wb') as out:
        with gzip.GzipFile(filename='',fileobj=out,mode='wb',mtime=0) as zipped:
            with tarfile.open(fileobj=zipped,mode='w|') as tar:
                for name,path in sorted(originals.items()):
                    raw=path.read_bytes();members.append({'archivePath':name,'originalPath':str(path),'bytes':len(raw),'sha256':H(raw)});tar.add(path,arcname=name,recursive=False)
    expected={item['archivePath']:item for item in members};seen=set()
    with tarfile.open(archive,'r:gz') as tar:
        for item in tar:
            assert item.isfile() and item.name in expected and item.name not in seen
            seen.add(item.name);raw=tar.extractfile(item).read();row=expected[item.name]
            assert len(raw)==row['bytes'] and H(raw)==row['sha256'] and raw==originals[item.name].read_bytes()
    assert seen==set(expected)
    save(target/'raw/RAW_INVENTORY.json',{'executionSHA':M,'files':members,'producerRoundtripVerified':True,'excludedOriginals':index['excludedPreservedPublicationCopies']})
    shutil.copyfile(INDEX,target/'ORIGINAL_RAW_INDEX.json')
    for name in ('FOUR_ORIGINAL_CHECKS.json','GENERIC_ACTUAL.json','FINDINGS.json'):shutil.copyfile(CHECKS/name,target/'receipts'/name)
    shutil.copyfile(FOUR/'RESULT.json',target/'receipts/architecture-four-result.json')
    previous=json.loads((R/'evidence/geo324-final-57b68014/CURRENT_STATE.json').read_bytes())
    rows=previous['rows'];actual_by_gate={item['gate']:item for item in original['rows']}
    for row in rows:
        if row['gate'] in actual_by_gate:
            actual=actual_by_gate[row['gate']];row.update(status='PASS' if actual['originalExit']==0 else 'RED',executionSHA=M,originalExitCode=actual['originalExit'],allowedSkip=None,
                receipt={'path':P+'/receipts/FOUR_ORIGINAL_CHECKS.json','sha256':H((CHECKS/'FOUR_ORIGINAL_CHECKS.json').read_bytes()),'jsonPointer':'/rows/'+str(original['rows'].index(actual))})
            command=actual.get('actualCommand')
            if command is None:command=json.loads((CHECKS/'GENERIC_ACTUAL.json').read_bytes())['actualCommand']
            row['originalCommand']=command['command']
    formal=['native-and-full-expected','canvas','assembly','documents','grid','space','timber','mutation-check','architecture-contract','architecture-tests','product-architecture-tests']
    selected=[row for row in rows if row['gate'] in formal]
    assert len(selected)==11
    counts={name:sum(row['status']==name for row in selected) for name in ('PASS','RED','UNRUN')}
    assert counts=={'PASS':3,'RED':1,'UNRUN':7}
    save(target/'CURRENT_STATE.json',{'schema':'geo339.original-current-state.v1','productSourceSHA':F,'executionM':M,'priorTargetedExecutionS':'57b680140da2c6b77ab0d362a72029d8d7c9334b','evidenceHead':None,'evidenceHeadResolution':'Containing normal evidence commit; exact SHA appears in PR_BODY.md and original publication receipt after commit.','formalIntegrationGateIds':formal,'formalIntegrationSummary':counts,'rows':rows,'MToFArchitecture604InputsEqual':True,'rootFinalLResultsInherited':False,'ledgerRegenerated':False})
    (target/'PROGRESS.md').write_text('# #339 原四項實跑與Linux四檔\n\n來源F：`'+F+'`；本輪executionM：`'+M+'`。三架構原exit0/0/0，generic205/product18；同Mmanifest反證0/1/0。原mutate--check1：123定義／110紀錄／107stale／3retired／13unrun，未重產帳本。11正式列＝3PASS／1RED／7UNRUN。原142與predicate仍S57，registry才M。\n\n完整原命令、公開stdout/stderr、環境、SHA、四檔schema、1119Git input與604完整inventory都封；manifest/scan bytes同，sourceF只report/receipt兩衍生diff且604inputs同M。215舊公開E副本同FSrename保，沒有刪raw。所有源只own branch，不碰rootlive/cache，未force push或合併PR。\n\n下一步：由root統排本線帳本全量與固定來源的完整native/expected、六browser；不繼承rootL結果，不把M改標F。\n')
    files={}
    for p in sorted(target.rglob('*')):
        if p.is_file():raw=p.read_bytes();files[p.relative_to(target).as_posix()]={'bytes':len(raw),'sha256':H(raw)}
    save(target/'PACKAGE_MANIFEST.json',{'schema':'geo339.original-light-checks-package.v1','sourceF':F,'executionM':M,'files':files,'manifestExcludesSelf':True,'formalIntegrationSummary':counts,'actualPeer':{'path':P+'/peer/ACTUAL_PEER.json','sha256':a.peer_sha256},'archiveSha256':H(archive.read_bytes()),'archiveBytes':archive.stat().st_size,'archiveRegularMembers':len(members)})
    run(['add','--force','--sparse','--',P]);_,staged,_=run(['diff','--cached','--name-only','-z']);assert all(path.decode().startswith(P+'/') for path in staged.split(b'\0') if path)
    run(['diff','--cached','--check','--',P+'/CURRENT_STATE.json',P+'/PROGRESS.md',P+'/PACKAGE_MANIFEST.json',P+'/tools/'+Path(__file__).name]);run(['commit','-m','test(geo339): archive original architecture and ledger checks'])
    _,head,_=run(['rev-parse','HEAD']);newE=head.decode().strip();context[str(R)]=newE;report['evidenceE']=newE
    run(['push','origin','refs/heads/'+BR+':refs/heads/'+BR]);_,remote,_=run(['ls-remote','--exit-code','origin','refs/heads/'+BR]);assert remote.decode().split()[0]==newE
    body=TEMPLATE.read_text();assert body.count('<PRODUCT_F>')==body.count('<EVIDENCE_E>')==1
    body=body.replace('<PRODUCT_F>',F).replace('<EVIDENCE_E>',newE);(D/'PR_BODY.md').write_text(body)
    run(['add','--force','--sparse','--','PR_BODY.md'],D);_,staged,_=run(['diff','--cached','--name-only','-z'],D);assert staged==b'PR_BODY.md\0'
    run(['diff','--cached','--check'],D);run(['commit','-m','docs(geo339): report original checks and remaining gates'],D)
    _,head,_=run(['rev-parse','HEAD'],D);newD=head.decode().strip();context[str(D)]=newD;report['bodyD']=newD
    run(['push','origin','refs/heads/'+BR+'-prbody:refs/heads/'+BR+'-prbody'],D);_,remote,_=run(['ls-remote','--exit-code','origin','refs/heads/'+BR+'-prbody'],D);assert remote.decode().split()[0]==newD
    report.update(bodySha256=H((D/'PR_BODY.md').read_bytes()),archiveSha256=H(archive.read_bytes()),archiveBytes=archive.stat().st_size,archiveRegularMembers=len(members),exitCode=0)
except BaseException as error:
    report['errors'].append(repr(error));report['exitCode']=1
finally:
    report['completedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['commandCount']=len(rec.rows);save(O/'receipt.json',report);print(json.dumps(report,ensure_ascii=False))
raise SystemExit(report['exitCode'])
