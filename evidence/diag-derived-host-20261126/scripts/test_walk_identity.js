// 隔離測共用的走查入口：假服務只提供 /runtime 和空白頁，沒有場景寫入路徑。
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs'), http = require('node:http'), os = require('node:os'), path = require('node:path');

test('走查只接受本次行程紀錄、runtime 與同一個 App 頁面', async t => {
  const fb = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'walk-identity-')));
  t.after(() => fs.rmSync(fb, { recursive: true, force: true }));
  const runtime = { schema: 'geometry-runtime/1', pid: process.pid, root: fb, fresh: true,
    version: 'test-version', session: 'test-session' };
  let live = runtime, pageSession = runtime.session;
  const requests = [];
  const server = http.createServer((req, res) => {
    requests.push(req.method + ' ' + req.url);
    if (req.url === '/runtime') return res.end(JSON.stringify(live));
    res.writeHead(200, { 'Content-Type': 'text/html', 'X-Geometry-Session': pageSession, 'X-Geometry-Version': runtime.version });
    res.end('<html></html>');
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => server.close());
  const { port } = server.address();
  const url = `http://127.0.0.1:${port}/`;
  process.env.GEOMETRY_FEEDBACK_DIR = fb;
  process.env.APP_URL = url;
  const L = require('./lib.js');
  const record = { feedback: fb, port, pid: runtime.pid, worktree: runtime.root, session: runtime.session, version: runtime.version };
  const save = values => fs.writeFileSync(path.join(fb, 'server-pid.json'), JSON.stringify(values));
  save(record);

  async function open() {
    const { b, runtime } = await L.start();
    await b.close();
    return runtime;
  }
  for (const change of [{ pid: runtime.pid + 1 }, { root: fb + '-other' }, { session: 'other' },
                         { version: 'old' }, { fresh: false }, { session: undefined }]) {
    live = { ...runtime, ...change };
    requests.length = 0;
    await assert.rejects(open, /runtime 與本次啟動紀錄不符/);
    assert.deepEqual(requests, ['GET /runtime']); // 連 App 首頁都不能開。
  }
  save({ ...record, port: port === 18891 ? 18892 : 18891 });
  await assert.rejects(open, /APP_URL/);
  save({ ...record, session: undefined }); // 尚未通過啟動探測的紀錄。
  await assert.rejects(open, /啟動紀錄不完整/);
  save(record);
  live = runtime;
  pageSession = 'other'; // 探測正確，實際導覽卻不是同一個服務。
  await assert.rejects(open, /頁面與本次啟動紀錄不符/);
  pageSession = runtime.session;
  assert.deepEqual(await open(), runtime);
  fs.unlinkSync(path.join(fb, 'server-pid.json'));
  await assert.rejects(open, /ENOENT/);
});
