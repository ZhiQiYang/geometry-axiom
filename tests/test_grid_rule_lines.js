'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),R=require('../geometry-web/grid-rule-lines.js');
const ref={kind:'grid-rule-line',appliedGridId:10,systemId:0,ruleKey:7,cellI:'9007199254740993',cellJ:'-9007199254740995',axis:'u',innerIndex:0};
test('RuleLineRef retains complete typed identities and signed strings through both native commands',()=>{
  assert.deepEqual(R.parseAnchor(R.anchor(ref)),ref);assert.deepEqual(R.parseExpression(R.expression(ref)),ref);
  for(const value of [{...ref,ruleKey:0},{...ref,cellI:Number(ref.cellI)},{...ref,cellJ:'-0'},{...ref,kind:'grid-line'}])assert.equal(R.ref(value),null);
  assert.notEqual(R.key(ref),R.key({...ref,systemId:1}));assert.notEqual(R.key(ref),R.key({...ref,appliedGridId:11}));
});
test('query decoder refuses wrong source, cell or synthetic applied reference and retains native clipping',()=>{
  const line={axis:'u',innerIndex:0,coordinate:200,segments:[[[200,0],[200,80]],[[200,120],[200,400]]],ref};
  const q={ok:true,systemId:0,ruleKey:7,cell:[ref.cellI,ref.cellJ],bounds:[0,0,600,400],lines:[line]},target={kind:'grid',id:10,systemId:0,ruleKey:7};
  assert.deepEqual(R.rows(q,target)[0].segments,line.segments);
  assert.throws(()=>R.rows(q,{...target,systemId:1}));assert.throws(()=>R.rows(q,{...target,cell:['0','0']}));
  assert.throws(()=>R.rows(q,{...target,kind:'binding'}));
  const source={...q,lines:[{...line,ref:null}]};assert.equal(R.rows(source,{...target,kind:'system'})[0].ref,null);assert.throws(()=>R.rows(source,target));
});
test('single rule usage includes signed arithmetic references without source-wide overcount',()=>{
  const references={guides:[{id:1,expression:'2*'+R.expression(ref)+'+spec:offset'},{id:2,expression:R.expression({...ref,ruleKey:8})},{id:3,expression:R.expression({...ref,systemId:1})}],timbers:[{id:1,definition:{anchor:R.anchor(ref)}},{id:2,definition:{anchor:'at-line grid 10 u 0'}}]};
  assert.deepEqual(R.usage(references,0,7).guides.map(g=>g.id),[1]);assert.deepEqual(R.usage(references,0,7).timbers.map(t=>t.id),[1]);
});
