/* R06: real read-only consumers must preserve native finite-bay identities.
 * Geometry is supplied as native facts; no test-side bay solver is substituted. */
const {test}=require('node:test'),assert=require('node:assert/strict');
const {createHash}=require('node:crypto');
const Core=require('../geometry-web/timber-schedule.js');
const Schedule=require('../geometry-web/timber-supports.js')(Core);
const Inspector=require('../geometry-web/source-inspector.js');
const clone=structuredClone,hash=n=>String(n).repeat(64);
const secondary={secondary:{line:31,left:11,right:22}};
const memberRows=[{primary:11,timberId:7},{primary:22,timberId:8},{...secondary,timberId:9}];
const owner=identity=>({instanceId:4,identity:clone(identity),bindingId:9,ruleId:7,ruleVersion:2,
  ruleFingerprint:hash('b'),bindingFingerprint:hash('c'),instanceFingerprint:hash('d')});
const timber=(id,secondary=false)=>({id,role:secondary?'secondary':'primary',
  geometry:{surface:0,length:secondary?973:2960,A:secondary?20:27,B:secondary?30:33,
    dir:secondary?'+u':'+v',side:'+n',origin:secondary?[500,1000,2500]:[500,20,2500],
    axes:secondary?[[1,0,0],[0,1,0],[0,0,1]]:[[0,1,0],[-1,0,0],[0,0,1]]},
  definition:{anchor:'at-line guide 0',selector:''}});
function endpoint(id,at,axis,ownerValue=null){
  const horizontal=axis==='u';
  return {status:'exact',at,crossRange:horizontal?[1000,1020]:[473,500],relation:{kind:'timber-face',
    source:{kind:'timber',id},localFace:at===20||at===500?'B1':'B0',
    normalWorld:horizontal?[at===500?1:-1,0,0]:[0,at===20?1:-1,0],owner:clone(ownerValue),surface:0,
    stop:{axis,at,range:horizontal?[20,2980]:[0,4000],fixity:'fixed'}}};
}
function references(){
  const source={id:4,name:'Labels are not identity',bindingId:9,rule:{id:7,version:2,fingerprint:hash('b')},
    surfaceId:0,layout:'bay-repeat',primaries:[11,22].map(key=>({key,at:{kind:'guide',id:key},
      ends:{start:{kind:'timber',id:90},finish:{kind:'timber',id:91}}})),
    secondaryLines:[{key:31,at:{kind:'guide',id:31}}],omit:[]};
  const rule={id:7,version:2,members:[{id:1,slotId:5},{id:2,slotId:5},{id:3,slotId:6}],
    joints:[{kind:'end-to-side',dir:'u',end:'start',side:'+u',terminatedMember:3,targetMember:1},
      {kind:'end-to-side',dir:'u',end:'finish',side:'-u',terminatedMember:3,targetMember:2}]};
  const slots=[{slotId:5,A:{kind:'literal',value:27},B:{kind:'literal',value:33}},
    {slotId:6,A:{kind:'literal',value:20},B:{kind:'literal',value:30}}];
  return {ok:true,sourceFingerprint:hash('a'),timbers:[timber(7),timber(8),timber(9,true),timber(90),timber(91),timber(0)],engineeringSources:[],
    assembly:{instances:[{fingerprint:hash('d'),value:{source,mapping:clone(memberRows)},members:clone(memberRows)}],
      rules:[{value:rule,fingerprint:hash('b')}],bindings:[{value:{id:9,rule:{id:7,version:2},slots},complete:true,fingerprint:hash('c'),
        effective:slots.map(s=>({slotId:s.slotId,A:{value:s.A.value,path:'直接值 '+s.A.value},B:{value:s.B.value,path:'直接值 '+s.B.value}}))}]},
    timberSupports:{schema:'native-timber-supports/1',sourceFingerprint:hash('a'),entries:[
      ...[11,22].map((key,i)=>({id:7+i,surface:0,owner:owner({primary:key}),start:endpoint(90,20,'v'),finish:endpoint(91,2980,'v')})),
      {id:9,surface:0,owner:owner(secondary),start:endpoint(7,500,'u',owner({primary:11})),finish:endpoint(8,1473,'u',owner({primary:22}))}]}};
}
function sourceGraph(){
  const refs=references(),typed=(kind,id,version=0)=>({kind,id:String(id),version,fieldId:0,
    key:Inspector.key(kind,id,version),definitionFingerprint:hash('a'),valueFingerprint:hash('a')});
  const edge=(from,to,relation,field)=>({from,to,relation,field,active:true});
  const identities=new Map([[7,{primary:11}],[8,{primary:22}],[9,secondary]]);
  const nodes=[typed('placement',0),...refs.timbers.map(t=>({...typed('timber',t.id),placed:true,surface:0,
    lengthAxis:t.id===9?'u':'v',nativeOwner:identities.has(t.id)?owner(identities.get(t.id)):null})),
    typed('assembly-instance',4),typed('assembly-binding',9),{...typed('assembly-rule',7,2),definitionFingerprint:hash('b')}];
  const edges=refs.timbers.map(t=>edge('timber:'+t.id,'placement:0','position','surface'));
  edges.push(edge('assembly-instance:4','assembly-binding:9','dimension','binding'),
    edge('assembly-instance:4','assembly-rule:7:v2','rule-version',hash('b')),
    edge('assembly-binding:9','assembly-rule:7:v2','rule-version','rule'),
    edge('timber:7','assembly-instance:4','member','primary:11'),
    edge('timber:8','assembly-instance:4','member','primary:22'),
    edge('timber:9','assembly-instance:4','member','secondary:31:11:22'));
  return {ok:true,schema:'source-inspector/1',revision:1,complete:true,sourceFingerprint:refs.sourceFingerprint,nodes,edges,
    timberSupports:clone(refs.timberSupports)};
}
function parseCSV(text){
  assert.equal(text[0],'\ufeff');const rows=[];let row=[],cell='',quoted=false;
  for(let i=1;i<text.length;i++){
    const c=text[i];
    if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++;}else quoted=!quoted;}
    else if(!quoted&&c===','){row.push(cell);cell='';}
    else if(!quoted&&c==='\r'&&text[i+1]==='\n'){row.push(cell);rows.push(row);row=[];cell='';i++;}
    else cell+=c;
  }
  assert.equal(quoted,false);assert.equal(cell,'');return rows;
}

test('R06_BAY_SOURCE_ROW: material schedule projects full native identities and fixed W slots',()=>{
  const refs=references(),before=JSON.stringify(refs);let result;
  assert.doesNotThrow(()=>{result=Core.derive(refs,0,[7,8,9]);},'R06_BAY_SOURCE_ROW');
  assert.deepEqual(result.rows.map(r=>r.assembly.identity),[{primary:11},{primary:22},secondary],'R06_BAY_SOURCE_ROW');
  assert.deepEqual(result.rows.map(r=>[r.A,r.B]),[[27,33],[27,33],[20,30]],'R06_BAY_SOURCE_ROW');
  assert.match(Core.sourceText(result.rows[2]),/副支 線 31／左 11／右 22/,'R06_BAY_SOURCE_ROW');
  assert.equal(JSON.stringify(refs),before,'R06_BAY_SOURCE_ROW');
  refs.assembly.instances[0].value.source.name='Renamed';refs.assembly.instances[0].value.source.primaries.reverse();
  refs.assembly.instances[0].members.reverse();refs.assembly.instances[0].value.mapping.reverse();
  assert.deepEqual(Core.derive(refs,0,[7,8,9]).rows,result.rows,'R06_BAY_SOURCE_ROW');
  result.rows[2].assembly.identity.secondary.left=99;
  assert.equal(refs.assembly.instances[0].members.find(m=>m.secondary).secondary.left,11,'R06_BAY_SOURCE_ROW');
});

test('R06_BAY_MAPPING_REJECT: missing, duplicate or omitted owned identities cannot become schedule rows',()=>{
  assert.doesNotThrow(()=>Core.derive(references(),0,[9]),'R06_BAY_MAPPING_REJECT');
  const variants=[
    r=>r.assembly.instances[0].value.source.primaries.pop(),
    r=>r.assembly.instances[0].value.source.secondaryLines[0].key=99,
    r=>r.assembly.instances[0].value.source.omit.push({line:31,left:11,right:22}),
    r=>r.assembly.instances[0].value.mapping[2].secondary.right=99,
    r=>r.assembly.instances[0].value.mapping.pop(),
    r=>r.assembly.instances[0].value.mapping.push({...secondary,timberId:10}),
    r=>r.assembly.instances[0].value.mapping.push({primary:99,timberId:9}),
    r=>r.assembly.instances[0].members[2].memberId=3,
    r=>r.assembly.instances[0].members.pop(),
    r=>{r.assembly.instances[0].members.pop();delete r.timberSupports;},
    r=>r.assembly.bindings[0].value.rule.id=99,
    r=>r.assembly.bindings[0].value.rule.version=3,
    r=>delete r.assembly.bindings[0].value.rule,
    r=>r.assembly.bindings.push(clone(r.assembly.bindings[0])),
    r=>r.assembly.rules.push(clone(r.assembly.rules[0])),
  ];
  for(const mutate of variants){const refs=references();mutate(refs);
    assert.throws(()=>Core.derive(refs,0,[9]),/身分|來源|核對/,'R06_BAY_MAPPING_REJECT');}
});

test('R06_BAY_SUPPORT_IDENTITY: every member and supporting end keeps its complete native owner tuple',()=>{
  const refs=references();let result;
  assert.doesNotThrow(()=>{result=Schedule.derive(refs,0,[7,8,9]);},'R06_BAY_SUPPORT_IDENTITY');
  assert.deepEqual(result.rows[2].supportOwner,owner(secondary),'R06_BAY_SUPPORT_IDENTITY');
  assert.deepEqual(result.rows[2].supports.start.relation.owner,owner({primary:11}),'R06_BAY_SUPPORT_IDENTITY');
  for(const mutate of [r=>r.timberSupports.entries[2].owner.identity.secondary.left=22,
    r=>r.timberSupports.entries[2].owner.identity.secondary.line=99,
    r=>r.timberSupports.entries[2].owner.memberId=3,
    r=>r.timberSupports.entries[2].start.relation.owner.identity.primary=22,
    r=>r.timberSupports.entries[2].finish.relation.owner.instanceFingerprint=hash('e')]){
    const broken=clone(refs);mutate(broken);
    assert.throws(()=>Schedule.derive(broken,0,[9]),/身分|來源|核對/,'R06_BAY_SUPPORT_IDENTITY');
  }
});

test('R06_BAY_SOURCE_GRAPH: typed native member edge and fixed rule are required for source inspection',()=>{
  let graph;assert.doesNotThrow(()=>{graph=Inspector.index(sourceGraph());},'R06_BAY_SOURCE_GRAPH');
  assert.deepEqual(graph.supportEntries.get('timber:9').owner.identity,secondary,'R06_BAY_SOURCE_GRAPH');
  assert.deepEqual(graph.out.get('timber:9').filter(e=>e.relation==='confirmed-support').map(e=>e.to),['timber:7','timber:8']);
  for(const mutate of [g=>g.edges=g.edges.filter(e=>e.field!=='secondary:31:11:22'),
    g=>g.edges.find(e=>e.field==='secondary:31:11:22').field='secondary:31:22:11',
    g=>g.nodes.find(n=>n.key==='assembly-rule:7:v2').definitionFingerprint=hash('f'),
    g=>g.timberSupports.entries[2].owner.identity.secondary.line=99]){
    const broken=sourceGraph();mutate(broken);
    assert.throws(()=>Inspector.index(broken),/成員|來源|核對/,'R06_BAY_SOURCE_GRAPH');
  }
  const newer=sourceGraph();newer.nodes.find(n=>n.key==='timber:9').nativeOwner.identity.secondary.line=32;
  newer.timberSupports.entries[2].owner.identity.secondary.line=32;
  newer.edges.find(e=>e.field==='secondary:31:11:22').field='secondary:32:11:22';
  assert.ok(Inspector.freshness(graph,Inspector.index(newer),['timber:9']).changes.some(c=>c.key==='timber:9'),'R06_BAY_SOURCE_GRAPH');
});

test('R06_BAY_CSV_IDENTITY: mixed ordinary and repeated rows use aligned columns and exact typed identity JSON',()=>{
  let snapshot;assert.doesNotThrow(()=>{snapshot=Schedule.derive(references(),0,[0,7,9]);},'R06_BAY_CSV_IDENTITY');
  const csv=parseCSV(Schedule.csv(snapshot)),header=csv[0],identityColumn=header.indexOf('assembly_identity');
  assert.ok(identityColumn>=0,'R06_BAY_CSV_IDENTITY');
  assert.ok(csv.every(row=>row.length===header.length),'R06_BAY_CSV_IDENTITY');
  const byId=new Map(csv.slice(1).map(row=>[Number(row[1]),row]));
  assert.equal(byId.get(0)[identityColumn],'','R06_BAY_CSV_IDENTITY');
  assert.deepEqual(JSON.parse(byId.get(7)[identityColumn]),{primary:11},'R06_BAY_CSV_IDENTITY');
  assert.deepEqual(JSON.parse(byId.get(9)[identityColumn]),secondary,'R06_BAY_CSV_IDENTITY');
  assert.equal(byId.get(9)[header.indexOf('assembly_member_id')],'','R06_BAY_CSV_IDENTITY');
});

test('R06_SINGLE_CSV_BYTES: legacy single-member schedule remains byte-for-byte compatible',()=>{
  const refs=references(),instance=refs.assembly.instances[0];
  instance.value={source:{id:4,name:'Legacy',bindingId:9,rule:{id:7,version:2,fingerprint:hash('b')},surfaceId:0}};
  instance.members=[{memberId:1,timberId:7}];
  const csv=Core.csv(Core.derive(refs,0,[7]));
  // Captured from exact main 405f8c5, before applying P; this is the full CSV byte hash.
  assert.equal(createHash('sha256').update(csv).digest('hex'),'6f165a2e3b0c34bcf24aa70c64277ac8b8c467d09c0c635b3c43f239b058af82','R06_SINGLE_CSV_BYTES');
  assert.ok(!parseCSV(csv)[0].includes('assembly_identity'),'R06_SINGLE_CSV_BYTES');
});
