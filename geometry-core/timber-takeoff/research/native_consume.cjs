'use strict';
/* Existing base product APIs over real native inputs; no native success mocks. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const [repo,out]=process.argv.slice(2);
const S=require(path.join(repo,'geometry-web/source-inspector.js'));
const P=require(path.join(repo,'geometry-web/project-store.js'));
const I=require(path.join(repo,'geometry-web/identity-ledger.js'));
const T=require(path.join(repo,'geometry-web/timber-supports.js'))(require(path.join(repo,'geometry-web/timber-schedule.js')));
const C=require(path.join(repo,'geometry-web/cutting-plan.js'));
const Settings=require(path.join(repo,'geometry-web/cutting-settings.js'));
const zip=require(path.join(repo,'geometry-web/vendor/fflate/umd/index.js'));
const read=name=>JSON.parse(fs.readFileSync(path.join(out,name),'utf8'));
const save=(name,value)=>fs.writeFileSync(path.join(out,name),JSON.stringify(value,null,2)+'\n');
function assertTypedRoots(data,input){
  assert.equal(data.ok,true);assert.equal(data.schema,'source-inspector/1');assert.equal(data.complete,true);
  const nodes=new Map();for(const node of data.nodes){assert.equal(typeof node.key,'string');assert.equal(nodes.has(node.key),false);nodes.set(node.key,node);}
  const typed=(kind,id)=>{
    assert.equal(Number.isSafeInteger(id)&&id>=0&&id<=4294967295,true);
    const key=`${kind}:${id}`,node=nodes.get(key);assert.ok(node,'U476_NATIVE_TYPED_ROOT_MISSING');
    const raw=node.id;if(typeof raw==='string')assert.match(raw,/^(0|[1-9][0-9]*)$/,'U476_NATIVE_ROOT_ID_CANONICAL');
    else assert.equal(typeof raw,'number','U476_NATIVE_ROOT_ID_TYPE');
    assert.equal(node.key,key,'U476_NATIVE_ROOT_KEY');assert.equal(node.kind,kind,'U476_NATIVE_ROOT_KIND');
    assert.equal(Number(raw),id,'U476_NATIVE_ROOT_ID');return node;
  };
  typed('placement',input.placement_id);
  for(const selected of input.timbers){assert.equal(selected.kind,'timber');const node=typed('timber',selected.id);assert.equal(node.placed,true);assert.equal(node.surface,input.placement_id);assert.equal(node.nativeOwner,null);}
}
async function scenario(name){
  const input=read(name+'/producer-input.json'),result=read(name+'/producer-result.json');
  const liveGraph=read(name+'/live-graph.json'),liveRefs=read(name+'/live-references.json');
  const snapshot=read(name+'/snapshot.json'),packageSnapshot=read(name+'/package-snapshot.json');
  for(const raw of [liveGraph,snapshot,packageSnapshot])assertTypedRoots(raw,input);
  const graph=S.index(liveGraph);
  const record={id:'u476-'+name,name:'U 原生重現 '+name,created_at:'2026-11-27T00:00:00Z',
    source:{kind:'scene',placement_id:0,boundary_id:1,scene_hash:result.source_sha256},input,result,
    sourceIdentity:I.buildSourceIdentity({...input,boundary_id:1},graph.nodes)};
  P.validateSpaceModel(record);
  await P.validateSpaceModelHashes(record);
  const envelope={baseline:S.index(snapshot),packageBaseline:S.index(packageSnapshot),
    packageSourceSha:record.result.source_sha256,graph,context:{id:'u476-native-reproduction'}};
  const live=T.derive(liveRefs,0,input.timbers.map(r=>r.id));
  const saved=S.deriveModelSchedule(record,envelope,T,P);
  assert.equal(saved.identityContinuity,'proved');
  assert.deepEqual(live.rows,saved.rows);
  assert.equal(live.rows.length,input.timbers.length);
  const scene=fs.readFileSync(path.join(out,name,'live.scene'),'utf8');
  const manifest={format:P.FORMAT,projectId:'u476-native-reproduction',name:'U 原生重現',
    sceneHash:await P.sha(new TextEncoder().encode(scene)),sources:[],faces:[],models:[record]};
  const packed=await P.pack(scene,manifest,new Map(),zip);
  fs.writeFileSync(path.join(out,name,'saved-project.gcanvas'),packed);
  const unpacked=await P.unpack(packed,zip);
  assert.deepEqual(unpacked.manifest.models[0],record);
  save(name+'/saved-record.json',record);
  save(name+'/live-schedule.json',live);
  save(name+'/saved-schedule.json',saved);
  fs.writeFileSync(path.join(out,name,'live-schedule.csv'),T.csv(live));
  fs.writeFileSync(path.join(out,name,'saved-schedule.csv'),S.modelScheduleCSV(saved,T));
  save(name+'/saved-validation.json',{validateSpaceModel:true,validateSpaceModelHashes:true,
    native_input_package_fingerprint_equal:snapshot.sourceFingerprint===packageSnapshot.sourceFingerprint,
    pack_unpack_record_equal:true,live_saved_rows_equal:true,identity_continuity:saved.identityContinuity});
  return {record,envelope,live,saved,liveRefs};
}
(async()=>{
  const single=await scenario('single'),control=await scenario('independent-control');
  assert.deepEqual(single.live.rows.map(r=>[r.id,r.A,r.B,r.L]),[[0,27,33,4000]]);
  assert.deepEqual(control.live.rows.map(r=>[r.id,r.A,r.B,r.L]),[[0,27,33,4000],[4,27,33,4000]]);
  assert.notDeepEqual(control.live.rows[0].origin,control.live.rows[1].origin);
  assert.notEqual(control.record.sourceIdentity.roots.find(r=>r.kind==='timber'&&r.id===0).incarnation,
    control.record.sourceIdentity.roots.find(r=>r.kind==='timber'&&r.id===4).incarnation);
  let multipleModels;
  try{S.deriveModelSchedule([single.record,control.record],single.envelope,T,P);multipleModels={accepted:true};}
  catch(error){multipleModels={accepted:false,message:error.message};}
  assert.equal(multipleModels.accepted,false);
  save('current-cross-world-guards.json',{multiple_saved_model_array:multipleModels,
    statement:'Existing APIs expose separate single-world schedules; these outputs are duplicate representations, not an observed same-call double-count bug.'});
  const settings={kerf:3,allowance:0,minRemnant:300,
    stockTypes:[{key:1,name:'U 研究明設原材',section:[27,33],material:null,length:4200,endTrim:5}],
    remnants:[],nextStockKey:2,nextRemnantKey:1};
  Settings.validate(settings);
  const one=await C.evaluate(single.liveRefs,settings,{world:{kind:'live'},scopes:[{surface:0,ids:[0]}]});
  const two=await C.evaluate(control.liveRefs,settings,{world:{kind:'live'},scopes:[{surface:0,ids:[0,4]}]});
  const repeatedScope=await C.evaluate(single.liveRefs,settings,{world:{kind:'live'},scopes:[{surface:0,ids:[0]},{surface:0,ids:[0]}]});
  const rejectedSaved=await C.evaluate(read('single/snapshot.json').timberReferences,settings,
    {world:{kind:'saved-model',id:single.record.id},scopes:[{surface:0,ids:[0]}]});
  const rejectedUnion=await C.evaluate(single.liveRefs,settings,{world:{kind:'union'},scopes:[{surface:0,ids:[0]}]});
  for(const p of [one,two,repeatedScope]){assert.equal(p.status,'COMPLETE');assert.equal(C.verify(p),true);}
  for(const p of [rejectedSaved,rejectedUnion]){assert.equal(p.status,'UNSUPPORTED');assert.equal(p.diagnostics[0].code,'WORLD_KIND');assert.deepEqual(p.groups,[]);}
  const count=p=>p.groups.reduce((n,g)=>n+g.newStockCount,0);
  assert.equal(count(one),1);assert.equal(count(two),2);assert.equal(count(repeatedScope),1);
  save('cutting-settings.json',settings);
  save('k1-single-native.json',one);
  save('k1-independent-control-native.json',two);
  save('k1-repeated-live-scope-native.json',repeatedScope);
  save('k1-saved-world-rejection-native.json',rejectedSaved);
  save('k1-union-world-rejection-native.json',rejectedUnion);
  fs.writeFileSync(path.join(out,'k1-single-native.csv'),C.csv(one));
  fs.writeFileSync(path.join(out,'k1-independent-control-native.csv'),C.csv(two));
  save('research-demand-arithmetic.json',{
    category:'研究對照；未啟用新的生產 union／physical-piece 去重規則',
    assumption:'研究情境明示假設：使用者在來源核對通過後，另外宣告 live 與此 ordinary-plan saved view 是同一實體件；此宣告未寫入產品。原生來源、內容及延續證明只是候選證據，不能單獨推出物理同件。這不是現行 K1 已接受的跨世界呼叫。',
    explicit_same_piece_declaration_required:true,same_settings_fingerprint:one.settingsFingerprint,
    source_length_mm:4000,stock_length_mm:4200,head_trim_mm:5,kerf_mm:3,tail_trim_mm:5,
    naive_separate_view_sum:{representation_rows:2,demand_rows_assumed:2,new_stock_count:count(one)+count(one),
      explanation:'同一 4000 mm 需求每個表示各買一支，數學對照為 1+1；無虛構 native union 成功。'},
    after_research_source_proof_dedup:{physical_demand_rows:1,new_stock_count:count(one)},
    independent_same_dimension_control:{physical_demand_rows:2,new_stock_count:count(two)},
    current_saved_world_status:rejectedSaved.status,current_union_world_status:rejectedUnion.status,
    current_repeated_same_live_id_new_stock_count:count(repeatedScope)});
  console.log(JSON.stringify({ok:true,live_rows:single.live.rows.length,saved_rows:single.saved.rows.length,
    continuity:single.saved.identityContinuity,independent_rows:control.live.rows.length,
    k1_single_new_stock:count(one),k1_independent_new_stock:count(two),
    cross_world_saved_status:rejectedSaved.status,cross_world_union_status:rejectedUnion.status}));
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
