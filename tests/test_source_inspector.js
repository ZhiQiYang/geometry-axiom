const {test}=require('node:test');
const assert=require('node:assert/strict');
const S=require(process.env.GEOMETRY_SOURCE_INSPECTOR_JS||'../geometry-web/source-inspector.js');
const hash=n=>String(n).padStart(64,'0');
const fs=require('node:fs'),vm=require('node:vm');
const locationData=(pid=20,tid=7)=>({ok:true,schema:'source-inspector/1',revision:5,sourceFingerprint:hash(5),complete:true,
  nodes:[['boundary',1],['placement',10],['placement',pid],['timber',tid]].map(([kind,id])=>({kind,id:String(id),key:S.key(kind,id),definitionFingerprint:hash(1),valueFingerprint:hash(1)})),
  edges:[{from:S.key('timber',tid),to:S.key('placement',pid),relation:'position',field:'surface',active:true},
    {from:S.key('placement',pid),to:'boundary:1',relation:'position',field:'boundary',active:true}]});
function navigationHarness(data=locationData()){
  const calls=[],context={id:'project',groups:new Map([[1,{activePageId:'page-a'}]])},state={id:'project',contextToken:'token',revision:0},history={frame:{},undo:[],redo:[]};
  const oc={focus:{t:'face',id:1,placementId:10},sel:null},fe={sel:null,timbers:[{id:7},{id:0}],grids:[],guides:[]};
  const sandbox={console,AbortSignal,innerWidth:1400,SourceInspector:S,oc,fe,window:{addEventListener(){},DraftGate:{ask:()=>true}},
    ReferenceWorkspace:{context:()=>context,getProjectState:()=>state,history},EngineeringWorkspace:{isOpen:false,configure(){}},
    document:{addEventListener(){},getElementById:()=>({}),querySelector:()=>null},
    apiRequest:async command=>{calls.push(command);return command==='source-inspect'?structuredClone(data):{ok:true,loops:[{verts:[[0,0],[4000,0],[4000,3000],[0,3000]]}]};},
    resetSceneFocus(){calls.push('resetFocus');oc.focus=null;fe.sel=null;},async setView3(){calls.push('setView3');},async renderObjects(){calls.push('renderObjects');},
    async enterFocus(t,id,options){calls.push(['enter',t,id,options]);oc.focus={t,id,...options};},feSid:()=>oc.focus?.placementId,
    feSelectTimber(id){calls.push(['select',id]);fe.sel={kind:'timber',id};},fiShowTab(tab){calls.push(['tab',tab]);},GridEditor:{open:id=>calls.push(['grid',id])},openPanel(){},toast(){}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../geometry-web/engineering-adapter.js'),'utf8'),sandbox);
  return {sandbox,calls,data,context,state,history,oc,fe,navigate:sandbox.window.EngineeringAdapter.navigateObject};
}
function guidePreparationHarness(waitFor='snap') {
  const state={contextToken:'original-frame',revision:0,nativeRevision:1,session:'original-service',undo:'u1',redo:null,blocked:false},calls=[],commits=[];
  let release,arrived;const reached=new Promise(resolve=>arrived=resolve),gate=new Promise(resolve=>release=resolve);
  const sandbox={oc:{edit:{bid:1},focus:{t:'face',id:1}},fe:{zoom:1,guides:[{id:7,source:'local',expression:'spec:authored'}]},
    ReferenceWorkspace:{getEvidenceState:()=>({...state})},feSid:()=>10,toast(){},
    api:async command=>{calls.push(command);if(command.startsWith(waitFor)){arrived();await gate;}return command==='newid'?{ok:true,guide:0}:{ok:true,expression:'spec:authored'};},
    emitLine:async command=>{commits.push(command);return true;}};
  const source=fs.readFileSync(process.env.GEOMETRY_REFERENCE_UI_JS||require.resolve('../geometry-web/reference-ui.js'),'utf8');
  const ownerStart=source.indexOf('function referenceGuidePreparation('),start=ownerStart<0?source.indexOf('async function createReferenceGuide('):ownerStart;
  vm.runInNewContext(source.slice(start,source.indexOf('/* D6c:',start)),sandbox);
  return {sandbox,state,calls,commits,reached,release};
}
test('native typed location preserves the second placement of a shared boundary and ID0',()=>{
  for(const [pid,tid] of [[20,7],[0,0]]){
    const g=S.index(locationData(pid,tid));
    assert.deepEqual(S.resolveLocation(g,{kind:'timber',id:tid}),{placementId:pid,boundaryId:1});
    assert.deepEqual(S.resolveLocation(g,{kind:'placement',id:pid}),{placementId:pid,boundaryId:1});
  }
});
test('missing, inactive, ambiguous or mistyped native relations never guess a placement',()=>{
  for(const mutate of [d=>d.edges=[],d=>d.edges[0].active=false,d=>d.nodes=d.nodes.filter(n=>n.kind!=='placement'||n.id!=='20'),
    d=>d.edges.push({...d.edges[0],to:'placement:10'}),d=>d.nodes.find(n=>n.key==='placement:20').kind='boundary',
    d=>d.nodes.find(n=>n.key==='placement:20').id='020',d=>d.nodes=d.nodes.filter(n=>n.kind!=='boundary')]){
    const d=locationData();mutate(d);assert.throws(()=>S.resolveLocation(S.index(d),{kind:'timber',id:7}),/來源/);
  }
  for(const id of [-1,4294967296,NaN,'7'])assert.throws(()=>S.resolveLocation(S.index(locationData()),{kind:'timber',id}),/不完整/);
});
test('shared navigation uses explicit placement from canvas and an already open different placement',async()=>{
  for(const open of [false,true])for(const [pid,tid] of [[20,7],[0,0]]){
    const h=navigationHarness(locationData(pid,tid));if(!open)h.oc.focus=null;
    await h.navigate({kind:'timber',id:tid},{sourceGraph:S.index(h.data)});
    assert.equal(h.oc.focus.id,1);assert.equal(h.oc.focus.placementId,pid);assert.equal(h.fe.sel.id,tid);
    assert.equal(h.state.revision,0);assert.equal(h.calls.filter(c=>Array.isArray(c)&&c[0]==='select').length,1);
    assert.ok(h.calls.filter(c=>typeof c==='string').every(c=>['source-inspect','boundary 1','resetFocus','setView3','renderObjects'].includes(c)));
  }
  const h=navigationHarness(locationData(0,0));h.data.edges=h.data.edges.filter(e=>e.field!=='boundary');
  const read=h.sandbox.apiRequest;h.sandbox.apiRequest=text=>text==='surfaces'?Promise.resolve({ok:true,surfaces:[{id:0,boundary:0}]}):read(text);
  h.sandbox.ocFind=(kind,id)=>kind==='placement'&&id===0;h.sandbox.selectObject=(kind,id)=>h.oc.sel={kind,id};h.sandbox.centerOnNode=()=>{};
  await h.navigate({kind:'placement',id:0});assert.equal(h.oc.sel.kind,'placement');assert.equal(h.oc.sel.id,0);assert.equal(h.oc.focus,null);
  const broken=navigationHarness();broken.data.edges=broken.data.edges.filter(e=>e.field!=='boundary');
  const brokenRead=broken.sandbox.apiRequest;broken.sandbox.apiRequest=text=>text==='surfaces'?Promise.resolve({ok:true,surfaces:[{id:20,boundary:1}]}):brokenRead(text);
  await assert.rejects(broken.navigate({kind:'placement',id:20}),/放置關係缺失/);
});
test('shared navigation refuses stale/reused ID pins and missing target before changing focus',async()=>{
  for(const mutate of [d=>d.revision++,d=>d.sourceFingerprint=hash(8),d=>d.nodes=d.nodes.filter(n=>n.kind!=='timber')]){
    const h=navigationHarness(),pin=S.index(structuredClone(h.data)),focus=h.oc.focus;mutate(h.data);
    await assert.rejects(h.navigate({kind:'timber',id:7},{sourceGraph:pin}),/來源/);
    assert.equal(h.oc.focus,focus);assert.ok(!h.calls.includes('resetFocus'));
  }
});
test('pending navigation stops on cancellation, project/history/page context or user focus changes',async()=>{
  for(const change of [h=>h.state.contextToken='other',h=>h.state.revision++,h=>h.history.frame={},
    h=>h.context.groups.get(1).activePageId='page-b',h=>h.oc.focus={t:'face',id:9},h=>h.fe.sel={kind:'timber',id:8},h=>h.current=false]){
    const h=navigationHarness();h.current=true;const read=h.sandbox.apiRequest;
    h.sandbox.apiRequest=async text=>{const result=await read(text);change(h);return result;};
    await h.navigate({kind:'timber',id:7},{isCurrent:()=>h.current});
    assert.ok(!h.calls.includes('resetFocus'));assert.ok(!h.calls.some(c=>Array.isArray(c)&&c[0]==='select'));
  }
});
test('draft cancellation leaves the current workspace intact and source changes during focus load cannot select a reused ID',async()=>{
  const h=navigationHarness(),focus=h.oc.focus;h.sandbox.window.DraftGate.ask=()=>false;
  await h.navigate({kind:'timber',id:7});assert.equal(h.oc.focus,focus);assert.ok(!h.calls.includes('resetFocus'));
  const late=navigationHarness(),enter=late.sandbox.enterFocus;
  late.sandbox.enterFocus=async(...args)=>{await enter(...args);late.data.revision++;late.data.sourceFingerprint=hash(8);};
  await assert.rejects(late.navigate({kind:'timber',id:7}),/來源已變更/);assert.equal(late.fe.sel,null);
  // The same ephemeral source-owner premise also guards read-only guide
  // preparation before it can submit a native mutation. These are dispatch
  // checks; the formal browser separately proves actual native acceptance.
  for(const stage of ['snap','newid'])for(const expired of ['focus','same-ID context','history','session']){
    const g=guidePreparationHarness(stage),pending=g.sandbox.createReferenceGuide(10,'u',1500);await g.reached;
    if(expired==='focus')g.sandbox.oc.focus=null;
    if(expired==='same-ID context'){g.sandbox.oc.edit={bid:1};g.state.contextToken='replacement-frame';}
    if(expired==='history'){g.state.undo='different-undo';g.state.nativeRevision++;}
    if(expired==='session')g.state.session='replacement-service';
    g.release();assert.equal(await pending,false,stage+': '+expired);assert.deepEqual(g.commits,[]);
  }
  for(const datum of [false,true]){
    const g=guidePreparationHarness(),pending=g.sandbox.moveReferenceGuide(7,'u',1500);await g.reached;
    g.sandbox.fe.guides=[{id:7,source:datum?'datum':'local',expression:'spec:replacement'}];g.release();
    assert.equal(await pending,false);assert.deepEqual(g.commits,[],'a reused guide ID never authorizes the former source');
  }
  for(const kind of ['create','move']){
    const g=guidePreparationHarness(),pending=kind==='create'?g.sandbox.createReferenceGuide(10,'u',1500):g.sandbox.moveReferenceGuide(7,'u',1500);
    await g.reached;g.release();assert.equal(await pending,true);
    assert.deepEqual(g.commits,[kind==='create'?'guide 0 10 u spec:authored':'move 7 spec:authored'],'current ownership preserves native expressions and ID0');
  }
  const rejected=guidePreparationHarness('never');rejected.sandbox.api=async command=>command==='newid'?{ok:false,error:'authored ID rejection'}:{ok:true,expression:'spec:authored'};
  assert.equal(await rejected.sandbox.createReferenceGuide(10,'u',1500),false);assert.deepEqual(rejected.commits,[]);
});
test('the navigation owner can cancel during render or the final native read before enter/select',async()=>{
  for(const stage of ['render','final']){
    const h=navigationHarness();let current=true,reads=0;const read=h.sandbox.apiRequest;
    h.sandbox.apiRequest=async text=>{const r=await read(text);if(text==='source-inspect'&&++reads===3&&stage==='final')current=false;return r;};
    if(stage==='render')h.sandbox.renderObjects=async()=>{current=false;};
    await h.navigate({kind:'timber',id:7},{isCurrent:()=>current});
    assert.equal(h.fe.sel,null);assert.ok(!h.calls.some(c=>Array.isArray(c)&&c[0]==='select'));
    if(stage==='render')assert.ok(!h.calls.some(c=>Array.isArray(c)&&c[0]==='enter'));
  }
});
test('source app forwards native face targets to the common navigation entry and its cancellation guard',async()=>{
  const calls=[],current=()=>true,g=S.index(locationData()),context={groups:new Map([[1,{activePageId:'a'}]])};let options;
  const sandbox={window:{addEventListener(){},SourceInspector:{...S,mount:(host,value)=>{options=value;return {detail:{isConnected:true},cancel(){}};}}},EngineeringAdapter:{navigateObject:(...args)=>calls.push(args)},ReferenceWorkspace:{context:()=>context},
    oc:{selection:[],sel:null,edit:null},fe:{timberSelection:new Set()},document:{getElementById:()=>null},queueMicrotask(){},MutationObserver:function(){}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../geometry-web/source-inspector-app.js'),'utf8'),sandbox);
  for(const kind of ['timber','guide','grid','placement'])await sandbox.window.SourceInspectorApp.navigate({kind,id:'7'},g,{isCurrent:current});
  assert.equal(calls.length,4);for(const [target,options] of calls){assert.equal(target.id,7);assert.equal(options.sourceGraph,g);assert.equal(options.isCurrent,current);}
  sandbox.oc.sel={kind:'boundary',id:1};sandbox.oc.selection=[sandbox.oc.sel];sandbox.ocFind=()=>({id:1});sandbox.document.getElementById=id=>id==='inspectorContent'?{}:null;
  sandbox.window.SourceInspectorApp.sync();const pin=options.stamp();context.groups.get(1).activePageId='b';
  assert.notEqual(options.stamp(),pin,'page context invalidates the initial source read before navigation owns it');
});
const node=(key,n=1)=>({key,definitionFingerprint:hash(n),valueFingerprint:hash(n),label:key});
const edge=(from,to,relation='dimension',field='A',active=true)=>({from,to,relation,field,active});
const graph=(nodes,edges=[],revision=1,complete=true)=>S.index({ok:true,schema:'source-inspector/1',nodes,edges,revision,complete});
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {resolve,promise};};
test('zero field differs from card, namespaces and versions remain distinct',()=>{
  assert.equal(S.key('parameter',0),'parameter:0');assert.equal(S.key('parameter-field',0,0,0),'parameter-field:0:f0');
  assert.notEqual(S.key('material','a',1),S.key('material','a',2));assert.notEqual(S.key('timber',0),S.key('guide',0));
});
test('nearby is bounded with explicit truncation, cycles and missing sources',()=>{
  const nodes=Array.from({length:80},(_,i)=>node('n'+i));const edges=nodes.slice(1).map(n=>edge('n0',n.key));edges.push(edge('n1','n0'),edge('n2','missing'));
  const g=graph(nodes,edges);assert.equal(S.nearby(g,'n0').rows.length,48);assert.equal(S.nearby(g,'n0').truncated,true);
  assert.equal(S.nearby(g,'n2').missing,true);assert.equal(S.nearby(g,'n0',{depth:0}).truncated,true);
  assert.equal(S.nearby(g,'n1',{direction:'uses'}).rows[0].key,'n0');
});
test('parameter card impact follows owned field zero without textual matches',()=>{
  const g=graph([{...node('parameter:0'),kind:'parameter'},node('parameter-field:0:f0'),node('guide:0'),node('parameter:10')],[edge('parameter:0','parameter-field:0:f0','member','field'),edge('guide:0','parameter-field:0:f0')]);
  assert.deepEqual(S.nearby(g,'parameter:0',{direction:'uses'}).rows.map(r=>r.key),['guide:0']);
});
test('only actual closure changes matter; presentation and unrelated nodes do not stale',()=>{
  const a=graph([node('p'),node('x'),node('unrelated')],[edge('p','x')]),b=graph([{...node('p'),label:'renamed'},node('x'),node('unrelated',2)],[edge('p','x')],99);
  assert.equal(S.freshness(a,b,['p']).contentStatus,'consistent');assert.equal(S.freshness(a,b,['p']).status,'unknown');
  const changed=graph([node('p'),node('x',2),node('unrelated')],[edge('p','x')]);assert.equal(S.freshness(a,changed,['p']).status,'changed');
});
test('possible span candidates and RC container membership are not fabricated evaluation dependencies',()=>{
  const column={...node('column:1'),kind:'column'},space={...node('space:1'),kind:'space'};
  const edges=[edge('timber:0','timber:1','span-candidate'),edge(column.key,space.key,'member'),edge(space.key,'boundary:2','member')];
  const before=graph([node('timber:0'),node('timber:1'),column,space,node('boundary:2')],edges);
  const now=graph([node('timber:0'),node('timber:1',2),column,space,node('boundary:2',2)],edges);
  assert.equal(S.freshness(before,now,['timber:0',column.key]).contentStatus,'consistent');
  assert.equal(S.nearby(before,'timber:0').rows[0].edge.relation,'span-candidate');
  assert.equal(S.freshness(before,graph([node('timber:0',2),node('timber:1',2),column,space,node('boundary:2',2)],edges),['timber:0']).status,'changed');
});
test('same effective value with different typed source and fixed versions is detected',()=>{
  const n=node('p'),x=node('material:a:v1'),y=node('material:a:v2');const a=graph([n,x,y],[edge('p',x.key)]),b=graph([n,x,y],[edge('p',y.key)]);
  assert.equal(S.freshness(a,b,['p']).changes[0].kind,'source-definition');
  assert.equal(S.freshness(a,graph([n,x,y],[edge('p',x.key),edge('p','ghost','dimension','ignored',false)]),['p']).contentStatus,'consistent');
});
test('missing, incomplete, reused identity and unsupported old model stay explicit',()=>{
  const a=graph([node('p'),node('x')],[edge('p','x')]);assert.equal(S.freshness(a,graph([node('p')]),['p']).status,'missing');
  assert.equal(S.freshness(a,a,['p'],{deleted:new Set(['x'])}).status,'unknown');
  assert.equal(S.freshness(a,graph([node('p'),node('x')],[edge('p','x')],1,false),['p']).contentStatus,'unchecked');
  assert.equal(S.freshness(a,a,[]).status,'unknown');assert.deepEqual(S.modelRoots({source:{kind:'example'}}),[]);
  assert.deepEqual(S.modelRoots({source:{kind:'scene'},input:{mode:'plan',base_scene:'',placement_id:0,obstacles:[],timbers:[{kind:'timber',id:0}]}}),['placement:0','timber:0']);
});
test('late async project switch, source revision change and cancellation never return stale result',async()=>{
  let ctx={},frame=1,revision=1,gate=deferred();const data=()=>graph([node('p')],[],revision).data;
  const session=S.createSession({context:()=>ctx,stamp:()=>frame,read:async()=>data(),readSnapshot:()=>gate.promise});
  let pending=session.inspect({input:{base_scene:''}});await new Promise(r=>setImmediate(r));ctx={};gate.resolve(data());assert.equal(await pending,null);
  gate=deferred();pending=session.inspect({input:{base_scene:''}});await new Promise(r=>setImmediate(r));revision=2;gate.resolve(data());await assert.rejects(pending,/來源已更新/);
  gate=deferred();pending=session.inspect({input:{base_scene:''}});await new Promise(r=>setImmediate(r));session.cancel();gate.resolve(data());assert.equal(await pending,null);
  gate=deferred();pending=session.inspect({input:{base_scene:''}});await new Promise(r=>setImmediate(r));frame++;gate.resolve(data());assert.equal(await pending,null);
});
test('invalid native response or duplicate source identities cannot yield green state',()=>{
  assert.throws(()=>S.index({ok:false}));assert.throws(()=>graph([node('p'),node('p')]));assert.throws(()=>graph([{...node('p'),valueFingerprint:'guessed'}]));
});

const typed=(kind,id,version=0,fieldId=0)=>({...node(S.key(kind,id,version,fieldId)),kind,id:String(id),version,fieldId});
const supportEnd=(source,face,at,owner=null)=>({status:'exact',at,crossRange:[400,427],relation:{kind:'timber-face',source:{kind:'timber',id:source},localFace:face,normalWorld:[0,at===20?1:-1,0],owner,surface:0,stop:{axis:'v',at,range:[0,4000],fixity:'fixed'}}});
function supportData(owned=false){
  const owner=memberId=>({instanceId:1,memberId,bindingId:2,ruleId:3,ruleVersion:2,ruleFingerprint:hash(4),bindingFingerprint:hash(5),instanceFingerprint:hash(6)});
  const timbers=[7,0,91].map((id,i)=>({...typed('timber',id),placed:true,surface:0,lengthAxis:id===7?'v':'u',nativeOwner:owned?owner(i===0?3:i):null}));
  const nodes=[typed('placement',0),...timbers],edges=timbers.map(n=>edge(n.key,'placement:0','position','surface'));
  if(owned){nodes.push(typed('assembly-instance',1),typed('assembly-binding',2),{...typed('assembly-rule',3,2),definitionFingerprint:hash(4)},...['1','2','3'].map(m=>typed('assembly-member',3,2,Number(m))));
    edges.push(edge('assembly-instance:1','assembly-binding:2','dimension','binding'),edge('assembly-instance:1','assembly-rule:3:v2','rule-version',hash(4)),edge('assembly-binding:2','assembly-rule:3:v2','rule-version','rule'));
    for(const n of timbers){edges.push(edge(n.key,'assembly-instance:1','member','member:'+n.nativeOwner.memberId));}
    for(const m of [1,2,3])edges.push(edge('assembly-rule:3:v2','assembly-member:3:v2:f'+m,'member','members'));
  }
  return {ok:true,schema:'source-inspector/1',revision:1,complete:true,identityContinuity:'unknown',supportStatus:'unknown',sourceFingerprint:hash(9),nodes,edges,
    timberSupports:{schema:'native-timber-supports/1',sourceFingerprint:hash(9),entries:[{id:7,surface:0,owner:owned?owner(3):null,start:supportEnd(0,'B1',20,owned?owner(1):null),finish:supportEnd(91,'B0',2980,owned?owner(2):null)}]}};
}
test('native exact supports produce typed endpoint edges including ID0 without changing raw data or claiming complete identity',()=>{
  const data=supportData(),before=JSON.stringify(data),g=S.index(data),edges=g.out.get('timber:7').filter(e=>e.relation==='confirmed-support');
  assert.deepEqual(edges.map(e=>[e.to,e.field,e.provenance.relation.localFace]),[['timber:0','start','B1'],['timber:91','finish','B0']]);
  assert.equal(g.data.identityContinuity,'unknown');assert.equal(g.data.supportStatus,'unknown');assert.equal(JSON.stringify(data),before);
  edges[0].provenance.relation.source.id=99;assert.equal(data.timberSupports.entries[0].start.relation.source.id,0);
});
test('all eight row and support owner fields are independently validated without comparing unrelated custom node hashes',()=>{
  const data=supportData(true),g=S.index(data);assert.equal(g.supportEntries.get('timber:7').start.relation.owner.memberId,1);
  assert.notEqual(g.nodes.get('assembly-binding:2').definitionFingerprint,data.timberSupports.entries[0].owner.bindingFingerprint);
  for(const target of ['row','support'])for(const field of ['instanceId','memberId','bindingId','ruleId','ruleVersion','ruleFingerprint','instanceFingerprint','bindingFingerprint']){
    const bad=structuredClone(data),o=target==='row'?bad.timberSupports.entries[0].owner:bad.timberSupports.entries[0].start.relation.owner;
    o[field]=typeof o[field]==='number'?99:hash(99);assert.throws(()=>S.index(bad),/來源|核對/);
  }
  const bad=structuredClone(data);bad.edges=bad.edges.filter(e=>e.from!=='timber:0'||e.relation!=='member');assert.throws(()=>S.index(bad),/成員/);
});
test('projection corruption never becomes confirmed support or silently replaces native source facts',()=>{
  const mutations=[d=>d.timberSupports.sourceFingerprint=hash(8),d=>d.timberSupports.schema='other',d=>d.timberSupports.entries.push(structuredClone(d.timberSupports.entries[0])),
    d=>d.timberSupports.entries[0].id=null,d=>d.timberSupports.entries[0].surface=1,d=>d.nodes.find(n=>n.key==='timber:7').placed=false,
    d=>d.nodes=d.nodes.filter(n=>n.key!=='timber:0'),d=>d.nodes.find(n=>n.key==='timber:0').surface=1,d=>d.nodes.find(n=>n.key==='timber:0').placed=false,
    d=>d.nodes.find(n=>n.key==='timber:0').id='91',d=>d.timberSupports.entries[0].start.relation.source.id=7,
    d=>d.timberSupports.entries[0].start.relation.localFace='min_v',d=>d.timberSupports.entries[0].start.relation.normalWorld=[0,0,0],
    d=>d.timberSupports.entries[0].start.relation.stop.range=[0,420],d=>d.timberSupports.entries[0].start.relation.stop.axis='u',d=>d.timberSupports.entries[0].start.relation.owner={}];
  for(const mutate of mutations){const bad=supportData();mutate(bad);assert.throws(()=>S.index(bad),/來源|核對|版本|無效|重複/);}
  const bad=supportData();bad.edges.push(edge('timber:7','timber:0','confirmed-support','start'));assert.throws(()=>S.index(bad),/型別/);
});
test('embedded placement, real boundary and hole0 preserve their typed native source',()=>{
  const data=supportData(),e=data.timberSupports.entries[0],r={kind:'outline-edge',source:{kind:'placement',id:0},edgeIndex:0,holeIndex:null,localFace:null,normalWorld:null,owner:null,surface:0,stop:{axis:'v',at:20,range:[0,4000],fixity:'fixed'}};
  e.start.relation=r;assert.equal(S.index(data).supportEntries.get('timber:7').start.relation.source.id,0);
  data.nodes.push(typed('boundary',1));data.edges.push(edge('placement:0','boundary:1','position','boundary'));
  e.start.relation={...r,kind:'hole-edge',source:{kind:'boundary',id:1},holeIndex:0};assert.equal(S.index(data).supportEntries.get('timber:7').start.relation.holeIndex,0);
  e.start.relation.source.id=0;assert.throws(()=>S.index(data),/來源/);
});
test('unknown, missing capability, missing entry and truncated native facts stay unknown rather than upgrading candidates',()=>{
  const data=supportData();data.edges.push(edge('timber:7','timber:0','span-candidate','I9 candidate, not confirmed support'));
  data.timberSupports.entries[0].start={status:'unknown',relation:{source:{id:99}}};
  let g=S.index(data);assert.deepEqual(g.supportEntries.get('timber:7').start,{status:'unknown',relation:null});assert.equal(g.out.get('timber:7').filter(e=>e.relation==='confirmed-support').length,1);
  data.timberSupports.entries=[];g=S.index(data);assert.equal(g.supportEntries.size,0);
  delete data.timberSupports;assert.equal(S.index(data).hasSupportProjection,false);
  const partial=supportData();partial.complete=false;partial.nodes=partial.nodes.filter(n=>n.key!=='timber:0');g=S.index(partial);
  assert.equal(g.supportEntries.get('timber:7').start.status,'unknown');assert.equal(S.nearby(g,'timber:7').truncated,true);
});
test('equal timber geometry with changed exact support source, local face or fixed owner marks source-definition without arbitrary dependency expansion',()=>{
  for(const mutate of [d=>{d.timberSupports.entries[0].start.relation.source.id=91;d.timberSupports.entries[0].start.relation.owner=structuredClone(d.nodes.find(n=>n.key==='timber:91').nativeOwner);},d=>d.timberSupports.entries[0].start.relation.localFace='B0',
    d=>{for(const n of d.nodes)if(n.nativeOwner?.memberId===1)n.nativeOwner.bindingFingerprint=hash(8);d.timberSupports.entries[0].start.relation.owner.bindingFingerprint=hash(8);}]){
    const before=supportData(true),now=structuredClone(before);mutate(now);
    const result=S.freshness(S.index(before),S.index(now),['timber:7']);assert.equal(result.status,'changed');assert.deepEqual(result.changes,[{key:'timber:7',kind:'source-definition'}]);
  }
  const before=supportData(),now=structuredClone(before);now.sourceFingerprint=now.timberSupports.sourceFingerprint=hash(10);now.nodes.find(n=>n.key==='timber:0').valueFingerprint=hash(12);
  assert.equal(S.freshness(S.index(before),S.index(now),['timber:7']).contentStatus,'consistent');
  now.timberSupports.entries[0].finish={status:'unknown',relation:null};assert.equal(S.freshness(S.index(before),S.index(now),['timber:7']).contentStatus,'unchecked');
});
test('stale path expansion cannot repaint an old snapshot in the actual mount adapter',async()=>{
  let stamp=1;const ctx={},handlers={},body={innerHTML:'',textContent:'',isConnected:true,addEventListener:(name,fn)=>handlers[name]=fn,removeEventListener(){}};
  const detail={open:false,isConnected:true,dataset:{},classList:{add(){}},querySelector:()=>body,addEventListener:(name,fn)=>handlers[name]=fn,removeEventListener(){},remove(){}};
  const host={querySelector:()=>null,ownerDocument:{createElement:()=>detail},append(){}};
  const data=graph([node('p'),node('x')],[edge('p','x')]).data;
  S.mount(host,{selection:'p',context:()=>ctx,stamp:()=>stamp,read:async()=>data,readSnapshot:async()=>data,navigate:async()=>{}});
  detail.open=true;handlers.toggle();await new Promise(r=>setImmediate(r));assert.match(body.innerHTML,/原生來源指紋/);
  stamp++;await handlers.click({target:{closest:selector=>selector==='[data-source-path]'?{dataset:{sourcePath:'x'}}:null}});
  assert.match(body.innerHTML,/來源已變更，請重新檢查/);assert.doesNotMatch(body.innerHTML,/原生來源指紋/);
});
test('a canonical source change cannot pass a stable native revision or late context boundary',async()=>{
  let ctx={},stamp=1,reads=0;const old=supportData(),fresh=structuredClone(old);fresh.sourceFingerprint=fresh.timberSupports.sourceFingerprint=hash(10);
  const session=S.createSession({context:()=>ctx,stamp:()=>stamp,read:async()=>++reads===1?old:fresh,readSnapshot:async()=>old});
  await assert.rejects(session.inspect(),/來源已更新/);
  const gate=deferred(),delayed=S.createSession({context:()=>ctx,stamp:()=>stamp,read:()=>gate.promise,readSnapshot:async()=>old});
  const pending=delayed.inspect();ctx={};stamp++;gate.resolve(old);assert.equal(await pending,null);
});
