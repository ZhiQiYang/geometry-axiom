"""Deterministic format-8 example, built through real native transactions."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests._bridge import BridgeSession,find_bridge
from tests.test_assembly_rules import rule,binding


def build():
    with tempfile.TemporaryDirectory(prefix='ar06-example-') as directory, BridgeSession(find_bridge(),cwd=directory) as bridge:
        def command(text):
            r=bridge.command(text)
            if not r.get('ok'):raise RuntimeError(r)
            return r
        def line(text):
            r=command('line '+text)
            if r.get('preview'):
                if not r['preview']['valid']:raise RuntimeError(r)
                command('line confirm '+str(r['preview']['token']))
        def apply(operations,generation=False):
            path=Path(directory)/'transaction.json';path.write_text(json.dumps({'schema':'assembly-generation-transaction/1' if generation else 'assembly-transaction/1','expectedRevision':command('assembly-read')['revision'],'operations':operations},ensure_ascii=False))
            p=command(('assembly-generation-preview ' if generation else 'assembly-preview ')+str(path))['preview']
            if not p['valid']:raise RuntimeError(p)
            command('assembly-confirm '+str(p['token']))
        command('reset')
        for text in ['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',*[f'spec position{i} {value}' for i,value in [(1,500),(2,2500),(3,1500)]],*[f'guide {i} 1 {axis} spec:position{i}' for i,axis in [(1,'v'),(2,'v'),(3,'u')]],'timber 90 20 20 role boundary','place 90 on 1 at-face e0 +u +n','timber 91 20 20 role boundary','place 91 on 1 at-face e2 +u +n']:
            line(text)
        value=binding()
        for slot in value['slots']:slot['orientation']='A'
        apply([{'op':'publish-rule','value':rule()},{'op':'create-binding','value':value}])
        fingerprint=command('assembly-read')['state']['rules'][0]['fingerprint']
        source={'id':1,'name':'雙主支與端接副支','bindingId':1,'rule':{'id':1,'version':1,'fingerprint':fingerprint},'surfaceId':1,'members':[{'memberId':i,'role':'secondary' if i==3 else 'primary','guideId':i,'dir':'+u' if i==3 else '+v','depthSide':'+n','ends':{'start':{'kind':'member','memberId':1},'finish':{'kind':'member','memberId':2}} if i==3 else {'start':{'kind':'timber','id':90},'finish':{'kind':'timber','id':91}}} for i in [1,2,3]]}
        apply([{'op':'create-instance','value':source,'expectedBindingFingerprint':command('assembly-read')['state']['bindings'][0]['fingerprint']}],True)
        state=command('assembly-read')['state'];assert [m['geometry']['length'] for m in state['instances'][0]['members']]==[2960,2960,1973]
        line('canvas-pos assembly-rule 1 40 40');line('canvas-pos assembly-binding 1 400 40')
        scene=command('dump')['text'].replace('\r\n','\n').encode()
    manifest={'format':'geometry-canvas/8','projectId':'assembly-generation-v1','name':'組構生成範例','sceneHash':hashlib.sha256(scene).hexdigest(),'sources':[],'faces':[],'models':[],'faceProjections':[],'requiredCapabilities':['assembly-rule-authoring/1','assembly-timber-generation/1','engineering-spec/1']}
    return scene,json.dumps(manifest,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();target=ROOT/'geometry-web/examples/assembly-generation-v1.gcanvas';scene,manifest=build()
    if args.check:
        with zipfile.ZipFile(target) as archive:
            assert archive.read('world.scene')==scene;assert archive.read('manifest.json')==manifest
        print('generation example matches native rebuild')
    else:
        with zipfile.ZipFile(target,'w') as archive:
            for name,data in [('world.scene',scene),('manifest.json',manifest)]:
                info=zipfile.ZipInfo(name,(2026,10,3,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,data)
        print(target)
