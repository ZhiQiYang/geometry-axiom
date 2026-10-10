#!/usr/bin/env python3
"""Build the self-authored Issue 77 two-room PDF without dependencies.

The page viewport is 600 x 400 points. In PDF.js's top-left, Y-down
viewport coordinates, Room A has corners (50, 50), (250, 50),
(250, 200), (50, 200); Room B has corners (330, 50), (530, 50),
(530, 200), (330, 200). The calibration line runs from (50, 300)
to (250, 300) and is labelled 4000 mm.

No private drawing, automatic recognition output, creation timestamp,
or random identifier is included. Running this script again produces
the same bytes. Use --check to verify the committed fixture.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


DEFAULT_OUTPUT = Path(__file__).with_name("fixtures") / "issue77-two-rooms.pdf"
PAGE_SIZE = (600, 400)
ROOM_CORNERS = {
    "Room A": ((50, 50), (250, 50), (250, 200), (50, 200)),
    "Room B": ((330, 50), (530, 50), (530, 200), (330, 200)),
}
CALIBRATION_LINE = ((50, 300), (250, 300))
CALIBRATION_LENGTH_MM = 4000


def build_pdf() -> bytes:
    """Return a single-page PDF with ordinary vector paths and labels."""
    # Native PDF coordinates are bottom-left, Y-up. Only the room paths
    # and calibration line use this transform; text stays upright.
    stream = (
        "q\n"
        "1 0 0 -1 0 400 cm\n"
        "0 0 0 RG\n"
        "1 w\n"
        "50 50 200 150 re S\n"
        "330 50 200 150 re S\n"
        "50 300 m 250 300 l S\n"
        "Q\n"
        "BT /F1 16 Tf 123 271 Td (Room A) Tj ET\n"
        "BT /F1 16 Tf 403 271 Td (Room B) Tj ET\n"
        "BT /F1 12 Tf 123 114 Td (4000 mm) Tj ET\n"
    ).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 400] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ),
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
        + stream + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = bytearray(b"%PDF-1.4\n% Self-authored Issue 77 test fixture\n")
    offsets = [0]
    for number, body in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode("ascii"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true",
                        help="verify existing bytes without writing")
    args = parser.parse_args()
    expected = build_pdf()
    if args.check:
        if not args.out.is_file() or args.out.read_bytes() != expected:
            parser.exit(1, f"Fixture differs or is missing: {args.out}\n")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(expected)
    print(f"{hashlib.sha256(expected).hexdigest()}  {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
