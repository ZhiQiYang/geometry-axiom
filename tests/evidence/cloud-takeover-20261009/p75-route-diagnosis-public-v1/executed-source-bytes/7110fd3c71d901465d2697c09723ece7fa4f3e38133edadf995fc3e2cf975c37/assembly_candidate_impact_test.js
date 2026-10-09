/* Trusted assembly UI with a public external/transitive dependency scene. */
'use strict';
module.exports=async({read,ctl,fill,wait,check})=>{
  const fs=require('node:fs'),path=require('node:path'),same=require('node:util').isDeepStrictEqual;
  const scene=fs.readFileSync(path.join(__dirname,'../tests/fixtures/assembly-external-dependencies.scene'),'utf8');
  await read(`(async()=>{AssemblyWorkspace.close();const r=await ReferenceWorkspace.uploadScene(${JSON.stringify(scene)});if(!r.ok)throw Error(r.error);resetSceneFocus();await renderObjects();})()`);
  // Named dimensions keep the transitive guides within D6a's public contract.
  const commands=['spec gapOne 100','spec gapTwo 200','guide 5 1 v timber:92:u:hi+spec:gapOne','timber 93 27 33 role primary','place 93 on 1 at-line guide 5 between t90 t91 +v +n','guide 6 1 v timber:93:u:lo+spec:gapTwo','timber 94 27 33 role primary','place 94 on 1 at-line guide 6 between t90 t91 +v +n'];
  await read(`(async()=>{for(const c of ${JSON.stringify(commands)}){let r=await apiRequest('line '+c);if(r.preview?.valid)r=await apiRequest('line confirm '+r.preview.token);if(!r.ok)throw Error(r.error);}await renderObjects();selectObject('assembly-binding',1);})()`);
  const snapshot=()=>read(`(async()=>({dump:(await apiRequest('dump')).text,refs:await apiRequest('references')}))()`);
  const before=await snapshot();
  await ctl('#asmInspectorOpen');await ctl('#asmEdit');await fill('#asmValue1A','40');
  const preview=async()=>{
    await read(`(()=>{const original=window.fetch;window.__impactRestore=()=>window.fetch=original;window.__impactPreview=null;window.fetch=async(...args)=>{const response=await original(...args);if(String(args[0])==='/assembly/preview')window.__impactPreview=(await response.clone().json()).preview;return response;};})()`);
    try{await ctl('#asmPreview');await wait(`!$('asmConfirm').disabled&&!!window.__impactPreview`);return await read('window.__impactPreview');}
    finally{await read('window.__impactRestore();void 0');}
  };
  const p=await preview(),rows=new Map(p.impact.timbers.map(t=>[t.id,t])),guides=new Map(p.impact.guides.map(g=>[g.id,g]));
  check('G10 完整候選包含外部與多跳角材，保留未變更支撐',p.valid&&[92,93,94].every(id=>rows.has(id))&&[90,91].every(id=>same(rows.get(id).before,rows.get(id).after)));
  check('G10 外部新舊幾何符合獨立整數座標',rows.get(92).before.length===1973&&rows.get(92).after.length===1960&&same(rows.get(92).after.origin,[520,987,2500])&&same(rows.get(93).after.origin,[2594,20,2500])&&same(rows.get(94).after.origin,[2781,20,2500])&&guides.get(5).after.off===2580&&guides.get(6).after.off===2767);
  check('G10 真UI顯示外部幾何與跨定位線依賴',await read(`['角材 #92（組構外）','角材 #93（組構外）','角材 #94（組構外）','長度 1973 mm','長度 1960 mm','世界位置 520,987,2500','定位線 #5','定位線 #6','未變更角材'].every(t=>$('asmPreviewResult').textContent.includes(t))`));
  check('G10 預覽未改正式世界',same(await snapshot(),before));
  await ctl('#asmCancel');check('G10 取消保留完整正式世界',same(await snapshot(),before)&&await read(`$('asmConfirm').disabled`));
  const shown=await preview();await ctl('#asmConfirm');await wait(`$('asmStatus')?.textContent.includes('已套用')`);
  const after=await snapshot();
  check('G10 確認恰為顯示候選的完整幾何',same(after.refs.timbers.map(t=>({id:t.id,geometry:t.geometry})),shown.impact.timbers.map(t=>({id:t.id,geometry:t.after})))&&same(after.refs.guides,shown.impact.guides.map(g=>g.after)));
  await ctl('#asmClose');
};
