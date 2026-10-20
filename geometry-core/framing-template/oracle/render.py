"""把 framing_oracle 的結果畫成一頁 HTML(內嵌 SVG)。用法: python render.py rooms.json out.html"""
import html
import json
import sys

import framing_oracle as fo

COLORS = {"boundary": "#2e7d32", "rc_parallel": "#00796b", "main": "#1565c0", "seam": "#e65100", "mark": "#f9a825", "ext": "#8bc34a"}
NAMES = {"boundary": "RC 邊界角材(貼牆、柱面)", "rc_parallel": "平行主支的 RC 面角材(柱面延伸到兩端牆;外牆在凹角處停在牆端)",
         "ext": "邊界角材越過凹角的延伸段(停在最近的主支側面)",
         "main": "主支(板縫下,整支連續)", "seam": "副支(板端縫下)", "mark": "副支(記號位置)"}
CONFLICT_TEXT = {
    "MAIN_LINE_CROSSES_RC": "主支線穿過 RC 後又回到室內,主支會被切斷",
    "MAIN_HITS_RC_TIMBER": "主支撞到牆或柱邊的角材",
    "SEAM_TOO_CLOSE_TO_RC": "板端縫太靠近 RC,縫上的副支撞到邊界角材",
    "TIMBERS_COLLIDE": "角材互相碰撞",
    "TIMBER_INTO_RC": "角材伸進 RC",
}


def poly_path(ring):
    return "M" + " L".join(f"{x},{y}" for x, y in ring) + " Z"


def svg(room, res, width=620):
    reg = res["region"]
    x0, y0, x1, y1 = reg.bbox
    pad = 120
    vb = (x0 - pad, y0 - pad, x1 - x0 + 2 * pad, y1 - y0 + 2 * pad)
    h = width * vb[3] / vb[2]
    out = [f'<svg viewBox="{vb[0]} {vb[1]} {vb[2]} {vb[3]}" width="{width}" height="{h:.0f}" xmlns="http://www.w3.org/2000/svg">']
    cid = f"clip{id(res)}"
    rings = [room["outer"]] + room.get("holes", [])
    d = " ".join(poly_path(r) for r in rings)
    out.append(f'<defs><clipPath id="{cid}"><path d="{d}" clip-rule="evenodd"/></clipPath></defs>')
    out.append(f'<rect x="{vb[0]}" y="{vb[1]}" width="{vb[2]}" height="{vb[3]}" fill="var(--rc)"/>')
    out.append(f'<path d="{d}" fill="var(--room)" fill-rule="evenodd"/>')
    a, b = res["a"], res["b"]
    g = 2

    def cuts(lo, hi, seams):
        out_, cur = [], lo
        for c in sorted(seams):
            out_.append((cur, c - g // 2))
            cur = c + g // 2
        out_.append((cur, hi))
        return out_

    cells = []
    for ar in cuts(reg.bbox[a], reg.bbox[a + 2], res["seams_a"]):
        for br in cuts(reg.bbox[b], reg.bbox[b + 2], res["seams_b"]):
            cells.append(fo.mk(a, ar, br))
    out.append(f'<g clip-path="url(#{cid})">')
    for c in cells:
        out.append(f'<rect x="{c[0]}" y="{c[1]}" width="{c[2]-c[0]}" height="{c[3]-c[1]}" fill="var(--panel)" stroke="var(--panel-edge)" stroke-width="6"/>')
    out.append("</g>")
    for t in res["timbers"]:
        r = t["rect"]
        k = t["kind"] if t["kind"] != "secondary" else t["role"]
        note = "(核心角色 custom、優先級 3)" if t.get("core_role") == "custom" else ""
        out.append(f'<rect x="{r[0]}" y="{r[1]}" width="{r[2]-r[0]}" height="{r[3]-r[1]}" fill="{COLORS[k]}"><title>{html.escape(NAMES[k] + note)} {list(r)}</title></rect>')
        for x in t.get("ext", []):
            q = fo.mk(a, tuple(x), fo.rng(r, b))
            out.append(f'<rect x="{q[0]}" y="{q[1]}" width="{q[2]-q[0]}" height="{q[3]-q[1]}" fill="{COLORS["ext"]}"><title>{html.escape(NAMES["ext"])} {list(q)}</title></rect>')
    for c in res["conflicts"]:
        for r in c.get("rects", []):
            out.append(f'<rect x="{r[0]-30}" y="{r[1]-30}" width="{r[2]-r[0]+60}" height="{r[3]-r[1]+60}" fill="none" stroke="var(--bad)" stroke-width="22"/>')
        if c["code"] == "MAIN_LINE_CROSSES_RC":
            s = c["seam"]
            p0 = (s, reg.bbox[b]) if a == 0 else (reg.bbox[b], s)
            p1 = (s, reg.bbox[b + 2]) if a == 0 else (reg.bbox[b + 2], s)
            out.append(f'<line x1="{p0[0]}" y1="{p0[1]}" x2="{p1[0]}" y2="{p1[1]}" stroke="var(--bad)" stroke-width="28" stroke-dasharray="90 60"/>')
    fs = 90
    for s in res["seams_a"]:
        x, y = ((s, y0 - 30) if a == 0 else (x0 - 30, s))
        anchor = "middle" if a == 0 else "end"
        out.append(f'<text x="{x}" y="{y}" font-size="{fs}" text-anchor="{anchor}" fill="var(--ink2)">{s}</text>')
    out.append("</svg>")
    return "\n".join(out)


def summary(res):
    kinds = {}
    for t in res["timbers"]:
        k = t["kind"] if t["kind"] != "secondary" else t["role"]
        kinds[k] = kinds.get(k, 0) + 1
    return "、".join(f"{NAMES[k].split('(')[0]} {n} 支" for k, n in kinds.items())


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    p = spec["params"]
    extra = {
        "例:3700×2000 矩形(最後一條縫挪動)": {"outer": [[0, 0], [3700, 0], [3700, 2000], [0, 2000]]},
        "例:940×2000 矩形(第一條縫就要挪)": {"outer": [[0, 0], [940, 0], [940, 2000], [0, 2000]]},
    }
    rooms = dict(spec["rooms"], **extra)
    parts = []
    for name, room in rooms.items():
        sol = fo.solve(room, p)
        rows = []
        shown_ok = shown_bad = 0
        figs = []
        for l, res, fails in sol:
            ok = not res["conflicts"] and not fails
            why = "; ".join(sorted({CONFLICT_TEXT.get(c["code"], c["code"]) for c in res["conflicts"]}))
            if fails:
                why += " 檢查失敗:" + ", ".join(sorted({f["check"] for f in fails}))
            moved = []
            for ax, mv in (("縫", res["moved_a"]), ("板端縫", res["moved_b"])):
                if mv:
                    moved.append(f"最後一條{ax}距起鋪側 {mv[0]} → {mv[1]}")
            rows.append(f"<tr><td>{fo.layout_name(l)}</td><td class={'ok' if ok else 'bad'}>{'可施工' if ok else '衝突'}</td>"
                        f"<td>{html.escape(why or summary(res))}{('<br>' + '；'.join(moved)) if moved else ''}</td></tr>")
            if (ok and shown_ok < 1) or (not ok and shown_bad < 1 and not fails):
                figs.append(f"<figure><figcaption>{fo.layout_name(l)} · {'可施工' if ok else '衝突:' + html.escape(why)}</figcaption>{svg(room, res)}</figure>")
                shown_ok += ok
                shown_bad += not ok
        parts.append(f"<section><h2>{html.escape(name)}</h2><div class=figs>{''.join(figs)}</div>"
                     f"<table><tr><th>排法</th><th>結果</th><th>說明</th></tr>{''.join(rows)}</table></section>")
    legend = "".join(f'<span><i style="background:{c}"></i>{html.escape(NAMES[k])}</span>' for k, c in COLORS.items())
    page = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>下角材幾何推演</title><style>
:root{{--bg:#f6f7f9;--card:#fff;--ink:#1d2433;--ink2:#5b6475;--rc:#b9bec7;--room:#fff;--panel:#e8f0ff;--panel-edge:#9db4e0;--bad:#d32f2f;--ok:#2e7d32}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#14171c;--card:#1d2128;--ink:#e6e9ef;--ink2:#a3abb9;--rc:#4a505b;--room:#2a2f38;--panel:#263452;--panel-edge:#4c6699;--bad:#ff6b6b;--ok:#66bb6a}}}}
body{{margin:0;padding:16px;background:var(--bg);color:var(--ink);font:15px/1.6 system-ui,"Noto Sans TC",sans-serif}}
h1{{font-size:22px;margin:4px 0 8px}} h2{{font-size:18px;margin:0 0 8px}}
section{{background:var(--card);border-radius:10px;padding:14px;margin:14px 0}}
.figs{{display:flex;flex-wrap:wrap;gap:14px}} figure{{margin:0;max-width:100%}} figure svg{{max-width:100%;height:auto}}
figcaption{{font-size:14px;color:var(--ink2);margin-bottom:4px}}
table{{border-collapse:collapse;width:100%;font-size:14px;margin-top:8px}} td,th{{border-top:1px solid var(--panel-edge);padding:4px 6px;text-align:left;vertical-align:top}}
.ok{{color:var(--ok);font-weight:600;white-space:nowrap}} .bad{{color:var(--bad);font-weight:600;white-space:nowrap}}
.legend span{{display:inline-flex;align-items:center;margin:2px 12px 2px 0;font-size:14px}} .legend i{{width:14px;height:14px;display:inline-block;margin-right:6px;border-radius:2px}}
p{{margin:6px 0}}
</style></head><body>
<h1>下角材幾何推演(oracle 第一版)</h1>
<p>這一頁的每一支角材都是 <code>framing_oracle.py</code> 算出來的座標,不是手畫。可施工的排法都通過 6 項自動檢查:面材每條邊有支撐(承接 ≥ {p['X']} mm)、副支間距 ≤ {p['M']} mm、主支整支連續、角材不碰撞、不入 RC、端面只頂角材。灰色是 RC,淺藍是面材,紅框是衝突位置。</p>
<p class=legend>{legend}</p>
{''.join(parts)}
</body></html>"""
    open(sys.argv[2], "w", encoding="utf-8").write(page)


if __name__ == "__main__":
    main()
