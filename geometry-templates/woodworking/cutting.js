/* Fixed woodworking/1 cutting policy. Inputs are explicit native-derived rows
   and declarations; this provider never imports host stores, schedules or UI. */
(function(root,factory){
 'use strict';
 const api=factory(typeof module==='object'&&module.exports?require('../../geometry-core/interval-allocation.js'):root.GeometryIntervalAllocation);
 if(typeof module==='object'&&module.exports)module.exports=api;
 else Object.defineProperty(root,'GeometryWoodworkingCutting',{value:api});
})(typeof globalThis!=='undefined'?globalThis:this,Core=>{
 'use strict';
 if(!Core||typeof Core.verify!=='function'||!Object.isFrozen(Core))throw Error('固定裁切模板缺少共用區間驗證器。');
 const uint=n=>Number.isSafeInteger(n)&&n>=0&&n<=4294967295,key=n=>uint(n)&&n>0;
 const integer=(n,min=0)=>Number.isSafeInteger(n)&&n>=min&&n<=100000000;
 function fail(code,detail){throw Object.assign(Error(`${code}：${detail}`),{code});}
 function keys(v,required){return v!==null&&typeof v==='object'&&!Array.isArray(v)&&Object.getOwnPropertySymbols(v).length===0&&Object.keys(v).length===required.length&&required.every(k=>Object.getOwnPropertyDescriptor(v,k)?.enumerable&&Object.hasOwn(Object.getOwnPropertyDescriptor(v,k),'value'));}
 const materialKey=m=>m===null?'unset':JSON.stringify([m.id,m.version,m.fingerprint]);
 const sectionKey=s=>[...s].sort((a,b)=>a-b).join('x');
 const stockIdentity=s=>sectionKey(s.section)+':'+materialKey(s.material);
 const sameMaterial=(a,b)=>materialKey(a)===materialKey(b);
 const validSettingsFields=v=>(v.kerf===null||integer(v.kerf,1))&&(v.allowance===null||integer(v.allowance))&&(v.minRemnant===null||integer(v.minRemnant,1));
 function validateDeclarations(stockTypes,declaredRemnants){
  if(!Array.isArray(stockTypes)||!Array.isArray(declaredRemnants)||stockTypes.length>32||declaredRemnants.length>128)fail('CAPACITY','原材至多 32 種、宣告餘料至多 128 段。');
  const stocks=new Map(),identities=new Set(),remnants=new Set();
  for(const s of stockTypes){
   if(!keys(s,['key','name','section','material','length','endTrim'])||!key(s.key)||typeof s.name!=='string'||!s.name.length||new TextEncoder().encode(s.name).length>96||
     !Array.isArray(s.section)||s.section.length!==2||!s.section.every(n=>integer(n,1))||!integer(s.length,1)||!integer(s.endTrim)||s.endTrim>=s.length/2)fail('STOCK_INVALID','原材欄位、名稱、截面或可用長度不合法。');
   if(s.material!==null&&(!keys(s.material,['id','version','fingerprint'])||typeof s.material.id!=='string'||!/^[A-Za-z0-9_-]{1,64}$/.test(s.material.id)||!key(s.material.version)||!/^[a-f0-9]{64}$/.test(s.material.fingerprint)))fail('MATERIAL_INVALID','材料鍵須為完整的固定版本與內容指紋。');
   if(stocks.has(s.key)||identities.has(stockIdentity(s)))fail('STOCK_DUPLICATE','原材 key 或截面與材料鍵重複。');
   stocks.set(s.key,s);identities.add(stockIdentity(s));
  }
  for(const r of declaredRemnants){
   if(!keys(r,['key','stockType','length','headTrim','tailTrim'])||!key(r.key)||!key(r.stockType)||!stocks.has(r.stockType)||!integer(r.length,1)||!integer(r.headTrim)||!integer(r.tailTrim)||r.length-r.headTrim-r.tailTrim<1||remnants.has(r.key))fail('REMNANT_INVALID','餘料 key、原材引用或可用長度不合法。');
   remnants.add(r.key);
  }
  return {stockKeys:[...stocks.keys()],remnantKeys:[...remnants]};
 }
 function validateStockTransition(old,next){
  for(const s of old.stockTypes){const n=next.stockTypes.find(n=>n.key===s.key);if(n&&old.remnants.some(r=>r.stockType===s.key)&&stockIdentity(s)!==stockIdentity(n))fail('STOCK_TYPE_IN_USE','被宣告餘料引用的截面與材料鍵不可修改。');}
  return true;
 }
 function evaluateRows(rows,settings,p){
  if(!validSettingsFields(settings))fail('SETTINGS_INVALID','裁切設定欄位或整數不合法。');
  validateDeclarations(settings.stockTypes,settings.remnants);
  const rank=new Map([['INCOMPLETE',1],['UNSUPPORTED',2],['INVALID',3]]);
  const diagnose=(status,code,detail)=>{p.diagnostics.push({status,code,detail});if((rank.get(status)||0)>(rank.get(p.status)||0))p.status=status;};
  const demands=new Map(),overlength=[];
  for(const row of Array.from(rows).sort((a,b)=>a.id-b.id)){
   const terminals=[];let bad=false;
   const fields=['A','B'];for(const field of fields){const source=row.sources.find(s=>s.target?.field===field);
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
   const section=[row.A,row.B],stock=settings.stockTypes.find(s=>sectionKey(s.section)===sectionKey(section)&&sameMaterial(s.material,material));
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
  const missing=[['kerf',settings.kerf],['allowance',settings.allowance],['minRemnant',settings.minRemnant]].filter(([,value])=>value===null).map(([key])=>key);if(missing.length)diagnose('INCOMPLETE','MISSING_SETTING',missing);
  if(p.diagnostics.length)return p;
  for(const stockType of Array.from(settings.stockTypes).sort((a,b)=>a.key-b.key)){
   const pieces=demands.get(stockType.key);if(!pieces)continue;
   const candidates=settings.remnants.filter(r=>r.stockType===stockType.key).sort((a,b)=>(a.length-a.headTrim-a.tailTrim)-(b.length-b.headTrim-b.tailTrim)||a.key-b.key)
    .map(r=>({label:'R'+r.key,key:r.key,length:r.length,headTrim:r.headTrim,tailTrim:r.tailTrim,pieces:[]}));
   const group={stockTypeKey:stockType.key,stockType:JSON.parse(JSON.stringify(stockType)),kerf:settings.kerf,newStockCount:0,stocks:[],unusedRemnants:[],kerfLoss:0,trimLoss:0};
   let failed=false;
   for(const demand of Array.from(pieces).sort((a,b)=>b.C-a.C||a.timberId-b.timberId)){
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
  p.status='COMPLETE';verify(p,rows.map(row=>row.id));return p;
 }
 function verify(plan,expectedIds=null){
  const containers=[],observed=[],identities=Core.createIdentityTracker();
  const checked=action=>{try{return action();}catch(error){if(error.code==='DEMAND_IDENTITY')throw Error(error.reason==='duplicate'?'DEMAND_IDENTITY：需求件重複。':'DEMAND_IDENTITY：需求件遺失。');throw Error('CONSERVATION：件的位置或加工長度不守恆。');}};
  for(const g of plan.groups){let kerfLoss=0,trimLoss=0;
   for(const s of g.stocks){let y=s.headTrim;const allocations=[],consumptions=[{start:0,end:s.headTrim}];
    for(const [i,p]of s.pieces.entries()){
     const key={type:'timber',id:p.timberId};checked(()=>identities.add(key));observed.push(key);
     if(![p.C,p.start,p.end].every(Number.isSafeInteger)||p.C!==p.L+p.allowance||p.seq!==i+1||p.start!==y+(i?g.kerf:0))throw Error('CONSERVATION：件的位置或加工長度不守恆。');
     if(i)consumptions.push({start:y,end:p.start});
     const allocation={key,length:p.C,start:p.start,end:p.end};checked(()=>Core.verifyAllocation(allocation,[s.headTrim,s.length-s.tailTrim]));
     allocations.push(allocation);y=p.end;
    }
    const trim=y===s.length-s.tailTrim,consumed=trim?s.tailTrim:Math.min(g.kerf,s.length-y),left=s.length-y-consumed;
    if(s.tail.consumed!==consumed||s.tail.kind!==(trim?s.tailTrim?'trim':'none':'separate')||s.tail.cuts!==(trim?s.tailTrim?1:0:1)||s.cuts!==(s.headTrim?1:0)+s.pieces.length-1+s.tail.cuts||left<0||left!==(s.leftover?.length??0)||s.leftover&&s.leftover.usable!==Math.max(0,left-s.tailTrim))throw Error('CONSERVATION：修整、鋸縫或剩料不守恆。');
    consumptions.push({start:y,end:y+consumed});
    containers.push({length:s.length,usable:[s.headTrim,s.length-s.tailTrim],allocations,consumptions,remainder:{start:y+consumed,end:s.length}});
    kerfLoss+=(s.pieces.length-1)*g.kerf+(trim?0:consumed);trimLoss+=s.headTrim+(trim?consumed:0);
   }if(g.kerfLoss!==kerfLoss||g.trimLoss!==trimLoss)throw Error('CONSERVATION：耗損彙總不守恆。');
  }
  checked(()=>Core.verify({expected:observed,containers}));
  if(expectedIds&&(identities.size!==expectedIds.length||expectedIds.some(id=>!checked(()=>identities.has({type:'timber',id})))))throw Error('DEMAND_IDENTITY：需求件遺失。');
  return true;
 }
 const api={id:'woodworking/1',materialKey,sectionKey,stockIdentity,validSettingsFields,validateDeclarations,validateStockTransition,evaluateRows,verify};
 Object.values(api).filter(value=>typeof value==='function').forEach(Object.freeze);
 return Object.freeze(api);
});
