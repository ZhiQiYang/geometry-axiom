/* H value adapters: persistent geometry lives exclusively in the K stores.
 * These compatibility values are caller-owned scratch or local edit buffers;
 * a scratch pointer is never an authoritative mutation slot. */
static GeoRegionDefinition app_boundary_region_definition(const SpaceBoundarySurface *b)
{
    GeoRegionDefinition region;memset(&region,0,sizeof region);
    if(!b)return region;
    region.id=b->id;region.hole_count=b->hole_count;region.outline.count=b->outline.count;
    size_t count=b->outline.count<POLY_MAX_VERTICES?b->outline.count:POLY_MAX_VERTICES;
    memcpy(region.outline.v,b->outline.v,count*sizeof region.outline.v[0]);
    for(size_t h=0;h<b->hole_count&&h<POLY_MAX_HOLES;++h){
        region.holes[h].count=b->holes[h].count;
        count=b->holes[h].count<POLY_MAX_VERTICES?b->holes[h].count:POLY_MAX_VERTICES;
        memcpy(region.holes[h].v,b->holes[h].v,count*sizeof region.holes[h].v[0]);
    }
    return region;
}
static WoodBoundaryPolicy app_boundary_policy(const SpaceBoundarySurface *b)
{
    WoodBoundaryPolicy p;memset(&p,0,sizeof p);p.id=b->id;p.kind=b->kind;
    for(size_t l=0;l<=b->hole_count&&l<=POLY_MAX_HOLES;++l){
        const PolygonLoop2 *loop=l?&b->holes[l-1]:&b->outline;
        size_t count=loop->count<POLY_MAX_VERTICES?loop->count:POLY_MAX_VERTICES;
        memcpy(p.fixity[l],loop->fixity,count*sizeof p.fixity[l][0]);
    }
    return p;
}
static void app_boundary_compose(const GeoRegionDefinition *region,const WoodBoundaryPolicy *policy,SpaceBoundarySurface *out)
{
    memset(out,0,sizeof *out);out->id=region->id;out->kind=policy->kind;out->hole_count=region->hole_count;
    for(size_t l=0;l<=region->hole_count&&l<=POLY_MAX_HOLES;++l){
        const GeoRegionLoop *from=l?&region->holes[l-1]:&region->outline;
        PolygonLoop2 *to=l?&out->holes[l-1]:&out->outline;to->count=from->count;
        size_t count=from->count<POLY_MAX_VERTICES?from->count:POLY_MAX_VERTICES;
        memcpy(to->v,from->v,count*sizeof to->v[0]);memcpy(to->fixity,policy->fixity[l],count*sizeof to->fixity[0]);
    }
}
static const SpaceBoundarySurface *app_boundary_at(const World *w,size_t index,SpaceBoundarySurface *out)
{
    const GeoRegionDefinition *r=geo_regions_at(&w->geo.region_data,index);if(!r)return NULL;
    app_boundary_compose(r,&w->wood.boundary_policy[index],out);return out;
}
static const SpaceBoundarySurface *app_boundary_read(const World *w,uint32_t id,SpaceBoundarySurface *out)
{
    for(size_t i=0;i<geo_regions_count(&w->geo.region_data);++i)
        if(geo_regions_at(&w->geo.region_data,i)->id==id)return app_boundary_at(w,i,out);
    return NULL;
}
static bool app_boundary_stage(World *w,const SpaceBoundarySurface *value)
{
    size_t at=0;while(at<geo_regions_count(&w->geo.region_data)&&geo_regions_at(&w->geo.region_data,at)->id!=value->id)++at;
    GeoRegionDefinition geometry=app_boundary_region_definition(value);WoodBoundaryPolicy policy=app_boundary_policy(value);
    if(!geo_regions_stage(&w->geo.region_data,&geometry))return false;
    w->wood.boundary_policy[at]=policy;return true;
}
static bool app_boundary_remove(World *w,uint32_t id)
{
    size_t at=0,count=geo_regions_count(&w->geo.region_data);while(at<count&&geo_regions_at(&w->geo.region_data,at)->id!=id)++at;
    if(at==count||!geo_regions_remove(&w->geo.region_data,id))return false;
    memmove(w->wood.boundary_policy+at,w->wood.boundary_policy+at+1,(count-at-1)*sizeof w->wood.boundary_policy[0]);
    memset(w->wood.boundary_policy+count-1,0,sizeof w->wood.boundary_policy[0]);return true;
}
static GeoPlacementDefinition app_placement_definition(const PlacementSurface *p)
{
    GeoPlacementDefinition d;memset(&d,0,sizeof d);d.id=p->id;d.frame=p->frame;
    d.domain=p->derived_fill_id?GEO_PLACEMENT_REGION_SET:p->boundary_id?GEO_PLACEMENT_REGION_REF:GEO_PLACEMENT_RECT;
    d.region_id=p->boundary_id;d.rect=p->rect;d.component_count=p->component_count;
    for(size_t c=0;c<p->component_count&&c<DP_COMPONENT_MAX;++c)d.components[c]=app_boundary_region_definition(&p->components[c]);
    return d;
}
static const PlacementSurface *app_placement_at(const World *w,size_t index,PlacementSurface *out)
{
    const GeoPlacementDefinition *d=geo_placements_at(&w->geo.placement_data,index);if(!d)return NULL;
    const WoodPlacementPolicy *p=&w->wood.placement_policy[index];memset(out,0,sizeof *out);
    out->id=d->id;out->frame=d->frame;out->boundary_id=d->region_id;
    out->rect=d->domain==GEO_PLACEMENT_REGION_REF?w->app.placement_metadata[index].unused_rect:d->rect;
    out->derived_fill_id=p->fill_id;out->derived_h=p->height;out->component_count=d->component_count;
    for(size_t c=0;c<d->component_count&&c<DP_COMPONENT_MAX;++c)app_boundary_compose(&d->components[c],&p->components[c],&out->components[c]);
    return out;
}
static const PlacementSurface *app_placement_read(const World *w,uint32_t id,PlacementSurface *out)
{
    for(size_t i=0;i<geo_placements_count(&w->geo.placement_data);++i)
        if(geo_placements_at(&w->geo.placement_data,i)->id==id)return app_placement_at(w,i,out);
    return NULL;
}
static bool app_placement_stage(World *w,const PlacementSurface *value)
{
    size_t at=0;while(at<geo_placements_count(&w->geo.placement_data)&&geo_placements_at(&w->geo.placement_data,at)->id!=value->id)++at;
    GeoPlacementDefinition d=app_placement_definition(value);WoodPlacementPolicy policy;memset(&policy,0,sizeof policy);
    policy.id=value->id;policy.fill_id=value->derived_fill_id;policy.height=value->derived_h;
    for(size_t c=0;c<value->component_count&&c<DP_COMPONENT_MAX;++c)policy.components[c]=app_boundary_policy(&value->components[c]);
    if(!geo_placements_stage(&w->geo.placement_data,&d))return false;
    w->wood.placement_policy[at]=policy;
    memset(&w->app.placement_metadata[at],0,sizeof w->app.placement_metadata[at]);
    if(d.domain==GEO_PLACEMENT_REGION_REF)w->app.placement_metadata[at].unused_rect=value->rect;
    return true;
}
static bool app_placement_remove(World *w,uint32_t id)
{
    size_t at=0,count=geo_placements_count(&w->geo.placement_data);while(at<count&&geo_placements_at(&w->geo.placement_data,at)->id!=id)++at;
    if(at==count||!geo_placements_remove(&w->geo.placement_data,id))return false;
    memmove(w->wood.placement_policy+at,w->wood.placement_policy+at+1,(count-at-1)*sizeof w->wood.placement_policy[0]);
    memset(w->wood.placement_policy+count-1,0,sizeof w->wood.placement_policy[0]);
    memmove(w->app.placement_metadata+at,w->app.placement_metadata+at+1,(count-at-1)*sizeof w->app.placement_metadata[0]);
    memset(w->app.placement_metadata+count-1,0,sizeof w->app.placement_metadata[0]);return true;
}
#define world_boundary_count(w) geo_regions_count(&(w)->geo.region_data)
#define world_placement_count(w) geo_placements_count(&(w)->geo.placement_data)
#define world_boundary_at(w,i) app_boundary_at((w),(i),&(SpaceBoundarySurface){0})
#define world_placement_at(w,i) app_placement_at((w),(i),&(PlacementSurface){0})
#define world_find_boundary(w,id) app_boundary_read((w),(id),&(SpaceBoundarySurface){0})
#define world_find_placement(w,id) app_placement_read((w),(id),&(PlacementSurface){0})
static const SpaceBoundarySurface *app_placement_boundary(const World *w,const PlacementSurface *p,SpaceBoundarySurface *out)
{
    if(p&&p->derived_fill_id)return p->component_count?&p->components[0]:NULL;
    return !p||!p->boundary_id?NULL:app_boundary_read(w,p->boundary_id,out);
}
#define world_placement_boundary(w,p) app_placement_boundary((w),(p),&(SpaceBoundarySurface){0})
static const PlacementSurface *app_scene_placement_at(const Scene *s,size_t index,PlacementSurface *out)
{return s->domain_world?app_placement_at(s->domain_world,index,out):index<s->placement_count?&s->placements[index]:NULL;}
static const SpaceBoundarySurface *app_scene_boundary_at(const Scene *s,size_t index,SpaceBoundarySurface *out)
{return s->domain_world?app_boundary_at(s->domain_world,index,out):index<s->boundary_count?&s->boundaries[index]:NULL;}
