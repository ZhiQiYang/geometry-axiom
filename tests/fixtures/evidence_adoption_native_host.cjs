'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),readline=require('node:readline'),{spawn}=require('node:child_process');
const {fixture,E,P}=require('./evidence_adoption_host.cjs');
const S=require('../../geometry-web/source-inspector.js'),zip=require('../../geometry-web/vendor/fflate/umd/index.js');
const directory=process.argv[3],processes=[];
function bridge(){
  const child=spawn(process.argv[2],[],{cwd:directory,stdio:['pipe','pipe','inherit']});processes.push(child);
  const pending=[];readline.createInterface({input:child.stdout}).on('line',line=>{const next=pending.shift();if(!next)throw Error('unexpected bridge response');try{next.resolve(JSON.parse(line));}catch(e){next.reject(e);}});
  child.on('error',error=>{for(const p of pending.splice(0))p.reject(error);});child.on('exit',code=>{for(const p of pending.splice(0))p.reject(Error('bridge exited '+code));});
  return command=>new Promise((resolve,reject)=>{pending.push({resolve,reject});child.stdin.write(command+'\n');});
}
async function main(){
  const ask=bridge();
  async function ok(command){const r=await ask(command);assert.equal(r.ok,true,command+': '+JSON.stringify(r));return r;}
  async function line(command){let r=await ask('line '+command);if(r.preview){assert.equal(r.preview.valid,true,JSON.stringify(r));r=await ask('line confirm '+r.preview.token);}assert.equal(r.ok,true,command+': '+JSON.stringify(r));return r;}
  const card=value=>({op:'put-parameter',value:{id:2,name:'adoption dimensions',fields:[{id:0,name:'height',type:'dimension',input:value},{id:1,name:'half',type:'dimension',input:'=@2:0/2'}]}});
  async function preview(value){const revision=(await ok('engineering-read')).revision,file=path.join(directory,'native-adopt.json');fs.writeFileSync(file,JSON.stringify({schema:'engineering-transaction/1',expectedRevision:revision,operations:[card(value)]}));return (await ok('engineering-preview '+file)).preview;}
  await ok('reset');await ok('identity-epoch 0123456789abcdef0123456789abcdef');
  const initial=await preview('3200');await ok('engineering-confirm '+initial.token);
  for(const command of ['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,4000 0,4000',
    'timber 3 20 20 role boundary','place 3 on 1 at-face e3 +v +n','timber 4 20 20 role boundary','place 4 on 1 at-face e1 +v +n',
    'spec Start1010 1010','guide 1 1 u spec:Start1010','timber 1 20 20 role primary','place 1 on 1 at-line guide 1 +u +n',
    'guide 2 1 u param:2:0','timber 6 20 20 role primary','place 6 on 1 at-line guide 2 +u +n',
    'grid 1 on 1 u 3000','timber 5 20 20 role secondary','place 5 on 1 at-line grid 1 u 0 between t1 t6 +v +n','identity-ledger activate'])await line(command);
  const graph=await ok('source-inspect'),read=await ok('engineering-read'),sceneBefore=(await ok('dump')).text;
  const field=read.state.parameters.find(c=>c.id===2).fields.find(f=>f.id===0),node=graph.nodes.find(n=>n.key==='parameter-field:2:f0');
  const timberLength=async()=>{const r=await ok('references');return r.timbers.find(t=>t.id===5).geometry.length;};
  const beforeLength=await timberLength();assert.equal(beforeLength,2170,'R365_REAL_TIMBER_LENGTH_BEFORE');
  const f=fixture({native:ask}),w=f.w;w.observeNativeRevision(read);
  const pdf=new TextEncoder().encode('%PDF-1.4\n% authored native adoption fixture\n'),hash=await P.sha(pdf);
  const document={sourceHash:hash,referencePageId:'native-page',page:1,coordinateSpace:E.COORDINATES,pageWidth:300,pageHeight:200,rotationBasis:0,cropBasis:[0,0,300,200]};
  const target={projectScope:w.context().id,kind:'parameter-field',parameterId:2,fieldId:0,definitionPin:node.definitionFingerprint,valuePin:node.valueFingerprint,incarnation:node.incarnation};
  const link={evidenceId:'native-adoption',document,region:[1,1,10,10],target,observations:{drawing:{rawText:'3235',rawValue:'3235',unit:'mm',note:''},measurement:null},identityBasis:'ledger',adoption:null,
    humanConfirmation:{documentHash:hash,definitionPin:target.definitionPin,valuePin:target.valuePin,confirmedAt:'2026-11-03T12:00:00.000Z'}};
  const source={meta:{id:hash,hash,type:'application/pdf',name:'authored.pdf',size:pdf.length,path:'sources/'+hash},bytes:pdf};
  w.context().sources.set(hash,source);
  // The evidence page is an authored input fixture; the real adapter reads its
  // persisted document through ReferenceWorkspace, as it would for a PDF page.
  const page={id:document.referencePageId,sourceId:hash,page:1,imgW:300,imgH:200,crop:[0,0,300,200],mmPerPx:1,x:0,y:0,rot:0,opacity:1,locked:false,calibration:null,reviewRequired:false,records:[]};
  const group=w.group(1,true);group.activePageId=page.id;group.pages=[page];
  const bundle={schema:E.SCHEMA_V2,links:[link]};w.setFeatureAttachment(E.KIND,bundle,w.getProjectState().contextToken);
  f.env.window.EvidenceLinks=E;f.env.window.SourceInspector=S;f.env.SourceInspector=S;
  f.env.queueMicrotask=()=>{};f.env.MutationObserver=class{observe(){}};
  vm.runInContext(fs.readFileSync(process.env.EVIDENCE_APP_MODULE||require.resolve('../../geometry-web/evidence-links-app.js'),'utf8'),f.env);
  const app=f.env.window.EvidenceLinksApp,p=await preview('3235');assert.equal(p.valid,true);
  const live={document,target,identityStatus:'continuous'},plan=E.planAdoption(link,live,{type:'dimension',formula:false,rawValue:'3235',unit:'mm'});
  const intent={link,observation:'drawing',plan,stamp:w.getEvidenceState(),field:{type:field.type,expression:field.expression}};
  const count=w.history.undo.length;assert.equal(typeof app.prepareAdoption,'function','R365_REAL_APP_ADOPTION_ENTRY');await app.prepareAdoption(intent,p);
  assert.equal((await ok('dump')).text,sceneBefore,'R365_REAL_PREPARE_PRESERVES_WORLD');assert.deepEqual(w.readFeatureAttachment(E.KIND),bundle);
  const receipt=await f.api('engineering-confirm '+p.token);assert.equal(receipt.ok,true);
  assert.equal(w.history.undo.length,count+1,'R365_REAL_SINGLE_NATIVE_METADATA_HISTORY');
  const after=w.readFeatureAttachment(E.KIND),adopted=after.links[0],afterLength=await timberLength();
  assert.equal(afterLength,2205,'R365_REAL_TIMBER_LENGTH_AFTER');assert.equal(adopted.adoption.literal,'3235');
  const afterGraph=await ok('source-inspect'),afterNode=afterGraph.nodes.find(n=>n.key===node.key);
  assert.equal(adopted.target.definitionPin,afterNode.definitionFingerprint);assert.equal(adopted.target.valuePin,afterNode.valueFingerprint);
  assert.equal(E.assessBound(adopted,{document,target:adopted.target,identityStatus:'continuous'},{identityStatus:'continuous'}).status,'confirmed-content');
  const sceneAfter=(await ok('dump')).text;
  await f.api('line undo');assert.equal((await ok('dump')).text,sceneBefore,'R365_REAL_UNDO_WORLD');assert.deepEqual(w.readFeatureAttachment(E.KIND),bundle,'R365_REAL_UNDO_ATTACHMENT');
  await f.api('line redo');assert.equal((await ok('dump')).text,sceneAfter);assert.deepEqual(w.readFeatureAttachment(E.KIND),after);
  const manifest={projectId:w.context().id,name:'adopted native fixture',faces:[],sources:[source.meta],featureAttachments:{schema:P.Features.SCHEMA,records:w.context().featureAttachments}};
  const packed=await P.pack(sceneAfter,manifest,new Map([[hash,pdf]]),zip),opened=await P.unpack(packed,zip);
  assert.equal(opened.scene,sceneAfter);assert.deepEqual(opened.manifest.featureAttachments.records[0].value,after,'R365_REAL_ZIP_ADOPTION_PINS');
  assert.deepEqual(opened.sources.get(hash),pdf);
  const pathAfter=path.join(directory,'reopened.scene');fs.writeFileSync(pathAfter,opened.scene);const fresh=bridge();assert.equal((await fresh('loadfile '+pathAfter)).ok,true);
  const cold=S.index(await fresh('source-inspect'));assert.equal(E.identityStatusFromGraph(adopted.target,cold,opened.manifest.projectId),'continuous','R365_REAL_COLD_IDENTITY');
  assert.equal(cold.nodes.get(node.key).definitionFingerprint,adopted.target.definitionPin);
  console.log(JSON.stringify({ok:true,native:true,parameterBefore:field.value,parameterAfter:'3235',timber5Before:beforeLength,timber5After:afterLength,historyDelta:1,undoWorldAndAttachment:true,redoWorldAndAttachment:true,zipColdReopen:true}));
}
main().catch(error=>{console.error(error);process.exitCode=1;}).finally(()=>{for(const child of processes){child.stdin.end();child.kill();}});
