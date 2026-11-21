'use strict';
/* R386: per-section contracts. The inherited stateful sequence is deliberately
 * opaque: its only proven cut is P88 -> P72. Costs never license reordering. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const nodeModule=require('node:module');
const floor=require('./cdp_floor.js');
const ROOT=path.resolve(__dirname,'..');
const PLAN='geometry-web/canvas_shards.json',GOLDEN='geometry-web/cdp_sections.golden.json';
const DIRECTORY='geometry-web/cdp_sections.d',MODULES='geometry-web/canvas_sections';
const META='geometry-web/canvas-registry/legacy.json';
const ARCHIVE_PLAN='geometry-web/canvas-registry/legacy.canvas_shards.json';
const ARCHIVE_GOLDEN='geometry-web/canvas-registry/legacy.cdp_sections.golden.json';
const UNIT_DIRECTORY='geometry-web/canvas-registry/units';
const SLOT_DIRECTORY='geometry-web/canvas-registry/slots';
const SCHEMA='geometry-canvas-section/1';
const clone=value=>structuredClone(value);
const encode=value=>JSON.stringify(value,null,2)+'\n';
const sha=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const lf=raw=>Buffer.from(raw.toString('utf8').replace(/\r\n/g,'\n'));
const stable=value=>Array.isArray(value)?'['+value.map(stable).join(',')+']':value&&typeof value==='object'?
  '{'+Object.keys(value).sort().map(key=>JSON.stringify(key)+':'+stable(value[key])).join(',')+'}':JSON.stringify(value);
const same=(left,right)=>stable(left)===stable(right);
let acorn=null;const dependencyCache=new Map();
function requireThat(ok,code,detail=''){
  if(!ok){const error=Error(code+(detail?': '+detail:''));error.code=code;throw error;}
}
function exactKeys(value,keys,code){requireThat(value&&typeof value==='object'&&!Array.isArray(value)&&same(Object.keys(value).sort(),[...keys].sort()),code);}
function sourceClosure(root,seeds,{strict=false}={}){
  if(!acorn){const native=process.binding('natives')['internal/deps/acorn/acorn/dist/acorn'];
    requireThat(typeof native==='string','R386_CANVAS_SOURCE_PARSER');acorn={};require('node:vm').runInNewContext(native,{exports:acorn,module:{exports:acorn}});}
  const hashes={},pending=[...seeds],builtins=new Set(nodeModule.builtinModules.map(name=>name.replace(/^node:/,'')));
  const pureBuiltins=new Set(['assert','assert/strict','buffer','crypto','os','path','path/posix','path/win32','url','util','util/types']);
  while(pending.length){
    const relative=pending.pop();if(Object.hasOwn(hashes,relative))continue;
    const file=relativeFile(root,relative,'R386_CANVAS_DEPENDENCY_SOURCE'),raw=lf(fs.readFileSync(file));hashes[relative]=sha(raw);
    if(!/\.(?:js|cjs|mjs)$/.test(relative))continue;
    const cacheKey=hashes[relative]+':'+strict;let dependencies=dependencyCache.get(cacheKey);
    if(!dependencies){
      const tree=acorn.parse(raw.toString('utf8'),{ecmaVersion:'latest',sourceType:relative.endsWith('.mjs')?'module':'script',allowReturnOutsideFunction:true});
      dependencies=[];
      const literal=node=>node?.type==='Literal'&&typeof node.value==='string'?node.value:null;
      const walk=(node,parent)=>{
        if(!node||typeof node!=='object')return;
        if(strict&&node.type==='Identifier'){
          requireThat(!['process','global','globalThis','eval','Function','AsyncFunction','GeneratorFunction','Reflect','Proxy','WebAssembly'].includes(node.name),
            'R386_CANVAS_REFLECTIVE_MODULE_LOADER',relative+' '+node.name);
          if(node.name==='module')requireThat(parent?.type==='MemberExpression'&&parent.object===node&&!parent.computed&&parent.property.name==='exports',
            'R386_CANVAS_INDIRECT_MODULE_DEPENDENCY',relative);
        }
        if(strict&&node.type==='MemberExpression'){
          const property=node.computed?literal(node.property):node.property?.name;
          requireThat(!node.computed||node.property.type==='Literal'&&(typeof node.property.value==='number'||typeof node.property.value==='string'),
            'R386_CANVAS_DYNAMIC_MODULE_PROPERTY',relative);
          requireThat(!['require','constructor','__proto__','getPrototypeOf','setPrototypeOf','__lookupGetter__','__lookupSetter__','__defineGetter__','__defineSetter__'].includes(property),
            'R386_CANVAS_REFLECTIVE_MODULE_LOADER',relative+' '+property);
        }
        if(node.type==='CallExpression'&&node.callee?.type==='Identifier'&&node.callee.name==='require'){
          const name=node.arguments.length===1?literal(node.arguments[0]):null;
          if(name!==null)dependencies.push(name);else requireThat(!strict,'R386_CANVAS_DYNAMIC_MODULE_DEPENDENCY',relative);
        }
        if(node.type==='Identifier'&&node.name==='require'&&strict)
          requireThat(parent?.type==='CallExpression'&&parent.callee===node,'R386_CANVAS_INDIRECT_MODULE_DEPENDENCY',relative);
        if(node.type==='ImportExpression'){
          const name=literal(node.source);if(name!==null)dependencies.push(name);else requireThat(!strict,'R386_CANVAS_DYNAMIC_MODULE_DEPENDENCY',relative);
        }
        if(['ImportDeclaration','ExportNamedDeclaration','ExportAllDeclaration'].includes(node.type)&&node.source){
          const name=literal(node.source);requireThat(name!==null,'R386_CANVAS_MODULE_IMPORT',relative);dependencies.push(name);
        }
        for(const value of Object.values(node))if(Array.isArray(value)){for(const item of value)if(item&&typeof item==='object')walk(item,node);}
          else if(value&&typeof value==='object')walk(value,node);
      };
      walk(tree,null);dependencies=[...new Set(dependencies)].sort();dependencyCache.set(cacheKey,dependencies);
    }
    for(const name of dependencies){
      if(!name.startsWith('.')){requireThat(!strict||builtins.has(name.replace(/^node:/,''))&&pureBuiltins.has(name.replace(/^node:/,'')),
        'R386_CANVAS_UNPINNED_PACKAGE',name);continue;}
      let target;try{target=nodeModule.createRequire(file).resolve(name);}catch{requireThat(false,'R386_CANVAS_DEPENDENCY_MISSING',relative+' '+name);}
      const rel=path.relative(path.resolve(root),target).split(path.sep).join('/');
      requireThat(!rel.startsWith('../')&&!path.isAbsolute(rel)&&/\.(?:js|cjs|mjs|json)$/.test(rel),'R386_CANVAS_DEPENDENCY_OUTSIDE_ROOT',name);pending.push(rel);
    }
  }
  return {files:Object.fromEntries(Object.entries(hashes).sort()),sha256:sha(stable(hashes))};
}
function moduleSourceHash(root,module){return sourceClosure(root,[module],{strict:true}).sha256;}
function relativeFile(root,relative,code='R386_CANVAS_FILE'){
  requireThat(typeof relative==='string'&&relative!==''&&!relative.includes('\\')&&!path.isAbsolute(relative)&&
    path.posix.normalize(relative)===relative&&!relative.startsWith('../'),code,relative);
  const resolved=path.resolve(root);requireThat(fs.existsSync(resolved)&&fs.realpathSync(resolved)===resolved,'R386_CANVAS_SYMLINK_PARENT',root);
  let target=resolved;const parts=relative.split('/');
  for(let index=0;index<parts.length;index++){
    target=path.join(target,parts[index]);
    requireThat(fs.existsSync(target)&&!fs.lstatSync(target).isSymbolicLink(),code,relative);
    requireThat(index===parts.length-1?fs.lstatSync(target).isFile():fs.lstatSync(target).isDirectory(),code,relative);
  }
  return target;
}
/* JSON.parse alone silently accepts duplicate keys. The small lexical parser
 * retains JSON's grammar and rejects duplicates before schema validation. */
function parseJson(raw,label='JSON'){
  const text=String(raw);let at=0;
  const fail=()=>{throw Error('R386_CANVAS_JSON: '+label+' at '+at);};
  const whitespace=()=>{while(/[\x20\t\r\n]/.test(text[at]||'x'))at++;};
  const string=()=>{
    const start=at++;while(at<text.length){const c=text[at++];if(c==='"')return JSON.parse(text.slice(start,at));if(c==='\\')at++;}
    fail();
  };
  const value=()=>{
    whitespace();const c=text[at];
    if(c==='"')return string();
    if(c==='{'||c==='['){
      const object=c==='{',result=object?{}:[],keys=new Set(),end=object?'}':']';at++;whitespace();
      if(text[at]===end){at++;return result;}
      for(;;){
        whitespace();let key;
        if(object){if(text[at]!=='"')fail();key=string();requireThat(!keys.has(key),'R386_CANVAS_DUPLICATE_JSON_KEY',label+' '+key);keys.add(key);whitespace();if(text[at++]!==':')fail();}
        const item=value();if(object)Object.defineProperty(result,key,{value:item,enumerable:true,writable:true,configurable:true});else result.push(item);
        whitespace();if(text[at]===end){at++;return result;}if(text[at++]!==',')fail();
      }
    }
    const match=text.slice(at).match(/^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/);
    if(!match)fail();at+=match[0].length;return JSON.parse(match[0]);
  };
  let result;try{result=value();whitespace();if(at!==text.length)fail();}
  catch(error){if(error.code||String(error.message).startsWith('R386_'))throw error;fail();}
  return result;
}
const readJson=(root,relative)=>{
  const raw=fs.readFileSync(relativeFile(root,relative));
  requireThat(!raw.includes(13)&&raw.at(-1)===10,'R386_CANVAS_FRAGMENT_LF',relative);return parseJson(raw,relative);
};
function filesAt(root,relative,suffix){
  const directory=path.join(root,relative);if(!fs.existsSync(directory))return [];
  requireThat(fs.lstatSync(directory).isDirectory()&&!fs.lstatSync(directory).isSymbolicLink(),'R386_CANVAS_DIRECTORY',relative);
  return fs.readdirSync(directory).sort().map(name=>{
    const file=relative+'/'+name;
    requireThat(name.endsWith(suffix),'R386_CANVAS_DIRECTORY_ENTRY',file);relativeFile(root,file);return file;
  });
}
function legacyInputs(plan,golden){
  requireThat(floor.validateGolden(golden).length===0&&Object.values(golden.sections).every(Number.isInteger),
    'R386_CANVAS_GOLDEN_EXACT');
  requireThat(golden.total===Object.values(golden.sections).reduce((sum,count)=>sum+count,0),'R386_CANVAS_GOLDEN_TOTAL');
  requireThat(plan.schema==='geometry-cdp-shards/1'&&plan.shards?.length===2&&plan.boundaries?.length===1,'R386_CANVAS_TWO_UNITS');
  const all=[];
  for(let index=0;index<2;index++){
    const row=plan.shards[index];requireThat(row.index===index+1&&Array.isArray(row.sections)&&row.sections.length,'R386_CANVAS_OWNER');
    all.push(...row.sections);
  }
  requireThat(new Set(all).size===all.length&&same([...all].sort(),Object.keys(golden.sections).sort()),'R386_CANVAS_COMPLETE_UNION');
  requireThat(plan.shards[0].sections.at(-1)==='P88'&&plan.shards[1].sections[0]==='P72'&&
    plan.boundaries[0].after==='P88'&&plan.boundaries[0].before==='P72','R386_CANVAS_HANDOFF');
  requireThat(plan.shards[1].sections.at(-1)==='P359'&&plan.shards[1].sections.includes('P353'),'R386_CANVAS_TERMINAL_SLOT');
  for(const id of all)requireThat(/^(?:Setup|[0-9]+|BF[0-9]+|R06I?|P[0-9]+[A-Z]?)$/.test(id)&&floor.sectionOf('=== '+id+'.')===id,'R386_CANVAS_SECTION_ID',id);
  return all;
}
function archive(root){
  const meta=readJson(root,META);
  exactKeys(meta,['schema','baseSha','files','policy'],'R386_CANVAS_LEGACY_KEYS');
  requireThat(meta.schema==='geometry-canvas-registry-legacy/1'&&/^[0-9a-f]{40}$/.test(meta.baseSha),'R386_CANVAS_LEGACY_SCHEMA');
  requireThat(same(meta.files.map(row=>row.path),[ARCHIVE_PLAN,ARCHIVE_GOLDEN]),'R386_CANVAS_ARCHIVE_SET');
  const raw=meta.files.map(row=>{
    exactKeys(row,['path','bytes','sha256'],'R386_CANVAS_ARCHIVE_KEYS');
    const bytes=fs.readFileSync(relativeFile(root,row.path));
    requireThat(bytes.length===row.bytes&&sha(bytes)===row.sha256,'R386_CANVAS_ARCHIVE_PIN',row.path);return bytes;
  });
  const plan=parseJson(raw[0],ARCHIVE_PLAN),golden=parseJson(raw[1],ARCHIVE_GOLDEN);
  const ids=legacyInputs(plan,golden);
  return {meta,plan,golden,ids};
}
function migrate(root=ROOT,{baseSha,outdir}={}){
  requireThat(/^[0-9a-f]{40}$/.test(baseSha||''),'R386_CANVAS_BASE_SHA');
  requireThat(typeof outdir==='string'&&outdir,'R386_CANVAS_OUTPUT_REQUIRED');
  const writes=new Map();
  if(fs.existsSync(path.join(root,META))){
    const current=load(root);
    for(const relative of current.sourceFiles.filter(file=>file.startsWith(DIRECTORY+'/')||file.startsWith('geometry-web/canvas-registry/')))
      writes.set(relative,fs.readFileSync(path.join(root,relative)));
  }else{
    const planRaw=fs.readFileSync(relativeFile(root,PLAN)),goldenRaw=fs.readFileSync(relativeFile(root,GOLDEN));
    const plan=parseJson(planRaw,PLAN),golden=parseJson(goldenRaw,GOLDEN);legacyInputs(plan,golden);
    writes.set(ARCHIVE_PLAN,planRaw);writes.set(ARCHIVE_GOLDEN,goldenRaw);
    const pins=[{path:ARCHIVE_PLAN,bytes:planRaw.length,sha256:sha(planRaw)},{path:ARCHIVE_GOLDEN,bytes:goldenRaw.length,sha256:sha(goldenRaw)}];
    writes.set(META,Buffer.from(encode({schema:'geometry-canvas-registry-legacy/1',baseSha,files:pins,
      policy:'Preserve the two proven stateful units and their sole P88/P72 handoff. Unknown legacy section costs are null, never estimates.'})));
    for(const unit of plan.shards)for(const [index,id] of unit.sections.entries()){
      writes.set(DIRECTORY+'/'+id+'.json',Buffer.from(encode({schema:SCHEMA,id,assertions:golden.sections[id],unit:unit.index,
        order:{legacy:index},execution:{kind:'legacy'},provenance:{kind:'migration',baseSha,
          planSha256:sha(planRaw),goldenSha256:sha(goldenRaw)},cost:null})));
    }
  }
  const files=[...writes.keys()].sort();
  for(const relative of files){const target=path.join(outdir,relative);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,writes.get(relative));}
  return {schema:'geometry-canvas-registry-migration/1',files,deletes:[PLAN,GOLDEN],
    hashes:Object.fromEntries(files.map(relative=>[relative,sha(writes.get(relative))]))};
}
function extensionOrder(rows){
  const ids=new Set(rows.map(row=>row.id)),edges=new Map(rows.map(row=>[row.id,new Set()])),indegree=new Map(rows.map(row=>[row.id,0]));
  const edge=(from,to)=>{if(!edges.get(from).has(to)){edges.get(from).add(to);indegree.set(to,indegree.get(to)+1);}};
  for(const row of rows){
    const order=row.order;
    exactKeys(order,['after','before'],'R386_CANVAS_MODULE_ORDER_KEYS');
    requireThat(order&&Array.isArray(order.after)&&Array.isArray(order.before),
      'R386_CANVAS_MODULE_SLOT',row.id);
    requireThat(new Set(order.after).size===order.after.length&&new Set(order.before).size===order.before.length,'R386_CANVAS_DEPENDENCY_DUPLICATE',row.id);
    for(const from of order.after){requireThat(ids.has(from),'R386_CANVAS_DEPENDENCY_MISSING',from);edge(from,row.id);}
    for(const to of order.before){requireThat(ids.has(to),'R386_CANVAS_DEPENDENCY_MISSING',to);edge(row.id,to);}
  }
  const order=[];
  while(order.length<rows.length){const ready=[...ids].filter(id=>!order.includes(id)&&indegree.get(id)===0).sort();
    requireThat(ready.length,'R386_CANVAS_DEPENDENCY_CYCLE');const id=ready[0];order.push(id);for(const to of edges.get(id))indegree.set(to,indegree.get(to)-1);}
  return order.map(id=>rows.find(row=>row.id===id));
}
function verifyMeasurement(manifest,stdout,stderr,row,moduleHash){
  requireThat(manifest.schema==='geometry-canvas-section-measurement/1'&&manifest.capture_verified===true&&manifest.acceptance===false,
    'R386_CANVAS_COST_CAPTURE');
  requireThat(/^[0-9a-f]{40}$/.test(manifest.execution_sha||'')&&/^[0-9a-f]{40}$/.test(manifest.head_sha||'')&&
    /^[0-9a-f]{40}$/.test(manifest.tree||'')&&/^\d+$/.test(manifest.run_id||'')&&/^\d+$/.test(manifest.run_attempt||''),
    'R386_CANVAS_COST_CI_IDENTITY');
  requireThat(manifest.process_exit===0&&manifest.module===row.execution.module&&manifest.module_sha256===moduleHash,
    'R386_CANVAS_COST_SOURCE');
  requireThat(same(manifest.command,['node','geometry-web/cdp_test.js'])&&manifest.runtime_fresh===true,
    'R386_CANVAS_COST_COMMAND');
  requireThat(manifest.files?.['stdout.log']===sha(stdout)&&manifest.files?.['stderr.log']===sha(stderr),'R386_CANVAS_COST_RAW_HASH');
  const results=stdout.toString('utf8').split(/\r?\n/).filter(line=>line.startsWith('CDP_RESULT '));
  requireThat(results.length===1,'R386_CANVAS_COST_RESULT_COUNT');
  const result=parseJson(results[0].slice('CDP_RESULT '.length),'CDP_RESULT');
  requireThat(result.schema==='geometry-cdp-result/1'&&result.completed===true&&result.failedAssertions===0&&
    same(result.skipped,[])&&!result.sectionsFailed&&result.unexpectedBrowserExceptions===0&&
    result.scope?.mode==='partial'&&result.scope.module===row.id&&
    same(result.scope.filters,['GEOMETRY_CANVAS_MODULE_ONLY'])&&same(result.scope.modifiers,[])&&
    result.goldenCompare==='not compared (partial mode)','R386_CANVAS_COST_PARTIAL_RESULT');
  requireThat(same(result.sectionOrder,[row.id])&&same(Object.keys(result.sections||{}),[row.id])&&
    Number.isInteger(result.sections[row.id])&&result.sections[row.id]===result.passedAssertions&&result.sections[row.id]===row.assertions,
    'R386_CANVAS_COST_COUNT');
  requireThat(same(Object.keys(result.sectionElapsedMs||{}),[row.id])&&Number.isFinite(result.sectionElapsedMs[row.id])&&result.sectionElapsedMs[row.id]>0,
    'R386_CANVAS_COST_TIMING');
  return {assertions:result.sections[row.id],milliseconds:result.sectionElapsedMs[row.id],runId:manifest.run_id,attempt:manifest.run_attempt,
    executionSha:manifest.execution_sha,headSha:manifest.head_sha};
}
function zipMembers(file){
  // Reading ZIP is deliberately delegated to the standard library, not to an
  // external unzip command or an archive extractor that writes arbitrary paths.
  const code='import sys,json,zipfile,base64\nz=zipfile.ZipFile(sys.argv[1])\nr={}\nfor i in z.infolist():\n if i.is_dir(): continue\n n=i.filename.rsplit("/",1)[-1]\n if n in ("manifest.json","stdout.log","stderr.log"):\n  assert n not in r and i.file_size <= 16777216, "duplicate or oversized cost raw"\n  r[n]=base64.b64encode(z.read(i)).decode()\nassert set(r)=={"manifest.json","stdout.log","stderr.log"}, "missing cost raw"\nprint(json.dumps(r))';
  const run=spawnSync(process.env.PYTHON||'python3',['-c',code,file],{encoding:'utf8',maxBuffer:64*1024*1024});
  requireThat(!run.error&&run.status===0,'R386_CANVAS_COST_ZIP',run.stderr||String(run.error||''));
  return Object.fromEntries(Object.entries(parseJson(run.stdout)).map(([name,value])=>[name,Buffer.from(value,'base64')]));
}
const zipCache=new Map();
function zipEntries(file,names){
  const raw=fs.readFileSync(file),key=sha(raw)+':'+names.join('|');
  if(zipCache.has(key))return zipCache.get(key);
  const code='import sys,json,zipfile,base64\nz=zipfile.ZipFile(sys.argv[1])\nr={}\nfor n in json.loads(sys.argv[2]):\n hits=[i for i in z.infolist() if not i.is_dir() and (i.filename==n or i.filename.endswith("/"+n))]\n assert len(hits)==1 and hits[0].file_size <= 16777216, "missing, duplicate or oversized original"\n r[n]=base64.b64encode(z.read(hits[0])).decode()\nprint(json.dumps(r))';
  const run=spawnSync(process.env.PYTHON||'python3',['-c',code,file,JSON.stringify(names)],{encoding:'utf8',maxBuffer:128*1024*1024});
  requireThat(!run.error&&run.status===0,'R386_CANVAS_ORIGINAL_ZIP',run.stderr||String(run.error||''));
  const entries=Object.fromEntries(Object.entries(parseJson(run.stdout)).map(([name,value])=>[name,Buffer.from(value,'base64')]));
  if(zipCache.size>=32)zipCache.delete(zipCache.keys().next().value);zipCache.set(key,entries);return entries;
}
function artifactRecord(root,record,sourceFiles){
  exactKeys(record,['id','url','path','sha256','runId'],'R386_CANVAS_ARTIFACT_KEYS');
  requireThat(Number.isSafeInteger(record.id)&&record.id>0&&record.url==='https://api.github.com/repos/ZhiQiYang/geometry-axiom/actions/artifacts/'+record.id&&
    /^[0-9a-f]{64}$/.test(record.sha256||'')&&/^\d+$/.test(String(record.runId)),'R386_CANVAS_ARTIFACT');
  const file=relativeFile(root,record.path,'R386_CANVAS_ARTIFACT_MISSING');
  requireThat(sha(fs.readFileSync(file))===record.sha256,'R386_CANVAS_ARTIFACT_DIGEST');sourceFiles.push(record.path);return file;
}
function exactZipFiles(file,wanted){
  const code='import sys,json,zipfile\nz=zipfile.ZipFile(sys.argv[1])\na=[i for i in z.infolist() if not i.is_dir()]\nn=[i.filename for i in a]\nassert len(n)==len(set(n)) and all(not i.filename.startswith("/") and ".." not in i.filename.split("/") and ((i.external_attr>>16)&0o170000)!=0o120000 for i in a), "unsafe or duplicate ZIP entry"\nprint(json.dumps(sorted(n)))';
  const run=spawnSync(process.env.PYTHON||'python3',['-c',code,file],{encoding:'utf8',maxBuffer:4*1024*1024});
  requireThat(!run.error&&run.status===0&&same(parseJson(run.stdout),[...wanted].sort()),'R386_CANVAS_ZIP_FILE_SET');
}
function legacySha(inherited){return sha(stable({plan:inherited.plan,golden:inherited.golden}));}
function unitCapture(entries,unit,inherited){
  const receipt=parseJson(entries['manifest.json']),plan=parseJson(entries['plan.json']);
  requireThat(receipt.schema==='geometry-canvas-shard/1'&&receipt.verified===true&&receipt.process_exit===0&&receipt.runtime_exit===0&&
    receipt.shard===unit+'/2'&&same(receipt.command,['node','geometry-web/cdp_test.js']),'R386_CANVAS_UNIT_RECEIPT');
  for(const key of ['execution_sha','head_sha','tree'])requireThat(/^[0-9a-f]{40}$/.test(receipt[key]||''),'R386_CANVAS_UNIT_IDENTITY');
  for(const key of ['run_id','run_attempt'])requireThat(/^\d+$/.test(receipt[key]||''),'R386_CANVAS_UNIT_IDENTITY');
  exactKeys(receipt.files,['plan.json','stdout.log','stderr.log','runtime.stdout','runtime.stderr'],'R386_CANVAS_UNIT_FILES');
  for(const [name,digest] of Object.entries(receipt.files))requireThat(sha(entries[name])===digest,'R386_CANVAS_UNIT_RAW_HASH',name);
  const snapshot=clone(plan);delete snapshot.sha256;
  requireThat(plan.schema==='geometry-canvas-plan/2'&&plan.sha256===sha(stable(snapshot))&&receipt.plan_sha256===plan.sha256,
    'R386_CANVAS_UNIT_PLAN_HASH');
  const legacySet=new Set(inherited.ids);
  requireThat(same(plan.numericPlan.shards.map(row=>({index:row.index,sections:row.sections.filter(id=>legacySet.has(id))})),inherited.plan.shards)&&
    plan.numericPlan.boundaries?.length===1&&plan.numericPlan.boundaries[0].before==='P72'&&
    same(plan.numericPlan.boundaries[0].localStorage,inherited.plan.boundaries[0].localStorage)&&
    inherited.ids.every(id=>plan.golden.sections[id]===inherited.golden.sections[id]),'R386_CANVAS_UNIT_LEGACY_CENSUS');
  const events=[],results=[];
  for(const line of entries['stdout.log'].toString('utf8').split(/\r?\n/)){
    if(line.startsWith('CANVAS_SHARD_EVENT '))events.push(parseJson(line.slice(19)));
    if(line.startsWith('CDP_RESULT '))results.push(parseJson(line.slice(11)));
  }
  requireThat(results.length===1,'R386_CANVAS_UNIT_RESULT_COUNT');
  require('../tests/helpers/canvas_shards.js').verifyTrace(plan,unit+'/2',events,results[0]);
  requireThat(Number.isFinite(results[0].elapsedSeconds)&&results[0].elapsedSeconds>0,'R386_CANVAS_UNIT_ELAPSED');
  const runtime=parseJson(entries['runtime.stdout']);
  requireThat(runtime.schema==='geometry-runtime/1'&&runtime.fresh===true&&runtime.version===receipt.runtime_version,'R386_CANVAS_UNIT_RUNTIME');
  let milliseconds=results[0].elapsedSeconds*1000,basis='opaque-unit-elapsed';
  if(results[0].sectionOrder.some(id=>!legacySet.has(id))){
    const timing=results[0].sectionElapsedMs,ids=inherited.plan.shards[unit-1].sections;
    requireThat(timing&&ids.every(id=>Number.isFinite(timing[id])&&timing[id]>=0),'R386_CANVAS_UNIT_SECTION_TIMING');
    milliseconds=ids.reduce((sum,id)=>sum+timing[id],0);basis='legacy-section-timing-sum';
    requireThat(milliseconds>0,'R386_CANVAS_UNIT_SECTION_TIMING');
  }
  return {milliseconds,basis,runId:receipt.run_id,attempt:receipt.run_attempt,
    executionSha:receipt.execution_sha,headSha:receipt.head_sha};
}
function readUnitCosts(root,inherited,sourceFiles){
  const costs={};
  for(const unit of [1,2]){
    const relative=UNIT_DIRECTORY+'/'+unit+'.json';if(!fs.existsSync(path.join(root,relative)))continue;
    const receipt=readJson(root,relative);exactKeys(receipt,['schema','unit','legacySha256','artifact','measured'],'R386_CANVAS_UNIT_COST_KEYS');
    requireThat(receipt.schema==='geometry-canvas-unit-cost/1'&&receipt.unit===unit&&receipt.legacySha256===legacySha(inherited),'R386_CANVAS_UNIT_COST_LEGACY');
    requireThat(receipt.artifact?.path===UNIT_DIRECTORY+'/'+unit+'/artifact.zip','R386_CANVAS_UNIT_COST_PATH');
    const file=artifactRecord(root,receipt.artifact,sourceFiles),entries=zipEntries(file,['manifest.json','plan.json','stdout.log','stderr.log','runtime.stdout','runtime.stderr']);
    const measured=unitCapture(entries,unit,inherited);
    requireThat(same(measured,receipt.measured)&&String(receipt.artifact.runId)===measured.runId,'R386_CANVAS_UNIT_COST_SUMMARY');
    sourceFiles.push(relative);costs[unit]={...measured,receipt:relative,sha256:sha(fs.readFileSync(path.join(root,relative)))};
  }
  return costs;
}
const PROTOCOL_FILES=['geometry-web/canvas_registry.js','geometry-web/canvas_shards.js','geometry-web/cdp_test.js',
  'geometry-web/cdp_floor.js','geometry-web/cdp_helpers.js','geometry-web/cdp_evaluation.js','geometry-web/cdp_navigation.js',
  'geometry-web/transport_failure_trace.js','tests/helpers/canvas_shards.js','.github/scripts/canvas_evidence.py',
  'geometry-web/runtime_version.py','.github/scripts/canvas_slot_proof.py',
  '.github/scripts/canvas_slot_probe.cjs','.github/scripts/test_canvas_slot_proof.py','.github/workflows/canvas-slot-proof.yml'];
function slotIdentity(root,id){
  const inherited=archive(root),row=readJson(root,DIRECTORY+'/'+id+'.json');
  requireThat(row.id===id&&row.execution?.kind==='module','R386_CANVAS_MODULE_UNKNOWN',id);
  const protocol=sourceClosure(root,PROTOCOL_FILES);
  return {id,module:row.execution.module,moduleSha256:moduleSourceHash(root,row.execution.module),
    protocolSha256:protocol.sha256,legacySha256:legacySha(inherited)};
}
function verifySlotRun({receipt,plan,candidate,events,result},root=ROOT){
  requireThat(receipt.schema==='geometry-canvas-slot-capture/1'&&receipt.capture_verified===true&&receipt.acceptance===false&&
    receipt.process_exit===0&&receipt.runtime_exit===0&&receipt.runtime_fresh===true,'R386_CANVAS_SLOT_CAPTURE');
  requireThat(candidate.schema==='geometry-canvas-placement-candidate/1'&&[1,2].includes(candidate.unit)&&
    candidate.id===receipt.id&&candidate.unit===receipt.slot&&candidate.sourceSha===receipt.execution_sha,'R386_CANVAS_SLOT_CANDIDATE');
  for(const key of ['module','moduleSha256','protocolSha256','legacySha256'])requireThat(candidate[key]===receipt[key],'R386_CANVAS_SLOT_PIN',key);
  requireThat(receipt.candidate_sha256===sha(encode(candidate))&&receipt.plan_sha256===plan.sha256,'R386_CANVAS_SLOT_PLAN_HASH');
  const bare=clone(plan);delete bare.sha256;requireThat(plan.sha256===sha(stable(bare)),'R386_CANVAS_SLOT_PLAN_HASH');
  requireThat(same(plan.numericPlan.registryCandidate,candidate),'R386_CANVAS_SLOT_PLAN_CANDIDATE');
  requireThat(result.scope?.acceptance===false&&result.scope?.placementCandidateSha256===receipt.candidate_sha256,'R386_CANVAS_SLOT_SCOPE');
  requireThat(same(receipt.command,['node','geometry-web/cdp_test.js']),'R386_CANVAS_SLOT_COMMAND');
  let url;try{url=new URL(receipt.environment?.GEOMETRY_TEST_URL);}catch{requireThat(false,'R386_CANVAS_SLOT_ENDPOINT');}
  requireThat(url.protocol==='http:'&&url.hostname==='127.0.0.1'&&url.port&&url.pathname==='/'&&!url.search&&!url.hash&&!url.username&&!url.password,
    'R386_CANVAS_SLOT_ENDPOINT');
  requireThat(same(receipt.runtime_command,['<python>','-B','geometry-web/runtime_version.py','--probe',url.port])&&
    result.scope.url===receipt.environment.GEOMETRY_TEST_URL&&result.scope.feedbackDirectory===receipt.environment.GEOMETRY_FEEDBACK_DIR,
    'R386_CANVAS_SLOT_RUNTIME_SCOPE');
  requireThat(receipt.environment.GEOMETRY_CDP_SHARD===(receipt.mode==='full'?null:receipt.mode.slice(-1)+'/2'),'R386_CANVAS_SLOT_RUNTIME_SHARD');
  const inherited=archive(root),legacySet=new Set(inherited.ids),row=readJson(root,DIRECTORY+'/'+candidate.id+'.json');
  requireThat(plan.golden.sections[candidate.id]===row.assertions&&inherited.ids.every(id=>plan.golden.sections[id]===inherited.golden.sections[id]),
    'R386_CANVAS_SLOT_PROVEN_COUNT');
  requireThat(same(plan.numericPlan.shards.map(unit=>({index:unit.index,sections:unit.sections.filter(id=>legacySet.has(id))})),inherited.plan.shards)&&
    plan.numericPlan.boundaries?.length===1&&plan.numericPlan.boundaries[0].before==='P72'&&
    same(plan.numericPlan.boundaries[0].localStorage,inherited.plan.boundaries[0].localStorage),'R386_CANVAS_SLOT_LEGACY_SEQUENCE');
  requireThat(same(plan.numericPlan.shards.map(unit=>unit.sections.filter(id=>id===candidate.id)),candidate.unit===1?[[candidate.id],[]]:[[],[candidate.id]]),
    'R386_CANVAS_SLOT_ACTUAL_OWNER');
  if(receipt.mode==='full'){
    requireThat(result.schema==='geometry-cdp-result/1'&&result.completed===true&&result.scope.mode==='full'&&same(result.scope.filters,[])&&
      same(result.scope.modifiers,[])&&result.failedAssertions===0&&same(result.skipped,[])&&!result.sectionsFailed&&
      result.unexpectedBrowserExceptions===0&&result.goldenCompare==='matched','R386_CANVAS_SLOT_FULL_RESULT');
    requireThat(result.passedAssertions===plan.golden.total&&same(result.sections,plan.golden.sections)&&
      same(result.sectionOrder,plan.numericPlan.shards.flatMap(row=>row.sections)),'R386_CANVAS_SLOT_FULL_CENSUS');
  }else{
    requireThat(receipt.mode==='shard1'||receipt.mode==='shard2','R386_CANVAS_SLOT_MODE');
    require('../tests/helpers/canvas_shards.js').verifyTrace(plan,receipt.mode.slice(-1)+'/2',events,result);
  }
  return {mode:receipt.mode,slot:receipt.slot,assertions:result.passedAssertions,planSha256:plan.sha256,capture_verified:true,acceptance:false};
}
function verifySlotProof(root,id,zipFile){
  const identity=slotIdentity(root,id),proof=parseJson(zipEntries(zipFile,['proof.json'])['proof.json']);
  requireThat(proof.schema==='geometry-canvas-slot-proof/1'&&proof.acceptance===false,'R386_CANVAS_SLOT_PROOF_SCHEMA');
  for(const [key,value] of Object.entries(identity))requireThat(proof[key]===value,'R386_CANVAS_SLOT_PROOF_PIN',key);
  for(const key of ['execution_sha','head_sha','tree'])requireThat(/^[0-9a-f]{40}$/.test(proof[key]||''),'R386_CANVAS_SLOT_PROOF_IDENTITY');
  for(const key of ['run_id','run_attempt'])requireThat(/^\d+$/.test(proof[key]||''),'R386_CANVAS_SLOT_PROOF_IDENTITY');
  requireThat(Array.isArray(proof.captures)&&proof.captures.length===6,'R386_CANVAS_SLOT_CAPTURE_SET');
  const results=[],expectedZip=['proof.json','mutations/manifest.json'];
  for(const slot of [1,2])for(const mode of ['full','shard1','shard2']){
    const folder='slot'+slot+'/'+mode+'/',names=['manifest.json','candidate.json','plan.json','stdout.log','stderr.log','runtime.stdout','runtime.stderr'];
    const entries=zipEntries(zipFile,names.map(name=>folder+name));
    expectedZip.push(...names.map(name=>folder+name));
    const receipt=parseJson(entries[folder+'manifest.json']);
    for(const key of ['execution_sha','head_sha','tree','run_id','run_attempt'])requireThat(receipt[key]===proof[key],'R386_CANVAS_SLOT_MIXED_SOURCE',key);
    for(const [key,value] of Object.entries(identity))requireThat(receipt[key]===value,'R386_CANVAS_SLOT_CAPTURE_PIN',key);
    requireThat(receipt.id===id&&receipt.slot===slot&&receipt.mode===mode,'R386_CANVAS_SLOT_DIRECTORY');
    const summaries=proof.captures.filter(item=>item.unit===slot&&item.mode===mode);
    requireThat(summaries.length===1&&summaries[0].manifest===folder+'manifest.json'&&summaries[0].sha256===sha(entries[folder+'manifest.json']),
      'R386_CANVAS_SLOT_CAPTURE_SUMMARY');
    exactKeys(receipt.files,names.filter(name=>name!=='manifest.json'),'R386_CANVAS_SLOT_FILES');
    for(const [name,digest] of Object.entries(receipt.files))requireThat(sha(entries[folder+name])===digest,'R386_CANVAS_SLOT_RAW_HASH',folder+name);
    const candidate=parseJson(entries[folder+'candidate.json']),plan=parseJson(entries[folder+'plan.json']),events=[],runs=[];
    for(const line of entries[folder+'stdout.log'].toString('utf8').split(/\r?\n/)){
      if(line.startsWith('CANVAS_SHARD_EVENT '))events.push(parseJson(line.slice(19)));
      if(line.startsWith('CDP_RESULT '))runs.push(parseJson(line.slice(11)));
    }
    requireThat(runs.length===1,'R386_CANVAS_SLOT_RESULT_COUNT');
    const runtime=parseJson(entries[folder+'runtime.stdout']);
    requireThat(runtime.schema==='geometry-runtime/1'&&runtime.fresh===true&&runtime.version===receipt.runtime_version&&runtime.root===receipt.execution_root,
      'R386_CANVAS_SLOT_RUNTIME');
    results.push(verifySlotRun({receipt,plan,candidate,events,result:runs[0]},root));
  }
  requireThat(proof.mutationProof&&typeof proof.mutationProof.file==='string'&&/^[0-9a-f]{64}$/.test(proof.mutationProof.sha256||''),'R386_CANVAS_SLOT_MUTATION_PROOF');
  const mutationRaw=zipEntries(zipFile,[proof.mutationProof.file])[proof.mutationProof.file];
  requireThat(sha(mutationRaw)===proof.mutationProof.sha256,'R386_CANVAS_SLOT_MUTATION_HASH');
  const mutations=parseJson(mutationRaw);
  requireThat(mutations.schema==='geometry-canvas-slot-mutations/1'&&Array.isArray(mutations.rows)&&mutations.rows.length===2,'R386_CANVAS_SLOT_MUTATIONS');
  requireThat(same(mutations.rows.map(row=>row.id).sort(),['R386_CANVAS_SLOT_STATE_GUARD','R386_CANVAS_SLOT_STORAGE_RESTORE']),'R386_CANVAS_SLOT_MUTATION_IDS');
  for(const row of mutations.rows){
    requireThat(row.baseline?.exit===0&&row.withdrawn?.exit===1&&row.restored?.exit===0&&
      typeof row.withdrawn.failedTest==='string'&&typeof row.withdrawn.oracle==='string','R386_CANVAS_SLOT_WITHDRAWAL',row.id);
    for(const phase of ['baseline','withdrawn','restored']){
      requireThat(row[phase].files&&typeof row[phase].files==='object','R386_CANVAS_SLOT_MUTATION_RAW');
      for(const [file,digest] of Object.entries(row[phase].files)){requireThat(sha(zipEntries(zipFile,[file])[file])===digest,'R386_CANVAS_SLOT_MUTATION_RAW',file);expectedZip.push(file);}
    }
  }
  const mutationJudge=spawnSync(process.env.PYTHON||'python3',[path.join(root,'.github/scripts/canvas_slot_proof.py'),
    'verify-mutations','--section',id,'--artifact',zipFile,'--mutation-file',proof.mutationProof.file],{cwd:root,encoding:'utf8',maxBuffer:4*1024*1024});
  requireThat(!mutationJudge.error&&mutationJudge.status===0,'R386_CANVAS_SLOT_MUTATION_JUDGE',mutationJudge.stderr||String(mutationJudge.error||''));
  for(const key of ['execution_sha','head_sha','tree','run_id','run_attempt'])requireThat(mutations[key]===proof[key],'R386_CANVAS_SLOT_MUTATION_IDENTITY',key);
  for(const [key,value] of Object.entries(identity))requireThat(mutations[key]===value,'R386_CANVAS_SLOT_MUTATION_PIN',key);
  exactZipFiles(zipFile,expectedZip);
  return {identity,executionSha:proof.execution_sha,headSha:proof.head_sha,runId:proof.run_id,attempt:proof.run_attempt,slots:[1,2],runs:results};
}
function readSlotProof(root,row,sourceFiles){
  exactKeys(row.balance,['receipt','sha256'],'R386_CANVAS_SLOT_RECEIPT_KEYS');
  requireThat(row.balance.receipt.startsWith(SLOT_DIRECTORY+'/'+row.id+'/'),'R386_CANVAS_SLOT_RECEIPT_PATH');
  const raw=fs.readFileSync(relativeFile(root,row.balance.receipt));requireThat(sha(raw)===row.balance.sha256,'R386_CANVAS_SLOT_RECEIPT_HASH');
  const receipt=parseJson(raw);exactKeys(receipt,['schema','artifact','verified'],'R386_CANVAS_SLOT_RECEIPT_KEYS');
  requireThat(receipt.schema==='geometry-canvas-slot-receipt/1'&&receipt.artifact?.path===path.posix.dirname(row.balance.receipt)+'/artifact.zip','R386_CANVAS_SLOT_RECEIPT_SCHEMA');
  const file=artifactRecord(root,receipt.artifact,sourceFiles),verified=verifySlotProof(root,row.id,file);
  requireThat(same(receipt.verified,verified)&&String(receipt.artifact.runId)===verified.runId,'R386_CANVAS_SLOT_RECEIPT_SUMMARY');
  sourceFiles.push(row.balance.receipt);return verified;
}
/* Independent dependency components are indivisible. At <= 24 flexible
 * components, meet-in-the-middle is exact (at most 2 * 4096 subsets). Larger
 * registries use deterministic LPT; no assertion count is a cost proxy. */
function solvePlacement(rows,costs,unitCosts,allowed){
  requireThat(unitCosts[1]&&unitCosts[2],'R386_CANVAS_UNIT_COST_REQUIRED');
  const parent=new Map(rows.map(row=>[row.id,row.id]));
  const find=id=>{while(parent.get(id)!==id)id=parent.get(id);return id;};
  const union=(a,b)=>{a=find(a);b=find(b);if(a!==b)parent.set(a<b?b:a,a<b?a:b);};
  for(const row of rows)for(const id of [...row.order.after,...row.order.before])union(row.id,id);
  const groups=new Map();for(const row of rows){const id=find(row.id);if(!groups.has(id))groups.set(id,[]);groups.get(id).push(row.id);}
  const ns=ms=>{const value=Math.round(ms*1e6);requireThat(Number.isSafeInteger(value)&&value>0,'R386_CANVAS_MEASURED_COST_REQUIRED');return value;};
  const base={1:ns(unitCosts[1].milliseconds),2:ns(unitCosts[2].milliseconds)},assignment={},flex=[];
  for(const ids of [...groups.values()].map(ids=>ids.sort()).sort((a,b)=>a[0]<b[0]?-1:1)){
    const choices=[1,2].filter(unit=>ids.every(id=>allowed[id]?.includes(unit)));
    requireThat(choices.length,'R386_CANVAS_DEPENDENCY_SLOT_CONFLICT',ids.join(','));
    const weight=ids.reduce((sum,id)=>sum+ns(costs[id]?.milliseconds),0),group={ids,weight};
    if(choices.length===1){base[choices[0]]+=weight;for(const id of ids)assignment[id]=choices[0];}else flex.push(group);
  }
  let algorithm='exact-meet-in-the-middle',best;
  if(flex.length<=24){
    const half=Math.floor(flex.length/2),left=flex.slice(0,half),right=flex.slice(half);
    const subsets=part=>{const values=[{sum:0,mask:0}];for(let at=0;at<part.length;at++){const size=values.length;for(let i=0;i<size;i++)values.push({sum:values[i].sum+part[at].weight,mask:values[i].mask|(1<<at)});}return values;};
    const a=subsets(left),b=subsets(right).sort((x,y)=>x.sum-y.sum||x.mask-y.mask),total=flex.reduce((sum,row)=>sum+row.weight,0),target=(base[2]+total-base[1])/2;
    for(const item of a){let lo=0,hi=b.length;while(lo<hi){const mid=(lo+hi)>>1;if(b[mid].sum<target-item.sum)lo=mid+1;else hi=mid;}
      for(const at of [lo-1,lo])if(b[at]){const chosen=item.sum+b[at].sum,maximum=Math.max(base[1]+chosen,base[2]+total-chosen),bits=item.mask+b[at].mask*2**half;
        if(!best||maximum<best.maximum||maximum===best.maximum&&bits<best.bits)best={maximum,bits};}}
    flex.forEach((group,index)=>{const unit=Math.floor(best.bits/2**index)%2?1:2;for(const id of group.ids)assignment[id]=unit;});
  }else{
    algorithm='deterministic-lpt';const loads={...base};
    for(const group of [...flex].sort((a,b)=>b.weight-a.weight||(a.ids[0]<b.ids[0]?-1:1))){const unit=loads[1]<=loads[2]?1:2;loads[unit]+=group.weight;for(const id of group.ids)assignment[id]=unit;}
  }
  const loads={1:unitCosts[1].milliseconds,2:unitCosts[2].milliseconds};
  for(const row of rows)loads[assignment[row.id]]+=costs[row.id].milliseconds;
  return {assignment:Object.fromEntries(Object.entries(assignment).sort()),milliseconds:loads,algorithm,
    maximumMilliseconds:Math.max(loads[1],loads[2]),fitsOriginalTimeout:Math.max(loads[1],loads[2])<=35*60*1000};
}
function verifyCost(root,row,moduleHash,sourceFiles){
  if(row.cost)exactKeys(row.cost,['receipt','sha256'],'R386_CANVAS_COST_KEYS');
  requireThat(row.cost&&typeof row.cost.receipt==='string'&&/^[0-9a-f]{64}$/.test(row.cost.sha256||''),'R386_CANVAS_COST_RECEIPT_REQUIRED',row.id);
  requireThat(row.cost.receipt.startsWith('geometry-web/canvas-registry/costs/'+row.id+'/'),'R386_CANVAS_COST_PATH',row.id);
  const receiptRaw=fs.readFileSync(relativeFile(root,row.cost.receipt,'R386_CANVAS_COST_RECEIPT_REQUIRED'));
  requireThat(sha(receiptRaw)===row.cost.sha256,'R386_CANVAS_COST_RECEIPT_HASH',row.id);
  const receipt=parseJson(receiptRaw,row.cost.receipt),artifact=receipt.artifact;
  exactKeys(receipt,['schema','artifact','measured'],'R386_CANVAS_COST_KEYS');
  exactKeys(artifact,['id','url','path','sha256','runId'],'R386_CANVAS_COST_ARTIFACT_KEYS');
  exactKeys(receipt.measured,['assertions','milliseconds','runId','attempt','executionSha','headSha'],'R386_CANVAS_COST_MEASURED_KEYS');
  requireThat(receipt.schema==='geometry-canvas-section-cost/1'&&artifact&&Number.isSafeInteger(artifact.id)&&artifact.id>0&&
    /^https:\/\/api\.github\.com\/repos\/ZhiQiYang\/geometry-axiom\/actions\/artifacts\/\d+$/.test(artifact.url||'')&&
    artifact.url.endsWith('/'+artifact.id)&&/^[0-9a-f]{64}$/.test(artifact.sha256||''),'R386_CANVAS_COST_ARTIFACT');
  requireThat(artifact.path===path.posix.dirname(row.cost.receipt)+'/artifact.zip','R386_CANVAS_COST_PATH');
  const zip=relativeFile(root,artifact.path,'R386_CANVAS_COST_ZIP'),raw=fs.readFileSync(zip);
  requireThat(sha(raw)===artifact.sha256,'R386_CANVAS_COST_ARTIFACT_DIGEST');
  const members=zipMembers(zip),manifest=parseJson(members['manifest.json'],'manifest.json');
  const measured=verifyMeasurement(manifest,members['stdout.log'],members['stderr.log'],row,moduleHash);
  requireThat(String(artifact.runId)===measured.runId&&same(receipt.measured,measured),'R386_CANVAS_COST_SUMMARY');
  sourceFiles.push(row.cost.receipt,artifact.path);return measured;
}
function load(root=ROOT,{allowCandidates=false,ignorePlacementCandidate=false}={}){
  requireThat(!fs.existsSync(path.join(root,'tests/.registry-migration-pending')),'R386_INTERRUPTED_MIGRATION');
  const inherited=archive(root),files=filesAt(root,DIRECTORY,'.json');
  const fragments=files.map(file=>{
    const row=readJson(root,file);
    exactKeys(row,['schema','id','assertions','unit','order','execution','provenance','cost',...(row.execution?.kind==='module'?['balance']:[])],'R386_CANVAS_FRAGMENT_KEYS');
    requireThat(row.schema===SCHEMA&&typeof row.id==='string'&&file===DIRECTORY+'/'+row.id+'.json','R386_CANVAS_FRAGMENT_NAME',file);
    requireThat(Number.isInteger(row.assertions)&&row.assertions>=0,'R386_CANVAS_ASSERTIONS',row.id);
    requireThat(row.unit===1||row.unit===2||row.unit==='auto'&&row.execution?.kind==='module','R386_CANVAS_OWNER',row.id);
    requireThat(floor.sectionOf('=== '+row.id+'.')===row.id,'R386_CANVAS_SECTION_ID',row.id);
    return row;
  });
  const ids=fragments.map(row=>row.id);requireThat(new Set(ids).size===ids.length,'R386_CANVAS_DUPLICATE_SECTION');
  for(const id of inherited.ids)requireThat(ids.includes(id),'R386_CANVAS_MISSING_FRAGMENT',id);
  const sourceFiles=[META,ARCHIVE_PLAN,ARCHIVE_GOLDEN,...files],modules=[],costs={},allowed={};
  let acceptance=true;
  for(const row of fragments){
    if(inherited.ids.includes(row.id)){
      const unit=inherited.plan.shards.find(shard=>shard.sections.includes(row.id));
      requireThat(row.unit===unit.index,'R386_CANVAS_OWNER',row.id);
      requireThat(same(row.order,{legacy:unit.sections.indexOf(row.id)})&&same(row.execution,{kind:'legacy'}),'R386_CANVAS_LEGACY_ORDER',row.id);
      requireThat(row.assertions===inherited.golden.sections[row.id],'R386_CANVAS_COUNT_DRIFT',row.id);
      requireThat(same(row.provenance,{kind:'migration',baseSha:inherited.meta.baseSha,
        planSha256:inherited.meta.files[0].sha256,goldenSha256:inherited.meta.files[1].sha256}),'R386_CANVAS_LEGACY_PROVENANCE',row.id);
      requireThat(row.cost===null,'R386_CANVAS_COST_LEGACY_OPAQUE',row.id);
    }else{
      exactKeys(row.execution,['kind','module','export'],'R386_CANVAS_MODULE_EXECUTION_KEYS');
      exactKeys(row.provenance,row.provenance?.kind==='candidate'?['kind']:['kind','executionSha','headSha','runId','attempt'],'R386_CANVAS_MODULE_PROVENANCE_KEYS');
      requireThat((row.unit===2||row.unit==='auto')&&row.execution?.kind==='module'&&row.execution.module===MODULES+'/'+row.id+'.js'&&
        row.execution.export==='default','R386_CANVAS_MODULE_DECLARATION',row.id);
      relativeFile(root,row.execution.module,'R386_CANVAS_MODULE_MISSING');
      const closure=sourceClosure(root,[row.execution.module],{strict:true}),moduleHash=closure.sha256;
      sourceFiles.push(...Object.keys(closure.files));
      if(allowCandidates&&!row.cost){acceptance=false;}
      else costs[row.id]=verifyCost(root,row,moduleHash,sourceFiles);
      if(row.unit==='auto'){
        requireThat(row.balance!==null,'R386_CANVAS_SLOT_PROOF_REQUIRED',row.id);
        readSlotProof(root,row,sourceFiles);allowed[row.id]=[1,2];
      }else{requireThat(row.balance===null,'R386_CANVAS_SLOT_PROOF_OWNER',row.id);allowed[row.id]=[2];}
      modules.push(row);
    }
  }
  requireThat(same(filesAt(root,MODULES,'.js'),modules.map(row=>row.execution.module).sort()),'R386_CANVAS_MODULE_INVENTORY');
  const extensions=extensionOrder(modules),plan=clone(inherited.plan),golden=clone(inherited.golden);
  const unitCosts=readUnitCosts(root,inherited,sourceFiles);
  let assignment=Object.fromEntries(extensions.map(row=>[row.id,2])),planning={mode:'fixed-proven-units',automaticBalanceAcceptance:false,
    reason:'No independent module has an adopted two-slot proof; the original two stateful units are not repartitioned.'};
  if(extensions.some(row=>row.unit==='auto')){
    const solved=solvePlacement(extensions,costs,unitCosts,allowed);
    requireThat(solved.fitsOriginalTimeout,'R386_CANVAS_ORIGINAL_TIMEOUT_CAPACITY');assignment=solved.assignment;
    planning={mode:'measured-independent-slots',automaticBalanceAcceptance:true,...solved};
  }
  let candidate=null;
  if(!ignorePlacementCandidate&&process.env.GEOMETRY_CANVAS_PLACEMENT_CANDIDATE){
    const file=path.resolve(process.env.GEOMETRY_CANVAS_PLACEMENT_CANDIDATE);
    requireThat(fs.existsSync(file)&&fs.realpathSync(file)===file&&fs.lstatSync(file).isFile(),'R386_CANVAS_PLACEMENT_CANDIDATE_FILE');
    candidate=parseJson(fs.readFileSync(file),file);
    exactKeys(candidate,['schema','id','module','moduleSha256','protocolSha256','legacySha256','unit','sourceSha'],'R386_CANVAS_PLACEMENT_CANDIDATE_KEYS');
    requireThat(candidate.schema==='geometry-canvas-placement-candidate/1'&&[1,2].includes(candidate.unit),'R386_CANVAS_PLACEMENT_CANDIDATE_SCHEMA');
    for(const [key,value] of Object.entries(slotIdentity(root,candidate.id)))requireThat(candidate[key]===value,'R386_CANVAS_PLACEMENT_CANDIDATE_PIN',key);
    requireThat(candidate.sourceSha===gitHead(root),'R386_CANVAS_PLACEMENT_CANDIDATE_HEAD');
    const related=new Set([candidate.id]);let changed=true;
    while(changed){changed=false;for(const row of extensions)if(related.has(row.id)||[...row.order.after,...row.order.before].some(id=>related.has(id))){
      for(const id of [row.id,...row.order.after,...row.order.before])if(!related.has(id)){related.add(id);changed=true;}}}
    for(const id of related)assignment[id]=candidate.unit;
    acceptance=false;planning={mode:'candidate-only',automaticBalanceAcceptance:false,assignment};plan.registryCandidate=candidate;
  }
  for(const shard of plan.shards)shard.sections=fragments.filter(row=>row.execution.kind==='legacy'&&row.unit===shard.index)
    .sort((a,b)=>a.order.legacy-b.order.legacy).map(row=>row.id);
  plan.shards[0].sections.push(...extensions.filter(row=>assignment[row.id]===1).map(row=>row.id));
  plan.shards[1].sections.splice(plan.shards[1].sections.length-1,0,...extensions.filter(row=>assignment[row.id]===2).map(row=>row.id));
  plan.boundaries[0].after=plan.shards[0].sections.at(-1);
  if(extensions.some(row=>row.unit==='auto'))plan.registryPlanning=planning;
  for(const key of Object.keys(golden.sections))golden.sections[key]=fragments.find(row=>row.id===key).assertions;
  for(const row of extensions)golden.sections[row.id]=row.assertions;
  golden.total=Object.values(golden.sections).reduce((sum,count)=>sum+count,0);
  return {schema:'geometry-canvas-registry/1',root,plan,golden,fragments,extensions,sourceFiles:[...new Set(sourceFiles)].sort(),acceptance,
    assignment,costs,unitCosts,planning,candidate,
    baseline:inherited,planSha256:sha(encode(plan)),goldenSha256:sha(encode(golden))};
}
const loadPlan=(root=ROOT,options={})=>load(root,options).plan;
const loadGolden=(root=ROOT,options={})=>load(root,options).golden;
function legacyView(root=ROOT,options={}){
  const current=load(root,options),keep=new Set(current.baseline.ids),plan=clone(current.plan),golden=clone(current.golden);
  for(const shard of plan.shards)shard.sections=shard.sections.filter(id=>keep.has(id));
  for(const id of Object.keys(golden.sections))if(!keep.has(id))delete golden.sections[id];
  plan.boundaries[0].after=current.baseline.plan.boundaries[0].after;delete plan.registryCandidate;delete plan.registryPlanning;
  golden.total=Object.values(golden.sections).reduce((sum,count)=>sum+count,0);return {plan,golden};
}
async function dispatch(root=ROOT,scope,helpers,options={}){
  const registry=load(root,options);
  let selected=[];
  const slot=options.slot??2;
  if(scope.mode==='full'||scope.mode==='shard'&&scope.shard.index===slot)selected=registry.extensions.filter(row=>registry.assignment[row.id]===slot);
  if(scope.mode==='partial'&&scope.module)selected=registry.extensions.filter(row=>row.id===scope.module);
  if(scope.module)requireThat(selected.length===1,'R386_CANVAS_MODULE_UNKNOWN',scope.module);
  for(const row of selected){const callback=require(path.join(root,row.execution.module));
    requireThat(typeof callback==='function','R386_CANVAS_MODULE_EXPORT',row.id);
    const context=Object.freeze({...helpers});await runSlotIsolation(context,()=>callback(context));}
}
const STORAGE_EXPRESSION='(()=>({local:Object.fromEntries(Object.keys(localStorage).sort().map(k=>[k,localStorage.getItem(k)])),session:Object.fromEntries(Object.keys(sessionStorage).sort().map(k=>[k,sessionStorage.getItem(k)]))}))()';
function restoreStorageExpression(snapshot){return '(()=>{const s='+JSON.stringify(snapshot)+';localStorage.clear();sessionStorage.clear();for(const [k,v] of Object.entries(s.local))localStorage.setItem(k,v);for(const [k,v] of Object.entries(s.session))sessionStorage.setItem(k,v);return true;})()';}
async function runSlotIsolation(helpers,callback){
  requireThat(typeof helpers.eval_==='function','R386_CANVAS_SLOT_BROWSER_EVALUATOR');
  const snapshot=await helpers.eval_(STORAGE_EXPRESSION);let result;
  exactKeys(snapshot,['local','session'],'R386_CANVAS_SLOT_STORAGE_SNAPSHOT');
  try{result=await callback();
    if(helpers.waitForUI)await helpers.waitForUI("(typeof oc==='undefined'||!oc.busy)&&(typeof ReferenceWorkspace==='undefined'||!ReferenceWorkspace.busy)&&!document.querySelector('dialog[open],.reference-impact[open]')");}
  finally{
    await helpers.eval_(restoreStorageExpression(snapshot));
    const actual=await helpers.eval_(STORAGE_EXPRESSION);
    requireThat(same(snapshot,actual),'R386_CANVAS_SLOT_STATE_RESTORE');
  }
  return result;
}
function gitHead(root){
  const run=spawnSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'});
  requireThat(run.status===0&&/^[0-9a-f]{40}\s*$/.test(run.stdout),'R386_CANVAS_GIT_HEAD');return run.stdout.trim();
}
function placementCandidate(root,id,unit,outfile){
  requireThat([1,2].includes(unit),'R386_CANVAS_PLACEMENT_SLOT');
  const current=load(root,{ignorePlacementCandidate:true});
  requireThat(current.extensions.some(row=>row.id===id),'R386_CANVAS_MODULE_UNKNOWN');
  const result={schema:'geometry-canvas-placement-candidate/1',...slotIdentity(root,id),unit,sourceSha:gitHead(root)};
  if(outfile){fs.mkdirSync(path.dirname(path.resolve(outfile)),{recursive:true});fs.writeFileSync(outfile,encode(result));}return result;
}
function createSectionTimer(clock=()=>process.hrtime.bigint()){
  const totals={};let current=null,start=null,finished=false;
  function close(){if(current!==null){const now=clock();requireThat(typeof now==='bigint'&&now>=start,'R386_CANVAS_CLOCK');
    totals[current]=(totals[current]||0)+Number(now-start)/1e6;start=now;}}
  return {enter(id){requireThat(!finished,'R386_CANVAS_TIMER_FINISHED');if(current===id)return;close();current=id;totals[id]??=0;start=clock();},
    finish(){if(!finished){close();finished=true;}return {...totals};}};
}
function importCost(root,{id,artifactFile,artifactId}){
  const registry=load(root,{allowCandidates:true}),row=registry.extensions.find(item=>item.id===id);
  requireThat(row,'R386_CANVAS_MODULE_UNKNOWN',id);
  requireThat(/^\d+$/.test(String(artifactId)),'R386_CANVAS_COST_ARTIFACT');
  const endpoint='repos/ZhiQiYang/geometry-axiom/actions/artifacts/'+artifactId;
  const api=spawnSync('gh',['api',endpoint],{encoding:'utf8',maxBuffer:4*1024*1024});
  requireThat(!api.error&&api.status===0,'R386_CANVAS_OFFICIAL_ARTIFACT_API',api.stderr||String(api.error||''));
  const official=parseJson(api.stdout,endpoint),raw=fs.readFileSync(artifactFile),digest=sha(raw);
  requireThat(official.id===Number(artifactId)&&official.expired===false&&official.digest==='sha256:'+digest,'R386_CANVAS_OFFICIAL_ARTIFACT_DIGEST');
  const members=zipMembers(artifactFile),manifest=parseJson(members['manifest.json']);
  const moduleHash=moduleSourceHash(root,row.execution.module);
  const actual=parseJson(members['stdout.log'].toString('utf8').split(/\r?\n/).find(line=>line.startsWith('CDP_RESULT '))?.slice(11)||'null');
  const proposed={...row,assertions:actual?.sections?.[id]};
  const measured=verifyMeasurement(manifest,members['stdout.log'],members['stderr.log'],proposed,moduleHash);
  requireThat(String(official.workflow_run?.id)===measured.runId,'R386_CANVAS_OFFICIAL_ARTIFACT_RUN');
  verifyOfficialRun(measured,'.github/workflows/canvas-section-measure.yml',true);
  const directory='geometry-web/canvas-registry/costs/'+id+'/'+artifactId,receiptPath=directory+'/receipt.json';
  const receipt={schema:'geometry-canvas-section-cost/1',artifact:{id:Number(artifactId),url:'https://api.github.com/'+endpoint,
    path:directory+'/artifact.zip',sha256:digest,runId:measured.runId},measured};
  const receiptRaw=encode(receipt),target=path.join(root,directory);fs.mkdirSync(target,{recursive:true});
  fs.writeFileSync(path.join(target,'artifact.zip'),raw);fs.writeFileSync(path.join(target,'receipt.json'),receiptRaw);
  const updated={...row,assertions:measured.assertions,provenance:{kind:'ci-capture',executionSha:manifest.execution_sha,
    headSha:manifest.head_sha,runId:measured.runId,attempt:measured.attempt},cost:{receipt:receiptPath,sha256:sha(receiptRaw)}};
  fs.writeFileSync(path.join(root,DIRECTORY+'/'+id+'.json'),encode(updated));
  load(root);return {id,...measured,receipt:receiptPath,acceptance:false,note:'Measurement imports count/cost only; current full and two-shard browser acceptance is still required.'};
}
function officialArtifact(artifactFile,artifactId){
  requireThat(/^\d+$/.test(String(artifactId)),'R386_CANVAS_OFFICIAL_ARTIFACT_ID');
  const endpoint='repos/ZhiQiYang/geometry-axiom/actions/artifacts/'+artifactId;
  const run=spawnSync('gh',['api',endpoint],{encoding:'utf8',maxBuffer:4*1024*1024});
  requireThat(!run.error&&run.status===0,'R386_CANVAS_OFFICIAL_ARTIFACT_API',run.stderr||String(run.error||''));
  const official=parseJson(run.stdout),digest=sha(fs.readFileSync(artifactFile));
  requireThat(official.id===Number(artifactId)&&official.digest==='sha256:'+digest&&official.workflow_run?.id,'R386_CANVAS_OFFICIAL_ARTIFACT_DIGEST');
  return {id:official.id,url:'https://api.github.com/'+endpoint,sha256:digest,runId:String(official.workflow_run.id)};
}
function verifyOfficialRun(identity,workflow,dispatch=false){
  requireThat(/^\d+$/.test(String(identity.runId))&&/^\d+$/.test(String(identity.attempt)),'R386_CANVAS_OFFICIAL_RUN_ID');
  const endpoint='repos/ZhiQiYang/geometry-axiom/actions/runs/'+identity.runId+'/attempts/'+identity.attempt;
  const run=spawnSync('gh',['api',endpoint],{encoding:'utf8',maxBuffer:4*1024*1024});
  requireThat(!run.error&&run.status===0,'R386_CANVAS_OFFICIAL_RUN_API',run.stderr||String(run.error||''));
  const official=parseJson(run.stdout);
  requireThat(String(official.id)===String(identity.runId)&&String(official.run_attempt)===String(identity.attempt)&&
    official.path===workflow&&official.status==='completed'&&official.conclusion==='success'&&official.head_sha===identity.headSha,
    'R386_CANVAS_OFFICIAL_RUN_SOURCE');
  if(dispatch)requireThat(official.event==='workflow_dispatch'&&identity.executionSha===identity.headSha,'R386_CANVAS_OFFICIAL_DISPATCH_SOURCE');
  return {runId:String(official.id),attempt:String(official.run_attempt),headSha:official.head_sha,workflow:official.path};
}
function writeImport(root,writes,validate){
  const previous=new Map([...writes.keys()].map(relative=>[relative,fs.existsSync(path.join(root,relative))?fs.readFileSync(path.join(root,relative)):null]));
  try{
    for(const [relative,raw] of writes){const file=path.join(root,relative);fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,raw);}
    return validate();
  }catch(error){for(const [relative,raw] of previous){const file=path.join(root,relative);if(raw===null)fs.rmSync(file,{force:true});else fs.writeFileSync(file,raw);}throw error;}
}
function importUnitCost(root,{unit,artifactFile,artifactId}){
  requireThat([1,2].includes(unit),'R386_CANVAS_UNIT');const inherited=archive(root),artifact=officialArtifact(artifactFile,artifactId);
  const measured=unitCapture(zipEntries(artifactFile,['manifest.json','plan.json','stdout.log','stderr.log','runtime.stdout','runtime.stderr']),unit,inherited);
  requireThat(artifact.runId===measured.runId,'R386_CANVAS_UNIT_OFFICIAL_RUN');
  verifyOfficialRun(measured,'.github/workflows/integration-tests.yml');
  artifact.path=UNIT_DIRECTORY+'/'+unit+'/artifact.zip';
  const receipt={schema:'geometry-canvas-unit-cost/1',unit,legacySha256:legacySha(inherited),artifact,measured};
  return writeImport(root,new Map([[artifact.path,fs.readFileSync(artifactFile)],[UNIT_DIRECTORY+'/'+unit+'.json',encode(receipt)]]),()=>{
    readUnitCosts(root,inherited,[]);return {unit,...measured,acceptance:false,note:'Historical measured cost only; no current browser acceptance is implied.'};});
}
function importSlots(root,{id,artifactFile,artifactId}){
  const current=load(root,{ignorePlacementCandidate:true}),row=current.extensions.find(item=>item.id===id);
  requireThat(row,'R386_CANVAS_MODULE_UNKNOWN',id);requireThat(current.unitCosts[1]&&current.unitCosts[2],'R386_CANVAS_UNIT_COST_REQUIRED');
  const artifact=officialArtifact(artifactFile,artifactId),verified=verifySlotProof(root,id,artifactFile);
  requireThat(artifact.runId===verified.runId,'R386_CANVAS_SLOT_OFFICIAL_RUN');
  verifyOfficialRun(verified,'.github/workflows/canvas-slot-proof.yml',true);
  const directory=SLOT_DIRECTORY+'/'+id+'/'+artifactId,relative=directory+'/receipt.json';artifact.path=directory+'/artifact.zip';
  const receipt=encode({schema:'geometry-canvas-slot-receipt/1',artifact,verified});
  const updated={...row,unit:'auto',balance:{receipt:relative,sha256:sha(receipt)}};
  return writeImport(root,new Map([[artifact.path,fs.readFileSync(artifactFile)],[relative,receipt],[DIRECTORY+'/'+id+'.json',encode(updated)]]),()=>{
    const applied=load(root,{ignorePlacementCandidate:true});return {id,verified,planning:applied.planning,
      acceptance:false,note:'Slot capability admitted; the current merged source still requires its complete full/two-shard checks.'};});
}
function proposeBalance(root=ROOT){
  const current=load(root,{ignorePlacementCandidate:true}),allowed=Object.fromEntries(current.extensions.map(row=>[row.id,[1,2]]));
  const proposal=solvePlacement(current.extensions,current.costs,current.unitCosts,allowed);
  return {schema:'geometry-canvas-balance-proposal/1',sourceSha:gitHead(root),...proposal,acceptance:false,
    admissionRequired:current.extensions.filter(row=>!row.balance).map(row=>row.id),
    modules:current.extensions.map(row=>slotIdentity(root,row.id))};
}
function stageModule(root,id,after=[],before=[]){
  requireThat(/^P[0-9]+$/.test(id)&&floor.sectionOf('=== '+id+'.')===id,'R386_CANVAS_SECTION_ID',id);
  const inherited=archive(root),module=MODULES+'/'+id+'.js',relative=DIRECTORY+'/'+id+'.json';
  requireThat(!inherited.ids.includes(id)&&!fs.existsSync(path.join(root,relative)),'R386_CANVAS_SECTION_ALREADY_EXISTS',id);
  relativeFile(root,module,'R386_CANVAS_MODULE_MISSING');
  const row={schema:SCHEMA,id,assertions:0,unit:2,order:{after,before},execution:{kind:'module',module,export:'default'},
    provenance:{kind:'candidate'},cost:null,balance:null};
  return writeImport(root,new Map([[relative,encode(row)]]),()=>{
    load(root,{allowCandidates:true});return {id,fragment:relative,acceptance:false,
      note:'The generated zero is an unaccepted placeholder. CI measurement and import-cost supply the actual count and elapsed time.'};});
}
function verifyCiSources(root=ROOT,{trustedRef=null}={}){
  requireThat(trustedRef===null||/^[0-9a-f]{40}$/.test(trustedRef),'R386_CANVAS_TRUSTED_REF');
  const registry=load(root),verified=[],inherited=[];
  const paths=registry.extensions.flatMap(row=>[row.cost.receipt,...(row.balance?[row.balance.receipt]:[])])
    .concat(Object.values(registry.unitCosts).map(row=>row.receipt));
  const matchesBase=relative=>{
    if(!trustedRef)return false;
    const run=spawnSync('git',['cat-file','blob',trustedRef+':'+relative],{cwd:root,maxBuffer:128*1024*1024});
    return !run.error&&run.status===0&&run.stdout.equals(fs.readFileSync(relativeFile(root,relative)));
  };
  for(const relative of paths){
    const receipt=readJson(root,relative),artifact=receipt.artifact;
    if(matchesBase(relative)&&matchesBase(artifact.path)){inherited.push({receipt:relative,artifactId:artifact.id,sha256:artifact.sha256});continue;}
    const endpoint='repos/ZhiQiYang/geometry-axiom/actions/artifacts/'+artifact.id;
    const run=spawnSync('gh',['api',endpoint],{encoding:'utf8',maxBuffer:4*1024*1024});
    requireThat(!run.error&&run.status===0,'R386_CANVAS_OFFICIAL_ARTIFACT_API',run.stderr||String(run.error||''));
    const official=parseJson(run.stdout,endpoint);
    requireThat(official.id===artifact.id&&official.digest==='sha256:'+artifact.sha256&&
      String(official.workflow_run?.id)===String(artifact.runId),'R386_CANVAS_OFFICIAL_ARTIFACT_DIGEST',relative);
    if(receipt.schema==='geometry-canvas-slot-receipt/1')verifyOfficialRun(receipt.verified,'.github/workflows/canvas-slot-proof.yml',true);
    else if(receipt.schema==='geometry-canvas-section-cost/1')verifyOfficialRun(receipt.measured,'.github/workflows/canvas-section-measure.yml',true);
    else verifyOfficialRun(receipt.measured,'.github/workflows/integration-tests.yml');
    verified.push({receipt:relative,artifactId:artifact.id,sha256:artifact.sha256});
  }
  return {verified_online:verified,inherited_from_base:inherited,trusted_base:trustedRef,status:'verified'};
}
module.exports={ROOT,PLAN,GOLDEN,DIRECTORY,MODULES,META,ARCHIVE_PLAN,ARCHIVE_GOLDEN,SCHEMA,sha,lf,stable,encode,parseJson,
  requireThat,migrate,load,loadPlan,loadGolden,legacyView,dispatch,createSectionTimer,verifyMeasurement,importCost,verifyCiSources,
  slotIdentity,slotMetadata:slotIdentity,verifySlotRun,verifySlotProof,solvePlacement,placementCandidate,runSlotIsolation,restoreStorageExpression,
  STORAGE_EXPRESSION,PROTOCOL_FILES,importUnitCost,importSlots,proposeBalance,stageModule,sourceClosure,moduleSourceHash};
if(require.main===module){
  try{
    const [mode,...args]=process.argv.slice(2),options={};for(let at=0;at<args.length;at++){
      requireThat(args[at].startsWith('--'),'R386_CANVAS_ARGUMENT');const name=args[at].slice(2);
      if(name==='verify-ci'){options[name]=true;if(args[at+1]==='true')at++;}else{requireThat(args[at+1]!==undefined,'R386_CANVAS_ARGUMENT');options[name]=args[++at];}}
    const root=path.resolve(options.root||ROOT);let result;
    if(mode==='migrate')result=migrate(root,{baseSha:options['base-sha'],outdir:options.outdir});
    else if(mode==='check'||mode==='report'){const registry=load(root);result={schema:registry.schema,sections:registry.fragments.length,
      assertions:registry.golden.total,units:registry.plan.shards.map(row=>({index:row.index,sections:row.sections.length})),
      planSha256:registry.planSha256,goldenSha256:registry.goldenSha256,declarations_complete:registry.acceptance,
      data_contract_verified:registry.acceptance,acceptance:false,
      planning:registry.planning,...(options['verify-ci']?{ciSources:verifyCiSources(root,{trustedRef:options['trusted-ref']||null})}:{})};}
    else if(mode==='golden')result=loadGolden(root);
    else if(mode==='plan')result=loadPlan(root);
    else if(mode==='import-cost')result=importCost(root,{id:options.id,artifactFile:options.artifact,artifactId:options['artifact-id']});
    else if(mode==='import-unit-cost')result=importUnitCost(root,{unit:Number(options.unit),artifactFile:options.artifact,artifactId:options['artifact-id']});
    else if(mode==='import-slots')result=importSlots(root,{id:options.id,artifactFile:options.artifact,artifactId:options['artifact-id']});
    else if(mode==='placement-candidate')result=placementCandidate(root,options.id,Number(options.unit),options.out);
    else if(mode==='propose-balance')result=proposeBalance(root);
    else if(mode==='stage-module')result=stageModule(root,options.id,options.after?options.after.split(','):[],options.before?options.before.split(','):[]);
    else throw Error('Use migrate, check, report, golden, plan, import-cost, import-unit-cost, placement-candidate, import-slots or propose-balance');
    process.stdout.write(encode(result));
  }catch(error){process.stderr.write(String(error.message)+'\n');process.exitCode=1;}
}
