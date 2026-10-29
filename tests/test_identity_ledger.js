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

test("只預填 continuous 且不確認", () => {
  let confirmed = false;
  const roots = ledger.prefillRoots([
    {id: 1, status: "continuous", confirm() { confirmed = true; }},
    {id: 2, status: "replaced"},
    {id: 3, status: "continuous", assemblyOwned: true},
    {id: 4, status: "unknown"},
  ]);
  assert.strictEqual(confirmed, false);
  assert.deepStrictEqual(roots.map(root => root.id), [1]);
  assert.strictEqual(roots[0].confirmed, false);
});

test("faces 沿用 orientation 與 purpose", () => {
  const planned = ledger.planFaces(
    [{id: 1, orientation: "+n", purpose: "finish"}, {id: 2, orientation: "-n", purpose: "base"}],
    [{id: 9, orientation: "changed", purpose: "changed"}, {id: 8, orientation: "changed", purpose: "changed"}]
  );
  assert.strictEqual(planned.ok, true);
  assert.deepStrictEqual(planned.uses.map(use => [use.id, use.orientation, use.purpose]), [[9, "+n", "finish"], [8, "-n", "base"]]);
});

test("faces 數量不同就拒絕", () => {
  const planned = ledger.planFaces([{orientation: "+n", purpose: "finish"}], []);
  assert.strictEqual(planned.ok, false);
  assert.match(planned.error, /數量、順序、orientation 與 purpose/);
});

test("faces 加 timbers 不支援", () => {
  const planned = ledger.facesUpdate([{orientation: "+n", purpose: "finish"}], [{orientation: "+n", purpose: "finish"}], {timbers: true});
  assert.strictEqual(planned.ok, false);
  assert.strictEqual(planned.code, "UNSUPPORTED");
  assert.match(planned.error, /assembly-owned/);
  const owned = ledger.planFaces([{orientation: "+n", purpose: "finish"}], [{orientation: "+n", purpose: "finish"}], {assemblyOwned: true});
  assert.strictEqual(owned.ok, false);
});

test("去身分文字去掉記號行", () => {
  const source = "boundary 1 outline 0,0 10,0 10,10 0,10\r\nrequires identity-ledger/1\nidentity boundary 1 aa:1\nidentity-ledger activate\n# identity boundary 1 kept-comment\n";
  assert.strictEqual(ledger.stripIdentityLedger(source), "boundary 1 outline 0,0 10,0 10,10 0,10\n# identity boundary 1 kept-comment\n");
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
