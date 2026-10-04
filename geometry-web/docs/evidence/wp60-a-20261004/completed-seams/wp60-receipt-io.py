import json, os, pathlib, subprocess
source=pathlib.Path('/tmp/wp60-receipt-io.scene')
source.write_text('boundary 7 outline 0,0 80,0 80,70 0,70\n')
for mode in ('open','write','read'):
    env={**os.environ,'LD_PRELOAD':'/tmp/wp60-receipt-io.so','WP60_IO_FAULT':mode}
    result=subprocess.run(['/tmp/geometry-tests/bridge'],input=f'dump\nload-prepare {source}\nload-confirm 1\ndump\n',text=True,capture_output=True,env=env,check=True,timeout=10)
    before,failed,confirm,after=map(json.loads,result.stdout.splitlines())
    assert failed=={'ok':False,'code':'IO','error':'Cannot serialize scene import candidate'},failed
    assert confirm['ok'] is False and confirm['code']=='TOKEN',confirm
    assert before==after,(before,after)
    print(f'PASS {mode}: IO response, candidate invalidated, zero world/revision change')
