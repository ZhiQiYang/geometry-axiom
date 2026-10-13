import concurrent.futures,hashlib,json,pathlib,shutil,subprocess,sys,time
root=pathlib.Path('/workspace/geometry-axiom');out=pathlib.Path('/tmp/geometry-tests/pr190-capacity/final-targeted-v2');out.mkdir(exist_ok=True)
sources=[root/'current_geometry.c']+list(root.glob('*.h'))+list(root.glob('*.inc'))
for folder in ('geometry-core','geometry-web'):
 sources += [p for p in (root/folder).rglob('*') if p.is_file() and p.suffix in ('.c','.h','.inc') and 'vendor' not in p.parts]
snapshot={str(p.relative_to(root)):p.read_bytes() for p in sources}
sha=lambda x:hashlib.sha256(x).hexdigest()
names=['test_name_capacity_is_not_invalid_and_never_commits','test_scene_obstacle_capacity_is_structured_and_atomic','test_scene_name_capacity_preserves_invalid_format_and_world']
inc='geometry-core/finish_surfaces.inc';bridge='geometry-web/web_bridge.c'
specs=[('name-capacity-as-invalid',inc,'if(n>FS_NAME_MAX)return fs_capacity_error(', 'if(n>FS_NAME_MAX)return fs_error('),
 ('scene-count-as-invalid',inc,'if(f.obstacle_count==FS_OBSTACLE_MAX){fs_capacity_error(', 'if(f.obstacle_count==FS_OBSTACLE_MAX){fs_error('),
 ('invalid-name-as-capacity',inc,'return fs_error("D41: finish surface name must be printable UTF-8");i+=k;', 'return fs_capacity_error("D41: finish surface name must be printable UTF-8");i+=k;'),
 ('invalid-reference-as-capacity',inc,'if(!fs_obstacle_parse(t[at],&ref))goto invalid;', 'if(!fs_obstacle_parse(t[at],&ref)){fs_capacity_error("invalid ref");scene_error(path,line_no,g_engineering_error);return false;}'),
 ('stale-scene-kind',bridge,'    g_fs_diagnostic=FS_DIAGNOSTIC_INVALID;\n    bool loaded=parse_scene_file(path,draft);','    bool loaded=parse_scene_file(path,draft);')]
def run(label,argv):
 started=time.time()
 with (out/(label+'.stdout')).open('wb') as a,(out/(label+'.stderr')).open('wb') as b:p=subprocess.run(argv,cwd=root,stdout=a,stderr=b)
 r={'argv':argv,'returncode':p.returncode,'duration_seconds':time.time()-started,'origin':'subprocess.run'}
 (out/(label+'.json')).write_text(json.dumps(r,indent=2)+'\n');return r
def case(spec):
 label,file,old,new=spec;shadow=out/('shadow-'+label);shadow.mkdir(exist_ok=True)
 data=snapshot[file].decode('utf-8');assert data.count(old)==1,(label,data.count(old))
 changed=data.replace(old,new).encode('utf-8')
 for rel,raw in snapshot.items():
    p=shadow/rel;p.parent.mkdir(parents=True,exist_ok=True);data=changed if rel==file else raw
    if label in ('scene-count-as-invalid','lower-capacity-baseline') and rel=='geometry-core/finish_surface_types.h':data=data.replace(b'#define FS_OBSTACLE_MAX 64',b'#define FS_OBSTACLE_MAX 63')
    p.write_bytes(data)
 exe=out/('bridge-'+label)
 c=run(label+'-compile',['cc','-std=c11','-O2',str(shadow/bridge),'-lm','-o',str(exe)])
 if c['returncode']:raise RuntimeError(label+' compile failed')
 r=run(label+'-test',[sys.executable,'/tmp/geometry-190-private-suite.py',str(exe),*names])
 actual=json.loads((out/(label+'-test.stdout')).read_text())
 if label=='lower-capacity-baseline':assert r['returncode']==0 and actual['failures']==actual['errors']==actual['skips']==0
 else:assert r['returncode']==1 and actual['failures']>0 and actual['errors']==actual['skips']==0
 assert all(e['type']=='AssertionError' for e in actual['events'])
 return {'id':label,'file':file,'old':old,'new':new,'original_sha256':sha(snapshot[file]),'mutated_sha256':sha(changed),'binary_sha256':sha(exe.read_bytes()),'compile':c,'test':r,'result':actual,'verdict':'baseline' if label=='lower-capacity-baseline' else 'killed','instrumentation':'FS_OBSTACLE_MAX 64 -> 63 only in private source copy' if label in ('lower-capacity-baseline','scene-count-as-invalid') else None}
baseline=case(('lower-capacity-baseline',inc,'if(n>FS_NAME_MAX)return fs_capacity_error(','if(n>FS_NAME_MAX)return fs_capacity_error('))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(case,specs))
assert all((root/rel).read_bytes()==raw for rel,raw in snapshot.items())
(out/'targeted-mutants.json').write_text(json.dumps({'sources':{k:sha(v) for k,v in snapshot.items()},'repository_restored':True,'lower_capacity_baseline':baseline,'results':results},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'mutants':len(results),'killed':len(results),'repository_restored':True}))
