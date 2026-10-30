/* H: definition-import/1. The native preview is the authority for ids and closure.
   This file mirrors allocation only so tests can name the fresh-id mutation. */
(function (root) {
  "use strict";

  function allocateImportedId(used, sourceId) {
    void sourceId;
    let max = 0;
    for (const id of used) {
      const value = id >>> 0;
      if (value > max) max = value;
    }
    let candidate = (max + 1) >>> 0;
    for (let attempt = 0; attempt <= used.size + 1; attempt++) {
      if (candidate === 0) candidate = 1;
      if (!used.has(candidate)) {
        used.add(candidate);
        return candidate; /* DI-FRESH-ID */
      }
      candidate = (candidate + 1) >>> 0;
    }
    return null;
  }

  function allocateCardId(used) {
    let cursor = 0;
    while (used.has(cursor)) cursor += 1;
    used.add(cursor);
    return cursor;
  }

  function specNameValid(name) {
    if (typeof name !== "string" || name.length === 0) return false;
    const bytes = new TextEncoder().encode(name);
    if (bytes.length === 0 || bytes.length >= 96) return false;
    for (const byte of bytes) {
      if (byte < 128 && !/[A-Za-z0-9_]/.test(String.fromCharCode(byte))) return false;
    }
    return true;
  }

  function rootsSchema(roots) {
    if (!roots || typeof roots !== "object" || Array.isArray(roots)) {
      return { ok: false, code: "UNSUPPORTED", error: "組構實例：首版不支援" };
    }
    const keys = Object.keys(roots);
    if (keys.some(key => key !== "rules" && key !== "bindings")) {
      return { ok: false, code: "UNSUPPORTED", error: "組構實例：首版不支援" };
    }
    if (!Array.isArray(roots.rules) || !Array.isArray(roots.bindings)) {
      return { ok: false, code: "SCHEMA", error: "匯入根必須包含規則與配置陣列" };
    }
    if (roots.rules.length === 0 && roots.bindings.length === 0) {
      return { ok: false, code: "SCHEMA", error: "匯入根不得是空的" };
    }
    return { ok: true };
  }

  root.DefinitionImport = { allocateImportedId, allocateCardId, specNameValid, rootsSchema };
  if (typeof document === "undefined") return;

  const $ = id => document.getElementById(id);
  const runtimeVersion = () => document.querySelector('meta[name="geometry-runtime-version"]')?.content || "";
  let entryEnabled = null;
  let sessionToken = null;
  let sceneText = "";
  let sceneHash = "";
  let definitions = null;
  let token = null;
  let lastMap = null;
  let busy = false;

  function sameProject() {
    return ReferenceWorkspace.getProjectState().contextToken === sessionToken;
  }
  function setLine(text) {
    const node = $("definitionImportStatus");
    if (node) node.textContent = text;
    if (typeof setStatus === "function") setStatus(text);
  }
  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }
  function add(parent, tag, text) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    parent.appendChild(node);
    return node;
  }
  async function refreshEntry() {
    try {
      const state = await apiRead();
      entryEnabled = !!(state && state.ok && Array.isArray(state.state?.capabilities) && state.state.capabilities.includes("definition-import/1"));
    } catch (_) {
      entryEnabled = null;
    }
  }
  function apiRead() {
    return api("engineering-read");
  }
  function walkSpecs(node, names) {
    if (!node || typeof node !== "object") return;
    if (node.kind === "spec" && typeof node.name === "string") names.add(node.name);
    for (const value of Object.values(node)) walkSpecs(value, names);
  }
  function selectedRoots() {
    const rules = [...document.querySelectorAll("#definitionImportRules input:checked")].map(input => {
      const [id, version] = input.value.split(":");
      return { id: Number(id), version: Number(version) };
    });
    const bindings = [...document.querySelectorAll("#definitionImportBindings input:checked")].map(input => Number(input.value));
    return { rules, bindings };
  }
  function collidingNames(targetSpecs) {
    const selected = new Set(selectedRoots().bindings.map(String));
    const referenced = new Set();
    for (const binding of definitions?.bindings || []) {
      if (!selected.has(String(binding.id))) continue;
      walkSpecs(binding.content, referenced);
    }
    const known = new Set((targetSpecs || []).map(spec => spec.name));
    return [...referenced].filter(name => known.has(name));
  }
  function syncNameRows(names) {
    const host = $("definitionImportNames");
    const keep = new Set(names);
    for (const row of [...host.querySelectorAll("[data-di-row]")]) {
      if (!keep.has(row.dataset.diRow)) row.remove();
    }
    for (const name of names) {
      if (host.querySelector(`[data-di-row="${CSS.escape(name)}"]`)) continue;
      const row = add(host, "fieldset");
      row.dataset.diRow = name;
      add(row, "legend", name);
      const rename = add(row, "label", "重新命名");
      const renameInput = document.createElement("input");
      renameInput.type = "radio";
      renameInput.name = "di-name-" + name;
      renameInput.dataset.diMode = "rename";
      renameInput.dataset.diSpec = name;
      rename.prepend(renameInput);
      const fresh = document.createElement("input");
      fresh.type = "text";
      fresh.maxLength = 95;
      fresh.dataset.diRename = name;
      fresh.setAttribute("aria-label", name + " 的新名稱");
      row.appendChild(fresh);
      const mapped = add(row, "label", "沿用既有名稱");
      const mappedInput = document.createElement("input");
      mappedInput.type = "radio";
      mappedInput.name = "di-name-" + name;
      mappedInput.dataset.diMode = "map-existing";
      mappedInput.dataset.diSpec = name;
      mapped.prepend(mappedInput);
    }
  }
  function nameChoices() {
    const names = {};
    for (const row of document.querySelectorAll("#definitionImportNames [data-di-row]")) {
      const name = row.dataset.diRow;
      const mode = row.querySelector("input[type=radio]:checked")?.dataset.diMode;
      if (mode === "rename") names[name] = { mode: "rename", name: row.querySelector("[data-di-rename]").value };
      else if (mode === "map-existing") names[name] = { mode: "map-existing" };
    }
    return names;
  }
  function renderLists() {
    const rules = $("definitionImportRules");
    const bindings = $("definitionImportBindings");
    clear(rules);
    clear(bindings);
    add(rules, "p", "規則");
    for (const rule of definitions.rules || []) {
      const label = add(rules, "label", ` ${rule.id}@${rule.version} ${rule.name || ""}`);
      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = rule.id + ":" + rule.version;
      input.dataset.diRule = input.value;
      label.prepend(input);
    }
    add(bindings, "p", "配置");
    for (const binding of definitions.bindings || []) {
      const label = add(bindings, "label", ` ${binding.id} ${binding.name || ""}`);
      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = String(binding.id);
      input.dataset.diBinding = String(binding.id);
      label.prepend(input);
    }
  }
  function renderMap(preview) {
    const host = $("definitionImportMap");
    clear(host);
    const closure = $("definitionImportClosure");
    clear(closure);
    const map = preview.map;
    if (!map) {
      add(closure, "p", "這次預覽沒有閉包。");
      return;
    }
    add(closure, "p", "閉包");
    const list = add(closure, "ul");
    for (const row of map.rules || []) add(list, "li", `規則 ${row.from.id}@${row.from.version} → ${row.to.id}@${row.to.version}`);
    for (const row of map.bindings || []) add(list, "li", `配置 ${row.from} → ${row.to}`);
    for (const row of map.parameters || []) add(list, "li", `參數 ${row.from} → ${row.to}`);
    for (const row of map.specs || []) add(list, "li", `規格 ${row.from} → ${row.to}（${row.action}）`);
    for (const row of map.materials || []) add(list, "li", `材料 ${row.id}@${row.version} ${row.action}`);
    const table = add(host, "table");
    for (const binding of preview.bindings || []) {
      for (const slot of binding.slots || []) {
        const line = add(table, "tr");
        add(line, "td", `配置 ${binding.id} 槽 ${slot.slotId}`);
        add(line, "td", slot.A && slot.A.effective !== undefined && slot.A.effective !== null ? String(slot.A.effective) : "未完成");
        add(line, "td", slot.B && slot.B.effective !== undefined && slot.B.effective !== null ? String(slot.B.effective) : "未完成");
      }
    }
  }
  function noteText(preview) {
    const rows = [...(preview.conflicts || []), ...(preview.diagnostics || [])];
    return rows.map(row => `${row.code || ""} ${row.name || ""} ${row.message || ""}`.trim()).join("；");
  }
  function importedCount(map) {
    if (!map) return 0;
    const rules = new Set((map.rules || []).filter(row => row.action === "create").map(row => row.to.id)).size;
    return rules
      + (map.bindings || []).filter(row => row.action === "create").length
      + (map.parameters || []).filter(row => row.action === "create").length
      + (map.specs || []).filter(row => row.action === "create" || row.action === "rename").length
      + (map.materials || []).filter(row => row.action === "create").length;
  }
  async function placeNew(map) {
    const occupied = ocAllObjects().filter(item => item.hasPos).map(cardBox);
    const seen = new Set();
    const jobs = [];
    for (const row of map.rules || []) {
      if (row.action !== "create" || seen.has(row.to.id)) continue;
      seen.add(row.to.id);
      jobs.push(["assembly-rule", row.to.id]);
    }
    for (const row of map.bindings || []) if (row.action === "create") jobs.push(["assembly-binding", row.to]);
    for (const row of map.parameters || []) if (row.action === "create") jobs.push(["parameter", row.to]);
    for (const [kind, id] of jobs) {
      if (!sameProject()) return;
      const [x, y] = nextCardPosition({ kind }, occupied);
      const placed = await api(`line canvas-pos ${kind} ${id} ${x} ${y}`);
      if (!placed.ok) return;
    }
  }
  async function cancelToken() {
    if (!token) return true;
    const current = token;
    const result = await api("definition-import-cancel " + current);
    if (result.transport) {
      setLine(result.error || "取消結果尚未確認。");
      return false;
    }
    token = null;
    lastMap = null;
    $("definitionImportConfirm").disabled = true;
    return result.ok !== false;
  }
  async function closeDialog() {
    if (busy) return;
    busy = true;
    try { await cancelToken(); }
    finally { busy = false; $("definitionImportDialog").close(); }
  }
  async function openFile(file) {
    if (busy) return;
    busy = true;
    try {
      sessionToken = ReferenceWorkspace.getProjectState().contextToken;
      const bytes = new Uint8Array(await file.arrayBuffer());
      const opened = await GeometryProject.readForImport(bytes, fflate);
      if (!sameProject()) return;
      sceneText = opened.scene;
      const encoded = new TextEncoder().encode(sceneText);
      const response = await fetch("/definition-import/read", {
        method: "POST",
        headers: { "Content-Type": "text/plain;charset=UTF-8", "X-Geometry-Version": runtimeVersion() },
        body: encoded
      });
      const catalog = await response.json();
      if (!sameProject()) return;
      if (!catalog.ok) { setLine(catalog.error || "無法讀取匯入來源。"); return; }
      if (!Array.isArray(catalog.capabilities) || !catalog.capabilities.includes("definition-import/1")) {
        setLine("這個執行器沒有 definition-import/1。");
        return;
      }
      sceneHash = catalog.scene_sha256;
      definitions = catalog.definitions;
      token = null;
      lastMap = null;
      $("definitionImportSource").textContent = file.name;
      renderLists();
      clear($("definitionImportNames"));
      clear($("definitionImportClosure"));
      add($("definitionImportClosure"), "p", "預覽後顯示閉包。");
      clear($("definitionImportMap"));
      $("definitionImportConfirm").disabled = true;
      $("definitionImportCancel").disabled = true;
      setLine("選擇要匯入的規則或配置。");
      $("definitionImportDialog").showModal();
    } catch (error) {
      setLine(error.message || "無法讀取專案。");
    } finally {
      busy = false;
    }
  }
  async function previewImport() {
    if (busy || !definitions || !sameProject()) return;
    busy = true;
    try {
      const state = await apiRead();
      if (!state.ok || !state.state?.capabilities?.includes("definition-import/1")) {
        setLine("這個執行器沒有 definition-import/1。");
        return;
      }
      syncNameRows(collidingNames(state.state.specs || []));
      if (!(await cancelToken())) return;
      const response = await fetch("/definition-import/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Geometry-Version": runtimeVersion() },
        body: JSON.stringify({
          schema: "definition-import/1",
          expectedRevision: state.revision,
          sourceSceneSha256: sceneHash,
          sourceScene: sceneText,
          roots: selectedRoots(),
          names: nameChoices()
        })
      });
      const result = await response.json();
      if (!sameProject()) { if (result.preview?.token) await api("definition-import-cancel " + result.preview.token); return; }
      if (!result.ok) { setLine(result.error || "預覽沒有建立。"); return; }
      const preview = result.preview || {};
      renderMap(preview);
      const notes = noteText(preview);
      if (preview.valid && preview.token) {
        token = preview.token;
        lastMap = preview.map;
        $("definitionImportConfirm").disabled = false;
        $("definitionImportCancel").disabled = false;
        setLine(notes || "預覽可以確認。");
      } else {
        token = null;
        lastMap = null;
        $("definitionImportConfirm").disabled = true;
        $("definitionImportCancel").disabled = true;
        for (const row of preview.diagnostics || []) {
          if (row.code === "IMPORT_RENAME_REQUIRED" && row.name) syncNameRows([...new Set([...collidingNames(state.state.specs || []), row.name])]);
        }
        setLine(notes || result.error || "預覽未通過。");
      }
    } catch (error) {
      setLine(error.message || "預覽沒有完成。");
    } finally {
      busy = false;
    }
  }
  async function confirmImport() {
    if (busy || !token || !sameProject()) return;
    busy = true;
    const map = lastMap;
    const current = token;
    try {
      const result = await api("definition-import-confirm " + current);
      if (result.transport) { setLine(result.error || "匯入結果尚未確認。"); return; }
      token = null;
      lastMap = null;
      $("definitionImportConfirm").disabled = true;
      if (!sameProject()) return;
      if (!result.ok) { setLine(result.error || "匯入沒有寫入。"); return; }
      await renderObjects();
      if (map) await placeNew(map);
      setLine(`已匯入 ${importedCount(map)} 項，可復原`);
      $("definitionImportDialog").close();
    } finally {
      busy = false;
    }
  }

  $("fileMenuBtn")?.addEventListener("click", () => { void refreshEntry(); });
  $("btnDefinitionImport")?.addEventListener("click", () => {
    if (entryEnabled === false) { setLine("這個執行器沒有 definition-import/1。"); return; }
    $("definitionImportFile").click();
  });
  $("definitionImportFile")?.addEventListener("change", () => {
    const file = $("definitionImportFile").files && $("definitionImportFile").files[0];
    $("definitionImportFile").value = "";
    if (file) void openFile(file);
  });
  $("definitionImportPreview")?.addEventListener("click", () => { void previewImport(); });
  $("definitionImportConfirm")?.addEventListener("click", () => { void confirmImport(); });
  $("definitionImportCancel")?.addEventListener("click", () => { void cancelToken().then(ok => { if (ok) setLine("已取消預覽。"); }); });
  $("definitionImportClose")?.addEventListener("click", () => { void closeDialog(); });
  $("definitionImportDialog")?.addEventListener("cancel", event => { event.preventDefault(); void closeDialog(); });
  $("definitionImportRules")?.addEventListener("change", () => { void cancelToken(); });
  $("definitionImportBindings")?.addEventListener("change", () => { void cancelToken(); });
})(typeof globalThis !== "undefined" ? globalThis : this);
