from pathlib import Path
import json,hashlib,subprocess,datetime
O=Path('/tmp/geo348-command-boundary-diagnostic-preparation-20261025');O.mkdir(exist_ok=True)
S='0f695866c0ba12d2c70dfd7d40628d0fda0f905f';S73='73b21e64dce72f0d16ca29e18559c51815b9724d';F8='75a1e93811a52b69385cbdaf6a09d773ed9052ad';B=Path('/workspace/geo348-F0f695866-formal/H7/observed')
bindings={};gitrows=[];sources=[];cases=[]
def h(b):return hashlib.sha256(b).hexdigest()
def take(p,to=None):
 p=Path(p);b=p.read_bytes();bindings[str(p)]={'bytes':len(b),'sha256':h(b)}
 if to:
  dest=O/to;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 return b
def git(*args,repo='/workspace/geo348-F0f695866-source'):
 cmd=['git','-c','gc.auto=0','-c','maintenance.auto=false','-C',repo,*args];r=subprocess.run(cmd,capture_output=True)
 d=O/'git-r2'/f'{len(gitrows)+1:03d}';d.mkdir(parents=True);(d/'stdout').write_bytes(r.stdout);(d/'stderr').write_bytes(r.stderr)
 row={'argv':cmd,'exit':r.returncode,'stdout_sha256':h(r.stdout),'stderr_sha256':h(r.stderr)};(d/'RESULT.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');gitrows.append(row)
 assert r.returncode==0 and not r.stderr,args
 return r.stdout
paths=['tests/test_geo261_timber_capacity_host.py','tests/_bridge.py','tests/geo300_scene_generator.py','geometry-web/web_bridge.c','geometry-web/reference_bridge.inc','geometry-web/engineering_bridge.inc','geometry-core/references.inc','geometry-core/kernel/source.c','geometry-app/native/reference_sources.inc','geometry-templates/woodworking/native/contact_world.c','geometry-templates/woodworking/native/contact_sources.c','current_geometry.c']
for p in paths:
 raw=git('show',S+':'+p);dest=O/'source-F0f'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 local=Path('/workspace/geo348-F0f695866-source')/p;assert raw==local.read_bytes(),p
 sources.append({'path':p,'source_sha':S,'bytes':len(raw),'sha256':h(raw),'copy':str(dest.relative_to(O))})
def tree(rev,repo):
 raw=git('ls-tree','-r','-z',rev,'--',*paths,repo=repo)
 return {row.split(b'\t')[1].decode():row.split(b'\t')[0].decode() for row in raw.split(b'\0') if row}
t0=tree(S,'/workspace/geo348-F0f695866-source');t73=tree(S73,'/workspace/geo348-F73b21e64-source');t8=tree(F8,'/workspace/geometry-axiom')
changes=[p for p in paths if t0.get(p)!=t73.get(p)]
f8changes=[p for p in paths if t0.get(p)!=t8.get(p)]
for n in [79,80,81,82,83]:
 p=B/f'command-{n:06d}';row=json.loads(take(p/'receipt.json',f'original-command-{n}/receipt.json'))
 raw=take(p/'input.bin',f'original-command-{n}/input.bin');assert h(raw)==row['input']['sha256'] and len(raw)==row['input']['bytes']
 for stream in ['stdout','stderr']:
  f=p/(stream+'.bin')
  if row[stream]['captured']:
   b=take(f,f'original-command-{n}/{stream}.bin');assert h(b)==row[stream]['sha256'] and len(b)==row[stream]['bytes']
  else:assert not f.exists()
 cases.append({'number':n,'command_bytes_sha256':h(raw),'input':raw.decode(),'timeout':row['kwargs']['timeout'],'completed_process_returned':row['completed_process_returned'],'returncode':row['returncode'],'exception':row['exception'],'stdout':row['stdout'],'stderr':row['stderr'],'executable':row['executable'],'original_recorder_elapsed_seconds':row['ended_epoch']-row['started_epoch']})
assert cases[0]['input']==cases[4]['input'] and cases[0]['timeout']==cases[4]['timeout']==600
assert cases[0]['returncode'] is None and cases[4]['returncode'] is None
supp=Path('/workspace/geo348-F0f695866-formal-input-supplement-20261024/pass-001');manifest=json.loads(take(supp/'MANIFEST.json','original-fixture/MANIFEST.json'))
entry=manifest['files'][0];scene=take(supp/entry['retained'],'original-fixture/512-placed.scene');assert h(scene)==entry['sha256'] and len(scene)==entry['bytes']
words=[x.split() for x in scene.decode().splitlines() if x.strip() and not x.lstrip().startswith('#')]
fixture={'sha256':h(scene),'bytes':len(scene),'capture_scope':manifest['scope'],'captured_utc':manifest['captured_utc'],'statements':len(words),'timbers':sum(x[0]=='timber' for x in words),'places':sum(x[0]=='place' for x in words)}
observer=Path('/workspace/geo300-capacity512-h-pipe-capture-20261024/observe_bridge_bytes.py');obs=take(observer,'observer-original/observe_bridge_bytes.py');assert b'source = result if result is not None else failure' in obs and b"getattr(source, name, None)" in obs
snapshot=json.loads(take(B/'native-inputs/compiler-input-snapshots.json'))
compilers=[x['argv'] for x in snapshot if any(Path(a).name in ['web_bridge.c','source.c','contact_world.c','contact_sources.c'] for a in x['argv'])]
assert compilers and all('-O0' in x and '-O2' not in x for x in compilers)
phases=json.loads(take('/workspace/geo348-F73b21e64-formal/RESULT.json'))['phases']
facts={'schema':'geo348-timeout-command-boundary-static-preparation/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'author':'/root/r8_terminal_peer','read_only':True,'product_executed':False,'product_changed':False,'source_sha':S,'later_sentinel_source':S73,'current_train_F8':F8,'sources':sources,'selected_paths_changed_F0f_to_F73':changes,'selected_paths_changed_F0f_to_F8':f8changes,'cases':cases,'fixture':fixture,'original_selected_compiler_argv':compilers,'F73_actual_phase_labels':[x['label'] for x in phases],'observer_already_retains_exception_stream_attributes':True,'git_read_count':len(gitrows),'bindings':bindings,'limits':['Two original600-second failures bound only toF0f; null returncode and absent stdout/stderr do not identify a command.','Retained512fixture was copied during second timeout, after first timeout, not a preexecution snapshot of either batch.','Original ELF is hash-only in these receipts; no payload-preservation claim.','Source inspection supplies candidate costs and conditional complexity, not measured attribution.','F73 and F8 differ from F0f; old results cannot be relabeled as either source.','No tests or product process launched; diagnostic scheme remains unimplemented/unexecuted.']}
(O/'FACTS.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'facts_sha256':h((O/'FACTS.json').read_bytes()),'source_files':len(sources),'git_reads':len(gitrows),'fixture':fixture,'source_delta_F73':changes,'source_delta_F8':f8changes},ensure_ascii=False))
