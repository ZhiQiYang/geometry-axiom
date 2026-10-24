"""Run only after root releases R7 exclusive performance; no archive body reads."""
from pathlib import Path
import datetime,hashlib,json,subprocess
O=Path('/tmp/train337-publication-peer-20261024');B=Path('/tmp/geo337-full-R5-R6-evidence-publication-20261024');MAN=Path('/tmp/geo337-full-R5-R6-publication-preparation-20261024/FILES.final.json');ROOT=Path('/workspace/geometry-axiom');F='6df0264f75e84f03adb70746b6ac3db07a9910fc';P='51e36b94b327c7bc1142c82b59e26ce9ab983d69';E='597bce63e296c85e64d33ca4496f167a599f0848';checks=0;findings=[]
def h(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(Path(p).read_bytes())
def ck(v,n):
 global checks
 checks+=1
 if not v:findings.append(n)
r=j(B/'RESULT.json');m=j(MAN);rows=j(B/'subcommands.json');outmap={}
ck(h(MAN.read_bytes())==r['manifest_sha256']=='f602cabe1d0dfe5fcf43de1d8c484c6f45a1cc047d58c0c75c33168002bea526','actual final manifest')
ck(r['tool_sha256']=='16d1b53f1ccb6a93b227fe31a2b28536287a77045107368afc1537363c266ea5','actual fixed corrected tree publisher')
ck(r['product_source']==F and r['previous_head']==P and r['evidence_head']==E and r['published'] and r['push_exit']==0 and r['product_unchanged'],'actual fixed source/parent and publication0')
for c in rows:
 d=Path(c['directory']);ck(j(d/'result.json')==c and j(d/'request.json')['command']==c['command'],'original complete request/result')
 ck(c['actual_process_returncode']==0 and not c['timeout_expired'] and c['ended_epoch']>=c['started_epoch'],'original true Git0')
 for stream in ['stdout','stderr']:
  data=(d/(stream+'.bin')).read_bytes();ck(len(data)==c[stream+'_bytes'] and h(data)==c[stream+'_sha256'],'complete original Git '+stream)
 inp=d/'stdin.bin';ck((inp.exists() and h(inp.read_bytes())==c['stdin_sha256']) or (not inp.exists() and not c['stdin_provided'] and c['stdin_sha256']==h(b'')),'original provided/inherited stdin')
 argv=c['command'][5:];out=(d/'stdout.bin').read_bytes();outmap.setdefault(tuple(argv),[]).append(out)
 ck(not any(x in argv for x in ['--force','--force-with-lease','reset','rebase','update-ref']),'no rewritten history')
files=m['files'];dest=[x['destination']for x in files];ck(len(files)==len(set(dest))==r['files']==398 and set(r['changed_paths'])==set(dest),'actual398 exact changed leaves')
ck(sum(x['bytes']for x in files)==r['logical_bytes']==77488565,'original logicalbytes')
blobs={}
for x in files:
 source=Path(x['source_path']);ck(source.is_file() and source.stat().st_size==x['bytes'],'original metadata size remains')
 if not x['destination'].endswith('.tar.gz'):ck(h(source.read_bytes())==x['sha256'],'original small metadata exact')
 if 'preloaded_blob'in x:
  blob=x['preloaded_blob'];ck(outmap.get(('cat-file','-t',blob))==[b'blob\n'] and outmap.get(('cat-file','-s',blob))==[str(x['bytes']).encode()+b'\n'],'ordinary preloaded type/size exact')
  proof=j(x['preload_receipt']);ck(h(Path(x['preload_receipt']).read_bytes())==x['preload_receipt_sha256'] and proof['exit_code']==0 and proof['object_oid']==blob and proof['archive_identity']['sha256']==x['sha256'],'original full-byte preload proof bound')
 else:
  outputs=outmap.get(('hash-object','-w','--no-filters','--',str(source)),[]);ck(len(outputs)==sum(y['source_path']==str(source) and 'preloaded_blob' not in y for y in files) and bool(outputs) and len(set(outputs))==1 and len(outputs[0].strip())==40,'one exact insertion per destination; repeated source must yield identical OID');blob=outputs[0].decode().strip()
  if not x['destination'].endswith('.tar.gz'):
   data=source.read_bytes();ck(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob,'independent small metadata Gitblob')
 blobs[x['destination']]=blob
ck(outmap.get(('merge','--ff-only',E))==[b'Updating '+P[:7].encode()+b'..'+E[:7].encode()+b'\nFast-forward\n'] or ('merge','--ff-only',E)in outmap,'normal ff actual captured')
ck(('push','origin','HEAD:refs/heads/codex/train-337-continue-20261024')in outmap,'ordinary train push captured')
remote=outmap.get(('ls-remote','--heads','origin','refs/heads/codex/train-337-continue-20261024'),[]);ck(remote and remote[-1]==(E+'\trefs/heads/codex/train-337-continue-20261024\n').encode(),'original remote evidencehead reached')
raw=O/'R5_R6_PUBLICATION_SMALL_GIT_ORIGINALS';ck(raw.is_dir(),'reuse only five already captured local Git metadata commands')
def git(n,*args):
 d=raw/n;argv=['git','-c','gc.auto=0','-c','maintenance.auto=false',*args];rec=j(d/'result.json');stdout=(d/'stdout').read_bytes();stderr=(d/'stderr').read_bytes();ck(rec['argv']==argv and rec['cwd']==str(ROOT) and rec['exit']==0 and rec['stdout_sha256']==h(stdout) and rec['stderr_sha256']==h(stderr),'reuse exact prior local metadata original '+n);return stdout

ck(git('001','show','-s','--format=%H%n%P',E)==(E+'\n'+P+'\n').encode(),'actual fixed ordinary Eparent')
ck(set(git('002','diff-tree','--no-commit-id','--name-only','-r','-z',P,E).decode().split('\0')[:-1])==set(dest),'fresh unfiltered complete changed leaves')
ck(git('003','diff','--name-only',F,E,'--','.',':(exclude)evidence')==b'','fresh actual product F unchanged')
for n,sha in [('004',E),('005',P)]:
 data=git(n,'ls-tree','-r','-z',sha,'--',*dest);entries={}
 for line in data.split(b'\0'):
  if not line:continue
  header,name=line.split(b'\t',1);mode,kind,oid=header.decode().split(' ');entries[name.decode()]=(mode,kind,oid)
 if sha==E:ck(entries=={name:('100644','blob',blob)for name,blob in blobs.items()},'all398 exact committed blob IDs/modes, no body capture')
 else:ck(set(entries)=={'evidence/geo337-train-20261024/PROGRESS.md'},'only rootprogress existed; no older evidence archive overwritten')
report={'schema':'root-full-R5-R6-and-maintenance-actual-publication-peer-v1','checks':checks,'exit_code':int(bool(findings)),'findings':findings,'product_source':F,'parent':P,'evidence_head':E,'original_result_sha256':h((B/'RESULT.json').read_bytes()),'manifest_sha256':h(MAN.read_bytes()),'original_Git_commands':len(rows),'original_readonly_Git_commands':5,'additional_Git_commands_on_corrected_review':0,'files':398,'logical_bytes':77488565,'large_archive_body_reads':0,'reviewer_initial_error':'Initial peer assumed a source file appears once in manifest; the same peer source is intentionally committed at two distinct paths. Both original hash-object commands produced the same OID. Initial failed report and helper retained; no product/publication change.','limits':['Original full Git streams plus small metadata independent blob checks and five fixed local metadata commands; no network, archive body cat-file/hash or test run.','All six original archives bound to already-reviewed exact SHA256 plus original insertion/preload Git OIDs. Permanent TMP object alternate cannot be removed merely because remote push succeeded.','Historical R5a22/R6F2bbe failures remain unchanged; current product F7 has its own formal R7 execution. No source/result relabel.']}
q=O/'ROOT_FULL_R5_R6_PUBLICATION_ACTUAL_PEER.json';q.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(q),'sha256':h(q.read_bytes()),'checks':checks,'exit_code':report['exit_code'],'findings':findings}));raise SystemExit(report['exit_code'])
