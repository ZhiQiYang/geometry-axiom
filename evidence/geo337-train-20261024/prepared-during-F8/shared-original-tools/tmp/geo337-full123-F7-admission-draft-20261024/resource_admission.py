"""Read-only resource admission for full123; no product threshold or verdict.

Run after both existing heavy locks and before any original formal command.
The root owner supplies an explicitly pinned, per-filesystem additional budget.
Existing seed/source bytes are already allocated and must not be counted again.
"""
from pathlib import Path
import hashlib,json,os

def validate(path, expected_hash, source_sha, paths):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('regular pinned admission file required')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_hash:raise ValueError('filesystem admission pin changed')
    doc=json.loads(raw)
    if doc.get('schema')!='full123-filesystem-admission/1' or doc.get('source_sha')!=source_sha:
        raise ValueError('filesystem admission schema/source mismatch')
    actual={name:str(Path(value).resolve()) for name,value in paths.items()}
    if doc.get('paths')!=actual:raise ValueError('filesystem admission exact output paths differ')
    devices={}
    for name,text in actual.items():
        target=Path(text)
        if not target.is_dir():raise ValueError('actual output anchor is not a directory: '+name)
        devices[name]=target.stat().st_dev
    groups=doc.get('filesystems')
    if not isinstance(groups,list) or not groups:raise ValueError('explicit per-filesystem budget required')
    seen_labels=set();seen_devices=set();rows=[]
    required_components={'binaries_additional','raw_ledger_additional','compiler_peak_additional','metadata_additional','reserve_additional'}
    for group in groups:
        labels=group.get('labels');components=group.get('additional_bytes');minimum=group.get('minimum_free_bytes')
        if not isinstance(labels,list) or not labels or any(not isinstance(x,str)or x not in actual for x in labels):raise ValueError('known nonempty filesystem labels required')
        if len(set(labels))!=len(labels)or seen_labels.intersection(labels):raise ValueError('filesystem label duplicated')
        devs={devices[x]for x in labels}
        if len(devs)!=1:raise ValueError('group contains different actual filesystems')
        device=next(iter(devs))
        if device in seen_devices:raise ValueError('same filesystem budget must be aggregated once')
        if type(group.get('device'))is not int or group['device']!=device:raise ValueError('filesystem device drift')
        if not isinstance(components,dict)or set(components)!=required_components or any(type(v)is not int or v<0 for v in components.values()):raise ValueError('explicit nonnegative integer additional allocations required')
        if type(minimum)is not int or minimum<=0 or minimum!=sum(components.values()):raise ValueError('positive exact sum of additional resource components required')
        if not isinstance(group.get('basis'),str)or not group['basis'].strip():raise ValueError('budget evidence/estimate basis must be disclosed')
        anchor=Path(actual[labels[0]]);fs=os.statvfs(anchor);free=fs.f_bavail*fs.f_frsize
        row={'labels':labels,'device':device,'anchor':str(anchor),'free_bytes':free,'minimum_free_bytes':minimum,'additional_bytes':components,'basis':group['basis'],'admitted':free>=minimum}
        rows.append(row);seen_devices.add(device);seen_labels.update(labels)
    if seen_labels!=set(actual)or seen_devices!=set(devices.values()):raise ValueError('every actual writable filesystem must be budgeted exactly once')
    return {'schema':'full123-filesystem-admission-result/1','source_sha':source_sha,'input':str(path.resolve()),'input_sha256':expected_hash,'paths':actual,'filesystems':rows,'passed':all(r['admitted']for r in rows),'scope':'Resource admission only; not a product oracle, performance limit, or measured peak.'}
