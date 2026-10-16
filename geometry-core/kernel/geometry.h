/* Orthogonal geometry primitives. Every view borrows caller-owned vertices;
 * no edge policy, object identity, source language or host state enters K.
 * Predicate inputs must satisfy the bounded-coordinate/loop contract, except
 * is_valid operations, which check that contract themselves. */
#ifndef GEOMETRY_KERNEL_GEOMETRY_H
#define GEOMETRY_KERNEL_GEOMETRY_H
#include "types.h"
#include <stdbool.h>
#include <stddef.h>
#define GEO_COORD_LIMIT INT64_C(100000000)
#define GEO_LOOP_MAX_VERTICES 32
#define GEO_REGION_MAX_HOLES 8
typedef int64_t GeoCoord;
typedef struct {GeoCoord x,y,z;} GeoPoint3;
typedef struct {GeoCoord x,y,z;} GeoVector3;
typedef struct {GeoCoord u,v;} GeoPoint2;
typedef struct {GeoPoint2 start,end;} GeoSegment2;
typedef struct {GeoPoint3 start,end;} GeoSegment3;
typedef struct {GeoPoint3 vertices[4];} GeoQuad3;
typedef struct {GeoPoint3 point;GeoVector3 normal;} GeoPlane3;
typedef struct {GeoPoint3 origin;GeoVector3 axis_u,axis_v,normal;} GeoFrame;
typedef struct {GeoCoord min_u,min_v,max_u,max_v;} GeoRect2;
typedef struct {const GeoPoint2 *v;size_t count;} GeoLoop2View;
typedef struct {GeoLoop2View outline;const GeoLoop2View *holes;size_t hole_count;} GeoRegionView;
typedef struct {const GeoRegionView *regions;size_t count;} GeoRegionSetView;
typedef struct {GeoFrame frame;GeoCoord extent[3];} GeoBox3;
typedef struct {GeoCoord start,end;} GeoInterval;
typedef struct {GeoInterval *items;size_t capacity,count;} GeoIntervalBuffer;
typedef struct {GeoCoord *cuts;size_t capacity;} GeoStripScratch;
typedef enum {GEO_GEOMETRY_OK=0,GEO_GEOMETRY_INVALID,GEO_GEOMETRY_CAPACITY} GeoGeometryStatus;
typedef enum {GEO_DIRECTION_POS_U=0,GEO_DIRECTION_NEG_U,GEO_DIRECTION_POS_V,GEO_DIRECTION_NEG_V} GeoDirection2;

bool geo_coord_in_range(GeoCoord value);
GeoCoord geo_vector_dot(GeoVector3 a, GeoVector3 b);
GeoVector3 geo_vector_cross(GeoVector3 a, GeoVector3 b);
GeoVector3 geo_vector_negate(GeoVector3 v);
bool geo_vector_equal(GeoVector3 a, GeoVector3 b);
bool geo_frame_is_valid(const GeoFrame *frame);
bool geo_loop_is_valid(const GeoLoop2View *loop);
bool geo_loop_point_on_edge(const GeoLoop2View *loop, GeoPoint2 p);
bool geo_loop_contains_point(const GeoLoop2View *loop, GeoPoint2 p);
bool geo_segment_crosses_rect_interior(
    GeoPoint2 a, GeoPoint2 b,
    GeoCoord min_u, GeoCoord min_v, GeoCoord max_u, GeoCoord max_v
);
bool geo_loop_contains_rect(
    const GeoLoop2View *loop,
    GeoCoord min_u, GeoCoord min_v, GeoCoord max_u, GeoCoord max_v
);
void geo_loop_bbox(
    const GeoLoop2View *loop,
    GeoCoord *out_min_u, GeoCoord *out_min_v,
    GeoCoord *out_max_u, GeoCoord *out_max_v
);
GeoGeometryStatus geo_loop_clip_line(
    const GeoLoop2View *loop,
    bool along_u,
    GeoCoord offset,
    GeoSegment2 out[],
    size_t out_cap,
    size_t *out_count
);
bool geo_region_is_valid(const GeoRegionView *b);
bool geo_region_contains_point(
    const GeoRegionView *b,
    GeoPoint2 p
);
bool geo_region_contains_rect(
    const GeoRegionView *b,
    GeoCoord min_u, GeoCoord min_v, GeoCoord max_u, GeoCoord max_v
);
GeoPoint3 geo_frame_point(const GeoFrame *frame,GeoCoord u,GeoCoord v,GeoCoord w);
GeoVector3 geo_frame_direction(const GeoFrame *frame,GeoDirection2 direction);
GeoPoint2 geo_frame_project_uv(const GeoFrame *frame,GeoPoint3 point);
GeoRect2 geo_rectangle_footprint(const GeoFrame *frame,GeoPoint2 anchor,
    GeoVector3 along,GeoVector3 across,GeoCoord extent_along,GeoCoord extent_across);
bool geo_rect_overlap_positive(const GeoRect2 *a,const GeoRect2 *b);
bool geo_box_face(const GeoBox3 *box,unsigned axis,unsigned side,GeoQuad3 *out);
GeoRect2 geo_aabb_project_uv(const GeoFrame *frame,GeoPoint3 low,GeoPoint3 high);
bool geo_region_set_contains_rect(const GeoRegionSetView *domain,const GeoRect2 *rect);
GeoGeometryStatus geo_strip_intervals(const GeoRegionSetView *domain,bool along_v,GeoInterval cross,
    const GeoRect2 *obstacles,size_t obstacle_count,GeoIntervalBuffer *out,GeoStripScratch scratch);
/* Clip: capacity failure returns no partial output; out_count is zero.
 * Strip: complete maximal feasible intervals across every region component.
 * Callers choose obstacles and later apply their own source/contact policies;
 * neither a selection scope nor a support concept exists in this operation.
 * A capacity failure leaves out->count zero; scratch/output storage is borrowed. */
GeoGeometryStatus geo_loop_rect_area2(const GeoLoop2View *loop,const GeoRect2 *rect,GeoCoord *out);
bool geo_region_set_intersects_rect_positive(const GeoRegionSetView *domain,const GeoRect2 *rect);
/* Exact positive-area complement of rect outside a simple orthogonal loop.
 * Rectangles are emitted in horizontal-band, then increasing-u order.
 * Inputs obey the bounded geometry contract. Failure sets out_count to zero. */
#define GEO_LOOP_RECT_COMPLEMENT_CAPACITY ((GEO_LOOP_MAX_VERTICES+1)*(GEO_LOOP_MAX_VERTICES/2+1))
GeoGeometryStatus geo_loop_rect_complement(const GeoLoop2View *loop,const GeoRect2 *rect,
    GeoRect2 *out,size_t capacity,size_t *out_count);
#endif
