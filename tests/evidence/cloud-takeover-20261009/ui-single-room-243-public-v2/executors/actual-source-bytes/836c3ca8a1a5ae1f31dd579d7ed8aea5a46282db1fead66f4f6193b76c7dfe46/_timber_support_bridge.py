"""Build the real bridge with the two isolated projection integration hooks.

The shared reference_bridge.inc is left untouched for its integration owner.
Only temporary build inputs get missing glue described in TIMBER-SUPPORTS.md.
Already-integrated hooks are retained, with the projection include redirected
to the requested source so the same helper also supports mutation checks.
"""
import os
from pathlib import Path
import shlex
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def _reference_with_projection(reference, projection):
    include = '#include "timber_support_projection.inc"'
    target = f'#include "{Path(projection).as_posix()}"'
    calls = ['    json_timber_supports(&g_world,fingerprint);',
             '    json_timber_supports(w,fingerprint);']
    pure = 'static void json_references_world(const World *w,const char *fingerprint)'
    call = calls[1] if pure in reference else calls[0]
    supports = '    fputs("],\\\"timberSupports\\\":",stdout);'
    specs = '    fputs(",\\\"specs\\\":[",stdout);'
    if include in reference:
        assert reference.count(include) == 1, 'Duplicate support projection include'
        assert all(reference.count(hook) == 1 for hook in [call, supports, specs]), \
            'Integrated reference support hooks changed'
        assert sum(reference.count(hook) for hook in calls) == 1, \
            'Duplicate support projection call'
        return reference.replace(include, target)
    assert call not in reference and supports not in reference, \
        'Partially integrated reference support hooks'
    marker = 'static void cmd_references(void)'
    assert reference.count(marker) == 1, 'Reference integration hook changed'
    reference = reference.replace(marker, f'{target}\n{marker}')
    marker = '    fputs("],\\\"specs\\\":[",stdout);'
    assert reference.count(marker) == 1, 'Reference integration hook changed'
    return reference.replace(marker, f'{supports}\n{call}\n{specs}')


def build(directory, projection=None):
    override = os.environ.get('GEOMETRY_TEST_SUPPORT_BRIDGE')
    if override:
        if not Path(override).is_file():
            raise RuntimeError('GEOMETRY_TEST_SUPPORT_BRIDGE does not exist')
        return override
    cc = shutil.which(os.environ.get('CC', 'cc'))
    if not cc:
        raise RuntimeError('Native support verification requires a C compiler')
    directory = Path(directory)
    projection = Path(projection) if projection else ROOT / 'geometry-web/timber_support_projection.inc'
    reference = _reference_with_projection(
        (ROOT / 'geometry-web/reference_bridge.inc').read_text(), projection)
    reference_path = directory / 'support_reference_bridge.inc'
    reference_path.write_text(reference)
    bridge = (ROOT / 'geometry-web/web_bridge.c').read_text()
    bridge = bridge.replace('#include "../current_geometry.c"',
                            f'#include "{(ROOT / "current_geometry.c").as_posix()}"')
    bridge = bridge.replace('#include "reference_bridge.inc"',
                            f'#include "{reference_path.as_posix()}"')
    # Fault injection is confined to a heap copy in this test binary. This
    # proves missing/ambiguous facts stay unknown without touching the World.
    marker = '        if (strcmp(line, "render") == 0) {'
    assert bridge.count(marker) == 1
    probe = r'''
        if (strcmp(line,"__support_missing")==0) {
            World *copy=malloc(sizeof *copy); if(!copy) return 2; *copy=g_world;
            for(size_t i=0;i<copy->timber_count;++i) if(copy->timbers[i].id!=7) copy->timbers[i].placed=false;
            char hash[65]; eng_definition_hash(&g_world,hash);
            json_timber_supports(copy,hash); putchar('\n'); free(copy);
        } else if (strcmp(line,"__support_ambiguous")==0 || strcmp(line,"__support_free")==0) {
            const PlacementSurface *p=world_find_placement(&g_world,1);
            TimberAnchor a={0};
            StopFace faces[2]={{STOP_OUTLINE_EDGE,1,0,-1,0,EDGE_FIXED,20,0,4000},
                               {STOP_OUTLINE_EDGE,1,0,-1,1,EDGE_FIXED,20,0,4000}};
            size_t count=2;
            if(!strcmp(line,"__support_free")) { faces[0].fixity=EDGE_FREE; count=1; }
            json_schedule_support_endpoint(&g_world,p,&a,faces,count,true,20,487,514); putchar('\n');
        } else if (strcmp(line, "render") == 0) {
'''
    bridge = bridge.replace(marker, probe)
    source = directory / 'support_web_bridge.c'
    source.write_text(bridge)
    binary = directory / 'support_web_bridge'
    flags = shlex.split(os.environ.get('GEOMETRY_SUPPORT_CFLAGS', '-O2'))
    command = [cc, '-std=c11', *flags, '-I', str(ROOT / 'geometry-web'),
               str(source), '-lm', '-o', str(binary)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(f'Projection bridge compilation failed: {result.stderr}')
    return str(binary)
