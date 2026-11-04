/* Finite, shared adapters for the formal reader and A/B workspace. */
"use strict";
window.ScenarioIntegration = (() => {
  const P=GeometryProject, S=GeometryScenarioSnapshots, encoder=new TextEncoder();
  const finalScenes=new WeakMap();
  async function verifyProject(project,assertCurrent=()=>{}) {
    P.validate(project.manifest);
    const data=structuredClone({manifest:project.manifest,scene:project.scene});
    const readerOnly=P.readerCapabilities([],{cutting:true});
    data.manifest.requiredCapabilities=(data.manifest.requiredCapabilities||[]).filter(c=>!readerOnly.includes(c));
    const response=await fetch('/scenarios/verify-native',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(data),signal:AbortSignal.timeout(60000)});
    assertCurrent();
    if(!response.ok)throw new Error('無法完成隔離方案驗證（HTTP '+response.status+'）。');
    const receipt=await response.json();assertCurrent();
    if(receipt.ok!==true)throw new Error(receipt.message||receipt.error||'隔離方案驗證未成功。');
    if(P.Features.evidenceLinks(project.manifest.featureAttachments||{schema:P.Features.SCHEMA,records:[]}))
      P.validateEvidenceTargets(project.manifest,{ok:true,schema:'source-inspector/1',complete:true,
        nodes:Object.values(receipt.inventory.nodes).map(n=>({...n,id:String(n.id)}))});
    return receipt;
  }
  function create(assertCurrent=()=>{}) {
    const scenes=new Map(),archive=S.create({project:P,featureAttachments:{validate:P.Features.validate,references:P.Features.sourceIds},
      verifyProject:async project=>{const receipt=await verifyProject(project,assertCurrent);
        if(typeof receipt.final_scene!=='string'||receipt.scene_sha256!==project.manifest.sceneHash)throw new Error('隔離方案缺少可核對的原生最終定義。');
        scenes.set(receipt.scene_sha256,receipt.final_scene);return receipt;}});
    finalScenes.set(archive,scenes);return archive;
  }
  function finalScene(archive,id){const hash=archive.project(id).manifest.sceneHash,scenes=finalScenes.get(archive);
    if(!scenes?.has(hash))throw new Error('方案尚未取得原生最終定義，請重新比較。');return scenes.get(hash);}
  async function read(catalog,sources,assertCurrent=()=>{}) {
    const archive=create(assertCurrent);
    if(!catalog)return archive;
    P.ScenarioCatalog.validate(catalog);
    const files=Object.create(null),records=[],assets=new Set();
    for(const s of catalog.scenarios){
      const {snapshot,...record}=s;records.push({...record,assetHashes:snapshot.assetHashes});
      files['scenarios/'+s.scenarioId+'/manifest.json']=encoder.encode(JSON.stringify(snapshot.projectManifest));
      files['scenarios/'+s.scenarioId+'/world.scene']=encoder.encode(snapshot.worldScene);
      for(const hash of snapshot.assetHashes)assets.add(hash);
    }
    files['scenarios.json']=encoder.encode(JSON.stringify({schema:S.SCHEMA,scenarios:records,assets:[...assets].sort()}));
    for(const hash of assets){
      const source=sources.get(hash),bytes=source?.bytes||source;
      if(!(bytes instanceof Uint8Array)||bytes.length>P.MAX_SOURCE)throw new Error('方案原始資產已遺失。');
      files['assets/'+hash]=bytes.slice();
    }
    const total=Object.values(files).reduce((n,b)=>n+b.length,0);
    if(total>S.LIMITS.expandedBytes)throw new Error('方案閉包超過容量上限。');
    const bytes=await new Promise((resolve,reject)=>fflate.zip(files,{level:0},(e,b)=>e?reject(e):resolve(b)));
    assertCurrent();await archive.unpack(bytes,fflate);assertCurrent();return archive;
  }
  function exportCatalog(archive){return {schema:S.SCHEMA,scenarios:archive.list()};}
  function exportSources(archive){
    const sources=new Map();
    for(const s of archive.list()){
      const project=archive.project(s.scenarioId);
      for(const meta of project.manifest.sources)if(!sources.has(meta.id))sources.set(meta.id,{meta:structuredClone(meta),bytes:project.sources.get(meta.id)});
    }
    return sources;
  }
  return {create,read,verifyProject,finalScene,exportCatalog,exportSources};
})();
