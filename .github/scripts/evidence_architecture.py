"""Adopt and select immutable, in-repository architecture execution bundles.

The original generator and its three commands are unchanged. Import is an
origin-side operation on the clean execution checkout; adoption into another
checkout copies the complete bundle. Selection checks the original inventory
and full dependency closure before considering any stored proof. It never
changes an execution head, refreshes a hash, or rewrites a legacy view.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "geometry-core/domain-decoupling/product-architecture.json"
GENERATOR = ".github/scripts/architecture_evidence.py"
SCANNER = "tests/architecture_contract.py"
TESTS = ("tests/test_architecture_contract.py", "tests/test_product_architecture.py")
DEFAULT_STORE = ".github/evidence/architecture"
RECEIPT = "product-architecture-receipt.json"
SCAN = "product-architecture-scan.json"
REPORT = "PRODUCT-ARCHITECTURE.md"
LABELS = ("architecture-cli", "architecture-unit", "architecture-product")
RAW_FILES = (RECEIPT, SCAN, REPORT, *(label + suffix for label in LABELS for suffix in (".stdout", ".stderr")))
BUNDLE_SCHEMA = "geometry-architecture-bundle/1"
CONTEXT_SCHEMA = "geometry-architecture-inputs/1"
FROZEN_BASE = "11eddfdb4d7b1f76aedfe001e084a3840790bedc"
FROZEN = {
    "geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md": "d02e0abdd34c222249dffe38ebc51fee25698252e870c6a1dd5afc31d6406fe0",
    "geometry-core/domain-decoupling/product-architecture-receipt.json": "81a114839812f92c6ed706588b3078a44220098b6e5267ed57923a3934ce89be",
    "geometry-core/domain-decoupling/product-architecture-scan.json": "f92d4110d26c21a3048ce484365019266ad5294025f0bf053942e3e67ea47e88",
}
# Receipt v1 did not record its generator. Import therefore supports exactly the
# reviewed, unchanged generator. A future generator needs an explicit migration,
# not an envelope that silently attaches a new generator hash to old output.
GENERATOR_LF_SHA256 = "9899d18b3fb80a750308e2342d8309ca7a2470ec5aab4f977bc3213690b07b5b"
ADOPTED_MAIN = "8f82b207e87c086705a1d8b7a00e2f215c07cbcf"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class EvidenceError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def require(condition, code, message):
    if not condition:
        raise EvidenceError(code, message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_json(raw, description):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, "JSON", description + ": duplicate key " + repr(key))
            value[key] = item
        return value
    try:
        return json.loads(raw, object_pairs_hook=unique,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (ValueError, UnicodeError) as error:
        if isinstance(error, EvidenceError):
            raise
        raise EvidenceError("JSON", description + ": " + str(error)) from error


def no_symlinks(path, code):
    path = Path(path).absolute()
    for parent in (*reversed(path.parents), path):
        require(not parent.is_symlink(), code, "symlink is not an evidence path: " + str(parent))
    return path


def read_regular(path, code):
    path = no_symlinks(path, code)
    require(path.is_file(), code, "missing regular file: " + str(path))
    return path.read_bytes()


def git(root, *args):
    process = subprocess.run(["git", *args], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    require(process.returncode == 0, "GIT", process.stderr.decode("utf-8", errors="replace").strip())
    return process.stdout


def frozen_baseline(root):
    for relative, expected in FROZEN.items():
        raw = read_regular(root / relative, "FROZEN_BASELINE")
        require(digest(raw) == expected, "FROZEN_BASELINE",
                relative + ": frozen working-tree bytes differ from " + FROZEN_BASE)
        committed = git(root, "show", "HEAD:" + relative)
        require(digest(committed) == expected, "FROZEN_BASELINE",
                relative + ": frozen committed bytes differ from " + FROZEN_BASE)


def _current_context(root):
    """Run the original complete inventory before computing the cache key."""
    root = Path(root).resolve()
    frozen_baseline(root)
    scanner_path = root / SCANNER
    scanner_raw = read_regular(scanner_path, "INVENTORY").replace(b"\r\n", b"\n")
    name = "_architecture_inventory_" + digest(str(root).encode("utf-8"))
    spec = importlib.util.spec_from_file_location(name, scanner_path)
    require(spec is not None and spec.loader is not None, "INVENTORY", "cannot load original scanner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        manifest_raw = read_regular(root / MANIFEST, "INVENTORY").replace(b"\r\n", b"\n")
        manifest = module.load_manifest(root / MANIFEST)
        scanner = module.Scanner(root, manifest)
        scanner.validate_manifest()
    except (OSError, ValueError, module.ContractError) as error:
        raise EvidenceError("INVENTORY", str(error)) from error
    inputs = [{"path": entry["path"],
               "lfSha256": digest(read_regular(root / entry["path"], "INVENTORY").replace(b"\r\n", b"\n"))}
              for entry in manifest["sources"] + manifest["exclusions"]]
    inputs.sort(key=lambda entry: entry["path"])
    context = {
        "schema": CONTEXT_SCHEMA,
        "manifestLfSha256": digest(manifest_raw),
        "scannerLfSha256": digest(scanner_raw),
        "testScriptsLfSha256": {relative: digest(read_regular(root / relative, "INVENTORY").replace(b"\r\n", b"\n"))
                               for relative in TESTS},
        "generatorLfSha256": digest(read_regular(root / GENERATOR, "INVENTORY").replace(b"\r\n", b"\n")),
        "inputs": inputs,
        "inputLfClosureSha256": digest("\n".join(entry["path"] + " " + entry["lfSha256"] for entry in inputs).encode("utf-8")),
        "ownedCount": len(manifest["sources"]),
        "exclusionCount": len(manifest["exclusions"]),
    }
    return context, manifest, scanner.result.to_dict()


def current_context(root):
    return _current_context(Path(root).resolve())[0]


def expected_commands():
    return [
        ["<python>", "-B", SCANNER, "--root", ".", "--manifest", MANIFEST],
        ["<python>", "-B", TESTS[0]],
        ["<python>", "-B", TESTS[1]],
    ]


def expected_report(receipt, manifest):
    layers = Counter(entry["layer"] for entry in manifest["sources"])
    rows = "\n".join("| " + layer + " | " + str(count) + " |" for layer, count in sorted(layers.items()))
    tests = "、".join(row["label"] + "=" + str(row["testsRun"]) for row in receipt["commands"] if "testsRun" in row)
    return (
        "# Product architecture — GitHub 新來源收據\n\n"
        f"來源 `{receipt['sourceHead']}`；採入 main `{receipt['adoptedMain']}`；Actions run `{receipt['runId']}`。\n\n"
        "這份衍生資料來自原 scanner CLI 與原兩支 unittest 的實際執行；三命令均 exit 0、零 skip。"
        "它只證明靜態依賴契約，不能替代演算法責任審查、原生／突變／瀏覽器或 SSOT 驗證。\n\n"
        f"本次 {len(receipt['inputs'])} inputs、{receipt['ownedCount']} owned、{receipt['exclusionCount']} exclusions、"
        f"{receipt['edgeCount']} edges、0 diagnostics；{tests}。完整命令、原始輸出與雜湊在同 artifact。\n\n"
        "| Layer | Sources |\n|---|---:|\n" + rows + "\n\n"
        f"main 的歷史收據保留在 Git `{receipt['adoptedMain']}`，本次沒有改寫其來源或沿用其綠燈。\n"
    ).encode("utf-8")


def read_artifact(directory, *, bundled=False):
    directory = no_symlinks(directory, "RAW_FILES")
    require(directory.is_dir(), "RAW_FILES", "missing artifact directory: " + str(directory))
    expected = set(RAW_FILES) | ({"bundle.json"} if bundled else set())
    require({path.name for path in directory.iterdir()} == expected, "RAW_FILES",
            "artifact must contain exactly the original nine files" + (" and bundle.json" if bundled else ""))
    return {name: read_regular(directory / name, "RAW_FILES") for name in RAW_FILES}


def validate_artifact(raw, context, manifest, inventory):
    receipt = load_json(raw[RECEIPT], RECEIPT)
    receipt_keys = {"schema", "sourceHead", "adoptedMain", "runId", "runAttempt", "complete", "commands",
                    "manifestLfSha256", "scannerLfSha256", "testScriptsLfSha256", "scanSha256", "ownedCount",
                    "exclusionCount", "edgeCount", "diagnosticCount", "inputs", "inputLfClosureSha256"}
    require(isinstance(receipt, dict) and set(receipt) == receipt_keys, "RECEIPT", "unexpected receipt fields")
    require(receipt["schema"] == "geometry-architecture-ci-receipt/1" and receipt["complete"] is True,
            "RECEIPT", "incomplete or unsupported original receipt")
    require(isinstance(receipt["sourceHead"], str) and HEX40.fullmatch(receipt["sourceHead"]),
            "RECEIPT", "invalid original sourceHead")
    require(receipt["adoptedMain"] == ADOPTED_MAIN, "RECEIPT", "unexpected original adoptedMain")
    for field in ("runId", "runAttempt"):
        require(isinstance(receipt[field], str) and re.fullmatch(r"[1-9][0-9]*", receipt[field]) is not None,
                "RECEIPT", "formal CI bundle requires a positive original " + field)
    for field in ("manifestLfSha256", "scannerLfSha256", "testScriptsLfSha256", "inputs", "inputLfClosureSha256",
                  "ownedCount", "exclusionCount"):
        require(receipt[field] == context[field], "CLOSURE", "original receipt no longer matches " + field)
    for field in ("ownedCount", "exclusionCount", "edgeCount", "diagnosticCount"):
        require(type(receipt[field]) is int and receipt[field] >= 0, "RECEIPT", "invalid count: " + field)
    rows = receipt["commands"]
    require(isinstance(rows, list) and len(rows) == 3, "COMMAND", "all three original commands are required")
    command_keys = {"label", "command", "cwd", "exitCode", "stdout", "stderr", "stdoutSha256", "stderrSha256"}
    for index, (row, label, command) in enumerate(zip(rows, LABELS, expected_commands())):
        require(isinstance(row, dict) and set(row) == command_keys | ({"testsRun"} if index else set()),
                "COMMAND", label + ": missing or unexpected command fields")
        require(row["label"] == label and row["command"] == command and row["cwd"] == "<repo>"
                and type(row["exitCode"]) is int and row["exitCode"] == 0,
                "COMMAND", label + ": original command did not pass unchanged")
        for stream in ("stdout", "stderr"):
            name = label + "." + stream
            require(row[stream] == name, "COMMAND", label + ": unexpected raw output path")
            require(row[stream + "Sha256"] == digest(raw[name]), "COMMAND_HASH",
                    label + ": original raw " + stream + " digest mismatch")
        if index:
            output = raw[label + ".stderr"]
            match = re.search(rb"Ran (\d+) tests? in ", output)
            require(match is not None and int(match[1]) > 0 and type(row["testsRun"]) is int
                    and row["testsRun"] == int(match[1]) and not re.search(rb"\bskipped=[1-9]\d*", output)
                    and re.search(rb"(?m)^OK\s*$", output) is not None,
                    "COMMAND", label + ": nonzero, complete, zero-skip unittest result required")
    require(raw[SCAN] == raw["architecture-cli.stdout"] and receipt["scanSha256"] == digest(raw[SCAN]),
            "SCAN", "scan must be the original CLI stdout, unchanged")
    scan = load_json(raw[SCAN], SCAN)
    require(isinstance(scan, dict) and set(scan) == {"ok", "sources", "trustedSourcesNotParsed", "edges", "diagnostics"},
            "SCAN", "unexpected scan fields")
    require(scan["ok"] is True and scan["diagnostics"] == [] and receipt["diagnosticCount"] == 0,
            "SCAN", "the original scanner must report zero diagnostics")
    require(scan["sources"] == inventory["sources"]
            and scan["trustedSourcesNotParsed"] == inventory["trustedSourcesNotParsed"],
            "SCAN", "original scan does not cover the complete current inventory")
    edges = scan["edges"]
    sources = set(inventory["sources"])
    require(isinstance(edges, list) and len(edges) == receipt["edgeCount"], "SCAN", "edge count differs")
    for edge in edges:
        require(isinstance(edge, dict) and set(edge) == {"source", "target", "line"}
                and isinstance(edge["source"], str) and edge["source"] in sources
                and isinstance(edge["target"], str) and edge["target"] in sources
                and type(edge["line"]) is int and edge["line"] > 0, "SCAN", "invalid original edge")
    require(edges == sorted(edges, key=lambda edge: (edge["source"], edge["target"], edge["line"]))
            and len({(edge["source"], edge["target"], edge["line"]) for edge in edges}) == len(edges),
            "SCAN", "original edges must be unique and sorted")
    require(raw[REPORT] == expected_report(receipt, manifest), "REPORT", "report differs from the original receipt")
    semantic = {"scan": scan, "ownedCount": receipt["ownedCount"], "exclusionCount": receipt["exclusionCount"],
                "edgeCount": receipt["edgeCount"], "testsRun": {row["label"]: row["testsRun"] for row in rows[1:]}}
    return receipt, canonical(semantic)


def file_manifest(raw):
    return {name: {"bytes": len(data), "sha256": digest(data)} for name, data in sorted(raw.items())}


def origin(receipt):
    return {field: receipt[field] for field in ("sourceHead", "runId", "runAttempt", "adoptedMain")}


def validate_bundle(path, key, context, manifest, inventory):
    require(HEX64.fullmatch(path.name) is not None and path.parent.name == key,
            "BUNDLE", "invalid bundle identity: " + str(path))
    raw = read_artifact(path, bundled=True)
    envelope = load_json(read_regular(path / "bundle.json", "BUNDLE"), "bundle.json")
    require(isinstance(envelope, dict) and set(envelope) == {"schema", "inputKey", "context", "origin", "files"}
            and envelope["schema"] == BUNDLE_SCHEMA, "BUNDLE", "invalid bundle envelope")
    require(envelope["inputKey"] == key and envelope["context"] == context and digest(canonical(context)) == key,
            "CLOSURE", "bundle dependency closure differs from current inputs")
    require(envelope["files"] == file_manifest(raw), "RAW_HASH", "bundle raw bytes or SHA-256 differ")
    require(digest(raw[RECEIPT]) == path.name, "BUNDLE", "receipt does not match its immutable directory name")
    receipt, semantic = validate_artifact(raw, context, manifest, inventory)
    require(envelope["origin"] == origin(receipt), "BUNDLE", "bundle rewrites the original execution origin")
    return receipt, semantic, raw


def store_path(root, store):
    path = Path(store)
    return no_symlinks(path if path.is_absolute() else root / path, "BUNDLE")


def import_artifact(root, artifact, store=DEFAULT_STORE):
    """Run only beside the original raw artifact on its clean execution head."""
    root = Path(root).resolve()
    head = git(root, "rev-parse", "HEAD").decode("ascii").strip()
    clean = subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=root)
    require(clean.returncode == 0, "DIRTY", "import requires the clean original execution checkout")
    context, manifest, inventory = _current_context(root)
    require(context["generatorLfSha256"] == GENERATOR_LF_SHA256, "GENERATOR",
            "receipt v1 import requires the reviewed original generator")
    tracked = [MANIFEST, SCANNER, GENERATOR, *TESTS, *(entry["path"] for entry in context["inputs"])]
    git(root, "ls-files", "--error-unmatch", "--", *tracked)
    raw = read_artifact(Path(artifact))
    receipt, _ = validate_artifact(raw, context, manifest, inventory)
    require(receipt["sourceHead"] == head, "SOURCE_HEAD",
            "raw artifact must be imported on its original sourceHead; copy prepared bundles for adoption")
    key = digest(canonical(context))
    store = store_path(root, store)
    target = store / key / digest(raw[RECEIPT])
    envelope = {"schema": BUNDLE_SCHEMA, "inputKey": key, "context": context,
                "origin": origin(receipt), "files": file_manifest(raw)}
    if target.exists():
        _, _, existing = validate_bundle(target, key, context, manifest, inventory)
        require(existing == raw, "BUNDLE", "an immutable bundle already exists with different raw bytes")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=".architecture-import-", dir=target.parent))
        try:
            for name, data in raw.items():
                (temporary / name).write_bytes(data)
            (temporary / "bundle.json").write_bytes(json_bytes(envelope))
            try:
                os.rename(temporary, target)
            except FileExistsError:
                _, _, existing = validate_bundle(target, key, context, manifest, inventory)
                require(existing == raw, "BUNDLE", "concurrent immutable bundle differs")
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
    # Validate every origin under this dependency key, including a prior bad or
    # contradictory candidate. An import may never hide it behind a new green.
    result = check_store(root, store)
    return {"ok": True, "inputKey": key, "path": str(target), "origin": origin(receipt),
            "origins": result["origins"]}


def check_store(root, store=DEFAULT_STORE, materialize=None):
    root = Path(root).resolve()
    context, manifest, inventory = _current_context(root)
    key = digest(canonical(context))
    directory = store_path(root, store) / key
    require(directory.is_dir() and not directory.is_symlink(), "STALE",
            "no raw architecture bundle matches the complete current inputs: " + key)
    candidates = sorted(directory.iterdir())
    require(bool(candidates), "STALE", "no raw architecture bundle exists for " + key)
    valid = []
    for candidate in candidates:
        receipt, semantic, raw = validate_bundle(candidate, key, context, manifest, inventory)
        valid.append((candidate, receipt, semantic, raw))
    require(len({item[2] for item in valid}) == 1, "CONTRADICTORY",
            "same-input architecture origins disagree about scan, counts, or executed tests")
    selected, _, _, selected_raw = valid[0]
    if materialize is not None:
        destination = no_symlinks(Path(materialize).absolute(), "MATERIALIZE")
        require(not destination.resolve().is_relative_to(root) and not destination.exists(), "MATERIALIZE",
                "materialization requires a new directory outside the repository")
        destination.mkdir(parents=True, exist_ok=False)
        for name, raw in selected_raw.items():
            (destination / name).write_bytes(raw)
    origins = [{**origin(receipt), "receiptSha256": path.name, "bundle": str(path)}
               for path, receipt, _, _ in valid]
    return {"ok": True, "inputKey": key, "selected": str(selected), "origins": origins,
            "ownedCount": context["ownedCount"], "exclusionCount": context["exclusionCount"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    for action in ("import", "check"):
        command = subparsers.add_parser(action)
        command.add_argument("--root", type=Path, default=ROOT)
        command.add_argument("--store", type=Path, default=Path(DEFAULT_STORE))
        if action == "import":
            command.add_argument("--artifact", type=Path, required=True)
        else:
            command.add_argument("--materialize", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "import":
            result = import_artifact(args.root, args.artifact, args.store)
        else:
            result = check_store(args.root, args.store, args.materialize)
    except (EvidenceError, OSError) as error:
        print(json.dumps({"ok": False, "error": getattr(error, "code", "IO"), "message": str(error)},
                         ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
