import sys, json, traceback
sys.path.insert(0, r"D:/geometry-axiom-bqa/geometry-web/docs/evidence/browser-acceptance-20261006/pr134")
from r_lib import *
OUT = EVID / "pr156"
port = int(sys.argv[1]); tag = sys.argv[2]; widths = [int(x) for x in sys.argv[3].split(",")]
gate("g8-" + tag)
R = {}
with sync_playwright() as pw:
    for width in widths:
        height = 804 if width > 900 else 844
        ctx, page, errs = launch(pw, (width, height), f"g8-{tag}-{width}")
        h = mk(page, port); h.open_app(); h.fresh()
        dialogs = []
        mode = {"act": "dismiss"}
        def on_dialog(d):
            dialogs.append({"type": d.type, "msg": d.message[:160], "act": mode["act"]})
            (d.accept() if mode["act"] == "accept" else d.dismiss())
        page.on("dialog", on_dialog)
        try:
            def new_param(name, val, confirm):
                if width > 900: h.ctl('#btnNewParameter')
                else:
                    h.ev("document.querySelector('#mobileCreateObject').click()"); page.wait_for_timeout(300)
                    h.ev("document.querySelector('#btnNewParameter').click()")
                page.wait_for_timeout(900)
                h.fill('#paramName', name)
                inp = page.locator('#inspectorContent input[type="number"], #inspectorContent input[inputmode="decimal"], #inspectorContent input[inputmode="numeric"]').first
                try: inp.fill(val)
                except Exception: pass
                if confirm:
                    h.ev("document.querySelector('#paramPreview').click()"); page.wait_for_timeout(800)
                    h.ev("document.querySelector('#paramConfirm').click()"); page.wait_for_timeout(1500)
            if width <= 900:
                pass
            new_param("P1", "100", True)
            pcount = h.ev("(oc.parameters||[]).length")
            # second parameter: pending draft
            new_param("P2draft", "250", False)
            state = lambda: h.ev("""()=>({sel:JSON.stringify(oc.selection||[]),selk:JSON.stringify(oc.sel||null),left:document.body.classList.contains('drawer-left-open'),right:document.body.classList.contains('drawer-right-open'),name:(document.getElementById('paramName')||{}).value,draftCard:!!document.querySelector('.ocard[data-kind="parameter"][data-draft],.ocard.draft')})""")
            h.ev("1")
            # close drawers (390) so state starts closed
            if width <= 900:
                for b in ('#toggleLeft', '#toggleRight'):
                    pass
                h.ev("closePanels()")
            s0 = state()
            cards = h.ev("[...document.querySelectorAll('.ocard[data-kind=\"parameter\"]')].map(c=>c.dataset.id)")
            target = cards[0]
            sel = f'.ocard[data-kind="parameter"][data-id="{target}"] .card-enter'
            R[f"G-08.setup.{width}"] = {"parameters": pcount, "cards": cards, "state0": s0}
            mode["act"] = "dismiss"; n0 = len(dialogs)
            h.ev("(s)=>document.querySelector(s).dispatchEvent(new MouseEvent('click',{bubbles:true}))", sel)
            page.wait_for_timeout(1000)
            s1 = state()
            page.screenshot(path=str(OUT / f"g8_{tag}_cancel_{width}.png"))
            R[f"G-08.cancel.{width}"] = {"dialogs": dialogs[n0:], "state_after": s1, "unchanged": s0 == s1, "draft_name_kept": s1.get("name") == "P2draft"}
            # accept path
            mode["act"] = "accept"; n1 = len(dialogs)
            h.ev("(s)=>document.querySelector(s).dispatchEvent(new MouseEvent('click',{bubbles:true}))", sel)
            page.wait_for_timeout(1200)
            s2 = state()
            page.screenshot(path=str(OUT / f"g9_{tag}_accept_{width}.png"))
            R[f"G-09.accept.{width}"] = {"dialogs": dialogs[n1:], "state_after": s2, "target": target}
        except Exception:
            R[f"EXC.{width}"] = traceback.format_exc()[-1200:]
            try: page.screenshot(path=str(OUT / f"g8_exc_{tag}_{width}.png"))
            except Exception: pass
        R[f"console_errors.{width}"] = errs
        ctx.close()
(OUT / f"g8_results_{tag}.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
for k, v in R.items(): print(k, json.dumps(v, ensure_ascii=False)[:600])
