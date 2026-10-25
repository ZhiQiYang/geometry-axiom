"""Synthetic only; no original user profile is read or printed."""
from pathlib import Path
import base64,json,sys,unittest

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'scan_profile_scope.py'
source=SOURCE.read_text()
if '--withdraw-decoder' in sys.argv:
 sys.argv.remove('--withdraw-decoder')
 needle="     inspect_text(decoded.decode('utf-8'),depth+1)  # FOLLOW_DECODED_PROFILE"
 if source.count(needle)!=2:raise RuntimeError('Exact two decoder guards required')
 source=source.replace(needle,'     pass  # WITHDRAWN_DECODED_PROFILE_GUARD')
namespace={'__name__':'synthetic_profile_detector','__file__':str(SOURCE)}
exec(compile(source,str(SOURCE),'exec'),namespace)

class EncodingGuard(unittest.TestCase):
 def test_reordered_minified_profile_encodings_are_detected(self):
  profile={'login':'synthetic-only','id':17,'node_id':'synthetic-node','type':'User','bio':'synthetic-text','extra':None}
  body=(json.dumps(profile,indent=20)+'\n').encode()
  raw=b'HTTP/2.0 200 OK\r\nSynthetic: yes\r\n\r\n'+body
  reordered={k:profile[k] for k in reversed(list(profile))}
  compact=json.dumps(reordered,separators=(',',':')).encode()
  variants=[compact.hex().encode(),compact.hex().upper().encode(),base64.b64encode(compact),
            json.dumps({'wrapped':compact.hex()}).encode(),json.dumps({'wrapped':base64.b64encode(compact).decode()}).encode(),
            ('\n'.join(base64.b64encode(compact).decode()[i:i+32] for i in range(0,len(base64.b64encode(compact)),32))).encode()]
  for i,variant in enumerate(variants):
   with self.subTest(variant=i):
    inspect=namespace['make_profile_inspector'](raw,body,profile)
    self.assertIn('complete-decoded-profile-object',inspect(variant))
  subset={k:profile[k] for k in ['login','id','node_id','type']}
  inspect=namespace['make_profile_inspector'](raw,body,profile)
  self.assertNotIn('complete-decoded-profile-object',inspect(json.dumps(subset).encode()))

if __name__=='__main__':unittest.main()
