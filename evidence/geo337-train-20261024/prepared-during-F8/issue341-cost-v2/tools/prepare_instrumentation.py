"""Reversible diagnostic-only source generation. Never compiles or edits a checkout."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).hexdigest()
header='''
uint64_t bench_shadow_iterations,bench_active_initializations,bench_active_reads;
uint64_t bench_active_deletions,bench_memmove_calls,bench_memmove_bytes,bench_compaction_copies;
uint64_t bench_orders_indexed,bench_orders_unique,bench_admitted,bench_indexed_calls;
static void *bench_move(void *destination,const void *source,size_t bytes)
{++bench_memmove_calls;bench_memmove_bytes+=bytes;return memmove(destination,source,bytes);}
'''
rows=[]
for name in ('fixed','withdrawn','restored'):
 raw=(P/(name+'.c')).read_bytes();s=raw.decode();edits=[]
 def replace(a,b):
  global s
  if s.count(a)!=1:raise ValueError((name,'exact anchor',a,s.count(a)))
  s=s.replace(a,b);edits.append([a,b])
 replace('#include <string.h>\n','#include <string.h>\n'+header)
 replace('ContactOrderIndex orders;contact_order_index(world,&orders);','ContactOrderIndex orders;contact_order_index(world,&orders);\n    bench_orders_indexed=orders.indexed;bench_orders_unique=orders.unique;bench_admitted=count;')
 replace('    ContactFaceIndex index;contact_member_index_sort(world,orders,out,count,first,&index);','    ++bench_indexed_calls;ContactFaceIndex index;contact_member_index_sort(world,orders,out,count,first,&index);')
 replace('for(size_t j=0;j<count&&!duplicate;++j){','for(size_t j=0;j<count&&!duplicate;++j){++bench_shadow_iterations;')
 replace('memmove(out+i,out+i+1,(count-i-1)*sizeof *out)','bench_move(out+i,out+i+1,(count-i-1)*sizeof *out)')
 replace('for(size_t i=0;i<count;++i)active[i]=true;','for(size_t i=0;i<count;++i){++bench_active_initializations;active[i]=true;}')
 replace('if(active[i]){if(write!=i)','if((++bench_active_reads,active[i])){if(write!=i)')
 replace('if(write!=i)out[write]=out[i];','if(write!=i){++bench_compaction_copies;out[write]=out[i];}')
 replace('active[i]=false;--*remaining;','active[i]=false;++bench_active_deletions;--*remaining;')
 if name!='withdrawn':
  replace('if(compact&&!active[j])continue;','if(compact&&(++bench_active_reads,!active[j]))continue;')
  replace('active[i]=false;--remaining;++i;','active[i]=false;++bench_active_deletions;--remaining;++i;')
 reverse=s
 for a,b in reversed(edits):
  if reverse.count(b)!=1:raise ValueError('ambiguous reverse')
  reverse=reverse.replace(b,a)
 if reverse.encode()!=raw:raise ValueError('roundtrip changed original')
 dest=P/(name+'-diagnostic.c');dest.write_text(s)
 rows.append(dict(name=name,source_sha256=H(raw),diagnostic_sha256=H(dest.read_bytes()),roundtrip_exact=True,edits=edits))
(P/'INSTRUMENTATION.json').write_text(json.dumps(dict(variants=rows,C_executed=False,performance_executed=False),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(exit=0,variants=len(rows),C_executed=False)))
