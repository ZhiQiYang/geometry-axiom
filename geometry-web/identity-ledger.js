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

  return {
    compareStatus,
    settleKey,
  };
});
