/* K4 (#116 other canvases) acceptance gate. Created by PR-a with the shell segment only; the cursor,
 * object-canvas menu and touch segments are added by PR-b/c/d (PROPOSAL.md section 11).
 *
 * Segment A -- face menu characterization. Pins the behaviour of the existing face context menu
 *   (#feCtxMenu) that PR-a must not change. Runs against the code BEFORE the extraction and AFTER it
 *   (GEOMETRY_K4_PHASE=characterize runs A only, for a pre-extraction baseline); it also records a
 *   byte-level snapshot of the menu DOM/geometry for a fixed set of targets, so a before/after run
 *   can be compared with `sha256`.
 * Segment B -- ContextMenuShell contract. Drives the shell through throw-away adapters mounted next
 *   to the real app: single live instance (DP-24), two-level guard (DP-33), the pre-run current()
 *   re-check, keyboard, edge clamping/flip, outside-pointer close, attribute parametrisation.
 *
 * Requires an explicitly isolated service and TEMP feedback/evidence directories (same rules as
 * tests/test_issue116_browser.js). NODE_PATH may point to an existing Playwright install.
 * GEOMETRY_CHROME / GEOMETRY_CHROME_FLAGS select the browser. GEOMETRY_K4_KEEP_GOING=1 records every
 * failing check instead of stopping at the first one (used for mutation runs).
 */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const {chromium}=require('playwright');
const url=process.env.GEOMETRY_TEST_URL, feedback=process.env.GEOMETRY_FEEDBACK_DIR;
if(!url || !feedback || !path.resolve(feedback).startsWith(os.tmpdir()+path.sep))throw Error('Explicit isolated URL and TEMP feedback directory required');
const evidence=process.env.GEOMETRY_K4_EVIDENCE || path.join(os.tmpdir(),'geometry-tests','issue116-k4-evidence');
if(!path.resolve(evidence).startsWith(os.tmpdir()+path.sep))throw Error('Evidence must stay under TEMP');
fs.mkdirSync(evidence,{recursive:true});
const characterizeOnly=process.env.GEOMETRY_K4_PHASE==='characterize', keepGoing=process.env.GEOMETRY_K4_KEEP_GOING==='1';
let checks=0;const errors=[],records=[],failures=[];
function show(v){try{return JSON.stringify(v)?.slice(0,400);}catch{return String(v);}}
function check(actual,expected,label){
  try{assert.deepEqual(actual,expected);}
  catch{
    const message='FAIL '+label+' | actual='+show(actual)+' expected='+show(expected);
    console.log(message);failures.push(message);
    if(!keepGoing)throw Error(message);
    return;
  }
  checks++;console.log('PASS '+label);records.push(label);
}
const cmds=[];
// The app's own definition of "this command can change the world" (apiRequest in app.js).
const isWrite=cmd=>/^(line |drag |reset$|default$|undo$|redo$|loadfile )/.test(cmd);
const writes=()=>cmds.filter(isWrite);
async function until(fn,ms=4000){const t0=Date.now();while(Date.now()-t0<ms){if(await fn())return true;await new Promise(r=>setTimeout(r,40));}return false;}
async function dump(page){return page.evaluate(async()=>{const r=await api('dump');if(!r.ok)throw Error(r.error);return r.text;});}
async function fixture(page,extra=[],placed=true){
  await page.evaluate(async ({extra,placed})=>{
    for(const d of document.querySelectorAll('dialog[open]'))d.close();resetSceneFocus();closePanels();oc.busy=false;
    for(const cmd of ['reset',placed?'line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000':'line boundary 1 outline 0,0 4000,0 4000,3000 0,3000',...extra]){
      const r=await apiRequest(cmd);if(!r.ok)throw Error(cmd+': '+r.error);
    }
    await renderObjects();await enterFocus('face',1);feSetTool('select');
    $('faceSnapToggle').checked=true;$('feZoomFit').click();drawFaceEditor();
  },{extra,placed});
}
async function at(page,u,v){return page.evaluate(([u,v])=>{const r=$('faceEditorSvg').getBoundingClientRect();return{x:r.left+fe.panX+u*fe.zoom,y:r.top+fe.panY+v*fe.zoom};},[u,v]);}
async function right(page,u=4000,v=1000){const p=await at(page,u,v);await page.mouse.click(p.x,p.y,{button:'right'});await page.locator('#feCtxMenu').waitFor({state:'visible'});}
async function close(page){await page.keyboard.press('Escape');await page.waitForFunction(()=>$('feCtxMenu').hidden);}
async function snapshot(page,label,store){
  store[label]=await page.evaluate(()=>{
    const rect=n=>{const r=n.getBoundingClientRect();return[r.left,r.top,r.width,r.height].map(v=>Math.round(v*100)/100);};
    const menu=$('feCtxMenu'),panel=$('feOpPanel'),sub=menu.querySelector('.fcm-submenu');
    return{menuHtml:menu.outerHTML,menuRect:rect(menu),panelOpen:!panel.hidden,panelClass:panel.className,formSide:panel.dataset.formSide??null,
      panelRect:panel.hidden?null:rect(panel),submenuHtml:sub?sub.outerHTML:null,submenuRect:sub?rect(sub):null,
      barSuppressed:$('feActionBar').classList.contains('fcm-suppressed'),anchorDisplay:document.querySelector('.fcm-anchor')?.style.display??null};
  });
}
async function main(){
  const runtime=await fetch(new URL('/runtime',url)).then(r=>r.json());
  check(runtime.fresh,true,'runtime fresh before the run');
  check(path.resolve(runtime.root),path.resolve(__dirname,'..'),'runtime belongs to this worktree');
  const executablePath=process.env.GEOMETRY_CHROME;
  const args=(process.env.GEOMETRY_CHROME_FLAGS||'').split(/\s+/).filter(Boolean);
  const browser=await chromium.launch({headless:true,...(executablePath?{executablePath}:{channel:'chrome'}),...(args.length?{args}:{})});
  const context=await browser.newContext({viewport:{width:1440,height:900},deviceScaleFactor:1});
  await context.addInitScript(()=>{window.showSaveFilePicker=undefined;});
  const page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  page.on('request',r=>{if(r.method()==='POST'&&new URL(r.url()).pathname==='/api'){try{cmds.push(JSON.parse(r.postData()).cmd);}catch{}}});
  try{
    await page.goto(url);await page.waitForFunction(()=>window.FaceContextMenu && connection.phase==='ready');

    // ---------------------------------------------------------------- Segment A: face menu characterization
    check(await page.evaluate(()=>Object.keys(Object.getOwnPropertyDescriptors(FaceContextMenu)).sort()),['current','hide','open','position','show','stamp','sync'],
      'a0 FaceContextMenu public surface is unchanged (callers in app.js depend on it)');
    check(await page.evaluate(()=>[$('feCtxMenu').getAttribute('role'),$('feCtxMenu').className,$('feCtxMenu').parentElement===document.body]),['menu','fe-ctx-menu',true],
      'a0 #feCtxMenu keeps role/class and is hoisted to body');

    // a1 -- the stale-node case of PROPOSAL section 10 PR-a: only fe.sel changes, edge -> another edge on loop 0.
    // feActionsFor() returns the same act set for both edges and no world write is refused for any other reason,
    // so the ONLY thing between the saved node and a real boundary write is the menu's "still current?" re-check.
    await fixture(page);await right(page,4000,1000);
    check(await page.evaluate(()=>({...fe.sel})),{kind:'edge',loop:0,i:1},'a1 real right-click selected the right edge (loop 0, edge 1)');
    await page.evaluate(()=>{window.__k4Stale=document.querySelector('#feCtxMenu [data-fe-act="fixity"]');});
    const a1Before=await dump(page);cmds.length=0;
    await page.evaluate(()=>{fe.sel={kind:'edge',loop:0,i:3};});
    check(await page.evaluate(()=>JSON.stringify(feActionsFor(fe.sel).map(a=>a.act))===JSON.stringify(feActionsFor({kind:'edge',loop:0,i:1}).map(a=>a.act))),true,
      'a1 precondition: both edges expose the same acts, so no other guard can hide a missing re-check');
    await page.evaluate(()=>{window.__k4Stale.click();});
    await new Promise(r=>setTimeout(r,500));
    check(writes(),[],'a1 STALE MENU NODE SENT A WORLD COMMAND: after fe.sel changed edge->edge the saved Fixity row must send 0 commands (pre-run current() re-check)');
    check(await dump(page),a1Before,'a1 stale click left the native dump byte for byte unchanged');
    check(await page.evaluate(()=>[FaceContextMenu.open,$('feCtxMenu').hidden]),[false,true],'a1 stale click closes the menu instead of running');
    // a1c -- control: the same node, not stale, is sent. Without this the zero above could be an instrument that sees nothing.
    await fixture(page);await right(page,4000,1000);const a1cBefore=await dump(page);cmds.length=0;
    await page.locator('#feCtxMenu [data-fe-act="fixity"]').click();
    check(await until(()=>writes().length>0),true,'a1c control: a live (not stale) Fixity click does send a world command');
    check((await dump(page))===a1cBefore,false,'a1c control: the live Fixity click really changed the world');

    // a2 -- two-level guard on the real menu: view-level items are not behind the write guard, world-level ones are.
    await fixture(page);await right(page,4000,1000);
    await page.evaluate(()=>{oc.busy=true;fe.fiTab='guide';});
    await page.locator('#feCtxMenu .fcm-tile[data-fe-act="op:notch"]').click();
    check(await page.evaluate(()=>[!$('feCtxMenu').hidden,fe.op,document.querySelector('.fcm-footer').textContent]),[true,null,'正在等待目前操作完成'],
      'a2 WORLD ITEM RAN UNDER oc.busy: a world-level tile must be refused with the write-guard reason and keep the menu open');
    await page.locator('#feCtxMenu [data-fe-act="props"]').click();
    check(await page.evaluate(()=>[$('feCtxMenu').hidden,fe.fiTab]),[true,'prop'],'a2 VIEW ITEM WAS BLOCKED BY THE WRITE GUARD: "edit in right panel" must still run while oc.busy');
    await page.evaluate(()=>{oc.busy=false;});

    // a3 -- IME composition never fires an item; an ordinary Enter on the same search does.
    await fixture(page);await right(page,4000,1000);
    await page.locator('.fcm-search input').fill('外凸');
    await page.evaluate(()=>{document.querySelector('.fcm-search input').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',isComposing:true,bubbles:true,cancelable:true}));});
    check(await page.evaluate(()=>fe.op),null,'a3 Enter during IME composition does not run the matched command');
    await page.locator('.fcm-search input').press('Enter');
    check(await page.evaluate(()=>fe.op?.type),'extend','a3 the same Enter outside composition runs it');
    await page.keyboard.press('Escape');await page.keyboard.press('Escape');

    // a4 -- focus leaving the menu closes it (existing behaviour, now owned by the shell).
    await fixture(page);await right(page,4000,1000);
    await page.evaluate(()=>{const i=document.createElement('input');i.id='k4Outside';document.body.append(i);i.focus();});
    check(await page.evaluate(()=>[FaceContextMenu.open,$('feCtxMenu').hidden]),[false,true],'a4 moving focus outside closes the face menu');
    await page.evaluate(()=>document.getElementById('k4Outside')?.remove());

    // a5 -- byte-level snapshots of the menu for a fixed set of targets (compared before/after the extraction by sha256).
    const snapshots={};
    await fixture(page);await right(page,4000,1000);await snapshot(page,'edge-outer',snapshots);
    await page.locator('#feCtxMenu [data-fe-act="create"]').click();await snapshot(page,'edge-outer+create-submenu',snapshots);
    await page.locator('#feCtxMenu [data-fe-act="view"]').click();await snapshot(page,'edge-outer+view-submenu',snapshots);
    await page.locator('.fcm-search input').fill('線');await snapshot(page,'edge-outer+search-line',snapshots);
    await page.locator('.fcm-search input').fill('');
    await page.locator('#feCtxMenu [data-fe-act="op:notch"]').click();await page.locator('#feOpPanel').waitFor({state:'visible'});await snapshot(page,'edge-outer+notch-form',snapshots);
    await close(page);await close(page);
    await fixture(page);await right(page,0,0);await snapshot(page,'corner-convex',snapshots);await close(page);
    await fixture(page,['line boundary 1 outline 0,0 4000,0 4000,900 3400,900 3400,2100 4000,2100 4000,3000 0,3000']);await right(page,3400,900);await snapshot(page,'corner-concave',snapshots);await close(page);
    await fixture(page,['line boundary 1 outline 0,0 4000,0 4000,3000 0,3000 hole 1200,1000 1200,1400 1600,1400 1600,1000']);await right(page,1600,1200);await snapshot(page,'edge-hole',snapshots);await close(page);
    await fixture(page);await right(page,2000,1500);await snapshot(page,'point-inside',snapshots);await close(page);
    await fixture(page);{const f=await at(page,4100,1000);await page.mouse.click(f.x,f.y,{button:'right'});await page.locator('#feCtxMenu').waitFor({state:'visible'});}await snapshot(page,'blank-outside',snapshots);await close(page);
    await fixture(page,['line spec guideAt 2000','line guide 1 1 v spec:guideAt']);await right(page,2000,1700);await snapshot(page,'guide',snapshots);await close(page);
    await fixture(page,[],false);await right(page,2000,1700);await snapshot(page,'point-unplaced',snapshots);await close(page);
    await fixture(page,['line timber 10 100 33 role boundary','line place 10 on 1 at-face e0 +u +n','line timber 11 100 33 role boundary','line place 11 on 1 at-face e2 +u +n']);
    {const p=await at(page,1000,50);await page.mouse.click(p.x,p.y);}await right(page,1000,50);await snapshot(page,'timber-single',snapshots);await close(page);
    {const p=await at(page,1000,50);await page.mouse.click(p.x,p.y);await page.keyboard.down('Shift');const q=await at(page,1000,2950);await page.mouse.click(q.x,q.y);await page.keyboard.up('Shift');}
    await right(page,1000,50);await snapshot(page,'timber-multi',snapshots);await close(page);
    await page.setViewportSize({width:390,height:844});await fixture(page);await right(page,4000,1000);await snapshot(page,'edge-outer@390',snapshots);
    await page.locator('#feCtxMenu [data-fe-act="op:notch"]').click();await page.locator('#feOpPanel').waitFor({state:'visible'});await snapshot(page,'edge-outer+notch-form@390',snapshots);await close(page);await close(page);
    await page.setViewportSize({width:1440,height:900});
    const snapshotJson=JSON.stringify(snapshots,null,1);
    fs.writeFileSync(path.join(evidence,'menu-snapshots.json'),snapshotJson);
    const snapshotHash=crypto.createHash('sha256').update(snapshotJson).digest('hex');
    fs.writeFileSync(path.join(evidence,'menu-snapshots.sha256'),snapshotHash+'\n');
    console.log('MENU-SNAPSHOT-SHA256 '+snapshotHash+' ('+Object.keys(snapshots).length+' targets)');
    check(Object.keys(snapshots).length,16,'a5 all 16 menu snapshots were recorded');

    if(characterizeOnly){
      check(errors,[],'no app page or console errors (characterize phase)');
      fs.writeFileSync(path.join(evidence,'result.json'),JSON.stringify({phase:'characterize',checks,records,failures,errors,snapshotHash,runtime:runtime.version},null,2));
      console.log(JSON.stringify({phase:'characterize',checks,failures:failures.length,snapshotHash}));
      return;
    }

    // ---------------------------------------------------------------- Segment B: ContextMenuShell contract
    check(await page.evaluate(()=>typeof window.ContextMenuShell?.create),'function','b0 window.ContextMenuShell.create exists');
    check(await page.evaluate(()=>[...document.scripts].map(s=>s.getAttribute('src')).filter(s=>/context-menu-shell|face-menu-icons|face-context-menu/.test(s))),
      ['face-menu-icons.js','context-menu-shell.js','face-context-menu.js'],'b0 shell loads after the icon pack and before the face adapter');
    // Throw-away adapters mounted beside the real app. A and B ignore each other's DOM (and the face menu's) in focusin,
    // so that only the single-instance rule -- not focus-out -- can be what closes the first one.
    await page.evaluate(()=>{
      const mk=(id,opts={})=>{
        const vp=document.createElement('div');vp.id=id+'Viewport';vp.tabIndex=-1;
        vp.style.cssText='position:fixed;left:40px;top:40px;width:900px;height:600px;pointer-events:none';document.body.append(vp);
        const menu=document.createElement('div');menu.id=id+'Menu';menu.setAttribute('role','menu');menu.hidden=true;menu.style.cssText='position:fixed;z-index:95;background:#fff';document.body.append(menu);
        const ctx={n:1,navReason:'',worldReason:'',refuse:false,log:[],throwOn:null,shell:null};
        const it=(act,label,extra={})=>({act,label,iconName:null,reason:'',...extra});
        const tiles=[it('v1','檢視項',{level:'view'})],
          groups=[[it('n1','導覽項',{level:'nav'}),it('w1','寫入項')],[it('sub1','子選單',{sub:true})]],
          submenus={sub1:[it('s1','子項')]};
        const shell=ContextMenuShell.create({
          host:id,menu,viewport:vp,actAttr:'data-cm-act',escape:v=>ReferenceWorkspace.escape(v),icon:n=>icon(n),
          model:()=>({title:'測試選單',meta:id,chip:'',typeIcon:'fit',tiles,groups,submenus}),
          stamp:()=>({n:ctx.n}),current:s=>!!s&&s.n===ctx.n,
          guards:{nav:()=>ctx.navReason,world:()=>ctx.worldReason},
          begin:(x,y)=>ctx.refuse?null:{x,y},
          // like the face adapter: the effect closes the menu itself (shell.hide) before it acts
          execute:async a=>{if(ctx.throwOn===a.act)throw Error('boom '+a.act);ctx.log.push(a.act);ctx.shell.hide();},
          related:node=>!!opts.related?.(node),outsidePointerClose:!!opts.outsidePointerClose,onError:e=>ctx.log.push('error:'+e.message),
        });
        ctx.shell=shell;
        return{vp,menu,ctx,shell};
      };
      const faceMenu=()=>document.getElementById('feCtxMenu');
      let a,b;
      a=mk('k4a',{related:n=>b.menu.contains(n)||faceMenu().contains(n)});
      b=mk('k4b',{related:n=>a.menu.contains(n)||faceMenu().contains(n)});
      window.__k4={mk,a,b};
    });
    // b1 single instance (DP-24).
    check(await page.evaluate(()=>{const {a,b}=window.__k4;const r1=a.shell.open(300,200);const first=[r1,a.shell.isOpen,ContextMenuShell.active===a.shell];
      const r2=b.shell.open(320,220);return[first,[r2,a.shell.isOpen,a.menu.hidden,b.shell.isOpen,ContextMenuShell.active===b.shell]];}),
      [[true,true,true],[true,false,true,true,true]],'b1 SECOND MENU DID NOT CLOSE THE FIRST: opening B closes A and A hides its element (one live instance, DP-24)');
    check(await page.evaluate(()=>['feCtxMenu','k4aMenu','k4bMenu'].filter(id=>!document.getElementById(id).hidden)),['k4bMenu'],'b1 exactly one of the menus is visible after the second open');
    await fixture(page);
    check(await page.evaluate(()=>{FaceContextMenu.show(300,300);return[FaceContextMenu.open,window.__k4.b.shell.isOpen,window.__k4.b.menu.hidden,ContextMenuShell.active!==window.__k4.b.shell];}),
      [true,false,true,true],'b1 opening the real face menu closes another live shell instance (the face adapter is registered in the same single-instance registry)');
    await page.evaluate(()=>FaceContextMenu.hide());
    check(await page.evaluate(()=>ContextMenuShell.active),null,'b1 no instance is active once everything is closed');

    // b2 two-level guard (DP-33) + b3 pre-run current() re-check, on instance A.
    const itemSel=(id,act)=>`#${id}Menu [data-cm-act="${act}"]`;
    await page.evaluate(()=>{const {a}=window.__k4;a.ctx.log.length=0;a.shell.open(300,200);});
    check(await page.evaluate(()=>[document.querySelectorAll('#k4aMenu [data-cm-act]').length,document.querySelectorAll('#k4aMenu [data-fe-act]').length]),[4,0],
      'b2 items carry the adapter-chosen attribute (data-cm-act), never data-fe-act');
    await page.evaluate(()=>{const {a}=window.__k4;a.ctx.worldReason='W-REASON';a.ctx.navReason='N-REASON';});
    await page.locator(itemSel('k4a','v1')).click();
    check(await page.evaluate(()=>[window.__k4.a.ctx.log.slice(),window.__k4.a.shell.isOpen]),[['v1'],false],'b2 VIEW ITEM WAS GUARDED: a view-level item runs although both write guards refuse');
    await page.evaluate(()=>{const {a}=window.__k4;a.ctx.log.length=0;a.shell.open(300,200);});
    await page.locator(itemSel('k4a','w1')).click();
    check(await page.evaluate(()=>[window.__k4.a.ctx.log.slice(),window.__k4.a.shell.isOpen,document.querySelector('#k4aMenu .fcm-footer').textContent]),[[],true,'W-REASON'],
      'b2 WORLD ITEM RAN UNDER A REFUSING WRITE GUARD: refused, reason shown in the footer, menu stays open');
    await page.locator(itemSel('k4a','n1')).click();
    check(await page.evaluate(()=>[window.__k4.a.ctx.log.slice(),document.querySelector('#k4aMenu .fcm-footer').textContent]),[[],'N-REASON'],'b2 nav-level item is refused by the nav guard, not the world guard');
    await page.evaluate(()=>{const {a}=window.__k4;a.ctx.worldReason='';});
    await page.locator(itemSel('k4a','w1')).click();
    check(await page.evaluate(()=>[window.__k4.a.ctx.log.slice(),window.__k4.a.shell.isOpen]),[['w1'],false],'b2 once the write guard allows, the world item runs and the adapter closes the menu');
    await page.evaluate(()=>{const {a}=window.__k4;a.ctx.log.length=0;a.shell.hide();a.ctx.worldReason='';a.ctx.navReason='';a.shell.open(300,200);});
    await page.evaluate(()=>{window.__k4.a.ctx.n++;});
    await page.locator(itemSel('k4a','v1')).click();
    check(await page.evaluate(()=>[window.__k4.a.ctx.log.slice(),window.__k4.a.shell.isOpen,window.__k4.a.menu.hidden]),[[],false,true],
      'b3 STALE NODE RAN: after the adapter context changed, even a view-level item must not run -- the shell re-checks current() before every item');
    await page.evaluate(()=>{const {a}=window.__k4;a.ctx.log.length=0;a.shell.open(300,200);});
    await page.evaluate(()=>{window.__k4.a.ctx.n++;});
    check(await page.evaluate(()=>{window.__k4.a.shell.position();return[window.__k4.a.shell.isOpen,window.__k4.a.menu.hidden];}),[false,true],'b3 position() on a stale menu closes it');
    await page.evaluate(()=>{const {a}=window.__k4;a.ctx.log.length=0;a.shell.open(300,200);a.ctx.throwOn='w1';});
    await page.locator(itemSel('k4a','w1')).click();
    check(await page.evaluate(()=>window.__k4.a.ctx.log.slice()),['error:boom w1'],'b3 an item that throws is reported through the adapter onError and does not break the shell');
    await page.evaluate(()=>{const {a}=window.__k4;a.ctx.throwOn=null;a.shell.hide();a.ctx.refuse=true;});
    check(await page.evaluate(()=>{const {a}=window.__k4;return[a.shell.open(300,200),a.shell.isOpen,a.menu.hidden];}),[false,false,true],'b3 begin() refusing keeps the menu closed');
    await page.evaluate(()=>{window.__k4.a.ctx.refuse=false;});

    // b4 keyboard on a shell menu: arrows, Home/End, Enter, IME, Esc and focus return.
    await page.evaluate(()=>{const {a}=window.__k4;a.ctx.log.length=0;a.shell.open(300,200);});
    const active=()=>page.evaluate(()=>document.activeElement.dataset.cmAct??document.activeElement.tagName);
    check(await active(),'INPUT','b4 search field is focused on open');
    await page.keyboard.press('ArrowDown');check(await active(),'v1','b4 ArrowDown focuses the first enabled item');
    await page.keyboard.press('ArrowDown');check(await active(),'n1','b4 ArrowDown moves on');
    await page.keyboard.press('End');check(await active(),'sub1','b4 End focuses the last item');
    await page.keyboard.press('ArrowDown');check(await active(),'v1','b4 ArrowDown wraps');
    await page.keyboard.press('ArrowUp');check(await active(),'sub1','b4 ArrowUp wraps back');
    await page.keyboard.press('Home');check(await active(),'v1','b4 Home focuses the first item');
    await page.keyboard.press('End');await page.keyboard.press('ArrowRight');
    check(await page.evaluate(()=>[document.querySelector('#k4aMenu .fcm-submenu [data-cm-act="s1"]')!==null,document.activeElement.dataset.cmAct]),[true,'s1'],'b4 ArrowRight opens the submenu and focuses its first item');
    await page.keyboard.press('ArrowLeft');check(await active(),'sub1','b4 ArrowLeft returns to the parent and closes the submenu');
    await page.keyboard.press('Home');await page.keyboard.press('ArrowDown');await page.keyboard.press('ArrowDown');check(await active(),'w1','b4 focus on the write item');
    await page.evaluate(()=>{document.activeElement.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',isComposing:true,bubbles:true,cancelable:true}));});
    check(await page.evaluate(()=>window.__k4.a.ctx.log.slice()),[],'b4 Enter during IME composition does not run the item');
    await page.keyboard.press('Enter');
    check(await page.evaluate(()=>window.__k4.a.ctx.log.slice()),['w1'],'b4 Enter on the focused item runs it');
    await page.evaluate(()=>{const {a}=window.__k4;a.ctx.log.length=0;a.shell.hide();a.shell.open(300,200);});
    await page.keyboard.press('Escape');
    check(await page.evaluate(()=>[window.__k4.a.shell.isOpen,window.__k4.a.menu.hidden,document.activeElement.id]),[false,true,'k4aViewport'],'b4 Esc closes the menu and returns focus to the adapter viewport');

    // b5 geometry: clamped inside the viewport on every side, submenu flips when the right side is too narrow.
    const inside=(id)=>page.evaluate(id=>{const v=document.getElementById(id+'Viewport').getBoundingClientRect(),m=document.getElementById(id+'Menu').getBoundingClientRect();
      return m.left>=v.left-1&&m.top>=v.top-1&&m.right<=v.right+1&&m.bottom<=v.bottom+1;},id);
    for(const [x,y] of [[5000,5000],[-300,-300],[5000,-300],[-300,5000]]){
      await page.evaluate(([x,y])=>{window.__k4.a.shell.hide();window.__k4.a.shell.open(x,y);},[x,y]);
      check(await inside('k4a'),true,`b5 menu opened at (${x},${y}) is clamped inside its viewport`);
    }
    await page.evaluate(()=>{window.__k4.a.shell.hide();window.__k4.a.shell.open(5000,100);});
    await page.locator(itemSel('k4a','sub1')).click();
    check(await page.evaluate(()=>{const v=document.getElementById('k4aViewport').getBoundingClientRect(),m=document.getElementById('k4aMenu').getBoundingClientRect(),
      s=document.querySelector('#k4aMenu .fcm-submenu').getBoundingClientRect();return[s.left<m.left,s.left>=v.left-1,s.right<=v.right+1];}),[true,true,true],'b5 submenu flips to the left edge when the right side has no room and stays inside the viewport');
    await page.evaluate(()=>window.__k4.a.shell.hide());

    // b6 outside pointer close is opt-in.
    await page.evaluate(()=>{
      window.__k4.a.shell.destroy();for(const id of ['k4aViewport','k4aMenu'])document.getElementById(id)?.remove();
      window.__k4.a=window.__k4.mk('k4a',{outsidePointerClose:true});window.__k4.a.shell.open(300,200);
    });
    await page.locator('#k4aMenu .fcm-head').dispatchEvent('pointerdown');
    check(await page.evaluate(()=>window.__k4.a.shell.isOpen),true,'b6 pointerdown inside the menu does not close it');
    await page.evaluate(()=>{document.body.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true}));});
    check(await page.evaluate(()=>window.__k4.a.shell.isOpen),false,'b6 pointerdown outside closes a menu that opted in');
    check(await page.evaluate(()=>{const {b}=window.__k4;b.shell.open(300,200);document.body.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true}));return b.shell.isOpen;}),true,
      'b6 a menu that did not opt in ignores outside pointerdown (the face editor closes itself in app.js)');
    // b7 destroy removes the shell's listeners.
    check(await page.evaluate(()=>{const {b}=window.__k4;b.shell.hide();b.shell.open(300,200);b.shell.destroy();
      document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true}));return[b.shell.isOpen,ContextMenuShell.active];}),[false,null],'b7 destroy() closes the menu and releases the instance');
    await page.evaluate(()=>{for(const n of ['k4a','k4b']){document.getElementById(n+'Viewport')?.remove();document.getElementById(n+'Menu')?.remove();}try{window.__k4.a.shell.destroy();}catch{}delete window.__k4;});

    check(errors,[],'no app page or console errors during the shell gate');
    fs.writeFileSync(path.join(evidence,'result.json'),JSON.stringify({phase:'full',checks,records,failures,errors,snapshotHash,runtime:runtime.version},null,2));
    console.log(JSON.stringify({phase:'full',checks,failures:failures.length,snapshotHash}));
  }finally{await browser.close();}
  if(failures.length)throw Error(failures.length+' check(s) failed:\n'+failures.join('\n'));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
