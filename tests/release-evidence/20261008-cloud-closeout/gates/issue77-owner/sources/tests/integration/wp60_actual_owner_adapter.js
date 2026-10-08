/* Test-only mapping of the five required gates to the existing finite owner.
 * No substitute registry, store, history or native receipts. Browser gates use
 * a disposable real app/service, plus real /10 and committed-rule /11 files.
 */
'use strict';
const assert=require('node:assert/strict');
const {before,after}=require('node:test');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),net=require('node:net');
const {spawn,spawnSync}=require('node:child_process');
const {chromium}=require('playwright');
const P=require('../../geometry-web/project-store.js'),S=require('../../geometry-web/source-plane.js');
const zip=require('../../geometry-web/vendor/fflate/umd/index.js');
const root=path.resolve(__dirname,'../..'),F=P.Features;
let service,browser,url,serverLog='',output;
const evidence=[];

before(async()=>{
  for(const name of ['GEOMETRY_TEST_BRIDGE','GEOMETRY_MODEL_BASE'])
    assert.ok(process.env[name]&&path.isAbsolute(process.env[name]),name+' must identify a fresh native test binary');
  const freshness=spawnSync(process.env.PYTHON||'python3',['-c',
    'import os,sys,json;sys.path.insert(0,"tests");import binaries;print(json.dumps({name:binaries.require_fresh(name,os.environ[key]) for name,key in [("bridge","GEOMETRY_TEST_BRIDGE"),("model-base","GEOMETRY_MODEL_BASE")]}))'],
    {cwd:root,env:process.env,encoding:'utf8'});
  assert.equal(freshness.status,0,'Native freshness receipt: '+freshness.stderr);
  evidence.push({name:'native-freshness',binaries:JSON.parse(freshness.stdout)});
  output=process.env.GEOMETRY_OWNER_GATE_DIR||fs.mkdtempSync(path.join(os.tmpdir(),'wp60-owner-five-'));
  assert.ok(output.startsWith(os.tmpdir()+path.sep),'Evidence and feedback must stay in TEMP');
  fs.mkdirSync(output,{recursive:true});
  const probe=net.createServer();await new Promise(resolve=>probe.listen(0,'127.0.0.1',resolve));
  const port=probe.address().port;await new Promise(resolve=>probe.close(resolve));url='http://127.0.0.1:'+port+'/';
  service=spawn(process.env.PYTHON||'python3',[path.join(root,'geometry-web/serve.py'),String(port)],{
    cwd:root,detached:true,env:{...process.env,GEOMETRY_BRIDGE:process.env.GEOMETRY_TEST_BRIDGE,GEOMETRY_FEEDBACK_DIR:path.join(output,'feedback')}});
  service.stdout.on('data',b=>serverLog+=b);service.stderr.on('data',b=>serverLog+=b);
  let runtime;
  for(let attempt=0;attempt<100;attempt++){
    if(service.exitCode!==null)throw Error('Private service exited: '+serverLog);
    try{const response=await fetch(url+'runtime');if(response.ok){runtime=await response.json();break;}}catch{}
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  const probeResult=spawnSync(process.env.PYTHON||'python3',[path.join(root,'geometry-web/runtime_version.py'),'--probe',String(port)],{cwd:root,encoding:'utf8'});
  assert.equal(probeResult.status,0,'Exact source/runtime probe: '+probeResult.stdout+probeResult.stderr);
  runtime=JSON.parse(probeResult.stdout);assert.equal(runtime.root,root,'This gate must use its own exact checkout');
  evidence.push({name:'runtime',...runtime});
  browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
});
after(async()=>{
  if(browser)await browser.close();
  if(service&&service.exitCode===null){
    // This isolated process group contains only our service and its bridge.
    process.kill(-service.pid,'SIGINT');
    await Promise.race([new Promise(resolve=>service.once('exit',resolve)),new Promise(resolve=>setTimeout(resolve,2000))]);
    try{process.kill(-service.pid,'SIGTERM');}catch(error){if(error.code!=='ESRCH')throw error;}
  }
  if(output){fs.writeFileSync(path.join(output,'service.log'),serverLog);fs.writeFileSync(path.join(output,'evidence.json'),JSON.stringify({entry:'tests/integration/issue77_attachment_owner.js',adapter:__filename,evidence},null,2));}
});

function register(contract){
  // Production has a finite built-in registry. Verify its public dispatch;
  // the test must not install a second, mutable registration mechanism.
  assert.equal(contract.kind,F.ROOM_KIND);assert.equal(contract.schema,F.ROOM_SCHEMA);assert.equal(contract.capability,F.ROOM_CAPABILITY);
  for(const name of ['validate','references','validateNativeRefs','validateNativePins'])assert.equal(contract[name],S[name]);
  F.assertKind(contract.kind);F.record(contract.kind,S.empty());
  assert.deepEqual(F.capabilities({schema:F.SCHEMA,records:[F.record(contract.kind,S.empty())]}),[contract.capability]);
}
const manifest=(base,payload)=>({...base,format:P.FEATURE_FORMAT,featureAttachments:{schema:F.SCHEMA,records:[F.record(F.ROOM_KIND,payload)]}});
const attachment=m=>F.sourceRooms(m.featureAttachments);
function corrupt(m,kind){
  const envelope=m.featureAttachments,record=envelope.records[0];
  switch(kind){
    case 'unknown-envelope-version':envelope.schema='geometry-feature-attachments/999';break;
    case 'unknown-kind':record.kind='unsupported-room-kind';break;
    case 'unknown-schema':record.schema='source-rooms/999';break;
    case 'unknown-capability':m.requiredCapabilities.push('unsupported-editor-cap/1');break;
    case 'missing-kind-capability':m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!==S.CAPABILITY);break;
    case 'duplicate-kind':envelope.records.push(structuredClone(record));break;
    default:throw Error('Unknown rejection fixture '+kind);
  }
}
async function withWorkspace(f,name,fn){
  const rules=await P.unpack(new Uint8Array(fs.readFileSync(path.join(root,'geometry-web/examples/source-subdivision-v11.gcanvas'))),zip);
  for(const [format,scene] of [[10,f.scene],[11,rules.scene+f.scene]]){
    const value=structuredClone(f.payload);value.schema=S.HISTORY_SCHEMA;
    value.legacyHistory=[{planeId:'plane-two-rooms',boundaryId:11,pageId:'historical-page',
      records:[{id:'unknown-history-record',label:'歷史原始值',location:'原頁',datum:'未確認',unit:'mm',value:null,opaque:{unrecognized:['retain',null,17]}}],reconstructionReview:null}];
    const bytes=await P.pack(scene,manifest(structuredClone(f.base),value),f.sources,zip);
    const decoded=await P.unpack(bytes,zip);assert.equal(decoded.manifest.format,format===11?P.SUBDIVISION_FORMAT:P.FEATURE_FORMAT);
    const context=await browser.newContext({viewport:{width:1280,height:900}}),page=await context.newPage(),errors=[];
    page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('dialog',d=>d.accept());
    try{
      await page.goto(url);await page.waitForFunction(()=>typeof ReferenceWorkspace!=='undefined'&&connection.phase==='ready');
      await page.evaluate(async bytes=>ReferenceWorkspace.importBytes(new Uint8Array(bytes),'required-owner.gcanvas'),[...bytes]);
      let timer;
      const result=await Promise.race([fn(page,{bytes:[...bytes],hash:f.hash,pdf:[...f.bytes],payload:value}),
        new Promise((_,reject)=>timer=setTimeout(()=>reject(Error(name+' /'+format+' timed out')),45000))]).finally(()=>clearTimeout(timer));
      assert.deepEqual(errors,[],'Unexpected app/native errors');
      evidence.push({name,format,status:'pass',...result});console.log('OWNER '+name+' /'+format+' '+JSON.stringify(result));
    }finally{await context.close();}
  }
}

async function verifyHistory(f){return withWorkspace(f,'history',async(page,input)=>page.evaluate(async data=>{
  const W=ReferenceWorkspace,C=RoomCollectionWorkspace.controller,kind='source-rooms',checks=[];
  const check=(name,ok)=>{if(!ok)throw Error(name);checks.push(name);};
  const read=()=>W.readFeatureAttachment(kind,W.getProjectState().contextToken),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const scene=async()=>{const r=await api('dump');check('real native dump',r.ok);return r.text;};
  const command=async cmd=>{const r=await api(cmd);check(cmd,r.ok);return r;};
  const initial=read(),nativeBefore=await scene();
  C.rename('room-a','正式改名');check('rename actual owner',read().rooms[0].name==='正式改名');check('rename geometry unchanged',await scene()===nativeBefore);
  await command('line undo');check('rename undo exact snapshot',same(read(),initial));
  await command('line redo');check('rename redo',read().rooms[0].name==='正式改名');await command('line undo');
  C.unlink('room-b');check('unlink attachment only',read().rooms.length===1&&await scene()===nativeBefore);
  await command('line undo');check('unlink undo exact snapshot',same(read(),initial));
  await command('line redo');check('unlink redo',read().rooms.length===1);await command('line undo');
  const returned=read();returned.rooms[0].name='mutated read';returned.legacyHistory[0].records[0].opaque.unrecognized[0]='mutated read';
  check('detached read and unknown historical JSON',same(read(),initial));
  const proposal=read();proposal.rooms[0].name='detached write';W.setFeatureAttachment(kind,proposal,W.getProjectState().contextToken);
  proposal.rooms[0].name='mutated caller';proposal.legacyHistory[0].records[0].opaque.unrecognized.push('mutated caller');
  check('immutable proposed snapshot',read().rooms[0].name==='detached write'&&same(read().legacyHistory,initial.legacyHistory));
  await command('line undo');check('immutable history restore',same(read(),initial));
  const incarnation=W.getRoomIntegration().readIncarnation(11,W.getProjectState().contextToken);
  await command('line delete boundary 11');check('native delete retires association',read().rooms[0].reviewState==='needs-reassociation');
  await command('line boundary 11 outline 1000,1000 5000,1000 5000,4000 1000,4000');
  check('same-ID birth cannot regain identity',read().rooms[0].reviewState==='needs-reassociation'&&
    W.getRoomIntegration().readIncarnation(11,W.getProjectState().contextToken)!==incarnation);
  check('retired association retains original saved pin',read().rooms[0].boundaryRef.associationPin===initial.rooms[0].boundaryRef.associationPin);
  await command('line undo');await command('line undo');check('native deletion undo restores exact association',same(read(),initial));
  await command('line redo');await command('line redo');check('same-ID redo remains retired',read().rooms[0].reviewState==='needs-reassociation');
  await command('line undo');await command('line undo');
  // Genuine native preview outside this page's observer simulates missing
  // owner history. No fabricated result or mutation of ContextHistory fields.
  const external=await fetch('/api',{method:'POST',headers:{'Content-Type':'application/json','X-Geometry-Version':pageRuntimeVersion},
    body:JSON.stringify({cmd:'line preview boundary 11 outline 1000,1000 4800,1000 4800,4000 1000,4000'})});
  const preview=await external.json();check('unobserved real native candidate',preview.ok&&preview.preview?.valid===true);
  await command('line confirm '+preview.preview.token);
  const unknown=read();check('unknown history requires reassociation',unknown.rooms.every(r=>r.reviewState==='needs-reassociation'));
  check('unknown history retains original saved pins',same(unknown.rooms.map(r=>r.boundaryRef),initial.rooms.map(r=>r.boundaryRef)));
  check('unknown history retains original raw history',same(unknown.legacyHistory,initial.legacyHistory));
  check('unknown history retains original PDF',same([...W.context().sources.get(data.hash).bytes],data.pdf));
  await command('line undo');check('unknown confirm undo restores exact attachment',same(read(),initial));
  await command('line redo');check('unknown confirm redo retains uncertainty',read().rooms.every(r=>r.reviewState==='needs-reassociation'));
  return {conditions:checks};
},input));}

async function verifyWorkspaceGuards(f){return withWorkspace(f,'guards',async(page,input)=>{
  const first=await page.evaluate(async data=>{
    const W=ReferenceWorkspace,I=W.getRoomIntegration(),kind='source-rooms',checks=[];
    const check=(name,ok)=>{if(!ok)throw Error(name);checks.push(name);};
    const throws=fn=>{try{fn();return false;}catch{return true;}};
    const token=W.getProjectState().contextToken,original=W.readFeatureAttachment(kind,token),before=(await api('dump')).text;
    const lease=I.beginTransaction(token);
    check('copied lease refused',throws(()=>I.assertTransaction({...lease})));
    check('grouped metadata without native dirty group refused',throws(()=>W.setFeatureAttachment(kind,original,token,{recordHistory:false,roomLease:lease})));
    check('missing lease refused',throws(()=>W.setFeatureAttachment(kind,original,token,{recordHistory:false})));
    const invalid=structuredClone(original);invalid.rooms[0].boundaryRef.id=0;
    check('transaction preflight rejects malformed payload',throws(()=>I.preflightAttachment(invalid,lease)));
    I.endTransaction(lease);check('retired lease refused',throws(()=>I.assertTransaction(lease)));
    check('lease rejections preserve world and metadata',(await api('dump')).text===before&&JSON.stringify(W.readFeatureAttachment(kind))===JSON.stringify(original));
    await W.importBytes(new Uint8Array(data.bytes),'next-real-context.gcanvas');
    check('stale context read refused',throws(()=>W.readFeatureAttachment(kind,token)));
    check('stale context write refused',throws(()=>W.setFeatureAttachment(kind,original,token)));
    // Intercept only delivery of an actual read response. The candidate,
    // native definitions, contexts and owner history remain production data.
    window.ownerGateFetch=window.fetch;window.ownerGateArrived=false;
    window.fetch=async(...args)=>{const response=await ownerGateFetch(...args);let body;
      try{body=JSON.parse(args[1]?.body||'{}');}catch{}
      if(args[0]==='/api'&&body.cmd==='boundary 11'&&!ownerGateArrived){
        ownerGateArrived=true;await new Promise(resolve=>window.ownerGateRelease=resolve);
      }return response;};
    window.ownerGateReview=RoomCollectionWorkspace.controller.review('room-a').then(()=>({accepted:true}),e=>({accepted:false,message:e.message}));
    return {conditions:checks};
  },input);
  await page.waitForFunction(()=>ownerGateArrived);
  // A real project import replaces the context while the read is pending.
  // This read has no mutating transaction lease or unpublished room draft.
  const late=await page.evaluate(async data=>{
    const W=ReferenceWorkspace,token=W.getProjectState().contextToken,value=W.readFeatureAttachment('source-rooms',token);
    await W.importBytes(new Uint8Array(data.bytes),'newer-real-context.gcanvas');
    if(W.getProjectState().contextToken===token)throw Error('Real import must replace the owner context');
    value.rooms[1].name='newer owner metadata';W.setFeatureAttachment('source-rooms',value,W.getProjectState().contextToken);
    const before=JSON.stringify(W.readFeatureAttachment('source-rooms')),native=(await ownerGateFetch('/api',{method:'POST',headers:{'Content-Type':'application/json','X-Geometry-Version':pageRuntimeVersion},body:JSON.stringify({cmd:'dump'})}).then(r=>r.json())).text;
    window.fetch=ownerGateFetch;ownerGateRelease();const result=await ownerGateReview;
    if(result.accepted||!result.message.includes('晚到')||JSON.stringify(W.readFeatureAttachment('source-rooms'))!==before||(await api('dump')).text!==native)throw Error('late native read must not replace newer owner metadata');
    return {accepted:result.accepted,message:result.message,contextChanged:true};
  },input);
  const atomic=await page.evaluate(async()=>{
    const W=ReferenceWorkspace,C=RoomCollectionWorkspace.controller,checks=[];
    const check=(name,ok)=>{if(!ok)throw Error(name);checks.push(name);};
    const snapshot=async()=>({scene:(await api('dump')).text,value:W.readFeatureAttachment('source-rooms')}),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
    const before=await snapshot(),entries=W.history.undo.length;
    C.beginNew('rooms-two-rooms');const preview=await C.prepare([[1000,5000],[5000,5000],[5000,7000],[1000,7000]],'atomic real native room');
    check('real pending preview preserves scene and metadata',same(await snapshot(),before));
    const result=await C.confirm(),after=await snapshot();
    check('native and room metadata both committed',after.value.rooms.length===before.value.rooms.length+1&&after.scene!==before.scene);
    check('one native metadata history entry',W.history.undo.length===entries+1&&!W.history.group);
    const native=await api('boundary '+result.boundaryId),room=after.value.rooms.find(r=>r.id===result.id);
    check('committed association uses actual typed native pin',native.ok&&room.boundaryRef.id===result.boundaryId&&room.boundaryRef.associationPin===native.geometryFingerprint);
    const undo=await api('line undo');check('one undo restores native and metadata',undo.ok&&same(await snapshot(),before));
    const redo=await api('line redo');check('one redo restores native and metadata',redo.ok&&same(await snapshot(),after));
    // Full reader validation of actual final candidate pins, not just IDs.
    const bytes=await W.exportBytes(),files=fflate.unzipSync(bytes),manifest=JSON.parse(new TextDecoder().decode(files['manifest.json']));
    manifest.featureAttachments.records.find(r=>r.kind==='source-rooms').value.rooms[0].boundaryRef.associationPin='0'.repeat(64);
    files['manifest.json']=new TextEncoder().encode(JSON.stringify(manifest));
    let rejected=false;try{await W.importBytes(fflate.zipSync(files),'wrong-native-pin.gcanvas');}catch{rejected=true;}
    check('reader rejects incorrect final native pin without publishing',rejected&&same(await snapshot(),after));
    return {conditions:checks};
  });
  return {conditions:[...first.conditions,'actual late native read rejected',...atomic.conditions],late};
});}

module.exports={register,manifest,attachment,pack:P.pack,unpack:P.unpack,corrupt,
  validateNativeRefs:(m,objects)=>F.validateNativeRefs(m.featureAttachments,objects),verifyHistory,verifyWorkspaceGuards};
