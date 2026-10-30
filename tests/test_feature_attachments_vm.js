/* Browser scripts have no module object. Node's require() path cannot see
 * a free `root` reference inside the factory, so load the page order here. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const WEB = path.join(__dirname, '..', 'geometry-web');
const PAGE_ORDER = [
  'reference-display.js',
  'source-plane.js',
  'evidence-links.js',
  'rule-case-data.js',
  'room-candidate-draft.js',
  'feature-attachments.js',
];

test('沒有 module 時載入後 GeometryFeatureAttachments 有定義', () => {
  const sandbox = {
    TextEncoder, TextDecoder, URL, URLSearchParams, crypto, console, structuredClone,
  };
  const context = vm.createContext(sandbox);
  for (const file of PAGE_ORDER) {
    const code = fs.readFileSync(path.join(WEB, file), 'utf8');
    vm.runInContext(code, context, {filename: file});
  }
  assert.equal(typeof sandbox.module, 'undefined');
  assert.equal(typeof sandbox.GeometryFeatureAttachments, 'object');
  assert.equal(sandbox.GeometryFeatureAttachments.ROOM_CANDIDATE_SCHEMA, 'room-candidate-drafts/1');
  assert.equal(typeof sandbox.GeometryFeatureAttachments.RoomCandidates.validate, 'function');
});
