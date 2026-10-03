/* F4a: a read-only view of native placed timbers. No dimension evaluation. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.TimberSchedule=api;})(typeof globalThis!=='undefined'?globalThis:this,()=>{
  'use strict';
  const positive=n=>Number.isSafeInteger(n)&&n>0;
  const timberId=n=>Number.isSafeInteger(n)&&n>=0&&n<=4294967295;
  function assemblySource(references,t,g){
    const state=references.assembly,owners=[];
    for(const instance of state?.instances || [])for(const member of instance.members || [])
      if(member.timberId===t.id)owners.push({instance,member});
    if(!owners.length)return null;
    if(owners.length!==1)throw Error(`角材 ${t.id} 的生成來源身分不唯一。`);
    const {instance,member}=owners[0],source=instance.value?.source;
    const rule=state.rules?.find(r=>r.value.id===source?.rule?.id&&r.value.version===source.rule.version&&r.fingerprint===source.rule.fingerprint);
    const binding=state.bindings?.find(b=>b.value.id===source?.bindingId&&b.complete);
    const slotId=rule?.value.members.find(m=>m.id===member.memberId)?.slotId;
    const slot=binding?.value.slots.find(s=>s.slotId===slotId),effective=binding?.effective.find(s=>s.slotId===slotId);
    if(!slot||!effective||effective.A?.value!==g.A||effective.B?.value!==g.B)
      throw Error(`角材 ${t.id} 的生成尺寸來源尚未核對，料單未就緒。`);
    const provenance={instanceId:source.id,memberId:member.memberId,bindingId:source.bindingId,
      ruleId:source.rule.id,ruleVersion:source.rule.version,ruleFingerprint:source.rule.fingerprint,bindingFingerprint:binding.fingerprint};
    return {provenance,sources:['A','B'].map(field=>({target:{kind:'timber',id:t.id,field},
      source:JSON.parse(JSON.stringify(slot[field])),effective:effective[field].value,path:effective[field].path,override:false}))};
  }
  function derive(references,surface,ids=null){
    if(!references?.ok || !/^[a-f0-9]{64}$/.test(references.sourceFingerprint || '') || !positive(surface) || !Array.isArray(references.timbers))
      throw Error('無法核對原生角材來源，料單尚未就緒。');
    const selected=ids===null?null:new Set(ids),seen=new Set(),rows=[];
    if(selected && [...selected].some(id=>!timberId(id)))throw Error('料單範圍身分不合法。');
    for(const t of references.timbers){
      if(!timberId(t.id)||seen.has(t.id))throw Error('原生角材身分不合法或重複。');
      seen.add(t.id);const g=t.geometry;
      if(g?.surface!==surface || selected && !selected.has(t.id))continue;
      if(![g.A,g.B,g.length].every(positive)||!['+u','-u','+v','-v'].includes(g.dir)||!['+n','-n'].includes(g.side)||
          !g.origin?.every(Number.isSafeInteger)||g.origin.length!==3||!g.axes?.[0]?.every(Number.isSafeInteger))
        throw Error(`角材 ${t.id} 的正式完成尺寸尚未求值，未加入料單。`);
      const assembly=assemblySource(references,t,g);
      const sources=assembly?.sources || (references.engineeringSources || []).filter(s=>s.target?.kind==='timber'&&s.target.id===t.id);
      const finish=g.origin.map((v,i)=>v+g.axes[0][i]*g.length);
      if(!finish.every(Number.isSafeInteger))throw Error(`角材 ${t.id} 的端面座標超出精確範圍。`);
      rows.push({kind:'timber',id:t.id,surface,role:t.role,A:g.A,B:g.B,L:g.length,dir:g.dir,side:g.side,
        origin:[...g.origin],finish,anchor:t.definition?.anchor || '未提供',selector:t.definition?.selector || '依 R6 自動推導；支撐身分未提供',
        sources:JSON.parse(JSON.stringify(sources)),assembly:assembly?.provenance || null,sourceFingerprint:references.sourceFingerprint});
    }
    if(selected && rows.length!==selected.size)throw Error('所選角材已移除或不在此承載面，請重新選定範圍。');
    return {schema:'native-timber-schedule/1',surface,scope:ids===null?'surface':'selection',ids:rows.map(r=>r.id),rows,
      sourceFingerprint:references.sourceFingerprint};
  }
  function sorted(rows,order='id'){return [...rows].sort(order==='length'?(a,b)=>a.L-b.L||a.id-b.id:(a,b)=>a.id-b.id);}
  function dimension(mm,unit='mm'){return unit==='cm'?String(mm/10):String(mm);}
  function sourceText(row){const a=row.assembly,prefix=a?`組構實例 ${a.instanceId}／member ${a.memberId}；配置 ${a.bindingId}；規則 ${a.ruleId} 第 ${a.ruleVersion} 版；`:'';return prefix+(row.sources.length?row.sources.map(s=>`${s.target.field}: ${s.path || JSON.stringify(s.source)}${s.override?'（物件覆寫）':''}`).join('；'):'直接尺寸；材料未設定');}
  function csvCell(value){let s=String(value??'');if(/^[\s\u0000-\u001f]*[=+\-@]/u.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';}
  function csv(snapshot,order='id'){
    const header=['kind','timber_id','surface_id','role','A_mm','B_mm','finished_length_mm','direction','depth_side','dimension_source',
      'anchor','span_selector','start_world_mm','finish_world_mm','source_fingerprint','material','machining','dimension_source_definitions',
      'assembly_instance_id','assembly_member_id','binding_id','rule_id','rule_version','rule_fingerprint','binding_fingerprint'];
    return '\ufeff'+[header,...sorted(snapshot.rows,order).map(r=>[r.kind,r.id,r.surface,r.role,r.A,r.B,r.L,r.dir,r.side,sourceText(r),
      r.anchor,r.selector,JSON.stringify(r.origin),JSON.stringify(r.finish),r.sourceFingerprint,'未知／未設定','未知／未設定',JSON.stringify(r.sources),
      r.assembly?.instanceId,r.assembly?.memberId,r.assembly?.bindingId,r.assembly?.ruleId,r.assembly?.ruleVersion,r.assembly?.ruleFingerprint,r.assembly?.bindingFingerprint])]
      .map(line=>line.map(csvCell).join(',')).join('\r\n')+'\r\n';
  }
  return {derive,sorted,dimension,sourceText,csvCell,csv};
});
