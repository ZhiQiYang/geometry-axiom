/* Substitute only returned public source values after real K evaluation.
 * The candidate and K memo retain their original authored data. */
#define main legacy_finish_source_main
#include "geo261_finish_sources_harness.c"
#undef main
#undef CHECK
#define CHECK(c,label) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",label);return 1;}}while(0)

enum { FA_NONE,FA_CONTENT,FA_STATUS,FA_SCHEMA,FA_MALFORMED,FA_QUANTITY,FA_KIND,FA_VERSION_QUANTITY,FA_VERSION_STATUS,FA_VERSION_DEFINITION };
enum { FA_VERSION_PROVIDER=13 };
static int authority_mode;
static WoodFinishSourceKind authority_kind;
static uint32_t authority_id;
static unsigned authority_hits;
static char authority_content[8192];
static GeoQuantity authority_quantity;
static GeoVersionSources *authority_versions;
static unsigned char authority_version_content[GEO_VERSION_DEFINITION_MAX];
static size_t authority_version_size;

GeoSourceStatus geo261_finish_get(GeoEvalContext *graph,GeoSourceRef ref,GeoDependencyKind relation,GeoSourceValue *out)
{
    GeoSourceStatus status=geo_eval_source(graph,ref,relation,out);WoodFinishSourceKind kind;uint32_t id;
    if(status!=GEO_SOURCE_OK)return status;
    bool selected=ref.provider==FS_SOURCE&&wood_finish_source_decode(&ref,&kind,&id)&&kind==authority_kind&&id==authority_id;
    if(authority_mode==FA_QUANTITY&&ref.provider==FS_PARAMETER&&ref.key_size==2*sizeof(uint32_t)){
        uint32_t key[2];memcpy(key,ref.key,sizeof key);selected=key[0]==90&&key[1]==authority_id;}
    if(ref.provider==FA_VERSION_PROVIDER){GeoVersionSourceKind version_kind;GeoVersionIdentity identity;uint32_t field;
        selected=geo_version_source_decode(&ref,&version_kind,&identity,&field)&&
            ((authority_mode==FA_VERSION_DEFINITION&&version_kind==GEO_VERSION_SOURCE_DEFINITION)||
             ((authority_mode==FA_VERSION_QUANTITY||authority_mode==FA_VERSION_STATUS)&&version_kind==GEO_VERSION_SOURCE_FIELD&&field==authority_id));}
    if(!selected)return status;++authority_hits;
    if(authority_mode==FA_STATUS||authority_mode==FA_VERSION_STATUS)return GEO_SOURCE_FAILED;
    if(authority_mode==FA_SCHEMA)out->as.definition.schema="wrong.finish.schema/1";
    else if(authority_mode==FA_KIND)out->kind=GEO_SOURCE_QUANTITY;
    else if(authority_mode==FA_MALFORMED){out->as.definition.content="{";out->as.definition.content_size=1;}
    else if(authority_mode==FA_CONTENT){out->as.definition.content=authority_content;out->as.definition.content_size=strlen(authority_content);}
    else if(authority_mode==FA_QUANTITY||authority_mode==FA_VERSION_QUANTITY)out->as.quantity=authority_quantity;
    else if(authority_mode==FA_VERSION_DEFINITION){out->as.definition.content=authority_version_content;out->as.definition.content_size=authority_version_size;}
    return status;
}
static void reset_authority(int mode,WoodFinishSourceKind kind,uint32_t id)
{authority_mode=mode;authority_kind=kind;authority_id=id;authority_hits=0;authority_content[0]=0;}
static bool canonical_authority(const char *text)
{GeoJson json={0};if(!geo_json_parse(&json,text))return false;bool ok=geo_json_canonical(&json,0,authority_content,sizeof authority_content);geo_json_free(&json);return ok;}
static bool attach_versions(Fixture *f)
{
    f->graph=geo_eval_create(261,73);if(!f->graph)return false;
    GeoSourceProvider provider={FS_NAMED,"core.named-value","finish-test-named/1",f,named_describe,named_evaluate};
    if(!geo_eval_register(f->graph,&provider))return false;
    authority_versions=geo_version_sources_register(f->graph,f->versions,FA_VERSION_PROVIDER);
    f->parameter_sources=geo_parameter_sources_register(f->graph,f->parameters,FS_PARAMETER,"core.parameter.field","finish-test-parameter/1");
    f->engineering_sources=wood_engineering_sources_register(f->graph,&f->context.finish.engineering,
        (WoodEngineeringSourceTokens){FS_DIMENSION,FS_BINDING,FS_DEFINITION,FS_NAMED,FS_PARAMETER,FA_VERSION_PROVIDER});
    if(!authority_versions||!f->parameter_sources||!f->engineering_sources)return false;wood_engineering_sources_bind(f->engineering_sources,&f->context.finish.engineering);
    f->sources=wood_finish_sources_create(f->graph,(WoodFinishSourceTokens){FS_SOURCE,FS_PARAMETER},&f->context);
    return f->sources&&wood_finish_sources_bind(f->sources,&f->context);
}
static void dispose_versions(Fixture *f)
{geo_eval_destroy(f->graph);f->graph=NULL;geo_version_sources_destroy(authority_versions);authority_versions=NULL;dispose(f,false);}
static size_t version_field_index(Fixture *f,uint32_t field)
{
    for(size_t i=0;i<geo_eval_node_count(f->graph);++i){GeoSourceNodeView node;GeoVersionSourceKind kind;GeoVersionIdentity identity;uint32_t found;
        if(geo_eval_node_at(f->graph,i,&node)&&node.source.provider==FA_VERSION_PROVIDER&&geo_version_source_decode(&node.source,&kind,&identity,&found)&&kind==GEO_VERSION_SOURCE_FIELD&&found==field)return i;}
    return SIZE_MAX;
}
static bool extra_definitions(Fixture *f)
{
    f->state.items[1]=f->state.items[0];f->state.items[1].id=2;f->state.items[1].frame.origin.x=50;f->state.items[1].obstacle_count=0;f->state.count=2;
    if(!parse(f,"{\"id\":\"other\",\"version\":1,\"kind\":\"panel\",\"name\":\"other\",\"width\":40,\"length\":60,\"thickness\":\"11.000\"}",0,NULL)||
       !parse(f,"{\"id\":2,\"finishSurfaceId\":2,\"panel\":{\"id\":\"other\",\"version\":1},\"lengthAlong\":\"u\",\"origin\":[13,27],\"gap\":7,\"pattern\":\"stagger\",\"stagger\":{\"axis\":\"v\",\"value\":9},\"threshold\":{\"parameterId\":90,\"fieldId\":3}}",1,&f->state.fills[1])||
       !parse(f,"{\"id\":11,\"fillId\":2,\"h\":12}",2,&f->state.hosts[1]))return false;
    f->state.fill_count=f->state.host_count=2;return true;
}
static int surface_authority(void)
{
    reset_authority(FA_CONTENT,WOOD_FINISH_SOURCE_DEFINITION,1);Fixture *f=fixture();CHECK(f&&attach(f),"surface-setup");
    strcpy(authority_content,"id=1;boundary=8;side=-1;origin=10,0,0;U=1,0,0;V=0,1,0;N=0,0,1;name=72657475726e6564;obstacles=0");
    FinishSurface raw=f->state.items[0];WoodDerivedValue value;char error[512];
    CHECK(wood_fs_rebuild(&f->context.finish,error,sizeof error)&&wood_finish_sources_read_derived(f->sources,10,&value),"surface-evaluates");
    CHECK(authority_hits&&value.frame.origin.x==10&&value.frame.origin.z==-9&&value.frame.axis_v.y==-1&&value.frame.normal.z==-1&&
          value.component_count==1&&value.components[0].hole_count==0&&f->box_calls==0,"surface-definition-controls-side-frame-obstacles");
    GeoCoord u0,v0,u1,v1;GeoLoop2View loop={value.components[0].outline.v,value.components[0].outline.count};geo_loop_bbox(&loop,&u0,&v0,&u1,&v1);
    CHECK(u0==0&&v0==-100&&u1==100&&v1==0,"surface-definition-controls-mirrored-region");
    CHECK(!memcmp(&raw,&f->state.items[0],sizeof raw)&&f->writes==0,"surface-authoring-preserved");
    FinishSurface returned;CHECK(wood_finish_sources_surface_definition(f->sources,1,&returned)&&returned.side==-1&&!strcmp(returned.name,"returned"),"surface-helper-returns-definition-only");
    CHECK(edge(f,WOOD_FINISH_SOURCE_CHECK,1,WOOD_FINISH_SOURCE_DEFINITION,1,GEO_DEPENDENCY_DEFINITION_REQUIRED),"surface-definition-required-edge");
    dispose(f,false);return 0;
}
static int surface_boundary_authority(void)
{
    reset_authority(FA_CONTENT,WOOD_FINISH_SOURCE_DEFINITION,1);Fixture *f=fixture();CHECK(f&&attach(f),"surface-boundary-setup");
    strcpy(authority_content,"id=1;boundary=99;side=1;origin=0,0,0;U=1,0,0;V=0,1,0;N=0,0,1;name=66696e697368;obstacles=1;1:20");
    char error[512];CHECK(!wood_fs_rebuild(&f->context.finish,error,sizeof error)&&authority_hits&&!strcmp(error,"I52: finish surface 1 references missing boundary 99")&&f->box_calls==0,"surface-definition-controls-boundary-policy");
    CHECK(f->state.items[0].boundary_id==8,"surface-boundary-authoring-preserved");dispose(f,true);return 0;
}
static int fill_authority(void)
{
    reset_authority(FA_CONTENT,WOOD_FINISH_SOURCE_FILL_DEFINITION,1);Fixture *f=fixture();CHECK(f&&extra_definitions(f)&&attach(f),"fill-setup");
    CHECK(canonical_authority("{\"id\":1,\"finishSurfaceId\":2,\"panel\":{\"id\":\"other\",\"version\":1},\"lengthAlong\":\"u\",\"origin\":[13,27],\"gap\":7,\"pattern\":\"stagger\",\"stagger\":{\"axis\":\"v\",\"value\":9},\"threshold\":{\"parameterId\":90,\"fieldId\":4}}"),"fill-canonical");
    PanelFill raw=f->state.fills[0];WoodFinishLayout layout={0};bool ok=wood_pf_build(&f->context.finish,&f->state.fills[0],&layout);
    CHECK(ok&&authority_hits&&layout.finish->id==2&&layout.frame.origin.x==50&&layout.layout.size[0]==60&&layout.layout.size[1]==40&&
          layout.t==11&&layout.layout.gap==7&&layout.layout.stagger==9,"fill-definition-controls-fields-and-axis");
    bool origin=false,stagger=false;for(size_t i=0;i<layout.layout.count;++i){const WoodPanelTile *tile=&layout.layout.tiles[i];
        if(tile->i==0&&tile->j==0)origin=tile->body[0]==13&&tile->body[1]==27;
        if(tile->i==1&&tile->j==0)stagger=tile->body[0]==80&&tile->body[1]==36;}
    CHECK(origin&&stagger,"fill-definition-controls-origin-and-stagger-axis");
    CHECK(!memcmp(&raw,&f->state.fills[0],sizeof raw),"fill-authoring-preserved");
    PanelFill returned;CHECK(wood_finish_sources_fill_definition(f->sources,1,&returned)&&returned.finish_id==2&&returned.origin[0]==13&&returned.threshold.field_id==4,"fill-helper-returns-definition-only");
    CHECK(edge_indices(f->graph,source_index(f->graph,WOOD_FINISH_SOURCE_THRESHOLD,1),parameter_index(f,4),GEO_DEPENDENCY_VALUE_REQUIRED),"fill-definition-controls-threshold-reference");
    CHECK(edge(f,WOOD_FINISH_SOURCE_FILL_FRAME,1,WOOD_FINISH_SOURCE_FILL_DEFINITION,1,GEO_DEPENDENCY_DEFINITION_REQUIRED),"fill-definition-required-edge");
    wood_pf_free(&layout);dispose(f,false);return 0;
}
static int fill_policy_authority(void)
{
    reset_authority(FA_CONTENT,WOOD_FINISH_SOURCE_FILL_DEFINITION,1);Fixture *f=fixture();CHECK(f&&attach(f),"fill-policy-setup");
    CHECK(canonical_authority("{\"id\":1,\"finishSurfaceId\":1,\"panel\":{\"id\":\"board\",\"version\":1},\"lengthAlong\":\"v\",\"origin\":[0,0],\"gap\":3,\"pattern\":\"stagger\",\"stagger\":{\"axis\":\"u\",\"value\":103},\"threshold\":{\"parameterId\":90,\"fieldId\":3}}"),"fill-policy-canonical");
    WoodFinishLayout layout={0};CHECK(!wood_pf_values(&f->context.finish,&f->state.fills[0],&layout)&&authority_hits&&
          !strcmp(f->error,"I52: stagger is zero or a whole pitch; odd and even rows coincide"),"fill-definition-controls-stagger-policy");
    dispose(f,false);return 0;
}
static int derived_authority(void)
{
    reset_authority(FA_CONTENT,WOOD_FINISH_SOURCE_DERIVED_DEFINITION,10);Fixture *f=fixture();CHECK(f&&extra_definitions(f)&&attach(f),"derived-setup");
    CHECK(canonical_authority("{\"id\":10,\"fillId\":2,\"h\":12}"),"derived-canonical");DerivedPlacement raw=f->state.hosts[0];WoodDerivedValue value;
    CHECK(wood_finish_sources_read_derived(f->sources,10,&value)&&authority_hits&&value.id==10&&value.derived_fill_id==2&&value.derived_h==12&&
          value.frame.origin.x==50&&value.frame.origin.z==11&&value.components[0].hole_count==0&&f->named_calls==0,"derived-definition-controls-fill-height-and-policy");
    CHECK(!memcmp(&raw,&f->state.hosts[0],sizeof raw)&&f->writes==0,"derived-authoring-preserved");
    CHECK(wood_dp_rebuild(&f->context)&&f->writes==2&&f->placements[0].derived_fill_id==2&&f->placements[0].derived_h==12,"derived-successful-cache-write-is-explicit");
    CHECK(edge(f,WOOD_FINISH_SOURCE_DERIVED_REGION,10,WOOD_FINISH_SOURCE_DERIVED_DEFINITION,10,GEO_DEPENDENCY_DEFINITION_REQUIRED),"derived-definition-required-edge");
    dispose(f,true);return 0;
}
static int parameter_authority(bool threshold)
{
    reset_authority(FA_QUANTITY,0,threshold?3:1);authority_quantity=(GeoQuantity){threshold?-1:17,1,GEO_UNIT_LENGTH};
    Fixture *f=fixture();CHECK(f&&attach(f),"parameter-return-setup");WoodFinishLayout layout={0};bool ok=wood_pf_values(&f->context.finish,&f->state.fills[0],&layout);
    if(threshold)CHECK(!ok&&authority_hits&&!strcmp(f->error,"D44: panel-fill threshold must be a positive dimension"),"returned-threshold-controls-policy");
    else CHECK(ok&&authority_hits&&layout.layout.gap==17,"returned-gap-controls-layout");
    GeoQuantity raw;GeoParameterError error;CHECK(geo_parameters_dimension_value(f->parameters,(GeoParameterRef){true,90,authority_id},&raw,&error)&&raw.num==(threshold?8:3),"parameter-raw-value-preserved");
    dispose(f,false);return 0;
}
static int panel_definition_authority(bool schema)
{
    reset_authority(schema?FA_SCHEMA:FA_CONTENT,WOOD_FINISH_SOURCE_PANEL_DEFINITION,1);Fixture *f=fixture();CHECK(f&&attach_versions(f),"panel-policy-setup");
    CHECK(canonical_authority("{\"id\":\"board\",\"version\":1,\"kind\":\"timber\",\"name\":\"returned timber\",\"A\":27,\"B\":33}"),"panel-policy-canonical");
    WoodFinishLayout layout={0};bool ok=wood_pf_values(&f->context.finish,&f->state.fills[0],&layout);
    CHECK(!ok&&authority_hits&&(schema?!strcmp(f->error,"I52/I56: invalid canonical finish definition 16:1"):
        !strcmp(f->error,"I52: panel-fill 1 needs an existing fixed panel material version")),"returned-panel-definition-controls-material-policy");
    CHECK(f->engineering.materials[0].kind==0&&f->writes==0,"panel-raw-material-preserved");dispose_versions(f);return 0;
}
static int version_field_authority(uint32_t field,bool edges)
{
    reset_authority(edges?FA_NONE:FA_VERSION_QUANTITY,0,field);authority_quantity=(GeoQuantity){field==ENG_LENGTH?33:field==ENG_WIDTH?41:15,1,GEO_UNIT_LENGTH};
    Fixture *f=fixture();CHECK(f&&attach_versions(f),"version-field-setup");WoodFinishLayout layout={0};
    CHECK(wood_pf_values(&f->context.finish,&f->state.fills[0],&layout),"version-field-evaluates");
    if(!edges)CHECK(authority_hits&&layout.layout.size[1]==(field==ENG_LENGTH?33:100)&&layout.layout.size[0]==(field==ENG_WIDTH?41:100)&&
        layout.t==(field==WOOD_ENG_VERSION_THICKNESS?15:9),"returned-k-field-controls-finish-quantity");
    const uint32_t fields[]={ENG_LENGTH,ENG_WIDTH,WOOD_ENG_VERSION_THICKNESS};
    for(size_t i=0;i<3;++i)CHECK(edge_indices(f->graph,source_index(f->graph,(WoodFinishSourceKind)(WOOD_FINISH_SOURCE_PANEL_LENGTH+i),1),version_field_index(f,fields[i]),GEO_DEPENDENCY_VALUE_REQUIRED),"finish-selected-k-field-edge");
    GeoSourceNodeView node;CHECK(geo_eval_node_at(f->graph,version_field_index(f,field),&node)&&node.value&&node.value->as.quantity.num==(field==WOOD_ENG_VERSION_THICKNESS?9:100),"version-field-k-memo-unchanged");
    dispose_versions(f);return 0;
}
static int version_field_failure(int failure)
{
    reset_authority(failure==3?FA_VERSION_STATUS:FA_VERSION_QUANTITY,0,WOOD_ENG_VERSION_THICKNESS);
    authority_quantity=(GeoQuantity){failure==0?0:15,failure==1?2:1,failure==2?GEO_UNIT_SCALAR:GEO_UNIT_LENGTH};
    Fixture *f=fixture_thickness(failure==4?"9.25":"9.000");CHECK(f&&attach_versions(f),"version-field-failure-setup");WoodFinishLayout layout={0};
    CHECK(!wood_pf_values(&f->context.finish,&f->state.fills[0],&layout)&&f->writes==0,"invalid-k-field-refused");
    if(failure==4)CHECK(authority_hits==0&&!strcmp(f->error,"I52: panel-fill thickness must be explicitly set positive integer mm in D1; no rounding"),"legacy-thickness-policy-precedes-k-field");
    else CHECK(authority_hits>0,"invalid-k-field-actually-returned");dispose_versions(f);return 0;
}
static int shared_version_definition_authority(void)
{
    reset_authority(FA_VERSION_DEFINITION,0,0);Fixture *f=fixture();CHECK(f&&attach_versions(f),"shared-definition-setup");
    CHECK(canonical_authority("{\"id\":\"board\",\"version\":1,\"kind\":\"panel\",\"name\":\"returned shared material\",\"width\":100,\"length\":100,\"thickness\":\"9.000\"}"),"shared-definition-canonical");
    GeoVersionView original;CHECK(wood_eng_version_view_direct(&f->context.finish.engineering,0,"board",1,&original),"shared-definition-original");
    GeoVersionView returned=original;char fingerprint[65];geo_sha256(authority_content,strlen(authority_content),fingerprint);
    returned.content=authority_content;returned.content_length=strlen(authority_content);returned.fingerprint=fingerprint;returned.fingerprint_length=64;
    authority_version_size=geo_version_definition_encode(&returned,authority_version_content,sizeof authority_version_content);CHECK(authority_version_size,"shared-definition-encoded");
    GeoSourceValue value;CHECK(get(f,WOOD_FINISH_SOURCE_PANEL_DEFINITION,1,&value)&&authority_hits&&value.kind==GEO_SOURCE_DEFINITION&&
        value.as.definition.content_size==strlen(authority_content)&&!memcmp(value.as.definition.content,authority_content,value.as.definition.content_size),"panel-definition-consumes-actual-shared-version-definition");
    CHECK(original.content_length!=strlen(authority_content)||memcmp(original.content,authority_content,original.content_length),"shared-version-store-unchanged");
    dispose_versions(f);return 0;
}
static bool definition_read(Fixture *f,WoodFinishSourceKind kind,void *out)
{return kind==WOOD_FINISH_SOURCE_DEFINITION?wood_finish_sources_surface_definition(f->sources,1,out):kind==WOOD_FINISH_SOURCE_FILL_DEFINITION?wood_finish_sources_fill_definition(f->sources,1,out):wood_finish_sources_derived_definition(f->sources,10,out);}
static int definition_failure(int mode,WoodFinishSourceKind kind,bool identity)
{
    reset_authority(mode,kind,kind==WOOD_FINISH_SOURCE_DERIVED_DEFINITION?10:1);Fixture *f=fixture();CHECK(f&&attach(f),"definition-failure-setup");
    if(identity){if(kind==WOOD_FINISH_SOURCE_DEFINITION)strcpy(authority_content,"id=2;boundary=8;side=1;origin=0,0,0;U=1,0,0;V=0,1,0;N=0,0,1;name=66696e697368;obstacles=0");
        else CHECK(canonical_authority(kind==WOOD_FINISH_SOURCE_FILL_DEFINITION?
            "{\"id\":2,\"finishSurfaceId\":1,\"panel\":{\"id\":\"board\",\"version\":1},\"lengthAlong\":\"v\",\"origin\":[0,0],\"gap\":3,\"pattern\":\"straight\",\"threshold\":{\"parameterId\":90,\"fieldId\":3}}":"{\"id\":11,\"fillId\":1,\"h\":30}"),"identity-canonical");}
    union {FinishSurface surface;PanelFill fill;DerivedPlacement derived;} value,prior;memset(&value,0x4d,sizeof value);prior=value;
    bool ok=definition_read(f,kind,&value);
    CHECK(!ok&&authority_hits&&!memcmp(&value,&prior,sizeof value)&&f->boundary_calls==0&&f->box_calls==0&&f->parameter_calls==0&&f->reads==0&&f->writes==0,"invalid-definition-return-refused-with-output-unchanged");
    dispose(f,false);return 0;
}
static int complete_authority(bool malformed)
{
    reset_authority(malformed?FA_MALFORMED:FA_NONE,WOOD_FINISH_SOURCE_FILL_DEFINITION,2);Fixture *f=fixture();CHECK(f&&extra_definitions(f)&&attach(f),"complete-setup");
    if(malformed){CHECK(!wood_finish_sources_definitions(f->sources)&&authority_hits&&f->boundary_calls==0&&f->writes==0,"dormant-malformed-definition-refused");dispose(f,false);return 0;}
    CHECK(wood_finish_sources_definitions(f->sources),"complete-definitions");GeoSourceNodeView node;
    CHECK(source_index(f->graph,WOOD_FINISH_SOURCE_DEFINITION,2)!=SIZE_MAX&&source_index(f->graph,WOOD_FINISH_SOURCE_FILL_DEFINITION,2)!=SIZE_MAX&&
          source_index(f->graph,WOOD_FINISH_SOURCE_DERIVED_DEFINITION,11)!=SIZE_MAX,"dormant-definitions-completed");
    CHECK(source_index(f->graph,WOOD_FINISH_SOURCE_FILL_FRAME,2)==SIZE_MAX&&source_index(f->graph,WOOD_FINISH_SOURCE_DERIVED_FRAME,11)==SIZE_MAX&&
          f->boundary_calls==0&&f->box_calls==0&&f->parameter_calls==0&&f->reads==0&&f->writes==0,"definition-only-does-not-evaluate-values");
    CHECK(geo_eval_node_at(f->graph,source_index(f->graph,WOOD_FINISH_SOURCE_FILL_DEFINITION,2),&node)&&node.state==GEO_NODE_VALID&&node.value&&
          node.value->as.definition.content_size==strlen(f->state.fills[1].definition)&&!memcmp(node.value->as.definition.content,f->state.fills[1].definition,node.value->as.definition.content_size),"dormant-canonical-bytes-preserved");
    CHECK(geo_eval_seal(f->graph)&&wood_finish_sources_definitions(f->sources),"sealed-definition-reads");dispose(f,true);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;const char *name=argv[1];
    if(!strcmp(name,"surface"))return surface_authority();
    if(!strcmp(name,"surface-boundary"))return surface_boundary_authority();
    if(!strcmp(name,"fill"))return fill_authority();
    if(!strcmp(name,"fill-policy"))return fill_policy_authority();
    if(!strcmp(name,"derived"))return derived_authority();
    if(!strcmp(name,"gap"))return parameter_authority(false);
    if(!strcmp(name,"threshold"))return parameter_authority(true);
    if(!strcmp(name,"panel-policy"))return panel_definition_authority(false);
    if(!strcmp(name,"panel-schema"))return panel_definition_authority(true);
    if(!strcmp(name,"version-length"))return version_field_authority(ENG_LENGTH,false);
    if(!strcmp(name,"version-width"))return version_field_authority(ENG_WIDTH,false);
    if(!strcmp(name,"version-thickness"))return version_field_authority(WOOD_ENG_VERSION_THICKNESS,false);
    if(!strcmp(name,"version-edges"))return version_field_authority(WOOD_ENG_VERSION_THICKNESS,true);
    if(!strcmp(name,"shared-version"))return shared_version_definition_authority();
    if(!strcmp(name,"version-zero"))return version_field_failure(0);
    if(!strcmp(name,"version-fraction"))return version_field_failure(1);
    if(!strcmp(name,"version-unit"))return version_field_failure(2);
    if(!strcmp(name,"version-status"))return version_field_failure(3);
    if(!strcmp(name,"legacy-thickness"))return version_field_failure(4);
    if(!strcmp(name,"complete"))return complete_authority(false);
    if(!strcmp(name,"dormant-malformed"))return complete_authority(true);
    if(!strcmp(name,"parity")){reset_authority(FA_NONE,0,0);return graph_case()||diagnostic_case()||finish_case()||shared_case()||lifetime_case();}
    const char *dash=strchr(name,'-');if(!dash)return 2;
    WoodFinishSourceKind kind=!strcmp(dash+1,"surface")?WOOD_FINISH_SOURCE_DEFINITION:!strcmp(dash+1,"fill")?WOOD_FINISH_SOURCE_FILL_DEFINITION:!strcmp(dash+1,"derived")?WOOD_FINISH_SOURCE_DERIVED_DEFINITION:0;
    if(!kind)return 2;
    if(!strncmp(name,"status-",7))return definition_failure(FA_STATUS,kind,false);
    if(!strncmp(name,"schema-",7))return definition_failure(FA_SCHEMA,kind,false);
    if(!strncmp(name,"kind-",5))return definition_failure(FA_KIND,kind,false);
    if(!strncmp(name,"malformed-",10))return definition_failure(FA_MALFORMED,kind,false);
    if(!strncmp(name,"identity-",9))return definition_failure(FA_CONTENT,kind,true);
    return 2;
}
