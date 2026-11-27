'use strict';
// stdin contains real native read/3 packets captured by test B16.
const fs=require('node:fs'),assert=require('node:assert/strict');
const {verifyReadRefusal}=require('../fixtures/framing_notch_scope_probe.cjs');
(async()=>{
 const packet=JSON.parse(fs.readFileSync(0,'utf8'));
 assert.deepEqual(packet.cases.map(row=>row.label),['U','holes'],'R03B_REAL_READ_CASES');
 const results=[];
 for(const row of packet.cases){assert.equal(row.read.ok,true,'R03B_REAL_READ_AVAILABLE');results.push(await verifyReadRefusal(row.read,row));}
 console.log(JSON.stringify({schema:'r03b-real-read-scope-proof/1',ok:true,cases:results}));
})().catch(error=>{console.error(error);process.exitCode=1;});
