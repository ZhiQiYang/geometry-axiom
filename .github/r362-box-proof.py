"""對照同一 checkout、原生執行檔及兩支原始 R362 suite，只改 Python 選擇。"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

root = Path.cwd()
out = Path(os.environ["RUNNER_TEMP"]) / "r362-path-evidence"
out.mkdir()
temp = Path(os.environ["RUNNER_TEMP"]) / "r362-path"
common = temp / "without-alias"
alias = temp / "only-python"
common.mkdir(parents=True)
alias.mkdir()
base_env = os.environ.copy()
base_env.pop("PYTHON", None)
for directory in base_env["PATH"].split(os.pathsep):
    if not directory or not Path(directory).is_dir():
        continue
    for entry in Path(directory).iterdir():
        if entry.name == "python" or not entry.is_file() or not os.access(entry, os.X_OK):
            continue
        link = common / entry.name
        if not link.is_symlink():
            link.symlink_to(entry.absolute())
original_python = shutil.which("python")
assert original_python is not None, "runner reference must supply the Python alias"
(alias / "python").symlink_to(original_python)
assert shutil.which("python", path=str(common)) is None
assert shutil.which("python3", path=str(common)) and shutil.which("node", path=str(common))
suites = ["node:model_update_faces_app", "node:model_update_faces_review"]
source_files = [root / "tests/test_model_update_faces_app.js", root / "tests/test_model_update_faces_review.js",
                root / "tests/_model_update_faces_native.py", root / "tests/run_all.py"]
bin_files = [Path("/tmp/geometry-tests/bridge"), Path("/tmp/geometry-tests/model-base")]
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def snapshot():
    return {str(x): digest(x) for x in bin_files + source_files}
def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n")
source_sha = subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
assert source_sha == "a2620da6b3ae79df19905285ea80f3df5396a37e"
dump(out/"runtime.json", {"head":source_sha, "tree":subprocess.check_output(["git","rev-parse","HEAD^{tree}"], text=True).strip(),
     "python":sys.executable, "python_version":sys.version, "alias_source":original_python,
     "node":subprocess.check_output(["node","--version"], text=True).strip()})
rows = []
reference = None
for phase, with_alias, explicit in [("alias", True, False), ("python3-only", False, False), ("explicit", False, True)]:
    directory = out / phase
    directory.mkdir()
    env = dict(base_env, PATH=os.pathsep.join([str(alias),str(common)]) if with_alias else str(common))
    if explicit:
        env["PYTHON"] = sys.executable
    argv = [sys.executable, "tests/run_all.py"]
    if phase == "alias":
        argv += ["--build"]
    else:
        assert snapshot() == reference
    for suite in suites:
        argv += ["--only",suite]
    argv += ["--report", str(directory / "report.json")]
    with (directory/"run-all.log").open("wb") as log:
        result = subprocess.run(argv,env=env,stdout=log,stderr=subprocess.STDOUT)
    hashes = snapshot()
    if phase == "alias":
        reference = hashes
    assert hashes == reference
    log_rows = {}
    for suite in suites:
        file = (suite.replace(":","_")+".log")
        raw = Path("/tmp/geometry-tests/run_all-logs") / file
        shutil.copy2(raw,directory/file)
        body = raw.read_text(encoding="utf8")
        names = [(m.group(1),m.group(2)) for m in re.finditer(r"^([✔✖]) (.+?) \([\d.]+ms\)\s*$",body,re.M)]
        log_rows[suite] = {"cases":names,"ENOENT":"spawnSync python ENOENT" in body, "sha256":digest(raw)}
    row = {"phase":phase,"exit":result.returncode,"pythonOnPath":shutil.which("python",path=env["PATH"]),
           "PYTHON":env.get("PYTHON"),"argv":argv,"hashes":hashes,"suites":log_rows}
    rows.append(row)
    dump(out/"result.json",rows)
    print(phase,"exit",result.returncode,json.dumps(log_rows,ensure_ascii=False),flush=True)
assert [row["exit"] for row in rows] == [0,1,0]
for row in (rows[0], rows[2]):
    for suite, count in zip(suites, [7,5]):
        cases = row["suites"][suite]["cases"]
        assert [flag for flag, _ in cases] == ["✔"]*count,(row["phase"],suite,cases)
for suite, count in zip(suites, [7,5]):
    cases = rows[1]["suites"][suite]["cases"]
    assert len(cases)==count and rows[1]["suites"][suite]["ENOENT"],(suite,cases)
for suite, prefix in [(suites[0],"R362_UI_FACES"), (suites[1],"R362_FACE_SELECTION"), (suites[1],"R362_NATIVE_FACES updates")]:
    assert any(mark == "✖" and name.startswith(prefix) for mark, name in rows[1]["suites"][suite]["cases"])
