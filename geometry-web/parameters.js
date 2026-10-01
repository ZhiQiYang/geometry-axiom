/* D31: all effective values and candidate validation come from the native core. */
window.ParameterUI = (() => {
  'use strict';
  const esc = ReferenceWorkspace.escape, clone = x => structuredClone(x);
  const $ = id => document.getElementById(id);
  let state = null, serial = 0, timer = null;
  const cards = () => (oc.parameters || []).map(o => o.card);
  const current = s => state === s && s.context === ReferenceWorkspace.context();
  const types = [['dimension','尺寸 mm'],['count','數量'],['ratio','比例']];
  function value(v) {
    if (!v || v.den === '0') return '待試算';
    let text = v.num;
    if (v.den !== '1') {
      const n = BigInt(v.num), d = BigInt(v.den); let reduced=d;
      while(reduced%2n===0n)reduced/=2n;while(reduced%5n===0n)reduced/=5n;
      if(reduced===1n){let rest=(n<0n?-n:n)%d; text=(n<0n?'-':'')+(n<0n?-n:n)/d+'.';while(rest){rest*=10n;text+=rest/d;rest%=d;}}
      else text=v.num+'/'+v.den;
    }
    return text+(v.unit==='mm'?' mm':'');
  }
  function sourceLabel(ref, catalog=cards()) {
    const c=catalog.find(c=>c.id===ref.parameterId),f=c?.fields.find(f=>f.id===ref.fieldId);
    return `${c?.name || '遺失卡片'}.${f?.name || '遺失欄位'} · #${ref.parameterId}:${ref.fieldId}`;
  }
  const refToken = ref => `⟦${sourceLabel(ref,state?.card?.fields?[...cards().filter(c=>c.id!==state.card.id),state.card]:cards()).replaceAll('⟦','[').replaceAll('⟧',']')}⟧`;
  function expression(a) {
    if(a.op==='ref')return refToken(a);
    if(a.op==='literal')return a.den==='1'?a.num+(a.unit==='mm'?' mm':''):`(${a.num}${a.unit==='mm'?' mm':''} / ${a.den})`;
    if(a.op==='neg')return `-(${expression(a.left)})`;
    return `(${expression(a.left)} ${{add:'+',sub:'−',mul:'×',div:'÷'}[a.op]} ${expression(a.right)})`;
  }
  const inputText = f => f.expression?.op==='literal' ? `${f.expression.num}${f.expression.den==='1'?'':'/'+f.expression.den}` : '='+expression(f.expression);
  const coreText = text => text.replaceAll('＝','=').replaceAll('−','-').replaceAll('×','*').replaceAll('÷','/').replace(/⟦[^⟦⟧]*#(\d+):(\d+)⟧/g,'@$1:$2');
  function options({dimensions=false,catalog=cards()}={}) {
    return catalog.flatMap(c=>c.fields.filter(f=>!dimensions||f.type==='dimension').map(f=>({ref:{kind:'parameter',parameterId:c.id,fieldId:f.id},text:`${sourceLabel({parameterId:c.id,fieldId:f.id},catalog)} · ${value(f.value)}`})));
  }
  function sourceControl(id,ref,dimension=true) {
    const key=ref?`${ref.parameterId}:${ref.fieldId}`:'';
    return `<span class="param-source"><select id="${id}Source" aria-label="引用來源"><option value="">直接輸入</option>${options({dimensions:dimension}).map(o=>`<option value="${o.ref.parameterId}:${o.ref.fieldId}"${key===o.ref.parameterId+':'+o.ref.fieldId?' selected':''}>${esc(o.text)}</option>`).join('')}</select><button type="button" class="param-jump btn" data-param-jump-for="${id}Source"${ref?'':' hidden'}>查看來源</button></span>`;
  }
  function sourceRef(id) {
    const key=$(id+'Source')?.value;if(!key)return null;const [parameterId,fieldId]=key.split(':').map(Number);return {kind:'parameter',parameterId,fieldId};
  }
  function bindSource(id,onChange) {
    const select=$(id+'Source'),input=$(id);if(!select||!input)return;
    const sync=()=>{const ref=sourceRef(id);input.readOnly=!!ref;input.setAttribute('aria-readonly',String(!!ref));const jump=document.querySelector(`[data-param-jump-for="${id}Source"]`);if(jump)jump.hidden=!ref;
      if(ref){const f=cards().find(c=>c.id===ref.parameterId)?.fields.find(f=>f.id===ref.fieldId);input.value=f?.value?.den==='1'?f.value.num:'';}
    };
    sync();select.addEventListener('change',()=>{sync();onChange?.();});
  }
  function definition(c) {return {id:c.id,name:c.name,nextFieldId:c.nextFieldId,fields:c.fields.map(({id,name,type,expression})=>({id,name,type,expression}))};}
  function refs(ast,result=[]) {if(ast?.op==='ref')result.push(ast);if(ast?.left)refs(ast.left,result);if(ast?.right)refs(ast.right,result);return result;}
  function usage(id) {
    const uses=[];
    for(const c of cards())for(const f of c.fields)if(refs(f.expression).some(r=>r.parameterId===id))uses.push({kind:'parameter',id:c.id,label:`${c.name}.${f.name}`});
    for(const g of oc.gridSystems)for(const a of ['u','v'])for(const [field,r] of Object.entries(g[a+'Definition']?.parameterRefs||{}))if(r.parameterId===id)uses.push({kind:'grid-system',id:g.id,label:`${g.name} · ${a} ${field}`});
    for(const use of oc.parameterUses||[])if(use.parameterId===id)uses.push(use);
    return uses;
  }
  function svgCard(o) {
    const short=(text,n)=>{const chars=Array.from(text);return chars.length>n?chars.slice(0,n-1).join('')+'…':text;};
    const label=(attrs,text,n)=>{const node=el('text',attrs,g);node.textContent=short(text,n);el('title',{},node).textContent=text;};
    const g=el('g',{class:'ocard parameter-card','data-kind':'parameter','data-id':o.id,transform:`translate(${o.cx},${o.cy})`,cursor:'pointer'});
    g.classList.toggle('selected',ocSelected('parameter',o.id));
    el('rect',{width:OC_W,height:OC_H,rx:12,fill:'#fff',stroke:'#c8c8e4','stroke-width':1.5},g);
    el('rect',{width:OC_W,height:38,rx:12,fill:'#efedf9'},g);
    label({x:14,y:25,fill:'#4f4581','font-size':14,'font-weight':600},'ƒ  '+o.name,17);
    o.card.fields.slice(0,4).forEach((f,i)=>{label({x:14,y:65+i*27,'font-size':13,fill:'#34425a'},f.name,8);label({x:OC_W-14,y:65+i*27,'text-anchor':'end','font-size':13,fill:'#4f4581'},value(f.value),16);});
    el('text',{x:14,y:OC_H-13,'font-size':11,fill:'#667085'},g).textContent=`${o.card.fields.length} 個欄位 · ${usage(o.id).length} 處使用`;
    return g;
  }
  function status(text,error=false) {const n=$('paramStatus');if(n){n.textContent=text;n.classList.toggle('param-error',error);}}
  function invalidate(s) {
    if(!current(s))return;s.changed=true;s.generation++;if(s.preview)EngineeringAdapter.cancel({token:s.preview.token}).catch(()=>{});s.preview=null;
    $('paramConfirm')?.setAttribute('disabled','');clearTimeout(timer);timer=setTimeout(()=>preview(s,true),450);
  }
  function capture(s) {
    const root=$('parameterEditor');if(!root||!current(s))return;
    s.card.name=$('paramName').value;
    for(const row of root.querySelectorAll('[data-param-field]')){
      const f=s.card.fields.find(f=>f.id===Number(row.dataset.paramField));
      f.name=row.querySelector('[data-name]').value;f.type=row.querySelector('[data-type]').value;f.input=row.querySelector('[data-input]').value;
    }
  }
  function buildOperation(s) {capture(s);return {op:'put-parameter',value:{id:s.card.id,name:s.card.name,nextFieldId:s.card.nextFieldId,fields:s.card.fields.map(f=>({id:f.id,name:f.name,type:f.type,input:coreText(f.input)}))}};}
  function showPreview(s,p) {
    if(!current(s)||!$('paramResult'))return;
    const before=new Map((p.before.parameters||[]).map(c=>[c.id,c]));
    const changes=(p.after.parameters||[]).flatMap(c=>c.fields.filter(f=>JSON.stringify(f)!==JSON.stringify(before.get(c.id)?.fields.find(x=>x.id===f.id))).map(f=>`<li>${esc(c.name+'.'+f.name)}：${esc(value(before.get(c.id)?.fields.find(x=>x.id===f.id)?.value))} → <strong>${esc(value(f.value))}</strong></li>`));
    for(const b of p.after.assembly?.bindings||[]){const old=p.before.assembly?.bindings.find(x=>x.value.id===b.value.id);
      for(const slot of b.effective)for(const axis of ['A','B']){const prior=old?.effective.find(x=>x.slotId===slot.slotId)?.[axis]?.value,now=slot[axis]?.value;
        if(prior!==now)changes.push(`<li>組構配置 ${b.value.id} 槽位 ${slot.slotId}.${axis}：${prior??'未設定'} → <strong>${now??'未設定'} mm</strong></li>`);}}
    const after=new Map((p.after.parameters||[]).map(c=>[c.id,c]));
    for(const c of before.values()){
      const next=after.get(c.id);
      if(next&&next.name!==c.name)changes.push(`<li>卡片名稱：${esc(c.name)} → ${esc(next.name)}</li>`);
      for(const f of c.fields)if(!next?.fields.some(n=>n.id===f.id))changes.push(`<li>刪除 ${esc(c.name+'.'+f.name)}：${esc(value(f.value))} → 刪除</li>`);
    }
    const geometry=['gridSystems','grids','guides','datums','timbers'].flatMap(kind=>(p.after[kind]||[]).filter(o=>JSON.stringify(o)!==JSON.stringify((p.before[kind]||[]).find(b=>b.id===o.id))).map(o=>`${{gridSystems:'網格來源',grids:'網格',guides:'參考線',datums:'基準面',timbers:'角材'}[kind]} ${o.id}`));
    $('paramResult').innerHTML=p.valid?`<h3>變更預覽</h3><ul>${changes.join('')||'<li>欄位有效值未改變</li>'}</ul><p>受影響物件：${esc(geometry.join('、')||'尚無幾何變更')}</p>`:`<p class="param-error">${esc(p.diagnostics.map(d=>d.message||d).join('\n'))}</p>`;
    if(p.valid){const uses=usage(s.card.id);if(uses.length){const row=document.createElement('p');row.textContent='直接使用處：'+uses.map(u=>u.label).join('、');$('paramResult').appendChild(row);}}
    $('paramConfirm').disabled=!p.valid;status(p.valid?'試算完成，確認後整筆套用。':'未套用：請修正欄位或引用。',!p.valid);
  }
  async function preview(s,quiet=false,operations=null) {
    if(!current(s)||s.busy)return;
    clearTimeout(timer);
    if(operations)s.generation++;
    if(s.preview)EngineeringAdapter.cancel({token:s.preview.token}).catch(()=>{});
    s.preview=null;$('paramConfirm')?.setAttribute('disabled','');
    const generation=s.generation,request=++serial;
    try{
      const ops=operations||[buildOperation(s)];
      const read=await apiRequest('engineering-read');if(!read.ok)throw Error(read.error);
      if(!current(s)||generation!==s.generation||request!==serial)return;
      if(s.fresh&&read.state.parameters.some(c=>c.id===s.card.id))throw Error('卡片編號已被其他操作使用，請捨棄草稿並重新建立。');
      if(!s.fresh&&JSON.stringify(definition(read.state.parameters.find(c=>c.id===s.card.id)||{fields:[]}))!==s.base)throw Error('參數已由其他操作變更，請捨棄草稿並重新開啟。');
      const p=await EngineeringAdapter.preview({operations:ops,expectedRevision:read.revision});
      if(!current(s)||generation!==s.generation||request!==serial){EngineeringAdapter.cancel({token:p.token}).catch(()=>{});return;}
      s.preview=p;s.operations=ops;showPreview(s,p);
    }catch(e){if(current(s)&&request===serial){status(e.message,true);if(!quiet)$('paramStatus')?.scrollIntoView({block:'nearest'});}}
  }
  async function confirm(s) {
    if(!current(s)||s.busy||!s.preview?.valid)return;
    s.busy=true;const p=s.preview;status('正在套用…');
    try{
      const id=s.card.id,context=s.context;
      await EngineeringAdapter.confirm({token:p.token});if(state!==s||context!==ReferenceWorkspace.context())return;
      state=null;oc.parameterCreating=false;clearTimeout(timer);await renderObjects();
      if(ocFind('parameter',id)){selectObject('parameter',id);centerOnNode('parameter',id);}else renderInspector();
      toast('參數與引用物件已整筆更新，可復原。','success');
    }catch(e){if(current(s)){s.preview=null;status(e.message,true);$('paramConfirm').disabled=true;}}
    finally{s.busy=false;}
  }
  function render(pane,object=null) {
    if(state?.legacyOnly&&current(state)&&pane.querySelector('#parameterEditor'))return;
    if(state&&current(state)&&state.card.id===(object?.id??state.card.id)&&pane.querySelector('#parameterEditor'))return;
    if(!state||!current(state)||object&&state.card.id!==object.id){
      if(!object)return;const c=object.card;state={context:ReferenceWorkspace.context(),card:{...clone(c),fields:c.fields.map(f=>({...clone(f),input:inputText(f)}))},base:JSON.stringify(definition(c)),fresh:false,changed:false,generation:0,busy:false,preview:null};
    }
    const s=state,c=s.card;
    pane.innerHTML=`<section id="parameterEditor" class="parameter-editor"><h2>${s.fresh?'建立參數':'參數卡'}</h2><label>名稱<input id="paramName" value="${esc(c.name)}"></label>${s.fresh?'<label>範本<select id="paramTemplate"><option value="single">單值</option><option value="panel">寬 × 長</option><option value="section">W × H</option></select></label><label>快速輸入<input id="paramQuick" placeholder="(915,1830) 或 W27H33"><button type="button" class="btn" id="paramParse">轉成欄位草稿</button></label>':''}<div id="paramFields">${c.fields.map(f=>`<fieldset data-param-field="${f.id}"><legend>欄位 ${esc(f.name)}</legend><div class="param-pair"><label>欄位名稱<input data-name value="${esc(f.name)}"></label><label>種類<select data-type>${types.map(([v,t])=>`<option value="${v}"${f.type===v?' selected':''}>${t}</option>`).join('')}</select></label></div><label>數值或算式<input data-input value="${esc(f.input)}" autocomplete="off" spellcheck="false"></label><div class="param-pair"><label>插入引用<select data-insert><option value="">選擇來源</option>${options({catalog:[...cards().filter(x=>x.id!==c.id),{...c,fields:c.fields.map(f=>({...f,value:null}))}]}).map(o=>`<option value="${o.ref.parameterId}:${o.ref.fieldId}">${esc(o.text)}</option>`).join('')}</select></label><div class="param-field-actions"><button type="button" class="btn" data-up aria-label="上移欄位">↑</button><button type="button" class="btn" data-remove>移除</button></div></div></fieldset>`).join('')}</div><button type="button" class="btn" id="paramAdd">＋ 欄位</button><p class="param-help">直接填尺寸可用小數或分數。算式以 = 開頭，尺寸常數加 mm；引用由選單插入。</p><div id="paramResult" aria-live="polite"></div><p id="paramStatus" role="status">${s.changed?'草稿尚未套用。':'修改欄位後可試算並預覽影響。'}</p><div class="param-pair"><button class="btn" id="paramPreview">重新試算</button><button class="primary-button" id="paramConfirm" disabled>確認套用</button></div><button class="btn" id="paramDiscard">${s.fresh?'捨棄草稿':'還原未套用修改'}</button>${!s.fresh?`<details><summary>使用關係與交換</summary><ul>${usage(c.id).map(u=>`<li><button class="btn" data-param-use="${u.kind}:${u.id}">${esc(u.label)}</button></li>`).join('')||'<li>尚未被其他物件引用</li>'}</ul><button class="btn" id="paramExport">匯出參數包</button><button class="btn danger" id="paramDelete">預覽刪除卡片</button></details>`:''}<details><summary>匯入參數包／既有具名規格</summary><button type="button" class="btn" id="paramImport">匯入參數包</button><input type="file" id="paramFile" accept=".json" hidden><div id="paramLegacy"></div></details></section>`;
    pane.querySelectorAll('#paramName,[data-name],[data-type],[data-input]').forEach(n=>n.addEventListener('input',()=>{capture(s);invalidate(s);}));
    for(const row of pane.querySelectorAll('[data-param-field]')){
      const id=Number(row.dataset.paramField);
      row.querySelector('[data-insert]').onchange=e=>{if(!e.target.value)return;const [parameterId,fieldId]=e.target.value.split(':').map(Number),input=row.querySelector('[data-input]');let v=input.value;if(!v.startsWith('='))v='=';input.value=v+refToken({parameterId,fieldId});e.target.value='';capture(s);invalidate(s);input.focus();};
      row.querySelector('[data-remove]').onclick=()=>{if(c.fields.length===1){status('卡片至少保留一個欄位。',true);return;}capture(s);c.fields=c.fields.filter(f=>f.id!==id);rerender(s);};
      row.querySelector('[data-up]').onclick=()=>{capture(s);const i=c.fields.findIndex(f=>f.id===id);if(i>0)[c.fields[i-1],c.fields[i]]=[c.fields[i],c.fields[i-1]];rerender(s);};
    }
    $('paramAdd').onclick=()=>{capture(s);if(c.fields.length>=16||!c.nextFieldId){status('欄位容量已滿。',true);return;}c.fields.push({id:c.nextFieldId++,name:'欄位 '+c.nextFieldId,type:'dimension',input:'0'});rerender(s);};
    $('paramPreview').onclick=()=>preview(s);$('paramConfirm').onclick=()=>confirm(s);$('paramDiscard').onclick=()=>discard(s);
    $('paramTemplate')?.addEventListener('change',e=>template(s,e.target.value));
    $('paramParse')?.addEventListener('click',()=>{const text=$('paramQuick').value.trim(),pair=text.match(/^\(\s*([+\-\d./]+)\s*,\s*([+\-\d./]+)\s*\)$/),wh=text.match(/^W\s*([+\-\d./]+)\s*H\s*([+\-\d./]+)$/i);if(!pair&&!wh){status('請輸入 (915,1830) 或 W27H33。',true);return;}template(s,wh?'section':'panel',(pair||wh).slice(1));});
    $('paramExport')?.addEventListener('click',()=>exportPackage([c.id]));
    $('paramDelete')?.addEventListener('click',()=>{s.changed=true;preview(s,false,[{op:'delete-parameter',id:c.id}]);});
    $('paramImport').onclick=()=>$('paramFile').click();$('paramFile').onchange=async e=>{try{const file=e.target.files[0];if(!file)return;if(file.size>1024*1024)throw Error('參數包超過 1 MB。');const pkg=JSON.parse(await file.text());if(!current(s))return;s.changed=true;preview(s,false,[{op:'import-parameters',value:pkg}]);}catch(e){status(e.message,true);}};
    pane.querySelectorAll('[data-param-use]').forEach(b=>b.onclick=()=>{const [kind,id]=b.dataset.paramUse.split(':');jump(kind,Number(id));});
    loadLegacy(s);if(s.preview)showPreview(s,s.preview);
  }
  function rerender(s) {const pane=$('parameterEditor')?.parentElement;if(!pane)return;pane.textContent='';render(pane);invalidate(s);}
  function template(s,kind,numbers=null) {
    capture(s);const names=kind==='panel'?['寬','長']:kind==='section'?['W','H']:['尺寸'];const defaults=kind==='panel'?['915','1830']:kind==='section'?['27','33']:['0'];
    s.card.fields=names.map((name,i)=>({id:s.card.nextFieldId++,name,type:'dimension',input:(numbers||defaults)[i]}));rerender(s);
  }
  function discard(s=state) {if(s?.busy)return;clearTimeout(timer);if(s?.preview)EngineeringAdapter.cancel({token:s.preview.token}).catch(()=>{});const id=s?.card.id;state=null;oc.parameterCreating=false;++serial;if(s?.fresh)ocSetSelection([]);else {const pane=$('inspectorContent');pane.textContent='';renderInspector();}return id;}
  function mayLeave() {if(!state)return true;if(state.busy)return false;if(state.changed&&!window.confirm('參數有未套用的草稿。選擇確定會捨棄，取消可繼續編輯。'))return false;discard();return true;}
  async function create() {
    if(!mayLeave())return;const context=ReferenceWorkspace.context(),support=await apiRequest('engineering-read');
    if(context!==ReferenceWorkspace.context())return;
    if(!support.ok||!support.state?.capabilities?.includes('parameters/1')){toast('目前服務尚未支援參數卡，請重新啟動更新後的服務。','error');return;}
    const ids=await apiRequest('newid');if(!ids.ok||context!==ReferenceWorkspace.context())return;
    if(oc.focus){oc.stack=[];await leaveFocus();}if(view3)await setView3(false);
    closePanels();ocSetSelection([]);oc.parameterCreating=true;state={context,card:{id:ids.parameter,name:'參數',nextFieldId:2,fields:[{id:1,name:'尺寸',type:'dimension',input:'0'}]},fresh:true,changed:true,generation:0,busy:false,preview:null};
    renderInspector();if(innerWidth<=900)openPanel('right',$('toggleRight'));$('paramName')?.focus();
  }
  async function jump(kind,id) {
    if(!mayLeave())return;
    const context=ReferenceWorkspace.context();
    try {
    if(kind==='parameter'||kind==='grid-system'||kind==='assembly-binding'){if(window.InfiniteGridWorkspace?.isOpen&&!window.InfiniteGridWorkspace.close())return;if(oc.focus){oc.stack=[];await leaveFocus();}oc.search='';$('searchInput').value='';await renderObjects();if(context!==ReferenceWorkspace.context())return;selectObject(kind,id);centerOnNode(kind,id);if(innerWidth<=900)openPanel('right',$('toggleRight'));}
    else if(kind==='datum')await openDatumManager();
    else if(kind==='guide'){
      const r=await apiRequest('references'),g=r.guides?.find(g=>g.id===id);if(!g){toast('參考線已不存在。');return;}
      await EngineeringAdapter.navigateObject({kind:'placement',id:g.surface});editReferenceGuide(id);
    }else await EngineeringAdapter.navigateObject({kind,id});
    }catch(e){if(context===ReferenceWorkspace.context())toast(e.message||'無法開啟引用來源。','error');}
  }
  async function loadLegacy(s) {
    const r=await apiRequest('references');if(!current(s)||!$('paramLegacy')||!r.ok)return;
    $('paramLegacy').innerHTML=`<label>既有具名規格<select id="paramSpec"><option value="">選擇原規格</option>${r.specs.map(x=>`<option value="${esc(x.name)}">${esc(x.name)} · ${x.value} mm</option>`).join('')}</select></label><label>數值 mm<input id="paramSpecValue" type="number" step="1"></label><button class="btn" id="paramSpecSave">預覽更新原規格</button>`;
    $('paramSpec').onchange=e=>{$('paramSpecValue').value=r.specs.find(x=>x.name===e.target.value)?.value??'';};
    $('paramSpecSave').onclick=async()=>{const name=$('paramSpec').value,raw=$('paramSpecValue').value;if(!name||!/^[-+]?\d+$/.test(raw)){status('請選規格並輸入整數 mm。',true);return;}if(s.changed){status('請先完成或捨棄參數草稿，再更新原規格。',true);return;}if(await emitLine(`spec ${name} ${raw}`)){state=null;await refreshActive();}};
  }
  async function openLegacy() {
    if(!mayLeave())return;
    const pane=oc.focus?.t==='face'?$('faceInspectorContent'):$('inspectorContent');if(!pane)return;
    state={context:ReferenceWorkspace.context(),legacyOnly:true,changed:false,busy:false,card:{id:null},generation:0};
    pane.hidden=false;pane.innerHTML='<section id="parameterEditor" class="parameter-editor"><h2>參數與具名規格</h2><button type="button" id="paramNewFromLegacy" class="btn">＋ 建立參數卡</button><div id="paramLegacy"></div><p id="paramStatus" role="status"></p><button type="button" class="btn" id="paramLegacyBack">返回物件設定</button></section>';
    $('paramNewFromLegacy').onclick=create;$('paramLegacyBack').onclick=()=>{state=null;if(oc.focus?.t==='face')renderFaceInspector();else renderInspector();};
    await loadLegacy(state);if(innerWidth<=900)openPanel('right',oc.focus?$('workspaceToggleRight'):$('toggleRight'));
  }
  function exportPackage(selected) {
    const found=new Map(),all=new Map(cards().map(c=>[c.id,c]));
    function visit(id){if(found.has(id))return;const c=all.get(id);if(!c)throw Error('缺少引用卡片，無法匯出。');found.set(id,definition(c));for(const f of c.fields)for(const r of refs(f.expression))visit(r.parameterId);}
    try{selected.forEach(visit);const blob=new Blob([JSON.stringify({schema:'geometry-parameters/1',cards:[...found.values()]},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='參數包.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);}catch(e){toast(e.message,'error');}
  }
  function relations(group,visibleKeys) {
    const drawn=new Set();
    for(const p of oc.parameters||[])for(const use of usage(p.id))for(const u of use.canvasTargets||[use]){
      if(!ocSelected('parameter',p.id)&&!ocSelected(u.kind,u.id))continue;
      if(!visibleKeys.has(`parameter:${p.id}`)||!visibleKeys.has(`${u.kind}:${u.id}`))continue;
      const key=`${p.id}:${u.kind}:${u.id}`;if(drawn.has(key))continue;drawn.add(key);
      const a=cardCenter('parameter',p.id),b=cardCenter(u.kind,u.id);if(!a||!b)continue;
      el('line',{x1:a.x,y1:a.y,x2:b.x,y2:b.y,stroke:'#8b7bb5','stroke-width':2,'stroke-dasharray':'5 4'},group);
    }
  }
  document.addEventListener('click',e=>{const b=e.target.closest('[data-param-jump-for]');if(!b)return;const [id]=$ (b.dataset.paramJumpFor).value.split(':');jump('parameter',Number(id));});
  window.addEventListener('beforeunload',e=>{if(state?.changed){e.preventDefault();e.returnValue='';}});
  window.addEventListener('geometry-definition-changed',()=>{if(state&&!state.busy){state.preview=null;state.generation++;++serial;clearTimeout(timer);if(!state.changed)state=null;else status('來源或物件已變更，請重新試算。');if($('paramConfirm'))$('paramConfirm').disabled=true;}});
  document.addEventListener('click',e=>{if(e.target.closest('#parameterSelectionExport'))exportPackage(oc.selection.filter(s=>s.kind==='parameter').map(s=>s.id));});
  window.addEventListener('project-info-changed',()=>{if(state&&!current(state)){clearTimeout(timer);state=null;oc.parameterCreating=false;++serial;}});
  $('btnNewParameter').onclick=()=>{ $('createObjectPop').hidden=true;create(); };
  return {value,sourceLabel,options,sourceControl,sourceRef,bindSource,card:svgCard,render,create,openLegacy,jump,usage,relations,mayLeave,discard,exportPackage,get pending(){return !!state&&(state.changed||state.busy);},get editingId(){return state?.card.id;}};
})();
