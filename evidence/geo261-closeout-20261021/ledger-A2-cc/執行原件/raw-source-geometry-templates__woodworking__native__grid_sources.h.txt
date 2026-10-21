/* Candidate-local grid source policy. K retains typed values and identities;
 * W evaluates the same candidate's applications and exact grid algorithms. */
#ifndef GEOMETRY_WOODWORKING_GRID_SOURCES_H
#define GEOMETRY_WOODWORKING_GRID_SOURCES_H
#include "grid_application.h"
#ifndef GEO_KERNEL_SOURCE_H
#include "source.h"
#endif
typedef enum {
    WOOD_GRID_SOURCE_SYSTEM_DEFINITION=1,WOOD_GRID_SOURCE_SYSTEM,
    WOOD_GRID_SOURCE_BINDING_DEFINITION,WOOD_GRID_SOURCE_BINDING,
    WOOD_GRID_SOURCE_APPLICATION_DEFINITION,WOOD_GRID_SOURCE_APPLICATION,
    WOOD_GRID_SOURCE_PANEL,WOOD_GRID_SOURCE_GAP,
    WOOD_GRID_SOURCE_LINE,WOOD_GRID_SOURCE_CELL,WOOD_GRID_SOURCE_RULE_LINE,
    WOOD_GRID_SOURCE_RULE_CELL,WOOD_GRID_SOURCE_RULE_DEFINITION
} WoodGridSourceKind;
typedef struct {unsigned char bytes[64];} WoodGridSourceKey;
typedef struct {GeoProviderToken grid,parameter,engineering_binding,region_keys;} WoodGridSourceTokens;
typedef struct WoodGridSources WoodGridSources;
/* Keys use canonical fixed-width big-endian fields, never C padding. */
GeoSourceRef wood_grid_source_ref(GeoProviderToken,WoodGridSourceKind,uint32_t,WoodGridSourceKey *);
GeoSourceRef wood_grid_dimension_source_ref(GeoProviderToken,uint32_t,int,int,WoodGridSourceKey *);
GeoSourceRef wood_grid_line_source_ref(GeoProviderToken,uint32_t,uint32_t,int,int64_t,bool,bool,int64_t,WoodGridSourceKey *);
GeoSourceRef wood_grid_rule_source_ref(GeoProviderToken,const GeoGridRuleLineRef *,uint32_t,WoodGridSourceKey *);
GeoSourceRef wood_grid_rule_definition_source_ref(GeoProviderToken,uint32_t,uint32_t,WoodGridSourceKey *);
bool wood_grid_source_decode(const GeoSourceRef *,WoodGridSourceKind *,uint32_t *);
/* Register before the first graph request. Base engineering must already use
 * this candidate's K graph. A zero parameter token keeps the base resolver. */
WoodGridSources *wood_grid_sources_create(GeoEvalContext *,WoodGridSourceTokens,const WoodGridContext *);
bool wood_grid_sources_bind(WoodGridSources *,WoodGridContext *);
/* Enumerate authored identities without evaluating unused geometry/fields. */
bool wood_grid_sources_definitions(WoodGridSources *,char *,size_t);
/* Read authored application policy without requesting dimensions or geometry. */
bool wood_grid_sources_definition(WoodGridSources *,uint32_t,WoodGridApplication *);
bool wood_grid_sources_application(WoodGridSources *,uint32_t,char *,size_t);
bool wood_grid_sources_dimension(WoodGridSources *,uint32_t,int,int,GeoCoord *,char *,size_t);
/* anchor=true applies the existing band/stagger anchor policy; false invokes
 * ordinary grid_line_coord_in. total follows that ordinary query's contract. */
bool wood_grid_sources_line(WoodGridSources *,uint32_t,uint32_t,int,int64_t,bool anchor,bool has_band,int64_t,GeoCoord *,size_t *,char *,size_t);
bool wood_grid_sources_cell(WoodGridSources *,uint32_t,GeoRect2 *,char *,size_t);
bool wood_grid_sources_rule_line(WoodGridSources *,const GeoGridRuleLineRef *,uint32_t,GeoCoord *,GeoRect2 *,char *,size_t);
/* No K calls during teardown. Once destroyed the graph may only be destroyed;
 * its provider pointer and borrowed definitions/regions are no longer live. */
void wood_grid_sources_destroy(WoodGridSources *);
#endif
