/* #54: local, non-authoritative room proposals. PDF paths stay vector paths. */
(function(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.RoomOutline = api;
})(globalThis, function() {
  'use strict';
  const EPS = 1e-5;
  const error = (code, message) => Object.assign(new Error(message), {code});
  const point = (m, x, y) => [m[0]*x+m[2]*y+m[4], m[1]*x+m[3]*y+m[5]];
  const multiply = (a,b) => [a[0]*b[0]+a[2]*b[1],a[1]*b[0]+a[3]*b[1],a[0]*b[2]+a[2]*b[3],a[1]*b[2]+a[3]*b[3],a[0]*b[4]+a[2]*b[5]+a[4],a[1]*b[4]+a[3]*b[5]+a[5]];
  const near = (a,b) => Math.abs(a-b)<EPS;
  function orthogonal(points) {
    return points.length>=4 && points.every((a,i)=>{const b=points[(i+1)%points.length];return (near(a[0],b[0])!==near(a[1],b[1]));});
  }
  function simplify(points) {
    let next=points;
    for(;;) {
      const result=next.filter((b,i)=>{const a=next[(i+next.length-1)%next.length],c=next[(i+1)%next.length];return !(near(a[0],b[0])&&near(b[0],c[0]) || near(a[1],b[1])&&near(b[1],c[1]));});
      if(result.length===next.length || result.length<4)return next;
      next=result;
    }
  }
  function contains(poly,p) {
    let inside=false;
    for(let i=0,j=poly.length-1;i<poly.length;j=i++) {
      const a=poly[i],b=poly[j];
      if((a[1]>p[1])!==(b[1]>p[1]) && p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])inside=!inside;
    }
    return inside;
  }
  // PDF.js 6.3.289 constructPath(op, [Float32Array DrawOPS], minMax).
  // The OPLIST intent keeps these arrays separate from render's cached Path2D.
  // Text, images and Bezier door arcs never become room boundary segments.
  function pdfObstacles(list, OPS, viewport, {minWidth=1,minLength=8}={}) {
    if(list.fnArray.length>200000)throw error('capacity','PDF 向量過多，請縮小取景或改用影像輔助。');
    const boxes=[], fills=[], widths=[], warnings=[];
    let state={matrix:[...viewport.transform],width:1,dash:false,clip:false,stroke:'#000000',fill:'#000000',strokeAlpha:1,fillAlpha:1}, stack=[], curved=0,diagonal=0,unsupported=0;
    const dark=color=>{if(color==='transparent')return false;const m=/^#([a-f0-9]{6})$/i.exec(color);return !!m&&(parseInt(m[1].slice(0,2),16)*.299+parseInt(m[1].slice(2,4),16)*.587+parseInt(m[1].slice(4,6),16)*.114)<180;};
    function path(data,paint) {
      if(!ArrayBuffer.isView(data)&&!Array.isArray(data)){unsupported++;return;}
      if(data.length>600000)throw error('capacity','PDF 路徑過大，請改用影像輔助或人工描繪。');
      const loops=[];let pts=[],first=null,last=null,hasCurve=false;
      const finish=()=>{if(pts.length)loops.push({pts,hasCurve});pts=[];first=last=null;hasCurve=false;};
      const segment=p=>{if(last)pts.push(p);else {pts=[p];first=p;}last=p;};
      for(let at=0;at<data.length;) {
        const op=data[at++];
        if(op===0){finish();segment(point(state.matrix,data[at++],data[at++]));}
        else if(op===1)segment(point(state.matrix,data[at++],data[at++]));
        else if(op===2 || op===3){const n=op===2?6:4;at+=n;hasCurve=true;curved++;segment(point(state.matrix,data[at-2],data[at-1]));}
        else if(op===4){if(first)segment(first);finish();}
        else {unsupported++;return;}
      }
      finish();
      const stroke=dark(state.stroke)&&state.strokeAlpha>.5&&[OPS.stroke,OPS.closeStroke,OPS.fillStroke,OPS.eoFillStroke,OPS.closeFillStroke,OPS.closeEOFillStroke].includes(paint);
      const fill=dark(state.fill)&&state.fillAlpha>.5&&[OPS.fill,OPS.eoFill,OPS.fillStroke,OPS.eoFillStroke,OPS.closeFillStroke,OPS.closeEOFillStroke].includes(paint);
      if(fill&&loops.length>1)unsupported++; // compound fill rules are not guessed
      const width=state.width*Math.sqrt(Math.abs(state.matrix[0]*state.matrix[3]-state.matrix[1]*state.matrix[2]));
      const mx=Math.hypot(state.matrix[0],state.matrix[1]),my=Math.hypot(state.matrix[2],state.matrix[3]);
      // An anisotropic/skewed pen has direction-dependent width. Do not
      // mislabel a guessed offset as the inner edge; raster fallback retains it.
      if(stroke&&(!near(mx,my)||Math.abs(state.matrix[0]*state.matrix[2]+state.matrix[1]*state.matrix[3])>EPS*mx*my))throw error('transform','PDF 描邊有非等比例／斜切變換，改用影像輔助核對內緣。');
      if(stroke&&!state.dash)widths.push(width);
      for(const loop of loops) {
        if(loop.hasCurve)continue;
        if(fill&&loops.length===1) {
          let p=loop.pts;
          if(p.length>1&&near(p[0][0],p.at(-1)[0])&&near(p[0][1],p.at(-1)[1]))p=p.slice(0,-1);
          if(orthogonal(p))fills.push(p);else diagonal++;
        }
        if(!stroke||state.dash||width<minWidth)continue;
        for(let i=1;i<loop.pts.length;i++) {
          const a=loop.pts[i-1],b=loop.pts[i];
          if(!near(a[0],b[0])&&!near(a[1],b[1])){diagonal++;continue;}
          if(Math.hypot(b[0]-a[0],b[1]-a[1])<minLength)continue;
          boxes.push([Math.min(a[0],b[0])-width/2,Math.min(a[1],b[1])-width/2,Math.max(a[0],b[0])+width/2,Math.max(a[1],b[1])+width/2]);
          if(boxes.length>12000)throw error('capacity','PDF 正交線段過多，請提高門檻或改用影像輔助。');
        }
      }
    }
    for(let i=0;i<list.fnArray.length;i++) {
      const op=list.fnArray[i],args=list.argsArray[i];
      if(op===OPS.save||op===OPS.paintFormXObjectBegin){stack.push(structuredClone(state));if(op===OPS.paintFormXObjectBegin){if(args[0])state.matrix=multiply(state.matrix,args[0]);if(args[1])state.clip=true;}}
      else if(op===OPS.restore||op===OPS.paintFormXObjectEnd)state=stack.pop()||state;
      else if(op===OPS.transform)state.matrix=multiply(state.matrix,args);
      else if(op===OPS.setLineWidth)state.width=args[0];
      else if(op===OPS.setDash)state.dash=!!args[0]?.length;
      else if(op===OPS.setStrokeRGBColor)state.stroke=args[0];
      else if(op===OPS.setFillRGBColor)state.fill=args[0];
      else if(op===OPS.setStrokeTransparent)state.stroke='transparent';
      else if(op===OPS.setFillTransparent)state.fill='transparent';
      else if(op===OPS.clip||op===OPS.eoClip)state.clip=true;
      else if(op===OPS.setGState){for(const [key,value] of args[0]||[]){if(key==='LW')state.width=value;if(key==='D')state.dash=!!value[0]?.length;if(key==='CA')state.strokeAlpha=value;if(key==='ca')state.fillAlpha=value;}}
      else if(op===OPS.constructPath){if(state.clip){unsupported++;continue;}path(args[1]?.[0],args[0]);}
      else if(op===OPS.rawFillPath){unsupported++;}
    }
    if(curved)warnings.push('已排除曲線／門扇弧；若曲線是牆，請取消並人工處理，不可改成直角。');
    if(diagonal)warnings.push('有斜線未納入；請確認不是斜牆，候選只支援正交房間。');
    if(unsupported)warnings.push('有裁切、填色或不支援的向量未納入；需檢查缺邊，必要時改用影像輔助。');
    return {boxes,fills,widths,warnings,method:'pdf-vector'};
  }
  // Long dark horizontal/vertical strokes; thin dimensions/grid and small text
  // are excluded by explicit width/length thresholds. No gap closing is applied.
  function imageObstacles(image,{minWidth=2,minLength=24,threshold=110}={}) {
    const {width:w,height:h,data}=image;
    if(w*h>4000000)throw error('capacity','影像分析超過 400 萬像素，請縮小取景。');
    const dark=new Uint8Array(w*h);
    for(let i=0;i<dark.length;i++){const a=data[i*4+3]/255;dark[i]=(data[i*4]*.299+data[i*4+1]*.587+data[i*4+2]*.114)*a+255*(1-a)<threshold?1:0;}
    const boxes=[];
    function scan(vertical) {
      const rows=vertical?w:h,columns=vertical?h:w;
      let previous=new Map();
      for(let r=0;r<=rows;r++) {
        const current=new Map();
        for(let c=0;c<columns&&r<rows;) {
          const get=x=>dark[vertical?x*w+r:r*w+x];
          if(!get(c)){c++;continue;}
          const start=c;while(c<columns&&get(c))c++;
          if(c-start<minLength)continue;
          const key=start+':'+c,old=previous.get(key);current.set(key,old?{...old,end:r+1}:{start,end:r+1,first:r,last:c});
        }
        for(const [key,run] of previous)if(!current.has(key)&&run.end-run.first>=minWidth)
          boxes.push(vertical?[run.first,run.start,run.end,run.last]:[run.start,run.first,run.last,run.end]);
        previous=current;
      }
    }
    scan(false);scan(true);
    return {boxes,fills:[],warnings:['影像暗線不是精確量測；薄線、文字與弧線可能被排除，需逐邊核對室內淨範圍。'],method:'image-lines'};
  }
  function region(obstacles,seed,crop,multiple=false) {
    const [left,top,width,height]=crop,right=left+width,bottom=top+height;
    if(!crop.every(Number.isFinite)||width<=0||height<=0||!multiple&&(seed[0]<=left||seed[0]>=right||seed[1]<=top||seed[1]>=bottom))throw error('seed','請點選取景範圍內的房間空白處。');
    const boxes=obstacles.boxes.filter(b=>b[2]>left&&b[0]<right&&b[3]>top&&b[1]<bottom).map(b=>[Math.max(left,b[0]),Math.max(top,b[1]),Math.min(right,b[2]),Math.min(bottom,b[3])]);
    const fills=obstacles.fills||[];
    const xs=new Set([left,right]),ys=new Set([top,bottom]);
    for(const b of boxes){xs.add(b[0]);xs.add(b[2]);ys.add(b[1]);ys.add(b[3]);}
    for(const p of fills.flat()){if(p[0]>left&&p[0]<right)xs.add(p[0]);if(p[1]>top&&p[1]<bottom)ys.add(p[1]);}
    const x=[...xs].sort((a,b)=>a-b),y=[...ys].sort((a,b)=>a-b),nx=x.length-1,ny=y.length-1;
    if(nx*ny>150000||boxes.length>12000||fills.length>2000||nx*ny*fills.reduce((n,p)=>n+p.length,0)>5000000)throw error('capacity','目標區域線段過多，請縮小取景或提高線寬／最短線門檻。');
    const blocked=new Uint8Array(nx*ny);
    const xi=new Map(x.map((v,i)=>[v,i])),yi=new Map(y.map((v,i)=>[v,i]));
    // Exact union on the same compressed coordinates: four updates per box
    // and one prefix pass, rather than repainting every overlapped cell.
    const stride=nx+1,coverage=new Int32Array(stride*(ny+1));
    for(const b of boxes) {
      const x0=xi.get(b[0]),x1=xi.get(b[2]),y0=yi.get(b[1]),y1=yi.get(b[3]);
      coverage[y0*stride+x0]++;coverage[y0*stride+x1]--;
      coverage[y1*stride+x0]--;coverage[y1*stride+x1]++;
    }
    for(let j=0;j<ny;j++)for(let i=0;i<nx;i++) {
      const n=j*stride+i;
      coverage[n]+=(i?coverage[n-1]:0)+(j?coverage[n-stride]:0)-(i&&j?coverage[n-stride-1]:0);
      blocked[j*nx+i]=coverage[n]>0?1:0;
    }
    if(fills.length)for(let j=0;j<ny;j++)for(let i=0;i<nx;i++)if(fills.some(p=>contains(p,[(x[i]+x[i+1])/2,(y[j]+y[j+1])/2])))blocked[j*nx+i]=1;
    const visited=new Uint8Array(nx*ny),components=[];
    function component(start) {
    const seen=new Set(),queue=[];
    if(blocked[start])throw error('wall','選點落在線條／牆體上，請改點房間內空白處。');
    seen.add(start);visited[start]=1;queue.push(start);let open=false;
    for(let at=0;at<queue.length;at++) {
      const n=queue[at],i=n%nx,j=Math.floor(n/nx);
      if(i===0||j===0||i===nx-1||j===ny-1)open=true;
      for(const nn of [i>0?n-1:-1,i+1<nx?n+1:-1,j>0?n-nx:-1,j+1<ny?n+nx:-1])if(nn>=0&&!blocked[nn]&&!seen.has(nn)){seen.add(nn);visited[nn]=1;queue.push(nn);}
    }
    if(open){if(multiple)return null;throw error('open-region','區域連到取景邊緣：可能有門洞、漏邊或斜／弧牆。未補牆；請補明確分隔線後重取，或人工描繪。');}
    // Oriented boundary of the exact connected cells; preserve every reentrant corner.
    const edges=new Map();
    const add=(a,b)=>{const key=a.join(',');if(edges.has(key))throw error('ambiguous','候選在角點分岔，請修正分隔後重取。');edges.set(key,b);};
    for(const n of queue) {
      const i=n%nx,j=Math.floor(n/nx),a=[x[i],y[j]],b=[x[i+1],y[j]],c=[x[i+1],y[j+1]],d=[x[i],y[j+1]];
      if(!seen.has(n-nx))add(a,b);if(!seen.has(n+1))add(b,c);if(!seen.has(n+nx))add(c,d);if(!seen.has(n-1))add(d,a);
    }
    const loops=[];
    while(edges.size) {
      const first=edges.keys().next().value,loop=[];let key=first;
      do {loop.push(key.split(',').map(Number));const next=edges.get(key);if(!next)throw error('open-loop','候選未閉合。');edges.delete(key);key=next.join(',');}while(key!==first);
      loops.push(simplify(loop));
    }
    const sample=[(x[start%nx]+x[start%nx+1])/2,(y[Math.floor(start/nx)]+y[Math.floor(start/nx)+1])/2];
    const outer=loops.filter(p=>contains(p,multiple?sample:seed));
    if(outer.length!==1)throw error('ambiguous','存在多個可能外環，請縮小範圍／加分隔後重取。');
    const warnings=[...(obstacles.warnings||[]),'此區域可能包含連通的相鄰房間；請逐邊核對門洞、凹口及牆內緣。'];
    if(loops.length>1)warnings.push('內部有孤立障礙／線條；本次只取外環，不把它們猜成孔洞或柱體。');
    return {points:outer[0],method:obstacles.method,warnings,holes:loops.length-1,
      ...(multiple?{vertexCount:loops.reduce((n,p)=>n+p.length,0)}:{})};
    }
    if(!multiple) {
      const sx=x.findIndex((v,i)=>i<nx&&seed[0]>=v&&seed[0]<x[i+1]),sy=y.findIndex((v,i)=>i<ny&&seed[1]>=v&&seed[1]<y[i+1]);
      return component(sy*nx+sx);
    }
    let vertices=0;
    for(let start=0;start<blocked.length;start++)if(!blocked[start]&&!visited[start]) {
      const c=component(start);if(!c)continue;
      vertices+=c.vertexCount;
      if(components.length===64||c.points.length>256||vertices>16384)throw error('capacity','同頁候選超過 64 個封閉分量、每區 256 頂點或總 16384 頂點；請縮小來源取景後重取。');
      components.push(c);
    }
    // A frame inside another enclosed component is an obstacle, not evidence
    // of another room. Examine the complete set before applying the display cap.
    const rooms=components.filter(c=>!components.some(other=>other!==c&&contains(other.points,c.points[0])));
    const unique=[...new Map(rooms.map(c=>[canonicalLoop(c.points),{...c,key:canonicalLoop(c.points)}])).values()];
    unique.sort((a,b)=>Math.min(...a.points.map(p=>p[1]))-Math.min(...b.points.map(p=>p[1]))||Math.min(...a.points.map(p=>p[0]))-Math.min(...b.points.map(p=>p[0]))||a.key.localeCompare(b.key));
    return {candidates:unique.slice(0,12),total:unique.length,complete:unique.length<=12,ignoredNested:components.length-rooms.length,method:obstacles.method,crop:[...crop]};
  }
  function canonicalLoop(points) {
    const versions=[];
    for(const p of [points,[...points].reverse()])for(let i=0;i<p.length;i++)versions.push(JSON.stringify([...p.slice(i),...p.slice(0,i)]));
    return versions.sort()[0];
  }
  function integerProposal(points) {
    if(!orthogonal(points))throw error('diagonal','候選含斜邊／零長邊，不能偷偷正交化。');
    const rounded=points.map(p=>p.map(Math.round));
    if(!orthogonal(rounded))throw error('precision','整數 mm 修整會使邊退化，請人工輸入尺寸。');
    const deviation=Math.max(...points.flatMap((p,i)=>p.map((v,a)=>Math.abs(v-rounded[i][a]))));
    return {points:rounded,deviation};
  }
  // Explicit draft operation: move one edge and both endpoints, retaining its
  // neighboring orthogonal edges. Inserting a notch uses the same point editor.
  function resizeEdge(points,index,length) {
    if(!Number.isSafeInteger(length)||length<=0||length>1e8)throw error('dimension','核對尺寸須為正整數 mm。');
    const next=points.map(p=>[...p]),a=next[index],j=(index+1)%next.length,b=next[j],axis=a[0]===b[0]?1:0;
    const coordinate=a[axis]+Math.sign(b[axis]-a[axis])*length,following=next[(j+1)%next.length];
    b[axis]=coordinate;following[axis]=coordinate;
    if(!orthogonal(next))throw error('dimension','此尺寸使相鄰邊退化，請調整頂點。');
    return next;
  }
  // Source geometry for manual tracing, independent of room inference. These
  // are painted path centreline points, never labelled as wall/inside corners.
  function pdfSnapFeatures(list, OPS, viewport) {
    if(list.fnArray.length>200000)throw error('capacity','PDF 向量超過吸附容量，請人工描繪。');
    const segments=[];let state={matrix:[...viewport.transform],clip:false,dash:false,alpha:1,transparent:false,text:false,textMode:0,mask:false},stack=[],marked=[],groups=0;
    const paints=[OPS.stroke,OPS.closeStroke,OPS.fillStroke,OPS.eoFillStroke,OPS.closeFillStroke,OPS.closeEOFillStroke];
    for(let i=0;i<list.fnArray.length;i++) {
      const op=list.fnArray[i],a=list.argsArray[i];
      if(op===OPS.beginMarkedContent||op===OPS.beginMarkedContentProps)marked.push(marked.at(-1)===true || op===OPS.beginMarkedContentProps&&a[0]==='OC');
      else if(op===OPS.endMarkedContent)marked.pop();
      else if(op===OPS.beginGroup||op===OPS.beginAnnotation){stack.push({...state,matrix:[...state.matrix]});groups++;}
      else if(op===OPS.endGroup||op===OPS.endAnnotation){state=stack.pop()||state;groups=Math.max(0,groups-1);}
      else if(op===OPS.save||op===OPS.paintFormXObjectBegin){stack.push({...state,matrix:[...state.matrix]});if(op===OPS.paintFormXObjectBegin){if(a[0])state.matrix=multiply(state.matrix,a[0]);if(a[1])state.clip=true;}}
      else if(op===OPS.restore||op===OPS.paintFormXObjectEnd)state=stack.pop()||state;
      else if(op===OPS.transform)state.matrix=multiply(state.matrix,a);
      else if(op===OPS.clip||op===OPS.eoClip)state.clip=true;
      else if(op===OPS.setDash)state.dash=!!a[0]?.length;
      else if(op===OPS.setStrokeTransparent)state.transparent=true;
      else if(op===OPS.setStrokeRGBColor)state.transparent=false;
      // Glyph clipping (text modes 4..7) persists after ET until Q. We do
      // not reconstruct glyph outlines or annotation-local transforms.
      else if(op===OPS.setTextRenderingMode){state.textMode=a[0];if(state.text && a[0]>=4 && a[0]<=7)state.clip=true;}
      else if(op===OPS.beginText){state.text=true;if(state.textMode>=4 && state.textMode<=7)state.clip=true;}
      else if(op===OPS.endText)state.text=false;
      else if(op===OPS.setGState){for(const [k,v] of a[0]||[]){if(k==='CA')state.alpha=v;if(k==='D')state.dash=!!v[0]?.length;if(k==='SMask')state.mask=!!v;}}
      else if(op===OPS.constructPath && !groups && !marked.at(-1) && !state.mask && !state.clip && !state.text && !state.dash && !state.transparent && state.alpha>0 && paints.includes(a[0])) {
        const data=a[1]?.[0];if(!data || data.length>600000)throw error('capacity','PDF 路徑超過吸附容量，請人工描繪。');
        let pts=[],curved=false,part=0;
        const finish=(closed=false)=>{
          if(!curved)for(let j=1;j<pts.length;j++)if(pts[j-1].every(Number.isFinite)&&pts[j].every(Number.isFinite)&&Math.hypot(pts[j][0]-pts[j-1][0],pts[j][1]-pts[j-1][1])>EPS)
            segments.push({a:pts[j-1],b:pts[j],closed,path:`${i}:${part}`,id:`${i}:${part}:${j-1}`});
          if(segments.length>12000)throw error('capacity','PDF 線段超過吸附容量，請人工描繪。');
          pts=[];curved=false;part++;
        };
        for(let at=0;at<data.length;) {
          const draw=data[at++];
          if(draw===0){finish();pts.push(point(state.matrix,data[at++],data[at++]));}
          else if(draw===1)pts.push(point(state.matrix,data[at++],data[at++]));
          else if(draw===2||draw===3){at+=draw===2?6:4;curved=true;}
          else if(draw===4){if(pts.length)pts.push(pts[0]);finish(true);}
          else {curved=true;break;}
        }
        if([OPS.closeStroke,OPS.closeFillStroke,OPS.closeEOFillStroke].includes(a[0]) && pts.length){pts.push(pts[0]);finish(true);}else finish();
      }
    }
    return {segments};
  }
  function nearestSnap(features, free, {map,zoom,crop,pts=[],radiusPx=8}) {
    if(!(zoom>0)||!features)return null;
    const radius=radiusPx/zoom, candidates=[],nearSegments=[];
    const inside=p=>!crop || p[0]>=crop[0]&&p[1]>=crop[1]&&p[0]<=crop[0]+crop[2]&&p[1]<=crop[1]+crop[3];
    const offer=(source,segments,kind)=>{
      if(!inside(source))return;
      const exact=map(source),mm=exact.map(Math.round),last=pts.at(-1);
      // Preserve exact existing orthogonal draft axes; never project a PDF
      // point onto an invented corner just to make it fit the draft.
      if(last && mm[0]!==last[0] && mm[1]!==last[1])return;
      const distance=Math.hypot(exact[0]-free[0],exact[1]-free[1]);
      if(distance<=radius)candidates.push({point:mm,exact,source,segments,kind,distance});
    };
    for(const s of features.segments) {
      offer(s.a,[s],'endpoint');offer(s.b,[s],'endpoint');
      if(!s.closed)continue; // open dimension/extension strokes cannot create crossing targets
      const a=map(s.a),b=map(s.b),dx=b[0]-a[0],dy=b[1]-a[1],t=Math.max(0,Math.min(1,((free[0]-a[0])*dx+(free[1]-a[1])*dy)/(dx*dx+dy*dy)));
      if(Math.hypot(a[0]+t*dx-free[0],a[1]+t*dy-free[1])<=radius)nearSegments.push(s);
    }
    if(nearSegments.length<=100)for(let i=0;i<nearSegments.length;i++)for(let j=i+1;j<nearSegments.length;j++) {
      const s=nearSegments[i],t=nearSegments[j],r=[s.b[0]-s.a[0],s.b[1]-s.a[1]],v=[t.b[0]-t.a[0],t.b[1]-t.a[1]],q=[t.a[0]-s.a[0],t.a[1]-s.a[1]],det=r[0]*v[1]-r[1]*v[0];
      if(Math.abs(det)<EPS)continue;
      const u=(q[0]*v[1]-q[1]*v[0])/det,w=(q[0]*r[1]-q[1]*r[0])/det;
      if(u>=0&&u<=1&&w>=0&&w<=1)offer([s.a[0]+u*r[0],s.a[1]+u*r[1]],[s,t],'intersection');
    }
    candidates.sort((a,b)=>a.distance-b.distance);
    return candidates[0]||null;
  }
  return {pdfSnapFeatures,nearestSnap,pdfObstacles,imageObstacles,region,regions:(obstacles,crop)=>region(obstacles,null,crop,true),canonicalLoop,integerProposal,resizeEdge,orthogonal,contains,multiply,point};
});
