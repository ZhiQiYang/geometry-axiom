'use strict';
// T36 局部回歸；只對自有的空白測試服務執行，不是 canvas 量測或冷開驗收。
const {chromium}=require('playwright-core');
const assert=require('node:assert/strict');
const {spawn,execFile}=require('node:child_process');
const {createInterface}=require('node:readline');
const {mkdtemp,rm}=require('node:fs/promises');
const {tmpdir}=require('node:os');
const path=require('node:path');
const exec=require('node:util').promisify(execFile);
const root=path.resolve(__dirname,'../..');

// URL 只指定要綁定的空埠，絕不沿用現有服務。start_local 以 exec 換成 serve，PID 不變。
async function withOwnService(port,visit){
  const feedback=await mkdtemp(path.join(tmpdir(),'pf6-review-'));
  const child=spawn('python3',['-Bu','geometry-web/start_local.py','--port',port],{cwd:root,
    env:{...process.env,GEOMETRY_FEEDBACK_DIR:feedback},stdio:['ignore','pipe','inherit']});
  const closed=new Promise(resolve=>child.once('close',resolve));
  const output=createInterface({input:child.stdout});
  try{
    await new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>reject(Error('專用服務未就緒')),60000);
      output.on('line',line=>{if(line.startsWith(`http://localhost:${port} `)){clearTimeout(timer);resolve();}});
      child.once('error',reject);closed.then(()=>{clearTimeout(timer);reject(Error('專用服務已退出'));});
    });
    const {stdout}=await exec('python3',['-B','geometry-web/runtime_version.py','--probe',port],{cwd:root});
    const runtime=JSON.parse(stdout);
    assert.ok(child.exitCode===null&&child.signalCode===null&&runtime.pid===child.pid&&typeof runtime.session==='string'&&runtime.session,'T39_DIAGNOSTIC_SERVICE_OWNER');
    await visit(runtime);
  }finally{
    child.kill('SIGINT');await closed;output.close();await rm(feedback,{recursive:true,force:true});
  }
}
async function run(url,width,mode){
  const {port}=new URL(url);assert.ok(port&&url===`http://127.0.0.1:${port}/`);assert.ok([390,1400].includes(width));
  assert.ok(['suggested','selected','d28','details'].includes(mode));
  await withOwnService(port,runtime=>exercise(url,width,mode,runtime));
}
async function exercise(url,width,mode,runtime){
  const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/google-chrome',headless:true});
  try{
    const page=await browser.newPage({viewport:{width,height:width===390?844:900}});
    page.setDefaultTimeout(15000);await page.goto(url);await page.waitForFunction(()=>connection.phase==='ready');
    assert.equal(page.url(),url);
    assert.ok(await page.evaluate(async expected=>{
      const response=await fetch('/runtime',{redirect:'error'}),current=await response.json();
      return response.ok&&current.fresh===true&&current.pid===expected.pid&&current.version===expected.version&&
        current.session===expected.session&&connection.session===expected.session;
    },runtime),'T39_DIAGNOSTIC_PAGE_OWNER');
    await page.evaluate(async d28=>{
      const cmd=async text=>{const r=await apiRequest(text);if(!r.ok)throw Error(text+': '+r.error);return r;};
      async function apply(route,schema,command,operations){
        const expectedRevision=(await cmd('panel-fill-read')).revision;
        const r=await (await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema,expectedRevision,operations})})).json();
        if(!r.ok||!r.preview?.valid)throw Error('fixture: '+JSON.stringify(r).slice(0,2000));
        await cmd(command+' '+r.preview.token);
      }
      resetSceneFocus();await setView3(false);await cmd('reset');await cmd('line boundary 8 outline 0,0 300,0 300,300 0,300 kind room_plan');
      const ops=[{op:'publish-material',value:{id:'board',version:1,name:'面板',kind:'panel',width:100,length:100,thickness:'9'}},
        {op:'put-parameter',value:{id:90,name:'門檻',fields:[{id:1,name:'X',type:'dimension',input:'8'}]}}];
      if(d28){
        await cmd('line surface 9 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000');
        await cmd('line timber 10 27 33 role boundary');await cmd('line place 10 on 9 at-face e0 +u +n');
        ops.push({op:'publish-material',value:{id:'wood',version:1,kind:'timber',name:'邊材',A:30,B:33}},
          {op:'publish-method',value:{id:'frame',version:1,name:'做法',roles:{boundary:{id:'wood',version:1}}}},
          {op:'put-application',value:{id:'other-face',placement_id:9,method:{id:'frame',version:1}}},
          {op:'bind-timber',id:10,application:'other-face',slot:'boundary'});
      }
      await apply('/engineering/preview','engineering-transaction/1','engineering-confirm',ops);
      await apply('/panel-fill/preview','panel-fill-transaction/1','panel-fill-confirm',[
        {op:'put-finish-surface',value:{id:1,name:'測試面',boundaryId:8,frame:{origin:[0,0,0],U:'+X',V:'+Y',N:'+Z'},structureSide:1,obstacles:[]}},
        {op:'put-panel-fill',value:{id:1,finishSurfaceId:1,panel:{id:'board',version:1},lengthAlong:'v',origin:[0,0],gap:3,pattern:'straight',threshold:{parameterId:90,fieldId:1}}}]);
      await renderObjects();
    },mode==='d28');
    const row=page.locator('.object-row[data-kind="boundary"][data-id="8"]');
    if(width===390)await page.locator('#toggleLeft').click();
    await row.dblclick();await page.waitForFunction(()=>oc.focus?.t==='face'&&oc.focus.id===8);
    if(width===390)await page.locator('#workspaceToggleRight').click();
    for(const selector of ['[data-fi-tab="prop"]','[data-face-settings="8"]','[data-panel-fill-open="8"]','[data-pf-action="suggest-timbers"][data-pf-fill-id="1"]'])await page.locator(selector).click();
    const field=name=>page.locator(`[data-pf6-field="${name}"]`),action=name=>page.locator(`[data-pf6-action="${name}"]`);
    for(const [slot,mm] of [['A','27'],['B','30']]){await field(slot+'.kind').selectOption('literal');await field(slot+'.value').fill(mm);}
    await field('primaryAlong').selectOption('u');
    const before=()=>page.evaluate(async()=>({dump:(await apiRequest('dump')).text,project:ReferenceWorkspace.getProjectState(),undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length}));
    const pin=await before();const cancels=[];
    page.on('request',r=>{if(r.url().endsWith('/api')&&r.postDataJSON()?.cmd?.startsWith('pf6-cancel '))cancels.push(r.postDataJSON().cmd);});
    const reply=page.waitForResponse(r=>r.url().endsWith('/builder/suggest'));await action('suggest').click();const suggestion=await (await reply).json();
    assert.ok(suggestion.valid&&suggestion.appView.completeForScope);
    if(mode==='d28')assert.deepEqual(suggestion.appView.timbers.find(t=>t.id===10).before.A.source,{kind:'application',field:'boundary.A',id:'other-face'});
    await page.waitForFunction(()=>['suggested','rejected'].includes(document.querySelector('[data-pf6-status]')?.dataset.pf6Status));
    assert.equal(await page.locator('[data-pf6-status]').getAttribute('data-pf6-status'),'suggested','T36_NATIVE_SUGGEST '+mode);
    let token=null;
    if(mode!=='suggested'){
      await action('all').click();const response=page.waitForResponse(r=>r.url().endsWith('/builder/select'));await action('preview').click();
      const {preview}=await (await response).json();assert.ok(preview.valid&&preview.token>0);token=preview.token;
      await page.waitForFunction(()=>!document.querySelector('[data-pf6-action="confirm"]').disabled);
      if(mode==='details'){
        const after=preview.appView.uiContract.after,area=page.locator('.pf6-results');
        const summary=area.locator('summary').filter({hasText:'裁片與來源明細'});
        assert.equal(await summary.count(),1,'T36_DOM_SELECTED_DETAILS disclosure');await summary.click();
        const text=await summary.locator('..').innerText();
        for(const [name,v] of [['fragment',after.panelFills[0].derived.tiles[0].fragments[0].key],['edge',after.derivedPlacements[0].derived.components[0].edges[0].key]])assert.ok(text.includes(JSON.stringify(v)),'T36_DOM_SELECTED_DETAILS '+name);
      }
    }
    if(mode==='suggested'||mode==='selected'){
      // 保存和開檔在持租約時原本就必須拒絕；不能只把 pending 改成 false。
      await assert.rejects(page.evaluate(()=>ReferenceWorkspace.exportBytes()),/角材建議/);
      await assert.rejects(page.evaluate(()=>ReferenceWorkspace.openProject(()=>{throw Error('不應進入讀檔');})),/角材候選尚未結束，請先確認或取消。/);
      // 呼叫實際退役的場景焦點事件，不從測試代按已不存在的取消鈕。
      await page.evaluate(()=>resetSceneFocus());
      if(token!==null)await page.waitForFunction(()=>!window.PanelFillBuilderWorkspace.pending,{},{timeout:15000}).catch(()=>{});
      assert.equal(await page.evaluate(()=>window.PanelFillBuilderWorkspace.pending),false,'T36_DOM_RETIRED_OWNER_BLOCKS_PROJECT '+mode);
    }else await action('cancel').click();
    await page.waitForFunction(()=>!window.PanelFillBuilderWorkspace.pending);
    assert.deepEqual(cancels,token===null?[]:['pf6-cancel '+token]);assert.deepEqual(await before(),pin);
    if(mode==='suggested'||mode==='selected'){
      const reopened=await page.evaluate(async()=>{
        const bytes=await ReferenceWorkspace.exportBytes();await ReferenceWorkspace.openProject(()=>bytes,'退役後往返');
        return {bytes:bytes.length,dump:(await apiRequest('dump')).text};
      });
      assert.ok(reopened.bytes>0);assert.equal(reopened.dump,pin.dump);console.log('T36_PROJECT_EXPORT_OPEN exact dump');
    }
    console.log(`T36_BROWSER ${width}px ${mode} OK; exact cancellations=${cancels.length}; world/project/history unchanged`);
  }finally{await browser.close();}
}
const [url,width,mode]=process.argv.slice(2);run(url,Number(width),mode).catch(e=>{console.error(e);process.exitCode=1;});
