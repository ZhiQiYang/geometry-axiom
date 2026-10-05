# -*- coding: utf-8 -*-
"""產生【合成】測試 PDF(手寫最小 PDF 語法,零相依)與 fixtures.md。
這些檔案是人工合成的測試資料,不是任何真實專案圖面。
輸出到 ./fixtures/ 。座標:PDF 原點在頁面左下,單位 pt;1 pt = 25.4/72 mm。
"""
from pathlib import Path

OUT = Path(__file__).parent / "fixtures"
OUT.mkdir(exist_ok=True)
MM = 72 / 25.4


def pt(mm):
    return round(mm * MM, 4)


class Page:
    def __init__(self, w_mm, h_mm, rotate=0):
        self.w, self.h, self.rotate = pt(w_mm), pt(h_mm), rotate
        self.ops = ["1 w 0 0 0 RG 0 0 0 rg"]
        self.log = []  # fixtures 記錄

    def poly(self, pts_mm, name, scale, origin_mm):
        """閉合多邊形(頂點給圖面 mm,左下為原點)。真實尺寸 = 圖面mm*scale。回傳頂點 pt。"""
        P = [(pt(x), pt(y)) for x, y in pts_mm]
        s = f"{P[0][0]} {P[0][1]} m " + " ".join(f"{x} {y} l" for x, y in P[1:]) + " h S"
        self.ops.append(s)
        real = [(round((x - origin_mm[0]) * scale, 3), round((y - origin_mm[1]) * scale, 3)) for x, y in pts_mm]
        self.log.append((name, P, real))
        return P

    def line(self, x1, y1, x2, y2):
        self.ops.append(f"{pt(x1)} {pt(y1)} m {pt(x2)} {pt(y2)} l S")

    def text(self, x_mm, y_mm, s, size=10):
        s = s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        self.ops.append(f"BT /F1 {size} Tf {pt(x_mm)} {pt(y_mm)} Td ({s}) Tj ET")

    def dimension(self, x1, x2, y, label, size=10, tick=3):
        """水平尺寸線:端點 (x1,y)-(x2,y),兩端垂直短線,文字置中於線上方。回傳端點 pt。"""
        self.line(x1, y, x2, y)
        self.line(x1, y - tick, x1, y + tick)
        self.line(x2, y - tick, x2, y + tick)
        self.text((x1 + x2) / 2 - 4, y + 1.5, label, size)
        return (pt(x1), pt(y)), (pt(x2), pt(y))


def write_pdf(path, pages):
    objs = []  # 1-based

    def add(b):
        objs.append(b)
        return len(objs)

    cat = add(b"")          # 1 Catalog (回填)
    pgs = add(b"")          # 2 Pages (回填)
    font = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    kids = []
    for pg in pages:
        stream = ("\n".join(pg.ops)).encode("latin-1")
        c = add(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
        rot = f" /Rotate {pg.rotate}" if pg.rotate else ""
        p = add(f"<< /Type /Page /Parent {pgs} 0 R /MediaBox [0 0 {pg.w} {pg.h}]{rot} /Contents {c} 0 R "
                f"/Resources << /Font << /F1 {font} 0 R >> >> >>".encode())
        kids.append(p)
    objs[cat - 1] = f"<< /Type /Catalog /Pages {pgs} 0 R >>".encode()
    objs[pgs - 1] = f"<< /Type /Pages /Count {len(kids)} /Kids [{' '.join(f'{k} 0 R' for k in kids)}] >>".encode()
    buf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(buf))
        buf += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xr = len(buf)
    buf += f"xref\n0 {len(objs) + 1}\n".encode() + b"0000000000 65535 f \n"
    for o in offs:
        buf += f"{o:010d} 00000 n \n".encode()
    buf += f"trailer\n<< /Size {len(objs) + 1} /Root {cat} 0 R >>\nstartxref\n{xr}\n%%EOF\n".encode()
    Path(path).write_bytes(bytes(buf))


md = ["# 合成測試資料 fixtures(SYNTHETIC — 人工合成,非任何真實圖面)", "",
      "座標系:PDF 原點在頁面左下角,x 向右、y 向上,單位 pt(1 pt = 25.4/72 mm = 0.352778 mm)。",
      "真實尺寸 = 圖面尺寸 × 比例分母。真實座標以各圖形外框左下角為 (0,0),x 右、y 上,單位 mm。",
      "線寬 1 pt、黑色、無填色;文字為 Helvetica(可被 PDF.js 抽出文字層)。", ""]

# ---------- A3 橫向 1:50 ----------
SC = 50
A = Page(420, 297)
a_org = (100, 150)                       # 房 A 左下角(圖面 mm)
a_pts = [(100, 150), (200, 150), (200, 230), (100, 230)]   # 100 x 80 mm 圖面 = 5000 x 4000 真實
PA = A.poly(a_pts, "ROOM_A 矩形 5000x4000", SC, a_org)
l_org = (230, 140)
l_pts = [(230, 140), (350, 140), (350, 200), (310, 200), (310, 240), (230, 240)]  # 外框 120x100;缺 40x40(右上)
PL = A.poly(l_pts, "ROOM_L L形 外框6000x5000 右上缺2000x2000", SC, l_org)
d1, d2 = A.dimension(100, 200, 130, "5000")   # 尺寸線:y=130mm,x 100→200mm,= 房 A 底邊正下方 20mm
A.text(100, 235, "ROOM A", 12)
A.text(230, 245, "ROOM L", 12)
A.text(10, 10, "SYNTHETIC TEST 1:50", 14)
write_pdf(OUT / "synthetic_floorplan_A3_landscape.pdf", [A])

md += ["## synthetic_floorplan_A3_landscape.pdf", "",
       f"- 頁面:A3 橫向,MediaBox = [0 0 {A.w} {A.h}] pt(= 420 x 297 mm);1 頁;比例 1:50(圖面 1 mm = 真實 50 mm,即 1 pt = 17.6389 mm 真實)。",
       "- 左下角文字 `SYNTHETIC TEST 1:50`(基線起點 10mm,10mm = 28.3465,28.3465 pt)。", "",
       "### ROOM_A:5000 x 4000 mm 矩形(圖面 100 x 80 mm)", "",
       "| 頂點 | PDF pt | 圖面 mm | 真實 mm(以左下為原點) |", "|---|---|---|---|"]
for i, (p, m, r) in enumerate(zip(PA, a_pts, A.log[0][2])):
    md.append(f"| A{i+1} | ({p[0]}, {p[1]}) | ({m[0]}, {m[1]}) | ({r[0]:g}, {r[1]:g}) |")
md += ["", "### ROOM_L:L 形(外框 6000 x 5000 mm,右上缺 2000 x 2000 mm;圖面外框 120 x 100 mm)", "",
       "| 頂點 | PDF pt | 圖面 mm | 真實 mm(以外框左下為原點) |", "|---|---|---|---|"]
for i, (p, m, r) in enumerate(zip(PL, l_pts, A.log[1][2])):
    md.append(f"| L{i+1} | ({p[0]}, {p[1]}) | ({m[0]}, {m[1]}) | ({r[0]:g}, {r[1]:g}) |")
md += ["", "面積核對:ROOM_A = 20,000,000 mm²(20 m²);ROOM_L = 6000×5000 − 2000×2000 = 26,000,000 mm²(26 m²);周長 A=18000 mm,L=22000 mm。", "",
       "### 尺寸線「5000」(用來設比例尺)", "",
       f"- 端點 1:({d1[0]}, {d1[1]}) pt = 圖面 (100, 130) mm;端點 2:({d2[0]}, {d2[1]}) pt = 圖面 (200, 130) mm。",
       f"- 兩端點距離 = {round(d2[0]-d1[0], 4)} pt = 100.000 mm 圖面 = **5000 mm 真實**(比例 1:50)。端點各有 ±3 mm 圖面的垂直端線(x=100 與 x=200 mm 處,y 127~133 mm)。",
       "- 文字「5000」在線上方(基線約 y=131.5 mm,x 約 146 mm)。尺寸線位於 ROOM_A 底邊(y=150 mm)正下方 20 mm,與房間輪廓不相接。",
       "- 預期:以此尺寸線兩端點校準 5000 mm 後,ROOM_A 邊長應為 5000 / 4000 mm,ROOM_L 邊長依上表;每個 pt = 17.6389 mm。", ""]

# ---------- A4 直向兩頁 ----------
P1 = Page(210, 297)
p1_pts = [(65, 150), (145, 150), (145, 210), (65, 210)]   # 80x60 圖面 @1:50 = 4000x3000
P1V = P1.poly(p1_pts, "P1_RECT 矩形 4000x3000", 50, (65, 150))
P1.text(20, 270, "PAGE 1 OF 2", 24)
P1.text(20, 255, "SYNTHETIC PORTRAIT - RECTANGLE 4000 x 3000 - SCALE 1:50", 9)
P1.text(10, 10, "SYNTHETIC TEST p1", 10)
P2 = Page(210, 297)
p2_pts = [(95, 140), (115, 140), (115, 170), (135, 170), (135, 190), (75, 190), (75, 170), (95, 170)]
P2V = P2.poly(p2_pts, "P2_T T形 橫桿6000x2000 豎桿2000x3000", 100, (75, 140))
e1, e2 = P2.dimension(75, 135, 200, "6000")
P2.text(20, 270, "PAGE 2 OF 2", 24)
P2.text(20, 255, "SYNTHETIC PORTRAIT - T-SHAPE - SCALE 1:100", 9)
P2.text(10, 10, "SYNTHETIC TEST p2", 10)
write_pdf(OUT / "synthetic_portrait_2page.pdf", [P1, P2])

md += ["## synthetic_portrait_2page.pdf", "",
       f"- 2 頁,A4 直向,MediaBox = [0 0 {P1.w} {P1.h}] pt(210 x 297 mm)。頁面標題文字 `PAGE 1 OF 2` / `PAGE 2 OF 2`(24pt),左下 `SYNTHETIC TEST p1/p2`。", "",
       "### 第 1 頁:比例 1:50,矩形 4000 x 3000 mm(圖面 80 x 60 mm)", "",
       "| 頂點 | PDF pt | 圖面 mm | 真實 mm |", "|---|---|---|---|"]
for i, (p, m, r) in enumerate(zip(P1V, p1_pts, P1.log[0][2])):
    md.append(f"| R{i+1} | ({p[0]}, {p[1]}) | ({m[0]}, {m[1]}) | ({r[0]:g}, {r[1]:g}) |")
md += ["", "### 第 2 頁:比例 1:100,T 形(橫桿 6000 x 2000 在上,豎桿 2000 x 3000 在下置中;圖面外框 60 x 50 mm)", "",
       "| 頂點 | PDF pt | 圖面 mm | 真實 mm(外框左下為原點) |", "|---|---|---|---|"]
for i, (p, m, r) in enumerate(zip(P2V, p2_pts, P2.log[0][2])):
    md.append(f"| T{i+1} | ({p[0]}, {p[1]}) | ({m[0]}, {m[1]}) | ({r[0]:g}, {r[1]:g}) |")
md += ["", f"- 第 2 頁尺寸線「6000」:端點 ({e1[0]}, {e1[1]}) → ({e2[0]}, {e2[1]}) pt,圖面 60 mm = **6000 mm 真實**(1:100)。位於 T 形橫桿頂邊(y=190 mm)上方 10 mm。",
       "- 面積:T 形 = 6000×2000 + 2000×3000 = 18,000,000 mm²(18 m²);矩形 = 12 m²。",
       "- 用途:驗證頁面選擇(第 1 頁矩形 / 第 2 頁 T 形)、各頁獨立比例(1:50 vs 1:100)、關聯多頁。", ""]

# ---------- 旋轉頁(加分) ----------
R = Page(210, 297, rotate=90)
r_pts = [(65, 150), (145, 150), (145, 210), (65, 210)]
RV = R.poly(r_pts, "R_RECT 4000x3000(頁面 /Rotate 90)", 50, (65, 150))
R.text(20, 270, "ROTATED 90 SYNTHETIC", 18)
write_pdf(OUT / "synthetic_rotated90_A4.pdf", [R])
md += ["## synthetic_rotated90_A4.pdf(加分項,測頁面旋轉)", "",
       "- 1 頁,A4 MediaBox 直向 + `/Rotate 90`(檢視時應顯示為橫向,內容順時針轉 90°)。內容為 1:50 的 4000 x 3000 矩形,頂點 PDF pt 與第一份第 1 頁相同:"
       + "、".join(f"({p[0]}, {p[1]})" for p in RV) + "。", ""]

md += ["## repo 內既有 PDF(合法可用的範例,非本次合成)", "",
       "- `D:/geometry-axiom-qa/geometry-web/docs/fixtures/issue54-public-rooms.pdf`(3722 B;配 `issue54-measurements.json`)",
       "- `D:/geometry-axiom-qa/tests/fixtures/issue77-two-rooms.pdf`(838 B)",
       "- `D:/geometry-axiom-qa/geometry-web/docs/evidence/issue119-20261004/asymmetric-ten.pdf`(1566 B)",
       "- `.gcanvas` 範例專案:`geometry-web/examples/*.gcanvas`(engineering-spec-v1、assembly-rules-v1、assembly-generation-v1、source-subdivision-v11、source-subdivision-rooms-v11、space-model-v1),見 examples/README.md。",
       "  註:這些是 repo 自帶的開發夾具;驗收當作『既有資料』來源可用,但不得當作獨立驗收的唯一依據(可能偏向程式已知行為)。", ""]
(OUT / "fixtures.md").write_text("\n".join(md), encoding="utf-8")
print("ok", [p.name for p in OUT.iterdir()])
