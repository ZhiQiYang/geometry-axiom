'use strict';
// T-stage identity seam: the R360 regression must fail with ERR_ASSERTION,
// not with a missing module. P supplies the checked P1161-only projection.
const clone = value => JSON.parse(JSON.stringify(value));

function project(golden, plan) {
  return {golden: clone(golden), plan: clone(plan)};
}

module.exports = {project};
