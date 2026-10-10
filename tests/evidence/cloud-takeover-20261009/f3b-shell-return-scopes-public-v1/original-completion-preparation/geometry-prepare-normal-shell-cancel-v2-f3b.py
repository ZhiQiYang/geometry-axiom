from pathlib import Path
import hashlib, json

base = Path('<workspace-path>')
output = base / 'geometry-root-shell-cancel-completion-v2-f3b'
assert not output.exists()
output.mkdir()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
old_helper = base / 'geometry-takeover-ui-tail/p77-shared-header-scope-9eb/normal_asm_sp_return_probe.cjs'
old_driver = base / 'geometry-ui-verification/shell-return-f3b/normal_shell_return_driver.cjs'
old_wrapper = base / 'geometry-root-normal-shell-return-gate-f3b.py'
old_controller = base / 'geometry-root-owned-shell-lifecycle-f3b.py'
helper = output / 'normal_asm_sp_return_probe.cjs'
driver = output / 'normal_shell_return_driver.cjs'
wrapper = output / 'run_normal_shell_return_gate.py'
controller = output / 'owned_shell_lifecycle.py'
assert sha(old_helper) == 'ca3ecb98d6091283bb242f4528ae0a47b153888626f7fe1d85479de649e74471'
assert sha(old_driver) == '31d0233a74630ee97fa9fae8a185b0c191f9a7142432306b3fa5cf783421aef1'
assert sha(old_wrapper) == '6bf4e3d7f965e7e0aba8cda783aff16ac717797d8e4513fce1bc297c752cd8eb'
assert sha(old_controller) == '73c1f08e5197dbe360744d490a7798d2971feb9f4e257e3dddda6e2c271c503c'
text = old_helper.read_text()
needle = 'if(cancel&&await page.locator(cancel).isEnabled()){await normalClick(cancel);check('
assert text.count(needle) == 1
text = text.replace(needle, '''if(cancel&&await page.locator(cancel).isEnabled()){await normalClick(cancel);
          // Original cancel() reads five native responses before its finally
          // restores controls. Observe that original completion once; do not
          // retry the click or bypass a busy/dirty guard. Preserve all40 checks.
          await page.waitForFunction(()=>document.getElementById('spStatus')?.textContent==='已取消修改，未改動世界。'&&document.getElementById('spCancel')?.disabled===true&&document.getElementById('spClose')?.disabled===false,null,{timeout:20000});
          check(''')
helper.write_text(text)
text = old_driver.read_text().replace(str(old_helper), str(helper)).replace(sha(old_helper), sha(helper)).replace('immutable ca3 helper required', 'immutable completion-aware helper required')
driver.write_text(text)
text = old_wrapper.read_text().replace(str(old_helper), str(helper)).replace(str(old_driver), str(driver)).replace(sha(old_helper), sha(helper)).replace(sha(old_driver), sha(driver))
wrapper.write_text(text)
text = old_controller.read_text().replace(str(old_wrapper), str(wrapper)).replace(sha(old_wrapper), sha(wrapper))
controller.write_text(text)
record = {'purpose': 'Single bounded normal SP Cancel completion precondition: original status plus Cancel disabled and Close enabled. All original40 assertions unchanged; previous16/1 source and logs retained. No product or golden edits.', 'originalSources': {str(p): sha(p) for p in [old_helper, old_driver, old_wrapper, old_controller]}, 'newSources': {str(p): sha(p) for p in [helper, driver, wrapper, controller]}}
(output / 'preparation.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record))
