// R04 a：在 App 的指令列，同一個面連續放 110 支角材（超過舊上限 64），另存、冷開比對
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n}.png` });
const keep = t => t.split('\n').filter(l => /^(boundary|placement|grid|timber|place) /.test(l));
(async () => {
  const r = { perCommand: [] };
  const lines = fs.readFileSync(`${OUT}/scenes/single-0110.scene`, 'utf8').split('\n').filter(l => l && !l.startsWith('#'));
  let { b, p, errs } = await L.start();
  const api = L.trackApi(p);
  await L.newProject(p);
  await p.click('#cmdToggle'); await p.waitForTimeout(300);
  let placed = 0, firstReject = null; const t00 = Date.now();
  for (const line of lines) {
    const n = api.length, t0 = Date.now();
    await p.fill('#cmd', line); await p.press('#cmd', 'Enter');
    const mine = x => x.cmd === ('line ' + line).slice(0, 80);
    for (let i = 0; i < 1200 && !api.slice(n).some(mine); i++) await p.waitForTimeout(50);
    const rep = api.slice(n).find(mine); await p.waitForTimeout(30);
    const sec = (Date.now() - t0) / 1000;
    if (rep?.ok === false) { firstReject = firstReject || { line, error: rep.error, afterPlaced: placed }; }
    if (/^place /.test(line) && rep?.ok !== false) placed++;
    r.perCommand.push({ i: r.perCommand.length, cmd: line.slice(0, 40), ok: rep?.ok, sec });
    if (placed === 65 && /^place /.test(line)) { r.sixtyFifth = { line, ok: rep?.ok, error: rep?.error }; await shot(p, 'R04a-1-65th-placed'); }
  }
  r.totalSeconds = (Date.now() - t00) / 1000;
  r.placed = placed; r.firstReject = firstReject;
  await p.waitForTimeout(800);
  const s0 = await L.snap(p); r.timbers = (s0.text.match(/^timber /gm) || []).length; r.places = (s0.text.match(/^place /gm) || []).length;
  await shot(p, 'R04a-2-110-placed');
  // 進入面 1 看構件
  await p.click('.ocard[data-kind="boundary"][data-id="1"]').catch(() => {}); await p.waitForTimeout(300);
  await p.click('.ocard[data-kind="boundary"][data-id="1"] .card-enter').catch(() => {}); await p.waitForTimeout(2000); await L.lesson(p);
  await shot(p, 'R04a-3-face-110');
  r.saved = await L.saveProject(p, `${OUT}/r04a-110.gcanvas`);
  const before = keep(s0.text);
  await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r04a-110.gcanvas`);
  const s1 = await L.snap(p); const after = keep(s1.text);
  r.cold = { timbers: (s1.text.match(/^timber /gm) || []).length, places: (s1.text.match(/^place /gm) || []).length, identical: JSON.stringify(before) === JSON.stringify(after) };
  await p.click('.ocard[data-kind="boundary"][data-id="1"]').catch(() => {}); await p.waitForTimeout(300);
  await p.click('.ocard[data-kind="boundary"][data-id="1"] .card-enter').catch(() => {}); await p.waitForTimeout(2000); await L.lesson(p);
  await shot(p, 'R04a-4-cold-face-110');
  r.errs = errs;
  fs.writeFileSync(`${OUT}/walk_r04a.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify({ ...r, perCommand: r.perCommand.length, slowest: r.perCommand.sort((a, b) => b.sec - a.sec).slice(0, 3) }, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 600)); process.exit(1); });
