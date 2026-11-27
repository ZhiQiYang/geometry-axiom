# R05 F4b S1 原生夾具：來源與重建

`r05_source_checks.json` 來自工作包 L 的[交付索引](https://github.com/ZhiQiYang/geometry-axiom/issues/47#issuecomment-7176504870)。原始產生器、命令紀錄、bridge／producer 輸出和 `r05_source_checks.receipt.json` 都在 `L467-evidence.tar.xz` 的 `L467/l467-recovered-reproduction/`。證據包為 429892 bytes，SHA-256 `0d8b15ca544526b0e3cf3d61483637af5152a0d8476d9a32de73d7326b4afb6c`。

## 取得原件（已有證據包可略過）

從 repo 根目錄執行；只讀公開 issue #47 的十段附件，依原順序合併解碼一次：

```sh
python3 - <<'PY'
import base64, json, re
from pathlib import Path
from urllib.request import urlopen
ids = [7176443914, 7176444440, 7176445178, 7176445707, 7176446194,
       7176446756, 7176447326, 7176447914, 7176448477, 7176448936]
parts = []
for i in ids:
    with urlopen(f'https://api.github.com/repos/ZhiQiYang/geometry-axiom/issues/comments/{i}') as response:
        body = json.load(response)['body']
    block, = re.findall(r'```base64\s+(.*?)\s*```', body, re.S)
    parts.append(''.join(block.split()))
Path('/tmp/L467-evidence.tar.xz').write_bytes(base64.b64decode(''.join(parts), validate=True))
PY
```

## 重建並逐位元組比對

```sh
ulimit -s 16384
python3 -B tests/fixtures/check_r05_source_checks.py /tmp/L467-evidence.tar.xz
```

需本地 Git 歷史含 `48d5f3887e8cb8d222307db62dbdea287fda8442`（原生 fixture 的 producer 基底）、Node、Python 與 C 編譯器。此步不需連網。命令先核證據包的大小與 SHA-256，再於暫存目錄執行原件：

1. `reproduce.py` 從該基底建 bridge、model-base，跑真實 `space_modeling.preview`、`verify_package`、`replay_stored` 及 snapshot 讀取；`consume.js` 組裝並驗證兩份保存紀錄。
2. `extend_fixture.py` 重載原生場景，分別執行同值改來源、刪除後重建兩個案例，寫出緊密 JSON（UTF-8、LF）。兩支 Python 原件原本用隨機 host epoch，直接重跑並不會得到相同的 incarnation；重建器只把兩份原始 `*.commands.txt` 記錄的三個 `identity-epoch` **輸入**依序重播給原腳本。沒有從待驗 JSON 取輸入，也沒有回填或正規化任何原生結果。
3. 核版控夾具對原收據的固定大小（79573 bytes）與 SHA-256（`b0aad00d5aa04091f548a469e662b07b702254e16b8d50530ac3d88d21e47bc4`），再直接比較重建檔與版控檔的全部 bytes。不解出證據包內的成品充當重建；不改版控檔。比對失敗結束碼非零。
