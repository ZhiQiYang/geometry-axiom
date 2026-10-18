/* The fixture expands this include, changing only the old main declaration
 * and its bridge include path. Every original lifecycle assertion is retained. */
#include "geo261_candidate_product_harness.c"

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
int main(int argc,char **argv)
{
    if(argc!=3)return 2;
    int result;
    if(!strcmp(argv[1],"factory"))result=factory();
    else if(!strcmp(argv[1],"lifecycle"))result=real_lifecycle(argv[2]);
    else if(!strcmp(argv[1],"core-first"))result=core_first(argv[2]);
    else return 2;
    if(!result)printf("PASS %s\n",argv[1]);
    return result;
}
