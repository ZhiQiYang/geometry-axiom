/* Trial geometry is presentation only: no boundary, timber or placement is
 * constructed. Lines and stagger-band endpoints come from the native query. */
(function(root) {
  'use strict';
  const intersect=(a,b)=>{const r=[Math.max(a[0],b[0]),Math.max(a[1],b[1]),Math.min(a[2],b[2]),Math.min(a[3],b[3])];return r[0]<r[2]&&r[1]<r[3]?r:null;};
  const area=r=>r?(r[2]-r[0])*(r[3]-r[1]):0;
  function unionArea(rects) {
    const xs=[...new Set(rects.flatMap(r=>[r[0],r[2]]))].sort((a,b)=>a-b);let sum=0;
    for(let i=1;i<xs.length;i++) {const spans=rects.filter(r=>r[0]<xs[i]&&r[2]>xs[i-1]).map(r=>[r[1],r[3]]).sort((a,b)=>a[0]-b[0]);let length=0,lo=null,hi=null;
      for(const span of spans){if(lo===null){[lo,hi]=span;}else if(span[0]>hi){length+=hi-lo;[lo,hi]=span;}else hi=Math.max(hi,span[1]);}sum+=(length+(lo===null?0:hi-lo))*(xs[i]-xs[i-1]);}
    return sum;
  }
  function footprints(query, rect, width, alignment, offset, direction) {
    if(!query?.ok||query.exact!==true||query.mode!=='exact')throw Error('試擺需要完整格線；不能使用抽樣結果。');
    const shift=(alignment==='center'?-width/2:alignment==='max'?-width:0)+offset, ghosts=[], lines=[];
    for(const axis of ['u','v'])for(const line of query.axes[axis].lines)for(const segment of line.segments){
      const cross=axis==='u'?0:1,along=1-cross,coordinate=segment.a[cross],lo=Math.max(rect[along],Math.min(segment.a[along],segment.b[along])),hi=Math.min(rect[along+2],Math.max(segment.a[along],segment.b[along]));
      if(!(lo<hi))continue;
      if(coordinate>=rect[cross]&&coordinate<=rect[cross+2])lines.push({axis,index:line.index,band:segment.band,coordinate,lo,hi});
      if(direction!=='both'&&direction!==(axis==='u'?'v':'u'))continue;
      const r=axis==='u'?[coordinate+shift,lo,coordinate+shift+width,hi]:[lo,coordinate+shift,hi,coordinate+shift+width];
      const clipped=intersect(r,rect);if(!clipped)continue;
      ghosts.push({axis,index:line.index,band:segment.band,rect:r,clipped,outside:area(r)-area(clipped)});
    }
    let overlaps=0;for(let i=0;i<ghosts.length;i++)for(let j=0;j<i;j++)if(intersect(ghosts[i].clipped,ghosts[j].clipped))overlaps++;
    const occupied=unionArea(ghosts.map(g=>g.clipped)),extents=ghosts.map(g=>g.clipped);
    const margins=extents.length?[Math.min(...extents.map(r=>r[0]))-rect[0],Math.min(...extents.map(r=>r[1]))-rect[1],rect[2]-Math.max(...extents.map(r=>r[2])),rect[3]-Math.max(...extents.map(r=>r[3]))]:null;
    return {ghosts,lines,occupied,overlaps,margins,outside:ghosts.reduce((s,g)=>s+g.outside,0)};
  }
  const api={footprints,unionArea};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(!root.document)return;
  const $=id=>document.getElementById(id), LIMIT=100000000;
  const fields=['X','Y','Width','Height','Face','Direction','Align','Offset'];
  function mount(host, options) {
    const section=document.createElement('details');section.id='igTrial';section.className='ig-trial';
    section.innerHTML=`<summary>矩形與角材試擺</summary><label class="ig-trial-toggle"><input id="igTrialEnabled" type="checkbox">顯示試擺（不保存）</label><div class="ig-pair"><label>寬 u mm<input id="igTrialWidth" type="number" step="1" min="1" value="2400"></label><label>高 v mm<input id="igTrialHeight" type="number" step="1" min="1" value="1800"></label><label>左上 u mm<input id="igTrialX" type="number" step="1" value="0"></label><label>左上 v mm<input id="igTrialY" type="number" step="1" value="0"></label></div><div class="ig-pair"><button id="igTrialDraw" type="button" class="btn" aria-pressed="false">拖畫矩形</button><button id="igTrialFit" type="button" class="btn">查看整個矩形</button></div><label>27 × 33 mm 角材 · 朝向<select id="igTrialFace"><option value="27">平面寬 27 · 厚 33 mm</option><option value="33">平面寬 33 · 厚 27 mm</option><option value="0">只看矩形與格線</option></select></label><label>桿件長軸<select id="igTrialDirection"><option value="u">沿 u →（貼 v 格線）</option><option value="v">沿 v ↓（貼 u 格線）</option><option value="both">兩向疊看</option></select></label><div class="ig-pair"><label>對齊格線<select id="igTrialAlign"><option value="center">中心線</option><option value="min">左／上緣</option><option value="max">右／下緣</option></select></label><label>向右／下偏移 mm<input id="igTrialOffset" type="number" step="1" value="0"></label></div><p id="igTrialNote" role="status">橙色是角材平面投影；紅邊表示超出試擺矩形。只檢查尺寸外觀，不驗證接合、可施工或結構安全；建立仍只保存網格。</p>`;
    host.append(section);
    let disposed=false,serial=0,timer=null,key='',result=null,error='',pending=false,armed=false,drag=null;
    const enabled=()=>$('igTrialEnabled')?.checked;
    const value=(name,min=-LIMIT,max=LIMIT)=>{const node=$('igTrial'+name),raw=node.value.trim(),n=Number(raw),valid=/^-?\d+$/.test(raw)&&Number.isSafeInteger(n)&&n>=min&&n<=max;node.setAttribute('aria-invalid',String(!valid));if(!valid)throw Error(`${node.closest('label').firstChild.textContent}須為 ${min} 至 ${max} 的整數。`);return n;};
    function config(){const x=value('X'),y=value('Y'),w=value('Width',1),h=value('Height',1),width=Number($('igTrialFace').value),offset=width?value('Offset'):0,r=[x,y,x+w,y+h];if(r[2]>LIMIT||r[3]>LIMIT)throw Error('矩形右／下緣超出 ±100,000,000 mm。');return {r,width,offset,alignment:$('igTrialAlign').value,direction:$('igTrialDirection').value};}
    function invalidate(){for(const name of ['Direction','Align','Offset'])$('igTrial'+name).disabled=$('igTrialFace').value==='0';++serial;clearTimeout(timer);key='';result=null;error='';pending=false;options.redraw();}
    function cancelDraw(){armed=false;drag=null;$('igTrialDraw')?.setAttribute('aria-pressed','false');}
    $('igTrialEnabled').onchange=()=>{cancelDraw();invalidate();};
    for(const name of fields)$('igTrial'+name).addEventListener('input',invalidate);
    $('igTrialDraw').onclick=()=>{armed=!armed;drag=null;$('igTrialEnabled').checked=true;$('igTrialDraw').setAttribute('aria-pressed',String(armed));$('igTrialNote').textContent=armed?'在網格上拖出矩形；放開後取整數 mm，可再輸入精確寬高。':'已取消拖畫。';options.view.scrollIntoView({block:'center'});};
    $('igTrialFit').onclick=()=>{try{const {r}=config();$('igTrialEnabled').checked=true;options.fit(r);invalidate();}catch(e){$('igTrialNote').textContent=e.message;}};
    const handlers={pointerdown:e=>{if(!armed||e.button!==0||!options.inPlot(e))return;e.preventDefault();e.stopImmediatePropagation();const p=options.point(e).map(Math.round);drag={start:p,id:e.pointerId};options.view.setPointerCapture(e.pointerId);},pointermove:e=>{if(!drag)return;e.preventDefault();e.stopImmediatePropagation();const p=options.point(e).map(Math.round),a=drag.start;for(const [name,v] of Object.entries({X:Math.min(a[0],p[0]),Y:Math.min(a[1],p[1]),Width:Math.abs(a[0]-p[0]),Height:Math.abs(a[1]-p[1])}))$('igTrial'+name).value=v;invalidate();},pointerup:e=>{if(!drag)return;e.preventDefault();e.stopImmediatePropagation();cancelDraw();if(options.view.hasPointerCapture(e.pointerId))options.view.releasePointerCapture(e.pointerId);invalidate();},pointercancel:()=>cancelDraw(),lostpointercapture:()=>{if(drag)cancelDraw();}};
    Object.entries(handlers).forEach(([event,fn])=>options.view.addEventListener(event,fn,true));
    function render(ctx, command, sourceError, sourceFingerprint) {
      if(disposed||!enabled())return false;
      const note=$('igTrialNote');let c;
      try{c=config();if(sourceError)throw Error(sourceError);}catch(e){++serial;clearTimeout(timer);key='';result=null;pending=false;note.textContent=e.message;return true;}
      const pad=c.width+Math.abs(c.offset),queryRect=[Math.floor(c.r[0]-pad),Math.floor(c.r[1]-pad),Math.ceil(c.r[2]+pad),Math.ceil(c.r[3]+pad)],newKey=JSON.stringify([queryRect,command,sourceFingerprint]);
      if(queryRect.some(n=>Math.abs(n)>LIMIT)){note.textContent='試擺含角材寬度／偏移後超出座標範圍，請縮小或移動矩形。';return true;}
      if(newKey!==key){key=newKey;result=null;error='';pending=true;const seq=++serial;clearTimeout(timer);timer=setTimeout(async()=>{try{const r=await options.query(`grid-trial-query rect ${queryRect.join(' ')} ${command}`);if(disposed||seq!==serial||!options.current())return;if(!r.ok)throw Error(r.code==='QUERY_CAPACITY'?'試擺格線過密，無法完整顯示。請縮小矩形或增加格距；未以抽樣代替完整試擺。':r.error||'無法取得完整試擺。');if(!r.exact)throw Error('試擺需要完整資料。');if(['u','v'].reduce((n,a)=>n+r.axes[a].lines.reduce((m,l)=>m+l.segments.length,0),0)>512)throw Error('試擺超過 512 段，請縮小矩形或增加格距；不顯示不完整結果。');result=r;}catch(e){if(disposed||seq!==serial)return;error=e.message;}finally{if(!disposed&&seq===serial){pending=false;options.redraw();}}},180);}
      const {svg,label,plot,px,py,scale}=ctx,r=c.r,rectAttrs=a=>({x:px(a[0]),y:py(a[1]),width:(a[2]-a[0])*scale,height:(a[3]-a[1])*scale});
      svg('rect',{...rectAttrs(r),fill:'#fff',stroke:'#bd6a22','stroke-width':2,'data-ig-trial-boundary':r.join(',')},plot);
      let geometry=null;
      if(result&&!pending&&!error){geometry=footprints(result,r,c.width,c.alignment,c.offset,c.width?c.direction:'none');
        for(const ghost of geometry.ghosts)svg('rect',{...rectAttrs(ghost.rect),fill:'#dc9b5460',stroke:ghost.outside?'#ba3434':'#a66a2b','stroke-width':1,'data-ig-trial-ghost':`${ghost.axis}:${ghost.index}:${ghost.band??''}`,'data-trial-rect':ghost.rect.join(','),'data-trial-outside':ghost.outside},plot);
        for(const line of geometry.lines){const a=line.axis==='u';svg('line',{x1:px(a?line.coordinate:line.lo),y1:py(a?line.lo:line.coordinate),x2:px(a?line.coordinate:line.hi),y2:py(a?line.hi:line.coordinate),stroke:'#526f92','stroke-width':1,'stroke-dasharray':'3 3','data-ig-trial-line':`${line.axis}:${line.index}:${line.band??''}`},plot);}
      }
      label(plot,px(r[0])+8,py(r[1])+17,`試擺 ${r[2]-r[0]} × ${r[3]-r[1]} mm`,{'font-size':12,fill:'#874611','data-ig-trial-dimensions':''});
      const fmt=n=>Number(n.toFixed(2));
      note.textContent=pending?'正在取得完整格線，角材暫不顯示…':error||`僅預覽 · 橙色角材／虛線格線；紅邊超出矩形。${geometry?`${geometry.ghosts.length} 段 · 平面占用 ${fmt(100*geometry.occupied/area(r))}% · 重疊 ${geometry.overlaps} 對 · 超出 ${fmt(geometry.outside)} mm²。${geometry.margins?'四側最小餘量（左上右下）'+geometry.margins.map(fmt).join(' / ')+' mm。':''}`:''} 不驗證接合、施工或結構安全；建立只保存網格。`;
      section.dataset.trialState=pending?'pending':error?'error':'ready';
      return true;
    }
    return {render,dispose(){disposed=true;++serial;clearTimeout(timer);Object.entries(handlers).forEach(([event,fn])=>options.view.removeEventListener(event,fn,true));},cancelDraw};
  }
  root.GridTrial={...api,mount};
})(typeof window==='undefined'?globalThis:window);
