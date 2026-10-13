// Read-only observation around the canonical P75 drag function. No actions,
// coordinates, original assertions, handlers or native commands are replaced.
const fs=require('fs'),path=require('path'),Module=require('module');
const load=Module._load,root=path.resolve(process.env.GEOMETRY_VERIFY_ROOT);
const target=path.join(root,'geometry-web','selection_cursor_test.js');
const output=path.resolve(process.env.GEOMETRY_P75_DIAGNOSTIC_OUT);
let sequence=0;
Module._load=function(request,parent,isMain){
  const value=load.apply(this,arguments);
  const resolved=Module._resolveFilename(request,parent,isMain);
  if(resolved!==target||parent?.filename!==path.join(root,'geometry-web','cdp_test.js'))return value;
  Module._load=load;
  const override=path.resolve(process.env.GEOMETRY_P75_HARNESS_OVERRIDE);
  const variant=new Module(target,parent);variant.filename=target;variant.paths=Module._nodeModulePaths(path.dirname(target));
  variant._compile(fs.readFileSync(override,'utf8'),target);
  console.log('P75_HARNESS_OVERRIDE_SCOPE '+JSON.stringify({originalRepositoryPath:target,actualScratchModulePath:override,actualScratchModuleSha256:require('crypto').createHash('sha256').update(fs.readFileSync(override)).digest('hex'),scope:'Changed normal crossing route only; all original 37 predicates unchanged; no formal repository module acceptance claim'}));
  return async function(args){
    const original=args.drag;
    const drag=async(...points)=>{
      const index=sequence++,label='drag-'+index;
      fs.mkdirSync(output,{recursive:true});
      const nativeBefore=await args.eval_(`apiRequest('dump').then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r.text;})`);
      const before=await args.eval_(`(()=>{
        const rr=r=>({left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height});
        const node=e=>e?{tag:e.tagName,id:e.id,classes:String(e.className?.baseVal??e.className??''),faceHit:e.closest?.('[data-face-hit]')?.dataset.faceHit,button:e.closest?.('button')?.id,rect:rr(e.getBoundingClientRect())}:null;
        const vp=$('faceEditorViewport'),r=vp.getBoundingClientRect(),coords=${JSON.stringify(points)};
        const state=()=>({tool:fe.tool,selected:[...fe.timberSelection].sort((a,b)=>a-b),focus:oc.focus,edit:oc.edit&&{bid:oc.edit.bid,contextId:oc.edit.contextId},contextId:ReferenceWorkspace.context().id,marquee:canvasMarquee&&{scope:canvasMarquee.scope,cx:canvasMarquee.cx,cy:canvasMarquee.cy,point:canvasMarquee.point,end:canvasMarquee.end,moved:canvasMarquee.moved,pointerId:canvasMarquee.pointerId,candidateIds:canvasMarquee.candidates.map(c=>c.id)},lastPD:fe.lastPD&&{x:fe.lastPD.x,y:fe.lastPD.y,clientX:fe.lastPD.clientX,clientY:fe.lastPD.clientY},drag:fe.drag&&{kind:fe.drag.kind,id:fe.drag.id}});
        if(!window.__p75PointerDiagnostic){
          window.__p75PointerDiagnostic={rows:[],state};
          for(const type of ['pointerdown','pointerup','pointercancel','lostpointercapture'])document.addEventListener(type,event=>{
            const probe=window.__p75PointerDiagnostic,row={stage:'capture',type,eventTrusted:event.isTrusted,pointerId:event.pointerId,button:event.button,clientX:event.clientX,clientY:event.clientY,target:node(event.target),viewportContainsTarget:vp.contains(event.target),state:probe.state()};probe.rows.push(row);
            queueMicrotask(()=>probe.rows.push({...row,stage:'after-event',state:probe.state()}));
          },true);
        }
        window.__p75PointerDiagnostic.rows=[];
        return {coords,viewport:rr(r),camera:{panX:fe.panX,panY:fe.panY,zoom:fe.zoom,viewportSize:fe.viewportSize,fittedBounds:fe.fittedBounds},insets:feViewportInsets(r),state:state(),startHit:node(document.elementFromPoint(coords[0],coords[1])),endHit:node(document.elementFromPoint(coords[2],coords[3])),startInsideViewport:coords[0]>=r.left&&coords[0]<=r.right&&coords[1]>=r.top&&coords[1]<=r.bottom,endInsideViewport:coords[2]>=r.left&&coords[2]<=r.right&&coords[3]>=r.top&&coords[3]<=r.bottom,feedback:node($('fbButton')),fit:node($('feZoomFit')),controls:node(document.querySelector('.face-canvas-controls'))};
      })()`);
      console.log('P75_DRAG_DIAGNOSTIC_BEFORE '+JSON.stringify({index,...before}));
      const screenBefore=await args.send('Page.captureScreenshot',{format:'png'});
      fs.writeFileSync(path.join(output,label+'-before.png'),Buffer.from(screenBefore.result.data,'base64'));
      await original(...points);
      const after=await args.eval_(`(()=>{const p=window.__p75PointerDiagnostic;return {state:p.state(),events:p.rows,activeElement:document.activeElement?.id,feedbackHidden:$('fbPanel').hidden};})()`);
      const nativeAfter=await args.eval_(`apiRequest('dump').then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r.text;})`);
      const record={index,before,after,nativeBefore,nativeAfter,nativeByteEqual:nativeBefore===nativeAfter};
      fs.writeFileSync(path.join(output,label+'.json'),JSON.stringify(record,null,2)+'\n');
      console.log('P75_DRAG_DIAGNOSTIC_AFTER '+JSON.stringify({index,...after,nativeByteEqual:record.nativeByteEqual}));
      const screenAfter=await args.send('Page.captureScreenshot',{format:'png'});
      fs.writeFileSync(path.join(output,label+'-after.png'),Buffer.from(screenAfter.result.data,'base64'));
    };
    return variant.exports({...args,drag});
  };
};
