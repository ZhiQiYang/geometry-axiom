/* Formal root catalog. Leaf projects never contain another catalog. */
(function(root,factory){
  const api=factory(typeof module==='object'&&module.exports?require('./feature-attachments.js'):root.GeometryFeatureAttachments);
  if(typeof module==='object'&&module.exports)module.exports=api;else root.GeometryScenarioCatalog=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(Features){
  'use strict';
  const SCHEMA='geometry-scenario-snapshots/1';
  const LIMITS={assets:256,origins:25000,objects:25000,manifestBytes:8*1024*1024};
  const HASH = /^[a-f0-9]{64}$/, ID = /^[\w-]{1,100}$/;
  const identifier=v=>typeof v==='string'&&ID.test(v);
  const KINDS = new Set(['boundary','placement','space','column','beam','timber','grid','grid-system','grid-binding',
    'parameter','assembly-rule','assembly-binding','material','method','application','datum','model',
    'engineering-draft','assembly-draft','reference-page','grid-draft','spec','guide','assembly-instance']);
  function fail(code, message) { throw Object.assign(new Error(message), {code}); }
  const exact = (v, required, optional=[]) => v && typeof v === 'object' && !Array.isArray(v) &&
    required.every(k => Object.hasOwn(v,k)) && Object.keys(v).every(k => required.includes(k)||optional.includes(k));
  const copy = v => JSON.parse(JSON.stringify(v));
  function canonical(v) {
    if (v===null||typeof v!=='object') return JSON.stringify(v);
    if (Array.isArray(v)) return '['+v.map(canonical).join(',')+']';
    return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
  }
  const refKey=v=>canonical([v.kind,v.id,v.version]);
  function validObject(v) {
    return exact(v,['kind','id','version'])&&KINDS.has(v.kind)&&
      (typeof v.id==='string'&&v.id.length>0&&v.id.length<=100&&!/[\u0000-\u001f]/.test(v.id)||
        Number.isSafeInteger(v.id)&&v.id>=0&&v.id<=4294967295)&&
      (v.version===null||Number.isSafeInteger(v.version)&&v.version>0);
  }
  const validRef=v=>exact(v,['scenarioId','kind','id','version'])&&identifier(v.scenarioId)&&validObject({kind:v.kind,id:v.id,version:v.version});
  function validateRecord(s,table,limits=LIMITS) {
      if(!exact(s,['scenarioId','label','basis','snapshot','originMapping','objects','requiredCapabilities','closureHash'])||
        !identifier(s.scenarioId)||typeof s.label!=='string'||!s.label.trim()||s.label.length>200||!HASH.test(s.closureHash)||
        !exact(s.snapshot,['projectManifest','worldScene','assetHashes'])||
        !Array.isArray(s.snapshot.assetHashes)||s.snapshot.assetHashes.length>limits.assets||
        new Set(s.snapshot.assetHashes).size!==s.snapshot.assetHashes.length||!s.snapshot.assetHashes.every(h=>HASH.test(h))||
        !Array.isArray(s.originMapping)||s.originMapping.length>limits.origins||!Array.isArray(s.objects)||s.objects.length>limits.objects||
        !s.objects.every(validObject)||new Set(s.objects.map(refKey)).size!==s.objects.length||
        !Array.isArray(s.requiredCapabilities)||new Set(s.requiredCapabilities).size!==s.requiredCapabilities.length||
        s.requiredCapabilities.some(c=>typeof c!=='string'||c.length>100))fail('SCENARIO','Invalid complete scenario record.');
      Features.jsonBytes({...s,snapshot:{...s.snapshot,worldScene:''}},limits.manifestBytes);
      if(canonical(s.snapshot.assetHashes)!==canonical(s.snapshot.projectManifest.sources.map(v=>v.id).sort())||
        canonical(s.requiredCapabilities)!==canonical([...(s.snapshot.projectManifest.requiredCapabilities||[])].sort()))
        fail('ASSET_CLOSURE','Scenario assets/capabilities differ from the complete manifest.');
      if(s.basis!==null&&(!exact(s.basis,['scenarioId','snapshotHash'])||!identifier(s.basis.scenarioId)||s.basis.scenarioId===s.scenarioId||!HASH.test(s.basis.snapshotHash)))
        fail('ORIGIN','Invalid scenario copy basis.');
      const from=new Set(),to=new Set(),ownObjects=new Set(s.objects.map(refKey));
      const base=s.basis===null?null:table.get(s.basis.scenarioId),baseObjects=new Set((base?.objects||[]).map(refKey));
      if(base&&s.snapshot.projectManifest.projectId!==base.snapshot.projectManifest.projectId)
        fail('PROJECT_IDENTITY','A copy basis cannot cross project identities.');
      if(s.originMapping.length&&(!base||canonical(s.snapshot)!==canonical(base.snapshot)))
        fail('ORIGIN','Copy origins require an exact archived fork; replacement has no proven object continuity.');
      for(const pair of s.originMapping) {
        if(!exact(pair,['from','to','snapshotHash'])||!validRef(pair.from)||!validRef(pair.to)||
          pair.to.scenarioId!==s.scenarioId||pair.from.scenarioId!==s.basis?.scenarioId||pair.snapshotHash!==s.basis?.snapshotHash||
          pair.from.kind!==pair.to.kind||pair.from.id!==pair.to.id||pair.from.version!==pair.to.version||
          !ownObjects.has(refKey(pair.to))||from.has(refKey(pair.from))||to.has(refKey(pair.to)))fail('ORIGIN','Invalid typed copy-origin pair.');
        if(!base||base.closureHash!==pair.snapshotHash||!baseObjects.has(refKey(pair.from)))
          fail('ORIGIN','Copy-origin basis is absent or changed.');
        from.add(refKey(pair.from));to.add(refKey(pair.to));
      }
      if(s.basis!==null&&(!table.has(s.basis.scenarioId)||table.get(s.basis.scenarioId).closureHash!==s.basis.snapshotHash))
        fail('ORIGIN','Scenario basis must remain retained at its captured hash.');
    }
  function validate(value){
    Features.jsonBytes(value,LIMITS.manifestBytes);
    if(!exact(value,['schema','scenarios'])||value.schema!==SCHEMA||!Array.isArray(value.scenarios)||
       !value.scenarios.length||value.scenarios.length>8)fail('SCHEMA','Unsupported or oversized root scenario catalog.');
    const table=new Map();
    for(const s of value.scenarios){
      if(!identifier(s.scenarioId)||table.has(s.scenarioId)||!s.snapshot||
         !exact(s.snapshot.projectManifest,['format','projectId','name','sceneHash','sources','faces'],
           ['models','faceProjections','requiredCapabilities','engineeringDrafts','assemblyDrafts','reconstructionReviews','featureAttachments'])||
         typeof s.snapshot.worldScene!=='string'||new TextEncoder().encode(s.snapshot.worldScene).length>16*1024*1024)
        fail('SCENARIO','Invalid namespace or recursive leaf project.');
      table.set(s.scenarioId,s);
      for(const source of s.snapshot.projectManifest.sources||[])
        if(!exact(source,['id','hash','name','type','size','path']))fail('MANIFEST','Unknown leaf source fields.');
      for(const face of s.snapshot.projectManifest.faces||[]){
        if(!exact(face,['bid','activePageId','pages']))fail('MANIFEST','Unknown leaf face fields.');
        for(const page of face.pages||[]){
          if(!exact(page,['id','sourceId','page','imgW','imgH','crop','mmPerPx','x','y','rot','opacity','locked','calibration','reviewRequired','records']))
            fail('MANIFEST','Unknown leaf reference-page fields.');
          if(page.calibration&&!exact(page.calibration,['points','distanceMm','inputValue','inputUnit']))fail('MANIFEST','Unknown leaf calibration fields.');
          for(const record of page.records||[])if(!exact(record,['id','label','location','datum','unit','value']))fail('MANIFEST','Unknown leaf observation fields.');
        }
      }
    }
    for(const s of table.values()){
      validateRecord(s,table);
      const seen=new Set([s.scenarioId]);let basis=s.basis;
      while(basis){if(seen.has(basis.scenarioId))fail('ORIGIN','Cyclic copy basis.');seen.add(basis.scenarioId);basis=table.get(basis.scenarioId).basis;}
    }
    return value;
  }
  return {SCHEMA,validate,validateRecord,canonical};
});
