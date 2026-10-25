"""Read-only provenance collection; never run a bridge or alter acceptance."""
from pathlib import Path
import datetime,difflib,gzip,hashlib,importlib.util,json,os

OUT=Path(__file__).resolve().parent
ROOT=Path('/workspace/geometry-axiom')
EVIDENCE=Path('/tmp/g337323R8/evidence')
F='75a1e93811a52b69385cbdaf6a09d773ed9052ad'
B='b74f9a2ae7ade1555b9be45283adecc097fb76e3'
C='6366304eb787b2a50282e4132f45e51eb7d21290'
P='4b665fae21ab63aaffb7d84f6a32d5a469ba1675'
NAMES=['_role_priority_mutant.scene','_s1_p8_l_room_primary_through_reflex_extension.scene','_s1_p8b_l_room_primary_through_reflex_extension_hi.scene']
CAP=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
def H(raw):return hashlib.sha256(raw).hexdigest()
assert H(CAP.read_bytes())=='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
spec=importlib.util.spec_from_file_location('original_capture',CAP);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
rawdir=OUT/'raw';rawdir.mkdir()
gitdir=OUT/'git-originals';gitdir.mkdir()
rec=cap.Recorder(gitdir,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),F)
def git(*args):
    row,out,err=rec.run(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=ROOT,timeout=None,check=True,source_sha=F,source_variant='read-only exact-three diagnostic provenance')
    return out
def show(commit,path):
    raw=git('show',commit+':'+path)
    dest=gitdir/'files'/commit/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    return raw
def clause(raw):
    lines=raw.decode().splitlines(True)
    start=next(i for i,l in enumerate(lines) if l.startswith('I22 '))
    end=next(i for i,l in enumerate(lines[start+1:],start+1) if l.startswith('I23 '))
    return ''.join(lines[start:end]),[start+1,end]
old_ssot=show(B,'公理層.md');current_ssot=show(F,'公理層.md')
old_clause,old_lines=clause(old_ssot);new_clause,new_lines=clause(current_ssot)
assert old_clause==new_clause and '訊息指名料件、定位邊與超出的區間。' in new_clause
for path in ['AGENTS.md','geometry-guide/PRODUCT-VISION.md','決策佇列.md','geometry-templates/woodworking/FIELD-RULES.md','geometry-templates/woodworking/native/contacts.c','geometry-templates/woodworking/native/contacts.h','geometry-templates/woodworking/native/contact_world.c','tests/run_tests.py','tests/geo261_contacts_harness.c','tests/test_geo261_wood_contacts.py']:
    show(F,path)
before=show(P,'geometry-templates/woodworking/native/contacts.c')
after=show(C,'geometry-templates/woodworking/native/contacts.c')
baseline=show(B,'geometry-templates/woodworking/native/contacts.c')
assert '——定位邊 e%d'.encode() not in before and '——定位邊 e%d'.encode() not in baseline
assert '——定位邊 e%d'.encode() in after
assert git('show','-s','--format=%P',C).decode().strip()==P
git('merge-base','--is-ancestor',C,F)
git('merge-base','--is-ancestor',B,F)
history=git('log','--format=%H %P %s','-S','——定位邊 e%d',F,'--','geometry-templates/woodworking/native/contacts.c')
assert history.decode().splitlines()[0].split()[0]==C and len(history.decode().splitlines())==1
(OUT/'INTRODUCING_COMMIT.patch').write_bytes(git('show','--format=fuller',C,'--','geometry-templates/woodworking/native/contacts.c','geometry-templates/woodworking/native/contacts.h','geometry-templates/woodworking/native/contact_world.c','tests/run_tests.py','tests/geo261_contacts_harness.c'))
(OUT/'SSOT_DIAGNOSTIC_HISTORY.txt').write_bytes(git('log','--format=%H %P %s','-S','訊息指名料件、定位邊與超出的區間。',F,'--','公理層.md'))
data=json.loads((EVIDENCE/'equivalence.json').read_text())
assert data['failures']==[[n,'stdout'] for n in NAMES]
rows=[]
for name in NAMES:
    versions={};commands=[]
    for version,commit in [('base',B),('fix',F)]:
        meta=next(x for x in data['runs'] if x['scene']==name and x['version']==version)
        streams={}
        for stream in ['stdout','stderr']:
            p=EVIDENCE/'stdout'/version/(name+'.'+stream);raw=p.read_bytes()
            assert len(raw)==meta[stream+'_bytes']
            if stream=='stdout':assert H(raw)==meta['stdout_sha256']
            dest=rawdir/name/version/(stream+'.bin');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
            streams[stream]={'original_path':str(p),'bytes':len(raw),'sha256':H(raw),'copy':str(dest.relative_to(OUT))}
        p=EVIDENCE/'graphs'/version/(name+'.bin.gz');graph=gzip.decompress(p.read_bytes())
        assert H(graph)==meta['graph_sha256'] and len(graph)==meta['graph_bytes']
        (rawdir/name/version/'graph.bin.gz').write_bytes(p.read_bytes())
        out=(rawdir/name/version/'stdout.bin').read_bytes();lines=out.splitlines(keepends=True)
        assert len(lines)==2
        parsed=json.loads(lines[0]);assert parsed['ok'] is False and parsed['status']=='INVALID' and parsed['code']=='SCENE_INVALID'
        versions[version]={'source_sha':commit,'streams':streams,'first_stdout_line':lines[0].decode(),'first_response':parsed,'dump_line_sha256':H(lines[1]),'graph_sha256':H(graph),'graph_bytes':len(graph),'guards':meta['guards'],'exit':meta['exit'],'trace_exit':meta['trace_exit']}
        commands.append(meta['command'])
    a,b=versions['base'],versions['fix'];assert commands[0]==commands[1]
    assert a['exit']==b['exit']==a['trace_exit']==b['trace_exit']==0
    assert a['dump_line_sha256']==b['dump_line_sha256'] and a['graph_sha256']==b['graph_sha256'] and a['guards']==b['guards']
    old_error=a['first_response']['error'];new_error=b['first_response']['error'];assert new_error.startswith(old_error)
    aa=dict(a['first_response']);bb=dict(b['first_response']);aa.pop('error');bb.pop('error');assert aa==bb
    diff=''.join(difflib.unified_diff((rawdir/name/'base/stdout.bin').read_text().splitlines(True),(rawdir/name/'fix/stdout.bin').read_text().splitlines(True),fromfile='fixed historical base stdout',tofile='F8 actual stdout'))
    (rawdir/name/'stdout.diff').write_text(diff)
    rows.append({'scene':name,'command':commands[0],'versions':versions,'only_stdout_json_field_changed':'error','added_message_suffix':new_error[len(old_error):],'introduced_by':C,'diagnostic_is_required_by_both_base_and_current_I22':True})
judge=Path('/tmp/g337323R8/tools-frozen/verify_linux.py');(OUT/'verify_linux.original.py').write_bytes(judge.read_bytes())
assert judge.read_text().splitlines()[155].strip()=='assert not failures,failures'
facts={'schema':'geo337-r8-exact-three-readonly-triage/1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha':F,'fixed_base':B,'introduced_commit':C,'introduced_parent':P,'ssot_I22_byte_equal_after_LF':True,'base_I22_lines':old_lines,'F8_I22_lines':new_lines,'I22_clause':new_clause,'original_compare_assertion':'verify_linux.py:156 assert not failures,failures','original_compare_exit':1,'scenes_in_original_compare':data['scenes'],'runs_in_original_compare':len(data['runs']),'failures':data['failures'],'cases':rows,'classification':'Historical base omits existing I22-required diagnostic detail; current output fixes that omission. Original cross-version byte-equality gate remains failed.','product_changed':False,'tests_changed':False,'comparator_changed':False,'bridge_or_perf_rerun':False,'new_semantic_decision_adopted':False,'proof_scope':'Only three existing failed scene pairs were inspected here; their raw streams/graphs preserved. No new product acceptance claimed.'}
cap.dump(OUT/'FACTS.json',facts)
inventory=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file() and p.name!='INVENTORY.json':inventory.append({'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':H(p.read_bytes())})
cap.dump(OUT/'INVENTORY.json',{'files':inventory,'files_count':len(inventory),'read_only_product':True})
print(json.dumps({'source':F,'cases':len(rows),'file_count':len(inventory),'facts_sha256':H((OUT/'FACTS.json').read_bytes()),'exit':0}))
