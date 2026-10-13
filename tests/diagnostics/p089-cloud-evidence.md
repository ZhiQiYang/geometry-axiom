# P-089 雲端部分驗證原始輸出

base: e95437877ed15e819fdd3dba3ce5a9d43b84eeda
環境: Linux 6.18.44 / Python 3.12.14 / overlayfs / ulimit -s 16384。
這是以 GitHub 連接逐檔取回的部分來源，不是完整 checkout；不是 native 全量收據，也不是 WSL/ext4 驗收。
正常與突變皆直接執行既有 unittest 方法。突變同時移除 _identity_signature 與 _observed_signature 的 ctime，因兩個檢查都會偵測改寫。
baseline 在此環境 200 pass，沒有重現 WSL/ext4 的紅燈。fixed 200 pass，mutant 200 fail (OSError not raised)。mutant harness exit 0 代表預期的 200 次失敗成立；每輪 unittest exit 1。

重現 harness（放在 repo 根目錄執行，baseline 模式需先還原 base 的 test_binaries.py）:
```python
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent / 'tests'))
import binaries
import test_binaries

name = 'test_same_size_rewrite_restoring_mtime_is_not_published'
mode = sys.argv[1]
if mode == 'mutant':
    # Both stat-vs-stat and fstat-vs-fstat signatures carry change time.
    original_identity = binaries._identity_signature
    original_observed = binaries._observed_signature
    binaries._identity_signature = lambda st: original_identity(st)[:-1]
    binaries._observed_signature = lambda st: original_observed(st)[:4] + original_observed(st)[5:]
out = Path(__file__).resolve().parent / (mode + '.log')
counts = {'pass': 0, 'fail': 0, 'error': 0, 'skip': 0}
with out.open('w') as log:
    for i in range(200):
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
            unittest.TestSuite([test_binaries.BinaryFreshnessTests(name)]))
        counts['pass' if result.wasSuccessful() else 'error' if result.errors else 'fail'] += 1
        log.write(f'iteration={i + 1}\n{stream.getvalue()}exit_code={0 if result.wasSuccessful() else 1}\n')
print(json.dumps({'mode': mode, 'iterations': 200, **counts}))
sys.exit(0 if (counts['fail'] == 200 if mode == 'mutant' else counts['pass'] == 200) else 1)

```

## baseline

```text
iteration=1
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=2
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=3
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=4
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=5
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=6
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=7
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=8
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=9
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=10
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=11
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=12
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=13
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=14
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=15
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=16
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=17
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=18
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=19
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=20
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=21
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=22
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=23
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=24
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=25
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=26
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=27
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=28
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=29
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=30
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=31
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=32
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=33
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=34
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=35
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=36
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=37
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=38
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=39
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=40
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=41
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=42
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=43
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=44
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=45
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=46
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=47
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=48
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=49
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=50
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=51
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=52
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=53
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=54
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=55
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=56
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=57
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=58
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=59
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=60
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=61
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=62
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=63
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=64
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=65
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=66
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=67
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=68
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=69
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=70
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=71
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=72
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=73
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=74
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=75
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=76
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=77
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=78
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=79
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=80
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=81
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=82
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=83
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=84
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=85
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=86
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=87
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=88
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=89
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=90
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=91
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=92
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=93
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=94
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=95
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=96
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=97
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=98
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=99
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=100
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=101
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=102
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=103
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=104
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=105
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=106
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=107
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=108
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=109
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=110
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=111
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=112
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=113
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=114
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=115
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=116
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=117
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=118
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=119
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=120
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=121
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=122
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=123
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=124
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=125
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=126
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=127
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=128
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=129
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=130
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=131
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=132
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=133
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=134
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=135
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=136
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=137
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=138
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=139
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=140
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=141
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=142
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=143
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=144
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=145
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=146
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=147
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=148
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=149
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=150
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=151
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=152
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=153
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=154
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=155
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=156
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=157
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=158
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=159
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=160
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=161
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=162
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=163
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=164
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=165
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=166
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=167
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=168
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=169
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=170
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=171
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=172
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=173
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=174
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=175
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=176
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=177
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=178
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=179
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=180
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=181
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=182
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=183
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=184
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=185
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=186
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=187
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=188
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=189
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=190
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=191
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=192
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=193
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=194
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=195
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=196
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=197
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=198
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0
iteration=199
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
exit_code=0
iteration=200
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
exit_code=0

```

## fixed

```text
iteration=1
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.003s

OK
exit_code=0
iteration=2
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=3
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.003s

OK
exit_code=0
iteration=4
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=5
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=6
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=7
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=8
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=9
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=10
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=11
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=12
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=13
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=14
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=15
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=16
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=17
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=18
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=19
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=20
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=21
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=22
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=23
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=24
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=25
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=26
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=27
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.003s

OK
exit_code=0
iteration=28
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=29
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=30
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=31
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=32
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=33
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=34
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=35
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=36
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=37
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=38
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=39
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=40
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=41
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=42
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=43
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=44
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=45
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=46
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=47
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=48
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=49
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=50
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=51
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=52
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=53
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=54
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=55
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=56
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=57
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=58
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=59
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=60
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=61
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=62
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=63
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=64
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=65
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=66
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=67
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=68
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=69
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=70
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=71
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=72
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=73
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=74
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=75
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=76
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=77
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=78
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=79
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=80
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=81
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=82
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=83
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=84
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=85
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=86
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=87
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=88
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=89
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=90
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=91
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=92
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=93
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=94
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.003s

OK
exit_code=0
iteration=95
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=96
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=97
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=98
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=99
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=100
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=101
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=102
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=103
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=104
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=105
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=106
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=107
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=108
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.003s

OK
exit_code=0
iteration=109
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=110
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=111
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=112
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=113
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=114
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=115
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=116
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=117
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=118
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=119
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=120
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=121
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=122
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=123
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=124
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=125
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=126
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=127
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=128
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=129
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=130
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.007s

OK
exit_code=0
iteration=131
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=132
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=133
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=134
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=135
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=136
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.003s

OK
exit_code=0
iteration=137
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=138
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=139
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=140
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=141
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=142
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=143
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=144
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=145
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=146
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=147
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.006s

OK
exit_code=0
iteration=148
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=149
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=150
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=151
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=152
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.003s

OK
exit_code=0
iteration=153
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.003s

OK
exit_code=0
iteration=154
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=155
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=156
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=157
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=158
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=159
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.003s

OK
exit_code=0
iteration=160
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=161
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=162
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=163
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=164
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=165
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=166
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=167
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=168
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=169
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=170
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=171
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=172
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=173
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=174
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=175
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=176
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=177
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=178
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=179
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=180
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=181
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=182
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=183
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=184
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=185
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=186
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=187
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=188
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=189
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=190
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=191
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=192
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=193
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=194
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=195
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=196
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=197
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=198
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=199
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0
iteration=200
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s

OK
exit_code=0

```

## mutant

```text
iteration=1
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.005s

FAILED (failures=1)
exit_code=1
iteration=2
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=3
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=4
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=5
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=6
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=7
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=8
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=9
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.004s

FAILED (failures=1)
exit_code=1
iteration=10
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=11
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=12
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=13
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=14
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=15
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=16
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=17
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=18
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=19
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=20
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=21
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=22
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=23
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=24
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=25
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=26
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=27
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=28
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=29
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=30
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=31
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=32
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=33
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=34
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=35
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=36
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=37
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=38
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=39
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=40
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=41
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=42
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=43
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=44
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=45
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=46
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=47
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=48
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=49
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=50
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=51
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=52
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=53
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=54
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=55
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=56
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=57
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=58
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=59
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=60
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=61
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=62
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=63
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=64
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=65
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=66
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=67
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=68
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=69
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=70
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=71
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=72
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=73
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=74
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=75
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=76
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=77
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=78
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=79
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=80
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=81
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=82
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=83
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=84
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=85
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=86
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=87
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=88
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=89
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=90
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=91
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=92
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=93
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=94
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=95
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=96
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=97
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=98
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=99
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=100
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=101
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=102
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=103
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=104
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=105
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=106
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=107
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=108
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=109
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=110
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=111
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=112
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=113
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=114
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=115
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=116
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=117
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=118
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=119
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=120
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=121
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=122
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=123
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=124
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=125
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=126
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=127
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=128
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=129
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=130
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=131
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=132
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=133
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=134
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=135
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=136
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=137
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=138
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=139
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=140
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=141
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=142
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=143
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=144
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=145
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=146
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=147
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=148
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=149
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=150
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=151
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=152
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=153
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=154
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=155
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=156
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=157
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=158
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=159
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=160
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=161
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=162
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=163
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=164
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=165
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=166
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=167
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=168
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=169
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=170
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=171
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=172
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=173
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=174
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=175
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.003s

FAILED (failures=1)
exit_code=1
iteration=176
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=177
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=178
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=179
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=180
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=181
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=182
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=183
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=184
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=185
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=186
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=187
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=188
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=189
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=190
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=191
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=192
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=193
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=194
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=195
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=196
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=197
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=198
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=199
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1
iteration=200
test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published) ... FAIL

======================================================================
FAIL: test_same_size_rewrite_restoring_mtime_is_not_published (test_binaries.BinaryFreshnessTests.test_same_size_rewrite_restoring_mtime_is_not_published)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/1cf89b0ff24d/repo/tests/test_binaries.py", line 607, in test_same_size_rewrite_restoring_mtime_is_not_published
    with self.assertRaises(OSError) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: OSError not raised

----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (failures=1)
exit_code=1

```
