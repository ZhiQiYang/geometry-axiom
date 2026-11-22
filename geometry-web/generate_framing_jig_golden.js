/* Cloud-only complete CDP producer. No measured count is supplied by this
 * script. Every old JSON value and every old LF byte survives projection.
 * Original stdout/stderr and the canonical generated JSON are retained, even
 * on failure. The author does not run Chromium in the patch environment.
 */
'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const extension=require('../tests/diagnostics/r03a_framing_canvas_extension.cjs');
const ROOT=path.resolve(__dirname,'..'),GOLDEN=path.join(__dirname,'cdp_sections.golden.json');
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
function appendObserved(before,after){
 const old=JSON.parse(before),observed=JSON.parse(after);
 assert.ok(!Object.hasOwn(old.sections,extension.SECTION),'R03A_GOLDEN_ALREADY_RECORDED');
 assert.deepEqual(extension.projectGolden(observed),old,'R03A_EXISTING_GOLDEN_UNCHANGED');
 const raw=before.toString('utf8').replace(/\r\n/g,'\n');
 assert.ok(raw.endsWith('\n  }\n}\n'),'R03A_OLD_GOLDEN_LAYOUT');
 const newTotal=raw.replace('  "total": '+old.total+',\n','  "total": '+observed.total+',\n');
 assert.notEqual(newTotal,raw,'R03A_OLD_TOTAL_LINE_REQUIRED');
 const suffix='\n  }\n}\n';
 const result=Buffer.from(newTotal.slice(0,-suffix.length)+',\n    "'+extension.SECTION+'": '+observed.sections[extension.SECTION]+suffix);
 assert.deepEqual(JSON.parse(result),observed,'R03A_GENERATED_VALUE_IDENTITY');
 assert.equal(extension.projectRaw(result.toString()),raw,'R03A_OLD_GOLDEN_RAW_BYTES_UNCHANGED');
 return result;
}
function verifyResult(stdout,observed){
 const results=stdout.split(/\r?\n/).filter(line=>line.startsWith('CDP_RESULT '));
 assert.equal(results.length,1,'R03A_CDP_EXACTLY_ONE_RESULT');
 const r=JSON.parse(results[0].slice(11));
 assert.equal(r.schema,'geometry-cdp-result/1','R03A_CDP_SCHEMA');
 assert.equal(r.scope?.mode,'full','R03A_CDP_FULL_MODE');
 assert.deepEqual(r.scope?.filters,[],'R03A_CDP_NO_FILTERS');
 assert.deepEqual(r.scope?.modifiers,[],'R03A_CDP_NO_MODIFIERS');
 assert.equal(r.completed,true,'R03A_CDP_COMPLETED');
 assert.equal(r.failedAssertions,0,'R03A_CDP_ZERO_FAILURES');
 assert.deepEqual(r.skipped,[],'R03A_CDP_ZERO_SKIPS');
 assert.equal(r.unexpectedBrowserExceptions,0,'R03A_CDP_NO_UNEXPECTED_EXCEPTIONS');
 assert.equal(r.passedAssertions,observed.total,'R03A_CDP_ACTUAL_TOTAL');
 assert.deepEqual(r.sections,observed.sections,'R03A_CDP_ACTUAL_SECTIONS');
 assert.equal(new Set(r.sectionOrder).size,r.sectionOrder.length,'R03A_CDP_UNIQUE_ORDER');
 assert.deepEqual([...r.sectionOrder].sort(),Object.keys(observed.sections).sort(),'R03A_CDP_COMPLETE_ORDER');
 return r;
}
function main(){
 assert.equal(process.argv[2],'--run','Use --run only with the usual isolated cloud service and Chrome environment.');
 assert.ok(!Object.keys(process.env).some(key=>(key.startsWith('GEOMETRY_')&&key.endsWith('_ONLY'))||key==='GEOMETRY_CDP_SHARD'||key==='GEOMETRY_CDP_FROM_P31'||key==='GEOMETRY_CDP_CAPTURE_P1161'),'R03A_GOLDEN_FULL_MODE_REQUIRED');
 const out=fs.mkdtempSync(path.join(os.tmpdir(),'r03a-full-cdp-'));
 const before=fs.readFileSync(GOLDEN),baseline=JSON.parse(before);
 assert.ok(!Object.hasOwn(baseline.sections,extension.SECTION),'R03A_GOLDEN_ALREADY_RECORDED');
 fs.writeFileSync(path.join(out,'before.golden.json'),before);
 const stdout=fs.openSync(path.join(out,'full.stdout'),'wx'),stderr=fs.openSync(path.join(out,'full.stderr'),'wx');
 console.log('R03A_FULL_CDP_ORIGINALS '+out);
 let child;
 try{
  try{child=spawnSync(process.execPath,[path.join(__dirname,'cdp_test.js')],{cwd:ROOT,env:{...process.env,GEOMETRY_CDP_UPDATE_GOLDEN:'1'},stdio:['ignore',stdout,stderr]});}
  finally{fs.closeSync(stdout);fs.closeSync(stderr);}
  if(child.status!==0||child.error||child.signal)throw child.error||Error('R03A_COMPLETE_CDP_FAILED: '+child.status+' / '+child.signal);
  const original=fs.readFileSync(GOLDEN);fs.writeFileSync(path.join(out,'canonical-generated.golden.json'),original);
  const result=verifyResult(fs.readFileSync(path.join(out,'full.stdout'),'utf8'),JSON.parse(original));
  const after=appendObserved(before,original);
  fs.writeFileSync(GOLDEN,after);fs.writeFileSync(path.join(out,'adopted.golden.json'),after);
  const receipt={schema:'framing-jig-golden-generation/1',producer:'original complete cdp_test.js',section:extension.SECTION,observedAssertions:result.sections[extension.SECTION],before:{bytes:before.length,sha256:sha(before)},canonical:{bytes:original.length,sha256:sha(original)},after:{bytes:after.length,sha256:sha(after)},exit:child.status,originals:out};
  fs.writeFileSync(path.join(out,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log('R03A_GOLDEN_RECEIPT '+JSON.stringify(receipt));
 }catch(error){fs.writeFileSync(GOLDEN,before);fs.writeFileSync(path.join(out,'failure.txt'),String(error.stack||error)+'\n');throw error;}
}
if(require.main===module)try{main();}catch(error){console.error(error.stack);process.exitCode=1;}
module.exports={appendObserved,verifyResult};
