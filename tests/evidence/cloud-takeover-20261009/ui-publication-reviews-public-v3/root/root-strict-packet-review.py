from pathlib import Path
import datetime, hashlib, io, json, subprocess, sys, zipfile

repository = Path('<workspace-path>')
def repository_state():
    return {'root': str(repository),
            'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repository, text=True).strip(),
            'dirty': subprocess.check_output(['git', 'status', '--short'], cwd=repository, text=True)}

before = repository_state()

def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result

def read_json(content):
    return json.loads(content, object_pairs_hook=strict_object)

def read_lines(content):
    count = 0
    for line in content.splitlines():
        if line.strip():
            read_json(line)
            count += 1
    return count

records = []
for name in sys.argv[1:]:
    folder = Path(name)
    manifest_path = folder / 'manifest.json'
    manifest = read_json(manifest_path.read_bytes())
    items = manifest['publicFiles']
    seen, total, json_count, jsonl_rows, trace_rows = set(), 0, 0, 0, 0
    for item in items:
        relative = Path(item['path'])
        assert not relative.is_absolute() and '..' not in relative.parts, relative
        assert str(relative) not in seen, relative
        seen.add(str(relative))
        file = folder / relative
        content = file.read_bytes()
        assert len(content) == item['bytes'], file
        assert hashlib.sha256(content).hexdigest() == item['sha256'], file
        total += len(content)
        if file.suffix == '.json':
            read_json(content)
            json_count += 1
        elif file.suffix == '.jsonl':
            jsonl_rows += read_lines(content)
        elif file.suffix == '.zip':
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                entries = archive.namelist()
                assert len(entries) == len(set(entries)), file
                for entry in entries:
                    data = archive.read(entry)
                    if entry.endswith(('.trace', '.network')):
                        trace_rows += read_lines(data)
                    elif entry.endswith('.stacks'):
                        read_json(data)
                    elif entry.endswith('.json'):
                        read_json(data)
    records.append({'folder': str(folder), 'manifestSHA256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                    'verifiedPublicFiles': len(items), 'verifiedBytes': total, 'strictJSONFiles': json_count,
                    'strictJSONLRows': jsonl_rows, 'strictTraceJSONRows': trace_rows})
after = repository_state()
assert before == after
script = Path(__file__).resolve()
python = Path('/proc/self/exe').resolve()
print(json.dumps({'schema': 'geometry-root-strict-readonly-packet-review/1',
                  'reviewedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'reviewer': '/root',
                  'repositoryWrites': False, 'productExecution': False, 'repositoryBefore': before, 'repositoryAfter': after,
                  'executionIdentity': {'script': str(script), 'scriptSHA256': hashlib.sha256(script.read_bytes()).hexdigest(),
                                        'actualPythonExecutable': str(python), 'actualPythonSHA256': hashlib.sha256(python.read_bytes()).hexdigest(),
                                        'argv': sys.argv, 'cwd': str(Path.cwd())}, 'records': records}, indent=2))
