# D06 發現 5 對照組：同 make_two_page_pdf.py，只把第 2 頁 L 形最後一邊從閉合運算子 h 改成明寫 l。
import sys
p1 = b"""0 0 0 RG 2 w
40 60 160 120 re S
240 60 140 120 re S
.5 w 40 195 m 200 195 l S
BT /F1 9 Tf 95 200 Td (1600) Tj ET
"""
p2 = b"""0 0 0 RG 2 w
60 40 m 300 40 l 300 140 l 220 140 l 220 200 l 60 200 l 60 40 l S
.5 w 60 20 m 260 20 l S
BT /F1 9 Tf 150 8 Td (2000) Tj ET
BT /F1 10 Tf 120 110 Td (page 2 L room) Tj ET
"""
objs = [
    b"<< /Type /Catalog /Pages 2 0 R >>",
    b"<< /Type /Pages /Kids [4 0 R 6 0 R] /Count 2 >>",
    b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 420 220] /Rotate 0 /Resources << /Font << /F1 3 0 R >> >> /Contents 5 0 R >>",
    b"<< /Length %d >>\nstream\n" % len(p1) + p1 + b"endstream",
    b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 360 220] /Rotate 0 /Resources << /Font << /F1 3 0 R >> >> /Contents 7 0 R >>",
    b"<< /Length %d >>\nstream\n" % len(p2) + p2 + b"endstream",
]
out = bytearray(b"%PDF-1.4\n"); offsets = []
for i, o in enumerate(objs, 1):
    offsets.append(len(out)); out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
xref = len(out)
out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
for off in offsets: out += b"%010d 00000 n \n" % off
out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
open(sys.argv[1], "wb").write(out)
