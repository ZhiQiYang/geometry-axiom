// Differential check: the committed (old) and the patched (new) project store must agree on every project file in the repository.
// Usage: node differential.js <old geometry-web dir> <new geometry-web dir> <list of .gcanvas paths file>
'use strict';
const fs = require('node:fs'), path = require('node:path');
const [oldDir, newDir, listFile] = process.argv.slice(2);
const load = dir => ({P: require(path.join(dir, 'project-store.js')), zip: require(path.join(dir, 'vendor/fflate/umd/index.js'))});
const A = load(path.resolve(oldDir)), B = load(path.resolve(newDir));
const outcome = async fn => { try { return {ok: await fn()}; } catch (e) { return {error: String(e && e.message)}; } };
const plain = value => JSON.stringify(value, (k, v) => v instanceof Map ? [...v.keys()].sort() : v instanceof Uint8Array ? 'bytes:' + v.length : v);
(async () => {
  const files = fs.readFileSync(listFile, 'utf8').split('\n').filter(Boolean);
  let same = 0, opened = 0, refused = 0, scenarios = 0, withCases = 0; const formats = {}, differ = [];
  for (const file of files) {
    const bytes = new Uint8Array(fs.readFileSync(file));
    const a = await outcome(() => A.P.unpack(bytes, A.zip)), b = await outcome(() => B.P.unpack(bytes, B.zip));
    const rows = [['unpack', plain(a), plain(b)]];
    if (a.ok && b.ok) {
      opened++;
      const m = a.ok.manifest, scene = a.ok.scene;
      formats[m.format] = (formats[m.format] || 0) + 1;
      if (m.scenarioCatalog?.scenarios?.length) scenarios++;
      if (JSON.stringify(m).includes('rule-case-workbench-data/1')) withCases++;
      for (const [name, fn] of [
        ['projectFormat', P => P.projectFormat(structuredClone(m), scene)],
        ['projectFormat without declared capabilities', P => P.projectFormat({...structuredClone(m), requiredCapabilities: []}, scene)],
        ['validate', P => P.validate(structuredClone(m))],
        ['features.validate', P => m.featureAttachments ? P.Features.validate(structuredClone(m.featureAttachments), true) : null],
        ['features.capabilities', P => m.featureAttachments ? P.Features.capabilities(structuredClone(m.featureAttachments)) : null],
        ['repack manifest', async (P, zip) => (await P.unpack(await P.pack(scene, structuredClone(m), a.ok.sources, zip), zip)).manifest],
      ]) rows.push([name, plain(await outcome(() => fn(A.P, A.zip))), plain(await outcome(() => fn(B.P, B.zip)))]);
    } else refused++;
    const bad = rows.filter(r => r[1] !== r[2]);
    if (bad.length) differ.push({file, checks: bad.map(r => ({check: r[0], old: r[1].slice(0, 200), new: r[2].slice(0, 200)}))}); else same++;
  }
  console.log(JSON.stringify({files: files.length, identical: same, opened, refusedByBoth: refused, withScenarioCatalog: scenarios, withRuleCases: withCases, formats, differ}, null, 1));
  process.exit(differ.length ? 1 : 0);
})();
