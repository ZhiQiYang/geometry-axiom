/* Compact canvas inspector. The model and confirmation transaction remain native. */
(() => {
  'use strict';
  const workspace = window.InfiniteGridWorkspace, esc = ReferenceWorkspace.escape;
  const axes = ['u', 'v'];
  let active = null;
  const sourceKey = o => GeometryProject.Features.gridSourceKey(o);
  const bindingKey = o => JSON.stringify(o && [o.id,o.system,o.boundary,o.vertexKey,o.cell,o.anchor]);
  const objectKey = o => o?.kind === 'grid-binding' ? bindingKey(o) : sourceKey(o);
  const current = s => active === s && s.pane.isConnected && s.node?.isConnected && s.pane.querySelector('#gridInlineInspector')===s.node && s.context === ReferenceWorkspace.context();
  const $ = (s,id) => s.pane.querySelector('#'+id);
  const isInfinite = o => o?.mode === 'infinite';
  const hasCells = o => isInfinite(o) && axes.every(a => ['repeat','repeat-panel'].includes(o[a+'Definition']?.source));
  const vertexId = v => v.loop < 0 ? 'outer:'+v.index : 'hole:'+v.loop+':'+v.index;
  const vertexTitle = v => `${v.loop < 0 ? '外環' : '孔洞 '+(v.loop+1)}・頂點 ${v.index+1}`;
  const catalogKey = () => JSON.stringify([(oc.gridSystems || []).map(sourceKey),(oc.faces || []).filter(b=>b.kind==='boundary').map(b=>[b.id,b.placed])]);
  const svg = (tag,attrs,parent) => {
    const n=document.createElementNS('http://www.w3.org/2000/svg',tag);
    Object.entries(attrs || {}).forEach(([k,v])=>n.setAttribute(k,v));parent?.append(n);return n;
  };
  function status(s,text,error=false) {
    if(!current(s))return;
    const n=$(s,'giStatus');n.textContent=text;n.classList.toggle('gi-error',error);
  }
  function definitionText(d) {
    if(!d || d.source==='none')return '未設定此軸';
    const stagger = d.stagger ? ` · 相鄰格子相位差 ${d.stagger} mm` : '';
    if(d.source==='repeat')return `每 ${d.step} mm · 基準 ${d.phase}${stagger}`;
    if(d.source==='repeat-panel')return `面材 ${d.panel} + 縫 ${d.gap} mm · 起點 ${d.anchor}${stagger}`;
    if(d.source==='series')return `有限等距 · ${d.count} 條`;
    if(d.source==='explicit')return `有限座標 · ${d.coordinates?.length || 0} 條`;
    return '有限面材排格';
  }
  function openFull(s) {
    if(!current(s)||s.busy)return;
    if(s.binding)workspace.openBinding(s.object.id);else workspace.openSystem(s.object.id);
  }
  function renderInspector(pane,object) {
    const context=ReferenceWorkspace.context(),key=objectKey(object);
    const renderKey=JSON.stringify([key,object.kind==='grid-binding'?sourceKey(oc.gridSystems.find(x=>x.id===object.system)):null,object.kind==='grid-binding'?oc.bmap[object.boundary]:null]);
    if(active?.pane===pane && active.context===context && active.renderKey===renderKey && pane.querySelector('#gridInlineInspector')){refreshCatalog(active);return;}
    disposeInspector();
    const binding=object.kind==='grid-binding';
    const s=active={pane,context,key,renderKey,catalogKey:catalogKey(),object:structuredClone(object),binding,busy:false,loadSerial:0,
      systems:structuredClone(oc.gridSystems || []),boundaries:structuredClone((oc.faces || []).filter(b=>b.kind==='boundary')),
      source:binding ? structuredClone(oc.gridSystems.find(x=>x.id===object.system)) : structuredClone(object),
      anchor:binding ? structuredClone(object.anchor) : null,vertices:[],vertex:null,boundary:null};
    pane.innerHTML=`<section id="gridInlineInspector" class="gi-inspector" data-gi-kind="${binding?'binding':'source'}"><header class="gi-header"><div class="gi-heading"><span class="gi-eyebrow">${binding?'配置設定':'網格來源'}</span><h2>${binding?'網格配置 '+object.id:esc(object.name)}</h2></div><div class="gi-actions"><button type="button" id="gridObjectOpen" class="btn gi-open">完整工作區</button>${!binding && isInfinite(object)?'<button type="button" id="gridObjectNewBinding" class="btn">建立配置</button>':''}</div></header>${binding?bindingForm(s):sourceForm(s)}<footer class="gi-footer"><p id="giStatus" role="status" aria-live="polite">${binding?'對齊邊界的實際頂點與格子內的位置。':'修改間距會一起預覽使用此來源的配置。'}</p><details class="gi-delete-section"><summary>刪除${binding?'配置':'來源'}</summary><button type="button" id="gridObjectDelete" class="btn gi-delete" aria-label="刪除${binding?'配置':'來源'}">刪除</button></details></footer></section>`;
    s.node=pane.querySelector('#gridInlineInspector');
    $(s,'gridObjectOpen').onclick=()=>openFull(s);
    $(s,'gridObjectNewBinding')?.addEventListener('click',()=>{if(!s.busy)workspace.createBinding(s.object.id);});
    $(s,'gridObjectDelete').onclick=()=>{if(current(s)&&!s.busy)deleteObject(s.object.kind,s.object.id);};
    $(s,'giPreview')?.addEventListener('click',()=>operation(s,()=>binding?saveBinding(s):saveSource(s)));
    if(binding)bindBinding(s);
    else {syncSourceDraft(s);for(const n of pane.querySelectorAll('#giName,#giUStep,#giVStep'))n.addEventListener('input',()=>{syncSourceDraft(s);status(s,'草稿尚未保存。預覽後確認，才會更新場景。');});}
  }
  function syncSourceDraft(s) {
    const create=$(s,'gridObjectNewBinding');if(!create)return;
    const dirty=$(s,'giName').value.trim()!==s.object.name || axes.some(a=>{
      const field=$(s,'gi'+a.toUpperCase()+'Step');return field && field.value.trim()!==String(s.object[a+'Definition'].step);
    });
    create.disabled=dirty||!hasCells(s.object);create.title=dirty?'請先預覽並保存來源變更，再建立配置。':hasCells(s.object)?'':'配置格子需要雙軸，請在完整工作區設定。';
  }
  function refreshCatalog(s) {
    if(!s.binding || s.catalogKey===catalogKey())return;
    s.catalogKey=catalogKey();s.systems=structuredClone(oc.gridSystems || []);s.boundaries=structuredClone((oc.faces || []).filter(b=>b.kind==='boundary'));
    const selectedSource=$(s,'giSystem').value,selectedBoundary=$(s,'giBoundary').value;
    $(s,'giSystem').innerHTML=sourceOptions(s,selectedSource);$(s,'giBoundary').innerHTML=boundaryOptions(s,selectedBoundary);
    const latest=s.systems.find(o=>String(o.id)===selectedSource);
    if(latest && sourceKey(latest)!==sourceKey(s.source)){
      s.source=structuredClone(latest);updateSourceSummary(s);status(s,'來源已更新；草稿頂點、格子與比例已保留，請重新預覽。');
    }
  }
  function sourceOptions(s,id) {
    const list=s.systems.filter(isInfinite),missing=!list.some(o=>String(o.id)===String(id));
    return (missing?`<option selected disabled value="${esc(id)}">來源 ${esc(id)} · 已移除</option>`:'')+list.map(o=>`<option value="${o.id}"${String(o.id)===String(id)?' selected':''}${hasCells(o)?'':' disabled'}>${esc(o.name)}${hasCells(o)?'':' · 需要雙軸'}</option>`).join('');
  }
  function boundaryOptions(s,id) {
    return (!s.boundaries.some(o=>String(o.id)===String(id))?`<option selected disabled value="${esc(id)}">面 ${esc(id)} · 已移除</option>`:'')+s.boundaries.map(o=>`<option value="${o.id}"${String(o.id)===String(id)?' selected':''}>面 ${o.id}${o.placed?'':' · 尚未放置'}</option>`).join('');
  }
  function updateSourceSummary(s) {$(s,'giSourceSummary').textContent=axes.map(a=>a+' '+definitionText(s.source?.[a+'Definition'])).join(' ／ ');}
  function sourceForm(s) {
    const o=s.object,legacy=!isInfinite(o);
    const axisField=a=>{const d=o[a+'Definition'],id='gi'+a.toUpperCase()+'Step';return `<label class="gi-axis-field"><span>${a==='u'?'X / u →':'Y / v ↓'} 間距</span>${d?.source==='repeat'?`<span class="gi-unit-input"><input id="${id}" type="number" min="1" max="100000000" step="1" value="${d.step}"${d.parameterRefs?.step?' readonly aria-readonly="true"':''}><span>mm</span></span><small>第 0 線座標 ${d.phase} mm${d.stagger?` · 相鄰格子相位差 ${d.stagger} mm`:''}${d.parameterRefs?.step?' · 引用參數，於完整工作區改綁':''}</small>`:`<span class="gi-readonly">${esc(definitionText(d))}</span><small>在完整工作區調整排法</small>`}</label>`;};
    if(legacy)return `<div class="gi-content gi-source-content"><section class="gi-section"><h3>舊版有限網格</h3><p class="gi-help">保留原有條數與座標，開啟完整工作區繼續編輯。</p></section>${axes.map(a=>`<section class="gi-section"><h3>${a} 軸</h3><p>${esc(definitionText(o[a+'Definition']))}</p></section>`).join('')}</div>`;
    return `<div class="gi-content gi-source-content"><section class="gi-section"><label>名稱<input id="giName" value="${esc(o.name)}" autocomplete="off"></label><p class="gi-help">${(oc.gridBindings || []).filter(b=>b.system===o.id).length} 個配置使用此來源 · 格線向兩端無限延伸</p></section><section class="gi-section gi-spacing">${axes.map(axisField).join('')}</section><section class="gi-section gi-source-submit"><div class="gi-source-rule">固定規則，持續重複<small>主支方向：${o.mainAlong ? '沿 '+o.mainAlong : '未設定'}；排法與基準可在完整工作區調整。</small></div><button type="button" id="giPreview" class="primary-button">預覽變更</button></section></div>`;
  }
  function bindingForm(s) {
    return `<div class="gi-content gi-binding-content"><section class="gi-section gi-references"><label>網格來源<select id="giSystem">${sourceOptions(s,s.object.system)}</select></label><label>邊界<select id="giBoundary">${boundaryOptions(s,s.object.boundary)}</select></label><p id="giSourceSummary" class="gi-help"></p></section><section class="gi-section gi-alignment"><div class="gi-vertex-pane"><label>對齊頂點<select id="giVertex"><option value="">讀取實際頂點…</option></select></label><svg id="giBoundaryView" viewBox="0 0 220 100" role="group" aria-label="點選邊界實際頂點"></svg></div><div class="gi-anchor-pane"><h3>格內位置</h3><svg id="giAnchorView" viewBox="0 0 100 100" role="group" aria-label="同一格內的九個對齊位置"></svg><p id="giAnchorSummary" class="gi-help"></p></div></section><section class="gi-section gi-cell"><h3>對齊格子 <span>u →　v ↓</span></h3><div class="gi-cell-fields"><label>cell i<input id="giCellI" type="text" inputmode="numeric" autocomplete="off" value="${esc(s.object.cell[0])}"></label><label>cell j<input id="giCellJ" type="text" inputmode="numeric" autocomplete="off" value="${esc(s.object.cell[1])}"></label></div><p class="gi-help">可輸入正、負整數索引</p><button type="button" id="giPreview" class="primary-button">預覽變更</button></section></div>`;
  }
  function bindBinding(s) {
    updateSourceSummary(s);
    $(s,'giSystem').onchange=()=>{s.source=structuredClone(s.systems.find(o=>o.id===Number($(s,'giSystem').value)));updateSourceSummary(s);status(s,'來源草稿已改變；預覽會檢查所有既有套用。');};
    $(s,'giBoundary').onchange=()=>loadBoundary(s,Number($(s,'giBoundary').value),false);
    $(s,'giVertex').onchange=()=>{s.vertex=s.vertices.find(v=>vertexId(v)===$(s,'giVertex').value)||null;drawBoundary(s);alignmentStatus(s);};
    for(const id of ['giCellI','giCellJ'])$(s,id).oninput=()=>alignmentStatus(s);
    drawAnchor(s);loadBoundary(s,s.object.boundary,true);
  }
  async function loadBoundary(s,id,restore) {
    const ticket=++s.loadSerial;s.boundary=null;s.vertex=null;s.vertices=[];
    $(s,'giVertex').innerHTML='<option value="">讀取實際頂點…</option>';drawBoundary(s);
    try {
      const b=await apiRequest('boundary '+id);
      if(!current(s)||ticket!==s.loadSerial)return;
      if(!b.ok||!b.loops?.length)throw Error(b.error||'無法讀取邊界。');
      s.boundary=b;s.boundaryId=id;
      s.vertices=b.loops.flatMap((loop,li)=>(loop.vertices || loop.verts.map((uv,index)=>({index,key:null,uv}))).map(v=>({...v,loop:loop.loop??li-1})));
      $(s,'giVertex').innerHTML='<option value="">選擇圖中的頂點</option>'+s.vertices.map(v=>`<option value="${vertexId(v)}">${vertexTitle(v)} (${v.uv.join(', ')})</option>`).join('');
      if(restore)s.vertex=s.vertices.find(v=>v.key===s.object.vertexKey)||null;
      $(s,'giVertex').value=s.vertex?vertexId(s.vertex):'';drawBoundary(s);alignmentStatus(s);
    } catch(e) {if(current(s)&&ticket===s.loadSerial)status(s,e.message,true);}
  }
  function activate(node,fn) {
    node.addEventListener('click',fn);node.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();fn(e);}});
  }
  function drawBoundary(s) {
    const view=$(s,'giBoundaryView'),focusedVertex=view.contains(document.activeElement)?document.activeElement.getAttribute('data-gi-vertex'):null;view.replaceChildren();if(!s.boundary)return;
    const points=s.boundary.loops.flatMap(l=>l.verts),xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
    const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
    const scale=Math.min(184/Math.max(1,maxX-minX),66/Math.max(1,maxY-minY));
    const point=p=>[110+(p[0]-(minX+maxX)/2)*scale,50+(p[1]-(minY+maxY)/2)*scale];
    svg('path',{d:s.boundary.loops.map(l=>l.verts.map((p,i)=>(i?'L':'M')+point(p).join(' ')).join(' ')+' Z').join(' '),class:'gi-boundary-shape','fill-rule':'evenodd'},view);
    for(const v of s.vertices){const p=point(v.uv),selected=s.vertex&&vertexId(v)===vertexId(s.vertex);
      const g=svg('g',{'data-gi-vertex':vertexId(v),'data-vertex-key':v.key??'',role:'button',tabindex:0,'aria-label':`${vertexTitle(v)}，座標 ${v.uv.join(', ')}`,'aria-pressed':String(!!selected),class:'gi-vertex-point'},view);
      svg('circle',{cx:p[0],cy:p[1],r:11,class:'gi-hit'},g);svg('circle',{cx:p[0],cy:p[1],r:selected?5:3.3,class:'gi-vertex-dot'},g);
      if(selected){const t=svg('text',{x:Math.max(9,Math.min(165,p[0]+9)),y:p[1]<25?p[1]+16:p[1]-8,class:'gi-vertex-label'},view);t.textContent='頂點 '+(v.index+1);}
      activate(g,()=>{if(!current(s)||s.busy)return;s.vertex=v;$(s,'giVertex').value=vertexId(v);drawBoundary(s);alignmentStatus(s);});
    }
    if(focusedVertex!=null)Array.from(view.querySelectorAll('[data-gi-vertex]')).find(node=>node.getAttribute('data-gi-vertex')===focusedVertex)?.focus({preventScroll:true});
  }
  function drawAnchor(s) {
    const view=$(s,'giAnchorView'),focusedAnchor=view.contains(document.activeElement)?document.activeElement.getAttribute('data-gi-anchor'):null;view.replaceChildren();
    svg('rect',{x:14,y:14,width:72,height:72,rx:2,class:'gi-anchor-cell'},view);
    svg('path',{d:'M50 14V86M14 50H86',class:'gi-anchor-midlines'},view);
    let selectedTitle=null;
    for(const position of GridAnchorPositions.positions){const {u,v,name}=position;
      const selected=GridAnchorPositions.selected(position,s.anchor);
      if(selected)selectedTitle=name;
      const g=svg('g',{'data-gi-anchor':u+','+v,role:'button',tabindex:0,'aria-label':name,'aria-pressed':String(selected),class:'gi-anchor-point'},view);
      svg('circle',{cx:14+36*u,cy:14+36*v,r:13,class:'gi-hit'},g);svg('circle',{cx:14+36*u,cy:14+36*v,r:selected?5.5:3.5,class:'gi-anchor-dot'},g);
      activate(g,()=>{if(!current(s)||s.busy)return;s.anchor=GridAnchorPositions.fractions(position);drawAnchor(s);alignmentStatus(s);});
    }
    $(s,'giAnchorSummary').textContent=(selectedTitle||'自訂比例')+' · '+s.anchor.map(a=>a.num+'/'+a.den).join(', ');
    if(focusedAnchor!=null)Array.from(view.querySelectorAll('[data-gi-anchor]')).find(node=>node.getAttribute('data-gi-anchor')===focusedAnchor)?.focus({preventScroll:true});
  }
  function alignmentStatus(s) {
    status(s,s.vertex?`${vertexTitle(s.vertex)} (${s.vertex.uv.join(', ')}) ↔ cell (${$(s,'giCellI').value}, ${$(s,'giCellJ').value})；格內 ${$(s,'giAnchorSummary').textContent}`:'請從縮圖或清單選擇一個實際頂點。');
  }
  function signed(s,id,title) {
    const node=$(s,id),raw=node.value.trim();
    if(!/^-?\d+$/.test(raw)){node.focus();throw Error(title+'請輸入整數索引。');}
    const n=BigInt(raw);
    if(n < -9223372036854775808n || n > 9223372036854775806n){node.focus();throw Error(title+'超出可建立格子的索引範圍。');}
    return n.toString();
  }
  async function stillSame(s) {
    if(!current(s))throw Error('目前專案或選取已切換，請重新選取物件。');
    const objects=await apiRequest('objects');
    if(!current(s))throw Error('目前專案或選取已切換，請重新選取物件。');
    if(!objects.ok)throw Error(objects.error||'無法核對目前場景。');
    const list=s.binding?objects.gridBindings:objects.gridSystems;
    if(objectKey(list?.find(o=>o.id===s.object.id))!==s.key)throw Error('此物件已更新，請重新選取後再編輯。');
    if(s.source && sourceKey(objects.gridSystems.find(o=>o.id===s.source.id))!==sourceKey(s.source))throw Error('網格來源已更新，請重新選取後再編輯。');
    if(s.binding){const b=await apiRequest('boundary '+s.boundaryId);if(!current(s))throw Error('目前選取已切換。');if(!b.ok||b.geometryFingerprint!==s.boundary.geometryFingerprint)throw Error('邊界頂點已更新，請重新選取邊界後再編輯。');}
  }
  async function saveSource(s) {
    const name=$(s,'giName').value.trim(),bytes=new TextEncoder().encode(name);
    if(!bytes.length || bytes.length>96 || /[\u0000-\u001f\u007f]/.test(name))throw Error('名稱需為 1–96 個 UTF-8 位元組，且不可包含控制字元。');
    const parts=axes.map(a=>{const d=s.object[a+'Definition'],token=(key,value=d[key])=>{const r=d.parameterRefs?.[key];return r?`param:${r.parameterId}:${r.fieldId}`:value;};if(d.source==='none')return a+' none';if(d.source==='repeat-panel')return `${a} repeat-panel ${token('panel')} gap ${token('gap')} from ${token('anchor')}`;if(d.source!=='repeat')throw Error('此排法請在完整工作區編輯。');const raw=$(s,'gi'+a.toUpperCase()+'Step').value.trim(),step=Number(raw);if(!/^\d+$/.test(raw)||!Number.isSafeInteger(step)||step<1||step>100000000)throw Error(a+' 間距須為 1 至 100000000 mm 的整數。');return `${a} repeat ${token('phase')} ${token('step',step)}`;});
    const hex=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
    await stillSame(s);
    await commit(s,`grid-system ${s.object.id} name-hex ${hex} main-along ${s.object.mainAlong||'none'} ${parts.join(' ')}`,'更新網格來源「'+name+'」');
  }
  async function saveBinding(s) {
    if(!s.source||!hasCells(s.source))throw Error('網格配置需要兩軸皆有定義的來源。');
    if(!s.boundary||!s.vertex)throw Error('請選擇邊界與一個實際頂點。');
    const i=signed(s,'giCellI','cell i'),j=signed(s,'giCellJ','cell j'),v=s.vertex;
    const vertex=v.key!=null?`vertex-key ${v.key}`:`vertex ${v.loop<0?'outer '+v.index:'hole '+v.loop+' '+v.index} geometry-hash ${s.boundary.geometryFingerprint}`;
    const line=`grid-binding ${s.object.id} on-boundary ${s.boundaryId} from-system ${s.source.id} ${vertex} cell ${i} ${j} anchor ${s.anchor.flatMap(a=>[a.num,a.den]).join(' ')}`;
    await stillSame(s);await commit(s,line,`更新配置 ${s.object.id}：${vertexTitle(v)} ↔ cell (${i}, ${j})`);
  }
  async function commit(s,line,title) {
    status(s,'正在預覽連動結果，場景尚未改動…');
    const result=await apiRequest('line preview '+line);
    if(!current(s)){if(result.preview)await apiRequest('line cancel-preview');return;}
    if(!result.preview)throw Error(result.error||'無法取得變更預覽。');
    const done=confirmReferenceImpact(result.preview),dialog=document.querySelector('dialog.reference-impact:last-of-type');
    if(dialog){const p=document.createElement('p');p.className='ig-impact-title';p.textContent=title;dialog.querySelector('h2')?.after(p);
      const code=dialog.querySelector(':scope > code');if(code){const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='進階：完整指令';details.append(summary);code.replaceWith(details);details.append(code);}
      dialog.querySelector('#impact-confirm')?.addEventListener('click',event=>{if(current(s))return;event.preventDefault();event.stopImmediatePropagation();dialog.querySelector('.impact-actions button')?.click();},{capture:true});
    }
    const response=await done;if(!response.ok){status(s,response.error||'未套用',true);return;}
    if(!current(s))return;
    await renderObjects();
    if(active?.object.id===s.object.id && active.object.kind===s.object.kind)status(active,'變更已保存。可使用復原或重做。');
  }
  async function operation(s,run) {
    if(!current(s)||s.busy||oc.busy)return;
    s.busy=true;oc.busy=true;s.pane.classList.add('gi-busy');
    const controls=[...s.pane.querySelectorAll('button,input,select')].map(n=>[n,n.disabled]);controls.forEach(([n])=>n.disabled=true);
    try{await run();}catch(e){status(s,e.message,true);}
    finally{s.busy=false;oc.busy=false;s.pane.classList.remove('gi-busy');if(current(s)){controls.forEach(([n,disabled])=>n.disabled=disabled);if(!s.binding)syncSourceDraft(s);}}
  }
  function disposeInspector() {if(active){++active.loadSerial;active=null;}}
  workspace.renderInspector=renderInspector;workspace.disposeInspector=disposeInspector;
})();
