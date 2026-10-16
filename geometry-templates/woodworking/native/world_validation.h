/* Final-world woodworking validation. H supplies same-candidate geometry and
 * source facts; W selects participants, checks scopes, supports and roles. */
#ifndef GEOMETRY_WOODWORKING_WORLD_VALIDATION_H
#define GEOMETRY_WOODWORKING_WORLD_VALIDATION_H
#include "grid_application.h"
#include "member_reference.h"
#include "contact_world.h"
typedef struct {
    const WoodMember *member;
    GeoPoint2 uv;
    uint32_t placement_id,grid_id;
    int anchor_kind,length_direction,depth_side,grid_axis;
    int64_t grid_index,grid_band;
    bool grid_has_band,has_between;
    GeoGridRuleLineRef rule;
} WoodWorldMemberFact;
typedef struct {
    WoodGridContext grids;
    void *user;
    size_t member_count,placement_count;
    bool (*member_at)(void *,size_t,WoodWorldMemberFact *);
    uint32_t (*placement_id)(void *,size_t);
    bool (*host)(void *,uint32_t,const GeoRect2 *,WoodGridHost *);
    bool (*footprint)(void *,size_t,uint32_t,GeoRect2 *);
    bool (*place)(void *,uint32_t,WoodMember *,GeoPoint2,int,int);
    size_t (*stops)(void *,uint32_t,const GeoRect2 *,bool,const WoodMember *,WoodStopFace *,size_t);
    bool (*end_faces)(void *,uint32_t,const GeoRect2 *,const WoodMember *,bool,char *,size_t);
    bool (*boundary_role)(void *,uint32_t,const GeoRect2 *,const WoodMember *,bool,char *,size_t);
} WoodWorldValidationContext;
bool wood_world_validate_members(const WoodWorldValidationContext *,char *,size_t);
typedef struct {uint32_t id,space_id;GeoCoord min[3],max[3];} WoodSolidObstacle;
typedef struct {GeoCoord min[3],max[3];} WoodRoomBounds;
typedef bool (*WoodRoomBoundsLookup)(void *,uint32_t,WoodRoomBounds *);
/* Columns collide in plan across the whole world; beams do not share that
 * rule. Both have positive volume and an optional containing room in plan. */
bool wood_world_validate_obstacles(const WoodSolidObstacle *,size_t,const WoodSolidObstacle *,size_t,
    WoodRoomBoundsLookup,void *);
#endif
