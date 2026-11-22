'use strict';

// Synthetic DOM/rectangle tests only. These do not render CSS or prove that
// the product passes Chrome. --replay-cloud-red replays the published failure;
// it stays red after a product fix because that historical observation stays.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const os=require('node:os'),{spawnSync}=require('node:child_process');
const {createHash}=require('node:crypto');
const sizes=[{width:390,height:844},{width:768,height:1024},{width:1400,height:900},
  {width:560,height:844},{width:561,height:844}];

function fixture(width,height,rowHeight=32){
  const rect=(left,top,right,bottom)=>({left,top,right,bottom,width:right-left,height:bottom-top});
  const node=(selector,r,border='0px')=>({selector,exists:true,visible:true,rect:r,computed:{
    display:'block',visibility:'visible',opacity:'1',height:r.height+'px',borderTopWidth:border,
    alignItems:'center',overflowX:'visible',overflowY:'visible',zIndex:'auto'}});
  const top=height-rowHeight,commandTop=top+1+(rowHeight-1-28)/2;
  return {schema:'r16-statusbar-probe/1',viewport:{width,height},breakpoint:width<=560?'narrow':'wide',
    statusbarVariable:rowHeight+'px',app:node('#app',rect(0,0,width,height)),
    surface:node('#ocv',rect(156,width<=560?96:56,width,top)),
    footer:node('#app > .statusbar',rect(0,top,width,height),'1px'),
    command:node('#cmdToggle',rect(width-37,commandTop,width-9,commandTop+28))};
}

function probeSynthetic(api,observation){
  const names=['document','getComputedStyle','innerWidth','innerHeight'];
  const saved=new Map(names.map(name=>[name,Object.getOwnPropertyDescriptor(globalThis,name)]));
  const nodes=new Map(),styles=new Map(),body=Object.freeze({});
  for(const data of [observation.app,observation.surface,observation.footer,observation.command]){
    if(!data.exists)continue;
    const node=Object.freeze({hidden:!data.visible,closest:()=>null,
      getBoundingClientRect:()=>Object.freeze({...data.rect})});
    nodes.set(data.selector,node);styles.set(node,Object.freeze({...data.computed}));
  }
  styles.set(body,Object.freeze({getPropertyValue:()=>observation.statusbarVariable}));
  const before=JSON.stringify(observation);
  try{
    globalThis.document=Object.freeze({body,querySelector:selector=>nodes.get(selector)||null});
    globalThis.getComputedStyle=node=>styles.get(node);
    globalThis.innerWidth=observation.viewport.width;globalThis.innerHeight=observation.viewport.height;
    const result=api.statusbarProbe();
    assert.equal(JSON.stringify(observation),before,'R16_STATUSBAR_PROBE_READ_ONLY');
    return result;
  }finally{
    for(const name of names){const descriptor=saved.get(name);
      if(descriptor)Object.defineProperty(globalThis,name,descriptor);else delete globalThis[name];}
  }
}

function contract(api){
  let checks=0;
  const same=(a,b,name)=>{assert.deepEqual(a,b,name);checks++;};
  const rows=[];
  for(const size of sizes)for(const state of ['teaching-open','normal-read']){
    const observation=fixture(size.width,size.height),actual=probeSynthetic(api,observation);
    same(actual,observation,'R16_STATUSBAR_READONLY_FIELDS '+size.width+' '+state);
    same(api.statusbarReady(actual),true,'R16_STATUSBAR_CLEAR_GEOMETRY '+size.width+' '+state);
    rows.push({requested:size,state,observation:actual});
  }
  same(api.statusbarMatrixReady(rows,sizes),true,'R16_STATUSBAR_EXACT_TEN_STATES');
  same(api.statusbarMatrixReady(rows.slice(0,8),sizes),false,'R16_STATUSBAR_MISSING_561_REJECTED');
  same(api.statusbarMatrixReady([...rows.slice(0,8),...rows.slice(0,2)],sizes),false,
    'R16_STATUSBAR_DUPLICATE_390_FOR_561_REJECTED');
  const wrongState=structuredClone(rows);wrongState.at(-1).state='teaching-open';
  same(api.statusbarMatrixReady(wrongState,sizes),false,'R16_STATUSBAR_REPEATED_TEACHING_REJECTED');
  const viewportMismatch=structuredClone(rows);viewportMismatch.at(-1).observation.viewport.width=560;
  same(api.statusbarMatrixReady(viewportMismatch,sizes),false,'R16_STATUSBAR_OBSERVED_WIDTH_REQUIRED');

  const historical=fixture(561,844,26);
  // Only these two rectangles and the viewport were reported by cloud Claude.
  // The surrounding footer box is inferred from the P-prime CSS, not claimed
  // as an additional Chrome observation.
  same(historical.surface.rect,{left:156,top:56,right:561,bottom:818,width:405,height:762},
    'R16_CLOUD_CANVAS_RECT_RETAINED');
  same(historical.command.rect,{left:524,top:817.5,right:552,bottom:845.5,width:28,height:28},
    'R16_CLOUD_COMMAND_RECT_RETAINED');
  same(api.statusbarReady(probeSynthetic(api,historical)),false,'R16_CLOUD_561_OBSTRUCTION_REJECTED');
  const topOverlap=fixture(561,844);topOverlap.command.rect.top=811.5;topOverlap.command.rect.bottom=839.5;
  same(api.statusbarReady(topOverlap),false,'R16_HALF_PIXEL_TOP_OVERLAP_REJECTED');
  const outside=fixture(561,844);outside.footer.rect.top+=0.5;outside.footer.rect.bottom+=0.5;
  same(api.statusbarReady(outside),false,'R16_STATUSBAR_OUTSIDE_VIEWPORT_REJECTED');
  const appClip=fixture(561,844);appClip.app.rect.bottom=843;
  same(api.statusbarReady(appClip),false,'R16_STATUSBAR_APP_CLIP_REJECTED');
  const bottomOverflow=fixture(561,844);bottomOverflow.command.rect.top=817;bottomOverflow.command.rect.bottom=845;
  same(api.statusbarReady(bottomOverflow),false,'R16_COMMAND_OUTSIDE_FOOTER_REJECTED');
  const cssOnly=fixture(561,844,26);cssOnly.statusbarVariable='32px';
  same(api.statusbarReady(cssOnly),false,'R16_CSS_VARIABLE_NOT_RENDERED_PROOF');
  for(const key of ['app','surface','footer','command']){
    const missing=fixture(561,844);missing[key].exists=false;
    same(api.statusbarReady(missing),false,'R16_STATUSBAR_MISSING_NODE_REJECTED '+key);
    const hidden=fixture(561,844);hidden[key].visible=false;
    same(api.statusbarReady(hidden),false,'R16_STATUSBAR_HIDDEN_NODE_REJECTED '+key);
  }
  const malformed=fixture(561,844);malformed.command.rect.top=NaN;
  same(api.statusbarReady(malformed),false,'R16_STATUSBAR_NONFINITE_REJECTED');
  return checks;
}

function main(){
  const args=process.argv.slice(2),option=args.indexOf('--probe');
  const filename=option<0?path.join(__dirname,'r16_statusbar_probe.cjs'):path.resolve(args.at(option+1));
  const api=require(filename);
  if(args.includes('--expression')){
    process.stdout.write('('+api.statusbarProbe.toString()+')()\n');return;
  }
  if(args.includes('--replay-cloud-red')){
    const observation=fixture(561,844,26);
    console.log(JSON.stringify({schema:'r16-statusbar-historical-replay/1',browserExecuted:false,
      sourceComment:'https://github.com/ZhiQiYang/geometry-axiom/issues/123#issuecomment-7073947192',
      reported:['viewport','surface.rect','command.rect'],footerInferredFromSource:true,observation}));
    assert.equal(api.statusbarReady(observation),true,'R123H_STATUSBAR_CONTAINS_COMMAND main teaching-open 561');
    return;
  }
  if(!args.includes('--withdraw-checks')){
    console.log(JSON.stringify({schema:'r16-statusbar-node-selftest/1',browserExecuted:false,checks:contract(api)}));return;
  }
  const source=fs.readFileSync(filename,'utf8'),folder=fs.mkdtempSync(path.join(os.tmpdir(),'r16-statusbar-withdrawal-'));
  const items=[
    {id:'R16_WITHDRAW_COMMAND_TOP_CONTAINMENT',marker:'R16_HALF_PIXEL_TOP_OVERLAP_REJECTED',
      before:'c.top>=f.top+borderTop&&c.bottom<=f.bottom',after:'c.bottom<=f.bottom'},
    {id:'R16_WITHDRAW_STATUSBAR_VIEWPORT_CONTAINMENT',marker:'R16_STATUSBAR_OUTSIDE_VIEWPORT_REJECTED',
      before:'f.bottom<=Math.min(viewport.height,a.bottom)',after:'true'}
  ];
  try{
    const run=file=>spawnSync(process.execPath,[__filename,'--probe',file],{encoding:'utf8',timeout:30000});
    const baseline=run(filename);assert.equal(baseline.status,0,baseline.stderr);
    const results=[];
    for(const item of items){
      assert.equal(source.split(item.before).length,2,item.id+' exact anchor');
      const file=path.join(folder,item.id+'.cjs');fs.writeFileSync(file,source.replace(item.before,item.after));
      const withdrawn=run(file);assert.equal(withdrawn.signal,null,item.id+' no signal');
      assert.equal(withdrawn.status,1,item.id+withdrawn.stderr);assert.match(withdrawn.stderr,new RegExp(item.marker));
      fs.writeFileSync(file,source);const restored=run(file);assert.equal(restored.status,0,item.id+restored.stderr);
      assert.equal(fs.readFileSync(file,'utf8'),source,item.id+' exact restore');
      results.push({id:item.id,marker:item.marker,baselineMutantRestoredExit:[baseline.status,withdrawn.status,restored.status]});
    }
    console.log(JSON.stringify({schema:'r16-statusbar-node-withdrawals/1',browserExecuted:false,
      probeSha256:createHash('sha256').update(source).digest('hex'),results},null,2));
  }finally{fs.rmSync(folder,{recursive:true,force:true});}
}
if(require.main===module)try{main();}catch(error){console.error(error);process.exitCode=1;}
module.exports={fixture,contract};
