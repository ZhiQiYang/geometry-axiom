 'use strict';
// Diagnostic entry selection only; never used for a formal canvas/grid receipt.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),Module=require('module');
const repo=fs.realpathSync(process.env.P88_SOURCE_REPO),reportPath=process.env.P88_ONLY_REPORT;
if(!reportPath||!path.isAbsolute(reportPath))throw Error('P88-only diagnostic report must be explicit');
const names=['grid_system_test.js','grid_rule_editor_test.js'];
const targets=new Set(names.map(name=>path.join(repo,'geometry-web',name)));
const rows=[],original=Module._extensions['.js'];
Module._extensions['.js']=function(module,filename){
  original.call(this,module,filename);
  if(!targets.has(path.resolve(filename)))return;
  const raw=fs.readFileSync(filename);
  module.exports=async function omittedDiagnosticModule(){
    const row={source:filename,sha256:crypto.createHash('sha256').update(raw).digest('hex'),
      reason:'Explicit P88-only diagnostic selection; this is not a formal grid or canvas gate.'};
    rows.push(row);console.log('P88_DIAGNOSTIC_OMITTED '+JSON.stringify(row));
  };
};
process.on('exit',()=>{if(rows.length)fs.writeFileSync(reportPath,JSON.stringify({schema:'geo288-p88-only-diagnostic-selection/1',
  diagnostic_only:true,source_repo:repo,omitted:rows,p88_module:'geometry-web/grid_rule_lines_test.js',
  p88_module_bytes_changed_by_scope_selection:false},null,2)+'\n',{flag:'wx'});});
