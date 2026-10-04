/* Self-authored #77 public PDF/payload fixture; no test registration or owner shim. */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const S=require('../geometry-web/source-plane.js');
const scene='boundary 11 outline 1000,1000 5000,1000 5000,4000 1000,4000\n'+
  'boundary 22 outline 6600,1000 10600,1000 10600,4000 6600,4000\n';
const sha=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(byte=>byte.toString(16).padStart(2,'0')).join('');

async function fixture() {
  const bytes = new Uint8Array(fs.readFileSync(path.join(__dirname, 'fixtures/issue77-two-rooms.pdf')));
  const hash = await sha(bytes);
  const source = {id:hash, hash, name:'issue77-two-rooms.pdf', type:'application/pdf',
    size:bytes.length, path:'sources/' + hash};
  const payload = {
    schema:S.SCHEMA,
    planes:[{id:'plane-two-rooms', sourceId:hash, page:1, coordinateSpace:'pdf-page-viewport/1', pageSize:[600,400],
      calibration:{points:[[50,300],[250,300]], distanceMm:4000, inputValue:4000, inputUnit:'mm'},
      alignment:{x:0,y:0,mmPerPx:20,rotation:0}, basisRevision:1}],
    collections:[{id:'rooms-two-rooms', planeId:'plane-two-rooms', roomIds:['room-a','room-b']}],
    rooms:[
      {id:'room-a', name:'房間 A', boundaryRef:{kind:'boundary',id:11,associationPin:'87c60cb609c6cc35d9581dfdf3e93bf1412c593cf2e57609de3e79eab3080be6'}, acceptedBasisRevision:1, reviewState:'confirmed'},
      {id:'room-b', name:'房間 B', boundaryRef:{kind:'boundary',id:22,associationPin:'c4d24a57956514787686f997f8f970f6cd9e78b1d929010b7c8c732cf573444f'}, acceptedBasisRevision:1, reviewState:'confirmed'},
    ],
  };
  return {bytes, hash, source, payload, scene, sources:new Map([[hash,bytes]]),
    sourceMetadata:new Map([[hash,source]]),
    base:{projectId:'issue77-project',name:'自製雙房保存',sceneHash:await sha(new TextEncoder().encode(scene)),sources:[source],faces:[]}};
}

module.exports={fixture};
