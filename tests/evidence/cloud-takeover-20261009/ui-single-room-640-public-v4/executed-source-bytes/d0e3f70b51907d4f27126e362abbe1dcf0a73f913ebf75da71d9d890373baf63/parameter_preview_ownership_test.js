/* Hold actual native receipts, never substitute candidate or confirm results. */
const cdp = require('./cdp_helpers.js');
module.exports = async ({send, eval_, sleep, click, waitForUI, check}) => {
  const read = eval_, wait = cdp.makeWait(waitForUI, 15000);
  const controls = {scroll: 'center', attempts: 1, pollMs: 130, settleMs: 120, missing: 'missing ', unreachable: (s,p) => 'Parameter preview control covered '+s+' '+JSON.stringify(p)};
  const ctl = cdp.makeCtl({eval_,sleep,click}, controls);
  const attemptCtl = cdp.makeCtl({eval_,sleep,click}, {...controls, ready: p => !!(p?.hit&&p.w&&p.h)});
  const key = cdp.makeKey({send,sleep}), fill = cdp.makeFill({ctl,key,send,sleep});
  const ready = `!ParameterUI.previewing && !!$('paramConfirm') && !$('paramConfirm').disabled`;
  console.log('=== P76 參數預覽與確認候選所有權 ===');
  await send('Emulation.setDeviceMetricsOverride', {width:1400,height:1000,deviceScaleFactor:1,mobile:false});
  await read(`(async()=>{ParameterUI.discard();resetSceneFocus();ocSetSelection([]);await api('reset');await renderObjects();})()`);
  await read(`(()=>{
    const original=window.fetch.bind(window), g=window.__parameterReceipts={hold:null,receipts:[],events:[]};
    g.restore=()=>window.fetch=original;
    window.fetch=async(...args)=>{
      const command=String(args[0])==='/api'?JSON.parse(args[1]?.body||'{}').cmd:String(args[0]);
      const held=g.hold===command; if(held)g.hold=null;
      const request={command,time:performance.now()};g.events.push(request);
      const response=await original(...args);
      if(command==='engineering-read'||command==='/engineering/preview'||command?.startsWith('engineering-confirm ')){
        const json=response.json.bind(response);response.json=async()=>{
          const result=await json();request.receiptTime=performance.now();request.token=result.preview?.token;request.ok=result.ok;request.error=result.error;
          if(held)await new Promise((resolve,reject)=>g.receipts.push({command,result,release:resolve,reject}));
          request.deliveryTime=performance.now();return result;
        };
      }
      return response;
    };
  })()`);
  const hold = async command => {
    const count = await read(`__parameterReceipts.receipts.length`);
    await read(`__parameterReceipts.hold=${JSON.stringify(command)};void 0`);
    return count;
  };
  const held = n => wait(`__parameterReceipts.receipts.length>${n}`);
  const release = n => read(`__parameterReceipts.receipts[${n}].release();void 0`);
  const create = async name => {
    await read(`ParameterUI.create()`);await wait(`$('paramName')?.value==='參數'`);
    await fill('#paramName',name);await fill('[data-input]','3');await wait(ready);
  };
  try {
    await create('候選所有權');
    const originalDump = await read(`apiRequest('dump').then(r=>r.text)`);
    const oldToken = await read(`__parameterReceipts.events.filter(e=>e.command==='/engineering/preview').at(-1).token`);
    const readGate = await hold('engineering-read');await ctl('#paramPreview');await held(readGate);
    check('重算在來源讀取回覆前撤銷舊確認，欄位仍可編輯', await read(`ParameterUI.previewing&&$('paramConfirm').disabled&&!document.querySelector('[data-input]').disabled&&document.querySelector('[data-result]').dataset.state==='pending'`));
    const writes = await read(`__parameterReceipts.events.filter(e=>e.command?.startsWith('engineering-confirm ')).length`);
    await attemptCtl('#paramConfirm');await read(`$('paramConfirm').onclick();void 0`);
    check('真連點及直接舊 handler 在重算期間都不送確認', await read(`__parameterReceipts.events.filter(e=>e.command?.startsWith('engineering-confirm ')).length===${writes}`));
    const oldRejected = await read(`apiRequest('engineering-confirm ${oldToken}').then(r=>!r.ok&&r.code==='TOKEN')`);
    check('旧 token 仍由原生核心拒絕且正式 dump 不變', oldRejected && await read(`apiRequest('dump').then(r=>r.text===${JSON.stringify(originalDump)})`));
    await release(readGate);await wait(ready);

    const failed = await hold('/engineering/preview');await ctl('#paramPreview');await held(failed);
    check('原生候選已產生但回覆未到仍不能確認', await read(`ParameterUI.previewing&&$('paramConfirm').disabled`));
    await read(`__parameterReceipts.receipts[${failed}].reject(Error('parameter receipt delivery failed'));void 0`);
    await wait(`!ParameterUI.previewing&&$('paramStatus').textContent.includes('parameter receipt delivery failed')`);
    check('重算回覆失敗不復活舊候選，保留可修正草稿', await read(`$('paramConfirm').disabled&&ParameterUI.pending&&!document.querySelector('[data-input]').disabled`));

    const first = await hold('/engineering/preview');await ctl('#paramPreview');await held(first);
    const second = await hold('/engineering/preview');await ctl('#paramPreview');await held(second);
    await release(first);await wait(`__parameterReceipts.events.filter(e=>e.command==='/engineering/preview').at(-2).deliveryTime!=null`);
    // Drain the discarded receipt's continuation through its token-scoped cancel.
    await wait(`__parameterReceipts.events.some(e=>e.command==='engineering-cancel '+__parameterReceipts.receipts[${first}].result.preview.token)`);
    check('連續重算的舊回覆不解除新請求 pending 或啟用舊確認', await read(`ParameterUI.previewing&&$('paramConfirm').disabled`));
    await release(second);await wait(ready);
    const candidate = await read(`__parameterReceipts.receipts[${second}].result.preview.token`);
    const confirmGate = await hold('engineering-confirm '+candidate);await ctl('#paramConfirm');await held(confirmGate);
    await attemptCtl('#paramConfirm');await read(`$('paramConfirm').onclick();void 0`);
    check('新候選確認連點只送一次且回覆前保持輸入鎖定', await read(`__parameterReceipts.events.filter(e=>e.command==='engineering-confirm ${candidate}').length===1&&$('parameterEditor').getAttribute('aria-busy')==='true'&&document.querySelector('[data-input]').disabled`));
    await release(confirmGate);await wait(`!ParameterUI.pending`);
    check('只有最新已看過候選被提交，正常建立值為3', await read(`apiRequest('engineering-read').then(r=>r.state.parameters.length===1&&r.state.parameters[0].fields[0].value.num==='3')`));
    const saved = await read(`(async()=>{ParameterUI.discard();window.__parameterOwnershipSaved=await ReferenceWorkspace.exportBytes();return (await apiRequest('dump')).text;})()`);
    await read(`api('line undo')`);await read(`renderObjects()`);
    check('候選確認仍是一筆原生 undo', await read(`apiRequest('engineering-read').then(r=>r.state.parameters.length===0)`));
    await read(`api('line redo')`);await read(`renderObjects()`);
    check('redo 恢復同一完整定義', await read(`apiRequest('dump').then(r=>r.text===${JSON.stringify(saved)})`));
    await read(`ReferenceWorkspace.importBytes(__parameterOwnershipSaved,'候選所有權.gcanvas')`);
    check('完整專案保存重開保留精確定義', await read(`apiRequest('dump').then(r=>r.text===${JSON.stringify(saved)})`));

    await create('捨棄晚回覆');const discarded = await hold('/engineering/preview');await ctl('#paramPreview');await held(discarded);
    await ctl('#paramDiscard');
    await create('下一張草稿');const next = await hold('/engineering/preview');await ctl('#paramPreview');await held(next);
    await release(discarded);await wait(`__parameterReceipts.events.some(e=>e.command==='engineering-cancel '+__parameterReceipts.receipts[${discarded}].result.preview.token)`);
    check('捨棄後晚回覆不覆蓋下一張草稿或解除它的 pending', await read(`$('paramName').value==='下一張草稿'&&ParameterUI.previewing&&$('paramConfirm').disabled`));
    await release(next);await wait(ready);await ctl('#paramConfirm');await wait(`!ParameterUI.pending`);
    check('捨棄候選沒進世界，下一張可正常确认', await read(`apiRequest('engineering-read').then(r=>r.state.parameters.length===2&&!r.state.parameters.some(c=>c.name==='捨棄晚回覆')&&r.state.parameters.some(c=>c.name==='下一張草稿'))`));

    await create('切換晚回覆');const switched = await hold('/engineering/preview');await ctl('#paramPreview');await held(switched);
    await ctl('#paramDiscard');await read(`ReferenceWorkspace.importBytes(__parameterOwnershipSaved,'切換專案.gcanvas')`);
    const switchedDump = await read(`apiRequest('dump').then(r=>r.text)`);
    await release(switched);await wait(`__parameterReceipts.events.filter(e=>e.command==='/engineering/preview').at(-1).deliveryTime!=null`);
    check('專案切換後晚回覆不重開編輯器或改世界', await read(`apiRequest('dump').then(r=>r.text===${JSON.stringify(switchedDump)}&&!ParameterUI.pending&&!ParameterUI.previewing&&!$('parameterEditor'))`));
  } finally {
    await read(`__parameterReceipts.receipts.forEach(r=>r.release());__parameterReceipts.restore();ParameterUI.discard();void 0`);
  }
};
