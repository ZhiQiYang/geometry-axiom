const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=process.cwd(), F=require(path.join(root,'geometry-web/feature-attachments.js'));
const bytes=v=>Buffer.byteLength(JSON.stringify(v),'utf8');
const hash=v=>crypto.createHash('sha256').update(JSON.stringify(v)).digest('hex');
function draft(i){return {schema:F.GRID_RULE_SCHEMA,draftId:'d-'+i,kind:'source',intent:'edit',
  baseRef:{kind:'grid-system',id:i,fingerprint:'f'.repeat(64)},
  inputRefs:[{kind:'parameter-field',parameterId:2,fieldId:1,fingerprint:'f'.repeat(64)}],
  rawForm:Object.fromEntries(F.sourceFields.map(k=>[k,''])),ruleDraft:{intent:'create',ruleKey:null,rawForm:Object.fromEntries(F.ruleFields.map(k=>[k,'']))}};}
function fill(drafts,container,target){
  for(const d of drafts)for(const form of [d.rawForm,d.ruleDraft.rawForm])for(const key of Object.keys(form)){
    const delta=Math.min(target-bytes(container),131072-bytes(d),12288);
    if(delta<=0)continue;
    const n=Math.floor(delta/3),rem=delta%3;form[key]='甲'.repeat(n)+(rem===2?'é':rem===1?'a':'');
    if(form[key].length>4096)throw Error('string limit');
  }
  if(bytes(container)!==target)throw Error('cannot reach requested byte boundary');
  drafts.forEach(d=>F.validateGridDraft(d)); // Actual original single-draft validator, not a collection runtime claim.
}
const single=draft(1);fill([single],single,131072);
const oneMarked=structuredClone(single);oneMarked.inputRefs[0].lost=true;
let markedRejected=false,markedError=null;try{F.validateGridDraft(oneMarked);}catch(e){markedRejected=true;markedError=e.message;}
if(!markedRejected||bytes(oneMarked)!==131084)throw Error('single boundary witness changed');
const drafts=Array.from({length:9},(_,i)=>draft(i+1));
const record={kind:'grid-draft',schema:'grid-editor-drafts/1',value:{schema:'grid-editor-drafts/1',drafts,orphans:[]}};
fill(drafts,record,1048576);const marked=structuredClone(record);marked.value.drafts.forEach(d=>d.inputRefs[0].lost=true);
if(bytes(marked)!==1048684)throw Error('collection boundary witness changed');
const allOrphan=structuredClone(marked);allOrphan.value.orphans=allOrphan.value.drafts.map(d=>d.draftId);
console.log(JSON.stringify({scope:'Original single-draft validator acceptance plus finite JSON byte arithmetic; no collection runtime, World deletion, save/reopen or Undo/Redo execution',
  single:{before_bytes:bytes(single),marked_bytes:bytes(oneMarked),automatic_lost_delta:12,unmarked_single_validator:'accepted',marked_single_validator:'rejected',marked_error:markedError,sha256:hash(single)},
  collection:{draft_count:9,before_record_bytes:bytes(record),marked_record_bytes:bytes(marked),automatic_lost_delta:108,all_orphan_record_bytes:bytes(allOrphan),
    individual_draft_bytes:drafts.map(bytes),every_unmarked_draft_original_validator:'accepted',record_sha256:hash(record),marked_record_sha256:hash(marked)},
  raw_preserved:JSON.stringify(single.rawForm)===JSON.stringify(oneMarked.rawForm),string_limits:'All raw/rule strings <=4096 UTF-16 code units'},null,2));
