"""Read verified saved space faces for an explicit D38 value copy."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'geometry-core'))
from modeling import ModelError, verify_package
from modeling.base import load_base


def saved_hosts(package):
    rebuilt = verify_package(package)
    request = rebuilt['request']
    if request['role'] != 'enclosure' or request['target'] != 'surface-set':
        raise ModelError('INVALID', 'SECTION_HOST', 'D38', '請選取已建立空間的邊界面。')
    definitions = rebuilt['definitions']
    roots = {(root['kind'], root['id']) for root in request['roots']}
    spaces = [extension for extension in definitions['extensions']
              if (extension.get('kind'), extension.get('id')) in roots
              and extension.get('kind') == 'composite_space']
    shell_ids = {space['shell_id'] for space in spaces}
    uses = {use['placement_id'] for extension in definitions['extensions']
            if extension.get('kind') == 'shell' and extension['id'] in shell_ids
            for use in extension['uses'] if use['purpose'] == 'boundary'}
    base = load_base(definitions['base_scene'])

    def axis(vector):
        for i, value in enumerate(vector):
            if value:
                return ('+' if value > 0 else '-') + 'XYZ'[i]
        raise ModelError('INVALID', 'SECTION_HOST', 'I48', '保存面的框架不完整。')

    hosts = []
    for placement in base['placements']:
        if placement['id'] not in uses:
            continue
        u, v = placement['u'], placement['v']
        n = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        hosts.append({'placementId': placement['id'],
                      'frame': {'origin': placement['origin'], 'U': axis(u), 'V': axis(v), 'N': axis(n)},
                      'region': {'outline': placement['outline'], 'holes': placement['holes']}})
    return {'ok': True, 'hosts': hosts}
