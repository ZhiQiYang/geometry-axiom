import json, re, sys
M = r"D:/geometry-axiom-123tests/geometry-web/docs/issue123-c-pending-tests/measurements/"
def parse(fn):
    L = open(M + fn, encoding="utf-8").read().splitlines()
    p35 = [l for l in L if l.startswith("P35")]
    r = {"log": fn, "P35_assertions": len(p35), "P35_pass": sum(1 for l in p35 if "✓" in l), "P35_fail": sum(1 for l in p35 if "✗" in l),
         "fails": [l[:160] for l in L if "✗" in l], "fatal": [l[:200] for l in L if l.startswith("FATAL:")]}
    ex = [l for l in L if l.startswith("EXIT=")]
    if ex:
        m = re.match(r"EXIT=(\d+) SECONDS=(\d+)", ex[-1]); r["exit"] = int(m.group(1)); r["seconds"] = int(m.group(2))
    res = [l for l in L if l.startswith("CDP_RESULT")]
    if res:
        j = json.loads(res[-1][len("CDP_RESULT "):]); r["completed"] = j.get("completed"); r["passedAssertions"] = j.get("passedAssertions"); r["failedAssertions"] = j.get("failedAssertions"); r["lastFatal"] = j.get("fatal")
    last = [l for l in L if l.startswith("=== P") or l.startswith("[TEST PAGE LEAVE]")]
    r["last_section"] = last[-1][:60] if last else None
    return r
out = {"sha": "d6b4b450d741fcbbfd75c51631915d3082926990", "invocation": "GEOMETRY_CDP_FROM_P31=1 node cdp_test.js (略過 P1–P30;P35 含 :3976 waitForFaceViewport)", "cap_seconds": 1200}
for k, fn in [("baseline_run1", "t3_cdp_baseline.log"), ("baseline_run2", "t3_cdp_baseline2.log"), ("patched", "t3_cdp_patched.log")]:
    try: out[k] = parse(fn)
    except FileNotFoundError: pass
json.dump(out, open(M + "t3_cdp_b6_patch.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1)[:2500])
