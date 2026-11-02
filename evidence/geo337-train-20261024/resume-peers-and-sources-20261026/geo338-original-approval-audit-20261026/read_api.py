import pathlib,subprocess,json,hashlib,datetime,sys
p=pathlib.Path(__file__).parent
name,endpoint=sys.argv[1:3]
assert name.replace('-','').replace('_','').isalnum()
a=['gh','api','--include','--method','GET',endpoint]
r=subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
(p/(name+'.http')).write_bytes(r.stdout);(p/(name+'.stderr')).write_bytes(r.stderr)
m={'argv':a,'exit_code':r.returncode,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stdout_bytes':len(r.stdout),'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_bytes':len(r.stderr)}
raw=r.stdout.replace(b'\r\n',b'\n');m['http_status_line']=raw.split(b'\n',1)[0].decode(errors='replace')
try:
 j=json.loads(raw.split(b'\n\n',1)[1]); (p/(name+'.json')).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n');m['json_type']=type(j).__name__;m['items']=len(j) if isinstance(j,list) else None
except Exception as e:m['parse_error']=type(e).__name__
(p/(name+'.meta.json')).write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(m))
