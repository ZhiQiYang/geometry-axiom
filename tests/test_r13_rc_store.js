'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),Module=require('node:module'),path=require('node:path');
const {R,make,available}=require('./fixtures/r13_rc_n1.cjs'),P=require('../geometry-web/project-store.js'),zip=require('../geometry-web/vendor/fflate/umd/index.js');
const {fixture}=require('./fixtures/reference_workspace_vm.cjs');
const envelope=value=>({schema:P.Features.SCHEMA,records:[P.Features.record(R.KIND,value)]});
const manifest=value=>({projectId:'n1-project',name:'人工RC',sources:[],faces:[],models:[],featureAttachments:envelope(value)});
const encode=new TextEncoder(),decode=new TextDecoder();
async function corrupt(bytes,change){const files=zip.unzipSync(bytes),m=JSON.parse(decode.decode(files['manifest.json']));change(m);files['manifest.json']=encode.encode(JSON.stringify(m));return zip.zipSync(files);}
test('R13_N1_H01 format22 host-only capability with exact old policies and unknown23 refusal',()=>{
 available();assert.equal(R.RC_CAPABILITY,'reconstruction-rc-data/1','R13_N1_RC_CAPABILITY');
 assert.deepEqual(P.supportedFormats,Array.from({length:22},(_,i)=>'geometry-canvas/'+(i+1)),'R13_N1_EXACT_FORMAT_22');
 assert.deepEqual(P.formatPolicy('geometry-canvas/22'),P.formatPolicy('geometry-canvas/21'));
 assert.throws(()=>P.formatPolicy('geometry-canvas/23'),undefined,'R13_N1_UNKNOWN_23');
 assert.ok(P.readerCapabilities([]).includes(R.RC_CAPABILITY),'R13_N1_READER_RC_CAPABILITY');assert.throws(()=>P.sceneCapabilities('requires '+R.RC_CAPABILITY+'\n'));
 assert.throws(()=>P.validateProjectCapabilities([R.RC_CAPABILITY]),undefined,'R13_N1_NOT_NATIVE_CAPABILITY');
 assert.deepEqual(P.Features.capabilities(envelope(make())),[R.CAPABILITY,R.RC_CAPABILITY]);
 assert.deepEqual(P.Features.capabilities(envelope(R.empty())),[R.CAPABILITY]);
});
test('R13_N1_H02 real ZIP cold unpack retains exact raw source confirmations axis and highwater',async()=>{
 for(const kind of ['rc-column','rc-beam']){
  const v=make(kind);const raw=R.edit(v,{type:'edit',id:'rd-1',fields:{width:{raw:'  未量 \u{1F4CF}',unit:null}}});
  const bytes=await P.pack('reset\n',manifest(raw),new Map(),zip),out=await P.unpack(bytes,zip);
  assert.equal(out.manifest.format,'geometry-canvas/22','R13_N1_RC_SELECTS_22');assert.deepEqual(out.manifest.featureAttachments,envelope(raw),'R13_N1_RC_ARCHIVE_EXACT');
  const fresh=await P.unpack(await P.pack(out.scene,out.manifest,out.sources,zip),zip);assert.deepEqual(fresh.manifest.featureAttachments,out.manifest.featureAttachments,'R13_N1_RC_SECOND_OPEN_EXACT');
 }
});
test('R13_N1_H03 downgrade stripping unknown and forged RC rejected before publish',async()=>{
 const bytes=await P.pack('reset\n',manifest(make()),new Map(),zip);
 for(const change of [m=>m.format='geometry-canvas/21',m=>m.format='geometry-canvas/23',m=>m.requiredCapabilities=m.requiredCapabilities.filter(x=>x!==R.RC_CAPABILITY),m=>m.featureAttachments.records[0].value.records[0].fields.width.confirmation.value++])
  await assert.rejects(P.unpack(await corrupt(bytes,change),zip),undefined,'R13_N1_RC_ARCHIVE_GATE');
 const room=R.edit(R.empty(),{type:'create'}),old=await P.pack('reset\n',manifest(room),new Map(),zip);
 assert.equal((await P.unpack(old,zip)).manifest.format,'geometry-canvas/21','R13_N1_ROOM_REMAINS_21');
 await assert.rejects(P.unpack(await corrupt(old,m=>{m.format='geometry-canvas/22';m.requiredCapabilities.push(R.RC_CAPABILITY);}),zip),undefined,'R13_N1_22_REQUIRES_RC');
 const unused=await P.pack('reset\n',{projectId:'old-project',name:'未用',sources:[],faces:[]},new Map(),zip);assert.equal((await P.unpack(unused,zip)).manifest.format,'geometry-canvas/1','R13_N1_UNUSED_UNCHANGED');
});
test('R13_N1_H04 real host history undo redo fresh branches and save format transitions',async()=>{
 available();const f=await fixture(),w=f.w,token=()=>w.getProjectState().contextToken;
 const first=w.reconstructionEdit({type:'create',kind:'rc-column',name:'柱'},token()),id=first.records[0].id;
 const data=()=>w.readFeatureAttachment(R.KIND),original=structuredClone(data());
 assert.deepEqual(w.tryLocalHistory('line undo'),{ok:true,local:true},'R13_N1_UNDO');assert.equal(data().records.length,0);assert.ok(data().nextId>=original.nextId,'R13_N1_UNDO_HIGHWATER');
 assert.deepEqual(w.tryLocalHistory('line redo'),{ok:true,local:true},'R13_N1_REDO');assert.deepEqual(data().records,original.records,'R13_N1_REDO_CONTENT');
 w.reconstructionEdit({type:'edit',id,fields:{x:{raw:'-',unit:null}}},token());assert.equal(data().records[0].fields.x.raw,'-');
 w.tryLocalHistory('line undo');assert.equal(data().records[0].fields.x.raw,'');w.reconstructionEdit({type:'edit',id,fields:{x:{raw:'2',unit:'mm'}}},token());assert.ok(data().records[0].revision>original.records[0].revision);
 w.reconstructionEdit({type:'delete',id},token());assert.equal(P.projectFormat(manifest(data()),'reset\n'),'geometry-canvas/21','R13_N1_DELETE_LAST_RC_21');
 w.tryLocalHistory('line undo');assert.equal(P.projectFormat(manifest(data()),'reset\n'),'geometry-canvas/22','R13_N1_RESTORE_RC_22');
 assert.equal(f.calls.filter(x=>x!=='dump'&&x!=='dump-deidentified').length,0,'R13_N1_NO_WORLD_WRITE');
});
test('R13_N1_H05 scenario-only RC requires root22 and retains leaf capability',async()=>{
 const v=make(),leaf=await P.unpack(await P.pack('reset\n',manifest(v),new Map(),zip),zip);
 const S=require('../geometry-web/scenario-snapshots.js');
 const archive=S.create({project:P,featureAttachments:{validate:P.Features.validate,references:P.Features.sourceIds},verifyProject:async()=>({ok:true,capabilities:[],final_objects:{boundaries:[],placements:[]},objects:[]})});
 await archive.capture(leaf,{scenarioId:'rc-A',label:'A'});const root={projectId:'n1-project',name:'root',sources:[],faces:[],scenarioCatalog:{schema:S.SCHEMA,scenarios:archive.list()}};
 const bytes=await P.pack('reset\n',root,new Map(),zip),loaded=await P.unpack(bytes,zip);
 assert.equal(loaded.manifest.format,'geometry-canvas/22','R13_N1_SCENARIO_ROOT_22');assert.ok(loaded.manifest.requiredCapabilities.includes(R.RC_CAPABILITY),'R13_N1_SCENARIO_ROOT_CAPABILITY');
 assert.deepEqual(loaded.manifest.scenarioCatalog.scenarios[0].snapshot.projectManifest.featureAttachments,envelope(v),'R13_N1_SCENARIO_LEAF_EXACT');
 await assert.rejects(P.unpack(await corrupt(bytes,m=>m.requiredCapabilities=m.requiredCapabilities.filter(x=>x!==R.RC_CAPABILITY)),zip),undefined,'R13_N1_SCENARIO_STRIPPING_REJECTED');
});
test('R13_N1_H06 exact frozen E1 reader accepts room21 rejects RC22 and preserves all21 policies',async()=>{
 const fixture=require('./fixtures/r13_n1_e1_reader.json'),source=require('node:zlib').gunzipSync(Buffer.from(fixture.gzip_base64,'base64'));
 assert.equal(fixture.base_sha,'470062e1806954ad87f2d94d302017c65f5e25f3','R13_N1_OLD_E1_FIXED_BASE');
 assert.equal(fixture.blob,'4443a1cffcbfb830b4ae3f26a30e74762663ece0','R13_N1_OLD_E1_BLOB');
 assert.equal(fixture.bytes,125913);assert.equal(source.length,125913,'R13_N1_OLD_E1_BYTES');assert.equal(fixture.sha256,'93d0b6ca01ba172da51042fb19fb6518849d4d6ca23e0c2949f8ea1f41e53be9');
 assert.equal(require('node:crypto').createHash('sha256').update(source).digest('hex'),'93d0b6ca01ba172da51042fb19fb6518849d4d6ca23e0c2949f8ea1f41e53be9','R13_N1_OLD_E1_HASH');
 const file=path.join(__dirname,'../geometry-web/project-store.js'),m=new Module(file,module);m.filename=file;m.paths=Module._nodeModulePaths(path.dirname(file));m._compile(source.toString('utf8'),file);const old=m.exports;
 assert.deepEqual(old.supportedFormats,Array.from({length:21},(_,i)=>'geometry-canvas/'+(i+1)),'R13_N1_OLD_E1_EXACT');
 for(const format of old.supportedFormats)assert.deepEqual(P.formatPolicy(format),old.formatPolicy(format),'R13_N1_PRIOR_POLICY_'+format);
 const v=make(),rc=await P.pack('reset\n',manifest(v),new Map(),zip);await assert.rejects(old.unpack(rc,zip),/版本不支援/,'R13_N1_OLD_E1_REFUSES_22');
 const room=await P.pack('reset\n',manifest(R.edit(R.empty(),{type:'create'})),new Map(),zip);
 assert.equal((await old.unpack(room,zip)).manifest.format,'geometry-canvas/21','R13_N1_OLD_E1_ACCEPTS_21');
 assert.equal((await P.unpack(rc,zip)).manifest.format,'geometry-canvas/22','R13_N1_NEW_ACCEPTS_22');
});
