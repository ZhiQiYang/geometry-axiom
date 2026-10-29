const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const ledger = require(process.env.IDENTITY_LEDGER_MODULE || path.join(__dirname, "..", "geometry-web", "identity-ledger.js"));
const store = require(path.join(__dirname, "..", "geometry-web", "project-store.js"));

test("延續保留記號", () => {
  assert.strictEqual(ledger.settleKey("aa:1", false, true, () => "bb:2"), "aa:1");
});

test("撤掉實作：沿用舊記號", () => {
  const mark = ledger.settleKey("aa:1", true, true, () => "bb:2");
  assert.notStrictEqual(mark, "aa:1");
  assert.strictEqual(mark, "bb:2");
});

test("新鍵得到記號", () => {
  assert.strictEqual(ledger.settleKey(null, false, true, () => "bb:2"), "bb:2");
});

test("不覆蓋回 null", () => {
  assert.strictEqual(ledger.settleKey("aa:1", true, false, () => "bb:2"), null);
});

test("比較狀態依 unknown、conflict、absent、replaced、continuous", () => {
  assert.strictEqual(ledger.compareStatus({continuous: true, unknown: true}), "unknown");
  assert.strictEqual(ledger.compareStatus({continuous: true, conflict: true, absent: true}), "conflict");
  assert.strictEqual(ledger.compareStatus({replaced: true, absent: true}), "absent");
  assert.strictEqual(ledger.compareStatus({continuous: true, replaced: true}), "replaced");
  assert.strictEqual(ledger.compareStatus({continuous: true}), "continuous");
  assert.strictEqual(ledger.compareStatus({}), "unknown");
});

test("撤掉實作：帳不完整仍沿用已保存", () => {
  const broken = store.restoreAfterProbe({dirty:false, dirtyReason:"", saved:true, downloaded:true}, false, null, "abc");
  assert.strictEqual(broken.saved, false);
  assert.strictEqual(broken.downloaded, false);
  assert.strictEqual(broken.dirty, true);
  assert.strictEqual(broken.dirtyReason, "身分帳不完整，須先復原上一步才能保存");
  const replaced = store.restoreAfterProbe({dirty:false, dirtyReason:"", saved:true, downloaded:true}, true, "new", "old");
  assert.strictEqual(replaced.saved, false);
  assert.strictEqual(replaced.dirtyReason, "有未保存的變更");
  const same = store.restoreAfterProbe({dirty:false, dirtyReason:"已保存", saved:true, downloaded:true}, true, "old", "old");
  assert.strictEqual(same.saved, true);
  assert.strictEqual(same.dirty, false);
  assert.strictEqual(same.dirtyReason, "已保存");
  const source = fs.readFileSync(path.join(__dirname, "..", "geometry-web", "project-store.js"), "utf8");
  assert.ok(source.includes("不得沿用已保存：帳不完整"));
});

test("去身分文字去掉記號行", () => {
  const source = "boundary 1 outline 0,0 10,0 10,10 0,10\r\nrequires identity-ledger/1\nidentity boundary 1 aa:1\nidentity-ledger activate\n# identity boundary 1 kept-comment\n";
  assert.strictEqual(store.stripIdentityLedger(source), "boundary 1 outline 0,0 10,0 10,10 0,10\n# identity boundary 1 kept-comment\n");
  assert.strictEqual(store.stripIdentityLedger("requires identity-ledger/1\n"), "\n".slice(0, 0) || "");
  const emptyActive = "requires identity-ledger/1\n";
  assert.strictEqual(store.stripIdentityLedger(emptyActive), "");
  const mixed = "requires engineering-spec/1\nrequires identity-ledger/1\nboundary 1 outline 0,0 1,0 1,1 0,1\nidentity boundary 1 aa:1\n";
  assert.strictEqual(store.stripIdentityLedger(mixed), "requires engineering-spec/1\nboundary 1 outline 0,0 1,0 1,1 0,1\n");
});

test("只有身分帳不升格式", () => {
  const scene = "requires identity-ledger/1\nboundary 1 outline 0,0 10,0 10,10 0,10\nidentity boundary 1 aa:1\n";
  assert.deepStrictEqual(store.sceneCapabilities(scene), ["identity-ledger/1"]);
  assert.throws(() => store.sceneCapabilities("requires future-native/1\n"), /尚未支援的工程能力/);
  assert.strictEqual(store.projectFormat({}, scene), store.FORMAT);
  assert.strictEqual(store.projectFormat({requiredCapabilities: ["identity-ledger/1"]}, ""), store.FORMAT);
  assert.strictEqual(store.projectFormat({}, "requires engineering-spec/1\n"), store.ENGINEERING_FORMAT);
  store.validateProjectCapabilities(["identity-ledger/1", store.ENGINEERING_CAPABILITY, store.PARAMETER_CAPABILITY, store.ASSEMBLY_CAPABILITY, store.GENERATION_CAPABILITY, store.SUBDIVISION_CAPABILITY, store.SECTION_CAPABILITY, store.CARD_CAPABILITY]);
  assert.throws(() => store.validateProjectCapabilities(["identity-ledger/1", "future-native/1"]), /尚未支援的工程能力/);
});

test("原生讀者保留身分能力", () => {
  assert.deepStrictEqual(store.nativeReaderCapabilities(["identity-ledger/1", "future-native/1"]), ["identity-ledger/1"]);
});

test("瀏覽器載入定義 IdentityLedger", () => {
  const sandbox = {console, TextEncoder, TextDecoder};
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "geometry-web", "identity-ledger.js"), "utf8"), sandbox, {filename: "identity-ledger.js"});
  assert.strictEqual(sandbox.module, undefined);
  assert.strictEqual(typeof sandbox.IdentityLedger, "object");
  assert.strictEqual(typeof sandbox.IdentityLedger.settleKey, "function");
});
