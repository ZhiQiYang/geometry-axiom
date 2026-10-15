"""唯讀重現任務 20 的 CR29 閉包前提；不實作整卡引用。

先以 cc 編譯 geometry-core/model_base.c 至 repo 外，再執行：
  ulimit -s 16384
  GEOMETRY_MODEL_BASE=/tmp/geometry-task20/model-base \
    python geometry-core/card-reference/probe_cr29_precondition.py --output /tmp/cr29

退出碼 2 表示根走訪圖未涵蓋 D29/D30，需要按看板停手核對範圍；
不把它登記為新功能測試通過，也不變更 native suite、expected 或產品程式。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "geometry-core"))
from modeling import build_package, verify_package  # noqa: E402
from modeling.base import load_base  # noqa: E402
from modeling.engine import evaluate  # noqa: E402

# 只驗整卡實作之前的鏈 T -> N -> B -> G。使用既有合法 DSL；
# 600/400 是定位用夾具，不以逐欄來源冒充新 CardReference。
SCENE = """boundary 1 outline 100,200 1300,200 1300,1000 100,1000
placement 1 on boundary 1 origin 0 0 0 u +x v +y
boundary-vertex-keys 1 outer 1 2 3 4 next-key 5
grid-system 4 name-hex 47 main-along none u repeat 0 600 v repeat 0 400
grid-binding 2 on-boundary 1 from-system 4 vertex-key 1 cell -2 1 anchor 0 1 0 1
grid 10 on 1 from-binding 2
timber 90 20 33 role boundary
place 90 on 1 at-face e0 +u +n
timber 91 20 33 role boundary
place 91 on 1 at-face e2 +u +n
timber 1 27 33 role primary
place 1 on 1 at-line grid 10 u -1 +v +n
"""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    adapter = Path(os.environ["GEOMETRY_MODEL_BASE"]).resolve()
    base = load_base(SCENE)
    selected = []

    def trace(frame, event, arg):
        # 唯讀觀察真正 evaluate 的最終 selected，不另寫閉包 oracle。
        if frame.f_code is evaluate.__code__ and event == "return":
            selected.append(sorted(frame.f_locals["selected"]))
        return trace

    request = {"roots": [{"kind": "timber", "id": 1}],
               "role": "geometry", "target": "solid-set", "allow_partial": False}
    previous_trace = sys.gettrace()
    try:
        sys.settrace(trace)
        package = build_package({"base_scene": SCENE, "extensions": []}, request,
                                base_executable=str(adapter))
    finally:
        sys.settrace(previous_trace)
    verify_package(package, base_executable=str(adapter))
    assert len(selected) == 1, "必須讀到一次實際匯出走訪結果"
    control = build_package({"base_scene": SCENE, "extensions": []},
                            {**request, "roots": [{"kind": "timber", "id": 90}]},
                            base_executable=str(adapter))
    required_definitions = {
        "D10": "grid 10 on 1 from-binding 2",
        "D30": "grid-binding 2 on-boundary 1 from-system 4",
        "D29": "grid-system 4 ",
    }
    preserved = {clause: token in package["definitions"]["base_scene"]
                 for clause, token in required_definitions.items()}
    # 必須承認：完整 definitions 已保留全部三種來源，不能誤報為資料遺失。
    assert all(preserved.values()), "本探針須區分原始定義保留與根走訪圖"
    missing = sorted({"grid", "grid-binding", "grid-system"}
                     - {kind for kind, identifier in selected[0]})
    source_paths = ["geometry-core/model_base.c", "geometry-core/modeling/engine.py",
                    "geometry-core/modeling/base.py", "current_geometry.c"]
    report = {
        "status": "BLOCKED_SCOPE_REVIEW" if missing else "PRECONDITION_PRESENT",
        "exit_code": 2 if missing else 0,
        "source_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {p: sha(ROOT / p) for p in source_paths},
        "probe_sha256": sha(__file__),
        "adapter_sha256": sha(adapter),
        "environment": {"os": platform.platform(), "python": platform.python_version(),
                        "stack_limit_bytes": resource.getrlimit(resource.RLIMIT_STACK)[0]},
        "request": request,
        "export_status": package["derived"]["status"],
        "verify_package": "returned successfully",
        "adapter_dependencies": base["dependencies"],
        "actual_evaluate_selected": selected[0],
        "missing_kinds_in_root_traversal": missing,
        "definitions_preserved": preserved,
        "unrelated_control_root": {"kind": "timber", "id": 90},
        "control_and_test_base_scene_equal": (
            control["definitions"]["base_scene"] == package["definitions"]["base_scene"]),
        "limitation": "完整場景保留 D10/D29/D30；缺少的是根依賴走訪圖節點。需 Claude 核對看板前提是否以此圖為準，不宣稱交換包遺失定義。",
    }
    artifacts = {"input.scene": SCENE, "base-snapshot.json": base,
                 "package.json": package, "control-package.json": control, "report.json": report}
    for name, value in artifacts.items():
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        (output / name).write_text(text, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(run(parser.parse_args().output))
