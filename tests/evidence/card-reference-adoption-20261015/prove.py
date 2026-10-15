"""獨立證明(不重用 apply.py 的程式碼):公理層.md 的改動恰好等於 PROPOSAL 指定的改動。
1. main 的每一行,除了 4 行被「替換」的原文,都依序出現在新檔。
2. 新檔多出來的每一行,都能在 PROPOSAL 的程式碼區塊(條號替換後)或採納橫幅裡找到。
3. PROPOSAL 每個新增/替換區塊的每一行都出現在新檔。
4. 🔒 行零刪改。
用法: python prove.py <main 的 公理層.md> <新 公理層.md> <PROPOSAL.md>
"""
import re
import sys

old = open(sys.argv[1], encoding="utf-8").read().replace("\r\n", "\n").split("\n")
new = open(sys.argv[2], encoding="utf-8").read().replace("\r\n", "\n").split("\n")
prop = open(sys.argv[3], encoding="utf-8").read()
ren = lambda s: s.replace("D-CR1", "D64").replace("I-CR1", "I74").replace("R-CR1", "R60")

sec3 = prop[prop.index("## 3. 既有條文逐條差異"):prop.index("## 5. 保存與相容契約草案")]
blocks = re.findall(r"```text\n(.*?)\n```", sec3, re.S)
# 每個 E 的第一個區塊是原文;其餘是新增/替換文字。§4 的三個區塊全是新增。
originals, additions = [], []
for part in re.split(r"\n### ", sec3)[1:]:
    bs = re.findall(r"```text\n(.*?)\n```", part, re.S)
    if part.startswith(("D-CR1", "I-CR1", "R-CR1")):
        additions += bs
    elif part.startswith("E"):
        originals.append(bs[0])
        additions += bs[1:]
add_lines = {ren(l).strip() for b in additions for l in b.split("\n")}
replaced_originals = []
for part in re.split(r"\n### ", sec3)[1:]:
    if part.startswith("E") and "替換為" in part:
        replaced_originals.append(re.findall(r"```text\n(.*?)\n```", part, re.S)[0].strip())

ok = True
# 1. main 行依序保留(被替換的原文除外)
removed = []
j = 0
for row in old:
    k = j
    while k < len(new) and new[k] != row:
        k += 1
    if k == len(new):
        removed.append(row)
    else:
        j = k + 1
print("main lines not kept in order:", len(removed))
for r in removed:
    tag = "替換原文" if r.strip() in replaced_originals else "!! 非預期"
    ok &= r.strip() in replaced_originals
    print("   ", tag, r[:70])
# 2. 新增行都有來源
old_set = set(old)
extra = [l for l in new if l not in old_set and l.strip()]
banner_ok = lambda l: l.startswith("> ") and ("整卡參數引用已採納" in l or "grid-card-reference/1" in l or "I38 新增的" in l)
unexplained = []
for l in extra:
    core = l.strip()
    core = re.sub(r"^\*\*D64 網格卡片引用（GridCardReference）\*\*：", "", core)
    if core in ("I74 完整、唯一且合法的整組來源：", "R60 整卡交易、求值及保存："):
        continue
    if core in add_lines or banner_ok(l):
        continue
    unexplained.append(l)
print("added lines:", len(extra), "unexplained:", len(unexplained))
for l in unexplained:
    print("   !!", l[:80])
ok &= not unexplained
# 3. 提案的每一行都寫進去了
new_stripped = {l.strip() for l in new} | {re.sub(r"^\*\*D64 網格卡片引用（GridCardReference）\*\*：", "", l.strip()) for l in new}
missing = [l for l in add_lines if l and l not in new_stripped]
print("proposal lines missing from SSOT:", len(missing))
for l in missing:
    print("   !!", l[:80])
ok &= not missing
# 4. 🔒 行
lock_old = [l for l in old if "\U0001F512" in l]
lock_new = [l for l in new if "\U0001F512" in l]
print("lock lines old/new:", len(lock_old), len(lock_new), "identical:", lock_old == lock_new)
ok &= lock_old == lock_new
print("RESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
