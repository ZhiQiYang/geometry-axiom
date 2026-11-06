"""Native-only fixtures/producer for R362 controller and adapter acceptance."""
import json, os, secrets, sys, tempfile
from pathlib import Path
from copy import deepcopy
from tests.test_model_update_identity_faces import ModelIdentityFaces
from tests.test_model_update import update, space_modeling, ModelError
from modeling import verify_package
from tests._bridge import BridgeSession

def fixture():
    # Match the native product launcher's 16 MiB stack for placement projection.
    if os.name != 'nt':
        import resource
        soft,hard=resource.getrlimit(resource.RLIMIT_STACK)
        if soft != resource.RLIM_INFINITY and soft < 16*1024*1024:
            resource.setrlimit(resource.RLIMIT_STACK,(16*1024*1024,hard))
    ModelIdentityFaces.setUpClass()
    old=deepcopy(ModelIdentityFaces.faces)
    with tempfile.TemporaryDirectory(prefix='r362-faces-live-') as directory:
        path=Path(directory)/'original.scene';path.write_text(old['input']['base_scene'])
        with BridgeSession(ModelIdentityFaces.native['bridge_executable']) as bridge:
            def read(command):
                response=bridge.command(command)
                assert response.get('ok') is True, (command,response)
                if command.startswith('line ') and response.get('preview',{}).get('valid'):
                    response=bridge.command('line confirm '+str(response['preview']['token']))
                    assert response.get('ok') is True,(command,response)
                return response
            read('loadfile '+str(path));read('identity-epoch '+secrets.token_hex(16));read('line identity-ledger activate')
            before=read('source-inspect')
            nodes={value['key']:value for value in before['nodes']}
            old['sourceIdentity']={'schema':'model-source-identity/1','roots':[
                {'role':'use','kind':'placement','id':use['placement_id'],
                 'incarnation':nodes['placement:'+str(use['placement_id'])]['incarnation'],
                 'definitionPin':nodes['placement:'+str(use['placement_id'])]['definitionFingerprint']}
                for use in old['input']['uses']]}
            for line in old['input']['base_scene'].replace('2800','3000').splitlines():read('line '+line)
            graph=read('source-inspect');scene=read('dump-deidentified')['text'];full=read('dump')
            return {'record':old,'scene':scene,'fullScene':full['text'],'capabilities':full['capabilities'],'requiredCapabilities':full['required_capabilities'],'graph':graph,'oldGraph':before,
                    'surfaces':read('surfaces')['surfaces'],'objects':read('objects'),
                    'selection':{'mode':'faces','uses':[{'placement_id':u['placement_id']} for u in old['input']['uses']],'obstacles':[]}}

if __name__=='__main__':
    try:
        mode=sys.argv[1]
        if mode=='fixture':result=fixture()
        else:
            data=json.load(sys.stdin)
            if mode=='update':result=update.prepare_update(data)
            elif mode=='replay':result=space_modeling.replay_stored(data['input'],data['result'])
            elif mode=='verify':result=verify_package(data)
            else:raise ValueError(mode)
    except ModelError as error:result=error.as_dict()
    print(json.dumps(result,ensure_ascii=False))
