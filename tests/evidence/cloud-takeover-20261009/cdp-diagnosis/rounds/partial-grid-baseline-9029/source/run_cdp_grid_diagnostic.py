"""Purposeful existing GRID_SYSTEM_ONLY partial CDP layout diagnosis on a caller-frozen clean candidate.

No service restart, production edits or golden updates. Explicit existing partial filter only. Call only
when root assigns the exclusive browser slot. Canonical counts remain those of
the actual tested SHA and committed golden, not a hardcoded historical count.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import socket
import subprocess
import sys
import tempfile

BASE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p,name):
    spec=importlib.util.spec_from_file_location(name,p)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('<takeover-repository-root>'))
    parser.add_argument('--url',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--expected-head',required=True)
    parser.add_argument('--bridge',type=Path,default=Path('<configured-native-directory>/bridge'))
    parser.add_argument('--model-base',type=Path,default=Path('<configured-native-directory>/model-base'))
    parser.add_argument('--feedback-dir',default='<isolated-test-directory>')
    parser.add_argument('--timeout',type=float,default=2400)
    args=parser.parse_args()
    root=args.root.resolve();output=args.output.resolve();bridge=args.bridge.resolve()
    assert not output.is_relative_to(root)
    assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==args.expected_head
    assert subprocess.check_output(['git','-C',str(root),'status','--short'],text=True)==''
    resource.setrlimit(resource.RLIMIT_STACK,(16777216,resource.getrlimit(resource.RLIMIT_STACK)[1]))
    # Existing standalone module screenshots use this shared TEMP destination.
    # It is separate from this round's configured native directory and Git.
    Path('<isolated-test-directory>').mkdir(exist_ok=True)
    gate=load(root/'tests/release_gate.py','takeover_full_cdp_gate')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));cdp_port=sock.getsockname()[1]
    profile=tempfile.mkdtemp(prefix='geometry-takeover-grid-diagnosis-profile-')
    environment=dict(os.environ)
    removed={}
    for key in list(environment):
        if key.startswith('GEOMETRY_') and (key.endswith('_ONLY') or key in {
            'GEOMETRY_CDP_FROM_P31','GEOMETRY_ASSEMBLY_INJECT_SWAP','GEOMETRY_CDP_UPDATE_GOLDEN',
            'GEOMETRY_CHROME_FLAGS','GEOMETRY_TEST_SERVER_PATH_STYLE'}):
            removed[key]=environment.pop(key)
    adapter=BASE/'full-launch-adapters'
    environment.update(GEOMETRY_GRID_SYSTEM_ONLY="1",GEOMETRY_TEST_URL=args.url,GEOMETRY_TEST_BRIDGE=str(bridge),
        GEOMETRY_BRIDGE=str(bridge),GEOMETRY_BRIDGE_EXECUTABLE=str(bridge),
        GEOMETRY_MODEL_BASE=str(args.model_base.resolve()),GEOMETRY_FEEDBACK_DIR=args.feedback_dir,
        GEOMETRY_CHROME='/usr/bin/chromium',GEOMETRY_CHROME_PROFILE=profile,
        GEOMETRY_CDP_PORT=str(cdp_port),GEOMETRY_REQUIRE_CLEAN='1',GEOMETRY_VERIFY_ROOT=str(root),
        GEOMETRY_PYTHON=sys.executable,PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(adapter)+(os.pathsep+environment['PYTHONPATH'] if environment.get('PYTHONPATH') else ''),
        NODE_OPTIONS='--require='+str(adapter/'sandbox-launch.cjs')+' --require='+str(BASE/'grid-rule-layout-read.cjs')+
                     (' '+environment['NODE_OPTIONS'] if environment.get('NODE_OPTIONS') else ''),
        GEOMETRY_TEST_SCREENSHOT=str(output/'screens/phase1-shell.png'),
        GEOMETRY_GRID_SCREENSHOT_DIR=str(output/'screens/grid'),GEOMETRY_GRID_RULE_SCREENSHOT_DIR=str(output/'screens/rule'),
        GEOMETRY_REPAIR_SCREENSHOT_DIR=str(output/'screens/repair'),
        GEOMETRY_ROOM_SCREENSHOT_DIR=str(output/'screens/room'),
        GEOMETRY_SCHEDULE_SCREENSHOT_DIR=str(output/'screens/schedule'),
        GEOMETRY_UX_REFINEMENT_SCREENSHOT_DIR=str(output/'screens/ux'),
        GEOMETRY_UIUX_SCREENSHOT_DIR=str(output/'screens/uiux'),
        GEOMETRY_ENGINEERING_DOWNLOAD_DIR=str(output/'engineering-downloads'))
    def capture(repo,url,env):
        value=gate.snapshot(repo,url,env)
        paths=[p for p in sorted((root/'geometry-web').iterdir()) if p.is_file() and p.suffix in {'.js','.css','.html'}]
        value['sourceSha256']={str(p.relative_to(root)):sha(p) for p in paths}
        value['runnerSha256']=sha(__file__);value['readOnlyLayoutPreloadSha256']=sha(BASE/'grid-rule-layout-read.cjs')
        value['launchAdapterSha256']={p.name:sha(p) for p in sorted(adapter.iterdir()) if p.is_file()}
        try:
            pid=value['runtime']['pid']
            parents=subprocess.check_output(['ps','-eo','pid=,ppid='],text=True)
            children=[{'pid':p,'parent':parent,'exe':str(Path(f'/proc/{p}/exe').resolve()),'sha256':sha(f'/proc/{p}/exe')}
                for p,parent in [tuple(map(int,line.split())) for line in parents.splitlines() if line.strip()]
                if parent==pid and Path(f'/proc/{p}/exe').resolve()==bridge]
            assert len(children)==1 and children[0]['sha256']==sha(bridge),children
            value['liveBridge']=children
        except Exception as error:value['problems'].append('live direct-child bridge: '+str(error))
        return value
    # mkdir occurs inside run_gate; screenshot directories are created by harness.
    command=['node','geometry-web/cdp_test.js']
    code,receipt=gate.run_gate(root,args.url,output,command,environment,args.timeout,capture=capture)
    receipt['purpose']='P87 original oracle diagnosis with existing GRID_SYSTEM_ONLY partial mode; not a full acceptance or golden claim'
    receipt['removedScopeEnvironment']=removed
    receipt['ownedBrowserProfile']=profile
    receipt['ownedCdpPort']=cdp_port
    receipt['stackBytes']=16777216
    if receipt.get('before') and receipt.get('after'):
        for key in ['sourceSha256','runnerSha256','launchAdapterSha256','readOnlyLayoutPreloadSha256','liveBridge']:
            if receipt['before'].get(key)!=receipt['after'].get(key):receipt['problems'].append(key+' changed during full CDP')
        sources=output/'executed-harness-sources';sources.mkdir()
        for relative,digest in receipt['before']['sourceSha256'].items():
            if sha(root/relative)!=digest:continue
            destination=sources/relative;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(root/relative,destination)
    if receipt['problems'] and code==0:
        code=2;receipt['executionVerified']=False;receipt['status']='source-or-identity-changed'
    receipt['gateExitCode']=code
    (output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'gateExitCode':code,'status':receipt['status'],'executionVerified':receipt['executionVerified'],
        'canonicalResult':receipt.get('evidence',{}).get('canonicalResult'),'receipt':str(output/'receipt.json')}))
    return code
if __name__=='__main__':sys.exit(main())
