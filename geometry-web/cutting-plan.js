/* R47-R50 deterministic, read-only evaluator. All dimensions come from native rows. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./cutting-settings.js'):root.CuttingSettings,
 typeof module==='object'&&module.exports?require('./timber-schedule.js'):root.TimberSchedule);if(typeof module==='object'&&module.exports)module.exports=api;else root.CuttingPlan=api;})(typeof globalThis!=='undefined'?globalThis:this,(Settings,Schedule)=>{
 'use strict';
 const uint=n=>Number.isSafeInteger(n)&&n>=0&&n<=4294967295,rank={INCOMPLETE:1,UNSUPPORTED:2,INVALID:3};
 const sameMaterial=(a,b)=>Settings.materialKey(a)===Settings.materialKey(b);
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
  const demands=new Map(),overlength=[];
  for(const row of [...rows.values()].sort((a,b)=>a.id-b.id)){
   const terminals=[];let bad=false;
   for(const field of ['A','B']){const source=row.sources.find(s=>s.target?.field===field);
    if(!source){terminals.push({kind:'literal'});continue;}
    if(!Object.hasOwn(source,'terminal')){diagnose('UNSUPPORTED','NATIVE_CAPABILITY',{timberId:row.id,field});bad=true;continue;}
    if(source.terminal===null){diagnose('INCOMPLETE','MATERIAL_UNRESOLVED',{timberId:row.id,field});bad=true;continue;}
    terminals.push(source.terminal);
   }
   if(bad)continue;
   let material=null;const [a,b]=terminals;
   if(a.kind==='material'||b.kind==='material'){
    if(a.kind!=='material'||b.kind!=='material'||!sameMaterial(a,b)){diagnose('INCOMPLETE','MATERIAL_MIXED',{timberId:row.id});continue;}
    material={id:a.id,version:a.version,fingerprint:a.fingerprint};
   }
   const section=[row.A,row.B],stock=settings.stockTypes.find(s=>Settings.sectionKey(s.section)===Settings.sectionKey(section)&&sameMaterial(s.material,material));
   if(!stock){const detail={timberId:row.id,section,material};
    if(material&&settings.stockTypes.some(s=>s.material?.id===material.id&&s.material.version===material.version&&s.material.fingerprint!==material.fingerprint))diagnose('INCOMPLETE','MATERIAL_FINGERPRINT_MISMATCH',detail);
    else if(material&&settings.stockTypes.some(s=>sameMaterial(s.material,material)))diagnose('INCOMPLETE','STOCK_SECTION_MISMATCH',detail);
    else diagnose('INCOMPLETE','NO_STOCK',detail);continue;
   }
   const C=row.L+(settings.allowance??0),maximum=Math.max(stock.length-2*stock.endTrim,...settings.remnants.filter(r=>r.stockType===stock.key).map(r=>r.length-r.headTrim-r.tailTrim));
   if(C>maximum)overlength.push({timberId:row.id,C,maximum});
   if(!demands.has(stock.key))demands.set(stock.key,[]);demands.get(stock.key).push({timberId:row.id,surface:row.surface,L:row.L,allowance:settings.allowance,C});
  }
  for(const detail of overlength)diagnose('INVALID','OVER_LENGTH',detail);
  const missing=['kerf','allowance','minRemnant'].filter(k=>settings[k]===null);if(missing.length)diagnose('INCOMPLETE','MISSING_SETTING',missing);
  if(p.diagnostics.length)return p;
  for(const stockType of [...settings.stockTypes].sort((a,b)=>a.key-b.key)){
   const pieces=demands.get(stockType.key);if(!pieces)continue;
   const candidates=settings.remnants.filter(r=>r.stockType===stockType.key).sort((a,b)=>(a.length-a.headTrim-a.tailTrim)-(b.length-b.headTrim-b.tailTrim)||a.key-b.key)
    .map(r=>({label:'R'+r.key,key:r.key,length:r.length,headTrim:r.headTrim,tailTrim:r.tailTrim,pieces:[]}));
   const group={stockTypeKey:stockType.key,stockType:JSON.parse(JSON.stringify(stockType)),kerf:settings.kerf,newStockCount:0,stocks:[],unusedRemnants:[],kerfLoss:0,trimLoss:0};
   let failed=false;
   for(const demand of [...pieces].sort((a,b)=>b.C-a.C||a.timberId-b.timberId)){
    const start=s=>s.pieces.length?s.pieces.at(-1).end+settings.kerf:s.headTrim;
    let s=candidates.find(s=>start(s)+demand.C<=s.length-s.tailTrim);
    if(!s){if(demand.C>stockType.length-2*stockType.endTrim){diagnose('INCOMPLETE','REMNANT_EXHAUSTED',{stockTypeKey:stockType.key,timberId:demand.timberId,reason:'本次找到的方案無法排入。'});failed=true;break;}
     s={label:`S${stockType.key}-N${++group.newStockCount}`,length:stockType.length,headTrim:stockType.endTrim,tailTrim:stockType.endTrim,pieces:[]};candidates.push(s);
    }
    const x=start(s);s.pieces.push({...demand,seq:s.pieces.length+1,start:x,end:x+demand.C});
   }
   if(failed)continue;
   for(const s of candidates){if(!s.pieces.length){group.unusedRemnants.push(s.key);continue;}delete s.key;
    const y=s.pieces.at(-1).end,trim=y===s.length-s.tailTrim;
    s.tail=trim?{kind:s.tailTrim?'trim':'none',consumed:s.tailTrim,cuts:s.tailTrim?1:0}:{kind:'separate',consumed:Math.min(settings.kerf,s.length-y),cuts:1};
    s.cuts=(s.headTrim>0?1:0)+s.pieces.length-1+s.tail.cuts;
    const length=s.length-y-s.tail.consumed,usable=Math.max(0,length-s.tailTrim);s.leftover=length?{length,usable,class:usable>=settings.minRemnant?'reusable':'waste'}:null;
    group.kerfLoss+=(s.pieces.length-1)*settings.kerf+(trim?0:s.tail.consumed);group.trimLoss+=s.headTrim+(trim?s.tail.consumed:0);group.stocks.push(s);
   }
   p.groups.push(group);
  }
  if(p.diagnostics.length){p.groups=[];return p;}
  p.status='COMPLETE';verify(p,[...rows.keys()]);return p;
 }
 function verify(plan,expectedIds=null){
  const ids=new Set();for(const g of plan.groups){let kerfLoss=0,trimLoss=0;
   for(const s of g.stocks){let y=s.headTrim;for(const [i,p]of s.pieces.entries()){
    if(ids.has(p.timberId))throw Error('DEMAND_IDENTITY：需求件重複。');ids.add(p.timberId);
    if(![p.C,p.start,p.end].every(Number.isSafeInteger)||p.C!==p.L+p.allowance||p.seq!==i+1||p.start!==y+(i?g.kerf:0)||p.end!==p.start+p.C||p.end>s.length-s.tailTrim)throw Error('CONSERVATION：件的位置或加工長度不守恆。');y=p.end;
   }
   const trim=y===s.length-s.tailTrim,consumed=trim?s.tailTrim:Math.min(g.kerf,s.length-y),left=s.length-y-consumed;
   if(s.tail.consumed!==consumed||s.tail.kind!==(trim?s.tailTrim?'trim':'none':'separate')||s.tail.cuts!==(trim?s.tailTrim?1:0:1)||s.cuts!==(s.headTrim?1:0)+s.pieces.length-1+s.tail.cuts||left<0||left!==(s.leftover?.length??0)||s.leftover&&s.leftover.usable!==Math.max(0,left-s.tailTrim)||s.headTrim+s.pieces.reduce((sum,p)=>sum+p.C,0)+(s.pieces.length-1)*g.kerf+consumed+left!==s.length)throw Error('CONSERVATION：修整、鋸縫或剩料不守恆。');
   kerfLoss+=(s.pieces.length-1)*g.kerf+(trim?0:consumed);trimLoss+=s.headTrim+(trim?consumed:0);
   }if(g.kerfLoss!==kerfLoss||g.trimLoss!==trimLoss)throw Error('CONSERVATION：耗損彙總不守恆。');
  }
  if(expectedIds&&(ids.size!==expectedIds.length||expectedIds.some(id=>!ids.has(id))))throw Error('DEMAND_IDENTITY：需求件遺失。');return true;
 }
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
