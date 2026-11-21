// Node 24 on Windows. Start a headed Chrome on a separate desktop so its
// native file chooser can receive keystrokes without moving the user's focus.
import {execFileSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const helper = fileURLToPath(new URL('./native_picker.py', import.meta.url));
const exe = process.env.L4_CHROME_EXE || path.join(process.env.ProgramFiles, 'Google/Chrome/Application/chrome.exe');
const guard = path.join(os.homedir(), '.claude/hooks/browser-guard/prep-profile.mjs');
const {prepareBrowserProfile} = await import(pathToFileURL(guard));
const query = '[Console]::Write(([ADSI]"WinNT://./$env:USERNAME,user").BadPasswordAttempts.Value)';
function checkCounter() {
  const value = execFileSync('powershell.exe', ['-NoProfile', '-Command', query],
                             {encoding: 'utf8', windowsHide: true}).trim();
  if (value !== '0') throw new Error('Stop. BadPasswordAttempts=' + value);
  return Number(value);
}
const before = checkCounter();
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'r22-picker-profile-'));
prepareBrowserProfile(profile);
let browserPid, after;
try {
  browserPid = Number(execFileSync('python', [helper, 'launch', exe, profile],
                                  {encoding: 'utf8', windowsHide: true}).trim());
  if (!Number.isInteger(browserPid) || browserPid < 1) throw new Error('Missing Chrome pid');
} finally {
  after = checkCounter();
}
let port = 0;
for (let i = 0; i < 100 && !port; i++) {
  const active = path.join(profile, 'DevToolsActivePort');
  if (fs.existsSync(active)) port = Number(fs.readFileSync(active, 'utf8').split('\n')[0]);
  if (!port) await new Promise(resolve => setTimeout(resolve, 200));
}
if (!port) throw new Error('Chrome CDP endpoint unavailable, pid=' + browserPid);
checkCounter();
console.log(JSON.stringify({browserPid, endpoint: 'http://127.0.0.1:' + port,
  desktop: process.env.L4_PICKER_DESKTOP || 'GeometryL4Picker20261121',
  BadPasswordAttempts: {before, after}}));
