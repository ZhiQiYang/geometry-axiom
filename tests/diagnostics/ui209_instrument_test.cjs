'use strict';
// Static regression for diagnostic labels; never evaluates product code.
// UI209_INSTRUMENT selects an old/removed-fix tool for the same assertions.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),vm=require('node:vm');
const instrument=require(process.env.UI209_INSTRUMENT||'./ui209_instrument.cjs');
const source=fs.readFileSync(path.join(__dirname,'../../geometry-web/grid-system-workspace.js'),'utf8');
assert.equal(crypto.createHash('sha256').update(source).digest('hex'),
  'ce0c48d2d2c3d0102f05a45c58ac1568da991c28cc55e2461c1a4644f2e7cf01','Reviewed source fixture changed');
// Independently pinned to the original source, including two exits on one line.
const returnLines=[952,954,955,956,958,963,963,966,969,971,971,972,972,973,973,
  976,978,979,980,980,983,986,987,988,991,992,993,995,996,999,1004,1012,1015];
const awaitLines=[963,971,972,973,978,979,980,986,987,988,992,996,1012];
function verify(input,shift=0){
  const result=instrument(input);
  assert.equal(result.awaits,13);assert.equal(result.returns,33);
  const exits=[...result.source.matchAll(/return window\.__uiReturn\(__uid,(\d+),(undefined|true|false),__us\(\)\);/g)];
  assert.deepEqual(exits.map(x=>Number(x[1])),returnLines.map(n=>n+shift));
  assert.deepEqual(exits.map(x=>x[2]),returnLines.map((_,i)=>i===32?'true':i>=27&&i<=29?'false':'undefined'));
  const waits=[...result.source.matchAll(/await __ua\("[^"\n]+ @(\d+)",/g)];
  assert.deepEqual(waits.map(x=>Number(x[1])),awaitLines.map(n=>n+shift));
  new vm.Script(result.source); // Parse only: no server, browser or native execution.
}
test('all original return/await labels, including objects rejection 963 and success 1015',()=>verify(source));
test('line labels survive added Unicode text and newline shifts',()=>{
  const shifted='// 額外 😀 source prefix\n// 第二行\n'+source.replace('無法讀取網格。','無法讀取網格。😀 additional text');
  verify(shifted,2);
});
test('unexpected return shape fails closed',()=>{
  assert.throws(()=>instrument(source.replace('return true;\n  }\n  function selectedOpen','void 0;\n  }\n  function selectedOpen')),/Unexpected open return shape/);
});
test('unexpected await shape and missing boundary fail closed',()=>{
  assert.throws(()=>instrument(source.replace("await apiRequest('surfaces')","await changedRequest('surfaces')")),/Unexpected open await shape/);
  assert.throws(()=>instrument(source.replace('  function selectedOpen(options)','  function renamedSelectedOpen(options)')),/Missing open boundaries/);
});
