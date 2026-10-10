'use strict';
// Source and parser review only; never requires Playwright or product code.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto'),cp=require('node:child_process');
const OUT=__dirname,ROOT='<workspace-path>',BASE='c0f05baade2424482fab94c72f0592f7b02326ae';
const native=process.binding('natives')['internal/deps/acorn/acorn/dist/acorn'];
const module_={exports:{}};vm.runInNewContext(native,{module:module_,exports:module_.exports});
const parse=s=>module_.exports.parse(s,{ecmaVersion:'latest',sourceType:'script'});
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const target=path.join(OUT,'issue123_s2_supplemental_browser.cjs'),base=path.join(OUT,'../supplement-f980/issue123_supplemental_browser.cjs');
const old=fs.readFileSync(base,'utf8'),source=fs.readFileSync(target,'utf8'),a=parse(old),b=parse(source),checks=[];
function check(name,ok,detail){checks.push({name,ok:ok===true,...(detail===undefined?{}:{detail})});}
const literal=s=>{const start=s.indexOf('const groups={');return s.slice(start,s.indexOf('\n};',start)+3);};
check('all six original group methods remain byte identical',literal(old)===literal(source));
for(const f of a.body.filter(n=>n.type==='FunctionDeclaration')){const found=b.body.find(n=>n.type==='FunctionDeclaration'&&n.id.name===f.id.name);check('original helper bytes retained '+f.id.name,!!found&&old.slice(f.start,f.end)===source.slice(found.start,found.end));}
const assignments=ast=>ast.body.filter(n=>n.type==='ExpressionStatement'&&n.expression.type==='CallExpression'&&n.expression.callee.object?.name==='Object'&&n.expression.callee.property?.name==='assign'&&n.expression.arguments[0]?.name==='groups');
const prior=assignments(a),after=assignments(b);
check('existing plan bom row-blur group methods remain byte identical',prior.length===1&&after.length===2&&old.slice(prior[0].start,prior[0].end)===source.slice(after[0].start,after[0].end));
check('S2 has one independent explicit additional scope',after[1]?.expression.arguments[1].properties.length===1&&after[1].expression.arguments[1].properties[0].key.name==='s2'&&source.includes("GEOMETRY_UI123_GROUPS||'s2'"));
check('original final receipt and failure logic retained byte identical',source.endsWith(old.slice(old.indexOf('(async()=>{let completed=false;try{'))));
check('no forced pointer action or disabled Chromium sandbox',!(/force\s*:\s*true|--no-sandbox|--disable-setuid-sandbox/.test(source))&&source.includes('chromiumSandbox:true'));
check('sources include new shared helper and both consumers',source.includes("'geometry-web/grid-inspector.js','geometry-web/grid-anchor-positions.js'"));
check('strict clean full-SHA and source-freeze guards retained',source.includes("run.head===EXPECTED&&run.dirty===''" )&&source.includes('sourcePaths.every(p=>sha(path.join(ROOT,p))===run.sources[p])'));
const expressions=[];
function walk(n,fn){if(!n||typeof n!=='object')return;fn(n);for(const v of Object.values(n)){if(Array.isArray(v))for(const c of v)walk(c,fn);else if(v&&typeof v==='object')walk(v,fn);}}
walk(b,n=>{if(n.type!=='CallExpression'||!['read','wait'].includes(n.callee.name))return;const v=n.arguments[0];if(v?.type==='TemplateLiteral')expressions.push(v.quasis.map(q=>q.value.cooked).join('0'));else if(v?.type==='Literal'&&typeof v.value==='string')expressions.push(v.value);});
const parsed=expressions.map((s,index)=>{try{parse(s);return {index,ok:true};}catch(error){return {index,ok:false,error:error.message,source:s};}});
check('all embedded page observation expressions parse',parsed.every(r=>r.ok),{count:parsed.length,failed:parsed.filter(r=>!r.ok)});
const group=source.slice(after[1].start,after[1].end);
check('canonical fixture includes disclosed actual outer and hole plus custom thirds',group.includes('hole 100,200 100,600 700,600 700,200')&&group.includes('cell -2 1 anchor 1 3 1 2'));
check('fixture reads actual stable native vertex keys after binding commit',group.includes("boundaryBefore:boundary,boundary:await apiRequest('boundary 901')")&&group.includes('selected.key===String(native.key)'));
check('single SVG pointer uses actual screen CTM and elementFromPoint hit test',group.includes('getScreenCTM()')&&group.includes('document.elementFromPoint(p.x,p.y)')&&group.includes('await page.mouse.click(point.x,point.y)'));
check('normal bounded Tab then real Enter Space select outer and hole',group.includes('count<80')&&group.includes("['outer:2','Enter'],['hole:0:2','Space']")&&group.includes('await page.keyboard.press(key)'));
check('dropdown interaction uses native keyboard path without selectOption',group.includes("await click('#igVertex');await page.keyboard.press('Home')")&&group.includes("page.keyboard.press('ArrowDown')")&&!group.includes('selectOption('));
check('main canvas drawer navigation uses existing public controls',group.includes("await click('#toggleRight')")&&group.includes('#app .drawer-close[data-close-panel="right"]')&&!group.includes("await panel()")&&!group.includes("await click('#workspaceToggleRight')"));
check('preview trigger never waits for settle before normal Cancel',group.includes("await page.locator('#igDeleteBinding').click();")&&!group.includes("await click('#igDeleteBinding')"));
check('discard exact question normal Cancel Escape Confirm retain raw World focus owners',group.includes("await discard(false)")&&group.includes("await page.keyboard.press('Escape')")&&group.includes('equal(await raw(),beforeRaw)')&&group.includes('equal(await project(),beforeState)')&&group.includes("document.activeElement===$('igDiscardDraft')")&&group.includes('dialogs.length===beforeDialogs'));
check('old-owner diagnostic uses actual same-ID export import and unmodified captured callback',group.includes('ReferenceWorkspace.exportBytes()')&&group.includes("ReferenceWorkspace.importBytes(__s2OwnerBBytes,'s2-same-id-owner-b.gcanvas')")&&group.includes('callback:node.onclick')&&group.includes('old.callback.call(old.node)')&&group.includes('contextToken!==ownerA.contextToken')&&group.includes('equal(await raw(),bRaw)')&&group.includes('(await dump())===bWorld'));
check('source clearly distinguishes scheduling-only owner callback delivery',source.includes('scheduling-only unchanged retired callback delivery')&&group.includes('Scheduling-only diagnostic'));
check('tested editing events require trusted real inputs',group.includes("eventRows.filter(e=>['pointerdown','pointerup','click','keydown','input'].includes(e.type)).every(e=>e.trusted)"));
const refs=['AGENTS.md','公理層.md','geometry-web/grid-system-workspace.js','geometry-web/grid-system-workspace.css','geometry-web/grid-inspector.js','geometry-web/grid-anchor-positions.js','geometry-web/index.html','geometry-web/grid_system_test.js'].map(p=>{const bytes=cp.execFileSync('git',['show',BASE+':'+p],{cwd:ROOT});return {commit:BASE,path:p,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),bytes:bytes.length};});
const observedHead=cp.execFileSync('git',['rev-parse','HEAD'],{cwd:ROOT,encoding:'utf8'}).trim(),observedDirty=cp.execFileSync('git',['status','--porcelain'],{cwd:ROOT,encoding:'utf8'}).trim();
const report={schema:'geometry-ui-s2-static-preparation/1',at:new Date().toISOString(),base,baseSHA256:sha(base),observedHead,observedDirty,sourceBaseSHA:BASE,preparedOnly:true,browserExecuted:false,nativeExecuted:false,scope:'Parser and source equivalence only; never a UI pass',command:[process.execPath,...process.argv.slice(1)],node:{path:process.execPath,sha256:sha(process.execPath),version:process.version},validator:{path:__filename,sha256:sha(__filename)},probe:{path:target,sha256:sha(target)},checks,parsed,sourceReferences:refs,ok:checks.every(c=>c.ok)};
fs.writeFileSync(path.join(OUT,'preparation-source-QA.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({ok:report.ok,checks:checks.length,expressions:parsed.length,failed:checks.filter(c=>!c.ok),preparedOnly:true}));process.exitCode=report.ok?0:1;
