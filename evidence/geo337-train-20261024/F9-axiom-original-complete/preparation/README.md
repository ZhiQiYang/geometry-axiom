# F9 §7 axiom 原件收件準備

僅收件，不重跑產品。原 gate / host / actual peer 均 0；189 個原始檔案 12,499,444 bytes 全數保留，包含 30 CLI 的完整 request/result/stdin/stdout/stderr，以及 V01–V05 原紅與恢復原流。

另納入真正執行的 v2 launcher / binding_guards、原 preparation 及其本地四檔、c387 capture、實際 argv 的 reaper、原 host 終態與 peer 三檔。V5 六檔是原 preparation 逐 hash 核對的依賴，本次 axiom 沒有執行它們，目錄明標 hash-checked-not-executed-v5。總計 206 regular / 0 symlinks / 12,652,356 bytes。

唯一 archive：ORIGINAL_AXIOM_PART1.tar.gz。保原 per-member logical + 4096 header/padding、11264 tar 結尾上界與 gzip 最壞上界；每次 fresh out-device free 至少 82,718,560 bytes（含64MiB reserve與2MiB metadata）。不假定壓縮率；尚未讀 SHM free，不代表已准入。

collector 沿已審 comparison SHM v2 的 source stat/hash/whole-leaf-scope、串流 tar 與完整 member roundtrip。差異是 axiom 固定來源與單包、無 ELF、結果名稱，另把 gzip 讀至 EOF 核 CRC/trailer。source before/after 不變，無 source tree/git objects 複製。禁止以收件結果推出其他 gate 綠。

root 需把 COLLECTION_REQUEST.unbound.json 的 peer 綁定實際獨審 pin，execute/root_execution_lease 改 true；透過正式 require_escalated exec 執行：

```
python3 -B /workspace/geo337-F9-axiom-collection-preparation-20261025/collect_axiom.py --request <root-bound-request.json> --execute
```

只容許既有 /dev/shm/geometry-axiom-geo337-20261025 下的新直接子目錄，拒 parent symlink/resolve 漂移；不自行建 parent、不改 mount/security。collection 0 仍是 volatile 未交付，須後續普通 push + remote blob hash 成功才可標交付。
