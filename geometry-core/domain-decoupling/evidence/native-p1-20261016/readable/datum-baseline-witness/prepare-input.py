import ast
import hashlib
import json
from pathlib import Path
import subprocess

source = 'db65132a41c4b4c815b6814784651e3980bf4f63'
path = 'tests/test_geo261_native_datums.py'
raw = subprocess.check_output(['git', '-C', 'D:/geometry-axiom', 'show', source + ':' + path])
tree = ast.parse(raw.decode('utf-8'))
scene = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'SCENE' for target in node.targets))
method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == 'test_malformed_suffix_keeps_earlier_missing_parameter_diagnostic')
expressions = next(ast.literal_eval(node.iter) for node in ast.walk(method) if isinstance(node, ast.For) and isinstance(node.target, ast.Name) and node.target.id == 'expression')
out = Path(__file__).resolve().parent / 'input.json'
if out.exists():
    raise RuntimeError('Preserve existing input recipe')
out.write_text(json.dumps({'testSource': source, 'testPath': path, 'testSourceSha256': hashlib.sha256(raw).hexdigest(), 'scene': scene, 'expressions': expressions}, indent=2) + '\n', encoding='utf-8')
print(hashlib.sha256(out.read_bytes()).hexdigest())
