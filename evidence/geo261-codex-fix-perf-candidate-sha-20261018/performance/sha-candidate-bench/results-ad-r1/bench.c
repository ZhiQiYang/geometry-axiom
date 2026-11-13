/* 外部量測：原產品 unity/factory，沒有替換 SHA、bind 或 publish。 */
#define _POSIX_C_SOURCE 200809L
#include <time.h>
#include <errno.h>
#ifdef _WIN32
#undef _WIN32
#endif
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_bridge_main
#include "geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT

typedef struct { double wall,cpu; } BenchTime;
static void bench_require(bool value,const char *label)
{if(!value){fprintf(stderr,"BENCH_ASSERT:%s\n",label);exit(70);}}
static double bench_clock(clockid_t id)
{
    struct timespec t;bench_require(clock_gettime(id,&t)==0,"clock_gettime");
    return (double)t.tv_sec+(double)t.tv_nsec/1e9;
}
static BenchTime bench_start(void)
{BenchTime t={bench_clock(CLOCK_MONOTONIC),bench_clock(CLOCK_PROCESS_CPUTIME_ID)};return t;}
static BenchTime bench_stop(BenchTime start)
{
    double cpu=bench_clock(CLOCK_PROCESS_CPUTIME_ID),wall=bench_clock(CLOCK_MONOTONIC);
    BenchTime delta={wall-start.wall,cpu-start.cpu};return delta;
}
static size_t bench_count(const char *text)
{
    char *end;errno=0;unsigned long n=strtoul(text,&end,10);
    bench_require(!errno&&*text&&!*end&&n>0&&n<=100000,"positive-count-1-to-100000");return (size_t)n;
}
static void bench_time(const char *name,BenchTime t)
{printf("\"%s\":{\"wall_s\":%.9f,\"process_cpu_s\":%.9f}",name,t.wall,t.cpu);}

static void bench_sizes(void)
{
    printf("{\"kind\":\"sizes\",\"world_bytes\":%zu,\"version_store_bytes\":%zu,\"bindings\":[",sizeof(World),sizeof g_world.geo.version_store);
    bool first=true;
#define BENCH_SIZE(field) do{if(!first)putchar(',');first=false;printf("{\"name\":\"core." #field "\",\"offset\":%zu,\"bytes\":%zu}",offsetof(World,geo)+offsetof(GeoDocument,field),sizeof g_world.geo.field);}while(0)
    BENCH_SIZE(parameters);BENCH_SIZE(named_values);BENCH_SIZE(datum_planes);
    BENCH_SIZE(guide_lines);BENCH_SIZE(region_data);BENCH_SIZE(placement_data);
    BENCH_SIZE(grid_store);BENCH_SIZE(version_store);BENCH_SIZE(enclosures);
#undef BENCH_SIZE
    puts("]}");
}
static void bench_sha(const char *kind,const char *expected,size_t warmup,size_t repeat)
{
    size_t bytes=!strcmp(kind,"world")?sizeof(World):sizeof g_world.geo.version_store;
    bench_require(!strcmp(kind,"world")||!strcmp(kind,"version_store"),"sha-payload-kind");
    bench_require(strlen(expected)==64,"independent-expected-digest-length");
    unsigned char *payload=malloc(bytes);BenchTime *times=calloc(repeat,sizeof *times);
    bench_require(payload&&times,"sha-allocation");
    /* 與 Python 獨立 hashlib fixture 相同的公開 byte 公式。 */
    for(size_t i=0;i<bytes;++i)payload[i]=(unsigned char)((i*131u+17u)&255u);
    char actual[65];
    void (*volatile hash_call)(const void *,size_t,char[65])=geo_sha256;
    for(size_t i=0;i<warmup+repeat;++i){
        BenchTime start=bench_start();hash_call(payload,bytes,actual);BenchTime delta=bench_stop(start);
        /* 每次真正結果都核對；比對與 JSON 輸出在 SHA 計時之外。 */
        bench_require(!strcmp(actual,expected),"sha-hashlib-digest");
        if(i>=warmup)times[i-warmup]=delta;
    }
    for(size_t i=0;i<bytes;++i)bench_require(payload[i]==(unsigned char)((i*131u+17u)&255u),"sha-input-unchanged");
    for(size_t i=0;i<repeat;++i){
        printf("{\"kind\":\"sha\",\"payload\":\"%s\",\"iteration\":%zu,\"bytes\":%zu,\"digest\":\"%s\",",kind,i,bytes,actual);
        bench_time("sha",times[i]);puts("}");
    }
    free(times);free(payload);
}
static void bench_bindings(AppWorldCandidate *owner)
{
    GeoCandidate *core=app_candidate_core(owner->control);size_t i=0;
    bench_require(core&&core->binding_count==9,"factory-nine-real-bindings");
#define BENCH_BIND(field) do{const GeoCandidateBinding *b=&core->bindings[i++];bench_require(!strcmp(b->name,"core." #field)&&b->before==&owner->before.geo.field&&b->current==&owner->after.geo.field&&b->size==sizeof owner->after.geo.field,"factory-binding-name-pointer-size");}while(0)
    BENCH_BIND(parameters);BENCH_BIND(named_values);BENCH_BIND(datum_planes);
    BENCH_BIND(guide_lines);BENCH_BIND(region_data);BENCH_BIND(placement_data);
    BENCH_BIND(grid_store);BENCH_BIND(version_store);BENCH_BIND(enclosures);
#undef BENCH_BIND
}
static bool bench_noop(void *after,GeoEvalContext *sources,void *opaque)
{
    AppWorldCandidate *owner=opaque;
    return after==&owner->after&&sources==geo_candidate_sources(app_candidate_core(owner->control));
}
static void bench_candidate(const char *scene,size_t warmup,size_t repeat)
{
    /* 既有 product harness 的真 scene 初始化，完全排除於候選計時之外。 */
    memset(&g_world,0,sizeof g_world);g_definition_revision=0;
    bench_require(parse_scene_file(scene,&g_world),"real-scene-parse");
    history_clear();g_preview.ready=false;
    World *original=malloc(sizeof *original);bench_require(original!=NULL,"original-world-memory");
    memcpy(original,&g_world,sizeof *original);
    for(size_t i=0;i<warmup+repeat;++i){
        uint64_t revision=g_definition_revision;
        BenchTime whole_start=bench_start(),start=bench_start();
        AppWorldCandidate *owner=app_world_candidate_create(&g_world);
        BenchTime create=bench_stop(start);bench_require(owner!=NULL,"real-factory-create");
        bench_bindings(owner);GeoCandidate *core=app_candidate_core(owner->control);
        bench_require(geo_candidate_state(core)==GEO_CANDIDATE_OPEN&&
            !memcmp(&owner->before,original,sizeof *original)&&!memcmp(&owner->after,original,sizeof *original),"factory-complete-copies");
        start=bench_start();GeoCandidateStatus evaluated=app_world_candidate_evaluate(owner,bench_noop,owner);
        BenchTime evaluate=bench_stop(start);
        bench_require(evaluated==GEO_CANDIDATE_OK&&geo_candidate_state(core)==GEO_CANDIDATE_EVALUATED&&
            geo_candidate_evaluation_generation(core)==1,"real-noop-evaluation-verdict");
        bench_require(geo_eval_provider_count(geo_candidate_sources(core))==0&&geo_eval_node_count(geo_candidate_sources(core))==0,"noop-has-no-geometry-provider-work");
        start=bench_start();bool sealed=app_world_candidate_seal(owner);BenchTime seal=bench_stop(start);
        bench_require(sealed&&geo_candidate_state(core)==GEO_CANDIDATE_SEALED&&geo_eval_is_sealed(geo_candidate_sources(core)),"real-seal-verdict");
        start=bench_start();bool published=app_world_candidate_publish(owner,&g_world,false);BenchTime publish=bench_stop(start);
        bench_require(published&&geo_candidate_state(core)==GEO_CANDIDATE_PUBLISHED&&
            geo_candidate_evaluation_generation(core)==1&&g_definition_revision==revision&&
            !memcmp(&g_world,original,sizeof *original),"one-real-complete-root-publication");
        start=bench_start();app_world_candidate_destroy(owner);BenchTime destroy=bench_stop(start);
        BenchTime whole=bench_stop(whole_start);
        /* 每個物件只經過上方一次 publish；不替換 callback、不使用計數器。 */
        if(i>=warmup){
            printf("{\"kind\":\"candidate\",\"iteration\":%zu,\"bindings\":9,\"evaluation_generation\":1,\"published\":true,",i-warmup);
            bench_time("create_and_9_bind",create);putchar(',');bench_time("noop_evaluate",evaluate);putchar(',');
            bench_time("seal",seal);putchar(',');bench_time("publish",publish);putchar(',');bench_time("destroy",destroy);putchar(',');
            bench_time("lifecycle_including_harness_checks",whole);puts("}");
        }
    }
    bench_require(!memcmp(&g_world,original,sizeof *original),"all-noop-candidates-preserve-world");free(original);
}
int main(int argc,char **argv)
{
    if(argc==2&&!strcmp(argv[1],"sizes")){bench_sizes();return 0;}
    if(argc==6&&!strcmp(argv[1],"sha")){bench_sha(argv[2],argv[3],bench_count(argv[4]),bench_count(argv[5]));return 0;}
    if(argc==5&&!strcmp(argv[1],"candidate")){bench_candidate(argv[2],bench_count(argv[3]),bench_count(argv[4]));return 0;}
    fprintf(stderr,"用法: bench sizes | sha world|version_store expected warmup repeats | candidate scene warmup repeats\n");return 2;
}
