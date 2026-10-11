import hashlib,json,pathlib
original=pathlib.Path('tests/evidence/geo198/review-three-residual/executors/reader-diagnostic-original.py')
source=original.read_text().replace('/tmp/geometry-198-review2/reader-diagnostic/artifacts','/tmp/geometry-202-corner/reader-diagnostic/artifacts')
exec(compile(source,str(original),'exec'))
out=pathlib.Path('/tmp/geometry-202-corner/reader-diagnostic/artifacts')
tags=lambda html:re.findall(r'<[^>]+\bdata-trace="[^"]+"[^>]*>',html)
old_tags,new_tags=tags(parent),tags(current)
assert len(old_tags)==len(new_tags)
(out/'trace-lamp-changes.json').write_text(json.dumps([{'before':a,'after':b} for a,b in zip(old_tags,new_tags) if a!=b],ensure_ascii=False,indent=2))
(out/'executor.json').write_text(json.dumps({'original_executor_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),
    'wrapper_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'operation':'original in-memory diagnostic, output-location override only; no canonical write'},indent=2))
