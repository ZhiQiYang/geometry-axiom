// R04 c：場景 99／299／499 支 → 再放第 100／300／500 支角材（指令列送 timber、place），量「送出到畫面更新」秒數，各 3 次（issue #381 的使用數據；只記錄不判定）
// 場景檔 = geo300_scene_generator.build(N,"single") 去掉最後一個葉節點（timber＋place 兩行），從「檔案 → 開啟場景檔…」載入；
// 之後把這兩行經指令列補回去。畫面更新 = place 回覆後 App 接著重讀 objects/surfaces/boundary/dump 的最後一個回覆，再等兩個 animation frame。
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n}.png` });
const pad = N => String(N).padStart(4, '0');
(async () => {
  const r = { runs: [] };
  const { b, p, errs } = await L.start();
  const api = L.trackApi(p);
  for (const N of [100, 300, 500]) {
    const meta = JSON.parse(fs.readFileSync(`${OUT}/scenes/single-${pad(N)}.json`, 'utf8')), leaf = meta.leaf;
    const run = { N, before: N - 1, after: N, leafId: leaf.id, trials: [] };
    for (let k = 1; k <= 3; k++) {
      await L.newProject(p);
      const t0 = await L.openScene(p, `${OUT}/scenes/single-${pad(N)}-minus-leaf.scene`);
      let load = null;
      for (let i = 0; i < 900; i++) { await p.waitForTimeout(200); const c = await p.evaluate(async () => (((await apiRequest('dump')).text).match(/^place /gm) || []).length).catch(() => -1); if (c >= N - 1) { load = (Date.now() - t0) / 1000; break; } }
      await p.waitForTimeout(1500);
      if (!(await p.isVisible('#cmd'))) { await p.click('#cmdToggle'); await p.waitForTimeout(300); }
      const send = async cmd => {
        const n = api.length; await p.fill('#cmd', cmd);
        const t = Date.now(); await p.press('#cmd', 'Enter');
        let reply = null;
        for (let i = 0; i < 12000 && reply === null; i++) { const m = api.slice(n).find(x => x.cmd === ('line ' + cmd).slice(0, 80)); if (m) reply = m; else await p.waitForTimeout(10); }
        let dump = null;
        for (let i = 0; i < 12000 && dump === null; i++) { const m = api.slice(n).find(x => x.cmd === 'dump' && reply && x.t >= reply.t); if (m) dump = m; else await p.waitForTimeout(10); }
        await p.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
        const screen = (Date.now() - t) / 1000;
        return { cmd: cmd.slice(0, 40), ok: reply?.ok, error: reply?.error, replySec: reply ? (reply.t - t) / 1000 : null, refreshDoneSec: dump ? (dump.t - t) / 1000 : null, screenSec: screen, apiCalls: api.slice(n).map(x => x.cmd.slice(0, 14)) };
      };
      const decl = await send(leaf.timber);
      const place = await send(leaf.place);
      const count = await p.evaluate(async () => (((await apiRequest('dump')).text).match(/^place /gm) || []).length);
      run.trials.push({ k, loadSeconds: load, decl, place, placesAfter: count });
      console.log(N, k, JSON.stringify({ load, place: place.replySec, refresh: place.refreshDoneSec, screen: place.screenSec, ok: place.ok, count }));
      if (k === 3) await shot(p, `R04c-N${N}-after`);
    }
    r.runs.push(run);
  }
  r.errs = errs;
  fs.writeFileSync(`${OUT}/walk_r04c.result.json`, JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 600)); process.exit(1); });
