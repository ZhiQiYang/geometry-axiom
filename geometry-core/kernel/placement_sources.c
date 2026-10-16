#include "placement_sources.h"
#include <stdlib.h>
#include <string.h>

struct GeoPlacementSources {
    GeoEvalContext *graph;const GeoPlacementStore *placements;const GeoRegionStore *regions;
    GeoProviderToken placement_token,region_token;
    GeoPlacementSourceBinding binding;void *user;
    GeoPlacementViewScratch placement_views[GEO_PLACEMENT_CAPACITY];
    GeoLoop2View region_holes[GEO_REGION_CAPACITY][GEO_REGION_MAX_HOLES];
    GeoRegionView region_views[GEO_REGION_CAPACITY];
};
static void geo_source_u32(unsigned char *bytes,uint32_t id)
{for(unsigned i=0;i<4;++i)bytes[i]=(unsigned char)(id>>(24-8*i));}
static uint32_t geo_source_read_u32(const unsigned char *bytes)
{uint32_t id=0;for(unsigned i=0;i<4;++i)id=(id<<8)|bytes[i];return id;}
GeoSourceRef geo_placement_source_ref(GeoProviderToken token,GeoPlacementSourceKind kind,uint32_t id,GeoPlacementSourceKey *key)
{key->bytes[0]=(unsigned char)kind;geo_source_u32(key->bytes+1,id);return (GeoSourceRef){token,key->bytes,sizeof key->bytes};}
GeoSourceRef geo_region_source_ref(GeoProviderToken token,uint32_t id,GeoRegionSourceKey *key)
{geo_source_u32(key->bytes,id);return (GeoSourceRef){token,key->bytes,sizeof key->bytes};}
bool geo_placement_source_decode(const GeoSourceRef *ref,GeoPlacementSourceKind *kind,uint32_t *id)
{
    if(!ref||!ref->key||ref->key_size!=5||!kind||!id)return false;
    const unsigned char *bytes=ref->key;if(bytes[0]<GEO_PLACEMENT_SOURCE_FRAME||bytes[0]>GEO_PLACEMENT_SOURCE_REGIONS)return false;
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
        d.kind=kind==GEO_PLACEMENT_SOURCE_FRAME?GEO_SOURCE_FRAME:GEO_SOURCE_REGION_SET;
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
        return geo_eval_source(graph,upstream,GEO_DEPENDENCY_VALUE_REQUIRED,out)==GEO_SOURCE_OK;
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
void geo_placement_sources_destroy(GeoPlacementSources *sources){free(sources);}
