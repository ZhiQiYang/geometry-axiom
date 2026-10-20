#!/bin/bash
# Re-run every static verification for the three patch variants.
# Read-only against the repo: a temporary index and an alternate object directory keep
# the repo's .git untouched; everything else is written under this directory.
#
#   REPO=D:/geometry-axiom BASE_REV=09ab5f79 ./verify_all.sh
cd "$(dirname "$0")" || exit 1
W="$(pwd)"
REPO="${REPO:-D:/geometry-axiom}"
REV="${BASE_REV:-09ab5f79}"
./fetch_base.sh || exit 1
python build.py | cut -c1-70
python checks.py | tail -12
python reader_impact.py
rm -rf gitwork && mkdir -p gitwork/objs
export GIT_DIR="$REPO/.git" GIT_OBJECT_DIRECTORY="$W/gitwork/objs" GIT_ALTERNATE_OBJECT_DIRECTORIES="$REPO/.git/objects"
for n in 299 316 all; do
  export GIT_INDEX_FILE="$W/gitwork/idx$n"
  git read-tree "$REV"
  if git apply --check --cached "patch$n.diff"; then echo "git apply --check --cached $n: OK"; else echo "git apply --check --cached $n: FAIL"; fi
  git apply --cached "patch$n.diff"
done
python - <<'PY'
import os, pathlib, subprocess
W = pathlib.Path('.').resolve()
env = dict(os.environ)
for n in ['299', '316', 'all']:
    env['GIT_INDEX_FILE'] = str(W / ('gitwork/idx' + n))
    out = pathlib.Path('out' + n)
    bad = cnt = 0
    for f in out.rglob('*'):
        if f.is_file():
            rel = f.relative_to(out).as_posix()
            blob = subprocess.run(['git', 'cat-file', 'blob', ':' + rel], env=env, capture_output=True).stdout
            cnt += 1
            bad += blob != f.read_bytes()
    print('blob-exact', n, 'files', cnt, 'mismatch', bad)
PY
export GIT_INDEX_FILE="$W/gitwork/idxseq"
git read-tree "$REV"
git apply --cached patch299.diff
echo "sequential 299 -> 316, files that do not apply: $(git apply --check --cached patch316.diff 2>&1 | grep -c 'does not apply')"
unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES
