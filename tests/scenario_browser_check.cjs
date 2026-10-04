/* Actual Chromium + ZIP/file input + disposable native CLI. No app/live /upload. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const {spawn}=require('node:child_process');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
const output=process.env.GEOMETRY_SCENARIO_TEST_DIR||'/tmp/geometry-scenario/browser';
if(!output.startsWith('/tmp/'))throw Error('Use an isolated /tmp test output directory.');
fs.mkdirSync(output,{recursive:true});
let nativeCalls=0, forbiddenCalls=0;
const pending=new Set();
const pageHTML=`<!doctype html><meta charset="utf-8"><title>Scenario archive acceptance harness</title>
<button id="save">Save complete A/B archive</button><input id="open" type="file"><output id="status">ready</output>
<script src="/project-store.js"></script><script src="/scenario-snapshots.js"></script>
<script src="/scenario-diff.js"></script><script src="/vendor/fflate/umd/index.js"></script>
<script>
window.stamp={context:{},frame:{},contextToken:'fresh-context',revision:0,blocked:false};
window.verify=async data=>{const r=await fetch('/verify',{method:'POST',body:JSON.stringify(data)});const receipt=await r.json();if(receipt.ok!==true)throw Error(JSON.stringify(receipt));
 if(window.hold){window.receiptArrived=true;await new Promise(resolve=>window.release=resolve);}return receipt;};
window.makeArchive=()=>GeometryScenarioSnapshots.create({verifyProject:verify,getState:()=>stamp});
window.archive=makeArchive();
document.querySelector('#save').onclick=async()=>{try{const bytes=await archive.pack(fflate),a=document.createElement('a');
 a.href=URL.createObjectURL(new Blob([bytes]));a.download='AB.scenario.zip';a.click();URL.revokeObjectURL(a.href);document.querySelector('#status').textContent='saved';}catch(e){document.querySelector('#status').textContent=e.message;}};
document.querySelector('#open').onchange=async event=>{try{const fresh=makeArchive();await fresh.unpack(new Uint8Array(await event.target.files[0].arrayBuffer()),fflate);
 window.reopened=fresh;document.querySelector('#status').textContent='reopened';}catch(e){document.querySelector('#status').textContent=e.message;}};
</script>`;
const server=http.createServer(async(req,res)=>{
  if(req.url.startsWith('/upload')||req.url==='/api'){forbiddenCalls++;res.writeHead(500);res.end('Live mutation forbidden');return;}
  if(req.url==='/verify'&&req.method==='POST') {
    let size=0;const chunks=[];
    for await(const chunk of req){size+=chunk.length;if(size>9*1024*1024){res.writeHead(413);res.end();return;}chunks.push(chunk);}
    nativeCalls++;
    const proc=spawn(process.env.PYTHON||'python3',[path.join(root,'geometry-web/scenario_verify.py')],{cwd:root,env:process.env});
    pending.add(proc);let stdout='',stderr='';
    const timer=setTimeout(()=>proc.kill('SIGKILL'),90000);
    proc.stdout.on('data',b=>{stdout+=b;if(stdout.length>16*1024*1024)proc.kill('SIGKILL');});
    proc.stderr.on('data',b=>{stderr+=b;});
    proc.on('close',()=>{clearTimeout(timer);pending.delete(proc);res.setHeader('Content-Type','application/json');
      try{JSON.parse(stdout);res.end(stdout);}catch(_){res.writeHead(500);res.end(JSON.stringify({ok:false,error:stderr||'Native verifier did not return JSON'}));}});
    proc.stdin.end(Buffer.concat(chunks));return;
  }
  if(req.url==='/'){res.setHeader('Content-Type','text/html');res.end(pageHTML);return;}
  const permitted=['/project-store.js','/scenario-snapshots.js','/scenario-diff.js','/vendor/fflate/umd/index.js'];
  if(permitted.includes(req.url)){res.setHeader('Content-Type','application/javascript');res.end(fs.readFileSync(path.join(root,'geometry-web',req.url)));return;}
  res.writeHead(404);res.end();
});
(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  const checks=[],errors=[];
  try {
    for(const width of [1280,390]) {
      const context=await browser.newContext({viewport:{width,height:900},acceptDownloads:true}),page=await context.newPage();
      page.on('pageerror',e=>errors.push(e.message));
      await page.goto('http://127.0.0.1:'+server.address().port+'/');
      const result=await page.evaluate(async()=>{
        const P=GeometryProject,S=GeometryScenarioSnapshots;
        const bytes=Uint8Array.from(atob('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j9ZkAAAAASUVORK5CYII='),c=>c.charCodeAt(0));
        const hash=await P.sha(bytes),scene='spec pitch 27\nboundary 1 outline 0,0 4000,0 4000,3000 0,3000\nplacement 1 on boundary 1 origin 0 0 0 u +x v +y\n';
        const page={id:'page-1',sourceId:hash,page:1,imgW:1,imgH:1,crop:[0,0,1,1],mmPerPx:1,x:0,y:0,rot:0,opacity:1,locked:false,calibration:null,reviewRequired:false,
          records:[{id:'observation',label:'原標值',location:'edge',datum:'drawing',unit:'mm',value:27}]};
        const manifest={format:P.FORMAT,projectId:'original-project',name:'A/B independent',sceneHash:await P.sha(new TextEncoder().encode(scene)),
          sources:[{id:hash,hash,name:'original.png',type:'image/png',size:bytes.length,path:'sources/'+hash}],faces:[{bid:1,activePageId:page.id,pages:[page]}]};
        const a=await archive.capture({manifest,scene,sources:new Map([[hash,bytes]])},{scenarioId:'A',label:'A'});
        await archive.fork('A',{scenarioId:'B',label:'B'});const b=archive.project('B');
        b.scene=b.scene.replace('spec pitch 27','spec other_pitch 27');b.manifest.sceneHash=await P.sha(new TextEncoder().encode(b.scene));
        b.manifest.faces[0].pages[0].records[0].datum='measured';
        await archive.replace('B',b);
        const diff=ScenarioDiff.compare(archive.list()[0],archive.list()[1]);
        bytes[0]=0;b.sources.get(hash)[0]=0;b.manifest.name='mutable copy';
        if(archive.project('A').sources.get(hash)[0]!==137||archive.project('B').sources.get(hash)[0]!==137)throw Error('Mutable asset sharing');
        if(JSON.stringify(archive.list()[0])!==JSON.stringify(a))throw Error('B changed A');
        return {hash,original:[...archive.project('A').sources.get(hash)],snapshots:archive.list(),stats:archive.stats(),
          diff:{fields:diff.sections.map(v=>v.field),physicalIdentity:diff.physicalIdentity,geometry:diff.geometry}};
      });
      assert.equal(result.stats.scenarios,2);assert.equal(result.stats.assets,1);
      assert.ok(result.diff.fields.includes('worldScene'));assert.ok(result.diff.fields.includes('projectManifest.faces'));
      assert.equal(result.diff.physicalIdentity,'unknown');assert.equal(result.diff.geometry.status,'not-evaluated');
      const downloadWait=page.waitForEvent('download');await page.locator('#save').click();const download=await downloadWait;
      const saved=path.join(output,'AB-'+width+'.scenario.zip');await download.saveAs(saved);
      await page.locator('#open').setInputFiles(saved);await page.waitForFunction(()=>document.querySelector('#status').textContent==='reopened');
      const reopened=await page.evaluate(hash=>({snapshots:reopened.list(),stats:reopened.stats(),original:[...reopened.project('B').sources.get(hash)]}),result.hash);
      assert.deepEqual(reopened.snapshots,result.snapshots);assert.deepEqual(reopened.original,result.original);
      const late=await page.evaluate(async()=>{
        const before=JSON.stringify(archive.list()),stats=JSON.stringify(archive.stats());window.hold=true;window.receiptArrived=false;
        window.lateResult=archive.capture(archive.project('A'),{scenarioId:'late',label:'late'}).then(()=>false,e=>e.code);
        return {before,stats};
      });
      await page.waitForFunction(()=>window.receiptArrived);await page.evaluate(()=>{stamp.context={};stamp.frame={};stamp.contextToken='next-context';stamp.revision++;hold=false;release();});
      const refusal=await page.evaluate(async()=>({code:await lateResult,before:JSON.stringify(archive.list()),stats:JSON.stringify(archive.stats())}));
      assert.equal(refusal.code,'CONTEXT');assert.equal(refusal.before,late.before);assert.equal(refusal.stats,late.stats);
      const tamper=await page.evaluate(async hash=>{
        const packed=await archive.pack(fflate),files=fflate.unzipSync(packed);files['assets/'+hash][0]^=1;
        const before=JSON.stringify(archive.list());let code;
        try{await archive.unpack(fflate.zipSync(files),fflate);}catch(e){code=e.code;}
        return {code,unchanged:before===JSON.stringify(archive.list())};
      },result.hash);
      assert.equal(tamper.code,'TAMPER');assert.equal(tamper.unchanged,true);
      await page.screenshot({path:path.join(output,'harness-'+width+'.png')});
      checks.push({width,completeSnapshot:true,originalBytes:true,independentCopies:true,zipFileReopen:true,lateContext:true,tamperRejected:true});
      await context.close();
    }
    assert.equal(errors.length,0,errors.join('\n'));assert.equal(forbiddenCalls,0);assert.ok(nativeCalls>=12);
    const evidence={scope:'independent-module-only; no product adoption/history/UI claim',checks,nativeCalls,forbiddenCalls,errors};
    fs.writeFileSync(path.join(output,'evidence.json'),JSON.stringify(evidence,null,2));console.log(JSON.stringify(evidence,null,2));
  } finally {await browser.close();for(const proc of pending)proc.kill('SIGKILL');await new Promise(resolve=>server.close(resolve));}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();for(const proc of pending)proc.kill('SIGKILL');});
