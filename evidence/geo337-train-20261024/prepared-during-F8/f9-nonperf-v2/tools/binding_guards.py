"""Pure metadata guards only; never imports or executes repository tests."""
import ast
F8 = '75a1e93811a52b69385cbdaf6a09d773ed9052ad'
EXPECTED_EIGHT = {'py:test_geo261_source_index': {'mode': 'count', 'count': 18, 'unit': 'test'}, 'py:test_geo261_candidate_cache': {'mode': 'count', 'count': 18, 'unit': 'test'}, 'py:test_geo261_graph_product': {'mode': 'count', 'count': 5, 'unit': 'test'}, 'py:test_geo261_assembly_graph_product': {'mode': 'count', 'count': 4, 'unit': 'test'}, 'py:test_bridge_integrity': {'mode': 'count', 'count': 24, 'unit': 'test'}, 'c:integrity': {'mode': 'count', 'count': 432, 'unit': 'C 檢查點'}, 'core:run_tests': {'mode': 'count', 'count': 166, 'unit': '場景'}, 'py:test_geo261_load_residual': {'mode': 'count', 'count': 14, 'unit': 'test'}}

def need(ok, message):
    if not ok:
        raise RuntimeError(message)

def validate_counts(counts, expected):
    need(expected == EXPECTED_EIGHT, 'reviewed eight registry binding changed')
    need(all(counts.get(name) == value for name,value in expected.items()), 'original eight exact counts/units must remain681')
    need(sum(value['count'] for value in expected.values()) == 681, 'original eight exact total must remain681')
    return 681

def validate_q38_source(source):
    tree = ast.parse(source)
    nodes = [n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CASES' for t in n.targets)]
    need(len(nodes)==1 and isinstance(nodes[0],ast.List), 'original Q38 static CASES list missing')
    ids=[]
    for item in nodes[0].elts:
        need(isinstance(item,ast.Call) and isinstance(item.func,ast.Name) and item.func.id=='case' and item.args and isinstance(item.args[0],ast.Constant), 'original Q38 CASES shape changed')
        ids.append(item.args[0].value)
    need(len(ids)==44 and set(ids)=={'SPM%02d'%i for i in range(1,45)}, 'original Q38 complete SPM01-SPM44 required')
    return ids

def validate_delta(sha, ancestor_exit, paths):
    need(len(sha)==40 and all(c in '0123456789abcdef' for c in sha) and sha!=F8, 'new full F9 SHA required, not F8 or a moving ref')
    need(ancestor_exit==0, 'F9 must descend from fixed F8 by ordinary history')
    need(len(paths)==len(set(paths)), 'duplicate changed path')
    need('tests/mutants_results.json' in paths, 'F9 must actually adopt the full ledger')
    need(all(p=='tests/mutants_results.json' or p.startswith('evidence/') for p in paths), 'F8 to F9 may change only ledger JSON and evidence')
    return {'fixed_product_source':F8,'execution_source':sha,'changed_paths':paths,'closure_rule':'only tests/mutants_results.json plus evidence; no product/test/judge changes'}
