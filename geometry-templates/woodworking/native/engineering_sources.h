#ifndef WOOD_ENGINEERING_SOURCES_H
#define WOOD_ENGINEERING_SOURCES_H
#include "engineering.h"
#include "version_sources.h"
#ifndef GEO_KERNEL_SOURCE_H
#include "source.h"
#endif
typedef struct WoodEngineeringSources WoodEngineeringSources;
/* Internal typed-source wire identity. Stored bindings are keyed by the four
 * target fields, never by their changing source/override values. A temporary
 * nonstored request carries its entire canonical payload in its own key. */
#define WOOD_ENGINEERING_BINDING_CONTENT_MAX (17+2*(32+GEO_NAMED_VALUE_NAME_BYTES))
#define WOOD_ENGINEERING_BINDING_KEY_MAX (1+WOOD_ENGINEERING_BINDING_CONTENT_MAX)
typedef enum {
    WOOD_BINDING_SOURCE_DEFINITION=1,WOOD_BINDING_SOURCE_EFFECTIVE=2,
    WOOD_BINDING_SOURCE_REQUEST_DEFINITION=3,WOOD_BINDING_SOURCE_REQUEST_VALUE=4
} WoodEngineeringBindingSourceKind;
typedef struct {unsigned char bytes[WOOD_ENGINEERING_BINDING_KEY_MAX];size_t size;} WoodEngineeringBindingSourceKey;
/* Canonical payload: target (four BE32), source, hasOverride byte, and an
 * optional override source. Source: kind/field BE32, value signed BE64,
 * string byte length BE32 + exact bytes, version BE32, parameter.set byte,
 * parameter id and field id BE32. No C padding or derived value is included.
 * Invalid/truncated/noncanonical input changes no output. */
size_t wood_engineering_binding_encode(const EngBinding *,unsigned char out[WOOD_ENGINEERING_BINDING_CONTENT_MAX]);
bool wood_engineering_binding_decode(const void *,size_t,EngBinding *);
GeoSourceRef wood_engineering_binding_source_ref(GeoProviderToken,WoodEngineeringBindingSourceKind,
    const EngBinding *,WoodEngineeringBindingSourceKey *);
bool wood_engineering_binding_source_decode(const GeoSourceRef *,WoodEngineeringBindingSourceKind *,EngTarget *,EngBinding *request);
typedef struct {
    GeoProviderToken dimension,binding,definition,named,parameter,version;
} WoodEngineeringSourceTokens;
/* Mutable W archive metadata is a separate definition from immutable K
 * versions. Bytes: material/method byte (0/1), BE32 version, BE32 id length,
 * id bytes, canonical archived byte (0/1). No quantity work or cache refresh. */
#define WOOD_VERSION_METADATA_MAX (10+ENG_ID_MAX-1)
size_t wood_engineering_version_metadata_encode(int,const EngVersionRef *,bool,void *,size_t);
bool wood_engineering_version_metadata_decode(const void *,size_t,int *,EngVersionRef *,bool *);
/* The context and its stores borrow the same isolated candidate as evaluation.
 * Destroy this binding before releasing that candidate; K owns copied keys. */
WoodEngineeringSources *wood_engineering_sources_register(GeoEvalContext *,const WoodEngineeringContext *,WoodEngineeringSourceTokens);
void wood_engineering_sources_destroy(WoodEngineeringSources *);
void wood_engineering_sources_bind(WoodEngineeringSources *,WoodEngineeringContext *);
/* Complete the candidate's published definition inventory after normal W
 * validation/rebuild. This requests only canonical definitions, never unused
 * dimensions or geometry; method slots retain DefinitionRequired edges. */
bool wood_engineering_sources_definitions(WoodEngineeringSources *);
bool wood_engineering_sources_metadata(WoodEngineeringSources *);
const EngineeringState *wood_engineering_sources_state(const WoodEngineeringSources *);
GeoEvalContext *wood_engineering_sources_context(const WoodEngineeringSources *);
#endif
