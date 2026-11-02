from pathlib import Path
import collections,hashlib,importlib.util,json,re,subprocess,sys
R=Path('/workspace/geometry-axiom');O=Path('/workspace/geo337-U-architecture-policy-preparation-20261024');O.mkdir()
def digest(b):return hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R)
head=git('rev-parse','HEAD').decode().strip();U='ca7838e0f4950452b9befcf40899d606db9b81fa';assert not git('diff','--name-only',U,head,'--','.',':(exclude)evidence')
p=R/'tests/architecture_contract.py';spec=importlib.util.spec_from_file_location('architecture_policy_original',p);mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
manifest=json.loads((R/'geometry-core/domain-decoupling/product-architecture.json').read_text());ids=collections.defaultdict(set);strings=collections.defaultdict(set);inputs=[]
for item in manifest['sources']:
 if item['layer']!='W' or item['language']!='c':continue
 path=item['path'];raw=(R/path).read_bytes();assert raw==git('show',U+':'+path);inputs.append({'path':path,'sha256':digest(raw)})
 _,_,tokens=mod.lex(raw.decode('utf-8-sig'),path,c=True)
 for token in tokens:
  if token.kind=='identifier' and token.value.startswith(('Wood','WOOD_','wood_')):ids[token.value].add((path,token.line))
 i=0
 while i<len(tokens):
  if tokens[i].kind=='string':
   line,value=tokens[i].line,tokens[i].value;i+=1
   while i<len(tokens) and tokens[i].kind=='string':value+=tokens[i].value;i+=1
   if re.match(r'^(?:wood|woodworking)[./-]',value):strings[value].add((path,line))
  else:i+=1
oldids=set(manifest['policy']['forbiddenIdentifiers']);oldstrings=set(manifest['policy']['forbiddenStrings'])
def origins(d,k):return [{'path':p,'line':n} for p,n in sorted(d[k])]
report={'source':U,'physical_head':head,'scope':'Read-only full original W C lexer inventory; no manifest edits, runtime tests or new architecture gate claimed','scanner_sha256':digest(p.read_bytes()),'inputs':inputs,'old_identifier_count':len(oldids),'old_string_count':len(oldstrings),'added_identifiers':[{'identifier':k,'origins':origins(ids,k)} for k in sorted(set(ids)-oldids)],'added_strings':[{'value':k,'origins':origins(strings,k)} for k in sorted(set(strings)-oldstrings)],'removed_identifiers':[],'removed_strings':[],'whole_union_identifier_count':len(oldids|set(ids)),'whole_union_string_count':len(oldstrings|set(strings))}
(O/'PROPOSAL.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(O/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps({k:v for k,v in report.items() if k!='inputs'},ensure_ascii=False))
