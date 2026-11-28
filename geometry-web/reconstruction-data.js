/* D51a-c / I63a-c / R58a-b: bounded manual room and RC draft records.
 * RC confirmation is observation data, never a World object or an adoption. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('../geometry-core/reconstruction-values.js'):root.GeometryReconstructionValues);if(typeof module==='object'&&module.exports)module.exports=api;else root.GeometryReconstructionData=api;})(typeof globalThis!=='undefined'?globalThis:this,K=>{
  'use strict';
  if(!K)throw new Error('缺少精確數值模組。');
  const KIND='reconstruction-data',SCHEMA='reconstruction-data/1',CAPABILITY=SCHEMA;
  const REVIEW_SCHEMA='reconstruction-model-review/1';
  const FIELD_NAMES=Object.freeze(['bottom','top','height','wallThickness']);
  const RELATION_FIELDS=Object.freeze(['bottom','height','top']);
  const RC_CAPABILITY='reconstruction-rc-data/1';
  const KINDS=Object.freeze(['room-height','rc-column','rc-beam']);
  const RC_FIELDS=Object.freeze({'rc-column':Object.freeze(['x','y','width','depth','bottom','top','height']),
    'rc-beam':Object.freeze(['start','end','center','width','depth','bottom','top'])});
  const fieldsFor=record=>record.kind==='room-height'?FIELD_NAMES:RC_FIELDS[record.kind];
  const relationFor=record=>record.kind==='rc-beam'?['bottom','depth','top']:RELATION_FIELDS;
  const positiveField=key=>['height','wallThickness','width','depth'].includes(key);
  const positionField=key=>['bottom','top','x','y','start','end','center'].includes(key);
  const SETTINGS=Object.freeze({bottom:'bottom',height:'height',wallThickness:'wall_thickness'});
  const MAX_RECORDS=256,MAX_RECORD_BYTES=16*1024,MAX_REVIEWS=64,MAX_REVIEW_BYTES=64*1024,MAX_BYTES=1024*1024;
  const HASH=/^[a-f0-9]{64}$/;
  const encoder=new TextEncoder();
  const clone=value=>JSON.parse(JSON.stringify(value));
  function fail(code,message){throw Object.assign(new Error(code+'：'+message),{code});}
  const positiveInteger=value=>Number.isSafeInteger(value)&&value>=1;
  function plain(value){
    if(!value||typeof value!=='object'||Array.isArray(value))return false;
    const proto=Object.getPrototypeOf(value);
    return proto===null||Object.getPrototypeOf(proto)===null&&Object.hasOwn(proto,'constructor')&&
      typeof Object.getOwnPropertyDescriptor(proto,'constructor')?.value==='function'&&proto.constructor.name==='Object';
  }
  function exact(value,keys){
    return plain(value)&&Object.getOwnPropertySymbols(value).length===0&&Object.getOwnPropertyNames(value).length===keys.length&&
      keys.every(key=>{const d=Object.getOwnPropertyDescriptor(value,key);return !!d&&d.enumerable&&Object.hasOwn(d,'value');});
  }
  function array(value){
    return Array.isArray(value)&&Object.getOwnPropertySymbols(value).length===0&&
      Object.getOwnPropertyNames(value).length===value.length+1&&Array.from({length:value.length},(_,index)=>index).every(index=>{
        const d=Object.getOwnPropertyDescriptor(value,String(index));return !!d&&d.enumerable&&Object.hasOwn(d,'value');
      });
  }
  function scalarLength(value){
    if(typeof value!=='string')return -1;
    let count=0;
    for(const scalar of value){const point=scalar.codePointAt(0);if(point>=0xd800&&point<=0xdfff)return -1;count++;}
    return count;
  }
  function text(value,max){const n=scalarLength(value);return n>=0&&n<=max;}
  function jsonData(value,seen=new Set()){
    if(value===null||typeof value==='boolean')return;
    if(typeof value==='string'){if(scalarLength(value)<0)fail('R13_JSON','文字含無效 Unicode scalar。');return;}
    if(typeof value==='number'){if(!Number.isFinite(value))fail('R13_JSON','資料必須是有限 JSON。');return;}
    if(typeof value!=='object'||seen.has(value))fail('R13_JSON','資料必須是不含循環的純 JSON。');
    const sequence=Array.isArray(value);
    if(sequence?!array(value):!plain(value)||Object.getOwnPropertySymbols(value).length)
      fail('R13_JSON','資料不能含非 JSON 物件或額外的陣列欄位。');
    seen.add(value);
    for(const key of sequence?Object.keys(value):Object.getOwnPropertyNames(value)){
      const d=Object.getOwnPropertyDescriptor(value,key);
      if(!d?.enumerable||!Object.hasOwn(d,'value'))fail('R13_JSON','資料不能含 getter 或不可序列化欄位。');
      jsonData(d.value,seen);
    }
    seen.delete(value);
  }
  function jsonBytes(value){jsonData(value);return encoder.encode(JSON.stringify(value)).byteLength;}
  function canonical(value){
    jsonData(value);
    const encode=v=>v===null||typeof v!=='object'?JSON.stringify(v):Array.isArray(v)?'['+v.map(encode).join(',')+']':
      '{'+Object.keys(v).sort().map(key=>JSON.stringify(key)+':'+encode(v[key])).join(',')+'}';
    return encode(value);
  }
  const same=(left,right)=>canonical(left)===canonical(right);
  function capacity(value,max,code){if(jsonBytes(value)>max)fail(code,'資料超過保存容量；沒有截斷或捨棄內容。');}
  function identifier(id){
    if(typeof id!=='string'||!/^rd-[1-9][0-9]*$/.test(id))fail('R13_RECORD_ID','補資料紀錄識別不合法。');
    const value=Number(id.slice(3));if(!positiveInteger(value))fail('R13_RECORD_ID','補資料紀錄識別超出範圍。');return value;
  }
  function name(value){if(scalarLength(value)<0||encoder.encode(value).byteLength>96)fail('R13_NAME','名稱必須在 96 UTF-8 bytes 內。');}
  function fieldInput(field){return {raw:field.raw,unit:field.unit,basis:clone(field.basis),source:clone(field.source)};}
  function validateBasis(basis,key){
    if(!exact(basis,['kind','note'])||!text(basis.note,256))fail('R13_DATUM','基準說明格式不合法。');
    const choices=key==='x'?['unknown','world-x']:key==='y'?['unknown','world-y']:
      ['bottom','top'].includes(key)?['unknown','world-z']:['start','end','center'].includes(key)?['unknown','world-x','world-y']:['distance'];
    if(!choices.includes(basis.kind))fail('R13_DATUM','位置與距離使用不同基準；位置須明選相符的世界軸。');
  }
  function assertDatum(field,key,record=null){
    let expected=['bottom','top'].includes(key)?'world-z':['x','y'].includes(key)?'world-'+key:null;
    if(['start','end','center'].includes(key)){
      if(!['x','y'].includes(record?.axis))fail('R13_AXIS','樑的水平走向須明選 x 或 y。');
      expected='world-'+(key==='center'?(record.axis==='x'?'y':'x'):record.axis);
    }
    if(expected!==null&&field.basis.kind!==expected)
      fail('R13_DATUM_ADOPTION',`位置採用或推導須明選世界 ${expected.slice(-1).toUpperCase()}；觀察確認及說明文字不建立座標轉換。`);
  }
  function directValue(field,key){return K.decimal(field.raw,field.unit,positiveField(key));}
  function validateField(field,key,recordRevision,record){
    if(!exact(field,['raw','unit','basis','source','revision','confirmation'])||!text(field.raw,64)||![null,'mm','cm'].includes(field.unit)||
        !positiveInteger(field.revision)||field.revision>recordRevision||!exact(field.source,['kind'])||field.source.kind!=='manual')
      fail('R13_FIELD','欄位只能保存原字串、單位、明示基準、人工來源、修訂與確認。');
    validateBasis(field.basis,key);
    const c=field.confirmation;if(c===null)return;
    if(!plain(c)||!positiveInteger(c.revision)||c.revision!==field.revision)fail('R13_CONFIRMATION','確認不屬於目前欄位修訂。');
    if(c.kind==='direct'){
      if(!exact(c,['kind','value','revision','input'])||!exact(c.input,['raw','unit','basis','source'])||!same(c.input,fieldInput(field))||c.value!==directValue(field,key))
        fail('R13_DIRECT_CONFIRMATION','直接確認的原文、基準、來源、修訂或精確值不相符。');
    }else if(c.kind==='derived'){
      if(!exact(c,['kind','value','revision','relation','inputs'])||c.relation!=='sum/1'||!relationFor(record).includes(key)||field.raw!==''||
          !array(c.inputs)||c.inputs.length!==2||c.inputs.some(input=>!exact(input,['field','revision','value'])||!relationFor(record).includes(input.field)||!positiveInteger(input.revision)))
        fail('R13_DERIVED_CONFIRMATION','推導確認必須保留唯一空白目標及兩個直接確認的版本依據。');
      K.integer(c.value,positiveField(key));assertDatum(field,key,record);
    }else fail('R13_CONFIRMATION','不支援此確認種類。');
  }
  function candidate(record,target=null){
    const names=relationFor(record),blanks=names.filter(key=>record.fields[key].raw==='');
    if(blanks.length!==1||target!==null&&blanks[0]!==target)return null;
    const field=blanks[0],others=names.filter(key=>key!==field);
    if(others.some(key=>record.fields[key].confirmation?.kind!=='direct'))return null;
    const targetField=record.fields[field];assertDatum(targetField,field);
    for(const key of others)assertDatum(record.fields[key],key);
    if(targetField.unit===null)fail('R13_DERIVED_UNIT','推導目標仍須明選 mm 或 cm；精確結果以整數 mm 保存。');
    const inputs=others.map(key=>({field:key,revision:record.fields[key].revision,value:directValue(record.fields[key],key)}));
    const values=names.map(key=>key===field?null:directValue(record.fields[key],key)),result=K.solve(...values);
    if(!result||names[result.index]!==field)return null;
    K.integer(result.value,positiveField(field));
    return {field,value:result.value,inputs,relation:'sum/1'};
  }
  function validateRecord(record){
    jsonData(record);
    if(!plain(record)||!KINDS.includes(record.kind)||!exact(record,['id','kind','name','revision','fields',
        ...(record.kind!=='room-height'?['spaceId']:[]),...(record.kind==='rc-beam'?['axis']:[])])||
        !positiveInteger(record.revision)||!exact(record.fields,fieldsFor(record)))
      fail('R13_RECORD','只接受完整且封閉的房間高度／RC 待補紀錄。');
    if(record.kind!=='room-height'&&record.spaceId!==null&&(!Number.isInteger(record.spaceId)||record.spaceId<1||record.spaceId>4294967295))
      fail('R13_SPACE_INTENT','空間意圖只可未指定或明選正整數 D5 id；尚未驗其存在。');
    if(record.kind==='rc-beam'&&![null,'x','y'].includes(record.axis))fail('R13_AXIS','樑的水平走向只可未指定、x 或 y。');
    identifier(record.id);name(record.name);
    for(const key of fieldsFor(record))validateField(record.fields[key],key,record.revision,record);
    for(const key of relationFor(record)){
      const c=record.fields[key].confirmation;if(c?.kind!=='derived')continue;
      const expected=candidate(record,key);
      if(!expected||c.value!==expected.value||!same(c.inputs,expected.inputs))
        fail('R13_DERIVED_BASIS','推導確認的完整依據不符，不能憑 hash 或舊數值沿用。');
    }
    capacity(record,MAX_RECORD_BYTES,'R13_RECORD_CAPACITY');return record;
  }
  function relationCheck(record){
    const values=relationFor(record).map(key=>{
      const field=record.fields[key];
      if(field.raw!=='')return directValue(field,key);
      return field.confirmation?.kind==='derived'?field.confirmation.value:null;
    });
    // Parse every entered observation. Only comparable World Z coordinates may be subtracted.
    // A valid unknown-basis top remains explicit omitted evidence, never a guessed coordinate.
    if(values.every(value=>value!==null)&&['bottom','top'].every(key=>record.fields[key].basis.kind==='world-z'))K.solve(...values);
  }
  function planRecord(record){
    if(record.kind!=='room-height')fail('R13_ROOM_ONLY','RC 待補資料沒有正式採用或房間建模入口。');
    relationCheck(record);
    const uses=[];
    for(const key of ['bottom','height']){
      const field=record.fields[key];if(!field.confirmation)fail('R13_PLAN_CONFIRMATION','請先有效確認底標高與高度；不會代填舊的建模預設。');
      assertDatum(field,key);uses.push({field:key,revision:field.revision,value:field.confirmation.value});
    }
    let wallThickness=null;
    const wall=record.fields.wallThickness;
    if(wall.raw!==''||wall.confirmation!==null){
      if(wall.confirmation?.kind!=='direct')fail('R13_PLAN_CONFIRMATION','有輸入的牆厚須先有效確認，或明確清空。');
      wallThickness=wall.confirmation.value;uses.push({field:'wallThickness',revision:wall.revision,value:wallThickness});
    }
    const bottom=uses[0].value,height=uses[1].value;
    K.integer(bottom);K.integer(height,true);K.integer(bottom+height);
    const checks=[],omitted=[],top=record.fields.top;
    if(top.confirmation&&top.basis.kind==='world-z')checks.push({field:'top',revision:top.revision,value:top.confirmation.value});
    else omitted.push({field:'top',reason:top.raw===''?'missing-value':'needs-review',
      detail:top.raw===''?'empty':top.basis.kind!=='world-z'?'world-basis-unconfirmed':'unconfirmed'});
    if(wallThickness===null)omitted.push({field:'wallThickness',reason:'missing-value',detail:'empty'});
    return {bottom,height,wallThickness,recordId:record.id,revision:record.revision,fields:uses,checks,omitted,
      completeness:omitted.length?'defined-subset':'selected-scope-reviewed'};
  }
  function validateReview(review){
    jsonData(review);
    if(!exact(review,['schema','modelId','sourceSha256','inputSha256','resultSha256','completeness','scope'])||review.schema!==REVIEW_SCHEMA||
        typeof review.modelId!=='string'||!review.modelId||encoder.encode(review.modelId).byteLength>200||
        ![review.sourceSha256,review.inputSha256,review.resultSha256].every(value=>typeof value==='string'&&HASH.test(value))||
        !['defined-subset','selected-scope-reviewed'].includes(review.completeness)||!array(review.scope)||review.scope.length!==1)
      fail('R13_REVIEW','模型核對必須保存完整模型指紋與明選的唯一紀錄。');
    const scope=review.scope[0];
    if(!exact(scope,['recordId','revision','snapshot','uses','checks','omitted','missing','disposition'])||typeof scope.missing!=='boolean'||scope.disposition!=='adopted'||
        !array(scope.uses)||!array(scope.checks)||!array(scope.omitted)||scope.recordId!==scope.snapshot?.id||scope.revision!==scope.snapshot?.revision)
      fail('R13_REVIEW_SCOPE','核對範圍、歷史缺失標記或快照不合法。');
    validateRecord(scope.snapshot);
    const expected=planRecord(scope.snapshot);
    if(review.completeness!==expected.completeness||!same(scope.omitted,expected.omitted))
      fail('R13_REVIEW_COMPLETENESS','核對範圍與逐欄未納入原因必須由保存確認重算，不能把已定子集冒稱全部已核對。');
    if(scope.uses.length!==expected.fields.length)fail('R13_REVIEW_USE','供值欄位必須完整且恰好對應明選內容。');
    for(let index=0;index<scope.uses.length;index++){
      const use=scope.uses[index],wanted=expected.fields[index];
      if(!exact(use,['field','revision','value','setting','confirmationSha256'])||use.field!==wanted.field||use.revision!==wanted.revision||use.value!==wanted.value||
          use.setting!==SETTINGS[wanted.field]||typeof use.confirmationSha256!=='string'||!HASH.test(use.confirmationSha256))
        fail('R13_REVIEW_USE','模型供值用途、修訂或值與確認快照不一致。');
    }
    if(scope.checks.length!==expected.checks.length)fail('R13_REVIEW_CHECK','人工核對欄位不能遺漏或假造。');
    for(let index=0;index<scope.checks.length;index++){
      const check=scope.checks[index],wanted=expected.checks[index];
      if(!exact(check,['field','revision','value','purpose','confirmationSha256'])||check.field!==wanted.field||check.revision!==wanted.revision||check.value!==wanted.value||
          check.purpose!=='human-review'||typeof check.confirmationSha256!=='string'||!HASH.test(check.confirmationSha256))
        fail('R13_REVIEW_CHECK','頂高只供人工核對，不能假稱模型供值，並須保留精確值與確認版本。');
    }
    capacity(review,MAX_REVIEW_BYTES,'R13_REVIEW_CAPACITY');return review;
  }
  function validate(value){
    jsonData(value);
    if(!exact(value,['schema','nextId','nextRevision','records','reviews'])||value.schema!==SCHEMA||!positiveInteger(value.nextId)||!positiveInteger(value.nextRevision)||
        !array(value.records)||value.records.length>MAX_RECORDS||!array(value.reviews)||value.reviews.length>MAX_REVIEWS)
      fail('R13_SCHEMA','補資料附件的版本、封閉欄位或容量不合法。');
    const ids=new Set(),models=new Set();
    const water=record=>{
      if(identifier(record.id)>=value.nextId||record.revision>=value.nextRevision||fieldsFor(record).some(key=>record.fields[key].revision>=value.nextRevision))
        fail('R13_HIGHWATER','識別或修訂高水位低於已保存紀錄，不能重用歷史版本。');
    };
    for(const record of value.records){validateRecord(record);if(ids.has(record.id))fail('R13_DUPLICATE_RECORD','紀錄識別重複。');ids.add(record.id);water(record);}
    for(const review of value.reviews){validateReview(review);if(models.has(review.modelId))fail('R13_DUPLICATE_REVIEW','一個模型只能有一份核對。');models.add(review.modelId);water(review.scope[0].snapshot);}
    capacity(value,MAX_BYTES,'R13_CAPACITY');return value;
  }
  const empty=()=>({schema:SCHEMA,nextId:1,nextRevision:1,records:[],reviews:[]});
  function allocate(value,key){const current=value[key];if(!positiveInteger(current)||current>=Number.MAX_SAFE_INTEGER)fail('R13_EXHAUSTED','識別或修訂高水位已耗盡；沒有重用舊值。');value[key]=current+1;return current;}
  function find(value,id){const record=value.records.find(item=>item.id===id);if(!record)fail('R13_RECORD_MISSING','待補資料紀錄不存在，未改動。');return record;}
  function assertAction(action,required,optional=[]){
    if(!plain(action)||Object.keys(action).some(key=>![...required,...optional].includes(key))||required.some(key=>!Object.hasOwn(action,key)))
      fail('R13_ACTION','不支援此資料操作或欄位。');
    jsonData(action);
  }
  function edit(value,action){
    const before=value===null||value===undefined?empty():validate(value);jsonData(action);
    const next=clone(before);
    if(action?.type==='create'){
      assertAction(action,['type'],['name','kind']);const kind=action.kind===undefined?'room-height':action.kind;
      if(!KINDS.includes(kind))fail('R13_RECORD','不支援此待補資料模板。');
      const title=action.name===undefined?{'room-height':'房間高度','rc-column':'RC 柱','rc-beam':'RC 樑'}[kind]:action.name;name(title);
      if(next.records.length>=MAX_RECORDS)fail('R13_RECORD_CAPACITY','已達 256 筆；原資料保留。');
      const id='rd-'+allocate(next,'nextId'),revision=allocate(next,'nextRevision'),fields={};
      for(const key of fieldsFor({kind}))fields[key]={raw:'',unit:null,basis:{kind:positionField(key)?'unknown':'distance',note:''},source:{kind:'manual'},revision,confirmation:null};
      next.records.push({id,kind,name:title,revision,fields,...(kind!=='room-height'?{spaceId:null}:{}),...(kind==='rc-beam'?{axis:null}:{})});
    }else if(action?.type==='edit'){
      assertAction(action,['type','id'],['name','fields','spaceId','axis']);const record=find(next,action.id),affected=new Set();let inputChanged=false;
      if(Object.hasOwn(action,'name')){name(action.name);record.name=action.name;}
      if(Object.hasOwn(action,'spaceId')){
        if(record.kind==='room-height')fail('R13_ACTION','房間資料沒有 RC 的 D5 意圖欄位。');
        if(record.spaceId!==action.spaceId){record.spaceId=action.spaceId;inputChanged=true;}
      }
      if(Object.hasOwn(action,'axis')){
        if(record.kind!=='rc-beam')fail('R13_ACTION','只有樑有水平走向。');
        if(record.axis!==action.axis){record.axis=action.axis;inputChanged=true;for(const key of ['start','end','center'])affected.add(key);}
      }
      if(Object.hasOwn(action,'fields')){
        if(!plain(action.fields)||Object.keys(action.fields).some(key=>!fieldsFor(record).includes(key)))fail('R13_ACTION','未知的模板欄位。');
        for(const key of Object.keys(action.fields)){
          const patch=action.fields[key];
          if(!plain(patch)||Object.keys(patch).some(part=>!['raw','unit','basis'].includes(part)))fail('R13_ACTION','只能編輯原字串、單位與基準。');
          const field=record.fields[key],merged={...field,...clone(patch)};
          if(!same(fieldInput(field),fieldInput(merged))){record.fields[key]=merged;affected.add(key);}
        }
      }
      for(const key of fieldsFor(record)){const c=record.fields[key].confirmation;if(c?.kind==='derived'&&c.inputs.some(input=>affected.has(input.field)))affected.add(key);}
      if(affected.size||inputChanged){const revision=allocate(next,'nextRevision');record.revision=revision;for(const key of affected){record.fields[key].revision=revision;record.fields[key].confirmation=null;}}
    }else if(action?.type==='confirm'||action?.type==='confirm-derived'){
      assertAction(action,['type','id','field']);const record=find(next,action.id),key=action.field;
      if(!fieldsFor(record).includes(key))fail('R13_ACTION','未知的確認欄位。');
      const field=record.fields[key];
      if(action.type==='confirm'){
        const value=directValue(field,key);
        if(field.confirmation?.kind==='direct')return validate(next);
        const revision=allocate(next,'nextRevision');record.revision=revision;field.revision=revision;
        field.confirmation={kind:'direct',value,revision,input:fieldInput(field)};
      }else{
        if(field.confirmation?.kind==='derived')return validate(next);
        const derived=candidate(record,key);if(!derived||derived.field!==key)fail('R13_NO_UNIQUE_DERIVATION','須有兩筆目前有效的直接確認與唯一空白欄位，才能推導。');
        const revision=allocate(next,'nextRevision');record.revision=revision;field.revision=revision;
        field.confirmation={kind:'derived',value:derived.value,revision,relation:derived.relation,inputs:derived.inputs};
      }
      for(const other of fieldsFor(record)){
        const dependency=record.fields[other].confirmation;
        if(other!==key&&dependency?.kind==='derived'&&dependency.inputs.some(input=>input.field===key)){
          record.fields[other].revision=record.revision;record.fields[other].confirmation=null;
        }
      }
    }else if(action?.type==='delete'){
      assertAction(action,['type','id']);find(next,action.id);next.records=next.records.filter(record=>record.id!==action.id);
      for(const review of next.reviews)for(const scope of review.scope)if(scope.recordId===action.id)scope.missing=true;
    }else fail('R13_ACTION','未知的補資料操作。');
    return validate(next);
  }
  function derivation(record){
    validateRecord(record);
    const blanks=relationFor(record).filter(key=>record.fields[key].raw==='');
    if(blanks.length!==1||record.fields[blanks[0]].confirmation!==null)return null;
    return candidate(record);
  }
  function plan(value,id){validate(value);return planRecord(find(value,id));}
  function rcValues(record){
    validateRecord(record);
    if(!RC_FIELDS[record.kind])fail('R13_RC_ONLY','研究障礙只接明選 RC 柱或樑資料。');
    relationCheck(record);
    const values={};for(const key of fieldsFor(record)){
      const field=record.fields[key];if(!field.confirmation)fail('R13_RC_CONFIRMATION','RC 研究幾何須逐欄有效確認；不猜補缺值。');
      assertDatum(field,key,record);values[key]=K.integer(field.confirmation.value,positiveField(key));
    }
    if(record.kind==='rc-beam')K.integer(values.end-values.start,true);
    return values;
  }
  function preserveHighwater(value,observed){
    if(value===null||value===undefined){if(observed===null||observed===undefined)return null;value=empty();}
    validate(value);
    let water=observed;
    if(water!==null&&water!==undefined){
      if(exact(water,['nextId','nextRevision'])){if(!positiveInteger(water.nextId)||!positiveInteger(water.nextRevision))fail('R13_HIGHWATER','高水位不合法。');}
      else validate(water);
    }
    const next=clone(value);if(water){next.nextId=Math.max(next.nextId,water.nextId);next.nextRevision=Math.max(next.nextRevision,water.nextRevision);}
    return validate(next);
  }
  // The missing marker is mandatory from the first receipt. false uses more bytes than true.
  function missingReserve(value){validate(value);return 0;}
  async function digest(value){
    const bytes=encoder.encode(canonical(value));
    const crypto=globalThis.crypto;
    if(!crypto?.subtle)fail('R13_HASH_UNAVAILABLE','目前環境不能核對完整資料指紋。');
    return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),byte=>byte.toString(16).padStart(2,'0')).join('');
  }
  function modelInput(model){
    jsonData(model);
    if(!plain(model)||typeof model.id!=='string'||!model.id||encoder.encode(model.id).byteLength>200||!plain(model.source)||!plain(model.input)||
        model.input.mode!=='plan'||typeof model.input.base_scene!=='string'||!plain(model.input.settings)||!plain(model.result))
      fail('R13_MODEL','補資料核對只接完整的保存 plan 模型；產品模型另須通過既有驗證器。');
    return model;
  }
  const sourceBasis=model=>({source:model.source,baseScene:model.input.base_scene,sourceSnapshot:model.result.source_snapshot??null,sourceIdentity:model.sourceIdentity??null});
  function matchSupply(expected,model){
    const settings=model.input.settings;
    if(settings.bottom!==expected.bottom||settings.height!==expected.height||settings.wall_thickness!==expected.wallThickness)
      fail('R13_MODEL_SUPPLY','保存模型的底標高、高度或選用牆厚不等於明選確認值。');
  }
  async function makeReview(value,id,model){
    validate(value);modelInput(model);
    const frozen=clone(value),saved=clone(model),snapshot=clone(find(frozen,id)),expected=planRecord(snapshot);matchSupply(expected,saved);
    const uses=[];
    for(const field of expected.fields)uses.push({...field,setting:SETTINGS[field.field],confirmationSha256:await digest(snapshot.fields[field.field].confirmation)});
    const checks=[];
    for(const field of expected.checks)checks.push({...field,purpose:'human-review',confirmationSha256:await digest(snapshot.fields[field.field].confirmation)});
    const review={schema:REVIEW_SCHEMA,modelId:saved.id,sourceSha256:await digest(sourceBasis(saved)),inputSha256:await digest(saved.input),resultSha256:await digest(saved.result),
      completeness:expected.completeness,scope:[{recordId:snapshot.id,revision:snapshot.revision,snapshot,uses,checks,omitted:clone(expected.omitted),missing:false,disposition:'adopted'}]};
    return validateReview(review);
  }
  async function verifyReviews(value,models){
    validate(value);jsonData(models);
    if(!array(models)||models.length>64)fail('R13_MODELS','保存模型集合不合法。');
    const next=clone(value),saved=clone(models),byId=new Map();
    for(const model of saved){if(!plain(model)||typeof model.id!=='string'||byId.has(model.id))fail('R13_MODELS','保存模型識別缺失或重複。');byId.set(model.id,model);}
    for(const review of next.reviews){
      const model=byId.get(review.modelId);if(!model)fail('R13_REVIEW_MODEL_MISSING','核對指向的保存模型缺失，未載入專案。');modelInput(model);
      if(review.sourceSha256!==await digest(sourceBasis(model))||review.inputSha256!==await digest(model.input)||review.resultSha256!==await digest(model.result))
        fail('R13_REVIEW_MODEL_PIN','核對與保存模型的完整來源、輸入或結果不相符，未載入專案。');
      const scope=review.scope[0],expected=planRecord(scope.snapshot);matchSupply(expected,model);
      for(const use of scope.uses)if(use.confirmationSha256!==await digest(scope.snapshot.fields[use.field].confirmation))
        fail('R13_REVIEW_CONFIRMATION_PIN','確認內容指紋不相符，不能視為有效核對。');
      for(const check of scope.checks)if(check.confirmationSha256!==await digest(scope.snapshot.fields[check.field].confirmation))
        fail('R13_REVIEW_CONFIRMATION_PIN','人工核對確認內容指紋不相符，不能視為有效核對。');
      if(!next.records.some(record=>record.id===scope.recordId))scope.missing=true;
    }
    return validate(next);
  }
  function reviewStatus(value,review){
    validate(value);validateReview(review);
    const scope=review.scope[0],record=value.records.find(item=>item.id===scope.recordId);
    if(scope.missing||!record)return 'missing';
    return record.revision===scope.revision&&same(record.fields,scope.snapshot.fields)?'current':'stale';
  }
  function reconcileModels(value,oldModels,newModels,options={releaseModelIds:[]}){
    validate(value);jsonData(oldModels);jsonData(newModels);jsonData(options);
    if(!array(oldModels)||!array(newModels)||!exact(options,['releaseModelIds'])||!array(options.releaseModelIds)||
        options.releaseModelIds.some(id=>typeof id!=='string')||new Set(options.releaseModelIds).size!==options.releaseModelIds.length)
      fail('R13_MODEL_TRANSITION','模型更新及明選解除清單不合法。');
    const index=models=>{const result=new Map();for(const model of models){if(!plain(model)||typeof model.id!=='string'||result.has(model.id))fail('R13_MODELS','模型識別缺失或重複。');result.set(model.id,model);}return result;};
    const before=index(oldModels),after=index(newModels),release=new Set(options.releaseModelIds),next=clone(value);
    if([...release].some(id=>!next.reviews.some(review=>review.modelId===id)))fail('R13_REVIEW_RELEASE','明選解除的核對不存在。');
    next.reviews=next.reviews.filter(review=>{
      if(!before.has(review.modelId))fail('R13_REVIEW_MODEL_MISSING','原模型已缺失，不能在更新時默默清除核對。');
      if(!after.has(review.modelId))return false;
      if(release.has(review.modelId))return false;
      if(!same(before.get(review.modelId),after.get(review.modelId)))fail('R13_REVIEW_RELEASE_REQUIRED','模型已有補資料核對；請在這次修改中明選解除，或重新建立完整核對。');
      return true;
    });
    return validate(next);
  }
  return Object.freeze({KIND,SCHEMA,CAPABILITY,RC_CAPABILITY,KINDS,REVIEW_SCHEMA,FIELD_NAMES,RELATION_FIELDS,MAX_RECORDS,MAX_RECORD_BYTES,MAX_REVIEWS,MAX_REVIEW_BYTES,MAX_BYTES,
    empty,validate,validateRecord,edit,derivation,plan,rcValues,preserveHighwater,makeReview,verifyReviews,reviewStatus,reconcileModels,jsonBytes,canonical,missingReserve});
});
