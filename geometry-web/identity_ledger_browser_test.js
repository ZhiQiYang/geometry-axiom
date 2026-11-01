/* Fresh-profile identity ledger: preview, confirm, cancel, save, reopen.
   Browser-only. This file is not a node unit test. */
'use strict';
const cdp = require('./cdp_helpers.js');

module.exports = async function identityLedgerBrowser({send, eval_, sleep, click, waitForUI}) {
  const check = cdp.makeCheck({prefix: 'IL ', throwOnFail: true});
  const boundary = 'boundary 1 outline 0,0 2000,0 2000,1000 0,1000';

  async function clickSelector(selector) {
    const point = await eval_(`(() => {
      const element = document.querySelector(${JSON.stringify(selector)});
      if (!element) return null;
      const rect = element.getBoundingClientRect();
      return {x: rect.x + rect.width / 2, y: rect.y + rect.height / 2, w: rect.width, h: rect.height, disabled: !!element.disabled};
    })()`);
    if (!point || !point.w || !point.h || point.disabled) throw Error('Unreachable control ' + selector + ' ' + JSON.stringify(point));
    await click(point.x, point.y);
    await sleep(150);
  }

  check('ledger script loaded', await eval_(`typeof IdentityLedger === 'object' && typeof IdentityLedger.settleKey === 'function'`) === true);
  check('reset', (await eval_(`api('reset')`)).ok === true);

  await eval_(`window.__ilResult = api(${JSON.stringify('line preview ' + boundary)}); true`);
  await waitForUI(`!!document.querySelector('.reference-impact')`);
  await clickSelector('.reference-impact .impact-actions button');
  const cancelled = await eval_(`window.__ilResult`);
  check('preview cancel keeps the scene', cancelled.ok === false);

  await eval_(`window.__ilResult = api(${JSON.stringify('line preview ' + boundary)}); true`);
  await waitForUI(`!!document.querySelector('#impact-confirm') && !document.querySelector('#impact-confirm').disabled`);
  await clickSelector('#impact-confirm');
  const confirmed = await eval_(`window.__ilResult`);
  check('preview confirm creates the boundary', confirmed.ok === true);

  const activated = await eval_(`api('line identity-ledger activate')`);
  check('activate', activated.ok === true);
  const second = await eval_(`api('line identity-ledger activate')`);
  check('second activate rejected', second.ok === false && String(second.error || '').includes('身分帳已啟用'));
  const forged = await eval_(`api('line identity boundary 1 0123456789abcdef0123456789abcdef:1')`);
  check('interactive identity rejected', forged.ok === false && String(forged.error || '').includes('互動輸入不得宣告 identity'));
  const epoch = await eval_(`api('identity-epoch 0123456789abcdef0123456789abcdef')`);
  check('page cannot set epoch', epoch.ok === false && epoch.error === '配號區段只由宿主設定。');

  const before = await eval_(`api('identity-read')`);
  check('mark issued', before.ok === true && before.active === true && before.marks.length === 1 && typeof before.marks[0].mark === 'string');

  const fullScene = await eval_(`api('dump')`);
  const rejectedImport = await eval_(`(async () => {
    const original = ${JSON.stringify(fullScene.text)};
    const lines = original.split('\\n');
    const invalid = lines.filter(line => line.trim() !== 'requires identity-ledger/1').join('\\n');
    const response = await fetch('/upload/prepare', {method: 'POST', headers: {'Content-Type': 'text/plain;charset=utf-8'}, body: invalid});
    return {removed: original !== invalid, result: await response.json()};
  })()`);
  check('native import rejects marks without requires', rejectedImport.removed && rejectedImport.result.ok === false &&
    String(rejectedImport.result.error || '').includes('I72: 記號行缺少 requires identity-ledger/1') &&
    !Object.hasOwn(rejectedImport.result, 'token'));
  const unchangedScene = await eval_(`api('dump')`);
  const unchangedLedger = await eval_(`api('identity-read')`);
  check('rejected identity import keeps full World and serial', unchangedScene.text === fullScene.text && JSON.stringify(unchangedLedger) === JSON.stringify(before));

  await eval_(`window.__ilSaved = null; window.showSaveFilePicker = async () => ({
    createWritable: async () => ({
      write: async (data) => {
        const bytes = data instanceof Uint8Array ? data : new Uint8Array(await data.arrayBuffer());
        let text = '';
        for (let index = 0; index < bytes.length; index++) text += String.fromCharCode(bytes[index]);
        window.__ilSaved = btoa(text);
      },
      close: async () => {},
      abort: async () => {},
    }),
  }); true`);
  await clickSelector('#projectBar [data-project-action="save"]');
  await waitForUI(`typeof window.__ilSaved === 'string' && window.__ilSaved.length > 0`, 30000);
  const saved = await eval_(`window.__ilSaved`);
  check('save wrote bytes', typeof saved === 'string' && saved.length > 0);
  const savedWorld = await eval_(`api('dump')`);

  const origin = new URL(process.env.GEOMETRY_TEST_URL).origin;
  await send('Storage.clearDataForOrigin', {origin, storageTypes: 'all'});
  await send('Page.navigate', {url: process.env.GEOMETRY_TEST_URL});
  await waitForUI(`typeof api === 'function' && typeof oc === 'object' && connection.phase === 'ready'`, 30000);
  const cold = await eval_(`(async () => ({reset: await api('reset'), ledger: await api('identity-read')}))()`);
  if (cold.reset.ok !== true || cold.ledger.ok !== true || cold.ledger.active !== false || cold.ledger.marks.length !== 0)
    throw Error('IL cold-open setup did not clear the native ledger');
  await eval_(`(() => {
    const binary = atob(${JSON.stringify(saved)});
    const bytes = Uint8Array.from(binary, char => char.charCodeAt(0));
    const file = new File([bytes], 'identity-reopen.gcanvas', {type: 'application/zip'});
    const input = document.getElementById('projectFile');
    const transfer = new DataTransfer();
    transfer.items.add(file);
    input.files = transfer.files;
    input.dispatchEvent(new Event('change', {bubbles: true}));
    return true;
  })()`);
  let reopened = null;
  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    reopened = await eval_(`api('identity-read')`);
    if (reopened && reopened.ok && reopened.marks && reopened.marks[0] && reopened.marks[0].mark === before.marks[0].mark) break;
    await sleep(100);
  }
  await waitForUI(`typeof ReferenceWorkspace === 'object' && !ReferenceWorkspace.busy`, 30000);
  const reopenedWorld = await eval_(`api('dump')`);
  check('reopen keeps the mark', !!(reopened && reopened.ok && reopened.active === true &&
    JSON.stringify(reopened.marks) === JSON.stringify(before.marks) && reopened.nextSerial >= cold.ledger.nextSerial &&
    reopenedWorld.ok === true && reopenedWorld.text === savedWorld.text));
};
