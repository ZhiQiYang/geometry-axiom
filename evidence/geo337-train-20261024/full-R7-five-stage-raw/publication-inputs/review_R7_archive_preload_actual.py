from pathlib import Path
import json,hashlib
B=Path('/tmp/geo337-R7-archive-preload-20261024');O=Path('/tmp/train337-publication-peer-20261024');F='6df0264f75e84f03adb70746b6ac3db07a9910fc';E='bd5df6b7fb3c563fa10d0e4cfd37e2ee3ca2b99e';OID='09d8fbda73dd3995cb245be79ec7d339f3b23ade';checks=0;bad=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(p):return json.loads(p.read_bytes())
def ck(v,n):
 global checks
 checks+=1
 if not v:bad.append(n)
r=j(B/'RESULT.json');q=j(B/'r7/RESULT.json');outer=j(B/'outer/subcommands.json');rows=j(B/'r7/commands/subcommands.json');ck(r['exit']==q['exit_code']==0 and r['product_source']==q['archive_source_sha']==F and r['root_head_unchanged']==q['expected_root_head']==E,'actual preload0 identities')
ck(r['oid']==q['object_oid']==OID and r['bytes']==q['archive_identity']['bytes']==31359550 and r['sha256']==q['archive_identity']['sha256']=='8f2420a2c4a78cd99355b32183928d1c8ce14c893fdbe88db0f101104622cd7e','original body proof pins')
ck(q['before']==q['after']and q['before']['head']==E,'exactoriginal refs/index/HEAD beforeafter unchanged')
ck(q['alternate_connected']and not q['refs_or_index_adopted']and not q['original_objects_moved_or_deleted']and q['global_git_environment_unchanged'],'nohistory/index/globalenv changes')
ck(len(rows)==29 and len(outer)==1,'29originalinner plus1outer')
for i,row in enumerate(rows+outer):
 d=Path(row['directory']);ck(j(d/'result.json')==row and not row['timeout_expired'],'originalatomic terminal')
 for stream in ['stdout','stderr']:
  p=d/(stream+'.bin');ck(h(p)==row[stream+'_sha256']and p.stat().st_size==row[stream+'_bytes'],'wholeoriginalsmallstream')
 stdin=d/'stdin.bin';ck((stdin.exists()and h(stdin)==row['stdin_sha256'])or(not stdin.exists()and row['stdin_provided']is False and row['stdin_sha256']==hashlib.sha256(b'').hexdigest()),'provided/inheritedstdin')
 ck(row['actual_process_returncode']==(1 if i==11 else 0),'true original exit; absent-object probe1 intentional')
ck(rows[11]['command'][-3:]==['cat-file','-e',OID],'onlyoriginal expectedmissingobject1')
ck(rows[12]['command'][:2]==['env','GIT_OBJECT_DIRECTORY=/tmp/geo337-published-archive-git-objects-20261024']and 'hash-object'in rows[12]['command'],'only archive insertion child objectdir')
ck((Path(rows[12]['directory'])/'stdout.bin').read_text().strip()==OID,'actual inserted object OID')
readers=q['ordinary_readers'];ck(readers==['/workspace/geometry-axiom','/workspace/geo300-capacity512-work-20261024','/tmp/geo323-final-r7-source-20261024','/tmp/train337-323-f64d638f-source'],'root+3 exactordinaryreaders')
for i,reader in enumerate(readers):
 a,b=rows[17+i*2:19+i*2];ck(a['cwd']==b['cwd']==reader and a['command'][-3:]==['cat-file','-t',OID]and b['command'][-3:]==['cat-file','-s',OID],'ordinaryreader exactblob type/size')
 ck((Path(a['directory'])/'stdout.bin').read_bytes()==b'blob\n'and(Path(b['directory'])/'stdout.bin').read_bytes()==b'31359550\n','original ordinaryreader success')
lease=q['permanent_lease'];ck(h(Path(lease['path']))==lease['sha256']=='556c513142d9559c9497bb118d12da5487ee61b80953ee27095e49269d7c0104','permanentstorelease intact')
ck(r['final_alternates_sha256']==q['final_alternates_sha256']==q['prior_alternates_identity']=='e4003887d478e946abfb1c76daa861b688d1c37d936f510a73fd833fbf48b7be','noextraalternatechange')
obj=Path(q['store'])/OID[:2]/OID[2:];st=obj.stat();x=q['new_object_identity'];ck(st.st_size==x['bytes']and st.st_ino==x['inode']and st.st_dev==x['device']and st.st_mtime_ns==x['mtime_ns'],'ordinary Gitobject metadata exact no rereadbody')
api=j(Path('/tmp/geo337-R7-preload-final-tool-result.json'));ck(api['exit_code']==0,'true API final0')
peer=j(Path('/tmp/train337-terminal-peer-20261024/R7_FULL_FIVE_STAGE_ACTUAL_PACKAGE_PEER.json'));ck(peer['exit_code']==0 and peer['checks']==50504 and not peer['findings']and peer['archive_sha256']==r['sha256'],'independent wholepackage exact priorproof')
report={'schema':'R7-original-archive-preload-small-actual-peer/1','checks':checks,'exit_code':int(bool(bad)),'findings':bad,'product_source':F,'root_evidence_head':E,'object_oid':OID,'original_result_sha256':h(B/'RESULT.json'),'original_inner_result_sha256':h(B/'r7/RESULT.json'),'command_exits':[x['actual_process_returncode']for x in rows],'limits':['No archive/object body read, rehash or new Git/network command. Original full smallstreams/type-size reader results and metadata independentchecked.','Preload is not publication or acceptance. Original absent-object probe exit1 preserved; ordinary insertion/readers0.','Permanent TMP Gitobject store is a live dependency; refs/index untouched at preloadtime, root later ordinarycommit may adopt. Never delete objects/alternate merely after remote push.']};p=O/'R7_ARCHIVE_PRELOAD_ACTUAL_PEER.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':h(p),'checks':checks,'exit_code':report['exit_code'],'findings':bad}));raise SystemExit(report['exit_code'])
