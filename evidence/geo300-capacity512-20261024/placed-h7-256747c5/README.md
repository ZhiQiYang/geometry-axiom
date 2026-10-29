# 512 已放置完整 H7 通過，原時限不變

真 execution `256747c5c8f8f8934eeb08ae404dee1f67591508`：2026-10-29 02:38:14–02:57:16UTC，原八方法全部通過，8/0/0/0，outer exit0、timed_out=false、1142.2716743946075秒；原600秒單批、1200秒整套、16MiBstack未改。所有原先600／1200紅與中斷仍留歷史，不覆寫。

| 路徑 | 原結果 |
|---|---|
| 512 load對照 | 199.063163259秒，exit0，wait4 RSS222136KiB |
| 512順序建立＋真token確認／history／513 CAPACITY | 214.230525873秒，exit0，RSS401948KiB |
| 512 load | 193.231267293秒，exit0，RSS222204KiB |
| 512 canonical fresh1 | 216.363949650秒，exit0，RSS227488KiB |
| 512 canonical fresh2 | 216.621138544秒，exit0，RSS227400KiB |

取消／新 token 的真案例是 **7 支已放置**的 `test_placed_history_uses_current_preview_token_and_one_undo`，不是 512 支情境。上表 512 路徑證明 load、canonical、順序確認、history 與 513 CAPACITY；取消的覆蓋範圍與此分列，8 方法全過的原終態不變。

64三批、小history、原容量／compile-contract反證也在同八方法內完成；每批都保stdin/fixture、stdout/stderr、ELF hash、時間／記憶體與命令。這是完整H7綠，不是全native／browser已綠。

新三處提示接線的35項（新7＋原H13/W15）真exit0；三個不同具名撤回0/1/0，各保完整原流及2/2/4次hash工作差，舊負控不放寬。圖比較172個凍結場景真execution622b665423a55b4042a638589d2cd1efff427c7e，plain／trace／有序圖／輸出與guards全等；185build葉及172輸入閉包到256747全等，但execution不移標。

普通merge已採入正式#348產品 `7a0e6dd81c54066995981393925fa46a815de2f8`，相對受測256747非evidence diff0；目前#343 a934、#346 eaf、#3478bb完整head皆為ancestor，沒有改原上游分支或合main。這只關閉來源祖先缺口，不宣告原上游PR未驗項已完成。

採入M的單次修後N128 profile實跑5.982724714秒、exit0/gprof0；原B9a8584f57be7935604c3bad4c2481945a6ec3d9f的14.914534721秒不重抽。input.scene／stdout／stderr逐byte等；不同loadfile本地路徑的stdin不宣稱相等。gprof為診斷，child_maxrss欄含先前compiler高水位，不冒純產品RSS；正式RSS以上述wait4為準。

本輪v7將同步Git/API移到整套終態後，原測試與計時未變；11個本地fsynced archives為build＋九batch＋final。初始request checkpoint呼叫在工具適配中被一併移除，不能說有獨立request.tar.gz；outer REQUEST事前已在/tmp持久保存，inner REQUEST及OBSERVER原bytes與全部11archive在本包補齊持久交付。這個限制不改產品斷言／timeout，亦未重跑洗掉結果。

完整123帳本在固定M另行執行，census、四份架構產物、原三裁判、正式native35分鐘及browser尚未完成，維持draft/NOT READY。不放寬I33、斷言、golden或時限，不改公理層。
