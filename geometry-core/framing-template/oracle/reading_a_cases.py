"""Frozen approved case identities keep an empty rejection list testable."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_required():
    raw = (HERE / "reading-a-expected-buildable.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != "b5e4e707a4fc4b2710db237d0252d67104e0a555a50a875e79de2ad43c7d46c0":
        raise ValueError("Reading A frozen approval identities changed")
    data = json.loads(raw)
    if data.get("schema") != "reading-a-required-buildable-cases/1" or data.get("target_verdict") != "buildable":
        raise ValueError("Reading A approved-case schema or verdict changed")
    result = {}
    for name, count in (("step", 528), ("step_mirror", 1056)):
        rows = [tuple(row) for row in data[name]]
        if len(rows) != count or len(set(rows)) != count or any(len(row) != 2 for row in rows):
            raise ValueError("Reading A approved-case identities changed: " + name)
        result[name] = set(rows)
    return result


def expected_for_run(required, room_ids, ci):
    """Only CI may restrict approval identities to its explicit sample."""
    return {key for key in required if not ci or key[0].split("|")[0] in room_ids}


def coverage_problems(observed, required):
    """Missing cases and changed verdicts remain separate evidence."""
    return {
        "missing": sorted(required - observed.keys()),
        "not_buildable": sorted((key, observed[key]) for key in required & observed.keys()
                                if observed[key] != "buildable"),
    }
