"""Optional ordinal dependency hints: exact graph, failure order and work.

These controls supplement unchanged source-index/node-slot/node-hint/scope
suites. Real callbacks exercise nested consumers; allocator failures use the
existing private source-index harness. No wall-time threshold is introduced.
"""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests.test_geo261_native_kernel import NativeBuild
from tests.test_geo300_source_node_hint import instrument_hint_work

HIT="    if(index&&index<=ctx->node_count&&geo_source_ref_equal(ctx->nodes[index-1]->source,source))"


class DependHint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build=NativeBuild(kernel_only=True)
        cls.original=(cls.build.kernel/"source.c").read_text(encoding="utf-8")
        cls.exe=cls.make_executable("baseline",cls.original)

    @classmethod
    def make_executable(cls,label,source):
        work=cls.build.work/("depend-hint-source-"+label);work.mkdir()
        (work/"source.c").write_text(instrument_hint_work(source),encoding="utf-8")
        shutil.copy2(ROOT/"tests/geo261_source_index_harness.c",work/"geo261_source_index_harness.c")
        client=work/"client.c";shutil.copy2(ROOT/"tests/geo300_depend_hint_harness.c",client)
        return cls.build.link("depend-hint-"+label,[cls.build.compile(client,"depend-hint-"+label)])

    def case(self,name,exe=None,phase="positive"):
        command=[str(exe or self.exe),name]
        result=subprocess.run(command,capture_output=True,text=True,timeout=30)
        log=os.environ.get("GEO300_DEPEND_HINT_LOG")
        if log:
            with open(log,"a",encoding="utf-8") as stream:
                stream.write(json.dumps({"command":command,"source_sha":os.environ.get("GITHUB_SHA"),
                    "phase":phase,"exit":result.returncode,"stdout":result.stdout,"stderr":result.stderr},ensure_ascii=False)+"\n")
        self.assertIn(result.returncode,(0,1),"Crash/setup failure is not a named assertion: "+result.stderr)
        return result

    def passes(self,name,phase="positive"):
        r=self.case(name,phase=phase)
        self.assertEqual((0,"PASS "+name+"\n",""),(r.returncode,r.stdout,r.stderr))

    def test_complete_identity_same_address_bytes_and_out_of_range_ordinals(self):
        self.passes("identity")

    def test_reset_and_another_context_do_not_trust_the_old_ordinal(self):
        self.passes("reset-context")

    def test_original_error_order_no_evaluation_and_sealed_guard(self):
        self.passes("status-order")

    def test_null_hint_keeps_the_original_api_status_and_order(self):
        self.passes("null-hint")

    def test_real_nested_callbacks_keep_all_kinds_consumers_and_cycles(self):
        self.passes("edge-scopes")

    def test_valid_hint_is_not_a_proof_of_an_existing_edge(self):
        self.passes("edge-wiring")

    def test_512_warmed_hints_skip_hash_lookup_without_allocating(self):
        self.passes("hit-work")

    def test_required_node_key_array_and_edge_failures_preserve_retry(self):
        self.passes("allocation-failure")

    def test_optional_index_failure_keeps_the_exact_graph_and_reset(self):
        self.passes("optional-fallback")

    def test_same_identity_in_another_context_uses_its_own_value(self):
        self.passes("context-values")

    def test_full_hash_collision_does_not_replace_source_identity(self):
        self.passes("full-collision")

    def kill(self,label,anchor,replacement,case,marker):
        self.assertEqual(1,self.original.count(anchor),"withdrawal anchor must be unique")
        exe=self.make_executable(label,self.original.replace(anchor,replacement))
        self.passes(case,phase="baseline")
        r=self.case(case,exe,phase="mutant")
        self.assertEqual((1,""),(r.returncode,r.stdout),r.stdout+r.stderr)
        self.assertRegex(r.stderr,r"^ASSERT:"+re.escape(marker)+r" line=\d+ expr=[^\n]+\n$")
        print("withdrawal",label,"exit",r.returncode,r.stderr.strip(),flush=True)
        self.passes(case,phase="restored")

    def test_withdrawn_full_identity_guard_fails_named_identity(self):
        self.kill("no-identity",HIT,"    if(index&&index<=ctx->node_count)",
                  "identity","depend-hint-full-identity")

    def test_withdrawn_edge_wiring_fails_named_current_consumer(self):
        self.kill("no-edge",HIT+"\n        return geo_source_edge(ctx,index-1,kind);",
                  HIT+"\n        return GEO_SOURCE_OK;","edge-wiring","depend-hint-current-consumer-edge")

    def test_withdrawn_fast_path_fails_named_actual_hash_lookup_work(self):
        self.kill("no-fast-path",HIT,HIT.replace("if(index", "if(false&&index"),
                  "hit-work","depend-hint-hit-avoids-hash-and-lookup")

    def test_withdrawn_sealed_guard_fails_named_immutability(self):
        self.kill("no-sealed-guard",
                  "    if(!ctx||ctx->sealed||(source.key_size&&!source.key))return GEO_SOURCE_INVALID;",
                  "    if(!ctx||(source.key_size&&!source.key))return GEO_SOURCE_INVALID;",
                  "status-order","depend-hint-sealed-guard")


if __name__=="__main__":unittest.main(verbosity=2)
