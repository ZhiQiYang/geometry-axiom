from pathlib import Path
import hashlib,json,re
HERE=Path(__file__).resolve().parent
paths={'R5':Path('/workspace/g337323R5/evidence/gprof-fix-64.stdout'),'R6':Path('/workspace/g337323R6/evidence/gprof-fix-64.stdout')}
def sha(b):return hashlib.sha256(b).hexdigest()
profile={};bindings={}
for label,p in paths.items():
 raw=p.read_bytes();bindings[label]={'path':str(p),'bytes':len(raw),'sha256':sha(raw)};rows={}
 for line in raw.decode().split('Call graph')[0].splitlines():
  m=re.match(r'^\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s*$',line)
  if m:rows[m[7]]={'calls':int(m[4]),'self_seconds':float(m[3])}
 profile[label]=rows
names=['contact_face_plane_compare','contact_face_index_before','contact_face_plane_range','contact_face_index_bounds','contact_face_index_build','contact_face_index_covered','contact_prefix_lo','contact_face_index_insert','contact_order','geo_source_find_node','geo_source_find_edge','geo_source_node','geo_source_index_append']
result={'r5_source':'a22df116c7e9f6b7d074451f1c8052d59e7e4f3e','r6_source':'2bbe54f19b2d19e8a816530f0c4edca950629a34','profile_bindings':bindings,'selected_counts_and_sampling_self_seconds':{n:{k:v.get(n)for k,v in profile.items()}for n in names},'removed_plane_comparisons':profile['R5']['contact_face_plane_compare']['calls']-profile['R6']['contact_face_plane_compare']['calls'],'r6_red':{'N64_main':1.3731562025736295,'N16_base':1.0434575834374764},'source_findings':['contact_face_index_build initializes sorted/maximum/rank/scratch only in the current count range, not the full face capacity.','contact_order_index zeros128 last slots on the64-member line; no full face-index memset exists.','out/rank are unchanged for one index lifetime; no cross-query cache is proposed without a complete invalidation identity.'],'candidate_only':'Use known query rank to narrow the existing prefix binary search: lo=rank+1 for lo<hi, hi=rank for zero/reversed spans. Preserve the original predicate/Fenwick query; prove independently before product changes.','limits':['No new performance run or resampling.','Profile uses original profiling compiler settings; sampling self seconds are not an O2wall verdict.','Reduced call count does not establish why formalwall remains red or guarantee further speedup.','Candidate is preparation only; root prioritizes independent K shadow diagnosis before another formal round.']}
assert result['removed_plane_comparisons']==13189192
(HERE/'R6_W_PROFILE_ANALYSIS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'removed_plane_comparisons':result['removed_plane_comparisons'],'output_sha256':sha((HERE/'R6_W_PROFILE_ANALYSIS.json').read_bytes())}))
