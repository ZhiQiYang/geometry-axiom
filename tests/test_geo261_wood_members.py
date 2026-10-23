"""Extracted W member behavior, historical source preservation and K geometry.

The isolated client links the actual W object with the actual public K object.
Product integration and the product-side W mutation witness are separately
owned by the native integration tests; this client alone is not product proof.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import native

MEMBERS = ROOT / "geometry-templates/woodworking/native"
BASELINE = "c28ea9639b79881f30995cd79ce843346373c31e"

# Computed once from the frozen product at BASELINE. Whitespace/comments and
# the explicit identifier renaming below are the only ignored differences.
# These hashes guard the move, not geometry correctness (the C client does).
BASELINE_TOKENS = {
    "wood_member_construct": "d00fa7375d6770c289d464c804528f8905689c5f04d62db189d5624c05d52054",
    "wood_member_role_name": "f4f5e086091a65cc826593036a37c72c7d4847beee6ba0434a07eb065b0c9466",
    "wood_member_face_valid": "076187db8a5861673dcd8360ed09b2f0c3850ee8fa21660de1e9c3d91436a47b",
    "wood_member_face_name": "07197250274b21de8ba1f507cfea08313751437eeccabf96ae0a8e15640a9bec",
    "wood_member_face_short_name": "844f80900b051b7fa69bf738c6c7c4218fb7688bca9c5fceaac3c092b683e93c",
    "wood_member_face_room": "3ba8be70721b9b233a741d4cfa479bee764f20a2ae19e12c8c4e745399c7b864",
    "WoodMemberRole": "93b60486ce069ab5b56e5da02fba210f8ed08ba6bbc43d006c8863fd9125efc4",
    "WoodMemberFace": "e7681361618f8b9e3525d59681b1a72dfc5a6dedd92615bc08c111327077a075",
    "WoodMember": "dba6e29b744d195c110b5627640dd55c1483f2d70c5a4c9d39fba14562cc4432",
    "WOOD_MEMBER_FACE_SPEC": "f9cde8f956892e3903541b8f45df92073414bcfbe80da7010aa584bba6a5bce5",
    "WOOD_MEMBER_FACE_NAMES": "436b5fa63e97c25918651427717bc6666ea73a8693c6b1a8af29393a68f759f8",
}

RENAMED = {
    "TimberId": "uint32_t",
    "Coord": "GeoCoord",
    "Point3": "GeoPoint3",
    "Vector3": "GeoVector3",
    "Quad3": "GeoQuad3",
    "Timber": "WoodMember",
    "TimberRole": "WoodMemberRole",
    "TimberFaceId": "WoodMemberFace",
    "timber_construct": "wood_member_construct",
    "timber_role_name": "wood_member_role_name",
    "timber_face_id_is_valid": "wood_member_face_valid",
    "timber_face_name": "wood_member_face_name",
    "timber_face_short_name": "wood_member_face_short_name",
    "timber_get_face_room": "wood_member_face_room",
}
FUNCTIONS = (
    "timber_construct", "timber_role_name", "timber_face_id_is_valid",
    "timber_face_name", "timber_face_short_name", "timber_get_face_room",
)


def without_comments(source):
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)


def token_digest(source):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[A-Za-z_]\w*|\d+|[^\s]', source)
    normalized = []
    for token in tokens:
        if token.startswith("TIMBER_FACE_"):
            token = token.replace("TIMBER_FACE_", "WOOD_MEMBER_FACE_", 1)
        elif token.startswith("TIMBER_ROLE_"):
            token = token.replace("TIMBER_ROLE_", "WOOD_MEMBER_ROLE_", 1)
        normalized.append(RENAMED.get(token, token))
    encoded = json.dumps(normalized, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def extraction_digests(source, *, legacy=False):
    source = without_comments(source)
    result = {}
    for original in FUNCTIONS:
        name = original if legacy else RENAMED[original]
        match = re.search(r"\b" + name + r"\s*\([^;]*?\)\s*(\{.*?^\})", source, flags=re.S | re.M)
        if not match:
            raise AssertionError("Missing member definition: " + name)
        result[RENAMED[original]] = token_digest(match.group(1))
    for original in ("TimberRole", "TimberFaceId", "Timber"):
        name = original if legacy else RENAMED[original]
        kind = "struct" if original == "Timber" else "enum"
        match = re.search(r"typedef " + kind + r"\s*\{([^{}]*?)\}\s*" + name + r"\s*;", source, flags=re.S)
        if not match:
            raise AssertionError("Missing member storage definition: " + name)
        result[RENAMED[original]] = token_digest(match.group(1))
    for suffix in ("SPEC", "NAMES"):
        name = ("TIMBER_FACE_" if legacy else "WOOD_MEMBER_FACE_") + suffix
        match = re.search(r"\b" + name + r"\s*\[[^]]+\]\s*=\s*(\{.*?^\});", source, flags=re.S | re.M)
        if not match:
            raise AssertionError("Missing member face table: " + name)
        result["WOOD_MEMBER_FACE_" + suffix] = token_digest(match.group(1))
    return result


class WoodMemberSourcePreservation(unittest.TestCase):
    def test_extracted_definitions_preserve_frozen_product_tokens(self):
        source = (MEMBERS / "members.h").read_text(encoding="utf-8") + "\n" + (MEMBERS / "members.c").read_text(encoding="utf-8")
        self.assertEqual(BASELINE_TOKENS, extraction_digests(source), BASELINE)

    def test_module_imports_only_its_own_header_and_public_geometry(self):
        for filename, expected in (("members.h", ["geometry.h"]), ("members.c", ["members.h"])):
            source = (MEMBERS / filename).read_text(encoding="utf-8")
            self.assertEqual(expected, re.findall(r'^\s*#include\s+"([^"]+)"', source, flags=re.M))
            self.assertNotRegex(without_comments(source), r"\b(?:World|PlacementSurface|surface_construct|timber_place)\b")


class WoodMembers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = native()
        source = build.woodworking / "wood-members-client.c"
        shutil.copy2(ROOT / "tests/geo261_wood_members_harness.c", source)
        cls.client = build.compile(source, "wood-members-client")
        cls.exe = build.link("wood-members-client", [cls.client, build.wood_members_object, build.geometry_object])

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True, text=True, timeout=10)
        self.assertIn(result.returncode, (0, 1), "Native crash/setup failure is not a member verdict: " + result.stderr)
        return result.returncode

    def test_storage_layout_and_enum_values_match_existing_product(self):
        self.assertEqual(0, self.case("layout"))

    def test_constructor_preserves_roles_priorities_identity_and_defaults(self):
        self.assertEqual(0, self.case("construction"))

    def test_rejected_construction_leaves_output_unchanged(self):
        self.assertEqual(0, self.case("rejection"))

    def test_full_short_and_unknown_face_names_are_unchanged(self):
        self.assertEqual(0, self.case("names"))

    def test_exact_six_face_corners_in_all_24_signed_frames(self):
        self.assertEqual(0, self.case("faces"))

    def test_face_rejections_and_degenerate_length_preserve_original_behavior(self):
        self.assertEqual(0, self.case("face-rejection"))

    def mutant(self, name, before, after):
        build = native()
        source = (build.woodworking / "members.c").read_text(encoding="utf-8")
        self.assertEqual(1, source.count(before), "Negative control must replace exactly one member expression")
        path = build.woodworking / ("members-" + name + ".c")
        path.write_text(source.replace(before, after), encoding="utf-8")
        # Compilation failures raise in NativeBuild. Only a successfully linked
        # process returning the harness's explicit 1 assertion verdict counts.
        obj = build.compile(path, "wood-members-" + name)
        return build.link("wood-members-" + name, [self.client, obj, build.geometry_object])

    def test_constructor_negative_control_fails_behavior_assertion(self):
        self.assertEqual(0, self.case("rejection"))
        mutant = self.mutant("zero-cross-section", "size_a <= 0", "size_a < 0")
        self.assertEqual(1, self.case("rejection", mutant))
        self.assertEqual(0, self.case("rejection"))

    def test_face_mapping_negative_control_fails_exact_geometry_assertion(self):
        self.assertEqual(0, self.case("faces"))
        mutant = self.mutant("contact-face", "[WOOD_MEMBER_FACE_A0]    = { 2, 0 }", "[WOOD_MEMBER_FACE_A0]    = { 1, 0 }")
        self.assertEqual(1, self.case("faces", mutant))
        self.assertEqual(0, self.case("faces"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
