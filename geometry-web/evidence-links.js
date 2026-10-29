/* #48: bounded project annotations. This module never issues native mutations.
   Attachment kind/schema are candidates until registered by the shared owner. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.EvidenceLinks=api;})(globalThis,()=>{
  'use strict';
  const KIND='evidence-links',SCHEMA='geometry-evidence-links/1',SCHEMA_V2='geometry-evidence-links/2',COORDINATES='pdf-viewport-scale-1-y-down';
  const MAX_LINKS=256,MAX_BYTES=2*1024*1024,HASH=/^[a-f0-9]{64}$/,MARK=/^[a-f0-9]{32}:[1-9][0-9]*$/;
  const IDENTITY_ORDER=['unknown','conflict','absent','replaced','continuous'];
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
  function finishLinks(value,valid){
    if(!keys(value,['schema','links']))fail('EVIDENCE_SCHEMA','證據附件版本尚未支援。');
    if(!Array.isArray(value.links)||value.links.length>MAX_LINKS)fail('EVIDENCE_CAPACITY','證據數量超過限制。');
    const ids=new Set();for(const l of value.links){if(!valid(l)||ids.has(l.evidenceId))fail('EVIDENCE_INVALID','證據欄位、頁碼、範圍或身分不合法。');ids.add(l.evidenceId);}
    if(new TextEncoder().encode(JSON.stringify(value)).length>MAX_BYTES)fail('EVIDENCE_CAPACITY','證據附件超過容量限制。');
    return true;
  }
  function validate(value){
    boundedJSON(value);
    if(!plain(value)||!Object.hasOwn(value,'schema'))fail('EVIDENCE_SCHEMA','證據附件版本尚未支援。');
    if(value.schema===SCHEMA)return finishLinks(value,linkValid);
    if(value.schema===SCHEMA_V2)return finishLinks(value,linkValidV2);
    fail('EVIDENCE_SCHEMA','證據附件版本尚未支援。');
  }
  const empty=()=>({schema:SCHEMA,links:[]});
  function referenceTarget(t){return t.kind==='parameter-field'?{kind:t.kind,projectScope:t.projectScope,parameterId:t.parameterId,fieldId:t.fieldId}:{kind:t.kind,projectScope:t.projectScope,id:t.id};}
  function references(value){validate(value);return {sources:[...new Set(value.links.map(l=>l.document.sourceHash))],targets:value.links.map(l=>referenceTarget(l.target))};}
  function documentFromReference(p,source){
    // Use the existing source-pool entry, not its filename or page shape. Its
    // bytes/runtime PDF cache are deliberately outside the JSON descriptor.
    const metaDescriptor=source&&Object.getOwnPropertyDescriptor(source,'meta'),meta=metaDescriptor?.value;
    if(!metaDescriptor||!Object.hasOwn(metaDescriptor,'value')||!plain(meta))fail('EVIDENCE_DOCUMENT','請選擇有效的既有 PDF 原頁。');
    boundedJSON(meta);
    const fields={};for(const key of ['sourceId','id','page','imgW','imgH','rot','crop']){
      const descriptor=p&&Object.getOwnPropertyDescriptor(p,key);
      if(!descriptor||!Object.hasOwn(descriptor,'value'))fail('EVIDENCE_DOCUMENT','原頁資訊無法安全核對。');fields[key]=descriptor.value;
    }
    boundedJSON(fields);
    if(!['id','hash','type'].every(k=>Object.hasOwn(meta,k))||meta.type!=='application/pdf'||meta.id!==fields.sourceId||meta.hash!==fields.sourceId)fail('EVIDENCE_DOCUMENT','證據只接受身分相符的既有 PDF 原頁。');
    const d={sourceHash:fields.sourceId,referencePageId:fields.id,page:fields.page,coordinateSpace:COORDINATES,pageWidth:fields.imgW,pageHeight:fields.imgH,rotationBasis:fields.rot,cropBasis:fields.crop};
    if(!documentValid(d))fail('EVIDENCE_DOCUMENT','請選擇有效的既有 PDF 原頁。');return clone(d);
  }
  function targetFromNode(projectScope,n){
    if(n?.kind!=='parameter-field'||typeof n.id!=='string'||!/^\d+$/.test(n.id)||n.key!==`parameter-field:${Number(n.id)}:f${n.fieldId}`)fail('EVIDENCE_TARGET','請明選參數欄位。');
    const t={projectScope,kind:'parameter-field',parameterId:Number(n.id),fieldId:n.fieldId,definitionPin:n.definitionFingerprint,incarnation:null};
    if(!targetValid(t))fail('EVIDENCE_TARGET','參數欄位來源指紋無效。');return t;
  }
  const targetKey=t=>t.kind==='boundary'||t.kind==='timber'?`${t.projectScope}:${t.kind}:${t.id}`:`${t.projectScope}:parameter-field:${t.parameterId}:f${t.fieldId}`;
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
  const iso=v=>text(v,24)&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(v)&&Number.isFinite(Date.parse(v))&&new Date(v).toISOString()===v;
  const mark=v=>typeof v==='string'&&MARK.test(v);
  function pinPair(t,ledger){return hash(t.definitionPin)&&(ledger?hash(t.valuePin):t.valuePin===null)&&(ledger?mark(t.incarnation):t.incarnation===null);}
  function targetValidV2(t){
    if(!plain(t)||!identity(t.projectScope)||!['parameter-field','boundary','timber'].includes(t.kind))return false;
    const ledger=t.identityBasis==='ledger';
    if(t.kind==='parameter-field')return keys(t,['projectScope','kind','parameterId','fieldId','definitionPin','valuePin','incarnation','identityBasis'])&&uint(t.parameterId)&&uint(t.fieldId)&&pinPair(t,ledger);
    return keys(t,['projectScope','kind','id','definitionPin','valuePin','incarnation','identityBasis'])&&uint(t.id)&&pinPair(t,ledger);
  }
  function confirmationValidV2(c,t){return c===null||keys(c,['documentHash','definitionPin','valuePin','confirmedAt'])&&c.documentHash&&c.definitionPin===t.definitionPin&&c.valuePin===t.valuePin&&iso(c.confirmedAt);}
  function adoptionValid(a,t){
    return a===null||t.kind==='parameter-field'&&keys(a,['observation','literal','value','definitionPinBefore','definitionPinAfter','adoptedAt'])&&['drawing','measurement'].includes(a.observation)&&text(a.literal,256)&&
      keys(a.value,['num','den'])&&/^-?\d+$/.test(a.value.num)&&/^[1-9]\d*$/.test(a.value.den)&&hash(a.definitionPinBefore)&&a.definitionPinAfter===t.definitionPin&&iso(a.adoptedAt);
  }
  function linkValidV2(l){
    if(!keys(l,['evidenceId','document','region','target','observations','humanConfirmation','identityBasis','adoption'])||!identity(l.evidenceId)||!documentValid(l.document)||!rect(l.region,l.document.pageWidth,l.document.pageHeight))return false;
    if(!['ledger','legacy-v1'].includes(l.identityBasis)||!targetValidV2({...l.target,identityBasis:l.identityBasis}))return false;
    if(!keys(l.observations,['drawing','measurement'])||!observationValid(l.observations.drawing)||!observationValid(l.observations.measurement)||(l.observations.drawing===null&&l.observations.measurement===null))return false;
    if(!confirmationValidV2(l.humanConfirmation,l.target)||(l.humanConfirmation&&l.humanConfirmation.documentHash!==l.document.sourceHash))return false;
    return adoptionValid(l.adoption,l.target);
  }
  function upgradePackage(value){
    validate(value);
    if(value.schema===SCHEMA_V2)return clone(value);
    const links=value.links.map(l=>({evidenceId:l.evidenceId,document:clone(l.document),region:[...l.region],target:{...clone(l.target),valuePin:null},observations:clone(l.observations),
      humanConfirmation:l.humanConfirmation?{documentHash:l.humanConfirmation.documentHash,definitionPin:l.humanConfirmation.targetPin,valuePin:null,confirmedAt:l.humanConfirmation.confirmedAt}:null,
      identityBasis:'legacy-v1',adoption:null}));
    const next={schema:SCHEMA_V2,links};validate(next);return next;
  }
  function identityVerdict(checks){for(const status of IDENTITY_ORDER)if(checks&&checks[status])return status;return 'unknown';}
  function assessBound(link,current,options={}){
    if(!link.identityBasis)return assess(link,current,options);
    validate({schema:SCHEMA_V2,links:[link]});
    if(!current?.document)return {status:'source-missing',canConfirm:false};
    if(!documentValid(current.document))fail('EVIDENCE_DOCUMENT','現行來源頁無法核對。');
    const a=link.document,b=current.document;
    if(a.sourceHash!==b.sourceHash||a.page!==b.page||a.pageWidth!==b.pageWidth||a.pageHeight!==b.pageHeight||a.coordinateSpace!==b.coordinateSpace||a.referencePageId!==b.referencePageId)return {status:'source-changed',canConfirm:false};
    if(link.identityBasis==='legacy-v1'){
      if(!current.target)return {status:'target-missing',canConfirm:false};
      if(targetKey(link.target)!==targetKey(current.target)||link.target.definitionPin!==current.target.definitionPin||!options.identityKnown)return {status:'needs-reassociation',canConfirm:false};
      return {status:link.humanConfirmation?'confirmed-content':'unchecked',canConfirm:true};
    }
    /* ledger 不看租約 */
    const verdict=options.identityStatus||'unknown';
    if(verdict==='unknown'||verdict==='conflict')return {status:'needs-reassociation',canConfirm:false};
    if(verdict==='absent'||!current.target)return {status:'target-missing',canConfirm:false};
    if(verdict==='replaced')return {status:'target-replaced',canConfirm:false};
    if(verdict!=='continuous')return {status:'needs-reassociation',canConfirm:false};
    if(current.target.definitionPin!==link.target.definitionPin||current.target.valuePin!==link.target.valuePin)return {status:'target-changed',canConfirm:true};
    const confirmed=!!link.humanConfirmation&&link.humanConfirmation.definitionPin===link.target.definitionPin&&link.humanConfirmation.valuePin===link.target.valuePin;
    return {status:confirmed?'confirmed-content':'unchecked',canConfirm:true};
  }
  function gcd(a,b){let x=a<0n?-a:a,y=b;while(y){const t=y;y=x%y;x=t;}return x;}
  function reduceRational(num,den){const g=gcd(num,den);return {num:(num/g).toString(),den:(den/g).toString()};}
  function parseLiteral(text,unit){
    if(unit!=='mm'&&unit!=='cm')fail('ADOPTION_UNIT','單位必須是 mm 或 cm。');
    const raw=typeof text==='string'?text:'';
    const frac=/^(-?\d+)\/([1-9]\d*)$/.exec(raw),dec=/^(-?\d+)(?:\.(\d+))?$/.exec(raw);
    let num,den;
    if(frac){num=BigInt(frac[1]);den=BigInt(frac[2]);}
    else if(dec){const scale=dec[2]?10n**BigInt(dec[2].length):1n;const whole=BigInt(dec[1]);const part=dec[2]?BigInt(dec[2]):0n;const sign=raw.startsWith('-')?-1n:1n;num=whole*scale+sign*part;den=scale;}
    else fail('ADOPTION_LITERAL','觀察值不是精確有理數。');
    if(unit==='cm'){/* cm 精確乘十 */num*=10n;}
    return reduceRational(num,den);
  }
  function planAdoption(link,live,field){
    /* 採用必須先預覽 */
    if(link?.identityBasis!=='ledger'||link.target?.kind!=='parameter-field')fail('ADOPTION_TARGET','只有身分帳上的參數欄位可以採用。');
    const state=assessBound(link,live,{identityStatus:live?.identityStatus||'unknown'});
    if(live?.identityStatus!=='continuous'||!state.canConfirm)fail('ADOPTION_IDENTITY','身分不是延續，或原圖已不能核對。');
    if(field?.type!=='dimension'||field.formula||!field.rawValue||(field.unit!=='mm'&&field.unit!=='cm'))fail('ADOPTION_FIELD','只能採用尺寸字面值。');
    const value=parseLiteral(field.rawValue,field.unit);
    const literal=value.den==='1'?value.num:`${value.num}/${value.den}`;
    return {ok:true,requiresPreview:true,writesGeometry:false,parameterId:link.target.parameterId,fieldId:link.target.fieldId,literal,value,definitionPinBefore:link.target.definitionPin};
  }
  function sealAdoption(link,receipt){
    if(!receipt||receipt.previewed!==true||receipt.confirmed!==true)fail('ADOPTION_PREVIEW','採用必須先預覽並確認。');
    const plan=planAdoption(link,receipt.live,receipt.field);
    if(receipt.value?.num!==plan.value.num||receipt.value?.den!==plan.value.den)fail('ADOPTION_RATIONAL','原生解析與精確換算不同，已中止。');
    if(!hash(receipt.definitionPinAfter)||!hash(receipt.valuePinAfter)||!iso(receipt.adoptedAt))fail('ADOPTION_RECEIPT','確認回執不完整。');
    const next=clone(link);
    next.target.definitionPin=receipt.definitionPinAfter;next.target.valuePin=receipt.valuePinAfter;
    next.adoption={observation:receipt.observation,literal:plan.literal,value:plan.value,definitionPinBefore:plan.definitionPinBefore,definitionPinAfter:receipt.definitionPinAfter,adoptedAt:receipt.adoptedAt};
    if(next.humanConfirmation){next.humanConfirmation.definitionPin=next.target.definitionPin;next.humanConfirmation.valuePin=next.target.valuePin;}
    validate({schema:SCHEMA_V2,links:[next]});
    return next;
  }
  function linksFor(links,target){
    return links.filter(l=>l.target.projectScope===target.projectScope&&l.target.kind===target.kind&&(target.kind==='parameter-field'?l.target.parameterId===target.parameterId&&(target.fieldId===undefined||l.target.fieldId===target.fieldId):l.target.id===target.id));
  }
  function adoptionSteps(){return Object.freeze(['native-preview','native-confirm','seal-adoption']);}
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
  // Prepare may await only detached, read-only work. Navigation/fit/paint are
  // one synchronous final commit, after every asynchronous stage is guarded.
  function createLocator({prepare,commit,getSourceStamp}){
    if(typeof prepare!=='function'||typeof getSourceStamp!=='function'||typeof commit!=='function'||commit.constructor?.name==='AsyncFunction')fail('EVIDENCE_ADAPTER','定位需要離線準備與同步導航接口。');
    const sourceStamp=d=>{const value=getSourceStamp(d);boundedJSON(value);if(!plain(value))fail('EVIDENCE_ADAPTER','定位來源基準無法確認。');return JSON.stringify(value);};
    return async function locateDocument(document,region,{isCurrent}){
      boundedJSON(document);boundedJSON(region);
      if(!documentValid(document)||!rect(region,document.pageWidth,document.pageHeight)||typeof isCurrent!=='function')fail('EVIDENCE_DOCUMENT','定位頁面或範圍不合法。');
      const d=clone(document),r=clone(region),basis=sourceStamp(d);
      const assertCurrent=()=>{if(!isCurrent()||sourceStamp(d)!==basis)fail('EVIDENCE_STALE','定位已取消或原圖基準已變更。');};
      assertCurrent();const prepared=await prepare(clone(d),clone(r),{assertCurrent});assertCurrent();
      const result=commit(prepared,clone(d),clone(r));
      if(result&&typeof result.then==='function')fail('EVIDENCE_ADAPTER','定位導航接口不能回傳非同步作業。');
      // A successful synchronous navigation may change the project's own
      // revision. Never reclassify that completed navigation as a late reply.
      return result;
    };
  }
  function createController({readFeatureAttachment,setFeatureAttachment,getStamp,readCurrent,locateDocument,getNavigationStamp=()=>null,uuid=()=>crypto.randomUUID(),now=()=>new Date().toISOString(),ledger=null}){
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
    function ledgerTarget(scope,request,read){
      if(read?.assemblyOwned)fail('EVIDENCE_ASSEMBLY','組構所有角材首版不支援。');
      if(request.kind==='parameter-field')return {projectScope:scope,kind:'parameter-field',parameterId:request.parameterId,fieldId:request.fieldId,definitionPin:read.definitionPin,valuePin:read.valuePin,incarnation:read.incarnation};
      if(request.kind==='boundary'||request.kind==='timber')return {projectScope:scope,kind:request.kind,id:request.id,definitionPin:read.definitionPin,valuePin:read.valuePin,incarnation:read.incarnation};
      fail('EVIDENCE_TARGET','請明選邊界、角材或參數欄位。');
    }
    async function addLedger(input){
      boundedJSON(input);if(!keys(input,['document','region','target','observations']))fail('EVIDENCE_INVALID','新增證據欄位不合法。');
      const seq=++sequence;
      await ledger.ensureActive(); /* 有預覽仍啟用 */
      const read=await ledger.readTarget(clone(input.target));boundedJSON(read);
      const s=stamp();let v=bundle();if(v.schema===SCHEMA)v=upgradePackage(v);
      const target=ledgerTarget(s.projectScope,input.target,read);
      const l={evidenceId:uuid(),document:clone(input.document),region:clone(input.region),target,observations:clone(input.observations),humanConfirmation:null,identityBasis:'ledger',adoption:null};
      validate({schema:SCHEMA_V2,links:[l]});if(l.target.projectScope!==s.projectScope)fail('EVIDENCE_SCOPE','目標屬於另一份專案。');
      const c=await current(l,s,seq);if(!assessBound(l,{...c,target},{identityStatus:'continuous'}).canConfirm)fail('EVIDENCE_ASSOCIATION','明選的來源或目標已變更。');
      v.links.push(l);commit(v,s,seq,l);return clone(l);
    }
    async function rebindLedger(evidenceId,target){
      boundedJSON(target);const seq=++sequence;
      await ledger.ensureActive();
      const read=await ledger.readTarget(clone(target));boundedJSON(read);
      const s=stamp();let v=bundle();if(v.schema===SCHEMA)v=upgradePackage(v);const l=find(v,evidenceId);
      l.target=ledgerTarget(s.projectScope,target,read);l.identityBasis='ledger';l.humanConfirmation=null;l.adoption=null;
      validate({schema:SCHEMA_V2,links:[l]});
      const c=await current(l,s,seq);if(!assessBound(l,{...c,target:l.target},{identityStatus:'continuous'}).canConfirm)fail('EVIDENCE_ASSOCIATION','來源或目標已變更，請重新選擇。');
      commit(v,s,seq,l);return clone(l);
    }
    async function add(input){
      if(ledger)return addLedger(input);
      // Do not destructure or stringify caller data until accessors/functions
      // and its complete bounded shape have been rejected without invocation.
      boundedJSON(input);if(!keys(input,['document','region','target','observations']))fail('EVIDENCE_INVALID','新增證據欄位不合法。');
      validate({schema:SCHEMA,links:[{evidenceId:'preflight',...input,humanConfirmation:null}]});
      const {document,region,target,observations}=clone(input);
      const seq=++sequence,s=stamp(),v=bundle(),l={evidenceId:uuid(),document,region,target,observations,humanConfirmation:null};
      validate({schema:SCHEMA,links:[l]});if(l.target.projectScope!==s.projectScope)fail('EVIDENCE_SCOPE','參數欄位屬於另一份專案。');
      const c=await current(l,s,seq),state=assess(l,c,{identityKnown:true});if(!state.canConfirm)fail('EVIDENCE_ASSOCIATION','明選的來源或參數欄位已變更。');v.links.push(l);commit(v,s,seq,l);return clone(l);
    }
    async function readView(){
      const seq=++sequence,s=stamp(),v=bundle();const links=[];
      for(const l of v.links){const c=await current(l,s,seq);const known=leaseKnown(l,s)&&l.target.projectScope===s.projectScope;
        const state=l.identityBasis?assessBound(l,c,{identityKnown:known,identityStatus:c.identityStatus||'unknown'}):assess(l,c,{identityKnown:known});
        links.push({...clone(l),...state,modelValue:clone(c?.modelValue??null)});}guard(s,seq);
      return {stamp:s,links};
    }
    async function setReviewed(evidenceId,checked){
      if(typeof checked!=='boolean')fail('EVIDENCE_CONFIRM','核對狀態不合法。');const seq=++sequence,s=stamp(),v=bundle(),l=find(v,evidenceId);
      const c=await current(l,s,seq);const known=leaseKnown(l,s)&&l.target.projectScope===s.projectScope;
      if(l.identityBasis){
        const state=assessBound(l,c,{identityKnown:known,identityStatus:c.identityStatus||'unknown'});
        if(checked&&!state.canConfirm)fail('EVIDENCE_RECHECK','來源或物件身分不明，請明選後重新關聯。');
        if(checked&&l.identityBasis==='ledger'&&state.status==='target-changed'){l.target.definitionPin=c.target.definitionPin;l.target.valuePin=c.target.valuePin;}
        l.humanConfirmation=checked?{documentHash:l.document.sourceHash,definitionPin:l.target.definitionPin,valuePin:l.target.valuePin,confirmedAt:now()}:null;
        commit(v,s,seq,l);return clone(l);
      }
      if(checked&&!assess(l,c,{identityKnown:known}).canConfirm)fail('EVIDENCE_RECHECK','來源或物件身分不明，請明選欄位重新關聯。');
      l.humanConfirmation=checked?{documentHash:l.document.sourceHash,targetPin:l.target.definitionPin,confirmedAt:now()}:null;
      commit(v,s,seq,known?l:null);return clone(l);
    }
    async function rebind(evidenceId,target){
      if(ledger)return rebindLedger(evidenceId,target);
      boundedJSON(target);const seq=++sequence,s=stamp(),v=bundle(),l=find(v,evidenceId);if(!targetValid(target)||target.projectScope!==s.projectScope)fail('EVIDENCE_SCOPE','請明選本專案的參數欄位。');
      l.target=clone(target);l.humanConfirmation=null;const c=await current(l,s,seq);if(!assess(l,c,{identityKnown:true}).canConfirm)fail('EVIDENCE_ASSOCIATION','來源或參數欄位已變更，請重新選擇。');commit(v,s,seq,l);return clone(l);
    }
    async function locate(evidenceId){
      const seq=++sequence,s=stamp(),l=find(bundle(),evidenceId);
      const navigationStamp=()=>{const value=getNavigationStamp();boundedJSON(value);return JSON.stringify(value);},navigation=navigationStamp();
      const c=await current(l,s,seq),status=(l.identityBasis?assessBound(l,c,{identityStatus:c.identityStatus||'unknown'}):assess(l,c)).status;
      if(navigationStamp()!==navigation)fail('EVIDENCE_STALE','定位期間畫面已變更，未定位。');
      if(['source-missing','source-changed'].includes(status))fail('EVIDENCE_RECHECK','原圖缺失或已換版，請重新核對。');guard(s,seq);
      return locateDocument(clone(l.document),clone(l.region),{isCurrent:()=>seq===sequence&&stable(s,stamp())});
    }
    return {add,readView,setReviewed,rebind,locate,cancel(){++sequence;}};
  }
  return Object.freeze({KIND,SCHEMA,SCHEMA_V2,COORDINATES,MAX_LINKS,MAX_BYTES,empty,validate,references,documentFromReference,targetFromNode,targetKey,assess,assessBound,upgradePackage,identityVerdict,parseLiteral,planAdoption,sealAdoption,linksFor,adoptionSteps,validateSourceClosure,createLocator,createController});
});
