"""產生 oracle-golden.json:F1–F5 與三個額外例子、8 種排法的完整輸出(凍結的標準答案)。
每個排法:buildable = 物理上可施工(沒有物理衝突);core_limits = 物理上可施工、核心條文表示不了的地方
(碼、建構端的料編號、端面座標、那支料的矩形;#251 審查 3d858c3 阻擋 1:核心限制和物理衝突分開,不再算不可施工。
審查 6332818768:timbers 會依種類與矩形重排,建構端 id 不是排序後的索引,所以矩形才是對回料件的資料)。
物理上可施工的排法(含有核心限制的)都列出逐支角材。
core_limit_witness 另收 FZ120、左上起鋪板長沿 Y 的 I22 延伸段非空核心限制,不放進 rooms:
閱讀 A 已解除 STEP20 的 I19 固定段限制；FZ120 的 I22 不在本次授權範圍,仍須保留非空與料件綁定反證。
rooms 維持原 8 房、64 排法,不把見證房送進探針。
只在人工覆核過圖與數字之後才可重產;重產時要在 PR 說明改了什麼、為什麼。
用法: python make_golden.py rooms.json oracle-golden.json
"""
import json
import sys

import framing_oracle as fo

EXTRA = {
    "例:3700×2000 矩形(最後一條縫挪動)": {"outer": [[0, 0], [3700, 0], [3700, 2000], [0, 2000]]},
    "例:940×2000 矩形(第一條縫就要挪)": {"outer": [[0, 0], [940, 0], [940, 2000], [0, 2000]]},
    "例:縫寬 3 的 3700×4000 矩形(反向起鋪首縫取上界)": {"outer": [[0, 0], [3700, 0], [3700, 4000], [0, 4000]], "params": {"gap": 3}},
}


def kind_label(t):
    """golden 裡的種類標籤。
    端面頂在延伸段上的沿牆料、沿柱料(凹角旁、牆階)與併料標 rc_parallel:custom(核心角色 custom、優先級 3)。
    端面頂到 custom 側面的副支在原標籤後加 :custom4(核心角色 custom、優先級 4;與主支垂直的柱面料也適用,
    會標 boundary:custom4,但現行房間沒有實例;
    使用者 2026-10-18 拍板,決策佇列「凹角沿牆料的排序」選項 C)。其餘照舊;核心角色對照見 README。"""
    if t["kind"] == "rc_parallel" and t.get("core_role") == "custom":
        return "rc_parallel:custom"
    base = "secondary:" + t["role"] if t["kind"] == "secondary" else t["kind"]
    if t.get("core_role") == "custom":
        base += f":custom{t['priority']}"
    return base


# 不放進 rooms。使用既有 FZ120 手算幾何,只見證仍受 I22 約束的延伸段。
FZ120_WITNESS = {"outer": [[0, 0], [4100, 0], [4100, 3672], [1450, 3672], [1450, 3720], [1000, 3720], [1000, 3675], [0, 3675]]}


def core_limit_rows(res):
    """[碼, 建構端 id, 端面, 矩形]。id 是 build() 給的編號,不是排序後 timbers 的索引;矩形才對得回料件。"""
    if res["conflicts"]:
        return []
    by_id = {t["id"]: [int(x) for x in t["rect"]] for t in res["timbers"]}
    return sorted([c["code"], c["id"], c["end"], by_id[c["id"]]] for c in res["core_limits"])


def layout_record(l, res):
    return {
        "layout": l,
        "name": fo.layout_name(l),
        "buildable": not res["conflicts"],  # 物理上可施工(沒有物理衝突);核心表示不了的另列 core_limits
        "conflict_codes": sorted({c["code"] for c in res["conflicts"]}),
        "core_limits": core_limit_rows(res),
        "seams_a": sorted(res["seams_a"]),
        "seams_b": sorted(res["seams_b"]),
        "timbers": sorted([kind_label(t), list(t["rect"])]
                          for t in res["timbers"]) if not res["conflicts"] else [],
    }


def snapshot(spec):
    p = spec["params"]
    out = {"params": p, "rooms": {}}
    for name, room in dict(spec["rooms"], **EXTRA).items():
        rows = []
        for l, res, fails in fo.solve(room, dict(p, **room.get("params", {}))):
            v, probs = fo.verdict(res, None, fails)
            assert v in ("buildable", "core_limited", "unbuildable"), (name, fo.layout_name(l), probs)
            rows.append(layout_record(l, res))
        out["rooms"][name] = {"room": room, "layouts": rows}
    witness_rows = []
    for l, res, fails in fo.solve(FZ120_WITNESS, p):
        v, probs = fo.verdict(res, None, fails)
        assert v in ("buildable", "core_limited", "unbuildable"), (fo.layout_name(l), probs)
        if fo.layout_name(l) != "左上起鋪,板長沿Y":
            continue
        witness_rows.append(layout_record(l, res))
    assert len(witness_rows) == 1 and witness_rows[0]["core_limits"], witness_rows
    assert witness_rows[0]["core_limits"] == [["CORE_LIMIT_EXTENSION_END_FREE", 1, 1000, [1000, 3645, 4100, 3672]]], witness_rows
    out["core_limit_witness"] = {
        "room_name": "例:FZ120(I22 延伸段非空見證)",
        "room": FZ120_WITNESS,
        "layouts": witness_rows,
    }
    return out


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as f:
        json.dump(snapshot(spec), f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
