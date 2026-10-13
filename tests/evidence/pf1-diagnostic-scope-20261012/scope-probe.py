import hashlib,json,pathlib,sys,tempfile
root=pathlib.Path('/workspace/geometry-axiom');sys.path.insert(0,str(root))
from tests._bridge import BridgeSession,find_bridge
from tests.test_panel_fill_finish_surface import BASE,put,surface
import tests.binaries as binaries
binary=find_bridge();rows=[]
with tempfile.TemporaryDirectory(prefix='geometry-pf1-scope-') as tmp:
 directory=pathlib.Path(tmp);scene=directory/'base.scene';scene.write_bytes(BASE.encode())
 with BridgeSession(binary,cwd=directory) as bridge:
  assert bridge.command('loadfile '+str(scene))['ok']
  def snapshot():return {'dump':bridge.command('dump')['text'],'read':bridge.command('panel-fill-read')}
  before=snapshot()
  for count in (2,65):
   for label,ref in (('duplicate','c1'),('missing','c99'),('malformed','x1')):
    refs=[ref]*count
    transaction=directory/'txn.json';transaction.write_text(json.dumps({'schema':'panel-fill-transaction/1','expectedRevision':before['read']['revision'],'operations':[put(surface(obstacles=refs))]}))
    result=bridge.command('panel-fill-preview '+str(transaction));assert result['ok'];preview=result['preview'];assert not preview['valid']
    violation=preview['violations'][0];wanted=('UNSUPPORTED','CAPACITY') if count>64 else ('INVALID','PANEL_FILL_INVALID')
    assert (violation['status'],violation['code'])==wanted
    assert not bridge.command('panel-fill-confirm '+str(preview['token']))['ok']
    assert snapshot()==before
    prefix='requires engineering-spec/1\nrequires parameters/1\nrequires panel-fill/1\n'
    record='finish-surface 1 on boundary 4 origin 0 0 2480 u +x v +y n +z side +n obstacles '+' '.join(refs)+' name-hex 61\n'
    scene.write_bytes((BASE+prefix+record).encode());loaded=bridge.command('loadfile '+str(scene));assert not loaded['ok']
    assert (loaded['status'],loaded['code'])==('INVALID','SCENE_INVALID');assert snapshot()==before
    rows.append({'scenario':label,'references':count,'json':violation,'scene':loaded,'json_confirm_rejected':True,'dump_read_state_revision_unchanged':True})
print(json.dumps({'schema':'pf1-diagnostic-scope/1','sources':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['current_geometry.c','geometry-core/finish_surfaces.inc','geometry-web/web_bridge.c','geometry-web/panel_fill_bridge.inc','tests/test_panel_fill_finish_surface.py']},'native_binary':str(binary),'native_binary_sha256':hashlib.sha256(pathlib.Path(binary).read_bytes()).hexdigest(),'sidecar':json.loads(binaries.BY_NAME['bridge'].sidecar.read_text()),'cases':rows},ensure_ascii=False,indent=2))
