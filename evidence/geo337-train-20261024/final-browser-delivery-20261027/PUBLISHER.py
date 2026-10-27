#!/usr/bin/env python3
"""Ordinary fast-forward evidence publication. No fetch, promisor ingestion or blob API writes."""
import pathlib,sys,json,hashlib,os,re,importlib.util,shutil,base64
P=pathlib.Path
HERE=P(__file__).resolve().parent
ROOT=P('/dev/shm/geometry-axiom-geo337-20261025/final-browser-delivery-20261027')
PROVIDER=ROOT.parent/'recovery-bundle-20261027/git-publication/repo.git'
OLD='e5da59b7e570a360f99ee07e2194c938da0c2626'
BRANCH='codex/train337-recovered-evidence-20261026'
REMOTE='https://github.com/ZhiQiYang/geometry-axiom.git'
PRE='evidence/geo337-train-20261024/'
DST=PRE+'final-browser-delivery-20261027/'
GROUPS=['F-space','F-timber','F-canvas','reception-publication']
INPUTS_SHA='f85d5b81729c611972a37bf30f042c8501514d8477fffec710b3ab890cc8d353'
HELP=P('/tmp/geo-card-F-no-fetch-delivery-20261027/publish_no_fetch.py')
HELP_SHA='dcf40e34228eac195f223a6090a06bd303d515e48f6e47d37ec5ea9814338e44'
CAP=P('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAP_SHA='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
OLD_DOCS={PRE+'PROGRESS.md':(10733,'2ac3af40322f77bc240a5f0c8132f7f0bb2a18804ff7a7736e30b3a94d990649','cff0a183dfd4c5c66c464ddae7b2fee742ff4dc1')}
def h(b):return hashlib.sha256(b).hexdigest()
def oid(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def js(x):return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
def need(v,msg):
 if not v:raise RuntimeError(msg)
def loadmod(name,p,pin):
 need(h(p.read_bytes())==pin,name+' tool pin');sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m

def allowed_sources():
 return {**{DST+g+'.tar.gz':ROOT/(g+'.tar.gz') for g in GROUPS},PRE+'PROGRESS.md':HERE/'PROGRESS.md',DST+'FINAL_PLAN.json':HERE/'FINAL_PLAN.json',DST+'FINAL_COST.json':HERE/'FINAL_COST.json',DST+'BUILD_RESULT.json':ROOT/'RESULT.json',DST+'FINAL_BUILDER_PEER.json':HERE/'FINAL_BUILDER_PEER.json',DST+'BUILD_ACTUAL_PEER.json':HERE/'BUILD_ACTUAL_PEER.json',DST+'PUBLISHER.py':HERE/'publish.py',DST+'PUBLISHER_PEER.json':HERE/'PUBLISHER_PEER.json'}

def alias_contract():
 raw=(HERE/'FIXED_INPUTS.json').read_bytes();need(h(raw)==INPUTS_SHA,'fixed15 alias source mapping');q=json.loads(raw)
 need(q['parent']==OLD and len(q['aliases'])==15 and sum(r['size']for r in q['aliases'])==100217727,'same complete prior readback15')
 rows=[{'destination':r['new_leaf'],'git_blob':r['git_blob'],'old_path':r['fixed_public_path'],'bytes':r['size'],'sha256':r['sha256']}for r in q['aliases']]
 need(len({r['destination']for r in rows})==15 and len({r['git_blob']for r in rows})==15,'unique15 alias leaves and blobs')
 need(all(r['destination'].startswith(DST+'six-bundle-publication/raw/subcommands/') and r['destination'].endswith('/stdout.bin') for r in rows),'exact alias namespace')
 return rows

def main():
 need(len(sys.argv)==3 and sys.argv[1] in ['--check','--execute'],'usage: publish.py --check|--execute MANIFEST_SHA256')
 need(sys.dont_write_bytecode and not sys.flags.optimize,'python -B, no optimize')
 mraw=(HERE/'MANIFEST.json').read_bytes();need(h(mraw)==sys.argv[2],'manifest pin');m=json.loads(mraw)
 need(m['parent']==OLD and m['branch']==BRANCH,'fixed parent/branch')
 allowed=allowed_sources();rows=m['files'];need({r['destination'] for r in rows}==set(allowed) and len(rows)==len(allowed),'exact payload leaves')
 payloads={}
 for r in rows:
  dst=r['destination'];p=P(r['source_path']);need(p==allowed[dst] and p.resolve()==p and p.is_file() and not p.is_symlink(),'exact source regular path')
  b=p.read_bytes();need(len(b)==r['size'] and h(b)==r['sha256'] and oid(b)==r['git_blob'],'full input identity');need(len(b)<100*1024**2,'single Git blob ceiling');payloads[dst]=b
 build=json.loads((ROOT/'RESULT.json').read_bytes());need(build['exit_code']==0 and len(build['archives'])==4,'exact completed four archives')
 for r in build['archives']:
  b=payloads[DST+r['name']+'.tar.gz'];need(r['roundtrip_exit']==0 and len(b)==r['size'] and h(b)==r['sha256'],'original successful archive result')
 aliases=alias_contract();need(m['aliases']==aliases,'exact immutable full-stdout alias list');alias_by_path={r['destination']:r for r in aliases};alias_oids={r['git_blob']for r in aliases}
 helper=loadmod('card_helper',HELP,HELP_SHA);helper.ROOT=ROOT;helper.PROVIDER=PROVIDER;helper.OWNS=[ROOT.parent,P('/dev/shm/geo337-F9-browsers-20261025')]
 packet=sum(map(len,payloads.values()));L=len(payloads)+len(aliases);M=len(mraw);base=3*packet+L*65536+M*8+67108864
 loose=sum(len(b)+(len(b)>>12)+(len(b)>>14)+(len(b)>>25)+4096 for b in payloads.values())
 parts={'new_loose_payloads_zlib_bound':loose,'possible_outgoing_pack':loose+16*1024**2,'all_new_payload_remote_readback':packet,'new_trees_metadata_command_streams':16*1024**2,'state_manifest':4*1024**2,'original_reserve':67108864}
 budget=max(base,sum(parts.values()));working=2*packet+128*1024**2
 summary={'P':packet,'L':L,'M':M,'original_formula':base,'components':parts,'budget':budget,'working_memory_bound':working,'no_fetch':True,'no_payload_stdin':True,'alias_new_payload_bytes':0,'alias_count':len(aliases),'alias_proof':'New remote tree/path resolves to the same blob as parent; Eprime e5da59b7e570a360f99ee07e2194c938da0c2626 already has all15 complete exact raw readbacks; no duplicate download.'}
 if sys.argv[1]=='--check':print(json.dumps(summary));return
 need(h(CAP.read_bytes())==CAP_SHA,'recorder pin')
 occ=helper.used();free=shutil.disk_usage(ROOT).free;memory=helper.memory_observation();need(occ+budget<=8*1024**3 and free>budget,'fresh actual-mount full publication admission');need(min(memory['host_available_bytes'],memory['cgroup_available_estimate'])>working,'fresh memory estimate')
 out=ROOT/'git-publication';out.mkdir(mode=0o700,exist_ok=False)
 (out/'EXECUTOR.py').write_bytes(P(__file__).read_bytes());(out/'MANIFEST.json').write_bytes(mraw)
 cap=loadmod('capture',CAP,CAP_SHA);env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env.update(PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_NO_LAZY_FETCH='1')
 rec=cap.Recorder(out,env,OLD);gd=out/'repo.git';result={'exit_code':1,'expected_parent':OLD,'published':False,'push_attempted':False,'delivered':False,'capacity':dict(summary,allocated_before=occ,physical_free_before=free,memory_before=memory),'verified_blobs':{},'verified_aliases':{}}
 def save():(out/'RESULT.json').write_bytes(js(result))
 def run(cmd,data=None,check=True):
  row,b,e=rec.run(cmd,cwd=ROOT,data=data,timeout=180,check=False)
  if check:need(row['actual_process_returncode']==0,'command failed; preserve/no retry: '+row['directory'])
  return row,b,e
 def git(*a,data=None):
  need(a and a[0] in {'rev-parse','cat-file','config','ls-remote','hash-object','ls-tree','mktree','commit-tree','rev-list','diff-tree','update-ref','push'},'no-fetch Git allowlist')
  return run(['git','--no-lazy-fetch','--git-dir='+str(gd),'-c','gc.auto=0','-c','maintenance.auto=false','-c','user.name=Codex','-c','user.email=codex@openai.com','-c','pack.window=0','-c','pack.threads=1',*a],data=data)[1]
 def obj(b):
  s=b.decode().strip();need(re.fullmatch('[0-9a-f]{40}',s),'full OID');return s
 def remote_ref():
  lines=git('ls-remote','--heads',REMOTE,'refs/heads/'+BRANCH).decode().splitlines();need(len(lines)==1,'one remote ref');a,b=lines[0].split('\t');need(b=='refs/heads/'+BRANCH and re.fullmatch('[0-9a-f]{40}',a),'remote ref identity');return a
 def api(path,raw=False):
  cmd=['gh','api','--hostname','github.com']
  if raw:cmd+=['-H','Accept: application/vnd.github.raw+json']
  cmd+=['repos/ZhiQiYang/geometry-axiom/'+path];b=run(cmd)[1];return b if raw else json.loads(b)
 before=None
 try:
  save();before=helper.snapshot_provider();(out/'PROVIDER_BEFORE.json').write_bytes(js(before))
  run(['git','init','--bare','--initial-branch=metadata-only',str(gd)]);(gd/'objects/info/alternates').write_text(str(PROVIDER/'objects')+'\n')
  need(obj(git('rev-parse',OLD+'^{commit}'))==OLD,'existing complete parent required; no ingestion')
  need(remote_ref()==OLD,'remote parent moved')
  pr=git('cat-file','commit',OLD);need(hashlib.sha1(b'commit '+str(len(pr)).encode()+b'\0'+pr).hexdigest()==OLD,'parent integrity')
  need('[remote ' not in (gd/'config').read_text(),'no remote config')
  cr,co,_=run(['git','--no-lazy-fetch','--git-dir='+str(gd),'config','--get-regexp',r'^remote\..*\.promisor$'],check=False);need(cr['actual_process_returncode']==1 and co==b'','no effective promisor')
  (gd/'shallow').write_text(OLD+'\n');git('update-ref','refs/heads/fixed-parent',OLD,'0'*40)
  for path,(size,sha,blob) in OLD_DOCS.items():
   b=git('cat-file','blob',OLD+':'+path);need(len(b)==size and h(b)==sha and oid(b)==blob,'exact old PROGRESS binding')
  for a in aliases:
   need(obj(git('rev-parse',OLD+':'+a['old_path']))==a['git_blob'],'parent full-readback blob reachable')
   need(git('cat-file','-s',a['git_blob']).decode().strip()==str(a['bytes']),'alias original size')
  entries={}
  for dst,b in sorted(payloads.items()):
   entries[dst]=obj(git('hash-object','-w','--no-filters','--',str(allowed[dst])));need(entries[dst]==oid(b),'new blob exact OID')
  entries.update({a['destination']:a['git_blob']for a in aliases})
  def readtree(tree):
   rows={}
   if tree:
    for row in git('ls-tree','-z',tree).split(b'\0'):
     if row:
      head,name=row.split(b'\t',1);mode,kind,sha=head.split(b' ');rows[name.decode()]=(mode,kind,sha)
   return rows
  created=set();alias_parent_trees={}
  def update(tree,changes,prefix=''):
   rows=readtree(tree);groups={}
   for path,blob in changes.items():
    name,sep,tail=path.partition('/');groups.setdefault(name,{})[tail if sep else '']=blob
   contained_aliases=[]
   for name,g in groups.items():
    old=rows.get(name);path=prefix+name
    if '' in g:
     need(len(g)==1 and path in entries,'only exact leaf')
     if path in OLD_DOCS:need(old==(b'100644',b'blob',OLD_DOCS[path][2].encode()),'only bound old document replacement')
     else:need(old is None,'new evidence path must not already exist')
     rows[name]=(b'100644',b'blob',g[''].encode())
     if path in alias_by_path:contained_aliases.append(path)
    else:
     need(old is None or old[:2]==(b'040000',b'tree'),'no tree collision');child=update(old[2].decode() if old else None,g,path+'/');rows[name]=(b'040000',b'tree',child.encode())
   raw=b''.join(mode+b' '+kind+b' '+sha+b'\t'+name.encode()+b'\0' for name,(mode,kind,sha) in rows.items());tid=obj(git('mktree','--missing','-z',data=raw));need(readtree(tid)==rows,'exact tree');created.add(tid)
   for path in contained_aliases:alias_parent_trees[path]=tid
   return tid
  tree=update(obj(git('rev-parse',OLD+'^{tree}')),entries)
  new=obj(git('commit-tree',tree,'-p',OLD,data=b'docs: publish final browser receipts and current acceptance matrix\n'));need(git('rev-list','--parents','-n','1',new).decode().strip()==new+' '+OLD,'one parent')
  diff=git('diff-tree','--no-commit-id','--no-renames','--name-status','-r','-z',OLD,new).split(b'\0');need(diff[-1]==b'','terminated diff');diff=diff[:-1]
  expected_diff={p.encode():(b'M' if p in OLD_DOCS else b'A') for p in entries};need(len(diff)==2*len(expected_diff) and dict(zip(diff[1::2],diff[0::2]))==expected_diff,'exact new evidence plus one canonical progress leaf')
  expected=(set(entries.values())-alias_oids)|created|{new};actual={x.split(b' ',1)[0].decode() for x in git('rev-list','--objects',new,'^'+OLD).splitlines()};need(actual==expected,'exact outgoing objects; alias must not be resent')
  sizes=git('cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)',data=('\n'.join(sorted(expected))+'\n').encode());metadata=0
  for line in sizes.decode().splitlines():
   sha,kind,size=line.split();need(sha in expected,'outgoing membership')
   matches=[len(payloads[p]) for p,v in entries.items() if v==sha and p in payloads]
   if matches:need(kind=='blob' and all(int(size)==n for n in matches),'outgoing blob size')
   else:need(kind in {'tree','commit'},'metadata type');metadata+=int(size)
  need(metadata<16*1024**2,'metadata bound');need(helper.snapshot_provider()==before,'provider drift')
  need((HERE/'MANIFEST.json').read_bytes()==mraw and all(allowed[k].read_bytes()==v for k,v in payloads.items()),'input drift before push');need(remote_ref()==OLD,'remote ref moved before push')
  git('update-ref','refs/heads/delivery',new,'0'*40);result.update(push_attempted=True,published=None,pending_commit=new,tree=tree,entries=entries,outgoing_objects=sorted(expected),outgoing_metadata_bytes=metadata,alias_parent_trees=alias_parent_trees);save()
  git('push','--porcelain',REMOTE,'refs/heads/delivery:refs/heads/'+BRANCH);result.update(published=True,commit=new);save();need(remote_ref()==new,'remote ref after push')
  for dst,b in sorted(payloads.items()):
   got=api('git/blobs/'+entries[dst],raw=True);need(got==b and oid(got)==entries[dst],'complete new remote bytes/hash/OID');result['verified_blobs'][dst]={'size':len(got),'sha256':h(got),'git_blob':entries[dst]}
  need(set(alias_parent_trees)==set(alias_by_path),'all15 alias parent trees bound')
  for a in aliases:
   dst=a['destination'];tid=alias_parent_trees[dst];rt=api('git/trees/'+tid)
   need(rt['sha']==tid and rt.get('truncated') is False,'complete remote alias tree')
   need(rt['tree']==[{'path':'stdout.bin','mode':'100644','type':'blob','sha':a['git_blob'],'size':a['bytes'],'url':'https://api.github.com/repos/ZhiQiYang/geometry-axiom/git/blobs/'+a['git_blob']}],'exact remote immutable alias leaf')
   need(obj(git('rev-parse',new+':'+dst))==a['git_blob'],'new full path immutable OID')
   result['verified_aliases'][dst]={'git_blob':a['git_blob'],'size':a['bytes'],'source_commit':OLD,'source_path':a['old_path'],'complete_existing_readback_commit':OLD,'new_download':False,'remote_tree':tid}
  need(remote_ref()==new and helper.snapshot_provider()==before,'final ref/provider unchanged');need((HERE/'MANIFEST.json').read_bytes()==mraw and all(allowed[k].read_bytes()==v for k,v in payloads.items()),'final input drift')
  result.update(exit_code=0,delivered=True,ordinary_fast_forward=True,no_fetch=True,force=False,changed_paths=sorted(entries))
 except BaseException as e:result['error']=repr(e);raise
 finally:
  try:
   after=helper.snapshot_provider();(out/'PROVIDER_AFTER.json').write_bytes(js(after));result['provider_unchanged']=before is not None and before==after
   if not result['provider_unchanged']:result.update(exit_code=1,delivered=False)
   result['memory_after']=helper.memory_observation()
  finally:save()
 need(result['exit_code']==0,'publication failed');print(json.dumps(result))
if __name__=='__main__':main()
