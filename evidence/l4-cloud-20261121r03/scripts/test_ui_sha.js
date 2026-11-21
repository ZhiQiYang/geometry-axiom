// 具名回歸 L4_GCANVAS_RAW_SHA256：ui.js 的 sha() 對 Buffer 必須雜湊原始位元組（與 crypto.update(Buffer) 相同），
// 對字串的結果不變。用法：node test_ui_sha.js [ui.js 路徑]；失敗時以 AssertionError 結束（exit 1）。
const assert = require('node:assert/strict'), crypto = require('node:crypto'), path = require('node:path');
const U = require(path.resolve(process.argv[2] || path.join(__dirname, 'ui.js')));
const raw = b => crypto.createHash('sha256').update(b).digest('hex');
const bytes = Buffer.from([0x50, 0x4b, 0x03, 0x04, 0xff, 0x80, 0x00, 0xc3, 0x28]);
assert.equal(U.sha(bytes), raw(bytes), 'L4_GCANVAS_RAW_SHA256: Buffer must hash raw bytes');
assert.equal(U.sha('abc'), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad', 'L4_GCANVAS_RAW_SHA256: text digest unchanged');
console.log('PASS L4_GCANVAS_RAW_SHA256');
