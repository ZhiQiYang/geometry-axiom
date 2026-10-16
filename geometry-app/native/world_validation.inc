/* H converts the candidate's geometry/identity records into W borrowed facts.
 * Participation, support counting, scopes, role order and obstacle rules live
 * in world_validation.c. No callback chooses acceptance or publication. */
#include "../../geometry-templates/woodworking/native/world_validation.h"
typedef struct {
    PlacementSurface placement;
    SpaceBoundarySurface boundary;
    const PlacementSurface *p;
    const SpaceBoundarySurface *b;
} AppValidationDomain;
static bool app_validation_domain(void *user,uint32_t id,const GeoRect2 *footprint,AppValidationDomain *out)
{
    const World *world=user;out->p=app_placement_read(world,id,&out->placement);
    if(!out->p)return false;
    out->b=app_placement_boundary(world,out->p,&out->boundary);
    if(footprint)out->b=placement_boundary_for_rect(out->p,out->b,footprint);
    return true;
}
static bool app_validation_member(void *user,size_t i,WoodWorldMemberFact *out)
{
    const World *world=user;if(i>=world->wood.timber_count)return false;
    const TimberAnchor *a=&world->wood.anchors[i];
    *out=(WoodWorldMemberFact){.member=&world->wood.timbers[i],.uv=a->uv,.placement_id=a->placement_id,
        .grid_id=a->ref_grid,.anchor_kind=a->anchor_kind,.length_direction=a->length_direction,.depth_side=a->depth_side,
        .grid_axis=a->ref_grid_axis,.grid_index=a->ref_grid_index,.grid_band=a->ref_grid_band,
        .grid_has_band=a->ref_grid_has_band,.has_between=a->has_between,.rule=a->ref_rule};return true;
}
static uint32_t app_validation_placement_id(void *user,size_t i)
{return geo_placements_at(&((const World *)user)->geo.placement_data,i)->id;}
static bool app_validation_host(void *user,uint32_t id,const GeoRect2 *footprint,WoodGridHost *out)
{AppValidationDomain domain;return app_validation_domain(user,id,footprint,&domain)&&app_grid_host_value(domain.p,domain.b,out);}
static bool app_validation_footprint(void *user,size_t i,uint32_t id,GeoRect2 *out)
{
    const World *world=user;AppValidationDomain domain;
    return app_validation_domain(user,id,NULL,&domain)&&timber_a0_footprint_uv(domain.p,&world->wood.timbers[i],&world->wood.anchors[i],out);
}
static bool app_validation_place(void *user,uint32_t id,WoodMember *member,GeoPoint2 uv,int direction,int depth)
{
    AppValidationDomain domain;
    return app_validation_domain(user,id,NULL,&domain)&&timber_place_a0_on_surface(member,domain.p,domain.b,uv,(SurfaceDirection)direction,(SurfaceDepthSide)depth);
}
static size_t app_validation_stops(void *user,uint32_t id,const GeoRect2 *footprint,bool along_v,
    const WoodMember *exclude,WoodStopFace *out,size_t capacity)
{
    AppValidationDomain domain;if(!app_validation_domain(user,id,footprint,&domain))return 0;
    return collect_stop_faces(user,domain.p,domain.b,along_v,exclude,out,capacity);
}
static bool app_validation_end_faces(void *user,uint32_t id,const GeoRect2 *footprint,const WoodMember *member,bool along_v,char *error,size_t capacity)
{
    AppValidationDomain domain;if(!app_validation_domain(user,id,footprint,&domain))return false;
    return timber_end_face_check(user,domain.p,domain.b,member,along_v,
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
static WoodWorldValidationContext app_world_validation_context(const World *world)
{
    WoodWorldValidationContext context={0};context.grids=app_grid_context(world);context.user=(void *)world;
    context.member_count=world->wood.timber_count;context.placement_count=world_placement_count(world);
    context.member_at=app_validation_member;context.placement_id=app_validation_placement_id;
    context.host=app_validation_host;context.footprint=app_validation_footprint;context.place=app_validation_place;
    context.stops=app_validation_stops;context.end_faces=app_validation_end_faces;context.boundary_role=app_validation_boundary_role;return context;
}
static bool app_validation_room(void *user,uint32_t id,WoodRoomBounds *out)
{
    const Space *space=world_find_space(user,id);if(!space)return false;
    for(size_t axis=0;axis<3;++axis){out->min[axis]=space->min[axis];out->max[axis]=space->max[axis];}return true;
}
static bool app_world_obstacles_valid(const World *world)
{
    WoodSolidObstacle columns[WORLD_MAX_RC],beams[WORLD_MAX_RC];
    for(size_t i=0;i<world->wood.column_count;++i){const RcColumn *column=&world->wood.columns[i];
        columns[i]=(WoodSolidObstacle){column->id,column->space_id,{column->x_lo,column->y_lo,column->z_lo},{column->x_hi,column->y_hi,column->z_hi}};
    }
    for(size_t i=0;i<world->wood.beam_count;++i){const RcBeam *beam=&world->wood.beams[i];
        beams[i]=(WoodSolidObstacle){beam->id,beam->space_id,{beam->x_lo,beam->y_lo,beam->z_lo},{beam->x_hi,beam->y_hi,beam->z_hi}};
    }
    return wood_world_validate_obstacles(columns,world->wood.column_count,beams,world->wood.beam_count,app_validation_room,(void *)world);
}
