/* D7/I9/I13: woodworking anchor reconstruction over same-candidate facts.
 * H supplies storage/source/geometry services; W owns anchor and candidate
 * policy. No host record, transaction, parser or global state is exposed. */
#ifndef GEOMETRY_WOODWORKING_MEMBER_REFERENCE_H
#define GEOMETRY_WOODWORKING_MEMBER_REFERENCE_H
#include "members.h"
#include "supports.h"
#include "contact_world.h"
#ifndef GEO_KERNEL_GRID_STORE_H
#include "grid_store.h"
#endif
#ifndef GEO_KERNEL_SOURCE_H
#include "source.h"
#endif

typedef enum {
    WOOD_ANCHOR_AT=0,WOOD_ANCHOR_AT_GUIDES,WOOD_ANCHOR_AT_GRID,
    WOOD_ANCHOR_AT_EDGE,WOOD_ANCHOR_AT_LINE,WOOD_ANCHOR_AT_RULE
} WoodMemberAnchorKind;
typedef enum {WOOD_DEPTH_POSITIVE_NORMAL=0,WOOD_DEPTH_NEGATIVE_NORMAL} WoodMemberDepth;
typedef struct {int kind,hole,edge;uint32_t timber;char key[512];} WoodMemberReferenceFace;
typedef struct {
    uint32_t placement_id;
    int anchor_kind,length_direction,depth_side;
    uint32_t ref_grid;int ref_grid_axis;int64_t ref_grid_index;
    bool ref_grid_has_band;int64_t ref_grid_band;
    GeoGridRuleLineRef ref_rule;
    int ref_hole,ref_edge;
    bool has_through;GeoCoord through;
    uint32_t ref_guide,ref_timber;bool ref_is_timber;
    char ref_derived_key[512];
    uint64_t order;bool has_between;WoodMemberReferenceFace between[2];
} WoodMemberReference;
typedef struct {WoodMember member;WoodMemberReference anchor;bool wanted;} WoodMemberReferenceFact;
typedef struct {uint32_t id,placement_id;bool along_v;GeoCoord offset;} WoodMemberGuideFact;
typedef struct {uint32_t id,placement_id;bool subgrid;} WoodMemberGridFact;
typedef struct {uint32_t id;GeoFrame frame;bool derived;GeoCoord height;} WoodMemberPlacementFact;
typedef enum {WOOD_MEMBER_EDGE_OK,WOOD_MEMBER_EDGE_NO_DOMAIN_HOLE,WOOD_MEMBER_EDGE_MISSING_HOLE,WOOD_MEMBER_EDGE_MISSING} WoodMemberEdgeStatus;
typedef struct {GeoSegment2 segment;GeoPoint2 outward;int hole;} WoodMemberEdgeFact;
typedef struct {
    bool along_v;GeoCoord cross_lo,cross_hi;
    bool contact;GeoCoord contact_lo,contact_hi;
    bool through;GeoCoord through_at;
    bool between;WoodStopRef stops[2];
    bool scoped;GeoRect2 scope;
    const WoodMember *self;
} WoodMemberSpanRequest;
typedef struct {
    void *user;bool use_current_values;
    size_t member_count,guide_count;
    bool (*member_at)(void *,size_t,WoodMemberReferenceFact *);
    bool (*guide_at)(void *,size_t,WoodMemberGuideFact *);
    bool (*placement)(void *,uint32_t,WoodMemberPlacementFact *);
    bool (*grid)(void *,uint32_t,WoodMemberGridFact *);
    bool (*grid_line)(void *,const WoodMemberReference *,GeoCoord *,char *,size_t);
    bool (*grid_scope)(void *,uint32_t,GeoRect2 *,char *,size_t);
    bool (*rule_line)(void *,const GeoGridRuleLineRef *,uint32_t,GeoCoord *,GeoRect2 *,char *,size_t);
    bool (*member_footprint)(void *,size_t,uint32_t,GeoRect2 *);
    bool (*resolve_key)(void *,uint32_t,const char *,int *,int *,char *,size_t);
    /* A resolved derived edge uses the original encoded component indices. */
    WoodMemberEdgeStatus (*edge)(void *,uint32_t,int,int,WoodMemberEdgeFact *);
    bool (*evaluate_member)(void *,size_t,GeoDependencyKind);
    bool (*evaluate_guide)(void *,size_t);
    bool (*span)(void *,uint32_t,const WoodMemberSpanRequest *,GeoCoord *,GeoCoord *,char *,size_t);
    bool (*primary_axis)(void *,uint32_t,const WoodMember *,bool,char *,size_t);
    bool (*end_faces)(void *,uint32_t,const WoodMember *,const WoodMemberSpanRequest *,GeoCoord,GeoCoord,const GeoRect2 *,char *,size_t);
    bool (*boundary_role)(void *,uint32_t,const WoodMember *,const WoodMemberSpanRequest *,GeoCoord,GeoCoord,const GeoRect2 *,char *,size_t);
    bool (*place)(void *,uint32_t,WoodMember *,GeoPoint2,int,int);
    void (*write)(void *,size_t,const WoodMember *,GeoPoint2);
    bool (*issue)(void *,uint32_t,const char *,const char *,const char *);
    size_t (*issue_count)(void *);
    void (*first_error)(void *,const char *);
} WoodMemberReferenceContext;

/* Ordered predecessors are evaluation-before edges, not value prerequisites.
 * Explicit source failures remain value prerequisites and are reported only
 * after every selected dependency has been attempted in its original order. */
/* The caller starts place only when needs_placement is true. This preserves
 * the old recursion lifetime: large placement scratch starts after sources. */
bool wood_member_reference_compute(const WoodMemberReferenceContext *,size_t,bool *needs_placement);
bool wood_member_reference_place(const WoodMemberReferenceContext *,size_t);
GeoPoint2 wood_member_anchor_corner(const GeoFrame *,int,int,const GeoRect2 *);
/* The consumer selects ordered same-world facts. These policies do not read
 * storage, derive new support sources, or mutate the caller on refusal. */
typedef struct {uint32_t id,placement_id;WoodMemberRole role;bool placed,along_v;} WoodMemberAxisFact;
bool wood_member_primary_axis_check(const WoodMemberAxisFact *,size_t,uint32_t,
    const WoodMember *,bool,char *,size_t);
bool wood_member_boundary_role_check(const WoodMember *,const GeoLoop2View *,
    const int *fixities,bool footprint_inside,bool along_v,
    GeoCoord span_lo,GeoCoord span_hi,GeoCoord cross_lo,GeoCoord cross_hi,char *,size_t);
/* A rectangle-only placement has a null outline-fixity pointer. Derived
 * components are tested in supplied order and one must contain the full A0. */
bool wood_member_place_a0(WoodMember *,const GeoFrame *,const GeoRegionSetView *,
    const int *const *outline_fixities,GeoPoint2,int direction,int depth);
typedef enum {
    WOOD_SPAN_OK,WOOD_SPAN_NO_INTERVAL,WOOD_SPAN_AMBIGUOUS,WOOD_SPAN_OUTSIDE_CONTACT,
    WOOD_SPAN_THROUGH_OUTSIDE,WOOD_SPAN_START_UNSUPPORTED,WOOD_SPAN_END_UNSUPPORTED,
    WOOD_SPAN_START_AMBIGUOUS,WOOD_SPAN_END_AMBIGUOUS,WOOD_SPAN_FREE_EDGE_END,
    WOOD_SPAN_BETWEEN_BLOCKED,WOOD_SPAN_BETWEEN_AMBIGUOUS
} WoodMemberSpanStatus;
/* Existing product bounds; these are W scratch capacities, not K concepts. */
#define WOOD_MEMBER_SPAN_MEMBER_CAPACITY 64
#define WOOD_MEMBER_SPAN_CUT_CAPACITY (8*GEO_LOOP_MAX_VERTICES*(GEO_REGION_MAX_HOLES+1)+WOOD_MEMBER_SPAN_MEMBER_CAPACITY*2)
typedef struct {
    GeoRegionSetView domain;
    const GeoRect2 *obstacles;size_t obstacle_count;
    const WoodStopFace *stops;size_t stop_count;
    /* Boundary endpoints are checked before complete-face selection too, so
     * a full RC candidate cannot hide an explicit bare-RC refusal. H supplies
     * current facts; its adapter delegates policy to W. */
    bool (*boundary_end)(void *,const WoodMember *,bool,
        GeoCoord,GeoCoord,GeoCoord,GeoCoord,int,const WoodStopFace *,size_t,const WoodStopFace *,WoodBoundaryEndAdmission *);
    void *boundary_user;
} WoodMemberSpanFacts;
WoodMemberSpanStatus wood_member_resolve_span(const WoodMemberSpanFacts *,
    const WoodMemberSpanRequest *,GeoCoord *,GeoCoord *,char *,size_t);
#endif
