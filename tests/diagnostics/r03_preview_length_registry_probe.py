"""R2054 exact historical projection probe. NOT a timing/CI receipt.

The one new count and 12345 ms below are synthetic inputs to the set guard.
All prior declarations and costs are read through the real registry. Nothing
is written to registry, evidence or receipt files.
"""
from copy import deepcopy
from pathlib import Path
import ast
import subprocess
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
import test_unittest_runner as runner

NAME = 'node:r03_preview_length'
mode = sys.argv[1] if len(sys.argv) > 1 else 'baseline'
rows = runner.native_registry.load_registry(ROOT, allow_pending=True)
row = deepcopy(next(row for row in rows if row['name'] == NAME))
old_rows = [row for row in rows if row['name'] != NAME]
with mock.patch.object(runner.native_registry, 'load_registry', return_value=old_rows):
    costs = runner.native_shards.added_suite_costs()
assert NAME not in costs
row['expected'] = {'count': 10, 'mode': 'count', 'unit': 'node test'}
rows = [*old_rows, row]
costs = {**costs, NAME: 12345}
if mode == 'R2054_MISSING_ROW':
    rows = old_rows
elif mode == 'R2054_DUPLICATE_ROW':
    rows.append(deepcopy(row))
elif mode == 'R2054_WRONG_ORDER':
    row['order'] = 'new/node__wrong'
elif mode == 'R2054_MISSING_COST':
    del costs[NAME]
elif mode == 'R2054_UNKNOWN_NEW_AND_COST':
    name = 'node:r2054_unreviewed'
    rows.append(dict(row, name=name, order='new/node__r2054_unreviewed'))
    costs[name] = 1000
elif mode == 'R2054_DROP_PRIOR_COST':
    del costs['node:workspace_view_state']
elif mode not in ('baseline', 'base-source', 'native-program'):
    raise ValueError(mode)

with mock.patch.object(runner.native_registry, 'load_registry', return_value=rows):
    with mock.patch.object(runner.native_shards, 'added_suite_costs', return_value=costs):
        if mode == 'base-source':
            source = subprocess.check_output(['git', 'show',
                'b3c4b981bb96b118c1c05b7a1bd98062d710c8b2:tests/test_unittest_runner.py'], cwd=ROOT, text=True)
            klass = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == 'NativeShardCoverage')
            method = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == 'test_workspace_historical_budget')
            namespace = dict(vars(runner))
            exec(compile(ast.Module(body=[method], type_ignores=[]), '<base-R396>', 'exec'), namespace)
            namespace[method.name](runner.NativeShardCoverage(method.name))
        elif mode == 'native-program':
            import native_sharding_mutation_check as judge
            sys.argv = [sys.argv[0], *sys.argv[2:]]
            exec(compile(judge.PROGRAM, '<original-native-sharding-program>', 'exec'), {'__name__': '__main__'})
        else:
            runner.NativeShardCoverage('test_workspace_historical_budget').test_workspace_historical_budget()
print('R2054_REGISTRY_PROBE_PASS synthetic set inputs only; not CI acceptance')
