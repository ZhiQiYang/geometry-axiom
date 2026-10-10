/* Exercise the actual app.js scheduler and pointer handlers without a bridge. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const nodeTest = require("node:test");
const source = fs.readFileSync(path.join(__dirname, "../geometry-web/app.js"), "utf8");
function between(start, end) {
  const i = source.indexOf(start), j = source.indexOf(end, i + start.length);
  assert(i >= 0 && j > i, `Missing source region: ${start}`);
  return source.slice(i, j);
}
function matching(pattern, end) {
  const found = pattern.exec(source);
  assert(found, `Missing source region: ${pattern}`);
  const i = found.index, j = source.indexOf(end, i + found[0].length);
  assert(j > i, `Missing source region: ${end}`);
  return source.slice(i, j);
}
function layer() {
  return { ops: [], dataset:{}, replaceChildren() {}, get textContent() { return this.text || ""; },
    set textContent(value) { this.text = value; this.ops = []; } };
}
function harness() {
  let nextFrame = 0, currentContext = {}, matrix = {a:1,b:0,c:0,d:1,e:0,f:0};
  const frames = new Map(), events = {}, windowEvents = {}, requests = [], calls = [];
  const history = {frame:{}, undo:[], group:null}, hoverInfo = layer(), pickInfo = layer();
  const svg = {isConnected:true, hidden:false, bounds:"0 0 100 100", hiddenParent:null,
    addEventListener(name, handler) { events[name] = handler; },
    hasAttribute(name) { return name === "hidden" && this.hidden; },
    setPointerCapture() {}, getAttribute() { return this.bounds; },
    getScreenCTM() { return matrix; }, closest() { return this.hiddenParent; }};
  const env = {
    requests, calls, svg, cv:svg, overlay:layer(), oc:{busy:false,on:false,focus:null,edit:null},
    fe:{projOpen:true}, connection:{phase:"ready",session:"session"},
    ReferenceWorkspace:{context:() => currentContext, history},
    selected:null, dragging:null, panning:null, layout:{}, zoom:1, panX:0, panY:0,
    tool:"view", hover:"", status:"", toasts:[], errors:[],
    console:{error(...args) { env.errors.push(args); }},
    requestAnimationFrame(fn) { const id = ++nextFrame; frames.set(id,fn); return id; },
    cancelAnimationFrame(id) { frames.delete(id); },
    api(cmd) {
      calls.push(cmd);
      if (cmd === "render") return Promise.resolve({ok:true,layout:{},ops:[]});
      if (!cmd.startsWith("pick ")) return Promise.resolve({ok:true});
      return new Promise((resolve, reject) => requests.push({cmd,resolve,reject}));
    },
    setHover(text) { env.hover = text; }, setStatus(text) { env.status = text; },
    toast(text) { env.toasts.push(text); },
    $(id) { return id === "v3HoverInfo" ? hoverInfo : pickInfo; },
    replay(ops, target) { target.ops.push(...ops); }, v3FixText() {}, transform:() => ({s:1}),
    world:layer(), v3FilterOps:ops=>ops, previewGs:[], affineCache:{},
    screenToView:(x,y) => x < 0 ? null : ({v:0,x,y,r:8}),
    applyTransform() {}, canvasMove() {}, canvasDown() {}, canvasUp() {}, render:async () => {},
    presentationCurrent() { return () => true; },
    /* Defined after the wheel listener, outside every extracted region. */
    retireCanvasGesture() { return null; },
    clearCanvasSelections() {}, GridEditor:{clear() {}}, ReferenceVisibility:{clear() {}},
    closePanels() {}, fiShowTab() {}, PolyDraft:{createState:()=>({})}, feSyncDraftMirror() {}, pendingSlot:null,
    document:{body:{classList:{add() {},remove() {},toggle() {}}}},
    window:{addEventListener(name, fn) { windowEvents[name] = fn; }}
  };
  vm.createContext(env);
  vm.runInContext(between("async function pickAt(sv)", "/* ---- 事件 ---- */") +
    between("function queueGuideDrag(d, sv)", 'cv.addEventListener("wheel"') +
    between("function bindProjectedGuideDrag(svg,", "/* ---- 世界層建立互動 ---- */") +
    between("function resetSceneFocus()", "async function loadScene(") +
    matching(/async function render\s*\(/, "/* ---- 拾取（hover / 點選共用） ---- */") +
    'function bindProjectionToggle(pane, bid) {\n' +
    between('const pt = pane.querySelector("#projectionDetails");', 'for (const c of pane.querySelectorAll("[data-proj-check]"))') + '}' +
    "\nthis.scheduler = hoverPickScheduler;", env);
  return {env, requests, calls, events, windowEvents, hoverInfo, pickInfo, frames,
    frame() { const work = [...frames.values()]; frames.clear(); work.forEach(fn => fn()); },
    context() { currentContext = {}; }, moveMatrix() { matrix = {...matrix,e:matrix.e + 1}; },
    projection(local = true) {
      const svg2 = {...svg}, overlay = layer();
      env.bindProjectedGuideDrag(svg2, e => e.x < 0 ? null : ({v:1,x:e.x,y:e.y}), overlay, async () => {}, local);
      return {svg:svg2, overlay};
    }};
}
const tick = async () => { for (let i=0; i<8; i++) await Promise.resolve(); };
const result = (desc, ops = [{op:"line",x0:1}]) => ({ok:true,desc,hover:ops,guide:-1,timber:-1,none:false});
const move = (h,x,y=2) => h.events.pointermove({clientX:x,clientY:y});
const reply = async (h,i,desc) => { h.requests[i].resolve(result(desc)); await tick(); };
async function main() {
  const test = nodeTest;
  await test("120 same-frame moves make one request at the final point", async () => {
    const h = harness(); for(let i=0;i<120;i++) move(h,i);
    assert.equal(h.requests.length,0); h.frame();
    assert.equal(h.requests.length,1); assert.equal(h.requests[0].cmd,"pick 0 119 2 8");
    await reply(h,0,"latest"); assert.equal(h.env.hover,"latest");
  });
  await test("slow bridge has one in-flight hover and one latest queued point", async () => {
    const h=harness(); move(h,0); h.frame();
    for(let i=1;i<120;i++) { move(h,i); h.frame(); }
    assert.equal(h.requests.length,1);
    await reply(h,0,"stale"); assert.equal(h.env.hover,"");
    h.frame(); assert.equal(h.requests.length,2);
    assert.equal(h.requests[1].cmd,"pick 0 119 2 8");
    await reply(h,1,"final"); assert.equal(h.env.hover,"final");
  });
  await test("leaving before a frame prevents dispatch", async () => {
    const h=harness(); move(h,1); h.events.pointerleave(); h.frame();
    assert.equal(h.requests.length,0); assert.equal(h.hoverInfo.textContent,"—");
  });
  await test("late leave reply cannot resurrect hover; selection stays visible", async () => {
    const h=harness(), selection=[{op:"selected"}];
    h.env.selected={hover:selection}; h.env.overlay.ops=[...selection];
    move(h,1); h.frame(); h.events.pointerleave(); await reply(h,0,"old");
    assert.equal(h.env.hover,""); assert.deepEqual(h.env.overlay.ops,selection);
    move(h,2); h.frame(); await reply(h,1,"new");
    assert.equal(h.env.hover,"new"); assert.deepEqual(h.env.overlay.ops,selection);
  });
  await test("moving outside all views supersedes an in-flight pick", async () => {
    const h=harness(); move(h,1); h.frame(); move(h,-1); await reply(h,0,"old");
    assert.equal(h.env.hover,""); assert.deepEqual(h.env.overlay.ops,[]);
  });
  await test("scene change before dispatch and during response invalidates hover", async () => {
    const h=harness(); move(h,1); h.context(); h.frame(); assert.equal(h.requests.length,0);
    move(h,2); h.frame(); h.context(); await reply(h,0,"old"); assert.equal(h.env.hover,"");
    move(h,3); h.frame(); await reply(h,1,"new"); assert.equal(h.env.hover,"new");
  });
  await test("view transforms, hidden canvas and changed history reject stale replies", async () => {
    for (const change of [h=>h.env.zoom++, h=>h.env.panX++, h=>h.env.layout={},
      h=>h.env.cv.hidden=true, h=>h.env.oc.on=true, h=>h.env.ReferenceWorkspace.history.undo.push({})]) {
      const h=harness(); move(h,1); h.frame(); change(h); await reply(h,0,"old");
      assert.equal(h.env.hover,"");
    }
  });
  await test("pointerdown uses the exact point directly and supersedes hover", async () => {
    const h=harness(); move(h,1); h.frame();
    const down=h.events.pointerdown({button:0,pointerId:1,clientX:40,clientY:50});
    assert.equal(h.requests.length,2); assert.equal(h.requests[1].cmd,"pick 0 40 50 8");
    await reply(h,0,"old"); assert.equal(h.env.hover,"");
    h.requests[1].resolve({...result("guide"),guide:7}); await down; await tick();
    move(h,99,88); await h.events.pointerup({button:0,clientX:100,clientY:90});
    assert(h.calls.includes("drag 7 0 100 90"));
    assert(h.calls.includes("line history-begin")); assert(h.calls.includes("line history-end"));
    assert.equal(h.requests.length,2);
  });
  await test("pointercancel drops hover and cancels the exact drag transaction", async () => {
    const h=harness(); move(h,1); h.frame();
    const down=h.events.pointerdown({button:0,pointerId:1,clientX:40,clientY:50});
    h.events.pointercancel(); await reply(h,0,"old");
    h.requests[1].resolve({...result("guide"),guide:7}); await down; await tick();
    assert(h.calls.includes("line history-abort")); assert(!h.calls.some(c=>c.startsWith("drag ")));
    assert.equal(h.env.hover,"");
  });
  await test("failed or thrown hover releases queue and preserves selection", async () => {
    for(const thrown of [false,true]) {
      const h=harness(); h.env.selected={hover:[{op:"selected"}]}; h.env.overlay.ops=[{op:"selected"}];
      move(h,1); h.frame();
      if(thrown) h.requests[0].reject(new Error("offline")); else h.requests[0].resolve({ok:false,transport:true});
      await tick(); assert.equal(h.env.hover,""); assert.deepEqual(h.env.overlay.ops,[{op:"selected"}]);
      move(h,2); h.frame(); await reply(h,1,"recovered"); assert.equal(h.env.hover,"recovered");
    }
  });
  await test("shared main/projection queue coalesces and strips local begin/end ops", async () => {
    const h=harness(), p=h.projection(); move(h,1); h.frame();
    for(let i=0;i<120;i++) p.svg.onpointermove({x:i,y:6});
    h.frame(); assert.equal(h.requests.length,1); await reply(h,0,"old"); h.frame();
    assert.equal(h.requests.length,2); assert.equal(h.requests[1].cmd,"pick 1 119 6 12");
    h.requests[1].resolve(result("projection",[{op:"begin"},{op:"line"},{op:"end"}])); await tick();
    assert.deepEqual(p.overlay.ops,[{op:"line"}]); assert.equal(h.env.hover,"projection");
  });
  await test("projection leave, detach, collapse, transform and focus invalidate responses", async () => {
    for(const change of [(h,p)=>p.svg.onpointerleave(), (h,p)=>p.svg.isConnected=false,
      h=>h.env.fe.projOpen=false, h=>h.moveMatrix(), (h,p)=>p.svg.bounds="new",
      (h,p)=>p.svg.hiddenParent={}, h=>h.env.oc.focus={}]) {
      const h=harness(),p=h.projection(); p.svg.onpointermove({x:1,y:2}); h.frame();
      change(h,p); await reply(h,0,"old"); assert.deepEqual(p.overlay.ops,[]); assert.equal(h.env.hover,"");
    }
  });
  await test("projection down/up remains exact and a late hover cannot repaint a drag", async () => {
    const h=harness(),p=h.projection(); p.svg.onpointermove({x:1,y:2}); h.frame();
    p.svg.onpointerdown({button:0,pointerId:1,x:40,y:50});
    assert.equal(h.requests[1].cmd,"pick 1 40 50 12"); await reply(h,0,"old");
    h.requests[1].resolve({...result("guide"),guide:8}); await tick();
    p.svg.onpointermove({x:70,y:80}); p.svg.onpointerup({button:0,x:90,y:100}); await tick();
    assert(h.calls.includes("drag 8 1 90 100")); assert(h.calls.includes("line history-end"));
    assert.equal(h.requests.length,2); assert.deepEqual(p.overlay.ops,[]);
  });
  await test("geometry change cancels queued reads without sending or replaying mutation", async () => {
    const h=harness(); move(h,1); h.windowEvents["geometry-definition-changed"](); h.frame();
    assert.equal(h.calls.length,0);
  });
  await test("throwing current or apply callbacks are reported and do not wedge the queue", async () => {
    for(const phase of ["dispatch","response","apply"]) {
      const h=harness(); let checks=0;
      h.env.scheduler.enqueue({v:0,x:1,y:2,r:8}, () => {
        if(phase === "dispatch" || phase === "response" && checks++ > 0) throw new Error("bad context");
        return true;
      }, () => { if(phase === "apply") throw new Error("bad overlay"); });
      h.frame();
      if(phase !== "dispatch") await reply(h,0,"first");
      assert.equal(h.env.errors.length,1);
      move(h,3); h.frame(); await reply(h,h.requests.length-1,"recovered");
      assert.equal(h.env.hover,"recovered");
    }
  });
  await test("definition and scene changes clear already displayed hover and readout", async () => {
    for(const transition of [h=>h.windowEvents["geometry-definition-changed"](),
      h=>{ h.context(); h.env.resetSceneFocus(); }]) {
      const h=harness(); move(h,1); h.frame(); await reply(h,0,"displayed");
      assert.equal(h.env.hover,"displayed"); assert.equal(h.env.overlay.ops.length,1);
      transition(h);
      assert.equal(h.env.hover,""); assert.equal(h.hoverInfo.textContent,"—");
      assert.deepEqual(h.env.overlay.ops,[]);
    }
  });
  await test("render clears displayed hover while keeping selected highlight", async () => {
    const h=harness(),selection=[{op:"selected"}]; h.env.selected={hover:selection};
    move(h,1); h.frame(); await reply(h,0,"displayed");
    assert.deepEqual(h.env.overlay.ops,selection); await h.env.render();
    assert.equal(h.env.hover,""); assert.equal(h.hoverInfo.textContent,"—");
    assert.deepEqual(h.env.overlay.ops,selection);
  });
  await test("projection collapse clears displayed hover and cancels its outstanding read", async () => {
    const h=harness(),p=h.projection(); let toggle;
    const details={open:false,addEventListener(name,fn) { assert.equal(name,"toggle"); toggle=fn; }};
    h.env.bindProjectionToggle({querySelector:()=>details},1);
    p.svg.onpointermove({x:1,y:2}); h.frame(); await reply(h,0,"displayed projection");
    assert.equal(p.overlay.ops.length,1); assert.equal(h.env.hover,"displayed projection");
    p.svg.onpointermove({x:3,y:4}); h.frame(); await toggle();
    assert.equal(h.env.fe.projOpen,false); assert.deepEqual(p.overlay.ops,[]);
    assert.equal(h.env.hover,""); assert.equal(h.hoverInfo.textContent,"—");
    await reply(h,1,"late"); assert.deepEqual(p.overlay.ops,[]); assert.equal(h.env.hover,"");
  });
  await test("context replacement clears displayed projection overlay", async () => {
    const h=harness(),p=h.projection(); p.svg.onpointermove({x:1,y:2}); h.frame();
    await reply(h,0,"displayed projection"); assert.equal(p.overlay.ops.length,1);
    h.context(); h.env.resetSceneFocus();
    assert.deepEqual(p.overlay.ops,[]); assert.equal(h.env.hover,"");
  });
}
main().catch(error => { console.error(error); process.exitCode=1; });
