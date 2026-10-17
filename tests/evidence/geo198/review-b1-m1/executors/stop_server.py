import json,pathlib,signal,os,urllib.request
out=pathlib.Path('/tmp/geometry-198-review2')
runtime=json.load(urllib.request.urlopen('http://127.0.0.1:18846/runtime'))
expected=json.loads((out/'runtime-before.json').read_text())
assert runtime['pid']==expected['pid'] and runtime['session']==expected['session'] and runtime['fresh']
(out/'runtime-after.json').write_text(json.dumps(runtime,indent=2)+'\n')
request=urllib.request.Request('http://127.0.0.1:18846/api',data=json.dumps({'cmd':'dump'}).encode(),headers={'Content-Type':'application/json'})
dump=json.load(urllib.request.urlopen(request));assert dump['ok']
(out/'server-final-dump.json').write_text(json.dumps(dump,ensure_ascii=False,indent=2)+'\n')
os.kill(runtime['pid'],signal.SIGINT)
print('Preserved dump and stopped owned service',runtime['pid'])
