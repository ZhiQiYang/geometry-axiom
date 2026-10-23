/* The fixture expands this include, changing only the old main declaration
 * and its bridge include path. Every original lifecycle assertion is retained. */
#define app_world_candidate_publish d_setup_world_candidate_publish
#include "geo261_candidate_product_harness.c"
#undef app_world_candidate_publish

static size_t host_calls,state_calls,provider_calls,bind_calls;
typedef struct {
    const char *name;
    const void *before;
    void *current;
    size_t size;
    GeoCandidateStatus status;
} ObservedBinding;
static ObservedBinding bindings[9];

/* These proxies only observe real inputs and call the original implementation. */
void hk_product_host_sha(const void *bytes,size_t size,char out[65])
{++host_calls;geo_sha256(bytes,size,out);}
void hk_product_state_sha(const void *bytes,size_t size,char out[65])
{++state_calls;geo_sha256(bytes,size,out);}
void hk_product_provider_sha(const void *bytes,size_t size,char out[65])
{++provider_calls;geo_sha256(bytes,size,out);}
GeoCandidateStatus hk_product_bind(GeoCandidate *core,const char *name,const void *before,void *current,size_t size)
{
    GeoCandidateStatus status=geo_candidate_bind_state(core,name,before,current,size);
    if(bind_calls<9)bindings[bind_calls]=(ObservedBinding){name,before,current,size,status};
    ++bind_calls;return status;
}
static void reset_observation(void)
{host_calls=state_calls=provider_calls=bind_calls=0;memset(bindings,0,sizeof bindings);}

static int factory(void)
{
    memset(&g_world,0,sizeof g_world);reset_observation();
    AppWorldCandidate *owner=app_world_candidate_create(&g_world);
    CHECK(owner,"deferred-product-factory-created");
    CHECK(host_calls==0,"world-factory-skips-host-sha");
    CHECK(state_calls==0,"world-factory-skips-bound-state-sha");
    CHECK(provider_calls==0,"world-factory-no-provider-before-evaluation");
    CHECK(bind_calls==9,"world-factory-nine-bindings");
    size_t index=0;
#define EXPECT_BINDING(field) do { \
    const ObservedBinding *b=&bindings[index++]; \
    CHECK(!strcmp(b->name,"core." #field),"world-factory-binding-name-order"); \
    CHECK(b->before==&owner->before.geo.field&&b->current==&owner->after.geo.field, \
          "world-factory-binding-actual-pointers"); \
    CHECK(b->size==sizeof owner->after.geo.field&&b->status==GEO_CANDIDATE_OK, \
          "world-factory-binding-complete-range"); \
} while(0)
    EXPECT_BINDING(parameters);EXPECT_BINDING(named_values);EXPECT_BINDING(datum_planes);
    EXPECT_BINDING(guide_lines);EXPECT_BINDING(region_data);EXPECT_BINDING(placement_data);
    EXPECT_BINDING(grid_store);EXPECT_BINDING(version_store);EXPECT_BINDING(enclosures);
#undef EXPECT_BINDING
    CHECK(!memcmp(&owner->before,&g_world,sizeof g_world)&&!memcmp(&owner->after,&g_world,sizeof g_world),
          "world-factory-complete-copies");
    app_world_candidate_destroy(owner);return 0;
}
static int real_lifecycle(const char *path)
{
    reset_observation();
    int result=lifecycle(path);if(result)return result;
    CHECK(host_calls==0,"product-lifecycle-skips-host-sha");
    CHECK(state_calls==0,"product-lifecycle-skips-bound-state-sha");
    CHECK(provider_calls>0,"product-lifecycle-keeps-real-provider-sha");
    return 0;
}
static int core_first(const char *path)
{
    CHECK(prepare(path)&&preview(),"deferred-product-preview");
    AppWorldCandidate *owner=g_preview.transaction;
    GeoCandidate *core=app_candidate_core(owner->control);
    unsigned char *bytes=(unsigned char*)&owner->after.geo.named_values;
    unsigned char saved=bytes[sizeof owner->after.geo.named_values-1];
    bytes[sizeof owner->after.geo.named_values-1]^=1;
    reset_observation();
    CHECK(geo_candidate_check(core,g_definition_revision,app_world_provider_stamp())==GEO_CANDIDATE_STATE_CHANGED,
          "product-core-first-rejects-bound-byte");
    CHECK(state_calls==2&&host_calls==0&&provider_calls==0,"product-core-first-real-saved-actual-pair");
    bytes[sizeof owner->after.geo.named_values-1]=saved;reset_observation();
    CHECK(geo_candidate_check(core,g_definition_revision,app_world_provider_stamp())==GEO_CANDIDATE_OK,
          "product-core-first-restored-seal");
    CHECK(state_calls==0&&host_calls==0&&provider_calls==1,"product-core-first-restored-provider-sha");
    CHECK(confirm(),"product-core-first-restored-confirm");
    return 0;
}
/* D uses the real final World publish body inserted by the Python fixture.
 * The original bridge keeps its own same-body spelling for setup/lifecycle. */
static size_t d_host_checks,d_kernel_checks,d_metadata_allocs,d_operation_shas;
static size_t d_equals,d_replaces,d_callbacks;
static unsigned d_fail_metadata;
void d_seen_host_check(void){++d_host_checks;}
void d_seen_kernel_check(void){++d_kernel_checks;}
void d_seen_callback(void){++d_callbacks;}
void *d_metadata_alloc(size_t size)
{
    ++d_metadata_allocs;
    if(d_fail_metadata==3||d_metadata_allocs==d_fail_metadata)return NULL;
    return malloc(size);
}
void d_flip_core_stamp(GeoCandidate *);
void d_flip_source_seal(GeoEvalContext *);
static void d_operation_sha(const void *bytes,size_t size,char out[65])
{++d_operation_shas;geo_sha256(bytes,size,out);}
static bool d_equal(const void *live,const void *before,void *opaque)
{++d_equals;return app_world_candidate_equal(live,before,opaque);}
static void d_replace(void *live,const void *after,void *opaque)
{++d_replaces;app_world_candidate_replace(live,after,opaque);}
#define geo_sha256 d_operation_sha
#define app_world_candidate_equal d_equal
#define app_world_candidate_replace d_replace
/* D_DIRECT_WORLD_PUBLISH */
#undef app_world_candidate_replace
#undef app_world_candidate_equal
#undef geo_sha256
static void d_reset(void)
{
    reset_observation();d_host_checks=d_kernel_checks=d_metadata_allocs=d_operation_shas=0;
    d_equals=d_replaces=d_callbacks=0;d_fail_metadata=0;
}
static int direct_success(const char *path,bool preserve,bool cost)
{
    CHECK(prepare(path)&&preview(),"publish-preview");
    AppWorldCandidate *owner=g_preview.transaction;GeoCandidate *core=app_candidate_core(owner->control);
    GeoEvalContext *sources=geo_candidate_sources(core);
    uint64_t generation=geo_candidate_evaluation_generation(core),revision=g_definition_revision;
    CHECK(app_world_candidate_current(owner,&g_world),"publish-current-before-reset");
    CHECK(owner->after.app.canvas_pos_count==0,"publish-fixture-no-saved-presentation");
    CHECK(line("canvas-pos placement 1 17 29")&&g_world.app.canvas_pos_count==1,"publish-live-presentation");
    World *expected=malloc(sizeof *expected);CHECK(expected,"publish-memory");*expected=owner->after;
    if(preserve){expected->app.canvas_pos_count=1;expected->app.canvas_pos[0]=g_world.app.canvas_pos[0];}
    d_reset();
    CHECK(app_world_candidate_publish(owner,&g_world,preserve),"publish-direct-success");
    if(cost){
        /* These are real body entries, the real provider malloc and SHA calls. */
        CHECK(d_host_checks==1,"publish-single-host-check");
        CHECK(d_kernel_checks==2,"publish-two-kernel-checks");
        CHECK(d_metadata_allocs==2&&provider_calls==2,"publish-two-provider-checks");
        CHECK(d_operation_shas==1,"publish-one-operation-sha");
        CHECK(d_equals==1,"publish-one-live-equality");
        CHECK(host_calls==0&&state_calls==0,"publish-keeps-hk-deferred-hits");
    }
    CHECK(d_replaces==1&&d_callbacks==0,"publish-once-without-provider-callbacks");
    CHECK(!memcmp(expected,&g_world,sizeof g_world),"publish-complete-root-and-presentation-policy");
    CHECK(geo_candidate_state(core)==GEO_CANDIDATE_PUBLISHED&&geo_candidate_sources(core)==sources&&
          geo_candidate_evaluation_generation(core)==generation&&g_definition_revision==revision,
          "publish-same-owner-no-evaluation-or-command-revision");
    CHECK(!app_world_candidate_publish(owner,&g_world,preserve),"publish-second-rejected");
    CHECK(d_replaces==1&&!memcmp(expected,&g_world,sizeof g_world),"publish-second-root-unchanged");
    free(expected);return 0;
}
static int direct_tamper(const char *path,const char *which)
{
    CHECK(prepare(path)&&preview(),"publish-preview");
    AppWorldCandidate *owner=g_preview.transaction;GeoCandidate *core=app_candidate_core(owner->control);
    GeoEvalContext *sources=geo_candidate_sources(core);
    World *live=malloc(sizeof *live);CHECK(live,"publish-memory");*live=g_world;
    unsigned char *byte=NULL,*mirror=NULL;bool operation=false,host_after=false,stamp=false,seal=false;
    bool revision=!strcmp(which,"revision");
    if(!strcmp(which,"operation-keyed")){owner->operation.boundary_keyed=!owner->operation.boundary_keyed;operation=true;}
    else if(!strcmp(which,"operation-id")){owner->operation.boundary_id^=1;operation=true;}
    else if(!strcmp(which,"operation-seal")){byte=(unsigned char*)&owner->operation_seal[0];operation=true;}
    else if(!strcmp(which,"host-after")){byte=(unsigned char*)&owner->after.wood.timbers[0].size_a;host_after=true;}
    else if(!strcmp(which,"host-before")){
        byte=(unsigned char*)&owner->before.wood.timbers[0].size_a;mirror=(unsigned char*)&g_world.wood.timbers[0].size_a;
    }else if(!strcmp(which,"bound"))byte=(unsigned char*)&owner->after.geo.named_values+sizeof owner->after.geo.named_values-1;
    else if(!strcmp(which,"live"))byte=(unsigned char*)&g_world.wood.timbers[0].size_a;
    else if(!strcmp(which,"provider")){
        const GeoSourceProvider *provider=geo_eval_provider_at(sources,0);
        CHECK(provider&&provider->implementation_fingerprint&&*provider->implementation_fingerprint,"publish-real-provider");
        /* source.c owns this allocated string; only one mutable byte changes. */
        byte=(unsigned char*)provider->implementation_fingerprint;
    }else if(!strcmp(which,"stamp")){d_flip_core_stamp(core);stamp=true;}
    else if(!strcmp(which,"source-seal")){d_flip_source_seal(sources);seal=true;}
    else CHECK(revision||operation,"publish-known-tamper-case");
    if(byte)*byte^=1;
    if(mirror)*mirror^=1;
    if(revision)++g_definition_revision;
    /* Before-only tamper mirrors live: equality cannot be the rejecting guard. */
    if(mirror)CHECK(world_definitions_equal(&g_world,&owner->before),"publish-before-mirror-equal");
    if(operation)CHECK(app_candidate_check(owner->control,&g_world,g_definition_revision,app_world_provider_stamp(),
                                         app_world_candidate_equal,NULL)==GEO_CANDIDATE_OK,
                       "publish-operation-only-other-guards-valid");
    *live=g_world;d_reset();
    bool accepted=app_world_candidate_publish(owner,&g_world,false);
    if(operation)CHECK(!accepted,"publish-operation-tamper-rejected");
    else if(host_after)CHECK(!accepted,"publish-host-after-tamper-rejected");
    else CHECK(!accepted,"publish-direct-tamper-rejected");
    CHECK(d_replaces==0&&d_callbacks==0&&!memcmp(live,&g_world,sizeof g_world),"publish-rejected-root-unchanged");
    CHECK(geo_candidate_state(core)==GEO_CANDIDATE_SEALED,"publish-rejected-owner-still-sealed");
    if(byte)*byte^=1;
    if(mirror)*mirror^=1;
    if(revision)--g_definition_revision;
    if(stamp)d_flip_core_stamp(core);
    if(seal)d_flip_source_seal(sources);
    if(!strcmp(which,"operation-keyed"))owner->operation.boundary_keyed=!owner->operation.boundary_keyed;
    if(!strcmp(which,"operation-id"))owner->operation.boundary_id^=1;
    d_reset();
    CHECK(app_world_candidate_publish(owner,&g_world,true),"publish-restored-same-owner-succeeds");
    CHECK(d_replaces==1&&geo_candidate_state(core)==GEO_CANDIDATE_PUBLISHED,"publish-restored-single-root");
    free(live);return 0;
}
static int direct_terminal(const char *path,const char *which)
{
    CHECK(prepare(path)&&preview(),"publish-preview");
    AppWorldCandidate *owner=g_preview.transaction;GeoCandidate *core=app_candidate_core(owner->control);
    World *live=malloc(sizeof *live);CHECK(live,"publish-memory");*live=g_world;
    bool fresh=!strcmp(which,"unsealed");
    if(fresh){
        owner=app_world_candidate_create(&g_world);CHECK(owner,"publish-unsealed-created");
        core=app_candidate_core(owner->control);
        /* Pass the operation gate so this case really reaches the H state gate. */
        geo_sha256(&owner->operation,sizeof owner->operation,owner->operation_seal);
    }else if(!strcmp(which,"discarded"))app_candidate_discard(owner->control);
    else CHECK(app_candidate_reopen(owner->control,&g_world,g_definition_revision,app_world_provider_stamp(),
                                   app_world_candidate_equal,NULL)==GEO_CANDIDATE_OK,"publish-reopened");
    GeoCandidateState state=geo_candidate_state(core);d_reset();
    CHECK(!app_world_candidate_publish(owner,&g_world,false),"publish-terminal-rejected");
    CHECK(d_host_checks==1&&d_replaces==0&&!memcmp(live,&g_world,sizeof g_world)&&geo_candidate_state(core)==state,
          "publish-terminal-state-and-root-unchanged");
    if(fresh)app_world_candidate_destroy(owner);
    free(live);return 0;
}
static int direct_oom(const char *path,unsigned fail)
{
    CHECK(prepare(path)&&preview(),"publish-preview");
    AppWorldCandidate *owner=g_preview.transaction;GeoCandidate *core=app_candidate_core(owner->control);
    World *live=malloc(sizeof *live);CHECK(live,"publish-memory");*live=g_world;
    uint64_t generation=geo_candidate_evaluation_generation(core);d_reset();d_fail_metadata=fail;
    CHECK(!app_world_candidate_publish(owner,&g_world,false),"publish-provider-oom-rejected");
    CHECK(d_metadata_allocs==(fail==2?2:1),"publish-provider-oom-exact-allocation");
    CHECK(d_replaces==0&&!memcmp(live,&g_world,sizeof g_world)&&geo_candidate_state(core)==GEO_CANDIDATE_SEALED,
          "publish-provider-oom-atomic");
    if(fail==3){
        CHECK(!app_world_candidate_publish(owner,&g_world,true),"publish-persistent-oom-rejected");
        CHECK(d_replaces==0&&!memcmp(live,&g_world,sizeof g_world),"publish-persistent-oom-atomic");
    }
    d_reset();
    CHECK(app_world_candidate_publish(owner,&g_world,false),"publish-oom-same-owner-retry");
    CHECK(d_replaces==1&&!memcmp(&owner->after,&g_world,sizeof g_world)&&
          geo_candidate_evaluation_generation(core)==generation,"publish-oom-retry-complete-without-evaluation");
    free(live);return 0;
}
static int direct_null(const char *path)
{
    CHECK(prepare(path)&&preview(),"publish-preview");
    AppWorldCandidate *owner=g_preview.transaction;World *live=malloc(sizeof *live);CHECK(live,"publish-memory");*live=g_world;
    d_reset();CHECK(!app_world_candidate_publish(NULL,&g_world,false),"publish-null-owner-rejected");
    CHECK(!app_world_candidate_publish(owner,NULL,false),"publish-null-live-rejected");
    CHECK(d_replaces==0&&!memcmp(live,&g_world,sizeof g_world)&&
          geo_candidate_state(app_candidate_core(owner->control))==GEO_CANDIDATE_SEALED,"publish-null-atomic");
    free(live);return 0;
}

int main(int argc,char **argv)
{
    if(argc!=3)return 2;
    int result;
    if(!strcmp(argv[1],"factory"))result=factory();
    else if(!strcmp(argv[1],"lifecycle"))result=real_lifecycle(argv[2]);
    else if(!strcmp(argv[1],"core-first"))result=core_first(argv[2]);
    else if(!strcmp(argv[1],"direct-cost"))result=direct_success(argv[2],false,true);
    else if(!strcmp(argv[1],"direct-keep"))result=direct_success(argv[2],true,false);
    else if(!strcmp(argv[1],"direct-replace"))result=direct_success(argv[2],false,false);
    else if(!strcmp(argv[1],"direct-null"))result=direct_null(argv[2]);
    else if(!strcmp(argv[1],"direct-unsealed")||!strcmp(argv[1],"direct-discarded")||!strcmp(argv[1],"direct-reopened"))
        result=direct_terminal(argv[2],argv[1]+7);
    else if(!strcmp(argv[1],"direct-oom1"))result=direct_oom(argv[2],1);
    else if(!strcmp(argv[1],"direct-oom2"))result=direct_oom(argv[2],2);
    else if(!strcmp(argv[1],"direct-oom-persistent"))result=direct_oom(argv[2],3);
    else if(!strncmp(argv[1],"direct-",7))result=direct_tamper(argv[2],argv[1]+7);
    else return 2;
    if(!result)printf("PASS %s\n",argv[1]);
    return result;
}
