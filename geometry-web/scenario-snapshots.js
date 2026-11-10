/* #46 independent complete snapshots, shared with the formal root catalog. */
(function (root, factory) {
  const api = factory(typeof module === 'object' && module.exports ? require('./project-store.js') : root.GeometryProject, typeof module === 'object' && module.exports ? require('./scenario-catalog.js') : root.GeometryScenarioCatalog);
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.GeometryScenarioSnapshots = api;
})(globalThis, function (defaultProject, Catalog) {
  'use strict';
  const SCHEMA = Catalog.SCHEMA;
  const MB = 1024 * 1024, encoder = new TextEncoder(), decoder = new TextDecoder('utf-8', {fatal:true});
  const LIMITS = Object.freeze({scenarios:8, assets:256, assetBytes:128*MB, manifestBytes:8*MB,
    sceneBytes:16*MB, descriptorBytes:8*MB, expandedBytes:512*MB, archiveBytes:256*MB,
    nodes:1000000, depth:48, origins:25000, objects:25000});
  const HASH = /^[a-f0-9]{64}$/, ID = /^[\w-]{1,100}$/;
  const identifier=v=>typeof v==='string'&&ID.test(v);
  const KINDS = new Set(['boundary','placement','space','column','beam','timber','grid','grid-system','grid-binding',
    'parameter','assembly-rule','assembly-binding','material','method','application','datum','model',
    'engineering-draft','assembly-draft','reference-page','grid-draft','spec','guide','assembly-instance',
    'section-profile','profile-member','profile-run','panel-spec']);
  function fail(code, message) { throw Object.assign(new Error(message), {code}); }
  const exact = (v, required, optional=[]) => v && typeof v === 'object' && !Array.isArray(v) &&
    required.every(k => Object.hasOwn(v,k)) && Object.keys(v).every(k => required.includes(k)||optional.includes(k));
  const copy = v => JSON.parse(JSON.stringify(v));
  function boundedJSON(value, limits=LIMITS, byteLimit=limits.manifestBytes) {
    let nodes=0,bytes=0;
    const visiting=new Set();
    function charge(size) {bytes+=size;if(bytes>byteLimit)fail('LIMIT','Snapshot JSON exceeds byte limits.');}
    function string(v) {
      if(v.length>byteLimit)fail('LIMIT','Snapshot string exceeds limits.');
      charge(2);
      for(let at=0;at<v.length;at++) {
        const c=v.charCodeAt(at);
        if(c<128)charge(c<32?([8,9,10,12,13].includes(c)?2:6):c===34||c===92?2:1);
        else if(c<2048)charge(2);
        else if(c>=0xd800&&c<=0xdbff&&at+1<v.length&&v.charCodeAt(at+1)>=0xdc00&&v.charCodeAt(at+1)<=0xdfff){charge(4);at++;}
        else charge(c>=0xd800&&c<=0xdfff?6:3);
      }
    }
    function walk(v,depth) {
      if (++nodes>limits.nodes || depth>limits.depth) fail('LIMIT','Snapshot JSON exceeds traversal limits.');
      if(v===null){charge(4);return;}
      if(typeof v==='boolean'){charge(v?4:5);return;}
      if(typeof v==='number'&&Number.isFinite(v)){charge(JSON.stringify(v).length);return;}
      if(typeof v==='string'){string(v);return;}
      if (!v || typeof v!=='object' || visiting.has(v)) fail('JSON','Snapshot requires finite plain JSON.');
      const array=Array.isArray(v), proto=Object.getPrototypeOf(v);
      if (array ? proto!==Array.prototype : proto!==Object.prototype&&proto!==null)
        fail('JSON','Snapshot runtime objects are not portable.');
      if (Object.getOwnPropertySymbols(v).length) fail('JSON','Snapshot symbol fields are not portable.');
      const names=Object.getOwnPropertyNames(v);
      if (names.length>limits.nodes || array&&(v.length>limits.nodes||names.length!==v.length+1)) fail('JSON','Snapshot array is incomplete or too large.');
      charge(2);let fields=0;
      visiting.add(v);
      for (const name of names) {
        if (array&&name==='length') continue;
        if(array&&(!/^(0|[1-9][0-9]*)$/.test(name)||Number(name)>=v.length))fail('JSON','Snapshot arrays require dense indices without extra fields.');
        const d=Object.getOwnPropertyDescriptor(v,name);
        if (!d.enumerable||!Object.hasOwn(d,'value')||['__proto__','constructor','prototype','toJSON'].includes(name) || name.length>200)
          fail('JSON','Snapshot accessors, hooks or hidden fields are not portable.');
        if(fields++)charge(1);
        if(!array){string(name);charge(1);}
        walk(d.value,depth+1);
      }
      visiting.delete(v);
    }
    walk(value,0);
    return value;
  }
  function canonical(v) {
    if (v===null||typeof v!=='object') return JSON.stringify(v);
    if (Array.isArray(v)) return '['+v.map(canonical).join(',')+']';
    return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
  }
  const freeze=v=> {if(v&&typeof v==='object') {for(const c of Object.values(v))freeze(c);Object.freeze(v);}return v;};
  const refKey=v=>canonical([v.kind,v.id,v.version]);
  function validObject(v) {
    return exact(v,['kind','id','version'])&&KINDS.has(v.kind)&&
      (typeof v.id==='string'&&v.id.length>0&&v.id.length<=100&&!/[\u0000-\u001f]/.test(v.id)||
        Number.isSafeInteger(v.id)&&v.id>=0&&v.id<=4294967295)&&
      (v.version===null||Number.isSafeInteger(v.version)&&v.version>0);
  }
  const validRef=v=>exact(v,['scenarioId','kind','id','version'])&&identifier(v.scenarioId)&&validObject({kind:v.kind,id:v.id,version:v.version});
  const crcTable=Uint32Array.from({length:256},(_,i)=>{for(let bit=0;bit<8;bit++)i=i&1?0xedb88320^(i>>>1):i>>>1;return i>>>0;});
  function crcUpdate(crc,bytes) {for(const byte of bytes)crc=crcTable[(crc^byte)&255]^(crc>>>8);return crc>>>0;}
  function binaryCopy(value) {
    if(!(value instanceof Uint8Array))fail('ASSET_CLOSURE','Original bytes must be Uint8Array data.');
    const proto=Object.getPrototypeOf(Uint8Array.prototype);
    const buffer=Object.getOwnPropertyDescriptor(proto,'buffer').get.call(value);
    if(typeof SharedArrayBuffer!=='undefined'&&buffer instanceof SharedArrayBuffer)fail('ASSET_CLOSURE','Shared mutable bytes are not portable.');
    const size=Object.getOwnPropertyDescriptor(proto,'byteLength').get.call(value);
    const result=new Uint8Array(size);result.set(value);return result;
  }
  function parseJSON(bytes,limits,limit) {
    if(bytes.length>limit)fail('LIMIT','Archived JSON exceeds byte limits.');
    const text=decoder.decode(bytes);let at=0,nodes=0;
    const whitespace=()=>{while(at<text.length&&[9,10,13,32].includes(text.charCodeAt(at)))at++;};
    function string(key=false) {
      if(text[at]!=='"')fail('JSON','Expected a JSON string.');const start=at++;
      while(at<text.length) {const char=text[at++];if(char==='"')return key?JSON.parse(text.slice(start,at)):null;
        if(char==='\\')at++;}
      fail('JSON','Truncated archived JSON string.');
    }
    function value(depth) {
      if(++nodes>limits.nodes||depth>limits.depth)fail('LIMIT','Archived JSON exceeds traversal limits.');
      whitespace();const char=text[at];
      if(char==='"'){string();return;}
      if(char==='{'||char==='[') {
        const object=char==='{',end=object?'}':']',keys=new Set();at++;whitespace();
        if(text[at]===end){at++;return;}
        for(;;) {
          if(object) {const key=string(true);if(keys.has(key))fail('JSON','Duplicate archived JSON field.');keys.add(key);whitespace();
            if(text[at++]!==':')fail('JSON','Expected JSON field separator.');}
          value(depth+1);whitespace();if(text[at]===end){at++;return;}
          if(text[at++]!==',')fail('JSON','Expected JSON item separator.');whitespace();
        }
      }
      for(const literal of ['true','false','null'])if(text.slice(at,at+literal.length)===literal){at+=literal.length;return;}
      const start=at;while(at<text.length&&/[0-9eE+.-]/.test(text[at]))at++;
      if(at===start)fail('JSON','Invalid archived JSON value.');
    }
    value(0);whitespace();if(at!==text.length)fail('JSON','Trailing archived JSON data.');
    const result=JSON.parse(text);boundedJSON(result,limits,limit);return result;
  }
  function zipDirectory(bytes,limits) {
    const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength), n=bytes.length;
    const sig=(at,s)=>at>=0&&at+4<=n&&view.getUint32(at,true)===s;
    let end=-1;
    for(let at=n-22;at>=Math.max(0,n-65557);at--)if(sig(at,0x06054b50)&&at+22+view.getUint16(at+20,true)===n){end=at;break;}
    if(end<0)fail('ZIP','ZIP end directory is missing or truncated.');
    const count=view.getUint16(end+10,true),size=view.getUint32(end+12,true),start=view.getUint32(end+16,true);
    if(view.getUint16(end+4,true)||view.getUint16(end+6,true)||view.getUint16(end+8,true)!==count||
      count>1+limits.scenarios*2+limits.assets||start+size!==end)fail('ZIP','Multi-disk, ZIP64 or inconsistent ZIP directory.');
    const names=new Map(),ranges=[];let at=start,expanded=0;
    for(let index=0;index<count;index++) {
      if(!sig(at,0x02014b50)||at+46>end)fail('ZIP','ZIP member directory is truncated.');
      const flags=view.getUint16(at+8,true),method=view.getUint16(at+10,true),crc=view.getUint32(at+16,true),compressed=view.getUint32(at+20,true),
        uncompressed=view.getUint32(at+24,true),nameSize=view.getUint16(at+28,true),extra=view.getUint16(at+30,true),
        comment=view.getUint16(at+32,true),local=view.getUint32(at+42,true);
      if(flags&1||![0,8].includes(method)||at+46+nameSize+extra+comment>end||view.getUint16(at+34,true)||
        compressed===0xffffffff||uncompressed===0xffffffff||!sig(local,0x04034b50)||local+30>start)fail('ZIP','Unsupported or invalid ZIP member.');
      const name=decoder.decode(bytes.subarray(at+46,at+46+nameSize));
      if(names.has(name)||!/^(scenarios\.json|scenarios\/[\w-]{1,100}\/(manifest\.json|world\.scene)|assets\/[a-f0-9]{64})$/.test(name))fail('ZIP','Duplicate or unknown ZIP directory member.');
      const localNameSize=view.getUint16(local+26,true),localExtra=view.getUint16(local+28,true);
      if(view.getUint16(local+6,true)!==flags||view.getUint16(local+8,true)!==method||local+30+localNameSize+localExtra+compressed>start||
        decoder.decode(bytes.subarray(local+30,local+30+localNameSize))!==name)fail('ZIP','ZIP local member differs from its directory.');
      if(!(flags&8)&&(view.getUint32(local+14,true)!==crc||view.getUint32(local+18,true)!==compressed||view.getUint32(local+22,true)!==uncompressed))
        fail('ZIP','ZIP local sizes or checksum differ from its directory.');
      let memberEnd=local+30+localNameSize+localExtra+compressed;
      if(flags&8) {
        const descriptor=memberEnd+(sig(memberEnd,0x08074b50)?4:0);
        if(descriptor+12>start||view.getUint32(descriptor,true)!==crc||view.getUint32(descriptor+4,true)!==compressed||view.getUint32(descriptor+8,true)!==uncompressed)
          fail('ZIP','ZIP data descriptor differs from its directory.');
        memberEnd=descriptor+12;
      }
      ranges.push([local,memberEnd]);
      const limit=name==='scenarios.json'?limits.descriptorBytes:name.endsWith('manifest.json')?limits.manifestBytes:name.endsWith('world.scene')?limits.sceneBytes:limits.assetBytes;
      expanded+=uncompressed;if(uncompressed>limit||expanded>limits.expandedBytes)fail('LIMIT','ZIP advertised sizes exceed limits.');
      names.set(name,{size:uncompressed,crc});at+=46+nameSize+extra+comment;
    }
    if(at!==end)fail('ZIP','ZIP directory size is inconsistent.');
    ranges.sort((a,b)=>a[0]-b[0]);let last=0;
    for(const [begin,end]of ranges){if(begin!==last)fail('ZIP','ZIP local members overlap or leave unlisted bytes.');last=end;}
    if(last!==start)fail('ZIP','ZIP local member sizes are inconsistent.');
    return names;
  }
  function strictManifest(m) {
    if (!exact(m,['format','projectId','name','sceneHash','sources','faces'],
      ['models','faceProjections','requiredCapabilities','engineeringDrafts','assemblyDrafts','reconstructionReviews','featureAttachments']))
      fail('MANIFEST','Unknown or incomplete portable project fields.');
    for(const s of m.sources||[]) if(!exact(s,['id','hash','name','type','size','path']))fail('MANIFEST','Unknown source fields.');
    for(const f of m.faces||[]) {
      if(!exact(f,['bid','activePageId','pages']))fail('MANIFEST','Unknown face fields.');
      for(const p of f.pages||[]) {
        if(!exact(p,['id','sourceId','page','imgW','imgH','crop','mmPerPx','x','y','rot','opacity','locked','calibration','reviewRequired','records']))
          fail('MANIFEST','Unknown reference-page fields.');
        if(p.calibration&&!exact(p.calibration,['points','distanceMm','inputValue','inputUnit']))fail('MANIFEST','Unknown calibration fields.');
        for(const r of p.records||[])if(!exact(r,['id','label','location','datum','unit','value']))fail('MANIFEST','Unknown reference observation fields.');
      }
    }
  }
  function create(options={}) {
    const P=options.project||defaultProject, limits={...LIMITS};
    for(const [key,value] of Object.entries(options.limits||{})) {
      if(!Object.hasOwn(limits,key)||!Number.isSafeInteger(value)||value<1||value>limits[key])fail('LIMIT','Limits may only be lowered.');
      limits[key]=value;
    }
    if(!P||typeof P.validate!=='function'||typeof P.projectFormat!=='function'||typeof P.sha!=='function'||typeof options.verifyProject!=='function')
      fail('MISSING_CAPABILITY','Complete snapshots require the project/scene format validator and an isolated native/model verifier.');
    const snapshots=new Map(), pool=new Map();
    let generation=0;
    function state() {
      if(!options.getState)return null;
      const s=options.getState();
      if(!s||!s.context||!s.frame||typeof s.contextToken!=='string'||!s.contextToken||
        !Number.isSafeInteger(s.revision)||s.revision<0||s.blocked!==false)
        fail('CONTEXT','Project capture is blocked or has no reliable context stamp.');
      return {...s};
    }
    function start() {return {generation:++generation,stamp:state()};}
    function guard(op) {
      if(op.generation!==generation)fail('STALE','Snapshot operation was cancelled or superseded.');
      const s=state(), before=op.stamp;
      if(before&&['context','frame','contextToken','revision','blocked'].some(k=>s[k]!==before[k]))
        fail('CONTEXT','Project changed while the snapshot was being verified.');
    }
    async function digest(v,op) {const hash=await P.sha(v);guard(op);if(!HASH.test(hash))fail('HASH','Invalid digest receipt.');return hash;}
    function validateManifest(m,scene) {
      boundedJSON(m,limits);strictManifest(m);
      if(Object.hasOwn(m,'featureAttachments')) {
        if(!options.featureAttachments)fail('MISSING_CAPABILITY','Feature attachment validator/reference dispatch is not connected; complete capture refused.');
        options.featureAttachments.validate(m.featureAttachments);
        const refs=options.featureAttachments.references(m.featureAttachments);
        if(!Array.isArray(refs)||refs.some(id=>!HASH.test(id)||!m.sources.some(s=>s.id===id)))
          fail('ASSET_CLOSURE','Feature attachment original assets are missing from the manifest.');
      }
      P.validate(m);
      // Reuse the reader's scene-dependent format selector without repacking:
      // pack() would upgrade the format and silently normalize the original data.
      // P.validate already checks registered formats and manifest-only requirements.
      const formats=P.supportedFormats||[P.FORMAT,P.MODEL_FORMAT,P.PROJECTION_FORMAT,P.TIMBER_FORMAT,P.ENGINEERING_FORMAT,
        P.PARAMETER_FORMAT,P.ASSEMBLY_FORMAT,P.GENERATION_FORMAT,P.OUTLINE_FORMAT,P.FEATURE_FORMAT].filter(v=>v!==undefined);
      const minimum=P.projectFormat({...m,requiredCapabilities:[]},scene),actualRank=formats.indexOf(m.format),minimumRank=formats.indexOf(minimum);
      if(actualRank<0||minimumRank<0)fail('MISSING_CAPABILITY','Reader scene-dependent format ordering is unavailable.');
      if(actualRank<minimumRank)fail('FORMAT','Project format is below the reader requirement for its complete scene and definitions.');
      if(typeof P.sceneCapabilities==='function') {
        const required=P.sceneCapabilities(scene);
        if(required.some(c=>!m.requiredCapabilities?.includes(c)))fail('CAPABILITY','Scene capabilities were stripped from the project manifest.');
      }
    }
    function sourceCopy(project) {
      if(!exact(project,['manifest','scene','sources']))fail('PROJECT','Capture requires a complete project.');
      for(const key of ['manifest','scene','sources']) {
        const d=Object.getOwnPropertyDescriptor(project,key);
        if(!d?.enumerable||!Object.hasOwn(d,'value'))fail('JSON','Project accessors are not portable.');
      }
      if(Object.getOwnPropertySymbols(project).length||Object.getOwnPropertyNames(project).length!==3||typeof project.scene!=='string'||project.scene.includes('\0'))
        fail('PROJECT','Capture requires a complete manifest, scene and original source bytes.');
      if(encoder.encode(project.scene).length>limits.sceneBytes)fail('LIMIT','Scene exceeds snapshot limits.');
      validateManifest(project.manifest,project.scene);
      if(!(project.sources instanceof Map)||Object.getPrototypeOf(project.sources)!==Map.prototype||Object.getOwnPropertyNames(project.sources).length||
        Object.getOwnPropertySymbols(project.sources).length||project.sources.size!==project.manifest.sources.length||project.sources.size>limits.assets)
        fail('ASSET_CLOSURE','Original source byte inventory is incomplete or contains unlisted data.');
      const sources=new Map();let bytes=0;
      for(const meta of project.manifest.sources) {
        const input=project.sources.get(meta.id);
        if(!(input instanceof Uint8Array))fail('ASSET_CLOSURE','Missing original source bytes.');
        const length=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(Uint8Array.prototype),'byteLength').get.call(input);
        if(length>limits.assetBytes)fail('LIMIT','Original asset exceeds snapshot byte limits.');
        if(length!==meta.size)
          fail('ASSET_CLOSURE','Missing, mutable-shared or incorrectly sized original source bytes.');
        bytes+=length;if(bytes>limits.expandedBytes)fail('LIMIT','Assets exceed expanded limits.');
        sources.set(meta.id,binaryCopy(input));
      }
      return {manifest:copy(project.manifest),scene:project.scene,sources};
    }
    async function verified(project,op) {
      const data=sourceCopy(project);guard(op);
      if(await digest(encoder.encode(data.scene),op)!==data.manifest.sceneHash)fail('TAMPER','Scene hash does not match the complete project.');
      for(const s of data.manifest.sources)if(await digest(data.sources.get(s.id),op)!==s.hash)fail('TAMPER','Original asset bytes do not match their content address.');
      // Callback receives values; retaining or modifying its arguments cannot change our archive.
      const receipt=await options.verifyProject({manifest:copy(data.manifest),scene:data.scene});guard(op);
      boundedJSON(receipt,limits,limits.descriptorBytes);
      if(receipt?.ok!==true||!Array.isArray(receipt.capabilities)||!receipt.final_objects)
        fail('NATIVE','Isolated native/model verification did not succeed.');
      P.validateProjectObjectRefs(data.manifest,receipt.final_objects);
      // A current native may offer capabilities beyond this portable reader.
      // Negotiate declared requirements without altering the native receipt;
      // missing native requirements still cannot be supplied by the reader.
      const declared=data.manifest.requiredCapabilities||[];
      const available=typeof P.readerCapabilities==='function'?
        P.readerCapabilities(receipt.capabilities.filter(c=>declared.includes(c)),{cutting:true}):receipt.capabilities;
      for(const c of data.manifest.requiredCapabilities||[])if(!available.includes(c))fail('CAPABILITY','Native/reader capability is unavailable: '+c);
      const objects=[];
      for(const v of receipt.objects||[])objects.push(copy(v));
      for(const id of receipt.final_objects.boundaries)objects.push({kind:'boundary',id,version:null});
      for(const p of receipt.final_objects.placements)objects.push({kind:'placement',id:p.id,version:null});
      for(const m of data.manifest.models||[])objects.push({kind:'model',id:m.id,version:null});
      for(const [field,kind] of [['engineeringDrafts','engineering-draft'],['assemblyDrafts','assembly-draft']])
        for(const d of data.manifest[field]?.records||[])objects.push({kind,id:d.id,version:null});
      for(const f of data.manifest.faces)for(const p of f.pages)objects.push({kind:'reference-page',id:p.id,version:null});
      if(data.manifest.featureAttachments&&typeof options.featureAttachments.objects==='function')
        objects.push(...options.featureAttachments.objects(copy(data.manifest.featureAttachments)));
      const unique=new Map();
      for(const v of objects) {if(!validObject(v))fail('NATIVE','Invalid typed object inventory.');unique.set(refKey(v),v);}
      if(unique.size>limits.objects)fail('LIMIT','Typed object inventory exceeds limits.');
      return {...data,objects:[...unique.values()].sort((a,b)=>refKey(a).localeCompare(refKey(b)))};
    }
    function validateRecord(s,table) {
      boundedJSON({...s,snapshot:{...s.snapshot,worldScene:''}},limits,limits.manifestBytes);
      Catalog.validateRecord(s,table,limits);
    }
    async function seal(data,settings,op) {
      boundedJSON(settings,limits,limits.descriptorBytes);
      if(!exact(settings,['scenarioId','label'],['basis','originMapping'])||!identifier(settings.scenarioId)||typeof settings.label!=='string'||
        !settings.label.trim()||settings.label.length>200)fail('SCENARIO','Choose a unique scenario namespace and label.');
      const value={scenarioId:settings.scenarioId,label:settings.label,basis:copy(settings.basis||null),
        snapshot:{projectManifest:data.manifest,worldScene:data.scene,assetHashes:data.manifest.sources.map(s=>s.id).sort()},
        originMapping:copy(settings.originMapping||[]),objects:data.objects,
        requiredCapabilities:[...(data.manifest.requiredCapabilities||[])].sort()};
      // The complete comparison metadata has one budget; scene text has its own.
      boundedJSON({...value,closureHash:'0'.repeat(64),snapshot:{...value.snapshot,worldScene:''}},limits,limits.manifestBytes);
      value.closureHash=await digest(encoder.encode(canonical(value)),op);
      validateRecord(value,snapshots);return freeze(value);
    }
    function expanded(table,assets) {
      let total=0;
      for(const s of table.values())total+=encoder.encode(JSON.stringify(s)).length;
      for(const b of assets.values())total+=b.length;
      if(total>limits.expandedBytes)fail('LIMIT','Complete archive exceeds expanded limits.');
    }
    function commit(s,data,op,replace=false) {
      guard(op);
      if(!replace&&snapshots.has(s.scenarioId))fail('SCENARIO','Scenario namespace already exists.');
      const next=new Map(snapshots);next.set(s.scenarioId,s);
      if(next.size>limits.scenarios)fail('LIMIT','Too many complete scenarios.');
      const assets=new Map(pool);
      for(const [hash,bytes]of data.sources)if(!assets.has(hash))assets.set(hash,Uint8Array.from(bytes));
      const retained=new Set([...next.values()].flatMap(v=>v.snapshot.assetHashes));
      for(const hash of assets.keys())if(!retained.has(hash))assets.delete(hash);
      if(assets.size>limits.assets)fail('LIMIT','Too many original assets.');
      for(const v of next.values())validateRecord(v,next);
      expanded(next,assets);guard(op);
      snapshots.clear();for(const [id,v]of next)snapshots.set(id,v);
      pool.clear();for(const [hash,bytes]of assets)pool.set(hash,bytes);
      return copy(s);
    }
    async function captureCopy(project,settings,copyOrigin=null) {
      boundedJSON(settings,limits,limits.descriptorBytes);boundedJSON(copyOrigin,limits,limits.descriptorBytes);
      // Own every option before state callbacks or verification can yield.
      // Only the private fork path can supply the separate origin envelope.
      const combinedSettings={...settings,basis:copyOrigin?.basis||null,originMapping:copyOrigin?.originMapping||[]};
      boundedJSON(combinedSettings,limits,limits.descriptorBytes);
      const ownedSettings=freeze(copy(combinedSettings));
      const op=start();
      if(snapshots.size>=limits.scenarios)fail('LIMIT','Too many complete scenarios.');
      const data=await verified(project,op);const s=await seal(data,ownedSettings,op);return commit(s,data,op);}
    async function capture(project,settings) {
      boundedJSON(settings,limits,limits.descriptorBytes);
      if(!exact(settings,['scenarioId','label']))fail('ORIGIN','Only an explicit archived fork can establish a copy basis and typed origins.');
      return captureCopy(project,freeze(copy(settings)));
    }
    function project(id) {
      const s=snapshots.get(id);if(!s)fail('SCENARIO','Scenario does not exist.');
      return {manifest:copy(s.snapshot.projectManifest),scene:s.snapshot.worldScene,
        sources:new Map(s.snapshot.assetHashes.map(h=>[h,Uint8Array.from(pool.get(h))]))};
    }
    async function fork(id,settings) {
      const base=snapshots.get(id);if(!base)fail('SCENARIO','Copy basis does not exist.');
      boundedJSON(settings,limits,limits.descriptorBytes);
      if(!exact(settings,['scenarioId','label']))fail('SCENARIO','Fork requires a new namespace and label.');
      const ownedSettings=freeze(copy(settings));
      const originMapping=base.objects.map(v=>({from:{scenarioId:id,...v},to:{scenarioId:ownedSettings.scenarioId,...v},snapshotHash:base.closureHash}));
      return captureCopy(project(id),ownedSettings,{basis:{scenarioId:id,snapshotHash:base.closureHash},originMapping});
    }
    async function replace(id,input) {
      const old=snapshots.get(id);if(!old)fail('SCENARIO','Scenario does not exist.');
      const op=start(),data=await verified(input,op);
      if(data.manifest.projectId!==old.snapshot.projectManifest.projectId)
        fail('PROJECT_IDENTITY','A foreign project must be captured in a new scenario namespace.');
      // A validated whole replacement proves content, not object incarnation
      // continuity. Same kind/id/version after reset or recreation is insufficient.
      // Keep the historical basis, but only an explicit fork creates copy origins.
      const originMapping=[];
      const s=await seal(data,{scenarioId:id,label:old.label,basis:old.basis,originMapping},op);return commit(s,data,op,true);
    }
    function remove(id) {
      if(!snapshots.has(id))return false;
      if([...snapshots.values()].some(s=>s.basis?.scenarioId===id))fail('RETENTION','A retained scenario still uses this exact copy basis.');
      generation++;snapshots.delete(id);
      const retained=new Set([...snapshots.values()].flatMap(s=>s.snapshot.assetHashes));
      for(const hash of pool.keys())if(!retained.has(hash))pool.delete(hash);
      return true;
    }
    async function pack(zip) {
      const op=start(),files=Object.create(null),records=[];
      for(const s of snapshots.values()) {
        const {snapshot,...meta}=s;
        records.push({...meta,assetHashes:snapshot.assetHashes});
        files['scenarios/'+s.scenarioId+'/manifest.json']=encoder.encode(JSON.stringify(snapshot.projectManifest));
        files['scenarios/'+s.scenarioId+'/world.scene']=encoder.encode(snapshot.worldScene);
      }
      const descriptor={schema:SCHEMA,scenarios:records,assets:[...pool.keys()].sort()};
      boundedJSON(descriptor,limits,limits.descriptorBytes);files['scenarios.json']=encoder.encode(JSON.stringify(descriptor));
      for(const [hash,bytes]of pool)files['assets/'+hash]=Uint8Array.from(bytes);
      let total=0;for(const bytes of Object.values(files))total+=bytes.length;
      if(total>limits.expandedBytes)fail('LIMIT','ZIP expanded input exceeds limits.');
      const bytes=await new Promise((resolve,reject)=>zip.zip(files,{level:0},(e,b)=>e?reject(e):resolve(b)));guard(op);
      if(bytes.length>limits.archiveBytes)fail('LIMIT','ZIP archive exceeds limits.');return bytes;
    }
    async function unpack(bytes,zip) {
      const op=start();
      if(!(bytes instanceof Uint8Array))fail('LIMIT','Invalid scenario ZIP bytes.');
      const length=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(Uint8Array.prototype),'byteLength').get.call(bytes);
      if(length>limits.archiveBytes)fail('LIMIT','Scenario ZIP exceeds limits.');
      // Copy compressed input before decoder callbacks or await can expose caller mutation.
      bytes=binaryCopy(bytes);const expectedNames=zipDirectory(bytes,limits);
      const files=Object.create(null);let total=0,count=0;
      await new Promise((resolve,reject)=> {
        let pending=0,ended=false,failed=false;const active=new Set();
        const die=e=>{if(failed)return;failed=true;for(const file of active)file.terminate?.();reject(e);};
        const done=()=>{if(ended&&pending===0&&!failed)resolve();};
        const unzip=new zip.Unzip(file=> {
          if(failed)return;
          if(++count>1+limits.scenarios*2+limits.assets||Object.hasOwn(files,file.name)||
            !/^(scenarios\.json|scenarios\/[\w-]{1,100}\/(manifest\.json|world\.scene)|assets\/[a-f0-9]{64})$/.test(file.name))
            return die(Object.assign(new Error('Duplicate or unknown ZIP member.'),{code:'ZIP'}));
          files[file.name]=null;pending++;active.add(file);let size=0,crc=0xffffffff;const chunks=[];
          const limit=file.name==='scenarios.json'?limits.descriptorBytes:file.name.endsWith('manifest.json')?limits.manifestBytes:file.name.endsWith('world.scene')?limits.sceneBytes:limits.assetBytes;
          file.ondata=(err,data,final)=> {
            if(failed)return;if(err)return die(err);size+=data.length;total+=data.length;
            if(size>limit||total>limits.expandedBytes)return die(Object.assign(new Error('Expanded ZIP exceeds limits.'),{code:'LIMIT'}));
            crc=crcUpdate(crc,data);chunks.push(Uint8Array.from(data));
            if(final) {
              const expected=expectedNames.get(file.name);
              if(!expected||size!==expected.size||((crc^0xffffffff)>>>0)!==expected.crc)return die(Object.assign(new Error('ZIP emitted size/checksum differs from its directory.'),{code:'ZIP'}));
              const value=new Uint8Array(size);let at=0;for(const chunk of chunks){value.set(chunk,at);at+=chunk.length;}
              files[file.name]=value;active.delete(file);pending--;done();}
          };file.start();
        });unzip.register(zip.UnzipInflate);
        try {for(let at=0;at<bytes.length&&!failed;at+=65536)unzip.push(bytes.subarray(at,at+65536),at+65536>=bytes.length);
          if(!bytes.length)unzip.push(bytes,true);ended=true;
          if(pending&&!failed)die(Object.assign(new Error('Truncated ZIP member.'),{code:'ZIP'}));else done();}catch(e){die(e);}
      });guard(op);
      if(Object.keys(files).length!==expectedNames.size||Object.keys(files).some(name=>!expectedNames.has(name)))fail('ZIP','ZIP stream differs from its directory.');
      function json(name,limit) {
        if(!files[name])fail('ZIP','Complete scenario ZIP member is missing: '+name);
        return parseJSON(files[name],limits,limit);
      }
      const descriptor=json('scenarios.json',limits.descriptorBytes);
      if(!exact(descriptor,['schema','scenarios','assets'])||descriptor.schema!==SCHEMA||!Array.isArray(descriptor.scenarios)||
        descriptor.scenarios.length>limits.scenarios||!Array.isArray(descriptor.assets)||descriptor.assets.length>limits.assets||
        !descriptor.assets.every(h=>HASH.test(h))||new Set(descriptor.assets).size!==descriptor.assets.length)
        fail('SCHEMA','Unsupported or invalid independent scenario archive.');
      const next=new Map(),assets=new Map();
      for(const h of descriptor.assets) {const b=files['assets/'+h];if(!b||b.length>limits.assetBytes||await digest(b,op)!==h)fail('TAMPER','Original archived asset is missing or altered.');assets.set(h,b);}
      for(const meta of descriptor.scenarios) {
        if(!exact(meta,['scenarioId','label','basis','originMapping','objects','requiredCapabilities','closureHash','assetHashes'])||!identifier(meta.scenarioId)||next.has(meta.scenarioId))fail('SCENARIO','Duplicate or invalid scenario namespace.');
        const prefix='scenarios/'+meta.scenarioId+'/',manifest=json(prefix+'manifest.json',limits.manifestBytes);
        if(!files[prefix+'world.scene']||!Array.isArray(meta.assetHashes)||meta.assetHashes.some(h=>!assets.has(h)))fail('ASSET_CLOSURE','Scenario closure is incomplete.');
        const input={manifest,scene:decoder.decode(files[prefix+'world.scene']),sources:new Map(meta.assetHashes.map(h=>[h,assets.get(h)]))};
        const data=await verified(input,op);
        if(canonical(meta.objects)!==canonical(data.objects))fail('TAMPER','Typed object inventory differs from isolated verification.');
        const {assetHashes,...record}=meta,s={...record,snapshot:{projectManifest:data.manifest,worldScene:data.scene,assetHashes}};
        boundedJSON({...s,snapshot:{...s.snapshot,worldScene:''}},limits,limits.manifestBytes);
        const {closureHash,...content}=s;
        if(await digest(encoder.encode(canonical(content)),op)!==closureHash)fail('TAMPER','Complete scenario closure hash does not match.');
        next.set(s.scenarioId,freeze(s));
      }
      const retained=new Set([...next.values()].flatMap(s=>s.snapshot.assetHashes));
      if(retained.size!==assets.size||[...assets.keys()].some(h=>!retained.has(h))||Object.keys(files).length!==1+next.size*2+assets.size)
        fail('ASSET_CLOSURE','Archive contains unlisted or unretained members.');
      for(const s of next.values())validateRecord(s,next);
      // Basis graph must be acyclic even if an attacker recomputes every digest.
      for(const s of next.values()) {const seen=new Set([s.scenarioId]);let basis=s.basis;while(basis) {if(seen.has(basis.scenarioId))fail('ORIGIN','Cyclic scenario copy basis.');seen.add(basis.scenarioId);basis=next.get(basis.scenarioId).basis;}}
      expanded(next,assets);guard(op);
      snapshots.clear();for(const [id,s]of next)snapshots.set(id,s);
      pool.clear();for(const [h,b]of assets)pool.set(h,Uint8Array.from(b));
      return list();
    }
    function list() {return [...snapshots.values()].map(copy);}
    return Object.freeze({capture,fork,replace,remove,project,pack,unpack,list,
      cancel:()=>{generation++;},stats:()=>({scenarios:snapshots.size,assets:pool.size,assetBytes:[...pool.values()].reduce((n,b)=>n+b.length,0)})});
  }
  return {SCHEMA,LIMITS,create,boundedJSON,canonical};
});
