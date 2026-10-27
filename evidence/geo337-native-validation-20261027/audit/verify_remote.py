import concurrent.futures,hashlib,json,subprocess,sys,urllib.parse
from pathlib import Path
sha=sys.argv[1]
base='https://raw.githubusercontent.com/ZhiQiYang/geometry-axiom/'+sha+'/'
def fetch(path):
    return subprocess.check_output(['curl','-fLsS','--max-time','60',base+urllib.parse.quote(path,safe='/')])
manifest_path='evidence/geo337-native-validation-20261027/MANIFEST.json'
manifest_bytes=fetch(manifest_path)
local=subprocess.check_output(['git','-C','/workspace/geometry-axiom','show',sha+':'+manifest_path])
assert manifest_bytes==local,'remote manifest mismatch'
manifest=json.loads(manifest_bytes)
def check(item):
    path,expected=item
    data=fetch(path)
    actual={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    assert actual==expected,path
    return {'path':path,**actual}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    rows=list(pool.map(check,manifest['files'].items()))
out=Path('/workspace/scratch')/('geo337-remote-verification-'+sha+'.json')
out.write_text(json.dumps({'commit':sha,'manifest_matches_git':True,'all_files_match':True,'files_verified':len(rows),'total_bytes':sum(r['bytes'] for r in rows),'files':rows},indent=2)+'\n')
print(json.dumps({'commit':sha,'verified':len(rows),'receipt':str(out)}))
