"""R362 Python producer mutations: behavioral failure only, always restore source.

Run with fresh GEOMETRY_TEST_BRIDGE and GEOMETRY_MODEL_BASE. This diagnostic is
separate from the native C mutation ledger and never writes that ledger.
"""
import argparse, hashlib, json, os, re, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PRODUCT=ROOT/'geometry-web/model_update.py'
PREFIX='tests.test_model_update_identity_faces.ModelIdentityFaces.'
MUTANTS=[
 ('R362_P01_SOURCE_IDENTITY_INTERFACE',
  '("id", "name", "created_at", "source", "input", "result"), (\'sourceIdentity\',), path=("record",)',
  '("id", "name", "created_at", "source", "input", "result"), (), path=("record",)',
  'test_identified_plan_record_reaches_real_native_replay','R362_SOURCE_IDENTITY_REPLAY'),
 ('R362_P02_FACES_INTERFACE',
  "    if inputs['mode'] == 'faces':\n", "    if inputs['mode'] == 'faces':\n        _fail('UPDATE_SCOPE', 'mutant removes faces producer')\n",
  'test_faces_full_replay_keeps_order_orientation_purpose_and_model_id','R362_FACES_REPLAY'),
 ('R362_P03_FACE_COUNT',
  "if face_mode and len(selection['uses']) != len(record['input']['uses']):",'if False:',
  'test_faces_invalid_count_duplicates_and_injected_orientation_are_rejected','ModelError not raised'),
 ('R362_P04_SLOT_METADATA',
  "'uses':[{**deepcopy(old), 'placement_id':selected['placement_id']}",
  "'uses':[{**deepcopy(old), 'orientation':1, 'purpose':'boundary', 'placement_id':selected['placement_id']}",
  'test_faces_full_replay_keeps_order_orientation_purpose_and_model_id','R362_FACES_REPLAY'),
 ('R362_P05_ROOT_SET',
  'if sorted(found) != sorted(expected):','if False:',
  'test_source_identity_schema_is_validated_before_any_replay','ModelError not raised'),
 ('R362_P06_MARK_RANGE',
  'int(mark[33:]) <= 0xFFFFFFFFFFFFFFFF','int(mark[33:]) <= 0x1FFFFFFFFFFFFFFFF',
  'test_faces_saved_identity_accepts_exact_roots_and_rejects_overflow_or_wrong_key','ModelError not raised'),
 ('R362_P07_FACES_NO_TIMBERS',
  "_keys(value, ('mode', 'uses', 'obstacles'), path=('selection',))",
  "_keys(value, ('mode', 'uses', 'obstacles'), ('timbers',), path=('selection',))",
  'test_faces_cannot_sneak_timbers_into_the_selection','ModelError not raised'),
 ('R362_P08_FACE_CAPACITY',
  "1 <= len(value['uses']) <= 512", "1 <= len(value['uses']) <= 16",
  'test_faces_invalid_count_duplicates_and_injected_orientation_are_rejected','R362_FACE_CAPACITY_CONTRACT'),
]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    original=PRODUCT.read_bytes();source=original.decode();records=[]
    def run(name,method):
        command=[sys.executable,'-B','-m','unittest','-v',method]
        process=subprocess.run(command,cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,timeout=180)
        raw=process.stdout+process.stderr;(out/(name+'.log')).write_bytes(raw)
        return {'command':command,'exit_code':process.returncode,'log':name+'.log','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},raw.decode()
    baseline,log=run('baseline','tests.test_model_update_identity_faces')
    assert baseline['exit_code']==0 and re.search(r'Ran 7 tests .*\n\nOK\n',log),log
    try:
        for name,before,after,method,marker in MUTANTS:
            assert source.count(before)==1,(name,source.count(before))
            PRODUCT.write_bytes(source.replace(before,after).encode())
            mutant,text=run(name,PREFIX+method)
            assert mutant['exit_code']==1 and 'AssertionError:' in text and marker in text and re.search(r'FAILED \(failures=\d+\)',text) and '\nERROR:' not in text and not any(word in text for word in ['BASE_TIMEOUT','TimeoutExpired','bridge closed','skipped=']),(name,text)
            PRODUCT.write_bytes(original)
            restored,normal=run(name+'-restored',PREFIX+method)
            assert restored['exit_code']==0 and 'Ran 1 test ' in normal and '\nOK\n' in normal,(name,normal)
            records.append({'id':name,'baseline':baseline['exit_code'],'mutant':mutant,'restored':restored,'marker':marker})
            print(name,'0/1/0',flush=True)
    finally:PRODUCT.write_bytes(original)
    result={'schema':'r362-producer-mutations/1','official_native_ledger':False,'product_sha256':hashlib.sha256(original).hexdigest(),'baseline':baseline,'mutations':records}
    (out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('all named mutations killed and restored')

if __name__=='__main__':main()
