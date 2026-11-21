// D07 從面建立 3D 空間（GEO-205～208、210、243、244；#117）：只用滑鼠與鍵盤。
// 檔案 → 範例 → 進入面 1 → 右欄「屬性」→「以此面建立空間」→ 俯視 →「確認用途與觀看方向」→「牆底設為 0 mm」→ 牆高 3000 改 2700
// → 「更新預覽」→「返回畫布」（取消：不建立）→ 再開 → 預覽 → 勾核對 →「建立空間」→ 復原／重做 → 3D 模型庫看模型
// → 另存 → 全新瀏覽器開檔 → 3D 模型庫。
const L = require('./lib.js');
const r = { steps: [] };
// 唯讀：目前專案的空間模型紀錄摘要
const models = p => p.evaluate(() => (ReferenceWorkspace.getSpaceModels?.() || []).map(m => ({ id: m.id, name: m.name, settings: m.input?.settings, timbers: (m.input?.timbers || []).length, projection: m.source?.projection, summary: m.result?.summary, walls: Array.isArray(m.result?.walls) ? m.result.walls.length : typeof m.result?.walls, bytes: JSON.stringify(m).length })));
const modelsFull = p => p.evaluate(() => JSON.stringify(ReferenceWorkspace.getSpaceModels?.() || []));
(async () => {
  let { b, p, errs } = await L.start();
  let shot = L.shotter(p, 'D07');
  const st = () => p.textContent('#smStatus').then(t => t.replace(/\s+/g, ' ').slice(0, 300)).catch(() => null);
  const step = async (name, extra = {}) => { const d = await L.dump(p); r.steps.push({ name, dumpLen: d.length, models: await models(p), spaceLines: d.split(/\r?\n/).filter(l => /^(space|model|projection|wall|plan)/i.test(l)).slice(0, 12), ...extra }); await shot(name); return d; };
  const openSpace = async (enter = true) => { if (enter) await L.enterFace1(p); await p.click('[data-fi-tab="prop"]'); await p.waitForTimeout(500); r.spaceButtons = (r.spaceButtons || []).concat(await p.getByRole('button', { name: /此(平)?面建立空間/ }).first().innerText()); await p.getByRole('button', { name: /此(平)?面建立空間/ }).first().click(); await p.waitForTimeout(3000); };
  await L.newProject(p); await L.loadExample(p);
  const d0 = await step('01-example');
  await openSpace();
  r.heightDefault = await p.inputValue('#smHeight'); r.heightHelp = await p.textContent('#smHeightHelp');
  r.timberCount = await p.textContent('#smTimberCount'); r.includeTimbers = await p.isChecked('#smIncludeTimbers');
  const dOpen = await step('02-space-dialog', { status: await st() });
  r.openWritesNothing = dOpen === d0;
  await p.selectOption('#smProjectionView', 'top');
  p._accept = true; await p.click('#smConfirmProjection'); await p.waitForTimeout(3000); p._accept = false;
  const cfm = p.getByRole('button', { name: '確認套用' }); if (await cfm.isVisible().catch(() => false)) { r.projectionImpactShown = true; await shot('03a-projection-impact'); await cfm.click(); await p.waitForTimeout(2500); }
  const dProj = await step('03-projection-confirmed', { status: await st() });
  r.projectionDiff = dProj.split(/\r?\n/).filter(l => !d0.split(/\r?\n/).includes(l));
  await p.click('#smBottomZero'); await p.waitForTimeout(600);
  await p.click('#smHeight', { clickCount: 3 }); await p.keyboard.type('2700'); await p.keyboard.press('Tab'); await p.waitForTimeout(600);
  r.bottom = await p.inputValue('#smBottom'); r.height = await p.inputValue('#smHeight');
  await p.click('#smPreview'); await p.waitForTimeout(3500);
  const dPrev = await step('04-preview', { status: await st(), badge: await p.textContent('#smResultBadge').catch(() => null), main: (await p.textContent('#smMain')).replace(/\s+/g, ' ').slice(0, 400) });
  r.previewWritesNothing = dPrev === dProj;
  // 取消：返回畫布、不建立
  await p.click('#smClose'); await p.waitForTimeout(1500);
  const dCancel = await step('05-cancel-back-to-canvas', { modelCount: (await p.textContent('#btnSpaceModels').catch(() => '')).trim() });
  r.cancelZeroWrite = dCancel === dProj;
  // 再開 → 預覽 → 建立
  r.afterCancelInFace = await p.isVisible('#workspaceBackButton');
  await openSpace(false);
  r.reopenHeight = await p.inputValue('#smHeight'); r.reopenBottom = await p.inputValue('#smBottom');
  if (r.reopenBottom === '') { await p.click('#smBottomZero'); await p.waitForTimeout(500); }
  if (r.reopenHeight !== '2700') { await p.click('#smHeight', { clickCount: 3 }); await p.keyboard.type('2700'); await p.keyboard.press('Tab'); await p.waitForTimeout(500); }
  await p.click('#smPreview'); await p.waitForTimeout(3500);
  if (await p.isVisible('#smReviewJump')) { await p.click('#smReviewJump'); await p.waitForTimeout(800); }
  const cf = p.locator('#smConfirmFaces'); await cf.scrollIntoViewIfNeeded().catch(() => {});
  r.createEnabledBeforeCheck = await p.isEnabled('#smCreate');
  if (await cf.isVisible() && !(await cf.isChecked())) await cf.click();
  await shot('06-preview-checked');
  r.createEnabled = await p.isEnabled('#smCreate');
  p._accept = true; await p.click('#smCreate'); await p.waitForTimeout(4500); p._accept = false;
  const dC = await step('07-created', { status: await st(), library: (await p.textContent('#smLibrary').catch(() => '')).trim() });
  r.createDiff = dC.split(/\r?\n/).filter(l => !dProj.split(/\r?\n/).includes(l)).slice(0, 30);
  await p.click('#smClose'); await p.waitForTimeout(1500);
  r.modelButton = (await p.textContent('#btnSpaceModels')).replace(/\s+/g, ' ').trim();
  await p.keyboard.press('Control+z'); await p.waitForTimeout(2000);
  const dU = await step('08-undo', { toasts: await L.toasts(p), modelButton: (await p.textContent('#btnSpaceModels')).replace(/\s+/g, ' ').trim() });
  r.undoEqualsBeforeCreate = dU === dProj;
  await p.keyboard.press('Control+y'); await p.waitForTimeout(2000);
  const dY = await step('09-redo', { modelButton: (await p.textContent('#btnSpaceModels')).replace(/\s+/g, ' ').trim() });
  r.redoEqualsCreated = dY === dC;
  // 3D 模型庫
  r.inputKeys = await p.evaluate(() => Object.keys((ReferenceWorkspace.getSpaceModels?.() || [])[0]?.input || {}));
  r.resultKeys = await p.evaluate(() => Object.keys((ReferenceWorkspace.getSpaceModels?.() || [])[0]?.result || {}));
  r.modelsFullBefore = await modelsFull(p);
  await p.click('#workspaceBackButton'); await p.waitForTimeout(1000);
  await p.click('#btnSpaceModels'); await p.waitForTimeout(2500);
  r.libraryText = (await p.evaluate(() => (document.querySelector('#smLibraryList, #smLibraryPanel, .sm-library') || document.querySelector('#spaceModel') || document.body).innerText)).replace(/\s+/g, ' ').slice(0, 900);
  await shot('10-model-library');
  await p.click('#smClose').catch(() => {}); await p.waitForTimeout(1000);
  r.saved = await L.saveProject(p, `${L.out()}/d07.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start()); shot = L.shotter(p, 'D07');
  await L.newProject(p); await L.openProject(p, `${L.out()}/d07.gcanvas`);
  const dR0 = await L.dump(p); r.reopenAt2500 = { dumpEqual: dR0 === dC, modelButton: (await p.textContent('#btnSpaceModels')).replace(/\s+/g, ' ').trim(), models: await models(p) };
  await p.waitForTimeout(4000);
  const dR = await L.dump(p); r.reopenEqual = dR === dC; r.reopenDumpOnlyBefore = dC.split(/\r?\n/).filter(l => !dR.split(/\r?\n/).includes(l)); r.reopenDumpOnlyAfter = dR.split(/\r?\n/).filter(l => !dC.split(/\r?\n/).includes(l)); r.reopenModels = await models(p); r.reopenModelsEqual = (await modelsFull(p)) === r.modelsFullBefore; delete r.modelsFullBefore; r.reopenModelButton = (await p.textContent('#btnSpaceModels')).replace(/\s+/g, ' ').trim();
  await shot('11-reopened');
  await p.click('#btnSpaceModels'); await p.waitForTimeout(2500);
  r.reopenLibraryText = (await p.evaluate(() => (document.querySelector('#smLibraryList, #smLibraryPanel, .sm-library') || document.querySelector('#spaceModel') || document.body).innerText)).replace(/\s+/g, ' ').slice(0, 900);
  await shot('12-reopened-library');
  r.errsB = errs;
  L.write('walk_d07.result.json', r); console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); L.write('walk_d07.partial.json', r); process.exit(1); });
