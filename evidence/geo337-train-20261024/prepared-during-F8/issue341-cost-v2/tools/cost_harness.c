#define _POSIX_C_SOURCE 200809L
#include "contact_world.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#define CHECK(tag,x) do{if(!(x)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
#ifdef CONTACT_COST_DIAGNOSTICS
extern uint64_t bench_shadow_iterations,bench_active_initializations,bench_active_reads;
extern uint64_t bench_active_deletions,bench_memmove_calls,bench_memmove_bytes,bench_compaction_copies;
extern uint64_t bench_orders_indexed,bench_orders_unique,bench_admitted,bench_indexed_calls;
#endif
static uint64_t ns(struct timespec t){return (uint64_t)t.tv_sec*UINT64_C(1000000000)+(uint64_t)t.tv_nsec;}
static int face_matches(const WoodStopFace *f,uint32_t id,int edge,GeoCoord at)
{return f->kind==WOOD_STOP_MEMBER_SIDE&&f->boundary_id==0&&f->timber_id==id&&f->hole_index==-1&&f->edge_index==edge&&f->fixity==WOOD_STOP_FIXED&&f->fixed==at&&f->lo==0&&f->hi==27;}
int main(int argc,char **argv)
{
    if(argc!=3)return 2;
    char *end=NULL;unsigned long supplied=strtoul(argv[2],&end,10);
    if(!*argv[2]||*end||supplied<2||supplied>WOOD_CONTACT_FACE_CAPACITY)return 2;
    size_t n=(size_t)supplied,cap=n*2;
    bool unique=!strncmp(argv[1],"unique-",7);
    const char *kind=unique?argv[1]+7:argv[1];
    bool dense=!strcmp(kind,"dense")||!strcmp(kind,"fallback-dense");
    bool few=!strcmp(kind,"few");
    bool fallback=!strcmp(kind,"fallback-none")||!strcmp(kind,"fallback-dense");
    if(strcmp(kind,"none")&&!dense&&!few&&!fallback)return 2;
    if(unique&&fallback)return 2;
    if(fallback&&n!=WOOD_CONTACT_FACE_CAPACITY/2+1)return 2;
    if(!fallback&&n>WOOD_CONTACT_MEMBER_CAPACITY)return 2;
    WoodMember *members=calloc(n,sizeof *members);
    WoodContactMemberFact *facts=calloc(n,sizeof *facts);
    WoodStopFace *out=malloc((cap+1)*sizeof *out);
    if(!members||!facts||!out){free(members);free(facts);free(out);return 2;}
    for(size_t i=0;i<n;++i){
        members[i].id=unique?(uint32_t)(i+1):42;members[i].role=WOOD_MEMBER_ROLE_PRIMARY;
        members[i].cut_priority=2;members[i].placed=true;
        size_t coordinate=dense?0:(few&&i==n-1?n-2:i);
        GeoCoord lo=(GeoCoord)coordinate*200;
        facts[i]=(WoodContactMemberFact){&members[i],7,(uint64_t)(i+1),false,true,{lo,0,lo+100,27}};
    }
    memset(out,0xa5,(cap+1)*sizeof *out);unsigned char sentinel[sizeof *out];memcpy(sentinel,out+cap,sizeof sentinel);
    WoodContactWorld world={.placement_id=7,.members=facts,.member_count=n};
    struct timespec cb,ce,wb,we,res_cpu,res_wall;
    if(clock_getres(CLOCK_PROCESS_CPUTIME_ID,&res_cpu)||clock_getres(CLOCK_MONOTONIC,&res_wall)||
       clock_gettime(CLOCK_MONOTONIC,&wb)||clock_gettime(CLOCK_PROCESS_CPUTIME_ID,&cb))return 2;
    size_t got=wood_contact_collect_stops(&world,false,NULL,out,cap);
    if(clock_gettime(CLOCK_PROCESS_CPUTIME_ID,&ce)||clock_gettime(CLOCK_MONOTONIC,&we))return 2;
    size_t wanted=dense?2:(few?(n-1)*2:n*2);
    CHECK("whole-compaction-count",got==wanted);
    CHECK("whole-compaction-caller-tail",!memcmp(sentinel,out+cap,sizeof sentinel));
    for(size_t i=0;i<got/2;++i){
        GeoCoord lo=dense?0:(GeoCoord)i*200;
        CHECK("whole-compaction-ordered-full-face",face_matches(out+i*2,unique?(uint32_t)(i+1):42,0,lo)&&face_matches(out+i*2+1,unique?(uint32_t)(i+1):42,1,lo+100));
    }
#ifdef CONTACT_COST_DIAGNOSTICS
    CHECK("observed-admitted-count",bench_admitted==cap);
    CHECK("observed-indexed-path",bench_indexed_calls==(unique?1u:0u));
    CHECK("observed-order-index-capacity",bench_orders_indexed==(n<=WOOD_CONTACT_MEMBER_CAPACITY));
    if(n<=WOOD_CONTACT_MEMBER_CAPACITY)CHECK("observed-id-uniqueness",bench_orders_unique==(uint64_t)unique);
    printf("PATH orders_indexed=%"PRIu64" orders_unique=%"PRIu64" admitted=%"PRIu64" indexed_calls=%"PRIu64"\n",bench_orders_indexed,bench_orders_unique,bench_admitted,bench_indexed_calls);
    puts("MODE diagnostic=true performance_sample=false");
#else
    puts("MODE diagnostic=false performance_sample=true");
#endif
    printf("META case=%s n=%zu admitted=%zu capacity=%d fallback=%d face_size=%zu\n",argv[1],n,cap,WOOD_CONTACT_FACE_CAPACITY,(int)fallback,sizeof *out);
    printf("TIME cpu_ns=%"PRIu64" wall_ns=%"PRIu64" cpu_resolution_ns=%"PRIu64" wall_resolution_ns=%"PRIu64"\n",ns(ce)-ns(cb),ns(we)-ns(wb),ns(res_cpu),ns(res_wall));
#ifdef CONTACT_COST_DIAGNOSTICS
    printf("WORK shadow_iterations=%"PRIu64" active_initializations=%"PRIu64" active_reads=%"PRIu64" active_deletions=%"PRIu64" memmove_calls=%"PRIu64" memmove_bytes=%"PRIu64" compaction_copies=%"PRIu64"\n",bench_shadow_iterations,bench_active_initializations,bench_active_reads,bench_active_deletions,bench_memmove_calls,bench_memmove_bytes,bench_compaction_copies);
#endif
    for(size_t i=0;i<got;++i){const WoodStopFace *f=out+i;
        printf("FACE %d %"PRIu32" %"PRIu32" %d %d %d %"PRId64" %"PRId64" %"PRId64"\n",f->kind,f->boundary_id,f->timber_id,f->hole_index,f->edge_index,f->fixity,(int64_t)f->fixed,(int64_t)f->lo,(int64_t)f->hi);
    }
    free(out);free(facts);free(members);return 0;
}
