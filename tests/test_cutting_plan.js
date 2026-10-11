const {test}=require('node:test'),assert=require('node:assert/strict');
const C=require('../geometry-web/cutting-plan.js'),S=require('../geometry-web/cutting-settings.js');
const material={id:'wood',version:1,fingerprint:'b'.repeat(64)};
const timber=(id,L,surface=1,A=27,B=33)=>({id,role:'primary',geometry:{surface,A,B,length:L,dir:'+v',side:'+n',origin:[0,0,0],axes:[[0,1,0],[1,0,0],[0,0,1]]}});
const refs=(lengths)=>({ok:true,sourceFingerprint:'a'.repeat(64),timbers:lengths.map((L,i)=>timber(i+1,L)),engineeringSources:[]});
const settings=(length=3636,endTrim=5)=>({kerf:3,allowance:0,minRemnant:300,stockTypes:[{key:1,name:'試用料',section:[27,33],material:null,length,endTrim}],remnants:[],nextStockKey:2,nextRemnantKey:1});
const request=(scopes=[{surface:1,ids:null}])=>({world:{kind:'live'},scopes});
const evaluate=(r,s=settings(),q=request())=>C.evaluate(r,s,q);
function source(r,id,terminal,field='A'){r.engineeringSources.push({target:{kind:'timber',id,field},terminal,path:'不可解析的顯示文字'});}
function diagnostic(p,status,code){assert.equal(p.status,status,code+' severity');assert.ok(p.diagnostics.some(d=>d.code===code),code+' missing');assert.deepEqual(p.groups,[],code+' must not leak a partial plan');}
test('T1 exact FFD coordinates, procurement, kerf and both leftover classes',async()=>{
 const p=await evaluate(refs([2560,2560,890,890,890,876]));assert.equal(p.status,'COMPLETE');const g=p.groups[0];assert.equal(g.newStockCount,3);
 assert.deepEqual(g.stocks.map(s=>s.pieces.map(p=>[p.timberId,p.start,p.end])),[[[1,5,2565],[3,2568,3458]],[[2,5,2565],[4,2568,3458]],[[5,5,895],[6,898,1774]]]);
 assert.deepEqual(g.stocks.map(s=>[s.cuts,s.tail.consumed,s.leftover]),[[3,3,{length:175,usable:170,class:'waste'}],[3,3,{length:175,usable:170,class:'waste'}],[3,3,{length:1859,usable:1854,class:'reusable'}]]);
 assert.equal(g.kerfLoss,18);assert.equal(g.trimLoss,15);
});
test('T2 T3 T3b original end, shortened last kerf, and last-cut expectation',async()=>{
 for(const [last,tail,cuts,left]of [[1497,{kind:'none',consumed:0,cuts:0},1,null],[1496,{kind:'separate',consumed:1,cuts:1},2,null],[1490,{kind:'separate',consumed:3,cuts:1},2,{length:4,usable:4,class:'waste'}]]){
  const p=await evaluate(refs([1500,last]),settings(3000,0));assert.equal(p.groups[0].newStockCount,1);const s=p.groups[0].stocks[0];assert.deepEqual(s.tail,tail);assert.equal(s.cuts,cuts);assert.deepEqual(s.leftover,left);
 }
});
test('T4 T11 T13 T25 finish trim, allowance, usable threshold and nonnegative usable',async()=>{
 const p=await evaluate(refs([3626]));assert.deepEqual(p.groups[0].stocks[0].tail,{kind:'trim',consumed:5,cuts:1});assert.equal(p.groups[0].stocks[0].cuts,2);assert.equal(p.groups[0].stocks[0].leftover,null);
 const s=settings();s.allowance=10;const a=await evaluate(refs([890]),s);assert.deepEqual([a.groups[0].stocks[0].pieces[0].L,a.groups[0].stocks[0].pieces[0].allowance,a.groups[0].stocks[0].pieces[0].C],[890,10,900]);
 for(const [L,usable,kind]of [[3323,300,'reusable'],[3324,299,'waste']])assert.deepEqual((await evaluate(refs([L]))).groups[0].stocks[0].leftover,{length:usable+5,usable,class:kind});
 assert.deepEqual((await evaluate(refs([2989]),settings(3000,5))).groups[0].stocks[0].leftover,{length:3,usable:0,class:'waste'});
});
test('T5 T5b smallest usable remnant first; unused remnants have no cuts or CSV rows',async()=>{
 const s=settings();s.remnants=[{key:1,stockType:1,length:1000,headTrim:0,tailTrim:5},{key:2,stockType:1,length:600,headTrim:0,tailTrim:5}];s.nextRemnantKey=3;
 const p=await evaluate(refs([900,590]),s),g=p.groups[0];assert.equal(g.newStockCount,0);assert.deepEqual(g.stocks.map(s=>s.label),['R2','R1']);assert.deepEqual(g.stocks.map(s=>s.leftover.usable),[2,92]);
 const one=await evaluate(refs([500]),s);assert.deepEqual(one.groups[0].unusedRemnants,[1]);assert.equal(one.groups[0].stocks[0].label,'R2');assert.ok(!C.csv(one).includes('"R1"'));
});
test('T6 T6b union uses timber identity including zero, never dimensions',async()=>{
 const r=refs([890,890,890]);r.timbers.push(timber(7,890,2),timber(0,890));const p=await evaluate(r,settings(),request([{surface:1,ids:null},{surface:1,ids:[2]},{surface:2,ids:[7]}]));
 assert.deepEqual(p.groups[0].stocks.flatMap(s=>s.pieces.map(p=>p.timberId)).sort((a,b)=>a-b),[0,1,2,3,7]);
});
test('T7 T18 T21 T22 request phases reject wrong world, capacities, stale selection, and empty scope',async()=>{
 assert.equal((await evaluate(null,settings(),request([]))).status,'EMPTY');diagnostic(await evaluate(refs([1]),settings(),{world:{kind:'model:1'},scopes:[{surface:1,ids:null}]}),'UNSUPPORTED','WORLD_KIND');
 diagnostic(await evaluate(refs([1]),settings(),request(Array.from({length:65},()=>({surface:1,ids:null})))),'UNSUPPORTED','CAPACITY');diagnostic(await evaluate(refs(Array(4097).fill(1))),'UNSUPPORTED','CAPACITY');
 for(const ids of [[9],[3]])diagnostic(await evaluate(refs([1,2]),settings(),request([{surface:1,ids}])),'INVALID','SCOPE_STALE');
 diagnostic(await evaluate(refs([])),'INCOMPLETE','SCOPE_EMPTY');diagnostic(await evaluate({...refs([1]),ok:false}),'INCOMPLETE','WORLD_UNREADABLE');
});
test('T8 T8b T9 material triplets and unordered section determine stock, never path',async()=>{
 const r=refs([100,100]);source(r,1,{kind:'material',...material});source(r,1,{kind:'material',...material},'B');r.timbers[0].geometry.A=33;r.timbers[0].geometry.B=27;
 const s=settings();s.stockTypes.push({...s.stockTypes[0],key:2,material});s.nextStockKey=3;
 const p=await evaluate(r,s);assert.deepEqual(p.groups.map(g=>[g.stockTypeKey,g.stocks[0].pieces[0].timberId]),[[1,2],[2,1]]);
 const missing=await evaluate(r);diagnostic(missing,'INCOMPLETE','NO_STOCK');assert.ok(JSON.stringify(missing.diagnostics).includes(material.fingerprint));
});
test('T10 T10b T10c unresolved, mixed and missing terminal remain distinct',async()=>{
 for(const [terminal,status,code]of [[null,'INCOMPLETE','MATERIAL_UNRESOLVED'],[{kind:'material',...material},'INCOMPLETE','MATERIAL_MIXED'],[undefined,'UNSUPPORTED','NATIVE_CAPABILITY']]){
  const r=refs([100]);source(r,1,terminal);if(terminal===undefined)delete r.engineeringSources[0].terminal;diagnostic(await evaluate(r),status,code);
 }
});
test('T15 T15b canonical settings, candidate order and CSV ignore input/view ordering',async()=>{
 const r=refs([2560,2560,890,890,890,876]),s=settings(),q=request([{surface:1,ids:[6,4,2]},{surface:1,ids:[1,3,5]}]);const a=await evaluate(r,s,q);
 r.timbers.reverse();q.scopes.reverse();q.scopes.forEach(s=>s.ids.reverse());const b=await evaluate(r,JSON.parse(JSON.stringify(s)),q);assert.deepEqual(a,b);assert.equal(C.csv(a,'length'),C.csv(b,'id'));
 const crypto=require('node:crypto');assert.equal(a.settingsFingerprint,crypto.createHash('sha256').update(S.canonical(s),'utf8').digest('hex'));
});
test('T19 T28 missing settings follow overlength diagnostics and severity',async()=>{
 for(const field of ['kerf','allowance','minRemnant']){const s=settings();s[field]=null;const p=await evaluate(refs([3700]),s);diagnostic(p,'INVALID','OVER_LENGTH');assert.ok(p.diagnostics.some(d=>d.code==='MISSING_SETTING'));}
 const s=settings();s.allowance=null;diagnostic(await evaluate(refs([1000]),s),'INCOMPLETE','MISSING_SETTING');
});
test('T23 T23b exhaustion is per-group first failure, and overlength considers every remnant',async()=>{
 const s=settings(3000,5);s.remnants=[{key:1,stockType:1,length:3300,headTrim:0,tailTrim:5}];s.nextRemnantKey=2;
 const p=await evaluate(refs([3200,3100]),s);diagnostic(p,'INCOMPLETE','REMNANT_EXHAUSTED');assert.equal(p.diagnostics.length,1);assert.ok(!p.diagnostics.some(d=>d.code==='OVER_LENGTH'));
 diagnostic(await evaluate(refs([3296]),s),'INVALID','OVER_LENGTH');
});
test('T26 T27 fingerprint mismatch precedes section mismatch; unnamed material is not inferred',async()=>{
 const r=refs([100]);source(r,1,{kind:'material',...material});source(r,1,{kind:'material',...material},'B');const s=settings();s.stockTypes[0].material={...material,fingerprint:'c'.repeat(64)};
 diagnostic(await evaluate(r,s),'INCOMPLETE','MATERIAL_FINGERPRINT_MISMATCH');s.stockTypes[0].material=material;s.stockTypes[0].section=[30,36];diagnostic(await evaluate(r,s),'INCOMPLETE','STOCK_SECTION_MISMATCH');
});
test('typed derive errors preserve old messages; no empty-scope second diagnosis',async()=>{
 const r=refs([100]);r.timbers[0].geometry.A=0;const p=await evaluate(r);diagnostic(p,'INCOMPLETE','ROW_NOT_READY:NOT_EVALUATED');assert.equal(p.diagnostics.length,1);
});
test('conservation detects corrupted positions and repeated demand identity',async()=>{
 const p=await evaluate(refs([2560,2560,890,890,890,876]));assert.equal(C.verify(p),true);
 const a=structuredClone(p);a.groups[0].stocks[0].pieces[0].end++;assert.throws(()=>C.verify(a),/CONSERVATION/);
 const b=structuredClone(p);b.groups[0].stocks[0].pieces[1].timberId=1;assert.throws(()=>C.verify(b),/DEMAND_IDENTITY/);
});
test('E1 E2 engineering proposal lengths produce overlength or six exact stocks',async()=>{
 const r=refs([4000,4000,2946,2946,2946,1960,1959]);r.timbers.forEach((t,i)=>t.id=[10,11,12,13,20,30,31][i]);
 for(const t of r.timbers)for(const field of ['A','B'])source(r,t.id,{kind:'material',...material},field);
 const s=settings();s.stockTypes[0].material=material;const short=await evaluate(r,s);diagnostic(short,'INVALID','OVER_LENGTH');assert.deepEqual(short.diagnostics.map(d=>d.detail.timberId),[10,11]);
 s.stockTypes[0].length=4200;const p=await evaluate(r,s),g=p.groups[0];assert.equal(p.status,'COMPLETE');assert.equal(g.newStockCount,6);
 assert.deepEqual(g.stocks.map(s=>s.pieces.map(p=>[p.timberId,p.start,p.end])),[[[10,5,4005]],[[11,5,4005]],[[12,5,2951]],[[13,5,2951]],[[20,5,2951]],[[30,5,1965],[31,1968,3927]]]);
 assert.deepEqual(g.stocks.map(s=>[s.leftover.length,s.leftover.usable,s.leftover.class]),[[192,187,'waste'],[192,187,'waste'],[1246,1241,'reusable'],[1246,1241,'reusable'],[1246,1241,'reusable'],[270,265,'waste']]);
});
test('CSV fixed 30 columns, empty end/piece cells, mm, escaping; all computation is read-only',async()=>{
 const r=refs([3626]),s=settings();s.stockTypes[0].name=' =HYPERLINK("x")\n木材';const before=JSON.stringify([r,s]);const p=await evaluate(r,s),csv=C.csv(p),lines=csv.trimEnd().split('\r\n');
 assert.ok(csv.startsWith('\ufeff"row_kind"'));assert.equal(lines.length,3);assert.ok(csv.includes('"\' =HYPERLINK(""x"")\n木材"'));assert.ok(csv.endsWith(',"","",""\r\n'));assert.equal(JSON.stringify([r,s]),before);
 assert.throws(()=>C.csv({status:'INCOMPLETE'}),/COMPLETE/);
});
test('F4a CSV byte equality removes terminal while owned rows retain the native slot terminal',async()=>{
 const T=require('../geometry-web/timber-schedule.js'),r=refs([100]);source(r,1,{kind:'literal'});const legacy=structuredClone(r);delete legacy.engineeringSources[0].terminal;
 assert.equal(T.csv(T.derive(r,1)),T.csv(T.derive(legacy,1)));
 r.assembly={instances:[{value:{source:{id:4,bindingId:9,rule:{id:7,version:2,fingerprint:'b'.repeat(64)}}},members:[{memberId:12,timberId:1}]}],rules:[{value:{id:7,version:2,members:[{id:12,slotId:5}]},fingerprint:'b'.repeat(64)}],bindings:[{value:{id:9,slots:[{slotId:5,A:{kind:'material',id:material.id,version:1},B:{kind:'material',id:material.id,version:1}}]},complete:true,fingerprint:'c'.repeat(64),effective:[{slotId:5,A:{value:27,path:'不可解析的來源',terminal:{kind:'material',...material}},B:{value:33,path:'不可解析的來源',terminal:{kind:'material',...material}}}]}]};
 const s=settings();s.stockTypes[0].material=material;assert.equal((await evaluate(r,s)).status,'COMPLETE');
 const old=structuredClone(r);for(const axis of ['A','B'])delete old.assembly.bindings[0].effective[0][axis].terminal;assert.equal(T.csv(T.derive(r,1)),T.csv(T.derive(old,1)));diagnostic(await evaluate(old,s),'UNSUPPORTED','NATIVE_CAPABILITY');
});
test('R1.1 each exhausted material group contributes its first unplaced demand',async()=>{
 const r=refs([3200,3100,3200,3100]),s=settings(3000,5);for(const id of [3,4])for(const field of ['A','B'])source(r,id,{kind:'material',...material},field);
 s.stockTypes.push({...s.stockTypes[0],key:2,material});s.nextStockKey=3;s.remnants=[{key:1,stockType:1,length:3300,headTrim:0,tailTrim:5},{key:2,stockType:2,length:3300,headTrim:0,tailTrim:5}];s.nextRemnantKey=3;
 const p=await evaluate(r,s);diagnostic(p,'INCOMPLETE','REMNANT_EXHAUSTED');assert.deepEqual(p.diagnostics.map(d=>[d.detail.stockTypeKey,d.detail.timberId]),[[1,2],[2,4]]);
});
