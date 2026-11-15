/* R22 manual correction: component/native acceptance, NOT browser acceptance.
 * Real RoomOutline, worker handler, RoomOutlineWorkspace, ReferenceWorkspace,
 * ContextHistory, ZIP reader/writer and fresh native bridge. Fake DOM events,
 * PDF operator-list provider and canvas decoding; no app.js / real Worker / UI.
 * The adapter explicitly drives native preview/confirm and observes its replies.
 * It does not assert that the App's event routing or OS picker works.
 */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const vm=require('node:vm'),crypto=require('node:crypto'),zlib=require('node:zlib');
const {spawn,execFileSync}=require('node:child_process'),{createInterface}=require('node:readline');
const ROOT=path.resolve(__dirname,'../..'),OUT=path.resolve(process.env.GEOMETRY_ROOM_REVIEW_OUT||'');
assert.ok(process.env.GEOMETRY_ROOM_REVIEW_OUT,'explicit output directory required');
assert.ok(!fs.existsSync(OUT),'output must be new; never replace a prior receipt');
fs.mkdirSync(OUT,{recursive:true});
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const clone=x=>JSON.parse(JSON.stringify(x));
const P=require('../../geometry-web/project-store.js'),R=require('../../geometry-web/room-outline.js');
const PolyDraft=require('../../geometry-web/polydraft.js'),zip=require('../../geometry-web/vendor/fflate/umd/index.js');
const {fixture}=require('../fixtures/reference_workspace_vm.cjs');
const {shapes,pdf}=require('../room_outline_fixture.js');
const bridgePath=process.env.GEOMETRY_TEST_BRIDGE;
assert.ok(bridgePath,'fresh bridge required through run_room_manual_review.py');
const checks=[],transcript=[],children=[];
const sources=['geometry-web/room-outline.js','geometry-web/room-outline-worker.js',
  'geometry-web/room-outline-workspace.js','geometry-web/reference-workspace.js',
  'geometry-web/project-store.js','geometry-web/feature-attachments.js','geometry-web/polydraft.js',
  'geometry-web/vendor/fflate/umd/index.js','tests/room_outline_fixture.js',
  'tests/fixtures/reference_workspace_vm.cjs','tests/diagnostics/room_manual_review.cjs',
  'tests/diagnostics/run_room_manual_review.py'];
const receipt={protocol:'r22-manual-review-component-native/1',startedUtc:new Date().toISOString(),
  head:execFileSync('git',['rev-parse','HEAD'],{cwd:ROOT,encoding:'utf8'}).trim(),
  node:process.version,command:[process.execPath,...process.argv.slice(1)],
  mutation:process.env.GEOMETRY_ROOM_REVIEW_MUTATION||null,
  bridge:{path:bridgePath,sha256:hash(fs.readFileSync(bridgePath)),
    sidecar:JSON.parse(fs.readFileSync(bridgePath+'.fingerprint.json','utf8'))},
  sourceHashes:Object.fromEntries(sources.map(f=>[f,hash(fs.readFileSync(path.join(ROOT,f)))])),
  boundaries:{browser:false,appRouting:false,pdfDecoding:false,canvasDecoding:false,realWorker:false,
    nativeBridge:true,productionWorkspaceHandlers:true,productionArchive:true,
    privatePDF:false,physicalDevice:false,humanTiming:false},checks,children};
function check(label,condition,detail){
  const row={label,ok:condition===true,...(detail===undefined?{}:{detail})};checks.push(row);
  console.log((row.ok?'PASS ':'FAIL ')+label);assert.ok(row.ok,label);
}
function same(a,b){return JSON.stringify(a)===JSON.stringify(b);}
// Exact sequence assertion: these fixtures have an explicit starting vertex.
// A bbox/area-only oracle would miss a notch or a rewired edge graph.
function ring(actual,expected,label){check(label,same(actual,expected),{actual:clone(actual),expected});}
async function rejects(label,fn,pattern){
  let error;try{await fn();}catch(e){error=e;}
  check(label,!!error&&pattern.test(error.message),error?.message);
}
class Bridge {
  constructor(label){
    this.label=label;this.pending=[];this.stderr='';
    this.child=spawn(bridgePath,[],{cwd:ROOT,stdio:['pipe','pipe','pipe']});
    const info={label,pid:this.child.pid};children.push(info);
    this.child.stderr.on('data',b=>{this.stderr+=b;});
    createInterface({input:this.child.stdout}).on('line',line=>{
      const waiter=this.pending.shift();
      if(!waiter)throw Error('unexpected native reply: '+line);
      let response;try{response=JSON.parse(line);}catch(e){waiter.reject(e);return;}
      transcript.push({process:label,command:waiter.command,response});waiter.resolve(response);
    });
    this.ended=new Promise(resolve=>this.child.on('close',(code,signal)=>{
      Object.assign(info,{exit:code,signal,stderr:this.stderr});
      for(const waiter of this.pending.splice(0))waiter.reject(Error('bridge closed: '+JSON.stringify(info)));
      resolve(info);
    }));
    this.child.on('error',e=>{for(const waiter of this.pending.splice(0))waiter.reject(e);});
  }
  send(command){return new Promise((resolve,reject)=>{this.pending.push({command,resolve,reject});this.child.stdin.write(command+'\n');});}
  async ok(command){const r=await this.send(command);assert.equal(r.ok,true,JSON.stringify({command,r}));return r;}
  async dump(){return (await this.ok('dump')).text;}
  async close(){this.child.stdin.end();const r=await this.ended;assert.equal(r.exit,0,JSON.stringify(r));}
}
// A deterministic public PNG and matching decoded pixels. Canvas decoding is
// substituted, so this is source-byte preservation, not an image-import test.
function raster(shape){
  const width=280,height=190,data=new Uint8ClampedArray(width*height*4).fill(255);
  for(let i=0;i<shape.points.length;i++){
    const a=shape.points[i],b=shape.points[(i+1)%shape.points.length];
    for(let y=Math.min(a[1],b[1])-2;y<Math.max(a[1],b[1])+2;y++)
      for(let x=Math.min(a[0],b[0])-2;x<Math.max(a[0],b[0])+2;x++)data.fill(0,(y*width+x)*4,(y*width+x)*4+3);
  }
  const crc=bytes=>{let c=0xffffffff;for(const n of bytes){c^=n;for(let i=0;i<8;i++)c=(c>>>1)^(c&1?0xedb88320:0);}return (c^0xffffffff)>>>0;};
  const chunk=(name,bytes)=>{const tag=Buffer.from(name),head=Buffer.alloc(4),tail=Buffer.alloc(4);head.writeUInt32BE(bytes.length);tail.writeUInt32BE(crc(Buffer.concat([tag,bytes])));return Buffer.concat([head,tag,bytes,tail]);};
  const header=Buffer.alloc(13);header.writeUInt32BE(width);header.writeUInt32BE(height,4);header[8]=8;header[9]=6;
  const rows=Buffer.alloc(height*(width*4+1));for(let y=0;y<height;y++)Buffer.from(data.buffer).copy(rows,y*(width*4+1)+1,y*width*4,(y+1)*width*4);
  return {width,height,data,bytes:Buffer.concat([Buffer.from('89504e470d0a1a0a','hex'),chunk('IHDR',header),chunk('IDAT',zlib.deflateSync(rows)),chunk('IEND',Buffer.alloc(0))])};
}
class Element {
  constructor(id,value=''){Object.assign(this,{id,value,dataset:{},isConnected:true,checked:false,disabled:false,listeners:new Map(),parentElement:{firstChild:{textContent:''}}});}
  addEventListener(type,fn){if(!this.listeners.has(type))this.listeners.set(type,[]);this.listeners.get(type).push(fn);}
  async fire(type,extra={}){const event={currentTarget:this,target:this,key:'',preventDefault(){this.defaultPrevented=true;},stopPropagation(){},...extra};for(const fn of this.listeners.get(type)||[])await fn(event);}
  click(){return this.fire('click');}
  focus(){}
  setAttribute(){}
}
const OPS={save:10,restore:11,transform:12,setLineWidth:2,constructPath:91,stroke:20,setDash:6};
const workerCode=fs.readFileSync(path.join(ROOT,'geometry-web/room-outline-worker.js'),'utf8');
let workspaceCode=fs.readFileSync(path.join(ROOT,'geometry-web/room-outline-workspace.js'),'utf8');
const mutations={
  'keep-reviewed-after-edit':['draft.dimensions=dimensions;draft.reviewed=false;','draft.dimensions=dimensions;'],
  'allow-unapplied-row':["if(rowsFor(draft)?.size){draft.reviewed=false;throw Error('逐邊尺寸尚未完成入值，請先核對或取消。');}",'']
};
if(receipt.mutation){const pair=mutations[receipt.mutation];assert.ok(pair);assert.equal(workspaceCode.split(pair[0]).length,2,'mutation must match exactly one production anchor');workspaceCode=workspaceCode.replace(...pair);}
receipt.effectiveWorkspaceSha256=hash(workspaceCode);
// Explicit synthetic user corrections, independent of the extractor/resize
// implementation: insert a notch, extend an L leg, or deepen an existing notch.
const corrections={
  rectangle:[[320,320],[2320,320],[2320,1480],[1720,1480],[1720,1280],[1280,1280],[1280,1480],[320,1480]],
  l:[[320,320],[2320,320],[2320,780],[1280,780],[1280,1520],[320,1520]],
  notch:[[320,320],[2320,320],[2320,1480],[1720,1480],[1720,1000],[1280,1000],[1280,1480],[320,1480]]
};

async function setup(kind,shape,index,bridge){
  let f;
  const native=async command=>{const r=await bridge.send(command);if(f)f.w.observe(command,r);return r;};
  f=await fixture({api:native});
  const {w,env}=f,pixels=raster(shape),bytes=kind==='pdf'?pdf():pixels.bytes,sourceHash=await P.sha(bytes);
  const source={meta:{id:sourceHash,hash:sourceHash,name:`public-${kind}-${shape.name}.${kind==='pdf'?'pdf':'png'}`,
    type:kind==='pdf'?'application/pdf':'image/png',size:bytes.length,path:'sources/'+sourceHash},bytes,
    doc:{numPages:8,getPage:async()=>({getOperatorList:async()=>({fnArray:[2,91],argsArray:[[4],[20,[new Float32Array([0,...shape.points[0],...shape.points.slice(1).flatMap(p=>[1,...p]),4])]]]}),getViewport:()=>({transform:[1,0,0,1,0,0]})})}};
  w.context().sources.clear();w.context().sources.set(sourceHash,source);
  const page={id:'review-page',sourceId:sourceHash,page:kind==='pdf'?index+1:1,imgW:280,imgH:190,crop:[0,0,280,190],mmPerPx:10,x:0,y:0,rot:0,opacity:.5,locked:false,
    calibration:{points:[[30,30],[230,30]],distanceMm:2000,inputValue:2000,inputUnit:'mm'},reviewRequired:true,records:[],src:'data:image/png;base64,synthetic'};
  w.group(1).pages=[page];w.group(1).activePageId=page.id;
  const hole={verts:[[500,500],[600,500],[600,600],[500,600]],fixity:[1,0,1,0]};
  await bridge.ok('line reset');
  await bridge.ok('line boundary 1 outline 0,0 4000,0 4000,3000 0,3000 hole 500,500 600,500 600,600 500,600 fixity F X F X');
  const original=await bridge.dump();
  env.oc.edit={bid:1};env.oc.bmap={1:[{verts:[[0,0],[4000,0],[4000,3000],[0,3000]],fixity:[1,1,1,1]},hole]};
  env.fe={tool:'select',zoom:1,draft:PolyDraft.createState(),feats:{}};
  Object.assign(env,{RoomOutline:R,PolyDraft,setTimeout,clearTimeout,innerWidth:1280,
    feUlMmToImg:(_p,x,y)=>[x/10,y/10],feUlImgToMm:(_p,x,y)=>[x*10,y*10],
    feSetTool:tool=>{env.fe.tool=tool;},feSyncDraftMirror(){},feLenShow(){},feSchedulePaint(){},
    Image:class {constructor(){this.naturalWidth=280;this.naturalHeight=190;}async decode(){}},
    Worker:class {
      constructor(){this.stopped=false;}
      terminate(){this.stopped=true;}
      postMessage(data){queueMicrotask(()=>{
        if(this.stopped)return;
        const self={postMessage:r=>this.onmessage({data:r})};
        vm.runInNewContext(workerCode,{RoomOutline:R,importScripts(){},self});self.onmessage({data});
      });}
    }});
  env.__pdfLibrary={OPS,AnnotationMode:{DISABLE:0}};
  const oldCreate=env.document.createElement;
  env.document.createElement=tag=>tag==='canvas'?{getContext:()=>({fillStyle:'',fillRect(){},drawImage(){},getImageData:()=>pixels})}:oldCreate(tag);
  let pane,api;
  const controls=new Map(),ordinary=env.document.getElementById;
  env.document.getElementById=id=>id==='faceInspectorContent'?pane:controls.get(id)||ordinary(id);
  function render(){
    if(pane){pane.isConnected=false;for(const e of controls.values())e.isConnected=false;}
    controls.clear();pane=new Element('faceInspectorContent');
    const html=api.paneHTML(1);
    for(const m of html.matchAll(/<(?:input|button|select|textarea|p|details)[^>]*\bid="([^"]+)"[^>]*>/g)){
      const tag=m[0],e=new Element(m[1],tag.match(/\bvalue="([^"]*)"/)?.[1]||'');
      e.checked=/\bchecked\b/.test(tag);e.disabled=/\bdisabled\b/.test(tag);
      const edge=tag.match(/data-room-edge-length="(\d+)"/);if(edge)e.dataset.roomEdgeLength=edge[1];
      controls.set(e.id,e);
    }
    if(controls.has('refRoomVertices'))controls.get('refRoomVertices').value=html.match(/<textarea[^>]*id="refRoomVertices"[^>]*>([^<]*)<\/textarea>/)[1];
    if(controls.has('refRoomMethod'))controls.get('refRoomMethod').value='auto';
    if(controls.has('refRoomEdge'))controls.get('refRoomEdge').value='0';
    pane.querySelector=s=>controls.get(s.slice(1))||null;
    pane.querySelectorAll=s=>s==='[data-room-edge-length]'?[...controls.values()].filter(e=>e.dataset.roomEdgeLength!==undefined):[];
    api.bindPane(pane,1);
  }
  env.renderFaceInspector=render;
  vm.runInNewContext(workspaceCode,env,{filename:'room-outline-workspace.js'});
  api=env.window.RoomOutlineWorkspace;render();
  const get=id=>{const e=controls.get(id);assert.ok(e,id);return e;};
  const click=id=>get(id).click();
  async function fill(id,value){const e=get(id);e.value=String(value);await e.fire('input');return e;}
  async function review(){const e=get('refRoomReviewed');e.checked=true;await e.fire('change');}
  async function acquire(){await click('refRoomPick');api.down({x:700,y:700});await api.up({x:700,y:700});assert.ok(api.pending(1),f.statuses.at(-1));}
  async function applyVertices(points){await fill('refRoomVertices',points.map(p=>p.join(',')).join('\n'));await click('refRoomApplyVertices');}
  async function syncGeometry(){const r=await bridge.ok('boundary 1');env.oc.bmap={1:clone(r.loops)};}
  return {w,env,api,get,click,fill,review,acquire,applyVertices,native,syncGeometry,original,page,source,hole,render};
}

async function scenario(kind,shape,index){
  const label=kind+'-'+shape.name,bridge=new Bridge(label);
  try{
    const f=await setup(kind,shape,index,bridge),{w,api,env}=f,expected=shape.inside.map(p=>p.map(n=>n*10));
    const originalCache=clone(env.oc.bmap);
    await f.acquire();ring(api.snapshot().points,expected,label+': acquired ordered ring');
    check(label+': provenance method',api.snapshot().method===(kind==='pdf'?'pdf-vector':'image-lines'));
    check(label+': acquisition preserves complete native scene',await bridge.dump()===f.original);
    await rejects(label+': Save rejects live candidate',()=>w.exportBytes(),/候選尚未確認/);
    const originalArchive=await P.pack(f.original,await w.manifest(),new Map([[f.source.meta.id,f.source.bytes]]),zip);
    check(label+': candidate absent from manifest',!(await w.manifest()).reconstructionReviews);
    await f.review();check(label+': explicit review permits beforeCommit',api.snapshot().reviewed);
    // Unapplied bad dimensions must invalidate the previous acknowledgement.
    const bad=await f.fill('refRoomEdgeLength0','1960.5');await bad.fire('blur');await f.review();
    check(label+': unapplied invalid row cannot be reviewed',api.snapshot().reviewed===false);
    await rejects(label+': invalid row blocks commit',()=>api.beforeCommit(),/重新核對|尚未完成入值/);
    ring(api.snapshot().points,expected,label+': fractional dimension is not rounded');
    const width=expected[1][0]-expected[0][0];
    const input=await f.fill('refRoomEdgeLength0',width+40);await input.fire('blur');
    const resized=clone(expected);resized[1][0]+=40;resized[2][0]+=40;
    ring(api.snapshot().points,resized,label+': dimension changes exact candidate edge');
    check(label+': one entered dimension marker',same(api.snapshot().dimensions,[{edge:0,length:width+40,kind:'user-confirmed-mm'}]));
    check(label+': editing leaves native and cached geometry unchanged',await bridge.dump()===f.original&&same(env.oc.bmap,originalCache));
    await f.review();await f.applyVertices(expected);
    check(label+': applying vertices clears acknowledgement',api.snapshot().reviewed===false);
    check(label+': vertex edit retires old entered dimension markers',api.snapshot().dimensions.length===0);
    // Each edge is explicitly entered, including both sides of a concavity.
    for(let edge=0;edge<expected.length;edge++){
      const a=expected[edge],b=expected[(edge+1)%expected.length],length=Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1]);
      await f.review();const e=await f.fill('refRoomEdgeLength'+edge,length);await e.fire('blur');
      ring(api.snapshot().points,expected,label+': edge '+edge+' preserves full ring');
      check(label+': edge '+edge+' requires renewed acknowledgement',api.snapshot().reviewed===false);
      check(label+': edge '+edge+' is the sole explicit dimension marker',same(api.snapshot().dimensions,[{edge,length,kind:'user-confirmed-mm'}]));
    }
    await f.review();
    // The native authority, rather than this orthogonality-only editor, rejects
    // a crossing whose bbox and integer/axis-aligned edge tests look plausible.
    const crossed=[[320,320],[2280,320],[2280,1200],[1000,1200],[1000,200],[500,200],[500,1480],[320,1480]];
    await f.applyVertices(crossed);await f.review();const invalid=api.beforeCommit();
    const crossing=await f.native('line preview boundary 1 outline '+crossed.map(p=>p.join(',')).join(' ')+' hole 500,500 600,500 600,600 500,600 fixity F X F X');
    check(label+': native rejects self-crossing candidate',!crossing.ok||crossing.preview?.valid===false,crossing);
    await f.native('line cancel-preview');api.afterCommit(invalid,false);
    check(label+': refusal keeps editable candidate but clears review',api.pending(1)&&!api.snapshot().reviewed);
    check(label+': refusal preserves complete scene',await bridge.dump()===f.original);
    await rejects(label+': refused candidate still blocks Save',()=>w.exportBytes(),/候選尚未確認/);
    await f.click('refRoomCancel');check(label+': cancel discards session candidate',!api.hasWork&&env.fe.draft.pts.length===0);
    const cancelled=await P.unpack(await w.exportBytes(),zip),initial=await P.unpack(originalArchive,zip);
    check(label+': cancelled archive has original scene, source and no receipt',cancelled.scene===f.original&&same(cancelled.manifest.faces,initial.manifest.faces)&&!cancelled.manifest.reconstructionReviews);
    await f.acquire();const corrected=corrections[shape.name];await f.applyVertices(corrected);
    ring(api.snapshot().points,corrected,label+': manual vertex correction is exact');
    check(label+': final correction differs from acquired ring',!same(corrected,expected));
    for(let edge=0;edge<corrected.length;edge++){
      const a=corrected[edge],b=corrected[(edge+1)%corrected.length],length=Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1]);
      const input=await f.fill('refRoomEdgeLength'+edge,length);await input.fire('blur');
      ring(api.snapshot().points,corrected,label+': corrected edge '+edge+' verified');
    }
    await f.review();const token=api.beforeCommit();
    const command='boundary 1 outline '+corrected.map(p=>p.join(',')).join(' ')+' hole 500,500 600,500 600,600 500,600 fixity F X F X';
    const preview=await f.native('line preview '+command);
    check(label+': native preview is valid',preview.ok&&preview.preview?.valid===true,preview);
    check(label+': preview preserves formal scene',await bridge.dump()===f.original);
    await f.native('line cancel-preview');api.afterCommit(token,false);
    check(label+': impact cancellation preserves scene and candidate',await bridge.dump()===f.original&&api.pending(1)&&!api.snapshot().reviewed);
    await f.review();const commit=api.beforeCommit(),next=await f.native('line preview '+command);
    assert.equal(next.preview.valid,true);assert.equal((await f.native('line confirm '+next.preview.token)).ok,true);
    await f.syncGeometry();env.fe.draft=PolyDraft.createState();api.afterCommit(commit,true);
    ring(env.oc.bmap[1][0].verts,corrected,label+': native confirmed corrected ordered ring');
    check(label+': confirmed replacement preserves hole and fixity',env.oc.bmap[1].length===2&&
      same(env.oc.bmap[1][1].verts,f.hole.verts)&&same(env.oc.bmap[1][1].fixity,f.hole.fixity));
    check(label+': confirmed source-bound receipt',w.reconstructionState(1)==='confirmed');
    const confirmed=await bridge.dump(),reviews=clone((await w.manifest()).reconstructionReviews);
    assert.equal((await f.native('line undo')).ok,true);await f.syncGeometry();
    check(label+': undo restores complete scene and source review',await bridge.dump()===f.original&&w.reconstructionState(1)==='unreviewed');
    assert.equal((await f.native('line redo')).ok,true);await f.syncGeometry();
    check(label+': redo restores complete scene and identical receipt',await bridge.dump()===confirmed&&same((await w.manifest()).reconstructionReviews,reviews)&&w.reconstructionState(1)==='confirmed');
    const bytes=await w.exportBytes(),file=path.join(OUT,label+'.gcanvas');fs.writeFileSync(file,bytes);
    const loaded=await P.unpack(new Uint8Array(fs.readFileSync(file)),zip),savedPage=loaded.manifest.faces[0].pages[0];
    check(label+': saved source bytes and calibration are exact',same([...loaded.sources.get(f.source.meta.id)],[...f.source.bytes])&&same(P.reference(savedPage),P.reference(w.active(1))));
    check(label+': saved review binds exact page and native loops',loaded.manifest.reconstructionReviews[0].basis===P.reviewBasis(savedPage)&&loaded.manifest.reconstructionReviews[0].geometry===P.outlineFingerprint(env.oc.bmap[1]));
    const cold=new Bridge(label+'-cold');
    try{
      await cold.ok('line reset');check(label+': cold native process starts blank',!(await cold.dump()).includes('boundary '));
      const sceneFile=path.join(OUT,label+'.scene');fs.writeFileSync(sceneFile,loaded.scene);
      await cold.ok('loadfile '+sceneFile);
      check(label+': cold native replay equals entire confirmed scene',await cold.dump()===confirmed);
    }finally{await cold.close();}
    // A changed calibration is a source alignment change, never geometry scaling.
    const p=w.active(1);p.mmPerPx=11;p.calibration.distanceMm=2200;p.calibration.inputValue=2200;api.invalidate();
    check(label+': recalibration invalidates review without scaling native geometry',w.reconstructionState(1)==='recheck'&&await bridge.dump()===confirmed);
  }finally{await bridge.close();}
}
(async()=>{
  try{
    for(const kind of ['pdf','image'])for(let i=0;i<shapes.length;i++)await scenario(kind,shapes[i],i);
    receipt.result='passed';
  }catch(e){receipt.result='failed';receipt.error={name:e.name,message:e.message,stack:e.stack};console.error(e);process.exitCode=1;}
  finally{
    receipt.endedUtc=new Date().toISOString();receipt.assertions=checks.length;
    fs.writeFileSync(path.join(OUT,'native-transcript.json'),JSON.stringify(transcript,null,2)+'\n');
    receipt.transcriptSha256=hash(fs.readFileSync(path.join(OUT,'native-transcript.json')));
    receipt.artifacts=Object.fromEntries(fs.readdirSync(OUT).map(f=>[f,{bytes:fs.statSync(path.join(OUT,f)).size,sha256:hash(fs.readFileSync(path.join(OUT,f)))}]));
    fs.writeFileSync(path.join(OUT,'result.json'),JSON.stringify(receipt,null,2)+'\n');
    console.log(JSON.stringify({result:receipt.result,assertions:receipt.assertions,out:OUT}));
  }
})();
