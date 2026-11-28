'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {spawn}=require('node:child_process'),http=require('node:http');
const {once}=require('node:events');

// 這是假頁面，沒有 bridge 或使用者場景。記錄舊診斷的第一個 reset 意圖就中止。
test('T39_DIAGNOSTIC_REFUSES_OCCUPIED_LOOPBACK',async()=>{
  const writes=[];
  const server=http.createServer((req,res)=>{
    if(req.method==='POST'){writes.push(req.url);res.end();return;}
    res.setHeader('Content-Type','text/html');res.end(`<script>
      const connection={phase:'ready'};function resetSceneFocus(){}function setView3(){}
      async function apiRequest(text){await fetch('/intent/'+text,{method:'POST'});throw Error('sentinel');}
    </script>`);
  });
  server.listen(0,'127.0.0.1');await once(server,'listening');
  try{
    const port=server.address().port;
    const child=spawn(process.execPath,[require.resolve('./pf6_review_browser.cjs'),`http://127.0.0.1:${port}/`,'390','suggested'],{stdio:['ignore','pipe','pipe']});
    let output='';for(const stream of [child.stdout,child.stderr])stream.on('data',data=>{output+=data;});
    const [code]=await once(child,'close');
    assert.deepEqual(writes,[],'T39_FOREIGN_SERVICE_RECEIVED_WRITE');
    assert.notEqual(code,0);assert.match(output,/連接埠 .* 無法使用/,'T39_REFUSED_BECAUSE_PORT_IS_OCCUPIED');
  }finally{await new Promise(resolve=>server.close(resolve));}
});
