#include "placement_sources.h"
#include <stdlib.h>
#include <string.h>

typedef struct GeoPlacementDefinitionRecord GeoPlacementDefinitionRecord;
struct GeoPlacementDefinitionRecord {
    uint32_t id;size_t size;
    unsigned char bytes[GEO_PLACEMENT_DEFINITION_MAX_BYTES];
    GeoPlacementDefinition decoded;
    GeoPlacementDefinitionRecord *next;
};
struct GeoPlacementSources {
    GeoEvalContext *graph;const GeoPlacementStore *placements;const GeoRegionStore *regions;
    GeoProviderToken placement_token,region_token;
    GeoPlacementSourceBinding binding;void *user;
    GeoPlacementViewScratch placement_views[GEO_PLACEMENT_CAPACITY];
    GeoLoop2View region_holes[GEO_REGION_CAPACITY][GEO_REGION_MAX_HOLES];
    GeoRegionView region_views[GEO_REGION_CAPACITY];
    GeoPlacementDefinitionRecord *definitions;
};
static GeoPlacementDefinitionRecord *geo_pd_record(GeoPlacementSources *s,uint32_t id)
{
    GeoPlacementDefinitionRecord *record=s->definitions;
    while(record&&record->id!=id)record=record->next;
    if(!record){record=calloc(1,sizeof *record);if(!record)return NULL;record->id=id;record->next=s->definitions;s->definitions=record;}
    return record;
}
static void geo_source_u32(unsigned char *bytes,uint32_t id)
{for(unsigned i=0;i<4;++i)bytes[i]=(unsigned char)(id>>(24-8*i));}
static uint32_t geo_source_read_u32(const unsigned char *bytes)
{uint32_t id=0;for(unsigned i=0;i<4;++i)id=(id<<8)|bytes[i];return id;}
static void geo_pd_put32(unsigned char **p,uint32_t value)
{geo_source_u32(*p,value);*p+=4;}
static void geo_pd_put64(unsigned char **p,GeoCoord value)
{uint64_t bits=(uint64_t)value;for(unsigned i=0;i<8;++i)*(*p)++=(unsigned char)(bits>>(56-8*i));}
static void geo_pd_vector_write(unsigned char **p,GeoVector3 value)
{geo_pd_put64(p,value.x);geo_pd_put64(p,value.y);geo_pd_put64(p,value.z);}
static bool geo_pd_loop_bounded(const GeoRegionLoop *loop)
{return loop->count<=GEO_LOOP_MAX_VERTICES;}
static bool geo_pd_bounded(const GeoPlacementDefinition *p)
{
    if(!p)return false;
    if(p->domain==GEO_PLACEMENT_RECT||p->domain==GEO_PLACEMENT_REGION_REF)return true;
    if(p->domain!=GEO_PLACEMENT_REGION_SET||p->component_count>GEO_PLACEMENT_COMPONENT_CAPACITY)return false;
    for(size_t c=0;c<p->component_count;++c){const GeoRegionDefinition *r=&p->components[c];
        if(!geo_pd_loop_bounded(&r->outline)||r->hole_count>GEO_REGION_MAX_HOLES)return false;
        for(size_t h=0;h<r->hole_count;++h)if(!geo_pd_loop_bounded(&r->holes[h]))return false;
    }return true;
}
static void geo_pd_loop_write(unsigned char **p,const GeoRegionLoop *loop)
{
    geo_pd_put32(p,(uint32_t)loop->count);
    for(size_t v=0;v<loop->count;++v){geo_pd_put64(p,loop->v[v].u);geo_pd_put64(p,loop->v[v].v);}
}
size_t geo_placement_definition_encode(const GeoPlacementDefinition *definition,void *out,size_t capacity)
{
    if(!out||!geo_pd_bounded(definition))return 0;
    unsigned char bytes[GEO_PLACEMENT_DEFINITION_MAX_BYTES],*p=bytes;
    geo_pd_put32(&p,definition->id);
    geo_pd_vector_write(&p,(GeoVector3){definition->frame.origin.x,definition->frame.origin.y,definition->frame.origin.z});
    geo_pd_vector_write(&p,definition->frame.axis_u);geo_pd_vector_write(&p,definition->frame.axis_v);geo_pd_vector_write(&p,definition->frame.normal);
    *p++=(unsigned char)definition->domain;
    if(definition->domain==GEO_PLACEMENT_RECT){
        geo_pd_put64(&p,definition->rect.min_u);geo_pd_put64(&p,definition->rect.min_v);
        geo_pd_put64(&p,definition->rect.max_u);geo_pd_put64(&p,definition->rect.max_v);
    }else if(definition->domain==GEO_PLACEMENT_REGION_REF)geo_pd_put32(&p,definition->region_id);
    else{geo_pd_put32(&p,(uint32_t)definition->component_count);
        for(size_t c=0;c<definition->component_count;++c){const GeoRegionDefinition *r=&definition->components[c];
            geo_pd_put32(&p,r->id);geo_pd_loop_write(&p,&r->outline);geo_pd_put32(&p,(uint32_t)r->hole_count);
            for(size_t h=0;h<r->hole_count;++h)geo_pd_loop_write(&p,&r->holes[h]);
        }
    }
    size_t size=(size_t)(p-bytes);if(size>capacity)return 0;memcpy(out,bytes,size);return size;
}
typedef struct {const unsigned char *p,*end;} GeoPDReader;
static bool geo_pd_read(GeoPDReader *r,unsigned count,uint64_t *out)
{
    if((size_t)(r->end-r->p)<count)return false;
    uint64_t bits=0;for(unsigned i=0;i<count;++i)bits=(bits<<8)|*r->p++;*out=bits;return true;
}
static bool geo_pd_coord_read(GeoPDReader *r,GeoCoord *out)
{uint64_t bits;if(!geo_pd_read(r,8,&bits))return false;*out=bits<=INT64_MAX?(GeoCoord)bits:-1-(GeoCoord)(~bits);return true;}
static bool geo_pd_vector_read(GeoPDReader *r,GeoVector3 *out)
{return geo_pd_coord_read(r,&out->x)&&geo_pd_coord_read(r,&out->y)&&geo_pd_coord_read(r,&out->z);}
static bool geo_pd_loop_read(GeoPDReader *r,GeoRegionLoop *out)
{
    uint64_t count;if(!geo_pd_read(r,4,&count)||count>GEO_LOOP_MAX_VERTICES)return false;
    out->count=(size_t)count;
    for(size_t v=0;v<out->count;++v)if(!geo_pd_coord_read(r,&out->v[v].u)||!geo_pd_coord_read(r,&out->v[v].v))return false;
    return true;
}
bool geo_placement_definition_decode(const void *content,size_t size,GeoPlacementDefinition *out)
{
    if(!content||!out||size>GEO_PLACEMENT_DEFINITION_MAX_BYTES)return false;
    GeoPDReader r={content,(const unsigned char *)content+size};GeoPlacementDefinition next;memset(&next,0,sizeof next);
    uint64_t id,domain,count;GeoVector3 origin;
    if(!geo_pd_read(&r,4,&id)||!geo_pd_vector_read(&r,&origin)||!geo_pd_vector_read(&r,&next.frame.axis_u)||
       !geo_pd_vector_read(&r,&next.frame.axis_v)||!geo_pd_vector_read(&r,&next.frame.normal)||!geo_pd_read(&r,1,&domain)||domain>GEO_PLACEMENT_REGION_SET)return false;
    next.id=(uint32_t)id;next.frame.origin=(GeoPoint3){origin.x,origin.y,origin.z};next.domain=(GeoPlacementDomain)domain;
    if(next.domain==GEO_PLACEMENT_RECT){
        if(!geo_pd_coord_read(&r,&next.rect.min_u)||!geo_pd_coord_read(&r,&next.rect.min_v)||
           !geo_pd_coord_read(&r,&next.rect.max_u)||!geo_pd_coord_read(&r,&next.rect.max_v))return false;
    }else if(next.domain==GEO_PLACEMENT_REGION_REF){if(!geo_pd_read(&r,4,&id))return false;next.region_id=(uint32_t)id;}
    else{if(!geo_pd_read(&r,4,&count)||count>GEO_PLACEMENT_COMPONENT_CAPACITY)return false;next.component_count=(size_t)count;
        for(size_t c=0;c<next.component_count;++c){GeoRegionDefinition *component=&next.components[c];
            if(!geo_pd_read(&r,4,&id)||!geo_pd_loop_read(&r,&component->outline)||!geo_pd_read(&r,4,&count)||count>GEO_REGION_MAX_HOLES)return false;
            component->id=(uint32_t)id;component->hole_count=(size_t)count;
            for(size_t h=0;h<component->hole_count;++h)if(!geo_pd_loop_read(&r,&component->holes[h]))return false;
        }
    }
    if(r.p!=r.end)return false;memcpy(out,&next,sizeof next);return true;
}
/* Header consumers still validate the complete canonical definition. Every
 * coordinate is an unrestricted signed 64-bit bit pattern in the full reader,
 * so bounded skips preserve its accepted set without constructing components. */
static bool geo_pd_skip(GeoPDReader *r,size_t bytes)
{
    if((size_t)(r->end-r->p)<bytes)return false;
    r->p+=bytes;return true;
}
static bool geo_pd_loop_skip(GeoPDReader *r)
{
    uint64_t count;
    if(!geo_pd_read(r,4,&count)||count>GEO_LOOP_MAX_VERTICES)return false;
    return geo_pd_skip(r,(size_t)count*16);
}
static bool geo_pd_definition_header(const void *content,size_t size,uint32_t id,
    GeoPlacementDefinitionHeader *out)
{
    if(!content||!out||size>GEO_PLACEMENT_DEFINITION_MAX_BYTES)return false;
    GeoPDReader r={content,(const unsigned char *)content+size};
    GeoPlacementDefinitionHeader next={0};uint64_t actual,domain,count;
    if(!geo_pd_read(&r,4,&actual)||!geo_pd_skip(&r,12*8)||
       !geo_pd_read(&r,1,&domain)||domain>GEO_PLACEMENT_REGION_SET)return false;
    next.domain=(GeoPlacementDomain)domain;
    if(next.domain==GEO_PLACEMENT_RECT){if(!geo_pd_skip(&r,4*8))return false;}
    else if(next.domain==GEO_PLACEMENT_REGION_REF){
        if(!geo_pd_read(&r,4,&count))return false;next.region_id=(uint32_t)count;
    }else{
        if(!geo_pd_read(&r,4,&count)||count>GEO_PLACEMENT_COMPONENT_CAPACITY)return false;
        size_t components=(size_t)count;
        for(size_t c=0;c<components;++c){
            uint64_t component_id;
            if(!geo_pd_read(&r,4,&component_id)||!geo_pd_loop_skip(&r)||
               !geo_pd_read(&r,4,&count)||count>GEO_REGION_MAX_HOLES)return false;
            size_t holes=(size_t)count;
            for(size_t h=0;h<holes;++h)if(!geo_pd_loop_skip(&r))return false;
        }
    }
    if(r.p!=r.end||actual!=id)return false;*out=next;return true;
}
GeoSourceRef geo_placement_source_ref(GeoProviderToken token,GeoPlacementSourceKind kind,uint32_t id,GeoPlacementSourceKey *key)
{key->bytes[0]=(unsigned char)kind;geo_source_u32(key->bytes+1,id);return (GeoSourceRef){token,key->bytes,sizeof key->bytes};}
GeoSourceRef geo_region_source_ref(GeoProviderToken token,uint32_t id,GeoRegionSourceKey *key)
{geo_source_u32(key->bytes,id);return (GeoSourceRef){token,key->bytes,sizeof key->bytes};}
bool geo_placement_source_decode(const GeoSourceRef *ref,GeoPlacementSourceKind *kind,uint32_t *id)
{
    if(!ref||!ref->key||ref->key_size!=5||!kind||!id)return false;
    const unsigned char *bytes=ref->key;if(bytes[0]<GEO_PLACEMENT_SOURCE_FRAME||bytes[0]>GEO_PLACEMENT_SOURCE_DEFINITION)return false;
    *kind=(GeoPlacementSourceKind)bytes[0];*id=geo_source_read_u32(bytes+1);return true;
}
bool geo_region_source_decode(const GeoSourceRef *ref,uint32_t *id)
{if(!ref||!ref->key||ref->key_size!=4||!id)return false;*id=geo_source_read_u32(ref->key);return true;}
static bool geo_placement_sources_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    GeoPlacementSources *s=opaque;uint32_t id;GeoSourceDescriptor d={0};d.unit=GEO_UNIT_LENGTH;d.context.axis=-1;
    if(ref->provider==s->region_token){
        if(!geo_region_source_decode(ref,&id)||!geo_regions_find(s->regions,id))return false;
        d.kind=GEO_SOURCE_REGION_SET;
    }else if(ref->provider==s->placement_token){
        GeoPlacementSourceKind kind;
        if(!geo_placement_source_decode(ref,&kind,&id)||!geo_placements_find(s->placements,id))return false;
        d.kind=kind==GEO_PLACEMENT_SOURCE_DEFINITION?GEO_SOURCE_DEFINITION:kind==GEO_PLACEMENT_SOURCE_FRAME?GEO_SOURCE_FRAME:GEO_SOURCE_REGION_SET;
        if(kind==GEO_PLACEMENT_SOURCE_DEFINITION)d.unit=GEO_UNIT_SCALAR;
        d.context.has_placement=true;d.context.placement=id;
    }else return false;
    *out=d;return true;
}
static bool geo_placement_sources_evaluate(void *opaque,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    GeoPlacementSources *s=opaque;uint32_t id;if(graph!=s->graph)return false;
    if(ref->provider==s->region_token){
        if(!geo_region_source_decode(ref,&id))return false;
        size_t i=0;const GeoRegionDefinition *r=NULL;
        for(;i<geo_regions_count(s->regions);++i){r=geo_regions_at(s->regions,i);if(r->id==id)break;}
        if(i==geo_regions_count(s->regions)||i>=GEO_REGION_CAPACITY)return false;
        for(size_t h=0;h<r->hole_count;++h)s->region_holes[i][h]=(GeoLoop2View){r->holes[h].v,r->holes[h].count};
        s->region_views[i]=(GeoRegionView){{r->outline.v,r->outline.count},s->region_holes[i],r->hole_count};
        out->kind=GEO_SOURCE_REGION_SET;out->as.regions=(GeoRegionSetView){&s->region_views[i],1};return true;
    }
    GeoPlacementSourceKind kind;
    if(ref->provider!=s->placement_token||!geo_placement_source_decode(ref,&kind,&id))return false;
    size_t i=0;const GeoPlacementDefinition *p=NULL;
    for(;i<geo_placements_count(s->placements);++i){p=geo_placements_at(s->placements,i);if(p->id==id)break;}
    if(i==geo_placements_count(s->placements)||i>=GEO_PLACEMENT_CAPACITY)return false;
    GeoSourceRef upstream;
    if(s->binding&&s->binding(s->user,id,kind,&upstream))
        return geo_eval_source(graph,upstream,kind==GEO_PLACEMENT_SOURCE_DEFINITION?GEO_DEPENDENCY_DEFINITION_REQUIRED:GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;
    if(kind==GEO_PLACEMENT_SOURCE_DEFINITION){
        GeoPlacementDefinitionRecord *record=geo_pd_record(s,id);if(!record)return false;
        record->size=geo_placement_definition_encode(p,record->bytes,sizeof record->bytes);if(!record->size)return false;
        out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){GEO_PLACEMENT_DEFINITION_SCHEMA,record->bytes,record->size};return true;
    }
    /* Explicit upstream geometry retains its existing evaluation order above.
     * Local geometry reads the same candidate's actual canonical definition;
     * region views must never borrow this evaluator's stack-local decode. */
    GeoPlacementDefinition decoded;
    if(!geo_placement_sources_definition(s,id,&decoded))return false;
    GeoPlacementDefinitionRecord *record=geo_pd_record(s,id);if(!record)return false;
    memcpy(&record->decoded,&decoded,sizeof decoded);p=&record->decoded;
    if(kind==GEO_PLACEMENT_SOURCE_FRAME){out->kind=GEO_SOURCE_FRAME;out->as.frame=p->frame;return true;}
    if(p->domain==GEO_PLACEMENT_REGION_REF){GeoRegionSourceKey key;
        return geo_eval_source(graph,geo_region_source_ref(s->region_token,p->region_id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;
    }
    out->kind=GEO_SOURCE_REGION_SET;
    return geo_placement_domain_view(p,s->regions,&s->placement_views[i],&out->as.regions);
}
GeoPlacementSources *geo_placement_sources_register(GeoEvalContext *graph,const GeoPlacementStore *placements,const GeoRegionStore *regions,
    GeoProviderToken placement_token,GeoProviderToken region_token,GeoPlacementSourceBinding binding,void *user)
{
    if(!graph||!placements||!regions||!placement_token||!region_token||placement_token==region_token)return NULL;
    GeoPlacementSources *s=calloc(1,sizeof *s);if(!s)return NULL;
    s->graph=graph;s->placements=placements;s->regions=regions;s->placement_token=placement_token;s->region_token=region_token;s->binding=binding;s->user=user;
    GeoSourceProvider providers[]={
        {region_token,"core.region","geo261-region-source/1",s,geo_placement_sources_describe,geo_placement_sources_evaluate},
        {placement_token,"core.placement","geo261-placement-source/1",s,geo_placement_sources_describe,geo_placement_sources_evaluate}};
    if(!geo_eval_register_many(graph,providers,2)){free(s);return NULL;}
    return s;
}
bool geo_placement_sources_definition(GeoPlacementSources *s,uint32_t id,GeoPlacementDefinition *out)
{
    if(!s||!out)return false;GeoPlacementSourceKey key;GeoSourceValue value;GeoPlacementDefinition result;
    if(geo_eval_source(s->graph,geo_placement_source_ref(s->placement_token,GEO_PLACEMENT_SOURCE_DEFINITION,id,&key),
        GEO_DEPENDENCY_DEFINITION_REQUIRED,&value)!=GEO_SOURCE_OK||value.kind!=GEO_SOURCE_DEFINITION||
        !value.as.definition.schema||strcmp(value.as.definition.schema,GEO_PLACEMENT_DEFINITION_SCHEMA)||
        !geo_placement_definition_decode(value.as.definition.content,value.as.definition.content_size,&result)||result.id!=id)return false;
    memcpy(out,&result,sizeof result);return true;
}
bool geo_placement_sources_definition_header(GeoPlacementSources *s,uint32_t id,GeoPlacementDefinitionHeader *out)
{
    if(!s||!out)return false;GeoPlacementSourceKey key;GeoSourceValue value;GeoPlacementDefinitionHeader result;
    if(geo_eval_source(s->graph,geo_placement_source_ref(s->placement_token,GEO_PLACEMENT_SOURCE_DEFINITION,id,&key),
        GEO_DEPENDENCY_DEFINITION_REQUIRED,&value)!=GEO_SOURCE_OK||value.kind!=GEO_SOURCE_DEFINITION||
        !value.as.definition.schema||strcmp(value.as.definition.schema,GEO_PLACEMENT_DEFINITION_SCHEMA)||
        !geo_pd_definition_header(value.as.definition.content,value.as.definition.content_size,id,&result))return false;
    *out=result;return true;
}
void geo_placement_sources_destroy(GeoPlacementSources *sources)
{
    if(sources){GeoPlacementDefinitionRecord *record=sources->definitions;
        while(record){GeoPlacementDefinitionRecord *next=record->next;free(record);record=next;}free(sources);}
}
