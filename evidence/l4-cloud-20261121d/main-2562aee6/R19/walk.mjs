// Node 24. Connect to an already running headless Chrome. The caller starts and probes the isolated App.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';

const [cdpOrigin,appOrigin,outDir] = process.argv.slice(2);
if(!cdpOrigin || !appOrigin) throw Error('node walk.mjs <CDP origin> <isolated App origin> [output directory]');
const out = outDir || path.dirname(fileURLToPath(import.meta.url));
fs.mkdirSync(out,{recursive:true});
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const hashFile=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const target=await (await fetch(cdpOrigin+'/json/new?'+encodeURIComponent(appOrigin),{method:'PUT'})).json();
const ws=new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
const pending=new Map(), observed=[], responseUrls=new Map(), inflight=new Set();
let sequence=0;
function send(method,params={}) {
  return new Promise((resolve,reject)=>{
    const id=++sequence;
    pending.set(id,r=>r.error?reject(Error(r.error.message)):resolve(r.result));
    ws.send(JSON.stringify({id,method,params}));
  });
}
ws.onmessage=event=>{
  const m=JSON.parse(event.data);
  if(m.id) {pending.get(m.id)?.(m); pending.delete(m.id);}
  if(m.method==='Page.javascriptDialogOpening'){
    observed.push({dialog:m.params.message});
  }
  if(m.method==='Network.responseReceived' && m.params.response.url===appOrigin+'/boundary-pair/preview'){
    responseUrls.set(m.params.requestId,m.params.response.url);
  }
  if(m.method==='Network.loadingFinished' && responseUrls.has(m.params.requestId)){
    responseUrls.delete(m.params.requestId);
    const p=send('Network.getResponseBody',{requestId:m.params.requestId}).then(({body,base64Encoded})=>{
      const result=JSON.parse(base64Encoded?Buffer.from(body,'base64').toString('utf8'):body);
      // Only the candidate geometry is needed. Owner keys and confirmation tokens stay private.
      observed.push({preview:{ok:result.ok,valid:result.preview?.valid,groups:result.preview?.boundaryPairs,error:result.error}});
    }).finally(()=>inflight.delete(p));
    inflight.add(p);
  }
};
async function read(expression){
  const r=await send('Runtime.evaluate',{expression,returnByValue:true});
  if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);
  return r.result.value;
}
async function wait(expression){
  const start=Date.now();
  while(Date.now()-start<15000){if(await read(expression))return;await delay(120);}
  throw Error('UI 未達預期 '+expression);
}
async function key(key,code,virtual,modifiers=0){
  for(const type of ['rawKeyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode:virtual,modifiers});
}
async function click(selector,double=false){
  const js='('+function(sel){
    const n=document.querySelector(sel);if(!n)return null;
    const r=n.getBoundingClientRect();if(!r.width||!r.height)return null;
    const x=r.x+r.width/2,y=r.y+r.height/2,hit=document.elementFromPoint(x,y);
    if(hit && n.contains(hit))return {x,y};
    for(let a=n.parentElement;a;a=a.parentElement){
      const b=a.getBoundingClientRect();
      if(a.scrollHeight>a.clientHeight+1&&/auto|scroll/.test(getComputedStyle(a).overflowY)&&
        (y<b.top+6||y>b.bottom-6))return {x:Math.max(1,Math.min(innerWidth-2,b.x+b.width/2)),y:Math.max(1,Math.min(innerHeight-2,b.y+b.height/2)),dy:y-(b.y+b.height/2)};
    }
    return {blocked:hit?.outerHTML.slice(0,170),x,y};
  }+')('+JSON.stringify(selector)+')';
  let pos;
  for(let i=0;i<25;i++){
    pos=await read(js);
    if(pos?.dy){await send('Input.dispatchMouseEvent',{type:'mouseWheel',x:pos.x,y:pos.y,deltaX:0,deltaY:pos.dy});await delay(150);continue;}
    if(pos&&!pos.blocked&&pos.x>=0&&pos.y>=0)break;
    await delay(160);
  }
  if(!pos||pos.dy||pos.blocked)throw Error('無法點選 '+selector+' '+JSON.stringify(pos));
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:pos.x,y:pos.y});
  for(let c=1;c<=(double?2:1);c++)for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x:pos.x,y:pos.y,button:'left',clickCount:c});
  await delay(190);
}
async function fill(sel,value){
  await click(sel);await key('a','KeyA',65,2);await send('Input.insertText',{text:String(value)});await key('Tab','Tab',9);
  assert.equal(await read('document.querySelector('+JSON.stringify(sel)+').value'),String(value));
}
async function select(sel,value){
  const q=JSON.stringify(sel);
  const index=await read('Array.from(document.querySelector('+q+').options).filter(o=>!o.disabled).findIndex(o=>o.value==='+JSON.stringify(String(value))+')');
  assert.ok(index>=0,sel+' option '+value);
  await click(sel);await key('Home','Home',36);
  for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);
  await key('Enter','Enter',13);
  await wait('document.querySelector('+q+').value==='+JSON.stringify(String(value)));
}
const report={main:'2562aee65c9f21a9ffdfd684100102d764bc2eb4',viewport:[1400,900],steps:[],observed};
const resultFile=path.join(out,'result.json');
const save=()=>fs.writeFileSync(resultFile,JSON.stringify(report,null,2)+'\n');
async function snap(name,action){
  const filename=String(report.steps.length+1).padStart(2,'0')+'-'+name+'.png';
  const file=path.join(out,filename);
  const png=await send('Page.captureScreenshot',{format:'png',fromSurface:true});fs.writeFileSync(file,Buffer.from(png.data,'base64'));
  const state=await read(`(()=>({projectLabel:document.querySelector('#projectBar')?.innerText,spaceIds:oc.spaces.map(s=>s.id),columns:oc.columns,focus:oc.edit?.bid??null,outer:oc.edit?oc.bmap[oc.edit.bid]?.[0]?.verts:null,projection:fe.obstacles?.items??[],faceTimbers:oc.edit?fe.timbers:[],dialog:document.querySelector('.reference-impact[open]')?.innerText,form:document.querySelector('#tbBoundaryPair')?.innerText,feedback:document.querySelector('#rcErr:not([hidden])')?.innerText||document.querySelector('#toastRegion')?.innerText}))()`);
  state.surfaceIds=await read('oc.surfs.map(s=>s.id)');
  state.selectedInputs=await read('Array.from(document.querySelectorAll("#tbBoundaryPair [data-field]"),n=>[n.id,n.value])');
  report.steps.push({action,screenshot:filename,sha256:hashFile(file),state});save();console.log(filename,action);
}
const stage=(name,label,action)=>action().then(()=>snap(name,label));
try{
  await send('Page.enable');await send('Network.enable');
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  await wait("typeof oc!=='undefined' && connection.phase==='ready'");
  await stage('initial','開啟獨立 App 的一般物件畫布，核對起始場景',async()=>{await wait('!ReferenceWorkspace.busy && !oc.busy && !oc.spaces.length && !oc.columns.length');});
  const startingIds=await read('oc.surfs.map(s=>s.id)');
  await stage('room-input','建立物件 → 知道尺寸 → 六面盒，輸入寬深 1000、高 2500、含地板',async()=>{
    await click('#btnCreateObject');await click('#btnBox6');await fill('#box6W',1000);await fill('#box6D',1000);await fill('#box6H',2500);
  });
  await stage('room-created','建立六面盒空間',async()=>{await click('#box6Submit');await wait('oc.spaces.length===1&&!oc.busy');});
  const spaceId=await read('oc.spaces[0].id');
  await stage('column-input','建立物件 → 柱，輸入足跡、連結空間',async()=>{
    await click('#btnCreateObject');await click('#btnNewColumn');await select('#rcSpace',spaceId);
    await fill('#rcW',500);await fill('#rcD',13);await fill('#rcX',500);await fill('#rcY',0);
  });
  await stage('column-created','建立空間所屬 RC 柱，足跡 500×13 mm，緊貼右下角的兩面牆',async()=>{await click('#rcSubmit');await wait('oc.columns.length===1&&!oc.busy');});
  const bid=await read('Math.min(...oc.surfs.filter(s=>!'+JSON.stringify(startingIds)+'.includes(s.id)).map(s=>s.id))');
  await stage('ceiling','連按兩下天花邊界，進入面內工作區',async()=>{
    await click('.ocard[data-kind="boundary"][data-id="'+bid+'"]',true);await wait('oc.edit?.bid==='+bid);
  });
  await stage('column-projection','形狀 → 查看柱投影的切角分類',async()=>{
    await click('#faceInspectorTabs [data-fi-tab="shape"]');await wait('document.querySelector(".fe-ob-check:checked") && !oc.busy');
  });
  await stage('column-cut','套用柱投影，確認角落的六頂點外環',async()=>{
    await click('#feApplyProj');await delay(550);
    if(await read('!!document.querySelector(".reference-impact[open] #impact-confirm")'))await click('#impact-confirm');
    await wait('oc.bmap['+bid+'][0].verts.length===6 && !oc.busy');
  });
  const outer=await read('oc.bmap['+bid+'][0].verts');
  const horizAt=y=>outer.findIndex((p,i)=>p[1]===y&&outer[(i+1)%outer.length][1]===y);
  const low=horizAt(0), high=horizAt(13);assert.ok(low>=0&&high>=0,'預期兩平行固定邊相差13mm');
  await stage('pair-input','構件 → 角材 → 兩支互頂壁邊材，選低邊及高邊，各 A27 B20，+u、+n',async()=>{
    await click('#faceInspectorTabs [data-fi-tab="components"]');await click('#faceComponentSwitch [data-component-tab="timber"]');
    await select('#tbPlacementMode','boundary-pair');
    for(const [i,edge] of [[1,low],[2,high]]){
      const s='#tbPair'+i;await select(s+'Anchor','e'+edge);await fill(s+'A',27);await fill(s+'B',20);await select(s+'Dir','+u');await select(s+'Side','+n');
    }
  });
  await stage('preview','預覽兩支互頂，核對接觸與長度',async()=>{
    await click('#tbPairPreview');await wait('document.querySelector(".reference-impact[open] #impact-confirm") && !document.querySelector("#impact-confirm").disabled');await delay(250);
  });
  const preview=observed.findLast(r=>r.preview)?.preview, group=preview?.groups?.[0]?.after;
  assert.ok(preview?.ok&&preview.valid&&group,'原生回傳的 UI 候選須合法');
  assert.deepEqual(group.members.map(m=>m.geometry.length),[500,500]);assert.equal(group.contacts.length,1);
  assert.equal(group.contacts[0].plane,500);assert.deepEqual(group.contacts[0].contact,[13,27]);assert.equal(await read('fe.timbers.length'),0);
  await stage('placed','確認套用，核對兩支壁邊材同時存在',async()=>{
    await click('#impact-confirm');await wait('fe.timbers.length===2 && !oc.busy');});
  await stage('undone','按 Ctrl+Z 一次，兩支同時移除',async()=>{await key('z','KeyZ',90,2);await wait('fe.timbers.length===0 && !oc.busy');});
  await stage('redone','按 Ctrl+Y 一次，兩支同時回復',async()=>{await key('y','KeyY',89,2);await wait('fe.timbers.length===2 && !oc.busy');});
  report.passed=true;
}catch(e){report.error=e.message;report.passed=false;await snap('stopped','操作中止時的畫面');process.exitCode=1;console.error(e);}
finally{await Promise.allSettled(inflight);save();ws.close();await fetch(cdpOrigin+'/json/close/'+target.id);}
