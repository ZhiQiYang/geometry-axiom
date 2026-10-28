/* Narrow non-DOM contract controls; true face-entry coverage lives in CDP. */
"use strict";
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),test=require('node:test');
function environment(){
  const project={id:'project',contextToken:'context',revision:0},context={},history={frame:{ids:new Map([[4,{}]])},undo:[],redo:[]};
  const state={finishSurfaces:[],panelFills:[],derivedPlacements:[]},calls=[];
  const c={console,AbortSignal,Set,Map,Number,JSON,Error,Promise};c.window=c;c.globalThis=c;c.addEventListener=()=>{};
  c.connection={session:'session',phase:'ready'};
  c.ReferenceWorkspace={context:()=>context,getProjectState:()=>project,history,assertEditable(){},assertAssemblyIdle(){}};
  c.reply=()=>({ok:true,revision:0,complete:false,uiContract:{schema:'panel-fill-workspace/1',supportedActions:['read','edit-definitions','read-layout','read-support'],
    scope:{finishSurfaceIds:[],fillIds:[]},revision:'0',completeForScope:true,errors:[],state}});
  c.apiRequest=async command=>{calls.push(command);if(command==='panel-fill-read')return c.reply();
    if(command==='engineering-read')return {ok:true,state:{parameters:[],materials:[],specs:[]}};
    if(command==='objects')return {ok:true,columns:[],beams:[]};if(command==='newid')return {ok:true,finishSurface:1,panelFill:1,placement:0};
    return {ok:true,history_changed:true};};
  c.checkApiSession=()=>{};
  vm.createContext(c);for(const file of ['panel-fill-adapter.js','panel-fill-workspace.js'])vm.runInContext(fs.readFileSync(file==='panel-fill-adapter.js'&&process.env.PF_UI_ADAPTER_PATH?process.env.PF_UI_ADAPTER_PATH:path.join(__dirname,'../geometry-web',file),'utf8'),c,{filename:file});
  return {c,project,context,history,state,calls,A:c.PanelFillAdapter,W:c.PanelFillWorkspace};
}
test('UI14 explicit contract permits global complete:false but rejects absent/unknown actions and scope loss',()=>{
  const {c,A}=environment();assert.equal(A.contract(c.reply()).completeForScope,true);
  for(const change of [r=>delete r.uiContract,r=>r.uiContract.supportedActions.push('suggest-timbers'),r=>r.uiContract.scope.fillIds.push(8),r=>r.uiContract.revision='1']){
    const r=c.reply();change(r);assert.throws(()=>A.contract(r));
  }
});
test('UI03 exact area remains a decimal string; D1 definition coordinates are explicitly narrowed',()=>{
  const {A}=environment();const record={id:1,name:'完成面',boundaryId:4,frame:{origin:['0','0','2480'],U:'+X',V:'+Y',N:'+Z'},structureSide:1,obstacles:[],derived:{area:'10000000000000001'}};
  assert.deepEqual(JSON.parse(JSON.stringify(A.definition(record,'finish').frame.origin)),[0,0,2480]);
  assert.equal(record.derived.area,'10000000000000001');record.frame.origin[0]='9007199254740993';assert.throws(()=>A.definition(record,'finish'));
});
test('UI06 unchanged definitions emit no operations; same value different source stays different',()=>{
  const {W}=environment(),finish={id:1,name:'完成面',boundaryId:4,frame:{origin:['0','0','2480'],U:'+X',V:'+Y',N:'+Z'},structureSide:1,obstacles:[]};
  const fill={id:1,finishSurfaceId:1,panel:{id:'board',version:1},lengthAlong:'v',origin:[0,0],gap:3,pattern:'straight',threshold:{parameterId:90,fieldId:1}};
  const s={boundaryId:4,selection:{finish:1,fill:1,host:null},snapshot:{finishSurfaces:[finish],panelFills:[{definition:fill}],derivedPlacements:[]},draft:{finishId:1,name:'完成面',origin:['0','0','2480'],U:'+X',V:'+Y',N:'+Z',side:'1',obstacles:[],fill:true,fillId:1,panel:'["board",1]',lengthAlong:'v',fillOrigin:['0','0'],gap:{kind:'literal',value:'3'},pattern:'straight',threshold:'90:1',host:false}};
  assert.equal(W._test.operations(s).length,0);s.draft.gap={kind:'parameter',value:'90:2'};
  const ops=W._test.operations(s);assert.equal(ops.length,1);assert.equal(ops[0].op,'put-panel-fill');assert.equal(ops[0].value.gap.fieldId,2);
});
test('UI02 host id zero and typed sources preserve identity, never fallback to literal',()=>{
  const {W}=environment();for(const value of [{kind:'literal',value:30},{kind:'parameter',parameterId:90,fieldId:2},{kind:'spec',name:'depth'},{kind:'material',id:'wood',version:2,field:'B'}])
    assert.deepEqual(JSON.parse(JSON.stringify(W._test.sourceValue(W._test.sourceDraft(value,true),true))),value);
  assert.throws(()=>W._test.sourceDraft({kind:'application',id:'bad',field:'primary.B'},true));
});
test('UI05 late preview after input invalidation is cancelled and cannot become confirmable',async()=>{
  const {c,A,calls}=environment(),s=new A.Session(4);await s.read();let release;
  c.fetch=()=>new Promise(resolve=>{release=resolve;});const running=s.preview([{op:'put-finish-surface',value:{id:1}}]);
  s.changed();const r=c.reply();delete r.uiContract.state;r.uiContract.before=s.snapshot;r.uiContract.after=s.snapshot;
  release({ok:true,json:async()=>({ok:true,preview:{revision:0,valid:true,token:7,uiContract:r.uiContract}})});
  assert.equal(await running,null);assert.equal(s.phase,'editing');assert.equal(s.candidate,null);assert.ok(calls.includes('panel-fill-cancel 7'));
});
test('UI05 owner includes same-dump history identity and delete/recreate incarnation',()=>{
  const {A,history}=environment(),s=new A.Session(4);assert.equal(s.current(),true);
  history.undo.push({sameDump:true});assert.equal(s.current(),false);history.undo.pop();assert.equal(s.current(),true);
  history.frame.ids.set(4,{});assert.equal(s.current(),false);
});
test('UI05 unknown confirmation is not resent and only its original receipt recovers',async()=>{
  const {c,A,calls}=environment(),s=new A.Session(4);await s.read();s.phase='confirmable';s.candidate={token:9,generation:s.generation};
  const command=c.apiRequest;c.apiRequest=async text=>text==='panel-fill-confirm 9'?(calls.push(text),{ok:false,transport:true}):command(text);
  await s.confirm();assert.equal(s.phase,'unknown');await assert.rejects(()=>s.confirm());assert.equal(calls.filter(c=>c==='panel-fill-confirm 9').length,1);
  assert.equal(await s.reconcileReceipt({ok:true},'panel-fill-confirm 8'),false);
  assert.equal(await s.reconcileReceipt({ok:true},'panel-fill-confirm 9'),true);assert.equal(s.phase,'committed');assert.equal(s.dirty,false);
});
function populated(){
  const env=environment(),{state,c}=env;
  const finish={id:1,name:'完成面',boundaryId:4,frame:{origin:['0','0','0'],U:'+X',V:'+Y',N:'+Z'},structureSide:1,obstacles:[],
    derived:{n:'+Z',region:{outline:[['0','0'],['100','0'],['100','100'],['0','100']],holes:[]},obstacles:[]}};
  const fill={definition:{id:1,finishSurfaceId:1,panel:{id:'board',version:1},lengthAlong:'v',origin:[0,0],gap:0,pattern:'straight',threshold:{parameterId:90,fieldId:1}},
    derived:{tileCount:1,fragmentCount:1,wholeCount:1,cutCount:0,thickness:'9',threshold:{num:'17',den:'2'},tiles:[{key:[1,'0','0'],i:'0',j:'0',body:['0','0','100','100'],whole:true,fragments:[{key:[1,'0','0',0],area:'10000',outer:finish.derived.region.outline,holes:[]}]}],obstacles:[],seamLines:[],effectiveSeams:[],nonSeams:[],support:[],derivedPlacement:null}};
  state.finishSurfaces.push(finish);state.panelFills.push(fill);
  const emptyReply=c.reply;c.reply=()=>{const r=emptyReply();r.uiContract.scope={finishSurfaceIds:[1],fillIds:[1]};return r;};return env;
}
test('UI03 strict wire accepts exact complete native records and rejects missing derived data',()=>{
  const {c,A,state}=populated();assert.equal(A.contract(c.reply()).completeForScope,true);state.finishSurfaces[0].derived=null;
  assert.throws(()=>A.contract(c.reply()),/缺派生結果/);
});
test('UI14 strict wire rejects duplicated record identities',()=>{
  const {c,A,state}=populated();state.finishSurfaces.push(JSON.parse(JSON.stringify(state.finishSurfaces[0])));
  assert.throws(()=>A.contract(c.reply()),/重複身分/);
});
test('UI04 strict wire rejects nested obstacle errors presented as complete',()=>{
  const {c,A,state}=populated();state.finishSurfaces[0].obstacles=['b1'];state.finishSurfaces[0].derived.obstacles=[{ref:'b1',error:'D1 rejected'}];
  assert.throws(()=>A.contract(c.reply()),/內層障礙錯誤/);
});
test('UI03 strict wire rejects lossy numeric area and numeric rational threshold',()=>{
  const {c,A,state}=populated(),d=state.panelFills[0].derived;d.tiles[0].fragments[0].area=9999999600000003;
  assert.throws(()=>A.contract(c.reply()),/裁片精確面積/);d.tiles[0].fragments[0].area='9999999600000003';d.threshold.num=17;
  assert.throws(()=>A.contract(c.reply()),/精確支撐門檻/);
});
test('UI14 strict wire rejects missing cross-record source closure',()=>{
  const {c,A,state}=populated();state.panelFills[0].definition.finishSurfaceId=2;assert.throws(()=>A.contract(c.reply()),/完成面來源閉包/);
});
test('UI05 real preview adapter rejects self-consistent empty reply for a requested put',async()=>{
  const {c,A}=environment(),s=new A.Session(4);await s.read();const r=c.reply();delete r.uiContract.state;r.uiContract.before=s.snapshot;r.uiContract.after=s.snapshot;
  c.fetch=async()=>({ok:true,json:async()=>({ok:true,preview:{revision:0,valid:true,token:8,uiContract:r.uiContract}})});
  await assert.rejects(()=>s.preview([{op:'put-finish-surface',value:{id:1,name:'missing'}}]),/操作範圍/);assert.notEqual(s.phase,'confirmable');
});
test('UI05 real preview adapter rejects before state from another snapshot',async()=>{
  const {c,A}=populated(),s=new A.Session(4);await s.read();const r=c.reply();delete r.uiContract.state;r.uiContract.before={finishSurfaces:[],panelFills:[],derivedPlacements:[]};r.uiContract.after=s.snapshot;
  c.fetch=async()=>({ok:true,json:async()=>({ok:true,preview:{revision:0,valid:true,token:8,uiContract:r.uiContract}})});
  await assert.rejects(()=>s.preview([{op:'put-finish-surface',value:A.definition(s.snapshot.finishSurfaces[0],'finish')}]),/before/);assert.notEqual(s.phase,'confirmable');
});
test('UI05 recovered original receipt while reconnecting does not read or display stale results',async()=>{
  const {c,A,calls}=environment(),s=new A.Session(4);await s.read();s.phase='unknown';s.candidate={token:9,generation:s.generation};c.connection.phase='loading';
  const reads=calls.filter(x=>x==='panel-fill-read').length;assert.equal(await s.reconcileReceipt({ok:true,history_changed:false},'panel-fill-confirm 9'),true);
  assert.equal(s.phase,'committed');assert.equal(s.snapshotFresh,false);assert.match(s.reason,/零新增歷史/);assert.equal(calls.filter(x=>x==='panel-fill-read').length,reads);
});
test('UI06 obstacle selection order is a set while source identity remains exact',()=>{
  const {A}=environment(),a={obstacles:['c2','b3','c1'],name:'test'},b={obstacles:['c1','c2','b3'],name:'test'};
  assert.equal(A.sameDefinition(a,b,'finish'),true);b.obstacles=['c1','c2'];assert.equal(A.sameDefinition(a,b,'finish'),false);
});
test('UI02 ParameterRef zero IDs follow native uint32 identity rules',()=>{
  const {c,A,state}=populated();state.panelFills[0].definition.threshold={parameterId:0,fieldId:0};assert.equal(A.contract(c.reply()).completeForScope,true);
});
