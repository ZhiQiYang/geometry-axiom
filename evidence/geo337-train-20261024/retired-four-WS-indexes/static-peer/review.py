from pathlib import Path
import json,hashlib,ast,datetime,stat
B=Path('/workspace/geo337-four-retired-WS-index-preservation-20261025');O=Path('/workspace/geo337-four-retired-WS-index-static-peer-20261025');O.mkdir(exist_ok=False);n=0
H=lambda b:hashlib.sha256(b).hexdigest()
def J(p):return json.loads(Path(p).read_bytes())
def ck(k,v):
 global n
 n+=1
 if not v:raise AssertionError(k)
prep=J(B/'PREPARATION.json');plan=J(B/'PLAN.json');req=J(B/'REQUEST.root-lease-false.json');code=(B/'archive_indexes.py').read_text();tree=ast.parse(code)
ck('exactpreppin',H((B/'PREPARATION.json').read_bytes())=='1d1dcedae2c0cf113d3ff715ebed39f09bf9c75d78596954c5ab696a9476b482')
for name,v in prep['files'].items():
 raw=(B/name).read_bytes();ck('fixedleaf',len(raw)==v['bytes']and H(raw)==v['sha256'])
ck('toolpin',prep['executor_sha256']==H(code.encode())=='b7e3f6c5c1f5ad18c1ea9db697c035d01a439991819ad160ae502374c15663ab')
ck('planpin',H((B/'PLAN.json').read_bytes())==req['plan_sha256']==prep['plan_sha256']=='24b2f5df655362bd2c2c6a9ea4c98e3d4bcabc384e80d8c46684e1ec7b2f872f')
ck('4ownroles',[s['role']for s in plan['subjects']]==['R5','R6','readingL','readerF9'])
roots=['/workspace/geo323-final-r5-source-20261024','/workspace/geo323-final-r6-source-20261024','/workspace/train337-L-reading-a-source','/workspace/geo337-F9-readers-actual-urce1nqh/source'];ck('4exactroots',[s['root']for s in plan['subjects']]==roots)
ck('independentgitdirs',len({tuple(s['gitdir_device_inode'])for s in plan['subjects']})==4)
ck('independentindex',len({(s['index_metadata']['dev'],s['index_metadata']['inode'])for s in plan['subjects']})==4)
ck('allocationbound',sum(s['index_metadata']['allocated']for s in plan['subjects'])==plan['index_allocated_total']==23400448)
ck('rawbytes',sum(s['index_metadata']['bytes']for s in plan['subjects'])==23386440)
originals=J(B/'inventory/subcommands.json');ck('16originals',len(originals)==16)
for row in originals:
 d=Path(row['directory']);ck('originalresult',J(d/'result.json')==row and row['actual_process_returncode']==0 and not row['timeout_expired'])
 for stream in ['stdout','stderr']:
  b=(d/(stream+'.bin')).read_bytes();ck('originalfullstream',H(b)==row[stream+'_sha256']and len(b)==row[stream+'_bytes'])
 ck('stdin',H((d/'stdin.bin').read_bytes())==row['stdin_sha256'])
 ck('optionalGitwritesoff',row['command'][:6]==['git','--no-optional-locks','-c','gc.auto=0','-c','maintenance.auto=false']and row['environment']['PYTHONOPTIMIZE']is None)
for s in plan['subjects']:
 m=s['index_metadata'];ck('regularprivateindex',stat.S_ISREG(m['mode']) and m['nlink']==1 and s['gitdir']==s['root']+'/.git' and s['index']==s['gitdir']+'/index')
 rows=s['original_commands'];ck('4pinnedGitrows',len(rows)==4 and all(x in originals for x in rows))
 outs=[(Path(x['directory'])/'stdout.bin').read_bytes()for x in rows]
 ck('head/staged/status/refs',outs[0].decode().strip()==s['head'] and outs[1]==b''and outs[2].hex()==s['git_status_hex']and H(outs[3])==s['git_refs_sha256'])
 if s['role']!='readerF9':ck('3clean',outs[2]==b'')
 else:ck('reader3Dretained',outs[2]==' D current_geometry.c\0 D geometry-guide/current_geometry-導讀.html\0 D geometry-guide/公理層-閱讀器.html\0'.encode())
 terminal=Path(s['terminal']['path']);b=terminal.read_bytes();j=json.loads(b);ck('terminalexact',H(b)==s['terminal']['sha256']and len(b)==s['terminal']['bytes']and j.get('source_sha',j.get('sha'))==s['head'])
 if s['role']in ('R5','R6'):ck('terminalclosedred',j['wrapper_exit']==1 and j['status'].startswith('完成'))
 elif s['role']=='readingL':ck('terminalclosed',j['passed']is True and bool(j['endedUTC']))
 else:ck('readerterminalclosed',j['exit']==0 and j['all_three_passed']is True and bool(j['ended_epoch']))
for k in ['root_four_sources_no_reuse_lease','root_no_active_consumers_lease','root_shared_shm_capacity_admitted']:ck('initialunbound',req[k]is False and k in code)
ck('peerexactpin',"peer['executor_sha256'] == h(Path(__file__).read_bytes())"in code and "not peer['blocking_findings']"in code)
ck('noremovalcalls',not any(isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr in {'unlink','remove','rmdir','rmtree','rename','replace','link'}for x in ast.walk(tree)))
for text in ['os.O_NOFOLLOW | os.O_NOATIME','root_shared_shm_capacity_admitted',"m['nlink'] == 1","not list(gitdir.glob('*.lock'))","not vals['staged']","vals['status'].hex() == s['git_status_hex']","h(vals['refs']) == s['git_refs_sha256']",'guard.consumer_check(ROOTS)','with gzip.open(destination','restored == body','os.fsync(stream.fileno())','syncdir(out); syncdir(out.parent)',"'remote_delivered':False","'removal_authorized_by_this_tool':False"]:ck('archiveguard '+text,text in code)
ck('fixedhelpers',H(Path('/workspace/clear_terminal_chrome_caches.py').read_bytes())=='c51b4da96fc8ce88043484d3072a870fd725a18b00e6288e12144c399069e847' and H(Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py').read_bytes())=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762')
report={'schema':'geo337-four-retired-private-index-archive-static-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':0,'checks':n,'executor_sha256':H(code.encode()),'plan_sha256':H((B/'PLAN.json').read_bytes()),'preparation_sha256':H((B/'PREPARATION.json').read_bytes()),'blocking_findings':[],'source_roots':roots,'index_regular_bytes':23386440,'index_allocated_bytes':23400448,'original_inventory_commands':16,'scope':'archive-only; no index removal/restore executed or authorized by this peer','limits':['Full10KB executor/staticAST and16 originalGitraw/pins reviewed; no liveindex/source payload scan, no newGit/process scan, no SHM operation or execution.','Exact4physical privateindex paths,nlink1,inodes,HEAD/staged/status/refs/terminal pins guarded before/perfile/after; reader historical3D retained withoutreset. Alloriginal indexes remain in place.','Originalc51 process guard records inaccessibleproc fields and only proves accessible matches absent; root no-consumer/no-reuse lease and freshGitlock guard remain mandatory, no claim allsystemprocess visible.','Archive rawgzip bytes/metadata/xattrs, fullroundtrip/fsync and protectedsource/index afterchecks required; actualpeer and normalpush/fullremote rawblob verification still pending.','This is not approval for unlink. Separate removal must first verify deliveredarchive and recheck effectiveprivateGitdir/common/index plus no consumer/locks/stageddirty/currentexactstatus; no source/fixtures/refs/objects deletion.','README original25MiB phrase is unit typo:25,165,824B=24MiB; tool changes no diskthreshold. Owner notified for separateannotation; not blocker to read-only archive.','Future restore cannot preserve originalinode/ctime; no-clobber restoredbytes/mode/uid/gid/xattrs/times plus original3D proof needed before reactivation. No restore/tool action performed now.']}
p=O/'REVIEW.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'exit_code':0,'checks':n,'path':str(p),'sha256':H(p.read_bytes())}))
