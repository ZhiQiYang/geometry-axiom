/* PRIVATE, UNCOMPILED DRAFT. Real public K graph and real W collector.
 * Hooks replace only test-copy call sites; the product has no test branches. */
#include "contact_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(tag,x) do{if(!(x)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
enum { CONTACT_TOKEN=16, BOX_TOKEN=4 };
bool contact_test_disable_memo;
static bool transform_features;
static unsigned collector_calls,allocation_calls[4],fail_remaining;
static const char *fail_role;
static int role_index(const char *role)
{return !strcmp(role,"facts")?0:!strcmp(role,"faces")?1:!strcmp(role,"collection")?2:3;}
static bool reject_allocation(const char *role)
{
    ++allocation_calls[role_index(role)];
    if(fail_role&&!strcmp(role,fail_role)&&fail_remaining){--fail_remaining;return true;}
    return false;
}
void *contact_test_malloc(const char *role,size_t size)
{return reject_allocation(role)?NULL:malloc(size);}
void *contact_test_calloc(const char *role,size_t count,size_t size)
{return reject_allocation(role)?NULL:calloc(count,size);}
size_t contact_test_collect(const WoodContactWorld *world,bool along,const WoodMember *exclude,WoodStopFace *out,size_t cap)
{++collector_calls;return wood_contact_collect_stops(world,along,exclude,out,cap);}
void contact_test_transform_feature(GeoSegment3 *segment)
{
    if(transform_features){segment->start.x+=1000;segment->end.x+=1000;
        segment->start.y+=2000;segment->end.y+=2000;}
}
typedef struct {
    GeoEvalContext *graph;
    WoodContactSources *contacts;
    WoodContactSourceFacts *facts;
    WoodMember members[2];
    unsigned facts_calls,box_calls;
    bool fail,invalid;
} Fixture;
static bool box_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    (void)user;if(ref->key_size!=1||!ref->key||*(const unsigned char *)ref->key!=7)return false;
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_BOX;out->unit=GEO_UNIT_LENGTH;return true;
}
static bool box_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    Fixture *f=user;if(graph!=f->graph||ref->key_size!=1)return false;++f->box_calls;
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_BOX;
    out->as.box=(GeoBox3){.frame={{20,20,0},{1,0,0},{0,1,0},{0,0,1}},.extent={10,10,10}};return true;
}
static bool facts_callback(void *user,GeoEvalContext *graph,const WoodContactSourceRequest *request,WoodContactSourceFacts *out)
{
    Fixture *f=user;(void)request;if(graph!=f->graph)return false;++f->facts_calls;
    const unsigned char key=7;GeoSourceValue value;
    if(geo_eval_source(graph,(GeoSourceRef){BOX_TOKEN,&key,1},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||
       value.kind!=GEO_SOURCE_BOX||f->fail)return false;
    /* A canonical callback DTO deliberately stays identical when the member
     * pointer's pointee id/placed changes. This isolates the alias safeguard. */
    memcpy(out,f->facts,sizeof *out);
    if(f->invalid)out->member_count=WOOD_CONTACT_MEMBER_CAPACITY+1;
    return true;
}
static int setup(Fixture *f)
{
    memset(f,0,sizeof *f);f->graph=geo_eval_create(300,73);f->facts=calloc(1,sizeof *f->facts);
    CHECK("result-memo-fixture",f->graph&&f->facts);
    f->facts->region_count=1;WoodBoundaryRegion *r=&f->facts->regions[0];r->id=7;
    r->outline.count=4;r->outline.v[0]=(GeoPoint2){0,0};r->outline.v[1]=(GeoPoint2){100,0};
    r->outline.v[2]=(GeoPoint2){100,100};r->outline.v[3]=(GeoPoint2){0,100};
    for(size_t i=0;i<4;++i)r->outline.fixity[i]=WOOD_EDGE_FIXED;
    f->facts->member_count=2;
    for(size_t i=0;i<2;++i){f->members[i].id=41+(uint32_t)i;f->members[i].placed=true;
        f->members[i].role=WOOD_MEMBER_ROLE_PRIMARY;
        WoodContactMemberFact *m=&f->facts->members[i];m->member=&f->members[i];m->placement_id=7;
        m->order=i+1;m->footprint_valid=true;GeoCoord p=20+(GeoCoord)i*20;
        m->footprint=(GeoRect2){p,p,p+10,p+10};}
    GeoSourceProvider box={BOX_TOKEN,"test.result-memo.box","test-box/1",f,box_describe,box_evaluate};
    CHECK("result-memo-provider",geo_eval_register(f->graph,&box));
    f->contacts=wood_contact_sources_create(f->graph,CONTACT_TOKEN,facts_callback,f);
    CHECK("result-memo-handle",f->contacts&&f->facts_calls==0);return 0;
}
static void dispose(Fixture *f,bool graph_first)
{
    if(graph_first){geo_eval_destroy(f->graph);wood_contact_sources_destroy(f->contacts);}
    else{wood_contact_sources_destroy(f->contacts);geo_eval_destroy(f->graph);}
    free(f->facts);
}
static bool collect(Fixture *f,WoodContactSourceRequest *request,WoodStopFace *out,size_t cap,size_t *count)
{return wood_contact_sources_collect(f->contacts,request,out,cap,count);}
static bool collection(Fixture *f,uint64_t id,GeoSourceValue *value)
{
    WoodContactSourceKey key;return geo_eval_source(f->graph,
        wood_contact_source_ref(CONTACT_TOKEN,WOOD_CONTACT_SOURCE_COLLECTION,id,0,&key),
        GEO_DEPENDENCY_VALUE_REQUIRED,value)==GEO_SOURCE_OK;
}
static bool equal_source(GeoSourceRef a,GeoSourceRef b)
{return a.provider==b.provider&&a.key_size==b.key_size&&(!a.key_size||!memcmp(a.key,b.key,a.key_size));}
static bool equal_value(const GeoSourceValue *a,const GeoSourceValue *b)
{
    if(!a||!b)return a==b;if(a->kind!=b->kind)return false;
    if(a->kind==GEO_SOURCE_DEFINITION)return !strcmp(a->as.definition.schema,b->as.definition.schema)&&
        a->as.definition.content_size==b->as.definition.content_size&&
        !memcmp(a->as.definition.content,b->as.definition.content,a->as.definition.content_size);
    if(a->kind==GEO_SOURCE_FEATURE)return a->as.feature.key_size==b->as.feature.key_size&&
        !memcmp(a->as.feature.key,b->as.feature.key,a->as.feature.key_size)&&
        !memcmp(&a->as.feature.segment,&b->as.feature.segment,sizeof a->as.feature.segment);
    if(a->kind==GEO_SOURCE_BOX)return !memcmp(&a->as.box,&b->as.box,sizeof a->as.box);
    return false;
}
static bool equal_graphs(GeoEvalContext *a,GeoEvalContext *b)
{
    if(geo_eval_node_count(a)!=geo_eval_node_count(b)||geo_eval_edge_count(a)!=geo_eval_edge_count(b))return false;
    for(size_t i=0;i<geo_eval_node_count(a);++i){GeoSourceNodeView x,y;
        if(!geo_eval_node_at(a,i,&x)||!geo_eval_node_at(b,i,&y)||!equal_source(x.source,y.source)||
           x.state!=y.state||x.status!=y.status||x.described!=y.described||
           x.descriptor.kind!=y.descriptor.kind||x.descriptor.unit!=y.descriptor.unit||
           x.descriptor.context.has_placement!=y.descriptor.context.has_placement||
           x.descriptor.context.placement!=y.descriptor.context.placement||
           x.descriptor.context.axis!=y.descriptor.context.axis||
           x.descriptor.retry_failure!=y.descriptor.retry_failure||
           x.descriptor.context_from_value!=y.descriptor.context_from_value||!equal_value(x.value,y.value))return false;}
    for(size_t i=0;i<geo_eval_edge_count(a);++i){GeoSourceEdge x,y;
        if(!geo_eval_edge_at(a,i,&x)||!geo_eval_edge_at(b,i,&y)||x.consumer!=y.consumer||x.source!=y.source||x.kind!=y.kind)return false;}
    return true;
}
static int repeat_case(void)
{
    Fixture a,b;CHECK("setup-a",setup(&a)==0);CHECK("setup-b",setup(&b)==0);
    WoodContactSourceRequest request={7,false,NULL};WoodStopFace av[16],bv[16];size_t an=0,bn=0;
    CHECK("result-memo-first",collect(&a,&request,av,16,&an)&&an==6);
    GeoSourceValue first,second;CHECK("result-memo-first-value",collection(&a,1,&first));
    unsigned char saved[8+16*48];size_t size=first.as.definition.content_size;memcpy(saved,first.as.definition.content,size);
    CHECK("result-memo-repeat",collect(&a,&request,av,16,&an)&&an==6);
    CHECK("result-memo-repeat-computes-once",collector_calls==1);
    CHECK("result-memo-callback-runs-each-query",a.facts_calls==2&&a.box_calls==1);
    CHECK("result-memo-second-value",collection(&a,2,&second));
    CHECK("result-memo-new-query-owns-copy",first.as.definition.content!=second.as.definition.content&&
        size==second.as.definition.content_size&&!memcmp(saved,first.as.definition.content,size)&&
        !memcmp(saved,second.as.definition.content,size));
    CHECK("result-memo-hit-keeps-required-allocations",allocation_calls[0]==2&&allocation_calls[1]==2&&allocation_calls[2]==2);
    contact_test_disable_memo=true;
    CHECK("result-memo-reference",collect(&b,&request,bv,16,&bn)&&collect(&b,&request,bv,16,&bn));
    CHECK("result-memo-ordered-graph-identical",equal_graphs(a.graph,b.graph)&&an==bn&&!memcmp(av,bv,an*sizeof *av));
    CHECK("result-memo-reference-still-computes",collector_calls==3&&b.facts_calls==2);
    dispose(&a,true);dispose(&b,false);return 0;
}
static int keys_case(const char *which)
{
    Fixture f;CHECK("setup",setup(&f)==0);WoodContactSourceRequest r={7,false,NULL};
    WoodStopFace out[16],expected[16];size_t n=0,en=0,cap=16;
    CHECK("result-memo-key-prime",collect(&f,&r,out,cap,&n)&&collect(&f,&r,out,cap,&n)&&collector_calls==1);
    if(!strcmp(which,"placement"))r.placement_id=8;
    else if(!strcmp(which,"axis"))r.along_v=true;
    else if(!strcmp(which,"exclude"))r.exclude=&f.members[0];
    else if(!strcmp(which,"cap"))cap=3;
    else if(!strcmp(which,"cap-room"))cap=15;
    else if(!strcmp(which,"member-id"))f.members[0].id=141;
    else if(!strcmp(which,"member-placed"))f.members[0].placed=false;
    else if(!strcmp(which,"footprint"))f.facts->members[0].footprint.min_u+=1;
    else if(!strcmp(which,"footprint-valid"))f.facts->members[0].footprint_valid=false;
    else if(!strcmp(which,"member-order"))f.facts->members[0].order=7;
    else if(!strcmp(which,"member-placement"))f.facts->members[0].placement_id=8;
    else if(!strcmp(which,"member-count"))f.facts->member_count=1;
    else if(!strcmp(which,"region-id"))f.facts->regions[0].id=9;
    else if(!strcmp(which,"region-count"))f.facts->region_count=0;
    else if(!strcmp(which,"region-coordinate"))f.facts->regions[0].outline.v[1].u+=1;
    else if(!strcmp(which,"region-fixity"))f.facts->regions[0].outline.fixity[1]=WOOD_EDGE_FREE;
    else if(!strcmp(which,"facts-unused"))f.facts->members[WOOD_CONTACT_MEMBER_CAPACITY-1].order=91;
    else CHECK("result-memo-known-key",false);
    CHECK("result-memo-key-query",collect(&f,&r,out,cap,&n));
    char marker[96];snprintf(marker,sizeof marker,"result-memo-key-%s-is-fresh",which);
    CHECK(marker,collector_calls==2);
    contact_test_disable_memo=true;CHECK("result-memo-key-reference",collect(&f,&r,expected,cap,&en));
    CHECK("result-memo-key-result-matches-recompute",n==en&&!memcmp(out,expected,n*sizeof *out));
    contact_test_disable_memo=false;CHECK("result-memo-key-new-snapshot-hits",collect(&f,&r,out,cap,&n)&&collector_calls==3);
    dispose(&f,false);return 0;
}
static int failure_case(const char *which)
{
    Fixture f;CHECK("setup",setup(&f)==0);WoodContactSourceRequest r={7,false,NULL};WoodStopFace out[16],saved[16];size_t n=0;
    CHECK("result-memo-failure-prime",collect(&f,&r,out,16,&n));
    memset(out,0x5a,sizeof out);memcpy(saved,out,sizeof saved);n=999;
    if(!strcmp(which,"callback"))f.fail=true;
    else if(!strcmp(which,"invalid"))f.invalid=true;
    else{fail_role=which;fail_remaining=1;}
    CHECK("result-memo-does-not-mask-failure",!collect(&f,&r,out,16,&n)&&n==999&&!memcmp(out,saved,sizeof out));
    bool before_callback=!strcmp(which,"facts")||!strcmp(which,"faces");
    CHECK("result-memo-failure-callback-order",f.facts_calls==(before_callback?1u:2u));
    if(!strcmp(which,"facts"))CHECK("result-memo-facts-failure-still-attempts-faces",allocation_calls[1]==2);
    f.fail=f.invalid=false;fail_role=NULL;fail_remaining=0;
    CHECK("result-memo-failure-recovery",collect(&f,&r,out,16,&n)&&n==6);
    CHECK("result-memo-failure-keeps-valid-prior-hint",collector_calls==1);
    dispose(&f,true);return 0;
}
static int optional_case(void)
{
    Fixture f;CHECK("setup",setup(&f)==0);WoodContactSourceRequest r={7,false,NULL};WoodStopFace out[16];size_t n=0;
    fail_role="memo";fail_remaining=2;
    CHECK("result-memo-optional-allocation-is-not-error",collect(&f,&r,out,16,&n)&&n==6&&collect(&f,&r,out,16,&n)&&n==6);
    CHECK("result-memo-optional-failure-recomputes",collector_calls==2&&f.facts_calls==2&&allocation_calls[3]==2);
    fail_role=NULL;CHECK("result-memo-optional-recovery",collect(&f,&r,out,16,&n)&&collect(&f,&r,out,16,&n));
    CHECK("result-memo-optional-recovery-hits",collector_calls==3&&f.facts_calls==4&&allocation_calls[3]==3);
    dispose(&f,false);return 0;
}
static int feature_case(void)
{
    Fixture f;CHECK("setup",setup(&f)==0);WoodContactSourceRequest r={7,false,NULL};WoodStopFace old[16],out[16];size_t n=0,on=0;
    CHECK("result-memo-feature-prime",collect(&f,&r,old,16,&on));transform_features=true;
    CHECK("result-memo-feature-query",collect(&f,&r,out,16,&n)&&n==on&&collector_calls==1);
    for(size_t i=0;i<n;++i)CHECK("result-memo-feature-result-is-consumed",out[i].fixed==old[i].fixed+1000&&out[i].lo==old[i].lo+2000&&out[i].hi==old[i].hi+2000);
    dispose(&f,true);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;int result;
    if(!strcmp(argv[1],"repeat"))result=repeat_case();
    else if(!strncmp(argv[1],"key-",4))result=keys_case(argv[1]+4);
    else if(!strncmp(argv[1],"failure-",8))result=failure_case(argv[1]+8);
    else if(!strcmp(argv[1],"optional"))result=optional_case();
    else if(!strcmp(argv[1],"feature"))result=feature_case();
    else return 2;
    if(!result)printf("PASS %s\n",argv[1]);return result;
}
