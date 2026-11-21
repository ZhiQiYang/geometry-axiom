'use strict';
// Execute the shipped transaction and placement functions. Native replies and
// DOM state below are finite fixtures; real pointer/keyboard/layout need CDP.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(process.env.GEOMETRY_FACE_REFERENCE_SOURCE||path.join(__dirname,'../geometry-web/app.js'),'utf8');
function between(text,start,end){const i=text.indexOf(start),j=text.indexOf(end,i);assert.ok(i>=0&&j>i,'production function boundary exists');return text.slice(i,j);}
const mutateSource=between(source,'async function mutate(lines, opts) {','/* 快速六面盒對話框');
const placementSource=between(source,'function faceReferenceOperation(bid,inputIds) {','/* ---- GEO-190/198:');
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};}
function classes(){const values=new Set();return {values,add:value=>values.add(value),remove:value=>values.delete(value),contains:value=>values.has(value)};}
function transactionHarness({rejectCommand=null,throwCommand=null,sourceText=mutateSource}={}){
  const calls=[],notices=[],timers=new Map(),body={classList:classes()},trigger={classList:classes()},indicator={hidden:true};
  const oc={busy:false};let timerId=0,commits=0,aborts=0;
  const sandbox={oc,document:{body,activeElement:{closest:()=>trigger}},$:id=>id==='busyIndicator'?indicator:null,
    setTimeout:fn=>{const id=++timerId;timers.set(id,fn);return id;},clearTimeout:id=>timers.delete(id),
    toast:message=>notices.push(message),api:async command=>{
      calls.push(command);
      if(command===throwCommand)throw new Error('native transport exploded');
      if(command===rejectCommand)return {ok:false,error:'native rejected'};
      if(command==='line history-end')commits++;
      if(command==='line history-abort')aborts++;
      return {ok:true};
    }};
  vm.runInNewContext(sourceText,sandbox,{filename:'mutate.production.js'});
  return {mutate:sandbox.mutate,oc,body,trigger,indicator,calls,notices,timers,
    get commits(){return commits;},get aborts(){return aborts;},tick:()=>{for(const fn of timers.values())fn();}};
}
function busy(h){assert.equal(h.oc.busy,true);assert.equal(h.body.classList.contains('oc-busy'),true);assert.equal(h.trigger.classList.contains('is-busy'),true);}
function released(h){assert.equal(h.oc.busy,false);assert.equal(h.body.classList.contains('oc-busy'),false);assert.equal(h.trigger.classList.contains('is-busy'),false);assert.equal(h.indicator.hidden,true);assert.equal(h.timers.size,0);}
async function reachedSettlement(h,pending,gate){
  await Promise.race([gate.promise,pending.then(()=>{throw Error('transaction returned before its settlement callback');})]);busy(h);
}
for(const accepted of [true,false])test(`native ${accepted?'commit':'rejection'} keeps busy until held settlement finishes and rejects a second transaction`,async()=>{
  const h=transactionHarness({rejectCommand:accepted?null:'line second'}),entered=deferred(),release=deferred(),states=[];
  let finished=false;
  const pending=h.mutate(['first','second'],{afterSettlement:async committed=>{states.push(committed);entered.resolve();await release.promise;busy(h);}});
  pending.then(()=>{finished=true;},()=>{finished=true;});
  try{
    await reachedSettlement(h,pending,entered);assert.deepEqual(states,[accepted]);assert.equal(finished,false);
    const commands=[...h.calls];assert.equal(await h.mutate(['must-not-dispatch']),false);assert.deepEqual(h.calls,commands);
    h.tick();assert.equal(h.indicator.hidden,false,'long settlement retains the actual busy indicator');
    assert.equal(h.commits,accepted?1:0);assert.equal(h.aborts,accepted?0:1);
  }finally{release.resolve();}
  assert.equal(await pending,accepted);released(h);
  assert.deepEqual(h.calls,accepted?['line history-begin','line first','line second','line history-end']:['line history-begin','line first','line second','line history-abort']);
});
for(const accepted of [true,false])for(const asynchronous of [false,true])test(`${accepted?'committed':'rejected'} transaction releases every busy resource when settlement ${asynchronous?'rejects':'throws'}`,async()=>{
  const h=transactionHarness({rejectCommand:accepted?null:'line first'}),error=new Error('refresh failed');let called=0;
  const fail=committed=>{called++;assert.equal(committed,accepted);busy(h);h.tick();throw error;};
  await assert.rejects(h.mutate(['first'],{afterSettlement:asynchronous?async committed=>fail(committed):fail}),e=>e===error);
  assert.equal(called,1);released(h);assert.equal(h.commits,accepted?1:0);assert.equal(h.aborts,accepted?0:1,'display failure cannot abort an already committed native transaction');
  assert.equal(await h.mutate(['recovery']),true,'cleanup makes the next independent operation available');released(h);
});
test('an existing busy owner is never cleaned or settled by an early rejected entrant',async()=>{
  const h=transactionHarness();h.oc.busy=true;h.body.classList.add('oc-busy');h.trigger.classList.add('is-busy');h.indicator.hidden=false;
  let called=0;assert.equal(await h.mutate(['forbidden'],{afterSettlement:()=>called++}),false);
  busy(h);assert.equal(h.indicator.hidden,false);assert.equal(called,0);assert.deepEqual(h.calls,[]);
});
test('a stale preflight returns before acquiring busy, native history or settlement',async()=>{
  const h=transactionHarness();let called=0;
  assert.equal(await h.mutate(['forbidden'],{operation:{current:()=>false},afterSettlement:()=>called++}),false);
  assert.equal(called,0);assert.deepEqual(h.calls,[]);released(h);
});
test('native throw settles as uncommitted after its original abort and preserves the native error',async()=>{
  const h=transactionHarness({throwCommand:'line first'}),states=[];
  await assert.rejects(h.mutate(['first'],{afterSettlement:committed=>{busy(h);states.push(committed);}}),/native transport exploded/);
  assert.deepEqual(states,[false]);assert.equal(h.commits,0);assert.equal(h.aborts,1);released(h);
});
test('history-end rejection never reports a committed settlement',async()=>{
  const h=transactionHarness({rejectCommand:'line history-end'}),states=[];
  assert.equal(await h.mutate(['first'],{afterSettlement:committed=>{busy(h);states.push(committed);}}),false);
  assert.deepEqual(states,[false]);assert.equal(h.commits,0);released(h);
});
test('callers without settlement keep successful, rejected and thrown native command semantics',async()=>{
  for(const outcome of ['accepted','rejected','throw']){
    const h=transactionHarness({rejectCommand:outcome==='rejected'?'line second':null,throwCommand:outcome==='throw'?'line second':null});
    if(outcome==='throw')await assert.rejects(h.mutate(['first','second']),/native transport exploded/);
    else assert.equal(await h.mutate(['first','second']),outcome==='accepted');
    assert.deepEqual(h.calls,['line history-begin','line first','line second',outcome==='accepted'?'line history-end':'line history-abort']);released(h);
  }
});

function placementHarness({accepted=true,retireAt=null,changeRawAt=null,holdLoad=false}={}){
  const inputs=Object.fromEntries(Object.entries({tbA:'20',tbB:'30',tbAnchor:'at-face e0',tbSelector:'',tbDir:'+u',tbSide:'+n',tbRole:'primary',tbPri:'0'}).map(([id,value])=>[id,{value}]));
  inputs.faceInspectorContent={dataset:{}};
  let context={id:'original'},frame={},mark=0,loadCount=0;const calls=[],paints=[],events=[],entered=deferred(),release=deferred();
  const history={get frame(){return frame;},group:null};
  const oc={busy:false,edit:{bid:1},focus:{kind:'face',id:1}},fe={referenceRevision:7,timberReferenceData:{sourceFingerprint:'original-native'}};
  const retire=()=>{context={id:'replacement'};frame={};oc.edit={bid:2};oc.focus={kind:'face',id:2};};
  const rawChange=()=>{inputs.tbA.value='37';};
  const $=id=>inputs[id]||null;
  const sandbox={oc,fe,$,connection:{session:'session'},ReferenceWorkspace:{context:()=>context,history,getModelOperationState:()=>({revision:mark})},
    GridRuleLines:{parseAnchor:()=>null,parseExpression:()=>null,find:()=>null,reloadNative:async(load,isCurrent)=>{events.push('guarded-reload');if(isCurrent())await load();}},
    feSid:()=>2,feSurf:()=>({id:2}),feTimberSuggestion:()=>null,toast:message=>events.push(['toast',message]),feMarkInvalid:()=>{},feTimberPlaceErrorMessage:message=>message,
    api:async command=>{calls.push(command);return {ok:true,timber:8};},apiRequest:async command=>{calls.push(command);return {ok:true,revision:7,sourceFingerprint:'original-native'};},
    feLoadGuides:async()=>{loadCount++;events.push(['load',oc.busy,context.id]);if(changeRawAt==='load')rawChange();if(retireAt==='load')retire();entered.resolve();if(holdLoad)await release.promise;},
    drawFaceEditor:()=>paints.push(['draw',oc.busy,context.id]),renderFaceLayers:()=>paints.push(['layers',oc.busy,context.id]),renderFaceInspector:()=>paints.push(['inspector',oc.busy,context.id]),
    // This host port supplies a terminal outcome to the placement function.
    // Transaction ordering/abort/cleanup use the real mutate closure above.
    mutate:async(lines,options)=>{events.push(['transaction',Array.from(lines)]);oc.busy=true;mark++;
      if(retireAt==='settlement')retire();if(changeRawAt==='settlement')rawChange();
      try{await options.afterSettlement?.(accepted);}finally{oc.busy=false;}return accepted;},
  };
  vm.runInNewContext(placementSource,sandbox,{filename:'face-reference-placement.production.js'});
  return {place:sandbox.fePlaceTimberFromForm,oc,fe,inputs,calls,paints,events,entered:entered.promise,release:()=>release.resolve(),retire,
    get loads(){return loadCount;}};
}
test('a busy placement returns before allocating an ID or checking the half-loaded native cache',async()=>{
  const h=placementHarness();h.oc.busy=true;h.fe.timberReferenceData=null;
  assert.equal(await h.place(1),false);assert.deepEqual(h.calls,[]);assert.equal(h.loads,0);assert.deepEqual(h.events,[]);assert.equal(h.oc.busy,true);
});
for(const accepted of [true,false])test(`placement ${accepted?'success':'rejection'} reloads inside settlement and releases before any normal repaint`,async()=>{
  const h=placementHarness({accepted,holdLoad:true}),pending=h.place(1);
  try{await Promise.race([h.entered,pending.then(()=>{throw Error('placement finished without native cache reload');})]);assert.equal(h.oc.busy,true);assert.deepEqual(h.paints,[]);
    assert.equal(await h.place(1),false,'busy entry rejects a keyboard/programmatic duplicate');assert.equal(h.calls.filter(c=>c==='newid').length,1);
  }finally{h.release();}
  assert.equal(await pending,accepted);assert.equal(h.oc.busy,false);assert.equal(h.loads,1);
  assert.deepEqual(h.events.filter(e=>Array.isArray(e)&&e[0]==='load'),[['load',true,'original']]);
  assert.deepEqual(h.paints,accepted?[['draw',false,'original'],['layers',false,'original'],['inspector',false,'original']]:[]);
});
for(const accepted of [true,false])test(`retired presentation prevents a ${accepted?'committed':'rejected'} old operation from loading or painting the replacement face`,async()=>{
  const h=placementHarness({accepted,retireAt:'settlement'});await h.place(1);
  assert.equal(h.loads,0);assert.deepEqual(h.paints,[]);assert.equal(h.oc.edit.bid,2);assert.equal(h.oc.busy,false);
});
test('same-face raw edits during successful cache loading survive without late inspector replacement',async()=>{
  const h=placementHarness({changeRawAt:'load'});await h.place(1);
  assert.equal(h.loads,1);assert.equal(h.inputs.tbA.value,'37');assert.deepEqual(h.paints,[]);assert.equal(h.oc.busy,false);
});
test('a presentation retired during a held successful read receives no late rendering',async()=>{
  const h=placementHarness({holdLoad:true}),pending=h.place(1);
  try{await h.entered;h.retire();}finally{h.release();}await pending;
  assert.equal(h.loads,1);assert.deepEqual(h.paints,[]);assert.equal(h.oc.edit.bid,2);assert.equal(h.oc.busy,false);
});

/* ---- 面內角材列的三個顯示面回歸（2026-11-16 雲端實機核對 D04／D16 的發現 10～12）----
 * 執行 app.js 裡實際的函式本文（從原始碼取出、在 vm 裡跑）並核對 app.css 的規則文字；不跑瀏覽器、不跑原生幾何。
 * 滑鼠實際點得到與否由核對紀錄（evidence/l4-cloud-20261116）的瀏覽器腳本另外量。 */
{
  const web = path.join(__dirname, '..', 'geometry-web');
  const app = fs.readFileSync(path.join(web, 'app.js'), 'utf8'), css = fs.readFileSync(path.join(web, 'app.css'), 'utf8');

  /* 取出一個頂層 function 的完整本文（以大括號配對；這幾個函式裡沒有不成對的括號字元）。 */
  function source(name) {
    const start = app.indexOf(`\nfunction ${name}(`);
    assert.notEqual(start, -1, `${name} 不在 app.js`);
    assert.equal(app.indexOf(`\nfunction ${name}(`, start + 1), -1, `${name} 定義了不只一次`);
    let depth = 0;
    for (let i = app.indexOf('{', start); i < app.length; i++) {
      if (app[i] === '{') depth++;
      else if (app[i] === '}' && --depth === 0) return app.slice(start + 1, i + 1);
    }
    assert.fail(`${name} 的括號沒有配對`);
  }
  function load(names, globals) {
    const context = vm.createContext({ ...globals });
    vm.runInContext(names.map(source).join('\n') + `\nthis.api={${names.join(',')}};`, context);
    return context.api;
  }
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  test('料單列與圖層列一樣，滑鼠移上去或鍵盤聚焦時才露出刪除鈕', () => {
    const block = css.match(/@media \(hover: hover\) and \(pointer: fine\) \{\s*\.face-layer-del \{ opacity: 0; pointer-events: none; \}([\s\S]*?)\n\}/);
    assert.ok(block, '找不到「可懸停的裝置上先隱藏刪除鈕」那一段');
    const reveal = block[1].match(/:is\(([^)]*)\):(hover|focus-within) \.face-layer-del/g) || [];
    assert.equal(reveal.length, 2, '露出規則應該有 :hover 與 :focus-within 兩條');
    for (const rule of reveal) {
      const rows = rule.match(/:is\(([^)]*)\)/)[1].split(',').map(s => s.trim());
      for (const row of ['.face-layer-row', '.fl-row', '.space-boundary-button', '.timber-schedule-row'])
        assert.ok(rows.includes(row), `${rule} 沒有包含 ${row}`);
    }
    assert.match(block[1], /\.face-layer-del:focus-visible \{ opacity: 1; pointer-events: auto; \}/);
    // 料單列確實帶著這顆鈕（否則上面的規則沒有對象）
    assert.match(app, /r\.className = "timber-schedule-row"/);
    assert.match(app, /del\.className = "face-layer-del"; del\.title = `刪除角材 \$\{t2\.id\}`/);
  });

  test('圖層清單的角材列寫出定位引用的名稱，取自 timber.definition.anchor', () => {
    const entries = [
      { value: 'at-face e0', label: '外輪廓邊 0', occupied: 90 },
      { value: 'at-line guide 1', label: '參考線 1 · 沿 v · u=500 mm', occupied: 1 },
      { value: 'at-line guide 2', label: '參考線 2 · <主支>&"中線"', occupied: null },
    ];
    const seen = [];
    const { feTimberLayerSub } = load(['feTimberAnchorLabel', 'feTimberLayerSub'], {
      referenceAnchorEntries: (bid, surf) => { seen.push([bid, surf]); return entries; },
      ReferenceWorkspace: { escape },
    });
    assert.equal(feTimberLayerSub(7, 3, { id: 90, definition: { anchor: 'at-face e0' } }), '定位 外輪廓邊 0');
    assert.equal(feTimberLayerSub(7, 3, { id: 1, definition: { anchor: 'at-line guide 1' } }), '定位 參考線 1 · 沿 v · u=500 mm');
    assert.deepEqual(seen, [[7, 3], [7, 3]], '要用這一面與它的承載面查名稱');
    // 清單列用 innerHTML 組：名稱裡的符號要跳脫
    assert.equal(feTimberLayerSub(7, 3, { id: 2, definition: { anchor: 'at-line guide 2' } }), '定位 參考線 2 · &lt;主支&gt;&amp;&quot;中線&quot;');
    // 對照表裡沒有的引用式照原文顯示（同樣跳脫）；沒有定義時才是「—」
    assert.equal(feTimberLayerSub(7, 3, { id: 3, definition: { anchor: 'at-face t<9>' } }), '定位 at-face t&lt;9&gt;');
    assert.equal(feTimberLayerSub(7, 3, { id: 4 }), '定位 —');
    assert.equal(feTimberLayerSub(7, 3, { id: 5, definition: { anchor: '' } }), '定位 —');
    // 清單真的用這個函式，而且不再讀角材列上不存在的 anchor 欄位
    assert.match(app, /row\(icon\('timber'\),`角材 \$\{timber\.id\}`,feTimberLayerSub\(e\.bid,feSurf\(e\.bid\),timber\),/);
    assert.doesNotMatch(app, /timber\.anchor\s*\|\|/);
  });

  test('浮動列和左上角的選取提示重疊時移到提示下方，沒有重疊時不動', () => {
    const { feBarClearOfSummary } = load(['feBarClearOfSummary'], {});
    const summary = { left: 12, right: 245, top: 12, bottom: 74 }, W = 142, H = 36;
    // 放大後：浮動列被夾在視窗上緣（中心 y=24），整條在提示底下 → 移到提示下方 6 px
    assert.equal(feBarClearOfSummary(150, 24, W, H, summary), 74 + H / 2 + 6);
    // 顯示全部時只壓到幾個像素也算重疊
    assert.equal(feBarClearOfSummary(150, 86, W, H, summary), 98);
    // 移過之後不再重疊，再算一次位置不變
    assert.equal(feBarClearOfSummary(150, 98, W, H, summary), 98);
    // 水平方向沒有碰到提示（提示右緣 245；浮動列左緣 = 中心 - 71）
    assert.equal(feBarClearOfSummary(245 + 71, 24, W, H, summary), 24);
    assert.equal(feBarClearOfSummary(245 + 70, 24, W, H, summary), 98);
    // 垂直方向剛好貼齊不算重疊
    assert.equal(feBarClearOfSummary(150, 74 + H / 2, W, H, summary), 74 + H / 2);
    // 沒有提示（隱藏或不在畫面上）時不動
    assert.equal(feBarClearOfSummary(150, 24, W, H, null), 24);
  });

  test('擺放浮動列時先夾在視窗內，再避開選取提示；提示不可見時不避', () => {
    const calls = [], style = {};
    const viewport = { getBoundingClientRect: () => ({ left: 260, top: 56, width: 820, height: 812 }) };
    const bar = { hidden: false, style, offsetWidth: 142, offsetHeight: 36 };
    const summaryBox = { left: 272, right: 505, top: 68, bottom: 130, width: 233, height: 62 };
    const summary = { hidden: false, getBoundingClientRect: () => summaryBox };
    const elements = { feActionBar: bar, feOpPanel: { hidden: true }, faceEditorViewport: viewport, feSelectionSummary: summary };
    let anchor = { x: 42, y: -300 };
    const { fePlaceOverlays } = load(['fePlaceOverlays'], {
      window: {}, $: id => elements[id], feSelAnchor: () => anchor, Math,
      feBarClearOfSummary: (...args) => { calls.push(args); return 777; },
    });
    fePlaceOverlays();
    // x 夾在 150；y 先夾在 24；提示換成視窗內座標
    assert.deepEqual(JSON.parse(JSON.stringify(calls)), [[150, 24, 142, 36, { left: 12, right: 245, top: 12, bottom: 74 }]]);
    assert.deepEqual({ ...style }, { left: '150px', top: '777px' });
    // 提示被隱藏、或不在版面上（寬高為 0）時傳 null
    calls.length = 0; summary.hidden = true; fePlaceOverlays();
    assert.equal(calls[0][4], null);
    calls.length = 0; summary.hidden = false; Object.assign(summaryBox, { width: 0, height: 0 }); fePlaceOverlays();
    assert.equal(calls[0][4], null);
    // 沒有選取錨點時整條收起來，不去算位置
    calls.length = 0; anchor = null; fePlaceOverlays();
    assert.equal(calls.length, 0); assert.equal(bar.hidden, true);
  });
}
