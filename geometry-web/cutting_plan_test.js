/* P89: registered by cdp_test.js; actual app and native references. */
const cdp=require('./cdp_helpers.js'),fs=require('fs'),path=require('path'),os=require('os');
module.exports=async function({send,eval_,sleep,click,waitForUI,exceptionCount}){
 console.log('=== P89. 裁切、宣告餘料與採購 ===');const check=cdp.makeCheck({prefix:'P89 '}),errors=exceptionCount();
 const ctl=async selector=>{const p=await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('missing control');e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return{x,y,hit:e.contains(document.elementFromPoint(x,y))};})()`);if(!p.hit)throw Error('Cutting control covered: '+selector);await click(p.x,p.y);await sleep(100);};
 const choose=async(id,value)=>eval_(`(()=>{const e=document.getElementById(${JSON.stringify(id)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('change',{bubbles:true}));})()`);
 const fill=async(selector,text)=>{await ctl(selector);await send('Input.dispatchKeyEvent',{type:'keyDown',key:'a',code:'KeyA',modifiers:2,windowsVirtualKeyCode:65});await send('Input.dispatchKeyEvent',{type:'keyUp',key:'a',code:'KeyA',modifiers:2,windowsVirtualKeyCode:65});await send('Input.insertText',{text});};
 const stockForm=async()=>{for(const [label,text]of [['名稱','木材'],['截面 A mm','27'],['截面 B mm','33'],['新料長度 mm','6000'],['原廠端修整 mm','0']])await fill(`#cuttingStocks fieldset:first-child input[aria-label="${label}"]`,text);await eval_(`(()=>{const m=document.querySelector('#cuttingStocks fieldset select');m.value='unset';m.dispatchEvent(new Event('change',{bubbles:true}));})()`);for(const [field,text]of [['kerf','3'],['allowance','0'],['minRemnant','300']])await fill(`#cuttingGlobals [data-setting="${field}"]`,text);};
 const screens=process.env.GEOMETRY_SCHEDULE_SCREENSHOT_DIR||path.join(os.tmpdir(),'geometry-k1-screens');fs.mkdirSync(screens,{recursive:true});
 const screenshot=async name=>fs.writeFileSync(path.join(screens,name),Buffer.from((await send('Page.captureScreenshot',{format:'png'})).result.data,'base64'));
 await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
 await eval_(`(async()=>{resetSceneFocus();await api('default');await renderObjects();await enterFocus('face',1);})()`);
 await ctl('[data-fi-tab="components"]');await ctl('[data-component-tab="timber"]');await waitForUI(`!!$('timberScheduleOrder')`);
 check('GEO-219 排序與裁切入口合併為既有料單檢視選單',await eval_(`$('timberScheduleOrder').parentElement.textContent.includes('料單檢視')&&[...$('timberScheduleOrder').options].map(o=>o.value).join(',')==='id,length,cutting'`));
 await choose('timberScheduleOrder','cutting');await waitForUI(`!!$('cuttingDialog')`);
 check('未設定保持空白，沒有鋸縫或修整預設值',await eval_(`[...document.querySelectorAll('#cuttingGlobals input')].every(i=>i.value==='')&&$('cuttingStocks').children.length===0`));
 await ctl('#cuttingAddStock');
 await stockForm();
 await ctl('#cuttingSave');
 check('表單明示保存一次設定與歷史',await eval_(`(()=>{const s=ReferenceWorkspace.readFeatureAttachment('cutting-settings');return s?.kerf===3&&s.stockTypes.length===1&&s.stockTypes[0].material===null&&ReferenceWorkspace.history.actionLabel('undo')==='裁切設定';})()`));
 const snapshot=()=>eval_(`(async()=>JSON.stringify({dump:(await api('dump')).text,revision:ReferenceWorkspace.getProjectState().revision,dirty:ReferenceWorkspace.context().dirty,undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length,settings:ReferenceWorkspace.readFeatureAttachment('cutting-settings')}))()`);
 const before=await snapshot();await ctl('#cuttingCalculate');await waitForUI(`$('cuttingStatus').textContent.startsWith('COMPLETE')`);
 check('真 native 求值且每個需求 id 恰一次；守恆驗證通過',await eval_(`(async()=>{const r=await apiRequest('references'),s=ReferenceWorkspace.readFeatureAttachment('cutting-settings'),p=await CuttingPlan.evaluate(r,s,{world:{kind:'live'},scopes:[{surface:1,ids:null},{surface:1,ids:[1]}]});const ids=r.timbers.filter(t=>t.geometry.surface===1).map(t=>t.id);return p.status==='COMPLETE'&&CuttingPlan.verify(p,ids)&&p.groups.flatMap(g=>g.stocks.flatMap(s=>s.pieces)).length===ids.length;})()`));
 await choose('cuttingUnit','cm');await choose('cuttingOrder','length');await ctl('#cuttingExport');
 check('求方案、顯示與匯出不改 World、revision、dirty、history 或宣告',await snapshot()===before);
 check('顯示購料、下刀、區間、剩料分類與未使用餘料',await eval_(`$('cuttingPlan').textContent.includes('新料需購入')&&$('cuttingPlan').textContent.includes('下刀')&&$('cuttingPlan').textContent.includes('在料上的區間 cm')&&$('cuttingPlan').textContent.includes('未使用宣告餘料')`));
 await screenshot('cutting-desktop.png');
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
   if(mode==='context')await eval_(`(async()=>{const b=await GeometryProject.pack('reset\\n',{projectId:'k1-other',name:'另一專案',sources:[],faces:[]},new Map(),fflate);await ReferenceWorkspace.importBytes(b,'另一專案.gcanvas');await renderObjects();})()`);
   if(mode==='repeat')await ctl('#cuttingExport');
   const result=await eval_(`(async()=>{__k1Guard.release();await Promise.all(__k1Guard.pending);return __k1Guard.blobs;})()`);
   check('T16 真畫面匯出守門 '+mode+' 的 Blob 數量',result===(mode==='repeat'?1:0),result);
  }finally{await eval_(`__k1Guard.release();__k1Guard.restore();document.getElementById('cuttingDialog')?.close();void 0`);}
 }
 await eval_(`(async()=>{resetSceneFocus();const response=await fetch('/examples/engineering-spec-v1.gcanvas');if(!response.ok)throw Error('Engineering example absent');await ReferenceWorkspace.importBytes(new Uint8Array(await response.arrayBuffer()),'K1 工程範例.gcanvas');await renderObjects();window.__k1Engineering=await apiRequest('references');})()`);
 check('E1 真原生七件長度與 application 材料末端，短料回 OVER_LENGTH',await eval_(`(async()=>{const r=__k1Engineering,expected=[[10,4000],[11,4000],[12,2946],[13,2946],[20,2946],[30,1960],[31,1959]],material={id:'example-timber-27x33',version:1,fingerprint:'f58363d2c040ecdaeaf38e314bb20357f251ba7d955ecb23262f3d7bc4f6db66'},s={kerf:3,allowance:0,minRemnant:300,stockTypes:[{key:1,name:'範例角材',section:[27,33],material,length:3636,endTrim:5}],remnants:[],nextStockKey:2,nextRemnantKey:1};window.__k1EngineeringSettings=s;const p=await CuttingPlan.evaluate(r,s,{world:{kind:'live'},scopes:[{surface:1,ids:null}]});return JSON.stringify(r.timbers.map(t=>[t.id,t.geometry.length]).sort((a,b)=>a[0]-b[0]))===JSON.stringify(expected)&&r.engineeringSources.filter(s=>s.target.kind==='timber').every(s=>s.terminal?.kind==='material'&&s.terminal.fingerprint===material.fingerprint)&&p.status==='INVALID'&&p.groups.length===0&&p.diagnostics.filter(d=>d.code==='OVER_LENGTH').map(d=>d.detail.timberId).join(',')==='10,11';})()`));
 check('E2 真原生需求排入六支，區間與剩料逐值守恆',await eval_(`(async()=>{const s=__k1EngineeringSettings;s.stockTypes[0].length=4200;const p=await CuttingPlan.evaluate(__k1Engineering,s,{world:{kind:'live'},scopes:[{surface:1,ids:null}]}),g=p.groups[0];return p.status==='COMPLETE'&&CuttingPlan.verify(p,[10,11,12,13,20,30,31])&&g.newStockCount===6&&JSON.stringify(g.stocks.map(s=>s.pieces.map(p=>[p.timberId,p.start,p.end])))===JSON.stringify([[[10,5,4005]],[[11,5,4005]],[[12,5,2951]],[[13,5,2951]],[[20,5,2951]],[[30,5,1965],[31,1968,3927]]])&&g.stocks.map(s=>s.leftover.length).join(',')==='192,192,1246,1246,1246,270';})()`));
 await eval_(`(async()=>{resetSceneFocus();await api('default');await renderObjects();await enterFocus('face',1);})()`);await ctl('[data-fi-tab="components"]');await ctl('[data-component-tab="timber"]');
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 if(await eval_(`!document.body.classList.contains('drawer-right-open')`))await ctl('#workspaceToggleRight');
 await choose('timberScheduleOrder','cutting');await waitForUI(`!!$('cuttingDialog')`);
 check('手機對話框在可視區，表單與關閉入口可操作',await eval_(`(()=>{const d=$('cuttingDialog'),r=d.getBoundingClientRect();return r.x>=0&&r.right<=innerWidth&&r.y>=0&&r.bottom<=innerHeight&&!!d.querySelector('[aria-label="關閉裁切與採購"]');})()`));
 await ctl('#cuttingAddStock');await stockForm();await ctl('#cuttingSave');const mobileBefore=await snapshot();await ctl('#cuttingCalculate');await waitForUI(`$('cuttingStatus').textContent.startsWith('COMPLETE')`);
 await eval_(`window.__k1MobileURL=URL.createObjectURL;window.__k1MobileBlob=null;URL.createObjectURL=b=>{window.__k1MobileBlob=b;return __k1MobileURL.call(URL,b);};`);
 try{await ctl('#cuttingExport');check('390px 真點按與鍵盤設定、求方案、精確 CSV 匯出保持唯讀',await snapshot()===mobileBefore&&await eval_(`(async()=>{const r=await apiRequest('references'),s=ReferenceWorkspace.readFeatureAttachment('cutting-settings'),p=await CuttingPlan.evaluate(r,s,{world:{kind:'live'},scopes:[{surface:1,ids:null}]});return !!__k1MobileBlob&&new TextDecoder('utf-8',{ignoreBOM:true}).decode(await __k1MobileBlob.arrayBuffer())===CuttingPlan.csv(p)&&$('cuttingPlan').textContent.includes('新料需購入')&&!$('cuttingExport').disabled&&s.stockTypes.length===1;})()`));}finally{await eval_(`URL.createObjectURL=__k1MobileURL;void 0`);}
 await screenshot('cutting-mobile.png');
 await ctl('#cuttingDialog [aria-label="關閉裁切與採購"]');
 await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
 check('裁切流程沒有新增 uncaught browser exception',exceptionCount()===errors);
};
