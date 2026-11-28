/* H research bridge: validated observations + explicit World context -> G input.
 * Not loaded by App. Success does not prove G feasibility or World legality. */
'use strict';
const R=require('./reconstruction-data.js'),W=require('../geometry-templates/woodworking/reconstruction-rc.js'),K=require('../geometry-core/reconstruction-values.js');
const copy=value=>JSON.parse(JSON.stringify(value));
const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===keys.length&&keys.every(key=>Object.hasOwn(value,key));
function need(ok,code){if(!ok)throw Object.assign(Error(code+'：研究轉接輸入不完整或不支援。'),{code});}
function toGInput(records,context){
  // canonical also rejects accessors, cycles, exotic objects and non-JSON data.
  R.canonical(records);R.canonical(context);
  need(Array.isArray(records)&&records.length<=64,'R13_G_LIMIT');
  need(exact(context,['outer','layout','params','ceiling_z']),'R13_G_CONTEXT');
  need(Array.isArray(context.outer)&&context.outer.length>=4&&context.outer.length<=512&&context.outer.every(p=>Array.isArray(p)&&p.length===2),'R13_G_OUTER');
  for(const p of context.outer)for(const n of p)K.integer(n);K.integer(context.ceiling_z);
  const l=context.layout,p=context.params;
  need(exact(l,['A','a_start','b_start'])&&['x','y'].includes(l.A)&&['min','max'].includes(l.a_start)&&['min','max'].includes(l.b_start),'R13_G_LAYOUT');
  need(exact(p,['P','L','gap','w','h','t','M','X','min_piece']),'R13_G_PARAMS');
  for(const [key,value] of Object.entries(p)){K.integer(value,!['gap','X'].includes(key));need(value>=0,'R13_G_PARAMS');}
  const ids=new Set(),obstacles=[],provenance=[];
  for(const record of records){
    R.validateRecord(record);need(!ids.has(record.id),'R13_G_DUPLICATE');ids.add(record.id);
    const values=R.rcValues(record);obstacles.push(W.obstacle(record.id,record.kind,record.axis,values));
    provenance.push({recordId:record.id,revision:record.revision,spaceId:record.spaceId,status:'research-candidate',worldIdentity:'unproven'});
  }
  return {input:{...copy(context),obstacles},provenance};
}
module.exports=Object.freeze({toGInput});
