/* K-only client: native parameter AST references must traverse the demand graph.
 * Expected arithmetic, identities and failures are fixed here, independently of
 * the parity check against the existing non-graph evaluator. */
#include "parameter_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(value,label) do{if(!(value)){fprintf(stderr,"ASSERT:%s:%d\n",label,__LINE__);return 1;}}while(0)
#define PARAMETER_PROVIDER 37
typedef struct {GeoEvalContext *context;GeoParameterSources *parameters;} Binding;
static GeoParameterRef ref(uint32_t card,uint32_t field)
{return (GeoParameterRef){true,card,field};}
static bool quantity(GeoQuantity q,int64_t num,int64_t den,GeoQuantityUnit unit)
{return q.num==num&&q.den==den&&q.unit==unit;}
static bool same_ref(GeoParameterRef a,GeoParameterRef b)
{return a.set==b.set&&a.parameter_id==b.parameter_id&&a.field_id==b.field_id;}
static bool same_error(const GeoParameterError *a,const GeoParameterError *b)
{
    if(a->status!=b->status||a->exact!=b->exact||!same_ref(a->source,b->source)||
       !quantity(a->quantity,b->quantity.num,b->quantity.den,b->quantity.unit)||
       strcmp(a->detail,b->detail)||a->trace_count!=b->trace_count)return false;
    for(size_t i=0;i<a->trace_count;++i)if(!same_ref(a->trace[i],b->trace[i]))return false;
    return true;
}
static void literal(GeoParameterField *f,uint32_t card,uint32_t id,int type,int num,int den)
{
    memset(f,0,sizeof *f);f->parameter_id=card;f->id=id;f->type=type;
    snprintf(f->name,sizeof f->name,"field-%u",id);
    snprintf(f->expression,sizeof f->expression,
        "{\"op\":\"literal\",\"num\":\"%d\",\"den\":\"%d\",\"unit\":\"%s\"}",num,den,type==GEO_PARAMETER_DIMENSION?"mm":"1");
}
static void reference(GeoParameterField *f,uint32_t card,uint32_t id,uint32_t from_card,uint32_t from_field)
{
    literal(f,card,id,GEO_PARAMETER_DIMENSION,0,1);
    snprintf(f->expression,sizeof f->expression,"{\"op\":\"ref\",\"parameterId\":%u,\"fieldId\":%u}",from_card,from_field);
}
static bool put(GeoParameterStore *store,uint32_t id,GeoParameterField *fields,size_t count)
{
    GeoParameterCard card;GeoParameterError error;geo_parameters_begin_definition(store,id,&card);
    snprintf(card.name,sizeof card.name,"card-%u",id);card.count=count;
    for(size_t i=0;i<count;++i)if(!geo_parameters_accept_field(store,&card,fields,i,&error))return false;
    return geo_parameters_put(store,&card,fields,&error);
}
static bool bind(Binding *binding,GeoParameterStore *store,uint64_t id)
{
    binding->context=geo_eval_create(id,73);if(!binding->context)return false;
    binding->parameters=geo_parameter_sources_register(binding->context,store,PARAMETER_PROVIDER,
        "test.parameter.field","geo261-native-ast/1");return binding->parameters!=NULL;
}
static void dispose(Binding *binding)
{geo_eval_destroy(binding->context);geo_parameter_sources_destroy(binding->parameters);}
static size_t node_index(const GeoEvalContext *ctx,uint32_t card,uint32_t field)
{
    for(size_t i=0;i<geo_eval_node_count(ctx);++i){GeoSourceNodeView node;uint32_t ids[2];
        if(!geo_eval_node_at(ctx,i,&node)||node.source.provider!=PARAMETER_PROVIDER||node.source.key_size!=sizeof ids)continue;
        memcpy(ids,node.source.key,sizeof ids);if(ids[0]==card&&ids[1]==field)return i;}
    return SIZE_MAX;
}
static bool edge(const GeoEvalContext *ctx,uint32_t consumer,uint32_t source)
{
    size_t a=node_index(ctx,consumer,1),b=node_index(ctx,source,1);
    for(size_t i=0;i<geo_eval_edge_count(ctx);++i){GeoSourceEdge e;
        if(geo_eval_edge_at(ctx,i,&e)&&e.consumer==a&&e.source==b&&e.kind==GEO_DEPENDENCY_VALUE_REQUIRED)return true;}
    return false;
}
static int node_value(const GeoEvalContext *ctx,uint32_t card,uint32_t field,int64_t num,int64_t den,GeoQuantityUnit unit)
{
    GeoSourceNodeView node;CHECK(geo_eval_node_at(ctx,node_index(ctx,card,field),&node),"parameter-node-present");
    CHECK(node.state==GEO_NODE_VALID&&node.status==GEO_SOURCE_OK&&node.value,"parameter-node-valid");
    CHECK(node.descriptor.kind==GEO_SOURCE_QUANTITY&&node.descriptor.unit==unit&&
        node.value->kind==GEO_SOURCE_QUANTITY&&quantity(node.value->as.quantity,num,den,unit),"parameter-node-exact-value-and-unit");
    return 0;
}
static bool diamond(GeoParameterStore *store)
{
    GeoParameterField f;literal(&f,1,1,GEO_PARAMETER_DIMENSION,0,1);
    strcpy(f.expression,"{\"op\":\"add\",\"left\":{\"op\":\"ref\",\"parameterId\":2,\"fieldId\":1},\"right\":{\"op\":\"ref\",\"parameterId\":3,\"fieldId\":1}}");
    if(!put(store,1,&f,1))return false;
    for(uint32_t card=2;card<=3;++card){literal(&f,card,1,GEO_PARAMETER_DIMENSION,0,1);
        snprintf(f.expression,sizeof f.expression,"{\"op\":\"mul\",\"left\":{\"op\":\"ref\",\"parameterId\":4,\"fieldId\":1},\"right\":{\"op\":\"literal\",\"num\":\"%u\",\"den\":\"1\",\"unit\":\"1\"}}",card);
        if(!put(store,card,&f,1))return false;}
    literal(&f,4,1,GEO_PARAMETER_DIMENSION,7,3);return put(store,4,&f,1);
}
static int diamond_case(void)
{
    GeoParameterStore *store=geo_parameters_create();CHECK(store&&diamond(store),"diamond-definitions");
    GeoParameterStore *plain=geo_parameters_clone(store);CHECK(plain,"parity-snapshot");Binding graph={0};CHECK(bind(&graph,store,901),"graph-binding");
    GeoParameterError a,b;GeoQuantity value={0};
    CHECK(geo_parameter_sources_value(graph.parameters,ref(1,1),&value,&a)&&quantity(value,35,3,GEO_UNIT_LENGTH),"diamond-exact-result");
    CHECK(geo_parameters_rebuild(plain,&b)&&geo_parameters_equal(store,plain),"diamond-existing-evaluator-parity");
    /* Mutation control bypasses the resolver but still computes all four
     * correct values. This edge assertion must be the first failing verdict. */
    CHECK(edge(graph.context,1,2)&&edge(graph.context,1,3)&&edge(graph.context,2,4)&&edge(graph.context,3,4),"parameter-ast-dependency-edge");
    CHECK(geo_eval_node_count(graph.context)==4&&geo_eval_edge_count(graph.context)==4,"diamond-has-four-nodes-four-edges");
    CHECK(node_value(graph.context,1,1,35,3,GEO_UNIT_LENGTH)==0&&node_value(graph.context,2,1,14,3,GEO_UNIT_LENGTH)==0&&
        node_value(graph.context,3,1,7,1,GEO_UNIT_LENGTH)==0&&node_value(graph.context,4,1,7,3,GEO_UNIT_LENGTH)==0,"diamond-node-values");
    CHECK(geo_parameter_sources_rebuild(graph.parameters,&a)&&geo_eval_edge_count(graph.context)==4,"rebuild-keeps-cached-edges");
    dispose(&graph);geo_parameters_destroy(plain);geo_parameters_destroy(store);return 0;
}
static int reject_type(int type,int num,int den,bool wrong_unit,GeoParameterStatus expected)
{
    GeoParameterStore *store=geo_parameters_create();CHECK(store,"type-store");GeoParameterField f;
    literal(&f,8,3,type,num,den);if(wrong_unit)strcpy(f.expression,"{\"op\":\"literal\",\"num\":\"3\",\"den\":\"1\",\"unit\":\"mm\"}");
    CHECK(put(store,8,&f,1),"type-definition");GeoParameterStore *plain=geo_parameters_clone(store);Binding graph={0};CHECK(plain&&bind(&graph,store,902),"type-bind");
    GeoParameterError a,b;CHECK(!geo_parameter_sources_rebuild(graph.parameters,&a)&&!geo_parameters_rebuild(plain,&b),"type-rejected");
    CHECK(a.status==expected&&same_ref(a.source,ref(0,0))&&a.trace_count==1&&same_ref(a.trace[0],ref(8,3)),"type-exact-error");
    CHECK(same_error(&a,&b),"type-error-parity");dispose(&graph);geo_parameters_destroy(plain);geo_parameters_destroy(store);return 0;
}
static int types_case(void)
{
    GeoParameterStore *store=geo_parameters_create();CHECK(store,"type-store");GeoParameterField fields[4];
    literal(&fields[0],1,1,GEO_PARAMETER_COUNT,3,1);literal(&fields[1],1,2,GEO_PARAMETER_RATIO,3,1);
    literal(&fields[2],1,3,GEO_PARAMETER_DIMENSION,3,1);literal(&fields[3],1,4,GEO_PARAMETER_RATIO,-3,2);
    CHECK(put(store,1,fields,4),"distinct-field-types");GeoParameterStore *plain=geo_parameters_clone(store);Binding graph={0};CHECK(plain&&bind(&graph,store,903),"type-bind");
    GeoParameterError a,b;CHECK(geo_parameter_sources_rebuild(graph.parameters,&a)&&geo_parameters_rebuild(plain,&b),"legal-types-rebuild");
    CHECK(geo_parameters_equal(store,plain),"types-existing-evaluator-parity");
    const GeoParameterField *actual=geo_parameters_fields(store);
    CHECK(actual[0].type==GEO_PARAMETER_COUNT&&actual[1].type==GEO_PARAMETER_RATIO&&actual[2].type==GEO_PARAMETER_DIMENSION,"count-ratio-definition-identities-retained");
    CHECK(node_value(graph.context,1,1,3,1,GEO_UNIT_SCALAR)==0&&node_value(graph.context,1,2,3,1,GEO_UNIT_SCALAR)==0&&
        node_value(graph.context,1,3,3,1,GEO_UNIT_LENGTH)==0&&node_value(graph.context,1,4,-3,2,GEO_UNIT_SCALAR)==0,"typed-node-quantities");
    GeoQuantity out={97,11,GEO_UNIT_LENGTH};
    for(uint32_t id=1;id<=2;++id)CHECK(!geo_parameters_dimension_value(store,ref(1,id),&out,&a)&&a.status==GEO_PARAMETER_NOT_DIMENSION&&
        same_ref(a.source,ref(1,id))&&quantity(out,97,11,GEO_UNIT_LENGTH),"scalar-does-not-become-dimension");
    CHECK(reject_type(GEO_PARAMETER_COUNT,-1,1,false,GEO_PARAMETER_COUNT_VALUE)==0&&
        reject_type(GEO_PARAMETER_COUNT,3,2,false,GEO_PARAMETER_COUNT_VALUE)==0&&
        reject_type(GEO_PARAMETER_RATIO,3,1,true,GEO_PARAMETER_FIELD_UNIT)==0,"type-rejection-boundaries");
    dispose(&graph);geo_parameters_destroy(plain);geo_parameters_destroy(store);return 0;
}
static int reference_failure(bool cycle)
{
    GeoParameterStore *store=geo_parameters_create();CHECK(store,"failure-store");GeoParameterField f;
    reference(&f,1,1,2,1);CHECK(put(store,1,&f,1),"first-reference");
    reference(&f,2,1,cycle?1:99,cycle?1:7);CHECK(put(store,2,&f,1),"second-reference");
    GeoParameterStore *plain=geo_parameters_clone(store);Binding graph={0};CHECK(plain&&bind(&graph,store,904),"failure-bind");
    GeoQuantity out={97,11,GEO_UNIT_LENGTH};GeoParameterError a,b;
    CHECK(!geo_parameter_sources_value(graph.parameters,ref(1,1),&out,&a)&&!geo_parameters_evaluate_field(plain,ref(1,1),&b),"reference-rejected");
    CHECK(a.status==(cycle?GEO_PARAMETER_CYCLE:GEO_PARAMETER_MISSING_FIELD)&&
        same_ref(a.source,cycle?ref(1,1):ref(99,7))&&a.trace_count==2&&
        same_ref(a.trace[0],ref(2,1))&&same_ref(a.trace[1],ref(1,1)),"reference-exact-error-and-inner-first-trace");
    CHECK(a.exact==GEO_EXACT_OK&&!a.detail[0]&&quantity(out,97,11,GEO_UNIT_LENGTH)&&same_error(&a,&b),"reference-error-parity-and-output-preservation");
    CHECK(geo_eval_node_count(graph.context)==2&&geo_eval_edge_count(graph.context)==(cycle?2:1)&&edge(graph.context,1,2)&&
        (!cycle||edge(graph.context,2,1)),"failed-reference-graph");
    for(size_t i=0;i<2;++i){GeoSourceNodeView node;CHECK(geo_eval_node_at(graph.context,i,&node)&&
        node.state==GEO_NODE_FAILED&&node.status==GEO_SOURCE_FAILED&&!node.value,"failure-node-without-value");}
    dispose(&graph);geo_parameters_destroy(plain);geo_parameters_destroy(store);return 0;
}
static GeoParameterRef chain_ref(size_t index)
{return ref((uint32_t)(index/16)+1,(uint32_t)(index%16)+1);}
static bool chain(GeoParameterStore *store,size_t count,bool cached)
{
    for(size_t start=0;start<count;start+=16){GeoParameterField fields[16];size_t n=count-start<16?count-start:16;
        for(size_t i=0;i<n;++i){size_t index=start+i;GeoParameterRef here=chain_ref(index);
            if((cached&&index==0)||(!cached&&index+1==count))literal(&fields[i],here.parameter_id,here.field_id,GEO_PARAMETER_DIMENSION,7,3);
            else{GeoParameterRef from=chain_ref(cached?index-1:index+1);reference(&fields[i],here.parameter_id,here.field_id,from.parameter_id,from.field_id);}}
        if(!put(store,chain_ref(start).parameter_id,fields,n))return false;}
    return true;
}
static int depth_case(bool cached)
{
    for(size_t count=64;count<=65;++count){GeoParameterStore *store=geo_parameters_create();CHECK(store&&chain(store,count,cached),"depth-definitions");
        GeoParameterStore *plain=geo_parameters_clone(store);Binding graph={0};CHECK(plain&&bind(&graph,store,905),"depth-bind");GeoParameterError a,b;
        bool graph_ok=geo_parameter_sources_rebuild(graph.parameters,&a),plain_ok=geo_parameters_rebuild(plain,&b);
        CHECK(graph_ok==(count==64)&&plain_ok==(count==64),"depth-limit-exactly-64");
        CHECK(same_error(&a,&b)&&geo_parameters_equal(store,plain),"depth-error-and-cache-parity");
        CHECK(geo_eval_node_count(graph.context)==count&&geo_eval_edge_count(graph.context)==count-1,"chain-node-and-edge-count");
        if(count==64){GeoParameterRef root=chain_ref(cached?63:0);CHECK(node_value(graph.context,root.parameter_id,root.field_id,7,3,GEO_UNIT_LENGTH)==0,"depth-64-exact-value");}
        else{CHECK(a.status==GEO_PARAMETER_DEPTH&&same_ref(a.source,ref(0,0))&&a.trace_count==(cached?1:64),"depth-65-exact-error");
            for(size_t i=0;i<a.trace_count;++i)CHECK(same_ref(a.trace[i],chain_ref(cached?64:63-i)),"depth-65-exact-trace");}
        dispose(&graph);geo_parameters_destroy(plain);geo_parameters_destroy(store);}
    return 0;
}
static int closure_case(void)
{
    GeoParameterStore *store=geo_parameters_create();CHECK(store,"closure-store");GeoParameterField f;
    reference(&f,9,1,99,7);CHECK(put(store,9,&f,1)&&diamond(store),"unrelated-invalid-field-before-closure");
    GeoParameterStore *plain=geo_parameters_clone(store);Binding graph={0};CHECK(plain&&bind(&graph,store,906),"closure-bind");
    GeoParameterError a,b;GeoQuantity out;
    CHECK(geo_parameter_sources_value(graph.parameters,ref(1,1),&out,&a)&&quantity(out,35,3,GEO_UNIT_LENGTH),"valid-closure-exact-value");
    CHECK(geo_parameters_evaluate_field(plain,ref(1,1),&b)&&geo_parameters_equal(store,plain),"closure-existing-evaluator-parity");
    CHECK(geo_eval_node_count(graph.context)==4&&geo_eval_edge_count(graph.context)==4&&node_index(graph.context,9,1)==SIZE_MAX,"closure-does-not-evaluate-unrelated-field");
    CHECK(!geo_parameter_sources_rebuild(graph.parameters,&a)&&!geo_parameters_rebuild(plain,&b)&&same_error(&a,&b),"full-rebuild-still-rejects-unrelated-field");
    CHECK(a.status==GEO_PARAMETER_MISSING_FIELD&&same_ref(a.source,ref(99,7))&&a.trace_count==1&&same_ref(a.trace[0],ref(9,1)),"unrelated-error-exact");
    CHECK(geo_parameter_sources_value(graph.parameters,ref(1,1),&out,&a)&&quantity(out,35,3,GEO_UNIT_LENGTH)&&a.status==GEO_PARAMETER_OK,"successful-closure-cache-survives-other-failure");
    dispose(&graph);geo_parameters_destroy(plain);geo_parameters_destroy(store);return 0;
}
static int snapshots_case(void)
{
    GeoParameterStore *live=geo_parameters_create();CHECK(live&&diamond(live),"live-definitions");GeoParameterField f;
    literal(&f,5,1,GEO_PARAMETER_DIMENSION,19,1);CHECK(put(live,5,&f,1),"unevaluated-independent-field");
    GeoParameterStore *before=geo_parameters_clone(live),*left=geo_parameters_clone(live),*right=geo_parameters_clone(live);
    CHECK(before&&left&&right,"independent-snapshots");literal(&f,4,1,GEO_PARAMETER_DIMENSION,11,3);CHECK(put(left,4,&f,1),"left-definition-edit");
    Binding a={0},b={0};CHECK(bind(&a,left,907)&&bind(&b,right,908),"snapshot-bindings");GeoParameterError error;GeoQuantity out;
    CHECK(geo_parameter_sources_store(a.parameters)==left&&geo_parameter_sources_store(b.parameters)==right&&
        geo_parameter_sources_context(a.parameters)==a.context&&geo_parameter_sources_context(b.parameters)==b.context,"binding-owns-exact-snapshot-and-context");
    CHECK(geo_eval_candidate_id(a.context)==907&&geo_eval_candidate_id(b.context)==908&&geo_eval_base_revision(a.context)==73,"snapshot-identities");
    CHECK(geo_parameter_sources_value(a.parameters,ref(1,1),&out,&error)&&quantity(out,55,3,GEO_UNIT_LENGTH),"left-snapshot-value");
    CHECK(geo_parameter_sources_value(b.parameters,ref(1,1),&out,&error)&&quantity(out,35,3,GEO_UNIT_LENGTH),"right-snapshot-value");
    CHECK(geo_parameters_equal(live,before)&&!geo_parameters_equal(left,right),"snapshot-evaluation-keeps-live-bytes");
    CHECK(geo_eval_seal(a.context)&&geo_eval_seal(b.context),"seal-both-snapshots");GeoParameterStore *sealed=geo_parameters_clone(left);CHECK(sealed,"sealed-store-snapshot");
    CHECK(geo_parameter_sources_value(a.parameters,ref(1,1),&out,&error)&&quantity(out,55,3,GEO_UNIT_LENGTH),"sealed-value-remains-readable");
    out=(GeoQuantity){97,11,GEO_UNIT_LENGTH};CHECK(!geo_parameter_sources_value(a.parameters,ref(5,1),&out,&error)&&
        error.status==GEO_PARAMETER_INVALID_DEFINITION&&same_ref(error.source,ref(5,1))&&quantity(out,97,11,GEO_UNIT_LENGTH),"sealed-context-does-not-evaluate-new-root");
    CHECK(geo_eval_node_count(a.context)==4&&geo_eval_edge_count(a.context)==4&&geo_parameters_equal(left,sealed)&&
        geo_parameters_equal(live,before)&&!geo_eval_reset(a.context),"sealed-read-keeps-graph-store-and-live-unchanged");
    dispose(&a);dispose(&b);geo_parameters_destroy(sealed);geo_parameters_destroy(before);
    geo_parameters_destroy(left);geo_parameters_destroy(right);geo_parameters_destroy(live);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"diamond"))return diamond_case();
    if(!strcmp(argv[1],"types"))return types_case();
    if(!strcmp(argv[1],"missing"))return reference_failure(false);
    if(!strcmp(argv[1],"cycle"))return reference_failure(true);
    if(!strcmp(argv[1],"depth-stack"))return depth_case(false);
    if(!strcmp(argv[1],"depth-cached"))return depth_case(true);
    if(!strcmp(argv[1],"closure"))return closure_case();
    if(!strcmp(argv[1],"snapshots"))return snapshots_case();
    return 2;
}
