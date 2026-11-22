/* R433 fragment migration T. Node/VM contracts only: no Chrome, trusted input,
 * section measurement, or browser 0/1/0 is claimed by this test. */
'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');
const ROOT = path.resolve(__dirname, '../..');
const MODULE = 'geometry-web/canvas_sections/P1162.js';
const registry = require(path.join(ROOT, 'geometry-web/canvas_registry.js'));
const sourcePath = path.resolve(process.env.R433_FRAGMENT_SOURCE || path.join(ROOT, MODULE));
const readModule = () => fs.readFileSync(sourcePath, 'utf8');
const sha256 = raw => crypto.createHash('sha256').update(raw).digest('hex');
const blob = raw => crypto.createHash('sha1').update('blob '+raw.length+'\0').update(raw).digest('hex');
const EXPECTED_CASES = ['LONG_PRESS','BLANK_EQUIVALENCE','SHEET_KEYBOARD','SHORT_VIEWPORT','DISABLED_REASON','VIEW_ACTION_FOCUS',
  'TAP','DOUBLE_TAP','DRAG','CARD_SECOND_TOUCH','TWO_FINGERS','RECT_CANCEL','CANCEL','ESCAPE','STALE_OWNER','STALE_NODE'];

test('the shared dispatcher is exactly main and the retired touch driver is absent', () => {
  // Exact main 883e68688f6480a5f1de6e86e6a056cc20339cb9 bytes, not a relaxed
  // token inventory that could miss the old early-observer preload insertion.
  assert.equal(blob(fs.readFileSync(path.join(ROOT, 'geometry-web/cdp_test.js'))),
    'a38b088e1e7a7ddab04d665f5d3bc1cbc28968ac', 'R433_DISPATCHER_MAIN_BYTES');
  assert.equal(fs.existsSync(path.join(ROOT, 'geometry-web/canvas_touch_test.js')), false, 'R433_RETIRED_TOUCH_DRIVER');
});

test('P1162 uses the existing strict module dependency checker', () => {
  const source = readModule();
  assert.match(source, /module\.exports = async helpers => \{/, 'R433_STRICT_ASYNC_MODULE');
  const closure = registry.sourceClosure(ROOT, [MODULE], {strict:true});
  assert.deepEqual(Object.keys(closure.files), [MODULE, 'geometry-web/cdp_navigation.js'], 'R433_MINIMAL_PURE_CLOSURE');
  assert.equal(closure.files[MODULE], sha256(source), 'R433_MODULE_SOURCE_EXACT');
});

test('all sixteen cases, their fixture, assertions and timing remain exact', () => {
  const source = readModule();
  const start = source.indexOf('  async function state() {');
  const end = source.indexOf('  const actions = ', start);
  assert.ok(start >= 0 && end > start, 'R433_CASE_BODY_BOUNDARIES');
  const body = Buffer.from(source.slice(start, end));
  // Independently taken from the fixed 82b7b765 base, covering fixture(), all
  // gesture/timing helpers and all sixteen case bodies. This is not a count.
  assert.equal(body.length, 40079, 'R433_ORIGINAL_CASE_BYTES');
  assert.equal(sha256(body), 'd85a89046c69b296b8d97aa05872bef9410fc560da99f05a7590eb28457d0532',
    'R433_ORIGINAL_ASSERTIONS_AND_THRESHOLDS');
  const declarations = source.slice(source.indexOf('const FIXTURE = ['), source.indexOf('// Installed by Page.'));
  const observed = vm.runInNewContext(declarations+'\nJSON.stringify({FIXTURE,CASES})');
  assert.deepEqual(JSON.parse(observed), {FIXTURE:[
    'boundary 41 outline 0,0 1000,0 1000,800 0,800', 'canvas-pos boundary 41 80 100',
    'boundary 42 outline 0,0 1200,0 1200,900 0,900', 'canvas-pos boundary 42 400 100',
    'boundary 43 outline 0,0 900,0 900,700 0,700', 'canvas-pos boundary 43 80 400'
  ], CASES:EXPECTED_CASES}, 'R433_SELF_CONTAINED_FIXTURE_AND_CASES');
});

function storage(rows) {
  const store = {...rows};
  Object.defineProperties(store, {
    getItem:{value:key=>Object.hasOwn(store,key)?store[key]:null},
    setItem:{value:(key,value)=>{store[key]=String(value);}},
    clear:{value:()=>{for(const key of Object.keys(store))delete store[key];}}
  });
  return store;
}

test('module reload observes a new document and cleans up on a probe failure', async () => {
  const execute = require(sourcePath);
  const sentinel = 'R433_STOP_BEFORE_CHROME_CASES';
  const local = storage({baseline:'local-before'}), session = storage({baseline:'session-before'});
  const expected = {local:{baseline:'local-before'},session:{baseline:'session-before'}};
  let context, registered = null, oldDocumentChecks = 0, fresh = false, probeReached = false, added = 0, removed = 0;
  const protocol = [];
  function makeDocument(loading) {
    const listeners = [];
    const window = {
      addEventListener:(...row)=>{listeners.push(row);added++;},
      removeEventListener:(...row)=>{
        const index = listeners.findIndex(entry=>entry.every((value,j)=>value===row[j]));
        assert.notEqual(index,-1,'R433_REMOVE_EXACT_LISTENER');listeners.splice(index,1);removed++;
      }
    };
    window.window = window;
    return vm.createContext({window,document:{readyState:loading?'loading':'complete'},localStorage:local,sessionStorage:session,
      WeakMap,Map,performance,requestAnimationFrame:callback=>callback(),
      CanvasContextMenu:{hide(){}},FaceContextMenu:{hide(){}},setOcTool(){},closeDialogs(){},closeMenus(){},closePanels(){}});
  }
  function productReady(c) {
    vm.runInContext("var api=()=>{};var oc={};var objectTouchOwner=()=>{};var ReferenceWorkspace={};var connection={phase:'ready'};document.readyState='complete';",c);
  }
  context = makeDocument(false); productReady(context);
  const helpers = {
    exceptionCount:()=>0,makeCheck:()=>()=>{},waitForUI:async()=>{},
    send:async(method,params)=>{
      protocol.push(method);
      if(method==='Page.addScriptToEvaluateOnNewDocument'){
        assert.equal(registered,null,'R433_ONE_PRELOAD');registered=params.source;return {result:{identifier:'p1162-owned-preload'}};
      }
      if(method==='Page.reload'){
        assert.equal(typeof registered,'string','R433_PRELOAD_BEFORE_RELOAD');return {result:{}};
      }
      if(method==='Page.removeScriptToEvaluateOnNewDocument'){
        assert.equal(params.identifier,'p1162-owned-preload','R433_REMOVE_OWN_PRELOAD');registered=null;
      }
      return {result:{}};
    },
    eval_:async source=>{
      if(source.startsWith('window.__cdpExpectedNavigationMarker === ')){
        assert.ok(protocol.includes('Page.reload'),'R433_RELOAD_BEFORE_MARKER_BARRIER');
        if(!fresh){
          oldDocumentChecks++;
          assert.equal(vm.runInContext(source,context),false,'R433_OLD_READY_DOCUMENT_REJECTED');
          context=makeDocument(true);vm.runInContext(registered,context);
          assert.equal(context.window.__p1162Early.beforeProduct,true,'R433_OBSERVER_BEFORE_PRODUCT');
          productReady(context);fresh=true;local.dirty='created-by-module';session.dirty='created-by-module';
          return false;
        }
        return vm.runInContext(source,context);
      }
      if(source.startsWith('(function installProbe()')){
        assert.equal(fresh,true,'R433_FRESH_DOCUMENT_BEFORE_PROBE');
        assert.equal(registered,null,'R433_PRELOAD_REMOVED_BEFORE_CASES');probeReached=true;
        throw Error(sentinel);
      }
      return vm.runInContext(source,context);
    }
  };
  await assert.rejects(registry.runSlotIsolation(helpers,()=>execute(helpers)),new RegExp(sentinel));
  assert.equal(oldDocumentChecks,1,'R433_FRESH_MARKER_EXERCISED');
  assert.equal(probeReached,true,'R433_BOOTSTRAP_REACHES_PROBE');
  assert.deepEqual(protocol.slice(0,3),['Page.addScriptToEvaluateOnNewDocument','Page.reload','Page.removeScriptToEvaluateOnNewDocument']);
  assert.equal(added,16,'R433_ALL_EARLY_LISTENERS_INSTALLED');
  assert.equal(removed,16,'R433_ALL_EARLY_LISTENERS_REMOVED');
  assert.equal(context.window.__p1162Early,undefined,'R433_EARLY_STATE_REMOVED');
  assert.equal(context.window.__cdpExpectedNavigationMarker,undefined,'R433_MARKER_REMOVED');
  const snapshot=JSON.parse(JSON.stringify(await helpers.eval_(registry.STORAGE_EXPRESSION)));
  assert.deepEqual(snapshot,expected,'R433_BOTH_STORAGE_RESTORED_AFTER_NEW_DOCUMENT_FAILURE');
});
