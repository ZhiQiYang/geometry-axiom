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
