from pathlib import Path
import json,sys
sys.path.insert(0,'/workspace/geometry-axiom')
from tests._bridge import BridgeSession
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
rows=[]
outline='0,0 100,0 100,100 60,100 60,40 40,40 40,100 0,100'
for name,items,command in [
    ('B1',['column 1 at 45 0 size 10 40 z 0 100','column 2 at 30 50 size 30 30 z 0 100'],'apply-proj 1 c1 c2'),
    ('B1-strip',['beam 2 along x from 30 to 60 at 65 width 30 depth 10 top 100'],'apply-proj 1 b2 cut-strip'),
    ('M1',['beam 1 along x from 30 to 70 at 65 width 30 depth 10 top 100'],'apply-proj 1 b1')]:
    with BridgeSession() as s:
        commands=['line reset','line surface 1 origin 0 0 100 u +x v +y outline '+outline]+['line '+x for x in items]
        fixture=[{'command':c,'response':s.send(c)} for c in commands]
        assert all(c['response']['ok'] for c in fixture)
        query=s.send('obstacles 1');before=s.send('dump');result=s.send('line '+command);after=s.send('dump')
        rows.append({'name':name,'fixture':fixture,'query':query,'command':command,'result':result,'before':before,'after':after,'dump_equal':before['text']==after['text']})
(out/'probe.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
print([(r['name'],r['result']['ok'],r['dump_equal']) for r in rows])
