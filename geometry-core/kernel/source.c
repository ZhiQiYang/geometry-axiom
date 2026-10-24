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
    size_t node_count, node_capacity;
    size_t *node_index, node_index_capacity;
    size_t node_hint[256];
    GeoSourceEdge *edges;
    size_t edge_count, edge_capacity;
    size_t *edge_index, edge_index_capacity;
    size_t active;
    bool started, sealed;
};
/* 索引只保存插入序號加一，零為空槽；陣列仍是唯一的列舉順序。
 * 配置失敗時捨棄索引並線性查找，不能讓可選索引新增 MEMORY 結果。 */
static uint64_t geo_source_hash_size(uint64_t hash,size_t value)
{
    hash^=(uint64_t)value;hash*=UINT64_C(11400714785074694791);
    return hash^(hash>>32);
}
static uint64_t geo_source_node_hash(GeoSourceRef source)
{
    uint64_t hash=geo_source_hash_size(UINT64_C(14695981039346656037),source.provider);
    hash=geo_source_hash_size(hash,source.key_size);
    const unsigned char *key=source.key;size_t i=0;
    /* 雜湊只選記憶體索引槽；身分仍完整比對每個位元組。
     * memcpy 可讀未對齊的鍵；主機端序只影響碰撞排列。 */
    while(source.key_size-i>=sizeof(uint64_t)){
        uint64_t word;memcpy(&word,key+i,sizeof word);
        hash^=word;hash*=UINT64_C(11400714785074694791);hash^=hash>>32;
        i+=sizeof word;
    }
    for(;i<source.key_size;++i){hash^=key[i];hash*=UINT64_C(1099511628211);}
    return hash;
}
static uint64_t geo_source_edge_hash(GeoSourceEdge edge)
{
    uint64_t hash=geo_source_hash_size(UINT64_C(14695981039346656037),edge.consumer);
    hash=geo_source_hash_size(hash,edge.source);
    return geo_source_hash_size(hash,(size_t)edge.kind);
}
static bool geo_source_ref_equal(GeoSourceRef a,GeoSourceRef b)
{
    return a.provider==b.provider&&a.key_size==b.key_size&&
        (!a.key_size||!memcmp(a.key,b.key,a.key_size));
}
static bool geo_source_edge_equal(GeoSourceEdge a,GeoSourceEdge b)
{return a.consumer==b.consumer&&a.source==b.source&&a.kind==b.kind;}
static size_t geo_source_find_node(const GeoEvalContext *ctx,GeoSourceRef source)
{
    if(ctx->node_index_capacity){
        size_t mask=ctx->node_index_capacity-1,slot=(size_t)geo_source_node_hash(source)&mask;
        while(ctx->node_index[slot]){
            size_t i=ctx->node_index[slot]-1;
            if(geo_source_ref_equal(ctx->nodes[i]->source,source))return i;
            slot=(slot+1)&mask;
        }
    }else for(size_t i=0;i<ctx->node_count;++i)
        if(geo_source_ref_equal(ctx->nodes[i]->source,source))return i;
    return SIZE_MAX;
}
static bool geo_source_find_edge(const GeoEvalContext *ctx,GeoSourceEdge edge,size_t *empty_slot)
{
    if(ctx->edge_index_capacity){
        size_t mask=ctx->edge_index_capacity-1,slot=(size_t)geo_source_edge_hash(edge)&mask;
        while(ctx->edge_index[slot]){
            if(geo_source_edge_equal(ctx->edges[ctx->edge_index[slot]-1],edge))return true;
            slot=(slot+1)&mask;
        }
        *empty_slot=slot;
    }else for(size_t i=0;i<ctx->edge_count;++i)
        if(geo_source_edge_equal(ctx->edges[i],edge))return true;
    return false;
}
/* 負載最多一半；新表建好才換入。失敗後舊表不完整，須改走線性搜尋。 */
static void geo_source_index_append(GeoEvalContext *ctx,bool nodes,size_t empty_slot)
{
    size_t **table=nodes?&ctx->node_index:&ctx->edge_index;
    size_t *capacity=nodes?&ctx->node_index_capacity:&ctx->edge_index_capacity;
    size_t count=nodes?ctx->node_count:ctx->edge_count,first=count-1;
    if(count>*capacity/2){
        size_t next=*capacity?*capacity:16;
        while(count>next/2){if(next>SIZE_MAX/2)goto fallback;next*=2;}
        if(next>SIZE_MAX/sizeof **table)goto fallback;
        size_t *fresh=calloc(next,sizeof *fresh);
        if(!fresh)goto fallback;
        free(*table);*table=fresh;*capacity=next;first=0;empty_slot=SIZE_MAX;
    }
    /* A missing edge already probed this unchanged index to an empty slot.
     * Rebuilding discards that slot; allocation fallback stays linear. */
    if(empty_slot<*capacity&&!(*table)[empty_slot]){(*table)[empty_slot]=count;return;}
    for(size_t i=first;i<count;++i){
        uint64_t hash=nodes?geo_source_node_hash(ctx->nodes[i]->source):geo_source_edge_hash(ctx->edges[i]);
        size_t mask=*capacity-1,slot=(size_t)hash&mask;
        while((*table)[slot])slot=(slot+1)&mask;
        (*table)[slot]=i+1;
    }
    return;
fallback:
    free(*table);*table=NULL;*capacity=0;
}
static void *geo_source_grow(void *data,size_t count,size_t *capacity,size_t item_size)
{
    if(count<*capacity)return data;
    size_t limit=SIZE_MAX/item_size,next=*capacity?*capacity:8;
    if(next<=limit/2)next*=2;else next=limit;
    if(next>limit)next=limit;
    void *grown=realloc(data,next*item_size);
    /* 倍增失敗仍重試舊實作需要的大小，不擴大 MEMORY 的條件。 */
    if(!grown&&next!=count+1){next=count+1;grown=realloc(data,next*item_size);}
    if(grown)*capacity=next;
    return grown;
}
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
    free(ctx->node_index);free(ctx->edge_index);
    ctx->providers=NULL;ctx->nodes=NULL;ctx->edges=NULL;
    ctx->node_index=NULL;ctx->edge_index=NULL;
    memset(ctx->node_hint,0,sizeof ctx->node_hint);
    ctx->provider_count=ctx->node_count=ctx->edge_count=0;
    ctx->node_capacity=ctx->edge_capacity=ctx->node_index_capacity=ctx->edge_index_capacity=0;
    ctx->active=SIZE_MAX;ctx->started=false;ctx->sealed=false;
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
    /* 只快取既有身分的插入序號；碰撞仍完整比對 K 持有的鍵。 */
    size_t slot=(size_t)source.provider^source.key_size;
    if(source.key_size){const unsigned char *key=source.key;slot^=(size_t)key[0]^key[source.key_size-1];}
    slot&=255;
    size_t hint=ctx->node_hint[slot];
    if(hint&&hint<=ctx->node_count&&geo_source_ref_equal(ctx->nodes[hint-1]->source,source)){
        *index=hint-1;return GEO_SOURCE_OK;
    }
    size_t found=geo_source_find_node(ctx,source);
    if(found!=SIZE_MAX){ctx->node_hint[slot]=found+1;*index=found;return GEO_SOURCE_OK;}
    size_t provider=0;while(provider<ctx->provider_count&&ctx->providers[provider].token!=source.provider)++provider;
    if(provider==ctx->provider_count)return GEO_SOURCE_MISSING;
    if(ctx->node_count==SIZE_MAX/sizeof *ctx->nodes)return GEO_SOURCE_MEMORY;
    GeoSourceNode *node=calloc(1,sizeof *node);
    if(!node)return GEO_SOURCE_MEMORY;
    if(source.key_size){void *key=malloc(source.key_size);if(!key){free(node);return GEO_SOURCE_MEMORY;}memcpy(key,source.key,source.key_size);source.key=key;}
    else source.key=NULL;
    GeoSourceNode **next=geo_source_grow(ctx->nodes,ctx->node_count,&ctx->node_capacity,sizeof *next);
    if(!next){free((void *)source.key);free(node);return GEO_SOURCE_MEMORY;}
    ctx->nodes=next;node->source=source;node->provider=provider;node->status=GEO_SOURCE_OK;
    *index=ctx->node_count;next[ctx->node_count++]=node;
    geo_source_index_append(ctx,true,SIZE_MAX);ctx->node_hint[slot]=*index+1;return GEO_SOURCE_OK;
}
static GeoSourceStatus geo_source_edge(GeoEvalContext *ctx,size_t source,GeoDependencyKind kind)
{
    if(kind<GEO_DEPENDENCY_VALUE_REQUIRED||kind>GEO_DEPENDENCY_EVALUATE_BEFORE)return GEO_SOURCE_INVALID;
    if(ctx->active==SIZE_MAX)return GEO_SOURCE_OK;
    GeoSourceEdge edge={ctx->active,source,kind};
    size_t empty_slot=SIZE_MAX;
    if(geo_source_find_edge(ctx,edge,&empty_slot))return GEO_SOURCE_OK;
    if(ctx->edge_count==SIZE_MAX/sizeof *ctx->edges)return GEO_SOURCE_MEMORY;
    GeoSourceEdge *next=geo_source_grow(ctx->edges,ctx->edge_count,&ctx->edge_capacity,sizeof *next);
    if(!next)return GEO_SOURCE_MEMORY;
    ctx->edges=next;next[ctx->edge_count++]=edge;
    geo_source_index_append(ctx,false,empty_slot);return GEO_SOURCE_OK;
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
        index=geo_source_find_node(ctx,source);
        if(index==SIZE_MAX||!ctx->nodes[index]->described)return GEO_SOURCE_INVALID;
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
        size_t i=geo_source_find_node(ctx,source);
        if(i==SIZE_MAX||ctx->nodes[i]->state!=GEO_NODE_VALID)return GEO_SOURCE_INVALID;
        *out=ctx->nodes[i]->value;return GEO_SOURCE_OK;
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
