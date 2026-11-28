'use strict';
// Structured actual test failures: a marker in source/stack is not a kill.
module.exports=async function* (events){
 for await(const event of events){
  if(event.type==='test:fail'){
   const wrapped=event.data.details?.error,error=wrapped?.cause||wrapped;
   yield JSON.stringify({type:'failure',name:event.data.name,error:{name:error?.name,code:error?.code,message:error?.message}})+'\n';
  }else if(event.type==='test:pass')yield JSON.stringify({type:'pass',name:event.data.name})+'\n';
  else if(event.type==='test:summary')yield JSON.stringify({type:'summary',data:event.data})+'\n';
 }
};
