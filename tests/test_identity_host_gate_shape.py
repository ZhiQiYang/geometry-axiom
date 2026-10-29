# -*- coding: utf-8 -*-
"""Source read-back for the K3-L host gate and the named de-identified call sites.

This does not compile or execute the desktop window. A missing exemption, a gate
inside the Windows-only block, or a named caller still using a full dump fails here.
"""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def lf(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n").decode("utf-8")


def lines(path: Path) -> list[str]:
    return lf(path).split("\n")


def win32_stack(text: str):
    """Track #ifdef _WIN32 / #ifndef _WIN32, including the flipped #else arm."""
    stack = []
    depths = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#ifndef") and "_WIN32" in stripped:
            stack.append("ndef")
        elif stripped.startswith("#if") and "_WIN32" in stripped:
            stack.append("def")
        elif stripped.startswith("#else") or stripped.startswith("#elif"):
            if stack:
                stack[-1] = {"def": "else", "ndef": "def", "else": "def"}.get(stack[-1], stack[-1])
        elif stripped.startswith("#endif") and stack:
            stack.pop()
        depths.append(tuple(stack))
    return depths


class IdentityHostGateShapeTest(unittest.TestCase):
    def test_gate_function_is_outside_win32_and_exempts_undo(self):
        text = lf(ROOT / "current_geometry.c")
        depths = win32_stack(text)
        start = text.index("static bool host_gate_rejects(")
        line_no = text[:start].count("\n")
        self.assertNotIn("def", depths[line_no])
        body = text[start:text.index("static bool apply_interactive_tokens", start)]
        self.assertIn('!strcmp(tokens[0], "undo")', body)
        self.assertIn('!strcmp(tokens[0], "redo")', body)
        self.assertIn("桌面版尚不支援身分帳，唯讀開啟", body)
        self.assertNotIn("g_host_mode", body)
        self.assertNotIn("g_identity_epoch", body)

    def test_gdi_wires_gate_before_apply_and_sets_flag_once(self):
        rows = lines(ROOT / "current_geometry.c")
        depths = win32_stack("\n".join(rows))
        apply_at = next(i for i, row in enumerate(rows) if row.startswith("static void interactive_apply_line(") and not row.rstrip().endswith(";"))
        self.assertIn("def", depths[apply_at])
        window = "\n".join(rows[apply_at:apply_at + 50])
        gate = window.index("host_gate_rejects(g_host_mode,")
        empty = window.index("if (count <= 0)")
        apply = window.index("apply_interactive_tokens(")
        self.assertLess(empty, gate)
        self.assertLess(gate, apply)
        self.assertLess(gate, window.index("reference_gdi_confirm("))
        assignments = [i for i, row in enumerate(rows) if "g_host_mode = 1;" in row]
        self.assertEqual(assignments, [i for i, row in enumerate(rows) if row.strip() == "g_host_mode = 1;"])
        self.assertEqual(len(assignments), 1)
        show = next(i for i, row in enumerate(rows) if "gdi_show_three_views(" in row and row.strip().startswith(("static", "void", "int")))
        loop = next(i for i, row in enumerate(rows) if "GetMessageW(" in row and i > show)
        self.assertLess(show, assignments[0])
        self.assertLess(assignments[0], loop)
        self.assertIn("def", depths[assignments[0]])
        export = "\n".join(rows)
        self.assertIn(
            "bool saved_marks = g_identity_include_marks;\n"
            "                        g_identity_include_marks = false;\n"
            "                        world_dump_dsl(app->world, f);\n"
            "                        g_identity_include_marks = saved_marks;",
            export,
        )

    def test_bridge_seam_is_readonly(self):
        bridge = lf(ROOT / "geometry-web" / "web_bridge.c")
        self.assertNotIn("g_host_mode", bridge)
        start = bridge.index("static void cmd_host_gate_check(")
        body = bridge[start:bridge.index("#include \"engineering_bridge.inc\"", start)]
        for forbidden in ("apply_interactive_tokens", "history_record", "world_dump_dsl", "g_host_mode"):
            self.assertNotIn(forbidden, body)
        self.assertIn("host_gate_rejects(mode, &g_world,", body)
        self.assertIn('strcmp(line, "host-gate-check") == 0 && arg', bridge)
        self.assertIn("cmd_host_gate_check(arg);", bridge)

    def test_named_dump_sites_are_deidentified(self):
        checks = {
            "geometry-web/feedback.js": ("rawApi(\"dump-deidentified\")", "rawApi(\"dump\")"),
            "geometry-web/model-update-app.js": ("read('dump-deidentified'", "read('dump',"),
            "geometry-web/section-profile-workspace.js": ("command('dump-deidentified')", "command('dump')"),
            "geometry-core/rule_cases/executor.py": ("command(\"dump-deidentified\")", "command(\"dump\")"),
        }
        for rel, (present, absent) in checks.items():
            text = lf(ROOT / rel)
            self.assertIn(present, text, rel)
            self.assertNotIn(absent, text, rel)
        space = lf(ROOT / "geometry-web" / "space-workspace.js")
        self.assertGreaterEqual(space.count("dump-deidentified"), 8)
        self.assertNotIn('api("dump")', space)
        self.assertNotIn("api('dump')", space)

    def test_restore_strips_locally_before_full_dump(self):
        rows = lines(ROOT / "geometry-web" / "reference-workspace.js")
        start = next(i for i, row in enumerate(rows) if "async function restoreSession()" in row)
        end = next(i for i, row in enumerate(rows) if i > start and row.startswith("  async function "))
        body = "\n".join(rows[start:end])
        probe = body.index("P.stripIdentityLedger(loaded.scene)")
        first = body.index('api("dump-deidentified")')
        second = body.index('api("dump-deidentified")', first + 1)
        full = body.index('api("dump")')
        self.assertLess(probe, first)
        self.assertLess(first, second)
        self.assertLess(second, full)
        self.assertEqual(body.count('api("dump-deidentified")'), 2)
        self.assertEqual(body.count('api("dump")'), 1)
        self.assertIn("身分帳不完整，須先復原上一步才能保存", body)
        self.assertIn("restoreAfterProbe", body)


if __name__ == "__main__":
    unittest.main()
