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
    bool started, sealed;
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
static void geo_eval_clear(GeoEvalContext *ctx)
{
    for(size_t i=0;i<ctx->provider_count;++i){free((void *)ctx->providers[i].name_space);free((void *)ctx->providers[i].implementation_fingerprint);}
    for(size_t i=0;i<ctx->node_count;++i){free((void *)ctx->nodes[i]->source.key);free(ctx->nodes[i]);}
    free(ctx->providers);free(ctx->nodes);free(ctx->edges);
    ctx->providers=NULL;ctx->nodes=NULL;ctx->edges=NULL;
    ctx->provider_count=ctx->node_count=ctx->edge_count=0;
    ctx->active=SIZE_MAX;ctx->started=false;
}
void geo_eval_destroy(GeoEvalContext *ctx)
{if(ctx){geo_eval_clear(ctx);free(ctx);}}
bool geo_eval_register(GeoEvalContext *ctx,const GeoSourceProvider *provider)
{return geo_eval_register_many(ctx,provider,1);}
bool geo_eval_register_many(GeoEvalContext *ctx,const GeoSourceProvider *providers,size_t count)
{
    if(!ctx||ctx->started||ctx->sealed||!providers||!count||count>SIZE_MAX/sizeof *providers-ctx->provider_count)return false;
    for(size_t n=0;n<count;++n){const GeoSourceProvider *p=&providers[n];
        if(!p->describe||!p->evaluate||!p->name_space||!*p->name_space||!p->implementation_fingerprint||!*p->implementation_fingerprint)return false;
        for(size_t i=0;i<ctx->provider_count;++i)
            if(ctx->providers[i].token==p->token||!strcmp(ctx->providers[i].name_space,p->name_space))return false;
        for(size_t i=0;i<n;++i)
            if(providers[i].token==p->token||!strcmp(providers[i].name_space,p->name_space))return false;
    }
    GeoSourceProvider *next=calloc(ctx->provider_count+count,sizeof *next);if(!next)return false;
    if(ctx->provider_count)memcpy(next,ctx->providers,ctx->provider_count*sizeof *next);
    for(size_t n=0;n<count;++n){GeoSourceProvider *p=&next[ctx->provider_count+n];*p=providers[n];
        p->name_space=geo_source_copy_text(providers[n].name_space);
        p->implementation_fingerprint=geo_source_copy_text(providers[n].implementation_fingerprint);
        if(!p->name_space||!p->implementation_fingerprint){
            for(size_t i=0;i<=n;++i){free((void *)next[ctx->provider_count+i].name_space);free((void *)next[ctx->provider_count+i].implementation_fingerprint);}
            free(next);return false;
        }
    }
    free(ctx->providers);ctx->providers=next;ctx->provider_count+=count;return true;
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
    return d->kind>=GEO_SOURCE_QUANTITY&&d->kind<=GEO_SOURCE_DEFINITION&&
        (d->unit==GEO_UNIT_SCALAR||d->unit==GEO_UNIT_LENGTH)&&
        d->context.axis>=-1&&d->context.axis<=2&&
        (!d->context_from_value||d->kind==GEO_SOURCE_AXIS_POSITION);
}
static bool geo_source_context_equal(GeoSourceContext a,GeoSourceContext b)
{
    return a.has_placement==b.has_placement&&a.axis==b.axis&&(!a.has_placement||a.placement==b.placement);
}
static bool geo_source_value_matches(const GeoSourceDescriptor *d,const GeoSourceValue *v)
{
    if(v->kind!=d->kind)return false;
    if(v->kind==GEO_SOURCE_QUANTITY)return v->as.quantity.den>0&&v->as.quantity.unit==d->unit;
    if(v->kind==GEO_SOURCE_AXIS_POSITION)return d->context_from_value?
        v->as.position.context.axis>=0&&v->as.position.context.axis<=2:
        geo_source_context_equal(d->context,v->as.position.context);
    if(v->kind==GEO_SOURCE_REGION_SET)return !v->as.regions.count||v->as.regions.regions!=NULL;
    if(v->kind==GEO_SOURCE_FEATURE)return !v->as.feature.key_size||v->as.feature.key!=NULL;
    if(v->kind==GEO_SOURCE_DEFINITION)return v->as.definition.schema&&*v->as.definition.schema&&
        (!v->as.definition.content_size||v->as.definition.content!=NULL);
    return true;
}
GeoSourceStatus geo_eval_describe(GeoEvalContext *ctx,GeoSourceRef source,GeoSourceDescriptor *out)
{
    if(!ctx||!out||(source.key_size&&!source.key))return GEO_SOURCE_INVALID;
    size_t index=0;
    if(ctx->sealed){
        for(;index<ctx->node_count;++index){const GeoSourceRef *ref=&ctx->nodes[index]->source;
            if(ref->provider==source.provider&&ref->key_size==source.key_size&&
               (!source.key_size||!memcmp(ref->key,source.key,source.key_size)))break;
        }
        if(index==ctx->node_count||!ctx->nodes[index]->described)return GEO_SOURCE_INVALID;
    }else{
        GeoSourceStatus status=geo_source_node(ctx,source,&index);
        if(status!=GEO_SOURCE_OK)return status;
    }
    GeoSourceNode *node=ctx->nodes[index];
    if(!node->described){
        GeoSourceProvider *provider=&ctx->providers[node->provider];
        GeoSourceDescriptor descriptor={0};
        if(!provider->describe(provider->candidate_state,&node->source,&descriptor))return GEO_SOURCE_MISSING;
        if(!geo_source_descriptor_valid(&descriptor))return GEO_SOURCE_INVALID;
        node->descriptor=descriptor;node->described=true;
    }
    if(!geo_source_descriptor_valid(&node->descriptor))return GEO_SOURCE_INVALID;
    *out=node->descriptor;return GEO_SOURCE_OK;
}
GeoSourceStatus geo_eval_depend(GeoEvalContext *ctx,GeoSourceRef source,GeoDependencyKind kind)
{
    if(ctx&&ctx->sealed)return GEO_SOURCE_INVALID;
    size_t index;GeoSourceStatus result=geo_source_node(ctx,source,&index);
    if(result!=GEO_SOURCE_OK)return result;
    return geo_source_edge(ctx,index,kind);
}
GeoSourceStatus geo_eval_source(GeoEvalContext *ctx,GeoSourceRef source,GeoDependencyKind kind,GeoSourceValue *out)
{
    if(!out)return GEO_SOURCE_INVALID;
    if(ctx&&ctx->sealed){
        if((source.key_size&&!source.key)||kind<GEO_DEPENDENCY_VALUE_REQUIRED||kind>GEO_DEPENDENCY_EVALUATE_BEFORE)return GEO_SOURCE_INVALID;
        for(size_t i=0;i<ctx->node_count;++i){
            const GeoSourceNode *node=ctx->nodes[i];const GeoSourceRef *ref=&node->source;
            if(ref->provider==source.provider&&ref->key_size==source.key_size&&
               (!source.key_size||!memcmp(ref->key,source.key,source.key_size))){
                if(node->state!=GEO_NODE_VALID)return GEO_SOURCE_INVALID;
                *out=node->value;return GEO_SOURCE_OK;
            }
        }
        return GEO_SOURCE_INVALID;
    }
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
    if(node->descriptor.context_from_value){node->descriptor.context=value.as.position.context;node->descriptor.context_from_value=false;}
    node->value=value;node->state=GEO_NODE_VALID;node->status=GEO_SOURCE_OK;
    *out=node->value;return GEO_SOURCE_OK;
}
size_t geo_eval_node_count(const GeoEvalContext *ctx){return ctx?ctx->node_count:0;}
bool geo_eval_node_at(const GeoEvalContext *ctx,size_t i,GeoSourceNodeView *out)
{
    if(!ctx||i>=ctx->node_count||!out)return false;
    const GeoSourceNode *node=ctx->nodes[i];
    *out=(GeoSourceNodeView){node->source,node->descriptor,node->state,node->status,node->state==GEO_NODE_VALID?&node->value:NULL,node->described};return true;
}
size_t geo_eval_edge_count(const GeoEvalContext *ctx){return ctx?ctx->edge_count:0;}
bool geo_eval_edge_at(const GeoEvalContext *ctx,size_t i,GeoSourceEdge *out)
{if(!ctx||i>=ctx->edge_count||!out)return false;*out=ctx->edges[i];return true;}
bool geo_eval_seal(GeoEvalContext *ctx)
{
    if(!ctx)return false;
    for(size_t i=0;i<ctx->node_count;++i)if(ctx->nodes[i]->state==GEO_NODE_ACTIVE)return false;
    ctx->sealed=true;ctx->started=true;return true;
}
bool geo_eval_is_sealed(const GeoEvalContext *ctx){return ctx&&ctx->sealed;}
bool geo_eval_reset(GeoEvalContext *ctx)
{
    if(!ctx||ctx->sealed||ctx->active!=SIZE_MAX)return false;
    geo_eval_clear(ctx);return true;
}
