/* D46-D48 project declarations. No World references or inferred defaults. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.CuttingSettings=api;})(typeof globalThis!=='undefined'?globalThis:this,()=>{
 'use strict';
 const KIND='cutting-settings',SCHEMA='cutting-settings/1',CAPABILITY='cutting-plan/1',MAX_KEY=4294967295;
 const copy=v=>JSON.parse(JSON.stringify(v)),uint=n=>Number.isSafeInteger(n)&&n>=0&&n<=MAX_KEY,key=n=>uint(n)&&n>0;
 const integer=(n,min=0)=>Number.isSafeInteger(n)&&n>=min&&n<=100000000;
 function fail(code,detail){throw Object.assign(Error(`${code}：${detail}`),{code});}
 function keys(v,required){return v!==null&&typeof v==='object'&&!Array.isArray(v)&&Object.getOwnPropertySymbols(v).length===0&&Object.keys(v).length===required.length&&required.every(k=>Object.getOwnPropertyDescriptor(v,k)?.enumerable&&Object.hasOwn(Object.getOwnPropertyDescriptor(v,k),'value'));}
 const materialKey=m=>m===null?'unset':JSON.stringify([m.id,m.version,m.fingerprint]);
 const sectionKey=s=>[...s].sort((a,b)=>a-b).join('x');
 const stockIdentity=s=>sectionKey(s.section)+':'+materialKey(s.material);
 const nextAfter=k=>k===MAX_KEY?0:k+1;
 const maximumNext=(a,b)=>a===0||b===0?0:Math.max(a,b);
 function empty(){return {kerf:null,allowance:null,minRemnant:null,stockTypes:[],remnants:[],nextStockKey:1,nextRemnantKey:1};}
 function validate(v){
  if(!keys(v,['kerf','allowance','minRemnant','stockTypes','remnants','nextStockKey','nextRemnantKey'])||
    !['kerf','allowance','minRemnant'].every(k=>v[k]===null||integer(v[k],k==='allowance'?0:1))||!uint(v.nextStockKey)||!uint(v.nextRemnantKey))fail('SETTINGS_INVALID','裁切設定欄位或整數不合法。');
  if(!Array.isArray(v.stockTypes)||!Array.isArray(v.remnants)||v.stockTypes.length>32||v.remnants.length>128)fail('CAPACITY','原材至多 32 種、宣告餘料至多 128 段。');
  const stocks=new Map(),identities=new Set(),remnants=new Set();
  for(const s of v.stockTypes){
   if(!keys(s,['key','name','section','material','length','endTrim'])||!key(s.key)||typeof s.name!=='string'||!s.name.length||new TextEncoder().encode(s.name).length>96||
     !Array.isArray(s.section)||s.section.length!==2||!s.section.every(n=>integer(n,1))||!integer(s.length,1)||!integer(s.endTrim)||s.endTrim>=s.length/2)fail('STOCK_INVALID','原材欄位、名稱、截面或可用長度不合法。');
   if(s.material!==null&&(!keys(s.material,['id','version','fingerprint'])||typeof s.material.id!=='string'||!/^[A-Za-z0-9_-]{1,64}$/.test(s.material.id)||!key(s.material.version)||!/^[a-f0-9]{64}$/.test(s.material.fingerprint)))fail('MATERIAL_INVALID','材料鍵須為完整的固定版本與內容指紋。');
   if(stocks.has(s.key)||identities.has(stockIdentity(s)))fail('STOCK_DUPLICATE','原材 key 或截面與材料鍵重複。');
   stocks.set(s.key,s);identities.add(stockIdentity(s));
  }
  for(const r of v.remnants){
   if(!keys(r,['key','stockType','length','headTrim','tailTrim'])||!key(r.key)||!key(r.stockType)||!stocks.has(r.stockType)||!integer(r.length,1)||!integer(r.headTrim)||!integer(r.tailTrim)||r.length-r.headTrim-r.tailTrim<1||remnants.has(r.key))fail('REMNANT_INVALID','餘料 key、原材引用或可用長度不合法。');
   remnants.add(r.key);
  }
  if(v.nextStockKey!==0&&[...stocks.keys()].some(k=>k>=v.nextStockKey)||v.nextRemnantKey!==0&&[...remnants].some(k=>k>=v.nextRemnantKey))fail('KEY_HIGHWATER','高水位須在所有已用 key 之後。');
  return v;
 }
 function transition(previous,value){
  const old=previous||empty(),next=value||empty();validate(old);validate(next);
  for(const [list,counter]of [['stockTypes','nextStockKey'],['remnants','nextRemnantKey']]){
   if(maximumNext(old[counter],next[counter])!==next[counter])fail('KEY_HIGHWATER','key 高水位不可回退。');
   const prior=new Set(old[list].map(r=>r.key));for(const row of next[list])if(!prior.has(row.key)&&(old[counter]===0||row.key<old[counter]))fail('KEY_REUSE','已配置的 key 不得重用。');
  }
  for(const s of old.stockTypes){const n=next.stockTypes.find(n=>n.key===s.key);if(n&&old.remnants.some(r=>r.stockType===s.key)&&stockIdentity(s)!==stockIdentity(n))fail('STOCK_TYPE_IN_USE','被宣告餘料引用的截面與材料鍵不可修改。');}
  return value;
 }
 function add(v,list,counter,row){validate(v);if(v[counter]===0)fail('KEY_EXHAUSTED','key 已耗盡。');const n=copy(v);n[list].push({...copy(row),key:n[counter]});n[counter]=nextAfter(n[counter]);transition(v,n);return n;}
 const addStock=(v,row)=>add(v,'stockTypes','nextStockKey',row),addRemnant=(v,row)=>add(v,'remnants','nextRemnantKey',row);
 function preserveHighwater(value,observed){const n=copy(value||empty());for(const k of ['nextStockKey','nextRemnantKey'])n[k]=maximumNext(n[k],observed?.[k]??1);validate(n);return n;}
 const codepointOrder=(a,b)=>{const x=Array.from(a,c=>c.codePointAt(0)),y=Array.from(b,c=>c.codePointAt(0));for(let i=0;i<Math.min(x.length,y.length);i++)if(x[i]!==y[i])return x[i]-y[i];return x.length-y.length;};
 function canonical(value){validate(value);const n=copy(value);n.stockTypes.sort((a,b)=>a.key-b.key);n.remnants.sort((a,b)=>a.key-b.key);function emit(v){if(Array.isArray(v))return '['+v.map(emit).join(',')+']';if(v&&typeof v==='object')return '{'+Object.keys(v).sort(codepointOrder).map(k=>JSON.stringify(k)+':'+emit(v[k])).join(',')+'}';return JSON.stringify(v);}return emit(n);}
 async function fingerprint(value){const bytes=new TextEncoder().encode(canonical(value)),digest=await globalThis.crypto.subtle.digest('SHA-256',bytes);return Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');}
 return {KIND,SCHEMA,CAPABILITY,validate,transition,empty,materialKey,sectionKey,stockIdentity,addStock,addRemnant,preserveHighwater,canonical,fingerprint};
});
