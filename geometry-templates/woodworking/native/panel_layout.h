/* Existing panel-fill lattice, tile identities and seam-band policy. All
 * geometry/source resolution is explicit and immutable for one evaluation. */
#ifndef GEO_WOOD_PANEL_LAYOUT_H
#define GEO_WOOD_PANEL_LAYOUT_H
#ifndef GEO_KERNEL_CLIP_H
#include "clip.h"
#endif
#define WOOD_PANEL_TILE_MAX 1024
#define WOOD_PANEL_VERTEX_MAX 32768
typedef GeoClipLoop WoodPanelLoop;
typedef GeoClipComponent WoodPanelFragment;
typedef struct {int64_t i,j;GeoCoord body[4],area;WoodPanelFragment *fragments;size_t count;} WoodPanelTile;
typedef struct {int axis;int64_t k,band;GeoCoord coordinate,range[2];bool staggered;} WoodPanelSeamLine;
typedef struct {
    WoodPanelTile *tiles;size_t count,fragments,vertices,whole;
    WoodPanelSeamLine *seams;size_t seam_count;GeoCoord size[2],gap,stagger;
} WoodPanelLayout;
typedef struct {
    GeoRegionView region;GeoFrame frame;const GeoRect2 *cuts;size_t cut_count;
    GeoCoord size[2],gap,stagger,origin[2];int stagger_axis;
} WoodPanelLayoutInput;
typedef enum {WOOD_PANEL_OK=0,WOOD_PANEL_WORKSPACE,WOOD_PANEL_ENUM_LIMIT,
    WOOD_PANEL_CLIP,WOOD_PANEL_CORNER_RANGE,WOOD_PANEL_VERTEX_RANGE,
    WOOD_PANEL_SEAM_WORKSPACE,WOOD_PANEL_SEAM_LIMIT,WOOD_PANEL_BAND_RANGE} WoodPanelStatus;
void wood_panel_layout_free(WoodPanelLayout *layout);
/* Dimensions, positive pitch and stagger are validated by the consumer.
 * Failure discards every result. clip_status specifies the exact K failure. */
WoodPanelStatus wood_panel_layout_build(const WoodPanelLayoutInput *input,
    WoodPanelLayout *out,GeoClipStatus *clip_status);
#endif
