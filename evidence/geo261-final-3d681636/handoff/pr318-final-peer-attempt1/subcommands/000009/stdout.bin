"""Small independent constructor/checker witness for source withdrawal proof."""
import argparse
import importlib.util
from pathlib import Path


def run(source, control):
    spec = importlib.util.spec_from_file_location('reading_a_control_oracle', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    region = module.Region([(0, 0), (500, 0), (500, 13), (1000, 13),
                            (1000, 1000), (0, 1000)], [])
    own = dict(id=1, kind='boundary', outer=True, edge=[0, 500], rect=(0, 0, 500, 27))
    other = dict(id=2, kind='boundary', outer=True, edge=[500, 1000], rect=(500, 13, 1000, 40))
    check = module._reading_a_build_end if control == 'builder' else module.reading_a_end_admission
    assert check(region, own, [own, other], 0, 500) == module.READING_A_PARTIAL, 'READING_A_' + control.upper() + '_PARTIAL'
    print('READING_A_' + control.upper() + '_PARTIAL: PASS')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--control', choices=('builder', 'checker'), required=True)
    args = parser.parse_args()
    run(args.source, args.control)
