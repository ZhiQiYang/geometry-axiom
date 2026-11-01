from pathlib import Path
import hashlib,json,difflib
HERE=Path(__file__).parent
OLD=Path('/workspace/geo337-assembly-publication-preparation-20261025')
BASE=Path('/workspace/geo337-F9-shm-checkpoint-preparation-v3-20261025/PROGRESS.md')
def sha(b):return hashlib.sha256(b).hexdigest()
raw=(OLD/'PROGRESS.md').read_bytes()
if sha(raw)!='bc8592b1ba44df007dc030ae9eba10213a781db90ab9ecf098801650147adec9':raise RuntimeError('prior prepared progress pin')
current,history=raw.split(b'\n<details>\n',1)
old=b'| space\xe3\x80\x81timber | \xe5\x85\xa9\xe9\xa0\x85\xe5\x90\x84UNRUN at F9\xef\xbc\x9b\xe5\x8e\x9fworkflow\xef\xbc\x8c\xe5\x90\x84\xe7\x8d\xa8\xe7\xab\x8b\xe5\x9f\xa0\xef\xbc\x8fTMP |'
new='| space | F9 原正式 job RUNNING（root host6522）；尚無真 FINAL／exit，不標通過 |\n| timber | UNRUN at F9；原workflow，獨立埠／TMP |'.encode()
if current.count(old)!=1:raise RuntimeError('unique current space/timber row')
current=current.replace(old,new)
old='目前native1、兩browser未跑，替代條件尚未達成'.encode();new='目前native1、space執行中、timber未跑，替代條件尚未達成'.encode()
if current.count(old)!=1:raise RuntimeError('unique current unfinished count')
current=current.replace(old,new);result=current+b'\n<details>\n'+history
(HERE/'PROGRESS.md').write_bytes(result)
(HERE/'PROGRESS.diff').write_text(''.join(difflib.unified_diff(BASE.read_text().splitlines(True),result.decode().splitlines(True),fromfile='E609/PROGRESS.md',tofile='prepared-v2/PROGRESS.md')))
(HERE/'V1_TO_V2.diff').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),result.decode().splitlines(True),fromfile='v1/PROGRESS.md',tofile='v2/PROGRESS.md')))
m=json.loads((OLD/'FILES.json').read_bytes())
for row in m['files']:
 if row['source_path'] in [str(OLD/'PROGRESS.md'),str(OLD/'PROGRESS.diff')]:
  p=HERE/Path(row['source_path']).name;b=p.read_bytes();row.update(source_path=str(p),bytes=len(b),sha256=sha(b))
p=Path(__file__);b=p.read_bytes();m['files'].append(dict(source_path=str(p),destination='evidence/geo337-train-20261024/F9-assembly-terminal/publication-preparation/prepare_current_delta.py',bytes=len(b),sha256=sha(b)))
(HERE/'FILES.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
binding=dict(parent=m['expected_parent'],source_sha=m['source_sha'],files=len(m['files']),bytes=sum(r['bytes']for r in m['files']),progress_sha256=sha(result),files_sha256=sha((HERE/'FILES.json').read_bytes()),historical_suffix_unchanged=result.split(b'\n<details>\n',1)[1]==history,delta='Only space RUNNING root host6522 and timber UNRUN current rows/count; original source/results unchanged',publication_executed=False)
(HERE/'BINDING.json').write_text(json.dumps(binding,ensure_ascii=False,indent=2)+'\n');print(json.dumps(binding))
