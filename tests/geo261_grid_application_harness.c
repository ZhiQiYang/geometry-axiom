/* Public woodworking grid client with isolated stores and candidate facts. */
#include "grid_application.h"
#include <stdio.h>
#include <string.h>

#define CHECK(value) do { if(!(value)){fprintf(stderr,"ASSERT:%s:%d\n",__func__,__LINE__);return 1;} } while(0)
#define CHECK_NAMED(value,label) do { if(!(value)){fprintf(stderr,"ASSERT:%s\n",label);return 1;} } while(0)
typedef struct {
    bool missing_host,missing_vertex;
    GeoPoint2 point;
    WoodGridReference refs[4];size_t ref_count;
} Facts;
static bool host(void *opaque,uint32_t id,WoodGridHost *out)
{
    Facts *facts=opaque;if(facts->missing_host)return false;
    memset(out,0,sizeof *out);out->id=id;out->boundary_id=71;
    out->bounds=(GeoRect2){0,0,200,200};out->bounds_valid=true;
    out->component_count=1;out->components[0].outline.count=4;
    GeoPoint2 vertices[4]={{0,0},{200,0},{200,200},{0,200}};
    memcpy(out->components[0].outline.v,vertices,sizeof vertices);return true;
}
static bool vertex(void *opaque,uint32_t boundary,uint32_t key,GeoPoint2 *out)
{
    Facts *facts=opaque;if(facts->missing_vertex||boundary!=71||key!=902)return false;
    *out=facts->point;return true;
}
static bool reference(void *opaque,size_t index,WoodGridReference *out)
{Facts *facts=opaque;if(index>=facts->ref_count)return false;*out=facts->refs[index];return true;}
static WoodGridContext context(WoodGridState *state,GeoGridStore *sources,EngineeringState *eng,Facts *facts)
{
    WoodGridContext c={0};c.state=state;c.sources=sources;c.user=facts;c.host=host;c.vertex=vertex;
    c.reference=reference;c.engineering.state=eng;return c;
}
static GeoGridSystem system_value(uint32_t id,bool infinite)
{
    GeoGridSystem s={0};s.id=id;s.next_rule_key=1;strcpy(s.name,"grid");
    for(int a=0;a<2;++a){s.axis[a].source=infinite?GEO_GRID_SOURCE_REPEAT:GEO_GRID_SOURCE_SERIES;
        s.axis[a].step=100;s.axis[a].series_count=infinite?0:3;}
    return s;
}
static WoodGridApplication direct_value(uint32_t id,uint32_t pid)
{
    WoodGridApplication g={0};g.id=id;g.placement_id=pid;
    for(int a=0;a<2;++a){g.axis[a].source=GEO_GRID_SOURCE_SERIES;g.axis[a].step=100;g.axis[a].series_count=3;}
    return g;
}
static GeoGridBinding binding_value(uint32_t id,uint32_t sid)
{
    GeoGridBinding b={0};b.id=id;b.system_id=sid;b.boundary_id=71;b.vertex_key=902;
    b.anchor_den[0]=b.anchor_den[1]=1;return b;
}
static int roles(void)
{
    GeoGridStore *store=geo_grid_store_create();CHECK(store);WoodGridState state={0};EngineeringState eng={0};Facts facts={0};
    WoodGridContext c=context(&state,store,&eng,&facts);GeoGridSystem five=system_value(5,false),nine=system_value(9,false),seven=system_value(7,false);
    CHECK(wood_grid_source_put(&c,&five,1));CHECK(wood_grid_source_put(&c,&nine,2));
    CHECK(geo_grid_systems_remove(store,5));CHECK(geo_grid_systems_at(store,0)->id==9);
    CHECK(wood_grid_source_main_along(&state,9)==2);CHECK(geo_grid_systems_put(store,&seven));
    CHECK(wood_grid_source_main_along(&state,7)==0);CHECK(wood_grid_source_main_along(&state,9)==2);
    CHECK(geo_grid_systems_put(store,&five));CHECK(wood_grid_source_main_along(&state,5)==1);
    CHECK(wood_grid_source_put(&c,&seven,1));CHECK(wood_grid_source_remove(&c,9));
    CHECK(wood_grid_source_main_along(&state,7)==1 && wood_grid_source_main_along(&state,5)==1);
    CHECK(wood_grid_source_main_along(&state,9)==0);GeoGridStoreError detail;
    seven.axis[0].start=10;CHECK(wood_grid_source_redeclare(&c,&seven,2,&detail));
    CHECK(wood_grid_source_main_along(&state,7)==2 && wood_grid_source_main_along(&state,5)==1);
    GeoGridSystem before;memcpy(&before,geo_grid_systems_find(store,7),sizeof before);
    WoodGridState before_state;memcpy(&before_state,&state,sizeof before_state);
    seven=system_value(7,true);CHECK(!wood_grid_source_redeclare(&c,&seven,1,&detail));CHECK(detail.status==GEO_GRID_STORE_SPACE_CHANGE);
    CHECK(!memcmp(geo_grid_systems_find(store,7),&before,sizeof before));CHECK(!memcmp(&state,&before_state,sizeof state));
    geo_grid_store_destroy(store);
    store=geo_grid_store_create();CHECK(store);memset(&state,0,sizeof state);c.sources=store;
    for(uint32_t i=0;i<GEO_GRID_SYSTEM_CAPACITY;++i){GeoGridSystem s=system_value(i,false);CHECK(wood_grid_source_put(&c,&s,i%3));}
    CHECK(geo_grid_systems_remove(store,0));memcpy(&before_state,&state,sizeof before_state);
    GeoGridSystem extra=system_value(100,false);CHECK(!wood_grid_source_redeclare(&c,&extra,2,&detail));
    CHECK(detail.status==GEO_GRID_STORE_CAPACITY);
    CHECK(!geo_grid_systems_find(store,100));CHECK(geo_grid_systems_count(store)==15);CHECK(!memcmp(&state,&before_state,sizeof state));
    geo_grid_store_destroy(store);return 0;
}
static int direct(void)
{
    GeoGridStore *store=geo_grid_store_create();CHECK(store);WoodGridState state={0};EngineeringState eng={0};Facts facts={0};
    WoodGridContext c=context(&state,store,&eng,&facts);WoodGridApplication g=direct_value(1,10),out={0};char error[256]="";
    g.from_system=true;g.system_id=5;CHECK(wood_grid_stage(&state,&g));WoodGridState snapshot;memcpy(&snapshot,&state,sizeof snapshot);
    CHECK_NAMED(!wood_grid_begin_direct(&c,1,10,&out,error,sizeof error),"grid-direct-source-lock");
    CHECK(!strcmp(error,"D29: edit the grid-system source or its application origin; direct axis edits are not allowed"));
    CHECK(!memcmp(&state,&snapshot,sizeof state));g.from_system=false;g.is_subgrid=true;CHECK(wood_grid_stage(&state,&g));
    CHECK(!wood_grid_begin_direct(&c,1,10,&out,error,sizeof error));CHECK(!strcmp(error,"D19：不能將既有子網格改成主網格"));
    g.is_subgrid=false;CHECK(wood_grid_stage(&state,&g));CHECK(!wood_grid_begin_direct(&c,1,11,&out,error,sizeof error));
    CHECK(!strcmp(error,"這個 grid id 已經用在別的承載面"));CHECK(!wood_grid_begin_direct(&c,2,10,&out,error,sizeof error));
    CHECK(!strcmp(error,"這片承載面已經有一座網格（一面一格）"));
    CHECK(wood_grid_begin_direct(&c,1,10,&out,error,sizeof error));CHECK(out.id==g.id && out.placement_id==g.placement_id && out.axis[0].step==100 && out.axis[1].series_count==3);
    CHECK(wood_grid_direct_declared(&c,&out,0,true,error,sizeof error));
    CHECK(wood_grid_begin_direct(&c,2,11,&out,error,sizeof error));CHECK(!wood_grid_direct_declared(&c,&out,0,true,error,sizeof error));
    CHECK(!strcmp(error,"新網格至少要一個格線來源"));out.main_along=1;out.axis[0]=g.axis[0];
    CHECK(!wood_grid_direct_declared(&c,&out,1,true,error,sizeof error));CHECK(!strcmp(error,"grid 主支方向沒有對應的格線來源"));
    out.axis[1]=g.axis[1];CHECK(wood_grid_direct_declared(&c,&out,1,true,error,sizeof error));CHECK(wood_grid_direct_check(&c,&out,error,sizeof error));
    out.axis[0].start=-1;CHECK(!wood_grid_direct_check(&c,&out,error,sizeof error));CHECK(strstr(error,"grid 座標不合法（u 軸）")!=NULL);
    for(uint32_t i=2;i<=WOOD_GRID_MAX;++i){g=direct_value(i,10+i);CHECK(wood_grid_stage(&state,&g));}
    memcpy(&snapshot,&state,sizeof snapshot);CHECK(!wood_grid_begin_direct(&c,99,99,&out,error,sizeof error));CHECK(!strcmp(error,"網格的數量超過上限"));
    CHECK(!memcmp(&state,&snapshot,sizeof state));geo_grid_store_destroy(store);return 0;
}
static int admission(void)
{
    GeoGridStore *store=geo_grid_store_create();CHECK(store);WoodGridState state={0};EngineeringState eng={0};Facts facts={0};
    WoodGridContext c=context(&state,store,&eng,&facts);GeoGridSystem s=system_value(5,false);CHECK(wood_grid_source_put(&c,&s,1));
    WoodGridApplication g={0};g.id=1;g.placement_id=10;g.system_id=5;char error[256]="";
    eng.binding_count=1;eng.bindings[0].target=(EngTarget){0,1,0,0};facts.missing_host=true;WoodGridState snapshot;memcpy(&snapshot,&state,sizeof snapshot);
    CHECK(!wood_grid_apply_system(&c,&g,error,sizeof error));CHECK(!strcmp(error,"I37: grid application needs an existing surface and grid-system"));
    facts.missing_host=false;CHECK_NAMED(!wood_grid_apply_system(&c,&g,error,sizeof error),"grid-engineering-source-lock");
    CHECK(!strcmp(error,"D29/I37: detach engineering bindings before choosing a grid-system source"));CHECK(!memcmp(&state,&snapshot,sizeof state));
    eng.binding_count=0;CHECK(wood_grid_apply_system(&c,&g,error,sizeof error));CHECK(state.count==1 && state.items[0].from_system);
    memcpy(&snapshot,&state,sizeof snapshot);g.placement_id=11;CHECK(!wood_grid_apply_system(&c,&g,error,sizeof error));
    CHECK(!strcmp(error,"I37: cannot change a subgrid or move an existing grid identity to another surface"));CHECK(!memcmp(&state,&snapshot,sizeof state));
    g.id=2;g.placement_id=10;CHECK(!wood_grid_apply_system(&c,&g,error,sizeof error));CHECK(!strcmp(error,"I10: this surface already has a main grid"));
    CHECK(!memcmp(&state,&snapshot,sizeof state));g.id=1;g.binding_id=11;g.system_id=0;
    CHECK(!wood_grid_apply_binding(&c,&g,error,sizeof error));CHECK(!strcmp(error,"D30/I37: from-binding requires an available lattice grid identity and the binding's boundary placement"));
    CHECK(!memcmp(&state,&snapshot,sizeof state));g.id=3;g.placement_id=12;
    eng.binding_count=1;eng.bindings[0].target.id=3;CHECK(!wood_grid_apply_binding(&c,&g,error,sizeof error));CHECK(!memcmp(&state,&snapshot,sizeof state));
    eng.binding_count=0;CHECK(wood_grid_apply_binding(&c,&g,error,sizeof error));CHECK(state.count==2 && state.items[1].from_binding);
    memcpy(&snapshot,&state,sizeof snapshot);g.system_id=5;CHECK(!wood_grid_apply_system(&c,&g,error,sizeof error));CHECK(!memcmp(&state,&snapshot,sizeof state));
    for(uint32_t i=4;state.count<WOOD_GRID_MAX;++i){WoodGridApplication next=direct_value(i,20+i);CHECK(wood_grid_stage(&state,&next));}
    memcpy(&snapshot,&state,sizeof snapshot);g.id=99;g.placement_id=99;g.from_binding=false;CHECK(!wood_grid_apply_system(&c,&g,error,sizeof error));CHECK(!strcmp(error,"I10: grid capacity exceeded"));
    CHECK(!memcmp(&state,&snapshot,sizeof state));CHECK(!wood_grid_apply_binding(&c,&g,error,sizeof error));CHECK(!memcmp(&state,&snapshot,sizeof state));
    geo_grid_store_destroy(store);return 0;
}
static int child(void)
{
    GeoGridStore *store=geo_grid_store_create();CHECK(store);WoodGridState state={0};EngineeringState eng={0};Facts facts={0};
    WoodGridContext c=context(&state,store,&eng,&facts);WoodGridApplication parent=direct_value(1,10),other=direct_value(3,11),g={0};
    CHECK(wood_grid_stage(&state,&parent));CHECK(wood_grid_stage(&state,&other));g.id=2;g.parent_id=1;
    for(int a=0;a<2;++a){g.cell_ref[a][0]=0;g.cell_ref[a][1]=1;}
    char error[256]="";CHECK(wood_grid_prepare_child(&c,&g,false,2,2,error,sizeof error));
    CHECK(g.is_subgrid && !g.lattice_cell && g.placement_id==10 && g.divisions[0]==2);
    CHECK(wood_grid_child_check(&c,&g,error,sizeof error));CHECK(wood_grid_stage(&state,&g));WoodGridState snapshot;memcpy(&snapshot,&state,sizeof snapshot);
    g.parent_id=3;WoodGridApplication unchanged;memcpy(&unchanged,&g,sizeof unchanged);CHECK_NAMED(!wood_grid_prepare_child(&c,&g,false,2,2,error,sizeof error),"grid-child-parent-lock");
    CHECK(!strcmp(error,"D19/I25：父格必須是主網格；既有網格的類型與父格編號不能更換"));CHECK(!memcmp(&g,&unchanged,sizeof g));CHECK(!memcmp(&state,&snapshot,sizeof state));
    g.parent_id=1;CHECK(!wood_grid_prepare_child(&c,&g,true,2,2,error,sizeof error));CHECK(!memcmp(&state,&snapshot,sizeof state));
    g.id=4;state.items[0].axis[0].stagger_set=true;
    CHECK(!wood_grid_prepare_child(&c,&g,true,2,2,error,sizeof error));CHECK(!strcmp(error,"I24：有相位差的主格不能建立子網格"));
    state.items[0].axis[0].stagger_set=false;CHECK(!wood_grid_prepare_child(&c,&g,true,2,2,error,sizeof error));
    CHECK(!strcmp(error,"D19/I25：子格 4 的父格 1 必須使用 cell 參照形式"));
    g.id=1;g.parent_id=3;CHECK(!wood_grid_prepare_child(&c,&g,false,2,2,error,sizeof error));
    g.id=4;g.parent_id=2;CHECK(!wood_grid_prepare_child(&c,&g,false,2,2,error,sizeof error));
    g.parent_id=1;CHECK(wood_grid_prepare_child(&c,&g,false,2,2,error,sizeof error));facts.missing_host=true;
    CHECK(!wood_grid_child_check(&c,&g,error,sizeof error));CHECK(!strcmp(error,"I25：找不到父格所屬的面"));
    geo_grid_store_destroy(store);return 0;
}
static int deletion(void)
{
    GeoGridStore *store=geo_grid_store_create();CHECK(store);WoodGridState state={0};EngineeringState eng={0};Facts facts={0};
    WoodGridContext c=context(&state,store,&eng,&facts);GeoGridSystem s=system_value(5,true);CHECK(wood_grid_source_put(&c,&s,2));
    GeoGridBinding b=binding_value(11,5);CHECK(geo_grid_bindings_put(store,&b));b=binding_value(12,99);CHECK(geo_grid_bindings_put(store,&b));
    char error[256]="";CHECK(!wood_grid_delete(&c,"grid-system",99,error,sizeof error));CHECK(!strcmp(error,"I37: grid-system is still referenced by a grid-binding"));
    CHECK(!wood_grid_delete(&c,"grid-system",5,error,sizeof error));CHECK(!strcmp(error,"I37: grid-system is still referenced by a grid-binding"));
    WoodGridApplication g=direct_value(9,10);g.from_binding=true;g.binding_id=11;CHECK(wood_grid_stage(&state,&g));
    CHECK(!wood_grid_delete(&c,"grid-binding",11,error,sizeof error));CHECK(!strcmp(error,"I37: grid-binding is still referenced by a grid"));
    WoodGridApplication child=direct_value(22,10);child.is_subgrid=true;child.parent_id=9;CHECK(wood_grid_stage(&state,&child));
    facts.refs[0]=(WoodGridReference){.kind=WOOD_GRID_REFERENCE_GUIDE,.id=77,.active=true,.expression="grid:9:u:0"};
    facts.refs[1]=(WoodGridReference){.kind=WOOD_GRID_REFERENCE_TIMBER,.id=88,.active=true,.grid_id=9};facts.ref_count=2;
    WoodGridState snapshot;memcpy(&snapshot,&state,sizeof snapshot);CHECK(!wood_grid_delete(&c,"grid",9,error,sizeof error));CHECK(!strcmp(error,"I23：網格 9 仍有子格 22，不能刪除"));CHECK(!memcmp(&state,&snapshot,sizeof state));
    CHECK(wood_grid_delete(&c,"grid",22,error,sizeof error));memcpy(&snapshot,&state,sizeof snapshot);
    CHECK(!wood_grid_delete(&c,"grid",9,error,sizeof error));CHECK_NAMED(!strcmp(error,"I23：網格 9 仍被參考線 77 引用，不能刪除"),"grid-guide-delete-before-timber");CHECK(!memcmp(&state,&snapshot,sizeof state));
    WoodGridReference first=facts.refs[0];facts.refs[0]=facts.refs[1];facts.refs[1]=first;
    CHECK(!wood_grid_delete(&c,"grid",9,error,sizeof error));CHECK_NAMED(!strcmp(error,"I23：網格 9 仍被參考線 77 引用，不能刪除"),"grid-guide-delete-order-is-template-policy");CHECK(!memcmp(&state,&snapshot,sizeof state));
    first=facts.refs[0];facts.refs[0]=facts.refs[1];facts.refs[1]=first;
    facts.refs[0].expression="prefixgrid:9:u:0";CHECK(!wood_grid_delete(&c,"grid",9,error,sizeof error));CHECK(!strcmp(error,"V_GRID_LOCKED：有角材錨在這個網格上，先刪角材（timber）"));
    facts.refs[0].expression="10*grid:9:u:0";CHECK(!wood_grid_delete(&c,"grid",9,error,sizeof error));CHECK(!strcmp(error,"I23：網格 9 仍被參考線 77 引用，不能刪除"));
    facts.refs[0].expression="gridrule:9:5:7:0:0:u:0";CHECK(!wood_grid_delete(&c,"grid",9,error,sizeof error));CHECK(strstr(error,"參考線 77")!=NULL);
    facts.refs[0].expression="grid:90:u:0";facts.refs[1].active=false;CHECK(wood_grid_delete(&c,"grid",9,error,sizeof error));CHECK(state.count==0);
    CHECK(wood_grid_delete(&c,"grid-binding",11,error,sizeof error));CHECK(wood_grid_delete(&c,"grid-system",5,error,sizeof error));CHECK(wood_grid_source_main_along(&state,5)==0);
    CHECK(!wood_grid_delete(&c,"grid",9,error,sizeof error));CHECK(!strcmp(error,"這個網格不存在"));
    CHECK(!wood_grid_delete(&c,"grid-binding",11,error,sizeof error));CHECK(!strcmp(error,"I37: grid-binding does not exist"));
    CHECK(!wood_grid_delete(&c,"grid-system",5,error,sizeof error));CHECK(!strcmp(error,"I37: grid-system does not exist"));
    geo_grid_store_destroy(store);return 0;
}
static int candidate(void)
{
    GeoGridStore *original=geo_grid_store_create();CHECK(original);WoodGridState old_state={0},new_state={0};EngineeringState eng={0};
    Facts old_facts={.point={400,500}},new_facts={.point={700,900}};
    WoodGridContext before=context(&old_state,original,&eng,&old_facts);GeoGridSystem s=system_value(5,true);CHECK(wood_grid_source_put(&before,&s,2));
    GeoGridBinding b=binding_value(11,5);CHECK(geo_grid_bindings_put(original,&b));WoodGridApplication g={0};g.id=9;g.placement_id=10;g.from_binding=true;g.binding_id=11;
    CHECK(wood_grid_stage(&old_state,&g));char error[256]="";CHECK(wood_grid_bindings_rebuild(&before,error,sizeof error));
    CHECK(old_state.items[0].lattice_base[0]==400 && old_state.items[0].lattice_base[1]==500);
    WoodGridState snapshot;memcpy(&snapshot,&old_state,sizeof snapshot);
    GeoGridSystem old_source;memcpy(&old_source,geo_grid_systems_find(original,5),sizeof old_source);
    GeoGridStore *copy=geo_grid_store_clone(original);CHECK(copy);memcpy(&new_state,&old_state,sizeof new_state);
    WoodGridContext after=context(&new_state,copy,&eng,&new_facts);after.before=&before;
    CHECK(wood_grid_bindings_rebuild(&after,error,sizeof error));CHECK(new_state.items[0].lattice_base[0]==700 && new_state.items[0].lattice_base[1]==900);
    CHECK(!memcmp(&old_state,&snapshot,sizeof snapshot));CHECK(!memcmp(geo_grid_systems_find(original,5),&old_source,sizeof old_source));
    new_facts.missing_vertex=true;CHECK(!wood_grid_bindings_rebuild(&after,error,sizeof error));
    CHECK(!strcmp(error,"D30/I37: grid-binding needs an existing boundary vertex and two infinite axes"));CHECK(!memcmp(&old_state,&snapshot,sizeof snapshot));
    new_facts.missing_host=true;g.id=10;g.system_id=5;g.placement_id=11;WoodGridState before_rejection;memcpy(&before_rejection,&new_state,sizeof before_rejection);
    CHECK(!wood_grid_apply_system(&after,&g,error,sizeof error));CHECK(!strcmp(error,"I37: grid application needs an existing surface and grid-system"));
    CHECK(!memcmp(&new_state,&before_rejection,sizeof new_state));CHECK(!memcmp(&old_state,&snapshot,sizeof snapshot));
    geo_grid_store_destroy(copy);geo_grid_store_destroy(original);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"roles"))return roles();if(!strcmp(argv[1],"direct"))return direct();
    if(!strcmp(argv[1],"admission"))return admission();if(!strcmp(argv[1],"child"))return child();
    if(!strcmp(argv[1],"deletion"))return deletion();if(!strcmp(argv[1],"candidate"))return candidate();return 2;
}
