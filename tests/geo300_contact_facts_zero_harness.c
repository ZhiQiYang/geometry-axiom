/* Run the real H adapter with linked K/W objects. The only instrumentation
 * counts bytes actually passed to memset inside app_contact_facts_prepare. */
#ifdef _WIN32
#undef _WIN32
#endif
#include <stddef.h>
#include <string.h>
static size_t facts_zero_bytes;
static void *facts_counted_memset(void *p,int value,size_t bytes)
{facts_zero_bytes+=bytes;return memset(p,value,bytes);}
#define main geometry_facts_zero_cli_main
#include "../current_geometry.c"
#undef main
#define CHECK(tag,x) do{if(!(x)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)

static void frozen_facts_prepare(const World *world,const PlacementSurface *placement,
    const SpaceBoundarySurface *boundary,AppContactFacts *facts,AppContactRawSnapshot *raw)
{
    memset(facts,0,sizeof *facts);facts->world.placement_id=placement->id;
    const SpaceBoundarySurface *effective=placement_effective_boundary(placement,boundary,&facts->effective);
    facts->world.role_boundary=effective;
    facts->world.region_count=placement->derived_fill_id?placement->component_count:1;
    for(size_t c=0;c<facts->world.region_count;++c)facts->world.regions[c]=placement->derived_fill_id?&placement->components[c]:effective;
    facts->world.members=facts->members;facts->world.member_count=world->wood.timber_count;
    for(size_t i=0;i<world->wood.timber_count;++i){WoodContactMemberFact *f=&facts->members[i];const TimberAnchor *a=&world->wood.anchors[i];
        f->member=&world->wood.timbers[i];f->placement_id=a->placement_id;f->order=a->order;
        f->along_v=a->length_direction==SURFACE_DIRECTION_POS_V||a->length_direction==SURFACE_DIRECTION_NEG_V;
        if(raw){
            AppContactRawSnapshot *s=&raw[i];s->placed=f->member->placed;s->pending=0;
            if(s->placed){s->anchor=a->uv;s->length_direction=a->length_direction;s->depth_side=a->depth_side;
                s->length=f->member->length;s->size_a=f->member->size_a;}
        }else f->footprint_valid=timber_a0_footprint_uv(placement,f->member,a,&f->footprint);
    }
}

static SpaceBoundarySurface test_region(unsigned id)
{
    SpaceBoundarySurface b={0};b.id=id;b.outline.count=4;
    GeoPoint2 corners[4]={{0,0},{1000,0},{1000,1000},{0,1000}};
    memcpy(b.outline.v,corners,sizeof corners);
    for(size_t i=0;i<4;++i)b.outline.fixity[i]=WOOD_STOP_FIXED;
    return b;
}
static int compare_case(size_t count,bool deferred,unsigned domain,bool check_work)
{
    World *world=calloc(1,sizeof *world),*before=malloc(sizeof *before);
    CHECK("facts-zero-fixture-memory",world&&before);
    CHECK("facts-zero-fixture-capacity",count<=WORLD_MAX_TIMBERS);
    world->wood.timber_count=count;
    PlacementSurface placement={0};placement.id=7;
    placement.frame=(GeoFrame){{10,20,30},{1,0,0},{0,1,0},{0,0,1}};
    placement.rect=(GeoRect2){0,0,1000,1000};
    SpaceBoundarySurface region=test_region(7);
    const SpaceBoundarySurface *boundary=domain==1?&region:NULL;
    if(domain>=2){placement.derived_fill_id=9;placement.component_count=domain==2?2:0;
        placement.components[0]=region;placement.components[1]=test_region(8);}
    for(size_t i=0;i<count;++i){
        Timber *member=&world->wood.timbers[i];TimberAnchor *anchor=&world->wood.anchors[i];
        member->id=(uint32_t)i+41;member->placed=i%3!=0;
        member->length=40;member->size_a=10;member->size_b=5;
        anchor->placement_id=i%2?7:8;anchor->order=UINT64_MAX-(uint64_t)i;
        anchor->uv=(GeoPoint2){(Coord)i*2,(Coord)i*3};
        anchor->length_direction=i%5==0?999:i%2?SURFACE_DIRECTION_POS_U:SURFACE_DIRECTION_POS_V;
        anchor->depth_side=SURFACE_DEPTH_POSITIVE_NORMAL;
    }
    memcpy(before,world,sizeof *before);
    AppContactFacts actual,expected;
    AppContactRawSnapshot raw[WORLD_MAX_TIMBERS],old_raw[WORLD_MAX_TIMBERS];
    memset(&actual,0xa5,sizeof actual);memset(&expected,0xa5,sizeof expected);
    memset(raw,0xa5,sizeof raw);memset(old_raw,0xa5,sizeof old_raw);
    facts_zero_bytes=0;
    app_contact_facts_prepare(world,&placement,boundary,&actual,deferred?raw:NULL);
    size_t zero_bytes=facts_zero_bytes;
    frozen_facts_prepare(world,&placement,boundary,&expected,deferred?old_raw:NULL);
    if(check_work)CHECK("facts-zero-work-scales-with-live-members",
        zero_bytes<=sizeof(WoodContactWorld)+count*sizeof(WoodContactMemberFact));
    /* Live bytes (including existing zero padding and invalid raw footprint)
     * remain the original adapter's output; inactive local tail is not read. */
    CHECK("facts-zero-live-member-bytes-match-original",
        !memcmp(actual.members,expected.members,count*sizeof actual.members[0]));
    WoodContactWorld view;memcpy(&view,&expected.world,sizeof view);
    view.members=actual.members;
    if(view.role_boundary==&expected.effective)view.role_boundary=&actual.effective;
    for(size_t i=0;i<view.region_count;++i)
        if(view.regions[i]==&expected.effective)view.regions[i]=&actual.effective;
    CHECK("facts-zero-original-world-view",!memcmp(&actual.world,&view,sizeof view));
    CHECK("facts-zero-effective-boundary-initialized",
        !memcmp(actual.world.role_boundary,expected.world.role_boundary,sizeof region));
    for(size_t i=0;i<view.region_count;++i)
        CHECK("facts-zero-original-region-bytes",!memcmp(actual.world.regions[i],expected.world.regions[i],sizeof region));
    if(deferred)CHECK("facts-zero-original-raw-snapshot",!memcmp(raw,old_raw,sizeof raw));
    CHECK("facts-zero-input-world-unchanged",!memcmp(world,before,sizeof *world));
    free(world);free(before);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"work")){
        const size_t counts[]={0,1,128,512};
        for(size_t i=0;i<sizeof counts/sizeof *counts;++i){int result=compare_case(counts[i],true,1,true);if(result)return result;}
        return 0;
    }
    if(!strcmp(argv[1],"live"))return compare_case(7,true,1,false);
    if(!strcmp(argv[1],"raw"))return compare_case(7,false,0,false);
    if(!strcmp(argv[1],"domains")){
        for(unsigned mode=0;mode<4;++mode)for(unsigned deferred=0;deferred<2;++deferred){
            int result=compare_case(7,deferred!=0,mode,false);if(result)return result;}
        return 0;
    }
    return 2;
}
