# #341 B1成本比較準備：純靜態，所有動態結果UNRUN

固定讀取head：`823729be5f4f025aebbf02c2dc85e09907c28812`；比較main：`e02057b4c725d6f03ae52c3bc30776bf9442b0cf`。最後原審查是[6378848374](https://github.com/ZhiQiYang/geometry-axiom/pull/341#issuecomment-6378848374)，2026-10-24T02:38:34Z。正式順序仍等#340真合main，再進#341。

四個完整leaf（contact_world.c、C harness、Python judge、expected）與main四blob全不同；main測試是14methods／41controls，舊head是10／23。但main:250–264的live-set迴圈、266–269的最後compact與舊head:103–117、118–121逐字相同，表示機制已被下游納入並共用，不是新實作，也不是B1效能通過。原件與四組Git blob見MAIN_LEAF_COMPARISON.json／MECHANISM_COMPARISON.json。

## 撤回範圍與歸因

歷史來源H可精確只替換contact_world.c:100–122（原片段SHA256`5ce7d06d42995b3b418e403d6eb1f6a012b77bec2f16a6bd7728e6a97b04f209`）：移除active／remaining／inactive-skip／末次compact，duplicate時用原內嵌memmove、--count、同i繼續。收集、原排序、ContactOrderIndex、完整座標、strict-overlap/full-cover與其餘檔不動。這對H原版/候選只回答歷史341來源；尚未寫patch、build或執行。

目前main不能全球compact=false：排序guard可能仍跳過insertion sort，indexed_dedup卻不執行，會漏排序。343還以固定out索引讀寫同一active；即刪會破壞其索引。可隔離的F對照只能完整保留343 indexed路徑與active/compact，僅在非indexed fallback撤341部分；歸因只限fallback。全域撤回會成341＋343聯合比較，不能冒獨立341結果。這是最終來源依賴，原B1尚未解除。既有tool_review已獨立只讀peer確認此陷阱。

## 四類最小資料配方

都沿原member/fact及既有literal geometry，不改規則；新組合先走原數值裁判及C/R完整欄位相等，不能用候選輸出生成oracle。

| 類別 | 可重現配方 | main歸因 |
|---|---|---|
| U無幾何重複 | regions原64個fact生成式，N取原member capacity、ID100+i、order64-i、原分離footprint；placement7、無RC regions、原輸出cap | unique IDs走343，只是pipeline/path控制，非341單因素收益 |
| S少量重複 | 同U，只令facts[1].footprint=facts[0].footprint；其餘分離，嚴格先後order | 同上，不可把343效應算341 |
| D密集重複 | active_dedup原many生成式的容量內64個prefix；同member42 pointer、orderi、原{0,0,100,27} | duplicate IDs關閉indexed，適用fallback局部比較 |
| X>cap | 原MANY=2432/2+1=1217、輸出2434＋原tail sentinel及最後一對CHECK，完全沿原公開buffer fixture | 兩邊都走原memmove，作null/no-regression控制，沒有提高產品容量 |

U/S/D是尚未執行的明確衍生replay，X沿原完整fixture。幾何重複與public-ID重複分別記錄；不能把forced fallback假稱一般host unique路徑。

## 成本與量測邊界

原NativeBuild實際在test_geo261_native_kernel.py:32；Linux保原`-std=c11 -O0 -Werror=implicit-function-declaration`、原include/defines及link，Windows原/Od與16MiB。不以O0→O2當產品收益。兩邊同完整source/include/judge/fixture/compiler/env及其他objects，只替換被審的contact-world object；編譯不計subject時間。

work另用可機械撤除的私有counter copy：admitted faces、實際path、bitmap寫入、inactive skip、pair/full-cover訪問、order/earlier呼叫、刪除數、compact scan/move，以及memmove calls/bytes。去counter後須還原真source hash，instrumented與uninstrumented輸出相同。時間用uninstrumented copy，不合成加權work分數。

記collector內CLOCK_MONOTONIC wall、getrusage user/sys；另保整個child的wall/user/sys/maxrss/exit。輸入建置／序列化與compiler成本另列。fresh process同分配，maxrss註平台單位；維持原16MiB及20s native child／300s build。RSS頁粒度或343共用frame可能遮住bitmap差異，只能記觀測不到，不能聲稱零儲存。

有限採樣提案是3個R/C/C/R區塊，容量內每process64次相同collector輸入，overflow每process1次；兩variant每類次數相同。這些是事前工作量，不是驗收門檻。達原時限／crash／setup錯照實留紅，不加時、不挑綠重試；粒度不足記UNMEASURABLE。保全部樣本、配對差與spread，零收益／倒退不能藏。

## 原裁判與新缺口

Sc493的32方法／46控制維持原SHA與歷史範圍，不重跑洗掉，也不移標main。既有最終canonical CI若完整executable＋judge＋fixture/compiler closure相同可沿用；本輪沒讀340新run，沒有宣稱其結果。新whole-withdrawal必須是真C/R/C **0/0/0等價**，不是killed mutant；新replay及counter round-trip/path proof仍UNRUN。candidate-only mutation錨點在撤回碼不存在時，setup錯不能算語義紅。

五個341 controls原保inactive-shadow、compact-active-only、compact-survivor-count、dedup-strict-overlap、dedup-full-coordinate；最終以main實際14／41及其真正受影響閉包決定缺哪個原執行，不自動重做所有舊成果，也不僅靠兩blob同一概括。逐九個公開face欄位、count/order、tail sentinel及pointer identity核對；不比較未初始化padding、不改先截斷後去重或刪後不補收，不把兩個半面合成見證。

🔒原SSOT／決策、Reading A與RC連續段、2432/64/8容量、16MiB與原timeout全保；不採舊2MiB/30秒或新加速門檻。本輪未創新木工規則，未作需新decision/#333FIELD-RULES推理的行為變更；若後續越出既有fixture再先讀指定已採決策與FIELD-RULES，這份準備不授權擴張。

下一步先等#340接受／合main，固定真正F，再明確選歷史／fallback局部／聯合歸因，才可由root排獨占時槽寫私有driver/撤回與補缺口。現時沒有variant、build、test、Chrome或性能樣本，所有量測欄位UNRUN。
