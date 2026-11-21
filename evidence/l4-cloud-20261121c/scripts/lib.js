// 2026-11-21c 共用：沿用 evidence/l4-cloud-20261114/scripts/lib1113.js（不修改它），另加 jpg 截圖、結果輸出與歷史提示讀取。
const path = require('path');
const fs = require('fs');
const L = require(path.resolve(__dirname, '../../l4-cloud-20261114/scripts/lib1113.js'));
module.exports = Object.assign({}, L);
const OUT = () => process.env.OUT;
module.exports.out = OUT;
module.exports.shotter = (p, prefix) => async name => {
  fs.mkdirSync(`${OUT()}/screens`, { recursive: true });
  await p.screenshot({ path: `${OUT()}/screens/${prefix}-${name}.jpg`, type: 'jpeg', quality: 72 });
};
module.exports.write = (name, r) => { fs.writeFileSync(`${OUT()}/${name}`, JSON.stringify(r, null, 1)); };
// 唯讀：最後一則狀態列／toast 文字
module.exports.toasts = p => p.evaluate(() => [...document.querySelectorAll('.toast, #status, [role=status]')].filter(e => e.offsetParent && e.textContent.trim()).map(e => e.textContent.trim().replace(/\s+/g, ' ').slice(0, 200)));
module.exports.dump = async p => (await L.snap(p)).text;
