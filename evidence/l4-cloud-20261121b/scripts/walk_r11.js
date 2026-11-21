// R11 空間平面圖與三視圖右鍵選單（#396，經 #426／#427 進 main）：只用 UI 走。
// 場景由「檔案 → 開啟場景檔…」載入 r11.scene（使用者可走的一般入口）；之後所有變更都經滑鼠右鍵、點擊與鍵盤。
// page.evaluate 只讀：dump、objects、history 長度、選單文字、把平面 mm／原生視圖座標換成螢幕座標（getScreenCTM）。
const L = require('./lib21.js');
const path = require('path');
const OUT = process.env.OUT; const shot = L.shooter(OUT);
const SCENE = path.resolve(__dirname, 'r11.scene');
const r = { steps: [] };
const step = (name, data) => { r.steps.push({ name, ...data }); console.log(name, JSON.stringify(data).slice(0, 300)); };
const gotIt = async p => { const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(() => false)) await k.first().click().catch(() => {}); };
const line = (scene, kind, id) => scene.split(/\r?\n/).find(l => l.startsWith(kind + ' ' + id + ' ')) || null;
const menuOf = (p, id, attr) => p.evaluate(([id, attr]) => { const m = document.getElementById(id); if (!m || m.hidden) return null;
  return { title: (m.querySelector('[role=heading], .fcm-title, header')?.textContent || '').trim(), items: [...m.querySelectorAll('[' + attr + ']')].filter(e => !e.closest('.fcm-submenu')).map(e => e.getAttribute(attr) + ':' + e.textContent.trim().replace(/\s+/g, ' ') + (e.getAttribute('aria-disabled') === 'true' ? ' [停用]' : '')),
    sub: [...m.querySelectorAll('.fcm-submenu [' + attr + ']')].map(e => e.getAttribute(attr) + ':' + e.textContent.trim().replace(/\s+/g, ' ')), text: m.textContent.replace(/\s+/g, ' ').slice(0, 300) }; }, [id, attr]);
const planPt = (p, x, y) => p.evaluate(([x, y]) => { const q = new DOMPoint(x, y).matrixTransform(document.getElementById('spacePlanSvg').getScreenCTM()); return { x: q.x, y: q.y }; }, [x, y]);
const viewPt = (p, viewId, x, y, scope) => p.evaluate(([viewId, x, y, scope]) => { const st = WorkspaceView.state(scope === 'project' ? { kind: 'project' } : { kind: 'space', id: 9 });
  const f = st.snapshot?.layout?.views.find(v => v.viewId === viewId), root = document.getElementById(scope === 'project' ? 'world' : 'spaceProjSvg'), m = root?.getScreenCTM(); if (!f || !m) return null;
  const q = new DOMPoint(x + f.tx, y + f.ty).matrixTransform(m); return { x: q.x, y: q.y }; }, [viewId, x, y, scope]);
const rightAt = async (p, pt) => { await p.mouse.move(pt.x, pt.y); await p.mouse.click(pt.x, pt.y, { button: 'right' }); await p.waitForTimeout(700); };
const sp = a => `#spaceCtxMenu [data-sp-act="${a}"]`, v3 = a => `#viewCtxMenu [data-v3-act="${a}"]`;
const state = async p => ({ dump: await L.dump(p), hist: await L.hist(p) });
const same = (a, b) => a.dump === b.dump && JSON.stringify(a.hist) === JSON.stringify(b.hist);
async function enterSpace(p) {
  await p.click('#btnZoom').catch(() => {}); await p.waitForTimeout(500);
  await gotIt(p);
  const card = await p.locator('.ocard[data-kind="space"][data-id="9"]').boundingBox();   // 卡片寫「雙擊進入」
  await p.mouse.dblclick(card.x + card.width / 2, card.y + 20); await p.waitForTimeout(2000); await gotIt(p);
  if (!(await p.locator('#spacePlanSvg').isVisible().catch(() => false))) { await p.click('[data-ss-tab="plan"]'); await p.waitForTimeout(1200); }
}
(async () => {
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  p._accept = true; await L.openScene(p, SCENE); await p.waitForTimeout(3000); p._accept = false; await gotIt(p);
  const s0 = await state(p); step('scene-loaded', { columns: [line(s0.dump, 'column', 71), line(s0.dump, 'column', 83)], beam: line(s0.dump, 'beam', 91), hist: s0.hist });
  await shot(p, 'R11-01-scene-loaded');
  await enterSpace(p); await shot(p, 'R11-02-space-plan');

  // ---- A1 柱右鍵、空白右鍵：只開選單，零寫入
  let base = await state(p);
  await rightAt(p, await planPt(p, 650, 700)); step('plan-column-menu', { menu: await menuOf(p, 'spaceCtxMenu', 'data-sp-act') }); await shot(p, 'R11-03-plan-column-menu');
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  await rightAt(p, await planPt(p, 3500, 800)); step('plan-blank-menu', { menu: await menuOf(p, 'spaceCtxMenu', 'data-sp-act') }); await shot(p, 'R11-04-plan-blank-menu');
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  step('menus-zero-write', { unchanged: same(base, await state(p)) });

  // ---- A2 改柱尺寸：取消 → 零寫入；確認 → 一筆歷史；復原／重做
  await rightAt(p, await planPt(p, 650, 700)); await p.click(sp('size')); await p.waitForTimeout(800);
  const orig = { w: await p.inputValue('#rcW'), d: await p.inputValue('#rcD') };
  await p.fill('#rcW', '340'); await p.fill('#rcD', '420'); await shot(p, 'R11-05-size-form');
  await p.click('#rcCancel'); await p.waitForTimeout(800);
  step('size-cancel', { formOriginal: orig, unchanged: same(base, await state(p)), formHidden: await p.locator('#rcDialog').isHidden() });
  await rightAt(p, await planPt(p, 650, 700)); await p.click(sp('size')); await p.waitForTimeout(800);
  await p.fill('#rcW', '340'); await p.fill('#rcD', '420'); await p.click('#rcSubmit'); await p.waitForTimeout(1800);
  const sSize = await state(p);
  step('size-confirm', { before: line(base.dump, 'column', 71), after: line(sSize.dump, 'column', 71), onlyColumn71Changed: sSize.dump.split(/\r?\n/).filter((l, i, a) => !base.dump.split(/\r?\n/).includes(l)).length === 1,
    histBefore: base.hist, histAfter: sSize.hist, oneStep: sSize.hist.undo === base.hist.undo + 1 && sSize.hist.redo === 0 });
  await shot(p, 'R11-06-size-confirmed');
  await p.click('#faceUndoButton'); await p.waitForTimeout(1500); step('size-undo', { backToBefore: (await L.dump(p)) === base.dump }); await shot(p, 'R11-07-size-undo');
  await p.click('#faceRedoButton'); await p.waitForTimeout(1500); step('size-redo', { backToConfirmed: (await L.dump(p)) === sSize.dump });

  // ---- A3 重複柱：Escape 取消零寫入；點新位置 → 表單 → 確認 → 一筆歷史 → 復原 → 重做
  base = await state(p);
  await rightAt(p, await planPt(p, 650, 700)); await p.click(sp('duplicate')); await p.waitForTimeout(500);
  await p.keyboard.press('Escape'); await p.waitForTimeout(500); step('duplicate-escape', { unchanged: same(base, await state(p)) });
  await rightAt(p, await planPt(p, 650, 700)); await p.click(sp('duplicate')); await p.waitForTimeout(500);
  const np = await planPt(p, 1000, 2000); await p.mouse.click(np.x, np.y); await p.waitForTimeout(900);
  const dupForm = await p.evaluate(() => ['rcX', 'rcY', 'rcW', 'rcD', 'rcZ0', 'rcZ1', 'rcSpace'].map(id => id + '=' + document.getElementById(id)?.value).join(' '));
  step('duplicate-form', { form: dupForm, unchangedBeforeSubmit: same(base, await state(p)) }); await shot(p, 'R11-08-duplicate-form');
  await p.click('#rcSubmit'); await p.waitForTimeout(1800);
  const sDup = await state(p), cols = (await L.objects(p)).columns.map(c => ({ id: c.id, box: c.box, space: c.space }));
  step('duplicate-confirm', { columns: cols, oneStep: sDup.hist.undo === base.hist.undo + 1, original71Same: line(sDup.dump, 'column', 71) === line(base.dump, 'column', 71) }); await shot(p, 'R11-09-duplicated');
  await p.click('#faceUndoButton'); await p.waitForTimeout(1500); step('duplicate-undo', { backToBefore: (await L.dump(p)) === base.dump });
  await p.click('#faceRedoButton'); await p.waitForTimeout(1500); step('duplicate-redo', { backToConfirmed: (await L.dump(p)) === sDup.dump });

  // ---- A4 樑右鍵刪除 → 一筆歷史 → 復原 → 重做
  base = await state(p);
  await rightAt(p, await planPt(p, 2000, 1500)); step('beam-menu', { menu: await menuOf(p, 'spaceCtxMenu', 'data-sp-act') }); await shot(p, 'R11-10-beam-menu');
  await p.click(sp('delete')); await p.waitForTimeout(1800); step('beam-delete-dialogs', { dialogs: await L.dialogs(p) });
  const sDel = await state(p);
  step('beam-delete', { beamGone: !line(sDel.dump, 'beam', 91), columnsKept: !!line(sDel.dump, 'column', 71) && !!line(sDel.dump, 'column', 83), oneStep: sDel.hist.undo === base.hist.undo + 1 }); await shot(p, 'R11-11-beam-deleted');
  await p.click('#faceUndoButton'); await p.waitForTimeout(1500); step('beam-delete-undo', { backToBefore: (await L.dump(p)) === base.dump });
  await p.click('#faceRedoButton'); await p.waitForTimeout(1500); step('beam-delete-redo', { backToDeleted: (await L.dump(p)) === sDel.dump });

  // ---- A5 空白處右鍵「放柱」→ 表單 → 取消零寫入
  base = await state(p);
  await rightAt(p, await planPt(p, 3500, 800)); await p.click(sp('column')); await p.waitForTimeout(800);
  step('create-column-form', { form: await p.evaluate(() => ['rcX', 'rcY', 'rcSpace'].map(id => id + '=' + document.getElementById(id)?.value).join(' ')) }); await shot(p, 'R11-12-create-column-form');
  await p.click('#rcCancel'); await p.waitForTimeout(600); step('create-column-cancel', { unchanged: same(base, await state(p)) });

  // ---- A6 另存 → 新頁面冷開 → 再右鍵核對
  const finalPlan = await L.dump(p);
  r.saved = await L.saveProject(p, `${OUT}/r11.gcanvas`); await p.waitForTimeout(1500);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.openProject(p, `${OUT}/r11.gcanvas`); await gotIt(p);
  const reopened = await L.dump(p);
  step('cold-reopen', { dumpSame: reopened === finalPlan, column71: line(reopened, 'column', 71), beam91: line(reopened, 'beam', 91) });

  // ---- B 三視圖（全域）：空白右鍵、對齊視角、柱屬性（唯讀）、隱藏／顯示、面「開啟」
  base = await state(p);
  await p.click('#btnObj'); await p.waitForTimeout(2500); await gotIt(p); await shot(p, 'R11-13-three-view');
  const blank = await p.evaluate(() => { const r = document.getElementById('cv').getBoundingClientRect(); return { x: r.right - 18, y: r.bottom - 18 }; });
  await rightAt(p, blank); step('view-blank-menu', { menu: await menuOf(p, 'viewCtxMenu', 'data-v3-act') }); await shot(p, 'R11-14-view-blank-menu');
  await p.click(v3('align')); await p.waitForTimeout(400); step('view-align-submenu', { menu: await menuOf(p, 'viewCtxMenu', 'data-v3-act') }); await shot(p, 'R11-15-align-submenu');
  await p.click(v3('top')); await p.waitForTimeout(2000);
  step('view-top', { views: await p.evaluate(() => WorkspaceView.state({ kind: 'project' }).snapshot?.layout?.views.map(v => ({ id: v.viewId, right: v.right, down: v.down }))) }); await shot(p, 'R11-16-top-view');
  await rightAt(p, await viewPt(p, 'top', 650, -700, 'project'));
  step('view-top-column-menu', { menu: await menuOf(p, 'viewCtxMenu', 'data-v3-act'), target: await p.evaluate(() => WorkspaceView.state({ kind: 'project' }).lastTarget) }); await shot(p, 'R11-17-top-column-menu');
  await p.click(v3('props')); await p.waitForTimeout(800);
  step('view-column-props', { props: await p.evaluate(() => { const w = document.getElementById('workspaceProperties'); return w ? { hidden: w.hidden, readonly: w.dataset.readonly, kind: w.dataset.propertiesKind, id: w.dataset.propertiesId, inputs: w.querySelectorAll('input,select,textarea').length, text: w.textContent.replace(/\s+/g, ' ').slice(0, 300) } : null; }) });
  await shot(p, 'R11-18-column-props');
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  await rightAt(p, await viewPt(p, 'top', 650, -700, 'project')); await p.click(v3('hide')); await p.waitForTimeout(1200);
  step('view-hide-column', { ops71: await p.evaluate(() => WorkspaceView.state({ kind: 'project' }).snapshot?.ops.filter(o => o.owner?.kind === 'column' && o.owner.id === 71).length) }); await shot(p, 'R11-19-column-hidden');
  await rightAt(p, blank); step('view-blank-after-hide', { menu: await menuOf(p, 'viewCtxMenu', 'data-v3-act') });
  await p.click(v3('show-all')); await p.waitForTimeout(400);
  const sub = await menuOf(p, 'viewCtxMenu', 'data-v3-act'); if (sub && sub.sub.length) { step('restore-submenu', { menu: sub }); await shot(p, 'R11-19b-restore-submenu'); await p.locator('#viewCtxMenu .fcm-submenu [data-v3-act]').first().click(); }
  await p.waitForTimeout(1500);
  step('view-restore-column', { ops71: await p.evaluate(() => WorkspaceView.state({ kind: 'project' }).snapshot?.ops.filter(o => o.owner?.kind === 'column' && o.owner.id === 71).length) }); await shot(p, 'R11-20-column-restored');
  await p.keyboard.press('Escape');
  await rightAt(p, blank); await p.click(v3('align')); await p.waitForTimeout(300); await p.click(v3('front')); await p.waitForTimeout(2000);
  step('view-zero-write-so-far', { unchanged: same(base, await state(p)) });
  await rightAt(p, await viewPt(p, 'front', 3500, -2600, 'project'));
  step('view-front-face-menu', { menu: await menuOf(p, 'viewCtxMenu', 'data-v3-act'), target: await p.evaluate(() => WorkspaceView.state({ kind: 'project' }).lastTarget) }); await shot(p, 'R11-21-front-face-menu');
  await p.click(v3('open')); await p.waitForTimeout(2000); await gotIt(p);
  step('view-open-face', { focus: await p.evaluate(() => ({ t: oc.focus?.t, id: oc.focus?.id, bid: oc.edit?.bid, workspaceVisible: !document.getElementById('objectWorkspace').hidden })), unchanged: same(base, await state(p)) });
  await shot(p, 'R11-22-face-opened');

  // ---- C 空間投影分頁也用同一個右鍵選單（冷開後的頁面）
  r.errsB = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.openProject(p, `${OUT}/r11.gcanvas`); await gotIt(p);
  base = await state(p);
  await enterSpace(p); await p.click('[data-ss-tab="proj"]'); await p.waitForTimeout(2500);
  await rightAt(p, await viewPt(p, 'front', 3500, -2600, 'space'));
  step('space-projection-menu', { menu: await menuOf(p, 'viewCtxMenu', 'data-v3-act'), target: await p.evaluate(() => WorkspaceView.state({ kind: 'space', id: 9 }).lastTarget) });
  await shot(p, 'R11-23-space-projection-menu'); await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  step('space-projection-zero-write', { unchanged: same(base, await state(p)) });
  r.errsC = errs.slice(); await b.close();
  r.dumps = { finalPlan };
  L.writeResult(`${OUT}/walk_r11.result.json`, r);
})().catch(e => { r.fatal = String(e.stack || e); L.writeResult(`${OUT}/walk_r11.result.json`, r); console.error(e); process.exit(1); });
