/* Browser-only observations; no product files, deadlines or return values changed. */
(()=>{
  let nodeSerial=0,requestSerial=0;const nodes=new WeakMap();
  const nodeId=n=>n?(nodes.has(n)?nodes.get(n):(nodes.set(n,++nodeSerial),nodeSerial)):null;
  const desc=n=>n?{node:nodeId(n),tag:n.tagName,id:n.id,class:String(n.className?.baseVal??n.className??'')}:null;
  const box=n=>{if(!n)return null;const r=n.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,h=document.elementFromPoint(x,y),c=getComputedStyle(n);return {...desc(n),rect:r.toJSON(),hidden:n.hidden,display:c.display,visibility:c.visibility,disabled:!!n.disabled,hit:n.contains(h),hitElement:desc(h),scrollTop:n.scrollTop,scrollLeft:n.scrollLeft,scrollHeight:n.scrollHeight,clientHeight:n.clientHeight};};
  window.__uiLog=row=>window.__uiSink({browserMs:performance.now(),epochMs:performance.timeOrigin+performance.now(),...row});
  window.__uiOpenSerial=0;window.__uiEnded={};window.__uiCall=null;window.__uiArm=false;
  window.__uiSnapshot=()=>{
    const by=id=>document.getElementById(id),ancestors=[];let n=by('igBoundary');
    for(let i=0;n&&i<9;i++,n=n.parentElement)ancestors.push(box(n));
    return {viewport:{width:innerWidth,height:innerHeight,visual:visualViewport?{width:visualViewport.width,height:visualViewport.height,scale:visualViewport.scale,offsetTop:visualViewport.offsetTop}:null},dialogs:[...document.querySelectorAll('dialog[open]')].map(desc),focus:desc(document.activeElement),connection:typeof connection==='undefined'?null:{...connection},projectBusy:typeof ReferenceWorkspace==='undefined'?null:ReferenceWorkspace.busy,ocBusy:typeof oc==='undefined'?null:oc.busy,sourceForm:box(by('igSourceForm')),bindingForm:box(by('igBindingForm')),newBinding:box(by('igNewBinding')),boundary:box(by('igBoundary')),retry:box(by('connectionRetry')),close:box(by('igClose')),ancestors,trial:by('igTrial')?.dataset.trialState??null};
  };
  window.__uiAwait=async(id,label,options,fn,state)=>{
    const previous=window.__uiCall;
    window.__uiLog({event:'open.await.begin',id,label,state:state()});
    let promise;
    try{window.__uiCall={id,label,mode:options.mode??null};promise=fn();}finally{window.__uiCall=previous;}
    try{const value=await promise;window.__uiLog({event:'open.await.end',id,label,ok:value?.ok,error:value?.error,state:state()});return value;}
    catch(error){window.__uiLog({event:'open.await.reject',id,label,name:error.name,message:error.message});throw error;}
  };
  window.__uiReturn=(id,line,value,state)=>{window.__uiLog({event:'open.return',id,line,value,state});return value;};
  const realFetch=window.fetch;
  window.fetch=function(input,options){
    let cmd;try{cmd=JSON.parse(options?.body||'{}').cmd;}catch{}
    if(!cmd)return realFetch.apply(this,arguments);
    const rid='ui209-'+(++requestSerial),call=window.__uiCall;
    const hold=window.__uiArm&&call?.mode==='binding'&&cmd==='objects';
    if(hold)window.__uiArm=false;
    const fields={rid,cmd,call,hold};
    options={...options,headers:new Headers(options.headers)};
    options.headers.set('X-UI209-Request-ID',rid);
    if(hold)options.headers.set('X-UI209-Hold','1');
    window.__uiLog({event:'fetch.begin',...fields,stack:new Error().stack});
    let settled=false;
    options.signal?.addEventListener('abort',()=>window.__uiLog({event:'fetch.signal.abort',...fields,settled,reason:{name:options.signal.reason?.name,message:options.signal.reason?.message},stack:new Error().stack}),{once:true});
    return realFetch.call(this,input,options).then(r=>{settled=true;window.__uiLog({event:'fetch.headers',...fields,status:r.status});return r;},error=>{settled=true;window.__uiLog({event:'fetch.reject',...fields,name:error.name,message:error.message,stack:error.stack});throw error;});
  };
  const timeout=AbortSignal.timeout;
  AbortSignal.timeout=function(ms){window.__uiLog({event:'abort.timer.created',ms,stack:new Error().stack});return timeout.call(this,ms);};
  window.__uiObserveReady=()=>{
    for(const key of ['phase','error','recovering']){let value=connection[key];Object.defineProperty(connection,key,{enumerable:true,configurable:true,get:()=>value,set:next=>{if(value!==next)window.__uiLog({event:'connection.change',key,old:value,next,stack:new Error().stack});value=next;}});}
    for(const name of ['click','keydown','focusin','scroll'])document.addEventListener(name,event=>{
      if(event.target?.closest?.('#infiniteGridWorkspace')||['connectionRetry','igClose'].includes(event.target?.id))window.__uiLog({event:'ui.'+name,trusted:event.isTrusted,key:event.key,target:desc(event.target),scrollTop:event.target.scrollTop,focus:desc(document.activeElement)});
    },true);
    let previous='';new MutationObserver(()=>{const d=document.getElementById('infiniteGridWorkspace'),a=document.getElementById('igNewBinding'),b=document.getElementById('igBindingForm');const next=JSON.stringify([nodeId(d),nodeId(a),nodeId(b),b?.hidden,d?.open]);if(next!==previous){previous=next;window.__uiLog({event:'ui.structure',ui:window.__uiSnapshot()});}}).observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['hidden','open']});
  };
})();
