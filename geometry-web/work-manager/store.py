"""Private, transactional work queue. No network calls or external authority."""
from __future__ import annotations

import contextlib
import copy
import datetime as dt
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from urllib.parse import urlsplit

SCHEMA_VERSION = 1
SOURCE_KINDS = {"manual_snapshot", "git", "github", "operator"}
EXECUTION_STATES = {"unknown", "unassigned", "active", "stopped", "blocked", "finished"}
EVENT_KINDS = {"task", "assignment", "result", "github"}
TASK_FIELDS = {"title", "refs", "scope", "files", "branch", "dependencies",
               "approval_constraints", "required_acceptance", "not_before", "head_sha", "head_tree_sha",
               "node_kind", "parent_id"}
ASSIGNMENT_FIELDS = {"owner_thread", "execution_status", "reserved", "reason", "files"}
RESULT_FIELDS = {"evidence", "pr", "pr_metadata", "head_sha", "execution_status", "owner_thread", "summary", "completed_actions"}
PR_METADATA_FIELDS = {"number", "url", "head_sha", "merged", "draft", "ci", "ci_runs", "updated_at"}
TRANSITION_ACTIONS = {"ready_for_review", "ready", "publish_bundle", "publish_pr", "create_pr"}
RECEIPT_ACTIONS = {"review_pr", "review_integration", "verify_acceptance", "verify_scope",
                   "verify_source", "collect_result", "resolve_blocker", "continue_work"}
CI_STATUSES = {"queued", "in_progress", "completed", "pending", "waiting", "requested"}
CI_CONCLUSIONS = {"success", "passed", "failure", "failed", "neutral", "cancelled",
                  "skipped", "timed_out", "action_required", "stale", "startup_failure", "unknown"}
VALID_BINDINGS = {"valid", "merged_commit", "tree_equivalent"}
STALE_AFTER_HOURS = 24
MAX_INPUT_BYTES = 8 * 1024 * 1024


class ValidationError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def iso(value):
    return value.astimezone(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def timestamp(value, label="timestamp"):
    if not isinstance(value, str) or len(value) > 64:
        raise ValidationError(f"{label} must be an ISO 8601 timestamp with timezone")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{label} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValidationError(f"{label} must include a timezone")
    return parsed.astimezone(dt.timezone.utc)


def _object(value, label, allowed, required=()):
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be an object")
    unexpected, missing = set(value) - set(allowed), set(required) - set(value)
    if unexpected:
        raise ValidationError(f"{label}: unsupported fields {sorted(unexpected)}")
    if missing:
        raise ValidationError(f"{label}: missing fields {sorted(missing)}")


def _string(value, label, nullable=False, maximum=4000):
    if nullable and value is None:
        return
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValidationError(f"{label} must be a nonempty string (max {maximum})")
    if any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise ValidationError(f"{label} contains control characters")


def _integer(value, label, minimum=1):
    if type(value) is not int or value < minimum:
        raise ValidationError(f"{label} must be an integer >= {minimum}")


def _enum(value, allowed, label, nullable=False):
    if nullable and value is None:
        return
    if not isinstance(value, str) or value not in allowed:
        raise ValidationError(f"{label} must be one of {sorted(allowed)}")


def _strings(value, label):
    if not isinstance(value, list):
        raise ValidationError(f"{label} must be an array")
    for item in value:
        _string(item, label)
    if len(value) != len(set(value)):
        raise ValidationError(f"{label} contains duplicates")


def _url(value, label):
    _string(value, label, maximum=2048)
    parsed = urlsplit(value)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc or parsed.username or parsed.password:
        raise ValidationError(f"{label} must be an HTTP(S) URL without credentials")


def _sha(value, label):
    if value is None:
        return
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", value):
        raise ValidationError(f"{label} requires a complete 40- or 64-character SHA")


def _files(value):
    _strings(value, "files")
    for item in value:
        if (item.startswith(("/", "\\")) or "\\" in item or ":" in item
                or any(part in {"", ".", ".."} for part in item.rstrip("/").split("/"))):
            raise ValidationError("files must use canonical repository-relative paths")


def _validate_ci(job):
    _object(job, "CI job", {"name", "sha", "status", "conclusion", "runner_id", "steps", "url", "id", "run_id", "attempt"},
            {"name", "sha", "status", "conclusion"})
    _string(job["name"], "CI job name")
    _sha(job["sha"], "CI job SHA")
    _enum(job["status"], CI_STATUSES, "CI status", nullable=True)
    _enum(job["conclusion"], CI_CONCLUSIONS, "CI conclusion", nullable=True)
    if "url" in job:
        _url(job["url"], "CI URL")
    if "runner_id" in job:
        _integer(job["runner_id"], "runner_id", 0)
    if "steps" in job:
        _validate_steps(job["steps"])
    for key in ("id", "run_id"):
        if key in job:
            _ci_identity(job[key], f"CI job {key}")
    if "attempt" in job:
        _integer(job["attempt"], "CI job attempt")


def _ci_identity(value, label):
    if type(value) is int:
        _integer(value, label)
    else:
        _string(value, label, maximum=200)


def _validate_ci_runs(runs):
    if not isinstance(runs, list):
        raise ValidationError("ci_runs must be an array")
    identities = set()
    for run in runs:
        _object(run, "CI run", {"id", "sha", "status", "conclusion", "attempt", "url", "job_count"},
                {"id", "sha", "status", "conclusion", "job_count"})
        _ci_identity(run["id"], "CI run id")
        _sha(run["sha"], "CI run SHA")
        _enum(run["status"], CI_STATUSES, "CI run status", nullable=True)
        _enum(run["conclusion"], CI_CONCLUSIONS, "CI run conclusion", nullable=True)
        _integer(run["job_count"], "CI run job_count", 0)
        if "attempt" in run:
            _integer(run["attempt"], "CI run attempt")
        if "url" in run:
            _url(run["url"], "CI run URL")
        identity = (str(run["id"]), run.get("attempt"))
        if identity in identities:
            raise ValidationError("duplicate CI run id/attempt")
        identities.add(identity)


def _validate_ci_fields(value, label):
    if "ci" in value:
        if not isinstance(value["ci"], list):
            raise ValidationError(f"{label} ci must be an array")
        for job in value["ci"]:
            _validate_ci(job)
    if "ci_runs" in value:
        _validate_ci_runs(value["ci_runs"])


def _validate_pr_metadata(pr):
    _object(pr, "pr_metadata", PR_METADATA_FIELDS, {"number", "url", "updated_at"})
    _integer(pr["number"], "PR number")
    _url(pr["url"], "PR URL")
    timestamp(pr["updated_at"], "PR updated_at")
    if "head_sha" in pr:
        _sha(pr["head_sha"], "PR head_sha")
    for key in ("merged", "draft"):
        if key in pr and type(pr[key]) is not bool:
            raise ValidationError(f"PR {key} must be boolean")
    _validate_ci_fields(pr, "PR metadata")


def _validate_steps(steps):
    if not isinstance(steps, list) or len(steps) > 2000:
        raise ValidationError("CI steps must be an array with at most 2000 entries")
    for step in steps:
        _object(step, "CI step", {"name", "status", "conclusion", "number", "started_at", "completed_at"})
        if "name" in step:
            _string(step["name"], "CI step name")
        if "status" in step:
            _enum(step["status"], CI_STATUSES, "CI step status", nullable=True)
        if "conclusion" in step:
            _enum(step["conclusion"], CI_CONCLUSIONS, "CI step conclusion", nullable=True)
        if "number" in step:
            _integer(step["number"], "CI step number", 0)
        for key in ("started_at", "completed_at"):
            if step.get(key) is not None:
                timestamp(step[key], f"CI step {key}")


def _validate_receipt(receipt):
    _object(receipt, "completed action", {"action", "input_pin", "timestamp", "summary"},
            {"action", "input_pin", "timestamp"})
    _enum(receipt["action"], RECEIPT_ACTIONS, "completed action")
    if not isinstance(receipt["input_pin"], str) or not re.fullmatch(r"[0-9a-f]{64}", receipt["input_pin"]):
        raise ValidationError("completed action input_pin must be the exact lowercase SHA256 action pin")
    timestamp(receipt["timestamp"], "completed action timestamp")
    if "summary" in receipt:
        _string(receipt["summary"], "completed action summary")


def _validate_inventory(inventory, kind):
    rows_key = "issues" if kind == "issue" else "prs"
    _object(inventory, f"{kind} inventory", {"repository", "complete", rows_key},
            {"repository", "complete", rows_key})
    repository = inventory["repository"]
    if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValidationError("inventory repository must be owner/repo")
    if type(inventory["complete"]) is not bool:
        raise ValidationError("inventory complete must be boolean")
    rows = inventory[rows_key]
    if not isinstance(rows, list) or len(rows) > 5000:
        raise ValidationError("inventory rows must be an array with at most 5000 entries")
    allowed = {"number", "url", "task_ids", "title"}
    if kind == "pr":
        allowed |= {"head_sha", "base", "base_sha", "draft", "merged"}
    normalized = {}
    for entry in rows:
        _object(entry, f"{kind} inventory row", allowed, {"number", "url", "task_ids"})
        _integer(entry["number"], "inventory number")
        _url(entry["url"], "inventory URL")
        _strings(entry["task_ids"], "inventory task_ids")
        if "title" in entry:
            _string(entry["title"], "inventory title", nullable=True)
        for key in ("head_sha", "base_sha"):
            if key in entry:
                _sha(entry[key], f"inventory {key}")
        if "base" in entry:
            _string(entry["base"], "inventory base", nullable=True)
        for key in ("draft", "merged"):
            if key in entry and entry[key] is not None and type(entry[key]) is not bool:
                raise ValidationError(f"inventory {key} must be boolean or null")
        previous = normalized.get(entry["number"])
        if previous:
            for key in (set(previous) & set(entry)) - {"task_ids"}:
                if previous[key] != entry[key]:
                    raise ValidationError("duplicate inventory number has conflicting metadata")
            previous.update({key: copy.deepcopy(value) for key, value in entry.items() if key != "task_ids"})
            previous["task_ids"] = sorted(set(previous["task_ids"]) | set(entry["task_ids"]))
        else:
            normalized[entry["number"]] = copy.deepcopy(entry)
    return normalized


def _validate_evidence(evidence):
    _object(evidence, "evidence", {"id", "criterion", "kind", "timestamp", "sha", "result", "url",
                                 "runner_id", "steps", "expires_at", "summary", "tree_sha", "equivalent_head_sha"},
            {"id", "criterion", "kind", "timestamp", "sha", "result"})
    for key in ("id", "criterion", "kind"):
        _string(evidence[key], f"evidence {key}")
    timestamp(evidence["timestamp"], "evidence timestamp")
    _sha(evidence["sha"], "evidence SHA")
    _enum(evidence["result"], {"passed", "failed", "unknown"}, "evidence result")
    for key in ("tree_sha", "equivalent_head_sha"):
        if key in evidence:
            _sha(evidence[key], f"evidence {key}")
    if "expires_at" in evidence:
        timestamp(evidence["expires_at"], "evidence expires_at")
    if "url" in evidence:
        _url(evidence["url"], "evidence URL")
    if "runner_id" in evidence:
        _integer(evidence["runner_id"], "evidence runner_id", 0)
    if "steps" in evidence:
        _validate_steps(evidence["steps"])
    if "summary" in evidence:
        _string(evidence["summary"], "evidence summary")


def validate_event(event):
    _object(event, "event", {"event_id", "task_id", "kind", "version", "occurred_at", "data"},
            {"event_id", "task_id", "kind", "version", "occurred_at", "data"})
    for key in ("event_id", "task_id"):
        _string(event[key], key, maximum=200)
    _enum(event["kind"], EVENT_KINDS, "event kind")
    _integer(event["version"], "event version")
    timestamp(event["occurred_at"], "occurred_at")
    data = event["data"]
    if event["kind"] == "task":
        _object(data, "task data", TASK_FIELDS)
        for key in ("title", "scope", "branch"):
            if key in data:
                _string(data[key], key)
        for key in ("dependencies", "required_acceptance"):
            if key in data:
                _strings(data[key], key)
        if "files" in data:
            _files(data["files"])
        for key in ("head_sha", "head_tree_sha"):
            if key in data:
                _sha(data[key], key)
        if "node_kind" in data:
            _enum(data["node_kind"], {"work", "umbrella"}, "node_kind")
        if "parent_id" in data:
            _string(data["parent_id"], "parent_id", nullable=True, maximum=200)
        if "not_before" in data and data["not_before"] is not None:
            timestamp(data["not_before"], "not_before")
        if "refs" in data:
            if not isinstance(data["refs"], list):
                raise ValidationError("refs must be an array")
            for ref in data["refs"]:
                _object(ref, "ref", {"kind", "url", "number"}, {"kind", "url"})
                _string(ref["kind"], "ref kind")
                _url(ref["url"], "ref URL")
                if "number" in ref:
                    _integer(ref["number"], "ref number")
        if "approval_constraints" in data:
            if not isinstance(data["approval_constraints"], list):
                raise ValidationError("approval_constraints must be an array")
            for rule in data["approval_constraints"]:
                _object(rule, "approval", {"action", "status", "reason", "scope"}, {"action", "status"})
                _string(rule["action"], "approval action")
                _enum(rule["status"], {"required", "granted", "denied"}, "approval status")
                if "scope" in rule:
                    _enum(rule["scope"], {"action", "completion"}, "approval scope")
                if "reason" in rule:
                    _string(rule["reason"], "approval reason")
    elif event["kind"] == "assignment":
        _object(data, "assignment data", ASSIGNMENT_FIELDS, {"execution_status"})
        _enum(data["execution_status"], EXECUTION_STATES, "execution_status")
        if "owner_thread" in data:
            _string(data["owner_thread"], "owner_thread", nullable=True, maximum=200)
        if data["execution_status"] == "active" and not data.get("owner_thread"):
            raise ValidationError("active assignment requires owner_thread")
        if "reserved" in data and type(data["reserved"]) is not bool:
            raise ValidationError("reserved must be boolean")
        if "reason" in data:
            _string(data["reason"], "assignment reason")
        if "files" in data:
            _files(data["files"])
    else:
        _object(data, "result data", RESULT_FIELDS)
        if "execution_status" in data:
            _enum(data["execution_status"], EXECUTION_STATES, "execution_status")
        if "owner_thread" in data:
            _string(data["owner_thread"], "owner_thread", nullable=True, maximum=200)
        if "summary" in data:
            _string(data["summary"], "result summary")
        if "head_sha" in data:
            _sha(data["head_sha"], "result head_sha")
        if "evidence" in data:
            if not isinstance(data["evidence"], list):
                raise ValidationError("evidence must be an array")
            for evidence in data["evidence"]:
                _validate_evidence(evidence)
        if "completed_actions" in data:
            if not isinstance(data["completed_actions"], list) or len(data["completed_actions"]) > 100:
                raise ValidationError("completed_actions must be an array with at most 100 receipts")
            for receipt in data["completed_actions"]:
                _validate_receipt(receipt)
        if "pr" in data and data["pr"] is not None:
            pr = data["pr"]
            _object(pr, "pr", {"number", "url", "head_sha", "merged", "merged_head_sha",
                              "review_state", "reviewed_sha", "merge_commit_sha", "ci", "ci_runs", "draft", "updated_at"},
                    {"number", "url", "head_sha", "merged", "review_state"})
            _integer(pr["number"], "PR number")
            _url(pr["url"], "PR URL")
            _sha(pr["head_sha"], "PR head_sha")
            for key in ("merged_head_sha", "merge_commit_sha", "reviewed_sha"):
                if key in pr:
                    _sha(pr[key], f"PR {key}")
            if type(pr["merged"]) is not bool or ("draft" in pr and type(pr["draft"]) is not bool):
                raise ValidationError("PR merged/draft must be boolean")
            _enum(pr["review_state"], {"unknown", "pending", "approved", "changes_requested"}, "PR review_state")
            if "updated_at" in pr:
                timestamp(pr["updated_at"], "PR updated_at")
            _validate_ci_fields(pr, "PR")
        if "pr_metadata" in data:
            if "pr" in data:
                raise ValidationError("pr_metadata and pr are mutually exclusive")
            _validate_pr_metadata(data["pr_metadata"])
    if not data:
        raise ValidationError("event data must not be empty")


def validate_snapshot(snapshot):
    _object(snapshot, "snapshot", {"schema_version", "source", "events", "issue_inventory", "pr_inventory"},
            {"schema_version", "source", "events"})
    if type(snapshot["schema_version"]) is not int or snapshot["schema_version"] != SCHEMA_VERSION:
        raise ValidationError("unsupported schema_version")
    source = snapshot["source"]
    _object(source, "source", {"id", "kind", "version", "as_of", "status", "url", "source_sha", "error", "ci", "ci_runs"},
            {"id", "kind", "version", "as_of", "status"})
    _string(source["id"], "source id", maximum=200)
    _enum(source["kind"], SOURCE_KINDS, "source kind")
    _integer(source["version"], "source version")
    timestamp(source["as_of"], "source as_of")
    _enum(source["status"], {"ok", "error"}, "source status")
    if "url" in source:
        _url(source["url"], "source URL")
    if "source_sha" in source:
        _sha(source["source_sha"], "source SHA")
    if "error" in source:
        _string(source["error"], "source error")
    if "ci" in source or "ci_runs" in source:
        if source["status"] == "error":
            raise ValidationError("failed source cannot assert new CI results")
        _validate_ci_fields(source, "source")
    if not isinstance(snapshot["events"], list):
        raise ValidationError("events must be an array")
    if source["status"] == "error" and snapshot["events"]:
        raise ValidationError("failed fetch must have events: []; old state is retained")
    for kind in ("issue", "pr"):
        if kind + "_inventory" in snapshot:
            if source["status"] == "error":
                raise ValidationError("failed fetch must omit inventory; previous coverage is retained")
            _validate_inventory(snapshot[kind + "_inventory"], kind)
    ids = set()
    for event in snapshot["events"]:
        validate_event(event)
        if event["event_id"] in ids:
            raise ValidationError("duplicate event_id within one snapshot")
        ids.add(event["event_id"])
    if len(canonical(snapshot).encode("utf-8")) > MAX_INPUT_BYTES:
        raise ValidationError("snapshot exceeds 8 MiB")


def files_overlap(left, right):
    left, right = left.rstrip("/"), right.rstrip("/")
    return (left == right or left.startswith(right + "/") or right.startswith(left + "/")
            or fnmatch.fnmatchcase(left, right) or fnmatch.fnmatchcase(right, left))


def ci_steps_result(runner_id, steps):
    """An asserted success and nonempty container are not execution evidence."""
    if not runner_id or not isinstance(steps, list) or not steps:
        return "not_run"
    if any(not isinstance(step, dict) or not isinstance(step.get("name"), str)
           or not step["name"].strip() or not step.get("status") or not step.get("conclusion")
           for step in steps):
        return "not_run"
    if any(step["status"] != "completed" for step in steps):
        return "unknown"
    conclusions = [step["conclusion"] for step in steps]
    if any(value in {"failure", "failed", "cancelled", "timed_out", "action_required"} for value in conclusions):
        return "failed"
    if all(value == "skipped" for value in conclusions):
        return "not_run"
    if not all(value in {"success", "passed", "skipped", "neutral"} for value in conclusions):
        return "unknown"
    return "passed" if any(value in {"success", "passed"} for value in conclusions) else "unknown"


def same_sha(left, right):
    return bool(left and right and left.lower() == right.lower())


def merged_exact(task):
    pr = task.get("pr") or {}
    return bool(pr.get("merged") and same_sha(pr.get("head_sha"), task["head_sha"])
                and same_sha(pr.get("merged_head_sha"), task["head_sha"]))


def evidence_binding(evidence, task):
    """Preserve the tested SHA; only these explicit bindings may satisfy a gate."""
    pr = task.get("pr") or {}
    if not evidence.get("sha") or not task["head_sha"]:
        return "unknown"
    if evidence["kind"] == "postmerge_test":
        return ("merged_commit" if merged_exact(task)
                and same_sha(pr.get("merge_commit_sha"), evidence["sha"]) else "stale")
    if same_sha(evidence["sha"], task["head_sha"]):
        return "valid"
    if (evidence["kind"] == "local_test"
            and same_sha(evidence.get("tree_sha"), task.get("head_tree_sha"))
            and same_sha(evidence.get("equivalent_head_sha"), task["head_sha"])):
        return "tree_equivalent"
    return "stale"


def project_ci_job(original, expected_sha):
    job = copy.deepcopy(original)
    steps = ci_steps_result(job.get("runner_id"), job.get("steps"))
    if expected_sha and job.get("sha") and not same_sha(job["sha"], expected_sha):
        result = "stale"
    elif steps == "not_run":
        result = "not_run"
    elif not expected_sha or not job.get("sha"):
        result = "unknown"
    elif not same_sha(job["sha"], expected_sha):
        result = "stale"
    elif steps != "passed":
        result = steps
    elif job["status"] == "completed" and job["conclusion"] in {"success", "passed"}:
        result = "passed"
    else:
        result = "unknown" if job["status"] != "completed" else "failed"
    job["effective_result"] = result
    return job


def project_ci_runs(originals, jobs, expected_sha):
    """Runs attest their own outcome and actual jobs; neither list replaces the other."""
    runs = []
    for original in originals:
        run = copy.deepcopy(original)
        matching = [job for job in jobs if (
            ("run_id" in job and str(job["run_id"]) == str(run["id"])
             and ("attempt" not in run or job.get("attempt") == run["attempt"]))
            or ("run_id" not in job and len(originals) == 1 and same_sha(job.get("sha"), run["sha"]))) ]
        run["observed_job_count"] = len(matching)
        if expected_sha and run.get("sha") and not same_sha(run["sha"], expected_sha):
            result = "stale"
        elif not expected_sha or not run.get("sha"):
            result = "unknown"
        elif run["status"] == "completed" and run["conclusion"] in {
                "failure", "failed", "cancelled", "timed_out", "action_required", "startup_failure"}:
            result = "failed"
        elif run["job_count"] == 0 or not matching:
            result = "not_run"
        elif len(matching) != run["job_count"]:
            result = "unknown"
        elif any(job["effective_result"] != "passed" for job in matching):
            outcomes = {job["effective_result"] for job in matching}
            result = next((value for value in ("failed", "stale", "not_run") if value in outcomes), "unknown")
        elif run["status"] == "completed" and run["conclusion"] in {"success", "passed"}:
            result = "passed"
        else:
            result = "unknown"
        run["effective_result"] = result
        runs.append(run)
    return runs


def set_task_head(task, head_sha, changed_at, origin="work", guarded=False):
    # A published PR head is a separate source fact. It cannot replace an
    # explicitly recorded work head, even when the remote poll/update is newer.
    if origin == "pr" and task.get("head_origin") == "work" and task["head_sha"]:
        return
    if same_sha(task["head_sha"], head_sha) or task["head_sha"] == head_sha:
        if head_sha and origin == "work":
            task["head_origin"] = "work"
        return
    previous_at = task.get("head_changed_at")
    if guarded and previous_at and timestamp(changed_at) <= timestamp(previous_at):
        return
    task["head_sha"] = head_sha
    task["head_changed_at"] = changed_at
    task["head_origin"] = origin if head_sha else "unknown"


def apply_pr_metadata(task, metadata):
    previous = task.get("pr")
    same_pr = (previous is not None and previous["number"] == metadata["number"]
               and reference_key(previous["url"]) == reference_key(metadata["url"]))
    pr = copy.deepcopy(previous) if same_pr else {
        "number": metadata["number"], "url": metadata["url"], "head_sha": None,
        "merged": False, "review_state": "unknown",
    }
    # Metadata cannot inject a review. Existing exact-head claims remain auditable
    # and become stale naturally when either task or PR head changes.
    pr.update(copy.deepcopy(metadata))
    task["pr"] = pr
    if metadata.get("head_sha"):
        set_task_head(task, metadata["head_sha"], metadata["updated_at"], origin="pr", guarded=True)


def action_input_pin(task, action, tasks):
    # Pin semantic inputs, not polling time, receipt history, old-head proofs,
    # source versions, or a newly repeated proof of the same result.
    applicable_ids = {evidence["id"] for evidence in task["evidence"]
                      if evidence["applicable_to_current_head"]}
    selected_ids = {entry["evidence_id"] for entry in task["acceptance"]
                    if entry["evidence_id"] in applicable_ids}
    selected = [{
        key: evidence.get(key) for key in ("criterion", "kind", "sha", "tree_sha",
                                         "equivalent_head_sha", "binding_kind", "validity", "effective_result")
    } for evidence in task["evidence"] if evidence["id"] in selected_ids]
    pr = task.get("pr")
    inputs = {
        "task_id": task["id"], "action": action,
        "head_sha": task["head_sha"], "head_tree_sha": task.get("head_tree_sha"),
        "scope": task["scope"], "files": sorted(task["files"]), "branch": task["branch"],
        "owner_thread": task["owner_thread"], "execution_status": task["execution_status"],
        "reserved": task["reserved"], "delivery_status": task["delivery_status"],
        "pr": {key: pr.get(key) for key in ("number", "head_sha", "reviewed_sha",
               "effective_review_state", "merged", "merged_head_sha", "merge_commit_sha", "draft")} if pr else None,
        "ci": sorted(({key: job.get(key) for key in ("name", "sha", "effective_result")}
                      for job in task["ci"]), key=canonical),
        "required_acceptance": sorted(task["required_acceptance"]),
        "acceptance": sorted(selected, key=canonical),
        "missing_acceptance": sorted(entry["criterion"] for entry in task["acceptance"]
                                     if entry["evidence_id"] not in applicable_ids),
        "constraints": sorted(({"action": rule["action"], "status": rule["status"],
                                "scope": rule.get("scope", "completion")}
                               for rule in task["approval_constraints"]), key=canonical),
        "dependencies": sorted(({"id": dependency, "head_sha": tasks.get(dependency, {}).get("head_sha"),
                                  "delivery_status": tasks.get(dependency, {}).get("delivery_status", "unknown")}
                                 for dependency in task["dependencies"]), key=canonical),
        "not_before": task["not_before"],
    }
    # Keep existing receipt pins unchanged when old records have no run evidence.
    if pr and "ci_runs" in pr:
        inputs["ci_runs"] = sorted(({key: run.get(key) for key in (
            "id", "sha", "status", "conclusion", "attempt", "job_count",
            "observed_job_count", "effective_result")}
            for run in task["ci_runs"]), key=canonical)
    return digest(inputs)


def empty_coverage():
    return {"count": 0, "captured": 0, "missing_scope": 0, "repositories": [],
            "pr_count": 0, "pr_captured": 0, "pr_missing_scope": 0,
            "pr_repositories": [], "pr_links": []}


def reference_key(url):
    parsed = urlsplit(url)
    path = parsed.path.rstrip("/")
    if parsed.hostname and parsed.hostname.lower() in {"github.com", "www.github.com"}:
        path = path.lower()
    return ((parsed.hostname or "").lower(), path)


def reference_number(url):
    match = re.search(r"/(?:pull|issues)/([0-9]+)/?$", urlsplit(url).path)
    return int(match.group(1)) if match else None


def reference_repository(url):
    match = re.fullmatch(r"/([^/]+)/([^/]+)/(?:pull|issues)/[0-9]+/?", urlsplit(url).path)
    return f"{match.group(1)}/{match.group(2)}" if match else None


def update_inventory(registries, snapshot):
    header = snapshot["source"]
    for kind in ("issue", "pr"):
        inventory = snapshot.get(kind + "_inventory")
        if inventory is None:
            continue
        repository = inventory["repository"]
        key = repository.casefold()
        old = registries[kind].get(key)
        if old and timestamp(header["as_of"]) < timestamp(old["as_of"]):
            continue
        incoming = _validate_inventory(inventory, kind)
        rows = {} if inventory["complete"] or old is None else copy.deepcopy(old["rows"])
        for number, entry in incoming.items():
            previous = rows.get(number, {})
            rows[number] = {**previous, **copy.deepcopy(entry),
                            "_source": {"id": header["id"], "version": header["version"], "as_of": header["as_of"]}}
        registries[kind][key] = {
            "repository": repository, "source_id": header["id"], "source_version": header["version"],
            "as_of": header["as_of"], "complete": inventory["complete"], "rows": rows}


def project_coverage(registries, tasks):
    coverage, links = empty_coverage(), {}

    def add_pr(url, number=None, repository=None):
        key = reference_key(url)
        if key not in links:
            links[key] = {
                "number": number if number is not None else reference_number(url), "url": url,
                "repository": repository or reference_repository(url), "title": None,
                "task_ids": [], "head_sha": None, "base": None, "base_sha": None,
                "draft": None, "merged": None, "listed_in_current_inventory": False, "sources": [],
            }
        return links[key]

    def add_source(link, source):
        if source not in link["sources"]:
            link["sources"].append(copy.deepcopy(source))

    def scope_status(task_ids):
        work = [tasks[task_id] for task_id in task_ids if tasks[task_id]["node_kind"] == "work"]
        return "known" if work and all(task["scope"] and task["files"] for task in work) else "missing"

    def validate_ids(task_ids):
        if any(task_id not in tasks for task_id in task_ids):
            raise ValidationError("inventory task_ids must reference existing tasks; whole snapshot rejected")
        return sorted(set(task_ids))

    for task in tasks.values():
        references = [ref for ref in task["refs"] if ref["kind"] in {"pr", "pull_request"}]
        if task["pr"]:
            references.append({"url": task["pr"]["url"], "number": task["pr"]["number"]})
        for ref in references:
            link = add_pr(ref["url"], ref.get("number"))
            if task["id"] not in link["task_ids"]:
                link["task_ids"].append(task["id"])
            for provenance in task["source_provenance"]:
                add_source(link, {"id": provenance["id"], "version": provenance["version"], "as_of": provenance["as_of"]})
            if task["pr"] and reference_key(task["pr"]["url"]) == reference_key(ref["url"]):
                for field in ("head_sha", "draft", "merged"):
                    if field in task["pr"]:
                        link[field] = task["pr"][field]

    for registry in sorted(registries["pr"].values(), key=lambda value: value["repository"].casefold()):
        repo = {key: value for key, value in registry.items() if key != "rows"}
        repo["prs"] = []
        for entry in sorted(registry["rows"].values(), key=lambda value: value["number"]):
            explicit_ids = validate_ids(entry["task_ids"])
            link = add_pr(entry["url"], entry["number"], registry["repository"])
            link["task_ids"] = sorted(set(link["task_ids"]) | set(explicit_ids))
            link["listed_in_current_inventory"] = True
            for field in ("title", "head_sha", "base", "base_sha", "draft", "merged"):
                if field in entry:
                    link[field] = entry[field]
            add_source(link, entry["_source"])
            row = {key: entry.get(key) for key in ("number", "url", "title", "head_sha", "base", "base_sha", "draft", "merged")}
            row.update(task_ids=list(link["task_ids"]), captured=bool(link["task_ids"]),
                       scope_status=scope_status(link["task_ids"]),
                       source_id=entry["_source"]["id"], source_version=entry["_source"]["version"],
                       as_of=entry["_source"]["as_of"])
            repo["prs"].append(row)
        repo.update(count=len(repo["prs"]), captured=sum(row["captured"] for row in repo["prs"]),
                    missing_scope=sum(row["scope_status"] == "missing" for row in repo["prs"]))
        coverage["pr_repositories"].append(repo)

    for link in links.values():
        link["task_ids"].sort()
        link["sources"].sort(key=canonical)
        link["captured"] = bool(link["task_ids"])
        link["scope_status"] = scope_status(link["task_ids"])
    coverage["pr_links"] = sorted(links.values(), key=lambda value: (value["repository"] or "", value["number"] or 0, value["url"]))

    for registry in sorted(registries["issue"].values(), key=lambda value: value["repository"].casefold()):
        repo = {key: value for key, value in registry.items() if key != "rows"}
        repo["issues"] = []
        for entry in sorted(registry["rows"].values(), key=lambda value: value["number"]):
            associated = set(validate_ids(entry["task_ids"]))
            for task in tasks.values():
                if any(ref["kind"] == "issue" and reference_key(ref["url"]) == reference_key(entry["url"])
                       for ref in task["refs"]):
                    associated.add(task["id"])
            task_ids = sorted(associated)
            repo["issues"].append({
                "number": entry["number"], "url": entry["url"], "title": entry.get("title"),
                "task_ids": task_ids, "captured": bool(task_ids), "scope_status": scope_status(task_ids),
                "pr_links": [copy.deepcopy(link) for link in coverage["pr_links"] if associated.intersection(link["task_ids"])],
                "source_id": entry["_source"]["id"], "source_version": entry["_source"]["version"],
                "as_of": entry["_source"]["as_of"],
            })
        repo.update(count=len(repo["issues"]), captured=sum(row["captured"] for row in repo["issues"]),
                    missing_scope=sum(row["scope_status"] == "missing" for row in repo["issues"]))
        coverage["repositories"].append(repo)
    for key in ("count", "captured", "missing_scope"):
        coverage[key] = sum(repo[key] for repo in coverage["repositories"])
        coverage["pr_" + key] = sum(repo[key] for repo in coverage["pr_repositories"])
    return coverage


class Store:
    def __init__(self, path):
        path = Path(path)
        self.path = path if path.suffix in {".db", ".sqlite", ".sqlite3"} else path / "state.sqlite3"
        self.data_dir = self.path.parent
        self.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.data_dir.resolve() not in {Path("/"), Path("/tmp"), Path("/workspace")}:
            self.data_dir.chmod(0o700)
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
        except FileExistsError:
            pass
        with self._db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY, current TEXT NOT NULL, last_good TEXT);
                CREATE TABLE IF NOT EXISTS snapshots (
                    ordinal INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL, source_version INTEGER NOT NULL,
                    payload TEXT NOT NULL, checksum TEXT NOT NULL,
                    UNIQUE(source_id, source_version));
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY, source_id TEXT NOT NULL,
                    source_version INTEGER NOT NULL, task_id TEXT NOT NULL, kind TEXT NOT NULL,
                    version INTEGER NOT NULL, occurred_at TEXT NOT NULL, payload TEXT NOT NULL,
                    applied INTEGER NOT NULL,
                    UNIQUE(source_id, task_id, kind, version));
            """)
        self.path.chmod(0o600)

    @contextlib.contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA synchronous=FULL")
        try:
            with db:
                yield db
        finally:
            db.close()

    def close(self):
        """Connections are deliberately short lived."""

    def _ledger_health(self, db):
        """Validate persisted rows too: earlier versions accepted unsafe inputs."""
        issues, snapshots, evidence_ids = [], {}, {}
        source_rows = db.execute("SELECT id,current,last_good FROM sources").fetchall()
        snapshot_rows = db.execute("SELECT source_id,source_version,payload,checksum FROM snapshots ORDER BY ordinal").fetchall()
        event_rows = db.execute("SELECT event_id,source_id,source_version,task_id,kind,version,payload,applied FROM events").fetchall()
        registered_tasks = {row["task_id"] for row in event_rows if row["applied"] == 1}

        def issue(code, message, row=None):
            item = {"code": code, "message": message}
            if row:
                for key in ("event_id", "task_id", "source_id"):
                    if key in row.keys():
                        item[key] = row[key]
            issues.append(item)

        for row in source_rows:
            try:
                for column in ("current", "last_good"):
                    if row[column] is None:
                        continue
                    header = json.loads(row[column])
                    validate_snapshot({"schema_version": 1, "source": header, "events": []})
                    if header["id"] != row["id"] or (column == "last_good" and header["status"] != "ok"):
                        raise ValidationError("source row does not match its validated header")
            except (ValueError, TypeError, KeyError):
                issue("source_record_invalid", "來源紀錄未通過資料契約驗證；保留原始資料。")
        for row in snapshot_rows:
            try:
                snapshot = json.loads(row["payload"])
                validate_snapshot(snapshot)
                if (snapshot["source"]["id"] != row["source_id"] or
                        snapshot["source"]["version"] != row["source_version"] or
                        digest(snapshot) != row["checksum"]):
                    raise ValidationError("snapshot identity or checksum mismatch")
                for kind in ("issue", "pr"):
                    if kind + "_inventory" in snapshot:
                        entries = _validate_inventory(snapshot[kind + "_inventory"], kind)
                        if any(task_id not in registered_tasks for entry in entries.values() for task_id in entry["task_ids"]):
                            raise ValidationError("inventory references an unregistered task")
                snapshots[(row["source_id"], row["source_version"])] = snapshot
            except (ValueError, TypeError, KeyError):
                issue("snapshot_record_invalid", "快照內容或 checksum 未通過驗證；保留原始資料。", row)
        for row in event_rows:
            try:
                event = json.loads(row["payload"])
                validate_event(event)
                if any(event[key] != row[key] for key in ("event_id", "task_id", "kind", "version")):
                    raise ValidationError("event columns differ from immutable payload")
                if row["applied"] not in (0, 1):
                    raise ValidationError("event applied flag is invalid")
                snapshot = snapshots.get((row["source_id"], row["source_version"]))
                if snapshot is None or not any(canonical(item) == canonical(event) for item in snapshot["events"]):
                    raise ValidationError("event does not match its source snapshot")
                for evidence in event["data"].get("evidence", []):
                    identity = (event["task_id"], evidence["id"])
                    encoded = canonical(evidence)
                    if identity in evidence_ids and evidence_ids[identity] != encoded:
                        issue("evidence_identity_conflict", "相同證據 ID 存有互相衝突的內容，不能判定通過。", row)
                    evidence_ids[identity] = encoded
            except (ValueError, TypeError, KeyError):
                issue("event_record_invalid", "事件內容未通過資料契約驗證，不能推導工作狀態。", row)
        return {"status": "invalid" if issues else "ok", "issues": issues,
                "read_only": bool(issues), "backup_preserved": False,
                "row_count": {"sources": len(source_rows), "snapshots": len(snapshot_rows), "events": len(event_rows)}}

    def _preserve_invalid_backup(self):
        # Called while the SQLite read/write transaction holds a stable ledger.
        # Never rewrite rows in an invalid database or disclose its local path.
        original = self.path.read_bytes()
        checksum = hashlib.sha256(original).hexdigest()
        directory = self.data_dir / "backups"
        directory.mkdir(mode=0o700, exist_ok=True)
        directory.chmod(0o700)
        destination = directory / ("invalid-ledger-" + checksum + ".sqlite3")
        if not destination.exists() or hashlib.sha256(destination.read_bytes()).hexdigest() != checksum:
            descriptor, temporary = tempfile.mkstemp(prefix=".invalid-ledger-", dir=directory)
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(original)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(temporary, 0o600)
                os.replace(temporary, destination)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        destination.chmod(0o600)
        preserved = hashlib.sha256(destination.read_bytes()).hexdigest() == checksum
        return preserved, checksum

    def _assert_healthy(self, db):
        health = self._ledger_health(db)
        if health["status"] == "invalid":
            try:
                self._preserve_invalid_backup()
            except OSError:
                pass
            raise ValidationError("existing ledger is invalid and read-only; inspect reconcile diagnostics; no rows were changed")
        return health

    def _read(self, db, now, strict=False):
        health = self._ledger_health(db)
        if health["status"] == "invalid":
            if strict:
                raise ValidationError("resulting ledger failed validation; transaction rejected")
            try:
                preserved, checksum = self._preserve_invalid_backup()
                health.update(backup_preserved=preserved, backup_checksum=checksum)
            except OSError:
                health["issues"].append({"code": "backup_failed", "message": "私有備份尚未成功；原始資料庫仍未改寫。"})
            state = {
                "schema_version": SCHEMA_VERSION, "generated_at": iso(now), "last_synced_at": None,
                "sources": [], "tasks": [], "ready": [], "ready_read_only": [], "ready_write": [],
                "ready_counts": {"all": 0, "read_only": 0, "write": 0, "wait": 0},
                "alerts": [{"code": "ledger_invalid", "severity": "error", "task_id": None,
                            "message": "資料校驗失敗；原紀錄已保留，停止派工與完成判定。"}],
                "store_health": health, "payload_hash": None,
                "coverage": empty_coverage(),
            }
        else:
            state = self._project(db, now)
            state["store_health"] = health
        state["state_hash"] = digest({key: value for key, value in state.items()
                                     if key not in {"generated_at", "state_hash"}})
        return state

    def _import(self, db, snapshot):
        validate_snapshot(snapshot)
        source = snapshot["source"]
        encoded = canonical(snapshot)
        existing = db.execute("SELECT payload FROM snapshots WHERE source_id=? AND source_version=?",
                              (source["id"], source["version"])).fetchone()
        if existing:
            if existing["payload"] != encoded:
                raise ValidationError("source version collision: same version has different content")
            return {"inserted": 0, "ignored": 0, "duplicates": len(snapshot["events"]), "source_updated": False}
        previous = db.execute("SELECT current,last_good FROM sources WHERE id=?", (source["id"],)).fetchone()
        current = json.loads(previous["current"]) if previous else None
        if current and current["kind"] != source["kind"]:
            raise ValidationError("source kind cannot change for an existing source id")
        source_newer = not current or (
            source["version"] > current["version"] and timestamp(source["as_of"]) >= timestamp(current["as_of"]))
        counts = {"inserted": 0, "ignored": 0, "duplicates": 0, "source_updated": source_newer}
        evidence_identities = {}
        for row in db.execute("SELECT task_id,payload FROM events WHERE kind IN ('result','github')"):
            for evidence in json.loads(row["payload"])["data"].get("evidence", []):
                evidence_identities[(row["task_id"], evidence["id"])] = canonical(evidence)
        for event in snapshot["events"]:
            for evidence in event["data"].get("evidence", []):
                identity = (event["task_id"], evidence["id"])
                encoded_evidence = canonical(evidence)
                if identity in evidence_identities and evidence_identities[identity] != encoded_evidence:
                    raise ValidationError("evidence_id collision: proof identity is immutable; use a new id for a new attempt")
                evidence_identities[identity] = encoded_evidence
        for event in sorted(snapshot["events"], key=lambda e: (e["version"], timestamp(e["occurred_at"]), e["event_id"])):
            known = db.execute("SELECT source_id,payload FROM events WHERE event_id=?", (event["event_id"],)).fetchone()
            if known:
                if known["source_id"] != source["id"] or known["payload"] != canonical(event):
                    raise ValidationError("event_id collision: different content; whole snapshot rejected")
                counts["duplicates"] += 1
                continue
            same_version = db.execute(
                "SELECT event_id FROM events WHERE source_id=? AND task_id=? AND kind=? AND version=?",
                (source["id"], event["task_id"], event["kind"], event["version"])).fetchone()
            if same_version:
                raise ValidationError("event version collision: ambiguous stream update")
            latest = db.execute(
                "SELECT version,occurred_at FROM events WHERE source_id=? AND task_id=? AND kind=? AND applied=1 "
                "ORDER BY version DESC LIMIT 1", (source["id"], event["task_id"], event["kind"])).fetchone()
            applied = source_newer and source["status"] == "ok" and (
                not latest or (event["version"] > latest["version"]
                               and timestamp(event["occurred_at"]) >= timestamp(latest["occurred_at"])))
            db.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?)",
                       (event["event_id"], source["id"], source["version"], event["task_id"],
                        event["kind"], event["version"],
                        timestamp(event["occurred_at"]).isoformat(timespec="microseconds"),
                        canonical(event), int(applied)))
            counts["inserted" if applied else "ignored"] += 1
        db.execute("INSERT INTO snapshots(source_id,source_version,payload,checksum) VALUES(?,?,?,?)",
                   (source["id"], source["version"], encoded, digest(snapshot)))
        if source_newer:
            last_good = canonical(source) if source["status"] == "ok" else (previous["last_good"] if previous else None)
            db.execute("INSERT INTO sources VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET "
                       "current=excluded.current,last_good=excluded.last_good",
                       (source["id"], canonical(source), last_good))
        return counts

    def import_snapshot(self, snapshot):
        snapshot = json.loads(canonical(snapshot))
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            self._assert_healthy(db)
            operation = self._import(db, snapshot)
            # Commit only after the entire resulting projection is usable.
            state = self._read(db, utc_now(), strict=True)
        state["operation"] = operation
        return state

    def _project(self, db, now):
        source_rows = db.execute("SELECT current,last_good FROM sources ORDER BY id").fetchall()
        event_rows = db.execute("SELECT * FROM events").fetchall()
        # Read the original timestamp, including subsecond precision. Existing
        # databases from the first slice may contain second-normalized columns.
        event_rows = sorted(event_rows, key=lambda row: (
            timestamp(json.loads(row["payload"])["occurred_at"]), row["version"],
            {"task": 0, "assignment": 1}.get(row["kind"], 2), row["event_id"]))
        source_versions, observation_headers, observed_tasks, ci_observations = {}, {}, {}, {}
        inventories = {"issue": {}, "pr": {}}
        event_by_id = {row["event_id"]: row for row in event_rows}
        latest_stream_versions = {}
        for row in event_rows:
            if row["applied"]:
                key = (row["source_id"], row["task_id"], row["kind"])
                latest_stream_versions[key] = max(latest_stream_versions.get(key, 0), row["version"])
        for row in db.execute("SELECT source_id,source_version,payload FROM snapshots ORDER BY ordinal"):
            snapshot = json.loads(row["payload"])
            header = snapshot["source"]
            source_versions[(row["source_id"], row["source_version"])] = header
            previous = observation_headers.get(header["id"])
            newer = not previous or (header["version"] > previous["version"]
                                    and timestamp(header["as_of"]) >= timestamp(previous["as_of"]))
            if not newer:
                continue
            observation_headers[header["id"]] = header
            if header["status"] != "ok":
                continue
            if "ci" in header or "ci_runs" in header:
                observation = copy.deepcopy(ci_observations.get(header["id"], {}))
                observation.update({key: copy.deepcopy(header[key]) for key in ("ci", "ci_runs") if key in header})
                observation.update({"source_sha": header.get("source_sha"), "as_of": header["as_of"]})
                ci_observations[header["id"]] = observation
            update_inventory(inventories, snapshot)
            for event in snapshot["events"]:
                original = event_by_id.get(event["event_id"])
                stream = (header["id"], event["task_id"], event["kind"])
                if (original is not None and original["applied"] and original["source_id"] == header["id"]
                        and event["version"] == latest_stream_versions.get(stream)):
                    observed_tasks[(event["task_id"], header["id"])] = header
        sources, source_by_id, source_ci_inputs = [], {}, {}
        for row in source_rows:
            source = json.loads(row["current"])
            good = json.loads(row["last_good"]) if row["last_good"] else None
            source["last_success_at"] = good["as_of"] if good else None
            source["last_success_version"] = good["version"] if good else None
            source["last_success_sha"] = good.get("source_sha") if good else None
            ci_observation = ci_observations.get(source["id"])
            if ci_observation:
                expected_sha = good.get("source_sha") if good else None
                raw_jobs = copy.deepcopy(ci_observation.get("ci", []))
                source["ci"] = [project_ci_job(job, expected_sha) for job in raw_jobs]
                source["ci_observed_at"] = ci_observation["as_of"]
                source_ci_inputs[source["id"]] = {"source_sha": expected_sha, "ci": raw_jobs}
                if "ci_runs" in ci_observation:
                    source["ci_runs"] = project_ci_runs(ci_observation["ci_runs"], source["ci"], expected_sha)
                    source_ci_inputs[source["id"]]["ci_runs"] = copy.deepcopy(ci_observation["ci_runs"])
            age = (now - timestamp(good["as_of"])).total_seconds() if good else None
            source["freshness"] = ("error" if source["status"] == "error" else
                                   "future" if timestamp(source["as_of"]) > now else
                                   "stale" if age is not None and age > STALE_AFTER_HOURS * 3600 else "current")
            source["mode"] = "手動匯入快照" if source["kind"] == "manual_snapshot" else "已記錄的來源快照"
            sources.append(source)
            source_by_id[source["id"]] = source
        tasks, evidence_by_task, task_provenance, receipts_by_task = {}, {}, {}, {}
        for row in event_rows:
            event, task_id = json.loads(row["payload"]), row["task_id"]
            if not row["applied"]:
                continue
            task = tasks.setdefault(task_id, {
                "id": task_id, "title": task_id, "refs": [], "scope": "", "files": [],
                "branch": None, "dependencies": [], "approval_constraints": [],
                "required_acceptance": [], "not_before": None, "head_sha": None, "head_tree_sha": None,
                "head_changed_at": None, "head_origin": "unknown",
                "owner_thread": None, "execution_status": "unknown", "reserved": False,
                "pr": None, "evidence": [], "assignment_history": [], "source_ids": [],
                "source_provenance": [], "last_event_at": None, "metadata_known": False,
                "completed_actions": [],
                "node_kind": "work", "parent_id": None, "child_ids": [],
            })
            if row["source_id"] not in task["source_ids"]:
                task["source_ids"].append(row["source_id"])
            task_provenance.setdefault(task_id, {})[row["source_id"]] = source_versions[
                (row["source_id"], row["source_version"])]
            task["last_event_at"] = event["occurred_at"]
            data = event["data"]
            if event["kind"] == "task":
                if "head_sha" in data:
                    set_task_head(task, data["head_sha"], event["occurred_at"])
                task.update({key: copy.deepcopy(value) for key, value in data.items() if key != "head_sha"})
                task["metadata_known"] = True
            elif event["kind"] == "assignment":
                if "owner_thread" in data:
                    task["owner_thread"] = data["owner_thread"]
                task["execution_status"] = data["execution_status"]
                task["reserved"] = data.get("reserved", False)
                task["assignment_files"] = data.get("files", task["files"])
            else:
                if "head_sha" in data:
                    set_task_head(task, data["head_sha"], event["occurred_at"])
                if "pr" in data:
                    task["pr"] = copy.deepcopy(data["pr"])
                    if data["pr"] and data["pr"].get("head_sha"):
                        set_task_head(task, data["pr"]["head_sha"], event["occurred_at"], origin="pr")
                if "pr_metadata" in data:
                    apply_pr_metadata(task, data["pr_metadata"])
                if "execution_status" in data and (
                        "owner_thread" not in data or data["owner_thread"] == task["owner_thread"]):
                    task["execution_status"] = data["execution_status"]
                for item in data.get("evidence", []):
                    evidence_by_task.setdefault(task_id, {})[item["id"]] = copy.deepcopy(item)
                for receipt in data.get("completed_actions", []):
                    key = (receipt["action"], receipt["input_pin"])
                    previous = receipts_by_task.setdefault(task_id, {}).get(key)
                    if (previous is None or
                            (timestamp(previous["timestamp"]) > now >= timestamp(receipt["timestamp"])) or
                            (timestamp(previous["timestamp"]) <= now and timestamp(receipt["timestamp"]) <= now
                             and timestamp(receipt["timestamp"]) >= timestamp(previous["timestamp"]))):
                        receipts_by_task[task_id][key] = copy.deepcopy(receipt)
        for row in event_rows:
            if row["kind"] == "assignment" and row["task_id"] in tasks:
                event = json.loads(row["payload"])
                tasks[row["task_id"]]["assignment_history"].append({
                    **event, "source_id": row["source_id"], "source_version": row["source_version"],
                    "applied": bool(row["applied"]),
                })
        alerts = []
        def alert(task, code, message, severity="warning"):
            item = {"code": code, "severity": severity, "task_id": task["id"] if task else None, "message": message}
            alerts.append(item)
            if task is not None:
                task["alerts"].append(item)
        for source in sources:
            if source["freshness"] == "error":
                alert(None, "source_error", f"來源 {source['id']} 查詢失敗；保留上次資料。")
            elif source["freshness"] == "future":
                alert(None, "source_future", f"來源 {source['id']} 的資料時間在未來，需核對時鐘。")
            elif source["freshness"] == "stale":
                alert(None, "source_stale", f"來源 {source['id']} 超過 24 小時未同步。")
            for job in source.get("ci", []):
                if job["effective_result"] == "not_run":
                    alert(None, "ci_not_run", f"來源 {source['id']} 的 CI {job['name']} 未實際執行，不算通過。")
                elif job["effective_result"] == "stale":
                    alert(None, "ci_stale", f"來源 {source['id']} 的 CI {job['name']} 並非來源的 exact SHA。")
                elif job["effective_result"] == "unknown":
                    alert(None, "ci_unknown", f"來源 {source['id']} 的 CI {job['name']} 缺少可核對的執行證據。")
            if "ci_runs" in source and not source["ci_runs"]:
                alert(None, "ci_unknown", f"來源 {source['id']} 尚未取得 CI run 紀錄。")
            for run in source.get("ci_runs", []):
                if run["effective_result"] != "passed":
                    alert(None, "ci_" + run["effective_result"],
                          f"來源 {source['id']} 的 CI run {run['id']} 為 {run['effective_result']}，不算通過。")
        for task in tasks.values():
            task["alerts"] = []
            task["source_ids"].sort()
            task["source_provenance"] = []
            for sid in task["source_ids"]:
                contributing = task_provenance[task["id"]][sid]
                observed = observed_tasks.get((task["id"], sid), contributing)
                freshness = ("error" if source_by_id[sid]["status"] == "error" else
                             "future" if timestamp(observed["as_of"]) > now else
                             "stale" if (now - timestamp(observed["as_of"])).total_seconds() >
                             STALE_AFTER_HOURS * 3600 else "current")
                task["source_provenance"].append({
                    "id": sid, "kind": contributing["kind"], "version": contributing["version"],
                    "as_of": contributing["as_of"], "status": source_by_id[sid]["status"],
                    "source_sha": contributing.get("source_sha"), "url": contributing.get("url"),
                    "freshness": freshness, "last_verified_at": observed["as_of"],
                    "observed_version": observed["version"],
                })
                if freshness in {"error", "future", "stale"}:
                    alert(task, "source_" + freshness, f"來源 {sid} {'失聯，保留舊資料' if freshness == 'error' else '需要重新核對時間與資料'}。")
            if timestamp(task["last_event_at"]) > now:
                alert(task, "event_future", "工作事件時間在未來，不能據此派工或完成。")
            if not task["metadata_known"]:
                alert(task, "unknown_task", "缺少工作範圍資料，待核對。")
            if task["node_kind"] == "work" and (not task["scope"] or not task["files"]):
                alert(task, "scope_unknown", "工作範圍或檔案清單待核；只可讀取審查，不可派出執行工作。")
            task["evidence"] = sorted(evidence_by_task.get(task["id"], {}).values(),
                                      key=lambda e: (timestamp(e["timestamp"]), e["id"]))
            task["completed_actions"] = sorted(
                receipts_by_task.get(task["id"], {}).values(), key=lambda receipt: timestamp(receipt["timestamp"]))[-100:]
            latest_by_criterion = {}
            for evidence in task["evidence"]:
                binding = evidence_binding(evidence, task)
                applicable = binding in VALID_BINDINGS
                validity = binding
                if applicable and evidence.get("expires_at") and timestamp(evidence["expires_at"]) <= now:
                    validity = "expired"
                elif applicable and timestamp(evidence["timestamp"]) > now:
                    validity = "future"
                elif applicable and evidence["kind"] in {"ci", "ci_job", "github_actions"}:
                    step_result = ci_steps_result(evidence.get("runner_id"), evidence.get("steps"))
                    if step_result != "passed":
                        validity = "not_run" if step_result == "not_run" else "ci_" + step_result
                evidence["binding_kind"] = binding
                evidence["applicable_to_current_head"] = applicable
                evidence["bound_head_sha"] = task["head_sha"] if applicable else None
                evidence["validity"] = validity
                evidence["effective_result"] = ("failed" if validity == "ci_failed" else
                                                  evidence["result"] if validity in VALID_BINDINGS else "unknown")
                previous = latest_by_criterion.get(evidence["criterion"])
                rank = lambda e: (e["applicable_to_current_head"], timestamp(e["timestamp"]),
                                   {"passed": 0, "unknown": 1, "failed": 2}[e["effective_result"]])
                if previous is None or rank(evidence) >= rank(previous):
                    latest_by_criterion[evidence["criterion"]] = evidence
            valid_attempts = [e for e in task["evidence"] if e["validity"] in VALID_BINDINGS | {"ci_failed"}]
            task["last_verified_evidence"] = copy.deepcopy(max(
                valid_attempts, key=lambda e: (timestamp(e["timestamp"]),
                                               {"passed": 0, "unknown": 1, "failed": 2}[e["effective_result"]])
            )) if valid_attempts else None
            task["acceptance"] = [{"criterion": criterion,
                                   "result": latest_by_criterion.get(criterion, {}).get("effective_result", "unknown"),
                                   "evidence_id": latest_by_criterion.get(criterion, {}).get("id")}
                                  for criterion in task["required_acceptance"]]
            acceptance_ok = bool(task["required_acceptance"]) and all(x["result"] == "passed" for x in task["acceptance"])
            if any(e["validity"] in {"stale", "expired", "future"} for e in task["evidence"]):
                alert(task, "evidence_stale", "有驗證已過期、時間未到或不屬於目前 head；不得作完成依據。")
            if any(e["validity"] == "not_run" for e in task["evidence"]):
                alert(task, "ci_not_run", "CI 沒有 steps 或 runner 為 0：未執行，不算通過。")
            ci_ok, pr = True, task["pr"]
            task["published_head_sha"] = pr.get("head_sha") if pr else None
            task["head_alignment"] = (
                "unknown" if not task["head_sha"] or not task["published_head_sha"] else
                "same" if same_sha(task["head_sha"], task["published_head_sha"]) else "different")
            if task["head_alignment"] == "different":
                alert(task, "head_conflict", "工作 head 與 PR 已發布 head 不同；需核對未發布變更或來源，不能視為已整合。")
            task["ci_runs"] = []
            if pr:
                task["ci"] = [project_ci_job(job, task["head_sha"]) for job in pr.get("ci", [])]
                for job in task["ci"]:
                    if job["effective_result"] == "not_run":
                        alert(task, "ci_not_run", f"CI {job['name']} 未執行（缺 steps 或 runner）。")
                    elif job["effective_result"] == "stale":
                        alert(task, "ci_stale", f"CI {job['name']} 並非目前 head。")
                    ci_ok = ci_ok and job["effective_result"] == "passed"
                if "ci_runs" in pr:
                    task["ci_runs"] = project_ci_runs(pr["ci_runs"], task["ci"], task["head_sha"])
                    ci_ok = ci_ok and bool(task["ci_runs"]) and all(
                        run["effective_result"] == "passed" for run in task["ci_runs"])
                    if not task["ci_runs"]:
                        alert(task, "ci_unknown", "尚未取得 CI run 紀錄，不能視為全部通過。")
                    for run in task["ci_runs"]:
                        if run["effective_result"] != "passed":
                            alert(task, "ci_" + run["effective_result"],
                                  f"CI run {run['id']} 為 {run['effective_result']}，不算通過。")
                is_merged_exact = merged_exact(task)
                pr_head_exact = bool(task["head_sha"] and pr.get("head_sha")
                                     and pr["head_sha"].lower() == task["head_sha"].lower())
                # Preserve the imported review claim, but expose its current-head
                # validity separately so a stale approval is never shown as current.
                pr["effective_review_state"] = pr["review_state"] if pr_head_exact else (
                    "stale" if task["head_sha"] and pr.get("head_sha") else "unknown")
                if pr["review_state"] in {"approved", "changes_requested"}:
                    if not pr.get("reviewed_sha"):
                        pr["effective_review_state"] = "unknown"
                    elif not pr_head_exact or not same_sha(pr["reviewed_sha"], task["head_sha"]):
                        pr["effective_review_state"] = "stale"
                    if pr["effective_review_state"] != pr["review_state"]:
                        alert(task, "review_head_unknown", "彙總審查宣稱尚未綁定目前 reviewed_sha，不算本輪審查結論。")
                if not pr_head_exact:
                    alert(task, "pr_head_stale", "PR head 未確認或不屬於目前 head；舊審查與 CI 不能當作整合依據。")
                if pr["merged"] and not is_merged_exact:
                    alert(task, "merge_head_unknown", "PR 已合併的紀錄未證明包含目前 exact head，待核。")
                if (is_merged_exact and acceptance_ok and ci_ok and pr["effective_review_state"] == "approved"
                        and task["execution_status"] != "blocked"
                        and timestamp(task["last_event_at"]) <= now
                        and all(s["freshness"] != "future" for s in task["source_provenance"])):
                    task["delivery_status"] = "done"
                elif not ci_ok or task["head_alignment"] == "different":
                    task["delivery_status"] = "verification_pending"
                elif pr["effective_review_state"] != "approved" and not pr["merged"]:
                    task["delivery_status"] = "awaiting_review"
                elif (not acceptance_ok or not ci_ok or not pr_head_exact or
                      pr["effective_review_state"] != "approved" or (pr["merged"] and not is_merged_exact)):
                    task["delivery_status"] = "verification_pending"
                else:
                    task["delivery_status"] = "awaiting_integration"
            else:
                task["ci"] = []
                task["delivery_status"] = "no_pr" if task["execution_status"] != "unknown" else "unknown"
            completion_holds = [rule for rule in task["approval_constraints"]
                                if rule["status"] != "granted" and rule.get("scope", "completion") == "completion"]
            transition_holds = [rule for rule in task["approval_constraints"]
                                if rule["status"] != "granted" and rule["action"] in TRANSITION_ACTIONS]
            if completion_holds or (transition_holds and not (pr and pr["merged"])):
                task["delivery_status"] = "approval_blocked"
            if task["node_kind"] == "umbrella":
                task["delivery_status"] = "unknown"
                if task["owner_thread"]:
                    alert(task, "umbrella_owner", "彙總節點留有 owner 歷史；不可將它當作可派工的工作。")
            if task["execution_status"] == "blocked":
                alert(task, "blocked", "工作明確受阻，不能算完成。")
            if task["execution_status"] in {"stopped", "finished"} and task["delivery_status"] != "done":
                alert(task, "delivery_gap", "執行者已停止或結束；" + ("PR 仍需審查、驗收與整合。" if pr else "尚未記錄 PR，需接續交付。"))
            if task["node_kind"] == "work" and not task["owner_thread"] and task["delivery_status"] != "done":
                alert(task, "owner_missing", "尚未有執行者接手。", "info")
            if task["not_before"] and timestamp(task["not_before"]) > now:
                alert(task, "not_before", "排程尚未到開始時間。", "info")
            for rule in task["approval_constraints"]:
                if rule["status"] != "granted":
                    alert(task, "approval_required", f"{rule['action']} {'被拒絕' if rule['status'] == 'denied' else '等待明示批准'}；工具不會代為批准。",
                          "warning" if rule["status"] == "denied" else "info")
        visiting, visited, cycle_members = [], set(), set()
        def visit(task_id):
            if task_id in visiting:
                cycle_members.update(visiting[visiting.index(task_id):])
                return
            if task_id in visited or task_id not in tasks:
                return
            visiting.append(task_id)
            for dependency in tasks[task_id]["dependencies"]:
                visit(dependency)
            visiting.pop()
            visited.add(task_id)
        for task_id in tasks:
            visit(task_id)
        for task in tasks.values():
            if task["id"] in cycle_members:
                alert(task, "dependency_cycle", "依賴形成循環；先調整工作依賴。")
            for dependency in task["dependencies"]:
                if dependency not in tasks:
                    alert(task, "dependency_unknown", f"依賴 {dependency} 尚未匯入，待核。")
                elif tasks[dependency]["delivery_status"] != "done":
                    alert(task, "dependency_incomplete", f"依賴 {dependency} 尚未完成驗收與整合。", "info")
        for task in tasks.values():
            parent_id = task["parent_id"]
            if parent_id is not None:
                if parent_id not in tasks:
                    alert(task, "parent_unknown", f"關聯父節點 {parent_id} 尚未登記；這不是執行依賴。")
                else:
                    tasks[parent_id]["child_ids"].append(task["id"])
        parent_cycles = set()
        for task_id in tasks:
            chain, current = [], task_id
            while current in tasks and current not in chain:
                chain.append(current)
                current = tasks[current]["parent_id"]
            if current in chain:
                parent_cycles.update(chain[chain.index(current):])
        for task in tasks.values():
            task["child_ids"].sort()
            if task["id"] in parent_cycles:
                alert(task, "parent_cycle", "父子關聯形成循環；只提示關聯錯誤，不當作執行依賴。")
        active = [t for t in tasks.values() if t["owner_thread"] and t["execution_status"] == "active"
                  and t["delivery_status"] != "done"]
        for index, left in enumerate(active):
            for right in active[index + 1:]:
                if left["owner_thread"] == right["owner_thread"]:
                    continue
                overlaps = sorted({a for a in left["files"] for b in right["files"] if files_overlap(a, b)})
                if overlaps:
                    alert(left, "file_conflict", f"與 {right['id']} 的不同執行者同時修改：{', '.join(overlaps)}")
                    alert(right, "file_conflict", f"與 {left['id']} 的不同執行者同時修改：{', '.join(overlaps)}")
        for task in tasks.values():
            codes = {a["code"] for a in task["alerts"]}
            execution_denied = any(c["action"] in {"execute", "assign", "all"} and c["status"] != "granted"
                                   for c in task["approval_constraints"])
            external_denied = any(c["action"] in {"merge", "integrate", "all"} and c["status"] != "granted"
                                  for c in task["approval_constraints"])
            hard_blocks = {"source_error", "source_stale", "source_future", "event_future", "unknown_task",
                           "not_before", "dependency_cycle", "dependency_unknown", "dependency_incomplete",
                           "file_conflict", "blocked"}
            task["ready"] = False
            mode = "wait"
            if task["node_kind"] == "umbrella":
                code, action = "inspect_group", "檢視已關聯子工作；彙總節點不派工、不推算完成"
                mode = "none"
            elif task["delivery_status"] == "done":
                code, action = "done", "已完成必要驗收與 exact head 整合"
                mode = "none"
            elif task["execution_status"] == "active":
                code, action = "collect_result", "目前執行者仍在工作；等待回收其交付，不重複派出另一輪工作"
            elif task["delivery_status"] == "approval_blocked":
                code, action = "request_approval", "等待所列批准條件明確解除；請求紀錄不等於批准"
            elif codes & {"source_error", "source_stale", "source_future", "event_future", "unknown_task"}:
                code, action = "verify_source", "核對來源並匯入新快照（僅讀取）"
                mode = "read_only"
            elif codes & hard_blocks:
                code, action = "resolve_blocker", "釐清警示或依賴後再接續；不自動擴大權限"
            elif task["delivery_status"] == "awaiting_review":
                code, action = "review_pr", "讀取 PR 與驗收證據，提出審查意見（不代為批准）"
                mode = "read_only"
                task["ready"] = True
            elif task["delivery_status"] == "verification_pending":
                code, action = "verify_acceptance", "讀取並核對目前 head 的必要驗收證據；不隱含執行新測試"
                mode = "read_only"
                task["ready"] = True
            elif task["delivery_status"] == "awaiting_integration":
                code, action = ("request_approval", "整理整合前證據，等待明示批准") if external_denied else (
                    "review_integration", "核對整合條件並交負責人決定；工具不自動 merge")
                mode = "wait" if external_denied else "read_only"
                task["ready"] = not external_denied
            elif execution_denied or task["reserved"]:
                code, action = "request_approval", "整理執行前條件，等待明示批准或解除保留"
            elif "scope_unknown" in codes:
                code, action = "verify_scope", "核對工作範圍與檔案清單（僅讀取，不派工）"
                mode = "read_only"
                task["ready"] = True
            elif task["owner_thread"] and task["execution_status"] not in {"stopped", "finished", "unassigned"}:
                code, action = "collect_result", "確認已記錄執行者的狀態與交付，再決定接續派工"
                mode = "read_only"
            else:
                code, action = "continue_work", "在已記錄範圍內接續工作並回收 PR 交付"
                mode = "write"
                task["ready"] = True
            task["next_action_code"], task["next_action"] = code, action
            task["next_action_mode"] = mode
            task["next_action_pin"] = action_input_pin(task, code, tasks)
            receipt = receipts_by_task.get(task["id"], {}).get((code, task["next_action_pin"]))
            task["next_action_completed"] = bool(receipt and timestamp(receipt["timestamp"]) <= now)
            if task["next_action_completed"]:
                task["ready"] = False
                task["next_action_mode"] = "none"
                task["next_action"] = "已完成這組輸入的本輪核對；等待 head 或相關條件更新"
            task["automatic_actions"] = []
        task_list = sorted(tasks.values(), key=lambda task: task["id"])
        alerts.sort(key=lambda alert: (alert["task_id"] or "", alert["code"], alert["message"]))
        state = {
            "schema_version": SCHEMA_VERSION, "generated_at": iso(now),
            "last_synced_at": max((s["last_success_at"] for s in sources if s["last_success_at"]),
                                  key=timestamp, default=None),
            "sources": sources, "tasks": task_list, "alerts": alerts,
            "ready": [t for t in task_list if t["ready"]],
            "ready_read_only": [t for t in task_list if t["ready"] and t["next_action_mode"] == "read_only"],
            "ready_write": [t for t in task_list if t["ready"] and t["next_action_mode"] == "write"],
            "coverage": project_coverage(inventories, tasks),
        }
        state["ready_counts"] = {"all": len(state["ready"]), "read_only": len(state["ready_read_only"]),
                                 "write": len(state["ready_write"]),
                                 "wait": sum(t["next_action_mode"] == "wait" for t in task_list)}
        state["payload_hash"] = digest({
            "schema_version": SCHEMA_VERSION, "events": [
                {"source_id": row["source_id"], **json.loads(row["payload"])}
                for row in event_rows if row["applied"]],
            "inventories": {kind: {
                repo: {"complete": registry["complete"], "rows": [
                    {key: value for key, value in entry.items() if key != "_source"}
                    for entry in sorted(registry["rows"].values(), key=lambda value: value["number"])]}
                for repo, registry in sorted(inventories[kind].items())}
                for kind in ("issue", "pr")},
            "source_ci": source_ci_inputs,
        })
        state["state_hash"] = digest({key: value for key, value in state.items() if key != "generated_at"})
        return state

    def reconcile(self, now=None):
        if now is None:
            now = utc_now()
        elif isinstance(now, str):
            now = timestamp(now, "now")
        elif not isinstance(now, dt.datetime) or now.tzinfo is None:
            raise ValidationError("now must be a timezone-aware datetime or ISO timestamp")
        with self._db() as db:
            db.execute("BEGIN")
            return self._read(db, now)

    def _record(self, event_input, kind):
        event_input = json.loads(canonical(event_input))
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            self._assert_healthy(db)
            if "schema_version" in event_input:
                snapshot = event_input
                validate_snapshot(snapshot)
                if len(snapshot["events"]) != 1 or snapshot["events"][0]["kind"] != kind:
                    raise ValidationError(f"record-{kind} requires exactly one {kind} event")
            else:
                _object(event_input, "record", {"event_id", "task_id", "kind", "version", "occurred_at", "data", "source_id"},
                        {"event_id", "task_id", "version", "occurred_at", "data"})
                source_id = event_input.pop("source_id", "local-operator")
                event_input.setdefault("kind", kind)
                if event_input["kind"] != kind:
                    raise ValidationError(f"record command requires event kind {kind}")
                validate_event(event_input)
                previous = db.execute("SELECT current FROM sources WHERE id=?", (source_id,)).fetchone()
                source_version = json.loads(previous["current"])["version"] + 1 if previous else 1
                snapshot = {"schema_version": SCHEMA_VERSION,
                            "source": {"id": source_id, "kind": "operator", "version": source_version,
                                       "as_of": iso(utc_now()), "status": "ok"}, "events": [event_input]}
            event = snapshot["events"][0]
            duplicate = db.execute("SELECT source_id,payload FROM events WHERE event_id=?", (event["event_id"],)).fetchone()
            if duplicate:
                if duplicate["source_id"] != snapshot["source"]["id"] or duplicate["payload"] != canonical(event):
                    raise ValidationError("event_id collision: different record content")
                result = self._read(db, utc_now(), strict=True)
                result["operation"] = {"inserted": 0, "ignored": 0, "duplicates": 1, "source_updated": False}
                return result
            state = self._read(db, utc_now(), strict=True)
            tasks = {t["id"]: t for t in state["tasks"]}
            task = tasks.get(event["task_id"])
            if not task or not task["metadata_known"]:
                raise ValidationError("record requires an existing task with a known scope")
            if kind == "assignment" and task["node_kind"] == "umbrella":
                raise ValidationError("umbrella nodes are associations, not assignable work")
            data = event["data"]
            if timestamp(event["occurred_at"]) > utc_now():
                raise ValidationError("cannot record a future execution event")
            if timestamp(event["occurred_at"]) < timestamp(task["last_event_at"]):
                raise ValidationError("record is older than current task evidence; import as history instead")
            if kind == "assignment" and data["execution_status"] == "active":
                if any(rule["action"] in {"execute", "assign", "all"} and rule["status"] != "granted"
                       for rule in task["approval_constraints"]):
                    raise ValidationError("assignment blocked by required or denied approval")
                if task["reserved"] and data.get("reserved", True):
                    raise ValidationError("assignment requires explicit reserved:false to release legacy reservation")
                if task["delivery_status"] == "done":
                    raise ValidationError("completed task cannot be assigned without new task evidence")
                if task["execution_status"] == "blocked" and not data.get("reason"):
                    raise ValidationError("resuming blocked work requires a reason recorded in the assignment audit")
                blocking = {"source_error", "source_stale", "source_future", "event_future", "not_before",
                            "dependency_cycle", "dependency_unknown", "dependency_incomplete", "file_conflict"}
                if any(alert["code"] in blocking for alert in task["alerts"]):
                    raise ValidationError("assignment blocked by source, schedule, dependency or file conflict alert")
                assigned_files = data.get("files", task["files"])
                if not assigned_files or not task["scope"]:
                    raise ValidationError("assignment requires an explicit nonempty scope and files")
                if any(not any(path == allowed or path.startswith(allowed.rstrip("/") + "/")
                               or fnmatch.fnmatchcase(path, allowed) for allowed in task["files"])
                       for path in assigned_files):
                    raise ValidationError("assignment files exceed task scope")
                if task["execution_status"] == "active" and task["owner_thread"] != data["owner_thread"]:
                    raise ValidationError("active owner must be stopped before reassignment")
                for other in tasks.values():
                    if (other["id"] != task["id"] and other["execution_status"] == "active"
                            and other["owner_thread"] != data["owner_thread"]
                            and other["delivery_status"] != "done"
                            and any(files_overlap(a, b) for a in assigned_files for b in other["files"])):
                        raise ValidationError(f"assignment file conflict with {other['id']}")
            if kind == "result" and data.get("owner_thread") and data["owner_thread"] != task["owner_thread"]:
                raise ValidationError("result owner does not match current assignment")
            if kind == "result" and data.get("execution_status") == "active" and task["execution_status"] != "active":
                raise ValidationError("record-result cannot start execution; use checked record-assignment")
            for receipt in data.get("completed_actions", []):
                if (receipt["action"] != task["next_action_code"] or
                        receipt["input_pin"] != task["next_action_pin"]):
                    raise ValidationError("completed action does not match the current action/input pin")
                if timestamp(receipt["timestamp"]) > utc_now():
                    raise ValidationError("completed action cannot have a future timestamp")
            operation = self._import(db, snapshot)
            if operation["ignored"]:
                raise ValidationError("record is out of order; use import-snapshot for historical observations")
            result = self._read(db, utc_now(), strict=True)
            result["operation"] = operation
            return result

    def record_assignment(self, event_dict):
        return self._record(event_dict, "assignment")

    def record_result(self, event_dict):
        return self._record(event_dict, "result")

    def export_snapshot(self):
        with self._db() as db:
            records = [json.loads(row["payload"]) for row in db.execute("SELECT payload FROM snapshots ORDER BY ordinal")]
        payload = {"schema_version": SCHEMA_VERSION, "format": "geometry-work-manager-export", "snapshots": records}
        return {**payload, "checksum": digest(payload)}

    def restore(self, exported):
        _object(exported, "export", {"schema_version", "format", "snapshots", "checksum"},
                {"schema_version", "format", "snapshots", "checksum"})
        payload = {k: v for k, v in exported.items() if k != "checksum"}
        if exported["format"] != "geometry-work-manager-export" or exported["schema_version"] != SCHEMA_VERSION:
            raise ValidationError("unknown export format")
        if not isinstance(exported["snapshots"], list) or digest(payload) != exported["checksum"]:
            raise ValidationError("export checksum mismatch; current state unchanged")
        for snapshot in exported["snapshots"]:
            validate_snapshot(snapshot)
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            self._assert_healthy(db)
            existing = [json.loads(row["payload"]) for row in db.execute("SELECT payload FROM snapshots ORDER BY ordinal")]
            if existing and existing != exported["snapshots"]:
                raise ValidationError("restore requires an empty store; existing newer state cannot be replaced")
            if not existing:
                for snapshot in exported["snapshots"]:
                    self._import(db, snapshot)
            state = self._read(db, utc_now(), strict=True)
        return state


def atomic_write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    encoded = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        if hasattr(os, "O_DIRECTORY"):
            directory = os.open(path.parent, os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
