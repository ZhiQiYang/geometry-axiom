/* Owned grid-source and stable-vertex binding state. This first store slice
 * does not own application/child graphs, role preferences or command text. */
#ifndef GEO_KERNEL_GRID_STORE_H
#define GEO_KERNEL_GRID_STORE_H
#include "grid.h"
#include "parameters.h"

#define GEO_GRID_SYSTEM_CAPACITY 16
#define GEO_GRID_BINDING_CAPACITY 32
#define GEO_GRID_RULE_CAPACITY 32
#define GEO_GRID_COORDINATE_CAPACITY 64
#define GEO_GRID_NAME_CAPACITY 97

typedef enum {
    GEO_GRID_SOURCE_NONE = 0, GEO_GRID_SOURCE_EXPLICIT, GEO_GRID_SOURCE_SERIES,
    GEO_GRID_SOURCE_REPEAT, GEO_GRID_SOURCE_REPEAT_BODY_GAP, GEO_GRID_SOURCE_BODY_GAP
} GeoGridSource;
typedef struct {
    int source;
    GeoCoord coords[GEO_GRID_COORDINATE_CAPACITY];
    size_t count;
    GeoCoord start, step;
    size_t series_count;
    GeoCoord body, gap, anchor;
    bool anchor_explicit;
    /* phase, step, body, gap, anchor, stagger. With a reference set, the
     * corresponding numeric field is an evaluated cache, not another source. */
    GeoParameterRef parameters[6];
    GeoCoord stagger;
    bool stagger_set;
} GeoGridAxisDef;
typedef struct {
    uint32_t key;
    char name[GEO_GRID_NAME_CAPACITY];
    bool all_cells;
    int64_t cell[2];
    unsigned divisions[2];
} GeoGridRule;
typedef struct {
    uint32_t id;
    char name[GEO_GRID_NAME_CAPACITY];
    GeoGridAxisDef axis[2];
    GeoGridRule rules[GEO_GRID_RULE_CAPACITY];
    size_t rule_count;
    uint32_t next_rule_key; /* 0 is exhausted; clone restores this exact value. */
} GeoGridSystem;
typedef struct {
    uint32_t id, boundary_id, system_id, vertex_key;
    int64_t cell[2];
    uint32_t anchor_num[2], anchor_den[2];
} GeoGridBinding;
typedef struct {
    uint32_t grid_id, system_id, rule_key;
    int64_t cell[2];
    int axis;
    uint32_t inner_index;
} GeoGridRuleLineRef;
typedef struct {
    GeoGridAxisDef axis[2];
    GeoLattice lattice[2];
} GeoGridBindingCache;

typedef enum {
    GEO_GRID_STORE_OK = 0, GEO_GRID_STORE_INVALID, GEO_GRID_STORE_CAPACITY,
    GEO_GRID_STORE_SYSTEM_MISSING, GEO_GRID_STORE_BINDING_MISSING,
    GEO_GRID_STORE_SYSTEM_NAME, GEO_GRID_STORE_AXIS_INVALID, GEO_GRID_STORE_SYSTEM_EMPTY,
    GEO_GRID_STORE_MIXED_SPACE, GEO_GRID_STORE_SPACE_CHANGE,
    GEO_GRID_STORE_PARAMETER_SOURCE, GEO_GRID_STORE_PARAMETER_AXIS,
    GEO_GRID_STORE_STAGGER_SOURCE, GEO_GRID_STORE_STAGGER_PITCH,
    GEO_GRID_STORE_STAGGER_ZERO, GEO_GRID_STORE_STAGGER_MULTIPLE, GEO_GRID_STORE_STAGGER_OVERFLOW,
    GEO_GRID_STORE_RULE_CAPACITY, GEO_GRID_STORE_RULE_SOURCE, GEO_GRID_STORE_RULE_KEY,
    GEO_GRID_STORE_RULE_NAME, GEO_GRID_STORE_RULE_DIVISIONS, GEO_GRID_STORE_RULE_NOT_DIVISIBLE,
    GEO_GRID_STORE_RULE_CELL_RANGE, GEO_GRID_STORE_RULE_OVERLAP,
    GEO_GRID_STORE_BINDING_SOURCE, GEO_GRID_STORE_BINDING_CELL_RANGE,
    GEO_GRID_STORE_BINDING_ANCHOR, GEO_GRID_STORE_BINDING_SHIFT_RANGE,
    GEO_GRID_STORE_BINDING_TRANSLATION_RANGE
} GeoGridStoreStatus;
typedef struct {
    GeoGridStoreStatus status;
    uint32_t system_id, binding_id, rule_key, other_rule_key;
    int axis, field; /* -1 when no axis/field applies. */
    GeoCoord pitch, value;
} GeoGridStoreError;

typedef struct GeoGridStore GeoGridStore;
/* Coordinate callbacks implement the already-selected dimensional source;
 * success supplies bounded integer mm, failure leaves out unchanged. Vertex
 * callbacks resolve the exact region-local key and supply bounded coordinates. */
typedef bool (*GeoGridCoordinateResolver)(void *, GeoParameterRef, GeoCoord *);
typedef bool (*GeoGridVertexResolver)(void *, uint32_t boundary_id, uint32_t vertex_key, GeoPoint2 *);

GeoGridStore *geo_grid_store_create(void);
GeoGridStore *geo_grid_store_clone(const GeoGridStore *store);
void geo_grid_store_destroy(GeoGridStore *store);
size_t geo_grid_systems_count(const GeoGridStore *store);
const GeoGridSystem *geo_grid_systems_at(const GeoGridStore *store, size_t index);
const GeoGridSystem *geo_grid_systems_values(const GeoGridStore *store);
const GeoGridSystem *geo_grid_systems_find(const GeoGridStore *store, uint32_t id);
/* Structural staging only: owns bounded arrays/text and supplied caches.
 * Complete candidate validation and cross-object deletion guards are separate. */
bool geo_grid_systems_put(GeoGridStore *store, const GeoGridSystem *system);
bool geo_grid_systems_remove(GeoGridStore *store, uint32_t id);
/* New declarations begin with no rules and next=1. Replacement preserves all
 * rule state and cannot silently change the finite/infinite index space. */
bool geo_grid_systems_redeclare(GeoGridStore *store, const GeoGridSystem *definition, GeoGridStoreError *error);
size_t geo_grid_bindings_count(const GeoGridStore *store);
const GeoGridBinding *geo_grid_bindings_at(const GeoGridStore *store, size_t index);
const GeoGridBinding *geo_grid_bindings_values(const GeoGridStore *store);
const GeoGridBinding *geo_grid_bindings_find(const GeoGridStore *store, uint32_t id);
bool geo_grid_bindings_put(GeoGridStore *store, const GeoGridBinding *binding);
bool geo_grid_bindings_remove(GeoGridStore *store, uint32_t id);
/* Validates and reduces both fractions atomically; does not resolve sources. */
bool geo_grid_binding_normalize(GeoGridBinding *binding);

bool geo_grid_axis_is_infinite(const GeoGridAxisDef *axis);
bool geo_grid_system_is_infinite(const GeoGridSystem *system);
/* pitch/phase require bounded numeric fields, as supplied by accepted source
 * definitions or a successful coordinate resolver; the derived phase may be
 * outside the output coordinate domain without invalidating the source. */
GeoCoord geo_grid_axis_pitch(const GeoGridAxisDef *axis);
GeoCoord geo_grid_axis_phase(const GeoGridAxisDef *axis);
bool geo_grid_axis_valid(const GeoGridAxisDef *axis);
/* Base definition checks preserve the existing order: index space, name,
 * axes, then nonempty. Parameter and stagger checks run in evaluate; rule
 * checks remain separate so the host can keep its intervening role check. */
bool geo_grid_system_validate(const GeoGridSystem *system, GeoGridStoreError *error);
bool geo_grid_system_evaluate(GeoGridStore *store, size_t index,
    GeoGridCoordinateResolver resolve, void *state, GeoGridStoreError *error);
const GeoGridRule *geo_grid_rule_find(const GeoGridSystem *system, uint32_t key);
bool geo_grid_rule_matches(const GeoGridRule *rule, const int64_t cell[2]);
/* Separate so the host can retain its intervening role-preference check. */
bool geo_grid_rules_validate(const GeoGridSystem *system, GeoGridStoreError *error);

/* Evaluates against the current, already-evaluated source system. Successful
 * earlier-axis writes survive a later failure, matching rejected-candidate
 * diagnostic caches. Missing source/vertex failures leave cache unchanged. */
bool geo_grid_binding_evaluate(const GeoGridStore *store, size_t index,
    GeoGridVertexResolver resolve, void *state, GeoGridBindingCache *cache, GeoGridStoreError *error);
/* Translation can be unrepresentable while the local lattice remains valid.
 * The first output may have been written when the second axis fails. */
bool geo_grid_binding_translation(const GeoGridStore *store, size_t index,
    GeoGridVertexResolver resolve, void *state, GeoCoord out[2], GeoGridStoreError *error);
#endif
