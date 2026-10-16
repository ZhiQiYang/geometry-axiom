/* Independent H client: neutral snapshot sections stand in for K, W and H.
 * Only the two core ranges are bound to K; H must guard the whole snapshot. */
#include "app_candidate.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"line %d: %s\n",__LINE__,#x);return 1;}}while(0)

typedef struct {int64_t input,result;} Core;
typedef struct {int64_t bias;unsigned version;char label[16];} Template;
typedef struct {uint64_t identity,next_id,history;unsigned view;} Host;
typedef struct {
    unsigned char leading[13];Core first;Template policy;Core second;
    Host host;unsigned char trailing[17];
} Snapshot;
typedef struct Probe Probe;
typedef struct {Snapshot *after;Probe *probe;GeoEvalContext *sources;} EvalState;
struct Probe {
    AppCandidate *candidate;Snapshot *live,*before,*after;
    GeoEvalContext *sources;uint64_t id,revision;
    unsigned evaluations,provider_calls,publications,disposals,errors;
    bool fail,preserve_view;
};
static const char STAMP[]="host-test-provider-set/1:complete";
static void initialize(Snapshot *value)
{
    memset(value,0,sizeof *value);memset(value->leading,0x31,sizeof value->leading);
    value->first.input=7;value->second.input=11;value->policy.bias=3;
    value->policy.version=4;strcpy(value->policy.label,"original");
    value->host.identity=41;value->host.next_id=80;value->host.history=6;value->host.view=2;
    memset(value->trailing,0x6a,sizeof value->trailing);
}
static void dispose_state(void *opaque)
{
    EvalState *state=opaque;Probe *probe=state->probe;
    /* Disposal must happen while both candidate and its borrowed resolver live. */
    if(app_candidate_evaluation_state(probe->candidate)!=state||
       (state->sources&&geo_eval_candidate_id(state->sources)!=probe->id))++probe->errors;
    ++probe->disposals;free(state);
}
static bool describe(void *opaque,const GeoSourceRef *source,GeoSourceDescriptor *out)
{
    (void)opaque;unsigned key=0;
    if(source->key_size!=sizeof key)return false;
    memcpy(&key,source->key,sizeof key);if(key!=1)return false;
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_QUANTITY;out->unit=GEO_UNIT_LENGTH;return true;
}
static bool provider_evaluate(void *opaque,GeoEvalContext *sources,const GeoSourceRef *source,GeoSourceValue *out)
{
    (void)source;EvalState *state=opaque;Probe *probe=state->probe;
    if(state->after!=probe->after||state->after==probe->live||sources!=state->sources)return false;
    ++probe->provider_calls;out->kind=GEO_SOURCE_QUANTITY;
    out->as.quantity=(GeoQuantity){state->after->first.input*2+state->after->policy.bias,1,GEO_UNIT_LENGTH};
    return true;
}
static bool evaluate(void *after,GeoEvalContext *sources,void *opaque)
{
    Probe *probe=opaque;Snapshot *copy=after;++probe->evaluations;
    if(after!=probe->after||after==probe->live||
       geo_candidate_state(app_candidate_core(probe->candidate))!=GEO_CANDIDATE_EVALUATING||
       geo_candidate_sources(app_candidate_core(probe->candidate))!=sources||
       geo_eval_candidate_id(sources)!=probe->id||geo_eval_base_revision(sources)!=probe->revision||
       geo_eval_provider_count(sources)||geo_eval_node_count(sources))return false;
    EvalState *state=calloc(1,sizeof *state);if(!state)return false;
    state->after=copy;state->probe=probe;state->sources=sources;probe->sources=sources;
    app_candidate_set_evaluation_state(probe->candidate,state,dispose_state);
    GeoSourceProvider provider={61,"host-test:neutral","host-test-implementation/1",state,describe,provider_evaluate};
    if(!geo_eval_register(sources,&provider))return false;
    unsigned key=1;GeoSourceRef source={61,&key,sizeof key};GeoSourceValue result;
    if(geo_eval_source(sources,source,GEO_DEPENDENCY_VALUE_REQUIRED,&result)!=GEO_SOURCE_OK)return false;
    copy->first.result=result.as.quantity.num;copy->second.result=copy->second.input+copy->first.result;
    ++copy->policy.version;strcpy(copy->policy.label,"evaluated");
    ++copy->host.next_id;++copy->host.history;copy->trailing[16]^=1;
    return !probe->fail;
}
static bool equal_snapshot(const void *live,const void *before,void *opaque)
{
    Probe *probe=opaque;Snapshot left,right;
    memcpy(&left,live,sizeof left);memcpy(&right,before,sizeof right);
    if(probe->preserve_view)left.host.view=right.host.view;
    return memcmp(&left,&right,sizeof left)==0;
}
static void publish_snapshot(void *live,const void *after,void *opaque)
{
    Probe *probe=opaque;unsigned view=((Snapshot*)live)->host.view;
    if(live!=probe->live||after!=probe->after||
       geo_candidate_state(app_candidate_core(probe->candidate))!=GEO_CANDIDATE_PUBLISHED||
       geo_candidate_sources(app_candidate_core(probe->candidate))!=probe->sources||
       !geo_eval_is_sealed(probe->sources))++probe->errors;
    ++probe->publications;memcpy(live,after,sizeof(Snapshot));
    if(probe->preserve_view)((Snapshot*)live)->host.view=view;
}
static AppCandidate *make(Probe *probe,Snapshot *live,Snapshot *before,Snapshot *after,uint64_t id)
{
    memset(probe,0,sizeof *probe);probe->live=live;probe->before=before;probe->after=after;probe->id=id;probe->revision=29;
    probe->candidate=app_candidate_create(before,after,live,sizeof *live,id,probe->revision,STAMP);
    if(!probe->candidate)return NULL;
    if(app_candidate_bind_core(probe->candidate,"first",offsetof(Snapshot,first),sizeof live->first)!=GEO_CANDIDATE_OK||
       app_candidate_bind_core(probe->candidate,"second",offsetof(Snapshot,second),sizeof live->second)!=GEO_CANDIDATE_OK){
        app_candidate_destroy(probe->candidate);return NULL;
    }
    return probe->candidate;
}
static GeoCandidateStatus check(Probe *probe)
{return app_candidate_check(probe->candidate,probe->live,probe->revision,STAMP,equal_snapshot,probe);}
static GeoCandidateStatus publish(Probe *probe)
{return app_candidate_publish(probe->candidate,probe->live,probe->revision,STAMP,equal_snapshot,publish_snapshot,probe);}
static int ownership(void)
{
    Snapshot live,before,after,other,other_before,other_after;Probe p,q;initialize(&live);initialize(&other);
    other.first.input=90;other.policy.bias=8;Snapshot original=live,other_original=other;
    memset(&before,0xa5,sizeof before);memset(&after,0x5a,sizeof after);
    CHECK(make(&p,&live,&before,&after,UINT64_MAX)&&make(&q,&other,&other_before,&other_after,2));
    CHECK(!memcmp(&before,&original,sizeof before)&&!memcmp(&after,&original,sizeof after));
    CHECK(app_candidate_before(p.candidate)==&before&&app_candidate_after(p.candidate)==&after);
    CHECK(geo_candidate_id(app_candidate_core(p.candidate))==UINT64_MAX);
    after.first.input=13;after.policy.bias=5;
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_OK);
    CHECK(app_candidate_evaluate(q.candidate,evaluate,&q)==GEO_CANDIDATE_OK);
    CHECK(after.first.result==31&&after.second.result==42&&other_after.first.result==188);
    CHECK(after.policy.version==5&&!strcmp(after.policy.label,"evaluated"));
    CHECK(after.host.identity==41&&after.host.next_id==81&&after.host.history==7&&after.trailing[16]==0x6b);
    CHECK(!memcmp(&live,&original,sizeof live)&&!memcmp(&before,&original,sizeof before));
    CHECK(!memcmp(&other,&other_original,sizeof other)&&p.sources!=q.sources);
    CHECK(geo_eval_provider_at(p.sources,0)->candidate_state==app_candidate_evaluation_state(p.candidate));
    CHECK(geo_eval_provider_at(q.sources,0)->candidate_state==app_candidate_evaluation_state(q.candidate));
    app_candidate_destroy(p.candidate);app_candidate_destroy(q.candidate);
    CHECK(p.disposals==1&&q.disposals==1&&!p.errors&&!q.errors);return 0;
}
static int bindings(void)
{
    Snapshot live,before,after;Probe p;initialize(&live);
    CHECK(app_candidate_create(&live,&after,&live,sizeof live,1,2,STAMP)==NULL);
    CHECK(app_candidate_create(&before,&before,&live,sizeof live,1,2,STAMP)==NULL);
    CHECK(app_candidate_create(&before,&after,&live,0,1,2,STAMP)==NULL);
    CHECK(app_candidate_create(NULL,&after,&live,sizeof live,1,2,STAMP)==NULL);
    CHECK(app_candidate_create(&before,&after,&live,sizeof live,1,2,"")==NULL);
    CHECK(app_candidate_create((void*)(uintptr_t)(UINTPTR_MAX-3),&after,&live,sizeof live,1,2,STAMP)==NULL);
    CHECK(make(&p,&live,&before,&after,1));
    CHECK(app_candidate_bind_core(p.candidate,"overflow",SIZE_MAX,1)==GEO_CANDIDATE_INVALID);
    CHECK(app_candidate_bind_core(p.candidate,"overflow",1,SIZE_MAX)==GEO_CANDIDATE_INVALID);
    CHECK(app_candidate_bind_core(p.candidate,"end",sizeof live,1)==GEO_CANDIDATE_INVALID);
    CHECK(app_candidate_bind_core(p.candidate,"zero",0,0)==GEO_CANDIDATE_INVALID);
    CHECK(app_candidate_bind_core(p.candidate,"first",0,1)==GEO_CANDIDATE_DUPLICATE);
    CHECK(app_candidate_bind_core(p.candidate,"overlap",offsetof(Snapshot,first)+1,1)==GEO_CANDIDATE_OVERLAP);
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_OK&&app_candidate_seal(p.candidate)==GEO_CANDIDATE_OK);
    ++after.policy.bias;++after.host.next_id;
    CHECK(geo_candidate_check(app_candidate_core(p.candidate),p.revision,STAMP)==GEO_CANDIDATE_OK);
    CHECK(check(&p)==GEO_CANDIDATE_STATE_CHANGED);
    --after.policy.bias;--after.host.next_id;++after.second.result;
    CHECK(geo_candidate_check(app_candidate_core(p.candidate),p.revision,STAMP)==GEO_CANDIDATE_STATE_CHANGED);
    CHECK(p.publications==0);app_candidate_destroy(p.candidate);CHECK(p.disposals==1&&!p.errors);return 0;
}
static int failed_evaluation(void)
{
    Snapshot live,before,after;Probe p;initialize(&live);Snapshot original=live;
    CHECK(make(&p,&live,&before,&after,1));p.fail=true;
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_EVALUATION_FAILED);
    CHECK(after.first.result==17&&after.host.next_id==81&&p.evaluations==1&&p.provider_calls==1);
    CHECK(app_candidate_seal(p.candidate)!=GEO_CANDIDATE_OK&&publish(&p)!=GEO_CANDIDATE_OK);
    CHECK(!memcmp(&live,&original,sizeof live)&&!memcmp(&before,&original,sizeof before)&&p.publications==0);
    app_candidate_destroy(p.candidate);CHECK(p.disposals==1&&!p.errors);return 0;
}
static int before_evaluation(void)
{
    Snapshot live,before,after;Probe p;initialize(&live);Snapshot original=live;
    CHECK(make(&p,&live,&before,&after,1));++before.host.next_id;
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_STATE_CHANGED);
    CHECK(p.evaluations==0&&p.provider_calls==0&&!memcmp(&after,&original,sizeof after));
    --before.host.next_id;++before.policy.bias;
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_STATE_CHANGED);
    CHECK(!memcmp(&live,&original,sizeof live)&&p.publications==0);
    app_candidate_destroy(p.candidate);CHECK(p.disposals==0&&!p.errors);return 0;
}
static int before_seal(void)
{
    Snapshot live,before,after;Probe p;initialize(&live);Snapshot original=live;
    CHECK(make(&p,&live,&before,&after,1));
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_OK);
    ++before.policy.bias;CHECK(app_candidate_seal(p.candidate)==GEO_CANDIDATE_STATE_CHANGED);
    --before.policy.bias;++before.host.history;CHECK(app_candidate_seal(p.candidate)==GEO_CANDIDATE_STATE_CHANGED);
    CHECK(publish(&p)!=GEO_CANDIDATE_OK&&p.publications==0&&!memcmp(&live,&original,sizeof live));
    app_candidate_destroy(p.candidate);CHECK(p.disposals==1&&!p.errors);return 0;
}
static int after_before_seal(void)
{
    Snapshot live,before,after;Probe p;initialize(&live);Snapshot original=live;
    CHECK(make(&p,&live,&before,&after,1));
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_OK);
    ++after.policy.bias;CHECK(app_candidate_seal(p.candidate)==GEO_CANDIDATE_STATE_CHANGED);
    --after.policy.bias;++after.host.history;CHECK(app_candidate_seal(p.candidate)==GEO_CANDIDATE_STATE_CHANGED);
    CHECK(publish(&p)!=GEO_CANDIDATE_OK&&p.publications==0&&!memcmp(&live,&original,sizeof live));
    app_candidate_destroy(p.candidate);CHECK(p.disposals==1&&!p.errors);return 0;
}
static int sealed_before(void)
{
    Snapshot live,before,after;Probe p;initialize(&live);Snapshot original=live;
    CHECK(make(&p,&live,&before,&after,1));
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_OK&&app_candidate_seal(p.candidate)==GEO_CANDIDATE_OK);
    ++before.policy.bias;CHECK(check(&p)==GEO_CANDIDATE_STATE_CHANGED&&publish(&p)==GEO_CANDIDATE_STATE_CHANGED);
    --before.policy.bias;++before.host.history;CHECK(check(&p)==GEO_CANDIDATE_STATE_CHANGED&&publish(&p)==GEO_CANDIDATE_STATE_CHANGED);
    CHECK(p.publications==0&&!memcmp(&live,&original,sizeof live));
    app_candidate_destroy(p.candidate);CHECK(p.disposals==1&&!p.errors);return 0;
}
static int sealed_after(void)
{
    Snapshot live,before,after;Probe p;initialize(&live);Snapshot original=live;
    CHECK(make(&p,&live,&before,&after,1));
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_OK&&app_candidate_seal(p.candidate)==GEO_CANDIDATE_OK);
    CHECK(check(&p)==GEO_CANDIDATE_OK);
    ++after.policy.bias;CHECK(check(&p)==GEO_CANDIDATE_STATE_CHANGED&&publish(&p)==GEO_CANDIDATE_STATE_CHANGED);
    --after.policy.bias;++after.host.next_id;CHECK(check(&p)==GEO_CANDIDATE_STATE_CHANGED&&publish(&p)==GEO_CANDIDATE_STATE_CHANGED);
    --after.host.next_id;after.trailing[0]^=1;CHECK(check(&p)==GEO_CANDIDATE_STATE_CHANGED);
    CHECK(p.publications==0&&!memcmp(&live,&original,sizeof live));
    app_candidate_destroy(p.candidate);CHECK(p.disposals==1&&!p.errors);return 0;
}
static int live_policy(void)
{
    Snapshot live,before,after;Probe p;initialize(&live);
    CHECK(make(&p,&live,&before,&after,1));
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_OK&&app_candidate_seal(p.candidate)==GEO_CANDIDATE_OK);
    ++live.host.history;Snapshot changed=live;
    CHECK(check(&p)==GEO_CANDIDATE_STATE_CHANGED&&publish(&p)==GEO_CANDIDATE_STATE_CHANGED);
    CHECK(!memcmp(&live,&changed,sizeof live)&&p.publications==0);
    --live.host.history;live.host.view=99;
    CHECK(check(&p)==GEO_CANDIDATE_STATE_CHANGED);p.preserve_view=true;
    CHECK(check(&p)==GEO_CANDIDATE_OK&&publish(&p)==GEO_CANDIDATE_OK);
    CHECK(live.host.view==99&&live.host.history==7&&live.host.next_id==81&&p.publications==1);
    Snapshot expected=after;expected.host.view=99;CHECK(!memcmp(&live,&expected,sizeof live));
    app_candidate_destroy(p.candidate);CHECK(p.disposals==1&&!p.errors);return 0;
}
static int publication(void)
{
    Snapshot live,before,after;Probe p;initialize(&live);Snapshot original=live;
    CHECK(make(&p,&live,&before,&after,1));
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_OK);
    GeoEvalContext *sources=p.sources;void *state=app_candidate_evaluation_state(p.candidate);Snapshot preview=after;
    CHECK(p.evaluations==1&&p.provider_calls==1&&!memcmp(&live,&original,sizeof live));
    CHECK(app_candidate_seal(p.candidate)==GEO_CANDIDATE_OK&&check(&p)==GEO_CANDIDATE_OK&&publish(&p)==GEO_CANDIDATE_OK);
    CHECK(p.evaluations==1&&p.provider_calls==1&&p.publications==1&&p.disposals==0&&!p.errors);
    CHECK(!memcmp(&live,&preview,sizeof live)&&!memcmp(&before,&original,sizeof before));
    CHECK(geo_candidate_sources(app_candidate_core(p.candidate))==sources&&app_candidate_evaluation_state(p.candidate)==state);
    CHECK(publish(&p)==GEO_CANDIDATE_STATE&&p.publications==1);
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_STATE&&p.evaluations==1);
    app_candidate_destroy(p.candidate);CHECK(p.disposals==1&&!p.errors);return 0;
}
static int revision_provider(void)
{
    Snapshot live,before,after;Probe p;initialize(&live);Snapshot original=live;
    CHECK(make(&p,&live,&before,&after,1));
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_OK&&app_candidate_seal(p.candidate)==GEO_CANDIDATE_OK);
    CHECK(app_candidate_publish(p.candidate,&live,p.revision+1,STAMP,equal_snapshot,publish_snapshot,&p)==GEO_CANDIDATE_REVISION_CHANGED);
    CHECK(app_candidate_publish(p.candidate,&live,p.revision,"changed",equal_snapshot,publish_snapshot,&p)==GEO_CANDIDATE_PROVIDER_CHANGED);
    GeoSourceProvider *provider=(GeoSourceProvider*)geo_eval_provider_at(p.sources,0);CHECK(provider);
    provider->token=62;CHECK(check(&p)==GEO_CANDIDATE_PROVIDER_CHANGED&&publish(&p)==GEO_CANDIDATE_PROVIDER_CHANGED);
    provider->token=61;CHECK(check(&p)==GEO_CANDIDATE_OK);
    CHECK(p.publications==0&&p.evaluations==1&&!memcmp(&live,&original,sizeof live));
    app_candidate_destroy(p.candidate);CHECK(p.disposals==1&&!p.errors);return 0;
}
static int state_lifetime(void)
{
    Snapshot live,before,after;Probe p;initialize(&live);Snapshot original=live;
    CHECK(make(&p,&live,&before,&after,1));
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_OK&&p.disposals==0);
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_OK&&p.disposals==1);
    CHECK(p.evaluations==2&&p.provider_calls==2&&!p.errors);p.fail=true;
    CHECK(app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_EVALUATION_FAILED&&p.disposals==2);
    app_candidate_discard(p.candidate);CHECK(p.disposals==3&&!app_candidate_evaluation_state(p.candidate));
    CHECK(geo_candidate_state(app_candidate_core(p.candidate))==GEO_CANDIDATE_DISCARDED);
    CHECK(publish(&p)==GEO_CANDIDATE_STATE&&app_candidate_evaluate(p.candidate,evaluate,&p)==GEO_CANDIDATE_STATE);
    app_candidate_discard(p.candidate);app_candidate_destroy(p.candidate);
    CHECK(p.disposals==3&&!p.errors&&!memcmp(&live,&original,sizeof live));
    CHECK(make(&p,&live,&before,&after,2));
    EvalState *a=calloc(1,sizeof *a),*b=calloc(1,sizeof *b);CHECK(a&&b);a->probe=b->probe=&p;
    app_candidate_set_evaluation_state(p.candidate,a,dispose_state);
    app_candidate_set_evaluation_state(p.candidate,a,dispose_state);CHECK(p.disposals==0);
    app_candidate_set_evaluation_state(p.candidate,b,dispose_state);CHECK(p.disposals==1);
    CHECK(app_candidate_evaluation_state(p.candidate)==b);app_candidate_destroy(p.candidate);
    CHECK(p.disposals==2&&!p.errors);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"ownership"))return ownership();
    if(!strcmp(argv[1],"bindings"))return bindings();
    if(!strcmp(argv[1],"failed-evaluation"))return failed_evaluation();
    if(!strcmp(argv[1],"before-evaluation"))return before_evaluation();
    if(!strcmp(argv[1],"before-seal"))return before_seal();
    if(!strcmp(argv[1],"after-before-seal"))return after_before_seal();
    if(!strcmp(argv[1],"sealed-before"))return sealed_before();
    if(!strcmp(argv[1],"sealed-after"))return sealed_after();
    if(!strcmp(argv[1],"live-policy"))return live_policy();
    if(!strcmp(argv[1],"publication"))return publication();
    if(!strcmp(argv[1],"revision-provider"))return revision_provider();
    if(!strcmp(argv[1],"state-lifetime"))return state_lifetime();
    return 2;
}
