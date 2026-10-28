# #348 熱點研究候選

完整 head：`f5806c60c6067a64776f979f77981e4aba087df3`，基底C `75481194f3b85a6b07e11896403633d7d0fa0d6f`。這個分支保留 #348 下一輪產品改善及測試，尚未採入 PR348；由主代理維持唯一 writer，待完整驗收後一般合入。

修補：W先完成原facts配置/callback/validation才重用純collector結果；K新node沿用已驗空槽；W完整uint64非遞減facts省排序。保留原public幾何、完整有序graph/provider/失敗要求。

實跑指令與完整source身份、exit、編譯命令和原流均在 [證據](https://github.com/ZhiQiYang/geometry-axiom/tree/dbdf68cf0181e84171d61d7164d1beb7b70556e9/evidence/geo300-capacity512-20261024/hotpath-candidate-f5806c60)。原K29、新K6、W原14/新7、容量7、contact15、memo10依各execution分列；原編譯前置錯誤與duplicate控制存活保留，修後具名紅/恢復皆過。不把不同source的測試加總冒成一次full實跑。

一次N128 feasibility baseline6.691757846秒、candidate6.037951393秒，兩者exit0且stdout/stderr逐byte相同。第三次插樁只觀測counts，不當性能樣本。這仍不足證明full H7原1200秒或native35分鐘。

未跑：候選完整172有序圖、512正式、全census/expected、全帳本、架構三條與四檔、native及browser。上游343→346→347仍阻擋；維持未達合併條件，沒有新增skip/公理/timeout豁免。
