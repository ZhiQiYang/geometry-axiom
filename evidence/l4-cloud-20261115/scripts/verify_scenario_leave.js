// 發現 7:隔離試改的內嵌畫面有修改後,用 MODE(cancel|save|pause)離開再重開。STAY=1 表示瀏覽器跳「要離開網站嗎」時選留下。
// 記錄瀏覽器自己跳出的對話框(訊息是空字串的那種)與第二次能不能開起來。
const C = require('./common.js'), L = C.L;
const MODE = process.env.MODE || 'cancel', EDIT = process.env.EDIT === '1';
const wait = async (p, fn, ms = 60000) => { for (const t0 = Date.now(); Date.now() - t0 < ms; await p.waitForTimeout(400)) if (await fn()) return true; return false; };
const count = p => p.evaluate(() => (ReferenceWorkspace.readScenarioCatalog().catalog?.scenarios || []).length);
const editorText = p => p.evaluate(() => { const d = document.getElementById('scenarioEditorDialog'); return d?.open ? d.innerText.replace(/\s+/g, ' ').slice(0, 160) : null; });
const frameState = async p => { const f = p.frames().find(x => /\?scenario=/.test(x.url())); if (!f) return null; return f.evaluate(() => ({ phase: typeof connection !== 'undefined' ? connection.phase : null, error: typeof connection !== 'undefined' ? connection.error : null, busy: typeof ReferenceWorkspace !== 'undefined' ? ReferenceWorkspace.busy : null })).catch(e => 'ERR ' + e.message.slice(0, 60)); };
const fsx = require('fs'); const out = {};
(async () => {
  const { b, p, errs } = await L.start();
  const net = [];
  p.on('response', async resp => { const u = resp.url().replace(/^https?:\/\/[^/]+/, ''); if (resp.status() >= 400 || /scenario/.test(u)) net.push(resp.status() + ' ' + resp.request().method() + ' ' + u.slice(0, 70)); });
  await L.newProject(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#exampleMenuBtn'); await p.waitForTimeout(200);
  p._accept = true; await p.click('#btnEx'); await p.waitForTimeout(1800); p._accept = false;
  await p.click('#projectInfoButton'); await p.waitForTimeout(600); await p.locator('.project-concepts summary').click(); await p.waitForTimeout(400); await p.click('#scenarioOpen'); await p.waitForTimeout(1000);
  await p.fill('#scenarioName', '方案A'); await p.click('#scenarioCapture'); await wait(p, async () => (await count(p)) === 1 && !(await p.isDisabled('#scenarioCapture')));
  await p.fill('#scenarioName', '方案B'); await p.click('#scenarioFork'); await wait(p, async () => (await count(p)) === 2 && !(await p.isDisabled('#scenarioFork')));
  const pick = async () => { const opts = await p.$$eval('#scenarioAfter option', os => os.map(o => [o.value, o.textContent.trim()])); await p.selectOption('#scenarioAfter', opts.find(o => /方案B/.test(o[1]))[0]); await p.waitForTimeout(300); };
  const open = async label => { await pick(); const t0 = Date.now(); await p.click('#scenarioEdit'); let last = ''; for (let i = 0; i < 45; i++) { await p.waitForTimeout(2000); const t = await editorText(p), fs = await frameState(p); const line = JSON.stringify([t, fs]); if (line !== last) { console.log(label, Math.round((Date.now() - t0) / 1000) + 's', line); last = line; } if (t && !/正在/.test(t) && !(await p.isDisabled('#scenarioPauseEdit').catch(() => true))) return true; if (t && /逾時|中斷|失敗/.test(t)) return false; } return false; };
  out.open1 = await open('open1'); console.log('open1 ok', out.open1);
  if (EDIT) { const f = p.frames().find(x => /\?scenario=/.test(x.url())); const box = await f.locator('#btnCreateObject').boundingBox(); await p.mouse.click(box.x + 20, box.y + 20); await p.waitForTimeout(500); const b2 = await f.locator('#btnNewParameter').boundingBox(); await p.mouse.click(b2.x + 20, b2.y + 10); await p.waitForTimeout(1200); await f.fill('#paramName', '試改板材'); await f.fill('#paramQuick', '(915,1830)'); await f.press('#paramQuick', 'Enter'); await p.waitForTimeout(1500); const b3 = await f.locator('#paramConfirm').boundingBox(); await p.mouse.click(b3.x + 20, b3.y + 10); await p.waitForTimeout(1800); console.log('edited cards', await f.evaluate(async () => ((await apiRequest('objects')).parameters || []).map(x => x.name))); }
  const leave = { cancel: '#scenarioCancelEdit', save: '#scenarioFinishEdit', pause: '#scenarioPauseEdit' }[MODE];
  const t1 = Date.now(); p._accept = process.env.STAY !== '1'; await p.click(leave); const closed = await wait(p, async () => !(await p.locator('#scenarioEditorDialog').isVisible().catch(() => false)), 60000); p._accept = false;
  out.leave = { mode: MODE, stayOnBrowserPrompt: process.env.STAY === '1', closed, status: await p.evaluate(() => document.getElementById('scenarioStatus')?.innerText) }; console.log(JSON.stringify(out.leave));
  net.push('--- reopen');
  out.open2 = await open('open2'); out.open2Text = await editorText(p); console.log('open2 ok', out.open2);
  // 結束前正常取消,不留下試改工作階段
  if (await p.locator('#scenarioEditorDialog').isVisible().catch(() => false)) { p._accept = true; await p.click('#scenarioCancelEdit').catch(() => {}); await p.waitForTimeout(3000); console.log('cleanup editor text', await editorText(p), 'status', await p.evaluate(() => document.getElementById('scenarioStatus')?.innerText)); }
  console.log('net', JSON.stringify(net.filter(x => !/^200 GET/.test(x)), null, 0));
  out.dialogs = errs.filter(e => e.startsWith('DIALOG')).slice(1).map(e => e.slice(0, 60)); out.browserLeavePrompts = out.dialogs.filter(e => e.trim() === 'DIALOG').length; out.errs = errs.filter(e => !e.startsWith('DIALOG'));
  console.log('dialogs', JSON.stringify(out.dialogs));
  if (process.env.OUT) fsx.writeFileSync(`${process.env.OUT}/verify_scenario_leave.${process.env.TAG || 'run'}.${MODE}${process.env.STAY === '1' ? '-stay' : ''}.json`, JSON.stringify(out, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 900)); process.exit(1); });
