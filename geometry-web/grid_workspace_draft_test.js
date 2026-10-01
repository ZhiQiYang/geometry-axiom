/* P73 scheduling regression against the real browser and native World.
 * The delayed query returns the original native response unchanged. Only its
 * delivery is gated so an actual input event can occur while it is pending.
 */
const cdp=require('./cdp_helpers.js');
module.exports = async function gridWorkspaceDrafts({send,eval_,sleep,click,waitForUI,expectNativeDialog}) {
  console.log('=== P73B. 網格延遲載入及切換邊界不吞草稿 ===');
  const check=cdp.makeCheck({prefix:'P73B ',throwOnFail:true});
  const wait=cdp.makeWait(waitForUI,20000);
  const ctl=cdp.makeCtl({eval_,sleep,click},{scroll:'nearest',attempts:1,pollMs:70,settleMs:130,missing:'Missing ',
    unreachable:(selector,p)=>'Draft control unreachable '+selector+' '+JSON.stringify(p)});
  const key=cdp.makeKey({send,sleep});
  const fill=cdp.makeFill({ctl,key,send,sleep},{afterMs:70});
  const choose=async(selector,value,expected=value)=>{
    const index=await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});return [...e.options].filter(o=>!o.disabled).findIndex(o=>o.value===${JSON.stringify(value)});})()`);if(index<0)throw Error('Missing option '+value);
    await ctl(selector);await key('Home','Home',36);for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);await key('Enter','Enter',13);await wait(`document.querySelector(${JSON.stringify(selector)}).value===${JSON.stringify(expected)}`);
  };
  const query=command=>eval_(`apiRequest(${JSON.stringify(command)}).then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r;})`),dump=async()=>(await query('dump')).text;
  const leaveMessage='這個網格工作區有尚未建立或套用的草稿。離開會捨棄這些草稿；已保存到場景的網格保持不變。確定離開？';
  const switchMessage='邊界有尚未套用的頂點草稿。切換邊界會捨棄這些草稿，確定切換？';
  // Dedicated native fixture. Direct confirmations are limited to this fixture;
  // every tested editing action below is driven through visible controls.
  await eval_(`(async()=>{
    const commit=async line=>{let r=await apiRequest('line '+line);if(r.preview){if(!r.preview.valid)throw Error(JSON.stringify(r));r=await apiRequest('line confirm '+r.preview.token);}if(!r.ok)throw Error(line+' '+JSON.stringify(r));};
    for(const line of ['boundary 801 outline 100,200 1300,200 1300,1000 100,1000','boundary 802 outline 0,0 800,0 800,600 0,600','grid-system 801 name-hex 526163652067726964 main-along none u repeat 0 600 v repeat 0 400'])await commit(line);
    const boundary=await apiRequest('boundary 801');if(!boundary.ok)throw Error(JSON.stringify(boundary));
    await commit('grid-binding 801 on-boundary 801 from-system 801 vertex outer 0 geometry-hash '+boundary.geometryFingerprint+' cell 0 0 anchor 0 1 0 1');
    await renderObjects();return true;
  })()`);
  const baseline=await dump();await ctl('#btnZoom');await ctl('.ocard[data-kind="grid-binding"][data-id="801"]');await wait(`!!$('gridObjectOpen')`);
  await eval_(`(()=>{if(window.__gridDraftDelay)throw Error('Existing query gate');const gate=window.__gridDraftDelay={original:window.apiRequest,captured:false,released:false};window.apiRequest=async function(command,...args){const result=await gate.original(command,...args);if(command==='boundary 801'&&!gate.captured){gate.captured=true;return new Promise(resolve=>{gate.release=()=>{gate.released=true;resolve(result);};});}return result;};return true;})()`);
  try {
    await ctl('#gridObjectOpen');await wait('window.__gridDraftDelay.captured && !!window.__gridDraftDelay.release');
    await fill('#igCellI','-3');
    check('邊界讀取未完成時輸入仍是未套用草稿',await eval_(`$('igCellI').value==='-3' && document.querySelector('#projectBar [data-project-action="save"]').disabled && $('igSaveBinding').disabled`));
    await eval_('window.__gridDraftDelay.release();void 0');await wait(`!$('igSaveBinding').disabled && !!$('igKeyedVertices').firstElementChild`);
    check('原生回應到達不把途中輸入當成已保存基準',await eval_(`$('igCellI').value==='-3' && document.querySelector('#projectBar [data-project-action="save"]').disabled && !$('igSaveBinding').disabled && /配置尚未/.test($('igDraftNote').textContent)`)&&(await dump())===baseline);
    await expectNativeDialog(()=>ctl('#igClose'),{message:leaveMessage,accept:false});
    check('取消退出保留延遲期間的cell草稿',await eval_(`$('infiniteGridWorkspace').open && $('igCellI').value==='-3'`));
  } finally {
    await eval_(`(()=>{const gate=window.__gridDraftDelay;if(gate){if(gate.release&&!gate.released)gate.release();window.apiRequest=gate.original;delete window.__gridDraftDelay;}return true;})()`);
  }
  await fill('#igCellI','0');await wait(`!document.querySelector('#projectBar [data-project-action="save"]').disabled`);await ctl('#igKeyedEditor > summary');
  const firstKey=await eval_(`$('igKeyedVertices').querySelector('[data-ig-key]').dataset.igKey`),vertexSelector='#igKey'+firstKey+'U';
  await fill(vertexSelector,'90');await fill('#igGrowLeft','120');
  check('頂點與尚未填入的擴大量都阻止保存專案',await eval_(`document.querySelector('#projectBar [data-project-action="save"]').disabled && $('igGrowLeft').value==='120' && /擴大量/.test($('igDraftNote').textContent)`)&&(await dump())===baseline);
  await expectNativeDialog(()=>choose('#igBoundary','802','801'),{message:switchMessage,accept:false});
  check('取消切換保留原邊界、頂點值與擴大量',await eval_(`$('igBoundary').value==='801' && $('igGrowLeft').value==='120' && document.querySelector(${JSON.stringify(vertexSelector)}).value==='90' && document.querySelector('#projectBar [data-project-action="save"]').disabled`)&&(await dump())===baseline);
  await expectNativeDialog(()=>ctl('#igClose'),{message:leaveMessage,accept:false});
  check('取消退出也完整保留兩類邊界草稿',await eval_(`$('infiniteGridWorkspace').open && $('igGrowLeft').value==='120' && document.querySelector(${JSON.stringify(vertexSelector)}).value==='90'`));
  await expectNativeDialog(()=>choose('#igBoundary','802'),{message:switchMessage,accept:true});await wait(`$('igVertex').options.length===5`);
  check('明示捨棄後新邊界不沿用舊頂點或擴大量',await eval_(`$('igBoundary').value==='802' && ['Left','Right','Top','Bottom'].every(a=>$('igGrow'+a).value==='0') && !document.querySelector(${JSON.stringify(vertexSelector)}) && document.querySelector('#projectBar [data-project-action="save"]').disabled`)&&(await dump())===baseline);
  await expectNativeDialog(()=>ctl('#igClose'),{message:leaveMessage,accept:true});
  check('退出全部草稿後原生世界逐字未變',(await dump())===baseline);
};
