/* A fixed, headless recipe using the public native geometry kernel. */
#ifndef RECTANGULAR_GRID_TEMPLATE_H
#define RECTANGULAR_GRID_TEMPLATE_H
#include "exact.h"
#include "grid.h"

#define RECTANGULAR_GRID_TEMPLATE_ID "rectangular-grid/1"
#define RECTANGULAR_GRID_MAX_DIVISIONS 32
#define RECTANGULAR_GRID_MAX_CELLS 256
#define RECTANGULAR_GRID_MAX_SOURCES 64

typedef enum { RG_LENGTH=1, RG_COUNT=2 } RGFieldKind;
typedef enum { RG_WIDTH=0, RG_HEIGHT, RG_COLUMNS, RG_ROWS, RG_FIELD_COUNT } RGField;
/* Names are deliberately absent: callers retain their display metadata.
 * owner/field/kind identify the source; revision identifies the evaluated
 * source value in a result. This recipe is not a general dependency graph. */
typedef struct { uint64_t owner,field; RGFieldKind kind; } RGSourceKey;
typedef struct { RGSourceKey key; uint64_t revision; GeoQuantity value; } RGSource;
typedef struct { RGSourceKey sources[RG_FIELD_COUNT]; } RGDefinition;
typedef struct { unsigned column,row; GeoRect2 bounds; } RGCell;
typedef struct {
    RGSource sources[RG_FIELD_COUNT];
    GeoPoint2 outline[4];
    GeoCoord u[RECTANGULAR_GRID_MAX_DIVISIONS+1];
    GeoCoord v[RECTANGULAR_GRID_MAX_DIVISIONS+1];
    size_t u_count,v_count,cell_count;
    RGCell cells[RECTANGULAR_GRID_MAX_CELLS];
} RGResult;
typedef enum {
    RG_OK=0, RG_INVALID_INPUT, RG_MISSING_SOURCE, RG_DUPLICATE_SOURCE,
    RG_FIELD_KIND_MISMATCH, RG_UNIT_MISMATCH, RG_INVALID_EXACT_VALUE,
    RG_FRACTIONAL_SOURCE, RG_SOURCE_RANGE, RG_CELL_CAPACITY,
    RG_FRACTIONAL_CELL, RG_CORE_GRID_FAILURE, RG_CORE_GEOMETRY_FAILURE
} RGStatus;
typedef struct {
    RGStatus status;
    RGField field;
    RGSourceKey source;
    GeoQuantity value;
    unsigned divisions;
    GeoQuantity required_step;
    GeoGridStatus grid_status;
    GeoExactStatus exact_status;
} RGDiagnostic;

/* No global state or allocation. On failure out is byte-for-byte untouched.
 * Input/output storage must not overlap the diagnostic. All input sources
 * have distinct typed keys and a nonzero revision. Only referenced values
 * are evaluated; RGResult retains all four typed keys and source revisions.
 * Geometry is derived by K; this function only binds fields and forms cells. */
RGStatus rectangular_grid_evaluate(const RGDefinition *definition,
    const RGSource *sources,size_t source_count,RGResult *out,RGDiagnostic *diagnostic);
const char *rectangular_grid_status_code(RGStatus status);
#endif
