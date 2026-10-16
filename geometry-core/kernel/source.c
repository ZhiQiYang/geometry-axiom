#include "source.h"
#include <stdlib.h>
#include <string.h>

typedef struct {
    GeoSourceRef source;
    GeoSourceDescriptor descriptor;
    GeoSourceValue value;
    GeoSourceState state;
    GeoSourceStatus status;
    size_t provider;
    bool described;
} GeoSourceNode;
struct GeoEvalContext {
    uint64_t candidate_id,base_revision;
    GeoSourceProvider *providers;
    size_t provider_count;
    GeoSourceNode **nodes;
    size_t node_count;
    GeoSourceEdge *edges;
    size_t edge_count;
    size_t active;
    bool started;
};
static char *geo_source_copy_text(const char *text)
{
    if(!text||!*text)return NULL;
    size_t length=strlen(text);char *copy=malloc(length+1);
    if(copy)memcpy(copy,text,length+1);return copy;
}
GeoEvalContext *geo_eval_create(uint64_t candidate_id,uint64_t base_revision)
{
    GeoEvalContext *ctx=calloc(1,sizeof *ctx);
    if(ctx){ctx->candidate_id=candidate_id;ctx->base_revision=base_revision;ctx->active=SIZE_MAX;}
    return ctx;
}
void geo_eval_destroy(GeoEvalContext *ctx)
{
    if(!ctx)return;
    for(size_t i=0;i<ctx->provider_count;++i){free((void *)ctx->providers[i].name_space);free((void *)ctx->providers[i].implementation_fingerprint);}
    for(size_t i=0;i<ctx->node_count;++i){free((void *)ctx->nodes[i]->source.key);free(ctx->nodes[i]);}
    free(ctx->providers);free(ctx->nodes);free(ctx->edges);free(ctx);
}
bool geo_eval_register(GeoEvalContext *ctx,const GeoSourceProvider *provider)
{
    if(!ctx||ctx->started||!provider||!provider->describe||!provider->evaluate||
       !provider->name_space||!*provider->name_space||!provider->implementation_fingerprint||!*provider->implementation_fingerprint)return false;
    for(size_t i=0;i<ctx->provider_count;++i)
        if(ctx->providers[i].token==provider->token||!strcmp(ctx->providers[i].name_space,provider->name_space))return false;
    char *name=geo_source_copy_text(provider->name_space),*fingerprint=geo_source_copy_text(provider->implementation_fingerprint);
    if(!name||!fingerprint){free(name);free(fingerprint);return false;}
    if(ctx->provider_count==SIZE_MAX/sizeof *ctx->providers){free(name);free(fingerprint);return false;}
    GeoSourceProvider *next=realloc(ctx->providers,(ctx->provider_count+1)*sizeof *next);
    if(!next){free(name);free(fingerprint);return false;}
    ctx->providers=next;next[ctx->provider_count]=*provider;
    next[ctx->provider_count].name_space=name;next[ctx->provider_count].implementation_fingerprint=fingerprint;
    ++ctx->provider_count;return true;
}
uint64_t geo_eval_candidate_id(const GeoEvalContext *ctx){return ctx?ctx->candidate_id:0;}
uint64_t geo_eval_base_revision(const GeoEvalContext *ctx){return ctx?ctx->base_revision:0;}
size_t geo_eval_provider_count(const GeoEvalContext *ctx){return ctx?ctx->provider_count:0;}
const GeoSourceProvider *geo_eval_provider_at(const GeoEvalContext *ctx,size_t i){return ctx&&i<ctx->provider_count?&ctx->providers[i]:NULL;}
static GeoSourceStatus geo_source_node(GeoEvalContext *ctx,GeoSourceRef source,size_t *index)
{
    if(!ctx||!index||(source.key_size&&!source.key))return GEO_SOURCE_INVALID;
    ctx->started=true;
    for(size_t i=0;i<ctx->node_count;++i){GeoSourceRef *ref=&ctx->nodes[i]->source;
        if(ref->provider==source.provider&&ref->key_size==source.key_size&&
           (!source.key_size||!memcmp(ref->key,source.key,source.key_size))){*index=i;return GEO_SOURCE_OK;}}
    size_t provider=0;while(provider<ctx->provider_count&&ctx->providers[provider].token!=source.provider)++provider;
    if(provider==ctx->provider_count)return GEO_SOURCE_MISSING;
    if(ctx->node_count==SIZE_MAX/sizeof *ctx->nodes)return GEO_SOURCE_MEMORY;
    GeoSourceNode *node=calloc(1,sizeof *node);
    if(!node)return GEO_SOURCE_MEMORY;
    if(source.key_size){void *key=malloc(source.key_size);if(!key){free(node);return GEO_SOURCE_MEMORY;}memcpy(key,source.key,source.key_size);source.key=key;}
    else source.key=NULL;
    GeoSourceNode **next=realloc(ctx->nodes,(ctx->node_count+1)*sizeof *next);
    if(!next){free((void *)source.key);free(node);return GEO_SOURCE_MEMORY;}
    ctx->nodes=next;node->source=source;node->provider=provider;node->status=GEO_SOURCE_OK;
    *index=ctx->node_count;next[ctx->node_count++]=node;return GEO_SOURCE_OK;
}
static GeoSourceStatus geo_source_edge(GeoEvalContext *ctx,size_t source,GeoDependencyKind kind)
{
    if(kind<GEO_DEPENDENCY_VALUE_REQUIRED||kind>GEO_DEPENDENCY_EVALUATE_BEFORE)return GEO_SOURCE_INVALID;
    if(ctx->active==SIZE_MAX)return GEO_SOURCE_OK;
    GeoSourceEdge edge={ctx->active,source,kind};
    for(size_t i=0;i<ctx->edge_count;++i)
        if(ctx->edges[i].consumer==edge.consumer&&ctx->edges[i].source==edge.source&&ctx->edges[i].kind==edge.kind)return GEO_SOURCE_OK;
    if(ctx->edge_count==SIZE_MAX/sizeof *ctx->edges)return GEO_SOURCE_MEMORY;
    GeoSourceEdge *next=realloc(ctx->edges,(ctx->edge_count+1)*sizeof *next);
    if(!next)return GEO_SOURCE_MEMORY;
    ctx->edges=next;next[ctx->edge_count++]=edge;return GEO_SOURCE_OK;
}
static bool geo_source_descriptor_valid(const GeoSourceDescriptor *d)
{
    return d->kind>=GEO_SOURCE_QUANTITY&&d->kind<=GEO_SOURCE_FEATURE&&
        (d->unit==GEO_UNIT_SCALAR||d->unit==GEO_UNIT_LENGTH)&&
        d->context.axis>=-1&&d->context.axis<=2;
}
static bool geo_source_context_equal(GeoSourceContext a,GeoSourceContext b)
{
    return a.has_placement==b.has_placement&&a.axis==b.axis&&(!a.has_placement||a.placement==b.placement);
}
static bool geo_source_value_matches(const GeoSourceDescriptor *d,const GeoSourceValue *v)
{
    if(v->kind!=d->kind)return false;
    if(v->kind==GEO_SOURCE_QUANTITY)return v->as.quantity.den>0&&v->as.quantity.unit==d->unit;
    if(v->kind==GEO_SOURCE_AXIS_POSITION)return geo_source_context_equal(d->context,v->as.position.context);
    if(v->kind==GEO_SOURCE_REGION_SET)return !v->as.regions.count||v->as.regions.regions!=NULL;
    if(v->kind==GEO_SOURCE_FEATURE)return !v->as.feature.key_size||v->as.feature.key!=NULL;
    return true;
}
GeoSourceStatus geo_eval_depend(GeoEvalContext *ctx,GeoSourceRef source,GeoDependencyKind kind)
{
    size_t index;GeoSourceStatus result=geo_source_node(ctx,source,&index);
    if(result!=GEO_SOURCE_OK)return result;
    return geo_source_edge(ctx,index,kind);
}
GeoSourceStatus geo_eval_source(GeoEvalContext *ctx,GeoSourceRef source,GeoDependencyKind kind,GeoSourceValue *out)
{
    if(!out)return GEO_SOURCE_INVALID;
    size_t index;GeoSourceStatus result=geo_source_node(ctx,source,&index);
    if(result!=GEO_SOURCE_OK)return result;
    result=geo_source_edge(ctx,index,kind);if(result!=GEO_SOURCE_OK)return result;
    GeoSourceNode *node=ctx->nodes[index];
    if(node->state==GEO_NODE_ACTIVE)return GEO_SOURCE_CYCLE;
    if(node->state==GEO_NODE_VALID){*out=node->value;return GEO_SOURCE_OK;}
    if(node->state==GEO_NODE_FAILED&&(!node->described||!node->descriptor.retry_failure))return node->status;
    GeoSourceProvider *provider=&ctx->providers[node->provider];
    if(!node->described){
        node->described=provider->describe(provider->candidate_state,&node->source,&node->descriptor);
        if(!node->described||!geo_source_descriptor_valid(&node->descriptor)){
            node->state=GEO_NODE_FAILED;node->status=node->described?GEO_SOURCE_INVALID:GEO_SOURCE_MISSING;return node->status;}
    }
    if(!geo_source_descriptor_valid(&node->descriptor))return GEO_SOURCE_INVALID;
    size_t previous=ctx->active;ctx->active=index;node->state=GEO_NODE_ACTIVE;
    GeoSourceValue value={0};bool ok=provider->evaluate(provider->candidate_state,ctx,&node->source,&value);
    ctx->active=previous;node->state=GEO_NODE_FAILED;node->status=GEO_SOURCE_FAILED;
    if(!ok)return node->status;
    if(!geo_source_value_matches(&node->descriptor,&value)){node->status=GEO_SOURCE_INVALID;return node->status;}
    node->value=value;node->state=GEO_NODE_VALID;node->status=GEO_SOURCE_OK;
    *out=node->value;return GEO_SOURCE_OK;
}
size_t geo_eval_node_count(const GeoEvalContext *ctx){return ctx?ctx->node_count:0;}
bool geo_eval_node_at(const GeoEvalContext *ctx,size_t i,GeoSourceNodeView *out)
{
    if(!ctx||i>=ctx->node_count||!out)return false;
    const GeoSourceNode *node=ctx->nodes[i];
    *out=(GeoSourceNodeView){node->source,node->descriptor,node->state,node->status,node->state==GEO_NODE_VALID?&node->value:NULL};return true;
}
size_t geo_eval_edge_count(const GeoEvalContext *ctx){return ctx?ctx->edge_count:0;}
bool geo_eval_edge_at(const GeoEvalContext *ctx,size_t i,GeoSourceEdge *out)
{if(!ctx||i>=ctx->edge_count||!out)return false;*out=ctx->edges[i];return true;}
