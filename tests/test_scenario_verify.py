"""Scenario closure checks against fresh native processes and real model replay.

The live World is a separate bridge process.  Its pending token must still be
confirmable after A/B verification, which catches isolation failures that a
read-only dump comparison alone cannot expose.
"""
from copy import deepcopy
import hashlib
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "geometry-core", ROOT / "geometry-web"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from tests import _bridge, binaries
from modeling import LEGACY_AXIOM_VERSIONS, ModelError
import scenario_verify as verifier
import space_modeling

CLI = ROOT / "geometry-web/scenario_verify.py"


def project(scene="", **fields):
    manifest = {"requiredCapabilities": [], "faces": [], "faceProjections": [],
                "reconstructionReviews": [], "models": []}
    manifest.update(fields)
    return {"manifest": manifest, "scene": scene}


def canonical_digest(value):
    data = json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def fresh_model_base():
    path = os.environ.get("GEOMETRY_MODEL_BASE")
    info = binaries.inspect_one(binaries.BY_NAME["model-base"], path=path)
    if info.state != "fresh" and path is None and not binaries.IS_WIN:
        with binaries.ProcessLock("build"):
            result = binaries.build_one(binaries.BY_NAME["model-base"], log=lambda *_: None)
        if not result.ok:
            raise unittest.SkipTest("model-base build failed: " + result.detail)
        info = binaries.inspect_one(binaries.BY_NAME["model-base"])
    if info.state != "fresh":
        raise unittest.SkipTest("model-base is not fresh: " + info.reason)
    return str(info.path)


class ScenarioNativeAcceptance(unittest.TestCase):
    def test_final_definition_receipt_uses_native_replay_after_reset_redefinition_and_crlf(self):
        def block(name, field, number):
            values=[('card',{'id':1,'name':name,'nextFieldId':2}),('field',{'parameterId':1,'id':1,'name':field,'type':0,'expression':{'op':'literal','num':str(number),'den':'1','unit':'mm'}})]
            return 'requires parameters/1\nparameters begin\n'+''.join('parameters '+kind+' '+base64.b64encode(json.dumps(value,ensure_ascii=False).encode()).decode()+'\n' for kind,value in values)+'parameters end\n'
        old,new=block('Old','Width',200),block('New','Length',300)
        for scene in (old+'reset\n',old+'reset\n'+new,old.replace('\n','\r\n')):
            with self.subTest(scene=scene), tempfile.TemporaryDirectory(prefix='scenario-final-definition-') as directory:
                source=Path(directory)/'original.scene';source.write_bytes(scene.encode())
                with _bridge.BridgeSession(self.bridge,cwd=directory) as oracle:
                    self.assertTrue(oracle.command('loadfile '+str(source))['ok'])
                    expected=oracle.command('dump')['text']
                    native_receipt=oracle.command('load-prepare '+str(source))
                    graph=oracle.command('source-inspect-file '+str(source))
                receipt=self.verify(project(scene,requiredCapabilities=['parameters/1']))
                self.assertEqual(receipt['final_scene'],expected)
                self.assertEqual(receipt['scene_sha256'],hashlib.sha256(scene.encode()).hexdigest())
                for invalid in (None,[],{'fake':'scene'}):
                    malformed={**native_receipt,'final_scene':invalid}
                    raw=(json.dumps(malformed)+'\n'+json.dumps(graph)+'\n').encode()
                    with mock.patch.object(verifier,'_run_bounded',return_value=raw):
                        self.reject(project(scene,requiredCapabilities=['parameters/1']),'SCENARIO_NATIVE_PROTOCOL')

    def test_candidate_boundary_fingerprint_summary_is_optional_complete_typed_and_exact(self):
        old = {"boundaries": [1, 2], "placements": []}
        self.assertEqual(verifier._final_objects(deepcopy(old)), old)
        entries = [{"id": 1, "geometryFingerprint": "a" * 64}, {"id": 2, "geometryFingerprint": "b" * 64}]
        complete = {**old, "boundaryFingerprints": entries}
        before = deepcopy(complete)
        self.assertIs(verifier._final_objects(complete), complete)
        self.assertEqual(complete, before)
        # Row order is not an identity rule; complete membership is required.
        self.assertEqual(verifier._final_objects({**old, "boundaryFingerprints": entries[::-1]})["boundaryFingerprints"], entries[::-1])
        self.assertEqual(verifier._final_objects({"boundaries": [], "placements": [], "boundaryFingerprints": []})["boundaryFingerprints"], [])
        invalid = [None, {}, "summary", [], entries[:1], [entries[0], entries[0]], entries + [entries[0]],
                   [entries[0], {"id": 3, "geometryFingerprint": "b" * 64}],
                   [entries[0], {"id": True, "geometryFingerprint": "b" * 64}],
                   [entries[0], {"id": "2", "geometryFingerprint": "b" * 64}],
                   [entries[0], {"id": 2.0, "geometryFingerprint": "b" * 64}],
                   [entries[0], {"id": 0, "geometryFingerprint": "b" * 64}],
                   [entries[0], {"id": -1, "geometryFingerprint": "b" * 64}],
                   [entries[0], {"id": 0x100000000, "geometryFingerprint": "b" * 64}],
                   [entries[0], {"id": 2, "geometryFingerprint": "B" * 64}],
                   [entries[0], {"id": 2, "geometryFingerprint": "b" * 63}],
                   [entries[0], {"id": 2, "geometryFingerprint": "b" * 65}],
                   [entries[0], {"id": 2, "geometryFingerprint": "g" * 64}],
                   [entries[0], {"id": 2, "geometryFingerprint": "b" * 64 + "\n"}],
                   [entries[0], {"id": 2, "geometryFingerprint": None}],
                   [entries[0], {"id": 2}], [entries[0], {**entries[1], "kind": "boundary"}]]
        for summary in invalid:
            with self.subTest(summary=summary):
                with self.assertRaises(ModelError) as caught:
                    verifier._final_objects({**old, "boundaryFingerprints": summary})
                self.assertEqual(caught.exception.code, "SCENARIO_NATIVE_PROTOCOL")
        for bad in [{**complete, "unknown": []}, {"boundaries": [1], "boundaryFingerprints": [entries[0]]},
                    {"boundaries": [], "placements": [], "boundaryFingerprints": [entries[0]]}]:
            with self.subTest(receipt=bad):
                with self.assertRaises(ModelError) as caught:
                    verifier._final_objects(bad)
                self.assertEqual(caught.exception.code, "SCENARIO_NATIVE_PROTOCOL")

    @classmethod
    def setUpClass(cls):
        cls.bridge = _bridge.find_bridge()
        cls.base = fresh_model_base()
        example = space_modeling.examples()["examples"][0]
        source = {key: deepcopy(example[key])
                  for key in ("base_scene", "placement_id", "settings")}
        source.update(mode="plan", obstacles=[])
        source["settings"]["wall_thickness"] = None
        result = space_modeling.preview(source, base_executable=cls.base)
        cls.model = {"id": "real-room", "name": "rectangle", "created_at": "2026-10-04T00:00:00Z",
                     "source": {"kind": "scene", "placement_id": 1, "boundary_id": 1,
                                "scene_hash": result["source_sha256"]},
                     "input": source, "result": result}

    def verify(self, value):
        original = deepcopy(value)
        try:
            return verifier.verify_project(value, bridge_executable=self.bridge,
                                           base_executable=self.base)
        finally:
            self.assertEqual(value, original, "verification must leave snapshot input untouched")

    def assert_final_objects(self, receipt, expected, scene):
        final = receipt['final_objects']
        self.assertEqual({key: final[key] for key in ('boundaries', 'placements')}, expected)
        self.assertEqual(set(final), {'boundaries', 'placements', 'boundaryFingerprints'})
        # Separate actual native World and full boundary reads. Never derive
        # expected pins with verify_project, _final_objects or load-prepare.
        with tempfile.TemporaryDirectory(prefix='scenario-boundary-oracle-') as directory:
            source = Path(directory) / 'oracle.scene'
            source.write_text(scene, encoding='utf-8')
            with _bridge.BridgeSession(self.bridge, cwd=directory) as oracle:
                self.assertTrue(oracle.command('loadfile ' + str(source))['ok'])
                entries = []
                for identifier in expected['boundaries']:
                    boundary = oracle.command('boundary ' + str(identifier))
                    self.assertTrue(boundary['ok'], boundary)
                    self.assertEqual(boundary['id'], identifier)
                    entries.append({'id': identifier, 'geometryFingerprint': boundary['geometryFingerprint']})
            self.assertEqual(oracle.process.returncode, 0)
        self.assertEqual(sorted(final['boundaryFingerprints'], key=lambda row: row['id']),
                         sorted(entries, key=lambda row: row['id']))
        return entries

    def reject(self, value, code):
        with self.assertRaises(ModelError) as caught:
            self.verify(value)
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def model_fault_worker(self, executable, directory, *, timeout=3):
        # Inject the fault below the public freshness gate in a private worker.
        # Exercise the real --model-worker path, including its bounded transport.
        # Production verify_project and its --model-worker retain that gate.
        worker = "\n".join([
            "import sys",
            "sys.path.insert(0, " + repr(str(ROOT / "geometry-web")) + ")",
            "import scenario_verify as verifier",
            "def fault_program(value, *, base=False):",
            "    if not base or value != sys.argv[1]:",
            "        raise AssertionError('unexpected fault fixture program lookup')",
            "    return str(value), 'fault-fixture'",
            "verifier._program = fault_program",
            "sys.exit(verifier.main(['--model-worker', '--base', sys.argv[1]]))",
        ])
        raw = verifier._run_bounded([sys.executable, "-c", worker, str(executable)],
                                    json.dumps({"models": [deepcopy(self.model)]}).encode(),
                                    cwd=directory, timeout=timeout, allowed_exit_codes=(0, 2))
        return json.loads(raw)

    def test_same_ids_in_a_and_b_are_isolated_from_live_pending_candidate(self):
        with tempfile.TemporaryDirectory(prefix="scenario-live-") as directory:
            with _bridge.BridgeSession(self.bridge, cwd=directory) as live:
                self.assertTrue(live.command("reset")["ok"])
                lines = [
                    "boundary 1 outline 0,0 4000,0 4000,3000 0,3000",
                    "placement 1 on boundary 1 origin 0 0 2500 u +x v +y",
                    "timber 90 20 20 role boundary", "place 90 on 1 at-face e0 +u +n",
                    "timber 91 20 20 role boundary", "place 91 on 1 at-face e2 +u +n",
                    "spec live_offset 500", "guide 1 1 v spec:live_offset",
                    "timber 3 27 33 role primary", "place 3 on 1 at-line guide 1 +v +n",
                ]
                for line in lines:
                    result = live.line(line)
                    self.assertTrue(result["ok"], result)
                scene_a = live.command("dump")["text"]
                before_refs = live.command("references")
                pending = live.line("spec live_offset 900")["preview"]
                self.assertTrue(pending["valid"], pending)
                a = project(scene_a)
                b = deepcopy(a)
                b["scene"] = scene_a.replace("4000", "6200").replace(
                    "spec live_offset 500", "spec live_offset 1300")
                self.assertNotEqual(a["scene"], b["scene"])
                receipt_a = self.verify(a)
                receipt_b = self.verify(b)
                self.assertTrue(receipt_a["ok"])
                self.assertTrue(receipt_b["ok"])
                expected = {"boundaries": [1],
                            "placements": [{"id": 1, "bid": 1, "horizontal": True}]}
                pins_a = self.assert_final_objects(receipt_a, expected, scene_a)
                pins_b = self.assert_final_objects(receipt_b, expected, b["scene"])
                self.assertNotEqual(pins_a, pins_b, 'Same native IDs do not prove identical geometry')
                forged = deepcopy(receipt_b)
                forged['final_objects']['boundaryFingerprints'] = pins_a
                with self.assertRaises(AssertionError):
                    self.assert_final_objects(forged, expected, b['scene'])
                self.assertEqual(receipt_a["scene_sha256"], hashlib.sha256(scene_a.encode()).hexdigest())
                self.assertNotEqual(receipt_a["scene_sha256"], receipt_b["scene_sha256"])
                self.assertNotEqual(receipt_a["inventory"]["sourceFingerprint"],
                                    receipt_b["inventory"]["sourceFingerprint"])
                identities = {(row["kind"], row["id"]) for row in receipt_a["objects"]}
                self.assertTrue({("boundary", 1), ("placement", 1), ("guide", 1)} <= identities)
                previous_receipt_a = deepcopy(receipt_a)
                receipt_b["inventory"]["nodes"][0]["id"] = 999
                self.assertEqual(receipt_a, previous_receipt_a,
                                 "B's returned mutable objects must not alias A")
                self.reject(project(b["scene"], faces=[{"bid": 99}]), "SCENARIO_REFERENCE")
                self.assertEqual(live.command("dump")["text"], scene_a)
                self.assertEqual(live.command("references"), before_refs)
                confirmed = live.line("confirm " + str(pending["token"]))
                self.assertTrue(confirmed["ok"], confirmed)
                member = next(t for t in live.command("references")["timbers"] if t["id"] == 3)
                self.assertEqual(member["geometry"]["centerline"], 900)
                self.assertEqual(a["scene"], scene_a)
                self.assertEqual(self.verify(a)["objects"], receipt_a["objects"])

    def test_deleted_boundary_is_checked_against_final_native_world(self):
        scene = "boundary 99 outline 0,0 100,0 100,100 0,100\ndelete boundary 99\n"
        receipt = self.verify(project(scene))
        self.assert_final_objects(receipt, {"boundaries": [], "placements": []}, scene)
        self.reject(project(scene, faces=[{"bid": 99}]), "SCENARIO_REFERENCE")
        self.reject(project(scene, reconstructionReviews=[{"bid": 99}]), "SCENARIO_REFERENCE")

    def test_projection_requires_matching_final_placement_and_horizontal_frame(self):
        projection = [{"bid": 1, "placement_id": 0}]
        horizontal = "boundary 1 outline 0,0 100,0 100,100 0,100\nplacement 0 on boundary 1 origin 0 0 0 u +x v +y\n"
        self.assertTrue(self.verify(project(horizontal, faceProjections=projection))["ok"])
        for scene in (horizontal + "delete placement 0\n",
                      horizontal.replace("u +x v +y", "u +x v +z")):
            with self.subTest(scene=scene):
                self.reject(project(scene, faceProjections=projection), "SCENARIO_REFERENCE")

    def test_projection_identity_rejects_boolean_and_container_values(self):
        scene = "boundary 1 outline 0,0 100,0 100,100 0,100\nplacement 0 on boundary 1 origin 0 0 0 u +x v +y\n"
        for identifier in (True, [], {}, -1, 0x100000000):
            with self.subTest(identifier=identifier):
                self.reject(project(scene, faceProjections=[{"bid": 1, "placement_id": identifier}]),
                            "SCENARIO_ID")

    def test_real_space_model_is_replayed_without_changing_its_source(self):
        value = project(self.model["input"]["base_scene"], models=[deepcopy(self.model)])
        self.assertTrue(self.verify(value)["ok"])
        self.assertEqual(value["manifest"]["models"][0]["result"]["summary"]["volume_mm3"],
                         "33600000000")

    def test_embedded_plan_source_with_null_boundary_is_preserved(self):
        model = deepcopy(self.model)
        model["input"]["base_scene"] = (
            "surface 1 origin 0 0 2500 u +x v +y rect 0 0 4000 3000\n")
        model["result"] = space_modeling.preview(model["input"], base_executable=self.base)
        model["source"].update(boundary_id=None, scene_hash=model["result"]["source_sha256"])
        self.assertEqual(model["result"]["summary"]["volume_mm3"], "33600000000")
        receipt = self.verify(project(model["input"]["base_scene"], models=[model]))
        self.assert_final_objects(receipt,
                                 {"boundaries": [], "placements": [{"id": 1, "bid": 0, "horizontal": True}]},
                                 model['input']['base_scene'])

    def test_faces_model_replays_full_multi_carrier_source_and_provenance(self):
        cases = json.loads((ROOT / "geometry-core/modeling-cases.json").read_text())["cases"]
        case = next(case for case in cases if case["id"] == "l_room_eight_faces")
        definitions = case["definitions"]
        uses = deepcopy(next(item for item in definitions["extensions"]
                             if item["kind"] == "shell")["uses"])
        uses[-1]["purpose"] = "calculation-cap"
        inputs = {"mode": "faces", "base_scene": definitions["base_scene"],
                  "uses": uses, "obstacles": []}
        result = space_modeling.preview(inputs, base_executable=self.base)
        self.assertEqual(result["summary"]["volume_mm3"], "68040000000")
        self.assertEqual(result["summary"]["generated_faces"], [])
        for placement, boundary in ((None, None), (1, 1), (None, 1)):
            with self.subTest(placement=placement, boundary=boundary):
                model = {"id": "faces-room", "name": "L room", "created_at": "2026-10-04T00:00:00Z",
                         "source": {"kind": "scene", "placement_id": placement, "boundary_id": boundary,
                                    "scene_hash": result["source_sha256"]},
                         "input": deepcopy(inputs), "result": deepcopy(result)}
                self.assertTrue(self.verify(project(inputs["base_scene"], models=[model]))["ok"])
        model["source"]["boundary_id"] = 99
        self.reject(project(inputs["base_scene"], models=[model]), "SCENARIO_MODEL_REPLAY")

    def test_legacy_optional_model_status_and_diagnostics_can_remain_absent(self):
        model = deepcopy(self.model)
        del model["result"]["ok"]
        del model["result"]["diagnostics"]
        self.assertTrue(self.verify(project(model["input"]["base_scene"], models=[model]))["ok"])

    def test_supported_legacy_packages_keep_external_generator_and_evidence_unchanged(self):
        for revision, axiom_hash in sorted(LEGACY_AXIOM_VERSIONS):
            with self.subTest(revision=revision):
                model = deepcopy(self.model)
                for name in ("space", "volume", "clearance", "walls"):
                    package = model["result"][name]
                    if package is None:
                        continue
                    package["manifest"].update(axiom_revision=revision, axiom_sha256=axiom_hash,
                                               generator={"name": "independent-original", "version": "7.2"})
                    package["diagnostics"] = [{"root": deepcopy(package["request"]["roots"][0]),
                                               "path": [], "code": "EXTERNAL_NOTE", "clause": "D25",
                                               "message": "Original generator evidence"}]
                    package["presentation"] = {"camera": [5, 8, 13], "canvas": {"x": -55, "y": 89}}
                value = project(model["input"]["base_scene"], models=[model])
                original = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
                self.assertTrue(self.verify(value)["ok"])
                self.assertEqual(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8"), original)
                for name in ("space", "volume", "clearance"):
                    package = value["manifest"]["models"][0]["result"][name]
                    self.assertEqual(package["manifest"]["axiom_revision"], revision)
                    self.assertEqual(package["manifest"]["axiom_sha256"], axiom_hash)
                    self.assertEqual(package["manifest"]["generator"],
                                     {"name": "independent-original", "version": "7.2"})
                    self.assertEqual(package["diagnostics"][0]["code"], "EXTERNAL_NOTE")
                    self.assertEqual(package["presentation"]["camera"], [5, 8, 13])

    def test_valid_saved_top_level_and_wall_diagnostic_evidence_can_differ_from_replay(self):
        model = deepcopy(self.model)
        evidence = {"root": deepcopy(model["result"]["space"]["request"]["roots"][0]),
                    "path": [], "code": "EXTERNAL_NOTE", "clause": "D25",
                    "message": "Original producer retained this explanatory note"}
        model["result"]["diagnostics"] = [deepcopy(evidence)]
        model["result"]["summary"]["wall_diagnostics"] = [deepcopy(evidence)]
        value = project(model["input"]["base_scene"], models=[model])
        self.assertTrue(self.verify(value)["ok"])
        self.assertEqual(value["manifest"]["models"][0]["result"]["diagnostics"], [evidence])
        self.assertEqual(value["manifest"]["models"][0]["result"]["summary"]["wall_diagnostics"], [evidence])

    def test_invalid_saved_package_metadata_and_rehashed_provenance_remain_rejected(self):
        def wrong_revision(package):
            package["manifest"]["axiom_revision"] = "0" * 40

        def wrong_axiom_hash(package):
            package["manifest"]["axiom_sha256"] = "0" * 64

        def empty_generator_name(package):
            package["manifest"]["generator"]["name"] = ""

        def empty_generator_version(package):
            package["manifest"]["generator"]["version"] = ""

        def extra_manifest_field(package):
            package["manifest"]["unexpected"] = "must not be discarded"

        def forged_provenance(package):
            package["derived"]["objects"][0]["face_sources"][0][0]["placement_id"] = 99
            package["manifest"]["geometry_sha256"] = canonical_digest(package["derived"])

        for alter in (wrong_revision, wrong_axiom_hash, empty_generator_name,
                      empty_generator_version, extra_manifest_field, forged_provenance):
            with self.subTest(tamper=alter.__name__):
                model = deepcopy(self.model)
                alter(model["result"]["volume"])
                self.reject(project(model["input"]["base_scene"], models=[model]),
                            "SCENARIO_MODEL_REPLAY")

    def test_unknown_result_or_summary_fields_and_malformed_diagnostics_are_rejected(self):
        for location, field, value in (("result", "unexpected", True),
                                       ("summary", "unexpected", True),
                                       ("result", "diagnostics", "not an array"),
                                       ("summary", "wall_diagnostics", "not an array")):
            with self.subTest(location=location, field=field):
                model = deepcopy(self.model)
                target = model["result"] if location == "result" else model["result"]["summary"]
                target[field] = value
                with self.assertRaises(ModelError) as caught:
                    self.verify(project(model["input"]["base_scene"], models=[model]))
                self.assertEqual(caught.exception.status, "INVALID")

    @unittest.skipIf(os.name == "nt", "temporary shebang executables are POSIX test fixtures")
    def test_model_timeout_stops_its_base_child_before_it_can_finish_late(self):
        with tempfile.TemporaryDirectory(prefix="scenario-model-timeout-") as directory:
            marker = Path(directory) / "child.pid"
            executable = Path(directory) / "sleeping-base"
            executable.write_text("#!" + sys.executable + "\nimport os, pathlib, time\n"
                                  "pathlib.Path(" + repr(str(marker)) + ").write_text(str(os.getpid()))\n"
                                  "time.sleep(10)\n", encoding="utf-8")
            executable.chmod(0o700)
            child = None
            try:
                with self.assertRaises(ModelError) as caught:
                    self.model_fault_worker(executable, directory, timeout=0.5)
                self.assertEqual(caught.exception.code, "SCENARIO_NATIVE_TIMEOUT")
                self.assertTrue(marker.exists(), "The base child must have started for this oracle")
                child = int(marker.read_text())
                state = Path("/proc") / str(child) / "stat"
                if state.exists():
                    self.assertEqual(state.read_text().split()[2], "Z",
                                     "A model timeout left its native base child running")
                else:
                    with self.assertRaises(ProcessLookupError):
                        os.kill(child, 0)
            finally:
                if child is None and marker.exists():
                    child = int(marker.read_text())
                if child is not None:
                    try:
                        import signal
                        os.kill(child, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    @unittest.skipIf(os.name == "nt", "temporary shebang executables are POSIX test fixtures")
    def test_model_base_stdout_and_stderr_are_bounded_inside_worker(self):
        with tempfile.TemporaryDirectory(prefix="scenario-model-output-") as directory:
            executable = Path(directory) / "flooding-base"
            for descriptor, count in ((1, verifier.MAX_OUTPUT_BYTES // 65536 + 1),
                                      (2, verifier.MAX_STDERR_BYTES // 65536 + 1)):
                with self.subTest(descriptor=descriptor):
                    executable.write_text("#!" + sys.executable + "\nimport os, time\n"
                                          "for _ in range(" + str(count) + "):\n"
                                          "    os.write(" + str(descriptor) + ", b'x' * 65536)\n"
                                          "time.sleep(10)\n", encoding="utf-8")
                    executable.chmod(0o700)
                    started = time.monotonic()
                    result = self.model_fault_worker(executable, directory)
                    self.assertFalse(result["ok"])
                    self.assertEqual(result["code"], "SCENARIO_NATIVE_CAPACITY")
                    self.assertLess(time.monotonic() - started, 3,
                                    "Output caps must stop the base before its sleep completes")

    @unittest.skipIf(os.name == "nt", "temporary shebang executables are POSIX test fixtures")
    def test_native_bytes_changed_during_verification_invalidate_the_receipt(self):
        with tempfile.TemporaryDirectory(prefix="scenario-runtime-tamper-") as directory:
            executable = Path(directory) / "changing-bridge"
            executable.write_text("#!" + sys.executable + "\nimport pathlib, subprocess, sys\n"
                                  "path = pathlib.Path(__file__)\n"
                                  "path.write_bytes(path.read_bytes() + b'# changed during verification\\n')\n"
                                  "result = subprocess.run([" + repr(self.bridge) + "], "
                                  "input=sys.stdin.buffer.read(), capture_output=True)\n"
                                  "sys.stdout.buffer.write(result.stdout)\n"
                                  "sys.stderr.buffer.write(result.stderr)\n"
                                  "sys.exit(result.returncode)\n", encoding="utf-8")
            executable.chmod(0o700)
            before = hashlib.sha256(executable.read_bytes()).hexdigest()
            def identified_program(value, *, base=False):
                path = Path(value).resolve()
                return str(path), hashlib.sha256(path.read_bytes()).hexdigest()

            # Isolate the post-execution pin check. Separate tests exercise the
            # public API's actual rejection of unknown and stale executables.
            with mock.patch.object(verifier, "_program", side_effect=identified_program), \
                    mock.patch.object(verifier, "_source_receipt", return_value="0" * 64):
                with self.assertRaises(ModelError) as caught:
                    verifier.verify_project(project(), bridge_executable=str(executable))
            self.assertEqual(caught.exception.code, "SCENARIO_RUNTIME_CHANGED")
            self.assertNotEqual(hashlib.sha256(executable.read_bytes()).hexdigest(), before)

    def test_copied_fresh_binary_with_bytes_or_source_receipt_tampered_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="scenario-build-receipt-") as directory:
            for tamper in ("binary-bytes", "source-fingerprint", "missing-sidecar"):
                with self.subTest(tamper=tamper):
                    executable = Path(directory) / (tamper + (".exe" if os.name == "nt" else ""))
                    shutil.copy2(self.bridge, executable)
                    source_sidecar = Path(self.bridge + binaries.SIDECAR_SUFFIX)
                    sidecar = Path(str(executable) + binaries.SIDECAR_SUFFIX)
                    shutil.copy2(source_sidecar, sidecar)
                    info = binaries.inspect_one(binaries.BY_NAME["bridge"], executable)
                    self.assertEqual(info.state, "fresh", info.reason)
                    if tamper == "binary-bytes":
                        stamp = executable.stat()
                        executable.write_bytes(executable.read_bytes() + b"tampered")
                        os.utime(executable, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
                    elif tamper == "source-fingerprint":
                        receipt = json.loads(sidecar.read_text())
                        receipt["fingerprint"] = "0" * 64
                        sidecar.write_text(json.dumps(receipt), encoding="utf-8")
                    else:
                        sidecar.unlink()
                    with mock.patch.object(verifier, "_run_bounded", side_effect=AssertionError("stale runtime launched")):
                        with self.assertRaises(ModelError) as caught:
                            verifier.verify_project(project(), bridge_executable=str(executable))
                    self.assertEqual(caught.exception.code, "SCENARIO_RUNTIME_UNKNOWN")
                    self.assertEqual(caught.exception.status, "UNSUPPORTED")

    def test_fresh_binary_build_receipt_must_match_its_requested_adapter_role(self):
        cases = [(project(), {"bridge_executable": self.base}),
                 (project(self.model["input"]["base_scene"], models=[deepcopy(self.model)]),
                  {"bridge_executable": self.bridge, "base_executable": self.bridge})]
        for value, executables in cases:
            with self.subTest(executables=executables):
                with mock.patch.object(verifier, "_run_bounded", side_effect=AssertionError("wrong adapter role launched")):
                    with self.assertRaises(ModelError) as caught:
                        verifier.verify_project(value, **executables)
                self.assertEqual(caught.exception.code, "SCENARIO_RUNTIME_UNKNOWN")
                self.assertEqual(caught.exception.status, "UNSUPPORTED")

    def test_native_inventory_key_version_and_field_must_match_typed_identity(self):
        with tempfile.TemporaryDirectory(prefix="scenario-typed-graph-") as directory:
            source = Path(directory) / "input.scene"
            source.write_text("boundary 1 outline 0,0 100,0 100,100 0,100\n", encoding="utf-8")
            with _bridge.BridgeSession(self.bridge, cwd=directory) as bridge:
                graph = bridge.command("source-inspect-file " + str(source))
            final = {"boundaries": [1], "placements": []}
            objects, _ = verifier._inventory(graph, final)
            self.assertEqual(objects, [{"kind": "boundary", "id": 1, "version": None}])
            for field, value in (("key", "boundary:99"), ("version", 1), ("fieldId", 1)):
                with self.subTest(field=field):
                    forged = deepcopy(graph)
                    forged["nodes"][0][field] = value
                    with self.assertRaises(ModelError) as caught:
                        verifier._inventory(forged, final)
                    self.assertEqual(caught.exception.code, "SCENARIO_NATIVE_PROTOCOL")

    def test_unicode_native_spec_identity_is_preserved_exactly(self):
        receipt = self.verify(project("spec 尺寸 500\n"))
        self.assertEqual(receipt["objects"], [{"kind": "spec", "id": "尺寸", "version": None}])
        self.assertEqual(receipt["inventory"]["nodes"][0]["key"], "spec:尺寸")
        self.assertEqual(receipt["inventory"]["nodes"][0]["id"], "尺寸")

    def test_raw_utf8_json_bytes_reach_real_native_verification(self):
        scene = "boundary 3 outline 0,0 100,0 100,100 0,100\nspec 尺寸 500\n"
        raw = json.dumps(project(scene), ensure_ascii=False).encode("utf-8")
        receipt = verifier.verify_bytes(raw, bridge_executable=self.bridge, base_executable=self.base)
        self.assertTrue(receipt["ok"])
        self.assert_final_objects(receipt, {"boundaries": [3], "placements": []}, scene)
        self.assertEqual(receipt["scene_sha256"], hashlib.sha256(scene.encode("utf-8")).hexdigest())
        self.assertEqual({(row["kind"], row["id"]) for row in receipt["objects"]},
                         {("boundary", 3), ("spec", "尺寸")})

    def test_model_source_and_self_consistent_result_tampering_cannot_pass(self):
        def forged_source(model):
            model["source"]["scene_hash"] = "0" * 64

        def forged_summary(model):
            model["result"]["summary"]["volume_mm3"] = "1"

        def forged_geometry(model):
            package = model["result"]["volume"]
            package["derived"]["objects"][0]["volume_mm3"] = "1"
            # The package's declared hash is deliberately made self-consistent.
            # Only a real replay can still detect this forged geometric result.
            package["manifest"]["geometry_sha256"] = canonical_digest(package["derived"])

        for alter in (forged_source, forged_summary, forged_geometry):
            with self.subTest(tamper=alter.__name__):
                model = deepcopy(self.model)
                alter(model)
                self.reject(project(model["input"]["base_scene"], models=[model]),
                            "SCENARIO_MODEL_REPLAY")

    def test_unknown_required_capability_is_explicitly_unsupported(self):
        for value in (project(requiredCapabilities=["future-scenario/99"]),
                      project("requires future-scenario/99\n")):
            with self.subTest(value=value):
                error = self.reject(value, "SCENARIO_CAPABILITY")
                self.assertEqual(error.status, "UNSUPPORTED")

    def test_known_capability_marker_is_preserved_even_without_live_objects(self):
        for capability in ("engineering-spec/1", "parameters/1",
                           "assembly-rule-authoring/1", "assembly-timber-generation/1"):
            with self.subTest(capability=capability):
                receipt = self.verify(project("requires " + capability + "\n",
                                              requiredCapabilities=[capability]))
                self.assertTrue(receipt["ok"])
                self.assertEqual(receipt["requiredCapabilities"], [capability])
                self.assertIn(capability, receipt["capabilities"])

    def test_legacy_scene_accepts_current_bridge_offer_without_promoting_requirements(self):
        scene = "boundary 3 outline 0,0 100,0 100,100 0,100\nspec stable 500\n"
        receipt = self.verify(project(scene, requiredCapabilities=["engineering-spec/1"]))
        self.assertTrue(receipt["ok"])
        self.assertIn("grid-subdivision-rules/1", receipt["capabilities"])
        self.assertEqual(receipt["requiredCapabilities"], ["engineering-spec/1"])
        self.assert_final_objects(receipt, {"boundaries": [3], "placements": []}, scene)
        self.assertEqual(receipt["scene_sha256"], hashlib.sha256(scene.encode()).hexdigest())

    def test_actual_source_rule_scene_uses_current_reader_and_rejects_stripped_requirements(self):
        with tempfile.TemporaryDirectory(prefix="scenario-source-rule-") as directory:
            with _bridge.BridgeSession(self.bridge, cwd=directory) as native:
                self.assertTrue(native.command("reset")["ok"])
                for command in (
                        "grid-system 0 name-hex 736f75726365 main-along none u repeat 0 600 v repeat 0 400",
                        "grid-source-rule 0 create name-hex 72756c65 selector all-cells divide 3 2"):
                    result = native.line(command)
                    if "preview" in result:
                        self.assertTrue(result["preview"]["valid"], result)
                        result = native.line("confirm " + str(result["preview"]["token"]))
                    self.assertTrue(result["ok"], result)
                scene = native.command("dump")["text"]
                self.assertIn("grid-source-rule", scene)
                self.assertIn("requires grid-subdivision-rules/1\n", scene)
                source = Path(directory) / "original.scene"
                source.write_text(scene, encoding="utf-8")
                prepared = native.command("load-prepare " + str(source))
                self.assertTrue(prepared["ok"], prepared)
                self.assertIn("grid-subdivision-rules/1", prepared["required_capabilities"])
                for required in ([], ["unknown-grid-subdivision/1"]):
                    error = self.reject(project(scene, requiredCapabilities=required), "SCENARIO_CAPABILITY")
                    self.assertEqual(error.status, "UNSUPPORTED")
                receipt = self.verify(project(scene, requiredCapabilities=["grid-subdivision-rules/1"]))
                self.assertTrue(receipt["ok"])
                self.assertIn("grid-subdivision-rules/1", receipt["requiredCapabilities"])
                self.assertEqual(receipt["scene_sha256"], hashlib.sha256(scene.encode("utf-8")).hexdigest())
                without_marker = scene.replace("requires grid-subdivision-rules/1\n", "")
                stripped = Path(directory) / "stripped.scene"
                stripped.write_text(without_marker, encoding="utf-8")
                self.assertFalse(native.command("load-prepare " + str(stripped))["ok"])
                self.assertEqual(self.reject(project(without_marker), "SCENARIO_CAPABILITY").status, "UNSUPPORTED")
                self.assertEqual(source.read_text(encoding="utf-8"), scene)
                self.assertEqual(native.command("dump")["text"], scene)

    def test_generation_scene_preserves_three_owned_members(self):
        with zipfile.ZipFile(ROOT / "geometry-web/examples/assembly-generation-v1.gcanvas") as archive:
            scene = archive.read("world.scene").decode("utf-8")
            manifest = json.loads(archive.read("manifest.json"))
        receipt = self.verify({"scene": scene, "manifest": manifest})
        self.assertTrue(receipt["ok"])
        self.assertIn("assembly-timber-generation/1", receipt["capabilities"])
        self.assertIn("assembly-timber-generation/1", receipt["requiredCapabilities"])
        self.assertEqual(sum(line.startswith("owned 1 ") and " timber " in line
                             for line in scene.splitlines()), 3)
        owned = {node["id"]: node["nativeOwner"] for node in receipt["inventory"]["nodes"]
                 if node["kind"] == "timber" and node.get("nativeOwner") is not None}
        self.assertEqual(set(owned), {1, 2, 3})
        for timber, owner in owned.items():
            self.assertEqual({name: owner[name] for name in
                              ("instanceId", "memberId", "bindingId", "ruleId", "ruleVersion")},
                             {"instanceId": 1, "memberId": timber, "bindingId": 1,
                              "ruleId": 1, "ruleVersion": 1})
            for name in ("ruleFingerprint", "instanceFingerprint", "bindingFingerprint"):
                self.assertRegex(owner[name], r"^[0-9a-f]{64}$")
        self.assertEqual({row["id"] for row in receipt["objects"] if row["kind"] == "timber"},
                         {1, 2, 3, 90, 91})
        unowned = [node for node in receipt["inventory"]["nodes"]
                   if node["kind"] == "timber" and node["id"] in (90, 91)]
        self.assertEqual([node["nativeOwner"] for node in unowned], [None, None])

    def test_cli_reports_real_final_inventory_and_structured_failure(self):
        environment = dict(os.environ)
        environment.update(GEOMETRY_SCENARIO_BRIDGE=self.bridge, GEOMETRY_SCENARIO_BASE=self.base)
        scene = "boundary 3 outline 0,0 100,0 100,100 0,100\n"
        for value, code in ((project(scene), 0), (project(scene, faces=[{"bid": 99}]), 2)):
            with self.subTest(exit_code=code):
                run = subprocess.run([sys.executable, str(CLI)], input=json.dumps(value),
                                     cwd=ROOT, env=environment, text=True, capture_output=True, timeout=30)
                self.assertEqual(run.returncode, code, run.stderr)
                result = json.loads(run.stdout)
                self.assertEqual(result["ok"], code == 0)
                if code == 0:
                    self.assertEqual(result["final_objects"]["boundaries"], [3])
                else:
                    self.assertEqual(result["code"], "SCENARIO_REFERENCE")
                    self.assertIn(result["status"], ("INVALID", "UNSUPPORTED"))
                    self.assertIsInstance(result["message"], str)
                    self.assertIsInstance(result["path"], list)


@unittest.skipIf(os.name == "nt", "temporary shebang executables are POSIX test fixtures")
class ScenarioExecutionBoundaries(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="scenario-executor-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def executable(self, body):
        path = self.directory / "mock-bridge"
        path.write_text("#!" + sys.executable + "\n" + body + "\n", encoding="utf-8")
        path.chmod(0o700)
        return str(path)

    def reject(self, body, code):
        with self.assertRaises(ModelError) as caught:
            verifier._run_bounded([self.executable(body)], b"", cwd=self.directory,
                                  timeout=verifier.BRIDGE_TIMEOUT)
        self.assertEqual(caught.exception.code, code)

    def test_crashed_native_process_never_returns_verified_receipt(self):
        self.reject("import os, signal\nos.kill(os.getpid(), signal.SIGKILL)", "SCENARIO_NATIVE_EXIT")

    def test_native_timeout_is_bounded_and_rejected(self):
        started = time.monotonic()
        with mock.patch.object(verifier, "BRIDGE_TIMEOUT", 0.1):
            self.reject("import time\ntime.sleep(10)", "SCENARIO_NATIVE_TIMEOUT")
        self.assertLess(time.monotonic() - started, 2)

    def test_excessive_native_stdout_and_stderr_are_stopped_and_rejected(self):
        for stream, limit in (("stdout", "MAX_OUTPUT_BYTES"), ("stderr", "MAX_STDERR_BYTES")):
            with self.subTest(stream=stream), mock.patch.object(verifier, limit, 1024):
                started = time.monotonic()
                self.reject("import sys, time\nsys." + stream + ".buffer.write(b'x' * 2048)\n"
                            "sys." + stream + ".buffer.flush()\ntime.sleep(10)",
                            "SCENARIO_NATIVE_CAPACITY")
                self.assertLess(time.monotonic() - started, 2,
                                "A stalled writer must be stopped as soon as its cap is exceeded")

    def test_forged_success_without_complete_typed_inventory_is_rejected(self):
        with self.assertRaises(ModelError) as caught:
            verifier._inventory({"ok": True}, {"boundaries": [], "placements": []})
        self.assertEqual(caught.exception.code, "SCENARIO_NATIVE_PROTOCOL")

    def test_unknown_runtime_is_rejected_before_the_executable_can_run(self):
        marker = self.directory / "launched"
        executable = self.executable("from pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('ran')")
        with self.assertRaises(ModelError) as caught:
            verifier.verify_project(project(), bridge_executable=executable)
        self.assertEqual(caught.exception.code, "SCENARIO_RUNTIME_UNKNOWN")
        self.assertEqual(caught.exception.status, "UNSUPPORTED")
        self.assertFalse(marker.exists())


class ScenarioInputBoundaries(unittest.TestCase):
    def test_raw_bytes_reject_duplicates_capacity_and_type_before_native_launch(self):
        cases = [
            ("duplicate key", b'{"manifest":{},"manifest":{},"scene":""}', "SCENARIO_JSON"),
            ("oversized bytes", b" " * (verifier.MAX_INPUT_BYTES + 1), "SCENARIO_CAPACITY"),
            ("decoded text", "{}", "SCENARIO_JSON"),
            ("mutable bytearray", bytearray(b"{}"), "SCENARIO_JSON"),
            ("parsed object", {}, "SCENARIO_JSON"),
        ]
        for name, raw, code in cases:
            with self.subTest(name=name):
                with mock.patch.object(verifier, "_run_bounded", side_effect=AssertionError("invalid bytes launched native")):
                    with self.assertRaises(ModelError) as caught:
                        verifier.verify_bytes(raw, bridge_executable="missing-scenario-test-executable")
                self.assertEqual(caught.exception.code, code)

    def test_scene_capacity_counts_utf8_bytes_before_launching_any_executable(self):
        oversized = "é" * (verifier.MAX_SCENE_BYTES // 2 + 1)
        with self.assertRaises(ModelError) as caught:
            verifier.verify_project(project(oversized), bridge_executable="missing-scenario-test-executable")
        self.assertEqual(caught.exception.code, "SCENARIO_CAPACITY")
        self.assertEqual(caught.exception.status, "UNSUPPORTED")

    def test_cli_rejects_duplicate_nonfinite_and_oversized_input_as_json_failure(self):
        payloads = [
            ('{"manifest":{},"manifest":{},"scene":""}', "SCENARIO_JSON"),
            ('{"manifest":{"unused":NaN},"scene":""}', "SCENARIO_JSON"),
            (" " * (verifier.MAX_INPUT_BYTES + 1), "SCENARIO_CAPACITY"),
        ]
        for payload, code in payloads:
            with self.subTest(code=code, bytes=len(payload)):
                run = subprocess.run([sys.executable, str(CLI), "--bridge", "missing-scenario-test-executable"],
                                     input=payload, cwd=ROOT, text=True, capture_output=True, timeout=10)
                self.assertEqual(run.returncode, 2, run.stderr)
                result = json.loads(run.stdout)
                self.assertFalse(result["ok"])
                self.assertEqual(result["code"], code)
                self.assertIsInstance(result["path"], list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
