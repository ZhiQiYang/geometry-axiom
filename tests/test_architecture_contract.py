"""Real temporary file trees for the generic GEO-261 dependency scanner.

No production manifest is fabricated here. These tests prove scanner behavior,
not that the current application is decoupled or that arbitrary dynamic code
has been statically verified. Run with ``python -B tests/test_architecture_contract.py``.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from architecture_contract import ContractError, LANGUAGES, SCHEMA, load_manifest, scan


class ArchitectureContract(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="geo261-architecture-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repo"
        (self.root / "src").mkdir(parents=True)
        self.manifest = {
            "schema": SCHEMA,
            "sourceRoots": ["src"],
            "searchRoots": {"c": ["src"], "python": ["src"], "javascript": ["src"]},
            "sources": [], "exclusions": [],
            "policy": {
                "cSystemHeaders": ["stdint.h", "stddef.h"],
                "pythonStdlib": ["math", "sys"],
                "javascriptBuiltins": ["node:assert"],
                "externalModules": [],
                "forbiddenIdentifiers": ["TIMBER_ROLE_PRIMARY", "WOODWORKING_FIXED_WIDTH"],
                "forbiddenStrings": ["calcium-silicate-6", "woodworking/1"],
                "forbiddenModules": {"c": ["woodworking_policy.h"], "python": ["woodworking"],
                                     "javascript": ["@geometry/woodworking"]},
            },
        }

    def put(self, relative, text="", layer="K", *, registered=True):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = text.encode("utf-8") if isinstance(text, str) else text
        path.write_bytes(raw)
        if registered:
            entry = {"path": relative, "layer": layer, "language": LANGUAGES[path.suffix.lower()],
                     "purpose": "Synthetic " + layer + " source used by this scanner test"}
            if layer == "vendor":
                entry["sha256"] = hashlib.sha256(raw).hexdigest()
            self.manifest["sources"].append(entry)
        return path

    def result(self):
        return scan(self.root, self.manifest)

    def green(self):
        result = self.result()
        self.assertTrue(result.ok, result.to_dict())
        return result

    def rejects(self, code, *, path=None, line=None, chain=None):
        result = self.result()
        self.assertFalse(result.ok, "scanner unexpectedly accepted the real source tree")
        matches = [item for item in result.diagnostics if item.code == code]
        self.assertTrue(matches, result.to_dict())
        if path is not None:
            matches = [item for item in matches if item.path == path]
        if line is not None:
            matches = [item for item in matches if item.line == line]
        if chain is not None:
            matches = [item for item in matches if item.chain == tuple(chain)]
        self.assertTrue(matches, result.to_dict())
        return matches[0]

    def test_clean_kw_h_composition_and_system_header(self):
        self.put("src/k/geometry.h", "#include <stdint.h>\nint boundary_area(int panel);\n")
        self.put("src/w/policy.h", '#include "../k/geometry.h"\n', "W")
        self.put("src/h/app.c", '#include "../w/policy.h"\n', "H")
        result = self.green()
        self.assertEqual([(edge.source, edge.target) for edge in result.edges],
                         [("src/h/app.c", "src/w/policy.h"), ("src/w/policy.h", "src/k/geometry.h")])

    def test_direct_c_template_include_is_rejected(self):
        self.put("src/k/core.c", '#include "../w/policy.h"\n')
        self.put("src/w/policy.h", "int policy;\n", "W")
        diagnostic = self.rejects("LAYER_DIRECTION", path="src/k/core.c", line=1,
                                  chain=["src/k/core.c", "src/w/policy.h"])
        self.assertEqual(diagnostic.direction, "K -> W")

    def test_indirect_c_helper_reports_complete_path(self):
        self.put("src/k/core.c", '#include "helper.h"\n')
        self.put("src/k/helper.h", '\n#include "../w/policy.h"\n')
        self.put("src/w/policy.h", "int policy;\n", "W")
        self.rejects("LAYER_DIRECTION", path="src/k/helper.h", line=2,
                     chain=["src/k/core.c", "src/k/helper.h", "src/w/policy.h"])

    def test_template_cannot_depend_on_host(self):
        self.put("src/w/policy.c", '#include "../h/host.h"\n', "W")
        self.put("src/h/host.h", "int host;\n", "H")
        self.assertEqual(self.rejects("LAYER_DIRECTION").direction, "W -> H")

    def test_imported_helper_outside_inventory_is_rejected(self):
        self.put("src/k/core.c", '#include "../../helpers/hidden.h"\n')
        self.put("helpers/hidden.h", "int hidden;\n", registered=False)
        self.rejects("DEPENDENCY_UNREGISTERED", path="src/k/core.c", line=1)

    def test_new_executable_cannot_be_omitted_from_manifest(self):
        self.put("src/k/core.c", "int core;\n")
        self.put("src/h/new_helper.py", "value = 1\n", registered=False)
        self.rejects("SOURCE_UNREGISTERED", path="src/h/new_helper.py")

    def test_duplicate_source_is_rejected(self):
        self.put("src/k/core.c", "int core;\n")
        self.manifest["sources"].append(deepcopy(self.manifest["sources"][0]))
        self.rejects("SOURCE_DUPLICATE")

    def test_missing_source_is_rejected(self):
        self.put("src/k/core.c", "int core;\n").unlink()
        self.rejects("SOURCE_MISSING", path="src/k/core.c")

    def test_extension_language_mismatch_is_rejected(self):
        self.put("src/k/core.py", "value = 1\n")
        self.manifest["sources"][0]["language"] = "c"
        self.rejects("SOURCE_LANGUAGE")

    def test_source_root_must_be_a_directory(self):
        self.put("src/k/core.c", "int core;\n")
        self.manifest["sourceRoots"] = ["src/k/core.c"]
        self.rejects("SOURCE_ROOT")

    def test_manifest_parent_escape_is_rejected(self):
        self.put("src/k/core.c", "int core;\n")
        self.manifest["sources"][0]["path"] = "../outside.c"
        self.rejects("ROOT_ESCAPE")

    def test_include_escape_is_rejected(self):
        self.put("src/k/core.c", '#include "../../../outside.h"\n')
        (self.root.parent / "outside.h").write_text("int outside;\n", encoding="utf-8")
        self.rejects("ROOT_ESCAPE", path="src/k/core.c", line=1)

    def test_symlink_escape_is_rejected(self):
        outside = self.root.parent / "outside.h"
        outside.write_text("int outside;\n", encoding="utf-8")
        try:
            (self.root / "src/link.h").symlink_to(outside)
        except OSError as error:
            self.skipTest(f"real symlink creation unavailable: {error}")
        self.rejects("ROOT_ESCAPE", path="src/link.h")

    def test_conditional_include_is_not_ignored(self):
        self.put("src/k/core.c", '#if 0\n#include "../w/policy.h"\n#endif\n')
        self.put("src/w/policy.h", "int policy;\n", "W")
        self.rejects("LAYER_DIRECTION", path="src/k/core.c", line=2)

    def test_c_macro_include_fails_closed(self):
        self.put("src/k/core.c", '#define HEADER "neutral.h"\n#include HEADER\n')
        self.put("src/neutral.h", "int neutral;\n")
        self.rejects("C_DYNAMIC_INCLUDE", path="src/k/core.c", line=2)

    def test_c_include_resolution_must_not_be_ambiguous(self):
        self.put("src/k/core.c", '#include "neutral.h"\n')
        self.put("src/neutral.h", "int neutral;\n")
        self.put("src/other/neutral.h", "int another;\n")
        self.manifest["searchRoots"]["c"].append("src/other")
        self.rejects("DEPENDENCY_AMBIGUOUS", path="src/k/core.c")

    def test_unapproved_system_header_is_rejected(self):
        self.put("src/k/core.c", "#include <unlisted.h>\n")
        self.rejects("DEPENDENCY_UNRESOLVED")

    def test_concrete_template_enum_is_rejected(self):
        self.put("src/k/core.c", "\nint role = TIMBER_ROLE_PRIMARY;\n")
        self.rejects("FORBIDDEN_IDENTIFIER", path="src/k/core.c", line=2)

    def test_concrete_material_string_is_rejected(self):
        self.put("src/k/core.c", 'const char *kind = "calcium-silicate-6";\n')
        self.rejects("FORBIDDEN_STRING", path="src/k/core.c", line=1)

    def test_c_adjacent_prefixed_literals_are_decoded_together(self):
        self.put("src/k/core.c", 'const char *kind = "calcium-" /* keep separation */ u8"silicate-6";\n')
        self.rejects("FORBIDDEN_STRING")

    def test_neutral_words_and_forbidden_comments_are_accepted(self):
        self.put("src/k/core.c", '/* TIMBER_ROLE_PRIMARY and "calcium-silicate-6" */\nint boundary(int panel);\n')
        self.green()

    def test_comment_removal_does_not_join_c_identifiers(self):
        self.put("src/k/core.c", "typedef int TIMBER_ROLE_;\nTIMBER_ROLE_/**/PRIMARY;\n")
        self.green()

    def test_crlf_comments_preserve_physical_line_numbers(self):
        self.put("src/k/core.c", b'/* first\r\n second */\r\n#include "../w/policy.h"\r\n')
        self.put("src/w/policy.h", "int policy;\n", "W")
        self.rejects("LAYER_DIRECTION", path="src/k/core.c", line=3)

    def test_c_line_splicing_cannot_hide_include_or_identifier(self):
        path = self.put("src/k/core.c", '#inc\\\nlude "../w/policy.h"\n')
        self.put("src/w/policy.h", "int policy;\n", "W")
        self.rejects("LAYER_DIRECTION", path="src/k/core.c", line=1)
        path.write_text("int role = TIMBER_RO\\\nLE_PRIMARY;\n", encoding="utf-8")
        self.rejects("FORBIDDEN_IDENTIFIER", path="src/k/core.c", line=1)

    def test_locked_vendor_is_exact_and_transitively_scanned(self):
        self.put("src/k/core.c", '#include "../vendor/exact.h"\n')
        vendor = self.put("src/vendor/exact.h", "int exact;\n", "vendor")
        self.green()
        vendor.write_text("int changed;\n", encoding="utf-8")
        self.rejects("VENDOR_DIGEST")

    def test_vendor_cannot_launder_a_template_dependency(self):
        self.put("src/k/core.c", '#include "../vendor/exact.h"\n')
        self.put("src/vendor/exact.h", '#include "../w/policy.h"\n', "vendor")
        self.put("src/w/policy.h", "int policy;\n", "W")
        self.rejects("LAYER_DIRECTION", chain=["src/k/core.c", "src/vendor/exact.h", "src/w/policy.h"])

    def test_exact_exclusion_is_locked_and_cannot_be_imported(self):
        omitted = self.put("src/generated_demo.py", "value = 1\n", registered=False)
        self.manifest["exclusions"].append({"path": "src/generated_demo.py", "reason": "Non-product generated example",
                                            "sha256": hashlib.sha256(omitted.read_bytes()).hexdigest()})
        self.green()
        self.put("src/core.py", "import generated_demo\n")
        self.rejects("DEPENDENCY_EXCLUDED")

    def test_python_direct_alias_import_follows_real_module(self):
        self.put("src/k/core.py", "import w.policy as p\n")
        self.put("src/w/__init__.py", "")
        self.put("src/w/policy.py", "value = 1\n", "W")
        self.rejects("LAYER_DIRECTION", path="src/k/core.py", line=1,
                     chain=["src/k/core.py", "src/w/policy.py"])

    def test_python_relative_package_import_follows_helper(self):
        self.put("src/k/__init__.py", "")
        self.put("src/k/core.py", "from . import helper as h\n")
        self.put("src/k/helper.py", "value = 1\n", "W")
        self.rejects("LAYER_DIRECTION", chain=["src/k/core.py", "src/k/helper.py"])

    def test_python_package_initializer_is_in_dependency_graph(self):
        self.put("src/core.py", "import pkg.neutral\n")
        self.put("src/pkg/__init__.py", "", "H")
        self.put("src/pkg/neutral.py", "value = 1\n")
        self.rejects("LAYER_DIRECTION", chain=["src/core.py", "src/pkg/__init__.py"])

    def test_python_namespace_package_fails_closed(self):
        self.put("src/core.py", "import pkg.neutral\n")
        self.put("src/pkg/neutral.py", "value = 1\n")
        self.rejects("PYTHON_PACKAGE")

    def test_python_stdlib_allowance_does_not_hide_local_shadow(self):
        self.put("src/core.py", "import math\n")
        self.put("src/math.py", "value = 1\n", "W")
        self.rejects("LAYER_DIRECTION", chain=["src/core.py", "src/math.py"])

    def test_python_dynamic_import_alias_is_rejected(self):
        self.put("src/core.py", 'import importlib as loader\nloader.import_module("w.policy")\n')
        self.manifest["policy"]["pythonStdlib"].append("importlib")
        self.rejects("CORE_DYNAMIC_IMPORT", path="src/core.py", line=1)

    def test_python_from_loader_alias_is_rejected(self):
        self.put("src/core.py", 'from importlib import import_module as load\nload("w.policy")\n')
        self.rejects("CORE_DYNAMIC_IMPORT", path="src/core.py", line=1)

    def test_python_sys_path_alias_injection_is_rejected(self):
        self.put("src/core.py", 'import sys as system\nalias = system\nalias.path.insert(0, "w")\nimport math as system\n')
        self.rejects("CORE_PATH_INJECTION", path="src/core.py", line=3)

    def test_python_from_sys_path_alias_is_rejected(self):
        self.put("src/core.py", 'from sys import path as paths\npaths.append("w")\n')
        self.rejects("CORE_PATH_INJECTION", path="src/core.py", line=1)

    def test_python_builtin_loader_escape_is_rejected(self):
        self.put("src/core.py", '__builtins__["__import__"]("w.policy")\n')
        self.rejects("CORE_DYNAMIC_IMPORT", path="src/core.py", line=1)

    def test_python_strings_and_names_use_precise_template_policy(self):
        path = self.put("src/core.py", 'value = "woodworking/1"\n')
        self.rejects("FORBIDDEN_STRING")
        path.write_text("TIMBER_ROLE_PRIMARY = 1\n", encoding="utf-8")
        self.rejects("FORBIDDEN_IDENTIFIER")
        path.write_text("# TIMBER_ROLE_PRIMARY\nboundary = 'panel'\n", encoding="utf-8")
        self.green()

    def test_declaring_third_party_as_python_stdlib_is_rejected(self):
        self.put("src/core.py", "value = 1\n")
        self.manifest["policy"]["pythonStdlib"].append("geometry_external_fake")
        self.rejects("EXTERNAL_POLICY")

    def test_explicit_host_external_allowance_does_not_allow_core(self):
        self.put("src/app.py", "import external_provider\n", "H")
        self.manifest["policy"]["externalModules"].append({"language": "python", "name": "external_provider",
                                                            "layers": ["H"], "purpose": "Host integration"})
        self.green()
        self.manifest["sources"][0]["layer"] = "K"
        self.rejects("DEPENDENCY_UNRESOLVED")

    def test_scanner_never_executes_python_source(self):
        self.put("src/core.py", "import neutral\n")
        self.put("src/neutral.py", 'raise RuntimeError("must not execute")\n')
        self.green()

    def test_javascript_literal_import_require_and_reexport(self):
        self.put("src/neutral.js", "export const value = 1;\n")
        source = self.put("src/core.js", "")
        forms = [
            "import './neutral.js';", "import value from './neutral.js';",
            "import {value as v} from './neutral.js';", "import * as all from './neutral.js';",
            "import value, {value as v} from './neutral.js';", "const value = require('./neutral.js');",
            "export {value as v} from './neutral.js';", "export * from './neutral.js';",
            "export * as all from './neutral.js';",
        ]
        for code in forms:
            with self.subTest(code=code):
                source.write_text(code + "\n", encoding="utf-8")
                result = self.green()
                self.assertTrue(any(edge.target == "src/neutral.js" for edge in result.edges))

    def test_javascript_template_dependency_is_rejected(self):
        self.put("src/core.js", "const policy = require('./w/policy.js');\n")
        self.put("src/w/policy.js", "module.exports = {};\n", "W")
        self.rejects("LAYER_DIRECTION", path="src/core.js", line=1)

    def test_javascript_dynamic_import_and_require_alias_fail_closed(self):
        path = self.put("src/core.js", "import('./w/policy.js');\n")
        self.rejects("JS_DYNAMIC_IMPORT")
        path.write_text("const load = require; load('./w/policy.js');\n", encoding="utf-8")
        self.rejects("JS_DYNAMIC_IMPORT")

    def test_javascript_unsupported_import_bindings_fail_closed(self):
        path = self.put("src/core.js", "import {value from './neutral.js';\n")
        self.put("src/neutral.js", "export const value = 1;\n")
        self.rejects("JS_IMPORT_SYNTAX")
        path.write_text("import './neutral.js'\nwith {type: 'json'};\n", encoding="utf-8")
        self.rejects("JS_IMPORT_SYNTAX")

    def test_javascript_interpolated_template_cannot_hide_loader(self):
        self.put("src/core.js", "const x = `${require('./w.js')}`;\n")
        self.rejects("JS_TEMPLATE_EXPRESSION")

    def test_typescript_type_import_is_tracked(self):
        self.put("src/core.ts", "import type {Size as S} from './types';\n")
        self.put("src/types.ts", "export type Size = number;\n", "W")
        self.rejects("LAYER_DIRECTION", chain=["src/core.ts", "src/types.ts"])

    def test_typescript_type_reexport_is_tracked(self):
        self.put("src/core.ts", "export type {Size} from './types';\n")
        self.put("src/types.ts", "export type Size = number;\n", "W")
        self.rejects("LAYER_DIRECTION", chain=["src/core.ts", "src/types.ts"])

    def test_jsx_is_inventoried_and_never_silently_accepted(self):
        self.put("src/view.jsx", "export const x = <div />;\n", registered=False)
        self.rejects("SOURCE_UNREGISTERED")
        self.manifest["sources"].append({"path": "src/view.jsx", "layer": "H", "language": "jsx", "purpose": "View"})
        self.rejects("UNSUPPORTED_LANGUAGE")

    def test_html_script_src_is_a_real_dependency(self):
        self.put("src/k/page.html", '<html>\n<script src="../w/policy.js"></script>\n</html>\n')
        self.put("src/w/policy.js", "const value = 1;\n", "W")
        self.rejects("LAYER_DIRECTION", path="src/k/page.html", line=2)

    def test_html_inline_script_keeps_document_line_numbers(self):
        self.put("src/k/page.html", '<html>\n<script type="module">\nimport "../w/policy.js";\n</script>\n</html>\n')
        self.put("src/w/policy.js", "const value = 1;\n", "W")
        self.rejects("LAYER_DIRECTION", path="src/k/page.html", line=3)

    def test_html_event_attribute_is_scanned(self):
        self.put("src/k/page.html", '<html>\n<button onclick="require(\'../w/policy.js\')">go</button>\n</html>\n')
        self.put("src/w/policy.js", "const value = 1;\n", "W")
        self.rejects("LAYER_DIRECTION", path="src/k/page.html", line=2)

    def test_html_data_script_is_data_but_import_map_is_unsupported(self):
        path = self.put("src/page.html", '<script type="application/json">{"text":"import w"}</script>\n')
        self.green()
        path.write_text('<script type="importmap">{}</script>\n', encoding="utf-8")
        self.rejects("HTML_SCRIPT_TYPE")

    def test_duplicate_json_key_is_rejected(self):
        path = self.root / "manifest.json"
        path.write_text('{"schema":"one","schema":"two"}', encoding="utf-8")
        with self.assertRaises(ContractError) as caught:
            load_manifest(path)
        self.assertEqual(caught.exception.diagnostic.code, "MANIFEST_DUPLICATE_KEY")

    def test_manifest_order_does_not_change_diagnostics_or_graph(self):
        self.put("src/k/core.c", '#include "../w/policy.h"\n')
        self.put("src/w/policy.h", '#include "../h/host.h"\n', "W")
        self.put("src/h/host.h", "int host;\n", "H")
        first = self.result().to_dict()
        self.manifest["sources"].reverse()
        self.assertEqual(first, self.result().to_dict())

    def test_scanner_leaves_every_input_byte_unchanged(self):
        self.put("src/core.py", "import math\nvalue = math.pi\n")
        before = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.green()
        after = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
