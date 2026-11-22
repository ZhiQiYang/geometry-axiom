'use strict';
/* R17 UI-adapter contracts, not native geometry or browser E2E.
 * Run the shipped workspace/impact scripts, app receipt dispatcher and lease
 * functions in a VM. Reuse the existing finite DOM and real ContextHistory.
 * HTTP results below are explicitly scripted protocol fixtures. They prove
 * routing, ownership and presentation gates, not geometry or actual HTTP. */
const {test:nodeTest}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {randomUUID}=require('node:crypto');
const {createDOM}=require('./_model_update_dom.js');
const root=process.env.GEOMETRY_BOUNDARY_PAIR_UI_ROOT||path.resolve(__dirname,'..');
const {ContextHistory}=require(path.join(root,'geometry-web/project-store.js'));
const test=(name,fn)=>nodeTest(name,{timeout:5000},fn),copy=structuredClone;
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
const read=file=>fs.readFileSync(path.join(root,'geometry-web',file),'utf8');
const app=read('app.js'),workspace=read('reference-workspace.js');
function section(source,start,end){
  const a=source.indexOf(start),b=source.indexOf(end,a+start.length);
  assert(a>=0&&b>a,'shipped function boundary must remain identifiable: '+start);
  return source.slice(a,b);
}
const leaseSource=section(workspace,'  function assertConfirmationIdle()','  function prepareFeatureConfirmation(')+
  section(workspace,'  function finishAssemblyConfirmation(','  const safe =');
const requestSource=section(app,'function checkApiSession(response)','// 離線只保留')+
  section(app,'async function apiRequest(cmd, roomLease = null)','async function api(cmd)');
const member=(id,edge,on=0)=>({id,role:'boundary',A:27,B:20,
  source:{surface:on,kind:'at-face',edge,dir:'+u',side:'+n'},order:id,
  interval:edge==='e0'?[0,500]:[500,1000],cross:edge==='e0'?[0,27]:[13,40],
  geometry:{surface:on,centerline:edge==='e0'?13:26,length:500,dir:'+u',side:'+n',
    A:27,B:20,origin:edge==='e0'?[0,0,2500]:[500,13,2500],axes:[[1,0,0],[0,1,0],[0,0,1]]}});
const group=()=>({first:7,second:9,ids:[7,9],on:0,members:[member(7,'e0'),member(9,'e2')],
  contacts:[{member:7,end:'END',peer:9,peerEnd:'START',plane:500,contact:[13,27]}]});
function preview({noOp=false}={}){
  const value=group(),side={members:value.members,contacts:value.contacts};
  const impact=m=>({...copy(m),boundaryPair:[value.first,value.second],contacts:[],source:{
    anchor:'at-face '+m.source.edge,selector:'',priority:1,surface:m.source.surface,dir:m.source.dir,side:m.source.side,
    dimensions:{A:{mode:'direct',value:m.A},B:{mode:'direct',value:m.B}}}});
  return {type:'boundary-pair',kind:noOp?'redeclare':'create',token:41,valid:true,noOp,command:'boundary-pair fixture',
    timbers:[],guides:[],grids:[],violations:[],
    boundaryPairs:[{first:7,second:9,capability:'boundary-pair/1',change:noOp?'unchanged':'created',before:noOp?copy(side):null,after:side}],
    timberImpacts:value.members.map(m=>({id:m.id,change:noOp?'unchanged':'created',before:noOp?impact(m):null,after:impact(m)}))};
}
function finiteDOM(){
  const dom=createDOM(),{Element,document}=dom,match=Element.prototype.matches;
  // Small standard DOM semantics missing from the existing finite fixture.
  // No layout, native event trust or browser parser is simulated here.
  Element.prototype.matches=function(selector){return selector.split(',').some(part=>match.call(this,part.trim()));};
  Element.prototype.closest=function(selector){for(let at=this;at;at=at.parentNode)if(at.matches(selector))return at;return null;};
  const html=Object.getOwnPropertyDescriptor(Element.prototype,'innerHTML');
  Object.defineProperty(Element.prototype,'innerHTML',{...html,set(value){html.set.call(this,value);
    for(const select of this.querySelectorAll('select')){const option=select.children.find(o=>o.getAttribute('selected')!==null);if(option)select.value=option.value;}}});
  document.addEventListener=()=>{};
  document.querySelector=selector=>document.body.querySelector(selector);
  return dom;
}
async function fixture(options={}){
  const {document}=finiteDOM(),pane=document.createElement('div');pane.id='faceInspectorContent';
  pane.innerHTML='<button id="btnDatums"></button><select id="tbPlacementMode"><option value="single">single</option><option value="boundary-pair">pair</option></select><div id="tbSinglePlacement"></div><section id="tbBoundaryPair" hidden></section>';
  document.body.append(pane);
  const history=new ContextHistory(()=>({id:'project-1',models:[],faceProjections:new Map(),featureAttachments:[]}));
  const project={revision:3,dirty:false,saved:true},calls=[],receipts=new Map(),listeners=new Map(),guards=[],toasts=[];
  const fe={sel:{kind:'timber',id:7},timberSelection:new Set([7]),tool:'select',panX:0,zoom:1};
  const oc={edit:{bid:1},focus:{t:'face',id:1},busy:false,
    surfs:[{id:0,outerEdges:[{edge:0,axis:'u'},{edge:1,axis:'v'},{edge:2,axis:'u'}]}],
    bmap:{1:[{fixity:[1,0,1],verts:[[0,0],[500,0],[500,13],[1000,13]]}]}};
  const native={session:'session-1',revision:'18',pending:null,commits:0,groups:options.groups??[group()],
    result:options.result??{ok:true,history_changed:false,revision:'18',ownerKey:'b'.repeat(64),preview:preview(options)},
    drop:null,blockReceipts:false,readGate:null};
  const env={console,structuredClone,crypto:{randomUUID},AbortSignal,setTimeout,clearTimeout,performance,
    Map,Set,BigInt,document,history,project,fe,oc,
    connection:{phase:'ready',known:true,session:native.session},pageRuntimeVersion:'unit-fixture',
    pendingApiResults:new Map(),acknowledgedApiResults:new Set(),pendingAssemblyConfirmations:new Map(),apiRecoveryNeedsAbort:false,
    assemblyConfirmation:null,timberPreview:null,roomTransaction:null,editorLease:'owned',editorLeaseSession:native.session,
    scenarioContext:()=>null,scenarioBootstrap:'ready',scenarioInitializationPermit:null,
    sceneTransaction:null,preparingSceneLoad:false,pendingLoad:null,contextConflict:false,busy:false,
    schedulePresentation(){},scheduleRecovery(){},revision:()=>project.revision,
    GeometryApplication:{woodworking:{section:{A:27,B:20}}},
    GeometryProject:require(path.join(root,'geometry-web/project-store.js')),
    feSid:()=>0,timberDirectionName:String,timberSideOptions:()=>[['+n','正面'],['-n','背面']],
    drawFaceEditor(){},feSetTool:tool=>{fe.tool=tool;},fiShowTab(){},innerWidth:1200,openPanel(){},
    toast:message=>toasts.push(message),
    CustomEvent:class {constructor(type,init){this.type=type;this.detail=init?.detail;}},
    connectionFailed:message=>{env.connection.phase='error';env.connection.error=message;},
    feAfterChange:async()=>{},ReferenceWorkspace:{}};
  const dispatch=event=>{for(const handler of listeners.get(event.type)||[])handler(event);};
  env.window={DraftGate:{register:fn=>guards.push(fn)},confirm:()=>true,
    addEventListener:(name,fn)=>{const list=listeners.get(name)||[];list.push(fn);listeners.set(name,list);},dispatchEvent:dispatch};
  env.renderFaceInspector=()=>env.window.BoundaryPairWorkspace?.afterInspectorRender(pane);
  const response=result=>({ok:true,status:200,headers:{get:key=>key==='X-Geometry-Session'?native.session:null},json:async()=>copy(result)});
  env.fetch=async(url,request)=>{
    const body=JSON.parse(request.body),headers=request.headers||{},record={url,body,headers};calls.push(record);
    if(url==='/boundary-pair/read'){
      const result={ok:true,schema:'boundary-pair-read-result/1',boundaryId:1,revision:native.revision,
        contextKey:'a'.repeat(64),groups:copy(native.groups)};
      const gate=native.readGate;native.readGate=null;if(gate)await gate.promise;
      return response(result);
    }
    let result,kind,id;
    if(url==='/boundary-pair/preview'){
      kind='preview';id=headers['X-Geometry-Request-Id'];
      assert.equal(headers['X-Geometry-Session'],native.session,'preview pins the service session');
      assert.match(id,/^[a-f0-9-]{36}$/,'preview has its own receipt ID');
      result=copy(native.result);if(result.ok)native.pending={token:result.preview.token,owner:result.ownerKey};
    }else{
      assert.equal(url,'/api');
      if(body.receipt){
        assert.equal(body.session,native.session,'receipt lookup stays in its original service');
        if(native.blockReceipts)throw Error('fixture receipt temporarily unavailable');
        assert(receipts.has(body.receipt),'lookup must name an issued request');
        return response({ok:true,result:receipts.get(body.receipt)});
      }
      assert.equal(typeof body.cmd,'string','real /api uses cmd, never command');
      id=body.requestId;kind=body.cmd.split(' ')[0].replace('boundary-pair-','');
      if(['confirm','cancel'].includes(kind)){
        const [,token,owner]=body.cmd.split(' ');
        assert.deepEqual({token:Number(token),owner},native.pending,'only the held candidate owner may be sent');
        const changed=kind==='confirm'&&!native.result.preview.noOp;
        if(changed)native.commits++;
        result={ok:true,history_changed:changed,transaction_id:Number(token),revision:changed?'19':'18',...(kind==='cancel'?{cancelled:true}:{})};
        native.pending=null;
      }else if(/^line (confirm \d+|cancel-preview)$/.test(body.cmd))result={ok:true,history_changed:false};
      else throw Error('unexpected fixture command: '+body.cmd);
    }
    if(id)receipts.set(id,copy(result));
    if(native.drop===kind){native.drop=null;throw Error('fixture lost '+kind+' reply after execution');}
    return response(result);
  };
  vm.createContext(env);vm.runInContext(leaseSource,env,{filename:'reference-workspace.js:lease-functions'});
  vm.runInContext('Object.assign(ReferenceWorkspace,{context,history,assertEditable,assertAssemblyIdle,beginTimberPreview,assertTimberPreview,bindTimberPreview,assertTimberPreviewToken,beginTimberConfirmation,finishTimberPreview,assemblyConfirmationCurrent,finishAssemblyConfirmation})',env);
  Object.assign(env.ReferenceWorkspace,{escape:String,getProjectState:()=>({...project,id:history.frame.context.id}),
    hasFeatureConfirmation:()=>false,hasEvidenceConfirmation:()=>false,
    observe:(command,result)=>{history.observe(command,result,env.connection.session);
      if(result.ok&&result.history_changed===true){project.revision++;project.dirty=true;project.saved=false;}}});
  vm.runInContext(requestSource,env,{filename:'app.js:receipt-functions'});
  vm.runInContext(read('reference-ui.js'),env,{filename:'reference-ui.js'});
  vm.runInContext(read('boundary-pair-workspace.js'),env,{filename:'boundary-pair-workspace.js'});
  if(options.ordinary)vm.runInContext(read('timber-edit.js'),env,{filename:'timber-edit.js'});
  const adapter=env.window.BoundaryPairWorkspace;
  adapter.afterInspectorRender(pane);await tick();await tick();
  const node=id=>{const value=document.getElementById(id);assert(value,'missing finite DOM node '+id);return value;};
  const mode=async value=>{node('tbPlacementMode').value=value;await node('tbPlacementMode').onchange();await tick();};
  const dialog=()=>document.body.descendants().find(value=>value.tagName==='DIALOG'&&value.open);
  const open=async()=>{await mode('boundary-pair');assert.equal(adapter.active(1),true);};
  const pick=()=>{assert.equal(adapter.pickHit(['e','0','0']),true);assert.equal(adapter.pickHit(['e','0','2']),true);};
  const raw=()=>[1,2].map(n=>['Anchor','A','B','Dir','Side'].map(field=>node('tbPair'+n+field).value));
  const awaitDialog=async()=>{for(let i=0;i<30&&!dialog();i++)await tick();assert(dialog(),'actual impact script must open a dialog');return dialog();};
  const recover=async()=>{native.blockReceipts=false;env.connection.phase='loading';await env.recoverApiResults();env.connection.phase='ready';};
  return {env,adapter,pane,node,mode,dialog,open,pick,raw,awaitDialog,recover,native,calls,history,project,guards,toasts,fe,oc,
    commands:()=>calls.filter(row=>row.url==='/api'&&row.body.cmd).map(row=>row.body.cmd),
    requests:kind=>calls.filter(row=>kind==='preview'?row.url==='/boundary-pair/preview':row.body.cmd?.startsWith('boundary-pair-'+kind+' ')),
    receiptIds:()=>calls.filter(row=>row.body.receipt).map(row=>row.body.receipt)};
}
async function startPreview(f){const pending=f.adapter.preview();await f.awaitDialog();return {pending};}
async function finish(f,approve){await f.node(approve?'impact-confirm':'impact-cancel').onclick();await tick();}

test('R335-UI-RAW: two edge picks stay raw and ordinary timber editing cannot consume them',async()=>{
  const f=await fixture({ordinary:true});await f.open();f.pick();
  f.node('tbPair1A').value='31';await f.node('tbPair1A').dispatch('input');const raw=f.raw();
  assert.equal(f.requests('preview').length,0);assert.equal(f.history.undo.length,0);
  await assert.rejects(f.env.window.TimberEdit.openBatch(),/互頂.*尚未保存/);
  assert.throws(()=>f.adapter.beforeSingleEntry(),/互頂.*尚未保存/);
  assert.equal(f.env.window.TimberEdit.renderInspector(f.pane),false);
  assert.deepEqual(f.raw(),raw);assert.equal(f.adapter.hasWork,true);
  assert.equal(f.guards.every(guard=>guard()),false,'leaving must not discard raw input');
  await f.adapter.close();assert.equal(f.adapter.hasWork,false);assert.equal(f.commands().length,0);
});

test('R335-UI-READ-OWNER: delayed group reads cannot overwrite a new mode, closed editor or selection',async()=>{
  for(const action of ['mode','close','selection','frame']){
    const f=await fixture(),gate=deferred();f.native.readGate=gate;
    const pending=f.adapter.openGroup(7);await tick();
    if(action==='mode'){await f.open();f.pick();f.node('tbPair1A').value='35';await f.node('tbPair1A').dispatch('input');}
    if(action==='close')await f.adapter.close();
    if(action==='selection'){f.fe.sel={kind:'timber',id:9};f.fe.timberSelection=new Set([9]);}
    if(action==='frame')f.history.frame={context:f.history.frame.context,ids:new Map()};
    const before=f.node('tbBoundaryPair').innerHTML;gate.resolve();
    await assert.rejects(pending,/選取|來源|專案/);
    assert.equal(f.node('tbBoundaryPair').innerHTML,before,action+' keeps the newer form');
    assert.equal(f.commands().length,0);assert.equal(f.history.undo.length,0);
  }
});

test('R335-UI-READONLY-PENDING: readonly or another real lease never prepares or cancels a pair',async()=>{
  const readonly=await fixture();readonly.env.editorLease='readonly';await readonly.mode('boundary-pair');
  assert.equal(readonly.adapter.active(1),false);assert.equal(readonly.requests('preview').length,0);
  assert.match(readonly.toasts.at(-1),/僅供查看/);assert.equal(readonly.history.undo.length,0);
  const f=await fixture();await f.open();f.pick();const foreign=f.env.ReferenceWorkspace.beginTimberPreview();
  await assert.rejects(f.adapter.preview(),/候選尚未結束/);
  assert.equal(f.requests('preview').length,0);assert.equal(f.commands().length,0);
  assert.equal(f.env.timberPreview,foreign,'pair does not consume another owner');
});

test('R335-UI-I8A-GATE: missing or empty pair facts cannot confirm even through a detached handler',async()=>{
  for(const damage of [p=>delete p.boundaryPairs,p=>p.boundaryPairs=[],p=>delete p.timberImpacts,
    p=>p.timberImpacts=[],p=>p.timberImpacts.pop(),p=>delete p.timberImpacts[0].after.source.dimensions,
    p=>delete p.timberImpacts[0].after.source.dimensions.A,p=>delete p.timberImpacts[0].after.source.dimensions.B,
    p=>delete p.timberImpacts[0].after.source.surface,p=>delete p.timberImpacts[0].after.source.dir,
    p=>delete p.timberImpacts[0].after.source.side]){
    const f=await fixture(),p=preview();damage(p);let confirms=0,cancels=0;
    const result=f.env.confirmReferenceImpact(p,{boundaryPair:true,confirm:async()=>{confirms++;return {ok:true};},cancel:async()=>{cancels++;return {ok:true};}});
    await f.awaitDialog();assert.equal(f.node('impact-confirm').disabled,true);
    await f.node('impact-confirm').onclick();assert.equal(confirms,0,'disabled handler must fail closed');
    await finish(f,false);assert.equal((await result).ok,false);assert.equal(cancels,1);
    assert.equal(f.commands().length,0);assert.equal(f.history.undo.length,0);
  }
});

test('R335-UI-GENERIC: groups in an upstream report do not switch the native confirmation route',async()=>{
  const f=await fixture(),result=f.env.confirmReferenceImpact(preview());await f.awaitDialog();
  assert.equal(f.node('impact-confirm').disabled,false);await finish(f,true);assert.equal((await result).ok,true);
  assert.deepEqual(f.commands(),['line confirm 41']);assert.equal(f.history.undo.length,0);
});

test('R335-UI-DIAGNOSTICS: discarded invalid candidates display violations with null token and no confirmation',async()=>{
  const diagnostics={...preview(),valid:false,token:null,violations:[{timber:7,clause:'D16a',expected:'one facing endpoint',actual:'no facing endpoint'}]};
  const f=await fixture({result:{ok:false,code:'BOUNDARY_PAIR_INVALID',error:'D16a rejected',diagnostics}});
  await f.open();f.pick();const {pending}=await startPreview(f);
  assert.equal(f.node('impact-confirm').disabled,true);assert.match(f.dialog().textContent,/D16a\n預期：one facing endpoint\n實際：no facing endpoint/);
  await f.node('impact-confirm').onclick();assert.equal(f.requests('confirm').length,0);
  await finish(f,false);assert.equal(await pending,false);
  assert.equal(f.requests('cancel').length,0,'discarded diagnostics own no native token');
  assert.equal(f.history.undo.length,0);assert.equal(f.env.timberPreview,null);assert.equal(f.adapter.hasWork,true);

  // The real P1-A diagnostic from the native core, not a JS geometry verdict.
  // Only this known clause + expectation is localized; unfamiliar text survives.
  const expected='two real end faces with opposite normals, one plane and positive contact';
  const actual='timber 1 [0,1000] 與 timber 2 [0,1000] 沒有恰一組相向端點同座標且寬向正長度接觸（寬向交集 0 mm）；P1-A：不互頂即整筆拒絕';
  for(const [clause,nativeExpected,shown] of [
    ['D16a',expected,'兩個真實端面須法向相反、位於同一平面，且有正長度接觸。'],
    ['unrecognized-clause',expected,expected],
    ['D16a',expected+'; additional constraint',expected+'; additional constraint']
  ]){
    const issue={timber:1,clause,expected:nativeExpected,actual};
    const rejected={...preview(),valid:false,token:null,violations:[issue]},original=copy(rejected);
    const isolated=await fixture();let confirms=0;
    const pending=isolated.env.confirmReferenceImpact(rejected,{boundaryPair:true,
      confirm:async()=>{confirms++;return {ok:false};},cancel:async()=>({ok:true})});
    await isolated.awaitDialog();
    const violation=isolated.dialog().descendants().find(node=>node.className==='impact-violation');
    assert(violation,'the actual shared impact renderer must create a violation row');
    assert.equal(violation.textContent,
      `角材 1 · ${clause}\n預期：${shown}\n實際：${actual}`,'R432_R17_P1A_EXPECTATION_PRESENTATION');
    assert.deepEqual(rejected,original,'translation must not rewrite the native diagnostic');
    assert.equal(isolated.node('impact-confirm').disabled,true);
    await isolated.node('impact-confirm').onclick();assert.equal(confirms,0);
    await finish(isolated,false);assert.equal((await pending).ok,false);
    assert.deepEqual(isolated.commands(),[]);assert.equal(isolated.history.undo.length,0);
  }
});

test('R335-UI-PREPARE-RECEIPT: lost preparation is queried once and only its exact owner is cancelled during recovery',async()=>{
  const f=await fixture();await f.open();f.pick();const raw=f.raw();
  f.native.drop='preview';f.native.blockReceipts=true;assert.equal(await f.adapter.preview(),false);
  const sent=f.requests('preview');assert.equal(sent.length,1);const id=sent[0].headers['X-Geometry-Request-Id'];
  assert.equal(f.env.pendingApiResults.get(id),'boundary-pair-preview '+id);
  assert.throws(()=>f.adapter.beforeSingleEntry(),/尚未保存/);assert.equal(f.history.undo.length,0);
  f.env.connection.phase='loading';
  assert.equal((await f.env.apiRequest('boundary-pair-cancel 99 '+'c'.repeat(64))).transport,true);
  assert.equal(f.requests('cancel').length,0,'loading exception does not authorize foreign cancellation');
  await assert.doesNotReject(f.recover(),'the original owner must finish receipt recovery during loading');
  assert.equal(f.requests('preview').length,1,'never retry preparation');
  assert.deepEqual(f.commands(),['boundary-pair-cancel 41 '+'b'.repeat(64)]);
  assert.deepEqual([...new Set(f.receiptIds())],[id]);assert.equal(f.env.pendingApiResults.size,0);
  assert.equal(f.env.timberPreview,null);assert.equal(f.native.pending,null);assert.deepEqual(f.raw(),raw);
  assert.equal(f.native.commits,0);assert.equal(f.history.undo.length,0);await f.adapter.close();
});

test('R335-UI-CONFIRM-RECEIPT: double click and lost reply settle the one exact confirmation without resending',async()=>{
  const f=await fixture();await f.open();f.pick();const {pending}=await startPreview(f);
  f.native.drop='confirm';f.native.blockReceipts=true;
  const detached=f.node('impact-confirm').onclick;await detached();await detached();await pending;
  const calls=f.requests('confirm');assert.equal(calls.length,1);const id=calls[0].body.requestId;
  assert.match(id,/^[a-f0-9-]{36}$/);assert.equal(f.native.commits,1);assert.equal(f.history.undo.length,0,'unknown reply is not local success');
  assert.equal(f.adapter.hasWork,true);await assert.rejects(f.adapter.close(),/結果尚未取得/);
  await f.recover();assert.equal(f.requests('confirm').length,1);assert.equal(f.history.undo.length,1);
  assert.equal(f.adapter.hasWork,false);assert.equal(f.env.assemblyConfirmation,null);
  assert.deepEqual([...new Set(f.receiptIds())],[id]);assert.equal(f.env.pendingApiResults.size,0);
});

test('R335-UI-CANCEL-RECEIPT: a lost cancellation keeps the lease until the matching receipt and preserves raw input',async()=>{
  const f=await fixture();await f.open();f.pick();const raw=f.raw(),{pending}=await startPreview(f);
  f.native.drop='cancel';f.native.blockReceipts=true;await finish(f,false);await pending;
  const sent=f.requests('cancel');assert.equal(sent.length,1);const id=sent[0].body.requestId;
  assert.notEqual(f.env.timberPreview,null);await assert.rejects(f.adapter.close(),/結果尚未取得/);
  await f.recover();assert.equal(f.requests('cancel').length,1);assert.equal(f.env.timberPreview,null);
  assert.deepEqual([...new Set(f.receiptIds())],[id]);assert.deepEqual(f.raw(),raw);
  assert.equal(f.requests('confirm').length,0);assert.equal(f.history.undo.length,0);assert.equal(f.native.commits,0);
  await f.adapter.close();assert.equal(f.adapter.hasWork,false);
});

test('R335-UI-NOOP: readonly queries and identical redeclaration do not invent a history entry',async()=>{
  const f=await fixture({noOp:true});const before=copy(f.project);
  assert.equal(await f.adapter.openGroup(7),true);assert.equal(f.history.undo.length,0);
  const {pending}=await startPreview(f);await finish(f,true);assert.equal(await pending,true);
  assert.equal(f.requests('confirm').length,1);assert.equal(f.history.undo.length,0);assert.equal(f.native.commits,0);
  assert.deepEqual(f.project,before);assert.equal(f.adapter.hasWork,false);
  assert(f.commands().every(command=>!command.startsWith('line history-')),'no history group substitutes for a candidate');
});

test('R335-UI-SESSION: recovery never releases an uncertain candidate into another native session',async()=>{
  const f=await fixture();await f.open();f.pick();f.native.drop='preview';f.native.blockReceipts=true;await f.adapter.preview();
  const [id,command]=[...f.env.pendingApiResults][0],lease=f.env.timberPreview;f.env.connection.session='session-2';
  await assert.rejects(f.adapter.settleRecovered(command,f.native.result),/原互頂工作階段/);
  assert.equal(f.env.pendingApiResults.has(id),true);assert.equal(f.env.timberPreview,lease);
  assert.equal(f.requests('cancel').length,0);assert.equal(f.history.undo.length,0);
});

test('R335-UI-GUIDE-SOURCE: equal geometry does not hide old and new guide sources',async()=>{
  const f=await fixture(),p=preview({noOp:true});
  const geometry={surface:0,axis:'v',off:27,worldPoint:[27,0,2500],worldDirection:[0,1,0],segments:[[[27,0],[27,1000]]]};
  p.guides=[
    {id:91,before:{...copy(geometry),source:'local',datum:0,expression:'timber:7:A'},after:{...copy(geometry),source:'local',datum:0,expression:'timber:9:A'}},
    {id:92,before:{...copy(geometry),source:'local',datum:0,expression:'27'},after:{...copy(geometry),source:'datum',datum:19,expression:''}}
  ];
  const result=f.env.confirmReferenceImpact(p,{boundaryPair:true,confirm:async()=>({ok:true}),cancel:async()=>({ok:true})});
  await f.awaitDialog();
  for(const id of [91,92])assert(f.dialog().descendants().some(node=>node.dataset.impactGuide===id),'source-only change must have its own visible guide row');
  const row=id=>f.dialog().descendants().find(node=>node.dataset.impactGuide===id).textContent;
  const expressions=row(91);
  assert.match(expressions,/timber:7:A/,'old authored expression must be visible despite equal geometry');
  assert.match(expressions,/timber:9:A/,'new authored expression must be visible despite equal geometry');
  assert.match(expressions,/local[\s\S]*timber:7:A[\s\S]*→[\s\S]*local[\s\S]*timber:9:A/,'both source kinds and expressions must retain old-to-new order');
  assert.match(row(92),/local[\s\S]*→[\s\S]*datum\s+19\b/,'datum rebinding must identify its actual new source');
  assert.equal(f.node('impact-confirm').disabled,false);await finish(f,false);assert.equal((await result).ok,false);
  assert.equal(f.commands().length,0);assert.equal(f.history.undo.length,0);
});
