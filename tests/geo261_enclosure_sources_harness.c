#include "enclosure_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x,name) do{if(!(x)){fprintf(stderr,"ASSERT:%s\n",name);exit(1);}}while(0)
enum { ENC=18,PLACE=7,REGION=8,MAX_ITEMS=8 };
typedef struct {
    GeoEvalContext *graph;GeoRegionStore *regions;GeoPlacementStore *placements;GeoEnclosureStore *enclosures;
    GeoEnclosureSources *sources;GeoPlacementSources *base;
    GeoRegionDefinition typed_regions[MAX_ITEMS];GeoRegionView region_views[MAX_ITEMS];
    GeoFrame typed_frames[MAX_ITEMS];uint32_t frame_ids[MAX_ITEMS];size_t region_count,frame_count;
    unsigned region_calls[MAX_ITEMS],frame_calls[MAX_ITEMS];uint32_t fail_region,fail_frame,cycle_frame;
    bool multi_region,bad_frame;unsigned cycles;int cycle_axis,cycle_slot;
} Fixture;
static GeoFrame zplus(GeoCoord z)
{return (GeoFrame){{0,0,z},{1,0,0},{0,1,0},{0,0,1}};}
static GeoFrame zminus(GeoCoord z)
{return (GeoFrame){{0,100,z},{1,0,0},{0,-1,0},{0,0,-1}};}
static GeoFrame xminus(GeoCoord x)
{return (GeoFrame){{x,0,100},{0,1,0},{0,0,-1},{-1,0,0}};}
static GeoRegionDefinition square(uint32_t id,GeoCoord width,GeoCoord height)
{
    GeoRegionDefinition r={0};r.id=id;r.outline.count=4;
    r.outline.v[0]=(GeoPoint2){0,0};r.outline.v[1]=(GeoPoint2){width,0};
    r.outline.v[2]=(GeoPoint2){width,height};r.outline.v[3]=(GeoPoint2){0,height};return r;
}
static Fixture *make(void)
{
    Fixture *f=calloc(1,sizeof *f);CHECK(f,"fixture-allocation");
    f->graph=geo_eval_create(501,37);f->regions=geo_regions_create();f->placements=geo_placements_create();
    f->enclosures=geo_enclosures_create();CHECK(f->graph&&f->regions&&f->placements&&f->enclosures,"fixture-stores");
    return f;
}
static void add_region(Fixture *f,uint32_t id,GeoCoord width,GeoCoord height)
{
    CHECK(f->region_count<MAX_ITEMS,"fixture-region-capacity");
    GeoRegionDefinition r=square(id,width,height);CHECK(geo_regions_put(f->regions,&r),"fixture-region-put");
    f->typed_regions[f->region_count++]=r;
}
static void add_placement(Fixture *f,uint32_t id,uint32_t region,GeoFrame frame)
{
    CHECK(f->frame_count<MAX_ITEMS,"fixture-frame-capacity");
    GeoPlacementDefinition p={0};p.id=id;p.domain=GEO_PLACEMENT_REGION_REF;p.region_id=region;p.frame=frame;
    CHECK(geo_placements_stage(f->placements,&p),"fixture-placement-put");
    f->frame_ids[f->frame_count]=id;f->typed_frames[f->frame_count++]=frame;
}
static void members(Fixture *f,uint32_t id,const uint32_t *ids,size_t count)
{
    GeoEnclosure e;memset(&e,0xa5,sizeof e);e.id=id;e.member_count=count;
    for(size_t i=0;i<count;++i)e.member_ids[i]=ids[i];
    for(int i=0;i<3;++i){e.min[i]=-9000-i;e.max[i]=9000+i;}e.closed=true;
    CHECK(geo_enclosures_stage(f->enclosures,&e),"fixture-members-put");
}
static size_t region_index(Fixture *f,uint32_t id)
{size_t i=0;while(i<f->region_count&&f->typed_regions[i].id!=id)++i;return i;}
static size_t frame_index(Fixture *f,uint32_t id)
{size_t i=0;while(i<f->frame_count&&f->frame_ids[i]!=id)++i;return i;}
static bool describe(void *state,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    Fixture *f=state;uint32_t id;GeoSourceDescriptor d={0};d.unit=GEO_UNIT_LENGTH;d.context.axis=-1;
    if(ref->provider==REGION){
        if(!geo_region_source_decode(ref,&id)||region_index(f,id)==f->region_count)return false;
        d.kind=GEO_SOURCE_REGION_SET;
    }else{
        GeoPlacementSourceKind kind;
        if(ref->provider!=PLACE||!geo_placement_source_decode(ref,&kind,&id)||kind!=GEO_PLACEMENT_SOURCE_FRAME||
            frame_index(f,id)==f->frame_count)return false;
        d.kind=GEO_SOURCE_FRAME;d.context.has_placement=true;d.context.placement=id;
    }
    *out=d;return true;
}
static bool evaluate(void *state,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    Fixture *f=state;uint32_t id;if(graph!=f->graph)return false;
    if(ref->provider==REGION){
        if(!geo_region_source_decode(ref,&id))return false;size_t i=region_index(f,id);if(i==f->region_count)return false;
        ++f->region_calls[i];if(id==f->fail_region)return false;
        GeoRegionDefinition *r=&f->typed_regions[i];f->region_views[i]=(GeoRegionView){{r->outline.v,r->outline.count},NULL,0};
        out->kind=GEO_SOURCE_REGION_SET;out->as.regions=(GeoRegionSetView){&f->region_views[i],f->multi_region?2:1};return true;
    }
    GeoPlacementSourceKind kind;if(!geo_placement_source_decode(ref,&kind,&id))return false;
    size_t i=frame_index(f,id);if(i==f->frame_count)return false;++f->frame_calls[i];if(id==f->fail_frame)return false;
    if(id==f->cycle_frame){
        GeoEnclosureSourceKey key;GeoSourceValue value;
        GeoSourceStatus result=geo_eval_source(graph,geo_enclosure_source_ref(ENC,GEO_ENCLOSURE_SOURCE_AXIS_BOUND,9,
            f->cycle_axis,f->cycle_slot,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&value);
        if(result==GEO_SOURCE_CYCLE)++f->cycles;return result==GEO_SOURCE_OK;
    }
    out->kind=GEO_SOURCE_FRAME;out->as.frame=f->typed_frames[i];
    if(f->bad_frame)out->as.frame.normal=(GeoVector3){0,0,0};return true;
}
static void start(Fixture *f,bool actual)
{
    if(actual){
        f->base=geo_placement_sources_register(f->graph,f->placements,f->regions,PLACE,REGION,NULL,NULL);
        CHECK(f->base,"fixture-actual-placement-provider");
    }else{
        GeoSourceProvider providers[]={
            {REGION,"test.regions","test/1",f,describe,evaluate},
            {PLACE,"test.frames","test/1",f,describe,evaluate}};
        CHECK(geo_eval_register_many(f->graph,providers,2),"fixture-typed-providers");
    }
    f->sources=geo_enclosure_sources_register(f->graph,f->enclosures,f->regions,f->placements,ENC,PLACE,REGION);
    CHECK(f->sources,"fixture-enclosure-provider");
}
static void destroy(Fixture *f)
{
    geo_eval_destroy(f->graph);geo_enclosure_sources_destroy(f->sources);geo_placement_sources_destroy(f->base);
    geo_enclosures_destroy(f->enclosures);geo_placements_destroy(f->placements);geo_regions_destroy(f->regions);free(f);
}
static Fixture *one(bool actual)
{
    Fixture *f=make();add_region(f,1,100,100);add_placement(f,11,1,zplus(100));
    uint32_t ids[]={1};members(f,9,ids,1);start(f,actual);return f;
}
static GeoSourceStatus source(Fixture *f,GeoEnclosureSourceKind kind,uint32_t id,int axis,int slot,GeoSourceValue *out)
{
    GeoEnclosureSourceKey key;return geo_eval_source(f->graph,geo_enclosure_source_ref(ENC,kind,id,axis,slot,&key),
        GEO_DEPENDENCY_VALUE_REQUIRED,out);
}
static void keys(void)
{
    GeoEnclosureSourceKey key;GeoSourceRef ref=geo_enclosure_source_ref(ENC,GEO_ENCLOSURE_SOURCE_AXIS_BOUND,0x01020304,2,1,&key);
    const unsigned char expected[]={3,1,2,3,4,3,2};
    CHECK(ref.provider==ENC&&ref.key_size==7&&!memcmp(ref.key,expected,7),"key-seven-byte-layout");
    GeoEnclosureSourceKind kind;uint32_t id;int axis,slot;
    for(unsigned i=0;i<2;++i){uint32_t value=i?UINT32_MAX:0;
        ref=geo_enclosure_source_ref(ENC,GEO_ENCLOSURE_SOURCE_RESULT,value,-1,-1,&key);
        CHECK(geo_enclosure_source_decode(&ref,&kind,&id,&axis,&slot)&&kind==GEO_ENCLOSURE_SOURCE_RESULT&&id==value&&axis==-1&&slot==-1,"key-zero-max-roundtrip");
    }
    CHECK(!geo_enclosure_source_ref(ENC,GEO_ENCLOSURE_SOURCE_DEFINITION,1,0,-1,&key).key_size&&
        !geo_enclosure_source_ref(ENC,GEO_ENCLOSURE_SOURCE_AXIS_BOUND,1,3,0,&key).key_size&&
        !geo_enclosure_source_ref(ENC,GEO_ENCLOSURE_SOURCE_AXIS_BOUND,1,0,2,&key).key_size&&
        !geo_enclosure_source_ref(ENC,(GeoEnclosureSourceKind)4,1,-1,-1,&key).key_size&&
        !geo_enclosure_source_ref(ENC,GEO_ENCLOSURE_SOURCE_RESULT,1,-1,-1,NULL).key_size,"key-axis-slot-domain");
    kind=(GeoEnclosureSourceKind)99;id=123;axis=55;slot=66;
    unsigned char bad[]={2,0,0,0,1,1,0};ref=(GeoSourceRef){ENC,bad,7};
    CHECK(!geo_enclosure_source_decode(&ref,&kind,&id,&axis,&slot)&&kind==99&&id==123&&axis==55&&slot==66,"key-decode-failure-atomic");
}
static void definition(void)
{
    Fixture *f=make();uint32_t ids[]={0,UINT32_MAX};members(f,0x01020304,ids,2);members(f,0,NULL,0);start(f,false);
    GeoSourceValue value;CHECK(source(f,GEO_ENCLOSURE_SOURCE_DEFINITION,0x01020304,-1,-1,&value)==GEO_SOURCE_OK,"definition-request");
    const unsigned char expected[]={1,2,3,4,0,0,0,2,0,0,0,0,255,255,255,255};
    CHECK(value.kind==GEO_SOURCE_DEFINITION&&!strcmp(value.as.definition.schema,"geo.enclosure.members/1")&&
        value.as.definition.content_size==sizeof expected&&!memcmp(value.as.definition.content,expected,sizeof expected),"definition-canonical-members-only");
    GeoSourceDescriptor descriptor;GeoEnclosureSourceKey key;
    CHECK(geo_eval_describe(f->graph,geo_enclosure_source_ref(ENC,GEO_ENCLOSURE_SOURCE_DEFINITION,0,-1,-1,&key),&descriptor)==GEO_SOURCE_OK&&
        descriptor.kind==GEO_SOURCE_DEFINITION&&descriptor.unit==GEO_UNIT_SCALAR&&descriptor.context.axis==-1,"definition-scalar-metadata");
    GeoEnclosure result;memset(&result,0xa5,sizeof result);GeoEnclosure empty;memset(&empty,0,sizeof empty);
    CHECK(geo_enclosure_sources_value(f->sources,0,&result,NULL)&&!memcmp(&result,&empty,sizeof result),"definition-empty-result");
    CHECK(source(f,GEO_ENCLOSURE_SOURCE_RESULT,0,-1,-1,&value)==GEO_SOURCE_OK&&value.kind==GEO_SOURCE_DEFINITION&&
        !strcmp(value.as.definition.schema,"geo.enclosure.result/1")&&value.as.definition.content_size==57,"definition-result-not-box");
    CHECK(geo_eval_provider_count(f->graph)==3&&geo_enclosure_sources_count(f->sources)==2&&
        geo_enclosure_sources_at(f->sources,0)->id==0x01020304&&geo_enclosure_sources_at(f->sources,1)->id==0&&
        !geo_enclosure_sources_at(f->sources,2)&&!geo_enclosure_sources_count(NULL),"definition-enumeration");
    for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView node;CHECK(geo_eval_node_at(f->graph,i,&node)&&node.source.provider==ENC,"definition-no-upstream-evaluation");}
    destroy(f);
}
static void typed(void)
{
    Fixture *f=one(false);f->typed_regions[0]=square(1,140,230);
    f->typed_frames[0]=(GeoFrame){{-10,-20,330},{1,0,0},{0,1,0},{0,0,1}};
    GeoEnclosure out;CHECK(geo_enclosure_sources_value(f->sources,9,&out,NULL),"typed-result-request");
    CHECK(out.max[0]-out.min[0]==140&&out.max[1]-out.min[1]==230,"typed-region-overrides-owned");
    CHECK(out.min[0]==-10&&out.min[1]==-20&&out.min[2]==0&&out.max[2]==330&&!out.closed,"typed-frame-overrides-owned");
    GeoSourceValue value;const unsigned char expected[]={
        0,0,0,9,0,0,0,1,0,0,0,1,
        255,255,255,255,255,255,255,246,255,255,255,255,255,255,255,236,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,130,0,0,0,0,0,0,0,210,0,0,0,0,0,0,1,74,0};
    CHECK(source(f,GEO_ENCLOSURE_SOURCE_RESULT,9,-1,-1,&value)==GEO_SOURCE_OK&&value.kind==GEO_SOURCE_DEFINITION&&
        !strcmp(value.as.definition.schema,"geo.enclosure.result/1")&&value.as.definition.content_size==sizeof expected&&
        !memcmp(value.as.definition.content,expected,sizeof expected),"typed-result-canonical-signed-coordinates");destroy(f);
    f=one(false);f->multi_region=true;CHECK(!geo_enclosure_sources_value(f->sources,9,&out,NULL),"typed-reject-multi-region");destroy(f);
    f=one(false);f->bad_frame=true;CHECK(!geo_enclosure_sources_value(f->sources,9,&out,NULL),"typed-reject-invalid-frame");destroy(f);
    f=one(false);f->typed_regions[0].outline.count=GEO_LOOP_MAX_VERTICES+1;
    CHECK(!geo_enclosure_sources_value(f->sources,9,&out,NULL),"typed-reject-unbounded-region");destroy(f);
    f=one(true);CHECK(geo_enclosure_sources_value(f->sources,9,&out,NULL)&&out.max[0]==100&&out.max[1]==100&&out.max[2]==100,"typed-actual-placement-provider");destroy(f);
}
static void graph(void)
{
    Fixture *f=one(false);GeoEnclosure out;CHECK(geo_enclosure_sources_value(f->sources,9,&out,NULL),"graph-result");
    bool definition_edge=false,region_edge=false,frame_edge=false;
    for(size_t i=0;i<geo_eval_edge_count(f->graph);++i){GeoSourceEdge edge;GeoSourceNodeView node;
        CHECK(geo_eval_edge_at(f->graph,i,&edge)&&geo_eval_node_at(f->graph,edge.source,&node),"graph-edge-readable");
        if(edge.kind==GEO_DEPENDENCY_DEFINITION_REQUIRED&&node.source.provider==ENC){
            GeoEnclosureSourceKind kind;uint32_t id;int axis,slot;
            definition_edge=geo_enclosure_source_decode(&node.source,&kind,&id,&axis,&slot)&&kind==GEO_ENCLOSURE_SOURCE_DEFINITION&&id==9&&node.state==GEO_NODE_NEW;
        }
        if(edge.kind==GEO_DEPENDENCY_VALUE_REQUIRED&&node.source.provider==REGION)region_edge=true;
        if(edge.kind==GEO_DEPENDENCY_VALUE_REQUIRED&&node.source.provider==PLACE)frame_edge=true;
    }
    CHECK(definition_edge,"graph-definition-edge-new");CHECK(region_edge&&frame_edge&&geo_eval_edge_count(f->graph)==3,"graph-value-region-frame-edges");
    CHECK(geo_enclosure_sources_value(f->sources,9,&out,NULL)&&f->region_calls[0]==1&&f->frame_calls[0]==1,"graph-success-memoized");
    Fixture *other=one(false);other->typed_frames[0]=zplus(250);
    CHECK(geo_enclosure_sources_value(other->sources,9,&out,NULL)&&out.max[2]==250&&
        geo_enclosure_sources_value(f->sources,9,&out,NULL)&&out.max[2]==100,"graph-candidate-isolation");destroy(other);
    CHECK(geo_eval_reset(f->graph)&&geo_eval_provider_count(f->graph)==0,"graph-reset-clears-provider-bindings");
    geo_enclosure_sources_destroy(f->sources);f->sources=NULL;f->typed_frames[0]=zplus(175);start(f,false);
    CHECK(geo_enclosure_sources_value(f->sources,9,&out,NULL)&&out.max[2]==175&&f->frame_calls[0]==2,"graph-reset-reregister");destroy(f);
    for(int nonmatching=0;nonmatching<2;++nonmatching){
        f=one(false);f->cycle_frame=11;f->cycle_axis=nonmatching?0:2;f->cycle_slot=1;
        GeoCoord coordinate=777;
        CHECK(!geo_enclosure_sources_axis_bound(f->sources,9,f->cycle_axis,1,&coordinate)&&coordinate==777&&f->cycles==1,
            nonmatching?"graph-nonmatching-frame-cycle":"graph-matching-frame-cycle");destroy(f);
    }
}
static void ordered(void)
{
    Fixture *f=make();add_region(f,1,100,100);add_region(f,2,100,100);
    add_placement(f,11,1,zplus(100));add_placement(f,22,2,zplus(200));uint32_t ids[]={1,2,99};members(f,9,ids,3);
    f->fail_region=2;start(f,false);GeoEnclosure out;GeoEnclosureFault fault={0};
    CHECK(!geo_enclosure_sources_value(f->sources,9,&out,&fault)&&fault.kind==GEO_ENCLOSURE_FAULT_SLOT_TAKEN&&
        fault.member_id==2&&fault.axis==2&&f->region_calls[1]==0,"ordered-slot-before-region-failure");destroy(f);
    f=make();for(uint32_t id=1;id<=3;++id)add_region(f,id,100,100);
    add_placement(f,11,1,zplus(100));add_placement(f,22,2,xminus(0));add_placement(f,33,3,zminus(0));
    uint32_t three[]={1,2,3};members(f,9,three,3);f->typed_regions[1]=square(2,200,100);f->fail_frame=33;start(f,false);
    CHECK(!geo_enclosure_sources_value(f->sources,9,&out,&fault)&&fault.kind==GEO_ENCLOSURE_FAULT_EXTENT_MISMATCH&&
        fault.member_id==2&&fault.axis==1&&f->frame_calls[2]==0,"ordered-extent-before-later-frame-failure");destroy(f);
    for(int mode=0;mode<4;++mode){
        f=make();add_region(f,1,100,100);if(mode!=2)add_placement(f,11,1,zplus(100));
        if(mode==3)add_placement(f,12,1,zplus(200));uint32_t members_id[]={mode==0?99u:1u,1};
        members(f,9,members_id,mode==1?2:1);start(f,false);
        GeoEnclosureFaultKind expected[]={GEO_ENCLOSURE_FAULT_MISSING_REGION,GEO_ENCLOSURE_FAULT_DUPLICATE_REGION,
            GEO_ENCLOSURE_FAULT_NO_CARRIER,GEO_ENCLOSURE_FAULT_AMBIGUOUS_CARRIER};
        CHECK(!geo_enclosure_sources_value(f->sources,9,&out,&fault)&&fault.kind==expected[mode]&&fault.axis==-1&&
            (mode==1||f->frame_calls[0]+f->frame_calls[1]==0),"ordered-member-identity-faults");destroy(f);
    }
    for(int inverted=0;inverted<2;++inverted){
        f=make();add_region(f,1,100,100);add_region(f,2,100,100);
        add_placement(f,11,1,zplus(inverted?0:100));add_placement(f,22,2,inverted?zminus(10):xminus(50));
        members(f,9,ids,3);start(f,false);
        CHECK(!geo_enclosure_sources_value(f->sources,9,&out,&fault)&&fault.kind==GEO_ENCLOSURE_FAULT_MISSING_REGION&&fault.member_id==99,
            inverted?"ordered-inverted-deferred":"ordered-plane-deferred");destroy(f);
    }
}
static void axis(void)
{
    Fixture *f=one(false);GeoCoord bound=777;GeoSourceValue value;
    CHECK(!geo_enclosure_sources_axis_bound(f->sources,9,0,1,&bound)&&bound==777,"axis-no-bbox-fallback");
    CHECK(geo_enclosure_sources_axis_bound(f->sources,9,2,1,&bound)&&bound==100,"axis-actual-normal-slot");
    GeoEnclosureSourceKey key;GeoSourceDescriptor descriptor;
    CHECK(geo_eval_describe(f->graph,geo_enclosure_source_ref(ENC,GEO_ENCLOSURE_SOURCE_AXIS_BOUND,9,2,1,&key),&descriptor)==GEO_SOURCE_OK&&
        descriptor.kind==GEO_SOURCE_AXIS_POSITION&&descriptor.unit==GEO_UNIT_LENGTH&&descriptor.context.axis==2&&!descriptor.context.has_placement,"axis-length-global-metadata");
    bool result_node=false;for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView node;geo_eval_node_at(f->graph,i,&node);
        if(node.source.provider==ENC){GeoEnclosureSourceKind kind;uint32_t id;int a,s;
            if(geo_enclosure_source_decode(&node.source,&kind,&id,&a,&s)&&kind==GEO_ENCLOSURE_SOURCE_RESULT)result_node=true;}}
    CHECK(!result_node&&f->region_calls[0]==0,"axis-no-result-dependency");destroy(f);
    f=make();add_region(f,1,100,100);add_region(f,2,100,100);
    add_placement(f,11,1,zplus(100));add_placement(f,22,2,zplus(200));uint32_t ids[]={2,1};members(f,9,ids,2);start(f,false);
    CHECK(geo_enclosure_sources_axis_bound(f->sources,9,2,1,&bound)&&bound==200&&f->frame_calls[0]==0,"axis-member-before-placement");destroy(f);
    f=make();add_region(f,1,100,100);add_placement(f,11,1,zplus(100));add_placement(f,12,1,zplus(200));
    uint32_t single[]={1};members(f,9,single,1);f->fail_frame=12;start(f,false);
    CHECK(geo_enclosure_sources_axis_bound(f->sources,9,2,1,&bound)&&bound==100&&f->frame_calls[1]==0,"axis-ambiguous-first");destroy(f);
    f=one(false);f->typed_frames[0]=(GeoFrame){{350,0,0},{0,1,0},{0,0,1},{1,0,0}};
    CHECK(geo_enclosure_sources_axis_bound(f->sources,9,0,1,&bound)&&bound==350,"axis-typed-normal-change");
    CHECK(source(f,GEO_ENCLOSURE_SOURCE_AXIS_BOUND,9,0,1,&value)==GEO_SOURCE_OK&&value.as.position.coordinate==350&&value.as.position.context.axis==0,"axis-published-position");destroy(f);
}
static void atomic(void)
{
    Fixture *f=one(false);f->fail_region=1;GeoEnclosure out,before;memset(&out,0xa5,sizeof out);memcpy(&before,&out,sizeof out);
    GeoEnclosureFault fault={GEO_ENCLOSURE_FAULT_INVERTED,123,2},old_fault;memcpy(&old_fault,&fault,sizeof fault);
    CHECK(!geo_enclosure_sources_value(f->sources,9,&out,&fault)&&!memcmp(&out,&before,sizeof out)&&!memcmp(&fault,&old_fault,sizeof fault),"atomic-upstream-preserves-output-fault");destroy(f);
    f=one(false);GeoRegionDefinition raw_region;GeoPlacementDefinition raw_placement;GeoEnclosure raw_enclosure;
    memcpy(&raw_region,geo_regions_at(f->regions,0),sizeof raw_region);memcpy(&raw_placement,geo_placements_at(f->placements,0),sizeof raw_placement);
    memcpy(&raw_enclosure,geo_enclosures_at(f->enclosures,0),sizeof raw_enclosure);f->typed_regions[0]=square(1,140,150);f->typed_frames[0]=zplus(250);
    CHECK(geo_enclosure_sources_value(f->sources,9,&out,&fault)&&!memcmp(&fault,&old_fault,sizeof fault),"atomic-success-preserves-fault");
    CHECK(!memcmp(&raw_region,geo_regions_at(f->regions,0),sizeof raw_region)&&!memcmp(&raw_placement,geo_placements_at(f->placements,0),sizeof raw_placement)&&
        !memcmp(&raw_enclosure,geo_enclosures_at(f->enclosures,0),sizeof raw_enclosure),"atomic-owned-stores-unchanged");destroy(f);
    f=make();uint32_t id[]={99};members(f,9,id,1);start(f,false);memcpy(&out,&before,sizeof out);
    CHECK(!geo_enclosure_sources_value(f->sources,9,&out,&fault)&&!memcmp(&out,&before,sizeof out)&&fault.kind==GEO_ENCLOSURE_FAULT_MISSING_REGION,"atomic-geometry-preserves-output");
    CHECK(geo_eval_seal(f->graph),"atomic-seal");memcpy(&fault,&old_fault,sizeof fault);
    CHECK(!geo_enclosure_sources_value(f->sources,9,&out,&fault)&&!memcmp(&out,&before,sizeof out)&&!memcmp(&fault,&old_fault,sizeof fault),"atomic-sealed-failure-preserves-fault");destroy(f);
}
static void registration(void)
{
    Fixture *f=make();
    CHECK(!geo_enclosure_sources_register(f->graph,f->enclosures,f->regions,f->placements,0,PLACE,REGION)&&
        !geo_enclosure_sources_register(f->graph,f->enclosures,f->regions,f->placements,ENC,ENC,REGION)&&
        !geo_enclosure_sources_register(f->graph,f->enclosures,f->regions,f->placements,ENC,PLACE,PLACE)&&
        !geo_enclosure_sources_register(NULL,f->enclosures,f->regions,f->placements,ENC,PLACE,REGION)&&
        geo_eval_provider_count(f->graph)==0,"registration-invalid-tokens-atomic");
    start(f,false);size_t count=geo_eval_provider_count(f->graph);
    CHECK(!geo_enclosure_sources_register(f->graph,f->enclosures,f->regions,f->placements,ENC,PLACE,REGION)&&
        geo_eval_provider_count(f->graph)==count,"registration-duplicate-atomic");
    CHECK(geo_eval_seal(f->graph)&&!geo_enclosure_sources_register(f->graph,f->enclosures,f->regions,f->placements,19,PLACE,REGION)&&
        geo_eval_provider_count(f->graph)==count,"registration-sealed-atomic");destroy(f);
    f=one(false);geo_enclosure_sources_destroy(f->sources);f->sources=NULL;destroy(f);
    geo_enclosure_sources_destroy(NULL);
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"keys"))keys();else if(!strcmp(argv[1],"definition"))definition();
    else if(!strcmp(argv[1],"typed"))typed();else if(!strcmp(argv[1],"graph"))graph();
    else if(!strcmp(argv[1],"ordered"))ordered();else if(!strcmp(argv[1],"axis"))axis();
    else if(!strcmp(argv[1],"atomic"))atomic();else if(!strcmp(argv[1],"registration"))registration();else return 2;
    return 0;
}
