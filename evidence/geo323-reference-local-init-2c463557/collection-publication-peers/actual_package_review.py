from pathlib import Path
import collections,hashlib,json,tarfile,datetime
H=Path('/tmp/geo337-h-init-evidence-preparation-20261025');OUT=Path(__file__).resolve().parent
count=collections.Counter();fail=[]
def ck(group,ok,label):
 count[group]+=1
 if not ok:fail.append({'group':group,'label':label})
def sha(b):return hashlib.sha256(b).hexdigest()
def r(p):return json.loads(p.read_bytes())
plan=r(H/'PACKAGE_PLAN.json');index=r(H/'package/RAW_INDEX.json');summary=r(H/'package/SUMMARY.json');launch=r(H/'collection-launch/RESULT.json');initial=r(H/'ORIGINAL_TOOL_INITIAL.json');final=r(H/'ORIGINAL_TOOL_FINAL.json');S='2c4635577a8fcb11e88b346547f7bb1c7b739fb7'
for item in (plan,index,summary,launch):ck('identity',item['source_sha']==S,'product S')
ck('exit',summary['exit']==launch['exit']==launch['command']['actual_process_returncode']==final['exit_code']==0,'all actual exits zero')
ck('exit','session_id'in initial and 'exit_code'not in initial,'initial tool running rather than invented completion')
ck('exit',not launch['command']['timeout_expired'],'original capture not timeout')
ck('inventory',index['files']==plan['files'],'inventory exact frozen plan')
ck('inventory',index['count']==plan['count']==summary['archive']['members']==2546,'2546 exact files')
ck('inventory',index['logical_bytes']==plan['bytes']==summary['logical_bytes']==29033543,'29,033,543 original bytes')
archive=Path(summary['archive']['path']);raw=archive.read_bytes()
ck('archive',len(raw)==summary['archive']['bytes']==6369236,'archive exact size')
ck('archive',sha(raw)==summary['archive']['sha256']=='7011e2b2fcf35f15e53deac9f2e5d27aabf4429ffe32f275465d8abd4c5d4388','archive exact SHA')
with tarfile.open(archive,'r:gz')as tar:
 members=tar.getmembers();ck('archive',[m.name for m in members]==[x['archive']for x in plan['files']],'member order/name exact')
 for member,item in zip(members,plan['files']):
  ck('member',member.isfile() and not member.issym() and not member.islnk(),'regular '+member.name)
  b=tar.extractfile(member).read();ck('member',len(b)==item['bytes']and sha(b)==item['sha256'],'exact archived bytes '+member.name)
  p=Path(item['local']);ck('original',p.is_file()and not p.is_symlink()and p.read_bytes()==b,'original still exact '+item['local'])
for stream in ('stdout','stderr'):
 b=(Path(launch['command']['directory'])/(stream+'.bin')).read_bytes();ck('capture',len(b)==launch['command'][stream+'_bytes']and sha(b)==launch[stream+'_sha256']==launch['command'][stream+'_sha256'],'original '+stream)
ck('capture',launch['command']['source_sha']==launch['command']['acceptance_sha']==S,'capture exact S')
ck('capture',launch['collector_sha256']==sha((H/'collect.py').read_bytes()),'actual collector pin')
ck('capture',launch['plan_sha256']==sha((H/'PACKAGE_PLAN.json').read_bytes()),'actual plan pin')
ck('scope',summary['originals_deleted']is False and summary['product_tests_reexecuted']is False and summary['roundtrip']is True and summary['original_bytes_unchanged']is True,'no deleted original, no rerun')
ck('scope',summary['lock']=='/tmp/g261r3/secondary.lock','secondary slot')
keys=['PACKAGE_PLAN.json','package/RAW_INDEX.json','package/SUMMARY.json','collection-launch/RESULT.json','ORIGINAL_TOOL_INITIAL.json','ORIGINAL_TOOL_FINAL.json','collect.py']
rpt={'reviewer':'/root/h_init_actual_review','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha':S,'checks':sum(count.values()),'groups':dict(count),'failures':fail,'exit':int(bool(fail)),'archive':summary['archive'],'logical_bytes':index['logical_bytes'],'bindings':{k:sha((H/k).read_bytes())for k in keys},'scope':'complete actual archive member-by-member and original capture verification; no product rerun/publication claim'}
(OUT/'ACTUAL_PACKAGE_REVIEW.json').write_text(json.dumps(rpt,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checks':sum(count.values()),'failures':fail,'exit':rpt['exit'],'sha256':sha((OUT/'ACTUAL_PACKAGE_REVIEW.json').read_bytes())},ensure_ascii=False));raise SystemExit(rpt['exit'])
