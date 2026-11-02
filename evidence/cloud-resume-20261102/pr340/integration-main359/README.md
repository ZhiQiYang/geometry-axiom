# #340 新 main359 合流來源的正式 CI 原件

固定 source M **abbf1465e4617110f16892ba3925b20615345177**；run **41453943080**，pull_request／attempt1；真 execution **8ba69d740da47031fe1a84b23b83340dca912d8c**，精確 base **fca3f1a80f1dab564f5dd4c01c9e1226eaf09e2d**。M與execution的Git tree完全相同：**48b4ec466454ead214e44a4984f4bd0c83d87238**。不把這輪結果改標成採入新衍生檔後的F或其他head。

| 正式項 | 真實終態 |
|---|---|
| native三片＋原 complete coverage | **240/240 suites**，5449 counted／5448pass／1原允許GDI skip；三片各80、零重複／漏列、原expected／timing hashes全等 |
| 原純Python aggregate CLI重驗 | **exit0**，`native-replay.json` 逐byte與官方 `native-complete.json` 相同，官方原缺suite反證0/1/0亦保留 |
| full canvas | **2310 pass／0 fail／0 skip**、87段原golden精確相符、full scope無filter/modifier；P38僅原預期單次fb-auto-probe，不冒無exception |
| grid | 原partial grid scope，**356/0** |
| assembly | 原partial assembly scope，**150/0** |
| space | 原full-space-suite，**242/0**、group completeness全符 |
| timber | 原partial timber scope，**79/0**、group completeness全符 |
| documents | 真 **47/0**，47行原PASS；此來源仍用原generic checkout且成功，不冒採入#368專用checkout |

一次25個GET取得 **12個官方原ZIP／674成員與10份真attempt1 job logs**，API SHA-256／size、inner bytes/CRC/PNG識別、固定source/tree/每列計數與原輸出核對共 **1866項、0失敗**。原artifact及log未重新生成。原native聚合是唯一執行過的repository CLI，只讀登記／三片JSON；**沒有dispatch／rerun、build、suite、下載ELF、產品或Chrome執行**。

source-actual僅物化原純聚合及registry inventory所需的 **372個固定blob／6,482,839B**，全部actual與M逐blob相同；沒有展開歷史root evidence，也沒有用共用pool的unborn HEAD。私有`.git`管理指標不發布。完整原命令／退出碼／UTC／hash見ACQUISITION、SOURCE_ISOLATION、NATIVE_REPLAY_EXECUTION、AUDIT_EXECUTION及FINAL_ACCEPTANCE。

第一份純解析結果沿用舊utility的欄名sameTreeUAndExecution，已原樣另存`.initial-field-spelling`；必要欄名修成sameTreeMAndExecution後再次純解析0。沒有重抓／重跑產品或變更檢查準則，原raw一概保留。

這不是#366 mutation artifact；那9ZIP由root在獨立SHM回收。本原件只對M／actual8ba69／base fca3成立；#340最終F採入後所需check／architecture／正式CI由root另行記錄。Windows GDI真資源驗收與新的其他來源均未由這輪宣稱。
