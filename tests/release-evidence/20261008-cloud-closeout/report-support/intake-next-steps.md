# 本階段全部來源的具體下一步

這是有限收尾清單，不是派工、批准或關單。[最新遠端快照](post-pr176-remote-summary.json)至2026-10-08T18:59:48.201950+00:00：32 PR、27 issues，新增draft #176，head為`5174a8dafd8c48329d7166abbd3d104e3c28c0c4`、base為#169 `a7bff8f4c7a0d61a3133b6e42d0d513dfe96367e`。#137正文於19:01:31Z更正，19:03:45Z GET核實，head未變；[原件](pr137-summary-correction.json)保留。#173最新`181fc76049b2b2d001957d2ee0008448bbf5b024`僅四份文件，已於產品測試結束後以`d8642b2e684038cbb8e24aba057c44e7aac1b231`接回。

本次清單依[43輪閘門矩陣](../gates/matrix.md)及[CSS封存](../css-c2-c4/README.md)更新；每輪完整SHA、命令、runtime、raw及退出碼沿原件，不相加成產品情境數。六個owner/module gates、native 300、compound非空專案、Q38保存及自有服務重啟、CSS限定流程均已有終態，不列成重跑待辦。**5174 full-CDP-r3已完成並獨審：2207／0，full無filters／modifiers／skip，completed true，84段golden相符，exit0；只有具名預期P38例外。** 所有結果以同一matrix為準，新專用async／390失敗不因full pass解除。

下表「有界切片具備合併依據」表示其記載範圍已核收，不是整個issue／PR批准或整體候選可合併。**D依賴順序：#169 → #176**；#176已含的舊heads不重複套入，個別切片若另行合併須保留表列base依賴。#176整體仍受async、完整安全Resume、#123其餘既定UI、390px卡片雙擊入口、#54完整成本及#175兩處文件交接阻塞；不能泛稱只剩外部条件。同版同範圍不再重跑或重排已完成審查。

## 27 個 issues

| Issue | 下一步 |
|---|---|
| [#166](https://github.com/ZhiQiYang/geometry-axiom/issues/166) | 判定已連raw，分歧與unknown保留；full-CDP-r3終態已核收；下一步沿#176發布收據取得最終文件SHA，不重排同版審查或用agent共識替驗收。 |
| [#142](https://github.com/ZhiQiYang/geometry-axiom/issues/142) | 空白／操作／保存／完整清空／重開及表列43輪已有原件；full-CDP-r3已核收，#176依本表產品阻塞保持draft，不能以gate數關單。 |
| [#128](https://github.com/ZhiQiYang/geometry-axiom/issues/128) | PF-0／#129未採納差分已獨立列決策；下一步由使用者決定精確語義，未採納前不改SSOT或實作，不反覆重審相同提案。 |
| [#123](https://github.com/ZhiQiYang/geometry-axiom/issues/123) | C2梁色／C4空槽的desktop、390限定流程已核收，390空槽採既有inspector入口；可依D交付此CSS切片。唯一UI writer下一步修390卡片選取後#btnZoom移入第二下位置的入口缺陷，及43列矩陣中token/header/料單/構件分段/網格控制/S4面板等既定差距。附件只阻原稿比較，不能整單稱external-only。 |
| [#119](https://github.com/ZhiQiYang/geometry-axiom/issues/119) | 既有容量／勾選診斷沿458歷史完整CDP保留；5174 full-CDP-r3相關段已核收，不另啟同版重跑。擴容政策仍另列決策。 |
| [#118](https://github.com/ZhiQiYang/geometry-axiom/issues/118) | room-worker的實際Worker取消／晚callback範圍及既有PDF流程已核收；full-CDP-r3內guide/card等整合段已核收；新真缺陷另交唯一writer修。環境中斷不当資源漏失。 |
| [#116](https://github.com/ZhiQiYang/geometry-axiom/issues/116) | #125已在main，5174 issue116 87項已過；有界右鍵B切片具備合併依據，依D交付。下一步僅留最終候選來源同一性；真手機/IME/OS操作交裝置QA，不重跑該gate。 |
| [#87](https://github.com/ZhiQiYang/geometry-axiom/issues/87) | 獨立multiroom 34項及共享來源／顯示回歸已核收；有界session slice具備合併依據，依D交付。不混#54，不採納#157；未接受草稿跨reload、zero-room首次建立不在此已授權slice。 |
| [#85](https://github.com/ZhiQiYang/geometry-axiom/issues/85) | 保留已跑 mutation --check freshness與舊48筆完整SHA；裁判或native變更才重算實跑，不把check當重跑。 |
| [#77](https://github.com/ZhiQiYang/geometry-axiom/issues/77) | owner及browser/exit/recovery/remove五入口已核收，含共享來源、獨立Boundary、bytes與receipt recovery；有界切片具備合併依據，依D交付。現版ZIP證據已在matrix，不再列重開重跑；真OS chooser由裝置QA補。 |
| [#62](https://github.com/ZhiQiYang/geometry-axiom/issues/62) | 來源／規則／保存的具名gates及[逐條映射](final-contract-mapping/subdivision/README.md)已核收。SR15參數／anchor、SR18角色鎖因及SR16／SR23真UI雙面更新與保存重開缺口已由[新補測附錄](../contract-gap-probes/verification-addendum.md)核收；ASan／故障注入的原始退出與獨審分類分開記錄，SR24實機仍待裝置QA，不由suite總數關單。 |
| [#61](https://github.com/ZhiQiYang/geometry-axiom/issues/61) | #133/#134實作已含，rule-reader 34及grid provenance 207已核收；有界來源規則切片具備合併依據。按D及#134→#160既有base交付，full-CDP-r3相鄰段已核收，不新增管理器。 |
| [#60](https://github.com/ZhiQiYang/geometry-axiom/issues/60) | compound兩寬22項已核收：非空model＋未發布rule draft＋native assembly，真Save/New完整清空/fresh Open及scene-only重開；有界保存契約具備合併依據，依D交付。非空跨專案碰撞政策另列決策，OS chooser僅裝置QA待驗。 |
| [#59](https://github.com/ZhiQiYang/geometry-axiom/issues/59) | 完整native及458→5174來源同一性已核收既有C按需細分／引用／原子交易範圍；有界契約具備合併依據。下一步只按D保留來源binding，Windows具名GDI由平台QA補，不另造core或重跑83suites。 |
| [#58](https://github.com/ZhiQiYang/geometry-axiom/issues/58) | 已有來源契約／公理判準保持不變；未採納PF-0等差分已另列。條文映射已補齊；#62新補測結果另沿附錄核收，不從C反推新公理、不重審已確認差分。 |
| [#57](https://github.com/ZhiQiYang/geometry-axiom/issues/57) | #58–62已完成gates與保存契約沿本表核收。條文映射已補；#62補測缺口沿附錄核收；full-CDP-r3已核收，不能重跑子suite或自動關父單。 |
| [#54](https://github.com/ZhiQiYang/geometry-axiom/issues/54) | 單房acceptance253、pan32、worker78、keyboard-r2 396及正常/取消/保存重開已核收；有界候選具備合併依據，依D交付。原keyboard中斷輪保留；整體效率目標未由此證明，[完整成本對照](final-contract-mapping/room54/README.md)已揭露21／27／33對16／20／24；下一步由單房writer在既有同起終點與完整修正協定下減少操作，不能只挑較輕P79。比較要求已採納，不列成等待新判準，不擴多房。 |
| [#49](https://github.com/ZhiQiYang/geometry-axiom/issues/49) | #146 formal76、races30及standalone controller17/browser91均已核收，含六案例、過期指紋、root/A/B ZIP隔離；有界切片具備合併依據，按#137→#143→#146及D交付。不再重合#141或重跑owner gates。 |
| [#48](https://github.com/ZhiQiYang/geometry-axiom/issues/48) | evidence-formal110與component67及來源/欄位披露、換版、/12 archive重開已核收；有界切片具備合併依據，依D交付。component明示in-memory backend不替formal；私人圖附件比較仍只由原持有者補。 |
| [#47](https://github.com/ZhiQiYang/geometry-axiom/issues/47) | 已合雙向定位切片保留现版來源／具名gates；full-CDP-r3相鄰段已核收。F4b裁切餘料已列未定案，沒有批准不實作。 |
| [#46](https://github.com/ZhiQiYang/geometry-axiom/issues/46) | #137 checkpoint/Finish/捨棄、lifecycle82/workflow34及native300已核收，正文已更正。**完整Resume仍內部未完成**：協調唯一app/space writer，完成修改前durable資格＋exact resolve＋完整快照/ticket＋metadata-only attach；保留安全阻擋，status endpoint不得單算完成。 |
| [#45](https://github.com/ZhiQiYang/geometry-axiom/issues/45) | grid-raw-provenance207已核收有限raw grid/F2a、來源拒絕、重新選取、preview及publish/Undo/Redo；有界切片具備合併依據，依D交付。未定組合只留決策，不重新實作入口。 |
| [#44](https://github.com/ZhiQiYang/geometry-axiom/issues/44) | source追溯／受控更新及formal evidence110已有候選原件；有界foundation具備合併依據，依D交付。下一步只將子項#46的完整Resume依賴保留於父狀態，不重做foundation。 |
| [#43](https://github.com/ZhiQiYang/geometry-axiom/issues/43) | 子切片已核收結果见本表；整體仍有#46 Resume與#123/async/390入口等內部阻塞。下一步沿這些具體缺陷交接writer，不以已合PR數關總單。 |
| [#25](https://github.com/ZhiQiYang/geometry-axiom/issues/25) | D34/I42/R35有限生成、member/native所有權、fresh load拒絕原因及前後完整資料不變已核收；有界切片具備合併依據，依D交付。任意拓撲不是本階段，沒有新規格不擴。 |
| [#24](https://github.com/ZhiQiYang/geometry-axiom/issues/24) | native ownership及assembly保存/清空/產品重開已核收；不把舊24項數字重標為新版。下一步由裝置QA解除A24實體操作條件；[A01–A24映射](final-contract-mapping/assembly/README.md)已补，各組合觀察限制明示，不重跑已過契約。 |
| [#19](https://github.com/ZhiQiYang/geometry-axiom/issues/19) | #24/#25有限生成與保存重開切片已具合併依據；父單下一步保留A24裝置、#24映射中具名範圍／組合限制及完整候選阻塞，不能由native pass推全部產品完成。 |

## 32 個未合併 PR

已包含的PR不需再重複合入。#141由#146接回實作；#129/#157排除；#173最新181文件已接回，ce74產品已含。新增#176是本整合draft，不重算為新增功能。D及表列base保留實際依賴；下列有界合併依據不批准整體#176。

| PR／完整 head | 來源 base | 下一步 |
|---|---|---|
| [#129](https://github.com/ZhiQiYang/geometry-axiom/pull/129) `1269e6bcc5d6928c6f51da5148a44c89d068cf7d` | `main` | 未納入：PF-0 語義仍待採納；維護者只對最新決策差分，沒有授權就不實作、不改公理。 |
| [#134](https://github.com/ZhiQiYang/geometry-axiom/pull/134) `b88545e00c13ccf5e238d4caec1c7b0d78cdc639` | `main` | 已含，reader34／grid provenance207已核收；來源規則切片具備合併依據，依D交付並保留#134→#160的base。full-CDP-r3相鄰段已核收，不另跑reader。 |
| [#136](https://github.com/ZhiQiYang/geometry-axiom/pull/136) `cc3c1c40e3fcfccfca35b305b0cbf5fab700c81e` | `main` | 已含候選：保留 Windows birth-time binary 身分修正；Windows QA 補候選啟動／binary 身分與平台回歸。 |
| [#137](https://github.com/ZhiQiYang/geometry-axiom/pull/137) `38975775cf42e9dc454aab2e25fc186d9fbd759d` | `codex/issue61-rule-line-display-20261005` | lifecycle82／workflow34、module/grid owner及native300已核收；正文19:01已更正並GET核實，勿再列摘要待改。既有checkpoint/Finish切片按#134→#137→#143交付；完整Resume仍需唯一app/space writer完成durable協定，不撤guard。 |
| [#141](https://github.com/ZhiQiYang/geometry-axiom/pull/141) `823fc91754bd3dbb7cb9fd2b27c045a739d3b14f` | `main` | 不重合head：全部9檔均由#146逐blob接回，分類為7實作／測試與2文件；standalone controller17/browser91已核收。依#146與D交付，不再跑owner或把九檔全稱元件。 |
| [#143](https://github.com/ZhiQiYang/geometry-axiom/pull/143) `6ae8e11d74b12f21fc4294e3bd068fbbc539a209` | `codex/issue46-adoption-integration-20261005` | shared-room-display89及source closure／Undo／Redo／ZIP已核收；有界切片具備合併依據，按#137→#143→#146及D交付。來源display不冒稱完整Resume。 |
| [#144](https://github.com/ZhiQiYang/geometry-axiom/pull/144) `7cfa1a87082e04908f10628485f975125dd8df9b` | `main` | feedback-resize-observer38已核收真通知／注入真錯誤／F8人工回報；有界G1修正具備合併依據，依D交付。不要另跑同gate或忽略新非預期例外。 |
| [#146](https://github.com/ZhiQiYang/geometry-axiom/pull/146) `d0c5671c5cb009e2549c0c4829dd4ca2a5a21369` | `codex/t4-reference-display-retention-20261005` | formal76／races30／standalone17與91均已核收，六案例及历史未核信語義保留；有界切片具備合併依據，按#137→#143→#146及D交付，無需重跑owner。 |
| [#147](https://github.com/ZhiQiYang/geometry-axiom/pull/147) `fb321eb1a998db47a9cd808b6df9ee36f68b3d15` | `codex/issue49-data-reader-preparation-20261005` | G3對比／間距來源已含、既有grid/formal回歸已核收；沿#146→#147→#148及D保留切片。#123整體仍有表列UI及390雙擊缺陷；不把此切片擴成整份設計驗收。 |
| [#148](https://github.com/ZhiQiYang/geometry-axiom/pull/148) `aa91cd25c62a67e2587e7ddd0cb0a6f96dd55d21` | `codex/issue123-g3-contrast-20261005` | F6 12px來源及當前space/font-layout已核收；有界字級切片具備合併依據，按#147→#148及D交付。#123其餘差距單列，不重做此變更。 |
| [#152](https://github.com/ZhiQiYang/geometry-axiom/pull/152) `43bf0566546e61ceb9a002ee4f511d9591ce86e9` | `main` | adapter冪等、限定UI／狀態／鍵盤／匯出恢復及PDF已有核收證據；有界工具切片具備合併依據。下一步只依已觀測#176／最終head完成私有ledger正式匯入與reconcile，不覆蓋舊DB；真OS print／手機及舊66 raw缺件由持有者補。 |
| [#153](https://github.com/ZhiQiYang/geometry-axiom/pull/153) `349e2a590f98ab783b7d3eeb952e95151db8e39e` | `main` | pan32、worker78、keyboard396、acceptance253及保存重開均已核收；單房切片具備合併依據，按#153→#155及D交付。無需再列worker/keyboard待跑；整體效率判準仍與此切片分開。 |
| [#154](https://github.com/ZhiQiYang/geometry-axiom/pull/154) `83769b9baef0ba23d3fd41f1058de90cf1f360ac` | `main` | room-worker的取消／晚callback與原PDF範圍已核收；full-CDP-r3相鄰段已核收，有新材料才再處理。既有環境中斷非資源漏失證明。 |
| [#155](https://github.com/ZhiQiYang/geometry-axiom/pull/155) `f1e020cba5051a331dd150d567698060bf1642b1` | `codex/issue54-room-outline-closeout` | 已含候選：keyboard原輪中斷保留；room-keyboard-r2完整396／0已得。沿matrix核收原census與正常Enter／取消，不重播不變材料。 |
| [#156](https://github.com/ZhiQiYang/geometry-axiom/pull/156) `2a7d9cba8d199a33f703e721553034400c0c5764` | `main` | 原guide/card修正已含，既有限定async與owner UI已核收；full-CDP-r3對應段已核收。新#173/#174晚回覆缺陷另修，不能因原限定async過而解除。 |
| [#157](https://github.com/ZhiQiYang/geometry-axiom/pull/157) `52d0c9e7942ff6d8a1b62d10e23f25a6bc0f6049` | `main` | 提案未納入：與已授權 #87 session slice 分開；不要將 proposal merge 或當新採納功能。 |
| [#158](https://github.com/ZhiQiYang/geometry-axiom/pull/158) `06343d8c0d7d195c30cc34832cd092cf980e1d50` | `main` | 已含歷史證據：保持原 Windows/head 綁定及原失敗，#152/#134/#156 當前結果另附；不可改標新版或填回缺失 raw。 |
| [#159](https://github.com/ZhiQiYang/geometry-axiom/pull/159) `e3ddd74e5a17b55b97c164cf7f69b6f0aeedab41` | `main` | model-history35及實際keyboard/history範圍已核收；有界切片具備合併依據，按#159→#161及D交付。當前full-CDP-r3已核收，不重跑35項。 |
| [#160](https://github.com/ZhiQiYang/geometry-axiom/pull/160) `2228da155b49d349a616b1e2737074f299e1d57d` | `codex/issue61-rule-line-display-20261005` | rule-reader34及正常焦點範圍已核收；有界切片依#134→#160及D交付。full-CDP-r3相鄰段已核收，不改正常Tab/Enter oracle。 |
| [#161](https://github.com/ZhiQiYang/geometry-axiom/pull/161) `92ded635e01aa42ea8a999e70da41b736c8b5a92` | `codex/issue123-library-history-20261006` | model-history35、save-roundtrip33、compound非空模型/typed draft/assembly重開22均已核收；有界切片具備合併依據，按#159→#161及D交付。下一步只由持有者補歷史10／155原件，不能拿新證據冒充舊raw。 |
| [#162](https://github.com/ZhiQiYang/geometry-axiom/pull/162) `8b9b6f80078c17238286e43da54b751e8d3b5b23` | `main` | 已交付：8b9b6f8 ABC 原證据曾核；保持已完成 oracle 判定，當前候選 gate另列，不重列無人接手。 |
| [#165](https://github.com/ZhiQiYang/geometry-axiom/pull/165) `354bad248180c6bb1c69735830b75827ab30b70e` | `main` | 文件來源已含，願景非公理／未採納功能界線已保留；可依D交付文件切片。現況banner已由root在本次文件commit更新，#175-owned兩處另交owner，不因文件量稱產品完成。 |
| [#167](https://github.com/ZhiQiYang/geometry-axiom/pull/167) `fb6ef45cf651235250523aa88a7fa89d0e6acb34` | `main` | Q38 native、UI68、同head fresh-browser18及自有18973服務restart13均已核收；有界切片具備合併依據，依D交付。不再跑producer/restart；assembly draft/live placement host未由restart覆蓋，OS picker交裝置QA。 |
| [#168](https://github.com/ZhiQiYang/geometry-axiom/pull/168) `a1b2f785e1bdcf13380c56b3b4c8c95093ea615c` | `main` | 已含測試修正：保留真卡片位置 commit 等待；已取消的 review comment 不發、不轉貼。原 Windows partial 不當當前 full。 |
| [#169](https://github.com/ZhiQiYang/geometry-axiom/pull/169) `a7bff8f4c7a0d61a3133b6e42d0d513dfe96367e` | `main` | #176既有base已確認；維護者按#169→#176審閱依賴，root不自行merge main。未批准review comment仍暫停，draft建立不代表此留言獲准。 |
| [#170](https://github.com/ZhiQiYang/geometry-axiom/pull/170) `ce0958ca700753172338fe291a17e781da89465a` | `codex/final-release-closeout-20261008` | 有界focus修正已有乾淨GRID346／0、P88內137證據，具備切片合併依據；按#169→#170或D交付。ce095文案/hash修正無需同版重跑，不擴為完整產品通過。 |
| [#171](https://github.com/ZhiQiYang/geometry-axiom/pull/171) `fd5b8c8c2ca65111bdc1cc33a2b9e6bb0a1ff44d` | `fix/rule-guide-focus-20261008` | I42 ownership確切拒因、拒絕後dump/assembly-read不變、正式規則線及assembly保存重開已核收；有界契約切片具備合併依據，按#170→#171或D交付，不重跑同版native／reopen。 |
| [#172](https://github.com/ZhiQiYang/geometry-axiom/pull/172) `f8225f767d969e30683a7de99270bbaff4535b5e` | `fix/rule-guide-focus-20261008` | 來源審查已交付且與原件區分；可依#170或D收文件，無新材料不重審。#174 held-bhit是真browser缺陷，新edge token-only失敗另列，不把來源推導擴為已觀察資料污染。 |
| [#173](https://github.com/ZhiQiYang/geometry-axiom/pull/173) `181fc76049b2b2d001957d2ee0008448bbf5b024` | `fix/rule-guide-focus-20261008` | ce74產品已接回，原16為12／4；新181四份文件已merge d8642b2，不能解產品阻塞。確認唯一writer交接後修replacement-rejected殘值及A成功晚回重啟B editToken歸屬；新8已獨審4成功/4token-only fail、B手把/World未變。修後才重播受影響原oracle，不為取綠重跑不變版本。 |
| [#174](https://github.com/ZhiQiYang/geometry-axiom/pull/174) `5083a456b1caff33fbc56c5fa10927582432a283` | `fix/rule-guide-focus-20261008` | 5083 projection已過：同檔唯一 writer修 held-bhit 的 edit世代＋pointer gesture歸屬，重播原bhit/proj；作者原兩例不替此新缺陷。 |
| [#175](https://github.com/ZhiQiYang/geometry-axiom/pull/175) `1127531f3aab472e01a4a99c03ef7b739b1b8ae5` | `fix/rule-guide-focus-20261008` | 命令／文件已接回：交 owner更新 AF_UNIX未執行與九元件檔過期語句；每項結果仍連原受測SHA，不稱新功能。 |
| [#176](https://github.com/ZhiQiYang/geometry-axiom/pull/176) `5174a8dafd8c48329d7166abbd3d104e3c28c0c4` | `codex/final-release-closeout-20261008` | 整合draft已發布並核head/base。full-CDP-r3已核收、#173 docs-only181已接回；本次提交公開證據/文件及source-equivalence，最終遠端／精確head CI／私有queue觀測記於#176正文發布收據。保留async/Resume/#123/390雙擊內部阻塞；依#169→#176審查，不自行merge。 |

發布順序已在draft #176確定：#169 → #176。#176含已接回的#170–175產品範圍與本輪修正；#173新181文件也已接回，不能將已含heads逐一重複套入。#137→#143→#146等歷史base依賴保留追溯，不冒稱現在main。#176當前head的7個CI jobs未啟動，不算產品pass或fail；最終文件head發布後只核該新head，無需重查同版舊jobs。

外部切片的下一步限具名責任：Windows QA交最終head完整CDP／GDI及native來源；裝置QA補真手機／IME／OS chooser／print；原持有者補#123附件、歷史10／155及#152舊DB／66 raw。這些不能解除上列內部產品缺陷。新合成來源已驗範圍不因舊私人缺件而重跑。

[#153/#155正文](pr153-pr155-summary-corrections.json)已於19:36更正並GET核對，原head歷史正文保留；新證據只綁5174。

作者／metadata不是写入交接：#173仍需明确停止/dirty状态/文件責任，#175文件同理。#168取消及#169未批准review comments保持暫停。
