/* Authored woodworking facts in one candidate. No pose, derived length or
 * rebuilt coordinate cache is presented as an authored definition. */
#ifndef GEOMETRY_WOODWORKING_DEFINITION_SOURCES_H
#define GEOMETRY_WOODWORKING_DEFINITION_SOURCES_H
#include "../native/document.h"
#ifndef GEO_KERNEL_SOURCE_H
#include "source.h"
#endif
#ifndef GEO_KERNEL_ENCLOSURE_SOURCES_H
#include "enclosure_sources.h"
#endif

typedef enum {
    WOOD_DEFINITION_MEMBER=1, WOOD_DEFINITION_PLACEMENT,
    WOOD_DEFINITION_MEMBER_A, WOOD_DEFINITION_MEMBER_B,
    WOOD_DEFINITION_COLUMN, WOOD_DEFINITION_BEAM, WOOD_DEFINITION_BOUNDARY
} WoodDefinitionKind;
typedef struct {unsigned char bytes[5];} WoodDefinitionKey;
typedef struct {
    uint32_t id; bool auto_length; WoodMemberRole role; GeoCoord priority;
    bool literal[2]; GeoCoord dimension[2];
} WoodMemberDefinition;
/* 接觸查詢只需要這三個定義欄位；讀取時仍驗證完整 placement 編碼。 */
typedef struct {uint32_t placement_id;int length_direction;uint64_t order;} WoodMemberPlacementContact;
typedef struct {
    const WoodDocument *document;
    const GeoRegionStore *regions;
    GeoProviderToken enclosure_token,region_token;
} WoodDefinitionContext;
typedef struct WoodDefinitionSources WoodDefinitionSources;

/* Keys are kind + big endian u32 id. Definitions use explicit integer and
 * length-prefixed string fields, never struct bytes, pointers or padding. */
GeoSourceRef wood_definition_source_ref(GeoProviderToken,WoodDefinitionKind,uint32_t,WoodDefinitionKey *);
bool wood_definition_source_decode(const GeoSourceRef *,WoodDefinitionKind *,uint32_t *);
WoodDefinitionSources *wood_definition_sources_create(GeoEvalContext *,GeoProviderToken,const WoodDefinitionContext *);
void wood_definition_sources_destroy(WoodDefinitionSources *);
/* Read helpers decode the actual returned source value. Failure preserves out. */
bool wood_definition_sources_member(WoodDefinitionSources *,uint32_t,WoodMemberDefinition *);
bool wood_definition_sources_placement(WoodDefinitionSources *,uint32_t,WoodMemberPlacement *);
bool wood_definition_sources_placement_contact(WoodDefinitionSources *,uint32_t,WoodMemberPlacementContact *);
bool wood_definition_sources_dimension(WoodDefinitionSources *,uint32_t,bool,GeoCoord *);
bool wood_definition_sources_column(WoodDefinitionSources *,uint32_t,WoodColumn *);
bool wood_definition_sources_beam(WoodDefinitionSources *,uint32_t,WoodBeam *);
bool wood_definition_sources_boundary(WoodDefinitionSources *,uint32_t,WoodBoundaryPolicy *);
/* Invoke after ordinary validation. Enumerates unused definitions without
 * demanding unplaced poses, inactive dimensions or live RC room heights. */
bool wood_definition_sources_complete(WoodDefinitionSources *);
#endif
