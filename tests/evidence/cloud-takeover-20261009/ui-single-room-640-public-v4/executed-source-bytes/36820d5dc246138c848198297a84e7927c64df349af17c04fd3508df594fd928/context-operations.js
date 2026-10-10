/* One bounded context operation. Pure UI metadata; no native mutation or inference.
 * The workspace owner still guards context/selection and owns drafts/transactions. */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.ContextOperations=api;
})(typeof globalThis!=='undefined'?globalThis:this,()=>{
  'use strict';
  const positiveId=n=>Number.isInteger(n)&&n>0&&n<=0xffffffff;
  const hash=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
  const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
  const operation=Object.freeze({id:'assembly-binding.create',label:'建立材料配置',
    inputKind:'assembly-rule',capability:'assembly-rule-authoring/1',
    workspace:'AssemblyWorkspace',draftKind:'binding',outputKind:'assembly-binding',generatesGeometry:false});
  const fields=Object.freeze([
    Object.freeze({field:'A',kind:'dimension-source',label:'A 尺寸來源'}),
    Object.freeze({field:'B',kind:'dimension-source',label:'B 尺寸來源'}),
    Object.freeze({field:'contactFace',kind:'contact-face',label:'接觸面'}),
    Object.freeze({field:'orientation',kind:'orientation',label:'截面方向'})
  ]);
  const messages={
    'invalid-selection':'所選規則的固定身分或原生指紋不合法，請重新選取。',
    'unsupported-selection':'此操作只適用於單一已發布組構規則。',
    'native-read-unchecked':'原生規則來源尚未核對。',
    'native-read-failed':'原生規則來源尚未讀取成功，請重新檢查。',
    'invalid-native-response':'原生規則回覆無法可靠核對，請更新服務或重新檢查。',
    'capabilities-unchecked':'原生服務的規則編寫能力尚未核對。',
    'invalid-capabilities':'原生服務的能力回覆不合法，請重新檢查。',
    'capability-missing':'原生服務未提供組構規則編寫能力。',
    'source-missing':'所選固定規則版本已移除或不存在，請重新選取。',
    'ambiguous-source':'所選固定規則版本不是唯一來源，請重新檢查。',
    'invalid-source':'原生固定規則的指紋或槽位身分不合法，請重新檢查。',
    'source-changed':'所選固定規則內容已變更，請重新選取；不會自動改用其他來源。'
  };
  function result(status,reason,source=null,extra={}){
    return {ok:false,status,reason,message:messages[reason],operation,source,...extra};
  }
  function getOperation(id){return id===operation.id?operation:null;}
  function resolveBindingCreate(selection,read){
    if(!object(selection))return result('invalid','invalid-selection');
    if(selection.kind!==operation.inputKind)return result('unavailable','unsupported-selection');
    if(!positiveId(selection.id)||!positiveId(selection.version)||!hash(selection.fingerprint))
      return result('invalid','invalid-selection');
    const source={kind:selection.kind,id:selection.id,version:selection.version,fingerprint:selection.fingerprint};
    if(read===undefined||read===null)return result('unchecked','native-read-unchecked',source);
    if(!object(read)||typeof read.ok!=='boolean')return result('invalid','invalid-native-response',source);
    if(!read.ok)return result('unchecked','native-read-failed',source);
    if(!Number.isSafeInteger(read.revision)||read.revision<0||!object(read.state))
      return result('invalid','invalid-native-response',source);
    const capabilities=read.state.capabilities;
    if(capabilities===undefined||capabilities===null)return result('unchecked','capabilities-unchecked',source);
    if(!Array.isArray(capabilities)||!capabilities.every(v=>typeof v==='string'))
      return result('invalid','invalid-capabilities',source);
    if(!capabilities.includes(operation.capability))return result('unavailable','capability-missing',source,
      {missingCapabilities:[operation.capability]});
    const rules=read.state.rules;
    if(!Array.isArray(rules)||!rules.every(r=>object(r)&&object(r.value)&&positiveId(r.value.id)&&positiveId(r.value.version)))
      return result('invalid','invalid-native-response',source);
    const matches=rules.filter(r=>r.value.id===source.id&&r.value.version===source.version);
    if(!matches.length)return result('missing','source-missing',source);
    if(matches.length!==1)return result('invalid','ambiguous-source',source);
    const record=matches[0],slots=record.value.slots;
    if(!hash(record.fingerprint)||!Array.isArray(slots)||slots.length<1||slots.length>8||
      !slots.every(s=>object(s)&&positiveId(s.id))||new Set(slots.map(s=>s.id)).size!==slots.length)
      return result('invalid','invalid-source',source);
    if(record.fingerprint!==source.fingerprint)return result('stale','source-changed',source);
    let copy;
    try{copy=structuredClone(record);}catch(_){return result('invalid','invalid-source',source);}
    // All four fields start unset in the owner's existing new binding draft.
    // These describe completeness, not permission to create/publish incomplete.
    const missingInputs=slots.flatMap(slot=>fields.map(field=>({slotId:slot.id,...field,
      stage:'complete',blocksDraft:false,blocksPublication:false})));
    return {ok:true,status:'ready',reason:null,message:'',operation,source,record:copy,
      nativeRevision:read.revision,missingInputs};
  }
  return Object.freeze({getOperation,resolveBindingCreate});
});
