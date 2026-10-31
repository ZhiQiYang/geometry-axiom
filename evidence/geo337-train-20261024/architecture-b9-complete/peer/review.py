from pathlib import Path
import collections,hashlib,json,re
B=Path('/workspace/geo337-b9c9-architecture-four-20261024');ROOT=Path('/workspace/geometry-axiom');O=Path(__file__).parent;S='b9c9fb818f031828530994a4d66f1976da0d8138';passed=0;failed=[];groups=collections.Counter()
def ck(v,l,g='general'):
 global passed
 groups[g]+=1
 if v:passed+=1
 else:failed.append(l)
def j(p):return json.loads(p.read_bytes())
def h(b):return hashlib.sha256(b).hexdigest()
def lf(b):return b.replace(b'\r\n',b'\n')
r=j(B/'RESULT.json');receipt=j(B/'new/product-architecture-receipt.json');manifest=j(B/'new/product-architecture.json');old=j(B/'previous-artifact/product-architecture.json');scan=j(B/'new/product-architecture-scan.json');rows=j(B/'subcommands.json');inputs=j(B/'source-inputs.json');inventory=j(B/'policy-guard-inventory.json')
ck(h((B/'tools/refresh_geo337_final_architecture_20261024.py').read_bytes())=='61aa806e619baa5f0b141d2a5026fe8146691e12406b112cb4b7f765e9db37b0','exact reviewed producer');ck(h((B/'tools/capture.py').read_bytes())=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762','exact recorder')
ck(r['sourceSHA']==receipt['sourceBaseHead']==receipt['headObservedBefore']==receipt['headObservedAfter']==S,'all current execution source bindings');ck(r['sourceBeforeAfterClean']is True and r['sourceCheckoutModified']is False and r['ledgerRegenerated']is False,'no root source/ledger mutation');ck(len(rows)==48,'48 original command receipts')
for row in rows:
 d=Path(row['directory']);stored=j(d/'result.json');ck(row==stored,'index/result exact '+d.name,'commands');ck(row['source_sha']==row['acceptance_sha']==S and row['cwd']==str(ROOT),'source/cwd exact '+d.name,'commands');ck(type(row['actual_process_returncode'])is int and not row['timeout_expired'],'true OS terminal '+d.name,'commands')
 for stream in ['stdout','stderr']:
  raw=(d/(stream+'.bin')).read_bytes();ck(len(raw)==row[stream+'_bytes'] and h(raw)==row[stream+'_sha256'],'full stream '+d.name+'/'+stream,'commands')
 ck(h((d/'stdin.bin').read_bytes())==row['stdin_sha256'],'full stdin '+d.name,'commands')
ck(sum(x['actual_process_returncode']==1 for x in rows)==9 and sum(x['actual_process_returncode']==0 for x in rows)==39,'only9 intended negative commands')
heads=[x for x in rows if x['command']==['git','rev-parse','HEAD']];statuses=[x for x in rows if x['command']==['git','status','--porcelain=v1','--untracked-files=all']];ck(len(heads)==len(statuses)==2,'two full head/status guards')
for x in heads:ck((Path(x['directory'])/'stdout.bin').read_bytes()==(S+'\n').encode(),'recorded HEAD exact')
for x in statuses:ck((Path(x['directory'])/'stdout.bin').read_bytes()==b'' and x['actual_process_returncode']==0,'recorded source clean')
for name,pin in r['outputs'].items():
 raw=(B/'new'/name).read_bytes();ck(len(raw)==pin['bytes'] and h(raw)==pin['rawSha256'] and h(lf(raw))==pin['lfSha256'],'new artifact hash '+name)
ck((B/'new/product-architecture.json').read_bytes()==(B/'execution-source-originals/product-architecture.json').read_bytes(),'fresh manifest is exact current execution937')
for name,field in [('product-architecture.json','manifestSha256'),('product-architecture-scan.json','scanSha256'),('PRODUCT-ARCHITECTURE.md','reportSha256')]:ck(h(lf((B/'new'/name).read_bytes()))==receipt[field],'receipt references '+name)
for sourcekey,dirname in [('previousOutputs','previous-artifact'),('executionSourceOutputs','execution-source-originals')]:
 for name,pin in receipt['manifestRefresh'][sourcekey].items():
  raw=(B/dirname/name).read_bytes();ck(len(raw)==pin['bytes'] and h(raw)==pin['rawSha256'] and h(lf(raw))==pin['lfSha256'],sourcekey+' '+name)
added={x['identifier'] for x in inventory['addedIdentifiers']};ck(len(added)==9 and len(old['policy']['forbiddenIdentifiers'])==928 and len(manifest['policy']['forbiddenIdentifiers'])==937,'distinct928historical/937current counts');ck(set(manifest['policy']['forbiddenIdentifiers'])-set(old['policy']['forbiddenIdentifiers'])==added and not set(old['policy']['forbiddenIdentifiers'])-set(manifest['policy']['forbiddenIdentifiers']),'exact9 additive guards')
copy=json.loads(json.dumps(manifest));copy['policy']['forbiddenIdentifiers']=old['policy']['forbiddenIdentifiers'];ck(copy==old,'all other policy/classification/trust/exclusion unchanged');ck(len(manifest['policy']['forbiddenStrings'])==55,'55string guards kept');ck((B/'withdrawn-manifest.json').read_bytes()==(B/'previous-artifact/product-architecture.json').read_bytes(),'withdrawn exact original928')
for item in inventory['addedIdentifiers']:
 for origin in item['origins']:
  line=(ROOT/origin['path']).read_text(encoding='utf-8-sig').splitlines()[origin['line']-1];ck(re.search(r'\b'+re.escape(item['identifier'])+r'\b',line) is not None,'actual W identifier origin '+str(origin),'origins')
ls=[x for x in rows if x['command'][:4]==['git','ls-tree','-r','-z']];ck(len(ls)==1,'one exact tree snapshot');tree={}
for record in (Path(ls[0]['directory'])/'stdout.bin').read_bytes().split(b'\0'):
 if record:
  meta,name=record.split(b'\t',1);mode,kind,oid=meta.split();tree[name.decode()]=(mode,kind,oid.decode())
declared=sorted(x['path'] for k in ['sources','exclusions'] for x in manifest[k]);ck(len(inputs)==len(declared)==len(set(declared))==604,'complete604');ck([x['path']for x in inputs]==declared,'sorted exact input paths')
for x in inputs:
 p=ROOT/x['path'];raw=p.read_bytes();oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();mode,kind,t_oid=tree[x['path']];ck(kind==b'blob' and mode!=b'120000' and oid==t_oid==x['gitBlobOid'],'actual Git blob '+x['path'],'inputs');ck(len(raw)==x['bytes'] and h(raw)==x['rawSha256'] and h(lf(raw))==x['lfSha256'],'actual raw/LF '+x['path'],'inputs')
compact=[{'path':x['path'],'sha256':x['lfSha256']}for x in inputs];closure=h(json.dumps(compact,ensure_ascii=False,separators=(',',':')).encode());ck(compact==receipt['inputs'] and closure==r['inputClosureSHA256']==receipt['inputClosureSha256']=='2373af45191d585e9f5b1652935e7802a9d154075d7d2de07a8ede37baa91773','exact closure serialization')
cv=receipt['completeInventoryVerification'];ck(cv['filesBefore']==cv['filesAfter']==604 and cv['inputClosureSha256Before']==cv['inputClosureSha256After']==closure and cv['toolHashesBefore']==cv['toolHashesAfter'] and cv['protectedSsotBefore']==cv['protectedSsotAfter'],'before/after inventory judges SSOT equal')
for n,pin in cv['toolHashesBefore'].items():ck(h(lf((ROOT/n).read_bytes()))==pin,'actual judge '+n)
for n,pin in cv['protectedSsotBefore'].items():
 raw=(ROOT/n).read_bytes();ck(len(raw)==pin['bytes'] and h(raw)==pin['rawSha256'] and h(lf(raw))==pin['lfSha256'],'actual SSOT '+n)
gates=[receipt['actualCliScan'],*receipt['validation']];ck([x['actual_process_returncode']for x in gates]==r['originalGateExits']==[0,0,0],'three original gates0')
for x in gates:
 original=next(y for y in rows if y['directory']==x['directory']);ck(all(x[k]==v for k,v in original.items()),'gate references true command');ck(x['source_sha']==S,'gate current SHA')
ck((Path(gates[0]['directory'])/'stdout.bin').read_bytes()==(B/'new/product-architecture-scan.json').read_bytes(),'new scan is real sameSHA CLI stdout, not reusedold')
for x,n in zip(gates[1:],[205,18]):
 raw=(Path(x['directory'])/'stderr.bin').read_text();ck(re.search(r'^Ran '+str(n)+r' tests in [0-9.]+s$',raw,re.M)is not None and raw.rstrip().endswith('OK') and 'skipped='not in raw,'exact native-free unittest count '+str(n))
ck(scan['ok']is True and scan['diagnostics']==[] and len(scan['edges'])==798,'scan798/0 actual')
for ident in sorted(added):
 proofs=[x for x in receipt['manifestRefresh']['manifestProof']if x['identifier']==ident];ck([x['phase']for x in proofs]==['fixed','withdrawn','restored'] and [x['exit']for x in proofs]==[0,1,0],'three same-source probes '+ident)
 for p in proofs:
  row=next(x for x in rows if x['directory']==p['directory']);out=(Path(p['directory'])/'stdout.bin').read_bytes();err=(Path(p['directory'])/'stderr.bin').read_bytes();obj=json.loads(out);ck(row['actual_process_returncode']==p['exit'] and row['command'][-2:]==[ident,'protected'],'actual probe exit/argv '+ident,'proofs');ck(obj['identifier']==ident,'actual probe identifier '+ident,'proofs')
  if p['phase']=='withdrawn':ck(obj['diagnostics']==[] and ('AssertionError: new W identifier must be rejected from K: '+ident).encode()in err,'exact intended withdrawal assertion '+ident,'proofs')
  else:ck(len(obj['diagnostics'])==1 and obj['diagnostics'][0]['code']=='FORBIDDEN_IDENTIFIER' and obj['diagnostics'][0]['path']=='geometry-core/kernel/geometry.c' and ident in obj['diagnostics'][0]['message'] and err==b'','fixed/restored exact rejection '+ident,'proofs')
neutral=[x for x in rows if x['command'][-1:] ==['neutral']];ck(len(neutral)==2 and all(x['actual_process_returncode']==0 and json.loads((Path(x['directory'])/'stdout.bin').read_bytes())['diagnostics']==[]for x in neutral),'two neutral controls0')
reporttext=(B/'new/PRODUCT-ARCHITECTURE.md').read_text();ck(S in reporttext and closure in reporttext and '205' in reporttext and '18' in reporttext and '928→937' in reporttext,'report current exact source/counts');ck(receipt['manifestRefresh']['previousArtifactCommit']=='38da31bcac91db631e6325e40b228f8604810e82' and receipt['manifestRefresh']['previousSource']!='b9c9fb818f031828530994a4d66f1976da0d8138','old artifact and source remain historical')
report={'scope':'Independent original raw command and four-artifact current-source audit; no rerun or root edit','source_sha':S,'result_sha256':h((B/'RESULT.json').read_bytes()),'passed':passed,'failed':len(failed),'exit':0 if not failed else 1,'checks_by_group':dict(groups),'failures':failed,'original_commands':48,'input_files':604,'original_gates':[0,0,0],'generic_tests':205,'product_tests':18,'same_source_guard_triples':9,'neutral_controls':2,'limits':['No native/browser/ledger/performance execution certified.','Old artifact928 and current execution937 explicitly separated; same bytes scan is accepted only because current raw CLI stdout is preserved.','604 actual file/Git raw/LF equality checked from retained ls-tree and current source bytes; producer before/after guards retained.'],'outputs':r['outputs']};(O/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['passed','failed','exit']}));print(h((O/'REVIEW.json').read_bytes()));raise SystemExit(report['exit'])
