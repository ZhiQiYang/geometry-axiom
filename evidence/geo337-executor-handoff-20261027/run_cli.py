from pathlib import Path
import datetime,fcntl,hashlib,json,os,resource,subprocess,sys
sys.dont_write_bytecode=True
ROOT=Path('/workspace/geo337-native-F-cbf0fb62');OUT=Path(__file__).parent;RAW=OUT/'cli-order';SHA='cbf0fb621888596aa14ad5f2349b503e23b1b72d'
BRIDGE=Path('/tmp/g337p52F27/formal/work/tmp/geometry-runtime/07b702aad250b8f104d4/bridge')
assert not RAW.exists();RAW.mkdir();(RAW/'tmp').mkdir()
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
assert git('rev-parse','HEAD')==SHA and not git('status','--porcelain')
lock=open('/tmp/geo337-native-owner.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
sys.path.insert(0,str(ROOT));from tests import binaries
info=binaries.inspect_one(binaries.BY_NAME['bridge'],path=str(BRIDGE));assert info.state=='fresh',info.reason
sys.path.insert(0,'/workspace/scratch/geo337-p52-tools-20261027');import capture
assert h(Path(capture.__file__))=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
probe=ROOT/'evidence/issue318-reading-a-20261023/tools/probe_cli_order.py';before={'probe':h(probe),'bridge':h(BRIDGE),'sidecar':h(BRIDGE.with_name('bridge.fingerprint.json'))}
env={'PATH':os.environ['PATH'],'HOME':os.environ['HOME'],'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8','TMPDIR':str(RAW/'tmp'),'GITHUB_SHA':SHA,'GITHUB_WORKSPACE':str(ROOT),'GEO261_REAPER_LOG':str(RAW/'reaper.jsonl')}
argv=[sys.executable,'-B',str(probe),'--bridge',str(BRIDGE),'--sha',SHA,'--output',str(RAW/'cli-order.json')]
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
capture.dump(RAW/'REQUEST.json',{'sha':SHA,'argv':argv,'cwd':str(ROOT),'environment':env,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_probe_child_timeout_seconds':30,'outer_timeout_seconds':None,'binary_reused_from':'P52 fixed-F build, evidence commit a08a036db335e88608ead761539d3e60b75e8e5d; no rebuild','binary_freshness':info.state,'source_hashes':before,'scope':'Original CLI reachability diagnostic only, not #335 construction-policy acceptance.'})
rec=capture.Recorder(RAW,env,SHA)
row,stdout,stderr=rec.run([sys.executable,'-B','/workspace/geo261-environment/reap_children.py',*argv],cwd=ROOT,timeout=None,check=False,source_sha=SHA,source_variant='original-reading-A-cli-order-diagnostic')
receipt=json.loads((RAW/'cli-order.json').read_text());after={'probe':h(probe),'bridge':h(BRIDGE),'sidecar':h(BRIDGE.with_name('bridge.fingerprint.json'))}
assert before==after and not git('status','--porcelain') and git('rev-parse','HEAD')==SHA
result={'sha':SHA,'actual_exit':row['actual_process_returncode'],'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'diagnostic_complete':row['actual_process_returncode']==0 and all(r['protocol_complete'] for r in receipt['rows']),'observed_orders':[{'order':r['order'],'actual_exit':r['exit_code'],'both_place_accepted':r['both_place_accepted']} for r in receipt['rows']],'construction_route_observed':any(r['both_place_accepted'] for r in receipt['rows']),'source_and_binary_unchanged':True,'new_construction_policy_accepted':False}
capture.dump(RAW/'RESULT.json',result);print(json.dumps(result))
