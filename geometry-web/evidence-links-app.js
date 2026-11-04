/* #48: the one saved bundle, existing reference canvas and parameter sources. */
(() => {
  'use strict';
  const E=window.EvidenceLinks,R=ReferenceWorkspace,S=window.SourceInspector;
  let controller=null,owner=null,referenceUI=null,referenceHost=null,parameterHost=null;
  let scheduled=false,sequence=0,located=null,referencePage=null,refreshReference=false,objectHosts=[],activatingLedger=0;
  const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const stamp=()=>R.getEvidenceState();
  const current=s=>same(s,stamp())&&!s.blocked;
  const selectedObjects=()=>[oc.sel?.kind==='boundary'?{kind:'boundary',id:oc.sel.id}:null,fe.sel?.kind==='timber'?{kind:'timber',id:fe.sel.id}:null].filter(Boolean);
  const page=()=>oc.edit&&R.active(oc.edit.bid);
  const pageIdentity=()=>{const p=page();return p?[p.id,p.sourceId,p.page,GeometryProject.reviewBasis(p)]:null;};
  async function readNative(initial) {
    const graph=S.index(await apiRequest('source-inspect'));
    const read=await apiRequest('engineering-read');
    if(!read.ok||graph.data.live!==true||graph.data.complete!==true||graph.data.revision!==read.revision||!current(initial)||read.revision!==initial.nativeRevision)
      throw Error('原生欄位或專案已變更，請重新核對。');
    return {graph,read};
  }
  const modelField=(read,t)=>read.state.parameters.find(p=>p.id===t.parameterId)?.fields.find(f=>f.id===t.fieldId)??null;
  const modelValue=(read,t)=>modelField(read,t)?.value??null;
  async function readCurrent(document,target) {
    const initial=stamp(),{graph,read}=await readNative(initial);
    const key=target.kind==='parameter-field'?S.key('parameter-field',target.parameterId,0,target.fieldId):S.key(target.kind,target.id);
    const node=graph.nodes.get(key);
    const identityStatus=E.identityStatusFromGraph(target,graph,initial.projectScope);
    if(!Object.hasOwn(target,'valuePin'))return {document:R.readEvidenceDocument(document),target:node&&target.kind==='parameter-field'?E.targetFromNode(initial.projectScope,node):null,
      modelValue:target.kind==='parameter-field'?modelValue(read,target):null,nativeRevision:read.revision,identityStatus};
    const live=node?{projectScope:initial.projectScope,kind:target.kind,definitionPin:node.definitionFingerprint,valuePin:node.valueFingerprint,incarnation:node.incarnation,
      ...(target.kind==='parameter-field'?{parameterId:target.parameterId,fieldId:target.fieldId}:{id:target.id})}:null;
    return {document:R.readEvidenceDocument(document),target:live,modelValue:target.kind==='parameter-field'?modelValue(read,target):null,
      parameterField:target.kind==='parameter-field'?modelField(read,target):null,nativeRevision:read.revision,identityStatus};
  }
  async function readSelection() {
    const initial=stamp(),identity=pageIdentity(),objects=selectedObjects(),{graph,read}=await readNative(initial),p=page();
    if(!same(identity,pageIdentity())||!same(objects,selectedObjects()))throw Error('參考頁或所選目標已切換，請重新框選。');
    const source=p&&R.context().sources.get(p.sourceId);
    const objectTargets=objects.map(t=>({target:{projectScope:initial.projectScope,...t},node:graph.nodes.get(S.key(t.kind,t.id))}))
      .filter(({node})=>node&&(node.kind!=='timber'||node.nativeOwner===null))
      .map(({target,node})=>({target,label:(target.kind==='boundary'?'邊界':'角材')+' #'+target.id+' · '+node.label,modelValue:null}));
    return {stamp:initial,document:p&&source?.meta.type==='application/pdf'?E.documentFromReference(p,source):null,
      targets:[...graph.nodes.values()].filter(n=>n.kind==='parameter-field').map(n=>{
        const target=E.targetFromNode(initial.projectScope,n);
        return {target,label:n.label+' · #'+n.id+':'+n.fieldId,modelValue:modelValue(read,target)};
      }).concat(objectTargets)};
  }
  function getController() {
    const state=stamp(),identity=state.contextToken+':'+state.session;
    if(owner!==identity){controller?.cancel();owner=identity;located=null;parameterHost=null;objectHosts=[];
      controller=E.createController({getStamp:stamp,getNavigationStamp:R.getEvidenceNavigationStamp,readCurrent,readFeatureAttachment:R.readFeatureAttachment,setFeatureAttachment:R.setFeatureAttachment,
        locateDocument:E.createLocator({getSourceStamp:R.getReferenceNavigationStamp,prepare:(...args)=>R.prepareReferencePage(...args),commit:(...args)=>R.commitPreparedReferencePage(...args)}),
        ledger:{
          async ensureActive({assertCurrent}){
            /* 有預覽仍啟用 */
            assertCurrent();const initial=stamp();
            const read=await apiRequest('identity-read');
            assertCurrent();
            if(!current(initial))throw Error('讀取身分帳期間專案已變更，未啟用。');
            if(!read.ok)throw Error(read.error||'無法讀取身分帳。');
            if(read.active)return {stamp:initial};
            let line;activatingLedger++;
            try{line=await apiRequest('line identity-ledger activate');}finally{activatingLedger--;}
            assertCurrent();if(!line.ok)throw Error(line.error||'未能啟用物件身分。');
            const after=stamp();if(after.nativeRevision!==line.revision||after.revision!==initial.revision+1)
              throw Error('啟用期間有其他變更，請重新明選目標。');
            return {stamp:after};
          },
          async readTarget(target){
            const initial=stamp(),graph=S.index(await apiRequest('source-inspect'));
            if(!current(initial)||graph.data.revision!==initial.nativeRevision||graph.data.live!==true||graph.data.complete!==true||graph.data.identityLedger?.active!==true)
              throw Error('專案或原生身分帳已變更，請重新明選目標。');
            const key=target.kind==='parameter-field'?S.key('parameter-field',target.parameterId,0,target.fieldId):S.key(target.kind,target.id);
            const node=graph.nodes.get(key);
            if(!node)throw Error('目標不存在。');
            if(target.kind==='timber'&&(node.nativeOwner!==null||node.incarnation==null))throw Object.assign(new Error('組構所有角材首版不支援。'),{code:'EVIDENCE_ASSEMBLY'});
            if(typeof node.incarnation!=='string')throw Error('目標沒有存在期記號。');
            if(E.identityStatusFromGraph({...target,projectScope:initial.projectScope,incarnation:node.incarnation},graph,initial.projectScope)!=='continuous')throw Error('目標身分有衝突，未建立證據。');
            return {definitionPin:node.definitionFingerprint,valuePin:node.valueFingerprint,incarnation:node.incarnation,assemblyOwned:false};
          }}});
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
    if(!link||['target-missing','target-replaced','needs-reassociation'].includes(link.status))throw Error('目標身分不明，請先明選重新關聯。');
    const {graph}=await readNative(initial),target=link.target,kind=target.kind==='parameter-field'?'parameter':target.kind,id=kind==='parameter'?target.parameterId:target.id;
    const node=graph.nodes.get(kind==='parameter'?S.key('parameter-field',id,0,target.fieldId):S.key(kind,id));
    if(!current(initial)||!same(navigation,R.getEvidenceNavigationStamp())||!node||kind!=='timber'&&!ocFind(kind,id))throw Error('目標或畫面已變更，未定位。');
    if(window.ParameterUI?.pending||fe.draft?.pts?.length||fe.ulCalib||window.RoomCollectionWorkspace?.hasWork)throw Error('請先完成或取消目前草稿。');
    if(kind==='timber'){
      let navigating=false;const allowed=()=>current(initial)&&(navigating||same(navigation,R.getEvidenceNavigationStamp()));
      await window.EngineeringAdapter.navigateObject({kind,id},{sourceGraph:graph,isCurrent:allowed,beginNavigation:()=>{if(!allowed())return false;navigating=true;return true;}});
      return {ok:true};
    }
    // All detached reads precede the final, synchronous selection transition.
    resetSceneFocus();drawObjects();selectObject(kind,id);centerOnNode(kind,id);
    if(kind==='parameter')document.querySelector(`[data-param-field="${target.fieldId}"]`)?.scrollIntoView({block:'nearest'});
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
  function renderEvidenceTarget(host,target,view) {
      if(!host.isConnected)return;
      host.replaceChildren();
      const links=E.linksFor(view.links,target),parameter=target.kind==='parameter-field';
      for(const link of links){
        const article=document.createElement('article');article.dataset[parameter?'parameterEvidence':'objectEvidence']=link.evidenceId;
        const text=document.createElement('p');text.textContent=parameter?`欄位 #${link.target.fieldId} · ${EvidenceLinksUI.statusText[link.status]} · 正式值 ${EvidenceLinksUI.valueText(link.modelValue)}`:
          `${target.kind==='boundary'?'邊界':'角材'} #${target.id} · ${EvidenceLinksUI.statusText[link.status]}`;
        article.append(text);
        for(const [label,o]of [['圖面標值',link.observations.drawing],['現場量測',link.observations.measurement]]){const line=document.createElement('p');line.textContent=label+'：'+(o?[o.rawText,o.rawValue===null?'':o.rawValue+(o.unit?' '+o.unit:''),o.note].filter(Boolean).join(' · '):'未記錄');article.append(line);}
        const button=document.createElement('button');button.type='button';button.className='btn';button.dataset[parameter?'parameterEvidenceLocate':'objectEvidenceLocate']=link.evidenceId;button.textContent='定位原頁範圍';
        button.disabled=['source-missing','source-changed'].includes(link.status);
        button.onclick=async()=>{button.disabled=true;try{await getController().locate(link.evidenceId);}catch(error){toast(error.message);}finally{if(button.isConnected)button.disabled=false;}};article.append(button);host.append(article);
      }
      if(!links.length){const p=document.createElement('p');p.textContent='尚無圖面證據；可從參考頁的來源紀錄框選並指定此目標。';host.append(p);}
  }
  async function sync() {
    const request=++sequence;
    try {
      if(stamp().nativeRevision===null){await apiRequest('source-inspect');if(request!==sequence)return;}
      getController();
      const host=document.querySelector('#refRecordDetails [data-evidence-host]');installReference(host);
      if(refreshReference&&!stamp().blocked){refreshReference=false;referenceUI?.refresh({preserveInput:true});}
      const target=document.querySelector('#paramUsage [data-parameter-evidence-host]');
      const objects=[...document.querySelectorAll('[data-object-evidence-host]')];
      if(parameterHost!==target||objects.length!==objectHosts.length||objects.some((h,i)=>h!==objectHosts[i])){
        parameterHost=target;objectHosts=objects;const initial=stamp(),targets=[];
        if(target&&oc.sel?.kind==='parameter')targets.push([target,{projectScope:initial.projectScope,kind:'parameter-field',parameterId:oc.sel.id}]);
        for(const host of objects){const kind=host.dataset.evidenceKind,id=Number(host.dataset.evidenceId);
          if(['boundary','timber'].includes(kind)&&Number.isSafeInteger(id)&&id>=0)targets.push([host,{projectScope:initial.projectScope,kind,id}]);}
        if(targets.length){const view=await getController().readView();if(request!==sequence||!current(initial))return;
          for(const [host,t]of targets){if(t.kind==='parameter-field'?(oc.sel?.kind==='parameter'&&oc.sel.id===t.parameterId):
            (host.dataset.evidenceKind===t.kind&&Number(host.dataset.evidenceId)===t.id))renderEvidenceTarget(host,t,view);}}
      }
    }catch(error){/* A view can be temporarily unavailable during native loads. */}
  }
  function queue(){if(scheduled)return;scheduled=true;queueMicrotask(()=>{scheduled=false;sync();});}
  for(const id of ['faceInspectorContent','inspectorContent']){
    const host=document.getElementById(id);if(host)new MutationObserver(records=>{if(records.some(r=>!r.target.closest?.('[data-evidence-links],[data-parameter-evidence-host],[data-object-evidence-host]')))queue();}).observe(host,{childList:true,subtree:true});
  }
  for(const name of ['project-local-history','geometry-definition-changed','evidence-links-changed','space-models-changed'])window.addEventListener(name,()=>{
    // This operation deliberately owns one native activation before its local
    // attachment step. Its own native event must not cancel that second step.
    if(name==='geometry-definition-changed'&&activatingLedger){parameterHost=null;objectHosts=[];return;}
    if(name!=='evidence-links-changed'){referenceUI?.cancel();refreshReference=true;}parameterHost=null;objectHosts=[];queue();
  });
  const savedLink=id=>R.readFeatureAttachment(E.KIND)?.links.find(l=>l.evidenceId===id);
  const adoptionField=(live,observation)=>({type:live.parameterField?.type,formula:live.parameterField?.expression?.op!=='literal',rawValue:observation?.rawValue||'',unit:observation?.unit||null});
  async function prefillAdoption(shown,observation){
    const initial=stamp(),link=savedLink(shown.evidenceId);
    if(!link||!Object.keys(link).every(key=>same(link[key],shown[key])))throw Error('證據已變更，請重新選擇採用值。');
    if(!['drawing','measurement'].includes(observation))throw Error('請明確選擇圖面標值或現場量測。');
    const live=await readCurrent(link.document,link.target);
    const plan=E.planAdoption(link,live,adoptionField(live,link.observations[observation]));
    if(!current(initial)||!same(savedLink(link.evidenceId),link))throw Error('採用來源已變更，未預填。');
    if(window.ParameterUI?.pending)throw Error('請先完成或捨棄目前參數草稿，再採用證據值。');
    await window.ParameterUI.jump('parameter',plan.parameterId);
    if(!current(initial)||!same(savedLink(link.evidenceId),link))throw Error('開啟參數卡期間來源已變更，未預填。');
    const intent={link:structuredClone(link),observation,plan,stamp:initial,field:{type:live.parameterField.type,expression:structuredClone(live.parameterField.expression)}};
    const result=window.ParameterUI.prefillEvidenceAdoption(intent);
    toast('已預填採用值。請檢視既有參數預覽，再確認套用。');return result;
  }
  async function prepareAdoption(intent,preview){
    const initial=stamp(),link=savedLink(intent.link.evidenceId),token=Number(preview?.token);
    if(!current(initial)||!same(initial,intent.stamp)||!same(link,intent.link)||preview?.valid!==true||!Number.isSafeInteger(token)||token<=0||token>4294967295)
      throw Error('採用候選或來源已變更，請重新預覽。');
    const live=await readCurrent(link.document,link.target),field=adoptionField(live,link.observations[intent.observation]);
    const plan=E.planAdoption(link,live,field);
    if(plan.literal!==intent.plan.literal||!current(initial))throw Error('採用值或專案已變更，未確認。');
    const graph=S.index(await apiRequest('engineering-preview-source '+token));
    if(!current(initial)||graph.data.live!==false||graph.data.complete!==true||graph.data.revision!==initial.nativeRevision||
       E.identityStatusFromGraph(link.target,graph,initial.projectScope)!=='continuous')throw Error('原生採用候選無法核對，未確認。');
    const key=S.key('parameter-field',plan.parameterId,0,plan.fieldId),node=graph.nodes.get(key);
    const native=preview.after?.parameters?.find(p=>p.id===plan.parameterId)?.fields.find(f=>f.id===plan.fieldId);
    if(native?.type!=='dimension'||native.expression?.op!=='literal'||native.value?.unit!=='mm')throw Error('原生候選不是尺寸字面值，未採用。');
    const candidate={previewed:true,live,field,value:structuredClone(native.value),definitionPinAfter:node.definitionFingerprint,valuePinAfter:node.valueFingerprint,
      adoptedAt:new Date().toISOString(),observation:intent.observation};
    E.previewAdoption(link,candidate);
    if(!current(initial)||!same(savedLink(link.evidenceId),link))throw Error('候選核對期間證據已變更，未確認。');
    R.prepareEvidenceConfirmation(token,{before:link,candidate,sourceFingerprint:graph.data.sourceFingerprint},initial);
  }
  window.EvidenceLinksApp={sync,queue,redraw,showRegion,locateTarget,getController,readSelection,prefillAdoption,prepareAdoption,getStamp:stamp,get ui(){return referenceUI;}};queue();
})();
