"""Read existing L census evidence only; no test or compilation execution."""
import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile

HERE=Path(__file__).parent
RAW=Path('/tmp/pr348-census-L7c8e9cee-text-20261029')
REPO=Path('/dev/shm/pr348-active')
E='75464e8cda864ebea6717f95853f724fb9278583'
L='7c8e9cee4ed5b3706ee919e2831a1dac0aa55ea5'
PREFIX='evidence/geo300-capacity512-20261024/native-census-L7c8e9cee/'
digest=lambda b:hashlib.sha256(b).hexdigest()
def git_bytes(path):
    return subprocess.run(['git','show',E+':'+path],cwd=REPO,capture_output=True,check=True).stdout
names=('COMPLETED_PYTHON_RESULTS.json','stdout.bin','PROCESS.json','SCHEDULING-NOTE.json')
originals={n:(RAW/n).read_bytes() for n in names}
assert all(git_bytes(PREFIX+n)==b for n,b in originals.items())
entries=json.loads(originals['COMPLETED_PYTHON_RESULTS.json'])
by_file={r['file']:r for r in entries}
order=re.findall(r'^\[(\d+)/243\] (\S+) ',originals['stdout.bin'].decode(),re.M)
assert len(entries)==102 and len(order)==107
archive=RAW/'actual-binaries-sidecars-logs.tar'
assert digest(archive.read_bytes())=='45d8650021db66415bf876ef4a1725ee3c2be5a1b0e67bd0d587b507e83070df'
rows=[]; py_sum=Decimal(0); unittest_sum=Decimal(0)
with tarfile.open(archive) as tar:
    for index,name in order:
        row={'index':int(index),'suite':name,'absolute_start_utc':None,
             'parent_run_all_process_seconds':None,'json_runner_seconds':None,
             'unittest_log_seconds':None,'completed':int(index)<107}
        if name.startswith('py:') and int(index)<107:
            fname=name.replace(':','_')+'.json'; entry=by_file[fname]
            member='run_all-logs/'+fname; data=tar.extractfile(member).read()
            assert digest(data)==entry['sha256'] and json.loads(data)==entry['result']
            log_member=member.replace('.json','.unittest.log')
            log=tar.extractfile(log_member).read()
            found=re.findall(rb'Ran (\d+) tests? in ([0-9.]+)s',log)
            assert len(found)==1
            elapsed=Decimal(str(entry['result']['seconds']))
            internal=Decimal(found[0][1].decode()); py_sum+=elapsed; unittest_sum+=internal
            row.update(json_runner_seconds=str(elapsed),unittest_log_seconds=str(internal),
                       json_member=member,json_sha256=digest(data),
                       unittest_member=log_member,unittest_sha256=digest(log),
                       tests=entry['result']['total'],failed=entry['result']['failed'],skipped=entry['result']['skipped'])
        elif int(index)<107:
            member='run_all-logs/'+name.replace(':','_')+'.log'
            data=tar.extractfile(member).read()
            row.update(log_member=member,log_sha256=digest(data),
                       time_limit='No whole-suite elapsed timestamp in retained log; parent table was never emitted.')
            if name=='oracle:framing-selftest':
                row['scan_only_integer_seconds']=90
                row['scan_clock_source']='selftest.py:1459 starts t0 AFTER mutants and golden checks; :1678 prints 90 seconds. Not whole-suite duration.'
        else:
            note=json.loads(originals['SCHEDULING-NOTE.json'])
            row.update(absolute_start_utc=note['census_h7_started_utc_proc'],
                       absolute_start_source='Previously recorded /proc observation in SCHEDULING-NOTE.json; no new proc measurement.',
                       duration='interrupted; no complete H7 JSON and no completed full duration')
        row['cumulative_python_json_seconds_only']=str(py_sum)
        row['cumulative_unittest_log_seconds_only']=str(unittest_sum)
        rows.append(row)
    sidecars=[]
    for name in ('bridge','core','engineering-json-test','integrity','model-base','pf3-algorithm'):
        member=name+'.fingerprint.json';data=tar.extractfile(member).read();side=json.loads(data)
        sidecars.append({'archive_member':member,'sha256':digest(data),'built_at':side['built_at'],
                         'meaning':'Product binary build completion metadata, truncated to seconds; NOT file mtime or a measured compile duration.'})
    oracle=tar.extractfile('run_all-logs/oracle_framing-selftest.log').read().decode()
    scan_ticks=re.findall(r'^\[計時\].*$',oracle,re.M)
process=json.loads(originals['PROCESS.json']);note=json.loads(originals['SCHEDULING-NOTE.json'])
start=datetime.datetime.fromisoformat(process['started_utc'])
h7start=datetime.datetime.fromisoformat(note['census_h7_started_utc_proc'])
before=Decimal(str((h7start-start).total_seconds()))
h7path='evidence/geo300-capacity512-20261024/placed-h7-256747c5/readable-originals/'
h7=json.loads(git_bytes(h7path+'h7/RESULT.json'))
wrapper=json.loads(git_bytes(h7path+'h7-wrapper/RESULT.json'))
heavy=sum(Decimal(str(b['seconds'])) for b in h7['batches'] if b['seconds']>100)
all_batches=sum(Decimal(str(b['seconds'])) for b in h7['batches'])
summary={'schema':'geo348-native-L-existing-time-audit/1','execution_sha':L,'evidence_sha':E,
         'tests_or_compilers_executed':False,'mtime_used_as_duration':False,
         'original_inputs':[{'path':str(RAW/n),'sha256':digest(b),'equal_fixed_E_git_bytes':True} for n,b in originals.items()],
         'archive_sha256':digest(archive.read_bytes()),'rows':rows,'binary_completion_metadata':sidecars,
         'python_reported_sum_102':str(py_sum),'unittest_reported_sum_102':str(unittest_sum),
         'json_minus_unittest_reported_sum':str(py_sum-unittest_sum),
         'clock_meaning':'Python JSON: round(time.time()-started,2), _unittest_runner.py:198-209; unittest log uses separate inner test-run clock, printed to 0.001s. Neither records absolute suite start. Sums preserve printed precision, not exact parent wall duration.',
         'h7_before_wall_seconds_from_recorded_proc_anchor_approx':str(before),
         'unallocated_before_h7_seconds_approx':str(before-py_sum),
         'unallocated_scope':'Six cold registry builds + four non-Python suites + interpreter/parent/IO overhead and rounding. No per-phase stopwatch; cannot call this compile time.',
         'h7_parent_remaining_budget_seconds_approx':str(Decimal(2100)-before),
         'standalone_h7_execution_sha':h7['source_sha'],'standalone_h7_outer_seconds':wrapper['seconds'],
         'standalone_h7_five_large_batch_seconds_sum':str(heavy),
         'standalone_h7_all_nine_batch_seconds_sum':str(all_batches),
         'standalone_h7_inner_nonbatch_difference_seconds':str(Decimal(str(h7['seconds']))-all_batches),
         'conditional_before_h7_plus_standalone_minus_2100_not_forecast':str(before+Decimal(str(wrapper['seconds']))-Decimal(2100)),
         'unrun_subsequent_suite_count':136,'unrun_duration':'unknown; no values inferred from older F or grouped runs',
         'oracle_scan_only_ticks':scan_ticks}
assert py_sum==Decimal('855.05') and unittest_sum==Decimal('838.141')
dest=HERE/'TIMING_AUDIT.json';assert not dest.exists();dest.write_text(json.dumps(summary,ensure_ascii=False,separators=(',',':'))+'\n')
header='index\tsuite\tjson_runner_seconds\tunittest_log_seconds\tcumulative_python_json_seconds_only\tabsolute_start_utc\n'
table=header+''.join('\t'.join(str(row[k]) if row[k] is not None else 'unknown' for k in ('index','suite','json_runner_seconds','unittest_log_seconds','cumulative_python_json_seconds_only','absolute_start_utc'))+'\n' for row in rows)
(HERE/'SUITE_TIMES.tsv').write_text(table)
print(json.dumps({'json':str(dest),'bytes':dest.stat().st_size,'sha256':digest(dest.read_bytes()),
                  'python_sum':str(py_sum),'unittest_sum':str(unittest_sum),'before_h7_approx':str(before),
                  'unallocated_approx':str(before-py_sum),'large_h7_batches':str(heavy)},ensure_ascii=False))
