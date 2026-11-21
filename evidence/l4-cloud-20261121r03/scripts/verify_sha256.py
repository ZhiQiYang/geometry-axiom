#!/usr/bin/env python3
"""核對證據目錄裡每一個記錄下來的 SHA-256（沿用 evidence/l4-cloud-20261121a 的核對腳本，R03 版加了三類欄位）。

用法：python3 -I verify_sha256.py [--repo <repo 根目錄>] <證據目錄> [<證據目錄> ...]
全部相符時 exit 0；任何一筆不符、無法歸類或找不到對應檔案時 exit 1。

做法：
1. 逐一讀目錄內每個檔案的原始位元組，算 SHA-256（不做任何解碼或換行轉換）。
2. 掃描所有文字檔（.json .md .js .py .sh .scene .log .txt）裡每一個 64 位十六進位字串。
3. 每一個出現都必須歸到下列其中一類，否則算失敗（不靜默略過）：
   a. 綁定檔案的欄位（FILE_KEYS）：解析出它指的檔案，值必須等於該檔原始位元組的 SHA-256。
   b. 值恰好等於目錄內某個檔案的原始位元組 SHA-256（例如 README 引述的指紋）。
   c. 已知「不是本目錄檔案指紋」的欄位（NON_FILE_KEYS，各附理由）；字串值裡緊接在 NON_FILE_CONTEXT
      欄位名後面的值（例如畫面文字擷取的 scene_hash）；或同一個值在目錄內以這類欄位出現過
      （README 引述 runtime version 之類）。
   d. 已知測試向量（KNOWN_VECTORS）。
   e. （R03 新增）`sceneSha` 與同一物件裡的 `scene` 字串並存時，重算 sha256(scene 的 UTF-8 位元組) 比對；
      `repoFileSha256` 與同一物件裡的 `path` 並存時，給了 --repo 就重算該 repo 檔原始位元組比對，沒給就算失敗。
4. `savedSha256Correction.wrongValue` 另外核對：它必須恰等於「把該檔先做 UTF-8 解碼（無效位元組
   換成 U+FFFD）再雜湊」的結果，也就是舊 `sha(String(Buffer))` 的錯值；且不得等於原始位元組雜湊。
"""
import hashlib
import json
import os
import re
import sys

HEX64 = re.compile(r'(?<![0-9a-fA-F])[0-9a-f]{64}(?![0-9a-fA-F])')
TEXT_EXT = {'.json', '.md', '.js', '.py', '.sh', '.scene', '.log', '.txt'}

# 綁定檔案的欄位：key -> 解析函式 (json 檔路徑, 所在物件) -> 目錄內相對路徑或 None
def _same_dir_single(ext):
    def resolve(json_path, obj, root):
        d = os.path.dirname(json_path)
        hits = sorted(f for f in os.listdir(d) if f.endswith(ext))
        if len(hits) != 1:
            return None, f'同目錄有 {len(hits)} 個 {ext}，無法唯一對應'
        return os.path.relpath(os.path.join(d, hits[0]), root), None
    return resolve

def _fixed(rel):
    def resolve(json_path, obj, root):
        return rel, None
    return resolve

FILE_KEYS = {
    # walk_*.result.json：另存後下載的 .gcanvas（結果 JSON 裡的 savedName 是 App 預設檔名，提交時改名）
    'savedSha256': _same_dir_single('.gcanvas'),
    # ui-sha-withdraw.receipt.json：撤回時的 ui.js
    'uiJsSha256': _fixed(os.path.join('scripts', 'ui.js')),
}

NON_FILE_KEYS = {
    'sceneSha': 'App dump 文字（UTF-8）的雜湊，checkpoint 的場景比對用；有同物件 scene 字串時另行重算',
    'identitySha': 'App identity-read 回覆 JSON 字串的雜湊，零寫入比對用，不是檔案',
    'lastUndoSha': 'ReferenceWorkspace 末筆歷史 JSON 字串的雜湊，零寫入比對用，不是檔案',
    'recipeSha': '專案配方附件 JSON 字串的雜湊，零寫入比對用，不是檔案',
    'idsSha': 'newid 唯讀回覆（id 高水位）JSON 字串的雜湊，零寫入比對用，不是檔案',
    'policyFingerprint': 'R03 模板 flat-ceiling/1 的政策指紋（flat_ceiling.h 描述字串的 sha256），不是本目錄檔案',
    'version': 'runtime_version.py 的來源版本指紋（repo 來源樹），不是本目錄檔案',
    'wrongValue': '已更正的舊錯值，另以 String(Buffer) 重算核對',
    'req': 'lib.js 側錄的 App 自身網路請求本文（contextKey、預覽 token），不是檔案指紋',
    'profilePkgHash': 'App 內 profile_runs 結果包的內容雜湊，不是本目錄檔案',
    'axiom_sha256': 'App 匯出模型內記的公理層雜湊，指 repo 檔案，不是本目錄檔案',
    'geometry_sha256': 'App 匯出模型內記的幾何雜湊，不是本目錄檔案',
    'source_sha256': 'App 匯出模型內記的來源雜湊，不是本目錄檔案',
}

# 依前文辨識的非檔案雜湊：值所在字串裡、緊接在它前面的欄位名（畫面文字擷取裡的表格沒有 JSON 結構可用）
NON_FILE_CONTEXT = {
    'scene_hash': 'App 預覽表顯示的 scene_hash（場景內容雜湊），擷自畫面文字，不是本目錄檔案',
}
# 欄位名後可接 JSON 的 `":"` 或畫面表格的 `"`；表格一列是「欄位名"舊值""新值"」，所以可跳過同列前一格
CONTEXT_TAIL = r'"?\s*[:=]?\s*"?(?:[0-9a-f]{64}"\s*"?)?$'


def context_key(text, start):
    window = text[max(0, start - 120):start]
    for name in NON_FILE_CONTEXT:
        if re.search(re.escape(name) + CONTEXT_TAIL, window):
            return name
    return None


KNOWN_VECTORS = {hashlib.sha256(b'abc').hexdigest(): 'sha256("abc") 測試向量'}


def walk_json(o, path=(), key=None):
    # 清單元素沿用所在清單的欄位名（例如 diff 的 [前, 後] 兩個值都歸 sceneSha）
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, str):
                yield path + (k,), k, v, o
            else:
                yield from walk_json(v, path + (k,), k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            if isinstance(v, str):
                yield path + (i,), key, v, o
            else:
                yield from walk_json(v, path + (i,), key)


def verify(root):
    root = os.path.abspath(root)
    files = {}
    for d, _, names in os.walk(root):
        for n in names:
            p = os.path.join(d, n)
            with open(p, 'rb') as f:
                files[os.path.relpath(p, root)] = f.read()
    raw = {rel: hashlib.sha256(b).hexdigest() for rel, b in files.items()}
    by_hash = {}
    for rel, h in raw.items():
        by_hash.setdefault(h, []).append(rel)

    rows, fails, nonfile_values = [], 0, set()

    # 第一輪：JSON 欄位（需要 key 才能判斷）
    json_hits = set()
    deferred = []
    for rel in sorted(files):
        if not rel.endswith('.json'):
            continue
        try:
            doc = json.loads(files[rel].decode('utf-8'))
        except Exception as e:  # 壞 JSON 也算失敗，不略過
            rows.append(('FAIL', rel, '-', f'JSON 解析失敗：{e}')); fails += 1
            continue
        for path, key, val, parent in walk_json(doc):
            for m in HEX64.finditer(val):
                v = m.group(0)
                json_hits.add((rel, v))
                where = f'{rel}:{"/".join(map(str, path))}'
                if key == 'sceneSha' and isinstance(parent, dict) and isinstance(parent.get('scene'), str):
                    h = hashlib.sha256(parent['scene'].encode('utf-8')).hexdigest()
                    if h == v:
                        rows.append(('OK', where, v, '= sha256(同物件 scene 字串 UTF-8)')); nonfile_values.add(v)
                    else:
                        rows.append(('FAIL', where, v, f'同物件 scene 重算為 {h}')); fails += 1
                    continue
                if key == 'repoFileSha256':
                    rp = parent.get('path') if isinstance(parent, dict) else None
                    if REPO and rp and os.path.isfile(os.path.join(REPO, rp)):
                        with open(os.path.join(REPO, rp), 'rb') as f:
                            h = hashlib.sha256(f.read()).hexdigest()
                        if h == v:
                            rows.append(('OK', where, v, f'= sha256(raw repo {rp})')); nonfile_values.add(v)
                        else:
                            rows.append(('FAIL', where, v, f'repo {rp} 原始位元組為 {h}')); fails += 1
                    else:
                        rows.append(('FAIL', where, v, '需要 --repo 與存在的 path 才能核對')); fails += 1
                    continue
                if key in FILE_KEYS:
                    target, err = FILE_KEYS[key](os.path.join(root, rel), parent, root)
                    if err or target not in raw:
                        rows.append(('FAIL', where, v, err or f'找不到 {target}')); fails += 1
                    elif raw[target] == v:
                        rows.append(('OK', where, v, f'= sha256(raw {target}, {len(files[target])} B)'))
                    else:
                        rows.append(('FAIL', where, v, f'{target} 原始位元組為 {raw[target]}')); fails += 1
                elif key == 'wrongValue' and 'savedSha256' in doc_parent_keys(doc, path):
                    target, err = FILE_KEYS['savedSha256'](os.path.join(root, rel), parent, root)
                    b = files.get(target, b'')
                    decoded = hashlib.sha256(b.decode('utf-8', 'replace').encode('utf-8')).hexdigest()
                    if not err and v == decoded and v != raw[target]:
                        rows.append(('OK', where, v, f'舊錯值 = sha256(String(Buffer {target}))，≠ 原始位元組'))
                        nonfile_values.add(v)
                    else:
                        rows.append(('FAIL', where, v, f'不是 {target} 的 String(Buffer) 雜湊')); fails += 1
                elif v in by_hash:
                    rows.append(('OK', where, v, f'= sha256(raw {", ".join(by_hash[v])})'))
                elif key in NON_FILE_KEYS:
                    rows.append(('NONFILE', where, v, NON_FILE_KEYS[key])); nonfile_values.add(v)
                elif context_key(val, m.start()) in NON_FILE_CONTEXT:
                    rows.append(('NONFILE', where, v, NON_FILE_CONTEXT[context_key(val, m.start())])); nonfile_values.add(v)
                elif v in KNOWN_VECTORS:
                    rows.append(('NONFILE', where, v, KNOWN_VECTORS[v]))
                else:
                    deferred.append((where, v, key))

    # 第一輪未歸類者：同一個值若在目錄內以已歸類的非檔案欄位出現過，就是引述（例如核對細節裡的 before／cold）
    for where, v, key in deferred:
        if v in nonfile_values:
            rows.append(('NONFILE', where, v, f'欄位 {key!r} 引述目錄內已歸類的非檔案雜湊'))
        else:
            rows.append(('FAIL', where, v, f'欄位 {key!r} 無法歸類')); fails += 1

    # 第二輪：其餘文字檔（README、腳本、日誌）與 JSON 裡不在字串值中的出現
    for rel in sorted(files):
        if os.path.splitext(rel)[1] not in TEXT_EXT:
            continue
        text = files[rel].decode('utf-8', 'replace')
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in HEX64.finditer(line):
                v = m.group(0)
                if (rel, v) in json_hits:
                    continue
                where = f'{rel}:{lineno}'
                if v in by_hash:
                    rows.append(('OK', where, v, f'= sha256(raw {", ".join(by_hash[v])})'))
                elif v in nonfile_values:
                    rows.append(('NONFILE', where, v, '引述目錄內已歸類的非檔案雜湊'))
                elif v in KNOWN_VECTORS:
                    rows.append(('NONFILE', where, v, KNOWN_VECTORS[v]))
                else:
                    rows.append(('FAIL', where, v, '無法歸類（不等於任何檔案的原始位元組雜湊）')); fails += 1

    bound = sum(1 for r in rows if r[0] == 'OK')
    print(f'== {os.path.relpath(root)}：{len(files)} 個檔案，{len(rows)} 處 SHA-256 記錄')
    for st, where, v, note in rows:
        print(f'{st:7} {where}  {v[:12]}…  {note}')
    print(f'== 結果：{"PASS" if fails == 0 else "FAIL"}（相符 {bound}、非檔案 {sum(1 for r in rows if r[0] == "NONFILE")}、失敗 {fails}）')
    return fails == 0


def doc_parent_keys(doc, path):
    o = doc
    for p in path[:-2]:
        o = o[p]
    return o.keys() if isinstance(o, dict) else ()


REPO = None

if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == '--repo':
        REPO = os.path.abspath(args[1]); args = args[2:]
    if not args:
        print(__doc__); sys.exit(2)
    ok = all([verify(d) for d in args])
    sys.exit(0 if ok else 1)
