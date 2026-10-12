import hashlib,json,os,pathlib,resource,subprocess,sys,time
root=pathlib.Path.cwd();out=pathlib.Path('/tmp/geometry-182-cause/full-gate');out.mkdir(parents=True,exist_ok=True)
resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def capture():
    paths=set(root.glob('*.c'))|set(root.glob('*.h'))|set(root.glob('*.inc'))
    for folder in ('geometry-core','geometry-web'):
        paths|={p for p in (root/folder).rglob('*') if p.is_file() and p.suffix in ('.c','.h','.inc') and 'vendor' not in p.parts}
    for pattern in ('tests/*.py','geometry-core/*.py','geometry-core/modeling/*.py','geometry-web/*.py'):
        paths|=set(root.glob(pattern))
    paths|={root/n for n in ('公理層.md','geometry-guide/公理層-白話.md','geometry-guide/公理層-閱讀器.html','BACKLOG.md','決策佇列.md','tests/run_all.expected.json','tests/mutants_results.json')}
    binaries={}
    for name in ('bridge','model-base'):
        path=pathlib.Path('/tmp/geometry-tests')/name;sidecar=pathlib.Path(str(path)+'.fingerprint.json')
        binaries[name]={'sha256':sha(path),'sidecar_sha256':sha(sidecar),'sidecar':json.loads(sidecar.read_text())}
    c=(root/'current_geometry.c').read_bytes()
    return {'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'status':subprocess.check_output(['git','status','--porcelain'],text=True).splitlines(),
            'sources':{p.relative_to(root).as_posix():sha(p) for p in sorted(paths)},
            'ssot_lf_sha256':hashlib.sha256((root/'公理層.md').read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
            'c_bytes':{'crlf':c.count(b'\r\n'),'bare_lf':c.count(b'\n')-c.count(b'\r\n'),'nul':c.count(b'\0')},'binaries':binaries}
before=capture();assert before['status']==[]
(out/'checkout-before.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n')
argv=[sys.executable,'-u','tests/section_profile_mutation_check.py','--receipt',str(out/'mutations.json'),'--logs',str(out/'logs')]
start=time.monotonic()
with (out/'stdout.log').open('wb') as log,(out/'stderr.log').open('wb') as errors:
    run=subprocess.run(argv,cwd=root,stdout=log,stderr=errors)
after=capture();(out/'checkout-after.json').write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
receipt={'argv':argv,'cwd':str(root),'returncode':run.returncode,'seconds':time.monotonic()-start,'stack_bytes':16777216,
         'stdout_sha256':sha(out/'stdout.log'),'stderr_sha256':sha(out/'stderr.log'),'before_after_equal':before==after,
         'scope':'Cloud standalone mutation gate only, original default jobs=4; not aggregate, AC16 completion, WSL or seven jobs'}
(out/'run.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
assert before==after
sys.exit(run.returncode)
