/* cdp_test.js 與各外掛模組(P67~P76)共用的樣板:斷言、按鍵、填值、點擊、截圖。
 *
 * 設計原則(行為守恆):每個工廠只吸收「各模組本來就相同」的部分;模組間真正不同的地方
 * (sleep 毫秒數、失敗時 throw 或只記數、錯誤訊息文字、是否先開選單)一律以明示選項傳入,
 * 預設值不代表任何模組的實際設定,也不偷偷統一。
 *
 * 本檔只依賴 Node 內建模組;瀏覽器端(CDP)能力一律由呼叫端把 send/eval_/sleep/click 傳進來。 */
'use strict';

/* ---- 斷言 ----------------------------------------------------------------
 * 通過判定一律是 `value === true`:物件、數字、非空字串即使為真值也記為失敗,
 * 避免「回傳了某個東西就算通過」的假綠。呼叫端要傳明確的布林比較。
 *
 * options:
 *   prefix          印在名稱前的段號,例如 'P68 '(含尾端空白)。預設 ''。
 *   throwOnFail     true=第一個失敗就 throw(原本就會 throw 的模組);false=只記數。
 *   mark(ok)        把布林轉成印出的判定值。預設 '✓'/'✗' 字串;cdp_test 本體傳
 *                   explicitVerdict 版本,讓 harness 只計受控斷言。
 *   detail          呼叫端省略 detail 時怎麼辦:'value'=以 value 代替(多數模組);
 *                   'empty'=代以 '';'none'=維持 undefined(parameter_workflow_test 原本如此)。
 *   detailWhenPassing  true=通過時也印 JSON.stringify(detail)(cdp_test 本體 P24~P52/P53 舊格式)。
 *   failMessage(name, detail)  客製 throw 訊息(各模組原本的措辭不同)。預設
 *                   prefix+'assertion failed: '+name+' '+JSON.stringify(detail)。
 *   log             預設在呼叫時才取 console.log(harness 會替換它來計數,不可提早綁定)。 */
function makeCheck(options = {}) {
  const {
    prefix = '',
    throwOnFail = false,
    mark = ok => (ok ? '✓' : '✗'),
    detail: detailMode = 'value',
    detailWhenPassing = false,
    failMessage = null,
    log = (...args) => console.log(...args),
  } = options;
  if (!['value', 'empty', 'none'].includes(detailMode)) throw Error('makeCheck: detail must be "value", "empty" or "none"');
  return function check(name, value, detail) {
    const ok = value === true;
    if (detail === undefined && detailMode !== 'none') detail = detailMode === 'value' ? value : '';
    log(prefix + name, mark(ok), detailWhenPassing || !ok ? JSON.stringify(detail) : '');
    if (!ok && throwOnFail) {
      throw Error(failMessage ? failMessage(name, detail) : prefix + 'assertion failed: ' + name + ' ' + JSON.stringify(detail));
    }
  };
}

/* ---- 瀏覽器端讀值 -------------------------------------------------------- */

/* eval_ 加上「頁面回 {__err}」即丟錯。 */
function makeRead(eval_) {
  return async expression => {
    const value = await eval_(expression);
    if (value?.__err) throw Error(value.__err);
    return value;
  };
}

/* waitForUI 加上固定逾時。 */
function makeWait(waitForUI, timeout) {
  return expression => waitForUI(expression, timeout);
}

/* ---- 輸入 ---------------------------------------------------------------- */

/* 按鍵(keyDown+keyUp)。
 * afterMs  按完後的 sleep;0/省略=不 sleep(不呼叫 sleep,避免多一次 settle)。
 * enterText  true=Enter 的 keyDown 帶 text:'\r'(composition_canvas_test 原本如此)。 */
function makeKey({ send, sleep }, { afterMs = 0, enterText = false } = {}) {
  return async (key, code, vk, modifiers = 0) => {
    for (const type of ['keyDown', 'keyUp']) {
      await send('Input.dispatchKeyEvent', {
        type, key, code, windowsVirtualKeyCode: vk, modifiers,
        ...(enterText && type === 'keyDown' && key === 'Enter' ? { text: '\r' } : {}),
      });
    }
    if (afterMs > 0) await sleep(afterMs);
  };
}

/* 填值:點欄位 → Ctrl+A → insertText。afterMs 為最後的 sleep(0/省略=不 sleep)。 */
function makeFill({ ctl, key, send, sleep }, { afterMs = 0 } = {}) {
  return async (selector, value) => {
    await ctl(selector);
    await key('a', 'KeyA', 65, 2);
    await send('Input.insertText', { text: String(value) });
    if (afterMs > 0) await sleep(afterMs);
  };
}

/* 「先開選單再點」:目標在未展開的『建立物件』選單裡時,先點開它(桌面/手機入口不同)。
 * 回傳可直接當 makeCtl 的 before 用的函式。 */
function openCreateObjectMenu(read, ctl) {
  return async selector => {
    if (await read(`document.querySelector(${JSON.stringify(selector)})?.closest('#createObjectPop')?.hidden===true`)) {
      await ctl(await read(`innerWidth<=900?'#mobileCreateObject':'#btnCreateObject'`));
    }
  };
}

/* 點擊控制項:捲入視野 → 輪詢到「可見、未停用、中心點真的命中它」→ 真實滑鼠點擊 → 等待。
 * 只涵蓋「捲動→(睡→量測)×N→丟錯→點→睡」這一族寫法(project_audit、engineering_workflow、
 * grid_system、composition_canvas、grid_workspace_draft、parameter_workflow)。
 *
 * options(各模組原本的差異,全部明示):
 *   scroll      scrollIntoView 的 block:'center' 或 'nearest'。
 *   attempts    最多量測幾次。
 *   pollMs      每次量測「前」先 sleep 幾毫秒。
 *   settleMs    點完後 sleep 幾毫秒。
 *   missing     找不到元素時頁面端丟的錯誤前綴('missing '/'Missing ')。
 *   hitElement  true=量測結果多帶 hitElement(只影響失敗訊息)。
 *   unreachable(selector, p)  連續量測仍不可點時的錯誤訊息。
 *   before(selector)  點之前的前置動作(等元素出現、先開選單…)。
 *   after(selector)   點之後的後續動作。
 *   probe(selector) / ready(p)  換掉預設的量測與可點判定(composition_canvas 用自己的 box/visible)。 */
function makeCtl({ eval_, sleep, click }, options = {}) {
  const {
    scroll = 'nearest', attempts = 1, pollMs = 0, settleMs = 0,
    missing = 'Missing ', hitElement = false,
    unreachable = (selector, p) => 'Control unreachable ' + selector + ' ' + JSON.stringify(p),
    before = null, after = null, probe = null, ready = null,
  } = options;
  if (scroll !== 'center' && scroll !== 'nearest') throw Error('makeCtl: scroll must be "center" or "nearest"');
  const read = makeRead(eval_);
  const measure = probe || (selector => read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error(${JSON.stringify(missing)}+${JSON.stringify(selector)});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,h=document.elementFromPoint(x,y);return {x,y,w:r.width,h:r.height,hit:e.contains(h),${hitElement ? "hitElement:h?.tagName+'#'+h?.id," : ''}disabled:!!e.disabled};})()`));
  const usable = ready || (p => !!(p && p.hit && !p.disabled && p.w && p.h));
  return async function ctl(selector) {
    if (before) await before(selector);
    await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:${JSON.stringify(scroll)},inline:'nearest'});void 0`);
    let p;
    for (let attempt = 0; attempt < attempts; attempt++) {
      await sleep(pollMs);
      p = await measure(selector);
      if (usable(p)) break;
    }
    if (!usable(p)) throw Error(unreachable(selector, p));
    await click(p.x, p.y);
    await sleep(settleMs);
    if (after) await after(selector);
  };
}

/* ---- 截圖 ---------------------------------------------------------------- */

/* 把目前畫面存成 <dir>/<name>.png;dir 取自 envNames 中第一個有值的環境變數(呼叫時才讀),
 * 全都沒設就什麼都不做(預設不寫任何檔案)。 */
function makeShot(send, envNames) {
  const fs = require('fs'), path = require('path');
  return async name => {
    const dir = envNames.map(n => process.env[n]).find(Boolean);
    if (!dir) return;
    fs.mkdirSync(dir, { recursive: true });
    const result = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(path.join(dir, name + '.png'), Buffer.from(result.result.data, 'base64'));
  };
}

module.exports = { makeCheck, makeRead, makeWait, makeKey, makeFill, openCreateObjectMenu, makeCtl, makeShot };
