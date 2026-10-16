"""A second real C template, built with only its public K source closure.

No existing product binary, application module or first-template source enters
the build. Compile failures/crashes do not count as semantic mutation catches.
The expected missing-object link failure is a separate dependency assertion.
"""
from __future__ import annotations

import importlib.abc
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
KERNEL_FILES = ("types.h", "exact.h", "exact.c", "geometry.h", "geometry.c", "grid.h", "grid.c")
SOURCE_FILES = tuple("geometry-core/kernel/" + name for name in KERNEL_FILES) + (
    "geometry-templates/rectangular-grid/rectangular_grid.h",
    "geometry-templates/rectangular-grid/rectangular_grid.c",
    "tests/rectangular_template_harness.c",
    "tests/test_rectangular_template.py",
)


def copy_sources(destination):
    for relative in SOURCE_FILES:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


class RectangularTemplateSourceIsolation(unittest.TestCase):
    def test_source_installation_is_closed_and_contains_only_core_recipe_and_tests(self):
        with tempfile.TemporaryDirectory(prefix="rectangular-template-sources-") as temporary:
            root = Path(temporary)
            copy_sources(root)
            actual = {str(path.relative_to(root)).replace("\\", "/") for path in root.rglob("*") if path.is_file()}
            self.assertEqual(set(SOURCE_FILES), actual)
            self.assertEqual(["rectangular-grid"], [path.name for path in (root / "geometry-templates").iterdir()])
            include_dirs = (root / "geometry-core/kernel", root / "geometry-templates/rectangular-grid")
            for relative in SOURCE_FILES:
                path = root / relative
                if path.suffix not in (".c", ".h"):
                    continue
                self.assertEqual((ROOT / relative).read_bytes(), path.read_bytes())
                for include in re.findall(r'^\s*#\s*include\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.M):
                    targets = [directory / include for directory in (path.parent, *include_dirs)]
                    self.assertTrue(any(target.is_file() and target.resolve().is_relative_to(root) for target in targets),
                                    f"non-isolated include: {relative}: {include}")


class IsolatedNativeBuild:
    def __init__(self):
        parent = Path(tempfile.gettempdir()) / "geometry-tests"
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="rectangular-template-", dir=parent)
        self.work = Path(self.temp.name)
        self.logs = []
        self.windows = os.name == "nt"
        self.suffix = ".exe" if self.windows else ""
        self.env = {key: value for key, value in os.environ.items()
                    if key not in ("CPATH", "C_INCLUDE_PATH", "CPLUS_INCLUDE_PATH", "LIBRARY_PATH")}
        try:
            if self.windows:
                vswhere = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
                if not vswhere.is_file():
                    raise unittest.SkipTest("MSVC unavailable for rectangular template isolation")
                install = subprocess.check_output([str(vswhere), "-latest", "-products", "*", "-requires",
                    "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"], text=True).strip()
                self.vcvars = Path(install) / "VC/Auxiliary/Build/vcvars64.bat"
                if not self.vcvars.is_file():
                    raise unittest.SkipTest("MSVC environment unavailable for rectangular template isolation")
            else:
                self.cc = shutil.which(os.environ.get("CC", "cc"))
                if not self.cc:
                    raise unittest.SkipTest("C compiler unavailable for rectangular template isolation")
            self.source_root = self.work / "installation"
            copy_sources(self.source_root)
            self.kernel = self.source_root / "geometry-core/kernel"
            self.recipe = self.source_root / "geometry-templates/rectangular-grid"
            self.objects = {name: self.compile(self.kernel / (name + ".c"), name)
                            for name in ("exact", "geometry", "grid")}
            self.objects["recipe"] = self.compile(self.recipe / "rectangular_grid.c", "recipe")
            self.objects["harness"] = self.compile(self.source_root / "tests/rectangular_template_harness.c", "harness")
            self.exe = self.link("rectangular-template", list(self.objects.values()))
        except BaseException:
            self.close()
            raise

    def close(self):
        destination = os.environ.get("GEOMETRY_RECTANGULAR_TEMPLATE_EVIDENCE")
        if destination:
            path = Path(destination)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"sources": SOURCE_FILES, "commands": self.logs}, indent=2), encoding="utf-8")
        self.temp.cleanup()

    def run(self, args, *, expect_success=True):
        if self.windows:
            script = self.work / ("build-%d.cmd" % len(self.logs))
            script.write_text('@echo off\ncall "' + str(self.vcvars) + '" >nul\n' + subprocess.list2cmdline(args) + '\n', encoding="utf-8")
            command = ["cmd", "/d", "/c", str(script)]
        else:
            command = args
        result = subprocess.run(command, cwd=self.work, env=self.env, capture_output=True,
                                text=True, errors="replace", timeout=120)
        self.logs.append({"command": command, "arguments": args, "exit": result.returncode,
                          "stdout": result.stdout, "stderr": result.stderr})
        if expect_success and result.returncode:
            raise AssertionError("Compile/link failed; not a semantic mutation verdict:\n" + result.stdout + result.stderr)
        return result

    def compile(self, source, name):
        output = self.work / (name + (".obj" if self.windows else ".o"))
        if self.windows:
            args = ["cl", "/nologo", "/utf-8", "/Od", "/W3", "/c", "/I" + str(self.kernel),
                    "/I" + str(self.recipe), "/Fo:" + str(output), str(source)]
        else:
            args = [self.cc, "-std=c11", "-O0", "-Werror=implicit-function-declaration", "-I", str(self.kernel),
                    "-I", str(self.recipe), "-c", str(source), "-o", str(output)]
        self.run(args)
        return output

    def link(self, name, objects, *, expect_success=True):
        output = self.work / (name + self.suffix)
        args = (["cl", "/nologo", *map(str, objects), "/Fe:" + str(output), "/link", "/STACK:16777216"]
                if self.windows else [self.cc, *map(str, objects), "-o", str(output)])
        result = self.run(args, expect_success=expect_success)
        return output if expect_success else result


class RectangularTemplateNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class RejectApplicationImports(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                root = fullname.partition(".")[0]
                if root in ("modeling", "geometry_app") or root.startswith("woodworking"):
                    raise AssertionError("application/template import in isolated recipe tests: " + fullname)
                return None
        cls.import_blocker = RejectApplicationImports()
        sys.meta_path.insert(0, cls.import_blocker)
        try:
            cls.build = IsolatedNativeBuild()
        except BaseException:
            sys.meta_path.remove(cls.import_blocker)
            raise

    @classmethod
    def tearDownClass(cls):
        try:
            cls.build.close()
        finally:
            sys.meta_path.remove(cls.import_blocker)

    def case(self, name, executable=None):
        result = subprocess.run([str(executable or self.build.exe), name], cwd=self.build.source_root,
                                env=self.build.env, capture_output=True, text=True, timeout=10)
        self.build.logs.append({"case": name, "executable": str(executable or self.build.exe),
                               "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        self.assertIn(result.returncode, (0, 1), "crash is not a template verdict: " + result.stderr)
        return result

    def check(self, name):
        result = self.case(name)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_exact_1000_by_600_has_15_200_by_200_cells(self): self.check("exact-cells")
    def test_source_edit_recomputes_same_references_after_reordering(self): self.check("source-update")
    def test_fractional_subdivision_rejects_with_exact_diagnostic_and_no_partial_result(self): self.check("fractional-rollback")
    def test_counts_and_lengths_retain_distinct_field_kinds_and_units(self): self.check("field-types")
    def test_exact_source_normalization_never_rounds_fractional_geometry(self): self.check("exact-sources")
    def test_source_owner_field_revision_and_duplicate_contract(self): self.check("references")
    def test_bounds_capacity_and_one_cell(self): self.check("bounds-capacity")
    def test_invalid_inputs_leave_output_untouched(self): self.check("invalid-input")

    def test_actual_kernel_divisibility_mutation_breaks_the_recipe_contract(self):
        self.check("fractional-rollback")
        original = (self.build.kernel / "grid.c").read_text(encoding="utf-8")
        target = "if((hi-lo)%n)return GEO_GRID_NOT_DIVISIBLE;"
        self.assertEqual(1, original.count(target), "mutation did not target exactly one real core guard")
        source = self.build.work / "grid-rounded-mutant.c"
        source.write_text(original.replace(target, "/* negative control: allow truncated cell coordinates */"), encoding="utf-8")
        mutant = self.build.compile(source, "grid-rounded-mutant")
        objects = [mutant if key == "grid" else obj for key, obj in self.build.objects.items()]
        executable = self.build.link("rectangular-rounded-mutant", objects)
        result = self.case("fractional-rollback", executable)
        self.assertEqual(1, result.returncode, "core mutation did not change real recipe behavior")
        self.assertIn("FRACTIONAL_CELL_ACCEPTED", result.stderr)
        self.check("fractional-rollback")

    def test_removing_core_grid_object_reports_the_real_required_api(self):
        objects = [obj for key, obj in self.build.objects.items() if key != "grid"]
        result = self.build.link("rectangular-without-grid", objects, expect_success=False)
        self.assertNotEqual(0, result.returncode, "recipe linked without the extracted core algorithm")
        self.assertIn("geo_interval_subdivide", result.stdout + result.stderr)
        self.check("exact-cells")


if __name__ == "__main__":
    unittest.main(verbosity=2)
