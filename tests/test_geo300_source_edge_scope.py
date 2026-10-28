"""Fresh consumer scope: original graph oracle, role failures, named withdrawals.

Private candidate draft. Supplements the original source-index suite unchanged.
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
from tests.test_geo261_source_index import instrument_edge_work


def instrument_scope_work(source):
    source=instrument_edge_work(source)
    replacements=(
        ("grown=malloc(next*sizeof *grown);",
         "grown=scope_undo_fail?(++scope_undo_failures,NULL):malloc(next*sizeof *grown);"),
        ("}else grown=realloc(scope->undo,next*sizeof *grown);",
         "}else grown=scope_undo_fail?(++scope_undo_failures,NULL):realloc(scope->undo,next*sizeof *grown);"),
    )
    for anchor,replacement in replacements:
        if source.count(anchor)!=1:raise AssertionError("scope-role-injection-anchor: "+anchor)
        source=source.replace(anchor,replacement)
    return source


class SourceEdgeScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build=NativeBuild(kernel_only=True)
        cls.original=(cls.build.kernel/"source.c").read_text(encoding="utf-8")
        cls.exe=cls.make_executable("baseline",cls.original)

    @classmethod
    def make_executable(cls,label,source):
        work=cls.build.work/("edge-scope-source-"+label);work.mkdir()
        (work/"source.c").write_text(instrument_scope_work(source),encoding="utf-8")
        shutil.copy2(ROOT/"tests/geo261_source_index_harness.c",work/"geo261_source_index_harness.c")
        harness=work/"client.c";shutil.copy2(ROOT/"tests/geo300_source_edge_scope_harness.c",harness)
        return cls.build.link("edge-scope-"+label,[cls.build.compile(harness,"edge-scope-"+label)])

    def case(self,name,exe=None):
        command=[str(exe or self.exe),name]
        result=subprocess.run(command,capture_output=True,text=True,timeout=30)
        log=os.environ.get("GEO300_EDGE_SCOPE_LOG")
        if log:
            with open(log,"a",encoding="utf-8") as stream:
                stream.write(json.dumps({"command":command,"source_sha":os.environ.get("GITHUB_SHA"),
                    "exit":result.returncode,"stdout":result.stdout,"stderr":result.stderr},ensure_ascii=False)+"\n")
        self.assertIn(result.returncode,(0,1),"Crash is not a named assertion: "+result.stderr)
        return result

    def passes(self,name):
        result=self.case(name)
        self.assertEqual(0,result.returncode,result.stdout+result.stderr)
        self.assertEqual("PASS "+name+"\n",result.stdout)
        self.assertEqual("",result.stderr)

    def test_fresh_one_edge_and_fanout_keep_order_without_hash_work(self):
        self.passes("scope-work")

    def test_nested_parent_marks_and_manual_ancestor_write_remain_sound(self):
        self.passes("scope-nested")

    def test_retry_failure_preserves_previous_edges_and_output(self):
        self.passes("scope-retry")

    def test_optional_undo_and_index_allocation_failures_fall_back(self):
        self.passes("scope-optional")

    def test_required_edge_growth_failure_does_not_publish_membership(self):
        self.passes("scope-required")

    def test_dirty_old_index_rebuilds_or_falls_back_to_linear_lookup(self):
        self.passes("scope-dirty")

    def test_describe_effect_cycle_reset_and_seal_keep_original_graph(self):
        self.passes("scope-control")

    def kill(self,label,case,anchor,replacement,expected):
        self.passes(case)
        self.assertEqual(1,self.original.count(anchor),"withdrawal anchor must be unique")
        mutated=self.original.replace(anchor,replacement)
        self.assertNotEqual(self.original,mutated)
        exe=self.make_executable(label,mutated)
        result=self.case(case,exe)
        self.assertEqual(1,result.returncode,result.stdout+result.stderr)
        self.assertEqual("",result.stdout)
        self.assertRegex(result.stderr,r"^ASSERT:"+re.escape(expected)+r" line=\d+ expr=[^\n]+\n$")
        print("withdrawal",label,"exit",result.returncode,result.stderr.strip(),flush=True)
        self.passes(case)

    def test_disabled_scope_fails_named_work_assertion(self):
        self.kill("disabled","scope-work",
                  "bool scoped=scope&&scope->consumer==ctx->active&&scope->complete;",
                  "bool scoped=false;","scope-fresh-no-edge-hash")

    def test_missing_restore_fails_named_parent_edge_assertion(self):
        self.kill("no-restore","scope-nested",
                  "node->edge_scope=old.previous;node->edge_scope_kinds=old.kinds;",
                  "(void)node;(void)old;","scope-parent-restored-no-duplicate")

    def test_missing_fresh_guard_fails_named_retry_assertion(self):
        self.kill("retry-fresh","scope-retry",
                  "scope->undo=scope->inline_undo;scope->complete=!ctx->nodes[consumer]->outgoing_seen;",
                  "scope->undo=scope->inline_undo;scope->complete=true;","scope-retry-retains-old-edges-once")

    def test_missing_dirty_rebuild_fails_named_general_lookup_assertion(self):
        # V2 discards the stale table immediately, so omitting rebuild alone
        # remains correct through linear lookup. This mutant instead builds
        # an incomplete nonempty index, then restores the authoritative count.
        self.kill("truncated-rebuild","scope-dirty",
                  "if(ctx->edge_count)geo_source_index_append(ctx,false);",
                  "if(ctx->edge_count){size_t saved=ctx->edge_count;ctx->edge_count=1;"
                  "geo_source_index_append(ctx,false);ctx->edge_count=saved;}",
                  "scope-dirty-fallback-preserves-edges")

    def test_retained_stale_table_fails_original_allocation_assertion(self):
        self.kill("retained-stale-table","allocation",
                  "        if(!ctx->edge_index_dirty){\n"
                  "            free(ctx->edge_index);ctx->edge_index=NULL;ctx->edge_index_capacity=0;\n"
                  "        }",
                  "        /* withdrawal: retain the old incomplete optional table */",
                  "index-allocation-was-rejected")

    def test_premature_membership_fails_named_memory_retry_assertion(self):
        anchor="if(ctx->edge_count==SIZE_MAX/sizeof *ctx->edges)return GEO_SOURCE_MEMORY;"
        self.kill("mark-before-grow","scope-required",anchor,
                  "if(scoped)geo_source_scope_record(ctx,scope,source,kind_bit);\n    "+anchor,
                  "scope-required-retry-keeps-edge")


if __name__=="__main__":unittest.main(verbosity=2)
