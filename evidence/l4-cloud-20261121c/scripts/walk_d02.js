// D02 主畫布畫房間形狀（GEO-176～181、185～187、189）：只用滑鼠與鍵盤。
// 新專案 → 工具列「多邊形 P」（建預設面並進面內重畫外環）→ 鍵入 4000→ 1500↓ 2500← 1500↓（草稿預覽）→「放棄草稿」（取消）
// → 再鍵入一次 →「完成外環」（確認）→「外環 E」用滑鼠逐點點 5 點 → Enter（自動補直角閉合）
// → Ctrl+Z ×3／Ctrl+Y ×3 → Esc 階梯 → 回物件畫布 → 另存 → 全新瀏覽器開檔。
const L = require('./lib.js');
const r = { steps: [] };
const outline = t => (t.match(/^boundary 1 outline .*$/m) || [null])[0];
(async () => {
  let { b, p, errs } = await L.start();
  let shot = L.shotter(p, 'D02');
  const step = async (name, extra = {}) => { const d = await L.dump(p); const s = { name, outline: outline(d), dumpLen: d.length, inFace: await p.isVisible('#workspaceBackButton'), ...extra }; r.steps.push(s); await shot(name); return d; };
  await L.newProject(p);
  const d0 = await step('01-new-project');
  await p.click('#btnNewPoly'); await p.waitForTimeout(1500);
  const dA = await step('02-placeholder-redraw', { draftNotice: await p.textContent('#faceDraftNotice').catch(() => null) });
  await L.lesson(p);
  // 鍵盤 L 形草稿（預覽）
  for (const [n, k] of [['4000', 'ArrowRight'], ['1500', 'ArrowDown'], ['2500', 'ArrowLeft'], ['1500', 'ArrowDown']]) { await p.keyboard.type(n); await p.keyboard.press(k); await p.waitForTimeout(250); }
  const dDraft = await step('03-keyboard-draft-preview', { draftNotice: (await p.textContent('#faceDraftNotice').catch(() => '')).replace(/\s+/g, ' ') });
  r.draftWritesNothing = dDraft === dA;
  // 取消
  await p.click('#faceDraftCancel'); await p.waitForTimeout(1200);
  const dCancel = await step('04-cancel-draft');
  r.cancelZeroWrite = dCancel === dA;
  // 再畫一次並確認
  await p.click('[data-face-tool="redraw"]'); await p.waitForTimeout(600); await L.lesson(p);
  for (const [n, k] of [['4000', 'ArrowRight'], ['1500', 'ArrowDown'], ['2500', 'ArrowLeft'], ['1500', 'ArrowDown']]) { await p.keyboard.type(n); await p.keyboard.press(k); await p.waitForTimeout(250); }
  await p.click('#faceDraftFinish'); await p.waitForTimeout(1800);
  const dK = await step('05-confirm-keyboard-L', { toasts: await L.toasts(p) });
  // 滑鼠逐點 + Enter 自動補直角
  await p.click('[data-face-tool="redraw"]'); await p.waitForTimeout(600); await L.lesson(p);
  const pts = [[0, 0], [3000, 0], [3000, 2000], [1500, 2000], [1500, 3000]];
  r.clicked = [];
  for (const [x, y] of pts) { const t = await L.pt(p, x, y); await p.mouse.move(t.x, t.y); await p.waitForTimeout(150); await p.mouse.click(t.x, t.y); await p.waitForTimeout(350); r.clicked.push([x, y]); }
  const dM = await step('06-mouse-draft-5pts', { draftNotice: (await p.textContent('#faceDraftNotice').catch(() => '')).replace(/\s+/g, ' ') });
  r.mouseDraftWritesNothing = dM === dK;
  await p.keyboard.press('Enter'); await p.waitForTimeout(1800);
  const dB = await step('07-enter-auto-corner', { toasts: await L.toasts(p) });
  // 復原／重做
  await p.keyboard.press('Control+z'); await p.waitForTimeout(1500); const u1 = await step('08-undo1', { toasts: await L.toasts(p) });
  await p.keyboard.press('Control+z'); await p.waitForTimeout(1500); const u2 = await step('09-undo2', { toasts: await L.toasts(p) });
  await p.keyboard.press('Control+y'); await p.waitForTimeout(1500); const y1 = await step('10-redo1');
  await p.keyboard.press('Control+y'); await p.waitForTimeout(1500); const y2 = await step('11-redo2');
  r.history = { undo1EqualsKeyboardL: u1 === dK, undo2EqualsPlaceholder: u2 === dA, redo1EqualsKeyboardL: y1 === dK, redo2EqualsMouse: y2 === dB };
  // Esc 階梯：外環 E → 點兩點 → 鍵入 12 → Esc ×3
  await p.click('[data-face-tool="redraw"]'); await p.waitForTimeout(600); await L.lesson(p);
  for (const [x, y] of [[0, 0], [2000, 0]]) { const t = await L.pt(p, x, y); await p.mouse.click(t.x, t.y); await p.waitForTimeout(300); }
  await p.keyboard.type('12'); await p.waitForTimeout(300);
  const hint = async () => ({ notice: (await p.textContent('#faceDraftNotice').catch(() => '')).replace(/\s+/g, ' ').slice(0, 160), inFace: await p.isVisible('#workspaceBackButton'), tool: (await p.textContent('.statusbar, footer').catch(() => '')).replace(/\s+/g, ' ').slice(0, 80) });
  r.esc = [{ before: await hint() }]; await shot('12-esc0-typed-12');
  for (let i = 1; i <= 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); r.esc.push({ ['after' + i]: await hint() }); await shot('13-esc' + i); }
  r.escSceneUnchanged = (await L.dump(p)) === dB;
  // 物件畫布上的卡片
  r.cardVisible = await p.isVisible('.ocard[data-kind="boundary"][data-id="1"]');
  r.saved = await L.saveProject(p, `${L.out()}/d02.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start()); shot = L.shotter(p, 'D02');
  await L.newProject(p); await L.openProject(p, `${L.out()}/d02.gcanvas`);
  const dR = await L.dump(p);
  r.reopenOutline = outline(dR); r.reopenEqual = dR.split(/\r?\n/).filter(l => /^boundary /.test(l)).join('\n') === dB.split(/\r?\n/).filter(l => /^boundary /.test(l)).join('\n');
  await shot('14-reopened');
  await L.enterFace1(p); await shot('15-reopened-face');
  r.errsB = errs;
  L.write('walk_d02.result.json', r);
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); process.exit(1); });
