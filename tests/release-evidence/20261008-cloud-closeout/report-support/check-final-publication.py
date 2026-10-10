import datetime,hashlib,json,pathlib,subprocess,sys
R=pathlib.Path('/workspace/geometry-axiom'); OUT=pathlib.Path(sys.argv[1]); TESTED='5174a8dafd8c48329d7166abbd3d104e3c28c0c4'
def g(*a): return subprocess.check_output(['git',*a],cwd=R)
def allowed(p): return p.startswith('tests/release-evidence/') or p=='geometry-web/docs/RELEASE-CANDIDATE.md'
def tree(h):
 out={}
 for row in g('ls-tree','-rz',h).split(b'\0'):
  if not row:continue
  meta,name=row.split(b'\t',1); mode,kind,blob=meta.decode().split(); name=name.decode()
  if not allowed(name):out[name]=(mode,blob)
 return out
old=tree(TESTED); head=g('rev-parse','HEAD').decode().strip(); current=tree(head); changes=[]
for name,(mode,blob) in old.items():
 f=R/name;b=f.read_bytes() if f.is_file() else None
 actual=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest() if b is not None else None
 if actual!=blob:changes.append(name)
dirty=g('diff','--name-only','-z','HEAD').decode().strip('\0').split('\0')
untracked=g('ls-files','--others','--exclude-standard','-z').decode().strip('\0').split('\0')
committed=g('diff','--name-only','-z',TESTED,head).decode().strip('\0').split('\0')
outside=[p for p in dirty+untracked+committed if p and not allowed(p)]
result={'observedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'testedProductHead':TESTED,'checkedHead':head,'main':g('rev-parse','origin/main').decode().strip(),'comparedPaths':len(old),'headModeBlobMapsIdentical':old==current,'worktreeBlobChanges':changes,'outsideAllowedPublicationPaths':outside,'committedPublicationPaths':[p for p in committed if p],'trackedDirtyPaths':[p for p in dirty if p],'untrackedPublicationPathCount':len([p for p in untracked if p]),'gitStatus':g('status','--short').decode(),'runtime':'No current live runtime claim; prior completed gates retain recorded runtime and actual process binary identities. Environment-return HTTP refusal preserved separately.'}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
assert old==current and len(old)==1980 and not changes and not outside
print(json.dumps({'checkedHead':head,'comparedPaths':len(old),'changed':changes,'outside':outside,'statusClean':not result['gitStatus']}))
