/* Actual section-profile evaluation through K's candidate-local graph.
 * Register before the first request. Values borrow the same candidate stores
 * and this handle's stable view storage while either can still be queried. */
#ifndef GEOMETRY_WOODWORKING_SECTION_PROFILE_SOURCES_H
#define GEOMETRY_WOODWORKING_SECTION_PROFILE_SOURCES_H
#include "section_profile.h"
#ifndef GEO_KERNEL_SOURCE_H
#include "source.h"
#endif
typedef enum {
    WOOD_SP_SOURCE_PROFILE_DEFINITION=1,
    WOOD_SP_SOURCE_MEMBER_DEFINITION,
    WOOD_SP_SOURCE_MEMBER_A,
    WOOD_SP_SOURCE_MEMBER_B,
    WOOD_SP_SOURCE_MEMBER_REGION,
    WOOD_SP_SOURCE_RUN_DEFINITION,
    WOOD_SP_SOURCE_RUN_LENGTH,
    WOOD_SP_SOURCE_RUN_FRAME,
    WOOD_SP_SOURCE_RUN_REGION,
    WOOD_SP_SOURCE_HOST_FRAME,
    WOOD_SP_SOURCE_HOST_REGION
} WoodSectionProfileSourceKind;
typedef struct {unsigned char bytes[5];} WoodSectionProfileSourceKey;
typedef struct WoodSectionProfileSources WoodSectionProfileSources;
GeoSourceRef wood_sp_source_ref(GeoProviderToken,WoodSectionProfileSourceKind,uint32_t,WoodSectionProfileSourceKey *);
bool wood_sp_source_decode(const GeoSourceRef *,WoodSectionProfileSourceKind *,uint32_t *);
/* Copies the base context, not the candidate state. Base callbacks stay bound
 * to that candidate. Does not evaluate or describe any source during create. */
WoodSectionProfileSources *wood_sp_sources_create(GeoEvalContext *,GeoProviderToken,const WoodSectionProfileContext *);
bool wood_sp_sources_bind(WoodSectionProfileSources *,WoodSectionProfileContext *);
/* Either teardown order is supported. After destroying the handle, do not
 * evaluate or inspect borrowed values in the graph; only destroy the graph.
 * This function does not call K, so it is also safe after graph destruction. */
void wood_sp_sources_destroy(WoodSectionProfileSources *);
#endif
