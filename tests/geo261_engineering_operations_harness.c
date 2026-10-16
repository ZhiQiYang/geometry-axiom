/* Real W editing/replay policy with facts and writes tied to one candidate. */
#include "engineering_operations.h"
#include <stdio.h>
#include <string.h>

#define CHECK(value) do { if(!(value)){fprintf(stderr,"ASSERT:%s:%d\n",__func__,__LINE__);return 1;} } while(0)
#define NAMED(value,label) do { if(!(value)){fprintf(stderr,"ASSERT:%s\n",label);return 1;} } while(0)
typedef struct {
    WoodGridState grids;EngineeringState eng;WoodMember members[4];uint32_t pids[4];size_t count;
    WoodEngineeringOperations operations;char error[256],trace[128];size_t trace_count;
    bool missing_host,owned,fail_rebuild,fail_effective,fail_serial,write_saw_binding,write_bad;
    GeoCoord parameter_value;uint32_t parameter_id,field_id;size_t created_count;
} Fixture;
static void mark(Fixture *f,char value){if(f->trace_count+1<sizeof f->trace){f->trace[f->trace_count++]=value;f->trace[f->trace_count]=0;}}
static int member_index(Fixture *f,uint32_t id){for(size_t k=0;k<f->count;++k)if(f->members[k].id==id)return (int)k;return -1;}
static bool target(void *opaque,const EngTarget *t,WoodEngineeringTargetInfo *out)
{
    Fixture *f=opaque;memset(out,0,sizeof *out);
    if(t->kind){int k=member_index(f,t->id);if(k<0)return false;out->placement_id=f->pids[k];out->role=f->members[k].role;out->placed=f->members[k].placed;return true;}
    const WoodGridApplication *g=wood_grid_find(&f->grids,t->id);if(!g)return false;
    out->placement_id=g->placement_id;out->from_system=g->from_system||g->from_binding;out->is_subgrid=g->is_subgrid;
    out->panel_axis=g->axis[t->axis].source==GEO_GRID_SOURCE_BODY_GAP;return true;
}
static bool placement(void *opaque,uint32_t pid,bool *derived){Fixture *f=opaque;*derived=false;return !f->missing_host&&pid==10;}
static bool host(void *opaque,uint32_t pid,WoodGridHost *out)
{bool derived;if(!placement(opaque,pid,&derived))return false;memset(out,0,sizeof *out);out->id=pid;out->bounds_valid=true;out->bounds=(GeoRect2){0,0,4000,3000};return true;}
static bool owned(void *opaque,uint32_t id){(void)id;return ((Fixture *)opaque)->owned;}
static bool named(void *opaque,const char *name,GeoCoord *value){(void)opaque;if(strcmp(name,"width"))return false;*value=27;return true;}
static bool parameter(void *opaque,GeoParameterRef ref,GeoCoord *value,char *error,size_t cap)
{
    Fixture *f=opaque;mark(f,'Q');if(!ref.set||ref.parameter_id!=f->parameter_id||ref.field_id!=f->field_id){snprintf(error,cap,"parameter identity mismatch");return false;}
    *value=f->parameter_value;return true;
}
static bool rebuild_parameters(void *opaque,char *error,size_t cap)
{Fixture *f=opaque;mark(f,'P');if(f->fail_rebuild){snprintf(error,cap,"parameter rebuild rejected");return false;}return true;}
static bool effective(void *opaque,const EngBinding *b,GeoCoord *value,char *path,size_t cap)
{
    Fixture *f=opaque;mark(f,'E');if(f->fail_effective)return wood_eng_fail(&f->operations.grids.engineering,"effective rejected");
    return wood_eng_effective_direct(&f->operations.grids.engineering,b,value,path,cap);
}
static void write_dimension(void *opaque,const EngTarget *t,GeoCoord value)
{
    Fixture *f=opaque;mark(f,'W');f->write_saw_binding=wood_eng_binding(&f->operations.grids.engineering,t)!=NULL;
    if(t->kind){int k=member_index(f,t->id);if(k<0){f->write_bad=true;return;}if(t->field)f->members[k].size_b=value;else f->members[k].size_a=value;}
    else {WoodGridApplication *g=wood_grid_find_mut(&f->grids,t->id);if(!g){f->write_bad=true;return;}if(t->field)g->axis[t->axis].gap=value;else g->axis[t->axis].body=value;}
}
static bool serializable(void *opaque,char *error,size_t cap)
{Fixture *f=opaque;mark(f,'S');if(f->fail_serial){snprintf(error,cap,"serialization rejected");return false;}return true;}
static void member_created(void *opaque,size_t index)
{Fixture *f=opaque;mark(f,'C');++f->created_count;f->pids[index]=0;}
static void wire(Fixture *f)
{
    WoodEngineeringOperations *o=&f->operations;memset(o,0,sizeof *o);o->members=f->members;o->member_count=&f->count;o->member_capacity=4;
    o->user=f;o->rebuild_parameters=rebuild_parameters;o->member_created=member_created;
    o->grids.state=&f->grids;o->grids.user=f;o->grids.host=host;WoodEngineeringContext *w=&o->grids.engineering;
    w->state=&f->eng;w->user=f;w->error=f->error;w->error_capacity=sizeof f->error;w->placement=placement;w->target=target;
    w->named_value=named;w->parameter=parameter;w->member_owned=owned;w->write_dimension=write_dimension;w->serializable=serializable;
    w->sources=f;w->resolve_binding=effective;
}
static void init(Fixture *f){memset(f,0,sizeof *f);f->parameter_id=17;f->field_id=23;f->parameter_value=55;wire(f);}
static bool add_member(Fixture *f,uint32_t id,bool placed,WoodMemberRole role)
{size_t k=f->count;if(k==4||!wood_member_construct(id,0,27,33,true,role,9,&f->members[k]))return false;f->members[k].placed=placed;f->pids[k]=10;++f->count;return true;}
static void catalog(Fixture *f)
{
    EngMaterialVersion *wood=&f->eng.materials[f->eng.material_count++];strcpy(wood->ref.id,"wood");wood->ref.version=1;wood->kind=1;wood->a=27;wood->b=33;
    EngMethodVersion *m=&f->eng.methods[f->eng.method_count++];strcpy(m->ref.id,"method");m->ref.version=1;m->main_along=1;
    for(int r=0;r<3;++r)m->roles[r]=wood->ref;
    EngApplication *a=&f->eng.applications[f->eng.application_count++];strcpy(a->id,"app");a->placement_id=10;a->method=m->ref;
    a->anchor_kind[0]=a->anchor_kind[1]=1;
}
static bool operation(Fixture *f,const char *text)
{
    GeoJson j;char op[40];f->error[0]=0;
    if(!geo_json_parse(&j,text)||!geo_json_string(&j,geo_json_member(&j,0,"op"),op,sizeof op)){fprintf(stderr,"SETUP:invalid operation JSON\n");geo_json_free(&j);return false;}
    bool ok=wood_engineering_operation(&f->operations,&j,0,op);geo_json_free(&j);return ok;
}
static bool restore(Fixture *f,const char *text)
{
    GeoJson j;f->error[0]=0;if(!geo_json_parse(&j,text)){fprintf(stderr,"SETUP:invalid member JSON\n");geo_json_free(&j);return false;}
    bool ok=wood_engineering_restore_member(&f->operations,&j,0);geo_json_free(&j);return ok;
}
static bool bind_parameter(Fixture *f,uint32_t id,int field)
{EngTarget t={1,id,0,field};EngDimensionSource s={0};s.kind=ENG_PARAMETER;s.parameter=(GeoParameterRef){true,17,23};return wood_eng_bind(&f->operations.grids.engineering,&t,&s);}
static int sources(void)
{
    const char *set="{\"op\":\"set-source\",\"target\":{\"kind\":\"timber\",\"id\":1,\"field\":\"A\"},\"source\":{\"kind\":\"parameter\",\"parameterId\":17,\"fieldId\":23}}";
    Fixture f;init(&f);CHECK(add_member(&f,1,false,WOOD_MEMBER_ROLE_PRIMARY));
    NAMED(!operation(&f,set)&&!strcmp(f.error,"D28: bind only an already placed timber"),"engineering-operations-unplaced-source");CHECK(f.eng.binding_count==0);
    CHECK(!operation(&f,"{\"op\":\"set-override\",\"target\":{\"kind\":\"timber\",\"id\":1,\"field\":\"A\"},\"value\":null}"));CHECK(!strcmp(f.error,"D28: bind only an already placed timber"));
    f.members[0].placed=true;
    CHECK(!operation(&f,"{\"op\":\"set-override\",\"target\":{\"kind\":\"timber\",\"id\":1,\"field\":\"A\"},\"value\":null}"));CHECK(!strcmp(f.error,"D28: object override requires an explicit source binding"));
    CHECK(operation(&f,set));CHECK(f.eng.binding_count==1&&f.eng.bindings[0].source.kind==ENG_PARAMETER&&f.eng.bindings[0].source.parameter.parameter_id==17&&f.eng.bindings[0].source.parameter.field_id==23);
    CHECK(operation(&f,"{\"op\":\"set-override\",\"target\":{\"kind\":\"timber\",\"id\":1,\"field\":\"A\"},\"value\":{\"kind\":\"parameter\",\"parameterId\":4,\"fieldId\":0}}"));
    EngBinding *b=&f.eng.bindings[0];CHECK(b->has_override&&b->override_value.kind==ENG_PARAMETER&&b->override_value.parameter.parameter_id==4&&b->override_value.parameter.field_id==0&&b->source.parameter.parameter_id==17);
    CHECK(operation(&f,"{\"op\":\"set-source\",\"target\":{\"kind\":\"timber\",\"id\":1,\"field\":\"A\"},\"source\":{\"kind\":\"literal\",\"value\":29}}"));
    CHECK(f.eng.binding_count==1&&b->has_override&&b->source.kind==ENG_LITERAL&&b->source.value==29);
    CHECK(operation(&f,"{\"op\":\"set-override\",\"target\":{\"kind\":\"timber\",\"id\":1,\"field\":\"A\"},\"value\":null}"));
    EngDimensionSource zero={0};CHECK(!b->has_override&&!memcmp(&b->override_value,&zero,sizeof zero)&&b->source.value==29);
    CHECK(!operation(&f,"{\"op\":\"set-override\",\"target\":{\"kind\":\"timber\",\"id\":1,\"field\":\"A\"},\"value\":{\"kind\":\"application\",\"id\":\"app\",\"field\":\"primary.A\"}}"));CHECK(!strcmp(f.error,"I35: application override cannot refer to another application"));
    f.owned=true;CHECK(!operation(&f,set));CHECK(!strcmp(f.error,"I42: owned timber dimensions come from its assembly binding"));f.owned=false;
    CHECK(!operation(&f,"{\"op\":\"set-source\",\"target\":{\"kind\":\"timber\",\"id\":9,\"field\":\"A\"},\"source\":{\"kind\":\"literal\",\"value\":1}}"));CHECK(!strcmp(f.error,"I35: dimension target timber does not exist"));return 0;
}
static int unbind_order(void)
{
    Fixture f;init(&f);CHECK(add_member(&f,1,true,WOOD_MEMBER_ROLE_PRIMARY));CHECK(bind_parameter(&f,1,0));CHECK(bind_parameter(&f,1,1));
    EngBinding kept=f.eng.bindings[1];
    CHECK(operation(&f,"{\"op\":\"unbind-source\",\"target\":{\"kind\":\"timber\",\"id\":1,\"field\":\"A\"}}"));
    NAMED(!strcmp(f.trace,"PEQW")&&f.write_saw_binding&&!f.write_bad,"engineering-operations-unbind-order");
    CHECK(f.members[0].size_a==55&&f.members[0].size_b==33&&f.eng.binding_count==1&&!memcmp(&f.eng.bindings[0],&kept,sizeof kept));
    EngBinding zero={0};CHECK(!memcmp(&f.eng.bindings[1],&zero,sizeof zero));
    f.trace_count=0;f.trace[0]=0;f.eng.bindings[0].has_override=true;f.eng.bindings[0].override_value.kind=ENG_LITERAL;f.eng.bindings[0].override_value.value=71;
    CHECK(operation(&f,"{\"op\":\"unbind-source\",\"target\":{\"kind\":\"timber\",\"id\":1,\"field\":\"B\"}}"));
    CHECK(!strcmp(f.trace,"PEQW")&&f.members[0].size_b==71&&f.eng.binding_count==0);
    WoodGridApplication grid={0};grid.id=1;grid.placement_id=10;grid.axis[0].source=GEO_GRID_SOURCE_BODY_GAP;grid.axis[0].body=100;grid.axis[0].gap=99;CHECK(wood_grid_stage(&f.grids,&grid));
    EngTarget gap={0,1,0,1};EngDimensionSource source={0};source.kind=ENG_PARAMETER;source.parameter=(GeoParameterRef){true,17,23};CHECK(wood_eng_bind(&f.operations.grids.engineering,&gap,&source));
    f.trace_count=0;f.trace[0]=0;CHECK(operation(&f,"{\"op\":\"unbind-source\",\"target\":{\"kind\":\"grid\",\"id\":1,\"axis\":\"u\",\"field\":\"gap\"}}"));
    CHECK(!strcmp(f.trace,"PEQW")&&f.grids.items[0].axis[0].gap==55&&f.grids.items[0].axis[0].body==100&&f.eng.binding_count==0);return 0;
}
static int unbind_failures(void)
{
    const char *unbind="{\"op\":\"unbind-source\",\"target\":{\"kind\":\"timber\",\"id\":1,\"field\":\"A\"}}";
    Fixture f;init(&f);CHECK(add_member(&f,1,true,WOOD_MEMBER_ROLE_PRIMARY));CHECK(bind_parameter(&f,1,0));EngineeringState original=f.eng;
    f.fail_rebuild=true;
    NAMED(!operation(&f,unbind)&&!strcmp(f.error,"parameter rebuild rejected"),"engineering-operations-unbind-rebuild-failure");
    CHECK(!strcmp(f.trace,"P")&&!memcmp(&f.eng,&original,sizeof original)&&f.members[0].size_a==27&&!f.write_saw_binding);
    f.fail_rebuild=false;f.fail_effective=true;f.trace_count=0;f.trace[0]=0;
    CHECK(!operation(&f,unbind));CHECK(!strcmp(f.error,"effective rejected")&&!strcmp(f.trace,"PE"));
    CHECK(!memcmp(&f.eng,&original,sizeof original)&&f.members[0].size_a==27);
    f.trace_count=0;f.trace[0]=0;
    CHECK(!operation(&f,"{\"op\":\"unbind-source\",\"target\":{\"kind\":\"timber\",\"id\":1,\"field\":\"B\"}}"));CHECK(!strcmp(f.error,"I38: target has no source binding")&&f.trace_count==0);
    CHECK(!operation(&f,"{\"op\":\"unbind-source\",\"target\":{},\"extra\":1}"));CHECK(!strcmp(f.error,"I38: invalid unbind target")&&f.trace_count==0);return 0;
}
static int roles(void)
{
    const char *bind="{\"op\":\"bind-timber\",\"id\":1,\"application\":\"app\",\"slot\":\"primary\"}";
    Fixture f;init(&f);catalog(&f);CHECK(add_member(&f,1,true,WOOD_MEMBER_ROLE_BOUNDARY));
    NAMED(!operation(&f,bind)&&!strcmp(f.error,"D28: timber must be placed on the application face with the selected matching role"),"engineering-operations-role-lock");CHECK(f.eng.binding_count==0&&f.members[0].role==WOOD_MEMBER_ROLE_BOUNDARY);
    f.members[0].role=WOOD_MEMBER_ROLE_PRIMARY;f.pids[0]=11;CHECK(!operation(&f,bind));CHECK(f.eng.binding_count==0);
    f.pids[0]=10;f.members[0].placed=false;CHECK(!operation(&f,bind));CHECK(f.eng.binding_count==0);
    f.members[0].placed=true;f.members[0].role=WOOD_MEMBER_ROLE_CUSTOM;CHECK(!operation(&f,bind));CHECK(f.eng.binding_count==0);
    f.members[0].role=WOOD_MEMBER_ROLE_PRIMARY;
    CHECK(!operation(&f,"{\"op\":\"bind-timber\",\"id\":1,\"application\":\"app\",\"slot\":\"custom\"}"));
    CHECK(!operation(&f,"{\"op\":\"bind-timber\",\"id\":1,\"application\":\"app\",\"slot\":null}"));CHECK(!strcmp(f.error,"D28: timber binding requires an explicit role slot"));
    CHECK(operation(&f,bind));CHECK(f.eng.binding_count==2&&f.members[0].role==WOOD_MEMBER_ROLE_PRIMARY);
    for(int field=0;field<2;++field){EngTarget t={1,1,0,field};EngBinding *b=wood_eng_binding(&f.operations.grids.engineering,&t);CHECK(b&&b->source.kind==ENG_APPLICATION&&!strcmp(b->source.ref,"app")&&b->source.field==ENG_PRIMARY_A+field);}
    CHECK(!operation(&f,"{\"op\":\"bind-timber\",\"id\":99,\"application\":\"missing\",\"slot\":null}"));CHECK(!strcmp(f.error,"D28: application not found"));
    f.eng.method_count=0;CHECK(!operation(&f,bind));CHECK(!strcmp(f.error,"I34: application method not found"));return 0;
}
static int publication(void)
{
    const char *value="{\"id\":\"wood\",\"version\":1,\"kind\":\"timber\",\"name\":\"Wood\",\"A\":27,\"B\":33}";
    Fixture f;init(&f);char text[1024],canonical[512],hash[65];GeoJson j;CHECK(geo_json_parse(&j,value));CHECK(geo_json_canonical(&j,0,canonical,sizeof canonical));geo_sha256(canonical,strlen(canonical),hash);geo_json_free(&j);
    snprintf(text,sizeof text,"{\"op\":\"publish-material\",\"value\":%s,\"extra\":1}",value);
    NAMED(!operation(&f,text)&&!strcmp(f.error,"I35: unexpected publication operation fields"),"engineering-operations-publication-fields");CHECK(f.eng.material_count==0);
    snprintf(text,sizeof text,"{\"op\":\"publish-material\",\"value\":%s,\"fingerprint\":false}",value);CHECK(!operation(&f,text));CHECK(!strcmp(f.error,"I34: invalid fingerprint"));
    snprintf(text,sizeof text,"{\"op\":\"publish-material\",\"value\":%s,\"fingerprint\":\"wrong\"}",value);CHECK(!operation(&f,text));CHECK(!strcmp(f.error,"I34: material fingerprint mismatch")&&f.eng.material_count==0);
    snprintf(text,sizeof text,"{\"op\":\"publish-material\",\"value\":%s,\"fingerprint\":\"%s\"}",value,hash);CHECK(operation(&f,text));CHECK(operation(&f,text));CHECK(f.eng.material_count==1&&!strcmp(f.eng.materials[0].fingerprint,hash));
    CHECK(operation(&f,"{\"op\":\"publish-method\",\"value\":{\"id\":\"method\",\"version\":1,\"name\":\"Method\",\"roles\":{\"primary\":{\"id\":\"wood\",\"version\":1}}}}"));CHECK(f.eng.method_count==1);
    CHECK(!operation(&f,"{\"op\":\"put-application\",\"value\":{},\"extra\":1}"));CHECK(!strcmp(f.error,"I35: unexpected application operation fields"));
    CHECK(operation(&f,"{\"op\":\"put-application\",\"value\":{\"id\":\"app\",\"placement_id\":10,\"method\":{\"id\":\"method\",\"version\":1}}}"));CHECK(f.eng.application_count==1&&!strcmp(f.eng.applications[0].id,"app"));
    CHECK(!operation(&f,"{\"op\":\"other\"}"));CHECK(!strcmp(f.error,"I35: unknown engineering operation"));return 0;
}
static int restore_members(void)
{
    Fixture f;init(&f);
    CHECK(!restore(&f,"{\"id\":0,\"A\":27,\"B\":33,\"role\":\"primary\",\"extra\":1}"));CHECK(!strcmp(f.error,"I36: invalid engineering timber declaration"));
    NAMED(!restore(&f,"{\"id\":0,\"A\":27,\"B\":33,\"role\":\"primary\",\"priority\":9}")&&!strcmp(f.error,"I36: non-custom role cannot set priority"),"engineering-operations-restore-priority");CHECK(f.count==0&&f.created_count==0);
    CHECK(!restore(&f,"{\"id\":0,\"A\":27,\"B\":33,\"role\":\"custom\"}"));CHECK(!strcmp(f.error,"I36: custom role requires positive priority"));
    CHECK(!restore(&f,"{\"id\":0,\"A\":27,\"B\":33,\"role\":\"custom\",\"priority\":0}"));CHECK(!strcmp(f.error,"I36: custom role requires positive priority"));
    CHECK(!restore(&f,"{\"id\":0,\"A\":27,\"B\":33,\"role\":\"other\"}"));CHECK(!strcmp(f.error,"I36: unknown timber role"));
    CHECK(restore(&f,"{\"id\":0,\"A\":27,\"B\":33,\"role\":\"custom\",\"priority\":9}"));
    CHECK(f.count==1&&f.created_count==1&&f.members[0].id==0&&f.members[0].role==WOOD_MEMBER_ROLE_CUSTOM&&f.members[0].cut_priority==9&&!f.members[0].placed&&f.members[0].auto_length&&f.members[0].length==0&&f.pids[0]==0);
    CHECK(!strcmp(f.trace,"CS")&&f.members[0].size_a==27&&f.members[0].size_b==33);
    NAMED(!restore(&f,"{\"id\":0,\"A\":27,\"B\":33,\"role\":\"primary\"}")&&!strcmp(f.error,"I10: timber ID exists or capacity exceeded"),"engineering-operations-restore-identity");CHECK(f.count==1&&f.created_count==1);
    init(&f);catalog(&f);
    CHECK(restore(&f,"{\"id\":2,\"A\":{\"source\":{\"kind\":\"application\",\"id\":\"app\",\"field\":\"primary.A\"},\"override\":{\"kind\":\"parameter\",\"parameterId\":17,\"fieldId\":23}},\"B\":{\"source\":{\"kind\":\"material\",\"id\":\"wood\",\"version\":1,\"field\":\"B\"},\"override\":null},\"role\":\"primary\"}"));
    CHECK(f.count==1&&!f.members[0].placed&&f.members[0].size_a==55&&f.members[0].size_b==33&&f.members[0].cut_priority==2&&f.eng.binding_count==2&&f.pids[0]==0);
    CHECK(f.eng.bindings[0].source.kind==ENG_APPLICATION&&!strcmp(f.eng.bindings[0].source.ref,"app")&&f.eng.bindings[0].source.field==ENG_PRIMARY_A&&f.eng.bindings[0].has_override&&f.eng.bindings[0].override_value.parameter.field_id==23);
    CHECK(f.eng.bindings[1].source.kind==ENG_MATERIAL&&f.eng.bindings[1].source.version==1&&f.eng.bindings[1].source.field==ENG_B);
    CHECK(!strcmp(f.trace,"CEQWEWS")&&f.write_saw_binding&&!f.write_bad);
    init(&f);f.operations.member_capacity=1;CHECK(add_member(&f,1,false,WOOD_MEMBER_ROLE_BOUNDARY));
    CHECK(!restore(&f,"{\"id\":2,\"A\":27,\"B\":33,\"role\":\"secondary\"}"));CHECK(!strcmp(f.error,"I10: timber ID exists or capacity exceeded")&&f.count==1&&f.created_count==0);return 0;
}
static int grid_dispatch(void)
{
    Fixture f;init(&f);catalog(&f);
    CHECK(!operation(&f,"{\"op\":\"bind-grid\",\"id\":1,\"application\":\"app\",\"slot\":\"primary\"}"));CHECK(!strcmp(f.error,"D28: invalid binding operation"));
    CHECK(!operation(&f,"{\"op\":\"bind-grid\",\"id\":1,\"application\":\"app\"}"));CHECK(!strcmp(f.error,"D28: selected main grid is missing; explicitly choose create"));
    CHECK(operation(&f,"{\"op\":\"bind-grid\",\"id\":1,\"application\":\"app\",\"create\":true}"));
    CHECK(f.grids.count==1&&f.grids.items[0].placement_id==10&&f.eng.binding_count==4);
    for(int axis=0;axis<2;++axis)for(int field=0;field<2;++field){EngTarget t={0,1,axis,field};EngBinding *b=wood_eng_binding(&f.operations.grids.engineering,&t);CHECK(b&&b->source.field==(field?ENG_U_GAP:ENG_U_PANEL)+axis&&!strcmp(b->source.ref,"app"));}return 0;
}
static int candidate(void)
{
    Fixture original,after;init(&original);CHECK(add_member(&original,1,false,WOOD_MEMBER_ROLE_PRIMARY));
    EngineeringState eng=original.eng;WoodMember member=original.members[0];
    memcpy(&after,&original,sizeof after);wire(&after);after.members[0].placed=true;
    CHECK(operation(&after,"{\"op\":\"set-source\",\"target\":{\"kind\":\"timber\",\"id\":1,\"field\":\"A\"},\"source\":{\"kind\":\"literal\",\"value\":42}}"));
    CHECK(after.eng.binding_count==1&&original.eng.binding_count==0&&!original.members[0].placed&&original.error[0]==0);
    CHECK(!memcmp(&original.eng,&eng,sizeof eng)&&!memcmp(&original.members[0],&member,sizeof member));
    memcpy(&after,&original,sizeof after);wire(&after);after.fail_serial=true;
    CHECK(!restore(&after,"{\"id\":2,\"A\":{\"source\":{\"kind\":\"literal\",\"value\":42},\"override\":null},\"B\":33,\"role\":\"secondary\"}"));
    CHECK(!strcmp(after.error,"serialization rejected")&&after.count==2&&after.eng.binding_count==1&&after.members[1].size_a==42&&after.created_count==1);
    CHECK(original.count==1&&original.created_count==0&&original.trace_count==0&&original.error[0]==0&&!memcmp(&original.eng,&eng,sizeof eng)&&!memcmp(&original.members[0],&member,sizeof member));return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"sources"))return sources();if(!strcmp(argv[1],"unbind-order"))return unbind_order();
    if(!strcmp(argv[1],"unbind-failures"))return unbind_failures();if(!strcmp(argv[1],"roles"))return roles();
    if(!strcmp(argv[1],"publication"))return publication();if(!strcmp(argv[1],"restore-members"))return restore_members();
    if(!strcmp(argv[1],"grid-dispatch"))return grid_dispatch();if(!strcmp(argv[1],"candidate"))return candidate();return 2;
}
