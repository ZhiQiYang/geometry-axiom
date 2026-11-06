"""Compile the real bridge with private fault-injection commands, outside the repo.

The private commands do not exist in production. The ledger under test remains
the native World/identity implementation: hooks remove one settled mark, place
the process counter at the uint64 boundary, or make the real final validator
reject a temporary allocation. No allocator is replaced.
"""
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def build(directory):
    cc = shutil.which(os.environ.get("CC", "cc"))
    if not cc:
        raise RuntimeError("Identity fault verification requires a C compiler")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    identity = (ROOT / "geometry-app/native/identity_ledger.inc").read_text(encoding="utf-8")
    marker = "    bool ok = identity_table_ok(after_keys, after_count, built, after_count, problem, sizeof problem);"
    assert identity.count(marker) == 1
    identity = "static bool g_identity_fault_settlement;\n" + identity.replace(marker,
        "    if (g_identity_fault_settlement && after_count) {\n"
        "        g_identity_fault_settlement = false; built[after_count - 1].serial = 0;\n"
        "    }\n" + marker)
    identity_path = directory / "identity_fault_ledger.inc"
    identity_path.write_text(identity, encoding="utf-8", newline="\n")
    core = (ROOT / "current_geometry.c").read_bytes().decode("utf-8")
    include = '#include "geometry-app/native/identity_ledger.inc"'
    assert core.count(include) == 1
    core = core.replace(include, '#include "' + identity_path.as_posix() + '"')
    core_path = directory / "identity_fault_core.c"
    core_path.write_bytes(core.encode("utf-8"))
    bridge = (ROOT / "geometry-web/web_bridge.c").read_text(encoding="utf-8")
    include = '#include "../current_geometry.c"'
    assert bridge.count(include) == 1
    bridge = bridge.replace(include, '#include "' + core_path.as_posix() + '"')
    marker = '        if (strcmp(line, "render") == 0) {'
    assert bridge.count(marker) == 1
    hook = r'''
        if (strcmp(line, "__identity_fail_settlement") == 0 && !arg) {
            g_identity_fault_settlement = true;
            fputs("{\"ok\":true}\n", stdout);
        } else if (strcmp(line, "__identity_drop_last") == 0 && !arg) {
            if (!g_world.app.identity_active || !g_world.app.identity_mark_count)
                fputs("{\"ok\":false,\"error\":\"no settled mark to remove\"}\n", stdout);
            else {
                --g_world.app.identity_mark_count;
                fputs("{\"ok\":true}\n", stdout);
            }
        } else if (strcmp(line, "__identity_counter") == 0 && arg) {
            uint64_t serial = 0;
            if (!identity_parse_serial(arg, &serial))
                fputs("{\"ok\":false,\"error\":\"invalid private serial\"}\n", stdout);
            else {
                g_identity_next_serial = serial;
                g_identity_pending_count = 0;
                g_identity_serial_exhausted = false;
                fputs("{\"ok\":true}\n", stdout);
            }
        } else if (strcmp(line, "render") == 0) {
'''
    bridge = bridge.replace(marker, hook)
    source = directory / "identity_fault_bridge.c"
    source.write_text(bridge, encoding="utf-8", newline="\n")
    binary = directory / ("identity_fault_bridge.exe" if os.name == "nt" else "identity_fault_bridge")
    result = subprocess.run([cc, "-std=c11", "-O0", "-I", str(ROOT), "-I", str(ROOT / "geometry-web"),
        str(source), "-lm", "-o", str(binary)], capture_output=True, text=True)
    if result.returncode:
        raise AssertionError("Identity fault bridge compilation failed: " + result.stderr)
    return str(binary)
