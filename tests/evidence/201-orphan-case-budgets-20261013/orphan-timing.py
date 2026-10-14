import hashlib, json, os, pathlib, resource, signal, subprocess, sys, time

root=pathlib.Path('/tmp/geometry-wake19')
repo=pathlib.Path('/workspace/geometry-axiom')
file=repo/'tests/test_reference_workspace_races.js'
source=file.read_text()
pattern='K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves both single boundaries'
start=source.index("test('"+pattern+"'")
end=source.index("\ntest('K2a B1 previous collection ZIP",start)
part=source[start:end]
assert 'for(const size of [130955,130956])' in part
part=part.replace('    const f=await fixture()', "    const clock=performance.now();console.log('ORPHAN_CASE '+JSON.stringify({pid:process.pid,size,event:'start',monotonic_ms:clock}));\n    const f=await fixture()",1)
part=part.replace('    assert.equal(C.bytes(remaining.drafts[0]),size);', "    console.log('ORPHAN_CASE '+JSON.stringify({pid:process.pid,size,event:'end',monotonic_ms:performance.now(),elapsed_ms:performance.now()-clock}));\n    assert.equal(C.bytes(remaining.drafts[0]),size);",1)
split=part.replace("test('"+pattern+"',async()=>{\n  const C=require('./test_grid_drafts_lifecycle_capacity.js');\n  for(const size of [130955,130956]){", "for(const size of [130955,130956])test(`"+pattern+" ${size}-byte boundary`,async()=>{\n  const C=require('./test_grid_drafts_lifecycle_capacity.js');")
assert split.endswith('  }\n});')
split=split[:-len('  }\n});')]+'});'
records=json.loads((root/'orphan-timing-receipts.json').read_text()) if len(sys.argv)>1 else []
resource.setrlimit(resource.RLIMIT_STACK,(16*1024*1024,resource.getrlimit(resource.RLIMIT_STACK)[1]))
def run(label,text,duty):
    contents=source[:start]+text+source[end:]
    wrapper="const Module=require('node:module'),path=require('node:path');const target="+json.dumps(str(file))+";const m=new Module(target,module);m.filename=target;m.paths=Module._nodeModulePaths(path.dirname(target));m._compile("+json.dumps(contents)+",target);\n"
    p=root/(label+'.cjs');p.write_text(wrapper)
    argv=['node','--test','--test-name-pattern='+pattern,str(p)]
    initial=time.monotonic();events=[]
    with (root/(label+'.stdout')).open('wb')as out,(root/(label+'.stderr')).open('wb')as err:
        child=subprocess.Popen(argv,cwd=repo,env={**os.environ,'GEOMETRY_TEST_BRIDGE':'/tmp/geometry-tests/bridge'},stdout=out,stderr=err,start_new_session=True)
        while child.poll() is None:
            time.sleep(.1*duty)
            if child.poll() is not None:break
            if duty<1:
                try:
                    os.killpg(child.pid,signal.SIGSTOP);events.append({'monotonic':time.monotonic(),'signal':'STOP'})
                    time.sleep(.1*(1-duty));os.killpg(child.pid,signal.SIGCONT);events.append({'monotonic':time.monotonic(),'signal':'CONT'})
                except ProcessLookupError:break
        code=child.wait()
    rec={'label':label,'argv':argv,'pid':child.pid,'exit':code,'seconds':time.monotonic()-initial,'duty':duty,'period_seconds':.1,'source_sha256':hashlib.sha256(contents.encode()).hexdigest(),'wrapper_sha256':hashlib.sha256(wrapper.encode()).hexdigest(),'signals':events}
    records.append(rec);(root/'orphan-timing-receipts.json').write_text(json.dumps(records,indent=2)+'\n')
    text=(root/(label+'.stdout')).read_text();print(label,code,[x for x in text.splitlines()if 'ORPHAN_CASE ' in x or 'timed out' in x],flush=True)
    return code
if len(sys.argv)==1:assert run('orphan-measure',part,1)==0
duty=float(sys.argv[1]) if len(sys.argv)>1 else .7
suffix='-'+str(duty).replace('.','') if len(sys.argv)>1 else ''
if len(sys.argv)>2:suffix+='-'+sys.argv[2]
codes=[run('orphan-throttled-grouped'+suffix,part,duty),run('orphan-throttled-split'+suffix,split,duty),run('orphan-throttled-revert'+suffix,part,duty),run('orphan-throttled-restored'+suffix,split,duty)]
assert codes==[1,0,1,0],codes
