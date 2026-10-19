"""Measure real native layouts; compare the same declaration minus capture storage."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    header = (ROOT / 'geometry-core/parameter_types.h').read_text()
    declaration = header[header.index('typedef struct {\n    ParameterSet cards'):]
    declaration = declaration[:declaration.index('} ParameterState;') + len('} ParameterState;')]
    capture = '    GridCardCapture card_captures[256]; size_t card_capture_count;\n'
    assert declaration.count(capture) == 1
    old = declaration.replace(capture, '').replace('} ParameterState;', '} ParameterStateWithoutCaptures;')
    code = '#define main geometry_core_entry\n#include "' + str(ROOT / 'current_geometry.c') + '"\n#undef main\n'
    code += old + r'''
int main(void) {
    size_t slots=sizeof(((ParameterState *)0)->card_captures)/sizeof(GridCardCapture);
    size_t delta=sizeof(ParameterState)-sizeof(ParameterStateWithoutCaptures);
    printf("{\"world_bytes\":%zu,\"parameter_state_bytes\":%zu,\"capture_bytes\":%zu,"
           "\"capture_slots\":%zu,\"capture_array_bytes\":%zu,\"capture_count_bytes\":%zu,"
           "\"added_per_world_bytes\":%zu,\"history_slots_per_stack\":%u,"
           "\"added_undo_redo_capacity_bytes\":%zu,\"max_operations\":%u}\n",
           sizeof(World),sizeof(ParameterState),sizeof(GridCardCapture),slots,
           sizeof(((ParameterState *)0)->card_captures),sizeof(((ParameterState *)0)->card_capture_count),
           delta,HISTORY_MAX,delta*HISTORY_MAX*2,ENG_OPERATION_MAX);
    return slots==ENG_OPERATION_MAX ? 0 : 1;
}
'''
    source = out / 'layout.c'
    source.write_text(code)
    command = ['cc', '-std=c11', '-O0', str(source), '-lm', '-o', str(out / 'layout')]
    compile_result = subprocess.run(command, cwd=ROOT, capture_output=True)
    (out / 'compile.stdout').write_bytes(compile_result.stdout)
    (out / 'compile.stderr').write_bytes(compile_result.stderr)
    if compile_result.returncode:
        raise RuntimeError('layout compile failed: ' + str(out / 'compile.stderr'))
    result = subprocess.run([str(out / 'layout')], cwd=ROOT, capture_output=True)
    (out / 'probe.stdout').write_bytes(result.stdout)
    (out / 'probe.stderr').write_bytes(result.stderr)
    report = {'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'header_sha256': hashlib.sha256(header.encode()).hexdigest(), 'compile_command': command,
              'compile_exit': compile_result.returncode, 'probe_exit': result.returncode,
              'layout': json.loads(result.stdout),
              'history_limit_source': [line for line in (ROOT / 'current_geometry.c').read_bytes().decode().splitlines() if re.match(r'#define HISTORY_MAX ', line)]}
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
