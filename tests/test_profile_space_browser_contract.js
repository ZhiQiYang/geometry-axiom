/* Syntax and census gates only. These checks do not launch or replace a browser. */
'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {CASES,pagePrograms,expression}=require('../geometry-web/profile_space_test.js');
const {EXPECTED,FULL_SPACE_GROUPS}=require('../geometry-web/space_test_floor.js');

test('R12 browser programs and JSON arguments are valid JavaScript before a renderer starts',()=>{
  for(const name of Object.keys(pagePrograms)){
    assert.doesNotThrow(()=>new Function('return '+expression(name)),name);
    assert.doesNotThrow(()=>new Function('return '+expression(name,'引號 " \\ \n ${value}',0,null)),name+' arguments');
  }
});

test('R12 keeps a separate source census with sixty unique named browser assertions',()=>{
  assert.equal(CASES.length,60);assert.equal(new Set(CASES).size,60);
  assert.equal(EXPECTED['profile-space'],60);assert.equal(Object.isFrozen(CASES),true);
  assert.equal(FULL_SPACE_GROUPS.filter(name=>name==='profile-space').length,1);
  const source=fs.readFileSync(path.join(__dirname,'../geometry-web/profile_space_test.js'),'utf8');
  const direct=[...source.matchAll(/\bcheck\('(R12_[A-Z0-9_]+)'\s*,/g)].map(m=>m[1]);
  assert.deepEqual([...direct,...[1400,690,390].map(width=>'R12_LAYOUT_'+width)].sort(),[...CASES].sort());
});

test('R12 full and partial browser execution call the same group without modifying legacy groups',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../geometry-web/space_model_test.js'),'utf8');
  assert.equal([...source.matchAll(/await runGroup\('profile-space', runProfileSpace\);/g)].length,2);
  assert.match(source,/GEOMETRY_SPACE_PROFILE_ONLY:\['profile-space'\]/);
  assert.deepEqual(Object.fromEntries(['space-height-library','projection-lifecycle','projection-placement','projection-close','font-layout','space-flow','timber-material','timber-source-guards','timber-history-guard'].map(k=>[k,EXPECTED[k]])),{
    'space-height-library':112,'projection-lifecycle':18,'projection-placement':36,'projection-close':14,
    'font-layout':19,'space-flow':39,'timber-material':48,'timber-source-guards':8,'timber-history-guard':5,
  });
});
