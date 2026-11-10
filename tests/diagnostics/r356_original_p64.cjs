/* Run the unchanged P64 block with the original CDP setup and result reporter.
 * Diagnostic only: neither this extractor nor a partial receipt grants shard
 * coverage. It never changes an assertion, the driver, or a golden file.
 *
 *   node tests/diagnostics/r356_original_p64.cjs
 *   node tests/diagnostics/r356_original_p64.cjs --through-t4
 *   node tests/diagnostics/r356_original_p64.cjs --describe --through-t4
 *
 * Runtime settings are the original driver's GEOMETRY_* environment variables.
 * --describe only validates extraction and prints hashes; it starts no browser.
 */
'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const Module = require('node:module');
const path = require('node:path');

const root = path.resolve(__dirname, '../..');
const args = process.argv.slice(2);
assert(args.every(arg => ['--through-t4', '--describe'].includes(arg)) &&
  new Set(args).size === args.length,
  'usage: node r356_original_p64.cjs [--through-t4] [--describe]');
const throughT4 = args.includes('--through-t4');
const file = path.join(root, 'geometry-web/cdp_test.js');
const bytes = fs.readFileSync(file), source = bytes.toString('utf8');
assert(Buffer.from(source, 'utf8').equals(bytes), 'driver must round-trip as UTF-8');
const unique = needle => {
  const at = source.indexOf(needle);
  assert(at >= 0 && source.indexOf(needle, at + needle.length) < 0,
    'exactly one original driver marker: ' + needle);
  return at;
};
const prefix = unique('  if(process.env.GEOMETRY_TIMBER_REUSE_ONLY){');
const begin = unique('  { // The 2026-09-27 review draft: visible controls and their real interactions.');
const end = unique('  { // First-version space-model entry points;');
const t4End = unique('    const edgeTimber=await eval_(');
const suffix = unique('  chrome.kill();\n  if(passN+failN===0)');
unique("    check('P64 T4 編輯角材聚焦且明示已帶入原定位引用',t4.tab==='timber'&&t4.focus==='tbEditAnchor'&&!!t4.anchor&&t4.note,t4);");
const entry = 'if(require.main===module){';
unique(entry);
assert(prefix < begin && begin < t4End && t4End < end && end < suffix,
  'original P64 and setup/report boundaries must remain in order');

const originalBlock = source.slice(begin, end);
const selectedOriginal = source.slice(begin, throughT4 ? t4End : end);
// The prefix variant ends at the original T4 statement; only its structural
// closing brace is supplied. No assertion statement or helper is rewritten.
const section = selectedOriginal + (throughT4 ? '  }\n' : '');
const program = (source.slice(0, prefix) + section + source.slice(suffix))
  .replace(entry, 'if(true){');
new Function(program);
const hash = value => ({bytes: Buffer.byteLength(value),
  sha256: crypto.createHash('sha256').update(value).digest('hex')});
const manifest = {
  schema: 'r356-original-p64-extraction/1', root, driver: file,
  selection: throughT4 ? 'original P64 prefix through T4' : 'original full P64 block',
  expectedAssertions: throughT4 ? 18 : 24,
  driverBytes: hash(bytes), originalBlock: hash(originalBlock),
  selectedOriginal: hash(selectedOriginal), executableProgram: hash(program),
  structuralChanges: ['select original setup/block/reporter',
    ...(throughT4 ? ['close the selected P64 block'] : []),
    'execute the original main-module entry in this wrapper'],
  coverage: 'Diagnostic partial mode only; no full run, shard, or golden credit.'
};
console.log('R356_P64_DIAGNOSTIC ' + JSON.stringify(manifest));
if (!args.includes('--describe')) {
  assert(!Object.keys(process.env).some(name => name.startsWith('GEOMETRY_') &&
    (name.endsWith('_ONLY') || ['GEOMETRY_CDP_SHARD', 'GEOMETRY_CDP_UPDATE_GOLDEN',
      'GEOMETRY_TIMBER_REUSE_CASE', 'GEOMETRY_R116_FRESH_STAGE'].includes(name))),
  'P64 diagnostic cannot combine scopes, reuse a child stage, or update golden');
  process.env.GEOMETRY_CDP_FROM_P31 = '1';
  const runner = new Module(file, module);
  runner.filename = file;
  runner.paths = Module._nodeModulePaths(path.dirname(file));
  runner._compile(program, file);
}
