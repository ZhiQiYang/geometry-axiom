#include "internal/guides.h"
#include <stdlib.h>
#include <string.h>

GeoGuideStore *geo_guides_create(void) { return calloc(1, sizeof(GeoGuideStore)); }
GeoGuideStore *geo_guides_clone(const GeoGuideStore *store)
{
    if (!store) return NULL;
    GeoGuideStore *copy = malloc(sizeof *copy);
    if (copy) memcpy(copy, store, sizeof *copy);
    return copy;
}
void geo_guides_destroy(GeoGuideStore *store) { free(store); }
size_t geo_guides_count(const GeoGuideStore *store) { return store ? store->count : 0; }
const GeoGuide *geo_guides_at(const GeoGuideStore *store, size_t index)
{
    return store && index < store->count ? &store->values[index] : NULL;
}
const GeoGuide *geo_guides_values(const GeoGuideStore *store) { return store ? store->values : NULL; }
const GeoGuide *geo_guides_find(const GeoGuideStore *store, uint32_t id)
{
    if (!store) return NULL;
    for (size_t i = 0; i < store->count; ++i)
        if (store->values[i].id == id) return &store->values[i];
    return NULL;
}
bool geo_guides_put(GeoGuideStore *store, const GeoGuide *guide)
{
    if (!store || !guide ||
        (guide->source != GEO_GUIDE_LOCAL && guide->source != GEO_GUIDE_DATUM) ||
        (guide->direction != GEO_GUIDE_ALONG_U && guide->direction != GEO_GUIDE_ALONG_V)) return false;
    size_t at = 0;
    while (at < store->count && store->values[at].id != guide->id) ++at;
    if (at >= GEO_GUIDE_CAPACITY) return false;
    /* Snapshot active fields first: guide may point into the slot we replace.
     * Field-wise construction followed by memcpy also fixes padding bytes. */
    GeoGuide next;
    memset(&next, 0, sizeof next);
    next.id = guide->id;
    next.placement_id = guide->placement_id;
    next.direction = guide->direction;
    next.source = guide->source;
    next.resolved = guide->resolved;
    next.offset = guide->offset;
    if (guide->source == GEO_GUIDE_DATUM) {
        next.datum_id = guide->datum_id;
    } else {
        const GeoLinearExpression *expression = &guide->expression;
        if (expression->count > GEO_LINEAR_MAX_TERMS || expression->key_bytes > GEO_LINEAR_KEY_BYTES) return false;
        geo_linear_begin(&next.expression, expression->mode);
        for (size_t i = 0; i < expression->count; ++i) {
            const GeoLinearTerm *term = &expression->terms[i];
            if (term->key_offset >= expression->key_bytes ||
                !memchr(expression->keys + term->key_offset, 0, expression->key_bytes - term->key_offset)) return false;
            GeoLinearSource source = {term->provider, term->id, term->field, expression->keys + term->key_offset};
            if (!geo_linear_append(&next.expression, term->numerator, term->denominator, source)) return false;
        }
        geo_linear_finish(&next.expression, expression->complete);
    }
    memcpy(&store->values[at], &next, sizeof next);
    if (at == store->count) ++store->count;
    return true;
}
bool geo_guides_remove(GeoGuideStore *store, uint32_t id)
{
    if (!store) return false;
    size_t at = 0;
    while (at < store->count && store->values[at].id != id) ++at;
    if (at == store->count) return false;
    memmove(store->values + at, store->values + at + 1, (store->count - at - 1) * sizeof *store->values);
    memset(&store->values[--store->count], 0, sizeof *store->values);
    return true;
}
void geo_guides_reset_resolved(GeoGuideStore *store)
{
    if (!store) return;
    for (size_t i = 0; i < store->count; ++i) store->values[i].resolved = false;
}
GeoGuideResult geo_guides_evaluate(GeoGuideStore *store, size_t index,
    const GeoFrame *frame, const GeoDatum *datum, GeoLinearResolver resolve, void *state)
{return geo_guides_evaluate_definition(store,index,geo_guides_at(store,index),frame,datum,resolve,state);}
GeoGuideResult geo_guides_evaluate_definition(GeoGuideStore *store, size_t index,
    const GeoGuide *definition, const GeoFrame *frame, const GeoDatum *datum,
    GeoLinearResolver resolve, void *state)
{
    GeoGuideResult result;
    memset(&result, 0, sizeof result);
    result.status = GEO_GUIDE_INVALID;
    result.linear.status = GEO_LINEAR_INVALID;
    result.linear.exact_status = GEO_EXACT_OK;
    result.linear.value.den = 1;
    result.linear.value.unit = GEO_UNIT_LENGTH;
    result.intersection = GEO_DATUM_INTERSECTION_INVALID;
    if (!store || index >= store->count || !definition || definition->id != store->values[index].id) return result;
    if (definition->source != GEO_GUIDE_LOCAL && definition->source != GEO_GUIDE_DATUM) return result;
    if (definition->source != store->values[index].source) return result;
    if (definition->source == GEO_GUIDE_LOCAL &&
        definition->direction != GEO_GUIDE_ALONG_U && definition->direction != GEO_GUIDE_ALONG_V) return result;
    GeoGuide *guide = &store->values[index];
    if (!frame) { result.status = GEO_GUIDE_MISSING_FRAME; return result; }
    if (definition->source == GEO_GUIDE_DATUM) {
        if (!datum || datum->id != definition->datum_id) {
            result.status = GEO_GUIDE_MISSING_DATUM;
            return result;
        }
        GeoDatumIntersection intersection;
        result.intersection = geo_datum_intersection(datum, frame, &intersection);
        if (result.intersection == GEO_DATUM_INTERSECTION_OK || result.intersection == GEO_DATUM_INTERSECTION_RANGE) {
            guide->direction = intersection.coordinate_axis == 0 ? GEO_GUIDE_ALONG_V : GEO_GUIDE_ALONG_U;
            guide->offset = intersection.coordinate;
        }
        if (result.intersection != GEO_DATUM_INTERSECTION_OK) {
            result.status = GEO_GUIDE_DATUM_FAILED;
            return result;
        }
    } else {
        result.linear = geo_linear_evaluate(&definition->expression, resolve, state);
        if (result.linear.status != GEO_LINEAR_OK) {
            result.status = GEO_GUIDE_LINEAR_FAILED;
            return result;
        }
        guide->offset = result.linear.value.num;
    }
    guide->resolved = true;
    result.status = GEO_GUIDE_OK;
    return result;
}
