const {test}=require('node:test'),assert=require('node:assert/strict');
const W=require('../geometry-web/cutting-workspace.js');
const settings=()=>({kerf:3,allowance:0,minRemnant:300,stockTypes:[{key:1,name:'木材',section:[27,33],material:null,length:3636,endTrim:5}],remnants:[],nextStockKey:2,nextRemnantKey:1});
const references=()=>({ok:true,sourceFingerprint:'a'.repeat(64),timbers:[{id:1,geometry:{surface:1,A:27,B:33,length:890,dir:'+v',side:'+n',origin:[0,0,0],axes:[[0,1,0],[1,0,0],[0,0,1]]}}],engineeringSources:[]});
function fixture(context){const f={state:{contextToken:'a',revision:1,...(context?{context}:{})},settings:settings(),refs:references(),downloads:[],reads:0};f.session=W.createSession({state:()=>({...f.state}),settings:()=>f.settings,references:async()=>{f.reads++;return f.refs;},download:csv=>f.downloads.push(csv)});f.session.addScope({surface:1,ids:null});return f;}
test('T14 plan, display and export are read-only; a single references response determines all scopes',async()=>{
 const f=fixture(),before=JSON.stringify([f.state,f.settings,f.refs]);f.session.addScope({surface:1,ids:[1]});const p=await f.session.calculate();assert.equal(p.status,'COMPLETE');assert.equal(f.reads,1);await f.session.exportCSV();assert.equal(f.downloads.length,1);assert.equal(JSON.stringify([f.state,f.settings,f.refs]),before);
});
for(const mode of ['world','settings','context','revision','scope'])test('T16 '+mode+' invalidates export without producing a Blob',async()=>{
 const f=fixture();await f.session.calculate();if(mode==='world')f.refs.sourceFingerprint='b'.repeat(64);if(mode==='settings')f.settings.kerf=4;if(mode==='context')f.state.contextToken='other';if(mode==='revision')f.state.revision++;if(mode==='scope')f.session.addScope({surface:2,ids:null});
 await assert.rejects(()=>f.session.exportCSV(),/已變更|過期|重新/);assert.equal(f.downloads.length,0);
});
test('T16 late references and repeated clicks produce zero or one download respectively',async()=>{
 const f=fixture();await f.session.calculate();let release;f.session.host.references=()=>new Promise(r=>release=r);const first=f.session.exportCSV(),second=f.session.exportCSV();let settled=false;second.then(()=>settled=true);await Promise.resolve();assert.equal(settled,true,'Repeated export must return immediately without another references read');assert.equal(await second,false);f.state.contextToken='other';release(f.refs);await assert.rejects(()=>first);assert.equal(f.downloads.length,0);
 const g=fixture();await g.session.calculate();let done;g.session.host.references=()=>new Promise(r=>done=r);const a=g.session.exportCSV(),b=g.session.exportCSV();assert.equal(await b,false);done(g.refs);assert.equal(await a,true);assert.equal(g.downloads.length,1);
});
test('session scopes clear at project context change and late calculation cannot install a plan',async()=>{
 const f=fixture();let release;f.session.host.references=()=>new Promise(r=>release=r);const p=f.session.calculate();f.state.contextToken='other';release(f.refs);await assert.rejects(()=>p,/已變更|過期/);assert.deepEqual(f.session.scopes,[]);assert.equal(f.session.plan,null);
});
test('invalid settings draft must be saved before calculation; no absent setting receives a default',async()=>{
 const f=fixture();f.settings.kerf=null;assert.equal((await f.session.calculate()).status,'INCOMPLETE');await assert.rejects(()=>f.session.exportCSV());assert.equal(f.downloads.length,0);
});
test('unrelated undo changes the frame receipt but keeps scopes in the same project context',async()=>{
 const f=fixture({});await f.session.calculate();f.state.contextToken='new-frame';f.state.revision++;assert.deepEqual(f.session.scopes,[{surface:1,ids:null}]);await assert.rejects(()=>f.session.exportCSV(),/已變更/);assert.equal(f.downloads.length,0);
});
test('T8b diagnostics identify the required section and complete native material key',()=>{
 assert.equal(typeof W.diagnosticText,'function','T8b UI must describe the missing stock dimensions and material key');
 const fingerprint='b'.repeat(64),text=W.diagnosticText({code:'NO_STOCK',detail:{timberId:10,section:[27,33],material:{id:'wood',version:2,fingerprint}}});
 for(const value of ['構件 10','27×33 mm','wood@2@'+fingerprint])assert.ok(text.includes(value),'T8b diagnostic omitted '+value);
 assert.ok(W.diagnosticText({code:'NO_STOCK',detail:{timberId:0,section:[33,27],material:null}}).includes('材料未設定'));
});
