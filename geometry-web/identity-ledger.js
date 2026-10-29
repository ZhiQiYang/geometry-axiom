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

  function prefillRoots(roots) {
    return (Array.isArray(roots) ? roots : []).filter(item => item && item.status === "continuous" && !item.assemblyOwned)
      .map(item => ({...item, confirmed: false}));
  }

  function planFaces(oldUses, newUses, extras) {
    const extra = extras || {};
    if (extra.timbers || extra.assemblyOwned) {
      return {ok: false, code: "UNSUPPORTED", error: "faces＋timbers 與 assembly-owned 首版不支援"};
    }
    if (!Array.isArray(oldUses) || !Array.isArray(newUses) || oldUses.length !== newUses.length) {
      return {ok: false, code: "REJECTED", error: "faces 更新只能沿用原本的數量、順序、orientation 與 purpose"};
    }
    return {
      ok: true,
      uses: newUses.map((use, index) => ({
        ...use,
        orientation: oldUses[index] ? oldUses[index].orientation : undefined,
        purpose: oldUses[index] ? oldUses[index].purpose : undefined,
      })),
    };
  }

  function settleKey(beforeMark, explicitDelete, stillCovered, allocate) {
    if (!stillCovered) return null;
    if (explicitDelete || beforeMark == null) {
      return allocate(); /* 不得沿用舊記號 */
    }
    return beforeMark;
  }

  function stripIdentityLedger(text) {
    const normalized = String(text == null ? "" : text).replace(/\r\n/g, "\n");
    const trailing = normalized.endsWith("\n");
    const body = trailing ? normalized.slice(0, -1) : normalized;
    const kept = body.split("\n").filter(line => {
      const code = line.split("#")[0].trim();
      if (code === "requires identity-ledger/1" || code === "identity-ledger activate") return false;
      if (code.startsWith("identity ")) return false;
      return true;
    });
    const joined = kept.join("\n");
    return trailing ? joined + "\n" : joined;
  }

  return {
    compareStatus,
    prefillRoots,
    planFaces,
    facesUpdate: planFaces,
    settleKey,
    stripIdentityLedger,
  };
});
