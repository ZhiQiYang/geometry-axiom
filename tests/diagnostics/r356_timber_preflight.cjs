'use strict';
// Real app transport, ReferenceWorkspace, ContextHistory and TimberEdit module.
// DOM/HTTP ports are controlled here; this is not a browser/native receipt.
const assert = require('node:assert/strict');
const fs = require('node:fs'), vm = require('node:vm');
const {fixture, prepare} = require('../fixtures/evidence_adoption_host.cjs');

function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return {promise, resolve};
}

function host({delayPreview = false, previewFailure = null,
  cancelResult = {ok:true,cancelled:true,revision:'7'}, cancelTransport = false,recoverCancelReceipt = false} = {}) {
  const cancelGate = deferred(), cancelStarted = deferred(), confirmGate = deferred(), confirmStarted = deferred();
  const previewGate = deferred(), previewStarted = deferred(), notices = [], draftGuards = [];
  let lease, token = 71, currentCancelResult = cancelResult, failTransport = cancelTransport, f;
  f = fixture({failedReceipts:cancelTransport && !recoverCancelReceipt ? 100 : 0,native:async command => {
    if (command === 'engineering-read') return {ok:true,state:{materials:[],specs:[],applications:[]}};
    if (command === 'timber-edit-cancel ' + token) {
      cancelStarted.resolve(); await cancelGate.promise;
      if (failTransport) throw TypeError('cancel response unavailable');
      return currentCancelResult;
    }
    if (/^(definition-import|engineering)-confirm 7$/.test(command)) {
      confirmStarted.resolve(); await confirmGate.promise; return f.receipt;
    }
    return {ok:true};
  }});
  const nodes = new Map(), patches = [], fields = [], controls = [];
  let visible = false, eligible = false;
  function element(id = '') {
    return {id,value:'',checked:false,disabled:false,hidden:false,dataset:{},textContent:'',parentElement:{hidden:false},
      classList:{toggle(){},contains(){return false;}},setAttribute(){},removeAttribute(){},replaceChildren(){},
      addEventListener(){},focus(){},contains(node){return nodes.get(node.id)===node;},closest(){return null;},
      querySelector(){return null;},querySelectorAll(){return [];}};
  }
  const get = id => {
    if (id === 'timberEditForm' && !visible) return null;
    if (!nodes.has(id)) nodes.set(id, element(id));
    return nodes.get(id);
  };
  const form = element('timberEditForm'); nodes.set(form.id, form);
  for (const name of ['A','B','role','priority','direction']) {
    const patch = element(); patch.dataset.timberPatch = name; patches.push(patch);
    const field = element(); field.dataset.timberField = name; field.querySelector = () => patch;
    const ids = ['A','B'].includes(name)
      ? ['Mode','Value','Source','OverrideMode','OverrideSource','OverrideValue'].map(suffix=>'timberEdit'+name+suffix)
      : [name === 'role' ? 'timberEditRole' : name === 'priority' ? 'timberEditPriority' : 'timberEditDirection'];
    const own = ids.map(get); controls.push(...own); field.querySelectorAll = () => own; fields.push(field);
  }
  form.querySelector = selector => selector === '[data-timber-patch]' ? patches[0] : null;
  form.querySelectorAll = selector => selector === '[data-timber-field]' ? (eligible ? fields : [])
    : selector === '[data-timber-patch]:checked' ? patches.filter(node=>node.checked)
      : selector === 'input,select' ? [...patches,...controls] : [];
  const pane = get('faceInspectorContent');
  Object.defineProperty(pane, 'innerHTML', {set(html) {
    visible = html.includes('id="timberEditForm"'); eligible = html.includes('data-timber-field');
    patches.forEach(node=>{node.checked=false;}); controls.forEach(node=>{node.value='';});
  }});
  const document = f.env.document;
  document.getElementById = get;
  document.body = {classList:{contains(){return false;}}};
  document.querySelector = selector => {
    const match = selector.match(/^\[data-timber-patch="([^"]+)"\]$/);
    return match ? patches.find(node=>node.dataset.timberPatch===match[1]) : null;
  };
  Object.assign(f.env, {ReferenceWorkspace:f.w,apiRequest:f.api,feSid:()=>0,
    fe:{timberSelection:new Set([42]),sel:{kind:'timber',id:42},tool:'select'},
    fiShowTab(){},openPanel(){},renderFaceInspector(){},timberDirectionName:value=>value,
    toast:message=>notices.push(message),FaceContextMenu:{refreshEligibility(){}}});
  Object.assign(f.env.oc, {edit:{bid:1},focus:{t:'face',id:1}});
  f.env.window.DraftGate = {register:guard=>draftGuards.push(guard)};
  const originalBegin = f.w.beginTimberPreview;
  f.w.beginTimberPreview = () => (lease = originalBegin());
  const row = {id:42,eligible:true,owner:null,groups:[],groupsKnown:true,placed:true,placementOrder:'1',
    definition:{A:{mode:'direct',value:27},B:{mode:'direct',value:33},role:'primary',priority:1,
      placement:{on:0,anchor:'at-face e0',selector:'',direction:'+u',side:'+n'}},effective:{A:27,B:33}};
  const originalFetch = f.env.fetch;
  f.env.fetch = async (url, options) => {
    if (url === '/api') {
      const response = await originalFetch(url, options);
      if (recoverCancelReceipt && JSON.parse(options.body).receipt)
        return {...response,json:async()=>({ok:true,result:currentCancelResult})};
      return response;
    }
    const body = JSON.parse(options.body); let result;
    if (url === '/timber-edit/read') {
      assert.deepEqual(body.timberIds,[42],'R356_PREFLIGHT_REAL_SELECTION');
      result = {ok:true,schema:'timber-edit-read-result/1',revision:'7',contextKey:'a'.repeat(64),
        boundaryId:1,maxOperations:64,eligible:true,reason:null,timbers:[row]};
    } else {
      assert.equal(url,'/timber-edit/preview'); previewStarted.resolve();
      if (delayPreview) await previewGate.promise;
      if (previewFailure === 'transport') throw TypeError('preview response lost after native creation');
      if (previewFailure === 'json') return {ok:true,status:200,headers:{get:()=> 'test-session'},json:async()=>{throw SyntaxError('truncated native response');}};
      result = {ok:true,preview:{schema:'timber-edit-preview-result/1',revision:'7',token,valid:true,noOp:false,
        before:[row],after:[{...row,definition:{...row.definition,role:'boundary'}}],violations:[],dependencies:[]}};
      if (previewFailure === 'malformed') delete result.preview.token;
      if (['rejected','missingSession'].includes(previewFailure)) result={ok:false,code:'STALE',error:'Timber definitions changed; read and preview again'};
      if (previewFailure === 'bridge') result={ok:false,error:'橋接器回應逾時，請重新啟動服務'};
    }
    const missingSession = url === '/timber-edit/preview' && ['missingSession','missingSuccessSession'].includes(previewFailure);
    return {ok:true,status:200,headers:{get:()=>missingSession ? null : 'test-session'},json:async()=>result};
  };
  vm.runInContext(fs.readFileSync(process.env.GEOMETRY_TEST_TIMBER_EDIT || require.resolve('../../geometry-web/timber-edit.js'),'utf8'),f.env,{filename:'actual-timber-edit.js'});
  const timber = f.env.window.TimberEdit;
  return {f,timber,cancelGate,cancelStarted,confirmGate,confirmStarted,previewGate,previewStarted,notices,draftGuards,
    lease:()=>lease,token,
    setCancel(result,transport=false){currentCancelResult=result;failTransport=transport;},
    async open(){await timber.openBatch();assert.equal(get('timberEditPreview').disabled,false,'R356_PREFLIGHT_BATCH_ELIGIBLE');},
    preview(){patches.find(node=>node.dataset.timberPatch==='role').checked=true;get('timberEditRole').value='boundary';return get('timberEditPreview').onclick();}};
}

async function idle() {
  for (const kind of ['definition-import','engineering']) {
    const h=host(),f=h.f; if(kind==='engineering')prepare(f);
    assert.equal(h.timber.beforeWorldMutation(),null,'R356_IDLE_PREFLIGHT_NO_PROMISE');
    const count=f.w.history.undo.length,pending=f.api(kind+'-confirm 7');
    assert.throws(()=>f.w.assertEditable(),/確認/,'R356_IDLE_MODULE_SYNC_CONFIRM_LEASE_'+kind);
    h.confirmGate.resolve();assert.equal((await pending).ok,true);
    assert.equal(f.w.history.undo.length,count+1,'R356_IDLE_MODULE_ONE_HISTORY_'+kind);
    assert.doesNotThrow(()=>f.w.assertEditable());
  }
  const h=host();await h.open();
  assert.equal(h.timber.beforeWorldMutation(),null,'R356_OPEN_IDLE_FORM_NO_PROMISE');
  assert.doesNotThrow(()=>h.f.w.assertEditable());
}

async function delayed({pendingPreview=false}={}) {
  const h=host({delayPreview:pendingPreview}),f=h.f;
  await h.open();const preview=h.preview();
  if(pendingPreview)await h.previewStarted.promise;else await preview;
  const original=f.w.finishTimberPreview,observations=[];
  f.w.finishTimberPreview=owner=>{
    original(owner);
    // Observe the next microtask after the real owner is released. The new
    // confirmation must already own the workspace in that same continuation.
    queueMicrotask(()=>{let blocked=false;try{f.w.assertEditable();}catch(_){blocked=true;}observations.push(blocked);});
  };
  const count=f.w.history.undo.length,context=f.w.context(),pending=f.api('definition-import-confirm 7');
  assert.throws(()=>f.w.assertEditable(),/候選|確認/,'R356_CANCEL_FIRST_AWAIT_LOCKED');
  assert.equal((await f.api('line boundary 9 outline 0,0 1,0 0,1')).ok,false,'R356_CANCEL_COMPETING_MUTATION_REFUSED');
  await assert.rejects(f.w.newProject(),/候選|確認/,'R356_CANCEL_PROJECT_SWITCH_REFUSED');
  if(pendingPreview){h.previewGate.resolve();}
  await h.cancelStarted.promise;
  const cancelRequest=f.requests.find(row=>row.cmd==='timber-edit-cancel 71');
  assert.equal(typeof cancelRequest.requestId,'string','R356_CANCEL_HAS_RECORDED_REQUEST_ID');
  assert.equal(cancelRequest.session,'test-session','R356_CANCEL_HAS_ORIGINAL_SERVER_SESSION');
  assert.equal(f.requests.some(row=>row.cmd==='definition-import-confirm 7'),false,'R356_CANCEL_BEFORE_CONFIRM');
  assert.equal(f.w.history.undo.length,count,'R356_CANCEL_HAS_NO_HISTORY');
  h.cancelGate.resolve();await h.confirmStarted.promise;
  assert.throws(()=>f.w.assertEditable(),/確認/,'R356_CANCEL_HANDOFF_CONFIRM_LEASE');
  assert.deepEqual(observations,[true],'R356_CANCEL_HANDOFF_NO_MICROTASK_GAP');
  h.confirmGate.resolve();assert.equal((await pending).ok,true);await preview;
  assert.equal(f.w.context(),context,'R356_CANCEL_OWNER_UNCHANGED');
  assert.equal(f.w.history.undo.length,count+1,'R356_CANCEL_ONE_HISTORY');
  assert.deepEqual(f.requests.filter(row=>row.cmd?.startsWith('line boundary')),[],'R356_CANCEL_NO_COMPETING_HTTP');
  assert.equal(f.requests.filter(row=>row.cmd==='timber-edit-cancel 71').length,1,'R356_CANCEL_EXACTLY_ONCE');
  assert.doesNotThrow(()=>f.w.assertEditable());
}

async function failure(transport=false) {
  const h=host({cancelResult:{ok:false,error:'CANCEL_REJECTED'},cancelTransport:transport}),f=h.f;
  await h.open();await h.preview();const lease=h.lease(),count=f.w.history.undo.length;
  const pending=f.api('definition-import-confirm 7');h.cancelGate.resolve();h.confirmGate.resolve();
  assert.equal((await pending).ok,false,'R356_CANCEL_FAILURE_REFUSES_MUTATION');
  assert.equal(f.requests.some(row=>row.cmd==='definition-import-confirm 7'),false,'R356_CANCEL_FAILURE_NO_CONFIRM_HTTP');
  assert.equal(f.w.history.undo.length,count,'R356_CANCEL_FAILURE_HISTORY_UNCHANGED');
  assert.throws(()=>f.w.assertEditable(),/候選|確認/,transport?'R356_CANCEL_TRANSPORT_RETAINS_LEASE':'R356_CANCEL_REJECTION_RETAINS_LEASE');
  assert.doesNotThrow(()=>f.w.assertTimberPreview(lease,h.token),'R356_CANCEL_FAILURE_RETAINS_SAME_TOKEN_OWNER');
  assert.equal(h.draftGuards.every(guard=>guard()),false,'R356_CANCEL_FAILURE_DRAFT_GATE_REFUSED');
  await assert.rejects(f.w.newProject(),/候選|確認/,'R356_CANCEL_FAILURE_PROJECT_SWITCH_REFUSED');
  // A later explicit retry uses the retained token. No failed attempt silently
  // turns into a confirmation or substitutes another candidate.
  h.setCancel({ok:true,cancelled:false,revision:'7'});f.transport.connection.phase='ready';
  const retry=f.api('definition-import-confirm 7');
  assert.equal((await retry).ok,true,'R356_CANCEL_RETRY_CAN_COMPLETE');
  assert.deepEqual(f.requests.filter(row=>row.cmd?.startsWith('timber-edit-cancel ')).map(row=>row.cmd),
    ['timber-edit-cancel 71','timber-edit-cancel 71'],'R356_CANCEL_RETRY_SAME_TOKEN');
  assert.equal(f.w.history.undo.length,count+1);assert.doesNotThrow(()=>f.w.assertEditable());
}

async function replacedOwner() {
  const h=host(),f=h.f;await h.open();await h.preview();
  const pending=f.api('definition-import-confirm 7');await h.cancelStarted.promise;
  // Recovery/external-replacement fault injection bypasses normal UI gates;
  // a successful cancellation must still retire the old queued command.
  f.w.history.replace(f.w.history.makeContext(),[],'external owner replacement');
  const count=f.w.history.undo.length;h.cancelGate.resolve();h.confirmGate.resolve();
  assert.equal((await pending).ok,false,'R356_CANCEL_REPLACED_OWNER_RETIRES_COMMAND');
  assert.equal(f.requests.some(row=>row.cmd==='definition-import-confirm 7'),false,'R356_CANCEL_REPLACED_OWNER_NO_HTTP');
  assert.equal(f.w.history.undo.length,count,'R356_CANCEL_REPLACED_OWNER_NO_HISTORY');
  assert.doesNotThrow(()=>f.w.assertEditable());
}

async function unknownPreview(reason) {
  const h=host({delayPreview:true,previewFailure:reason}),f=h.f;await h.open();
  const preview=h.preview();await h.previewStarted.promise;
  const count=f.w.history.undo.length,pending=f.api('definition-import-confirm 7');
  assert.throws(()=>f.w.assertEditable(),/候選|確認/,'R356_UNKNOWN_PREVIEW_FIRST_AWAIT_LOCKED');
  h.previewGate.resolve();h.cancelGate.resolve();h.confirmGate.resolve();
  assert.equal((await pending).ok,false,'R356_UNKNOWN_PREVIEW_REFUSES_MUTATION_'+reason);await preview;
  assert.equal(f.requests.some(row=>/^(definition-import-confirm|timber-edit-cancel) /.test(row.cmd)),false,'R356_UNKNOWN_PREVIEW_NEVER_GUESSES_TOKEN');
  assert.equal(f.w.history.undo.length,count,'R356_UNKNOWN_PREVIEW_HISTORY_UNCHANGED');
  assert.throws(()=>f.w.assertEditable(),/候選|確認/,'R356_UNKNOWN_PREVIEW_RETAINS_LEASE');
  assert.equal((await f.api('line reset')).ok,false,'R356_UNKNOWN_PREVIEW_RETRY_STILL_BLOCKED');
  assert.equal(f.requests.some(row=>row.cmd==='line reset'),false,'R356_UNKNOWN_PREVIEW_NO_RETRY_HTTP');
  await assert.rejects(f.w.newProject(),/候選|確認/,'R356_UNKNOWN_PREVIEW_PROJECT_SWITCH_REFUSED');
}

async function knownRejection() {
  const h=host({previewFailure:'rejected'}),f=h.f;await h.open();const count=f.w.history.undo.length;
  await h.preview();assert.doesNotThrow(()=>f.w.assertEditable(),'R356_KNOWN_PREVIEW_REJECTION_RELEASES_OWNER');
  const pending=f.api('definition-import-confirm 7');h.confirmGate.resolve();
  assert.equal((await pending).ok,true,'R356_KNOWN_PREVIEW_REJECTION_PERMITS_LATER_COMMAND');
  assert.equal(f.w.history.undo.length,count+1);
}

async function changedSession() {
  const h=host(),f=h.f;await h.open();await h.preview();
  f.transport.connection.session='replacement-session';
  const pending=f.api('definition-import-confirm 7');h.cancelGate.resolve();h.confirmGate.resolve();
  assert.equal((await pending).ok,false,'R356_CHANGED_SESSION_RETIRES_OLD_COMMAND');
  assert.equal(f.requests.some(row=>row.cmd==='timber-edit-cancel 71'),false,'R356_OLD_CANCEL_TOKEN_NEVER_SENT_TO_NEW_SESSION');
  assert.equal(f.requests.some(row=>row.cmd==='definition-import-confirm 7'),false,'R356_CHANGED_SESSION_NO_CONFIRM_HTTP');
  assert.throws(()=>f.w.assertEditable(),/候選|確認/,'R356_CHANGED_SESSION_RETAINS_OWNER');
}

async function recoveredCancellation() {
  const h=host({cancelTransport:true,recoverCancelReceipt:true}),f=h.f;await h.open();await h.preview();
  const count=f.w.history.undo.length,pending=f.api('definition-import-confirm 7');
  assert.throws(()=>f.w.assertEditable(),/候選|確認/,'R356_CANCEL_LOST_RESPONSE_FIRST_AWAIT_LOCKED');
  h.cancelGate.resolve();h.confirmGate.resolve();
  assert.equal((await pending).ok,true,'R356_CANCEL_LOST_RESPONSE_RECOVERED');
  const cancellations=f.requests.filter(row=>row.cmd==='timber-edit-cancel 71');
  assert.equal(cancellations.length,1,'R356_CANCEL_LOST_RESPONSE_NOT_RESENT');
  assert.deepEqual(f.requests.filter(row=>row.receipt).map(row=>row.receipt),
    [cancellations[0].requestId],'R356_CANCEL_RECOVERS_EXACT_RECEIPT');
  assert.equal(f.transport.pending.size,0,'R356_CANCEL_RECOVERY_CLEARS_UNKNOWN_RESULT');
  assert.equal(f.w.history.undo.length,count+1,'R356_CANCEL_RECOVERY_ONE_CONFIRM_HISTORY');
  assert.doesNotThrow(()=>f.w.assertEditable());
}

const cases={idle,delayed:()=>delayed(),pending:()=>delayed({pendingPreview:true}),rejection:()=>failure(),transport:()=>failure(true),replacedOwner,
  unknownTransport:()=>unknownPreview('transport'),unknownJson:()=>unknownPreview('json'),unknownMalformed:()=>unknownPreview('malformed'),unknownBridge:()=>unknownPreview('bridge'),
  missingSession:()=>unknownPreview('missingSession'),missingSuccessSession:()=>unknownPreview('missingSuccessSession'),knownRejection,changedSession,recoveredCancellation};
async function exercise(names=Object.keys(cases)) {
  for(const name of names){assert.ok(cases[name],'known preflight case');await cases[name]();}
}
module.exports={exercise};
if(require.main===module){
  let completed=false;
  process.once('beforeExit',()=>{if(!completed){console.error('R356_PREFLIGHT_INCOMPLETE');process.exitCode=2;}});
  exercise(process.argv.slice(2).length?process.argv.slice(2):undefined)
    .then(()=>{completed=true;console.log('R356_PREFLIGHT_PASS');},error=>{completed=true;console.error(error);process.exitCode=1;});
}
