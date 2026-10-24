#!/usr/bin/env python3
"""Independent lexical proposal and recorded static-probe review; no subject rerun."""
import collections,copy,hashlib,importlib.util,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
R=Path('/workspace/geometry-axiom');B=Path('/workspace/geo337-U-architecture-policy-preparation-20261024');O=Path('/workspace/geo337-U-architecture-policy-proof-20261024');P=Path('/workspace/train337-canvas-peer-resume');U='ca7838e0f4950452b9befcf40899d606db9b81fa'
checks=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(p):return json.loads(p.read_text())
def need(v,n):checks.append({'check':n,'passed':bool(v)})
proposal=j(B/'PROPOSAL.json');result=j(O/'RESULT.json');old=j(O/'withdrawn-old-manifest.json');new=j(O/'candidate-manifest.json')
need(proposal['source']==result['product_source']==U,'true product U')
need(proposal['physical_head']==result['execution_head']=='4d0ef8dee14873256efae1ee646c01d8dcfe947f','true physical E4d not relabelled U')
need(h(O/'withdrawn-old-manifest.json')==result['old_manifest_sha256']=='80f44b8c870e097413e395d30ba029199ba66b7302985c0f325d4f446d0ce525','exact old manifest')
need(h(O/'candidate-manifest.json')==result['candidate_manifest_sha256']=='81882184010b5ddb9aa8e8d45467be788a65a79b378037ba6c99268f99bfa975','exact candidate manifest')
need(len(old['policy']['forbiddenIdentifiers'])==928 and len(new['policy']['forbiddenIdentifiers'])==937,'928 to937 identifiers')
remaining=copy.deepcopy(new);remaining['policy']['forbiddenIdentifiers']=old['policy']['forbiddenIdentifiers'];need(remaining==old,'all other manifest fields exactly unchanged')
need(old['policy']['forbiddenStrings']==new['policy']['forbiddenStrings'] and len(new['policy']['forbiddenStrings'])==55,'all55 strings unchanged')
need(set(old['policy']['forbiddenIdentifiers'])<set(new['policy']['forbiddenIdentifiers']),'strict strengthening no removed prior guards')
scanner=R/'tests/architecture_contract.py';need(h(scanner)==proposal['scanner_sha256']=='bbd54265d0df88497228e1c362c904a495ed7ea986a3568adbeeb753e19d8f5e','original scanner exact')
spec=importlib.util.spec_from_file_location('peer_original_architecture_lexer',scanner);mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
entries=[x for x in old['sources'] if x['layer']=='W' and x['language']=='c'];need(len(entries)==len(proposal['inputs'])==60,'all60 registered W C inputs')
need({x['path'] for x in entries}=={x['path'] for x in proposal['inputs']},'whole W inventory none hand-picked')
pins={x['path']:x['sha256'] for x in proposal['inputs']};ids=collections.defaultdict(set);strings=set()
for entry in entries:
 path=entry['path'];raw=(R/path).read_bytes();need(hashlib.sha256(raw).hexdigest()==pins[path],'unchanged source '+path)
 _,_,tokens=mod.lex(raw.decode('utf-8-sig'),path,c=True)
 for token in tokens:
  if token.kind=='identifier' and token.value.startswith(('Wood','WOOD_','wood_')):ids[token.value].add((path,token.line))
 k=0
 while k<len(tokens):
  if tokens[k].kind=='string':
   value=tokens[k].value;k+=1
   while k<len(tokens) and tokens[k].kind=='string':value+=tokens[k].value;k+=1
   if re.match(r'^(?:wood|woodworking)[./-]',value):strings.add(value)
  else:k+=1
added=sorted(set(ids)-set(old['policy']['forbiddenIdentifiers']));names=[x['identifier'] for x in proposal['added_identifiers']]
need(added==names and len(names)==9,'nine exact independent lexical additions')
need(new['policy']['forbiddenIdentifiers']==sorted(set(old['policy']['forbiddenIdentifiers'])|set(ids)),'complete old plus current W union')
need(not(strings-set(old['policy']['forbiddenStrings'])) and proposal['added_strings']==[],'independent no new strings')
for x in proposal['added_identifiers']:
 need({(z['path'],z['line']) for z in x['origins']}==ids[x['identifier']],'full lexical origins '+x['identifier'])
 need(all(p.startswith('geometry-templates/woodworking/native/') for p,line in ids[x['identifier']]),'W native origins only '+x['identifier'])
doc=(R/'geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md').read_text();need('完整 W C 詞彙盤點保留全部舊 guard' in doc and 'guard增量由全部真W-native原lexer集合與舊集合的union實證' in doc,'documented union rule no new numerical threshold or SSOT decision')
rows=j(O/'subcommands.json');dirs={x['directory']:x for x in rows}
need(len(result['proof'])==27,'nine actual triples27 original commands')
for row in rows:
 p=Path(row['directory']);need(j(p/'result.json')==row,'original capture row '+p.name)
 need(type(row['actual_process_returncode']) is int and not row['timeout_expired'],'original terminal '+p.name)
 for stream in ['stdout','stderr']:
  raw=(p/(stream+'.bin')).read_bytes();need(len(raw)==row[stream+'_bytes'] and hashlib.sha256(raw).hexdigest()==row[stream+'_sha256'],'full '+stream+' '+p.name)
for name in names:
 triple=[x for x in result['proof'] if x['identifier']==name];need([x['phase'] for x in triple]==['fixed','withdrawn','restored'] and [x['exit'] for x in triple]==[0,1,0],'actual0/1/0 '+name)
 for x in triple:
  row=dirs[x['directory']];p=Path(x['directory']);stdout=(p/'stdout.bin').read_bytes();stderr=(p/'stderr.bin').read_bytes();data=json.loads(stdout)
  need(row['actual_process_returncode']==x['exit'] and row['acceptance_sha']==U,'actual process/source '+name+' '+x['phase'])
  need(data['identifier']==name,'exact identifier probe '+name+' '+x['phase'])
  if x['phase']=='withdrawn':need(data['diagnostics']==[] and b'AssertionError: new W identifier must be rejected from K:' in stderr,'old policy misses specific guard '+name)
  else:need(len(data['diagnostics'])==1 and data['diagnostics'][0]['code']=='FORBIDDEN_IDENTIFIER' and name in data['diagnostics'][0]['message'] and not stderr,'new policy exact rejection '+name+' '+x['phase'])
neutrals=[x for x in rows if 'geo261_architecture_neutral_probe' in x['command']];need(len(neutrals)==2 and all(x['actual_process_returncode']==0 and json.loads((Path(x['directory'])/'stdout.bin').read_bytes())['diagnostics']==[] for x in neutrals),'old/new neutral identifiers actually accepted')
formal=[x for x in rows if 'tests/architecture_contract.py' in x['command']];need(len(formal)==1 and formal[0]['actual_process_returncode']==0,'original scanner full candidate exit0')
fdata=json.loads((Path(formal[0]['directory'])/'stdout.bin').read_bytes());need(fdata['ok'] is True and not fdata['diagnostics'],'full scanner no diagnostics')
need(result['source_unchanged'] and result['final_four_artifacts_regenerated'] is False and result['published'] is False,'limited external policy experiment no final receipts claimed')
need(h(R/'geometry-core/domain-decoupling/product-architecture.json')==result['old_manifest_sha256'],'live original manifest not rewritten by proof')
failed=[x['check'] for x in checks if not x['passed']];o=P/'U_ARCHITECTURE_POLICY_PROPOSAL_AND_ACTUAL_PEER.json';o.write_text(json.dumps({'scope':'Whole W lexical proposal and original recorded27 guards+2 neutral+full scanner; no final receipt regeneration','checks':len(checks),'exit_code':int(bool(failed)),'findings':failed,'proposal_sha256':h(B/'PROPOSAL.json'),'proof_tool_sha256':h(Path('/workspace/prove_geo337_architecture_policy_delta_20261024.py')),'result_sha256':h(O/'RESULT.json'),'candidate_manifest_sha256':result['candidate_manifest_sha256'],'added_identifiers':names,'original_command_count':len(rows),'limits':['Original lexer invoked independently only; no C compile, formal test rerun, root source edit or branch mutation.','Nine guarded concrete W identifiers are mechanical union strengthening; no axiom semantics or locked decision changed.','Four architecture artifacts still require final-source regeneration and all three original judges.','Source-changing343 next merge must refresh its own source closure; do not reuse U physical execution identity.'],'check_details':checks},ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(o),'sha256':h(o),'checks':len(checks),'exit_code':int(bool(failed)),'findings':failed}));raise SystemExit(bool(failed))
