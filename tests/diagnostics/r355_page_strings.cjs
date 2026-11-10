'use strict';
/* Syntax audit only; it does not claim browser execution. Literal strings and
 * injected function sources are exact. JSON interpolation uses a serialized
 * representative value; raw data interpolation uses an identifier/number.
 * All finite conditional interpolation branches are expanded. */
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const root=path.resolve(process.argv[2]||path.join(__dirname,'../..'));
const output=path.resolve(process.argv[3]||'/tmp/r355-page-strings.json');
function builtin(name){const m=new Module(name,module);m._compile(process.binding('natives')[name],name);return m.exports;}
const acorn=builtin('internal/deps/acorn/acorn/dist/acorn'),walk=builtin('internal/deps/acorn/acorn-walk/dist/walk');
const files=['geometry-web/cdp_test.js','geometry-web/panel_fill_workflow_test.js'];
const out={node:process.version,scope:'changed CDP driver and R02 browser module; compile-only, no browser execution; representative values for runtime data interpolation',files,checked:[],forwarded:[],external:[],failures:[]};
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
for(const file of out.files){const source=fs.readFileSync(path.join(root,file),'utf8'),ast=acorn.parse(source,{ecmaVersion:'latest',locations:true}),declarations=new Map();
 const add=(n,v)=>{if(!declarations.has(n))declarations.set(n,[]);declarations.get(n).push(v);};
 walk.simple(ast,{VariableDeclarator(n){if(n.id.type==='Identifier'&&n.init)add(n.id.name,n.init);},FunctionDeclaration(n){if(n.id)add(n.id.name,n);}});
 const raw=n=>source.slice(n.start,n.end),callName=n=>n.type==='Identifier'?n.name:n.type==='MemberExpression'?(n.computed?n.property.value:n.property.name):'';
 function resolve(n,depth=0){
  if(!n||depth>8)return null;
  if(n.type==='MemberExpression'&&raw(n)==='shards.SNAPSHOT_EXPRESSION')return [{text:require(path.join(root,'geometry-web/canvas_shards.js')).SNAPSHOT_EXPRESSION,mode:'literal'}];
  if(n.type==='Literal'&&typeof n.value==='string')return [{text:n.value,mode:'literal'}];
  if(['ArrowFunctionExpression','FunctionExpression','FunctionDeclaration'].includes(n.type))return [{text:'('+raw(n)+')',mode:'function-source'}];
  if(n.type==='Identifier'){
   const all=declarations.get(n.name)||[],candidate=all.filter(x=>x.end<=n.start).at(-1)||all.find(x=>x!==n);
   return candidate?resolve(candidate,depth+1):null;
  }
  if(n.type==='ConditionalExpression'){const a=resolve(n.consequent,depth+1),b=resolve(n.alternate,depth+1);return a&&b?[...a,...b]:null;}
  if(n.type==='TemplateLiteral'){
   let results=[{text:n.quasis[0].value.cooked,mode:n.expressions.length?'template-values':'literal'}];
   for(let i=0;i<n.expressions.length;i++){
    const e=n.expressions[i],values=interpolation(e,depth+1);
    results=results.flatMap(r=>values.map(v=>({text:r.text+v+n.quasis[i+1].value.cooked,mode:r.mode})));
   }
   return results;
  }
  if(n.type==='BinaryExpression'&&n.operator==='+'){
   const part=x=>resolve(x,depth+1)||(x.type==='Identifier'?[{text:'__PAGE_AUDIT_VALUE__',mode:'template-values'}]:x.type==='Literal'?[{text:String(x.value),mode:'template-values'}]:null);
   const a=part(n.left),b=part(n.right);return a&&b?a.flatMap(x=>b.map(y=>({text:x.text+y.text,mode:x.mode==='literal'&&y.mode==='literal'?'literal':'template-values'}))):null;
  }
  if(n.type==='CallExpression'&&n.callee.type==='Identifier'&&n.callee.name==='phase'&&n.arguments.length===1&&n.arguments[0].type==='Literal'){
   const fn=(declarations.get('phase')||[]).find(x=>x.type==='ArrowFunctionExpression'&&x.body.type==='TemplateLiteral');
   if(fn&&fn.params.length===1&&fn.body.expressions.length===1&&fn.body.expressions[0].name===fn.params[0].name)
    return [{text:fn.body.quasis[0].value.cooked+String(n.arguments[0].value)+fn.body.quasis[1].value.cooked,mode:'literal'}];
  }
  if(n.type==='CallExpression'&&n.callee.type==='MemberExpression'){
   if(raw(n.callee)==='shards.applyExpression'){
    const shard=require(path.join(root,'geometry-web/canvas_shards.js'));
    return [{text:shard.applyExpression(shard.materializeStorage(shard.loadPlan().boundaries[0].localStorage,'audit-current-token')),mode:'template-values'}];
   }
   if(callName(n.callee)==='toString'){
    if(raw(n.callee.object)==='installClientTransportTrace')return [{text:require(path.join(root,'geometry-web/transport_failure_trace.js')).installClientTransportTrace.toString(),mode:'function-source'}];
    return resolve(n.callee.object,depth+1)?.map(r=>({...r,text:r.text.slice(1,-1)}))||null;
   }
   if(callName(n.callee)==='replace'){
    const inputs=resolve(n.callee.object,depth+1),needle=n.arguments[0]?.value,replacement=interpolation(n.arguments[1],depth+1);
    if(inputs&&typeof needle==='string')return inputs.flatMap(r=>replacement.map(s=>({...r,text:r.text.replace(needle,s)})));
   }
   if(raw(n.callee)==='JSON.stringify')return [{text:'"audit-value"',mode:'template-values'}];
  }
  return null;
 }
 function interpolation(e,depth){
  if(e.type==='Literal')return [String(e.value)];
  if(e.type==='ConditionalExpression')return [...new Set([...interpolation(e.consequent,depth+1),...interpolation(e.alternate,depth+1)])];
  if(e.type==='CallExpression'&&raw(e.callee)==='JSON.stringify')return ['"audit-value"'];
  if(e.type==='CallExpression'&&callName(e.callee)==='toString'){const r=resolve(e,depth+1);if(r)return r.map(x=>x.text);}
  if(e.type==='Identifier'&&['unchanged','visibleState'].includes(e.name)){const r=resolve(e,depth+1);if(r)return r.map(x=>x.text);return ['null'];}
  // Value fragments may occur inside a string, after '.', or as an expression.
  return ['__PAGE_AUDIT_VALUE__'];
 }
 function compile(n,call){const variants=resolve(n);
  const info={file,line:call.loc.start.line,argumentLine:n.loc.start.line,callee:callName(call.callee),source:raw(n)};
  if(!variants){if(n.type==='Identifier'&&['adapter','ownerAdapter'].includes(n.name))out.external.push({...info,reason:'optional external adapter not selected or read'});else out.forwarded.push(info);return;}
  for(const [i,v] of variants.entries()){
   try{const asyncWrapped=/\bawait\b/.test(v.text);if(v.mode==='function-source')new Function('return '+v.text);else if(asyncWrapped)new Function('return (async function(){\n'+v.text+'\n});');else new Function(v.text);out.checked.push({...info,variant:i,mode:v.mode,asyncWrapped});}
   catch(error){out.failures.push({...info,variant:i,mode:v.mode,error:String(error),expanded:v.text});}
  }
 }
 walk.simple(ast,{CallExpression(n){const name=callName(n.callee);if(['read','eval_','evaluate','ev','page','wait','waitForUI','waitForFunction','subgridRead','until','ready'].includes(name)){
   const index=name==='wait'&&file==='geometry-web/timber_reuse_test.js'?1:0;
   if(n.arguments[index])compile(n.arguments[index],n);
  }
  if(name==='captureNewToasts'&&n.arguments[1])compile(n.arguments[1],n);
  if(name==='send'&&['Runtime.evaluate','Page.addScriptToEvaluateOnNewDocument'].includes(n.arguments[0]?.value)&&n.arguments[1]?.type==='ObjectExpression'){
   const key=n.arguments[0].value==='Runtime.evaluate'?'expression':'source';
   const expression=n.arguments[1].properties.find(p=>p.key?.name===key||p.key?.value===key);if(expression)compile(expression.value,n);
  }
 }});
}
fs.writeFileSync(output,JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify({files:out.files.length,checked:out.checked.length,modes:out.checked.reduce((a,r)=>(a[r.mode]=(a[r.mode]||0)+1,a),{}),forwarded:out.forwarded.map(({file,line,source})=>({file,line,source})),external:out.external.map(({file,line})=>({file,line})),failures:out.failures.map(({file,line,error,source})=>({file,line,error,source}))},null,2));
process.exitCode=out.failures.length?1:0;
