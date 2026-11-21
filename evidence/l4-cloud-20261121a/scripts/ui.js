// 只用滑鼠與鍵盤的輸入輔助，以及唯讀的檢查點。
const crypto = require('crypto');
const sha = s => crypto.createHash('sha256').update(String(s)).digest('hex');
exports.sha = sha;

// 下拉選單：滑鼠點一下取得焦點（Escape 收起原生清單），再用方向鍵移到目標值。
exports.pick = async (p, sel, value) => {
  await p.click(sel); await p.keyboard.press('Escape'); await p.waitForTimeout(80);
  for (let guard = 0; guard < 40; guard++) {
    const st = await p.$eval(sel, (s, v) => ({ cur: s.selectedIndex, want: [...s.options].findIndex(o => o.value === v) }), value);
    if (st.want < 0) throw new Error('no option ' + value + ' in ' + sel);
    if (st.cur === st.want) break;
    await p.keyboard.press(st.cur < st.want ? 'ArrowDown' : 'ArrowUp'); await p.waitForTimeout(60);
  }
  const got = await p.$eval(sel, s => s.value);
  if (got !== value) throw new Error(`pick ${sel}: ${got} != ${value}`);
  await p.waitForTimeout(200);
};
// 數字或文字欄：三擊選取原內容，鍵盤輸入新值，Tab 離開。
exports.type = async (p, sel, value) => {
  await p.click(sel, { clickCount: 3 }); await p.keyboard.press('Control+A');
  await p.keyboard.type(String(value)); await p.keyboard.press('Tab'); await p.waitForTimeout(150);
};
exports.click = async (p, sel, wait = 600) => { await p.click(sel); await p.waitForTimeout(wait); };
exports.check = async (p, sel, on = true) => { const cur = await p.$eval(sel, n => n.checked); if (cur !== on) await p.click(sel); await p.waitForTimeout(200); };

// 唯讀檢查點：場景 dump、修訂號、歷史深度與末筆身分、專案 dirty、身分帳
exports.checkpoint = async (p, L) => {
  const scene = await L.snap(p);
  const eng = await L.q(p, 'engineering-read').catch(e => ({ error: String(e) }));
  const ident = await L.q(p, 'identity-read').catch(e => ({ error: String(e) }));
  const h = await p.evaluate(() => { const h = ReferenceWorkspace.history; const ps = ReferenceWorkspace.getProjectState?.() || {}; return { undo: h.undo.length, redo: h.redo.length, frame: h.frame ?? null, lastUndo: h.undo.length ? JSON.stringify(h.undo[h.undo.length - 1]).slice(0, 4000) : null, dirty: ps.dirty ?? null }; });
  return { scene, sceneSha: sha(scene), revision: eng && eng.revision != null ? String(eng.revision) : null, identitySha: sha(JSON.stringify(ident)), undo: h.undo, redo: h.redo, frame: h.frame, lastUndoSha: h.lastUndo ? sha(h.lastUndo) : null, dirty: h.dirty };
};
exports.same = (a, b) => ['sceneSha', 'revision', 'identitySha', 'undo', 'redo', 'lastUndoSha'].every(k => a[k] === b[k]);
exports.diff = (a, b) => Object.fromEntries(['sceneSha', 'revision', 'identitySha', 'undo', 'redo', 'lastUndoSha', 'dirty'].filter(k => a[k] !== b[k]).map(k => [k, [a[k], b[k]]]));
