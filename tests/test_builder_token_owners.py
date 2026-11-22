"""PF-6/#438 integration: real native terminal commands retain foreign candidates.

These are CLI/native tests, not browser evidence. Existing PF-6 and framing
fixtures remain independently owned. No counts, golden values or timeouts are
changed. Each rejected operation is followed by the original owner's exact
confirm/cancel and by observable undo/redo checks.
"""
import copy
import json
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
