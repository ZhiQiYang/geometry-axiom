// D09（#443 D09 修正：工程規格表單顯示既有本面覆寫）：所有輸入走 CDP Input。
// 檔案 → 新專案 → 檔案 → 範例 ▸ →「試用工程規格現成專案…」→「本面覆寫與恢復沿用」縫寬：改成本面數值 4
// → 預覽套用 → 勾核對 → 確認套用 → 關閉 → 檔案 →「工程規格 · 面材與角材」再開：縫寬欄應顯示「改成本面數值」4（21c-4 原本顯示「沿用來源」）
// → 不改直接預覽：0 項變更、零寫入 → 返回修改 → 關閉 → 復原（表單應回「沿用來源」）→ 重做（回 4）
// → 另存 → 新瀏覽器（390×844）新專案 → 開啟專案 → 再開工程規格：仍顯示 4。
const L = require('./lib.js');
const r = { checks: [] };
const ok = L.checker(r);
const F = '#ewField-application-targets-1-overrides-gap-';
const DISC = '#ewContent details:has(> .ew-override ' + F + 'mode)';
const waitFor = async (S, expr, ms = 20000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await S.p.evaluate(expr).catch(() => false)) return true; await L.sleep(150); } return false; };
const idle = S => waitFor(S, "connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy");
const ready = S => waitFor(S, "$('ewWorkspace')?.open&&!$('ewPreview').disabled&&!$('ewContent').inert&&$('ewStatus').textContent.startsWith('已讀取目前工程。')");
const reveal = async S => { if (!(await S.p.evaluate(d => document.querySelector(d)?.open, DISC))) await L.click(S, DISC + ' > summary', { wait: 400 }); };
const form = S => S.p.evaluate(f => { const m = document.querySelector(f + 'mode'), v = document.querySelector(f + 'value'), sm = document.querySelector(f + 'mode')?.closest('.ew-override')?.querySelector('small'); return { mode: m?.value ?? null, modeText: m ? m.options[m.selectedIndex]?.textContent : null, value: v?.value ?? null, note: sm?.textContent ?? null }; }, F);
const openSpecs = async S => { await L.fileMenu(S, '#btnEngineeringSpecs'); await ready(S); await reveal(S); };
const close = async S => { await L.click(S, '#ewClose', { wait: 800 }); await idle(S); };
const appOverrides = d => { const m = d.match(/^engineering application (.*)$/m); try { return m ? JSON.parse(Buffer.from(m[1], 'base64').toString('utf8')).overrides : null; } catch (_) { return 'undecodable'; } };
(async () => {
  let S = await L.start();
  r.browser = S.version; r.runtime = await S.p.evaluate(async () => (await fetch('/runtime')).json());
  await L.newProject(S);
  await L.click(S, '#fileMenuBtn', { wait: 250 }); await L.click(S, '#exampleMenuBtn', { wait: 300 });
  S.p._accept = true; await L.click(S, '#btnEngineeringExample', { wait: 1500 }); S.p._accept = false;
  ok('D09_EXAMPLE_WORKSPACE_READY', await ready(S));
  await reveal(S);
  const f0 = await form(S); r.formInitial = f0;
  ok('D09_INITIAL_INHERIT', f0.mode === 'inherit', f0);
  const c0 = await L.checkpoint(S);
  await L.pick(S, F + 'mode', 'literal'); await L.sleep(300);
  await L.fill(S, F + 'value', '4');
  r.shotEdited = await L.shot(S, 'D09-1-edited-4');
  await L.click(S, '#ewPreview', { wait: 300 }); await waitFor(S, "!$('ewReview').hidden&&!!$('ewReviewed')");
  r.review1 = (await L.text(S, '#ewReview') || '').slice(0, 600);
  ok('D09_PREVIEW_ZERO_WRITE', L.same(c0, await L.checkpoint(S)));
  await L.check(S, '#ewReviewed', true);
  await L.click(S, '#ewConfirm', { wait: 1500 }); await idle(S);
  const c1 = await L.checkpoint(S); r.afterConfirm = L.strip(c1); r.overridesAfterConfirm = appOverrides(c1.scene);
  ok('D09_CONFIRM_ONE_HISTORY', c1.undo === c0.undo + 1 && c1.sceneSha !== c0.sceneSha, { undo: [c0.undo, c1.undo], overrides: r.overridesAfterConfirm });
  // 修正重點：確認後表單（同一開啟、以及關閉重開）顯示目前本面值
  await reveal(S);
  const fA = await form(S); r.formAfterConfirmSameOpen = fA;
  ok('D09_SAME_OPEN_SHOWS_4', fA.mode === 'literal' && fA.value === '4', fA);
  await close(S);
  await openSpecs(S);
  const f1 = await form(S); r.formReopened = f1; r.shotReopened = await L.shot(S, 'D09-2-reopened-shows-4');
  ok('D09_REOPEN_SHOWS_LITERAL_4', f1.mode === 'literal' && f1.value === '4', f1);
  // 不改再預覽：0 項變更、零寫入
  const c2 = await L.checkpoint(S);
  await L.click(S, '#ewPreview', { wait: 300 }); await waitFor(S, "!$('ewReview').hidden&&!!$('ewReviewed')");
  r.review2 = (await L.text(S, '#ewReview') || '').slice(0, 600);
  ok('D09_UNEDITED_PREVIEW_ZERO_CHANGE', L.same(c2, await L.checkpoint(S)) && /0\s*項/.test(r.review2), { review: r.review2.slice(0, 200) });
  r.shotUnedited = await L.shot(S, 'D09-3-unedited-preview');
  await L.click(S, '#ewCancelPreview', { wait: 800 });
  ok('D09_CANCEL_ZERO_WRITE', L.same(c2, await L.checkpoint(S)));
  await close(S);
  // 復原：表單回沿用來源；重做：回 4
  await L.click(S, '#btnUndo', { wait: 2000 }); await idle(S);
  const cU = await L.checkpoint(S);
  ok('D09_UNDO_RESTORES_SCENE', cU.sceneSha === c0.sceneSha, { undo: cU.undo, redo: cU.redo });
  await openSpecs(S); const fU = await form(S); r.formAfterUndo = fU;
  ok('D09_UNDO_FORM_INHERIT', fU.mode === 'inherit', fU);
  await close(S);
  await L.click(S, '#btnRedo', { wait: 2000 }); await idle(S);
  const cR = await L.checkpoint(S);
  ok('D09_REDO_RESTORES_SCENE', cR.sceneSha === c1.sceneSha);
  await openSpecs(S); const fR = await form(S); r.formAfterRedo = fR;
  ok('D09_REDO_FORM_SHOWS_4', fR.mode === 'literal' && fR.value === '4', fR);
  await close(S);
  r.saved = await L.saveProject(S, L.out() + '/d09.gcanvas');
  r.errorsA = S.errs; await S.b.close();
  // 冷開：新瀏覽器、390×844
  S = await L.start({ viewport: { width: 390, height: 844 } });
  await L.newProject(S); await L.openProject(S, L.out() + '/d09.gcanvas'); await idle(S); await L.sleep(1500);
  const cC = await L.checkpoint(S);
  ok('D09_COLD_SCENE_EQUAL', cC.scene === c1.scene, { cold: cC.sceneSha, saved: c1.sceneSha });
  await openSpecs(S); const fC = await form(S); r.formCold390 = fC;
  r.shotCold = await L.shot(S, 'D09-4-cold-390-shows-4');
  const vis = await L.rect(S, F + 'value'); r.cold390ValueRect = vis;
  ok('D09_COLD_390_SHOWS_4', fC.mode === 'literal' && fC.value === '4' && !!vis && vis.right <= vis.vw, fC);
  r.errorsB = S.errs; await S.b.close();
  r.pass = r.checks.every(c => c.pass); r.passed = r.checks.filter(c => c.pass).length + '/' + r.checks.length;
  L.write('walk_d09.result.json', r); console.log('D09', r.passed);
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); r.fatal = String(e.stack).slice(0, 800); L.write('walk_d09.result.json', r); process.exit(1); });
