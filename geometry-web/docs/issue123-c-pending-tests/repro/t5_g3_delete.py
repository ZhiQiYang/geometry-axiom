from common import *
res = {"sha": "d6b4b450d741fcbbfd75c51631915d3082926990", "viewport": "1382x804", "steps": {}}
def step(k, v=True): res["steps"][k] = v
STATE = """() => ({cards:[...document.querySelectorAll('.ocard[data-kind="grid-system"],.ocard[data-kind="grid-binding"]')].map(c=>({kind:c.dataset.kind,id:c.dataset.id,t:c.textContent.trim().replace(/\s+/g,' ').slice(0,30)})),
  impact: !!document.querySelector('.reference-impact[open]'),
  impactText: (document.querySelector('.reference-impact[open]')||{innerText:''}).innerText.slice(0,1200),
  toasts:[...document.querySelectorAll('.toast')].map(t=>({t:t.textContent.trim().slice(0,90),cls:String(t.className)})),
  status:(document.getElementById('status')||{}).textContent})"""
mem_gate("t5")
with sync_playwright() as pw:
    ctx, page, errors = session(pw, VIEWS["1382x804"], "t5")
    dialogs = []
    def on_dialog(d): dialogs.append({"type": d.type, "message": d.message[:100]}); d.dismiss()
    page.on("dialog", on_dialog)
    try:
        open_app(page); load_example(page)
        def create_source(name):
            page.click("#btnNewGridSystem"); page.wait_for_timeout(2500)
            page.fill("#igName", name); page.wait_for_timeout(400)
            page.click("#igSaveSource")
            page.wait_for_selector("dialog.reference-impact[open] #impact-confirm", timeout=60000)
            page.click("#impact-confirm")
            page.wait_for_function("() => { const b=document.getElementById('igClose'); return b && !b.disabled; }", timeout=60000)
            page.wait_for_timeout(600)
        create_source("有配置來源"); step("src1_created")
        # 為來源 1 建立配置(真 UI:＋ 選邊界建立配置 → 邊界/頂點/格 → 預覽並建立配置 → 確認)
        page.click("#igNewBinding"); page.wait_for_timeout(2500)
        opts = page.evaluate("() => [...document.getElementById('igBoundary').options].map(o=>o.value)")
        page.select_option("#igBoundary", [o for o in opts if o][0]); page.wait_for_timeout(1200)
        vopts = page.evaluate("() => [...document.getElementById('igVertex').options].map(o=>o.value)")
        step("vertex_options", vopts)
        page.select_option("#igVertex", [o for o in vopts if o][0]); page.wait_for_timeout(800)
        page.click('[data-ig-anchor="1,1"]'); page.wait_for_timeout(500)
        step("save_binding_state", page.evaluate("() => ({dis:document.getElementById('igSaveBinding').disabled, text:document.getElementById('igSaveBinding').textContent, status:document.getElementById('igStatus').textContent.slice(0,80)})"))
        page.click("#igSaveBinding")
        page.wait_for_selector("dialog.reference-impact[open] #impact-confirm", timeout=60000)
        res["binding_create_impact_text"] = page.evaluate("() => document.querySelector('dialog.reference-impact[open]').innerText.slice(0,200)")
        page.click("#impact-confirm"); page.wait_for_timeout(2500)
        page.click("#igClose"); page.wait_for_timeout(1500)
        step("binding_created", page.evaluate(STATE)["cards"])
        create_source("無配置來源"); step("src2_created")
        page.click("#igClose"); page.wait_for_timeout(1500)
        st = page.evaluate(STATE); res["cards_before"] = st["cards"]
        srcs = [c for c in st["cards"] if c["kind"] == "grid-system"]
        res["sources"] = srcs
        def card(c):
            row = page.locator(f'#objectList .object-row[data-kind="grid-system"][data-id="{c["id"]}"]')
            return row if row.count() else page.locator(f'.ocard[data-kind="grid-system"][data-id="{c["id"]}"]')
        def count(c): return page.locator(f'.ocard[data-kind="grid-system"][data-id="{c["id"]}"]').count()
        for label, nm in (("with_binding", "有配置來源"), ("without_binding", "無配置來源")):
            tgt = next((c for c in srcs if nm in c["t"]), None)
            r = {"target": tgt}
            if not tgt: res[label] = r; continue
            card(tgt).first.click(); page.wait_for_timeout(1200)
            r["inspector_actions"] = page.evaluate("() => [...document.querySelectorAll('.gi-actions button')].map(b=>b.id+':'+b.textContent.trim())")
            if label == "with_binding": page.screenshot(path=str(SHOTS / "t5-inspector-with-binding.png"), clip={"x":0,"y":100,"width":1382,"height":700})
            # --- 第一次:按刪除 → 取消
            page.click("#gridObjectDelete"); page.wait_for_timeout(2500)
            s1 = page.evaluate(STATE); r["after_click_delete"] = {"impact": s1["impact"], "impactText": s1["impactText"], "toasts": s1["toasts"]}
            if s1["impact"]:
                r["confirm_disabled_first"] = page.evaluate("() => document.getElementById('impact-confirm').disabled")
                r["cancel_label"] = page.evaluate("() => document.querySelector('dialog.reference-impact[open] .impact-actions button:first-child').textContent")
                if label == "with_binding": page.screenshot(path=str(SHOTS / "t5-impact-with-binding.png"))
                page.click("dialog.reference-impact[open] .impact-actions button:first-child"); page.wait_for_timeout(1500)
            r["after_cancel"] = {"stillExists": count(tgt) == 1, "impactOpen": page.evaluate(STATE)["impact"]}
            if not s1["impact"] and count(tgt) == 0:
                # 無確認對話框:直接刪除(見 toast);驗 Ctrl+Z
                r["deleted_without_dialog"] = True
                if label == "without_binding": page.screenshot(path=str(SHOTS / "t5-no-dialog-deleted-toast.png"), clip={"x":0,"y":100,"width":1382,"height":704})
                page.evaluate("() => document.activeElement && document.activeElement.blur()")
                page.keyboard.press("Control+z"); page.wait_for_timeout(3000)
                s4 = page.evaluate(STATE)
                r["after_ctrl_z"] = {"exists": count(tgt) == 1, "toasts": s4["toasts"], "impact": s4["impact"], "cards": s4["cards"]}
                res[label] = r; continue
            # --- 第二次:按刪除 → 確認
            if count(tgt):
                card(tgt).first.click(); page.wait_for_timeout(800)
                page.click("#gridObjectDelete"); page.wait_for_timeout(2500)
                s2 = page.evaluate(STATE); r["second_click_delete"] = {"impact": s2["impact"], "impactText": s2["impactText"]}
                if s2["impact"]:
                    r["confirm_disabled_second"] = page.evaluate("() => document.getElementById('impact-confirm').disabled")
                    if r["confirm_disabled_second"]:
                        r["blocked"] = True
                        page.click("dialog.reference-impact[open] .impact-actions button:first-child"); page.wait_for_timeout(1200)
                        res[label] = r; continue
                    page.click("#impact-confirm"); page.wait_for_timeout(2500)
                s3 = page.evaluate(STATE)
                r["after_confirm"] = {"exists": count(tgt) == 1, "toasts": s3["toasts"], "status": s3["status"], "cards": s3["cards"]}
                # --- Ctrl+Z
                page.evaluate("() => document.activeElement && document.activeElement.blur()")
                page.keyboard.press("Control+z"); page.wait_for_timeout(3000)
                s4 = page.evaluate(STATE)
                r["after_ctrl_z"] = {"exists": count(tgt) == 1, "toasts": s4["toasts"], "impact": s4["impact"], "cards": s4["cards"]}
                if label == "with_binding" and not r["after_ctrl_z"]["exists"] and s4["impact"]:
                    r["note"] = "Ctrl+Z 後出現影響對話框,見 impactText"; r["ctrlz_impact"] = s4["impactText"]
            res[label] = r
        res["native_dialogs"] = dialogs; res["errors"] = errors[:10]
    except Exception as ex:
        res["exception"] = str(ex)[:500]
        try: page.screenshot(path=str(SHOTS / "t5-exception.png"))
        except Exception: pass
    finally:
        save("t5_g3_delete.json", res); ctx.close()
for k in ("with_binding", "without_binding"):
    r = res.get(k, {})
    print(k, "impact@click:", (r.get("after_click_delete") or {}).get("impact"), "| cancel keeps:", (r.get("after_cancel") or {}).get("stillExists"),
          "| confirm exists:", (r.get("after_confirm") or {}).get("exists"), "toasts:", (r.get("after_confirm") or {}).get("toasts"), "| ctrlz exists:", (r.get("after_ctrl_z") or {}).get("exists"))
print(res.get("exception"), res.get("steps", {}).get("save_binding_state"))
