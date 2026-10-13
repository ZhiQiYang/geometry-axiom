#!/usr/bin/env python3
"""Produce a SHA-bound correction overlay; never rewrite or execute raw payloads.

The only Node call runs the current text transformer on stdin. Product JavaScript
is data: no browser, server, bridge, archived tool, or product script is executed.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'tests/evidence/ui209-recovery-20261013'
ARCHIVE_SHA = '89a7ea908a7fb3d0957d1103d45f00b11c5de55d2a305b589b5a5bfcf7d6f5ba'
MANIFEST_SHA = '317572989637967e5b0ba7974b1dc5d396976ace00886dcef4f919846158ccb8'
SUMMARY_SHA = '4750214a24efd8daf4fd58dc10bdb599370e2f694ee10d38206153150f586d29'
SOURCE_SHA = 'ce0c48d2d2c3d0102f05a45c58ac1568da991c28cc55e2461c1a4644f2e7cf01'
SERVED_SHA = '19b834a3f5b4c40e1f7a69a63b9ffca31d3fdb07c77ab54b0a5213a6c0be29f4'
SOURCE_FILE = 'geometry-web/grid-system-workspace.js'
RETURN = re.compile(r'return window\.__uiReturn\(__uid,(\d+),(undefined|true|false),__us\(\)\);')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=EVIDENCE / 'raw.tar.xz')
    parser.add_argument('--manifest', type=Path, default=EVIDENCE / 'manifest.json')
    parser.add_argument('--summary', type=Path, default=EVIDENCE / 'summary.json')
    parser.add_argument('--instrument', type=Path, default=Path(__file__).with_name('ui209_instrument.cjs'))
    args = parser.parse_args()
    archive, manifest_bytes, summary_bytes = (p.read_bytes() for p in (args.archive, args.manifest, args.summary))
    require(sha(archive) == ARCHIVE_SHA, 'Original archive SHA mismatch')
    require(sha(manifest_bytes) == MANIFEST_SHA, 'Original manifest SHA mismatch')
    require(sha(summary_bytes) == SUMMARY_SHA, 'Original summary SHA mismatch')
    manifest, summary = json.loads(manifest_bytes), json.loads(summary_bytes)
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:xz') as bundle:
        members = bundle.getmembers()
        require(len(members) == len(manifest) == 328, 'Archive member count mismatch')
        require({m.name for m in members} == set(manifest), 'Archive member set mismatch')
        payload = {}
        for member in members:
            require(member.isfile() and member.name not in payload, 'Duplicate or non-file member')
            data = bundle.extractfile(member).read()
            require({'bytes': len(data), 'sha256': sha(data)} == manifest[member.name], member.name + ': hash/length mismatch')
            payload[member.name] = data

    source_members = ['source-snapshots/' + group + '/' + SOURCE_FILE for group in ('p70-vs-195', 'p88-vs-b406')]
    source_bytes = payload[source_members[0]]
    require(all(payload[name] == source_bytes for name in source_members), 'Historical sources differ')
    require(sha(source_bytes) == SOURCE_SHA, 'Source SHA mismatch')
    source = source_bytes.decode('utf-8')
    start = source.index('  async function open(options={}, committed=false) {')
    end = source.index('  function selectedOpen(options)', start)
    originals = list(re.finditer(r'\breturn(?: (true|false))?;', source[start:end]))
    transformed = subprocess.run(['node', '-e',
        "const fs=require('node:fs');process.stdout.write(require(process.argv[1])(fs.readFileSync(0,'utf8')).source)",
        str(args.instrument.resolve())], input=source_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
    fixed = transformed.decode('utf-8')
    new_sites = list(RETURN.finditer(fixed))
    names = sorted(n.removeprefix('runs/').removesuffix('/instrumentation.json') for n in payload if n.startswith('runs/') and n.endswith('/instrumentation.json'))
    old_bytes = payload['runs/' + names[0] + '/served-grid-system-workspace.js']
    require(sha(old_bytes) == SERVED_SHA, 'Served SHA mismatch')
    old = old_bytes.decode('utf-8')
    old_sites = list(RETURN.finditer(old))
    require(len(originals) == len(old_sites) == len(new_sites) == 33, 'Return shape mismatch')
    normalize = lambda text: RETURN.sub(lambda m: m[0].replace(',' + m[1] + ',', ',SOURCE_LINE,', 1), text)
    require(normalize(old) == normalize(fixed), 'Change exceeds return line labels')
    awaits = re.findall(r'await __ua\("([^"\n]+)",', old)
    require(len(awaits) == 13 and awaits == re.findall(r'await __ua\("([^"\n]+)",', fixed), 'Await labels changed')
    sites = []
    for ordinal, (original, recorded, corrected) in enumerate(zip(originals, old_sites, new_sites), 1):
        offset = start + original.start()
        line = source.count('\n', 0, offset) + 1
        value = original[1] or 'undefined'
        require(int(corrected[1]) == line and recorded[2] == corrected[2] == value, 'Incorrect fixed label/value')
        sites.append({'ordinal': ordinal, 'recordedLine': int(recorded[1]), 'correctedLine': line,
                      'sourceColumnCodePoints': offset - source.rfind('\n', 0, offset), 'value': value,
                      'sourceLineText': source.splitlines()[line - 1]})
    require(sum(s['recordedLine'] != s['correctedLine'] for s in sites) == 27, 'Historical mismatch count changed')

    def resolve(line, value):
        literal = 'undefined' if value is None else 'true' if value is True else 'false' if value is False else 'invalid'
        matches = [s for s in sites if s['recordedLine'] == line and s['value'] == literal]
        require(len(matches) == 1, 'Ambiguous or unknown recorded site; do not infer an exit')
        return matches[0]

    runs = {}
    patches = []
    for name in names:
        prefix = 'runs/' + name + '/'
        read = lambda suffix: json.loads(payload[prefix + suffix])
        identity, instrumentation = read('identity.json'), read('instrumentation.json')
        require(instrumentation['originalSha256'] == SOURCE_SHA and instrumentation['servedSha256'] == SERVED_SHA, name + ': instrumentation mismatch')
        require(payload[prefix + 'served-grid-system-workspace.js'] == old_bytes, name + ': served mismatch')
        before = read('sources-before.json')
        require(before == read('sources-after.json') and before[SOURCE_FILE] == SOURCE_SHA, name + ': source mismatch')
        tool_key = 'diagnostic-tools/ui209_instrument.cjs'
        tool_member = read('executed-tool-index.json')[tool_key]
        require(sha(payload[tool_member]) == before[tool_key], name + ': original tool mismatch')
        events = []
        for number, text in enumerate(payload[prefix + 'browser.jsonl'].decode('utf-8').splitlines(), 1):
            row = json.loads(text)
            if row.get('event') != 'open.return':
                continue
            site = resolve(row['line'], row.get('value'))
            events.append({'browserJsonlLine': number, 'openId': row['id'], 'browserMs': row['browserMs'],
                           'recordedLine': row['line'], 'correctedLine': site['correctedLine'], 'siteOrdinal': site['ordinal']})
        target = summary['runs'][name].get('target')
        if target:
            for index, row in enumerate(target['returns']):
                site = resolve(row['line'], row['value'])
                witnesses = [r for r in events if r['openId'] == target['call']['id'] and r['siteOrdinal'] == site['ordinal']]
                require(len(witnesses) == 1, name + ': summary/raw mismatch')
                patches.append({'pointer': '/runs/' + name + '/target/returns/' + str(index) + '/line',
                                'recorded': row['line'], 'corrected': site['correctedLine'],
                                'browserJsonlMember': prefix + 'browser.jsonl', 'browserJsonlLine': witnesses[0]['browserJsonlLine']})
        runs[name] = {'sourceRef': identity['sourceRef'], 'sourceSha256': SOURCE_SHA, 'servedSha256': SERVED_SHA,
                      'originalInstrumentSha256': before[tool_key], 'browserJsonlSha256': sha(payload[prefix + 'browser.jsonl']),
                      'events': events}
    require(len(names) == 8 and len(patches) == 6 and sum(len(r['events']) for r in runs.values()) == 42, 'Unexpected event/summary coverage')
    result = {'kind': 'static-source-location-correction-only', 'productExecution': False, 'archivedPayloadExecution': False,
              'originalDeliveryCommit': '52c34a6d6faef1d3cdaf52d52b6f8edb66eda012',
              'archiveSha256': ARCHIVE_SHA, 'manifestSha256': MANIFEST_SHA, 'verifiedMembers': 328, 'originalSummarySha256': SUMMARY_SHA,
              'sourceFile': SOURCE_FILE, 'sourceMembers': source_members, 'sourceSha256': SOURCE_SHA, 'servedSha256': SERVED_SHA,
              'fixedInstrumentSha256': sha(args.instrument.read_bytes()), 'fixedServedSha256': sha(transformed),
              'onlyReturnLabelsChanged': True, 'unchangedAwaitLabels': awaits, 'returnSites': sites, 'runs': runs, 'summaryPatches': patches,
              'limits': 'Historical raw/summary remain unchanged. Ambiguous old labels fail closed; unobserved exits are only a static map. No new UI recovery, timing, or WSL evidence.'}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
