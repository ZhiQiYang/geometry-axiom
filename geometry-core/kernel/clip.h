/* Regularized orthogonal region/rectangle difference. Inputs borrow valid,
 * bounded geometry; output owns every component, hole and point in canonical
 * order. Point-touching material stays in separate components. No host policy. */
#ifndef GEO_KERNEL_CLIP_H
#define GEO_KERNEL_CLIP_H
#include "geometry.h"
#define GEO_CLIP_AXIS_MAX 128
#define GEO_CLIP_EDGE_MAX 4096
typedef struct {GeoPoint2 *points;size_t count;bool hole;} GeoClipLoop;
typedef struct {GeoClipLoop *loops;size_t count;GeoCoord area;} GeoClipComponent;
typedef struct {GeoClipComponent *fragments;size_t count;GeoCoord area;} GeoClipResult;
typedef enum {GEO_CLIP_OK=0,GEO_CLIP_AXIS_LIMIT,GEO_CLIP_WORKSPACE,
    GEO_CLIP_COMPONENT_WORKSPACE,GEO_CLIP_EDGE_LIMIT,GEO_CLIP_LOOP_WORKSPACE,
    GEO_CLIP_TRAVERSAL,GEO_CLIP_OPEN_CONTOUR,GEO_CLIP_CORNERS_WORKSPACE,
    GEO_CLIP_ORDERED_WORKSPACE,GEO_CLIP_VERTEX_LIMIT,GEO_CLIP_COLLECTION_WORKSPACE,
    GEO_CLIP_NO_OUTER} GeoClipStatus;
int geo_clip_point_order(GeoPoint2 a,GeoPoint2 b);
void geo_clip_result_free(GeoClipResult *result);
/* out starts zeroed. On any status it owns its allocated partial result and
 * must be freed; no caller may publish a failed result. vertex_count is a
 * caller-owned cumulative budget, incremented in the original traversal order.
 * keep_collinear retains subdivision vertices for geometric provenance. */
GeoClipStatus geo_region_clip_rect_minus_rects(const GeoRegionView *region,
    const GeoRect2 *body,const GeoRect2 *cuts,size_t cut_count,bool keep_collinear,
    size_t vertex_limit,size_t *vertex_count,GeoClipResult *out);
#endif
