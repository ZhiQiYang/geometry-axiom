/* Real K placement sources -> candidate facts -> existing W ordered policy ->
 * owned collection -> FEATURE -> caller output. Test-only feature transform
 * proves the final wrapper consumes returned graph values, not hidden DTOs. */
#include "contact_sources.h"
#include "placement_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(tag,x) do{if(!(x)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
enum { CONTACT_TOKEN=16,PLACEMENT_TOKEN=2,REGION_TOKEN=3,BOX_TOKEN=4 };
static bool transform_features;
void contact_test_transform_feature(GeoSegment3 *segment)
{
    if(!transform_features)return;
    segment->start.x+=1000;segment->end.x+=1000;
    segment->start.y+=2000;segment->end.y+=2000;
}
typedef struct {
    GeoEvalContext *graph;
    GeoPlacementStore *placements;
    GeoRegionStore *regions;
    GeoPlacementSources *placement_sources;
    WoodContactSources *contacts;
    WoodMember members[4];
    GeoBox3 boxes[4];
    uint64_t order[4];
    uint32_t member_placement[4];
    unsigned box_calls[4],unplaced_calls,facts_calls;
    size_t member_count;
    WoodBoundaryPolicy policy[2];
    bool fail,invalid,cycle;
    GeoSourceStatus cycle_status;
} Fixture;
static GeoFrame frame(GeoCoord x)
{return (GeoFrame){{x,0,0},{1,0,0},{0,1,0},{0,0,1}};}
static void loop_box(GeoRegionLoop *loop,GeoCoord u,GeoCoord v,GeoCoord size)
{
    memset(loop,0,sizeof *loop);loop->count=4;loop->v[0]=(GeoPoint2){u,v};loop->v[1]=(GeoPoint2){u+size,v};
    loop->v[2]=(GeoPoint2){u+size,v+size};loop->v[3]=(GeoPoint2){u,v+size};
}
static GeoBox3 member_box(GeoCoord a,GeoCoord b,GeoCoord c,GeoCoord d)
{return (GeoBox3){.frame={{a,b,0},{1,0,0},{0,1,0},{0,0,1}},.extent={c-a,d-b,10}};}
static int member_index(const Fixture *f,const GeoSourceRef *ref)
{
    uint32_t id;if(ref->key_size!=sizeof id||!ref->key)return -1;memcpy(&id,ref->key,sizeof id);
    for(size_t i=0;i<f->member_count;++i)if(f->members[i].id==id)return (int)i;return -1;
}
static bool box_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    Fixture *f=user;if(member_index(f,ref)<0)return false;memset(out,0,sizeof *out);
    out->kind=GEO_SOURCE_BOX;out->unit=GEO_UNIT_LENGTH;out->context=(GeoSourceContext){true,7,-1};return true;
}
static bool box_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    Fixture *f=user;int i=member_index(f,ref);if(graph!=f->graph||i<0)return false;
    ++f->box_calls[i];if(!f->members[i].placed){++f->unplaced_calls;return false;}
    out->kind=GEO_SOURCE_BOX;out->as.box=f->boxes[i];return true;
}
static bool copy_loop(WoodBoundaryLoop *out,GeoLoop2View loop,const WoodEdgeFixity *fixity)
{
    if(loop.count>GEO_LOOP_MAX_VERTICES||(loop.count&&!loop.v))return false;
    out->count=loop.count;
    for(size_t i=0;i<loop.count;++i){out->v[i]=loop.v[i];out->fixity[i]=fixity[i];}return true;
}
static bool facts_callback(void *user,GeoEvalContext *graph,const WoodContactSourceRequest *request,WoodContactSourceFacts *out)
{
    Fixture *f=user;if(graph!=f->graph)return false;++f->facts_calls;
    GeoPlacementSourceKey key;GeoSourceValue fv,rv;
    if(geo_eval_source(graph,geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_FRAME,request->placement_id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&fv)!=GEO_SOURCE_OK||fv.kind!=GEO_SOURCE_FRAME)return false;
    if(geo_eval_source(graph,geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_REGIONS,request->placement_id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&rv)!=GEO_SOURCE_OK||rv.kind!=GEO_SOURCE_REGION_SET)return false;
    if(f->fail)return false;
    if(f->cycle){
        for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView n;WoodContactSourceKind kind;uint64_t query,index;
            if(geo_eval_node_at(graph,i,&n)&&n.source.provider==CONTACT_TOKEN&&n.state==GEO_NODE_ACTIVE&&
               wood_contact_source_decode(&n.source,&kind,&query,&index)&&kind==WOOD_CONTACT_SOURCE_COLLECTION){
                GeoSourceValue ignored;f->cycle_status=geo_eval_source(graph,n.source,GEO_DEPENDENCY_VALUE_REQUIRED,&ignored);return false;
            }
        }
        return false;
    }
    if(rv.as.regions.count>2)return false;out->region_count=rv.as.regions.count;
    for(size_t c=0;c<rv.as.regions.count;++c){const GeoRegionView *r=&rv.as.regions.regions[c];WoodBoundaryRegion *b=&out->regions[c];
        b->id=f->policy[c].id;b->kind=f->policy[c].kind;b->hole_count=r->hole_count;
        if(r->hole_count>GEO_REGION_MAX_HOLES||!copy_loop(&b->outline,r->outline,f->policy[c].fixity[0]))return false;
        for(size_t h=0;h<r->hole_count;++h)if(!copy_loop(&b->holes[h],r->holes[h],f->policy[c].fixity[h+1]))return false;
    }
    out->member_count=f->member_count;
    for(size_t i=0;i<f->member_count;++i){WoodContactMemberFact *fact=&out->members[i];
        fact->member=&f->members[i];fact->placement_id=f->member_placement[i];fact->order=f->order[i];
        if(!f->members[i].placed||fact->placement_id!=request->placement_id)continue;
        uint32_t id=f->members[i].id;GeoSourceValue value;
        if(geo_eval_source(graph,(GeoSourceRef){BOX_TOKEN,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||value.kind!=GEO_SOURCE_BOX)return false;
        GeoPoint3 lo=value.as.box.frame.origin,hi={lo.x+value.as.box.extent[0],lo.y+value.as.box.extent[1],lo.z+value.as.box.extent[2]};
        fact->footprint=geo_aabb_project_uv(&fv.as.frame,lo,hi);fact->footprint_valid=true;
    }
    if(f->invalid)out->region_count=WOOD_CONTACT_COMPONENT_CAPACITY+1;
    return true;
}
static int setup(Fixture *f,uint64_t candidate,GeoCoord frame_origin,GeoCoord region_offset,unsigned components)
{
    memset(f,0,sizeof *f);f->graph=geo_eval_create(candidate,73);f->placements=geo_placements_create();f->regions=geo_regions_create();
    CHECK("contact-fixture-stores",f->graph&&f->placements&&f->regions);
    GeoPlacementDefinition p;memset(&p,0,sizeof p);p.id=7;p.frame=frame(frame_origin);p.domain=GEO_PLACEMENT_REGION_SET;p.component_count=components;
    for(size_t c=0;c<components;++c){GeoRegionDefinition *r=&p.components[c];r->id=(uint32_t)(7+c);
        loop_box(&r->outline,region_offset+(GeoCoord)c*200,(GeoCoord)c*300,100);
        if(components==2){r->hole_count=1;loop_box(&r->holes[0],region_offset+20+(GeoCoord)c*200,30+(GeoCoord)c*300,10);}
        f->policy[c].id=r->id;
        for(size_t h=0;h<=GEO_REGION_MAX_HOLES;++h)for(size_t i=0;i<GEO_LOOP_MAX_VERTICES;++i)f->policy[c].fixity[h][i]=WOOD_EDGE_FIXED;
    }
    f->policy[0].fixity[0][3]=WOOD_EDGE_FREE;
    f->policy[1].fixity[0][1]=WOOD_EDGE_FREE;f->policy[1].fixity[1][3]=(WoodEdgeFixity)-13;
    CHECK("contact-fixture-placement",geo_placements_put(f->placements,&p,f->regions));
    f->placement_sources=geo_placement_sources_register(f->graph,f->placements,f->regions,PLACEMENT_TOKEN,REGION_TOKEN,NULL,NULL);
    CHECK("contact-fixture-placement-provider",f->placement_sources);
    f->member_count=4;
    for(size_t i=0;i<4;++i){f->members[i].id=(uint32_t)(41+i);f->members[i].role=WOOD_MEMBER_ROLE_PRIMARY;f->members[i].placed=true;f->member_placement[i]=7;}
    f->boxes[0]=member_box(70,0,80,10);f->boxes[1]=member_box(20,20,30,30);f->boxes[2]=member_box(40,40,50,50);f->boxes[3]=member_box(55,60,65,70);
    f->order[0]=30;f->order[1]=10;f->order[2]=10;f->order[3]=20;
    GeoSourceProvider boxes={BOX_TOKEN,"test.member.box","actual-box/1",f,box_describe,box_evaluate};
    CHECK("contact-fixture-box-provider",geo_eval_register(f->graph,&boxes));
    f->contacts=wood_contact_sources_create(f->graph,CONTACT_TOKEN,facts_callback,f);CHECK("contact-fixture-contact-provider",f->contacts);
    CHECK("contact-registration-does-not-read-facts",f->facts_calls==0&&geo_eval_node_count(f->graph)==0);return 0;
}
static void dispose(Fixture *f,bool graph_first)
{
    if(graph_first){geo_eval_destroy(f->graph);wood_contact_sources_destroy(f->contacts);geo_placement_sources_destroy(f->placement_sources);}
    else{wood_contact_sources_destroy(f->contacts);geo_placement_sources_destroy(f->placement_sources);geo_eval_destroy(f->graph);}
    geo_placements_destroy(f->placements);geo_regions_destroy(f->regions);
}
static bool collect(Fixture *f,bool along,const WoodMember *exclude,WoodStopFace *out,size_t cap,size_t *count)
{WoodContactSourceRequest request={7,along,exclude};return wood_contact_sources_collect(f->contacts,&request,out,cap,count);}
static GeoSourceRef contact_ref(WoodContactSourceKind kind,uint64_t query,uint64_t index,WoodContactSourceKey *key)
{return wood_contact_source_ref(CONTACT_TOKEN,kind,query,index,key);}
static size_t node(GeoEvalContext *graph,GeoSourceRef ref)
{
    for(size_t i=0;i<geo_eval_node_count(graph);++i){GeoSourceNodeView n;
        if(geo_eval_node_at(graph,i,&n)&&n.source.provider==ref.provider&&n.source.key_size==ref.key_size&&!memcmp(n.source.key,ref.key,ref.key_size))return i;}
    return SIZE_MAX;
}
static bool edge(GeoEvalContext *graph,GeoSourceRef consumer,GeoSourceRef source)
{
    size_t a=node(graph,consumer),b=node(graph,source);
    for(size_t i=0;i<geo_eval_edge_count(graph);++i){GeoSourceEdge e;
        if(geo_eval_edge_at(graph,i,&e)&&e.consumer==a&&e.source==b&&e.kind==GEO_DEPENDENCY_VALUE_REQUIRED)return true;}return false;
}
static bool face(const WoodStopFace *f,int kind,uint32_t bid,uint32_t mid,int hole,int e,int fixity,GeoCoord fixed,GeoCoord lo,GeoCoord hi)
{return f->kind==kind&&f->boundary_id==bid&&f->timber_id==mid&&f->hole_index==hole&&f->edge_index==e&&f->fixity==fixity&&f->fixed==fixed&&f->lo==lo&&f->hi==hi;}
static uint64_t u64(const unsigned char *bytes)
{uint64_t value=0;for(unsigned i=0;i<8;++i)value=(value<<8)|bytes[i];return value;}
static int graph_case(void)
{
    Fixture f;CHECK("setup",setup(&f,1001,0,0,1)==0);f.member_count=1;f.boxes[0]=member_box(20,20,30,30);
    WoodStopFace out[8];size_t count=99;CHECK("contact-collection-success",collect(&f,false,NULL,out,8,&count));
    CHECK("contact-collection-runs-real-facts-and-policy",count==4&&f.facts_calls==1&&f.box_calls[0]==1);
    CHECK("contact-real-frame-region-box-values",face(out,WOOD_STOP_OUTLINE_EDGE,7,0,-1,1,1,100,0,100)&&
        face(out+1,WOOD_STOP_OUTLINE_EDGE,7,0,-1,3,0,0,0,100)&&face(out+2,WOOD_STOP_MEMBER_SIDE,0,41,-1,0,1,20,20,30));
    WoodContactSourceKey ck,fk;GeoPlacementSourceKey pk;uint32_t mid=41;
    GeoSourceRef collection=contact_ref(WOOD_CONTACT_SOURCE_COLLECTION,1,0,&ck);
    CHECK("contact-collection-requires-real-placement-frame",edge(f.graph,collection,geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_FRAME,7,&pk)));
    CHECK("contact-collection-requires-real-placement-regions",edge(f.graph,collection,geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_REGIONS,7,&pk)));
    CHECK("contact-collection-requires-placed-box",edge(f.graph,collection,(GeoSourceRef){BOX_TOKEN,&mid,sizeof mid}));
    for(size_t i=0;i<count;++i)CHECK("contact-feature-requires-collection-value",edge(f.graph,contact_ref(WOOD_CONTACT_SOURCE_FEATURE,1,i,&fk),collection));
    GeoSourceValue value;CHECK("contact-collection-typed-value",geo_eval_source(f.graph,collection,GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
        value.kind==GEO_SOURCE_DEFINITION&&!strcmp(value.as.definition.schema,"wood.contact.stops/1")&&value.as.definition.content_size==8+count*48);
    const unsigned char *bytes=value.as.definition.content;
    CHECK("contact-canonical-count-and-first-face",u64(bytes)==4&&u64(bytes+8+24)==100&&u64(bytes+8+32)==0&&u64(bytes+8+40)==100&&
        bytes[8+7]==7&&bytes[8+15]==255&&bytes[8+19]==1&&bytes[8+23]==1);
    GeoSourceDescriptor d;GeoSourceRef feature=contact_ref(WOOD_CONTACT_SOURCE_FEATURE,1,0,&fk);
    CHECK("contact-feature-context",geo_eval_describe(f.graph,feature,&d)==GEO_SOURCE_OK&&d.kind==GEO_SOURCE_FEATURE&&d.unit==GEO_UNIT_LENGTH&&d.context.has_placement&&d.context.placement==7&&d.context.axis==-1);
    CHECK("contact-feature-local-uv-value",geo_eval_source(f.graph,feature,GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&value.as.feature.key_size==24&&
        value.as.feature.segment.start.x==100&&value.as.feature.segment.start.y==0&&value.as.feature.segment.end.y==100&&value.as.feature.segment.start.z==0);
    CHECK("contact-exact-query-key",fk.bytes[0]==2&&u64(fk.bytes+1)==1&&u64(fk.bytes+9)==0);
    dispose(&f,true);return 0;
}
static int feature_consumption(void)
{
    Fixture f;CHECK("setup",setup(&f,1002,0,0,1)==0);f.member_count=0;WoodStopFace out[8];size_t count=99;transform_features=true;
    CHECK("contact-transformed-feature-success",collect(&f,false,NULL,out,8,&count)&&count==2);
    CHECK("contact-returned-feature-segment-consumed",face(out,WOOD_STOP_OUTLINE_EDGE,7,0,-1,1,1,1100,2000,2100)&&
        face(out+1,WOOD_STOP_OUTLINE_EDGE,7,0,-1,3,0,1000,2000,2100));
    CHECK("contact-transformed-along-v-success",collect(&f,true,NULL,out,8,&count)&&count==2);
    CHECK("contact-along-v-returned-segment-consumed",face(out,WOOD_STOP_OUTLINE_EDGE,7,0,-1,0,1,2000,1000,1100)&&
        face(out+1,WOOD_STOP_OUTLINE_EDGE,7,0,-1,2,1,2100,1000,1100));
    transform_features=false;dispose(&f,false);return 0;
}
static int upstream_changes(void)
{
    Fixture a,b;CHECK("setup-a",setup(&a,1003,0,0,1)==0);CHECK("setup-b",setup(&b,1004,100,1000,1)==0);
    a.member_count=b.member_count=1;a.boxes[0]=b.boxes[0]=member_box(20,20,30,30);WoodStopFace av[8],bv[8];size_t an=0,bn=0;
    CHECK("contact-two-candidate-queries",collect(&a,false,NULL,av,8,&an)&&collect(&b,false,NULL,bv,8,&bn)&&an==4&&bn==4);
    CHECK("contact-upstream-region-change-reaches-output",av[0].fixed==100&&bv[0].fixed==1100);
    CHECK("contact-upstream-frame-change-reaches-footprint",av[2].fixed==20&&bv[2].fixed==-80&&bv[3].fixed==-70);
    WoodContactSourceKey key;GeoSourceValue borrowed;CHECK("contact-borrowed-feature",geo_eval_source(b.graph,contact_ref(WOOD_CONTACT_SOURCE_FEATURE,1,2,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&borrowed)==GEO_SOURCE_OK);
    const void *metadata=borrowed.as.feature.key;unsigned char copy[24];memcpy(copy,metadata,24);
    const GeoSourceProvider *provider=geo_eval_provider_at(a.graph,3);GeoSourceValue untouched,saved;memset(&untouched,0x5a,sizeof untouched);memcpy(&saved,&untouched,sizeof saved);
    CHECK("contact-provider-candidate-binding",provider&&!provider->evaluate(provider->candidate_state,b.graph,&(GeoSourceRef){CONTACT_TOKEN,key.bytes,17},&untouched)&&!memcmp(&untouched,&saved,sizeof untouched));
    dispose(&a,false);CHECK("contact-other-candidate-metadata-remains-live",!memcmp(metadata,copy,24)&&borrowed.as.feature.segment.start.x==-80);
    CHECK("contact-query-keeps-prior-values",collect(&b,false,NULL,bv,8,&bn)&&bn==4&&!memcmp(metadata,copy,24));dispose(&b,true);return 0;
}
static int ordering(void)
{
    Fixture f;CHECK("setup",setup(&f,1005,0,0,0)==0);WoodStopFace out[12];size_t n=0;
    CHECK("contact-order-query",collect(&f,false,NULL,out,12,&n)&&n==8);
    CHECK("contact-placement-order-and-stable-ties",out[0].timber_id==42&&out[0].edge_index==0&&out[1].edge_index==1&&
        out[2].timber_id==43&&out[2].edge_index==0&&out[3].edge_index==1&&out[4].timber_id==44&&out[6].timber_id==41);
    dispose(&f,true);
    for(unsigned mode=0;mode<3;++mode){CHECK("dedup-setup",setup(&f,1006+mode,0,0,0)==0);f.member_count=2;
        f.boxes[0]=f.boxes[1]=member_box(20,20,30,30);f.order[0]=1;f.order[1]=mode?2:1;
        if(mode==2)f.boxes[1]=member_box(20,20,30,40);
        CHECK("contact-dedup-query",collect(&f,false,NULL,out,12,&n));
        CHECK("contact-equal-order-and-partial-cover-preserved",n==(mode==1?2u:4u)&&out[0].timber_id==41&&(mode==1||out[2].timber_id==42));dispose(&f,mode%2!=0);
    }
    return 0;
}
static int components(void)
{
    Fixture f;CHECK("setup",setup(&f,1010,0,0,2)==0);f.member_count=0;WoodStopFace out[12];size_t n=0;
    CHECK("contact-components-query",collect(&f,false,NULL,out,12,&n)&&n==8);
    CHECK("contact-component-outline-identities",face(out+4,WOOD_STOP_OUTLINE_EDGE,8,0,-1,33,0,300,300,400)&&face(out+5,WOOD_STOP_OUTLINE_EDGE,8,0,-1,35,1,200,300,400));
    CHECK("contact-hole-indices-and-free-metadata",face(out+2,WOOD_STOP_HOLE_EDGE,7,0,0,1,1,30,30,40)&&
        face(out+6,WOOD_STOP_HOLE_EDGE,8,0,8,1,1,230,330,340)&&face(out+7,WOOD_STOP_HOLE_EDGE,8,0,8,3,-13,220,330,340));
    CHECK("contact-components-along-v",collect(&f,true,NULL,out,12,&n)&&n==8&&face(out,WOOD_STOP_OUTLINE_EDGE,7,0,-1,0,1,0,0,100)&&
        face(out+4,WOOD_STOP_OUTLINE_EDGE,8,0,-1,32,1,300,200,300));dispose(&f,true);return 0;
}
static int evolving(void)
{
    Fixture f;CHECK("setup",setup(&f,1011,0,0,0)==0);f.member_count=2;f.members[0].placed=f.members[1].placed=false;WoodStopFace out[8];size_t n=99;
    CHECK("contact-empty-is-success",collect(&f,false,NULL,out,8,&n)&&n==0&&f.facts_calls==1&&f.unplaced_calls==0&&f.box_calls[0]+f.box_calls[1]==0);
    WoodContactSourceKey key;GeoPlacementSourceKey pk;GeoSourceRef first=contact_ref(WOOD_CONTACT_SOURCE_COLLECTION,1,0,&key);
    CHECK("contact-empty-list-retains-dependencies",edge(f.graph,first,geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_REGIONS,7,&pk))&&
        edge(f.graph,first,geo_placement_source_ref(PLACEMENT_TOKEN,GEO_PLACEMENT_SOURCE_FRAME,7,&pk)));
    f.members[0].placed=true;CHECK("contact-evolving-second-query",collect(&f,false,NULL,out,8,&n));
    CHECK("contact-evolving-placed-subset-is-fresh",n==2&&out[0].timber_id==41&&f.facts_calls==2&&f.box_calls[0]==1&&f.box_calls[1]==0);
    f.members[1].placed=true;CHECK("contact-evolving-third-query",collect(&f,false,NULL,out,8,&n)&&n==4&&f.facts_calls==3&&f.box_calls[1]==1);
    WoodMember other_candidate=f.members[0];CHECK("contact-pointer-exclude-not-id",collect(&f,false,&other_candidate,out,8,&n)&&n==4);
    CHECK("contact-exact-original-pointer-excluded",collect(&f,false,&f.members[0],out,8,&n)&&n==2&&out[0].timber_id==42);
    GeoSourceValue value;CHECK("contact-old-empty-query-remains-empty",geo_eval_source(f.graph,first,GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&u64(value.as.definition.content)==0&&f.facts_calls==5);
    f.member_placement[1]=8;CHECK("contact-other-placement-is-ignored",collect(&f,false,&f.members[0],out,8,&n)&&n==0&&f.box_calls[1]==1);
    CHECK("contact-sealed-existing-query",geo_eval_seal(f.graph));n=91;CHECK("contact-sealed-new-query-refused",!collect(&f,false,NULL,out,8,&n)&&n==91);
    CHECK("contact-sealed-old-empty-readable",geo_eval_source(f.graph,first,GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&u64(value.as.definition.content)==0);
    dispose(&f,false);return 0;
}
static int capacities(void)
{
    Fixture f;CHECK("setup",setup(&f,1012,0,0,1)==0);f.member_count=2;f.boxes[0]=member_box(0,20,10,30);f.boxes[1]=member_box(40,40,50,50);
    WoodStopFace out[10],saved;memset(out,0x5a,sizeof out);memcpy(&saved,out+1,sizeof saved);size_t n=93;
    CHECK("contact-zero-capacity-still-evaluates",collect(&f,false,NULL,NULL,0,&n)&&n==0&&f.facts_calls==1&&f.box_calls[0]==1&&f.box_calls[1]==1);
    CHECK("contact-cap-one-preserves-tail",collect(&f,false,NULL,out,1,&n)&&n==1&&!memcmp(out+1,&saved,sizeof saved));
    CHECK("contact-capacity-before-dedup",collect(&f,false,NULL,out,4,&n)&&n==3&&out[2].timber_id==41&&out[2].fixed==10);
    CHECK("contact-larger-cap-admits-later-member",collect(&f,false,NULL,out,6,&n)&&n==5&&out[2].timber_id==42&&out[4].timber_id==41);
    dispose(&f,true);CHECK("pair-setup",setup(&f,1013,0,0,0)==0);f.member_count=2;memset(out,0x5a,sizeof out);memcpy(&saved,out+2,sizeof saved);
    CHECK("contact-member-pairs-truncate-before-order",collect(&f,false,NULL,out,3,&n)&&n==2&&out[0].timber_id==41&&out[1].timber_id==41&&!memcmp(out+2,&saved,sizeof saved));
    dispose(&f,false);return 0;
}
static bool rejecting_end_resolver(void *user,bool along,const WoodMember *self,WoodStopFace *out,size_t cap,size_t *count)
{
    (void)along;(void)self;(void)out;(void)cap;(void)count;
    ++*(unsigned *)user;return false;
}
static int resolver_failures(void)
{
    WoodContactWorld world={.placement_id=7};WoodMember self={0};
    self.id=17;self.role=WOOD_MEMBER_ROLE_PRIMARY;self.cut_priority=2;
    unsigned calls=0;char error[128];memset(error,0x5a,sizeof error);
    CHECK("contact-resolver-failure-has-complete-error",!wood_contact_end_faces_with_sources(&world,&self,false,0,100,20,30,
        rejecting_end_resolver,&calls,error,sizeof error)&&calls==1&&!strcmp(error,"I8: ordered contact source evaluation failed"));
    struct {char error[8];char guard;} short_error;memset(&short_error,0x5a,sizeof short_error);
    CHECK("contact-resolver-failure-error-truncates-safely",!wood_contact_end_faces_with_sources(&world,&self,false,0,100,20,30,
        rejecting_end_resolver,&calls,short_error.error,sizeof short_error.error)&&calls==2&&
        !memcmp(short_error.error,"I8: ord\0",sizeof short_error.error)&&short_error.guard==0x5a);
    CHECK("contact-resolver-failure-allows-null-error",!wood_contact_end_faces_with_sources(&world,&self,false,0,100,20,30,
        rejecting_end_resolver,&calls,NULL,128)&&calls==3);
    char untouched='Z';CHECK("contact-resolver-failure-zero-capacity-error-is-untouched",!wood_contact_end_faces_with_sources(&world,&self,false,0,100,20,30,
        rejecting_end_resolver,&calls,&untouched,0)&&calls==4&&untouched=='Z');
    WoodBoundaryRegion elbow={0};elbow.id=7;elbow.outline.count=6;
    GeoPoint2 points[6]={{0,0},{100,0},{100,50},{50,50},{50,100},{0,100}};
    memcpy(elbow.outline.v,points,sizeof points);for(size_t i=0;i<6;++i)elbow.outline.fixity[i]=WOOD_STOP_FIXED;
    world.role_boundary=&elbow;world.regions[0]=&elbow;world.region_count=1;calls=0;memset(error,0,sizeof error);
    CHECK("contact-extension-error-precedes-source-resolver",!wood_contact_end_faces_with_sources(&world,&self,false,0,100,40,50,
        rejecting_end_resolver,&calls,error,sizeof error)&&calls==0&&strstr(error,"V_EXTENSION"));
    return 0;
}
static int failures(void)
{
    for(unsigned mode=0;mode<3;++mode){Fixture f;CHECK("setup",setup(&f,1014+mode,0,0,0)==0);f.member_count=0;
        f.fail=mode==0;f.invalid=mode==1;f.cycle=mode==2;WoodStopFace out[2],saved[2];memset(out,0x5a,sizeof out);memcpy(saved,out,sizeof out);size_t n=77;
        CHECK("contact-failed-facts-refused",!collect(&f,false,NULL,out,2,&n));
        CHECK("contact-failure-keeps-output-and-count",n==77&&!memcmp(out,saved,sizeof out));
        if(mode==2)CHECK("contact-cycle-is-an-actual-graph-cycle",f.cycle_status==GEO_SOURCE_CYCLE);
        f.fail=f.invalid=f.cycle=false;CHECK("contact-next-query-can-recover",collect(&f,false,NULL,out,2,&n)&&n==0&&f.facts_calls==2);
        dispose(&f,mode%2==0);
    }
    Fixture f;CHECK("bad-argument-setup",setup(&f,1017,0,0,0)==0);size_t n=88;WoodContactSourceRequest request={7,false,NULL};
    CHECK("contact-invalid-output-refused-before-query",!wood_contact_sources_collect(f.contacts,&request,NULL,1,&n)&&n==88&&f.facts_calls==0);
    WoodContactSourceKey key;GeoSourceRef ref=contact_ref(WOOD_CONTACT_SOURCE_COLLECTION,UINT64_MAX,0,&key);WoodContactSourceKind kind=WOOD_CONTACT_SOURCE_FEATURE;uint64_t query=8,index=9;
    CHECK("contact-full-u64-key-decode",wood_contact_source_decode(&ref,&kind,&query,&index)&&kind==WOOD_CONTACT_SOURCE_COLLECTION&&query==UINT64_MAX&&index==0);
    key.bytes[16]=1;query=8;index=9;kind=WOOD_CONTACT_SOURCE_FEATURE;
    CHECK("contact-invalid-key-preserves-decode-output",!wood_contact_source_decode(&ref,&kind,&query,&index)&&query==8&&index==9&&kind==WOOD_CONTACT_SOURCE_FEATURE);
    dispose(&f,true);return resolver_failures();
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;const char *name=argv[1];int result;
    if(!strcmp(name,"graph"))result=graph_case();else if(!strcmp(name,"feature-values"))result=feature_consumption();
    else if(!strcmp(name,"upstream"))result=upstream_changes();else if(!strcmp(name,"ordering"))result=ordering();
    else if(!strcmp(name,"components"))result=components();else if(!strcmp(name,"evolving"))result=evolving();
    else if(!strcmp(name,"capacity"))result=capacities();else if(!strcmp(name,"failures"))result=failures();
    else return 2;if(!result)printf("PASS %s\n",name);return result;
}
