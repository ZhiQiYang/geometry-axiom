'use strict';
// P1162 is additive to main 1b1c6674's 99-section contract. The full CDP
// producer must measure its count first. These projections never supply a count.
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const SECTION='P1162';
function projectGolden(value){
  assert.equal(value.schema,'geometry-cdp-sections/1','R433_GOLDEN_SCHEMA');
  assert.equal(value.mode,'full','R433_GOLDEN_FULL_MODE');
  const count=value.sections[SECTION];
  assert.ok(Number.isSafeInteger(count)&&count>0,'R433_FULL_BROWSER_RECEIPT_REQUIRED');
  assert.ok(Object.values(value.sections).every(n=>Number.isSafeInteger(n)&&n>=0),'R433_ALL_COUNTS_EXACT');
  assert.equal(value.total,Object.values(value.sections).reduce((a,b)=>a+b,0),'R433_TOTAL_CONSERVATION');
  const projected=structuredClone(value);delete projected.sections[SECTION];projected.total-=count;
  return projected;
}
function projectPlan(value){
  assert.equal(value.schema,'geometry-cdp-shards/1','R433_PLAN_SCHEMA');
  assert.deepEqual(value.shards.map(shard=>shard.index),[1,2],'R433_TWO_SHARDS');
  assert.deepEqual(value.shards.map(shard=>shard.sections.filter(name=>name===SECTION)),[[],[SECTION]],'R433_EXACT_OWNER');
  const at=value.shards[1].sections.indexOf(SECTION);
  assert.deepEqual(value.shards[1].sections.slice(at-1,at+2),['P116',SECTION,'P335'],'R433_EXACT_NEIGHBORS');
  const projected=structuredClone(value);projected.shards[1].sections.splice(at,1);
  return projected;
}
function projectRaw(rawSource){
  const raw=String(rawSource).replace(/\r\n/g,'\n'),parsed=JSON.parse(raw);
  const projected=projectGolden(parsed),count=parsed.sections[SECTION];
  const added='    "P1284": 36,\n    "P1162": '+count+'\n';
  assert.equal(raw.split(added).length,2,'R433_ADDED_RAW_LINE_EXACTLY_ONCE');
  const without=raw.replace(added,'    "P1284": 36\n');
  const total='  "total": '+parsed.total+',\n';
  assert.equal(without.split(total).length,2,'R433_TOTAL_RAW_LINE_EXACTLY_ONCE');
  const restored=without.replace(total,'  "total": '+projected.total+',\n');
  assert.deepEqual(JSON.parse(restored),projected,'R433_ONLY_P1162_PROJECTED');
  assert.equal(crypto.createHash('sha256').update(restored).digest('hex'),
    'cfbe3dc18bf983b3ea3d468c456c8dfddf33e893e5ed85916edfaa2be7e87bca','R433_MAIN99_RAW_BYTES_UNCHANGED');
  return restored;
}
module.exports={projectGolden,projectPlan,projectRaw};
