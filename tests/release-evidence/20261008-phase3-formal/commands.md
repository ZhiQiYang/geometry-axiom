# 命令

工作目錄是暫存裡的 `phase3-formal.js`。服務已經在 `D:\geometry-axiom-inspector-draft\geometry-web` 聽 8915。沒有重編 bridge，也沒有重編 model-base。

```
$env:GEOMETRY_TEST_URL='http://127.0.0.1:8915/'
$env:GEOMETRY_PHASE3_OUT='<local-user>\AppData\Local\Temp\geometry-inspector-draft-20261008\phase3-out'
$env:GEOMETRY_CHROME='C:\Program Files\Google\Chrome\Application\chrome.exe'
$env:GEOMETRY_CDP_PORT='9516'
$env:GEOMETRY_MODEL_BASE='<local-user>\AppData\Local\Temp\geometry-tests\model-base.exe'
node phase3-formal.js
```

```
PHASE3_SUMMARY {"passed":32,"failed":1}
NODE_EXIT 1
```

追蹤同一支 8915 與同一個 `model-save.gcanvas`。這份三行紀錄沒有寫 CDP port。

```
node phase3-undo.js
```

```
UNDO_DIFF {"dump":true,"id":true,"name":true,"dirty":false,"saved":true,"downloaded":true,"models":true,"undo":true,"redo":false,"label":true}
LABELS {"before":"開啟專案「未命名專案」","emptied":"建立新專案","undone":"開啟專案「未命名專案」","emptiedModels":0,"undoneModels":1}
NODE_EXIT 0
```
