'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),Module=require('node:module'),path=require('node:path');
const {R,available,names,defaults,basis}=require('./fixtures/r13_rc_n1.cjs');
function fixture(){
 const file=require.resolve('./test_r13_reconstruction_ui.js'),m=new Module(file,module);m.filename=file;m.paths=Module._nodeModulePaths(path.dirname(file));const normal=m.require.bind(m);
 m.require=name=>name==='node:test'?()=>{}:normal(name);m._compile(fs.readFileSync(file,'utf8')+'\nmodule.exports={fixture};',file);return m.exports.fixture({syncNotification:true});
}
const stem=k=>k[0].toUpperCase()+k.slice(1);
function create(kind){const f=fixture();assert.match(f.UI.paneHTML(),/id="rdKind"/,'R13_N1_TEMPLATE_CHOICE_VISIBLE');f.change('rdKind',kind);f.click('rdAdd');assert.equal(f.value.records[0].kind,kind,'R13_N1_UI_CREATED_CHOICE');return f;}
function fill(f,kind){if(kind==='rc-beam')f.change('rdAxis','x');for(const key of names[kind]){const s=stem(key);f.input('rd'+s+'Raw',String(defaults[kind][key]));f.change('rd'+s+'Unit','mm');if(basis(kind,key)!=='distance')f.change('rd'+s+'Basis',basis(kind,key));f.click('rdConfirm'+s);}}
test('R13_N1_U01 reuses one editor with explicit kinds no new always-visible action blocks',()=>{
 for(const kind of ['rc-column','rc-beam']){const f=create(kind);assert.ok(f.e('rdPanel').innerHTML.includes('人工輸入'),'R13_N1_UI_MANUAL_DISCLOSURE');assert.deepEqual(Object.keys(f.value.records[0].fields),names[kind]);assert.equal(f.value.records[0].spaceId,null);assert.equal(f.e('rdAdopt').hidden,true,'R13_N1_RC_ADOPT_HIDDEN');}
});
test('R13_N1_U02 column origin labels are not centres and beam uses centre on other axis',()=>{
 const c=create('rc-column');assert.match(c.e('rdPanel').innerHTML,/X 起點/,'R13_N1_COLUMN_X_ORIGIN_LABEL');assert.match(c.e('rdPanel').innerHTML,/Y 起點/,'R13_N1_COLUMN_Y_ORIGIN_LABEL');
 const b=create('rc-beam');assert.match(b.e('rdPanel').innerHTML,/橫向中線/,'R13_N1_BEAM_CENTER_LABEL');
});
test('R13_N1_U03 confirms exact manual fields and blocks forged RC adoption event',async()=>{
 for(const kind of ['rc-column','rc-beam']){const f=create(kind);fill(f,kind);assert.deepEqual(R.rcValues(f.value.records[0]),defaults[kind],'R13_N1_UI_CONFIRMED_VALUES');await f.click('rdAdopt');assert.equal(f.calls.some(x=>Array.isArray(x)&&x[0]==='open'),false,'R13_N1_FORGED_RC_ADOPT_REJECTED');assert.equal(f.e('rdPlanStatus').textContent,'RC 尺寸與位置基準已核對；目前只保存資料，尚未建立柱樑模型。','R13_N1_DATA_ONLY_STATUS');}
});
test('R13_N1_U04 axis switch keeps focused controls raw basis and cancels only dependent confirms',()=>{
 const f=create('rc-beam');fill(f,'rc-beam');const renders=f.e('rdPanel').renders,old=f.value.records[0];f.change('rdAxis','y');
 assert.equal(f.e('rdPanel').renders,renders,'R13_N1_AXIS_DOM_NOT_REPLACED');
 for(const key of ['start','end','center']){assert.equal(f.value.records[0].fields[key].confirmation,null);assert.equal(f.e('rd'+stem(key)+'Raw').value,old.fields[key].raw,'R13_N1_AXIS_UI_RAW');assert.equal(f.e('rd'+stem(key)+'Basis').value,old.fields[key].basis.kind,'R13_N1_AXIS_UI_BASIS');}
});
test('R13_N1_U05 beam relation conflict names depth not height and retains all originals',()=>{
 const f=create('rc-beam');fill(f,'rc-beam');f.input('rdTopRaw','2801');const msg=f.e('rdPlanStatus').textContent;
 assert.match(msg,/樑底.*樑深.*樑頂/s,'R13_N1_BEAM_RELATION_VISIBLE');assert.match(msg,/人工輸入/);assert.match(msg,/1\s*mm/,'R13_N1_CONFLICT_DIFFERENCE');assert.equal(f.value.records[0].fields.top.raw,'2801');assert.equal(f.e('rdAdopt').hidden,true);
});
test('R13_N1_U06 raw flush IME failed save and history keep visible uncommitted text',()=>{
 const f=create('rc-column');f.e('rdXRaw').value='待量';f.UI.flush();assert.equal(f.value.records[0].fields.x.raw,'待量','R13_N1_RC_FOCUSED_RAW_FLUSH');
 f.e('rdPanel').dispatch('compositionstart');f.input('rdXRaw','3');f.change('rdXUnit','mm');f.click('rdConfirmX');assert.equal(f.value.records[0].fields.x.confirmation,null,'R13_N1_RC_IME_NO_CONFIRM');
 f.e('rdPanel').dispatch('compositionend');f.click('rdConfirmX');assert.equal(f.value.records[0].fields.x.confirmation.value,3);
 f.e('rdXRaw').value='x'.repeat(65);assert.throws(()=>f.UI.flush(),undefined,'R13_N1_RC_FAILED_FLUSH_BLOCKS');assert.equal(f.e('rdXRaw').value,'x'.repeat(65));assert.equal(f.value.records[0].fields.x.raw,'3');
});
for(const kind of ['rc-column','rc-beam'])test('R13_N1_U07 '+kind+' keeps saved CR and CRLF originals through textarea projection and no-op save',()=>{
 const f=create(kind),key=kind==='rc-column'?'x':'start',s=stem(key),raw='12\r\n待量\r34',note='基準\r\n待核';
 assert.match(f.e('rdPanel').innerHTML,new RegExp('<textarea id="rd'+s+'Raw"'),'R13_N1_RAW_MULTILINE_CONTROL');
 // Model the browser value projection, rather than assuming a plain JS object
 // reproduces textarea/input normalization. The persisted bytes remain distinct.
 for(const [id,normalize] of [['rd'+s+'Raw',v=>v.replace(/\r\n?/g,'\n')],['rd'+s+'Note',v=>v.replace(/[\r\n]/g,'')]]){
  let visible=f.e(id).value;Object.defineProperty(f.e(id),'value',{configurable:true,get:()=>visible,set:value=>{visible=normalize(value);}});
 }
 const next=R.edit(f.value,{type:'edit',id:'rd-1',fields:{[key]:{raw,unit:null,basis:{kind:'unknown',note}}}});
 f.value=next;f.listeners.get('project-info-changed')();
 assert.equal(f.e('rd'+s+'Raw').value,'12\n待量\n34','R13_N1_BROWSER_NEWLINE_PROJECTION');
 const before=f.calls.length;f.UI.flush();
 assert.deepEqual(f.value,next,'R13_N1_PROJECTED_RAW_EXACT');
 assert.equal(f.calls.length,before,'R13_N1_PROJECTION_SAVE_IS_NOOP');
 f.input('rd'+s+'Raw','新\r\n輸入');
 assert.equal(f.value.records[0].fields[key].raw,'新\n輸入','R13_N1_CHANGED_DISPLAY_BECOMES_NEW_RAW');
 assert.equal(f.value.records[0].fields[key].basis.note,note,'R13_N1_UNCHANGED_NOTE_ORIGINAL_RETAINED');
});
for(const release of ['notification','detached-save'])test('R13_N1_U08 '+release+' keeps foreign RC draft without writing or blocking the new project',()=>{
 const f=create('rc-column'),oldContext=f.host.context(),oldToken=f.host.getProjectState().contextToken,oldValue=f.value;
 f.e('rdXRaw').value='尚未送出輸入事件';f.e('rdPanel').isConnected=false;f.newContext();
 const other=R.edit(R.empty(),{type:'create',kind:'rc-column',name:'另一專案同號資料'});f.value=other;
 if(release==='notification')f.listeners.get('project-info-changed')();
 assert.doesNotThrow(()=>f.UI.flush(),'R13_N1_FOREIGN_PANE_DOES_NOT_BLOCK_SAVE');
 assert.deepEqual(f.value,other,'R13_N1_FOREIGN_PANE_ZERO_CROSS_PROJECT_WRITE');
 f.host.context=()=>oldContext;f.host.getProjectState=()=>({contextToken:oldToken});f.value=oldValue;f.e('rdPanel').isConnected=true;
 f.UI.bindPane(f.e('pane'),7);
 assert.equal(f.e('rdXRaw').value,'尚未送出輸入事件','R13_N1_FOREIGN_DRAFT_RETAINED');
 assert.deepEqual(f.value,oldValue,'R13_N1_RETURNED_DRAFT_NOT_SILENTLY_COMMITTED');
});
test('R13_N1_U09 canvas history predicates wait for idle and retain their exact data conditions',()=>{
 const vm=require('node:vm'),source=fs.readFileSync(process.env.GEOMETRY_N1_CANVAS_SOURCE||path.join(__dirname,'../geometry-web/canvas_sections/P4314.js'),'utf8');
 const needles=['${first}.fields.top.confirmation===null','${first}.fields.top.confirmation?.value===2600','${feature}.records.length===2'];
 const waits=[...source.matchAll(/await waitForUI\((`[^`]+`)\);/g)].map(m=>m[1]);
 for(const needle of needles){
  const matches=waits.filter(s=>s.includes(needle)&&!s.includes('${last}.kind'));assert.equal(matches.length,1,'R13_N1_CANVAS_HISTORY_WAIT_UNIQUE');
  const feature="ReferenceWorkspace.readFeatureAttachment('reconstruction-data')",first=feature+'.records.at(0)';
  const expression=new Function('feature','first','return '+matches[0]+';')(feature,first);
  const record={fields:{top:{confirmation:needle.includes('2600')?{value:2600}:null}}};
  const attachment={records:needle.includes('records.length')?[record,record]:[record]};
  let blocked=false;const context={connection:{phase:'ready'},oc:{busy:false},ReferenceWorkspace:{readFeatureAttachment:()=>attachment,getEvidenceState:()=>({blocked})}};
  const ready=()=>vm.runInNewContext(expression,context);
  assert.equal(ready(),true,'R13_N1_HISTORY_COMPLETION_ACCEPTED');
  context.oc.busy=true;assert.equal(ready(),false,'R13_N1_CANVAS_HISTORY_IDLE');context.oc.busy=false;
  blocked=true;assert.equal(ready(),false,'R13_N1_CANVAS_HISTORY_OWNER_RELEASED');blocked=false;
  context.connection.phase='error';assert.equal(ready(),false,'R13_N1_CANVAS_HISTORY_CONNECTION_READY');context.connection.phase='ready';
  if(needle.includes('records.length'))attachment.records.pop();else record.fields.top.confirmation=needle.includes('2600')?null:{value:2600};
  assert.equal(ready(),false,'R13_N1_CANVAS_HISTORY_DATA_CONDITION_RETAINED');
 }
});
test('R13_N1_U10 native select reacquires controls replaced by each real change event',async()=>{
 const vm=require('node:vm'),source=fs.readFileSync(process.env.GEOMETRY_N1_CANVAS_SOURCE||path.join(__dirname,'../geometry-web/canvas_sections/P4314.js'),'utf8');
 const start=source.indexOf('  async function select(selector,value){'),end=source.indexOf('  async function inspector(){',start);
 assert.ok(start>=0&&end>start,'R13_N1_NATIVE_SELECT_SOURCE');
 const values=['','rd-1','rd-2'];let selected='',active=null,generation=0;
 function makeControl(){return {tagName:'SELECT',value:selected,generation:++generation,options:values.map(value=>({value,disabled:false,closest:()=>null}))};}
 let control=makeControl();const document={querySelector:()=>control,get activeElement(){return active;}};
 const read=async expression=>vm.runInNewContext(expression,{document});
 const ctl=async()=>{active=control;};
 const key=async key=>{
  if(['ArrowDown','ArrowUp','Home'].includes(key)&&active===control){
   const at=values.indexOf(selected),next=key==='Home'?0:key==='ArrowDown'?Math.min(at+1,values.length-1):Math.max(at-1,0);
   if(next!==at){selected=values[next];control=makeControl();active=null;}
  }
 };
 const waitForUI=async expression=>assert.equal(await read(expression),true,'R13_N1_NATIVE_SELECT_TARGET_REACHED');
 const select=new Function('read','ctl','key','waitForUI',source.slice(start,end)+'\nreturn select;')(read,ctl,key,waitForUI);
 await assert.doesNotReject(()=>select('#rdSelect','rd-2'),'R13_N1_NATIVE_SELECT_REACQUIRE');
 assert.equal(selected,'rd-2','R13_N1_NATIVE_SELECT_SECOND_RECORD');
 await assert.doesNotReject(()=>select('#rdSelect','rd-1'),'R13_N1_NATIVE_SELECT_REACQUIRE');
 assert.equal(selected,'rd-1','R13_N1_NATIVE_SELECT_RETURN_FIRST_RECORD');
});
