/* I63a: exact scalar arithmetic; no template field names or geometry builders. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else Object.defineProperty(root,'GeometryReconstructionValues',{value:api});})(this,()=>{
  'use strict';
  const LIMIT=100000000;
  function fail(code,message){throw Object.assign(new Error(code+'：'+message),{code});}
  function integer(value,positive=false){
    if(!Number.isSafeInteger(value)||Math.abs(value)>LIMIT||(positive&&value<=0))
      fail('EXACT_DOMAIN','值必須是範圍內的整數 mm，正尺寸須大於零。');
    return value;
  }
  function decimal(raw,unit,positive=false){
    if(typeof raw!=='string'||!/^[-+]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)$/.test(raw))
      fail('EXACT_DECIMAL_LITERAL','請輸入完整十進位字串；不接受算式、指數、分數或千分位。');
    if(unit!=='mm'&&unit!=='cm')fail('EXACT_DECIMAL_UNIT','單位只能是 mm 或 cm。');
    const negative=raw.startsWith('-'),unsigned=/^[-+]/.test(raw)?raw.slice(1):raw;
    const parts=unsigned.split('.'),fraction=parts[1]||'',scale=10n**BigInt(fraction.length);
    const numerator=BigInt((parts[0]||'0')+fraction)*(negative?-1n:1n)*(unit==='cm'?10n:1n);
    if(numerator%scale!==0n)fail('EXACT_INTEGER_MM','換算結果不是整數 mm；不會四捨五入或截斷。');
    const value=numerator/scale;
    if(value < -BigInt(LIMIT)||value>BigInt(LIMIT)||(positive&&value<=0n))
      fail('EXACT_DOMAIN','換算結果超出整數 mm 範圍，或正尺寸不大於零。');
    return Number(value);
  }
  function solve(a,b,c){
    const values=[a,b,c],missing=[];
    values.forEach((value,index)=>{if(value===null)missing.push(index);else integer(value);});
    if(missing.length>1)return null;
    if(!missing.length){
      if(BigInt(a)+BigInt(b)!==BigInt(c))fail('SUM_CONFLICT','三個值不符合 a + b = c；保留原值，不選擇其中一個覆蓋。');
      return null;
    }
    const index=missing[0],value=index===0?BigInt(c)-BigInt(b):index===1?BigInt(c)-BigInt(a):BigInt(a)+BigInt(b);
    if(value < -BigInt(LIMIT)||value>BigInt(LIMIT))fail('EXACT_DOMAIN','唯一推導結果超出整數 mm 範圍。');
    return {index,value:Number(value)};
  }
  return Object.freeze({LIMIT,integer,decimal,solve});
});
