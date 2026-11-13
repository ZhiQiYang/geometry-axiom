#include "world_validation.h"
#include <stdio.h>
#include <string.h>
#define CHECK(c,n) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",n);return 1;}}while(0)
typedef struct {
    WoodGridState grids;WoodMember members[3];WoodWorldMemberFact facts[3];GeoRect2 rectangles[3];size_t count;
    bool host_ok,place_ok,footprint_ok,end_ok,role_ok;int stop_mode;
    unsigned placed_probes,end_calls,role_calls;bool probe_was_placed;
} Fixture;
static bool member_at(void *user,size_t i,WoodWorldMemberFact *out)
{Fixture *f=user;if(i>=f->count)return false;*out=f->facts[i];return true;}
static uint32_t placement_id(void *user,size_t i){(void)user;return (uint32_t)(10+i);}
static bool host(void *user,uint32_t id,const GeoRect2 *rect,WoodGridHost *out)
{
    Fixture *f=user;(void)rect;memset(out,0,sizeof *out);out->id=id;out->boundary_id=71;
    out->bounds=(GeoRect2){0,0,1000,1000};out->bounds_valid=true;out->component_count=1;
    WoodBoundaryRegion *part=&out->components[0];part->id=71;part->outline.count=4;
    part->outline.v[0]=(GeoPoint2){0,0};part->outline.v[1]=(GeoPoint2){1000,0};
    part->outline.v[2]=(GeoPoint2){1000,1000};part->outline.v[3]=(GeoPoint2){0,1000};
    for(size_t i=0;i<4;++i)part->outline.fixity[i]=WOOD_EDGE_FIXED;
    return f->host_ok&&id!=999;
}
static bool grid_host(void *user,uint32_t id,WoodGridHost *out){return host(user,id,NULL,out);}
static bool vertex(void *user,uint32_t boundary,uint32_t key,GeoPoint2 *out)
{(void)user;if(boundary!=71||key!=902)return false;*out=(GeoPoint2){0,0};return true;}
static bool footprint(void *user,size_t i,uint32_t id,GeoRect2 *out)
{Fixture *f=user;(void)id;*out=f->rectangles[i];return f->footprint_ok;}
static bool place(void *user,uint32_t id,WoodMember *member,GeoPoint2 uv,int direction,int depth)
{Fixture *f=user;(void)id;(void)uv;(void)direction;(void)depth;++f->placed_probes;f->probe_was_placed=member->placed;return f->place_ok;}
static size_t stops(void *user,uint32_t id,const GeoRect2 *r,bool along_v,const WoodMember *excluded,WoodStopFace *out,size_t capacity)
{
    Fixture *f=user;(void)id;(void)excluded;(void)capacity;if(!f->stop_mode)return 0;
    GeoCoord lo=along_v?r->min_u:r->min_v,hi=along_v?r->max_u:r->max_v;
    out[0]=(WoodStopFace){WOOD_STOP_OUTLINE_EDGE,1,0,-1,0,f->stop_mode==3?WOOD_STOP_FREE:WOOD_STOP_FIXED,along_v?r->min_v:r->min_u,lo,hi};
    out[1]=(WoodStopFace){WOOD_STOP_OUTLINE_EDGE,1,0,-1,1,WOOD_STOP_FIXED,along_v?r->max_v:r->max_u,lo,hi};
    if(f->stop_mode==2){out[2]=out[0];out[2].kind=WOOD_STOP_HOLE_EDGE;out[2].hole_index=0;return 3;}return 2;
}
static bool ends(void *user,uint32_t id,const GeoRect2 *r,const WoodMember *member,bool along_v,char *error,size_t cap)
{Fixture *f=user;(void)id;(void)r;(void)member;(void)along_v;++f->end_calls;if(!f->end_ok)snprintf(error,cap,"end-first");return f->end_ok;}
static bool role(void *user,uint32_t id,const GeoRect2 *r,const WoodMember *member,bool along_v,char *error,size_t cap)
{Fixture *f=user;(void)id;(void)r;(void)member;(void)along_v;++f->role_calls;if(!f->role_ok)snprintf(error,cap,"role-second");return f->role_ok;}
static WoodWorldValidationContext setup(Fixture *f)
{
    memset(f,0,sizeof *f);f->count=1;f->host_ok=f->place_ok=f->footprint_ok=f->end_ok=f->role_ok=true;f->stop_mode=1;
    for(size_t i=0;i<3;++i){f->members[i].id=(uint32_t)(i+1);f->members[i].placed=true;f->members[i].role=WOOD_MEMBER_ROLE_PRIMARY;
        f->facts[i]=(WoodWorldMemberFact){.member=&f->members[i],.placement_id=10,.length_direction=GEO_DIRECTION_POS_U};
        f->rectangles[i]=(GeoRect2){(GeoCoord)(i*100),0,(GeoCoord)((i+1)*100),20};}
    WoodWorldValidationContext c={0};c.grids.state=&f->grids;c.grids.user=f;c.grids.host=grid_host;c.grids.vertex=vertex;
    c.user=f;c.member_count=f->count;c.placement_count=2;
    c.member_at=member_at;c.placement_id=placement_id;c.host=host;c.footprint=footprint;c.place=place;c.stops=stops;c.end_faces=ends;c.boundary_role=role;return c;
}
static int support(void)
{
    Fixture f;WoodWorldValidationContext c=setup(&f);char error[256]="sentinel";WoodMember before[3];memcpy(before,f.members,sizeof before);
    CHECK(wood_world_validate_members(&c,error,sizeof error)&&!strcmp(error,"sentinel"),"validation-baseline");
    CHECK(!f.probe_was_placed&&f.placed_probes==1&&!memcmp(before,f.members,sizeof before),"validation-local-probe");
    f.stop_mode=2;CHECK(!wood_world_validate_members(&c,error,sizeof error)&&strstr(error,"R6(d)"),"validation-unique-stops");
    f.facts[0].has_between=true;CHECK(wood_world_validate_members(&c,error,sizeof error),"validation-between-multiple");
    f.stop_mode=0;CHECK(!wood_world_validate_members(&c,error,sizeof error)&&strstr(error,"R6(d)"),"validation-between-needs-stop");
    f.stop_mode=3;CHECK(!wood_world_validate_members(&c,error,sizeof error)&&strstr(error,"R6(d)"),"validation-free-not-support");return 0;
}
static int phases(void)
{
    Fixture f;WoodWorldValidationContext c=setup(&f);char error[256]="unchanged";
    f.members[0].placed=false;f.host_ok=false;CHECK(wood_world_validate_members(&c,error,sizeof error)&&!f.placed_probes,"validation-unplaced-skipped");
    f.members[0].placed=true;CHECK(!wood_world_validate_members(&c,error,sizeof error)&&!strcmp(error,"unchanged"),"validation-missing-host");
    f.host_ok=true;f.facts[0].anchor_kind=WOOD_ANCHOR_AT_GRID;f.facts[0].grid_id=99;
    CHECK(!wood_world_validate_members(&c,error,sizeof error)&&!strcmp(error,"被網格錨定的格線已不存在")&&!f.placed_probes,"validation-grid-before-placement");
    f.facts[0].anchor_kind=WOOD_ANCHOR_AT;f.place_ok=false;strcpy(error,"untouched");
    CHECK(!wood_world_validate_members(&c,error,sizeof error)&&!strcmp(error,"untouched"),"validation-place-failure-preserves-error");
    f.place_ok=true;f.end_ok=false;f.role_ok=false;
    CHECK(!wood_world_validate_members(&c,error,sizeof error)&&!strcmp(error,"end-first")&&!f.role_calls,"validation-end-before-role");
    f.end_ok=true;CHECK(!wood_world_validate_members(&c,error,sizeof error)&&!strcmp(error,"role-second"),"validation-role-error");return 0;
}
static int collision(void)
{
    Fixture f;WoodWorldValidationContext c=setup(&f);char error[256]="same";c.member_count=f.count=2;
    CHECK(wood_world_validate_members(&c,error,sizeof error),"validation-touch-is-legal");
    f.rectangles[1]=(GeoRect2){50,0,150,20};CHECK(!wood_world_validate_members(&c,error,sizeof error)&&!strcmp(error,"same"),"validation-positive-collision");
    f.facts[1].placement_id=11;CHECK(wood_world_validate_members(&c,error,sizeof error),"validation-separate-hosts");
    f.facts[1].placement_id=10;f.members[1].placed=false;CHECK(wood_world_validate_members(&c,error,sizeof error),"validation-unplaced-no-collision");return 0;
}
static int axis_policy(void)
{
    Fixture f;WoodWorldValidationContext c=setup(&f);char error[256]="axis";c.member_count=f.count=2;
    f.facts[1].length_direction=GEO_DIRECTION_POS_V;CHECK(!wood_world_validate_members(&c,error,sizeof error),"validation-primary-axis");
    f.members[1].role=WOOD_MEMBER_ROLE_SECONDARY;CHECK(wood_world_validate_members(&c,error,sizeof error),"validation-secondary-axis");return 0;
}
/* These fixtures use the production source, binding, cell and lattice APIs.
 * Only H's already-derived member footprint/pose facts are supplied above. */
static bool binding_grid(WoodWorldValidationContext *c,bool stagger)
{
    c->grids.sources=geo_grid_store_create();if(!c->grids.sources)return false;
    GeoGridSystem source={0};source.id=5;strcpy(source.name,"validation-source");source.next_rule_key=8;
    for(int axis=0;axis<2;++axis){source.axis[axis].source=GEO_GRID_SOURCE_REPEAT;source.axis[axis].step=100;}
    source.axis[0].stagger_set=stagger;source.axis[0].stagger=stagger?25:0;
    if(!stagger){source.rule_count=1;source.rules[0].key=7;strcpy(source.rules[0].name,"halves");
        source.rules[0].all_cells=true;source.rules[0].divisions[0]=source.rules[0].divisions[1]=2;}
    GeoGridBinding binding={0};binding.id=11;binding.boundary_id=71;binding.system_id=5;binding.vertex_key=902;
    binding.anchor_den[0]=binding.anchor_den[1]=1;
    WoodGridApplication grid={0};grid.id=9;grid.placement_id=10;grid.from_binding=true;grid.binding_id=11;
    return wood_grid_source_put(&c->grids,&source,0)&&geo_grid_bindings_put(c->grids.sources,&binding)&&
        wood_grid_binding_cache(&c->grids,geo_grid_bindings_find(c->grids.sources,11),&grid,NULL,0)&&wood_grid_stage(c->grids.state,&grid);
}
static int rule_scope(void)
{
    Fixture f;WoodWorldValidationContext c=setup(&f);CHECK(binding_grid(&c,false),"validation-rule-fixture");
    char error[256]="untouched";GeoCoord coordinate=-1;GeoRect2 cell={0};
    f.facts[0].anchor_kind=WOOD_ANCHOR_AT_RULE;
    f.facts[0].length_direction=GEO_DIRECTION_POS_V;f.facts[0].uv=(GeoPoint2){255,300};
    f.members[0].length=100;f.members[0].size_a=10;f.members[0].size_b=5;
    f.facts[0].rule=(GeoGridRuleLineRef){.grid_id=9,.system_id=5,.rule_key=7,.cell={2,3},.axis=0,.inner_index=0};
    CHECK(wood_grid_rule_line(&c.grids,&f.facts[0].rule,10,&coordinate,&cell,error,sizeof error)&&coordinate==250&&
        cell.min_u==200&&cell.max_u==300&&cell.min_v==300&&cell.max_v==400,"validation-rule-numeric-cell");
    f.rectangles[0]=(GeoRect2){245,300,255,400};
    CHECK(wood_world_validate_members(&c,error,sizeof error)&&!strcmp(error,"untouched"),"validation-rule-closed-cell");
    f.rectangles[0].max_v=401;unsigned probes=f.placed_probes;
    CHECK(!wood_world_validate_members(&c,error,sizeof error)&&!strcmp(error,"I13: rule anchor footprint exceeds parent cell")&&
        f.placed_probes==probes,"validation-rule-full-cell");
    f.rectangles[0]=(GeoRect2){199,300,255,400};
    CHECK(!wood_world_validate_members(&c,error,sizeof error)&&strstr(error,"I13"),"validation-rule-cross-width");
    f.rectangles[0]=(GeoRect2){245,300,255,400};f.facts[0].rule.rule_key=99;f.footprint_ok=false;
    CHECK(!wood_world_validate_members(&c,error,sizeof error)&&strstr(error,"RULE_MISSING")&&f.placed_probes==probes,
        "validation-rule-error-before-footprint");
    geo_grid_store_destroy(c.grids.sources);return 0;
}
static int subgrid_scope(void)
{
    Fixture f;WoodWorldValidationContext c=setup(&f);char error[256]="same";
    WoodGridApplication parent={0};parent.id=9;parent.placement_id=10;
    for(int axis=0;axis<2;++axis){parent.axis[axis].source=GEO_GRID_SOURCE_EXPLICIT;parent.axis[axis].count=2;
        parent.axis[axis].coords[0]=100;parent.axis[axis].coords[1]=200;}
    WoodGridApplication child={0};child.id=19;child.placement_id=10;child.parent_id=9;child.is_subgrid=true;
    for(int axis=0;axis<2;++axis){child.cell_ref[axis][0]=0;child.cell_ref[axis][1]=1;child.divisions[axis]=2;}
    CHECK(wood_grid_stage(&f.grids,&parent)&&wood_grid_stage(&f.grids,&child),"validation-subgrid-fixture");
    WoodGridHost surface;GeoRect2 cell={0};GeoCoord coordinate=-1;CHECK(host(&f,10,NULL,&surface),"validation-subgrid-host");
    CHECK(wood_grid_cell_bounds(f.grids.items,f.grids.count,&child,&surface,&cell,error,sizeof error)&&
        cell.min_u==100&&cell.min_v==100&&cell.max_u==200&&cell.max_v==200&&
        wood_grid_anchor_line_coord(f.grids.items,f.grids.count,&child,&surface,0,0,false,0,&coordinate,error,sizeof error)&&
        coordinate==150,"validation-subgrid-numeric-cell");
    f.facts[0].anchor_kind=WOOD_ANCHOR_AT_GRID;f.facts[0].grid_id=19;f.facts[0].grid_axis=0;f.facts[0].grid_index=0;
    f.facts[0].length_direction=GEO_DIRECTION_POS_V;f.facts[0].uv=(GeoPoint2){155,100};
    f.members[0].length=100;f.members[0].size_a=10;f.members[0].size_b=5;
    f.rectangles[0]=(GeoRect2){145,100,155,200};
    CHECK(wood_world_validate_members(&c,error,sizeof error)&&!strcmp(error,"same"),"validation-subgrid-closed-cell");
    f.rectangles[0].min_v=99;unsigned probes=f.placed_probes;
    CHECK(!wood_world_validate_members(&c,error,sizeof error)&&!strcmp(error,"I13：角材的完整足跡超出子格範圍")&&
        f.placed_probes==probes+1,"validation-subgrid-full-cell");
    f.rectangles[0]=(GeoRect2){145,100,201,200};
    CHECK(!wood_world_validate_members(&c,error,sizeof error)&&strstr(error,"I13"),"validation-subgrid-cross-width");
    f.rectangles[0]=(GeoRect2){145,100,155,200};f.facts[0].grid_index=1;probes=f.placed_probes;
    CHECK(!wood_world_validate_members(&c,error,sizeof error)&&strstr(error,"I23")&&f.placed_probes==probes,
        "validation-subgrid-line-before-placement");return 0;
}
static int stagger_scope(void)
{
    Fixture f;WoodWorldValidationContext c=setup(&f);CHECK(binding_grid(&c,true),"validation-stagger-fixture");
    char error[256]="same";WoodGridHost surface;GeoCoord coordinate=-1;CHECK(host(&f,10,NULL,&surface),"validation-stagger-host");
    const WoodGridApplication *grid=wood_grid_find(&f.grids,9);
    CHECK(wood_grid_anchor_line_coord(f.grids.items,f.grids.count,grid,&surface,0,2,true,3,&coordinate,error,sizeof error)&&
        coordinate==225,"validation-stagger-odd-coordinate");
    CHECK(wood_grid_anchor_line_coord(f.grids.items,f.grids.count,grid,&surface,0,2,true,2,&coordinate,error,sizeof error)&&
        coordinate==200,"validation-stagger-even-coordinate");
    f.facts[0].anchor_kind=WOOD_ANCHOR_AT_GRID;f.facts[0].grid_id=9;f.facts[0].grid_axis=0;f.facts[0].grid_index=2;
    f.facts[0].length_direction=GEO_DIRECTION_POS_V;f.facts[0].uv=(GeoPoint2){230,300};
    f.members[0].length=100;f.members[0].size_a=10;f.members[0].size_b=5;
    f.facts[0].grid_has_band=true;f.facts[0].grid_band=3;f.rectangles[0]=(GeoRect2){220,300,230,400};
    CHECK(wood_world_validate_members(&c,error,sizeof error)&&!strcmp(error,"same"),"validation-stagger-closed-band");
    f.rectangles[0].min_v=299;
    CHECK(!wood_world_validate_members(&c,error,sizeof error)&&!strcmp(error,"I24：角材沿線範圍超出該格子"),"validation-stagger-lower-bound");
    f.rectangles[0]=(GeoRect2){220,300,230,401};
    CHECK(!wood_world_validate_members(&c,error,sizeof error)&&!strcmp(error,"I24：角材沿線範圍超出該格子"),"validation-stagger-upper-bound");
    f.rectangles[0]=(GeoRect2){220,300,230,400};f.facts[0].grid_has_band=false;unsigned probes=f.placed_probes;
    CHECK(!wood_world_validate_members(&c,error,sizeof error)&&strstr(error,"I24: 有相位差")&&f.placed_probes==probes,
        "validation-stagger-band-required-first");
    f.facts[0].grid_has_band=true;f.facts[0].grid_band=INT64_MAX;
    CHECK(!wood_world_validate_members(&c,error,sizeof error)&&!strcmp(error,"I24：角材沿線範圍超出該格子"),"validation-stagger-next-index-range");
    geo_grid_store_destroy(c.grids.sources);return 0;
}
static bool room(void *user,uint32_t id,WoodRoomBounds *out)
{(void)user;if(id!=1)return false;*out=(WoodRoomBounds){{0,0,0},{100,100,100}};return true;}
static int obstacles(void)
{
    WoodSolidObstacle columns[2]={{1,1,{0,0,0},{20,20,20}},{2,0,{20,0,1000},{40,20,1100}}};
    WoodSolidObstacle beams[2]={{3,1,{0,0,500},{20,20,600}},{4,1,{0,0,500},{20,20,600}}};
    CHECK(wood_world_validate_obstacles(columns,2,beams,2,room,NULL),"validation-obstacle-touch-and-beam-overlap");
    columns[1].min[0]=19;CHECK(!wood_world_validate_obstacles(columns,2,beams,2,room,NULL),"validation-column-plan-overlap");columns[1].min[0]=20;
    columns[0].max[2]=0;CHECK(!wood_world_validate_obstacles(columns,2,beams,2,room,NULL),"validation-positive-volume");columns[0].max[2]=20;
    beams[0].space_id=2;CHECK(!wood_world_validate_obstacles(columns,2,beams,2,room,NULL),"validation-obstacle-room-exists");beams[0].space_id=1;
    beams[0].max[0]=101;CHECK(!wood_world_validate_obstacles(columns,2,beams,2,room,NULL),"validation-room-plan-containment");return 0;
}
int main(int argc,char **argv)
{if(argc!=2)return 2;if(!strcmp(argv[1],"support"))return support();if(!strcmp(argv[1],"phases"))return phases();if(!strcmp(argv[1],"collision"))return collision();if(!strcmp(argv[1],"axis"))return axis_policy();if(!strcmp(argv[1],"rule"))return rule_scope();if(!strcmp(argv[1],"subgrid"))return subgrid_scope();if(!strcmp(argv[1],"stagger"))return stagger_scope();if(!strcmp(argv[1],"obstacles"))return obstacles();return 2;}
