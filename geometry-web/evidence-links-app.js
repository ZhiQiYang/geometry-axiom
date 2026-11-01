/* #48: the one saved bundle, existing reference canvas and parameter sources. */
(() => {
  'use strict';
  const E=window.EvidenceLinks,R=ReferenceWorkspace,S=window.SourceInspector;
  let controller=null,owner=null,referenceUI=null,referenceHost=null,parameterHost=null;
  let scheduled=false,sequence=0,parameterSequence=0,located=null,referencePage=null,refreshReference=false;
  const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const stamp=()=>R.getEvidenceState();
  const current=s=>same(s,stamp())&&!s.blocked;
  const page=()=>oc.edit&&R.active(oc.edit.bid);
  const pageIdentity=()=>{const p=page();return p?[p.id,p.sourceId,p.page,GeometryProject.reviewBasis(p)]:null;};
  async function readNative(initial) {
    const graph=S.index(await apiRequest('source-inspect'));
    const read=await apiRequest('engineering-read');
    if(!read.ok||graph.data.complete!==true||graph.data.revision!==read.revision||!current(initial)||read.revision!==initial.nativeRevision)
      throw Error('原生欄位或專案已變更，請重新核對。');
    return {graph,read};
  }
  const modelValue=(read,t)=>read.state.parameters.find(p=>p.id===t.parameterId)?.fields.find(f=>f.id===t.fieldId)?.value??null;
  async function readCurrent(document,target) {
    const initial=stamp(),{graph,read}=await readNative(initial);
    const node=graph.nodes.get(S.key('parameter-field',target.parameterId,0,target.fieldId));
    return {document:R.readEvidenceDocument(document),target:node?E.targetFromNode(initial.projectScope,node):null,
      modelValue:modelValue(read,target),nativeRevision:read.revision};
  }
  async function readSelection() {
    const initial=stamp(),identity=pageIdentity(),{graph,read}=await readNative(initial),p=page();
    if(!same(identity,pageIdentity()))throw Error('參考頁已切換，請重新框選。');
    const source=p&&R.context().sources.get(p.sourceId);
    return {stamp:initial,document:p&&source?.meta.type==='application/pdf'?E.documentFromReference(p,source):null,
      targets:[...graph.nodes.values()].filter(n=>n.kind==='parameter-field').map(n=>{
        const target=E.targetFromNode(initial.projectScope,n);
        return {target,label:n.label+' · #'+n.id+':'+n.fieldId,modelValue:modelValue(read,target)};
      })};
  }
  function getController() {
    const state=stamp(),identity=state.contextToken+':'+state.session;
    if(owner!==identity){controller?.cancel();owner=identity;located=null;
      controller=E.createController({getStamp:stamp,getNavigationStamp:R.getEvidenceNavigationStamp,readCurrent,readFeatureAttachment:R.readFeatureAttachment,setFeatureAttachment:R.setFeatureAttachment,
        locateDocument:E.createLocator({getSourceStamp:R.getReferenceNavigationStamp,prepare:(...args)=>R.prepareReferencePage(...args),commit:(...args)=>R.commitPreparedReferencePage(...args)})});
    }
    return controller;
  }
  function showRegion(document,region){located={document:structuredClone(document),region:[...region]};}
  function redraw() {
    referenceUI?.redraw();
    const p=page(),root=document.getElementById('faceEditorRoot');
    root?.querySelector('[data-evidence-located]')?.remove();
    if(!root||!p||!located||p.sourceId!==located.document.sourceHash||p.page!==located.document.page||p.id!==located.document.referencePageId)return;
    const [x,y,w,h]=located.region,polygon=document.createElementNS('http://www.w3.org/2000/svg','polygon');polygon.dataset.evidenceLocated='';
    for(const [k,v]of Object.entries({points:[[x,y],[x+w,y],[x+w,y+h],[x,y+h]].map(v=>feUlImgToMm(p,...v).join(',')).join(' '),fill:'rgba(107,78,158,.12)',stroke:'#70549a','stroke-width':2,'vector-effect':'non-scaling-stroke','pointer-events':'none'}))polygon.setAttribute(k,v);
    root.append(polygon);
  }
  async function locateTarget(evidenceId) {
    const c=getController(),initial=stamp(),navigation=R.getEvidenceNavigationStamp(),view=await c.readView();
    const link=view.links.find(l=>l.evidenceId===evidenceId);
    if(!link||['target-missing','needs-reassociation'].includes(link.status))throw Error('欄位身分不明，請先明選重新關聯。');
    const {graph}=await readNative(initial),node=graph.nodes.get(S.key('parameter-field',link.target.parameterId,0,link.target.fieldId));
    if(!current(initial)||!same(navigation,R.getEvidenceNavigationStamp())||!node||!ocFind('parameter',link.target.parameterId))throw Error('參數欄位或畫面已變更，未定位。');
    if(window.ParameterUI?.pending||fe.draft?.pts?.length||fe.ulCalib||window.RoomCollectionWorkspace?.hasWork)throw Error('請先完成或取消目前草稿。');
    // All detached reads precede the final, synchronous selection transition.
    resetSceneFocus();drawObjects();selectObject('parameter',link.target.parameterId);centerOnNode('parameter',link.target.parameterId);
    document.querySelector(`[data-param-field="${link.target.fieldId}"]`)?.scrollIntoView({block:'nearest'});
    if(innerWidth<=900)openPanel('right',document.getElementById('toggleRight'));
    return {ok:true};
  }
  function installReference(host) {
    const identity=JSON.stringify([pageIdentity(),stamp().contextToken]);
    if(referenceHost===host&&referencePage===identity&&host?.isConnected)return;
    const open=referenceHost?.closest('details')?.open;
    const initialInput=referencePage===identity?referenceUI?.captureInput():null;
    referenceUI?.destroy();referenceUI=null;referenceHost=host;referencePage=identity;
    if(!host)return;
    if(open)host.closest('details').open=true;
    const canvas={svg:document.getElementById('faceEditorSvg'),layer:()=>document.getElementById('faceEditorRoot'),eventPoint:fePoint,
      toPage:p=>feUlMmToImg(page(),...p),fromPage:p=>feUlImgToMm(page(),...p),pageIdentity,
      beginSelection(){if(innerWidth<=680)closePanels();},
      endSelection(){if(innerWidth<=680)openPanel('right',document.getElementById('workspaceToggleRight'));}};
    referenceUI=EvidenceLinksUI.mount(host,{controller:getController(),getStamp:stamp,readSelection,canvas,initialInput,
      filter:link=>{const p=page();return !!p&&(link.document.referencePageId===p.id||link.document.sourceHash===p.sourceId&&link.document.page===p.page);},locateTarget});
  }
  async function renderParameter(host) {
    const request=++parameterSequence,initial=stamp(),id=oc.sel?.kind==='parameter'?oc.sel.id:null;
    try {
      const view=await getController().readView();
      if(request!==parameterSequence||!host.isConnected||!current(initial)||id!==oc.sel?.id)return;
      host.replaceChildren();
      const links=view.links.filter(l=>l.target.projectScope===initial.projectScope&&l.target.parameterId===id);
      for(const link of links){
        const article=document.createElement('article');article.dataset.parameterEvidence=link.evidenceId;
        const text=document.createElement('p');text.textContent=`欄位 #${link.target.fieldId} · ${EvidenceLinksUI.statusText[link.status]} · 正式值 ${EvidenceLinksUI.valueText(link.modelValue)}`;
        article.append(text);
        for(const [label,o]of [['圖面標值',link.observations.drawing],['現場量測',link.observations.measurement]]){const line=document.createElement('p');line.textContent=label+'：'+(o?[o.rawText,o.rawValue===null?'':o.rawValue+(o.unit?' '+o.unit:''),o.note].filter(Boolean).join(' · '):'未記錄');article.append(line);}
        const button=document.createElement('button');button.type='button';button.className='btn';button.dataset.parameterEvidenceLocate=link.evidenceId;button.textContent='定位原頁範圍';
        button.disabled=['source-missing','source-changed'].includes(link.status);
        button.onclick=async()=>{button.disabled=true;try{await getController().locate(link.evidenceId);}catch(error){toast(error.message);}finally{if(button.isConnected)button.disabled=false;}};article.append(button);host.append(article);
      }
      if(!links.length){const p=document.createElement('p');p.textContent='尚無圖面證據；可從參考頁的來源紀錄框選並指定此欄位。';host.append(p);}
    }catch(error){if(request===parameterSequence&&host.isConnected)host.textContent=error.message;}
  }
  async function sync() {
    const request=++sequence;
    try {
      if(stamp().nativeRevision===null){await apiRequest('source-inspect');if(request!==sequence)return;}
      getController();
      const host=document.querySelector('#refRecordDetails [data-evidence-host]');installReference(host);
      if(refreshReference&&!stamp().blocked){refreshReference=false;referenceUI?.refresh({preserveInput:true});}
      const target=document.querySelector('#paramUsage [data-parameter-evidence-host]');
      if(parameterHost!==target){parameterHost=target;if(target)renderParameter(target);}
    }catch(error){/* A view can be temporarily unavailable during native loads. */}
  }
  function queue(){if(scheduled)return;scheduled=true;queueMicrotask(()=>{scheduled=false;sync();});}
  for(const id of ['faceInspectorContent','inspectorContent']){
    const host=document.getElementById(id);if(host)new MutationObserver(records=>{if(records.some(r=>!r.target.closest?.('[data-evidence-links],[data-parameter-evidence-host]')))queue();}).observe(host,{childList:true,subtree:true});
  }
  for(const name of ['project-local-history','geometry-definition-changed','evidence-links-changed','space-models-changed'])window.addEventListener(name,()=>{
    if(name!=='evidence-links-changed'){referenceUI?.cancel();refreshReference=true;}parameterHost=null;queue();
  });
  window.EvidenceLinksApp={sync,queue,redraw,showRegion,locateTarget,getController,readSelection,getStamp:stamp,get ui(){return referenceUI;}};queue();
})();
