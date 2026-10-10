const {test}=require('node:test'),assert=require('node:assert/strict');
const P=require('../geometry-web/project-store.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const profile={id:0,name:'零構件斷面',outline:[[0,0],[100,0],[100,60],[0,60]]};
const run={id:0,profileId:0,length:{kind:'literal',value:2400},placement:null};
const record=(kind,value)=>'section-profile '+kind+' '+Buffer.from(JSON.stringify(value)).toString('base64')+'\n';
const scene='requires section-profile/1\n'+record('profile',profile)+record('run',run);
const manifest={projectId:'profile-project',name:'Q38',sources:[],faces:[]};
async function mutateArchive(change){const bytes=await P.pack(scene,manifest,new Map(),zip),files=zip.unzipSync(bytes);const m=JSON.parse(new TextDecoder().decode(files['manifest.json']));change(m,files);m.sceneHash=require('node:crypto').createHash('sha256').update(files['world.scene']).digest('hex');files['manifest.json']=new TextEncoder().encode(JSON.stringify(m));return zip.zipSync(files);}
test('section data uses new /16 format and roundtrips empty profile and unplaced run exactly',async()=>{
 const bytes=await P.pack(scene,manifest,new Map(),zip),result=await P.unpack(bytes,zip);
 assert.equal(result.manifest.format,'geometry-canvas/16');
 assert.deepEqual(result.manifest.requiredCapabilities,['section-profile/1']);
 assert.equal(result.scene,scene);assert.deepEqual(result.manifest.models,[]);
});
test('stripped marker cannot pack or reopen',async()=>{
 const stripped=scene.replace('requires section-profile/1\n','');
 assert.throws(()=>P.sceneCapabilities(stripped),/section-profile/);
 await assert.rejects(()=>P.pack(stripped,manifest,new Map(),zip),/section-profile/);
 const bytes=await mutateArchive((_m,files)=>files['world.scene']=new TextEncoder().encode(stripped));
 await assert.rejects(()=>P.unpack(bytes,zip),/section-profile/);
});
test('old archive formats cannot carry new records, even with valid hashes',async()=>{
 for(const format of ['geometry-canvas/5','geometry-canvas/15']){
  const bytes=await mutateArchive(m=>m.format=format);
  await assert.rejects(()=>P.unpack(bytes,zip),/斷面|規則案例/);
 }
});
test('required declaration cannot be dropped or replaced by unknown capability',async()=>{
 for(const requiredCapabilities of [[],['section-profile/2']]){
  const bytes=await mutateArchive(m=>m.requiredCapabilities=requiredCapabilities);
  await assert.rejects(()=>P.unpack(bytes,zip),/斷面|能力/);
 }
});
test('reader grants support only when native full capability is present',()=>{
 assert.deepEqual(P.nativeReaderCapabilities(['engineering-spec/1','section-profile-native/1']),['engineering-spec/1']);
 assert.deepEqual(P.nativeReaderCapabilities(['engineering-spec/1','section-profile-native/1','section-profile/1']),['engineering-spec/1','section-profile/1']);
 assert.throws(()=>P.assertProjectCapabilities({requiredCapabilities:['section-profile/1']},['section-profile-native/1']));
 assert.throws(()=>P.assertProjectCapabilities({requiredCapabilities:['section-profile/1']},P.readerCapabilities(['section-profile-native/1'])));
 assert.deepEqual(P.sceneCapabilities('# section-profile ignored\nspec A 27\n'),[]);
});
test('native profile confirmation is a single ordinary history entry, no-op is not',()=>{
 const h=new P.ContextHistory(()=>({id:'test',sources:new Map(),groups:new Map(),models:[],faceProjections:new Map()}));
 h.observe('section-profile-confirm 12',{ok:true,history_changed:false},'service');assert.equal(h.undo.length,0);
 h.observe('section-profile-confirm 13',{ok:true,history_changed:true},'service');assert.equal(h.undo.length,1);
 h.observe('section-profile-cancel 14',{ok:true},'service');assert.equal(h.undo.length,1);
 h.observe('line undo',{ok:true},'service');assert.equal(h.undo.length,0);assert.equal(h.redo.length,1);
});
