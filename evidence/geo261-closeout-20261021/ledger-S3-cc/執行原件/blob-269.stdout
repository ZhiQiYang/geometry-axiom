/* Immutable, owned, typed version sources. Identity and canonical content are
 * opaque bytes: a caller supplies its schema and namespace, never this store.
 * No text terminator is included in either byte length. */
#ifndef GEO_KERNEL_VERSIONS_H
#define GEO_KERNEL_VERSIONS_H
#include "exact.h"
#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>

#define GEO_VERSION_CAPACITY 128
#define GEO_VERSION_KEY_BYTES 128
#define GEO_VERSION_CONTENT_BYTES 1024
#define GEO_VERSION_FIELD_CAPACITY 16
#define GEO_VERSION_FINGERPRINT_BYTES 64
#define GEO_VERSION_SCHEMA_BYTES 96
#define GEO_VERSION_DECIMAL_BYTES 128

typedef enum {
    GEO_VERSION_OK=0,
    GEO_VERSION_MISSING,
    GEO_VERSION_DUPLICATE_FIELD,
    GEO_VERSION_CAPACITY_EXCEEDED,
    GEO_VERSION_INVALID,
    GEO_VERSION_FINGERPRINT,
    GEO_VERSION_IMMUTABLE,
    GEO_VERSION_MEMORY,
    GEO_VERSION_EXACT,
    GEO_VERSION_DECIMAL,
    GEO_VERSION_UNIT,
    GEO_VERSION_INTEGER,
    GEO_VERSION_RANGE
} GeoVersionStatus;

typedef struct {
    const void *key;
    size_t key_length;
    uint32_t version;
} GeoVersionIdentity;
typedef enum { GEO_VERSION_QUANTITY=0, GEO_VERSION_DECIMAL_LITERAL=1 } GeoVersionFieldKind;
typedef struct {
    uint32_t id;
    GeoQuantity value;
    GeoVersionFieldKind kind;
    /* Decimal literals retain every byte. value.unit supplies the unit; its
     * numerator/denominator are unused for this kind. Conversion is a separate
     * use-site request, so legal source precision never depends on int64. */
    char literal[GEO_VERSION_DECIMAL_BYTES+1];
    size_t literal_length;
} GeoVersionField;
typedef struct {
    GeoVersionIdentity identity;
    const void *content;
    size_t content_length;
    const char *fingerprint;
    size_t fingerprint_length;
    const GeoVersionField *fields;
    size_t field_count;
    const char *schema;
    size_t schema_length;
} GeoVersionDefinition;
typedef GeoVersionDefinition GeoVersionView;
typedef struct {
    GeoVersionIdentity identity;
    GeoVersionField field;
} GeoVersionFieldView;
typedef struct GeoVersionStore GeoVersionStore;

/* Failed create/clone/read calls leave their output unchanged. These calls
 * require non-NULL stores/output pointers. equal(NULL,...) is false;
 * count(NULL) is zero and destroy(NULL) is harmless. */
GeoVersionStatus geo_versions_create(GeoVersionStore **out);
GeoVersionStatus geo_versions_clone(const GeoVersionStore *source,GeoVersionStore **out);
void geo_versions_destroy(GeoVersionStore *store);
bool geo_versions_equal(const GeoVersionStore *a,const GeoVersionStore *b);
size_t geo_versions_count(const GeoVersionStore *store);

/* Views borrow read-only owned storage, valid until that store is destroyed.
 * Appending records and idempotent puts do not invalidate any borrowed view.
 * at() follows insertion order; equal() compares identities independent of it.
 * Field IDs may be zero; versions and key lengths must be nonzero. */
GeoVersionStatus geo_versions_at(const GeoVersionStore *store,size_t index,GeoVersionView *out);
GeoVersionStatus geo_versions_find(const GeoVersionStore *store,GeoVersionIdentity identity,GeoVersionView *out);
GeoVersionStatus geo_versions_field(const GeoVersionStore *store,GeoVersionIdentity identity,uint32_t field_id,GeoVersionFieldView *out);
/* Rational conversion is exact or reports its int64 representation limit.
 * Integer use-site validation accepts arbitrary leading/trailing zeroes and
 * checks fractional, unit and caller-supplied range rules without rounding.
 * Every failed conversion leaves out unchanged. */
GeoVersionStatus geo_version_field_quantity(const GeoVersionField *field,GeoQuantity *out,GeoExactStatus *exact_detail);
GeoVersionStatus geo_version_field_integer(const GeoVersionField *field,GeoQuantityUnit unit,int64_t minimum,int64_t maximum,int64_t *out);
GeoVersionStatus geo_versions_integer(const GeoVersionStore *store,GeoVersionIdentity identity,uint32_t field_id,GeoQuantityUnit unit,int64_t minimum,int64_t maximum,int64_t *out);

/* Fingerprints are exactly 64 lowercase hexadecimal bytes and are recomputed
 * over the complete canonical content, including embedded zero bytes. Content
 * may be empty. The store does not parse or canonicalize those opaque bytes;
 * the caller's schema must derive the fields consistently from that content.
 * Schema is an optional opaque byte string (zero bytes are permitted); it is
 * owned and immutable separately from the legacy content fingerprint. Fields
 * are sorted by ID. Quantities normalize exactly; decimal literal spelling is
 * retained and validated as optional sign, digits, optional dot and digits.
 * A repeat identity succeeds only for identical content and normalized fields,
 * including at capacity. Every failure leaves the entire store unchanged.
 * exact_detail, when supplied, is reset to GEO_EXACT_OK and reports the exact
 * validation cause on GEO_VERSION_EXACT. No integer/range use-site policy is
 * imposed here: legal fractional sources remain fractional. */
GeoVersionStatus geo_versions_put(GeoVersionStore *store,const GeoVersionDefinition *definition,GeoExactStatus *exact_detail);
/* The identical admission check without mutation lets a template enforce its
 * own per-kind capacity after fingerprint/immutable diagnostics, then put. */
GeoVersionStatus geo_versions_check(const GeoVersionStore *store,const GeoVersionDefinition *definition,GeoExactStatus *exact_detail);
#endif
