from pathlib import Path
import hashlib,json,re,shutil,subprocess,tarfile

audit=Path(__file__).parent
out=Path('/workspace/scratch/geo337-native-F-cbf0fb62-20261027-r2')
result=json.loads((out/'RESULT.json').read_text())
request=json.loads((out/'REQUEST.json').read_text())
assert result['sha']=='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
for name,expected in json.loads((out/'SHA256.json').read_text()).items():
    data=(out/name).read_bytes()
    assert len(data)==expected['bytes'] and hashlib.sha256(data).hexdigest()==expected['sha256'],name
verified=[]
with tarfile.open(out/'native-output.original.tar.gz') as tar:
    for member in tar:
        if not member.isfile(): continue
        data=tar.extractfile(member).read()
        original=Path('/tmp')/member.name
        assert hashlib.sha256(data).digest()==hashlib.sha256(original.read_bytes()).digest(),member.name
        verified.append(member.name)
(out/'ARCHIVE_VERIFICATION.json').write_text(json.dumps({'original_manifest_verified':True,'archive_files_match_live_owned_output':True,'files':verified},indent=2)+'\n')
for source,dest in [('run_native_F.py','launcher.original.py'),('reaper.py','reaper.original.py'),('reaper-selftest.json','reaper-selftest.json'),('F-r2-launcher.stdout','launcher.stdout.bin'),('F-r2-launcher.stderr','launcher.stderr.bin')]:
    shutil.copy2(audit/source,out/dest)
bindings={}
for name in ['run_native_F.py','reaper.py']:
    earlier=subprocess.check_output(['git','-C','/workspace/geometry-axiom','show','1202060804dc05b9d9eb58994be7cf7a3254e05d:evidence/geo337-native-validation-20261027/audit/'+name])
    assert earlier==(audit/name).read_bytes(),name
    bindings[name]=hashlib.sha256(earlier).hexdigest()
(out/'LAUNCHER_BINDING.json').write_text(json.dumps({'matches_precompletion_commit':'1202060804dc05b9d9eb58994be7cf7a3254e05d','sha256':bindings},indent=2)+'\n')
text=(out/'stdout.bin').read_text()
total_line=next(line for line in text.splitlines() if line.startswith('合計(已執行、有計數者)'))
counts=re.search(r'\)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+',total_line)
assert counts,total_line
total,passed,failed,skipped=map(int,counts.groups())
suites=re.findall(r'^\[(\d+)/(\d+)\]',text,re.M)
assert suites[-1]==('230','230'),suites[-1]
ledger=next(line for line in text.splitlines() if line.startswith('mutation:check'))
summary={'sha':result['sha'],'actual_exit':result['actual_process_returncode'],'timed_out':result['timed_out'],'suite_count':230,'counted_total':total,'passed':passed,'failed':failed,'skipped':skipped,'ledger_row':ledger,'elapsed_seconds':result['elapsed_seconds'],'checkout_clean':result['status_after']=='','sampled_max_allocated_bytes':result['sampled_max_allocated_bytes']}
(out/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(out/'README.md').write_text(f'''# Complete recovery F native execution

Executed SHA: `{result['sha']}` in clean detached checkout `/workspace/geo337-native-F-cbf0fb62`.

- Actual native exit **{result['actual_process_returncode']}**; timeout **{result['timed_out']}**; all **230 suites** executed.
- Counted total **{total}**, pass **{passed}**, fail **{failed}**, skip **{skipped}**. The original permitted Windows GDI harness skip is visible in stdout.
- Elapsed **{result['elapsed_seconds']:.3f} seconds**, original cap **2100 seconds**; stack **16384 KiB**.
- Request time UTC: `{request['started_utc']}`. Completion UTC: `{result['completed_utc']}`.
- Command: `ulimit -s 16384` then `python3 tests/run_all.py --build`. No source, assertion, test inventory, expected count, workflow, or timeout changes. Checkout clean after run: **{result['status_after']==''}**.
- Ledger row: `{ledger.strip()}`.
- Five-second sampled maximum output: **{result['sampled_max_allocated_bytes']} allocated bytes**, **{result['sampled_max_logical_bytes']} logical bytes**. This is a sampled maximum, not an exact instantaneous peak.

## Environment deviations and originals

The current environment has sufficient writable tmpfs at `/tmp`; no SHM, bind mount, symlink, or mount namespace is used. Fixed native output remains `/tmp/geometry-tests`; TMPDIR points to the owned receipt temp directory on /workspace. Device/free-byte data before and after, plus five-second samples, are retained.

Container PID 1 is `tail`, which did not reap killed orphans in the prior a4bd run. This launcher uses process-local `PR_SET_CHILD_SUBREAPER` and reaps only its adopted exited children, identified by parent PID and zombie state. It does not relax the test's empty-process-group assertion. The same original assembly mutation suite passed 12/12 in this run. `REAPER.json`, `REAPED.json`, `reaper.original.py`, and its actual selftest record document the adjustment. Launcher/helper bytes match the previously published commit; see `LAUNCHER_BINDING.json`.

`stdout.bin`/`stderr.bin` are the original native streams; `launcher.stdout.bin`/`launcher.stderr.bin` are separate outer-launcher streams. `native-output.original.tar.gz` retains binaries, fingerprints, and all suite logs. The original end-of-run `SHA256.json` was verified before adding documentation; `ARCHIVE_VERIFICATION.json` verifies every archived regular file against owned output. The enclosing publication MANIFEST covers later additions too.

The withdrawn a4bd complete failure and interrupted first F launcher attempt remain separate evidence directories, with their actual SHAs and exits. They are not relabelled as this attempt. No GitHub Actions execution is claimed by this local container receipt.
''')
print(json.dumps(summary,ensure_ascii=False,indent=2))
