"""Prepare immutable original evidence paths; does not hash archives or touch Git."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
PREFIX='evidence/geo300-capacity512-20261024/formal-F73b21e64/'
files=[]
def add(local,relative,known=None):
    p=Path(local);assert p.is_file()and not p.is_symlink()
    if known:
        size,digest=known;assert p.stat().st_size==size
    else:
        b=p.read_bytes();size=len(b);digest=hashlib.sha256(b).hexdigest()
    files.append({'local':str(p),'relative':PREFIX+relative,'bytes':size,'sha256':digest,'archive_preload_required':known is not None})
old=Path('/workspace/geo348-F0f695866-formal-package')
add(old/'ORIGINAL_W7_H7_AND_HELPER_TRIPLES.tar.gz','historical-F0f/ORIGINAL_W7_H7_AND_HELPER_TRIPLES.tar.gz',(12616070,'dbe988b880024aee708d85d3b0364adf5ab61c9587f861271d8e2170755b37a7'))
for name in ['RAW_INDEX.json','SUMMARY.json']:add(old/name,'historical-F0f/'+name)
new=Path('/workspace/geo348-F73b21e64-formal-with-resume-package-r2')
add(new/'ORIGINAL_AFFECTED_H3_HELPERS_AND_ENVIRONMENT_RESUME.tar.gz','targeted-F73/ORIGINAL_AFFECTED_H3_HELPERS_AND_ENVIRONMENT_RESUME.tar.gz',(13842178,'72eb29033c8d7d6bed80fd045ba302846313815ca0953a8aa5148abbbf0c3b23'))
for name in ['RAW_INDEX.json','SUMMARY.json','SPECIAL_FIXTURE_ENTRIES.json','EXEC_LAUNCH.json','EXEC_COMPLETION.json']:add(new/name,'targeted-F73/'+name)
peer=Path('/workspace/archive-package-peer-specials-20261024')
for name in ['REVIEW.json','TERMINAL_REVIEW.json']:add(peer/'geo348-F0f'/name,'independent-peers/F0f/'+name)
for name in ['review_package.py','review_F0f_terminal.py','review_F0f_terminal.initial-syntax.py.txt']:add(peer/name,'independent-peers/F0f/'+name)
add('/workspace/geo348-F73-package-peer-combined-20261024/REVIEW.json','independent-peers/F73/PACKAGE_REVIEW.json')
add('/workspace/review_geo348_f73_package_compact_20261024.py','independent-peers/F73/review_package.py')
peer=Path('/workspace/geo348-F73-partial-actual-peer-backlog-20261024')
for p in sorted(peer.iterdir()):
    if p.is_file():add(p,'independent-peers/F73/actual/'+p.name)
add('/workspace/geo348-F73-body-peer-specials-20261024/REVIEW.json','independent-peers/F73/HISTORICAL_BODY_REVIEW.json')
add(P/'PROGRESS.md','PROGRESS.md')
files.append({**files[-1],'relative':'evidence/geo300-capacity512-20261024/PROGRESS.md'})
assert len({x['relative']for x in files})==len(files)
report={'status':'UNBOUND; archive preloads and actual publication budget not yet bound',
 'source_sha':'73b21e64dce72f0d16ca29e18559c51815b9724d','old_body_sha':'9cca9a4d7ea5992366c8ef5df7ef639a455544c7',
 'body_template_sha256':hashlib.sha256((P/'PR_BODY.template.md').read_bytes()).hexdigest(),
 'files':files,'payload_bytes':sum(x['bytes']for x in files),
 'archive_bytes':sum(x['bytes']for x in files if x['archive_preload_required']),
 'nonarchive_bytes':sum(x['bytes']for x in files if not x['archive_preload_required']),
 'limits':['No Git object/ref/index or archive body read in this preparation.','Both archive known pins come from completed independent full original roundtrips and must be revalidated by actual preload and final publisher.','Formal100MiB guard and600-second test timeouts unchanged.']}
(P/'FILE_ALLOWLIST_UNBOUND.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='files'},ensure_ascii=False))
