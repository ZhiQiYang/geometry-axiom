#include "candidate.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"line %d: %s\n",__LINE__,#x);return 1;}}while(0)

typedef struct { int64_t input,result; unsigned calls[4]; bool soft; } Pod;
typedef struct {
    GeoCandidate *candidate;
    Pod *copy;
    uint64_t id,revision;
    const char *name,*fingerprint;
    bool fail,reentrant;
} Assembly;
static const char STAMP[]="fixed-provider-set/1:exact";
static unsigned key_id(const GeoSourceRef *source)
{unsigned id=0;if(source->key_size==sizeof id)memcpy(&id,source->key,sizeof id);return id;}
static GeoSourceRef source_ref(unsigned *id){return (GeoSourceRef){19,id,sizeof *id};}
static bool describe(void *opaque,const GeoSourceRef *source,GeoSourceDescriptor *out)
{
    (void)opaque;if(key_id(source)>2)return false;
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_QUANTITY;out->unit=GEO_UNIT_LENGTH;
    return true;
}
static bool provider_evaluate(void *opaque,GeoEvalContext *context,const GeoSourceRef *source,GeoSourceValue *out)
{
    Pod *copy=opaque;unsigned id=key_id(source);
    if(id<1||id>2)return false;
    ++copy->calls[id];if(id==2)return false;
    if(copy->soft){
        unsigned failed=2,definition=3;GeoSourceValue ignored;
        if(geo_eval_source(context,source_ref(&failed),GEO_DEPENDENCY_EVALUATE_BEFORE,&ignored)!=GEO_SOURCE_FAILED)return false;
        if(geo_eval_depend(context,source_ref(&definition),GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)return false;
    }
    out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){copy->input*2,1,GEO_UNIT_LENGTH};return true;
}
static bool evaluate(void *opaque,GeoEvalContext *context)
{
    Assembly *assembly=opaque;
    if(geo_candidate_state(assembly->candidate)!=GEO_CANDIDATE_EVALUATING||
       geo_candidate_sources(assembly->candidate)!=context||geo_eval_candidate_id(context)!=assembly->id||
       geo_eval_base_revision(context)!=assembly->revision||geo_eval_node_count(context)!=0||
       geo_eval_provider_count(context)!=0)return false;
    if(assembly->reentrant){
        if(geo_candidate_evaluate(assembly->candidate,evaluate,assembly)!=GEO_CANDIDATE_STATE||
           geo_candidate_seal(assembly->candidate)!=GEO_CANDIDATE_STATE||
           geo_candidate_mark_published(assembly->candidate,assembly->revision,STAMP)!=GEO_CANDIDATE_STATE||
           geo_candidate_discard(assembly->candidate)!=GEO_CANDIDATE_STATE)return false;
    }
    GeoSourceProvider provider={19,assembly->name,assembly->fingerprint,assembly->copy,describe,provider_evaluate};
    if(!geo_eval_register(context,&provider))return false;
    unsigned id=1;GeoSourceValue value;
    if(geo_eval_source(context,source_ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
    assembly->copy->result=value.as.quantity.num;return !assembly->fail;
}
static GeoCandidate *make(Assembly *assembly,Pod *before,Pod *current,const char *stamp,uint64_t id,uint64_t revision)
{
    GeoCandidate *candidate=geo_candidate_create(id,revision,stamp);
    if(!candidate)return NULL;
    if(geo_candidate_bind_state(candidate,"opaque:pod",before,current,sizeof *current)!=GEO_CANDIDATE_OK){geo_candidate_destroy(candidate);return NULL;}
    *assembly=(Assembly){candidate,current,id,revision,"provider:neutral","implementation:exact/1",false,false};
    return candidate;
}
static int ownership(void)
{
    Pod before_a={0},a={0},before_b={0},b={0};before_a.input=7;a=before_a;before_b.input=90;b=before_b;
    Assembly x,y;char stamp[sizeof STAMP];memcpy(stamp,STAMP,sizeof stamp);
    GeoCandidate *ca=make(&x,&before_a,&a,stamp,UINT64_MAX,UINT64_MAX-1),*cb=make(&y,&before_b,&b,STAMP,2,3);
    CHECK(ca&&cb);memset(stamp,'x',sizeof stamp-1);x.reentrant=true;
    CHECK(geo_candidate_id(ca)==UINT64_MAX&&geo_candidate_base_revision(ca)==UINT64_MAX-1);
    CHECK(geo_candidate_sources(ca)==NULL&&geo_candidate_state(ca)==GEO_CANDIDATE_OPEN);
    CHECK(geo_candidate_evaluate(ca,evaluate,&x)==GEO_CANDIDATE_OK);
    CHECK(geo_candidate_evaluate(cb,evaluate,&y)==GEO_CANDIDATE_OK);
    CHECK(a.result==14&&b.result==180&&before_a.result==0&&before_b.result==0);
    CHECK(a.calls[1]==1&&b.calls[1]==1&&before_a.calls[1]==0&&before_b.calls[1]==0);
    CHECK(geo_candidate_sources(ca)!=geo_candidate_sources(cb));
    CHECK(geo_eval_provider_at(geo_candidate_sources(ca),0)->candidate_state==&a);
    CHECK(geo_eval_provider_at(geo_candidate_sources(cb),0)->candidate_state==&b);
    CHECK(geo_candidate_seal(ca)==GEO_CANDIDATE_OK&&geo_candidate_seal(cb)==GEO_CANDIDATE_OK);
    CHECK(geo_candidate_check(ca,UINT64_MAX-1,STAMP)==GEO_CANDIDATE_OK);
    a.input=9;CHECK(geo_candidate_check(ca,UINT64_MAX-1,STAMP)==GEO_CANDIDATE_STATE_CHANGED);
    CHECK(geo_candidate_check(cb,3,STAMP)==GEO_CANDIDATE_OK);
    geo_candidate_destroy(ca);geo_candidate_destroy(cb);return 0;
}
static int bindings(void)
{
    unsigned char bytes[96]={0};char name[]="owned:name";
    GeoCandidate *candidate=geo_candidate_create(1,2,STAMP);CHECK(candidate);
    CHECK(geo_candidate_create(1,2,NULL)==NULL&&geo_candidate_create(1,2,"")==NULL);
    CHECK(geo_candidate_bind_state(candidate,name,bytes,bytes+16,16)==GEO_CANDIDATE_OK);
    name[0]='X';
    CHECK(geo_candidate_bind_state(candidate,"owned:name",bytes+32,bytes+48,16)==GEO_CANDIDATE_DUPLICATE);
    CHECK(geo_candidate_bind_state(candidate,"second",bytes+32,bytes+48,16)==GEO_CANDIDATE_OK);
    CHECK(geo_candidate_bind_state(candidate,"self",bytes+64,bytes+64,16)==GEO_CANDIDATE_OVERLAP);
    CHECK(geo_candidate_bind_state(candidate,"partial",bytes+64,bytes+65,16)==GEO_CANDIDATE_OVERLAP);
    CHECK(geo_candidate_bind_state(candidate,"alias-before",bytes+1,bytes+64,16)==GEO_CANDIDATE_OVERLAP);
    CHECK(geo_candidate_bind_state(candidate,"alias-current",bytes+64,bytes+20,16)==GEO_CANDIDATE_OVERLAP);
    CHECK(geo_candidate_bind_state(candidate,"cross",bytes+16,bytes+80,16)==GEO_CANDIDATE_OVERLAP);
    CHECK(geo_candidate_bind_state(candidate,"zero",bytes+64,bytes+80,0)==GEO_CANDIDATE_INVALID);
    CHECK(geo_candidate_bind_state(candidate,"null",NULL,bytes+64,16)==GEO_CANDIDATE_INVALID);
    CHECK(geo_candidate_bind_state(candidate,"",bytes+64,bytes+80,16)==GEO_CANDIDATE_INVALID);
    CHECK(geo_candidate_bind_state(candidate,"overflow",(void *)(uintptr_t)(UINTPTR_MAX-3),bytes+64,16)==GEO_CANDIDATE_INVALID);
    CHECK(geo_candidate_bind_state(candidate,"huge",bytes+64,bytes+80,SIZE_MAX)==GEO_CANDIDATE_INVALID);
    CHECK(geo_candidate_discard(candidate)==GEO_CANDIDATE_OK);
    CHECK(geo_candidate_bind_state(candidate,"late",bytes+64,bytes+80,16)==GEO_CANDIDATE_STATE);
    geo_candidate_destroy(candidate);return 0;
}
static int before_seal(void)
{
    Pod before={0},current={0};Assembly assembly;GeoCandidate *candidate=make(&assembly,&before,&current,STAMP,1,2);CHECK(candidate);
    before.input=1;CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_STATE_CHANGED);
    CHECK(current.calls[1]==0&&geo_candidate_state(candidate)==GEO_CANDIDATE_REJECTED);
    before.input=0;CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_OK);
    before.input=1;CHECK(geo_candidate_seal(candidate)==GEO_CANDIDATE_STATE_CHANGED);
    CHECK(geo_candidate_mark_published(candidate,2,STAMP)==GEO_CANDIDATE_STATE);
    before.input=0;current.input=1;
    CHECK(geo_candidate_seal(candidate)==GEO_CANDIDATE_STATE_CHANGED);
    CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_OK);
    CHECK(current.result==2&&geo_candidate_seal(candidate)==GEO_CANDIDATE_OK);
    geo_candidate_destroy(candidate);return 0;
}
static int tampering(void)
{
    Pod before={0},current={0};Assembly assembly;GeoCandidate *candidate=make(&assembly,&before,&current,STAMP,1,2);CHECK(candidate);
    CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_OK&&geo_candidate_seal(candidate)==GEO_CANDIDATE_OK);
    CHECK(geo_candidate_check(candidate,2,STAMP)==GEO_CANDIDATE_OK);
    before.input=1;CHECK(geo_candidate_check(candidate,2,STAMP)==GEO_CANDIDATE_STATE_CHANGED);
    CHECK(geo_candidate_reopen(candidate,2,STAMP)==GEO_CANDIDATE_STATE_CHANGED);
    before.input=0;current.result=1;
    CHECK(geo_candidate_check(candidate,2,STAMP)==GEO_CANDIDATE_STATE_CHANGED);
    CHECK(geo_candidate_mark_published(candidate,2,STAMP)==GEO_CANDIDATE_STATE_CHANGED);
    CHECK(geo_candidate_state(candidate)==GEO_CANDIDATE_SEALED);
    current.result=0;CHECK(geo_candidate_check(candidate,2,STAMP)==GEO_CANDIDATE_OK);
    /* A successful earlier check is not authority to publish later bytes. */
    current.input=1;CHECK(geo_candidate_mark_published(candidate,2,STAMP)==GEO_CANDIDATE_STATE_CHANGED);
    current.input=0;CHECK(geo_candidate_mark_published(candidate,2,STAMP)==GEO_CANDIDATE_OK);
    CHECK(before.result==0&&before.calls[1]==0&&current.calls[1]==1);
    CHECK(geo_candidate_state(candidate)==GEO_CANDIDATE_PUBLISHED);
    CHECK(geo_candidate_mark_published(candidate,2,STAMP)==GEO_CANDIDATE_STATE);
    CHECK(geo_candidate_discard(candidate)==GEO_CANDIDATE_STATE);
    CHECK(geo_candidate_reopen(candidate,2,STAMP)==GEO_CANDIDATE_STATE);
    CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_STATE);
    geo_candidate_destroy(candidate);return 0;
}
static int revision(void)
{
    Pod before={0},current={0};Assembly assembly;GeoCandidate *candidate=make(&assembly,&before,&current,STAMP,1,2);CHECK(candidate);
    CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_OK&&geo_candidate_seal(candidate)==GEO_CANDIDATE_OK);
    CHECK(geo_candidate_check(candidate,3,STAMP)==GEO_CANDIDATE_REVISION_CHANGED);
    CHECK(geo_candidate_reopen(candidate,3,STAMP)==GEO_CANDIDATE_REVISION_CHANGED);
    CHECK(geo_candidate_mark_published(candidate,3,STAMP)==GEO_CANDIDATE_REVISION_CHANGED);
    CHECK(geo_candidate_state(candidate)==GEO_CANDIDATE_SEALED);
    geo_candidate_destroy(candidate);return 0;
}
static int provider_stamp(void)
{
    Pod before={0},current={0};Assembly assembly;char stamp[8193];memset(stamp,'a',sizeof stamp-1);stamp[sizeof stamp-1]='\0';
    GeoCandidate *candidate=make(&assembly,&before,&current,stamp,1,2);CHECK(candidate);
    CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_OK&&geo_candidate_seal(candidate)==GEO_CANDIDATE_OK);
    CHECK(geo_candidate_check(candidate,2,stamp)==GEO_CANDIDATE_OK);
    stamp[8191]='b';CHECK(geo_candidate_check(candidate,2,stamp)==GEO_CANDIDATE_PROVIDER_CHANGED);
    CHECK(geo_candidate_reopen(candidate,2,stamp)==GEO_CANDIDATE_PROVIDER_CHANGED);
    CHECK(geo_candidate_mark_published(candidate,2,stamp)==GEO_CANDIDATE_PROVIDER_CHANGED);
    geo_candidate_destroy(candidate);return 0;
}
static int providers(void)
{
    Pod before={0},current={0};Assembly assembly;char fingerprint[8193],name[8193];
    memset(fingerprint,'f',sizeof fingerprint-1);fingerprint[8192]='\0';memset(name,'n',sizeof name-1);name[8192]='\0';
    GeoCandidate *candidate=make(&assembly,&before,&current,STAMP,1,2);CHECK(candidate);
    assembly.fingerprint=fingerprint;assembly.name=name;
    CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_OK);
    fingerprint[8191]='x';name[8191]='x';
    CHECK(geo_candidate_seal(candidate)==GEO_CANDIDATE_OK);
    GeoSourceProvider *provider=(GeoSourceProvider *)geo_eval_provider_at(geo_candidate_sources(candidate),0);CHECK(provider);
    CHECK(provider->implementation_fingerprint[8191]=='f'&&provider->name_space[8191]=='n');
    CHECK(geo_candidate_check(candidate,2,STAMP)==GEO_CANDIDATE_OK);
    /* Deliberate writes to allocated registry storage model corruption after
     * sealing, while the independently supplied assembly stamp stays equal. */
    ((char *)provider->implementation_fingerprint)[8191]='g';
    CHECK(geo_candidate_check(candidate,2,STAMP)==GEO_CANDIDATE_PROVIDER_CHANGED);
    CHECK(geo_candidate_mark_published(candidate,2,STAMP)==GEO_CANDIDATE_PROVIDER_CHANGED);
    ((char *)provider->implementation_fingerprint)[8191]='f';
    ((char *)provider->name_space)[8191]='m';
    CHECK(geo_candidate_check(candidate,2,STAMP)==GEO_CANDIDATE_PROVIDER_CHANGED);
    ((char *)provider->name_space)[8191]='n';provider->token=20;
    CHECK(geo_candidate_check(candidate,2,STAMP)==GEO_CANDIDATE_PROVIDER_CHANGED);
    provider->token=19;CHECK(geo_candidate_check(candidate,2,STAMP)==GEO_CANDIDATE_OK);
    geo_candidate_destroy(candidate);return 0;
}
static int revalidation(void)
{
    Pod before={0},current={0},extra_before={0},extra_current={0};Assembly assembly;
    GeoCandidate *candidate=make(&assembly,&before,&current,STAMP,11,22);CHECK(candidate);
    current.input=4;CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_OK);
    CHECK(current.result==8&&current.calls[1]==1);
    current.input=5;CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_OK);
    CHECK(current.result==10&&current.calls[1]==2&&geo_eval_node_count(geo_candidate_sources(candidate))==1);
    CHECK(geo_candidate_bind_state(candidate,"late",&extra_before,&extra_current,sizeof extra_before)==GEO_CANDIDATE_STATE);
    CHECK(geo_candidate_seal(candidate)==GEO_CANDIDATE_OK);
    CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_STATE);
    CHECK(geo_candidate_reopen(candidate,22,STAMP)==GEO_CANDIDATE_OK);
    CHECK(geo_candidate_state(candidate)==GEO_CANDIDATE_OPEN&&geo_candidate_sources(candidate)==NULL);
    CHECK(geo_candidate_id(candidate)==11&&geo_candidate_base_revision(candidate)==22);
    CHECK(geo_candidate_bind_state(candidate,"late",&extra_before,&extra_current,sizeof extra_before)==GEO_CANDIDATE_STATE);
    CHECK(geo_candidate_seal(candidate)==GEO_CANDIDATE_STATE&&geo_candidate_mark_published(candidate,22,STAMP)==GEO_CANDIDATE_STATE);
    current.input=6;CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_OK);
    CHECK(current.result==12&&current.calls[1]==3&&geo_eval_node_count(geo_candidate_sources(candidate))==1);
    CHECK(geo_candidate_seal(candidate)==GEO_CANDIDATE_OK&&geo_candidate_mark_published(candidate,22,STAMP)==GEO_CANDIDATE_OK);
    CHECK(before.input==0&&before.result==0&&before.calls[1]==0);
    geo_candidate_destroy(candidate);return 0;
}
static int failure_discard(void)
{
    Pod before={0},current={0};Assembly assembly;GeoCandidate *candidate=make(&assembly,&before,&current,STAMP,1,2);CHECK(candidate);
    CHECK(geo_candidate_seal(candidate)==GEO_CANDIDATE_STATE&&geo_candidate_mark_published(candidate,2,STAMP)==GEO_CANDIDATE_STATE);
    assembly.fail=true;current.input=8;
    CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_EVALUATION_FAILED);
    CHECK(geo_candidate_state(candidate)==GEO_CANDIDATE_REJECTED&&current.result==16&&before.result==0);
    CHECK(geo_candidate_seal(candidate)==GEO_CANDIDATE_STATE&&geo_candidate_mark_published(candidate,2,STAMP)==GEO_CANDIDATE_STATE);
    assembly.fail=false;CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_OK);
    CHECK(current.calls[1]==2&&geo_candidate_seal(candidate)==GEO_CANDIDATE_OK);
    CHECK(geo_candidate_discard(candidate)==GEO_CANDIDATE_OK&&geo_candidate_sources(candidate)==NULL);
    CHECK(geo_candidate_state(candidate)==GEO_CANDIDATE_DISCARDED&&before.calls[1]==0);
    CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_STATE);
    CHECK(geo_candidate_seal(candidate)==GEO_CANDIDATE_STATE&&geo_candidate_mark_published(candidate,2,STAMP)==GEO_CANDIDATE_STATE);
    CHECK(geo_candidate_reopen(candidate,2,STAMP)==GEO_CANDIDATE_STATE&&geo_candidate_discard(candidate)==GEO_CANDIDATE_STATE);
    geo_candidate_destroy(candidate);geo_candidate_destroy(NULL);return 0;
}
static int soft_edges(void)
{
    Pod before={0},current={0};current.soft=true;Assembly assembly;
    GeoCandidate *candidate=make(&assembly,&before,&current,STAMP,1,2);CHECK(candidate);
    CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_OK);
    GeoEvalContext *sources=geo_candidate_sources(candidate);GeoSourceNodeView node;
    CHECK(geo_eval_node_count(sources)==3&&geo_eval_edge_count(sources)==2);
    CHECK(geo_eval_node_at(sources,1,&node)&&node.state==GEO_NODE_FAILED);
    CHECK(geo_eval_node_at(sources,2,&node)&&node.state==GEO_NODE_NEW);
    CHECK(current.calls[1]==1&&current.calls[2]==1&&current.calls[3]==0);
    CHECK(geo_candidate_seal(candidate)==GEO_CANDIDATE_OK&&geo_eval_is_sealed(sources));
    CHECK(geo_candidate_mark_published(candidate,2,STAMP)==GEO_CANDIDATE_OK);
    geo_candidate_destroy(candidate);return 0;
}
static int source_seal(void)
{
    Pod before={0},current={0};Assembly assembly;GeoCandidate *candidate=make(&assembly,&before,&current,STAMP,1,2);CHECK(candidate);
    CHECK(geo_candidate_evaluate(candidate,evaluate,&assembly)==GEO_CANDIDATE_OK&&geo_candidate_seal(candidate)==GEO_CANDIDATE_OK);
    GeoEvalContext *sources=geo_candidate_sources(candidate);GeoSourceValue value;unsigned id=1;
    CHECK(geo_eval_source(sources,source_ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&current.calls[1]==1);
    id=2;CHECK(geo_eval_source(sources,source_ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_INVALID);
    CHECK(geo_eval_depend(sources,source_ref(&id),GEO_DEPENDENCY_DEFINITION_REQUIRED)==GEO_SOURCE_INVALID);
    GeoSourceProvider extra={20,"other","other/1",&current,describe,provider_evaluate};
    CHECK(!geo_eval_register(sources,&extra));
    CHECK(geo_eval_node_count(sources)==1&&geo_eval_edge_count(sources)==0&&geo_eval_provider_count(sources)==1);
    CHECK(geo_candidate_check(candidate,2,STAMP)==GEO_CANDIDATE_OK);
    geo_candidate_destroy(candidate);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"ownership"))return ownership();if(!strcmp(argv[1],"bindings"))return bindings();
    if(!strcmp(argv[1],"before-seal"))return before_seal();if(!strcmp(argv[1],"tampering"))return tampering();
    if(!strcmp(argv[1],"revision"))return revision();if(!strcmp(argv[1],"provider-stamp"))return provider_stamp();
    if(!strcmp(argv[1],"providers"))return providers();if(!strcmp(argv[1],"revalidation"))return revalidation();
    if(!strcmp(argv[1],"failure-discard"))return failure_discard();if(!strcmp(argv[1],"soft-edges"))return soft_edges();
    if(!strcmp(argv[1],"source-seal"))return source_seal();return 2;
}
