import json,sys
from pathlib import Path
from tests.architecture_contract import ContractError,Scanner,load_manifest
root=Path(sys.argv[1]);manifest=load_manifest(Path(sys.argv[2]));name=sys.argv[3];protected=sys.argv[4]=='protected'
path='geometry-core/kernel/geometry.c';text=(root/path).read_text(encoding='utf-8')+'\nint '+name+';\n'
scanner=Scanner(root,manifest);diagnostics=[]
try:scanner.validate_manifest();scanner.scan_c(path,text)
except ContractError as error:diagnostics=[error.diagnostic.__dict__]
print(json.dumps({'identifier':name,'diagnostics':diagnostics},ensure_ascii=False),flush=True)
if protected:
 assert len(diagnostics)==1, 'new W identifier must be rejected from K: '+name
 assert diagnostics[0]['code']=='FORBIDDEN_IDENTIFIER' and diagnostics[0]['path']==path and name in diagnostics[0]['message'],diagnostics
else:assert diagnostics==[],diagnostics
