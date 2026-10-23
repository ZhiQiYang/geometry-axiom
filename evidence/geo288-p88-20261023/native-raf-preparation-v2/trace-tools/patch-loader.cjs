'use strict';
// 診斷專用：只在記憶體綁定已凍結候選。來源 repository 一字不改。
const fs=require('fs'),path=require('path'),crypto=require('crypto'),Module=require('module');
const manifestPath=process.env.P88_PATCH_MANIFEST,variant=process.env.P88_PROOF_VARIANT;
if(!manifestPath||!['fixed','withdrawn','restored'].includes(variant))throw Error('P88 patch loader requires explicit manifest/variant');
const manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
const repo=fs.realpathSync(process.env.P88_SOURCE_REPO||'');
if(fs.realpathSync(manifest.repo)!==repo)throw Error('P88 candidate repo binding mismatch');
const h=b=>crypto.createHash('sha256').update(b).digest('hex');
const targets=new Map(manifest.files.map(row=>[path.resolve(repo,row.source_relative),row]));
const loaded=[],original=Module._extensions['.js'];
Module._extensions['.js']=function(module,filename){
  const row=targets.get(path.resolve(filename));
  if(!row)return original(module,filename);
  const raw=fs.readFileSync(filename);
  if(h(raw)!==row.original_sha256)throw Error('P88 original source bytes changed: '+filename);
  const fixed=variant!=='withdrawn',body=fixed?raw:fs.readFileSync(row.withdrawn);
  if(h(body)!==(fixed?row.original_sha256:row.withdrawn_sha256))throw Error('P88 candidate bytes changed');
  loaded.push({source:filename,original_sha256:h(raw),executed_sha256:h(body),variant,
    memory_only:true,source_file_modified:false,candidate:fixed?null:row.withdrawn});
  module._compile(body.toString('utf8'),filename);
};
process.on('exit',()=>{
  const target=process.env.P88_PATCH_REPORT;
  if(target&&loaded.length){
    if(fs.existsSync(target))throw Error('P88 patch report must be fresh');
    fs.writeFileSync(target,JSON.stringify({schema:'geo288-p88-executed-memory-candidate/1',variant,
      source_repo:repo,source_files_modified:false,files:loaded},null,2)+'\n',{flag:'wx'});
  }
});
