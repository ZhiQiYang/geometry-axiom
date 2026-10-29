"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const sourcePath = process.env.GEOMETRY_DEFINITION_IMPORT_SOURCE
  || path.join(__dirname, "..", "geometry-web", "definition-import.js");
const context = { console, TextEncoder, Uint8Array, Set, Object, Array };
context.globalThis = context;
vm.createContext(context);
vm.runInContext(fs.readFileSync(sourcePath, "utf8"), context);
const DefinitionImport = context.DefinitionImport;

test("撤掉實作：撞號仍沿用來源號碼", () => {
  const used = new Set([1, 2]);
  const fresh = DefinitionImport.allocateImportedId(used, 1);
  assert.notStrictEqual(fresh, 1);
  assert.strictEqual(fresh, 3);
  assert.equal(used.has(3), true);
});

test("empty used set starts at 1", () => {
  const used = new Set();
  assert.strictEqual(DefinitionImport.allocateImportedId(used, 7), 1);
});

test("skip zero and ids already assigned", () => {
  const used = new Set([0, 1]);
  assert.strictEqual(DefinitionImport.allocateImportedId(used, 0), 2);
});

test("uint32 wrap skips zero and used ids", () => {
  const used = new Set([1, 4294967295]);
  assert.strictEqual(DefinitionImport.allocateImportedId(used, 4294967295), 2);
});

test("parameter cards use the import walk from zero", () => {
  const used = new Set();
  assert.strictEqual(DefinitionImport.allocateCardId(used), 0);
  assert.strictEqual(DefinitionImport.allocateCardId(used), 1);
  assert.strictEqual(DefinitionImport.allocateCardId(new Set([0, 1])), 2);
});

test("spec names reject ascii hyphen and accept chinese", () => {
  assert.equal(DefinitionImport.specNameValid("柱寬"), true);
  assert.equal(DefinitionImport.specNameValid("柱寬匯入"), true);
  assert.equal(DefinitionImport.specNameValid("A_1"), true);
  assert.equal(DefinitionImport.specNameValid("柱寬-匯入"), false);
  assert.equal(DefinitionImport.specNameValid(""), false);
});

test("empty roots and unlisted identities stay outside the import", () => {
  assert.equal(DefinitionImport.rootsSchema({ rules: [], bindings: [] }).ok, false);
  assert.equal(DefinitionImport.rootsSchema({ rules: [], bindings: [] }).code, "SCHEMA");
  assert.equal(DefinitionImport.rootsSchema({ rules: [], bindings: [], instances: [1] }).code, "UNSUPPORTED");
  assert.equal(DefinitionImport.rootsSchema({ rules: [{ id: 1, version: 1 }], bindings: [] }).ok, true);
});
