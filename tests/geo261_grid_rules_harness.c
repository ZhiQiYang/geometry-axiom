/* Public W client: no application World, command parser or global baseline. */
#include "grid_application.h"
#include <limits.h>
#include <stdio.h>
#include <string.h>

#define CHECK(value) do { if(!(value)){fprintf(stderr,"%s:%d\n",__func__,__LINE__);return 1;} } while(0)
typedef struct {
    WoodGridReference references[4];size_t reference_count;
    bool missing_host,missing_vertex;
} Facts;
static bool reference(void *opaque,size_t index,WoodGridReference *out)
{
    Facts *facts=opaque;if(index>=facts->reference_count)return false;
    *out=facts->references[index];return true;
}
static bool host(void *opaque,uint32_t id,WoodGridHost *out)
{
    Facts *facts=opaque;if(facts->missing_host || id!=0)return false;
    memset(out,0,sizeof *out);out->id=0;out->boundary_id=71;return true;
}
static bool vertex(void *opaque,uint32_t boundary,uint32_t key,GeoPoint2 *out)
{
    Facts *facts=opaque;if(facts->missing_vertex || boundary!=71 || key!=902)return false;
    *out=(GeoPoint2){400,500};return true;
}
static GeoGridSystem system_value(void)
{
    GeoGridSystem s={0};s.id=5;strcpy(s.name,"source");s.next_rule_key=8;s.rule_count=1;
    for(int a=0;a<2;++a)s.axis[a].source=GEO_GRID_SOURCE_REPEAT;
    s.axis[0].start=7;s.axis[0].step=120;s.axis[1].start=-11;s.axis[1].step=80;
    s.rules[0].key=7;strcpy(s.rules[0].name,"rule");s.rules[0].all_cells=true;
    s.rules[0].divisions[0]=3;s.rules[0].divisions[1]=2;return s;
}
static WoodGridContext context(WoodGridState *state,GeoGridStore *sources,Facts *facts)
{
    WoodGridContext c={0};c.state=state;c.sources=sources;c.user=facts;
    c.reference=reference;c.host=host;c.vertex=vertex;return c;
}
static bool fixture(WoodGridContext *c)
{
    GeoGridSystem s=system_value();
    GeoGridBinding b={0};b.id=11;b.boundary_id=71;b.system_id=5;b.vertex_key=902;
    b.cell[0]=-2;b.cell[1]=-3;b.anchor_num[0]=1;b.anchor_den[0]=2;b.anchor_num[1]=1;b.anchor_den[1]=4;
    WoodGridApplication g={0};g.id=9;g.placement_id=0;g.from_binding=true;g.binding_id=11;
    return wood_grid_source_put(c,&s,2)&&geo_grid_bindings_put(c->sources,&b)&&wood_grid_stage(c->state,&g);
}
static int references(void)
{
    WoodGridState state={0};Facts facts={0};WoodGridContext c=context(&state,NULL,&facts);
    facts.references[0]=(WoodGridReference){.kind=WOOD_GRID_REFERENCE_GUIDE,.active=true,
        .expression="10+gridrule:9:5:7:-2:+3:u:1-20"};facts.reference_count=1;
    CHECK(wood_grid_rule_used(&c,5,7));CHECK(!wood_grid_rule_used(&c,5,8));
    CHECK(!wood_grid_rule_used(&c,6,7));
    facts.references[0].expression="gridrule:9:5:7:-9223372036854775809:3:u:1";
    CHECK(!wood_grid_rule_used(&c,5,7));
    facts.references[0].expression="gridrule:9:5:7:-9223372036854775808:3:u:1+gridrule:9:6:8:0:0:v:0";
    CHECK(wood_grid_rule_used(&c,5,7));CHECK(wood_grid_rule_used(&c,6,8));
    facts.references[0].expression="gridrule:9:5:0:0:0:u:1";CHECK(!wood_grid_rule_used(&c,5,0));
    facts.references[0].expression="gridrule:9:5:7:0:0:w:1";CHECK(!wood_grid_rule_used(&c,5,7));
    facts.references[0].expression="gridrule:9:5:7:0:0:u:4294967296";CHECK(!wood_grid_rule_used(&c,5,7));
    facts.references[0].expression="gridrule:9:5:7:0:0:u:0:extra";CHECK(!wood_grid_rule_used(&c,5,7));
    facts.references[1]=(WoodGridReference){.kind=WOOD_GRID_REFERENCE_TIMBER,.active=false,.is_rule=true,
        .rule={.system_id=5,.rule_key=7}};facts.reference_count=2;
    CHECK(!wood_grid_rule_used(&c,5,7));facts.references[1].active=true;CHECK(wood_grid_rule_used(&c,5,7));
    facts.references[1].is_rule=false;CHECK(!wood_grid_rule_used(&c,5,7));return 0;
}
static int edits(void)
{
    GeoGridStore *store=geo_grid_store_create();CHECK(store);
    WoodGridState state={0};Facts facts={0};WoodGridContext c=context(&state,store,&facts);CHECK(fixture(&c));
    facts.references[0]=(WoodGridReference){.kind=WOOD_GRID_REFERENCE_GUIDE,.active=true,.expression="gridrule:9:5:7:0:0:u:0"};facts.reference_count=1;
    GeoGridRule changed=system_value().rules[0];char error[256]="";
    strcpy(changed.name,"renamed");CHECK(wood_grid_rule_edit(&c,5,&changed,false,false,false,error,sizeof error));
    CHECK(!strcmp(geo_grid_rule_find(geo_grid_systems_find(store,5),7)->name,"renamed"));
    CHECK(geo_grid_systems_find(store,5)->next_rule_key==8 && wood_grid_source_main_along(&state,5)==2);
    GeoGridSystem snapshot;memcpy(&snapshot,geo_grid_systems_find(store,5),sizeof snapshot);changed.divisions[0]=2;
    CHECK(!wood_grid_rule_edit(&c,5,&changed,false,false,false,error,sizeof error));
    CHECK(!strcmp(error,"I25a: RULE_REFERENCED source 5 rule 7"));
    CHECK(!memcmp(geo_grid_systems_find(store,5),&snapshot,sizeof snapshot));
    changed=snapshot.rules[0];changed.all_cells=false;CHECK(!wood_grid_rule_change_allowed(&c,5,7,&changed,false,error,sizeof error));
    CHECK(!wood_grid_rule_edit(&c,5,&changed,false,true,false,error,sizeof error));
    CHECK(!memcmp(geo_grid_systems_find(store,5),&snapshot,sizeof snapshot));
    facts.reference_count=0;CHECK(wood_grid_rule_edit(&c,5,&changed,false,true,false,error,sizeof error));
    CHECK(geo_grid_systems_find(store,5)->rule_count==0 && geo_grid_systems_find(store,5)->next_rule_key==8);
    changed.key=0;changed.all_cells=true;CHECK(wood_grid_rule_edit(&c,5,&changed,true,false,false,error,sizeof error));
    CHECK(geo_grid_systems_find(store,5)->rules[0].key==8 && geo_grid_systems_find(store,5)->next_rule_key==9);
    CHECK(wood_grid_source_main_along(&state,5)==2);
    uint32_t key=0;CHECK(!wood_grid_rule_edit_begin(&c,5,0,true,false,true,&key,error,sizeof error));
    CHECK(!strcmp(error,"I25a: RULE_KEY_EXHAUSTED or create in scene"));
    CHECK(!wood_grid_rule_edit_begin(&c,5,77,false,true,false,&key,error,sizeof error));CHECK(!strcmp(error,"I25a: RULE_MISSING"));
    GeoGridSystem max=*geo_grid_systems_find(store,5);max.rule_count=0;max.next_rule_key=UINT32_MAX;CHECK(wood_grid_source_put(&c,&max,2));
    CHECK(wood_grid_rule_edit(&c,5,&changed,true,false,false,error,sizeof error));
    CHECK(geo_grid_systems_find(store,5)->rules[0].key==UINT32_MAX && geo_grid_systems_find(store,5)->next_rule_key==0);
    CHECK(!wood_grid_rule_edit_begin(&c,5,0,true,false,false,&key,error,sizeof error));
    geo_grid_store_destroy(store);return 0;
}
static int world(void)
{
    GeoGridStore *original=geo_grid_store_create();CHECK(original);
    WoodGridState before_state={0},after_state={0};Facts before_facts={0},after_facts={0};
    WoodGridContext before=context(&before_state,original,&before_facts);CHECK(fixture(&before));
    before_facts.references[0]=(WoodGridReference){.kind=WOOD_GRID_REFERENCE_GUIDE,.active=true,.expression="gridrule:9:5:7:0:0:u:0"};before_facts.reference_count=1;
    GeoGridStore *candidate=geo_grid_store_clone(original);CHECK(candidate);after_state=before_state;
    WoodGridContext after=context(&after_state,candidate,&after_facts);after.before=&before;
    GeoGridSystem changed=*geo_grid_systems_find(candidate,5);changed.rules[0].divisions[0]=2;CHECK(wood_grid_source_put(&after,&changed,2));
    WoodGridApplication child={0};child.id=22;child.parent_id=9;child.is_subgrid=true;child.lattice_cell=true;
    child.lattice_cell_index[0]=-2;child.lattice_cell_index[1]=-3;CHECK(wood_grid_stage(&after_state,&child));
    char error[256]="";CHECK(!wood_grid_rules_world_valid(&after,error,sizeof error));
    CHECK(!strcmp(error,"I25a: RULE_REFERENCED source 5 rule 7"));
    changed=system_value();CHECK(wood_grid_source_put(&after,&changed,2));
    CHECK(!wood_grid_rules_world_valid(&after,error,sizeof error));
    CHECK(!strcmp(error,"I25a: MANUAL_CONFLICT source 5 rule 7 manual 22 parent 9 cell (-2,-3)"));
    --after_state.count;CHECK(wood_grid_rules_world_valid(&after,error,sizeof error));
    CHECK(wood_grid_source_remove(&after,5));CHECK(!wood_grid_rules_world_valid(&after,error,sizeof error));
    CHECK(!strcmp(error,"I25a: RULE_REFERENCED source 5 rule 7"));
    CHECK(geo_grid_systems_find(original,5)->rules[0].divisions[0]==3);
    after.before=NULL;CHECK(wood_grid_rules_world_valid(&after,error,sizeof error));
    geo_grid_store_destroy(candidate);geo_grid_store_destroy(original);return 0;
}
static int geometry(void)
{
    GeoGridStore *store=geo_grid_store_create();CHECK(store);WoodGridState state={0};Facts facts={0};
    WoodGridContext c=context(&state,store,&facts);CHECK(fixture(&c));char error[256]="";WoodGridRuleTarget target;
    int64_t cell[2]={-2,3};CHECK(wood_grid_rule_cell(&c,"system",5,7,cell,&target,error,sizeof error));
    CHECK(target.bounds.min_u==-233 && target.bounds.max_u==-113 && target.bounds.min_v==229 && target.bounds.max_v==309);
    CHECK(!target.has_placement && !target.has_boundary);
    cell[1]=-3;CHECK(wood_grid_rule_cell(&c,"binding",11,7,cell,&target,error,sizeof error));
    CHECK(target.bounds.min_u==340 && target.bounds.max_u==460 && target.bounds.min_v==480 && target.bounds.max_v==560);
    CHECK(!target.has_placement && target.has_boundary && target.boundary_id==71);
    CHECK(wood_grid_rule_cell(&c,"grid",9,7,cell,&target,error,sizeof error));
    CHECK(target.has_placement && target.placement_id==0 && target.has_boundary);
    GeoGridRuleLineRef ref={.grid_id=9,.system_id=5,.rule_key=7,.cell={-2,-3},.axis=0,.inner_index=1};
    GeoCoord coordinate=999;GeoRect2 scope;CHECK(wood_grid_rule_line(&c,&ref,0,&coordinate,&scope,error,sizeof error));
    CHECK(coordinate==420 && scope.min_u==340 && scope.max_v==560);
    ref.axis=1;ref.inner_index=0;CHECK(wood_grid_rule_line(&c,&ref,0,&coordinate,&scope,error,sizeof error));CHECK(coordinate==520);
    CHECK(!wood_grid_rule_line(&c,&ref,1,&coordinate,&scope,error,sizeof error));CHECK(!strcmp(error,"I25a: WRONG_SOURCE source 5 rule 7"));
    ref.axis=0;ref.inner_index=2;CHECK(!wood_grid_rule_line(&c,&ref,0,&coordinate,&scope,error,sizeof error));CHECK(!strcmp(error,"I25a: INDEX_RANGE source 5 rule 7"));
    ref.system_id=6;ref.rule_key=99;CHECK(!wood_grid_rule_line(&c,&ref,0,&coordinate,&scope,error,sizeof error));CHECK(!strcmp(error,"I25a: RULE_MISSING source 5 rule 99"));
    cell[0]=INT64_MAX;CHECK(!wood_grid_rule_cell(&c,"system",5,7,cell,&target,error,sizeof error));CHECK(!strcmp(error,"I25a: CELL_RANGE source 5 rule 7"));
    facts.missing_host=true;facts.missing_vertex=true;CHECK(!wood_grid_rule_target(&c,"grid",9,&target,error,sizeof error));CHECK(!strcmp(error,"I25a: WRONG_SOURCE source 0 rule 0"));
    facts.missing_host=false;CHECK(!wood_grid_rule_target(&c,"grid",9,&target,error,sizeof error));CHECK(!strcmp(error,"D30/I37: grid-binding needs an existing boundary vertex and two infinite axes"));
    geo_grid_store_destroy(store);return 0;
}
static int validation(void)
{
    GeoGridSystem s=system_value();char error[256]="";CHECK(wood_grid_rules_valid(&s,error,sizeof error));
    s.axis[0].source=GEO_GRID_SOURCE_REPEAT_BODY_GAP;s.rules[0].divisions[0]=0;
    CHECK(!wood_grid_rules_valid(&s,error,sizeof error));CHECK(!strcmp(error,"I25a: SOURCE_KIND source 5 rule 0"));
    s=system_value();s.rules[0].divisions[0]=7;CHECK(!wood_grid_rules_valid(&s,error,sizeof error));CHECK(!strcmp(error,"I25a: DIVISION_NOT_EXACT source 5 rule 7"));
    s=system_value();s.rule_count=2;s.next_rule_key=9;s.rules[1]=s.rules[0];s.rules[1].key=8;
    CHECK(!wood_grid_rules_valid(&s,error,sizeof error));CHECK(!strcmp(error,"I25a: RULE_OVERLAP source 5 rules 7/8"));return 0;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"references"))return references();
    if(!strcmp(argv[1],"edits"))return edits();
    if(!strcmp(argv[1],"world"))return world();
    if(!strcmp(argv[1],"geometry"))return geometry();
    if(!strcmp(argv[1],"validation"))return validation();return 2;
}
