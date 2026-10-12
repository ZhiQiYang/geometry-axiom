import ast,errno,json,pathlib,socket,subprocess,sys,types,unittest
root=pathlib.Path('/workspace/geometry-axiom');source=(subprocess.check_output(['git','show','5d7b044:tests/test_lan_review.py'],cwd=root).decode() if '--before' in sys.argv else (root/'tests/test_lan_review.py').read_text())
tree=ast.parse(source);method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='test_denied_late_body_is_drained_after_response_before_socket_release')
guard=next(n for n in ast.walk(method) if isinstance(n,ast.Try) and any(isinstance(a,ast.Call) and isinstance(a.func,ast.Attribute) and a.func.attr=='sendall' for a in ast.walk(n)))
block=next(n for n in ast.walk(method) if hasattr(n,'body') and isinstance(n.body,list) and guard in n.body);following=block.body[block.body.index(guard)+1]
code=compile(ast.fix_missing_locations(ast.Module(body=[guard,following],type_ignores=[])),'actual-lan-review-guard','exec')
cases=[('ENOTCONN',lambda:OSError(errno.ENOTCONN,'closed')),('broken-pipe',lambda:BrokenPipeError('pipe')),('reset',lambda:ConnectionResetError('reset')),
 ('EBADF',lambda:OSError(errno.EBADF,'bad fd')),('ETIMEDOUT',lambda:OSError(errno.ETIMEDOUT,'timeout')),('ENETUNREACH',lambda:OSError(errno.ENETUNREACH,'network')),('no-errno',lambda:OSError('no errno')),('permission',lambda:PermissionError(errno.EACCES,'permission'))]
rows=[]
for operation in ('sendall','shutdown'):
 for label,factory in cases:
  error=factory()
  def send(*a):
   if operation=='sendall':raise error
  def shutdown(*a):
   if operation=='shutdown':raise error
  try:exec(code,{'client':types.SimpleNamespace(sendall=send,shutdown=shutdown),'socket':socket,'errno':errno,'body':b'body','drained':types.SimpleNamespace(wait=lambda timeout:False),'self':unittest.TestCase()})
  except BaseException as actual:
   expected=label in ('broken-pipe','reset') or label=='ENOTCONN' and '--before' not in sys.argv
   if expected:assert type(actual) is AssertionError and 'refused late body was not drained after the response' in str(actual)
   else:assert actual is error
   rows.append({'operation':operation,'case':label,'exception':type(actual).__name__,'same_exception':actual is error,'drain_assert_reached':type(actual) is AssertionError})
  else:raise AssertionError('guard reached no original drain assertion or error')
print(json.dumps({'before':'--before' in sys.argv,'actual_source_guard_and_next_assert':True,'cases':rows},indent=2))
