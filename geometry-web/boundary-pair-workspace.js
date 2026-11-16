/* R17 H adapter: native D16a owns allocation, joint evaluation and commit.
   The two row draft and candidate token never enter project attachments. */
window.BoundaryPairWorkspace = (() => {
  'use strict';
  const $=id=>document.getElementById(id),esc=value=>ReferenceWorkspace.escape(value);
  let form=null,cache=null,reading=null,entrySequence=0;
  const stamp=()=>({context:ReferenceWorkspace.context(),frame:ReferenceWorkspace.history.frame,
    edit:oc.edit,bid:oc.edit?.bid,sid:feSid(oc.edit?.bid),session:connection.session,
    revision:ReferenceWorkspace.getProjectState().revision});
  const owns=s=>!!s&&s.context===ReferenceWorkspace.context()&&s.edit===oc.edit&&s.bid===oc.edit?.bid&&
    s.sid===feSid(oc.edit?.bid)&&s.session===connection.session;
  const current=s=>owns(s)&&s.frame===ReferenceWorkspace.history.frame&&s.revision===ReferenceWorkspace.getProjectState().revision;
  const active=bid=>!!form&&owns(form.stamp)&&form.stamp.bid===bid;
  const hasWork=()=>!!form&&(form.dirty||form.busy||form.preview||form.uncertain||form.confirming);
  const rowDefault=()=>({edge:'',A:String(GeometryApplication.woodworking.section.A),B:String(GeometryApplication.woodworking.section.B),direction:'+u',side:'+n'});
  function report(message,error=false){const node=$('tbPairStatus');if(node){node.textContent=message;node.classList.toggle('fi-error',error);}else if(error)toast(message);}
  const safe=run=>async()=>{try{await run();}catch(error){report(error.message,true);}};
  async function post(path,body){
    const session=connection.session;
    const requestId=path==='/boundary-pair/preview'?crypto.randomUUID():null;
    try{
      const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Geometry-Version':pageRuntimeVersion,
        ...(requestId?{'X-Geometry-Request-Id':requestId,'X-Geometry-Session':session}:{})},body:JSON.stringify(body),signal:AbortSignal.timeout(30000)});
      checkApiSession(response);
      if(!session||session!==connection.session||response.headers.get('X-Geometry-Session')!==session)
        throw Error('互頂候選的服務識別已改變；請重新載入後再核對。');
      const result=await response.json();
      if(!response.ok||!result||typeof result.ok!=='boolean')throw Error('無法確認互頂服務回應；請重新連線。');
      if(requestId)acknowledgedApiResults.add(requestId);
      return result;
    }
    catch(error){
      if(requestId){
        pendingApiResults.set(requestId,'boundary-pair-preview '+requestId);
        try{
          if(session!==connection.session)throw error;
          const result=await readApiReceipt(requestId);pendingApiResults.delete(requestId);acknowledgedApiResults.add(requestId);
          return {...result,receiptKnown:true};
        }
        catch(_){connectionFailed('互頂預覽結果尚未取得；重新連線將查本次回執，不重送。');}
      }
      throw error;
    }
  }
  function validRead(result,bid){
    return result.ok&&result.schema==='boundary-pair-read-result/1'&&result.boundaryId===bid&&
      typeof result.revision==='string'&&/^(0|[1-9]\d{0,19})$/.test(result.revision)&&
      /^[a-f0-9]{64}$/.test(result.contextKey||'')&&Array.isArray(result.groups)&&
      result.groups.every(group=>Number.isInteger(group.first)&&Number.isInteger(group.second)&&
        Array.isArray(group.members)&&group.members.length===2&&group.members.every(member=>member?.source));
  }
  async function read(s){
    const result=await post('/boundary-pair/read',{schema:'boundary-pair-read/1',boundaryId:s.bid});
    if(!current(s))throw Error('面、專案或來源已變更，請重新選取。');
    if(!validRead(result,s.bid))throw Error(result.error||'服務未提供完整的互頂組定義。');
    cache={stamp:s,result};return result;
  }
  function groupFor(id){return cache&&current(cache.stamp)?cache.result.groups.find(group=>group.first===id||group.second===id):null;}
  function rowsFrom(group){return group.members.map(member=>({edge:member.source.edge,A:String(member.A),B:String(member.B),direction:member.source.dir,side:member.source.side}));}
  function fixedEdges(surf){
    const fixity=oc.bmap[oc.edit?.bid]?.[0]?.fixity||[];
    return (surf?.outerEdges||[]).filter(edge=>Number.isInteger(edge.edge)&&fixity[edge.edge]===1);
  }
  function renderPair(){
    const root=$('tbBoundaryPair');if(!root||!active(oc.edit?.bid))return;
    const value=form,surf=oc.surfs.find(surface=>surface.id===value.stamp.sid),edges=fixedEdges(surf);
    const select=(id,field,options,selected)=>`<select id="${id}" data-field="${field}">${options.map(([key,label])=>`<option value="${esc(key)}"${key===selected?' selected':''}>${esc(label)}</option>`).join('')}</select>`;
    root.innerHTML=`<p id="tbPairOperation">${value.ids?'編輯互頂組 '+value.ids.join('＋'):'新增兩支互頂壁邊材'}</p>`+
      '<p class="face-help">依序選兩條固定外邊與截面；兩支沿各自整條邊放置。先預覽兩支與下游，確認才整筆套用。</p>'+
      value.rows.map((row,index)=>{const n=index+1,prefix='tbPair'+n;
        return `<fieldset data-boundary-pair-member="${n}"><legend>壁邊材 ${value.ids?value.ids[index]:n}</legend><div class="place-form">`+
          `<label>固定外邊${select(prefix+'Anchor','anchor',[['','請選一條固定外邊'],...edges.map(edge=>['e'+edge.edge,`外邊 e${edge.edge} · 沿 ${edge.axis}`])],row.edge)}</label>`+
          `<label>寬 A（沿面）<input id="${prefix}A" data-field="A" type="number" min="1" step="1" value="${esc(row.A)}"></label>`+
          `<label>厚 B（出面）<input id="${prefix}B" data-field="B" type="number" min="1" step="1" value="${esc(row.B)}"></label>`+
          `<label>延伸方向${select(prefix+'Dir','dir',['+u','-u','+v','-v'].map(dir=>[dir,timberDirectionName(dir)]),row.direction)}</label>`+
          `<label>厚度朝${select(prefix+'Side','side',timberSideOptions(surf),row.side)}</label></div>`+
          `<button type="button" class="btn" id="tbPairPick${n}" aria-pressed="${value.pick===index}">點畫布選第 ${n} 條邊</button></fieldset>`;
      }).join('')+
      '<p id="tbPairStatus" role="status" aria-live="polite">尚未提交；兩支角色固定為壁邊材。</p>'+
      '<div class="tb-pair-actions"><button type="button" class="primary-button" id="tbPairPreview">預覽兩支互頂</button><button type="button" class="btn" id="tbPairCancel">取消互頂輸入</button>'+
      (value.ids?'<button type="button" class="btn danger" id="tbPairDelete">預覽整組刪除</button>':'')+'</div>';
    for(const node of root.querySelectorAll('input,select'))node.addEventListener(node.tagName==='SELECT'?'change':'input',()=>{
      if(value!==form||value.busy)return;
      const index=Number(node.closest('[data-boundary-pair-member]').dataset.boundaryPairMember)-1;
      const field={anchor:'edge',dir:'direction',side:'side',A:'A',B:'B'}[node.dataset.field];
      value.rows[index][field]=node.value;value.dirty=true;
      if(field==='edge'){
        const edge=edges.find(edge=>'e'+edge.edge===node.value);
        if(edge){value.rows[index].direction='+'+edge.axis;$('tbPair'+(index+1)+'Dir').value='+'+edge.axis;}
      }
      report('輸入尚未保存；預覽確認後才寫入場景。');drawFaceEditor();
    });
    for(let index=0;index<2;index++)$('tbPairPick'+(index+1)).onclick=()=>{
      if(value.busy)return;value.pick=index;
      for(let k=0;k<2;k++)$('tbPairPick'+(k+1)).setAttribute('aria-pressed',String(k===index));
      feSetTool('timber');report(`下一次點選會填入第 ${index+1} 條邊；不會提交。`);
    };
    $('tbPairPreview').onclick=safe(()=>preview('upsert'));
    $('tbPairCancel').onclick=safe(()=>close());
    $('tbPairDelete')?.addEventListener('click',safe(()=>preview('delete')));
    lock();
  }
  function lock(){
    for(const node of $('tbBoundaryPair')?.querySelectorAll('button,input,select')||[])node.disabled=!!form?.busy;
    if($('tbPlacementMode'))$('tbPlacementMode').disabled=!!form?.busy;
  }
  async function openGroup(id,operation='edit'){
    if(form?.busy)throw Error('請先完成目前互頂候選。');
    const s=stamp(),entry=++entrySequence,selection=JSON.stringify([fe.sel,[...fe.timberSelection]]);
    const result=await read(s);
    if(entry!==entrySequence||selection!==JSON.stringify([fe.sel,[...fe.timberSelection]]))throw Error('選取已變更，未開啟先前的互頂組。');
    const group=result.groups.find(group=>group.first===id||group.second===id);
    if(!group)return false;
    ReferenceWorkspace.assertEditable();
    if(hasWork()&&!window.confirm('互頂輸入尚未保存。放棄這份輸入並編輯所選組？'))return true;
    form={stamp:s,rows:rowsFrom(group),ids:[group.first,group.second],dirty:false,pick:0,busy:false};
    fiShowTab('timber');renderFaceInspector();
    if(innerWidth<=680)openPanel('right',$('workspaceToggleRight'));
    if(operation==='delete')await preview('delete');else $('tbPair1Anchor')?.focus();
    return true;
  }
  async function close(){
    ++entrySequence;
    const value=form;if(!value)return;
    if(value.confirming||value.uncertain)throw Error('候選結果尚未取得；請先重新連線核對，尚未保存互頂輸入。');
    if(value.busy)throw Error('正在準備互頂候選，請等候預覽後取消。');
    if(value.preview)await cancel(value);
    if(form===value)form=null;
    renderFaceInspector();drawFaceEditor();
  }
  function operation(value,kind){
    if(kind==='delete')return {op:'delete',ids:[...value.ids]};
    const members=value.rows.map(row=>{
      const A=Number(row.A),B=Number(row.B);
      if(!/^e\d+$/.test(row.edge)||!Number.isSafeInteger(A)||!Number.isSafeInteger(B)||A<1||B<1)
        throw Error('請選齊兩條固定外邊，並填寫兩支的正整數截面 A／B。');
      return {A,B,edge:row.edge,direction:row.direction,side:row.side};
    });
    return {op:value.ids?'redeclare':'create',on:value.stamp.sid,members,...(value.ids?{ids:[...value.ids]}:{})};
  }
  function release(value){ReferenceWorkspace.finishTimberPreview(value.lease);value.lease=null;}
  async function cancel(value){
    if(!value.preview){release(value);return {ok:true};}
    if(value.stamp.session!==connection.session)throw Error('服務已變更，未取消其他服務的候選。');
    const result=await apiRequest(`boundary-pair-cancel ${value.preview.token} ${value.ownerKey}`);
    if(result.transport){value.uncertain=true;value.cancelUncertain=true;value.busy=true;lock();}
    if(!result.ok||result.transport)throw Error(result.error||'取消結果尚未確認，請重新連線。');
    value.preview=null;value.ownerKey=null;release(value);return result;
  }
  async function confirm(value){
    if(form!==value||!current(value.stamp)||!value.preview?.valid)throw Error('互頂候選已過期，請重新預覽。');
    ReferenceWorkspace.assertTimberPreview(value.lease,value.preview.token);
    value.confirming=true;
    const result=await apiRequest(`boundary-pair-confirm ${value.preview.token} ${value.ownerKey}`);
    if(result.transport){value.uncertain=true;report('確認結果尚未取得；重新連線只查本次回執，不重送。',true);return result;}
    value.confirming=false;value.preview=null;value.ownerKey=null;release(value);
    return result;
  }
  async function preview(kind='upsert'){
    const value=form;if(!value||value.busy||!current(value.stamp))return false;
    const proposed=operation(value,kind);
    value.operation=proposed.op;
    // Acquire before every await. R11's candidate retains its own lease and
    // is never cancelled merely because this separate entry was requested.
    value.lease=ReferenceWorkspace.beginTimberPreview();value.busy=true;lock();
    try{
      const result=await read(value.stamp);
      ReferenceWorkspace.assertTimberPreview(value.lease);
      value.uncertain=true;
      const prepared=await post('/boundary-pair/preview',{schema:'boundary-pair-transaction/1',boundaryId:value.stamp.bid,
        contextKey:result.contextKey,expectedRevision:result.revision,operation:proposed});
      if(!prepared.ok){
        if(prepared.code||prepared.receiptKnown)value.uncertain=false;
        if(prepared.diagnostics?.valid===false&&prepared.diagnostics.token===null){
          release(value);
          await confirmReferenceImpact(prepared.diagnostics,{boundaryPair:true,
            confirm:async()=>({ok:false,error:'違規候選不能確認。'}),cancel:async()=>({ok:true})});
        }
        throw Error(prepared.error||'完整互頂候選遭拒；場景保持原狀。');
      }
      if(!prepared.preview||!Number.isInteger(prepared.preview.token)||prepared.preview.token<1||
         !/^[a-f0-9]{64}$/.test(prepared.ownerKey||'')||!Array.isArray(prepared.preview.violations))
        throw Error('互頂候選資料不完整；請重新連線核對。');
      value.preview=prepared.preview;value.ownerKey=prepared.ownerKey;value.uncertain=false;
      ReferenceWorkspace.bindTimberPreview(value.lease,value.preview.token);
      if(form!==value||!current(value.stamp)){await cancel(value);return false;}
      const confirmed=await confirmReferenceImpact(value.preview,{boundaryPair:true,confirm:()=>confirm(value),cancel:()=>cancel(value)});
      if(value.uncertain)return false;
      if(confirmed.ok){
        const stillHere=owns(value.stamp);if(form===value)form=null;cache=null;
        if(stillHere){
          if(kind==='delete'){for(const id of value.ids)fe.timberSelection.delete(id);if(value.ids.includes(fe.sel?.id)&&fe.sel?.kind==='timber')fe.sel=null;}
          await feAfterChange();toast(confirmed.history_changed===false?'定義相同，未新增歷史。':'互頂組已整筆套用，可一步復原。');
        }
        return true;
      }
      report(confirmed.error||'已取消；場景保持原狀。',!confirmed.error?.startsWith('已取消'));
      return false;
    }catch(error){
      if(!value.uncertain){if(value.preview)await cancel(value);else release(value);}
      report(value.uncertain?'互頂候選結果尚未確認；請重新連線，尚未保存這份輸入。':error.message,true);
      return false;
    }finally{value.busy=!!value.uncertain;if(form===value)lock();}
  }
  function afterInspectorRender(pane){
    const mode=$('tbPlacementMode'),root=$('tbBoundaryPair'),single=$('tbSinglePlacement');if(!mode||!root||!single)return;
    if(form&&!owns(form.stamp)&&!form.busy)form=null;
    const pair=active(oc.edit?.bid);mode.value=pair?'boundary-pair':'single';single.hidden=pair;root.hidden=!pair;
    mode.onchange=async()=>{
      ++entrySequence;
      if(mode.value==='single'){try{await close();}catch(error){mode.value='boundary-pair';report(error.message,true);}return;}
      try{
        ReferenceWorkspace.assertEditable();
        if(feSid(oc.edit?.bid)==null)throw Error('請先放置這片面，再建立互頂組。');
        form={stamp:stamp(),rows:[rowDefault(),rowDefault()],ids:null,dirty:false,pick:0,busy:false};
        single.hidden=true;root.hidden=false;renderPair();feSetTool('timber');drawFaceEditor();
      }catch(error){mode.value='single';toast(error.message);}
    };
    if(pair)renderPair();
    $('tbPairEdit')?.addEventListener('click',safe(()=>openGroup(fe.sel.id)));
    const s=stamp();
    if(!reading&&(!cache||!current(cache.stamp))&&s.sid!=null&&connection.phase==='ready'){
      reading=read(s).then(()=>{if(current(s)&&fe.sel?.kind==='timber'&&groupFor(fe.sel.id))renderFaceInspector();}).catch(()=>{}).finally(()=>{reading=null;});
    }
  }
  function selectedHTML(id){
    const group=groupFor(id);if(!group)return null;
    return `<section id="tbSelected" class="inspector-block"><div class="ib-title">互頂組 ${group.first}＋${group.second}</div>`+
      `<p>兩支壁邊材是一筆操作；編輯保留原成員身分，刪除須整組預覽。</p>`+
      `<button type="button" class="btn primary-button" id="tbPairEdit">編輯互頂組</button> <button type="button" class="btn danger" id="tbSelDelete">整組刪除…</button></section>`;
  }
  function pickHit(hit){
    if(!active(oc.edit?.bid))return false;
    const value=form;if(value.busy)return true;
    const edges=fixedEdges(oc.surfs.find(surface=>surface.id===value.stamp.sid));
    const edge=hit?.[0]==='e'&&Number(hit[1])===0?edges.find(edge=>edge.edge===Number(hit[2])):null;
    if(!edge){report('互頂組只選普通外輪廓的固定邊；本次未改輸入。',true);return true;}
    const index=value.pick;value.rows[index].edge='e'+edge.edge;value.rows[index].direction='+'+edge.axis;
    value.pick=index===0?1:0;value.dirty=true;renderPair();
    report(`第 ${index+1} 支已選 e${edge.edge}；尚未提交，請核對兩列後按預覽。`);drawFaceEditor();return true;
  }
  function draw(root,el){
    if(!active(oc.edit?.bid))return;
    const vertices=oc.bmap[oc.edit.bid]?.[0]?.verts||[];
    for(const [index,row] of form.rows.entries()){
      if(!/^e\d+$/.test(row.edge))continue;
      const edge=Number(row.edge.slice(1)),a=vertices[edge],b=vertices[(edge+1)%vertices.length];if(!a||!b)continue;
      el('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],class:'fe-pair-edge','data-pair-slot':index+1},root);
    }
  }
  async function settleRecovered(command,result){
    if(!command.startsWith('boundary-pair-')||!form?.uncertain)return;
    const value=form;
    if(value.stamp.session!==connection.session)throw Error('回執不屬於原互頂工作階段，未釋放候選。');
    if(command.startsWith('boundary-pair-preview ')){
      if(result.ok){
        if(!Number.isInteger(result.preview?.token)||!/^[a-f0-9]{64}$/.test(result.ownerKey||''))
          throw Error('取回的互頂預覽不完整，未開放其他修改。');
        value.preview=result.preview;value.ownerKey=result.ownerKey;
        ReferenceWorkspace.bindTimberPreview(value.lease,value.preview.token);
        value.uncertain=false;
        value.recovering=true;
        try{await cancel(value);}finally{value.recovering=false;}
      }else {value.uncertain=false;release(value);}
      value.busy=false;lock();report('已查回上次預覽結果；未提交且候選已結束，原輸入保留，請重新預覽。');return;
    }
    if(command.startsWith('boundary-pair-cancel ')){
      value.uncertain=false;value.busy=false;value.cancelUncertain=false;
      if(result.ok){value.preview=null;value.ownerKey=null;release(value);report('已查回取消結果；場景保持原狀，原輸入保留。');}
      else report(result.error||'取消未送達，請再次取消此候選。',true);
      lock();return;
    }
    value.confirming=false;value.uncertain=false;value.busy=false;value.preview=null;release(value);form=null;cache=null;
    if(owns(value.stamp)){
      if(result.ok&&value.operation==='delete'){for(const id of value.ids)fe.timberSelection.delete(id);if(fe.sel?.kind==='timber'&&value.ids.includes(fe.sel.id))fe.sel=null;}
      await feAfterChange();toast(result.ok?'已查回互頂確認結果；沒有重送。':result.error||'候選未提交。');
    }
  }
  function assertWorldMutation(){
    if(hasWork())throw Error('互頂輸入或候選尚未保存；請先確認或取消，再修改其他來源或復原。');
  }
  function beforeSingleEntry(){assertWorldMutation();++entrySequence;form=null;}
  function isRecoveryCancel(command){
    return !!form?.recovering&&owns(form.stamp)&&command===`boundary-pair-cancel ${form.preview?.token} ${form.ownerKey}`;
  }
  window.DraftGate?.register(()=>{
    if(!hasWork()){++entrySequence;form=null;return true;}
    toast('互頂輸入或候選尚未保存；請先確認或取消，再離開或切換專案。');return false;
  });
  window.addEventListener('beforeunload',event=>{if(hasWork()){event.preventDefault();event.returnValue='';}});
  window.addEventListener('geometry-definition-changed',()=>{
    cache=null;if(form&&!form.confirming&&!form.busy&&!current(form.stamp))report('來源已變更；原互頂輸入保留，請取消後重新選取。',true);
  });
  return {active,afterInspectorRender,selectedHTML,groupFor,openGroup,pickHit,draw,preview,close,settleRecovered,assertWorldMutation,beforeSingleEntry,isRecoveryCancel,
    get hasWork(){return hasWork();}};
})();
