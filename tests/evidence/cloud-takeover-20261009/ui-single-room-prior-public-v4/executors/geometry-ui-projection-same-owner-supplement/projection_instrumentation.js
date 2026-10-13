() => {
  const clone=v=>v==null?v:structuredClone(v);
  const identities=new WeakMap();let serial=0;
  const identity=o=>{if(!o)return null;if(typeof o!=='object'&&typeof o!=='function')return o;if(!identities.has(o))identities.set(o,++serial);return identities.get(o);};
  const audit=window.__projectionSupplement={gate:null,apply:[],downs:[],moves:[],ups:[],loads:[],events:[],fetches:[],originals:{}};
  audit.form=()=>({checks:[...document.querySelectorAll('#faceProjectionEditor .fe-ob-check')].map(c=>[c.dataset.itemType+':'+c.dataset.itemId,c.checked]),cut:document.querySelector('#feCutStrip')?.checked??null,button:document.querySelector('#feApplyProj')?.textContent??null});
  audit.state=()=>({contextId:ReferenceWorkspace.context().id,contextObject:identity(ReferenceWorkspace.context()),frame:identity(ReferenceWorkspace.history.frame),session:connection.session,
    edit:clone(oc.edit),editObject:identity(oc.edit),focus:clone(oc.focus),focusObject:identity(oc.focus),navigationSequence:oc.navigationSequence,
    tool:fe.tool,work:clone(fe.work),drag:clone(fe.drag),panHold:clone(fe.panHold),draft:clone(fe.draft),op:clone(fe.op),selection:clone(fe.sel),timbers:[...fe.timberSelection],
    actualModel:clone(oc.bmap[oc.edit?.bid]),form:audit.form(),
    canvas:[...document.querySelector('#faceEditorRoot').children].filter(e=>e.id!=='feBackgroundGrid').map(e=>e.outerHTML),
    workspaceHidden:document.querySelector('#objectWorkspace').hidden,workspaceTitle:document.querySelector('#workspaceTitle').textContent});
  const originalFetch=window.fetch;
  window.fetch=async(...args)=>{
    let command;try{command=JSON.parse(args[1]?.body||'{}').cmd;}catch(_){}
    const stack=new Error().stack,gate=audit.gate;
    const target=gate&&gate.phase==='armed'&&String(args[0])==='/api'&&command===gate.command&&/feApplyProj/.test(stack);
    if(target){gate.phase='requested';gate.stack=stack;}
    const response=await originalFetch(...args);
    if(String(args[0])==='/api')audit.fetches.push({command,status:response.status});
    if(target){const json=response.json.bind(response);response.json=async()=>{const data=await json();gate.nativeReply=clone(data);gate.phase='held';await gate.promise;gate.phase='released';return data;};}
    return response;
  };
  audit.arm=command=>{if(audit.gate)throw Error('one held operation per fresh case');const g={command,phase:'armed'};g.promise=new Promise(resolve=>g.release=resolve);audit.gate=g;};
  for(const [name,key,async]of[['feApplyProj','apply',true],['feDown','downs',true],['feMove','moves',false],['feUp','ups',true],['feLoadGuides','loads',true]]){
    audit.originals[name]=window.eval(name);
    window.eval(name+'='+ (async?'async ':'')+'function(...args){const c={phase:"running",before:__projectionSupplement.state(),trusted:args[1]?.isTrusted??null};__projectionSupplement.'+key+'.push(c);try{return '+(async?'await ':'')+'__projectionSupplement.originals.'+name+'(...args);}finally{c.after=__projectionSupplement.state();c.phase="settled";}}');
  }
  for(const type of['pointerdown','pointerup','pointermove','click','keydown','change','input'])document.addEventListener(type,e=>{
    const n=e.target.closest?.('button,input,select,[data-timber-id]')||e.target;
    audit.events.push({type,trusted:e.isTrusted,id:n.id||null,key:e.key||null,shift:e.shiftKey??false,button:e.button??null,buttons:e.buttons??null,pointerId:e.pointerId??null,
      timber:n.closest?.('[data-timber-id]')?.dataset.timberId??null,faceTool:n.dataset?.faceTool??null,itemType:n.dataset?.itemType??null,itemId:n.dataset?.itemId??null,
      x:e.clientX??null,y:e.clientY??null});
  },true);
  audit.read=()=>({gate:audit.gate&&{...audit.gate,promise:undefined,release:undefined},apply:audit.apply,downs:audit.downs,moves:audit.moves,ups:audit.ups,loads:audit.loads,events:audit.events,fetches:audit.fetches});
}
