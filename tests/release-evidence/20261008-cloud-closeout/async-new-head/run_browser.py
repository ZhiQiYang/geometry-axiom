import datetime,json,pathlib,subprocess,sys
base=pathlib.Path(__file__).resolve().parent
label=sys.argv[1]
cmd=[sys.executable,str(base/'browser_probe.py'),'--out',str(base/label),*sys.argv[2:]]
p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
out,err=p.communicate()
(base/(label+'.stdout')).write_text(out)
(base/(label+'.stderr')).write_text(err)
(base/(label+'.command.json')).write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':cmd,'exitCode':p.returncode},indent=2)+'\n')
print(out,end='');print(err,end='',file=sys.stderr);sys.exit(p.returncode)
