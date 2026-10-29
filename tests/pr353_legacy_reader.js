'use strict';
/* Fixed real pre-PR353 archive reader. Never fall back to today's implementation.
 * The optional root supplies original files when this checkout is shallow/offline.
 * Every source is checked against the immutable Git blob before execution.
 */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {createHash}=require('node:crypto'),{execFileSync}=require('node:child_process');
const Module=require('node:module');
const LEGACY_COMMIT='405f8c5e1a637a16cbe47470faf5ae1fa02b8676';
const LEGACY_BLOBS=Object.freeze({
  "geometry-web/project-store.js": "961088f6fe27433f95f9e425d333a90352cd59dd",
  "geometry-web/feature-attachments.js": "7db220ab5cd528aaacef41747b8360452145131a",
  "geometry-web/scenario-catalog.js": "b0ef33f08ddc20bb33c5a0b278a1a395037a5724",
  "geometry-web/rule-case-data.js": "70851c203947c054ad10861a65f5ba07715da67c",
  "geometry-web/source-plane.js": "5f985604472f4dda5c0000318326b08dc33e44cd",
  "geometry-web/evidence-links.js": "c2ce6a6c6fdcab2ffbdd7aa495282f72fb28b728",
  "geometry-web/reference-display.js": "8210d4428e44a9b8edf0dd4c4073ba6667076f0e"
});
function readLegacySources() {
  const checkout=path.resolve(__dirname,'..'),provided=process.env.GEOMETRY_PR353_LEGACY_ROOT;
  const sources={};
  for(const [file,expected]of Object.entries(LEGACY_BLOBS)){
    let bytes;
    try { bytes=provided?fs.readFileSync(path.join(provided,file)):execFileSync('git',['show',LEGACY_COMMIT+':'+file],{cwd:checkout,maxBuffer:2*1024*1024,stdio:['ignore','pipe','pipe']}); }
    catch(error){throw Error('PR353 legacy reader precondition: exact '+LEGACY_COMMIT+' source unavailable: '+file+'. Supply GEOMETRY_PR353_LEGACY_ROOT or fetch the fixed commit. '+error.message);}
    const actual=createHash('sha1').update(Buffer.from('blob '+bytes.length+String.fromCharCode(0))).update(bytes).digest('hex');
    if(actual!==expected)throw Error('PR353 legacy reader precondition: Git blob mismatch for '+file+': '+actual+' != '+expected);
    sources[file]=bytes.toString('utf8');
  }
  return sources;
}
function loadLegacyReader(){
  const sources=readLegacySources(),cache=new Map();
  function load(file){
    if(cache.has(file))return cache.get(file).exports;
    if(!Object.hasOwn(sources,file))throw Error('PR353 legacy reader dependency outside fixed closure: '+file);
    const module={exports:{}};
    cache.set(file,module);
    const filename=path.resolve(__dirname,'..',file);
    const requireFixed=request=>{
      if(!request.startsWith('./'))throw Error('PR353 legacy reader unexpected dependency: '+request);
      return load(path.posix.normalize(path.posix.join(path.posix.dirname(file),request)));
    };
    vm.runInThisContext(Module.wrap(sources[file]),{filename:LEGACY_COMMIT+'/'+file})(module.exports,requireFixed,module,filename,path.dirname(filename));
    return module.exports;
  }
  return load('geometry-web/project-store.js');
}
function materializeLegacyReader(destination){
  const sources=readLegacySources(),target=path.resolve(destination),receipt=[];
  if(fs.existsSync(target)&&fs.readdirSync(target).length)throw Error('Legacy reader destination must be empty.');
  for(const [file,source]of Object.entries(sources)){
    const filename=path.join(target,file),bytes=Buffer.from(source,'utf8');
    fs.mkdirSync(path.dirname(filename),{recursive:true});fs.writeFileSync(filename,bytes,{flag:'wx'});
    receipt.push({file,gitBlob:LEGACY_BLOBS[file],bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
  }
  return {commit:LEGACY_COMMIT,root:target,files:receipt};
}
module.exports={LEGACY_COMMIT,LEGACY_BLOBS,readLegacySources,loadLegacyReader,loadLegacyProject:loadLegacyReader,materializeLegacyReader};
if(require.main===module){
  if(process.argv.length!==4||process.argv[2]!=='--materialize')throw Error('Usage: node tests/pr353_legacy_reader.js --materialize EMPTY_DIRECTORY');
  console.log(JSON.stringify(materializeLegacyReader(process.argv[3]),null,2));
}
