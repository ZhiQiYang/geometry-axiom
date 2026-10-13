import pathlib,subprocess,sys
root=pathlib.Path('/workspace/geometry-axiom')
names=['geometry-core/finish_surfaces.inc','geometry-web/web_bridge.c']
fixed={n:(root/n).read_bytes() for n in names}
try:
 for n in names:(root/n).write_bytes(subprocess.check_output(['git','show','26a7c443b9bd10ae036b0956bd99233f594b5395:'+n],cwd=root))
 p=subprocess.run([sys.executable,'/tmp/geometry-190-run.py','corrected-input-original-product',sys.executable,'-m','unittest','-v',
  *['tests.test_panel_fill_finish_surface.FinishSurfaceNative.'+n for n in (
  'test_name_capacity_is_not_invalid_and_never_commits','test_scene_obstacle_capacity_is_structured_and_atomic','test_scene_name_capacity_preserves_invalid_format_and_world')]],cwd=root)
finally:
 for n,data in fixed.items():(root/n).write_bytes(data)
sys.exit(p.returncode)
