/* #61 /13 formal reader gate. Real native prepare and UI file chooser;
 * tamper only detached reply metadata. All fixtures are repo-authored. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),cp=require('node:child_process');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),P=require('../geometry-web/project-store.js'),F=P.Features,zip=require('../geometry-web/vendor/fflate/umd/index.js');
const url=process.env.GEOMETRY_TEST_URL,feedback=process.env.GEOMETRY_FEEDBACK_DIR,out=process.env.GEOMETRY_RULE_READER_OUT;
if(!url||![feedback,out].every(p=>p&&path.resolve(p).startsWith(os.tmpdir()+path.sep)))throw Error('Explicit isolated URL and TEMP feedback/output directories required');
fs.mkdirSync(out,{recursive:true});let passed=0;const checks=[],results=[],errors=[];
function check(label,value){assert.equal(value,true,label);passed++;checks.push(label);console.log('PASS '+label);}
const git=(...args)=>cp.execFileSync('git',args,{cwd:root,encoding:'utf8'}).trim();
async function snapshot(page){return page.evaluate(async()=>({scene:(await apiRequest('dump')).text,state:ReferenceWorkspace.getProjectState(),raw:ReferenceWorkspace.context().featureAttachments,history:{undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length}}));}
async function openFile(page,file){const chooser=page.waitForEvent('filechooser');await page.locator('#fileMenuBtn').click();await page.locator('#btnOpenProject').click();await(await chooser).setFiles(file);await page.waitForFunction(()=>!ReferenceWorkspace.busy);}
async function freshPage(browser){
  const page=await browser.newPage({viewport:{width:1280,height:900},acceptDownloads:true});page.on('dialog',d=>d.accept());page.on('pageerror',e=>errors.push(e.message));
  await page.goto(url);await page.waitForFunction(()=>connection.phase==='ready');await page.locator('#fileMenuBtn').click();await page.locator('#btnNewProject').click();await page.waitForFunction(()=>!ReferenceWorkspace.busy&&oc.gridSystems.length===0);return page;
}
(async()=>{
  const head=git('rev-parse','HEAD'),tree=git('rev-parse','HEAD^{tree}'),status=git('status','--porcelain');
  if(process.env.GEOMETRY_REQUIRE_CLEAN==='1')assert.equal(status,'','Frozen clean head required');
  const runtime=await fetch(new URL('/runtime',url)).then(r=>r.json());check('runtime fresh before real native operations',runtime.fresh===true);check('runtime belongs to selected worktree',path.resolve(runtime.root)===root);
  const original=await P.unpack(new Uint8Array(fs.readFileSync(path.join(root,'geometry-web/docs/evidence/issue48-34a6222-20261005/archives/1280-full.gcanvas'))),zip);
  const raw={schema:F.GRID_RULE_SCHEMA,draftId:'reader-rule-raw',kind:'source',intent:'edit',baseRef:{kind:'grid-system',id:901,fingerprint:'a'.repeat(64)},inputRefs:[],rawForm:Object.fromEntries(F.sourceFields.map(k=>[k,''])),ruleDraft:{intent:'edit',ruleKey:7,rawForm:{name:'Pending reader rule',selector:'all-cells',cellI:'0',cellJ:'0',divisionsU:' 7 ',divisionsV:''}}};
  const scene=original.scene+'\nrequires grid-subdivision-rules/1\ngrid-system 901 name-hex 526561646572 main-along none u repeat 0 600 v repeat 0 400\ngrid-source-rule 901 key 7 name-hex 72756c65 selector all-cells divide 3 2\ngrid-source-rule-highwater 901 next 11\n';
  const metadata=structuredClone(original.manifest);metadata.featureAttachments.records.push(F.record(F.GRID_KIND,raw));const bytes=await P.pack(scene,metadata,original.sources,zip),file=path.join(out,'authored-reader13.gcanvas');fs.writeFileSync(file,bytes);
  const loaded=await P.unpack(bytes,zip);check('fixture is genuine /13 raw/native/evidence ZIP',loaded.manifest.format===P.GRID_RULE_FORMAT&&loaded.manifest.requiredCapabilities.includes(F.GRID_RULE_SCHEMA)&&loaded.manifest.requiredCapabilities.includes(P.SUBDIVISION_CAPABILITY)&&loaded.manifest.requiredCapabilities.includes(P.EVIDENCE_CAPABILITY));
  const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  try{
    for(const mode of ['missing-canonical','capability-mismatch','incomplete-snapshot','invalid-pin']){
      const page=await freshPage(browser);
      // Keep a distinct real current project, so rejection must preserve its
      // world and history rather than merely ending up at another empty scene.
      await page.locator('#emptyNewGridSystem').click();await page.locator('#igName').fill('Current project '+mode);await page.locator('#igSaveSource').click();await page.locator('#impact-confirm').click();await page.waitForFunction(()=>!oc.busy&&!!document.getElementById('igClose'));await page.locator('#igClose').click();
      const before=await snapshot(page);await page.evaluate(()=>{window.__readerBeforeFrame=ReferenceWorkspace.history.frame;});
      await page.evaluate(mode=>{
        const g=window.__readerGate={mode,original:window.fetch,prepares:0,confirms:0,cancels:0,snapshots:0};
        window.fetch=async function(url,init){
          if(url==='/upload/confirm')g.confirms++;if(url==='/upload/cancel')g.cancels++;
          const response=await g.original.call(window,url,init);
          if(url==='/upload/prepare'){g.prepares++;const data=await response.json();if(g.mode==='missing-canonical')delete data.final_scene;if(g.mode==='capability-mismatch')data.required_capabilities=[];return new Response(JSON.stringify(data),{status:response.status,headers:response.headers});}
          if(url==='/sources/snapshot'){g.snapshots++;const data=await response.json();if(g.mode==='incomplete-snapshot')data.complete=false;if(g.mode==='invalid-pin'){const node=data.nodes.find(n=>n.kind==='parameter-field');if(!node)throw Error('Real native candidate lacks fixture field');node.definitionFingerprint='invalid';}return new Response(JSON.stringify(data),{status:response.status,headers:response.headers});}
          return response;
        };
      },mode);
      await openFile(page,file);const after=await snapshot(page),network=await page.evaluate(()=>Object.fromEntries(['prepares','confirms','cancels','snapshots'].map(k=>[k,window.__readerGate[k]]))),message=await page.locator('#status').textContent();
      check(mode+' real candidate prepared once',network.prepares===1);
      check(mode+' sends zero confirms and cancels owned candidate once',network.confirms===0&&network.cancels===1);
      check(mode+' preserves native world byte for byte',after.scene===before.scene);
      check(mode+' preserves context identity and revision',after.state.contextToken===before.state.contextToken&&after.state.id===before.state.id&&after.state.revision===before.state.revision);
      check(mode+' preserves raw and history frame',JSON.stringify(after.raw)===JSON.stringify(before.raw)&&JSON.stringify(after.history)===JSON.stringify(before.history)&&await page.evaluate(()=>ReferenceWorkspace.history.frame===window.__readerBeforeFrame));
      check(mode+' uses canonical/evidence guard and reports rejection',network.snapshots===(mode==='missing-canonical'?0:1)&&!!message&&!message.includes('已開啟'));
      await page.screenshot({path:path.join(out,mode+'.png')});results.push({mode,before,after,network,message});await page.close();
    }
    const page=await freshPage(browser);await page.addInitScript(()=>{window.showSaveFilePicker=undefined;});await page.evaluate(()=>{window.showSaveFilePicker=undefined;window.__validReader={original:window.fetch,snapshots:0};window.fetch=async function(url,init){if(url==='/sources/snapshot')window.__validReader.snapshots++;return window.__validReader.original.call(window,url,init);};});
    const empty=await snapshot(page);await openFile(page,file);const accepted=await snapshot(page),objects=await page.evaluate(()=>apiRequest('objects'));
    check('valid /13 replaces a genuinely empty context',empty.scene!==accepted.scene&&empty.state.contextToken!==accepted.state.contextToken&&objects.gridSystems.some(s=>s.id===901));
    check('valid /13 executes real detached evidence snapshot',await page.evaluate(()=>window.__validReader.snapshots===1));
    const source=objects.gridSystems.find(s=>s.id===901);check('valid /13 preserves rule key and highwater',source.nextRuleKey===11&&source.rules[0].ruleKey===7);
    check('valid /13 preserves exact raw strings and pins',JSON.stringify(await page.evaluate(()=>ReferenceWorkspace.readFeatureAttachment('grid-draft')))===JSON.stringify(raw));
    check('valid /13 preserves evidence and original source bytes',await page.evaluate(()=>!!ReferenceWorkspace.readFeatureAttachment('evidence-links'))&&accepted.raw.length===loaded.manifest.featureAttachments.records.length);
    const downloadPromise=page.waitForEvent('download');await page.locator('#projectBar [data-project-action="save"]').click();const download=await downloadPromise,saved=path.join(out,'accepted-reader13.gcanvas');await download.saveAs(saved);const roundtrip=await P.unpack(new Uint8Array(fs.readFileSync(saved)),zip);
    check('formal Save retains /13 model collections, raw/evidence/source closure and native',roundtrip.manifest.format===P.GRID_RULE_FORMAT&&roundtrip.scene===accepted.scene&&roundtrip.manifest.models.length===loaded.manifest.models.length&&roundtrip.manifest.faceProjections.length===loaded.manifest.faceProjections.length&&JSON.stringify(roundtrip.manifest.featureAttachments.records.find(r=>r.kind===F.GRID_KIND).value)===JSON.stringify(raw)&&[...loaded.sources].every(([key,bytes])=>Buffer.from(roundtrip.sources.get(key)||[]).equals(Buffer.from(bytes))));
    await page.screenshot({path:path.join(out,'accepted-reader13.png')});await page.close();check('formal reader gate has zero browser exceptions',errors.length===0);
    fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({schema:'geometry-rule-reader-gate/1',head,tree,worktreeClean:status==='',runtime,passed,checks,results,errors},null,2));console.log('RULE_READER_RESULT '+JSON.stringify({head,passed,failed:0,errors,output:out}));
  }finally{await browser.close();}
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
