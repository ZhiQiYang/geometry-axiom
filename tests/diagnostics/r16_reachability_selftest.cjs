'use strict';

// Node-only contract tests for the real page probe and pre-entry ordering.
// These use synthetic DOM objects; they do not render CSS or prove Chrome green.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const {spawnSync}=require('node:child_process');
const {createHash}=require('node:crypto');

async function contract(api) {
  let checks=0;
  const same=(actual,expected,name)=>{assert.deepEqual(actual,expected,name);checks++;};
  const sizes=[{width:390,height:844},{width:768,height:1024},{width:1400,height:900}];
  const rect={left:358,top:791,right:420,bottom:823,width:62,height:32};
  const blocker={id:'',tagName:'ASIDE',getAttribute:()=> 'sidebar sidebar-left'};
  let hits=[true,true,true,true,true],calls=[],missing=false,disabled=false;
  const control={id:'btnZoom',tagName:'BUTTON',hidden:false,title:'顯示全部',textContent:'顯示全部',
    parentElement:null,getBoundingClientRect:()=>rect,getAttribute:()=>null,
    matches:selector=>selector===':disabled'&&disabled,contains:node=>node===control};
  const style={display:'block',visibility:'visible',opacity:'1',pointerEvents:'auto'};
  const names=['document','getComputedStyle','innerWidth','innerHeight'];
  const descriptors=new Map(names.map(name=>[name,Object.getOwnPropertyDescriptor(globalThis,name)]));
  try {
    globalThis.document={querySelector:()=>missing?null:control,activeElement:null,
      elementFromPoint:(x,y)=>{const i=calls.length;calls.push({x,y});return hits.at(i)?control:blocker;}};
    globalThis.getComputedStyle=()=>style;
    globalThis.innerWidth=1400;globalThis.innerHeight=900;
    const measure=()=>{calls=[];return api.controlProbe('#btnZoom');};
    let p=measure();
    same(calls,[{x:389,y:807},{x:363,y:807},{x:415,y:807},{x:389,y:796},{x:389,y:818}],
      'R16_ORIGINAL_FIVE_COORDINATES');
    same(api.entryControlReady(p),true,'R16_CLEAR_CONTROL_ACCEPTED');
    for(let index=0;index<5;index++){
      hits=[true,true,true,true,true];hits[index]=false;p=measure();
      same(p.reachable,false,'R16_EVERY_PROBE_REQUIRED_'+index);
      same(api.entryControlReady(p),false,'R16_ENTRY_REJECTS_OCCLUDED_POINT_'+index);
      same(p.points.at(index).hitTarget,{id:'',tag:'ASIDE',className:'sidebar sidebar-left'},
        'R16_BLOCKER_FROM_SAME_EVALUATION_'+index);
      same(calls.length,5,'R16_NO_SECOND_HIT_TEST_'+index);
    }
    hits=[false,false,false,false,false];
    same(api.entryControlReady(measure()),false,'R16_RECORDED_DESKTOP_BLOCKER_REJECTED');
    hits=[true,true,true,true,true];disabled=true;
    same(api.entryControlReady(measure()),false,'R16_DISABLED_REJECTED');disabled=false;
    control.hidden=true;same(api.entryControlReady(measure()),false,'R16_HIDDEN_REJECTED');control.hidden=false;
    style.opacity='0';same(api.entryControlReady(measure()),false,'R16_TRANSPARENT_REJECTED');style.opacity='1';
    missing=true;same(api.entryControlReady(measure()),false,'R16_MISSING_REJECTED');missing=false;
    const clear=measure();
    same(api.entryControlReady({...clear,points:clear.points.slice(0,4)}),false,'R16_TRUNCATED_PROBES_REJECTED');
    same(api.entryControlReady({...clear,points:clear.points.map(point=>({...point,hit:1}))}),false,'R16_TRUTHY_HITS_REJECTED');
    const sequence=[],recorded=[];let active;
    const rows=await api.sweepEntryControl({sizes,selector:'#btnZoom',
      viewport:async size=>{active=size;sequence.push('viewport:'+size.width);},
      point:async selector=>{sequence.push('point:'+active.width);return {...clear,selector,
        reachable:active.width!==1400,points:clear.points.map(point=>({...point,hit:active.width!==1400}))};},
      record:row=>recorded.push(row)});
    same(sequence,['viewport:390','point:390','viewport:768','point:768','viewport:1400','point:1400'],
      'R16_ALL_THREE_SIZES_BEFORE_ASSERTION');
    same(rows,recorded,'R16_EVERY_OBSERVATION_RECORDED');
    same(rows.map(row=>api.entryControlReady(row.observation)),[true,true,false],
      'R16_DESKTOP_FAILURE_NOT_HIDDEN_BY_NARROW_PASS');
  } finally {
    for(const name of names){const descriptor=descriptors.get(name);
      if(descriptor)Object.defineProperty(globalThis,name,descriptor);else delete globalThis[name];}
  }
  return checks;
}

async function main() {
  const args=process.argv.slice(2),option=args.indexOf('--probe');
  const filename=option<0?path.join(__dirname,'r16_control_probe.cjs'):path.resolve(args.at(option+1));
  const api=require(filename);
  if(args.includes('--withdraw-checks')){
    const source=fs.readFileSync(filename,'utf8'),folder=fs.mkdtempSync(path.join(os.tmpdir(),'r16-probe-withdrawal-'));
    const items=[
      ['R16_WITHDRAW_ALL_FIVE_HITS','reachable:visible&&points.every(point=>point.hit)','reachable:visible&&points.some(point=>point.hit)','R16_EVERY_PROBE_REQUIRED'],
      ['R16_WITHDRAW_ENTRY_OCCLUSION','observation.reachable===true && observation.points?.length===5 &&\n    observation.points.every(point=>point.hit===true)','observation.points?.length===5','R16_ENTRY_REJECTS_OCCLUDED_POINT'],
      ['R16_WITHDRAW_THREE_SIZE_SWEEP','for(const size of sizes){','for(const size of sizes.slice(0,2)){','R16_ALL_THREE_SIZES_BEFORE_ASSERTION']
    ];
    try{
      const run=file=>spawnSync(process.execPath,[__filename,'--probe',file],{encoding:'utf8',timeout:30000});
      const baseline=run(filename);assert.equal(baseline.status,0,baseline.stderr);
      const results=[];
      for(const [id,before,after,marker] of items){
        assert.equal(source.split(before).length,2,id+' exact anchor');
        const temporary=path.join(folder,id+'.cjs');fs.writeFileSync(temporary,source.replace(before,after));
        const mutant=run(temporary);assert.equal(mutant.status,1,id+mutant.stderr);
        assert.ok(mutant.stderr.includes(marker),id+' named assertion');
        fs.writeFileSync(temporary,source);const restored=run(temporary);
        assert.equal(restored.status,0,id+restored.stderr);
        assert.equal(fs.readFileSync(temporary,'utf8'),source,id+' exact restore');
        results.push({id,marker,baselineMutantRestoredExit:[baseline.status,mutant.status,restored.status]});
      }
      console.log(JSON.stringify({schema:'r16-reachability-node-withdrawals/1',browserExecuted:false,
        probeSha256:createHash('sha256').update(source).digest('hex'),results},null,2));
    }finally{fs.rmSync(folder,{recursive:true,force:true});}
  }else{
    const checks=await contract(api);
    console.log(JSON.stringify({schema:'r16-reachability-node-selftest/1',browserExecuted:false,checks}));
  }
}
if(require.main===module)main().catch(error=>{console.error(error);process.exitCode=1;});
module.exports={contract};
