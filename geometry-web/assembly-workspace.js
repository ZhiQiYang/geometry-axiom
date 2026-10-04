/* Drafts are project data. Only the native candidate publishes definitions. */
window.AssemblyWorkspace=(()=>{
  'use strict';
  const esc=ReferenceWorkspace.escape,clone=structuredClone,$=id=>document.getElementById(id);
  const dialog=document.createElement('dialog');dialog.id='assemblyWorkspace';dialog.setAttribute('aria-label','組構規則');document.body.append(dialog);
  let s=null,ownDraft=false,serial=0,entryBusy=false;
  const token=()=>ReferenceWorkspace.getProjectState().contextToken;
  const current=x=>!!x&&s===x&&x.context===token();
  const checked=r=>{if(!r?.ok)throw Object.assign(Error(r?.error||'組構操作失敗。'),{transport:!!r?.transport});return r;};
  const command=async c=>checked(await apiRequest(c));
  const MAX_ID=0xffffffff;
  const positiveId=v=>Number.isInteger(v)&&v>0&&v<=MAX_ID;
  const validRuleRef=r=>!!r&&positiveId(r.id)&&positiveId(r.version)&&typeof r.fingerprint==='string'&&/^[a-f0-9]{64}$/.test(r.fingerprint);
  function ruleReference(record){const ref={id:record?.value?.id,version:record?.value?.version,fingerprint:record?.fingerprint};if(!validRuleRef(ref))throw Error('固定規則來源不合法；請更新服務或重新開啟規則。');return ref;}
  // A failed fresh read must not repin the still-displayed record, even when
  // its original fingerprint was missing. Reopening supplies a new record.
  const displayedBindingRules=new WeakMap();
  function captureBindingRule(source){
    if(!displayedBindingRules.has(source)){const r=s.read?.state?.rules?.find(r=>r.value.id===source.value.rule.id&&r.value.version===source.value.rule.version);displayedBindingRules.set(source,{id:r?.value?.id,version:r?.value?.version,fingerprint:r?.fingerprint});}
    return displayedBindingRules.get(source);
  }
  function freeId(start,used){
    if(!Number.isInteger(start)||start<1||start>MAX_ID)throw Error('配號超出有效範圍，請重新開啟工作區。');
    let id=start;
    for(let i=0;i<=used.size;i++){if(!used.has(id))return id;id=id===MAX_ID?1:id+1;}
    throw Error('找不到可用的組構身分。');
  }
  const next=xs=>{const max=Math.max(0,...xs.map(x=>x.id));return freeId(max===MAX_ID?1:max+1,new Set(xs.map(x=>x.id)));};
  const identityValue=v=>JSON.stringify(v,(_,value)=>value&&typeof value==='object'&&!Array.isArray(value)?Object.fromEntries(Object.keys(value).sort().map(key=>[key,value[key]])):value);
  const btn=(id,text,off=false,cls='')=>`<button type="button" id="${id}"${cls?` class="${cls}"`:''}${off?' disabled':''}>${text}</button>`;
  const sideWord={'+u':'右側','-u':'左側','+v':'下側','-v':'上側'},endWord={start:'起點',finish:'終點'};
  const plainName=(rule,id)=>rule.slots.find(v=>v.id===rule.members.find(m=>m.id===id)?.slotId)?.name?.trim()||'未命名槽位';
  const spoken=(rule,id)=>{const name=plainName(rule,id),ids=rule.members.filter(m=>plainName(rule,m.id)===name).map(m=>m.id).sort((a,b)=>a-b);return ids.length<2?name:ids.length===2?(ids[0]===id?name:'另一根'+name):`第 ${ids.indexOf(id)+1} 根${name}`;};
  function syncFooter(){const foot=$('asmFooter'),preview=$('asmPreview'),confirm=$('asmConfirm'),cancel=$('asmCancel');if(!foot||!preview||!confirm||!cancel)return;const pending=!!s?.preview,can=!!(s?.draft||s?.operations)&&!pending;preview.hidden=!can;confirm.hidden=!pending;cancel.hidden=!pending;foot.hidden=!pending&&!can;}
  const select=(id,items,value)=>`<select id="${id}">${items.map(([v,t])=>`<option value="${esc(String(v))}"${String(v)===String(value)?' selected':''}>${esc(t)}</option>`).join('')}</select>`;
  const input=(id,v,type='text')=>`<input id="${id}" type="${type}" value="${esc(String(v??''))}"${type==='number'?' min="1" step="1"':''}>`;
  const field=(t,control)=>`<label>${esc(t)}${control}</label>`;
  function report(t,error=false){if(dialog.open&&$('asmStatus')){$('asmStatus').textContent=t;$('asmStatus').classList.toggle('asm-error',error);}else if(error)toast(t);}
  const confirming=()=>!!s?.confirming;
  const pendingMessage='正在確認套用；編輯、切換與關閉暫停，請等候結果。';
  const safe=fn=>async e=>{try{if(confirming()&&!(s.confirming.uncertain&&e?.currentTarget?.id==='asmClose')){report(pendingMessage);return;}await fn(e);}catch(error){report(error.message,true);}};
  function lockConfirm(){if(!confirming())return;const controls=s.confirming.controls||=new Map();for(const n of dialog.querySelectorAll('button,input,select')){if(!controls.has(n))controls.set(n,n.disabled);n.disabled=true;}for(const n of dialog.querySelectorAll('[data-face]')){n.setAttribute('aria-disabled','true');n.setAttribute('tabindex','-1');}dialog.setAttribute('aria-busy','true');report(pendingMessage);}
  function unlockConfirm(x){for(const [n,disabled] of x.confirming?.controls||[])n.disabled=disabled;x.confirming=null;}
  function bind(id,event,fn){$(id)?.addEventListener(event,safe(fn));}
  function invalidate(){if(s?.preview)command('assembly-cancel '+s.preview.token).catch(()=>{});if(s){s.preview=null;s.generation++;}if($('asmConfirm'))$('asmConfirm').disabled=true;if($('asmPreviewResult'))$('asmPreviewResult').textContent='';syncFooter();}
  function flush(){if(!s?.draft||!current(s))return;const old=ReferenceWorkspace.getAssemblyDrafts().find(d=>d.id===s.draft.id);if(old&&JSON.stringify(old.data)===JSON.stringify(s.draft.data)&&identityValue(old.base_ref)===identityValue(s.draft.base_ref))return;s.draft.updated_at=new Date().toISOString();ownDraft=true;try{ReferenceWorkspace.setAssemblyDraft(s.draft,s.context);}finally{ownDraft=false;}s.draftsRef=ReferenceWorkspace.context().assemblyDrafts;}
  function changed(redraw=false){invalidate();flush();if(redraw)render();else diagram();report('草稿已保留；保存專案可寫入檔案。');}
  async function readState(x,isCurrent=()=>current(x)){const a=await command('assembly-read'),e=await command('engineering-read'),r=await command('references'),b=await command('assembly-read');if(!isCurrent())throw Error('專案或工作區已切換。');if(a.revision!==b.revision||e.revision!==b.revision)throw Error('來源已變更，請重新開啟。');x.read=b;x.references=r;x.engineering={...e.state,specs:r.specs||[]};}
  async function open(kind=null,id=null){if(confirming()){report(pendingMessage);return;}flush();ReferenceWorkspace.assertEditable();if(window.DraftGate&&!window.DraftGate.ask())return;invalidate();const x={context:token(),generation:0,kind,id,rotation:0,zoom:1,draftsRef:ReferenceWorkspace.context().assemblyDrafts};s=x;await readState(x);if(!current(x))return;if(kind==='assembly-rule')x.record=x.read.state.rules.filter(r=>r.value.id===id).sort((a,b)=>b.value.version-a.value.version)[0];if(kind==='assembly-binding')x.record=x.read.state.bindings.find(r=>r.value.id===id);render();if(!dialog.open)dialog.showModal();WorkspaceShell.attach(dialog);}
  function close(){if(confirming()&&!s.confirming.uncertain){report(pendingMessage);return;}flush();invalidate();s=null;++serial;dialog.close();WorkspaceShell.detach(dialog);}
  async function newDraft(kind,source=null,revision=false){
    if(confirming())return;if(kind!=='binding')flush();const x=s,g=x.generation;
    const draft=await prepareDraft(x,kind,source,revision,()=>current(x)&&!x.confirming&&g===x.generation);
    if(!draft)return;if(kind==='binding')flush();
    invalidate();x.draft=draft;x.record=null;x.operations=null;flush();render();
  }
  async function prepareDraft(x,kind,source,revision,isCurrent,resolveSource=null){
    const creatingBinding=kind==='binding'&&!source?.value?.rule,editingBinding=kind==='binding'&&!!source?.value?.rule;
    const capturedRule=editingBinding?captureBindingRule(source):null;if(editingBinding&&!validRuleRef(capturedRule))throw Error('固定規則來源不合法；請更新服務或重新開啟規則。');
    await readState(x,isCurrent);if(!isCurrent())return;
    if(resolveSource)source=resolveSource(x.read);
    let selectedRule;
    if(creatingBinding){selectedRule=source||x.read.state.rules.at(-1);if(!selectedRule)throw Error('請先發布一份規則。');const ref=ruleReference(selectedRule),fresh=x.read.state.rules.find(r=>r.value.id===ref.id&&r.value.version===ref.version);if(!fresh||fresh.fingerprint!==ref.fingerprint)throw Error('原始規則版本已變更或移除；請重新開啟規則。');selectedRule=fresh;}
    else if(editingBinding){selectedRule=x.read.state.rules.find(r=>r.value.id===capturedRule.id&&r.value.version===capturedRule.version);if(!selectedRule||selectedRule.fingerprint!==capturedRule.fingerprint)throw Error('原始配置的固定規則版本已變更或移除；請重新開啟配置。');const original=x.read.state.bindings.find(r=>r.value.id===source.value.id);if(!original||identityValue(original.value)!==identityValue(source.value))throw Error('原始配置已變更，請重新開啟。');}
    const ids=await command('newid');if(!isCurrent())return;
    const drafts=ReferenceWorkspace.getAssemblyDrafts().filter(d=>d.kind===kind),records=kind==='rule'?x.read.state.rules:x.read.state.bindings;
    const used=new Set([...records.map(r=>r.value.id),...drafts.map(d=>d.data.id)]);
    const id=freeId(kind==='rule'?ids.assemblyRule:ids.assemblyBinding,used);
    let data,base=null,bindingIntent=null;
    if(kind==='rule'){
      data=source?clone(source.value):{name:'',slots:[],members:[],joints:[]};data.id=revision?source.value.id:id;data.version=1;
      if(revision){
        const original=records.find(r=>r.value.id===source.value.id&&r.value.version===source.value.version);
        if(!original||original.fingerprint!==source.fingerprint)throw Error('原始規則版本已變更，請重新開啟。');
        const version=Math.max(...records.filter(r=>r.value.id===data.id).map(r=>r.value.version),...drafts.filter(d=>d.data.id===data.id).map(d=>d.data.version));
        if(version>=MAX_ID)throw Error('規則版本已達上限，請複製成新規則。');
        data.version=version+1;base={id:source.value.id,version:source.value.version,fingerprint:source.fingerprint};
      }
    }
    else if(editingBinding){
      data=clone(source.value);base=ruleReference(selectedRule);bindingIntent={mode:'update',source:clone(source.value)};
    }
    else {const r=selectedRule.value;base=ruleReference(selectedRule);data={id,name:'',rule:{id:r.id,version:r.version},slots:r.slots.map(slot=>({slotId:slot.id,A:null,B:null,contactFace:null,orientation:null}))};}
    return {id:crypto.randomUUID(),kind,base_ref:base,data,updated_at:new Date().toISOString(),...(kind==='binding'?{binding_intent:bindingIntent||{mode:'create'}}:{})};
  }
  async function createBindingFromRule(selection,isSelected){
    if(entryBusy||confirming())return false;
    ReferenceWorkspace.assertEditable();
    const pinned=clone(selection),old=s,g=old?.generation,context=token(),entrySerial=serial;
    const isCurrent=()=>context===token()&&s===old&&g===old?.generation&&entrySerial===serial&&!confirming()&&isSelected();
    if(!isCurrent())return false;
    const x={context,generation:0,kind:'assembly-rule',id:pinned.id,rotation:0,zoom:1,draftsRef:ReferenceWorkspace.context().assemblyDrafts};
    entryBusy=true;
    try{
      // Stage reads/allocation without replacing, flushing or cancelling the
      // old owner. A stale entry cannot consume its pending preview or inputs.
      const draft=await prepareDraft(x,'binding',null,false,isCurrent,read=>{
        const resolved=window.ContextOperations.resolveBindingCreate(pinned,read);
        if(!resolved.ok)throw Error(resolved.message);return resolved.record;
      });
      if(!draft||!isCurrent())return false;
      ReferenceWorkspace.assertEditable();
      if(window.DraftGate&&!window.DraftGate.ask())return false;
      if(!isCurrent())return false;
      flush();invalidate();s=x;x.draft=draft;flush();render();
      if(!dialog.open)dialog.showModal();WorkspaceShell.attach(dialog);return true;
    }catch(error){if(!isCurrent())return false;throw error;}finally{entryBusy=false;}
  }
  function render(){
    if(!s||!current(s))return;s.draftsRef=ReferenceWorkspace.context().assemblyDrafts;const x=s,header=dialog.querySelector(':scope > .workspace-project-header');header?.remove();
    dialog.innerHTML=`<header class="asm-header"><h2>組構規則</h2>${btn('asmClose','返回畫布')}</header><p id="asmWorkspaceLesson" class="studio-first-lesson" hidden></p><div class="asm-layout"><nav aria-label="組構來源"><h3>草稿</h3>${ReferenceWorkspace.getAssemblyDrafts().map(d=>`<button type="button" data-asm-draft="${esc(d.id)}">${esc(d.data.name||'未命名草稿')} · ${d.kind==='rule'?'規則':d.kind==='instance'?'角材實例':'配置'}</button>`).join('')}${btn('asmNewRule','新增規則')}<h3>已發布規則</h3>${s.read.state.rules.map(r=>`<button type="button" data-asm-rule="${r.value.id}:${r.value.version}">${esc(r.value.name)} · 第 ${r.value.version} 版</button>`).join('')}<h3>材料配置</h3>${s.read.state.bindings.map(r=>`<button type="button" data-asm-binding="${r.value.id}">${esc(r.value.name)} · ${r.complete?'完整':'未完成'}</button>`).join('')}</nav><main class="asm-body"><div id="asmEditor"></div><p id="asmStatus" role="status" aria-live="polite"></p></main></div><div id="asmPreviewResult"></div><footer id="asmFooter">${btn('asmPreview','預覽變更',!s.draft&&!s.operations)}${btn('asmConfirm','確認套用',true,'primary-button')}${btn('asmCancel','取消預覽')}</footer>`;
    if(header)dialog.prepend(header);bind('asmClose','click',close);bind('asmNewRule','click',()=>newDraft('rule'));
    for(const b of dialog.querySelectorAll('[data-asm-draft]'))b.onclick=safe(()=>{flush();invalidate();s.draft=ReferenceWorkspace.getAssemblyDrafts().find(d=>d.id===b.dataset.asmDraft);s.record=null;s.operations=null;render();});
    for(const b of dialog.querySelectorAll('[data-asm-rule]'))b.onclick=safe(()=>{flush();invalidate();const [id,v]=b.dataset.asmRule.split(':').map(Number);s.draft=null;s.operations=null;s.record=s.read.state.rules.find(r=>r.value.id===id&&r.value.version===v);s.kind='assembly-rule';render();});
    for(const b of dialog.querySelectorAll('[data-asm-binding]'))b.onclick=safe(()=>{flush();invalidate();s.draft=null;s.operations=null;s.record=s.read.state.bindings.find(r=>r.value.id===Number(b.dataset.asmBinding));s.kind='assembly-binding';render();});
    bind('asmPreview','click',preview);bind('asmConfirm','click',confirm);bind('asmCancel','click',()=>{s.operations=null;invalidate();report('已取消預覽；正式來源未變更。');});
    if(s.draft){if(s.draft.kind==='rule')ruleForm();else if(s.draft.kind==='instance')instanceForm();else bindingForm();}
    else if(s.record)published();else $('asmEditor').innerHTML='<h3>建立自己的接合關係</h3><p>新增規則後，依序建立槽位、構件與局部接合。</p>';
    syncFooter();placeStudioLesson(dialog.querySelector('#asmWorkspaceLesson'),'assembly:first','這裡定義誰抵住誰；尺寸在材料配置，確認後才寫進場景。');WorkspaceShell.refresh(dialog);dialog.removeAttribute('aria-busy');lockConfirm();
  }
  function ruleForm(){
    const d=s.draft.data,options=d.members.map(m=>[m.id,`構件 #${m.id} · ${d.slots.find(x=>x.id===m.slotId)?.name||'未命名槽位'}`]);
    $('asmEditor').innerHTML=`<h3>規則草稿 · 第 ${d.version} 版</h3>${field('名稱',input('asmName',d.name))}<section><h4>槽位</h4>${d.slots.map((v,i)=>`<div class="asm-row">${field('槽位 #'+v.id,input('asmSlot'+v.id,v.name))}${btn('asmSlotUp'+v.id,'上移',!i)}${btn('asmSlotDelete'+v.id,'刪除')}</div>`).join('')}${btn('asmAddSlot','新增槽位',d.slots.length>=8)}</section><section><h4>構件實例</h4>${d.members.map(m=>`<div class="asm-row">${field('構件 #'+m.id,select('asmMember'+m.id,d.slots.map(v=>[v.id,v.name||'未命名槽位']),m.slotId))}${btn('asmMemberDelete'+m.id,'刪除')}</div>`).join('')}${btn('asmAddMember','新增構件',!d.slots.length||d.members.length>=12)}</section><section><h4>局部接合</h4>${d.joints.map(j=>`<fieldset><legend>接合 #${j.id}</legend><div class="asm-grid">${field('交接區域識別',input('asmScope'+j.id,j.scope))}${field('接合方式',select('asmKind'+j.id,[['end-to-side','端抵側'],['ortho-split','正交分段']],j.kind))}${j.kind==='end-to-side'?field('終止構件',select('asmTerm'+j.id,options,j.terminatedMember))+field('目標構件',select('asmTarget'+j.id,options,j.targetMember))+field('終止端',select('asmEnd'+j.id,[['start','起點'],['finish','終點']],j.end)):field('連續構件',select('asmContinuous'+j.id,options,j.continuousMember))+field('分段一（末端）',select('asmFirst'+j.id,options,j.splitMembers[0]))+field('分段二（起端）',select('asmSecond'+j.id,options,j.splitMembers[1]))}${field('目標局部側面',select('asmSide'+j.id,['+u','-u','+v','-v'].map(v=>[v,sideWord[v]]),j.side))}${field('局部走向',select('asmDir'+j.id,[['u','沿 u'],['v','沿 v']],j.dir))}</div>${btn('asmSwap'+j.id,'交換此處的連續／終止角色')}${btn('asmJointDelete'+j.id,'刪除接合')}</fieldset>`).join('')}${btn('asmAddJoint','新增接合',d.members.length<2||d.joints.length>=16)}</section><section><h4>只表示誰抵住誰，尺寸見材料配置</h4><p class="asm-note">右側、左側、上側、下側對應資料裡的 +u、-u、+v、-v。</p><div class="asm-actions">${btn('asmRotate','旋轉檢視')}${btn('asmZoomIn','放大')}${btn('asmZoomOut','縮小')}</div><div id="asmDiagram"></div></section>${btn('asmDeleteDraft','刪除草稿')}`;
    bind('asmName','input',e=>{d.name=e.target.value;changed();});
    for(const v of d.slots){bind('asmSlot'+v.id,'input',e=>{v.name=e.target.value;changed();});bind('asmSlotUp'+v.id,'click',()=>{const i=d.slots.indexOf(v);[d.slots[i-1],d.slots[i]]=[v,d.slots[i-1]];changed(true);});bind('asmSlotDelete'+v.id,'click',()=>{const used=d.members.filter(m=>m.slotId===v.id);if(used.length)throw Error(`槽位 #${v.id} 仍被構件 ${used.map(m=>'#'+m.id).join('、')} 使用。`);d.slots=d.slots.filter(x=>x!==v);changed(true);});}
    bind('asmAddSlot','click',()=>{d.slots.push({id:next(d.slots),name:''});changed(true);});
    for(const m of d.members){bind('asmMember'+m.id,'change',e=>{m.slotId=Number(e.target.value);changed();});bind('asmMemberDelete'+m.id,'click',()=>{const used=d.joints.filter(j=>[j.terminatedMember,j.targetMember,j.continuousMember,...(j.splitMembers||[])].includes(m.id));if(used.length)throw Error(`構件 #${m.id} 仍被接合 ${used.map(j=>'#'+j.id).join('、')} 使用。`);d.members=d.members.filter(x=>x!==m);changed(true);});}
    bind('asmAddMember','click',()=>{d.members.push({id:next(d.members),slotId:d.slots.at(-1).id});changed(true);});
    bind('asmAddJoint','click',()=>{const id=next(d.joints);d.joints.push({id,kind:'end-to-side',scope:'junction-'+id,terminatedMember:d.members[1].id,targetMember:d.members[0].id,end:'start',side:'+u',dir:'u'});changed(true);});
    for(const j of d.joints){
      for(const [p,k,event,n] of [['asmScope','scope','input'],['asmTerm','terminatedMember','change',true],['asmTarget','targetMember','change',true],['asmEnd','end','change'],['asmSide','side','change'],['asmDir','dir','change']])bind(p+j.id,event,e=>{j[k]=n?Number(e.target.value):e.target.value;changed();});
      bind('asmKind'+j.id,'change',e=>{if(e.target.value==='ortho-split'){if(d.members.length<3){e.target.value=j.kind;throw Error('正交分段需要三個不同構件。');}const ids=[j.targetMember,j.terminatedMember,...d.members.map(m=>m.id)].filter((x,i,a)=>a.indexOf(x)===i);Object.assign(j,{kind:'ortho-split',continuousMember:ids[0],splitMembers:ids.slice(1,3)});delete j.targetMember;delete j.terminatedMember;delete j.end;}else{Object.assign(j,{kind:'end-to-side',targetMember:j.continuousMember,terminatedMember:j.splitMembers[0],end:'finish'});delete j.continuousMember;delete j.splitMembers;}changed(true);});
      bind('asmContinuous'+j.id,'change',e=>{const id=Number(e.target.value),i=j.splitMembers.indexOf(id);if(i>=0)j.splitMembers[i]=j.continuousMember;j.continuousMember=id;changed(true);});
      for(const [p,i] of [['asmFirst',0],['asmSecond',1]])bind(p+j.id,'change',e=>{j.splitMembers[i]=Number(e.target.value);changed();});
      bind('asmSwap'+j.id,'click',()=>{if(j.kind==='end-to-side')[j.targetMember,j.terminatedMember]=[j.terminatedMember,j.targetMember];else [j.continuousMember,j.splitMembers[0]]=[j.splitMembers[0],j.continuousMember];changed(true);});bind('asmJointDelete'+j.id,'click',()=>{d.joints=d.joints.filter(x=>x!==j);changed(true);});
    }
    bind('asmRotate','click',()=>{s.rotation=(s.rotation+90)%360;diagram();});bind('asmZoomIn','click',()=>{s.zoom=Math.min(1.5,s.zoom+.1);diagram();});bind('asmZoomOut','click',()=>{s.zoom=Math.max(.6,s.zoom-.1);diagram();});bindDeleteDraft();diagram();
  }
  function bindDeleteDraft(){bind('asmDeleteDraft','click',()=>{const id=s.draft.id;s.draft=null;ReferenceWorkspace.removeAssemblyDraft(id,s.context);invalidate();render();});}
  function diagram(){
    const container=$('asmDiagram'),d=s?.draft?.kind==='rule'?s.draft.data:s?.record?.value;if(!container||!d?.joints)return;
    const caption=j=>(j.kind==='end-to-side'?`${spoken(d,j.terminatedMember)}的${endWord[j.end]||j.end}抵住${spoken(d,j.targetMember)}的${sideWord[j.side]||j.side}`:`${spoken(d,j.continuousMember)}在此連續通過；分段一 ${spoken(d,j.splitMembers[0])}的終點抵住${sideWord[j.side]}，分段二 ${spoken(d,j.splitMembers[1])}的起點抵住相反側`)+`；局部走向 ${j.dir}。規則示意，非施工尺寸。`;
    container.innerHTML=d.joints.map(j=>{
      const angle={'+u':0,'-u':180,'+v':90,'-v':270}[j.side],target=j.targetMember??j.continuousMember;
      const opposite={'+u':'-u','-u':'+u','+v':'-v','-v':'+v'};
      const branch=(id,a,end,side)=>{
        const start=end==='start'?48:126,finish=end==='finish'?48:126;
        const marker=(e,x)=>e==='start'?`<circle data-end="start" cx="${x}" cy="0" r="5" fill="white" stroke="#334" stroke-width="2"/>`:`<rect data-end="finish" x="${x-5}" y="-5" width="10" height="10" fill="#334"/>`;
        return `<g data-member="${id}" data-contact-end="${end}" data-contact-side="${side}" transform="rotate(${a})"><title>${esc(spoken(d,id))} #${id}：${endWord[end]}接觸${sideWord[side]}</title><rect x="48" y="-14" width="78" height="28" fill="#daac71"/><line x1="40" y1="0" x2="48" y2="0" stroke="#334" stroke-width="3"/>${marker('start',start)}${marker('finish',finish)}<line data-member-axis="start-finish" x1="${start}" y1="20" x2="${finish}" y2="20" stroke="#334" stroke-width="2"/><path d="M ${finish+(finish>start?-7:7)} 16 L ${finish} 20 L ${finish+(finish>start?-7:7)} 24" fill="none" stroke="#334" stroke-width="2"/><text x="48" y="-23" text-anchor="middle" transform="rotate(${-a-s.rotation},48,-27)">${endWord[end]}</text><text x="126" y="-23" text-anchor="middle" transform="rotate(${-a-s.rotation},126,-27)">${endWord[end==='start'?'finish':'start']}</text><text x="88" y="4" text-anchor="middle" transform="rotate(${-a-s.rotation},88,0)">#${id}</text></g>`;
      };
      // The contact map is topological. A separate local-axis key displays dir
      // without deriving geometry or rewriting local identities from SVG pixels.
      const dx=j.dir==='u'?30:0,dy=j.dir==='v'?30:0;
      return `<figure data-diagram-joint="${j.id}"><figcaption>${esc(caption(j))}</figcaption><svg viewBox="0 0 360 424" role="img" aria-label="${esc(caption(j))}"><g data-local-direction="${j.dir}" transform="translate(45 42) rotate(${s.rotation})"><path d="M -18 0 H 18 M 0 -18 V 18" stroke="#889bc7" fill="none"/><line data-direction-axis="${j.dir}" x1="0" y1="0" x2="${dx}" y2="${dy}" stroke="#334" stroke-width="3"/><path d="${j.dir==='u'?'M 23 -5 L 30 0 L 23 5':'M -5 23 L 0 30 L 5 23'}" stroke="#334" fill="none" stroke-width="3"/></g><text x="95" y="47">局部走向 ${esc(j.dir)}（箭頭）</text><g data-contact-map="${j.id}" transform="translate(180 200) rotate(${s.rotation}) scale(${s.zoom*.65})"><rect data-member="${target}" data-continuous="${j.kind==='ortho-split'}" x="-40" y="-40" width="80" height="80" fill="#889bc7"/><text x="0" y="5" text-anchor="middle" transform="rotate(${-s.rotation})">#${target}${j.kind==='ortho-split'?' 連續':''}</text>${['+u','-u','+v','-v'].map((v,i)=>{const [x,y]=[[40,0],[-40,0],[0,40],[0,-40]][i];return `<text data-local-side="${v}" x="${x}" y="${y-6}" text-anchor="middle" transform="rotate(${-s.rotation},${x},${y-10})">${v}</text>`;}).join('')}${branch(j.terminatedMember??j.splitMembers?.[0],angle,j.kind==='ortho-split'?'finish':j.end,j.side)}${j.kind==='ortho-split'?branch(j.splitMembers[1],(angle+180)%360,'start',opposite[j.side]):''}</g>${['+u','-u','+v','-v'].map((v,i)=>{const x=8+i*88;return `<g role="button" tabindex="0" data-face="${v}" data-joint="${j.id}" aria-pressed="${j.side===v}" aria-label="接合 ${j.id} 目標側面 ${sideWord[v]}"><rect x="${x}" y="348" width="80" height="68" rx="4" fill="${j.side===v?'#f8dc6b':'#f3f5fa'}" stroke="#445"/><text x="${x+40}" y="387" text-anchor="middle">${sideWord[v]} ${v}</text></g>`;}).join('')}</svg></figure>`;
    }).join('')||'<p>加入接合後會顯示局部構件與可選側面。</p>';
    for(const n of container.querySelectorAll('[data-face]')){const pick=()=>{if(!s.draft||confirming())return;d.joints.find(j=>j.id===Number(n.dataset.joint)).side=n.dataset.face;changed(true);};n.onclick=pick;n.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();pick();}};}
  }
  function sources(axis){const a=[['','尚未選擇'],['literal','直接輸入 mm']];for(const r of s.engineering.materials||[]){const m=r.value||r;if(m.kind==='timber')a.push([JSON.stringify({kind:'material',id:m.id,version:m.version,field:axis}),`${m.name} v${m.version} · ${axis} ${m[axis]} mm`]);}for(const c of s.engineering.parameters||[])for(const f of c.fields)if(f.type==='dimension')a.push([JSON.stringify({kind:'parameter',parameterId:c.id,fieldId:f.id}),`${c.name}.${f.name}`]);for(const v of s.engineering.specs||[])a.push([JSON.stringify({kind:'spec',name:v.name}),`尺寸 ${v.name}`]);return a;}
  function bindingForm(){
    const d=s.draft.data,r=s.read.state.rules.find(r=>r.value.id===d.rule.id&&r.value.version===d.rule.version)?.value;
    $('asmEditor').innerHTML=`<h3>材料配置草稿</h3>${field('名稱',input('asmName',d.name))}${field('固定規則版本',select('asmBindingRule',s.read.state.rules.map(r=>[r.value.id+':'+r.value.version,`${r.value.name} · 第 ${r.value.version} 版`]),d.rule.id+':'+d.rule.version))}<div id="asmMapping"></div>${d.slots.map(v=>`<fieldset><legend>${esc(r?.slots.find(x=>x.id===v.slotId)?.name||'遺失槽位')} #${v.slotId}</legend><div class="asm-grid">${['A','B'].map(axis=>{const src=v[axis],options=sources(axis),value=src?.kind==='literal'?'literal':src?JSON.stringify(src):'';if(value&&!options.some(o=>o[0]===value))options.push([value,'原來源（請預覽確認）']);return field(axis+' 尺寸來源',select(`asmSource${v.slotId}${axis}`,options,value))+field(axis+' mm',input(`asmValue${v.slotId}${axis}`,src?.kind==='literal'?src.value:'','number'));}).join('')}${field('接觸面',select('asmContact'+v.slotId,[['','尚未選擇'],['A','A 面'],['B','B 面']],v.contactFace||''))}${field('A/B 擺向',select('asmOrientation'+v.slotId,[['','尚未選擇'],['A','A 沿局部 u'],['B','B 沿局部 u']],v.orientation||''))}</div></fieldset>`).join('')}${btn('asmDeleteDraft','刪除草稿')}`;
    bind('asmName','input',e=>{d.name=e.target.value;changed();});
    bind('asmBindingRule','change',()=>{invalidate();const [id,version]=$('asmBindingRule').value.split(':').map(Number),record=s.read.state.rules.find(r=>r.value.id===id&&r.value.version===version),ref=ruleReference(record),next=record.value;
      $('asmMapping').innerHTML=`<fieldset><legend>明確對應新版槽位</legend>${next.slots.map(v=>field(v.name,select('asmMap'+v.id,[['','未設定'],...d.slots.map(old=>[old.slotId,r?.slots.find(x=>x.id===old.slotId)?.name||'#'+old.slotId])],''))).join('')}${btn('asmApplyMapping','套用槽位對應到草稿')}${btn('asmCancelMapping','取消換版')}</fieldset>`;$('asmPreview').disabled=true;
      bind('asmApplyMapping','click',()=>{d.slots=next.slots.map(v=>{const old=d.slots.find(x=>x.slotId===Number($('asmMap'+v.id).value));return old?{...clone(old),slotId:v.id}:{slotId:v.id,A:null,B:null,contactFace:null,orientation:null};});d.rule={id,version};s.draft.base_ref=ref;changed(true);});bind('asmCancelMapping','click',render);
    });
    for(const v of d.slots){for(const axis of ['A','B']){const source=$(`asmSource${v.slotId}${axis}`),value=$(`asmValue${v.slotId}${axis}`);value.disabled=source.value!=='literal';source.onchange=safe(()=>{value.disabled=source.value!=='literal';v[axis]=source.value==='literal'?{kind:'literal',value:value.value===''?'':Number(value.value)}:source.value?JSON.parse(source.value):null;changed();});value.oninput=safe(()=>{v[axis]={kind:'literal',value:value.value===''?'':Number(value.value)};changed();});}for(const [p,k] of [['asmContact','contactFace'],['asmOrientation','orientation']])bind(p+v.slotId,'change',e=>{v[k]=e.target.value||null;changed();});}bindDeleteDraft();
  }
  function faceWords(slot){const contact=slot?.contactFace==='A'?'接觸面是 A 面':slot?.contactFace==='B'?'接觸面是 B 面':'接觸面尚未選擇',orient=slot?.orientation==='A'?'A 沿局部 u':slot?.orientation==='B'?'B 沿局部 u':'擺向尚未選擇';return `${contact}，${orient}`;}
  function bindingCards(record){const d=record.value,rule=s.read.state.rules.find(r=>r.value.id===d.rule.id&&r.value.version===d.rule.version)?.value;return d.slots.map(slot=>{const eff=record.effective.find(v=>v.slotId===slot.slotId),name=rule?.slots.find(v=>v.id===slot.slotId)?.name?.trim()||'未命名槽位',a=eff?.A?.value,b=eff?.B?.value,section=a==null||b==null?`A ${a??'未設定'} / B ${b??'未設定'} mm`:`截面 ${a} × ${b} mm`;return `<article class="asm-slot"><strong>${esc(name)}</strong><p>${esc(section)}</p><p class="asm-note">${esc(faceWords(slot))}</p></article>`;}).join('');}
  function published(){const r=s.record,d=r.value,isRule=s.kind==='assembly-rule',rule=isRule?null:s.read.state.rules.find(x=>x.value.id===d.rule.id&&x.value.version===d.rule.version)?.value;if(!isRule)captureBindingRule(r);$('asmEditor').innerHTML=`<h3>${esc(d.name)}</h3><p>${isRule?`第 ${d.version} 版已發布，內容固定。要改就做成下一版。`:`用「${esc(rule?.name||'規則')}」第 ${d.rule.version} 版。${r.complete?'':'還有尺寸或方向沒選。'}`}</p><div class="asm-actions">${isRule?btn('asmEdit','編輯為下一版',false,'primary-button')+btn('asmCopy','複製成新規則')+btn('asmBind',window.ContextOperations.getOperation('assembly-binding.create').label):btn('asmEdit','編輯材料配置',false,'primary-button')}${btn('asmDeletePublished','刪除'+(isRule?'此版本':'配置'))}</div>${isRule?'<h4>只表示誰抵住誰，尺寸見材料配置</h4><p class="asm-note">右側、左側、上側、下側對應資料裡的 +u、-u、+v、-v。</p><div id="asmDiagram"></div>':bindingCards(r)}${isRule?'':generationActions(d.id,r.complete)}`;if(!isRule)bindGenerationActions(d.id);bind('asmEdit','click',()=>newDraft(isRule?'rule':'binding',r,isRule));bind('asmCopy','click',()=>newDraft('rule',r));bind('asmBind','click',()=>newDraft('binding',r));bind('asmDeletePublished','click',async()=>{s.operations=[isRule?{op:'delete-rule',id:d.id,version:d.version}:{op:'delete-binding',id:d.id}];await preview();});diagram();}
  function generationActions(bindingId,complete){return `<section><h4>角材實例</h4>${btn('asmGenerate','依來源生成角材',!complete)}${(s.read.state.instances||[]).filter(r=>r.value.source.bindingId===bindingId).map(r=>`<article class="asm-slot"><strong>${esc(r.value.source.name)}</strong><p>${r.members.map(m=>`角材 #${m.timberId} · ${m.geometry?.length??'?'} mm`).join('；')}</p>${btn('asmInstanceEdit'+r.value.source.id,'編輯來源')}${btn('asmInstanceDelete'+r.value.source.id,'刪除實例')}</article>`).join('')}</section>`;}
  function bindGenerationActions(bindingId){bind('asmGenerate','click',()=>newInstance(bindingId));for(const r of s.read.state.instances||[])if(r.value.source.bindingId===bindingId){bind('asmInstanceEdit'+r.value.source.id,'click',()=>newInstance(bindingId,r));bind('asmInstanceDelete'+r.value.source.id,'click',async()=>{s.operations=[{op:'delete-instance',id:r.value.source.id,expectedFingerprint:r.fingerprint}];await preview();});}}
  async function newInstance(bindingId,record=null){
    if(confirming())return;flush();const x=s,g=x.generation;await readState(x);if(!current(x)||g!==x.generation)return;const binding=x.read.state.bindings.find(r=>r.value.id===bindingId),rule=x.read.state.rules.find(r=>r.value.id===binding?.value.rule.id&&r.value.version===binding?.value.rule.version);
    if(!binding?.complete||!rule)throw Error('請先選齊材料配置。');let data,base=null;
    if(record){const fresh=x.read.state.instances?.find(r=>r.value.source.id===record.value.source.id);if(!fresh||fresh.fingerprint!==record.fingerprint)throw Error('實例來源已變更，請重新開啟。');data=clone(fresh.value.source);base={id:data.id,fingerprint:fresh.fingerprint};}
    else{const r=rule.value;if(r.members.length!==3||r.joints.length!==2||r.joints.some(j=>j.kind!=='end-to-side')||r.joints[0].terminatedMember!==r.joints[1].terminatedMember)throw Error('首版只支援兩支主支與一支端接副支。');const sec=r.joints[0].terminatedMember,start=r.joints.find(j=>j.end==='start'),finish=r.joints.find(j=>j.end==='finish');if(!start||!finish)throw Error('副支必須有起端與末端接合。');const ids=await command('newid');if(!current(x)||g!==x.generation)return;const used=new Set([...(x.read.state.instances||[]).map(r=>r.value.source.id),...ReferenceWorkspace.getAssemblyDrafts().filter(d=>d.kind==='instance').map(d=>d.data.id)]);
      data={id:freeId(ids.assemblyInstance,used),name:binding.value.name+'・角材',bindingId,rule:{...binding.value.rule,fingerprint:rule.fingerprint},surfaceId:0,members:r.members.map(m=>({memberId:m.id,role:m.id===sec?'secondary':'primary',guideId:0,dir:m.id===sec?'+u':'+v',depthSide:'+n',ends:m.id===sec?{start:{kind:'member',memberId:start.targetMember},finish:{kind:'member',memberId:finish.targetMember}}:{start:{kind:'timber',id:0},finish:{kind:'timber',id:0}}}))};
    }
    invalidate();x.draft={id:crypto.randomUUID(),kind:'instance',base_ref:base,data,updated_at:new Date().toISOString()};x.operations=null;x.record=null;flush();render();
  }
  function instanceForm(){const d=s.draft.data,refs=s.references||{},guides=(refs.guides||[]).filter(Boolean),timbers=refs.timbers||[],surfaces=[...new Set(guides.map(g=>g.surface))],rule=s.read.state.rules.find(r=>r.value.id===d.rule.id&&r.value.version===d.rule.version)?.value;
    $('asmEditor').innerHTML=`<h3>${s.draft.base_ref?'編輯':'生成'}角材實例</h3>${field('名稱',input('asmInstanceName',d.name))}${field('材料配置',select('asmInstanceBinding',s.read.state.bindings.filter(r=>r.complete).map(r=>[r.value.id,r.value.name+' · 規則第 '+r.value.rule.version+' 版']),d.bindingId))}${field('承載面',select('asmInstanceSurface',[[0,'請選擇'],...surfaces.map(id=>[id,'承載面 #'+id])],d.surfaceId))}${d.members.map(m=>`<fieldset><legend>${esc(rule?spoken(rule,m.memberId):'構件 #'+m.memberId)} · ${m.role==='primary'?'主支沿面 v':'副支沿面 u'}</legend>${field('定位線',select('asmInstanceGuide'+m.memberId,[[0,'請選擇'],...guides.filter(g=>g.surface===d.surfaceId&&g.axis===(m.role==='primary'?'v':'u')).map(g=>[g.id,`定位線 #${g.id} · ${g.expression}`])],m.guideId))}${m.role==='primary'?['start','finish'].map(k=>field(k==='start'?'支撐邊界材一（無序）':'支撐邊界材二（無序）',select('asmInstanceEnd'+m.memberId+k,[[0,'請選擇'],...timbers.filter(t=>t.role==='boundary'&&t.geometry?.surface===d.surfaceId).map(t=>[t.id,'邊界角材 #'+t.id])],m.ends[k].id))).join(''):`<p>起端抵主支 #${m.ends.start.memberId}，末端抵主支 #${m.ends.finish.memberId} 的相向側面。</p>`}</fieldset>`).join('')}${btn('asmDeleteDraft','刪除草稿')}`;
    bind('asmInstanceName','input',e=>{d.name=e.target.value;changed();});bind('asmInstanceBinding','change',e=>{const b=s.read.state.bindings.find(r=>r.value.id===Number(e.target.value)),r=s.read.state.rules.find(r=>r.value.id===b.value.rule.id&&r.value.version===b.value.rule.version),sec=d.members.find(m=>m.role==='secondary');if(r.value.members.length!==3||r.value.members.some(m=>!d.members.some(old=>old.memberId===m.id))||r.value.joints.length!==2||r.value.joints.some(j=>j.kind!=='end-to-side'||j.terminatedMember!==sec.memberId)){render();throw Error('換版必須保留三個構件身分與主副支角色。');}d.bindingId=b.value.id;d.rule={...b.value.rule,fingerprint:r.fingerprint};for(const k of ['start','finish']){const joint=r.value.joints.find(j=>j.end===k);if(!joint)throw Error('新版缺少副支端接來源。');sec.ends[k]={kind:'member',memberId:joint.targetMember};}changed(true);});bind('asmInstanceSurface','change',e=>{d.surfaceId=Number(e.target.value);for(const m of d.members){m.guideId=0;if(m.role==='primary')for(const k of ['start','finish'])m.ends[k].id=0;}changed(true);});for(const m of d.members){bind('asmInstanceGuide'+m.memberId,'change',e=>{m.guideId=Number(e.target.value);changed();});if(m.role==='primary')for(const k of ['start','finish'])bind('asmInstanceEnd'+m.memberId+k,'change',e=>{m.ends[k].id=Number(e.target.value);changed();});}bindDeleteDraft();
  }
  function previewCopy(p){
    const rows=[],beforeR=new Map(p.before.rules.map(r=>[`${r.value.id}:${r.value.version}`,r])),afterR=new Map(p.after.rules.map(r=>[`${r.value.id}:${r.value.version}`,r]));
    const ruleTitle=r=>`「${r.value.name||'未命名規則'}」第 ${r.value.version} 版`,mmPair=slot=>`${slot?.A?.value??'未設定'}×${slot?.B?.value??'未設定'}`;
    const sourceKey=src=>JSON.stringify(!src?null:src.kind==='literal'?['literal']:src.kind==='parameter'?['parameter',src.parameterId,src.fieldId]:src.kind==='material'?['material',src.id,src.version,src.field]:src.kind==='spec'?['spec',src.name]:src);
    const sourceWords=src=>{
      if(!src)return '尚未選擇';
      if(src.kind==='literal')return '直接數值';
      if(src.kind==='parameter'){const card=s?.engineering?.parameters?.find(c=>c.id===src.parameterId),field=card?.fields.find(f=>f.id===src.fieldId);return `參數卡${card?.name?'「'+card.name+'」':''} #${src.parameterId} 的欄位${field?.name?'「'+field.name+'」':''} #${src.fieldId}`;}
      if(src.kind==='material'){const material=s?.engineering?.materials?.map(r=>r.value||r).find(m=>m.id===src.id&&m.version===src.version);return `材料${material?.name?'「'+material.name+'」':''} #${src.id} 第 ${src.version} 版 · ${src.field}`;}
      if(src.kind==='spec')return `尺寸「${src.name}」`;
      return JSON.stringify(src);
    };
    let added=0,removed=0;
    for(const [k,r] of afterR) if(!beforeR.has(k)){rows.push([`發布${ruleTitle(r)}`,'新增']);added++;}
    for(const [k,r] of beforeR) if(!afterR.has(k)){rows.push([`刪除${ruleTitle(r)}`,'移除']);removed++;}
    const beforeB=new Map(p.before.bindings.map(b=>[b.value.id,b])),afterB=new Map(p.after.bindings.map(b=>[b.value.id,b])),changed=[];
    for(const [id,b] of afterB){
      const old=beforeB.get(id);
      if(!old){rows.push([`新增配置「${b.value.name||'未命名配置'}」`,'新增']);changed.push(b);continue;}
      if(JSON.stringify(old.value)===JSON.stringify(b.value)&&JSON.stringify(old.effective)===JSON.stringify(b.effective)) continue;
      changed.push(b);
      const rule=p.after.rules.find(r=>r.value.id===b.value.rule.id&&r.value.version===b.value.rule.version)?.value||p.before.rules.find(r=>r.value.id===b.value.rule.id&&r.value.version===b.value.rule.version)?.value;
      const oldRule=p.before.rules.find(r=>r.value.id===old.value.rule.id&&r.value.version===old.value.rule.version)?.value;
      if(old.value.rule.id!==b.value.rule.id||old.value.rule.version!==b.value.rule.version) rows.push(['固定規則',`${oldRule?.name||'規則'} 第 ${old.value.rule.version} 版 → ${rule?.name||'規則'} 第 ${b.value.rule.version} 版`]);
      const ids=[...new Set([...(old.value.slots||[]),...(b.value.slots||[])].map(v=>v.slotId))];
      let contactSame=true;
      for(const slotId of ids){
        const o=old.value.slots.find(v=>v.slotId===slotId),n=b.value.slots.find(v=>v.slotId===slotId);
        const name=rule?.slots.find(v=>v.id===slotId)?.name?.trim()||oldRule?.slots.find(v=>v.id===slotId)?.name?.trim()||'未命名槽位';
        const before=old.effective.find(v=>v.slotId===slotId),after=b.effective.find(v=>v.slotId===slotId),from=mmPair(before),to=mmPair(after);
        const sourcesChanged=['A','B'].filter(axis=>sourceKey(o?.[axis])!==sourceKey(n?.[axis]));
        rows.push([name,from===to?(sourcesChanged.length?`截面仍為 ${to} mm`:'沒有改'):`截面 ${from} → ${to} mm`]);
        for(const axis of sourcesChanged){const a=before?.[axis]?.value,b=after?.[axis]?.value,dimension=a===b?`尺寸仍為 ${b??'未設定'}${b==null?'':' mm'}`:`尺寸 ${a??'未設定'} → ${b??'未設定'} mm`;rows.push([`${name} ${axis} 來源`,`${dimension}；${sourceWords(o?.[axis])} → ${sourceWords(n?.[axis])}`]);}
        if((o?.contactFace??null)!==(n?.contactFace??null)||(o?.orientation??null)!==(n?.orientation??null)){contactSame=false;rows.push([`${name}的接觸面與擺向`,`${faceWords(o)} → ${faceWords(n)}`]);}
      }
      if(contactSame) rows.push(['接觸面與擺向','沒有改']);
    }
    for(const [id,b] of beforeB) if(!afterB.has(id)){rows.push([`刪除配置「${b.value.name||'未命名配置'}」`,'移除']);removed++;}
    let title='變更預覽';
    if(!p.valid) title='這次還不能套用';
    else if(changed.length===1&&added===0&&removed===0) title=`這次會改「${changed[0].value.name||'未命名配置'}」`;
    else if(added===1&&changed.length===0&&removed===0){const only=[...afterR].find(([k])=>!beforeR.has(k));if(only) title=`這次會發布${ruleTitle(only[1])}`;}
    const beforeI=new Map((p.before.instances||[]).map(r=>[r.value.source.id,r])),afterI=new Map((p.after.instances||[]).map(r=>[r.value.source.id,r]));
    const owned=new Map();
    for(const records of [beforeI,afterI])for(const r of records.values())for(const m of r.members||[])owned.set(m.timberId,`構件 #${m.memberId} → 角材 #${m.timberId}`);
    for(const id of new Set([...beforeI.keys(),...afterI.keys()])){const a=beforeI.get(id),b=afterI.get(id);if(identityValue(a)!==identityValue(b)){title=b?`這次會${a?'更新':'生成'}「${b.value.source.name}」`:`這次會刪除「${a.value.source.name}」與所屬角材`;rows.push(['來源',JSON.stringify(b?.value.source||a.value.source)]);}}
    // The native candidate supplies all geometry, including ordinary external
    // dependents. Membership labels are presentation only, never the impact set.
    const describe=g=>g?`承載面 #${g.surface}，中心線 ${g.centerline} mm，長度 ${g.length} mm，局部位置 ${g.u},${g.v}，世界位置 ${g.origin.join(',')}，擺向 ${g.dir}/${g.side}，A ${g.A} / B ${g.B}，世界軸 ${g.axes.map(a=>a.join(',')).join(' / ')}`:'無';
    const unchanged=[];
    for(const t of p.impact?.timbers||[]){
      const label=owned.get(t.id)||`角材 #${t.id}（組構外）`;
      if(identityValue(t.before)===identityValue(t.after)){
        unchanged.push(`#${t.id}`);
        if(owned.has(t.id))rows.push([label,`沒有幾何變更；${describe(t.after)}`]);
      }
      else rows.push([label,`${describe(t.before)} → ${describe(t.after)}`]);
    }
    if(unchanged.length)rows.push(['未變更角材',unchanged.join('、')]);
    for(const g of p.impact?.guides||[])if(identityValue(g.before)!==identityValue(g.after))rows.push([`定位線 #${g.id}`,`${JSON.stringify(g.before)} → ${JSON.stringify(g.after)}`]);
    return `<h4>${esc(title)}</h4>${rows.length?`<div class="asm-diff">${rows.map(([a,b])=>`<p><span>${esc(a)}</span><span>${esc(b)}</span></p>`).join('')}</div>`:'<p>正式內容不會改變。</p>'}`;
  }
  async function preview(){
    if(confirming())return;flush();ReferenceWorkspace.assertEditable();invalidate();const x=s,g=x.generation,seq=++serial,operations=x.operations||[{op:x.draft.kind==='rule'?'publish-rule':'create-binding',value:clone(x.draft.data)}],read=await command('assembly-read');if(!current(x)||g!==x.generation)return;
    if(!x.operations){
      const d=x.draft;
      if(d.kind==='binding'){
        const original=read.state.bindings.find(r=>r.value.id===d.data.id),intent=d.binding_intent;
        if(intent?.mode==='update'){
          if(!original||identityValue(original.value)!==identityValue(intent.source))throw Error('原始配置已變更或移除；草稿仍保留，請從已發布配置重新開啟編輯。');
          if(!/^[a-f0-9]{64}$/.test(original.fingerprint||''))throw Error('原生服務缺少配置來源指紋，請更新服務再預覽；草稿仍保留。');
          operations[0]={op:'edit-binding',id:d.data.id,expectedFingerprint:original.fingerprint,value:clone(d.data)};
        }else if(original)throw Error('新增或舊版草稿的配置身分已被占用；草稿仍保留，請另建配置，或從已發布配置明確開啟編輯。');
        if(d.base_ref){const ref=d.base_ref,rule=read.state.rules.find(r=>r.value.id===ref.id&&r.value.version===ref.version);if(!validRuleRef(ref)||d.data.rule.id!==ref.id||d.data.rule.version!==ref.version||!rule||rule.fingerprint!==ref.fingerprint)throw Error('材料配置的規則來源已變更或移除；草稿仍保留，請明確重新選擇規則並對應槽位。');}
      }else if(d.kind==='instance'){
        const binding=read.state.bindings.find(r=>r.value.id===d.data.bindingId),original=read.state.instances?.find(r=>r.value.source.id===d.data.id);
        if(!binding?.fingerprint)throw Error('材料來源不存在或服務未支援生成。');
        if(d.base_ref&&(!original||original.fingerprint!==d.base_ref.fingerprint))throw Error('原始實例已變更；草稿仍保留，請重新開啟。');
        operations[0]=d.base_ref?{op:'edit-instance',id:d.data.id,expectedFingerprint:d.base_ref.fingerprint,expectedBindingFingerprint:binding.fingerprint,value:clone(d.data)}:{op:'create-instance',expectedBindingFingerprint:binding.fingerprint,value:clone(d.data)};
      }else if(d.base_ref){
        const ref=d.base_ref,original=read.state.rules.find(r=>r.value.id===ref.id&&r.value.version===ref.version);
        if(d.data.id!==ref.id||!original||original.fingerprint!==ref.fingerprint)throw Error('原始規則版本已變更或移除；草稿仍保留，請重新開啟。');
      }else if(read.state.rules.some(r=>r.value.id===d.data.id))throw Error('新規則身分已被占用；草稿仍保留，請另建或複製規則。');
    }
    const generation=operations.some(o=>o.op.endsWith('-instance'));
    const response=await fetch(generation?'/assembly/generate-preview':'/assembly/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:generation?'assembly-generation-transaction/1':'assembly-transaction/1',expectedRevision:read.revision,operations}),signal:AbortSignal.timeout(30000)});checkApiSession(response);if(!response.ok)throw Error('預覽服務失敗（'+response.status+'）。');const p=checked(await response.json()).preview;
    if(!current(x)||g!==x.generation||seq!==serial){command('assembly-cancel '+p.token).catch(()=>{});return;}
    if(p.impact?.schema!=='candidate-geometry/1'||!Array.isArray(p.impact.timbers)||!Array.isArray(p.impact.guides)){await command('assembly-cancel '+p.token);throw Error('原生服務缺少完整幾何預覽，請更新服務再預覽；草稿仍保留。');}
    x.preview=p;$('asmConfirm').disabled=!p.valid;
    $('asmPreviewResult').innerHTML=`${previewCopy(p)}<ul>${(p.violations||[]).map(v=>`<li>${esc(v.message||v.actual||'驗證拒絕')}</li>`).join('')}</ul><details><summary>完整資料，給除錯對照</summary><h5>變更前</h5><pre>${esc(JSON.stringify(p.before,null,2))}</pre><h5>變更後</h5><pre>${esc(JSON.stringify(p.after,null,2))}</pre><h5>完整幾何對照</h5><pre>${esc(JSON.stringify(p.impact,null,2))}</pre></details>`;syncFooter();report(p.valid?'驗證通過，確認後才會套用。':'尚不能套用，請依上列原因修正。',!p.valid);
  }
  async function confirm(){
    const x=s;if(!current(x)||!x.preview?.valid||x.confirming)return;ReferenceWorkspace.assertEditable();flush();
    // Capture the candidate before awaiting. The lock keeps local edits out of the
    // native history step; identity/content checks also protect external updates.
    const tx={context:x.context,generation:x.generation,token:x.preview.token,draftId:x.draft?.id,draft:JSON.stringify(x.draft)};
    x.confirming=tx;lockConfirm();let committed=false;
    try{
      await command('assembly-confirm '+tx.token);
      committed=true;
      if(!current(x))return;
      const saved=ReferenceWorkspace.getAssemblyDrafts().find(d=>d.id===tx.draftId);
      const unchanged=x.generation===tx.generation&&x.draft?.id===tx.draftId&&JSON.stringify(x.draft)===tx.draft&&JSON.stringify(saved)===tx.draft;
      if(unchanged&&tx.draftId){x.draft=null;ownDraft=true;try{ReferenceWorkspace.removeAssemblyDraft(tx.draftId,tx.context,false);}finally{ownDraft=false;}}
      else if(tx.draftId&&JSON.stringify(x.draft)===tx.draft&&JSON.stringify(saved)!==tx.draft)x.draft=saved||null;
      x.record=null;x.operations=null;x.preview=null;
      await readState(x);await renderObjects();
      if(current(x)){unlockConfirm(x);render();report(x.draft?'已套用送出時的內容；後續草稿仍保留，請重新預覽。':'已套用，可使用畫布復原；請保存專案。');}
    }catch(error){
      if(error.transport&&typeof connection!=='undefined'){
        if(current(x)){x.preview=null;x.confirming.uncertain=true;$('asmClose').disabled=false;report(committed?'已套用，但畫面更新失敗；返回畫布後重新連線，勿重送。':'套用結果尚未確認，草稿仍保留；返回畫布後重新連線，勿重送。',true);}
        // Keep inputs locked while the shared transport resolves its receipt.
        // A recovered result is read back, never inferred or re-submitted here.
        while(current(x)&&connection.phase!=='ready')await new Promise(resolve=>setTimeout(resolve,250));
        if(current(x)){await readState(x);unlockConfirm(x);render();report(committed?'已套用且畫面已更新；請保存專案。':'連線已恢復，草稿仍保留；請核對已發布內容，再重新預覽。');}
        return;
      }
      if(current(x)){x.preview=null;unlockConfirm(x);render();}
      // Never retry an uncertain commit. apiRequest owns exact receipt recovery.
      throw error;
    }finally{unlockConfirm(x);if(current(x))dialog.removeAttribute('aria-busy');}
  }
  function card(o){const g=el('g',{class:'ocard assembly-card','data-kind':o.kind,'data-id':o.id,transform:`translate(${o.cx},${o.cy})`,cursor:'pointer'});g.classList.toggle('selected',ocSelected(o.kind,o.id));el('rect',{width:OC_W,height:OC_H,rx:12,fill:'#fff',stroke:'#9299b2','stroke-width':1.5},g);const t=el('text',{x:14,y:28,'font-size':14,fill:'#343e58'},g);t.textContent=Array.from(o.name).slice(0,16).join('');el('title',{},t).textContent=o.name;el('text',{x:14,y:65,'font-size':13,fill:'#667085'},g).textContent=o.kind==='assembly-rule'?`組構規則 #${o.id} v${o.version}`:`材料配置 #${o.id}`;el('text',{x:14,y:95,'font-size':13,fill:'#667085'},g).textContent=o.kind==='assembly-rule'?'局部接合 · 固定版本':o.complete?'配置完整':'未完成配置';return g;}
  function inspector(pane,o){
    if(o.kind!=='assembly-rule'){pane.innerHTML=`<h3>${esc(o.name)}</h3><p>${o.complete?'材料配置完整':'材料配置未完成'}</p>${btn('asmInspectorOpen','開啟組構工作區')}`;bind('asmInspectorOpen','click',()=>open(o.kind,o.id));return;}
    const selection={kind:o.kind,id:o.id,version:o.version,fingerprint:o.fingerprint},context=token();
    const valid=validRuleRef(selection),operation=window.ContextOperations.getOperation('assembly-binding.create');
    pane.innerHTML=`<h3>${esc(o.name)}</h3><p>組構規則 v${esc(String(o.version))} · ${valid?'材料與接觸方向可在配置中補齊；配置本身不產生角材。':'缺少固定來源，請更新服務後重新選取。'}</p>${btn('asmInspectorOpen',operation.label,!valid,'primary-button')}`;
    const button=$('asmInspectorOpen'),selected=()=>pane.isConnected!==false&&pane.contains(button)&&context===token()&&typeof oc!=='undefined'&&oc.selection.length===1&&oc.sel?.kind===o.kind&&oc.sel.id===o.id&&ocFind(o.kind,o.id)===o;
    bind('asmInspectorOpen','click',async()=>{button.disabled=true;try{await createBindingFromRule(selection,selected);}finally{if(pane.contains(button))button.disabled=!valid;}});
  }
  async function remove(kind,id){if(confirming())return;await open(kind,id);if(!s?.record||confirming())return;s.operations=[kind==='assembly-rule'?{op:'delete-rule',id,version:s.record.value.version}:{op:'delete-binding',id}];await preview();}
  window.addEventListener('project-local-history',event=>{
    if(!s||!dialog.open||confirming()||s.context!==event.detail?.previousContextToken||token()!==event.detail.contextToken)return;
    invalidate();s.context=event.detail.contextToken;
    const saved=ReferenceWorkspace.getAssemblyDrafts().find(d=>d.id===s.draft?.id);
    if(s.draft)s.draft=saved||null;render();
  });
  dialog.addEventListener('cancel',e=>{e.preventDefault();close();});window.addEventListener('geometry-definition-changed',()=>{if(s&&!confirming()){invalidate();report('工程來源已變更，請重新預覽。');}});window.addEventListener('project-info-changed',()=>{if(s&&!current(s)){unlockConfirm(s);s=null;dialog.close();WorkspaceShell.detach(dialog);}else if(s?.read&&!ownDraft&&s.draftsRef!==ReferenceWorkspace.context().assemblyDrafts){const saved=ReferenceWorkspace.getAssemblyDrafts().find(d=>d.id===s.draft?.id);if(s.draft)s.draft=saved||null;invalidate();render();}});
  $('btnNewAssembly').onclick=safe(async()=>{$('createObjectPop').hidden=true;await open();});
  return {open,close,flush,card,inspector,remove,createBindingFromRule,get isOpen(){return dialog.open;},get canCloseForRecovery(){return dialog.open&&!!s?.confirming?.uncertain&&current(s);}};
})();
