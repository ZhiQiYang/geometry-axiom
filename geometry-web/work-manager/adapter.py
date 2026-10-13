"""Convert an authorized read-only observation into a validated private snapshot.

No network calls, task execution, permission changes or database writes. A user
must still import the output through the normal transactional CLI.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from store import (MAX_INPUT_BYTES, Store, ValidationError, _enum, _integer,
                   _object, _sha, _string, _validate_ci, atomic_write_json,
                   canonical, digest, timestamp, validate_snapshot)


def _reference(repository, kind, number):
    return f"https://github.com/{repository}/{'issues' if kind == 'issue' else 'pull'}/{number}"


def validate_observation(value):
    _object(value, "observation", {"format", "repository", "observed_at", "mode", "main", "counts",
            "pull_requests", "issues", "exact_head_ci", "caveats", "changes_after_baseline"},
            {"format", "repository", "observed_at", "mode", "main", "counts", "pull_requests", "issues", "exact_head_ci"})
    if value["format"] != "geometry-github-read-observation/1" or value["mode"] != "read_only_connector_snapshot":
        raise ValidationError("unsupported read observation format or mode")
    repository = value["repository"]
    if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValidationError("repository must be owner/name")
    observed = timestamp(value["observed_at"])
    _object(value["main"], "main", {"sha", "url"}, {"sha", "url"})
    _sha(value["main"]["sha"], "main SHA")
    if not value["main"]["sha"] or value["main"]["url"] != f"https://github.com/{repository}/commit/{value['main']['sha']}":
        raise ValidationError("main reference does not match repository and complete SHA")
    _object(value["counts"], "counts", {"open_issues", "open_prs"}, {"open_issues", "open_prs"})
    numbers = {}
    for kind, key, count_key in (("issue", "issues", "open_issues"), ("pr", "pull_requests", "open_prs")):
        rows = value[key]
        if not isinstance(rows, list):
            raise ValidationError(f"{key} must be an array")
        _integer(value["counts"][count_key], count_key, 0)
        if value["counts"][count_key] != len(rows):
            raise ValidationError(f"{count_key} does not match the supplied rows")
        numbers[kind] = {}
        allowed = {"task_id", "number", "title", "state", "updated_at", "url"}
        if kind == "pr":
            allowed |= {"draft", "head_sha", "base_ref", "base_sha", "author"}
        for row in rows:
            _object(row, kind, allowed, allowed)
            _integer(row["number"], f"{kind} number")
            if row["number"] in numbers[kind]:
                raise ValidationError(f"duplicate {kind} number")
            numbers[kind][row["number"]] = row
            if row["task_id"] != f"gh:{kind}:{row['number']}":
                raise ValidationError("observation task_id does not match its reference")
            if row["url"] != _reference(repository, kind, row["number"]):
                raise ValidationError("observation URL does not match repository/kind/number")
            _string(row["title"], f"{kind} title")
            _enum(row["state"], {"open"}, f"{kind} state")
            if timestamp(row["updated_at"]) > observed:
                raise ValidationError("item updated_at is later than the observation")
            if kind == "pr":
                _sha(row["head_sha"], "PR head SHA")
                _sha(row["base_sha"], "PR base SHA")
                if not row["head_sha"] or not row["base_sha"] or type(row["draft"]) is not bool:
                    raise ValidationError("PR requires complete SHA values and boolean draft")
                _string(row["base_ref"], "PR base ref")
                _string(row["author"], "PR author")
    if set(numbers["issue"]) & set(numbers["pr"]):
        raise ValidationError("GitHub issue and PR numbers share one namespace; overlapping kinds need correction")
    if not isinstance(value["exact_head_ci"], list):
        raise ValidationError("exact_head_ci must be an array")
    seen_ci = set()
    for group in value["exact_head_ci"]:
        _object(group, "exact head CI", {"pr_number", "head_sha", "runs"}, {"pr_number", "head_sha", "runs"})
        number = group["pr_number"]
        if number is not None:
            _integer(number, "CI PR number")
        if number in seen_ci or (number is not None and number not in numbers["pr"]):
            raise ValidationError("CI references an absent or repeated PR")
        seen_ci.add(number)
        expected_sha = value["main"]["sha"] if number is None else numbers["pr"][number]["head_sha"]
        if group["head_sha"] != expected_sha or not isinstance(group["runs"], list):
            raise ValidationError("CI group must bind its observed exact head")
        seen_runs = set()
        for run in group["runs"]:
            _object(run, "CI run", {"id", "head_sha", "status", "conclusion", "attempt", "updated_at", "url", "jobs"},
                    {"id", "head_sha", "status", "conclusion", "attempt", "updated_at", "url", "jobs"})
            _integer(run["id"], "run id")
            _integer(run["attempt"], "run attempt")
            if run["id"] in seen_runs or run["head_sha"] != expected_sha:
                raise ValidationError("CI run identity or SHA does not match")
            seen_runs.add(run["id"])
            if run["url"] != f"https://github.com/{repository}/actions/runs/{run['id']}":
                raise ValidationError("CI run URL does not match repository/id")
            if timestamp(run["updated_at"]) > observed or not isinstance(run["jobs"], list):
                raise ValidationError("invalid CI run timestamp or jobs")
            _validate_ci({"name": "run metadata", "sha": expected_sha, "status": run["status"], "conclusion": run["conclusion"]})
            seen_jobs = set()
            for job in run["jobs"]:
                _object(job, "observed CI job", {"id", "name", "status", "conclusion", "runner_id", "steps"},
                        {"id", "name", "status", "conclusion", "runner_id", "steps"})
                _integer(job["id"], "job id")
                if job["id"] in seen_jobs:
                    raise ValidationError("duplicate CI job id")
                seen_jobs.add(job["id"])
                _validate_ci({**{k: job[k] for k in ("name", "status", "conclusion", "runner_id", "steps")}, "sha": expected_sha})
    if "caveats" in value and (not isinstance(value["caveats"], list) or not all(isinstance(x, str) for x in value["caveats"])):
        raise ValidationError("caveats must be an array of strings")
    if "changes_after_baseline" in value:
        _string(value["changes_after_baseline"], "changes_after_baseline")
    if len(canonical(value).encode()) > MAX_INPUT_BYTES:
        raise ValidationError("observation exceeds 8 MiB")


def _ci_jobs(group):
    """Keep each observed run/job identity, including failures with shared names."""
    jobs = []
    for run in group["runs"]:
        for job in run["jobs"]:
            normalized = {key: copy.deepcopy(job[key]) for key in ("id", "name", "status", "conclusion", "runner_id", "steps")}
            normalized.update(sha=group["head_sha"], url=run["url"], run_id=run["id"], attempt=run["attempt"])
            jobs.append(normalized)
    return sorted(jobs, key=lambda job: (job["run_id"], job["attempt"], job["id"]))


def _ci_runs(group):
    return [{"id": run["id"], "sha": run["head_sha"], "status": run["status"],
             "conclusion": run["conclusion"], "attempt": run["attempt"], "url": run["url"],
             "job_count": len(run["jobs"])}
            for run in sorted(group["runs"], key=lambda run: (run["id"], run["attempt"]))]


def adapt_observation(store, observation, source_id="github-read-observation"):
    validate_observation(observation)
    _string(source_id, "source id", maximum=200)
    state = store.reconcile()
    if state.get("store_health", {}).get("status") == "invalid":
        raise ValidationError("invalid ledger: inspect diagnostics before adapting new observations")
    tasks = {task["id"]: task for task in state["tasks"]}
    snapshots = [snapshot for snapshot in store.export_snapshot()["snapshots"] if snapshot["source"]["id"] == source_id]
    previous = max(snapshots, key=lambda snapshot: snapshot["source"]["version"], default=None)
    if previous and timestamp(observation["observed_at"]) < timestamp(previous["source"]["as_of"]):
        raise ValidationError("observation is older than the last source version")
    streams = {}
    for snapshot in snapshots:
        for event in snapshot["events"]:
            key = (event["task_id"], event["kind"])
            if key not in streams or event["version"] > streams[key]["version"]:
                streams[key] = event
    events, mappings, pending = [], [], {}
    repository, when = observation["repository"], observation["observed_at"]

    def emit(task_id, kind, data):
        key = (task_id, kind)
        if key in pending:
            if kind != "task":
                raise ValidationError("multiple observed PRs map to one work item; record separate delivery tasks")
            combined = pending[key]
            if "refs" in data:
                known = {ref["url"] for ref in combined.get("refs", [])}
                combined.setdefault("refs", []).extend(ref for ref in data["refs"] if ref["url"] not in known)
            if "title" in data and combined.get("title") != data["title"]:
                # Multiple issue links do not rename an existing bounded task
                # according to whichever issue happened to be listed last.
                combined["title"] = tasks.get(task_id, {}).get("title", combined.get("title", data["title"]))
        else:
            pending[key] = copy.deepcopy(data)

    def finish_event(task_id, kind, data):
        if kind == "task" and "refs" in data:
            data["refs"] = sorted(data["refs"], key=canonical)
        prior = streams.get((task_id, kind))
        if prior and canonical(prior["data"]) == canonical(data):
            events.append(copy.deepcopy(prior))
            return
        version = prior["version"] + 1 if prior else 1
        event_id = "observation:" + digest([source_id, task_id, kind, version, data])
        events.append({"event_id": event_id, "task_id": task_id, "kind": kind, "version": version,
                       "occurred_at": when, "data": data})

    def resolve(row, kind):
        exact = row["task_id"]
        matches = [task["id"] for task in tasks.values() if any(ref.get("url") == row["url"] for ref in task["refs"])
                   or (kind == "pr" and (task.get("pr") or {}).get("url") == row["url"])]
        if exact in tasks:
            existing = tasks[exact]
            references = existing.get("refs", []) + ([{**existing["pr"], "kind": "pr"}] if existing.get("pr") else [])
            conflicting_repository = any(
                urlsplit(ref.get("url", "")).hostname == "github.com"
                and "/".join(urlsplit(ref["url"]).path.strip("/").split("/")[:2]).lower() != repository.lower()
                for ref in references)
            conflicting_identity = any(ref.get("kind") == kind and ref.get("url") != row["url"] for ref in references)
            if exact not in matches and (matches or conflicting_repository or conflicting_identity):
                raise ValidationError("canonical task ID conflicts with existing repository/reference; explicit mapping is required")
            chosen = exact
        elif len(matches) == 1:
            chosen = matches[0]
        elif not matches:
            chosen = exact
        else:
            raise ValidationError("ambiguous existing task references; record an explicit umbrella mapping first")
        if chosen != exact:
            mappings.append({"observed_task_id": exact, "existing_task_id": chosen, "url": row["url"]})
        return chosen

    issue_rows = []
    for row in observation["issues"]:
        task_id = resolve(row, "issue")
        task = tasks.get(task_id, {})
        refs = copy.deepcopy(task.get("refs", []))
        if not any(ref.get("url") == row["url"] for ref in refs):
            refs.append({"kind": "issue", "number": row["number"], "url": row["url"]})
        data = {"refs": refs}
        if not task or not task.get("scope") or task.get("node_kind") == "umbrella":
            data["title"] = row["title"]
        emit(task_id, "task", data)
        linked = sorted({task_id, *[t["id"] for t in tasks.values() if t.get("parent_id") == task_id]})
        issue_rows.append({"number": row["number"], "url": row["url"], "title": row["title"], "task_ids": linked})
    ci_groups = {group["pr_number"]: group for group in observation["exact_head_ci"]}
    pr_rows = []
    for row in observation["pull_requests"]:
        task_id = resolve(row, "pr")
        task = tasks.get(task_id, {})
        if not task:
            emit(task_id, "task", {"title": row["title"], "refs": [{"kind": "pr", "number": row["number"], "url": row["url"]}]})
        elif (task_id, "task") in streams and (task_id, "task") not in pending:
            # Retain this source's original task event after its first import.
            # Copying the current projection would absorb independent scope or
            # approval changes; omitting it makes an identical poll a new source.
            emit(task_id, "task", streams[(task_id, "task")]["data"])
        raw_pr = {"number": row["number"], "url": row["url"], "head_sha": row["head_sha"],
                  "draft": row["draft"], "merged": False, "updated_at": row["updated_at"]}
        if row["number"] in ci_groups:
            raw_pr["ci"] = _ci_jobs(ci_groups[row["number"]])
            raw_pr["ci_runs"] = _ci_runs(ci_groups[row["number"]])
        emit(task_id, "github", {"pr_metadata": raw_pr, "summary": "唯讀 metadata／CI 觀測；不寫 review、批准、owner 或執行終態，未推論費用原因。"})
        pr_rows.append({"number": row["number"], "url": row["url"], "title": row["title"], "head_sha": row["head_sha"],
                        "base": row["base_ref"], "base_sha": row["base_sha"], "draft": row["draft"], "merged": False, "task_ids": [task_id]})
    source = {"id": source_id, "kind": "manual_snapshot", "version": previous["source"]["version"] + 1 if previous else 1,
              "as_of": when, "status": "ok", "source_sha": observation["main"]["sha"], "url": observation["main"]["url"]}
    if None in ci_groups:
        source["ci"] = _ci_jobs(ci_groups[None])
        source["ci_runs"] = _ci_runs(ci_groups[None])
    for (task_id, kind), data in sorted(pending.items()):
        finish_event(task_id, kind, data)
    snapshot = {"schema_version": 1, "source": source, "events": events,
                "issue_inventory": {"repository": repository, "complete": False, "issues": issue_rows},
                "pr_inventory": {"repository": repository, "complete": False, "prs": pr_rows}}
    # Counts certify only the supplied observed rows. Missing items are retained;
    # this adapter never silently prunes a previously registered inventory.
    if previous:
        comparison = copy.deepcopy(snapshot)
        comparison["source"]["version"] = previous["source"]["version"]
        if canonical(comparison) == canonical(previous):
            snapshot = comparison
    validate_snapshot(snapshot)
    return snapshot, {"mapped_existing_tasks": mappings, "source_version": snapshot["source"]["version"],
                      "events": len(events), "issues": len(issue_rows), "prs": len(pr_rows),
                      "database_modified": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description="將已授權的 GitHub 唯讀 observation 轉成待匯入私有快照")
    parser.add_argument("file", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent / ".local")
    parser.add_argument("--source-id", default="github-read-observation")
    args = parser.parse_args(argv)
    try:
        with args.file.open("rb") as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValidationError("observation exceeds 8 MiB")
        observation = json.loads(raw)
        validate_observation(observation)
        database = args.data_dir if args.data_dir.suffix in {".db", ".sqlite", ".sqlite3"} else args.data_dir / "state.sqlite3"
        if not database.is_file():
            raise ValidationError("ledger does not exist; initialize the private store with import-snapshot before adaptation")
        snapshot, report = adapt_observation(Store(args.data_dir), observation, args.source_id)
        atomic_write_json(args.out, snapshot)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({"error": type(error).__name__, "message": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
