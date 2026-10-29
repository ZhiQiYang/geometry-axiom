"""Three remaining real H/W dependency sites keep graph semantics without hash.

Original fixtures and their value/consumer/kind/order assertions are reused
unchanged. Each withdrawal restores only one old call; no wall-time threshold.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests.test_geo261_native_kernel import native
from tests.test_geo261_wood_world_validation import copy_product_closure, PRODUCT_DEFINES

REFERENCE="geometry-app/native/reference_sources.inc"
CONTACT="geometry-templates/woodworking/native/contact_sources.c"
DEFINITION_HINT=("geo_eval_depend_hint(ctx->sources,wood_definition_source_ref(APP_SOURCE_WOOD_DEFINITION,WOOD_DEFINITION_MEMBER,id,&key),\n"
                 "            GEO_DEPENDENCY_DEFINITION_REQUIRED,&ctx->member_reads[i].definition_node_hint)")
DEFINITION_OLD=("geo_eval_depend(ctx->sources,wood_definition_source_ref(APP_SOURCE_WOOD_DEFINITION,WOOD_DEFINITION_MEMBER,id,&key),\n"
                "            GEO_DEPENDENCY_DEFINITION_REQUIRED)")
POSE_HINT="geo_eval_depend_hint(ctx->sources,ref,relation,&ctx->member_reads[i].footprint_node_hint)"
POSE_OLD="geo_eval_depend(ctx->sources,ref,relation)"
COLLECTION_HINT="geo_eval_depend_hint(graph,collection_ref,GEO_DEPENDENCY_VALUE_REQUIRED,&collection_hint)"
COLLECTION_OLD="geo_eval_depend(graph,collection_ref,GEO_DEPENDENCY_VALUE_REQUIRED)"
DEFINITION_ENTRY="    if(ctx->member_reads[i].definition_valid&&ctx->member_reads[i].definition.id==id){"
POSE_ENTRY="    if(ctx->member_reads[i].pose_valid&&ctx->member_reads[i].pose_id==id&&!geo_eval_is_sealed(ctx->sources)){"
HASH_ENTRY="static uint64_t geo_source_node_hash(GeoSourceRef source)\n{"


def once(source,before,after):
    if source.count(before)!=1:raise AssertionError("Expected one actual instrumentation/withdrawal anchor: "+before)
    return source.replace(before,after)


class RemainingDependHint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build=native();cls.sequence=0
        source=(cls.build.kernel/"source.c").read_text(encoding="utf-8")
        source=once(source,'#include "source.h"','#include "source.h"\nextern void remaining_hint_observe_hash(GeoSourceRef source);')
        source=once(source,HASH_ENTRY,HASH_ENTRY+"\n    remaining_hint_observe_hash(source);")
        path=cls.build.work/"remaining-hint-kernel.c";path.write_text(source,encoding="utf-8")
        cls.source_object=cls.build.compile(path,"remaining-hint-kernel")
        cls.host=cls.host_variant("baseline")
        shutil.copy2(ROOT/"tests/geo261_contact_sources_harness.c",cls.build.woodworking/"geo261_contact_sources_harness.c")
        client=cls.build.woodworking/"remaining-collection-client.c"
        shutil.copy2(ROOT/"tests/geo300_remaining_collection_hint_harness.c",client)
        cls.collection_client=cls.build.compile(client,"remaining-collection-client")
        cls.collection=cls.collection_variant("baseline")

    @classmethod
    def host_variant(cls,name):
        destination=cls.build.work/("remaining-host-source-"+name)
        harness=copy_product_closure(ROOT/"tests/geo300_remaining_host_hint_harness.c",destination)
        legacy=destination/"tests/geo261_load_residual_harness.c"
        source=once(legacy.read_text(encoding="utf-8"),"int main(int argc,char **argv)","int remaining_original_main(int argc,char **argv)")
        legacy.write_text(source,encoding="utf-8")
        path=destination/REFERENCE;source=path.read_text(encoding="utf-8")
        if name=="withdraw-definition":source=once(source,DEFINITION_HINT,DEFINITION_OLD)
        elif name=="withdraw-pose":source=once(source,POSE_HINT,POSE_OLD)
        elif name!="baseline":raise AssertionError("Unknown H variant "+name)
        source=once(source,DEFINITION_ENTRY,DEFINITION_ENTRY+"\n        if(residual_second_consumer)++remaining_definition_calls;")
        source=once(source,POSE_ENTRY,POSE_ENTRY+"\n        if(residual_second_consumer)++remaining_pose_calls;")
        path.write_text(source,encoding="utf-8")
        obj=cls.build.compile(harness,"remaining-host-"+name,PRODUCT_DEFINES)
        objects=cls.build.product_objects()
        if objects.count(cls.build.source_object)!=1:raise AssertionError("Expected one K source object")
        return cls.build.link("remaining-host-"+name,[obj,*[cls.source_object if x==cls.build.source_object else x for x in objects]])

    @classmethod
    def collection_variant(cls,name):
        source=(ROOT/CONTACT).read_text(encoding="utf-8")
        call=COLLECTION_HINT
        if name=="withdraw-collection":source=once(source,call,COLLECTION_OLD);call=COLLECTION_OLD
        elif name!="baseline":raise AssertionError("Unknown W variant "+name)
        source=once(source,'#include "contact_sources.h"',
                    '#include "contact_sources.h"\nextern void remaining_collection_begin(void);\nextern void remaining_collection_end(void);')
        site="        if("+call+"!=GEO_SOURCE_OK)return false;"
        source=once(source,site,"        remaining_collection_begin();\n"+site+"\n        remaining_collection_end();")
        path=cls.build.woodworking/("remaining-collection-"+name+".c");path.write_text(source,encoding="utf-8")
        provider=cls.build.compile(path,"remaining-collection-provider-"+name)
        b=cls.build
        return b.link("remaining-collection-"+name,[cls.collection_client,provider,b.wood_contact_world_object,
            b.wood_contacts_object,b.wood_supports_object,b.placement_sources_object,b.placements_object,
            b.regions_object,cls.source_object,b.geometry_object])

    def case(self,name,exe,marker=None,phase="positive"):
        command=[str(exe),name];r=subprocess.run(command,capture_output=True,timeout=30)
        if directory:=os.environ.get("GEO300_REMAINING_HINT_LOG"):
            type(self).sequence+=1;folder=Path(directory)/(f"{self.sequence:03d}-"+name+"-"+phase);folder.mkdir(parents=True,exist_ok=False)
            (folder/"stdout.bin").write_bytes(r.stdout);(folder/"stderr.bin").write_bytes(r.stderr)
            paths=(REFERENCE,CONTACT,"geometry-core/references.inc","geometry-core/kernel/source.c",
                   "tests/geo261_load_residual_harness.c","tests/geo261_contact_sources_harness.c",
                   "tests/geo300_remaining_host_hint_harness.c","tests/geo300_remaining_collection_hint_harness.c",
                   "tests/test_geo300_remaining_depend_hint.py")
            (folder/"RESULT.json").write_text(json.dumps({"source_sha":os.environ.get("GITHUB_SHA"),
                "source_hashes":{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
                "command":command,"timeout_seconds":30,"exit":r.returncode,"expected_assertion":marker,
                "binary_sha256":hashlib.sha256(Path(command[0]).read_bytes()).hexdigest(),
                "stdout_sha256":hashlib.sha256(r.stdout).hexdigest(),"stderr_sha256":hashlib.sha256(r.stderr).hexdigest()},indent=2)+"\n")
        self.assertEqual(1 if marker else 0,r.returncode,r.stdout+r.stderr)
        lines=r.stdout.decode().splitlines()
        if name=="collection-reset":
            self.assertEqual((["PASS collection-reset"],b""),(lines,r.stderr));return
        self.assertEqual(1 if marker else 2,len(lines),r.stdout+r.stderr)
        observed=json.loads(lines[0])
        if name=="collection-cache-edges":expected={"collection_calls":4,"collection_hashes":4 if marker else 0}
        elif name=="cache-definition":expected={"definition_calls":2,"definition_hashes":2 if marker else 0,"pose_calls":0,"pose_hashes":0}
        else:expected={"definition_calls":0,"definition_hashes":0,"pose_calls":2,"pose_hashes":2 if marker else 0}
        self.assertEqual(expected,observed)
        if marker:
            tail=r"\n$" if name=="collection-cache-edges" else r" line=\d+ expr=[^\n]+\n$"
            self.assertRegex(r.stderr.decode(),r"^ASSERT:"+re.escape(marker)+tail)
        else:self.assertEqual(("PASS "+name,b""),(lines[-1],r.stderr))

    def test_real_definition_consumers_preserve_original_graph_and_value(self):self.case("cache-definition",self.host)
    def test_real_pose_consumers_keep_different_requested_kinds(self):self.case("cache-pose-kind",self.host)
    def test_four_real_features_keep_exact_collection_identity_and_nine_edges(self):self.case("collection-cache-edges",self.collection)
    def test_collection_reset_keeps_mismatched_ordinal_and_new_state_fallbacks(self):self.case("collection-reset",self.host)

    def test_withdraw_definition_hint_named_red_then_restore(self):
        self.case("cache-definition",self.host,phase="baseline")
        self.case("cache-definition",self.host_variant("withdraw-definition"),"remaining-definition-hint-skips-node-hash","mutant")
        self.case("cache-definition",self.host,phase="restored")

    def test_withdraw_pose_hint_named_red_then_restore(self):
        self.case("cache-pose-kind",self.host,phase="baseline")
        self.case("cache-pose-kind",self.host_variant("withdraw-pose"),"remaining-pose-hint-skips-node-hash","mutant")
        self.case("cache-pose-kind",self.host,phase="restored")

    def test_withdraw_collection_hint_named_red_then_restore(self):
        self.case("collection-cache-edges",self.collection,phase="baseline")
        self.case("collection-cache-edges",self.collection_variant("withdraw-collection"),"remaining-collection-hint-skips-node-hash","mutant")
        self.case("collection-cache-edges",self.collection,phase="restored")


if __name__=="__main__":unittest.main(verbosity=2)
