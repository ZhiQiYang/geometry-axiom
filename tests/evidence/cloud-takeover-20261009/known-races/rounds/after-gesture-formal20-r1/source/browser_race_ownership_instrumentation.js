() => {
  // Supplemental observer only. Held native payloads are returned unchanged.
  const clone = value => value == null ? value : structuredClone(value);
  const audit = window.__raceSupplement = {gate:null, downs:[], moves:[], ups:[], draws:[], changes:[], events:[], fetches:[]};
  audit.state = () => ({
    workSurf:document.querySelector('#workSurf').value, view3, tool, editBid, editToken,
    editLoops:clone(editLoops), editDrag:clone(editDrag), rectStart:clone(rectStart),
    ocOn:oc.on, ocFocus:clone(oc.focus), ocEdit:clone(oc.edit),
    navigationSequence:oc.navigationSequence,
    groups:previewGs.filter(g=>g.isConnected).map(g=>g.outerHTML),
    handles:[...document.querySelectorAll('#world polygon[stroke-dasharray="8 4"],#world circle[fill="#c0392b"]')].map(e=>e.outerHTML),
    canvasVisible:!cv.hidden && cv.getBoundingClientRect().width>0,
    workspaceHidden:document.querySelector('#objectWorkspace').hidden,
    inspectorHidden:document.querySelector('#inspectorContent').hidden,
    context:ReferenceWorkspace.context().id,
  });
  const originalFetch = window.fetch;
  window.fetch = async (...args) => {
    let command;
    try { command = JSON.parse(args[1]?.body || '{}').cmd; } catch (_) {}
    const stack = new Error().stack, gate = audit.gate;
    const target = gate && gate.phase==='armed' && String(args[0])==='/api' &&
      (gate.kind==='bhit' ? new RegExp('^bhit '+gate.id+' ').test(command||'') && /canvasDown/.test(stack)
        : new RegExp('^line boundary '+gate.id+' outline ').test(command||'') &&
          (gate.kind==='up-boundary' ? /canvasUp/.test(stack) : /commitEdgeLength/.test(stack)));
    if(target){gate.phase='requested';gate.command=command;gate.stack=stack;}
    const response = await originalFetch(...args);
    if(String(args[0])==='/api')audit.fetches.push({command,httpStatus:response.status});
    if(target){
      const json=response.json.bind(response);
      response.json=async()=>{const data=await json();gate.nativeReply=clone(data);gate.phase='held';await gate.promise;gate.phase='released';return data;};
    }
    return response;
  };
  audit.arm = (kind,id) => {
    if(audit.gate)throw Error('One held operation per fresh case');
    const gate={kind,id,phase:'armed'};gate.promise=new Promise(resolve=>gate.release=resolve);audit.gate=gate;
  };
  for(const [name,key] of [['canvasDown','downs'],['canvasMove','moves'],['canvasUp','ups']]){
    const original=window.eval(name);
    window.eval(name+'=async function(...args){const call={phase:"running",trusted:args[0]?.isTrusted,pointerId:args[0]?.pointerId,buttons:args[0]?.buttons,before:__raceSupplement.state()};__raceSupplement.'+key+'.push(call);try{return await __raceSupplement.originals.'+name+'(...args);}finally{call.after=__raceSupplement.state();call.phase="settled";}}');
    (audit.originals ||= {})[name]=original;
  }
  const draw=drawEditHandles;
  drawEditHandles=async(...args)=>{const call={bid:editBid,token:args[0]??editToken,phase:'running'};audit.draws.push(call);try{return await draw(...args);}finally{call.phase='settled';}};
  const add=Element.prototype.addEventListener;
  Element.prototype.addEventListener=function(type,listener,...rest){
    if(type==='change'&&this.matches?.('input[data-edge-len]')&&typeof listener==='function'){
      const wrapped=async function(event){const call={id:this.id,value:this.value,trusted:event.isTrusted,phase:'running'};audit.changes.push(call);try{return await listener.call(this,event);}finally{call.phase='settled';}};
      return add.call(this,type,wrapped,...rest);
    }
    return add.call(this,type,listener,...rest);
  };
  for(const type of ['pointerdown','pointermove','pointerup','pointercancel','lostpointercapture','click','keydown','change'])document.addEventListener(type,event=>{
    const target=event.target.closest?.('.ocard,button,input,select')||event.target;
    audit.events.push({type,trusted:event.isTrusted,id:target.id||null,card:target.dataset?.kind||null,cardId:target.dataset?.id||null,
      key:event.key||null,pointerId:event.pointerId??null,pointerType:event.pointerType??null,button:event.button??null,buttons:event.buttons??null,
      x:event.clientX??null,y:event.clientY??null,value:type==='change'?target.value:undefined});
  },true);
  audit.read=()=>({gate:audit.gate&&{...audit.gate,promise:undefined,release:undefined},downs:audit.downs,moves:audit.moves,
    ups:audit.ups,draws:audit.draws,changes:audit.changes,events:audit.events,fetches:audit.fetches});
}
