#include "engineering.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x,n) do{if(!(x)){fprintf(stderr,"ASSERT:%s error=%s\n",n,error);return 1;}}while(0)
static EngineeringState state;
static char error[256];
static int write_count,serial_count;
static bool derived,owned,serial_ok=true;
static WoodEngineeringTargetInfo targets[3];
static GeoCoord written[3][2];
static bool placement(void *user,uint32_t id,bool *is_derived)
{(void)user;if(is_derived)*is_derived=derived;return id==10||id==20;}
static int slot(uint32_t id){return id==1?0:id==2?1:id==7?2:-1;}
static bool target(void *user,const EngTarget *t,WoodEngineeringTargetInfo *out)
{(void)user;int i=slot(t->id);if(i<0)return false;*out=targets[i];return true;}
static bool named(void *user,const char *name,GeoCoord *out)
{(void)user;if(strcmp(name,"width"))return false;*out=42;return true;}
static bool parameter(void *user,GeoParameterRef ref,GeoCoord *out,char *message,size_t cap)
{(void)user;if(ref.parameter_id==3&&ref.field_id==5){*out=67;return true;}snprintf(message,cap,"I38 MISSING: parameter %u field %u",ref.parameter_id,ref.field_id);return false;}
static bool member_owned(void *user,uint32_t id){(void)user;(void)id;return owned;}
static void write_dimension(void *user,const EngTarget *t,GeoCoord value)
{(void)user;++write_count;written[slot(t->id)][t->field]=value;}
static bool serializable(void *user,char *message,size_t cap)
{(void)user;++serial_count;if(!serial_ok)snprintf(message,cap,"I10: test record capacity");return serial_ok;}
static WoodEngineeringContext context={&state,NULL,error,sizeof error,placement,target,named,parameter,member_owned,write_dimension,serializable};
static bool publish(const char *text,int kind,const char *fingerprint)
{GeoJson j;if(!geo_json_parse(&j,text)){geo_json_free(&j);return false;}bool ok=kind==0?wood_eng_publish_material(&context,&j,0,fingerprint):kind==1?wood_eng_publish_method(&context,&j,0,fingerprint):wood_eng_put_application(&context,&j,0);geo_json_free(&j);return ok;}
static const char *panel="{\"id\":\"p\",\"version\":1,\"kind\":\"panel\",\"name\":\"Panel\",\"width\":100,\"length\":200,\"thickness\":\"6.50\"}";
static const char *member="{\"id\":\"t\",\"version\":1,\"kind\":\"timber\",\"name\":\"Member\",\"A\":30,\"B\":40}";
static const char *method="{\"id\":\"m\",\"version\":1,\"name\":\"Method\",\"panel\":{\"id\":\"p\",\"version\":1},\"roles\":{\"primary\":{\"id\":\"t\",\"version\":1}},\"gap\":0,\"longAxis\":\"v\",\"mainAlong\":\"u\"}";
static const char *application="{\"id\":\"a\",\"placement_id\":10,\"method\":{\"id\":\"m\",\"version\":1}}";
static bool seed(void){return publish(panel,0,NULL)&&publish(member,0,NULL)&&publish(method,1,NULL)&&publish(application,2,NULL);}
static void reset(void)
{memset(&state,0,sizeof state);memset(error,0,sizeof error);memset(written,0,sizeof written);write_count=serial_count=0;derived=owned=false;serial_ok=true;for(int i=0;i<3;++i){targets[i]=(WoodEngineeringTargetInfo){10,i==2?1:-1,false,false,true,true};}}
static EngDimensionSource source(int kind,int field,const char *id)
{EngDimensionSource s={0};s.kind=kind;s.field=field;s.version=1;if(id)snprintf(s.ref,sizeof s.ref,"%s",id);return s;}
static int materials(void)
{
    REQUIRE(publish(panel,0,NULL),"material-publish");
    REQUIRE(!strcmp(state.materials[0].content,"{\"id\":\"p\",\"kind\":\"panel\",\"length\":200,\"name\":\"Panel\",\"thickness\":\"6.50\",\"version\":1,\"width\":100}"),"material-canonical");
    char digest[65];geo_sha256(state.materials[0].content,strlen(state.materials[0].content),digest);
    REQUIRE(!strcmp(digest,state.materials[0].fingerprint),"material-fingerprint");
    REQUIRE(publish(panel,0,digest)&&state.material_count==1,"material-repeat");
    REQUIRE(!publish(panel,0,"wrong")&&!strcmp(error,"I34: material fingerprint mismatch"),"material-fingerprint-refusal");
    REQUIRE(!publish("{\"id\":\"p\",\"version\":1,\"kind\":\"panel\",\"name\":\"Changed\",\"width\":100,\"length\":200}",0,NULL),"material-immutable");
    REQUIRE(!strcmp(error,"I34: material ID/version already has different immutable content"),"material-immutable-error");
    REQUIRE(state.material_count==1&&state.materials[0].width==100,"material-preserved");
    state.materials[0].archived=true;REQUIRE(wood_eng_material(&context,"p",1)==&state.materials[0],"archived-reference");
    REQUIRE(!publish("{\"id\":\"z\",\"version\":1,\"kind\":\"panel\",\"name\":\"Z\",\"width\":1,\"length\":1,\"thickness\":\"0.00\"}",0,NULL),"thickness-positive");
    return 0;
}
static int methods(void)
{
    REQUIRE(!publish(method,1,NULL)&&!strcmp(error,"I34: method material version is missing or has incompatible kind"),"method-missing");
    REQUIRE(publish(panel,0,NULL)&&publish(member,0,NULL),"method-materials");
    REQUIRE(publish(method,1,NULL)&&state.methods[0].has_gap&&state.methods[0].gap==0,"method-explicit-zero");
    REQUIRE(!publish("{\"id\":\"x\",\"version\":1,\"name\":\"Wrong\",\"panel\":{\"id\":\"t\",\"version\":1}}",1,NULL),"method-kind");
    REQUIRE(publish(method,1,NULL)&&state.method_count==1,"method-repeat");
    REQUIRE(!publish(method,1,"wrong")&&!strcmp(error,"I34: method fingerprint mismatch"),"method-fingerprint");
    REQUIRE(!publish("{\"id\":\"m\",\"version\":1,\"name\":\"Other\"}",1,NULL),"method-immutable");
    return 0;
}
static int applications(void)
{
    REQUIRE(seed(),"application-seed");
    REQUIRE(!publish("{\"id\":\"a\",\"placement_id\":20,\"method\":{\"id\":\"m\",\"version\":1}}",2,NULL),"application-cannot-move");
    REQUIRE(!publish("{\"id\":\"b\",\"placement_id\":10,\"method\":{\"id\":\"m\",\"version\":1}}",2,NULL),"application-one-per-face");
    derived=true;REQUIRE(!publish(application,2,NULL)&&!strcmp(error,"D4: derived placements cannot receive D28 face applications"),"application-derived");derived=false;
    REQUIRE(!publish("{\"id\":\"a\",\"placement_id\":10,\"method\":{\"id\":\"m\",\"version\":1},\"overrides\":{\"gap\":{\"kind\":\"parameter\",\"parameterId\":3,\"fieldId\":5}}}",2,NULL),"application-parameter-override");
    REQUIRE(state.application_count==1&&!state.applications[0].overridden[0],"application-failure-preserved");
    return 0;
}
static int resolution(void)
{
    REQUIRE(seed(),"resolve-seed");GeoCoord value=-1;char path[256];EngTarget grid={0,1,0,0};EngDimensionSource s=source(ENG_APPLICATION,ENG_U_PANEL,"a");
    REQUIRE(wood_eng_resolve(&context,&s,&grid,10,-1,&value,path,sizeof path)&&value==100,"resolve-width-axis");
    grid.axis=1;s.field=ENG_V_PANEL;REQUIRE(wood_eng_resolve(&context,&s,&grid,10,-1,&value,path,sizeof path)&&value==200,"resolve-length-axis");
    grid.field=1;s.field=ENG_V_GAP;REQUIRE(wood_eng_resolve(&context,&s,&grid,10,-1,&value,path,sizeof path)&&value==0,"resolve-zero-gap");
    state.applications[0].overridden[0]=true;state.applications[0].overrides[0]=source(ENG_SPEC,0,"width");
    REQUIRE(wood_eng_resolve(&context,&s,&grid,10,-1,&value,path,sizeof path)&&value==42&&strstr(path,"face override -> spec:width"),"resolve-face-precedence");
    EngBinding b={grid,s,{0},true};b.override_value.value=9;
    REQUIRE(wood_eng_effective(&context,&b,&value,path,sizeof path)&&value==9&&!strcmp(path,"explicit integer mm"),"resolve-object-precedence");
    targets[0].placement_id=20;REQUIRE(!wood_eng_effective(&context,&b,&value,NULL,0),"override-base-face-required");targets[0].placement_id=10;
    b.source=source(ENG_SPEC,0,"missing");REQUIRE(!wood_eng_effective(&context,&b,&value,NULL,0),"override-inactive-base-required");
    b.source=source(ENG_PARAMETER,0,NULL);b.source.parameter=(GeoParameterRef){true,3,5};b.has_override=false;
    REQUIRE(wood_eng_effective(&context,&b,&value,path,sizeof path)&&value==67&&!strcmp(path,"param:3:5"),"parameter-identity");
    return 0;
}
static int roles(void)
{
    REQUIRE(seed(),"roles-seed");GeoCoord value;EngTarget t={1,7,0,0};EngDimensionSource s=source(ENG_APPLICATION,ENG_PRIMARY_A,"a");
    REQUIRE(wood_eng_resolve(&context,&s,&t,10,1,&value,NULL,0)&&value==30,"role-primary");
    REQUIRE(!wood_eng_resolve(&context,&s,&t,10,0,&value,NULL,0),"role-mismatch");
    EngBinding b={t,s,{0},true};b.override_value.value=55;targets[2].role=3;
    REQUIRE(!wood_eng_effective(&context,&b,&value,NULL,0),"role-custom-override");targets[2].role=1;
    s=source(ENG_MATERIAL,ENG_B,"t");REQUIRE(!wood_eng_resolve(&context,&s,&t,10,1,&value,NULL,0),"material-axis-mismatch");
    owned=true;REQUIRE(!wood_eng_bind(&context,&t,&s)&&state.binding_count==0,"owned-member-bind");owned=false;
    targets[2].placed=false;b.has_override=false;targets[2].placement_id=20;
    REQUIRE(wood_eng_effective(&context,&b,&value,NULL,0)&&value==30,"unplaced-replay");
    targets[2].placed=true;REQUIRE(!wood_eng_effective(&context,&b,&value,NULL,0),"placed-face-check");
    return 0;
}
static int rebuild(void)
{
    REQUIRE(seed(),"rebuild-seed");EngTarget a={0,1,0,0},b={0,2,0,0};EngDimensionSource s=source(ENG_LITERAL,0,NULL);s.value=17;
    REQUIRE(wood_eng_bind(&context,&a,&s),"rebuild-bind-one");s.value=0;REQUIRE(wood_eng_bind(&context,&b,&s),"rebuild-bind-two");char message[256];
    REQUIRE(!wood_engineering_rebuild(&context,message,sizeof message)&&write_count==1&&written[0][0]==17&&serial_count==0,"rebuild-partial-order");
    state.bindings[1].source.value=19;serial_ok=false;write_count=0;
    REQUIRE(!wood_engineering_rebuild(&context,message,sizeof message)&&write_count==2&&serial_count==1&&!strcmp(message,"I10: test record capacity"),"rebuild-record-capacity");
    serial_ok=true;targets[0].from_system=true;write_count=0;
    REQUIRE(!wood_engineering_rebuild(&context,message,sizeof message)&&write_count==0&&!strcmp(message,"D29: edit the grid-system source; engineering bindings are not allowed on its application"),"rebuild-system-target");
    targets[0].from_system=false;targets[0].panel_axis=false;
    REQUIRE(!wood_engineering_rebuild(&context,message,sizeof message)&&write_count==0,"rebuild-panel-axis");
    targets[0].panel_axis=true;REQUIRE(wood_engineering_rebuild(&context,message,sizeof message)&&written[1][0]==19,"rebuild-complete");
    return 0;
}
static int fragments(void)
{
    REQUIRE(seed(),"fragment-seed");EngTarget a={0,1,0,0},b={0,2,0,0};EngDimensionSource s=source(ENG_APPLICATION,ENG_U_PANEL,"a");
    REQUIRE(wood_eng_bind(&context,&a,&s)&&wood_eng_bind(&context,&b,&s),"fragment-bindings");
    targets[0].placement_id=20;
    REQUIRE(!wood_engineering_follow_fragment(&context,10)&&state.applications[0].placement_id==10,"fragment-conflict");
    targets[1].placement_id=20;
    REQUIRE(wood_engineering_follow_fragment(&context,10)&&state.applications[0].placement_id==20,"fragment-move");
    REQUIRE(!strcmp(state.applications[0].content,"{\"id\":\"a\",\"method\":{\"id\":\"m\",\"version\":1},\"placement_id\":20}"),"fragment-canonical-content");
    return 0;
}
static int deletion(void)
{
    REQUIRE(seed(),"delete-seed");EngTarget a={0,1,0,0},b={1,7,0,0};EngDimensionSource s=source(ENG_LITERAL,0,NULL);s.value=12;
    REQUIRE(wood_eng_bind(&context,&a,&s)&&wood_eng_bind(&context,&b,&s),"delete-bindings");
    wood_engineering_drop_owned(&context,"grid",1);
    REQUIRE(state.binding_count==1&&state.bindings[0].target.id==7,"delete-only-owned");
    EngBinding zero={0};REQUIRE(!memcmp(&state.bindings[1],&zero,sizeof zero),"delete-zero-tail");
    wood_engineering_drop_owned(&context,"placement",10);REQUIRE(state.application_count==0&&state.binding_count==1,"delete-no-orphan-collection");
    REQUIRE(state.material_count==2&&state.method_count==1&&wood_engineering_used(&context),"delete-retain-versions");
    return 0;
}
int main(int argc,char **argv)
{if(argc!=2)return 2;reset();if(!strcmp(argv[1],"materials"))return materials();if(!strcmp(argv[1],"methods"))return methods();if(!strcmp(argv[1],"applications"))return applications();if(!strcmp(argv[1],"resolution"))return resolution();if(!strcmp(argv[1],"roles"))return roles();if(!strcmp(argv[1],"rebuild"))return rebuild();if(!strcmp(argv[1],"fragments"))return fragments();if(!strcmp(argv[1],"deletion"))return deletion();return 2;}
