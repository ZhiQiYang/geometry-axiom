// Run the existing acceptance unchanged, adding failure-only evidence capture.
// Product source and original test bytes are never written.
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const sourcePath = path.resolve(__dirname, '../../../tests/test_section_profile_browser.js');
let source = fs.readFileSync(sourcePath, 'utf8');
const needle = '}catch(error){fs.writeFileSync';
if (!source.includes(needle)) throw Error('Original diagnostic insertion point changed');
source = source.replace(needle, `}catch(error){
 try {
   if(page) {
     fs.writeFileSync(path.join(out,'failure-visible.txt'),await page.locator('body').innerText());
     await page.screenshot({path:path.join(out,'failure.png'),fullPage:true});
     fs.writeFileSync(path.join(out,'failure-console.json'),JSON.stringify(errors,null,2));
   }
 } catch(captureError) { console.error('Failure capture:',captureError.message); }
 fs.writeFileSync`);
const run = new Module(sourcePath, module);
run.filename = sourcePath;
run.paths = Module._nodeModulePaths(path.dirname(sourcePath));
run._compile(source, sourcePath);
