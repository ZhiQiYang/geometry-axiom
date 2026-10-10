# 102ff 正式六組、caption 失敗與唯讀診斷

三個範圍皆實際測於乾淨完整 SHA `102ff28ecb005a85b42a8ae9cd7f22fdcf8cf01c`，before／after 都 clean。產品來源提交 `6784b6e0b74949bb7b425d13d1a3ad1c5a433127` 與此實際受測、文件發布 head 分開；不把102ff實跑改綁6784。

| 獨立實際範圍 | 原結果／actual exit／acceptance | 邊界 |
|---|---|---|
| 正式原六組 UI＋四個 header hit 斷言 | 198／0、exit0、completed:true、probeVerified:true | 桌面／390，正式 committed source 無 sourceOverride；不是 caption／全43項／fullCDP |
| caption／正常 pointer／keyboard 七寬度 scratch probe | 27／1、exit1、completed:false、probeVerified:false | 只有第一1382px pointer PAN／SELECT 與 caption bbox 已過；forward Tab第7個PAN取得focus卻hit:false／insideNav:false。其他六寬度、reverse Tab／Enter及final native equality未到 |
| 唯讀 single1382 scroll diagnostic | 27／1、exit1、completed:false、acceptanceClaim:false | ROOT另授權的診斷；不是正式七寬度重測。九個新scroll JSON記錄pointer PAN inner50且完整hit，Tab PAN inner0被clip且hit HEADER |

正式六組來源 SHA `6efba5412916a31df431c557a7893019f186bf8adc3fa15aa059098367e272d1`。caption 使用明示 reviewed sourceOverride `01744e5910989b2454800ae1cef2c07c9b7db29185c28ece5fec6c65d44e496d`；其 inner completed:true 僅表示單一group嘗試結束，不能當七寬度都過。這是正常keyboard導航的真實待診斷缺陷或前提，不改標為caption沒有問題。正式六組198／0仍是另一套有效收據。

唯讀診斷的明示 sourceOverride 為 `eca2f1083f13751bc4471780ac651699d34c6ffd2e111bebe829f4b0de306484`。原caption沒有記錄的getter幾何維持未知，不倒填；新diagnostic只核它本身實際取得的九個記錄。中間 prepared source970887沒有執行，不當測試結果。19／23／29與8個獨立census或static/source checks都是證據核對，不新增產品通過數。ROOT須保留全部七寬度及原keyboard目標，在後續修復候選驗正常操作；不以force、弱化斷言或無限重試取得成功。

本包封存時，fullCDP102ff仍未終端，沒有收mutable中段raw、局部count或未來full結果。原243 fullCDP1713／6、exit1、completed:false保留在先前已刊包；四組327／0、正式單房273／0與六成本、Space228／0也維持受測243。每套範圍分列，絕不相加。

三份原source archives各304／305／305 entries、receipt／raw／probe hashes、actual Python→Node→Chromium ELF／native身分、命令及clean完整SHA均保留。Original與public projection hash分開，公共source副本沒有執行；JSON鍵映射一對一，World／result值不改。私有profile、feedback、queueDB、native binary bytes及大張單獨截圖不公開。

CI於2026-10-09 UTC16:38:53.061070–16:38:55.605137單次原REST核exact102ff run37960396485：七個runner_id0、空runner_name、steps[]，CI未執行。七payment／spending annotations與七Ubuntu資訊分列，無retry、帳務或安全設定寫入。另UTC16:40:38.289144–16:40:40.486242一次核八個draft／open／unmerged PR heads與main `5cc1ffa1ee85120eca14258b86b715151cad274f`，含reader actualPython／source／command exit0及原rawhash；已停止作者無需另釋放。

公開work-manager availability確認real ledger／export仍currentunknown、歷史v5保留。Help／source availability不等於reconcile／list-ready／list-alerts，三者都未執行；未initialize空DB，私人DB與原receipt路徑不公開。七份Windows原logs仍雲端未核收，由dot唯讀核；歷史完整CDP2207／0／0只綁 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`，Windows1692／2 exit1 false保原。實體手機／touch／IME／OS、私人原稿像素與未定政策不由本包結案。
