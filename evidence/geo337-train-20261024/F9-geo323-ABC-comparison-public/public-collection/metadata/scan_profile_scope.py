"""Read selected original sources; report full-profile copies by path/hash, never values."""
from pathlib import Path
import base64,gzip,hashlib,json,os,re,stat,time

HERE=Path(__file__).resolve().parent
PREP=Path('/workspace/geo323-F9-owner-comparison-collection-preparation-20261025')
RAW=Path('/workspace/geo323-F9-owner-compare-once-20261025-r1')
PROFILE=RAW/'tools-frozen/authority/connected-user/subcommands/000001/stdout.bin'
IPIN='1ab22f16962fb861204932c4c46ff379c9c1e6144d9b7006999ded216a0f416f'
PPIN='14f6ddb9cb1358f93125d86f3dc8b716400fa16e2a62e9d6b9007d5e35745143'
PROFILE_PIN='b8939b00b88600ac7c4e96dcb45f38d75ffa5b5eddf7a3fa3f24d8109f6d9f29'
F='4f8a794f4167c3562eb182045102e86e9e37cca9'

def h(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def save(name,x):
 p=HERE/name
 if p.exists():raise RuntimeError('Do not overwrite profile scope evidence: '+name)
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def must(v,msg):
 if not v:raise RuntimeError(msg)
def body_of(b):
 for sep in (b'\r\n\r\n',b'\n\n'):
  if sep in b:
   candidate=b.split(sep,1)[1]
   try:return candidate,json.loads(candidate)
   except (ValueError,UnicodeError):pass
 return b,json.loads(b)

def make_profile_inspector(profile_raw,profile_body,profile):
 keys=set(profile)
 target_variants=[('complete-http-raw',profile_raw),('complete-json-body-raw',profile_body),
                  ('complete-http-hex',profile_raw.hex().encode()),('complete-body-hex',profile_body.hex().encode()),
                  ('complete-http-base64',base64.b64encode(profile_raw)),('complete-body-base64',base64.b64encode(profile_body))]
 decoder=json.JSONDecoder()
 def inspect(b):
  reasons=set()
  for label,target in target_variants:
   if target and target in b:reasons.add(label)
  try:text=b.decode('utf-8')
  except UnicodeError:text=b.decode('utf-8',errors='replace')
  visited=set()
  def visit(node,depth=0):
   if depth>100:raise RuntimeError('Nested representation too deep; no silent skip')
   if isinstance(node,dict):
    if keys<=set(node) and all(node[k]==profile[k] for k in keys):reasons.add('complete-decoded-profile-object')
    for v in node.values():visit(v,depth+1)
   elif isinstance(node,list):
    for v in node:visit(v,depth+1)
   elif isinstance(node,str):
    inspect_text(node,depth+1)
  def inspect_text(t,depth=0):
   if depth>100:raise RuntimeError("Nested decoded representation too deep; no silent skip")
   if t in visited:return
   visited.add(t)
   encoded=t.encode('utf-8',errors='replace')
   for label,target in target_variants:
    if target and target in encoded:reasons.add('decoded-string:'+label)
   candidates=[t]
   for sep in ('\r\n\r\n','\n\n'):
    if sep in t:candidates.append(t.split(sep,1)[1])
   parsed=False
   for c in candidates:
    try:node=json.loads(c)
    except (ValueError,UnicodeError):continue
    parsed=True;visit(node,depth+1)
   # Free text or JSONL can contain a complete JSON object without being one JSON document.
   if not parsed and ('"login"' in t or '\\"login\\"' in t or '\\u006c' in t):
    for match in re.finditer(r'\{',t):
     try:node,_=decoder.raw_decode(t,match.start())
     except ValueError:continue
     visit(node,depth+1)
   # Recognize common encoded complete responses even if a string adds whitespace.
   compact=''.join(t.split())
   if len(compact)>=2 and re.fullmatch('[0-9a-fA-F]+',compact):
    try:
     decoded=bytes.fromhex(compact)
     if decoded in (profile_raw,profile_body):reasons.add('complete-profile-hex-string')
     inspect_text(decoded.decode('utf-8'),depth+1)  # FOLLOW_DECODED_PROFILE
    except (ValueError,UnicodeError):pass
   if len(compact)>=4 and re.fullmatch('[A-Za-z0-9+/]*={0,2}',compact):
    try:
     decoded=base64.b64decode(compact,validate=True)
     if decoded in (profile_raw,profile_body):reasons.add('complete-profile-base64-string')
     inspect_text(decoded.decode('utf-8'),depth+1)  # FOLLOW_DECODED_PROFILE
    except (ValueError,UnicodeError):pass
  inspect_text(text)
  return reasons
 return inspect

def main():
 invraw=(PREP/'INVENTORY.json').read_bytes();partsraw=(PREP/'PARTS.json').read_bytes()
 must(h(invraw)==IPIN and h(partsraw)==PPIN,'Private inventory or part plan changed')
 inv=json.loads(invraw);parts=json.loads(partsraw);profile_raw=PROFILE.read_bytes()
 must(h(profile_raw)==PROFILE_PIN,'Known private GET/user raw changed')
 profile_body,profile=body_of(profile_raw);must(isinstance(profile,dict),'Profile body is not an object')
 keys=set(profile);rootmap=inv['roots'];member_part={n:p['part'] for p in parts for n in p['members_exact']}
 inspect=make_profile_inspector(profile_raw,profile_body,profile)
 exclusions=[];counts={'regular_files':0,'symlinks':0,'source_bytes':0,'gzip_files':0,'gzip_decoded_bytes':0}
 selected=[];formal=[];safe_identity_member=None
 for ordinal,row in enumerate(inv['records']):
  ri,rel,kind,size,digest,st,target=row;root=rootmap[ri];path=Path(root['source_root'])/rel;name=root['prefix']+'/'+rel
  actual=path.lstat();must([actual.st_dev,actual.st_ino,actual.st_mode,actual.st_size,actual.st_mtime_ns,actual.st_nlink]==st,'Source stat changed: '+name)
  if kind=='symlink':
   must(os.readlink(path)==target and h(os.fsencode(target))==digest,'Literal symlink changed')
   counts['symlinks']+=1;selected.append(ordinal);continue
  must(kind=='regular' and stat.S_ISREG(actual.st_mode),'Unknown source kind')
  b=path.read_bytes();must(len(b)==size and h(b)==digest,'Source raw/hash changed: '+name)
  counts['regular_files']+=1;counts['source_bytes']+=len(b);reasons=inspect(b)
  if b.startswith(b'\x1f\x8b'):
   decoded=gzip.decompress(b);counts['gzip_files']+=1;counts['gzip_decoded_bytes']+=len(decoded)
   reasons.update('gzip:'+reason for reason in inspect(decoded))
  if reasons:
   exclusions.append({'private_inventory_index':ordinal,'member':name,'source_path':str(path),'bytes':size,
                      'sha256':digest,'detections':sorted(reasons),'reason':'Unrelated full GET /user profile response is auxiliary account authentication data; retain cloud-only under E70 scope.',
                      'private_archive_part':member_part[name],
                      'private_archive_root':'/dev/shm/geometry-axiom-geo337-20261025/geo323-F9-owner-comparison-terminal-package-shm-v2-20261025',
                      'private_original_retained':True})
  else:selected.append(ordinal)
  if name.startswith('comparison/invocation/commands/'):
   formal.append((ordinal,name,digest,size))
  if name=='comparison/tools-frozen/authority/IDENTITY_AND_ORIGINAL_COMMENT.json':safe_identity_member={'private_inventory_index':ordinal,'member':name,'sha256':digest,'bytes':size}
 selected_set=set(selected);must(all(i in selected_set for i,_,_,_ in formal),'Attempted exclusion of formal comparison command raw')
 must(safe_identity_member and safe_identity_member['private_inventory_index'] in selected_set,'Safe identity witness excluded')
 commands=load(RAW/'invocation/commands/commands.json')
 must(len(commands)==712 and sum(row['command'][0]=='git' for row in commands)==12,'Formal original command scope changed')
 must(len(commands)-12==700,'Original 700 O2/trace commands incomplete')
 retained_streams=sum(name.endswith(('/stdout.bin','/stderr.bin')) for _,name,_,_ in formal)
 must(retained_streams==1424,'Expected 712 complete stdout/stderr pairs')
 excluded_indices={x['private_inventory_index'] for x in exclusions};must(not (selected_set&excluded_indices) and selected_set|excluded_indices==set(range(len(inv['records']))),'Exact public/private partition failed')
 public_names={rootmap[inv['records'][i][0]]['prefix']+'/'+inv['records'][i][1] for i in selected}
 part_delta=[]
 for part in parts:
  excluded=[name for name in part['members_exact'] if name not in public_names]
  part_delta.append({'part':part['part'],'original_members':part['members'],'retained_members':part['members']-len(excluded),
                     'excluded_members':excluded,'action':'REPACK_PUBLIC_PART_REQUIRED' if excluded else 'REUSE_ORIGINAL_ARCHIVE_BYTES_AFTER_PUBLIC_SCOPE_REVIEW'})
 report={'schema':'geo323-full-profile-public-scope-scan/1','exit_code':0,'source_sha':F,'evidence_base':'70d00309d7985db722c339c77331c436d26a7ab1',
         'private_inventory_sha256':IPIN,'private_parts_sha256':PPIN,'scan_counts':counts,'complete_profile_keys':len(keys),
         'known_private_response':{'path':str(PROFILE),'bytes':len(profile_raw),'sha256':PROFILE_PIN,'decoded_body_bytes':len(profile_body),'decoded_body_sha256':h(profile_body)},
         'exclusions':exclusions,'formal_command_count':712,'formal_O2_trace_commands':700,'readonly_git_commands':12,
         'retained_command_streams':retained_streams,'all_formal_command_source_hashes_unchanged':True,'safe_identity_witness':safe_identity_member,
         'archive_repacked':False,'private_archives_modified':False,'profile_values_printed':False,'product_rerun':False,
         'scan_scope':'Every regular source leaf in the fixed 4667-member private publication candidate, plus each gzip decoded payload; not a filesystem-wide private-data scan.',
         'representations':['raw HTTP','raw JSON body','decoded JSON object/subobject/string','hex','base64','gzip payload'],
         'scanner_sha256':h(Path(__file__).read_bytes()),'epoch':time.time()}
 save('PROFILE_SCAN.json',report)
 save('PUBLIC_EXCLUSIONS.json',{'schema':'geo323-public-auxiliary-profile-exclusions/1','source_sha':F,'private_inventory_sha256':IPIN,
       'exclusions':exclusions,'private_complete_archives_retained':True,'no_formal_product_command_stream_excluded':True,
       'disclosure':'All formal comparison observations and command streams remain public candidates. Full unrelated GET /user response is cloud-only; do not claim every API raw payload is public.'})
 save('PUBLIC_INVENTORY_DELTA.json',{'schema':'geo323-public-inventory-selection-delta/1','source_sha':F,
       'private_inventory_path':str(PREP/'INVENTORY.json'),'private_inventory_sha256':IPIN,
       'selected_private_indices':selected,'excluded_private_indices':sorted(excluded_indices),'part_delta':part_delta,
       'selected_members':len(selected),'selected_regular_files':counts['regular_files']-len(exclusions),'selected_symlinks':counts['symlinks'],
       'selected_regular_bytes':counts['source_bytes']-sum(x['bytes'] for x in exclusions),'formal_commands_preserved':712,
       'safe_identity_witness':safe_identity_member,'public_collection_executed':False})
 save('SAFE_AUTHORITY_LOCATOR.json',{'schema':'geo323-public-safe-authority-locator/1','source_sha':F,
       'connected_account_identity':{k:profile[k] for k in ['login','id','node_id','type']},
       'original_full_profile_raw_sha256':PROFILE_PIN,'original_full_profile_raw_bytes':len(profile_raw),
       'safe_original_witness':safe_identity_member,
       'existing_public_proof':'https://github.com/ZhiQiYang/geometry-axiom/tree/c32e70aa2c848f89a0e2e9fd92ed232a4dd27bcc/evidence/geo337-train-20261024/F9-readers-and-verified-decision/',
       'approved_comment':'https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6396611849',
       'approval_source_sha':'405f8c5e1a637a16cbe47470faf5ae1fa02b8676',
       'api_request_and_result_retained':'comparison/tools-frozen/authority/connected-user/subcommands/000001/{request.json,result.json}; stdout raw is the explicitly excluded auxiliary profile.',
       'original_policy_guard_inputs_disclosure':'The executed authority guard and original binding are retained unchanged. The public package intentionally lacks the excluded full-profile input; private originals and their hashes remain available for original full-input replay.'})
 print(json.dumps({'exit_code':0,'regular_files_scanned':counts['regular_files'],'gzip_files_scanned':counts['gzip_files'],
                   'excluded_members':len(exclusions),'excluded_bytes':sum(x['bytes'] for x in exclusions),
                   'affected_parts':[p['part'] for p in part_delta if p['excluded_members']],
                   'formal_commands_retained':712,'profile_values_printed':False}))

if __name__=='__main__':main()
