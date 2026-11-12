# 有效 contact facts 初始化與獨立來源鏈合流

候選 03e427510c8795e34890d731a10dd4e3f84d59c9 只將整份 AppContactFacts 清零縮為 world 與有效 members 前綴。有效欄位與 padding、effective 初始化、callback 順序、visited failure prefix 均保留。新增六項加原 host authority 二十二項，28 tests exit 0、0 failure/error/skip；36.781596945 秒，來源前後 clean。撤回 whole clear 與漏清 live prefix 各由不同具名 assertion 捕捉，原碼恢復後皆通過。結構清零量不是效能時限替代。

單次 N256 32.141760736 秒、RSS110572KiB、exit0，原 placed_geometry 判準通過，stdout/stderr 與固定原 8b 對照完全相同。原 baseline34.701295152 秒不重抽；沒有在本候選重跑正式512/H7，不宣告整套通過。後續 4b17edac67648fb5f6048b05114a66e99eb1846a 新增 generic ordinal hint 仍在獨立驗證，本包的 execution 不改標。

私有一般合流已實作：M346=4c9f5031edb7940f80975fb45363b40b6aaed95f，M347=291511caf4860638d6286b3b5b0cd17335c3b921；已普通 push 至 codex/geo346-chain-private-20261029 與 codex/geo347-chain-private-20261029。原 #343/#346/#347 分支沒有寫入。從精確 a934/eaf/8bb 三頭開始，M346相對eaf只20葉evidence、M347相對8bb只34葉evidence，非evidence diff exit0、所有原head皆ancestor。root尚未將M347合入最終348產品，且未代替上游待驗正式gates；不能稱上游PR已可合併。原50葉只新取5891-byte PROGRESS，其餘49復用本地Git objects，未重跑／重封原測試。

舊 alternate 目錄不存在的警告已保留於命令原流；所需commit/tree/blob皆在既有其他store可讀，兩次merge與正常push成功。沒有刪Gitobjects、改原checkout、forcepush、mergePR或改公理。
