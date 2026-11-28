'use strict';

/* T scaffold: the separately invoked study API is present, but the proposed S2
 * algorithm is not implemented. This is never a product capability or fallback. */
const fs = require('node:fs');
function evaluate(data) {
  const rows = JSON.parse(JSON.stringify(data.representations));
  const excluded = [...data.declarations.excluded].sort();
  const sum = list => list.reduce((n, row) => n + row.native.content.L, 0);
  return {studySchema: 'U476-result/1', researchOnly: true, status: 'INCOMPLETE',
    diagnostics: [{severity: 'INCOMPLETE', code: 'S2_NOT_IMPLEMENTED', ref: ''}],
    rawRows: rows.sort((a, b) => a.ref < b.ref ? -1 : a.ref > b.ref ? 1 : 0), excluded,
    items: [], itemCount: null, accounting: {rawRepresentedLengthMm: sum(rows),
      excludedLengthMm: sum(rows.filter(row => excluded.includes(row.ref))),
      includedRepresentedLengthMm: sum(rows.filter(row => !excluded.includes(row.ref))),
      physicalItemLengthMm: null, removedAliasLengthMm: null}};
}
function notImplemented() { const error = new Error('S2_NOT_IMPLEMENTED'); error.code = error.message; throw error; }
class StudyHistory {
  constructor() {notImplemented();}
  static reopen() {return notImplemented();}
  begin() {return notImplemented();} commit() {return notImplemented();} cancel() {return notImplemented();}
  undo() {return notImplemented();} redo() {return notImplemented();} view() {return notImplemented();}
  save() {return notImplemented();} evaluate() {return notImplemented();}
}
module.exports = {LIMITS: {items:64,representations:128,models:8,bytes:131072,nodes:4096,depth:12},
  DOCUMENT_SCHEMA: 'U476-study-document/1', evaluate, memberOf: notImplemented, tupleOf: notImplemented,
  validateDocument: notImplemented, serializeDocument: notImplemented, parseDocument: notImplemented,
  evaluateDocument: notImplemented, StudyHistory, runHistory: notImplemented};
if (require.main === module) {
  try { const data = JSON.parse(fs.readFileSync(0, 'utf8'));
    process.stdout.write(JSON.stringify(process.argv[2] === 'batch' ? data.map(evaluate) : evaluate(data)) + '\n');
  } catch (error) {process.stderr.write((error.code || error.message) + '\n'); process.exitCode = 1;}
}
