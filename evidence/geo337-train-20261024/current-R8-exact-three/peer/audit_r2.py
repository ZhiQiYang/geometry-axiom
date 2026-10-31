from pathlib import Path
import hashlib,json,gzip,re,subprocess,datetime
P=Path('/tmp/geo337-r8-exact-three-triage-20261025');O=Path('/tmp/geo337-r8-exact-three-triage-peer-20261025')
R=Path('/workspace/geometry-axiom');F='75a1e93811a52b69385cbdaf6a09d773ed9052ad';BASE='b74f9a2ae7ade1555b9be45283adecc097fb76e3';INTRO='6366304eb787b2a50282e4132f45e51eb7d21290';PARENT='4b665fae21ab63aaffb7d84f6a32d5a469ba1675';OLD='1ee76768b1a8123d04083eac4710603f43aaeb84'
checks=0;findings=[];reads=[]
def h(x):return hashlib.sha256(x).hexdigest()
def j(p):return json.loads(Path(p).read_bytes())
def ck(v,label):
 global checks
 checks+=1
 if not v:findings.append(label)
def git(*args):
 d=O/'independent-git-r2'/f'{len(reads)+1:03d}';d.mkdir(parents=True)
 cmd=['git','-c','gc.auto=0','-c','maintenance.auto=false',*args];r=subprocess.run(cmd,cwd=R,capture_output=True)
 (d/'stdout.bin').write_bytes(r.stdout);(d/'stderr.bin').write_bytes(r.stderr)
 row=dict(argv=cmd,cwd=str(R),exit=r.returncode,stdout_sha256=h(r.stdout),stderr_sha256=h(r.stderr))
 (d/'result.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');reads.append(row);ck(r.returncode==0,'immutable Git read '+str(args));return r.stdout
facts=j(P/'FACTS.json'); inv=j(P/'FINAL_INVENTORY.json')
ck(h((P/'FACTS.json').read_bytes())=='bbb66b1f5f19ede946a10ce40987569cda71c75578e597e7557fd5d0b5b00849','unchanged original facts pin')
ck(h((P/'REPORT.md').read_bytes())=='337c42769598af8c4ca46bf440970e0e3e0fbf767367e773730beca46823b7de','reviewed corrected report pin')
ck(h((P/'FINAL_INVENTORY.json').read_bytes())=='140d3c1c0d24ac7f61fae9beb38c1e03edb84b22f195d99a6a92a126283b4e5b','final updated inventory pin')
ck(inv['files_count']==len(inv['files'])==150,'exact150 inventory')
actual={x.relative_to(P).as_posix() for x in P.rglob('*') if x.is_file()};ck(actual=={x['path'] for x in inv['files']}|{'FINAL_INVENTORY.json'},'inventory includes all source artifacts except itself')
for row in inv['files']:
 p=P/row['path'];b=p.read_bytes();ck(not p.is_symlink() and len(b)==row['bytes'] and h(b)==row['sha256'],'inventory leaf '+row['path'])
for row in j(P/'git-originals/subcommands.json'):
 d=Path(row['directory']);ck(j(d/'result.json')==row and row['actual_process_returncode']==0 and not row['timeout_expired'],'original provenance exit and atomic record')
 for n in ['stdin','stdout','stderr']:
  b=(d/(n+'.bin')).read_bytes();ck(h(b)==row[n+'_sha256'],'original full Git stream '+str(d)+'/'+n)
  if n+'_bytes' in row:ck(len(b)==row[n+'_bytes'],'original Git stream size')
 ck(row['source_sha']==F and row['acceptance_sha']==F,'original read attributed to F8')
for p in sorted((P/'git-originals/files').rglob('*')):
 if not p.is_file():continue
 rev,rel=p.relative_to(P/'git-originals/files').as_posix().split('/',1)
 ck(git('show',rev+':'+rel)==p.read_bytes(),'independent immutable Git blob '+rev+':'+rel)
ck(git('rev-parse',INTRO+'^').decode().strip()==PARENT,'introducing direct parent')
git('merge-base','--is-ancestor',INTRO,F);git('merge-base','--is-ancestor',OLD,BASE)
ck(git('log','--format=%H','-S','——定位邊 e%d',F,'--','geometry-templates/woodworking/native/contacts.c').decode().splitlines()==[INTRO],'exact introduction ancestry')
scope=['geometry-templates/woodworking/native/contacts.c','geometry-templates/woodworking/native/contacts.h','geometry-templates/woodworking/native/contact_world.c','tests/run_tests.py','tests/geo261_contacts_harness.c']
ck(git('show','--format=fuller','--no-ext-diff',INTRO,'--',*scope)==(P/'INTRODUCING_COMMIT.patch').read_bytes(),'complete original explicitly scoped five-file diff bytes')
ssots={s:(P/'git-originals/files'/s/'公理層.md').read_bytes() for s in [BASE,F]}
clauses={s:b[b.index('I22 延伸段'.encode()):b.index(b'I23',b.index('I22 延伸段'.encode()))]for s,b in ssots.items()}
ck(clauses[BASE]==clauses[F] and clauses[F].decode()==facts['I22_clause'],'entire I22 raw clause equal without normalization')
needle='訊息指名料件、定位邊與超出的區間。'.encode();ck(needle in clauses[BASE] and needle in git('show',OLD+':公理層.md'),'diagnostic contract predates fixed base')
for s,span in [(BASE,facts['base_I22_lines']),(F,facts['F8_I22_lines'])]:
 lines=ssots[s].decode().splitlines(keepends=True);ck(''.join(lines[span[0]-1:span[1]])==facts['I22_clause'],'exact stated I22 line span '+s)
contacts={s:(P/'git-originals/files'/s/'geometry-templates/woodworking/native/contacts.c').read_bytes()for s in [BASE,PARENT,INTRO,F]}
ck(contacts[BASE]==contacts[PARENT] and contacts[INTRO]==contacts[F],'base-parent and introducing-current diagnostic source exact equality')
condition=b'if (has_edge && self->role != WOOD_MEMBER_ROLE_BOUNDARY &&\n        (span_lo < edge_lo || span_hi > edge_hi))'
ck(all(condition in b for b in contacts.values()),'unchanged rejecting condition all four sources')
eq=j('/tmp/g337323R8/evidence/equivalence.json');rec=j('/tmp/g337323R8/receipt.json')
ck(eq['failures']==facts['failures'] and rec['stages']['compare']['execution_exit']==facts['original_compare_exit']==1,'original exact red preserved')
ck(facts['source_sha']==F and facts['fixed_base']==BASE and facts['introduced_commit']==INTRO and facts['introduced_parent']==PARENT,'all four identity fields')
for key in ['product_changed','tests_changed','comparator_changed','bridge_or_perf_rerun','new_semantic_decision_adopted']:ck(facts[key] is False,'readonly declared scope '+key)
for case in facts['cases']:
 scene=case['scene'];original={x['version']:x for x in eq['runs'] if x['scene']==scene};parts={}
 for v,row in case['versions'].items():
  parts[v]={}
  for stream,pin in row['streams'].items():
   b=(P/pin['copy']).read_bytes();ck(b==Path(pin['original_path']).read_bytes() and len(b)==pin['bytes'] and h(b)==pin['sha256'],'full unchanged raw '+scene+'/'+v+'/'+stream);parts[v][stream]=b
  lines=parts[v]['stdout'].splitlines(keepends=True);first=json.loads(lines[0]);ck(len(lines)==2 and lines[0].decode()==row['first_stdout_line'] and first==row['first_response'] and h(lines[1])==row['dump_line_sha256'],'complete two-line stdout '+scene+'/'+v)
  raw=(P/'raw'/scene/v/'graph.bin.gz').read_bytes();ck(raw==(Path('/tmp/g337323R8/evidence/graphs')/v/(scene+'.bin.gz')).read_bytes(),'original complete compressed graph')
  graph=gzip.decompress(raw);ck(h(graph)==row['graph_sha256']==original[v]['graph_sha256'] and len(graph)==row['graph_bytes']==original[v]['graph_bytes'],'decompressed graph binding')
  ck(row['exit']==row['trace_exit']==original[v]['exit']==original[v]['trace_exit']==0 and row['guards']==original[v]['guards'],'original process exit and reported guard counts')
  ck(case['command']==original[v]['command'],'original exact command')
  parts[v]['json']=first;parts[v]['dump']=lines[1];parts[v]['graph']=graph
 a,b=parts['base'],parts['fix'];ck({k for k in a['json'] if a['json'][k]!=b['json'].get(k)}=={'error'} and a['json'].keys()==b['json'].keys(),'only error field differs '+scene)
 ck(a['dump']==b['dump'] and a['graph']==b['graph'] and case['versions']['base']['guards']==case['versions']['fix']['guards'],'dump graph and original guard records same '+scene)
 suffix=case['added_message_suffix'];ck(b['json']['error']==a['json']['error']+suffix,'exact named error suffix '+scene)
 ck(b['stderr'].count(suffix.encode())==1 and b['stderr'].replace(suffix.encode(),b'')==a['stderr'],'stderr changed only by same complete suffix '+scene)
 ck(a['json']['ok'] is False and a['json']['status']=='INVALID' and a['json']['code']=='SCENE_INVALID','same rejection result '+scene)
report=(P/'REPORT.md').read_text();questions=(P/'QUESTIONS.md').read_text()
ck('五檔' in report and '不是整個提交' in report or ('五檔' in report and '不代表整個提交' in report),'five-file selected patch scope disclosed; not entire introducing commit')
ck('目前維持 A' in report and '沒有採用 B′' in report,'corrected A status versus unadopted new policies')
ck('需先批准新的比較版本邊界' in questions and '不能由 agent 自行寫成例外' in questions and '本次未建置或採用B′' in questions,'B and C explicitly need decision')
ck('性能分母仍用原b74及adbaebf9' in questions and '不自動套用' in questions,'old performance denominator and P189 scope preserved')
ck('不把 base/fix stderr 列入這三個比較欄位' in report,'report accurately scopes actual comparator omission of stderr across versions')
# The incompatibility is direct: preserving the complete old stdout makes the current required error tokens absent.
tests=(P/'git-originals/files'/F/'tests/run_tests.py').read_text()
for fragment in ['定位邊 e3 [3000,4800] mm','低端超出 [27,3000] mm','定位邊 e1 [0,1800] mm','高端超出 [1800,4773] mm']:
 ck(fragment in tests,'current explicit diagnostic test requires '+fragment)
 ck(all(fragment not in c['versions']['base']['first_response']['error'] for c in facts['cases']),'old exact stdout cannot supply required token '+fragment)
result=dict(schema='geo337-r8-three-exact-triage-independent-peer/1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='/root/r8_terminal_peer',checks=checks,exit=int(bool(findings)),findings=findings,source_sha=F,fixed_base=BASE,introduced_commit=INTRO,introduced_parent=PARENT,files=150,original_compare_exit=1,new_policy_accepted=False,report_sha256=h((P/'REPORT.md').read_bytes()),facts_sha256=h((P/'FACTS.json').read_bytes()),final_inventory_sha256=h((P/'FINAL_INVENTORY.json').read_bytes()),questions_sha256=h((P/'QUESTIONS.md').read_bytes()),independent_git_reads=len(reads),limits=['Read-only evidence and contract review; no C, mutation, performance or P189 execution.','Per-scene guard values verified against original equivalence report, not independently reconstructed from unavailable historical guard file payloads.','No lawful product-only repair identified under unchanged full old-base bytes plus explicit current diagnostic assertions; this is scoped to current documented contracts, not a proof about every conceivable future design.','Initial report ambiguity between maintained option A and unadopted B/C corrected before final review; source facts and original collector receipts unchanged.','Initial factual finding: stored introducing patch was five explicitly selected files, not whole commit. Owner corrected report scope only; original failed REVIEW.json/audit.py/Git reads retained, original collector/patch/facts unchanged.'])
(O/'REVIEW_FINAL.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checks':checks,'exit':result['exit'],'findings':findings,'sha256':h((O/'REVIEW_FINAL.json').read_bytes())}));raise SystemExit(result['exit'])
