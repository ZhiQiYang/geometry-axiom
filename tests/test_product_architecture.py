"""Actual-product static contract and controls; no compiler or native execution.

The actual source roots are inventoried before creating a snapshot. The complete
product graph is scanned once. Mutation controls reparse actual
changed files against that graph, with unchanged files copied byte-for-byte.
This proves the static dependency gate, not native no-template execution.
"""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest

from architecture_contract import ContractError, Scanner, load_manifest, scan


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "geometry-core/domain-decoupling/product-architecture.json"


def snapshot_product_sources(source_root, target_root, manifest):
    """Reject omissions in the actual input roots before copying declared files."""
    Scanner(source_root, manifest).validate_manifest()
    for entry in manifest["sources"] + manifest["exclusions"]:
        relative = entry["path"]
        target = target_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_root / relative, target)


class ProductArchitecture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest(MANIFEST)
        cls.temporary = tempfile.TemporaryDirectory(prefix="geo261-product-architecture-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name) / "product"
        snapshot_product_sources(ROOT, cls.root, cls.manifest)
        cls.baseline = scan(cls.root, cls.manifest)

    def setUp(self):
        self.config = deepcopy(self.manifest)

    @contextmanager
    def change(self, relative, transform):
        path = self.root / relative
        raw = path.read_bytes()
        path.write_bytes(transform(raw))
        try:
            yield path
        finally:
            path.write_bytes(raw)

    def focused(self, *changed):
        """Reparse changed real files; retain only unchanged baseline edges."""
        scanner = Scanner(self.root, self.config)
        try:
            scanner.validate_manifest()
        except ContractError as error:
            scanner.result.diagnostics.append(error.diagnostic)
            return scanner.result
        scanner.result.edges = [edge for edge in self.baseline.edges if edge.source not in changed]
        for relative in changed:
            try:
                text = (self.root / relative).read_text(encoding="utf-8")
                language = scanner.entries[relative]["language"]
                method = {"c": scanner.scan_c, "python": scanner.scan_python,
                          "javascript": scanner.scan_javascript, "html": scanner.scan_html}[language]
                method(relative, text)
            except ContractError as error:
                scanner.result.diagnostics.append(error.diagnostic)
        scanner.directions()
        return scanner.result

    def rejects(self, result, code, path=None, chain=None):
        matches = [item for item in result.diagnostics if item.code == code
                   and (path is None or item.path == path)
                   and (chain is None or item.chain == tuple(chain))]
        self.assertTrue(matches, [item.__dict__ for item in result.diagnostics])

    def test_complete_product_graph(self):
        self.assertTrue(self.baseline.ok, [item.__dict__ for item in self.baseline.diagnostics])
        self.assertEqual(set(self.manifest["sourceRoots"]),
                         {"geometry-core", "geometry-app", "geometry-templates", "geometry-web", "geometry-guide"})
        self.assertEqual(set(self.manifest["sourceFiles"]),
                         {"current_geometry.c", "tests/__init__.py", "tests/binaries.py"})
        self.assertEqual(len(self.baseline.sources), len(self.manifest["sources"]))

    def test_actual_native_core_identifier_is_rejected(self):
        path = "geometry-core/kernel/geometry.c"
        with self.change(path, lambda raw: raw + b"\nint TIMBER_ROLE_PRIMARY;\n"):
            self.rejects(self.focused(path), "FORBIDDEN_IDENTIFIER", path)

    def test_actual_native_core_direct_template_dependency_is_rejected(self):
        path = "geometry-core/kernel/geometry.c"
        with self.change(path, lambda raw: raw + b'\n#include "../../geometry-templates/woodworking/native/members.h"\n'):
            self.rejects(self.focused(path), "LAYER_DIRECTION", path,
                         [path, "geometry-templates/woodworking/native/members.h"])

    def test_actual_native_core_transitive_template_dependency_is_rejected(self):
        path = "geometry-core/kernel/geometry.h"
        with self.change(path, lambda raw: raw + b'\n#include "../../geometry-templates/woodworking/native/members.h"\n'):
            self.rejects(self.focused(path), "LAYER_DIRECTION", path,
                         ["geometry-core/kernel/geometry.c", path,
                          "geometry-templates/woodworking/native/members.h"])

    def test_actual_python_core_template_import_is_rejected(self):
        path = "geometry-core/geometry_kernel/canonical.py"
        with self.change(path, lambda raw: raw + b"\nimport geometry_woodworking.model_policy\n"):
            self.rejects(self.focused(path), "FORBIDDEN_MODULE", path)

    def test_actual_python_core_transitive_host_import_is_rejected(self):
        path = "geometry-core/geometry_kernel/errors.py"
        with self.change(path, lambda raw: raw + b"\nimport geometry_app.model_common\n"):
            self.rejects(self.focused(path), "LAYER_DIRECTION", path,
                         ["geometry-core/geometry_kernel/evaluate.py", path,
                          "geometry-app/geometry_app/__init__.py"])

    def test_actual_interval_core_woodworking_policy_tokens_are_rejected(self):
        path = "geometry-core/interval-allocation.js"
        for token in (b"GeometryWoodworkingCutting", b"materialKey", b"stockIdentity", b"sectionKey",
                      b"kerf", b"minRemnant", b"allowance", b"TIMBER_ROLE_PRIMARY"):
            with self.subTest(token=token), self.change(path, lambda raw: raw + b"\nvoid " + token + b";\n"):
                self.rejects(self.focused(path), "FORBIDDEN_IDENTIFIER", path)

    def test_actual_interval_core_fixed_template_identity_is_rejected(self):
        path = "geometry-core/interval-allocation.js"
        with self.change(path, lambda raw: raw + b'\nvoid "woodworking/1";\n'):
            self.rejects(self.focused(path), "FORBIDDEN_STRING", path)

    def test_actual_interval_core_template_dependency_is_rejected(self):
        path = "geometry-core/interval-allocation.js"
        target = "geometry-templates/woodworking/cutting.js"
        with self.change(path, lambda raw: raw + b'\nrequire("../geometry-templates/woodworking/cutting.js");\n'):
            self.rejects(self.focused(path), "LAYER_DIRECTION", path, [path, target])

    def test_actual_woodworking_cutting_host_dependencies_are_rejected(self):
        path = "geometry-templates/woodworking/cutting.js"
        for target in ("geometry-web/cutting-settings.js", "geometry-web/timber-schedule.js",
                       "geometry-app/application.js"):
            with self.subTest(target=target), self.change(
                    path, lambda raw: raw + ('\nrequire("../../' + target + '");\n').encode("utf-8")):
                self.rejects(self.focused(path), "LAYER_DIRECTION", path, [path, target])

    def test_unlisted_product_file_is_rejected(self):
        path = self.root / "geometry-core/kernel/architecture_probe.c"
        try:
            path.write_text("int neutral_probe;\n", encoding="utf-8")
            self.rejects(self.focused(), "SOURCE_UNREGISTERED")
        finally:
            path.unlink(missing_ok=True)

    def test_snapshot_setup_rejects_unlisted_input_before_copy(self):
        # The existing temporary product tree is now the input to the identical
        # setup routine. No undeclared file is created in the real repository.
        path = self.root / "geometry-core/kernel/input_inventory_probe.c"
        with tempfile.TemporaryDirectory(prefix="geo261-inventory-destination-") as folder:
            destination = Path(folder) / "snapshot"
            try:
                path.write_text("int input_inventory_probe;\n", encoding="utf-8")
                with self.assertRaises(ContractError) as caught:
                    snapshot_product_sources(self.root, destination, self.config)
                self.assertEqual("SOURCE_UNREGISTERED", caught.exception.diagnostic.code)
                self.assertEqual("geometry-core/kernel/input_inventory_probe.c", caught.exception.diagnostic.path)
                self.assertFalse(destination.exists(), "An invalid input tree must fail before any snapshot is copied")
            finally:
                path.unlink(missing_ok=True)

    def test_exact_exclusion_digest_cannot_hide_changed_code(self):
        entry = self.manifest["exclusions"][0]
        with self.change(entry["path"], lambda raw: raw + b"\n "):
            self.rejects(self.focused(), "EXCLUSION_DIGEST", entry["path"])

    def test_remove_all_templates_still_scans_every_actual_core_source(self):
        with tempfile.TemporaryDirectory(prefix="geo261-no-template-static-") as folder:
            target = Path(folder)
            sources = [deepcopy(entry) for entry in self.manifest["sources"] if entry["layer"] == "K"]
            for entry in sources:
                path = target / entry["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(self.root / entry["path"], path)
            config = deepcopy(self.manifest)
            config.update(sourceRoots=["geometry-core"],
                          sourceFiles=[], sources=sources, exclusions=[], htmlScriptRoutes=[],
                          javascriptImportRoutes=[], htmlEmbedRoutes=[], trustedVendorBundles=[],
                          searchRoots={"c": [".", "geometry-core/kernel"], "python": ["geometry-core"],
                                       "javascript": ["geometry-core"]})
            self.assertFalse((target / "geometry-templates").exists())
            self.assertFalse((target / "geometry-app").exists())
            self.assertFalse((target / "geometry-web").exists())
            result = scan(target, config)
            self.assertTrue(result.ok, [item.__dict__ for item in result.diagnostics])
            self.assertEqual(set(result.sources), {entry["path"] for entry in sources})

    def test_iframe_external_src_is_rejected(self):
        path = "geometry-web/index.html"
        with self.change(path, lambda raw: raw.replace(b'<iframe id="scenarioEditorFrame"',
                                                       b'<iframe src="https://example.invalid/" id="scenarioEditorFrame"', 1)):
            self.rejects(self.focused(path), "HTML_EMBED_SOURCE", path)

    def test_iframe_unregistered_src_and_extra_query_are_rejected(self):
        path = "geometry-web/index.html"
        for source in (b"/other.html", b"//example.invalid/", b"/?scenario=one&amp;extra=two"):
            with self.subTest(src=source), self.change(path, lambda raw: raw.replace(
                    b'<iframe id="scenarioEditorFrame"', b'<iframe src="' + source + b'" id="scenarioEditorFrame"', 1)):
                self.rejects(self.focused(path), "HTML_EMBED_SOURCE", path)

    def test_iframe_srcdoc_is_rejected(self):
        path = "geometry-web/index.html"
        with self.change(path, lambda raw: raw.replace(b'<iframe id="scenarioEditorFrame"',
                                                       b'<iframe srcdoc="" id="scenarioEditorFrame"', 1)):
            self.rejects(self.focused(path), "HTML_SRCDOC_UNSUPPORTED", path)

    def test_iframe_unregistered_element_is_rejected(self):
        path = "geometry-web/index.html"
        with self.change(path, lambda raw: raw.replace(b'<iframe id="scenarioEditorFrame"',
                                                       b'<iframe id="otherFrame"', 1)):
            self.rejects(self.focused(path), "HTML_EMBED_UNSUPPORTED", path)

    def test_iframe_non_host_route_is_rejected(self):
        source = self.config["htmlEmbedRoutes"][0]["source"]
        next(entry for entry in self.config["sources"] if entry["path"] == source)["layer"] = "K"
        self.rejects(self.focused(), "HTML_EMBED_ROUTE_LAYER", source)

    def test_iframe_driver_and_router_changes_require_review(self):
        route = self.config["htmlEmbedRoutes"][0]
        for key in ("driver", "router"):
            path = route[key]
            with self.subTest(source=path), self.change(path, lambda raw: raw + b"\n "):
                self.rejects(self.focused(), "HTML_EMBED_ROUTE_DIGEST", path)

    def test_iframe_reapproved_external_assignment_still_fails(self):
        route = self.config["htmlEmbedRoutes"][0]
        path = route["driver"]
        with self.change(path, lambda raw: raw.replace(b"'/?scenario='+context", b"'https://example.invalid/'+context", 1)) as changed:
            route["driverSha256"] = hashlib.sha256(changed.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            self.rejects(self.focused(), "HTML_EMBED_ASSIGNMENT", path)

    def test_iframe_external_manifest_prefix_still_fails(self):
        self.config["htmlEmbedRoutes"][0]["srcPrefix"] = "https://example.invalid/?scenario="
        self.rejects(self.focused(), "HTML_EMBED_ROUTE_SYNTAX", "geometry-web/index.html")


if __name__ == "__main__":
    unittest.main()
