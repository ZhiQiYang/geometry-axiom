"""Run actual N1 adapter outputs through the separately published pinned G CLI.

G archive: issue #205 7173437704, 441744 bytes,
sha256 4e694d3eb226318b8854aae9c197f0d4d38ced5a11ec71f37b711192d6bb8a9f.
Supply extracted r03g directory; no network and no new G policy is installed.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
PINS={'obstacle_oracle.py':'40458176160c02a1c119bf791f1466512e9ba096965f79292cabb14c35c73f55',
      'obstacle_check.py':'e5a906eb986cab31485287235b838c51c829f3a1d976b4c5fcc02f9ec170ef26'}
def sha(x):return hashlib.sha256(x).hexdigest()
def run(cmd,path):
 p=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=60)
 path.with_suffix('.stdout').write_bytes(p.stdout);path.with_suffix('.stderr').write_bytes(p.stderr)
 r=dict(command=cmd,exit=p.returncode,stdout=dict(bytes=len(p.stdout),sha256=sha(p.stdout)),stderr=dict(bytes=len(p.stderr),sha256=sha(p.stderr)))
 path.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');return p,r
def main():
 p=argparse.ArgumentParser();p.add_argument('--g-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 g=a.g_root.resolve()/'g-oracle';out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);assert not list(out.iterdir())
 for name,pin in PINS.items():assert sha((g/name).read_bytes())==pin,('G_PIN',name)
 raw,_=run(['node','tests/diagnostics/r13_n1_g_inputs.cjs'],out/'inputs');assert raw.returncode==0,'N1_ACTUAL_ADAPTER_EXECUTION'
 results=[]
 for case in json.loads(raw.stdout):
  path=out/(case['name']+'.input.json');path.write_text(json.dumps(case['converted']['input'],indent=2)+'\n')
  raw,receipt=run([sys.executable,'-B',str(g/'obstacle_oracle.py'),str(path),'--repo',str(ROOT)],out/case['name'])
  result=json.loads(raw.stdout);assert raw.returncode==case['expected_exit'],('N1_G_EXPECTED_EXIT',case['name'],result)
  if raw.returncode==0:assert result['status']=='geometry_ok' and result['independent_failures']==[],('N1_G_CHECKER',case['name'])
  elif raw.returncode==1:assert case['expected_code'] in json.dumps(result) and result['status']=='conflict',('N1_G_CONFLICT',case['name'])
  else:assert result==dict(status='input_rejected',code=case['expected_code']),('N1_G_REJECTION',case['name'])
  results.append(dict(name=case['name'],receipt=receipt,result_status=result['status'],expected_code=case['expected_code'],checker_ran=raw.returncode!=2))
 for name,pin in PINS.items():assert sha((g/name).read_bytes())==pin
 (out/'summary.json').write_text(json.dumps(dict(schema='r13-n1-g-compat/1',source_pins=PINS,cases=results),indent=2)+'\n')
 print(json.dumps(dict(cases=len(results),geometry_ok=6,conflict=1,input_rejected=2)))
if __name__=='__main__':main()
