/* Independent public K geometry/fault oracles. The private enclosure header
 * is used only for complete-store byte, padding and tail checks. */
#include "enclosure.h"
#include "internal/enclosures.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(c,n) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",n);return 1;}}while(0)
typedef struct {GeoRegionStore *regions;GeoPlacementStore *placements;} Fixture;
static bool open_fixture(Fixture *f)
{f->regions=geo_regions_create();f->placements=geo_placements_create();return f->regions&&f->placements;}
static void close_fixture(Fixture *f){geo_regions_destroy(f->regions);geo_placements_destroy(f->placements);}
static GeoRegionDefinition rectangle(uint32_t id,GeoCoord width,GeoCoord height)
{
    GeoRegionDefinition r;memset(&r,0,sizeof r);r.id=id;r.outline.count=4;
    r.outline.v[0]=(GeoPoint2){0,0};r.outline.v[1]=(GeoPoint2){width,0};
    r.outline.v[2]=(GeoPoint2){width,height};r.outline.v[3]=(GeoPoint2){0,height};return r;
}
static bool put_face(Fixture *f,uint32_t id,uint32_t placement,GeoFrame frame,GeoCoord width,GeoCoord height)
{
    GeoRegionDefinition r=rectangle(id,width,height);GeoPlacementDefinition p={0};p.id=placement;
    p.domain=GEO_PLACEMENT_REGION_REF;p.region_id=id;p.frame=frame;
    return geo_regions_put(f->regions,&r)&&geo_placements_put(f->placements,&p,f->regions);
}
static bool move_face(Fixture *f,uint32_t placement,GeoPoint3 origin)
{
    const GeoPlacementDefinition *old=geo_placements_find(f->placements,placement);if(!old)return false;
    GeoPlacementDefinition p;memcpy(&p,old,sizeof p);p.frame.origin=origin;
    return geo_placements_put(f->placements,&p,f->regions);
}
static bool equal_bounds(const GeoEnclosure *e,GeoCoord x0,GeoCoord y0,GeoCoord z0,GeoCoord x1,GeoCoord y1,GeoCoord z1)
{return e->min[0]==x0&&e->min[1]==y0&&e->min[2]==z0&&e->max[0]==x1&&e->max[1]==y1&&e->max[2]==z1;}
static bool zero_bytes(const void *p,size_t n)
{const unsigned char *b=p;for(size_t i=0;i<n;++i)if(b[i])return false;return true;}
static bool fault_is(GeoEnclosureFault f,GeoEnclosureFaultKind kind,uint32_t member,int axis)
{return f.kind==kind&&f.member_id==member&&f.axis==axis;}
static bool refused(Fixture *f,const uint32_t *ids,size_t count,GeoEnclosureFaultKind kind,uint32_t member,int axis)
{
    GeoEnclosure out,before;memset(&out,0xa5,sizeof out);memcpy(&before,&out,sizeof before);
    GeoEnclosureFault fault={GEO_ENCLOSURE_FAULT_NONE,UINT32_MAX,17};
    return !geo_enclosure_evaluate(f?f->regions:NULL,f?f->placements:NULL,543,ids,count,&out,&fault)&&
        fault_is(fault,kind,member,axis)&&!memcmp(&out,&before,sizeof out);
}
/* Every frame is right-handed. Region dimensions are literal, not computed
 * using the enclosure's extent helper. Placement order differs from members. */
static bool box_fixture(Fixture *f)
{
    return open_fixture(f)&&
        put_face(f,22,104,(GeoFrame){{10,220,30},{0,0,1},{1,0,0},{0,1,0}},300,100)&&
        put_face(f,31,105,(GeoFrame){{10,20,30},{0,1,0},{1,0,0},{0,0,-1}},200,100)&&
        put_face(f,12,102,(GeoFrame){{110,20,30},{0,1,0},{0,0,1},{1,0,0}},200,300)&&
        put_face(f,32,106,(GeoFrame){{10,20,330},{1,0,0},{0,1,0},{0,0,1}},100,200)&&
        put_face(f,11,101,(GeoFrame){{10,20,30},{0,0,1},{0,1,0},{-1,0,0}},300,200)&&
        put_face(f,21,103,(GeoFrame){{10,20,30},{1,0,0},{0,0,1},{0,-1,0}},100,300);
}
static bool unit_fixture(Fixture *f)
{
    return open_fixture(f)&&
        put_face(f,1,101,(GeoFrame){{0,0,10},{0,1,0},{0,0,-1},{-1,0,0}},10,10)&&
        put_face(f,2,102,(GeoFrame){{10,0,0},{0,1,0},{0,0,1},{1,0,0}},10,10)&&
        put_face(f,3,103,(GeoFrame){{0,0,0},{1,0,0},{0,0,1},{0,-1,0}},10,10)&&
        put_face(f,4,104,(GeoFrame){{0,10,10},{1,0,0},{0,0,-1},{0,1,0}},10,10)&&
        put_face(f,5,105,(GeoFrame){{0,10,0},{1,0,0},{0,-1,0},{0,0,-1}},10,10)&&
        put_face(f,6,106,(GeoFrame){{0,0,10},{1,0,0},{0,1,0},{0,0,1}},10,10);
}
static int box(void)
{
    Fixture f;CHECK(box_fixture(&f),"box-fixture");uint32_t ids[]={32,11,22,31,12,21};
    GeoEnclosure out;GeoEnclosureFault fault={GEO_ENCLOSURE_FAULT_INVERTED,91,-9},before;memcpy(&before,&fault,sizeof before);
    CHECK(geo_enclosure_evaluate(f.regions,f.placements,UINT32_MAX,ids,6,&out,&fault)&&out.id==UINT32_MAX&&out.member_count==6&&
        !memcmp(out.member_ids,ids,sizeof ids)&&out.closed&&equal_bounds(&out,10,20,30,110,220,330),"box-six-literal-bounds");
    CHECK(!memcmp(&fault,&before,sizeof fault)&&out.member_ids[6]==0&&out.member_ids[7]==0,"box-success-fault-and-unused");
    const GeoCoord bounds[3][2]={{10,110},{20,220},{30,330}};
    for(int axis=0;axis<3;++axis)for(int slot=0;slot<2;++slot){GeoCoord value=-999;
        CHECK(geo_enclosure_axis_bound(f.placements,&out,axis,slot,&value)&&value==bounds[axis][slot],"box-six-axis-planes");}
    GeoEnclosure canonical;memset(&canonical,0,sizeof canonical);canonical.id=UINT32_MAX;canonical.member_count=6;
    memcpy(canonical.member_ids,ids,sizeof ids);canonical.closed=true;
    for(int axis=0;axis<3;++axis){canonical.min[axis]=bounds[axis][0];canonical.max[axis]=bounds[axis][1];}
    CHECK(!memcmp(&out,&canonical,sizeof out),"box-output-canonical-bytes");
    for(size_t missing=0;missing<6;++missing){uint32_t five[5];size_t at=0;
        for(size_t i=0;i<6;++i)if(i!=missing)five[at++]=ids[i];
        CHECK(geo_enclosure_evaluate(f.regions,f.placements,4,five,5,&out,NULL)&&!out.closed&&
            equal_bounds(&out,10,20,30,110,220,330),"box-open-five");
    }
    memset(&out,0xa5,sizeof out);memcpy(out.member_ids,ids,sizeof ids);
    CHECK(geo_enclosure_evaluate(f.regions,f.placements,0,out.member_ids,6,&out,NULL)&&out.id==0&&out.closed&&
        !memcmp(out.member_ids,ids,sizeof ids)&&equal_bounds(&out,10,20,30,110,220,330),"box-input-output-id-alias");
    close_fixture(&f);return 0;
}
static int partial(void)
{
    Fixture f;CHECK(open_fixture(&f)&&put_face(&f,32,106,(GeoFrame){{10,20,330},{1,0,0},{0,1,0},{0,0,1}},100,200),"partial-fixture");
    uint32_t id=32;GeoEnclosure out;
    CHECK(geo_enclosure_evaluate(f.regions,f.placements,7,&id,1,&out,NULL)&&!out.closed&&
        equal_bounds(&out,10,20,0,110,220,330),"single-plane-extents");
    close_fixture(&f);return 0;
}
static int negative_axes(void)
{
    Fixture f;CHECK(open_fixture(&f)&&put_face(&f,32,106,(GeoFrame){{110,220,330},{-1,0,0},{0,-1,0},{0,0,1}},100,200),"negative-fixture");
    uint32_t id=32;GeoEnclosure out;
    CHECK(geo_enclosure_evaluate(f.regions,f.placements,7,&id,1,&out,NULL),"negative-evaluate");
    CHECK(out.min[0]==10&&out.max[0]==110,"negative-u-extents");
    CHECK(out.min[1]==20&&out.max[1]==220,"negative-v-extents");
    CHECK(out.min[2]==0&&out.max[2]==330&&!out.closed,"negative-normal-plane");
    GeoPlacementDefinition p;memcpy(&p,geo_placements_find(f.placements,106),sizeof p);
    p.frame=(GeoFrame){{110,20,30},{-1,0,0},{0,1,0},{0,0,-1}};
    CHECK(geo_placements_put(f.placements,&p,f.regions)&&geo_enclosure_evaluate(f.regions,f.placements,7,&id,1,&out,NULL)&&
        equal_bounds(&out,10,20,30,110,220,0),"negative-lower-plane-no-upper-invention");
    p.frame=(GeoFrame){{110,20,330},{0,1,0},{-1,0,0},{0,0,1}};GeoRegionDefinition r=rectangle(32,200,100);
    CHECK(geo_regions_put(f.regions,&r)&&geo_placements_put(f.placements,&p,f.regions)&&
        geo_enclosure_evaluate(f.regions,f.placements,7,&id,1,&out,NULL)&&equal_bounds(&out,10,20,0,110,220,330),"negative-permuted-local-axes");
    close_fixture(&f);return 0;
}
static int outline(void)
{
    Fixture f;CHECK(open_fixture(&f)&&put_face(&f,32,106,(GeoFrame){{10,20,330},{1,0,0},{0,1,0},{0,0,1}},100,200),"outline-fixture");
    uint32_t id=32;GeoEnclosure out;GeoRegionDefinition r=rectangle(32,100,200);r.hole_count=1;r.holes[0].count=4;
    r.holes[0].v[0]=(GeoPoint2){10,10};r.holes[0].v[1]=(GeoPoint2){10,20};
    r.holes[0].v[2]=(GeoPoint2){20,20};r.holes[0].v[3]=(GeoPoint2){20,10};
    CHECK(geo_regions_put(f.regions,&r)&&geo_enclosure_evaluate(f.regions,f.placements,8,&id,1,&out,NULL)&&
        equal_bounds(&out,10,20,0,110,220,330),"outline-hole-does-not-shrink");
    r.outline.count=6;r.outline.v[0]=(GeoPoint2){0,0};r.outline.v[1]=(GeoPoint2){100,0};r.outline.v[2]=(GeoPoint2){100,80};
    r.outline.v[3]=(GeoPoint2){40,80};r.outline.v[4]=(GeoPoint2){40,200};r.outline.v[5]=(GeoPoint2){0,200};
    CHECK(geo_regions_put(f.regions,&r)&&geo_enclosure_evaluate(f.regions,f.placements,8,&id,1,&out,NULL)&&
        equal_bounds(&out,10,20,0,110,220,330),"outline-concave-bbox-extremes");
    close_fixture(&f);return 0;
}
static int arguments(void)
{
    CHECK(GEO_ENCLOSURE_FAULT_NONE==0&&GEO_ENCLOSURE_FAULT_MEMBER_COUNT==1&&GEO_ENCLOSURE_FAULT_MISSING_REGION==2&&
        GEO_ENCLOSURE_FAULT_DUPLICATE_REGION==3&&GEO_ENCLOSURE_FAULT_NO_CARRIER==4&&GEO_ENCLOSURE_FAULT_AMBIGUOUS_CARRIER==5&&
        GEO_ENCLOSURE_FAULT_SLOT_TAKEN==6&&GEO_ENCLOSURE_FAULT_EXTENT_MISMATCH==7&&GEO_ENCLOSURE_FAULT_PLANE_MISMATCH==8&&
        GEO_ENCLOSURE_FAULT_INVERTED==9,"arguments-fault-kind-values");
    GeoEnclosure out,expected;memset(&out,0xa5,sizeof out);memset(&expected,0,sizeof expected);expected.id=UINT32_MAX;
    GeoEnclosureFault fault={GEO_ENCLOSURE_FAULT_INVERTED,91,-9},before;memcpy(&before,&fault,sizeof before);
    CHECK(geo_enclosure_evaluate(NULL,NULL,UINT32_MAX,NULL,0,&out,&fault)&&!memcmp(&out,&expected,sizeof out)&&
        !memcmp(&fault,&before,sizeof fault),"arguments-empty-canonical-success");
    uint32_t nine[9]={6,6,6,6,6,6,6,6,6};
    CHECK(refused(NULL,nine,9,GEO_ENCLOSURE_FAULT_MEMBER_COUNT,0,-1),"arguments-nine-members");
    CHECK(refused(NULL,NULL,1,GEO_ENCLOSURE_FAULT_MEMBER_COUNT,0,-1),"arguments-null-ids");
    CHECK(!geo_enclosure_evaluate(NULL,NULL,1,NULL,0,NULL,&fault)&&fault_is(fault,GEO_ENCLOSURE_FAULT_MEMBER_COUNT,0,-1),"arguments-null-output");
    Fixture f;CHECK(unit_fixture(&f),"arguments-fixture");
    CHECK(refused(&f,nine,8,GEO_ENCLOSURE_FAULT_DUPLICATE_REGION,6,-1),"arguments-eight-enters-member-validation");
    memset(&out,0xa5,sizeof out);memcpy(&expected,&out,sizeof expected);uint32_t absent=99;
    CHECK(!geo_enclosure_evaluate(f.regions,f.placements,7,&absent,1,&out,NULL)&&!memcmp(&out,&expected,sizeof out),"arguments-null-fault-atomic");
    close_fixture(&f);return 0;
}
static int identity_faults(void)
{
    Fixture f;CHECK(unit_fixture(&f),"identity-fixture");uint32_t ids[]={99,1};
    CHECK(refused(&f,ids,1,GEO_ENCLOSURE_FAULT_MISSING_REGION,99,-1),"identity-missing-region");
    CHECK(geo_placements_remove(f.placements,101),"identity-remove-carrier");ids[0]=1;
    CHECK(refused(&f,ids,1,GEO_ENCLOSURE_FAULT_NO_CARRIER,1,-1),"identity-no-carrier");
    ids[1]=99;CHECK(refused(&f,ids,2,GEO_ENCLOSURE_FAULT_NO_CARRIER,1,-1),"identity-member-order-first");
    ids[0]=99;ids[1]=1;CHECK(refused(&f,ids,2,GEO_ENCLOSURE_FAULT_MISSING_REGION,99,-1),"identity-member-order-reversed");
    close_fixture(&f);CHECK(unit_fixture(&f),"identity-second-fixture");ids[0]=ids[1]=1;
    CHECK(refused(&f,ids,2,GEO_ENCLOSURE_FAULT_DUPLICATE_REGION,1,-1),"identity-duplicate-before-slot");
    GeoPlacementDefinition p;memcpy(&p,geo_placements_find(f.placements,101),sizeof p);p.id=201;
    CHECK(geo_placements_put(f.placements,&p,f.regions),"identity-second-carrier");
    CHECK(refused(&f,ids,2,GEO_ENCLOSURE_FAULT_AMBIGUOUS_CARRIER,1,-1),"identity-ambiguous-before-later-duplicate");
    close_fixture(&f);return 0;
}
static int member_faults(void)
{
    Fixture f;CHECK(unit_fixture(&f),"member-fault-fixture");uint32_t ids[]={6,7};
    CHECK(put_face(&f,7,107,(GeoFrame){{1,2,20},{1,0,0},{0,1,0},{0,0,1}},10,10),"member-fault-second-slot-fixture");
    CHECK(refused(&f,ids,2,GEO_ENCLOSURE_FAULT_SLOT_TAKEN,7,2),"member-slot-before-extents");
    ids[0]=5;ids[1]=6;CHECK(move_face(&f,106,(GeoPoint3){1,2,10}),"member-fault-extent-x-fixture");
    CHECK(refused(&f,ids,2,GEO_ENCLOSURE_FAULT_EXTENT_MISMATCH,6,0),"member-extent-x-before-y");
    CHECK(move_face(&f,106,(GeoPoint3){0,2,10}),"member-fault-extent-y-fixture");
    CHECK(refused(&f,ids,2,GEO_ENCLOSURE_FAULT_EXTENT_MISMATCH,6,1),"member-extent-y");
    ids[0]=1;ids[1]=2;CHECK(move_face(&f,102,(GeoPoint3){10,0,1}),"member-fault-extent-z-fixture");
    CHECK(refused(&f,ids,2,GEO_ENCLOSURE_FAULT_EXTENT_MISMATCH,2,2),"member-extent-z");
    close_fixture(&f);return 0;
}
static int plane_faults(void)
{
    Fixture f;CHECK(unit_fixture(&f),"plane-fixture");uint32_t ids[]={1,3,0};
    CHECK(move_face(&f,101,(GeoPoint3){1,0,10}),"plane-lower-fixture");
    CHECK(refused(&f,ids,2,GEO_ENCLOSURE_FAULT_PLANE_MISMATCH,0,0),"plane-lower-mismatch");
    CHECK(move_face(&f,101,(GeoPoint3){0,0,10})&&move_face(&f,102,(GeoPoint3){9,0,0}),"plane-upper-fixture");ids[0]=2;
    CHECK(refused(&f,ids,2,GEO_ENCLOSURE_FAULT_PLANE_MISMATCH,0,0),"plane-upper-mismatch");
    CHECK(move_face(&f,101,(GeoPoint3){1,0,10})&&move_face(&f,103,(GeoPoint3){0,2,0})&&
        move_face(&f,105,(GeoPoint3){0,10,3}),"plane-axis-order-fixture");ids[0]=5;ids[1]=3;ids[2]=1;
    CHECK(refused(&f,ids,3,GEO_ENCLOSURE_FAULT_PLANE_MISMATCH,0,0),"plane-final-x-before-y-z");
    CHECK(move_face(&f,101,(GeoPoint3){0,0,10}),"plane-repair-x");
    CHECK(refused(&f,ids,3,GEO_ENCLOSURE_FAULT_PLANE_MISMATCH,0,1),"plane-final-y-before-z");
    CHECK(move_face(&f,103,(GeoPoint3){0,0,0}),"plane-repair-y");
    CHECK(refused(&f,ids,3,GEO_ENCLOSURE_FAULT_PLANE_MISMATCH,0,2),"plane-final-z");
    ids[0]=1;ids[1]=2;ids[2]=3;
    CHECK(move_face(&f,101,(GeoPoint3){10,0,10})&&move_face(&f,102,(GeoPoint3){0,0,0}),"plane-before-inversion-fixture");
    CHECK(refused(&f,ids,3,GEO_ENCLOSURE_FAULT_PLANE_MISMATCH,0,0),"plane-lower-before-inversion");
    CHECK(move_face(&f,101,(GeoPoint3){0,0,10}),"plane-upper-before-inversion-fixture");
    CHECK(refused(&f,ids,3,GEO_ENCLOSURE_FAULT_PLANE_MISMATCH,0,0),"plane-upper-before-inversion");
    close_fixture(&f);return 0;
}
static int inverted(void)
{
    Fixture f;CHECK(unit_fixture(&f),"inverted-fixture");uint32_t ids[]={1,2};
    CHECK(move_face(&f,101,(GeoPoint3){5,0,10})&&move_face(&f,102,(GeoPoint3){5,0,0}),"inverted-equal-fixture");
    CHECK(refused(&f,ids,2,GEO_ENCLOSURE_FAULT_INVERTED,0,0),"inverted-equal-planes");
    CHECK(move_face(&f,102,(GeoPoint3){0,0,0}),"inverted-x-fixture");
    CHECK(refused(&f,ids,2,GEO_ENCLOSURE_FAULT_INVERTED,0,0),"inverted-x");ids[0]=3;ids[1]=4;
    CHECK(move_face(&f,103,(GeoPoint3){0,5,0})&&move_face(&f,104,(GeoPoint3){0,0,10}),"inverted-y-fixture");
    CHECK(refused(&f,ids,2,GEO_ENCLOSURE_FAULT_INVERTED,0,1),"inverted-y");ids[0]=5;ids[1]=6;
    CHECK(move_face(&f,105,(GeoPoint3){0,10,5})&&move_face(&f,106,(GeoPoint3){0,0,0}),"inverted-z-fixture");
    CHECK(refused(&f,ids,2,GEO_ENCLOSURE_FAULT_INVERTED,0,2),"inverted-z");close_fixture(&f);return 0;
}
static int axis_query(void)
{
    Fixture f;CHECK(open_fixture(&f)&&put_face(&f,32,106,(GeoFrame){{10,20,330},{1,0,0},{0,1,0},{0,0,1}},100,200),"axis-fixture");
    uint32_t id=32;GeoEnclosure out;CHECK(geo_enclosure_evaluate(f.regions,f.placements,7,&id,1,&out,NULL),"axis-evaluate");
    GeoCoord value=987;CHECK(!geo_enclosure_axis_bound(f.placements,&out,0,0,&value)&&value==987,"axis-no-cached-extent-fallback");
    CHECK(!geo_enclosure_axis_bound(f.placements,&out,1,1,&value)&&value==987,"axis-no-other-extent");
    CHECK(geo_enclosure_axis_bound(f.placements,&out,2,1,&value)&&value==330,"axis-upper-plane");value=987;
    CHECK(!geo_enclosure_axis_bound(f.placements,&out,2,0,&value)&&value==987,"axis-normal-slot-sign");
    CHECK(!geo_enclosure_axis_bound(f.placements,&out,-1,0,&value)&&!geo_enclosure_axis_bound(f.placements,&out,3,0,&value)&&
        !geo_enclosure_axis_bound(f.placements,&out,2,-1,&value)&&!geo_enclosure_axis_bound(f.placements,&out,2,2,&value)&&
        !geo_enclosure_axis_bound(f.placements,NULL,2,1,&value)&&!geo_enclosure_axis_bound(f.placements,&out,2,1,NULL)&&value==987,"axis-invalid-atomic");
    GeoEnclosure bad;memcpy(&bad,&out,sizeof bad);bad.member_count=9;
    CHECK(!geo_enclosure_axis_bound(f.placements,&bad,2,1,&value)&&value==987,"axis-over-capacity-atomic");
    GeoPlacementDefinition p;memcpy(&p,geo_placements_find(f.placements,106),sizeof p);p.id=206;p.frame.origin.z=440;
    CHECK(geo_placements_put(f.placements,&p,f.regions)&&refused(&f,&id,1,GEO_ENCLOSURE_FAULT_AMBIGUOUS_CARRIER,32,-1),"axis-ambiguous-evaluation");
    out.min[2]=-800;out.max[2]=900;
    CHECK(geo_enclosure_axis_bound(f.placements,&out,2,1,&value)&&value==330,"axis-first-placement-no-unique-recheck");
    CHECK(put_face(&f,88,308,(GeoFrame){{10,20,550},{1,0,0},{0,1,0},{0,0,1}},100,200),"axis-second-member-fixture");
    out.member_count=2;out.member_ids[0]=88;out.member_ids[1]=32;
    CHECK(geo_enclosure_axis_bound(f.placements,&out,2,1,&value)&&value==550,"axis-member-before-placement-order");
    close_fixture(&f);return 0;
}
static int typed_carriers(void)
{
    Fixture f;CHECK(open_fixture(&f),"typed-fixture");GeoRegionDefinition r=rectangle(0,100,200);
    CHECK(geo_regions_put(f.regions,&r),"typed-zero-region");GeoPlacementDefinition p={0};p.id=1;
    p.frame=(GeoFrame){{10,20,330},{1,0,0},{0,1,0},{0,0,1}};p.domain=GEO_PLACEMENT_RECT;p.rect=(GeoRect2){0,0,100,200};
    CHECK(geo_placements_put(f.placements,&p,f.regions),"typed-rectangle");p.id=2;p.domain=GEO_PLACEMENT_REGION_SET;p.component_count=1;p.components[0]=r;
    CHECK(geo_placements_put(f.placements,&p,f.regions),"typed-region-set");uint32_t id=0;
    CHECK(refused(&f,&id,1,GEO_ENCLOSURE_FAULT_NO_CARRIER,0,-1),"typed-inactive-zero-is-not-reference");
    p.id=3;p.domain=GEO_PLACEMENT_REGION_REF;p.region_id=0;
    CHECK(geo_placements_put(f.placements,&p,f.regions),"typed-explicit-zero-reference");GeoEnclosure out;
    CHECK(geo_enclosure_evaluate(f.regions,f.placements,0,&id,1,&out,NULL)&&out.member_ids[0]==0&&
        equal_bounds(&out,10,20,0,110,220,330),"typed-zero-reference-single-carrier");
    p.id=4;CHECK(geo_placements_put(f.placements,&p,f.regions)&&
        refused(&f,&id,1,GEO_ENCLOSURE_FAULT_AMBIGUOUS_CARRIER,0,-1),"typed-two-explicit-references");
    close_fixture(&f);return 0;
}
static int storage(void)
{
    GeoEnclosureStore *store=geo_enclosures_create();CHECK(store&&zero_bytes(store,sizeof *store),"store-create-zero");
    GeoEnclosure noisy,expected;memset(&noisy,0xa5,sizeof noisy);memset(&expected,0,sizeof expected);
    noisy.id=expected.id=UINT32_MAX;noisy.member_count=expected.member_count=2;
    noisy.member_ids[0]=expected.member_ids[0]=0;noisy.member_ids[1]=expected.member_ids[1]=7;
    for(int a=0;a<3;++a){noisy.min[a]=expected.min[a]=10+a;noisy.max[a]=expected.max[a]=20+a;}noisy.closed=expected.closed=true;
    CHECK(geo_enclosures_stage(store,&noisy),"store-stage-noisy");const GeoEnclosure *saved=geo_enclosures_find(store,UINT32_MAX);
    CHECK(saved&&!memcmp(saved,&expected,sizeof expected),"store-canonical-unused-padding");
    noisy.member_ids[0]=77;noisy.min[0]=-99;
    CHECK(saved->member_ids[0]==0&&saved->min[0]==10&&geo_enclosures_values(store)==saved,"store-owns-input-and-values");
    CHECK(geo_enclosures_stage(store,saved)&&!memcmp(geo_enclosures_at(store,0),&expected,sizeof expected),"store-self-alias");
    GeoEnclosureStore *clone=geo_enclosures_clone(store);CHECK(clone&&clone!=store&&!memcmp(clone,store,sizeof *store),"store-clone-complete-bytes");
    expected.min[0]=777;CHECK(geo_enclosures_stage(clone,&expected)&&geo_enclosures_find(store,UINT32_MAX)->min[0]==10,"store-clone-isolation");
    GeoEnclosure bad;memcpy(&bad,&expected,sizeof bad);bad.member_count=9;GeoEnclosureStore before;memcpy(&before,store,sizeof before);
    CHECK(!geo_enclosures_stage(store,&bad)&&!memcmp(store,&before,sizeof before),"store-member-count-failure-atomic");
    CHECK(!geo_enclosures_stage(store,NULL)&&!geo_enclosures_stage(NULL,&expected)&&!memcmp(store,&before,sizeof before),"store-null-stage-atomic");
    CHECK(!geo_enclosures_remove(store,123)&&!memcmp(store,&before,sizeof before),"store-missing-remove-atomic");
    CHECK(geo_enclosures_count(NULL)==0&&!geo_enclosures_values(NULL)&&!geo_enclosures_at(NULL,0)&&!geo_enclosures_find(NULL,0)&&
        !geo_enclosures_clone(NULL)&&!geo_enclosures_remove(NULL,0)&&!geo_enclosures_at(store,1),"store-null-and-outside-queries");
    geo_enclosures_destroy(NULL);geo_enclosures_destroy(clone);geo_enclosures_destroy(store);return 0;
}
static int capacity(void)
{
    GeoEnclosureStore *store=geo_enclosures_create();CHECK(store,"capacity-create");uint32_t ids[]={0,UINT32_MAX,7,8};
    GeoEnclosure value={0};for(size_t i=0;i<4;++i){value.id=ids[i];value.member_count=1;value.member_ids[0]=(uint32_t)i;
        CHECK(geo_enclosures_stage(store,&value)&&geo_enclosures_at(store,i)->id==ids[i],"capacity-four-in-order");}
    GeoEnclosureStore before;memcpy(&before,store,sizeof before);value.id=9;
    CHECK(!geo_enclosures_stage(store,&value)&&!memcmp(store,&before,sizeof before),"capacity-fifth-atomic");
    value.id=UINT32_MAX;value.min[0]=77;
    CHECK(geo_enclosures_stage(store,&value)&&geo_enclosures_count(store)==4&&geo_enclosures_at(store,1)->min[0]==77&&
        geo_enclosures_at(store,0)->id==0&&geo_enclosures_at(store,2)->id==7,"capacity-replace-stays-in-place");
    CHECK(geo_enclosures_remove(store,7)&&geo_enclosures_count(store)==3&&geo_enclosures_at(store,0)->id==0&&
        geo_enclosures_at(store,1)->id==UINT32_MAX&&geo_enclosures_at(store,2)->id==8,"capacity-remove-preserves-order");
    CHECK(zero_bytes(&store->values[3],sizeof store->values[3]),"capacity-zero-vacated-tail");
    value.id=9;CHECK(geo_enclosures_stage(store,&value)&&geo_enclosures_at(store,3)->id==9,"capacity-append-freed-slot");
    store->count=5;memcpy(&before,store,sizeof before);
    CHECK(!geo_enclosures_stage(store,&value)&&!geo_enclosures_remove(store,0)&&!geo_enclosures_find(store,0)&&
        !geo_enclosures_at(store,4)&&!memcmp(store,&before,sizeof before),"capacity-corrupt-count-atomic");
    geo_enclosures_destroy(store);return 0;
}
static int empty_cache(void)
{
    GeoEnclosureStore *store=geo_enclosures_create();CHECK(store,"empty-cache-create");GeoEnclosure e={0};e.id=17;e.closed=true;
    e.min[0]=10;e.min[1]=20;e.min[2]=30;e.max[0]=110;e.max[1]=220;e.max[2]=330;
    CHECK(geo_enclosures_stage(store,&e)&&geo_enclosures_find(store,17)->closed&&
        equal_bounds(geo_enclosures_find(store,17),10,20,30,110,220,330),"empty-cache-stage-preserves-derived-values");
    CHECK(geo_enclosure_evaluate(NULL,NULL,17,NULL,0,&e,NULL)&&geo_enclosures_stage(store,&e)&&
        !geo_enclosures_find(store,17)->closed&&equal_bounds(geo_enclosures_find(store,17),0,0,0,0,0,0),"empty-cache-evaluation-clears-later");
    geo_enclosures_destroy(store);return 0;
}
static int shared_members(void)
{
    Fixture f;CHECK(box_fixture(&f),"shared-fixture");uint32_t ids[]={32,11,22,31,12,21};GeoEnclosure a,b;
    GeoEnclosureStore *store=geo_enclosures_create();CHECK(store,"shared-store");
    CHECK(geo_enclosure_evaluate(f.regions,f.placements,1,ids,6,&a,NULL)&&geo_enclosures_stage(store,&a)&&
        geo_enclosure_evaluate(f.regions,f.placements,2,ids,6,&b,NULL)&&geo_enclosures_stage(store,&b)&&
        geo_enclosures_count(store)==2&&geo_enclosures_at(store,0)->closed&&geo_enclosures_at(store,1)->closed,"shared-members-not-exclusive");
    CHECK(geo_enclosures_remove(store,1)&&geo_regions_count(f.regions)==6&&geo_placements_count(f.placements)==6&&
        geo_enclosures_at(store,0)->id==2,"shared-remove-no-cascade");
    geo_enclosures_destroy(store);close_fixture(&f);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"box"))return box();if(!strcmp(argv[1],"partial"))return partial();
    if(!strcmp(argv[1],"negative"))return negative_axes();if(!strcmp(argv[1],"outline"))return outline();
    if(!strcmp(argv[1],"arguments"))return arguments();if(!strcmp(argv[1],"identity"))return identity_faults();
    if(!strcmp(argv[1],"members"))return member_faults();if(!strcmp(argv[1],"planes"))return plane_faults();
    if(!strcmp(argv[1],"inverted"))return inverted();if(!strcmp(argv[1],"axis"))return axis_query();
    if(!strcmp(argv[1],"typed"))return typed_carriers();if(!strcmp(argv[1],"storage"))return storage();
    if(!strcmp(argv[1],"capacity"))return capacity();if(!strcmp(argv[1],"empty-cache"))return empty_cache();
    if(!strcmp(argv[1],"sharing"))return shared_members();return 2;
}
