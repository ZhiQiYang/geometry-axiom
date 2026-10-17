const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),cp=require('child_process');
const root='/workspace/geometry-axiom',out='/tmp/geometry-198-review/browser/targeted';
fs.mkdirSync(out,{recursive:true});
const run={head:cp.execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),url:'http://127.0.0.1:18842/',browserPlugin:'Browser plugin not available',browser:'/usr/bin/chromium',checks:[],cases:[],consoleErrors:[],exceptions:[],scope:'Real rendered app; API-seeded independent native fixtures; pointer activates original shape tab and apply control. Not formal WSL or full seven jobs.'};
const check=(name,value,detail)=>{run.checks.push({name,ok:value===true,detail});if(value!==true)throw Error(name+': '+JSON.stringify(detail));};
let browser,page;
async function fixture(outline,item,width=1400){
 const context=await browser.newContext({viewport:{width,height:900}});
 page=await context.newPage();page.on('console',m=>{if(m.type()==='error')run.consoleErrors.push(m.text());});page.on('pageerror',e=>run.exceptions.push(e.message));
 await page.goto(run.url);await page.waitForFunction(()=>typeof api==='function'&&connection.phase==='ready');
 await page.evaluate(async({outline,item})=>{for(const cmd of ['line reset','line surface 1 origin 0 0 0 u +x v +y outline '+outline,...item.map(x=>'line '+x)]){const r=await api(cmd);if(!r.ok)throw Error(cmd+': '+JSON.stringify(r));}await renderObjects();await enterFocus('face',1);},{outline,item});
 await page.waitForFunction(()=>oc.edit?.bid===1 && !oc.busy);
 if(width<680&&await page.locator('#workspaceToggleRight').isVisible())await page.locator('#workspaceToggleRight').click();
 await page.locator('#faceInspectorTabs [data-fi-tab="shape"]').click();
 return context;
}
const native=cmd=>page.evaluate(cmd=>api(cmd),cmd);
async function main(){
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox'],headless:true});
 const notch='0,0 100,0 100,100 60,100 60,40 40,40 40,100 0,100',ridge='0,0 100,0 100,50 60,50 60,90 40,90 40,50 0,50';
 for(const [name,item,cut,width] of [['B-column',['column 1 at 20 70 size 60 10 z 0 100'],false,1400],['B-beam',['beam 1 along x from 20 to 80 at 75 width 10 depth 100 top 100'],true,1400],['B-mobile',['column 1 at 20 70 size 60 10 z 0 100'],false,390]]){
  const context=await fixture(ridge,item,width);
  const title=await page.title(),body=await page.locator('body').innerText();
  check(name+' page identity',page.url()===run.url&&title.length>0,{title});check(name+' meaningful page',body.length>100);check(name+' no framework overlay',await page.locator('vite-error-overlay,nextjs-portal').count()===0);
  const query=await native('obstacles 1');check(name+' exact native contact',query.ok&&query.items.length===1&&(!cut?query.items[0].cls==='split':query.items[0].cls==='strip'),query);
  if(!cut)check(name+' exact clipped rectangle',JSON.stringify(query.items[0].rect)==='[40,70,60,80]',query.items[0]);
  await page.waitForFunction(()=>document.querySelectorAll('#faceProjectionEditor .fe-ob-check').length===1);
  await page.locator('#faceProjectionEditor .fe-ob-check').check();if(cut)await page.locator('#feCutStrip').check();
  await page.screenshot({path:path.join(out,name+'-before.png')});
  await page.locator('#feApplyProj').click();
  let after;for(let i=0;i<100;i++){after=await native('dump');if(after.ok&&after.text.includes('boundary 2 outline'))break;await page.waitForTimeout(50);}
  check(name+' original pointer apply splits actual geometry',after.ok&&after.text.includes('boundary 2 outline')&&after.text.includes('60,70')&&after.text.includes('40,80'),after);
  const boundary=await native('boundary 1');
  await page.waitForFunction(loops=>JSON.stringify(oc.bmap[1])===JSON.stringify(loops),boundary.loops,{timeout:15000});
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  check(name+' UI boundary follows actual native split',true);
  if(!cut)await page.waitForFunction(()=>document.querySelectorAll('#faceProjectionEditor .fe-ob-check').length===0&&document.querySelectorAll('#faceEditorRoot .obstacle-ghost').length===0,{},{timeout:15000});
  const postQuery=await native('obstacles 1'),ghostCount=await page.locator('.obstacle-ghost').count();
  await page.screenshot({path:path.join(out,name+'-after.png')});run.cases.push({name,width,query,after,boundary,postQuery,ghostCount,...(cut?{limitation:'Beam initial strip/bbox path can retain a ghost after applying; general exact ghost clipping is outside this fix.'}:{})});await context.close();
 }
 for(const mixed of [false,true]){
  const name=mixed?'A-mixed':'A';const context=await fixture(notch,['column 1 at 30 50 size 40 30 z 0 100',...(mixed?['column 2 at 10 10 size 10 10 z 0 100']:[])]);
  const query=await native('obstacles 1'),before=await native('dump'),rejected=await native('line apply-proj 1 c1'),after=await native('dump');
  check(name+' query explicit R7',!query.ok&&query.error.startsWith('R7:'),query);check(name+' selected invalid item rejected and rollback',!rejected.ok&&/(^|: )R7: 投影接觸非單一矩形或僅相切（退化，不猜）$/.test(rejected.error)&&after.text===before.text,{rejected});
  check(name+' renders no fabricated ghost or selectable row',await page.locator('.obstacle-ghost,#faceProjectionEditor .fe-ob-check').count()===0);
  const ui=await page.locator('#faceLayerList').innerText().catch(()=>page.locator('body').innerText());
  const valid=mixed?await native('line apply-proj 1 c2'):null;if(mixed)check(name+' direct valid item accepted',valid.ok,valid);
  await page.screenshot({path:path.join(out,name+'.png')});run.cases.push({name,query,before,rejected,after,valid,ui,limitation:'obstacles error suppresses the whole UI list; direct c2 success does not prove UI can select it.'});await context.close();
 }
 check('no uncaught app exceptions',run.exceptions.length===0,run.exceptions);check('console health',run.consoleErrors.length===0,run.consoleErrors);
}
main().catch(async error=>{run.error=error.stack;process.exitCode=1;if(page)await page.screenshot({path:path.join(out,'fatal.png')}).catch(()=>{});}).finally(async()=>{run.passed=run.checks.filter(c=>c.ok).length;run.failed=run.checks.filter(c=>!c.ok).length;fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(run,null,2)+'\n');console.log(JSON.stringify({passed:run.passed,failed:run.failed,error:run.error}));await browser?.close();});
