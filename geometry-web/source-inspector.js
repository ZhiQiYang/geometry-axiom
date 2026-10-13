/* F1a presentation/index adapter. Native fingerprints are opaque: no DSL/path guessing. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.SourceInspector=api;})(globalThis,()=>{
  'use strict';
  const LIMIT=48,DEPTH=6,HASH=/^[a-f0-9]{64}$/;
  const labels={dimension:'尺寸來源',position:'定位來源',containment:'所屬斷面','material-spec':'固定面材規格',profile:'斷面輪廓','rule-version':'固定規則版本','material-version':'固定材料版本',member:'成員對應','joint-definition':'接合規則定義（未生成也可存在）','span-candidate':'跨距求值候選（支撐未知）','confirmed-support':'原生已確認支撐'};
  const key=(kind,id,version=0,fieldId=0)=>`${kind}:${id}${version?':v'+version:''}${fieldId||kind==='parameter-field'?':f'+fieldId:''}`;
  const id=n=>Number.isSafeInteger(n)&&n>=0&&n<=4294967295,hash=s=>typeof s==='string'&&HASH.test(s),clone=x=>JSON.parse(JSON.stringify(x));
  const ownerFields=['instanceId','memberId','bindingId','ruleId','ruleVersion','ruleFingerprint','instanceFingerprint','bindingFingerprint'];
  const ownerValid=o=>o===null||o&&ownerFields.slice(0,5).every(k=>id(o[k])&&o[k]>0)&&ownerFields.slice(5).every(k=>hash(o[k]));
  const unknown=()=>({status:'unknown',relation:null});
  const pair=a=>Array.isArray(a)&&a.length===2&&a.every(Number.isSafeInteger)&&a[0]<a[1];
  function supports(data,nodes){
    const projection=data.timberSupports,result=new Map();if(projection==null)return result;
    if(projection.schema!=='native-timber-supports/1'||!hash(data.sourceFingerprint)||projection.sourceFingerprint!==data.sourceFingerprint||!Array.isArray(projection.entries)||projection.entries.length>2048)throw Error('支撐來源版本不一致，請重新檢查。');
    const edgeKey=(from,to,relation,field)=>JSON.stringify([from,to,relation,field]),edges=new Set(data.edges.filter(e=>e.active).map(e=>edgeKey(e.from,e.to,e.relation,e.field)));
    const hasEdge=(from,to,relation,field)=>edges.has(edgeKey(from,to,relation,field));
    function owner(value,node){
      const expected=node.nativeOwner;if(!ownerValid(value)||!ownerValid(expected)||(expected===null?value!==null:value===null||ownerFields.some(k=>value[k]!==expected[k])))throw Error('支撐所有權來源無法核對。');
      if(value===null)return true;
      const instance=key('assembly-instance',value.instanceId),binding=key('assembly-binding',value.bindingId),rule=key('assembly-rule',value.ruleId,value.ruleVersion),member=key('assembly-member',value.ruleId,value.ruleVersion,value.memberId);
      if(![instance,binding,rule,member].every(k=>nodes.has(k))){if(data.complete===false)return false;throw Error('支撐所有權的具型別來源缺失。');}
      // Rule fingerprints are canonical in this native index. Binding/instance
      // node fingerprints use a different scheme; their nativeOwner hashes do not.
      if(nodes.get(instance).kind!=='assembly-instance'||nodes.get(instance).id!==String(value.instanceId)||nodes.get(binding).kind!=='assembly-binding'||nodes.get(binding).id!==String(value.bindingId)||nodes.get(rule).kind!=='assembly-rule'||nodes.get(rule).id!==String(value.ruleId)||nodes.get(rule).version!==value.ruleVersion||nodes.get(member).kind!=='assembly-member'||nodes.get(member).id!==String(value.ruleId)||nodes.get(member).version!==value.ruleVersion||nodes.get(member).fieldId!==value.memberId||nodes.get(rule).definitionFingerprint!==value.ruleFingerprint||
        !hasEdge(node.key,instance,'member','member:'+value.memberId)||!hasEdge(instance,binding,'dimension','binding')||!hasEdge(instance,rule,'rule-version',value.ruleFingerprint)||!hasEdge(binding,rule,'rule-version','rule')||!hasEdge(rule,member,'member','members'))throw Error('支撐所有權的成員與固定版本無法核對。');
      return true;
    }
    function fact(n){return n?.kind==='timber'&&typeof n.id==='string'&&/^(0|[1-9][0-9]*)$/.test(n.id)&&id(Number(n.id))&&n.key===key('timber',Number(n.id))&&typeof n.placed==='boolean'&&id(n.surface)&&['u','v'].includes(n.lengthAxis);}
    function endpoint(value,node){
      if(!value||value.status==='unknown')return unknown();const r=value.relation,s=r?.source;
      if(value.status!=='exact'||!Number.isSafeInteger(value.at)||!pair(value.crossRange)||!r||r.surface!==node.surface||!s||!id(s.id)||r.stop?.axis!==node.lengthAxis||r.stop.at!==value.at||!pair(r.stop.range)||r.stop.range[0]>value.crossRange[0]||r.stop.range[1]<value.crossRange[1]||r.stop.fixity!=='fixed')throw Error('原生支撐端面資料無法核對。');
      const target=nodes.get(key(s.kind,s.id));if(!target){if(data.complete===false)return unknown();throw Error('原生支撐來源不存在。');}if(target.id!==String(s.id))throw Error('原生支撐來源身分無法核對。');
      if(r.kind==='timber-face'){
        if(s.kind!=='timber'||s.id===Number(node.id)||!fact(target)||!target.placed||target.surface!==node.surface||!['A0','A1','B0','B1','START','END'].includes(r.localFace)||!Array.isArray(r.normalWorld)||r.normalWorld.length!==3||!r.normalWorld.every(n=>[-1,0,1].includes(n))||r.normalWorld.reduce((sum,n)=>sum+n*n,0)!==1)throw Error('原生支撐局部面或承載面無法核對。');
        if(!owner(r.owner,target))return unknown();
      }else if(['outline-edge','hole-edge'].includes(r.kind)){
        if(!['boundary','placement'].includes(s.kind)||target.kind!==s.kind||s.kind==='boundary'&&s.id===0||s.kind==='placement'&&s.id!==node.surface||!id(r.edgeIndex)||(r.kind==='hole-edge'?!id(r.holeIndex)||s.kind!=='boundary':r.holeIndex!==null)||r.localFace!==null||r.normalWorld!==null||r.owner!==null||!nodes.has(key('placement',node.surface))||s.kind==='boundary'&&!hasEdge(key('placement',node.surface),target.key,'position','boundary'))throw Error('原生支撐邊的具型別來源無法核對。');
      }else throw Error('原生支撐型別未知。');
      return clone(value);
    }
    const seen=new Set();for(const e of projection.entries){
      if(!id(e.id)||!id(e.surface)||seen.has(e.id)||!ownerValid(e.owner))throw Error('原生支撐身分重複或無效。');seen.add(e.id);
      const node=nodes.get(key('timber',e.id));if(!node){if(data.complete===false)continue;throw Error('支撐所屬角材來源不存在。');}
      if(!fact(node)||!node.placed||node.surface!==e.surface)throw Error('支撐所屬角材放置資料無法核對。');
      if(!owner(e.owner,node)){result.set(node.key,{owner:null,start:unknown(),finish:unknown()});continue;}
      result.set(node.key,{owner:clone(e.owner),start:endpoint(e.start,node),finish:endpoint(e.finish,node)});
    }return result;
  }
  function index(data){
    if(data?.ok!==true||data.schema!=='source-inspector/1'||!Array.isArray(data.nodes)||!Array.isArray(data.edges)||data.nodes.length>2048||data.edges.length>8192||!Number.isSafeInteger(data.revision))throw Error('執行能力不足或來源尚未檢查。');
    const nodes=new Map(),out=new Map(),into=new Map();
    for(const n of data.nodes){if(typeof n.key!=='string'||nodes.has(n.key)||!HASH.test(n.definitionFingerprint)||!HASH.test(n.valueFingerprint))throw Error('來源資料不完整，無法可靠追溯。');nodes.set(n.key,n);}
    const add=e=>{if(!out.has(e.from))out.set(e.from,[]);out.get(e.from).push(e);if(!into.has(e.to))into.set(e.to,[]);into.get(e.to).push(e);};
    for(const e of data.edges){if(typeof e.from!=='string'||typeof e.to!=='string'||!labels[e.relation]||e.relation==='confirmed-support'||typeof e.active!=='boolean')throw Error('來源型別未知。');add(e);}
    const supportEntries=supports(data,nodes);for(const [from,entry] of supportEntries)for(const end of ['start','finish']){const value=entry[end];if(value.status==='exact')add({from,to:key(value.relation.source.kind,value.relation.source.id),relation:'confirmed-support',field:end,active:true,provenance:clone(value)});}
    return {data,nodes,out,into,supportEntries,hasSupportProjection:data.timberSupports!=null};
  }
  function nearby(graph,start,{direction='sources',limit=LIMIT,depth=DEPTH}={}){
    limit=Math.min(LIMIT,Math.max(1,limit));depth=Math.min(DEPTH,Math.max(0,depth));
    const visited=new Set([start]),queue=[[start,0]],rows=[];let truncated=!graph.data.complete;
    if(direction==='uses'&&graph.nodes.get(start)?.kind==='parameter')for(const e of graph.out.get(start)||[])if(e.relation==='member')queue.push([e.to,0]);
    while(queue.length){const [at,d]=queue.shift();const edges=(direction==='uses'?graph.into:graph.out).get(at)||[];
      for(const e of edges){if(!e.active)continue;const target=direction==='uses'?e.from:e.to;if(visited.has(target))continue;
        if(d>=depth||rows.length>=limit){truncated=true;continue;}visited.add(target);rows.push({edge:e,node:graph.nodes.get(target)||null,key:target,depth:d+1});queue.push([target,d+1]);}
    }return {rows,truncated,missing:rows.some(r=>!r.node)};
  }
  // Resolve only native, active typed relations. A boundary can have several
  // placements; neither card order nor the first face with that boundary is identity.
  function resolveLocation(graph,target){
    if(!target||!['guide','grid','timber','placement'].includes(target.kind)||!id(target.id))throw Error('定位資料不完整，請重新檢查。');
    const typed=(kind,identifier)=>{
      const n=graph.nodes.get(key(kind,identifier));
      if(!n||n.kind!==kind||n.id!==String(identifier)||n.key!==key(kind,identifier))throw Error('來源物件已缺失或型別不一致，請重新檢查。');
      return n;
    };
    const follow=(n,field,kind)=>{
      const edges=(graph.out.get(n.key)||[]).filter(e=>e.active&&e.relation==='position'&&e.field===field);
      if(edges.length!==1)throw Error('來源放置關係缺失或不唯一，無法定位。');
      const next=graph.nodes.get(edges[0].to),identifier=Number(next?.id);
      if(!next||!id(identifier)||next.id!==String(identifier)||next.key!==key(kind,identifier))throw Error('來源放置身分無法核對，請重新檢查。');
      return typed(kind,identifier);
    };
    const n=typed(target.kind,target.id),placement=target.kind==='placement'?n:follow(n,'surface','placement');
    if(target.kind==='placement' && !(graph.out.get(placement.key)||[]).some(e=>e.active&&e.relation==='position'&&e.field==='boundary'))
      return {placementId:Number(placement.id),boundaryId:null}; // Native surfaces must confirm the embedded rectangular case.
    const boundary=follow(placement,'boundary','boundary');
    return {placementId:Number(placement.id),boundaryId:Number(boundary.id)};
  }
  function modelRoots(record){
    const input=record?.input;if(record?.source?.kind!=='scene'||!input||typeof input.base_scene!=='string')return [];
    return [...new Set([...(input.mode==='plan'&&input.placement_id!=null?[key('placement',input.placement_id)]:input.mode==='faces'&&Array.isArray(input.uses)?input.uses.map(u=>key('placement',u.placement_id)):[]),...(input.obstacles||[]).map(o=>key(o.kind,o.id)),...(input.timbers||[]).map(t=>key(t.kind,t.id))])];
  }
  function modelTimberIds(record){
    const refs=record?.input?.timbers;if(refs===undefined)return [];
    if(!Array.isArray(refs)||refs.length>512||refs.some(r=>!r||Object.keys(r).length!==2||r.kind!=='timber'||!id(r.id))||new Set(refs.map(r=>r.id)).size!==refs.length)throw Error('保存模型的明選角材身分無效或重複。');
    return refs.map(r=>r.id);
  }
  function checkDimensionSources(row,baseline){
    if(row.assembly)return; // Owned members use the fixed binding/owner checks.
    const fields=['width','length','A','B','u.panel','v.panel','u.gap','v.gap','boundary.A','boundary.B','primary.A','primary.B','secondary.A','secondary.B'];
    const edges=baseline.out.get(key('timber',row.id))||[],seen=new Set();
    const sourceKey=source=>{
      if(!source)throw Error('快照尺寸來源缺失。');
      if(source.kind==='literal'&&Number.isSafeInteger(source.value))return null;
      if(source.kind==='parameter'&&id(source.parameterId)&&id(source.fieldId))return key('parameter-field',source.parameterId,0,source.fieldId);
      if(source.kind==='spec'&&typeof source.name==='string')return key('spec',source.name);
      if(source.kind==='material'&&typeof source.id==='string'&&id(source.version)&&source.version>0&&fields.slice(0,4).includes(source.field))return key('material',source.id,source.version);
      if(source.kind==='application'&&typeof source.id==='string'&&fields.indexOf(source.field)>=4)return key('application-field',source.id,0,fields.indexOf(source.field));
      throw Error('快照尺寸來源型別無效。');
    };
    const verify=(source,field,active)=>{const target=sourceKey(source),label=['material','application'].includes(source.kind)?field+' ← '+source.field:field,relation=source.kind==='material'?'material-version':'dimension';if(target&&(!baseline.nodes.has(target)||!edges.some(e=>e.to===target&&e.active===active&&e.relation===relation&&e.field===label)))throw Error('快照尺寸來源與原生具型別關係無法核對。');};
    for(const s of row.sources){
      const field=s.target?.field;if(s.target?.kind!=='timber'||s.target.id!==row.id||!['A','B'].includes(field)||seen.has(field)||s.effective!==row[field])throw Error('快照尺寸來源重複或與原生完成尺寸不一致。');seen.add(field);
      const overridden=s.override!==null&&s.override!==undefined&&s.override!==false;
      verify(s.source,field,!overridden);if(overridden)verify(s.override,field+' override',true);
      const effective=overridden?s.override:s.source;if(effective.kind==='literal'&&effective.value!==row[field])throw Error('快照明設尺寸來源與有效值不一致。');
    }
    for(const e of edges)if(['dimension','material-version'].includes(e.relation)&&/^[AB](?: override)?(?: ← |$)/.test(e.field)&&!seen.has(e.field[0]))throw Error('快照尺寸來源資料未完整提供。');
  }
  function deriveModelSchedule(record,result,timberSchedule,project){
    if(typeof project?.validateSpaceModel!=='function'||typeof timberSchedule?.derive!=='function')throw Error('保存快照料單能力尚未核對。');
    project.validateSpaceModel(record);const ids=modelTimberIds(record),baseline=result?.baseline;
    if(!baseline||baseline.data.live!==false||!hash(baseline.data.sourceFingerprint))throw Error('保存來源快照尚未核對。');
    if(ids.length&&(!result.packageBaseline||result.packageBaseline.data.live!==false||result.packageBaseline.data.sourceFingerprint!==baseline.data.sourceFingerprint||result.packageSourceSha!==record.result.source_sha256))throw Error('保存模型輸入與角材套件定義尚未核對或不一致。');
    const refs=baseline.data.timberReferences;
    if(refs?.ok!==true||refs.sourceFingerprint!==baseline.data.sourceFingerprint||!Array.isArray(refs.timbers))throw Error('快照料單與原生來源版本不一致。');
    if(JSON.stringify(refs.timberSupports)!==JSON.stringify(baseline.data.timberSupports))throw Error('快照支撐與同次原生來源無法核對。');
    const seen=new Set(),native=new Map();for(const t of refs.timbers){if(!t||!id(t.id)||seen.has(t.id))throw Error('快照原生角材身分無效或重複。');seen.add(t.id);native.set(t.id,t);}
    const groups=new Map();for(const timberId of ids){
      const t=native.get(timberId),n=baseline.nodes.get(key('timber',timberId)),g=t?.geometry;
      if(!n||n.kind!=='timber'||n.id!==String(timberId)||n.placed!==true||!id(g?.surface)||n.surface!==g.surface||n.lengthAxis!==(['+u','-u'].includes(g.dir)?'u':['+v','-v'].includes(g.dir)?'v':null))throw Error('明選角材不存在、未放置或與快照承載面無法核對。');
      if(g.surface!==record.input.placement_id)throw Error('明選角材不在保存模型明定的承載面。');
      if(!Array.isArray(g.axes)||g.axes.length!==3||g.axes.some(axis=>!Array.isArray(axis)||axis.length!==3||!axis.every(v=>[-1,0,1].includes(v))||axis.reduce((sum,v)=>sum+v*v,0)!==1)||g.axes.some((axis,i)=>g.axes.some((other,j)=>i!==j&&axis.reduce((sum,v,k)=>sum+v*other[k],0)!==0)))throw Error('快照角材原生軸資料無效。');
      if(!groups.has(g.surface))groups.set(g.surface,[]);groups.get(g.surface).push(timberId);
    }
    const rows=[];for(const [surface,selected] of groups){
      const schedule=timberSchedule.derive(refs,surface,selected);
      for(const row of schedule.rows){
        const n=baseline.nodes.get(key('timber',row.id)),entry=baseline.supportEntries.get(n.key),owner=row.supportOwner;
        if(!ownerValid(owner)||(n.nativeOwner===null?owner!==null:owner===null||ownerFields.some(k=>owner[k]!==n.nativeOwner?.[k]))||!entry||JSON.stringify(row.supports)!==JSON.stringify({start:entry.start,finish:entry.finish}))throw Error('快照料單的支撐與固定所有權來源無法核對。');
        checkDimensionSources(row,baseline);rows.push(row);
      }
    }
    if(rows.length!==ids.length||new Set(rows.map(r=>r.id)).size!==ids.length||rows.some(r=>!ids.includes(r.id)))throw Error('快照料單範圍超出保存模型的明選角材。');
    return {schema:'native-timber-schedule/1',scope:'saved-model-snapshot',ids:[...ids],rows,sourceFingerprint:refs.sourceFingerprint,
      supportSourceFingerprint:refs.timberSupports.sourceFingerprint,modelId:record.id,modelName:record.name,contextId:result.context?.id||'',
      identityContinuity:'unknown',freshness:freshness(baseline,result.graph,modelRoots(record)),liveSourceFingerprint:result.graph.data.sourceFingerprint};
  }
  function modelScheduleCSV(snapshot,timberSchedule,order='id',unit='mm'){
    if(snapshot?.scope!=='saved-model-snapshot'||!['mm','cm'].includes(unit)||!['id','length'].includes(order))throw Error('快照料單範圍或顯示單位無效。');
    const columns=['snapshot_kind','snapshot_model_id','snapshot_model_name','snapshot_context_id','snapshot_source_fingerprint','snapshot_units','snapshot_display_units','snapshot_source_status','snapshot_content_status','snapshot_identity_continuity','checked_live_source_fingerprint'];
    const cells=['saved-model-snapshot',snapshot.modelId,snapshot.modelName,snapshot.contextId,snapshot.sourceFingerprint,'mm',unit,snapshot.freshness.status,snapshot.freshness.contentStatus,'unknown',snapshot.liveSourceFingerprint].map(timberSchedule.csvCell).join(',');
    const header=timberSchedule.csv({...snapshot,rows:[]},order).slice(0,-2)+','+columns.map(timberSchedule.csvCell).join(',');
    const rows=timberSchedule.sorted(snapshot.rows,order).map(row=>{const csv=timberSchedule.csv({...snapshot,rows:[row]},order);return csv.slice(csv.indexOf('\r\n')+2,-2)+','+cells;});
    return [header,...rows].join('\r\n')+'\r\n';
  }
  function freshness(before,now,roots,{deleted=new Set()}={}){
    if(!roots.length)return {status:'unknown',contentStatus:'unchecked',changes:[],message:'來源缺失或無法可靠追溯。'};
    // I9 candidates are possible stops, not confirmed sources. RC membership
    // names its container; these frozen world dimensions do not depend on every face.
    const evaluationEdge=(g,e)=>e.active&&!['span-candidate','confirmed-support'].includes(e.relation)&&!(e.relation==='member'&&['column','beam'].includes(g.nodes.get(e.from)?.kind));
    const closure=new Set(),pending=[...roots];let complete=before.data.complete&&now.data.complete,missing=[];
    while(pending.length){const at=pending.pop();if(closure.has(at))continue;if(closure.size===512){complete=false;break;}closure.add(at);
      if(!before.nodes.has(at)){complete=false;continue;}for(const e of before.out.get(at)||[])if(evaluationEdge(before,e))pending.push(e.to);}
    const changes=[];
    for(const at of closure){const old=before.nodes.get(at),current=now.nodes.get(at);if(!current){missing.push(at);continue;}if(!old)continue;
      if(deleted.has(at))changes.push({key:at,kind:'identity-unknown'});
      else if(old.definitionFingerprint!==current.definitionFingerprint||old.valueFingerprint!==current.valueFingerprint)changes.push({key:at,kind:old.definitionFingerprint!==current.definitionFingerprint?(old.valueFingerprint===current.valueFingerprint?'source-definition':'source-and-value'):'value'});
      if(old.kind==='timber'&&(before.hasSupportProjection||now.hasSupportProjection)){
        const a=before.supportEntries.get(at),b=now.supportEntries.get(at),ownerTuple=o=>o===null?null:ownerFields.map(k=>o[k]),endpointTuple=v=>{const r=v.relation;return [v.at,v.crossRange,r.kind,r.source.kind,r.source.id,r.localFace,r.normalWorld,ownerTuple(r.owner),r.surface,r.edgeIndex??null,r.holeIndex??null,r.stop.axis,r.stop.at,r.stop.range,r.stop.fixity];};
        let changed=!!a&&!!b&&JSON.stringify(ownerTuple(a.owner))!==JSON.stringify(ownerTuple(b.owner));
        for(const end of ['start','finish']){if(a?.[end]?.status!=='exact'||b?.[end]?.status!=='exact')complete=false;else if(JSON.stringify(endpointTuple(a[end]))!==JSON.stringify(endpointTuple(b[end])))changed=true;}
        if(changed&&!changes.some(c=>c.key===at))changes.push({key:at,kind:'source-definition'});
      }
      const a=(before.out.get(at)||[]).filter(e=>evaluationEdge(before,e)).map(e=>JSON.stringify([e.to,e.relation,e.field])).sort(),b=(now.out.get(at)||[]).filter(e=>evaluationEdge(now,e)).map(e=>JSON.stringify([e.to,e.relation,e.field])).sort();
      if(JSON.stringify(a)!==JSON.stringify(b)&&!changes.some(c=>c.key===at))changes.push({key:at,kind:'source-definition'});
    }
    if(missing.length)return {status:'missing',contentStatus:'missing',changes:missing.map(key=>({key,kind:'missing'})),message:'相關來源缺失，快照需核對。'};
    if(changes.length)return {status:changes.some(c=>c.kind==='identity-unknown')?'unknown':'changed',contentStatus:'changed',changes,message:'相關來源已變更，需核對；模型保持原快照。'};
    // Existing project formats carry snapshots, but no durable object incarnation receipt.
    // Content equality cannot prove that a deleted ID is the same object after reopen.
    return {status:'unknown',contentStatus:complete?'consistent':'unchecked',changes:[],message:complete?'可追溯來源內容一致；物件延續性未知。':'來源資料不完整，尚未完成檢查。'};
  }
  function createSession({context,stamp,read,readSnapshot,project=null}){
    let sequence=0,controller=null;
    const current=(ctx,token,seq)=>context()===ctx&&stamp()===token&&sequence===seq;
    async function inspect(record=null){
      controller?.abort();controller=new AbortController();const signal=controller.signal,seq=++sequence,ctx=context(),token=stamp();
      const first=index(await read());if(!current(ctx,token,seq))return null;
      let baseline=null,packageBaseline=null,packageSourceSha=null;if(record){
        const saved=clone(record);if(typeof saved.input?.base_scene!=='string')throw Error('來源快照缺失，尚未完成檢查。');
        baseline=index(await readSnapshot(saved.input.base_scene,signal));if(!current(ctx,token,seq))return null;
        if(modelTimberIds(saved).length){
          if(typeof project?.validateSpaceModel!=='function'||typeof project?.sha!=='function')throw Error('保存套件核對能力尚未確認。');project.validateSpaceModel(saved);
          const scene=saved.result.timbers.definitions.base_scene;
          packageSourceSha=await project.sha(new TextEncoder().encode(scene));if(!current(ctx,token,seq))return null;
          if(packageSourceSha!==saved.result.source_sha256)throw Error('保存角材套件的來源摘要不一致。');
          packageBaseline=index(await readSnapshot(scene,signal));if(!current(ctx,token,seq))return null;
          if(baseline.data.live!==false||packageBaseline.data.live!==false||!hash(baseline.data.sourceFingerprint)||baseline.data.sourceFingerprint!==packageBaseline.data.sourceFingerprint)throw Error('保存模型輸入與角材套件定義不一致。');
        }
      }
      const last=index(await read());if(!current(ctx,token,seq))return null;
      if(first.data.revision!==last.data.revision||first.data.sourceFingerprint!==last.data.sourceFingerprint)throw Error('來源已更新，請重新檢查。');
      return {graph:last,baseline,packageBaseline,packageSourceSha,revision:last.data.revision,context:ctx,stamp:token};
    }
    return {inspect,cancel(){++sequence;controller?.abort();},valid(result){return context()===result.context&&stamp()===result.stamp;}};
  }
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function supportHTML(graph,node){
    if(node.kind!=='timber')return '<p>求值支撐身分：僅依角材原生端點資料確認。檢視不重建模型。</p>';
    const entry=graph.supportEntries.get(node.key),ownerText=o=>o?` · 組構實例 ${o.instanceId}／member ${o.memberId}／binding ${o.bindingId}／規則 ${o.ruleId} 固定 v${o.ruleVersion} · rule ${o.ruleFingerprint} · instance ${o.instanceFingerprint} · binding ${o.bindingFingerprint}`:'';
    return ['start','finish'].map((end,i)=>{const value=entry?.[end];if(value?.status!=='exact')return `<p data-source-support="${end}">${i?'末端':'起端'}支撐：未知／原生證據未提供或非唯一。</p>`;const r=value.relation,s=r.source,k=key(s.kind,s.id),label=r.kind==='timber-face'?`角材 ${s.id}／${r.localFace}`:`${s.kind==='boundary'?'邊界':'承載面'} ${s.id}／${r.kind==='hole-edge'?'h'+r.holeIndex:''}e${r.edgeIndex}`;return `<p data-source-support="${end}" data-source-support-status="exact">${i?'末端':'起端'}支撐：<button type="button" data-source-path="${esc(k)}">${esc(label)}</button>${esc(ownerText(r.owner))}</p>`;}).join('')+'<p>支撐為原生端點證據；物件延續性仍未知。檢視不重建模型。</p>';
  }
  function mount(host,{selection,context,stamp,read,readSnapshot,navigate,record=null,timberSchedule=null,project=null,getRecord=()=>record,isActive=()=>true,activate=()=>{},exportCSV=null,snapshotOnly=false,onSchedule=()=>{},onSelect=null}){
    const existing=host.querySelector(':scope > [data-source-inspector]');if(existing)existing.remove();
    const reuse=host.querySelector('#paramUsage'),detail=reuse||host.ownerDocument.createElement('details');detail.classList.add('source-inspector','inspector-block');detail.dataset.sourceInspector=selection||'model';
    if(reuse){reuse.querySelector('summary').textContent='來源／影響與參數交換';reuse.querySelector('ul')?.remove();reuse.querySelector('[data-source-body]')?.remove();const body=host.ownerDocument.createElement('div');body.dataset.sourceBody='';body.setAttribute('role','status');body.setAttribute('aria-live','polite');body.textContent='尚未檢查';reuse.append(body);}
    else {detail.innerHTML=`<summary>${snapshotOnly?'保存角材料單':'來源／影響'}</summary><div data-source-body role="status" aria-live="polite">尚未檢查</div>`;host.append(detail);}
    const body=detail.querySelector('[data-source-body]'),session=createSession({context,stamp,read,readSnapshot,project}),recordPin=record&&JSON.stringify(record);
    let result=null,schedule=null,start=selection,loadSequence=0,busy=false,active=true,order='id',unit='mm',navigationLease=null;
    let selectedTimber=null;
    const hasTimbers=record&&Array.isArray(record.input?.timbers)&&record.input.timbers.length>0;
    const refresh=()=>`<button type="button" data-source-refresh>${hasTimbers?'核對並匯出快照CSV':'重新檢查'}</button>`;
    const recordCurrent=()=>!record||JSON.stringify(getRecord())===recordPin;
    const mounted=()=>active&&detail.open&&detail.isConnected!==false&&body.isConnected&&isActive()&&recordCurrent();
    function scheduleHTML(){
      if(!schedule)return '';const table=timberSchedule.sorted(schedule.rows,order).map(row=>{const content=`<strong>快照角材 ${row.id} · 承載面 ${row.surface}</strong><span>A ${esc(timberSchedule.dimension(row.A,unit))} × B ${esc(timberSchedule.dimension(row.B,unit))} · 完成 L ${esc(timberSchedule.dimension(row.L,unit))} ${unit}</span><span>${esc(timberSchedule.sourceText(row))}</span>`;return `<li data-snapshot-timber="${row.id}" data-snapshot-surface="${row.surface}">${onSelect?`<button type="button" data-snapshot-select="${row.id}" aria-pressed="${selectedTimber===row.id}" aria-label="3D定位快照角材 ${row.id}">${content}</button>`:content}</li>`;}).join('');
      return `<section data-model-schedule><h4>保存快照料單 · ${esc(schedule.modelName)}</h4><p>單一模型 ${esc(schedule.modelId)} · ${schedule.rows.length} 支明選角材；保存快照尺寸，物件延續性未知。${esc(schedule.freshness.message)}</p><code title="保存快照原生來源指紋">${esc(schedule.sourceFingerprint)}</code><label>排列<select data-snapshot-order><option value="id"${order==='id'?' selected':''}>角材 ID</option><option value="length"${order==='length'?' selected':''}>完成料長</option></select></label><label>顯示單位<select data-snapshot-unit><option value="mm"${unit==='mm'?' selected':''}>mm</option><option value="cm"${unit==='cm'?' selected':''}>cm</option></select></label><ol>${table||'<li>此模型沒有明選角材；未納入來源場景的其他角材。</li>'}</ol><p>CSV 尺寸保持整數 mm；材料與加工未設定。${onSelect?'點料單列定位此保存模型的構件（隱藏材料牆）；點 3D 角材回選同列。':'快照列不定位同 ID 的目前角材。'}</p></section>`;
    }
    function render(){
      if(snapshotOnly){body.innerHTML=`${scheduleHTML()}${refresh()}`;return;}
      if(!result)return;const g=result.graph,n=g.nodes.get(start);
      const state=record?freshness(result.baseline,g,modelRoots(record)):null;
      if(!n){body.innerHTML=`${scheduleHTML()}<p${state?` data-source-freshness="${state.status}"`:''}>${esc(state?.message||'來源缺失或目前型別尚未提供，無法可靠追溯。')}</p>${refresh()}`;return;}
      const sources=nearby(g,start),uses=nearby(g,start,{direction:'uses'});
      const rows=(entries,title)=>`<h4>${title}</h4><ol>${entries.rows.map((r,i)=>`<li><span>${esc(labels[r.edge.relation])} · ${esc(r.edge.field)}</span><button type="button" data-source-path="${esc(r.key)}">${esc(r.node?.label||'來源缺失')} · ${esc(r.key)}</button>${r.node?`<button type="button" data-source-locate="${esc(r.key)}" aria-label="定位 ${esc(r.node.label)}">定位</button>`:''}</li>`).join('')||'<li>目前沒有已知關係</li>'}</ol>${entries.truncated?'<p>已達容量／深度上限；關係清單不完整。</p>':''}`;
      body.innerHTML=`${scheduleHTML()}${state?`<p data-source-freshness="${state.status}">${esc(state.message)}</p>${state.changes.map(c=>`<p>${esc(c.key)} · ${esc(c.kind)}</p>`).join('')}<h4>已核對的目前來源 · 與保存快照尺寸分開</h4>`:''}<p>${esc(n.label)} · ${esc(n.key)}${n.version?' · 固定 v'+n.version:''}</p><code title="原生來源指紋">${esc(n.definitionFingerprint)}</code>${rows(sources,'直接與間接來源')}${rows(uses,'修改可能涉及（未試算）')}${supportHTML(g,n)}${refresh()}`;
    }
    const unavailable=message=>{result=null;schedule=null;selectedTimber=null;onSchedule(null);body.innerHTML=`<p>${esc(message)}</p>${refresh()}`;};
    async function load(exportRequested=false){
      if(busy)return;activate();if(!mounted())return;busy=true;selectedTimber=null;onSchedule(null);const seq=++loadSequence,ctx=context(),token=stamp();body.textContent='正在唯讀檢查…';
      try{
        const loaded=await session.inspect(record);if(seq!==loadSequence||context()!==ctx||!mounted())return;
        if(!loaded||stamp()!==token){unavailable('來源已變更，請重新檢查。');return;}
        const candidate=hasTimbers?deriveModelSchedule(record,loaded,timberSchedule,project):null;
        if(exportRequested&&candidate){
          // Re-read after derivation as well. A delayed earlier reply must not
          // authorize a download after native sources or the model have moved.
          const final=index(await read());if(seq!==loadSequence||!mounted()||!session.valid(loaded))return;
          if(final.data.revision!==loaded.revision||final.data.sourceFingerprint!==loaded.graph.data.sourceFingerprint)throw Error('來源已更新，快照CSV未匯出，請重新核對。');
          if(typeof exportCSV!=='function')throw Error('快照CSV匯出能力尚未核對。');
        }
        if(seq!==loadSequence||!mounted()||!session.valid(loaded))return;
        result=loaded;schedule=candidate;if(record)start=modelRoots(record)[0];render();
        if(candidate)onSchedule(candidate,{isCurrent:()=>seq===loadSequence&&mounted()&&session.valid(loaded)});
        if(exportRequested&&candidate&&mounted()&&session.valid(loaded))exportCSV(modelScheduleCSV(candidate,timberSchedule,order,unit),candidate);
      }catch(e){if(seq===loadSequence&&context()===ctx&&mounted())unavailable(e.name==='AbortError'?'檢查已取消。':e.message);}
      finally{if(seq===loadSequence)busy=false;}
    }
    const onToggle=()=>{if(detail.open)load();else{onSchedule(null);selectedTimber=null;if(navigationLease)navigationLease.cancelled=true;++loadSequence;busy=false;session.cancel();result=null;schedule=null;body.textContent='尚未檢查';}};
    detail.addEventListener('toggle',onToggle);
    const onClick=async e=>{
      if(e.target.closest('[data-source-refresh]')){await load(!!hasTimbers);return;}
      const row=e.target.closest('[data-snapshot-select]');if(row&&onSelect){
        if(!schedule||!result||!mounted()||!session.valid(result)){unavailable('來源已變更，請重新核對。');return;}
        const id=Number(row.dataset.snapshotSelect);if(!schedule.ids.includes(id))return;
        if(onSelect(id)!==false){selectSnapshot(id,false);body.querySelector(`[data-snapshot-select="${id}"]`)?.focus({preventScroll:true});}return;
      }
      const path=e.target.closest('[data-source-path]');if(path&&result){if(!mounted()||!session.valid(result)){unavailable('來源已變更，請重新檢查。');return;}start=path.dataset.sourcePath;render();return;}
      const button=e.target.closest('[data-source-locate]');if(!button||!result)return;
      const captured=result,key=button.dataset.sourceLocate;button.disabled=true;
      if(navigationLease)navigationLease.cancelled=true;
      const seq=loadSequence,lease=navigationLease={cancelled:false,transferred:false};
      const isCurrent=()=>!lease.cancelled&&session.valid(captured)&&recordCurrent()&&isActive()&&
        (lease.transferred&&!record || seq===loadSequence&&mounted());
      const beginNavigation=()=>{if(!isCurrent())return false;lease.transferred=true;return true;};
      try{const fresh=index(await read());if(!isCurrent())return;if(fresh.data.revision!==captured.revision||fresh.data.sourceFingerprint!==captured.graph.data.sourceFingerprint||!fresh.nodes.has(key)){body.textContent='來源已變更或刪除，請重新檢查。';return;}await navigate(fresh.nodes.get(key),fresh,{isCurrent,beginNavigation});}catch(error){if(mounted())body.textContent=error.message;}finally{if(navigationLease===lease)navigationLease=null;if(button.isConnected)button.disabled=false;}
    };
    const onChange=e=>{if(!schedule||!result||!mounted()||!session.valid(result)){if(result)unavailable('來源已變更，請重新核對。');return;}if(e.target.matches('[data-snapshot-order]')&&['id','length'].includes(e.target.value))order=e.target.value;else if(e.target.matches('[data-snapshot-unit]')&&['mm','cm'].includes(e.target.value))unit=e.target.value;else return;render();};
    function selectSnapshot(id,scroll=true){
      if(!schedule||!result||!mounted()||!session.valid(result)||id!==null&&!schedule.ids.includes(id))return false;
      selectedTimber=id;render();if(scroll&&id!==null)body.querySelector(`[data-snapshot-select="${id}"]`)?.scrollIntoView({block:'nearest'});return true;
    }
    body.addEventListener('click',onClick);body.addEventListener('change',onChange);if(snapshotOnly)detail.open=true;else if(detail.open)load();return {detail,selectSnapshot,cancel(){onSchedule(null);if(navigationLease&&(record||!navigationLease.transferred))navigationLease.cancelled=true;active=false;++loadSequence;session.cancel();detail.removeEventListener('toggle',onToggle);body.removeEventListener('click',onClick);body.removeEventListener('change',onChange);}};
  }
  return {key,index,nearby,resolveLocation,modelRoots,modelTimberIds,deriveModelSchedule,modelScheduleCSV,freshness,createSession,mount,LIMIT,DEPTH};
});
