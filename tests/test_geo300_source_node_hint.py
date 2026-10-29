"""Full identity hint hashing: actual typed keys, exact work, original graph.

This supplements the original source-index/node-slot/scope suites unchanged.
No elapsed-time assertion or extra cache capacity is introduced.
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
from tests.test_geo300_source_node_slot import instrument_node_work

HINT_SLOT="    size_t slot=(size_t)hash&255;"
OLD_SLOT="""    size_t slot=(size_t)source.provider^source.key_size;
    if(source.key_size){const unsigned char *key=source.key;slot^=(size_t)key[0]^key[source.key_size-1];}
    slot&=255;"""


def once(source,anchor,replacement):
    if source.count(anchor)!=1:raise AssertionError("node-hint-anchor-not-unique: "+anchor)
    return source.replace(anchor,replacement)


def instrument_hint_work(source):
    source=instrument_node_work(source)
    marker="geo_source_find_node("
    at=source.index("{",source.index(marker))+1
    return source[:at]+"\n    ++node_find_calls;"+source[at:]


class SourceNodeHint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build=NativeBuild(kernel_only=True)
        cls.original=(cls.build.kernel/"source.c").read_text(encoding="utf-8")
        cls.exe=cls.make_executable("baseline",cls.original)
        cls.old_slot=cls.make_executable("old-selector",once(cls.original,HINT_SLOT,OLD_SLOT))

    @classmethod
    def make_executable(cls,label,source):
        work=cls.build.work/("node-hint-source-"+label);work.mkdir()
        (work/"source.c").write_text(instrument_hint_work(source),encoding="utf-8")
        shutil.copy2(ROOT/"tests/geo261_source_index_harness.c",work/"geo261_source_index_harness.c")
        client=work/"client.c";shutil.copy2(ROOT/"tests/geo300_source_node_hint_harness.c",client)
        # The actual K typed-key constructor/decoder is linked, not copied.
        return cls.build.link("node-hint-"+label,[cls.build.compile(client,"node-hint-"+label),
            *[obj for obj in cls.build.kernel_objects() if obj!=cls.build.source_object]])

    def case(self,name,exe=None,phase="positive"):
        command=[str(exe or self.exe),name]
        result=subprocess.run(command,capture_output=True,text=True,timeout=30)
        log=os.environ.get("GEO300_NODE_HINT_LOG")
        if log:
            with open(log,"a",encoding="utf-8") as stream:
                stream.write(json.dumps({"command":command,"source_sha":os.environ.get("GITHUB_SHA"),
                    "phase":phase,"exit":result.returncode,"stdout":result.stdout,"stderr":result.stderr},ensure_ascii=False)+"\n")
        self.assertIn(result.returncode,(0,1),"Crash/setup failure is not a named assertion: "+result.stderr)
        return result

    def passes(self,name,exe=None,phase="positive"):
        r=self.case(name,exe,phase)
        self.assertEqual((0,"PASS "+name+"\n",""),(r.returncode,r.stdout,r.stderr))

    def test_actual_typed_middle_bytes_avoid_the_original_selector_collisions(self):
        observations={}
        for label,exe in (("new",self.exe),("old-selector",self.old_slot)):
            r=self.case("typed-observe",exe,phase=label)
            self.assertEqual(0,r.returncode,r.stdout+r.stderr)
            self.assertEqual("",r.stderr)
            lines=r.stdout.splitlines()
            self.assertEqual("PASS typed-observe",lines[-1])
            observations[label]=json.loads(lines[0])
        new,old=observations["new"],observations["old-selector"]
        self.assertEqual(32,new["requests"])
        self.assertEqual(new["requests"],old["requests"])
        self.assertEqual(32,old["finds"],"fixed same-end typed keys must expose the old selector")
        self.assertGreaterEqual(old["probes"],old["finds"])
        self.assertEqual((0,0,32),(new["finds"],new["probes"],new["hashes"]))

    def test_a_forced_hint_miss_reuses_the_same_hash_in_the_actual_lookup(self):
        self.passes("typed-probe")

    def test_real_typed_hash_collision_keeps_identity_and_invalid_input_precedes_hash(self):
        self.passes("typed-collision")

    def test_optional_index_failure_reset_and_sealed_reads_preserve_state(self):
        self.passes("typed-fallback")

    def assert_killed(self,exe,case,marker):
        self.passes(case,phase="baseline")
        r=self.case(case,exe,phase="mutant")
        self.assertEqual(1,r.returncode,r.stdout+r.stderr)
        self.assertEqual("",r.stdout)
        self.assertRegex(r.stderr,r"^ASSERT:"+re.escape(marker)+r" line=\d+ expr=[^\n]+\n$")
        print("withdrawal",marker,"exit",r.returncode,r.stderr.strip(),flush=True)
        self.passes(case,phase="restored")

    def test_withdrawn_full_key_selector_fails_named_lookup_work(self):
        self.assert_killed(self.old_slot,"typed-hint","node-hint-middle-bytes-avoid-full-lookup")

    def test_recomputed_lookup_hash_fails_named_single_hash_work(self):
        changed=once(self.original,"slot=(size_t)hash&mask;","slot=(size_t)geo_source_node_hash(source)&mask;")
        exe=self.make_executable("recomputed-hash",changed)
        self.assert_killed(exe,"typed-probe","node-hint-miss-hash-reused-once")

    def test_ignored_hint_identity_fails_named_typed_collision(self):
        changed=once(self.original,
            "if(hint&&hint<=ctx->node_count&&geo_source_ref_equal(ctx->nodes[hint-1]->source,source)){",
            "if(hint&&hint<=ctx->node_count){")
        exe=self.make_executable("identity-ignored",changed)
        self.assert_killed(exe,"typed-collision","node-hint-collision-retains-full-identity")


if __name__=="__main__":unittest.main(verbosity=2)
