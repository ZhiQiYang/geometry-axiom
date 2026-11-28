/* PF-5 presentation of the same candidate's native diagnostic envelopes.
 * This host validates and paints native loops/projections. It never clips a
 * region, invents a finish, chooses a joint or treats an envelope as timber.
 */
'use strict';
(function (root) {
  const schema='panel-fill-spatial/1',scope='diagnostic-envelope-only';
  const axes=['top','front','side'],layers=['panel','timber'];
  const layerPairs=['panel-panel','panel-timber','timber-panel','timber-timber'];
  const axisNames={top:'俯視（X 向右，Y 向上）',front:'正視（X 向右，Z 向上）',side:'側視（Y 向右，Z 向上）'};
  const axisVectors={'+X':[1,0,0],'-X':[-1,0,0],'+Y':[0,1,0],'-Y':[0,-1,0],'+Z':[0,0,1],'-Z':[0,0,-1]};
  const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const id=v=>Number.isSafeInteger(v)&&v>=0&&v<=4294967295;
  const integer=v=>typeof v==='string'&&/^(0|-?[1-9]\d*)$/.test(v);
  const nonnegative=v=>integer(v)&&BigInt(v)>=0n;
  const tuple=(v,n)=>Array.isArray(v)&&v.length===n&&v.every(integer);
  const loop=(v,n)=>Array.isArray(v)&&v.length>=3&&v.every(p=>tuple(p,n));
  const region=(v,n)=>!!v&&loop(v.outer,n)&&Array.isArray(v.holes)&&v.holes.every(h=>loop(h,n));
  const vector=v=>Array.isArray(v)&&v.length===3&&v.every(n=>Number.isInteger(n)&&Math.abs(n)<=1)&&v.reduce((sum,n)=>sum+Math.abs(n),0)===1;
  const frame=v=>!!v&&tuple(v.origin,3)&&[v.u,v.v,v.n].every(vector);
  const statuses=['complete','pending','unsupported','invalid'];
  const demand=(ok,field)=>{if(!ok)throw Error('PF5_SPATIAL_WIRE：原生空間診斷不完整或不一致（'+field+'）。');};
  const error=v=>!!v&&typeof v.code==='string'&&typeof v.message==='string';
  function validateLayer(value,t,h,name) {
    demand(value&&value.status==='complete'&&tuple(value.interval,2)&&nonnegative(value.area)&&Array.isArray(value.components),name+' 層');
    demand(name==='panel'?same(value.interval,['0',t]):same(value.interval,[t,String(BigInt(t)+BigInt(h))]),name+' 明示層區間');
    demand((value.components.length===0)===(value.area==='0'),name+' 空集合');
    for(const c of value.components){
      demand(region(c,2)&&c.world&&region(c.world.near,3)&&region(c.world.far,3),name+' 全部分量與世界輪廓');
      for(const edge of ['near','far']){
        demand(c.world[edge].outer.length===c.outer.length&&c.world[edge].holes.length===c.holes.length&&
          c.world[edge].holes.every((ring,i)=>ring.length===c.holes[i].length),name+' 世界孔／輪廓閉包');
        for(const axis of axes){const p=c.projections?.[axis]?.[edge];
          demand(region(p,2)&&p.outer.length===c.outer.length&&p.holes.length===c.holes.length&&
            p.holes.every((ring,i)=>ring.length===c.holes[i].length),name+' 原生三視圖閉包');
        }
      }
    }
  }
  function contract(value,state) {
    demand(value&&value.schema===schema&&value.scope===scope&&typeof value.complete==='boolean'&&
      ['finishes','junctions','errors'].every(k=>Array.isArray(value[k])),'schema／集合');
    const fills=new Map(state.panelFills.map(r=>[r.definition.id,r]));
    const finishes=new Map(state.finishSurfaces.map(r=>[r.id,r]));
    const hosts=new Map(state.derivedPlacements.map(r=>[r.definition.id,r]));
    demand(value.finishes.length===fills.size&&new Set(value.finishes.map(f=>f.id)).size===fills.size,'明設鋪排範圍');
    let allComplete=true;
    for(const f of value.finishes){
      const fill=fills.get(f.id),source=finishes.get(fill?.definition.finishSurfaceId);
      demand(fill&&source&&f.finishId===source.id&&typeof f.label==='string'&&statuses.includes(f.status)&&Array.isArray(f.missing),'明設完成面身分');
      allComplete=allComplete&&f.status==='complete';
      if(['unsupported','invalid'].includes(f.status)){demand(error(f.error),'失敗診斷');continue;}
      demand(frame(f.frame)&&same(f.frame.origin,source.frame.origin.map(String))&&
        same(f.frame.u,axisVectors[source.frame.U])&&same(f.frame.v,axisVectors[source.frame.V])&&same(f.frame.n,axisVectors[source.frame.N])&&
        f.side===source.structureSide&&same(f.panelVersion,fill.definition.panel)&&integer(f.thickness)&&BigInt(f.thickness)>0n&&
        f.thickness===fill.derived.thickness,'固定來源與框架');
      demand(Array.isArray(f.obstacles)&&f.obstacles.length===source.obstacles.length&&
        new Set(f.obstacles.map(o=>o.ref)).size===f.obstacles.length&&f.obstacles.every(o=>source.obstacles.includes(o.ref)),'明選障礙閉包');
      for(const o of f.obstacles)demand(tuple(o.projectedRect,4)&&tuple(o.normalInterval,2)&&
        ['overlap','touch','separate'].includes(o.footprintRelation)&&['cut','touch','clear'].includes(o.panel)&&
        (o.timber===null||['cut','touch','clear'].includes(o.timber))&&tuple(o.world?.min,3)&&tuple(o.world?.max,3)&&
        axes.every(a=>tuple(o.projections?.[a],4)),'障礙原生座標／層判定');
      validateLayer(f.panel,f.thickness,null,'panel');
      if(f.status==='pending'){
        demand(f.h===null&&f.hostId===null&&f.host===null&&f.timber===null&&f.missing.includes('derived-placement.h')&&
          f.obstacles.every(o=>o.timber===null),'缺 h 不補值');continue;
      }
      const nativeHost=hosts.get(f.hostId);
      demand(f.missing.length===0&&integer(f.h)&&BigInt(f.h)>0n&&nativeHost?.definition.fillId===f.id&&
        f.h===nativeHost.derived.h&&f.host?.id===f.hostId&&same(f.host.definition,nativeHost.definition)&&
        frame(f.host.frame)&&f.host.h===f.h&&nonnegative(f.host.region?.area)&&Array.isArray(f.host.region?.components),'板背正式宿主來源');
      demand(same(f.host.frame.origin,nativeHost.derived.frame.origin)&&
        same(f.host.frame.u,axisVectors[nativeHost.derived.frame.U])&&same(f.host.frame.v,axisVectors[nativeHost.derived.frame.V])&&
        same(f.host.frame.n,axisVectors[nativeHost.derived.frame.N]),'板背原生框架');
      demand(f.host.region.components.length===nativeHost.derived.components.length&&f.host.region.components.every((c,i)=>{
        const n=nativeHost.derived.components[i];return region(c,2)&&same(c.outer,n.outline)&&same(c.holes,n.holes)&&same(c.edges,n.edges);
      }),'全部宿主分量／孔／完整邊鍵');
      validateLayer(f.timber,f.thickness,f.h,'timber');
      demand(f.timber.area===f.host.region.area,'宿主與角材層面積');
    }
    const seen=new Set(),known=new Set(value.finishes.map(f=>f.id));
    for(const pair of value.junctions){
      demand(Array.isArray(pair.finishes)&&pair.finishes.length===2&&pair.finishes.every(v=>id(v)&&known.has(v))&&
        pair.finishes[0]<pair.finishes[1]&&statuses.includes(pair.status)&&pair.joinPolicy==='unselected','交界身分／未選接法');
      const key=pair.finishes.join(':');demand(!seen.has(key),'交界不可重複');seen.add(key);allComplete=allComplete&&pair.status==='complete';
      if(['unsupported','invalid'].includes(pair.status)){demand(error(pair.error),'交界失敗診斷');continue;}
      demand(Number.isInteger(pair.visibleContactDimension)&&pair.visibleContactDimension>=-1&&pair.visibleContactDimension<=2&&
        (pair.minimumL1Gap===null||nonnegative(pair.minimumL1Gap))&&Array.isArray(pair.sharedEdges)&&pair.layers,'可見交界');
      for(const e of pair.sharedEdges)demand(tuple(e.start,3)&&tuple(e.end,3)&&nonnegative(e.length)&&BigInt(e.length)>0n,'全部共同邊');
      for(const name of layerPairs){const p=pair.layers[name];
        if(p===null){demand(pair.status==='pending','缺層不可冒稱完整');continue;}
        demand(p&&nonnegative(p.volume)&&Number.isInteger(p.contactDimension)&&p.contactDimension>=-1&&p.contactDimension<=3&&
          ['overlap','touch','separate'].includes(p.relation),'四組層關係');
      }
    }
    demand(value.junctions.length===value.finishes.length*(value.finishes.length-1)/2,'全部面對');
    demand(value.errors.every(e=>error(e)&&(e.fillId===null||known.has(e.fillId))&&
      (e.finishes===null||Array.isArray(e.finishes)&&e.finishes.length===2&&e.finishes.every(i=>known.has(i)))),'診斷來源');
    demand(value.complete===(allComplete&&value.errors.length===0),'完整性旗標');
    return value;
  }
  const relation={cut:'裁切',touch:'接觸（不裁）',clear:'通過',overlap:'正體積交疊',separate:'分離'};
  const list=(tag,value)=>`<${tag}>${esc(value)}</${tag}>`;
  const quantity=(field,label,value,unit='')=>`<div data-pf5-field="${field}"><dt>${esc(label)}</dt><dd><span data-pf5-value>${esc(value??'未提供')}</span>${unit?' '+esc(unit):''}</dd></div>`;
  function pathData(r){return [r.outer,...r.holes].map(ring=>'M '+ring.map(p=>p.map(esc).join(' ')).join(' L ')+' Z').join(' ');}
  function diagrams(value) {
    return `<div class="pf5-views">${axes.map(axis=>{
      const pieces=value.finishes.flatMap(f=>layers.flatMap(name=>(f[name]?.components||[]).map((c,index)=>({f,name,c,index}))));
      const obstacles=new Map();for(const f of value.finishes)for(const o of f.obstacles||[])obstacles.set(o.ref,o);
      const points=pieces.flatMap(p=>['near','far'].flatMap(edge=>{const r=p.c.projections[axis][edge];return [r.outer,...r.holes].flat();}));
      for(const o of obstacles.values()){const r=o.projections[axis];points.push([r[0],r[1]],[r[2],r[3]]);}
      if(!points.length)return `<figure data-pf5-view="${axis}"><figcaption>${axisNames[axis]}</figcaption><p data-pf5-empty>沒有可繪製的原生輪廓。</p></figure>`;
      const bounds=points.reduce((b,p)=>{const x=Number(p[0]),y=Number(p[1]);return [Math.min(b[0],x),Math.min(b[1],y),Math.max(b[2],x),Math.max(b[3],y)];},[Infinity,Infinity,-Infinity,-Infinity]);
      const [xmin,ymin,xmax,ymax]=bounds,pad=Math.max(xmax-xmin,ymax-ymin,1)*.04;
      const box=[xmin-pad,-ymax-pad,Math.max(xmax-xmin,1)+2*pad,Math.max(ymax-ymin,1)+2*pad];
      const rc=[...obstacles.values()].map(o=>{const r=o.projections[axis];return `<rect data-pf5-rc="${esc(o.ref)}" x="${esc(r[0])}" y="${esc(r[1])}" width="${esc(String(BigInt(r[2])-BigInt(r[0])))}" height="${esc(String(BigInt(r[3])-BigInt(r[1])))}"><title>${esc(o.ref)} · 明選障礙的原生投影</title></rect>`;}).join('');
      const shapes=pieces.map(({f,name,c,index})=>{
        const projection=c.projections[axis];
        const rings=['near','far'].map(edge=>`<path data-pf5-fill="${f.id}" data-pf5-layer="${name}" data-pf5-component="${index}" data-pf5-depth="${edge}" d="${pathData(projection[edge])}" fill-rule="evenodd"><title>${esc(f.label)} · ${name==='panel'?'面材層':'角材層包絡'} · 分量 ${index+1} · ${edge==='near'?'近面':'遠面'}</title></path>`).join('');
        const connectors=[projection.near.outer,...projection.near.holes].flatMap((ring,ri)=>ring.map((p,i)=>{const q=[projection.far.outer,...projection.far.holes][ri][i];
          return `<line data-pf5-connector="${name}" x1="${esc(p[0])}" y1="${esc(p[1])}" x2="${esc(q[0])}" y2="${esc(q[1])}"/>`; })).join('');
        return rings+connectors;
      }).join('');
      return `<figure data-pf5-view="${axis}"><figcaption>${axisNames[axis]}</figcaption><svg class="pf5-projection" role="img" aria-label="${axisNames[axis]}：原生面材、角材層包絡與明選障礙" viewBox="${box.join(' ')}" preserveAspectRatio="xMidYMid meet"><g transform="scale(1 -1)">${rc}${shapes}</g></svg></figure>`;
    }).join('')}</div>`;
  }
  function render(value) {
    if(!value)return '<p data-pf5-unavailable>目前服務未提供完成面空間診斷。</p>';
    if(value.status==='unavailable')return `<p data-pf5-unavailable role="status">空間診斷目前不可呈現：${esc(value.error?.message)}。完成面定義的確認條件仍由原生交易裁判決定。</p>`;
    const cards=value.finishes.map(f=>{
      const state=f.status==='complete'?'兩層資料完整':f.status==='pending'?'待補明示來源':'目前未能求值';
      const body=['complete','pending'].includes(f.status)?`<dl class="pf5-values">${quantity('origin','完成面原點',f.frame.origin.join('、'),'mm')}${quantity('side','結構側 s',f.side)}${quantity('thickness','固定面材厚 t',f.thickness,'mm')}${quantity('h','角材層厚 h',f.h===null?'未選':f.h,f.h===null?'':'mm')}${quantity('panelArea','面材有效面積',f.panel.area,'mm²')}${quantity('timberArea','角材層有效面積',f.timber?.area??'尚未求值',f.timber?'mm²':'')}${quantity('hostId','板背宿主',f.hostId===null?'尚未建立':'#'+f.hostId)}${quantity('hostOrigin','板背原點',f.host?.frame.origin.join('、')??'尚未求值',f.host?'mm':'')}</dl>
        <p data-pf5-intervals>面材層 [${esc(f.panel.interval.join('、'))}] mm；${f.timber?'角材層 ['+esc(f.timber.interval.join('、'))+'] mm':'角材層厚 h 尚未明選，不以 0 代入。'}</p>
        <div class="pf5-obstacle-list">${f.obstacles.map(o=>`<p data-pf5-obstacle="${esc(o.ref)}"><strong>${esc(o.ref)}</strong>：面材 ${relation[o.panel]}；角材 ${o.timber===null?'尚未求值':relation[o.timber]}。沿結構方向區間 [${esc(o.normalInterval.join('、'))}] mm。</p>`).join('')||'<p>明選障礙為空集合。</p>'}</div>`:`<p role="status">${esc(f.error?.code)}：${esc(f.error?.message)}</p>`;
      return `<article class="pf5-finish" data-pf5-finish="${f.id}" data-pf5-status="${f.status}"><h5>${esc(f.label)} · 完成面 #${f.finishId}／鋪排 #${f.id}</h5><p>${state}</p>${body}</article>`;
    }).join('');
    const pairs=value.junctions.map(j=>{
      const pair=j.finishes.join('、');
      const details=['complete','pending'].includes(j.status)?`<dl class="pf5-values">${quantity('visibleContactDimension','可見面接觸維度',j.visibleContactDimension)}${quantity('minimumL1Gap','最小 L1 距離',j.minimumL1Gap===null?'空區域，無距離':j.minimumL1Gap,j.minimumL1Gap===null?'':'mm')}</dl>
        <ul data-pf5-shared-edges>${j.sharedEdges.map(e=>list('li',e.start.join('、')+' → '+e.end.join('、')+'；長 '+e.length+' mm')).join('')||list('li','沒有共同邊。')}</ul>
        <div class="pf5-pair-layers">${layerPairs.map(name=>{const p=j.layers[name];return `<p data-pf5-pair-layer="${name}">${esc(({ 'panel-panel':'面材／面材','panel-timber':'面材／角材層','timber-panel':'角材層／面材','timber-timber':'角材層／角材層'})[name])}：${p?esc(relation[p.relation])+'；體積 '+list('span',p.volume)+' mm³；接觸維度 '+p.contactDimension:'尚未求值'}</p>`;}).join('')}</div>`:`<p role="status">${esc(j.error?.code)}：${esc(j.error?.message)}</p>`;
      return `<article class="pf5-junction" data-pf5-junction="${j.finishes.join(':')}"><h5>鋪排 #${esc(pair)} 的交界</h5>${details}<p data-pf5-join-policy="${j.joinPolicy}">接法未選。共同邊與包絡交疊不會自動補側封或決定板材退讓。</p></article>`;
    }).join('');
    return `<section class="pf5-spatial" data-pf5-spatial="${schema}" data-pf5-complete="${value.complete}" aria-label="完成面雙層與交界"><h4>明設完成面：雙層與交界</h4><p>列出專案中已明設的完成面。藍色為面材層，橘色虛線為角材層包絡，灰色為明選障礙；包絡不是已放入的角材，也不證明支撐。</p>${diagrams(value)}${cards||'<p>尚未明設鋪排，沒有可求值的層。</p>'}${pairs}${value.errors.length?'<p role="status">尚有未完成診斷；請核對下方原生資料。</p>':''}<details data-pf5-native-details><summary>完整原生座標、分量、孔與宿主邊鍵</summary><pre data-pf5-native>${esc(JSON.stringify(value,null,2))}</pre></details></section>`;
  }
  root.PanelFillSpatial={schema,contract,render};
})(typeof window!=='undefined'?window:globalThis);
