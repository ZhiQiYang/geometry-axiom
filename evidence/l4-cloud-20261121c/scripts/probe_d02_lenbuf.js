// D02 發現 1 的重現：重畫外環點兩點後鍵入「12」，鍵入長度欄 #feLenInput 的內容是否看得到（唯讀檢查最上層元素＋局部截圖）。
const L = require('./lib.js');
const fs = require('fs');
const r = {};
const check = async (p, tag) => {
  const info = await p.evaluate(() => { const i = document.getElementById('feLenInput'); if (!i) return null; const b = i.getBoundingClientRect();
    const at = (x, y) => { const e = document.elementFromPoint(x, y); return e ? (e.id ? '#' + e.id : e.tagName.toLowerCase()) + ' ' + (e.getAttribute('class') || '') + ' ｜' + (e.textContent || '').trim().slice(0, 24) : null; };
    return { value: i.value, rect: [Math.round(b.left), Math.round(b.top), Math.round(b.width), Math.round(b.height)], topAtTextStart: at(b.left + 10, b.top + b.height / 2), topAtCenter: at(b.left + b.width / 2, b.top + b.height / 2) }; });
  r[tag] = info;
  if (info) { fs.mkdirSync(`${L.out()}/screens`, { recursive: true }); await p.screenshot({ path: `${L.out()}/screens/D02-F1-${tag}.jpg`, type: 'jpeg', quality: 80, clip: { x: info.rect[0] - 140, y: info.rect[1] - 50, width: 380, height: 110 } }); }
};
(async () => {
  const { b, p } = await L.start();
  await L.newProject(p); await p.click('#btnNewPoly'); await p.waitForTimeout(1500);
  for (const [x, y] of [[0, 0], [2000, 0]]) { const t = await L.pt(p, x, y); await p.mouse.click(t.x, t.y); await p.waitForTimeout(300); }
  await p.keyboard.type('12'); await p.waitForTimeout(400);
  await check(p, 'a-guidance-open');
  // 關掉說明卡（點卡上的「知道了」），再看一次
  await p.locator('#faceCanvasHint button', { hasText: '知道了' }).first().click().catch(() => {}); await p.waitForTimeout(400);
  r.guidanceOpenAfterDismiss = await p.isVisible('#faceCanvasHint.guidance-open');
  await check(p, 'b-guidance-closed');
  await p.keyboard.press('ArrowDown'); await p.waitForTimeout(600);
  r.afterArrowDown = (await p.textContent('#faceDraftNotice')).replace(/\s+/g, ' ').slice(0, 40);
  r.draftLastSegment = await p.evaluate(() => [...document.querySelectorAll('#faceEditorRoot text')].map(t => t.textContent).filter(t => /mm$/.test(t)).slice(0, 6));
  L.write('probe_d02_lenbuf.result.json', r); console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.stack.slice(0, 600)); process.exit(1); });
