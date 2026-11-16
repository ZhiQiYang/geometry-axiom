// Baseline: how many whole-attachment validations does one projectFormat / projectCapabilities call cost?
// Usage: node count_node.js <worktree>
'use strict';
const path = require('node:path'), {execFileSync} = require('node:child_process');
const root = path.resolve(process.argv[2]);
const P = require(path.join(root, 'geometry-web/project-store.js')), C = P.Features.Cases;
const templates = JSON.parse(execFileSync('python3', ['-c', "import sys,json;sys.path.insert(0,'geometry-core');from rule_cases.catalog import cases;print(json.dumps(cases()))"], {cwd: root, encoding: 'utf8'}));
const data = () => ({schema: C.SCHEMA, definitions: structuredClone(templates), receipts: []});
const manifest = () => ({format: P.FORMAT, projectId: 'case-project', name: 'Synthetic cases', sources: [], faces: [], models: [], faceProjections: [],
  featureAttachments: {schema: P.Features.SCHEMA, records: [P.Features.record(C.KIND, data())]}});
console.log('frozen Features:', Object.isFrozen(P.Features), 'frozen Cases:', Object.isFrozen(C), 'exports projectCapabilities:', typeof P.projectCapabilities);
let caps = 0, cases = 0;
const realCaps = P.Features.capabilities, realValidate = C.validate;
P.Features.capabilities = envelope => { caps++; return realCaps(envelope); };
C.validate = value => { cases++; return realValidate(value); };
for (const scenarios of [0, 1, 2, 4]) {
  const m = manifest();
  if (scenarios) m.scenarioCatalog = {scenarios: Array.from({length: scenarios}, () => ({snapshot: {projectManifest: manifest(), worldScene: 'reset\n'}}))};
  caps = cases = 0; const t = process.hrtime.bigint();
  const format = P.projectFormat(m, 'reset\n');
  const ms = Number(process.hrtime.bigint() - t) / 1e6;
  console.log(JSON.stringify({scenarios, format, capabilitiesCalls: caps, caseValidateCalls: cases, ms: Math.round(ms)}));
}
