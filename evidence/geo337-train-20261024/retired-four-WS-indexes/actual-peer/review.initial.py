from pathlib import Path
import json,hashlib,gzip,datetime,os,stat
B=Path('/dev/shm/geometry-axiom-geo337-20261025');P=B/'retired-four-WS-indexes-20261025';C=B/'four-WS-index-archive-root-original-20261025';O=Path('/workspace/geo337-four-retired-WS-index-actual-peer-20261025');O.mkdir(exist_ok=False);n=0
H=lambda b:hashlib.sha256(b).hexdigest()
def J(p):return json.loads(Path(p).read_bytes())
def ck(k,v):
 global n
 n+=1
 if not v:raise AssertionError(k)
def meta(p):
 s=p.lstat();return dict(dev=s.st_dev,inode=s.st_ino,nlink=s.st_nlink,mode=s.st_mode,uid=s.st_uid,gid=s.st_gid,bytes=s.st_size,allocated=s.st_blocks*512,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,atime_ns=s.st_atime_ns)
def read_original(p):
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NOATIME)
 with os.fdopen(fd,'rb')as f:return f.read()
r=J(P/'RESULT.json');plan=J(P/'PLAN.json');req=J(P/'REQUEST.json');outer=J(C/'RESULT.json');hostpath=Path('/workspace/geo337-four-WS-index-archive-EXEC_FINAL-20261025.json');host=J(hostpath)
ck('allterminal0',host['status']=='FINISHED' and host['actual_tool_result']['exit_code']==outer['exit_code']==r['exit_code']==0)
ck('scopeonly',r['index_removed']is False and outer['index_removed']is False and r['formal_executed']is False and r['remote_delivered']is False and r['removal_authorized_by_this_tool']is False)
ck('planpin',H((P/'PLAN.json').read_bytes())==r['plan_sha256']=='24b2f5df655362bd2c2c6a9ea4c98e3d4bcabc384e80d8c46684e1ec7b2f872f')
ck('executorpin',H((C/'EXECUTOR.py').read_bytes())==r['executor_sha256']=='b7e3f6c5c1f5ad18c1ea9db697c035d01a439991819ad160ae502374c15663ab')
q=(C/'ROOT_REQUEST.json').read_bytes();ck('requestexact',H(q)==outer['request_sha256']==r['request_sha256']=='05ac1bd34a6a8fd010db5edbdc161e8b08e65820de56277ea379c254727701d9'and json.loads(q)==req)
for k in ['root_four_sources_no_reuse_lease','root_no_active_consumers_lease','root_shared_shm_capacity_admitted']:ck('rootlease',req[k]is True)
pp=Path(req['independent_peer']['path']);peer=J(pp);ck('acceptedexactpeer',H(pp.read_bytes())==req['independent_peer']['sha256']=='f0a7d83c4fa0d0440c34769b92a7e4b20844fe8cebfdb65a40bdc73cb7c98f53'and peer['exit_code']==0 and peer['executor_sha256']==r['executor_sha256'])
rows=J(P/'commands/subcommands.json');orows=J(C/'subcommands.json');ck('48plus1commands',len(rows)==48 and len(orows)==1 and rows==r['commands'] and orows[0]==outer['original_command'])
for row in rows+orows:
 d=Path(row['directory']);ck('exactoriginalexit',J(d/'result.json')==row and row['actual_process_returncode']==0 and not row['timeout_expired'])
 for s in ['stdout','stderr']:
  raw=(d/(s+'.bin')).read_bytes();ck('fulloriginalstream',H(raw)==row[s+'_sha256']and len(raw)==row[s+'_bytes'])
 ck('fullstdin',H((d/'stdin.bin').read_bytes())==row['stdin_sha256'])
summary=json.loads((Path(orows[0]['directory'])/'stdout.bin').read_bytes());ck('hostsameoriginalstdout',json.loads(host['actual_tool_result']['output'])==summary and summary=={'exit_code':0,'out':str(P),'index_removed':False,'remote_delivered':False})
ck('fourarchives12snapshots',len(r['archives'])==4 and len(r['snapshots'])==12)
archivechecks=[]
for s,a in zip(plan['subjects'],r['archives']):
 role=s['role'];ck('exactrolehead',role==a['role']and s['head']==a['head']and s['index']==a['original_index'])
 snaps=[x for x in r['snapshots']if x['role']==role];ck('3snapshotphases',[x['phase']for x in snaps]==['before','prearchive','after'])
 for snap in snaps:
  ck('snapshotindex',snap['index_sha256']==s['index_sha256']and snap['index_metadata']==s['index_metadata'])
  ck('snapshotstagedstatusrefs',snap['staged_empty']is True and snap['status_sha256']==s['git_status_sha256']and snap['refs_sha256']==s['git_refs_sha256'])
 ck('xattrsconsistent',snaps[0]['xattrs_hex']==snaps[1]['xattrs_hex']==snaps[2]['xattrs_hex']==a['xattrs_hex'])
 for phase in ['before','prearchive','after']:
  rr=[x for x in rows if x['cwd']==s['root'] and x['source_variant']=='Retired index archive only: '+phase]
  ck('fourphaseCLI',len(rr)==4 and all(x['source_sha']==s['head']for x in rr));outs=[(Path(x['directory'])/'stdout.bin').read_bytes()for x in rr]
  ck('phaseexacthead/staged/status/refs',outs[0].decode().strip()==s['head']and outs[1]==b''and outs[2].hex()==s['git_status_hex']and H(outs[3])==s['git_refs_sha256'])
  ck('Gitoptionalnoauto',all(x['command'][:6]==['git','--no-optional-locks','-c','gc.auto=0','-c','maintenance.auto=false']for x in rr))
 ap=P/a['archive'];compressed=ap.read_bytes();ck('fullcompressedhash',H(compressed)==a['archive_sha256']and len(compressed)==a['archive_bytes'])
 raw=gzip.decompress(compressed);ck('fullgzipEOFCRCraw',H(raw)==a['original_sha256']==s['index_sha256']and len(raw)==a['original_bytes']==s['index_metadata']['bytes'] and raw[:4]==b'DIRC')
 ip=Path(s['index']);before=meta(ip);original=read_original(ip);after=meta(ip)
 ck('retiredactualrawpreserved',original==raw and before==after==s['index_metadata'] and stat.S_ISREG(after['mode'])and after['nlink']==1)
 ck('retiredactualxattrs',{x:os.getxattr(ip,x,follow_symlinks=False).hex()for x in os.listxattr(ip,follow_symlinks=False)}==a['xattrs_hex'])
 archivechecks.append({'role':role,'path':str(ap),'archive_bytes':len(compressed),'archive_sha256':H(compressed),'original_index':str(ip),'original_bytes':len(raw),'original_sha256':H(raw),'original_still_present_unchanged':True,'gzip_crc_verified':True})
consumers=sorted(P.glob('consumer-*/CONSUMERS.json'));ck('sixconsumerchecks',len(consumers)==6)
unknown=0
for p in consumers:
 c=J(p);ck('zeroaccessiblehits',c['hits']==[] and isinstance(c['unreadable'],list)and 'accessible'in c['limitation']);unknown+=len(c['unreadable'])
ck('readeroriginal3D',bytes.fromhex(plan['subjects'][3]['git_status_hex'])==' D current_geometry.c\0 D geometry-guide/current_geometry-導讀.html\0 D geometry-guide/公理層-閱讀器.html\0'.encode())
ck('rawtotal',sum(x['original_bytes']for x in archivechecks)==r['archived_raw_index_bytes']==23386440)
ck('noactualreclaim',r['hypothetical_later_WS_release_bytes']==23400448 and r['all_four_original_indexes_still_present']is True)
report={'schema':'geo337-four-retired-index-archive-actual-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':0,'checks':n,'plan_sha256':r['plan_sha256'],'executor_sha256':r['executor_sha256'],'archive_result_sha256':H((P/'RESULT.json').read_bytes()),'outer_result_sha256':H((C/'RESULT.json').read_bytes()),'host_final_sha256':H(hostpath.read_bytes()),'original_command_counts':{'archive':48,'outer':1},'archives':archivechecks,'archive_bytes':sum(x['archive_bytes']for x in archivechecks),'raw_index_bytes':23386440,'potential_allocated_release_bytes':23400448,'actual_reclaimed_bytes':0,'index_removed':False,'remote_delivered':False,'consumer_checks':6,'unreadable_proc_fields_recorded':unknown,'blocking_findings':[],'limits':['Read-only formally approved require_escalated on closedarchive/streams and exactfour retiredindexes O_NOATIME; no newGit/process scan or activeROOT access, no archive/product rerun.','All4complete compressedbytes/hash+gzipEOFCRC+decompressedoriginalbytes exact;12snapshots/48Gitcommands preserveHEAD/staged/status/refs/index and originalreader3D.','Originalc51 only checks accessibleprocess fields and records unknowns; no claim allsystemprocess visible. Freshconsumer/lock/privateGitdir/no-staged guards still required for later removal.','Sourceindex metadata compared byte/inode/ctime/mtime/mode/owner/nlink/xattrs and allfour remain. NoWS bytes reclaimed and no deletion authorized by thispeer.','Original code completedfsync calls; SHM remains volatile, not durablepublication. Fullnormalpush/remoteallblob verification pending before separate removal.','Exact originalmode/uid/gid/times/xattrs restore contract preserved; futureinode/ctime cannot be restored physically.']}
f=O/'REVIEW.json';f.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'exit_code':0,'checks':n,'path':str(f),'sha256':H(f.read_bytes()),'archive_bytes':report['archive_bytes']}))
