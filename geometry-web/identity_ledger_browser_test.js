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

  const origin = new URL(process.env.GEOMETRY_TEST_URL).origin;
  await send('Storage.clearDataForOrigin', {origin, storageTypes: 'all'});
  await send('Page.navigate', {url: process.env.GEOMETRY_TEST_URL});
  await waitForUI(`typeof api === 'function' && typeof oc === 'object' && connection.phase === 'ready'`, 30000);
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
  check('reopen keeps the mark', !!(reopened && reopened.ok && reopened.marks && reopened.marks[0] && reopened.marks[0].mark === before.marks[0].mark));
};
