"""來源圖索引的順序、碰撞、配置降級，以及必須命名病因的突變自證。"""
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests.test_geo261_native_kernel import NativeBuild

# 突變的錨點：都是 source.c 裡單行、唯一的片段，所以行尾是 LF 或 CRLF 都不影響；
# 錨點不唯一或不存在時 inject() 直接失敗，不會悄悄產生一個沒改動的「突變」。
NODE_PROBE = "while(ctx->node_index[slot]){"
EDGE_PROBE = "while(ctx->edge_index[slot]){"


EDGE_PROBE_REUSE_EDITS = [('static bool geo_source_find_edge(const GeoEvalContext *ctx,GeoSourceEdge edge)', 'static bool geo_source_find_edge(const GeoEvalContext *ctx,GeoSourceEdge edge,size_t *empty_slot)'), ('            slot=(slot+1)&mask;\n        }\n    }else for(size_t i=0;i<ctx->edge_count;++i)', '            slot=(slot+1)&mask;\n        }\n        *empty_slot=slot;\n    }else for(size_t i=0;i<ctx->edge_count;++i)'), ('static void geo_source_index_append(GeoEvalContext *ctx,bool nodes)', 'static void geo_source_index_append(GeoEvalContext *ctx,bool nodes,size_t empty_slot)'), ('free(*table);*table=fresh;*capacity=next;first=0;', 'free(*table);*table=fresh;*capacity=next;first=0;empty_slot=SIZE_MAX;'), ('    for(size_t i=first;i<count;++i){\n        uint64_t hash=nodes?geo_source_node_hash', '    /* A missing edge already probed this unchanged index to an empty slot.\n     * Rebuilding discards that slot; allocation fallback stays linear. */\n    if(empty_slot<*capacity&&!(*table)[empty_slot]){(*table)[empty_slot]=count;return;}\n    for(size_t i=first;i<count;++i){\n        uint64_t hash=nodes?geo_source_node_hash'), ('geo_source_index_append(ctx,true);ctx->node_hint[slot]=*index+1;', 'geo_source_index_append(ctx,true,SIZE_MAX);ctx->node_hint[slot]=*index+1;'), ('    if(geo_source_find_edge(ctx,edge))return GEO_SOURCE_OK;', '    size_t empty_slot=SIZE_MAX;\n    if(geo_source_find_edge(ctx,edge,&empty_slot))return GEO_SOURCE_OK;'), ('geo_source_index_append(ctx,false);return GEO_SOURCE_OK;', 'geo_source_index_append(ctx,false,empty_slot);return GEO_SOURCE_OK;')]


class SourceIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = NativeBuild(kernel_only=True)
        cls.harness = cls.build.work / "source-index-client.c"
        shutil.copy2(ROOT / "tests/geo261_source_index_harness.c", cls.harness)
        cls.exe = cls.build.link("source-index-client", [cls.build.compile(cls.harness, "source-index-client")])

    def case(self, name, exe=None):
        result = subprocess.run([str(exe or self.exe), name], capture_output=True,
                                text=True, timeout=30)
        self.assertIn(result.returncode, (0, 1), "原生崩潰或啟動失敗不是有效斷言：" + result.stderr)
        return result

    def passes(self, name):
        result = self.case(name)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("PASS " + name + "\n", result.stdout)

    def test_many_binary_keys_collisions_identity_order_and_sealed_lookup(self):
        self.passes("nodes")

    def test_each_edge_field_deduplicates_in_linear_order_and_reset_rebuilds(self):
        self.passes("edges")

    def test_forced_edge_collisions_deduplicate_each_field_in_linear_order(self):
        self.passes("edge-collisions")

    def test_allocation_failure_falls_back_without_changing_existing_state(self):
        self.passes("allocation")

    def test_array_growth_retries_exact_size_and_preserves_state_on_memory(self):
        self.passes("growth")

    def test_missing_invalid_failed_cycle_and_output_statuses(self):
        self.passes("statuses")

    def source(self):
        return (self.build.kernel / "source.c").read_text(encoding="utf-8")

    def inject(self, anchor, replacement):
        source = self.source()
        self.assertEqual(1, source.count(anchor), "突變錨點必須在 source.c 恰好出現一次：" + anchor)
        return source.replace(anchor, replacement)

    def kill(self, name, case, label, mutated):
        """基準先過、再編突變；突變必須以名為 label 的正常斷言失敗，之後基準仍過。
        編譯錯誤會讓 build 拋例外，崩潰、逾時由 case() 擋下，三者都不算偵測成功。"""
        self.passes(case)
        self.assertNotEqual(self.source(), mutated, "突變必須真的改到 source.c")
        work = self.build.work / ("mutant-source-" + name)
        work.mkdir()
        (work / "source.c").write_text(mutated, encoding="utf-8")
        client = work / "client.c"
        shutil.copy2(self.harness, client)
        exe_name = "source-index-" + name
        exe = self.build.link(exe_name, [self.build.compile(client, exe_name)])
        result = self.case(case, exe)
        self.assertEqual(1, result.returncode, "突變必須由正常斷言偵測：" + result.stdout + result.stderr)
        self.assertRegex(result.stderr, rf"^ASSERT:{label} line=\d+ expr=")
        self.assertEqual("", result.stdout)
        print(f"突變 {name}：結束碼 {result.returncode}；{result.stderr.strip()}", flush=True)
        self.passes(case)

    def control(self, target, case, verdict):
        source = self.source()
        marker = "geo_source_find_" + target + "("
        start = source.index("{", source.index(marker))
        # 僅在函式最前面插入永遠查不到；所有配置與插入路徑維持原碼。
        mutated = source[:start+1] + ("\nreturn SIZE_MAX;" if target == "node" else "\nreturn false;") + source[start+1:]
        self.kill("never-" + target, case, "duplicate-" + verdict, mutated)

    def test_never_find_node_mutant_reports_duplicate(self):
        self.control("node", "nodes", "node")

    def test_never_find_edge_mutant_reports_duplicate(self):
        self.control("edge", "edges", "edge")

    # 以下六個突變各自代表一種索引查找的壞法。node 由 nodes 案例（32 個刻意同槽的鍵）偵測，
    # edge 由 edge-collisions 案例（寫死的同槽鍵與只差 kind 的鍵對）確定性偵測。

    def test_node_compare_ignoring_key_bytes_mutant_reports_merged_node(self):
        # 相等判斷只比 provider 與 key_size：同長度的不同鍵被併成同一個節點。
        self.kill("node-key-bytes-ignored", "nodes", "merged-node",
                  self.inject("||!memcmp(a.key,b.key,a.key_size)", "||1"))

    def test_node_probe_stopping_at_first_occupied_slot_mutant_reports_duplicate(self):
        # 起始槽被別的鍵占用就當作沒找到：被推到後面槽位的鍵永遠查不到，再加入就重複。
        self.kill("node-probe-miss", "nodes", "duplicate-node",
                  self.inject(NODE_PROBE, NODE_PROBE + "if(!geo_source_ref_equal(ctx->nodes[ctx->node_index[slot]-1]->source,source))return SIZE_MAX;"))

    def test_node_probe_accepting_first_occupied_slot_mutant_reports_merged_node(self):
        # 起始槽有人就當作找到、不驗鍵：碰撞的不同鍵被併成同一個節點。
        self.kill("node-probe-hit", "nodes", "merged-node",
                  self.inject(NODE_PROBE, NODE_PROBE + "if(1)return ctx->node_index[slot]-1;"))

    def test_edge_compare_ignoring_kind_mutant_reports_missing_edge(self):
        # 相等判斷漏比 kind：只差 kind 的另一條邊被當成已存在而丟掉。
        self.kill("edge-kind-ignored", "edge-collisions", "missing-edge",
                  self.inject("&&a.kind==b.kind", ""))

    def test_edge_probe_stopping_at_first_occupied_slot_mutant_reports_duplicate(self):
        self.kill("edge-probe-miss", "edge-collisions", "duplicate-edge",
                  self.inject(EDGE_PROBE, EDGE_PROBE + "if(!geo_source_edge_equal(ctx->edges[ctx->edge_index[slot]-1],edge))return false;"))

    def test_edge_probe_accepting_first_occupied_slot_mutant_reports_missing_edge(self):
        self.kill("edge-probe-hit", "edge-collisions", "missing-edge",
                  self.inject(EDGE_PROBE, EDGE_PROBE + "if(1)return true;"))

    def test_edge_probe_reuse_keeps_order_across_rebuild_and_fallback(self):
        self.passes("edge-probe")

    def test_edge_probe_reuse_controls_fail_on_full_ordered_graph(self):
        self.kill("edge-reuse-old-slot-after-resize","edge-probe","duplicate-edge",
                  self.inject("first=0;empty_slot=SIZE_MAX;","first=0;"))
        self.kill("edge-reuse-wrong-empty-slot","edge-probe","duplicate-edge",
                  self.inject("*empty_slot=slot;","*empty_slot=(slot+1)&mask;"))

    def test_edge_probe_reuse_whole_withdrawal_preserves_graph_and_changes_work(self):
        source=self.source();withdrawn=source
        for before,after in reversed(EDGE_PROBE_REUSE_EDITS):
            self.assertEqual(1,withdrawn.count(after))
            withdrawn=withdrawn.replace(after,before)
        restored=withdrawn
        for before,after in EDGE_PROBE_REUSE_EDITS:
            self.assertEqual(1,restored.count(before))
            restored=restored.replace(before,after)
        self.assertEqual(source,restored)
        anchor="static uint64_t geo_source_edge_hash(GeoSourceEdge edge)\n{"
        for phase,contents,expected,calls in (("fixed",source,0,21),("withdrawn",withdrawn,1,31),("restored",restored,0,21)):
            with self.subTest(phase=phase):
                self.assertEqual(1,contents.count(anchor))
                work=self.build.work/("edge-probe-source-"+phase);work.mkdir()
                (work/"source.c").write_text(contents.replace(anchor,anchor+"++edge_probe_hash_calls;"),encoding="utf-8")
                client=work/"client.c";shutil.copy2(self.harness,client)
                exe=self.build.link("edge-probe-cost-"+phase,[self.build.compile(client,"edge-probe-cost-"+phase)])
                semantic=self.case("edge-probe",exe)
                self.assertEqual(0,semantic.returncode,semantic.stdout+semantic.stderr)
                self.assertEqual("PASS edge-probe\n",semantic.stdout)
                self.assertEqual("",semantic.stderr)
                result=self.case("edge-probe-cost",exe)
                print("edge-probe phase="+phase+"\n"+result.stdout+result.stderr,end="")
                self.assertEqual(expected,result.returncode,result.stdout+result.stderr)
                self.assertEqual(f"PROBE_HASH_CALLS={calls}\n"+("PASS edge-probe-cost\n" if expected==0 else ""),result.stdout)
                if expected:self.assertRegex(result.stderr,r"^ASSERT:edge-probe-reuses-lookup-hash line=\d+ expr=")
                else:self.assertEqual("",result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
