/* D32-D34 candidate provenance. Canonical definitions borrow candidate storage;
 * quantities are evaluated by the original W engineering source policy. */
#ifndef GEOMETRY_WOODWORKING_ASSEMBLY_SOURCES_H
#define GEOMETRY_WOODWORKING_ASSEMBLY_SOURCES_H
#include "assembly.h"
#ifndef GEO_KERNEL_SOURCE_H
#include "source.h"
#endif
typedef enum {
    WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION=1,
    WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,
    WOOD_ASSEMBLY_SOURCE_BINDING_CHECK,
    WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION,
    WOOD_ASSEMBLY_SOURCE_SLOT_A,WOOD_ASSEMBLY_SOURCE_SLOT_B,
    WOOD_ASSEMBLY_SOURCE_INSTANCE_DEFINITION,
    WOOD_ASSEMBLY_SOURCE_MAPPING_DEFINITION,
    WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION,
    WOOD_ASSEMBLY_SOURCE_GENERATED_A,WOOD_ASSEMBLY_SOURCE_GENERATED_B,
    WOOD_ASSEMBLY_SOURCE_INSTANCE_CHECK,
    WOOD_ASSEMBLY_SOURCE_GENERATED
} WoodAssemblySourceKind;
typedef struct {unsigned char bytes[13];} WoodAssemblySourceKey;
typedef struct WoodAssemblySources WoodAssemblySources;
/* RULE uses id/version/sub=0; SLOT uses binding id/version=0/slot id;
 * GENERATED uses instance id/version=0/member id. Other kinds use id/0/0.
 * Integers are canonical big endian; values and C padding never enter keys. */
GeoSourceRef wood_assembly_source_ref(GeoProviderToken,WoodAssemblySourceKind,uint32_t id,uint32_t version,uint32_t sub,WoodAssemblySourceKey *);
bool wood_assembly_source_decode(const GeoSourceRef *,WoodAssemblySourceKind *,uint32_t *,uint32_t *,uint32_t *);
/* Register before first request; engineering must share this graph/candidate.
 * Create/bind performs no source evaluation and reads no host geometry. */
WoodAssemblySources *wood_assembly_sources_create(GeoEvalContext *,GeoProviderToken,const WoodAssemblyContext *);
bool wood_assembly_sources_bind(WoodAssemblySources *,WoodAssemblyContext *);
/* Materialize canonical authored definitions (including unused rules/bindings
 * and nullable slots), without demanding quantities or running I42 checks.
 * Invoke after normal successful validation; normal rebuild also visits these. */
bool wood_assembly_sources_definitions(WoodAssemblySources *);
bool wood_assembly_sources_generated(WoodAssemblySources *,uint32_t instance_id,uint32_t member_id,WoodAssemblyDefinition *);
bool wood_assembly_sources_member_dimensions(WoodAssemblySources *,uint32_t instance_id,uint32_t member_id,GeoCoord *,GeoCoord *);
/* No placement/pose evaluation here. H can consume these returned quantities
 * in its existing owned-member pose provider without advancing I42 checks. */
bool wood_assembly_sources_owned_dimensions(WoodAssemblySources *,uint32_t timber_id,GeoCoord *,GeoCoord *);
/* Both destruction orders are safe. After this handle is destroyed the graph
 * may only be destroyed; its borrowed views/provider pointer are no longer live. */
void wood_assembly_sources_destroy(WoodAssemblySources *);
#endif
