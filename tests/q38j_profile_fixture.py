"""Regenerate the Q38j-b native fixture with the registered fresh adapter.

GEOMETRY_MODEL_BASE=/tmp/.../model-base.exe python tests/q38j_profile_fixture.py
"""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / 'geometry-web', ROOT / 'geometry-core'):
    sys.path.insert(0, str(directory))
from start_local import ensure_stack
from tests import binaries
from tests.test_space_profile_runs import f1, saved_record
from modeling.base import load_base
from modeling import verify_package
from space_modeling import preview


def generate():
    ensure_stack()
    info = binaries.inspect_one(binaries.BY_NAME['model-base'], path=os.environ.get('GEOMETRY_MODEL_BASE'))
    if info.state != 'fresh':
        raise RuntimeError('Fresh native model-base required: ' + info.reason)
    data = f1(timber=True)
    data['base_scene'] = load_base(data['base_scene'], executable=str(info.path))['base_scene']
    result = preview(data, base_executable=str(info.path))
    for key in ('space', 'volume', 'clearance', 'walls', 'timbers', 'profile_runs'):
        if result.get(key) is not None:
            assert verify_package(result[key], base_executable=str(info.path)) == result[key], key
    record = saved_record(data, result)
    record.update(id='q38j-b-native-model', name='Q38j 原生混合空間')
    value = {'scene': data['base_scene'], 'model': record}
    target = ROOT / 'tests/fixtures/q38j-b-native-model.json'
    target.write_text(json.dumps(value, ensure_ascii=False, indent=0) + '\n', encoding='utf-8')
    print(json.dumps({'path': str(target.relative_to(ROOT)), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                      'bytes': target.stat().st_size, 'verified_packages': sum(result.get(k) is not None for k in ('space', 'volume', 'clearance', 'walls', 'timbers', 'profile_runs'))}))


if __name__ == '__main__':
    generate()
