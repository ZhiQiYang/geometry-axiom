/* Real component flow, same finite HTTP handler/native engine. Synthetic only.
   Uses installed Playwright: Browser plugin not available in this environment.
   Explicit isolated URL is required; no production app or storage is reset. */
'use strict';
const assert = require('node:assert/strict'), fs=require('node:fs'), os=require('node:os'), path=require('node:path');
const {chromium}=require('playwright');
const url=process.env.GEOMETRY_RULE_CASE_TEST_URL;
if(!url)throw new Error('GEOMETRY_RULE_CASE_TEST_URL is required');
const evidence=path.resolve(process.env.GEOMETRY_RULE_CASE_BROWSER_EVIDENCE || path.join(os.tmpdir(),'rule-case-workbench-browser'));
if(!evidence.startsWith(path.resolve(os.tmpdir())+path.sep))throw new Error('Browser evidence must remain in TEMP');
fs.mkdirSync(evidence,{recursive:true});
const ids=['same-role-distinct-members','one-local-joint-new-version','wrong-type-dimension-reference',
  'legal-rule','legal-incomplete-binding','fixed-version-immutable'];
let checks=0;const check=(value,message)=>{assert.equal(value,true,message);checks++;};
const gate=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};

(async()=>{
  const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME || '/usr/bin/chromium',headless:true,
    args:['--no-sandbox']});
  const results=[];
  try{
    for(const width of [1280,390]){
      const context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage();
      const unexpected=[];page.on('pageerror',error=>unexpected.push(error.message));
      page.on('console',message=>{if(['error','warning'].includes(message.type()))unexpected.push(message.text());});
      await page.goto(url);await page.locator('[data-rcw=run]').waitFor();
      check(await page.title()==='規則案例 · 獨立接線驗證','page identity');
      check((await page.locator('nav [data-case-id]').count())===6,'six meaningful templates');
      check(!await page.locator('#__next-build-watcher,nextjs-portal,.vite-error-overlay').count(),'no framework overlay');
      check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'first viewport no horizontal overflow');
      await page.screenshot({path:path.join(evidence,`${width}-initial.png`)});
      for(const id of ids){
        await page.locator(`[data-case-id="${id}"]`).click();
        check(await page.locator('[data-rcw=selected-title]').evaluate(el=>el===document.activeElement),'selected heading receives focus');
        await page.locator('[data-rcw=run]').click();
        await page.locator('[data-rcw=result]').filter({hasText:'本次核對 · 通過'}).waitFor();
        const expected=id==='wrong-type-dimension-reference'||id==='fixed-version-immutable'?'拒絕':'接受';
        const values=await page.locator('[data-rcw=result] dd').allTextContents();
        check(values[0]===expected&&values[1]===expected,'expected and actual distinct columns');
        check(await page.locator('#retained').innerText()==='metadata history: 0','runs/display do not write host history');
        if(id==='wrong-type-dimension-reference'){
          const raw=await page.locator('details').filter({has:page.locator('summary',{hasText:'原生診斷與核對明細'})}).innerText();
          check(raw.includes('DIMENSION_TYPE')&&raw.includes('D33')&&raw.includes('"id": 41')&&raw.includes('"fieldId": 9'),'precise negative parameter diagnostic');
          await page.screenshot({path:path.join(evidence,`${width}-dimension-diagnostic.png`),fullPage:true});
        }
        if(id==='fixed-version-immutable'){
          const raw=await page.locator('details').filter({has:page.locator('summary',{hasText:'原生診斷與核對明細'})}).innerText();
          check(raw.includes('RULE_VERSION_IMMUTABLE')&&raw.includes('D32')&&raw.includes('"version": 1'),'precise immutable diagnostic');
        }
      }
      // Keyboard can return to the list and activate a case.
      const legal=page.locator('[data-case-id="legal-rule"]');await legal.focus();await page.keyboard.press('Enter');
      check(await page.locator('[data-rcw=selected-title]').innerText()==='合法規則可獨立發布','keyboard template selection');
      if(width===390){await page.locator('[data-rcw=back]').click();
        check(await legal.evaluate(el=>el===document.activeElement),'mobile back returns focus to case list');}
      const beforeHistory=await page.locator('#retained').innerText();
      await page.locator('input[name=label]').fill('<img src=x onerror=alert(1)>');
      await page.getByRole('button',{name:'採用有限修改',exact:true}).click();
      await page.locator('[data-rcw=result]').filter({hasText:'歷史未核信 · 已過期'}).waitFor();
      check(await page.locator('[data-rcw=selected-title]').innerText()==='<img src=x onerror=alert(1)>','label rendered as text');
      check(await page.locator('#workbench img').count()===0,'no executable markup');
      check(await page.locator('#retained').innerText()===beforeHistory,'editing remains detached until retain');
      await page.locator('select[name=jointSide]').selectOption('-u');
      await page.getByRole('button',{name:'採用有限修改',exact:true}).click();
      await page.locator('[data-rcw=status]').filter({hasText:'案例修改已核對'}).waitFor();
      await page.locator('[data-rcw=run]').click();
      await page.locator('[data-rcw=result]').filter({hasText:'本次核對 · 驗證失敗'}).waitFor();
      check((await page.locator('[data-rcw=result] dd').allTextContents())[1]==='接受','actual acceptance does not falsely imply pass');
      await page.locator('[data-rcw=reset]').click();
      await page.locator('[data-rcw=status]').filter({hasText:'已還原模板'}).waitFor();
      await page.locator('[data-rcw=run]').click();await page.locator('[data-rcw=result]').filter({hasText:'本次核對 · 通過'}).waitFor();
      await page.locator('[data-rcw=retain]').click();await page.locator('#retained').filter({hasText:'metadata history: 1'}).waitFor();
      await page.locator('[data-rcw=retain]').click();await page.locator('[data-rcw=status]').filter({hasText:'案例資料未變更'}).waitFor();
      check(await page.locator('#retained').innerText()==='metadata history: 1','no-op retain adds no metadata step');
      await page.locator('#restore').click();
      await page.locator('[data-rcw=result]').filter({hasText:'歷史未核信 · 通過'}).waitFor();
      check(await page.locator('nav [data-case-id]').filter({hasText:'本次 · 通過'}).count()===0,'import cannot restore current trust');
      await page.screenshot({path:path.join(evidence,`${width}-historical.png`),fullPage:true});
      // Delay a REAL response after route.fetch completes native execution.
      for(const action of ['cancel','close','edit']){
        const reached=gate(),release=gate();let held=false;
        await page.route('**/rule-cases/workbench',async route=>{
          const payload=route.request().postDataJSON();
          if(payload.action==='run'&&!held){held=true;const response=await route.fetch();reached.resolve();await release.promise;
            try{await route.fulfill({response});}catch{}return;}
          await route.continue();
        });
        await page.locator('[data-rcw=run]').click();await reached.promise;
        check((await page.locator('[data-rcw=result]').innerText()).includes('執行中'),'running remains distinct from previous receipt');
        if(action==='cancel'){
          await page.locator('[data-rcw=cancel]').click();
          await page.locator('[data-rcw=status]').filter({hasText:'已取消'}).waitFor();
        }else if(action==='close'){
          await page.locator('[data-rcw=close]').click();await page.locator('#reopen').click();await page.locator('[data-rcw=run]').waitFor();
        }else{
          await page.locator('input[name=label]').fill('changed during held old result');
          await page.getByRole('button',{name:'採用有限修改',exact:true}).click();
          await page.locator('[data-rcw=status]').filter({hasText:'案例修改已核對'}).waitFor();
        }
        const before=await page.locator('#workbench').innerText();release.resolve();
        // Wait for the interception to drain using a harmless real adapter response.
        await page.request.post(new URL('/rule-cases/workbench',url).href,{data:{protocol:'rule-case-workbench/1',action:'close',sessionId:'nonexistent'}});
        await page.waitForTimeout(100);
        check(await page.locator('#workbench').innerText()===before,'late response does not paint after '+action);
        check(await page.locator('#retained').innerText()==='metadata history: 1','late response does not write history');
        await page.unroute('**/rule-cases/workbench');
      }
      check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'final viewport no horizontal overflow');
      check(unexpected.length===0,'no unexpected console/page errors: '+unexpected.join('; '));
      results.push({viewport:{width,height:900},unexpectedConsole:unexpected,checksCompleted:checks});
      await page.locator('[data-rcw=close]').click();await context.close();
    }
    fs.writeFileSync(path.join(evidence,'browser.json'),JSON.stringify({url,checks,results},null,2));
    console.log(JSON.stringify({checks,results,evidence}));
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
