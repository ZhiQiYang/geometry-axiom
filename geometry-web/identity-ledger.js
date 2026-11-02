(function (root, factory) {
  const ledger = factory();
  if (typeof module === "object" && module.exports) module.exports = ledger;
  else root.IdentityLedger = ledger;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const ORDER = ["unknown", "conflict", "absent", "replaced", "continuous"];

  function compareStatus(checks) {
    for (const status of ORDER) if (checks && checks[status]) return status;
    return "unknown";
  }

  function settleKey(beforeMark, explicitDelete, stillCovered, allocate) {
    if (!stillCovered) return null;
    if (explicitDelete || beforeMark == null) {
      return allocate(); /* 不得沿用舊記號 */
    }
    return beforeMark;
  }

  const SCHEMA = "model-source-identity/1";
  const MARK = /^[a-f0-9]{32}:[1-9][0-9]*$/;
  const STATUSES = ["unknown", "conflict", "absent", "replaced", "continuous"];
  const fail = (code, message) => { throw Object.assign(new Error(message), {code}); };
  const copy = value => JSON.parse(JSON.stringify(value));
  const liveKey = root => root.kind + ":" + root.id;

  function deidentifiedBase(scene) {
    /* 去身分基準 */
    const normalized = String(scene == null ? "" : scene).replace(/\r\n/g, "\n");
    const trailing = normalized.endsWith("\n");
    const body = trailing ? normalized.slice(0, -1) : normalized;
    const kept = body.split("\n").filter(line => {
      const code = line.split("#")[0].trim();
      if (code === "requires identity-ledger/1" || code === "identity-ledger activate") return false;
      if (code.startsWith("identity ")) return false;
      return true;
    });
    if (!kept.length) return "";
    const joined = kept.join("\n");
    return trailing ? joined + "\n" : joined;
  }

  function rootValid(root) {
    if (!root || typeof root !== "object" || Array.isArray(root)) return false;
    const keys = Object.keys(root);
    const allowed = ["role", "kind", "id", "incarnation", "fieldId", "uncovered", "status", "definitionPin", "decision", "confirmed"];
    if (!keys.every(key => allowed.includes(key)) || !["placement", "boundary", "timber", "obstacle", "use"].includes(root.role)) return false;
    if (typeof root.kind !== "string" || !Number.isSafeInteger(root.id) || root.id < 0) return false;
    const uncovered = Object.hasOwn(root, "uncovered");
    if (uncovered) {
      if (root.uncovered !== "assembly-owned" || root.kind !== "timber" || root.incarnation !== null) return false;
    } else if (typeof root.incarnation !== "string" || !MARK.test(root.incarnation)) return false;
    if (Object.hasOwn(root, "fieldId") && (!Number.isSafeInteger(root.fieldId) || root.fieldId < 0)) return false;
    if (Object.hasOwn(root, "status") && !STATUSES.includes(root.status)) return false;
    return true;
  }

  function expectedRoots(input) {
    if (!input || (input.mode !== "plan" && input.mode !== "faces")) fail("MODEL_IDENTITY", "模型輸入沒有可引用的根。");
    const hasTimbers = Array.isArray(input.timbers) ? input.timbers.length > 0 : !!input.timbers;
    if (input.mode === "faces" && (hasTimbers || input.assemblyOwned)) {
      return {ok: false, code: "UNSUPPORTED", error: "faces＋timbers 與 assembly-owned 首版不支援"};
    }
    const roots = [];
    if (input.mode === "plan") {
      roots.push({role: "placement", kind: "placement", id: input.placement_id});
      if (input.boundary_id > 0) roots.push({role: "boundary", kind: "boundary", id: input.boundary_id});
      for (const timber of input.timbers || []) roots.push({role: "timber", kind: "timber", id: timber.id});
    } else {
      for (const use of input.uses || []) roots.push({role: "use", kind: "placement", id: use.placement_id});
    }
    for (const obstacle of input.obstacles || []) roots.push({role: "obstacle", kind: obstacle.kind, id: obstacle.id});
    return {ok: true, roots};
  }

  function sameRoot(a, b) {
    return a.role === b.role && a.kind === b.kind && a.id === b.id && (a.fieldId || 0) === (b.fieldId || 0);
  }

  function validateSourceIdentity(identity, input) {
    if (!identity || identity.schema !== SCHEMA || !Array.isArray(identity.roots)) fail("MODEL_IDENTITY", "模型來源身分不合法。");
    const expected = expectedRoots(input);
    if (!expected.ok) fail(expected.code, expected.error);
    if (identity.roots.length !== expected.roots.length || identity.roots.some(root => !rootValid(root))) fail("MODEL_IDENTITY", "模型來源身分的根不合法。");
    const used = new Set();
    for (const want of expected.roots) {
      const found = identity.roots.findIndex((root, index) => !used.has(index) && sameRoot(root, want));
      if (found < 0) fail("MODEL_IDENTITY", "模型來源身分與紀錄的根集合不一致。");
      used.add(found);
    }
    return true;
  }

  function liveOf(live, root) {
    if (!live) return null;
    if (typeof live.get === "function") return live.get(liveKey(root)) || null;
    return live[liveKey(root)] || null;
  }

  function judgeRoots(identity, live) {
    const roots = identity?.roots || [];
    return roots.map(root => {
      const savedId = root.id;
      if (!rootValid(root) || root.incarnation == null || root.uncovered) {
        return {...copy(root), id: savedId, status: "unknown", confirmed: false};
      }
      const node = liveOf(live, root);
      let status = "absent";
      if (node?.conflict === true) status = "conflict";
      else if (node && node.incarnation == null) status = "unknown";
      else if (node && node.incarnation === root.incarnation) status = "continuous";
      else if (node) status = "replaced";
      const livePin = node?.definitionFingerprint || node?.definitionPin || null;
      return {...copy(root), id: savedId, status, definitionPin: livePin, previousDefinitionPin: root.definitionPin ?? null, confirmed: false};
    });
  }

  function prefillRoots(roots) {
    return (Array.isArray(roots) ? roots : []).filter(item => item && item.status === "continuous" && item.incarnation && !item.uncovered) /* 只預填延續 */
      .map(item => ({...item, id: item.id, confirmed: false}));
  }

  function edgesPrefill(boundaryStatus, pinsEqual, edges) {
    if (boundaryStatus !== "continuous" || pinsEqual !== true) return []; /* 指紋變不預填邊 */
    return Array.isArray(edges) ? edges.slice() : [];
  }

  function previewAllowed(roots) {
    return !(Array.isArray(roots) ? roots : []).some(root =>
      ["absent", "replaced", "conflict"].includes(root?.status) && root.decision !== "retarget" && root.decision !== "remove");
  }

  function confirmIdentity(reviewed, live) {
    /* 確認時重比 */
    if (!Array.isArray(reviewed) || !Array.isArray(live) || reviewed.length !== live.length) return {ok: false, code: "STALE"};
    for (let i = 0; i < reviewed.length; i += 1) {
      if (reviewed[i].status !== live[i].status || reviewed[i].incarnation !== live[i].incarnation || reviewed[i].id !== live[i].id) return {ok: false, code: "STALE"};
    }
    return {ok: true};
  }

  function planFaces(oldUses, newUses, extras) {
    const extra = extras || {};
    const hasTimbers = Array.isArray(extra.timbers) ? extra.timbers.length > 0 : !!extra.timbers;
    if (hasTimbers || extra.assemblyOwned) return {ok: false, code: "UNSUPPORTED", error: "faces＋timbers 與 assembly-owned 首版不支援"};
    if (!Array.isArray(oldUses) || !Array.isArray(newUses) || oldUses.length !== newUses.length) {
      return {ok: false, code: "REJECTED", error: "faces 更新只能沿用原本的數量、順序、orientation 與 purpose"};
    }
    if (new Set(newUses.map(use => use && use.placement_id)).size !== newUses.length) {
      return {ok: false, code: "REJECTED", error: "faces 更新不能重複同一放置面"};
    }
    return {ok: true, uses: newUses.map((use, index) => ({...use, orientation: oldUses[index].orientation, purpose: oldUses[index].purpose}))};
  }

  function continuitySummary(identity) {
    // Stored roots have no live status. Only an explicit status is a verdict.
    if (!identity?.roots?.length) return {token: "unknown", text: "物件延續性未知", listed: []};
    const statuses = identity.roots.map(root => root.status || "unknown");
    if (statuses.some(status => status === "unknown")) return {token: "unknown", text: "物件延續性未知", listed: []};
    if (statuses.some(status => ["absent", "replaced", "conflict"].includes(status))) {
      const listed = identity.roots.filter(root => ["absent", "replaced", "conflict"].includes(root.status)).map(root => root.kind + " #" + root.id);
      return {token: "partial", text: "部分來源物件已不存在或已刪除重建", listed};
    }
    if (statuses.every(status => status === "continuous")) return {token: "proved", text: "物件延續已證明", listed: []};
    return {token: "unknown", text: "物件延續性未知", listed: []};
  }

  function buildSourceIdentity(input, live) {
    const expected = expectedRoots(input);
    if (!expected.ok) fail(expected.code, expected.error);
    const roots = expected.roots.map(root => {
      const node = liveOf(live, root);
      if (!node || node.incarnation == null) {
        if (root.kind === "timber") fail("UNSUPPORTED", "faces＋timbers 與 assembly-owned 首版不支援");
        fail("MODEL_IDENTITY", "這個根沒有存在期記號，不能寫入來源身分。");
      }
      if (typeof node.incarnation !== "string" || !MARK.test(node.incarnation)) fail("MODEL_IDENTITY", "存在期記號不合法。");
      const definitionPin = node.definitionFingerprint || node.definitionPin || null;
      return {...root, incarnation: node.incarnation, ...(definitionPin ? {definitionPin} : {})};
    });
    const identity = {schema: SCHEMA, roots};
    validateSourceIdentity(identity, input);
    return identity;
  }

  return {
    compareStatus,
    settleKey,
    SCHEMA,
    deidentifiedBase,
    expectedRoots,
    validateSourceIdentity,
    judgeRoots,
    prefillRoots,
    edgesPrefill,
    previewAllowed,
    confirmIdentity,
    planFaces,
    facesUpdate: planFaces,
    continuitySummary,
    buildSourceIdentity,
  };
});
