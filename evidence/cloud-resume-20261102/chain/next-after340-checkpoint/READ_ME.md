# #340 後序API與純Git checkpoint

API snapshot UTC：2026-11-02T10:32:23.405316+00:00。main=`e02057b4c725d6f03ae52c3bc30776bf9442b0cf`，09:41:42Z merge#354，parents`df7eb43af3389ff2afc1a73aaf4e57580ae612fc`＋`ec3ffcca315dc762d615f85fc331443f444058a1`。API原文/UTC/HTTP/SHA256在OBSERVATION.json。

#339仍merged，03:14:39Z，head8f39025be6708bd9d58e576ed5b349b7ef628624，merge8fd6c984f73ae66d0f60ebfa6761ebf408848a2b。#340仍open/non-draft、merged=false，head`b3a248607d7eb68d3167abbb926cf491d9b35a26`、base ref main（API歷史base.sha5775a9e9e46bca801a9a70aaeafcdab9f597bc4d）。API ancestry為diverged、main ahead26/behind3，merge-base502a64ff6214dd6060927b7f14643a533536f20d；#340未合入新main。

#340最新[ChatGPT審查6379912948](https://github.com/ZhiQiYang/geometry-axiom/pull/340#issuecomment-6379912948)是2026-10-24T04:34:29Z，仍綁舊04959e04c334ceaf03f865514f76b1cac8ee91f2；最新[dot6570850986](https://github.com/ZhiQiYang/geometry-axiom/pull/340#issuecomment-6570850986)是2026-11-02T06:40:52Z、綁b3a與df7。原文分別保存，不冒e020新來源審查。

精確fetch main exit0；模擬ordinary merge b3a＋e020的merge-tree exit0、無衝突，結果tree **26ef5dfd1c6f838887a30c9968021e513e2dc460**。相對新main精確只17個原歷史evidence，其他path/mode/type/blob完整等新main。相對舊b3a帶入#354完整77葉（49M/28A），含8個新test檔、1個browser plugin、2個mutation runner及native/browser/golden/registry/expected/ledger/architecture變化。原始Git entries與分類另存。

5檔局部文字diff因promisor缺blob及禁用lazyfetch而原exit128，stderr保留；不補取大量blob，內部rows/counts/assertions未核。source HEAD/index未動，舊20綠不移標。

#341仍open/draft，head823729be5f4f025aebbf02c2dc85e09907c28812，base codex/geo324-faces-20261024（API歷史SHA dcdf22655e0cf8ed47cd0b7f66d89f3a7beca694）。最後[ChatGPT審查6378848374](https://github.com/ZhiQiYang/geometry-axiom/pull/341#issuecomment-6378848374)是2026-10-24T02:38:34Z，保留whole-opt／4類成本效能、完整native/browser、基底閉包與strict aggregate10項；原文保存，未重做產品審查。

下一步由root在既有340分支普通merge固定e020，保新main全部77葉＋17歷史evidence，記真新SHA/parents並依新source做必要原check/CI；#340完成後才進#341，#339跳過。本輪不碰full D、產品工作樹/HEAD/index、任何branch/base/PR/body或既有收據，不跑test/build/Chrome/CI、不下載ZIP或hash binary。
