#include "source.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"line %d: %s\n",__LINE__,#x);return 1;}}while(0)
typedef struct {
    int calls[300],cycles;
    GeoCoord base;
    GeoEvalContext *context;
} State;
static unsigned key_id(const GeoSourceRef *ref)
{unsigned id=0;if(ref->key_size==sizeof id)memcpy(&id,ref->key,sizeof id);else if(ref->key_size)id=((const unsigned char *)ref->key)[ref->key_size-1];return id;}
static GeoSourceRef ref(unsigned *id){return (GeoSourceRef){1,id,sizeof *id};}
static bool describe(void *opaque,const GeoSourceRef *source,GeoSourceDescriptor *d)
{
    (void)opaque;unsigned id=key_id(source);memset(d,0,sizeof *d);d->unit=GEO_UNIT_LENGTH;d->kind=GEO_SOURCE_QUANTITY;
    if(id==20||id==21||id==24)d->retry_failure=true;
    if(id==21){d->kind=(GeoSourceValueKind)99;return true;}
    if(id==23){d->kind=GEO_SOURCE_AXIS_POSITION;d->context=(GeoSourceContext){true,8,0};}
    if(id==24||id==40){d->kind=GEO_SOURCE_AXIS_POSITION;d->context=(GeoSourceContext){false,0,0};}
    if(id>=50&&id<=54)d->kind=(GeoSourceValueKind)(id-49);
    return true;
}
static bool evaluate(void *opaque,GeoEvalContext *context,const GeoSourceRef *source,GeoSourceValue *out)
{
    State *state=opaque;unsigned id=key_id(source);if(id>=300||context!=state->context)return false;
    ++state->calls[id];out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){state->base+id,1,GEO_UNIT_LENGTH};
    if(id==1||id==2){unsigned other=id==1?2:1;GeoSourceValue value;
        GeoSourceStatus result=geo_eval_source(context,ref(&other),GEO_DEPENDENCY_VALUE_REQUIRED,&value);
        if(result==GEO_SOURCE_CYCLE)++state->cycles;return result==GEO_SOURCE_OK;}
    if(id==10){unsigned failed=11,value_id=12,definition=13;GeoSourceValue value;
        (void)geo_eval_source(context,ref(&failed),GEO_DEPENDENCY_EVALUATE_BEFORE,&value);
        if(geo_eval_depend(context,ref(&definition),GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)return false;
        if(geo_eval_source(context,ref(&value_id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
        out->as.quantity=value.as.quantity;return true;}
    if(id==11||id==19||id==20)return false;
    if(id==21){out->kind=(GeoSourceValueKind)99;return true;}
    if(id==22){out->as.quantity.unit=GEO_UNIT_SCALAR;return true;}
    if(id==23){out->kind=GEO_SOURCE_AXIS_POSITION;out->as.position=(GeoAxisPosition){7,{true,9,0}};return true;}
    if(id==24){out->kind=GEO_SOURCE_AXIS_POSITION;out->as.position=(GeoAxisPosition){7,{false,0,1}};return true;}
    if(id==40){out->kind=GEO_SOURCE_AXIS_POSITION;out->as.position=(GeoAxisPosition){40,{false,0,0}};return true;}
    if(id==50){out->kind=GEO_SOURCE_AXIS_POSITION;out->as.position=(GeoAxisPosition){7,{false,0,0}};return true;}
    if(id==51){out->kind=GEO_SOURCE_FRAME;out->as.frame=(GeoFrame){{1,2,3},{1,0,0},{0,1,0},{0,0,1}};return true;}
    if(id==52){out->kind=GEO_SOURCE_REGION_SET;out->as.regions=(GeoRegionSetView){NULL,0};return true;}
    if(id==53){out->kind=GEO_SOURCE_BOX;out->as.box=(GeoBox3){{{1,2,3},{1,0,0},{0,1,0},{0,0,1}},{2,3,4}};return true;}
    if(id==54){out->kind=GEO_SOURCE_FEATURE;out->as.feature=(GeoFeatureValue){"long exact key",14,{{0,0,0},{1,2,3}}};return true;}
    if(id==100){for(unsigned n=101;n<299;++n){GeoSourceValue value;if(geo_eval_source(context,ref(&n),GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;}out->as.quantity.num=198;}
    return true;
}
static GeoEvalContext *make(State *state)
{
    GeoEvalContext *ctx=geo_eval_create(123,456);state->context=ctx;
    GeoSourceProvider provider={1,"neutral.test","algorithm/1",state,describe,evaluate};
    if(!ctx||!geo_eval_register(ctx,&provider)){geo_eval_destroy(ctx);return NULL;}return ctx;
}
static int ownership(void)
{
    State a={0},b={0};a.base=10;b.base=90;GeoEvalContext *x=make(&a),*y=make(&b);CHECK(x&&y);
    unsigned id=12;GeoSourceValue value;CHECK(geo_eval_source(x,ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&value.as.quantity.num==22);
    id=14;GeoSourceNodeView node;CHECK(geo_eval_node_at(x,0,&node)&&key_id(&node.source)==12);
    id=12;CHECK(geo_eval_source(y,ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&value.as.quantity.num==102);
    unsigned char ka[]={42,0,12},kb[]={43,0,12};
    CHECK(geo_eval_source(x,(GeoSourceRef){1,ka,sizeof ka},GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);
    ka[0]=44;CHECK(geo_eval_source(x,(GeoSourceRef){1,kb,sizeof kb},GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK);
    CHECK(geo_eval_node_count(x)==3);CHECK(geo_eval_node_at(x,1,&node)&&((const unsigned char *)node.source.key)[0]==42);
    CHECK(geo_eval_candidate_id(x)==123&&geo_eval_base_revision(x)==456);
    const GeoSourceProvider *p=geo_eval_provider_at(x,0);CHECK(p&&strcmp(p->name_space,"neutral.test")==0&&strcmp(p->implementation_fingerprint,"algorithm/1")==0);
    CHECK(!geo_eval_register(x,p));geo_eval_destroy(x);geo_eval_destroy(y);return 0;
}
static int cycles(void)
{
    State state={0};GeoEvalContext *ctx=make(&state);CHECK(ctx);unsigned id=1;GeoSourceValue value={0};value.as.quantity.num=999;
    CHECK(geo_eval_source(ctx,ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_FAILED);
    CHECK(value.as.quantity.num==999&&state.calls[1]==1&&state.calls[2]==1&&state.cycles==1);
    CHECK(geo_eval_source(ctx,ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_FAILED&&state.calls[1]==1);
    CHECK(geo_eval_edge_count(ctx)==2);geo_eval_destroy(ctx);return 0;
}
static int relations(void)
{
    State state={0};GeoEvalContext *ctx=make(&state);CHECK(ctx);unsigned id=10;GeoSourceValue value;
    CHECK(geo_eval_source(ctx,ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&value.as.quantity.num==12);
    CHECK(state.calls[11]==1&&state.calls[12]==1&&state.calls[13]==0&&geo_eval_edge_count(ctx)==3);
    bool kinds[3]={0};for(size_t i=0;i<geo_eval_edge_count(ctx);++i){GeoSourceEdge edge;CHECK(geo_eval_edge_at(ctx,i,&edge)&&edge.consumer==0);kinds[edge.kind]=true;}
    CHECK(kinds[0]&&kinds[1]&&kinds[2]);GeoSourceNodeView node;CHECK(geo_eval_node_at(ctx,2,&node)&&node.state==GEO_NODE_NEW);
    geo_eval_destroy(ctx);return 0;
}
static int failures(void)
{
    State state={0};GeoEvalContext *ctx=make(&state);CHECK(ctx);GeoSourceValue value;
    for(unsigned id=19;id<=21;++id)for(int k=0;k<2;++k)
        CHECK(geo_eval_source(ctx,ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==(id==21?GEO_SOURCE_INVALID:GEO_SOURCE_FAILED));
    CHECK(state.calls[19]==1&&state.calls[20]==2&&state.calls[21]==0);
    geo_eval_destroy(ctx);return 0;
}
static int types(void)
{
    State state={0};GeoEvalContext *ctx=make(&state);CHECK(ctx);GeoSourceValue value;
    for(unsigned id=22;id<=24;++id)for(int repeat=0;repeat<2;++repeat)
        CHECK(geo_eval_source(ctx,ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_INVALID);
    for(unsigned id=50;id<=54;++id)CHECK(geo_eval_source(ctx,ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&value.kind==(GeoSourceValueKind)(id-49));
    geo_eval_destroy(ctx);return 0;
}
static int growth(void)
{
    State state={0};GeoEvalContext *ctx=make(&state);CHECK(ctx);unsigned id=100;GeoSourceValue value;
    CHECK(geo_eval_source(ctx,ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&value.as.quantity.num==198);
    CHECK(geo_eval_node_count(ctx)==199&&geo_eval_edge_count(ctx)==198);
    CHECK(geo_eval_source(ctx,ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&state.calls[100]==1);
    geo_eval_destroy(ctx);return 0;
}
static int position(void)
{
    State state={0};GeoEvalContext *ctx=make(&state);CHECK(ctx);unsigned id=40;GeoSourceValue value;
    CHECK(geo_eval_source(ctx,ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&value.as.position.coordinate==40);
    geo_eval_destroy(ctx);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"ownership"))return ownership();if(!strcmp(argv[1],"cycles"))return cycles();
    if(!strcmp(argv[1],"relations"))return relations();if(!strcmp(argv[1],"failures"))return failures();
    if(!strcmp(argv[1],"types"))return types();if(!strcmp(argv[1],"growth"))return growth();
    if(!strcmp(argv[1],"position"))return position();return 2;
}
