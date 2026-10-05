/* #48 interface adapter for the existing reference-record disclosure.
   The host owns attachment persistence and all reference/native access. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.EvidenceLinksUI=api;})(globalThis,()=>{
  'use strict';
  const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const statusText={unchecked:'尚未核對','confirmed-content':'已核對內容','needs-reassociation':'物件身分需重新指定','source-missing':'原 PDF 缺失','source-changed':'原 PDF 已換版，需重新核對','target-missing':'參數欄位缺失'};
  const valueText=v=>v?`${v.num}${v.den==='1'?'':'/'+v.den}${v.unit==='mm'?' mm':''}`:'無現行正式值';
  const typed=t=>`${t.parameterId}:${t.fieldId}`;
  function mount(host,{controller,readSelection,getStamp,canvas,filter=()=>true,locateTarget=null}){
    if(!host||!controller||typeof readSelection!=='function'||typeof getStamp!=='function')throw Error('證據介面接線不完整。');
    const doc=host.ownerDocument,section=doc.createElement('section');section.dataset.evidenceLinks='';
    section.style.cssText='min-width:0;max-width:100%;overflow-wrap:anywhere';host.append(section);
    let sequence=0,destroyed=false,selection=null,selectionIdentity=null,view=null,region=null,selecting=false,drag=null,overlay=null,busy=false;
    let form=null,targetSelect=null,model=null,message=null,list=null,save=null,start=null,cancelButton=null,regionFields=null;
    const disclosure=host.closest('details');
    const connected=()=>!destroyed&&section.isConnected&&disclosure?.open!==false;
    const stamp=()=>getStamp();
    const pageIdentity=()=>canvas?.pageIdentity?.()??null;
    const live=s=>connected()&&same(s,stamp());
    const element=(tag,text,attrs={})=>{const n=doc.createElement(tag);if(text!==null)n.textContent=text;for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);return n;};
    function tell(text){if(message)message.textContent=text;}
    function removeOverlay(){overlay?.remove();overlay=null;}
    function release(){if(drag&&canvas?.svg.hasPointerCapture?.(drag.pointerId))canvas.svg.releasePointerCapture(drag.pointerId);drag=null;}
    function resetRegion(){release();selecting=false;region=null;removeOverlay();if(save)save.disabled=true;}
    function cancel(){++sequence;controller.cancel();busy=false;resetRegion();tell('已取消，證據與正式模型保持原狀。');section.querySelectorAll('input,select,[data-evidence-locate],[data-evidence-rebind]').forEach(n=>n.disabled=false);section.querySelectorAll('[data-evidence-reviewed]').forEach(n=>{n.disabled=n.dataset.canConfirm!=='true';n.checked=view?.links.find(l=>l.evidenceId===n.dataset.evidenceReviewed)?.status==='confirmed-content';});if(cancelButton)cancelButton.disabled=false;if(start)start.disabled=!selection||!canvas;}
    function draw(rect){
      removeOverlay();if(!canvas?.svg||!rect)return;
      const layer=canvas.layer();if(!layer)return;
      const [x,y,w,h]=rect,points=[[x,y],[x+w,y],[x+w,y+h],[x,y+h]].map(p=>canvas.fromPage(p).join(','));
      overlay=doc.createElementNS('http://www.w3.org/2000/svg','polygon');overlay.dataset.evidenceRegion='';
      for(const [k,v]of Object.entries({points:points.join(' '),fill:'rgba(107,78,158,.12)',stroke:'#70549a','stroke-width':2,'vector-effect':'non-scaling-stroke','pointer-events':'none'}))overlay.setAttribute(k,v);
      layer.append(overlay);
    }
    function readTarget(select=targetSelect){return selection?.targets.find(t=>typed(t.target)===select.value)||null;}
    function updateModel(){model.textContent=valueText(readTarget()?.modelValue??null);}
    function labelInput(parent,text,key,max=2000){const label=element('label',text);label.style.cssText='display:block;min-width:0';const input=element('input',null,{'data-evidence-input':key,maxlength:max});input.style.cssText='display:block;width:100%;min-width:0;box-sizing:border-box';label.append(input);parent.append(label);return input;}
    function observationFields(kind,title){
      const box=element('fieldset',null);box.style.cssText='min-width:0;margin:8px 0;padding:8px';box.append(element('legend',title));
      labelInput(box,'原文字',kind+'-text');labelInput(box,'手動數值（保留原輸入）',kind+'-value',256);
      const unitLabel=element('label','原單位'),unit=element('select',null,{'data-evidence-input':kind+'-unit'});unit.style.cssText='max-width:100%;margin-left:8px';
      for(const [value,text]of [['','未指定'],['mm','mm'],['cm','cm']])unit.append(element('option',text,{value}));unitLabel.append(unit);box.append(unitLabel);
      labelInput(box,'備註',kind+'-note');form.append(box);
    }
    function observation(kind){
      const input=k=>form.querySelector(`[data-evidence-input="${kind}-${k}"]`).value;
      const rawText=input('text'),rawValue=input('value'),note=input('note');
      return !rawText&&!rawValue&&!note?null:{rawText,rawValue:rawValue||null,unit:input('unit')||null,note};
    }
    function observationText(o){return o?[o.rawText,o.rawValue===null?'':o.rawValue+(o.unit?' '+o.unit:''),o.note].filter(Boolean).join(' · ')||'已保留空文字':'未記錄';}
    function targetOptions(select){select.append(element('option','請指定參數欄位',{value:''}));for(const t of selection?.targets||[])select.append(element('option',t.label,{value:typed(t.target)}));}
    async function act(operation,onFailure=null,refreshOnFailure=false){
      if(busy||!connected())return;const request=++sequence,initial=stamp();busy=true;
      section.querySelectorAll('button,input,select').forEach(n=>{if(n!==cancelButton)n.disabled=true;});
      try{await operation();if(request!==sequence||!connected()||stamp().contextToken!==initial.contextToken||stamp().nativeRevision!==initial.nativeRevision)return;await refresh();}
      catch(error){if(request===sequence&&connected()){onFailure?.();const reason=error.message||'證據操作失敗。';if(refreshOnFailure){const updated=await refresh();if(updated||live(initial))tell(reason);}else if(live(initial)&&same(selectionIdentity,pageIdentity()))tell(reason);else{cancel();tell(reason);}}}
      finally{if(request===sequence){busy=false;section.querySelectorAll('input,select').forEach(n=>n.disabled=false);if(start)start.disabled=!selection;if(save)save.disabled=!region;section.querySelectorAll('[data-evidence-locate],[data-evidence-rebind]').forEach(n=>n.disabled=false);section.querySelectorAll('[data-evidence-reviewed]').forEach(n=>n.disabled=n.dataset.canConfirm!=='true');}}
    }
    function renderLinks(){
      list.replaceChildren();
      for(const link of view.links.filter(filter)){
        const article=element('article',null,{'data-evidence-id':link.evidenceId});article.style.cssText='min-width:0;border-top:1px solid #ccc;padding:10px 0';
        const current=selection.targets.find(t=>t.target.projectScope===link.target.projectScope&&typed(t.target)===typed(link.target));
        article.append(element('strong',current?.label||`參數 #${link.target.parameterId} · 欄位 #${link.target.fieldId}`));
        article.append(element('p',statusText[link.status]||'需重新核對',{'data-evidence-status':link.status}));
        const values=element('dl',null);values.style.cssText='margin:8px 0;min-width:0';
        for(const [title,text,key]of [['圖面標值',observationText(link.observations.drawing),'drawing'],['現場量測',observationText(link.observations.measurement),'measurement'],['正式模型值',valueText(link.modelValue),'model']]){
          values.append(element('dt',title));const cell=element('dd',text,{'data-evidence-value':key});cell.style.cssText='margin:2px 0 10px';values.append(cell);
        }article.append(values);
        const locate=element('button','定位原頁範圍',{type:'button','data-evidence-locate':link.evidenceId});locate.className='btn';
        locate.addEventListener('click',()=>act(async()=>{await controller.locate(link.evidenceId);}));article.append(locate);
        if(locateTarget){const target=element('button','定位參數欄位',{type:'button','data-evidence-locate-target':link.evidenceId});target.className='btn';target.disabled=['target-missing','needs-reassociation'].includes(link.status);target.addEventListener('click',()=>act(()=>locateTarget(link.evidenceId)));article.append(target);}
        const reviewedLabel=element('label',null);reviewedLabel.style.cssText='display:block;margin:10px 0';
        const reviewed=element('input',null,{type:'checkbox','data-evidence-reviewed':link.evidenceId});reviewed.checked=link.status==='confirmed-content';reviewed.disabled=!link.canConfirm;reviewed.dataset.canConfirm=String(link.canConfirm);
        reviewed.addEventListener('change',()=>act(()=>controller.setReviewed(link.evidenceId,reviewed.checked),()=>{reviewed.checked=link.status==='confirmed-content';reviewed.disabled=true;},true));reviewedLabel.append(reviewed,doc.createTextNode(' 已核對圖面與欄位'));article.append(reviewedLabel);
        if(!link.canConfirm){
          const select=element('select',null,{'aria-label':'重新指定參數欄位','data-evidence-rebind-target':link.evidenceId});select.style.cssText='display:block;max-width:100%;width:100%;margin:8px 0';targetOptions(select);article.append(select);
          const rebind=element('button','明選欄位重新關聯',{type:'button','data-evidence-rebind':link.evidenceId});rebind.className='btn';
          rebind.addEventListener('click',()=>{if(!live(selection.stamp)||!same(selectionIdentity,pageIdentity())){cancel();tell('來源或欄位已變更，請重新讀取後明選。');return;}const selected=readTarget(select);if(!selected){tell('請明確指定參數欄位。');return;}act(()=>controller.rebind(link.evidenceId,selected.target),null,true);});article.append(rebind);
        }list.append(article);
      }
      if(!view.links.some(filter))list.append(element('p','此頁尚無參數證據連結。'));
    }
    function render(){
      resetRegion();section.replaceChildren();section.append(element('h4','參數證據連結'));
      message=element('p','框選原 PDF 區域，手動記錄圖面與現場值；核對只更新此紀錄。',{'data-evidence-message':'',role:'status'});section.append(message);
      form=element('div',null,{'data-evidence-form':''});section.append(form);
      const label=element('label','指定參數欄位');targetSelect=element('select',null,{'aria-label':'指定參數欄位','data-evidence-target':''});targetSelect.style.cssText='display:block;width:100%;min-width:0;max-width:100%';targetOptions(targetSelect);label.append(targetSelect);form.append(label);
      const modelLabel=element('p','正式模型值：');model=element('output','無現行正式值',{'data-evidence-current-model':''});modelLabel.append(model);form.append(modelLabel);targetSelect.addEventListener('change',updateModel);
      observationFields('drawing','圖面標值');observationFields('measurement','現場量測');
      const actions=element('div',null);actions.style.cssText='display:flex;flex-wrap:wrap;gap:8px';
      start=element('button','在原頁框選區域',{type:'button','data-evidence-select':''});start.className='btn';start.disabled=!canvas||!selection.document;
      start.addEventListener('click',()=>{if(!live(selection.stamp)||!same(selectionIdentity,pageIdentity())){cancel();tell('來源已變更，請重新讀取來源紀錄。');return;}resetRegion();canvas?.beginSelection?.();selecting=true;drag=null;tell('在現有底圖按住拖曳框選；取消可保留原狀。');});
      save=element('button','保存證據連結',{type:'button','data-evidence-save':''});save.className='btn';save.disabled=true;
      save.addEventListener('click',()=>{const target=readTarget();if(!target){tell('請指定參數欄位。');return;}if(!live(selection.stamp)||!same(selectionIdentity,pageIdentity())){cancel();tell('來源已變更，請重新框選。');return;}
        const observations={drawing:observation('drawing'),measurement:observation('measurement')};if(!observations.drawing&&!observations.measurement){tell('請手動記錄至少一項圖面或現場觀察。');return;}
        act(()=>controller.add({document:selection.document,region,target:target.target,observations}));});
      cancelButton=element('button','取消',{type:'button','data-evidence-cancel':''});cancelButton.className='btn';cancelButton.addEventListener('click',cancel);actions.append(start,save,cancelButton);form.append(actions);
      regionFields=element('fieldset',null,{'data-evidence-region-controls':''});regionFields.hidden=true;regionFields.style.cssText='min-width:0';regionFields.append(element('legend','調整原頁框選範圍'));
      for(const [i,label]of ['X','Y','寬','高'].entries()){
        const input=labelInput(regionFields,label,'region-'+i,32);input.type='number';input.step='any';
        input.addEventListener('input',()=>{
          const rect=[0,1,2,3].map(i=>Number(regionFields.querySelector(`[data-evidence-input="region-${i}"]`).value)),d=selection.document;
          const valid=rect.every(Number.isFinite)&&rect[0]>=0&&rect[1]>=0&&rect[2]>0&&rect[3]>0&&rect[0]+rect[2]<=d.pageWidth&&rect[1]+rect[3]<=d.pageHeight;
          save.disabled=!valid;if(valid){region=rect;draw(region);}else {region=null;removeOverlay();tell('範圍須在原 PDF 頁面內。');}
        });
      }form.append(regionFields);
      list=element('div',null,{'data-evidence-list':''});section.append(list);renderLinks();
    }
    async function refresh(){
      const request=++sequence,initial=stamp(),identity=pageIdentity();busy=false;resetRegion();
      try{
        const results=await Promise.all([controller.readView(),readSelection()]);
        if(request!==sequence||!live(initial)||!same(identity,pageIdentity()))return false;
        const [nextView,nextSelection]=results;
        if(!same(nextView.stamp,initial)||!same(nextSelection.stamp,initial))return false;
        view=nextView;selection=nextSelection;selectionIdentity=identity;render();return true;
      }catch(error){if(request===sequence&&live(initial)){section.replaceChildren(element('p',error.message||'證據來源尚未讀取。',{'data-evidence-error':''}));}return false;}
    }
    function point(event){const p=canvas.eventPoint(event),page=canvas.toPage(Array.isArray(p)?p:[p.x,p.y]);if(!Array.isArray(page)||page.length!==2||!page.every(Number.isFinite))throw Error('原頁座標無法讀取。');return page;}
    function pointerDown(event){
      if(!selecting||event.button!==0||event.shiftKey)return;
      if(!selection||!live(selection.stamp)||!same(selectionIdentity,pageIdentity())){cancel();return;}
      event.preventDefault();event.stopImmediatePropagation();
      try{drag={pointerId:event.pointerId,start:point(event),identity:pageIdentity()};canvas.svg.setPointerCapture?.(event.pointerId);}catch(error){cancel();tell(error.message);}
    }
    function pointerMove(event){
      if(!drag||event.pointerId!==drag.pointerId)return;event.preventDefault();event.stopImmediatePropagation();
      if(!live(selection.stamp)||!same(drag.identity,pageIdentity())){cancel();return;}
      try{const end=point(event),begin=drag.start;region=[Math.min(begin[0],end[0]),Math.min(begin[1],end[1]),Math.abs(begin[0]-end[0]),Math.abs(begin[1]-end[1])];draw(region);}catch(error){cancel();tell(error.message);}
    }
    function pointerUp(event){
      if(!drag||event.pointerId!==drag.pointerId)return;pointerMove(event);if(!drag)return;release();selecting=false;
      const d=selection.document;
      if(!region||region[2]<=0||region[3]<=0||region[0]<0||region[1]<0||region[0]+region[2]>d.pageWidth||region[1]+region[3]>d.pageHeight){resetRegion();tell('請在原 PDF 頁面內框選有面積的區域。');return;}
      save.disabled=false;regionFields.hidden=false;
      region.forEach((n,i)=>regionFields.querySelector(`[data-evidence-input="region-${i}"]`).value=String(n));
      canvas?.endSelection?.();tell(`原頁範圍：${region.map(n=>Number(n.toFixed(3))).join(', ')}。`);
    }
    function toggle(){if(disclosure.open)refresh();else cancel();}
    function pointerCancel(){if(selecting||drag)cancel();}
    if(canvas?.svg){canvas.svg.addEventListener('pointerdown',pointerDown,true);canvas.svg.addEventListener('pointermove',pointerMove,true);canvas.svg.addEventListener('pointerup',pointerUp,true);canvas.svg.addEventListener('pointercancel',pointerCancel,true);}
    disclosure?.addEventListener('toggle',toggle);refresh();
    return {refresh,cancel,redraw(){if(region)draw(region);},destroy(){cancel();destroyed=true;disclosure?.removeEventListener('toggle',toggle);if(canvas?.svg){canvas.svg.removeEventListener('pointerdown',pointerDown,true);canvas.svg.removeEventListener('pointermove',pointerMove,true);canvas.svg.removeEventListener('pointerup',pointerUp,true);canvas.svg.removeEventListener('pointercancel',pointerCancel,true);}section.remove();},snapshot(){return {selecting,region:region&&[...region],links:view?.links.length??0};}};
  }
  return Object.freeze({mount,valueText,statusText:Object.freeze(statusText)});
});
