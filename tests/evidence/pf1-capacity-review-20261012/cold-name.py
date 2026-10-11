import json,pathlib,sys,tempfile
sys.path.insert(0,'/workspace/geometry-axiom')
from tests._bridge import BridgeSession,find_bridge
from tests.test_panel_fill_finish_surface import BASE,put,surface
with tempfile.TemporaryDirectory(prefix='geometry-pr190-cold-') as tmp:
 path=pathlib.Path(tmp);scene=path/'base.scene';scene.write_bytes(BASE.encode())
 transaction=path/'txn.json'
 with BridgeSession(find_bridge(),cwd=path) as bridge:
  assert bridge.command('loadfile '+str(scene))['ok']
  revision=bridge.command('panel-fill-read')['revision']
  transaction.write_text(json.dumps({'schema':'panel-fill-transaction/1','expectedRevision':revision,'operations':[put(surface(name='a'*96))]}))
  preview=bridge.command('panel-fill-preview '+str(transaction))['preview'];assert preview['valid']
  assert bridge.command('panel-fill-confirm '+str(preview['token']))['ok']
  saved=bridge.command('dump');state=bridge.command('panel-fill-read')['state']
 scene.write_bytes(saved['text'].encode())
 with BridgeSession(find_bridge(),cwd=path) as reopened:
  result=reopened.command('loadfile '+str(scene));assert result['ok'],result
  after=reopened.command('dump');assert after['text'].encode()==saved['text'].encode()
  assert after['definition_sha256']==saved['definition_sha256']
  assert reopened.command('panel-fill-read')['state']==state
 print(json.dumps({'name_utf8_bytes':96,'cold_bridge_process':True,'dump_bytes':len(saved['text'].encode()),'dump_bytes_equal':True,'definition_sha256':saved['definition_sha256'],'state_equal':True}))
