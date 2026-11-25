// R17（#443 R17 修正：App 顯示 D16a／P1-A 的中文診斷）：所有輸入走 CDP Input。
// 檔案 → 新專案 → 檔案 → 開啟場景檔（r17-rect.scene，1000×1000 矩形面，沿用 21a）→ 點面卡 → 進入面內
// → 構件 → 角材 → 放置方式「兩支互頂壁邊材」→ 第 1 支 e0、第 2 支 e2（A 27、B 20、+u、+n）→ 預覽
// → 影響視窗：條文 D16a、預期改顯示中文「兩個真實端面須法向相反、位於同一平面，且有正長度接觸。」、確認停用 → 取消 → 零寫入。
// 另於 390×844 重走同一路徑，看中文預期是否完整顯示。
const path = require('path');
const L = require('./lib.js');
const r = { checks: [], sizes: {} };
const ok = L.checker(r);
const RECT = path.join(__dirname, 'r17-rect.scene');
const ZH = '兩個真實端面須法向相反、位於同一平面，且有正長度接觸。';
const EN = 'two real end faces with opposite normals, one plane and positive contact';
const dlg = S => S.p.evaluate(() => { const d = document.querySelector('.reference-impact[open]'); if (!d) return null; const c = d.querySelector('#impact-confirm');
  return { text: d.innerText, violations: [...d.querySelectorAll('.impact-violation')].map(v => v.textContent), confirmDisabled: c ? c.disabled : null, confirmPresent: !!c }; });
(async () => {
  for (const [w, h] of [[1400, 900], [390, 844]]) {
    const k = String(w), s = r.sizes[k] = {};
    const S = await L.start({ viewport: { width: w, height: h } }); s.browser = S.version;
    await L.newProject(S); await L.openProject(S, RECT, '#btnOpen'); await L.lesson(S);
    if (w === 390 && !(await L.visible(S, '.ocard[data-kind="boundary"][data-id="1"]'))) s.note = 'card not visible at 390';
    await L.click(S, '.ocard[data-kind="boundary"][data-id="1"]', { wait: 300 });
    await L.click(S, '.ocard[data-kind="boundary"][data-id="1"] .card-enter', { wait: 1500 }); await L.lesson(S);
    if (!(await L.visible(S, '#faceInspectorTabs [data-fi-tab="components"]')) && (await L.visible(S, '#workspaceToggleRight'))) { s.openedInspector = true; await L.click(S, '#workspaceToggleRight', { wait: 600 }); }
    await L.click(S, '#faceInspectorTabs [data-fi-tab="components"]', { wait: 500 });
    await L.click(S, '#faceComponentSwitch [data-component-tab="timber"]', { wait: 500 }); await L.lesson(S);
    await L.pick(S, '#tbPlacementMode', 'boundary-pair'); await L.sleep(400); await L.lesson(S);
    for (const [n, a] of [[1, 'e0'], [2, 'e2']]) {
      await L.pick(S, `#tbPair${n}Anchor`, a); await L.fill(S, `#tbPair${n}A`, '27'); await L.fill(S, `#tbPair${n}B`, '20');
      await L.pick(S, `#tbPair${n}Dir`, '+u'); await L.pick(S, `#tbPair${n}Side`, '+n');
    }
    const c0 = await L.checkpoint(S);
    await L.click(S, '#tbPairPreview', { wait: 300 });
    for (let i = 0; i < 40 && !(await dlg(S)); i++) await L.sleep(250);
    await L.sleep(400);
    const d = await dlg(S); s.dialog = d;
    s.shot = await L.shot(S, `R17-${k}-1-p1a-dialog`);
    const v = (d?.violations || []).find(t => /D16a/.test(t)) || null; s.d16a = v;
    ok(k + '_D16A_DIALOG', !!d && !!v, { violations: d?.violations });
    ok(k + '_EXPECTED_ZH', !!v && v.includes('預期：' + ZH) && !v.includes(EN), { line: v });
    ok(k + '_CONFIRM_DISABLED', !!d && (d.confirmDisabled === true || d.confirmPresent === false), { confirmDisabled: d?.confirmDisabled, present: d?.confirmPresent });
    // 中文預期在視窗內完整可見（未被裁掉）
    const vr = await S.p.evaluate(() => { const n = [...document.querySelectorAll('.reference-impact[open] .impact-violation')].find(e => /D16a/.test(e.textContent)); if (!n) return null; const b = n.getBoundingClientRect(); return { left: b.left, right: b.right, top: b.top, bottom: b.bottom, sw: n.scrollWidth, cw: n.clientWidth }; });
    s.violationRect = vr;
    ok(k + '_EXPECTED_NOT_CLIPPED', !!vr && vr.left >= 0 && vr.right <= w && vr.sw <= vr.cw + 1, vr);
    await L.click(S, '.reference-impact[open] .impact-actions button:not(#impact-confirm)', { wait: 900 });
    const c1 = await L.checkpoint(S);
    ok(k + '_PREVIEW_CANCEL_ZERO_WRITE', L.same(c0, c1) && !/^timber /m.test(c1.scene), { before: L.strip(c0), after: L.strip(c1) });
    s.status = await L.text(S, '#tbPairStatus');
    s.errors = S.errs; await S.b.close();
  }
  r.pass = r.checks.every(c => c.pass); r.passed = r.checks.filter(c => c.pass).length + '/' + r.checks.length;
  L.write('walk_r17.result.json', r); console.log('R17', r.passed);
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); r.fatal = String(e.stack).slice(0, 800); L.write('walk_r17.result.json', r); process.exit(1); });
