#!/usr/bin/env python3
"""Read-only audit of fixed historical B2 originals. Never executes a product binary."""
import argparse, ast, collections, datetime, gzip, hashlib, importlib.util, json, os, platform, posixpath, re, statistics, subprocess, sys, tarfile
from pathlib import Path
P=argparse.ArgumentParser();P.add_argument('--git',required=True,type=Path);P.add_argument('--archives',required=True,type=Path);P.add_argument('--out',required=True,type=Path);a=P.parse_args()
M='0ae1728c2309e1d670369289a6b8da059fa63a50';F='cbf0fb621888596aa14ad5f2349b503e23b1b72d';F8='75a1e93811a52b69385cbdaf6a09d773ed9052ad';F9='4f8a794f4167c3562eb182045102e86e9e37cca9';BASE='b74f9a2ae7ade1555b9be45283adecc097fb76e3';MAIN='adbaebf9c73ea6801d7b4d5214e4b846b132923b'
R8_PATH='evidence/geo337-train-20261024/full-R8-five-stage-raw/ORIGINAL_R8_FIVE_STAGE_RAW.tar.gz';ABC_DIR='evidence/geo337-train-20261024/F9-geo323-ABC-comparison-public/archives/'
def sha(b):return hashlib.sha256(b).hexdigest()
def stamp(b):return {'bytes':len(b),'sha256':sha(b)}
def must(v,msg):
 if not v:raise AssertionError(msg)
def git(*args):return subprocess.check_output(['git','--no-optional-locks','-C',str(a.git),*args])
def url(path):return 'https://github.com/ZhiQiYang/geometry-axiom/blob/'+M+'/'+path
blobs={};trees={}
def tree(ref):
 if ref not in trees:
  trees[ref]={}
  for row in git('ls-tree','-rz',ref).split(b'\0'):
   if not row:continue
   desc,p=row.split(b'\t',1);mode,kind,oid=desc.decode().split();trees[ref][p.decode()]={'mode':mode,'kind':kind,'oid':oid}
 return trees[ref]
def source(ref,path):
 item=tree(ref)[path];must(item['kind']=='blob' and item['mode'] in ('100644','100755'),'not regular source '+path);oid=item['oid']
 if oid not in blobs:blobs[oid]=git('cat-file','blob',oid)
 return blobs[oid]
def closure(ref):
 files={};absent=[];system=set()
 def read(path):
  if path in files:return
  data=source(ref,path);files[path]=stamp(data)
  for operand in re.findall(rb'^\s*#\s*include\s+([^\r\n]+)',data,re.M):must(operand.lstrip().startswith((b'"',b'<')),'macro include '+path)
  for inc in re.findall(rb'^\s*#\s*include\s*<([^>\r\n]+)>',data,re.M):system.add(inc.decode())
  for inc in re.findall(rb'^\s*#\s*include\s*"([^"\r\n]+)"',data,re.M):
   child=posixpath.normpath(posixpath.join(posixpath.dirname(path),inc.decode()));must(not child.startswith('../'),'escaped repo')
   if child in tree(ref):read(child)
   else:absent.append({'including':path,'operand':inc.decode(),'resolved':child})
 read('geometry-web/web_bridge.c')
 return {'source_sha':ref,'entry':'geometry-web/web_bridge.c','files':dict(sorted(files.items())),'file_count':len(files),'missing_quoted_includes':absent,'system_includes':sorted(system)}
closures={ref:closure(ref) for ref in (BASE,MAIN,F8,F9,F,M)}
for ref in (F9,F,M):must(closures[ref]['files']==closures[F8]['files'],'product closure changed '+ref)
print('C closure: base=%d main=%d F8/F9/F/M=%d; all four fix closures identical'%(closures[BASE]['file_count'],closures[MAIN]['file_count'],closures[F8]['file_count']),flush=True)
raw={};archive_map={};symlinks=[]
for name,path in [('ORIGINAL_R8_FIVE_STAGE_RAW.tar.gz',R8_PATH)]+[(f'PUBLIC_COMPARISON_PART{i}.tar.gz',ABC_DIR+f'PUBLIC_COMPARISON_PART{i}.tar.gz') for i in range(1,6)]:
 disk=a.archives/name;b=disk.read_bytes();must(b==source(M,path),'archive differs from fixed Git '+name);archive_map[name]=dict(stamp(b),git_path=path,git_url=url(path),git_blob=tree(M)[path]['oid'])
 with tarfile.open(disk,'r|gz') as t:
  for member in t:
   if member.issym():
    if member.name.endswith('/bridge'):symlinks.append({'archive':name,'member':member.name,'target':member.linkname,'mode':oct(member.mode),'payload_present':False})
    continue
   if not member.isfile():continue
   n=member.name
   wanted=name!='ORIGINAL_R8_FIVE_STAGE_RAW.tar.gz' or n.startswith(('tools/v5/','original/evidence/','original/work/','original/invocations/','original/control/','original-orchestration/')) or n=='original/receipt.json' or n.startswith('fixed-R-source/')
   if wanted:
    b=t.extractfile(member).read()
    if n in raw:must(raw[n]==b,'duplicate member conflict '+n)
    raw[n]=b
print('Read six original archives; no ELF invocation; no resampling',flush=True)
def J(name):return json.loads(raw[name])
def bind(name):
 ar='ORIGINAL_R8_FIVE_STAGE_RAW.tar.gz' if name.startswith(('original/','original-orchestration/','fixed-R-source/','tools/v5/')) else next(n for n in archive_map if n.startswith('PUBLIC_') and name in members[n])
 return dict(stamp(raw[name]),archive=ar,member=name,git_archive_url=archive_map[ar]['git_url'])
# Build the member lookup from the already read tar headers, not filesystem symlink resolution.
members={}
for name in archive_map:
 if name.startswith('PUBLIC_'):
  with tarfile.open(a.archives/name) as t:members[name]={m.name for m in t.getmembers()}
for ref,prefix in ((F8,'fixed-R-source/'),(BASE,'original/work/source-base/'),(MAIN,'original/work/source-main/')):
 for p,h in closures[ref]['files'].items():must(stamp(raw[prefix+p])==h,'archived build source changed '+prefix+p)
reuse=J('comparison/REUSE_BEFORE.json');must(raw['comparison/REUSE_BEFORE.json']==raw['comparison/REUSE_AFTER.json'],'reuse before/after changed')
must(reuse['old_closure']==closures[F8]['files'] and reuse['execution_closure']==closures[F9]['files'],'recorded closure not independently reproducible')
inv=J('original/evidence/scene-inventory.json');finv=J('comparison/evidence/scene-inventory.json');must(inv==finv,'F9 inventory changed')
must(inv['root_count']==171 and inv['generated_count']==4 and inv['total']==175,'scene counts');must(len(inv['scenes'])==175,'scene list count')
fixtures=[]
for e in inv['scenes']:
 name=e['name'];h={'bytes':e['bytes'],'sha256':e['sha256']}
 if 'generated_n' in e:
  must(e['generated_n'] in (16,32,48,64),'unknown generated N');r=raw['original/evidence/scenes/'+name];must(r==raw['comparison/evidence/scenes/'+name],'generated F9 changed')
 else:
  for ref in (BASE,F8,F9,F,M):must(stamp(source(ref,name))==h,'root fixture changed '+ref+':'+name)
  r=raw['fixed-R-source/'+name];must(r==source(BASE,name),'archived root fixture changed '+name)
 must(stamp(r)==h,'fixture original mismatch '+name);fixtures.append(dict(e,original_member=('original/evidence/scenes/' if 'generated_n'in e else 'fixed-R-source/')+name))
must('_i11_two_surfaces_same_uv_accept.scene' not in [x['name'] for x in fixtures],'extra scene incorrectly included')
print('Inputs verified: 171 exact base fixtures + 4 generated fixtures; additional I11 scene excluded',flush=True)
r8=J('original/receipt.json');f9=J('comparison/receipt.json');must(r8['source_sha']==F8 and f9['source_sha']==F9,'execution SHA');must(r8['base']==BASE and r8['main']==MAIN,'fixed denominator')
# Frozen tools are external data inputs; no present-checkout judge replacement is allowed.
tools8={k:bind('tools/v5/'+k) for k in r8['tool_hashes']};tools9={k:bind('comparison/tools-frozen/'+k) for k in f9['tool_hashes'] if k.endswith('.py')}
for k,v in tools8.items():must(v['sha256']==r8['tool_hashes'][k],'R8 frozen tool '+k)
for k,v in tools9.items():must(v['sha256']==f9['tool_hashes'][k],'F9 frozen tool '+k)
builds={}
for role in ('base','fix','main','base-trace','fix-trace','base-pg','fix-pg'):
 path='original/work/'+role+'/build.json';b=J(path);must(b['exit']==0,'build failed '+role);builds[role]={'original':bind(path),'result':b}
# Reconstruct the frozen trace overlay in memory (no compiler/product execution).
const={node.targets[0].id:ast.literal_eval(node.value) for node in ast.parse(raw['tools/v5/verify_linux.py']).body if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('TRACE','GUARDS')}
trace_closures={}
for ref,role in ((BASE,'base-trace'),(F8,'fix-trace')):
 traced={p:source(ref,p) for p in closures[ref]['files']}
 for rel,names in [('geometry-app/native/world_candidate.inc',const['GUARDS'][:3]),('current_geometry.c',[const['GUARDS'][3]]),('geometry-core/references.inc',[const['GUARDS'][4]]),('geometry-core/kernel/source.c',['geo_eval_seal'])]:
  data=traced[rel]
  for name in names:
   matches=list(re.finditer(rb'\b'+name.encode()+rb'\s*\([^;{}]*\)\s*\{',data));must(len(matches)==1,'trace anchor '+name);at=matches[0].end();hook='residual_trace_seal(ctx);' if name=='geo_eval_seal' else 'residual_guard(%d);'%const['GUARDS'].index(name);data=data[:at]+hook.encode()+data[at:]
  traced[rel]=data
 pre=b'struct GeoEvalContext;static void residual_trace_seal(const struct GeoEvalContext *);static void residual_guard(unsigned);\n'
 traced['geometry-web/web_bridge.c']=pre+traced['geometry-web/web_bridge.c']+const['TRACE'].encode()
 for p,data in traced.items():must(raw['original/work/'+role+'/source/'+p]==data,'trace source reconstruction '+role+':'+p)
 trace_closures[role]={'source_sha':ref,'frozen_overlay_tool':tools8['verify_linux.py'],'files':{p:stamp(data) for p,data in sorted(traced.items())},'archive_source_prefix':'original/work/'+role+'/source/','independently_reconstructed_byte_equal':True}
perf=J('original/evidence/performance.json');samples=perf['samples'];must(len(samples)==36,'36 exact samples')
wanted=[(n,r,v) for n in (16,32,48,64) for r in (1,2,3) for v in ('base','fix','main')];must([(x['n'],x['round'],x['version']) for x in samples]==wanted,'sample order')
for x in samples:must(type(x['exit']) is int and x['exit']==0,'perf exit')
med={}
for n in (16,32,48,64):
 values={v:statistics.median(x['seconds'] for x in samples if x['n']==n and x['version']==v) for v in ('base','fix','main')};values.update({'fix/base':values['fix']/values['base'],'fix/main':values['fix']/values['main']});must(values==perf['medians'][str(n)],'median mismatch');med[str(n)]=values
must(med['64']['fix/main']<=1.3 and all(med[str(n)]['fix/base']<=1 for n in (16,32,48)),'original perf threshold failed')
profiles=J('original/evidence/profile-counts.json');profile_inputs={}
for k,row in profiles.items():
 data=raw['original/evidence/gprof-'+k+'.stdout'];must(sha(data)==row['gprof_stdout_sha256'],'gprof hash')
 counts={}
 for line in data.decode().split('Call graph')[0].splitlines():
  parts=line.split()
  if len(parts)==7 and parts[-1] in row['counts']:counts[parts[-1]]=int(parts[3])
 for symbol in row['counts']:counts.setdefault(symbol,0)
 must(counts==row['counts'],'gprof counts');profile_inputs[k]={'gprof':bind('original/evidence/gprof-'+k+'.stdout'),'gmon':bind('original/evidence/gmon-'+k+'.gz'),'load':{'original':bind('original/evidence/checks/profile-'+k+'-load.json'),'result':J('original/evidence/checks/profile-'+k+'-load.json')},'gprof_command':{'original':bind('original/evidence/checks/profile-'+k+'-gprof.json'),'result':J('original/evidence/checks/profile-'+k+'-gprof.json')}}
ratio=profiles['fix-64']['counts']['geo_eval_source']/profiles['fix-32']['counts']['geo_eval_source'];must(ratio<=4.5,'source call ratio')
# Cross-check all original invocation streams, exits, and sample stdout hashes.
r8commands={};r8cmdrefs={}
for p,b in raw.items():
 if p.startswith('original/invocations/') and p.endswith('/commands/commands.json'):
  commands=json.loads(b);r8commands[p]=commands;r8cmdrefs[p]=bind(p)
for p,commands in r8commands.items():
 prefix=p.rsplit('/',1)[0]
 for index,c in enumerate(commands,1):
  for stream in ('stdin','stdout','stderr'):
   n=f'{prefix}/{index:06}/{stream}.bin'
   if n in raw and c.get(stream+'_sha256') is not None:must(sha(raw[n])==c[stream+'_sha256'],'R8 raw stream '+n)
perf_cmds=[c for p,cs in r8commands.items() if '064908' in p for c in cs if c['command'][0].endswith('/bridge')]
must(len(perf_cmds)==36,'R8 36 real bridge commands')
for sample,c in zip(samples,perf_cmds):must(sample['stdout_sha256']==c['stdout_sha256'] and c['actual_process_returncode']==0 and not c['timeout_expired'],'R8 perf process identity')
# F9: independently recompute the saved raw comparisons with the immutable exact comparator.
module_name='frozen_q323_exact_policy';spec=importlib.util.spec_from_loader(module_name,loader=None);policy=importlib.util.module_from_spec(spec);sys.modules[module_name]=policy;exec(compile(raw['comparison/tools-frozen/q323_exact_policy.py'],module_name,'exec'),policy.__dict__)
equiv=J('comparison/evidence/equivalence.json');owner=J('comparison/evidence/owner-exact-audit.json');must(equiv['scenes']==175 and len(equiv['runs'])==350,'175/350 rows');must(owner['execution_source_sha']==F9 and owner['audit_exit']==0,'owner execution identity')
rows=equiv['runs'];pairs={};observations=[];insertions=[]
fixed=sorted(e['name'] for e in fixtures if 'generated_n'not in e);generated=sorted(e['name'] for e in fixtures if 'generated_n'in e)
must([(r['scene'],r['version']) for r in rows]==[(n,v) for n in fixed+generated for v in ('base','fix')],'F9 row order')
for r in rows:
 n,v=r['scene'],r['version'];streams={}
 for s in ('stdout','stderr'):
  member='comparison/evidence/stdout/'+v+'/'+n+'.'+s;data=raw[member];must(stamp(data)=={'bytes':r[s+'_bytes'],'sha256':r[s+'_sha256']},'ABC stream hash');streams[s]=data
 compressed=raw['comparison/evidence/graphs/'+v+'/'+n+'.bin.gz'];graph=gzip.decompress(compressed);must(stamp(graph)=={'bytes':r['graph_bytes'],'sha256':r['graph_sha256']},'ABC ordered graph hash')
 must(r['command']=='loadfile '+r['path']+'\ndump\n','ABC exact command');pairs.setdefault(n,{})[v]=dict(streams,graph=graph,guards=r['guards'],exit=r['exit'],trace_exit=r['trace_exit'])
 observations.append({'scene':n,'version':v,'stdout_sha256':sha(streams['stdout']),'stderr_sha256':sha(streams['stderr']),'graph_sha256':sha(graph),'compressed_graph_sha256':sha(compressed)})
for n in fixed+generated:
 row=next(r for r in rows if r['scene']==n and r['version']=='base');res=policy.compare_pair(n,row['path'],pairs[n]['base'],pairs[n]['fix'],scope=policy.SCOPE,base_sha=BASE);must(res['ok'],'ABC recomputation failure '+n+str(res['failures']));insertions+=res['authorized_insertions']
must(len(insertions)==6 and insertions==equiv['authorized_insertions']==owner['authorized_insertions_recomputed'],'exact 3 scenes / 6 stream insertions');must(observations==owner['observations'],'raw owner audit observations changed');must(not equiv['failures'] and not owner['failures'],'original ABC failure')
f9commands=J('comparison/invocation/commands/commands.json');bc=[c for c in f9commands if c['command'][0].endswith('/bridge')];must(len(bc)==700,'700 plain/trace actual commands')
for i,c in enumerate(f9commands,1):
 for s in ('stdin','stdout','stderr'):
  n=f'comparison/invocation/commands/{i:06}/{s}.bin'
  if n not in raw:
   must(s=='stdin' and c['stdin_provided'] is False and c[s+'_sha256']==sha(b''),'missing nonempty original '+n)
  else:must(sha(raw[n])==c[s+'_sha256'],'F9 process raw stream hash '+n)
for c in bc:must(c['actual_process_returncode']==0 and c['timeout_expired'] is False,'F9 process return/timeout')
# Trace outputs must match each plain run, in addition to paired base/fix checks.
for i,r in enumerate(rows):
 plain,trace=bc[2*i:2*i+2]
 for s in ('stdout','stderr'):must(plain[s+'_sha256']==trace[s+'_sha256']==r[s+'_sha256'],'trace observer changed output')
 must(plain['stdin_sha256']==trace['stdin_sha256']==sha(r['command'].encode()),'trace stdin changed')
print('R8 36 samples + 4 profiles: original green thresholds rechecked, no new samples',flush=True)
print('F9 raw audit: 175 pairs / 350 observations / 700 original bridge calls / 6 exact insertions; exit 0',flush=True)
# Current differences are classified against actual reader/build inputs, not ignored wholesale.
diffs={}
for ref in (F8,F9,F):
 changed=git('diff','--name-only','-z',ref,M).decode().rstrip('\0').split('\0');records=[]
 for p in changed:
  in_c=p in closures[M]['files'] or p in closures[ref]['files'];in_scene=p in [x['name']for x in fixtures];must(not in_c and not in_scene,'changed runtime input '+p)
  category='historical_evidence_not_runtime_input' if p.startswith('evidence/') else {'geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md':'architecture_generated_report','geometry-core/domain-decoupling/product-architecture-receipt.json':'architecture_generated_receipt','tests/mutants_results.json':'mutation_ledger_not_read_by_b2','tests/test_geo314_commit_paths.py':'other_suite_not_invoked_by_b2','決策佇列.md':'current_policy_document_not_read_frozen_F9_authority_is_distinct'}.get(p)
  must(category is not None,'unclassified changed path '+p);records.append({'path':p,'category':category,'in_product_include_closure':in_c,'in_scene_inventory':in_scene})
 diffs[ref]={'to_sha':M,'changed_count':len(records),'non_evidence':[r for r in records if not r['path'].startswith('evidence/')],'evidence_count':sum(r['path'].startswith('evidence/')for r in records),'all_changed_paths':records}
for excluded in ('tests/test_geo314_commit_paths.py','決策佇列.md'):
 must(excluded not in closures[M]['files'] and excluded not in [e['name']for e in fixtures],'excluded input actually read')
# Frozen F9 authority inputs remain historical pins; private identity payload is excluded from the public archive.
# This audit does not reconstruct identities or claim current execution of require_verified_authority.
authority={'original_binding_sha256':policy.AUTHORITY_BINDING_SHA256,'approval_sha':policy.APPROVAL_SHA,'scope':policy.SCOPE,'statement':'Original receipt records verified authority. This read-only closure audit replays byte comparator only; it does not rerun private authority verification. Current 決策佇列.md is not that frozen authority input.','private_authority_payload_in_public_archive':False}
outer={stage: {'original':bind('original-orchestration/launch-five/'+stage+'/result.json'),'result':J('original-orchestration/launch-five/'+stage+'/result.json')} for stage in ('prepare','build','compare','perf','profile')}
result={'schema':'pr338-b2-closure-audit/1','audit_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'audit_command':sys.argv,'audit_exit':0,'audit_kind':'read_only_original_artifact_and_source_closure_verification_no_product_execution','execution_identities':{'R8':F8,'F9_ABC':F9,'final_product_F':F,'integration_M':M,'base':BASE,'main':MAIN},'archives':archive_map,'source_closures':closures,'source_snapshot_checks':{'F8':True,'base':True,'main':True},'fixtures':fixtures,'extra_I11_scene_included':False,'r8':{'original_receipt':bind('original/receipt.json'),'original_execution_sha':F8,'original_stage_results':r8['stages'],'original_outer_and_cumulative_results':outer,'original_compare_exit':1,'original_overall_exit':1,'strict_post_compare_ABC_audit':'not completed after strict stdout assertion; not retrospectively marked green','frozen_tools':tools8,'builds':builds,'trace_source_closures':trace_closures,'build_binary_pins':r8['builds'],'performance_original':bind('original/evidence/performance.json'),'samples_unchanged':samples,'medians':med,'profile_original':bind('original/evidence/profile-counts.json'),'profiles':profiles,'profile_inputs':profile_inputs,'thresholds':r8['quantitative_targets'],'invocation_manifests':r8cmdrefs,'original_environment':{k:r8[k]for k in ('environment','platform','versions','stack_before','stack_during')},'adoption':'only original perf/profile green subgates, by identical source/input/judge/build closure; no performance rerun'},'f9':{'original_receipt':bind('comparison/receipt.json'),'original_execution_sha':F9,'original_stage_results':f9['stages'],'frozen_tools':tools9,'reuse_before':bind('comparison/REUSE_BEFORE.json'),'reuse_after':bind('comparison/REUSE_AFTER.json'),'inventory':bind('comparison/evidence/scene-inventory.json'),'equivalence':bind('comparison/evidence/equivalence.json'),'original_owner_audit':bind('comparison/evidence/owner-exact-audit.json'),'invocation_manifest':bind('comparison/invocation/commands/commands.json'),'binary_pins':reuse['binaries'],'binary_members_are_symlinks_only':symlinks,'original_execution_calls':700,'scene_pairs':175,'observations':350,'independent_raw_audit_exit':0,'raw_observation_hashes':observations,'exact_insertions':insertions,'source_graph_and_five_guards_equal':True,'plain_and_trace_returncodes_zero':True,'compiler_rerun':False,'performance_rerun':False,'frozen_authority':dict(authority,original_pinned_hashes={k:v for k,v in f9['tool_hashes'].items() if not k.endswith('.py')}),'adoption':'original F9 ABC green only; fixed base b74; does not satisfy P-189 fixed-main comparison'},'closure_diffs_to_M':diffs,'current_excluded_files':['tests/test_geo314_commit_paths.py','決策佇列.md'],'limits':['No R8 ELF bodies recovered: F9 bridge tar entries are symlinks; B1 unresolved by this audit.','This is not a new product execution at F/M and must not relabel F8/F9 execution identity.','System/compiler closure is the original recorded environment and binaries, not a new equivalent compiler claim.','P-189 B3 is independent and not satisfied by Q-323 ABC.']}
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('WROTE',a.out,stamp(a.out.read_bytes()),flush=True)
