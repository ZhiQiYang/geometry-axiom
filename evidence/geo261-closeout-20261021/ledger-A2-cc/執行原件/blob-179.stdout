/* The application's persistent spelling, ordering and display metadata.
 * Geometry and template definitions are owned by their separate documents. */
#ifndef GEOMETRY_APP_DOCUMENT_H
#define GEOMETRY_APP_DOCUMENT_H
#include "../../geometry-core/kernel/document.h"
#include "../../geometry-templates/woodworking/native/document.h"
#include "definition_texts.h"

typedef struct {GeoRect2 unused_rect;} AppPlacementMetadata;
typedef enum {
    APP_CANVAS_POS_BOUNDARY=0,APP_CANVAS_POS_PLACEMENT,APP_CANVAS_POS_SPACE,
    APP_CANVAS_POS_COLUMN,APP_CANVAS_POS_BEAM,APP_CANVAS_POS_GRID_BINDING,
    APP_CANVAS_POS_PARAMETER,APP_CANVAS_POS_GRID_SYSTEM,
    APP_CANVAS_POS_ASSEMBLY_RULE,APP_CANVAS_POS_ASSEMBLY_BINDING
} AppCanvasPositionKind;
typedef struct {int kind;uint32_t id;GeoCoord x,y;} AppCanvasPosition;

#define APP_CANVAS_POSITION_CAPACITY (GEO_REGION_CAPACITY+GEO_PLACEMENT_CAPACITY+GEO_ENCLOSURE_CAPACITY+WOOD_OBSTACLE_CAPACITY*2+GEO_GRID_SYSTEM_CAPACITY+GEO_GRID_BINDING_CAPACITY+GEO_PARAMETER_CARD_MAX)

typedef struct {
    AppDatumText datum_texts[GEO_DATUM_CAPACITY];
    uint64_t next_order;
    AppPlacementMetadata placement_metadata[GEO_PLACEMENT_CAPACITY];
    AppGuideText guide_texts[GEO_GUIDE_CAPACITY];
    /* Only this exact contiguous span is excluded from definition equality.
     * The remaining application fields still participate in candidate seals. */
    AppCanvasPosition canvas_pos[APP_CANVAS_POSITION_CAPACITY];
    size_t canvas_pos_count;
    bool parameter_loading;
} AppDocument;
#endif
