import binaries,json,hashlib,pathlib
b=binaries.BY_NAME['bridge']
info=binaries.inspect_one(b)
assert info.state=='fresh',info.as_dict()
fingerprint,files,command=binaries.compute_fingerprint(b)
record={'preparation':'reused existing fresh isolated binary without build','info':info.as_dict(),'fingerprint':fingerprint,'sourceHashes':files,'historicalBuildCommandFingerprint':command,'binarySha256':hashlib.sha256(info.path.read_bytes()).hexdigest(),'sidecarSha256':hashlib.sha256(b.sidecar.read_bytes()).hexdigest()}
pathlib.Path('<unit-evidence-root>/scenario-units-c0f05baa/native-identity.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
