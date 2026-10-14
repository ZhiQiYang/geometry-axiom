const test = require('node:test');
const assert = require('node:assert/strict');
const {createTransportFailureTrace, installClientTransportTrace} = require('../geometry-web/transport_failure_trace.js');

test('canvas observer remains independent of the disabled server flag', async () => {
  const prior = process.env.GEOMETRY_WAIT_TRACE;
  delete process.env.GEOMETRY_WAIT_TRACE;
  try {
    let ticks = 0, calls = 0;
    const result = {ok:true};
    const promise = Promise.resolve(result);
    const target = {apiRequest: () => { calls++; return promise; }};
    const reports = [];
    installClientTransportTrace(target, record => reports.push(record), () => ({wall:'test',monotonic:++ticks}));
    assert.strictEqual(target.apiRequest('one'), promise);
    assert.strictEqual(await promise, result);
    assert.equal(ticks, 1, 'BROWSER_OBSERVER_IS_NOT_SERVER_DEFAULT_OFF');
    assert.equal(calls, 1);
    assert.deepEqual(reports, []);
  } finally {
    if (prior === undefined) delete process.env.GEOMETRY_WAIT_TRACE;
    else process.env.GEOMETRY_WAIT_TRACE = prior;
  }
});

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

test('frontend transport flag is recorded even without a failed network event', async () => {
  assert.equal(typeof installClientTransportTrace, 'function', 'API_TRANSPORT_OBSERVER_MISSING');
  const trace = createTransportFailureTrace('http://localhost:8765');
  const firstResult = {ok:false,transport:true,error:'first bridge failure'};
  let calls = 0, tick = 0;
  const promises = [Promise.resolve(firstResult),Promise.resolve({ok:false,transport:true,error:'later guard'})];
  const target = {apiRequest: () => promises[calls++]};
  const reports = [];
  installClientTransportTrace(target, record => { reports.push(record); trace.observeApiFailure(record); }, () => ({wall:`time-${++tick}`,monotonic:tick}));
  const first = target.apiRequest('first command');
  assert.strictEqual(first, promises[0], 'API_PROMISE_IDENTITY_CHANGED');
  assert.strictEqual(await first, firstResult);
  await target.apiRequest('later command');
  assert.equal(calls, 2, 'API_OBSERVER_RETRIED');
  assert.equal(reports.length, 1, 'API_FIRST_FAILURE_OVERWRITTEN');
  assert.equal(trace.apiFirst().command, 'first command');
  assert.equal(trace.apiFirst().error, 'first bridge failure');
  assert.equal(trace.first(), null, 'BODY_TRANSPORT_IS_NOT_NETWORK_FAILURE');
  trace.observeApiFailure({...reports[0],command:'secondary'});
  assert.equal(trace.apiFirst().command, 'first command', 'API_COLLECTOR_OVERWRITTEN');
});

test('observer preserves success and rejection and does not replay either', async () => {
  assert.equal(typeof installClientTransportTrace, 'function', 'API_TRANSPORT_OBSERVER_MISSING');
  let calls = 0;
  const value = {ok:true};
  const error = Error('original rejection');
  const target = {apiRequest: () => { calls++; return calls === 1 ? Promise.resolve(value) : Promise.reject(error); }};
  const reports = [];
  installClientTransportTrace(target, record => reports.push(record));
  assert.strictEqual(await target.apiRequest('success'), value);
  await assert.rejects(target.apiRequest('reject'), caught => caught === error);
  assert.equal(calls, 2);
  assert.deepEqual(reports, []);
});

test('a broken diagnostic sink cannot alter a transport result', async () => {
  assert.equal(typeof installClientTransportTrace, 'function', 'API_TRANSPORT_OBSERVER_MISSING');
  const value = {ok:false,transport:true,error:'original'};
  const promise = Promise.resolve(value);
  const target = {apiRequest: () => promise};
  installClientTransportTrace(target, () => { throw Error('sink unavailable'); });
  assert.strictEqual(target.apiRequest('cmd'), promise);
  assert.strictEqual(await promise, value);
});
