from pathlib import Path
import hashlib,json,runpy,subprocess,tarfile,platform,shutil
ROOT=Path('/workspace/geo337-native-F-cbf0fb62')
OUT=Path('/workspace/scratch/geo337-pf3-F-cbf0fb62-20261027')
TOOLS=Path(__file__).parent
SHA='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
def h(data):return hashlib.sha256(data).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
result=json.loads((OUT/'RESULT.json').read_text())
assert result['actual_exit']==0 and result['passed']
scope=runpy.run_path(str(ROOT/'tests/pf3_mutation_check.py'),run_name='pf3_receipt_verifier')
cases=[('baseline',[], 'all',''),*scope['CASES'],('restored',[],'all','')]
summary=json.loads((OUT/'subject/summary.json').read_text())
original=json.loads((OUT/'subject/sources.json').read_text())
rows=[]
for name,patches,selection,marker in cases:
    d=OUT/'subject'/name
    expected={rel:(ROOT/rel).read_bytes() for rel in original}
    assert all(h(data)==original[rel] for rel,data in expected.items())
    for rel,before,after in patches:
        assert expected[rel].count(before.encode())==1
        expected[rel]=expected[rel].replace(before.encode(),after.encode())
    assert set(str(p.relative_to(d/'source')) for p in (d/'source').rglob('*') if p.is_file())==set(expected)
    assert all((d/'source'/rel).read_bytes()==data for rel,data in expected.items()),name
    r=json.loads((d/'result.json').read_text())
    build=json.loads((d/'build/execution.json').read_text());test=json.loads((d/'tests/execution.json').read_text())
    assert build['exit']==0 and test['exit']==r['exit']
    assert all(h((d/'binaries'/f).read_bytes())==digest for f,digest in r['artifacts'].items())
    assert selection==test['argv'][-1]
    if name in ('baseline','restored'):
        assert r['verdict']=='pass' and r['counts']==dict(run=20,failures=0,errors=0,skipped=0)
    else:
        assert r['verdict']=='killed' and r['counts']==dict(run=1,failures=1,errors=0,skipped=0)
        assert marker in (d/'tests/stderr').read_text() and 'AssertionError' in (d/'tests/stderr').read_text()
        assert r['artifacts']['bridge']!=summary['baseline']['artifacts']['bridge']
    rows.append({'id':name,'verdict':r['verdict'],'counts':r['counts'],'required_marker':marker,'build_seconds':build['seconds'],'test_seconds':test['seconds'],'source_files':len(expected),'source_matches_original_prescribed_patch':True})
inventory={str(p.relative_to(OUT/'subject')):{'bytes':p.stat().st_size,'sha256':h(p.read_bytes())} for p in sorted((OUT/'subject').rglob('*')) if p.is_file()}
with tarfile.open(OUT/'subject.original.tar.gz','r:gz') as tar:
    actual={m.name.removeprefix('subject/'):{'bytes':m.size,'sha256':h(tar.extractfile(m).read())} for m in tar.getmembers() if m.isfile()}
assert actual==inventory
dump(OUT/'SUBJECT_INVENTORY.json',inventory)
dump(OUT/'VERIFICATION.json',{'sha':SHA,'source_variants':len(rows),'cases':rows,'source_inventory_files':len(original),'archive_files':len(inventory),'archive_bytes_verified':sum(r['bytes'] for r in inventory.values()),'archive_roundtrip_all_bytes_match':True})
owned=[]
for p in Path('/proc').glob('[0-9]*'):
    try:
        cwd=str((p/'cwd').resolve());cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
        if cwd.startswith(str(OUT/'subject')) or (cmd.startswith(str(OUT/'subject'))):owned.append({'pid':int(p.name),'cwd':cwd,'argv':cmd})
    except (OSError,RuntimeError):pass
dump(OUT/'OWNED_PROCESSES_AFTER.json',owned);assert not owned
authority=ROOT/'evidence/geo337-train-20261024/prepared-during-F8/f9-nonperf-v2/tools/REQUESTS.json'
shutil.copy2(authority,OUT/'COMMAND_AUTHORITY.original.json')
dump(OUT/'ENVIRONMENT.json',{'platform':platform.platform(),'compiler':subprocess.check_output(['cc','--version'],text=True),'source_head':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),'source_status':subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'],text=True),'scope':'managed cloud native acceptance; historical WSL receipt is not reused'})
request=json.loads((OUT/'REQUEST.json').read_text())
report=f'''# Fixed-F PF3 complete mutation acceptance

Execution source `{SHA}`. Original producer exit **0**, no test/source/assertion changes. Started {request['started_utc']}; completed {result['completed_utc']}; elapsed {result['elapsed_seconds']:.3f} seconds.

- Baseline: 20 passed, zero failures/errors/skips.
- Original 19 mutations: 19 killed by the named original assertion; each ran one test with one AssertionError, zero errors/skips. Every bridge differs from baseline. No compile failure, crash, timeout or identical binary counted as a kill.
- Restored: 20 passed, zero failures/errors/skips.
- All 21 source variants match the original source plus the exact producer-prescribed patch list. The host-identity case intentionally has the two original patches; the judge is unchanged.
- Original checkout stays clean at F; {len(original)} input source files retain their original bytes. No remaining owned subject processes found.

Command: `python3 -B tests/pf3_mutation_check.py --out /workspace/scratch/geo337-pf3-F-cbf0fb62-20261027/subject --jobs 1`, from the fixed-F clean checkout. Stack 16 MiB. Original timeout is 900 seconds per build/test subprocess; original producer has no overall timeout. Full argv and explicit environment are in REQUEST.json. Scope authority is the original producer, PF3-NATIVE.md and the retained original formal command plan. D43/D44 and R42/R43 remain the behavior SSOT.

Operational capture only: private output/TMPDIR, exclusive owner lock and a process-local subreaper for this container's non-reaping PID1. No mount, symlink or shared native output rewrite. Source variants and binaries are private to this run. Previous native, oracle, reader and required-eight results were not rerun.

`subject.original.tar.gz` preserves every original source copy, ELF, fingerprint, full build/test stdout/stderr, execution record, result and summary: {len(inventory)} files, {sum(r['bytes'] for r in inventory.values())} uncompressed bytes. Every archived file was read back and compared with the retained original; SUBJECT_INVENTORY.json indexes exact hashes. VERIFICATION.json independently checks all 21 patch identities and all original classifications. Original stdout.bin/stderr.bin and the capture tools are retained separately. No original is deleted.

This is fixed-F cloud PF3 validation, with its own identity; the historical WSL results are not relabelled. It makes no claim about browser, Q38, P189 or remote CI acceptance. The next non-overlapping missing fixed-F scope is the original complete Q38 registry (SPM01–SPM44); browser remains assigned elsewhere.
'''
(TOOLS/'HANDOFF.md').write_text(report)
print(json.dumps({'passed':True,'variants':len(rows),'archive_files':len(inventory),'archive_bytes':(OUT/'subject.original.tar.gz').stat().st_size}))
