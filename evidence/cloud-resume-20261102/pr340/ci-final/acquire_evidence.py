"""Read-only GitHub evidence acquisition; preserves proxy authentication path."""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.github.com/repos/ZhiQiYang/geometry-axiom"
OUT = Path(__file__).resolve().parent
RUNS = {"integration": 41382015317, "mutation": 41382015277}
HEAD = "b3a248607d7eb68d3167abbb926cf491d9b35a26"


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        redirected = super().redirect_request(request, response, code, message, headers, new_url)
        if urllib.parse.urlparse(request.full_url).hostname != urllib.parse.urlparse(new_url).hostname:
            redirected.remove_header("Authorization")
        return redirected


def fetch(url, destination):
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "geometry-pr340-evidence-readonly"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.build_opener(SafeRedirect()).open(request, timeout=120) as response:
        data = response.read()
        status = response.status
        content_type = response.headers.get("Content-Type")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return {"url": url, "file": str(destination), "http_status": status, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "content_type": content_type}


def snapshot():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder = OUT / "api" / stamp
    tasks = [(BASE + "/pulls/340", folder / "pr340.json")]
    for name, run_id in RUNS.items():
        tasks.extend((BASE + f"/actions/runs/{run_id}" + suffix, folder / f"{name}-{label}.json")
                     for suffix, label in [("", "run"), ("/jobs?per_page=100", "jobs"), ("/artifacts?per_page=100", "artifacts")])
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        results = list(executor.map(lambda task: fetch(*task), tasks))
    (folder / "acquisition.json").write_text(json.dumps({"command": "python acquire_evidence.py snapshot", "exit_code": 0, "utc": stamp, "requests": results}, indent=2) + "\n")
    print(folder)
    for name in RUNS:
        run = json.loads((folder / f"{name}-run.json").read_text())
        assert run["head_sha"] == HEAD, (name, run["head_sha"])
        jobs = json.loads((folder / f"{name}-jobs.json").read_text())["jobs"]
        artifacts = json.loads((folder / f"{name}-artifacts.json").read_text())["artifacts"]
        print(name, run["id"], run["status"], run["conclusion"], run["head_sha"], "attempt", run["run_attempt"])
        for job in jobs:
            print(" JOB", job["id"], job["name"], job["status"], job["conclusion"])
        for artifact in artifacts:
            print(" ARTIFACT", artifact["id"], artifact["name"], artifact.get("digest"), artifact["size_in_bytes"])


def download(url, destination):
    result = fetch(url, Path(destination))
    (Path(destination).with_suffix(Path(destination).suffix + ".acquisition.json")).write_text(json.dumps({"command": "python acquire_evidence.py download <url> <destination>", "exit_code": 0, **result}, indent=2) + "\n")
    print(json.dumps(result, indent=2))


def collect(snapshot_folder):
    folder = Path(snapshot_folder)
    tasks = []
    artifacts_by_file = {}
    for name in RUNS:
        jobs = json.loads((folder / f"{name}-jobs.json").read_text())["jobs"]
        artifacts = json.loads((folder / f"{name}-artifacts.json").read_text())["artifacts"]
        for job in jobs:
            destination = OUT / "job-logs" / f"{job['id']}.txt"
            if job["status"] == "completed" and not destination.exists():
                tasks.append((BASE + f"/actions/jobs/{job['id']}/logs", destination))
        for artifact in artifacts:
            destination = OUT / "official-zips" / f"{artifact['id']}-{artifact['name']}.zip"
            artifacts_by_file[str(destination)] = artifact
            if not destination.exists():
                tasks.append((artifact["archive_download_url"], destination))
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        pending = {executor.submit(fetch, *task): task for task in tasks}
        for future in concurrent.futures.as_completed(pending):
            url, destination = pending[future]
            try:
                result = future.result()
                if str(destination) in artifacts_by_file:
                    artifact = artifacts_by_file[str(destination)]
                    result["github_artifact_digest"] = artifact.get("digest")
                    result["digest_matches"] = artifact.get("digest") == "sha256:" + result["sha256"]
                    result["artifact_id"] = artifact["id"]
                    assert result["digest_matches"], artifact["name"]
                results.append(result)
                print(destination.name, result["bytes"], result.get("digest_matches", "log"))
            except Exception as error:
                results.append({"url": url, "file": str(destination), "error_type": type(error).__name__, "error": str(error)})
                print(destination.name, "ERROR", type(error).__name__, str(error))
    receipt = {"command": "python acquire_evidence.py collect " + str(folder), "exit_code": int(any("error" in result for result in results)), "requests": results}
    (folder / "collection.json").write_text(json.dumps(receipt, indent=2) + "\n")
    raise SystemExit(receipt["exit_code"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["snapshot", "download", "collect"])
    parser.add_argument("url", nargs="?")
    parser.add_argument("destination", nargs="?")
    args = parser.parse_args()
    if args.mode == "snapshot":
        snapshot()
    elif args.mode == "download":
        download(args.url, args.destination)
    else:
        collect(args.url)
