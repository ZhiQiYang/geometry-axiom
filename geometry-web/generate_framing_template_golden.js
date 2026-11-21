/* Run by cloud Claude with the unchanged canonical full CDP path and an
 * isolated native service. Never launch from the author's Chromium-less host.
 * Only observed P205 may be added; all previous counts remain byte-equivalent
 * as JSON values. Failure restores the original golden bytes.
 */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),{spawnSync}=require('node:child_process'),assert=require('node:assert/strict');
const ROOT=path.resolve(__dirname,'..'),GOLDEN=path.join(__dirname,'cdp_sections.golden.json');
function verify(before,after){
 const old=JSON.parse(before),next=JSON.parse(after),extension=require('../tests/diagnostics/r03_framing_canvas_extension.cjs');
 assert.equal(next.sections.P205,extension.COUNT,'R03_OBSERVED_NEW_SECTION_COUNT');
 const projected=extension.projectGolden(next);assert.deepEqual(projected,old,'R03_EXISTING_GOLDEN_UNCHANGED');return {section:'P205',observedAssertions:next.sections.P205};
}
function main(){
 if(process.argv[2]!=='--run')throw Error('Use --run in cloud CI with GEOMETRY_TEST_URL, GEOMETRY_FEEDBACK_DIR and the usual Chrome environment. This always runs the complete suite.');
 if(Object.keys(process.env).some(key=>(key.startsWith('GEOMETRY_')&&key.endsWith('_ONLY'))||key==='GEOMETRY_CDP_SHARD'||key==='GEOMETRY_CDP_FROM_P31'))throw Error('R03_GOLDEN_FULL_MODE_REQUIRED: remove all scope flags and shards');
 const before=fs.readFileSync(GOLDEN),old=JSON.parse(before);assert.ok(!Object.hasOwn(old.sections,'P205'),'P205 is already recorded; review changes explicitly instead of overwriting it');
 const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
 try{
  const result=spawnSync(process.execPath,[path.join(__dirname,'cdp_test.js')],{cwd:ROOT,env:{...process.env,GEOMETRY_CDP_UPDATE_GOLDEN:'1'},stdio:'inherit'});
  if(result.status!==0||result.error)throw result.error||Error('Complete CDP run failed: '+result.status);
  const after=fs.readFileSync(GOLDEN),accepted=verify(before,after);
  console.log('R03_GOLDEN_RECEIPT '+JSON.stringify({schema:'framing-template-golden-generation/1',...accepted,beforeBytes:before.length,beforeSha256:hash(before),afterBytes:after.length,afterSha256:hash(after),producer:'canonical complete cdp_test.js; observed full-mode counts; previous sections unchanged'}));
 }catch(error){fs.writeFileSync(GOLDEN,before);throw error;}
}
if(require.main===module)try{main();}catch(error){console.error(error.stack);process.exitCode=1;}
module.exports={verify};
