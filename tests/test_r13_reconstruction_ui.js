'use strict';
// Node DOM seams exercise the actual adapter; this is not a Chrome receipt.
const test=require('node:test'), assert=require('node:assert/strict');
const fs=require('node:fs'), path=require('node:path');
const ROOT=path.resolve(__dirname,'..'), file=process.env.GEOMETRY_R13_UI_SOURCE||path.join(ROOT,'geometry-web/reconstruction-workspace.js');
const contract=require('./oracles/r13_e1_contract.json'),uiRow=id=>contract.uiRows.find(row=>row.id===id);
const clone=value=>JSON.parse(JSON.stringify(value));
function fixture(options={}){
  assert.ok(fs.existsSync(file),'R13_REAL_UNDERLAY_EDITOR_REGISTERED');
  const R=require('../geometry-web/reconstruction-data.js');
  let context={},value=null,token='context-a',operationBlocked=false,historySerial=0;
  const listeners=new Map(),elements=new Map(),calls=[];
  const element=id=>{
    if(elements.has(id))return elements.get(id);
    const handlers=new Map(),e={id,value:'',checked:false,disabled:false,hidden:false,open:true,isConnected:true,dataset:{},textContent:'',
      addEventListener(name,fn){handlers.set(name,fn);},
      dispatch(name,event={}){return handlers.get(name)?.({target:e,...event});},
      querySelector(selector){return elements.get(selector.replace(/^#/,''))||null;},
      querySelectorAll(){return [];},contains(){return true;},
      closest(selector){return selector==='button'&&id.startsWith('rd')?e:null;},focus(){},scrollIntoView(){},
      set innerHTML(text){this.html=text;this.renders=(this.renders||0)+1;for(const match of text.matchAll(/id="([^"]+)"/g))element(match[1]);},
      get innerHTML(){return this.html||'';}};
    elements.set(id,e);return e;
  };
  const pane=element('pane');pane.innerHTML='<details id="rdPanel"></details>';
  const host={context:()=>context,getProjectState:()=>({contextToken:token}),getModelOperationState:()=>({blocked:operationBlocked}),
    readFeatureAttachment:()=>clone(value),
    reconstructionEdit(action,expected){assert.equal(expected,token);calls.push(clone(action));value=R.edit(value||R.empty(),action);if(options.syncNotification)listeners.get('project-info-changed')?.();return clone(value);}};
  const w={GeometryReconstructionData:R,GeometryReconstructionValues:require('../geometry-core/reconstruction-values.js'),ReferenceWorkspace:host,addEventListener:(name,fn)=>listeners.set(name,fn),
    SpaceModelWorkspace:{openReconstruction:async(...args)=>calls.push(['open',...args])}};
  const UI=new Function('window','ReferenceWorkspace','GeometryReconstructionData','document','feSurf',
    fs.readFileSync(file,'utf8')+'\nreturn window.ReconstructionWorkspace;')(w,host,R,{getElementById:id=>elements.get(id)},()=>({id:11}));
  UI.bindPane(pane,7);
  const click=id=>element('rdPanel').dispatch('click',{target:element(id)});
  const input=(id,text)=>{element(id).value=text;return element('rdPanel').dispatch('input',{target:element(id)});};
  const change=(id,text)=>{element(id).value=text;return element('rdPanel').dispatch('change',{target:element(id)});};
  return {UI,R,host,w,e:element,click,input,change,calls,listeners,
    get value(){return clone(value);},set value(v){value=clone(v);},
    newContext(){context={};value=null;token='context-b';},block(){operationBlocked=true;},
    history(next,previous=token){value=clone(next);token='context-a-history-'+(++historySerial);
      listeners.get('project-local-history')?.({detail:{previousContextToken:previous,contextToken:token}});
      listeners.get('project-info-changed')?.();}};
}
test('R13 UI starts with empty values and records each raw input as manual, without 3000/100',()=>{
  const f=fixture();f.click('rdAdd');
  const record=f.value.records[0];
  assert.deepEqual(Object.values(record.fields).map(x=>x.raw),['','','',''],'R13_NO_NUMERIC_DEFAULTS');
  assert.deepEqual(Object.values(record.fields).map(x=>x.unit),[null,null,null,null],'R13_UNIT_REQUIRES_EXPLICIT_SELECTION');
  assert.equal(f.e('rdHeightUnit').value,'','R13_UNIT_UNKNOWN_VISIBLE');
  assert.match(f.e('rdPanel').innerHTML,/<option value="">尚未選單位<\/option>/,'R13_UNIT_UNKNOWN_OPTION');
  assert.equal(f.e('rdBottomBasis').value,'unknown');
  f.input('rdHeightRaw','250.1');f.change('rdHeightUnit','cm');f.click('rdConfirmHeight');
  assert.equal(f.value.records[0].fields.height.confirmation.value,2501,'R13_CONFIRMED_EXACT_INPUT');
  assert.deepEqual(f.value.records[0].fields.height.source,{kind:'manual'});
  f.input('rdTopRaw','尚待量測');f.UI.flush();
  assert.equal(f.value.records[0].fields.top.raw,'尚待量測','R13_UNFINISHED_RAW_SURVIVES_FLUSH');
  assert.equal(f.value.records[0].fields.top.confirmation,null);
});
test('R13 focused DOM text without a final input event is flushed; invalid capacity blocks save',()=>{
  const f=fixture();f.click('rdAdd');f.e('rdHeightRaw').value=' 250.01 ';f.UI.flush();
  assert.equal(f.value.records[0].fields.height.raw,' 250.01 ','R13_FOCUSED_RAW_FLUSH');
  f.e('rdHeightRaw').value='x'.repeat(65);
  assert.throws(()=>f.UI.flush(),undefined,'R13_UNSAVED_RAW_MUST_BLOCK_SAVE');
  assert.equal(f.value.records[0].fields.height.raw,' 250.01 ');
  f.e('rdHeightRaw').value='待量';f.UI.flush();assert.equal(f.value.records[0].fields.height.raw,'待量');
});
test('R13 IME may save unfinished raw but cannot confirm or adopt during composition',async()=>{
  const f=fixture();f.click('rdAdd');
  f.change('rdHeightUnit','mm');
  f.e('rdPanel').dispatch('compositionstart',{target:f.e('rdHeightRaw')});
  const row=uiRow('composing-save');f.input('rdHeightRaw',row.raw);const before=f.calls.length,renders=f.e('rdPanel').renders;f.UI.flush();
  f.click('rdConfirmHeight');await f.click('rdAdopt');
  assert.equal(f.value.records[0].fields.height.raw,'2500','R13_COMPOSITION_RAW_CAPTURE');
  assert.equal(f.value.records[0].fields.height.confirmation,null,'R13_COMPOSITION_NOT_CONFIRMATION');
  assert.equal(f.calls.some(x=>Array.isArray(x)&&x[0]==='open'),false);
  assert.deepEqual({confirmation:f.value.records[0].fields.height.confirmation,adoptionOpened:f.calls.some(x=>Array.isArray(x)&&x[0]==='open'),saveAddsHistory:f.calls.length!==before,controlReplaced:f.e('rdPanel').renders!==renders},row.expected,'R13_ORACLE_COMPOSING_SAVE');
  f.e('rdPanel').dispatch('compositionend',{target:f.e('rdHeightRaw')});f.click('rdConfirmHeight');
  assert.equal(f.value.records[0].fields.height.confirmation.value,2500);
});
test('R13 explicit basis, separate derived confirmation and explicit record-to-face adoption',async()=>{
  const f=fixture();f.click('rdAdd');f.change('rdBottomUnit','mm');f.change('rdHeightUnit','mm');f.change('rdTopUnit','mm');f.input('rdBottomRaw','-20');f.click('rdConfirmBottom');
  assert.equal(f.value.records[0].fields.bottom.confirmation?.value,-20,'R13_UNKNOWN_DATUM_OBSERVATION_CAN_CONFIRM');
  assert.equal(f.e('rdAdopt').disabled,true,'R13_UNKNOWN_DATUM_CANNOT_ADOPT');
  f.change('rdBottomBasis','world-z');f.input('rdBottomNote','本工程世界 Z 零點');f.click('rdConfirmBottom');
  f.input('rdHeightRaw','2501');f.click('rdConfirmHeight');
  f.change('rdTopBasis','world-z');f.input('rdTopNote','同一世界 Z 零點');
  assert.equal(f.value.records[0].fields.top.confirmation,null,'R13_DERIVATION_IS_NOT_AUTO_CONFIRM');
  f.click('rdConfirmDerived');assert.equal(f.value.records[0].fields.top.confirmation.value,2481);
  await f.click('rdAdopt');assert.deepEqual(f.calls.at(-1),['open','rd-1',11],'R13_EXPLICIT_ENTRY');
  assert.equal(f.value.reviews.length,0,'R13_ENTRY_PREVIEW_NOT_MODEL_WRITE');
});
test('R13 context switch and external history cannot write obsolete UI back over current data',()=>{
  const f=fixture();f.click('rdAdd');const original=f.value;
  f.value=f.R.edit(original,{type:'edit',id:'rd-1',fields:{height:{raw:'2600',unit:'mm',basis:{kind:'distance',note:''}}}});
  f.e('rdHeightRaw').value='2700';
  assert.throws(()=>f.UI.flush(),undefined,'R13_HISTORY_OWNER_REJECTS_STALE_RAW');
  assert.equal(f.value.records[0].fields.height.raw,'2600');
  f.newContext();f.e('rdHeightRaw').value='2800';assert.throws(()=>f.UI.flush(),undefined,'R13_CONTEXT_OWNER_REJECTS_STALE_RAW');
  assert.equal(f.value,null,'R13_NO_CROSS_CONTEXT_WRITES');
});
test('R13 old project pane is read only until an explicit add, and existing R10 stays in the common group',()=>{
  const f=fixture();const html=f.UI.paneHTML(7);assert.equal(f.value,null);assert.equal(f.calls.length,0);
  assert.match(html,/房間高度/);assert.match(html,/人工輸入/);
  const app=fs.readFileSync(path.join(ROOT,'geometry-web/app.js'),'utf8');
  assert.match(app,/ReconstructionWorkspace\?\.paneHTML\(bid\)/,'R13_COMMON_LEGACY_AND_SHARED_ROOM_PANE');
  assert.match(app,/ReconstructionWorkspace\?\.bindPane\(pane, bid\)/,'R13_REAL_PANE_EVENT_BINDING');
  const htmlIndex=fs.readFileSync(path.join(ROOT,'geometry-web/index.html'),'utf8');
  for(const file of ['kernel/reconstruction-values.js','reconstruction-data.js','reconstruction-workspace.js'])
    assert.match(htmlIndex,new RegExp('<script src="'+file.replaceAll('.','\\.')+'"></script>'),'R13_REAL_MODULE_LOAD_'+file);
});
test('R13 typing keeps the original controls through synchronous or scheduled project notifications',()=>{
  const f=fixture({syncNotification:true});f.click('rdAdd');
  const before=f.e('rdPanel').renders;
  f.input('rdHeightRaw','27');
  assert.equal(f.e('rdPanel').renders,before,'R13_INPUT_DOM_NOT_REPLACED_DURING_WRITE');
  f.listeners.get('project-info-changed')();
  assert.equal(f.e('rdPanel').renders,before,'R13_INPUT_DOM_NOT_REPLACED_AFTER_WRITE');
  f.input('rdHeightRaw','270');assert.equal(f.value.records[0].fields.height.raw,'270');
});
test('R13 three provided heights visibly list their conflict, sources, relation and exact difference',()=>{
  const f=fixture();f.click('rdAdd');
  for(const stem of ['Bottom','Height','Top'])f.change('rd'+stem+'Unit','mm');
  f.input('rdBottomRaw','0');f.change('rdBottomBasis','world-z');f.input('rdBottomNote','世界 Z 零點');f.click('rdConfirmBottom');
  f.input('rdHeightRaw','2700');f.click('rdConfirmHeight');
  f.input('rdTopRaw','2800');f.change('rdTopBasis','world-z');f.input('rdTopNote','同一世界 Z');
  const text=f.e('rdPlanStatus').textContent;
  assert.match(text,/底高[^\n]*0[^\n]*高度[^\n]*2700[^\n]*頂高[^\n]*2800/s,'R13_CONFLICT_VISIBLE_VALUES');
  assert.match(text,/人工/,'R13_CONFLICT_VISIBLE_SOURCES');
  assert.match(text,/底高\s*[+＋]\s*高度\s*[=＝]\s*頂高/,'R13_CONFLICT_VISIBLE_RELATION');
  assert.match(text,/差/,'R13_CONFLICT_VISIBLE_DIFFERENCE_LABEL');
  assert.match(text,/100\s*mm/,'R13_CONFLICT_EXACT_DIFFERENCE_100_MM');
  assert.equal(f.e('rdAdopt').disabled,true,'R13_CONFLICT_ADOPTION_REMAINS_BLOCKED');
  assert.equal(f.value.records[0].fields.top.raw,'2800','R13_CONFLICT_ALL_ORIGINALS_RETAINED');
  assert.equal(f.value.records[0].fields.top.confirmation,null,'R13_UNCONFIRMED_THIRD_STILL_PARTICIPATES');
});
test('R13 blocked raw flush preserves the exact editor text when the pane is rebound',()=>{
  const f=fixture();f.click('rdAdd');f.input('rdHeightRaw','2500');
  f.e('rdHeightRaw').value='尚未失焦原字';f.block();
  assert.throws(()=>f.UI.flush(),undefined,'R13_BLOCKED_RAW_SAVE_REJECTED');
  assert.equal(f.value.records[0].fields.height.raw,'2500','R13_BLOCKED_RAW_ZERO_WRITE');
  f.UI.bindPane(f.e('pane'),7);
  assert.equal(f.e('rdHeightRaw').value,'尚未失焦原字','R13_BLOCKED_RAW_REBIND_PRESERVES_TEXT');
  assert.equal(f.value.records[0].fields.height.raw,'2500','R13_REBIND_DOES_NOT_COMMIT_REJECTED_RAW');
});
test('R13 IME after external history retains rejected composition text through the next notification',()=>{
  const f=fixture();f.click('rdAdd');const original=f.value;
  f.e('rdPanel').dispatch('compositionstart',{target:f.e('rdHeightRaw')});f.input('rdHeightRaw','二');
  f.value=original;f.listeners.get('project-info-changed')();
  f.e('rdHeightRaw').value='二七';f.e('rdPanel').dispatch('compositionend',{target:f.e('rdHeightRaw')});
  assert.equal(f.value.records[0].fields.height.raw,'','R13_HISTORY_NOT_OVERWRITTEN_BY_COMPOSITION');
  f.listeners.get('project-info-changed')();
  assert.equal(f.e('rdHeightRaw').value,'二七','R13_IME_HISTORY_FAILURE_PRESERVES_TEXT');
  assert.equal(f.e('rdAdopt').disabled,true,'R13_REJECTED_COMPOSITION_NOT_ADOPTABLE');
});
test('R13 owned local undo renews only its exact editor token and allows the next ordinary input',()=>{
  const f=fixture();f.click('rdAdd');const original=f.value;f.input('rdHeightRaw','2500');
  f.history(original);
  assert.equal(f.e('rdHeightRaw').value,'','R13_UI_RENDERED_UNDO_CONTENT');
  f.input('rdHeightRaw','2700');
  assert.equal(f.value.records[0].fields.height.raw,'2700','R13_UI_CONTINUES_AFTER_OWNED_HISTORY');
  assert.doesNotThrow(()=>f.UI.flush(),'R13_UI_SAVE_AFTER_OWNED_HISTORY');
  const g=fixture();g.click('rdAdd');const untouched=g.value;g.input('rdHeightRaw','2500');
  g.history(untouched,'wrong-prior-owner');g.input('rdHeightRaw','2800');
  assert.equal(g.value.records[0].fields.height.raw,'','R13_UNRELATED_HISTORY_EVENT_CANNOT_RENEW_OWNER');
  const before=g.host.getProjectState().contextToken;g.newContext();
  g.listeners.get('project-local-history')?.({detail:{previousContextToken:before,contextToken:g.host.getProjectState().contextToken}});
  assert.throws(()=>g.UI.flush(),undefined,'R13_HISTORY_EVENT_CANNOT_CROSS_CONTEXT');
  assert.equal(g.value,null,'R13_HISTORY_EVENT_ZERO_CROSS_CONTEXT_WRITE');
});
test('R13 busy save accepts an exact unchanged editor without writing and still rejects pending raw',()=>{
  const f=fixture();f.click('rdAdd');f.input('rdHeightRaw','2500');
  const before=clone(f.value),calls=f.calls.length;f.block();
  assert.doesNotThrow(()=>f.UI.flush(),'R13_BUSY_UNCHANGED_FLUSH_IS_READ_ONLY');
  assert.equal(f.calls.length,calls,'R13_BUSY_UNCHANGED_FLUSH_DOES_NOT_WRITE');
  assert.deepEqual(f.value,before,'R13_BUSY_UNCHANGED_FLUSH_PRESERVES_PROJECT');
  f.e('rdHeightRaw').value='2700';
  assert.throws(()=>f.UI.flush(),undefined,'R13_BUSY_PENDING_RAW_REMAINS_REJECTED');
  assert.equal(f.calls.length,calls,'R13_BUSY_PENDING_RAW_ZERO_WRITE');
  assert.equal(f.value.records[0].fields.height.raw,'2500','R13_BUSY_PENDING_RAW_KEEPS_SAVED_ORIGINAL');
});

test('R13 raw edit commits once per changed input and composing save adds no duplicate operation',()=>{
  const f=fixture();f.click('rdAdd');const count=f.calls.length,version=f.value.nextRevision;
  const row=uiRow('raw-input-history');for(const raw of row.inputs)f.input('rdHeightRaw',raw);
  assert.equal(f.calls.length,count+2,'R13_RAW_ONE_OPERATION_PER_CHANGED_INPUT');
  assert.ok(f.value.nextRevision>version,'R13_RAW_REVISION_TRACKED');
  const before=clone(f.value),saved=f.calls.length;
  f.UI.flush();assert.deepEqual({successfulChanges:saved-count,raw:f.value.records[0].fields.height.raw,confirmation:f.value.records[0].fields.height.confirmation,saveAddsHistory:f.calls.length!==saved},row.expected,'R13_ORACLE_RAW_INPUT_HISTORY');
  f.e('rdPanel').dispatch('compositionstart',{target:f.e('rdHeightRaw')});
  f.input('rdHeightRaw','二七');const composition=clone(f.value),composingCount=f.calls.length;
  f.UI.flush();
  assert.equal(f.calls.length,composingCount,'R13_COMPOSING_SAVE_NO_DUPLICATE_HISTORY');
  assert.deepEqual(f.value,composition,'R13_COMPOSING_SAVE_EXACT_CURRENT_RAW');
  assert.equal(f.e('rdHeightRaw').value,'二七','R13_COMPOSING_SAVE_RETAINS_INPUT_ELEMENT');
  f.e('rdPanel').dispatch('compositionend',{target:f.e('rdHeightRaw')});
  f.input('rdHeightRaw','二七');
  assert.equal(f.calls.length,composingCount,'R13_UNCHANGED_INPUT_IS_NOOP');
  assert.equal(saved,count+2);assert.equal(before.records[0].fields.height.raw,'27');
});

test('R13 actual underlay dispatcher mounts and binds the same editor in ordinary and D13 branches',()=>{
  const source=fs.readFileSync(process.env.GEOMETRY_R13_APP_SOURCE||path.join(ROOT,'geometry-web/app.js'),'utf8');
  const functionText=name=>{const start=source.indexOf('function '+name+'(');assert.ok(start>=0,'R13_REAL_UNDERLAY_FUNCTION_'+name);const end=source.indexOf('\nfunction ',start+1);return source.slice(start,end<0?undefined:end);};
  for(const shared of [false,true]){
    let mounted=0,bound=0,legacy=0,rooms=0;
    const reconstruction={paneHTML(){mounted++;return '<details id="rdPanel"></details>';},bindPane(){bound++;}};
    const room={roomForBoundary:()=>shared?{id:'room'}:null,paneHTML(){rooms++;return shared?'<details id="refRecordDetails">原頁歷史紀錄與核對</details>':'';},bindPane(){}};
    const reference={active:()=>null,reconstructionState:()=> 'unreviewed',paneHTML(){legacy++;return '<details id="refRecordDetails">來源紀錄與待補資訊</details>';},bindPane(){}};
    const outline={paneHTML:()=>'',bindPane(){}},env={window:{RoomCollectionWorkspace:room,ReconstructionWorkspace:reconstruction},RoomCollectionWorkspace:room,ReferenceWorkspace:reference,RoomOutlineWorkspace:outline,oc:{underlays:{}},fe:{fiTab:'underlay'},feSyncUnderlayReadonlyControls(){}};
    const api=new Function(...Object.keys(env),functionText('feUnderlayPaneHTML')+'\n'+functionText('feBindUnderlayPane')+'\nreturn {html:feUnderlayPaneHTML,bind:feBindUnderlayPane};')(...Object.values(env));
    const html=api.html(7);api.bind({querySelector:()=>null},7);
    assert.equal(mounted,1,'R13_ONE_EDITOR_PER_ROUTE_'+shared);assert.equal(bound,1,'R13_LIVE_BIND_PER_ROUTE_'+shared);
    assert.equal(legacy,shared?0:1,'R13_LEGACY_BRANCH_RETAINED_'+shared);assert.equal(rooms,1,'R13_ROOM_BRANCH_RETAINED_'+shared);
    assert.equal((html.match(/id="rdPanel"/g)||[]).length,1,'R13_NO_DUPLICATE_EDITOR_'+shared);
    assert.match(html,shared?/原頁歷史紀錄與核對/:/來源紀錄與待補資訊/,'R13_SOURCE_HISTORY_RETAINED_'+shared);
  }
});

test('R13 project record list survives a face switch without inventing a persistent association',()=>{
  const f=fixture();f.click('rdAdd');f.input('rdName','一號房');f.click('rdAdd');f.input('rdName','二號房');
  const before=JSON.stringify(f.value.records);f.UI.bindPane(f.e('pane'),8);
  const records=f.value.records;
  assert.deepEqual({storedAssociation:records.some(record=>record.association!=null),recordCountAfterFaceSwitch:records.length,recordBytesChangedByFaceSwitch:JSON.stringify(records)!==before},uiRow('unassociated-project-records').expected,'R13_ORACLE_PROJECT_RECORD_SCOPE');
  assert.match(f.e('rdPanel').innerHTML,/一號房/,'R13_BOTH_RECORDS_VISIBLE_AFTER_FACE_SWITCH');
  assert.match(f.e('rdPanel').innerHTML,/二號房/,'R13_BOTH_RECORDS_VISIBLE_AFTER_FACE_SWITCH');
});

test('R13 saved-model status keeps conditional scope and human-only top checks visible',async()=>{
  const f=fixture();f.click('rdAdd');const R=f.R,id=f.value.records[0].id;
  let value=R.edit(f.value,{type:'edit',id,fields:{bottom:{raw:'0',unit:'mm',basis:{kind:'world-z',note:''}},height:{raw:'2531',unit:'mm'}}});
  for(const field of ['bottom','height'])value=R.edit(value,{type:'confirm',id,field});
  // These are bounded owner records for the display seam, not geometric native evidence.
  const model=wall=>({id:'display-model',source:{},input:{mode:'plan',base_scene:'',settings:{bottom:0,height:2531,wall_thickness:wall}},result:{}});
  value.reviews.push(await R.makeReview(value,id,model(null)));f.value=value;
  const partial=f.UI.reviewSummary('display-model');
  assert.match(partial,/僅依本次已定資料的條件結果/,'R13_PARTIAL_MODEL_IS_NOT_FULLY_REVIEWED');
  assert.match(partial,/頂高：缺值/,'R13_PARTIAL_TOP_REASON_VISIBLE');assert.match(partial,/牆厚（選用）：缺值/,'R13_PARTIAL_WALL_REASON_VISIBLE');
  value.reviews=[];value=R.edit(value,{type:'edit',id,fields:{top:{raw:'2531',unit:'mm',basis:{kind:'world-z',note:''}},wallThickness:{raw:'137',unit:'mm'}}});
  for(const field of ['top','wallThickness'])value=R.edit(value,{type:'confirm',id,field});
  value.reviews.push(await R.makeReview(value,id,model(137)));f.value=value;
  assert.match(f.UI.reviewSummary('display-model'),/明選 1 筆房間高度已核對/,'R13_FULLY_REVIEWED_EXPLICIT_SCOPE_VISIBLE');
  assert.match(f.UI.reviewSummary('display-model'),/頂高：僅人工核對（2531 mm），未直接供值/,'R13_TOP_HUMAN_CHECK_NOT_MODEL_SUPPLY_VISIBLE');
});

test('R13 canvas shared-image fixture preserves real source history with its actual owner selector',async()=>{
  // Execute the fixture's actual source-room construction; no browser or layout claim.
  const section=fs.readFileSync(path.join(ROOT,'geometry-web/canvas_sections/P4313.js'),'utf8');
  const start=section.indexOf('const plane=GeometrySourcePlane.fromPage(page'),end=section.indexOf("ReferenceWorkspace.setFeatureAttachment('source-rooms'",start);
  assert.ok(start>=0&&end>start,'R13_CANVAS_SHARED_FIXTURE_AVAILABLE');
  const S=require('../geometry-web/source-plane.js'),Rooms=require('../geometry-web/room-collection.js');
  const hash='1'.repeat(64),page={sourceId:hash,page:1,imgW:400,imgH:300,mmPerPx:10,x:0,y:0,rot:0,
    calibration:{points:[[0,0],[400,0]],distanceMm:4000,inputValue:4000,inputUnit:'mm'}};
  const boundary={kind:'unspecified',loops:[{verts:[[0,0],[4000,0],[4000,3000],[0,3000]],fixity:[1,1,1,1]}],geometryFingerprint:'2'.repeat(64)};
  const data=await new Function('GeometrySourcePlane','GeometryRoomCollection','page','api','return (async()=>{'+section.slice(start,end)+'return data;})();')(S,Rooms,page,async command=>{assert.equal(command,'boundary 4313');return boundary;});
  assert.doesNotThrow(()=>S.validate(data,new Map([[hash,{meta:{id:hash,hash,type:'image/png'}}]])),'R13_CANVAS_SHARED_FIXTURE_IS_VALID');
  assert.equal(data.legacyHistory?.length,1,'R13_CANVAS_SHARED_HISTORY_FIXTURE');
  assert.equal(data.legacyHistory[0].records[0].value,null,'R13_CANVAS_HISTORY_STAYS_MISSING');
  const roomSource=fs.readFileSync(path.join(ROOT,'geometry-web/room-collection-workspace.js'),'utf8');
  const hs=roomSource.indexOf('  function historyHTML('),he=roomSource.indexOf('  function bindHistory(',hs);
  assert.ok(hs>=0&&he>hs,'R13_REAL_SHARED_HISTORY_RENDERER');
  const history=new Function(roomSource.slice(hs,he)+'return historyHTML;')()(data,'p4313-plane',false);
  assert.match(history,/data-room-source-history="p4313-plane"/,'R13_SHARED_IMAGE_HISTORY_SELECTOR');
  assert.doesNotMatch(history,/id="refRecordDetails"/,'R13_IMAGE_HISTORY_HAS_NO_PDF_EVIDENCE_ID');
  assert.ok(section.includes("[data-room-source-history=\"p4313-plane\"]"),'R13_CANVAS_USES_ACTUAL_HISTORY_SELECTOR');
  const openPurposes=section.indexOf("ctl('#smBoundaryAdvanced > summary')"),choosePurpose=section.indexOf("select('#smFloor','boundary')");
  assert.ok(openPurposes>=0&&choosePurpose>openPurposes,'R13_CANVAS_EXPANDS_REAL_END_PURPOSE_CONTROLS');
  assert.ok(section.includes('await expectNativeDialog(')&&section.includes('message:newProjectMessage,accept:true'), 'R13_CANVAS_EXPECTS_ONLY_ITS_EXACT_NEW_PROJECT_DIALOG');
  assert.ok(section.includes('ReferenceWorkspace.context().dirty===true'),'R13_CANVAS_NEW_PROJECT_DIALOG_PINS_DIRTY_STATE');
  const messageLine=section.match(/    const newProjectMessage=([^\n]+);/);
  assert.ok(messageLine,'R13_CANVAS_EXACT_NEW_PROJECT_MESSAGE_AVAILABLE');
  const expectedMessage=new Function('dirty','return '+messageLine[1]+';');
  const ownerSource=fs.readFileSync(path.join(ROOT,'geometry-web/reference-workspace.js'),'utf8');
  const ownerStart=ownerSource.indexOf('  async function replaceWithEmpty('),ownerEnd=ownerSource.indexOf('    const previous=context()',ownerStart);
  assert.ok(ownerStart>=0&&ownerEnd>ownerStart,'R13_CANVAS_REAL_NEW_PROJECT_CONFIRM_OWNER');
  for(const dirty of [false,true]){
    let actual=null;
    await new Function('window','context','assertWritableLease','assertRoomDraftIdle','busy','oc','history','pendingLoad',
      ownerSource.slice(ownerStart,ownerEnd)+'}\nreturn replaceWithEmpty(false);')({confirm(message){actual=message;return false;}},()=>({dirty}),()=>{},()=>{},false,{busy:false},{group:null},false);
    assert.equal(expectedMessage(dirty),actual,'R13_CANVAS_EXACT_DIALOG_MATCHES_OWNER_'+dirty);
  }
});

// The browser driver must await the end of the actual App history operation,
// not only the earlier attachment swap. Keep repaint pending deterministically
// and execute the original handler, owner state and save guard without a browser.
function historyCompletionHarness(verb){
  const vm=require('node:vm');
  const app=fs.readFileSync(path.join(ROOT,'geometry-web/app.js'),'utf8').replace(/\r\n/g,'\n');
  const owner=fs.readFileSync(path.join(ROOT,'geometry-web/reference-workspace.js'),'utf8').replace(/\r\n/g,'\n');
  const section=fs.readFileSync(process.env.GEOMETRY_R13_CANVAS_SOURCE||path.join(ROOT,'geometry-web/canvas_sections/P4313.js'),'utf8');
  function between(source,startText,endText){
    const start=source.indexOf(startText),end=source.indexOf(endText,start);
    assert.ok(start>=0&&end>start,'R13_HISTORY_ACTUAL_SOURCE '+startText);
    assert.equal(source.indexOf(startText,start+1),-1,'R13_HISTORY_UNIQUE_SOURCE '+startText);
    return source.slice(start,end);
  }
  const marker=verb==='undo'?'Undo':'Redo';
  const pattern=new RegExp("await ctl\\('#face"+marker+"Button'\\);await waitForUI\\((`[^`]+`)\\);");
  const match=section.match(pattern);
  assert.ok(match,'R13_CANVAS_EXISTING_HISTORY_WAIT '+verb);
  const expression=new Function('feature','return '+match[1]+';')("ReferenceWorkspace.readFeatureAttachment('reconstruction-data')");
  const deferred=()=>{let resolve;const promise=new Promise(r=>{resolve=r;});return {promise,resolve};};
  const painting=deferred(),paintStarted=deferred(),faceRefresh=deferred(),faceStarted=deferred();
  const model={id:'model-r13',height:2700},review={modelId:model.id,scope:['room-r13']};
  const state={id:'project-r13',models:verb==='undo'?[model]:[],reviews:verb==='undo'?[review]:[]};
  const classes=new Set(),history={undo:[],redo:[],group:null,frame:{}},statuses=[];
  let serial=0;
  const context={oc:{busy:false,on:true,focus:{t:'face',id:4313},faces:[{kind:'boundary',id:4313}],spaces:[]},
    document:{body:{classList:{add:key=>classes.add(key),remove:key=>classes.delete(key)}}},
    window:{},fe:{},history,busy:false,sceneTransaction:null,preparingSceneLoad:false,pendingLoad:null,
    nativePending:0,nativeRevision:1,nativeSession:'session-r13',connection:{phase:'ready',session:'session-r13'},
    modelOperationIdentities:new WeakMap(),uuid:()=>String(++serial),context:()=>state,
    getProjectState:()=>({id:state.id,contextToken:'context-r13',revision:1}),assertModelReady(){},assertEditable(){},
    ReferenceWorkspace:{context:()=>state,historyActionLabel:()=>null,getSpaceModels:()=>state.models,
      readFeatureAttachment:()=>({reviews:state.reviews})},
    api:async command=>{assert.equal(command,'line '+verb);state.models=verb==='redo'?[model]:[];state.reviews=verb==='redo'?[review]:[];return {ok:true};},
    clearCanvasSelections(){},renderObjects:()=>{paintStarted.resolve();return painting.promise;},
    feAfterChange:()=>{faceStarted.resolve();return faceRefresh.promise;},
    setStatus:message=>statuses.push(message),toast(){throw Error('R13_UNEXPECTED_BUSY_HISTORY_REENTRY');}};
  vm.createContext(context);
  vm.runInContext(between(app,'async function doUndoRedo(verb) {','\n$("btnUndo").addEventListener')+
    between(owner,'  function getModelOperationState() {','  function dirty(')+
    between(owner,'  function getEvidenceState() {','  const recoveryPeer=')+
    between(owner,'  function assertSaveReady(transactionOwner=null) {','  function unchanged('),context);
  context.ReferenceWorkspace.getEvidenceState=context.getEvidenceState;
  return {state,context,classes,statuses,painting,paintStarted,faceRefresh,faceStarted,
    start:()=>context.doUndoRedo(verb),ready:()=>vm.runInContext(expression,context),saveReady:()=>context.assertSaveReady()};
}
for(const verb of ['undo','redo'])test('R13 canvas '+verb+' waits for both App repaint stages before saving',async()=>{
  const h=historyCompletionHarness(verb),label='R13_CANVAS_'+verb.toUpperCase()+'_WAITS_FOR_HISTORY_IDLE';
  assert.equal(h.ready(),false,'R13_HISTORY_TARGET_NOT_REACHED '+verb);
  const operation=h.start();
  try{
    await h.paintStarted.promise;
    for(const stage of ['objects','face']){
      if(stage==='face'){h.painting.resolve();await h.faceStarted.promise;}
      assert.equal(h.state.models.length,verb==='redo'?1:0,'R13_HISTORY_MODEL_ALREADY_SWAPPED');
      assert.equal(h.state.reviews.length,verb==='redo'?1:0,'R13_HISTORY_REVIEW_ALREADY_SWAPPED');
      assert.equal(h.context.oc.busy,true,'R13_HISTORY_REPAINT_STILL_OWNED');
      assert.throws(h.saveReady,/請先完成目前的操作再保存/,'R13_REAL_SAVE_GUARD_REJECTS_REPAINT');
      console.log('R13_HISTORY_WAIT '+JSON.stringify({verb,stage,ocBusy:h.context.oc.busy,ownerBlocked:h.context.getEvidenceState().blocked,predicate:h.ready()}));
      assert.equal(h.ready(),false,label+' '+stage);
    }
  }finally{h.painting.resolve();h.faceRefresh.resolve();await operation;}
  assert.equal(h.context.oc.busy,false,'R13_HISTORY_FINALLY_RELEASED');
  assert.equal(h.classes.has('oc-busy'),false,'R13_HISTORY_PRESENTATION_RELEASED');
  assert.equal(h.ready(),true,'R13_HISTORY_WAIT_ACCEPTS_COMPLETION '+verb);
  assert.doesNotThrow(h.saveReady,'R13_SAVE_ALLOWED_AFTER_HISTORY_COMPLETION');
  // An idle owner is not sufficient: preserve each original data predicate.
  const originalModels=h.state.models,originalReviews=h.state.reviews;
  h.state.models=verb==='redo'?[]:[{}];assert.equal(h.ready(),false,'R13_HISTORY_MODEL_PREDICATE_RETAINED');
  h.state.models=originalModels;h.state.reviews=verb==='redo'?[]:[{}];assert.equal(h.ready(),false,'R13_HISTORY_REVIEW_PREDICATE_RETAINED');
  h.state.reviews=originalReviews;h.context.connection.phase='error';assert.equal(h.ready(),false,'R13_HISTORY_CONNECTION_MUST_BE_READY');
});
