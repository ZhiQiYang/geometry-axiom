'use strict';
// A declared browser assertion contract, never an execution receipt. The
// producer may add P2052 only after the original complete CDP run succeeds.
const assert=require('node:assert/strict');
const SECTION='P2052';
const count=()=>require('../../geometry-web/framing_template_jig_workflow_test.js').ASSERTIONS.length;
const clone=value=>JSON.parse(JSON.stringify(value));
function projectGolden(value){
 assert.equal(value.schema,'geometry-cdp-sections/1','R03A_GOLDEN_SCHEMA');
 assert.equal(value.mode,'full','R03A_GOLDEN_FULL_MODE');
 assert.equal(value.sections[SECTION],count(),'R03A_BROWSER_GOLDEN_REQUIRED');
 assert.equal(value.total,Object.values(value.sections).reduce((a,b)=>a+b,0),'R03A_GOLDEN_SUM');
 const projected=clone(value);delete projected.sections[SECTION];projected.total-=count();return projected;
}
function projectPlan(value){
 assert.equal(value.shards.length,2,'R03A_TWO_BROWSER_SHARDS');
 assert.deepEqual(value.shards.map(s=>s.sections.filter(key=>key===SECTION)),[[],[SECTION]],'R03A_BROWSER_EXACT_OWNER');
 const at=value.shards[1].sections.indexOf(SECTION);
 assert.deepEqual(value.shards[1].sections.slice(at-1,at+2),['P205',SECTION,'P353'],'R03A_BROWSER_EXACT_ORDER');
 const projected=clone(value);projected.shards[1].sections.splice(at,1);return projected;
}
function projectRaw(rawSource){
 const raw=String(rawSource).replace(/\r\n/g,'\n'),parsed=JSON.parse(raw),projected=projectGolden(parsed);
 const line=',\n    "'+SECTION+'": '+count()+'\n';
 const without=raw.replace(line,'\n');
 assert.notEqual(without,raw,'R03A_RAW_APPENDED_LINE_REQUIRED');
 const old=without.replace('  "total": '+parsed.total+',\n','  "total": '+projected.total+',\n');
 assert.notEqual(old,without,'R03A_RAW_TOTAL_REQUIRED');
 assert.deepEqual(JSON.parse(old),projected,'R03A_ONLY_P2052_PROJECTED');return old;
}
module.exports={SECTION,get COUNT(){return count();},projectGolden,projectPlan,projectRaw};
