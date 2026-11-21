// D05 操作當下留回報（GEO-183）：只用滑鼠與鍵盤。服務與本腳本都設 GEOMETRY_FEEDBACK_DIR（不寫進 repo 的 feedback/）。
// 新專案 → 工具列「多邊形 P」建一個面 → 按 F8 開回報面板 → 填說明 →「指出位置」點「復原」鈕 →「取消」（不留紀錄）
// → 右下「回報」鈕 → 填說明 →「指出位置」點「保存」鈕 → Ctrl+Enter 送出 → Shift+F8 快速標記
// → 回報目錄裡應各一筆；用 feedback_cli.py list／show 讀回（與 agent 實際讀法相同）。
const L = require('./lib.js');
const fs = require('fs');
const { execFileSync } = require('child_process');
const FB = process.env.GEOMETRY_FEEDBACK_DIR;
const r = { feedbackDir: FB ? '(scratch，不在 repo)' : null };
const list = () => fs.existsSync(FB) ? fs.readdirSync(FB).filter(n => fs.statSync(`${FB}/${n}`).isDirectory()).sort() : [];
(async () => {
  if (!FB) throw Error('需要 GEOMETRY_FEEDBACK_DIR');
  const before = list(); r.recordsBefore = before.length;
  const { b, p, errs } = await L.start();
  const shot = L.shotter(p, 'D05');
  await L.newProject(p); await p.click('#btnNewPoly'); await p.waitForTimeout(1500); await L.lesson(p); await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  const d0 = await L.dump(p);
  // 1) F8 → 填 → 指出位置 → 取消
  await p.keyboard.press('F8'); await p.waitForTimeout(600);
  r.panelOpenByF8 = await p.isVisible('#fbPanel');
  await p.click('#fbNote'); await p.keyboard.type('L4 核對：這筆會取消，不應留下');
  await p.click('#fbPick'); await p.waitForTimeout(300); await p.click('#btnUndo'); await p.waitForTimeout(400);
  r.pickedTarget1 = (await p.textContent('#fbTarget')).trim();
  await shot('01-f8-panel-picked');
  await p.click('#fbCancel'); await p.waitForTimeout(800);
  r.panelClosedAfterCancel = !(await p.isVisible('#fbPanel'));
  r.recordsAfterCancel = list().length - before.length;
  r.sceneUnchangedAfterPick = (await L.dump(p)) === d0;
  // 2) 右下「回報」鈕 → 填 → 指出「保存」→ Ctrl+Enter
  await p.click('#fbButton'); await p.waitForTimeout(600);
  r.panelOpenByButton = await p.isVisible('#fbPanel');
  await p.click('#fbNote'); await p.keyboard.type('L4 核對 D05：送出這一筆（20261121c）');
  await p.click('#fbPick'); await p.waitForTimeout(300);
  await p.locator('button:visible', { hasText: '保存' }).first().click(); await p.waitForTimeout(400);
  r.pickedTarget2 = (await p.textContent('#fbTarget')).trim();
  await shot('02-button-panel-picked');
  await p.keyboard.press('Control+Enter'); await p.waitForTimeout(3000);
  r.msgAfterSend = (await p.textContent('#fbMsg').catch(() => '')).trim(); r.toastsAfterSend = await L.toasts(p);
  await shot('03-sent');
  r.recordsAfterSend = list().length - before.length;
  // 3) Shift+F8 快速標記
  await p.keyboard.press('Shift+F8'); await p.waitForTimeout(3000);
  r.toastsAfterQuick = await L.toasts(p);
  await shot('04-quick-mark');
  r.recordsAfterQuick = list().length - before.length;
  r.sceneUnchanged = (await L.dump(p)) === d0;
  r.errs = errs;
  await b.close();
  const added = list().filter(n => !before.includes(n));
  r.added = added.map(id => ({ files: fs.readdirSync(`${FB}/${id}`).sort() }));
  const env = { ...process.env };
  r.cliList = execFileSync('python3', ['geometry-web/feedback_cli.py', 'list'], { env, encoding: 'utf8' }).split('\n').filter(l => added.some(a => l.includes(a))).map(l => l.replace(/F-\d{8}-\d+[-\w]*/, 'F-…'));
  r.cliShow = added.map(id => { const t = execFileSync('python3', ['geometry-web/feedback_cli.py', 'show', id], { env, encoding: 'utf8' }); return { note: (t.match(/L4 核對[^\n]*|快速標記[^\n]*/) || [null])[0], target: (t.match(/(button#\w+|元素[^\n]*)/) || [null])[0], hasWorldScene: /world\.scene/.test(t), lines: t.split('\n').length }; });
  L.write('walk_d05.result.json', r); console.log(JSON.stringify(r, null, 1));
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); L.write('walk_d05.partial.json', r); process.exit(1); });
