const {test}=require('node:test'),assert=require('node:assert/strict');
const S=require('../geometry-web/timber-schedule.js');
const timber=(id,surface=1,length=2960)=>({id,role:'primary',geometry:{surface,length,A:27,B:33,dir:'+v',side:'+n',origin:[100,20,2500],axes:[[0,1,0],[-1,0,0],[0,0,1]]},definition:{anchor:'at-line guide 2',selector:'between t90 t91'}});
const refs=()=>({ok:true,sourceFingerprint:'a'.repeat(64),timbers:[timber(1),timber(2),timber(3,2)],engineeringSources:[]});
test('counts native placements once, preserving two equal independent identities and an explicit surface',()=>{
 const r=S.derive(refs(),1);assert.deepEqual(r.ids,[1,2]);assert.equal(r.rows[0].L,2960);assert.equal(r.rows[0].A,27);
 assert.deepEqual(r.rows[0].finish,[100,2980,2500]);assert.deepEqual(S.derive(refs(),1,[2]).ids,[2]);
});
test('native timber ID zero remains a real, selectable identity',()=>{
 const r=refs();r.timbers.unshift(timber(0));assert.deepEqual(S.derive(r,1,[0]).ids,[0]);
 assert.ok(S.csv(S.derive(r,1,[0])).includes('"timber","0","1"'));
});
test('native placement surface zero remains valid while missing or malformed scope is rejected',()=>{
 const r=refs();r.timbers=[timber(0,0)];const s=S.derive(r,0,[0]);assert.deepEqual(s.ids,[0]);assert.equal(s.surface,0);
 assert.ok(S.csv(s).includes('"timber","0","0"'));
 for(const surface of [null,-1,4294967296,'0'])assert.throws(()=>S.derive(r,surface),/尚未就緒/);
});
test('rejects disappeared or wrong-surface selected IDs rather than changing the selected quantity',()=>{
 assert.throws(()=>S.derive(refs(),1,[1,3]),/重新選定/);assert.throws(()=>S.derive(refs(),1,[9]),/重新選定/);
 assert.equal(S.derive(refs(),1,[]).rows.length,0);
});
test('invalid native dimensions, duplicate identities and missing fingerprints cannot create zero quantities',()=>{
 for(const field of ['A','B','length']){const r=refs();r.timbers[0].geometry[field]=0;assert.throws(()=>S.derive(r,1),/尚未求值/);}
 const r=refs();r.timbers.push(timber(1));assert.throws(()=>S.derive(r,1),/重複/);
 assert.throws(()=>S.derive({...refs(),sourceFingerprint:null},1),/尚未就緒/);
});
test('sorting and cm presentation preserve exact native dimensions, scopes and identities',()=>{
 const r=refs();r.timbers[0].geometry.length=2961;const snapshot=S.derive(r,1),before=JSON.stringify(snapshot);
 assert.deepEqual(S.sorted(snapshot.rows,'length').map(r=>r.id),[2,1]);assert.equal(S.dimension(2961,'cm'),'296.1');
 assert.equal(JSON.stringify(snapshot),before);assert.equal(snapshot.rows[0].L,2961);
});
test('CSV preserves exact mm and source selectors and handles quotes, line breaks and formula style labels',()=>{
 const r=refs();r.timbers[0].definition.anchor='\t=HYPERLINK("danger")\nnext';
 r.engineeringSources=[{target:{kind:'timber',id:1,field:'A'},path:'材料 "木材"\n固定版 2',source:{kind:'material',id:'wood',version:2},effective:27}];
 const csv=S.csv(S.derive(r,1));assert.ok(csv.startsWith('\ufeff'));assert.ok(csv.includes('"2960"'));assert.ok(csv.includes('"\'\t=HYPERLINK(""danger"")\nnext"'));
 assert.ok(csv.includes('材料 ""木材""\n固定版 2'));assert.equal(S.csvCell(' +SUM(A1)'), '"\' +SUM(A1)"');
 assert.equal(S.csvCell('@cmd'),'"\'@cmd"');assert.ok(csv.includes('未知／未設定'));
});
test('only placed native timbers are included, bindings and stored mesh snapshots do not create material',()=>{
 const r=refs();r.timbers=[];r.bindings=[{id:1,complete:true}];r.models=[{timbers:[{id:1}]}];
 assert.equal(S.derive(r,1).rows.length,0);
});
test('owned timber dimensions keep the native member, fixed rule and typed binding source instead of becoming literals',()=>{
 const r=refs();r.assembly={instances:[{value:{source:{id:4,bindingId:9,rule:{id:7,version:2,fingerprint:'b'.repeat(64)}}},members:[{memberId:12,timberId:1}]}],
  rules:[{value:{id:7,version:2,members:[{id:12,slotId:5}]},fingerprint:'b'.repeat(64)}],
  bindings:[{value:{id:9,slots:[{slotId:5,A:{kind:'parameter',parameterId:6,fieldId:1},B:{kind:'literal',value:33}}]},complete:true,fingerprint:'c'.repeat(64),effective:[{slotId:5,A:{value:27,path:'參數 6／欄 1'},B:{value:33,path:'直接值 33'}}]}]};
 const s=S.derive(r,1),row=s.rows[0];assert.equal(s.rows.length,2);assert.equal(row.assembly.memberId,12);
 assert.equal(row.assembly.ruleVersion,2);assert.equal(row.sources[0].source.kind,'parameter');assert.ok(S.sourceText(row).includes('組構實例 4'));
 assert.ok(S.csv(s).includes('"4","12","9","7","2","'+'b'.repeat(64)+'"'));
 r.assembly.bindings[0].effective[0].A.value=40;assert.throws(()=>S.derive(r,1),/尚未核對/);
});
