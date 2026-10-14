import pathlib, shutil
root=pathlib.Path('/workspace/scratch/860de1a99063/geometry-axiom')
hook='''static void *fragment_fault_malloc(size_t bytes) {
    static unsigned calls;
    const char *value=getenv("FRAGMENT_OOM_AT");
    if (++calls==(value?strtoul(value,NULL,10):0)) return NULL;
    return malloc(bytes);
}
'''
for mode in ('old','new'):
    target=pathlib.Path('/tmp/geometry217-oom-'+mode)
    shutil.copytree(root,target,dirs_exist_ok=True)
    inc=target/'geometry-core/subgrid_rebind.inc'
    if mode=='old':
        inc.write_bytes(pathlib.Path('/tmp/geometry211-fixed-subgrid_rebind.inc').read_bytes())
        p=target/'current_geometry.c';s=p.read_bytes().replace(b'int k=reference_fragment_candidate',b'bool k=reference_fragment_candidate').replace(b'int n=reference_fragment_candidate',b'bool n=reference_fragment_candidate').replace(b'if (k<0 || n<0 || (!k && !n)) return false;',b'if (!k && !n) return false;');p.write_bytes(s)
    original=inc.read_bytes()
    inc.write_bytes(hook.encode()+original.replace(b'World *candidate=malloc(sizeof *candidate);',b'World *candidate=fragment_fault_malloc(sizeof *candidate);'))
