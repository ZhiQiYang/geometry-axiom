// R04 b：從「檔案 → 開啟場景檔…」載入 512 支場景（geo300_scene_generator.build(512,"single")），再放第 513 支
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n}.png` });
const count = text => ({ timbers: (text.match(/^timber /gm) || []).length, places: (text.match(/^place /gm) || []).length });
(async () => {
  const r = {};
  const { b, p, errs } = await L.start();
  const api = L.trackApi(p);
  await L.newProject(p);
  const t0 = await L.openScene(p, `${OUT}/scenes/single-0512.scene`);
  // 載入完成 = 物件清單出現邊界卡片且 dump 含 512 支
  let loaded = null;
  for (let i = 0; i < 600; i++) { await p.waitForTimeout(250); const c = await p.evaluate(async () => { const d = await apiRequest('dump'); return (d.text.match(/^place /gm) || []).length; }).catch(() => -1); if (c >= 512) { loaded = Date.now() - t0; break; } }
  r.loadSecondsToDump512 = loaded === null ? null : loaded / 1000;
  const cardShown = await p.locator('.ocard[data-kind="boundary"]').first().isVisible().catch(() => false);
  r.cardShown = cardShown;
  r.loadStatus = await L.status(p);
  const s0 = await L.snap(p); r.before = count(s0.text);
  await shot(p, 'R04b-1-loaded-512');
  // 第 513 支：經指令列
  await p.click('#cmdToggle'); await p.waitForTimeout(300);
  const send = async (cmd, shotName) => { const n = api.length; await p.fill('#cmd', cmd); await p.press('#cmd', 'Enter'); await p.waitForTimeout(800); if (shotName) await shot(p, shotName); await p.waitForTimeout(1700); return { cmd, replies: api.slice(n) }; };
  r.cmds = [];
  r.cmds.push(await send('timber 513 27 33 role secondary', 'R04b-2-513-rejected'));
  r.cmds.push(await send('place 513 on 1 at-face e3 between e3 e1 -v +n'));
  r.statusAfter = await L.status(p);
  const bodyText = await p.evaluate(() => document.body.innerText);
  r.limitTextOnScreen = (bodyText.match(/[^\n]*(上限|512)[^\n]*/g) || []).slice(0, 5);
  const s1 = await L.snap(p); r.after = count(s1.text); const strip = t => t.split('\n').filter(l => !l.startsWith('#') && !l.startsWith('canvas-pos')).join('\n'); r.sceneUnchanged = strip(s1.text) === strip(s0.text); r.rawDiffLines = s1.text.split('\n').filter(l => !s0.text.split('\n').includes(l)).slice(0, 5);
  r.errs = errs;
  fs.writeFileSync(`${OUT}/walk_r04b.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 600)); process.exit(1); });
