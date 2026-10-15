"""Real JS archive guard mutations; every row runs the actual Node archive suite."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
TARGET=ROOT/'geometry-web/project-store.js'
MUTATIONS=[
    ('A01-format', [('if(card && (manifest.format !== CARD_FORMAT || !manifest.requiredCapabilities?.includes(CARD_CAPABILITY)) || manifest.format === CARD_FORMAT && !card)', 'if(false)')]),
    ('A02-manifest', [('if(card && (manifest.format !== CARD_FORMAT || !manifest.requiredCapabilities?.includes(CARD_CAPABILITY)) || manifest.format === CARD_FORMAT && !card)', 'if(false)'), ('needed.some(c => !manifest.requiredCapabilities?.includes(c))', 'needed.some(c => c!==CARD_CAPABILITY && !manifest.requiredCapabilities?.includes(c))')]),
    ('A03-source-markers', [('if (usesCard && (!declared.has(CARD_CAPABILITY) || !declared.has(PARAMETER_CAPABILITY)))', 'if (false)')]),
    ('A04-reader', [('SECTION_CAPABILITY,CARD_CAPABILITY].includes(capability)', 'SECTION_CAPABILITY].includes(capability)')]),
    ('A05-version', [('const CARD_FORMAT = "geometry-canvas/18"', 'const CARD_FORMAT = "geometry-canvas/6"')]),
    ('A06-nested', [('if(manifest.scenarioCatalog?.scenarios.some(s=>projectCapabilities(s.snapshot.projectManifest,s.snapshot.worldScene).includes(CARD_CAPABILITY)))', 'if(false)')]),
]


def run(directory):
    start=time.monotonic();command=['node','--test','tests/test_card_reference_project_store.js']
    p=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=60)
    (directory/'stdout.log').write_bytes(p.stdout);(directory/'stderr.log').write_bytes(p.stderr)
    text=p.stdout.decode()+p.stderr.decode()
    match=re.search(r'(?:#|ℹ) fail (\d+)',text)
    skip=re.search(r'(?:#|ℹ) skipped (\d+)',text)
    return {'command':command,'exit_code':p.returncode,'seconds':time.monotonic()-start,
            'failures':int(match[1]) if match else None,'skips':int(skip[1]) if skip else None,
            'failed_names':[line for line in text.splitlines() if line.startswith(('✖ ', 'not ok '))]}


def main(out):
    out.mkdir(parents=True,exist_ok=False);original=TARGET.read_bytes()
    baseline=out/'baseline';baseline.mkdir();b=run(baseline)
    assert b['exit_code']==0 and b['failures']==0 and b['skips']==0,b
    report={'source_sha256':hashlib.sha256(original).hexdigest(),'baseline':b,'mutants':[]}
    try:
        for name,patches in MUTATIONS:
            d=out/name;d.mkdir();text=original.decode()
            for old,new in patches:
                assert text.count(old)==1,(name,old,text.count(old));text=text.replace(old,new,1)
            TARGET.write_text(text)
            red=run(d);TARGET.write_bytes(original)
            restored=d/'restored';restored.mkdir();green=run(restored)
            row={'id':name,'patches':patches,'mutant_sha256':hashlib.sha256(text.encode()).hexdigest(),'red':red,'restored':green}
            expected={'A01-format':'CR20 NO_SILENT_DOWNGRADE','A02-manifest':'CR20 manifest capability',
                      'A03-source-markers':'CR20 manifest capability','A04-reader':'CR20 reader',
                      'A05-version':'CR19 CARD_SAVE_ROUNDTRIP','A06-nested':'CR19 snapshot-only'}[name]
            row['verdict']='killed' if red['exit_code']==1 and red['failures'] and red['skips']==0 and green['exit_code']==0 and any(expected in n for n in red['failed_names']) else 'NOT_KILLED'
            report['mutants'].append(row);(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
            print(name,row['verdict'],flush=True)
            if row['verdict']!='killed':return 1
    finally:
        TARGET.write_bytes(original)
    return 0


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    raise SystemExit(main(p.parse_args().output))
