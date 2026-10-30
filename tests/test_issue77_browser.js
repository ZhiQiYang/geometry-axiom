/* Run only against the isolated, owner-patched cloud checkout. */
"use strict";
const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path"), os = require("node:os");
const {chromium} = require("playwright");
const url = process.env.GEOMETRY_TEST_URL;
if (!url || !process.env.GEOMETRY_FEEDBACK_DIR?.startsWith(os.tmpdir() + path.sep)) throw new Error("Explicit isolated GEOMETRY_TEST_URL and TEMP feedback directory are required.");
const PDF = fs.readFileSync(path.join(__dirname, "fixtures/issue77-two-rooms.pdf")).toString("base64");
const A = [[1000,1000],[5000,1000],[5000,4000],[1000,4000]], B = [[6600,1000],[10600,1000],[10600,4000],[6600,4000]];
const evidence = process.env.GEOMETRY_ISSUE77_SCREENSHOTS || path.join(os.tmpdir(), "issue77-browser-evidence");
const adapter = process.env.GEOMETRY_ISSUE77_BROWSER_ADAPTER ? fs.readFileSync(process.env.GEOMETRY_ISSUE77_BROWSER_ADAPTER, "utf8") : null;
fs.mkdirSync(evidence, {recursive: true});
let checks = 0;
function check(value, expected, label) {assert.deepEqual(value, expected, label); checks++; console.log("PASS " + label);}
async function drawing(page, pts) {
  await page.evaluate(() => {$("faceSnapToggle").checked = false; feFit([0,0,12000,8000]);});
  for (const point of pts) {
    const at = await page.evaluate(([x,y]) => {const r=$("faceEditorSvg").getBoundingClientRect(); return {x:r.left+x*fe.zoom+fe.panX,y:r.top+y*fe.zoom+fe.panY};}, point);
    await page.mouse.click(at.x, at.y);
  }
  check(await page.evaluate(() => fe.draft.pts.map(p=>p.map(Math.round))), pts, "real pointer drafting has expected UV vertices");
}
async function native(page, bid) {return page.evaluate(async id => (await api("boundary " + id)).loops, bid);}
async function snapshot(page) {return page.evaluate(async () => ({scene:(await api("dump")).text,data:RoomCollectionWorkspace.controller.state()}));}
async function ready(page) {await page.waitForFunction(() => typeof RoomCollectionWorkspace !== "undefined" && connection.phase === "ready"); if(adapter)await page.evaluate(adapter);}
async function main() {
  const browser = await chromium.launch({executablePath: process.env.GEOMETRY_CHROME || "/usr/bin/chromium", headless: true, args: ["--no-sandbox"]});
  const errors = [], page = await browser.newPage({viewport:{width:1440,height:1000}});
  page.on("pageerror", error => errors.push(error.message));
  page.on("console", message => {if(message.type()==="error")errors.push(message.text());});
  let prompts = [];
  page.on("dialog", async dialog => {await dialog.accept(prompts.shift() || "房間 B");});
  try {
    await page.goto(url); await ready(page);
    check(await page.title(), "構形 Canvas · 工程規格與空間建模", "correct app identity");
    check(await page.locator("#objectWorkspace").count(), 1, "meaningful app shell is present");
    await page.evaluate(async base64 => {
      const reset=await api("line reset");if(!reset.ok)throw new Error(reset.error);
      const created=await api("line boundary 1 outline 1000,1000 5000,1000 5000,4000 1000,4000");if(!created.ok)throw new Error(created.error);
      await renderObjects();
      const bytes=Uint8Array.from(atob(base64),ch=>ch.charCodeAt(0));
      const source=await ReferenceWorkspace.sourceFromFile(new File([bytes],"issue77-two-rooms.pdf",{type:"application/pdf"}));
      ReferenceWorkspace.context().sources.set(source.meta.id,source);
      const page={id:crypto.randomUUID(),sourceId:source.meta.id,page:1,imgW:600,imgH:400,crop:[0,0,600,400],mmPerPx:20,x:0,y:0,rot:0,opacity:.5,locked:false,
        calibration:{points:[[50,300],[250,300]],distanceMm:4000,inputValue:4000,inputUnit:"mm"},reviewRequired:false,records:[]};
      await ReferenceWorkspace.preparePage(page,source); ReferenceWorkspace.addPage(1,page);
      await enterFocus("face",1); fiShowTab("underlay");
    }, PDF);
    prompts.push("房間 A"); await page.locator("#roomNew").click();
    await page.waitForFunction(() => RoomCollectionWorkspace.controller.state().rooms.length === 1);
    let data = await page.evaluate(() => RoomCollectionWorkspace.controller.state());
    check(data.planes.length, 1, "one shared source plane"); check(data.rooms[0].name,"房間 A","existing boundary is explicitly named and associated");
    const initialA=await native(page,1), beforeCancel=await snapshot(page);
    await page.locator("#roomNew").click();
    check(await page.locator("#faceDraftCancel").isEnabled(),true,"empty new-room draft can be cancelled");
    check(await page.evaluate(async () => {try {await ReferenceWorkspace.exportBytes();return false;} catch {return true;}}),true,"pending room draft blocks project save");
    await page.locator("#faceDraftCancel").click(); await page.waitForFunction(() => !RoomCollectionWorkspace.hasWork);
    check(await snapshot(page),beforeCancel,"empty draft cancellation leaves project untouched");
    await page.locator("#roomNew").click(); await drawing(page,B); await page.locator("#faceDraftCancel").click();
    await page.waitForFunction(() => !RoomCollectionWorkspace.hasWork);
    check(await snapshot(page),beforeCancel,"cancel leaves native geometry and attachment untouched");
    await page.locator("#roomNew").click(); await drawing(page,B); prompts.push("房間 B");
    await page.locator("#faceDraftFinish").click(); await page.waitForSelector("#roomConfirm");
    check(await native(page,1),initialA,"new preview does not replace A");
    await page.locator("#roomConfirm").click(); await page.waitForFunction(() => RoomCollectionWorkspace.controller.state().rooms.length===2 && !RoomCollectionWorkspace.hasWork);
    await page.waitForFunction(() => oc.edit?.bid===2);
    data=await page.evaluate(() => RoomCollectionWorkspace.controller.state());
    check(data.rooms.map(r=>r.boundaryRef.id),[1,2],"two independent native boundary IDs"); check(await native(page,1),initialA,"new B preserves A");
    check((await native(page,2))[0].verts,B,"new B equals independent oracle");
    check(data.rooms.map(r=>r.acceptedBasisRevision),[1,1],"both rooms use shared initial basis");
    await page.screenshot({path:path.join(evidence,"desktop-two-rooms.png")});
    const named = data.rooms[1].id; prompts.push("房間 B 改名"); await page.locator(`[data-room-rename="${named}"]`).click();
    check((await snapshot(page)).data.rooms[1].name,"房間 B 改名","rename changes only selected room metadata");
    await page.evaluate(async () => {const r=await api("line undo");if(!r.ok)throw new Error(r.error);renderFaceInspector();});
    check((await snapshot(page)).data.rooms[1].name,"房間 B","metadata undo restores room name");
    const editedB=[[6600,1000],[10200,1000],[10200,4000],[6600,4000]];
    await page.locator(`[data-room-edit="${named}"]`).click();
    await page.waitForFunction(id => RoomCollectionWorkspace.controller.intent?.roomId===id && fe.tool==="redraw",named);
    await drawing(page,editedB);
    await page.locator("#faceDraftFinish").click(); await page.locator("#roomConfirm").click();
    await page.waitForFunction(() => !RoomCollectionWorkspace.hasWork && fe.tool==="select");
    check((await native(page,2))[0].verts,editedB,"explicit edit replaces only selected B outer boundary");
    check(await native(page,1),initialA,"explicit B edit preserves A");
    const beforeBasis = (await snapshot(page)).scene;
    await page.locator("#refAlignmentDetails > summary").click(); await page.locator("#ulX").fill("100"); await page.locator("#ulX").press("Tab");
    data=(await snapshot(page)).data;
    check(data.rooms.map(r=>r.reviewState),["needs-review","needs-review"],"basis change marks existing rooms for review"); check((await snapshot(page)).scene,beforeBasis,"basis change never transforms native geometry");
    await page.locator(`[data-room-review="${named}"]`).click();
    await page.waitForFunction(() => RoomCollectionWorkspace.controller.state().rooms[1].reviewState==="confirmed");
    check((await snapshot(page)).data.rooms.map(r=>r.reviewState),["needs-review","confirmed"],"explicit review acknowledges only selected room");
    check((await snapshot(page)).scene,beforeBasis,"explicit review changes no native geometry");
    await page.locator("#roomNew").click(); await drawing(page,[[100,5000],[1100,5000],[1100,6000],[100,6000]]); prompts.push("新基準房間");
    await page.locator("#faceDraftFinish").click(); await page.locator("#roomConfirm").click();
    await page.waitForFunction(() => RoomCollectionWorkspace.controller.state().rooms.length===3 && !RoomCollectionWorkspace.hasWork && oc.edit?.bid===3 && fe.tool==="select");
    data=(await snapshot(page)).data;check(data.rooms[2].acceptedBasisRevision,2,"new room accepts new basis");
    check(await native(page,1),initialA,"new basis room preserves A geometry");
    // Full ZIP is reopened in a different browser context against the same isolated service.
    const saved=await page.evaluate(async () => [...await ReferenceWorkspace.exportBytes()]);
    const archive=await page.evaluate(bytes => {const entries=fflate.unzipSync(new Uint8Array(bytes));return {manifest:JSON.parse(new TextDecoder().decode(entries['manifest.json'])),keys:Object.keys(entries)};},saved);
    check(archive.manifest.faces.length,0,"adopted source saves no legacy independent basis shadow");
    check(archive.keys.filter(key=>key.startsWith('sources/')).length,1,"shared PDF stored once in ZIP");
    const nativeBeforeOpen=(await snapshot(page)).scene;
    const fresh=await browser.newContext({viewport:{width:1440,height:1000}}), reopened=await fresh.newPage();
    reopened.on("pageerror",error=>errors.push(error.message)); reopened.on("dialog",dialog=>dialog.accept());
    await page.close(); await reopened.goto(url); await ready(reopened);
    await reopened.evaluate(async bytes => {await ReferenceWorkspace.importBytes(new Uint8Array(bytes),"issue77-fresh.gcanvas");},saved);
    check((await snapshot(reopened)).scene,nativeBeforeOpen,"true ZIP fresh-context import preserves full native scene");
    check((await snapshot(reopened)).data,data,"true ZIP fresh-context import preserves source basis and room records");
    await reopened.evaluate(async id => {await enterFocus("face",id);fiShowTab("underlay");},2);
    const beforeUnlink=(await snapshot(reopened)).scene;
    await reopened.locator(`[data-room-unlink="${named}"]`).click();
    check((await snapshot(reopened)).data.rooms.length,2,"unlink removes selected room list record");
    check((await snapshot(reopened)).scene,beforeUnlink,"unlink keeps native geometry");
    await reopened.evaluate(async () => {await api("line undo");ReferenceWorkspace.sync();renderFaceInspector();});
    check((await snapshot(reopened)).data.rooms.length,3,"undo restores room association");
    await reopened.setViewportSize({width:390,height:844});
    await reopened.evaluate(() => {fiShowTab("underlay");openPanel("right",$("workspaceToggleRight"));});
    await reopened.locator("#roomNew").scrollIntoViewIfNeeded();
    await reopened.screenshot({path:path.join(evidence,"mobile-room-list.png")});
    check(await reopened.locator("#roomNew").isVisible(),true,"390px has visible continuous-room entry");
    check(await reopened.locator("[data-room-id]").count(),3,"390px lists all room records");
    check(errors,[],"no app page or console errors");
    await fresh.close();
    console.log(JSON.stringify({checks,evidence,viewports:["1440x1000","390x844"],browser:"Chromium via Playwright; Browser plugin unavailable",ownerAdapter:process.env.GEOMETRY_ISSUE77_BROWSER_ADAPTER || "official owner API",iOS:"not tested"}));
  } finally {await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
