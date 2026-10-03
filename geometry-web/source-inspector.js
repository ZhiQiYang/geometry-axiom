/* F1a presentation/index adapter. Native fingerprints are opaque: no DSL/path guessing. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.SourceInspector=api;})(globalThis,()=>{
  'use strict';
  const LIMIT=48,DEPTH=6,HASH=/^[a-f0-9]{64}$/;
  const labels={dimension:'尺寸來源',position:'定位來源','rule-version':'固定規則版本','material-version':'固定材料版本',member:'成員對應','joint-definition':'接合規則定義（未生成也可存在）','span-candidate':'跨距求值候選（支撐未知）'};
  const key=(kind,id,version=0,fieldId=0)=>`${kind}:${id}${version?':v'+version:''}${fieldId||kind==='parameter-field'?':f'+fieldId:''}`;
  function index(data){
    if(data?.ok!==true||data.schema!=='source-inspector/1'||!Array.isArray(data.nodes)||!Array.isArray(data.edges)||data.nodes.length>2048||data.edges.length>8192||!Number.isSafeInteger(data.revision))throw Error('執行能力不足或來源尚未檢查。');
    const nodes=new Map(),out=new Map(),into=new Map();
    for(const n of data.nodes){if(typeof n.key!=='string'||nodes.has(n.key)||!HASH.test(n.definitionFingerprint)||!HASH.test(n.valueFingerprint))throw Error('來源資料不完整，無法可靠追溯。');nodes.set(n.key,n);}
    for(const e of data.edges){if(typeof e.from!=='string'||typeof e.to!=='string'||!labels[e.relation]||typeof e.active!=='boolean')throw Error('來源型別未知。');if(!out.has(e.from))out.set(e.from,[]);out.get(e.from).push(e);if(!into.has(e.to))into.set(e.to,[]);into.get(e.to).push(e);}
    return {data,nodes,out,into};
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
    const evaluationEdge=(g,e)=>e.active&&e.relation!=='span-candidate'&&!(e.relation==='member'&&['column','beam'].includes(g.nodes.get(e.from)?.kind));
    const closure=new Set(),pending=[...roots];let complete=before.data.complete&&now.data.complete,missing=[];
    while(pending.length){const at=pending.pop();if(closure.has(at))continue;if(closure.size===512){complete=false;break;}closure.add(at);
      if(!before.nodes.has(at)){complete=false;continue;}for(const e of before.out.get(at)||[])if(evaluationEdge(before,e))pending.push(e.to);}
    const changes=[];
    for(const at of closure){const old=before.nodes.get(at),current=now.nodes.get(at);if(!current){missing.push(at);continue;}if(!old)continue;
      if(deleted.has(at))changes.push({key:at,kind:'identity-unknown'});
      else if(old.definitionFingerprint!==current.definitionFingerprint||old.valueFingerprint!==current.valueFingerprint)changes.push({key:at,kind:old.definitionFingerprint!==current.definitionFingerprint?(old.valueFingerprint===current.valueFingerprint?'source-definition':'source-and-value'):'value'});
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
      if(first.data.revision!==last.data.revision)throw Error('來源已更新，請重新檢查。');
      return {graph:last,baseline,revision:last.data.revision,context:ctx,stamp:token};
    }
    return {inspect,cancel(){++sequence;controller?.abort();},valid(result){return context()===result.context&&stamp()===result.stamp;}};
  }
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
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
      body.innerHTML=`${state?`<p data-source-freshness="${state.status}">${esc(state.message)}</p>${state.changes.map(c=>`<p>${esc(c.key)} · ${esc(c.kind)}</p>`).join('')}`:''}<p>${esc(n.label)} · ${esc(n.key)}${n.version?' · 固定 v'+n.version:''}</p><code title="原生來源指紋">${esc(n.definitionFingerprint)}</code>${rows(sources,'直接與間接來源')}${rows(uses,'修改可能涉及（未試算）')}<p>求值支撐身分：未知。檢視不重建模型。</p><button type="button" data-source-refresh>重新檢查</button>`;
    }
    const unavailable=message=>{result=null;body.innerHTML=`<p>${esc(message)}</p><button type="button" data-source-refresh>重新檢查</button>`;};
    async function load(){const seq=++loadSequence,ctx=context(),token=stamp();body.textContent='正在唯讀檢查…';try{const loaded=await session.inspect(record);if(seq!==loadSequence||context()!==ctx||!detail.open||!body.isConnected)return;if(!loaded||stamp()!==token){unavailable('來源已變更，請重新檢查。');return;}result=loaded;if(record)start=modelRoots(record)[0];render();}catch(e){if(seq===loadSequence&&context()===ctx&&detail.open&&body.isConnected)unavailable(e.name==='AbortError'?'檢查已取消。':e.message);}}
    const onToggle=()=>{if(detail.open)load();else{session.cancel();result=null;body.textContent='尚未檢查';}};
    detail.addEventListener('toggle',onToggle);
    const onClick=async e=>{
      if(e.target.closest('[data-source-refresh]')){load();return;}
      const path=e.target.closest('[data-source-path]');if(path&&result){start=path.dataset.sourcePath;render();return;}
      const button=e.target.closest('[data-source-locate]');if(!button||!result)return;
      const captured=result,key=button.dataset.sourceLocate;button.disabled=true;
      try{const fresh=index(await read());if(!session.valid(captured)||!detail.open||!detail.isConnected)return;if(fresh.data.revision!==captured.revision||!fresh.nodes.has(key)){body.textContent='來源已變更或刪除，請重新檢查。';return;}await navigate(fresh.nodes.get(key),fresh);}catch(error){if(detail.isConnected)body.textContent=error.message;}finally{if(button.isConnected)button.disabled=false;}
    };body.addEventListener('click',onClick);if(detail.open)load();return {detail,cancel(){++loadSequence;session.cancel();detail.removeEventListener('toggle',onToggle);body.removeEventListener('click',onClick);}};
  }
  return {key,index,nearby,modelRoots,freshness,createSession,mount,LIMIT,DEPTH};
});
