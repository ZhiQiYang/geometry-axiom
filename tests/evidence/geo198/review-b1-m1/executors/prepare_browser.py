from pathlib import Path
source=Path('/tmp/geometry-198-review-browser.cjs').read_text()
source=source.replace("out='/tmp/geometry-198-review/browser/targeted'", "out='/tmp/geometry-198-review2/browser/targeted'").replace('127.0.0.1:18842','127.0.0.1:18846')
source=source.replace('async function fixture(outline,item,width=1400){','async function fixture(outline,item,width=1400,z=0){').replace("async({outline,item})=>", "async({outline,item,z})=>").replace("'line surface 1 origin 0 0 0 u +x v +y outline '+outline", "'line surface 1 origin 0 0 '+z+' u +x v +y outline '+outline").replace('{outline,item});','{outline,item,z});')
anchor=" check('no uncaught app exceptions',"
extra="""
 {
  const context=await fixture(notch,['beam 1 along x from 30 to 70 at 65 width 30 depth 10 top 100'],1400,100);
  const before=await native('dump'),query=await native('obstacles 1');
  check('M1 original strip listed',query.ok&&query.items.length===1&&query.items[0].cls==='strip',query);
  await page.waitForFunction(()=>document.querySelectorAll('#faceProjectionEditor .fe-ob-check').length===1);
  await page.locator('#faceProjectionEditor .fe-ob-check').check();
  check('M1 cut-strip unchecked',!(await page.locator('#feCutStrip').isChecked()));
  await page.screenshot({path:path.join(out,'M1-before.png')});
  const responsePromise=page.waitForResponse(async r=>r.request().method()==='POST' && r.request().postData()?.includes('apply-proj 1 b1'));
  await page.locator('#feApplyProj').click();
  const response=await responsePromise,result=await response.json();
  check('M1 pointer apply succeeds',result.ok,result);
  const after=await native('dump');check('M1 pointer apply keeps complete dump',before.text===after.text,{before,after});
  await page.screenshot({path:path.join(out,'M1-after.png')});run.cases.push({name:'M1-pointer',query,before,result,after});await context.close();
 }
"""
assert source.count(anchor)==1
source=source.replace(anchor,extra+anchor)
Path('/tmp/geometry-198-review2/browser.cjs').write_text(source)
