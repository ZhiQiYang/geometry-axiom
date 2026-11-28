'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {R,names,defaults,make,available,record}=require('./fixtures/r13_rc_n1.cjs');
const clone=structuredClone;
function change(value,fields,extra={}){return R.edit(value,{type:'edit',id:record(value).id,fields,...extra});}
for(const kind of ['rc-column','rc-beam']){
 test('R13_N1_D01 '+kind+' closed empty manual template',()=>{
  available();const value=R.edit(R.empty(),{type:'create',kind});const r=record(value);
  assert.equal(r.kind,kind,'R13_N1_KIND');assert.deepEqual(Object.keys(r.fields),names[kind],'R13_N1_FIELD_INVENTORY');
  assert.equal(r.spaceId,null,'R13_N1_NO_D5_DEFAULT');if(kind==='rc-beam')assert.equal(r.axis,null,'R13_N1_NO_AXIS_DEFAULT');
  for(const [key,f] of Object.entries(r.fields)){
   assert.equal(f.raw,'','R13_N1_NO_DIMENSION_DEFAULT');assert.equal(f.unit,null);assert.equal(f.confirmation,null);assert.deepEqual(f.source,{kind:'manual'});
   assert.equal(f.basis.kind,['width','depth','height'].includes(key)?'distance':'unknown');
  }
  for(const mutate of [x=>x.extra=true,x=>x.kind='rc-wall',x=>x.fields.extra=x.fields.width,x=>x.fields.width.source={kind:'drawing'},x=>x.spaceId=0,x=>x.spaceId=4294967296]){
   const bad=clone(value);mutate(record(bad));assert.throws(()=>R.validate(bad),undefined,'R13_N1_CLOSED_SCHEMA');
  }
 });
 test('R13_N1_D02 '+kind+' exact confirmations and unknown basis',()=>{
  const value=make(kind),r=record(value);assert.deepEqual(R.rcValues(r),defaults[kind],'R13_N1_EXACT_CONFIRMED_VALUES');
  const k=kind==='rc-column'?'x':'start';let v=change(value,{[k]:{raw:'-.1',unit:'cm',basis:{kind:'unknown',note:'不是坐標轉換'}}});
  v=R.edit(v,{type:'confirm',id:r.id,field:k});assert.equal(record(v).fields[k].confirmation.value,-1,'R13_N1_EXACT_CM');
  assert.throws(()=>R.rcValues(record(v)),e=>e.code==='R13_DATUM_ADOPTION','R13_N1_UNKNOWN_BASIS_BLOCKS_GEOMETRY');
  assert.throws(()=>R.rcValues(record(v)),e=>e.message.includes('世界 X；'),'R13_N1_DATUM_AXIS_EXACT');
  const forged=clone(value);record(forged).fields.width.confirmation.value++;
  assert.throws(()=>R.validate(forged),undefined,'R13_N1_FORGED_CONFIRMATION_REJECTED');
 });
 test('R13_N1_D03 '+kind+' invalid raw remains exact until explicit confirm',()=>{
  const value=make(kind);for(const raw of ['',' ','１','1.','1e2','1/2','1,000','0.1','-1','0','100000001']){
   const v=change(value,{width:{raw,unit:'mm'}});assert.equal(record(v).fields.width.raw,raw,'R13_N1_RAW_EXACT');
   assert.equal(record(v).fields.width.confirmation,null);assert.throws(()=>R.edit(v,{type:'confirm',id:record(v).id,field:'width'}),undefined,'R13_N1_INVALID_NOT_CONFIRMED');
  }
  const v=change(value,{width:{raw:'a'.repeat(64)}});assert.equal(record(v).fields.width.raw.length,64);
  assert.throws(()=>change(value,{width:{raw:'a'.repeat(65)}}),undefined,'R13_N1_RAW_LIMIT');
  for(const raw of ['+001','1.000','.1']){const unit=raw==='.1'?'cm':'mm';const q=R.edit(change(value,{width:{raw,unit}}),{type:'confirm',id:record(value).id,field:'width'});assert.equal(record(q).fields.width.confirmation.value,1);}
 });
 test('R13_N1_D04 '+kind+' unique derivation is independent explicit confirmation',()=>{
  const middle=kind==='rc-beam'?'depth':'height';
  for(const missing of ['bottom',middle,'top']){
   const values={...defaults[kind],[missing]:null};let value=make(kind,values),r=record(value);
   const candidate=R.derivation(r);assert.equal(candidate.field,missing,'R13_N1_RELATION_FIELD');assert.equal(candidate.value,defaults[kind][missing],'R13_N1_RELATION_VALUE');
   assert.equal(r.fields[missing].confirmation,null,'R13_N1_DERIVATION_NOT_AUTO_CONFIRM');
   value=R.edit(value,{type:'confirm-derived',id:r.id,field:missing});assert.deepEqual(R.rcValues(record(value)),defaults[kind]);
   const dependency=missing==='bottom'?'top':'bottom';const stale=change(value,{[dependency]:{raw:String(defaults[kind][dependency]+1)}});
   assert.equal(record(stale).fields[missing].confirmation,null,'R13_N1_DERIVED_INVALIDATED');
   const before=JSON.stringify(value);assert.throws(()=>R.edit(value,{type:'confirm-derived',id:r.id,field:dependency}),undefined,'R13_N1_DERIVED_CHAIN_REJECTED');assert.equal(JSON.stringify(value),before);
  }
 });
 test('R13_N1_D05 '+kind+' conflicts retain all observations and block geometry',()=>{
  const value=make(kind,{...defaults[kind],top:defaults[kind].top+1});
  assert.throws(()=>R.rcValues(record(value)),e=>e.code==='SUM_CONFLICT','R13_N1_CONFLICT_BLOCKS');
  assert.equal(record(value).fields.top.raw,String(defaults[kind].top+1),'R13_N1_CONFLICT_RETENTION');
  const extra=clone(value);extra.records[0].fields.top.confirmation=null;
  assert.throws(()=>R.rcValues(record(extra)),undefined,'R13_N1_UNCONFIRMED_CONFLICT_NOT_ADOPTED');
 });
 test('R13_N1_D06 '+kind+' revisions no-op name failure space and immutable inputs',()=>{
  const value=make(kind),before=JSON.stringify(value),r=record(value);
  assert.equal(R.edit(value,{type:'edit',id:r.id,name:'改名'}).nextRevision,value.nextRevision,'R13_N1_NAME_NO_REVISION');
  assert.deepEqual(change(value,{}, {spaceId:null}),value,'R13_N1_NOOP_NO_REVISION');
  const q=change(value,{}, {spaceId:1});assert.equal(q.nextRevision,value.nextRevision+1,'R13_N1_D5_REVISION');assert.equal(record(q).revision,value.nextRevision);
  assert.deepEqual(record(q).fields,r.fields,'R13_N1_D5_NOT_FIELD_REWRITE');
  assert.throws(()=>change(value,{}, {spaceId:'1'}));assert.throws(()=>change(value,{unknown:{raw:'1'}}));assert.equal(JSON.stringify(value),before,'R13_N1_INPUT_IMMUTABLE');
  assert.throws(()=>R.plan(value,r.id),e=>e.code==='R13_ROOM_ONLY','R13_N1_RC_NOT_ROOM_ADOPTION');
 });
}
test('R13_N1_D07 axis edit retains raw and basis but invalidates dependent positions',()=>{
 let v=make('rc-beam'),before=record(v);v=change(v,{}, {axis:'y'});const after=record(v);
 for(const key of ['start','end','center']){assert.equal(after.fields[key].confirmation,null,'R13_N1_AXIS_INVALIDATES');assert.equal(after.fields[key].raw,before.fields[key].raw,'R13_N1_AXIS_RAW_RETAINED');assert.deepEqual(after.fields[key].basis,before.fields[key].basis,'R13_N1_AXIS_BASIS_NOT_GUESSED');}
 assert.deepEqual(after.fields.depth,before.fields.depth,'R13_N1_AXIS_UNRELATED_CONFIRMATION');
 assert.throws(()=>R.rcValues(after));assert.throws(()=>change(v,{}, {axis:'z'}));
});
test('R13_N1_D08 mixed template capacity highwater delete and no foreign model reviews',()=>{
 available();let value=R.empty();for(let i=0;i<256;i++)value=R.edit(value,{type:'create',kind:i%3===0?'room-height':i%3===1?'rc-column':'rc-beam'});
 assert.equal(value.records.length,256,'R13_N1_SHARED_256');assert.throws(()=>R.edit(value,{type:'create',kind:'rc-beam'}),undefined,'R13_N1_CAPACITY_NO_TRUNCATION');
 const removed=R.edit(value,{type:'delete',id:'rd-1'}),added=R.edit(removed,{type:'create',kind:'rc-column'});assert.equal(added.records.at(-1).id,'rd-257');
 const restored=R.preserveHighwater(value,added);assert.equal(restored.nextId,258,'R13_N1_HIGHWATER_PRESERVED');
});
