#!/usr/bin/env python3
"""P73 revert: on top of the timing commit, restore the pre-6615db6 form
(sleep(180), no row wait). WSL-only commit; never pushed.

    python3 make_p73_revert.py  -> prints the revert commit SHA on the last line
"""
import os
import pathlib
import subprocess

src = pathlib.Path('/root/p73-verify/src')
env = dict(os.environ, PATH='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin')


def git(*a, cwd=src, check=True):
    return subprocess.run(['git', '-c', 'core.autocrlf=false', *a], cwd=cwd, env=env, check=check, capture_output=True, text=True).stdout.strip()


p = src / 'geometry-web' / 'uiux_review_test.js'
data = p.read_bytes().decode('utf-8')

new1 = "  await choose('#refGuideAxis','v');await choose('#refGuideSource','edge:e1:u');await choose('#refGuideRatio','1/2');const __p73t0=Date.now();await ctl('#refGuideCreate');await wait('!oc.busy');const __p73t1=Date.now();"
old1 = "  await choose('#refGuideAxis','v');await choose('#refGuideSource','edge:e1:u');await choose('#refGuideRatio','1/2');await ctl('#refGuideCreate');await wait('!oc.busy');await sleep(180);"
assert data.count(new1) == 1, data.count(new1)
data = data.replace(new1, old1)

added = "  await wait(`(()=>{const g=(fe.guides||[]).find(g=>g.expression==='1/2*edge:e1:u'&&g.axis==='v'&&g.off===2000);return !!g&&!!document.querySelector('[data-edit-guide=\"'+g.id+'\"]');})()`);\n  console.log('P73_WAIT_MS '+JSON.stringify({createToBusyClearMs:__p73t1-__p73t0,busyClearToRowMs:Date.now()-__p73t1}));\n"
assert data.count(added) == 1, data.count(added)
data = data.replace(added, '')
p.write_bytes(data.encode('utf-8'))

print(git('--no-pager', 'diff', '--stat'))
git('-c', 'user.name=p73-verify', '-c', 'user.email=p73-verify@invalid', 'commit', '-q', '-am',
    'WSL-ONLY (never push): revert P73 to the fixed sleep(180) form to re-check it is red')
print(git('rev-parse', 'HEAD'))
