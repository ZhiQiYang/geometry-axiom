import ast,collections,hashlib,json,tarfile
from pathlib import Path
F='38da31bcac91db631e6325e40b228f8604810e82';M='1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599'
B=Path('/workspace/geo339-F38da-affected-terminal-collection-20261024');O=Path('/workspace/train337-canvas-peer-resume');checks=0;findings=[]
def ck(v,l):
 global checks
 checks+=1
 if not v:findings.append(l)
def sh(b):return hashlib.sha256(b).hexdigest()
def h(p):return sh(Path(p).read_bytes())
def j(p):return json.loads(Path(p).read_text())
p=j(B/'PACKAGE.json');s=j(B/'SUMMARY.json');iv=j(B/'RAW_INVENTORY.json');mapping={x['name']:x for x in iv['members']};paths={x['source_path'] for x in iv['members']}
ck(h(p['archive']['path'])==p['archive']['sha256']=='c2d2c75b39536d7e801cb31af2cc49d0de3aafd130a0a0cdd27b6701b8abc435','original archive pin')
ck(h(B/'RAW_INVENTORY.json')==p['inventory']['sha256']=='b2f45b29a4f1a644c8042f8c8718fe69bce88b4c3ea39ba4d35c08aacae1e2c8','original inventory pin')
ck(p['sourceSHA']==iv['sourceSHA']==s['sourceSHA']==F and len(mapping)==len(iv['members'])==1468,'sourceF and exact1468 originals')
ck(sum(x['bytes'] for x in iv['members'])==iv['logical_original_bytes'],'original logical byte sum')
with tarfile.open(p['archive']['path'],'r:gz') as t:
 ms=t.getmembers();ck(len(ms)==len({x.name for x in ms})==1469 and {x.name for x in ms}==set(mapping)|{'RAW_INVENTORY.json'},'exact1469 unique archive members')
 for m in ms:
  ck(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts,'safe regular '+m.name);data=t.extractfile(m).read()
  if m.name=='RAW_INVENTORY.json':ck(data==(B/'RAW_INVENTORY.json').read_bytes(),'embedded original inventory');continue
  x=mapping[m.name];ck(len(data)==x['bytes']==m.size and sh(data)==x['sha256'],'original tar bytes '+m.name);ck(data==Path(x['source_path']).read_bytes(),'unchanged actual original '+m.name)
roots=[Path('/workspace/geo339-F38da-source-materialization-20261024'),Path('/workspace/geo339-F38da-affected-formal-capture-20261024')]+[Path('/tmp/geo339-'+x+'-F38da31bc') for x in ('three-predicates','pure65','pure18','domain16','native43','native43-launch')]
allrows=[]
def capture(row):
 d=Path(row['directory']);ck(j(d/'result.json')==row and j(d/'request.json')['command']==row['command'],'actual original request/result '+str(d));ck(row['timeout_expired'] is False and row['ended_epoch']>=row['started_epoch'],'actual terminal original '+str(d))
 for stream in ('stdin','stdout','stderr'):
  raw=(d/(stream+'.bin')).read_bytes();ck(sh(raw)==row[stream+'_sha256'],'full original stream '+str(d/stream))
  if stream!='stdin':ck(len(raw)==row[stream+'_bytes'],'stream length '+str(d/stream))
for root in roots:
 rows=j(root/'subcommands.json');allrows.extend(rows)
 for row in rows:capture(row)
ck(len(allrows)==len(s['original_capture_rows'])==251 and len({x['directory'] for x in allrows})==251,'251 distinct original capture rows')
ck(collections.Counter(x['actual_process_returncode'] for x in allrows)=={0:248,1:3},'only three deliberate predicate process failures')
for index,row in enumerate(j(roots[0]/'subcommands.json')):ck(row['source_sha']==(M if index<4 else F),'materialization correct priorM/F original variants')
for row in allrows:
 if not row['directory'].startswith(str(roots[0])):ck(row['source_sha']==row['acceptance_sha']==F,'formal fixedF original binding '+row['directory'])
material=j(roots[0]/'RESULT.json');ck(material['exitCode']==0 and material['cleanFinalHEAD']==F and material['requiredPriorSHA']==M and material['originalTenCommandsComplete'] and not material['errors'],'actual reviewed ten-command source materialization')
outer=j(roots[1]/'RESULT.json');req=j('/workspace/geo339-F38da-startup-20261024/COMMANDS.json');ck(outer['exitCode']==0 and outer['completeFiveCommands'] and [x['command'] for x in outer['commands']]==req['launchOriginalCommands'],'actual exact five original CLI commands allzero')
groups={x:j(Path('/tmp/geo339-'+x+'-F38da31bc/receipt.json')) for x in ('pure65','pure18','domain16','native43')}
expected={'test_geometry_host_sources':45,'test_geometry_source_runtime':10,'test_geometry_kernel_runtime':10,'test_rectangular_python':9,'test_geometry_host_world':8,'test_geometry_kernel_compatibility':1,'test_domain_source_pins':16,'test_geometry_host_native':30,'test_geo261_default_native':13}
suite_rows=[]
for name,value in groups.items():
 ck(value['exitCode']==0 and not value['errors'] and bool(value['endedUTC']) and value['request']['sourceSHA']==F and value['sourceAfter']['head']==F and value['sourceAfter']['porcelain']=='','original group zero and closed cleanF '+name)
 suite_rows+=value['rows'];root=Path('/tmp/geo339-'+name+'-F38da31bc')
 for row in value['rows']:
  suite=row['suite'];rr=row['originalResult'];ck(row['originalProcessExit']==0 and row['timeout'] is False and row['executionSHA']==F,'original suite actual0 '+suite)
  ck(rr==j(root/suite/'result.json') and rr['total']==rr['run']==rr['passed']==row['expectedContract']['count']==expected[suite],'original exact method count '+suite)
  ck(all(rr[k]==0 for k in ('failed','skipped','explicit_skipped','unrun_skipped','blocked_by_error','expected_failed','extra_errors')) and rr['import_error'] is None and rr['failures']==[],'no hidden skip/error '+suite)
  matches=[x for x in allrows if x['command']==row['originalCommand']];ck(len(matches)==1 and matches[0]['actual_process_returncode']==0,'exact original unittest CLI distinct '+suite)
  text=(root/suite/'unittest.log').read_text();ck(('Ran '+str(expected[suite])+' test') in text and '\nOK\n' in text,'complete original unittest log '+suite)
ck(len(suite_rows)==9 and {x['suite'] for x in suite_rows}==set(expected) and sum(x['originalResult']['passed'] for x in suite_rows)==142,'exact nine modules142/142')
native=groups['native43'];nr=Path('/tmp/geo339-native43-F38da31bc');ck(native['buildOriginalProcessExit']==0 and native['buildTimeout'] is False and native['sourceAfter']['inputsEqualBefore'] and native['sourceAfter']['indexEqualBefore'],'actual native43 build and original inputs/index restoration')
ck((nr/'INPUTS_BEFORE.json').read_bytes()==(nr/'INPUTS_AFTER.json').read_bytes(),'original before/after input manifests byte equal')
pr=Path('/tmp/geo339-three-predicates-F38da31bc');proof=j(pr/'receipt.json');ck(proof['sourceSHA']==F and proof['exitCode']==0 and proof['proofAccepted'] and not proof['errors'] and proof['checkoutBefore']==proof['checkoutAfter'] and proof['checkoutAfter']['head']==F and proof['checkoutAfter']['status']=='','predicate original terminal and clean/restoredF')
tool=Path('/tmp/geo324-owner-20261024/preparation/run_face_predicate_proofs_v2.py');a=ast.parse(tool.read_text());cases=ast.literal_eval(next(n.value for n in a.body if isinstance(n,ast.Assign) and any(isinstance(k,ast.Name) and k.id=='CASES' for k in n.targets)))
inputs=j(pr/'tracked-inputs.json');ck(len(inputs)==37 and h(pr/'tracked-inputs.json')==proof['trackedInputs']['manifestSHA256'] and h(pr/'input-git-tree.bin')==proof['inputGitTreeSHA256'],'original37 tracked closure exact')
source_path='geometry-templates/woodworking/geometry_woodworking/model_sources.py'
for declared,row in zip(cases,proof['rows']):
 key,before,after,method,diagnostic=declared;ck(row['predicate']==key and row['test'].endswith('.'+method) and row['anchorCount']==1 and row['originalExitCodes']==[0,1,0] and row['byteRestored'] and row['proofAccepted'],'original declared predicate triplet '+key)
 root=pr/('isolated-'+key)
 for item in inputs:
  data=(root/item['path']).read_bytes();ck(len(data)==item['bytes'] and sh(data)==item['sha256'] and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==item['gitBlob'],'exact restored Git input '+key+'/'+item['path'])
 original=(root/source_path).read_bytes();ck(sh(original)==proof['sourceOriginalSHA256'] and original.count(before)==1 and sh(original.replace(before,after))==row['mutantSHA256'],'single original predicate withdrawal exact bytes '+key)
 ck((root/'tests/__init__.py').read_bytes()==b'','original empty synthetic package marker '+key)
 for phase,want in zip(row['phases'],(0,1,0)):
  c=phase['commandResult'];text=(Path(c['directory'])/'stderr.bin').read_bytes();ck(c in allrows and c['actual_process_returncode']==want and c['command'][-1]==row['test'] and phase['ranOneExistingMethod'] and b'Ran 1 test in ' in text,'actual original one named method '+key+'/'+phase['phase'])
  if want:
   ck(diagnostic in text and b'AssertionError:' in text and b'FAILED (failures=2)' in text and b'FAILED (errors=' not in text and phase['normalUnittestFailure'] and phase['originalDiagnosticObserved'],'specific product guard withdrawal failure rather than crash '+key)
  else:ck(b'\nOK\n' in text and phase['sourceSHA256']==proof['sourceOriginalSHA256'],'original baseline/restored pass '+key)
excluded=j(B/'EXCLUDED_ELF_PAYLOADS.json');ck(len(excluded)==2 and sum(x['bytes'] for x in excluded)==2091120,'two private native ELF exclusions only')
for x in excluded:
 f=Path(x['source_path']);side=j(f.with_name(f.name+'.fingerprint.json'));ck(f.read_bytes()[:4]==b'\x7fELF' and f.stat().st_size==x['bytes']==side['exe_size'] and h(f)==x['sha256']==side['exe_sha256'],'retained original ELF bytes and fingerprint '+f.name);ck(x['name'] not in mapping and str(f.with_name(f.name+'.fingerprint.json')) in paths,'only payload omitted '+f.name)
for root in roots:ck({str(x) for x in root.rglob('*') if x.is_file() or x.is_symlink()}<=paths|{x['source_path'] for x in excluded},'complete original namespace '+str(root))
producer=j('/workspace/geo339-F38da-terminal-collection-producer-20261024/RESULT.json');capture(producer);ck(producer['actual_process_returncode']==0,'collector actual0 independent from product gates')
report={'schema':'independent-geo339-F38da-original-affected-actual-peer/1','checks':checks,'exit_code':int(bool(findings)),'findings':findings,'source_sha':F,'archive_sha256':p['archive']['sha256'],'members':1469,'original_files':1468,'original_bytes':iv['logical_original_bytes'],'capture_rows':251,'actual_original_exits':{'0':248,'1':3},'modules':expected,'original_methods_total':142,'original_methods_passed':142,'original_skip':0,'predicate_triplets':{x['predicate']:x['originalExitCodes'] for x in proof['rows']},'limits':['Only specified nine importer modules and three original predicate proofs. Full project native, six browser jobs, ledger and architecture are not inferred.','Three withdraw phases exit1 through named original AssertionError diagnostics; raw underlying TypeError/AttributeError context is retained, not misclassified as an infrastructure crash.','The original #339 wrapper uses private binaries and original thresholds. No subject was rerun by this reviewer.','Two private ELF payloads are retained at original paths and fingerprinted; archive omits only their body.','Source materialization first four original Git captures bind prior M; formal captures bind F. No source relabeling.']};out=O/'GEO339_AFFECTED_ACTUAL_PACKAGE_PEER.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checks':checks,'exit_code':report['exit_code'],'findings':findings,'path':str(out),'sha256':h(out)},ensure_ascii=False));raise SystemExit(report['exit_code'])
