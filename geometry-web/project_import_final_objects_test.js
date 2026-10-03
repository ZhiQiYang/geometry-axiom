/* Loaded by cdp_test.js. Public PNG, real ZIP/native service and real file input. */
const fs=require('fs'),os=require('os'),path=require('path');
module.exports=async({read,send,until,check,doUndoRedo})=>{
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-final-objects-'));
  try {
    const fixtures=await read(String.raw`(async()=>{
      const canvas=document.createElement('canvas');canvas.width=32;canvas.height=24;
      const ctx=canvas.getContext('2d');ctx.fillStyle='#317873';ctx.fillRect(0,0,32,24);
      const bytes=new Uint8Array(await (await new Promise(r=>canvas.toBlob(r,'image/png'))).arrayBuffer()),P=GeometryProject,hash=await P.sha(bytes);
      const page={id:'public-page',sourceId:hash,page:1,imgW:32,imgH:24,crop:[0,0,32,24],mmPerPx:10,x:-10,y:20,rot:90,opacity:.5,locked:true,
        calibration:{points:[[0,0],[10,0]],distanceMm:100,inputValue:100,inputUnit:'mm'},reviewRequired:true,records:[{id:'public-note',label:'Public note',value:null,unit:'mm',datum:'FFL',location:''}]};
      const projection={kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'};
      const scene='boundary 1 outline 0,0 800,0 800,700 0,700\nplacement 0 on boundary 1 origin 0 0 0 u +x v +y\ncanvas-pos boundary 1 900 900\n';
      const manifest={projectId:'public-final-base',name:'Public final objects',sources:[{id:hash,hash,name:'public.png',type:'image/png',size:bytes.length,path:'sources/'+hash}],faces:[{bid:1,activePageId:page.id,pages:[page]}],models:[],faceProjections:[{bid:1,placement_id:0,projection}],
        reconstructionReviews:[{bid:1,pageId:page.id,basis:P.reviewBasis(page),geometry:P.outlineFingerprint([{verts:[[0,0],[800,0],[800,700],[0,700]],fixity:[1,1,1,1]}]),method:'manual',warnings:[],confirmedAt:'2026-10-03T00:00:00.000Z'}]};
      const packed=await P.pack(scene,manifest,new Map([[hash,bytes]]),fflate),fixtures={};
      const scenes={base:scene,trim:scene.split('\n').map(l=>'  '+l).join('\n'),reset:scene+'reset\n',deleted:scene+'delete placement 0\ndelete boundary 1\n',
        projectionDeleted:scene+'delete placement 0\n',vertical:scene+'placement 0 on boundary 1 origin 0 0 0 u +x v +z\n',
        reassigned:scene+'boundary 2 outline 0,0 800,0 800,700 0,700\nplacement 0 on boundary 2 origin 0 0 0 u +x v +y\n',
        redeclared:scene+'delete placement 0\ndelete boundary 1\n'+scene,
        finalExisting:scene+'boundary 2 outline 0,0 80,0 80,70 0,70\ndelete boundary 2\n',
        zeroBoundary:scene.replace('boundary 1 outline','boundary 0 outline')};
      for(const [name,text]of Object.entries(scenes)){
        const entries=fflate.unzipSync(packed),m=JSON.parse(new TextDecoder().decode(entries['manifest.json']));
        m.projectId='public-final-'+name;entries['world.scene']=new TextEncoder().encode(text);m.sceneHash=await P.sha(entries['world.scene']);
        entries['manifest.json']=new TextEncoder().encode(JSON.stringify(m));fixtures[name]=Array.from(fflate.zipSync(entries));
      }
      window.__finalExpected={bytes:Array.from(bytes),faces:manifest.faces,faceProjections:manifest.faceProjections,reviews:manifest.reconstructionReviews};
      window.__finalSnapshot=async()=>{
        const m=await ReferenceWorkspace.manifest(),sourceBytes=[...ReferenceWorkspace.context().sources].map(([id,s])=>[id,Array.from(s.bytes)]);
        return {scene:(await api('dump')).text,id:ReferenceWorkspace.context().id,faces:m.faces,projections:m.faceProjections,reviews:m.reconstructionReviews,sourceBytes,
          undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length};
      };
      return fixtures;
    })()`);
    const open=async name=>{
      const filename=path.join(directory,name+'.gcanvas');fs.writeFileSync(filename,Buffer.from(fixtures[name]));
      const doc=await send('DOM.getDocument'),input=await send('DOM.querySelector',{nodeId:doc.result.root.nodeId,selector:'#projectFile'});
      await send('DOM.setFileInputFiles',{nodeId:input.result.nodeId,files:[filename]});
      await until(`!ReferenceWorkspace.busy`);
    };
    for(const name of ['base','trim','redeclared','finalExisting']) {
      await open(name);
      check('P61 QR2 '+name+' PNG/ZIP native final targets retain exact assets and metadata',await read(`(async()=>{
        const loaded=await GeometryProject.unpack(await ReferenceWorkspace.exportBytes(),fflate),m=loaded.manifest,e=__finalExpected;
        return ReferenceWorkspace.context().id==='public-final-${name}'&&m.sources.length===1&&
          JSON.stringify(Array.from(loaded.sources.values().next().value))===JSON.stringify(e.bytes)&&
          JSON.stringify(m.faces)===JSON.stringify(e.faces)&&JSON.stringify(m.faceProjections)===JSON.stringify(e.faceProjections)&&
          JSON.stringify(m.reconstructionReviews)===JSON.stringify(e.reviews)&&(await api('dump')).text.includes('canvas-pos boundary 1 900 900');
      })()`));
    }
    for(const name of ['reset','deleted','projectionDeleted','vertical','reassigned','zeroBoundary']) {
      await read(`(async()=>window.__finalBefore=JSON.stringify(await __finalSnapshot()))()`);await open(name);
      check('P61 QR2 '+name+' rejects before context/World/history replacement',await read(`(async()=>
        $('status').textContent.includes('未能完成')&&JSON.stringify(await __finalSnapshot())===__finalBefore)()`));
    }
    const before=await read(`(async()=>JSON.stringify(await __finalSnapshot()))()`);
    await open('trim');
    await doUndoRedo('undo');
    check('P61 QR2 import undo restores original bytes references and World',await read(`(async()=>{const a=await __finalSnapshot(),b=JSON.parse(${JSON.stringify(before)});return a.id===b.id&&a.scene===b.scene&&JSON.stringify(a.faces)===JSON.stringify(b.faces)&&JSON.stringify(a.sourceBytes)===JSON.stringify(b.sourceBytes);})()`));
    await doUndoRedo('redo');
    check('P61 QR2 redo restores placement ID0 projection and source bytes',await read(`ReferenceWorkspace.context().id==='public-final-trim'&&ReferenceWorkspace.getFaceProjection(1,0)?.view==='top'&&ReferenceWorkspace.active(1)?.sourceId===__finalExpected.faces[0].pages[0].sourceId`));
  } finally {fs.rmSync(directory,{recursive:true,force:true});}
};
