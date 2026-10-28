"""New-node empty-slot reuse: real K graph, exact work and named withdrawal.

This supplements, never replaces or edits, test_geo261_source_index's controls.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests.test_geo261_native_kernel import NativeBuild
from tests.test_geo261_source_index import instrument_edge_work


def instrument_node_work(source):
    source=instrument_edge_work(source)
    replacements=(
        ("static uint64_t geo_source_node_hash(GeoSourceRef source)\n{",
         "static uint64_t geo_source_node_hash(GeoSourceRef source)\n{\n    ++node_hash_calls;"),
        ("while(ctx->node_index[slot]){","while((++node_probe_steps,ctx->node_index[slot])){"),
        ("while((nodes?0:++edge_probe_steps,(*table)[slot]))slot=(slot+1)&mask;",
         "while((nodes?++node_probe_steps:++edge_probe_steps,(*table)[slot]))slot=(slot+1)&mask;"),
    )
    for anchor,replacement in replacements:
        if source.count(anchor)!=1:raise AssertionError("node-slot-instrumentation-anchor: "+anchor)
        source=source.replace(anchor,replacement)
    return source


class SourceNodeSlot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build=NativeBuild(kernel_only=True)
        cls.original=(cls.build.kernel/"source.c").read_text(encoding="utf-8")
        cls.exe=cls.make_executable("baseline",cls.original)

    @classmethod
    def make_executable(cls,label,source):
        work=cls.build.work/("node-slot-"+label);work.mkdir()
        (work/"source.c").write_text(instrument_node_work(source),encoding="utf-8")
        shutil.copy2(ROOT/"tests/geo261_source_index_harness.c",work/"geo261_source_index_harness.c")
        harness=work/"client.c";shutil.copy2(ROOT/"tests/geo300_source_node_slot_harness.c",harness)
        return cls.build.link("node-slot-"+label,[cls.build.compile(harness,"node-slot-"+label)])

    def case(self,name,exe=None):
        result=subprocess.run([str(exe or self.exe),name],capture_output=True,text=True,timeout=30)
        self.assertIn(result.returncode,(0,1),"Crash is not a named assertion: "+result.stderr)
        return result

    def passes(self,name):
        r=self.case(name)
        self.assertEqual(0,r.returncode,r.stdout+r.stderr)
        self.assertEqual("PASS "+name+"\n",r.stdout)
        self.assertEqual("",r.stderr)

    def test_node_miss_hashes_and_probes_once_with_exact_ordered_values(self):
        self.passes("node-slot-work")

    def test_growth_rebuilds_all_old_ordinals_and_preserves_lookup(self):
        self.passes("node-slot-growth")

    def test_required_failure_optional_fallback_retry_and_reset(self):
        self.passes("node-slot-failure")

    def test_original_uint32_guard_precedes_new_fast_slot(self):
        self.passes("node-slot-packed")

    def kill(self,label,anchor,replacement,expected):
        self.passes("node-slot-work")
        self.assertEqual(1,self.original.count(anchor),"withdrawal anchor must be unique")
        mutated=self.original.replace(anchor,replacement)
        exe=self.make_executable(label,mutated)
        r=self.case("node-slot-work",exe)
        self.assertEqual(1,r.returncode,r.stdout+r.stderr)
        self.assertEqual("",r.stdout)
        self.assertRegex(r.stderr,r"^ASSERT:"+re.escape(expected)+r" line=\d+ expr=[^\n]+\n$")
        print("withdrawal",label,"exit",r.returncode,r.stderr.strip(),flush=True)
        self.passes("node-slot-work")

    def test_withdrawn_slot_reuse_fails_named_hash_work(self):
        self.kill("removed","else if(empty_slot!=SIZE_MAX&&empty_slot<*capacity){",
                  "else if(false&&empty_slot!=SIZE_MAX&&empty_slot<*capacity){","node-miss-one-hash")

    def test_wrong_written_ordinal_fails_named_identity(self):
        self.kill("wrong-ordinal","(*table)[empty_slot]=(uint32_t)count;return;",
                  "(*table)[empty_slot]=(uint32_t)(count-1);return;",
                  "node-miss-committed-slot-points-to-new-ordinal")


if __name__=="__main__":unittest.main(verbosity=2)
