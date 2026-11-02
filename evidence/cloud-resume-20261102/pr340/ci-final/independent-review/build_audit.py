from pathlib import Path

out = Path(__file__).resolve().parent
reference = Path('/tmp/geometry-resume-20261102/pr366/check_downloaded_native_browser.py').read_text()
reference = reference.replace('ROOT = Path(__file__).resolve().parent', "OUT = Path(__file__).resolve().parent\nROOT = OUT.parent")
reference = reference.replace('/tmp/geometry-pr366-20261102', '/tmp/geometry-pr340-20261102')
reference = reference.replace('7d2a1927e15d3c0d59b20fa6618005f19c4a6c56', 'fc1c9f565a2e15660e931b3884dca2220cb1b7b2')
reference = reference.replace('502a64ff6214dd6060927b7f14643a533536f20d', 'b3a248607d7eb68d3167abbb926cf491d9b35a26')
reference = reference.replace('api/20261102T025323Z/integration-jobs.json', 'api/20261102T033519Z/integration-jobs.json')
reference = reference.replace('import hashlib', 'import ast\nimport hashlib\nimport math')
reference = reference.replace('return json.loads(raw(path))', '''def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(raw(path), object_pairs_hook=unique)''')
reference = reference.replace('jobs = load(', '''expected = load(SOURCE / 'tests/run_all.expected.json')['suites']
timing_document = load(SOURCE / 'tests/native_shard_timings.json')
timings = timing_document['timings_ms']
expected_digest = hashlib.sha256((SOURCE / 'tests/run_all.expected.json').read_bytes().replace(b'\\r\\n', b'\\n')).hexdigest()
timings_digest = hashlib.sha256((SOURCE / 'tests/native_shard_timings.json').read_bytes().replace(b'\\r\\n', b'\\n')).hexdigest()
module = ast.parse(raw(SOURCE / 'tests/run_all.py'))
assignments = {node.targets[0].id: node.value for node in module.body if isinstance(node, ast.Assign)
               and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}
py_needs = ast.literal_eval(assignments['PY_NEEDS'])
document_nodes = ast.literal_eval(assignments['NODE_DOCUMENT_SCRIPT_FILES'])
pure_nodes = ast.literal_eval(assignments['NODE_PURE_TEST_FILES'])
registry = ['c:integrity', 'core:run_tests', 'mutation:check', 'oracle:framing-selftest']
registry += ['py:' + name for name in sorted(py_needs) if (SOURCE / 'tests' / (name + '.py')).is_file()]
registry += ['node:tests-js', 'node:model_viewer', 'node:polydraft', 'node:canvas_direct']
registry += list(document_nodes) + list(pure_nodes)
require(set(expected) == set(registry) and len(registry) == len(set(registry)), 'current static registry exact expected')
owners, loads = {}, [0, 0, 0]
for name in sorted(registry, key=lambda name: (-timings.get(name, 1000), name)):
    index = min(range(3), key=lambda index: (loads[index], index))
    owners[name] = index
    loads[index] += timings.get(name, 1000)
planned = [[name for name in registry if owners[name] == index] for index in range(3)]
raw(SOURCE / 'tests/native_shards.py')
raw(SOURCE / 'tests/native_shard_receipts.py')
pr = load(ROOT / 'api/20261102T033519Z/pr340.json')
require(pr['head']['sha'] == HEAD and pr['merge_commit_sha'] == MERGE, 'official PR head and execution merge')
jobs = load(''')
reference = reference.replace('and golden["total"] == actual_lines == 2267 and len(raw_sections) == 85', 'and golden["total"] == actual_lines and len(raw_sections) == len(golden["sections"])')
reference = reference.replace('require(len(browser) == 6, "exactly six completed browser groups")', '''pending_browser = [dict(name=job['name'], id=job['id'], status=job['status'], conclusion=job['conclusion']) for job in jobs
                   if job['name'].startswith('browser') and job['conclusion'] != 'success']
require(len(browser) + len(pending_browser) == 6, 'six browser jobs accounted')
require(all(job['status'] in ('queued', 'in_progress') and job['conclusion'] is None for job in pending_browser),
        'unfinished browser remains pending without failed conclusion')''')
reference = reference.replace('require(part["commit_sha"] == MERGE and part["exit_code"] == 0,', '''require(part['schema'] == 'geometry-native-shard/1' and part['shard'] == [shard, 3]
            and part['expected_sha256'] == expected_digest and part['timings_sha256'] == timings_digest
            and part['universe'] == registry and part['selected'] == planned[shard-1]
            and math.isfinite(part['seconds']) and 0 <= part['seconds'] < 1200,
            f'native {shard} exact source plan and source hashes')
    require(part["commit_sha"] == MERGE and part["exit_code"] == 0,''')
reference = reference.replace('name + " unexpected skip")', '''name + " unexpected skip")
        require((row['counted'] and expected[name]['mode'] == 'count' and row['total'] == expected[name]['count']
                 and row['passed'] + row['skipped'] == row['total'])
                or (not row['counted'] and expected[name]['mode'] == 'exit-code-only' and row['total'] == 0
                    and row['passed'] == (0 if name == 'mutation:check' else 1)), name + ' current expected count')''')
reference = reference.replace('[("408", "0")]\n                        and row["total"] == row["passed"] == 408', '[(str(expected[name]["count"]), "0")]\n                        and row["total"] == row["passed"] == expected[name]["count"]')
reference = reference.replace('output.startswith("432/432 integrity checks passed") and row["total"] == row["passed"] == 432', 'output.startswith(str(expected[name]["count"]) + "/" + str(expected[name]["count"]) + " integrity checks passed") and row["total"] == row["passed"] == expected[name]["count"]')
reference = reference.replace('result["total"] == row["total"] == 166 and result["counts"] == {"pass": 166, "fail": 0, "infrastructure": 0}\n                    and len(result["cases"]) == 166', 'result["total"] == row["total"] == expected[name]["count"] and result["counts"] == {"pass": expected[name]["count"], "fail": 0, "infrastructure": 0}\n                    and len(result["cases"]) == expected[name]["count"]')
reference = reference.replace('len(selected) == len(set(selected)) == 230 and set(selected) == set(universes[0])', 'len(selected) == len(set(selected)) == len(registry) and set(selected) == set(universes[0])')
reference = reference.replace('summary["suite_count"] == summary["executed_suites"] == 230', 'summary["suite_count"] == summary["executed_suites"] == len(registry)')
reference = reference.replace('browser=browser, native=native, native_complete=summary,', 'browser=browser, pending_browser=pending_browser, all_browser_complete=not pending_browser, native=native, native_complete=summary,')
reference = reference.replace('(ROOT / "independent-native-browser-check.json")', '(OUT / "independent-native-browser-check.json")')
reference = reference.replace('"native")}', '"native", "pending_browser")}' )
(out / 'check_current_native_browser.py').write_text(reference)
