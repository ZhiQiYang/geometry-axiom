/* Shared VM/ZIP fixture used by the unchanged race suite and the separate
 * R07 save-warning increment. DOM/PDF/picker are fakes, not browser evidence. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const P=require('../../geometry-web/project-store.js');
const zip=require('../../geometry-web/vendor/fflate/umd/index.js');
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
async function fixture(options = {}) {
  const writes = [], statuses = [], written = deferred(), writeGate = options.writeGate || deferred();
  const calls = [], closing = deferred(), fetchReached = deferred();
  let aborts = 0, closes = 0;
  const elements = new Map();
  const element = id => {
    if (!elements.has(id)) elements.set(id, {textContent:'',dataset:{},classList:{toggle(){}},style:{},value:'',
      addEventListener(){},setAttribute(){},removeAttribute(){},replaceChildren(){},click(){},close(){this.open=false;},showModal(){this.open=true;},
      querySelector:()=>({}),parentElement:{clientWidth:800,clientHeight:600},append(){},prepend(){}});
    return elements.get(id);
  };
  const handle = {createWritable:async () => ({write:async bytes => {writes.push(bytes.slice());written.resolve();await writeGate.promise;},
    close:async()=>{closes++;closing.resolve();await options.closeGate?.promise;},abort:async()=>{aborts++;}})};
  const env = {GeometryProject:{...P,...options.projectOverride,...(options.packGate?{pack:async(...args)=>{await options.packGate.promise;return P.pack(...args);}}:{})},fflate:zip,crypto,structuredClone,JSON,TextEncoder,TextDecoder,Uint8Array,Map,Set,WeakMap,console,AbortSignal,BroadcastChannel:options.BroadcastChannel,
    requestAnimationFrame:()=>1,CustomEvent:class {},ResizeObserver:class {observe(){}},File,Blob,
    pageRuntimeVersion:"vm-runtime",checkApiSession(){},
    fetch:async (url,request)=>{if(url==="/rule-cases/prepare"&&options.casePrepare)return options.casePrepare(request);assert.equal(url,'data:image/png;base64,legacy');fetchReached.resolve();
      assert.ok(options.legacyGate,'Unexpected fetch: '+url);return options.legacyGate.promise;},
    window:{dispatchEvent(){},addEventListener(){},showSaveFilePicker:()=>options.pickerGate?.promise || Promise.resolve(handle),confirm:()=>false},
    document:{getElementById:element,querySelectorAll:()=>[],querySelector:()=>element('scroll'),addEventListener(){},
      createElement:tag=>tag==='canvas'?{getContext:()=>({}),toDataURL:()=> 'data:image/png;base64,rendered'}:element(tag)},
    oc:{busy:false,faces:[{id:1,kind:'boundary'}],bmap:{},edit:null},fe:{feats:{}},connection:{phase:'ready'},
    api:async command=>{if(options.api)return options.api(command);assert.ok(command==='dump'||command==='dump-deidentified','Unexpected API command: '+command);calls.push(command);return options.dumpGate ? options.dumpGate.promise : {ok:true,text:'boundary 1 outline 0,0 800,0 800,700 0,700\n'};},
    setStatus:s=>statuses.push(s),toast:s=>statuses.push(s),drawFaceEditor(){},renderFaceInspector(){},
    innerWidth:1280,feUlImgToMm:(_p,x,y)=>[x,y],feFit(){}};
  // Only the PDF library provider is faked here; production validation/cleanup
  // and save code execute unchanged. Real PDF worker coverage is in the app gate.
  env.__pdfLibrary=options.pdfLibrary;
  const workspaceCode=fs.readFileSync(process.env.GEOMETRY_TEST_REFERENCE_WORKSPACE || require.resolve('../../geometry-web/reference-workspace.js'),'utf8')
    .replace('if (!pdfLib) pdfLib = import(', 'if (globalThis.__pdfLibrary) return globalThis.__pdfLibrary; if (!pdfLib) pdfLib = import(');
  vm.runInNewContext(workspaceCode+'\nglobalThis.workspace=ReferenceWorkspace;',env);
  const w=env.workspace, bytes=new TextEncoder().encode('original PDF source bytes'),hash=await P.sha(bytes);
  const pageGates=new Map();
  const source={meta:{id:hash,hash,name:'圖.pdf',type:'application/pdf',size:bytes.length,path:'sources/'+hash},bytes,
    doc:{numPages:3,getPage:async number=>{await pageGates.get(number)?.promise;return {getViewport:({scale})=>({width:100*scale,height:80*scale}),render:()=>({promise:Promise.resolve()})};}}};
  w.context().sources.set(hash,source);
  for(let n=1;n<=3;n++)w.addPage(1,{id:'page-'+n,sourceId:hash,page:n,imgW:100,imgH:80,crop:[0,0,100,80],mmPerPx:10,
    x:0,y:0,rot:0,opacity:.5,locked:false,calibration:null,reviewRequired:false,records:[],...(n===1?{src:'data:image/png;base64,old'}:{})});
  w.group(1).activePageId='page-1';
  return {w,env,source,pageGates,writes,statuses,written,writeGate,handle,element,calls,closing,fetchReached,
    get aborts(){return aborts;},get closes(){return closes;}};
}

module.exports={fixture};
