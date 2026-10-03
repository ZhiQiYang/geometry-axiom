const {test}=require('node:test'),assert=require('node:assert/strict');
const core=require('../geometry-web/timber-schedule.js'),S=require('../geometry-web/timber-supports.js')(core);
const hash='a'.repeat(64),clone=x=>JSON.parse(JSON.stringify(x));
const timber=(id,surface=0)=>({id,role:'primary',geometry:{surface,length:2960,A:27,B:33,dir:'+v',side:'+n',
  origin:[514,20,2500],axes:[[0,1,0],[-1,0,0],[0,0,1]]},definition:{anchor:'at-line guide 0',selector:''}});
const endpoint=(id,face,at,normal)=>({status:'exact',at,crossRange:[487,514],relation:{kind:'timber-face',
  source:{kind:'timber',id},localFace:face,normalWorld:normal,owner:null,surface:0,
  stop:{axis:'v',at,range:[0,4000],fixity:'fixed'}}});
function refs(){return {ok:true,sourceFingerprint:hash,timbers:[timber(7),timber(8)],engineeringSources:[],
  timberSupports:{schema:'native-timber-supports/1',sourceFingerprint:hash,entries:[7,8].map(id=>({id,surface:0,owner:null,
    start:endpoint(0,'B1',20,[0,1,0]),finish:endpoint(91,'B0',2980,[0,-1,0])}))}};}

test('decorates each native placement once and preserves typed zero support and surface identities',()=>{
  const r=refs(),before=JSON.stringify(r),s=S.derive(r,0);
  assert.deepEqual(s.ids,[7,8]);assert.equal(s.rows[0].supports.start.relation.source.id,0);
  assert.equal(s.supportSourceFingerprint,hash);
  assert.equal(s.rows[0].selector,'依 R6 自動推導');
  assert.match(S.sourceText(s.rows[0]),/角材 0／B1/);
  assert.equal(JSON.stringify(r),before);
  s.rows[0].supports.start.relation.source.id=99;assert.equal(r.timberSupports.entries[0].start.relation.source.id,0);
  assert.deepEqual(S.derive(r,0,[8]).ids,[8]);
});

test('missing bridge capability, missing entry and unknown relation stay unknown',()=>{
  const r=refs();delete r.timberSupports;
  assert.equal(S.derive(r,0).rows[0].supports.start.status,'unknown');
  const partial=refs();partial.timberSupports.entries.shift();
  assert.equal(S.derive(partial,0).rows[0].supports.finish.status,'unknown');
  partial.timberSupports.entries[0].finish={status:'unknown',relation:{source:{id:99}}};
  assert.deepEqual(S.derive(partial,0).rows[1].supports.finish,{status:'unknown',relation:null});
  assert.match(S.sourceText(S.derive(partial,0).rows[1]),/末端：未知/);
});

test('rejects stale source fingerprint, unknown schema and malformed exact provenance instead of guessing',()=>{
  for(const mutate of [
    r=>r.timberSupports.sourceFingerprint='b'.repeat(64),
    r=>r.timberSupports.schema='native-timber-supports/2',
    r=>r.timberSupports.sourceFingerprint=null,
    r=>r.timberSupports.entries[0].start.relation.source.id=null,
    r=>r.timberSupports.entries[0].start.relation.localFace='min_v',
    r=>r.timberSupports.entries[0].start.relation.normalWorld=[0,0,0],
    r=>r.timberSupports.entries[0].start.relation.stop.range=[0,500],
    r=>r.timberSupports.entries[0].start.relation.source.id=7,
    r=>r.timberSupports.entries[0].start.relation.surface=9,
    r=>r.timberSupports.entries[0].surface=9,
  ]){const r=refs();mutate(r);assert.throws(()=>S.derive(r,0),/核對|一致/);}
});

test('duplicate projection identities reject rather than causing double counting or silent replacement',()=>{
  const r=refs();r.timberSupports.entries.push(clone(r.timberSupports.entries[0]));
  assert.throws(()=>S.derive(r,0),/重複/);
});

test('boundary and embedded placement edges keep different typed sources; hole zero is exact',()=>{
  const r=refs(),e=r.timberSupports.entries[0];
  e.start.relation={kind:'hole-edge',source:{kind:'boundary',id:1},edgeIndex:2,holeIndex:0,localFace:null,normalWorld:null,owner:null,
    surface:0,stop:{axis:'v',at:20,range:[0,4000],fixity:'fixed'}};
  e.finish.relation={kind:'outline-edge',source:{kind:'placement',id:0},edgeIndex:1,holeIndex:null,localFace:null,normalWorld:null,owner:null,
    surface:0,stop:{axis:'v',at:2980,range:[0,4000],fixity:'fixed'}};
  const row=S.derive(r,0).rows[0];assert.match(S.sourceText(row),/邊界 1／h0e2/);assert.match(S.sourceText(row),/承載面 0／e1/);
  e.start.relation.source.id=0;assert.throws(()=>S.derive(r,0),/核對/);
});

function owned(){
  const r=refs(),p={instanceId:4,memberId:12,bindingId:9,ruleId:7,ruleVersion:2,
    ruleFingerprint:'b'.repeat(64),bindingFingerprint:'c'.repeat(64),instanceFingerprint:'d'.repeat(64)};
  r.assembly={instances:[{value:{source:{id:4,bindingId:9,rule:{id:7,version:2,fingerprint:p.ruleFingerprint}}},members:[{memberId:12,timberId:7}]}],
    rules:[{value:{id:7,version:2,members:[{id:12,slotId:5}]},fingerprint:p.ruleFingerprint}],
    bindings:[{value:{id:9,slots:[{slotId:5,A:{kind:'literal',value:27},B:{kind:'literal',value:33}}]},complete:true,
      fingerprint:p.bindingFingerprint,effective:[{slotId:5,A:{value:27,path:'直接值 27'},B:{value:33,path:'直接值 33'}}]}]};
  r.timberSupports.entries[0].owner=p;
  return r;
}
test('checks exact owned member and fixed source versions against the schedule dependency',()=>{
  const r=owned(),row=S.derive(r,0).rows[0];assert.equal(row.supportOwner.memberId,12);
  assert.equal(row.supportOwner.instanceFingerprint,'d'.repeat(64));
  for(const field of ['instanceId','memberId','ruleVersion','ruleFingerprint','bindingFingerprint']){
    const broken=clone(r);broken.timberSupports.entries[0].owner[field]=typeof row.supportOwner[field]==='number'?99:'e'.repeat(64);
    assert.throws(()=>S.derive(broken,0),/來源無法核對/);
  }
  const broken=refs();broken.timberSupports.entries[0].owner=clone(row.supportOwner);
  assert.throws(()=>S.derive(broken,0),/來源無法核對/);
});

// Independent CSV parser: quoted line breaks must remain in a single cell.
function parseCSV(text){
  const rows=[];let row=[],cell='',quoted=false;
  for(let i=1;i<text.length;i++){
    const c=text[i];
    if(c==='"'){
      if(quoted&&text[i+1]==='"'){cell+='"';i++;}else quoted=!quoted;
    }else if(!quoted&&c===','){row.push(cell);cell='';}
    else if(!quoted&&c==='\r'&&text[i+1]==='\n'){row.push(cell);rows.push(row);row=[];cell='';i++;}
    else cell+=c;
  }
  assert.equal(quoted,false);assert.equal(cell,'');return rows;
}
test('CSV retains all original schedule cells, safe multiline labels and exact per-row provenance',()=>{
  const r=refs();r.timbers[0].definition.anchor='\t=HYPERLINK("danger")\nsecond line';
  const snapshot=S.derive(r,0),base=parseCSV(core.csv(snapshot)),csv=parseCSV(S.csv(snapshot));
  assert.equal(csv.length,3);assert.equal(csv[0].length,base[0].length+3);
  for(let i=0;i<base.length;i++)assert.deepEqual(csv[i].slice(0,base[i].length),base[i]);
  assert.equal(csv[1].at(-3),hash);
  assert.deepEqual(JSON.parse(csv[1].at(-2)),snapshot.rows[0].supports.start);
  assert.deepEqual(JSON.parse(csv[2].at(-1)),snapshot.rows[1].supports.finish);
  assert.match(csv[1][10],/^'\t=HYPERLINK/);
});

test('sorting and CSV export are read-only and preserve selections and unknown provenance',()=>{
  const r=refs();r.timbers[0].geometry.length=3000;
  const snapshot=S.derive(r,0),before=JSON.stringify(snapshot);
  assert.deepEqual(S.sorted(snapshot.rows,'length').map(r=>r.id),[8,7]);
  assert.equal(parseCSV(S.csv(snapshot,'length'))[1][1],'8');assert.equal(JSON.stringify(snapshot),before);
  delete r.timberSupports;const csv=parseCSV(S.csv(S.derive(r,0)));
  assert.deepEqual(JSON.parse(csv[1].at(-2)),{status:'unknown',relation:null});
  assert.equal(parseCSV(S.csv(S.derive(refs(),0,[]))).length,1);
});
