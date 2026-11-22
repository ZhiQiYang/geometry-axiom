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
/* R445: reviewed independent CDP driver sections. A driver is NOT a module:
 * it may use fs/ZIP/new processes, so it is admitted only through this closed,
 * source-reviewed allowlist (this file is pinned by the architecture exclusion
 * and tests/registry-source-reviews). A fragment can only restate an entry; it
 * cannot name another file, flag, command, slot or helper set.
 * Trust level (7072484935 X1): this allowlist and its checker live in the same
 * PR-editable file; the source review only recomputes hashes. The real defence
 * for a change here is the human review of the diff. */
const DRIVER_SECTIONS=Object.freeze({
  P2052:Object.freeze({
    driver:'geometry-web/framing_template_jig_workflow_test.js',
    flag:'GEOMETRY_FRAMING_JIG_ONLY',unit:2,after:'P205',before:'P353',
    assertions:Object.freeze(['ENTRY','VERSION2_SCOPE','SOURCES_BLANK','SAVE_INTENT','V1_RETAINED','READ_VERSION','POLICY_REQUEST',
      'ORACLE_F4_FIXED','MARKS','PREVIEW_TABLE','PREVIEW_ZERO','CANCEL_ZERO','NEW_TOKEN','CONFIRM_SAME_CANDIDATE','LIVE_DEFINITIONS',
      'UNDO','REDO','REJECT_ZERO','VERSION1_STILL_REJECTS','NARROW_LAYOUT','WIDE_LAYOUT','SAVE_FILE','FRESH_CONTEXT','COLD_EXACT',
      'COLD_NO_SEARCH','WRONG_V2_POLICY','UNKNOWN_VERSION','NO_EXCEPTIONS']),
    /* Exact cdp_test.js text: the P205 statement, its closing brace and the
       single P2052 statement. The helper set passed to the driver is part of it. */
    dispatch:["  if(inSequence(2)||process.env.GEOMETRY_FRAMING_TEMPLATE_ONLY)",
      "    await require('./framing_template_workflow_test.js')({send,eval_,sleep,click,dblclick,waitForUI,exceptionCount:()=>excN});",
      "  } // FRAMING_JIG_ONLY owns only P2052; the complete v1 P205 path is unchanged.",
      "  if(inSequence(2)||process.env.GEOMETRY_FRAMING_JIG_ONLY)",
      "    await require('./framing_template_jig_workflow_test.js')({send,eval_,sleep,click,dblclick,waitForUI,exceptionCount:()=>excN});",
      ""].join('\n'),
    /* R445 (7072803590 item 2): the statement that must directly follow the
       P2052 dispatch in the same block (the P353 dispatch). */
    following:["  if(inSequence(2)||process.env.GEOMETRY_GRID_CARD_ENTRY_ONLY)",
      "    await require('./grid_card_entry_test.js')({send,eval_,sleep,click,waitForUI,expectNativeDialog,exceptionCount:()=>excN});",
      ""].join('\n'),
    guard:'  if (!process.env.GEOMETRY_FRAMING_JIG_ONLY) {\n',
    closure:Object.freeze(['geometry-core/framing-template/oracle/oracle-golden.json','geometry-web/cdp_bay_repeat_io.js',
      'geometry-web/cdp_helpers.js','geometry-web/framing_template_jig_workflow_test.js','geometry-web/vendor/fflate/umd/index.js']),
    builtins:Object.freeze(['child_process','crypto','fs','net','os','path','util']),
    vendor:Object.freeze({'geometry-web/vendor/fflate/umd/index.js':Object.freeze(['worker_threads'])}),
    processProperties:Object.freeze(['env','kill','platform']),
    /* R445 (7072803590 item 1): like strict modules, a computed member must be
       a literal; the only exceptions are these reviewed sites, each pinned by
       its exact text and the SHA-256 of its innermost enclosing function. */
    computed:Object.freeze({
      "geometry-web/framing_template_jig_workflow_test.js":Object.freeze([
        "first.members[i]@9c5c862d4da971c729241b07fafa8f7de081b4eadd15f6e4fb80ae55a48e9d9e",
        "first.members[i]@9c5c862d4da971c729241b07fafa8f7de081b4eadd15f6e4fb80ae55a48e9d9e",
        "first.members[i]@9c5c862d4da971c729241b07fafa8f7de081b4eadd15f6e4fb80ae55a48e9d9e",
        "first.members[i]@9c5c862d4da971c729241b07fafa8f7de081b4eadd15f6e4fb80ae55a48e9d9e"]),
      "geometry-web/cdp_helpers.js":Object.freeze([
        "retained[i]@9699819b9ad0ef0dd41f5630505bea7aa235e974bddf47600e731c633d7781c5",
        "process.env[n]@c85612ec549d9df59f1161a106bf90b3cc56002fc28e9843d4f2ae95e5f6f092",
        "CARD_NATIVE_LIST[kind]@806397ce2276cea0751b89b7a463c451174b99f17fc6e5c987cdf01e405884e7"]),
      "geometry-web/cdp_bay_repeat_io.js":Object.freeze([
        "attributes[at+1]@fb01ddd3ea80128fae5ddc66ca697b44deb3b5ca10c8b2a69a97f52bc9b56f9b"])}),
    /* R445: child_process is reachable only through this one reviewed import;
       every call of spawn/spawnSync/ownedSpawn must be one of these exact sites
       (text + innermost enclosing function SHA-256). The scripts those sites
       execute are hashed into the driver identity (see driverIdentity). */
    subprocess:Object.freeze({file:'geometry-web/cdp_bay_repeat_io.js',
      import:"const {spawn,spawnSync}=require('node:child_process');",
      callees:Object.freeze(['ownedSpawn','spawn','spawnSync']),wrapper:'ownedSpawn',
      sites:Object.freeze([
        "spawnSync('taskkill',['/PID',String(child.pid),'/T','/F'],{stdio:'ignore'})@da8e245b68c6266c3f99b88a61b2f5fef46171ea1913c1e944ccd019179718d8",
        "spawn(executable,args,{cwd:ROOT,detached:process.platform!=='win32',stdio:['ignore','pipe','pipe'],...options})@5034bbb8d37169547239c393e3251bc624332fc89a1478312ae50151a027fae4",
        "spawnSync(python,['-B','-c',script,ROOT,configured],{cwd:ROOT,encoding:'utf8',timeout:30000})@7475d4b5be865c4750c6a64489782ffc6d3589dd4e0a0ae193b6980572feb8c6",
        "ownedSpawn(python,['-B',path.join(__dirname,'serve.py'),String(port)],{env:{...process.env,\n    GEOMETRY_BRIDGE_EXECUTABLE:record.path,GEOMETRY_FEEDBACK_DIR:feedback,GEOMETRY_ISOLATED_SERVICE:'1'}})@b4df205f98c5a3185a8ab313ceac2c40fa0d910f1a03e84d3133129ddb69a367",
        "ownedSpawn(process.env.GEOMETRY_CHROME||'C:\\\\Program Files\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe',[\n     '--headless=new','--disable-gpu','--no-first-run','--remote-debugging-port=0','--window-size=1280,900',\n     '--user-data-dir='+profile,...(process.env.GEOMETRY_CHROME_FLAGS||'').split(' ').filter(Boolean),'about:blank'])@b4df205f98c5a3185a8ab313ceac2c40fa0d910f1a03e84d3133129ddb69a367"]),
      scripts:Object.freeze(['geometry-web/serve.py','geometry-web/start_local.py','tests/binaries.py'])}),
    outputs:Object.freeze({saved:/^saved-[0-9]+\.gcanvas$/,cold:/^cold-[0-9]+\.json$/,coldFinal:/^cold-final-[0-9]+\.json$/,
      fixed:Object.freeze(['unknown-v2-generator.gcanvas','wrong-v2-policy.gcanvas'])}),
    artifactEnv:'GEOMETRY_FRAMING_JIG_ARTIFACT_DIR',
  }),
});
const DRIVER_MEASUREMENT_SCHEMA='geometry-canvas-driver-measurement/2',DRIVER_OUTPUTS='driver-outputs';
const DRIVER_RECEIPT_FILES=Object.freeze(['process-ledger.json','runtime.stderr','runtime.stdout','stderr.log','stdout.log']);
const DRIVER_LEDGER_SCHEMA='geometry-driver-process-ledger/1';
const DRIVER_COMMAND=Object.freeze(['node','geometry-web/cdp_test.js']);
function driverEntry(id){requireThat(typeof id==='string'&&Object.hasOwn(DRIVER_SECTIONS,id),'R386_CANVAS_DRIVER_UNREVIEWED',String(id));return DRIVER_SECTIONS[id];}
function driverDeclaration(id){const entry=driverEntry(id);
  return {unit:entry.unit,order:{anchor:{after:entry.after,before:entry.before}},execution:{kind:'driver',driver:entry.driver,flag:entry.flag}};}
function parseScript(raw,relative){
  if(!acorn){const native=process.binding('natives')['internal/deps/acorn/acorn/dist/acorn'];
    requireThat(typeof native==='string','R386_CANVAS_SOURCE_PARSER');acorn={};require('node:vm').runInNewContext(native,{exports:acorn,module:{exports:acorn}});}
  return acorn.parse(raw.toString('utf8'),{ecmaVersion:'latest',sourceType:relative.endsWith('.mjs')?'module':'script',allowReturnOutsideFunction:true});
}
const DRIVER_BANNED_IDS=Object.freeze(['eval','Function','AsyncFunction','GeneratorFunction','AsyncGeneratorFunction','WebAssembly','global','globalThis','Reflect','Proxy']);
const DRIVER_BANNED_PROPS=Object.freeze(['constructor','__proto__','createRequire','mainModule','binding','_linkedBinding','dlopen','_load','_resolveFilename',
  'getPrototypeOf','setPrototypeOf','__defineGetter__','__defineSetter__','__lookupGetter__','__lookupSetter__',
  'getOwnPropertyDescriptor','getOwnPropertyDescriptors','getOwnPropertyNames','getOwnPropertySymbols','defineProperty','defineProperties',...DRIVER_BANNED_IDS]);
/* Constant value of a string-literal expression ('a', `a`, 'a'+'b'); null otherwise. */
function constantString(node){
  if(node?.type==='Literal'&&typeof node.value==='string')return node.value;
  if(node?.type==='TemplateLiteral'&&node.expressions.length===0)return node.quasis.map(quasi=>quasi.value.cooked).join('');
  if(node?.type==='BinaryExpression'&&node.operator==='+'){const left=constantString(node.left),right=constantString(node.right);
    return left!==null&&right!==null?left+right:null;}
  return null;
}
/* Every node with its ancestor chain; scope = SHA-256 of the innermost
 * enclosing function's LF source (or 'program'). */
function walkWithScope(tree,source,visit){
  const stack=[];
  const step=(node,parent,scope)=>{
    if(!node||typeof node!=='object')return;
    if(['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression'].includes(node.type))scope=sha(Buffer.from(source.slice(node.start,node.end)));
    visit(node,parent,scope,stack);stack.push(node);
    for(const value of Object.values(node))if(Array.isArray(value)){for(const item of value)if(item&&typeof item==='object')step(item,node,scope);}
      else if(value&&typeof value==='object'&&typeof value.type==='string')step(value,node,scope);
    stack.pop();
  };
  step(tree,null,'program');
}
const countSet=items=>{const counts={};for(const item of items)counts[item]=(counts[item]||0)+1;return counts;};
/* Driver-mode closure: every dependency must be a literal, resolvable path
 * inside the root or a listed builtin; loaders, reflection, dynamic members,
 * pattern-extracted reflective keys and unreviewed subprocess sites are
 * rejected. The resulting file SET must equal the reviewed entry; bytes go
 * into the hash. */
function driverClosure(root,id){
  const entry=driverEntry(id),hashes={},pending=[entry.driver],builtins=new Set(entry.builtins);
  const bannedIds=new Set(DRIVER_BANNED_IDS),bannedProps=new Set(DRIVER_BANNED_PROPS);
  const literal=node=>node?.type==='Literal'&&typeof node.value==='string'?node.value:null;
  const computedSeen={},sitesSeen=[];
  while(pending.length){
    const relative=pending.pop();if(Object.hasOwn(hashes,relative))continue;
    const file=relativeFile(root,relative,'R386_CANVAS_DRIVER_CLOSURE_MISSING'),raw=lf(fs.readFileSync(file));hashes[relative]=sha(raw);
    if(!/\.(?:js|cjs|mjs)$/.test(relative))continue;
    const vendor=Object.hasOwn(entry.vendor,relative)?new Set(entry.vendor[relative]):null,dependencies=[];
    const source=raw.toString('utf8'),tree=parseScript(raw,relative),text=node=>source.slice(node.start,node.end);
    const subprocessFile=relative===entry.subprocess.file;let importNode=null;
    if(!vendor)for(const statement of tree.body)if(statement.type==='VariableDeclaration'&&text(statement)===entry.subprocess.import)
      {requireThat(subprocessFile&&!importNode,'R386_CANVAS_DRIVER_SUBPROCESS',relative+' import');importNode=statement;}
    if(subprocessFile)requireThat(importNode!==null,'R386_CANVAS_DRIVER_SUBPROCESS',relative+' import missing');
    const inside=(node,outer)=>outer&&node.start>=outer.start&&node.end<=outer.end;
    const childProcess=name=>name.replace(/^node:/,'')==='child_process';
    walkWithScope(tree,source,(node,parent,scope,ancestors)=>{
      if(node.type==='CallExpression'&&node.callee?.type==='Identifier'&&node.callee.name==='require'){
        const name=node.arguments.length===1?literal(node.arguments[0]):null;
        requireThat(name!==null,'R386_CANVAS_DRIVER_CLOSURE_DYNAMIC',relative);dependencies.push(name);
        if(childProcess(name))requireThat(!vendor&&inside(node,importNode),'R386_CANVAS_DRIVER_SUBPROCESS',relative+' '+text(node));
      }
      if(node.type==='ImportExpression'){const name=literal(node.source);requireThat(name!==null,'R386_CANVAS_DRIVER_CLOSURE_DYNAMIC',relative);dependencies.push(name);
        requireThat(!childProcess(name),'R386_CANVAS_DRIVER_SUBPROCESS',relative+' '+text(node));}
      if(['ImportDeclaration','ExportNamedDeclaration','ExportAllDeclaration'].includes(node.type)&&node.source){
        const name=literal(node.source);requireThat(name!==null,'R386_CANVAS_DRIVER_CLOSURE_DYNAMIC',relative);dependencies.push(name);
        requireThat(!childProcess(name),'R386_CANVAS_DRIVER_SUBPROCESS',relative+' '+text(node));}
      if(vendor)return;
      const value=node.type==='Literal'||node.type==='TemplateLiteral'?constantString(node):null;
      if(value!==null&&!(parent?.type==='Property'&&parent.key===node&&!parent.computed&&ancestors.at(-2)?.type==='ObjectExpression'))
        requireThat(!bannedProps.has(value),'R386_CANVAS_DRIVER_CLOSURE_REFLECTIVE',relative+' '+JSON.stringify(value));
      if(node.type==='Identifier'){
        const asKey=parent&&(parent.type==='Property'&&parent.key===node&&!parent.computed&&parent.value!==node||
          parent.type==='MemberExpression'&&parent.property===node&&!parent.computed);
        if(!asKey){
          requireThat(!bannedIds.has(node.name),'R386_CANVAS_DRIVER_CLOSURE_REFLECTIVE',relative+' '+node.name);
          if(node.name==='require')requireThat(parent?.type==='CallExpression'&&parent.callee===node,'R386_CANVAS_DRIVER_CLOSURE_INDIRECT',relative);
          if(node.name==='module')requireThat(parent?.type==='UnaryExpression'&&parent.operator==='typeof'||
            parent?.type==='MemberExpression'&&parent.object===node&&!parent.computed&&parent.property.name==='exports','R386_CANVAS_DRIVER_CLOSURE_INDIRECT',relative);
          if(node.name==='process')requireThat(parent?.type==='MemberExpression'&&parent.object===node&&!parent.computed&&
            entry.processProperties.includes(parent.property.name),'R386_CANVAS_DRIVER_PROCESS_CAPABILITY',relative);
          if(entry.subprocess.callees.includes(node.name)&&!inside(node,importNode)&&
            !(subprocessFile&&parent?.type==='FunctionDeclaration'&&parent.id===node&&node.name===entry.subprocess.wrapper&&ancestors.length===2)){
            requireThat(parent?.type==='CallExpression'&&parent.callee===node,'R386_CANVAS_DRIVER_SUBPROCESS',relative+' '+node.name);
            sitesSeen.push(relative+'|'+text(parent)+'@'+scope);
          }
        }
      }
      /* process.env is read-only: a member read or an object spread, never a
         write, delete, alias or argument (env injects into pinned children). */
      if(node.type==='MemberExpression'&&node.object?.type==='Identifier'&&node.object.name==='process'&&!node.computed&&node.property.name==='env'){
        const grand=ancestors.at(-2),member=parent?.type==='MemberExpression'&&parent.object===node;
        const write=member&&(grand?.type==='AssignmentExpression'&&grand.left===parent||grand?.type==='UpdateExpression'&&grand.argument===parent||
          grand?.type==='UnaryExpression'&&grand.operator==='delete'&&grand.argument===parent||
          grand?.type==='Property'&&grand.value===parent&&ancestors.at(-3)?.type==='ObjectPattern'||grand?.type==='ArrayPattern'||
          grand?.type==='AssignmentPattern'&&grand.left===parent||grand?.type==='RestElement'&&grand.argument===parent||
          ['ForInStatement','ForOfStatement'].includes(grand?.type)&&grand.left===parent);
        requireThat((parent?.type==='MemberExpression'&&parent.object===node||parent?.type==='SpreadElement')&&!write,
          'R386_CANVAS_DRIVER_PROCESS_CAPABILITY',relative+' process.env');
      }
      if(node.type==='MemberExpression'){
        if(node.computed){
          const key=constantString(node.property),numeric=node.property.type==='Literal'&&typeof node.property.value==='number';
          if(key!==null)requireThat(!bannedProps.has(key),'R386_CANVAS_DRIVER_CLOSURE_REFLECTIVE',relative+' '+key);
          else if(!numeric){const site=text(node)+'@'+scope;computedSeen[relative]=computedSeen[relative]||[];computedSeen[relative].push(site);
            requireThat((entry.computed[relative]||[]).includes(site),'R386_CANVAS_DRIVER_CLOSURE_DYNAMIC_PROPERTY',relative+' '+text(node));}
          requireThat(!(node.object.type==='Identifier'&&['process','module','require','exports'].includes(node.object.name)),
            'R386_CANVAS_DRIVER_CLOSURE_DYNAMIC_PROPERTY',relative);
        }else requireThat(!bannedProps.has(node.property.name),'R386_CANVAS_DRIVER_CLOSURE_REFLECTIVE',relative+' '+node.property.name);
      }
      /* Destructuring is a property read: {constructor:F}=fn and {[k]:F}=fn. */
      if(node.type==='Property'&&parent?.type==='ObjectPattern'){
        const key=node.computed?constantString(node.key):node.key.type==='Identifier'?node.key.name:literal(node.key);
        requireThat(key!==null,'R386_CANVAS_DRIVER_CLOSURE_DYNAMIC_PROPERTY',relative+' '+text(node));
        requireThat(!bannedProps.has(key),'R386_CANVAS_DRIVER_CLOSURE_REFLECTIVE',relative+' '+key);
      }
    });
    for(const name of [...new Set(dependencies)].sort()){
      if(!name.startsWith('.')){
        const bare=name.replace(/^node:/,'');
        requireThat(nodeModule.builtinModules.includes(bare)&&(vendor?vendor.has(bare):builtins.has(bare)),'R386_CANVAS_DRIVER_BUILTIN',relative+' '+name);continue;}
      requireThat(!vendor,'R386_CANVAS_DRIVER_VENDOR_LEAF',relative+' '+name);
      let target;try{target=nodeModule.createRequire(file).resolve(name);}catch{requireThat(false,'R386_CANVAS_DRIVER_CLOSURE_MISSING',relative+' '+name);}
      const rel=path.relative(path.resolve(root),target).split(path.sep).join('/');
      requireThat(!rel.startsWith('../')&&!path.isAbsolute(rel)&&/\.(?:js|cjs|mjs|json)$/.test(rel),'R386_CANVAS_DEPENDENCY_OUTSIDE_ROOT',name);pending.push(rel);
    }
  }
  const files=Object.fromEntries(Object.entries(hashes).sort());
  requireThat(same(Object.keys(files),[...entry.closure]),'R386_CANVAS_DRIVER_CLOSURE_SET',JSON.stringify(Object.keys(files)));
  /* The reviewed lists are exact: no extra site, and no silently dropped one. */
  for(const relative of new Set([...Object.keys(computedSeen),...Object.keys(entry.computed)]))
    requireThat(same(countSet(computedSeen[relative]||[]),countSet(entry.computed[relative]||[])),'R386_CANVAS_DRIVER_CLOSURE_DYNAMIC_PROPERTY',relative+' reviewed set');
  requireThat(same(countSet(sitesSeen),countSet(entry.subprocess.sites.map(site=>entry.subprocess.file+'|'+site))),'R386_CANVAS_DRIVER_SUBPROCESS','reviewed site set');
  return files;
}
/* The scripts that the pinned subprocess sites execute. Their own repo-local
 * imports are part of the runtime fingerprint (see FRAGMENTED-REGISTRIES.md). */
function driverScripts(root,entry){
  return Object.fromEntries([...entry.subprocess.scripts].sort().map(relative=>
    [relative,sha(lf(fs.readFileSync(relativeFile(root,relative,'R386_CANVAS_DRIVER_SUBPROCESS'))))]));
}
/* The 28 names are read statically from the authored driver; it is never run here. */
function driverAssertionNames(root,entry){
  const raw=lf(fs.readFileSync(relativeFile(root,entry.driver,'R386_CANVAS_DRIVER_CLOSURE_MISSING'))),tree=parseScript(raw,entry.driver),found=[];
  for(const statement of tree.body)if(statement.type==='VariableDeclaration')for(const item of statement.declarations){
    if(item.id?.type!=='Identifier'||item.id.name!=='ASSERTIONS')continue;
    const init=item.init;
    requireThat(init?.type==='CallExpression'&&init.callee?.type==='MemberExpression'&&init.callee.object?.name==='Object'&&
      init.callee.property?.name==='freeze'&&init.arguments.length===1&&init.arguments[0].type==='ArrayExpression'&&
      init.arguments[0].elements.every(element=>element?.type==='Literal'&&typeof element.value==='string'),'R386_CANVAS_DRIVER_ASSERTIONS','literal');
    found.push(init.arguments[0].elements.map(element=>element.value));
  }
  requireThat(found.length===1,'R386_CANVAS_DRIVER_ASSERTIONS','declaration count '+found.length);return found[0];
}
function countText(text,part){let count=0,at=0;while((at=text.indexOf(part,at))>=0){count++;at+=part.length;}return count;}
/* R445 (7072803590 item 2): "dispatched exactly once" is an AST fact. Every
 * require()/import() whose literal module path normalizes to the driver is
 * counted (any quoting, with or without extension); every string constant
 * naming the driver stem is counted; the one dispatch must sit in the reviewed
 * block: after the guard block ending in P205, before the reviewed P353 statement. */
function driverDispatch(root,entry){
  const relative='geometry-web/cdp_test.js',raw=lf(fs.readFileSync(relativeFile(root,relative,'R386_CANVAS_DRIVER_DISPATCH'))),text=raw.toString('utf8');
  requireThat(countText(text,entry.dispatch)===1,'R386_CANVAS_DRIVER_DISPATCH','statement');
  requireThat(countText(text,entry.guard)===1,'R386_CANVAS_DRIVER_DISPATCH','guard');
  const scope=text.split('\n').filter(line=>line.startsWith('SCOPE_FLAGS.push(')&&line.includes("'"+entry.flag+"'"));
  requireThat(scope.length===1&&countText(text,"'"+entry.flag+"'")===1,'R386_CANVAS_DRIVER_SCOPE_FLAG',entry.flag);
  let tree;try{tree=parseScript(raw,relative);}catch(error){requireThat(false,'R386_CANVAS_DRIVER_DISPATCH','parse '+error.message);}
  const directory=path.posix.dirname(relative),driver=entry.driver,stem=path.posix.basename(driver).replace(/\.[cm]?js$/,'');
  const normalized=name=>{if(!name.startsWith('.'))return null;const joined=path.posix.normalize(path.posix.join(directory,name));
    return [joined,joined+'.js',joined+'.cjs',joined+'/index.js'].includes(driver)?driver:joined;};
  const dispatches=[],named=[],source=node=>text.slice(node.start,node.end);
  walkWithScope(tree,text,(node,parent,scope,ancestors)=>{
    const loader=node.type==='CallExpression'&&node.callee?.type==='Identifier'&&node.callee.name==='require'?node.arguments[0]:
      node.type==='ImportExpression'?node.source:null;
    if(loader){const name=constantString(loader);if(name!==null&&normalized(name)===driver)dispatches.push({node,ancestors:[...ancestors]});}
    if(node.type==='TemplateElement'&&(node.value.cooked||'').includes(stem))named.push(node);
    else{const value=constantString(node);if(value!==null&&node.type==='Literal'&&value.includes(stem))named.push(node);}
  });
  requireThat(dispatches.length===1,'R386_CANVAS_DRIVER_DISPATCH','driver loaded '+dispatches.length+' times');
  requireThat(named.length===1&&named[0]===dispatches[0].node.arguments[0],'R386_CANVAS_DRIVER_DISPATCH','driver named '+named.length+' times');
  /* Structure: await require(<driver>)({...}) as the sole consequent of the
     reviewed `if`, directly inside a block, between the reviewed neighbours. */
  const chain=dispatches[0].ancestors,at=offset=>chain.at(-offset);
  const call=at(1),awaited=at(2),statement=at(3),branch=at(4),block=at(5);
  const strip=value=>value.replace(/^\s+/,'').replace(/\n$/,'');
  const lines=entry.dispatch.split('\n');
  requireThat(call?.type==='CallExpression'&&call.callee===dispatches[0].node&&awaited?.type==='AwaitExpression'&&
    statement?.type==='ExpressionStatement'&&branch?.type==='IfStatement'&&branch.consequent===statement&&!branch.alternate&&
    block?.type==='BlockStatement'&&strip(source(branch))===strip(lines.slice(3,5).join('\n')),'R386_CANVAS_DRIVER_DISPATCH','structure');
  const index=block.body.indexOf(branch),previous=block.body[index-1],next=block.body[index+1];
  requireThat(previous?.type==='IfStatement'&&strip(source(previous.test))==='!process.env.'+entry.flag&&previous.consequent?.type==='BlockStatement'&&
    strip(source(previous.consequent.body.at(-1)||{start:0,end:0}))===strip(lines.slice(0,2).join('\n')),'R386_CANVAS_DRIVER_DISPATCH','previous');
  requireThat(next&&strip(source(next))===strip(entry.following),'R386_CANVAS_DRIVER_DISPATCH','following');
  return sha(entry.dispatch);
}
function driverIdentity(root,id){
  const entry=driverEntry(id),files=driverClosure(root,id),dispatchSha256=driverDispatch(root,entry),scripts=driverScripts(root,entry);
  requireThat(same(driverAssertionNames(root,entry),[...entry.assertions]),'R386_CANVAS_DRIVER_ASSERTIONS','names');
  const reviewed={driver:entry.driver,flag:entry.flag,unit:entry.unit,after:entry.after,before:entry.before,assertions:[...entry.assertions],
    dispatch:entry.dispatch,following:entry.following,guard:entry.guard,closure:[...entry.closure],builtins:[...entry.builtins],vendor:entry.vendor,
    processProperties:[...entry.processProperties],computed:entry.computed,subprocess:entry.subprocess,command:[...DRIVER_COMMAND],
    bannedIds:[...DRIVER_BANNED_IDS],bannedProps:[...DRIVER_BANNED_PROPS]};
  const entrySha256=sha(stable(reviewed));
  return {id,driver:entry.driver,flag:entry.flag,files,scripts,dispatchSha256,entrySha256,
    sha256:sha(stable({id,files,scripts,dispatchSha256,entrySha256}))};
}
function driverSourceHash(root,id){return driverIdentity(root,id).sha256;}
const ZIP_READER='import sys,json,zipfile,base64,io\nz=zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read()) if sys.argv[1]=="-" else sys.argv[1])\nr={}\nt=0\nfor i in z.infolist():\n if i.is_dir(): continue\n n=i.filename\n assert n not in r and not n.startswith("/") and ".." not in n.split("/") and ((i.external_attr>>16)&0o170000)!=0o120000 and i.file_size<=16777216, "unsafe, duplicate or oversized driver original"\n t+=i.file_size\n assert t<=67108864, "driver artifact too large"\n r[n]=base64.b64encode(z.read(i)).decode()\nprint(json.dumps(r))';
function zipAll(file,{input=null,code='R386_CANVAS_COST_ZIP'}={}){
  const run=spawnSync(process.env.PYTHON||'python3',['-c',ZIP_READER,input===null?file:'-'],{encoding:'utf8',input:input===null?undefined:input,maxBuffer:128*1024*1024});
  requireThat(!run.error&&run.status===0,code,run.stderr||String(run.error||''));
  return Object.fromEntries(Object.entries(parseJson(run.stdout)).map(([name,value])=>[name,Buffer.from(value,'base64')]));
}
/* R445 F4: the saved archive is a real .gcanvas, carrying both recipe versions. */
function driverArchive(raw,code){
  requireThat(Buffer.isBuffer(raw)&&raw.length>0,code,'empty');
  const members=zipAll(null,{input:raw,code});
  requireThat(same(Object.keys(members).sort(),['manifest.json','world.scene']),code,'members '+JSON.stringify(Object.keys(members)));
  let manifest;try{manifest=JSON.parse(members['manifest.json'].toString('utf8'));}catch{requireThat(false,code,'manifest');}
  requireThat(manifest&&typeof manifest==='object'&&/^geometry-canvas\/[0-9]+$/.test(manifest.format||'')&&manifest.sceneHash===sha(members['world.scene']),code,'format/sceneHash');
  const records=(manifest.featureAttachments?.records||[]).filter(record=>record?.kind==='framing-template-recipes');
  requireThat(manifest.featureAttachments?.schema==='geometry-feature-attachments/1'&&records.length===1&&Array.isArray(records[0].value?.recipes),code,'recipes');
  const versions=records[0].value.recipes.map(recipe=>recipe?.template?.version);
  requireThat(versions.filter(version=>version===1).length>=1&&versions.filter(version=>version===2).length===1,code,'versions '+JSON.stringify(versions));
  return {members,manifest};
}
/* R445 F3: each tampered archive is the saved one with exactly the driver's edit. */
function driverTampered(saved,raw,name){
  const code='R386_CANVAS_DRIVER_TAMPERED';
  requireThat(Buffer.isBuffer(raw)&&raw.length>0&&!raw.equals(saved.raw),code,name+' empty or unchanged');
  const members=zipAll(null,{input:raw,code});
  requireThat(same(Object.keys(members).sort(),Object.keys(saved.members).sort())&&members['world.scene'].equals(saved.members['world.scene']),code,name+' members');
  let actual;try{actual=JSON.parse(members['manifest.json'].toString('utf8'));}catch{requireThat(false,code,name+' manifest');}
  const expected=structuredClone(saved.manifest),recipe=expected.featureAttachments.records.find(record=>record.kind==='framing-template-recipes')
    .value.recipes.find(item=>item.template.version===2);
  if(name==='wrong-v2-policy.gcanvas')recipe.template.policyFingerprint='0'.repeat(64);
  else{recipe.template.version=999;recipe.template.policyFingerprint='f'.repeat(64);}
  requireThat(same(actual,expected)&&!same(actual,saved.manifest),code,name+' edit');
}
/* R445 F1: the cold service and Chrome must be processes that the measuring
 * script itself observed under cdp_test.js (not only the driver's own words). */
function driverLedger(ledger,pkg,info,runtime){
  const code='R386_CANVAS_DRIVER_COLD_OPEN';
  requireThat(ledger?.schema===DRIVER_LEDGER_SCHEMA&&same(ledger.root?.argv,[...DRIVER_COMMAND])&&Number.isSafeInteger(ledger.root?.pid)&&
    Array.isArray(ledger.processes),code,'ledger');
  const byPid=new Map();for(const item of ledger.processes){requireThat(Number.isSafeInteger(item?.pid)&&Number.isSafeInteger(item?.ppid)&&
    Array.isArray(item.argv)&&item.argv.every(arg=>typeof arg==='string'),code,'ledger row');byPid.set(item.pid,[...(byPid.get(item.pid)||[]),item]);}
  const descends=item=>{const seen=new Set();for(let at=item;at;){if(at.ppid===ledger.root.pid)return true;if(seen.has(at.pid))return false;seen.add(at.pid);
    const parents=byPid.get(at.ppid)||[];if(parents.length!==1)return false;at=parents[0];}return false;};
  const only=(pid,match,label)=>{const rows=(byPid.get(pid)||[]).filter(item=>descends(item)&&match(item.argv));
    requireThat(rows.length===1&&(byPid.get(pid)||[]).length===1,code,'ledger '+label);};
  const port=new URL(info.url).port;
  only(pkg.nativeService.pid,argv=>argv.length>=3&&argv.includes('-B')&&/(?:^|\/)geometry-web\/serve\.py$/.test(argv.at(-2))&&argv.at(-1)===port,'cold service');
  only(pkg.browserPid,argv=>argv.includes('--user-data-dir='+pkg.profile)&&argv.includes('--remote-debugging-port=0'),'cold chrome');
  requireThat(!(byPid.get(runtime.pid)||[]).some(descends)&&runtime.pid!==ledger.root.pid,code,'ledger source service');
}
function verifyDriverMeasurement(members,row,identity){
  const entry=driverEntry(row.id),manifest=parseJson(members['manifest.json']||'null','manifest.json');
  exactKeys(manifest,['schema','execution_sha','head_sha','tree','run_id','run_attempt','id','driver','driver_sha256','dispatch_sha256','flag',
    'command','process_exit','runtime_fresh','runtime_version','capture_verified','acceptance','files','outputs'],'R386_CANVAS_DRIVER_RECEIPT_KEYS');
  requireThat(manifest.schema===DRIVER_MEASUREMENT_SCHEMA&&manifest.capture_verified===true&&manifest.acceptance===false,'R386_CANVAS_COST_CAPTURE');
  requireThat(/^[0-9a-f]{40}$/.test(manifest.execution_sha||'')&&/^[0-9a-f]{40}$/.test(manifest.head_sha||'')&&
    /^[0-9a-f]{40}$/.test(manifest.tree||'')&&/^\d+$/.test(manifest.run_id||'')&&/^\d+$/.test(manifest.run_attempt||''),'R386_CANVAS_COST_CI_IDENTITY');
  requireThat(manifest.process_exit===0&&manifest.id===row.id&&manifest.driver===entry.driver&&manifest.flag===entry.flag&&
    manifest.driver_sha256===identity.sha256&&manifest.dispatch_sha256===identity.dispatchSha256,'R386_CANVAS_COST_SOURCE');
  requireThat(same(manifest.command,DRIVER_COMMAND)&&manifest.runtime_fresh===true,'R386_CANVAS_COST_COMMAND');
  exactKeys(manifest.files,[...DRIVER_RECEIPT_FILES],'R386_CANVAS_COST_RAW_HASH');
  for(const [name,digest] of Object.entries(manifest.files))requireThat(members[name]&&sha(members[name])===digest,'R386_CANVAS_COST_RAW_HASH',name);
  const outputs=Object.keys(members).filter(name=>name.startsWith(DRIVER_OUTPUTS+'/')).sort();
  requireThat(same(Object.keys(members).sort(),['manifest.json',...DRIVER_RECEIPT_FILES,...outputs].sort()),'R386_CANVAS_ZIP_FILE_SET');
  requireThat(manifest.outputs&&typeof manifest.outputs==='object'&&same(Object.keys(manifest.outputs).sort(),outputs)&&
    outputs.every(name=>manifest.outputs[name]===sha(members[name])),'R386_CANVAS_DRIVER_OUTPUT_HASH');
  const runtime=parseJson(members['runtime.stdout'],'runtime.stdout');
  requireThat(runtime.schema==='geometry-runtime/1'&&runtime.fresh===true&&runtime.version===manifest.runtime_version&&
    Number.isSafeInteger(runtime.pid)&&typeof runtime.session==='string'&&runtime.session&&typeof runtime.root==='string','R386_CANVAS_COST_COMMAND');
  const lines=members['stdout.log'].toString('utf8').split(/\r?\n/),results=lines.filter(line=>line.startsWith('CDP_RESULT '));
  requireThat(results.length===1,'R386_CANVAS_COST_RESULT_COUNT');
  const result=parseJson(results[0].slice('CDP_RESULT '.length),'CDP_RESULT');
  requireThat(result.schema==='geometry-cdp-result/1'&&result.completed===true&&result.failedAssertions===0&&
    same(result.skipped,[])&&!result.sectionsFailed&&result.unexpectedBrowserExceptions===0&&result.scope?.mode==='partial'&&
    same(result.scope.filters,[entry.flag])&&same(result.scope.modifiers,[])&&!Object.hasOwn(result.scope,'module')&&
    result.goldenCompare==='not compared (partial mode)','R386_CANVAS_DRIVER_PARTIAL_RESULT');
  requireThat(same(result.sectionOrder,[row.id])&&same(Object.keys(result.sections||{}),[row.id])&&
    result.sections[row.id]===result.passedAssertions&&result.sections[row.id]===entry.assertions.length&&result.sections[row.id]===row.assertions,
    'R386_CANVAS_COST_COUNT');
  requireThat(same(Object.keys(result.sectionElapsedMs||{}),[row.id])&&Number.isFinite(result.sectionElapsedMs[row.id])&&result.sectionElapsedMs[row.id]>0,
    'R386_CANVAS_COST_TIMING');
  /* Same 28 named checks, really executed once each in this one run. */
  const verdicts=lines.map((line,index)=>[line.match(/^(\S+) ([A-Z0-9_]+) ([✓✗])(?: |$)/),index]).filter(([match])=>match&&match[1]===row.id);
  const passed=verdicts.filter(([match])=>match[3]==='✓').map(([match])=>match[2]);
  requireThat(verdicts.every(([match])=>match[3]==='✓')&&passed.length===entry.assertions.length&&
    same([...passed].sort(),[...entry.assertions].sort()),'R386_CANVAS_DRIVER_NAMED_CHECKS',JSON.stringify(passed));
  const tagged=tag=>lines.flatMap((line,index)=>line.startsWith(tag+' ')?[[parseJson(line.slice(tag.length+1),tag),index]]:[]);
  const scope=tagged('R03A_BROWSER_SCOPE');
  requireThat(scope.length===1&&scope[0][0].schema==='framing-template-jig-browser-scope/1'&&scope[0][0].assertions===entry.assertions.length,'R386_CANVAS_DRIVER_SCOPE_LINE');
  const packages=tagged('R03A_BROWSER_PACKAGE');
  requireThat(packages.length===1,'R386_CANVAS_DRIVER_COLD_OPEN','package');
  /* R445 F2: one run's log shape: CDP_SCOPE (= the result scope) < the section
     header < every named check < SCOPE line < CDP_RESULT, PACKAGE inside. */
  const scopes=tagged('CDP_SCOPE'),headers=lines.flatMap((line,index)=>line.startsWith('=== '+row.id+'. ')?[index]:[]);
  const resultIndex=lines.indexOf(results[0]),first=Math.min(...verdicts.map(([,index])=>index)),last=Math.max(...verdicts.map(([,index])=>index));
  requireThat(scopes.length===1&&same(scopes[0][0],result.scope)&&headers.length===1&&scopes[0][1]<headers[0]&&headers[0]<first&&
    last<scope[0][1]&&headers[0]<packages[0][1]&&packages[0][1]<scope[0][1]&&scope[0][1]<resultIndex,'R386_CANVAS_DRIVER_LOG_STRUCTURE');
  /* Cold open: a new native service/session and a new Chrome process/profile
   * reopened the exact archived bytes; both tampered archives exist. */
  const folders=[...new Set(outputs.map(name=>name.split('/').slice(0,2).join('/')))];
  requireThat(folders.length===1,'R386_CANVAS_DRIVER_COLD_OPEN','package/folder');
  const names=outputs.map(name=>name.slice(folders[0].length+1)),pkg=packages[0][0];
  const saved=names.filter(name=>entry.outputs.saved.test(name)),cold=names.filter(name=>entry.outputs.cold.test(name));
  const final=names.filter(name=>entry.outputs.coldFinal.test(name)),known=[...saved,...cold,...final];
  requireThat(saved.length===1&&cold.length===1&&final.length===1&&same(names.filter(name=>!known.includes(name)).sort(),[...entry.outputs.fixed]),
    'R386_CANVAS_DRIVER_COLD_OPEN','outputs');
  const archive=members[folders[0]+'/'+saved[0]],info=parseJson(members[folders[0]+'/'+cold[0]],'cold');
  const closing=parseJson(members[folders[0]+'/'+final[0]],'cold-final');
  requireThat(same(closing.info,info)&&closing.end?.pid===info.service?.pid&&closing.end?.session===info.service?.session&&
    Array.isArray(closing.errors)&&closing.errors.length===0,'R386_CANVAS_DRIVER_COLD_OPEN','close');
  requireThat(pkg.sha256===sha(archive)&&pkg.bytes===archive.length&&Number.isSafeInteger(pkg.browserPid)&&pkg.browserPid>0&&
    pkg.nativeService?.pid!==pkg.sourceService?.pid&&pkg.nativeService?.session!==pkg.sourceService?.session&&
    pkg.nativeService?.fresh===true&&pkg.nativeService?.version===pkg.sourceService?.version&&typeof pkg.profile==='string'&&pkg.profile&&
    same(info.service,pkg.nativeService)&&same(info.sourceRuntime,pkg.sourceService)&&info.browserPid===pkg.browserPid&&info.profile===pkg.profile,
    'R386_CANVAS_DRIVER_COLD_OPEN','identity');
  /* R445 F1: bind the driver's words to the measuring script's own probe:
     the source service IS the probed service, the cold one runs the probed
     source version under the same root, and both cold processes are in the
     measuring script's own process ledger under cdp_test.js. */
  requireThat(same(pkg.sourceService,runtime)&&pkg.nativeService.version===manifest.runtime_version&&pkg.nativeService.root===runtime.root&&
    pkg.nativeService.schema===runtime.schema&&Number.isSafeInteger(scopes[0][0].browserPid)&&scopes[0][0].browserPid!==pkg.browserPid,
    'R386_CANVAS_DRIVER_COLD_OPEN','runtime');
  driverLedger(parseJson(members['process-ledger.json'],'process-ledger.json'),pkg,info,runtime);
  /* R445 F4/F3: the saved file is a real .gcanvas; each tampered file is it with exactly the driver's one edit. */
  const savedArchive={raw:archive,...driverArchive(archive,'R386_CANVAS_DRIVER_ARCHIVE')};
  for(const name of entry.outputs.fixed)driverTampered(savedArchive,members[folders[0]+'/'+name],name);
  return {assertions:result.sections[row.id],milliseconds:result.sectionElapsedMs[row.id],runId:manifest.run_id,attempt:manifest.run_attempt,
    executionSha:manifest.execution_sha,headSha:manifest.head_sha};
}
function verifyDriverRow(root,row,inherited){
  const declared=driverDeclaration(row.id);
  for(const key of ['unit','order','execution'])requireThat(same(row[key],declared[key]),'R386_CANVAS_DRIVER_UNREVIEWED',row.id+' '+key);
  const entry=driverEntry(row.id),legacy=inherited.plan.shards.find(unit=>unit.index===entry.unit).sections;
  requireThat(!inherited.ids.includes(row.id)&&legacy.indexOf(entry.after)>=0&&legacy[legacy.indexOf(entry.after)+1]===entry.before,'R386_CANVAS_DRIVER_ANCHOR',row.id);
  if(row.cost===null){
    exactKeys(row.provenance,['kind'],'R386_CANVAS_MODULE_PROVENANCE_KEYS');
    requireThat(row.provenance.kind==='candidate'&&row.assertions===0,'R386_CANVAS_DRIVER_CANDIDATE',row.id);
  }else{
    exactKeys(row.provenance,['kind','executionSha','headSha','runId','attempt'],'R386_CANVAS_MODULE_PROVENANCE_KEYS');
    requireThat(row.provenance.kind==='ci-capture'&&row.assertions===entry.assertions.length,'R386_CANVAS_DRIVER_ASSERTIONS',row.id);
  }
  return driverIdentity(root,row.id);
}
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
  let measured;
  if(row.execution.kind==='driver')measured=verifyDriverMeasurement(zipAll(zip),row,moduleHash);/* moduleHash is the driver identity here */
  else{const members=zipMembers(zip),manifest=parseJson(members['manifest.json'],'manifest.json');
    measured=verifyMeasurement(manifest,members['stdout.log'],members['stderr.log'],row,moduleHash);}
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
  const sourceFiles=[META,ARCHIVE_PLAN,ARCHIVE_GOLDEN,...files],modules=[],drivers=[],costs={},allowed={};
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
    }else if(row.execution?.kind==='driver'||Object.hasOwn(DRIVER_SECTIONS,row.id)){
      /* Reviewed driver: only an exact restatement of DRIVER_SECTIONS. */
      exactKeys(row.execution,['kind','driver','flag'],'R386_CANVAS_DRIVER_UNREVIEWED');
      const identity=verifyDriverRow(root,row,inherited);
      sourceFiles.push(...Object.keys(identity.files),'geometry-web/cdp_test.js');
      if(allowCandidates&&!row.cost){acceptance=false;}
      else costs[row.id]=verifyCost(root,row,identity,sourceFiles);
      drivers.push(row);
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
  for(const row of [...drivers].sort((a,b)=>a.id<b.id?-1:1)){
    const entry=driverEntry(row.id),sections=plan.shards[entry.unit-1].sections,at=sections.indexOf(entry.after);
    requireThat(at>=0&&sections[at+1]===entry.before,'R386_CANVAS_DRIVER_ANCHOR',row.id);sections.splice(at+1,0,row.id);
  }
  plan.shards[0].sections.push(...extensions.filter(row=>assignment[row.id]===1).map(row=>row.id));
  plan.shards[1].sections.splice(plan.shards[1].sections.length-1,0,...extensions.filter(row=>assignment[row.id]===2).map(row=>row.id));
  plan.boundaries[0].after=plan.shards[0].sections.at(-1);
  for(const row of drivers){
    const entry=driverEntry(row.id),owners=plan.shards.map(unit=>unit.sections.filter(id=>id===row.id).length);
    requireThat(same(owners,plan.shards.map(unit=>unit.index===entry.unit?1:0)),'R386_CANVAS_DRIVER_OWNER',row.id);
    const sections=plan.shards[entry.unit-1].sections,at=sections.indexOf(row.id);
    requireThat(same(sections.slice(at-1,at+2),[entry.after,row.id,entry.before]),'R386_CANVAS_DRIVER_ORDER',row.id);
  }
  requireThat(plan.shards[1].sections.at(-1)==='P359'&&plan.shards[0].sections[0]===inherited.plan.shards[0].sections[0],'R386_CANVAS_TERMINAL_SLOT');
  if(extensions.some(row=>row.unit==='auto'))plan.registryPlanning=planning;
  for(const key of Object.keys(golden.sections))golden.sections[key]=fragments.find(row=>row.id===key).assertions;
  for(const row of [...drivers,...extensions])golden.sections[row.id]=row.assertions;
  golden.total=Object.values(golden.sections).reduce((sum,count)=>sum+count,0);
  return {schema:'geometry-canvas-registry/1',root,plan,golden,fragments,extensions,drivers,sourceFiles:[...new Set(sourceFiles)].sort(),acceptance,
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
  const registry=load(root,{allowCandidates:true}),row=registry.extensions.find(item=>item.id===id)||registry.drivers.find(item=>item.id===id);
  requireThat(row,'R386_CANVAS_MODULE_UNKNOWN',id);
  requireThat(/^\d+$/.test(String(artifactId)),'R386_CANVAS_COST_ARTIFACT');
  const driver=row.execution.kind==='driver';
  const endpoint='repos/ZhiQiYang/geometry-axiom/actions/artifacts/'+artifactId;
  const api=spawnSync('gh',['api',endpoint],{encoding:'utf8',maxBuffer:4*1024*1024});
  requireThat(!api.error&&api.status===0,'R386_CANVAS_OFFICIAL_ARTIFACT_API',api.stderr||String(api.error||''));
  const official=parseJson(api.stdout,endpoint),raw=fs.readFileSync(artifactFile),digest=sha(raw);
  requireThat(official.id===Number(artifactId)&&official.expired===false&&official.digest==='sha256:'+digest,'R386_CANVAS_OFFICIAL_ARTIFACT_DIGEST');
  const members=driver?zipAll(artifactFile):zipMembers(artifactFile),manifest=parseJson(members['manifest.json']);
  const moduleHash=driver?driverSourceHash(root,id):moduleSourceHash(root,row.execution.module);
  const actual=parseJson(members['stdout.log'].toString('utf8').split(/\r?\n/).find(line=>line.startsWith('CDP_RESULT '))?.slice(11)||'null');
  const proposed={...row,assertions:actual?.sections?.[id]};
  const measured=driver?verifyDriverMeasurement(members,proposed,driverIdentity(root,id)):
    verifyMeasurement(manifest,members['stdout.log'],members['stderr.log'],proposed,moduleHash);
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
function stageDriver(root,id){
  const entry=driverEntry(id),inherited=archive(root),relative=DIRECTORY+'/'+id+'.json';
  requireThat(!inherited.ids.includes(id)&&!fs.existsSync(path.join(root,relative)),'R386_CANVAS_SECTION_ALREADY_EXISTS',id);
  const row={schema:SCHEMA,id,assertions:0,...driverDeclaration(id),provenance:{kind:'candidate'},cost:null};
  const ordered={schema:row.schema,id:row.id,assertions:row.assertions,unit:row.unit,order:row.order,execution:row.execution,provenance:row.provenance,cost:row.cost};
  return writeImport(root,new Map([[relative,encode(ordered)]]),()=>{
    load(root,{allowCandidates:true});return {id,fragment:relative,driver:entry.driver,acceptance:false,
      note:'Reviewed driver candidate; the zero is a placeholder. Canvas section measurement and import-cost supply the real count, cost and receipt.'};});
}
function verifyCiSources(root=ROOT,{trustedRef=null}={}){
  requireThat(trustedRef===null||/^[0-9a-f]{40}$/.test(trustedRef),'R386_CANVAS_TRUSTED_REF');
  const registry=load(root),verified=[],inherited=[];
  const paths=[...registry.drivers,...registry.extensions].flatMap(row=>[row.cost.receipt,...(row.balance?[row.balance.receipt]:[])])
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
  STORAGE_EXPRESSION,PROTOCOL_FILES,importUnitCost,importSlots,proposeBalance,stageModule,sourceClosure,moduleSourceHash,
  DRIVER_SECTIONS,DRIVER_MEASUREMENT_SCHEMA,DRIVER_RECEIPT_FILES,DRIVER_OUTPUTS,driverClosure,driverIdentity,driverSourceHash,verifyDriverMeasurement,stageDriver};
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
    else if(mode==='stage-driver')result=stageDriver(root,options.id);
    else if(mode==='driver-identity')result=driverIdentity(root,options.id);
    else if(mode==='stage-module')result=stageModule(root,options.id,options.after?options.after.split(','):[],options.before?options.before.split(','):[]);
    else throw Error('Use migrate, check, report, golden, plan, import-cost, import-unit-cost, placement-candidate, import-slots, propose-balance, stage-module, stage-driver or driver-identity');
    process.stdout.write(encode(result));
  }catch(error){process.stderr.write(String(error.message)+'\n');process.exitCode=1;}
}
