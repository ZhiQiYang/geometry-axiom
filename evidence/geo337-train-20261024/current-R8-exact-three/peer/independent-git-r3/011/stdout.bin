"""Existing W end-contact policy: independent oracles and frozen comparison.

The product owns geometry eligibility, owner resolution and contact iteration.
This isolated client proves the moved policy blocks, not product integration.
Its legacy judge is an integrity-checked, versioned extraction from the original
main file; source archives need no Git installation or historical checkout.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native

MODULE = ROOT / "geometry-templates/woodworking/native"
BASELINE = "c94c11e193d1a96b658ebd50ff5b57759b295e5b"
FIXTURE = ROOT / "tests/geo261_contacts_legacy_fixture.txt"
FIXTURE_SHA256 = "ced6f5b6b2eaa87b77f1f289426eb09455a1141a92a0ad7f6225b4c6df9a475a"


def record_native_execution(test, command, result, *, case, phase, control=None, assertion=None):
    """Optionally preserve the original subprocess result; never change the oracle."""
    target = os.environ.get("GEO299316_EXECUTION_LOG")
    if not target:
        return
    record = {
        "test": test, "command": command, "cwd": os.getcwd(), "case": case,
        "phase": phase, "control": control, "expected_assertion": assertion,
        "source_sha": os.environ.get("GITHUB_SHA"),
        "executable_sha256": hashlib.sha256(Path(command[0]).read_bytes()).hexdigest(),
        "environment": {name: os.environ.get(name) for name in
                        ("PATH", "LANG", "LC_ALL", "TMPDIR", "CC", "CFLAGS", "CPPFLAGS", "LDFLAGS",
                         "GITHUB_SHA", "PYTHONOPTIMIZE", "PYTHONDONTWRITEBYTECODE")},
        "actual_exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
        "capture_mode": "original subprocess text stdout/stderr; executable raw bytes are hashed",
    }
    with Path(target).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def without_comments(source):
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)


def definition(source, name):
    source = without_comments(source)
    match = re.search(r"^bool\s+" + re.escape(name) + r"\s*\([^;]*?\)\s*\{", source, flags=re.M | re.S)
    if not match:
        raise AssertionError("Missing contact-policy definition: " + name)
    depth, end = 1, match.end()
    while depth:
        if end >= len(source):
            raise AssertionError("Unbalanced contact-policy definition: " + name)
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[match.start():end]


@lru_cache(maxsize=1)
def fixture():
    raw = FIXTURE.read_bytes().replace(b"\r\n", b"\n")
    actual = hashlib.sha256(raw).hexdigest()
    if actual != FIXTURE_SHA256:
        raise AssertionError("Frozen contact-policy judge hash mismatch: " + actual)
    source = raw.decode("utf-8")
    if BASELINE + ":current_geometry.c" not in source:
        raise AssertionError("Frozen contact-policy judge lost original provenance")
    return source


def legacy_blocks():
    original = fixture()
    span_start = original.index("if (has_edge && self->role")
    span_end = original.index("ext_end[0]", span_start)
    span = without_comments(original[span_start:span_end]).strip()
    contact_start = original.index("if (f->kind == STOP_OUTLINE_EDGE)")
    contact_end = original.index("/* STOP_HOLE_EDGE：", contact_start)
    contact = without_comments(original[contact_start:contact_end]).strip()
    # Owner identity and its extension fact are inputs resolved by the same
    # consumer that owns World. Retain every subsequent original decision.
    lookup_start = contact.index("const Timber *owner = NULL;")
    lookup_end = contact.index("if (owner == NULL || owner == self)", lookup_start)
    contact = contact[:lookup_start] + "Coord owner_prio;\n" + contact[lookup_end:]
    contact, count = re.subn(
        r"stop_in_owner_extension\(\s*world,\s*placement,\s*boundary,\s*owner,\s*cross_lo,\s*cross_hi\s*\)",
        "owner_extension", contact)
    if count != 1:
        raise AssertionError("Expected exactly one old owner-extension query")
    return span, contact


def tokens(source):
    result = []
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[A-Za-z_]\w*|\d+|[^\s]', source):
        if token.startswith("TIMBER_ROLE_"):
            token = token.replace("TIMBER_ROLE_", "WOOD_MEMBER_ROLE_", 1)
        token = {"Coord": "GeoCoord", "STOP_OUTLINE_EDGE": "WOOD_STOP_OUTLINE_EDGE",
                 "STOP_TIMBER_SIDE": "WOOD_STOP_MEMBER_SIDE"}.get(token, token)
        result.append(token)
    return result


def frozen_translation_unit():
    span, contact = legacy_blocks()
    # Keep the original continues in a one-contact loop. Production returns
    # true for those same branches because its caller retains the face loop.
    return '''#include "contacts.h"
#include <stdio.h>
typedef GeoCoord Coord;
enum { TIMBER_ROLE_BOUNDARY=0, TIMBER_ROLE_PRIMARY=1, TIMBER_ROLE_SECONDARY=2, TIMBER_ROLE_CUSTOM=3 };
enum { STOP_OUTLINE_EDGE=0, STOP_HOLE_EDGE=1, STOP_TIMBER_SIDE=2 };
bool frozen_span_extension_check(const WoodMember *self, bool has_edge,
    GeoCoord span_lo, GeoCoord span_hi, GeoCoord edge_lo, GeoCoord edge_hi,
    char *err, size_t err_cap)
{
''' + span + '''
    return true;
}
bool frozen_end_contact_check(const WoodMember *self, const WoodStopFace *f,
    const WoodMember *owner, bool owner_extension, char *err, size_t err_cap)
{
    for (int once=0; once<1; ++once) {
''' + contact + '''
    }
    return true;
}
'''


class WoodContactSourcePreservation(unittest.TestCase):
    def test_policy_blocks_preserve_frozen_product_decisions_and_error_text(self):
        source = (MODULE / "contacts.c").read_text(encoding="utf-8")
        span, contact = legacy_blocks()
        # I22 W (#299) deliberately extends the V_EXTENSION wording. The frozen decision (the guard) and the
        # frozen wording (as exact literal prefix pieces) must survive unchanged; the added fields are pinned
        # by the span/buffer/equivalence cases of geo261_contacts_harness.c and by the controls below.
        with self.subTest(function="wood_member_span_extension_check"):
            actual = definition(source, "wood_member_span_extension_check")
            body = tokens(actual[actual.index("{") :])
            guard = tokens(span[: span.index("{")])
            self.assertEqual(guard, body[1 : 1 + len(guard)])
            for literal in (item for item in tokens(span) if item.startswith('"')):
                self.assertIn(literal, body)
        expected = {
            "wood_member_end_contact_check": "{" + contact.replace("continue;", "return true;") + " return true; }",
        }
        for name, body in expected.items():
            with self.subTest(function=name):
                actual = definition(source, name)
                self.assertEqual(tokens(body), tokens(actual[actual.index("{") :]))

    def test_module_imports_only_public_woodworking_and_standard_headers(self):
        for filename, expected in (("contacts.h", ["members.h", "supports.h"]), ("contacts.c", ["contacts.h"])):
            source = (MODULE / filename).read_text(encoding="utf-8")
            self.assertEqual(expected, re.findall(r'^\s*#include\s+"([^"]+)"', source, flags=re.M))
            self.assertNotRegex(without_comments(source), r"\b(?:World|PlacementSurface|SpaceBoundarySurface|TimberAnchor)\b")

    def test_archive_judge_uses_verified_original_fixture_without_git(self):
        fixture.cache_clear()
        with patch("subprocess.check_output", side_effect=AssertionError("Archive judge must not invoke Git")):
            judge = frozen_translation_unit()
        self.assertIn("continue;", judge)
        self.assertIn("frozen_span_extension_check", judge)
        self.assertNotIn("world->", judge)


class WoodContacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        client = build.woodworking / "wood-contacts-client.c"
        shutil.copy2(ROOT / "tests/geo261_contacts_harness.c", client)
        judge = build.woodworking / "wood-contacts-frozen.c"
        judge.write_text(frozen_translation_unit(), encoding="utf-8")
        cls.client_object = build.compile(client, "wood-contacts-client")
        cls.judge_object = build.compile(judge, "wood-contacts-frozen")
        cls.exe = build.link("wood-contacts-client", [cls.client_object, cls.judge_object, build.wood_contacts_object])

    def case(self, name, exe=None, *, phase="positive", control=None, assertion=None):
        command = [str(exe or self.exe), name]
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        record_native_execution(self.id(), command, result, case=name, phase=phase, control=control, assertion=assertion)
        self.assertIn(result.returncode, (0, 1), "Crash/setup failure is not a contact-policy verdict: " + result.stderr)
        if result.returncode == 1:
            self.assertRegex(result.stderr, r"ASSERT:[a-z0-9-]+")
        return result

    def test_span_extension_role_and_closed_boundary_limits(self):
        self.assertEqual(0, self.case("span").returncode)

    def test_outline_hole_and_unknown_contact_kinds(self):
        self.assertEqual(0, self.case("kinds").returncode)

    def test_owner_pointer_identity_and_two_boundary_exemption(self):
        self.assertEqual(0, self.case("owners").returncode)

    def test_strict_priority_extension_override_and_full_coord_width(self):
        self.assertEqual(0, self.case("priorities").returncode)

    def test_exact_utf8_errors_capacity_null_termination_and_unchanged_tail(self):
        self.assertEqual(0, self.case("buffer").returncode)

    def test_frozen_verdict_and_error_bytes_equivalence(self):
        self.assertEqual(0, self.case("equivalence").returncode)

    def mutant(self, name, function, before, after):
        build = native()
        source = (build.woodworking / "contacts.c").read_text(encoding="utf-8")
        original = definition(source, function)
        self.assertEqual(1, original.count(before), "Contact mutation must hit exactly once: " + name)
        self.assertEqual(1, source.count(original))
        path = build.woodworking / ("contacts-" + name + ".c")
        path.write_text(source.replace(original, original.replace(before, after)), encoding="utf-8")
        obj = build.compile(path, "wood-contacts-" + name)
        return build.link("wood-contacts-" + name, [self.client_object, self.judge_object, obj])

    def test_guard_controls_fail_named_independent_assertions(self):
        controls = (
            ("span-edge", "wood_member_span_extension_check", "has_edge &&", "true &&", "span", "span-no-edge"),
            ("span-role", "wood_member_span_extension_check", "self->role != WOOD_MEMBER_ROLE_BOUNDARY", "true", "span", "span-boundary-extension"),
            ("span-low", "wood_member_span_extension_check", "span_lo < edge_lo", "false", "span", "span-low-refusal"),
            ("span-high", "wood_member_span_extension_check", "span_hi > edge_hi", "false", "span", "span-high-refusal"),
            ("span-error", "wood_member_span_extension_check", "err != NULL", "false", "span", "span-error-exact"),
            ("span-edge-id", "wood_member_span_extension_check", "(unsigned)self->id, edge_index,", "(unsigned)self->id, 0,", "span", "span-error-exact"),
            ("span-edge-interval", "wood_member_span_extension_check", "(long long)edge_lo, (long long)edge_hi, low_note, high_note);", "(long long)span_lo, (long long)edge_hi, low_note, high_note);", "span", "span-error-exact"),
            ("span-low-clause", "wood_member_span_extension_check", "if (edge_lo > span_lo) {", "if (0) {", "span", "span-error-exact"),
            ("span-high-clause", "wood_member_span_extension_check", "if (edge_hi < span_hi) {", "if (0) {", "span", "span-high-error-exact"),
            ("span-low-always", "wood_member_span_extension_check", "if (edge_lo > span_lo) {", "if (1) {", "span", "span-high-error-exact"),
            ("span-high-always", "wood_member_span_extension_check", "if (edge_hi < span_hi) {", "if (1) {", "span", "span-error-exact"),
            ("outline-kind", "wood_member_end_contact_check", "f->kind == WOOD_STOP_OUTLINE_EDGE", "false", "kinds", "outline-primary-refusal"),
            ("outline-role", "wood_member_end_contact_check", "self->role != WOOD_MEMBER_ROLE_BOUNDARY", "false", "kinds", "outline-primary-refusal"),
            ("member-kind", "wood_member_end_contact_check", "f->kind == WOOD_STOP_MEMBER_SIDE", "true", "kinds", "hole-accepted"),
            ("owner-guard", "wood_member_end_contact_check", "owner == NULL || owner == self", "true", "owners", "same-id-distinct-pointer-not-exempt"),
            ("owner-identity", "wood_member_end_contact_check", "owner == self", "false", "owners", "self-owner-exempt"),
            ("two-boundary-self", "wood_member_end_contact_check", "self->role == WOOD_MEMBER_ROLE_BOUNDARY", "false", "owners", "two-boundary-exempt"),
            ("two-boundary-owner", "wood_member_end_contact_check", "owner->role == WOOD_MEMBER_ROLE_BOUNDARY", "true", "owners", "only-self-boundary-not-exempt"),
            ("owner-extension", "wood_member_end_contact_check", "if (owner_extension)", "if (false)", "priorities", "extension-priority-two"),
            ("extension-value", "wood_member_end_contact_check", "owner_prio = 2;", "owner_prio = 1;", "priorities", "extension-priority-two"),
            ("equal-priority", "wood_member_end_contact_check", "owner_prio >= self->cut_priority", "owner_prio > self->cut_priority", "owners", "same-id-distinct-pointer-not-exempt"),
            ("priority-guard", "wood_member_end_contact_check", "owner_prio >= self->cut_priority", "false", "owners", "same-id-distinct-pointer-not-exempt"),
            ("priority-error", "wood_member_end_contact_check", "if (owner_prio >= self->cut_priority) {\n            if (err != NULL)", "if (owner_prio >= self->cut_priority) {\n            if (false)", "owners", "priority-error-exact"),
        )
        for name, function, before, after, case, assertion in controls:
            with self.subTest(guard=name):
                self.assertEqual(0, self.case(case, phase="baseline", control=name, assertion=assertion).returncode)
                mutant = self.mutant(name, function, before, after)
                result = self.case(case, mutant, phase="mutant", control=name, assertion=assertion)
                self.assertEqual(1, result.returncode, "Contact-policy mutation survived: " + name)
                self.assertIn("ASSERT:" + assertion, result.stderr)
                self.assertEqual(0, self.case(case, phase="restored", control=name, assertion=assertion).returncode)


if __name__ == "__main__":
    unittest.main(verbosity=2)
