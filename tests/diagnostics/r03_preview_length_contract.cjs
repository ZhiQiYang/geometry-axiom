'use strict';
/* This is a source policy / read-only probe regression, NOT a browser layout
 * receipt. The shipping layout is checked by P2054 in actual Chromium. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {lengthValuesReady,lengthSingleLine,lengthUnclipped}=require('./r03_preview_length_probe.cjs');
const root=path.resolve(__dirname,'../..');
function sourcePolicy(css){
  const selectors=['.ft-workspace .ft-results [data-ft-length]'];
  for(const selector of selectors){
    const rules=[...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)].filter(match=>match[1].split(',').map(s=>s.trim()).includes(selector));
    assert.ok(rules.length>0,'R03_PREVIEW_LENGTH_POLICY: scoped length column is missing: '+selector);
    const declarations=new Map(rules.flatMap(match=>match[2].split(';')).filter(s=>s.trim()).map(s=>{
      const at=s.indexOf(':');return [s.slice(0,at).trim(),s.slice(at+1).trim()];
    }));
    assert.equal(declarations.get('white-space'),'nowrap','R03_PREVIEW_LENGTH_POLICY: four-digit lengths must be indivisible');
    assert.equal(declarations.get('overflow-wrap'),'normal','R03_PREVIEW_LENGTH_POLICY: inherited anywhere must not split digits');
    assert.equal(declarations.get('word-break'),'normal','R03_PREVIEW_LENGTH_POLICY: digit breaking must not be enabled');
  }
}
function probeSelftest(){
  const row={text:'3247',cells:['主支','0, 0, 27, 3247','3247','27 × 33'],
    cell:{left:10,right:60,top:10,bottom:35},lines:[{left:15,right:47,top:15,bottom:29}],
    member:{width:27,height:3247}};
  const positive={exists:true,rows:[row],scroll:{width:200,contentWidth:200}};
  assert.equal(lengthValuesReady(positive,1,'3247'),true);
  assert.equal(lengthSingleLine(positive),true);
  assert.equal(lengthUnclipped(positive),true);
  const copy=()=>structuredClone(positive);
  const wrapped=copy();wrapped.rows[0].lines.push({left:15,right:23,top:29,bottom:43});
  assert.equal(lengthSingleLine(wrapped),false,'R03_PROBE_REJECTS_324_7');
  const clipped=copy();clipped.rows[0].lines[0].right=70;
  assert.equal(lengthUnclipped(clipped),false,'R03_PROBE_REJECTS_NO_WRAP_BUT_CLIPPED');
  const overflow=copy();overflow.scroll.contentWidth=230;
  assert.equal(lengthUnclipped(overflow),false,'R03_PROBE_REJECTS_HORIZONTAL_OVERFLOW');
  const missing=copy();missing.rows=[];
  assert.equal(lengthSingleLine(missing),false,'R03_PROBE_REJECTS_EMPTY_TABLE');
  const wrong=copy();wrong.rows[0].text='324';
  assert.equal(lengthValuesReady(wrong,1,'3247'),false,'R03_PROBE_REJECTS_TRUNCATED_VALUE');
  console.log('R03_PREVIEW_LENGTH_PROBE_SELFTEST PASS: positive plus five independent negatives');
}
if(require.main===module){
  probeSelftest();
  sourcePolicy(fs.readFileSync(path.join(root,'geometry-web/framing-template-workspace.css'),'utf8'));
  console.log('R03_PREVIEW_LENGTH_POLICY PASS (source policy only; Chromium remains required)');
}
module.exports={sourcePolicy,probeSelftest};
