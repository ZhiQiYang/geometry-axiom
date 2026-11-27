/* Actual native fixtures; mocked DOM/async delivery tests do not claim browser coverage. */
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const S=require(process.env.GEOMETRY_SOURCE_INSPECTOR_JS||'../geometry-web/source-inspector.js');
const P=require('../geometry-web/project-store.js');
const T=require('../geometry-web/timber-supports.js')(require('../geometry-web/timber-schedule.js'));
const fixtures=require('./fixtures/model_snapshot_schedule.json'),clone=x=>JSON.parse(JSON.stringify(x));
const sample=()=>clone(fixtures.ordinary[0]),tick=()=>new Promise(r=>setImmediate(r));
const graph=data=>S.index(data),live=e=>{const g=clone(e.snapshot);g.live=true;delete g.timberReferences;return g;};
const result=(e,current=live(e))=>({baseline:graph(e.snapshot),packageBaseline:graph(e.packageSnapshot),packageSourceSha:e.record.result.source_sha256,graph:graph(current),context:{id:'snapshot-project'}});
const derive=(e,current)=>S.deriveModelSchedule(e.record,result(e,current),T,P);
const gate=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
const until=async predicate=>{for(let n=0;n<200&&!predicate();n++)await new Promise(r=>setTimeout(r,1));assert.ok(predicate(),'asynchronous native snapshot cycle must finish');};

// Real bridge reads and ordinary-plan producer output. See the delivery's
// reproduce.py/extend_fixture.py and raw logs; no synthetic positive receipt.
const sourceFixtures=require('./fixtures/r05_source_checks.json');
const sourceSample=()=>clone(sourceFixtures.single);
const checks=(e,current=e.live)=>{
  const schedule=derive(e,current);
  assert.ok(schedule.sourceChecks,'R05_F4B_SOURCE_CHECKS_PRESENT');
  return schedule.sourceChecks;
};
const localStatuses=row=>row.localIncarnationComparison.map(x=>[x.kind,x.id,x.status]);

test('R05_F4B_NATIVE_DIAGNOSTIC_ROWS: native two-root checks are readonly, not physical identity',()=>{
  const e=sourceSample(),before=JSON.stringify(e),s=derive(e,e.live),c=checks(e);
  assert.equal(c.purpose,'source-diagnostics','R05_F4B_DIAGNOSTIC_ONLY');
  assert.equal(c.scopeProof,'unverified','R05_F4B_SCOPE_NOT_INVENTED');
  assert.equal(c.physicalSameness,'unverified','R05_F4B_NO_PHYSICAL_IDENTITY');
  assert.equal(c.rows.length,1,'R05_F4B_ONE_CHECK_PER_ROW');
  const r=c.rows[0];assert.deepEqual(r.timberRoot,{kind:'timber',id:0});
  assert.deepEqual(r.placementRoot,{kind:'placement',id:0});
  assert.deepEqual(localStatuses(r),[['timber',0,'same-mark'],['placement',0,'same-mark']],'R05_F4B_LOCAL_TWO_ROOTS');
  assert.equal(r.definition,'consistent','R05_F4B_ROOT_DEFINITION');
  assert.equal(r.effectiveValues,'consistent','R05_F4B_ROOT_VALUE');
  assert.equal(r.exactSupport,'consistent','R05_F4B_EXACT_SUPPORT');
  assert.equal(r.sourceContent.contentStatus,'consistent','R05_F4B_SOURCE_CLOSURE');
  assert.equal(JSON.stringify(e),before,'R05_F4B_READONLY');
  const plain=clone(s);delete plain.sourceChecks;
  assert.equal(S.modelScheduleCSV(s,T),S.modelScheduleCSV(plain,T),'R05_F4B_CSV_BYTES_UNCHANGED');
});
test('R05_F4B_EQUAL_DISTINCT_ROOTS: two ordinary timbers stay two diagnostics and two rows',()=>{
  const e=clone(sourceFixtures.independent),s=derive(e,e.live),c=checks(e);
  assert.deepEqual(s.rows.map(r=>[r.id,r.A,r.B,r.L]),[[0,27,33,4000],[4,27,33,4000]]);
  assert.deepEqual(c.rows.map(r=>r.timberRoot.id),[0,4],'R05_F4B_NO_DIMENSION_DEDUP');
  assert.notEqual(c.rows[0].localIncarnationComparison[0].saved,c.rows[1].localIncarnationComparison[0].saved);
  assert.equal(c.rows[1].localIncarnationComparison[1].status,'same-mark');
});
test('R05_F4B_OLD_MODEL_UNKNOWN: no retroactive pins and historical CSV remains usable',()=>{
  const e=sample(),s=derive(e),c=checks(e,live(e));
  assert.equal(s.rows.length,1);assert.equal(s.identityContinuity,'unknown');
  assert.deepEqual(localStatuses(c.rows[0]),[['timber',0,'unknown'],['placement',0,'unknown']],'R05_F4B_NO_BACKFILLED_PIN');
  assert.equal(c.rows[0].definition,'consistent');assert.ok(S.modelScheduleCSV(s,T).includes('"4000"'));
});
test('R05_F4B_LOCAL_IDENTITY: activation, placement and same-id recreation are separate checks',()=>{
  const e=sourceSample(),off=clone(e.live);off.identityLedger.active=false;
  assert.deepEqual(localStatuses(checks(e,off).rows[0]),[['timber',0,'inactive'],['placement',0,'inactive']],'R05_F4B_ACTIVE_LEDGER_REQUIRED');
  const moved=clone(e.live);moved.nodes.find(n=>n.key==='placement:0').incarnation='f'.repeat(32)+':1';
  assert.deepEqual(localStatuses(checks(e,moved).rows[0]),[['timber',0,'same-mark'],['placement',0,'replaced']],'R05_F4B_PLACEMENT_PIN_REQUIRED');
  const recreated=checks(e,sourceFixtures.recreated.live).rows[0];
  assert.equal(recreated.localIncarnationComparison[0].status,'replaced','R05_F4B_RECREATE_NOT_CONTINUOUS');
  assert.equal(recreated.definition,'consistent');assert.equal(recreated.effectiveValues,'consistent');
});
test('R05_F4B_SEPARATE_AXES: real same-value source change cannot pass definition checks',()=>{
  const e=sourceSample(),r=checks(e,sourceFixtures.sameValueDifferentSource.live).rows[0];
  assert.equal(r.localIncarnationComparison[0].status,'same-mark');
  assert.equal(r.definition,'changed','R05_F4B_DEFINITION_NOT_VALUE');
  assert.equal(r.effectiveValues,'consistent','R05_F4B_VALUE_INDEPENDENT');
  assert.equal(r.sourceContent.contentStatus,'changed','R05_F4B_CLOSURE_CHANGE');
  const changed=clone(e.live);changed.nodes.find(n=>n.key==='timber:0').valueFingerprint='a'.repeat(64);
  const valueOnly=checks(e,changed).rows[0];assert.equal(valueOnly.definition,'consistent');
  assert.equal(valueOnly.effectiveValues,'changed','R05_F4B_VALUE_NOT_DEFINITION');
});
test('R05_F4B_TYPED_SOURCE_CLOSURE: referenced closure is checked beyond the two roots',()=>{
  const e=sourceSample(),changed=clone(e.live);changed.nodes.find(n=>n.key==='boundary:1').definitionFingerprint='b'.repeat(64);
  const r=checks(e,changed).rows[0];assert.equal(r.definition,'consistent');assert.equal(r.effectiveValues,'consistent');
  assert.equal(r.sourceContent.contentStatus,'changed','R05_F4B_CLOSURE_NOT_ROOT_ONLY');
  const edges=clone(e.live);edges.edges.find(x=>x.from==='timber:0').field='altered-field';
  assert.equal(checks(e,edges).rows[0].sourceContent.contentStatus,'changed','R05_F4B_TYPED_EDGE_CHECKED');
});
test('R05_F4B_SUPPORT_AXIS: exact native endpoint changes do not hide behind opaque pins',()=>{
  const e=sourceSample(),changed=clone(e.live);changed.timberSupports.entries[0].start.relation.edgeIndex=2;
  const r=checks(e,changed).rows[0];assert.equal(r.definition,'consistent');assert.equal(r.effectiveValues,'consistent');
  assert.equal(r.exactSupport,'changed','R05_F4B_SUPPORT_NOT_ROOT_HASH');
  const unknown=clone(e.live);unknown.timberSupports.entries[0].start={status:'unknown',relation:null};
  assert.equal(checks(e,unknown).rows[0].exactSupport,'unchecked','R05_F4B_UNKNOWN_SUPPORT_NOT_EQUAL');
  const reordered=clone(e.live);reordered.timberSupports.entries[0].start.relation.source={id:1,kind:'boundary'};
  assert.equal(checks(e,reordered).rows[0].exactSupport,'consistent','R05_F4B_SUPPORT_KEY_ORDER_IRRELEVANT');
});
test('R05_F4B_INCOMPLETE_READ: incomplete or missing facts never certify equal source',()=>{
  const e=sourceSample(),partial=clone(e.live);partial.complete=false;
  const r=checks(e,partial).rows[0];
  for(const field of ['definition','effectiveValues','exactSupport'])assert.equal(r[field],'unchecked','R05_F4B_COMPLETE_NATIVE_REQUIRED:'+field);
  const missing=clone(partial);missing.nodes=missing.nodes.filter(n=>n.key!=='timber:0');
  const m=checks(e,missing).rows[0];assert.equal(m.definition,'missing','R05_F4B_MISSING_ROOT');
  assert.equal(m.effectiveValues,'missing');assert.equal(m.localIncarnationComparison[0].status,'unknown','R05_F4B_PARTIAL_NOT_ABSENT');
  const completeMissing=clone(e.live);completeMissing.nodes=completeMissing.nodes.filter(n=>n.key!=='timber:0');
  completeMissing.timberSupports.entries=[];
  assert.equal(checks(e,completeMissing).rows[0].localIncarnationComparison[0].status,'absent','R05_F4B_ABSENT_REQUIRES_COMPLETE_READ');

  // 模擬兩端均為角材面的回覆形狀（不是新原生夾具）。先確認有根時一致，
  // 再只移除 live placement；兩端支承及其目標角材仍在。
  const faces=clone(sourceFixtures.independent);
  for(const entry of faces.snapshot.timberSupports.entries){
    for(const [end,face,normal] of [['start','START',1],['finish','END',-1]]){
      const {surface,stop}=entry[end].relation;
      entry[end].relation={kind:'timber-face',source:{kind:'timber',id:entry.id===0?4:0},
        localFace:face,normalWorld:[normal,0,0],owner:null,surface,stop};
    }
  }
  faces.snapshot.timberReferences.timberSupports=clone(faces.snapshot.timberSupports);
  const withoutPlacement=faces.live;
  withoutPlacement.timberSupports=clone(faces.snapshot.timberSupports);
  assert.equal(withoutPlacement.complete,true);
  assert.equal(checks(faces,withoutPlacement).rows[0].exactSupport,'consistent');
  withoutPlacement.nodes=withoutPlacement.nodes.filter(n=>n.key!=='placement:0');
  const row=checks(faces,withoutPlacement).rows[0];
  assert.equal(row.definition,'missing');
  assert.equal(row.exactSupport,'unchecked','R05_F4B_EXACT_SUPPORT_REQUIRES_PLACEMENT');
});
test('R05_F4B_NO_MERGE_AUTHORITY: repeated saved representations remain independent',()=>{
  const a=sourceSample(),b=clone(a);b.record.id='separate-saved-view';b.record.name='Another view';
  const x=derive(a,a.live),y=derive(b,b.live);checks(a);checks(b);
  assert.equal(x.rows.length+y.rows.length,2,'R05_F4B_REPRESENTATIONS_NOT_AUTO_MERGED');
  for(const s of [x,y]){assert.equal(s.sourceChecks.physicalSameness,'unverified');
    assert.equal(Object.hasOwn(s,'itemKey'),false);assert.equal(Object.hasOwn(s,'takeoffSet'),false);}
});

test('actual native saved models include only explicit roots, with zero and real placement identities',()=>{
  for(const e of fixtures.ordinary){const before=JSON.stringify(e),s=derive(e);assert.deepEqual(s.ids,e.record.input.timbers.map(t=>t.id));assert.equal(s.rows.length,1);assert.equal(s.rows[0].A,27);assert.equal(s.rows[0].B,33);assert.equal(s.rows[0].L,4000);assert.equal(s.rows[0].surface,e.record.input.placement_id);assert.equal(s.identityContinuity,'unknown');assert.equal(JSON.stringify(e),before);}
  assert.deepEqual(derive(fixtures.ordinary[0]).ids,[0]);assert.deepEqual(derive(fixtures.ordinary[2]).ids,[4]);
});
test('two real saved views are independent, never merged or deduplicated by model ID, name or native hash',()=>{
  const a=derive(fixtures.ordinary[0]),b=derive(fixtures.ordinary[1]);assert.notEqual(a.modelId,b.modelId);assert.equal(a.sourceFingerprint,b.sourceFingerprint);assert.deepEqual(a.ids,b.ids);assert.equal(a.rows.length,1);assert.equal(b.rows.length,1);assert.throws(()=>S.deriveModelSchedule(fixtures.ordinary.map(e=>e.record),result(sample()),T,P));
});
test('one genuinely produced model counts its two equal independent timbers exactly once each',()=>{
  const e=fixtures.twoRoot,s=derive(e);assert.deepEqual(s.ids,[0,4]);assert.equal(s.rows.length,2);assert.deepEqual(s.rows.map(r=>[r.A,r.B,r.L]),[[27,33,4000],[27,33,4000]]);assert.notDeepEqual(s.rows[0].origin,s.rows[1].origin);assert.equal(e.record.result.summary.timber_count,2);assert.equal(e.independentlyRebuiltPackages.length,4);
});
test('actual changed live dimensions leave saved sizes frozen and report changed content with unknown continuity',()=>{
  const e=sample(),s=derive(e,fixtures.changedLive);assert.equal(s.rows[0].A,27);assert.equal(s.rows[0].B,33);assert.equal(s.freshness.status,'changed');assert.equal(s.freshness.contentStatus,'changed');assert.equal(s.identityContinuity,'unknown');assert.notEqual(s.sourceFingerprint,s.liveSourceFingerprint);
  const missing=clone(fixtures.changedLive);missing.nodes=missing.nodes.filter(n=>n.key!=='timber:0');missing.timberSupports.entries=missing.timberSupports.entries.filter(t=>t.id!==0);const historical=derive(e,missing);assert.equal(historical.rows[0].A,27);assert.equal(historical.freshness.status,'missing');
});
test('real parameter field zero keeps typed dimension provenance and changed live field is detected',()=>{
  const e=fixtures.parameter,s=derive(e,e.live),row=s.rows[0];assert.equal(row.A,27);assert.equal(row.sources.find(s=>s.target.field==='A').source.parameterId,0);assert.equal(row.sources.find(s=>s.target.field==='A').source.fieldId,0);assert.equal(s.freshness.status,'changed');assert.ok(S.modelScheduleCSV(s,T).includes('""parameterId"":0'));assert.equal(e.independentlyRebuiltPackages.length,4);
});
test('comments, saved package SHA and canonical native SHA retain their distinct existing hash domains',async()=>{
  const e=fixtures.comment;assert.match(e.record.input.base_scene,/# retained note/);assert.notEqual(await P.sha(new TextEncoder().encode(e.record.input.base_scene)),e.snapshot.sourceFingerprint);assert.equal(await P.sha(new TextEncoder().encode(e.record.result.timbers.definitions.base_scene)),e.record.result.source_sha256);assert.notEqual(e.record.result.source_sha256,e.snapshot.sourceFingerprint);assert.equal(derive(e).rows.length,1);
});
test('each lawful actual package candidate shares its input native World, with same-domain saved source digest',async()=>{
  for(const e of [...fixtures.ordinary,fixtures.parameter,fixtures.comment,fixtures.twoRoot,fixtures.override]){assert.equal(await P.sha(new TextEncoder().encode(e.record.result.timbers.definitions.base_scene)),e.record.result.source_sha256);assert.equal(e.snapshot.sourceFingerprint,e.packageSnapshot.sourceFingerprint);assert.equal(e.packageSnapshot.live,false);}
});
test('real coherent wrong-carrier and same-carrier changed-dimensions candidates cannot adopt stale saved packages',()=>{
  for(const e of [fixtures.wrongCarrier,fixtures.wrongDimensions]){P.validateSpaceModel(e.record);assert.notEqual(e.snapshot.sourceFingerprint,e.packageSnapshot.sourceFingerprint);assert.throws(()=>derive(e),/套件定義/);}
  const e=sample(),r=result(e);delete r.packageBaseline;assert.throws(()=>S.deriveModelSchedule(e.record,r,T,P),/套件定義/);
});
test('legacy absent roots and explicit empty selections do not adopt other base-scene timbers',()=>{
  const e=sample();delete e.record.input.timbers;delete e.record.result.timbers;delete e.record.result.summary.timber_count;delete e.record.result.summary.timber_volume_mm3;e.record.result.schema='geometry-space-preview/1';assert.ok(e.snapshot.timberReferences.timbers.length>0);assert.deepEqual(derive(e).rows,[]);
  const empty=sample();empty.record.input.timbers=[];assert.deepEqual(S.modelTimberIds(empty.record),[]);assert.throws(()=>derive(empty),/角材|套件/);
});
test('malformed, duplicate and out-of-package roots are rejected without zero quantities or scope fallback',()=>{
  for(const mutate of [e=>e.record.input.timbers.push({kind:'timber',id:0}),e=>e.record.input.timbers[0].id='0',e=>e.record.input.timbers[0].id=-1,e=>e.record.input.timbers[0].id=4294967296,e=>e.record.input.timbers[0].kind='beam',e=>e.record.input.timbers[0].extra=true,e=>e.record.input.timbers[0].id=99,e=>e.record.input.timbers=null]){const e=sample();mutate(e);assert.throws(()=>derive(e));}
});
test('native snapshot envelope, source fingerprint, unique IDs and placed facts must agree',()=>{
  for(const mutate of [e=>e.snapshot.live=true,e=>delete e.snapshot.timberReferences,e=>e.snapshot.timberReferences.ok=false,e=>e.snapshot.timberReferences.sourceFingerprint='f'.repeat(64),e=>e.snapshot.timberReferences.timbers.push(clone(e.snapshot.timberReferences.timbers[0])),e=>e.snapshot.timberReferences.timbers=e.snapshot.timberReferences.timbers.filter(t=>t.id!==0),e=>e.snapshot.nodes.find(n=>n.key==='timber:0').placed=false,e=>e.snapshot.nodes.find(n=>n.key==='timber:0').surface=2,e=>e.snapshot.nodes.find(n=>n.key==='timber:0').lengthAxis='v']){const e=sample();mutate(e);assert.throws(()=>derive(e));}
  assert.throws(()=>S.deriveModelSchedule(sample().record,result(sample()),null,P),/能力/);assert.throws(()=>S.deriveModelSchedule(sample().record,result(sample()),T,null),/能力/);
});
test('invalid native dimensions, geometry axes or altered typed support metadata cannot make a ready schedule',()=>{
  for(const mutate of [g=>g.A=0,g=>g.B=null,g=>g.length=0,g=>g.dir='auto',g=>g.side=null,g=>g.axes[0]=[2,0,0],g=>g.axes[1]=g.axes[0],g=>g.origin=[0,0],g=>g.surface='0']){const e=sample();mutate(e.snapshot.timberReferences.timbers.find(t=>t.id===0).geometry);assert.throws(()=>derive(e));}
  const e=sample();e.snapshot.timberReferences.timberSupports.entries[0].start.relation.localFace='B0';assert.throws(()=>derive(e),/支撐/);
});
test('corrupt engineering parameter reference cannot replace the actual typed field-zero edge',()=>{
  const e=clone(fixtures.parameter);e.snapshot.timberReferences.engineeringSources[0].source.parameterId=99;assert.throws(()=>derive(e,e.live),/具型別/);
});
test('engineering effective value and duplicate target cannot disagree with real native dimensions',()=>{
  for(const mutate of [sources=>sources[0].effective=29,sources=>sources.push(clone(sources[0]))]){const e=clone(fixtures.parameter);mutate(e.snapshot.timberReferences.engineeringSources);assert.throws(()=>derive(e,e.live),/完成尺寸|重複/);}
});
test('omitted typed engineering provenance cannot silently become direct literal dimensions',()=>{
  const e=clone(fixtures.parameter);e.snapshot.timberReferences.engineeringSources=[];assert.throws(()=>derive(e,e.live),/完整提供/);
});
test('genuine literal override preserves inactive parameter lineage and rejects its omission',()=>{
  const e=clone(fixtures.override),row=derive(e).rows[0],source=row.sources.find(s=>s.target.field==='A');assert.equal(row.A,31);assert.equal(source.source.parameterId,0);assert.equal(source.override.kind,'literal');assert.equal(source.override.value,31);assert.ok(e.snapshot.edges.some(edge=>edge.from==='timber:0'&&edge.to===S.key('parameter-field',0,0,0)&&edge.field==='A'&&edge.active===false));assert.equal(e.independentlyRebuiltPackages.length,4);
  e.snapshot.timberReferences.engineeringSources=[];assert.throws(()=>derive(e),/完整提供/);
});
test('snapshot CSV extends actual schedule quoting and formula safety, names source/model/context/units and stays readonly',()=>{
  const e=sample();e.record.name='\t=HYPERLINK("not executed")\nsecond';const s=derive(e),before=JSON.stringify(s),csv=S.modelScheduleCSV(s,T,'length','cm');assert.ok(csv.startsWith('\ufeff'));assert.ok(csv.includes('snapshot_identity_continuity'));assert.ok(csv.includes('"saved-model-snapshot"'));assert.ok(csv.includes('"snapshot-project"'));assert.ok(csv.includes('"mm","cm"'));assert.ok(csv.includes('"unknown","consistent","unknown"'));assert.ok(csv.includes('"\'\t=HYPERLINK(""not executed"")\nsecond"'));assert.ok(csv.includes('"4000"'));assert.equal(JSON.stringify(s),before);assert.throws(()=>S.modelScheduleCSV(s,T,'template','mm'));assert.throws(()=>S.modelScheduleCSV(s,T,'id','m'));
});

function mounted(e=sample()){
  let html='',text='';const events={},body={get innerHTML(){return html;},set innerHTML(value){html=String(value);text=html.replace(/<[^>]*>/g,'');},get textContent(){return text;},set textContent(value){text=String(value);html=text;},isConnected:true,addEventListener:(name,fn)=>events[name]=fn,removeEventListener(){}};
  const detail={open:false,isConnected:true,dataset:{},classList:{add(){}},querySelector:()=>body,addEventListener:(name,fn)=>events[name]=fn,removeEventListener(){},remove(){}};
  const host={querySelector:()=>null,ownerDocument:{createElement:()=>detail},append(){}};
  const state={record:clone(e.record),context:{id:'snapshot-project'},stamp:1,active:true,exports:[],reads:0,snapshots:0,read:async()=>live(e),snapshot:async scene=>clone(scene===e.record.input.base_scene?e.snapshot:e.packageSnapshot)};
  const mount=S.mount(host,{selection:S.modelRoots(e.record)[0],record:e.record,context:()=>state.context,stamp:()=>state.stamp,read:async()=>{state.reads++;return state.read();},readSnapshot:async scene=>{state.snapshots++;return state.snapshot(scene);},navigate:async()=>{throw Error('snapshot quantities cannot locate live objects');},project:P,timberSchedule:T,getRecord:()=>state.record,isActive:()=>state.active,exportCSV:(csv,s)=>state.exports.push({csv,s})});
  const click=()=>events.click({target:{closest:selector=>selector==='[data-source-refresh]'?{}:null}});
  const open=async()=>{detail.open=true;events.toggle();await until(()=>body.innerHTML.includes('data-model-schedule'));};
  return {state,body,detail,events,mount,click,open};
}
test('actual mount displays snapshot on expansion, replaces only refresh, then rechecks and exports the displayed version',async()=>{
  const m=mounted();await m.open();assert.equal(m.state.exports.length,0);assert.equal((m.body.innerHTML.match(/data-source-refresh/g)||[]).length,1);assert.match(m.body.innerHTML,/核對並匯出快照CSV/);assert.match(m.body.innerHTML,/保存快照/);assert.doesNotMatch(m.body.innerHTML,/<li data-snapshot[^>]*data-source-locate/);await m.click();assert.equal(m.state.exports.length,1);assert.equal(m.state.reads,5);assert.equal(m.state.snapshots,4);assert.ok(m.state.exports[0].csv.includes(m.state.exports[0].s.sourceFingerprint));
});
test('sorting and display units are local presentation and preserve actual record and native payload',async()=>{
  const m=mounted(),before=JSON.stringify(m.state.record);await m.open();m.events.change({target:{matches:s=>s==='[data-snapshot-unit]',value:'cm'}});assert.match(m.body.innerHTML,/完成 L 400 cm/);m.events.change({target:{matches:s=>s==='[data-snapshot-order]',value:'length'}});assert.equal(JSON.stringify(m.state.record),before);assert.equal(m.state.reads,2);await m.click();assert.ok(m.state.exports[0].csv.includes('"mm","cm"'));
});
test('held real-shaped snapshot response is discarded after context, model mutation/removal, another selection or close',async()=>{
  for(const invalidate of [m=>m.state.context={id:'next-project'},m=>m.state.record.name='replacement',m=>m.state.record=null,m=>m.state.active=false,m=>{m.detail.open=false;m.events.toggle();},m=>m.state.stamp++]){
    const m=mounted();await m.open();const held=gate();m.state.snapshot=()=>held.promise;const pending=m.click();await tick();invalidate(m);held.resolve(sample().snapshot);await pending;assert.equal(m.state.exports.length,0);
  }
});
test('late native source changes before the final export read discard the ready earlier schedule',async()=>{
  const m=mounted();await m.open();let calls=0;m.state.read=async()=>++calls===3?fixtures.changedLive:live(sample());await m.click();assert.equal(m.state.exports.length,0);assert.match(m.body.innerHTML,/來源已更新/);
});
test('snapshot read and native source failures do not emit a CSV or retain a misleading ready table',async()=>{
  for(const fail of [m=>m.state.snapshot=async()=>{throw Error('snapshot failed');},m=>m.state.read=async()=>({ok:false})]){const m=mounted();await m.open();fail(m);await m.click();assert.equal(m.state.exports.length,0);assert.doesNotMatch(m.body.innerHTML,/data-model-schedule/);}
});
test('repeated export click while pending causes one read cycle and one download; cancellation forbids late export',async()=>{
  const m=mounted();await m.open();const held=gate();m.state.snapshot=()=>held.promise;const pending=m.click();await tick();await m.click();assert.equal(m.state.snapshots,3);held.resolve(sample().snapshot);await pending;assert.equal(m.state.exports.length,1);
  const stopped=mounted();await stopped.open();const late=gate();stopped.state.snapshot=()=>late.promise;const p=stopped.click();await tick();stopped.mount.cancel();late.resolve(sample().snapshot);await p;assert.equal(stopped.state.exports.length,0);
});
test('close then immediate reopen starts a fresh owner and an older finally cannot unlock or publish that owner',async()=>{
  const m=mounted();await m.open();const old=gate(),fresh=gate();let calls=0;m.state.snapshot=()=>++calls===1?old.promise:fresh.promise;const pending=m.click();await tick();m.detail.open=false;m.events.toggle();assert.doesNotMatch(m.body.innerHTML,/data-model-schedule|data-source-refresh/);m.detail.open=true;m.events.toggle();await until(()=>calls===2);old.resolve(sample().snapshot);await pending;await m.click();assert.equal(calls,2);assert.equal(m.state.exports.length,0);fresh.resolve(sample().snapshot);await until(()=>m.body.innerHTML.includes('data-model-schedule'));await m.click();assert.equal(m.state.exports.length,1);
});
test('live mount keeps its existing refresh and does not request snapshot schedules or export',async()=>{
  const m=mounted();m.mount.cancel();const events={},body={innerHTML:'',textContent:'',isConnected:true,addEventListener:(n,f)=>events[n]=f,removeEventListener(){}},detail={open:false,isConnected:true,dataset:{},classList:{add(){}},querySelector:()=>body,addEventListener:(n,f)=>events[n]=f,removeEventListener(){},remove(){}},host={querySelector:()=>null,ownerDocument:{createElement:()=>detail},append(){}};
  S.mount(host,{selection:'timber:0',context:()=>m.state.context,stamp:()=>1,read:async()=>live(sample()),readSnapshot:async()=>{throw Error('live source cannot borrow snapshot');},navigate:async()=>{}});detail.open=true;events.toggle();await tick();assert.match(body.innerHTML,/重新檢查/);assert.doesNotMatch(body.innerHTML,/快照CSV|data-model-schedule/);
});
test('single-owner app supplies current model visibility/selection guards and exports only via its mount callback',()=>{
  const mountedCalls=[],handlers={};let models=[sample().record],callback;
  const library={addEventListener:(n,f)=>handlers[n]=f},host={hidden:false,isConnected:true,closest:s=>s==='dialog'?{open:true}:null};const button={dataset:{smOpenModel:models[0].id},closest:()=>host};library.querySelectorAll=()=>[button];
  const doc={getElementById:id=>id==='smLibraryList'?library:null};
  const env={window:{addEventListener(){},SourceInspector:{...S,mount:(host,options)=>{mountedCalls.push(options);callback=options;return {detail:{isConnected:true},cancel(){}};}},GeometryProject:P,TimberSchedule:T},ReferenceWorkspace:{context:()=>({id:'p'}),history:{frame:1},getProjectState:()=>({revision:1}),getSpaceModels:()=>clone(models)},document:doc,oc:{sel:null},MutationObserver:class{observe(){}},queueMicrotask:()=>{}};
  // Same context identity is authoritative, not regenerated UUID/name equality.
  const ctx={id:'p'};env.ReferenceWorkspace.context=()=>ctx;vm.runInNewContext(fs.readFileSync(require.resolve('../geometry-web/source-inspector-app.js'),'utf8'),env);env.window.SourceInspectorApp.sync();assert.equal(mountedCalls.length,1);callback.activate();assert.equal(callback.isActive(),true);assert.deepEqual(callback.getRecord(),models[0]);const old=callback.stamp();handlers.click({target:{closest:()=>({})}});assert.notEqual(callback.stamp(),old);assert.equal(callback.isActive(),false);models=[];assert.equal(callback.getRecord(),null);
});
