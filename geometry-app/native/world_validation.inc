/* H converts the candidate's geometry/identity records into W borrowed facts.
 * Participation, support counting, scopes, role order and obstacle rules live
 * in world_validation.c. No callback chooses acceptance or publication. */
#include "../../geometry-templates/woodworking/native/world_validation.h"
static bool app_reference_host_read(const World *,uint32_t,PlacementSurface *,SpaceBoundarySurface *,const SpaceBoundarySurface **);
static bool app_reference_member_anchor(const World *,size_t,WoodMemberPlacement *);
static bool app_reference_member_footprint(const World *,size_t,uint32_t,GeoRect2 *);
/* 僅供同一次驗證的直接讀取共用成功值；provider 回呼仍須透過原入口
 * 記錄各自 consumer 的依賴。兩個驗證函式執行期間不修改 World；
 * 每次 begin 都捨棄前一次的讀取。 */
typedef struct {
    const World *world;
    bool valid[WORLD_MAX_TIMBERS];
    uint32_t placement[WORLD_MAX_TIMBERS];
    GeoRect2 value[WORLD_MAX_TIMBERS];
} AppFootprintMemo;
static void app_footprint_memo_begin(AppFootprintMemo *memo,const World *world)
{
    memo->world=world;
    memset(memo->valid,0,sizeof memo->valid);
}
static bool app_footprint_memo_read(AppFootprintMemo *memo,size_t i,uint32_t placement,GeoRect2 *out)
{
    if(i>=WORLD_MAX_TIMBERS)return app_reference_member_footprint(memo->world,i,placement,out);
    if(memo->valid[i]&&memo->placement[i]==placement){*out=memo->value[i];return true;}
    if(!app_reference_member_footprint(memo->world,i,placement,out))return false;
    memo->value[i]=*out;memo->placement[i]=placement;memo->valid[i]=true;return true;
}
static bool app_reference_validation_room(const World *,uint32_t,WoodRoomBounds *);
static bool app_reference_validation_obstacle(const World *,bool,size_t,WoodSolidObstacle *);
static bool app_reference_member_geometry(const World *,WoodMember *,bool *);
static bool app_reference_end_faces(const World *,const PlacementSurface *,const SpaceBoundarySurface *,const WoodMember *,bool,
    Coord,Coord,Coord,Coord,char *,size_t);
typedef struct {
    PlacementSurface placement;
    SpaceBoundarySurface boundary;
    const PlacementSurface *p;
    const SpaceBoundarySurface *b;
} AppValidationDomain;
typedef struct {
    const World *world;AppFootprintMemo footprints;
    bool host_valid,has_boundary;
    uint32_t host_id;
    PlacementSurface host;
    SpaceBoundarySurface boundary;
} AppValidationInputs;
static bool app_validation_domain(void *user,uint32_t id,const GeoRect2 *footprint,AppValidationDomain *out)
{
    AppValidationInputs *inputs=user;
    if(!inputs->host_valid||inputs->host_id!=id){
        const SpaceBoundarySurface *view;
        if(!app_reference_host_read(inputs->world,id,&inputs->host,&inputs->boundary,&view))return false;
        inputs->has_boundary=view!=NULL;if(view)inputs->boundary=*view;
        inputs->host_id=id;inputs->host_valid=true;
    }
    out->placement=inputs->host;out->boundary=inputs->boundary;
    out->b=inputs->has_boundary?&out->boundary:NULL;
    out->p=&out->placement;
    if(footprint)out->b=placement_boundary_for_rect(out->p,out->b,footprint);
    return true;
}
static bool app_validation_member(void *user,size_t i,WoodWorldMemberFact *out)
{
    const World *world=((AppValidationInputs *)user)->world;if(i>=world->wood.timber_count)return false;
    TimberAnchor actual;if(!app_reference_member_anchor(world,i,&actual))return false;
    const TimberAnchor *a=&actual;
    *out=(WoodWorldMemberFact){.member=&world->wood.timbers[i],.uv=a->uv,.placement_id=a->placement_id,
        .grid_id=a->ref_grid,.anchor_kind=a->anchor_kind,.length_direction=a->length_direction,.depth_side=a->depth_side,
        .grid_axis=a->ref_grid_axis,.grid_index=a->ref_grid_index,.grid_band=a->ref_grid_band,
        .grid_has_band=a->ref_grid_has_band,.has_between=a->has_between,.rule=a->ref_rule};return true;
}
static uint32_t app_validation_placement_id(void *user,size_t i)
{return geo_placements_at(&((AppValidationInputs *)user)->world->geo.placement_data,i)->id;}
static bool app_validation_host(void *user,uint32_t id,const GeoRect2 *footprint,WoodGridHost *out)
{AppValidationDomain domain;return app_validation_domain(user,id,footprint,&domain)&&app_grid_host_value(domain.p,domain.b,out);}
static bool app_validation_footprint(void *user,size_t i,uint32_t id,GeoRect2 *out)
{
    return app_footprint_memo_read(&((AppValidationInputs *)user)->footprints,i,id,out);
}
static bool app_validation_place(void *user,uint32_t id,WoodMember *member,GeoPoint2 uv,int direction,int depth)
{
    AppValidationDomain domain;bool from_source=false;
    if(!app_validation_domain(user,id,NULL,&domain)||!app_reference_member_geometry(((AppValidationInputs *)user)->world,member,&from_source))return false;
    if(from_source)uv=geo_frame_project_uv(&domain.p->frame,member->origin);
    return timber_place_a0_on_surface(member,domain.p,domain.b,uv,(SurfaceDirection)direction,(SurfaceDepthSide)depth);
}
static size_t app_validation_stops(void *user,uint32_t id,const GeoRect2 *footprint,bool along_v,
    const WoodMember *exclude,WoodStopFace *out,size_t capacity)
{
    AppValidationDomain domain;if(!app_validation_domain(user,id,footprint,&domain))return 0;
    return collect_stop_faces(((AppValidationInputs *)user)->world,domain.p,domain.b,along_v,exclude,out,capacity);
}
static bool app_validation_end_faces(void *user,uint32_t id,const GeoRect2 *footprint,const WoodMember *member,bool along_v,char *error,size_t capacity)
{
    AppValidationDomain domain;if(!app_validation_domain(user,id,footprint,&domain))return false;
    return app_reference_end_faces(((AppValidationInputs *)user)->world,domain.p,domain.b,member,along_v,
        along_v?footprint->min_v:footprint->min_u,along_v?footprint->max_v:footprint->max_u,
        along_v?footprint->min_u:footprint->min_v,along_v?footprint->max_u:footprint->max_v,error,capacity);
}
static bool app_validation_boundary_role(void *user,uint32_t id,const GeoRect2 *footprint,const WoodMember *member,bool along_v,char *error,size_t capacity)
{
    AppValidationDomain domain;if(!app_validation_domain(user,id,footprint,&domain))return false;
    return timber_boundary_role_check(domain.p,domain.b,member,along_v,
        along_v?footprint->min_v:footprint->min_u,along_v?footprint->max_v:footprint->max_u,
        along_v?footprint->min_u:footprint->min_v,along_v?footprint->max_u:footprint->max_v,error,capacity);
}
static WoodWorldValidationContext app_world_validation_context(const World *world,AppValidationInputs *inputs)
{
    inputs->world=world;inputs->host_valid=false;app_footprint_memo_begin(&inputs->footprints,world);
    WoodWorldValidationContext context={0};context.grids=app_grid_context(world);context.user=inputs;
    context.member_count=world->wood.timber_count;context.placement_count=world_placement_count(world);
    context.member_at=app_validation_member;context.placement_id=app_validation_placement_id;
    context.host=app_validation_host;context.footprint=app_validation_footprint;context.place=app_validation_place;
    context.stops=app_validation_stops;context.end_faces=app_validation_end_faces;context.boundary_role=app_validation_boundary_role;return context;
}
static bool app_validation_room(void *user,uint32_t id,WoodRoomBounds *out)
{
    return app_reference_validation_room(user,id,out);
}
static bool app_world_obstacles_valid(const World *world)
{
    WoodSolidObstacle columns[WORLD_MAX_RC],beams[WORLD_MAX_RC];
    for(size_t i=0;i<world->wood.column_count;++i)if(!app_reference_validation_obstacle(world,true,i,&columns[i]))return false;
    for(size_t i=0;i<world->wood.beam_count;++i)if(!app_reference_validation_obstacle(world,false,i,&beams[i]))return false;
    return wood_world_validate_obstacles(columns,world->wood.column_count,beams,world->wood.beam_count,app_validation_room,(void *)world);
}
