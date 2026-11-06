from pathlib import Path,PurePosixPath
import json,hashlib,ast,datetime,tarfile
B=Path('/workspace/geo337-F9-q38-collection-preparation-20261025');OLD=Path('/workspace/geo337-F9-axiom-collection-preparation-20261025');O=Path('/workspace/geo337-F9-q38-collector-static-peer-20261025');O.mkdir(exist_ok=False);H=lambda b:hashlib.sha256(b).hexdigest();n=0
F='4f8a794f4167c3562eb182045102e86e9e37cca9'
def J(p):return json.loads(Path(p).read_bytes())
def ck(k,v):
 global n
 n+=1
 if not v:raise AssertionError(k)
pins=J(B/'PINS.json');names={'collector_sha256':'collect_q38.py','inventory_sha256':'INVENTORY.json','parts_sha256':'PARTS.json','preparation_result_sha256':'RESULT.json','preparer_sha256':'prepare_inventory.py'}
for key,name in names.items():ck('inputpin',H((B/name).read_bytes())==pins[key])
ck('expectedtoolpin',pins['collector_sha256']=='65a25be44032bff390584123e86740c78e4ff0a5e7709b317b8f9e3fc785f820')
old=(OLD/'collect_axiom.py').read_text();new=(B/'collect_q38.py').read_text();ck('oldexact0587',H(old.encode())=='0587f5a2730f8ce66406235e3dce176bd1e22e99865351e04ef85ebf34774787')
expected=old.replace('axiom','q38').replace('AXIOM','Q38').replace('189','300')
for x,y in [('9779dd47502124d55bd62fe5146627a81a853e1ef274fefba74b2fad7bf08aeb',pins['inventory_sha256']),('1edc089f03935973f062e0aaebe05c48bb66d5cf5b32d473cdb0d3202bc85134',pins['parts_sha256']),('9622a1be5b794d79d37d4cd2b3bf7b1353451c6bb1593507a5cff5f090fa24d5',pins['preparation_result_sha256'])]:expected=expected.replace(x,y)
ck('wholeexactlabelpin/countdelta',expected==new)
ot=ast.parse(old);nt=ast.parse(new)
for name in ['sha','digest','J','state','write','verify','overhead']:
 a=next(x for x in ot.body if isinstance(x,ast.FunctionDef)and x.name==name);b=next(x for x in nt.body if isinstance(x,ast.FunctionDef)and x.name==name);ck('helperAST '+name,ast.dump(a)==ast.dump(b))
i=J(B/'INVENTORY.json');parts=J(B/'PARTS.json');r=J(B/'RESULT.json');request=J(B/'COLLECTION_REQUEST.unbound.json')
ck('F9identity',i['source_sha']==r['source_sha']==request['source_sha']==F)
ck('originalpreponly',r['inventory_exit']==0 and r['archive_created']is False and r['subject_rerun']is False and r['current_execution_admitted']is False)
ck('346regular',len(i['records'])==r['inventory_regular_files']==346 and all(x[2]=='regular'for x in i['records']))
ck('totalbytes',sum(x[3]for x in i['records'])==r['inventory_regular_bytes']==14674721)
ck('original300',sum(x[0]==0 for x in i['records'])==300 and sum(x[3]for x in i['records']if x[0]==0)==14309477)
selectionpath=Path('/workspace/geo337-F9-q38-package-selection-v2-20261025/ROOT_SELECTION.json');selection=J(selectionpath);ck('selectionpin',H(selectionpath.read_bytes())==i['selection_sha256']=='64da4885e6f4288317feb0c71708d4073c79d3334ec4c308839dd9a40745cde1')
rawref=selection['raw']['inventory'];rawpath=Path(rawref['path']);ck('originalinventorypin',H(rawpath.read_bytes())==rawref['sha256']and rawpath.stat().st_size==rawref['bytes']);raw=J(rawpath)
expectedrows={('q38-original/'+Path(x['path']).relative_to(selection['raw']['source_root']).as_posix()):(x['bytes'],x['sha256'])for x in raw}
for group in selection['additional_groups'].values():
 for rel,nb,h in group['files']:expectedrows[group['archive_prefix']+'/'+rel]=(nb,h)
expectedrows['root-admission/q38-root-admission-20261025.json']=(502,'3d9aee200e26446310de5fee635ec15f79573c19c907ed61e87f84dec4450c75')
observed={};headers=0
for row in i['records']:
 ri,rel,kind,size,pin,st,target=row;root=i['roots'][ri];member=root['prefix']+'/'+rel
 ck('safe/source/member',not PurePosixPath(rel).is_absolute()and '..'not in PurePosixPath(rel).parts and not PurePosixPath(member).is_absolute()and '..'not in PurePosixPath(member).parts and not root['source_root'].startswith('/tmp/train337-323-f64d638f-source'))
 ck('completeexpectedrow',expectedrows.get(member)==(size,pin)and kind=='regular'and target is None and st[3]==size)
 observed[member]=(size,pin);info=tarfile.TarInfo(member);info.mode=st[2]&0o777;info.mtime=st[4]//1000000000;info.size=size;ck('actualPAXbound',len(info.tobuf(tarfile.PAX_FORMAT))+511<=4096)
ck('allonceexact',observed==expectedrows and len(observed)==346)
for ri,root in enumerate(i['roots']):
 wanted={x[1]for x in i['records']if x[0]==ri};ck('rootscope',root['selection']==('whole-tree'if ri==0 else'exact-files')and(ri==0 or wanted==set(root['exact_files'])))
ck('singleexactpart',len(parts)==1 and len(parts[0]['members_exact'])==346 and set(parts[0]['members_exact'])==set(observed))
p=parts[0];logical=sum(x[3]for x in i['records']);upper=logical+4096*346+11264;over=(upper+4095)//4096+(upper+16383)//16384+(upper+33554431)//33554432+1024
ck('fullbudget64MiB2MiB',p['logical_regular_bytes']==logical and p['tar_upper_bytes']==upper and p['gzip_upper_bytes']==upper+over and p['metadata_bytes']==2*1024**2 and p['reserve_bytes']==64*1024**2 and p['required_fresh_bytes']==r['maximum_required_fresh_bytes']==upper+over+66*1024**2==85315157)
ck('unboundfalse',request['execute']is False and request['root_execution_lease']is False and request['root_admission']['actual_collection_admitted']is False)
ck('rootcapexplicit',request['root_admission']['shared_planning_ceiling_bytes']==2147483648 and request['root_admission']['incremental_planning_bytes']==85315157 and request['root_admission']['shared_allocated_before_bytes']is None)
C=Path('/workspace/geo337-F9-q38-collection-preparation-original-20261025');rows=J(C/'subcommands.json');ck('onepreptrue0',len(rows)==1 and J(C/'RESULT.json')['exit_code']==0)
for row in rows:
 d=Path(row['directory']);ck('trueprepcapture',J(d/'result.json')==row and row['actual_process_returncode']==0 and not row['timeout_expired'])
 for s in ['stdout','stderr']:
  b=(d/(s+'.bin')).read_bytes();ck('fullpreporiginalstream',H(b)==row[s+'_sha256']and len(b)==row[s+'_bytes'])
 summary=json.loads((d/'stdout.bin').read_bytes());ck('prepoutputidentity',summary['inventory_sha256']==pins['inventory_sha256']and summary['parts_sha256']==pins['parts_sha256']and summary['result_sha256']==pins['preparation_result_sha256']and summary['archive_created']is False)
report={'schema':'geo337-F9-Q38-complete-collector-static-peer/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':0,'checks':n,'source_sha':F,**{k:pins[k]for k in ['collector_sha256','inventory_sha256','parts_sha256','preparation_result_sha256','preparer_sha256']},'blocking_findings':[],'original_files':300,'total_regular_files':346,'total_regular_bytes':14674721,'required_fresh_bytes':85315157,'limits':['Exact wholecollector byte delta against acceptedaxiom0587 is only names/schema/pins and189→300. Sevenhelpers AST identical; originalfullsourcehash/stat/scope/roundtrip/gzipCRC/64MiB+2MiB preserved.','Original300 scope exact matches accepted300rawmetadata;45selectedtools/peers+502Boriginaladmission included. ExistingjudgetemporaryELFs were cleaned by originallifecycle; no claim unavailablebytes retained.','Static/inventory/originalprepstream only; noSHM/liveROOT read, noarchive creation/product execution/recollection. Runtime actualsource/fulltar peer still required.','Root must freshly check twoOWNuniqueallocated+85,315,157<=2GiB and actualoutdevicefree, preserveclosedsourcelease and formalrequire_escalated. Collector independently checksdevicefree but does not implementsharedcapadmission.','F9Q38 original44/43killed+SPM24equivalent remains historicalF9; collection0 never impliesF10gate0 or durablepublicdelivery.']}
f=O/'REVIEW.json';f.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'exit_code':0,'checks':n,'path':str(f),'sha256':H(f.read_bytes())}))
