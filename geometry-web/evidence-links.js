/* #48: bounded project annotations. This module never issues native mutations.
   Attachment kind/schema are candidates until registered by the shared owner. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.EvidenceLinks=api;})(globalThis,()=>{
  'use strict';
  const KIND='evidence-links',SCHEMA='geometry-evidence-links/1',COORDINATES='pdf-viewport-scale-1-y-down';
  const MAX_LINKS=256,MAX_BYTES=2*1024*1024,HASH=/^[a-f0-9]{64}$/;
  const clone=v=>JSON.parse(JSON.stringify(v));
  const fail=(code,message)=>{throw Object.assign(new Error(message),{code});};
  const plain=v=>v!==null&&typeof v==='object'&&!Array.isArray(v)&&[Object.prototype,null].includes(Object.getPrototypeOf(v));
  const keys=(v,expected)=>plain(v)&&Object.keys(v).length===expected.length&&expected.every(k=>Object.hasOwn(v,k));
  const text=(v,max,empty=false)=>typeof v==='string'&&v.length<=max&&(empty||v.length>0);
  const identity=v=>text(v,128)&&/^[a-zA-Z0-9_.:-]+$/.test(v);
  const uint=v=>Number.isSafeInteger(v)&&v>=0&&v<=4294967295;
  const hash=v=>typeof v==='string'&&HASH.test(v);
  function rect(v,w,h){return Array.isArray(v)&&v.length===4&&v.every(Number.isFinite)&&v[0]>=0&&v[0]<w&&v[1]>=0&&v[1]<h&&v[2]>0&&v[3]>0&&v[2]<=w-v[0]&&v[3]<=h-v[1];}
  function documentValid(d){
    return keys(d,['sourceHash','referencePageId','page','coordinateSpace','pageWidth','pageHeight','rotationBasis','cropBasis'])&&hash(d.sourceHash)&&identity(d.referencePageId)&&
      Number.isSafeInteger(d.page)&&d.page>=1&&d.page<=100000&&d.coordinateSpace===COORDINATES&&
      Number.isFinite(d.pageWidth)&&d.pageWidth>=1&&d.pageWidth<=1e7&&Number.isFinite(d.pageHeight)&&d.pageHeight>=1&&d.pageHeight<=1e7&&
      [0,90,180,270].includes(d.rotationBasis)&&rect(d.cropBasis,d.pageWidth,d.pageHeight);
  }
  function targetValid(t){return keys(t,['projectScope','kind','parameterId','fieldId','definitionPin','incarnation'])&&identity(t.projectScope)&&t.kind==='parameter-field'&&uint(t.parameterId)&&uint(t.fieldId)&&hash(t.definitionPin)&&t.incarnation===null;}
  function observationValid(o){return o===null||keys(o,['rawText','rawValue','unit','note'])&&text(o.rawText,2000,true)&&(o.rawValue===null||text(o.rawValue,256,true))&&[null,'mm','cm'].includes(o.unit)&&text(o.note,2000,true);}
  function linkValid(l){return keys(l,['evidenceId','document','region','target','observations','humanConfirmation'])&&identity(l.evidenceId)&&documentValid(l.document)&&rect(l.region,l.document.pageWidth,l.document.pageHeight)&&targetValid(l.target)&&
    keys(l.observations,['drawing','measurement'])&&observationValid(l.observations.drawing)&&observationValid(l.observations.measurement)&&(l.observations.drawing!==null||l.observations.measurement!==null)&&
    (l.humanConfirmation===null||keys(l.humanConfirmation,['documentHash','targetPin','confirmedAt'])&&l.humanConfirmation.documentHash===l.document.sourceHash&&l.humanConfirmation.targetPin===l.target.definitionPin&&
      text(l.humanConfirmation.confirmedAt,24)&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(l.humanConfirmation.confirmedAt)&&Number.isFinite(Date.parse(l.humanConfirmation.confirmedAt))&&new Date(l.humanConfirmation.confirmedAt).toISOString()===l.humanConfirmation.confirmedAt);
  }
  // Validate before cloning: reject exotic prototypes/accessors/executable data.
  function boundedJSON(v,depth=0){
    if(depth>16)fail('EVIDENCE_JSON','證據資料層數超過限制。');
    if(v===null||typeof v==='boolean'||typeof v==='string'||typeof v==='number'&&Number.isFinite(v))return;
    if(Array.isArray(v)?Object.getPrototypeOf(v)!==Array.prototype:!plain(v))fail('EVIDENCE_JSON','證據只能保存 plain JSON。');
    if(Object.getOwnPropertySymbols(v).length)fail('EVIDENCE_JSON','證據資料含有不支援欄位。');
    for(const descriptor of Object.values(Object.getOwnPropertyDescriptors(v))){if(!Object.hasOwn(descriptor,'value'))fail('EVIDENCE_JSON','證據不能保存 accessor。');boundedJSON(descriptor.value,depth+1);}
  }
  function validate(value){
    boundedJSON(value);
    if(!keys(value,['schema','links'])||value.schema!==SCHEMA)fail('EVIDENCE_SCHEMA','證據附件版本尚未支援。');
    if(!Array.isArray(value.links)||value.links.length>MAX_LINKS)fail('EVIDENCE_CAPACITY','證據數量超過限制。');
    const ids=new Set();for(const l of value.links){if(!linkValid(l)||ids.has(l.evidenceId))fail('EVIDENCE_INVALID','證據欄位、頁碼、範圍或身分不合法。');ids.add(l.evidenceId);}
    if(new TextEncoder().encode(JSON.stringify(value)).length>MAX_BYTES)fail('EVIDENCE_CAPACITY','證據附件超過容量限制。');
    return true;
  }
  const empty=()=>({schema:SCHEMA,links:[]});
  function references(value){validate(value);return {sources:[...new Set(value.links.map(l=>l.document.sourceHash))],targets:value.links.map(l=>({kind:l.target.kind,projectScope:l.target.projectScope,parameterId:l.target.parameterId,fieldId:l.target.fieldId}))};}
  function documentFromReference(p){
    const d={sourceHash:p.sourceId,referencePageId:p.id,page:p.page,coordinateSpace:COORDINATES,pageWidth:p.imgW,pageHeight:p.imgH,rotationBasis:p.rot,cropBasis:clone(p.crop)};
    if(!documentValid(d))fail('EVIDENCE_DOCUMENT','請選擇有效的既有 PDF 原頁。');return d;
  }
  function targetFromNode(projectScope,n){
    if(n?.kind!=='parameter-field'||typeof n.id!=='string'||!/^\d+$/.test(n.id)||n.key!==`parameter-field:${Number(n.id)}:f${n.fieldId}`)fail('EVIDENCE_TARGET','請明選參數欄位。');
    const t={projectScope,kind:'parameter-field',parameterId:Number(n.id),fieldId:n.fieldId,definitionPin:n.definitionFingerprint,incarnation:null};
    if(!targetValid(t))fail('EVIDENCE_TARGET','參數欄位來源指紋無效。');return t;
  }
  const targetKey=t=>`${t.projectScope}:parameter-field:${t.parameterId}:f${t.fieldId}`;
  const valueValid=v=>v===null||keys(v,['num','den','unit'])&&text(v.num,200)&&/^-?\d+$/.test(v.num)&&text(v.den,200)&&/^[1-9]\d*$/.test(v.den)&&['mm','1'].includes(v.unit);
  function assess(link,current,{identityKnown=false}={}){
    validate({schema:SCHEMA,links:[link]});
    if(!current?.document)return {status:'source-missing',canConfirm:false};
    if(!documentValid(current.document))fail('EVIDENCE_DOCUMENT','現行來源頁無法核對。');
    const a=link.document,b=current.document;
    // Display rotation/crop changes do not change original full-page coordinates.
    if(a.sourceHash!==b.sourceHash||a.page!==b.page||a.pageWidth!==b.pageWidth||a.pageHeight!==b.pageHeight||a.coordinateSpace!==b.coordinateSpace||a.referencePageId!==b.referencePageId)return {status:'source-changed',canConfirm:false};
    if(!current.target)return {status:'target-missing',canConfirm:false};
    if(!targetValid(current.target)||!valueValid(current.modelValue))fail('EVIDENCE_TARGET','現行參數欄位無法核對。');
    if(targetKey(link.target)!==targetKey(current.target)||link.target.definitionPin!==current.target.definitionPin||!identityKnown)return {status:'needs-reassociation',canConfirm:false};
    return {status:link.humanConfirmation?'confirmed-content':'unchecked',canConfirm:true};
  }
  // Shared archive owner calls this before replacing any live project state.
  async function validateSourceClosure(value,{readSource,hashBytes,readPage}){
    validate(value);const snapshot=clone(value);
    for(const sourceHash of references(snapshot).sources){
      const source=await readSource(sourceHash);
      if(!source||source.meta?.id!==sourceHash||source.meta.hash!==sourceHash||source.meta.type!=='application/pdf'||!(source.bytes instanceof Uint8Array)||source.meta.size!==source.bytes.length)fail('EVIDENCE_SOURCE_CLOSURE','證據原 PDF 缺失或內容指紋不符。');
      const s={meta:{...source.meta},bytes:source.bytes.slice()};
      if(await hashBytes(s.bytes)!==sourceHash)fail('EVIDENCE_SOURCE_CLOSURE','證據原 PDF 內容指紋不符。');
      const pages=new Map();for(const l of snapshot.links.filter(l=>l.document.sourceHash===sourceHash)){
        const d=l.document;if(!pages.has(d.page))pages.set(d.page,await readPage(s,d.page));const p=pages.get(d.page);
        if(!p||p.width!==d.pageWidth||p.height!==d.pageHeight)fail('EVIDENCE_PAGE_CLOSURE','證據頁碼或原頁尺寸與 PDF 不符。');
      }
    }
    validate(value);if(JSON.stringify(value)!==JSON.stringify(snapshot))fail('EVIDENCE_STALE_CLOSURE','驗證期間證據附件已變更，未接受來源閉包。');
    return true;
  }
  function createController({readFeatureAttachment,setFeatureAttachment,getStamp,readCurrent,locateDocument,uuid=()=>crypto.randomUUID(),now=()=>new Date().toISOString()}){
    if(typeof setFeatureAttachment!=='function'||setFeatureAttachment.constructor?.name==='AsyncFunction')fail('EVIDENCE_ADAPTER','證據附件需要同步、原子的一步本地寫入接口。');
    let sequence=0;const leases=new Map();
    const stamp=()=>{const s=getStamp();if(!identity(s.projectScope)||!identity(s.contextToken)||!Number.isSafeInteger(s.revision)||s.revision<0||!Number.isSafeInteger(s.nativeRevision)||s.nativeRevision<0)fail('EVIDENCE_CONTEXT','目前專案上下文無法確認。');return clone(s);};
    const stable=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
    const guard=(s,seq)=>{if(seq!==sequence||!stable(s,stamp()))fail('EVIDENCE_STALE','操作已取消或專案已變更，請重新核對。');};
    const bundle=()=>{const v=readFeatureAttachment(KIND)??empty();validate(v);return clone(v);};
    const find=(v,id)=>{const l=v.links.find(l=>l.evidenceId===id);if(!l)fail('EVIDENCE_MISSING','證據已移除。');return l;};
    const leaseKnown=(l,s)=>{const x=leases.get(l.evidenceId);return !!x&&x.contextToken===s.contextToken&&x.nativeRevision===s.nativeRevision&&x.targetPin===l.target.definitionPin&&x.targetKey===targetKey(l.target);};
    const bind=(l,s)=>leases.set(l.evidenceId,{contextToken:s.contextToken,nativeRevision:s.nativeRevision,targetPin:l.target.definitionPin,targetKey:targetKey(l.target)});
    function commit(v,s,seq,l){
      validate(v);guard(s,seq);
      // No await between the final guard and the local history mutation. The
      // shared setter is synchronous; remote writes/late acknowledgments do
      // not belong in this interface.
      const result=setFeatureAttachment(KIND,clone(v),s.contextToken);
      if(result&&typeof result.then==='function')fail('EVIDENCE_ADAPTER','附件接口不能回傳非同步寫入。');
      // A synchronous notification may cancel the view after a completed local
      // commit. That is success, with no new runtime identity lease; do not
      // report a rejected operation after its annotation was already saved.
      const end=stamp();if(l&&seq===sequence&&end.contextToken===s.contextToken&&end.nativeRevision===s.nativeRevision)bind(l,end);return clone(v);
    }
    async function current(l,s,seq){const c=await readCurrent(clone(l.document),clone(l.target));guard(s,seq);if(c?.nativeRevision!==s.nativeRevision)fail('EVIDENCE_STALE','原生來源版本已變更，請重新核對。');return c;}
    async function add({document,region,target,observations}){
      const seq=++sequence,s=stamp(),v=bundle(),l={evidenceId:uuid(),document:clone(document),region:clone(region),target:clone(target),observations:clone(observations),humanConfirmation:null};
      validate({schema:SCHEMA,links:[l]});if(l.target.projectScope!==s.projectScope)fail('EVIDENCE_SCOPE','參數欄位屬於另一份專案。');
      const c=await current(l,s,seq),state=assess(l,c,{identityKnown:true});if(!state.canConfirm)fail('EVIDENCE_ASSOCIATION','明選的來源或參數欄位已變更。');v.links.push(l);commit(v,s,seq,l);return clone(l);
    }
    async function readView(){
      const seq=++sequence,s=stamp(),v=bundle();const links=[];
      for(const l of v.links){const c=await current(l,s,seq);links.push({...clone(l),...assess(l,c,{identityKnown:leaseKnown(l,s)&&l.target.projectScope===s.projectScope}),modelValue:clone(c?.modelValue??null)});}guard(s,seq);
      return {stamp:s,links};
    }
    async function setReviewed(evidenceId,checked){
      if(typeof checked!=='boolean')fail('EVIDENCE_CONFIRM','核對狀態不合法。');const seq=++sequence,s=stamp(),v=bundle(),l=find(v,evidenceId);
      const c=await current(l,s,seq);if(checked&&!assess(l,c,{identityKnown:leaseKnown(l,s)&&l.target.projectScope===s.projectScope}).canConfirm)fail('EVIDENCE_RECHECK','來源或物件身分不明，請明選欄位重新關聯。');
      l.humanConfirmation=checked?{documentHash:l.document.sourceHash,targetPin:l.target.definitionPin,confirmedAt:now()}:null;
      commit(v,s,seq,leaseKnown(l,s)?l:null);return clone(l);
    }
    async function rebind(evidenceId,target){
      const seq=++sequence,s=stamp(),v=bundle(),l=find(v,evidenceId);if(!targetValid(target)||target.projectScope!==s.projectScope)fail('EVIDENCE_SCOPE','請明選本專案的參數欄位。');
      l.target=clone(target);l.humanConfirmation=null;const c=await current(l,s,seq);if(!assess(l,c,{identityKnown:true}).canConfirm)fail('EVIDENCE_ASSOCIATION','來源或參數欄位已變更，請重新選擇。');commit(v,s,seq,l);return clone(l);
    }
    async function locate(evidenceId){
      const seq=++sequence,s=stamp(),l=find(bundle(),evidenceId),c=await current(l,s,seq),status=assess(l,c).status;
      if(['source-missing','source-changed'].includes(status))fail('EVIDENCE_RECHECK','原圖缺失或已換版，請重新核對。');guard(s,seq);
      return locateDocument(clone(l.document),clone(l.region),{isCurrent:()=>seq===sequence&&stable(s,stamp())});
    }
    return {add,readView,setReviewed,rebind,locate,cancel(){++sequence;}};
  }
  return Object.freeze({KIND,SCHEMA,COORDINATES,MAX_LINKS,MAX_BYTES,empty,validate,references,documentFromReference,targetFromNode,targetKey,assess,validateSourceClosure,createController});
});
