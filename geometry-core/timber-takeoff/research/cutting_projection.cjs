'use strict';
// Offline U476 comparison only. These numeric row IDs are itemKey projections,
// never native timber IDs and never an invocation of cutting-plan/1 or /2.
const Woodworking = require('../../../geometry-templates/woodworking/cutting.js');

function project(result, settings) {
  const out = {studySchema:'U476-cutting-projection/1', researchOnly:true,
    formalCapability:false, status:result.status, itemKeys:[], newStockCount:null, plan:null};
  if (!['COMPLETE','EMPTY'].includes(result.status)) return out;
  if (result.status === 'EMPTY') return {...out, newStockCount:0};
  const rows = result.items.map(item => {
    const material = item.material;
    if (!material || !material.A || !material.B) throw Error('U476_PROJECTION_TYPED_TERMINALS_REQUIRED');
    return {id:item.itemKey, surface:item.provenance[0].placement.id, A:item.A, B:item.B, L:item.L,
      sources:['A','B'].map(field => ({target:{kind:'timber',id:item.itemKey,field}, terminal:material[field]}))};
  });
  const plan = Woodworking.evaluateRows(rows, settings, {status:'COMPLETE',diagnostics:[],groups:[]});
  if (plan.status !== 'COMPLETE') return {...out,status:plan.status};
  Woodworking.verify(plan, rows.map(row => row.id));
  return {...out, itemKeys:rows.map(row=>row.id), newStockCount:plan.groups.reduce((n,g)=>n+g.newStockCount,0), plan};
}

module.exports = {project};
