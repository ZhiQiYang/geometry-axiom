# host authority 錨點修復與定向驗證

公開 S3：19401ca5448e162ee6140fed37b64b83b31ddec8；分支 codex/geo261-host-authority-anchor-fix-20261021；唯一 parent L2：249571fe2477845d5330f6190dad965bf327f43b。唯一改檔 tests/test_geo261_host_authority.py；只更新 FOOTPRINT_ANCHOR，保留 count==1、原 marker、原數值及突變流程。6c 的區域暫存調整使舊單行錨點失效；既有 L2 native 的兩案失敗原件仍由原正式包保存，未改成綠。

定向驗證實際發生在提交前：HEAD=L2 加唯一已固定 dirty 測試 bytes，沒有冒稱先在 S3 執行。之後以 Git blob 綁定 479 份受驗來源至 S3，測試 bytes SHA256=a8e56b75390d4ca545077d03af81067517271c5cab0eb601c29a8afea65d4ec2。公開收據記錄 commit/push/remote exact；封裝未重新連線或 push。

命令：python3 -B /workspace/geo261-evidence/host-authority-anchor-fix-20261021/launch_targeted.py。真頂層 session77501/chunk8e67db=0；04:49:32.967688Z 至 04:49:48.274974Z。完整原 18 案全綠，無 skip/errors/failures；原八項控制均正常 0 → 突變 1／精確具名 ASSERT → 恢復正常 0。footprint 對應 command99/100/101，精確 ASSERT:host-footprint-actual-box-and-frame。65 次 compile、11 次 link 全 0；117 個 subprocess.run、468 份完整返回字串／解碼前 bytes 及 hashes 保存。479 來源前後相同。原 -O0／編譯300秒／案例30秒、16MiB stack、私有 fresh NativeBuild、CC/PYOPT unset 均維持。

fix-targeted 的 raw-stdout/raw-stderr 是 Popen communicate 解碼前 bytes；stdout/stderr 是原 subprocess.run 返回字串以 UTF-8 保存。建場 BridgeSession 的直接協定串流未另捕獲，僅保存完整建場 scene dump；不得稱所有 bridge 協定 bytes 已封存。NativeBuild 正常退出清理了暫存 binaries，包內不提供 ELF 或完整暫存來源樹。獨立靜態 peer 與頂層工具結果部分只有對話／工具觀察，轉錄均明示不是原 transport，也未假造接受器原碼。

準備期文件中的「尚未執行」是當時狀態，完成結果以 targeted-receipt、targeted-result 及 committed-binding 為準。先前未執行 runner v1 由最小差異重建，其 hash 與當時準備收據完全相符，不能冒稱另有當時原始檔。

尚未完成 S3 帳本與未來 L3 的全量正式關卡；此包只證明本次定向修復及來源綁定，不代表 PR 可合併。最主要未確定事項是後續全量驗收，不是本次具名突變是否執行。所有方法程式以純文字 .txt 保存；artifact-mapping 綁原件，SHA256SUMS 涵蓋除自身外全部檔案。
