/* Hold the real native reply and attempt trusted input while confirming. */
const cdp=require('./cdp_helpers.js');
module.exports=async({send,eval_,sleep,click,waitForUI,check})=>{
 const read=eval_,wait=cdp.makeWait(waitForUI,15000),key=cdp.makeKey({send,sleep});
 const controls={scroll:'center',attempts:1,pollMs:130,settleMs:120,missing:'missing ',unreachable:(s,p)=>'Confirmation control covered '+s+' '+JSON.stringify(p)};
 const ctl=cdp.makeCtl({eval_,sleep,click},controls);
 const attemptCtl=cdp.makeCtl({eval_,sleep,click},{...controls,ready:p=>!!(p?.hit&&p.w&&p.h)});
 const attemptFill=cdp.makeFill({ctl:attemptCtl,key,send,sleep});
 const fill=cdp.makeFill({ctl,key,send,sleep});
 console.log('=== P76 確認期間保全參數輸入 ===');
 await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
 for(const mode of ['success','stale']){
  await read(`(async()=>{ParameterUI.discard();resetSceneFocus();ocSetSelection([]);await api('reset');const r=await apiRequest('engineering-read');const p=await EngineeringAdapter.preview({expectedRevision:r.revision,operations:[{op:'put-parameter',value:{id:1,name:'確認輸入保全',nextFieldId:2,fields:[{id:1,name:'寬',type:'dimension',input:'11'}]}}]});await EngineeringAdapter.confirm({token:p.token});await renderObjects();})()`);
  await read(`(()=>{const original=window.fetch,g=window.__paramLegacyGuard={held:false};const gate=new Promise(resolve=>g.release=resolve);g.restore=()=>window.fetch=original;
   window.fetch=async(...args)=>{const body=String(args[0])==='/api'?JSON.parse(args[1]?.body||'{}'):{};const response=await original(...args);
    if(body.cmd==='references'&&$('paramLegacy')&&!g.held){const json=response.json.bind(response);response.json=async()=>{const result=await json();g.held=true;await gate;return result;};}return response;};
  })()`);
  await read(`ParameterUI.jump('parameter',1)`);await wait(`__paramLegacyGuard.held`);
  await ctl('#paramExchange > summary');
  await fill('[data-param-field="1"] [data-input]','27');await ctl('#paramPreview');await wait(`!$('paramConfirm').disabled`);
  await read(`(()=>{const original=window.fetch,g=window.__paramConfirmGuard={held:false,calls:0};const gate=new Promise(resolve=>g.release=resolve);
   g.restore=()=>window.fetch=original;
   window.fetch=async(...args)=>{const body=String(args[0])==='/api'?JSON.parse(args[1]?.body||'{}'):{};
    const confirmation=body.cmd?.startsWith('engineering-confirm ');
    if(confirmation){g.calls++;if(${JSON.stringify(mode)}==='stale'){g.held=true;await gate;}}
    const response=await original(...args);
    if(confirmation&&${JSON.stringify(mode)}==='success'){const json=response.json.bind(response);response.json=async()=>{const result=await json();g.held=true;await gate;return result;};}
    return response;};
  })()`);
  await ctl('#paramConfirm');await wait(`__paramConfirmGuard.held`);
  await read(`__paramLegacyGuard.release();void 0`);await wait(`!!$('paramSpecValue')`);
  const locked=await read(`$('parameterEditor').getAttribute('aria-busy')==='true'&&[...$('parameterEditor').querySelectorAll('button,input,select,textarea')].every(e=>e.disabled)`);
  // Disabled controls still have real hit targets. Trusted typing must not be accepted.
  await attemptFill('[data-param-field="1"] [data-input]','99');
  const during=await read(`document.querySelector('[data-param-field="1"] [data-input]').value`);
  await attemptFill('#paramSpecValue','99');
  const late=await read(`({input:$('paramSpecValue').value,controls:['paramSpec','paramSpecValue','paramSpecSave'].map(id=>({id,disabled:$(id).disabled}))})`);
  if(mode==='stale')await read(`api('line spec ParameterConfirmRevision 1')`);
  await read(`__paramConfirmGuard.release();void 0`);
  await wait(mode==='success'?`!ParameterUI.pending`:`!document.querySelector('[data-param-field="1"] [data-input]').disabled&&$('paramConfirm').disabled&&ParameterUI.pending`);
  const after=await read(`(async()=>({input:document.querySelector('[data-param-field="1"] [data-input]').value,disabled:document.querySelector('[data-param-field="1"] [data-input]').disabled,native:(await apiRequest('engineering-read')).state.parameters[0].fields[0].value.num,pending:ParameterUI.pending,calls:__paramConfirmGuard.calls}))()`);
  await read(`__paramConfirmGuard.restore();void 0`);
  await read(`__paramLegacyGuard.restore();void 0`);await wait(`!!$('paramSpecValue')`);
  check('確認 '+mode+' 回覆未到時拒絕編輯，不接受後再丟失99',locked&&during==='27',{locked,during,late,after});
  check('確認 '+mode+' 延遲載入舊規格也鎖定，不接受途中99',late.input===''&&late.controls.every(e=>e.disabled),late);
  check('確認 '+mode+' 完成後解鎖並保留正確正式值／草稿',after.input==='27'&&!after.disabled&&after.native===(mode==='success'?'27':'11')&&after.pending===(mode!=='success')&&after.calls===1,after);
  check('確認 '+mode+' 新插入控制於結束後恢復可操作',await read(`['paramSpec','paramSpecValue','paramSpecSave'].every(id=>!$(id).disabled)`));
  await fill('[data-param-field="1"] [data-input]','99');await ctl('#paramPreview');await wait(`!$('paramConfirm').disabled`);await ctl('#paramConfirm');await wait(`!ParameterUI.pending`);
  check('確認 '+mode+' 恢復後可明確試算並提交99',await read(`(async()=>(await apiRequest('engineering-read')).state.parameters[0].fields[0].value.num==='99'&&document.querySelector('[data-param-field="1"] [data-input]').value==='99')()`));
 }
};
