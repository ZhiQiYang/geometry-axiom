/* D28/I35/I36 public W client. Only the host owns candidate commit/rollback. */
#include "grid_application.h"
#include <stdio.h>
#include <string.h>

#define CHECK(value) do { if(!(value)){fprintf(stderr,"ASSERT:%s:%d\n",__func__,__LINE__);return 1;} } while(0)
#define NAMED(value,label) do { if(!(value)){fprintf(stderr,"ASSERT:%s\n",label);return 1;} } while(0)
typedef struct { bool missing,bounds_valid; GeoRect2 bounds; unsigned calls; uint32_t last_pid; } Facts;
typedef struct { WoodGridState grids; EngineeringState eng; Facts facts; char error[256]; WoodGridContext context; } Fixture;
static bool host(void *opaque,uint32_t pid,WoodGridHost *out)
{
    Facts *f=opaque;++f->calls;f->last_pid=pid;if(f->missing)return false;
    memset(out,0,sizeof *out);out->id=pid;out->boundary_id=71;out->bounds=f->bounds;out->bounds_valid=f->bounds_valid;return true;
}
static bool owned(void *opaque,uint32_t id){(void)opaque;(void)id;return false;}
static void wire(Fixture *f)
{
    memset(&f->context,0,sizeof f->context);f->context.state=&f->grids;f->context.user=&f->facts;f->context.host=host;
    f->context.engineering.state=&f->eng;f->context.engineering.user=&f->facts;
    f->context.engineering.error=f->error;f->context.engineering.error_capacity=sizeof f->error;f->context.engineering.member_owned=owned;
}
static void init(Fixture *f)
{memset(f,0,sizeof *f);f->facts.bounds_valid=true;f->facts.bounds=(GeoRect2){10,20,1010,2020};wire(f);}
static EngApplication application(void)
{
    EngApplication a={0};strcpy(a.id,"application-a");a.placement_id=10;a.main_along=2;
    a.anchor_kind[0]=a.anchor_kind[1]=1;a.anchor[0]=10;a.anchor[1]=20;return a;
}
static EngMethodVersion method(void){EngMethodVersion m={0};m.main_along=1;return m;}
static WoodGridApplication direct(uint32_t id,uint32_t pid)
{
    WoodGridApplication g={0};g.id=id;g.placement_id=pid;g.main_along=1;
    for(int k=0;k<2;++k){g.axis[k].source=GEO_GRID_SOURCE_SERIES;g.axis[k].step=100;g.axis[k].series_count=3;}return g;
}
static bool bind(Fixture *f,const char *text,uint32_t id,const EngApplication *a,const EngMethodVersion *m)
{
    GeoJson j;f->error[0]=0;if(!geo_json_parse(&j,text)){fprintf(stderr,"SETUP:invalid bind JSON\n");geo_json_free(&j);return false;}
    bool ok=wood_grid_bind_engineering(&f->context,&j,0,id,a,m);geo_json_free(&j);return ok;
}
static bool restore(Fixture *f,const char *text)
{
    GeoJson j;f->error[0]=0;if(!geo_json_parse(&j,text)){fprintf(stderr,"SETUP:invalid restore JSON\n");geo_json_free(&j);return false;}
    bool ok=wood_grid_restore_engineering(&f->context,&j,0);geo_json_free(&j);return ok;
}
static bool dimension(Fixture *f,const char *text,EngTarget target,GeoCoord *value)
{
    GeoJson j;f->error[0]=0;if(!geo_json_parse(&j,text)){fprintf(stderr,"SETUP:invalid dimension JSON\n");geo_json_free(&j);return false;}
    bool ok=wood_grid_dimension_read(&f->context.engineering,&j,0,&target,value);geo_json_free(&j);return ok;
}
static int admission(void)
{
    Fixture f;init(&f);EngApplication a=application();EngMethodVersion m=method();WoodGridApplication g=direct(1,99);
    g.from_system=true;g.is_subgrid=true;CHECK(wood_grid_stage(&f.grids,&g));WoodGridState original=f.grids;
    NAMED(!bind(&f,"{\"create\":\"bad\"}",1,&a,&m)&&!strcmp(f.error,"D29: grid-system applications cannot have engineering bindings"),"grid-engineering-source-first");
    CHECK(!memcmp(&original,&f.grids,sizeof original));CHECK(f.eng.binding_count==0&&f.facts.calls==0);
    f.grids.items[0].from_system=false;f.grids.items[0].from_binding=true;
    CHECK(!bind(&f,"{}",1,&a,&m));CHECK(!strcmp(f.error,"D29: grid-system applications cannot have engineering bindings"));
    f.grids.items[0].from_binding=false;
    CHECK(!bind(&f,"{\"create\":\"bad\"}",1,&a,&m));CHECK(!strcmp(f.error,"D28: create must be boolean"));
    CHECK(!bind(&f,"{\"create\":true}",1,&a,&m));CHECK(!strcmp(f.error,"D28: selected main grid belongs to another face or is a subgrid"));
    f.grids.items[0].is_subgrid=false;
    CHECK(!bind(&f,"{}",1,&a,&m));CHECK(!strcmp(f.error,"D28: selected main grid belongs to another face or is a subgrid"));
    f.grids.items[0].placement_id=10;
    CHECK(!bind(&f,"{}",2,&a,&m));CHECK(!strcmp(f.error,"D28: selected main grid is missing; explicitly choose create"));
    CHECK(!bind(&f,"{\"create\":true}",2,&a,&m));CHECK(!strcmp(f.error,"I10: placement already has a main grid"));
    for(size_t k=0;k<WOOD_GRID_MAX;++k)f.grids.items[k]=direct((uint32_t)k+1,(uint32_t)k+100);
    f.grids.count=WOOD_GRID_MAX;
    CHECK(!bind(&f,"{\"create\":true}",100,&a,&m));CHECK(!strcmp(f.error,"I10: grid capacity exceeded"));
    CHECK(f.grids.count==WOOD_GRID_MAX&&f.eng.binding_count==0);
    init(&f);a.main_along=m.main_along=0;
    CHECK(!bind(&f,"{\"create\":true}",1,&a,&m));CHECK(!strcmp(f.error,"D28: new grid main direction is not set"));
    CHECK(f.facts.calls==0&&f.eng.binding_count==0);return 0;
}
static int create_update(void)
{
    Fixture f;init(&f);EngApplication a=application();EngMethodVersion m=method();WoodGridApplication g=direct(1,10);CHECK(wood_grid_stage(&f.grids,&g));
    WoodGridState original=f.grids;
    NAMED(!bind(&f,"{\"create\":true}",1,&a,&m)&&!strcmp(f.error,"D28: create grid ID already exists; select update instead"),"grid-engineering-create-existing");
    CHECK(!memcmp(&original,&f.grids,sizeof original)&&f.eng.binding_count==0);
    CHECK(bind(&f,"{\"create\":false}",1,&a,&m));CHECK(f.grids.count==1&&f.grids.items[0].main_along==1&&f.eng.binding_count==4);
    for(int axis=0;axis<2;++axis)for(int field=0;field<2;++field){
        EngTarget target={0,1,axis,field};EngBinding *b=wood_eng_binding(&f.context.engineering,&target);CHECK(b);
        CHECK(b->source.kind==ENG_APPLICATION&&b->source.field==(field?ENG_U_GAP:ENG_U_PANEL)+axis&&!strcmp(b->source.ref,a.id));
        CHECK(!b->has_override&&f.grids.items[0].axis[axis].source==GEO_GRID_SOURCE_BODY_GAP);
    }
    EngTarget target={0,1,1,0};EngBinding *old=wood_eng_binding(&f.context.engineering,&target);
    old->has_override=true;old->override_value.kind=ENG_PARAMETER;old->override_value.parameter=(GeoParameterRef){true,77,91};
    strcpy(a.id,"application-b");CHECK(bind(&f,"{}",1,&a,&m));CHECK(f.eng.binding_count==4);
    old=wood_eng_binding(&f.context.engineering,&target);CHECK(old->has_override&&old->override_value.parameter.parameter_id==77&&old->override_value.parameter.field_id==91);
    CHECK(!strcmp(old->source.ref,"application-b"));
    init(&f);a=application();CHECK(bind(&f,"{\"create\":true}",0,&a,&m));CHECK(f.grids.items[0].id==0&&f.grids.items[0].main_along==2);
    init(&f);a.main_along=0;CHECK(bind(&f,"{\"create\":true}",2,&a,&m));CHECK(f.grids.items[0].main_along==1);return 0;
}
static int anchors(void)
{
    Fixture f;init(&f);EngApplication a=application();EngMethodVersion m=method();
    a.anchor_kind[0]=2;a.anchor_kind[1]=3;
    CHECK(bind(&f,"{\"create\":true,\"anchors\":{\"u\":123}}",1,&a,&m));
    CHECK(f.grids.items[0].axis[0].anchor==123&&f.grids.items[0].axis[1].anchor==2020&&f.facts.last_pid==10);
    a.anchor_kind[0]=a.anchor_kind[1]=1;a.anchor[0]=777;a.anchor[1]=888;
    CHECK(bind(&f,"{}",1,&a,&m));
    NAMED(f.grids.items[0].axis[0].anchor==123&&f.grids.items[0].axis[1].anchor==2020,"grid-engineering-anchor-inheritance");
    CHECK(bind(&f,"{\"anchors\":{\"v\":42}}",1,&a,&m));CHECK(f.grids.items[0].axis[0].anchor==123&&f.grids.items[0].axis[1].anchor==42);
    CHECK(f.grids.items[0].axis[0].anchor_explicit&&f.grids.items[0].axis[1].anchor_explicit);
    CHECK(!bind(&f,"{\"anchors\":{\"x\":1}}",1,&a,&m));CHECK(!strcmp(f.error,"D28: anchor fields must be u/v"));
    CHECK(!bind(&f,"{\"anchors\":{\"u\":true}}",1,&a,&m));CHECK(!strcmp(f.error,"D28: grid anchor must be integer mm in D1 range"));
    char text[160];snprintf(text,sizeof text,"{\"anchors\":{\"u\":%lld}}",(long long)GEO_COORD_LIMIT+1);
    CHECK(!bind(&f,text,1,&a,&m));CHECK(!strcmp(f.error,"D28: grid anchor must be integer mm in D1 range"));
    f.facts.bounds_valid=false;CHECK(!bind(&f,"{}",1,&a,&m));CHECK(!strcmp(f.error,"D28: cannot resolve application face bounds"));
    f.facts.bounds_valid=true;f.facts.missing=true;CHECK(!bind(&f,"{}",1,&a,&m));CHECK(!strcmp(f.error,"D28: cannot resolve application face bounds"));
    init(&f);a=application();a.anchor_kind[0]=0;
    CHECK(!bind(&f,"{\"create\":true}",1,&a,&m));CHECK(!strcmp(f.error,"D28: new panel axis needs an explicit origin or chosen face edge"));
    init(&f);a=application();a.anchor_kind[0]=2;a.anchor_kind[1]=3;CHECK(bind(&f,"{\"create\":true}",1,&a,&m));
    CHECK(f.grids.items[0].axis[0].anchor==10&&f.grids.items[0].axis[1].anchor==2020);return 0;
}
static int dimensions(void)
{
    Fixture f;init(&f);GeoCoord value=99;EngTarget panel={0,1,0,0},gap={0,1,0,1},timber_a={1,1,0,0},timber_b={1,1,0,1};
    CHECK(dimension(&f,"0",gap,&value)&&value==0&&f.eng.binding_count==0);
    NAMED(!dimension(&f,"0",panel,&value)&&!strcmp(f.error,"I35: invalid direct dimension"),"grid-engineering-panel-positive");
    CHECK(!dimension(&f,"-1",gap,&value));CHECK(!dimension(&f,"0",timber_a,&value));CHECK(!dimension(&f,"0",timber_b,&value));
    CHECK(dimension(&f,"1",panel,&value)&&value==1);CHECK(dimension(&f,"1",timber_b,&value)&&value==1);
    char text[80];snprintf(text,sizeof text,"%lld",(long long)GEO_COORD_LIMIT);CHECK(dimension(&f,text,panel,&value)&&value==GEO_COORD_LIMIT);
    snprintf(text,sizeof text,"%lld",(long long)GEO_COORD_LIMIT+1);CHECK(!dimension(&f,text,gap,&value));
    CHECK(dimension(&f,"{\"source\":{\"kind\":\"material\",\"id\":\"panel-a\",\"version\":7,\"field\":\"width\"},\"override\":{\"kind\":\"parameter\",\"parameterId\":0,\"fieldId\":17}}",panel,&value)&&value==1);
    EngBinding *b=wood_eng_binding(&f.context.engineering,&panel);CHECK(b&&b->source.kind==ENG_MATERIAL&&b->source.version==7&&b->source.field==ENG_WIDTH&&!strcmp(b->source.ref,"panel-a"));
    CHECK(b->has_override&&b->override_value.kind==ENG_PARAMETER&&b->override_value.parameter.set&&b->override_value.parameter.parameter_id==0&&b->override_value.parameter.field_id==17);
    CHECK(dimension(&f,"{\"source\":{\"kind\":\"application\",\"id\":\"application-a\",\"field\":\"u.gap\"},\"override\":{\"kind\":\"literal\",\"value\":0}}",gap,&value)&&value==0);
    CHECK(f.eng.binding_count==2);b=wood_eng_binding(&f.context.engineering,&gap);CHECK(b->source.kind==ENG_APPLICATION&&b->source.field==ENG_U_GAP&&b->has_override&&b->override_value.value==0);
    CHECK(dimension(&f,"{\"source\":{\"kind\":\"spec\",\"name\":\"panel_size\"},\"override\":null}",panel,&value));
    CHECK(f.eng.binding_count==2);b=wood_eng_binding(&f.context.engineering,&panel);CHECK(b->source.kind==ENG_SPEC&&!strcmp(b->source.ref,"panel_size")&&!b->has_override);
    CHECK(!dimension(&f,"{\"source\":{\"kind\":\"literal\",\"value\":10},\"override\":{\"kind\":\"application\",\"id\":\"a\",\"field\":\"u.panel\"}}",panel,&value));
    CHECK(!strcmp(f.error,"I35: application override cannot refer to another application"));return 0;
}
static int binding_capacity(void)
{
    Fixture f;init(&f);GeoCoord value;const char *source="{\"source\":{\"kind\":\"literal\",\"value\":10},\"override\":null}";
    for(uint32_t k=0;k<ENG_BINDING_MAX;++k){EngTarget target={0,k,0,0};CHECK(dimension(&f,source,target,&value));}
    CHECK(f.eng.binding_count==ENG_BINDING_MAX);EngTarget extra={0,ENG_BINDING_MAX,0,0},old={0,0,0,0};EngineeringState snapshot=f.eng;
    CHECK(!dimension(&f,source,extra,&value));CHECK(!strcmp(f.error,"I10: engineering dimension binding capacity exceeded"));CHECK(!memcmp(&snapshot,&f.eng,sizeof snapshot));
    CHECK(dimension(&f,"{\"source\":{\"kind\":\"parameter\",\"parameterId\":32,\"fieldId\":6},\"override\":null}",old,&value));
    CHECK(f.eng.binding_count==ENG_BINDING_MAX&&f.eng.bindings[0].source.parameter.parameter_id==32&&f.eng.bindings[0].source.parameter.field_id==6);return 0;
}
static int restore_axes(void)
{
    Fixture f;init(&f);
    CHECK(restore(&f,"{\"id\":0,\"placement_id\":10,\"mainAlong\":\"v\",\"axes\":{\"u\":{\"kind\":\"panel\",\"anchor\":-10,\"panel\":{\"source\":{\"kind\":\"material\",\"id\":\"panel-a\",\"version\":7,\"field\":\"length\"},\"override\":{\"kind\":\"literal\",\"value\":300}},\"gap\":0},\"v\":{\"kind\":\"series\",\"start\":20,\"step\":100,\"count\":3}}}"));
    WoodGridApplication *g=&f.grids.items[0];CHECK(g->id==0&&g->placement_id==10&&g->main_along==2);
    CHECK(g->axis[0].source==GEO_GRID_SOURCE_BODY_GAP&&g->axis[0].anchor==-10&&g->axis[0].anchor_explicit&&g->axis[0].body==1&&g->axis[0].gap==0);
    CHECK(g->axis[1].source==GEO_GRID_SOURCE_SERIES&&g->axis[1].start==20&&g->axis[1].step==100&&g->axis[1].series_count==3);
    EngTarget target={0,0,0,0};EngBinding *b=wood_eng_binding(&f.context.engineering,&target);CHECK(b&&b->source.kind==ENG_MATERIAL&&b->source.version==7&&b->source.field==ENG_LENGTH&&!strcmp(b->source.ref,"panel-a"));
    CHECK(b->has_override&&b->override_value.kind==ENG_LITERAL&&b->override_value.value==300&&f.eng.binding_count==1);
    CHECK(restore(&f,"{\"id\":2,\"placement_id\":11,\"mainAlong\":null,\"axes\":{\"u\":null,\"v\":{\"kind\":\"explicit\",\"coords\":[-20,0,20]}}}"));
    g=&f.grids.items[1];CHECK(g->main_along==0&&g->axis[0].source==0&&g->axis[1].source==GEO_GRID_SOURCE_EXPLICIT&&g->axis[1].count==3);
    CHECK(g->axis[1].coords[0]==-20&&g->axis[1].coords[1]==0&&g->axis[1].coords[2]==20);CHECK(f.eng.binding_count==1);return 0;
}
static int restore_errors(void)
{
    const char *valid="{\"id\":1,\"placement_id\":10,\"mainAlong\":\"u\",\"axes\":{\"u\":null,\"v\":null}}";
    Fixture f;init(&f);CHECK(restore(&f,valid));WoodGridState snapshot=f.grids;
    NAMED(!restore(&f,valid)&&!strcmp(f.error,"I36: repeated engineering grid declaration"),"grid-engineering-restore-identity");CHECK(!memcmp(&snapshot,&f.grids,sizeof snapshot));
    CHECK(!restore(&f,"{\"id\":2,\"placement_id\":10,\"mainAlong\":\"u\",\"axes\":{}}"));CHECK(!strcmp(f.error,"I10: duplicate main grid on placement"));
    for(size_t k=0;k<WOOD_GRID_MAX;++k)f.grids.items[k]=direct((uint32_t)k+2,(uint32_t)k+100);f.grids.count=WOOD_GRID_MAX;
    CHECK(!restore(&f,valid));CHECK(!strcmp(f.error,"I10: grid capacity exceeded")&&f.grids.count==WOOD_GRID_MAX);
    init(&f);f.facts.missing=true;CHECK(!restore(&f,valid));CHECK(!strcmp(f.error,"I36: invalid engineering grid declaration"));
    init(&f);CHECK(!restore(&f,"{\"id\":1,\"placement_id\":10,\"mainAlong\":\"x\",\"axes\":{}}"));CHECK(!strcmp(f.error,"I36: invalid engineering grid declaration"));
    CHECK(!restore(&f,"{\"id\":1,\"placement_id\":10,\"mainAlong\":null,\"axes\":{\"u\":null}}"));CHECK(!strcmp(f.error,"I36: grid axes require u/v")&&f.grids.count==0);
    const char *axis[]={"{}","{\"kind\":\"other\"}","{\"kind\":\"panel\",\"anchor\":true,\"panel\":10,\"gap\":0}","{\"kind\":\"series\",\"start\":0,\"step\":0,\"count\":3}","{\"kind\":\"series\",\"start\":0,\"step\":10,\"count\":0}","{\"kind\":\"explicit\",\"coords\":[]}","{\"kind\":\"explicit\",\"coords\":[true]}","{\"kind\":\"explicit\",\"coords\":0}"};
    const char *error[]={"I36: missing grid axis kind","I36: unknown grid axis kind","I36: invalid panel grid anchor","I36: invalid series axis","I36: invalid series axis","I10: grid coordinate capacity exceeded","I36: invalid grid coordinate","I36: invalid explicit axis"};
    for(size_t i=0;i<sizeof axis/sizeof *axis;++i){char text[512];init(&f);snprintf(text,sizeof text,"{\"id\":1,\"placement_id\":10,\"mainAlong\":null,\"axes\":{\"u\":%s,\"v\":null}}",axis[i]);CHECK(!restore(&f,text));CHECK(!strcmp(f.error,error[i]));}
    char text[1024];init(&f);
    snprintf(text,sizeof text,"{\"id\":1,\"placement_id\":10,\"mainAlong\":null,\"axes\":{\"u\":{\"kind\":\"series\",\"start\":0,\"step\":1,\"count\":%u},\"v\":null}}",(unsigned)WOOD_GRID_MAX_LINES+1);
    CHECK(!restore(&f,text));CHECK(!strcmp(f.error,"I36: invalid series axis"));init(&f);
    snprintf(text,sizeof text,"{\"id\":1,\"placement_id\":10,\"mainAlong\":null,\"axes\":{\"u\":{\"kind\":\"explicit\",\"coords\":[%lld]},\"v\":null}}",(long long)GEO_COORD_LIMIT+1);
    CHECK(!restore(&f,text));CHECK(!strcmp(f.error,"I36: invalid grid coordinate"));init(&f);
    size_t used=(size_t)snprintf(text,sizeof text,"{\"id\":1,\"placement_id\":10,\"mainAlong\":null,\"axes\":{\"u\":{\"kind\":\"explicit\",\"coords\":[");
    for(size_t k=0;k<=WOOD_GRID_MAX_LINES;++k)used+=(size_t)snprintf(text+used,sizeof text-used,"%s%u",k?",":"",(unsigned)k);
    snprintf(text+used,sizeof text-used,"]},\"v\":null}}");CHECK(!restore(&f,text));CHECK(!strcmp(f.error,"I10: grid coordinate capacity exceeded"));
    return 0;
}
static int candidate(void)
{
    Fixture original,after;init(&original);EngApplication a=application();EngMethodVersion m=method();a.anchor_kind[0]=2;a.anchor_kind[1]=3;
    memcpy(&after,&original,sizeof after);wire(&after);after.context.before=&original.context;after.facts.bounds=(GeoRect2){300,400,900,1200};
    CHECK(bind(&after,"{\"create\":true}",1,&a,&m));CHECK(after.grids.items[0].axis[0].anchor==300&&after.grids.items[0].axis[1].anchor==1200);
    CHECK(original.grids.count==0&&original.eng.binding_count==0&&original.facts.calls==0&&original.error[0]==0);
    WoodGridState grids=original.grids;EngineeringState eng=original.eng;
    memcpy(&after,&original,sizeof after);wire(&after);after.context.before=&original.context;
    CHECK(!bind(&after,"{\"create\":true,\"anchors\":{\"u\":50,\"v\":true}}",1,&a,&m));
    CHECK(!strcmp(after.error,"D28: grid anchor must be integer mm in D1 range"));CHECK(after.eng.binding_count==2&&after.grids.count==1);
    CHECK(!memcmp(&original.grids,&grids,sizeof grids)&&!memcmp(&original.eng,&eng,sizeof eng)&&original.error[0]==0&&original.facts.calls==0);
    memcpy(&after,&original,sizeof after);wire(&after);after.facts.missing=true;
    CHECK(!restore(&after,"{\"id\":1,\"placement_id\":10,\"mainAlong\":null,\"axes\":{\"u\":null,\"v\":null}}"));
    CHECK(!strcmp(after.error,"I36: invalid engineering grid declaration"));CHECK(original.error[0]==0&&original.facts.calls==0);
    CHECK(!memcmp(&original.grids,&grids,sizeof grids)&&!memcmp(&original.eng,&eng,sizeof eng));return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"admission"))return admission();if(!strcmp(argv[1],"create-update"))return create_update();
    if(!strcmp(argv[1],"anchors"))return anchors();if(!strcmp(argv[1],"dimensions"))return dimensions();
    if(!strcmp(argv[1],"binding-capacity"))return binding_capacity();if(!strcmp(argv[1],"restore-axes"))return restore_axes();
    if(!strcmp(argv[1],"restore-errors"))return restore_errors();if(!strcmp(argv[1],"candidate"))return candidate();return 2;
}
