// Native CR19's archive transport: actual project-store and ZIP, no UI mirror.
'use strict';
const fs=require('node:fs');
const assert=require('node:assert/strict');
const P=require('../../geometry-web/project-store.js');
const zip=require('../../geometry-web/vendor/fflate/umd/index.js');
(async()=>{
  const path=process.argv[2],scene=fs.readFileSync(path,'utf8');
  const bytes=await P.pack(scene,{format:P.FORMAT,projectId:'cr19',name:'CR19',sceneHash:'0'.repeat(64),sources:[],faces:[],models:[]},new Map(),zip);
  fs.writeFileSync(path+'.gcanvas',bytes);
  const fresh=await P.unpack(bytes,zip);
  assert.equal(fresh.manifest.format,'geometry-canvas/18','CARD_SAVE_ROUNDTRIP archive version');
  assert.deepEqual(fresh.manifest.requiredCapabilities,['grid-card-reference/1','parameters/1']);
  P.assertProjectCapabilities(fresh.manifest,P.readerCapabilities(['grid-card-reference/1','parameters/1']));
  assert.equal(fresh.scene,scene,'CARD_SAVE_ROUNDTRIP archive source bytes');
  fs.writeFileSync(path+'.reopened',fresh.scene);
  console.log('CR19 CARD_SAVE_ROUNDTRIP: /18 ZIP and source bytes verified');
})().catch(error=>{console.error(error);process.exitCode=1;});
