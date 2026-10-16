"""N1a: standalone K codec/exact arithmetic and real bridge shared-code controls.

K builds copy ONLY public K headers/implementations to an isolated directory.
They have no repository include search path and cannot reach a template or host.
The product witness compiles the real web_bridge separately and links exactly
those K objects. Each negative control changes only one K object, then requires
both a K assertion and an actual bridge transaction assertion to fail.
Compile errors, process crashes and unavailable compilers never count as kills.
"""
from __future__ import annotations

import atexit
from fractions import Fraction
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests import test_engineering_json as existing_codec


class NativeBuild:
    def __init__(self):
        parent = Path(tempfile.gettempdir()) / "geometry-tests"
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="geo261-n1a-", dir=parent)
        atexit.register(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.kernel = self.work / "isolated-kernel"
        self.kernel.mkdir()
        for name in ("types.h", "exact.h", "exact.c", "codec.h", "codec.c", "geometry.h", "geometry.c", "grid.h", "grid.c", "parameters.h", "parameters.c", "linear.h", "linear.c", "named_values.h", "named_values.c", "datums.h", "datums.c", "source.h", "source.c"):
            shutil.copy2(ROOT / "geometry-core/kernel" / name, self.kernel / name)
        (self.kernel / "internal").mkdir()
        shutil.copy2(ROOT / "geometry-core/kernel/internal/parameter_store.h", self.kernel / "internal/parameter_store.h")
        shutil.copy2(ROOT / "geometry-core/kernel/internal/named_values.h", self.kernel / "internal/named_values.h")
        shutil.copy2(ROOT / "geometry-core/kernel/internal/datums.h", self.kernel / "internal/datums.h")
        self.woodworking = self.work / "isolated-woodworking"
        self.woodworking.mkdir()
        for name in ("members.h", "members.c"):
            shutil.copy2(ROOT / "geometry-templates/woodworking/native" / name, self.woodworking / name)
        self.windows = os.name == "nt"
        self.suffix = ".exe" if self.windows else ""
        self.logs = []
        self.vcvars = None
        if self.windows:
            vswhere = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
            if not vswhere.exists():
                raise unittest.SkipTest("No MSVC discovery tool for K build")
            install = subprocess.check_output([str(vswhere), "-latest", "-products", "*", "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"], text=True).strip()
            self.vcvars = Path(install) / "VC/Auxiliary/Build/vcvars64.bat"
            if not self.vcvars.is_file():
                raise unittest.SkipTest("No MSVC compiler for K build")
        else:
            self.cc = shutil.which(os.environ.get("CC", "cc"))
            if not self.cc:
                raise unittest.SkipTest("No C compiler for K build")
        self.exact_object = self.compile(self.kernel / "exact.c", "exact")
        self.codec_object = self.compile(self.kernel / "codec.c", "codec")
        self.geometry_object = self.compile(self.kernel / "geometry.c", "geometry")
        self.grid_object = self.compile(self.kernel / "grid.c", "grid")
        self.parameters_object = self.compile(self.kernel / "parameters.c", "parameters")
        self.linear_object = self.compile(self.kernel / "linear.c", "linear")
        self.named_values_object = self.compile(self.kernel / "named_values.c", "named-values")
        self.datums_object = self.compile(self.kernel / "datums.c", "datums")
        self.source_object = self.compile(self.kernel / "source.c", "source")
        self.wood_members_object = self.compile(self.woodworking / "members.c", "wood-members")
        exact_source = self.work / "exact-client.c"
        shutil.copy2(ROOT / "tests/geo261_exact_harness.c", exact_source)
        self.exact_client = self.compile(exact_source, "exact-client")
        codec_source = self.work / "codec-client.c"
        source = existing_codec.HARNESS.replace('#include "engineering_json.inc"', '#include "codec.h"')
        source = source.replace("EngJson", "GeoJson")
        source = re.sub(r"\beng_(json_|sha256|base64_)", r"geo_\1", source)
        codec_source.write_text(source, encoding="utf-8")
        self.codec_client = self.compile(codec_source, "codec-client")
        self.exact = self.link("exact-client", [self.exact_client, self.exact_object])
        self.codec = self.link("codec-client", [self.codec_client, self.codec_object])
        self.bridge_object = None
        self.bridge_exe = None

    def run_build(self, args):
        if self.windows:
            script = self.work / ("build-%d.cmd" % len(self.logs))
            script.write_text('@echo off\ncall "' + str(self.vcvars) + '" >nul\n' + subprocess.list2cmdline(args) + '\n', encoding="utf-8")
            command = ["cmd", "/d", "/c", str(script)]
        else:
            command = args
        run = subprocess.run(command, cwd=self.work, capture_output=True, text=True, errors="replace", timeout=300)
        self.logs.append({"command": command, "exit": run.returncode, "stdout": run.stdout, "stderr": run.stderr})
        (self.work / "build-log.json").write_text(json.dumps(self.logs, indent=2), encoding="utf-8")
        if run.returncode:
            raise AssertionError("Native compile/link failed (not a valid negative control):\n" + run.stdout + run.stderr)

    def compile(self, source, name, defines=()):
        out = self.work / (name + (".obj" if self.windows else ".o"))
        if self.windows:
            args = ["cl", "/nologo", "/utf-8", "/Od", "/W3", "/c", "/I" + str(self.kernel), "/Fo:" + str(out)]
            # Product CLI excludes GDI; codec clients must retain _WIN32 so
            # their stdout stays binary during base64 round-trip assertions.
            if source == ROOT / "geometry-web/web_bridge.c":
                args.append("/U_WIN32")
            args += ["/D" + d for d in defines] + [str(source)]
        else:
            args = [self.cc, "-std=c11", "-O0", "-Werror=implicit-function-declaration", "-I", str(self.kernel)]
            args += ["-D" + d for d in defines] + ["-c", str(source), "-o", str(out)]
        self.run_build(args)
        return out

    def link(self, name, objects):
        out = self.work / (name + self.suffix)
        if self.windows:
            args = ["cl", "/nologo", *map(str, objects), "/Fe:" + str(out), "/link", "/STACK:16777216"]
        else:
            args = [self.cc, *map(str, objects), "-lm", "-o", str(out)]
        self.run_build(args)
        return out

    def bridge(self):
        if self.bridge_object is None:
            self.bridge_object = self.compile(ROOT / "geometry-web/web_bridge.c", "product-bridge", ["GEOMETRY_KERNEL_EXTERNAL=1", "GEOMETRY_WOODWORKING_EXTERNAL=1"])
            self.bridge_exe = self.link("product-bridge", [self.bridge_object, *self.product_objects()])
        return self.bridge_exe

    def product_objects(self):
        return [*self.kernel_objects(), self.wood_members_object]

    def kernel_objects(self):
        return [self.exact_object, self.codec_object, self.geometry_object, self.grid_object,
                self.parameters_object, self.linear_object, self.named_values_object, self.datums_object, self.source_object]

    def mutant(self, module, before, after, client_object=None):
        text = (self.kernel / (module + ".c")).read_text(encoding="utf-8")
        if text.count(before) != 1:
            raise AssertionError("Negative control did not hit exactly once: " + module)
        source = self.work / (module + "-mutant.c")
        source.write_text(text.replace(before, after), encoding="utf-8")
        changed = self.compile(source, module + "-mutant")
        self.bridge()
        exact = changed if module == "exact" else self.exact_object
        codec = changed if module == "codec" else self.codec_object
        geometry = changed if module == "geometry" else self.geometry_object
        grid = changed if module == "grid" else self.grid_object
        parameters = changed if module == "parameters" else self.parameters_object
        linear = changed if module == "linear" else self.linear_object
        named_values = changed if module == "named_values" else self.named_values_object
        datums = changed if module == "datums" else self.datums_object
        source_object = changed if module == "source" else self.source_object
        if client_object is None:
            client_object = self.exact_client if module == "exact" else self.codec_client
        dependencies = [self.geometry_object] if module == "grid" else []
        if module == "parameters":
            dependencies = [self.codec_object, self.exact_object, self.geometry_object]
        if module == "linear":
            dependencies = [self.exact_object, self.geometry_object, self.named_values_object]
        if module == "named_values":
            dependencies = [self.geometry_object, self.linear_object, self.exact_object]
        if module == "datums":
            dependencies = [self.geometry_object, self.linear_object, self.exact_object]
        client = self.link(module + "-mutant-client", [client_object, changed, *dependencies])
        product = self.link(module + "-mutant-bridge", [self.bridge_object, exact, codec, geometry, grid, parameters, linear, named_values, datums, source_object, self.wood_members_object])
        return client, product


_BUILD = None
def native():
    global _BUILD
    if _BUILD is None:
        _BUILD = NativeBuild()
    return _BUILD


class KernelCodec(existing_codec.EngineeringJson):
    @classmethod
    def setUpClass(cls):
        build = native()
        cls.work = build.work
        cls.exe = build.codec
        cls.compiler_output = "K-only independent compilation; isolated public source closure"


def exact_call(exe, operation, a, b=None):
    args = [str(exe), str(operation), *map(str, a)]
    if b is not None:
        args += list(map(str, b))
    run = subprocess.run(args, capture_output=True, text=True, timeout=10)
    if run.returncode:
        raise AssertionError("K process failed, not a numerical rejection: " + run.stderr)
    return tuple(map(int, run.stdout.split()))


class KernelExact(unittest.TestCase):
    def test_fractional_arithmetic_matches_independent_fraction_oracle(self):
        rng = random.Random(261)
        for operation in range(4):
            for _ in range(40):
                a, b = Fraction(rng.randint(-10000, 10000), rng.randint(1, 100)), Fraction(rng.randint(1, 10000), rng.randint(1, 100))
                expected = (lambda: a+b, lambda: a-b, lambda: a*b, lambda: a/b)[operation]()
                result = exact_call(native().exact, operation, (a.numerator, a.denominator, 0), (b.numerator, b.denominator, 0))
                self.assertEqual((0, expected.numerator, expected.denominator, 0), result)

    def test_cross_cancellation_precedes_checked_multiplication(self):
        self.assertEqual((0, 1, 1, 1), exact_call(native().exact, 2, (2**63-1, 3, 1), (3, 2**63-1, 0)))
        self.assertEqual((0, 0, 1, 0), exact_call(native().exact, 1, (-17, 23, 0), (-17, 23, 0)))
        self.assertEqual((0, -2, 3, 0), exact_call(native().exact, 3, (2, 7, 1), (-3, 7, 1)))

    def test_overflow_unit_failures_preserve_output(self):
        cases = [(0, (2**63-1, 1, 0), (1, 1, 0), 3),
                 (1, (-(2**63-1), 1, 0), (1, 1, 0), 3),
                 (2, (2**63-1, 1, 0), (2, 1, 0), 2),
                 (0, (1, 1, 0), (1, 1, 1), 4),
                 (2, (1, 1, 1), (1, 1, 1), 5),
                 (3, (1, 1, 0), (0, 1, 0), 6),
                 (3, (1, 1, 0), (1, 1, 1), 7),
                 (9, (1, 1, 0), (1, 1, 0), 8)]
        for operation, a, b, error in cases:
            with self.subTest(operation=operation, a=a, b=b):
                self.assertEqual((error, 37, 41, 1), exact_call(native().exact, operation, a, b))

    def test_public_normalization_rejects_invalid_values(self):
        for value, expected in [((0, 19, 0), (0, 0, 1, 0)), ((-4, 6, 1), (0, -2, 3, 1)),
                                ((-2**63, 1, 0), (1, 37, 41, 1)), ((1, 0, 0), (9, 37, 41, 1)),
                                ((1, -1, 0), (9, 37, 41, 1)), ((1, 1, 4), (10, 37, 41, 1))]:
            with self.subTest(value=value):
                self.assertEqual(expected, exact_call(native().exact, "normalize", value))


def product_preview(exe, expression, *, duplicate=False):
    with _bridge.BridgeSession(exe) as session:
        if not session.command("reset")["ok"]:
            raise AssertionError("bridge reset failed")
        read = session.command("engineering-read")
        if not read["ok"]:
            raise AssertionError(read)
        card = {"op": "put-parameter", "value": {"id": 1, "name": "exact witness", "fields": [{"id": 1, "name": "length", "type": "dimension", "input": expression}]}}
        request = {"schema": "engineering-transaction/1", "expectedRevision": read["revision"], "operations": [card]}
        raw = json.dumps(request)
        if duplicate:
            raw = raw.replace('{"schema":', '{"schema":"engineering-transaction/1","schema":', 1)
        path = native().work / "production-witness.json"
        path.write_text(raw, encoding="utf-8")
        response = session.command("engineering-preview " + str(path))
        return response


class ProductSharedImplementation(unittest.TestCase):
    def assert_exact_witness(self, client, bridge):
        self.assertEqual((0, 2, 1, 1), exact_call(client, 2, (2**63-1, 3, 1), (6, 2**63-1, 0)))
        self.assert_product_exact(bridge)

    def assert_product_exact(self, bridge):
        response = product_preview(bridge, "=9223372036854775807 mm/3*(6/9223372036854775807)")
        self.assertTrue(response["ok"], response)
        self.assertTrue(response["preview"]["valid"], response)
        value = response["preview"]["after"]["parameters"][0]["fields"][0]["value"]
        self.assertEqual({"num": "2", "den": "1", "unit": "mm"}, value)

    def assert_codec_witness(self, client):
        path = native().work / "duplicate.json"
        path.write_text('{"a":1,"\\u0061":2}', encoding="utf-8")
        run = subprocess.run([str(client), "canonical", str(path)], capture_output=True, text=True, timeout=10)
        self.assertIn(run.returncode, (0, 1), "crash is not a parser result")
        self.assertEqual(1, run.returncode)
        self.assertIn("Duplicate JSON object key", run.stderr)

    def assert_product_codec(self, bridge):
        response = product_preview(bridge, "1", duplicate=True)
        self.assertFalse(response["ok"], response)
        self.assertIn("Duplicate JSON object key", response["error"])

    def test_exact_negative_control_changes_both_kernel_and_product(self):
        build = native()
        self.assert_exact_witness(build.exact, build.bridge())
        client, bridge = build.mutant("exact", "g=geo_exact_gcd(a.num,b.den);a.num/=g;b.den/=g;", "g=1;a.num/=g;b.den/=g;")
        self.assertNotEqual(0, exact_call(client, 2, (2**63-1, 3, 1), (6, 2**63-1, 0))[0])
        response = product_preview(bridge, "=9223372036854775807 mm/3*(6/9223372036854775807)")
        self.assertTrue(response["ok"], response)
        self.assertFalse(response["preview"]["valid"], response)
        self.assertIn("PRECISION", json.dumps(response))
        self.assert_exact_witness(build.exact, build.bridge())

    def test_codec_negative_control_changes_both_kernel_and_product(self):
        build = native()
        self.assert_codec_witness(build.codec)
        self.assert_product_codec(build.bridge())
        client, bridge = build.mutant("codec", "if(strcmp(order[i-1].key,order[i].key)==0)", "if(0)")
        path = build.work / "duplicate.json"
        run = subprocess.run([str(client), "canonical", str(path)], capture_output=True, text=True, timeout=10)
        self.assertEqual(0, run.returncode, run.stderr)
        response = product_preview(bridge, "1", duplicate=True)
        self.assertTrue(response["ok"], response)
        self.assertTrue(response["preview"]["valid"], response)
        self.assert_codec_witness(build.codec)
        self.assert_product_codec(build.bridge())


if __name__ == "__main__":
    unittest.main(verbosity=2)
