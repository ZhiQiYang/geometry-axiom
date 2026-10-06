"""Browser native build contract; standalone, outside aggregate test floors.

The source gate follows a conservative textual superset of literal CommonJS
requires. Unknown require expressions/packages and new child-process consumers
fail review rather than silently authorizing removal of a needed executable.
Arguments are bounded to 4096 characters, including multiline whitespace.
Local files use Node's exact-file then appended-extension order. Directory
packages with package.json and native addons require review rather than an
incomplete interpretation of package main or executable code.
It is not a general JavaScript parser or a security boundary.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
ENTRIES = ('geometry-web/cdp_test.js', 'geometry-web/space_model_test.js',
           'geometry-web/documents_browser_test.js')
REQUIRE_START = re.compile(r'\brequire\s*\(')
MAX_REQUIRE_ARGUMENT = 4096
LITERAL = re.compile(r'\s*([\'"])([^\'"]+)\1\s*')
CORE = re.compile(r'\.build[\\/]+core\b|geometry-tests[\\/]+core\b|GEOMETRY_TEST_CORE')
SPAWN = re.compile(r'(?<![\w.])spawn\s*\(\s*')
EXPECTED = {
    'current_geometry.c': ['-std=c11', '-O2', 'current_geometry.c', '-lm', '-o', '.build/core'],
    'geometry-web/web_bridge.c': ['-std=c11', '-O2', 'geometry-web/web_bridge.c', '-lm', '-o', '.build/web_bridge'],
    'geometry-core/model_base.c': ['-std=c11', '-O2', 'geometry-core/model_base.c', '-lm', '-o', '.build/model_base'],
}


def literal_requires(source, name):
    for match in REQUIRE_START.finditer(source):
        end = source.find(')', match.end(), match.end() + MAX_REQUIRE_ARGUMENT + 1)
        argument = source[match.end():end] if end >= 0 else ''
        value = LITERAL.fullmatch(argument)
        if end < 0 or value is None:
            raise ValueError('Unreviewed require expression in ' + name)
        yield value[2]


def local_dependency(caller, target):
    candidate = caller.parent / target
    # LOAD_AS_FILE appends an extension; it never replaces a dotted suffix.
    for choice in [candidate, *(Path(str(candidate) + suffix) for suffix in ('.js', '.json', '.node'))]:
        if choice.is_file():
            resolved = choice.resolve()
            if resolved.suffix not in {'', '.js', '.cjs', '.json'}:
                raise ValueError('Unreviewed local dependency type: ' + target)
            return resolved
    if candidate.is_dir():
        if (candidate / 'package.json').exists():
            raise ValueError('Unreviewed directory package: ' + target)
        for suffix in ('.js', '.json', '.node'):
            choice = candidate / ('index' + suffix)
            if choice.is_file():
                resolved = choice.resolve()
                if resolved.suffix not in {'', '.js', '.cjs', '.json'}:
                    raise ValueError('Unreviewed local dependency type: ' + target)
                return resolved
    raise ValueError('Missing local dependency: ' + target)


def dependency_closure(root):
    builtins = set(json.loads(subprocess.check_output(
        ['node', '-p', 'JSON.stringify(require("module").builtinModules)'], text=True, timeout=10)))
    pending = [root / name for name in ENTRIES]
    seen = set()
    spawns = []
    while pending:
        path = pending.pop().resolve()
        name = path.relative_to(root.resolve()).as_posix()
        if name in seen:
            continue
        seen.add(name)
        source = path.read_text(encoding='utf-8')
        if path.suffix == '.json':
            json.loads(source)
            continue
        if CORE.search(source):
            raise ValueError('Core binary consumer in ' + name)
        if re.search(r'\bimport\s*\(', source):
            raise ValueError('Unreviewed dynamic import in ' + name)
        child_requires = 0
        for target in literal_requires(source, name):
            if target.startswith('.'):
                pending.append(local_dependency(path, target))
            elif target.removeprefix('node:') not in builtins:
                raise ValueError('Unreviewed package dependency: ' + target)
            if target.removeprefix('node:') == 'child_process':
                child_requires += 1
        if child_requires:
            allowed = re.findall(r'\{\s*spawn\s*\}\s*=\s*require\(\s*[\'"](?:node:)?child_process[\'"]\s*\)', source)
            if name not in ENTRIES or child_requires != 1 or len(allowed) != 1:
                raise ValueError('Unreviewed child-process consumer in ' + name)
        calls = list(SPAWN.finditer(source))
        if calls:
            if name not in ENTRIES or not child_requires or len(calls) != 1:
                raise ValueError('Unreviewed spawn in ' + name)
            first = source[calls[0].end():]
            expected = ("process.env.GEOMETRY_CHROME||'/usr/bin/google-chrome',"
                        if name.endswith('documents_browser_test.js') else 'CHROME,')
            if not first.startswith(expected):
                raise ValueError('Browser spawn no longer selects Chrome: ' + name)
            spawns.append(name)
    if sorted(spawns) != sorted(ENTRIES):
        raise ValueError('Browser entry spawn census changed')
    return sorted(seen)


class Dependencies(unittest.TestCase):
    def test_recursive_browser_consumers_need_no_standalone_core(self):
        files = dependency_closure(ROOT)
        self.assertIn('geometry-web/parameter_workflow_test.js', files)
        self.assertNotIn('geometry-web/polydraft_test.js', files)
        self.assertNotIn('geometry-web/canvas_test.js', files)
        print('DEPENDENCY_RESULT ' + json.dumps(dict(files=files, chrome_spawns=3, core_consumers=0)))

    def fixture(self, directory, tail):
        root = Path(directory)
        (root / 'geometry-web').mkdir()
        for name in ENTRIES:
            executable = ("process.env.GEOMETRY_CHROME||'/usr/bin/google-chrome'"
                          if name.endswith('documents_browser_test.js') else 'CHROME')
            (root / name).write_text("const {spawn}=require('child_process'); spawn(" + executable + ", []);\n")
        with (root / ENTRIES[0]).open('a') as stream:
            stream.write("require('./late.js');\n")
        (root / 'geometry-web/late.js').write_text(tail)
        return root

    def test_late_transitive_core_consumer_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='browser-core-negative-') as directory:
            root = self.fixture(directory, "const {spawn}=require('child_process'); spawn('.build/core', []);\n")
            with self.assertRaisesRegex(ValueError, 'Core binary consumer'):
                dependency_closure(root)

    def test_unresolved_transitive_require_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='browser-require-negative-') as directory:
            root = self.fixture(directory, 'require(process.env.UNREVIEWED_MODULE);\n')
            with self.assertRaisesRegex(ValueError, 'Unreviewed require expression'):
                dependency_closure(root)

    def test_new_transitive_process_consumer_with_assembled_path_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='browser-process-negative-') as directory:
            root = self.fixture(directory, "const {spawn}=require('child_process'); spawn(require('path').join('.build','core'), []);\n")
            with self.assertRaisesRegex(ValueError, 'Unreviewed child-process consumer'):
                dependency_closure(root)

    def test_multiline_require_cannot_hide_new_native_process_consumer(self):
        with tempfile.TemporaryDirectory(prefix='browser-multiline-negative-') as directory:
            root = self.fixture(directory, "const cp=require(\n'child_process'\n); cp.spawnSync(['.build','core'].join('/'));\n")
            with self.assertRaisesRegex(ValueError, 'Unreviewed child-process consumer'):
                dependency_closure(root)

    def node_resolve(self, caller, target):
        program = 'const {createRequire}=require("node:module"); console.log(createRequire(process.argv[1]).resolve(process.argv[2]));'
        return Path(subprocess.check_output(['node', '-e', program, str(caller), target],
                                            text=True, timeout=10).strip())

    def test_dotted_specifier_uses_appended_extension_without_shadowing(self):
        with tempfile.TemporaryDirectory(prefix='browser-suffix-negative-') as directory:
            root = self.fixture(directory, "require('./late.test');\n")
            actual = root / 'geometry-web/late.test.js'
            actual.write_text("const cp=require('child_process'); cp.spawnSync(['.build','core'].join('/'));\n")
            self.assertEqual(self.node_resolve(root / 'geometry-web/late.js', './late.test'), actual)
            with self.assertRaisesRegex(ValueError, 'Unreviewed child-process consumer'):
                dependency_closure(root)

    def test_directory_package_main_cannot_be_hidden_by_benign_index(self):
        with tempfile.TemporaryDirectory(prefix='browser-package-negative-') as directory:
            root = self.fixture(directory, "require('./consumer');\n")
            package = root / 'geometry-web/consumer'
            package.mkdir()
            (package / 'package.json').write_text('{"main":"actual.js"}')
            (package / 'index.js').write_text('module.exports = {};\n')
            actual = package / 'actual.js'
            actual.write_text("const cp=require('child_process'); cp.spawnSync(['.build','core'].join('/'));\n")
            self.assertEqual(self.node_resolve(root / 'geometry-web/late.js', './consumer'), actual)
            with self.assertRaisesRegex(ValueError, 'Unreviewed directory package'):
                dependency_closure(root)

    def test_multiline_chrome_imports_and_builtin_require_are_supported(self):
        with tempfile.TemporaryDirectory(prefix='browser-multiline-positive-') as directory:
            root = self.fixture(directory, "require(\n 'path'\n);\n")
            for name in ENTRIES:
                path = root / name
                path.write_text(path.read_text().replace("require('child_process')", "require(\n'child_process'\n)"))
            self.assertIn('geometry-web/late.js', dependency_closure(root))

    def test_multiline_nonliteral_require_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='browser-expression-negative-') as directory:
            root = self.fixture(directory, 'require(\nprocess.env.UNREVIEWED_MODULE\n);\n')
            with self.assertRaisesRegex(ValueError, 'Unreviewed require expression'):
                dependency_closure(root)

    def test_oversized_require_is_rejected_instead_of_ignored(self):
        with tempfile.TemporaryDirectory(prefix='browser-bound-negative-') as directory:
            root = self.fixture(directory, "require(\n" + ' ' * 8192 + "'child_process');\n")
            with self.assertRaisesRegex(ValueError, 'Unreviewed require expression'):
                dependency_closure(root)

    def test_dotted_extension_and_bare_directory_index_match_node(self):
        with tempfile.TemporaryDirectory(prefix='browser-resolve-positive-') as directory:
            root = self.fixture(directory, "require('./extra.test'); require('./plain');\n")
            caller = root / 'geometry-web/late.js'
            (root / 'geometry-web/extra.js').write_text('module.exports = {};\n')
            actual = root / 'geometry-web/extra.test.js'
            actual.write_text('module.exports = {};\n')
            plain = root / 'geometry-web/plain'
            plain.mkdir()
            (plain / 'index.js').write_text('module.exports = {};\n')
            for target in ('./extra.test', './plain'):
                self.assertEqual(local_dependency(caller, target), self.node_resolve(caller, target))
            files = dependency_closure(root)
            self.assertIn('geometry-web/extra.test.js', files)
            self.assertNotIn('geometry-web/extra.js', files)
            self.assertIn('geometry-web/plain/index.js', files)

    def test_unreviewed_native_addon_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='browser-addon-negative-') as directory:
            root = self.fixture(directory, "require('./addon');\n")
            (root / 'geometry-web/addon.node').write_bytes(b'fixture only; never executed')
            with self.assertRaisesRegex(ValueError, 'Unreviewed local dependency type'):
                dependency_closure(root)


class BuildPlans(unittest.TestCase):
    def run_build(self, script, failure=None):
        with tempfile.TemporaryDirectory(prefix='browser-build-contract-') as directory:
            root = Path(directory)
            (root / 'package.json').write_bytes((ROOT / 'package.json').read_bytes())
            (root / 'bin').mkdir()
            compiler = root / 'bin/gcc'
            compiler.write_text(
                '#!' + sys.executable + '\n'
                'import json,os,pathlib,sys\n'
                'with open(os.environ["BUILD_CALLS"],"a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")\n'
                'if os.environ.get("FAIL_SOURCE") in sys.argv[1:]: sys.exit(7)\n'
                'out=pathlib.Path(sys.argv[sys.argv.index("-o")+1]); out.write_text("fixture only\\n")\n')
            compiler.chmod(0o755)
            environment = dict(os.environ, PATH=str(root / 'bin') + os.pathsep + os.environ['PATH'],
                               BUILD_CALLS=str(root / 'calls.jsonl'))
            environment.pop('FAIL_SOURCE', None)
            if failure:
                environment['FAIL_SOURCE'] = failure
            result = subprocess.run(['npm', 'run', script], cwd=root, env=environment,
                                    capture_output=True, text=True, timeout=30)
            calls = [json.loads(line) for line in (root / 'calls.jsonl').read_text().splitlines()]
            outputs = sorted(path.name for path in (root / '.build').iterdir())
            return result.returncode, calls, outputs

    def test_browser_build_compiles_only_bridge_and_base_with_original_arguments(self):
        code, calls, outputs = self.run_build('build:browser')
        self.assertEqual(code, 0)
        self.assertEqual(calls, [EXPECTED['geometry-web/web_bridge.c'], EXPECTED['geometry-core/model_base.c']])
        self.assertEqual(outputs, ['model_base', 'web_bridge'])

    def test_general_build_keeps_original_core_bridge_base_order_and_arguments(self):
        code, calls, outputs = self.run_build('build')
        self.assertEqual(code, 0)
        self.assertEqual(calls, list(EXPECTED.values()))
        self.assertEqual(outputs, ['core', 'model_base', 'web_bridge'])

    def test_bridge_compile_failure_stops_before_base(self):
        code, calls, outputs = self.run_build('build:browser', 'geometry-web/web_bridge.c')
        self.assertEqual(code, 7)
        self.assertEqual(calls, [EXPECTED['geometry-web/web_bridge.c']])
        self.assertEqual(outputs, [])

    def test_base_compile_failure_is_not_reported_as_success(self):
        code, calls, outputs = self.run_build('build:browser', 'geometry-core/model_base.c')
        self.assertEqual(code, 7)
        self.assertEqual(calls, [EXPECTED['geometry-web/web_bridge.c'], EXPECTED['geometry-core/model_base.c']])
        self.assertEqual(outputs, ['web_bridge'])

    def test_general_core_compile_failure_stops_before_browser_targets(self):
        code, calls, outputs = self.run_build('build', 'current_geometry.c')
        self.assertEqual(code, 7)
        self.assertEqual(calls, [EXPECTED['current_geometry.c']])
        self.assertEqual(outputs, [])


if __name__ == '__main__':
    dependencies_only = '--dependencies-only' in sys.argv
    if dependencies_only:
        sys.argv.remove('--dependencies-only')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Dependencies)
    if not dependencies_only:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(BuildPlans))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
