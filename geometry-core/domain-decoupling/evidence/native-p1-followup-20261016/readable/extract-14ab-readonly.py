"""Extract an already recorded actual dump, without executing product code."""
import ast
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
receipt = root / 'native-candidate-14ab395d-v1'
source = receipt / 'test-result.json'
result = json.loads(source.read_bytes())
failures = result['failure_details']
matches = [item for item in failures if item['test'].endswith('.test_reset_and_default_replace_complete_world_and_keep_old_history_policy')]
assert len(matches) == 1
failure = matches[0]
prefix = "'surface' not found in "
assert failure['message'].startswith(prefix)
actual = ast.literal_eval(failure['message'][len(prefix):])
assert isinstance(actual, str) and actual.startswith('boundary 1 outline ')
out = root / '14ab-readonly-diagnostics'
out.mkdir(exist_ok=False)
dump_path = out / 'default-scene.actual-dump.txt'
dump_path.write_bytes(actual.encode('utf-8'))
provenance = {
    'kind': 'extraction-from-original-unittest-assertion-not-new-execution',
    'source': '14ab395d56ce1dcabe43e65b5311776a8d3e6221',
    'original_result': str(source),
    'original_result_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'original_failure': failure,
    'dump_sha256': hashlib.sha256(dump_path.read_bytes()).hexdigest(),
    'dump_bytes': dump_path.stat().st_size,
    'dump_newline_count': actual.count('\n'),
    'new_product_executions': 0,
    'original_result_unchanged': True,
}
(out / 'default-scene.provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in provenance.items() if key != 'original_failure'}, ensure_ascii=False, indent=2))
