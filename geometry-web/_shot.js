/* 截圖工具:node _shot.js <out.png> [setupExpr] [width height] */
const { spawn } = require("child_process");
const http = require("http");
const fs = require("fs");
const path = require("path");
const out = process.argv[2], setup = process.argv[3] || "true";
const W = +(process.argv[4] || 1382), H = +(process.argv[5] || 804);
const chrome = spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  ["--headless=new", "--disable-gpu", "--remote-debugging-port=9340",
   `--user-data-dir=C:/tmp/chrome-shot-${Date.now()}`,
   `--window-size=${W},${H}`, "http://localhost:8765/"], { stdio: "ignore" });
function j(u) {
  return new Promise((res, rej) => http.get(u,
    r => { let d = ""; r.on("data", c => d += c); r.on("end", () => res(JSON.parse(d))); })
    .on("error", rej));
}
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  let t;
  for (let i = 0; i < 30; i++) {
    try { t = (await j("http://localhost:9340/json")).find(x => x.url.includes("8765")); if (t) break; } catch {}
    await sleep(400);
  }
  if (!t) { console.log("NO TAB"); process.exit(1); }
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  let id = 0;
  const send = (m, p = {}) => new Promise(r => {
    const i = ++id;
    ws.onmessage = e => { const o = JSON.parse(e.data); if (o.id === i) r(o.result); };
    ws.send(JSON.stringify({ id: i, method: m, params: p }));
  });
  await new Promise(r => ws.onopen = r);
  await send("Emulation.setDeviceMetricsOverride",
    { width: W, height: H, deviceScaleFactor: 1, mobile: false });
  await sleep(2500);
  await send("Runtime.evaluate",
    { expression: `(async()=>{${setup}})()`, awaitPromise: true });
  await sleep(1200);
  const shot = await send("Page.captureScreenshot", { format: "png" });
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, Buffer.from(shot.data, "base64"));
  console.log("OK", out);
  chrome.kill(); process.exit(0);
})().catch(e => { console.log("ERR", e.message); chrome.kill(); process.exit(1); });
