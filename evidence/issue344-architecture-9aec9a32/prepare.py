from pathlib import Path
import hashlib,json,os
P=Path(__file__).parent
PREFIX='evidence/issue344-architecture-9aec9a32/'
def H(b):return hashlib.sha256(b).hexdigest()
peer=Path('/workspace/geo344-architecture-actual-peer-20261025/REVIEW.json')
assert H(peer.read_bytes())=='0e68746969b66f9e3cf59cbe2a31fce322311da0bb63e367818356ade5618b94'
j=json.loads(peer.read_bytes());assert j['exit_code']==0 and j['checks']==2683
body=(P/'PR_BODY.template.md').read_text().replace('{{ACTUAL_PEER_CHECKS}}','2683')
(P/'PR_BODY.prepared.md').write_text(body)
progress='# #344 目前架構驗收與未完成項\n\n'+body.replace('`{{EVIDENCE_HEAD}}`','本檔所在證據提交；完整 SHA 在另行 prbody 列明').replace('https://github.com/ZhiQiYang/geometry-axiom/tree/{{EVIDENCE_HEAD}}/evidence/issue344-architecture-9aec9a32/','./')
(P/'PROGRESS.md').write_text(progress)
(P/'SCOPE.md').write_text('''# 原件範圍與讀法

本批是 S344 `9aec9a32630fc65f94c53d49e99969e546574d6e` 的完整架構驗收原流，沒有壓縮或省略已完成的子命令。`originals/` 保留正式 driver 全部原件，`outer/` 保留來源材料化、資源、stack 與正式外層，`source-publication/` 是此前單 hash commit/push；兩份 host EXEC_FINAL 另列。原命令中的絕對路徑保持原文，不改寫 execution SHA。

每個 `subcommands.json` 對應 `subcommands/NNNNNN/` 的原 request、result、stdin.bin、stdout.bin、stderr.bin。負控制的 exit 1 仍原樣保留；三條原正式 judge 的 exit 為 0/0/0。604 inputs、原 Git blob/raw/LF 閉包、三裁判及兩份 SSOT 前後核對在正式原件中。

`originals/new/` 是實際產生的四檔；同一 bytes 採入產品路徑。manifest 及 scan 本來已與這次輸出一致，因此該採用提交只變更 report、receipt 與新 evidence。四檔 sourceBaseHead 仍為 S344，後續 evidence head 不冒充執行來源。未重跑 C、native、Node strict9、Chrome、mutation ledger 或性能。

`adapter-preparation/` 保留實際 driver、差分、dry-plan 原流；dry-plan -O 的 1 屬工具入口拒絕，不是產品反證。`actual-peer/` 與其他 peer 目錄保存獨立檢查程式與報告，peer 0 不代產品 gate。所有原始外部檔案仍保留，未清除 fixtures、git objects 或其他來源。

`COPYMAP.json` 列每個選定來源及 SHA256。它不自我雜湊；publisher 原流另存於雲端及後續 publication peer。唯讀驗證可按原 map 比對 Git blob。沒有把尚未公開的 Git push 收據放進其自己的提交。
''')
rows=[]
def leaf(p,d):
    assert p.is_file() and not p.is_symlink()
    b=p.read_bytes();rows.append({'source_path':str(p),'destination':d,'bytes':len(b),'sha256':H(b)})
directories=[
('/tmp/geo344-architecture-exact-20261025','originals'),
('/tmp/geo344-architecture-outer-20261025','outer'),
('/tmp/geo344-manifest-source-publication-20261025','source-publication'),
('/workspace/geo344-architecture-adapter-preparation-20261025','adapter-preparation'),
('/workspace/geo344-architecture-actual-peer-20261025','actual-peer'),
('/workspace/geo344-manifest-source-publication-actual-peer-20261025','source-publication-peer'),
('/workspace/geo344-architecture-adapter-static-peer-20261025','adapter-static-peer'),
('/workspace/geo344-architecture-launcher-static-peer-20261025','launcher-static-peer')]
for root,label in directories:
    root=Path(root)
    for p in sorted(root.rglob('*')):
        assert not p.is_symlink()
        if p.is_file():leaf(p,PREFIX+label+'/'+p.relative_to(root).as_posix())
for n in ['PROGRESS.md','SCOPE.md','prepare.py']:leaf(P/n,PREFIX+n)
for n in ['geo344-manifest-source-EXEC_FINAL-20261025.json','geo344-architecture-EXEC_FINAL-20261025.json']:leaf(Path('/tmp')/n,PREFIX+n)
for p in sorted(Path('/tmp/geo344-architecture-exact-20261025/new').iterdir()):leaf(p,'geometry-core/domain-decoupling/'+p.name)
assert len({x['destination'] for x in rows})==len(rows)
out={'schema':'geo344-original-files-map/1','source_sha':'9aec9a32630fc65f94c53d49e99969e546574d6e','copy_map_self_excluded':True,'files':rows}
(P/'FILES.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
budget={'files':len(rows),'logical_bytes':sum(x['bytes'] for x in rows),'alloc4K':sum(((x['bytes']+4095)//4096)*4096 for x in rows),'manifest_bytes':(P/'FILES.json').stat().st_size,'free':{x:os.statvfs(x).f_bavail*os.statvfs(x).f_frsize for x in ['/workspace','/tmp']},'sha256':H((P/'FILES.json').read_bytes()),'body_sha256':H((P/'PR_BODY.prepared.md').read_bytes()),'progress_sha256':H((P/'PROGRESS.md').read_bytes())}
(P/'BUDGET.json').write_text(json.dumps(budget,ensure_ascii=False,indent=2)+'\n');print(json.dumps(budget))
