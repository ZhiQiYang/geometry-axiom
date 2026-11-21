// 11-21b 共用：沿用 11-14 的 lib1113.js（開頁、存檔、開檔、新專案），另加唯讀狀態讀取。
// page.evaluate 只做唯讀：dump、objects、engineering-read、ReferenceWorkspace.history 長度、畫面文字。
const path = require('path');
const L = require(path.resolve(__dirname, '../../l4-cloud-20261114/scripts/lib1113.js'));
const fs = require('fs');
module.exports = Object.assign({}, L, {
  hist: p => p.evaluate(() => { const h = ReferenceWorkspace.history; return { undo: h.undo.length, redo: h.redo.length, group: h.group === null ? null : 'open' }; }),
  dump: p => p.evaluate(async () => (await apiRequest('dump')).text),
  objects: p => p.evaluate(async () => await apiRequest('objects')),
  dialogs: p => p.evaluate(() => [...document.querySelectorAll('dialog[open], [role=dialog], [role=alertdialog]')].filter(e => e.offsetParent || e.open).map(e => e.innerText.replace(/\s+/g, ' ').slice(0, 600))),
  menu: p => p.$$eval('[role=menu]:not([hidden]) [role=menuitem], [role=menu]:not([hidden]) [role=menuitemcheckbox]', els => els.filter(e => e.offsetParent).map(e => e.textContent.trim().replace(/\s+/g, ' ') + (e.getAttribute('aria-disabled') === 'true' || e.disabled ? ' [停用]' : ''))),
  shooter: dir => { fs.mkdirSync(dir + '/screens', { recursive: true }); return (p, n) => p.screenshot({ path: `${dir}/screens/${n}.jpg`, type: 'jpeg', quality: 70 }); },
  writeResult: (file, r) => fs.writeFileSync(file, JSON.stringify(r, null, 2) + '\n'),
});
