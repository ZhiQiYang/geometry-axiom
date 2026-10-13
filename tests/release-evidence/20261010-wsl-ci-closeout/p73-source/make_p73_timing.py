#!/usr/bin/env python3
"""P73 verify: clone of 6615db6 + ONE WSL-only commit adding timing marks around
the new guide-row wait in uiux_review_test.js. Never pushed; origin removed.

    python3 make_p73_timing.py  -> prints the mutant commit SHA on the last line
"""
import os
import pathlib
import subprocess

BASE = '6615db613a75fbad43116d85251782b5083479df'
src = pathlib.Path('/root/p73-verify/src')
env = dict(os.environ, PATH='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin')


def git(*a, cwd=src, check=True):
    return subprocess.run(['git', '-c', 'core.autocrlf=false', *a], cwd=cwd, env=env, check=check, capture_output=True, text=True).stdout.strip()


if not (src / '.git').exists():
    src.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', 'clone', '-q', '--no-checkout', '/mnt/d/geometry-axiom', str(src)], env=env, check=True)
git('-c', 'advice.detachedHead=false', 'checkout', '-q', '--detach', BASE)
git('reset', '-q', '--hard', BASE)
git('clean', '-qfd')
git('remote', 'remove', 'origin', check=False)

p = src / 'geometry-web' / 'uiux_review_test.js'
data = p.read_bytes().decode('utf-8')

old1 = "  await choose('#refGuideAxis','v');await choose('#refGuideSource','edge:e1:u');await choose('#refGuideRatio','1/2');await ctl('#refGuideCreate');await wait('!oc.busy');"
new1 = "  await choose('#refGuideAxis','v');await choose('#refGuideSource','edge:e1:u');await choose('#refGuideRatio','1/2');const __p73t0=Date.now();await ctl('#refGuideCreate');await wait('!oc.busy');const __p73t1=Date.now();"
assert data.count(old1) == 1, data.count(old1)
data = data.replace(old1, new1)

old2 = "  await wait(`(()=>{const g=(fe.guides||[]).find(g=>g.expression==='1/2*edge:e1:u'&&g.axis==='v'&&g.off===2000);return !!g&&!!document.querySelector('[data-edit-guide=\"'+g.id+'\"]');})()`);"
new2 = old2 + "\n  console.log('P73_WAIT_MS '+JSON.stringify({createToBusyClearMs:__p73t1-__p73t0,busyClearToRowMs:Date.now()-__p73t1}));"
assert data.count(old2) == 1, data.count(old2)
data = data.replace(old2, new2)
p.write_bytes(data.encode('utf-8'))

print(git('--no-pager', 'diff', '--stat'))
git('-c', 'user.name=p73-verify', '-c', 'user.email=p73-verify@invalid', 'commit', '-q', '-am',
    'WSL-ONLY (never push): log ms from guide-create click and !oc.busy to the [data-edit-guide] row appearing')
print(git('rev-parse', 'HEAD'))
