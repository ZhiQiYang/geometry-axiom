r"""Windows function integration, not native-window E2E.

In a VS Developer Prompt, compile current repo source to TEMP (never the repo):
  cl /nologo /utf-8 /Od /W3 /TC /I. /Fe:%TEMP%\geometry-tests\gdi-contract.exe ^
     /Fo:%TEMP%\geometry-tests\gdi-contract.obj tests\gdi_contract_harness.c ^
     /link /STACK:16777216 user32.lib gdi32.lib comdlg32.lib
Set GEOMETRY_TEST_GDI_HARNESS to that exe and run this test. Rebuild with
/DAUDIT_DISABLE_FAILURES to verify the failure-hit assertion rejects a broken
injector. The source includes the current core through /I., not a stale copy.
"""
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
try:
    from tests import binaries
except ModuleNotFoundError:
    import binaries

HARNESS = os.environ.get('GEOMETRY_TEST_GDI_HARNESS')


@unittest.skipUnless(os.name == 'nt' and HARNESS, 'requires compiled Windows GDI contract harness')
class GdiContract(unittest.TestCase):
    def test_confirmed_failures_release_real_resources(self):
        harness = binaries.require_fresh('gdi', HARNESS)
        with tempfile.TemporaryDirectory(prefix='geometry-gdi-contract-') as directory:
            result = subprocess.run([harness], cwd=directory, capture_output=True, timeout=30)
            log = result.stdout.decode('utf-8', errors='replace')
            self.assertEqual(result.returncode, 0, log + result.stderr.decode('utf-8', errors='replace'))
            failures = [line for line in log.splitlines() if line.startswith('PASS bench injected-failure ')]
            self.assertEqual(len(failures), 11)
            self.assertTrue(all(line.endswith('hits=1') for line in failures))
            self.assertEqual(log.count('PASS bench success '), 2)
            self.assertEqual(log.count('PASS bench no-op '), 1)
            self.assertIn('PASS actual Windows GDI count unchanged;', log)
            self.assertIn('PASS SVG ferror/fclose partial cleanup;', log)
            root = ET.parse(Path(directory) / 'complete.svg').getroot()
            self.assertEqual(root.tag, '{http://www.w3.org/2000/svg}svg')
            self.assertFalse((Path(directory) / 'partial-ferror.svg').exists())
            self.assertFalse((Path(directory) / 'partial-close.svg').exists())


# ---------------------------------------------------------------------------
# #412：GDI 載入場景檔時堆疊上不得同時有兩份 World。
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[1]
PROJECT_STACK = 16 * 1024 * 1024          # /STACK:16777216 與 CI 的 ulimit -s 16384；不拉高
GDI_WINDOW_PROC_FRAME = 135200            # mingw -O2 量到的 gdi_window_proc 框（#412 表格第一列）
APPLY_PROJ_SCENE = REPO / '_ax_r08_snapshot.scene'   # 含成功的 apply-proj；修前 16 MiB 下 SIGSEGV
PLAIN_SCENE = REPO / 'room_a.scene'

# 照 #412 第 2 步的形狀：視窗程序的框 → 產品的快照式載入 → parse_scene_file → apply-proj。
# 和 issue 的 emu.c 不同，這裡呼叫的是 GDI 實際使用的 scene_load_file_with_undo，
# 所以把快照搬回堆疊（撤回修正）會在這裡直接 SIGSEGV。
SCENE_LOAD_HARNESS = r"""
#include <stddef.h>
static int g_fail_alloc, g_fail_snapshot, g_snapshot_calls;
#define GEOMETRY_SCENE_LOAD_ALLOC(size) (g_fail_alloc ? NULL : malloc(size))
#define GEOMETRY_WORLD_SNAPSHOT_ALLOC(size) (++g_snapshot_calls, g_fail_snapshot ? NULL : malloc(size))
#define GEOMETRY_TEST_SCENE_LOAD_SNAPSHOT 1
#define main geometry_program_main
#include "current_geometry.c"
#undef main

static World g_world, g_expected;

__attribute__((noinline)) static int emu_window_proc(World *w, const char *path)
{
    volatile unsigned char frame[GDI_FRAME];      /* gdi_window_proc 自己的框 */
    frame[0] = 1; frame[GDI_FRAME - 1] = 1;
    int result = (int)scene_load_file_with_undo(w, path);
    return result + frame[0] + frame[GDI_FRAME - 1] - 2;
}

int main(int argc, char **argv)
{
    if (argc < 3 || (argc != 3 && strcmp(argv[1], "snapshot-nomem") != 0)) return 64;
    const char *mode = argv[1], *path = argv[2];
    if (strcmp(mode, "load") == 0) {
        int r = emu_window_proc(&g_world, path);
        printf("result=%d undo_count=%zu\n", r, g_history.undo_count);
        if (r != SCENE_LOAD_OK) return 1;
        if (!history_undo(&g_world)) return 2;
        printf("undo_restored=%d\n", memcmp(&g_world, &g_expected, sizeof g_world) == 0);
        return 0;
    }
    if (strcmp(mode, "snapshot-nomem") == 0) {
        /* #412 根治：handler 借不到 World 快照時整行拒絕，世界與歷史都不動；記憶體回來後同一行照常成功。 */
        if (emu_window_proc(&g_world, path) != SCENE_LOAD_OK) return 3;
        for (int i = 3; i < argc; ++i) {
            char text[SCENE_MAX_LINE]; char *tokens[SCENE_MAX_TOKENS];
#ifdef WORLD_SNAPSHOT_CACHE
            /* 快取裡的緩衝不經配置；清空才能讓這一行真的向配置器要快照。 */
            while (g_world_snapshot_cached > 0) free(g_world_snapshot_cache[--g_world_snapshot_cached]);
#endif
            memcpy(&g_expected, &g_world, sizeof g_world);
            size_t depth = g_history.undo_count;
            snprintf(text, sizeof text, "%s", argv[i]);
            int count = split_tokens(text, tokens, SCENE_MAX_TOKENS);
            g_fail_snapshot = 1; g_snapshot_calls = 0;
            bool refused = !apply_scene_line("snapshot-nomem", i, tokens, count, &g_world);
            g_fail_snapshot = 0;
            printf("line=%d refused=%d alloc_calls=%d world_unchanged=%d history_unchanged=%d reported=%d\n", i, refused,
                   g_snapshot_calls, memcmp(&g_world, &g_expected, sizeof g_world) == 0, g_history.undo_count == depth,
                   strstr(scene_last_error(), "World snapshot unavailable") != NULL);
            snprintf(text, sizeof text, "%s", argv[i]);
            count = split_tokens(text, tokens, SCENE_MAX_TOKENS);
            printf("line=%d retry=%d\n", i, apply_scene_line("snapshot-nomem", i, tokens, count, &g_world));
        }
        /* 每行都把快照歸還一次：之後的行重用同一份緩衝，不再向配置器要。 */
        g_snapshot_calls = 0;
        for (int round = 0; round < 3; ++round)
            for (int i = 3; i < argc; ++i) {
                char text[SCENE_MAX_LINE]; char *tokens[SCENE_MAX_TOKENS];
                snprintf(text, sizeof text, "%s", argv[i]);
                int count = split_tokens(text, tokens, SCENE_MAX_TOKENS);
                (void)apply_scene_line("snapshot-reuse", i, tokens, count, &g_world);
            }
        printf("reuse_alloc_calls=%d\n", g_snapshot_calls);
        return 0;
    }
    /* parse-fail / nomem：先載一份，再做會失敗的載入，世界與歷史都不得變。 */
    if (emu_window_proc(&g_world, path) != SCENE_LOAD_OK) return 3;
    memcpy(&g_expected, &g_world, sizeof g_world);
    size_t depth = g_history.undo_count;
    int r;
    if (strcmp(mode, "nomem") == 0) { g_fail_alloc = 1; r = emu_window_proc(&g_world, path); }
    else if (strcmp(mode, "parse-fail") == 0) r = emu_window_proc(&g_world, "__missing_412__.scene");
    else return 64;
    printf("result=%d world_unchanged=%d history_unchanged=%d\n", r,
           memcmp(&g_world, &g_expected, sizeof g_world) == 0, g_history.undo_count == depth);
    return 0;
}
"""


def _stack_limit(size):
    def apply():
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
        if hard != resource.RLIM_INFINITY and hard < size:
            raise OSError('hard stack limit below %d bytes' % size)
        resource.setrlimit(resource.RLIMIT_STACK, (size, hard))
    return apply


_limit_stack_to_project_size = _stack_limit(PROJECT_STACK)


@unittest.skipUnless(os.name == 'posix', 'requires POSIX setrlimit for the 16 MiB stack replay')
class GdiSceneLoadStack412(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cc = shutil.which(os.environ.get('CC', 'cc'))
        if cc is None:
            raise AssertionError('CC not found; this suite needs a C compiler on POSIX')
        cls.tmp = tempfile.TemporaryDirectory(prefix='geometry-412-')
        source = Path(cls.tmp.name) / 'scene_load_412.c'
        source.write_text(SCENE_LOAD_HARNESS, encoding='utf-8')
        cls.exe = str(Path(cls.tmp.name) / 'scene_load_412')
        # 與 tests/binaries.py 的 core 同旗標（-std=c11 -O2）。
        build = subprocess.run([cc, '-std=c11', '-O2', f'-DGDI_FRAME={GDI_WINDOW_PROC_FRAME}', f'-I{REPO}',
                                str(source), '-o', cls.exe, '-lm'], capture_output=True, text=True, timeout=600)
        if build.returncode != 0:
            raise AssertionError('scene_load_412 harness failed to compile:\n' + build.stderr[-4000:])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _run(self, mode, scene, *lines, stack=PROJECT_STACK):
        return subprocess.run([self.exe, mode, str(scene), *lines], cwd=REPO, capture_output=True, text=True,
                              timeout=120, preexec_fn=_stack_limit(stack))

    def test_apply_proj_scene_loads_under_project_16mib_stack(self):
        result = self._run('load', APPLY_PROJ_SCENE)
        self.assertNotEqual(result.returncode, -signal.SIGSEGV,
                            '#412 SIGSEGV: GDI scene-load snapshot is back on the stack '
                            '(two Worlds on a 16 MiB stack)')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('result=0 undo_count=1', result.stdout)
        self.assertIn('undo_restored=1', result.stdout)

    def test_failed_parse_leaves_world_and_history_untouched(self):
        result = self._run('parse-fail', PLAIN_SCENE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('result=1 world_unchanged=1 history_unchanged=1', result.stdout)

    def test_snapshot_allocation_failure_is_reported_and_world_untouched(self):
        result = self._run('nomem', PLAIN_SCENE)
        self.assertNotEqual(result.returncode, -signal.SIGSEGV,
                            '#412 SIGSEGV: snapshot allocation failure was not handled (NULL snapshot used)')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('result=2 world_unchanged=1 history_unchanged=1', result.stdout)

    def test_world_snapshot_allocation_failure_leaves_world_and_history_untouched(self):
        # 一行走 current_geometry.c 的回滾備份（column、space 重宣告），一行走 .inc 的暫存候選（grid-system）。
        with tempfile.TemporaryDirectory(prefix='geometry-412-nomem-') as directory:
            scene = Path(directory) / 'space-redeclare.scene'
            scene.write_text(INLINE_SCENES['space-redeclare.scene'][1], encoding='utf-8')
            lines = ('column 2 in 1 at 2500 1500 size 400 400', 'space 1 boundary 1 2 3 4 5 6',
                     'grid-system 7 name-hex 41 main-along none u repeat 0 600 v repeat 0 400')
            result = self._run('snapshot-nomem', scene, *lines, stack=LINUX_DEFAULT_STACK)
        self.assertNotEqual(result.returncode, -signal.SIGSEGV,
                            '#412 SIGSEGV under the Linux default 8 MiB stack before reaching the handler')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for number in range(3, 3 + len(lines)):
            self.assertIn(f'line={number} refused=1 alloc_calls=1 world_unchanged=1 history_unchanged=1 reported=1',
                          result.stdout, '#412: the handler did not take a heap World snapshot, or a failed '
                          'snapshot changed the world, the history or the diagnostic\n' + result.stdout)
            self.assertIn(f'line={number} retry=1', result.stdout, result.stdout)
        self.assertIn('reuse_alloc_calls=0', result.stdout,
                      '#412: a handler did not return its World snapshot exactly once (no reuse)\n' + result.stdout)


# _WIN32 版（桌面 GDI）用 mingw-w64 編譯：#412 附帶發現的編譯錯誤，以及堆疊框靜態守門。
MINGW = os.environ.get('GEOMETRY_MINGW_CC') or shutil.which('x86_64-w64-mingw32-gcc')
REQUIRE_MINGW = os.environ.get('GEOMETRY_REQUIRE_MINGW') == '1'
ONE_MIB = 1024 * 1024    # World ≈ 6.7 MiB；GDI 框只要含一份 World 就遠超過 1 MiB
# #412 量到的最深鏈（分派表的函式指標邊由人工補上）。
ISSUE_412_CHAIN = ('gdi_window_proc', 'gdi_load_scene_file', 'parse_scene_file', 'apply_applyproj_line',
                   'world_revalidate_candidate', 'reference_check_all', 'app_reference_end_faces',
                   'wood_contact_end_faces_with_sources', 'wood_contact_collect_stops')
# gdi_open_scene_dialog 在 -O2 下被內聯進 gdi_window_proc，其框已算在 gdi_window_proc 內。
GDI_FRAMES_WITHOUT_WORLD = ('gdi_window_proc', 'gdi_load_scene_file', 'interactive_apply_line')


@unittest.skipUnless(MINGW or REQUIRE_MINGW, 'requires mingw-w64 x86_64 gcc for the _WIN32 build check')
class Win32Build412(unittest.TestCase):
    def test_win32_build_compiles_and_scene_load_keeps_world_off_stack(self):
        self.assertTrue(MINGW, 'GEOMETRY_REQUIRE_MINGW=1 but x86_64-w64-mingw32-gcc was not found')
        with tempfile.TemporaryDirectory(prefix='geometry-412-win32-') as directory:
            out = Path(directory) / 'gdi.o'
            build = subprocess.run([MINGW, '-std=c11', '-O2', '-fstack-usage', '-c',
                                    str(REPO / 'current_geometry.c'), '-o', str(out)],
                                   cwd=directory, capture_output=True, text=True, timeout=600)
            errors = [line for line in build.stderr.splitlines() if ' error: ' in line]
            self.assertEqual(build.returncode, 0, '#412 _WIN32 build does not compile:\n' + '\n'.join(errors[:20]))
            frames = {}
            for line in (Path(directory) / 'gdi.su').read_text(encoding='utf-8', errors='replace').splitlines():
                location, size, _kind = line.split('\t')
                name = location.rsplit(':', 1)[-1].split('.')[0]   # 去掉 GCC 的 .isra/.constprop/.part 複本後綴
                frames[name] = max(frames.get(name, 0), int(size))
        for name in GDI_FRAMES_WITHOUT_WORLD:
            self.assertTrue(name in frames, f'{name} missing from the _WIN32 stack-usage report')
            self.assertLess(frames[name], ONE_MIB, f'#412 {name} stack frame holds a World ({frames[name]} B)')
        missing = [name for name in ISSUE_412_CHAIN if name not in frames]
        self.assertEqual(missing, [], 'update ISSUE_412_CHAIN: renamed or inlined functions')
        # 分派表呼叫 WORLD_SNAPSHOT_HANDLER 產生的 name_with_snapshot，它再呼叫 name：兩框同時在堆疊上，一起算。
        chain = sum(frames[name] + frames.get(name + '_with_snapshot', 0) for name in ISSUE_412_CHAIN) \
            + frames.get('scene_load_file_with_undo', 0)
        self.assertLess(chain, PROJECT_STACK, f'#412 chain stack {chain} B exceeds 16 MiB')
        print(f'\n#412 _WIN32 chain stack = {chain} B (16 MiB margin {PROJECT_STACK - chain} B)')



# ---------------------------------------------------------------------------
# #412 根治：World（約 6.7 MiB）不得整份放在任何產品堆疊框；Linux 預設 8 MiB 堆疊下也不溢位。
# 上面兩組只守 GDI 載入（16 MiB）；這組守三支產品（core／bridge／model-base）本身。
# ---------------------------------------------------------------------------
LINUX_DEFAULT_STACK = 8 * 1024 * 1024    # ulimit -s 8192。CI 與 start_local.py 仍是 16 MiB，這裡不改它們。
# 單一堆疊框上限（守門，二選一選 -fstack-usage 而非原始碼掃描）：World 7,061,472 B、GridQueryAxis
# 6,047,280 B；修後最大的合法框是 apply-proj 的面片陣列（約 1.7 MB）。2 MiB 夾在中間：不論變數叫什麼、
# 包在哪個 struct 或陣列裡、是否被內聯進別的函式，整份 World 回到任何一個框都會超過。
FRAME_CAP = 2 * 1024 * 1024
PRODUCT_SOURCES = (('core', 'current_geometry.c'), ('bridge', 'geometry-web/web_bridge.c'),
                   ('model-base', 'geometry-core/model_base.c'))
PRODUCT_ENVS = {'core': 'GEOMETRY_TEST_CORE', 'bridge': 'GEOMETRY_TEST_BRIDGE', 'model-base': 'GEOMETRY_MODEL_BASE'}
# 每個場景至少走到一處修前在堆疊上放整份 World 的 handler（檔:行以修前 main 0c796e30 為準）。
STACK_SCENES = (
    ('_ax_r08_snapshot.scene', 'apply-proj current_geometry.c:9246、delete :9387、column :7858、surface :7205'),
    ('_ax_r7_ridge_strip.scene', 'beam current_geometry.c:7979'),
    ('_edge_gridref_wrong_face.scene', 'surface 無 outline current_geometry.c:7090（失敗回滾）'),
    ('tests/fixtures/legacy-two-axis-stagger-bound.scene', 'placement current_geometry.c:6993'),
    ('_wit_d30_infinite_grid_binding.scene', 'grid-binding grid_bindings.inc:18、from-binding :79、'
     'boundary-vertex-keys boundary_vertex_keys.inc:178、grid-system grid_systems.inc:222、GridQueryAxis subgrids.inc:51'),
    ('_wit_d29_grid_system.scene', 'grid from-system grid_systems.inc:250'),
    ('_wit_d19_subgrid_cell.scene', 'subgrid subgrid_commands.inc:58'),
    ('subgrid-local.scene', 'subgrid subgrid_commands.inc:58'),
)
# repo 裡沒有場景檔走到的四處，用最小場景補上。
INLINE_SCENES = {
    'space-redeclare.scene': ('space 重宣告 current_geometry.c:9658', (
        'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000\n'
        'surface 2 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000\n'
        'surface 3 origin 0 0 0 u +x v +z outline 0,0 4000,0 4000,2500 0,2500\n'
        'surface 4 origin 0 3000 0 u +z v +x outline 0,0 2500,0 2500,4000 0,4000\n'
        'surface 5 origin 0 0 0 u +z v +y outline 0,0 2500,0 2500,3000 0,3000\n'
        'surface 6 origin 4000 0 0 u +y v +z outline 0,0 3000,0 3000,2500 0,2500\n'
        'space 1 boundary 1 2 3 4 5 6\n'
        'column 1 in 1 at 1000 1000 size 400 400\n'
        'space 1 boundary 1 2 3 4 5 6\n')),
    'boundary-keyed.scene': ('boundary-keyed boundary_vertex_keys.inc:263', (
        'boundary 1 outline 0,0 1000,0 1000,800 0,800\n'
        'placement 1 on boundary 1 origin 0 0 0 u +x v +y\n'
        'boundary-vertex-keys 1 outer 1 2 3 4 next-key 5\n'
        'boundary-keyed 1 geometry-hash 280230f158ca1d999ce5184326a6607100866582ddf8f12d3b1cb48a802592af '
        'outline 1:0,0 2:1200,0 3:1200,800 4:0,800\n')),
    'grid-source-rule.scene': ('grid-source-rule grid_subdivision.inc:97', (
        'boundary 1 outline 100,200 2100,200 2100,1800 100,1800\n'
        'placement 1 on boundary 1 origin 0 0 0 u +x v +y\n'
        'boundary-vertex-keys 1 outer 1 2 3 4 next-key 5\n'
        'requires grid-subdivision-rules/1\n'
        'grid-system 1 name-hex 41 main-along none u repeat 0 600 v repeat 0 400\n'
        'grid-source-rule 1 key 1 name-hex 72756c65 selector all-cells divide 3 2\n'
        'grid-source-rule-highwater 1 next 2\n'
        'grid-binding 1 on-boundary 1 from-system 1 vertex-key 1 cell -2 1 anchor 0 1 0 1\n'
        'grid 1 on 1 from-binding 1\n')),
    # tests/test_panel_fill_grid_source.py 的 C0 主格經 bridge dump 存下來的定義。
    'from-fill.scene': ('grid from-fill grid_bindings.inc:109', (
        'requires parameters/1\n'
        'parameters begin\n'
        'parameters card eyJpZCI6OTAsIm5hbWUiOiLploDmqrsiLCJuZXh0RmllbGRJZCI6Mn0=\n'
        'parameters field eyJwYXJhbWV0ZXJJZCI6OTAsImlkIjoxLCJuYW1lIjoiWCIsInR5cGUiOjAsImV4cHJlc3Npb24iOnsiZGVuIjoiMSIs'
        'Im51bSI6IjgiLCJvcCI6ImxpdGVyYWwiLCJ1bml0IjoibW0ifX0=\n'
        'parameters end\n'
        'requires engineering-spec/1\n'
        'engineering material eyJmaW5nZXJwcmludCI6IjVjOWY4YTRiNTBkMjZlMjg5MWFlMWY0Y2YwOWQ5NWQ3OGUzNWI4Mjg1NWFiZWMyYmEx'
        'MDg5MmI3ZmUwMThhMWIiLCJ2YWx1ZSI6eyJpZCI6InBmLWJvYXJkIiwia2luZCI6InBhbmVsIiwibGVuZ3RoIjoxMDAsIm5hbWUiOiLmnb8i'
        'LCJ0aGlja25lc3MiOiI5IiwidmVyc2lvbiI6MSwid2lkdGgiOjEwMH19\n'
        'boundary 8 outline -250,-250 350,-250 350,350 -250,350 kind room_plan\n'
        'requires panel-fill/1\n'
        'finish-surface 1 on boundary 8 origin 0 0 0 u +x v +y n +z side +n name-hex e5a4a9e88ab1e5ae8ce68890e99da2\n'
        'panel-fill 1 definition-hex 7b2266696e697368537572666163654964223a312c22676170223a332c226964223a312c226c656e'
        '677468416c6f6e67223a2276222c226f726967696e223a5b302c305d2c2270616e656c223a7b226964223a2270662d626f617264222c'
        '2276657273696f6e223a317d2c227061747465726e223a227374726169676874222c227468726573686f6c64223a7b226669656c6449'
        '64223a312c22706172616d657465724964223a39307d7d\n'
        'derived-placement 10 definition-hex 7b2266696c6c4964223a312c2268223a33302c226964223a31307d\n'
        'grid 11 on 10 from-fill 1 main-along v\n'
        'guide 1 10 v grid:11:u:-1\n')),
}


def _product(name):
    path = os.environ.get(PRODUCT_ENVS[name])
    if not path:
        raise unittest.SkipTest(f'set {PRODUCT_ENVS[name]} (tests/run_all.py sets it to a fresh {name})')
    return binaries.require_fresh(name, path)


@unittest.skipUnless(os.name == 'posix', 'requires POSIX setrlimit for the 8 MiB stack replay')
class ProductStack8MiB412(unittest.TestCase):
    """同一份輸入在 8 MiB 與 16 MiB 下必須得到逐位元相同的輸出；8 MiB 下 SIGSEGV 就是 #412 回歸。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='geometry-412-8mib-')
        cls.scenes = [(name, REPO / name, why) for name, why in STACK_SCENES]
        for name, (why, text) in INLINE_SCENES.items():
            path = Path(cls.tmp.name) / name
            path.write_text(text, encoding='utf-8')
            cls.scenes.append((name, path, why))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _compare(self, run):
        """{scene: 16 MiB result} for every scene whose 8 MiB run is byte-identical; mismatches fail as subtests."""
        identical = {}
        for name, path, why in self.scenes:
            with self.subTest(scene=name):
                reference = run(path, PROJECT_STACK)
                self.assertNotEqual(reference.returncode, -signal.SIGSEGV, f'{name}: SIGSEGV even at 16 MiB')
                result = run(path, LINUX_DEFAULT_STACK)
                self.assertNotEqual(result.returncode, -signal.SIGSEGV,
                                    f'#412 SIGSEGV under the Linux default 8 MiB stack: {name} ({why})')
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (reference.returncode, reference.stdout, reference.stderr),
                                 f'{name}: 8 MiB output differs from 16 MiB')
                identical[name] = reference
        return identical

    def test_core_scene_replay_under_linux_default_8mib_stack(self):
        core = _product('core')
        out = Path(self.tmp.name) / 'core.svg'

        def run(path, stack):
            out.unlink(missing_ok=True)
            result = subprocess.run([core, '--scene', str(path), '--no-window', '--out', str(out)], cwd=REPO,
                                    capture_output=True, timeout=120, preexec_fn=_stack_limit(stack))
            result.stdout += b'\n--svg--\n' + (out.read_bytes() if out.exists() else b'<none>')
            return result
        identical = self._compare(run)
        refused = sorted(name for name, reference in identical.items() if reference.returncode != 0)
        self.assertLessEqual(set(refused), {'_edge_gridref_wrong_face.scene'}, 'unexpected scene refusal')

    def test_bridge_scene_load_under_linux_default_8mib_stack(self):
        bridge = _product('bridge')

        def run(path, stack):
            script = f'reset\nloadfile {path}\ndump\nrender\nline undo\ndump\n'
            return subprocess.run([bridge], input=script.encode('utf-8'), cwd=REPO, capture_output=True,
                                  timeout=120, preexec_fn=_stack_limit(stack))
        for name, reference in self._compare(run).items():
            self.assertEqual(reference.returncode, 0, name)
            self.assertEqual(len(reference.stdout.splitlines()), 6, name)

    def test_model_base_under_linux_default_8mib_stack(self):
        model = _product('model-base')

        def run(path, stack):
            return subprocess.run([model, str(path)], cwd=REPO, capture_output=True, timeout=120,
                                  preexec_fn=_stack_limit(stack))
        self._compare(run)


@unittest.skipUnless(os.name == 'posix', 'requires GCC -fstack-usage for the product frame cap')
class ProductFrameCap412(unittest.TestCase):
    def test_no_product_stack_frame_holds_a_world(self):
        cc = shutil.which(os.environ.get('CC', 'cc'))
        self.assertIsNotNone(cc, 'CC not found; this suite needs a C compiler on POSIX')
        with tempfile.TemporaryDirectory(prefix='geometry-412-frames-') as directory:
            jobs = {}
            for name, source in PRODUCT_SOURCES:      # 與 tests/binaries.py 同旗標（-std=c11 -O2），三支並行
                jobs[name] = subprocess.Popen([cc, '-std=c11', '-O2', '-fstack-usage', '-c', str(REPO / source),
                                               '-o', str(Path(directory) / (name + '.o'))],
                                              cwd=directory, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            frames, over = {}, []
            for name, job in jobs.items():
                _out, err = job.communicate(timeout=600)
                self.assertEqual(job.returncode, 0, f'{name} does not compile:\n' + err.decode(errors='replace')[-4000:])
                for line in (Path(directory) / (name + '.su')).read_text(encoding='utf-8', errors='replace').splitlines():
                    location, size, _kind = line.split('\t')
                    function = location.rsplit(':', 1)[-1].split('.')[0]
                    frames[(name, function)] = max(frames.get((name, function), 0), int(size))
        for (name, function), size in sorted(frames.items(), key=lambda item: -item[1]):
            if size >= FRAME_CAP:
                over.append(f'{name}: {function} {size} B')
        # 守門自身要真的看得到場景 handler，否則一個空報告也會通過。
        for name, _source in PRODUCT_SOURCES:
            self.assertIn((name, 'apply_scene_line'), frames, f'{name}: stack-usage report misses the scene dispatcher')
        self.assertEqual(over, [], '#412: a product stack frame holds a World-sized value (cap %d B):\n' % FRAME_CAP
                         + '\n'.join(over))
        largest = sorted(frames.items(), key=lambda item: -item[1])[:3]
        print('\n#412 largest product frames: ' + ', '.join(f'{n}:{f} {s} B' for (n, f), s in largest))


if __name__ == '__main__':
    unittest.main()
