"""PF-6/#438 integration: real native terminal commands retain foreign candidates.

These are CLI/native tests, not browser evidence. Existing PF-6 and framing
fixtures remain independently owned. No counts, golden values or timeouts are
changed. Each rejected operation is followed by the original owner's exact
confirm/cancel and by observable undo/redo checks.
"""
import copy
import json
from pathlib import Path
import subprocess
import unittest

from tests import test_panel_fill_builder as pf6
from tests import test_framing_template as framing


class BuilderTokenOwners(unittest.TestCase):
    setUpClass = pf6.PanelFillBuilder.__dict__["setUpClass"]
    setUp = pf6.PanelFillBuilder.setUp
    command = pf6.PanelFillBuilder.command
    load_text = pf6.PanelFillBuilder.load_text
    read = pf6.PanelFillBuilder.read
    preview = pf6.PanelFillBuilder.preview
    apply = pf6.PanelFillBuilder.apply
    seed = pf6.PanelFillBuilder.seed
    require_builder = pf6.PanelFillBuilder.require_builder
    fixture = pf6.PanelFillBuilder.fixture
    request = pf6.PanelFillBuilder.request
    commit_line = pf6.PanelFillBuilder.commit_line
    suggest_request = pf6.PanelFillBuilder.suggest_request
    suggest = pf6.PanelFillBuilder.suggest
    select_request = pf6.PanelFillBuilder.select_request
    select = pf6.PanelFillBuilder.select
    all_keys = pf6.PanelFillBuilder.all_keys
    formal_snapshot = pf6.PanelFillBuilder.formal_snapshot

    def packet(self, command, value):
        path = self.directory / "owner-request.json"
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8", newline="\n")
        return self.command(command + " " + str(path))

    def seed_framing(self):
        self.assertTrue(self.command("reset")["ok"])
        self.commit_line("surface 1 origin 0 0 2500 u +x v +y outline 0,0 3740,0 3740,2000 0,2000")
        revision = self.command("engineering-read")["revision"]
        result = self.packet("engineering-preview", {
            "schema": "engineering-transaction/1", "expectedRevision": revision,
            "operations": [
                {"op": "publish-material", "value": {"id": "r03-board", "version": 1,
                 "kind": "panel", "name": "明選試驗板材", "width": 915, "length": 1830, "thickness": "6"}},
                {"op": "put-parameter", "value": {"id": 90, "name": "承接", "fields": [
                 {"id": 1, "name": "X", "type": "dimension", "input": "8"}]}}]})
        self.assertTrue(result["ok"] and result["preview"]["valid"], result)
        self.assertTrue(self.command("engineering-confirm " + str(result["preview"]["token"]))["ok"])

    def framing_pending(self):
        read = self.packet("framing-template-read", {"schema": "framing-template-read/1", "boundaryId": 1})
        self.assertTrue(read["ok"], read)
        result = self.packet("framing-template-preview", {
            "schema": "framing-template-generate/1", "expectedRevision": read["revision"],
            "contextKey": read["contextKey"], "definitionFingerprint": read["definitionFingerprint"],
            "boundaryId": 1, "on": 1,
            "template": {"id": "flat-ceiling", "version": 1, "policyFingerprint": framing.POLICY},
            "parameters": copy.deepcopy(framing.PARAMETERS),
            "sources": {"panel": {"id": "r03-board", "version": 1},
                        "threshold": {"parameterId": 90, "fieldId": 1}},
            "layout": {"corner": "min-min", "lengthAlong": "v"},
            "material": {"boundary": "rc", "timber": "literal"}})
        self.assertTrue(result["ok"] and result["preview"]["valid"], "PF6_OWNER_FRAMING_REAL_CANDIDATE: " + str(result))
        return {"owner": "framing-template", "token": result["preview"]["token"], "ownerKey": result["ownerKey"]}

    def history_sentinel(self):
        self.assertTrue(self.command("identity-epoch " + "78" * 16)["ok"])
        self.history_previous = self.command("dump")["text"]
        self.commit_line("spec owner_history 901")
        self.history_current = self.command("dump")["text"]
        self.commit_line("spec owner_history 902")
        self.history_redo = self.command("dump")["text"]
        self.commit_line("undo")
        self.assertEqual(self.history_current, self.command("dump")["text"], "PF6_OWNER_HISTORY_FIXTURE")

    def pending(self, owner):
        # Use an actual prior framing owner's key, not an invalid syntax input.
        self.seed_framing()
        old_framing = self.framing_pending()
        old_key = old_framing["ownerKey"]
        self.assertTrue(self.command(self.terminal(old_framing, "cancel"))["cancelled"])
        if owner == "pf6":
            self.fixture()
        elif owner == "engineering":
            self.assertTrue(self.command("reset")["ok"])
        self.history_sentinel()
        if owner == "pf6":
            suggestion = self.suggest()
            selected = self.select(suggestion, self.all_keys(suggestion))
            self.assertTrue(selected["valid"], "PF6_OWNER_REAL_SELECTED_CANDIDATE")
            pending = {"owner": owner, "token": selected["token"]}
        elif owner == "framing-template":
            pending = self.framing_pending()
        else:
            revision = self.command("engineering-read")["revision"]
            result = self.packet("engineering-preview", {
                "schema": "engineering-transaction/1", "expectedRevision": revision,
                "operations": [{"op": "put-parameter", "value": {"id": 91, "name": "交易所有者測試",
                    "fields": [{"id": 1, "name": "A", "type": "dimension", "input": "27"}]}}]})
            self.assertTrue(result["ok"] and result["preview"]["valid"], result)
            pending = {"owner": owner, "token": result["preview"]["token"]}
        pending["foreignFramingKey"] = old_key
        return pending

    @staticmethod
    def terminal(pending, action, owner=None):
        owner = owner or pending["owner"]
        value = owner + "-" + action + " " + str(pending["token"])
        if owner == "framing-template":
            key = pending["ownerKey"] if pending["owner"] == owner else pending["foreignFramingKey"]
            value += " " + key
        elif owner == "boundary-pair":
            # Valid key syntax reaches the native kind/owner check.
            value += " " + pending["foreignFramingKey"]
        return value

    def retained_candidate(self, pending, action, before):
        result = self.command(self.terminal(pending, action))
        self.assertTrue(result["ok"], "PF6_OWNER_ORIGINAL_TOKEN_RETAINED: " + str(result))
        if action == "cancel":
            self.assertTrue(result["cancelled"], "PF6_OWNER_ORIGINAL_CANCEL_RETAINED")
            self.assertEqual(before, self.formal_snapshot(), "PF6_OWNER_CANCEL_ZERO_WRITE")
            # A hidden history record would have erased this redo branch.
            self.commit_line("redo")
            self.assertEqual(self.history_redo, self.command("dump")["text"], "PF6_OWNER_FOREIGN_REJECT_PRESERVES_REDO")
            self.commit_line("undo")
        else:
            self.assertTrue(result["history_changed"], "PF6_OWNER_ORIGINAL_CONFIRM_ONE_WRITE")
            self.assertEqual(before["revision"] + 1, self.read()["revision"], "PF6_OWNER_SINGLE_REVISION")
            self.commit_line("undo")
        self.assertEqual(self.history_current, self.command("dump")["text"], "PF6_OWNER_ONE_UNDO_RESTORES_BEFORE")
        self.commit_line("undo")
        self.assertEqual(self.history_previous, self.command("dump")["text"], "PF6_OWNER_NO_HIDDEN_HISTORY_ENTRY")

    def reject_foreign(self, owner, foreign, action):
        pending = self.pending(owner)
        before = self.formal_snapshot()
        command = ("line cancel-preview" if foreign == "line" and action == "cancel" else
                   "line confirm " + str(pending["token"]) if foreign == "line" else
                   self.terminal(pending, action, foreign))
        result = self.command(command)
        marker = "PF6_OWNER_" + owner.upper().replace("-", "_") + "_REJECTS_" + foreign.upper().replace("-", "_") + "_" + action.upper()
        if action == "cancel" and foreign not in ("line", "framing-template", "boundary-pair"):
            self.assertIs(result.get("cancelled"), False, marker + ": " + str(result))
        else:
            self.assertIs(result.get("ok"), False, marker + ": " + str(result))
        self.assertFalse(result.get("history_changed", False), marker + "_HISTORY_ZERO_WRITE")
        self.assertEqual(before, self.formal_snapshot(), marker + "_WORLD_REVISION_IDENTITY_IDS_ZERO_WRITE")
        self.retained_candidate(pending, action, before)

    def test_pf6_and_framing_reject_each_others_confirmation_and_cancellation(self):
        for owner, foreign in (("pf6", "framing-template"), ("framing-template", "pf6")):
            for action in ("confirm", "cancel"):
                with self.subTest(owner=owner, foreign=foreign, action=action):
                    self.reject_foreign(owner, foreign, action)

    def test_general_batch_cannot_consume_pf6_or_framing_candidates(self):
        for owner in ("pf6", "framing-template"):
            for foreign in ("engineering", "assembly", "section-profile", "panel-fill"):
                for action in ("confirm", "cancel"):
                    with self.subTest(owner=owner, foreign=foreign, action=action):
                        self.reject_foreign(owner, foreign, action)

    def test_pf6_and_framing_cannot_consume_engineering_candidate(self):
        for foreign in ("pf6", "framing-template"):
            for action in ("confirm", "cancel"):
                with self.subTest(foreign=foreign, action=action):
                    self.reject_foreign("engineering", foreign, action)

    def test_other_terminal_owners_preserve_builder_candidates(self):
        for owner in ("pf6", "framing-template"):
            for foreign in ("line", "definition-import", "timber-edit", "boundary-pair", "load"):
                for action in ("confirm", "cancel"):
                    with self.subTest(owner=owner, foreign=foreign, action=action):
                        self.reject_foreign(owner, foreign, action)

    def simultaneous_load(self, pending, before):
        path = self.directory / "simultaneous-load.scene"
        path.write_text(before["dump"] + "spec owner_import 777\n", encoding="utf-8", newline="\n")
        # On the old independent allocator, walk actual load previews until
        # its counter catches the live builder token. On the shared allocator,
        # the first load token is already newer. No invented token is sent.
        for unused in range(pending["token"] + 1):
            result = self.command("load-prepare " + str(path))
            self.assertTrue(result["ok"], "PF6_OWNER_SIMULTANEOUS_LOAD_PREPARED: " + str(result))
            if result["token"] >= pending["token"]:
                return result
        self.fail("PF6_OWNER_LOAD_ALLOCATOR_DID_NOT_ADVANCE")

    def test_simultaneous_load_and_builders_reject_both_foreign_terminals(self):
        for owner in ("pf6", "framing-template"):
            for direction in ("builder-to-load", "load-to-builder"):
                for action in ("confirm", "cancel"):
                    # Separate continuations prove each retained candidate is
                    # still confirmable before a valid commit changes revision.
                    for commit_owner in ("builder", "load"):
                        with self.subTest(owner=owner, direction=direction, action=action, commit_owner=commit_owner):
                            pending = self.pending(owner)
                            before = self.formal_snapshot()
                            loading = self.simultaneous_load(pending, before)
                            self.assertEqual(before, self.formal_snapshot(), "PF6_OWNER_DUAL_PREVIEW_ZERO_WRITE")
                            if direction == "builder-to-load":
                                command = "load-" + action + " " + str(pending["token"])
                            else:
                                foreign = dict(pending, token=loading["token"])
                                command = self.terminal(foreign, action)
                            result = self.command(command)
                            marker = "PF6_OWNER_SHARED_LOAD_TOKEN: " + owner + "/" + direction + "/" + action
                            if action == "cancel" and (direction == "builder-to-load" or owner == "pf6"):
                                self.assertIs(result.get("cancelled"), False, marker + ": " + str(result))
                            else:
                                self.assertIs(result.get("ok"), False, marker + ": " + str(result))
                            self.assertNotEqual(pending["token"], loading["token"], "PF6_OWNER_SHARED_LOAD_TOKEN: exact token namespaces")
                            self.assertEqual(before, self.formal_snapshot(), marker + " World/revision/identity/ids unchanged")
                            if commit_owner == "builder":
                                self.assertTrue(self.command("load-cancel " + str(loading["token"]))["cancelled"],
                                                "PF6_OWNER_LOAD_CANDIDATE_RETAINED")
                                self.retained_candidate(pending, "confirm", before)
                            else:
                                self.assertTrue(self.command(self.terminal(pending, "cancel"))["cancelled"],
                                                "PF6_OWNER_BUILDER_CANDIDATE_RETAINED")
                                self.assertEqual(before, self.formal_snapshot(), "PF6_OWNER_BUILDER_CANCEL_ZERO_WRITE")
                                done = self.command("load-confirm " + str(loading["token"]))
                                self.assertTrue(done["ok"], "PF6_OWNER_LOAD_STILL_CONFIRMABLE: " + str(done))
                                self.assertEqual(before["revision"] + 1, done["revision"], "PF6_OWNER_LOAD_ONE_REVISION")
                                self.assertIn("spec owner_import 777", self.command("dump")["text"])
                                self.commit_line("undo")
                                self.assertEqual(self.history_current, self.command("dump")["text"], "PF6_OWNER_LOAD_ONE_UNDO")
                                self.commit_line("undo")
                                self.assertEqual(self.history_previous, self.command("dump")["text"], "PF6_OWNER_LOAD_NO_HIDDEN_HISTORY")

    def test_load_shared_serial_survives_reset(self):
        pending = self.pending("pf6")
        before = self.formal_snapshot()
        loading = self.simultaneous_load(pending, before)
        self.assertGreater(loading["token"], pending["token"], "PF6_OWNER_SHARED_LOAD_TOKEN: newer than active builder")
        self.assertTrue(self.command("load-cancel " + str(loading["token"]))["cancelled"])
        self.assertTrue(self.command(self.terminal(pending, "cancel"))["cancelled"])
        self.assertTrue(self.command("reset")["ok"])
        path = self.directory / "after-reset.scene"
        path.write_text("spec after_reset 17\n", encoding="utf-8", newline="\n")
        next_load = self.command("load-prepare " + str(path))
        self.assertTrue(next_load["ok"])
        self.assertGreater(next_load["token"], loading["token"], "PF6_OWNER_LOAD_RESET_NEVER_REUSES_TOKEN")
        self.assertTrue(self.command("load-cancel " + str(next_load["token"]))["cancelled"])

    def test_load_shared_serial_refuses_uint32_exhaustion(self):
        # An actual C include probe reaches UINT32_MAX without billions of CLI
        # calls. It invokes the production prepare function and checks the
        # pre-existing builder candidate, full World and serial remain intact.
        from tests import _bridge
        root = Path(__file__).resolve().parents[1]
        path = self.directory / "capacity-input.scene"
        path.write_text("spec capacity_input 17\n", encoding="utf-8", newline="\n")
        source = self.directory / "load-capacity.c"
        source.write_text(r'''#define GEOMETRY_BRIDGE_ENTRYPOINT original_bridge_main
#include "geometry-web/web_bridge.c"
int main(int argc,char **argv){
    if(argc!=2)return 2;
    if(!app_replace_world(&g_world,false))return 3;
    World *before=malloc(sizeof *before);if(!before)return 4;*before=g_world;
    cmd_line("preview spec retained_builder 9");
    if(!g_preview.ready||!g_preview.valid||!scene_load_prepare(argv[1]))return 5;
    ReferencePreview *prior=malloc(sizeof *prior);if(!prior)return 6;*prior=g_preview;
    AppWorldCandidate *load=g_load_transaction;uint32_t load_token=g_load_token;
    g_preview_serial=UINT32_MAX;
    bool accepted=scene_load_prepare(argv[1]);
    bool exact=!accepted&&g_preview_serial==UINT32_MAX&&!memcmp(prior,&g_preview,sizeof *prior)&&
        g_load_ready&&g_load_token==load_token&&g_load_transaction==load&&!memcmp(before,&g_world,sizeof *before);
    free(prior);free(before);
    printf("{\"capacity_zero_write\":%s}\n",exact?"true":"false");
    return 0;
}
''', encoding="utf-8", newline="\n")
        binaries = _bridge.binaries
        original = binaries.BY_NAME["bridge"]
        probe = binaries.Binary("pf6-load-capacity", "pf6-load-capacity", str(source),
                                original.win_flags, original.win_link, original.posix_flags, [], include=".")
        previous_output = binaries.OUT_DIR
        try:
            binaries.OUT_DIR = self.directory
            executable = probe.path
            status, output, missing = binaries._compile(probe, source)
        finally:
            binaries.OUT_DIR = previous_output
        self.assertFalse(missing, "PF6_OWNER_CAPACITY_PROBE_COMPILER_AVAILABLE: " + output)
        self.assertEqual(0, status, "PF6_OWNER_CAPACITY_PROBE_COMPILES: " + output)
        checked = subprocess.run([str(executable), str(path)], capture_output=True, text=True, timeout=30)
        self.assertEqual(0, checked.returncode, "PF6_OWNER_CAPACITY_PROBE_EXECUTES: " + checked.stderr)
        self.assertTrue(json.loads(checked.stdout.splitlines()[-1])["capacity_zero_write"],
                        "PF6_OWNER_LOAD_COUNTER_CAPACITY / PF6_OWNER_LOAD_CAPACITY_RETAINS_CANDIDATE: UINT32 capacity retains both live candidates without wrap or write")

    def test_reference_stage_shared_serial_refuses_uint32_exhaustion(self):
        from tests import _bridge
        path = self.directory / "reference-capacity.scene"
        path.write_text("spec retained_import 17\n", encoding="utf-8", newline="\n")
        source = self.directory / "reference-capacity.c"
        source.write_text(r'''#define GEOMETRY_BRIDGE_ENTRYPOINT original_bridge_main
#include "geometry-web/web_bridge.c"
int main(int argc,char **argv){
    if(argc!=2||!app_replace_world(&g_world,false)||!scene_load_prepare(argv[1]))return 2;
    cmd_line("preview spec retained_builder 9");
    if(!g_preview.ready||!g_preview.valid)return 3;
    World *before=malloc(sizeof *before);ReferencePreview *prior=malloc(sizeof *prior);
    if(!before||!prior)return 4;*before=g_world;*prior=g_preview;
    uint32_t load=g_load_token;uint64_t revision=g_definition_revision;
    g_preview_serial=UINT32_MAX;
    cmd_line("preview spec wrapped_preview 7");
    bool first=g_preview_serial==UINT32_MAX&&!memcmp(prior,&g_preview,sizeof *prior);
    cmd_line("preview spec wrapped_preview 8");
    bool second=g_preview_serial==UINT32_MAX&&!memcmp(prior,&g_preview,sizeof *prior);
    bool exact=first&&second&&g_load_ready&&g_load_token==load&&
        g_definition_revision==revision&&!memcmp(before,&g_world,sizeof *before);
    char token[32];snprintf(token,sizeof token,"%u",load);cmd_load_confirm(token);
    bool retained=!g_load_ready&&g_definition_revision==revision+1;
    cmd_line("undo");
    bool history=!memcmp(before,&g_world,sizeof *before);
    free(prior);free(before);
    printf("{\"reference_capacity_zero_write\":%s,\"load_retained\":%s,\"history_retained\":%s}\n",
        exact?"true":"false",retained?"true":"false",history?"true":"false");
    return 0;
}
''', encoding="utf-8", newline="\n")
        executable = self.compile_capacity_probe(source, "reference-capacity")
        checked = subprocess.run([str(executable), str(path)], capture_output=True, text=True, timeout=30)
        self.assertEqual(0, checked.returncode, "PF6_OWNER_CAPACITY_PROBE_EXECUTES: " + checked.stderr)
        rows = [json.loads(line) for line in checked.stdout.splitlines()]
        for row in rows[1:3]:
            self.assertIs(row["ok"], False, "PF6_OWNER_PREVIEW_COUNTER_CAPACITY: real line preview refuses exhaustion")
            self.assertIn("token capacity", row["error"], "PF6_OWNER_PREVIEW_COUNTER_CAPACITY: explicit native capacity reason")
        self.assertEqual({"reference_capacity_zero_write": True, "load_retained": True, "history_retained": True},
                         rows[-1], "PF6_OWNER_PREVIEW_COUNTER_CAPACITY: no wrap, candidate replacement, World or history write")

    def compile_capacity_probe(self, source, name):
        from tests import _bridge
        binaries = _bridge.binaries
        original = binaries.BY_NAME["bridge"]
        probe = binaries.Binary(name, name, str(source), original.win_flags,
                                original.win_link, original.posix_flags, [], include=".")
        previous_output = binaries.OUT_DIR
        try:
            binaries.OUT_DIR = self.directory
            executable = probe.path
            status, output, missing = binaries._compile(probe, source)
        finally:
            binaries.OUT_DIR = previous_output
        self.assertFalse(missing, "PF6_OWNER_CAPACITY_PROBE_COMPILER_AVAILABLE: " + output)
        self.assertEqual(0, status, "PF6_OWNER_CAPACITY_PROBE_COMPILES: " + output)
        return executable

    def test_builder_capacity_reports_refusal_without_aliasing_live_load(self):
        # Instrument only stdin to place the production allocator at its finite
        # boundary; all previews, validation, replies and final commits still
        # execute the unmodified real command dispatcher.
        from tests import _bridge
        source = self.directory / "capacity-bridge.c"
        source.write_text(r'''#include <stdio.h>
static char *capacity_fgets(char *text,int size,FILE *stream);
#define fgets capacity_fgets
#define GEOMETRY_BRIDGE_ENTRYPOINT original_bridge_main
#include "geometry-web/web_bridge.c"
#undef fgets
static char *capacity_fgets(char *text,int size,FILE *stream){
    for(;;){char *result=fgets(text,size,stream);
        if(!result||stream!=stdin||strcmp(text,"test-token-capacity\n"))return result;
        g_preview_serial=UINT32_MAX;
        fputs("{\"ok\":true}\n",stdout);fflush(stdout);
    }
}
int main(void){return original_bridge_main();}
''', encoding="utf-8", newline="\n")
        executable = self.compile_capacity_probe(source, "capacity-bridge")
        for owner in ("pf6", "framing-template", "engineering"):
            with self.subTest(owner=owner):
                self.bridge.stop()
                self.bridge = _bridge.BridgeSession(str(executable), cwd=self.directory)
                self.addCleanup(self.bridge.stop)
                pending = self.pending(owner)
                request = self.directory / ("pf6.json" if owner == "pf6" else "owner-request.json")
                command = ("pf6-select" if owner == "pf6" else owner + "-preview") + " " + str(request)
                self.assertTrue(self.command(self.terminal(pending, "cancel"))["cancelled"])
                before = self.formal_snapshot()
                path = self.directory / "capacity-live-load.scene"
                path.write_text(before["dump"] + "spec capacity_load 17\n", encoding="utf-8", newline="\n")
                loading = self.command("load-prepare " + str(path))
                self.assertTrue(loading["ok"])
                self.assertTrue(self.command("test-token-capacity")["ok"])
                for unused in range(2):
                    refused = self.command(command)
                    self.assertIs(refused.get("ok"), False,
                                  "PF6_OWNER_PREVIEW_COUNTER_CAPACITY: " + owner + " refuses exhausted shared serial")
                    self.assertEqual("CAPACITY", refused.get("code"), "PF6_OWNER_PREVIEW_COUNTER_CAPACITY: exact capacity code")
                    self.assertEqual(before, self.formal_snapshot(), "PF6_OWNER_PREVIEW_COUNTER_CAPACITY: zero formal write")
                done = self.command("load-confirm " + str(loading["token"]))
                self.assertTrue(done["ok"], "PF6_OWNER_PREVIEW_COUNTER_CAPACITY: existing load still confirms")
                self.assertEqual(before["revision"] + 1, done["revision"])
                self.commit_line("undo")
                self.assertEqual(self.history_current, self.command("dump")["text"])
                self.commit_line("undo")
                self.assertEqual(self.history_previous, self.command("dump")["text"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
