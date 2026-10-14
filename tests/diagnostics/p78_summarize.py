#!/usr/bin/env python3
"""Summarize raw P78 events without confusing a spent timer with a failed fetch."""
import json
from pathlib import Path
import sys


def summarize(directory):
    directory = Path(directory)
    browser = [json.loads(line) for line in (directory / 'browser.jsonl').read_text().splitlines()]
    server = [json.loads(line) for line in (directory / 'server.jsonl').read_text().splitlines()]
    result = json.loads((directory / 'result.json').read_text())
    identity = json.loads((directory / 'identity.json').read_text())
    trials = []
    for start in browser:
        if start['event'] != 'fetch.begin' or not start['cmd'].startswith('grid-trial-query '):
            continue
        rid = start['rid']
        brows = [x for x in browser if x.get('rid') == rid]
        host = [x for x in server if x.get('rid') == rid or (x.get('correlation') or {}).get('rid') == rid]
        def b(event):
            return next((x for x in brows if x['event'] == event), None)
        def s(event):
            return next((x for x in host if x['event'] == event), None)
        def elapsed(event):
            x = b(event)
            return round(x['browserMs']-start['browserMs'], 3) if x else None
        def host_elapsed(a, z):
            x, y = s(a), s(z)
            return round((y['mono_ns']-x['mono_ns'])/1e6, 3) if x and y else None
        candidate = start.get('candidate') or {}
        schedule = next((x for x in browser if x['event']=='candidate.scheduled' and
                         x['instance']==candidate.get('instance') and x['seq']==candidate.get('seq')), None)
        abort, rejection = b('fetch.signal.abort'), b('fetch.reject')
        trials.append(dict(rid=rid, candidate=candidate, command=start['cmd'],
                           candidateToFetchMs=round(start['browserMs']-schedule['browserMs'],3) if schedule else None,
                           browserHeadersMs=elapsed('fetch.headers'), browserRejectMs=elapsed('fetch.reject'),
                           signalFiredMs=elapsed('fetch.signal.abort'),
                           rejected=bool(rejection), rejectionName=rejection.get('name') if rejection else None,
                           signalReason=abort.get('reason') if abort else None,
                           serverPreBridgeMs=host_elapsed('server.request.begin','bridge.queue.enter'),
                           bridgeQueueMs=host_elapsed('bridge.queue.enter','bridge.lock.acquired'),
                           injectedHoldMs=host_elapsed('injection.hold.begin','injection.hold.end'),
                           bridgeIOMs=host_elapsed('bridge.stdin.flushed','bridge.stdout.received'),
                           serverTotalMs=host_elapsed('server.request.begin','server.request.end'),
                           clientDisconnected=bool(s('server.client.disconnected'))))
    return dict(run=directory.name, result=result, identity=identity, trials=trials,
                snapshots=[x for x in browser if x['event'].startswith('state.')],
                recovery=[x for x in browser if x['event'].startswith('recovery.')],
                waitFailures=[x for x in browser if x['event']=='wait.fail'],
                harnessErrors=[x for x in browser if x['event']=='harness.error'],
                timerCaveat='A signal can expire after successful fetch completion. Only fetch.reject proves that this wrapper observed a rejection.',
                clockCaveat='Browser durations use performance.now; server durations use monotonic_ns. No cross-clock latency is claimed.')


if __name__ == '__main__':
    print(json.dumps([summarize(arg) for arg in sys.argv[1:]], ensure_ascii=False, indent=2))
