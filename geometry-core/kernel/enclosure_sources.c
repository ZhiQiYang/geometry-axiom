#include "enclosure_sources.h"
#include <stdlib.h>
#include <string.h>

enum { GEO_ENCLOSURE_MEMBERS_BYTES=8+4*GEO_ENCLOSURE_MEMBER_CAPACITY,
       GEO_ENCLOSURE_RESULT_BYTES=GEO_ENCLOSURE_MEMBERS_BYTES+49 };
struct GeoEnclosureSources {
    GeoEvalContext *graph;
    const GeoEnclosureStore *enclosures;
    const GeoRegionStore *regions;
    const GeoPlacementStore *placements;
    GeoProviderToken token,placement_token,region_token;
    unsigned char definitions[GEO_ENCLOSURE_CAPACITY][GEO_ENCLOSURE_MEMBERS_BYTES];
    unsigned char results[GEO_ENCLOSURE_CAPACITY][GEO_ENCLOSURE_RESULT_BYTES];
    GeoEnclosure values[GEO_ENCLOSURE_CAPACITY];
    GeoEnclosureFault faults[GEO_ENCLOSURE_CAPACITY];
    bool has_fault[GEO_ENCLOSURE_CAPACITY];
};
static void geo_enclosure_source_u32(unsigned char *bytes,uint32_t value)
{for(unsigned i=0;i<4;++i)bytes[i]=(unsigned char)(value>>(24-8*i));}
static uint32_t geo_enclosure_source_read_u32(const unsigned char *bytes)
{uint32_t value=0;for(unsigned i=0;i<4;++i)value=(value<<8)|bytes[i];return value;}
static void geo_enclosure_source_i64(unsigned char *bytes,GeoCoord value)
{uint64_t bits=(uint64_t)value;for(unsigned i=0;i<8;++i)bytes[i]=(unsigned char)(bits>>(56-8*i));}
static bool geo_enclosure_source_indices(GeoEnclosureSourceKind kind,int axis,int slot)
{
    if(kind==GEO_ENCLOSURE_SOURCE_DEFINITION||kind==GEO_ENCLOSURE_SOURCE_RESULT)return axis==-1&&slot==-1;
    return kind==GEO_ENCLOSURE_SOURCE_AXIS_BOUND&&axis>=0&&axis<=2&&slot>=0&&slot<=1;
}
GeoSourceRef geo_enclosure_source_ref(GeoProviderToken token,GeoEnclosureSourceKind kind,uint32_t id,
    int axis,int slot,GeoEnclosureSourceKey *key)
{
    if(!key||!geo_enclosure_source_indices(kind,axis,slot))return (GeoSourceRef){token,NULL,0};
    key->bytes[0]=(unsigned char)kind;geo_enclosure_source_u32(key->bytes+1,id);
    key->bytes[5]=(unsigned char)(axis+1);key->bytes[6]=(unsigned char)(slot+1);
    return (GeoSourceRef){token,key->bytes,sizeof key->bytes};
}
bool geo_enclosure_source_decode(const GeoSourceRef *ref,GeoEnclosureSourceKind *kind,uint32_t *id,int *axis,int *slot)
{
    if(!ref||!ref->key||ref->key_size!=7||!kind||!id||!axis||!slot)return false;
    const unsigned char *bytes=ref->key;GeoEnclosureSourceKind k=(GeoEnclosureSourceKind)bytes[0];
    int a=(int)bytes[5]-1,b=(int)bytes[6]-1;
    if(!geo_enclosure_source_indices(k,a,b))return false;
    *kind=k;*id=geo_enclosure_source_read_u32(bytes+1);*axis=a;*slot=b;return true;
}
static size_t geo_enclosure_source_index(const GeoEnclosureSources *s,uint32_t id)
{
    for(size_t i=0;i<geo_enclosures_count(s->enclosures)&&i<GEO_ENCLOSURE_CAPACITY;++i){
        const GeoEnclosure *value=geo_enclosures_at(s->enclosures,i);
        if(value&&value->id==id)return i;
    }
    return GEO_ENCLOSURE_CAPACITY;
}
static size_t geo_enclosure_source_members(unsigned char *bytes,const GeoEnclosure *value)
{
    geo_enclosure_source_u32(bytes,value->id);
    geo_enclosure_source_u32(bytes+4,(uint32_t)value->member_count);
    for(size_t i=0;i<value->member_count;++i)geo_enclosure_source_u32(bytes+8+4*i,value->member_ids[i]);
    return 8+4*value->member_count;
}
static bool geo_enclosure_sources_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    GeoEnclosureSources *s=opaque;GeoEnclosureSourceKind kind;uint32_t id;int axis,slot;
    if(ref->provider!=s->token||!geo_enclosure_source_decode(ref,&kind,&id,&axis,&slot))return false;
    size_t at=geo_enclosure_source_index(s,id);if(at==GEO_ENCLOSURE_CAPACITY)return false;
    const GeoEnclosure *value=geo_enclosures_at(s->enclosures,at);
    if(value->member_count>GEO_ENCLOSURE_MEMBER_CAPACITY)return false;
    GeoSourceDescriptor next={0};next.unit=kind==GEO_ENCLOSURE_SOURCE_AXIS_BOUND?GEO_UNIT_LENGTH:GEO_UNIT_SCALAR;next.context.axis=axis;
    next.kind=kind==GEO_ENCLOSURE_SOURCE_AXIS_BOUND?GEO_SOURCE_AXIS_POSITION:GEO_SOURCE_DEFINITION;
    *out=next;return true;
}
static bool geo_enclosure_source_frame(GeoEnclosureSources *s,const GeoPlacementDefinition *source,GeoPlacementStore *target)
{
    GeoPlacementSourceKey key;GeoSourceValue value;
    if(geo_eval_source(s->graph,geo_placement_source_ref(s->placement_token,GEO_PLACEMENT_SOURCE_FRAME,source->id,&key),
        GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||value.kind!=GEO_SOURCE_FRAME||!geo_frame_is_valid(&value.as.frame))return false;
    GeoPlacementDefinition next=*source;next.frame=value.as.frame;
    return geo_placements_stage(target,&next);
}
static bool geo_enclosure_source_region(GeoEnclosureSources *s,uint32_t id,GeoRegionStore *target)
{
    GeoRegionSourceKey key;GeoSourceValue value;
    if(geo_eval_source(s->graph,geo_region_source_ref(s->region_token,id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||
        value.kind!=GEO_SOURCE_REGION_SET||value.as.regions.count!=1||!value.as.regions.regions)return false;
    const GeoRegionView *view=value.as.regions.regions;
    if(view->outline.count>GEO_LOOP_MAX_VERTICES||!view->outline.v||view->hole_count>GEO_REGION_MAX_HOLES||
        (view->hole_count&&!view->holes))return false;
    GeoRegionDefinition next={0};next.id=id;next.outline.count=view->outline.count;
    memcpy(next.outline.v,view->outline.v,view->outline.count*sizeof next.outline.v[0]);next.hole_count=view->hole_count;
    for(size_t h=0;h<view->hole_count;++h){
        if(view->holes[h].count>GEO_LOOP_MAX_VERTICES||!view->holes[h].v)return false;
        next.holes[h].count=view->holes[h].count;
        memcpy(next.holes[h].v,view->holes[h].v,view->holes[h].count*sizeof next.holes[h].v[0]);
    }
    return geo_regions_put(target,&next);
}
static bool geo_enclosure_source_fault(GeoEnclosureSources *s,size_t at,GeoEnclosureFault fault)
{s->faults[at]=fault;s->has_fault[at]=true;return false;}
static const GeoPlacementDefinition *geo_enclosure_source_carrier(GeoEnclosureSources *s,
    const GeoEnclosure *definition,size_t member_index,GeoEnclosureFault *fault)
{
    uint32_t member=definition->member_ids[member_index];
    *fault=(GeoEnclosureFault){GEO_ENCLOSURE_FAULT_NONE,member,-1};
    /* These identity checks precede all geometry in enclosure_evaluate. They
     * cannot inspect raw frame/outline caches: only typed values are validated
     * below, and an input candidate may still contain invalid geometry. */
    if(!geo_regions_find(s->regions,member)){fault->kind=GEO_ENCLOSURE_FAULT_MISSING_REGION;return NULL;}
    for(size_t i=0;i<member_index;++i)if(definition->member_ids[i]==member){
        fault->kind=GEO_ENCLOSURE_FAULT_DUPLICATE_REGION;return NULL;
    }
    size_t count=0;const GeoPlacementDefinition *carrier=NULL;
    for(size_t p=0;p<geo_placements_count(s->placements);++p){
        const GeoPlacementDefinition *candidate=geo_placements_at(s->placements,p);
        if(candidate->domain==GEO_PLACEMENT_REGION_REF&&candidate->region_id==member){carrier=candidate;++count;}
    }
    if(count!=1){fault->kind=count?GEO_ENCLOSURE_FAULT_AMBIGUOUS_CARRIER:GEO_ENCLOSURE_FAULT_NO_CARRIER;return NULL;}
    return carrier;
}
static bool geo_enclosure_source_result(GeoEnclosureSources *s,size_t at)
{
    const GeoEnclosure *definition=geo_enclosures_at(s->enclosures,at);
    s->has_fault[at]=false;
    GeoRegionStore *regions=geo_regions_clone(s->regions);
    GeoPlacementStore *placements=geo_placements_clone(s->placements);
    if(!regions||!placements){geo_regions_destroy(regions);geo_placements_destroy(placements);return false;}
    bool ok=false;GeoEnclosure next;GeoEnclosureFault fault;
    for(size_t i=0;i<definition->member_count;++i){
        const GeoPlacementDefinition *carrier=geo_enclosure_source_carrier(s,definition,i,&fault);
        if(!carrier){geo_enclosure_source_fault(s,at,fault);goto done;}
        if(!geo_enclosure_source_frame(s,carrier,placements))goto done;
        /* A valid placeholder lets the existing evaluator check its slot
         * rule without reading this member's unresolved outline. Only that
         * early fault is observable; this temporary extent is never published. */
        GeoRegionDefinition placeholder={0};placeholder.id=definition->member_ids[i];placeholder.outline.count=4;
        placeholder.outline.v[0]=(GeoPoint2){0,0};placeholder.outline.v[1]=(GeoPoint2){1,0};
        placeholder.outline.v[2]=(GeoPoint2){1,1};placeholder.outline.v[3]=(GeoPoint2){0,1};
        if(!geo_regions_put(regions,&placeholder))goto done;
        bool prefix=geo_enclosure_evaluate(regions,placements,definition->id,definition->member_ids,i+1,&next,&fault);
        /* A duplicate normal slot precedes this member's outline/extent read. */
        if(!prefix&&fault.kind<=GEO_ENCLOSURE_FAULT_SLOT_TAKEN){geo_enclosure_source_fault(s,at,fault);goto done;}
        if(!geo_enclosure_source_region(s,definition->member_ids[i],regions))goto done;
        prefix=geo_enclosure_evaluate(regions,placements,definition->id,definition->member_ids,i+1,&next,&fault);
        /* Plane/inversion checks belong to the complete member list. Earlier
         * member-local faults still win over every later upstream failure. */
        if(!prefix&&fault.kind!=GEO_ENCLOSURE_FAULT_PLANE_MISMATCH&&fault.kind!=GEO_ENCLOSURE_FAULT_INVERTED){
            geo_enclosure_source_fault(s,at,fault);goto done;
        }
    }
    if(!geo_enclosure_evaluate(regions,placements,definition->id,definition->member_ids,definition->member_count,&next,&fault)){
        geo_enclosure_source_fault(s,at,fault);goto done;
    }
    memcpy(&s->values[at],&next,sizeof next);ok=true;
done:
    geo_regions_destroy(regions);geo_placements_destroy(placements);return ok;
}
static bool geo_enclosure_source_axis(GeoEnclosureSources *s,size_t at,int axis,int slot,GeoCoord *out)
{
    const GeoEnclosure *definition=geo_enclosures_at(s->enclosures,at);
    GeoPlacementStore *placements=geo_placements_create();if(!placements)return false;
    bool ok=false;GeoCoord next;
    for(size_t i=0;i<definition->member_count;++i)for(size_t p=0;p<geo_placements_count(s->placements);++p){
        const GeoPlacementDefinition *candidate=geo_placements_at(s->placements,p);
        if(candidate->domain!=GEO_PLACEMENT_REGION_REF||candidate->region_id!=definition->member_ids[i])continue;
        if(!geo_enclosure_source_frame(s,candidate,placements))goto done;
        if(geo_enclosure_axis_bound(placements,definition,axis,slot,&next)){*out=next;ok=true;goto done;}
    }
done:
    geo_placements_destroy(placements);return ok;
}
static bool geo_enclosure_sources_evaluate(void *opaque,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    GeoEnclosureSources *s=opaque;GeoEnclosureSourceKind kind;uint32_t id;int axis,slot;
    if(graph!=s->graph||ref->provider!=s->token||!geo_enclosure_source_decode(ref,&kind,&id,&axis,&slot))return false;
    size_t at=geo_enclosure_source_index(s,id);if(at==GEO_ENCLOSURE_CAPACITY)return false;
    const GeoEnclosure *definition=geo_enclosures_at(s->enclosures,at);
    if(kind==GEO_ENCLOSURE_SOURCE_DEFINITION){
        size_t size=geo_enclosure_source_members(s->definitions[at],definition);
        out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){"geo.enclosure.members/1",s->definitions[at],size};return true;
    }
    if(kind==GEO_ENCLOSURE_SOURCE_RESULT)s->has_fault[at]=false;
    GeoEnclosureSourceKey key;
    if(geo_eval_depend(graph,geo_enclosure_source_ref(s->token,GEO_ENCLOSURE_SOURCE_DEFINITION,id,-1,-1,&key),
        GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)return false;
    if(kind==GEO_ENCLOSURE_SOURCE_AXIS_BOUND){
        GeoCoord coordinate;if(!geo_enclosure_source_axis(s,at,axis,slot,&coordinate))return false;
        out->kind=GEO_SOURCE_AXIS_POSITION;out->as.position=(GeoAxisPosition){coordinate,{false,0,axis}};return true;
    }
    if(!geo_enclosure_source_result(s,at))return false;
    const GeoEnclosure *value=&s->values[at];size_t size=geo_enclosure_source_members(s->results[at],value);
    for(int a=0;a<3;++a){geo_enclosure_source_i64(s->results[at]+size,value->min[a]);size+=8;}
    for(int a=0;a<3;++a){geo_enclosure_source_i64(s->results[at]+size,value->max[a]);size+=8;}
    s->results[at][size++]=value->closed?1:0;
    out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){"geo.enclosure.result/1",s->results[at],size};return true;
}
GeoEnclosureSources *geo_enclosure_sources_register(GeoEvalContext *graph,const GeoEnclosureStore *enclosures,
    const GeoRegionStore *regions,const GeoPlacementStore *placements,GeoProviderToken token,GeoProviderToken placement_token,GeoProviderToken region_token)
{
    if(!graph||!enclosures||!regions||!placements||!token||!placement_token||!region_token||
        token==placement_token||token==region_token||placement_token==region_token)return NULL;
    GeoEnclosureSources *s=calloc(1,sizeof *s);if(!s)return NULL;
    s->graph=graph;s->enclosures=enclosures;s->regions=regions;s->placements=placements;
    s->token=token;s->placement_token=placement_token;s->region_token=region_token;
    GeoSourceProvider provider={token,"core.enclosure","geo261-enclosure-source/1",s,geo_enclosure_sources_describe,geo_enclosure_sources_evaluate};
    if(!geo_eval_register(graph,&provider)){free(s);return NULL;}return s;
}
void geo_enclosure_sources_destroy(GeoEnclosureSources *s){free(s);}
size_t geo_enclosure_sources_count(const GeoEnclosureSources *s)
{return s?geo_enclosures_count(s->enclosures):0;}
const GeoEnclosure *geo_enclosure_sources_at(const GeoEnclosureSources *s,size_t at)
{return s?geo_enclosures_at(s->enclosures,at):NULL;}
bool geo_enclosure_sources_value(GeoEnclosureSources *s,uint32_t id,GeoEnclosure *out,GeoEnclosureFault *fault)
{
    if(!s||!out)return false;size_t at=geo_enclosure_source_index(s,id);if(at==GEO_ENCLOSURE_CAPACITY)return false;
    GeoEnclosureSourceKey key;GeoSourceValue value;
    GeoSourceStatus status=geo_eval_source(s->graph,geo_enclosure_source_ref(s->token,GEO_ENCLOSURE_SOURCE_RESULT,id,-1,-1,&key),
        GEO_DEPENDENCY_VALUE_REQUIRED,&value);
    if(status!=GEO_SOURCE_OK){if(status==GEO_SOURCE_FAILED&&fault&&s->has_fault[at])*fault=s->faults[at];return false;}
    memcpy(out,&s->values[at],sizeof *out);return true;
}
bool geo_enclosure_sources_axis_bound(GeoEnclosureSources *s,uint32_t id,int axis,int slot,GeoCoord *out)
{
    if(!s||!out)return false;GeoEnclosureSourceKey key;GeoSourceValue value;
    if(geo_eval_source(s->graph,geo_enclosure_source_ref(s->token,GEO_ENCLOSURE_SOURCE_AXIS_BOUND,id,axis,slot,&key),
        GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
    *out=value.as.position.coordinate;return true;
}
