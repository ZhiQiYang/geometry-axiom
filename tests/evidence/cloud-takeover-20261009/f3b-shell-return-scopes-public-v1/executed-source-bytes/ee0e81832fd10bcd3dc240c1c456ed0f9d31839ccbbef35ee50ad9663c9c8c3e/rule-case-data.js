/* Closed portable #49 data. Native predicates are verified by the core adapter. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.GeometryRuleCaseData=api;})(globalThis,()=>{
  'use strict';
  const KIND='rule-cases',SCHEMA='rule-case-workbench-data/1',MAX_BYTES=8*1024*1024;
  const IDS=Object.freeze(['same-role-distinct-members','one-local-joint-new-version','wrong-type-dimension-reference','legal-rule','legal-incomplete-binding','fixed-version-immutable']);
  const STATUSES=['not-run','missing-capability','blocked','timeout','crashed','failed','passed','stale','unknown-runtime'];
  const encoder=new TextEncoder(),own=(v,k)=>Object.hasOwn(v,k),fail=()=>{throw new Error('規則案例的版本、欄位、來源或容量不合法。');};
  const check=ok=>{if(!ok)fail();}, obj=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
  function shape(v,required,optional=[]){check(obj(v)&&required.every(k=>own(v,k))&&Object.keys(v).every(k=>required.includes(k)||optional.includes(k)));}
  const text=(v,max=96,min=1,controls=false)=>check(typeof v==='string'&&encoder.encode(v).length>=min&&encoder.encode(v).length<=max&&(controls||!/[\x00-\x1f\x7f-\x9f]/.test(v)));
  const uint=(v,min=0,max=4294967295)=>check(Number.isSafeInteger(v)&&v>=min&&v<=max);
  const num=(v,min,max)=>check(typeof v==='number'&&Number.isFinite(v)&&v>=min&&v<=max);
  const hash=v=>check(typeof v==='string'&&/^[a-f0-9]{64}$/.test(v));
  const ident=v=>check(typeof v==='string'&&/^[A-Za-z0-9_-]{1,64}$/.test(v));
  const array=(v,max,min=0)=>check(Array.isArray(v)&&v.length>=min&&v.length<=max);
  const canonical=v=>v===null||typeof v!=='object'?JSON.stringify(v):Array.isArray(v)?'['+v.map(canonical).join(',')+']':'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
  function bounded(v,maxBytes=MAX_BYTES,maxNodes=600000,maxDepth=40,integer=false){
    const stack=[{v,d:0}],seen=new Set();let nodes=0,bytes=0;
    while(stack.length){const f=stack.pop(),x=f.v;if(f.exit){seen.delete(x);continue;}
      check(++nodes<=maxNodes&&f.d<=maxDepth);
      if(x===null||typeof x==='boolean')bytes+=x===null?4:x?4:5;
      else if(typeof x==='string'){check(!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(x));bytes+=encoder.encode(JSON.stringify(x)).length;}
      else if(typeof x==='number'){check(Number.isFinite(x)&&(!integer||Number.isSafeInteger(x)));bytes+=JSON.stringify(x).length;}
      else {check(obj(x)||Array.isArray(x));const proto=Object.getPrototypeOf(x),ctor=proto&&Object.getOwnPropertyDescriptor(proto,'constructor')?.value;
        check(proto===null||typeof ctor==='function'&&ctor.prototype===proto&&Function.prototype.toString.call(ctor)===Function.prototype.toString.call(Array.isArray(x)?Array:Object));
        check(!seen.has(x)&&!Object.getOwnPropertySymbols(x).length);seen.add(x);stack.push({v:x,exit:true});
        const keys=Object.getOwnPropertyNames(x).filter(k=>!Array.isArray(x)||k!=='length');check(!Array.isArray(x)||keys.length===x.length);
        bytes+=2+Math.max(0,keys.length-1);
        for(let i=keys.length-1;i>=0;i--){const k=keys[i],d=Object.getOwnPropertyDescriptor(x,k);check(d.enumerable&&own(d,'value')&&(!Array.isArray(x)||k===String(i)));
          if(!Array.isArray(x)){check(!['__proto__','constructor','prototype'].includes(k));bytes+=encoder.encode(JSON.stringify(k)).length+1;check(++nodes<=maxNodes);}stack.push({v:d.value,d:f.d+1});}
      }check(bytes<=maxBytes);
    }return bytes;
  }
  function caps(v,max=16){array(v,max);check(new Set(v).size===v.length);for(const c of v)check(typeof c==='string'&&/^[A-Za-z0-9][A-Za-z0-9._/-]{0,95}$/.test(c));}
  function ref(v,record=false,diagnostic=false){
    shape(v,['kind','id'],['version',...(diagnostic?['fieldId','slotId','axis']:[])]);check((record?['rule','binding']:['rule','binding','parameter','material']).includes(v.kind));
    if(v.kind==='material')ident(v.id);else uint(v.id,v.kind==='parameter'?0:1);
    if(['rule','material'].includes(v.kind))uint(v.version,1);else check(!own(v,'version'));
    if(own(v,'fieldId')){check(v.kind==='parameter');uint(v.fieldId);}
    if(own(v,'slotId')){check(['rule','binding'].includes(v.kind));uint(v.slotId,1);}
    if(own(v,'axis')){check(v.kind==='binding'&&own(v,'slotId')&&['A','B'].includes(v.axis));}
  }
  function source(v){if(v===null)return;check(obj(v));
    if(v.kind==='literal'){shape(v,['kind','value']);check(Number.isSafeInteger(v.value));num(v.value,-1e8,1e8);}
    else if(v.kind==='parameter'){shape(v,['kind','parameterId','fieldId']);uint(v.parameterId);uint(v.fieldId);}
    else if(v.kind==='material'){shape(v,['kind','id','version','field']);ident(v.id);uint(v.version,1);check(['A','B','width','length'].includes(v.field));}else fail();
  }
  function joint(v){check(obj(v));const end=v.kind==='end-to-side';check(end||v.kind==='ortho-split');
    shape(v,['id','kind','scope','side','dir',...(end?['terminatedMember','targetMember','end']:['continuousMember','splitMembers'])]);
    uint(v.id,1);text(v.scope,64);check(['+u','-u','+v','-v'].includes(v.side)&&['u','v'].includes(v.dir));
    if(end){uint(v.terminatedMember,1);uint(v.targetMember,1);check(['start','finish'].includes(v.end));}
    else{uint(v.continuousMember,1);array(v.splitMembers,2,2);v.splitMembers.forEach(x=>uint(x,1));}
  }
  function expression(v){let count=0;function visit(x){check(++count<=128&&obj(x));
    if(x.op==='literal'){shape(x,['op','num','den','unit']);for(const k of ['num','den']){check(typeof x[k]==='string'&&/^-?\d{1,20}$/.test(x[k]));check(BigInt(x[k])>=-9223372036854775808n&&BigInt(x[k])<=9223372036854775807n);}check(['mm','1'].includes(x.unit));}
    else if(x.op==='ref'){shape(x,['op','parameterId','fieldId']);uint(x.parameterId);uint(x.fieldId);}
    else{check(['neg','add','sub','mul','div'].includes(x.op));shape(x,x.op==='neg'?['op','left']:['op','left','right']);visit(x.left);if(x.op!=='neg')visit(x.right);}}
    visit(v);check(encoder.encode(canonical(v)).length<=2047);
  }
  function operation(v){shape(v,['op','value']);const x=v.value;check(obj(x));
    if(v.op==='publish-rule'){
      shape(x,['id','version','name','slots','members','joints']);uint(x.id,1);uint(x.version,1);text(x.name);array(x.slots,8,1);array(x.members,12,1);array(x.joints,16,1);
      for(const s of x.slots){shape(s,['id','name']);uint(s.id,1);text(s.name);}for(const m of x.members){shape(m,['id','slotId']);uint(m.id,1);uint(m.slotId,1);}x.joints.forEach(joint);
      check(encoder.encode(canonical(x)).length<=8191);
    }else if(['create-binding','put-binding'].includes(v.op)){
      shape(x,['id','name','rule','slots']);uint(x.id,1);text(x.name);shape(x.rule,['id','version']);uint(x.rule.id,1);uint(x.rule.version,1);array(x.slots,8,1);
      for(const s of x.slots){shape(s,['slotId','A','B','contactFace','orientation']);uint(s.slotId,1);source(s.A);source(s.B);check([null,'A','B'].includes(s.contactFace)&&[null,'A','B'].includes(s.orientation));}check(encoder.encode(canonical(x)).length<=8191);
    }else if(v.op==='put-parameter'){
      shape(x,['id','name','fields'],['nextFieldId']);uint(x.id);text(x.name);if(own(x,'nextFieldId'))uint(x.nextFieldId);array(x.fields,16,1);
      for(const f of x.fields){shape(f,['id','name','type'],['input','expression']);uint(f.id);text(f.name);check(['dimension','count','ratio'].includes(f.type)&&own(f,'input')!==own(f,'expression'));
        if(own(f,'expression'))expression(f.expression);else{text(f.input,2047,0,true);let rest=f.input.replace(/\s+|@\d{1,10}:\d{1,10}|(?:\d+(?:\.\d*)?|\.\d+)|mm|[=＝()+\-−*×/÷]/g,'');check(rest==='');}}
      check(encoder.encode(canonical(x)).length<=65536);
    }else if(v.op==='publish-material'){
      const timber=x.kind==='timber';check(timber||x.kind==='panel');shape(x,['id','version','kind','name',...(timber?['A','B']:['width','length'])],['brand','model','notes',...(timber?[]:['thickness'])]);ident(x.id);uint(x.version,1);text(x.name);
      for(const k of timber?['A','B']:['width','length']){check(Number.isSafeInteger(x[k]));num(x[k],-1e8,1e8);}for(const k of ['brand','model','notes','thickness'])if(own(x,k)&&x[k]!==null)text(x[k],k==='thickness'?127:191,0);
      check(encoder.encode(canonical(x)).length<=1023);
    }else fail();
  }
  function assertion(v){check(obj(v));
    if(v.kind==='rejection_world_unchanged')shape(v,['kind']);
    else if(v.kind==='joint_tuple_equal'){shape(v,['kind','before','after']);for(const side of [v.before,v.after]){shape(side,['ref','jointId']);ref(side.ref,true);check(side.ref.kind==='rule');uint(side.jointId,1);}}
    else{const fields={record_exists:[],member_slot:['memberId','slotId'],joint_tuple:['jointId','value'],complete_flag:['value'],exact_typed_ref:['slotId','axis','value'],record_pin_unchanged:[]}[v.kind];check(fields!==undefined);shape(v,['kind','ref',...fields]);ref(v.ref,true);
      if(v.kind==='member_slot'){check(v.ref.kind==='rule');uint(v.memberId,1);uint(v.slotId,1);}if(v.kind==='joint_tuple'){check(v.ref.kind==='rule');uint(v.jointId,1);joint(v.value);check(v.value.id===v.jointId);}
      if(v.kind==='complete_flag')check(v.ref.kind==='binding'&&typeof v.value==='boolean');if(v.kind==='exact_typed_ref'){check(v.ref.kind==='binding'&&['A','B'].includes(v.axis));uint(v.slotId,1);source(v.value);}}
  }
  function expected(v){shape(v,['outcome','diagnostic']);check(['accepted','rejected'].includes(v.outcome));if(v.outcome==='accepted')check(v.diagnostic===null);else{shape(v.diagnostic,['code','clause','ref']);text(v.diagnostic.code,64);text(v.diagnostic.clause,64);ref(v.diagnostic.ref,false,true);}}
  function closure(v){
    const records=new Map(),setup=new Set(),refs=[],required=new Set(),key=r=>canonical([r.kind,r.id,r.version??null]);
    const add=(r,selector=null,target=null)=>refs.push([key(r),selector,target]);
    const src=s=>{if(s?.kind==='parameter'){add({kind:'parameter',id:s.parameterId},'field',s.fieldId);required.add('parameters/1');}if(s?.kind==='material'){add({kind:'material',id:s.id,version:s.version},'material_field',s.field);required.add('engineering-spec/1');}};
    const expr=x=>{if(x.op==='ref')add({kind:'parameter',id:x.parameterId},'field',x.fieldId);if(x.left)expr(x.left);if(x.right)expr(x.right);};
    const verify=()=>{for(const [id,selector,target] of refs){const values=records.get(id);check(values?.length>0);if(selector){const field={field:'fields',slot:'slots',member:'members',joint:'joints'}[selector];check(values.some(x=>selector==='material_field'?own(x,target):x[field]?.some(i=>(selector==='slot'&&JSON.parse(id)[0]==='binding'?i.slotId:i.id)===target)));}}};
    for(const stage of ['setup','transaction']){
      for(const op of v.input[stage]){const x=op.value,kind={'publish-rule':'rule','create-binding':'binding','put-binding':'binding','put-parameter':'parameter','publish-material':'material'}[op.op],r={kind,id:x.id,...(['rule','material'].includes(kind)?{version:x.version}:{})},id=key(r);
        if(stage==='setup'){check(!setup.has(id));setup.add(id);}records.set(id,[...(records.get(id)||[]),x]);
        if(['rule','binding'].includes(kind))required.add('assembly-rule-authoring/1');if(kind==='material')required.add('engineering-spec/1');if(kind==='parameter')required.add('parameters/1');
        if(kind==='binding'){add({kind:'rule',...x.rule});for(const s of x.slots){src(s.A);src(s.B);}}
        if(kind==='parameter')for(const f of x.fields){if(f.expression)expr(f.expression);else for(const m of f.input.matchAll(/@(\d{1,10}):(\d{1,10})/g)){uint(+m[1]);uint(+m[2]);add({kind:'parameter',id:+m[1]},'field',+m[2]);}}
      }if(stage==='setup')verify();
    }
    check(v.sourcePins.length===setup.size&&v.sourcePins.every(p=>setup.has(key(p.ref))));
    for(const a of v.assertions){if(a.kind!=='rejection_world_unchanged')required.add('assembly-rule-authoring/1');if(a.ref)add(a.ref);
      if(a.kind==='member_slot'){add(a.ref,'member',a.memberId);add(a.ref,'slot',a.slotId);}if(a.kind==='joint_tuple')add(a.ref,'joint',a.jointId);
      if(a.kind==='joint_tuple_equal')for(const s of [a.before,a.after])add(s.ref,'joint',s.jointId);
      if(a.kind==='exact_typed_ref'){add(a.ref,'slot',a.slotId);src(a.value);}if(a.kind==='record_pin_unchanged')check(setup.has(key(a.ref)));
    }
    const d=v.expect.diagnostic;if(d){add(d.ref);if(own(d.ref,'fieldId'))add(d.ref,'field',d.ref.fieldId);if(own(d.ref,'slotId'))add(d.ref,'slot',d.ref.slotId);}
    verify();check([...required].every(c=>v.requiredCapabilities.includes(c)));
  }
  function definition(v){bounded(v,65536,4096,16,true);shape(v,['schema','caseId','label','input','sourcePins','requiredCapabilities','expect','assertions']);check(v.schema==='rule-case/1');ident(v.caseId);text(v.label);shape(v.input,['setup','transaction']);array(v.input.setup,32);array(v.input.transaction,32,1);[...v.input.setup,...v.input.transaction].forEach(operation);
    array(v.sourcePins,32);const seen=new Set();for(const p of v.sourcePins){shape(p,['ref','sha256']);ref(p.ref);hash(p.sha256);const k=canonical(p.ref);check(!seen.has(k));seen.add(k);}caps(v.requiredCapabilities);expected(v.expect);array(v.assertions,32,1);v.assertions.forEach(assertion);closure(v);return v;
  }
  function diagnostics(v){array(v,256);for(const d of v){shape(d,['clause','message'],['code','ref','timber','expected']);for(const k of ['clause','message','code','expected'])if(own(d,k))text(d[k],['clause','code'].includes(k)?64:4096,0,true);if(own(d,'ref'))ref(d.ref,false,true);if(own(d,'timber'))uint(d.timber);}}
  function observed(v){shape(v,['capabilities','rules','bindings','instances']);caps(v.capabilities,32);array(v.instances,0);
    for(const kind of ['rules','bindings']){array(v[kind],64);for(const r of v[kind]){shape(r,['value','fingerprint',...(kind==='bindings'?['complete','effective']:[])]);hash(r.fingerprint);operation({op:kind==='rules'?'publish-rule':'create-binding',value:r.value});if(kind==='bindings'){check(typeof r.complete==='boolean');array(r.effective,8);for(const s of r.effective){shape(s,['slotId','A','B']);uint(s.slotId);for(const axis of ['A','B'])if(s[axis]!==null){shape(s[axis],['value','path']);num(s[axis].value,-1e8,1e8);text(s[axis].path,2047,0,true);}}}}}
  }
  function receipt(r,d){bounded(r,4*1024*1024,65536,32);shape(r,['caseId','definitionHash','sourceHash','executor','context','status','authorExpected','actualOutcome','actualDiagnostics','assertionResults','conditions'],['reason','detail','recordedStatus','staleReasons','setupDiagnostics','observations','missingCapabilities']);
    check(r.caseId===d.caseId&&STATUSES.includes(r.status));hash(r.definitionHash);hash(r.sourceHash);expected(r.authorExpected);check(canonical(r.authorExpected)===canonical(d.expect));shape(r.context,['projectId','generation']);text(r.context.projectId,128);uint(r.context.generation,0,Number.MAX_SAFE_INTEGER);
    const fields=['nativeBinaryHash','nativeSourceHash','validatorVersion','axiomHash','assertionSchemaHash'];check(typeof r.executor?.known==='boolean');shape(r.executor,['known',...(r.executor.known?fields:['reason'])]);if(r.executor.known)fields.forEach(k=>hash(r.executor[k]));else text(r.executor.reason,4096,0,true);
    if(own(r,'recordedStatus'))check(STATUSES.includes(r.recordedStatus)&&r.recordedStatus!=='stale');if(own(r,'staleReasons')){array(r.staleReasons,6,1);check(r.staleReasons.every(x=>['definition','source','unknown-runtime','runtime','project-context','generation'].includes(x)));}if(r.status==='stale')check(own(r,'recordedStatus')&&own(r,'staleReasons'));
    for(const k of ['reason','detail'])if(own(r,k))text(r[k],4096,0,true);check([null,'accepted','rejected'].includes(r.actualOutcome));diagnostics(r.actualDiagnostics);if(own(r,'setupDiagnostics'))diagnostics(r.setupDiagnostics);if(own(r,'missingCapabilities'))caps(r.missingCapabilities,32);
    const c=r.conditions;shape(c,['timeoutSeconds','maxOutputBytes','isolated','nativePid','privateDirectoryRemoved'],['capabilities','elapsedSeconds']);num(c.timeoutSeconds,.01,30);uint(c.maxOutputBytes,1,2*1024*1024);check(c.isolated===true&&typeof c.privateDirectoryRemoved==='boolean');if(c.nativePid!==null)uint(c.nativePid);if(own(c,'capabilities'))caps(c.capabilities,32);if(own(c,'elapsedSeconds'))num(c.elapsedSeconds,0,60);
    array(r.assertionResults,d.assertions.length);for(const [i,a] of r.assertionResults.entries()){shape(a,['kind','passed','predicate']);check(typeof a.passed==='boolean'&&a.kind===d.assertions[i].kind&&canonical(a.predicate)===canonical(d.assertions[i]));}
    if(own(r,'observations')){const o=r.observations;shape(o,['before','after','beforeRevision','afterRevision','beforeDumpHash','afterDumpHash']);observed(o.before);observed(o.after);uint(o.beforeRevision,0,Number.MAX_SAFE_INTEGER);uint(o.afterRevision,0,Number.MAX_SAFE_INTEGER);hash(o.beforeDumpHash);hash(o.afterDumpHash);}
    if(r.status==='passed'||r.recordedStatus==='passed'){check(r.executor.known&&c.nativePid>0&&c.privateDirectoryRemoved===true&&own(c,'capabilities')&&own(c,'elapsedSeconds')&&own(r,'observations')&&r.actualOutcome===d.expect.outcome&&r.assertionResults.length===d.assertions.length&&r.assertionResults.every(a=>a.passed));
      if(d.expect.outcome==='rejected'){check(r.actualDiagnostics.some(a=>a.code===d.expect.diagnostic.code&&a.clause===d.expect.diagnostic.clause&&canonical(a.ref)===canonical(d.expect.diagnostic.ref)));const o=r.observations;check(canonical(o.before)===canonical(o.after)&&o.beforeRevision===o.afterRevision&&o.beforeDumpHash===o.afterDumpHash);}}
  }
  function validate(v){bounded(v);shape(v,['schema','definitions','receipts']);check(v.schema===SCHEMA);array(v.definitions,6,6);check(new Set(v.definitions.map(d=>d.caseId)).size===6&&v.definitions.every(d=>IDS.includes(d.caseId)));v.definitions.forEach(definition);array(v.receipts,24);for(const entry of v.receipts){shape(entry,['definition','receipt']);definition(entry.definition);check(IDS.includes(entry.definition.caseId));receipt(entry.receipt,entry.definition);}return v;}
  async function verifyHashes(v){validate(v);const sha=async x=>Array.from(new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',encoder.encode(canonical(x))))).map(n=>n.toString(16).padStart(2,'0')).join('');
    for(const d of [...v.definitions,...v.receipts.map(e=>e.definition)]){const pins=new Map(d.sourcePins.map(p=>[canonical(p.ref),p.sha256]));check(pins.size===d.input.setup.length);for(const op of d.input.setup){const kind={ 'publish-rule':'rule','create-binding':'binding','put-binding':'binding','put-parameter':'parameter','publish-material':'material'}[op.op],ref={kind,id:op.value.id,...(['rule','material'].includes(kind)?{version:op.value.version}:{})};check(pins.get(canonical(ref))===await sha(op.value));}}
    for(const e of v.receipts)check(e.receipt.definitionHash===await sha(e.definition)&&e.receipt.sourceHash===await sha(e.definition.sourcePins));
  }
  return {KIND,SCHEMA,IDS,MAX_BYTES,validate,definition,bounded,canonical,verifyHashes};
});
