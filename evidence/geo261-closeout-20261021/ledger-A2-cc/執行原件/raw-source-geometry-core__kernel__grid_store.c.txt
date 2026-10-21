#include "internal/grid_store.h"
#include "codec.h"
#include <stdlib.h>
#include <string.h>
#include <limits.h>

static void geo_grid_error_begin(GeoGridStoreError *error)
{
    if (!error) return;
    memset(error, 0, sizeof *error);
    error->axis = error->field = -1;
}
static bool geo_grid_error(GeoGridStoreError *error, GeoGridStoreStatus status)
{
    if (error) error->status = status;
    return false;
}
static bool geo_grid_copy_name(char out[GEO_GRID_NAME_CAPACITY], const char in[GEO_GRID_NAME_CAPACITY])
{
    const char *end = memchr(in, 0, GEO_GRID_NAME_CAPACITY);
    if (!end) return false;
    memcpy(out, in, (size_t)(end - in));
    return true;
}
static bool geo_grid_name_valid(const char name[GEO_GRID_NAME_CAPACITY])
{
    size_t n = 0;
    while (n < GEO_GRID_NAME_CAPACITY && name[n]) ++n;
    return geo_utf8_name_valid((const unsigned char *)name, n, GEO_GRID_NAME_CAPACITY - 1);
}
static bool geo_grid_copy_axis(GeoGridAxisDef *out, const GeoGridAxisDef *in)
{
    if (in->count > GEO_GRID_COORDINATE_CAPACITY) return false;
    out->source = in->source;
    out->count = in->count;
    memcpy(out->coords, in->coords, in->count * sizeof in->coords[0]);
    out->start = in->start; out->step = in->step; out->series_count = in->series_count;
    out->body = in->body; out->gap = in->gap; out->anchor = in->anchor;
    out->anchor_explicit = in->anchor_explicit;
    for (size_t i = 0; i < 6; ++i) {
        out->parameters[i].set = in->parameters[i].set;
        out->parameters[i].parameter_id = in->parameters[i].parameter_id;
        out->parameters[i].field_id = in->parameters[i].field_id;
    }
    out->stagger = in->stagger; out->stagger_set = in->stagger_set;
    out->card_length = in->card_length;
    return true;
}
/* Field copies keep store bytes (and their padding) deterministic. */
static void geo_grid_copy_card(GeoGridCardReference *out, const GeoGridCardReference *in)
{
    out->set = in->set; out->parameter_id = in->parameter_id;
    out->fields[0] = in->fields[0]; out->fields[1] = in->fields[1];
}
static bool geo_grid_copy_system(GeoGridSystem *out, const GeoGridSystem *in)
{
    memset(out, 0, sizeof *out);
    if (in->rule_count > GEO_GRID_RULE_CAPACITY || !geo_grid_copy_name(out->name, in->name)) return false;
    out->id = in->id;
    for (int axis = 0; axis < 2; ++axis)
        if (!geo_grid_copy_axis(&out->axis[axis], &in->axis[axis])) return false;
    geo_grid_copy_card(&out->card_reference, &in->card_reference);
    out->rule_count = in->rule_count; out->next_rule_key = in->next_rule_key;
    for (size_t i = 0; i < in->rule_count; ++i) {
        GeoGridRule *next = &out->rules[i]; const GeoGridRule *rule = &in->rules[i];
        if (!geo_grid_copy_name(next->name, rule->name)) return false;
        next->key = rule->key; next->all_cells = rule->all_cells;
        for (int axis = 0; axis < 2; ++axis) {
            next->cell[axis] = rule->cell[axis]; next->divisions[axis] = rule->divisions[axis];
        }
    }
    return true;
}
GeoGridStore *geo_grid_store_create(void) { return calloc(1, sizeof(GeoGridStore)); }
GeoGridStore *geo_grid_store_clone(const GeoGridStore *store)
{
    if (!store) return NULL;
    GeoGridStore *copy = malloc(sizeof *copy);
    if (copy) memcpy(copy, store, sizeof *copy);
    return copy;
}
void geo_grid_store_destroy(GeoGridStore *store) { free(store); }
size_t geo_grid_systems_count(const GeoGridStore *store) { return store ? store->system_count : 0; }
const GeoGridSystem *geo_grid_systems_at(const GeoGridStore *store, size_t index)
{ return store && index < store->system_count ? &store->systems[index] : NULL; }
const GeoGridSystem *geo_grid_systems_values(const GeoGridStore *store) { return store ? store->systems : NULL; }
const GeoGridSystem *geo_grid_systems_find(const GeoGridStore *store, uint32_t id)
{
    if (!store) return NULL;
    for (size_t i = 0; i < store->system_count; ++i) if (store->systems[i].id == id) return &store->systems[i];
    return NULL;
}
bool geo_grid_systems_put(GeoGridStore *store, const GeoGridSystem *system)
{
    if (!store || !system) return false;
    size_t at = 0;
    while (at < store->system_count && store->systems[at].id != system->id) ++at;
    if (at >= GEO_GRID_SYSTEM_CAPACITY) return false;
    GeoGridSystem next;
    if (!geo_grid_copy_system(&next, system)) return false;
    memcpy(&store->systems[at], &next, sizeof next);
    if (at == store->system_count) ++store->system_count;
    return true;
}
bool geo_grid_systems_remove(GeoGridStore *store, uint32_t id)
{
    if (!store) return false;
    size_t at = 0;
    while (at < store->system_count && store->systems[at].id != id) ++at;
    if (at == store->system_count) return false;
    memmove(store->systems + at, store->systems + at + 1, (store->system_count - at - 1) * sizeof *store->systems);
    memset(&store->systems[--store->system_count], 0, sizeof *store->systems);
    return true;
}
bool geo_grid_systems_redeclare(GeoGridStore *store, const GeoGridSystem *definition, GeoGridStoreError *error)
{
    geo_grid_error_begin(error);
    if (!store || !definition) return geo_grid_error(error, GEO_GRID_STORE_INVALID);
    if (error) error->system_id = definition->id;
    const GeoGridSystem *old = geo_grid_systems_find(store, definition->id);
    if (old && geo_grid_system_is_infinite(old) != geo_grid_system_is_infinite(definition))
        return geo_grid_error(error, GEO_GRID_STORE_SPACE_CHANGE);
    GeoGridSystem next;
    memset(&next, 0, sizeof next);
    next.id = definition->id;
    if (!geo_grid_copy_name(next.name, definition->name) ||
        !geo_grid_copy_axis(&next.axis[0], &definition->axis[0]) ||
        !geo_grid_copy_axis(&next.axis[1], &definition->axis[1])) return geo_grid_error(error, GEO_GRID_STORE_INVALID);
    geo_grid_copy_card(&next.card_reference, &definition->card_reference); /* authored definition */
    next.next_rule_key = 1;
    if (old) {
        next.rule_count = old->rule_count; next.next_rule_key = old->next_rule_key;
        memcpy(next.rules, old->rules, sizeof next.rules);
    }
    if (!geo_grid_systems_put(store, &next))
        return geo_grid_error(error, old || store->system_count < GEO_GRID_SYSTEM_CAPACITY ? GEO_GRID_STORE_INVALID : GEO_GRID_STORE_CAPACITY);
    return true;
}
size_t geo_grid_bindings_count(const GeoGridStore *store) { return store ? store->binding_count : 0; }
const GeoGridBinding *geo_grid_bindings_at(const GeoGridStore *store, size_t index)
{ return store && index < store->binding_count ? &store->bindings[index] : NULL; }
const GeoGridBinding *geo_grid_bindings_values(const GeoGridStore *store) { return store ? store->bindings : NULL; }
const GeoGridBinding *geo_grid_bindings_find(const GeoGridStore *store, uint32_t id)
{
    if (!store) return NULL;
    for (size_t i = 0; i < store->binding_count; ++i) if (store->bindings[i].id == id) return &store->bindings[i];
    return NULL;
}
bool geo_grid_bindings_put(GeoGridStore *store, const GeoGridBinding *binding)
{
    if (!store || !binding) return false;
    size_t at = 0;
    while (at < store->binding_count && store->bindings[at].id != binding->id) ++at;
    if (at >= GEO_GRID_BINDING_CAPACITY) return false;
    GeoGridBinding next;
    memset(&next, 0, sizeof next);
    next.id = binding->id; next.boundary_id = binding->boundary_id;
    next.system_id = binding->system_id; next.vertex_key = binding->vertex_key;
    for (int axis = 0; axis < 2; ++axis) {
        next.cell[axis] = binding->cell[axis];
        next.anchor_num[axis] = binding->anchor_num[axis]; next.anchor_den[axis] = binding->anchor_den[axis];
    }
    memcpy(&store->bindings[at], &next, sizeof next);
    if (at == store->binding_count) ++store->binding_count;
    return true;
}
bool geo_grid_bindings_remove(GeoGridStore *store, uint32_t id)
{
    if (!store) return false;
    size_t at = 0;
    while (at < store->binding_count && store->bindings[at].id != id) ++at;
    if (at == store->binding_count) return false;
    memmove(store->bindings + at, store->bindings + at + 1, (store->binding_count - at - 1) * sizeof *store->bindings);
    memset(&store->bindings[--store->binding_count], 0, sizeof *store->bindings);
    return true;
}
bool geo_grid_binding_normalize(GeoGridBinding *binding)
{
    if (!binding) return false;
    uint32_t numerator[2], denominator[2];
    for (int axis = 0; axis < 2; ++axis) {
        uint32_t n = binding->anchor_num[axis], d = binding->anchor_den[axis], a = n, b = d;
        if (!d || n > d) return false;
        while (b) { uint32_t remainder = a % b; a = b; b = remainder; }
        numerator[axis] = n / a; denominator[axis] = d / a;
    }
    memcpy(binding->anchor_num, numerator, sizeof numerator);
    memcpy(binding->anchor_den, denominator, sizeof denominator);
    return true;
}
bool geo_grid_axis_is_infinite(const GeoGridAxisDef *axis)
{ return axis && (axis->source == GEO_GRID_SOURCE_REPEAT || axis->source == GEO_GRID_SOURCE_REPEAT_BODY_GAP); }
bool geo_grid_system_is_infinite(const GeoGridSystem *system)
{ return system && (geo_grid_axis_is_infinite(&system->axis[0]) || geo_grid_axis_is_infinite(&system->axis[1])); }
GeoCoord geo_grid_axis_pitch(const GeoGridAxisDef *axis)
{ return axis->source == GEO_GRID_SOURCE_REPEAT ? axis->step : geo_period_pitch(axis->body, axis->gap); }
GeoCoord geo_grid_axis_phase(const GeoGridAxisDef *axis)
{ return axis->source == GEO_GRID_SOURCE_REPEAT ? axis->start : geo_period_center(axis->anchor, axis->body, axis->gap, 0); }
bool geo_grid_axis_valid(const GeoGridAxisDef *a)
{
    if (!a) return false;
    if (a->source == GEO_GRID_SOURCE_NONE) return true;
    if (a->source == GEO_GRID_SOURCE_REPEAT) return geo_coord_in_range(a->start) && a->step > 0 && geo_coord_in_range(a->step);
    if (a->source == GEO_GRID_SOURCE_REPEAT_BODY_GAP) return a->body > 0 && geo_coord_in_range(a->body) &&
        a->gap >= 0 && geo_coord_in_range(a->gap) && geo_coord_in_range(a->anchor) && a->anchor_explicit;
    if (a->source == GEO_GRID_SOURCE_EXPLICIT) {
        if (!a->count || a->count > GEO_GRID_COORDINATE_CAPACITY || !geo_coordinates_increasing(a->coords, a->count)) return false;
        for (size_t k = 0; k < a->count; ++k) if (!geo_coord_in_range(a->coords[k])) return false;
        return true;
    }
    if (a->source == GEO_GRID_SOURCE_SERIES) {
        if (!geo_coord_in_range(a->start) || a->step <= 0 || !geo_coord_in_range(a->step) ||
            !a->series_count || a->series_count > GEO_GRID_COORDINATE_CAPACITY) return false;
        return geo_coord_in_range(a->start + (GeoCoord)(a->series_count - 1) * a->step);
    }
    return a->source == GEO_GRID_SOURCE_BODY_GAP && a->body > 0 && geo_coord_in_range(a->body) &&
        a->gap >= 0 && geo_coord_in_range(a->gap) && geo_coord_in_range(a->anchor) && a->anchor_explicit;
}
bool geo_grid_system_validate(const GeoGridSystem *system, GeoGridStoreError *error)
{
    geo_grid_error_begin(error);
    if (!system) return geo_grid_error(error, GEO_GRID_STORE_INVALID);
    if (error) error->system_id = system->id;
    if (geo_grid_system_is_infinite(system)) for (int axis = 0; axis < 2; ++axis)
        if (system->axis[axis].source && !geo_grid_axis_is_infinite(&system->axis[axis])) {
            if (error) error->axis = axis;
            return geo_grid_error(error, GEO_GRID_STORE_MIXED_SPACE);
        }
    if (!geo_grid_name_valid(system->name)) return geo_grid_error(error, GEO_GRID_STORE_SYSTEM_NAME);
    for (int axis = 0; axis < 2; ++axis) if (!geo_grid_axis_valid(&system->axis[axis])) {
        if (error) error->axis = axis;
        return geo_grid_error(error, GEO_GRID_STORE_AXIS_INVALID);
    }
    if (!system->axis[0].source && !system->axis[1].source) return geo_grid_error(error, GEO_GRID_STORE_SYSTEM_EMPTY);
    return true;
}
static bool geo_grid_axis_stagger_valid(const GeoGridSystem *system, int axis, GeoGridStoreError *error)
{
    const GeoGridAxisDef *a = &system->axis[axis], *other = &system->axis[1 - axis];
    GeoCoord pitch; int64_t sum;
    if (!a->stagger_set) return true;
    if (error) { error->axis = axis; error->field = 5; error->value = a->stagger; }
    if (!geo_grid_axis_is_infinite(a) || !geo_grid_axis_is_infinite(other))
        return geo_grid_error(error, GEO_GRID_STORE_STAGGER_SOURCE);
    /* The former command parser bounded these operands before they reached
     * this algorithm. A public staging API must enforce that precondition
     * before pitch/phase arithmetic, without rejecting a derived wide phase. */
    const GeoCoord values[] = {a->start, a->step, a->body, a->gap, a->anchor, a->stagger};
    for (int field = 0; field < 6; ++field) {
        bool used = field == 5 || (a->source == GEO_GRID_SOURCE_REPEAT ? field < 2 : field >= 2 && field < 5);
        if (used && !geo_coord_in_range(values[field])) {
            if (error) { error->field = field; error->value = values[field]; }
            return geo_grid_error(error, GEO_GRID_STORE_AXIS_INVALID);
        }
    }
    pitch = geo_grid_axis_pitch(a);
    if (error) error->pitch = pitch;
    if (pitch <= 0) return geo_grid_error(error, GEO_GRID_STORE_STAGGER_PITCH);
    if (a->stagger == 0) return geo_grid_error(error, GEO_GRID_STORE_STAGGER_ZERO);
    if (a->stagger % pitch == 0) return geo_grid_error(error, GEO_GRID_STORE_STAGGER_MULTIPLE);
    if (!geo_i64_add(geo_grid_axis_phase(a), a->stagger, &sum))
        return geo_grid_error(error, GEO_GRID_STORE_STAGGER_OVERFLOW);
    return true;
}
/* D64/I74: the card reference is one source for both controlled lengths.
 * Same order as the per-system rebuild: mapping, fields, then each axis. */
static bool geo_grid_card_resolve(GeoGridSystem *system,
    GeoGridCoordinateResolver resolve, void *state, GeoGridStoreError *error)
{
    const GeoGridCardReference *r = &system->card_reference;
    if (!r->set) {
        for (int axis = 0; axis < 2; ++axis) if (system->axis[axis].card_length) {
            if (error) error->axis = axis;
            return geo_grid_error(error, GEO_GRID_STORE_CARD_MAPPING);
        }
        return true;
    }
    if (r->fields[0] == r->fields[1]) return geo_grid_error(error, GEO_GRID_STORE_CARD_FIELDS);
    for (int axis = 0; axis < 2; ++axis) {
        GeoGridAxisDef *a = &system->axis[axis];
        int slot = a->source == GEO_GRID_SOURCE_REPEAT ? 1 : 2;
        if (error) { error->axis = axis; error->field = slot; }
        if (!geo_grid_axis_is_infinite(a)) return geo_grid_error(error, GEO_GRID_STORE_CARD_MODE);
        if (!a->card_length || a->parameters[slot].set) return geo_grid_error(error, GEO_GRID_STORE_CARD_EXCLUSIVE);
        GeoParameterRef ref = {true, r->parameter_id, r->fields[axis]};
        GeoCoord value = 0;
        if (!resolve || !resolve(state, ref, &value)) return geo_grid_error(error, GEO_GRID_STORE_CARD_SOURCE);
        if (value <= 0) {
            if (error) error->value = value;
            return geo_grid_error(error, GEO_GRID_STORE_CARD_POSITIVE);
        }
        if (slot == 1) a->step = value; else a->body = value;
    }
    return true;
}
bool geo_grid_system_resolve_card(GeoGridSystem *system,
    GeoGridCoordinateResolver resolve, void *state, GeoGridStoreError *error)
{
    geo_grid_error_begin(error);
    if (!system) return geo_grid_error(error, GEO_GRID_STORE_SYSTEM_MISSING);
    if (error) error->system_id = system->id;
    return geo_grid_card_resolve(system, resolve, state, error);
}
bool geo_grid_system_evaluate(GeoGridStore *store, size_t index,
    GeoGridCoordinateResolver resolve, void *state, GeoGridStoreError *error)
{
    geo_grid_error_begin(error);
    if (!store || index >= store->system_count) return geo_grid_error(error, GEO_GRID_STORE_SYSTEM_MISSING);
    GeoGridSystem *system = &store->systems[index];
    if (error) error->system_id = system->id;
    if (!geo_grid_card_resolve(system, resolve, state, error)) return false;
    if (error) { error->axis = error->field = -1; }
    for (int axis = 0; axis < 2; ++axis) {
        GeoGridAxisDef *a = &system->axis[axis];
        GeoCoord *values[] = {&a->start, &a->step, &a->body, &a->gap, &a->anchor, &a->stagger};
        for (int field = 0; field < 6; ++field) if (a->parameters[field].set) {
            if (error) { error->axis = axis; error->field = field; }
            if (!geo_grid_axis_is_infinite(a)) return geo_grid_error(error, GEO_GRID_STORE_PARAMETER_AXIS);
            if (!resolve || !resolve(state, a->parameters[field], values[field]))
                return geo_grid_error(error, GEO_GRID_STORE_PARAMETER_SOURCE);
        }
        if (!geo_grid_axis_stagger_valid(system, axis, error)) return false;
    }
    return geo_grid_system_validate(system, error);
}
const GeoGridRule *geo_grid_rule_find(const GeoGridSystem *system, uint32_t key)
{
    if (system && system->rule_count <= GEO_GRID_RULE_CAPACITY)
        for (size_t i = 0; i < system->rule_count; ++i) if (system->rules[i].key == key) return &system->rules[i];
    return NULL;
}
bool geo_grid_rule_matches(const GeoGridRule *rule, const int64_t cell[2])
{ return rule && cell && (rule->all_cells || (rule->cell[0] == cell[0] && rule->cell[1] == cell[1])); }
bool geo_grid_rules_validate(const GeoGridSystem *system, GeoGridStoreError *error)
{
    geo_grid_error_begin(error);
    if (!system) return geo_grid_error(error, GEO_GRID_STORE_INVALID);
    if (error) error->system_id = system->id;
    if (system->rule_count > GEO_GRID_RULE_CAPACITY) return geo_grid_error(error, GEO_GRID_STORE_RULE_CAPACITY);
    if (!system->rule_count) return true;
    for (int axis = 0; axis < 2; ++axis)
        if (system->axis[axis].source != GEO_GRID_SOURCE_REPEAT || system->axis[axis].stagger_set) {
            if (error) error->axis = axis;
            return geo_grid_error(error, GEO_GRID_STORE_RULE_SOURCE);
        }
    for (size_t i = 0; i < system->rule_count; ++i) {
        const GeoGridRule *rule = &system->rules[i];
        if (error) error->rule_key = rule->key;
        if (!rule->key || (system->next_rule_key && rule->key >= system->next_rule_key))
            return geo_grid_error(error, GEO_GRID_STORE_RULE_KEY);
        if (!geo_grid_name_valid(rule->name)) return geo_grid_error(error, GEO_GRID_STORE_RULE_NAME);
        if (rule->divisions[0] < 1 || rule->divisions[1] < 1 || rule->divisions[0] > 65 || rule->divisions[1] > 65 ||
            (rule->divisions[0] == 1 && rule->divisions[1] == 1)) return geo_grid_error(error, GEO_GRID_STORE_RULE_DIVISIONS);
        for (int axis = 0; axis < 2; ++axis) if (geo_grid_axis_pitch(&system->axis[axis]) % rule->divisions[axis]) {
            if (error) { error->axis = axis; error->pitch = geo_grid_axis_pitch(&system->axis[axis]); error->value = rule->divisions[axis]; }
            return geo_grid_error(error, GEO_GRID_STORE_RULE_NOT_DIVISIBLE);
        }
        if (!rule->all_cells && (rule->cell[0] == INT64_MAX || rule->cell[1] == INT64_MAX))
            return geo_grid_error(error, GEO_GRID_STORE_RULE_CELL_RANGE);
        for (size_t j = 0; j < i; ++j) {
            const GeoGridRule *other = &system->rules[j];
            if (other->key == rule->key) return geo_grid_error(error, GEO_GRID_STORE_RULE_KEY);
            if (other->all_cells || rule->all_cells || (other->cell[0] == rule->cell[0] && other->cell[1] == rule->cell[1])) {
                if (error) error->other_rule_key = other->key;
                return geo_grid_error(error, GEO_GRID_STORE_RULE_OVERLAP);
            }
        }
    }
    if (error) error->rule_key = 0;
    return true;
}
bool geo_grid_binding_evaluate(const GeoGridStore *store, size_t index,
    GeoGridVertexResolver resolve, void *state, GeoGridBindingCache *cache, GeoGridStoreError *error)
{
    geo_grid_error_begin(error);
    if (!cache) return geo_grid_error(error, GEO_GRID_STORE_INVALID);
    const GeoGridBinding *binding = geo_grid_bindings_at(store, index);
    if (!binding) return geo_grid_error(error, GEO_GRID_STORE_BINDING_MISSING);
    if (error) { error->binding_id = binding->id; error->system_id = binding->system_id; }
    const GeoGridSystem *system = geo_grid_systems_find(store, binding->system_id); GeoPoint2 vertex;
    if (!system || !geo_grid_axis_is_infinite(&system->axis[0]) || !geo_grid_axis_is_infinite(&system->axis[1]) ||
        !resolve || !resolve(state, binding->boundary_id, binding->vertex_key, &vertex))
        return geo_grid_error(error, GEO_GRID_STORE_BINDING_SOURCE);
    for (int a = 0; a < 2; ++a) {
        if (error) error->axis = a;
        if (binding->cell[a] == INT64_MAX) return geo_grid_error(error, GEO_GRID_STORE_BINDING_CELL_RANGE);
        uint32_t n = binding->anchor_num[a], d = binding->anchor_den[a];
        GeoCoord pitch = geo_grid_axis_pitch(&system->axis[a]);
        if (error) error->pitch = pitch;
        if (!d || n > d || pitch <= 0 || ((uint64_t)pitch * n) % d)
            return geo_grid_error(error, GEO_GRID_STORE_BINDING_ANCHOR);
        memcpy(&cache->axis[a], &system->axis[a], sizeof cache->axis[a]);
        cache->lattice[a].pitch = pitch; cache->lattice[a].index = binding->cell[a];
        GeoCoord base = (a ? vertex.v : vertex.u) - (GeoCoord)(((uint64_t)pitch * n) / d);
        if (system->axis[a].stagger_set && (binding->cell[1 - a] & 1)) {
            int64_t shifted;
            if (!geo_i64_add(base, -(int64_t)system->axis[a].stagger, &shifted))
                return geo_grid_error(error, GEO_GRID_STORE_BINDING_SHIFT_RANGE);
            base = (GeoCoord)shifted;
        }
        cache->lattice[a].base = base;
    }
    if (error) error->axis = -1;
    return true;
}
bool geo_grid_binding_translation(const GeoGridStore *store, size_t index,
    GeoGridVertexResolver resolve, void *state, GeoCoord out[2], GeoGridStoreError *error)
{
    geo_grid_error_begin(error);
    if (!out) return geo_grid_error(error, GEO_GRID_STORE_INVALID);
    GeoGridBindingCache cache;
    memset(&cache, 0, sizeof cache);
    if (!geo_grid_binding_evaluate(store, index, resolve, state, &cache, error)) return false;
    const GeoGridBinding *binding = geo_grid_bindings_at(store, index);
    const GeoGridSystem *system = geo_grid_systems_find(store, binding->system_id);
    for (int a = 0; a < 2; ++a) {
        if (error) error->axis = a;
        int64_t cell = binding->cell[a], relative = cache.lattice[a].base - geo_grid_axis_phase(&system->axis[a]);
        uint64_t magnitude = cell < 0 ? UINT64_C(0) - (uint64_t)cell : (uint64_t)cell;
        uint64_t pitch = (uint64_t)cache.lattice[a].pitch, product;
        if (magnitude > UINT64_MAX / pitch) return geo_grid_error(error, GEO_GRID_STORE_BINDING_TRANSLATION_RANGE);
        product = magnitude * pitch;
        bool negative = cell >= 0;
        if (negative) {
            if (relative >= 0) {
                if (product < (uint64_t)relative) { product = (uint64_t)relative - product; negative = false; }
                else product -= (uint64_t)relative;
            } else {
                uint64_t extra = UINT64_C(0) - (uint64_t)relative;
                if (product > UINT64_MAX - extra) return geo_grid_error(error, GEO_GRID_STORE_BINDING_TRANSLATION_RANGE);
                product += extra;
            }
        } else {
            if (relative < 0) {
                uint64_t extra = UINT64_C(0) - (uint64_t)relative;
                if (product < extra) { product = extra - product; negative = true; } else product -= extra;
            } else {
                if (product > UINT64_MAX - (uint64_t)relative) return geo_grid_error(error, GEO_GRID_STORE_BINDING_TRANSLATION_RANGE);
                product += (uint64_t)relative;
            }
        }
        uint64_t negative_limit = (uint64_t)INT64_MAX + 1;
        if (product > (negative ? negative_limit : (uint64_t)INT64_MAX))
            return geo_grid_error(error, GEO_GRID_STORE_BINDING_TRANSLATION_RANGE);
        out[a] = negative ? (product == negative_limit ? INT64_MIN : -(int64_t)product) : (int64_t)product;
    }
    if (error) error->axis = -1;
    return true;
}
