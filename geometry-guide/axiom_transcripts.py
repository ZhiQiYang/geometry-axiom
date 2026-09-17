# -*- coding: utf-8 -*-
"""web bridge 實錄:三條不存在於場景 DSL 的公理的範例來源。

R1(拾取)、R4(dump 往返)、R5(拖曳 clamp)講的都是互動行為。
`SCENE_COMMANDS` 裡沒有 pick / dump / drag 這些動詞,
所以無論怎麼寫 `.scene` 都逼不出這三條——它們只有 `geometry-web/web_bridge.c`
的 stdin 協定看得到。

這裡的做法是真的把 bridge 跑起來、把指令送進去、把回應原文收下來,
再貼進閱讀器。跟夾具同一個標準:顯示出來的每一個字都是真的跑出來的,
不是我描述的。每一份實錄自己帶一個斷言,斷言不成立就整份標紅。
"""
import io
import json
import os

import axiom_examples as ax

ROOT = ax.ROOT


def _desc(resp):
    """從 bridge 的 JSON 回應取 desc;取不到就回原文。"""
    try:
        return json.loads(resp).get("desc", "") or "(沒有命中)"
    except ValueError:
        return resp


def _short(resp, keep=("ok", "none", "desc", "guide", "timber",
                       "column", "beam", "offset")):
    """把回應縮成人看得懂的幾個欄位;hover 那種一大包 ops 不顯示。"""
    try:
        d = json.loads(resp)
    except ValueError:
        return resp
    bits = [(k, d[k]) for k in keep if k in d]
    return "{" + ", ".join('"%s": %s' % (k, json.dumps(v, ensure_ascii=False))
                           for k, v in bits) + "}"


# ------------------------------------------------------------------
def t_r1(bridge, tmpdir):
    """R1:同一點多個命中 → 取最後畫的。"""
    scene = os.path.join(ROOT, "room_a.scene").replace("\\", "/")
    cmds = [
        "loadfile " + scene,
        "pick 2 500 2000 12",
        "pick 2 3000 300 12",
        "pick 2 500 300 12",
    ]
    pairs = ax.run_bridge(bridge, cmds)

    notes = [
        "room_a 的天花板:參考線 1(沿 U,offset 300)、參考線 2(沿 V,offset 500),"
        "角材 1 就放在這兩條線的交點上。",
        "只有參考線 2 經過這裡 → 命中參考線 2。",
        "只有參考線 1 經過這裡 → 命中參考線 1。",
        "這一點上三個東西都命中:參考線 1、參考線 2、角材 1。"
        "角材畫在參考線之後 → 回傳角材。",
    ]
    steps = [(c, _short(r), n) for (c, r), n in zip(pairs, notes)]

    hit = [_desc(r) for _, r in pairs[1:]]
    ok = ("參考線2" in hit[0] and "參考線1" in hit[1] and "角材1" in hit[2])
    return {
        "steps": steps,
        "expect": "前兩點各自只有一條參考線,回傳那條;"
                  "第三點三者重疊,回傳最後畫的角材 1。",
        "ok": ok,
        "why": "" if ok else "命中結果與畫家演算法不符:%s" % hit,
    }


# ------------------------------------------------------------------
def t_r4(bridge, tmpdir):
    """R4:dump → 重放 → 再 dump,兩份必須逐字相同。"""
    scene = os.path.join(ROOT, "_demo_ceiling.scene").replace("\\", "/")
    first = ax.run_bridge(bridge, ["loadfile " + scene, "dump"])
    text_a = json.loads(first[1][1]).get("text", "")

    replay = os.path.join(tmpdir, "_r4_replay.scene")
    io.open(replay, "w", encoding="utf-8", newline="").write(text_a)

    second = ax.run_bridge(
        bridge, ["loadfile " + replay.replace("\\", "/"), "dump"])
    text_b = json.loads(second[1][1]).get("text", "")

    same = text_a == text_b
    head = "\n".join(text_a.split("\n")[:8])

    steps = [
        (first[0][0], _short(first[0][1]),
         "載入原始場景檔。"),
        ("dump", "(%d 行 / %d 字元,前 8 行如下)\n%s" %
         (text_a.count("\n") + 1, len(text_a), head),
         "World 序列化回 DSL:幾何、放置、canvas-pos 全部輸出。"
         "auto 角材的長度以凍結後的明寫形式輸出,不再是推導式。"),
        ("(把上面這份 dump 原封不動存成一個新的場景檔)", "",
         "這一步不是 bridge 指令,是把輸出當成輸入。"),
        # 顯示時把暫存路徑換成佔位符:實際送出的是絕對路徑,
        # 但那是機器專屬的,貼進頁面只會讓讀者以為路徑有意義。
        ("loadfile <暫存目錄>/_r4_replay.scene", _short(second[0][1]),
         "重放剛剛那份 dump。"),
        ("dump", "(%d 行 / %d 字元)" %
         (text_b.count("\n") + 1, len(text_b)),
         "第二次序列化。"),
        ("(逐字比對兩份 dump)",
         "相同" if same else "不同",
         "場景檔是 SSOT,所以 dump 出來的東西再讀回去必須得到同一個 World。"),
    ]
    return {
        "steps": steps,
        "expect": "兩份 dump 逐字相同(各 %d 字元)。" % len(text_a),
        "ok": same,
        "why": "" if same else "兩份 dump 不同,R4 的往返性質被破壞了",
    }


# ------------------------------------------------------------------
def t_r5(bridge, tmpdir):
    """R5:游標拖到範圍外 → clamp,不是拒絕。"""
    scene = os.path.join(ROOT, "room_a.scene").replace("\\", "/")
    cmds = [
        "loadfile " + scene,
        "drag 0 2 9999 9999",
        "drag 0 2 -5000 -5000",
        "drag 0 2 1234 1234",
    ]
    pairs = ax.run_bridge(bridge, cmds)
    offs = []
    for _, r in pairs[1:]:
        try:
            offs.append(json.loads(r).get("offset"))
        except ValueError:
            offs.append(None)

    notes = [
        "room_a:參考線 0 是沿 U 的線,合法 offset 區間是 [0, 3000]。",
        "游標拖到 9999,遠超過上界 → 夾回 3000,不是回一個錯誤。",
        "拖到 -5000,遠低於下界 → 夾回 0。",
        "拖到區間內的 1234 → 就是 1234,沒有被動手腳。",
    ]
    steps = [(c, _short(r), n) for (c, r), n in zip(pairs, notes)]

    ok = offs == [3000, 0, 1234]
    return {
        "steps": steps,
        "expect": "三次拖曳分別得到 offset 3000、0、1234——"
                  "越界的被夾回區間端點,區間內的原樣通過。"
                  "所以拖曳在構造上產生不出非法的 offset。",
        "ok": ok,
        "why": "" if ok else "clamp 結果不如預期:%s" % offs,
    }


TRANSCRIPTS = {
    "R1": ("拾取:同一點三個命中,回傳最後畫的", t_r1),
    "R4": ("dump 往返:序列化再重放,逐字相同", t_r4),
    "R5": ("拖曳:游標拖到範圍外會被夾回,不是拒絕", t_r5),
}


def build_all(bridge, tmpdir):
    """跑完三份實錄。回傳 {條號: 結果 dict}。"""
    out = {}
    for cid, (title, fn) in sorted(TRANSCRIPTS.items()):
        r = fn(bridge, tmpdir)
        r["title"] = title
        out[cid] = r
    return out


if __name__ == "__main__":
    import shutil
    import sys
    import tempfile

    sys.stdout.reconfigure(encoding="utf-8")
    tmp = tempfile.mkdtemp(prefix="axiomtrans_")
    try:
        res = build_all(ax.resolve_bridge(), tmp)
        bad = 0
        for cid, r in sorted(res.items()):
            print("──── %s %s" % (cid, r["title"]))
            for cmd, resp, note in r["steps"]:
                print("  送出  %s" % cmd)
                if resp:
                    print("  回應  %s" % resp.replace("\n", "\n        "))
                print("  說明  %s" % note)
            print("  預期  %s" % r["expect"])
            print("  結果  %s" % ("通過" if r["ok"] else "失敗:" + r["why"]))
            bad += 0 if r["ok"] else 1
        print("\n三份實錄,失敗 %d" % bad)
        sys.exit(1 if bad else 0)
    except ax.RenderError as exc:
        print("FAIL:%s" % exc)
        sys.exit(2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
