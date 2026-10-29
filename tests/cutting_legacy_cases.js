/* Fixed inputs for the independent cd4bc880 cutting oracle; no product imports. */
'use strict';
const material={id:'wood',version:1,fingerprint:'b'.repeat(64)};
const timber=(id,L,surface=1,A=27,B=33)=>({id,role:'primary',geometry:{surface,A,B,length:L,dir:'+v',side:'+n',origin:[0,0,0],axes:[[0,1,0],[1,0,0],[0,0,1]]}});
const refs=lengths=>({ok:true,sourceFingerprint:'a'.repeat(64),timbers:lengths.map((L,i)=>timber(i+1,L)),engineeringSources:[]});
const settings=(length=3636,endTrim=5)=>({kerf:3,allowance:0,minRemnant:300,stockTypes:[{key:1,name:'試用料',section:[27,33],material:null,length,endTrim}],remnants:[],nextStockKey:2,nextRemnantKey:1});
const request=(scopes=[{surface:1,ids:null}])=>({world:{kind:'live'},scopes});
function source(r,id,terminal,field='A'){
 const row={target:{kind:'timber',id,field},path:'不可解析的顯示文字'};
 if(terminal!==undefined)row.terminal=terminal;
 r.engineeringSources.push(row);
}
function cases(){
 const out=[];
 const add=(id,r=refs([100]),s=settings(),q=request())=>{const c={id,action:'evaluate',references:r,settings:s,request:q};out.push(c);return c;};
 add('ffd-success',refs([2560,2560,890,890,890,876]));
 add('empty-request',null,settings(),request([]));
 add('world-kind',refs([100]),settings(),{world:{kind:'model:1'},scopes:[{surface:1,ids:null}]});
 add('world-unreadable',{...refs([100]),ok:false});
 add('empty-scope',refs([]));
 add('unknown-scope',refs([100]),settings(),request([{surface:9,ids:null}]));
 add('stale-selection',refs([100]),settings(),request([{surface:1,ids:[9]}]));
 add('surface-mismatch',refs([100]),settings(),request([{surface:2,ids:[1]}]));
 add('invalid-scope-id',refs([100]),settings(),request([{surface:-1,ids:null}]));
 add('missing-scopes',refs([100]),settings(),{world:{kind:'live'}});
 add('scope-capacity',refs([1]),settings(),request(Array.from({length:65},()=>({surface:1,ids:null}))));
 add('demand-capacity',refs(Array(4097).fill(1)));
 for(const field of ['kerf','allowance','minRemnant']){const s=settings();s[field]=null;add('missing-'+field,refs([100]),s);}
 add('over-length',refs([3700]));
 {const r=refs([3700,100]),s=settings();r.timbers[1].geometry.A=30;r.timbers[1].geometry.B=36;s.kerf=null;add('diagnostic-phase-order',r,s);}
 for(const [name,terminal]of [['unresolved-terminal',null],['mixed-material',{kind:'material',...material}],['missing-terminal',undefined]]){const r=refs([100]);source(r,1,terminal);add(name,r);}
 {const r=refs([100,100]),s=settings();for(const field of ['A','B'])source(r,1,{kind:'material',...material},field);r.timbers[0].geometry.A=33;r.timbers[0].geometry.B=27;s.stockTypes.push({...s.stockTypes[0],key:2,material});s.nextStockKey=3;add('material-triplet-and-unordered-section',r,s);}
 for(const [name,mat,section]of [['no-stock',null,[27,33]],['material-fingerprint',{...material,fingerprint:'c'.repeat(64)},[27,33]],['stock-section',material,[30,36]]]){const r=refs([100]),s=settings();for(const field of ['A','B'])source(r,1,{kind:'material',...material},field);s.stockTypes[0].material=mat;s.stockTypes[0].section=section;add(name,r,s);}
 {const r=refs([3200,3100,3200,3100]),s=settings(3000,5);for(const id of [3,4])for(const field of ['A','B'])source(r,id,{kind:'material',...material},field);s.stockTypes.push({...s.stockTypes[0],key:2,material});s.nextStockKey=3;s.remnants=[{key:1,stockType:1,length:3300,headTrim:0,tailTrim:5},{key:2,stockType:2,length:3300,headTrim:0,tailTrim:5}];s.nextRemnantKey=3;add('remnant-exhaustion-every-group',r,s);}
 {const r=refs([100]);r.timbers=[timber(0,100,0),timber(1,100,0),timber(7,100,2)];add('zero-and-union-identity',r,settings(),request([{surface:0,ids:null},{surface:0,ids:[0]},{surface:2,ids:[7]}]));}
 add('exact-finish-trim',refs([3626]));
 for(const [name,last]of [['original-end',1497],['short-last-kerf',1496],['normal-last-kerf',1490]])add(name,refs([1500,last]),settings(3000,0));
 add('remnant-threshold-equal',refs([3323]));add('remnant-threshold-below',refs([3324]));add('usable-zero',refs([2989]),settings(3000,5));
 {const s=settings();s.allowance=10;add('explicit-allowance',refs([890]),s);}
 for(const [name,lengths]of [['smallest-remnant-first',[900,590]],['unused-remnant',[500]]]){const s=settings();s.remnants=[{key:1,stockType:1,length:1000,headTrim:0,tailTrim:5},{key:2,stockType:1,length:600,headTrim:0,tailTrim:5}];s.nextRemnantKey=3;add(name,refs(lengths),s);}
 {const s=settings();s.stockTypes[0].name=' =HYPERLINK("x")\n木材';add('csv-formula-and-newline',refs([3626]),s);}
 {const r=refs([2560,2560,890,890,890,876]),s=settings();r.timbers.reverse();s.stockTypes.push({...s.stockTypes[0],key:2,section:[28,33]});s.nextStockKey=3;s.stockTypes.reverse();s.remnants=[{key:2,stockType:2,length:700,headTrim:0,tailTrim:0},{key:1,stockType:1,length:1000,headTrim:0,tailTrim:5}];s.nextRemnantKey=3;add('reversed-declarations-and-selection',r,s,request([{surface:1,ids:[6,4,2]},{surface:1,ids:[5,3,1]}]));}
 {const r=refs([100]);r.timbers[0].geometry.A=0;add('typed-row-not-ready',r);}
 for(const terminal of [true,false]){const r=refs([100]),s=settings();s.stockTypes[0].material=material;r.assembly={instances:[{value:{source:{id:4,bindingId:9,rule:{id:7,version:2,fingerprint:'b'.repeat(64)}}},members:[{memberId:12,timberId:1}]}],rules:[{value:{id:7,version:2,members:[{id:12,slotId:5}]},fingerprint:'b'.repeat(64)}],bindings:[{value:{id:9,slots:[{slotId:5,A:{kind:'material',id:material.id,version:1},B:{kind:'material',id:material.id,version:1}}]},complete:true,fingerprint:'c'.repeat(64),effective:[{slotId:5,A:{value:27,path:'不可解析的來源'},B:{value:33,path:'不可解析的來源'}}]}]};if(terminal)for(const field of ['A','B'])r.assembly.bindings[0].effective[0][field].terminal={kind:'material',...material};add(terminal?'owned-material-terminal':'owned-missing-terminal',r,s);}
 for(const [name,edit]of [
  ['kerf-zero',s=>s.kerf=0],['negative-allowance',s=>s.allowance=-1],['minimum-zero',s=>s.minRemnant=0],
  ['range-overflow',s=>s.stockTypes[0].length=100000001],['stock-zero-key',s=>s.stockTypes[0].key=0],
  ['stock-duplicate',s=>s.stockTypes.push({...s.stockTypes[0],key:2})],['material-zero-version',s=>s.stockTypes[0].material={...material,version:0}],
  ['remnant-unknown-stock',s=>s.remnants=[{key:1,stockType:9,length:100,headTrim:0,tailTrim:0}]],
  ['trim-no-usable',s=>s.stockTypes[0].endTrim=1818],['unknown-setting',s=>s.extra=true]]){const s=settings();edit(s);add('reject-'+name,refs([100]),s);}
 {const previous=settings();previous.remnants=[{key:1,stockType:1,length:600,headTrim:0,tailTrim:5}];previous.nextRemnantKey=2;const value=structuredClone(previous);value.stockTypes[0].section=[28,33];out.push({id:'transition-stock-in-use',action:'transition',previous,value});}
 {const previous=settings();previous.nextStockKey=3;out.push({id:'transition-highwater',action:'transition',previous,value:settings()});}
 return out;
}
function verifyCases(){return [
 {id:'duplicate-before-same-piece-invalid-geometry',planCase:'ffd-success',changes:[{path:['groups',0,'stocks',0,'pieces',1,'timberId'],value:1},{path:['groups',0,'stocks',0,'pieces',1,'end'],value:3459}]},
 {id:'earlier-piece-geometry-before-later-duplicate',planCase:'ffd-success',changes:[{path:['groups',0,'stocks',0,'pieces',0,'end'],value:2566},{path:['groups',0,'stocks',0,'pieces',1,'timberId'],value:1}]},
 {id:'earlier-group-loss-before-later-group-duplicate',planCase:'material-triplet-and-unordered-section',changes:[{path:['groups',0,'kerfLoss'],value:99},{path:['groups',1,'stocks',0,'pieces',0,'timberId'],value:2}]},
 {id:'later-group-duplicate-before-same-piece-geometry',planCase:'material-triplet-and-unordered-section',changes:[{path:['groups',1,'stocks',0,'pieces',0,'timberId'],value:2},{path:['groups',1,'stocks',0,'pieces',0,'end'],value:106}]},
];}
function applyChanges(plan,changes){for(const change of changes){const owner=change.path.slice(0,-1).reduce((v,k)=>v[k],plan);owner[change.path.at(-1)]=change.value;}return plan;}
module.exports={cases,verifyCases,applyChanges,material,refs,settings,request,source,timber};
