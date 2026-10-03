const {test}=require('node:test');
const assert=require('node:assert/strict');
const S=require('../geometry-web/source-inspector.js');
const hash=n=>String(n).padStart(64,'0');
const node=(key,n=1)=>({key,definitionFingerprint:hash(n),valueFingerprint:hash(n),label:key});
const edge=(from,to,relation='dimension',field='A',active=true)=>({from,to,relation,field,active});
const graph=(nodes,edges=[],revision=1,complete=true)=>S.index({ok:true,schema:'source-inspector/1',nodes,edges,revision,complete});
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {resolve,promise};};
test('zero field differs from card, namespaces and versions remain distinct',()=>{
  assert.equal(S.key('parameter',0),'parameter:0');assert.equal(S.key('parameter-field',0,0,0),'parameter-field:0:f0');
  assert.notEqual(S.key('material','a',1),S.key('material','a',2));assert.notEqual(S.key('timber',0),S.key('guide',0));
});
test('nearby is bounded with explicit truncation, cycles and missing sources',()=>{
  const nodes=Array.from({length:80},(_,i)=>node('n'+i));const edges=nodes.slice(1).map(n=>edge('n0',n.key));edges.push(edge('n1','n0'),edge('n2','missing'));
  const g=graph(nodes,edges);assert.equal(S.nearby(g,'n0').rows.length,48);assert.equal(S.nearby(g,'n0').truncated,true);
  assert.equal(S.nearby(g,'n2').missing,true);assert.equal(S.nearby(g,'n0',{depth:0}).truncated,true);
  assert.equal(S.nearby(g,'n1',{direction:'uses'}).rows[0].key,'n0');
});
test('parameter card impact follows owned field zero without textual matches',()=>{
  const g=graph([{...node('parameter:0'),kind:'parameter'},node('parameter-field:0:f0'),node('guide:0'),node('parameter:10')],[edge('parameter:0','parameter-field:0:f0','member','field'),edge('guide:0','parameter-field:0:f0')]);
  assert.deepEqual(S.nearby(g,'parameter:0',{direction:'uses'}).rows.map(r=>r.key),['guide:0']);
});
test('only actual closure changes matter; presentation and unrelated nodes do not stale',()=>{
  const a=graph([node('p'),node('x'),node('unrelated')],[edge('p','x')]),b=graph([{...node('p'),label:'renamed'},node('x'),node('unrelated',2)],[edge('p','x')],99);
  assert.equal(S.freshness(a,b,['p']).contentStatus,'consistent');assert.equal(S.freshness(a,b,['p']).status,'unknown');
  const changed=graph([node('p'),node('x',2),node('unrelated')],[edge('p','x')]);assert.equal(S.freshness(a,changed,['p']).status,'changed');
});
test('possible span candidates and RC container membership are not fabricated evaluation dependencies',()=>{
  const column={...node('column:1'),kind:'column'},space={...node('space:1'),kind:'space'};
  const edges=[edge('timber:0','timber:1','span-candidate'),edge(column.key,space.key,'member'),edge(space.key,'boundary:2','member')];
  const before=graph([node('timber:0'),node('timber:1'),column,space,node('boundary:2')],edges);
  const now=graph([node('timber:0'),node('timber:1',2),column,space,node('boundary:2',2)],edges);
  assert.equal(S.freshness(before,now,['timber:0',column.key]).contentStatus,'consistent');
  assert.equal(S.nearby(before,'timber:0').rows[0].edge.relation,'span-candidate');
  assert.equal(S.freshness(before,graph([node('timber:0',2),node('timber:1',2),column,space,node('boundary:2',2)],edges),['timber:0']).status,'changed');
});
test('same effective value with different typed source and fixed versions is detected',()=>{
  const n=node('p'),x=node('material:a:v1'),y=node('material:a:v2');const a=graph([n,x,y],[edge('p',x.key)]),b=graph([n,x,y],[edge('p',y.key)]);
  assert.equal(S.freshness(a,b,['p']).changes[0].kind,'source-definition');
  assert.equal(S.freshness(a,graph([n,x,y],[edge('p',x.key),edge('p','ghost','dimension','ignored',false)]),['p']).contentStatus,'consistent');
});
test('missing, incomplete, reused identity and unsupported old model stay explicit',()=>{
  const a=graph([node('p'),node('x')],[edge('p','x')]);assert.equal(S.freshness(a,graph([node('p')]),['p']).status,'missing');
  assert.equal(S.freshness(a,a,['p'],{deleted:new Set(['x'])}).status,'unknown');
  assert.equal(S.freshness(a,graph([node('p'),node('x')],[edge('p','x')],1,false),['p']).contentStatus,'unchecked');
  assert.equal(S.freshness(a,a,[]).status,'unknown');assert.deepEqual(S.modelRoots({source:{kind:'example'}}),[]);
  assert.deepEqual(S.modelRoots({source:{kind:'scene'},input:{mode:'plan',base_scene:'',placement_id:0,obstacles:[],timbers:[{kind:'timber',id:0}]}}),['placement:0','timber:0']);
});
test('late async project switch, source revision change and cancellation never return stale result',async()=>{
  let ctx={},frame=1,revision=1,gate=deferred();const data=()=>graph([node('p')],[],revision).data;
  const session=S.createSession({context:()=>ctx,stamp:()=>frame,read:async()=>data(),readSnapshot:()=>gate.promise});
  let pending=session.inspect({input:{base_scene:''}});await new Promise(r=>setImmediate(r));ctx={};gate.resolve(data());assert.equal(await pending,null);
  gate=deferred();pending=session.inspect({input:{base_scene:''}});await new Promise(r=>setImmediate(r));revision=2;gate.resolve(data());await assert.rejects(pending,/來源已更新/);
  gate=deferred();pending=session.inspect({input:{base_scene:''}});await new Promise(r=>setImmediate(r));session.cancel();gate.resolve(data());assert.equal(await pending,null);
  gate=deferred();pending=session.inspect({input:{base_scene:''}});await new Promise(r=>setImmediate(r));frame++;gate.resolve(data());assert.equal(await pending,null);
});
test('invalid native response or duplicate source identities cannot yield green state',()=>{
  assert.throws(()=>S.index({ok:false}));assert.throws(()=>graph([node('p'),node('p')]));assert.throws(()=>graph([{...node('p'),valueFingerprint:'guessed'}]));
});
