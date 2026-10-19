import difflib
import hashlib
import importlib.util
import io
import json
import re
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

root = Path('/workspace/geometry-axiom')
out = Path('/tmp/geometry-198-review/reader-diagnostic')
out.mkdir(parents=True, exist_ok=True)
base = '635dd86ee368579aec444fb3ba16e48bccf4877e'
sys.path.insert(0, str(root/'geometry-guide'))
spec = importlib.util.spec_from_file_location('reader_sync', root/'geometry-guide/sync_axiom_reader.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
canonical = reader.CANONICAL.read_bytes()
template = canonical.decode()
axiom = reader.AXIOM.read_text()
plain = reader.PLAIN.read_text()
current = reader.rebuild(template, axiom, plain)
report = reader.validate(current, axiom, plain)
again = reader.rebuild(current, axiom, plain)

def traces(html):
    import re
    return re.findall(r'<details class="trace-section">.*?</details>', html, re.S)

with tempfile.TemporaryDirectory(prefix='geo198-parent-trace-') as temp:
    fixture = Path(temp)
    names = subprocess.check_output(['git','ls-tree','--name-only',base],cwd=root,text=True).splitlines()
    paths = ['current_geometry.c','tests/mutate.py'] + [p for p in names if p.endswith('.scene')]
    data = subprocess.check_output(['git','archive','--format=tar',base,*paths],cwd=root)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(fixture,filter='data')
    reader.axiom_matrix.ROOT = str(fixture)
    reader.axiom_matrix.SRC = str(fixture/'current_geometry.c')
    reader.axiom_matrix.MUTATE = str(fixture/'tests/mutate.py')
    parent = reader.rebuild(template,axiom,plain)

old = json.loads(reader.script_text(template,'axiom-review-data'))
new = json.loads(reader.script_text(current,'axiom-review-data'))
preserved = ['documentId','baseDocumentHash','comments','proposals','revisions','draft']
diff = '\n'.join(difflib.unified_diff(traces(parent),traces(current),fromfile='parent-trace-sections',tofile='head-trace-sections',lineterm=''))+'\n'
(out/'parent-vs-head-trace.diff').write_text(diff)
result = {
    'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
    'base':base,'scope':'in-memory rebuild diagnostic, canonical file unchanged; no second reader artifact',
    'canonical_sha256':hashlib.sha256(canonical).hexdigest(),
    'current_rebuild_sha256':hashlib.sha256(current.encode()).hexdigest(),
    'parent_rebuild_sha256':hashlib.sha256(parent.encode()).hexdigest(),
    'canonical_chars':len(template),'parent_rebuild_chars':len(parent),'current_rebuild_chars':len(current),
    'current_minus_parent_chars':len(current)-len(parent),
    'current_rebuild_idempotent':current==again,
    'review_identity_preserved':{k:old[k]==new[k] for k in preserved},
    'validate_rebuilt_in_memory':report,
    'changed_trace_section_indices':[i for i,(a,b) in enumerate(zip(traces(parent),traces(current))) if a!=b],
    'changed_trace_clauses':[old['clauses'][i]['id'] for i,(a,b) in enumerate(zip(traces(parent),traces(current))) if a!=b],
    'non_trace_content_equal_parent':re.sub(r'<details class="trace-section">.*?</details>','',parent,flags=re.S)==re.sub(r'<details class="trace-section">.*?</details>','',current,flags=re.S),
    'canonical_bytes_unchanged':reader.CANONICAL.read_bytes()==canonical,
}
(out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
