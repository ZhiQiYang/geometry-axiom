#include "world_validation.h"
#include <stdio.h>
static bool validation_refuse(char *error,size_t capacity,const char *message)
{if(error&&capacity)snprintf(error,capacity,"%s",message);return false;}
static bool validation_inside(const GeoRect2 *inner,const GeoRect2 *outer)
{return inner->min_u>=outer->min_u&&inner->max_u<=outer->max_u&&inner->min_v>=outer->min_v&&inner->max_v<=outer->max_v;}
bool wood_world_validate_members(const WoodWorldValidationContext *context,char *error,size_t capacity)
{
    const WoodGridState *grids=context->grids.state;
    for(size_t i=0;i<grids->count;++i){const WoodGridApplication *grid=&grids->items[i];WoodGridHost host;
        if(!context->host(context->user,grid->placement_id,NULL,&host)||
            !wood_grid_valid_in(grids->items,grids->count,grid,&host,NULL,0))return false;
    }
    for(size_t i=0;i<context->member_count;++i){WoodWorldMemberFact fact;
        if(!context->member_at(context->user,i,&fact))return false;const WoodMember *member=fact.member;
        if(!member->placed)continue;
        WoodGridHost host;
        if(!context->host(context->user,fact.placement_id,NULL,&host))return false;
        if(fact.anchor_kind==WOOD_ANCHOR_AT_GRID){
            const WoodGridApplication *grid=wood_grid_find(grids,fact.grid_id);WoodGridHost anchor_host;char detail[256]="";
            if(!grid||!context->host(context->user,grid->placement_id,NULL,&anchor_host)||
                !wood_grid_anchor_line_coord(grids->items,grids->count,grid,&anchor_host,fact.grid_axis,fact.grid_index,
                    fact.grid_has_band,fact.grid_band,NULL,detail,sizeof detail))
                return validation_refuse(error,capacity,detail[0]?detail:"被網格錨定的格線已不存在");
        }
        if(fact.anchor_kind==WOOD_ANCHOR_AT_RULE){GeoRect2 cell,footprint;char detail[256]="";
            if(!wood_grid_rule_line(&context->grids,&fact.rule,fact.placement_id,NULL,&cell,detail,sizeof detail)||
                !context->footprint(context->user,i,fact.placement_id,&footprint)||!validation_inside(&footprint,&cell))
                return validation_refuse(error,capacity,detail[0]?detail:"I13: rule anchor footprint exceeds parent cell");
        }
        WoodMember probe=*member;probe.placed=false;
        if(!context->place(context->user,fact.placement_id,&probe,fact.uv,fact.length_direction,fact.depth_side))return false;
        GeoRect2 footprint;
        if(!context->footprint(context->user,i,fact.placement_id,&footprint))return false;
        if(!context->host(context->user,fact.placement_id,&footprint,&host))return false;
        bool along_v=fact.length_direction==GEO_DIRECTION_POS_V||fact.length_direction==GEO_DIRECTION_NEG_V;
        if(fact.anchor_kind==WOOD_ANCHOR_AT_GRID){const WoodGridApplication *grid=wood_grid_find(grids,fact.grid_id);GeoRect2 cell;
            if(grid&&grid->is_subgrid&&(!wood_grid_cell_bounds(grids->items,grids->count,grid,&host,&cell,NULL,0)||!validation_inside(&footprint,&cell)))
                return validation_refuse(error,capacity,"I13：角材的完整足跡超出子格範圍");
            if(grid&&grid->from_binding&&fact.grid_has_band&&grid->axis[fact.grid_axis].stagger_set){
                int axis=fact.grid_axis,other=1-axis;int64_t next;GeoCoord lo,hi;
                GeoCoord flo=axis==0?footprint.min_v:footprint.min_u,fhi=axis==0?footprint.max_v:footprint.max_u;
                if(!geo_i64_add(fact.grid_band,1,&next)||!wood_grid_lattice_coord(grid,other,fact.grid_band,&lo)||
                    !wood_grid_lattice_coord(grid,other,next,&hi)||flo<lo||fhi>hi)
                    return validation_refuse(error,capacity,"I24：角材沿線範圍超出該格子");
            }
        }
        WoodStopFace faces[WOOD_CONTACT_FACE_CAPACITY];
        size_t count=context->stops(context->user,fact.placement_id,&footprint,along_v,member,faces,WOOD_CONTACT_FACE_CAPACITY);
        GeoCoord ends[2]={along_v?footprint.min_v:footprint.min_u,along_v?footprint.max_v:footprint.max_u};
        GeoCoord lo=along_v?footprint.min_u:footprint.min_v,hi=along_v?footprint.max_u:footprint.max_v;
        for(size_t end=0;end<2;++end){size_t hits=wood_stop_count_legal(faces,count,ends[end],lo,hi);
            if(!hits||(!fact.has_between&&hits!=1))return validation_refuse(error,capacity,"R6(d): 端面需要恰好一個涵蓋全寬的合法擋面");
        }
        char detail[256]="";
        if(!context->end_faces(context->user,fact.placement_id,&footprint,member,along_v,detail,sizeof detail))
            return validation_refuse(error,capacity,detail[0]?detail:"端面裁切優先序不成立");
        if(!context->boundary_role(context->user,fact.placement_id,&footprint,member,along_v,detail,sizeof detail))
            return validation_refuse(error,capacity,detail[0]?detail:"邊界材固定段未覆蓋定位邊");
    }
    for(size_t i=0;i<context->member_count;++i){WoodWorldMemberFact a;
        if(!context->member_at(context->user,i,&a))return false;if(!a.member->placed)continue;
        for(size_t j=i+1;j<context->member_count;++j){WoodWorldMemberFact b;GeoRect2 left,right;WoodGridHost host;
            if(!context->member_at(context->user,j,&b))return false;
            if(!b.member->placed||a.placement_id!=b.placement_id)continue;
            if(!context->host(context->user,a.placement_id,NULL,&host)||
                !context->footprint(context->user,i,a.placement_id,&left)||
                !context->footprint(context->user,j,a.placement_id,&right))return false;
            if(geo_rect_overlap_positive(&left,&right))return false;
        }
    }
    WoodMemberAxisFact axes[WOOD_CONTACT_MEMBER_CAPACITY];
    for(size_t i=0;i<context->member_count;++i){WoodWorldMemberFact fact;
        if(!context->member_at(context->user,i,&fact))return false;
        axes[i]=(WoodMemberAxisFact){fact.member->id,fact.placement_id,fact.member->role,fact.member->placed,
            fact.length_direction==GEO_DIRECTION_POS_V||fact.length_direction==GEO_DIRECTION_NEG_V};
    }
    for(size_t i=0;i<context->placement_count;++i)
        if(!wood_member_primary_axis_check(axes,context->member_count,context->placement_id(context->user,i),NULL,false,NULL,0))return false;
    return true;
}
static bool validation_obstacle(const WoodSolidObstacle *obstacle,WoodRoomBoundsLookup room,void *user)
{
    for(size_t axis=0;axis<3;++axis)if(obstacle->max[axis]<=obstacle->min[axis])return false;
    if(obstacle->space_id){WoodRoomBounds bounds;if(!room(user,obstacle->space_id,&bounds))return false;
        for(size_t axis=0;axis<2;++axis)if(obstacle->min[axis]<bounds.min[axis]||obstacle->max[axis]>bounds.max[axis])return false;
    }
    return true;
}
bool wood_world_validate_obstacles(const WoodSolidObstacle *columns,size_t column_count,const WoodSolidObstacle *beams,size_t beam_count,
    WoodRoomBoundsLookup room,void *user)
{
    for(size_t i=0;i<column_count;++i){const WoodSolidObstacle *column=&columns[i];
        if(!validation_obstacle(column,room,user))return false;
        GeoRect2 left={column->min[0],column->min[1],column->max[0],column->max[1]};
        for(size_t j=i+1;j<column_count;++j){const WoodSolidObstacle *other=&columns[j];
            GeoRect2 right={other->min[0],other->min[1],other->max[0],other->max[1]};
            if(geo_rect_overlap_positive(&left,&right))return false;
        }
    }
    for(size_t i=0;i<beam_count;++i)if(!validation_obstacle(&beams[i],room,user))return false;
    return true;
}
