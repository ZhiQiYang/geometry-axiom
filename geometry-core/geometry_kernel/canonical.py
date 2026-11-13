"""Integer-only, deterministic JSON encoding without host policy."""
import hashlib
import json
from .errors import EvaluationError


def canonical_bytes(value):
    """Encode JSON with exact integers, sorted keys and no insignificant spaces."""
    def check(item):
        if item is None or type(item) in (bool, int):
            return
        if isinstance(item, str):
            try:
                item.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise EvaluationError("INVALID", "UNICODE", "Unpaired Unicode surrogate") from exc
            return
        if isinstance(item, list):
            for child in item:
                check(child)
            return
        if isinstance(item, dict) and all(isinstance(key, str) for key in item):
            for key, child in item.items():
                check(key)
                check(child)
            return
        raise EvaluationError("INVALID", "JSON_TYPE", "Only JSON objects, arrays, strings, booleans, null and integers are supported")
    check(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def strict_json_loads(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise EvaluationError("INVALID", "DUPLICATE_KEY", "Duplicate JSON key: " + key)
            result[key] = value
        return result
    def forbidden(value):
        raise EvaluationError("INVALID", "JSON_TYPE", "Non-integer JSON number: " + value)
    try:
        result = json.loads(text, object_pairs_hook=pairs,
                            parse_float=forbidden, parse_constant=forbidden)
        canonical_bytes(result)
        return result
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise EvaluationError("INVALID", "JSON_PARSE", str(exc)) from exc
