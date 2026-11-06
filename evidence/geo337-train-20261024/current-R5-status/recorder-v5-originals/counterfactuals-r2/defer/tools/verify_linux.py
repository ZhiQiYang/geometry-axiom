import argparse, gzip, hashlib, json, os, re, resource, shutil, statistics, subprocess, sys, time
from pathlib import Path
from geo323_record import recorded_run

TRACE = r'''
static unsigned long long residual_guards[5];
static void residual_finish(void)
{
    const char *path=getenv("GEO261_GUARDS");if(!path)return;
    FILE *f=fopen(path,"w");if(!f)exit(92);
    for(unsigned i=0;i<5;++i)fprintf(f,"%llu\n",residual_guards[i]);
    if(fclose(f))exit(93);
}
static void residual_guard(unsigned i)
{static int ready;if(!ready){ready=1;atexit(residual_finish);}++residual_guards[i];}
/* 固定以小端序整數寫出；借用的 view 逐項寫內容，不寫入指標、
 * C 結構填補位元組或未使用的 union 儲存區。 */
static void rt_n(FILE *f,uint64_t n)
{for(unsigned i=0;i<8;++i){if(fputc((unsigned char)(n>>(8*i)),f)==EOF)exit(94);}}
static void rt_bytes(FILE *f,const void *p,size_t n)
{rt_n(f,n);if(n&&fwrite(p,1,n,f)!=n)exit(95);}
static void rt_context(FILE *f,GeoSourceContext c)
{rt_n(f,c.has_placement);rt_n(f,c.placement);rt_n(f,(uint64_t)c.axis);}
static void rt_point(FILE *f,GeoPoint3 p)
{rt_n(f,(uint64_t)p.x);rt_n(f,(uint64_t)p.y);rt_n(f,(uint64_t)p.z);}
static void rt_frame(FILE *f,GeoFrame v)
{rt_point(f,v.origin);rt_point(f,(GeoPoint3){v.axis_u.x,v.axis_u.y,v.axis_u.z});rt_point(f,(GeoPoint3){v.axis_v.x,v.axis_v.y,v.axis_v.z});rt_point(f,(GeoPoint3){v.normal.x,v.normal.y,v.normal.z});}
static void rt_loop(FILE *f,GeoLoop2View v)
{rt_n(f,v.count);for(size_t i=0;i<v.count;++i){rt_n(f,(uint64_t)v.v[i].u);rt_n(f,(uint64_t)v.v[i].v);}}
static void rt_value(FILE *f,const GeoSourceValue *v)
{
    rt_n(f,v!=NULL);if(!v)return;rt_n(f,v->kind);
    switch(v->kind){
    case GEO_SOURCE_QUANTITY:rt_n(f,(uint64_t)v->as.quantity.num);rt_n(f,(uint64_t)v->as.quantity.den);rt_n(f,v->as.quantity.unit);break;
    case GEO_SOURCE_AXIS_POSITION:rt_n(f,(uint64_t)v->as.position.coordinate);rt_context(f,v->as.position.context);break;
    case GEO_SOURCE_FRAME:rt_frame(f,v->as.frame);break;
    case GEO_SOURCE_BOX:rt_frame(f,v->as.box.frame);for(unsigned i=0;i<3;++i)rt_n(f,(uint64_t)v->as.box.extent[i]);break;
    case GEO_SOURCE_REGION_SET:
        rt_n(f,v->as.regions.count);
        for(size_t i=0;i<v->as.regions.count;++i){const GeoRegionView *r=&v->as.regions.regions[i];
            rt_loop(f,r->outline);rt_n(f,r->hole_count);for(size_t j=0;j<r->hole_count;++j)rt_loop(f,r->holes[j]);}break;
    case GEO_SOURCE_FEATURE:rt_bytes(f,v->as.feature.key,v->as.feature.key_size);rt_point(f,v->as.feature.segment.start);rt_point(f,v->as.feature.segment.end);break;
    case GEO_SOURCE_DEFINITION:rt_n(f,v->as.definition.schema!=NULL);if(v->as.definition.schema)rt_bytes(f,v->as.definition.schema,strlen(v->as.definition.schema));
        rt_bytes(f,v->as.definition.content,v->as.definition.content_size);break;
    default:exit(96);
    }
}
static void residual_trace_seal(const GeoEvalContext *ctx)
{
    const char *path=getenv("GEO261_GRAPH");if(!path)return;
    FILE *f=fopen(path,"ab");if(!f)exit(91);
    rt_n(f,UINT64_C(0x5345414c));rt_n(f,ctx!=NULL);
    if(ctx){
        rt_n(f,geo_eval_candidate_id(ctx));rt_n(f,geo_eval_base_revision(ctx));rt_n(f,geo_eval_is_sealed(ctx));
        rt_n(f,geo_eval_node_count(ctx));rt_n(f,geo_eval_edge_count(ctx));
        for(size_t i=0;i<geo_eval_node_count(ctx);++i){GeoSourceNodeView n;if(!geo_eval_node_at(ctx,i,&n))exit(97);
            rt_n(f,n.source.provider);rt_bytes(f,n.source.key,n.source.key_size);
            rt_n(f,n.descriptor.kind);rt_n(f,n.descriptor.unit);rt_context(f,n.descriptor.context);
            rt_n(f,n.descriptor.retry_failure);rt_n(f,n.descriptor.context_from_value);
            rt_n(f,n.state);rt_n(f,n.status);rt_n(f,n.described);rt_value(f,n.value);
        }
        for(size_t i=0;i<geo_eval_edge_count(ctx);++i){GeoSourceEdge e;if(!geo_eval_edge_at(ctx,i,&e))exit(98);
            rt_n(f,e.consumer);rt_n(f,e.source);rt_n(f,e.kind);}
    }
    if(fclose(f))exit(99);
}
'''
GUARDS = ['app_world_candidate_create','app_world_candidate_seal','app_world_candidate_publish','app_world_candidate_revalidate','reference_check_all']

def once(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)

def closure(root, dest, entry):
    seen=set()
    def copy(path):
        path=path.resolve()
        if path in seen:return
        seen.add(path)
        data=path.read_bytes()
        target=dest/path.relative_to(root)
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        for inc in re.findall(rb'^\s*#\s*include\s*"([^"\r\n]+)"',data,re.M):
            child=path.parent/os.fsdecode(inc)
            if child.is_file():copy(child)
    copy(root/entry)
    return seen

def build(root, work, trace=False, profile=False):
    root=root.resolve();work.mkdir(parents=True,exist_ok=True)
    tree=root
    if trace:
        tree=work/'source';closure(root,tree,'geometry-web/web_bridge.c')
        for rel, names in [('geometry-app/native/world_candidate.inc',GUARDS[:3]),('current_geometry.c',[GUARDS[3]]),('geometry-core/references.inc',[GUARDS[4]]),('geometry-core/kernel/source.c',['geo_eval_seal'])]:
            p=tree/rel;s=p.read_bytes()
            for name in names:
                pattern=rb'\b'+name.encode()+rb'\s*\([^;{}]*\)\s*\{'
                matches=list(re.finditer(pattern,s));assert len(matches)==1,(name,len(matches))
                at=matches[0].end()
                hook='residual_trace_seal(ctx);' if name=='geo_eval_seal' else 'residual_guard(%d);'%GUARDS.index(name)
                s=s[:at]+hook.encode()+s[at:]
            p.write_bytes(s)
        p=tree/'geometry-web/web_bridge.c'
        pre=b'struct GeoEvalContext;static void residual_trace_seal(const struct GeoEvalContext *);static void residual_guard(unsigned);\n'
        p.write_bytes(pre+p.read_bytes()+TRACE.encode())
    cmd=['gcc','-std=c11',*(['-O1','-fno-inline','-pg'] if profile else ['-O2']),str(tree/'geometry-web/web_bridge.c'),'-o',str(work/'bridge'),'-lm']
    r=recorded_run(cmd,cwd=root,capture_output=True)
    log={'command':cmd,'cwd':str(root),'exit':r.returncode,'stdout':r.stdout.decode(errors='replace'),'stderr':r.stderr.decode(errors='replace')}
    (work/'build.json').write_text(json.dumps(log,ensure_ascii=False,indent=2))
    assert r.returncode==0,log
    print('BUILD',root, 'trace' if trace else 'profile' if profile else 'O2','exit=0',flush=True)
    return work/'bridge'

def stack():
    soft,hard=resource.getrlimit(resource.RLIMIT_STACK)
    if hard!=resource.RLIM_INFINITY and hard<16777216:raise RuntimeError("環境 hard stack 小於16MiB")
    resource.setrlimit(resource.RLIMIT_STACK,(16777216,hard))
def run(exe,scene,cwd,dump=True,env=None):
    command=f'loadfile {scene}\n'+('dump\n' if dump else '')
    start=time.perf_counter()
    r=recorded_run([str(exe)],input=command.encode(),capture_output=True,cwd=cwd,env=env,preexec_fn=stack,timeout=600)
    return r,time.perf_counter()-start,command
def sha(data):return hashlib.sha256(data).hexdigest()

def compare(root,work,evidence):
    evidence.mkdir(parents=True,exist_ok=True)
    inventory=json.loads((evidence/'scene-inventory.json').read_text())
    fixed_names=sorted(s['name'] for s in inventory['scenes'] if 'generated_n' not in s)
    assert len(fixed_names)==171 and len(set(fixed_names))==171
    scenes=[root/name for name in fixed_names]+sorted((evidence/'scenes').glob('s*.scene'))
    rows=[];failures=[]
    for i,scene in enumerate(scenes):
        pair={};key=scene.name
        for version in ['base','fix']:
            r,seconds,command=run(work/version/'bridge',scene,root)
            out=evidence/'stdout'/version;out.mkdir(parents=True,exist_ok=True)
            (out/(key+'.stdout')).write_bytes(r.stdout);(out/(key+'.stderr')).write_bytes(r.stderr)
            row={'scene':key,'path':str(scene),'version':version,'command':command,'exit':r.returncode,'stdout_bytes':len(r.stdout),'stdout_sha256':sha(r.stdout),'stderr_bytes':len(r.stderr)}
            assert r.returncode==0,row
            env=os.environ.copy();graph=work/(version+'-graph.bin');guards=work/(version+'-guards.txt')
            graph.unlink(missing_ok=True);guards.unlink(missing_ok=True)
            env.update(GEO261_GRAPH=str(graph),GEO261_GUARDS=str(guards))
            t,_,_=run(work/(version+'-trace')/'bridge',scene,root,env=env)
            assert t.returncode==0 and t.stdout==r.stdout and t.stderr==r.stderr,(key,version,'instrumentation changed observable output')
            data=graph.read_bytes() if graph.exists() else b''
            counts=list(map(int,guards.read_text().split())) if guards.exists() else [0]*5
            row.update(trace_exit=t.returncode,graph_bytes=len(data),graph_sha256=sha(data),guards=dict(zip(GUARDS,counts)))
            out=evidence/'graphs'/version;out.mkdir(parents=True,exist_ok=True)
            (out/(key+'.bin.gz')).write_bytes(gzip.compress(data,mtime=0))
            pair[version]=(r.stdout,data,counts);rows.append(row)
        a,b=pair['base'],pair['fix']
        for n,label in enumerate(['stdout','source graph (possible cross-consumer dependency loss)','guard traffic']):
            if a[n]!=b[n]:failures.append([key,label])
        if i%10==0 or i==len(scenes)-1:print('COMPARE',i+1,'/',len(scenes),'failures',len(failures),flush=True)
        (evidence/'equivalence.json').write_text(json.dumps({'scenes':len(scenes),'failures':failures,'runs':rows},ensure_ascii=False,indent=2))
    assert not failures,failures
    print('PASS A/B/C:',len(scenes),'scenes; byte-identical stdout, full ordered graphs at every seal, all five guard counts',flush=True)

def perf(root,work,evidence):
    rows=[]
    for n in [16,32,48,64]:
        scene=evidence/'scenes'/f's{n}.scene'
        for round in range(3):
            for version in ['base','fix','main']:
                r,sec,cmd=run(work/version/'bridge',scene,root,False)
                out=evidence/'performance-stdout';out.mkdir(exist_ok=True)
                (out/f'{version}-{n}-{round+1}.stdout').write_bytes(r.stdout)
                (out/f'{version}-{n}-{round+1}.stderr').write_bytes(r.stderr)
                row={'n':n,'round':round+1,'version':version,'seconds':sec,'command':cmd,'exit':r.returncode,'stdout_sha256':sha(r.stdout)}
                assert r.returncode==0 and json.loads(r.stdout)['ok'],(row,r.stdout,r.stderr)
                rows.append(row);print('PERF',n,round+1,version,round_num(sec),flush=True)
    medians={}
    for n in [16,32,48,64]:
        med={v:statistics.median(r['seconds'] for r in rows if r['n']==n and r['version']==v) for v in ['base','fix','main']}
        med.update({'fix/main':med['fix']/med['main'],'fix/base':med['fix']/med['base']});medians[n]=med
    (evidence/'performance.json').write_text(json.dumps({'samples':rows,'medians':medians},indent=2))
    print(json.dumps(medians,indent=2),flush=True)

def round_num(n):return format(n,'.6f')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['build','compare','perf']);p.add_argument('root',type=Path);p.add_argument('work',type=Path);p.add_argument('--trace',action='store_true');p.add_argument('--profile',action='store_true');p.add_argument('--evidence',type=Path)
    a=p.parse_args()
    if a.mode=='build':build(a.root,a.work,a.trace,a.profile)
    elif a.mode=='compare':compare(a.root,a.work,a.evidence)
    else:perf(a.root,a.work,a.evidence)
