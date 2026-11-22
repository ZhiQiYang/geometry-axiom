'use strict';

// Node/source regression only, NOT a layout engine or a Chrome receipt.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const {faceGuidanceProbe,faceGuidanceReady}=require('./r16_face_guidance_probe.cjs');
const root=path.resolve(__dirname,'../..');
const marker=/\/\* R123H_FACE_GUIDANCE_WIDTH_BEGIN\b[\s\S]*?\/\* R123H_FACE_GUIDANCE_WIDTH_END \*\//g;
const rect=(left,top,right,bottom)=>({left,top,right,bottom,width:right-left,height:bottom-top});
function fixture(){
  return {viewport:{width:390,height:844},pan:{shown:true},points:Array.from({length:5},()=>({hit:true})),
    help:{shown:true,parent:'faceWorkspaceTools',inDock:false,rect:rect(235,48,321,92),
      textRects:[rect(246,62,310,78)]}};
}
function judgeTests(){
  let checks=0;
  const good=fixture();assert.equal(faceGuidanceReady(good),true);checks++;
  const bad=(label,change)=>{const p=structuredClone(good);change(p);assert.equal(faceGuidanceReady(p),false,label);checks++;};
  for(let i=0;i<5;i++)bad('R123H_ALL_FIVE_PAN_HITS_REQUIRED '+i,p=>p.points.at(i).hit=false);
  bad('R123H_OVERHANG_NOT_EXCUSED_BY_FIVE_GOOD_HITS',p=>p.help.textRects=[rect(217.5,62,281.5,78)]);
  bad('R123H_RIGHT_OVERHANG_REJECTED',p=>p.help.textRects=[rect(246,62,322,78)]);
  bad('R123H_VERTICAL_OVERHANG_REJECTED',p=>p.help.textRects=[rect(246,47,310,78)]);
  bad('R123H_HELP_NOT_REMOVED',p=>p.help.shown=false);
  bad('R123H_HELP_TEXT_NOT_REMOVED',p=>p.help.textRects=[]);
  bad('R123H_HELP_TOUCH_WIDTH',p=>p.help.rect=rect(235,48,264,92));
  bad('R123H_HELP_TOUCH_HEIGHT',p=>p.help.rect=rect(235,48,321,82));
  bad('R123H_REAL_HELP_PARENT',p=>{p.help.parent='faceCanvasDock';p.help.inDock=true;});
  const source=fs.readFileSync(path.join(root,'geometry-web/workspace-guidance.js'),'utf8');
  assert.ok(source.includes('parent.append(help); state.help = help;'),'R123H_HELP_USES_CALLER_PARENT');checks++;
  const app=fs.readFileSync(path.join(root,'geometry-web/app.js'),'utf8');
  assert.ok(app.includes('parent: $(face ? "faceWorkspaceTools" : "canvasDrawToolbar")'),'R123H_SELECTION_HELP_PARENT');checks++;
  return checks;
}

// Bounded source cascade for width declarations that explicitly address the
// existing tool/help classes. It does not estimate fonts, paint or hit testing.
// Read stylesheet order from index.html; unknown relevant selectors fail closed.
function widthAt(viewport,withdraw=false){
  const html=fs.readFileSync(path.join(root,'geometry-web/index.html'),'utf8');
  const files=[...html.matchAll(/<link rel="stylesheet" href="([^"]+)"/g)].map(m=>m[1]);
  let order=0,winner={specificity:-1,order:-1,value:'auto',file:'initial'};
  const ancestors=[{tag:'button',id:'feSelectionSummaryHelp',classes:['tool-button','guidance-help']},
    {tag:'nav',id:'faceWorkspaceTools',classes:['face-workspace-tools']},
    {tag:'div',classes:['workspace-tools-row']},{tag:'header',classes:['object-workspace-topbar']},
    {tag:'section',id:'objectWorkspace',classes:['object-workspace']},{tag:'body',classes:[]},{tag:'html',classes:[]}];
  function matches(selector){
    if(!/^[\w.# >*-]+$/.test(selector))throw Error('R123H_UNSUPPORTED_WIDTH_SELECTOR '+selector);
    const tokens=selector.trim().split(/\s+/).reverse();let at=0,direct=true;
    for(const token of tokens){
      if(token==='>'){direct=true;continue;}
      const match=n=>(!token.match(/^[a-z]+/i)||n.tag===token.match(/^[a-z]+/i)[0])&&
        [...token.matchAll(/#([\w-]+)/g)].every(m=>n.id===m[1])&&
        [...token.matchAll(/\.([\w-]+)/g)].every(m=>n.classes.includes(m[1]));
      if(direct){if(!ancestors[at]||!match(ancestors[at]))return false;}
      else{while(ancestors[at]&&!match(ancestors[at]))at++;if(!ancestors[at])return false;}
      at++;direct=false;
    }
    return true;
  }
  function parse(text,enabled,file){
    let at=0;
    while(at<text.length){
      const open=text.indexOf('{',at);if(open<0)break;
      const selector=text.slice(at,open).trim();let end=open+1,depth=1;
      while(end<text.length&&depth){if(text[end]==='{')depth++;else if(text[end]==='}')depth--;end++;}
      assert.equal(depth,0,'R123H_BALANCED_CSS');const body=text.slice(open+1,end-1);at=end;
      if(selector.startsWith('@media')){
        const arms=selector.slice(6).split(',');
        const active=arms.some(arm=>{
          if(arm.includes('pointer: coarse'))return viewport<=560;
          const ranges=[...arm.matchAll(/\((min|max)-width:\s*(\d+)px\)/g)];
          if(!ranges.length)return false;
          return ranges.every(m=>m[1]==='min'?viewport>=Number(m[2]):viewport<=Number(m[2]));
        });parse(body,enabled&&active,file);continue;
      }
      if(selector.startsWith('@'))continue;
      const width=body.match(/(?:^|;)\s*width\s*:\s*([^;]+)/);if(!width)continue;
      for(const part of selector.split(',')){
        const s=part.trim();
        if(!/(?:\.tool-button|\.guidance-help)(?:[\w.-]*)$/.test(s))continue;
        const ordinal=++order;if(!enabled||!matches(s))continue;
        const specificity=(s.match(/#/g)||[]).length*100+(s.match(/\./g)||[]).length*10+(s.match(/(?:^|\s)[a-z]+/g)||[]).length;
        if(specificity>winner.specificity||specificity===winner.specificity&&ordinal>winner.order)
          winner={specificity,order:ordinal,value:width[1].trim(),file,selector:s};
      }
    }
  }
  for(const file of files){
    let text=fs.readFileSync(path.join(root,'geometry-web',file),'utf8');
    if(withdraw&&file==='workspace-height.css'){
      assert.equal([...text.matchAll(marker)].length,1,'R123H_EXACT_GUIDANCE_WITHDRAWAL');
      text=text.replace(marker,'');
    }
    parse(text.replace(/\/\*[\s\S]*?\*\//g,''),true,file);
  }
  return winner;
}
function main(){
  if(process.argv.includes('--expression')){console.log('('+faceGuidanceProbe.toString()+')()');return;}
  if(process.argv.includes('--replay-cloud-red')){
    const p=fixture();p.points[2]={hit:false,target:'feSelectionSummaryHelp'};
    assert.equal(faceGuidanceReady(p),true,'R123H_CONTROLS face 390 (published hit replay; no inferred box supplied)');return;
  }
  if(process.argv.includes('--withdraw-checks')){
    const run=extra=>{
      const r=spawnSync(process.execPath,[__filename,...extra],{cwd:root,encoding:'utf8',timeout:30000});
      assert.equal(r.error,undefined);assert.equal(r.signal,null);return {exit:r.status,stdout:r.stdout,stderr:r.stderr};
    };
    const baseline=run([]),withdrawn=run(['--withdraw']),restored=run([]);
    assert.deepEqual([baseline.exit,withdrawn.exit,restored.exit],[0,1,0]);
    assert.ok(withdrawn.stderr.includes('R123H_FACE_HELP_INTRINSIC_WIDTH 390'));
    console.log(JSON.stringify({browserExecuted:false,id:'R123H_WITHDRAW_FACE_GUIDANCE_INTRINSIC_WIDTH',
      scope:'Node source cascade, not browser mutation evidence',baseline,withdrawn,restored},null,2));return;
  }
  const checks=judgeTests(),widths=[390,560,561,768,1400].map(viewport=>({viewport,...widthAt(viewport,process.argv.includes('--withdraw'))}));
  console.log(JSON.stringify({browserExecuted:false,judgeChecks:checks,widths}));
  for(const row of widths)assert.ok(['auto','max-content','fit-content'].includes(row.value),
    'R123H_FACE_HELP_INTRINSIC_WIDTH '+row.viewport+': '+row.value);
}
if(require.main===module)try{main();}catch(error){console.error(error);process.exitCode=1;}
module.exports={widthAt,judgeTests};
