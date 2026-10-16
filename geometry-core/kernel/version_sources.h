/* Candidate-local typed sources for immutable version records. */
#ifndef GEO_KERNEL_VERSION_SOURCES_H
#define GEO_KERNEL_VERSION_SOURCES_H
#include "versions.h"
#include "source.h"

typedef struct GeoVersionSources GeoVersionSources;
typedef enum { GEO_VERSION_SOURCE_DEFINITION=1,GEO_VERSION_SOURCE_FIELD=2 } GeoVersionSourceKind;
#define GEO_VERSION_SOURCE_KEY_MAX (13+GEO_VERSION_KEY_BYTES)
#define GEO_VERSION_DEFINITION_MAX (24+GEO_VERSION_KEY_BYTES+GEO_VERSION_CONTENT_BYTES+GEO_VERSION_FINGERPRINT_BYTES+GEO_VERSION_SCHEMA_BYTES+GEO_VERSION_FIELD_CAPACITY*(26+GEO_VERSION_DECIMAL_BYTES))
typedef struct {unsigned char bytes[GEO_VERSION_SOURCE_KEY_MAX];size_t size;} GeoVersionSourceKey;
/* Key: kind byte, BE32 key length/version/field, then opaque identity bytes.
 * Definition keys reserve field=0. All failed calls preserve their outputs. */
GeoSourceRef geo_version_source_ref(GeoProviderToken,GeoVersionSourceKind,GeoVersionIdentity,uint32_t,GeoVersionSourceKey *);
bool geo_version_source_decode(const GeoSourceRef *,GeoVersionSourceKind *,GeoVersionIdentity *,uint32_t *);
/* geometry.version/1 carries complete immutable identity, content, fingerprint,
 * schema and sorted typed fields. Integers are big endian; no C padding.
 * Decode borrows bytes from input and writes fields into the supplied array.
 * Decimal spelling is retained. Quantities must already be normalized; decimal
 * numerator/denominator are canonicalized to unused 0/1. Invalid spelling,
 * ordering or fingerprints reject without output writes. Neither operation
 * converts a decimal literal into a numeric value. */
size_t geo_version_definition_encode(const GeoVersionView *,void *,size_t);
bool geo_version_definition_decode(const void *,size_t,GeoVersionView *,GeoVersionField [GEO_VERSION_FIELD_CAPACITY]);
/* Registration borrows one candidate's immutable store. Destroy this handle
 * after its graph and before the store; reset requires a fresh registration.
 * A field consumes the actual returned complete definition, never the store
 * again. Description and complete inventory request no quantity values. */
GeoVersionSources *geo_version_sources_register(GeoEvalContext *,const GeoVersionStore *,GeoProviderToken);
void geo_version_sources_destroy(GeoVersionSources *);
bool geo_version_sources_definitions(GeoVersionSources *);
const GeoVersionStore *geo_version_sources_store(const GeoVersionSources *);
const GeoEvalContext *geo_version_sources_context(const GeoVersionSources *);
#endif
