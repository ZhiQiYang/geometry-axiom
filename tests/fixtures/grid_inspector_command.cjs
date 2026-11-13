/* Executes the production saveSource body with only its DOM/commit ports stubbed.
 * This is a command-boundary probe, not a browser or native validation oracle. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const defaultSource=path.join(__dirname,'../../geometry-web/grid-inspector.js');
async function serialize(object,name,fields={},sourceFile=process.env.GEOMETRY_GRID_INSPECTOR_SOURCE || defaultSource) {
  const source=fs.readFileSync(sourceFile,'utf8');
  const start=source.indexOf('  async function saveSource(s) {'),end=source.indexOf('  async function saveBinding(s) {',start);
  assert.ok(start>=0 && end>start,'production saveSource boundary is present');
  const values={giName:name,giUStep:String(object.uDefinition?.step??''),giVStep:String(object.vDefinition?.step??''),...fields};
  let line,checked=false;
  const context=vm.createContext({TextEncoder,axes:['u','v'],$:(_s,id)=>({value:values[id]}),
    stillSame:async()=>{checked=true;},commit:async(_s,command)=>{assert.equal(checked,true);line=command;}});
  vm.runInContext(source.slice(start,end),context,{filename:sourceFile});
  await context.saveSource({object:structuredClone(object)});
  return line;
}
module.exports={serialize};
if(require.main===module) {
  const data=JSON.parse(fs.readFileSync(0,'utf8'));
  serialize(data.object,data.name,data.fields).then(line=>process.stdout.write(JSON.stringify({line}))).catch(error=>{console.error(error);process.exitCode=1;});
}
