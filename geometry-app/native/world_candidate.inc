/* Complete H application snapshot. All K and W mutations use after; the only
 * publication callback replaces the whole root after the common seal passes. */
#include "candidate_unity.inc"
typedef struct {
    bool boundary_keyed; uint32_t boundary_id;
    size_t stagger_count; uint32_t stagger_steps;
    char stagger_seal[65];
} AppWorldOperation;
typedef struct {
    World before,after;
    AppCandidate *control;
    AppWorldOperation operation;
    char operation_seal[65];
    WoodGridStaggerFact *stagger_facts;
    size_t stagger_capacity;
} AppWorldCandidate;
static AppWorldCandidate *g_active_app_candidate;
static uint64_t g_app_candidate_serial;
static bool g_boundary_keyed_update;
static uint32_t g_boundary_keyed_id;
static const char *app_world_provider_stamp(void)
{
    return "native-composition/5;core:typed-definitions,linear-graph,parameter-ast,parameters,named-values,datums,guides,regions,placements,grid;"
        "wood:engineering-source-graph,members,supports,contacts,panel;host:history,candidate";
}
/* Optional block reuse for a process that opens many sequential candidates
 * (model-base, GEO-261 cost). Off unless that process enables it. A reused
 * block is zeroed after its two Worlds, as calloc left it; the constructor
 * overwrites both Worlds from live before anything reads them. */
#define APP_WORLD_CANDIDATE_POOL_MAX 4
static bool g_app_world_candidate_pool_enabled;
static AppWorldCandidate *g_app_world_candidate_pool[APP_WORLD_CANDIDATE_POOL_MAX];
static size_t g_app_world_candidate_pool_count;
/* Ordered I24 evidence is owned by this candidate, outside World/history and
 * the parameter-deletion scratch. The existing operation seal binds its bytes. */
static void app_world_candidate_clear_stagger(AppWorldCandidate *candidate)
{
    if(!candidate)return;
    free(candidate->stagger_facts);candidate->stagger_facts=NULL;candidate->stagger_capacity=0;
    candidate->operation.stagger_count=0;candidate->operation.stagger_steps=0;
    memset(candidate->operation.stagger_seal,0,sizeof candidate->operation.stagger_seal);
}
static void app_world_candidate_discard(AppWorldCandidate *candidate)
{if(candidate){app_world_candidate_clear_stagger(candidate);app_candidate_discard(candidate->control);}}
static void app_world_stagger_hash(const AppWorldCandidate *candidate,char hash[65])
{
    if(!candidate->operation.stagger_count){memset(hash,0,65);return;}
    geo_sha256(candidate->stagger_facts,candidate->operation.stagger_count*sizeof(WoodGridStaggerFact),hash);
}
static bool app_world_stagger_current(const AppWorldCandidate *candidate)
{
    if(candidate->operation.stagger_count>candidate->stagger_capacity||
       (candidate->operation.stagger_count&&!candidate->stagger_facts))return false;
    char hash[65];app_world_stagger_hash(candidate,hash);
    return !strcmp(hash,candidate->operation.stagger_seal);
}
static void app_world_candidate_destroy(AppWorldCandidate *candidate)
{
    if(!candidate)return;
    app_world_candidate_clear_stagger(candidate);
    app_candidate_destroy(candidate->control);
    if(g_app_world_candidate_pool_enabled&&g_app_world_candidate_pool_count<APP_WORLD_CANDIDATE_POOL_MAX)
        g_app_world_candidate_pool[g_app_world_candidate_pool_count++]=candidate;
    else free(candidate);
}
static AppWorldCandidate *app_world_candidate_alloc(void)
{
    if(!g_app_world_candidate_pool_enabled||!g_app_world_candidate_pool_count)
        return calloc(1,sizeof(AppWorldCandidate));
    AppWorldCandidate *candidate=g_app_world_candidate_pool[--g_app_world_candidate_pool_count];
    size_t worlds=offsetof(AppWorldCandidate,after)+sizeof(World);
    memset((unsigned char*)candidate+worlds,0,sizeof *candidate-worlds);
    return candidate;
}
static AppWorldCandidate *app_world_candidate_create(const World *live)
{
    AppWorldCandidate *candidate=app_world_candidate_alloc();
    if(!candidate)return NULL;
    candidate->control=app_candidate_create_deferred_sha(&candidate->before,&candidate->after,live,sizeof(World),
        ++g_app_candidate_serial,g_definition_revision,app_world_provider_stamp());
    if(!candidate->control){free(candidate);return NULL;}
#define APP_BIND_CORE(field) \
    if(app_candidate_bind_core(candidate->control,"core." #field,offsetof(World,geo)+offsetof(GeoDocument,field), \
        sizeof candidate->after.geo.field)!=GEO_CANDIDATE_OK){app_world_candidate_destroy(candidate);return NULL;}
    APP_BIND_CORE(parameters)
    APP_BIND_CORE(named_values)
    APP_BIND_CORE(datum_planes)
    APP_BIND_CORE(guide_lines)
    APP_BIND_CORE(region_data)
    APP_BIND_CORE(placement_data)
    APP_BIND_CORE(grid_store)
    APP_BIND_CORE(version_store)
    APP_BIND_CORE(enclosures)
#undef APP_BIND_CORE
    return candidate;
}
static GeoCandidateStatus app_world_candidate_evaluate(AppWorldCandidate *candidate,
    AppCandidateEvaluate evaluate,void *opaque)
{
    AppWorldCandidate *previous=g_active_app_candidate;g_active_app_candidate=candidate;
    GeoCandidateStatus status=app_candidate_evaluate(candidate->control,evaluate,opaque);
    g_active_app_candidate=previous;return status;
}
static bool app_world_candidate_equal(const void *live,const void *before,void *opaque)
{(void)opaque;return world_definitions_equal(live,before);}
static void app_world_candidate_replace(void *live,const void *after,void *opaque)
{
    if(opaque)history_restore_world(live,after);
    else memcpy(live,after,sizeof(World));
}
static bool app_world_candidate_describe_sources(AppWorldCandidate *candidate)
{
    GeoEvalContext *sources=geo_candidate_sources(app_candidate_core(candidate->control));
    for(size_t i=0;i<geo_eval_node_count(sources);++i){GeoSourceNodeView node;GeoSourceDescriptor descriptor;
        if(!geo_eval_node_at(sources,i,&node)||(!node.described&&
            geo_eval_describe(sources,node.source,&descriptor)!=GEO_SOURCE_OK))return false;
    }
    return true;
}
static bool app_world_candidate_seal(AppWorldCandidate *candidate)
{
    if(candidate->operation.stagger_count>candidate->stagger_capacity||
       (candidate->operation.stagger_count&&!candidate->stagger_facts))return false;
    if(!app_world_candidate_describe_sources(candidate))return false;
    if(app_candidate_seal(candidate->control)!=GEO_CANDIDATE_OK)return false;
    app_world_stagger_hash(candidate,candidate->operation.stagger_seal);
    geo_sha256(&candidate->operation,sizeof candidate->operation,candidate->operation_seal);return true;
}
static bool app_world_candidate_current(const AppWorldCandidate *candidate,const World *live)
{
    if(!candidate)return false;
    char hash[65];geo_sha256(&candidate->operation,sizeof candidate->operation,hash);
    return !strcmp(hash,candidate->operation_seal)&&app_world_stagger_current(candidate)&&app_candidate_check(candidate->control,live,g_definition_revision,
        app_world_provider_stamp(),app_world_candidate_equal,NULL)==GEO_CANDIDATE_OK;
}
static bool app_world_candidate_publish(AppWorldCandidate *candidate,World *live,bool preserve_canvas)
{
    if(!candidate)return false;
    char hash[65];geo_sha256(&candidate->operation,sizeof candidate->operation,hash);
    if(strcmp(hash,candidate->operation_seal))return false;
    if(!app_world_stagger_current(candidate))return false;
    return app_candidate_publish(candidate->control,live,g_definition_revision,app_world_provider_stamp(),
        app_world_candidate_equal,app_world_candidate_replace,preserve_canvas?(void*)candidate:NULL)==GEO_CANDIDATE_OK;
}
