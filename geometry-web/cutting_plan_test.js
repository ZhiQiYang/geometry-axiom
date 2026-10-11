/* P89: registered by cdp_test.js; actual app and native references. */
const cdp=require('./cdp_helpers.js');
module.exports=async function({send,eval_,sleep,click,waitForUI,exceptionCount}){
 console.log('=== P89. 裁切、宣告餘料與採購 ===');const check=cdp.makeCheck({prefix:'P89 '}),errors=exceptionCount();
 const ctl=async selector=>{const p=await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('missing control');e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2};})()`);await click(p.x,p.y);await sleep(100);};
 const choose=async(id,value)=>eval_(`(()=>{const e=document.getElementById(${JSON.stringify(id)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('change',{bubbles:true}));})()`);
 await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
 await eval_(`(async()=>{resetSceneFocus();await api('default');await renderObjects();await enterFocus('face',1);})()`);
 await ctl('[data-fi-tab="components"]');await ctl('[data-component-tab="timber"]');await waitForUI(`!!$('timberScheduleOrder')`);
 check('GEO-219 排序與裁切入口合併為既有料單檢視選單',await eval_(`$('timberScheduleOrder').parentElement.textContent.includes('料單檢視')&&[...$('timberScheduleOrder').options].map(o=>o.value).join(',')==='id,length,cutting'`));
 await choose('timberScheduleOrder','cutting');await waitForUI(`!!$('cuttingDialog')`);
 check('未設定保持空白，沒有鋸縫或修整預設值',await eval_(`[...document.querySelectorAll('#cuttingGlobals input')].every(i=>i.value==='')&&$('cuttingStocks').children.length===0`));
 await ctl('#cuttingAddStock');
 await eval_(`(()=>{const row=document.querySelector('[data-stock-key]'),values={'名稱':'木材','截面 A mm':'27','截面 B mm':'33','新料長度 mm':'6000','原廠端修整 mm':'0'};for(const i of row.querySelectorAll('input')){i.value=values[i.getAttribute('aria-label')];i.dispatchEvent(new Event('input',{bubbles:true}));}const m=row.querySelector('select');m.value='unset';m.dispatchEvent(new Event('change',{bubbles:true}));for(const i of document.querySelectorAll('#cuttingGlobals input')){i.value=({kerf:'3',allowance:'0',minRemnant:'300'})[i.dataset.setting];i.dispatchEvent(new Event('input',{bubbles:true}));}})()`);
 await ctl('#cuttingSave');
 check('表單明示保存一次設定與歷史',await eval_(`(()=>{const s=ReferenceWorkspace.readFeatureAttachment('cutting-settings');return s?.kerf===3&&s.stockTypes.length===1&&s.stockTypes[0].material===null&&ReferenceWorkspace.history.actionLabel('undo')==='裁切設定';})()`));
 const snapshot=()=>eval_(`(async()=>JSON.stringify({dump:(await api('dump')).text,revision:ReferenceWorkspace.getProjectState().revision,dirty:ReferenceWorkspace.context().dirty,undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length,settings:ReferenceWorkspace.readFeatureAttachment('cutting-settings')}))()`);
 const before=await snapshot();await ctl('#cuttingCalculate');await waitForUI(`$('cuttingStatus').textContent.startsWith('COMPLETE')`);
 check('真 native 求值且每個需求 id 恰一次；守恆驗證通過',await eval_(`(async()=>{const r=await apiRequest('references'),s=ReferenceWorkspace.readFeatureAttachment('cutting-settings'),p=await CuttingPlan.evaluate(r,s,{world:{kind:'live'},scopes:[{surface:1,ids:null},{surface:1,ids:[1]}]});const ids=r.timbers.filter(t=>t.geometry.surface===1).map(t=>t.id);return p.status==='COMPLETE'&&CuttingPlan.verify(p,ids)&&p.groups.flatMap(g=>g.stocks.flatMap(s=>s.pieces)).length===ids.length;})()`));
 await choose('cuttingUnit','cm');await choose('cuttingOrder','length');await ctl('#cuttingExport');
 check('求方案、顯示與匯出不改 World、revision、dirty、history 或宣告',await snapshot()===before);
 check('顯示購料、下刀、區間、剩料分類與未使用餘料',await eval_(`$('cuttingPlan').textContent.includes('新料需購入')&&$('cuttingPlan').textContent.includes('下刀')&&$('cuttingPlan').textContent.includes('在料上的區間 cm')&&$('cuttingPlan').textContent.includes('未使用宣告餘料')`));
 await ctl('#cuttingAddRemnant');await eval_(`(()=>{const row=document.querySelector('[data-remnant-key]');row.querySelector('select').value='1';row.querySelector('select').dispatchEvent(new Event('change'));for(const i of row.querySelectorAll('input')){i.value=i.getAttribute('aria-label')==='餘料實長 mm'?'1000':'0';i.dispatchEvent(new Event('input'));}})()`);await ctl('#cuttingSave');
 await eval_(`(async()=>{await api('line undo');})()`);
 check('P-047 復原餘料清單但 key 高水位不退',await eval_(`(()=>{const s=ReferenceWorkspace.readFeatureAttachment('cutting-settings');return s.remnants.length===0&&s.nextRemnantKey===2;})()`));
 await eval_(`(async()=>{await api('line redo');})()`);
 check('P-047 重做同一餘料 key 且高水位不變',await eval_(`(()=>{const s=ReferenceWorkspace.readFeatureAttachment('cutting-settings');return s.remnants[0].key===1&&s.nextRemnantKey===2;})()`));
 await ctl('#cuttingDialog [aria-label="關閉裁切與採購"]');
 for(const mode of ['world','settings','scope','context','late','repeat']){
  await eval_(`(async()=>{resetSceneFocus();await api('default');await renderObjects();await enterFocus('face',1);const old=ReferenceWorkspace.readFeatureAttachment('cutting-settings'),s=old||{kerf:3,allowance:0,minRemnant:300,stockTypes:[{key:1,name:'木材',section:[27,33],material:null,length:6000,endTrim:0}],remnants:[],nextStockKey:2,nextRemnantKey:1};ReferenceWorkspace.setFeatureAttachment('cutting-settings',s,ReferenceWorkspace.getProjectState().contextToken);})()`);
  await ctl('[data-fi-tab="components"]');await ctl('[data-component-tab="timber"]');await choose('timberScheduleScope','surface');await choose('timberScheduleOrder','cutting');await ctl('#cuttingCalculate');await waitForUI(`$('cuttingStatus').textContent.startsWith('COMPLETE')`);
  await eval_(`(()=>{const g=window.__k1Guard={held:false,blobs:0,pending:[]},originalFetch=window.fetch,originalURL=URL.createObjectURL,gate=new Promise(resolve=>g.release=resolve);g.restore=()=>{window.fetch=originalFetch;URL.createObjectURL=originalURL;};window.fetch=async(...args)=>{const body=String(args[0])==='/api'?JSON.parse(args[1]?.body||'{}'):{};const response=await originalFetch(...args);if(body.cmd==='references'&&!g.held){g.held=true;await gate;}return response;};URL.createObjectURL=b=>{g.blobs++;return originalURL.call(URL,b);};const b=$('cuttingExport'),handler=b.onclick;b.onclick=()=>g.pending.push(handler());})()`);
  try{
   await ctl('#cuttingExport');await waitForUI(`__k1Guard.held`);
   if(mode==='world')await eval_(`(async()=>{let r=await api('line spec k1_race 7');if(r.preview?.valid)r=await api('line confirm '+r.preview.token);if(!r.ok)throw Error(JSON.stringify(r));})()`);
   if(mode==='settings')await eval_(`(()=>{const s=ReferenceWorkspace.readFeatureAttachment('cutting-settings');s.kerf++;ReferenceWorkspace.setFeatureAttachment('cutting-settings',s,ReferenceWorkspace.getProjectState().contextToken);})()`);
   if(mode==='scope')await ctl('#cuttingScopes button');
   if(mode==='late')await ctl('#cuttingDialog [aria-label="關閉裁切與採購"]');
   if(mode==='context')await eval_(`(async()=>{const b=await GeometryProject.pack('reset\n',{projectId:'k1-other',name:'另一專案',sources:[],faces:[]},new Map(),fflate);await ReferenceWorkspace.importBytes(b,'另一專案.gcanvas');await renderObjects();})()`);
   if(mode==='repeat')await ctl('#cuttingExport');
   const result=await eval_(`(async()=>{__k1Guard.release();await Promise.all(__k1Guard.pending);return __k1Guard.blobs;})()`);
   check('T16 真畫面匯出守門 '+mode+' 的 Blob 數量',result===(mode==='repeat'?1:0),result);
  }finally{await eval_(`__k1Guard.release();__k1Guard.restore();document.getElementById('cuttingDialog')?.close();void 0`);}
 }
 await eval_(`(async()=>{resetSceneFocus();await api('default');await renderObjects();await enterFocus('face',1);})()`);await ctl('[data-fi-tab="components"]');await ctl('[data-component-tab="timber"]');
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 if(await eval_(`!document.body.classList.contains('drawer-right-open')`))await ctl('#workspaceToggleRight');
 await choose('timberScheduleOrder','cutting');await waitForUI(`!!$('cuttingDialog')`);
 check('手機對話框在可視區，表單與關閉入口可操作',await eval_(`(()=>{const d=$('cuttingDialog'),r=d.getBoundingClientRect();return r.x>=0&&r.right<=innerWidth&&r.y>=0&&r.bottom<=innerHeight&&!!d.querySelector('[aria-label="關閉裁切與採購"]');})()`));
 await ctl('#cuttingDialog [aria-label="關閉裁切與採購"]');
 await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
 check('裁切流程沒有新增 uncaught browser exception',exceptionCount()===errors);
};
