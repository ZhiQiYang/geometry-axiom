'use strict';
const fs = require('fs');
const path = require('path');
const qa = require('D:/geometry-axiom-inspector-draft/geometry-web/docs/evidence/qa-acceptance-d6b4b45-20261005/tools/qa_cdp.js');
const TEST_URL = process.env.GEOMETRY_TEST_URL;
const OUT = process.env.GEOMETRY_PHASE3_OUT;
const file = path.join(OUT, 'model-save.gcanvas');
(async () => {
  const b = await qa.launch({
    chrome: process.env.GEOMETRY_CHROME,
    port: Number(process.env.GEOMETRY_CDP_PORT),
    profileDir: path.join(OUT, 'chrome-profile-undo'),
    width: 1440, height: 1000, cleanupProfile: false
  });
  b.setDialogPolicy('accept');
  const read = expr => b.evalReadOnly(expr);
  const idle = () => b.waitFor('!oc.busy && !ReferenceWorkspace.busy', 30000);
  try {
    await b.goto(TEST_URL);
    await b.waitFor(`connection.phase==='ready'`, 40000);
    await b.chooseFileOnNext(file);
    await b.click('#fileMenuBtn');
    await b.click('#btnOpenProject');
    await b.waitForChooser();
    await idle();
    await b.waitFor(`ReferenceWorkspace.getSpaceModels().length===1`, 20000);
    const snap = async () => read(`(async()=>{const c=ReferenceWorkspace.context();const r=await apiRequest('dump');return {dump:r.text,id:c.id,name:c.name,dirty:!!c.dirty,saved:!!c.saved,downloaded:!!c.downloaded,models:ReferenceWorkspace.getSpaceModels().map(m=>({id:m.id,source:m.result&&m.result.source_sha256})),undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length,label:ReferenceWorkspace.historyActionLabel('undo')};})()`);
    const before = await snap();
    await b.click('#fileMenuBtn');
    await b.click('#btnNewProject');
    await idle();
    const emptied = await snap();
    await b.click('#btnUndo');
    await idle();
    const undone = await snap();
    const diff = {};
    for (const key of Object.keys(before)) diff[key] = { before: before[key], undone: undone[key], same: JSON.stringify(before[key]) === JSON.stringify(undone[key]) };
    fs.writeFileSync(path.join(OUT, 'undo-new-project.json'), JSON.stringify({ before, emptied, undone, diff }, null, 2));
    console.log('UNDO_DIFF ' + JSON.stringify(Object.fromEntries(Object.entries(diff).map(([k, v]) => [k, v.same]))));
    console.log('LABELS ' + JSON.stringify({ before: before.label, emptied: emptied.label, undone: undone.label, emptiedModels: emptied.models.length, undoneModels: undone.models.length }));
  } finally { await b.close(); }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
