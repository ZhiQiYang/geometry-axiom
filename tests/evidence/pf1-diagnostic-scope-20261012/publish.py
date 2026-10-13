import json,pathlib,subprocess,sys,urllib.request
root=pathlib.Path('/workspace/geometry-axiom');folder=pathlib.Path(__file__).resolve().parent;head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip();prepared=pathlib.Path('/tmp/geometry-tests/pr190-scope-publication');prepared.mkdir(parents=True,exist_ok=True)
for name in ('pr-body','completion-comment','reply'):
 data=json.loads((folder/(name+'-template.json')).read_text());data['body']=data['body'].replace('{{HEAD_SHA}}',head)
 (prepared/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False));(prepared/(name+'.md')).write_text(data['body']+'\n')
if '--prepare-only' in sys.argv:print(json.dumps({'head':head,'prepared':str(prepared),'published':False}));sys.exit(0)
assert subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True).strip()=='feat/pf1-finish-surface-20261011'
def public(path):
 with urllib.request.urlopen(urllib.request.Request('https://api.github.com/repos/ZhiQiYang/geometry-axiom/'+path,headers={'User-Agent':'Codex-repository-review'})) as r:return json.load(r)
before=json.loads((folder/'publication-before.json').read_text());pr=public('pulls/190');comment=public('issues/comments/6115302508')
assert pr['head']['sha']==head and pr['state']=='open' and pr['draft'],'PR head or status changed'
desired_body=json.loads((prepared/'pr-body.json').read_text())['body'];desired_comment=json.loads((prepared/'completion-comment.json').read_text())['body']
assert pr['body'] in (before['pr_body'],desired_body),'PR body changed; refresh before publishing'
assert comment['body'] in (before['completion_comment_body'],desired_comment),'Completion comment changed; refresh before publishing'
for method,path,name in [('PATCH','pulls/190','pr-body'),('PATCH','issues/comments/6115302508','completion-comment'),('POST','issues/190/comments','reply')]:
 if name=='pr-body' and pr['body']==desired_body or name=='completion-comment' and comment['body']==desired_comment:continue
 output=subprocess.check_output(['gh','api','-X',method,'repos/ZhiQiYang/geometry-axiom/'+path,'--input',str(prepared/(name+'.json'))],cwd=root)
 (prepared/(name+'-published.json')).write_bytes(output)
print(json.dumps({'head':head,'published':True,'reply_url':json.loads((prepared/'reply-published.json').read_text())['html_url']}))
