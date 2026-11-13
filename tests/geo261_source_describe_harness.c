/* Public K-only describe contract. Metadata is observable without inventing a
 * value or a value dependency; NEW and described are independent facts. */
#include "source.h"
#include <stdio.h>
#include <string.h>

#define CHECK(value,label) do{if(!(value)){fprintf(stderr,"ASSERT:%s:%d\n",label,__LINE__);return 1;}}while(0)
#define DESCRIBE_PROVIDER 17
typedef struct {
    GeoEvalContext *context;
    unsigned descriptions[100],evaluations[100];
    bool saw_undescribed_definition,saw_active_parent;
} State;
static const char definition_schema[]="geometry.test-definition/1";
static const unsigned char definition_bytes[]={0x41,0x00,0xfe,0x00,0x42};

static GeoSourceRef source_ref(const uint32_t *id)
{return (GeoSourceRef){DESCRIBE_PROVIDER,id,sizeof *id};}
static bool source_id(const GeoSourceRef *source,uint32_t *id)
{
    if(source->provider!=DESCRIBE_PROVIDER||!source->key||source->key_size!=sizeof *id)return false;
    memcpy(id,source->key,sizeof *id);return *id<100;
}
static size_t node_index(const GeoEvalContext *ctx,uint32_t id)
{
    for(size_t i=0;i<geo_eval_node_count(ctx);++i){GeoSourceNodeView node;uint32_t key;
        if(geo_eval_node_at(ctx,i,&node)&&source_id(&node.source,&key)&&key==id)return i;}
    return SIZE_MAX;
}
static bool describe(void *opaque,const GeoSourceRef *source,GeoSourceDescriptor *out)
{
    State *state=opaque;uint32_t id;if(!source_id(source,&id))return false;
    ++state->descriptions[id];memset(out,0,sizeof *out);
    out->kind=GEO_SOURCE_QUANTITY;out->unit=id==1?GEO_UNIT_SCALAR:GEO_UNIT_LENGTH;out->context.axis=-1;
    if(id==3||id==4){out->kind=GEO_SOURCE_AXIS_POSITION;out->context=id==3?
        (GeoSourceContext){true,42,1}:(GeoSourceContext){false,0,2};}
    if(id>=20&&id<=26){out->kind=GEO_SOURCE_DEFINITION;out->unit=GEO_UNIT_SCALAR;}
    if(id==90)return false; /* Even a rejecting callback writes its scratch output. */
    if(id==91)out->kind=(GeoSourceValueKind)99;
    if(id==92)out->unit=(GeoQuantityUnit)99;
    if(id==93)out->context.axis=3;
    return true;
}
static bool evaluate(void *opaque,GeoEvalContext *ctx,const GeoSourceRef *source,GeoSourceValue *out)
{
    State *state=opaque;uint32_t id;if(ctx!=state->context||!source_id(source,&id))return false;
    ++state->evaluations[id];memset(out,0,sizeof *out);
    out->kind=GEO_SOURCE_QUANTITY;
    out->as.quantity=id==1?(GeoQuantity){3,2,GEO_UNIT_SCALAR}:(GeoQuantity){9,4,GEO_UNIT_LENGTH};
    if(id==3||id==4){out->kind=GEO_SOURCE_AXIS_POSITION;out->as.position=id==3?
        (GeoAxisPosition){123,{true,42,1}}:(GeoAxisPosition){-37,{false,0,2}};}
    if(id>=20&&id<=26){
        out->kind=GEO_SOURCE_DEFINITION;
        out->as.definition=(GeoDefinitionValue){definition_schema,definition_bytes,sizeof definition_bytes};
        if(id==21)out->as.definition.schema="";
        if(id==22)out->as.definition.schema=NULL;
        if(id==23)out->as.definition.content=NULL;
        if(id>=24){out->as.definition.content_size=0;out->as.definition.content=id==26?definition_bytes:NULL;}
        if(id==25)out->as.definition.schema=" \t ";
    }
    if(id==94)return false;
    if(id==10){
        uint32_t child=2,metadata_only=3;GeoSourceNodeView node;GeoSourceDescriptor descriptor;
        if(geo_eval_depend(ctx,source_ref(&child),GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)return false;
        state->saw_undescribed_definition=geo_eval_node_at(ctx,node_index(ctx,child),&node)&&
            node.state==GEO_NODE_NEW&&!node.described&&!node.value;
        if(geo_eval_describe(ctx,source_ref(&child),&descriptor)!=GEO_SOURCE_OK)return false;
        if(geo_eval_describe(ctx,source_ref(&metadata_only),&descriptor)!=GEO_SOURCE_OK)return false;
        state->saw_active_parent=geo_eval_node_at(ctx,node_index(ctx,id),&node)&&node.state==GEO_NODE_ACTIVE;
        out->as.quantity=(GeoQuantity){42,1,GEO_UNIT_LENGTH};
    }
    return true;
}
static GeoEvalContext *make(State *state)
{
    state->context=geo_eval_create(261,73);if(!state->context)return NULL;
    GeoSourceProvider provider={DESCRIBE_PROVIDER,"test.describe-only","geo261-describe/1",state,describe,evaluate};
    if(!geo_eval_register(state->context,&provider)){geo_eval_destroy(state->context);state->context=NULL;}
    return state->context;
}
static bool descriptor_equal(GeoSourceDescriptor a,GeoSourceDescriptor b)
{
    return a.kind==b.kind&&a.unit==b.unit&&a.context.has_placement==b.context.has_placement&&
        a.context.placement==b.context.placement&&a.context.axis==b.context.axis&&a.retry_failure==b.retry_failure;
}
static int new_node(const GeoEvalContext *ctx,uint32_t id,const GeoSourceDescriptor *descriptor)
{
    GeoSourceNodeView node;CHECK(geo_eval_node_at(ctx,node_index(ctx,id),&node),"described-node-present");
    CHECK(node.described&&node.state==GEO_NODE_NEW&&node.status==GEO_SOURCE_OK&&!node.value,"described-is-new-and-has-no-value");
    CHECK(descriptor_equal(node.descriptor,*descriptor),"node-retains-exact-descriptor");return 0;
}
static int quantities(void)
{
    State state={0};GeoEvalContext *ctx=make(&state);CHECK(ctx,"quantity-context");
    for(uint32_t id=1;id<=2;++id){GeoSourceDescriptor descriptor;
        CHECK(geo_eval_describe(ctx,source_ref(&id),&descriptor)==GEO_SOURCE_OK,"quantity-describe");
        CHECK(descriptor.kind==GEO_SOURCE_QUANTITY&&descriptor.unit==(id==1?GEO_UNIT_SCALAR:GEO_UNIT_LENGTH)&&
            !descriptor.context.has_placement&&descriptor.context.placement==0&&descriptor.context.axis==-1,"quantity-exact-metadata");
        CHECK(new_node(ctx,id,&descriptor)==0,"quantity-new-node");
        CHECK(geo_eval_describe(ctx,source_ref(&id),&descriptor)==GEO_SOURCE_OK&&state.descriptions[id]==1&&
            state.evaluations[id]==0,"describe-memoizes-metadata-without-evaluation");
    }
    CHECK(geo_eval_node_count(ctx)==2&&geo_eval_edge_count(ctx)==0,"quantity-describe-adds-no-edges");
    CHECK(geo_eval_candidate_id(ctx)==261&&geo_eval_base_revision(ctx)==73,"describe-keeps-candidate-identity");
    geo_eval_destroy(ctx);return 0;
}
static int axes(void)
{
    State state={0};GeoEvalContext *ctx=make(&state);CHECK(ctx,"axis-context");
    for(uint32_t id=3;id<=4;++id){GeoSourceDescriptor descriptor;
        CHECK(geo_eval_describe(ctx,source_ref(&id),&descriptor)==GEO_SOURCE_OK,"axis-describe");
        CHECK(descriptor.kind==GEO_SOURCE_AXIS_POSITION&&descriptor.unit==GEO_UNIT_LENGTH&&
            descriptor.context.has_placement==(id==3)&&descriptor.context.placement==(id==3?42:0)&&
            descriptor.context.axis==(id==3?1:2),"axis-preserves-global-or-placed-context");
        CHECK(new_node(ctx,id,&descriptor)==0&&state.descriptions[id]==1&&state.evaluations[id]==0,"axis-remains-unevaluated");
    }
    CHECK(geo_eval_node_count(ctx)==2&&geo_eval_edge_count(ctx)==0,"axis-describe-adds-no-edges");geo_eval_destroy(ctx);return 0;
}
static int definition_edge(void)
{
    State state={0};GeoEvalContext *ctx=make(&state);CHECK(ctx,"definition-context");uint32_t root=10;GeoSourceValue value;
    CHECK(geo_eval_source(ctx,source_ref(&root),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
        value.kind==GEO_SOURCE_QUANTITY&&value.as.quantity.num==42&&value.as.quantity.den==1&&value.as.quantity.unit==GEO_UNIT_LENGTH,"definition-parent-value");
    CHECK(state.saw_undescribed_definition&&state.saw_active_parent,"describe-fills-new-node-without-disturbing-active-parent");
    CHECK(geo_eval_node_count(ctx)==3&&geo_eval_edge_count(ctx)==1,"describe-with-active-consumer-adds-no-dependency");
    GeoSourceEdge edge;CHECK(geo_eval_edge_at(ctx,0,&edge)&&edge.consumer==node_index(ctx,10)&&
        edge.source==node_index(ctx,2)&&edge.kind==GEO_DEPENDENCY_DEFINITION_REQUIRED,"only-explicit-definition-edge-remains");
    for(uint32_t id=2;id<=3;++id){GeoSourceDescriptor descriptor;
        CHECK(geo_eval_describe(ctx,source_ref(&id),&descriptor)==GEO_SOURCE_OK&&new_node(ctx,id,&descriptor)==0&&
            state.descriptions[id]==1&&state.evaluations[id]==0,"definition-and-metadata-only-children-remain-new");}
    CHECK(state.descriptions[10]==1&&state.evaluations[10]==1,"only-parent-was-evaluated");geo_eval_destroy(ctx);return 0;
}
static int describe_then_evaluate(void)
{
    State state={0};GeoEvalContext *ctx=make(&state);CHECK(ctx,"transition-context");uint32_t id=1;GeoSourceDescriptor descriptor;
    CHECK(geo_eval_describe(ctx,source_ref(&id),&descriptor)==GEO_SOURCE_OK&&new_node(ctx,id,&descriptor)==0,"transition-starts-described-new");
    CHECK(state.descriptions[1]==1&&state.evaluations[1]==0,"transition-does-not-evaluate-early");
    GeoSourceValue value;CHECK(geo_eval_source(ctx,source_ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
        value.kind==GEO_SOURCE_QUANTITY&&value.as.quantity.num==3&&value.as.quantity.den==2&&value.as.quantity.unit==GEO_UNIT_SCALAR,"transition-exact-value");
    GeoSourceNodeView node;CHECK(geo_eval_node_at(ctx,0,&node)&&node.described&&node.state==GEO_NODE_VALID&&
        node.status==GEO_SOURCE_OK&&node.value&&descriptor_equal(node.descriptor,descriptor),"transition-retains-metadata-and-publishes-value");
    CHECK(geo_eval_describe(ctx,source_ref(&id),&descriptor)==GEO_SOURCE_OK&&
        geo_eval_source(ctx,source_ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
        state.descriptions[1]==1&&state.evaluations[1]==1,"description-and-evaluation-each-run-once");
    CHECK(geo_eval_node_count(ctx)==1&&geo_eval_edge_count(ctx)==0,"transition-does-not-invent-edge");geo_eval_destroy(ctx);return 0;
}
static int sealed(void)
{
    State state={0};GeoEvalContext *ctx=make(&state);CHECK(ctx,"sealed-context");uint32_t id=1;GeoSourceDescriptor first;
    CHECK(geo_eval_describe(ctx,source_ref(&id),&first)==GEO_SOURCE_OK,"sealed-described-new-precondition");
    id=2;CHECK(geo_eval_depend(ctx,source_ref(&id),GEO_DEPENDENCY_DEFINITION_REQUIRED)==GEO_SOURCE_OK,"sealed-undescribed-precondition");
    GeoSourceNodeView node;CHECK(geo_eval_node_at(ctx,node_index(ctx,2),&node)&&!node.described&&node.state==GEO_NODE_NEW,"sealed-definition-is-undescribed");
    id=3;GeoSourceValue value;CHECK(geo_eval_source(ctx,source_ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK,"sealed-valid-precondition");
    id=94;CHECK(geo_eval_source(ctx,source_ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_FAILED,"sealed-described-failed-precondition");
    CHECK(geo_eval_seal(ctx)&&geo_eval_is_sealed(ctx),"sealed-graph");State before=state;
    id=1;GeoSourceDescriptor descriptor;CHECK(geo_eval_describe(ctx,source_ref(&id),&descriptor)==GEO_SOURCE_OK&&
        descriptor_equal(descriptor,first)&&new_node(ctx,1,&descriptor)==0,"sealed-described-new-is-readable");
    id=3;CHECK(geo_eval_describe(ctx,source_ref(&id),&descriptor)==GEO_SOURCE_OK&&descriptor.kind==GEO_SOURCE_AXIS_POSITION&&
        descriptor.context.has_placement&&descriptor.context.placement==42&&descriptor.context.axis==1,"sealed-valid-metadata-is-readable");
    CHECK(geo_eval_source(ctx,source_ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&value.as.position.coordinate==123,"sealed-valid-value-is-readable");
    id=94;CHECK(geo_eval_describe(ctx,source_ref(&id),&descriptor)==GEO_SOURCE_OK&&descriptor.kind==GEO_SOURCE_QUANTITY&&
        descriptor.unit==GEO_UNIT_LENGTH&&geo_eval_node_at(ctx,node_index(ctx,id),&node)&&node.described&&
        node.state==GEO_NODE_FAILED&&node.status==GEO_SOURCE_FAILED&&!node.value,"sealed-failed-value-retains-readable-valid-metadata");
    GeoSourceDescriptor sentinel;memset(&sentinel,0x5a,sizeof sentinel);
    for(uint32_t key=2;key<=4;key+=2){memcpy(&descriptor,&sentinel,sizeof descriptor);
        CHECK(geo_eval_describe(ctx,source_ref(&key),&descriptor)==GEO_SOURCE_INVALID&&
            !memcmp(&descriptor,&sentinel,sizeof descriptor),"sealed-rejects-undescribed-and-new-key-without-out-write");}
    id=1;GeoSourceValue original;memset(&original,0x5a,sizeof original);memcpy(&value,&original,sizeof value);
    CHECK(geo_eval_source(ctx,source_ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_INVALID&&
        !memcmp(&value,&original,sizeof value),"sealed-described-new-cannot-become-value");
    CHECK(geo_eval_node_count(ctx)==4&&geo_eval_edge_count(ctx)==0&&
        !memcmp(before.descriptions,state.descriptions,sizeof state.descriptions)&&
        !memcmp(before.evaluations,state.evaluations,sizeof state.evaluations),"sealed-reads-add-no-nodes-edges-or-provider-calls");
    CHECK(geo_eval_node_at(ctx,node_index(ctx,2),&node)&&!node.described&&node.state==GEO_NODE_NEW&&!node.value,"sealed-does-not-backfill-definition-metadata");
    geo_eval_destroy(ctx);return 0;
}
static int failures(void)
{
    State state={0};GeoEvalContext *ctx=make(&state);CHECK(ctx,"failure-context");GeoSourceDescriptor sentinel;
    memset(&sentinel,0x5a,sizeof sentinel);
    for(uint32_t id=90;id<=93;++id)for(unsigned attempt=1;attempt<=2;++attempt){GeoSourceDescriptor descriptor;memcpy(&descriptor,&sentinel,sizeof descriptor);
        CHECK(geo_eval_describe(ctx,source_ref(&id),&descriptor)==(id==90?GEO_SOURCE_MISSING:GEO_SOURCE_INVALID),"describe-failure-status");
        CHECK(!memcmp(&descriptor,&sentinel,sizeof descriptor)&&state.descriptions[id]==attempt&&state.evaluations[id]==0,"rejecting-or-invalid-descriptor-never-writes-out-or-evaluates");
        GeoSourceNodeView node;CHECK(geo_eval_node_at(ctx,node_index(ctx,id),&node)&&!node.described&&
            node.state==GEO_NODE_NEW&&node.status==GEO_SOURCE_OK&&!node.value,"failed-description-is-not-cached-as-value-failure");}
    GeoSourceDescriptor descriptor;memcpy(&descriptor,&sentinel,sizeof descriptor);uint32_t id=1;
    CHECK(geo_eval_describe(NULL,source_ref(&id),&descriptor)==GEO_SOURCE_INVALID&&!memcmp(&descriptor,&sentinel,sizeof descriptor),"null-context-keeps-out");
    CHECK(geo_eval_describe(ctx,source_ref(&id),NULL)==GEO_SOURCE_INVALID&&state.descriptions[id]==0,"null-output-never-calls-provider");
    CHECK(geo_eval_describe(ctx,(GeoSourceRef){DESCRIBE_PROVIDER,NULL,sizeof id},&descriptor)==GEO_SOURCE_INVALID&&
        !memcmp(&descriptor,&sentinel,sizeof descriptor),"null-key-keeps-out");
    CHECK(geo_eval_describe(ctx,(GeoSourceRef){99,&id,sizeof id},&descriptor)==GEO_SOURCE_MISSING&&
        !memcmp(&descriptor,&sentinel,sizeof descriptor),"missing-provider-keeps-out");
    CHECK(geo_eval_edge_count(ctx)==0&&state.evaluations[1]==0,"failure-describe-creates-no-edges-or-values");geo_eval_destroy(ctx);return 0;
}
static int definitions(void)
{
    State state={0};GeoEvalContext *ctx=make(&state);CHECK(ctx,"definition-value-context");
    GeoSourceValue sentinel;memset(&sentinel,0x5a,sizeof sentinel);
    for(uint32_t id=20;id<=26;++id){GeoSourceDescriptor descriptor;
        CHECK(geo_eval_describe(ctx,source_ref(&id),&descriptor)==GEO_SOURCE_OK&&
            descriptor.kind==GEO_SOURCE_DEFINITION&&descriptor.unit==GEO_UNIT_SCALAR&&
            descriptor.context.axis==-1&&new_node(ctx,id,&descriptor)==0,"definition-type-is-describable-before-value");
        CHECK(state.descriptions[id]==1&&state.evaluations[id]==0,"definition-description-does-not-evaluate");
        GeoSourceValue value;memcpy(&value,&sentinel,sizeof value);
        GeoSourceStatus status=geo_eval_source(ctx,source_ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value);
        GeoSourceNodeView node;CHECK(geo_eval_node_at(ctx,node_index(ctx,id),&node)&&node.described,"definition-node-view");
        if(id>=21&&id<=23){
            CHECK(status==GEO_SOURCE_INVALID&&!memcmp(&value,&sentinel,sizeof value),"invalid-schema-or-missing-content-preserves-output");
            CHECK(node.state==GEO_NODE_FAILED&&node.status==GEO_SOURCE_INVALID&&!node.value,"invalid-definition-has-no-published-value");
        }else{
            CHECK(status==GEO_SOURCE_OK&&value.kind==GEO_SOURCE_DEFINITION&&node.state==GEO_NODE_VALID&&
                node.status==GEO_SOURCE_OK&&node.value&&node.value->kind==GEO_SOURCE_DEFINITION,"valid-definition-retains-typed-node-value");
            const GeoDefinitionValue *definition=&value.as.definition,*stored=&node.value->as.definition;
            CHECK(definition->schema==stored->schema&&definition->content==stored->content&&
                definition->content_size==stored->content_size,"definition-node-keeps-provider-owned-schema-and-content");
            if(id==20){
                CHECK(definition->schema==definition_schema&&!strcmp(definition->schema,"geometry.test-definition/1")&&
                    definition->content==definition_bytes&&definition->content_size==5&&
                    !memcmp(definition->content,definition_bytes,5),"definition-retains-exact-binary-content-including-nuls");
            }else{
                CHECK(definition->content_size==0&&definition->content==(id==26?definition_bytes:NULL),"zero-size-definition-allows-null-or-nonnull-content");
                CHECK(!strcmp(definition->schema,id==25?" \t ":"geometry.test-definition/1"),"nonempty-whitespace-schema-is-not-trimmed");
            }
        }
        CHECK(state.descriptions[id]==1&&state.evaluations[id]==1,"definition-describe-and-evaluate-each-once");
    }
    CHECK(geo_eval_node_count(ctx)==7&&geo_eval_edge_count(ctx)==0&&geo_eval_seal(ctx),"definition-values-seal-without-invented-edges");
    for(uint32_t id=20;id<=26;++id){GeoSourceDescriptor descriptor;GeoSourceValue value;memcpy(&value,&sentinel,sizeof value);
        CHECK(geo_eval_describe(ctx,source_ref(&id),&descriptor)==GEO_SOURCE_OK&&descriptor.kind==GEO_SOURCE_DEFINITION,"sealed-definition-metadata-remains-readable");
        GeoSourceStatus status=geo_eval_source(ctx,source_ref(&id),GEO_DEPENDENCY_VALUE_REQUIRED,&value);
        if(id>=21&&id<=23)CHECK(status==GEO_SOURCE_INVALID&&!memcmp(&value,&sentinel,sizeof value),"sealed-invalid-definition-keeps-output");
        else{
            CHECK(status==GEO_SOURCE_OK&&value.kind==GEO_SOURCE_DEFINITION&&
                value.as.definition.content_size==(id==20?5:0)&&
                !strcmp(value.as.definition.schema,id==25?" \t ":"geometry.test-definition/1"),"sealed-definition-retains-exact-schema-and-size");
            if(id==20)CHECK(value.as.definition.content==definition_bytes&&!memcmp(value.as.definition.content,definition_bytes,5),"sealed-definition-retains-binary-content");
        }
        CHECK(state.descriptions[id]==1&&state.evaluations[id]==1,"sealed-definition-read-does-not-call-provider");
    }
    CHECK(geo_eval_node_count(ctx)==7&&geo_eval_edge_count(ctx)==0,"sealed-definition-graph-unchanged");geo_eval_destroy(ctx);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"quantities"))return quantities();
    if(!strcmp(argv[1],"axes"))return axes();
    if(!strcmp(argv[1],"definition-edge"))return definition_edge();
    if(!strcmp(argv[1],"transition"))return describe_then_evaluate();
    if(!strcmp(argv[1],"sealed"))return sealed();
    if(!strcmp(argv[1],"failures"))return failures();
    if(!strcmp(argv[1],"definitions"))return definitions();
    return 2;
}
