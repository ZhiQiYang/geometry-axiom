'use strict';
// Read-only parser and exact-helper mock DOM review. No browser/native import.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto'),cp=require('node:child_process');
const DIR=__dirname,ROOT='<workspace-path>',BASE='c0f05baade2424482fab94c72f0592f7b02326ae';
const target=path.join(DIR,'issue123_adopted_slices_browser.header-corrected.cjs'),patch=path.join(DIR,'issue123-header-oracle-correction.patch');
const source=fs.readFileSync(target,'utf8'),original=cp.execFileSync('git',['show',BASE+':tests/issue123_adopted_slices_browser.cjs'],{cwd:ROOT,encoding:'utf8'});
const mod={exports:{}};vm.runInNewContext(process.binding('natives')['internal/deps/acorn/acorn/dist/acorn'],{module:mod,exports:mod.exports});
const parse=s=>mod.exports.parse(s,{ecmaVersion:'latest',sourceType:'script'}),a=parse(original),b=parse(source),checks=[];
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
function check(name,ok,detail){checks.push({name,ok:ok===true,...(detail===undefined?{}:{detail})});}
function walk(n,fn){if(!n||typeof n!=='object')return;fn(n);for(const v of Object.values(n)){if(Array.isArray(v))for(const c of v)walk(c,fn);else if(v&&typeof v==='object')walk(v,fn);}}
function calls(ast,s,exclude){const rows=[];walk(ast,n=>{if(n.type==='CallExpression'&&n.callee.name==='check'&&!(exclude&&n.start>=exclude.start&&n.end<=exclude.end))rows.push(s.slice(n.start,n.end));});return rows;}
const af=a.body.find(n=>n.type==='FunctionDeclaration'&&n.id.name==='assertHeaderActions'),bf=b.body.find(n=>n.type==='FunctionDeclaration'&&n.id.name==='assertHeaderActions');
check('only assertHeaderActions helper bytes change',original.slice(0,af.start)===source.slice(0,bf.start)&&original.slice(af.end)===source.slice(bf.end));
check('all six group methods and all other assertions remain byte identical',JSON.stringify(calls(a,original,af))===JSON.stringify(calls(b,source,bf)),{old:calls(a,original).length,new:calls(b,source).length});
for(const f of a.body.filter(n=>n.type==='FunctionDeclaration'&&n.id.name!=='assertHeaderActions')){const n=b.body.find(n=>n.type==='FunctionDeclaration'&&n.id.name===f.id.name);check('unchanged helper '+f.id.name,!!n&&source.slice(n.start,n.end)===original.slice(f.start,f.end));}
check('visible action condition retains original size inside hit parent and mobile44',source.includes('r.width>0&&r.height>0&&r.inside&&r.hit&&r.rightActions&&(width>560||r.width>=44&&r.height>=44)'));
check('own zero rectangle plus computed display:none is mandatory for hidden exception',source.includes("r.width===0&&r.height===0&&s.display==='none'&&panel?.ok===true"));
check('hidden left and right use their existing distinct strict breakpoints',source.includes("selector==='#workspaceToggleLeft'&&innerWidth>900")&&source.includes("selector==='#workspaceToggleRight'&&innerWidth>680"));
check('no forced input or disabled browser sandbox was introduced',!(/force\s*:\s*true|--no-sandbox|--disable-setuid-sandbox/.test(source)));
const helper=source.slice(bf.start,bf.end),selectors=['#faceUndoButton','#faceRedoButton','#workspaceFitButton','#workspaceToggleLeft','#workspaceToggleRight','#fileMenuBtn','#workspaceProjectActions .project-save','#workspaceProjectActions .project-info-button'];
function rect(left,top,width,height){return {x:left,y:top,left,top,width,height,right:left+width,bottom:top+height};}
function setup(width){
 const height=804,h=width<=560?96:56,left=width>900?240:0,right=width>680?240:0,doc=new Map(),actions={contains:e=>e?.member===true},header={box:rect(0,0,width,h)},viewport={box:rect(left,h,width-left-right,height-h-32)};
 const make=(key,box,style={},extra={})=>{const e={key,box,style:{display:'block',visibility:'visible',position:'static',...style},member:true,...extra,getBoundingClientRect(){return this.box;},contains(n){return n===this||n?.parent===this;}};doc.set(key,e);return e;};
 doc.set('.object-workspace-topbar',{getBoundingClientRect:()=>header.box});doc.set('#faceEditorViewport',{getBoundingClientRect:()=>viewport.box});doc.set('.object-workspace-actions',actions);
 let x=12;for(const key of selectors){const size=width<=560?44:38,hidden=(key==='#workspaceToggleLeft'&&width>900)||(key==='#workspaceToggleRight'&&width>680);make(key,hidden?rect(0,0,0,0):rect(x,width<=560?44:6,size,44),{display:hidden?'none':'block'});if(!hidden)x+=size+2;}
 make('#objectWorkspace .face-layer-panel',left?rect(0,h,left,height-h-32):rect(0,0,0,0),{display:left?'block':'none'});
 make('#objectWorkspace .face-inspector-panel',right?rect(width-right,h,right,height-h-32):rect(0,0,0,0),{display:right?'block':'none'});
 const config={width,height,h,doc,header,viewport,overlay:null,make};
 config.document={querySelector:key=>doc.get(key)||null,elementFromPoint(x,y){if(config.overlay&&x>=config.overlay.box.left&&x<=config.overlay.box.right&&y>=config.overlay.box.top&&y<=config.overlay.box.bottom)return config.overlay;for(const e of doc.values()){const r=e.box;if(r&&r.width>0&&r.height>0&&e.style.display!=='none'&&x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom)return e;}return null;}};
 return config;
}
async function runMock(name,width,expected,modify=()=>{}){const c=setup(width);modify(c);let outcome=null,detail=null,error=null;const context={document:c.document,getComputedStyle:e=>e.style,innerWidth:width,innerHeight:c.height,read:expression=>vm.runInNewContext(expression,{document:c.document,getComputedStyle:e=>e.style,innerWidth:width,innerHeight:c.height}),check:(name,ok,d)=>{outcome=ok;detail=d;}};try{await vm.runInNewContext(helper+';assertHeaderActions('+width+');',context);}catch(e){error=e.message;outcome=false;}check('exact-helper mock: '+name,outcome===expected,{expected,observed:outcome,error,detail});}
(async()=>{
 for(const width of [1382,901,900,681,680,560,390])await runMock('correct header and persistent panel or opener at '+width,width,true);
 const right='#objectWorkspace .face-inspector-panel',left='#objectWorkspace .face-layer-panel',button='#workspaceToggleRight';
 await runMock('hidden right opener at900 accepted with real persistent right panel',900,true);
 await runMock('hidden left opener at901 accepted with real persistent left panel',901,true);
 await runMock('hidden left opener at900 rejected at its exact drawer breakpoint',900,false,c=>{const e=c.doc.get('#workspaceToggleLeft');e.box=rect(0,0,0,0);e.style.display='none';});
 await runMock('hidden right opener at680 rejected at its exact drawer breakpoint',680,false,c=>{const e=c.doc.get(button);e.box=rect(0,0,0,0);e.style.display='none';});
 await runMock('zero right opener not computed displaynone rejected',900,false,c=>c.doc.get(button).style.display='block');
 await runMock('half-zero right opener rejected',900,false,c=>c.doc.get(button).box=rect(0,0,0,44));
 await runMock('zero history action never receives panel exception',900,false,c=>{const e=c.doc.get('#faceUndoButton');e.box=rect(0,0,0,0);e.style.display='none';});
 await runMock('persistent right panel zero rectangle rejected',900,false,c=>c.doc.get(right).box=rect(0,0,0,0));
 await runMock('persistent right panel displaynone rejected',900,false,c=>c.doc.get(right).style.display='none');
 await runMock('persistent right panel visibilityhidden rejected',900,false,c=>c.doc.get(right).style.visibility='hidden');
 await runMock('persistent right panel outside window rejected',900,false,c=>c.doc.get(right).box=rect(700,56,240,716));
 await runMock('persistent right panel overlays canvas rejected',900,false,c=>c.doc.get(right).box=rect(630,56,240,716));
 await runMock('persistent left panel overlays canvas rejected',1382,false,c=>c.doc.get(left).box=rect(0,56,280,716));
 await runMock('fixed right drawer impersonating persistent panel rejected',900,false,c=>c.doc.get(right).style.position='fixed');
 await runMock('unrelated overlay at persistent panel live hit rejected',900,false,c=>c.overlay={box:c.doc.get(right).box});
 await runMock('missing persistent panel rejected',900,false,c=>c.doc.delete(right));
 await runMock('missing visible history action rejected',900,false,c=>c.doc.delete('#faceUndoButton'));
 await runMock('visible action outside header rejected',900,false,c=>c.doc.get('#faceUndoButton').box=rect(12,70,38,44));
 await runMock('visible action missing right-actions parent rejected',900,false,c=>c.doc.get('#faceUndoButton').member=false);
 await runMock('unrelated overlay at visible action live hit rejected',900,false,c=>c.overlay={box:c.doc.get('#faceUndoButton').box});
 await runMock('mobile visible action below44 rejected',390,false,c=>c.doc.get('#faceUndoButton').box=rect(12,44,40,44));
 const report={schema:'geometry-header-oracle-static-mock-review/1',at:new Date().toISOString(),baseFullSHA:BASE,observedHead:cp.execFileSync('git',['rev-parse','HEAD'],{cwd:ROOT,encoding:'utf8'}).trim(),observedDirty:cp.execFileSync('git',['status','--porcelain'],{cwd:ROOT,encoding:'utf8'}).trim(),browserExecuted:false,nativeExecuted:false,productOrFormalTestWrites:false,sourceScope:'Exact corrected helper with mocks plus parser/source equivalence; no browser paint acceptance',command:[process.execPath,...process.argv.slice(1)],node:{path:process.execPath,sha256:sha(process.execPath),version:process.version},validator:{path:__filename,sha256:sha(__filename)},inputs:[target,patch].map(p=>({path:p,sha256:sha(p)})),checks,ok:checks.every(c=>c.ok),limits:['Mock rectangles/styles/hits do not prove actual browser geometry or rendered panel contents.','Persistent-panel predicate excludes fixed drawers and canvas-overlap, permits other non-fixed layout positions as original CSS contract does.','Physical mobile, touch, OS dialogs and all43/full gates remain separate.']};
 fs.writeFileSync(path.join(DIR,'header-oracle-static-mock-review.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({ok:report.ok,checks:checks.length,failed:checks.filter(c=>!c.ok).map(c=>({name:c.name,detail:c.detail})),browserExecuted:false}));process.exitCode=report.ok?0:1;
})();
