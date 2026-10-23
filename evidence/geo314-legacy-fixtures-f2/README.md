# #314 凍結舊雙軸場景

七份場景均由未修改的 F2 `8f76f2b7d6f669670e5834310bfc26495b4a4aa6` 官方 bridge 實際產生；每份 seed／dump／loadfile／dump 逐位元組相同，七個 process exit 均 0。沒有用新產品的互動後門建立 legacy baseline。

私有輸出適配器只設定原 `tests/binaries.py` 的 OUT_DIR；原 flags、smoke、fingerprint 及 explicit inspect 均保留。原工具／適配器 hash、前後設定、官方 sidecar 與完整 build stdout／stderr 同封。`prepatch-bridge-and-inputs.tar.gz` 保留實際 binary、sidecar 與每個來源；`legacy-generation-raw.tar.gz` 保存逐指令、完整 stdin／stdout／stderr、退出碼、環境及每份 provenance。

這是 fixture 產製收據；#314 新產品完整驗收尚未完成。
