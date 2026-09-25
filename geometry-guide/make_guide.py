# -*- coding: utf-8 -*-
"""
產生 current_geometry.c 的離線導讀頁。

用法：
    python make_guide.py

輸出：同目錄的 current_geometry-導讀.html
原始碼與三視圖 SVG 都內嵌進 HTML，雙擊即可離線開啟。
程式碼段落由頁內 JS 依「函式名 / 型別名 / 區段標題」即時從內嵌原始碼抽出，
所以 .c 改了只要重跑本腳本，行號與內容都會跟著更新。
"""

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE.parent / "current_geometry.c"
SVG = HERE.parent / "current_geometry.svg"
OUT = HERE / "current_geometry-導讀.html"


def js_string(text: str) -> str:
    return json.dumps(text, ensure_ascii=False).replace("</", "<\\/")


TEMPLATE = r"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>角材幾何導讀</title>
<style>
:root {
  --paper: #f5f7f4;
  --panel: #ffffff;
  --panel-2: #eef2ee;
  --rule: #d5dcd6;
  --ink: #1e2a32;
  --ink-2: #4b5962;
  --ink-3: #6e7b86;
  --blue: #2e5fa6;
  --blue-soft: #dfe8f6;
  --timber: #b26e14;
  --timber-soft: #f6e6cc;
  --guide: #b23a3a;
  --guide-soft: #f4dede;
  --code-bg: #f9faf8;
  --code-hl: #fff3d6;
  --kw: #7a3e9d;
  --ty: #1f6f8b;
  --fn: #2e5fa6;
  --cm: #6e7b86;
  --st: #9a5b1a;
  --nu: #0f7a5a;
  --pp: #8a4a10;
  --focus: #2e5fa6;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #141a20;
    --panel: #1b232b;
    --panel-2: #222c35;
    --rule: #33404b;
    --ink: #e4e9ee;
    --ink-2: #b3bec8;
    --ink-3: #8593a0;
    --blue: #7fa6e0;
    --blue-soft: #253853;
    --timber: #e0a24c;
    --timber-soft: #4a3617;
    --guide: #e07a7a;
    --guide-soft: #4a2626;
    --code-bg: #171e25;
    --code-hl: #3a3118;
    --kw: #c792ea;
    --ty: #7fd1e6;
    --fn: #8fb4f0;
    --cm: #8593a0;
    --st: #e0b072;
    --nu: #7fd9b3;
    --pp: #e0a24c;
    --focus: #7fa6e0;
  }
}
:root[data-theme="dark"] {
  --paper: #141a20;
  --panel: #1b232b;
  --panel-2: #222c35;
  --rule: #33404b;
  --ink: #e4e9ee;
  --ink-2: #b3bec8;
  --ink-3: #8593a0;
  --blue: #7fa6e0;
  --blue-soft: #253853;
  --timber: #e0a24c;
  --timber-soft: #4a3617;
  --guide: #e07a7a;
  --guide-soft: #4a2626;
  --code-bg: #171e25;
  --code-hl: #3a3118;
  --kw: #c792ea;
  --ty: #7fd1e6;
  --fn: #8fb4f0;
  --cm: #8593a0;
  --st: #e0b072;
  --nu: #7fd9b3;
  --pp: #e0a24c;
  --focus: #7fa6e0;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "Microsoft JhengHei UI", "Microsoft JhengHei", "PingFang TC", "Noto Sans TC", "Segoe UI", system-ui, sans-serif;
  font-size: 16px;
  line-height: 1.75;
}
code, pre, .mono {
  font-family: "Cascadia Code", "Cascadia Mono", "JetBrains Mono", Consolas, "Noto Sans Mono CJK TC", "Microsoft JhengHei", monospace;
}
a { color: var(--blue); text-decoration-thickness: 1px; text-underline-offset: 3px; }
a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible {
  outline: 2px solid var(--focus); outline-offset: 2px;
}

.layout {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  min-height: 100vh;
}
.rail {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  border-right: 1px solid var(--rule);
  padding: 28px 20px 40px;
  background: var(--panel);
}
.rail h1 {
  font-size: 18px;
  margin: 0 0 4px;
  letter-spacing: 0.02em;
}
.rail .sub { color: var(--ink-3); font-size: 12.5px; margin: 0 0 22px; }
.rail nav a {
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 8px;
  align-items: baseline;
  padding: 6px 8px;
  border-radius: 6px;
  color: var(--ink-2);
  text-decoration: none;
  font-size: 14px;
}
.rail nav a .n { font-size: 11.5px; color: var(--ink-3); letter-spacing: 0.06em; }
.rail nav a:hover { background: var(--panel-2); color: var(--ink); }
.rail nav a.active { background: var(--blue-soft); color: var(--ink); }
.legend { margin-top: 26px; padding-top: 18px; border-top: 1px solid var(--rule); }
.legend h2 { font-size: 11.5px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-3); margin: 0 0 10px; }
.chip {
  display: flex; align-items: center; gap: 10px;
  font-size: 13.5px; padding: 5px 0; color: var(--ink-2);
}
.chip i { width: 12px; height: 12px; border-radius: 3px; flex: none; }
.chip.room i { background: var(--ink-2); }
.chip.surface i { background: var(--blue); }
.chip.timber i { background: var(--timber); }
.chip.guide i { background: var(--guide); }
.rail .toggle {
  margin-top: 22px; font-size: 12.5px; color: var(--ink-3);
  background: none; border: 1px solid var(--rule); border-radius: 6px; padding: 5px 10px; cursor: pointer;
}
button.copy {
  margin-left: 10px; font-size: 12.5px; color: var(--ink-3);
  background: none; border: 1px solid var(--rule); border-radius: 6px; padding: 3px 10px; cursor: pointer;
}

main { padding: 44px 56px 120px; max-width: 1080px; }
.eyebrow {
  font-size: 12px; letter-spacing: 0.12em; color: var(--ink-3); text-transform: uppercase;
}
h2.sec { font-size: 26px; margin: 4px 0 14px; text-wrap: balance; letter-spacing: 0.01em; }
h3 { font-size: 17px; margin: 30px 0 8px; }
section.block { padding: 36px 0 16px; border-top: 1px solid var(--rule); }
section.block:first-of-type { border-top: 0; padding-top: 0; }
.prose { max-width: 68ch; }
.prose p { margin: 0 0 14px; }
.prose ul, .prose ol { margin: 0 0 14px; padding-left: 1.3em; }
.prose li { margin: 4px 0; }
.prose code {
  font-size: 0.88em; background: var(--panel-2); padding: 1px 5px; border-radius: 4px;
}
.key {
  border-left: 3px solid var(--blue);
  background: var(--blue-soft);
  padding: 10px 16px; margin: 16px 0; border-radius: 0 6px 6px 0;
  max-width: 68ch;
}
.key b { color: var(--blue); }

.formula {
  font-family: "Cascadia Code", "Cascadia Mono", "JetBrains Mono", Consolas, monospace;
  background: var(--code-bg);
  border: 1px solid var(--rule);
  border-radius: 6px;
  padding: 10px 16px;
  margin: 8px 0 14px;
  font-size: 14.5px;
  line-height: 1.9;
  white-space: pre;
  overflow-x: auto;
}
.formula b { color: var(--ty); font-weight: 600; }

.ftab { border-collapse: collapse; margin: 12px 0 18px; font-size: 14px; }
.ftab th, .ftab td {
  border: 1px solid var(--rule);
  padding: 6px 12px;
  text-align: left;
  vertical-align: top;
}
.ftab th { background: var(--panel-2); color: var(--ink-2); font-weight: 600; }
.ftab td:first-child { font-family: "Cascadia Code", Consolas, monospace; white-space: nowrap; }

.flow {
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 18px 0 8px;
  font-size: 13.5px;
}
.flow span {
  padding: 5px 11px; border: 1px solid var(--rule); border-radius: 999px; background: var(--panel);
}
.flow span.s { border-color: var(--blue); color: var(--blue); }
.flow span.t { border-color: var(--timber); color: var(--timber); }
.flow span.g { border-color: var(--guide); color: var(--guide); }
.flow em { color: var(--ink-3); font-style: normal; }

figure { margin: 18px 0; }
figure svg { width: 100%; height: auto; display: block; background: var(--panel); border: 1px solid var(--rule); border-radius: 8px; }
figcaption { font-size: 13px; color: var(--ink-3); margin-top: 8px; }

.panel {
  margin: 18px 0 26px;
  border: 1px solid var(--rule);
  border-radius: 8px;
  background: var(--code-bg);
  overflow: hidden;
}
.panel header {
  display: flex; justify-content: space-between; align-items: baseline; gap: 12px; flex-wrap: wrap;
  padding: 9px 14px; border-bottom: 1px solid var(--rule); background: var(--panel);
  font-size: 13px;
}
.panel header .sym { font-weight: 600; color: var(--ink); }
.panel header .loc { color: var(--ink-3); font-variant-numeric: tabular-nums; }
.panel header .loc a { color: inherit; }
.panel pre {
  margin: 0; padding: 10px 0; overflow-x: auto; font-size: 13px; line-height: 1.6; tab-size: 4;
}
.panel .row { display: grid; grid-template-columns: 30px 56px 1fr; }
.panel .row.hl { background: var(--code-hl); }
.panel .mk { text-align: center; color: var(--timber); font-weight: 700; user-select: none; }
.panel .ln { color: var(--ink-3); text-align: right; padding-right: 14px; user-select: none; font-variant-numeric: tabular-nums; }
.panel .lc { white-space: pre; padding-right: 16px; }
.panel .miss { padding: 12px 14px; color: var(--guide); }
.notes { margin: -14px 0 26px; padding: 0; list-style: none; max-width: 76ch; font-size: 14.5px; }
.notes li { display: grid; grid-template-columns: 26px 1fr; gap: 6px; padding: 4px 0; }
.notes li b { color: var(--timber); }

.kw { color: var(--kw); } .ty { color: var(--ty); } .fn { color: var(--fn); }
.cm { color: var(--cm); } .st { color: var(--st); } .nu { color: var(--nu); } .pp { color: var(--pp); }

.bench {
  border: 1px solid var(--rule); border-radius: 8px; background: var(--panel); padding: 18px 20px; margin: 18px 0;
  display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 22px;
}
.bench .ctl { display: grid; gap: 10px; align-content: start; }
.bench label { display: grid; gap: 3px; font-size: 13px; color: var(--ink-2); }
.bench .ctl { min-width: 0; }
.bench input, .bench select {
  font: inherit; font-size: 14px; padding: 5px 8px; border: 1px solid var(--rule); border-radius: 5px;
  background: var(--panel-2); color: var(--ink); min-width: 0; max-width: 100%;
}
.bench .out { font-size: 14px; }
.bench .out table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }
.bench .out td, .bench .out th { text-align: left; padding: 4px 8px; border-bottom: 1px solid var(--rule); }
.bench .out th { font-weight: 600; color: var(--ink-2); font-size: 12.5px; letter-spacing: 0.04em; }
.bench .verdict { padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; font-weight: 600; }
.bench .verdict.ok { background: var(--blue-soft); color: var(--blue); }
.bench .verdict.bad { background: var(--guide-soft); color: var(--guide); }
.bench svg { width: 100%; height: auto; margin-top: 12px; border: 1px solid var(--rule); border-radius: 6px; background: var(--code-bg); }
.calc { display: grid; grid-template-columns: repeat(3, 110px) 1fr; gap: 10px; align-items: end; margin: 12px 0 18px; }
.calc label { display: grid; gap: 3px; font-size: 13px; color: var(--ink-2); }
.calc input { font: inherit; padding: 5px 8px; border: 1px solid var(--rule); border-radius: 5px; background: var(--panel-2); color: var(--ink); width: 100%; min-width: 0; }
.calc .res { min-width: 0; overflow-wrap: anywhere; }
.calc .res { font-size: 15px; }

.full { margin-top: 20px; }
.full pre { max-height: none; }
.exp { display: grid; gap: 14px; margin: 14px 0; max-width: 76ch; }
.exp article { border: 1px solid var(--rule); border-radius: 8px; padding: 12px 16px; background: var(--panel); }
.exp article h4 { margin: 0 0 6px; font-size: 15px; }
.exp article p { margin: 0; font-size: 14.5px; color: var(--ink-2); }

@media (max-width: 900px) {
  .layout { grid-template-columns: minmax(0, 1fr); }
  .rail { position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--rule); }
  main { padding: 28px 18px 80px; }
  .bench { grid-template-columns: 1fr; }
  .calc { grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); }
}
</style>
</head>
<body>
<div class="layout">
<aside class="rail">
  <h1>角材幾何導讀</h1>
  <p class="sub mono">current_geometry.c</p>
  <nav id="nav">
    <a href="#s0"><span class="n">§0</span><span>心智模型</span></a>
    <a href="#s1"><span class="n">§1</span><span>基礎型別與向量</span></a>
    <a href="#s2"><span class="n">§2</span><span>空間邊界面</span></a>
    <a href="#s3"><span class="n">§3</span><span>四條正交邊</span></a>
    <a href="#s4"><span class="n">§4</span><span>參考線與錨點</span></a>
    <a href="#s5"><span class="n">§5</span><span>角材與放置</span></a>
    <a href="#s6"><span class="n">§6</span><span>文字輸出</span></a>
    <a href="#s7"><span class="n">§7</span><span>SVG 三視圖</span></a>
    <a href="#s8"><span class="n">§8</span><span>主程式與實驗台</span></a>
    <a href="#s9"><span class="n">§9</span><span>作業系統視窗</span></a>
    <a href="#s10"><span class="n">§10</span><span>場景檔 DSL</span></a>
    <a href="#s11"><span class="n">§11</span><span>數學公式與矩陣</span></a>
    <a href="#src"><span class="n">全文</span><span>完整原始碼</span></a>
  </nav>
  <div class="legend">
    <h2>三套座標系</h2>
    <div class="chip room"><i></i>房間座標 (x, y, z)</div>
    <div class="chip surface"><i></i>表面 UV 座標 (u, v, w)</div>
    <div class="chip timber"><i></i>角材局部 (長度, A, B)</div>
    <div class="chip guide"><i></i>參考線：只定位，非實體</div>
  </div>
  <button class="toggle" id="themeBtn" type="button">切換深色／淺色</button>
</aside>

<main>

<section class="block" id="s0">
  <div class="eyebrow mono">§0 · 先建立心智模型</div>
  <h2 class="sec">三套座標系，一條資料流</h2>
  <div class="prose">
    <p>整份程式 __LINES__ 行，但骨架只有一句話。所有東西都活在三套座標系裡，再由一條資料流串起來。單位一律 mm，全部用 64 位元整數，所以相等比較和叉積都是精確的，沒有浮點誤差。</p>
    <ul>
      <li><b>房間座標</b> (x, y, z)：X 向右、Y 向房間深處、Z 向上。所有最終答案都用它表達。</li>
      <li><b>表面 UV 座標</b> (u, v, w)：只存在於某一片空間邊界面上。天花板的 u 對應房間 X、v 對應房間 Y、w 沿法線離開表面。</li>
      <li><b>角材局部座標</b> (長度, A, B)：只存在於某一支角材上。A 是 27、B 是 33、長度是 L。</li>
    </ul>
  </div>
  <div class="flow">
    <span class="s">邊界面＋承載面</span><em>→</em>
    <span class="s">推導外環邊</span><em>→</em>
    <span class="g">參考線與邊當錨點</span><em>→</em>
    <span class="t">造一支角材</span><em>→</em>
    <span class="t">A0 面貼到錨點</span><em>→</em>
    <span class="t">推導六個面</span><em>→</em>
    <span>印文字</span><em>→</em>
    <span>印 SVG</span>
  </div>
  <figure>
    <svg id="mentalModel" viewBox="0 -80 900 550" role="img" aria-label="房間、天花板表面與角材的斜視示意圖"></svg>
    <figcaption>斜視示意（cabinet 投影）：灰色是房間軸，藍色是天花板邊界面（4000×3000，z = 2500）與它的 U、V、N 軸；前後兩條邊上各一支邊界角材（at-face e0、e2）；紅色虛線是唯一的參考線 guide 1（沿 V，u = 500，出自 spec:主支中線）；橘色是貼在它上面的主支角材（at-line，27×33，跨距 v = 27→2973）。所有數字取自內建預設世界。</figcaption>
  </figure>
  <div class="key"><b>最重要的設計決定：</b>只存「定義」，不存「推導結果」。邊不存端點、參考線不存線段、角材不存八個角，全部在需要時從父物件算出來。改一個數字，所有推導自動跟著對。</div>
</section>

<section class="block" id="s1">
  <div class="eyebrow mono">§1 · 基礎幾何型別 / 向量運算</div>
  <h2 class="sec">兩個長得一樣的結構，四個小函式</h2>
  <div class="prose">
    <p><code>Point3</code> 和 <code>Vector3</code> 欄位完全相同，分開命名只是為了讓讀者一眼知道「這是位置」還是「這是方向」。<code>Coord</code> 是 <code>int64_t</code>：整數座標讓後面的「軸長是否為 1」「兩軸是否正交」都能用 <code>==</code> 判斷。</p>
    <p>向量運算只有四個。點積用來檢查長度與正交，叉積用來檢查與建立右手座標，後面會反覆看到。</p>
  </div>
  <div data-panel='{"kind":"section","title":"基礎幾何型別","label":"七個基礎型別","callouts":[{"match":"\\} Point3;","note":"位置。"},{"match":"\\} Vector3;","note":"方向。與 Point3 同構，但語義不同。"},{"match":"\\} Quad3;","note":"四個房間座標頂點，角材的每一個面最後都變成這個。"},{"match":"\\} Plane3;","note":"一點加一法線就是一個平面；邊的「側向承載平面」用它表達。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"vector_cross","label":"叉積","callouts":[{"match":"\\.x = a\\.y \\* b\\.z","note":"標準右手叉積。放置角材時用它從 B 軸與長度軸反推 A 軸。"}]}'></div>
</section>

<section class="block" id="s2">
  <div class="eyebrow mono">§2 · 空間邊界面</div>
  <h2 class="sec">一個原點、三個軸，一條公式</h2>
  <div class="prose">
    <p>空間邊界面就是「房間裡的一片矩形」，例如天花板。它的核心是 <code>SurfaceFrame</code>：原點加三個單位軸。任何表面上的東西要變成房間座標，都經過同一條公式：</p>
    <p><code>room = origin + u·axis_u + v·axis_v + w·normal</code></p>
    <p>下面第一個面板是這條公式的執行者，第二個面板是把第一版限制鎖死的守門員。</p>
  </div>
  <div data-panel='{"kind":"type","name":"SurfaceFrame","label":"表面局部座標框架","callouts":[{"match":"Point3 origin;","note":"表面 (0,0,0) 在房間裡的位置。天花板是 (0, 0, 2500)。"},{"match":"Vector3 normal;","note":"離開表面的方向。天花板是 (0, 0, 1)。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"surface_point_to_room","label":"UV → 房間座標","callouts":[{"match":"\\.x = surface->frame\\.origin\\.x","note":"公式的 x 分量。y、z 分量長得一模一樣。"},{"match":"w \\* surface->frame\\.normal\\.x","note":"w 是沿法線的高度；貼在表面上的東西 w = 0。"}]}'></div>
  <div class="prose">
    <p>試算一下。下面用 main 裡的天花板框架（原點 (0,0,2500)，U=X，V=Y，N=Z）：</p>
  </div>
  <div class="calc">
    <label>u<input id="cu" type="number" value="500"></label>
    <label>v<input id="cv" type="number" value="300"></label>
    <label>w<input id="cw" type="number" value="0"></label>
    <div class="res mono" id="cres"></div>
  </div>
  <div data-panel='{"kind":"fn","name":"surface_frame_is_valid","label":"第一版限制的守門員","callouts":[{"match":"return vector_dot\\(frame->axis_u, frame->axis_u\\) == 1 &&","note":"U、V 長度 1。整數向量下只有 ±X、±Y、±Z 六種可能。"},{"match":"vector_dot\\(frame->axis_u, frame->axis_v\\) == 0 &&","note":"U ⊥ V。"},{"match":"vector_cross\\(frame->axis_u, frame->axis_v\\),","note":"U × V 必須等於 N：右手座標。N 的長度與垂直性由叉積本身保證，所以不必另外檢查。"}]}'></div>
</section>

<section class="block" id="s3">
  <div class="eyebrow mono">§3 · 邊界面與承載面：輪廓環推導邊</div>
  <h2 class="sec">邊不再是物件，是環上的一段</h2>
  <div class="prose">
    <p><code>SpaceBoundarySurface</code> 是純局部 2D：一個正交外輪廓 <code>PolygonLoop2</code>、零個以上的孔、每條邊的 fixity（FIXED／FREE）。它不知道自己在世界哪裡；3D 位置由承載面 <code>PlacementSurface</code> 的 frame 提供。邊不再獨立宣告——第 i 條邊就是 <code>outline.v[i] → outline.v[i+1]</code>，fixity 存在環上。</p>
  </div>
  <div data-panel='{"kind":"type","name":"PolygonLoop2","label":"環：外輪廓與孔共用"}'></div>
  <div data-panel='{"kind":"type","name":"SpaceBoundarySurface","label":"邊界面：輪廓＋孔＋fixity"}'></div>
  <div data-panel='{"kind":"fn","name":"loop_get_edge_segment","label":"環的第 i 條邊","callouts":[{"match":"out_segment->end = loop->v\\[\\(edge_index \\+ 1\\) % loop->count\\];","note":"環是封閉的：最後一條邊繞回 v[0]。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"loop_edge_outward_normal","label":"邊的局部外向法線","callouts":[{"match":"area2 \\+= a\\.u \\* b\\.v - b\\.u \\* a\\.v;","note":"先算環的有向面積定左右手——外向法線取決於環是 CCW 還是 CW。"},{"match":"out_normal->u = dv > 0 \\? 1 :","note":"CCW 環內側在邊的左邊，外向 = (dv, −du)；邊軸平行所以必有一分量 ±1、另一分量 0。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"surface_get_edge_side_plane","label":"邊帶有的側向平面","callouts":[{"match":"uv_outward_normal\\.u \\* surface->frame\\.axis_u\\.x","note":"UV 外向法線 (nu, nv) 換成房間方向 = nu·axis_u + nv·axis_v。"},{"match":"out_plane->point = surface_point_to_room\\(","note":"平面上的一點：直接拿邊的起點轉成房間座標。"}]}'></div>
</section>

<section class="block" id="s4">
  <div class="eyebrow mono">§4 · 表面參考線</div>
  <h2 class="sec">一條線只記方向和一個 offset</h2>
  <div class="prose">
    <p>參考線不是實體，只是定位工具。沿 U 的線是「固定 v = offset」，沿 V 的線是「固定 u = offset」。因此兩條不同方向的線交點只需要兩行：u 取沿 V 那條的 offset，v 取沿 U 那條的 offset。</p>
  </div>
  <div data-panel='{"kind":"type","name":"GuideLine","label":"參考線的定義","callouts":[{"match":"Coord offset;","note":"沿 U 時它是 v，沿 V 時它是 u。上方註解寫得很清楚。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"guide_line_intersection","label":"兩條參考線的交點","callouts":[{"match":"a->direction == b->direction","note":"同方向的兩條線平行，或線不屬於這片承載面，直接拒絕。"},{"match":"\\.u = along_v->offset,","note":"交點的 u 來自沿 V 的線。"},{"match":"\\.v = along_u->offset","note":"交點的 v 來自沿 U 的線。"},{"match":"交點必須真的在有效區域內","note":"多邊形與孔洞下，offset 合法不保證交點在有效區域內——交點可能落在孔裡或凹區，要再過一次 surface_contains_point。"}]}'></div>
</section>

<section class="block" id="s5">
  <div class="eyebrow mono">§5 · 完整角材實體</div>
  <h2 class="sec">造出來、貼上去、再推導六個面</h2>
  <div class="prose">
    <p><code>Timber</code> 存三個尺寸，加上一個自己的框架（原點加三軸）。<code>placed</code> 旗標告訴你框架是否有效：剛 construct 出來時是標準框架，貼到表面後才換成真的。</p>
    <p>整段最值得細讀的是 <code>timber_place_a0_on_surface</code>，它做四件事：長度軸取表面的 ±U 或 ±V；B 軸取表面法線的正或負；<b>A 軸用叉積算出來</b>，不用你手填；最後檢查 A0 面是否在有效區域內：多邊形凹角與孔洞讓「兩角點在內」不再是充分條件，所以改用整個矩形的包含檢查；另外長度端面若正好貼到外輪廓邊，該邊必須是 FIXED——自由邊外側沒有實體可釘。</p>
    <p><code>timber_get_face_room</code> 也不再逐面列頂點：六個面由「法向軸 k + 哪一側 s」一條規則推導——面內兩軸恆為 (k+1)%3、(k+2)%3，同一個繞行順序在 s=1 給 +k 法向、s=0 反走給 −k 法向，法向一律朝外。</p>
  </div>
  <div data-panel='{"kind":"type","name":"Timber","label":"角材的定義","callouts":[{"match":"bool placed;","note":"false 時 origin 與三軸只是佔位的標準框架。"},{"match":"Vector3 axis_length;","note":"放置後三軸都是房間座標裡的單位向量。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"timber_place_a0_on_surface","label":"把 A0 面貼到表面","callouts":[{"match":"Vector3 axis_length = surface_direction_vector\\(","note":"第一件事：長度軸。"},{"match":"\\? surface->frame\\.normal","note":"第二件事：B 軸沿 +N 或 −N。"},{"match":"Vector3 axis_a = vector_cross\\(axis_b, axis_length\\);","note":"第三件事：A 軸 = B × 長度，保證 長度 × A = B 的右手座標。兩個單位長且垂直的向量，叉積必為單位長。"},{"match":"SurfacePoint2 far_corner = \\{","note":"第四件事：A0 面在錨點對角的那一點。"},{"match":"surface_contains_rect","note":"整個 A0 矩形必須落在有效區域內——多邊形凹角與孔洞下「兩角點在內」不再是充分條件。§8 實驗台可以親手觸發。"},{"match":"timber->placed = true;","note":"到這裡框架才算有效。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"timber_local_to_room","label":"角材局部 → 房間座標","callouts":[{"match":"length_coordinate \\* timber->axis_length\\.x","note":"跟 surface_point_to_room 是同一個形狀的公式，只是三個軸換了名字。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"timber_get_face_room","label":"推導六個面","callouts":[{"match":"const int k = TIMBER_FACE_SPEC\\[face\\]\\.axis;","note":"面 = 法向軸 k + 側 s，規格表在型別段落：A0/A1 的 k=2（B 軸），B0/B1 的 k=1（A 軸），START/END 的 k=0（長度軸）。"},{"match":"local\\[u\\] = TIMBER_FACE_WALK\\[s\\]\\[i\\]\\[0\\]","note":"面內兩軸 (k+1)%3、(k+2)%3 上按繞行表走四角；s=0 反向走，法向因此一律朝外。"},{"match":"out_face->vertices\\[i\\] = timber_local_to_room\\(","note":"六個面的局部頂點一律經過同一個轉換。"}]}'></div>
</section>

<section class="block" id="s6">
  <div class="eyebrow mono">§6 · 輸出函式</div>
  <h2 class="sec">輸出不算幾何，只呼叫 get 再 printf</h2>
  <div class="prose">
    <p>這一整段沒有任何幾何計算。每個 print 函式都是「呼叫上面的 get 函式、拿到結果、printf」。這就是輸出跟模型分離：想換輸出格式，模型一行都不用動。下一段的 SVG 輸出正是靠這一點才能純新增。</p>
  </div>
  <div data-panel='{"kind":"fn","name":"print_timber_face","label":"印一個面的四個頂點","callouts":[{"match":"if \\(!timber_get_face_room\\(timber, face, &quad\\)\\) \\{","note":"幾何來自 get 函式。"},{"match":"print_point3\\(quad\\.vertices\\[i\\]\\);","note":"輸出只負責排版。"}]}'></div>
</section>

<section class="block" id="s7">
  <div class="eyebrow mono">§7 · SVG 三視圖輸出</div>
  <h2 class="sec">把 printf 的目標從文字換成 SVG 標籤</h2>
  <div class="prose">
    <p>純 C 沒有畫圖能力，但 SVG 是純文字，所以「畫圖」就是 fprintf 一堆標籤。這段結構刻意跟 §6 平行。讀它抓三個關鍵：<b>視圖框架</b>、<b>距離</b>、<b>兩趟走訪</b>。</p>
    <p><b>視圖框架：</b>每個視圖是兩個互相垂直的單位軸：畫面向右 <code>right</code>、畫面向下 <code>down</code>。視線方向 <code>into</code> 不另外存，直接由 <code>right × down</code> 算出，跟表面的 U × V = N 是同一條公理。投影就是內積：畫面座標 = (p·right, p·down)。畫面方向與遠近順序出自同一組軸，所以畫面不可能是鏡像。</p>
  </div>
  <div data-panel='{"kind":"type","name":"ViewFrame","label":"視圖框架","callouts":[{"match":"Vector3 down;","note":"只存兩個軸。視線方向由 right × down 算出，不存第三個欄位，也就不會與畫面方向打架。"}]}'></div>
  <div data-panel='{"kind":"section","title":"三視圖：幾何走訪與繪圖後端介面","from":"static const ViewFrame VIEW_FRAMES","to":"^\\};$","label":"三個視圖的軸","callouts":[{"match":"\\[VIEW_SIDE\\]","note":"側視：right = +Y、down = −Z，Y × (−Z) = −X，觀者站在 +X 往 −X 看。"},{"match":"\\[VIEW_BOTTOM\\]","note":"仰視：right = +X、down = +Y，X × Y = +Z，觀者在房間裡往上看天花板。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"view_project","label":"投影就是內積"}'></div>
  <div class="prose">
    <p><b>距離：</b>點沿視線的分量 p·into 就是「離觀者多遠」。角材六個面在一個視圖裡只有兩個面有面積，其餘退化成線；有面積的面依距離由遠到近畫，最近的那面才標名。所以仰視圖標 A0（貼著天花板面、最靠近往上看的人）、前視圖標 B0、側視圖標 END。</p>
  </div>

  <div class="prose">
    <p><b>後端介面：</b>幾何層不知道自己在畫 SVG 還是視窗。它只呼叫 <code>DrawTarget</code> 裡的函式指標，說「畫一個多邊形，角色是表面」；長什麼樣子由後端決定。這是整段最關鍵的設計，§9 的視窗就是靠它接上去的。</p>
  </div>
  <div data-panel='{"kind":"type","name":"DrawTarget","label":"繪圖後端介面","callouts":[{"match":"void \\*ctx;","note":"後端自己的狀態：SVG 是 FILE*，視窗是 HDC 加縮放比例。"},{"match":"void \\(\\*polygon\\)","note":"幾何層只會呼叫這幾個函式指標。"}]}'></div>
  <div data-panel='{"kind":"type","name":"DrawStyle","label":"角色，不是樣式","callouts":[{"match":"STYLE_TIMBER_FACE_NEAR,","note":"幾何層只說「這是最近的面」；SVG 後端翻成 class，視窗後端翻成較深的橘色刷子。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"timber_project_faces","label":"六個面投影、去退化、依距離排序","callouts":[{"match":"distance4 \\+= point_along\\(quad\\.vertices\\[i\\], into\\);","note":"四個頂點沿視線的分量加總：越大越遠。into 在函式開頭由 right × down 算出。"},{"match":"if \\(view_quad_area2\\(pf->q\\) == 0\\) \\{","note":"退化成線的面不畫。"},{"match":"faces\\[j - 1\\]\\.distance4 < faces\\[j\\]\\.distance4","note":"依距離遞減插入排序：遠的先畫，近的後畫（畫家演算法）。繪製與滑鼠拾取共用這一份結果。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"scene_draw_view","from":"/\\* 4\\. 角材","to":"^\\}$","label":"scene_draw_view 的角材段落","callouts":[{"match":"timber_project_faces\\(timber, view, bounds, faces\\);","note":"投影與排序交給上面的 helper，這裡只負責畫。"},{"match":"bool nearest = i \\+ 1 == face_count;","note":"最後一個就是最近的面，只有它拿到標籤。"}]}'></div>
  <div class="prose">
    <p><b>兩趟走訪：</b><code>scene_draw_view</code> 的 <code>target</code> 傳 NULL 時只累積邊界、不輸出。<code>scene_compute_layout</code> 先用 NULL 跑三次量出每個視圖多大，排好版面算出平移量；之後 <code>scene_render</code> 再用真的後端跑三次。同一段畫圖程式碼不用寫兩份，而且 SVG 與視窗共用同一個版面。（函式開頭另有一條捷徑：世界沒有承載面時不量測，直接回一個最小空版面。）</p>
  </div>
  <div data-panel='{"kind":"fn","name":"scene_compute_layout","from":"^    for \\(size_t v = 0; v < VIEW_COUNT; \\+\\+v\\) \\{","to":"layout->total_h","label":"scene_compute_layout 的量測與排版段落","callouts":[{"match":"scene_draw_view\\(NULL, &layout->bounds\\[v\\], &VIEW_FRAMES\\[v\\], scene\\);","note":"第一趟：target = NULL，只量邊界。"},{"match":"前視圖與仰視圖的畫面 x 都是房間 X","note":"對齊規則直接來自框架：畫面軸相同的兩個視圖就共用那個範圍。"},{"match":"layout->ty\\[VIEW_BOTTOM\\] = front_h \\+ GAP - bottom->min_y;","note":"第三角法：仰視圖的觀者在下方，所以放在前視圖下面。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"emit_svg_three_views","from":"DrawTarget target = SVG_TARGET;","to":"return fclose","label":"SVG 後端：接上函式表","callouts":[{"match":"target\\.ctx = out;","note":"函式表 SVG_TARGET 是檔案層常數，只有 ctx（這次的 FILE*）每次呼叫才綁；表裡的 polygon 就是 fprintf 一個 &lt;polygon&gt;。"},{"match":"scene_render\\(&target, layout, scene\\);","note":"之後幾何層接手，SVG 後端只被動接電話。"}]}'></div>
  <figure>
    <div id="svgOut"></div>
    <figcaption>程式實際輸出的 current_geometry.svg，內嵌於本頁。</figcaption>
  </figure>
</section>

<section class="block" id="s8">
  <div class="eyebrow mono">§8 · 主程式</div>
  <h2 class="sec">資料流的逐字翻譯，加一座實驗台</h2>
  <div class="prose">
    <p><code>main</code> 就是 §0 那條資料流一步一步寫下來，每一步失敗就印錯誤、回傳 1。它自己不再組場景：世界要嘛來自 <code>--scene</code> 場景檔，要嘛來自內建預設世界。下面只節錄場景來源與輸出 SVG 兩段。</p>
  </div>
  <div data-panel='{"kind":"fn","name":"main","from":"--scene：幾何改從場景檔讀","to":"場景裡沒有任何物件","label":"main：場景來源——場景檔或內建預設","callouts":[{"match":"if \\(!parse_scene_file\\(scene_path, &world\\)\\) \\{","note":"--scene：整份場景檔走逐行套用，讀完再總檢查（§10）。"},{"match":"reference_default_world\\(&world\\)","note":"沒給 --scene 就用內建預設世界（定義在 geometry-core/transactions.inc，web bridge 開機也用同一份）。"},{"match":"場景裡沒有任何物件","note":"兩條路徑之後只讀 world，輸出層不分來源。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"main","from":"純 C 輸出三視圖 SVG","to":"^\\}$","label":"main：輸出 SVG，再開視窗","callouts":[{"match":"scene_from_world\\(&world\\)","note":"World 是事實來源，繪圖層只拿指標組 Scene。"},{"match":"if \\(!scene_compute_layout\\(&scene, &layout\\)\\) \\{","note":"版面只算一次，SVG 與視窗共用。"},{"match":"path_beside_source\\(","note":"路徑由 __FILE__ 推導，SVG 固定落在 .c 旁邊。"},{"match":"if \\(!gdi_show_three_views\\(&world\\)\\) \\{","note":"第二層：開視窗。把 World 交進去——互動指令會改它。--no-window 可跳過。"}]}'></div>

  <h3>放置實驗台</h3>
  <div class="prose">
    <p>這座實驗台用 JavaScript 重寫了 <code>timber_place_a0_on_surface</code> 與三視圖的「最近面」判斷，邏輯逐行對應 C。改參數，看程式會接受還是拒絕、角材落在哪裡、每個視圖標哪個面。</p>
  </div>
  <div class="bench">
    <div class="ctl">
      <label>表面 max_u（天花板 U 方向長度）<input id="bMaxU" type="number" value="4000" step="100"></label>
      <label>表面 max_v<input id="bMaxV" type="number" value="3000" step="100"></label>
      <label>錨點 u<input id="bU" type="number" value="500" step="10"></label>
      <label>錨點 v<input id="bV" type="number" value="300" step="10"></label>
      <label>角材長度 L<input id="bL" type="number" value="1800" step="100"></label>
      <label>長度方向
        <select id="bDir">
          <option value="POS_U">SURFACE_DIRECTION_POS_U</option>
          <option value="NEG_U">SURFACE_DIRECTION_NEG_U</option>
          <option value="POS_V">SURFACE_DIRECTION_POS_V</option>
          <option value="NEG_V">SURFACE_DIRECTION_NEG_V</option>
        </select>
      </label>
      <label>B 尺寸方向
        <select id="bDepth">
          <option value="POS">SURFACE_DEPTH_POSITIVE_NORMAL</option>
          <option value="NEG">SURFACE_DEPTH_NEGATIVE_NORMAL</option>
        </select>
      </label>
    </div>
    <div class="out" id="bOut"></div>
  </div>

  <h3>三個建議實驗</h3>
  <div class="exp">
    <article>
      <h4>1. 把 max_u 改成 2000</h4>
      <p>角材長 1800 從 u = 500 起算會到 2300，超出表面。放置那步應該拒絕：對角點 (2300, 327) 超出 max_u，整個 A0 面就不在表面內。</p>
    </article>
    <article>
      <h4>2. 長度方向改成 POS_V</h4>
      <p>看 A 軸怎麼被叉積自動算出來：Z × Y = (−1, 0, 0)。角材在仰視圖轉了 90 度，從 v = 300 往 +Y 延伸到 2100，寬度往 −X 佔 473 到 500。</p>
    </article>
    <article>
      <h4>3. B 尺寸改成 NEGATIVE</h4>
      <p>角材掉到天花板下方，Z 變成 2467 到 2500。仰視圖最近的面從 A0 換成 A1，因為往上看的人現在先看到比較低的 A1。</p>
    </article>
  </div>
</section>

<section class="block" id="s9">
  <div class="eyebrow mono">§9 · 第二層：作業系統視窗</div>
  <h2 class="sec">不裝任何庫，只靠 Windows 自帶的 user32 與 gdi32</h2>
  <div class="prose">
    <p>C 標準庫碰不到螢幕，螢幕是作業系統的財產。所以「不靠庫開視窗」最誠實的做法是直接呼叫作業系統：Windows 上就是 <code>windows.h</code>，每台機器都有，MSVC 也附帶標頭檔。所有 GUI 庫最底下都在做同一件事。這一段用 <code>#ifdef _WIN32</code> 包起來，其他平台編譯時整段消失。</p>
    <p>讀它抓三個觀念，換成任何 GUI 庫都一樣：<b>事件迴圈</b>、<b>回呼函式</b>、<b>只在 WM_PAINT 裡畫</b>。</p>
    <p>這一層也是「語言為體、GUI 為殼」的落點：視窗下方的輸入列收下的一行指令，交給的是與場景檔<b>同一個</b> <code>apply_scene_line()</code>；滑鼠拖曳參考線，實際做的是把落點交給 <code>reference_snap</code> 對到最近的合法引用式、組出一行 <code>move</code> 指令，走的也是同一條路。UI 從頭到尾沒有直接寫過 <code>World</code> 的任何欄位——它能做的，不會超過 DSL 能說的。</p>
  </div>
  <div data-panel='{"kind":"fn","name":"gdi_show_three_views","label":"開視窗：註冊、建立、事件迴圈","callouts":[{"match":"wc\\.lpfnWndProc = gdi_window_proc;","note":"回呼函式：把自己的函式交給作業系統，之後由它來呼叫你。"},{"match":"HWND window = CreateWindowW\\(","note":"建立視窗。最後一個參數把場景與版面傳進去，WM_CREATE 會拿到。"},{"match":"while \\(GetMessageW\\(&msg, NULL, 0, 0\\) > 0\\) \\{","note":"事件迴圈：程式的心臟。作業系統把滑鼠、鍵盤、重繪要求排進佇列，這裡一則一則取出。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"gdi_window_proc","label":"回呼函式：作業系統打電話進來","callouts":[{"match":"case WM_CREATE: \\{","note":"視窗剛建立：把 CreateWindow 傳進來的指標掛在視窗上。"},{"match":"case WM_PAINT: \\{","note":"只有這裡畫圖。被遮住再露出、被拉大，作業系統都會再送一次 WM_PAINT。"},{"match":"app->mem_dc = CreateCompatibleDC\\(dc\\);","note":"離屏緩衝：先畫到記憶體再一次貼上，避免閃爍。DC 與位圖建在 GdiApp 上重用，尺寸變了才重建。"},{"match":"gdi_app_release_objects\\(app\\);","note":"關窗時統一釋放：離屏位圖、記憶體 DC、快取裡的筆刷與字型。"},{"match":"case WM_DESTROY:","note":"視窗關了就讓 GetMessage 回傳 0，事件迴圈結束，main 返回。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"gdi_paint","label":"視窗後端：離屏緩衝 → 共用走訪 → 疊 hover","callouts":[{"match":"gdi_view_transform\\(app, draw, &g\\.scale","note":"mm → 像素的比例：先 fit（整個版面塞進視窗，取較小的那個方向），再疊使用者的 zoom 與 pan。滑鼠逆投影用同一組參數。"},{"match":"scene_draw_pick\\(&target, &app->layout, &app->scene, show\\);","note":"幾何走訪與 SVG 後端同一條路，再疊一層 hover 高亮——渲染狀態，不動 domain。"}]}'></div>
  <div data-panel='{"kind":"type","name":"GdiObjectCache","label":"GDI 物件快取：筆、刷、字型","callouts":[{"match":"HPEN pens\\[STYLE_COUNT\\];","note":"DrawStyle 是封閉 enum，直接當索引——第一次用到才 CreatePen，之後每幀只是查表。"},{"match":"size_t font_count;","note":"字型以（像素、粗細、旋轉）為鍵，固定上限 16 個，視窗關閉時統一 DeleteObject。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"gdi_text","from":"int rotate10 = -rotate_degrees","to":"TextOutW","label":"文字：UTF-8 轉 UTF-16，旋轉靠字型的 escapement","callouts":[{"match":"int rotate10 = -rotate_degrees \\* 10;","note":"GDI 沒有「旋轉文字」指令，旋轉是字型的屬性，單位 0.1 度、逆時針為正。SVG 的 rotate(−90) 對應 900。"},{"match":"cache->fonts\\[i\\]\\.px == px &&","note":"命中快取就直接拿舊字型——CreateFontW 是系統呼叫，實測佔每幀成本的大頭。"}]}'></div>
  <div class="key"><b>效能實測（<code>--bench 2000</code>）：</b>每幀重建所有 GDI 物件約 3.8ms，快取重用約 2.5ms——省三分之一。大頭不是位圖，是每個圖元的 CreatePen/CreateSolidBrush/CreateFontW。快取只住在 UI 層（<code>GdiApp</code>），domain 一行沒動。</div>
  <div class="key"><b>代價：</b>GDI 只有 2D，沒有半透明，只在 Windows 上跑。實際長出的第三層是網頁——<code>geometry-web/web_bridge.c</code> 把同一套 DrawTarget 走訪序列化成 JSON ops 串流，瀏覽器端照著畫。要 3D 互動或原生跨平台，raylib 這類純 C 庫仍是最短的路：幾何層與 <code>DrawTarget</code> 介面不用改，再寫一個後端就好。</div>
</section>

<section class="block" id="s10">
  <div class="eyebrow mono">§10 · 場景檔：組成抽到程式外</div>
  <h2 class="sec">十八列指令的文字檔，就是這個 domain 目前全部能說的話</h2>
  <div class="prose">
    <p>前面所有範例的結構都寫死在 main 裡。這一層把它抽出去：<code>--scene</code> 接一份文字檔，一行一個指令，由上而下套用。指令表現在有十八列：宣告用的 <code>spec</code>、<code>boundary</code>、<code>placement</code>、<code>surface</code>（邊界＋承載面合體）、<code>space</code>、<code>datum</code>、<code>column</code>、<code>beam</code>、<code>timber</code>；依附承載面的 <code>guide</code>、<code>grid</code>、<code>place</code>；操作動詞 <code>move</code>、<code>apply-proj</code>、<code>delete</code>、<code>reset</code>、<code>canvas-pos</code>；外加一列墓碑 <code>span-auto</code>（已廢除，寫了會被明確拒絕）。場景檔寫不出這十八列以外的行為，也寫不出非單位軸的向量（軸只有 ±x ±y ±z 六個詞）；「封閉行為集合」在這裡是字面的事實。</p>
    <p>邊界面可以有好幾片：<code>boundary</code>／<code>placement</code>（或合體的 <code>surface</code>）寫幾次就有幾片（上限 <code>WORLD_MAX_BOUNDARIES</code> = 16），牆、地板、天花板各是一片，直立角材就是「貼在直立的面上」。<code>place</code> 因此必須明寫 <code>on 承載面id</code>——貼在哪片不再是隱含的。參考線與錨點都各自記著 <code>placement_id</code>，誰屬於誰是資料裡的事實，不是靠順序猜。</p>
    <p>id 要先宣告才能被引用，所以「place 寫在 timber 前面」自然變成「id 不存在」，不必另外規定。錯誤不直接印 stderr，而是寫進 domain 層的錯誤緩衝，檔案路徑與視窗輸入列讀的是同一份——拒絕的理由到哪一層都是同一個字串。合法的場景檔與內建預設世界共用同一個 <code>World</code>，輸出層完全不分來源。同目錄的 <code>room_a.scene</code> 是現行語法的完整範例：合體的 <code>surface</code>、具名 <code>spec</code> 引用、at-face 與 at-line 兩族錨法都在裡面。</p>
    <p><code>move</code> 有一條已拍板的語義（公理層 R2，2026-09-18 反轉）：移動參考線<b>要</b>重放引用它的角材——錨點存的是引用不是座標，引用的語意就是跟著動。中線與長度重新推導，先走 I8a 影響預覽，零違規且確認才提交，失敗整筆回滾。</p>
  </div>
  <div data-panel='{"kind":"type","name":"World","label":"一份場景的全部狀態","callouts":[{"match":"SpaceBoundarySurface boundaries\\[WORLD_MAX_BOUNDARIES\\];","note":"邊界面與承載面分兩個陣列：boundary 是純 2D 輪廓，placement 帶 3D frame。"},{"match":"TimberAnchor anchors\\[WORLD_MAX_TIMBERS\\];","note":"錨點帶著 placement_id——UV 座標離開它所屬的承載面就沒有意義。"},{"match":"Timber timbers\\[WORLD_MAX_TIMBERS\\];","note":"上限是常數，不做動態配置——寫不下的場景在解析時就被拒絕。"}]}'></div>
  <div data-panel='{"kind":"range","title":"SCENE_COMMANDS 指令表","from":"\\} SCENE_COMMANDS\\[\\] = \\{","to":"^\\};","label":"指令表：欄位數與前置條件集中在同一列","callouts":[{"match":"\"boundary\", 6, SCENE_MAX_TOKENS, false,","note":"欄位數是 min～max 區間（含指令本身）與「要先有承載面」寫在表裡，apply_ 函式就不必各自檢查一次。"},{"match":"\"place\", 8, 16, true,","note":"錨法有兩族：at-line（guide 參考線，或 grid 網格的 u|v 索引）與 at-face（e 外環邊／h 孔邊／t 既有角材面），可再加 through 選段或 between 兩個擋面。"},{"match":"\"move\", 3, SCENE_MAX_TOKENS, true,","note":"move 的新位置是引用式，不是寫死的數字；拖曳參考線與鍵入 move 走到同一個 apply_——GUI 只是另一種輸入法。"}]}'></div>
  <div data-panel='{"kind":"range","title":"place / move：交給引用層","from":"^static bool apply_place_line\\(","to":"^\\{ return apply_reference_move\\(","label":"place / move：交給引用層","callouts":[{"match":"return apply_reference_place\\(","note":"place 整段交給引用層（geometry-core/references.inc）：錨點存的是引用定義，不是當場算好的座標；本頁只內嵌 current_geometry.c，實作不在這裡展開。"},{"match":"R4: span-auto 已廢除","note":"舊保存標記明確拒絕，不讓它被誤讀成新的引用定義。"},{"match":"return apply_reference_move\\(","note":"move 同樣交給引用層：改的是參考線的位置引用式，接著由 reference_checked 重驗整個世界；共用基準的參考線不能在本地移動（R5）。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"parse_scene_file","label":"逐行套用，讀完再總檢查","callouts":[{"match":"FILE \\*in = fopen\\(path, \"rb\"\\);","note":"二進位模式：換行與 BOM 都自己處理，Windows 的文字模式不介入。"},{"match":"!out_world->timbers\\[i\\]\\.placed","note":"讀完檔再掃一次：沒 place 的角材印不出也畫不出，一定是場景檔漏寫。"}]}'></div>
  <div class="key"><b>設計上最重要的一行註解：</b>「軸只有六種寫法，所以場景檔根本寫不出非單位、非軸向的向量。」錯誤的輸入不是被檢查出來，是<b>構造不出來</b>——這就是公理作為根源的意思。</div>
</section>

<section class="block" id="s11">
  <div class="eyebrow mono">§11 · 數學：公式與隱形的矩陣</div>
  <h2 class="sec">程式裡沒有 matrix 型別，但有三個隱形矩陣</h2>
  <div class="prose">
    <p>這份程式刻意不寫矩陣型別——整數幾何下每個「矩陣乘法」都攤開成分量相加，效果相同、可逐行審查。但它確實用了三個矩陣，只是它們活在結構的欄位裡：</p>
  </div>

  <h3 style="margin:22px 0 6px">矩陣一：座標變換 M = [ U | V | N ]（3×3）</h3>
  <div class="prose">
    <p><code>SurfaceFrame</code> 的三個軸擺成直欄就是一個 3×3 矩陣。<code>surface_point_to_room</code> 做的事字面上就是仿射變換：</p>
  </div>
  <div class="formula">room = M · (u, v, w)ᵀ + origin
     = origin + u·U + v·V + w·N</div>
  <div class="prose">
    <p>角材的框架是同一個矩陣（<code>timber_local_to_room</code> 完全同構）。「框架合法」=<b>M 是正交矩陣且右手向</b>：<code>surface_frame_is_valid</code> 檢查的 |U|=|V|=1、U⊥V、U×V=N，正是正交矩陣的定義。軸只能是 ±X/±Y/±Z 六種單位向量，所以 M 實際上是「24 種軸對齊旋轉」之一——任意旋轉在這個 domain 裡構造不出來。</p>
  </div>

  <h3 style="margin:22px 0 6px">矩陣二：正交投影 P = [ right ; down ]（2×3）</h3>
  <div class="prose">
    <p><code>ViewFrame</code> 的兩個方向向量擺成橫列就是投影矩陣。<code>view_project</code> 是兩次點積：</p>
  </div>
  <div class="formula">view = P · p   →   x = p·right,  y = p·down</div>
  <div class="prose">
    <p>三視圖 = 三個不同的 P（前視 X/Z、側視 Y/Z、仰視 X/Y）。這是丟掉深度的正交投影——丟掉的那個方向 into = right × down 沒有浪費，正好拿來畫遠近排序。</p>
  </div>

  <h3 style="margin:22px 0 6px">矩陣三：反解 A = P · [ U | V ]（2×2）</h3>
  <div class="prose">
    <p>滑鼠反向查詢要把視圖座標解回表面 (u,v)：兩個未知數、兩條方程式。實際動手解的是 <code>view_unproject_on_surface_near</code>——裡面的 a, b, c, d 不是憑空的，它們是「先變換再投影」的複合，也就是 <b>P 乘上 M 的前兩欄</b>：</p>
  </div>
  <div class="formula">A = [ U·right  V·right ]      det = a·d − b·c
    [ U·down   V·down  ]
u = (e·d − b·f) / det      v = (a·f − e·c) / det     （Cramer 法則）</div>
  <div class="prose">
    <p>同一個反解拆成兩版。<code>_near</code> 是容差版，給畫布滑鼠用：Cramer 的商用 <code>llround</code> 四捨五入到最近的整數 mm，滑鼠不必剛好落在整數點上；<code>det = 0</code> 仍是表面在此視圖退化成一條線，無解。嚴格版 <code>view_unproject_on_surface</code> 先借 near 解出候選 (u,v)，再<b>代回原方程式驗算</b>——答案必須讓 a·u + b·v 恰好等於 e，差 1mm 都拒絕。整數 domain 的「不猜」一路守到反解，只是守的方式從整除檢查換成代回驗算。</p>
  </div>
  <div data-panel='{"kind":"fn","name":"view_unproject_on_surface_near","label":"容差反解：Cramer + llround（給滑鼠）","callouts":[{"match":"Coord det = a \\* d - b \\* c;","note":"det = 0 → 表面在此視圖是一條線，無解。"},{"match":"llround\\(u_num / \\(double\\)det\\)","note":"商四捨五入到最近整數 mm——滑鼠不必精準落在整數點。幾何層唯一的浮點在這裡。"}]}'></div>
  <div data-panel='{"kind":"fn","name":"view_unproject_on_surface","label":"嚴格版：near 解完再代回驗算","callouts":[{"match":"view_unproject_on_surface_near\\(view, surface, p, out_uv\\)","note":"先借容差版解出候選 (u,v)，det = 0 一樣當場拒絕。"},{"match":"a \\* out_uv->u \\+ b \\* out_uv->v == e","note":"代回原方程式：候選必須精確滿足才收——四捨五入產生的近似在這關被擋掉。"}]}'></div>

  <h3 style="margin:22px 0 6px">其餘公式一覽</h3>
  <table class="ftab">
    <tr><th>公式</th><th>函式</th><th>用途</th></tr>
    <tr><td>a·b = Σ aᵢbᵢ</td><td><code>vector_dot</code> / <code>point_along</code></td><td>|a|²=1 檢查、正交檢查、取向量在某軸上的分量</td></tr>
    <tr><td>a×b</td><td><code>vector_cross</code></td><td>N=U×V、右手系檢查、角材 A 軸 = B×L、邊的側向法線</td></tr>
    <tr><td>2·面積 = Σ(xᵢ·yⱼ − xⱼ·yᵢ)</td><td><code>view_quad_area2</code></td><td>shoelace 公式：判斷面在此視圖是否退化成線</td></tr>
    <tr><td>sign(邊ᵢ × (p−vᵢ)) 全同號</td><td><code>view_quad_contains</code></td><td>凸四邊形包含測試——滑鼠命中的幾何核心</td></tr>
    <tr><td>t = (p−a)·(b−a) / |b−a|²</td><td><code>view_dist2_to_segment</code></td><td>點到線段距離²（夾 t 進 [0,1]，整數除法版）</td></tr>
    <tr><td>u = v_線.offset, v = u_線.offset</td><td><code>guide_line_intersection</code></td><td>兩條參考線交點——兩行就解完</td></tr>
    <tr><td>d₄ = Σᵢ vᵢ·into</td><td><code>timber_project_faces</code></td><td>六面依「離觀者深度」排序（painter's algorithm）</td></tr>
    <tr><td>槽位 + 區間約束</td><td><code>room_bind</code></td><td>room 一致性：每片面釘住一個法向槽位與兩個軸區間</td></tr>
    <tr><td>px = origin + (mm + t)·scale</td><td><code>gdi_to_pixel</code></td><td>mm → 像素——全域唯二的浮點之一，另一處是上面 _near 反解的 llround</td></tr>
  </table>

  <div data-panel='{"kind":"fn","name":"view_quad_contains","label":"點在凸四邊形內：四邊叉積同號","callouts":[{"match":"Coord cross =","note":"每條邊的有向叉積：p 在邊的哪一側。"},{"match":"else if \\(s != sign\\)","note":"出現異號 → 點在四邊形外。叉積為 0 表示點在邊上，不算出局。"}]}'></div>

  <div class="key"><b>為什麼沒有 matrix 型別：</b>三個矩陣都是軸對齊（元素只有 0 與 ±1），展開成分量比通用矩陣乘法更短、更可讀，也不會引入浮點。哪天要支援斜面或非軸向框架，才值得把 M 真的寫出來。</div>
</section>

<section class="block full" id="src">
  <div class="eyebrow mono">全文</div>
  <h2 class="sec">完整原始碼</h2>
  <div class="prose"><p>每一行都有錨點，例如 <a href="#L193">#L193</a>。上面各面板標題右側的行號也會跳到這裡。<button class="copy" id="copySrc" type="button">複製完整原始碼</button></p></div>
  <div class="panel" id="fullPanel"><pre id="fullPre"></pre></div>
</section>

</main>
</div>

<script>
const SRC = __SOURCE__;
const SVG_OUT = __SVG__;
const LINES = SRC.split("\n");

/* ---------- 語法上色 ---------- */
const KEYWORDS = new Set("auto break case char const continue default do double else enum extern float for goto if inline int long register return short signed sizeof static struct switch typedef union unsigned void volatile while bool true false NULL".split(" "));
const TYPES = new Set(["int64_t","uint32_t","int32_t","uint8_t","size_t","FILE","Coord"]);
for (const m of SRC.matchAll(/^\} (\w+);/gm)) TYPES.add(m[1]);
for (const m of SRC.matchAll(/^typedef \w+ (\w+);/gm)) TYPES.add(m[1]);

function esc(s) { return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

const HILITED = (() => {
  const out = [];
  let inComment = false;
  const tok = /\/\*[\s\S]*?\*\/|\/\*.*$|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|^\s*#.*$|\b\d+\b|\b[A-Za-z_]\w*(?=\s*\()|\b[A-Za-z_]\w*\b|[\s\S]/g;
  for (const line of LINES) {
    let html = "";
    let rest = line;
    if (inComment) {
      const end = rest.indexOf("*/");
      if (end < 0) { out.push('<span class="cm">' + esc(rest) + "</span>"); continue; }
      html += '<span class="cm">' + esc(rest.slice(0, end + 2)) + "</span>";
      rest = rest.slice(end + 2);
      inComment = false;
    }
    tok.lastIndex = 0;
    for (const m of rest.matchAll(tok)) {
      const t = m[0];
      if (t.startsWith("/*")) {
        html += '<span class="cm">' + esc(t) + "</span>";
        if (!t.endsWith("*/")) inComment = true;
      } else if (t.startsWith('"') || t.startsWith("'")) html += '<span class="st">' + esc(t) + "</span>";
      else if (/^\s*#/.test(t)) html += '<span class="pp">' + esc(t) + "</span>";
      else if (/^\d+$/.test(t)) html += '<span class="nu">' + t + "</span>";
      else if (KEYWORDS.has(t)) html += '<span class="kw">' + t + "</span>";
      else if (TYPES.has(t)) html += '<span class="ty">' + t + "</span>";
      else if (/^[A-Za-z_]\w*$/.test(t) && /^\s*\(/.test(rest.slice(m.index + t.length)) && !KEYWORDS.has(t)) html += '<span class="fn">' + t + "</span>";
      else html += esc(t);
    }
    out.push(html);
  }
  return out;
})();

/* ---------- 由符號名抽出範圍（0-based, 含頭尾） ---------- */
function withLeadingComment(start) {
  let i = start - 1;
  if (i >= 0 && LINES[i].trim() === "*/") {
    while (i > 0 && !LINES[i].startsWith("/*")) i--;
    return i;
  }
  if (i >= 0 && /^\/\*.*\*\/\s*$/.test(LINES[i])) return i;
  return start;
}
function findFunction(name) {
  const re = new RegExp("^(static|int)\\b[^\\n]*\\b" + name + "\\(");
  for (let i = 0; i < LINES.length; i++) {
    if (!re.test(LINES[i])) continue;
    // 前置宣告：簽名在遇到 "{" 之前就以 ";" 結尾，跳過、找下一個。
    let open = i;
    while (open < LINES.length && LINES[open] !== "{" && !/;\s*$/.test(LINES[open])) open++;
    if (open >= LINES.length || LINES[open] !== "{") continue;
    let close = open + 1; while (close < LINES.length && LINES[close] !== "}") close++;
    return { start: withLeadingComment(i), end: close };
  }
  return null;
}
function findTypedef(name) {
  const i = LINES.findIndex(l => l === "} " + name + ";");
  if (i < 0) return null;
  let t = i; while (t > 0 && !LINES[t].startsWith("typedef")) t--;
  return { start: withLeadingComment(t), end: i };
}
function findSection(title) {
  const i = LINES.findIndex((l, k) => l === " * " + title && k > 0 && LINES[k - 1].startsWith("/* ===="));
  if (i < 0) return null;
  let s = i + 2;
  let e = s;
  while (e < LINES.length && !LINES[e].startsWith("/* ====")) e++;
  e--;
  while (e > s && LINES[e].trim() === "") e--;
  while (s < e && LINES[s].trim() === "") s++;
  return { start: s, end: e };
}
function narrow(range, from, to) {
  if (!range) return range;
  let s = range.start, e = range.end;
  if (from) { const rf = new RegExp(from); for (let i = s; i <= e; i++) if (rf.test(LINES[i])) { s = i; break; } }
  if (to) { const rt = new RegExp(to); for (let i = s + 1; i <= e; i++) if (rt.test(LINES[i])) { e = i; break; } }
  return { start: s, end: e };
}

/* ---------- 複製 ---------- */
async function copyText(text, btn) {
  const orig = btn.textContent;
  let ok = false;
  try {
    await navigator.clipboard.writeText(text);
    ok = true;
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    try { ok = document.execCommand("copy"); } catch {}
    ta.remove();
  }
  btn.textContent = ok ? "已複製" : "複製失敗";
  setTimeout(() => { btn.textContent = orig; }, 1600);
}
document.addEventListener("click", (e) => {
  const btn = e.target.closest("button.copy");
  if (!btn) return;
  const text = btn.id === "copySrc"
    ? SRC
    : LINES.slice(+btn.dataset.s, +btn.dataset.e + 1).join("\n");
  copyText(text, btn);
});

/* ---------- 面板 ---------- */
const MARKS = "①②③④⑤⑥⑦⑧⑨";
function renderPanel(el) {
  const cfg = JSON.parse(el.getAttribute("data-panel"));
  let range = null;
  if (cfg.kind === "fn") range = findFunction(cfg.name);
  else if (cfg.kind === "type") range = findTypedef(cfg.name);
  else if (cfg.kind === "section") range = findSection(cfg.title);
  else if (cfg.kind === "range") range = { start: 0, end: LINES.length - 1 };
  range = narrow(range, cfg.from, cfg.to);

  const sym = cfg.label || cfg.name || cfg.title;
  if (!range) {
    el.innerHTML = '<div class="panel"><header><span class="sym">' + esc(sym) + '</span></header><div class="miss">在目前的原始碼裡找不到「' + esc(cfg.name || cfg.title) + '」。重跑 make_guide.py 或更新面板設定。</div></div>';
    return;
  }
  const callouts = cfg.callouts || [];
  const hit = new Map();
  callouts.forEach((c, idx) => {
    const re = new RegExp(c.match);
    for (let i = range.start; i <= range.end; i++) {
      if (re.test(LINES[i]) && !hit.has(i)) { hit.set(i, idx); break; }
    }
  });
  let rows = "";
  for (let i = range.start; i <= range.end; i++) {
    const idx = hit.get(i);
    rows += '<div class="row' + (idx !== undefined ? " hl" : "") + '"><span class="mk">' + (idx !== undefined ? MARKS[idx] : "") + '</span><span class="ln">' + (i + 1) + '</span><span class="lc">' + (HILITED[i] || "&nbsp;") + "</span></div>";
  }
  const loc = "第 " + (range.start + 1) + " 到 " + (range.end + 1) + " 行";
  el.innerHTML =
    '<div class="panel"><header><span class="sym">' + esc(sym) + '</span><span class="loc"><a href="#L' + (range.start + 1) + '">' + loc + '</a> <button class="copy" data-s="' + range.start + '" data-e="' + range.end + '" type="button">複製</button></span></header><pre>' + rows + "</pre></div>" +
    (callouts.length ? '<ul class="notes">' + callouts.map((c, idx) => "<li><b>" + MARKS[idx] + "</b><span>" + esc(c.note) + (hit.has ? "" : "") + "</span></li>").join("") + "</ul>" : "");
}
document.querySelectorAll("[data-panel]").forEach(renderPanel);

/* ---------- 全文 ---------- */
(() => {
  let rows = "";
  for (let i = 0; i < LINES.length; i++) {
    rows += '<div class="row" id="L' + (i + 1) + '"><span class="mk"></span><span class="ln">' + (i + 1) + '</span><span class="lc">' + (HILITED[i] || "&nbsp;") + "</span></div>";
  }
  document.getElementById("fullPre").innerHTML = rows;
})();

/* ---------- SVG 輸出內嵌 ---------- */
document.getElementById("svgOut").innerHTML = SVG_OUT.replace(/<\?xml[^>]*\?>/, "");

/* ---------- 心智模型示意圖 ---------- */
(() => {
  const svg = document.getElementById("mentalModel");
  const S = 0.12;                       // mm → px
  const ox = 120, oy = 400;             // 房間原點的螢幕位置
  const P = (x, y, z) => [ox + (x + 0.5 * y * 0.7071) * S, oy - (z + 0.5 * y * 0.7071) * S];
  const poly = (pts, attrs) => "<polygon points=\"" + pts.map(p => P(...p).map(v => v.toFixed(1)).join(",")).join(" ") + "\" " + attrs + "/>";
  const line = (a, b, attrs) => { const [x1, y1] = P(...a), [x2, y2] = P(...b); return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" ${attrs}/>`; };
  const text = (p, t, attrs, dx = 0, dy = 0) => { const [x, y] = P(...p); return `<text x="${x + dx}" y="${y + dy}" ${attrs}>${t}</text>`; };
  const ink = "var(--ink-2)", blue = "var(--blue)", tim = "var(--timber)", red = "var(--guide)";
  const W = 4000, D = 3000, H = 2500;
  let s = "";
  // 房間：地板、天花線框
  s += poly([[0,0,0],[W,0,0],[W,D,0],[0,D,0]], `fill="none" stroke="${ink}" stroke-dasharray="4 4" stroke-width="1"`);
  for (const [x, y] of [[0,0],[W,0],[W,D],[0,D]]) s += line([x,y,0],[x,y,H], `stroke="${ink}" stroke-dasharray="4 4" stroke-width="1"`);
  // 房間軸
  s += line([0,0,0],[1200,0,0], `stroke="${ink}" stroke-width="2"`); s += text([1200,0,0], "X", `fill="${ink}" font-size="13"`, 6, 4);
  s += line([0,0,0],[0,1500,0], `stroke="${ink}" stroke-width="2"`); s += text([0,1500,0], "Y（向房間深處）", `fill="${ink}" font-size="13"`, 6, -4);
  s += line([0,0,0],[0,0,1000], `stroke="${ink}" stroke-width="2"`); s += text([0,0,1000], "Z", `fill="${ink}" font-size="13"`, -14, 0);
  s += text([0,0,0], "房間原點 (0,0,0)", `fill="${ink}" font-size="12"`, -20, 18);
  // 天花板表面
  s += poly([[0,0,H],[W,0,H],[W,D,H],[0,D,H]], `fill="${blue}" fill-opacity="0.15" stroke="${blue}" stroke-width="1.8"`);
  s += text([W,D,H], "空間邊界面：天花板 z = 2500，U = [0,4000]，V = [0,3000]", `fill="${blue}" font-size="12.5" text-anchor="end"`, 0, -8);
  s += line([0,0,H],[900,0,H], `stroke="${blue}" stroke-width="2.5"`); s += text([900,0,H], "U", `fill="${blue}" font-size="13" font-weight="700"`, 6, 14);
  s += line([0,0,H],[0,900,H], `stroke="${blue}" stroke-width="2.5"`); s += text([0,900,H], "V", `fill="${blue}" font-size="13" font-weight="700"`, -14, -2);
  s += line([0,0,H],[0,0,H+500], `stroke="${blue}" stroke-width="2.5"`); s += text([0,0,H+500], "N", `fill="${blue}" font-size="13" font-weight="700"`, -14, 0);
  // 邊界角材：前後兩條邊各一支（at-face e0、e2），厚度放大 6 倍
  const T = 6, bw = 27 * T, z1 = H + 33 * T;
  for (const [e, ya, yb] of [["e0", 0, bw], ["e2", D - bw, D]]) {
    s += poly([[0,ya,z1],[W,ya,z1],[W,yb,z1],[0,yb,z1]], `fill="${tim}" fill-opacity="0.5" stroke="${tim}"`);
    s += poly([[0,ya,H],[W,ya,H],[W,ya,z1],[0,ya,z1]], `fill="${tim}" fill-opacity="0.6" stroke="${tim}"`);
    s += poly([[0,yb,H],[W,yb,H],[W,yb,z1],[0,yb,z1]], `fill="${tim}" fill-opacity="0.6" stroke="${tim}"`);
    s += text([W,(ya+yb)/2,z1], "邊界角材 at-face " + e, `fill="${tim}" font-size="12" text-anchor="end"`, -8, -4);
  }
  // 主支角材：at-line 貼在 guide 1 上、沿 +V，跨 v = 27 → 2973（厚度同樣放大）
  const x0 = 500, x1 = 500 + bw, y0 = bw, y1 = D - bw;
  s += poly([[x0,y0,z1],[x0,y1,z1],[x1,y1,z1],[x1,y0,z1]], `fill="${tim}" fill-opacity="0.55" stroke="${tim}"`);
  s += poly([[x0,y0,H],[x0,y1,H],[x0,y1,z1],[x0,y0,z1]], `fill="${tim}" fill-opacity="0.8" stroke="${tim}"`);
  s += poly([[x0,y0,H],[x1,y0,H],[x1,y0,z1],[x0,y0,z1]], `fill="${tim}" fill-opacity="0.35" stroke="${tim}"`);
  s += text([x0,y0,H], "主支 at-line guide 1：+v，跨 v = 27→2973", `fill="${tim}" font-size="12"`, -4, 18);
  s += text([x1,y0+700,z1], "角材 27 × 33（厚度放大 6 倍）", `fill="${tim}" font-size="12"`, 8, -6);
  s += text([(x0+x1)/2,y0+700,z1], "A1", `fill="${tim}" font-size="12" font-weight="700" text-anchor="middle"`, 0, -6);
  // 參考線 guide 1：沿 V，位置 u = 500（spec:主支中線）；畫在主支之後才看得見
  s += line([500,0,H],[500,D,H], `stroke="${red}" stroke-width="1.6" stroke-dasharray="6 4"`);
  s += text([500,1500,H], "guide 1：u = 500（沿 V）", `fill="${red}" font-size="12" text-anchor="end"`, -12, 4);
  svg.innerHTML = s;
})();

/* ---------- UV → 房間 試算 ---------- */
(() => {
  const frame = { origin: [0,0,2500], u: [1,0,0], v: [0,1,0], n: [0,0,1] };
  const ids = ["cu","cv","cw"];
  const res = document.getElementById("cres");
  const upd = () => {
    const [u, v, w] = ids.map(id => Number(document.getElementById(id).value) || 0);
    const r = [0,1,2].map(k => frame.origin[k] + u*frame.u[k] + v*frame.v[k] + w*frame.n[k]);
    res.textContent = `room = (0,0,2500) + ${u}·(1,0,0) + ${v}·(0,1,0) + ${w}·(0,0,1) = (${r.join(", ")})`;
  };
  ids.forEach(id => document.getElementById(id).addEventListener("input", upd));
  upd();
})();

/* ---------- 放置實驗台：逐行對應 C ---------- */
(() => {
  const dot = (a, b) => a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
  const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
  const neg = v => v.map(x => -x);
  const frame = { origin: [0,0,2500], u: [1,0,0], v: [0,1,0], n: [0,0,1] };
  const toRoom = (u, v, w) => [0,1,2].map(k => frame.origin[k] + u*frame.u[k] + v*frame.v[k] + w*frame.n[k]);
  const A = 27, B = 33;
  const FACES = {
    A0: (l,a,b) => [[0,0,0],[0,a,0],[l,a,0],[l,0,0]],
    A1: (l,a,b) => [[0,0,b],[l,0,b],[l,a,b],[0,a,b]],
    B0: (l,a,b) => [[0,0,0],[l,0,0],[l,0,b],[0,0,b]],
    B1: (l,a,b) => [[0,a,0],[0,a,b],[l,a,b],[l,a,0]],
    START: (l,a,b) => [[0,0,0],[0,0,b],[0,a,b],[0,a,0]],
    END: (l,a,b) => [[l,0,0],[l,a,0],[l,a,b],[l,0,b]]
  };
  const VIEWS = {
    "仰視圖": { proj: p => [p[0], p[1]], depth: p => -p[2] },
    "前視圖": { proj: p => [p[0], -p[2]], depth: p => -p[1] },
    "側視圖": { proj: p => [p[1], -p[2]], depth: p => p[0] }
  };
  const area2 = q => { let s = 0; for (let i = 0; i < 4; i++) { const j = (i+1)%4; s += q[i][0]*q[j][1] - q[j][0]*q[i][1]; } return s; };
  const $ = id => document.getElementById(id);
  const out = $("bOut");

  function run() {
    const region = { min_u: 0, min_v: 0, max_u: Number($("bMaxU").value), max_v: Number($("bMaxV").value) };
    const anchor = { u: Number($("bU").value), v: Number($("bV").value) };
    const L = Number($("bL").value);
    const dir = $("bDir").value, depth = $("bDepth").value;
    const contains = p => p.u >= region.min_u && p.u <= region.max_u && p.v >= region.min_v && p.v <= region.max_v;

    if (!contains(anchor)) return fail("錨點不在表面範圍內（surface_contains_point 失敗）。");
    const axis_length = { POS_U: frame.u, NEG_U: neg(frame.u), POS_V: frame.v, NEG_V: neg(frame.v) }[dir];
    const axis_b = depth === "POS" ? frame.n : neg(frame.n);
    const axis_a = cross(axis_b, axis_length);
    const ldu = dot(axis_length, frame.u), ldv = dot(axis_length, frame.v);
    const adu = dot(axis_a, frame.u), adv = dot(axis_a, frame.v);
    const far = { u: anchor.u + L*ldu + A*adu, v: anchor.v + L*ldv + A*adv };
    const bad = contains(far) ? null : far;
    if (bad) return fail(`A0 面在錨點對角的那一點 (u=${bad.u}, v=${bad.v}) 超出表面範圍 U=[${region.min_u},${region.max_u}]，V=[${region.min_v},${region.max_v}]。程式會印「無法把角材 A0 面放到空間邊界面」並回傳 1。`);

    const origin = toRoom(anchor.u, anchor.v, 0);
    const local = (l, a, b) => [0,1,2].map(k => origin[k] + l*axis_length[k] + a*axis_a[k] + b*axis_b[k]);
    const faces = Object.entries(FACES).map(([name, f]) => ({ name, pts: f(L, A, B).map(p => local(...p)) }));
    const all = faces.flatMap(f => f.pts);
    const ext = k => [Math.min(...all.map(p => p[k])), Math.max(...all.map(p => p[k]))];
    const nearest = {};
    for (const [vn, V] of Object.entries(VIEWS)) {
      let best = null;
      for (const f of faces) {
        const q = f.pts.map(V.proj);
        if (area2(q) === 0) continue;
        const d = f.pts.reduce((s, p) => s + V.depth(p), 0);
        if (!best || d > best.d) best = { name: f.name, d };
      }
      nearest[vn] = best ? best.name : "—";
    }
    const vec = v => "(" + v.join(", ") + ")";
    const [xr, yr, zr] = [ext(0), ext(1), ext(2)];
    out.innerHTML =
      '<div class="verdict ok">放置成功（timber_place_a0_on_surface 回傳 true）</div>' +
      '<table><tr><th>項目</th><th>值</th></tr>' +
      `<tr><td>角材原點</td><td class="mono">${vec(origin)}</td></tr>` +
      `<tr><td>長度軸</td><td class="mono">${vec(axis_length)}</td></tr>` +
      `<tr><td>A 軸 = B × 長度</td><td class="mono">${vec(axis_a)}</td></tr>` +
      `<tr><td>B 軸</td><td class="mono">${vec(axis_b)}</td></tr>` +
      `<tr><td>整支範圍</td><td class="mono">X ${xr[0]}～${xr[1]}，Y ${yr[0]}～${yr[1]}，Z ${zr[0]}～${zr[1]}</td></tr>` +
      `<tr><td>仰視圖最近的面</td><td class="mono">${nearest["仰視圖"]}</td></tr>` +
      `<tr><td>前視圖最近的面</td><td class="mono">${nearest["前視圖"]}</td></tr>` +
      `<tr><td>側視圖最近的面</td><td class="mono">${nearest["側視圖"]}</td></tr>` +
      "</table>" + topView(region, anchor, faces);
  }
  function topView(region, anchor, faces) {
    const pad = 200;
    const w = region.max_u - region.min_u + pad*2, h = region.max_v - region.min_v + pad*2;
    let s = `<svg viewBox="${region.min_u - pad} ${region.min_v - pad} ${w} ${h}" role="img" aria-label="仰視圖">`;
    s += `<rect x="${region.min_u}" y="${region.min_v}" width="${region.max_u-region.min_u}" height="${region.max_v-region.min_v}" fill="var(--blue-soft)" stroke="var(--blue)" stroke-width="12"/>`;
    s += `<line x1="${region.min_u}" y1="${anchor.v}" x2="${region.max_u}" y2="${anchor.v}" stroke="var(--guide)" stroke-width="8" stroke-dasharray="60 30"/>`;
    s += `<line x1="${anchor.u}" y1="${region.min_v}" x2="${anchor.u}" y2="${region.max_v}" stroke="var(--guide)" stroke-width="8" stroke-dasharray="60 30"/>`;
    const f = faces.find(x => x.name === "A1");
    s += `<polygon points="${f.pts.map(p => p[0] + "," + p[1]).join(" ")}" fill="var(--timber)" fill-opacity="0.8" stroke="var(--timber)" stroke-width="10"/>`;
    s += `<circle cx="${anchor.u}" cy="${anchor.v}" r="40" fill="var(--guide)"/>`;
    s += "</svg>";
    return s;
  }
  function fail(msg) {
    out.innerHTML = '<div class="verdict bad">放置被拒絕</div><p>' + esc(msg) + "</p>";
  }
  ["bMaxU","bMaxV","bU","bV","bL","bDir","bDepth"].forEach(id => $(id).addEventListener("input", run));
  run();
})();

/* ---------- 導覽高亮與主題切換 ---------- */
(() => {
  const links = [...document.querySelectorAll("#nav a")];
  const secs = links.map(a => document.querySelector(a.getAttribute("href")));
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        links.forEach(a => a.classList.toggle("active", a.getAttribute("href") === "#" + e.target.id));
      }
    });
  }, { rootMargin: "-20% 0px -70% 0px" });
  secs.forEach(s => s && io.observe(s));

  const root = document.documentElement;
  document.getElementById("themeBtn").addEventListener("click", () => {
    const dark = root.getAttribute("data-theme") === "dark" ||
      (!root.getAttribute("data-theme") && matchMedia("(prefers-color-scheme: dark)").matches);
    root.setAttribute("data-theme", dark ? "light" : "dark");
  });
})();
</script>
</body>
</html>
"""


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    svg = SVG.read_text(encoding="utf-8") if SVG.exists() else "<p>尚未產生 current_geometry.svg，請先執行程式。</p>"
    html = (TEMPLATE
            .replace("__SOURCE__", js_string(source))
            .replace("__SVG__", js_string(svg))
            .replace("__LINES__", f"{source.count(chr(10)) + 1:,}"))
    OUT.write_text(html, encoding="utf-8", newline="\n")
    print(f"已輸出：{OUT}（{OUT.stat().st_size} bytes，原始碼 {source.count(chr(10)) + 1} 行）")


if __name__ == "__main__":
    main()
