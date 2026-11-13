/* H: compare native assembly identities and project their fixed W sources.
 * This adapter never creates a bay, assigns an id or evaluates geometry. */
(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory(require('../geometry-app/application.js'));
  else root.AssemblyProvenance=factory(root.GeometryApplication);
})(typeof globalThis!=='undefined'?globalThis:this,application=>{
  'use strict';
  const own=(o,k)=>Object.hasOwn(o,k),id=n=>Number.isSafeInteger(n)&&n>0&&n<=4294967295;
  const hash=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
  const object=o=>o&&typeof o==='object'&&!Array.isArray(o);
  const keys=(o,names)=>object(o)&&Object.keys(o).length===names.length&&names.every(k=>own(o,k));
  const fail=()=>{throw Error('組構分件身分或固定來源無法核對。');};
  function identityKey(value){
    if(keys(value,['memberId'])&&id(value.memberId))return 'member:'+value.memberId;
    if(keys(value,['primary'])&&id(value.primary))return 'primary:'+value.primary;
    const s=value?.secondary;
    if(keys(value,['secondary'])&&keys(s,['line','left','right'])&&[s.line,s.left,s.right].every(id)&&s.left!==s.right)
      return `secondary:${s.line}:${s.left}:${s.right}`;
    return fail();
  }
  function memberIdentity(member){
    if(!object(member))return fail();
    const names=['memberId','primary','secondary'].filter(k=>own(member,k));
    if(names.length!==1)return fail();
    const value={[names[0]]:member[names[0]]};identityKey(value);return JSON.parse(JSON.stringify(value));
  }
  function ownerIdentity(owner){
    if(!object(owner))return fail();
    if(own(owner,'identity')){
      if(own(owner,'memberId')||own(owner.identity||{},'memberId'))return fail();
      identityKey(owner.identity);return owner.identity;
    }
    const value={memberId:owner.memberId};identityKey(value);return value;
  }
  const ownerFields=['instanceId','bindingId','ruleId','ruleVersion','ruleFingerprint','instanceFingerprint','bindingFingerprint'];
  function ownerValid(owner){
    if(owner===null)return true;
    if(!object(owner)||!ownerFields.slice(0,4).every(k=>id(owner[k]))||!ownerFields.slice(4).every(k=>hash(owner[k])))return false;
    try{ownerIdentity(owner);return true;}catch(_){return false;}
  }
  function sameOwner(a,b){
    return ownerValid(a)&&ownerValid(b)&&(a===null||b===null?a===b:
      ownerFields.every(k=>a[k]===b[k])&&identityKey(ownerIdentity(a))===identityKey(ownerIdentity(b)));
  }
  function identityLabel(value){
    identityKey(value);
    if(own(value,'memberId'))return `member ${value.memberId}`;
    if(own(value,'primary'))return `主支 ${value.primary}`;
    const s=value.secondary;return `副支 線 ${s.line}／左 ${s.left}／右 ${s.right}`;
  }
  function memberSlot(rule,member){
    const identity=memberIdentity(member);
    if(own(identity,'memberId'))return rule?.members?.find(m=>m.id===identity.memberId)?.slotId;
    const shape=application.woodworking.assemblyBayRepeatShape(rule);
    return own(identity,'primary')?shape.primarySlot:rule.members.find(m=>m.id===shape.secondaryMember)?.slotId;
  }
  function verifyRepeatMember(instance,member){
    const source=instance?.value?.source,identity=memberIdentity(member);
    if(source?.layout!=='bay-repeat'||own(identity,'memberId')||!id(member.timberId))return fail();
    const primary=k=>source.primaries?.filter(p=>p.key===k).length===1;
    if(own(identity,'primary')){if(!primary(identity.primary))return fail();}
    else{const s=identity.secondary;
      if(source.secondaryLines?.filter(l=>l.key===s.line).length!==1||!primary(s.left)||!primary(s.right)||
        source.omit?.some(o=>o.line===s.line&&o.left===s.left&&o.right===s.right))return fail();}
    const mapping=instance.value.mapping;
    if(!Array.isArray(mapping)||mapping.filter(m=>m.timberId===member.timberId).length!==1||
      mapping.filter(m=>identityKey(memberIdentity(m))===identityKey(identity)).length!==1||
      !mapping.some(m=>m.timberId===member.timberId&&identityKey(memberIdentity(m))===identityKey(identity)))return fail();
    return identity;
  }
  return Object.freeze({identityKey,memberIdentity,ownerIdentity,ownerFields,ownerValid,sameOwner,identityLabel,memberSlot,verifyRepeatMember});
});
