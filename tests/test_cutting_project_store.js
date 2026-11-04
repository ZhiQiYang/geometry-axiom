const {test}=require('node:test'),assert=require('node:assert/strict');
const P=require('../geometry-web/project-store.js'),S=require('../geometry-web/cutting-settings.js'),zip=require('../geometry-web/vendor/fflate/umd/index.js');
const settings=()=>({kerf:3,allowance:0,minRemnant:300,stockTypes:[{key:1,name:'木材',section:[27,33],material:null,length:3636,endTrim:5}],remnants:[],nextStockKey:2,nextRemnantKey:1});
const record=value=>P.Features.record(S.KIND,value),attachment=value=>({schema:P.Features.SCHEMA,records:[record(value)]});
test('T12 strict settings refuse values without rounding, clamping, ignored keys or defaults',()=>{
 const original=settings();for(const mutate of [s=>s.kerf=0,s=>s.kerf='2.4',s=>s.allowance=-1,s=>s.minRemnant=0,s=>s.kerf=100000001,s=>s.stockTypes[0].length=100000001,s=>s.stockTypes[0].length=10,s=>s.stockTypes[0].name='',s=>s.stockTypes[0].name='木'.repeat(33),s=>s.stockTypes[0].material={id:'wood',version:1,fingerprint:'X'.repeat(64)},s=>s.stockTypes.push({...s.stockTypes[0],key:2,section:[33,27]}),s=>s.remnants=[{key:1,stockType:1,length:10,headTrim:0,tailTrim:10}],s=>s.extra=true,s=>s.nextStockKey=1]){
  const s=structuredClone(original);mutate(s);assert.throws(()=>record(s));assert.deepEqual(original,settings());
 }const unset=settings();unset.kerf=unset.allowance=unset.minRemnant=null;assert.deepEqual(record(unset).value,unset);
});
test('T12b referenced stock section/material locked, but name and new-stock trims editable',()=>{
 const a=settings();a.remnants=[{key:1,stockType:1,length:1000,headTrim:0,tailTrim:5}];a.nextRemnantKey=2;
 for(const mutate of [s=>s.stockTypes[0].section=[30,40],s=>s.stockTypes[0].material={id:'wood',version:1,fingerprint:'a'.repeat(64)}]){const b=structuredClone(a);mutate(b);assert.throws(()=>S.transition(a,b),e=>e.code==='STOCK_TYPE_IN_USE');}
 const b=structuredClone(a);Object.assign(b.stockTypes[0],{name:'另名',length:4000,endTrim:8});assert.deepEqual(S.transition(a,b),b);assert.deepEqual(b.remnants,a.remnants);
});
test('T18 settings capacities reject edit rather than truncating',()=>{
 const s=settings();s.stockTypes=Array.from({length:33},(_,i)=>({...s.stockTypes[0],key:i+1,section:[27+i,33]}));s.nextStockKey=34;assert.throws(()=>record(s),/CAPACITY/);
 const r=settings();r.remnants=Array.from({length:129},(_,i)=>({key:i+1,stockType:1,length:100,headTrim:0,tailTrim:0}));r.nextRemnantKey=130;assert.throws(()=>record(r),/陣列|CAPACITY/);
});
test('T20 a referenced stock cannot be deleted alone; deleting its remnants atomically is allowed',()=>{
 const a=settings();a.remnants=[{key:1,stockType:1,length:100,headTrim:0,tailTrim:0}];a.nextRemnantKey=2;
 const b=structuredClone(a);b.stockTypes=[];assert.throws(()=>S.transition(a,b));b.remnants=[];assert.deepEqual(S.transition(a,b),b);
});
test('key allocation remains exhausted or monotonic; deleted keys cannot be reused',()=>{
 const a=settings();a.nextRemnantKey=3;const b=structuredClone(a);b.remnants=[{key:2,stockType:1,length:100,headTrim:0,tailTrim:0}];assert.throws(()=>S.transition(a,b),/KEY_REUSE/);
 const c=structuredClone(a);c.nextRemnantKey=2;assert.throws(()=>S.transition(a,c),/KEY_HIGHWATER/);
 const max=settings();max.nextRemnantKey=4294967295;const allocated=S.addRemnant(max,{stockType:1,length:100,headTrim:0,tailTrim:0});assert.equal(allocated.remnants[0].key,4294967295);assert.equal(allocated.nextRemnantKey,0);assert.throws(()=>S.addRemnant(allocated,{stockType:1,length:100,headTrim:0,tailTrim:0}),/KEY_EXHAUSTED/);
});
test('P-047(a)(b) remnant undo/redo restore only the edit while counters never rewind',()=>{
 const h=new P.ContextHistory(()=>({sources:new Map(),groups:new Map(),featureAttachments:[record(settings())]}));
 const before=h.snapshot(),first=S.addRemnant(settings(),{stockType:1,length:1000,headTrim:0,tailTrim:5});h.push(before,'local','裁切設定');h.frame.context.featureAttachments=[record(first)];
 assert.equal(h.step('undo'),true);let s=h.frame.context.featureAttachments[0].value;assert.equal(s.remnants.length,0);assert.equal(s.nextRemnantKey,2,'P-047 consumed key must survive undo');
 assert.equal(h.step('redo'),true);s=h.frame.context.featureAttachments[0].value;assert.equal(s.remnants[0].key,1);assert.equal(s.nextRemnantKey,2);
 h.step('undo');s=h.frame.context.featureAttachments[0].value;assert.equal(S.addRemnant(s,{stockType:1,length:100,headTrim:0,tailTrim:0}).remnants[0].key,2);
});
test('P-047(c) unrelated local/core restoration does not change remnant declaration or highwater',()=>{
 const s=S.addRemnant(settings(),{stockType:1,length:1000,headTrim:0,tailTrim:5}),h=new P.ContextHistory(()=>({sources:new Map(),groups:new Map(),models:[],featureAttachments:[record(s)]}));
 const before=JSON.stringify(h.frame.context.featureAttachments);h.changeModels([{id:'unrelated'}]);h.step('undo');assert.equal(JSON.stringify(h.frame.context.featureAttachments),before);h.step('redo');assert.equal(JSON.stringify(h.frame.context.featureAttachments),before);
});
test('P-047 absent attachment undo preserves consumed keys, and different contexts remain independent',()=>{
 const h=new P.ContextHistory(()=>({sources:new Map(),groups:new Map(),featureAttachments:[]}));h.push(h.snapshot(),'local','裁切設定');const s=S.addRemnant(settings(),{stockType:1,length:100,headTrim:0,tailTrim:0});h.frame.context.featureAttachments=[record(s)];h.step('undo');
 const restored=h.frame.context.featureAttachments.find(r=>r.kind===S.KIND).value;assert.equal(restored.remnants.length,0);assert.equal(restored.stockTypes.length,0);assert.equal(restored.nextRemnantKey,2);assert.equal(restored.nextStockKey,2);
 const other={sources:new Map(),groups:new Map(),featureAttachments:[]};h.restore({context:other,ids:new Map(),featureAttachments:[]});assert.deepEqual(other.featureAttachments,[]);
});
test('T17 archive roundtrip retains settings and highwater but no plan, scope or World declaration',async()=>{
 let s=S.addRemnant(settings(),{stockType:1,length:1000,headTrim:0,tailTrim:0});s=S.addRemnant(s,{stockType:1,length:600,headTrim:0,tailTrim:0});s.remnants=s.remnants.filter(r=>r.key!==2);s=S.addRemnant(s,{stockType:1,length:800,headTrim:0,tailTrim:0});assert.equal(s.remnants.at(-1).key,3);
 const m={format:P.FORMAT,projectId:'k1',name:'裁切往返',sceneHash:'0'.repeat(64),sources:[],faces:[],featureAttachments:attachment(s)},scene='';const bytes=await P.pack(scene,m,new Map(),zip),loaded=await P.unpack(bytes,zip);
 assert.equal(loaded.manifest.format,P.CUTTING_FORMAT);assert.deepEqual(loaded.manifest.requiredCapabilities,['cutting-plan/1']);assert.deepEqual(loaded.manifest.featureAttachments,attachment(s));assert.equal(loaded.scene,scene);
 const entries=zip.unzipSync(bytes);assert.deepEqual(Object.keys(entries).sort(),['manifest.json','world.scene']);assert.equal(P.readerCapabilities([],{cutting:true}).includes('cutting-plan/1'),true);assert.equal(P.readerCapabilities([]).includes('cutting-plan/1'),false);
});
test('T17b old project format, missing capability and unknown schema refuse import before changing project',async()=>{
 const m={format:P.FORMAT,projectId:'k1',name:'拒絕',sceneHash:'0'.repeat(64),sources:[],faces:[],featureAttachments:attachment(settings())},bytes=await P.pack('',m,new Map(),zip),enc=new TextEncoder(),dec=new TextDecoder();
 for(const mutate of [m=>m.format=P.SECTION_FORMAT,m=>m.format=P.FEATURE_FORMAT,m=>m.requiredCapabilities=[],m=>m.featureAttachments.records[0].schema='cutting-settings/2']){const entries=zip.unzipSync(bytes),v=JSON.parse(dec.decode(entries['manifest.json']));mutate(v);entries['manifest.json']=enc.encode(JSON.stringify(v));await assert.rejects(()=>P.unpack(zip.zipSync(entries),zip));}
 assert.throws(()=>record({...settings(),schema:'cutting-settings/1'}));
});
test('cutting record obeys existing finite plain JSON gate including getters and oversized escaped bytes',()=>{
 const s=settings();Object.defineProperty(s,'kerf',{get(){throw Error('getter executed');},enumerable:true});assert.throws(()=>record(s),/欄位/);
 const cyclic=settings();cyclic.stockTypes[0].material=cyclic;assert.throws(()=>record(cyclic));
 const a=attachment(settings());a.records.push(structuredClone(a.records[0]));assert.throws(()=>P.Features.validate(a),/重複/);
});
test('cutting format keeps existing native section capability admission independently of project metadata',async()=>{
 const scene='requires section-profile/1\n',m={format:P.FORMAT,projectId:'k1-mixed',name:'並存',sceneHash:'0'.repeat(64),sources:[],faces:[],featureAttachments:attachment(settings())};
 const loaded=await P.unpack(await P.pack(scene,m,new Map(),zip),zip);assert.equal(loaded.manifest.format,P.CUTTING_FORMAT);assert.deepEqual(loaded.manifest.requiredCapabilities,['cutting-plan/1','section-profile/1']);
 assert.throws(()=>P.assertProjectCapabilities(loaded.manifest,P.readerCapabilities([],{cutting:true})));P.assertProjectCapabilities(loaded.manifest,P.readerCapabilities(['section-profile/1'],{cutting:true}));
});
