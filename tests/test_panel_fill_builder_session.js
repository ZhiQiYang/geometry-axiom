'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const filename=path.join(__dirname,'../geometry-web/panel-fill-builder-session.js');
const M=fs.existsSync(filename)?require(filename):{};
const clone=v=>JSON.parse(JSON.stringify(v));
const key='1'.repeat(64),setKey='a'.repeat(64);
const input={fillId:1,A:{kind:'literal',value:27},B:{kind:'literal',value:30},roles:{u:'secondary',v:'primary'}};
const dim=(value)=>({source:{kind:'literal',value},effective:String(value),unit:'mm',name:'明設尺寸',cardName:null,fieldName:null,path:'literal'});
const frame={origin:['0','0','0'],U:'+X',V:'+Y',N:'+Z'};
function state(host=false){return {
  finishSurfaces:[{id:1,name:'測試完成面',boundaryId:1,frame,structureSide:1,obstacles:[],derived:{n:'+Z',region:{outline:[['0','0'],['300','0'],['300','300'],['0','300']],holes:[]},obstacles:[]}}],
  panelFills:[{definition:{id:1,finishSurfaceId:1,panel:{id:'panel',version:1},lengthAlong:'u',origin:[0,0],gap:3,pattern:'straight',threshold:{parameterId:1,fieldId:1}},derived:{tileCount:0,fragmentCount:0,wholeCount:0,cutCount:0,thickness:'10',tiles:[],obstacles:[],seamLines:[],effectiveSeams:[],nonSeams:[],support:[],threshold:{num:'8',den:'1'},derivedPlacement:host?0:null}}],
  derivedPlacements:host?[{id:0,definition:{id:0,fillId:1,h:{kind:'literal',value:30}},derived:{h:'30',frame,components:[]}}]:[],
  fillGrids:host?[{id:0,definition:{id:0,hostId:0,fillId:1,mainAlong:'u'},derived:{indexSpace:'lattice',bandIndexSpace:'panel-row',side:1,staggerAxis:null,staggerDelta:'0',axes:{u:{baseCoordinate:'101',pitch:'103',baseIndex:'0'},v:{baseCoordinate:'101',pitch:'103',baseIndex:'0'}}}}]:[]
};}
function view(phase='ANALYSIS',selected=[]){return {schema:'panel-fill-builder-workspace/1',revision:'12',setKey,generation:'1',phase,selected,completeForScope:true,input:{fillId:1,primaryAlong:'u',A:dim(27),B:dim(30)},host:{id:0,created:true,h:dim(30)},grid:{id:0,created:true,mainAlong:'u'},timbers:[],uiContract:{schema:'panel-fill-workspace/1',revision:'12',supportedActions:['read','edit-definitions','read-layout','read-support','create-from-fill-grid','suggest-timbers'],completeForScope:true,errors:[],scope:{finishSurfaceIds:[1],fillIds:[1],fillGridIds:[0]},before:state(false),after:state(true)}};}
function entry(){return {key,phase:'seam-secondary',selectable:true,selected:false,valid:true,role:'secondary',axis:'v',source:{edgeKey:null,lineAxis:'u',k:'0',band:null,range:['0','300'],through:'150'},geometry:{rect:['101','0','128','300'],length:'300'},duplicateOf:null,diagnostics:[]};}
function suggestion(){return {ok:true,schema:'panel-fill-builder-suggestions/1',revision:'12',setKey,generation:'1',valid:true,confirmable:false,token:null,complete:false,intent:{schema:'panel-fill-builder-suggest/1',expectedRevision:'12',input,pre:[],post:[]},entries:[entry()],omissions:[],appView:view()};}
function preview(token=7){const appView=view('SELECTED',[key]);appView.timbers=[{id:1,before:null,after:{role:'secondary',A:dim(27),B:dim(30),geometry:{surface:0,centerline:'101',length:'300',u:'101',v:'0',dir:'+v',side:'+n',A:'27',B:'30',origin:['101','0','0'],axes:[['0','1','0'],['1','0','0'],['0','0','1']]}}}];return {ok:true,preview:{schema:'panel-fill-builder-preview/1',valid:true,token,revision:'12',phase:'SELECTED',candidateIdsAreTemporary:true,beforeScene:'before',afterScene:'after',entries:[{...entry(),selected:true}],omissions:[],createdDefinitions:[{tempKey:'r45:'+key,kind:'timber',candidateId:1}],reusedDefinitions:[],idMap:null,dependencies:{timbers:[],guides:[]},violations:[],appView}};}
function setup(options={}){
  assert.equal(typeof M.Session,'function','PF6_APP_SESSION_ENTRY: normal PF-6 owner must exist');
  let projectRevision=1,session='session-a',nativeRevision=options.revision??12;const context={};const history={frame:{context,ids:new Map([[1,'incarnation-a']])},undo:[],redo:[]};
  let lease=null;const calls=[];
  const host={history,context:()=>context,getProjectState:()=>({contextToken:'context-a',revision:projectRevision,id:'project-a'}),getEvidenceState:()=>({session,nativeRevision}),assertEditable(){assert.equal(lease,null);},
    beginTimberPreview(kind){assert.equal(lease,null);lease={kind,token:null};calls.push(['begin',kind]);return lease;},
    bindTimberPreview(owner,token){assert.equal(owner,lease);owner.token=String(token);},
    clearTimberPreviewToken(owner){assert.equal(owner,lease);owner.token=null;},
    assertTimberPreview(owner,token){assert.equal(owner,lease);if(token!==null)assert.equal(owner.token,String(token));},
    finishTimberPreview(owner){if(owner===lease)lease=null;},
    refreshTimberPreviewPresentation(owner){return owner===lease&&nativeRevision===12;}
  };
  const transport={async post(route,body,origin){calls.push([route,clone(body),origin]);if(options.post)return options.post(route,body,origin);return route.endsWith('/suggest')?suggestion():preview(options.token??7);},async command(command,origin){calls.push([command,origin]);if(options.command)return options.command(command,origin);return command.startsWith('pf6-confirm ')?{ok:true,history_changed:true,revision:'13'}:{ok:true,cancelled:true,revision:'12'};}};
  const s=new M.Session({host,transport,boundaryId:1,fillId:1,revision:options.revision??'12',snapshot:state(),sources:{},onChange(){}});
  return {s,host,calls,lease:()=>lease,setSession:v=>{session=v;},metadata:()=>{projectRevision++;},geometry:()=>{projectRevision++;nativeRevision++;}};
}
async function selected(setupValue){await setupValue.s.suggest(input);await setupValue.s.select([key]);await setupValue.s.preview();return setupValue;}
test('PF6_APP_EXPLICIT_INPUTS',async()=>{const h=setup();await assert.rejects(h.s.suggest({...input,A:null}),/明選|來源|input/i);assert.equal(h.calls.length,0);await h.s.suggest(input);assert.deepEqual(h.s.selected,[]);assert.equal(h.lease().kind,'pf6');assert.equal(h.s.confirmable,false);assert.equal(h.calls[1][1].expectedRevision,'12');assert.deepEqual(h.calls[1][1].pre,[]);assert.deepEqual(h.calls[1][1].post,[]);});
for(const phase of ['suggest','select'])for(const mode of ['unknown','duplicate','order','missing-old','missing-new'])test('PF6_APP_EMBEDDED_CAPABILITIES '+phase+' '+mode,async()=>{
 const h=setup({post:route=>{const result=route.endsWith('/suggest')?suggestion():preview();
  if(route.endsWith('/'+phase)){const c=(result.preview||result).appView.uiContract,actions=c.supportedActions;
   if(mode==='unknown')actions[5]='unknown-action';if(mode==='duplicate')actions.push(actions[0]);
   if(mode==='order')[actions[0],actions[1]]=[actions[1],actions[0]];
   if(mode==='missing-old')actions.splice(1,1);if(mode==='missing-new')actions.pop();}
  return result;}});
 if(phase==='select'){await h.s.suggest(input);await h.s.select([key]);}
 await assert.rejects(()=>phase==='suggest'?h.s.suggest(input):h.s.preview(),/投影|能力|完整/,'PF6_APP_EMBEDDED_CAPABILITIES '+phase+' '+mode);
 assert.equal(h.s.confirmable,false);assert.equal(h.calls.filter(c=>String(c[0]).startsWith('pf6-confirm ')).length,0);
 assert.equal(h.calls.filter(c=>c[0]==='pf6-cancel 7').length,phase==='select'?1:0,'PF6_APP_INCOMPLETE_CAPABILITY_CLEANUP');
});
test('PF6_APP_SELECTION_REVOKES_TOKEN_BEFORE_CANCEL_REPLY',async()=>{let cancelResolve;const h=await selected(setup({command:cmd=>cmd.startsWith('pf6-cancel ')?new Promise(r=>{cancelResolve=r;}):{ok:true}}));assert.equal(h.s.confirmable,true);const p=h.s.select([]);assert.equal(h.s.confirmable,false,'PF6_APP_KEEP_OLD_SELECTION_TOKEN');assert.equal(h.lease().token,null,'PF6_APP_KEEP_OLD_SELECTION_TOKEN');await assert.rejects(h.s.confirm(),/確認|候選/);cancelResolve({ok:true,cancelled:true});await p;assert.deepEqual(h.s.selected,[]);});
test('PF6_APP_INVALID_AND_INCOMPLETE_NEVER_CONFIRM',async()=>{for(const mode of ['invalid','incomplete','wrong-selection','wrong-source','wrong-before']){const h=setup({post:route=>{if(route.endsWith('/suggest'))return suggestion();const r=preview();if(mode==='invalid')r.preview.valid=false;if(mode==='incomplete')delete r.preview.appView.uiContract.after;if(mode==='wrong-selection')r.preview.appView.selected=[];if(mode==='wrong-source')r.preview.appView.input.B.source={kind:'spec',name:'same-value'};if(mode==='wrong-before')r.preview.appView.uiContract.before.finishSurfaces[0].name='另一份來源';return r;}});await h.s.suggest(input);await h.s.select([key]);await h.s.preview().catch(()=>{});assert.equal(h.s.confirmable,false,'PF6_APP_TOKEN_MEANS_VALID '+mode);await assert.rejects(h.s.confirm(),/確認|候選/);assert.equal(h.calls.some(c=>String(c[0]).startsWith('pf6-confirm ')),false);}});
test('PF6_APP_TOKEN_ZERO_IS_REJECTED while positive candidates use the shared lease',async()=>{
 for(const value of [0,'0']){
  const h=setup({token:value});await h.s.suggest(input);await h.s.select([key]);
  await assert.rejects(()=>h.s.preview(),/令牌|token|識別/,'PF6_APP_TOKEN_ZERO_IS_REJECTED');
  assert.equal(h.s.confirmable,false);assert.equal(h.s.cleanupToken,null);assert.equal(h.lease().token,null);
  await h.s.cancel();assert.equal(h.calls.some(c=>/^pf6-(cancel|confirm) 0$/.test(c[0])),false,'PF6_APP_ZERO_NEVER_DISPATCHED');
 }
 for(const value of [1,'7',4294967295]){const h=await selected(setup({token:value}));assert.equal(h.s.confirmable,true);assert.equal(h.lease().token,String(value));await h.s.cancel();}
});
test('PF6_APP_SUGGEST_AND_NOOP_HOLD_NULL_LEASE without manufacturing a token',async()=>{
 const h=setup({post:route=>{if(route.endsWith('/suggest'))return suggestion();const r=preview(null),p=r.preview;
  Object.assign(p,{phase:'NO_OP',afterScene:p.beforeScene,createdDefinitions:[],entries:[],appView:view('NO_OP',[])});
  p.appView.host={id:null,created:false,h:dim(30)};p.appView.grid={id:null,created:false,mainAlong:'u'};
  p.appView.uiContract.scope.fillGridIds=[];p.appView.uiContract.after=state(false);return r;}});
 await h.s.suggest(input);const owner=h.lease();assert.equal(owner.token,null,'PF6_APP_SUGGEST_NULL_LEASE');assert.equal(h.s.pending,true);
 await h.s.select([]);const p=await h.s.preview();assert.equal(p.phase,'NO_OP');assert.equal(h.lease(),owner,'PF6_APP_NOOP_SHARED_LEASE');
 assert.equal(owner.token,null,'PF6_APP_NOOP_NULL_LEASE');assert.equal(h.s.confirmable,false);assert.equal(h.s.pending,true);
 await h.s.cancel();assert.equal(h.lease(),null);assert.equal(h.calls.some(c=>/^pf6-(cancel|confirm) /.test(c[0])),false);
});
test('PF6_APP_INVALID_ANALYSIS_PREFIX_IS_NOT_SELECTABLE',async()=>{
 const h=setup({post:()=>{const r=suggestion();r.valid=false;r.error='last entry failed';return r;}});await h.s.suggest(input);
 assert.equal(h.s.suggestions.entries[0].valid,true);assert.equal(h.s.suggestions.entries[0].selectable,true);
 await assert.rejects(()=>h.s.select([key]),/整輪|完整/,'PF6_APP_INVALID_ANALYSIS_PREFIX_IS_NOT_SELECTABLE');
 await assert.rejects(()=>h.s.preview(),/完整|有效/,'PF6_APP_INVALID_ANALYSIS_PREVIEW_BLOCKED');
 assert.equal(h.calls.filter(c=>String(c[0]).endsWith('/select')).length,0);assert.equal(h.lease().token,null);await h.s.cancel();
});
test('PF6_APP_PREVIEW_IDS_ARE_TEMPORARY_AND_MAP_IS_RECEIPT_ONLY',async()=>{
 for(const mode of ['missing-flag','false-flag','early-map','missing-map','formal-id','duplicate-temp-key']){
  const h=setup({post:route=>{if(route.endsWith('/suggest'))return suggestion();const r=preview(),p=r.preview;
   if(mode==='missing-flag')delete p.candidateIdsAreTemporary;if(mode==='false-flag')p.candidateIdsAreTemporary=false;
   if(mode==='early-map')p.idMap=[{tempKey:'r45:'+key,kind:'timber',id:101}];if(mode==='missing-map')delete p.idMap;
   if(mode==='formal-id')p.createdDefinitions[0].id=101;
   if(mode==='duplicate-temp-key'){p.createdDefinitions.push({...p.createdDefinitions[0],candidateId:2});p.appView.timbers.push({...clone(p.appView.timbers[0]),id:2});}
   return r;}});await h.s.suggest(input);await h.s.select([key]);
  await assert.rejects(()=>h.s.preview(),/暫|正式|定義|對應/,'PF6_APP_TEMPORARY_ID_GUARD '+mode);
  assert.equal(h.s.confirmable,false);assert.equal(h.calls.filter(c=>c[0]==='pf6-cancel 7').length,1,'PF6_APP_BAD_PROJECTION_CANCELS_POSITIVE_TOKEN');
  assert.equal(h.calls.some(c=>String(c[0]).startsWith('pf6-confirm ')),false);
 }
});
test('PF6_APP_DEDUPLICATED_SOURCES_SHARE_A_CANDIDATE_ID',async()=>{
 const duplicateKey='2'.repeat(64),h=setup({post:route=>{
  if(route.endsWith('/suggest')){const r=suggestion();r.entries.push({...entry(),key:duplicateKey,duplicateOf:key});return r;}
  const r=preview(),p=r.preview;p.createdDefinitions.push({...p.createdDefinitions[0],tempKey:'r45:'+duplicateKey});
  p.entries.push({...entry(),key:duplicateKey,selected:true,duplicateOf:key});p.appView.selected.push(duplicateKey);return r;
 }});await h.s.suggest(input);await h.s.select([key,duplicateKey]);
 await assert.doesNotReject(()=>h.s.preview(),'PF6_APP_DEDUPLICATED_SOURCES_SHARE_A_CANDIDATE_ID');
 assert.equal(h.s.confirmable,true);assert.equal(h.s.candidate.createdDefinitions.length,2);assert.equal(h.s.candidate.appView.timbers.length,1);
 await h.s.cancel();
});
test('PF6_APP_CANCEL_AND_CONFIRM_SINGLE_DISPATCH',async()=>{const h=await selected(setup());await h.s.confirm();await assert.rejects(h.s.confirm(),/確認|候選/);assert.equal(h.calls.filter(c=>c[0]==='pf6-confirm 7').length,1);assert.equal(h.s.phase,'committed');assert.equal(h.lease(),null);const c=setup();await c.s.suggest(input);await c.s.cancel();assert.equal(c.calls.filter(r=>String(r[0]).startsWith('pf6-confirm ')).length,0);assert.equal(c.lease(),null);});
test('PF6_APP_UNKNOWN_CONFIRM_ORIGINAL_RECEIPT_ONLY',async()=>{const h=await selected(setup({command:()=>({ok:false,transport:true,error:'lost'})}));await h.s.confirm();assert.equal(h.s.phase,'unknown');await assert.rejects(h.s.confirm(),/確認|候選/);assert.equal(h.s.settleRecovered('pf6-confirm 7',{ok:true},'session-b'),false,'PF6_APP_RECEIPT_CURRENT_SESSION');assert.equal(h.s.phase,'unknown');assert.equal(h.s.settleRecovered('pf6-confirm 7',{ok:true,history_changed:true},'session-a'),true);assert.equal(h.s.phase,'committed');assert.equal(h.calls.filter(c=>c[0]==='pf6-confirm 7').length,1);});
test('PF6_APP_LATE_INVALID_POSITIVE_TOKEN_IS_CLEANED',async()=>{let resolve;const h=setup({post:route=>route.endsWith('/suggest')?suggestion():new Promise(r=>{resolve=r;})});await h.s.suggest(input);await h.s.select([key]);const pending=h.s.preview();const cancelled=h.s.cancel();const r=preview(7);r.preview.valid=false;resolve(r);await pending.catch(()=>{});await cancelled;assert.ok(h.calls.some(c=>c[0]==='pf6-cancel 7'),'PF6_APP_LATE_INVALID_POSITIVE_TOKEN_IS_CLEANED');assert.equal(h.s.confirmable,false);assert.equal(h.lease(),null);});
test('PF6_APP_INVALID_SELECTED_RETAINS_POSITIVE_CLEANUP_TOKEN',async()=>{
 const h=setup({post:route=>{if(route.endsWith('/suggest'))return suggestion();const r=preview();r.preview.valid=false;return r;}});
 await h.s.suggest(input);await h.s.select([key]);await h.s.preview();assert.equal(h.s.phase,'rejected');assert.equal(h.s.cleanupToken,'7','PF6_APP_INVALID_SELECTED_CLEANUP_TOKEN');
 assert.equal(h.s.pending,true);assert.equal(h.lease().token,null);assert.equal(h.s.confirmable,false);
 await h.s.cancel();assert.equal(h.calls.filter(c=>c[0]==='pf6-cancel 7').length,1);assert.equal(h.lease(),null);
});
test('PF6_APP_SOURCE_CHANGE_INVALIDATES_BUT_CANVAS_POS_PRESERVES',async()=>{const h=await selected(setup());h.metadata();assert.equal(h.s.current(),true,'PF6_APP_CANVAS_POS_EXPIRES');assert.equal(h.s.confirmable,true);h.geometry();assert.equal(h.s.current(),false);await assert.rejects(h.s.confirm(),/來源|失效|變更/);assert.equal(h.calls.filter(c=>c[0]==='pf6-confirm 7').length,0);});
test('PF6_APP_UINT64_STRINGS_PRESERVE_EXACT_VALUE',()=>{assert.equal(typeof M.uint64,'function','PF6_APP_SESSION_ENTRY');assert.equal(M.uint64('18446744073709551615'),true);assert.equal(M.uint64('18446744073709551616'),false);assert.equal(M.uint64('012'),false);assert.equal(M.uint64(12),false);});
test('PF6_APP_UINT64_REVISION_GENERATION_FLOW remains exact through suggest select and lease pins',async()=>{
 const revision='18446744073709551614',generation='18446744073709551615';
 const h=setup({revision,post:route=>{const r=route.endsWith('/suggest')?suggestion():preview(),p=r.preview||r;
  p.revision=revision;p.generation=generation;p.appView.revision=revision;p.appView.generation=generation;p.appView.uiContract.revision=revision;return r;}});
 await selected(h);assert.equal(h.s.owner.nativeRevision,revision,'PF6_APP_UINT64_OWNER_EXACT');assert.equal(h.s.confirmable,true);
 const request=h.calls.find(c=>c[0]==='/panel-fill/builder/select')[1];assert.equal(request.expectedRevision,revision,'PF6_APP_UINT64_REQUEST_EXACT');assert.equal(request.generation,generation,'PF6_APP_UINT64_GENERATION_EXACT');
 await h.s.cancel();
});
test('PF6_APP_DEFINITION_ZERO_IS_VALID independently of preview tokens',()=>{
 assert.equal(typeof M.source,'function','PF6_APP_SESSION_ENTRY');
 assert.equal(M.source({kind:'parameter',parameterId:0,fieldId:0},'A'),true,'PF6_APP_PARAMETER_ZERO_VALID');
 assert.doesNotThrow(()=>M.validateInput({...input,fillId:0,A:{kind:'parameter',parameterId:0,fieldId:0}},0),'PF6_APP_FILL_ZERO_VALID');
 const snapshot=state();snapshot.finishSurfaces[0].id=0;snapshot.finishSurfaces[0].boundaryId=0;
 snapshot.panelFills[0].definition.id=0;snapshot.panelFills[0].definition.finishSurfaceId=0;
 const h=setup();assert.doesNotThrow(()=>new M.Session({host:h.host,transport:{},boundaryId:0,fillId:0,revision:'12',snapshot,sources:{}}),'PF6_APP_BOUNDARY_ZERO_VALID');
});
test('PF6_APP_FORMAL_ID_MAP_COMES_ONLY_FROM_CONFIRM_RECEIPT',async()=>{
 for(const recovered of [false,true]){
  const receipt={ok:true,history_changed:true,revision:'13',actionReceipt:{idMap:[{tempKey:'r45:'+key,kind:'timber',id:101}]}};
  const h=await selected(setup({command:()=>recovered?{ok:false,transport:true}:receipt}));
  assert.equal(h.s.candidate.idMap,null);assert.equal(h.s.candidate.createdDefinitions[0].candidateId,1);
  await h.s.confirm();if(recovered)assert.equal(h.s.settleRecovered('pf6-confirm 7',receipt,'session-a'),true);
  assert.equal(h.s.phase,'committed');assert.equal(h.s.candidate,null);assert.deepEqual(h.s.receipt,receipt);
  assert.deepEqual(h.s.committedDefinitions,[{tempKey:'r45:'+key,kind:'timber',candidateId:1}],'PF6_APP_CONFIRMED_TEMP_KEYS_RETAINED');
  assert.equal(h.s.receipt.actionReceipt.idMap[0].id,101);assert.equal('candidateId' in h.s.receipt.actionReceipt.idMap[0],false);
 }
});
test('PF6_APP_MISSING_WORLD_GEOMETRY_IS_NOT_COMPLETE',async()=>{for(const mode of ['origin','omitted-member']){const h=setup({post:route=>{if(route.endsWith('/suggest'))return suggestion();const r=preview();if(mode==='origin')delete r.preview.appView.timbers[0].after.geometry.origin;else r.preview.appView.timbers=[];return r;}});await h.s.suggest(input);await h.s.select([key]);await h.s.preview().catch(()=>{});assert.equal(h.s.confirmable,false,'PF6_APP_COMPLETE_GEOMETRY '+mode);}});

async function realHost(options={}){
  assert.equal(typeof M.Session,'function','PF6_APP_SESSION_ENTRY');
  const f=await require('./fixtures/reference_workspace_vm.cjs').fixture(),w=f.w,env=f.env;
  env.connection.session='origin-service';w.observeNativeRevision({revision:'12'});
  const functions=fs.readFileSync(path.join(__dirname,'../geometry-web/app.js'),'utf8'),names=['checkApiSession','readApiReceipt','panelFillBuilderPost','recoverApiResults','apiRequest'];
  const code=names.map(name=>{const value=functions.match(new RegExp('^(?:async )?function '+name+'\\([\\s\\S]*?\\n}', 'm'));assert.ok(value,'PF6_APP_SHIPPING_API '+name);return value[0];}).join('\n');
  Object.assign(env,{ReferenceWorkspace:w,performance,pendingApiResults:new Map(),pendingApiSessions:new Map(),acknowledgedApiResults:new Set(),pendingAssemblyConfirmations:new Map(),apiRecoveryNeedsAbort:false,
    connectionFailed:message=>{env.connection.phase='error';env.connection.error=message;env.window.PanelFillBuilderWorkspace?.invalidate(message);}});
  const requests=[],receipts=new Map();let allowReceipts=false;
  env.fetch=async(route,request)=>{
    const body=JSON.parse(request.body);requests.push({route,body:clone(body),headers:clone(request.headers)});
    const answer=(value,stale=false)=>({ok:!stale,headers:{get:name=>name==='X-Geometry-Session'?'origin-service':name==='X-Geometry-Stale'&&stale?'1':null},json:async()=>clone(value)});
    if(body.receipt){if(!allowReceipts)throw Error('receipt temporarily unavailable');return answer({ok:true,result:receipts.get(body.receipt)});}
    let result;if(route.endsWith('/suggest'))result=suggestion();else if(route.endsWith('/select'))result=preview(7);
    else if(body.cmd.startsWith('pf6-confirm '))result=options.confirmResult||{ok:true,history_changed:true,revision:'13'};
    else if(body.cmd.startsWith('pf6-cancel '))result={ok:true,cancelled:true,history_changed:false,revision:'12'};
    else if(body.cmd.startsWith('line canvas-pos '))result={ok:true,history_changed:false,revision:'12'};
    else throw Error('unexpected '+body.cmd);
    const id=body.requestId||request.headers['X-Geometry-Request-Id'];receipts.set(id,result);
    if(options.selectGate&&route.endsWith('/select'))await options.selectGate;
    if(options.lost==='confirm'&&body.cmd?.startsWith('pf6-confirm ')||options.lost==='select'&&route.endsWith('/select'))throw Error('response lost after native result');
    return answer(result,options.stale&&body.cmd?.startsWith('pf6-confirm '));
  };
  require('node:vm').runInNewContext(code+'\nglobalThis.shipping={apiRequest,panelFillBuilderPost,recoverApiResults};',env);
  const s=new M.Session({host:w,transport:{post:(...args)=>env.shipping.panelFillBuilderPost(...args),command:cmd=>env.shipping.apiRequest(cmd)},boundaryId:1,fillId:1,revision:'12',snapshot:state(),sources:{}});
  env.window.PanelFillBuilderWorkspace={invalidate:reason=>s.invalidate(reason),settleRecovered:(cmd,result,origin)=>/^pf6-(suggest|select) /.test(cmd)?s.settlePreviewReceipt(cmd,result,origin):s.settleRecovered(cmd,result,origin),isRecoveryCancel:cmd=>s.cleanupToken!==null&&cmd==='pf6-cancel '+s.cleanupToken&&s.owner.session===env.connection.session};
  return {s,w,env,requests,allowReceipts:()=>{allowReceipts=true;},api:env.shipping.apiRequest,recover:env.shipping.recoverApiResults};
}
test('PF6_APP_REAL_HOST_POSITIVE_TOKEN_CANCEL_AND_ONE_HISTORY',async()=>{
  const h=await realHost(),before={undo:h.w.history.undo.length,state:clone(h.w.getProjectState())};
  await h.s.suggest(input);await h.s.select([key]);await h.s.preview();assert.equal(h.s.confirmable,true);await h.s.cancel();
  assert.deepEqual({undo:h.w.history.undo.length,state:clone(h.w.getProjectState())},before,'PF6_APP_REAL_CANCEL_NO_WRITE');
  await h.s.suggest(input);await h.s.select([key]);await h.s.preview();const result=await h.s.confirm();
  assert.equal(result.ok,true);assert.equal(h.w.history.undo.length,before.undo+1,'PF6_APP_REAL_ONE_HISTORY');
  assert.equal(h.requests.filter(r=>r.body.cmd==='pf6-confirm 7').length,1);assert.equal(h.w.getEvidenceState().nativeDefinitionRevision,'13');
});
test('PF6_APP_REAL_HOST_CANVAS_POS_RETAINS_CANDIDATE',async()=>{
  const h=await realHost();await h.s.suggest(input);await h.s.select([key]);await h.s.preview();
  const result=await h.api('line canvas-pos 1 17 29');assert.equal(result.ok,true,'PF6_APP_REAL_CANVAS_POS_WRITE');
  assert.equal(h.s.current(),true,'PF6_APP_REAL_CANVAS_POS_CURRENT');assert.equal(h.s.confirmable,true);
  await h.s.cancel();h.w.assertAssemblyIdle();
});
test('PF6_APP_REAL_UNKNOWN_CONFIRM_AND_LATE_SELECT_RECEIPTS',async()=>{
  for(const lost of ['confirm','select']){
    const h=await realHost({lost}),before=h.w.history.undo.length;await h.s.suggest(input);await h.s.select([key]);await h.s.preview().catch(()=>{});
    if(lost==='confirm')await assert.doesNotReject(()=>h.s.confirm(),'PF6_APP_CONFIRM_DISCONNECT_MUST_KEEP_RECEIPT');assert.equal(h.s.phase,'unknown');assert.equal(h.env.pendingApiResults.size,1);
    h.allowReceipts();h.env.connection.phase='loading';await h.recover();
    assert.equal(h.s.phase,lost==='confirm'?'committed':'cancelled','PF6_APP_REAL_RECOVER_PHASE');
    assert.equal(h.w.history.undo.length,before+(lost==='confirm'?1:0),'PF6_APP_REAL_RECOVER_HISTORY');
    assert.equal(h.env.pendingApiResults.size,0);h.w.assertAssemblyIdle();
    if(lost==='select')assert.equal(h.requests.filter(r=>r.body.cmd==='pf6-cancel 7').length,1,'PF6_APP_REAL_LATE_POSITIVE_CLEANUP');
    assert.equal(h.requests.filter(r=>lost==='select'?r.route.endsWith('/select'):r.body.cmd==='pf6-confirm 7').length,1,'PF6_APP_REAL_NO_RESEND');
    assert.ok(h.requests.filter(r=>r.body.receipt).every(r=>r.body.session==='origin-service'),'PF6_APP_REAL_ORIGIN_SESSION');
  }
});
test('PF6_APP_REAL_UNSENT_CANCEL_WAITS_FOR_CONNECTION_NOT_A_PHANTOM_RECEIPT',async()=>{
  let release;const h=await realHost({selectGate:new Promise(resolve=>{release=resolve;})}),before=h.w.history.undo.length;
  await h.s.suggest(input);await h.s.select([key]);const previewing=h.s.preview(),cancelling=h.s.cancel();
  h.env.connectionFailed('unrelated readonly response failed');release();await Promise.allSettled([previewing,cancelling]);
  assert.equal(h.env.pendingApiResults.size,0,'PF6_APP_UNSENT_HAS_NO_RECEIPT');
  assert.equal(h.s.phase,'cleanup-required','PF6_APP_CANCEL_UNSENT_IS_NOT_UNKNOWN');
  assert.equal(h.s.cleanupToken,'7');assert.equal(h.s.pendingCommand,null);assert.equal(h.s.confirmable,false);
  assert.equal(h.requests.filter(r=>r.body.cmd==='pf6-cancel 7').length,0,'PF6_APP_CANCEL_REALLY_NOT_SENT');
  h.env.connection.phase='ready';await h.s.cancel();
  assert.equal(h.requests.filter(r=>r.body.cmd==='pf6-cancel 7').length,1,'PF6_APP_UNSENT_CANCEL_SENDS_ONCE_AFTER_RECOVERY');
  assert.equal(h.s.phase,'cancelled');assert.equal(h.w.history.undo.length,before);h.w.assertAssemblyIdle();
});
test('PF6_APP_REAL_UNSENT_CONFIRM_CAN_RETRY_OR_CANCEL_WITHOUT_RESENDING_A_MUTATION',async()=>{
  for(const action of ['confirm','cancel']){
    const h=await realHost(),before=h.w.history.undo.length;await h.s.suggest(input);await h.s.select([key]);await h.s.preview();
    h.env.connection.phase='error';const rejected=await h.s.confirm();assert.equal(rejected.transport,true);
    assert.equal(h.env.pendingApiResults.size,0);assert.equal(h.s.phase,'confirm-not-sent','PF6_APP_CONFIRM_UNSENT_IS_NOT_UNKNOWN');
    assert.equal(h.s.pendingCommand,null);assert.equal(h.s.cleanupToken,'7');
    assert.equal(h.requests.filter(r=>r.body.cmd==='pf6-confirm 7').length,0);
    h.env.connection.phase='ready';if(action==='confirm'){assert.equal(h.s.confirmable,true);await h.s.confirm();}else await h.s.cancel();
    assert.equal(h.s.phase,action==='confirm'?'committed':'cancelled');assert.equal(h.w.history.undo.length,before+(action==='confirm'?1:0));
    assert.equal(h.requests.filter(r=>r.body.cmd==='pf6-confirm 7').length,action==='confirm'?1:0);h.w.assertAssemblyIdle();
  }
});

// 不建另一套租約模型：讓出貨的子表單在真 ReferenceWorkspace 上取得／退役 owner。
async function mountedBuilder(options={}){
  const h=await realHost(options),{env}=h;
  env.document.querySelector=()=>null; // 本 suite 不算 DOM 驗收
  env.window.PanelFillBuilderSession={Session:class extends M.Session{constructor(args){super(args);h.s=this;}}};
  require('node:vm').runInNewContext(fs.readFileSync(require.resolve('../geometry-web/panel-fill-builder-workspace.js'),'utf8'),env);
  const ui=env.window.PanelFillBuilderWorkspace;
  ui.open({boundaryId:1,contract:{revision:'12'},snapshot:state(),sources:{}},1);
  return {...h,ui};
}
for(const kind of ['suggested','selected','offline','unknown-confirm'])test('T36_RETIRE '+kind,async()=>{
  const h=await mountedBuilder({lost:kind==='unknown-confirm'?'confirm':null});
  const undo=h.w.history.undo.length;
  await h.s.suggest(input);
  if(kind!=='suggested'){await h.s.select([key]);await h.s.preview();}
  if(kind==='unknown-confirm')await h.s.confirm();
  if(kind==='offline')h.env.connection.phase='error';
  await h.ui.retireContext();
  assert.equal(h.ui.isOpen,false);
  const cancels=()=>h.requests.filter(r=>r.body.cmd?.startsWith('pf6-cancel '));
  if(kind==='unknown-confirm'||kind==='offline'){
    assert.equal(h.ui.pending,true);assert.equal(cancels().length,0);
    assert.equal(h.env.pendingApiResults.size,kind==='offline'?0:1);
    h.env.connection.phase='loading';h.allowReceipts();await h.recover();
  }
  assert.equal(h.ui.pending,false,'T36_RETIRED_OWNER_BLOCKS_PROJECT '+kind);
  h.w.assertAssemblyIdle();
  assert.deepEqual(cancels().map(r=>[r.body.cmd,r.body.session]),['selected','offline'].includes(kind)?[['pf6-cancel 7','origin-service']]:[]);
  assert.equal(h.w.history.undo.length,undo+(kind==='unknown-confirm'?1:0));
});

test('T36_D28_EXISTING_TIMBER',async()=>{
  const row=clone(preview().preview.appView.timbers[0].after);row.geometry.surface=9;
  for(const field of ['A','B'])row[field].source={kind:'application',id:'other-face',field:row.role+'.'+field};
  const h=setup({post:route=>{
    const r=route.endsWith('/suggest')?suggestion():preview();
    (r.preview||r).appView.timbers.push({id:99,before:clone(row),after:clone(row)});return r;
  }});
  await assert.doesNotReject(()=>h.s.suggest(input),'T36_D28_FORMAL_TIMBER_REJECTED');
  await h.s.select([key]);await h.s.preview();assert.equal(h.s.confirmable,true);
  await h.s.cancel();
  await assert.rejects(()=>h.s.suggest({...input,A:row.A.source}),/明選/,'T36_APPLICATION_IS_NOT_A_BUILDER_INPUT');
  for(const source of [{...row.A.source,field:'primary.A'},{...row.A.source,field:'secondary.B'},
    {...row.A.source,id:''},{...row.A.source,extra:1}]){
    const bad=clone(row);bad.A.source=source;const projected=view();projected.timbers=[{id:99,before:row,after:bad}];
    assert.throws(()=>M.validateView(projected,{revision:'12',setKey,generation:'1',phase:'ANALYSIS',input,selected:[]}),/角材尺寸/);
  }
});

// 實際的 apiRequest 會把 preview owner 移交給 confirmation；session.pending 不等於仍持有共享鎖。
for(const kind of ['stale','sealed','recovered-sealed'])test('T39_CONFIRM_NOT_DELIVERED '+kind,async()=>{
  const recovered=kind==='recovered-sealed',stale=kind==='stale';
  const h=await mountedBuilder({lost:recovered?'confirm':null,stale,
    confirmResult:{ok:false,error:stale?'版本不符':'操作未送達，場景未變更；請重新操作。'}});
  const before=h.w.history.undo.length;await selected(h);await h.s.confirm();
  if(recovered){
    assert.equal(h.s.phase,'unknown');assert.equal(h.env.pendingApiResults.size,1);
    await assert.rejects(h.s.cancel(),/回執/);h.env.connection.phase='loading';h.allowReceipts();await h.recover();
  }
  assert.equal(h.s.phase,'cleanup-required','T39_CONFIRM_REJECTION_LOST_CANDIDATE '+kind);
  assert.equal(h.ui.pending,true);assert.equal(h.s.cleanupToken,'7');assert.equal(h.s.pendingCommand,null);
  assert.equal(h.s.confirmable,false);await assert.rejects(h.s.confirm(),/候選/);
  assert.throws(()=>h.w.beginTimberPreview(),/候選/,'T39_SHARED_OWNER_RELEASED_EARLY');
  assert.throws(()=>h.w.assertTimberPreviewToken(7,'pf6'),/失效/,'T39_STILL_CONFIRMABLE_AT_HOST');
  h.s.invalidate();await assert.rejects(h.s.edit(),/請先完成/,'T39_ONLY_CANCEL_AFTER_INVALIDATION');
  h.env.connection.session='different-service';await assert.rejects(h.s.cancel(),/工作階段/);
  h.env.connection.session='origin-service';await h.ui.retireContext();
  assert.deepEqual(h.requests.filter(r=>/^pf6-(confirm|cancel) /.test(r.body.cmd)).map(r=>[r.body.cmd,r.body.session]),
    [['pf6-confirm 7','origin-service'],['pf6-cancel 7','origin-service']],'T39_ONLY_EXACT_CLEANUP');
  assert.equal(h.ui.pending,false);assert.equal(h.env.pendingApiResults.size,0);
  assert.equal(h.w.history.undo.length,before);const next=h.w.beginTimberPreview();h.w.finishTimberPreview(next);
});

// 對照：這些拒絕在原生 cmd_pf6_confirm 內已 pf6_pending_clear，不留假的待清理候選。
test('T39_NATIVE_CLEARED_CONFIRM',async()=>{
  for(const code of ['EXPIRED','INVALID','CAPACITY']){
    const h=await selected(await realHost({confirmResult:{ok:false,code,error:'World unchanged'}}));
    await h.s.confirm();assert.equal(h.s.phase,'rejected');assert.equal(h.s.pending,false);h.w.assertAssemblyIdle();
  }
});
