import os,json,subprocess,urllib.request
print('pwd',os.getcwd())
for args in [['git','status','--short'],['git','rev-parse','HEAD']]:
 r=subprocess.run(args,capture_output=True,text=True); print(json.dumps({'command':args,'stdout':r.stdout,'stderr':r.stderr,'exit':r.returncode}))
try:
 print('runtime',urllib.request.urlopen('http://127.0.0.1:18971/runtime',timeout=5).read().decode())
except Exception as e:
 print('runtime unavailable after environment return:',repr(e)); raise
