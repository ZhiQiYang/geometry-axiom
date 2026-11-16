const { chromium } = require('playwright');
exports.start = async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1400, height: 900 }, acceptDownloads: true });
  const p = await ctx.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push('PAGEERR ' + String(e)));
  p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  p.on('dialog', d => { errs.push('DIALOG ' + d.message()); (p._accept ? d.accept(p._promptText) : d.dismiss()); });
  await p.goto('http://localhost:18839/', { waitUntil: 'networkidle' });
  await p.waitForTimeout(1200);
  const dismiss = p.getByRole('button', { name: '知道了' });
  if (await dismiss.isVisible().catch(()=>false)) await dismiss.click();
  return { b, ctx, p, errs };
};
exports.visibleButtons = p => p.$$eval('button, [role=menuitem], select, input', els => els.filter(e => e.offsetParent && e.getBoundingClientRect().width > 0).map(e => e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + ' ' + (e.textContent || e.value || e.placeholder || '').trim().replace(/\s+/g, ' ').slice(0, 40)));
exports.noPickers = p => p.evaluate(() => { for (const k of ['showSaveFilePicker','showOpenFilePicker']) Object.defineProperty(window, k, { configurable: true, writable: true, value: undefined }); });
exports.saveProject = async (p, file) => {
  await exports.noPickers(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200);
  const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 20000 }), p.click('#btnSaveProject')]);
  await dl.saveAs(file); return dl.suggestedFilename();
};
exports.openProject = async (p, file) => {
  await exports.noPickers(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 20000 }), p.click('#btnOpenProject')]);
  await fc.setFiles(file); await p.waitForTimeout(2500);
};
exports.status = p => p.evaluate(() => [...document.querySelectorAll('[role=status]')].filter(e=>e.offsetParent && e.textContent.trim()).map(e=>(e.id||'-')+': '+e.textContent.trim().slice(0,200)));

exports.newProject = async p => {
  p._accept = true;
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200);
  await p.click('#btnNewProject'); await p.waitForTimeout(1500);
  p._accept = false;
  const dismiss = p.getByRole('button', { name: '知道了' });
  if (await dismiss.first().isVisible().catch(()=>false)) await dismiss.first().click().catch(()=>{});
};
