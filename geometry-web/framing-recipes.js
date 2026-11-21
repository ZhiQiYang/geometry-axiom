/* D/I/R<FT1>: project intent only. No generated geometry or search is stored here. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.GeometryFramingRecipes=api;})(typeof globalThis!=='undefined'?globalThis:this,()=>{
  'use strict';
  const KIND='framing-template-recipes',SCHEMA='framing-template-recipes/1',CAPABILITY=SCHEMA;
  const POLICY_FINGERPRINT='21d364e9cbc1d98bf7d3663d0878829c00adc17f43957127d6cea748b3cebd83';
  const TEMPLATE=Object.freeze({id:'flat-ceiling',version:1,policyFingerprint:POLICY_FINGERPRINT});
  const DEFAULTS=Object.freeze({panelWidth:915,panelLength:1830,gap:2,timberWidth:27,timberDepth:33,maxSecondarySpacing:367});
  const SLOTS=Object.freeze(['boundary','frame','material-semantics','panel-version','support-threshold']);
  const CORNERS=Object.freeze(['min-min','max-min','min-max','max-max']);
  const MAX_RECIPES=32;
  const clone=v=>JSON.parse(JSON.stringify(v));
  const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
  const ident=v=>typeof v==='string'&&/^[a-zA-Z0-9_-]{1,100}$/.test(v);
  const integer=(v,min=0,max=100000000)=>Number.isSafeInteger(v)&&v>=min&&v<=max;
  function fail(code,message){throw Object.assign(new Error(code+'：'+message),{code});}
  function exact(v,fields){return !!v&&typeof v==='object'&&!Array.isArray(v)&&Object.getOwnPropertySymbols(v).length===0&&Object.keys(v).length===fields.length&&fields.every(k=>{const d=Object.getOwnPropertyDescriptor(v,k);return d?.enumerable&&Object.hasOwn(d,'value');});}
  function availability(recipe){
    const t=recipe?.template;
    return {canGenerate:t?.id===TEMPLATE.id&&t?.version===TEMPLATE.version&&t?.policyFingerprint===POLICY_FINGERPRINT,
      reason:t?.id===TEMPLATE.id&&t?.version===TEMPLATE.version?'':'此不可變模板版本目前不可用；配方原樣保留，只能查看。'};
  }
  function validateRecipe(r){
    if(!exact(r,['id','name','template','defaults','preference','sourceSlots','sourceHints'])||!ident(r.id)||typeof r.name!=='string'||!r.name.trim()||r.name.length>160)
      fail('FT_RECIPE_FIELDS','配方只能保存名稱、固定版本、字面預設、偏好與來源槽／提示。');
    if(!exact(r.template,['id','version','policyFingerprint'])||!ident(r.template.id)||!integer(r.template.version,1,4294967295)||!hash(r.template.policyFingerprint))
      fail('FT_RECIPE_VERSION','模板版本或指紋不合法。');
    if(r.template.id===TEMPLATE.id&&r.template.version===TEMPLATE.version&&r.template.policyFingerprint!==POLICY_FINGERPRINT)
      fail('FT_RECIPE_POLICY','已知版本的規則指紋不符，未載入專案。');
    if(!exact(r.defaults,Object.keys(DEFAULTS))||Object.entries(r.defaults).some(([k,v])=>!integer(v,k==='gap'?0:1)))
      fail('FT_RECIPE_DEFAULTS','預設必須是合法整數 mm；長邊使用 length 欄位語意，不依尺寸大小換軸。');
    if(!exact(r.preference,['corner','lengthAlong'])||!CORNERS.includes(r.preference.corner)||!['u','v'].includes(r.preference.lengthAlong))
      fail('FT_RECIPE_PREFERENCE','起鋪角與板長軸向必須明示。');
    if(!Array.isArray(r.sourceSlots)||r.sourceSlots.length!==SLOTS.length||new Set(r.sourceSlots).size!==SLOTS.length||!SLOTS.every(s=>r.sourceSlots.includes(s)))
      fail('FT_RECIPE_SLOTS','來源槽必須完整且不重複。');
    if(!Array.isArray(r.sourceHints)||r.sourceHints.length>1||r.sourceHints.some(h=>!exact(h,['slot','kind','id','fingerprint'])||h.slot!=='boundary'||h.kind!=='boundary'||!integer(h.id,0,4294967295)||!hash(h.fingerprint)))
      fail('FT_RECIPE_HINT','提示只能保存來源內容線索，不能宣稱原生身分或自動重指。');
    return r;
  }
  function validate(value){
    if(!exact(value,['schema','recipes'])||value.schema!==SCHEMA||!Array.isArray(value.recipes)||value.recipes.length>MAX_RECIPES)
      fail('FT_RECIPE_SCHEMA','配方集合版本或容量不支援。');
    const ids=new Set();for(const recipe of value.recipes){validateRecipe(recipe);if(ids.has(recipe.id))fail('FT_RECIPE_DUPLICATE','配方 id 重複。');ids.add(recipe.id);}
    return value;
  }
  function assertGeneratable(recipe){validateRecipe(recipe);if(!availability(recipe).canGenerate)fail('FT_GENERATOR_UNAVAILABLE','此模板版本不可生成，不會自動換成另一版。');return recipe;}
  const empty=()=>({schema:SCHEMA,recipes:[]});
  function upsert(value,recipe){const current=value||empty();validate(current);assertGeneratable(recipe);const previous=current.recipes.find(r=>r.id===recipe.id);if(previous)assertGeneratable(previous);const next=clone(current),index=next.recipes.findIndex(r=>r.id===recipe.id);if(index<0)next.recipes.push(clone(recipe));else next.recipes[index]=clone(recipe);return validate(next);}
  function remove(value,id){validate(value);if(!value.recipes.some(r=>r.id===id))fail('FT_RECIPE_MISSING','配方不存在。');return validate({...clone(value),recipes:value.recipes.filter(r=>r.id!==id).map(clone)});}
  function create(id,name,defaults={...DEFAULTS},preference={corner:'min-min',lengthAlong:'v'}){return validateRecipe({id,name,template:{...TEMPLATE},defaults:clone(defaults),preference:clone(preference),sourceSlots:[...SLOTS],sourceHints:[]});}
  return Object.freeze({KIND,SCHEMA,CAPABILITY,POLICY_FINGERPRINT,TEMPLATE,DEFAULTS,SLOTS,CORNERS,MAX_RECIPES,validate,validateRecipe,availability,assertGeneratable,empty,upsert,remove,create});
});
