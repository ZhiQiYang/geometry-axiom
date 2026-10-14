const fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),cp=require('node:child_process'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const repo='/tmp/geometry-p095-201',file=repo+'/tests/test_reference_workspace_races.js',root='/tmp/geometry-wake25-201';
const before=cp.execFileSync('git',['show','a09a90cbd13a13cf223ad4cdb0a1be76253e94e6:tests/test_reference_workspace_races.js'],{cwd:repo,encoding:'utf8'}),after=fs.readFileSync(file,'utf8');
function registrations(source){
 const rows=[],load=Module._load;
 const test=(name,options,fn)=>{if(typeof options==='function'){fn=options;options={};}rows.push({name,options:options||{},body_sha256:crypto.createHash('sha256').update(fn.toString()).digest('hex')});};
 Module._load=function(id,...args){if(id==='node:test')return {test,before(){}};return load.call(this,id,...args);};
 try{const m=new Module(file,module);m.filename=file;m.paths=Module._nodeModulePaths(path.dirname(file));m._compile(source,file);}finally{Module._load=load;}
 return rows;
}
const old=registrations(before),now=registrations(after);assert.equal(old.length,now.length);const changed=[];
for(let i=0;i<old.length;i++){
 assert.equal(old[i].name,now[i].name);assert.equal(old[i].body_sha256,now[i].body_sha256,'all original callback bytes must stay exact');
 if(JSON.stringify(old[i].options)!==JSON.stringify(now[i].options))changed.push({name:now[i].name,before:old[i].options,after:now[i].options});
}
assert.equal(changed.length,4);assert.deepEqual(changed.map(r=>r.after.timeout),[15000,22000,31000,21000]);
const receipt={prior_head:'a09a90cbd13a13cf223ad4cdb0a1be76253e94e6',local_case_count:now.length,all_names_order_and_callback_bytes_identical:true,changed,source_sha256:crypto.createHash('sha256').update(after).digest('hex'),case_bodies_executed:false};
fs.writeFileSync(root+'/registration-proof.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
