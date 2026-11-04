'use strict';
/* Independent fixed-head action/owner VM probe. Not browser or native E2E.
 * Executes extracted, unmodified app and ReferenceWorkspace function bodies.
 * Network/native state, history storage, DOM, and derived rendering are fakes.
 */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=process.env.GEOMETRY_REVIEW_ROOT||require('node:path').resolve(__dirname,'..');
const app=fs.readFileSync(root+'/geometry-web/app.js','utf8'),owner=fs.readFileSync(root+'/geometry-web/reference-workspace.js','utf8');
function extract(source,name){const re=new RegExp('(?:async\\s+)?function '+name+'\\s*\\('),m=re.exec(source);assert.ok(m,'function '+name);const start=m.index;let i=source.indexOf('{',start),depth=0,quote='',line=false,block=false,escape=false;
  // Function parameters here may contain object destructuring; find body via parens first.
  let p=source.indexOf('(',start),pd=0;for(;p<source.length;p++){if(source[p]==='(')pd++;if(source[p]===')'&&--pd===0)break;}i=source.indexOf('{',p);
  for(;i<source.length;i++){const c=source[i],n=source[i+1];if(line){if(c==='\n')line=false;continue;}if(block){if(c==='*'&&n==='/'){block=false;i++;}continue;}if(quote){if(escape){escape=false;continue;}if(c==='\\'){escape=true;continue;}if(c===quote)quote='';continue;}if(c==='/'&&n==='/'){line=true;i++;continue;}if(c==='/'&&n==='*'){block=true;i++;continue;}if(c==='"'||c==="'"||c==='`'){quote=c;continue;}if(c==='{')depth++;if(c==='}'&&--depth===0)return source.slice(start,i+1);}throw Error('unterminated '+name);
}
function harness({holdNewid=false,holdRender=false,holdFocus=false,holdCommand=null,selectionDenied=false,rejectDelete=false}={}){
  const commands=[],status=[],presentation=[],world={boundaries:[],spaces:[],positions:[]};let release,heldResolve,releaseRender,renderResolve,releaseFocus,focusResolve,releaseCommand,commandResolve;const held=new Promise(r=>heldResolve=r),gate=new Promise(r=>release=r),renderHeld=new Promise(r=>renderResolve=r),renderGate=new Promise(r=>releaseRender=r),focusHeld=new Promise(r=>focusResolve=r),focusGate=new Promise(r=>releaseFocus=r),commandHeld=new Promise(r=>commandResolve=r),commandGate=new Promise(r=>releaseCommand=r);
  const emptyClass={add(){},remove(){},toggle(){},contains(){return false;}},element={classList:emptyClass,hidden:true,closest(){return null;},setAttribute(){},click(){},getBoundingClientRect(){return {left:100,top:50,width:1000,height:700};}};
  let serial=0,context;
  const history={frame:{context:{id:'project-A',name:'A',dirty:false},ids:new Map()},group:null,undo:[],redo:[],replace(c){this.undo.push(this.frame);this.frame={context:c,ids:new Map()};}};
  const oc={busy:false,panX:40,panY:20,zoom:2,on:true,focus:null,selection:[],sel:null,surfs:[],bmap:{},navigationSequence:0};
  const response=result=>({ok:true,status:200,headers:{get:()=>null},json:async()=>result});
  const env={console,structuredClone,performance,Date,Map,Set,WeakSet,AbortSignal,crypto:require('node:crypto').webcrypto,setTimeout,clearTimeout,
    document:{body:{classList:emptyClass},activeElement:null,getElementById:()=>element,querySelectorAll:()=>[],querySelector:()=>null},$:()=>element,oc,ocv:element,OC_W:200,OC_H:156,SP_W:240,SP_H:180,
    window:{confirm:()=>true,dispatchEvent(){},DraftGate:{ask:()=>true}},CustomEvent:class {},connection:{phase:'ready',session:'session-a'},pageRuntimeVersion:'fixture',pendingApiResults:new Map(),acknowledgedApiResults:new Set(),pendingAssemblyConfirmations:new Map(),
    checkApiSession(){},confirmReferenceImpact:async()=>{throw Error('unused preview');},connectionFailed:m=>{throw Error(m);},
    history,context:()=>history.frame.context,revision:()=>0,fresh:()=>({id:'project-'+(++serial),name:'B',dirty:false}),busy:false,busyLabel:'',preparingSceneLoad:false,sceneTransaction:null,pendingLoad:null,contextConflict:false,
    assemblyConfirmation:null,roomTransaction:null,editorLease:'writable',editorLeaseSession:'session-a',scenarioContext:()=>null,scenarioBootstrap:'ready',scenarioInitializationPermit:null,
    nativePending:0,nativeRevision:0,projectRevision:0,nativeSession:'session-a',detachedPDFContexts:new Set(),recoveryDB:null,recoveryKey:null,recoveryReady:false,curScene:null,
    assertRoomDraftIdle(){},schedulePresentation(){},present(){},sync(){},scheduleRecovery(){},notifySceneChange(){},sceneMenuDisplay:s=>s,resetSceneFocus(){oc.focus=null;oc.selection=[];oc.sel=null;oc.navigationSequence++;},refreshActive:async()=>{},
    closeMenus(){},closePanels(){},renderObjects:async()=>{if(holdRender){renderResolve();await renderGate;}return true;},selectObject(){return true;},centerOnNode:(kind,id)=>presentation.push({kind:'center',project:history.frame.context.id,targetKind:kind,id}),setStatus:s=>status.push(s),toast:s=>status.push(s),pendingSlot:null,innerWidth:1400,view3:false,
    enterFocus:async(t,id)=>{presentation.push({kind:'focus',project:history.frame.context.id,t,id});oc.focus={t,id};oc.navigationSequence++;if(holdFocus){focusResolve();await focusGate;}},fe:{},fiShowTab(){},feSetTool:t=>{env.fe.tool=t;},feFit(){},loopsBBox:()=>({}),openPanel(){},
    ParameterUI:{create:()=>{}},setOcTool:t=>{oc.drawTool=t;},
    fetch:async(url,init)=>{if(url==='/upload'){commands.push({project:history.frame.context.id,cmd:'UPLOAD reset'});world.boundaries=[];world.spaces=[];world.positions=[];return response({ok:true,revision:1});}
      assert.equal(url,'/api');const {cmd}=JSON.parse(init.body);commands.push({project:history.frame.context.id,cmd});
      if(cmd==='newid'){if(holdNewid){heldResolve();await gate;}return response({ok:true,boundary:7,space:8});}
      if(cmd==='dump')return response({ok:true,text:'',revision:0});
      if(cmd==='line history-begin')history.group={base:structuredClone(world)};
      else if(cmd==='line history-abort'){Object.assign(world,history.group.base);history.group=null;}
      else if(cmd==='line history-end'){history.undo.push({project:history.frame.context.id});history.group=null;}
      else if(cmd.startsWith('line boundary ')){world.boundaries.push({project:history.frame.context.id,cmd});oc.bmap[7]=[];}
      else if(cmd.startsWith('line space '))world.spaces.push({project:history.frame.context.id,cmd});
      else if(cmd.startsWith('line canvas-pos '))world.positions.push({project:history.frame.context.id,cmd});
      else if(rejectDelete&&cmd.startsWith('line delete boundary '))return response({ok:false,error:'injected dependent boundary rejection'});
      if(holdCommand&&cmd.startsWith(holdCommand)){commandResolve();await commandGate;}
      return response({ok:true,revision:1});
    }};
  const appNames=['ocToCanvasPx','ocToCanvas','ocMenuCanvasPosition','ocCreateFromMenu','objNewSpace','objNewPolyFace','apiRequest','api','mutate','deleteObject','selectObject'];
  if(/function ocCreationOwner\s*\(/.test(app))appNames.unshift('ocCreationOwner');
  const ownerNames=['beginNativeOperation','assertConfirmationIdle','assertAssemblyIdle','assertEditorLease','assertWritableLease','assertEditable','beginSceneTransaction','finishSceneTransaction','unchanged','assertLoadContext','uploadScene','adoptLoadedContext','replaceWithEmpty','observeNativeRevision'];
  vm.createContext(env);vm.runInContext(ownerNames.map(n=>extract(owner,n)).join('\n')+'\n'+appNames.map(n=>extract(app,n)).join('\n'),env,{filename:'actual-fixed-head-functions.js'});
  env.ReferenceWorkspace={beginNativeOperation:env.beginNativeOperation,assertAssemblyIdle:env.assertAssemblyIdle,assertEditable:env.assertEditable,hasFeatureConfirmation:()=>false,
    observe(command,result){if(result.ok&&/^line (?:boundary|space|canvas-pos|delete) /.test(command))env.projectRevision++;},
    getProjectState:()=>({id:env.context().id,revision:env.projectRevision}),context:env.context,history};
  env.selectObject=(kind,id)=>{if(selectionDenied)return false;presentation.push({kind:'select',project:history.frame.context.id,targetKind:kind,id});oc.selection=[{kind,id}];oc.sel={kind,id};oc.navigationSequence++;return true;};
  return {env,commands,world,history,held,release,renderHeld,releaseRender,focusHeld,releaseFocus,commandHeld,releaseCommand,status,presentation};
}

const {test}=require('node:test');





for(const entry of ['btnNewSpace','btnCreatePoly'])test('R352 action retires across project replacement while newid reply is pending: '+entry,async()=>{
  const h=harness({holdNewid:true});
  const pending=h.env.ocCreateFromMenu(entry,{invocation:'pointer',clientX:500,clientY:300});
  await h.held;
  assert.equal(await h.env.replaceWithEmpty(false),true);
  const newProject=h.env.context().id;assert.notEqual(newProject,'project-A');
  h.release();await pending.catch(()=>{});
  const lateWrites=h.commands.filter(x=>x.project===newProject&&/^line (?:space|boundary|canvas-pos) /.test(x.cmd));
  assert.deepEqual(lateWrites,[],'a completed new-project switch must retire the old create operation');
});
test('R352 controls: action-time anchor, keyboard refusal, rectangle tool, grouped native delete',async()=>{
  const h=harness();h.env.oc.panX=80;h.env.oc.panY=-10;h.env.oc.zoom=4;
  assert.deepEqual(JSON.parse(JSON.stringify(h.env.ocMenuCanvasPosition({invocation:'pointer',clientX:500,clientY:300}))),{cx:-20,cy:-13});
  await assert.rejects(h.env.ocCreateFromMenu('btnCreatePoly',{invocation:'keyboard',clientX:500,clientY:300}),/指定建立位置/);assert.equal(h.commands.length,0);
  await h.env.ocCreateFromMenu('btnCreateRect',{invocation:'pointer',clientX:500,clientY:300});assert.equal(h.env.oc.drawTool,'rect');assert.equal(h.commands.length,0);
  const del=harness();del.env.oc.surfs=[{id:91,boundary:7}];await del.env.deleteObject('boundary',7);
  assert.deepEqual(del.commands.map(x=>x.cmd),['line history-begin','line delete placement 91','line delete boundary 7','line history-end']);
  const reject=harness({rejectDelete:true});reject.env.oc.surfs=[{id:91,boundary:7}];reject.env.oc.selection=[{kind:'boundary',id:7}];await reject.env.deleteObject('boundary',7);
  assert.equal(reject.commands.at(-1).cmd,'line history-abort');assert.equal(reject.env.oc.selection.length,1);
});
for(const entry of ['btnNewSpace','btnCreatePoly'])test('R352 ordinary creation stays functional: '+entry,async()=>{
  const h=harness();await h.env.ocCreateFromMenu(entry,{invocation:'pointer',clientX:500,clientY:300});
  const created=entry==='btnNewSpace'?h.world.spaces:h.world.boundaries;
  assert.equal(created.length,1);assert.equal(created[0].project,'project-A');assert.equal(h.world.positions.length,1);
  assert.ok(h.presentation.some(x=>x.kind==='select'));
  if(entry==='btnCreatePoly'){assert.equal(h.env.oc.focus?.id,7);assert.equal(h.env.fe.newOutline?.bid,7);}
});
for(const entry of ['btnNewSpace','btnCreatePoly'])test('R352 same-context navigation retires pending creation: '+entry,async()=>{
  const h=harness({holdNewid:true});const pending=h.env.ocCreateFromMenu(entry,{invocation:'pointer',clientX:500,clientY:300});await h.held;
  h.env.oc.navigationSequence++;h.release();await pending.catch(()=>{});
  assert.equal(h.commands.some(x=>/^line (?:space|boundary|canvas-pos) /.test(x.cmd)),false,'navigation after command starts must not borrow the new presentation');
});
for(const entry of ['btnNewSpace','btnCreatePoly'])test('R352 same project id with a fresh history frame retires creation: '+entry,async()=>{
  const h=harness({holdNewid:true});const pending=h.env.ocCreateFromMenu(entry,{invocation:'pointer',clientX:500,clientY:300});await h.held;
  // Explicit undo/redo-frame fault injection: same context and project id, new frame identity.
  h.history.frame={context:h.history.frame.context,ids:new Map()};h.release();await pending.catch(()=>{});
  assert.equal(h.commands.some(x=>/^line (?:space|boundary|canvas-pos) /.test(x.cmd)),false,'same context/id cannot revive an old frame owner');
});
test('R352 poly beforeCreate late completion cannot write a replacement project',async()=>{
  const h=harness();let release,started;const gate=new Promise(r=>release=r),held=new Promise(r=>started=r);
  const pending=h.env.objNewPolyFace({canvasPosition:{cx:1,cy:2},beforeCreate:async()=>{started();await gate;}});await held;
  await h.env.replaceWithEmpty(false);const newProject=h.env.context().id;release();await pending.catch(()=>{});
  assert.equal(h.commands.some(x=>x.project===newProject&&/^line (?:space|boundary|canvas-pos) /.test(x.cmd)),false);
});
test('R352 normal source import may call poly beforeCreate while its owner is busy',async()=>{
  const h=harness();h.env.busy=true;let called=0;
  const bid=await h.env.objNewPolyFace({beforeCreate:async allocated=>{assert.equal(allocated,7);called++;}});
  assert.equal(called,1);assert.equal(bid,7);assert.equal(h.world.boundaries.length,1);assert.equal(h.env.fe.newOutline?.bid,7);
});
test('R352 poly render completion rejects an externally replaced history frame',async()=>{
  const h=harness({holdRender:true});const pending=h.env.ocCreateFromMenu('btnCreatePoly',{invocation:'pointer',clientX:500,clientY:300});await h.renderHeld;
  assert.equal(h.world.boundaries.length,1,'old project has a completed original create');
  // Explicit external/history-recovery fault injection, independent of the input lock.
  h.history.frame={context:h.history.frame.context,ids:new Map()};h.releaseRender();await pending.catch(()=>{});
  assert.deepEqual(h.presentation,[],'late render must not select/focus using a retired frame');
  assert.equal(h.env.fe.newOutline,undefined);
});
test('R352 poly transaction prevents project replacement through the native write reply',async()=>{
  const h=harness({holdCommand:'line boundary '});const pending=h.env.ocCreateFromMenu('btnCreatePoly',{invocation:'pointer',clientX:500,clientY:300});await h.commandHeld;
  let rejected;try{await h.env.replaceWithEmpty(false);}catch(error){rejected=error;}
  h.releaseCommand();await pending;
  assert.match(rejected?.message||'',/請先完成目前的操作/,'new-project command must be refused while mutation is unsettled');
  assert.equal(h.env.context().id,'project-A');assert.equal(h.env.fe.newOutline?.bid,7);
});
test('R352 poly transaction keeps input lock until committed native render completes',async()=>{
  const h=harness({holdRender:true});const pending=h.env.ocCreateFromMenu('btnCreatePoly',{invocation:'pointer',clientX:500,clientY:300});await h.renderHeld;
  let rejected;try{await h.env.replaceWithEmpty(false);}catch(error){rejected=error;}
  h.releaseRender();await pending;
  assert.match(rejected?.message||'',/請先完成目前的操作/,'new-project command must be refused until derived rendering settles');
  assert.equal(h.env.context().id,'project-A');assert.equal(h.env.fe.newOutline?.bid,7);assert.equal(h.env.oc.busy,false);
});
for(const entry of ['btnNewSpace','btnCreatePoly'])test('R352 session replacement retires pending creation: '+entry,async()=>{
  const h=harness({holdNewid:true});const pending=h.env.ocCreateFromMenu(entry,{invocation:'pointer',clientX:500,clientY:300});await h.held;
  // Explicit session fault injection; transport header checks are mocked independently.
  h.env.connection.session='session-b';h.release();await pending.catch(()=>{});
  assert.equal(h.commands.some(x=>/^line (?:space|boundary|canvas-pos) /.test(x.cmd)),false);
});
for(const entry of ['btnNewSpace','btnCreatePoly'])test('R352 selection rejection stops creation presentation: '+entry,async()=>{
  const h=harness({selectionDenied:true});await h.env.ocCreateFromMenu(entry,{invocation:'pointer',clientX:500,clientY:300});
  assert.equal(h.world.spaces.length+h.world.boundaries.length,1,'completed original creation remains valid');
  assert.deepEqual(h.presentation,[],'DraftGate/select rejection must prevent focus or centering');assert.equal(h.env.fe.newOutline,undefined);
});
test('R352 poly delayed enterFocus cannot start redraw in a same-id face of a replacement project',async()=>{
  const h=harness({holdFocus:true});const pending=h.env.ocCreateFromMenu('btnCreatePoly',{invocation:'pointer',clientX:500,clientY:300});await h.focusHeld;
  await h.env.replaceWithEmpty(false);const newProject=h.env.context().id;
  // Explicitly arrange the same numeric boundary id in the replacement project.
  h.env.oc.focus={t:'face',id:7};h.env.oc.bmap[7]=[{verts:[[0,0],[5,0],[5,5],[0,5]],fixity:[1,1,1,1]}];
  h.releaseFocus();await pending.catch(()=>{});
  assert.equal(h.env.fe.newOutline,undefined,'old opening must not mark the new face for redraw');assert.notEqual(h.env.fe.tool,'redraw');
  assert.equal(h.env.context().id,newProject);
});
for(const entry of ['btnNewSpace','btnCreatePoly'])test('R352 changed project revision retires an allocated id before first write: '+entry,async()=>{
  const h=harness({holdNewid:true});const pending=h.env.ocCreateFromMenu(entry,{invocation:'pointer',clientX:500,clientY:300});await h.held;
  h.env.projectRevision++;h.release();await pending.catch(()=>{});
  assert.equal(h.commands.some(x=>/^line (?:space|boundary|canvas-pos) /.test(x.cmd)),false,'same owner must recheck the state on which newid was read');
});
test('R352 real ContextHistory records one polygon creation and one undo restores boundary identity',async()=>{
  const P=require(root+'/geometry-web/project-store.js');
  const h=harness();await h.env.ocCreateFromMenu('btnCreatePoly',{invocation:'pointer',clientX:500,clientY:300});
  const timeline=new P.ContextHistory(()=>({id:'history-project',groups:new Map(),sources:new Map(),featureAttachments:[]}));
  const originalFrame=timeline.frame;
  // Feed the exact successful handler commands to the real history observer.
  // Native World itself remains the explicit mock used by the action probe.
  for(const {cmd} of h.commands)timeline.observe(cmd,{ok:true},'session-a');
  assert.equal(timeline.undo.length,1);assert.equal(timeline.group,null);assert.equal(timeline.frame.ids.has(7),true);
  const incarnation=timeline.frame.ids.get(7);timeline.observe('line undo',{ok:true},'session-a');
  assert.equal(timeline.frame.ids.has(7),false);assert.equal(timeline.undo.length,0);assert.equal(timeline.redo.length,1);assert.notEqual(timeline.frame,originalFrame);
  timeline.observe('line redo',{ok:true},'session-a');assert.equal(timeline.frame.ids.get(7),incarnation);assert.equal(timeline.undo.length,1);assert.equal(timeline.redo.length,0);
});
