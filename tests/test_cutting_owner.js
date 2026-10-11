/* Actual ReferenceWorkspace metadata owner; DOM and native transport are VM seams. */
const {test}=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const P=require('../geometry-web/project-store.js'),S=P.Features.Cutting;
const settings=()=>({kerf:3,allowance:0,minRemnant:300,stockTypes:[{key:1,name:'木材',section:[27,33],material:null,length:3636,endTrim:5}],remnants:[],nextStockKey:2,nextRemnantKey:1});
function fixture(){const env={GeometryProject:P,crypto,structuredClone,JSON,TextEncoder,TextDecoder,Uint8Array,Map,Set,WeakMap,console,AbortSignal,Blob,File,requestAnimationFrame:()=>1,CustomEvent:class{},
 window:{dispatchEvent(){},addEventListener(){}},document:{getElementById:()=>null,querySelectorAll:()=>[],addEventListener(){}},oc:{busy:false,faces:[],bmap:{},edit:null},fe:{feats:{}},connection:{phase:'ready'},setStatus(){},toast(){}};
 vm.runInNewContext(fs.readFileSync(require.resolve('../geometry-web/reference-workspace.js'),'utf8')+'\nglobalThis.owner=ReferenceWorkspace;',env);return {w:env.owner,env};}
test('actual owner rejects invalid, referenced-stock and stale/busy edits before history or revision changes',()=>{
 const {w,env}=fixture(),token=w.getProjectState().contextToken,s=S.addRemnant(settings(),{stockType:1,length:1000,headTrim:0,tailTrim:5});w.setFeatureAttachment(S.KIND,s,token);
 const before=JSON.stringify([w.getProjectState(),w.history.undo.length,w.readFeatureAttachment(S.KIND)]);
 for(const change of [s=>s.kerf=0,s=>s.stockTypes[0].section=[30,40],s=>s.stockTypes=[]]){const next=structuredClone(s);change(next);assert.throws(()=>w.setFeatureAttachment(S.KIND,next,token));assert.equal(JSON.stringify([w.getProjectState(),w.history.undo.length,w.readFeatureAttachment(S.KIND)]),before);}
 assert.throws(()=>w.setFeatureAttachment(S.KIND,s,'stale'));env.oc.busy=true;assert.throws(()=>w.setFeatureAttachment(S.KIND,s,token));assert.equal(JSON.stringify([w.getProjectState(),w.history.undo.length,w.readFeatureAttachment(S.KIND)]),before);
});
test('actual owner P-047 undo, redo and alternate edit allocate key 2 after key 1 was undone',()=>{
 const {w}=fixture(),token=w.getProjectState().contextToken;w.setFeatureAttachment(S.KIND,settings(),token);w.setFeatureAttachment(S.KIND,S.addRemnant(settings(),{stockType:1,length:1000,headTrim:0,tailTrim:5}),token);
 assert.equal(w.tryLocalHistory('line undo').ok,true);assert.equal(w.readFeatureAttachment(S.KIND).remnants.length,0);assert.equal(w.readFeatureAttachment(S.KIND).nextRemnantKey,2);
 assert.equal(w.tryLocalHistory('line redo').ok,true);assert.equal(w.readFeatureAttachment(S.KIND).remnants[0].key,1);w.tryLocalHistory('line undo');
 const next=S.addRemnant(w.readFeatureAttachment(S.KIND),{stockType:1,length:600,headTrim:0,tailTrim:0});w.setFeatureAttachment(S.KIND,next,w.getProjectState().contextToken);assert.equal(w.readFeatureAttachment(S.KIND).remnants[0].key,2);assert.equal(w.history.redo.length,0);
});
test('actual owner no-op and unrelated history do not modify declarations; caller aliases are detached',()=>{
 const {w}=fixture(),token=w.getProjectState().contextToken,s=settings();w.setFeatureAttachment(S.KIND,s,token);const state=JSON.stringify(w.getProjectState());w.setFeatureAttachment(S.KIND,s,token);assert.equal(JSON.stringify(w.getProjectState()),state);s.stockTypes[0].name='外部改寫';assert.equal(w.readFeatureAttachment(S.KIND).stockTypes[0].name,'木材');
 const before=JSON.stringify(w.readFeatureAttachment(S.KIND));w.history.changeModels([]);w.tryLocalHistory('line undo');w.tryLocalHistory('line redo');assert.equal(JSON.stringify(w.readFeatureAttachment(S.KIND)),before);
});
