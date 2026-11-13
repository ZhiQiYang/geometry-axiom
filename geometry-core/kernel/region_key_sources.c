#include "region_key_sources.h"
#include "placement_sources.h"
#include <stdlib.h>
#include <string.h>

typedef struct GeoRegionKeyDefinition GeoRegionKeyDefinition;
struct GeoRegionKeyDefinition {
    uint32_t id;
    unsigned char content[GEO_REGION_KEY_LEDGER_CONTENT_MAX];
    size_t size;
    GeoRegionKeyDefinition *next;
};
struct GeoRegionKeySources {
    GeoEvalContext *graph;
    const GeoRegionStore *regions;
    GeoProviderToken key_token,region_token;
    GeoRegionKeyDefinition *definitions;
};
static void geo_region_key_write32(unsigned char *bytes,uint32_t value)
{for(unsigned i=0;i<4;++i)bytes[i]=(unsigned char)(value>>(24-8*i));}
static uint32_t geo_region_key_read32(const unsigned char *bytes)
{uint32_t value=0;for(unsigned i=0;i<4;++i)value=(value<<8)|bytes[i];return value;}

GeoSourceRef geo_region_key_source_ref(GeoProviderToken token,GeoRegionKeySourceKind kind,
    uint32_t id,uint32_t key,uint32_t axis,GeoRegionKeySourceKey *out)
{
    if(!out)return (GeoSourceRef){token,NULL,0};
    if(kind==GEO_REGION_KEY_SOURCE_LEDGER)key=axis=0;
    geo_region_key_write32(out->bytes,(uint32_t)kind);geo_region_key_write32(out->bytes+4,id);
    geo_region_key_write32(out->bytes+8,key);geo_region_key_write32(out->bytes+12,axis);
    return (GeoSourceRef){token,out->bytes,sizeof out->bytes};
}
bool geo_region_key_source_decode(const GeoSourceRef *ref,GeoRegionKeySourceKind *kind,
    uint32_t *id,uint32_t *key,uint32_t *axis)
{
    if(!ref||!ref->key||ref->key_size!=16||!kind||!id||!key||!axis)return false;
    const unsigned char *bytes=ref->key;uint32_t k=geo_region_key_read32(bytes);
    uint32_t rid=geo_region_key_read32(bytes+4),vertex=geo_region_key_read32(bytes+8),a=geo_region_key_read32(bytes+12);
    if(k==GEO_REGION_KEY_SOURCE_LEDGER){if(vertex||a)return false;}
    else if(k!=GEO_REGION_KEY_SOURCE_COORDINATE||a>1)return false;
    *kind=(GeoRegionKeySourceKind)k;*id=rid;*key=vertex;*axis=a;return true;
}
static bool geo_region_key_ledger_valid(const GeoRegionKeys *keys)
{
    if(!keys||!keys->loop_count||keys->loop_count>GEO_REGION_MAX_HOLES+1)return false;
    GeoRegionDefinition shape={0};shape.id=keys->boundary_id;shape.hole_count=keys->loop_count-1;
    shape.outline.count=keys->counts[0];
    for(size_t l=1;l<keys->loop_count;++l)shape.holes[l-1].count=keys->counts[l];
    return geo_region_keys_valid(&shape,keys);
}
size_t geo_region_key_ledger_encode(const GeoRegionKeys *keys,void *out,size_t capacity)
{
    if(!out||!geo_region_key_ledger_valid(keys))return 0;
    size_t size=12;
    for(size_t l=0;l<keys->loop_count;++l)size+=4+4*keys->counts[l];
    if(capacity<size)return 0;
    unsigned char *bytes=out;
    geo_region_key_write32(bytes,keys->boundary_id);
    geo_region_key_write32(bytes+4,keys->next_key);
    geo_region_key_write32(bytes+8,(uint32_t)keys->loop_count);size_t offset=12;
    for(size_t l=0;l<keys->loop_count;++l){
        geo_region_key_write32(bytes+offset,(uint32_t)keys->counts[l]);offset+=4;
        for(size_t i=0;i<keys->counts[l];++i){geo_region_key_write32(bytes+offset,keys->keys[l][i]);offset+=4;}
    }
    return size;
}
bool geo_region_key_ledger_decode(const void *content,size_t size,GeoRegionKeys *out)
{
    if(!content||!out||size<12||size>GEO_REGION_KEY_LEDGER_CONTENT_MAX)return false;
    const unsigned char *bytes=content;GeoRegionKeys next={0};
    next.boundary_id=geo_region_key_read32(bytes);next.next_key=geo_region_key_read32(bytes+4);
    next.loop_count=geo_region_key_read32(bytes+8);
    if(!next.loop_count||next.loop_count>GEO_REGION_MAX_HOLES+1)return false;
    size_t offset=12;
    for(size_t l=0;l<next.loop_count;++l){
        if(size-offset<4)return false;size_t count=geo_region_key_read32(bytes+offset);offset+=4;
        if(count>GEO_LOOP_MAX_VERTICES||count>(size-offset)/4)return false;next.counts[l]=count;
        for(size_t i=0;i<count;++i){next.keys[l][i]=geo_region_key_read32(bytes+offset);offset+=4;}
    }
    if(offset!=size||!geo_region_key_ledger_valid(&next))return false;
    *out=next;return true;
}
static GeoRegionKeyDefinition *geo_region_key_definition(GeoRegionKeySources *s,uint32_t id)
{
    for(GeoRegionKeyDefinition *d=s->definitions;d;d=d->next)if(d->id==id)return d;
    GeoRegionKeyDefinition *d=calloc(1,sizeof *d);if(!d)return NULL;
    d->id=id;d->next=s->definitions;s->definitions=d;return d;
}
static bool geo_region_key_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    GeoRegionKeySources *s=opaque;GeoRegionKeySourceKind kind;uint32_t id,key,axis;
    if(ref->provider!=s->key_token||!geo_region_key_source_decode(ref,&kind,&id,&key,&axis))return false;
    GeoSourceDescriptor next={.context={false,0,-1},.retry_failure=true};
    next.kind=kind==GEO_REGION_KEY_SOURCE_LEDGER?GEO_SOURCE_DEFINITION:GEO_SOURCE_QUANTITY;
    next.unit=kind==GEO_REGION_KEY_SOURCE_LEDGER?GEO_UNIT_SCALAR:GEO_UNIT_LENGTH;
    *out=next;return true;
}
/* Materialize only the returned typed geometry. Do not replace its vertices
 * with the store's numeric cache or add geometry validity beyond the original
 * geo_region_vertex_by_key table/shape agreement contract. */
static bool geo_region_key_geometry(uint32_t id,const GeoSourceValue *value,GeoRegionDefinition *out)
{
    if(value->kind!=GEO_SOURCE_REGION_SET||value->as.regions.count!=1||!value->as.regions.regions)return false;
    const GeoRegionView *region=value->as.regions.regions;
    if(region->hole_count>GEO_REGION_MAX_HOLES||(region->hole_count&&!region->holes))return false;
    GeoRegionDefinition next={0};next.id=id;next.hole_count=region->hole_count;
    for(size_t l=0;l<=region->hole_count;++l){
        const GeoLoop2View *loop=l?&region->holes[l-1]:&region->outline;
        if(loop->count>GEO_LOOP_MAX_VERTICES||(loop->count&&!loop->v))return false;
        GeoRegionLoop *to=l?&next.holes[l-1]:&next.outline;to->count=loop->count;
        if(loop->count)memcpy(to->v,loop->v,loop->count*sizeof *to->v);
    }
    *out=next;return true;
}
static bool geo_region_key_evaluate(void *opaque,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    GeoRegionKeySources *s=opaque;GeoRegionKeySourceKind kind;uint32_t id,key,axis;
    if(graph!=s->graph||ref->provider!=s->key_token||!geo_region_key_source_decode(ref,&kind,&id,&key,&axis))return false;
    if(kind==GEO_REGION_KEY_SOURCE_LEDGER){
        const GeoRegionKeys *keys=geo_region_keys_find(s->regions,id);if(!keys)return false;
        GeoRegionKeyDefinition *d=geo_region_key_definition(s,id);if(!d)return false;
        size_t size=geo_region_key_ledger_encode(keys,d->content,sizeof d->content);if(!size)return false;d->size=size;
        out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){"geometry.region-key-ledger/1",d->content,d->size};return true;
    }
    GeoRegionKeySourceKey ledger_key;GeoSourceValue ledger;
    if(geo_eval_source(graph,geo_region_key_source_ref(s->key_token,GEO_REGION_KEY_SOURCE_LEDGER,id,0,0,&ledger_key),GEO_DEPENDENCY_DEFINITION_REQUIRED,&ledger)!=GEO_SOURCE_OK)return false;
    if(ledger.kind!=GEO_SOURCE_DEFINITION||strcmp(ledger.as.definition.schema,"geometry.region-key-ledger/1"))return false;
    GeoRegionKeys keys;
    if(!geo_region_key_ledger_decode(ledger.as.definition.content,ledger.as.definition.content_size,&keys)||keys.boundary_id!=id)return false;
    GeoRegionSourceKey region_key;GeoSourceValue region;
    if(geo_eval_source(graph,geo_region_source_ref(s->region_token,id,&region_key),GEO_DEPENDENCY_VALUE_REQUIRED,&region)!=GEO_SOURCE_OK)return false;
    GeoRegionDefinition geometry;
    if(!geo_region_key_geometry(id,&region,&geometry))return false;
    GeoPoint2 point;if(!geo_region_vertex_by_key(&geometry,&keys,key,&point))return false;
    out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){axis?point.v:point.u,1,GEO_UNIT_LENGTH};return true;
}
GeoRegionKeySources *geo_region_key_sources_register(GeoEvalContext *graph,const GeoRegionStore *regions,
    GeoProviderToken token,GeoProviderToken region_token)
{
    if(!graph||!regions||!token||!region_token||token==region_token)return NULL;
    GeoRegionKeySources *s=calloc(1,sizeof *s);if(!s)return NULL;
    s->graph=graph;s->regions=regions;s->key_token=token;s->region_token=region_token;
    GeoSourceProvider provider={token,"core.region-key","geo261-region-key-source/1",s,geo_region_key_describe,geo_region_key_evaluate};
    if(!geo_eval_register(graph,&provider)){free(s);return NULL;}return s;
}
bool geo_region_key_sources_definitions(GeoRegionKeySources *s)
{
    if(!s)return false;
    for(size_t i=0;i<geo_region_keys_count(s->regions);++i){const GeoRegionKeys *keys=geo_region_keys_at(s->regions,i);GeoRegionKeySourceKey key;GeoSourceValue value;
        if(!keys||geo_eval_source(s->graph,geo_region_key_source_ref(s->key_token,GEO_REGION_KEY_SOURCE_LEDGER,keys->boundary_id,0,0,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
    }
    return true;
}
bool geo_region_key_sources_vertex(GeoRegionKeySources *s,uint32_t id,uint32_t key,GeoPoint2 *out)
{
    if(!s)return false;GeoPoint2 next={0};
    for(uint32_t axis=0;axis<2;++axis){GeoRegionKeySourceKey source;GeoSourceValue value;
        if(geo_eval_source(s->graph,geo_region_key_source_ref(s->key_token,GEO_REGION_KEY_SOURCE_COORDINATE,id,key,axis,&source),GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||
            value.kind!=GEO_SOURCE_QUANTITY||value.as.quantity.unit!=GEO_UNIT_LENGTH||value.as.quantity.den!=1)return false;
        if(axis)next.v=value.as.quantity.num;else next.u=value.as.quantity.num;
    }
    if(out)*out=next;return true;
}
void geo_region_key_sources_destroy(GeoRegionKeySources *s)
{
    if(!s)return;GeoRegionKeyDefinition *d=s->definitions;
    while(d){GeoRegionKeyDefinition *next=d->next;free(d);d=next;}free(s);
}
