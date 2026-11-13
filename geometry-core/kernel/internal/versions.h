#ifndef GEO_KERNEL_VERSIONS_INTERNAL_H
#define GEO_KERNEL_VERSIONS_INTERNAL_H
#include "../versions.h"

/* Fixed POD backing for a document/candidate value. No borrowed pointers. */
typedef struct {
    unsigned char key[GEO_VERSION_KEY_BYTES];
    size_t key_length;
    uint32_t version;
    unsigned char content[GEO_VERSION_CONTENT_BYTES+1];
    size_t content_length;
    char fingerprint[GEO_VERSION_FINGERPRINT_BYTES+1];
    GeoVersionField fields[GEO_VERSION_FIELD_CAPACITY];
    size_t field_count;
    char schema[GEO_VERSION_SCHEMA_BYTES+1];
    size_t schema_length;
} GeoVersionRecord;
struct GeoVersionStore {
    GeoVersionRecord records[GEO_VERSION_CAPACITY];
    size_t count;
};
#endif
