/* F1a presentation/index adapter. Native fingerprints are opaque: no DSL/path guessing. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.SourceInspector=api;})(globalThis,()=>{
  'use strict';
  const LIMIT=48,DEPTH=6,HASH=/^[a-f0-9]{64}$/;
  const labels={dimension:'尺寸來源',position:'定位來源','rule-version':'固定規則版本','material-version':'固定材料版本',member:'成員對應','joint-definition':'接合規則定義（未生成也可存在）','span-candidate':'跨距求值候選（支撐未知）','confirmed-support':'原生已確認支撐'};
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
  function modelRoots(record){
    const input=record?.input;if(record?.source?.kind!=='scene'||!input||typeof input.base_scene!=='string')return [];
    return [...new Set([...(input.mode==='plan'&&input.placement_id!=null?[key('placement',input.placement_id)]:input.mode==='faces'&&Array.isArray(input.uses)?input.uses.map(u=>key('placement',u.placement_id)):[]),...(input.obstacles||[]).map(o=>key(o.kind,o.id)),...(input.timbers||[]).map(t=>key(t.kind,t.id))])];
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
  function createSession({context,stamp,read,readSnapshot}){
    let sequence=0,controller=null;
    const current=(ctx,token,seq)=>context()===ctx&&stamp()===token&&sequence===seq;
    async function inspect(record=null){
      controller?.abort();controller=new AbortController();const signal=controller.signal,seq=++sequence,ctx=context(),token=stamp();
      const first=index(await read());if(!current(ctx,token,seq))return null;
      let baseline=null;if(record){if(typeof record.input?.base_scene!=='string')throw Error('來源快照缺失，尚未完成檢查。');baseline=index(await readSnapshot(record.input.base_scene,signal));if(!current(ctx,token,seq))return null;}
      const last=index(await read());if(!current(ctx,token,seq))return null;
      if(first.data.revision!==last.data.revision||first.data.sourceFingerprint!==last.data.sourceFingerprint)throw Error('來源已更新，請重新檢查。');
      return {graph:last,baseline,revision:last.data.revision,context:ctx,stamp:token};
    }
    return {inspect,cancel(){++sequence;controller?.abort();},valid(result){return context()===result.context&&stamp()===result.stamp;}};
  }
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function supportHTML(graph,node){
    if(node.kind!=='timber')return '<p>求值支撐身分：僅依角材原生端點資料確認。檢視不重建模型。</p>';
    const entry=graph.supportEntries.get(node.key),ownerText=o=>o?` · 組構實例 ${o.instanceId}／member ${o.memberId}／binding ${o.bindingId}／規則 ${o.ruleId} 固定 v${o.ruleVersion} · rule ${o.ruleFingerprint} · instance ${o.instanceFingerprint} · binding ${o.bindingFingerprint}`:'';
    return ['start','finish'].map((end,i)=>{const value=entry?.[end];if(value?.status!=='exact')return `<p data-source-support="${end}">${i?'末端':'起端'}支撐：未知／原生證據未提供或非唯一。</p>`;const r=value.relation,s=r.source,k=key(s.kind,s.id),label=r.kind==='timber-face'?`角材 ${s.id}／${r.localFace}`:`${s.kind==='boundary'?'邊界':'承載面'} ${s.id}／${r.kind==='hole-edge'?'h'+r.holeIndex:''}e${r.edgeIndex}`;return `<p data-source-support="${end}" data-source-support-status="exact">${i?'末端':'起端'}支撐：<button type="button" data-source-path="${esc(k)}">${esc(label)}</button>${esc(ownerText(r.owner))}</p>`;}).join('')+'<p>支撐為原生端點證據；物件延續性仍未知。檢視不重建模型。</p>';
  }
  function mount(host,{selection,context,stamp,read,readSnapshot,navigate,record=null}){
    const existing=host.querySelector(':scope > [data-source-inspector]');if(existing)existing.remove();
    const reuse=host.querySelector('#paramUsage'),detail=reuse||host.ownerDocument.createElement('details');detail.classList.add('source-inspector','inspector-block');detail.dataset.sourceInspector=selection||'model';
    if(reuse){reuse.querySelector('summary').textContent='來源／影響與參數交換';reuse.querySelector('ul')?.remove();reuse.querySelector('[data-source-body]')?.remove();const body=host.ownerDocument.createElement('div');body.dataset.sourceBody='';body.setAttribute('role','status');body.setAttribute('aria-live','polite');body.textContent='尚未檢查';reuse.append(body);}
    else {detail.innerHTML='<summary>來源／影響</summary><div data-source-body role="status" aria-live="polite">尚未檢查</div>';host.append(detail);}
    const body=detail.querySelector('[data-source-body]'),session=createSession({context,stamp,read,readSnapshot});let result=null,start=selection,loadSequence=0;
    function render(){
      if(!result)return;const g=result.graph,n=g.nodes.get(start);
      const state=record?freshness(result.baseline,g,modelRoots(record)):null;
      if(!n){body.innerHTML=`<p${state?` data-source-freshness="${state.status}"`:''}>${esc(state?.message||'來源缺失或目前型別尚未提供，無法可靠追溯。')}</p><button type="button" data-source-refresh>重新檢查</button>`;return;}
      const sources=nearby(g,start),uses=nearby(g,start,{direction:'uses'});
      const rows=(entries,title)=>`<h4>${title}</h4><ol>${entries.rows.map((r,i)=>`<li><span>${esc(labels[r.edge.relation])} · ${esc(r.edge.field)}</span><button type="button" data-source-path="${esc(r.key)}">${esc(r.node?.label||'來源缺失')} · ${esc(r.key)}</button>${r.node?`<button type="button" data-source-locate="${esc(r.key)}" aria-label="定位 ${esc(r.node.label)}">定位</button>`:''}</li>`).join('')||'<li>目前沒有已知關係</li>'}</ol>${entries.truncated?'<p>已達容量／深度上限；關係清單不完整。</p>':''}`;
      body.innerHTML=`${state?`<p data-source-freshness="${state.status}">${esc(state.message)}</p>${state.changes.map(c=>`<p>${esc(c.key)} · ${esc(c.kind)}</p>`).join('')}`:''}<p>${esc(n.label)} · ${esc(n.key)}${n.version?' · 固定 v'+n.version:''}</p><code title="原生來源指紋">${esc(n.definitionFingerprint)}</code>${rows(sources,'直接與間接來源')}${rows(uses,'修改可能涉及（未試算）')}${supportHTML(g,n)}<button type="button" data-source-refresh>重新檢查</button>`;
    }
    const unavailable=message=>{result=null;body.innerHTML=`<p>${esc(message)}</p><button type="button" data-source-refresh>重新檢查</button>`;};
    async function load(){const seq=++loadSequence,ctx=context(),token=stamp();body.textContent='正在唯讀檢查…';try{const loaded=await session.inspect(record);if(seq!==loadSequence||context()!==ctx||!detail.open||!body.isConnected)return;if(!loaded||stamp()!==token){unavailable('來源已變更，請重新檢查。');return;}result=loaded;if(record)start=modelRoots(record)[0];render();}catch(e){if(seq===loadSequence&&context()===ctx&&detail.open&&body.isConnected)unavailable(e.name==='AbortError'?'檢查已取消。':e.message);}}
    const onToggle=()=>{if(detail.open)load();else{session.cancel();result=null;body.textContent='尚未檢查';}};
    detail.addEventListener('toggle',onToggle);
    const onClick=async e=>{
      if(e.target.closest('[data-source-refresh]')){load();return;}
      const path=e.target.closest('[data-source-path]');if(path&&result){if(!session.valid(result)){unavailable('來源已變更，請重新檢查。');return;}start=path.dataset.sourcePath;render();return;}
      const button=e.target.closest('[data-source-locate]');if(!button||!result)return;
      const captured=result,key=button.dataset.sourceLocate;button.disabled=true;
      try{const fresh=index(await read());if(!session.valid(captured)||!detail.open||!detail.isConnected)return;if(fresh.data.revision!==captured.revision||fresh.data.sourceFingerprint!==captured.graph.data.sourceFingerprint||!fresh.nodes.has(key)){body.textContent='來源已變更或刪除，請重新檢查。';return;}await navigate(fresh.nodes.get(key),fresh);}catch(error){if(detail.isConnected)body.textContent=error.message;}finally{if(button.isConnected)button.disabled=false;}
    };body.addEventListener('click',onClick);if(detail.open)load();return {detail,cancel(){++loadSequence;session.cancel();detail.removeEventListener('toggle',onToggle);body.removeEventListener('click',onClick);}};
  }
  return {key,index,nearby,modelRoots,freshness,createSession,mount,LIMIT,DEPTH};
});
