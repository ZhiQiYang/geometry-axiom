/* Exact two-sided widths on effective panel seams. The consumer supplies
 * selected footprints in the same frame; insufficient support is a result. */
#ifndef GEO_WOOD_PANEL_SUPPORT_H
#define GEO_WOOD_PANEL_SUPPORT_H
#include "panel_layout.h"
#define WOOD_PANEL_SUPPORT_MAX 32768
#define WOOD_PANEL_SUPPORT_WORK_MAX 1048576
typedef struct {GeoCoord lo[2],hi[2];} WoodPanelFootprint;
typedef struct {size_t line;GeoCoord range[2],edges[2];} WoodPanelEffectiveSeam;
typedef struct {size_t seam;GeoCoord range[2],left,right;bool supported;} WoodPanelSupportPart;
typedef struct {WoodPanelEffectiveSeam *seams,*nonseams;size_t count,non_count;WoodPanelSupportPart *parts;size_t part_count;} WoodPanelSupport;
typedef enum {WOOD_PANEL_SUPPORT_OK=0,WOOD_PANEL_SUPPORT_FOOTPRINT_LIMIT,
    WOOD_PANEL_SUPPORT_WORKSPACE,WOOD_PANEL_SUPPORT_SLAB_LIMIT,
    WOOD_PANEL_SUPPORT_SEAM_LIMIT,WOOD_PANEL_SUPPORT_PART_LIMIT} WoodPanelSupportStatus;
void wood_panel_support_free(WoodPanelSupport *support);
/* The layout is a complete evaluated result. threshold is a positive exact
 * dimension with positive denominator; capacity is the caller's source limit.
 * Failed evaluation frees all result arrays and zeros the complete output. */
WoodPanelSupportStatus wood_panel_support_evaluate(const WoodPanelLayout *layout,
    const WoodPanelFootprint *rects,size_t count,size_t footprint_capacity,
    GeoQuantity threshold,WoodPanelSupport *out);
#endif
