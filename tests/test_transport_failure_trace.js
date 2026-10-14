const test = require('node:test');
const assert = require('node:assert/strict');
const {createTransportFailureTrace} = require('../geometry-web/transport_failure_trace.js');

test('first API transport failure survives later failures and other sessions', () => {
  let tick = 0;
  const trace = createTransportFailureTrace('http://localhost:8765', () => `time-${++tick}`);
  const request = (id, sessionId, path) => ({method:'Network.requestWillBeSent',sessionId,params:{requestId:id,timestamp:1,request:{url:`http://localhost:8765${path}`,method:'POST',postData:'{"cmd":"dump"}'}}});
  trace.observe(request('1','a','/api'), 'first step');
  trace.observe(request('1','b','/api'), 'other step');
  trace.observe({method:'Network.loadingFailed',sessionId:'a',params:{requestId:'1',timestamp:16,errorText:'net::ERR_ABORTED',canceled:true}}, 'later step');
  const first = trace.first();
  trace.observe({method:'Network.loadingFailed',sessionId:'b',params:{requestId:'1',timestamp:17,errorText:'secondary'}}, 'secondary');
  assert.strictEqual(trace.first(), first, 'FIRST_TRANSPORT_FAILURE_OVERWRITTEN');
  assert.equal(first.step, 'first step');
  assert.equal(first.postData, '{"cmd":"dump"}');
  assert.equal(first.failedMonotonic, 16);
  assert.equal(first.failedAt, 'time-3');
});

test('successful API and asset failures do not become API transport failures', () => {
  const trace = createTransportFailureTrace('http://localhost:8765');
  for (const path of ['/api','/app.js']) {
    trace.observe({method:'Network.requestWillBeSent',params:{requestId:path,request:{url:`http://localhost:8765${path}`,method:'POST'}}}, 'step');
    trace.observe({method:path === '/api' ? 'Network.loadingFinished' : 'Network.loadingFailed',params:{requestId:path,errorText:'asset'}}, 'step');
  }
  assert.equal(trace.first(), null);
});

test('first non-api business fetch failure survives later api failure', () => {
  const trace = createTransportFailureTrace('http://localhost:8765');
  trace.observe({method:'Network.requestWillBeSent',params:{requestId:'model',type:'Fetch',timestamp:1,request:{url:'http://localhost:8765/model/space-preview',method:'POST',postData:'{"fixture":true}'}}}, 'model step');
  trace.observe({method:'Network.responseReceived',params:{requestId:'model',type:'Fetch',timestamp:2,response:{status:503,statusText:'Unavailable'}}}, 'model step');
  trace.observe({method:'Network.requestWillBeSent',params:{requestId:'api',type:'Fetch',timestamp:3,request:{url:'http://localhost:8765/api',method:'POST'}}}, 'api step');
  trace.observe({method:'Network.loadingFailed',params:{requestId:'api',timestamp:4,errorText:'secondary'}}, 'api step');
  assert.equal(trace.first()?.url, 'http://localhost:8765/model/space-preview', 'FIRST_BUSINESS_FETCH_FAILURE_MISSING');
  assert.equal(trace.first().status, 503);
  assert.equal(trace.first().step, 'model step');
});
