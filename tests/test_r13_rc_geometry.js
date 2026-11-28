'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{spawnSync}=require('node:child_process');
const {R,make,defaults,context,available}=require('./fixtures/r13_rc_n1.cjs');
const file=path.join(__dirname,'../geometry-web/reconstruction-rc-adapter.js');
function adapter(){assert.ok(fs.existsSync(file),'R13_N1_G_ADAPTER_AVAILABLE');return require(file);}
test('R13_N1_G01 research adapter matches independent inverse-checked 1 mm Cartesian oracle',()=>{
 const A=adapter(),run=spawnSync(process.env.PYTHON||'python3',['-B',path.join(__dirname,'oracles/r13_rc_oracle.py')],{encoding:'utf8',timeout:30000,maxBuffer:8*1024*1024});
 assert.equal(run.status,0,'R13_N1_ORACLE_EXECUTED '+run.stderr);const out=JSON.parse(run.stdout);
 assert.equal(out.count,999,'R13_N1_FULL_SCAN_COUNT');assert.equal(out.corruptionsRejected,999,'R13_N1_INDEPENDENT_CHECKER_REJECTS');assert.equal(out.typedCorruptionsRejected,2,'R13_N1_CHECKER_BOOLEAN_Z_REJECTED');
 for(const row of out.rows){const value=make(row.case.kind,row.case.values,row.case.axis),c=context(),before=JSON.stringify([value,c]);
  const actual=A.toGInput(value.records,c);assert.deepEqual(actual.input.obstacles,[row.expected],'R13_N1_G_PER_VALUE');assert.equal(JSON.stringify([value,c]),before,'R13_N1_G_INPUT_UNCHANGED');
  assert.deepEqual(actual.provenance,[{recordId:'rd-1',revision:value.records[0].revision,spaceId:null,status:'research-candidate',worldIdentity:'unproven'}],'R13_N1_G_PROVENANCE_NOT_AUTHORITY');
 }
});
test('R13_N1_G02 exact D13 origin and D14 odd-width positive-side with both axes',()=>{
 const A=adapter();assert.deepEqual(A.toGInput(make().records,context()).input.obstacles[0].rect,[-10,20,91,80],'R13_N1_COLUMN_NEGATIVE_ORIGIN');
 assert.deepEqual(A.toGInput(make('rc-beam').records,context()).input.obstacles[0].rect,[-10,-30,1000,71],'R13_N1_BEAM_ODD_X');
 assert.deepEqual(A.toGInput(make('rc-beam',defaults['rc-beam'],'y').records,context()).input.obstacles[0].rect,[-30,-10,71,1000],'R13_N1_BEAM_ODD_Y');
});
test('R13_N1_G03 no incomplete values guessed and batch rejects duplicates capacity unsupported kinds',()=>{
 const A=adapter(),v=make(),c=context();const q=structuredClone(v);q.records[0].fields.x.confirmation=null;
 assert.throws(()=>A.toGInput(q.records,c),undefined,'R13_N1_G_CONFIRMATION_GATE');
 assert.throws(()=>A.toGInput([...v.records,...v.records],c),undefined,'R13_N1_G_DUPLICATE');
 const many=Array.from({length:65},(_,i)=>({...v.records[0],id:'rd-'+(i+1)}));assert.throws(()=>A.toGInput(many,c),undefined,'R13_N1_G_64_LIMIT');
 assert.equal(A.toGInput(many.slice(0,64),c).input.obstacles.length,64,'R13_N1_G_NO_GEOMETRY_DEDUP');
 const room=R.edit(R.empty(),{type:'create'});assert.throws(()=>A.toGInput(room.records,c),undefined,'R13_N1_G_ROOM_NOT_OBSTACLE');
 assert.throws(()=>A.toGInput(v.records,{...c,ceiling_z:null}),undefined,'R13_N1_G_NO_CEILING_DEFAULT');
 for(const mutation of [x=>x.params.extra=0,x=>x.layout.A='z',x=>x.layout.a_start='unknown',x=>x.outer[0][0]=.1,x=>delete x.params.P]){const bad=structuredClone(c);mutation(bad);assert.throws(()=>A.toGInput(v.records,bad),undefined,'R13_N1_G_CLOSED_CONTEXT');}
});
test('R13_N1_G04 endpoint lengths remain D1 bounded and geometry does not prove D5 exists',()=>{
 const A=adapter();
 for(const [kind,values] of [['rc-column',{...defaults['rc-column'],x:100000000}],['rc-column',{...defaults['rc-column'],y:-100000000,depth:100000000}],['rc-beam',{...defaults['rc-beam'],center:100000000}],['rc-beam',{...defaults['rc-beam'],start:-100000000,end:100000000}]]){
  const v=make(kind,values);if(kind==='rc-column'&&values.y===-100000000)assert.equal(A.toGInput(v.records,context()).input.obstacles[0].rect[3],0);else assert.throws(()=>A.toGInput(v.records,context()),undefined,'R13_N1_G_D1_ENDPOINT_LENGTH');
 }
 const v=make();const q=R.edit(v,{type:'edit',id:'rd-1',spaceId:4294967295});assert.equal(A.toGInput(q.records,context()).provenance[0].spaceId,4294967295);assert.equal(A.toGInput(q.records,context()).provenance[0].worldIdentity,'unproven');
});
