/* #47 F4a: decorate the existing native schedule with native support facts.
 * Load after timber-schedule.js. No inference from endpoints, names or meshes. */
(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory;
  else root.TimberSchedule=factory(root.TimberSchedule);
})(typeof globalThis!=='undefined'?globalThis:this,core=>{
  'use strict';
  const id=n=>Number.isSafeInteger(n)&&n>=0&&n<=4294967295;
  const hash=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
  const pair=a=>Array.isArray(a)&&a.length===2&&a.every(Number.isSafeInteger)&&a[0]<a[1];
  const clone=x=>JSON.parse(JSON.stringify(x));
  const unknown=()=>({status:'unknown',relation:null});
  function ownerValid(a){
    return a===null || a && ['instanceId','memberId','bindingId','ruleId','ruleVersion'].every(k=>id(a[k])&&a[k]>0)&&
      ['ruleFingerprint','instanceFingerprint','bindingFingerprint'].every(k=>hash(a[k]));
  }
  const ownerFields=['instanceId','memberId','bindingId','ruleId','ruleVersion','ruleFingerprint','instanceFingerprint','bindingFingerprint'];
  const sameOwner=(value,expected)=>expected===null?value===null:ownerValid(value)&&value!==null&&ownerFields.every(key=>value[key]===expected[key]);
  function nativeFacts(references,snapshot){
    const rows=core.derive(references,snapshot.surface).rows,facts=new Map();
    for(const row of rows){
      let owner=null;
      if(row.assembly){
        const instances=(references.assembly?.instances||[]).filter(instance=>instance.value?.source?.id===row.assembly.instanceId&&
          instance.members?.some(member=>member.timberId===row.id&&member.memberId===row.assembly.memberId));
        if(instances.length!==1||!hash(instances[0].fingerprint))throw Error(`角材 ${row.id} 的支撐所有權來源無法核對。`);
        owner={...row.assembly,instanceFingerprint:instances[0].fingerprint};
      }
      facts.set(row.id,{surface:row.surface,owner});
    }
    return facts;
  }
  function endpoint(value,row,end,facts){
    if(!value || value.status==='unknown')return unknown();
    const r=value.relation,s=r?.source,axis=['+v','-v'].includes(row.dir)?'v':'u';
    if(value.status!=='exact'||!Number.isSafeInteger(value.at)||!pair(value.crossRange)||!r||
      r.surface!==row.surface||!s||!id(s.id)||r.stop?.axis!==axis||r.stop.at!==value.at||
      !pair(r.stop.range)||r.stop.range[0]>value.crossRange[0]||r.stop.range[1]<value.crossRange[1]||r.stop.fixity!=='fixed')
      throw Error(`角材 ${row.id} 的${end}支撐原生資料無法核對。`);
    if(r.kind==='timber-face'){
      const support=facts.get(s.id);
      if(s.kind!=='timber'||s.id===row.id||!['A0','A1','B0','B1','START','END'].includes(r.localFace)||
        !Array.isArray(r.normalWorld)||r.normalWorld.length!==3||!r.normalWorld.every(n=>[-1,0,1].includes(n))||
        r.normalWorld.reduce((v,n)=>v+n*n,0)!==1||!support||support.surface!==row.surface||!sameOwner(r.owner,support.owner))throw Error(`角材 ${row.id} 的支撐局部面與所有權來源無法核對。`);
    }else if(['outline-edge','hole-edge'].includes(r.kind)){
      if(!['boundary','placement'].includes(s.kind)||s.kind==='boundary'&&s.id===0||
        s.kind==='placement'&&s.id!==row.surface||!id(r.edgeIndex)||
        (r.kind==='hole-edge'?!id(r.holeIndex)||s.kind!=='boundary':r.holeIndex!==null)||
        r.localFace!==null||r.normalWorld!==null||r.owner!==null)throw Error(`角材 ${row.id} 的支撐邊身分無法核對。`);
    }else throw Error(`角材 ${row.id} 的支撐來源型別無法核對。`);
    return clone(value);
  }
  function derive(references,surface,ids=null){
    const snapshot=core.derive(references,surface,ids),projection=references.timberSupports;
    if(!projection){return {...snapshot,rows:snapshot.rows.map(row=>({...row,supports:{start:unknown(),finish:unknown()}}))};}
    if(projection.schema!=='native-timber-supports/1'||projection.sourceFingerprint!==snapshot.sourceFingerprint||
      !Array.isArray(projection.entries))throw Error('料單支撐來源版本不一致，請重新讀取。');
    const entries=new Map(),facts=nativeFacts(references,snapshot);
    const nativeTimbers=new Map(references.timbers.map(t=>[t.id,t]));
    for(const e of projection.entries){
      if(!id(e.id)||!id(e.surface)||entries.has(e.id)||!ownerValid(e.owner)||nativeTimbers.get(e.id)?.geometry?.surface!==e.surface)throw Error('料單支撐身分重複、無效或與原生來源無法核對。');
      entries.set(e.id,e);
    }
    const rows=snapshot.rows.map(row=>{
      const e=entries.get(row.id);
      if(!e)return {...row,supports:{start:unknown(),finish:unknown()}};
      if(e.surface!==row.surface || !sameOwner(e.owner,facts.get(row.id).owner))throw Error(`角材 ${row.id} 的支撐所有權來源無法核對。`);
      const supports={start:endpoint(e.start,row,'起端',facts),finish:endpoint(e.finish,row,'末端',facts)};
      const selector=row.selector==='依 R6 自動推導；支撐身分未提供'&&supports.start.status==='exact'&&supports.finish.status==='exact'?'依 R6 自動推導':row.selector;
      return {...row,selector,supports,supportOwner:clone(e.owner)};
    });
    return {...snapshot,rows,supportSourceFingerprint:projection.sourceFingerprint};
  }
  function label(value){
    if(value?.status!=='exact')return '未知／原生支撐身分未提供';
    const r=value.relation,o=r.owner;
    return r.kind==='timber-face'?`角材 ${r.source.id}／${r.localFace}${o?`（組構實例 ${o.instanceId}／member ${o.memberId}）`:''}`:
      `${r.source.kind==='boundary'?'邊界':'承載面'} ${r.source.id}／${r.kind==='hole-edge'?`h${r.holeIndex}`:''}e${r.edgeIndex}`;
  }
  function sourceText(row){return `${core.sourceText(row)}；起端：${label(row.supports?.start)}；末端：${label(row.supports?.finish)}`;}
  function csv(snapshot,order='id'){
    const empty=core.csv({...snapshot,rows:[]},order),header=empty.slice(0,-2);
    const columns=['support_source_fingerprint','start_support_provenance','finish_support_provenance'];
    const lines=core.sorted(snapshot.rows,order).map(row=>{
      const base=core.csv({...snapshot,rows:[row]},order);
      const cells=[snapshot.supportSourceFingerprint,JSON.stringify(row.supports?.start||unknown()),JSON.stringify(row.supports?.finish||unknown())];
      return base.slice(base.indexOf('\r\n')+2,-2)+','+cells.map(core.csvCell).join(',');
    });
    return [header+','+columns.map(core.csvCell).join(','),...lines].join('\r\n')+'\r\n';
  }
  return {...core,derive,sourceText,csv};
});
