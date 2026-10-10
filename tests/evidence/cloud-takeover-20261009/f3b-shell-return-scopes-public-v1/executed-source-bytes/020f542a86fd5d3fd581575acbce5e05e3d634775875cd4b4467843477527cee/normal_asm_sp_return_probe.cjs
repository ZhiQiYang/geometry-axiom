/* Prepared caller-owned Playwright helper only. No browser/service is launched.
 * Root may use it after the frozen integration slot is released; it cannot run
 * on a user service. Original ASSEMBLY_ONLY already covers ASM's full workflow.
 * This bounded helper records normal ASM/SP entry/Cancel/return geometry and
 * exact native preservation. It is not full CDP/Space or all43 acceptance. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
module.exports=async function normalWorkspaceReturnProbe({page,root,expectedSHA,url,output,isolatedService}){
  if(isolatedService!==true||!/^[a-f0-9]{40}$/.test(expectedSHA))throw Error('Explicit isolated service and full SHA required');
  const address=new URL(url);
  if(address.protocol!=='http:'||!['localhost','127.0.0.1'].includes(address.hostname)||!address.port||address.port==='8765'||address.pathname!=='/')throw Error('Dedicated local test service required');
  const sha=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
  const git=args=>execFileSync('git',args,{cwd:root,encoding:'utf8'}).trim();
  if(git(['rev-parse','HEAD'])!==expectedSHA||git(['status','--porcelain']))throw Error('Caller candidate must be frozen clean');
  const results=[],measurements=[],trusted=[],checks=[];
  const check=(name,ok,detail)=>{checks.push({name,ok:ok===true,detail});if(ok!==true)throw Error(name);};
  const dump=()=>page.evaluate(async()=>{const r=await api('dump');if(!r.ok||typeof r.text!=='string')throw Error('Native dump failed');return r.text;});
  const settle=()=>page.waitForFunction(()=>connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy,null,{timeout:20000});
  const geometry=selector=>page.locator(selector).evaluate(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e),x=r.x+r.width/2,y=r.y+r.height/2,h=document.elementFromPoint(x,y);return {selector:e.id,rect:{left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height},center:{x,y},position:s.position,display:s.display,hit:!!h&&e.contains(h),hitElement:h?.tagName+'#'+h?.id,disabled:!!e.disabled,insideViewport:r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight};});
  const normalClick=async selector=>{await page.locator(selector).scrollIntoViewIfNeeded();const p=await geometry(selector);check('one normal physical click precondition '+selector,p.hit&&!p.disabled&&p.rect.width>0&&p.rect.height>0&&p.insideViewport,p);await page.locator(selector).click();await settle();};
  async function openCreate(entry){
    const candidates=[];
    for(const selector of ['#btnCreateObject','#mobileCreateObject'])if(await page.locator(selector).isVisible())candidates.push(selector);
    check('unique visible original Create entry',candidates.length===1,candidates);
    await normalClick(candidates[0]);await normalClick(entry);
  }
  const start={head:git(['rev-parse','HEAD']),dirty:git(['status','--porcelain']),sourceSHA256:sha(__filename),expectedSHA};
  fs.mkdirSync(output,{recursive:false});
  let error=null;
  try{
    for(const width of [1400,390]){
      await page.setViewportSize({width,height:1000});await page.goto(url);await settle();
      await page.evaluate(()=>{window.__normalShellTrusted=[];for(const type of ['pointerdown','pointerup','click'])document.addEventListener(type,e=>{const b=e.target.closest?.('#asmClose,#spClose');if(b)window.__normalShellTrusted.push({type,isTrusted:e.isTrusted,id:b.id});},true);});
      for(const [family,entry,dialog,close,cancel] of [['ASM','#btnNewAssembly','#assemblyWorkspace','#asmClose',null],['SP','#btnNewSectionProfile','#sectionProfileWorkspace','#spClose','#spCancel']]){
        const before=await dump(),bar=await page.$('#projectBar');
        await openCreate(entry);await page.waitForFunction(selector=>document.querySelector(selector)?.open,dialog,{timeout:20000});
        const row=await geometry(dialog+' > .workspace-project-header'),button=await geometry(close);
        const identity=await page.evaluate((bar)=>{const active=[...document.querySelectorAll('dialog[open]')];return {barSame:bar===document.getElementById('projectBar'),oneBar:document.querySelectorAll('#projectBar').length===1,insideActive:active.length===1&&active[0].contains(bar)};},bar);
        check(width+' '+family+' shared original row stays normal flow',row.position==='relative'&&identity.barSame&&identity.oneBar&&identity.insideActive,{row,identity});
        check(width+' '+family+' actual return center hits original control',button.hit&&!button.disabled&&button.insideViewport&&button.rect.height>=44&&row.rect.bottom<=button.rect.top,{row,button});
        measurements.push({width,family,row,button,identity});
        // Existing empty SP entry creates a local unsaved draft; honor its
        // original explicit Cancel guard before returning, never bypass state.
        if(cancel&&await page.locator(cancel).isEnabled()){await normalClick(cancel);
          // Original cancel() reads five native responses before its finally
          // restores controls. Observe that original completion once; do not
          // retry the click or bypass a busy/dirty guard. Preserve all40 checks.
          await page.waitForFunction(()=>document.getElementById('spStatus')?.textContent==='已取消修改，未改動世界。'&&document.getElementById('spCancel')?.disabled===true&&document.getElementById('spClose')?.disabled===false,null,{timeout:20000});
          check(width+' SP original Cancel preserves exact native dump',await dump()===before);}
        const count=await page.evaluate(()=>window.__normalShellTrusted.length);
        await normalClick(close);await page.waitForFunction(selector=>!document.querySelector(selector)?.open,dialog,{timeout:20000});
        const events=await page.evaluate(n=>window.__normalShellTrusted.slice(n),count);
        check(width+' '+family+' one original trusted return gesture',events.length===3&&events.every(e=>e.isTrusted&&e.id===close.slice(1))&&events.map(e=>e.type).join(',')==='pointerdown,pointerup,click',events);
        check(width+' '+family+' exact native full dump unchanged',await dump()===before);
        check(width+' '+family+' same original project bar returns home',await page.evaluate(bar=>bar===document.getElementById('projectBar')&&!bar.closest('.workspace-project-header')&&document.querySelectorAll('#projectBar').length===1,bar));
        trusted.push({width,family,events});results.push({width,family,completed:true});await bar.dispose();
      }
    }
  }catch(e){error={message:e.message,stack:e.stack};}
  const finish={head:git(['rev-parse','HEAD']),dirty:git(['status','--porcelain'])};
  const receipt={schema:'geometry-shared-row-normal-return-probe/1',startedSource:start,finishedSource:finish,checks,results,measurements,trusted,error,
    completed:!error&&results.length===4&&finish.head===expectedSHA&&finish.dirty==='',scope:{families:['ASM','SP'],widths:[1400,390],input:'Original normal Create/entry/optional existing SP Cancel/return pointer controls',fixture:'Existing isolated native world; no geometry mutation or injected UI state',notCovered:['full ASM workflows or save/reopen beyond original formal harness','full CDP/golden','full standalone Space','physical touch/IME','all43/privateZIP']}};
  fs.writeFileSync(path.join(output,'results.json'),JSON.stringify(receipt,null,2)+'\n');
  if(error)throw Object.assign(Error(error.message),{probeReceipt:receipt});
  return receipt;
};
