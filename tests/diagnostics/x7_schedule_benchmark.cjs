#!/usr/bin/env node
'use strict';
// Measures the real F4a module, with verified native references as input.
// Process startup, file I/O and JSON parsing are outside the measured region.
const fs = require('node:fs');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const schedule = require('../../geometry-web/timber-schedule.js');
const [referencesPath, iterationsText = '5', outputPath] = process.argv.slice(2);
assert(referencesPath && outputPath, 'X7_SCHEDULE_USAGE: references.json iterations result.json');
assert(!fs.existsSync(outputPath) && !fs.existsSync(outputPath + '.csv-array.json'), 'X7_SCHEDULE_NEW_OUTPUT');
const iterations = Number(iterationsText);
assert(Number.isSafeInteger(iterations) && iterations >= 1 && iterations <= 30, 'X7_SCHEDULE_BOUNDED_ITERATIONS');
const input = fs.readFileSync(referencesPath);
const references = JSON.parse(input);
assert.equal(references.ok, true, 'X7_SCHEDULE_REAL_REFERENCES');
const surfaces = [...new Set(references.timbers.map(row => row.geometry.surface))].sort((a, b) => a - b);
const expectedIds = references.timbers.map(row => row.id).sort((a, b) => a - b);
const rows = [];
let exactBytes;
for (let index = 0; index < iterations; ++index) {
  let started = process.hrtime.bigint();
  const lists = surfaces.map(surface => schedule.derive(references, surface));
  const deriveNs = process.hrtime.bigint() - started;
  started = process.hrtime.bigint();
  const csv = lists.map(list => schedule.csv(list));
  const csvNs = process.hrtime.bigint() - started;
  assert.deepEqual(lists.flatMap(list => list.rows.map(row => row.id)).sort((a, b) => a - b), expectedIds, 'X7_SCHEDULE_ALL_MEMBERS');
  const source = new Map(references.timbers.map(row => [row.id, row]));
  for (const list of lists) for (const row of list.rows) {
    const geometry = source.get(row.id).geometry;
    assert.deepEqual([row.A, row.B, row.L, row.surface, row.origin],
      [geometry.A, geometry.B, geometry.length, geometry.surface, geometry.origin], 'X7_SCHEDULE_VALUES');
    assert.deepEqual(row.finish, geometry.origin.map((value, axis) => value + geometry.axes[0][axis] * geometry.length), 'X7_SCHEDULE_FINISH');
    assert.equal(row.sourceFingerprint, references.sourceFingerprint, 'X7_SCHEDULE_PROVENANCE');
  }
  const bytes = Buffer.from(JSON.stringify(csv));
  if (exactBytes) assert(bytes.equals(exactBytes), 'X7_SCHEDULE_DETERMINISTIC_BYTES');
  else exactBytes = bytes;
  rows.push({iteration: index, derive_ms: Number(deriveNs) / 1e6, csv_ms: Number(csvNs) / 1e6,
    cold_module_sample: index === 0});
}
const result = {schema: 'x7-schedule-measurement/1', acceptance: false, node: process.version,
  references_sha256: crypto.createHash('sha256').update(input).digest('hex'),
  count: expectedIds.length, surfaces: surfaces.length, csv_bytes: exactBytes.length,
  csv_sha256: crypto.createHash('sha256').update(exactBytes).digest('hex'), rows};
fs.writeFileSync(outputPath, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
fs.writeFileSync(outputPath + '.csv-array.json', exactBytes, {flag: 'wx'});
process.stdout.write(JSON.stringify(result) + '\n');
