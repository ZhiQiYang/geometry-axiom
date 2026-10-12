'use strict';
// Observation only: fail closed if the expected open() source changes.
// Each await adds a logging Promise layer; its timing overhead is not calibrated.
module.exports=function instrument(source){
  const begin=source.indexOf('  async function open(options={}, committed=false) {');
  const end=source.indexOf('  function selectedOpen(options)',begin);
  if(begin<0||end<0)throw Error('Missing open boundaries');
  let part=source.slice(begin,end),awaits=0,returns=0;
  const line=offset=>source.slice(0,begin+offset).split('\n').length;
  part=part.replace(/await (apiRequest\('[^']+'\)|setView3\(false\)|leaveFocus\(\)|catalogPins\(final,(?:draftSchema|F.GRID_RULE_SCHEMA)\)|render\(state\))/g,(whole,expr,offset)=>{
    awaits++;return `await __ua(${JSON.stringify(expr+' @'+line(offset))},()=>${expr})`;
  });
  if(awaits!==13||(part.match(/\bawait\b/g)||[]).length!==13)throw Error('Unexpected open await shape: '+awaits);
  part=part.replace(/\breturn(?: (true|false))?;/g,(whole,value,offset)=>{
    returns++;return `return window.__uiReturn(__uid,${line(offset)},${value||'undefined'},__us());`;
  });
  const guard="const ownsEntry=()=>ticket===serial&&context===ReferenceWorkspace.context()&&contextToken===ReferenceWorkspace.getProjectState().contextToken&&\n      (options.ruleKey==null||frame===ReferenceWorkspace.history.frame&&nativeStamp===JSON.stringify(ReferenceWorkspace.getEvidenceState())&&(transferred||options.isCurrent?.()!==false));";
  if(!part.includes(guard))throw Error('Missing ownsEntry anchor');
  const expr=guard.slice('const ownsEntry=()=>'.length,-1);
  part=part.replace(guard,`const ownsEntry=()=>{const ok=${expr};window.__uiLog({event:'open.owns',id:__uid,ok,ticket,serial,sameContext:context===ReferenceWorkspace.context(),sameToken:contextToken===ReferenceWorkspace.getProjectState().contextToken,ruleKey:options.ruleKey??null,sameFrame:frame===ReferenceWorkspace.history.frame,transferred});return ok;};`);
  const header='  async function open(options={}, committed=false) {';
  part=part.replace(header,header+`
    const __uid=++window.__uiOpenSerial;
    const __us=()=>({mode:state?.mode??null,busy:!!state?.busy,initializing:!!state?.initializing,heldControls:!!state?.heldControls,projectControls:!!state?.projectControls,releasing:!!state?.releasing,serial,projectBusy:ReferenceWorkspace.busy});
    const __ua=(label,fn)=>window.__uiAwait(__uid,label,options,fn,__us);
    window.__uiLog({event:'open.begin',id:__uid,options:{system:options.system,mode:options.mode,binding:options.binding,ruleKey:options.ruleKey,committed},state:__us()});
    try {`);
  const tail=part.lastIndexOf('  }');
  part=part.slice(0,tail)+`    }catch(error){window.__uiLog({event:'open.throw',id:__uid,name:error.name,message:error.message,stack:error.stack,state:__us()});throw error;}
    finally{window.__uiEnded[__uid]=true;window.__uiLog({event:'open.end',id:__uid,state:__us(),ui:window.__uiSnapshot()});}
`+part.slice(tail);
  return {source:source.slice(0,begin)+part+source.slice(end),awaits,returns};
};
