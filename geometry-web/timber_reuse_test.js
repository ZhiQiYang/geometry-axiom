/* R11 second slice A / issue #116: real menu, same-face batch, native candidates.
 * Run only through cdp_test.js. Native fixture setup is labelled separately from
 * trusted UI actions. Fault injection holds/drops actual completed responses;
 * it never manufactures a successful native result.
 */
'use strict';
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawn}=require('node:child_process'),net=require('node:net'),crypto=require('node:crypto');
const {isDeepStrictEqual:same}=require('node:util');
const cdp=require('./cdp_helpers.js');
const P=require('./project-store.js'),zip=require('./vendor/fflate/umd/index.js');
const CASE_IDS=Object.freeze(Array.from({length:12},(_,i)=>'C'+String(i+1).padStart(2,'0')));
const READ_COMMAND=/^(?:dump|objects|surfaces|references|engineering-read|section-profile-read|assembly-read|source-inspect|render|boundary \d+|obstacles \d+)$/;
const ZERO_FIXTURE=[
  'boundary 1 outline 0,0 4000,0 4000,3000 0,3000',
  'placement 0 on boundary 1 origin 0 0 2500 u +x v +y',
  'timber 0 27 33 role boundary','place 0 on 0 at-face e0 +u +n'
];
const PAIR_FIXTURE=[...ZERO_FIXTURE,'timber 7 29 33 role boundary','place 7 on 0 at-face e2 +u +n'];
const ATOMIC_FIXTURE=[...ZERO_FIXTURE.slice(0,2),
  'spec position1 500','spec position2 550','guide 1 0 v spec:position1','guide 2 0 v spec:position2',
  'timber 90 20 20 role boundary','place 90 on 0 at-face e0 +u +n',
  'timber 91 20 20 role boundary','place 91 on 0 at-face e2 +u +n',
  'timber 1 20 33 role primary','place 1 on 0 at-line guide 1 +v +n',
  'timber 2 80 33 role primary','place 2 on 0 at-line guide 2 +v +n'];
const REPEAT_FIXTURE=[...ZERO_FIXTURE,'spec position1 500','spec position2 550',
  'guide 1 0 v spec:position1','guide 2 0 v spec:position2',
  'timber 90 20 20 role boundary','place 90 on 0 at-face e2 +u +n',
  'timber 1 20 33 role primary','place 1 on 0 at-line guide 1 +v +n',
  'timber 2 80 33 role primary','place 2 on 0 at-line guide 2 +v +n',
  'spec repeat3 1000','spec repeat4 1500','guide 3 0 v spec:repeat3','guide 4 0 v spec:repeat4'];
const SOURCE_A={mode:'source',source:{kind:'parameter',parameterId:10,fieldId:5},override:{kind:'literal',value:27}};
const SOURCE_B={mode:'source',source:{kind:'material',id:'pine',version:1,field:'B'},override:null};
const sha256=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
function selectCases(value){
  if(value===undefined)return [...CASE_IDS];
  const ids=typeof value==='string'?value.split(',').map(x=>x.trim()):[];
  if(!ids.length||new Set(ids).size!==ids.length||ids.some(id=>!CASE_IDS.includes(id)))throw Error('GEOMETRY_TIMBER_REUSE_CASE requires unique C01..C12 IDs');
  return ids;
}
function fault(kind,assertion,message,detail){const e=new Error(message+(detail===undefined?'':' '+JSON.stringify(detail)));e.r116={kind,assertion};return e;}
function installProbe(){
  if(window.__r116)throw Error('R116 probe already installed');
  const original=window.fetch,p=window.__r116={original,rows:[],events:[],pending:0,gate:null};
  const observe=e=>p.events.push({type:e.type,trusted:e.isTrusted,key:e.key,composing:e.isComposing,ctrl:e.ctrlKey,meta:e.metaKey,target:e.target?.id||e.target?.tagName});
  for(const type of ['contextmenu','keydown','keyup','compositionstart','compositionend'])document.addEventListener(type,observe,true);
  p.arm=(pathname,command='',mode='hold',alter=null)=>{
    if(p.gate)throw Error('R116 gate already armed');
    let release;p.gate={pathname,command,mode,alter,phase:'armed',claims:0,promise:new Promise(r=>release=r),release:()=>release()};
  };
  const wrapped=async(...args)=>{
    const url=new URL(typeof args[0]==='string'?args[0]:args[0].url,location.href);
    if(url.origin!==location.origin||!['/api','/timber-edit/read','/timber-edit/preview'].includes(url.pathname))return original.apply(window,args);
    let body;try{body=JSON.parse(args[1]?.body||'{}');}catch(_){return original.apply(window,args);}
    const row={path:url.pathname,command:body.cmd||'',body,settled:false};p.rows.push(row);p.pending++;
    try{
      if(body.receipt&&p.blockReceipts)throw new TypeError('R116 injected receipt temporarily unavailable');
      const response=await original.apply(window,args);let data;
      try{data=await response.clone().json();row.result=data;row.status=response.status;}catch(e){row.observationError=String(e);}
      const gate=p.gate;
      if(gate?.phase==='armed'&&gate.pathname===url.pathname&&(!gate.command||row.command.startsWith(gate.command))){
        gate.phase='held';gate.claims++;gate.nativeOK=data?.ok===true;
        if(gate.mode==='hold')await gate.promise;
        gate.phase='released';
        if(gate.mode==='drop')throw new TypeError('R116 injected lost reply after native completion');
        if(gate.mode==='eligibility'){
          const changed=structuredClone(data);
          for(const timber of changed.timbers||[])if(gate.alter==='unknown')timber.groupsKnown=false;
          else if(gate.alter==='group')timber.groups=[{kind:'boundary-pair',id:335}];
          else if(gate.alter==='owner')timber.owner={kind:'assembly-instance',id:116};
          return new Response(JSON.stringify(changed),{status:response.status,headers:response.headers});
        }
      }
      return response;
    }catch(e){row.error=String(e);throw e;}finally{row.settled=true;p.pending--;}
  };
  window.fetch=wrapped;
  p.cleanup=()=>{p.gate?.release();if(window.fetch===wrapped)window.fetch=original;for(const type of ['contextmenu','keydown','keyup','compositionstart','compositionend'])document.removeEventListener(type,observe,true);delete window.__r116;};
}
module.exports=async function timberReuseTests({send,eval_,sleep,click,waitForUI,expectNativeDialog,captureNewToasts,exceptionCount}){
  if(process.env.GEOMETRY_TIMBER_REUSE_CASE!==undefined&&process.env.GEOMETRY_TIMBER_REUSE_ONLY!=='1')throw Error('GEOMETRY_TIMBER_REUSE_CASE requires ONLY=1');
  const selected=selectCases(process.env.GEOMETRY_TIMBER_REUSE_CASE);
  console.log('=== P116R. R11 第二片：同面角材重用與原子批改 ===');
  const read=cdp.makeRead(eval_),page=(fn,...args)=>read('('+fn.toString()+')('+args.map(x=>JSON.stringify(x)).join(',')+')');
  const record=cdp.makeCheck({prefix:'R116 ',throwOnFail:false}),history=cdp.makeHistoryOracle(read,'R116');
  const key=cdp.makeKey({send,sleep}),pins=new Set();let currentCase=null,offline=false,lastPointer=null;
  const check=(name,ok,detail)=>{record(name,ok,detail);if(ok!==true)throw fault('assertion',name,name,detail);};
  const need=(name,ok,detail)=>{if(ok!==true)throw fault('precondition',name,name,detail);};
  const visible=selector=>page(s=>{const n=document.querySelector(s),r=n?.getBoundingClientRect();return !!r&&r.width>0&&r.height>0&&!n.closest('[hidden]')&&getComputedStyle(n).visibility!=='hidden';},selector);
  const query=async command=>{const result=await page(cmd=>apiRequest(cmd),command);need('NATIVE_READ_OR_FIXTURE_OK',result?.ok===true,{command,result});return result;};
  const line=async source=>{const result=await query('line '+source);if(result.preview){need('FIXTURE_VALID_NATIVE_PREVIEW',result.preview.valid===true,{source,result});return query('line confirm '+result.preview.token);}return result;};
  const dump=async()=>(await query('dump')).text;
  const nativeRead=ids=>page(async selected=>{const response=await fetch('/timber-edit/read',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'timber-edit-read/1',boundaryId:oc.edit.bid,timberIds:selected})});return response.json();},ids);
  const mark=()=>page(()=>window.__r116.rows.length);
  const rows=from=>page(n=>window.__r116.rows.slice(n),from);
  const wait=async(name,expr,timeout=20000)=>{
    try{await waitForUI(expr,timeout);}catch(e){
      if(!e.message.startsWith('UI condition timed out'))throw e;
      const state=await page(()=>({phase:connection.phase,pending:window.__r116?.pending,form:document.getElementById('timberEditForm')?.outerHTML,menuHTML:document.getElementById('feCtxMenu')?.outerHTML,selection:[...fe.timberSelection],sel:fe.sel,menuItems:window.TimberEdit?.menuItems(),requests:window.__r116?.rows.slice(-8)}));state.lastPointer=lastPointer;
      if(state.phase!=='ready'||state.pending)throw fault('exception',name+'_ENVIRONMENT',e.message,state);
      check(name,false,{expression:expr,state});
    }
  };
  const settled=()=>wait('UI_SETTLED',"connection.phase==='ready'&&!oc.busy&&!ReferenceWorkspace.busy&&window.__r116?.pending===0");
  const ctl=cdp.makeCtl({eval_,sleep,click},{scroll:'center',attempts:14,pollMs:60,settleMs:70,missing:'R116 missing ',unreachable:(s,p)=>'R116 unreachable '+s+' '+JSON.stringify(p)});
  const fill=cdp.makeFill({ctl,key,send,sleep},{afterMs:50});
  const choose=async(selector,value)=>{
    const index=await page((s,v)=>{const n=document.querySelector(s);return n?[...n.options].filter(o=>!o.disabled).findIndex(o=>o.value===v):-1;},selector,String(value));
    need('SELECT_OPTION_AVAILABLE',index>=0,{selector,value});await ctl(selector);await key('Home','Home',36);
    for(let n=0;n<index;n++)await key('ArrowDown','ArrowDown',40);await key('Enter','Enter',13);
    await wait('SELECT_VALUE_APPLIED','document.querySelector('+JSON.stringify(selector)+')?.value==='+JSON.stringify(String(value)));
  };
  const checkpoint=async()=>{const pin=await history.capture();pins.add(pin);return {pin,world:await dump(),project:await page(()=>ReferenceWorkspace.getProjectState()),metadata:await page(()=>ReferenceWorkspace.manifest()),revision:(await query('engineering-read')).revision,from:await mark()};};
  const unchanged=async(before,name,{noWrites=true}={})=>{
    const observed=await rows(before.from);
    if(noWrites)check(name+'_ZERO_WRITES',observed.every(r=>r.path==='/timber-edit/read'||r.path==='/api'&&READ_COMMAND.test(r.command)),observed);
    check(name+'_WORLD',(await dump())===before.world);
    check(name+'_NATIVE_REVISION',(await query('engineering-read')).revision===before.revision);
    check(name+'_PROJECT',same(await page(()=>ReferenceWorkspace.getProjectState()),before.project));
    check(name+'_METADATA',same(await page(()=>ReferenceWorkspace.manifest()),before.metadata));
    check(name+'_HISTORY',await history.unchanged(before.pin));
  };
  const selection=()=>page(()=>[...fe.timberSelection]);
  const timberPoint=async id=>{
    await wait('TIMBER_FOOTPRINT_READY','(()=>{const id='+JSON.stringify(id)+',vp=document.getElementById("faceEditorViewport"),node=vp?.querySelector(\'[data-face-hit="t:\'+id+\'"]\'),v=vp?.getBoundingClientRect(),r=node?.getBoundingClientRect();return oc.focus?.t==="face"&&!!oc.edit&&fe.timbers.some(t=>t.id===id)&&!!v&&!!r&&v.width>0&&v.height>0&&r.width>0&&r.height>0&&v.right>0&&v.bottom>0&&v.left<innerWidth&&v.top<innerHeight&&r.right>v.left&&r.left<v.right&&r.bottom>v.top&&r.top<v.bottom;})()');
    const p=await page(value=>{const t=fe.timbers.find(t=>t.id===value);if(!t)return null;const b=feTimberRect(t),v=document.getElementById('faceEditorViewport').getBoundingClientRect();return{x:v.left+(b[0]+b[2])/2*fe.zoom+fe.panX,y:v.top+(b[1]+b[3])/2*fe.zoom+fe.panY};},id);
    need('TIMBER_FOOTPRINT',!!p,{id});return p;
  };
  const selectTimber=async(id,additive=false)=>{const p=await timberPoint(id);await send('Input.dispatchMouseEvent',{type:'mouseMoved',...p,button:'none'});await sleep(70);lastPointer={id,additive,...p,hit:await page(point=>{const n=document.elementFromPoint(point.x,point.y);return n&&{tag:n.tagName,id:n.id,hit:n.closest('[data-face-hit]')?.getAttribute('data-face-hit'),html:n.outerHTML?.slice(0,600),tool:fe.tool};},p)};for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,...p,button:'left',clickCount:1,modifiers:additive?8:0});await settled();};
  const selectTimbers=async ids=>{for(let i=0;i<ids.length;i++)await selectTimber(ids[i],i>0);check('EXPLICIT_SELECTION',same(await selection(),ids),{expected:ids,actual:await selection(),lastPointer,state:await page(()=>({sel:fe.sel,tool:fe.tool,focus:oc.focus,zoom:fe.zoom,panX:fe.panX,panY:fe.panY}))});};
  const rightTimber=async id=>{const p=await timberPoint(id);lastPointer={id,...p};await send('Input.dispatchMouseEvent',{type:'mouseMoved',...p,button:'none'});await sleep(70);for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,...p,button:'right',clickCount:1});await wait('FACE_MENU_VISIBLE',"!document.getElementById('feCtxMenu').hidden");check('TRUSTED_REUSE_MENU',await page(()=>window.__r116.events.some(e=>e.type==='contextmenu'&&e.trusted)));};
  const reuseItem=name=>'#feCtxMenu [data-fe-act="timber-'+name+'"]';
  const menu=async(id,action)=>{
    await rightTimber(id);check('REUSE_SUBMENU_PRESENT',await visible('#feCtxMenu [data-fe-act="reuse"]'));
    await ctl('#feCtxMenu [data-fe-act="reuse"]');
    await wait('REUSE_ACTION_READY','!!document.querySelector('+JSON.stringify(reuseItem(action))+')&&!document.querySelector('+JSON.stringify(reuseItem(action))+').disabled&&document.querySelector('+JSON.stringify(reuseItem(action))+').getAttribute("aria-disabled")!=="true"');
    await ctl(reuseItem(action));await settled();
  };
  const batch=async ids=>{await selectTimbers(ids);await wait('BATCH_FORM_VISIBLE',"document.getElementById('timberEditForm')?.dataset.mode==='batch'");check('BATCH_RIGHT_PANE',await page(()=>!!document.getElementById('faceInspectorContent').querySelector('#timberEditForm')));};
  const reopenBatchFromMenu=async ids=>{
    await selectTimbers(ids);await rightTimber(ids[0]);
    await wait('BATCH_MENU_READY',"!!document.querySelector('#feCtxMenu [data-fe-act=timber-batch]')&&!document.querySelector('#feCtxMenu [data-fe-act=timber-batch]').disabled&&document.querySelector('#feCtxMenu [data-fe-act=timber-batch]').getAttribute('aria-disabled')!=='true'");
    await ctl('#feCtxMenu [data-fe-act="timber-batch"]');await settled();await wait('BATCH_FORM_REOPENED_FROM_MENU',"document.getElementById('timberEditForm')?.dataset.mode==='batch'");
  };
  const editSingle=async id=>{await selectTimbers([id]);await rightTimber(id);await wait('SINGLE_EDIT_READY',"!!document.querySelector('#feCtxMenu [data-fe-act=edit]')&&document.querySelector('#feCtxMenu [data-fe-act=edit]').getAttribute('aria-disabled')!=='true'&&!document.querySelector('#feCtxMenu [data-fe-act=edit]').disabled");await ctl('#feCtxMenu [data-fe-act="edit"]');await wait('SINGLE_NEW_FIELD_FORM',"document.getElementById('timberEditForm')?.dataset.mode==='batch'&&!document.getElementById('timberEditPreview').disabled");await settled();};
  const explicit=async(field,value)=>{
    const selector='[data-timber-patch="'+field+'"]';await ctl(selector);
    if(field==='A'||field==='B'){await choose('#timberEdit'+field+'Mode','direct');await fill('#timberEdit'+field+'Value',String(value));}
    else if(field==='priority')await fill('#timberEditPriority',String(value));
    else await choose('#timberEdit'+field[0].toUpperCase()+field.slice(1),String(value));
  };
  const setPlacement=async(anchor,direction='+u')=>{await choose('#timberEditPlacement','0');await choose('#tbAnchor',anchor);await choose('#tbDir',direction);await choose('#tbSide','+n');};
  const chooseSource=async(selector,source)=>{
    const actual=await page((s,wanted)=>{const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.keys(x).sort().map(k=>[k,x[k]])):x);return [...document.querySelector(s).options].find(o=>{try{return canonical(JSON.parse(o.value))===canonical(wanted);}catch(_){return false;}})?.value;},selector,source);
    need('FULL_TYPED_SOURCE_OPTION',typeof actual==='string',{selector,source});await choose(selector,actual);
  };
  const explicitSource=async(field,source,override=null)=>{
    await ctl('[data-timber-patch="'+field+'"]');await choose('#timberEdit'+field+'Mode','source');await chooseSource('#timberEdit'+field+'Source',source);
    if(override?.kind==='literal'){await choose('#timberEdit'+field+'OverrideMode','literal');await fill('#timberEdit'+field+'OverrideValue',String(override.value));}
    else if(override){await choose('#timberEdit'+field+'OverrideMode','source');await chooseSource('#timberEdit'+field+'OverrideSource',override);}
    else await choose('#timberEdit'+field+'OverrideMode','none');
  };
  const preview=async(code,{valid=true}={})=>{
    const from=await mark();await ctl('#timberEditPreview');
    await wait(code+'_PREVIEW_SETTLED',"window.__r116.pending===0&&window.__r116.rows.slice("+from+").some(r=>r.path==='/timber-edit/preview'&&r.settled)");
    const response=(await rows(from)).find(r=>r.path==='/timber-edit/preview')?.result;
    check(code+'_PREVIEW_RESPONSE',response?.ok===true&&response.preview?.valid===valid,response);
    if(valid&&!response.preview.noOp)check(code+'_CONFIRM_VISIBLE',await visible('#timberEditConfirm'));
    return response.preview;
  };
  const confirm=async code=>{const from=await mark();await ctl('#timberEditConfirm');await settled();const calls=(await rows(from)).filter(r=>r.path==='/api'&&r.command.startsWith('timber-edit-confirm '));check(code+'_ONE_CONFIRM',calls.length===1&&calls[0].result?.ok===true,calls);check(code+'_REQUEST_RECEIPT',typeof calls[0].body.requestId==='string'&&/^[a-f0-9-]{36}$/.test(calls[0].body.requestId)&&typeof calls[0].body.session==='string'&&calls[0].body.session.length>0,calls[0].body);return calls[0].result;};
  const cancel=async()=>{if(await visible('#timberEditCancel')){await ctl('#timberEditCancel');await settled();}};
  const fixture=async(lines=ZERO_FIXTURE)=>{
    await cleanup();await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
    await page(()=>{resetSceneFocus();closePanels();});
    await query('reset');for(const line of lines){let r=await query('line '+line);if(r.preview){need('FIXTURE_VALID_PREVIEW',r.preview.valid===true,{line,r});r=await query('line confirm '+r.preview.token);}}
    need('FIXTURE_RENDERED',await page(async()=>{const ok=await renderObjects();await enterFocus('face',1);feSetTool('select');return ok===true;}));
    await settled();await page(()=>{window.__r116.rows.length=0;window.__r116.events.length=0;});
  };
  async function cleanup(){
    await page(()=>{if(window.__r116)window.__r116.blockReceipts=false;});
    if(await page(()=>!!window.__r116?.gate)){await page(()=>{window.__r116.gate.release();window.__r116.gate=null;});}
    if(offline){await send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});offline=false;if(await visible('#connectionRetry'))await ctl('#connectionRetry');}
    if(await page(()=>connection.phase==='error'&&pendingApiResults.size>0)){await ctl('#connectionRetry');await settled();}
    if(await page(()=>pendingApiResults.size>0))throw Error('R116 unresolved native confirmation; refusing to reset');
    await cancel();for(const pin of pins)await history.release(pin);pins.clear();
    await page(()=>{window.FaceContextMenu?.hide();window.CanvasContextMenu?.hide();closeMenus();});
  }
  const rerender=async()=>{await page(async()=>{await renderObjects();await enterFocus('face',1);feSetTool('select');});await settled();};
  const rawPreview=body=>page(async value=>{const response=await fetch('/timber-edit/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});return {status:response.status,result:await response.json()};},body);
  const rawTransaction=async operations=>({schema:'timber-edit-transaction/1',expectedRevision:String((await query('engineering-read')).revision),boundaryId:1,operations});
  const nativeRows=async(ids,label)=>{const result=await nativeRead(ids);check(label,result?.ok===true&&result.eligible===true&&same(result.timbers.map(t=>t.id),ids),result);return result.timbers;};
  const seedSources=async()=>{
    const operations=[{op:'put-parameter',value:{id:10,name:'section',nextFieldId:14,fields:[{id:5,name:'same one',type:'dimension',input:'27'},{id:13,name:'same two',type:'dimension',input:'27'}]}},
      ...[1,2].map(version=>({op:'publish-material',value:{id:'pine',version,kind:'timber',name:'pine',A:27,B:33}})),
      {op:'set-source',target:{kind:'timber',id:0,field:'A'},source:SOURCE_A.source},
      {op:'set-source',target:{kind:'timber',id:0,field:'B'},source:SOURCE_B.source},
      {op:'set-override',target:{kind:'timber',id:0,field:'A'},value:SOURCE_A.override}];
    const revision=(await query('engineering-read')).revision;
    const result=await page(async body=>{const response=await fetch('/engineering/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});return response.json();},{schema:'engineering-transaction/1',expectedRevision:revision,operations});
    need('TYPED_FIXTURE_PREVIEW',result?.ok&&result.preview?.valid,result);await query('engineering-confirm '+result.preview.token);await rerender();
    const actual=(await nativeRows([0],'TYPED_NATIVE_READ'))[0];
    need('TYPED_FIXTURE_EXACT',same(actual.definition.A,SOURCE_A)&&same(actual.definition.B,SOURCE_B),actual);return actual;
  };
  const engineeringFixture=async operations=>{
    const revision=(await query('engineering-read')).revision;
    const result=await page(async body=>{const response=await fetch('/engineering/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});return response.json();},{schema:'engineering-transaction/1',expectedRevision:revision,operations});
    need('ENGINEERING_FIXTURE_VALID',result?.ok&&result.preview?.valid,result);await query('engineering-confirm '+result.preview.token);await rerender();
  };
  const seedOwned=async()=>{
    await fixture(['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
      'timber 89 20 20 role boundary','place 89 on 1 at-face e0 +u +n',
      'spec left 500','spec right 2500','spec middle 1500','guide 1 1 v spec:left','guide 2 1 v spec:right','guide 3 1 u spec:middle',
      'timber 90 20 20 role boundary','place 90 on 1 at-face e2 +u +n']);
    const batch=async(family,operations)=>{
      const body={schema:family+'-transaction/1',expectedRevision:(await query('engineering-read')).revision,operations},route=family==='assembly-generation'?'/assembly/generate-preview':'/assembly/preview';
      const result=await page(async(url,value)=>{const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});return response.json();},route,body);
      need('OWNED_FIXTURE_VALID_NATIVE_PREVIEW',result?.ok&&result.preview?.valid,result);await query('assembly-confirm '+result.preview.token);
    };
    const rule={id:1,version:1,name:'R11 owner guard',slots:[{id:1,name:'main'},{id:2,name:'cross'}],members:[{id:1,slotId:1},{id:2,slotId:1},{id:3,slotId:2}],
      joints:[{id:1,kind:'end-to-side',scope:'left',terminatedMember:3,targetMember:1,end:'start',side:'+u',dir:'u'},
        {id:2,kind:'end-to-side',scope:'right',terminatedMember:3,targetMember:2,end:'finish',side:'-u',dir:'u'}]};
    const binding={id:1,name:'R11 owner binding',rule:{id:1,version:1},slots:[1,2].map(slotId=>({slotId,A:{kind:'literal',value:27},B:{kind:'literal',value:33},contactFace:'A',orientation:'A'}))};
    await batch('assembly',[{op:'publish-rule',value:rule},{op:'create-binding',value:binding}]);
    const state=(await query('assembly-read')).state,source={id:1,name:'owned',bindingId:1,rule:{id:1,version:1,fingerprint:state.rules[0].fingerprint},surfaceId:1,members:[1,2,3].map(memberId=>({memberId,role:memberId<3?'primary':'secondary',guideId:memberId,dir:memberId<3?'+v':'+u',depthSide:'+n',ends:memberId<3?{start:{kind:'timber',id:89},finish:{kind:'timber',id:90}}:{start:{kind:'member',memberId:1},finish:{kind:'member',memberId:2}}}))};
    await batch('assembly-generation',[{op:'create-instance',value:source,expectedBindingFingerprint:state.bindings[0].fingerprint}]);await rerender();
    return (await query('assembly-read')).state.instances[0].members[0].timberId;
  };
  const expectRecipeUnavailable=async(id,action,label)=>{
    await rightTimber(id);await ctl('#feCtxMenu [data-fe-act="reuse"]');await settled();
    const state=await page(s=>{const n=document.querySelector(s);return n&&{disabled:n.disabled||n.getAttribute('aria-disabled')==='true',text:n.textContent,title:n.title,footer:document.getElementById('feCtxMenu').textContent};},reuseItem(action));
    check(label,!!state?.disabled&&!!(state.text||state.title||state.footer),state);await key('Escape','Escape',27);
  };
  const saveFile=async()=>{
    const directory=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-r116-save-'));
    await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:directory});
    await page(()=>{window.__r116Picker=Object.getOwnPropertyDescriptor(window,'showSaveFilePicker');Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});});
    let file;
    try{await ctl('#projectBar [data-project-action="save"]');for(let i=0;i<150;i++){const files=fs.readdirSync(directory).filter(n=>n.endsWith('.gcanvas'));need('UNAMBIGUOUS_SAVE',files.length<2,files);if(files.length){file=path.join(directory,files[0]);break;}await sleep(100);}}
    finally{await page(()=>{if(window.__r116Picker)Object.defineProperty(window,'showSaveFilePicker',window.__r116Picker);else delete window.showSaveFilePicker;delete window.__r116Picker;});}
    check('FORMAL_SAVE_FILE',!!file&&fs.statSync(file).size>0,{directory,file});await settled();const bytes=new Uint8Array(fs.readFileSync(file));return {file,directory,bytes,loaded:await P.unpack(bytes,zip)};
  };
  const openFile=async(file,projectId)=>{
    await send('Page.setInterceptFileChooserDialog',{enabled:true});
    try{
      await page(()=>{window.__r116FileOpened=false;document.getElementById('projectFile').addEventListener('change',()=>window.__r116FileOpened=true,{once:true});});
      await ctl('#fileMenuBtn');
      if(await page(()=>ReferenceWorkspace.context().dirty))await expectNativeDialog(()=>ctl('#btnOpenProject'),{message:'目前專案有尚未保存的變更。要離開目前專案嗎？',accept:true});else await ctl('#btnOpenProject');
      const document=await send('DOM.getDocument',{depth:0}),node=await send('DOM.querySelector',{nodeId:document.result.root.nodeId,selector:'#projectFile'});need('FORMAL_OPEN_INPUT',node.result.nodeId>0);
      await send('DOM.setFileInputFiles',{nodeId:node.result.nodeId,files:[path.resolve(file)]});
      await wait('FORMAL_OPEN_FINISHED',"window.__r116FileOpened&&!ReferenceWorkspace.busy&&!document.getElementById('app').inert&&document.getElementById('projectFile').value===''");
      if(projectId)check('FORMAL_OPEN_PROJECT_ID',await page(id=>ReferenceWorkspace.getProjectState().id===id,projectId));await settled();
    }finally{await send('Page.setInterceptFileChooserDialog',{enabled:false});await page(()=>{delete window.__r116FileOpened;});}
  };
  const appReadyAfterNavigation=async()=>{
    let ready=false,lastError;
    for(let attempt=0;attempt<300;attempt++){
      try{ready=await page(()=>typeof api==='function'&&typeof oc==='object'&&typeof connection!=='undefined'&&connection.phase==='ready');}catch(e){lastError=e.message;}
      if(ready)break;await sleep(100);
    }
    need('NAVIGATION_RETURNED_TO_REAL_APP',ready,lastError);
  };
  const freshChild=async receipt=>{
    const runRoot=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-r116-fresh-')),profile=path.join(runRoot,'profile');fs.mkdirSync(profile);
    const receiptPath=path.join(runRoot,'saved-receipt.json'),logPath=path.join(runRoot,'child.log');
    const port=await new Promise((resolve,reject)=>{const socket=net.createServer();socket.once('error',reject);socket.listen(0,'127.0.0.1',()=>{const selected=socket.address().port;socket.close(error=>error?reject(error):resolve(selected));});});
    check('C07_NEW_USER_DATA_DIR_EMPTY',fs.readdirSync(profile).length===0&&path.resolve(profile)!==path.resolve(process.env.GEOMETRY_CHROME_PROFILE||'.'));
    fs.writeFileSync(receiptPath,JSON.stringify({...receipt,freshProfile:profile},null,2)+'\n');
    const env={...process.env};for(const name of Object.keys(env))if(/^GEOMETRY_.*_(?:ONLY|CASE|CASES)$/.test(name)||name==='GEOMETRY_CDP_FROM_P31'||name==='GEOMETRY_CDP_UPDATE_GOLDEN')delete env[name];
    Object.assign(env,{GEOMETRY_TIMBER_REUSE_ONLY:'1',GEOMETRY_TIMBER_REUSE_CASE:'C07',GEOMETRY_R116_FRESH_STAGE:'open',GEOMETRY_R116_FRESH_RECEIPT:receiptPath,GEOMETRY_CHROME_PROFILE:profile,GEOMETRY_CDP_PORT:String(port)});
    for(const pin of pins)await history.release(pin);pins.clear();await cancel();await page(()=>window.__r116.cleanup());
    let outcome,childText;
    try{
      await send('Page.navigate',{url:'about:blank'});
      const log=fs.openSync(logPath,'wx');
      try{outcome=await new Promise((resolve,reject)=>{const child=spawn(process.execPath,[path.join(__dirname,'cdp_test.js')],{env,stdio:['ignore',log,log]});child.once('error',reject);child.once('close',(code,signal)=>resolve({code,signal,pid:child.pid}));});}
      finally{fs.closeSync(log);}
      childText=fs.readFileSync(logPath,'utf8');
    }finally{
      await send('Page.navigate',{url:process.env.GEOMETRY_TEST_URL});await appReadyAfterNavigation();await page(installProbe);
      await openFile(receipt.file,receipt.projectId);await rerender();
    }
    const parse=prefix=>childText.split('\n').filter(line=>line.startsWith(prefix)).map(line=>JSON.parse(line.slice(prefix.length)));
    const results=parse('CDP_RESULT '),cases=parse('R116_CASE_RESULT '),summary=results[0];
    console.log('R116_FRESH_CHILD_RECEIPT '+JSON.stringify({outcome,profile,cdpPort:port,receiptPath,logPath,logSHA256:sha256(Buffer.from(childText)),results:results.length,cases:cases.length,completed:summary?.completed,failedAssertions:summary?.failedAssertions,uncaughtBrowserExceptions:summary?.uncaughtBrowserExceptions}));
    check('C07_FRESH_PROFILE_CHILD_COMPLETED',outcome?.code===0&&outcome.signal===null&&results.length===1&&summary.completed===true&&summary.failedAssertions===0&&summary.passedAssertions>0&&summary.uncaughtBrowserExceptions===0&&summary.scope.browserProfile===profile&&cases.length===1&&cases[0].id==='C07'&&cases[0].status==='pass',{outcome,summary,cases,logPath});
  };
  await page(installProbe);
  const cases={
    C01:async()=>{
      await fixture();await selectTimbers([0]);const baseline=await checkpoint(),original=(await nativeRows([0],'C01_NATIVE_ID_ZERO'))[0];
      await menu(0,'copy');await unchanged(baseline,'C01_COPY_READ_ONLY');await menu(0,'paste');
      check('C01_REUSE_CREATE_FORM',await page(()=>document.getElementById('timberEditForm')?.dataset.mode==='create'));
      check('C01_ANCHOR_REQUIRES_EXPLICIT_SELECTION',await page(()=>document.getElementById('tbAnchor')?.value===''));
      check('C01_NO_FORMAL_ALLOCATION_BEFORE_PREVIEW',(await dump())===baseline.world);
      await setPlacement('at-face e0');const rejected=await preview('C01_OVERLAP',{valid:false});
      check('C01_OVERLAP_NATIVE_RULE',Array.isArray(rejected.violations)&&rejected.violations.length>0,rejected);await unchanged(baseline,'C01_REJECT_AT_ORIGINAL_ANCHOR',{noWrites:false});await cancel();
      await menu(0,'paste');await setPlacement('at-face e2');const staged=await preview('C01_NEW_POSITION');
      check('C01_PRIVATE_PREVIEW_HANDLE',staged.after.length===1&&staged.after[0].handle==='new:0'&&!Object.hasOwn(staged.after[0],'id'),staged.after);
      check('C01_NATIVE_TYPED_RECIPE',same(staged.after[0].definition.A,original.definition.A)&&same(staged.after[0].definition.B,original.definition.B)&&staged.after[0].definition.placement.on===0);
      const request=(await rows(baseline.from)).filter(r=>r.path==='/timber-edit/preview').at(-1).body.operations[0];
      check('C01_NO_BAKED_LENGTH_OR_FORMAL_ID',same(Object.keys(request).sort(),['op','placement','recipeKey'])&&same(Object.keys(request.placement).sort(),['anchor','direction','on','selector','side']),request);
      await unchanged(baseline,'C01_CANCEL_CANDIDATE_PRIVATE',{noWrites:false});await cancel();await unchanged(baseline,'C01_CANCEL_ZERO_FORMAL_CHANGE',{noWrites:false});
      await menu(0,'paste');await setPlacement('at-face e2');await preview('C01_FINAL');const done=await confirm('C01');
      check('C01_NEW_ID_ONLY_AFTER_CONFIRM',same(done.created,[{handle:'new:0',kind:'timber',id:1}])&&done.changedIds.length===0,done);
      const final=await nativeRows([0,1],'C01_NEW_NATIVE_MEMBER');check('C01_ORIGINAL_UNCHANGED',same(final[0],original));
      check('C01_COPY_SOURCE_AND_NEW_ANCHOR',same(final[1].definition.A,original.definition.A)&&same(final[1].definition.B,original.definition.B)&&final[1].definition.placement.anchor==='at-face e2'&&final[1].geometry.length===4000);
      check('C01_ONE_HISTORY',await history.single(baseline.pin));
    },
    C02:async()=>{
      await fixture();await seedSources();const otherField={kind:'parameter',parameterId:10,fieldId:13};
      await engineeringFixture([{op:'set-source',target:{kind:'timber',id:0,field:'B'},source:otherField}]);
      const original=(await nativeRows([0],'C02_EQUAL_AXES_FIXTURE'))[0];need('C02_EQUAL_EFFECTIVE_DIFFERENT_FIELDS',original.effective.A===27&&original.effective.B===27&&!same(original.definition.A.source,original.definition.B.source),original);
      await selectTimbers([0]);await menu(0,'copy');await menu(0,'paste');
      check('C02_RECIPE_SHOWS_EXACT_TYPED_FIELDS',await page(()=>{const text=document.getElementById('timberEditForm').textContent;return text.includes('parameterId')&&text.includes('fieldId')&&text.includes('13')&&text.includes('5')&&text.includes('覆寫');}));
      await setPlacement('at-face e2');const candidate=await preview('C02_TYPED_PASTE');
      check('C02_TYPED_RECIPE_NOT_EFFECTIVE_NUMBERS',same(candidate.after[0].definition.A,original.definition.A)&&same(candidate.after[0].definition.B,original.definition.B),candidate.after);
      const created=await confirm('C02_PASTE'),id=created.created[0].id;const both=await nativeRows([0,id],'C02_NATIVE_TYPED_COPY');
      check('C02_AXES_AND_OVERRIDE_IDENTITIES_PRESERVED',both.every(t=>same(t.definition.A,original.definition.A)&&same(t.definition.B,original.definition.B)),both);
      await editSingle(id);await explicitSource('A',otherField,{kind:'literal',value:27});const beforeField=await checkpoint(),fieldCandidate=await preview('C02_EQUAL_VALUE_NEW_FIELD');
      check('C02_DIFFERENT_FIELD_IS_NOT_NOOP',fieldCandidate.noOp===false&&same(fieldCandidate.after[0].definition.A,{mode:'source',source:otherField,override:{kind:'literal',value:27}})&&fieldCandidate.after[0].effective.A===fieldCandidate.before[0].effective.A);
      await confirm('C02_FIELD');check('C02_FIELD_CHANGE_ONE_HISTORY',await history.single(beforeField.pin));
      await batch([0,id]);check('C02_EQUAL_NUMBERS_DIFFERENT_SOURCE_MARKED_MIXED',await page(()=>document.querySelector('[data-timber-mixed="A"]')?.textContent.includes('多種')));await cancel();
      await editSingle(id);await explicitSource('B',SOURCE_B.source);await preview('C02_MATERIAL_BASE');await confirm('C02_MATERIAL_BASE');
      await editSingle(id);const versionTwo={...SOURCE_B.source,version:2};await explicitSource('B',versionTwo);const beforeVersion=await checkpoint(),versionCandidate=await preview('C02_EQUAL_VALUE_NEW_VERSION');
      check('C02_DIFFERENT_VERSION_IS_NOT_NOOP',versionCandidate.noOp===false&&versionCandidate.before[0].effective.B===versionCandidate.after[0].effective.B&&same(versionCandidate.after[0].definition.B,{mode:'source',source:versionTwo,override:null}));
      await confirm('C02_VERSION');check('C02_VERSION_CHANGE_ONE_HISTORY',await history.single(beforeVersion.pin));
      const final=(await nativeRows([id],'C02_FINAL_NATIVE_SOURCE'))[0];check('C02_OTHER_AXIS_OVERRIDE_RETAINED',same(final.definition.A,{mode:'source',source:otherField,override:{kind:'literal',value:27}}));
      await ctl('#faceUndoButton');await settled();const undone=(await nativeRows([id],'C02_UNDO_NATIVE_SOURCE'))[0];check('C02_UNDO_RESTORES_VERSION_IDENTITY',same(undone.definition.B,SOURCE_B)&&same(undone.definition.A,final.definition.A));
    },
    C03:async()=>{
      await fixture(PAIR_FIXTURE);await batch([0,7]);const baseline=await checkpoint();
      const fields=await page(()=>[...document.querySelectorAll('[data-timber-patch]')].map(n=>({field:n.dataset.timberPatch,checked:n.checked,text:n.closest('label')?.textContent||n.parentElement.textContent})));
      check('C03_KEEP_EACH_ORIGINAL_DEFAULT',fields.length===5&&fields.every(f=>!f.checked),fields);
      check('C03_MIXED_MARKED',await page(()=>document.getElementById('timberEditForm').textContent.includes('多種')));
      const emptyEnabled=await page(()=>!document.getElementById('timberEditPreview').disabled);
      if(emptyEnabled){await ctl('#timberEditPreview');await settled();}
      await unchanged(baseline,'C03_EMPTY_PATCH');
      await explicit('B',33);const noOp=await preview('C03_SAME_DEFINITION');
      check('C03_NATIVE_NOOP_TOKEN_NULL',noOp.noOp===true&&noOp.token===null,noOp);
      const writes=await rows(baseline.from);check('C03_NOOP_NEVER_CONFIRMS',!writes.some(r=>r.command.startsWith('timber-edit-confirm ')),writes);
      await unchanged(baseline,'C03_NOOP',{noWrites:false});
    },
    C04:async()=>{
      await fixture(ATOMIC_FIXTURE);const baseline=await checkpoint(),definitions=await nativeRows([90,91,1,2],'C04_NATIVE_FIXTURE');
      const single=await rawPreview(await rawTransaction([{op:'update-timber-fields',id:1,fields:{A:{mode:'direct',value:50}}}]));
      need('C04_INTERMEDIATE_IS_INVALID',single.result?.ok&&single.result.preview?.valid===false,single);await query('timber-edit-cancel '+single.result.preview.token);
      await batch([1,2]);await explicit('A',50);const final=await preview('C04_FINAL_PAIR');
      const trace=await rows(baseline.from),requests=trace.filter(r=>r.path==='/timber-edit/preview');
      check('C04_ALL_EXPLICIT_PATCHES_ONE_CANDIDATE',same(requests.at(-1).body.operations,[1,2].map(id=>({op:'update-timber-fields',id,fields:{A:{mode:'direct',value:50}}}))),requests);
      check('C04_FINAL_REVALIDATION_ACCEPTS_PAIR',final.valid===true&&same(final.after.map(t=>[t.id,t.definition.A.value]),[[1,50],[2,50]]),final);
      check('C04_COMPLETE_DEPENDENCIES',same(final.dependencies.timbers.map(t=>t.id),[90,91,1,2])&&same(final.dependencies.guides.map(g=>g.id),[1,2]),final.dependencies);
      await confirm('C04');const committed=await dump();check('C04_SINGLE_HISTORY_STEP',await history.single(baseline.pin));
      const after=await nativeRows([90,91,1,2],'C04_NATIVE_FINAL');check('C04_SUPPORTS_UNCHANGED',same(after.slice(0,2),definitions.slice(0,2)));
      await ctl('#faceUndoButton');await settled();check('C04_UNDO_WHOLE_WORLD',(await dump())===baseline.world);
      await ctl('#faceRedoButton');await settled();check('C04_REDO_WHOLE_WORLD',(await dump())===committed);
      await batch([90,1,2]);const rejectedBase=await checkpoint();await explicit('A',9999);const rejected=await preview('C04_THREE_TARGET_REJECTION',{valid:false});
      const three=(await rows(rejectedBase.from)).find(r=>r.path==='/timber-edit/preview').body.operations;
      check('C04_NO_FILTER_OF_INVALID_TARGETS',same(three.map(op=>op.id),[90,1,2])&&three.every(op=>op.fields.A.value===9999),three);
      check('C04_REJECTION_NAMES_NATIVE_RULE',rejected.violations.length>0,rejected.violations);await unchanged(rejectedBase,'C04_ALL_OR_NOTHING',{noWrites:false});
    },
    C05:async()=>{
      for(const alter of ['unknown','group','owner']){
        await fixture(PAIR_FIXTURE);const native=await nativeRead([0,7]);need('C05_NATIVE_ORDINARY_FIXTURE',native.ok&&native.eligible&&native.timbers.every(t=>t.groupsKnown&&t.groups.length===0&&t.owner===null),native);
        await selectTimbers([0]);const baseline=await checkpoint();await page(mode=>window.__r116.arm('/timber-edit/read','','eligibility',mode),alter);await batch([0,7]);
        const gate=await page(()=>window.__r116.gate&&{phase:window.__r116.gate.phase,claims:window.__r116.gate.claims,nativeOK:window.__r116.gate.nativeOK});need('C05_FAULT_WAS_REAL_NATIVE_RESPONSE',gate?.phase==='released'&&gate.claims===1&&gate.nativeOK,gate);
        check('C05_'+alter.toUpperCase()+'_WHOLE_SELECTION_DISABLED',await page(()=>document.getElementById('timberEditPreview').disabled&&/所有權|群組|未知|資格/.test(document.getElementById('timberEditStatus').textContent)));
        check('C05_'+alter.toUpperCase()+'_NO_PREVIEW_OR_FILTER',!(await rows(baseline.from)).some(r=>r.path==='/timber-edit/preview'));
        await unchanged(baseline,'C05_'+alter.toUpperCase());await page(()=>{window.__r116.gate=null;});
      }
      const ownedId=await seedOwned(),ids=[89,ownedId],readBack=await nativeRead(ids);
      need('C05_REAL_ASSEMBLY_FIXTURE',readBack.ok&&readBack.timbers.some(t=>t.owner)&&readBack.timbers.some(t=>t.owner===null),readBack);
      const owner=readBack.timbers.find(t=>t.owner),ordinary=readBack.timbers.find(t=>t.owner===null&&t.eligible);
      need('C05_OWNER_AND_ORDINARY',!!owner&&!!ordinary);await selectTimbers([owner.id]);const baseline=await checkpoint();
      await expectRecipeUnavailable(owner.id,'copy','C05_NATIVE_OWNER_NOT_REUSABLE');await batch([ordinary.id,owner.id]);
      check('C05_MIXED_OWNER_WHOLE_SELECTION_DISABLED',await page(()=>document.getElementById('timberEditPreview').disabled));
      const rejected=await rawPreview({...await rawTransaction([ordinary.id,owner.id].map(id=>({op:'update-timber-fields',id,fields:{B:{mode:'direct',value:34}}}))),boundaryId:1});
      check('C05_NATIVE_OWNER_REJECTS_BYPASS',rejected.result?.ok===false,rejected);await unchanged(baseline,'C05_OWNER_ALL_OR_NOTHING',{noWrites:false});
    },
    C06:async()=>{
      await fixture(PAIR_FIXTURE);await selectTimbers([0]);await menu(0,'copy');const viewBaseline=await checkpoint();
      await page(()=>{fe.panX+=11;fe.panY-=7;fe.zoom*=1.05;drawFaceEditor();});await menu(0,'paste');
      check('C06_PAN_ZOOM_KEEPS_RECIPE',await page(()=>document.getElementById('timberEditForm')?.dataset.mode==='create'));await cancel();await unchanged(viewBaseline,'C06_VIEW_ONLY');
      const worldBefore=await dump(),revisionBefore=(await query('engineering-read')).revision;await ctl('#faceUndoButton');await settled();await ctl('#faceRedoButton');await settled();
      need('C06_IDENTICAL_DUMP_NEW_NATIVE_GENERATION',(await dump())===worldBefore&&(await query('engineering-read')).revision!==revisionBefore);
      await rerender();
      await selectTimbers([0]);await expectRecipeUnavailable(0,'paste','C06_UNDO_REDO_INVALIDATES_RECIPE');
      await batch([0,7]);await explicit('B',34);const baseline=await checkpoint();await page(()=>window.__r116.arm('/timber-edit/preview'));await ctl('#timberEditPreview');
      await wait('C06_REAL_PREVIEW_HELD',"window.__r116.gate?.phase==='held'&&window.__r116.gate.nativeOK===true");
      // Adversarial selection reorder during an actual in-flight native reply.
      // This is the production selection API; no candidate/adapter is replaced.
      await page(()=>{feSetTimberSelection([7,0]);renderFaceInspector();});
      await page(()=>window.__r116.gate.release());await settled();await page(()=>{window.__r116.gate=null;});
      check('C06_LATE_REPLY_CANNOT_REOPEN_CONFIRM',await page(()=>document.getElementById('timberEditConfirm')?.hidden!==false));
      check('C06_SELECTION_ORDER_RETAINED',same(await selection(),[7,0]));
      check('C06_LATE_REPLY_CANCELS_OWN_TOKEN', (await rows(baseline.from)).some(r=>r.command.startsWith('timber-edit-cancel '))&&!(await rows(baseline.from)).some(r=>r.command.startsWith('timber-edit-confirm ')));
      await unchanged(baseline,'C06_SELECTION_REORDER',{noWrites:false});await cancel();
      await selectTimbers([0]);await menu(0,'copy');const oldDefinition=(await nativeRows([0],'C06_RECREATE_BASELINE'))[0].definition;
      await line('preview delete timber 0');await line('timber 0 27 33 role boundary');await line('place 0 on 0 at-face e0 +u +n');await rerender();
      check('C06_RECREATED_SAME_ID_SAME_DEFINITION',same((await nativeRows([0],'C06_RECREATED_NATIVE'))[0].definition,oldDefinition));
      await selectTimbers([0]);await expectRecipeUnavailable(0,'paste','C06_RECREATE_SAME_ID_INVALIDATES_RECIPE');
      await menu(0,'copy');await query('line boundary 2 outline 0,0 4000,0 4000,3000 0,3000');await query('line placement 2 on boundary 2 origin 5000 0 2500 u +x v +y');await rerender();
      await selectTimbers([0]);await menu(0,'copy');await page(async()=>{await enterFocus('face',2);await enterFocus('face',1);});await settled();
      await selectTimbers([0]);await expectRecipeUnavailable(0,'paste','C06_FACE_CONTEXT_CHANGE_INVALIDATES_RECIPE');
      await menu(0,'copy');const saved=await saveFile();await openFile(saved.file,saved.loaded.manifest.projectId);await rerender();await selectTimbers([0]);
      await expectRecipeUnavailable(0,'paste','C06_FORMAL_PROJECT_OPEN_INVALIDATES_RECIPE');
    },
    C07:async()=>{
      if(process.env.GEOMETRY_R116_FRESH_STAGE==='open'){
        const receipt=JSON.parse(fs.readFileSync(process.env.GEOMETRY_R116_FRESH_RECEIPT,'utf8'));
        need('C07_FRESH_RECEIPT_SCHEMA',receipt.schema==='r116-fresh-profile/1'&&receipt.file&&Array.isArray(receipt.ids),receipt);
        check('C07_SEPARATE_PROFILE_PATH',process.env.GEOMETRY_CHROME_PROFILE===receipt.freshProfile);
        const fresh=await page(()=>window.__r116FreshStart);check('C07_NO_PRIOR_BROWSER_STORAGE',fresh&&same(fresh.local,[])&&same(fresh.session,[]),fresh);
        check('C07_FILE_BYTES_MATCH_SAVED_RECEIPT',sha256(fs.readFileSync(receipt.file))===receipt.fileSHA256);
        await openFile(receipt.file,receipt.projectId);await rerender();
        check('C07_FRESH_OPEN_EXACT_SCENE',(await dump())===receipt.scene);
        const reopened=await nativeRows(receipt.ids,'C07_FRESH_NATIVE_ROWS');check('C07_FRESH_TYPED_DEFINITIONS_AND_OVERRIDE',same(reopened,receipt.rows),{expected:receipt.rows,reopened});
        await selectTimbers([receipt.ids[0]]);await expectRecipeUnavailable(receipt.ids[0],'paste','C07_NO_SAVED_CLIPBOARD');await expectRecipeUnavailable(receipt.ids[0],'repeat','C07_NO_SAVED_REPEAT');
        check('C07_NO_SAVED_CANDIDATE',await page(()=>!document.getElementById('timberEditConfirm')||document.getElementById('timberEditConfirm').hidden));return;
      }
      await fixture();await seedSources();await selectTimbers([0]);await menu(0,'copy');await menu(0,'paste');await setPlacement('at-face e2');await preview('C07_CONFIRMED_COPY');const created=await confirm('C07_CREATE'),id=created.created[0].id;
      const confirmedScene=await dump(),typedRows=await nativeRows([0,id],'C07_CONFIRMED_TYPED_ROWS');
      await menu(id,'repeat');check('C07_UNCONFIRMED_FORM_PRESENT',await page(()=>document.getElementById('timberEditForm')?.dataset.mode==='create'));
      const keys=(await rows(0)).map(row=>row.result?.recipeKey).filter(Boolean),saved=await saveFile();
      check('C07_SAVE_CONTAINS_ONLY_CONFIRMED_SCENE',saved.loaded.scene===confirmedScene);
      const metadata=JSON.stringify(saved.loaded.manifest);check('C07_RECIPES_CANDIDATES_NOT_SERIALIZED',keys.length>0&&keys.every(value=>!metadata.includes(value)&&!saved.loaded.scene.includes(value))&&!metadata.includes('timber-edit-transaction/1')&&!metadata.includes('create-from-recipe'));
      console.log('R116_ARTIFACT '+JSON.stringify({case:'C07',file:saved.file,fileSHA256:sha256(saved.bytes),format:saved.loaded.manifest.format}));
      await freshChild({schema:'r116-fresh-profile/1',file:saved.file,fileSHA256:sha256(saved.bytes),projectId:saved.loaded.manifest.projectId,scene:confirmedScene,ids:[0,id],rows:typedRows});
    },
    C08:async()=>{
      await fixture();await selectTimbers([0]);await menu(0,'copy');const baseline=await checkpoint();
      await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});await page(()=>closePanels());await ctl('#feZoomFit');await rightTimber(0);
      const menuRect=await page(()=>{const r=document.getElementById('feCtxMenu').getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:innerWidth,height:innerHeight,overflow:document.documentElement.scrollWidth>innerWidth+1};});
      check('C08_390_MENU_REACHABLE',menuRect.left>=-1&&menuRect.right<=390+1&&menuRect.top>=-1&&menuRect.bottom<=844+1&&!menuRect.overflow,menuRect);
      await ctl('#feCtxMenu [data-fe-act="reuse"]');await ctl(reuseItem('paste'));await settled();await setPlacement('at-face e2');
      const formRect=await page(()=>{const form=document.getElementById('timberEditForm');return {pageOverflow:document.documentElement.scrollWidth>innerWidth+1,formOverflow:form.scrollWidth>form.clientWidth+1};});
      check('C08_390_FORM_NO_HORIZONTAL_OVERFLOW',!formRect.pageOverflow&&!formRect.formOverflow,formRect);
      await fill('#tbSelector','text clipboard');await key('a','KeyA',65,2);await key('c','KeyC',67,2);await fill('#tbSelector','replacement');await key('a','KeyA',65,2);await key('v','KeyV',86,2);await sleep(150);
      check('C08_INPUT_TEXT_COPY_PASTE_RETAINED',await page(()=>document.getElementById('tbSelector').value==='text clipboard'));
      const beforeComposition=await mark();await send('Input.imeSetComposition',{text:'中',selectionStart:1,selectionEnd:1});await key('Enter','Enter',13);await sleep(120);
      check('C08_CDP_COMPOSITION_DID_NOT_COMMIT',!(await rows(beforeComposition)).some(r=>r.path==='/timber-edit/preview'||r.command.startsWith('timber-edit-confirm '))&&await page(()=>!!document.getElementById('timberEditForm')));
      check('C08_TRUSTED_COMPOSITION_OBSERVED',await page(()=>window.__r116.events.some(e=>e.type==='compositionstart'&&e.trusted)),await page(()=>window.__r116.events.slice(-12)));
      await key('Escape','Escape',27);check('C08_COMPOSING_ESCAPE_LEAVES_FORM',await page(()=>document.getElementById('timberEditForm')?.dataset.mode==='create'));
      await send('Input.imeSetComposition',{text:'',selectionStart:0,selectionEnd:0});await fill('#tbSelector','');await ctl('#tbSelector');await key('Escape','Escape',27);await settled();
      check('C08_ESCAPE_CLOSES_OWN_FORM',await page(()=>!document.getElementById('timberEditForm')||document.getElementById('timberEditForm').dataset.mode!=='create'));
      check('C08_ESCAPE_RESTORES_CANVAS_FOCUS',await page(()=>document.activeElement===document.getElementById('faceEditorViewport')));
      await unchanged(baseline,'C08_TEXT_IME_ESCAPE');
      console.log('R116_DEVICE_LIMIT '+JSON.stringify({case:'C08',tested:'Chrome CDP at 390 CSS px with trusted CDP composition',notClaimed:['physical Chinese IME','iOS Safari','Android','TalkBack','Pencil']}));
    },
    C09:async()=>{
      await fixture(PAIR_FIXTURE);await batch([0,7]);await explicit('B',34);const before=await checkpoint();await preview('C09_SEALED_INPUT');
      // Programmatic value changes model a late form writer without an input
      // event. The trusted confirm click must still compare the displayed raw form.
      await page(()=>{document.getElementById('timberEditBValue').value='35';});await ctl('#timberEditConfirm');await settled();
      check('C09_FINAL_RAW_FORM_GUARD',!(await rows(before.from)).some(r=>r.command.startsWith('timber-edit-confirm ')));
      await unchanged(before,'C09_SEALED_VISIBLE_INPUT',{noWrites:false});await cancel();await reopenBatchFromMenu([0,7]);await explicit('B',34);await preview('C09_DOUBLE_CONFIRM');
      const beforeDouble=await checkpoint(),point=await page(()=>{const n=document.getElementById('timberEditConfirm'),r=n.getBoundingClientRect();window.__r116OldConfirm=n;return{x:r.x+r.width/2,y:r.y+r.height/2};});
      await page(()=>window.__r116.arm('/api','timber-edit-confirm '));await ctl('#timberEditConfirm');await wait('C09_CONFIRM_ACTUALLY_HELD',"window.__r116.gate?.phase==='held'");
      for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,...point,button:'left',clickCount:1});
      await page(()=>window.__r116.gate.release());await settled();await page(()=>{window.__r116.gate=null;window.__r116OldConfirm.click();delete window.__r116OldConfirm;});await settled();
      check('C09_DOUBLE_AND_DETACHED_CONFIRM_ONCE',(await rows(beforeDouble.from)).filter(r=>r.command.startsWith('timber-edit-confirm ')).length===1);
      check('C09_DOUBLE_CONFIRM_ONE_HISTORY',await history.single(beforeDouble.pin));
    },
    C10:async()=>{
      const lines=[...ATOMIC_FIXTURE.slice(0,-4),...ATOMIC_FIXTURE.slice(-2),...ATOMIC_FIXTURE.slice(-4,-2)];
      await fixture(lines);const before=await nativeRows([90,91,2,1],'C10_NON_ID_PLACEMENT_ORDER'),sources=(await query('engineering-read')).state.sources;
      need('C10_ORDER_FIXTURE',BigInt(before[2].placementOrder)<BigInt(before[3].placementOrder));
      await batch([2,1]);await explicit('B',35);const baseline=await checkpoint();await preview('C10_IN_PLACE');await confirm('C10');
      const after=await nativeRows([90,91,2,1],'C10_READ_BACK');
      check('C10_IDS_ORDER_AND_PLACEMENTS_RETAINED',before.every((t,i)=>t.id===after[i].id&&t.placementOrder===after[i].placementOrder&&same(t.definition.placement,after[i].definition.placement)),after);
      check('C10_UNSELECTED_FIELDS_RETAINED',before.every((t,i)=>same(t.definition.A,after[i].definition.A)&&t.definition.role===after[i].definition.role&&t.definition.priority===after[i].definition.priority));
      check('C10_B_ONLY_SELECTED_TARGETS',same(after.map(t=>t.definition.B),[{mode:'direct',value:20},{mode:'direct',value:20},{mode:'direct',value:35},{mode:'direct',value:35}]));
      check('C10_SOURCES_UNCHANGED',same((await query('engineering-read')).state.sources,sources));
      const commands=(await rows(baseline.from)).filter(r=>r.path==='/api'&&!READ_COMMAND.test(r.command));
      check('C10_NO_DELETE_RECREATE_OR_PER_OBJECT_COMMIT',commands.length===1&&commands[0].command.startsWith('timber-edit-confirm '),commands);check('C10_ONE_HISTORY',await history.single(baseline.pin));
      await editSingle(1);await explicit('role','custom');const exactPriority='9007199254740993';await explicit('priority',exactPriority);const precisionBase=await checkpoint();
      const precise=await preview('C10_EXACT_PRIORITY'),precisionRequest=(await rows(precisionBase.from)).find(r=>r.path==='/timber-edit/preview').body.operations;
      check('C10_PRIORITY_WIRE_IS_EXACT_STRING',precisionRequest.length===1&&precisionRequest[0].id===1&&precisionRequest[0].fields.priority===exactPriority&&precisionRequest[0].fields.role==='custom',precisionRequest);
      check('C10_PREVIEW_PRIORITY_TEXT_EXACT',precise.after[0].definition.priorityText===exactPriority,precise.after[0].definition);await confirm('C10_EXACT_PRIORITY');
      const preciseNative=(await nativeRows([1],'C10_EXACT_PRIORITY_NATIVE'))[0];
      check('C10_NATIVE_PRIORITY_TEXT_EXACT',preciseNative.definition.priorityText===exactPriority&&preciseNative.placementOrder===after[3].placementOrder&&same(preciseNative.definition.placement,after[3].definition.placement),preciseNative);
      check('C10_PRECISE_PRIORITY_ONE_HISTORY',await history.single(precisionBase.pin));
    },
    C11:async()=>{
      await fixture(REPEAT_FIXTURE);await selectTimbers([1]);await expectRecipeUnavailable(1,'repeat','C11_REPEAT_REQUIRES_LAST_SUCCESSFUL_CREATE');
      await rightTimber(1);check('C11_REDUNDANT_PLACEHOLDERS_ABSENT',await page(()=>document.querySelectorAll('#feCtxMenu [data-fe-act="reuse"]').length===1&&!document.querySelector('#feCtxMenu [data-fe-act="copy"],#feCtxMenu [data-fe-act="paste"]')));
      check('C11_DUPLICATE_FLOATING_ACTIONS_SUPPRESSED',await page(()=>document.getElementById('feActionBar').classList.contains('fcm-suppressed')));await key('Escape','Escape',27);
      const baseline=await checkpoint();await menu(1,'copy');
      const menuText=await page(()=>document.getElementById('feCtxMenu').textContent);
      check('C11_OLD_DISABLED_PLACEHOLDERS_REMOVED',!menuText.includes('複製未實作')&&!menuText.includes('貼上未實作'),menuText);
      await menu(1,'paste');check('C11_SHARED_CREATE_FORM',await page(()=>document.querySelectorAll('#timberEditForm').length===1&&!!document.querySelector('#faceInspectorContent #timberEditForm')&&!document.querySelector('dialog #timberEditForm')));
      await setPlacement('at-line guide 3','+v');await preview('C11_PASTE');const done=await confirm('C11_PASTE');const id=done.created[0].id;
      await menu(id,'repeat');check('C11_REPEAT_REQUIRES_NEW_ANCHOR',await page(()=>document.getElementById('tbAnchor')?.value===''));
      await setPlacement('at-line guide 4','+v');await preview('C11_REPEAT');const repeated=await confirm('C11_REPEAT');
      check('C11_REPEAT_CREATES_NEW_MEMBER',repeated.created.length===1&&repeated.created[0].id!==id&&repeated.created[0].id!==0&&repeated.changedIds.length===0,repeated);
      const originals=await nativeRows([id,repeated.created[0].id],'C11_REPEAT_TYPED_RECIPE');check('C11_REPEAT_SAME_DEFINITION_NEW_PLACEMENT',same(originals[0].definition.A,originals[1].definition.A)&&same(originals[0].definition.B,originals[1].definition.B)&&originals[0].definition.role===originals[1].definition.role&&originals[1].definition.placement.anchor==='at-line guide 4');
      await batch([1,id]);await explicit('B',34);await preview('C11_BATCH');await confirm('C11_BATCH');
      await expectRecipeUnavailable(1,'repeat','C11_MODIFICATION_IS_NOT_REPEATABLE_CREATE');
      check('C11_MENU_TO_NATIVE_ENTRY', (await rows(baseline.from)).filter(r=>r.path==='/timber-edit/preview').length===3);
    },
    C12:async()=>{
      await fixture();await selectTimbers([0]);const initial=await checkpoint(),readBack=await nativeRead([0]);
      const operation={op:'update-timber-fields',id:0,fields:{B:{mode:'direct',value:34}}},base=await rawTransaction([operation]);
      const bad=[['duplicate-target',{...base,operations:[operation,operation]}],['unknown-field',{...base,operations:[{...operation,fields:{B:{mode:'direct',value:34},placement:{on:0}}}]}],['unknown-key',{...base,unexpected:true}],['invalid-anchor',{...base,operations:[{op:'create-from-recipe',recipeKey:readBack.recipeKey,placement:{on:0,anchor:'at-face e2 timber 123 27 33',selector:'',direction:'+u',side:'+n'}}]}],['stale-key',{...base,operations:[{op:'create-from-recipe',recipeKey:'0'.repeat(64),placement:{on:0,anchor:'at-face e2',selector:'',direction:'+u',side:'+n'}}]}]];
      for(const [label,body] of bad){const reply=await rawPreview(body);check('C12_REJECT_'+label.toUpperCase().replaceAll('-','_'),reply.result?.ok===false,reply);}
      await unchanged(initial,'C12_INVALID_WIRE_ZERO_FORMAL_CHANGE',{noWrites:false});
      await menu(0,'copy');await menu(0,'paste');await setPlacement('at-face e2');await preview('C12_LOST_REPLY');const before=await checkpoint();
      await page(()=>{window.__r116.blockReceipts=true;window.__r116.arm('/api','timber-edit-confirm ','drop');});await ctl('#timberEditConfirm');
      await wait('C12_UNKNOWN_RESULT_VISIBLE',"connection.phase==='error'&&window.__r116.pending===0");
      const uncertain=await rows(before.from),confirmCalls=uncertain.filter(r=>r.command.startsWith('timber-edit-confirm '));
      check('C12_CONFIRM_HAS_REQUEST_RECEIPT',confirmCalls.length===1&&typeof confirmCalls[0].body.requestId==='string'&&confirmCalls[0].result?.ok===true,confirmCalls);
      check('C12_UNKNOWN_RESULT_HOLDS_OWNER',await page(()=>{let blocked=false;try{ReferenceWorkspace.assertAssemblyIdle();}catch(_){blocked=true;}return blocked&&ReferenceWorkspace.getProjectInfo().editingBlocked&&pendingApiResults.size===1;}));
      check('C12_HISTORY_NOT_GUESSED',await history.unchanged(before.pin));
      const unknownMark=await mark(),refused=await page(()=>apiRequest('reset'));
      check('C12_UNKNOWN_RESULT_BLOCKS_WRITES',refused?.ok===false&&(await rows(unknownMark)).length===0,refused);
      await page(()=>{window.__r116.blockReceipts=false;window.__r116.gate=null;});await ctl('#connectionRetry');await settled();
      const recovered=await rows(before.from),receipts=recovered.filter(r=>r.body.receipt);
      check('C12_QUERY_RECEIPT_NEVER_RESEND',recovered.filter(r=>r.command.startsWith('timber-edit-confirm ')).length===1&&receipts.some(r=>r.body.receipt===confirmCalls[0].body.requestId&&r.result?.ok===true),recovered);
      check('C12_OWNER_RELEASED_AFTER_REAL_RECEIPT',await page(()=>{try{ReferenceWorkspace.assertAssemblyIdle();return pendingApiResults.size===0;}catch(_){return false;}}));
      check('C12_RECOVERED_EXACTLY_ONE_HISTORY',await history.single(before.pin));
      const final=await nativeRows([0,1],'C12_RECOVERED_NATIVE_OBJECTS');check('C12_NO_DUPLICATE_AFTER_RECONNECT',final.length===2&&(await query('references')).timbers.length===2);
      await rerender();await selectTimbers([0]);
      await expectRecipeUnavailable(0,'paste','C12_RECONNECT_INVALIDATES_COPY');
    }
  };
  const results=[];
  for(const id of selected){
    currentCase=id;const beforeExceptions=exceptionCount();let result={id,status:'pass',kind:null,assertion:null,error:null};
    try{await cases[id]();if(exceptionCount()!==beforeExceptions)throw fault('exception','UNCAUGHT_BROWSER_EXCEPTION','Unhandled browser exception');}
    catch(e){const kind=e.r116?.kind||'exception';result={id,status:kind==='assertion'?'fail':'error',kind,assertion:e.r116?.assertion||'UNEXPECTED_EXCEPTION',error:e.message};}
    try{await cleanup();}catch(e){result={id,status:'error',kind:'cleanup',assertion:'CLEANUP_FAILED',error:e.message,firstFailure:result};}
    results.push(result);console.log('R116_CASE_RESULT '+JSON.stringify(result));if(result.kind==='cleanup')break;
  }
  await page(()=>window.__r116?.cleanup());
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  if(results.length!==selected.length||results.some(r=>r.status==='error'))throw Error('R116 incomplete cases: '+results.filter(r=>r.status!=='pass').map(r=>r.id+'/'+r.assertion).join(','));
};
module.exports.caseIds=CASE_IDS;module.exports.selectCases=selectCases;
