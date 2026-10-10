/* Fixed assertion census, independently inventoried from the existing checks
 * and loop cardinalities; see docs/SPACE-GROUP-VALIDATION.md. Never learned from
 * a run. Optional timber groups remain outside the default full space suite. */
'use strict';
const FULL_SPACE_GROUPS = Object.freeze(['space-height-library', 'projection-lifecycle', 'projection-placement', 'font-layout', 'space-flow']);
const EXPECTED = Object.freeze({
  setup: 2,
  'space-height-library': 112,
  'projection-lifecycle': 18,
  'projection-placement': 36,
  'font-layout': 19,
  'space-flow': 39,
  'timber-material': 48,
  'timber-source-guards': 8,
  'timber-history-guard': 5,
  'async-reply-ui': 8,
  'save-reopen-grid': 20,
  'browser-health': 2,
});

function createGroupCensus(included) {
  const selected = ['setup', ...included, 'browser-health'];
  if (new Set(selected).size !== selected.length || selected.some(name => !Object.hasOwn(EXPECTED, name))) throw Error('Invalid space census scope');
  const groups = Object.fromEntries(selected.map(name => [name, {expected: EXPECTED[name], passed: 0, failed: 0, completed: false}]));
  const started = new Set();
  let current = null;
  return {
    async run(name, action) {
      if (current || !Object.hasOwn(groups, name) || started.has(name)) throw Error('Unexpected or duplicate space group: ' + name);
      started.add(name);
      current = name;
      try {
        await action();
        const group = groups[name];
        group.completed = group.passed === group.expected && group.failed === 0;
      }
      finally { current = null; }
    },
    record(ok) {
      // Fatal/completeness diagnostics retain their existing global fail count.
      if (current) groups[current][ok ? 'passed' : 'failed']++;
      return current;
    },
    report(runFinished) {
      const problems = [];
      if (!runFinished) problems.push('Space run did not finish');
      for (const [name, group] of Object.entries(groups)) {
        if (!group.completed) problems.push('Group ' + name + ' did not complete');
        if (group.passed !== group.expected || group.failed) problems.push('Group ' + name + ': expected ' + group.expected + ' passed assertions, got ' + group.passed + ' passed / ' + group.failed + ' failed');
      }
      return {completed: problems.length === 0, groups: structuredClone(groups), completenessProblems: problems};
    },
  };
}
module.exports = {EXPECTED, FULL_SPACE_GROUPS, createGroupCensus};
