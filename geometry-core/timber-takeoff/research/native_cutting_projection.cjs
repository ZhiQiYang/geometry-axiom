'use strict';
/* Research-only itemKey -> woodworking row projection. It does not invoke a
 * formal cutting-plan/2 API or register a project attachment/capability. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const [repo,root,candidatePath]=process.argv.slice(2);
assert.ok(repo&&root&&candidatePath,'usage: node native_cutting_projection.cjs REPO NATIVE_OUT CANDIDATE');
const Candidate=require(path.resolve(candidatePath));
const Policy=require(path.resolve(repo,'geometry-templates/woodworking/cutting.js'));
const Settings=require(path.resolve(repo,'geometry-web/cutting-settings.js'));
const copy=value=>JSON.parse(JSON.stringify(value));
const read=name=>JSON.parse(fs.readFileSync(path.join(root,name),'utf8'));
const write=(name,value)=>fs.writeFileSync(path.join(root,name),JSON.stringify(value,null,2)+'\n');
const count=plan=>plan.groups.reduce((n,g)=>n+g.newStockCount,0);
function documentOf(data){
  const members=new Map(data.representations.map(row=>[row.ref,Candidate.memberOf(row)]));
  return {schema:Candidate.DOCUMENT_SCHEMA,projectScope:data.context.projectScope,scenario:data.context.scenario,
    nextItemKey:Math.max(0,...data.declarations.items.map(item=>item.itemKey))+1,
    items:data.declarations.items.map(item=>({itemKey:item.itemKey,members:item.members.map(ref=>copy(members.get(ref))),
      representative:Candidate.tupleOf(members.get(item.representative))})),excluded:data.declarations.excluded.map(ref=>copy(members.get(ref)))};
}
(async()=>{
  const settings=read('cutting-settings.json');Settings.validate(settings);
  const settingsFingerprint=await Settings.fingerprint(settings),cases=[];
  for(const name of ['single','independent-control']){
    const unresolved=read(`facts/${name}-unresolved.input.json`),explicit=read(`facts/${name}-explicit.input.json`);
    const before=Candidate.evaluate(unresolved),after=Candidate.evaluate(explicit);
    assert.equal(before.status,'INCOMPLETE');assert.ok(before.diagnostics.some(d=>d.code==='DUPLICATE_SOURCE_NEEDS_REVIEW'));
    assert.equal(after.status,'COMPLETE');assert.equal(after.itemCount,name==='single'?1:2);
    const rawRows=JSON.stringify(before.rawRows),history=new Candidate.StudyHistory(documentOf(unresolved));
    const draft=history.begin(),merged=documentOf(explicit);
    merged.nextItemKey=draft.document.nextItemKey;draft.document=merged;
    assert.equal(history.commit(draft).changed,true);assert.equal(history.evaluate(explicit).status,'COMPLETE');
    assert.equal(history.undo(),true);
    const undone=history.evaluate(unresolved);
    assert.equal(undone.status,'INCOMPLETE');assert.ok(undone.diagnostics.some(d=>d.code==='DUPLICATE_SOURCE_NEEDS_REVIEW'));
    assert.equal(JSON.stringify(undone.rawRows),rawRows,'U476_NATIVE_UNDO_ORIGINAL_ROWS');
    assert.equal(history.view().document.nextItemKey,unresolved.representations.length+1,'U476_NATIVE_UNDO_HIGH_WATER');
    assert.equal(history.redo(),true);assert.equal(history.evaluate(explicit).status,'COMPLETE');
    const live=read(`${name}/live-schedule.json`),saved=read(`${name}/saved-schedule.json`),byRef=new Map(explicit.representations.map(row=>[row.ref,row])),mapping=[];
    const rows=after.items.map(item=>{
      const rep=byRef.get(item.representative),native=(rep.kind==='live'?live:saved).rows.find(row=>row.id===rep.timber.id);
      assert.ok(native);assert.equal(native.L,item.L);assert.equal(native.A,item.A);assert.equal(native.B,item.B);
      const row=copy(native);mapping.push({itemKey:item.itemKey,originalTypedTimberId:native.id,representative:item.representative,aliases:item.members});
      row.id=item.itemKey;
      row.sources=row.sources.map(source=>({...source,target:source.target?.kind==='timber'?{...source.target,id:item.itemKey}:source.target}));
      return row;
    });
    const plan=Policy.evaluateRows(rows,settings,{status:'EMPTY',diagnostics:[],groups:[],
      worldFingerprint:explicit.context.liveReadPin,settingsFingerprint,label:'U476 research itemKey row projection'});
    assert.equal(plan.status,'COMPLETE');assert.equal(Policy.verify(plan,after.items.map(item=>item.itemKey)),true);
    assert.equal(count(plan),name==='single'?1:2);
    assert.equal(after.accounting.physicalItemLengthMm,name==='single'?4000:8000);
    write(`facts/${name}-unresolved.output.json`,before);write(`facts/${name}-explicit.output.json`,after);
    write(`facts/${name}-revoked.output.json`,undone);
    write(`k1-${name}-item-projection.json`,{researchOnly:true,
      statement:'These woodworking row ids are study itemKey surrogates, not native timber ids or a formal cutting-plan/2 request.',mapping,plan});
    const record={name,rawRepresentations:before.rawRows.length,rawRepresentedLengthMm:before.accounting.rawRepresentedLengthMm,
      beforeStatus:before.status,afterItemCount:after.itemCount,physicalItemLengthMm:after.accounting.physicalItemLengthMm,
      removedAliasLengthMm:after.accounting.removedAliasLengthMm,newStockCount:count(plan),stockLengthMm:4200,
      undoStatus:undone.status,undoRawRowsEqual:true,undoHighWater:history.view().document.nextItemKey,redoStatus:'COMPLETE'};
    cases.push(record);console.log(JSON.stringify(record));
  }
  const candidateBytes=fs.readFileSync(candidatePath);
  const summary={researchOnly:true,formalCuttingPlan2:false,formalOwnerService:false,literalDimensionsOnly:true,
    candidate:{bytes:candidateBytes.length,sha256:crypto.createHash('sha256').update(candidateBytes).digest('hex')},
    projection:'itemKey is explicitly converted to a synthetic row.id for the existing woodworking policy; original rows and aliases remain separately recorded.',
    settings,cases};
  write('native-cutting-projection-summary.json',summary);
  console.log(JSON.stringify({ok:true,researchOnly:true,cases:cases.length}));
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
