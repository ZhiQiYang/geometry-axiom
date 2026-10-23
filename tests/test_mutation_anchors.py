"""Every standalone mutation tool's anchors occur exactly once in this checkout.

The acceptance tools below patch real sources with exact text and are run by hand
or in their own CI receipts, not by run_all. When a refactor moves the anchored
text, the tool only fails at its next manual run (GEO-261: the Q38 gate and the
card-reference table drifted unnoticed). This suite reads each tool's own table
and applies its patches in the tool's order to the LF form of the sources (the
form every tool runs on in WSL). mutate.py is judged by its own definition_kind(),
so a retired mutant whose old text reappears is also a problem. The last test
removes one live anchor per tool and requires each check to report it.

KNOWN_DRIFT is empty: the five anchors that had already drifted when this suite was
added (2026-10-20, GEO-261 K/W/H moves) were re-anchored, each with its tool's own
WSL receipt (the per-tool tables are in ASSEMBLY-RULES-VALIDATION.md, PF3-NATIVE.md
and FRONTEND-F1.md). It stays as a ratchet, not an allowance: the found set must
equal it exactly, so a new drift and a repaired one both fail until the list is
edited. Re-anchoring needs the tool's own WSL receipt, as Q38 had. A present anchor
does not prove the mutation still bites (cancelled-preview survived the move with
its anchor intact), so the receipt, not this suite, is what proves a case is killed.
"""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'tests'
for directory in (ROOT, HERE):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

MISSING = '\x00anchor removed by test_mutation_anchors\x00'
KNOWN_DRIFT = set()


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Sources:
    """LF text of checkout files, read once."""

    def __init__(self):
        self.cache = {}

    def text(self, relative):
        if relative not in self.cache:
            path = ROOT / relative
            self.cache[relative] = path.read_bytes().replace(b'\r\n', b'\n').decode('utf-8') if path.is_file() else None
        return self.cache[relative]


def apply_in_order(tool, entries, sources):
    """entries: (identifier, [(relative path, old, new), ...]); each old must occur once when its turn comes.

    Returns {(tool, identifier): message} for every entry with a problem."""
    problems = {}
    for identifier, patches in entries:
        current = {}
        for relative, old, new in patches:
            text = current.get(relative, sources.text(relative))
            if text is None:
                problems[(tool, identifier)] = '%s does not exist' % relative
                break
            count = text.count(old)
            if count != 1:
                problems[(tool, identifier)] = 'anchor occurs %d times in %s: %r' % (count, relative, old[:80])
                break
            current[relative] = text.replace(old, new, 1)
    return problems


def q38_entries(module):
    return [(case['id'], [tuple(patch) for patch in case['patches']]) for case in module.CASES]


def assembly_entries(module):
    # Cases and negative controls alike: a control whose anchor drifted would stop being a control.
    return [(entry[0], [tuple(patch) for patch in entry[1]]) for entry in module.CASES + module.CONTROLS]


def pf3_entries(module):
    return [(case[0], [tuple(change) for change in case[1]]) for case in module.CASES]


def frontend_entries(module):
    return [(name, [(relative, before, after)]) for name, _, relative, before, after, _ in module.MUTATIONS]


def card_entries(module):
    return [(m['id'], [(p['path'], p['old'], p['new']) for p in m['patches']]) for m in module.MUTATIONS]


def archive_entries(module):
    target = module.TARGET.relative_to(module.ROOT).as_posix()
    return [(name, [(target, old, new) for old, new in patches]) for name, patches in module.MUTATIONS]


def axiom_entries(module):
    target = module.TARGET.relative_to(module.ROOT).as_posix()
    entries = [('CONDITION', [(target, module.CONDITION, module.CONDITION)])]
    return entries + [(identifier, [(target, old, new)]) for identifier, old, new, _, _ in module.MUTATIONS]


TOOLS = {
    'tests/section_profile_mutation_check.py': q38_entries,
    'tests/assembly_mutation_check.py': assembly_entries,
    'tests/pf3_mutation_check.py': pf3_entries,
    'tests/geo261_frontend_mutations.py': frontend_entries,
    'geometry-core/card-reference/mutations.py': card_entries,
    'geometry-core/card-reference/run_archive_mutations.py': archive_entries,
    'geometry-core/card-reference/run_axiom_mutations.py': axiom_entries,
}


def mutate_problems(mutate, mutants):
    sources = mutate.Sources(ROOT)
    problems = {}
    for m in mutants:
        kind, why = mutate.definition_kind(m, sources)
        if kind == 'invalid':
            problems[('tests/mutate.py', m['id'])] = why
    return problems


def drop_live_anchor(tool, entries, sources):
    """The entries with the first currently valid entry's first anchor made absent, and that entry's id."""
    for index, (identifier, patches) in enumerate(entries):
        if not apply_in_order(tool, [(identifier, patches)], sources):
            changed = copy.deepcopy(entries)
            relative, old, new = patches[0]
            changed[index] = (identifier, [(relative, old + MISSING, new), *patches[1:]])
            return changed, identifier
    raise AssertionError(tool + ' has no valid entry to remove')


class MutationAnchors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = Sources()
        cls.entries = {}
        for index, (relative, extract) in enumerate(TOOLS.items()):
            cls.entries[relative] = extract(load(relative, 'mutation_anchor_tool_%d' % index))
        cls.mutate = load('tests/mutate.py', 'mutation_anchor_mutate')

    def found(self):
        problems = {}
        for relative, entries in self.entries.items():
            problems.update(apply_in_order(relative, entries, self.sources))
        problems.update(mutate_problems(self.mutate, self.mutate.MUTANTS))
        return problems

    def test_tables_are_not_empty(self):
        for relative, entries in self.entries.items():
            with self.subTest(tool=relative):
                self.assertGreater(len(entries), 0)
        self.assertGreater(len(self.mutate.MUTANTS), 0)

    def test_every_tool_anchor_occurs_exactly_once_except_the_known_drift(self):
        found = self.found()
        self.assertEqual({}, {key: why for key, why in found.items() if key not in KNOWN_DRIFT},
                         'new drift: re-anchor the tool entry (with its WSL receipt)')
        self.assertEqual(set(), KNOWN_DRIFT - set(found), 'repaired drift: remove it from KNOWN_DRIFT')

    def test_a_removed_anchor_is_reported_for_every_tool(self):
        for relative, entries in self.entries.items():
            with self.subTest(tool=relative):
                broken, identifier = drop_live_anchor(relative, entries, self.sources)
                problems = apply_in_order(relative, broken, self.sources)
                self.assertIn((relative, identifier), problems)
                self.assertIn('anchor occurs 0 times', problems[(relative, identifier)])
                self.assertEqual(set(problems) - {(relative, identifier)},
                                 {key for key in KNOWN_DRIFT if key[0] == relative})
        live = next(m for m in self.mutate.MUTANTS
                    if not m.get('retired') and not mutate_problems(self.mutate, [m]))
        problems = mutate_problems(self.mutate, [dict(live, old=live['old'] + MISSING)])
        self.assertEqual([('tests/mutate.py', live['id'])], list(problems))


if __name__ == '__main__':
    unittest.main()
