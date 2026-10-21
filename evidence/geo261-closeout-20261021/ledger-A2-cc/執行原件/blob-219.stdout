#include "internal/enclosures.h"
#include <stdlib.h>
#include <string.h>

GeoEnclosureStore *geo_enclosures_create(void){return calloc(1,sizeof(GeoEnclosureStore));}
GeoEnclosureStore *geo_enclosures_clone(const GeoEnclosureStore *source)
{
    if(!source)return NULL;
    GeoEnclosureStore *copy=malloc(sizeof *copy);
    if(copy)memcpy(copy,source,sizeof *copy);
    return copy;
}
void geo_enclosures_destroy(GeoEnclosureStore *store){free(store);}
size_t geo_enclosures_count(const GeoEnclosureStore *store){return store?store->count:0;}
const GeoEnclosure *geo_enclosures_at(const GeoEnclosureStore *store,size_t index)
{return store&&index<store->count&&index<GEO_ENCLOSURE_CAPACITY?&store->values[index]:NULL;}
const GeoEnclosure *geo_enclosures_values(const GeoEnclosureStore *store)
{return store?store->values:NULL;}
const GeoEnclosure *geo_enclosures_find(const GeoEnclosureStore *store,uint32_t id)
{
    if(!store||store->count>GEO_ENCLOSURE_CAPACITY)return NULL;
    for(size_t i=0;i<store->count;++i)if(store->values[i].id==id)return &store->values[i];
    return NULL;
}
bool geo_enclosures_stage(GeoEnclosureStore *store,const GeoEnclosure *value)
{
    if(!store||!value||store->count>GEO_ENCLOSURE_CAPACITY||value->member_count>GEO_ENCLOSURE_MEMBER_CAPACITY)return false;
    size_t at=0;while(at<store->count&&store->values[at].id!=value->id)++at;
    if(at>=GEO_ENCLOSURE_CAPACITY)return false;
    GeoEnclosure next;memset(&next,0,sizeof next);next.id=value->id;next.member_count=value->member_count;
    memcpy(next.member_ids,value->member_ids,next.member_count*sizeof next.member_ids[0]);
    for(int axis=0;axis<3;++axis){next.min[axis]=value->min[axis];next.max[axis]=value->max[axis];}
    next.closed=value->closed;
    memcpy(&store->values[at],&next,sizeof next);if(at==store->count)++store->count;
    return true;
}
bool geo_enclosures_remove(GeoEnclosureStore *store,uint32_t id)
{
    if(!store||store->count>GEO_ENCLOSURE_CAPACITY)return false;
    size_t at=0;while(at<store->count&&store->values[at].id!=id)++at;
    if(at==store->count)return false;
    memmove(store->values+at,store->values+at+1,(store->count-at-1)*sizeof store->values[0]);
    memset(&store->values[--store->count],0,sizeof store->values[0]);return true;
}

static int geo_enclosure_axis(GeoVector3 axis)
{return axis.x!=0?0:axis.y!=0?1:2;}
static GeoCoord geo_enclosure_point_component(GeoPoint3 point,int axis)
{return axis==0?point.x:axis==1?point.y:point.z;}
static GeoCoord geo_enclosure_vector_component(GeoVector3 vector,int axis)
{return axis==0?vector.x:axis==1?vector.y:vector.z;}
static bool geo_enclosure_carrier(const GeoPlacementDefinition *placement,uint32_t member)
{return placement&&placement->domain==GEO_PLACEMENT_REGION_REF&&placement->region_id==member;}
static bool geo_enclosure_fail(GeoEnclosureFault *out,GeoEnclosureFaultKind kind,uint32_t member,int axis)
{if(out){out->kind=kind;out->member_id=member;out->axis=axis;}return false;}
static void geo_enclosure_extent(const GeoFrame *frame,const GeoRegionDefinition *region,int axis,GeoCoord *low,GeoCoord *high)
{
    GeoLoop2View outline={region->outline.v,region->outline.count};GeoRect2 bounds;
    geo_loop_bbox(&outline,&bounds.min_u,&bounds.min_v,&bounds.max_u,&bounds.max_v);
    GeoCoord origin=geo_enclosure_point_component(frame->origin,axis);
    GeoCoord u=geo_enclosure_vector_component(frame->axis_u,axis);
    GeoCoord v=geo_enclosure_vector_component(frame->axis_v,axis);
    if(u!=0){*low=origin+(u>0?bounds.min_u:-bounds.max_u);*high=origin+(u>0?bounds.max_u:-bounds.min_u);}
    else{*low=origin+(v>0?bounds.min_v:-bounds.max_v);*high=origin+(v>0?bounds.max_v:-bounds.min_v);}
}

bool geo_enclosure_evaluate(const GeoRegionStore *regions,const GeoPlacementStore *placements,
    uint32_t id,const uint32_t *member_ids,size_t member_count,GeoEnclosure *out,GeoEnclosureFault *fault)
{
    typedef struct {GeoCoord value;bool set;} MaybeBound;
    MaybeBound bound[3][2]={0},extent_low[3]={0},extent_high[3]={0};
    bool occupied[3][2]={0};
    if(!out||member_count>GEO_ENCLOSURE_MEMBER_CAPACITY||(!member_ids&&member_count))
        return geo_enclosure_fail(fault,GEO_ENCLOSURE_FAULT_MEMBER_COUNT,0,-1);
    GeoEnclosure next;memset(&next,0,sizeof next);next.id=id;next.member_count=member_count;
    if(member_count)memcpy(next.member_ids,member_ids,member_count*sizeof next.member_ids[0]);
    for(size_t i=0;i<member_count;++i){
        uint32_t member=next.member_ids[i];const GeoRegionDefinition *region=geo_regions_find(regions,member);
        if(!region)return geo_enclosure_fail(fault,GEO_ENCLOSURE_FAULT_MISSING_REGION,member,-1);
        for(size_t j=0;j<i;++j)if(next.member_ids[j]==member)
            return geo_enclosure_fail(fault,GEO_ENCLOSURE_FAULT_DUPLICATE_REGION,member,-1);
        const GeoPlacementDefinition *carrier=NULL;size_t carriers=0;
        for(size_t p=0;p<geo_placements_count(placements);++p){
            const GeoPlacementDefinition *placement=geo_placements_at(placements,p);
            if(geo_enclosure_carrier(placement,member)){carrier=placement;++carriers;}
        }
        if(carriers!=1)return geo_enclosure_fail(fault,carriers?GEO_ENCLOSURE_FAULT_AMBIGUOUS_CARRIER:GEO_ENCLOSURE_FAULT_NO_CARRIER,member,-1);
        int axis=geo_enclosure_axis(carrier->frame.normal);
        int slot=geo_enclosure_vector_component(carrier->frame.normal,axis)>0?1:0;
        if(occupied[axis][slot])return geo_enclosure_fail(fault,GEO_ENCLOSURE_FAULT_SLOT_TAKEN,member,axis);
        occupied[axis][slot]=true;
        bound[axis][slot].value=geo_enclosure_point_component(carrier->frame.origin,axis);bound[axis][slot].set=true;
        for(int j=0;j<3;++j){
            if(j==axis)continue;
            GeoCoord low,high;geo_enclosure_extent(&carrier->frame,region,j,&low,&high);
            if(extent_low[j].set&&(extent_low[j].value!=low||extent_high[j].value!=high))
                return geo_enclosure_fail(fault,GEO_ENCLOSURE_FAULT_EXTENT_MISMATCH,member,j);
            extent_low[j].value=low;extent_low[j].set=true;extent_high[j].value=high;extent_high[j].set=true;
        }
    }
    for(int axis=0;axis<3;++axis){
        if(bound[axis][0].set&&extent_low[axis].set&&bound[axis][0].value!=extent_low[axis].value)
            return geo_enclosure_fail(fault,GEO_ENCLOSURE_FAULT_PLANE_MISMATCH,0,axis);
        if(bound[axis][1].set&&extent_high[axis].set&&bound[axis][1].value!=extent_high[axis].value)
            return geo_enclosure_fail(fault,GEO_ENCLOSURE_FAULT_PLANE_MISMATCH,0,axis);
        if(bound[axis][0].set&&bound[axis][1].set&&bound[axis][0].value>=bound[axis][1].value)
            return geo_enclosure_fail(fault,GEO_ENCLOSURE_FAULT_INVERTED,0,axis);
        next.min[axis]=bound[axis][0].set?bound[axis][0].value:extent_low[axis].value;
        next.max[axis]=bound[axis][1].set?bound[axis][1].value:extent_high[axis].value;
    }
    next.closed=occupied[0][0]&&occupied[0][1]&&occupied[1][0]&&occupied[1][1]&&occupied[2][0]&&occupied[2][1];
    memcpy(out,&next,sizeof next);return true;
}

bool geo_enclosure_axis_bound(const GeoPlacementStore *placements,const GeoEnclosure *enclosure,int axis,int slot,GeoCoord *out)
{
    if(!enclosure||!out||enclosure->member_count>GEO_ENCLOSURE_MEMBER_CAPACITY||axis<0||axis>2||slot<0||slot>1)return false;
    for(size_t i=0;i<enclosure->member_count;++i)for(size_t p=0;p<geo_placements_count(placements);++p){
        const GeoPlacementDefinition *placement=geo_placements_at(placements,p);
        if(!geo_enclosure_carrier(placement,enclosure->member_ids[i]))continue;
        if(geo_enclosure_axis(placement->frame.normal)!=axis)continue;
        if((geo_enclosure_vector_component(placement->frame.normal,axis)>0?1:0)==slot){
            *out=geo_enclosure_point_component(placement->frame.origin,axis);return true;
        }
    }
    return false;
}
