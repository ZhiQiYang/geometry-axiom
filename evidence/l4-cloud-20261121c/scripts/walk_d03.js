// D03 面內工作區改形狀（GEO-188、190、192、193）：只用滑鼠與鍵盤。
// 新專案 → 工具列「多邊形 P」建預設 4000×3000 面 → 選取 V →「形狀 ▾ → 凹口」點上邊 → 置中、寬 1000、深 500（預覽）→「取消 Esc」
// → 再一次 →「套用 Enter」→ 右鍵點右下角 →「切角」600×600 → 套用 →「形狀 ▾ → 推拉」點右邊 → 往外 500 → Enter
// → Ctrl+Z ×3／Ctrl+Y ×3 → 右欄外環邊長度欄改一條邊 → 另存 → 全新瀏覽器開檔。
const L = require('./lib.js');
const r = { steps: [] };
const outline = t => (t.match(/^boundary 1 outline .*$/m) || [null])[0];
(async () => {
  let { b, p, errs } = await L.start();
  let shot = L.shotter(p, 'D03');
  const step = async (name, extra = {}) => { const d = await L.dump(p); r.steps.push({ name, outline: outline(d), dumpLen: d.length, ...extra }); await shot(name); return d; };
  const setParam = async (sel, v) => { await p.click(sel, { clickCount: 3 }); await p.keyboard.type(String(v)); await p.waitForTimeout(250); };
  const panelText = () => p.textContent('#feOpPanel').then(s => s.replace(/\s+/g, ' ').slice(0, 200)).catch(() => null);
  await L.newProject(p); await p.click('#btnNewPoly'); await p.waitForTimeout(1500); await L.lesson(p);
  await p.click('[data-face-tool="select"]'); await p.waitForTimeout(500); await L.lesson(p);
  const d0 = await step('01-face-4000x3000');
  // 凹口：預覽 → 取消
  const notch = async () => { await p.click('#shapeToolButton'); await p.waitForTimeout(300); await p.click('[data-shape-action="notch"]'); await p.waitForTimeout(300);
    const t = await L.pt(p, 2000, 0); await p.mouse.click(t.x, t.y); await p.waitForTimeout(800);
    await p.locator('#feOpPanel [data-fe-anchor]', { hasText: '置中' }).first().click(); await p.waitForTimeout(200);
    await setParam('#feOpPanel [data-fe-param="w"]', 1000); await setParam('#feOpPanel [data-fe-param="d"]', 500); };
  await notch();
  r.notchPanel = await panelText(); r.ghost = await p.$$eval('[data-fe-ghost]', es => es.length);
  const dPrev = await step('02-notch-preview'); r.notchPreviewZeroWrite = dPrev === d0;
  await p.click('#feOpCancel'); await p.waitForTimeout(600);
  const dCancel = await step('03-notch-cancel'); r.notchCancelZeroWrite = dCancel === d0; r.ghostAfterCancel = await p.$$eval('[data-fe-ghost]', es => es.length);
  await notch(); await p.click('#feOpApply'); await p.waitForTimeout(1800);
  const dN = await step('04-notch-applied', { toasts: await L.toasts(p) });
  // 右鍵切角
  let t = await L.pt(p, 4000, 3000); await p.mouse.click(t.x, t.y, { button: 'right' }); await p.waitForTimeout(700);
  r.ctxMenu = await p.$$eval('#feCtxMenu [data-fe-act]', es => es.filter(e => e.offsetParent).map(e => e.dataset.feAct + ':' + e.textContent.trim().replace(/\s+/g, ' ').slice(0, 20)));
  await shot('05-ctx-menu-corner');
  await p.click('#feCtxMenu [data-fe-act="op:corner"]'); await p.waitForTimeout(600);
  r.cornerPanel = await panelText();
  await setParam('#feOpPanel [data-fe-param="w"]', 600); await setParam('#feOpPanel [data-fe-param="d"]', 600);
  await p.keyboard.press('Enter'); await p.waitForTimeout(1800);
  const dC = await step('06-corner-applied');
  // 推拉右邊往外 500
  await p.click('#shapeToolButton'); await p.waitForTimeout(300); await p.click('[data-shape-action="push"]'); await p.waitForTimeout(300);
  t = await L.pt(p, 4000, 1000); await p.mouse.click(t.x, t.y); await p.waitForTimeout(800);
  r.pushPanel = await panelText();
  await p.locator('#feOpPanel [data-fe-dir]', { hasText: '往外' }).first().click(); await p.waitForTimeout(200);
  await setParam('#feOpPanel [data-fe-param="dist"]', 500);
  await shot('07-push-preview');
  await p.keyboard.press('Enter'); await p.waitForTimeout(1800);
  const dP = await step('08-push-applied');
  // 復原／重做
  const seq = [];
  for (const k of ['Control+z', 'Control+z', 'Control+z', 'Control+y', 'Control+y', 'Control+y']) { await p.keyboard.press(k); await p.waitForTimeout(1300); seq.push(await L.dump(p)); }
  await shot('09-after-undo-redo');
  r.history = { u1EqNotchCorner: seq[0] === dC, u2EqNotch: seq[1] === dN, u3EqRect: seq[2] === d0, y1EqNotch: seq[3] === dN, y2EqCorner: seq[4] === dC, y3EqPush: seq[5] === dP };
  r.saved = await L.saveProject(p, `${L.out()}/d03.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start()); shot = L.shotter(p, 'D03');
  await L.newProject(p); await L.openProject(p, `${L.out()}/d03.gcanvas`); await p.waitForTimeout(2500);
  const dR = await L.dump(p); r.reopenOutline = outline(dR); r.reopenEqual = outline(dR) === outline(dP);
  await L.enterFace1(p); await shot('10-reopened-face');
  r.errsB = errs;
  L.write('walk_d03.result.json', r); console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); L.write('walk_d03.partial.json', r); process.exit(1); });
