#include "internal/placements.h"
#include <stdlib.h>
#include <string.h>

static bool placement_region_structure(const GeoRegionDefinition *region)
{
    if (region->hole_count > GEO_REGION_MAX_HOLES || region->outline.count > GEO_LOOP_MAX_VERTICES) return false;
    for (size_t h=0;h<region->hole_count;++h)
        if (region->holes[h].count > GEO_LOOP_MAX_VERTICES) return false;
    return true;
}

static bool placement_structure(const GeoPlacementDefinition *definition)
{
    if (!definition) return false;
    switch (definition->domain) {
    case GEO_PLACEMENT_RECT:
    case GEO_PLACEMENT_REGION_REF:
        return true;
    case GEO_PLACEMENT_REGION_SET:
        if (definition->component_count > GEO_PLACEMENT_COMPONENT_CAPACITY) return false;
        for (size_t c=0;c<definition->component_count;++c)
            if (!placement_region_structure(&definition->components[c])) return false;
        return true;
    }
    return false;
}

static GeoRegionView placement_region_view(const GeoRegionDefinition *region,GeoLoop2View *holes)
{
    for (size_t h=0;h<region->hole_count;++h)
        holes[h]=(GeoLoop2View){region->holes[h].v,region->holes[h].count};
    return (GeoRegionView){{region->outline.v,region->outline.count},holes,region->hole_count};
}

static void placement_copy_region(GeoRegionDefinition *to,const GeoRegionDefinition *from)
{
    to->id=from->id;
    to->outline.count=from->outline.count;
    memcpy(to->outline.v,from->outline.v,from->outline.count*sizeof *from->outline.v);
    to->hole_count=from->hole_count;
    for (size_t h=0;h<from->hole_count;++h) {
        to->holes[h].count=from->holes[h].count;
        memcpy(to->holes[h].v,from->holes[h].v,from->holes[h].count*sizeof *from->holes[h].v);
    }
}

GeoPlacementStore *geo_placements_create(void) { return calloc(1,sizeof(GeoPlacementStore)); }
GeoPlacementStore *geo_placements_clone(const GeoPlacementStore *source)
{
    if (!source) return NULL;
    GeoPlacementStore *copy=malloc(sizeof *copy);
    if (copy) memcpy(copy,source,sizeof *copy);
    return copy;
}
void geo_placements_destroy(GeoPlacementStore *store) { free(store); }
size_t geo_placements_count(const GeoPlacementStore *store) { return store ? store->count : 0; }
const GeoPlacementDefinition *geo_placements_at(const GeoPlacementStore *store,size_t index)
{
    return store && index<store->count && index<GEO_PLACEMENT_CAPACITY ? &store->items[index] : NULL;
}
const GeoPlacementDefinition *geo_placements_find(const GeoPlacementStore *store,uint32_t id)
{
    if (!store || store->count>GEO_PLACEMENT_CAPACITY) return NULL;
    for (size_t i=0;i<store->count;++i) if (store->items[i].id==id) return &store->items[i];
    return NULL;
}

bool geo_placements_stage(GeoPlacementStore *store,const GeoPlacementDefinition *definition)
{
    if (!store || store->count>GEO_PLACEMENT_CAPACITY || !placement_structure(definition)) return false;
    size_t at=0;
    while (at<store->count && store->items[at].id!=definition->id) ++at;
    if (at>=GEO_PLACEMENT_CAPACITY) return false;
    /* Snapshot before mutation: definition may alias the slot being replaced.
     * Inactive fields, array tails and padding all remain zero. */
    GeoPlacementDefinition next;
    memset(&next,0,sizeof next);
    next.id=definition->id;
    next.frame=definition->frame;
    next.domain=definition->domain;
    switch (definition->domain) {
    case GEO_PLACEMENT_RECT:
        next.rect=definition->rect;
        break;
    case GEO_PLACEMENT_REGION_REF:
        next.region_id=definition->region_id;
        break;
    case GEO_PLACEMENT_REGION_SET:
        next.component_count=definition->component_count;
        for (size_t c=0;c<next.component_count;++c)
            placement_copy_region(&next.components[c],&definition->components[c]);
        break;
    }
    memcpy(&store->items[at],&next,sizeof next);
    if (at==store->count) ++store->count;
    return true;
}

bool geo_placement_is_valid(const GeoPlacementDefinition *definition,const GeoRegionStore *regions)
{
    if (!placement_structure(definition) || !geo_frame_is_valid(&definition->frame)) return false;
    if (definition->domain==GEO_PLACEMENT_RECT) {
        const GeoRect2 *rect=&definition->rect;
        return geo_coord_in_range(rect->min_u) && geo_coord_in_range(rect->min_v) &&
               geo_coord_in_range(rect->max_u) && geo_coord_in_range(rect->max_v) &&
               rect->min_u<rect->max_u && rect->min_v<rect->max_v;
    }
    if (definition->domain==GEO_PLACEMENT_REGION_REF) {
        const GeoRegionDefinition *region=geo_regions_find(regions,definition->region_id);
        if (!region || !placement_region_structure(region)) return false;
        GeoLoop2View holes[GEO_REGION_MAX_HOLES];
        GeoRegionView view=placement_region_view(region,holes);
        return geo_region_is_valid(&view);
    }
    for (size_t c=0;c<definition->component_count;++c) {
        GeoLoop2View holes[GEO_REGION_MAX_HOLES];
        GeoRegionView view=placement_region_view(&definition->components[c],holes);
        if (!geo_region_is_valid(&view)) return false;
    }
    return true;
}

bool geo_placements_put(GeoPlacementStore *store,const GeoPlacementDefinition *definition,const GeoRegionStore *regions)
{
    return geo_placement_is_valid(definition,regions) && geo_placements_stage(store,definition);
}

bool geo_placements_remove(GeoPlacementStore *store,uint32_t id)
{
    if (!store || store->count>GEO_PLACEMENT_CAPACITY) return false;
    size_t at=0;
    while (at<store->count && store->items[at].id!=id) ++at;
    if (at==store->count) return false;
    memmove(store->items+at,store->items+at+1,(store->count-at-1)*sizeof *store->items);
    memset(&store->items[--store->count],0,sizeof *store->items);
    return true;
}

bool geo_placement_domain_view(const GeoPlacementDefinition *definition,const GeoRegionStore *regions,
    GeoPlacementViewScratch *scratch,GeoRegionSetView *out)
{
    if (!out) return false;
    *out=(GeoRegionSetView){NULL,0};
    if (!scratch || !placement_structure(definition)) return false;
    memset(scratch,0,sizeof *scratch);
    size_t count=0;
    switch (definition->domain) {
    case GEO_PLACEMENT_RECT: {
        const GeoRect2 *r=&definition->rect;
        scratch->rectangle[0]=(GeoPoint2){r->min_u,r->min_v};
        scratch->rectangle[1]=(GeoPoint2){r->max_u,r->min_v};
        scratch->rectangle[2]=(GeoPoint2){r->max_u,r->max_v};
        scratch->rectangle[3]=(GeoPoint2){r->min_u,r->max_v};
        scratch->regions[0]=(GeoRegionView){{scratch->rectangle,4},NULL,0};
        count=1;
        break;
    }
    case GEO_PLACEMENT_REGION_REF: {
        const GeoRegionDefinition *region=geo_regions_find(regions,definition->region_id);
        if (!region || !placement_region_structure(region)) return false;
        scratch->regions[0]=placement_region_view(region,scratch->holes[0]);
        count=1;
        break;
    }
    case GEO_PLACEMENT_REGION_SET:
        count=definition->component_count;
        for (size_t c=0;c<count;++c)
            scratch->regions[c]=placement_region_view(&definition->components[c],scratch->holes[c]);
        break;
    }
    *out=(GeoRegionSetView){scratch->regions,count};
    return true;
}

bool geo_placement_contains_point(const GeoPlacementDefinition *definition,const GeoRegionStore *regions,GeoPoint2 point)
{
    if (!definition) return false;
    if (definition->domain==GEO_PLACEMENT_RECT)
        return point.u>=definition->rect.min_u && point.u<=definition->rect.max_u &&
               point.v>=definition->rect.min_v && point.v<=definition->rect.max_v;
    GeoPlacementViewScratch scratch;GeoRegionSetView domain;
    if (!geo_placement_domain_view(definition,regions,&scratch,&domain)) return false;
    for (size_t c=0;c<domain.count;++c)
        if (geo_region_contains_point(&domain.regions[c],point)) return true;
    return false;
}

bool geo_placement_component_for_rect(const GeoPlacementDefinition *definition,const GeoRegionStore *regions,
    const GeoRect2 *rect,size_t *index)
{
    if (!definition || !rect) return false;
    if (definition->domain==GEO_PLACEMENT_RECT) {
        if (rect->min_u>=definition->rect.min_u && rect->max_u<=definition->rect.max_u &&
            rect->min_v>=definition->rect.min_v && rect->max_v<=definition->rect.max_v) {
            if (index) *index=0;
            return true;
        }
        return false;
    }
    GeoPlacementViewScratch scratch;GeoRegionSetView domain;
    if (!geo_placement_domain_view(definition,regions,&scratch,&domain)) return false;
    for (size_t c=0;c<domain.count;++c)
        if (geo_region_contains_rect(&domain.regions[c],rect->min_u,rect->min_v,rect->max_u,rect->max_v)) {
            if (index) *index=c;
            return true;
        }
    return false;
}

bool geo_placement_contains_rect(const GeoPlacementDefinition *definition,const GeoRegionStore *regions,const GeoRect2 *rect)
{
    return geo_placement_component_for_rect(definition,regions,rect,NULL);
}

bool geo_placement_local_bounds(const GeoPlacementDefinition *definition,const GeoRegionStore *regions,GeoRect2 *out)
{
    if (!definition || !out) return false;
    if (definition->domain==GEO_PLACEMENT_RECT) {
        if (definition->rect.min_u>=definition->rect.max_u || definition->rect.min_v>=definition->rect.max_v) return false;
        *out=definition->rect;
        return true;
    }
    GeoPlacementViewScratch scratch;GeoRegionSetView domain;
    if (!geo_placement_domain_view(definition,regions,&scratch,&domain) || !domain.count) return false;
    GeoRect2 result;
    for (size_t c=0;c<domain.count;++c) {
        const GeoLoop2View *loop=&domain.regions[c].outline;
        if (!loop->count) return false;
        GeoRect2 bounds;
        geo_loop_bbox(loop,&bounds.min_u,&bounds.min_v,&bounds.max_u,&bounds.max_v);
        if (!c) result=bounds;
        else {
            if (bounds.min_u<result.min_u) result.min_u=bounds.min_u;
            if (bounds.min_v<result.min_v) result.min_v=bounds.min_v;
            if (bounds.max_u>result.max_u) result.max_u=bounds.max_u;
            if (bounds.max_v>result.max_v) result.max_v=bounds.max_v;
        }
    }
    *out=result;
    return true;
}
