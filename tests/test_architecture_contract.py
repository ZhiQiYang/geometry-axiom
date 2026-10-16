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

    def test_standalone_source_file_is_inventoried(self):
        self.put("entry.c", '#include "src/helper.h"\n')
        self.put("src/helper.h", "int helper;\n")
        self.manifest["sourceFiles"] = ["entry.c"]
        self.assertEqual(self.green().edges[0].target, "src/helper.h")

    def test_standalone_source_cannot_be_unregistered(self):
        self.put("entry.c", "int entry;\n", registered=False)
        self.manifest["sourceFiles"] = ["entry.c"]
        self.rejects("SOURCE_UNREGISTERED", path="entry.c")

    def test_standalone_source_cannot_overlap_root(self):
        self.put("src/core.c", "int core;\n")
        self.manifest["sourceFiles"] = ["src/core.c"]
        self.rejects("MANIFEST_SCHEMA")

    def test_standalone_source_must_exist_and_be_executable(self):
        self.manifest["sourceFiles"] = ["missing.c"]
        self.rejects("SOURCE_ROOT")
        self.put("readme.md", "documentation", registered=False)
        self.manifest["sourceFiles"] = ["readme.md"]
        self.rejects("SOURCE_ROOT")

    def test_standalone_source_parent_escape_is_rejected(self):
        self.manifest["sourceFiles"] = ["../outside.c"]
        self.rejects("ROOT_ESCAPE")

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

    def test_unknown_c_header_cannot_be_declared_standard(self):
        self.put("src/core.c", "int core;\n")
        self.manifest['policy']['cSystemHeaders'].append('unknown_vendor.h')
        self.rejects("EXTERNAL_POLICY")

    def test_platform_c_header_cannot_be_declared_standard(self):
        self.put("src/core.c", "int core;\n")
        self.manifest['policy']['cSystemHeaders'].append('windows.h')
        self.rejects("EXTERNAL_POLICY")

    def test_explicit_host_platform_header_does_not_allow_core(self):
        self.put("src/host.c", "#include <windows.h>\n", "H")
        self.manifest['policy']['externalModules'].append({'language': 'c', 'name': 'windows.h',
            'layers': ['H'], 'purpose': 'Host Win32 platform integration'})
        self.green()
        self.manifest['sources'][0]['layer'] = 'K'
        self.rejects("DEPENDENCY_UNRESOLVED")

    def test_host_platform_header_cannot_launder_through_core_helper(self):
        self.put("src/core.c", '#include "helper.h"\n')
        self.put("src/helper.h", "#include <windows.h>\n")
        self.manifest['policy']['externalModules'].append({'language': 'c', 'name': 'windows.h',
            'layers': ['H'], 'purpose': 'Host Win32 platform integration'})
        self.rejects("DEPENDENCY_UNRESOLVED", path='src/helper.h')

    def test_host_platform_allowance_is_exact_not_prefix(self):
        self.put("src/host.c", "#include <windows.h/other.h>\n", "H")
        self.manifest['policy']['externalModules'].append({'language': 'c', 'name': 'windows.h',
            'layers': ['H'], 'purpose': 'Host Win32 platform integration'})
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
        self.put("src/h/host.c", '#include "../vendor/exact.h"\n', "H")
        vendor = self.put("src/vendor/exact.h", "int exact;\n", "vendor")
        self.green()
        vendor.write_text("int changed;\n", encoding="utf-8")
        self.rejects("VENDOR_DIGEST")

    def test_vendor_cannot_launder_a_template_dependency(self):
        self.put("src/h/host.c", '#include "../vendor/exact.h"\n', "H")
        self.put("src/vendor/exact.h", '#include "../w/policy.h"\n', "vendor")
        self.put("src/w/policy.h", "int policy;\n", "W")
        self.rejects("LAYER_DIRECTION", chain=["src/vendor/exact.h", "src/w/policy.h"])

    def test_core_cannot_depend_on_even_digest_locked_vendor(self):
        self.put("src/k/core.c", '#include "../vendor/exact.h"\n')
        self.put("src/vendor/exact.h", "int exact;\n", "vendor")
        self.rejects("LAYER_DIRECTION", chain=["src/k/core.c", "src/vendor/exact.h"])

    def test_core_helper_cannot_launder_vendor(self):
        self.put("src/k/core.c", '#include "helper.h"\n')
        self.put("src/k/helper.h", '#include "../vendor/exact.h"\n')
        self.put("src/vendor/exact.h", "int exact;\n", "vendor")
        self.rejects("LAYER_DIRECTION", chain=["src/k/core.c", "src/k/helper.h", "src/vendor/exact.h"])

    def test_exact_exclusion_is_locked_and_cannot_be_imported(self):
        omitted = self.put("src/generated_demo.py", "value = 1\n", registered=False)
        self.manifest["exclusions"].append({"path": "src/generated_demo.py", "reason": "Non-product generated example",
                                            "sha256": hashlib.sha256(omitted.read_bytes()).hexdigest()})
        self.green()
        self.put("src/core.py", "import generated_demo\n")
        self.rejects("DEPENDENCY_EXCLUDED")

    def exclude_text(self, raw=b"value = 1\r\n", mode="lf"):
        omitted = self.put("src/omitted.py", raw, registered=False)
        digest_bytes = raw.replace(b"\r\n", b"\n") if mode == "lf" else raw
        entry = {"path": "src/omitted.py", "reason": "Synthetic excluded text", "sha256": hashlib.sha256(digest_bytes).hexdigest()}
        if mode is not None:
            entry['hashMode'] = mode
        self.manifest['exclusions'].append(entry)
        return omitted, entry

    def test_lf_exclusion_same_content_accepts_crlf_and_lf(self):
        omitted, _ = self.exclude_text()
        self.green()
        omitted.write_bytes(b"value = 1\n")
        self.green()

    def test_lf_exclusion_changed_character_is_rejected(self):
        omitted, _ = self.exclude_text()
        self.green()
        omitted.write_bytes(b"value = 2\r\n")
        self.rejects("EXCLUSION_DIGEST")

    def test_raw_exclusion_remains_byte_exact_by_default(self):
        omitted, _ = self.exclude_text(mode=None)
        self.green()
        omitted.write_bytes(b"value = 1\n")
        self.rejects("EXCLUSION_DIGEST")

    def test_exclusion_rejects_unknown_hash_mode(self):
        self.exclude_text(mode="text")
        self.rejects("EXCLUSION_HASH_MODE")

    def test_lf_exclusion_cannot_be_imported(self):
        self.exclude_text()
        self.put("src/core.py", "import omitted\n")
        self.rejects("DEPENDENCY_EXCLUDED")

    def test_lf_exclusion_preserves_bare_carriage_return(self):
        omitted, _ = self.exclude_text(raw=b"value = 1\rvalue = 2\r\n")
        self.green()
        omitted.write_bytes(b"value = 1\nvalue = 2\n")
        self.rejects("EXCLUSION_DIGEST")

    def test_vendor_cannot_choose_any_hash_mode(self):
        self.put("src/vendor/exact.h", "int exact;\n", "vendor")
        for mode in ['lf', 'raw']:
            with self.subTest(mode=mode):
                self.manifest['sources'][0]['hashMode'] = mode
                self.rejects("MANIFEST_SCHEMA")

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

    def test_python_relative_package_root_ignores_nonmodule_parent(self):
        self.put("src/project-core/k/__init__.py", "")
        self.put("src/project-core/k/core.py", "from . import helper\n")
        self.put("src/project-core/k/helper.py", "value = 1\n")
        self.manifest["searchRoots"]["python"] = [".", "src/project-core"]
        self.assertTrue(any(edge.target.endswith('/helper.py') for edge in self.green().edges))

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
        self.rejects("LEXICAL_SYNTAX")
        path.write_text("import './neutral.js'\nwith {type: 'json'};\n", encoding="utf-8")
        self.rejects("JS_IMPORT_SYNTAX")

    def test_javascript_interpolated_template_cannot_hide_loader(self):
        self.put("src/core.js", "const x = `${require('./w.js')}`;\n")
        self.put("src/w.js", "export const policy = 1;\n", "W")
        self.rejects("LAYER_DIRECTION", chain=["src/core.js", "src/w.js"])

    def test_javascript_nested_template_tracks_dependency(self):
        self.put("src/core.js", "const x = `outer ${`inner ${require('./w.js')}`} tail`;\n")
        self.put("src/w.js", "export const policy = 1;\n", "W")
        self.rejects("LAYER_DIRECTION", chain=["src/core.js", "src/w.js"])

    def test_javascript_template_keeps_transitive_closure(self):
        self.put("src/core.js", "const x = `${require('./helper.js')}`;\n")
        self.put("src/helper.js", "const x = `${`nested ${require('./w.js')}`}`;\n")
        self.put("src/w.js", "export const policy = 1;\n", "W")
        self.rejects("LAYER_DIRECTION", chain=["src/core.js", "src/helper.js", "src/w.js"])

    def test_javascript_host_template_still_tracks_dependency(self):
        self.put("src/host.js", "const x = `${require('./w.js')}`;\n", "H")
        self.put("src/w.js", "export const policy = 1;\n", "W")
        result = self.green()
        self.assertEqual([(edge.source, edge.target) for edge in result.edges], [("src/host.js", "src/w.js")])

    def test_javascript_template_dynamic_loaders_fail_closed(self):
        path = self.put("src/core.js", "")
        for expression in ["import('./w.js')", "require(name)", "require(`./${name}.js`)",
                           "(() => {const load = require; return load(name);})()", "eval(code)",
                           "object[`require`](name)"]:
            with self.subTest(expression=expression):
                path.write_text("const x = `${" + expression + "}`;\n", encoding="utf-8")
                self.rejects("JS_DYNAMIC_IMPORT")

    def test_javascript_template_forbidden_identifier_is_executable(self):
        self.put("src/core.js", "const x = `${`inner ${TIMBER_ROLE_PRIMARY}`}`;\n")
        self.rejects("FORBIDDEN_IDENTIFIER")

    def test_javascript_template_forbidden_string_is_executable(self):
        self.put("src/core.js", "const x = `${'calcium-silicate-6'}`;\n")
        self.rejects("FORBIDDEN_STRING")

    def test_javascript_template_display_words_are_not_code(self):
        self.put("src/core.js", "const x = `require('./w.js') import('./w.js') TIMBER_ROLE_PRIMARY ${'TIMBER_ROLE_PRIMARY'}`;\n")
        self.assertEqual(self.green().edges, [])

    def test_javascript_template_chunks_do_not_expand_exact_string_policy(self):
        self.put("src/core.js", "const x = `calcium-silicate-6${value}`;\n")
        self.green()

    def test_javascript_escaped_interpolation_is_literal(self):
        self.put("src/core.js", r"const x = `\${require('./missing.js')}`;" + "\n")
        self.assertEqual(self.green().edges, [])

    def test_javascript_even_backslashes_do_not_hide_interpolation(self):
        self.put("src/core.js", r"const x = `\\${require('./w.js')}`;" + "\n")
        self.put("src/w.js", "export const policy = 1;\n", "W")
        self.rejects("LAYER_DIRECTION")

    def test_javascript_template_braces_in_string_comment_and_nested_template(self):
        self.put("src/core.js", "const x = `${({a:'}', b:'{', c:`safe ${value}`, d:/* } */ require('./w.js')}).d}`;\n")
        self.put("src/w.js", "export const policy = 1;\n", "W")
        self.rejects("LAYER_DIRECTION")

    def test_javascript_template_comment_keeps_physical_line(self):
        self.put("src/core.js", "const x = `first\n${(() => { // }\n return require('./w.js');\n})()}`;\n")
        self.put("src/w.js", "export const policy = 1;\n", "W")
        self.rejects("LAYER_DIRECTION", path="src/core.js", line=3)

    def test_javascript_template_regex_braces_are_not_delimiters(self):
        path = self.put("src/core.js", "")
        self.put("src/w.js", "export const policy = 1;\n", "W")
        for pattern in [r"/[}]/", r"/\}/", r"/[/*]/"]:
            with self.subTest(pattern=pattern):
                path.write_text("const x = `${" + pattern + ".test(value) ? require('./w.js') : ''}`;\n", encoding="utf-8")
                self.rejects("LAYER_DIRECTION")

    def test_javascript_regex_comment_cannot_swallow_dependency(self):
        self.put("src/core.js", "const x = /[/*]/; require('./w.js'); // */\n")
        self.put("src/w.js", "export const policy = 1;\n", "W")
        self.rejects("LAYER_DIRECTION")

    def test_javascript_template_regex_comment_cannot_swallow_dependency(self):
        self.put("src/core.js", "const x = `${(() => {const r = /[/*]/; require('./w.js'); // */\nreturn '';})()}`;\n")
        self.put("src/w.js", "export const policy = 1;\n", "W")
        self.rejects("LAYER_DIRECTION")

    def test_javascript_division_does_not_hide_later_loader(self):
        path = self.put("src/core.js", "")
        self.put("src/w.js", "export const policy = 1;\n", "W")
        for expression in ["a / b / require('./w.js')", "a++ / b / require('./w.js')",
                           "(a + b) / require('./w.js')", "obj.value / require('./w.js')"]:
            with self.subTest(expression=expression):
                path.write_text("const x = `${" + expression + "}`;\n", encoding="utf-8")
                self.rejects("LAYER_DIRECTION")

    def test_javascript_reserved_property_names_are_not_regex_prefixes(self):
        path = self.put("src/core.js", "")
        self.put("src/w.js", "export const policy = 1;\n", "W")
        for expression in ["obj.return / require('./w.js') / x", "obj.if(x) / require('./w.js') / x",
                           "obj.await / require('./w.js') / x"]:
            with self.subTest(expression=expression):
                path.write_text("const x = `${" + expression + "}`;\n", encoding="utf-8")
                self.rejects("LAYER_DIRECTION")

    def test_javascript_ambiguous_regex_goal_fails_closed(self):
        path = self.put("src/core.js", "")
        for expression in ["yield / require('w') / x", "await / require('w') / x", "{} / require('w') / x"]:
            with self.subTest(expression=expression):
                path.write_text("const x = `${" + expression + "}`;\n", encoding="utf-8")
                self.rejects("JS_REGEX_SYNTAX")

    def test_javascript_control_condition_accepts_regex_statement(self):
        self.put("src/core.js", "if (ready) /[/*]/.test(value); require('./w.js'); // */\n")
        self.put("src/w.js", "export const policy = 1;\n", "W")
        self.rejects("LAYER_DIRECTION")

    def test_javascript_regex_display_words_are_not_code(self):
        self.put("src/core.js", r"const x = `${/require\('missing'\)|TIMBER_ROLE_PRIMARY/.test(value)}`;" + "\n")
        self.assertEqual(self.green().edges, [])

    def test_javascript_unclosed_templates_fail_closed(self):
        path = self.put("src/core.js", "")
        for text in ["const x = `unclosed", "const x = `${value", "const x = `${`nested ${value}`",
                     "const x = `${({value: 1})`", "const x = `${/[}]/.test(value)"]:
            with self.subTest(text=text):
                path.write_text(text, encoding="utf-8")
                self.rejects("LEXICAL_SYNTAX")

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

    def route(self, source="src/page.html", src="/templates/woodworking.js", target="src/w/frontend.js"):
        route = {"source": source, "src": src, "target": target, "purpose": "Host serves a reviewed frontend route"}
        self.manifest.setdefault("htmlScriptRoutes", []).append(route)
        return route

    def test_html_exact_host_route_is_an_owned_edge(self):
        self.put("src/page.html", '<script src="/templates/woodworking.js"></script>\n', "H")
        self.put("src/w/frontend.js", "const value = 1;\n", "W")
        self.route()
        self.assertEqual(self.green().edges[0].target, "src/w/frontend.js")

    def test_html_relative_host_route_takes_precedence_over_file_resolution(self):
        self.put("src/page.html", '<script src="templates/woodworking.js"></script>\n', "H")
        self.put("src/templates/woodworking.js", "const local = 1;\n", "H")
        self.put("src/w/frontend.js", "const routed = 1;\n", "W")
        self.route(src="templates/woodworking.js")
        self.assertEqual([edge.target for edge in self.green().edges], ["src/w/frontend.js"])

    def test_html_host_route_cannot_bypass_layer_direction(self):
        self.put("src/page.html", '<script src="/templates/woodworking.js"></script>\n')
        self.put("src/w/frontend.js", "const value = 1;\n", "W")
        self.route()
        self.rejects("LAYER_DIRECTION", chain=["src/page.html", "src/w/frontend.js"])

    def test_html_host_route_keeps_transitive_closure(self):
        self.put("src/page.html", '<script src="/templates/woodworking.js"></script>\n')
        self.put("src/w/frontend.js", "require('./policy.js');\n")
        self.put("src/w/policy.js", "const value = 1;\n", "W")
        self.route()
        self.rejects("LAYER_DIRECTION", chain=["src/page.html", "src/w/frontend.js", "src/w/policy.js"])

    def test_html_root_route_must_be_mapped(self):
        self.put("src/page.html", '<script src="/w/frontend.js"></script>\n', "H")
        self.put("src/w/frontend.js", "const value = 1;\n", "W")
        self.rejects("HTML_ROUTE_UNMAPPED")

    def test_html_route_is_scoped_to_exact_source(self):
        self.put("src/page.html", '<script src="/templates/woodworking.js"></script>\n', "H")
        self.put("src/other.html", '<script src="/templates/woodworking.js"></script>\n', "H")
        self.put("src/w/frontend.js", "const value = 1;\n", "W")
        self.route()
        self.rejects("HTML_ROUTE_UNMAPPED", path="src/other.html")

    def test_html_route_duplicate_is_rejected(self):
        self.put("src/page.html", "", "H")
        self.put("src/w/frontend.js", "const value = 1;\n", "W")
        self.route()
        self.route()
        self.rejects("HTML_ROUTE_DUPLICATE")

    def test_html_route_unknown_target_is_rejected(self):
        self.put("src/page.html", "", "H")
        self.route()
        self.rejects("HTML_ROUTE_TARGET")

    def test_html_route_unknown_source_is_rejected(self):
        self.put("src/w/frontend.js", "const value = 1;\n", "W")
        self.route()
        self.rejects("HTML_ROUTE_SOURCE")

    def test_html_route_does_not_accept_prefix_match(self):
        self.put("src/page.html", '<script src="/templates/woodworking.js/extra.js"></script>\n', "H")
        self.put("src/w/frontend.js", "const value = 1;\n", "W")
        self.route()
        self.rejects("HTML_ROUTE_UNMAPPED")

    def test_html_route_cannot_target_excluded_code(self):
        self.put("src/page.html", "", "H")
        omitted = self.put("src/w/frontend.js", "const value = 1;\n", registered=False)
        self.manifest["exclusions"].append({"path": "src/w/frontend.js", "reason": "Synthetic excluded example",
                                            "sha256": hashlib.sha256(omitted.read_bytes()).hexdigest()})
        self.route()
        self.rejects("HTML_ROUTE_TARGET")

    def import_route(self, source="src/host.js", specifier="/vendor/lib.js", target="src/vendor/lib.js"):
        route = {"source": source, "specifier": specifier, "target": target, "purpose": "Exact host lazy module route"}
        self.manifest.setdefault("javascriptImportRoutes", []).append(route)
        return route

    def trusted_bundle(self, files=None):
        bundle = {"id": "browser-library", "files": files or ["src/vendor/lib.js"], "layers": ["H"],
                  "purpose": "Reviewed immutable browser library; its internal runtime behavior is explicitly trusted"}
        self.manifest.setdefault("trustedVendorBundles", []).append(bundle)
        return bundle

    def test_host_literal_import_route_is_an_owned_edge_inside_template(self):
        self.put("src/host.js", "const x = `${await import('/vendor/lib.js')}`;\n", "H")
        self.put("src/vendor/lib.js", "globalThis.library = {};\n", "vendor")
        self.import_route()
        self.trusted_bundle()
        result = self.green()
        self.assertEqual([edge.target for edge in result.edges], ["src/vendor/lib.js"])
        self.assertEqual(result.to_dict()["trustedSourcesNotParsed"], ["src/vendor/lib.js"])

    def test_host_computed_import_still_fails_with_route(self):
        path = self.put("src/host.js", "", "H")
        self.put("src/vendor/lib.js", "globalThis.library = {};\n", "vendor")
        self.import_route()
        self.trusted_bundle()
        for expression in ["import(prefix + '/vendor/lib.js')", "import(`/vendor/${name}.js`)",
                           "import('/vendor/lib.js', {with: {type: 'json'}})"]:
            with self.subTest(expression=expression):
                path.write_text(expression + ';\n', encoding='utf-8')
                self.rejects("JS_DYNAMIC_IMPORT")

    def test_host_unmapped_literal_import_is_rejected(self):
        self.put("src/host.js", "import('/vendor/lib.js');\n", "H")
        self.put("src/vendor/lib.js", "globalThis.library = {};\n", "vendor")
        self.trusted_bundle()
        self.rejects("JS_DYNAMIC_IMPORT")

    def test_host_import_route_does_not_apply_to_other_source(self):
        self.put("src/host.js", "", "H")
        self.put("src/other.js", "import('/vendor/lib.js');\n", "H")
        self.put("src/vendor/lib.js", "globalThis.library = {};\n", "vendor")
        self.import_route()
        self.trusted_bundle()
        self.rejects("JS_DYNAMIC_IMPORT", path="src/other.js")

    def test_import_route_cannot_be_declared_for_core(self):
        self.put("src/host.js", "import('/vendor/lib.js');\n")
        self.put("src/vendor/lib.js", "const value = 1;\n", "vendor")
        self.import_route()
        self.rejects("JS_ROUTE_SOURCE")

    def test_import_route_duplicate_and_unknown_target_are_rejected(self):
        self.put("src/host.js", "", "H")
        self.put("src/vendor/lib.js", "const value = 1;\n", "vendor")
        route = self.import_route()
        self.import_route()
        self.rejects("JS_ROUTE_DUPLICATE")
        self.manifest['javascriptImportRoutes'].pop()
        route['target'] = 'src/unknown.js'
        self.rejects("JS_ROUTE_TARGET")

    def test_import_route_parent_escape_is_rejected(self):
        self.put("src/host.js", "", "H")
        route = self.import_route(target="../outside.js")
        self.rejects("ROOT_ESCAPE")
        route['target'] = 'src/vendor/lib.js'
        route['specifier'] = '/../outside.js'
        self.rejects("ROOT_ESCAPE")

    def test_trusted_vendor_cannot_be_reached_by_core_or_template(self):
        self.put("src/core.js", "require('./helper.js');\n")
        self.put("src/helper.js", "require('./vendor/lib.js');\n")
        self.put("src/w.js", "require('./vendor/lib.js');\n", "W")
        self.put("src/vendor/lib.js", "globalThis.library = {};\n", "vendor")
        self.trusted_bundle()
        self.rejects("LAYER_DIRECTION", chain=['src/core.js', 'src/helper.js', 'src/vendor/lib.js'])
        self.rejects("LAYER_DIRECTION", chain=['src/w.js', 'src/vendor/lib.js'])

    def test_vendor_globals_are_not_trusted_without_explicit_bundle(self):
        self.put("src/vendor/lib.js", "globalThis.library = {};\n", "vendor")
        self.rejects("JS_DYNAMIC_IMPORT")

    def test_trusted_vendor_digest_is_still_mandatory_and_current(self):
        vendor = self.put("src/vendor/lib.js", "globalThis.library = {};\n", "vendor")
        self.trusted_bundle()
        self.green()
        vendor.write_text("globalThis.changed = {};\n", encoding="utf-8")
        self.rejects("VENDOR_DIGEST")
        del self.manifest['sources'][0]['sha256']
        self.rejects("VENDOR_DIGEST")

    def test_trusted_vendor_file_cannot_be_missing(self):
        self.put("src/vendor/lib.js", "globalThis.library = {};\n", "vendor").unlink()
        self.trusted_bundle()
        self.rejects("SOURCE_MISSING")

    def test_trusted_vendor_bundle_cannot_omit_owned_vendor_file(self):
        self.put("src/vendor/lib.js", "globalThis.library = {};\n", "vendor")
        self.put("src/vendor/helper.js", "globalThis.helper = {};\n", "vendor")
        self.trusted_bundle()
        self.rejects("VENDOR_TRUST_UNDECLARED")

    def test_trusted_vendor_bundle_cannot_cover_new_unregistered_file(self):
        self.put("src/vendor/lib.js", "globalThis.library = {};\n", "vendor")
        self.put("src/vendor/new.js", "globalThis.new = {};\n", registered=False)
        self.trusted_bundle()
        self.rejects("SOURCE_UNREGISTERED")

    def test_trusted_vendor_bundle_must_be_host_only(self):
        self.put("src/vendor/lib.js", "globalThis.library = {};\n", "vendor")
        self.trusted_bundle()['layers'] = ['H', 'K']
        self.rejects("VENDOR_TRUST_POLICY")

    def test_trusted_vendor_bundle_cannot_relabel_host_code(self):
        self.put("src/vendor/lib.js", "globalThis.library = {};\n", "H")
        self.trusted_bundle()
        self.rejects("VENDOR_TRUST_SOURCE")

    def test_trusted_vendor_bundle_duplicate_file_is_rejected(self):
        self.put("src/vendor/lib.js", "globalThis.library = {};\n", "vendor")
        self.trusted_bundle()
        self.trusted_bundle()['id'] = 'second-library'
        self.rejects("VENDOR_TRUST_DUPLICATE")

    def test_html_route_escape_and_ambiguous_urls_are_rejected(self):
        self.put("src/page.html", "", "H")
        self.put("src/w/frontend.js", "const value = 1;\n", "W")
        route = self.route()
        for key, value, error in [("source", "../outside.html", "ROOT_ESCAPE"),
                                  ("target", "../outside.js", "ROOT_ESCAPE"),
                                  ("src", "/../outside.js", "ROOT_ESCAPE"),
                                  ("src", "//outside/a.js", "HTML_ROUTE_SYNTAX"),
                                  ("src", "/a%2f.js", "HTML_ROUTE_SYNTAX"),
                                  ("src", "/a.js?x=1", "HTML_ROUTE_SYNTAX")]:
            previous = route[key]
            with self.subTest(key=key, value=value):
                route[key] = value
                self.rejects(error)
            route[key] = previous

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

    def test_c_formfeed_cannot_hide_template_include(self):
        self.put("src/k/core.c", '\f#include "../w/policy.h"\n')
        self.put("src/w/policy.h", "int policy;\n", "W")
        self.rejects("LAYER_DIRECTION", path="src/k/core.c", line=1)

    def test_c_directive_horizontal_whitespace_cannot_hide_include(self):
        self.put("src/k/core.c", '/* lead */\v#\finclude "../w/policy.h"\n')
        self.put("src/w/policy.h", "int policy;\n", "W")
        self.rejects("LAYER_DIRECTION", path="src/k/core.c", line=1)

    def test_c_preprocessor_digraph_fails_closed(self):
        self.put("src/k/core.c", '%:include "../w/policy.h"\n')
        self.put("src/w/policy.h", "int policy;\n", "W")
        self.rejects("C_UNSUPPORTED_PREPROCESSOR", path="src/k/core.c")

    def test_c_digraph_token_paste_fails_closed(self):
        self.put("src/core.c", '#define JOIN(a,b) a %:%: b\n')
        self.rejects("C_UNSUPPORTED_PREPROCESSOR")

    def test_c_display_digraph_is_not_preprocessor_code(self):
        self.put("src/core.c", '/* %:include "missing.h" */\nconst char *x = "%:";\n')
        self.green()

    def test_python_annotated_sys_alias_cannot_read_loaded_template(self):
        self.put("src/core.py", 'import sys\nalias: object = sys\npolicy = alias.modules["w.policy"]\n')
        self.put("src/w/policy.py", "value = 1\n", "W")
        self.rejects("CORE_PATH_INJECTION", path="src/core.py", line=3)

    def test_python_named_expression_sys_alias_is_tracked(self):
        self.put("src/core.py", 'import sys\nif (alias := sys):\n    policy = alias.modules["w.policy"]\n')
        self.put("src/w/policy.py", "value = 1\n", "W")
        self.rejects("CORE_PATH_INJECTION", path="src/core.py", line=3)

    def test_python_annotated_neutral_alias_remains_supported(self):
        self.put("src/core.py", 'import math\nalias: object = math\nvalue = alias.pi\n')
        self.green()

    def test_python_core_owns_implicit_host_initializer_dependency(self):
        self.put("src/pkg/__init__.py", "host_value = 1\n", "H")
        self.put("src/pkg/core.py", "value = 1\n")
        self.put("src/app.py", "import pkg.core\n", "H")
        self.rejects("LAYER_DIRECTION", path="src/pkg/core.py", line=1,
                     chain=["src/pkg/core.py", "src/pkg/__init__.py"])

    def test_python_nested_core_requires_outer_initializer_without_importer(self):
        self.put("src/pkg/__init__.py", "host_value = 1\n", "H")
        self.put("src/pkg/sub/__init__.py", "value = 1\n")
        self.put("src/pkg/sub/core.py", "value = 1\n")
        self.rejects("LAYER_DIRECTION", chain=["src/pkg/sub/core.py", "src/pkg/__init__.py"])

    def test_python_neutral_implicit_initializers_are_graph_edges(self):
        self.put("src/pkg/__init__.py", "value = 1\n")
        self.put("src/pkg/sub/__init__.py", "value = 1\n")
        self.put("src/pkg/sub/core.py", "value = 1\n")
        edges = {(edge.source, edge.target) for edge in self.green().edges}
        self.assertIn(("src/pkg/sub/core.py", "src/pkg/__init__.py"), edges)
        self.assertIn(("src/pkg/sub/core.py", "src/pkg/sub/__init__.py"), edges)

    def test_html_base_href_cannot_redirect_a_core_script(self):
        self.put("src/page.html", '<base href="./w/"><script src="load.js"></script>')
        self.put("src/load.js", "const value = 1;")
        self.put("src/w/load.js", "const value = 2;", "W")
        self.rejects("HTML_BASE_URL_UNSUPPORTED", path="src/page.html")

    def test_html_late_base_href_fails_closed_even_with_route(self):
        self.put("src/page.html", '<script src="/load.js"></script><base href="./w/">', "H")
        self.put("src/load.js", "const value = 1;", "H")
        self.route(src="/load.js", target="src/load.js")
        self.rejects("HTML_BASE_URL_UNSUPPORTED")

    def test_html_base_target_does_not_change_script_resolution(self):
        self.put("src/page.html", '<base target="_blank"><script src="load.js"></script>')
        self.put("src/load.js", "const value = 1;")
        self.assertEqual(self.green().edges[0].target, "src/load.js")

    def test_html_javascript_tab_cannot_hide_dynamic_import(self):
        self.put("src/core.html", '<a href="java&#x09;script:import(&quot;./w.js&quot;)">go</a>')
        self.put("src/w.js", "export const value = 1;", "W")
        self.rejects("JS_DYNAMIC_IMPORT", path="src/core.html")

    def test_html_javascript_url_preprocessing_preserves_dependency(self):
        self.put("src/core.html", '<a href="&#x01;JaVa&#10;ScRi&#13;pT:require(&quot;./w.js&quot;) ">go</a>')
        self.put("src/w.js", "module.exports = 1;", "W")
        self.rejects("LAYER_DIRECTION", chain=["src/core.html", "src/w.js"])

    def test_javascript_unicode_identifier_cannot_hide_division_loader(self):
        self.put("src/core.js", r"const π=1; const x=π / require('.\x2fw.js') / 1;")
        self.put("src/w.js", "module.exports = 1;", "W")
        self.rejects("JS_UNSUPPORTED_IDENTIFIER", path="src/core.js")

    def test_javascript_unicode_identifier_in_template_fails_closed(self):
        self.put("src/core.js", r"const x=`${π / require('.\x2fw.js') / 1}`;")
        self.put("src/w.js", "module.exports = 1;", "W")
        self.rejects("JS_UNSUPPORTED_IDENTIFIER")

    def test_javascript_unicode_display_content_remains_supported(self):
        self.put("src/core.js", "// π is display text\nconst x='π'; const y=`幾何 ${1}`; const z=/π/;\n")
        self.green()

    def test_javascript_line_separator_ends_comment_before_dependency(self):
        self.put("src/core.js", "// display only\u2028require('./w.js');")
        self.put("src/w.js", "module.exports = 1;", "W")
        self.rejects("LAYER_DIRECTION", path="src/core.js", line=2)

    def test_javascript_paragraph_separator_ends_comment_before_dependency(self):
        self.put("src/core.js", "// display only\u2029require('./w.js');")
        self.put("src/w.js", "module.exports = 1;", "W")
        self.rejects("LAYER_DIRECTION", path="src/core.js", line=2)

    def test_javascript_template_line_separator_ends_comment(self):
        self.put("src/core.js", "const x=`${// display only\u2028require('./w.js')}`;")
        self.put("src/w.js", "module.exports = 1;", "W")
        self.rejects("LAYER_DIRECTION", path="src/core.js", line=2)

    def test_javascript_arrow_constructor_cannot_create_loader(self):
        self.put("src/core.js", r'''(()=>{}).constructor('return import("./w.js")')();''')
        self.put("src/w.js", "export const value = 1;", "W")
        self.rejects("JS_REFLECTIVE_LOADER")

    def test_javascript_computed_constructor_fails_closed_in_template_layer(self):
        self.put("src/core.js", r'''(()=>{})["constructor"]('return import("./h.js")')();''', "W")
        self.put("src/h.js", "export const value = 1;", "H")
        self.rejects("JS_REFLECTIVE_LOADER")

    def test_javascript_constructor_display_text_is_not_a_loader(self):
        self.put("src/core.js", "// constructor\nconst x='constructor'; const y=`constructor`;\n")
        self.green()

    def test_javascript_regex_cannot_cross_unicode_line_terminator(self):
        self.put("src/core.js", "const x=/display\u2028require('./w.js')/;")
        self.put("src/w.js", "module.exports = 1;", "W")
        self.rejects("LEXICAL_SYNTAX")

    def test_javascript_unicode_line_continuation_keeps_exact_string_policy(self):
        self.put("src/core.js", "const x='calcium-\\\u2028silicate-6';")
        self.rejects("FORBIDDEN_STRING")

    def test_c_trigraph_cannot_hide_template_include(self):
        self.put("src/core.c", '??=include "w.h"\n')
        self.put("src/w.h", "int policy;\n", "W")
        self.rejects("C_UNSUPPORTED_TRIGRAPH", path="src/core.c", line=1)

    def test_c_trigraph_splicing_is_rejected_before_comment_processing(self):
        self.put("src/core.c", '// display??/\n#include "w.h"\n')
        self.put("src/w.h", "int policy;\n", "W")
        self.rejects("C_UNSUPPORTED_TRIGRAPH", line=1)

    def test_c_trigraph_in_literal_is_explicitly_unsupported(self):
        self.put("src/core.c", 'const char *x = "??=";\n')
        self.rejects("C_UNSUPPORTED_TRIGRAPH")

    def test_c_double_question_without_trigraph_remains_display_text(self):
        self.put("src/core.c", 'const char *x = "??x";\n')
        self.green()

    def test_python_destructured_sys_alias_cannot_read_loaded_template(self):
        self.put("src/core.py", 'import sys\nalias, = (sys,)\npolicy = alias.modules["w.policy"]\n')
        self.put("src/w/policy.py", "value = 1\n", "W")
        self.rejects("CORE_PATH_INJECTION", path="src/core.py", line=3)

    def test_python_nested_list_and_starred_sys_unpacking_is_tracked(self):
        path = self.put("src/core.py", "")
        self.put("src/w/policy.py", "value = 1\n", "W")
        for binding in ['[alias] = [sys]', '((alias,),) = ((sys,),)',
                        'alias, *rest = (sys, 0)', '*rest, alias = (0, sys)']:
            with self.subTest(binding=binding):
                path.write_text('import sys\n' + binding + '\npolicy = alias.modules["w.policy"]\n', encoding="utf-8")
                self.rejects("CORE_PATH_INJECTION", line=3)

    def test_python_container_then_unpack_preserves_sys_provenance(self):
        self.put("src/core.py", 'import sys\nbox = (sys,)\nalias, = box\npolicy = alias.modules["w.policy"]\n')
        self.put("src/w/policy.py", "value = 1\n", "W")
        self.rejects("CORE_PATH_INJECTION", line=4)

    def test_python_container_index_preserves_sys_provenance(self):
        self.put("src/core.py", 'import sys\nalias = (sys,)[0]\npolicy = alias.modules["w.policy"]\n')
        self.put("src/w/policy.py", "value = 1\n", "W")
        self.rejects("CORE_PATH_INJECTION", line=3)

    def test_python_dict_and_loop_bindings_preserve_sys_provenance(self):
        path = self.put("src/core.py", "")
        for source in ['import sys\nalias = {"module": sys}["module"]\npolicy = alias.modules["w.policy"]\n',
                       'import sys\nfor alias in [sys]:\n    policy = alias.modules["w.policy"]\n',
                       'import sys\npolicy = [alias.modules["w.policy"] for alias in [sys]]\n']:
            with self.subTest(source=source):
                path.write_text(source, encoding="utf-8")
                self.rejects("CORE_PATH_INJECTION")

    def test_python_sys_storage_through_attribute_target_fails_closed(self):
        self.put("src/core.py", 'import sys\nholder.alias = sys\npolicy = holder.alias.modules["w.policy"]\n')
        self.rejects("CORE_SYS_ALIAS_TARGET", line=2)

    def test_python_mixed_nested_sys_storage_target_fails_closed(self):
        self.put("src/core.py", 'import sys\nvalue, holder.alias = (0, sys)\npolicy = holder.alias.modules["w.policy"]\n')
        self.rejects("CORE_SYS_ALIAS_TARGET", line=2)

    def test_python_neutral_destructuring_remains_supported(self):
        self.put("src/core.py", 'import math\nalias, value = (math, 1)\n[nested] = [alias]\nresult = nested.pi + value\n')
        self.green()

    def test_javascript_parenthesized_constructor_key_fails_closed(self):
        self.put("src/core.js", r'''(()=>{})[("constructor")]('return import("./w.js")')();''')
        self.put("src/w.js", "export const value = 1;", "W")
        self.rejects("JS_COMPUTED_KEY_UNSUPPORTED")

    def test_javascript_constructed_reflective_keys_fail_closed(self):
        path = self.put("src/core.js", "")
        self.put("src/w.js", "export const value = 1;", "W")
        for key in ["(('constructor'))", "'con'+'structor'", "(0,'constructor')",
                    "'con'.concat('structor')", "`con${'structor'}`", "['constructor'][0]"]:
            with self.subTest(key=key):
                path.write_text("(()=>{})[" + key + "]('return import(\"./w.js\")')();", encoding="utf-8")
                self.rejects("JS_COMPUTED_KEY_UNSUPPORTED")

    def test_javascript_bare_index_variable_is_not_assumed_numeric(self):
        self.put("src/core.js", "const i = 'constructor'; (()=>{})[i]('return 1')();")
        self.rejects("JS_COMPUTED_KEY_UNSUPPORTED")

    def test_javascript_unknown_addition_key_is_not_assumed_numeric(self):
        self.put("src/core.js", "const key = 'con'; (()=>{})[key + 'structor']('return 1')();")
        self.rejects("JS_COMPUTED_KEY_UNSUPPORTED")

    def test_javascript_numeric_and_coerced_arithmetic_indices_remain_supported(self):
        self.put("src/core.js", "const values = [1,2,3]; const a=values[0]; const b=values[(1+2)*3]; "
                 "const c=values[+i + 1]; const d=values[i-1]; const e=values[i|0]; "
                 "const f=values[(i >>> 0) % 3]; const g=values[i++];\n")
        self.green()

    def test_javascript_arrays_and_destructuring_are_not_member_keys(self):
        self.put("src/core.js", "const labels=['constructor', 'srcdoc']; const [first, second]=labels; "
                 "function values([x,y]=[1,2]) {return [x,y];} const firstValue=[...values()][0];\n")
        self.green()

    def test_javascript_literal_neutral_property_keys_remain_supported(self):
        self.put("src/core.js", "const shape={width:1}; const a=shape['width']; const b=shape[`width`];\n")
        self.green()

    def test_html_srcdoc_document_is_explicitly_unsupported(self):
        self.put("src/core.html", '<iframe srcdoc="&lt;script src=&quot;./w.js&quot;&gt;&lt;/script&gt;"></iframe>')
        self.put("src/w.js", "export const value = 1;", "W")
        self.rejects("HTML_SRCDOC_UNSUPPORTED")

    def test_html_empty_or_host_srcdoc_still_requires_document_parser(self):
        self.put("src/host.html", '<iframe SRCDOC=""></iframe>', "H")
        self.rejects("HTML_SRCDOC_UNSUPPORTED")

    def test_javascript_template_srcdoc_property_is_not_a_static_dependency(self):
        self.put("src/core.js", "frame.srcdoc = '<script src=\"./h.js\"></script>';", "W")
        self.put("src/h.js", "export const value = 1;", "H")
        self.rejects("JS_HTML_WRITER_UNSUPPORTED")

    def test_javascript_literal_srcdoc_property_fails_closed(self):
        self.put("src/core.js", "frame['srcdoc'] = '<script src=\"./h.js\"></script>';", "W")
        self.put("src/h.js", "export const value = 1;", "H")
        self.rejects("JS_HTML_WRITER_UNSUPPORTED")

    def test_javascript_constructed_srcdoc_key_fails_closed(self):
        self.put("src/core.js", "frame['src'+'doc'] = '<script src=\"./h.js\"></script>';", "W")
        self.put("src/h.js", "export const value = 1;", "H")
        self.rejects("JS_COMPUTED_KEY_UNSUPPORTED")

    def test_javascript_attribute_writer_cannot_hide_srcdoc(self):
        self.put("src/core.js", "frame.setAttribute('srcdoc', '<script src=\"./h.js\"></script>');", "W")
        self.put("src/h.js", "export const value = 1;", "H")
        self.rejects("JS_HTML_WRITER_UNSUPPORTED")

    def test_javascript_dom_writer_display_names_are_not_executable(self):
        self.put("src/core.js", "const labels=['srcdoc','innerHTML','setAttribute']; // frame.srcdoc\n")
        self.green()

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
