'use strict';
// Node's test-runner events, not a search over rendered test names/stdout.
module.exports=async function* report(source){
  for await(const event of source){
    const d=event.data;
    if(['test:pass','test:fail'].includes(event.type)){
      const error=d.details?.error,cause=error?.cause||error;
      yield JSON.stringify({type:event.type,name:d.name,nesting:d.nesting,
        skip:!!d.skip,todo:!!d.todo,error:error?{name:cause.name,code:cause.code,
          failureType:error.failureType,message:cause.message}:null})+'\n';
    }else if(event.type==='test:summary'&&!d.file){
      yield JSON.stringify({type:event.type,data:d})+'\n';
    }
  }
};
