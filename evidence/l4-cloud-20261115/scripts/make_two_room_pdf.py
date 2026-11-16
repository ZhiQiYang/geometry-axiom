# 自製的兩房平面 PDF(1 單位 = 10 mm):房 A 1600×1200、房 B 1400×1200,中間隔 400。
import sys
content = b"""0 0 0 RG 2 w
40 60 160 120 re S
240 60 140 120 re S
.5 w 40 195 m 200 195 l S
BT /F1 9 Tf 95 200 Td (1600) Tj ET
BT /F1 10 Tf 90 115 Td (room A) Tj ET
BT /F1 10 Tf 285 115 Td (room B) Tj ET
"""
objs = [
    b"<< /Type /Catalog /Pages 2 0 R >>",
    b"<< /Type /Pages /Kids [4 0 R] /Count 1 >>",
    b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 420 220] /Rotate 0 /Resources << /Font << /F1 3 0 R >> >> /Contents 5 0 R >>",
    b"<< /Length %d >>\nstream\n" % len(content) + content + b"endstream",
]
out = bytearray(b"%PDF-1.4\n"); offsets = []
for i, o in enumerate(objs, 1):
    offsets.append(len(out)); out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
xref = len(out)
out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
for off in offsets: out += b"%010d 00000 n \n" % off
out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
open(sys.argv[1], "wb").write(out)
