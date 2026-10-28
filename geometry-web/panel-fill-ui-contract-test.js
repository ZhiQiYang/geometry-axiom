/* Narrow non-DOM contract controls; true face-entry coverage lives in CDP. */
"use strict";
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const tests=[];const test=(name,run)=>tests.push({name,run});
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
  vm.createContext(c);for(const file of ['panel-fill-adapter.js','panel-fill-workspace.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,file),'utf8'),c,{filename:file});
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
(async()=>{let failures=0;for(const {name,run} of tests)try{await run();console.log('PASS '+name);}catch(error){failures++;console.error('FAIL '+name+'\n'+error.stack);}console.log(`${tests.length-failures} passed, ${failures} failed; unit-only, no true UI claim`);process.exitCode=failures?1:0;})();
