"""F8 fallback-only cost collection. Default: metadata plan, never compile.
Original #341 Sc493 whole withdrawal remains a separate, unexecuted subject.
"""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,importlib.util,json,os,re,resource,shutil,statistics,sys
P=Path(__file__).resolve().parent
SOURCE='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
LEAF='geometry-templates/woodworking/native/contact_world.c'
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAP_HASH='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
KERNEL=('exact','codec','geometry','clip','grid','parameters','parameter_sources','linear','named_values','datums','source','candidate','placements','placement_sources','versions','enclosure','enclosure_sources','document','regions','region_key_sources','grid_store','guides','linear_definition_sources','version_sources')
VARIANTS=('fixed','withdrawn','restored')
POSITIVE=('ordering','regions','active-dedup','intervals','extensions','ends','indexed-dedup','indexed-sort')
CASES=[(kind,n)for kind in ('none','few','dense')for n in (8,32,64)]+[('fallback-none',1217),('fallback-dense',1217)]+[(kind,64)for kind in ('unique-none','unique-few','unique-dense')]
def h(b):return hashlib.sha256(b).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def inspect_output(raw,diagnostic,case,n):
 need((case,n)in CASES,'exact requested case and size')
 need(raw.endswith(b'\n'),'complete final output line')
 lines=raw.decode('utf-8').splitlines()
 expected_mode='MODE diagnostic=true performance_sample=false'if diagnostic else 'MODE diagnostic=false performance_sample=true'
 need([x for x in lines if x.startswith('MODE ')]==[expected_mode],'diagnostic/performance separation')
 keys={'META','TIME','WORK','PATH'}if diagnostic else {'META','TIME'}
 fields={}
 for line in lines:
  key,sep,rest=line.partition(' ')
  need(sep and key in keys|{'MODE','FACE'},'known complete output record')
  if key in keys:
   need(key not in fields,'one '+key)
   pairs=[p.split('=',1)for p in rest.split()]
   need(all(len(p)==2 and p[0]and p[1]for p in pairs),'complete key/value record')
   need(len({p[0]for p in pairs})==len(pairs),'unique fields')
   fields[key]=dict(pairs)
 need(set(fields)==keys,'complete diagnostic or timing records')
 meta=fields['META']
 need(set(meta)=={'case','n','admitted','capacity','fallback','face_size'},'complete META fields')
 need(meta['case']==case and meta['n']==str(n),'META matches exact requested case/size')
 need(meta['admitted']==str(n*2)and meta['capacity']=='2432'and meta['fallback']==str(int(case.startswith('fallback-'))),'META matches fixture capacity and path')
 need(re.fullmatch(r'[0-9]+',meta['face_size'])and int(meta['face_size'])>0,'positive numeric face size')
 numeric_keys={'TIME':{'cpu_ns','wall_ns','cpu_resolution_ns','wall_resolution_ns'}}
 if diagnostic:
  numeric_keys.update(WORK={'shadow_iterations','active_initializations','active_reads','active_deletions','memmove_calls','memmove_bytes','compaction_copies'},PATH={'orders_indexed','orders_unique','admitted','indexed_calls'})
 for key,expected in numeric_keys.items():
  need(set(fields[key])==expected,'complete '+key+' fields')
  need(all(re.fullmatch(r'[0-9]+',v)for v in fields[key].values()),'unsigned numeric '+key)
 kind=case.removeprefix('unique-')
 expected_faces=2 if kind in ('dense','fallback-dense')else (n-1)*2 if kind=='few'else n*2
 fields['FACE']=[line for line in lines if line.startswith('FACE ')]
 need(len(fields['FACE'])==expected_faces,'complete expected FACE row count')
 for line in fields['FACE']:
  values=line.split()[1:]
  need(len(values)==9 and all(re.fullmatch(r'-?[0-9]+',v)for v in values),'nine numeric FACE fields')
  need(all(re.fullmatch(r'[0-9]+',values[i])for i in (1,2)),'unsigned FACE identifiers')
 return fields

def plan():
 return dict(source_sha=SOURCE,scope='F8 legacy fallback only; does not discharge historical whole-341 B1',variants=VARIANTS,
   positive_cases=POSITIVE,cases=CASES,warmup_triplets=1,scored_triplets=7,alternating_order=True,
   collects_per_sample=1,compile_timeout=300,run_timeout=20,compiler_flags=['-std=c11','-O2','-Werror=implicit-function-declaration'],
   timing_scope='uninstrumented O2 full collect; fixture creation and output outside timers',
   performance_thresholds_added=False,Sc493_whole_withdrawal_executed=False)

def validate_plan(d):
 need(d['source_sha']==SOURCE,'exact F8 source identity')
 need(tuple(d['variants'])==VARIANTS,'fixed/withdrawn/restored identities')
 need(tuple(d['positive_cases'])==POSITIVE,'all original eight positive cases')
 need([tuple(x)for x in d['cases']]==CASES,'complete four-class and unique-control inputs')
 need(d['warmup_triplets']==1 and d['scored_triplets']==7 and d['collects_per_sample']==1,'no sample deletion or adaptation')
 need(d['compile_timeout']==300 and d['run_timeout']==20,'original native timeouts')
 need(d['performance_thresholds_added'] is False and d['Sc493_whole_withdrawal_executed'] is False,'do not widen acceptance claims')
 return True

def main():
 validate_plan(plan())
 a=argparse.ArgumentParser();a.add_argument('--owner',type=Path,default=Path('/workspace/geometry-axiom'))
 a.add_argument('--out',type=Path);a.add_argument('--execute',action='store_true');a.add_argument('--root-exclusive-lease',action='store_true')
 a.add_argument('--minimum-free-bytes',type=int,default=134217728);args=a.parse_args()
 if not args.execute:print(json.dumps(plan(),ensure_ascii=False,indent=2));return 0
 need(args.root_exclusive_lease and args.out is not None,'root must supply exclusive lease and fresh OUT')
 owner=args.owner.resolve();out=args.out.resolve()
 need(not out.exists()and out.parent.is_dir()and out.is_relative_to('/tmp'),'fresh /tmp artifact directory')
 need(not out.is_relative_to(owner)and not owner.is_relative_to(out),'no checkout changes')
 need(sys.flags.optimize==0 and args.minimum_free_bytes>=0,'normal Python and explicit resource reserve')
 pins=json.loads((P/'PINS.json').read_text())
 for name,digest in pins.items():need(h((P/name).read_bytes())==digest,'frozen preparation '+name)
 need(h(CAP.read_bytes())==CAP_HASH,'original Recorder')
 locks=[]
 for name in ('heavy.lock','secondary.lock'):
  f=Path('/tmp/g261r3',name).open('a+b');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 fs=os.statvfs(out.parent);need(fs.f_bavail*fs.f_frsize>=args.minimum_free_bytes,'resource reserve unavailable; no compile')
 out.mkdir();(out/'tmp').mkdir();snap=out/'source';snap.mkdir();bins=out/'bins';bins.mkdir()
 env={k:v for k,v in os.environ.items()if not k.startswith(('GIT_','MUTATE_','GEOMETRY_'))and k not in ('PYTHONOPTIMIZE','PYTHONPATH','PYTHONSTARTUP','NODE_OPTIONS','CFLAGS','CPPFLAGS','LDFLAGS')}
 env.update(PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(out/'tmp'),LC_ALL='C.UTF-8',LANG='C.UTF-8')
 spec=importlib.util.spec_from_file_location('original_cost_capture',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
 rec=cap.Recorder(out/'originals',env,SOURCE);report=dict(plan(),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=False,exit=1,commands=[],samples=[],errors=[],source_files=[],elfs=[],formal_acceptance=False)
 def run(argv,cwd=out,timeout=20,check=True):
  row,stdout,stderr=rec.run(list(map(str,argv)),cwd=cwd,timeout=timeout,check=False,source_sha=SOURCE,source_variant='F8 fallback-only cost; retained 343 index; not original whole341')
  report['commands'].append(row)
  if check:need(row['actual_process_returncode']==0,'command failed; original raw retained '+row['directory'])
  return row,stdout,stderr
 def git(*argv):return run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*argv],cwd=owner,timeout=None)[1]
 def build(src,name,diagnostic=False):
  dest=bins/(name+'.o');cmd=[cc,'-std=c11','-O2','-Werror=implicit-function-declaration','-I',kernel,'-I',wood]
  if diagnostic:cmd+=['-DCONTACT_COST_DIAGNOSTICS=1']
  cmd+=['-c',src,'-o',dest];run(cmd,timeout=300);return dest
 def link(name,objects):
  dest=bins/name;run([cc,*objects,'-lm','-o',dest],timeout=300);report['elfs'].append(dict(path=str(dest),bytes=dest.stat().st_size,sha256=h(dest.read_bytes())));return dest
 try:
  need(git('rev-parse',SOURCE+'^{commit}').decode().strip()==SOURCE,'public fixed source')
  raw=git('ls-tree','-r','-z','--name-only',SOURCE,'--','geometry-core/kernel','geometry-templates/woodworking/native','tests/geo261_contact_world_harness.c','tests/test_geo261_native_kernel.py')
  names=[]
  for path in raw.decode().strip('\0').split('\0'):
   if path.startswith('geometry-core/kernel/')and path.endswith(('.c','.h','.inc')):names.append(path)
   elif path.startswith('geometry-templates/woodworking/native/')and(path.endswith(('.h','.inc'))or Path(path).name in ('contacts.c','supports.c','contact_world.c')):names.append(path)
   elif path.startswith('tests/'):names.append(path)
  for name in names:
   data=git('show',SOURCE+':'+name);dest=snap/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
   report['source_files'].append(dict(path=name,bytes=len(data),sha256=h(data)))
  need((snap/LEAF).read_bytes()==(P/'fixed.c').read_bytes()==(P/'restored.c').read_bytes(),'F8 fixed/restored exact Git bytes')
  kernel=snap/'geometry-core/kernel';wood=snap/'geometry-templates/woodworking/native'
  header=(wood/'contact_world.h').read_text();kh=(kernel/'geometry.h').read_text()
  need('#define WOOD_CONTACT_MEMBER_CAPACITY 64'in header and '#define WOOD_CONTACT_COMPONENT_CAPACITY 8'in header and '#define GEO_LOOP_MAX_VERTICES 32'in kh and '#define GEO_REGION_MAX_HOLES 8'in kh,'F8 capacities drift; no inferred capacity expansion')
  need('#define WOOD_CONTACT_FACE_CAPACITY (WOOD_CONTACT_COMPONENT_CAPACITY*GEO_LOOP_MAX_VERTICES*(GEO_REGION_MAX_HOLES+1)+WOOD_CONTACT_MEMBER_CAPACITY*2)'in header,'exact 2432 face capacity expression')
  soft,hard=resource.getrlimit(resource.RLIMIT_STACK);resource.setrlimit(resource.RLIMIT_STACK,(16777216,hard));report['stack_limit']=list(resource.getrlimit(resource.RLIMIT_STACK))
  cc=shutil.which('cc');need(cc,'compiler available');run([cc,'--version']);run(['uname','-a']);run([sys.executable,'--version'])
  common=[build(kernel/(name+'.c'),'kernel-'+name)for name in KERNEL]
  common += [build(wood/(name+'.c'),'wood-'+name)for name in ('contacts','supports')]
  client=build(snap/'tests/geo261_contact_world_harness.c','original-positive-client')
  timing_client=build(P/'cost_harness.c','uninstrumented-cost-client')
  diagnostic_client=build(P/'cost_harness.c','diagnostic-cost-client',True)
  executables={}
  for variant in VARIANTS:
   obj=build(P/(variant+'.c'),variant+'-product');diag=build(P/(variant+'-diagnostic.c'),variant+'-diagnostic')
   original=link(variant+'-positive',[client,obj,*common])
   executables[variant]=(link(variant+'-cost',[timing_client,obj,*common]),link(variant+'-diagnostic',[diagnostic_client,diag,*common]))
   for case in POSITIVE:
    row,_,stderr=run([original,case],check=False)
    if row['actual_process_returncode']!=0:report['errors'].append(dict(scope='original positive',variant=variant,case=case,command=row['directory']))
  for case,n in CASES:
   diagnostics={};reference=None
   for variant in VARIANTS:
    row,stdout,stderr=run([executables[variant][1],case,n],check=False)
    if row['actual_process_returncode']!=0:report['errors'].append(dict(scope='diagnostic',variant=variant,case=case,n=n,command=row['directory']));continue
    fields=inspect_output(stdout,True,case,n);diagnostics[variant]=fields;reference=reference or fields['FACE']
    need(fields['FACE']==reference,'diagnostic exact sequence mismatch')
    report['samples'].append(dict(kind='diagnostic-not-performance',case=case,n=n,variant=variant,fields=fields,command=row['directory']))
   if set(diagnostics)==set(VARIANTS):need(diagnostics['fixed']['WORK']==diagnostics['restored']['WORK'],'restored exact work differs')
   for round_no in range(8):
    order=VARIANTS if round_no%2==0 else tuple(reversed(VARIANTS))
    for variant in order:
     row,stdout,stderr=run([executables[variant][0],case,n],check=False)
     if row['actual_process_returncode']!=0:report['errors'].append(dict(scope='timing',round=round_no,variant=variant,case=case,n=n,command=row['directory']));continue
     fields=inspect_output(stdout,False,case,n);need(reference is not None and fields['FACE']==reference,'uninstrumented exact sequence mismatch')
     report['samples'].append(dict(kind='warmup'if round_no==0 else 'scored',round=round_no,case=case,n=n,variant=variant,fields=fields,command=row['directory']))
  report['medians']=[]
  for case,n in CASES:
   values={v:{metric:[int(s['fields']['TIME'][metric])for s in report['samples']if s['kind']=='scored'and s['case']==case and s['n']==n and s['variant']==v]for metric in ('cpu_ns','wall_ns')}for v in VARIANTS}
   need(all(len(xs)==7 for v in values.values()for xs in v.values()),'all seven samples retained')
   report['medians'].append(dict(case=case,n=n,values={v:{m:statistics.median(xs)for m,xs in d.items()}for v,d in values.items()},scope='measurement only; no new performance pass threshold'))
  need(not report['errors'],'one or more original semantic/measurement runs failed')
  report.update(passed=True,exit=0,semantic_passed=True,performance_acceptance_decided=False)
 except BaseException as exc:report['error']=repr(exc)
 finally:
  report['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();dump(out/'RESULT.json',report)
  for lock in reversed(locks):lock.close()
 print(json.dumps({k:report.get(k)for k in ('source_sha','scope','exit','passed','error','performance_acceptance_decided')},ensure_ascii=False));return report['exit']
if __name__=='__main__':raise SystemExit(main())
