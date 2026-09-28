/* Signed lattice identities through the existing face editor. */
module.exports = async function ({send,eval_,sleep,click,waitForUI}) {
  console.log('=== P71. 無限格線的面內引用與真 cell ===');
  const check=(name,ok,detail='')=>console.log(name,ok===true?'✓':'✗',ok===true?'':JSON.stringify(detail));
  const ctl=async selector=>{
    const p=await eval_(`(()=>{const n=document.querySelector(${JSON.stringify(selector)});if(!n)throw Error('Missing control');n.scrollIntoView({block:'center'});const r=n.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
    await click(p.x,p.y);await sleep(250);
  };
  await send('Emulation.setDeviceMetricsOverride',{width:1382,height:900,deviceScaleFactor:1,mobile:false});
  if(await eval_(`!!$('infiniteGridWorkspace')?.open`))await ctl('#igClose');
  await eval_(`(async()=>{await leaveFocus();await setView3(false);await api('reset');
    for(const l of ${JSON.stringify([
      'grid-system 70 name-hex 36303078343030 main-along u u repeat 0 600 v repeat 0 400',
      'surface 70 origin 0 0 2500 u +x v +y outline 100,200 2500,200 2500,1800 100,1800 hole 900,600 1300,600 1300,1000 900,1000',
      'boundary-vertex-keys 70 outer 1 2 3 4 hole 5 6 7 8 next-key 9',
      'grid-binding 70 on-boundary 70 from-system 70 vertex-key 1 cell -2 1 anchor 1 2 1 2',
      'grid 70 on 70 from-binding 70'
    ])}){let r=await apiRequest('line '+l);if(r.preview){if(!r.preview.valid)throw Error(JSON.stringify(r));r=await apiRequest('line confirm '+r.preview.token);}if(!r.ok)throw Error(JSON.stringify(r));}
    await renderObjects();await enterFocus('face',70);GridEditor.open(70);})()`);
  await waitForUI(`!!$('gridBindingOpen') && fe.grids.some(g=>g.id===70)`);
  const identity=await eval_(`(()=>{const g=fe.grids.find(g=>g.id===70),a='at-line grid 70 u -1';return {space:g.indexSpace,value:feAnchorLineInfo(70,a)?.value,option:referenceAnchorEntries(70,feSurf(70)).find(x=>x.value===a),hit:!!document.querySelector('[data-face-hit="k:70:u:-1"]')};})()`);
  check('P71-1 負索引 -1 對應 u=400，選項與命中區保持同一身分',identity.space==='lattice'&&identity.value===400&&!!identity.option&&identity.hit,identity);
  await ctl('#subgridNew');
  await waitForUI(`!!$('subgridCellI')`);
  const edge=await eval_(`(()=>{const n=document.querySelector('[data-subgrid-cell="lattice:-2:1"]');return n?{x:+n.getAttribute('x'),y:+n.getAttribute('y'),w:+n.getAttribute('width'),h:+n.getAttribute('height')}:null;})()`);
  check('P71-2 靠邊 cell 保持原始 -200..400 與 0..400，外接框不冒充格線',!!edge&&edge.x===-200&&edge.y===0&&edge.w===600&&edge.h===400,edge);
  const target=await eval_(`(()=>{const n=document.querySelector('[data-subgrid-cell="lattice:-1:2"]');const m=n.getScreenCTM();return {x:m.a*500+m.c*500+m.e,y:m.b*500+m.d*500+m.f};})()`);
  await click(target.x,target.y);await sleep(300);
  await waitForUI(`!!fe.gridPreview && $('gridCreate')?.disabled===false`);
  const preview=await eval_(`({choice:$('subgridCellChoice').value,command:$('gridCommand').textContent,u:fe.gridPreview.u,v:fe.gridPreview.v})`);
  check('P71-3 實際點選負索引 cell，預覽使用 lattice-cell 並精確等分',preview.choice==='lattice:-1:2'&&preview.command.includes('lattice-cell -1 2')&&preview.u[0]===700&&preview.v[0]===600,preview);
  await ctl('#gridCreate');
  if(await eval_(`!!document.querySelector('.reference-impact[open] #impact-confirm')`))await ctl('#impact-confirm');
  await waitForUI(`fe.grids.some(g=>g.kind==='subgrid'&&g.parentId===70)`);
  const saved=await eval_(`(async()=>{const g=fe.grids.find(g=>g.kind==='subgrid'&&g.parentId===70);return {cell:g.cell,mode:g.cellMode,text:(await api('dump')).text};})()`);
  check('P71-4 保存 signed cell，子線仍為局部 ordinal 索引',saved.mode==='lattice'&&saved.cell.i==='-1'&&saved.cell.j==='2'&&saved.text.includes('lattice-cell -1 2'),saved);
  await ctl('.face-layer-row[data-grid-id="70"] .face-layer-del');
  check('P71-5 有依賴的來源格刪除顯示說明，沒有空狀態欄例外',await eval_(`fe.grids.some(g=>g.id===70) && [...document.querySelectorAll('.toast')].some(n=>n.textContent.includes('無法刪除網格 70'))`));
  await eval_(`(async()=>{await leaveFocus();})()`);
  await eval_(`(async()=>{await api('reset');for(const l of ${JSON.stringify([
    'surface 80 origin 0 0 2500 u +x v +y outline 0,0 10000,0 10000,10000 0,10000',
    'grid-system 80 name-hex 64656e7365 main-along u u repeat 0 100 v repeat 0 100',
    'boundary-vertex-keys 80 outer 1 2 3 4 next-key 5',
    'grid-binding 80 on-boundary 80 from-system 80 vertex-key 1 cell 0 0 anchor 0 1 0 1',
    'grid 80 on 80 from-binding 80'
  ])}){let r=await apiRequest('line '+l);if(r.preview){if(!r.preview.valid)throw Error(JSON.stringify(r));r=await apiRequest('line confirm '+r.preview.token);}if(!r.ok)throw Error(JSON.stringify(r));}await renderObjects();await enterFocus('face',80);})()`);
  await waitForUI(`!!$('feLatticeDensity') && !$('feLatticeDensity').hidden`);
  const missing=await eval_(`(()=>{const g=fe.grids.find(g=>g.id===80),i=['49','50','51'].find(k=>!g.indices.u.includes(k));return {i,value:feAnchorLineInfo(80,'at-line grid 80 u '+i)?.value};})()`);
  check('P71-6 抽樣省略的合法線仍可用 lattice 定義精確求座標',!!missing.i&&missing.value===Number(missing.i)*100,missing);
  for(let n=0;n<12;n++)await ctl('#feZoomIn');
  await waitForUI(`fe.grids.find(g=>g.id===80)?.query?.axes?.u?.stride==='1'`);
  check('P71-7 實際放大後重新查詢，恢復被抽樣省略的真格線與命中區',await eval_(`!!document.querySelector('[data-face-hit="k:80:u:${missing.i}"]') && $('feLatticeDensity').hidden`));
  check('P71-8 放大後的新可見線能正確帶入角材引用，不落回空選項',await eval_(`(()=>{const a='at-line grid 80 u ${missing.i}';feChooseTimberAnchor(a);return $('tbAnchor').value===a;})()`));
  await eval_(`(async()=>{await leaveFocus();})()`);
};
