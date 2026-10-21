/* Bounded W wire values. These codecs do not evaluate sources or validate
 * grid policy: rejected/incomplete candidate definitions remain representable. */
#ifndef GEOMETRY_WOODWORKING_GRID_DEFINITION_CODEC_H
#define GEOMETRY_WOODWORKING_GRID_DEFINITION_CODEC_H
#include "grid_application.h"
#ifndef GEO_KERNEL_SOURCE_H
#include "source.h"
#endif

#define WOOD_GRID_CODEC_MAX_BYTES 16384
#define WOOD_GRID_SYSTEM_VALUE_SCHEMA "wood.grid.system-value/1"
#define WOOD_GRID_APPLICATION_VALUE_SCHEMA "wood.grid.application-value/1"

/* Authored schemas and field order match grid_sources.c. Each axis ends with
 * card_length and each system with its D64 card reference (set, parameter id,
 * u field id, v field id); a card-controlled step/body slot is masked on the
 * authored wire like a parameter slot. Every integer is
 * BE64, signed fields use two's-complement bits, and strings are byte-length
 * prefixed UTF-8 without embedded NUL. Array counts are bounded by the public
 * grid capacities; scalar fields are checked before narrowing to their type.
 * All outputs, including main_along, remain unchanged on any failure.
 *
 * prior is optional and supplies only omitted/evaluated cache fields. A
 * parameter or engineering-bound numeric slot is zero on the authored wire;
 * its old numeric cache is retained, or becomes zero without prior. Derived
 * application axes/main_along and every application's lattice caches are
 * absent from the authored wire and likewise retain prior values. */
bool wood_grid_decode_system(const GeoDefinitionValue *,uint32_t expected_id,
    const GeoGridSystem *prior,GeoGridSystem *out,int *main_along);
bool wood_grid_decode_binding(const GeoDefinitionValue *,uint32_t expected_id,
    GeoGridBinding *out);
bool wood_grid_decode_application(const GeoDefinitionValue *,uint32_t expected_id,
    const WoodGridApplication *prior,WoodGridApplication *out);
bool wood_grid_decode_rule(const GeoDefinitionValue *,uint32_t expected_system_id,
    uint32_t expected_rule_key,GeoGridRule *out);

/* Value schemas retain all numeric fields, including parameter caches.
 * System values follow authored system order; application values always
 * contain the authored prefix, main_along, both axes, then per-axis
 * lattice_base/lattice_step/lattice_index. Axis engineering-bound flags are
 * zero in value schemas: the resolved numeric value is present instead.
 * No C padding or inactive array storage enters the wire. Writers stage into
 * a bounded local buffer; bytes and *size are unchanged on failure. */
bool wood_grid_encode_system_value(const GeoGridSystem *,int main_along,
    unsigned char *bytes,size_t capacity,size_t *size);
bool wood_grid_decode_system_value(const GeoDefinitionValue *,uint32_t expected_id,
    GeoGridSystem *out,int *main_along);
bool wood_grid_encode_application_value(const WoodGridApplication *,
    unsigned char *bytes,size_t capacity,size_t *size);
bool wood_grid_decode_application_value(const GeoDefinitionValue *,uint32_t expected_id,
    WoodGridApplication *out);
#endif
