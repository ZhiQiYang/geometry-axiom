# GEO-261 main (e980cb0d) 的建模交換包

產生者固定為 main `e980cb0dbf39beb40f6f3002a9ffbc43ee38c425` 的乾淨 clone(`make_fixture.sh generate`);使用該版未修改的 `modeling.build_package` 與 `tests.test_engineering_model_compatibility.StaggerModelCompatibility().build() (v stagger 400, band 0)`。
adapter 由該 clone 的原始 `modeling.base._build_adapter` 以 `cc -std=c11 -O2 geometry-core/model_base.c -lm` 編到私人暫存目錄，不借用其他分支的 adapter;執行前 `ulimit -s 16384`。
產生後以同版 `verify_package` 重驗整包相等，再直接寫入 `modeling.common.canonical_bytes(package)`;未改寫任何 manifest 欄位或幾何。

- 產生者 head:`e980cb0dbf39beb40f6f3002a9ffbc43ee38c425`。
- 產生者公理 revision:`e744f5316fd7c896275bdee4c34ad22ae97d9d8e`。
- 產生者 LF 公理 SHA-256:`18a9a75bcf4a5d5fed28c6c5f5cb9702d173198d7d0cd198ffad9936a4b94fa5`。
- 宣告能力:`extrusion/1, shell/1, composite-space/1, solid-composition/1, model-export/1`。
- 夾具大小:3962 bytes。
- 夾具 SHA-256:`fd60c8c5d5e052a504e304b0e870ac8bd4033f22e623c89e4a510503526492b8`。
- 環境:Linux-6.6.114.1-microsoft-standard-WSL2-x86_64-with-glibc2.39、Python 3.12.3、cc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0、stack 16384 KiB。

用途:#309 的 `PRE_ONE_AXIS_STAGGER_AXIOM_VERSIONS` 相容測試(重開只改兩個公理版本欄位、交叉版本拒絕)。
