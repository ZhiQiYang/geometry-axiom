/* Neutral K-only contract: geometry-derived context without eager evaluation. */
#include "source.h"
#include <stdio.h>
#include <string.h>
#define CHECK(c,label) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",label);return 1;}}while(0)
typedef struct {GeoSourceDescriptor descriptor;GeoSourceValue value;unsigned describes,evaluates;bool fails;} ContextFixture;
static bool describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{ContextFixture *f=user;(void)ref;++f->describes;*out=f->descriptor;return true;}
static bool evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{ContextFixture *f=user;(void)graph;(void)ref;++f->evaluates;*out=f->value;return !f->fails;}
static GeoSourceRef source_ref(void){return (GeoSourceRef){91,"axis",4};}
static GeoEvalContext *fixture(ContextFixture *f)
{
    memset(f,0,sizeof *f);
    f->descriptor=(GeoSourceDescriptor){.kind=GEO_SOURCE_AXIS_POSITION,.unit=GEO_UNIT_LENGTH,
        .context={false,0,-1},.retry_failure=true,.context_from_value=true};
    f->value=(GeoSourceValue){.kind=GEO_SOURCE_AXIS_POSITION,.as.position={37,{true,0,2}}};
    GeoEvalContext *graph=geo_eval_create(12,34);
    GeoSourceProvider provider={91,"test.generic-axis","context-contract/1",f,describe,evaluate};
    if(graph&&!geo_eval_register(graph,&provider)){geo_eval_destroy(graph);return NULL;}return graph;
}
static int metadata_case(void)
{
    ContextFixture f;GeoEvalContext *graph=fixture(&f);CHECK(graph,"context-fixture");
    GeoSourceDescriptor d;CHECK(geo_eval_describe(graph,source_ref(),&d)==GEO_SOURCE_OK&&
        d.context_from_value&&d.context.axis==-1&&f.describes==1&&f.evaluates==0,"context-description-does-not-evaluate");
    GeoSourceNodeView node;CHECK(geo_eval_node_at(graph,0,&node)&&node.state==GEO_NODE_NEW&&!node.value&&geo_eval_edge_count(graph)==0,
        "context-description-keeps-node-new");
    GeoSourceValue value;CHECK(geo_eval_source(graph,source_ref(),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
        value.as.position.coordinate==37&&value.as.position.context.has_placement&&value.as.position.context.placement==0&&value.as.position.context.axis==2,
        "context-value-admits-derived-axis-and-zero-placement");
    CHECK(geo_eval_describe(graph,source_ref(),&d)==GEO_SOURCE_OK&&d.context.has_placement&&d.context.placement==0&&d.context.axis==2,
        "context-finalizes-exact-returned-context");
    CHECK(!d.context_from_value,"context-clears-unresolved-flag");
    CHECK(geo_eval_node_at(graph,0,&node)&&node.state==GEO_NODE_VALID&&node.descriptor.context.axis==2&&!node.descriptor.context_from_value,
        "context-node-view-is-consistent");
    f.value.as.position.context=(GeoSourceContext){true,91,1};f.value.as.position.coordinate=99;
    CHECK(geo_eval_seal(graph)&&geo_eval_source(graph,source_ref(),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
        geo_eval_describe(graph,source_ref(),&d)==GEO_SOURCE_OK&&value.as.position.coordinate==37&&d.context.axis==2&&f.evaluates==1&&f.describes==1,
        "context-sealed-value-and-metadata-memoize-together");geo_eval_destroy(graph);return 0;
}
static int rejection_case(void)
{
    ContextFixture f;GeoEvalContext *graph=fixture(&f);CHECK(graph,"context-rejection-fixture");
    GeoSourceValue value,before;memset(&value,0x6a,sizeof value);memcpy(&before,&value,sizeof value);
    f.value.as.position.context.axis=3;
    CHECK(geo_eval_source(graph,source_ref(),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_INVALID&&!memcmp(&before,&value,sizeof value),
        "context-rejects-invalid-derived-axis");
    GeoSourceDescriptor d;CHECK(geo_eval_describe(graph,source_ref(),&d)==GEO_SOURCE_OK&&d.context_from_value&&d.context.axis==-1,
        "context-invalid-value-does-not-finalize-metadata");
    f.value.as.position.context.axis=-1;
    CHECK(geo_eval_source(graph,source_ref(),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_INVALID&&!memcmp(&before,&value,sizeof value),
        "context-rejects-unresolved-derived-axis");
    f.value.as.position.context=(GeoSourceContext){false,0,0};
    CHECK(geo_eval_source(graph,source_ref(),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&
        geo_eval_describe(graph,source_ref(),&d)==GEO_SOURCE_OK&&!d.context_from_value&&!d.context.has_placement&&d.context.axis==0&&f.evaluates==3,
        "context-retry-resolves-global-axis");geo_eval_destroy(graph);return 0;
}
static int strict_case(void)
{
    ContextFixture f;GeoEvalContext *graph=fixture(&f);CHECK(graph,"context-strict-fixture");
    f.descriptor.context_from_value=false;f.descriptor.context=(GeoSourceContext){true,1,0};
    GeoSourceValue value;
    CHECK(geo_eval_source(graph,source_ref(),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_INVALID,"context-strict-provider-still-rejects-mismatch");
    f.value.as.position.context=f.descriptor.context;
    CHECK(geo_eval_source(graph,source_ref(),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK,"context-strict-provider-accepts-exact-match");
    geo_eval_destroy(graph);return 0;
}
static int kind_case(void)
{
    ContextFixture f;GeoEvalContext *graph=fixture(&f);CHECK(graph,"context-kind-fixture");
    f.descriptor.kind=GEO_SOURCE_QUANTITY;f.value.kind=GEO_SOURCE_QUANTITY;f.value.as.quantity=(GeoQuantity){1,1,GEO_UNIT_LENGTH};
    GeoSourceValue value;GeoSourceDescriptor d;
    CHECK(geo_eval_describe(graph,source_ref(),&d)==GEO_SOURCE_INVALID&&f.evaluates==0,"context-flag-is-axis-only");
    CHECK(geo_eval_source(graph,source_ref(),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_INVALID&&f.evaluates==0,"context-invalid-kind-never-evaluates");
    geo_eval_destroy(graph);
    graph=fixture(&f);CHECK(graph,"context-kind-mismatch-fixture");f.value.kind=GEO_SOURCE_QUANTITY;
    CHECK(geo_eval_source(graph,source_ref(),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_INVALID,"context-typed-kind-must-still-match");
    CHECK(geo_eval_describe(graph,source_ref(),&d)==GEO_SOURCE_OK&&d.context_from_value,"context-kind-failure-preserves-metadata");
    geo_eval_destroy(graph);return 0;
}
static int failed_case(void)
{
    ContextFixture f;GeoEvalContext *graph=fixture(&f);CHECK(graph,"context-failed-fixture");f.fails=true;
    GeoSourceValue value,before;memset(&value,0x4b,sizeof value);memcpy(&before,&value,sizeof value);
    CHECK(geo_eval_source(graph,source_ref(),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_FAILED&&!memcmp(&before,&value,sizeof value),
        "context-failed-provider-does-not-publish");
    GeoSourceDescriptor d;CHECK(geo_eval_describe(graph,source_ref(),&d)==GEO_SOURCE_OK&&d.context_from_value&&d.context.axis==-1,
        "context-failed-provider-preserves-unresolved-metadata");
    f.fails=false;
    CHECK(geo_eval_source(graph,source_ref(),GEO_DEPENDENCY_VALUE_REQUIRED,&value)==GEO_SOURCE_OK&&f.evaluates==2,"context-failed-provider-can-retry");
    CHECK(geo_eval_reset(graph)&&geo_eval_node_count(graph)==0&&geo_eval_provider_count(graph)==0,"context-reset-requires-fresh-provider");
    geo_eval_destroy(graph);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"metadata"))return metadata_case();
    if(!strcmp(argv[1],"rejection"))return rejection_case();
    if(!strcmp(argv[1],"strict"))return strict_case();
    if(!strcmp(argv[1],"kind"))return kind_case();
    if(!strcmp(argv[1],"failed"))return failed_case();return 2;
}
