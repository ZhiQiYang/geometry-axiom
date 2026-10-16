/* Candidate-local D41/D42/D4 evaluation. Definitions and geometric views
 * borrow the same candidate and this handle until graph teardown. */
#ifndef GEOMETRY_WOODWORKING_FINISH_SOURCES_H
#define GEOMETRY_WOODWORKING_FINISH_SOURCES_H
#include "derived_placement.h"
#ifndef GEO_KERNEL_SOURCE_H
#include "source.h"
#endif
typedef enum {
    WOOD_FINISH_SOURCE_DEFINITION=1,
    WOOD_FINISH_SOURCE_CHECK,
    WOOD_FINISH_SOURCE_FRAME,
    WOOD_FINISH_SOURCE_REGION,
    WOOD_FINISH_SOURCE_BOUNDARY_REGION,
    WOOD_FINISH_SOURCE_COLUMN_BOX,
    WOOD_FINISH_SOURCE_BEAM_BOX,
    WOOD_FINISH_SOURCE_FILL_DEFINITION,
    WOOD_FINISH_SOURCE_FILL_FRAME,
    WOOD_FINISH_SOURCE_PANEL_LENGTH,
    WOOD_FINISH_SOURCE_PANEL_WIDTH,
    WOOD_FINISH_SOURCE_PANEL_THICKNESS,
    WOOD_FINISH_SOURCE_GAP,
    WOOD_FINISH_SOURCE_STAGGER,
    WOOD_FINISH_SOURCE_THRESHOLD,
    WOOD_FINISH_SOURCE_PANEL_DEFINITION,
    WOOD_FINISH_SOURCE_DERIVED_DEFINITION,
    WOOD_FINISH_SOURCE_DERIVED_H,
    WOOD_FINISH_SOURCE_DERIVED_FRAME,
    WOOD_FINISH_SOURCE_DERIVED_REGION,
    WOOD_FINISH_SOURCE_DERIVED_POLICY,
    WOOD_FINISH_SOURCE_BOUNDARY_POLICY
} WoodFinishSourceKind;
typedef struct {unsigned char bytes[5];} WoodFinishSourceKey;
typedef struct {GeoProviderToken finish,parameter;} WoodFinishSourceTokens;
typedef struct WoodFinishSources WoodFinishSources;
GeoSourceRef wood_finish_source_ref(GeoProviderToken,WoodFinishSourceKind,uint32_t,WoodFinishSourceKey *);
bool wood_finish_source_decode(const GeoSourceRef *,WoodFinishSourceKind *,uint32_t *);
/* Base engineering must already be bound to the same K graph. The parameter
 * token identifies K's shared parameter provider; 0 keeps only the base fact
 * callback for standalone clients without a parameter store. Register before
 * the first source request. No candidate facts are read during create/bind. */
WoodFinishSources *wood_finish_sources_create(GeoEvalContext *,WoodFinishSourceTokens,const WoodDerivedContext *);
bool wood_finish_sources_bind(WoodFinishSources *,WoodDerivedContext *);
bool wood_finish_sources_bind_finish(WoodFinishSources *,WoodFinishContext *);
/* Definition-only reads consume the actual K return value. The copy contains
 * authored inputs only; these helpers neither evaluate geometry nor write the
 * candidate. Failed reads leave the caller's output unchanged. */
bool wood_finish_sources_surface_definition(WoodFinishSources *,uint32_t,FinishSurface *);
bool wood_finish_sources_fill_definition(WoodFinishSources *,uint32_t,PanelFill *);
bool wood_finish_sources_derived_definition(WoodFinishSources *,uint32_t,DerivedPlacement *);
/* H can return DERIVED_FRAME/DERIVED_REGION refs from its neutral placement
 * provider. Evaluating them runs the direct W policy, never placement caches.
 * Read returns the same graph value including fixities for W/H callers. */
bool wood_finish_sources_read_derived(WoodFinishSources *,uint32_t,WoodDerivedValue *);
/* R41 keys and fixities are canonical definition values. All geometry copied
 * by read_derived is the returned K REGION_SET/FRAME/QUANTITY, not a side cache. */
bool wood_finish_sources_edge_key(WoodFinishSources *,uint32_t,size_t,int,size_t,char *,size_t);
bool wood_finish_sources_edge_resolve(WoodFinishSources *,uint32_t,const char *,int *,int *);
bool wood_finish_sources_definitions(WoodFinishSources *);
/* Both teardown orders are safe. After handle destruction the graph may only
 * be destroyed; its borrowed views and provider user pointer are no longer live. */
void wood_finish_sources_destroy(WoodFinishSources *);
#endif
