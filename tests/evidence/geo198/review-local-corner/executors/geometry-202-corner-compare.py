import hashlib,json,pathlib,resource,shutil,subprocess,sys,tempfile
root=pathlib.Path.cwd();sys.path.insert(0,str(root));from tests._bridge import BridgeSession
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
phase=sys.argv[1];out=pathlib.Path('/tmp/geometry-202-corner/comparison');out.mkdir(parents=True,exist_ok=True)
source=pathlib.Path('/tmp/geometry-198-review2/comparison/base-bridge') if phase=='base' else pathlib.Path('/tmp/geometry-tests/bridge')
binary=out/(phase+'-bridge');shutil.copy2(source,binary)
if phase=='base':
    binding=json.loads((root/'tests/evidence/geo198/review-b1-m1/comparison/metadata.json').read_text())['base_compilation_receipt']
    assert hashlib.sha256(binary.read_bytes()).hexdigest()==binding['binary_sha256']['bridge']
else:binding=json.loads(pathlib.Path(str(source)+'.fingerprint.json').read_text())
outline='0,10 10,10 10,0 20,0 20,10 30,10 30,20 20,20 20,40 10,40 10,20 0,20'
def cells(verts):
    return {(x,y) for x in range(min(a[0] for a in verts),max(a[0] for a in verts))
            for y in range(min(a[1] for a in verts),max(a[1] for a in verts))
            if sum(a[0]==b[0] and 2*min(a[1],b[1])<2*y+1<2*max(a[1],b[1]) and 2*a[0]>2*x+1
                   for a,b in zip(verts,verts[1:]+verts[:1]))%2}
original=cells([list(map(int,p.split(','))) for p in outline.split()])
rows=[]
for strip in (False,True):
    for prior in (False,True):
        with BridgeSession(str(binary),cwd=root) as s:
            commands=['line reset','line surface 1 origin 0 0 0 u +x v +y outline '+outline,
                      'line beam 1 along y from 10 to 30 at 15 width 10 depth 10 top 0' if strip else 'line column 1 at 10 10 size 10 20 z 0 100']
            if prior:commands+=['line column 2 at 12 2 size 4 4 z 0 100']
            fixtures=[{'command':c,'result':s.send(c)} for c in commands];assert all(x['result']['ok'] for x in fixtures)
            before=s.send('dump');query=s.send('obstacles 1');apply='line apply-proj 1 '+('c2 ' if prior else '')+('b1 cut-strip' if strip else 'c1')
            result=s.send(apply);after=s.send('dump')
            pieces=[{'id':i,'result':s.send('boundary '+str(i))} for i in (1,2)]
            expected=original-{(x,y) for x in range(10,20) for y in range(10,30)}
            if prior:expected-={(x,y) for x in range(12,16) for y in range(2,6)}
            actual=set(); areas=[]
            for piece in pieces:
                if not piece['result']['ok']:continue
                loops=piece['result']['loops']; occupied=cells(loops[0]['verts'])
                for hole in loops[1:]:occupied-=cells(hole['verts'])
                actual|=occupied; areas.append(len(occupied))
            undo=s.send('line undo');undo_dump=s.send('dump');redo=s.send('line redo');redo_dump=s.send('dump')
            with tempfile.TemporaryDirectory() as tmp:
                path=pathlib.Path(tmp)/'after.scene';path.write_text(after['text']);s.send('line reset');reload=s.send('loadfile '+str(path));reopened=s.send('dump')
            row={'strip':strip,'prior_hole':prior,'fixture':fixtures,'query':query,'before':before,'command':apply,'result':result,'after':after,'dump_equal':before['text']==after['text'],'pieces':pieces,'undo':undo,'undo_dump':undo_dump,'redo':redo,'redo_dump':redo_dump,'reload':reload,'reopened':reopened,
                 'geometry':{'original_area':len(original),'expected_area':len(expected),'piece_areas':areas,'actual_union_area':len(actual),'saved_difference_equal':actual==expected,'removed_15_15_retained':(15,15) in actual}}
        row['bridge_returncode']=s.process.returncode;rows.append(row)
meta={'phase':phase,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'source_binding':binding,'source_c_sha256':hashlib.sha256((root/'current_geometry.c').read_bytes()).hexdigest() if phase!='base' else None,'cases':rows}
(out/(phase+'.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print(phase,[(r['strip'],r['prior_hole'],r['result']['ok'],r['dump_equal'],r['geometry']) for r in rows],flush=True)
