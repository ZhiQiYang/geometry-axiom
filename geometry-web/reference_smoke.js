/* Focused real-browser acceptance for the new reference workflow.
 * Same Chrome/environment configuration as cdp_test.js; uses its own CDP port.
 */
const {spawn}=require('child_process');
const fs=require('fs'), path=require('path'), os=require('os');
const port=9334;
const chrome=spawn(process.env.GEOMETRY_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
 ['--headless=new','--disable-gpu',`--remote-debugging-port=${port}`,'--window-size=1160,900',
  `--user-data-dir=${path.join(os.tmpdir(),'geometry-reference-smoke')}`,
  ...(process.env.GEOMETRY_CHROME_FLAGS||'').split(' ').filter(Boolean),'about:blank']);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let ws,seq=0,checks=0;const pending=new Map(),errors=[];
function send(method,params={}) {return new Promise((resolve,reject)=>{const id=++seq;
 const timer=setTimeout(()=>{pending.delete(id);reject(Error('CDP timeout '+method))},15000);
 pending.set(id,r=>{clearTimeout(timer);r.error?reject(Error(JSON.stringify(r.error))):resolve(r.result)});
 ws.send(JSON.stringify({id,method,params}));});}
async function evaluate(expression) {const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
 if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);return r.result.value;}
function check(name,ok) {if(!ok)throw Error(name);checks++;console.log('PASS '+name);}
async function waitFor(expression) {for(let i=0;i<80;i++){if(await evaluate(expression))return;await sleep(50);}throw Error('UI timeout '+expression);}
async function click(selector) {const p=await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);
 for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,...p,button:'left',clickCount:1});}
(async()=>{
 let page;
 for(let i=0;i<60;i++){try{page=(await fetch(`http://127.0.0.1:${port}/json`).then(r=>r.json())).find(x=>x.type==='page');if(page)break;}catch{}await sleep(100);}
 if(!page)throw Error('Chrome unavailable');
 ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
 ws.onmessage=ev=>{const m=JSON.parse(ev.data);if(m.id&&pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id)}
 else if(m.method==='Runtime.exceptionThrown')errors.push(m.params);};
 await send('Runtime.enable');await send('Page.enable');
 await send('Page.navigate',{url:process.env.GEOMETRY_TEST_URL||'http://localhost:8765/'});
 await waitFor(`typeof apiRequest==='function' && typeof oc!=='undefined' && !oc.busy`);
 await evaluate(`(async()=>{await apiRequest('default');resetSceneFocus();await renderObjects();await enterFocus('face',1);fiShowTab('prop')})()`);
 check('reference form available',await evaluate(`!!document.querySelector('#refSpecSave') && !!document.querySelector('#refGuideExpr')`));
 check('form fits inspector',await evaluate(`(()=>{const e=document.querySelector('#faceInspectorContent');return e.scrollWidth<=e.clientWidth+1})()`));
 const before=(await evaluate(`apiRequest('dump')`)).text;
 await evaluate(`document.querySelector('#refSpecName').value='主支中線';document.querySelector('#refSpecValue').value='900';void 0`);
 await click('#refSpecSave');await waitFor(`!!document.querySelector('dialog.reference-impact[open]')`);
 check('old/new center and length shown',await evaluate(`document.querySelector('dialog').innerText.includes('500 → 900') && document.querySelector('dialog').innerText.includes('2946 → 2946')`));
 check('candidate never mutates live world',(await evaluate(`apiRequest('dump')`)).text===before);
 const shot=await send('Page.captureScreenshot',{format:'png'});
 fs.writeFileSync(process.env.GEOMETRY_IMPACT_SCREENSHOT||path.join(os.tmpdir(),'geometry-impact.png'),Buffer.from(shot.data,'base64'));
 await click('#impact-confirm');await waitFor(`!document.querySelector('dialog.reference-impact') && !oc.busy`);
 check('confirm updates timber',await evaluate(`apiRequest('references').then(r=>r.timbers.find(t=>t.id===3).geometry.centerline===900)`));
 await evaluate(`window.__result=api('line spec 主支中線 1200');void 0`);await waitFor(`!!document.querySelector('dialog.reference-impact[open]')`);
 await click('.impact-actions button:first-child');await waitFor(`!document.querySelector('dialog.reference-impact')`);
 check('cancel preserves world',await evaluate(`apiRequest('references').then(r=>r.timbers.find(t=>t.id===3).geometry.centerline===900)`));
 await evaluate(`window.__result=api('line spec 主支中線 0');void 0`);await waitFor(`!!document.querySelector('dialog.reference-impact[open]')`);
 check('invalid preview cannot confirm',await evaluate(`document.querySelector('#impact-confirm').disabled && document.querySelectorAll('.impact-violation').length>0`));
 await click('.impact-actions button:first-child');await waitFor(`!document.querySelector('dialog.reference-impact')`);
 await evaluate(`apiRequest('line undo')`);
 check('undo restores original', (await evaluate(`apiRequest('dump')`)).text===before);
 await evaluate(`(async()=>{resetSceneFocus();await apiRequest('reset');for(const line of [
 'surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000 hole 1000,1000 2000,1000 2000,2000 1000,2000',
 'spec 孔中線 1500','guide 1 1 v spec:孔中線','grid 1 on 1 u panel 400 gap 3']){const r=await apiRequest('line '+line);if(!r.ok)throw Error(r.error)}
 await renderObjects();await enterFocus('face',1)})()`);
 check('reference lines and hit regions are clipped',await evaluate(`document.querySelector('.face-reference-line').parentElement.getAttribute('clip-path')==='url(#face-material-clip)' && document.querySelector('#face-material-clip path').getAttribute('clip-rule')==='evenodd'`));
 check('hole cannot pick guide',await evaluate(`(()=>{const svg=document.querySelector('#faceEditorSvg'),p=svg.createSVGPoint();p.x=1500;p.y=1500;const q=p.matrixTransform(document.querySelector('#faceEditorRoot').getScreenCTM());return !document.elementFromPoint(q.x,q.y)?.closest('[data-face-hit^="g:"]')})()`));
 check('odd panel gap rendered',await evaluate(`fe.grids[0].u[0]===401 && document.querySelectorAll('.face-grid-line').length>0`));
 check('no uncaught browser exceptions',errors.length===0);
 await evaluate(`apiRequest('default')`);
 console.log(`${checks} passed / 0 failed`);
})().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>{ws?.close();chrome.kill();});
