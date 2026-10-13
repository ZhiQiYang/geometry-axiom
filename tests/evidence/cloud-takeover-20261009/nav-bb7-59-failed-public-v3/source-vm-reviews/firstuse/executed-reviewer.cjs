'use strict';
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto'),vm=require('node:vm');
const ROOT='<workspace-path>',OUT=__dirname;
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex'),digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const git=a=>cp.execFileSync('git',a,{cwd:ROOT,encoding:'utf8'}).trim();
const before={head:git(['rev-parse','HEAD']),dirty:git(['status','--porcelain'])};
const original=cp.execFileSync('git',['show','59c736066a97ca044c3a47c0ecdcb5245a59efab:tests/issue123_caption_browser.cjs'],{cwd:ROOT,encoding:'utf8'});
const current=fs.readFileSync(path.join(ROOT,'tests/issue123_caption_browser.cjs'),'utf8');
const builtin=process.binding('natives')['internal/deps/acorn/acorn/dist/acorn'];const moduleCopy={exports:{}};new Function('exports','module',builtin)(moduleCopy.exports,moduleCopy);const acorn=moduleCopy.exports;
const parse=s=>acorn.parse(s,{ecmaVersion:'latest',sourceType:'script'});
const oldAST=parse(original),newAST=parse(current),checks=[];
const check=(name,ok,detail)=>checks.push({name,ok:ok===true,...(detail===undefined?{}:{detail})});
const clean=n=>JSON.parse(JSON.stringify(n,(k,v)=>['start','end','loc','range'].includes(k)?undefined:v));
const fn=(ast,name)=>ast.body.find(n=>n.type==='FunctionDeclaration'&&n.id.name===name);
const oldEntry=fn(oldAST,'enterFace'),newEntry=fn(newAST,'enterFace');const entry=current.slice(newEntry.start,newEntry.end);
check('root held final7ee bytes exact',digest(current)==='7ee40cb53fb1f561d0e7d33282b641bc3a4850f8cbdc9fa6105994bd3d43d765');
check('old executed01355 remains exact Git original',digest(original)==='01355f60d7a7a817f99a58ab088cf1a4609c020d94ba93fc0c325392b6754252');
check('exact final patch40c7 identity',sha(path.join(OUT,'first-use-normal-entry.patch'))==='40c7d1b7f4a9d99134842afcce44a63e1c2de7ae2814aa1445c908e898572b0d');
check('every Program AST node except entry unchanged',JSON.stringify(clean(oldAST.body.filter(n=>n!==oldEntry)))===JSON.stringify(clean(newAST.body.filter(n=>n!==newEntry))));
check('original entry dblclick/wait/settle AST retained as exact final three steps',JSON.stringify(clean(oldEntry.body.body))===JSON.stringify(clean(newEntry.body.body.slice(-3))));
function walk(n,f){if(!n||typeof n!=='object')return;f(n);for(const v of Object.values(n))if(Array.isArray(v))v.forEach(x=>walk(x,f));else if(v&&typeof v==='object')walk(v,f);}
const callChecks=ast=>{const a=[];walk(ast,n=>{if(n.type==='CallExpression'&&n.callee.type==='Identifier'&&n.callee.name==='check')a.push(n);});return a;};
const oldCalls=callChecks(oldAST),newCalls=callChecks(newAST),addedNames=['initial canvas lesson has one normal reachable dismissal','normal first-use dismissal hides lesson and preserves exact native source'];
const originalNewCalls=newCalls.filter(n=>!addedNames.includes(n.arguments[0]?.value));
check('all original73 check AST bodies/order exact; only2 positive additions',oldCalls.length===73&&newCalls.length===75&&JSON.stringify(clean(oldCalls))===JSON.stringify(clean(originalNewCalls)),{old:oldCalls.length,new:newCalls.length});
check('new checks exact unique positive names',addedNames.every(name=>newCalls.filter(n=>n.arguments[0]?.value===name).length===1));
check('entry conditional visible existing lesson and one normal click; no retries/force/DOMpatch',newEntry.body.body[0].declarations[0].init.value==='#ocSelectionSummary [data-guidance-dismiss]'&&!/force|while\s*\(|for\s*\(|\.focus\(|dispatchEvent|preventDefault|setAttribute|\.hidden\s*=|localStorage|\bapi\(/.test(entry)&&entry.match(/await click\(lesson\)/g).length===1);
const actualRead=[];walk(newEntry,n=>{if(n.type==='CallExpression'&&n.callee.name==='read')actualRead.push(n.arguments[0]);});
check('one readonly measurement expression',actualRead.length===1);
const template=actualRead[0];let expression='';for(let i=0;i<template.quasis.length;i++){expression+=template.quasis[i].value.cooked;if(i<template.expressions.length){check('measurement interpolation is only fixed lesson identifier',template.expressions[i].type==='Identifier'&&template.expressions[i].name==='lesson');expression+='#ocSelectionSummary [data-guidance-dismiss]';}}
parse(expression);check('embedded page expression parses under real JS parser',true);
check('measurement includes uniqueness and real center hit without mutation',expression.includes('document.querySelectorAll')&&expression.includes('document.elementFromPoint')&&!/\.click\(|dispatchEvent|setAttribute|\.remove\(|\.hidden\s*=|append|replaceChildren/.test(expression));
const commentOld='// Added standalone scope. Existing six group bodies, helpers and footer stay exact.';
const commentNew='// Standalone scope retains the six group bodies and footer; face entry normally dismisses the existing first-use lesson.';
const reconstructedF608=current.replace(commentNew,commentOld);
check('f608 intermediate is recoverable by comment-only inverse',digest(reconstructedF608)==='f6088fc82085f663e39bbd1ee0d61da4c1ad38fc9191094f12ab084353dff176');
fs.writeFileSync(path.join(OUT,'first-use-f608-reconstructed-unexecuted.cjs'),reconstructedF608);
check('finalcomment describes retained bodies/footer and new premise truthfully',current.includes(commentNew));
check('exact patch equals only entry replacement and truth comment',current.replace(entry,original.slice(oldEntry.start,oldEntry.end)).replace(commentNew,commentOld)===original);
check('seven widths/fixture/source/footer block bytes unchanged',current.slice(current.indexOf('if(!equal(requested'))===original.slice(original.indexOf('if(!equal(requested')));
check('all product/SIX/floor/golden untouched',sha(path.join(ROOT,'geometry-web/app.js'))==='b68832bfd7e48a6c370e2ba64152511944b9aba085d0870397c1b1743dd08227'&&sha(path.join(ROOT,'tests/issue123_adopted_slices_browser.cjs'))==='6efba5412916a31df431c557a7893019f186bf8adc3fa15aa059098367e272d1'&&sha(path.join(ROOT,'geometry-web/cdp_floor.js'))==='01a45d7881d583a7d328e579b457c959baa2b8d3570c3e3fbe66e8781c5f679e'&&sha(path.join(ROOT,'geometry-web/cdp_sections.golden.json'))==='e3e742ec3d731e701afc22149efa9bc11cf6506340715176175e594c94778bd9');

function measurement({count=1,hit=true,width=44,height=44}={}){
 const e={getBoundingClientRect:()=>({left:10,top:10,width,height}),contains:x=>x===e};
 const doc={querySelectorAll:selector=>{if(selector!=='#ocSelectionSummary [data-guidance-dismiss]')throw Error('foreign selector');return Array(count).fill(e);},elementFromPoint:()=>hit?e:null};
 return vm.runInNewContext(expression,{document:doc});
}
check('measurement zero element safely rejects',measurement({count:0}).count===0&&measurement({count:0}).hit===false);
for(const [name,options] of [['duplicate',{count:2}],['occluded',{hit:false}],['zero width',{width:0}],['zero height',{height:0}],['negative width',{width:-1}]]){
 const r=measurement(options);check('positive premise rejects '+name,!(r.count===1&&r.hit&&r.width>0&&r.height>0),r);
}
async function exercise(options={}){
 const o={visible:true,hideAfter:true,nativeSame:true,...options};let dismissed=false,reads=0;const actions=[],predicates=[];
 const env={visible:async()=>!dismissed?o.visible:!o.hideAfter,dump:async()=>{reads++;return dismissed&&!o.nativeSame?'changed full original scene':'exact original full scene';},
  read:async s=>{if(s!==expression)throw Error('measurement source changed');return measurement(o);},
  check:(name,ok)=>{predicates.push({name,ok:ok===true});if(!ok)throw Error(name);},
  click:async(...a)=>{actions.push({action:'click',args:a});dismissed=true;},
  page:{locator:s=>({dblclick:async(...a)=>actions.push({action:'dblclick',selector:s,args:a})})},
  wait:async s=>actions.push({action:'wait',expression:s}),settle:async()=>actions.push({action:'settle'})};
 const run=vm.runInNewContext('('+entry+')',env);let rejected=false;try{await run();}catch(_){rejected=true;}
 return {actions,predicates,reads,rejected};
}
(async()=>{
 let r=await exercise();check('normal visible lesson dismissed exactly once then original card doubleclick',!r.rejected&&r.actions.filter(a=>a.action==='click').length===1&&r.actions[0].args.length===1&&r.actions[0].args[0]==='#ocSelectionSummary [data-guidance-dismiss]'&&r.actions[1].action==='dblclick'&&r.actions[1].selector==='.ocard[data-kind="boundary"][data-id="1"]'&&r.actions[1].args.length===0&&r.reads===2,r);
 check('normal premise verifies hidden and full native source equal before card',r.predicates.length===2&&r.predicates.every(x=>x.ok),r);
 r=await exercise({visible:false});check('already dismissed lesson stays untouched; original card path exact',!r.rejected&&r.reads===0&&r.predicates.length===0&&r.actions[0].action==='dblclick'&&r.actions.length===3,r);
 for(const [name,options] of [['duplicate',{count:2}],['occluded',{hit:false}],['zero rect',{width:0}],['fails to close',{hideAfter:false}],['native changes',{nativeSame:false}]]){
  r=await exercise(options);check('workflow rejects '+name+' before card action',r.rejected&&!r.actions.some(a=>a.action==='dblclick'),r);
 }
 const syntax=cp.spawnSync(process.execPath,['--check',path.join(ROOT,'tests/issue123_caption_browser.cjs')],{encoding:'utf8'});check('actual finaltest Node syntax',syntax.status===0,syntax.stderr);
 const after={head:git(['rev-parse','HEAD']),dirty:git(['status','--porcelain'])};check('only root-owned pending test dirty beforeafter; reviewer repo unchanged',JSON.stringify(after)===JSON.stringify(before)&&before.head==='59c736066a97ca044c3a47c0ecdcb5245a59efab'&&before.dirty==='M tests/issue123_caption_browser.cjs');
 const log=path.join(OUT,'first-use-final7ee-static-review.log');fs.writeFileSync(log,checks.map(r=>(r.ok?'PASS ':'FAIL ')+r.name).join('\n')+'\n');
 const report={schema:'geometry-caption-first-use-source-review/1',checkedUTC:new Date().toISOString(),executor:{path:process.execPath,sha256:sha(process.execPath),version:process.version,command:[process.execPath,...process.execArgv,...process.argv.slice(1)],scriptSHA256:sha(__filename),parser:{origin:'Node bundled internal Acorn',version:acorn.version,builtinSourceSHA256:digest(builtin)}},before,after,
  originalExecutedSource:{fullSHA:'59c736066a97ca044c3a47c0ecdcb5245a59efab',path:'tests/issue123_caption_browser.cjs',sha256:digest(original)},reviewedUncommittedSource:{path:path.join(ROOT,'tests/issue123_caption_browser.cjs'),sha256:digest(current)},
  patch:{path:path.join(OUT,'first-use-normal-entry.patch'),sha256:sha(path.join(OUT,'first-use-normal-entry.patch'))},checks,passed:checks.filter(r=>r.ok).length,failed:checks.filter(r=>!r.ok).length,total:checks.length,rawLog:log,rawLogSHA256:sha(log),
  browserExecuted:false,productWritten:false,formalTestWritten:false,productAcceptanceClaim:false,
  limits:['Only AST/isolated DOM/workflow counterexamples; native API and browser/trusted pointer are not run','Actual7width acceptance requires new committed frozen sourceSHA with final7ee identity;01355 original59 failure stays228/1','f608 intermediate reconstructed by exactcomment inverse is expressly unexecuted; it is not a receipt of the executed01355 bytes']};
 const p=path.join(OUT,'first-use-final7ee-static-review.json');fs.writeFileSync(p,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:report.passed,failed:report.failed,total:report.total,receipt:p,sha256:sha(p),rawLogSHA256:sha(log)}));process.exitCode=report.failed?1:0;
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
