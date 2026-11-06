# F9 native 終態封存包獨立核對

6191 項核對，0 項錯誤；1374 members／2,605,652B gzip。collection exit0，原 native exit1，CI35 gate0。

- 本獨審只驗封存包、原 collector 全流及已獨審的完整230列證據；collection0不改 native1／CI35gate0。
- 未重跑 native、未修改 ROOT/cache。root已可接其他工作，故本審核沒有再掃描或重新hash目前可變的 /tmp/geometry-tests payload。
- 六普通ELF依原collector實際hash與已封入sidecar一致而排除；本peer核排除名單全部為原F9 REGISTRY頂層普通執行檔，沒有未知ELF排除，未第二次讀它們的payload。
- 原未知/反證ELF預設納入，tar每個已選member完整核hash；歷史 preserved cache 明確整份排除且原BEFORE/PRESERVED manifest保留，不冒新native產物。
- 原run_all內部未另存的管線／測試自行刪除scratch不能重建，沿原收據限制；沒有把另驗browser/owner整合當native通過。
