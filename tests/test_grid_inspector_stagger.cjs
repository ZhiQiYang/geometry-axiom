/* #263: whole inspector event path + real native bridge; no HTTP/browser claim. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const {spawn} = require('node:child_process');
const {createInterface} = require('node:readline');
const ROOT = path.join(__dirname,'..','geometry-web');

function element(value='') {
  return {value, disabled:false, isConnected:true, children:[], dataset:{},
    classList:{add(){},remove(){},toggle(){}}, setAttribute(){}, append(){},
    addEventListener(type,fn){this['on'+type]=fn;}, focus(){}, querySelector(){return null;},
    querySelectorAll(){return [];}};
}
function pane() {
  const p=element();p.nodes=new Map();
  Object.defineProperty(p,'innerHTML',{set(html){
    p.nodes.clear();for(const m of html.matchAll(/<(\w+)\b([^>]*\bid="([^"]+)"[^>]*)>/g)){
      const n=element(/\bvalue="([^"]*)"/.exec(m[2])?.[1]||'');n.tag=m[1];p.nodes.set(m[3],n);
    }
  }});
  p.querySelector=s=>p.nodes.get(s.replace(/^#/,''))||null;
  p.querySelectorAll=s=>s==='button,input,select'?[...p.nodes.values()].filter(n=>['button','input','select'].includes(n.tag)):
    s.split(',').map(q=>p.querySelector(q)).filter(Boolean);
  return p;
}
async function run(testContext) {
  const binary=process.env.GEOMETRY_TEST_BRIDGE;
  assert.ok(binary,'Set GEOMETRY_TEST_BRIDGE to the freshly compiled native bridge');
  const temp=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-263-'));
  const child=spawn(binary,[],{cwd:temp,stdio:['pipe','pipe','pipe']});
  let errors='',pending=[],transcript=[];child.stderr.on('data',b=>{errors+=b;});
  const lines=createInterface({input:child.stdout});
  lines.on('line',line=>{const item=pending.shift();if(!item)throw Error('Unexpected bridge reply '+line);transcript.push({response:line});try{item.resolve(JSON.parse(line));}catch(e){item.reject(e);}});
  child.on('error',e=>{for(const item of pending.splice(0))item.reject(e);});
  child.on('exit',(code,signal)=>{for(const item of pending.splice(0))item.reject(Error(`bridge exit ${code}/${signal}: ${errors}`));});
  const ask=cmd=>new Promise((resolve,reject)=>{transcript.push({command:cmd});pending.push({resolve,reject});child.stdin.write(cmd+'\n');});
  const ok=async cmd=>{const r=await ask(cmd);assert.equal(r.ok,true,cmd+': '+JSON.stringify(r));return r;};
  const declare=async declaration=>{const r=await ask('line preview '+declaration);assert.equal(r.ok,true,JSON.stringify(r));assert.equal(r.preview?.valid,true,JSON.stringify(r));return ok('line confirm '+r.preview.token);};
  let sequence=0,oc={gridBindings:[],faces:[],gridSystems:[],busy:false};
  const context={},document={body:{append(){}},querySelector(){return null;},createElement(){return element();},getElementById(){return null;}};
  const workspace={};
  const globals={window:{InfiniteGridWorkspace:workspace,addEventListener(){}},document,oc,TextEncoder,structuredClone,console,
    ReferenceWorkspace:{escape:String,context:()=>context},GeometryProject:{Features:{gridSourceKey:JSON.stringify}},
    apiRequest:ask,confirmReferenceImpact:async preview=>ok('line confirm '+preview.token),
    renderObjects:async()=>{oc.gridSystems=(await ok('objects')).gridSystems;}};
  vm.createContext(globals);vm.runInContext(fs.readFileSync(path.join(ROOT,'grid-inspector.js'),'utf8'),globals,{filename:'grid-inspector.js'});
  const card=value=>({id:90,name:'source',fields:[{id:1,name:'stagger',type:'dimension',input:String(value)},
    {id:2,name:'phase',type:'dimension',input:'-20'},{id:3,name:'step',type:'dimension',input:'600'},
    {id:4,name:'panel',type:'dimension',input:'400'},{id:5,name:'gap',type:'dimension',input:'6'},
    {id:6,name:'anchor',type:'dimension',input:'-100'}]});
  const parameter=async value=>{
    const request={schema:'engineering-transaction/1',expectedRevision:(await ok('engineering-read')).revision,
      operations:[{op:'put-parameter',value:card(value)}]};
    const file=path.join(temp,'parameter-'+(++sequence)+'.json');fs.writeFileSync(file,JSON.stringify(request));
    const p=(await ok('engineering-preview '+file)).preview;assert.equal(p.valid,true,JSON.stringify(p));await ok('engineering-confirm '+p.token);
  };
  const grid=async()=>{oc.gridSystems=(await ok('objects')).gridSystems;return oc.gridSystems.find(g=>g.id===7);};
  const rename=async(name,step)=>{
    const current=await grid(),p=pane();workspace.renderInspector(p,current);
    p.querySelector('#giName').value=name;
    if(step!=null)p.querySelector('#giUStep').value=String(step);
    await p.querySelector('#giPreview').onclick();
    assert.ok(!p.querySelector('#giStatus').textContent?.includes('無法'),p.querySelector('#giStatus').textContent);
    const next=await grid();assert.equal(next.name,name,'inspector must actually confirm renamed source');return next;
  };
  let passed=0;
  const check=async(name,body)=>{
    const execute=async()=>{await body();passed++;console.log('PASS '+name);};
    if(testContext)await testContext.test(name,execute);else await execute();
  };
  try {
    await ok('reset');await parameter(400);
    for(const axis of ['u','v'])for(const mode of ['repeat','repeat-panel'])for(const ref of [false,true]){
      const stagger=ref?'param:90:1':'-250';
      const definition=mode==='repeat'?'repeat param:90:2 param:90:3':'repeat-panel param:90:4 gap param:90:5 from param:90:6';
      const along=axis==='u'?`u ${definition} stagger ${stagger} v repeat 0 400`:`u repeat 0 600 v ${definition} stagger ${stagger}`;
      await declare(`grid-system 7 name-hex 41 main-along none ${along}`);
      const before=await grid();
      await check(`GEO263_RENAME_PRESERVES_STAGGER ${axis}/${mode}/${ref?'parameter':'literal'}`,async()=>{
        const after=await rename('renamed');
        assert.deepEqual(after[axis+'Definition'],before[axis+'Definition'],'GEO263_STAGGER_LOST: rename must preserve value and every ParameterRef');
        assert.deepEqual(after[(axis==='u'?'v':'u')+'Definition'],before[(axis==='u'?'v':'u')+'Definition']);
        const dump=(await ok('dump')).text;assert.ok(dump.includes('stagger '+stagger),'GEO263_STAGGER_LOST_IN_DUMP');
        const scene=path.join(temp,'roundtrip.scene');fs.writeFileSync(scene,dump);await ok('loadfile '+scene);
        assert.deepEqual((await grid())[axis+'Definition'],before[axis+'Definition'],'GEO263_STAGGER_LOST_ON_REOPEN');
      });
    }
    await declare('grid-system 7 name-hex 41 main-along none u repeat 0 600 stagger param:90:1 v repeat 0 400');
    await rename('parameter remains live');
    await check('GEO263_PARAMETER_CHANGE_REEVALUATES_STAGGER',async()=>{
      await parameter(350);const g=await grid();assert.equal(g.uDefinition.stagger,350,'GEO263_STAGGER_REFERENCE_LOST: parameter change must recalculate');
      assert.equal(g.uDefinition.parameterRefs.stagger.parameterId,90);assert.equal(g.uDefinition.parameterRefs.stagger.fieldId,1);
    });
    await check('GEO263_SPACING_EDIT_PRESERVES_STAGGER',async()=>{
      const g=await rename('spacing edit',700);assert.equal(g.uDefinition.step,700);assert.equal(g.uDefinition.stagger,350,'GEO263_STAGGER_LOST_ON_SPACING_EDIT');
    });
    await check('GEO263_EXPLICIT_REMOVAL_REMAINS_OMISSION',async()=>{
      // Execute the existing workspace serializer, not a test copy of its syntax.
      const source=fs.readFileSync(path.join(ROOT,'grid-system-workspace.js'),'utf8');
      const start=source.indexOf('  function sourceCommand(d,id) {'),end=source.indexOf('\n  async function saveSource(s)',start);
      assert.ok(start>=0&&end>start,'locate production serializer');
      const command=vm.runInNewContext(source.slice(start,end)+'\nsourceCommand', {axes:['u','v']});
      const g=await grid(),fields=new Map(),refs=new Map();
      const s={mode:'source',source:structuredClone(g),rawOverrides:new Map(),staggerOpen:{u:true,v:false}};
      const field=(id,value)=>{const node=element(String(value));node.dispatchEvent=event=>{if(event.type==='change')refs.delete(id.replace(/Source$/,''));};fields.set(id,node);};
      field('igName','removed');field('igMainAlong','none');
      for(const a of ['u','v']){const p='ig'+a.toUpperCase(),d=g[a+'Definition'];field(p+'Source',d.source);
        for(const key of ['Phase','Step','Panel','Gap','Anchor','Stagger']){
          const lower=key.toLowerCase();field(p+key,d[lower]??'');field(p+key+'Source',d.parameterRefs?.[lower]?'90:1':'');
          if(d.parameterRefs?.[lower])refs.set(p+key,d.parameterRefs[lower]);
        }}
      const slice=(from,to)=>{const start=source.indexOf(from),end=source.indexOf(to,start);assert.ok(start>=0&&end>start,from);return source.slice(start,end);};
      const intSource=slice('  const int = (id, title, min = -LIMIT, max = LIMIT) => {','  const signed =');
      const draftSource=slice('  function sourceDraft(s) {','  function anchor(');
      const removeSource=slice('      const a = b.dataset.igRemoveStagger,','\n    };\n    $(\'igSourceForm\')');
      const inputContext={axes:['u','v'],TextEncoder,LIMIT:100000000,state:s,quietDraft:false,
        rawField:(_s,id)=>fields.get(id).value,$:id=>fields.get(id),canEdit:()=>true,
        window:{ParameterUI:{sourceRef:id=>refs.get(id)}},Event:class {constructor(type){this.type=type;}},
        b:{dataset:{igRemoveStagger:'u'}},s};
      vm.createContext(inputContext);
      vm.runInContext('(function(){'+removeSource+'})()',inputContext);
      assert.equal(fields.get('igUStagger').value,'','GEO263_REMOVE_CLEARS_INPUT');
      assert.equal(refs.has('igUStagger'),false,'GEO263_REMOVE_CLEARS_REFERENCE');
      const draft=vm.runInContext(intSource+draftSource+'\nsourceDraft(s)',inputContext);
      assert.equal(Object.hasOwn(draft.uDefinition,'stagger'),false,'GEO263_SOURCE_DRAFT_MUST_NOT_RESTORE_REMOVED_STAGGER');
      assert.equal(Object.hasOwn(draft.uDefinition.parameterRefs,'stagger'),false);
      const declaration=command(draft,7);assert.ok(!declaration.includes('stagger'),'explicit removal must not copy the old stagger');
      await declare(declaration);assert.equal(Object.hasOwn((await grid()).uDefinition,'stagger'),false);
    });
    await check('GEO263_RENAME_PRESERVES_MAIN_ALONG_AND_SOURCE_RULE',async()=>{
      await declare('grid-system 7 name-hex 41 main-along u u repeat 0 600 v repeat 0 400');
      await declare('grid-source-rule 7 create name-hex 72756c65 selector all-cells divide 2 2');
      const before=await grid(),after=await rename('with rule');
      assert.equal(after.mainAlong,'u','GEO263_MAIN_ALONG_LOST');assert.ok(before.rules.length===1);
      assert.deepEqual(after.rules,before.rules,'GEO263_SOURCE_RULE_LOST');
    });
    console.log(`${passed} pass / ${12-passed} fail`);
  } finally {child.stdin.end();await new Promise(resolve=>child.once('close',resolve));lines.close();
    if(process.env.GEOMETRY_263_TRANSCRIPT)fs.writeFileSync(process.env.GEOMETRY_263_TRANSCRIPT,transcript.map(row=>JSON.stringify(row)).join('\n')+'\n');
    fs.rmSync(temp,{recursive:true,force:true});}
}
if(require.main===module)require('node:test')('GEO263 native inspector contract',run);
module.exports=run;
