/* Extend the existing real public-API fixture; its original cases stay intact. */
#define main geo261_grid_original_main
#include "geo261_grid_sources_harness.c"
#undef main
#include "grid_definition_codec.h"
#ifndef GEO261_GRID_AUTHORITY_CONTROL
#define GEO261_GRID_AUTHORITY_CONTROL 0
#endif
static const char *authority_case;
static unsigned authority_changes;
static unsigned char authority_bytes[14][WOOD_GRID_CODEC_MAX_BYTES];
static void authority_u64(unsigned char *bytes,size_t offset,uint64_t value)
{for(int i=0;i<8;++i)bytes[offset+(size_t)i]=(unsigned char)(value>>(56-8*i));}
static bool authority_is(const char *name){return !strcmp(authority_case,name);}
/* Only the grid provider is compiled with this function replacing
 * geo_eval_source. The real engine still owns evaluation, edges and memoization;
 * the control changes the value returned to a consumer, never its raw store. */
GeoSourceStatus geo261_grid_authority_source(GeoEvalContext *graph,GeoSourceRef ref,
    GeoDependencyKind relation,GeoSourceValue *out)
{
    GeoSourceStatus status=geo_eval_source(graph,ref,relation,out);
    if(status!=GEO_SOURCE_OK)return status;
    if(GEO261_GRID_AUTHORITY_CONTROL&&authority_is("parameter-value")&&ref.provider==GS_PARAMETER&&out->kind==GEO_SOURCE_QUANTITY){
        out->as.quantity.num+=100; ++authority_changes;return status;
    }
    WoodGridSourceKind kind;uint32_t id;
    if(ref.provider!=GS_GRID||!wood_grid_source_decode(&ref,&kind,&id))return status;
    if(GEO261_GRID_AUTHORITY_CONTROL&&id==5&&out->kind==GEO_SOURCE_QUANTITY&&
        ((authority_is("panel-value")&&kind==WOOD_GRID_SOURCE_PANEL)||(authority_is("gap-value")&&kind==WOOD_GRID_SOURCE_GAP))){
        out->as.quantity.num+=authority_is("panel-value")?50:10;++authority_changes;return status;
    }
    if(out->kind!=GEO_SOURCE_DEFINITION)return status;
    bool corrupt=authority_is("invalid-definition")&&kind==WOOD_GRID_SOURCE_APPLICATION_DEFINITION&&id==3;
    bool stable=authority_is("rule-stability")&&kind==WOOD_GRID_SOURCE_RULE_DEFINITION&&id==1;
    bool mutate=GEO261_GRID_AUTHORITY_CONTROL&&(
        (authority_is("system-definition")&&kind==WOOD_GRID_SOURCE_SYSTEM_DEFINITION&&id==1)||
        (authority_is("binding-definition")&&kind==WOOD_GRID_SOURCE_BINDING_DEFINITION&&id==2)||
        (authority_is("application-definition")&&kind==WOOD_GRID_SOURCE_APPLICATION_DEFINITION&&id==5)||
        (authority_is("rule-definition")&&kind==WOOD_GRID_SOURCE_RULE_DEFINITION&&id==1)||
        (authority_is("system-value")&&kind==WOOD_GRID_SOURCE_SYSTEM&&id==1)||
        (authority_is("binding-value")&&kind==WOOD_GRID_SOURCE_BINDING&&id==2)||
        (authority_is("application-value")&&kind==WOOD_GRID_SOURCE_APPLICATION&&id==3)||
        (authority_is("world-policy")&&kind==WOOD_GRID_SOURCE_APPLICATION_DEFINITION&&id==3)||
        (authority_is("rule-policy")&&kind==WOOD_GRID_SOURCE_RULE_DEFINITION&&id==1));
    if(!corrupt&&!mutate&&!stable)return status;
    unsigned char *bytes=authority_bytes[kind];size_t size=out->as.definition.content_size;
    if(size>WOOD_GRID_CODEC_MAX_BYTES)return GEO_SOURCE_INVALID;
    memcpy(bytes,out->as.definition.content,size);
    if(corrupt)authority_u64(bytes,24,2); /* noncanonical boolean */
    else if(authority_is("system-definition")){
        /* id, byte-count + seven-byte name, main; axis source/count; start ref;
         * then step ref. Remove that reference and author a literal step 200. */
        size_t step=8+8+7+8+16+40;
        for(size_t i=0;i<4;++i)authority_u64(bytes,step+i*8,0);
        authority_u64(bytes,step+32,200);
    }else if(authority_is("binding-definition"))authority_u64(bytes,32,1);
    else if(authority_is("application-definition"))authority_u64(bytes,19*8+8+16+4*40+32,20);
    else if(authority_is("rule-definition")||stable)authority_u64(bytes,48,2);
    else if(authority_is("world-policy"))authority_u64(bytes,8,99);
    else if(authority_is("rule-policy"))authority_u64(bytes,32,1);
    else if(authority_is("system-value")){
        GeoGridSystem system;int main;
        if(!wood_grid_decode_system_value(&out->as.definition,id,&system,&main))return GEO_SOURCE_INVALID;
        system.axis[0].step=200;
        if(!wood_grid_encode_system_value(&system,main,bytes,WOOD_GRID_CODEC_MAX_BYTES,&size))return GEO_SOURCE_INVALID;
    }else{
        WoodGridApplication application;
        if(!wood_grid_decode_application_value(&out->as.definition,id,&application))return GEO_SOURCE_INVALID;
        application.lattice_base[0]+=10;
        if(!wood_grid_encode_application_value(&application,bytes,WOOD_GRID_CODEC_MAX_BYTES,&size))return GEO_SOURCE_INVALID;
    }
    out->as.definition.content=bytes;out->as.definition.content_size=size;++authority_changes;return status;
}
static int authority_line_case(void)
{
    Fixture *f=fixture(100);CHECK(f&&attach(f),"authority-line-fixture");
    GeoGridBinding before=*geo_grid_bindings_find(f->store,2);
    GeoCoord value=777;char error[1024]="";
    bool ok=wood_grid_sources_line(f->sources,3,9,0,2,true,false,0,&value,NULL,error,sizeof error);
    CHECK(ok&&value==210,"grid-authority-line-return");
    const GeoGridSystem *system=geo_grid_systems_find(f->store,1);
    CHECK(system->axis[0].parameters[1].set&&system->axis[0].parameters[1].parameter_id==90&&
        !memcmp(&before,geo_grid_bindings_find(f->store,2),sizeof before)&&f->state.items[0].placement_id==9,
        "grid-authority-preserves-authoring");
    dispose(f,false);return 0;
}
static int authority_application_case(void)
{
    Fixture *f=fixture(100);CHECK(f&&attach(f),"authority-application-fixture");
    GeoCoord value;char error[1024]="";
    /* D10a, k=1: 10+(50+10)+50+5 = 125. */
    CHECK(wood_grid_sources_line(f->sources,5,9,0,1,false,false,0,&value,NULL,error,sizeof error)&&value==125,
        "grid-authority-application-definition-return");
    CHECK(f->state.items[2].axis[0].anchor==10&&f->state.items[2].axis[0].body==50,"grid-authority-only-publishes-bound-cache");
    dispose(f,true);return 0;
}
static int authority_rule_case(void)
{
    Fixture *f=fixture(100);CHECK(f&&attach(f),"authority-rule-fixture");
    GeoGridRuleLineRef rule={3,1,7,{1,-1},0,0};GeoCoord value;GeoRect2 scope;char error[1024]="";
    CHECK(wood_grid_sources_rule_line(f->sources,&rule,9,&value,&scope,error,sizeof error)&&value==135&&rect(scope,110,-80,210,20),
        "grid-authority-rule-definition-return");
    CHECK(geo_grid_systems_find(f->store,1)->rules[0].divisions[0]==4,"grid-authority-rule-authoring-unchanged");
    dispose(f,false);return 0;
}
static int authority_world_case(void)
{
    Fixture *f=fixture(100);CHECK(f,"authority-world-fixture");f->state.count=1;
    CHECK(attach(f),"authority-world-attach");char error[1024]="";
    CHECK(wood_grid_world_valid(&f->context,error,sizeof error),"grid-authority-world-policy-definition");
    CHECK(f->state.items[0].placement_id==9,"grid-authority-world-policy-keeps-raw");dispose(f,false);return 0;
}
static int authority_rule_policy_case(void)
{
    Fixture *f=fixture(100);CHECK(f,"authority-rule-policy-fixture");f->state.count=2;
    f->state.items[1].lattice_cell_index[0]=2;
    GeoGridSystem system=*geo_grid_systems_find(f->store,1);system.rules[0].all_cells=false;
    CHECK(geo_grid_systems_put(f->store,&system)&&attach(f),"authority-rule-policy-attach");
    char error[1024]="";
    CHECK(wood_grid_rules_world_valid(&f->context,error,sizeof error),"grid-authority-rule-policy-definition");
    CHECK(!geo_grid_systems_find(f->store,1)->rules[0].all_cells&&f->host_calls==0&&f->vertex_calls==0&&f->coordinate_calls==0,
        "grid-authority-rule-policy-is-definition-only");dispose(f,false);return 0;
}
static int authority_invalid_case(void)
{
    Fixture *f=fixture(100);CHECK(f&&attach(f),"authority-invalid-fixture");
    WoodGridState before;memcpy(&before,&f->state,sizeof before);GeoCoord value=777;size_t total=888;char error[1024]="";
    CHECK(!wood_grid_sources_line(f->sources,3,9,0,2,true,false,0,&value,&total,error,sizeof error)&&authority_changes&&
        value==777&&total==888&&!memcmp(&before,&f->state,sizeof before),"grid-authority-rejects-invalid-definition-atomically");
    dispose(f,true);return 0;
}
static int authority_multi_case(void)
{
    Fixture *f=fixture(100);CHECK(f,"authority-multi-fixture");
    f->state.items[2].axis[1]=f->state.items[2].axis[0];
    f->engineering.bindings[1]=f->engineering.bindings[0];f->engineering.bindings[1].target.axis=1;
    f->engineering.bindings[1].source.parameter.field_id=1;f->engineering.binding_count=2;
    CHECK(attach(f),"authority-multi-attach");char error[1024]="";
    CHECK(wood_grid_sources_application(f->sources,5,error,sizeof error)&&f->state.items[2].axis[0].body==50&&f->state.items[2].axis[1].body==100,
        "grid-authority-keeps-both-bound-dimensions");
    /* D10a, k=1 on the second axis: 10+(100+10)+100+5 = 225. */
    GeoCoord value;CHECK(wood_grid_sources_line(f->sources,5,9,1,1,false,false,0,&value,NULL,error,sizeof error)&&value==225,
        "grid-authority-second-axis-line");
    unsigned calls=f->coordinate_calls+f->host_calls+f->vertex_calls;
    CHECK(geo_eval_seal(f->graph)&&wood_grid_sources_line(f->sources,5,9,1,1,false,false,0,&value,NULL,error,sizeof error)&&value==225&&
        calls==f->coordinate_calls+f->host_calls+f->vertex_calls,"grid-authority-memoized-result");
    dispose(f,false);return 0;
}
static int authority_plain_quantities_case(void)
{
    Fixture *f=fixture(100);CHECK(f,"authority-plain-fixture");
    f->engineering.binding_count=0;f->state.items[2].axis[0].body=50;
    f->state.items[2].axis[1]=f->state.items[2].axis[0];
    CHECK(attach(f),"authority-plain-attach");char error[1024]="";GeoCoord value;
    /* D10a, k=1: 10+(50+10)+50+5 = 125. */
    CHECK(wood_grid_sources_line(f->sources,5,9,0,1,false,false,0,&value,NULL,error,sizeof error)&&value==125,
        "grid-authority-preserves-unbound-returned-quantities");
    CHECK(f->state.items[2].axis[0].body==50&&f->state.items[2].axis[0].gap==10&&f->state.items[2].axis[1].body==50,
        "grid-authority-unbound-raw-authoring-unchanged");dispose(f,false);return 0;
}
static int authority_rule_stability_case(void)
{
    Fixture *f=fixture(100);CHECK(f&&attach(f),"authority-rule-stability-fixture");
    GeoGridRuleLineRef rule={3,1,7,{1,-1},0,0};GeoCoord value;char error[1024]="";
    CHECK(wood_grid_sources_rule_line(f->sources,&rule,9,&value,NULL,error,sizeof error)&&value==160&&authority_changes,
        "grid-authority-rule-stability-first-value");
    CHECK(wood_grid_systems_rebuild(&f->context,error,sizeof error),"grid-authority-rule-stability-reinstall-system");
    rule.inner_index=1;value=777;
    CHECK(!wood_grid_sources_rule_line(f->sources,&rule,9,&value,NULL,error,sizeof error)&&value==777&&strstr(error,"INDEX_RANGE"),
        "grid-authority-memoized-rule-keeps-returned-policy");
    CHECK(geo_grid_systems_find(f->store,1)->rules[0].divisions[0]==4,"grid-authority-rule-stability-keeps-raw");
    dispose(f,true);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;authority_case=argv[1];
    if(authority_is("application-definition"))return authority_application_case();
    if(authority_is("rule-definition"))return authority_rule_case();
    if(authority_is("world-policy"))return authority_world_case();
    if(authority_is("rule-policy"))return authority_rule_policy_case();
    if(authority_is("invalid-definition"))return authority_invalid_case();
    if(authority_is("multiple-and-memo"))return authority_multi_case();
    if(authority_is("panel-value")||authority_is("gap-value"))return authority_plain_quantities_case();
    if(authority_is("rule-stability"))return authority_rule_stability_case();
    return authority_line_case();
}
