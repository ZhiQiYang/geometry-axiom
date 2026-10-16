/* GEO-075 report policy. The host owns text rendering; W owns participation,
 * equal-spec grouping, declaration-order IDs and deterministic group order. */
#ifndef GEOMETRY_WOODWORKING_CUT_LIST_H
#define GEOMETRY_WOODWORKING_CUT_LIST_H
#include "members.h"
#define WOOD_CUT_LIST_MEMBER_CAPACITY 64
typedef struct {
    GeoCoord length,size_a,size_b;
    WoodMemberRole role;
    size_t count;
    uint32_t ids[WOOD_CUT_LIST_MEMBER_CAPACITY];
} WoodCutGroup;
typedef struct {
    WoodCutGroup groups[WOOD_CUT_LIST_MEMBER_CAPACITY];
    size_t group_count,placed;
    GeoCoord total_length;
} WoodCutList;
bool wood_cut_list_collect(const WoodMember *,size_t,WoodCutList *);
#endif
