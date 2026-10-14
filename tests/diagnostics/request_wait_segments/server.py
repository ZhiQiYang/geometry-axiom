"""Run the unmodified server with observational proxies and test-only contention.

No product source, deadline, receipt body or native reply is rewritten. Only the
dedicated diagnostic service accepts /__diag/hold; never attach to a user service.
"""
import argparse,hashlib,importlib.util,json,os,pathlib,signal,sys,threading,time

parser=argparse.ArgumentParser();parser.add_argument('--repo',type=pathlib.Path,required=True);parser.add_argument('--out',type=pathlib.Path,required=True);parser.add_argument('--port',type=int,required=True)
args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
tls=threading.local();write_lock=threading.Lock();active={};holds=[]
stream=(args.out/'server-events.jsonl').open('a',buffering=1)
def emit(event,**fields):
 row={'event':event,'mono_ns':time.monotonic_ns(),'pid':os.getpid(),'tid':threading.get_native_id(),'request':getattr(tls,'request',None),'command':getattr(tls,'command',None),**fields}
 with write_lock:stream.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
class Lock:
 def __init__(self,inner,stage,context=None):self.inner=inner;self.stage=stage;self.context=context
 def acquire(self,*a,**kw):
  start=time.monotonic_ns();emit(self.stage+'_wait',context=self.context)
  value=self.inner.acquire(*a,**kw)
  emit(self.stage+'_acquired',context=self.context,acquired=value,wait_ms=(time.monotonic_ns()-start)/1e6)
  return value
 def release(self):
  self.inner.release();emit(self.stage+'_released',context=self.context)
 def __enter__(self):self.acquire();return self
 def __exit__(self,*unused):self.release()
 def __getattr__(self,key):return getattr(self.inner,key)
class Input:
 def __init__(self,inner,context):self.inner=inner;self.context=context
 def write(self,data):
  active[self.context]={'request':getattr(tls,'request',None),'command':getattr(tls,'command',None)}
  start=time.monotonic_ns();emit('stdin_write_begin',context=self.context,bytes=len(data))
  try:return self.inner.write(data)
  finally:emit('stdin_write_end',context=self.context,elapsed_ms=(time.monotonic_ns()-start)/1e6)
 def flush(self):
  start=time.monotonic_ns();emit('stdin_flush_begin',context=self.context)
  try:return self.inner.flush()
  finally:emit('stdin_flush_end',context=self.context,elapsed_ms=(time.monotonic_ns()-start)/1e6)
 def __getattr__(self,key):return getattr(self.inner,key)
class Responses:
 def __init__(self,inner,context):self.inner=inner;self.context=context
 def put(self,value,*a,**kw):
  emit('native_response_arrived',context=self.context,bytes=len(value),sha256=hashlib.sha256(value).hexdigest(),**active.get(self.context,{}))
  return self.inner.put(value,*a,**kw)
 def get(self,*a,**kw):
  start=time.monotonic_ns();emit('response_queue_wait',context=self.context)
  try:return self.inner.get(*a,**kw)
  finally:emit('response_queue_end',context=self.context,elapsed_ms=(time.monotonic_ns()-start)/1e6)
 def __getattr__(self,key):return getattr(self.inner,key)
def observe_native(native):
 key=str(native.bridge.pid)
 native.bridge_lock=Lock(native.bridge_lock,'bridge_lock',key)
 native.receipt_lock=Lock(native.receipt_lock,'receipt_lock',key)
 native.bridge.stdin=Input(native.bridge.stdin,key)
 native.bridge_responses=Responses(native.bridge_responses,key)
 return native

sys.path[:0]=[str(args.repo),str(args.repo/'geometry-web')];sys.argv=[str(args.repo/'geometry-web/serve.py'),str(args.port)]
spec=importlib.util.spec_from_file_location('diagnostic_product_server',args.repo/'geometry-web/serve.py');product=importlib.util.module_from_spec(spec);spec.loader.exec_module(product)
observe_native(product.root_context)
old_init=product.NativeContext.__init__
def native_init(self,*a,**kw):old_init(self,*a,**kw);observe_native(self)
product.NativeContext.__init__=native_init
product.RUNTIME._lock=Lock(product.RUNTIME._lock,'runtime_lock','global')
old_fresh=product.RUNTIME.fresh
def fresh():
 start=time.monotonic_ns();emit('fresh_enter')
 try:return old_fresh()
 finally:emit('fresh_exit',elapsed_ms=(time.monotonic_ns()-start)/1e6)
product.RUNTIME.fresh=fresh
class Read:
 def __init__(self,inner):self.inner=inner
 def read(self,*a,**kw):
  value=self.inner.read(*a,**kw)
  try:
   data=json.loads(value);tls.command=data.get('cmd','receipt:'+str(data.get('receipt')))
   emit('request_body',business_request_id=data.get('requestId'),receipt=data.get('receipt'),bytes=len(value))
  except (ValueError,AttributeError):pass
  return value
 def __getattr__(self,key):return getattr(self.inner,key)
def load(data):
 stage=data['stage'];seconds=float(data['seconds']);assert stage in ['runtime','receipt','bridge','native'] and 0<=seconds<=25
 acquired=threading.Event();release=threading.Event();native=product.root_context
 def worker():
  tls.request='load:'+str(data.get('label',stage));tls.command=None;lock=None
  try:
   if stage=='native':
    assert native.bridge.poll() is None
    assert int(pathlib.Path(f'/proc/{native.bridge.pid}/stat').read_text().split(') ')[1].split()[1])==os.getpid()
    os.kill(native.bridge.pid,signal.SIGSTOP)
   else:
    lock={'runtime':product.RUNTIME._lock,'receipt':native.receipt_lock,'bridge':native.bridge_lock}[stage];lock.acquire()
   emit('load_held',stage=stage,seconds=seconds,native_pid=native.bridge.pid);acquired.set();release.wait(seconds)
  finally:
   if stage=='native':
    try:os.kill(native.bridge.pid,signal.SIGCONT)
    except ProcessLookupError:pass
   elif lock is not None:lock.release()
   emit('load_released',stage=stage)
 thread=threading.Thread(target=worker,daemon=True);holds.append((release,thread));thread.start()
 if not acquired.wait(5):raise RuntimeError('diagnostic load was not acquired')
 return {'ok':True,'stage':stage,'seconds':seconds,'native_pid':native.bridge.pid}

old_post=product.Handler.do_POST
def post(self):
 tls.request=self.headers.get('X-Geometry-Diagnostic-Id','unlabelled:'+str(threading.get_native_id()));tls.command=None
 emit('http_enter',path=self.path)
 if self.path=='/__diag/status':
  native=product.root_context
  self._send(json.dumps({'native_returncode':native.bridge.poll(),'bridge_failure':native.bridge_failure}).encode());return
 if self.path=='/__diag/hold':
  data=json.loads(self.rfile.read(int(self.headers['Content-Length'])));self._send(json.dumps(load(data)).encode());return
 original=self.rfile;self.rfile=Read(original)
 try:return old_post(self)
 finally:self.rfile=original;emit('http_exit')
product.Handler.do_POST=post
old_send=product.Handler._send
def send(self,body,*a,**kw):
 start=time.monotonic_ns();emit('http_write_begin',bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),status=kw.get('status',200))
 try:return old_send(self,body,*a,**kw)
 except Exception as e:emit('http_write_error',exception=type(e).__name__,message=str(e));raise
 finally:emit('http_write_end',elapsed_ms=(time.monotonic_ns()-start)/1e6)
product.Handler._send=send
server=product.PreviewHTTPServer(('127.0.0.1',args.port),product.Handler)
ready={'server_pid':os.getpid(),'native_pid':product.root_context.bridge.pid,'port':args.port,'root':str(args.repo),'version':product.RUNTIME.version,'binary':product.BRIDGE_CMD[0],'binary_sha256':hashlib.sha256(pathlib.Path(product.BRIDGE_CMD[0]).read_bytes()).hexdigest(),'clock':'server monotonic_ns; subtract only within this process'}
(args.out/'ready.json').write_text(json.dumps(ready,indent=2)+'\n');emit('server_ready',**ready)
def stop(*unused):raise KeyboardInterrupt
signal.signal(signal.SIGTERM,stop)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:
 for event,thread in holds:event.set()
 for event,thread in holds:thread.join(3)
 server.server_close();product.root_context.close()
 for native in product.scenario_contexts.values():native.close()
 emit('server_stopped');stream.close()
