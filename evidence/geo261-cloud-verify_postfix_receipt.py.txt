#!/usr/bin/env python3
"""只讀核對：每筆 Node 的真實退出碼必須與收據一致，不能把 timeout/crash 算 killed。"""
import hashlib
import json
from pathlib import Path
import sys

here=Path(__file__).resolve().parent
sha=sys.argv[1]
out=here/('postfix-'+sha[:8])
receipt=json.loads((out/'receipt.json').read_text())
assert receipt['sha']==sha
codes={}
for line in (here/('postfix-'+sha[:8]+'-launch.log')).read_text(encoding='utf-8-sig').splitlines():
    try:row=json.loads(line)
    except ValueError:continue
    if isinstance(row,dict) and set(('command','rc','log'))<=set(row):
        assert row['log'] not in codes,'重複指令收據：'+row['log']
        codes[row['log']]=row['rc']
records=receipt['records']+receipt['controls']
for row in records:
    actual=codes[row['log']]
    assert actual==row['exit'],(row['label'],actual,row['exit'])
    assert actual in (0,1),(row['label'],'環境錯誤／崩潰／逾時不得當反證',actual)
    if row['mode'] in ('measure','normal','delay'):assert actual==0
    else:assert actual==1 and row['expected_behavior_proved'] is True
for name,wanted in receipt['drivers_sha256'].items():
    assert hashlib.sha256((here/name).read_bytes()).hexdigest()==wanted,name
assert receipt['timing']['no_regression'] is True
assert len(receipt['records'])==4 and len(receipt['controls'])==5
result={'sha':sha,'command_exit_codes_match':True,'no_timeout_or_crash_counted':True,'drivers_match':True,'nodes':len(records),'pass':True}
(out/'verified.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
