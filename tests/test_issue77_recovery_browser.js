/* Real UI receipt recovery. Run only against an isolated owner-patched server:
 * GEOMETRY_TEST_URL=http://localhost:8815 GEOMETRY_FEEDBACK_DIR=/tmp/... \
 * GEOMETRY_ISSUE77_BROWSER_ADAPTER=/tmp/... node tests/test_issue77_recovery_browser.js
 * The TEMP adapter is explicit prototype evidence, not production-owner proof.
 */
"use strict";
const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path"), os = require("node:os");
const {chromium} = require("playwright");
const url = process.env.GEOMETRY_TEST_URL;
if (!url || !process.env.GEOMETRY_FEEDBACK_DIR?.startsWith(os.tmpdir() + path.sep)) throw new Error("Explicit isolated URL and TEMP feedback directory are required.");
const adapter = process.env.GEOMETRY_ISSUE77_BROWSER_ADAPTER ? fs.readFileSync(process.env.GEOMETRY_ISSUE77_BROWSER_ADAPTER, "utf8") : null;
const PDF = fs.readFileSync(path.join(__dirname, "fixtures/issue77-two-rooms.pdf")).toString("base64");
const A = [[1000,1000],[5000,1000],[5000,4000],[1000,4000]], B = [[6600,1000],[10600,1000],[10600,4000],[6600,4000]];
const evidence = process.env.GEOMETRY_ISSUE77_RECOVERY_SCREENSHOTS || path.join(os.tmpdir(), "issue77-recovery-evidence");
fs.mkdirSync(evidence, {recursive: true});
let checks = 0;
function check(value, expected, label) {assert.deepEqual(value, expected, label); checks++; console.log("PASS " + label);}
async function snapshot(page) {return page.evaluate(async () => ({scene:(await api("dump")).text, data:RoomCollectionWorkspace.controller.state(), nativeA:await api("boundary 1")}));}
async function setup(page) {
  await page.goto(url); await page.waitForFunction(() => window.RoomCollectionWorkspace && connection.phase === "ready");
  if (adapter) await page.evaluate(adapter);
  check(await page.title(), "構形 Canvas · 工程規格與空間建模", "app identity");
  check(await page.locator("#objectWorkspace").count(), 1, "meaningful app shell");
  await page.evaluate(async base64 => {
    for (const cmd of ["line reset", "line boundary 1 outline 1000,1000 5000,1000 5000,4000 1000,4000"]) {
      const reply=await api(cmd); if(!reply.ok)throw new Error(reply.error);
    }
    await renderObjects();
    const source=await ReferenceWorkspace.sourceFromFile(new File([Uint8Array.from(atob(base64), c=>c.charCodeAt(0))], "issue77-two-rooms.pdf", {type:"application/pdf"}));
    ReferenceWorkspace.context().sources.set(source.meta.id, source);
    const reference={id:crypto.randomUUID(),sourceId:source.meta.id,page:1,imgW:600,imgH:400,crop:[0,0,600,400],mmPerPx:20,x:0,y:0,rot:0,opacity:.5,locked:false,
      calibration:{points:[[50,300],[250,300]],distanceMm:4000,inputValue:4000,inputUnit:"mm"},reviewRequired:false,records:[]};
    await ReferenceWorkspace.preparePage(reference,source);ReferenceWorkspace.addPage(1,reference);
    await enterFocus("face",1);fiShowTab("underlay");
  }, PDF);
  await page.locator("#roomSourceCreate").click(); await page.waitForSelector("#roomNew");
}
async function draw(page) {
  await page.evaluate(() => {$("faceSnapToggle").checked=false;feFit([0,0,12000,8000]);});
  for (const point of B) {
    const at=await page.evaluate(([x,y])=>{const rect=$("faceEditorSvg").getBoundingClientRect();return {x:rect.left+x*fe.zoom+fe.panX,y:rect.top+y*fe.zoom+fe.panY};},point);
    await page.mouse.click(at.x,at.y);
  }
  check(await page.evaluate(()=>fe.draft.pts), B, "real pointer room B draft");
}
async function loseExecutedReply(page, target) {
  await page.evaluate(target => {
    const originalFetch=window.fetch.bind(window);
    window.__loss={target,lost:false,requestId:null,nativeResult:null,blockReceipts:true,commands:[],receipts:[]};
    window.fetch=async (input,options) => {
      let body;try {body=JSON.parse(options?.body || "null");}catch {}
      const loss=window.__loss;
      if(body?.receipt) {
        loss.receipts.push(body.receipt);
        if(body.receipt===loss.requestId && loss.blockReceipts) throw new TypeError("Injected unavailable receipt before manual recovery");
      }
      if(body?.cmd) {
        loss.commands.push({cmd:body.cmd,requestId:body.requestId});
        const matches=target==="confirm" ? /^line confirm \d+$/.test(body.cmd) : target==="preview" ? /^line preview boundary \d+ /.test(body.cmd) : body.cmd==="line " + target;
        if(matches && !loss.lost) {
          const response=await originalFetch(input,options);
          loss.nativeResult=await response.clone().json(); loss.requestId=body.requestId; loss.lost=true;
          if(!response.ok || !loss.nativeResult.ok)throw new Error("Injected request did not execute successfully");
          // The backend actually executed the request and saved its exact receipt.
          // Only delivery of that response, then the first receipt read, is lost.
          throw new TypeError("Injected executed request reply loss");
        }
      }
      return originalFetch(input,options);
    };
  },target);
}
async function main() {
  const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME || "/usr/bin/chromium",headless:true,args:["--no-sandbox"]});
  const errors=[];
  try {
    for (const target of ["preview","history-begin","confirm","history-end","cancel-preview"]) {
      const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage();
      page.on("pageerror",error=>errors.push(error.message));
      page.on("console",message=>{if(message.type()==="error")errors.push(message.text());});
      page.on("dialog",dialog=>dialog.accept(dialog.message().includes("目前房間") ? "Room A" : "Room B"));
      try {
        await setup(page);const before=await snapshot(page);check(before.nativeA.loops[0].verts,A,"independent A oracle");
        await page.locator("#roomNew").click();await draw(page);await loseExecutedReply(page,target);
        await page.locator("#faceDraftFinish").click();
        if(target!=="preview") {
          await page.waitForSelector("#roomConfirm");
          if(target==="cancel-preview") await page.getByRole("button",{name:"取消，保留原狀",exact:true}).click();
          else await page.locator("#roomConfirm").click();
        }
        await page.waitForFunction(()=>connection.phase==="error" && pendingApiResults.size===1);
        const lost=await page.evaluate(()=>({requestId:__loss.requestId,result:__loss.nativeResult,pending:[...pendingApiResults],receipts:__loss.receipts,hasWork:RoomCollectionWorkspace.hasWork,busy:RoomCollectionWorkspace.busy}));
        check(lost.result.ok,true,target+" actually executed before reply loss");assert.ok(lost.requestId,"mutation has exact native receipt ID");
        check(lost.pending[0][0],lost.requestId,target+" pending exact receipt");
        check(lost.receipts,[lost.requestId],target+" first automatic receipt unavailable");
        check(lost.busy,true,target+" unknown outcome keeps room lease");
        if(target==="history-end") await page.screenshot({path:path.join(evidence,"end-lost-reply.png")});
        await page.evaluate(()=>{__loss.blockReceipts=false;});
        await page.locator("#connectionRetry").click();
        await page.waitForFunction(()=>connection.phase==="ready" && pendingApiResults.size===0 && !RoomCollectionWorkspace.busy);
        const retired=await page.evaluate(()=>({tool:fe.tool,points:fe.draft.pts,preview:fe.draftPreview,drag:fe.drag,typed:fe.lenBuf,panHold:fe.panHold,newOutline:fe.newOutline,
          hasWork:RoomCollectionWorkspace.hasWork,lease:!!RoomCollectionWorkspace.transactionLease,dialogOpen:RoomCollectionWorkspace.dialogOpen,
          finishDisabled:$("faceDraftFinish").disabled,noticeHidden:$("faceDraftNotice").hidden,group:!!ReferenceWorkspace.history.group}));
        check(retired,{tool:"select",points:[],preview:null,drag:null,typed:"",panHold:null,newOutline:null,hasWork:false,lease:false,dialogOpen:false,finishDisabled:true,noticeHidden:true,group:false},target+" retires all room UI draft before editing resumes");
        const recovered=await snapshot(page);check(recovered.nativeA,before.nativeA,target+" recovery preserves original A");
        if(target==="preview") check(await page.evaluate(async token=>(await apiRequest("line confirm "+token)).ok,lost.result.preview.token),false,
          "recovered owned preview is cancelled natively before ownership is released");
        if(target==="history-end") {
          check(recovered.data.rooms.length,2,"committed end receipt preserves independent B metadata");
          check(await page.evaluate(async()=> (await api("boundary 2")).loops[0].verts),B,"committed end receipt preserves independent B geometry");
          await page.screenshot({path:path.join(evidence,"end-recovered-select.png")});
        } else check(recovered,before,target+" cancels unfinished transaction without geometry/metadata changes");
        const receiptCommands=await page.evaluate(()=>__loss.commands);
        check(receiptCommands.filter(row=>row.requestId===lost.requestId).length,1,target+" recovery never resends executed mutation");
        check(await page.evaluate(()=>__loss.receipts.length),2,target+" manual recovery reads existing receipt");
        // Exercise the real event handler even though the retired Finish button is hidden.
        await page.locator("#faceDraftFinish").dispatchEvent("click");
        await page.locator("#faceEditorViewport").focus();await page.keyboard.press("Enter");
        await page.evaluate(async()=>{await feDraftTryClose();});
        check(await snapshot(page),recovered,target+" Finish/Enter after recovery cannot reinterpret New B as an A replacement");
        check(await page.locator("dialog[open]").count(),0,target+" no fallback replacement confirmation");
        if(target==="cancel-preview") {
          await page.setViewportSize({width:390,height:844});
          await page.evaluate(()=>{fiShowTab("underlay");openPanel("right",$("workspaceToggleRight"));});
          await page.locator("#roomNew").scrollIntoViewIfNeeded();
          check(await page.locator("#roomNew").isVisible(),true,"390px recovered room entry is usable");
          await page.screenshot({path:path.join(evidence,"mobile-recovered-room-entry.png")});
          await page.setViewportSize({width:1440,height:1000});await page.evaluate(()=>closePanels());
        }
        await page.locator("#roomNew").click();await page.locator("#faceDraftCancel").click();
        await page.waitForFunction(()=>!RoomCollectionWorkspace.hasWork);
        check(await page.evaluate(()=>({tool:fe.tool,pts:fe.draft.pts})),{tool:"select",pts:[]},target+" known New cancel also retires redraw mode");
        check(await snapshot(page),recovered,target+" fresh new/cancel remains available after recovery");
      } catch(error) {
        await page.screenshot({path:path.join(evidence,target+"-failure.png")});
        console.error(await page.evaluate(()=>({phase:connection.phase,error:connection.error,draft:fe.draft,tool:fe.tool,loss:window.__loss,busy:RoomCollectionWorkspace?.busy,lease:!!RoomCollectionWorkspace?.transactionLease})));
        throw error;
      } finally {await context.close();}
    }
    check(errors,[],"no relevant app page/console errors");
    console.log(JSON.stringify({checks,evidence,browser:"Chromium via Playwright; Browser plugin unavailable",viewports:["1440x1000","390x844"],ownerAdapter:process.env.GEOMETRY_ISSUE77_BROWSER_ADAPTER || "official owner API",iOS:"not tested"}));
  } finally {await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
