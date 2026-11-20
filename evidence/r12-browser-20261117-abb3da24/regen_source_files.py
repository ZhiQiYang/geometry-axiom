"""Regenerate r12_browser_evidence source-files.json for a commit from git objects alone.
Usage (inside a clone): python3 regen_source_files.py <commit> > source-files.json
Same writer as tests/r12_browser_evidence.py::write_json (sorted paths, indent=2, ensure_ascii=False, trailing LF).
"""
import hashlib, json, subprocess, sys

commit = sys.argv[1]
rows = subprocess.run(["git", "ls-tree", "-r", "-z", commit], capture_output=True, check=True).stdout.split(b"\0")
blobs = {}
for row in rows:
    if row:
        head, name = row.split(b"\t", 1)
        blobs[name.decode()] = head.decode().split()[2]
cat = subprocess.Popen(["git", "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
receipt = {}
for name in sorted(blobs):
    cat.stdin.write((blobs[name] + "\n").encode()); cat.stdin.flush()
    size = int(cat.stdout.readline().split()[2]); data = cat.stdout.read(size); cat.stdout.read(1)
    receipt[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
sys.stdout.buffer.write((json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
