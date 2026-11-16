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
static int g_fail_alloc;
#define GEOMETRY_SCENE_LOAD_ALLOC(size) (g_fail_alloc ? NULL : malloc(size))
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
    if (argc != 3) return 64;
    const char *mode = argv[1], *path = argv[2];
    if (strcmp(mode, "load") == 0) {
        int r = emu_window_proc(&g_world, path);
        printf("result=%d undo_count=%zu\n", r, g_history.undo_count);
        if (r != SCENE_LOAD_OK) return 1;
        if (!history_undo(&g_world)) return 2;
        printf("undo_restored=%d\n", memcmp(&g_world, &g_expected, sizeof g_world) == 0);
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


def _limit_stack_to_project_size():
    import resource
    soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
    if hard != resource.RLIM_INFINITY and hard < PROJECT_STACK:
        raise OSError('hard stack limit below the project 16 MiB')
    resource.setrlimit(resource.RLIMIT_STACK, (PROJECT_STACK, hard))


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

    def _run(self, mode, scene):
        return subprocess.run([self.exe, mode, str(scene)], cwd=REPO, capture_output=True, text=True,
                              timeout=120, preexec_fn=_limit_stack_to_project_size)

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
        chain = sum(frames[name] for name in ISSUE_412_CHAIN) + frames.get('scene_load_file_with_undo', 0)
        self.assertLess(chain, PROJECT_STACK, f'#412 chain stack {chain} B exceeds 16 MiB')
        print(f'\n#412 _WIN32 chain stack = {chain} B (16 MiB margin {PROJECT_STACK - chain} B)')


if __name__ == '__main__':
    unittest.main()
