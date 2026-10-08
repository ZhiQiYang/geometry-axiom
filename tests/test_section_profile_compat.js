const {test}=require('node:test'),assert=require('node:assert/strict');
const P=require('../geometry-web/project-store.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const profile={id:0,name:'empty native profile',outline:[[0,0],[1,0],[1,1],[0,1]]};
const record='section-profile profile '+Buffer.from(JSON.stringify(profile)).toString('base64')+'\n';
const manifest={projectId:'profile-native-only',name:'Q38',sources:[],faces:[]};
test('unsupported profile scene refuses pack with or without its required marker',async()=>{
 for(const scene of [record,'requires section-profile/1\n'+record,'requires section-profile/1\n']){
  assert.throws(()=>P.sceneCapabilities(scene));
  await assert.rejects(()=>P.pack(scene,manifest,new Map(),zip));
 }
});
test('legacy archive containing stripped-marker profile records cannot reopen',async()=>{
 const bytes=await P.pack('reset\n',manifest,new Map(),zip),files=zip.unzipSync(bytes);
 const manifestValue=JSON.parse(new TextDecoder().decode(files['manifest.json']));
 const scenePath='world.scene';
 assert.ok(files[scenePath],Object.keys(files));
 files[scenePath]=new TextEncoder().encode(record);
 manifestValue.sceneHash=require('node:crypto').createHash('sha256').update(files[scenePath]).digest('hex');
 files['manifest.json']=new TextEncoder().encode(JSON.stringify(manifestValue));
 await assert.rejects(()=>P.unpack(zip.zipSync(files),zip),/section-profile/);
});
test('extra native capabilities do not reject legacy scenes or promise profile support',()=>{
 const supported=P.nativeReaderCapabilities(['engineering-spec/1','section-profile-native/1','section-profile/1']);
 assert.deepEqual(supported,['engineering-spec/1']);
 assert.deepEqual(P.sceneCapabilities('# section-profile ignored comment\nspec A 27\n'),[]);
 assert.throws(()=>P.validateProjectCapabilities(['section-profile/1']));
});
