"""Native candidate facts for R365 adoption; no frontend fingerprint evaluator."""
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests import _bridge


def card(text="3200"):
    return {"op":"put-parameter","value":{"id":2,"name":"adoption dimensions","fields":[
        {"id":0,"name":"width","type":"dimension","input":text},
        {"id":1,"name":"half","type":"dimension","input":"=@2:0/2"}]}}


class EvidenceAdoptionNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.bridge=_bridge.find_bridge()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="r365-adoption-native-");self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name);self.session=_bridge.BridgeSession(self.bridge,cwd=self.directory)
        self.addCleanup(self.session.stop)
        self.assertTrue(self.command("reset")["ok"])
        self.assertTrue(self.command("identity-epoch 0123456789abcdef0123456789abcdef")["ok"])
        initial=self.preview("3200")
        self.assertTrue(self.command("engineering-confirm "+str(initial["token"]))["ok"])
        self.assertTrue(self.command("line identity-ledger activate")["ok"])

    def command(self,text):return self.session.command(text)
    def dump(self):return self.command("dump")["text"]
    def preview(self,text):
        read=self.command("engineering-read");self.assertTrue(read["ok"])
        request={"schema":"engineering-transaction/1","expectedRevision":read["revision"],"operations":[card(text)]}
        path=self.directory/"request.json";path.write_text(json.dumps(request),encoding="utf-8")
        result=self.command("engineering-preview "+str(path));self.assertTrue(result["ok"],result)
        return result["preview"]
    def candidate(self,p):
        result=self.command("engineering-preview-source "+str(p["token"]))
        self.assertTrue(result["ok"],"R365_NATIVE_CANDIDATE_READ: "+str(result))
        self.assertFalse(result["live"]);self.assertTrue(result["complete"])
        return result
    @staticmethod
    def field(graph):return next(n for n in graph["nodes"] if n["key"]=="parameter-field:2:f0")

    def test_candidate_read_is_readonly_and_pins_equal_the_exact_confirmed_candidate(self):
        before=self.dump();live=self.command("source-inspect");ledger=self.command("identity-read")
        p=self.preview("3235");self.assertTrue(p["valid"])
        candidate=self.candidate(p)
        self.assertEqual(before,self.dump(),"R365_PREVIEW_DOES_NOT_PUBLISH")
        self.assertEqual(ledger,self.command("identity-read"),"R365_PREVIEW_DOES_NOT_ISSUE_MARKS")
        self.assertEqual(self.field(live)["incarnation"],self.field(candidate)["incarnation"])
        self.assertNotEqual(self.field(live)["definitionFingerprint"],self.field(candidate)["definitionFingerprint"],"R365_CANDIDATE_PINS_ARE_AFTER")
        receipt=self.command("engineering-confirm "+str(p["token"]));self.assertTrue(receipt["ok"],receipt)
        after=self.command("source-inspect")
        self.assertEqual(receipt["definition_sha256"],candidate["sourceFingerprint"],"R365_CANDIDATE_CONFIRM_HASH")
        self.assertEqual(self.field(after),self.field(candidate),"R365_CANDIDATE_CONFIRM_PINS")
        values=self.command("engineering-read")["state"]["parameters"][0]["fields"]
        self.assertEqual({"num":"3235","den":"1","unit":"mm"},values[0]["value"])
        self.assertEqual({"num":"3235","den":"2","unit":"mm"},values[1]["value"])
        self.assertTrue(self.command("line undo")["ok"])
        self.assertEqual(before,self.dump(),"R365_ONE_NATIVE_UNDO_RESTORES_PARAMETER")

    def test_wrong_token_does_not_consume_the_valid_candidate(self):
        p=self.preview("3235");before=self.dump()
        bad=self.command("engineering-preview-source "+str(p["token"]+1))
        self.assertFalse(bad["ok"],"R365_CANDIDATE_TOKEN_REQUIRED")
        self.assertEqual(before,self.dump());self.candidate(p)
        self.assertTrue(self.command("engineering-confirm "+str(p["token"]))["ok"])

    def test_changed_source_cannot_be_inspected_or_confirmed_as_the_old_candidate(self):
        p=self.preview("3235");self.assertTrue(self.command("line boundary 3 outline 0,0 20,0 20,20 0,20")["ok"])
        before=self.dump()
        self.assertFalse(self.command("engineering-preview-source "+str(p["token"]))["ok"],"R365_CANDIDATE_STALE_REQUIRED")
        self.assertFalse(self.command("engineering-confirm "+str(p["token"]))["ok"])
        self.assertEqual(before,self.dump())

    def test_cancelled_preview_has_no_candidate_facts(self):
        before=self.dump();p=self.preview("3235");self.candidate(p)
        self.assertTrue(self.command("engineering-cancel "+str(p["token"]))["ok"])
        self.assertFalse(self.command("engineering-preview-source "+str(p["token"]))["ok"],"R365_CANCEL_REMOVES_CANDIDATE")
        self.assertEqual(before,self.dump())

    def test_exact_fraction_is_preserved_and_integer_consumer_blocks_confirmation(self):
        p=self.preview("10/3");self.assertTrue(p["valid"]);self.candidate(p)
        field=p["after"]["parameters"][0]["fields"][0]
        self.assertEqual({"num":"10","den":"3","unit":"mm"},field["value"],"R365_NATIVE_EXACT_FRACTION")
        self.assertTrue(self.command("engineering-cancel "+str(p["token"]))["ok"])
        datum=self.command("line preview datum 1 x param:2:0")
        self.assertTrue(datum["preview"]["valid"],datum)
        self.assertTrue(self.command("line confirm "+str(datum["preview"]["token"]))["ok"])
        before=self.dump();p=self.preview("10/3");self.assertFalse(p["valid"])
        self.assertFalse(self.command("engineering-preview-source "+str(p["token"]))["ok"],"R365_INVALID_HAS_NO_ADOPTABLE_PINS")
        self.assertFalse(self.command("engineering-confirm "+str(p["token"]))["ok"])
        self.assertEqual(before,self.dump())

    def test_reading_noop_candidate_preserves_history_and_token(self):
        before=self.dump();p=self.preview("3200");candidate=self.candidate(p)
        receipt=self.command("engineering-confirm "+str(p["token"]));self.assertTrue(receipt["ok"],receipt)
        self.assertFalse(receipt["history_changed"],"R365_READ_DOES_NOT_FORCE_NATIVE_HISTORY")
        self.assertEqual(candidate["sourceFingerprint"],receipt["definition_sha256"])
        self.assertEqual(before,self.dump())

    def test_real_native_app_history_and_zip_cold_reopen(self):
        result=subprocess.run(["node",str(ROOT/"tests/fixtures/evidence_adoption_native_host.cjs"),str(self.bridge),str(self.directory)],cwd=ROOT,
                              text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
        self.assertEqual(result.returncode,0,"R365_REAL_ADOPTION_CHAIN: "+result.stdout)
        receipt=json.loads(result.stdout.strip().splitlines()[-1])
        self.assertTrue(receipt["native"]);self.assertTrue(receipt["zipColdReopen"])
        self.assertEqual(receipt["historyDelta"],1)
        print(json.dumps({"R365_REAL_ADOPTION_CHAIN":receipt},sort_keys=True))


if __name__=="__main__":unittest.main()
