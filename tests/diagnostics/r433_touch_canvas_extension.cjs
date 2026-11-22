'use strict';
// The full producer on 61bacf17 measured P1162=504 (golden commit 7e804649).
// Project only that section back to main 3ef07683's exact 100-section bytes;
// R03's P205 remains until its own historical oracle projects it out.
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const SECTION='P1162';
function projectGolden(value){
  assert.equal(value.schema,'geometry-cdp-sections/1','R433_GOLDEN_SCHEMA');
  assert.equal(value.mode,'full','R433_GOLDEN_FULL_MODE');
  const count=value.sections[SECTION];
  assert.equal(count,504,'R433_P1162_MEASURED_ASSERTION_COUNT');
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
  const projected=projectGolden(parsed);
  const added='    "P205": 25,\n    "P1162": 504\n';
  assert.equal(raw.split(added).length,2,'R433_ADDED_RAW_LINE_EXACTLY_ONCE');
  const without=raw.replace(added,'    "P205": 25\n');
  const total='  "total": '+parsed.total+',\n';
  assert.equal(without.split(total).length,2,'R433_TOTAL_RAW_LINE_EXACTLY_ONCE');
  const restored=without.replace(total,'  "total": '+projected.total+',\n');
  assert.deepEqual(JSON.parse(restored),projected,'R433_ONLY_P1162_PROJECTED');
  assert.equal(crypto.createHash('sha256').update(restored).digest('hex'),
    '0acd8bdccce2eb3aae13b94bd04d9dfa89521dcd58d085e0e634698d4ca41e7b','R433_MAIN100_RAW_BYTES_UNCHANGED');
  return restored;
}
module.exports={projectGolden,projectPlan,projectRaw};
