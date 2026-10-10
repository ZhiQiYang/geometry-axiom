import hashlib,json,pathlib,subprocess,datetime,urllib.request
R=pathlib.Path('/workspace/geometry-axiom'); P=pathlib.Path('/workspace/closure-evidence/public-candidate/report-support')
TESTED='5174a8dafd8c48329d7166abbd3d104e3c28c0c4'
def g(*a): return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def allowed(p): return p.startswith('tests/release-evidence/') or p=='geometry-web/docs/RELEASE-CANDIDATE.md'
old={}
for line in g('ls-tree','-rz',TESTED).strip('\0').split('\0'):
 meta,name=line.split('\t',1); mode,kind,blob=meta.split()
 if not allowed(name): old[name]=(mode,blob)
changed=[]
manifest=[]
for name,(mode,blob) in sorted(old.items()):
 f=R/name
 actual=g('hash-object',str(f)) if f.exists() else None
 if actual!=blob: changed.append(name)
 manifest.append(f'{mode} {blob} {name}')
tracked=g('ls-files','-z').strip('\0').split('\0')
newOutside=[x for x in tracked if x not in old and not allowed(x)]
committed=g('diff','--name-only',TESTED,'HEAD').splitlines()
dirty=g('diff','--name-only','HEAD').splitlines()
print(json.dumps({'changed': changed, 'newOutside': newOutside})); assert not changed and not newOutside
assert all(allowed(x) for x in committed+dirty)
runtime=json.load(urllib.request.urlopen('http://127.0.0.1:18971/runtime',timeout=10))
assert runtime['fresh'] and runtime['version']=='82b45ea9cf53c10b2c4fd6591ce0dd45d055a9d8f0e7e4fb5765eeaf64075200'
record={'schema':'geometry-publication-source-equivalence/1','observedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'testedProductHead':TESTED,'docsMergeHead':g('rev-parse','HEAD'),'main':g('rev-parse','origin/main'),'comparedScope':'All tested tracked paths except tests/release-evidence/** (archived evidence, not registered test sources) and geometry-web/docs/RELEASE-CANDIDATE.md (status document).','pathCount':len(old),'gitModeBlobPathListSHA256':hashlib.sha256(('\n'.join(manifest)+'\n').encode()).hexdigest(),'changedComparedPaths':changed,'newTrackedOutsidePublicationPaths':newOutside,'committedChangesSinceTestedHead':committed,'pendingTrackedChanges':dirty,'runtime':runtime,'publicationAllowedPaths':['tests/release-evidence/**','geometry-web/docs/RELEASE-CANDIDATE.md'],'checkerCorrection':'Preliminary checker used quoted ls-tree paths; non-ASCII names were treated as nonexistent. Corrected path parsing to NUL-delimited -z; comparison criterion unchanged. No product change or test rerun.', 'finalBinding':'Final containing commit, remote equality, clean status and exact-head CI recorded after push in PR #176 publication receipt. Historical gates remain bound to their actual tested SHAs; no claim of rerun on a documentation commit.'}
(P/'publication-source-equivalence.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
(P/'publication-compared-git-blobs.txt').write_text('\n'.join(manifest)+'\n')
print(json.dumps({'pathCount':len(old),'changed':changed,'head':record['docsMergeHead'],'runtimeFresh':runtime['fresh']}))
