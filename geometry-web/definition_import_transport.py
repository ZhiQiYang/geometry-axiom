"""Server-owned transport for definition-import/1.

The bridge reads a directory it owns. The HTTP body may carry the source
scene, but that text is never placed in request.json or in the command line.
"""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

SCENE_MAX = 16 * 1024 * 1024
REQUEST_MAX = 1024 * 1024
READ_MAX = SCENE_MAX
PREVIEW_MAX = 20 * 1024 * 1024
_REQUIRED = {"schema", "expectedRevision", "sourceSceneSha256", "roots", "names"}


def _error(code, message):
    return json.dumps({"ok": False, "code": code, "error": message}, ensure_ascii=False).encode("utf-8")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 不得包含重複欄位")
        result[key] = value
    return result


def _constant(_value):
    raise ValueError("JSON 不接受非有限數值")


def read_request(body, ask_bridge):
    if not isinstance(body, bytes) or len(body) > READ_MAX:
        return _error("CAPACITY", "來源場景必須是完整位元組，且不得超過 16 MiB")
    if not body:
        return _error("INPUT", "來源場景不得為空")
    try:
        text = body.decode("utf-8")
        if "\0" in text:
            raise ValueError("來源場景不得含 NUL")
    except (ValueError, UnicodeError) as error:
        return _error("INPUT", str(error))
    path = None
    try:
        with tempfile.NamedTemporaryFile("wb", suffix=".scene", delete=False) as stream:
            stream.write(body)
            path = Path(stream.name)
        return ask_bridge(f"definition-import-read {path}")
    finally:
        if path is not None:
            path.unlink(missing_ok=True)


def preview_request(body, ask_bridge):
    if not isinstance(body, bytes) or len(body) > PREVIEW_MAX:
        return _error("CAPACITY", "匯入預覽必須是完整位元組，且不得超過 20 MiB")
    if not body:
        return _error("INPUT", "匯入預覽不得為空")
    try:
        text = body.decode("utf-8")
        if "\0" in text:
            raise ValueError("匯入資料不得含 NUL")
        data = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, UnicodeError) as error:
        return _error("INPUT", str(error))
    if not isinstance(data, dict) or set(data) != _REQUIRED | {"sourceScene"}:
        return _error("SCHEMA", "需要 definition-import/1、expectedRevision、來源摘要、roots、names 與 sourceScene")
    scene = data.get("sourceScene")
    if not isinstance(scene, str) or "\0" in scene:
        return _error("SCHEMA", "sourceScene 必須是不含 NUL 的字串")
    scene_bytes = scene.encode("utf-8")
    if len(scene_bytes) > SCENE_MAX:
        return _error("CAPACITY", "來源場景超過 16 MiB")
    reduced = {key: value for key, value in data.items() if key != "sourceScene"}
    if set(reduced) != _REQUIRED or reduced.get("schema") != "definition-import/1":
        return _error("SCHEMA", "需要 definition-import/1、expectedRevision、來源摘要、roots 與 names")
    revision = reduced.get("expectedRevision")
    if type(revision) is not int or revision < 0:
        return _error("SCHEMA", "expectedRevision 必須是非負整數")
    digest = reduced.get("sourceSceneSha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        return _error("SCHEMA", "sourceSceneSha256 必須是 64 位小寫十六進位")
    if hashlib.sha256(scene_bytes).hexdigest() != digest:
        return _error("INVALID", "來源場景摘要不符")
    request_bytes = json.dumps(reduced, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(request_bytes) > REQUEST_MAX:
        return _error("CAPACITY", "匯入請求超過 1 MiB")
    directory = Path(tempfile.mkdtemp(prefix="definition-import-"))
    try:
        (directory / "request.json").write_bytes(request_bytes)
        (directory / "source.scene").write_bytes(scene_bytes)
        return ask_bridge(f"definition-import-preview {directory}")
    finally:
        shutil.rmtree(directory, ignore_errors=False)
