/* H: one native snapshot, existing schedule extraction, fixed policy invocation and CSV. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./cutting-settings.js'):root.CuttingSettings,
 typeof module==='object'&&module.exports?require('./timber-schedule.js'):root.TimberSchedule,
 typeof module==='object'&&module.exports?require('../geometry-app/application.js').cutting:root.GeometryApplication.cutting);if(typeof module==='object'&&module.exports)module.exports=api;else root.CuttingPlan=api;})(typeof globalThis!=='undefined'?globalThis:this,(Settings,Schedule,Policy)=>{
 'use strict';
 const uint=n=>Number.isSafeInteger(n)&&n>=0&&n<=4294967295,rank={INCOMPLETE:1,UNSUPPORTED:2,INVALID:3};
 async function evaluate(references,settings,request){
  Settings.validate(settings);
  const p={status:'EMPTY',diagnostics:[],worldFingerprint:null,settingsFingerprint:await Settings.fingerprint(settings),label:'本次找到的方案',groups:[]};
  const diagnose=(status,code,detail)=>{p.diagnostics.push({status,code,detail});if((rank[status]||0)>(rank[p.status]||0))p.status=status;};
  if(!Array.isArray(request?.scopes))throw Error('REQUEST_INVALID：需求範圍必須是清單。');
  if(!request.scopes.length)return p;
  if(request.world?.kind!=='live'){diagnose('UNSUPPORTED','WORLD_KIND',request.world?.kind);return p;}
  if(request.scopes.length>64){diagnose('UNSUPPORTED','CAPACITY','需求範圍至多 64 個。');return p;}
  if(!references?.ok||!/^[a-f0-9]{64}$/.test(references.sourceFingerprint||'')||!Array.isArray(references.timbers)){diagnose('INCOMPLETE','WORLD_UNREADABLE','無法核對計量世界。');return p;}
  p.worldFingerprint=references.sourceFingerprint;
  const placements=new Map(references.timbers.map(t=>[t.id,t]));
  for(const scope of request.scopes){
   if(!uint(scope.surface)||scope.ids!==null&&(!Array.isArray(scope.ids)||scope.ids.some(id=>!uint(id)))){diagnose('INVALID','SCOPE_STALE',scope);return p;}
   if(scope.ids!==null&&scope.ids.some(id=>placements.get(id)?.geometry?.surface!==scope.surface)){diagnose('INVALID','SCOPE_STALE',scope);return p;}
  }
  const rows=new Map();
  for(const scope of request.scopes){let snapshot;
   try{snapshot=Schedule.derive(references,scope.surface,scope.ids);}catch(e){diagnose('INCOMPLETE','ROW_NOT_READY:'+e.code,{surface:scope.surface});continue;}
   if(!snapshot.rows.length)diagnose('INCOMPLETE','SCOPE_EMPTY',scope);
   for(const row of snapshot.rows)rows.set(row.id,row);
   if(rows.size>4096){p.diagnostics=[];p.status='EMPTY';diagnose('UNSUPPORTED','CAPACITY','需求件至多 4096 支，不截斷。');return p;}
  }
  return Policy.evaluateRows([...rows.values()],settings,p);
 }
 const verify=(plan,expectedIds=null)=>Policy.verify(plan,expectedIds);
 function csv(plan){
  if(plan.status!=='COMPLETE')throw Error('COMPLETE 方案才能匯出。');verify(plan);
  const lines=[['row_kind','plan_status','plan_label','world_fingerprint','settings_fingerprint','stock_type_key','stock_type_name','section_mm','material_id','material_version','material_fingerprint','stock_label','stock_length_mm','head_trim_mm','tail_trim_mm','kerf_mm','seq','timber_id','surface_id','finished_length_mm','allowance_mm','cut_length_mm','start_mm','end_mm','tail_kind','tail_consumed_mm','cuts','leftover_mm','leftover_usable_mm','leftover_class']];
  for(const g of plan.groups){const t=g.stockType;for(const s of g.stocks){const common=[plan.status,plan.label,plan.worldFingerprint,plan.settingsFingerprint,t.key,t.name,t.section.join('x'),t.material?.id,t.material?.version,t.material?.fingerprint,s.label,s.length,s.headTrim,s.tailTrim,g.kerf];
   for(const p of s.pieces)lines.push(['piece',...common,p.seq,p.timberId,p.surface,p.L,p.allowance,p.C,p.start,p.end,'','','','','','']);
   lines.push(['end',...common,'','','','','','','','',s.tail.kind,s.tail.consumed,s.cuts,s.leftover?.length,s.leftover?.usable,s.leftover?.class]);
  }}return '\ufeff'+lines.map(line=>line.map(Schedule.csvCell).join(',')).join('\r\n')+'\r\n';
 }
 return {evaluate,verify,csv};
});
