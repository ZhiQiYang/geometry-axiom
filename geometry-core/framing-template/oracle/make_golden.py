"""產生 oracle-golden.json:F1–F5 與兩個挪縫例子、8 種排法的完整輸出(凍結的標準答案)。
只在人工覆核過圖與數字之後才可重產;重產時要在 PR 說明改了什麼、為什麼。
用法: python make_golden.py rooms.json oracle-golden.json
"""
import json
import sys

import framing_oracle as fo

EXTRA = {
    "例:3700×2000 矩形(最後一條縫挪動)": {"outer": [[0, 0], [3700, 0], [3700, 2000], [0, 2000]]},
    "例:940×2000 矩形(第一條縫就要挪)": {"outer": [[0, 0], [940, 0], [940, 2000], [0, 2000]]},
}


def kind_label(t):
    """golden 裡的種類標籤。頂在凹角延伸段上的沿牆料標 rc_parallel:custom(核心角色 custom、優先級 3)。"""
    if t["kind"] == "secondary":
        return "secondary:" + t["role"]
    if t.get("core_role") == "custom":
        return t["kind"] + ":custom"
    return t["kind"]


def snapshot(spec):
    p = spec["params"]
    out = {"params": p, "rooms": {}}
    for name, room in dict(spec["rooms"], **EXTRA).items():
        rows = []
        for l, res, fails in fo.solve(room, p):
            assert not fails, (name, fo.layout_name(l), fails)
            rows.append({
                "layout": l,
                "name": fo.layout_name(l),
                "buildable": not res["conflicts"],
                "conflict_codes": sorted({c["code"] for c in res["conflicts"]}),
                "seams_a": sorted(res["seams_a"]),
                "seams_b": sorted(res["seams_b"]),
                "timbers": sorted([kind_label(t), list(t["rect"])]
                                  for t in res["timbers"]) if not res["conflicts"] else [],
            })
        out["rooms"][name] = {"room": room, "layouts": rows}
    return out


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as f:
        json.dump(snapshot(spec), f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
