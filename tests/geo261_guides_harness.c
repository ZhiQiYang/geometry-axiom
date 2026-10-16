#include "guides.h"
#include <limits.h>
#include <stdio.h>
#include <string.h>

#define CHECK(condition) do { if (!(condition)) { fprintf(stderr, "%s:%d\n", __func__, __LINE__); return 1; } } while (0)
typedef struct {
    GeoQuantity values[3];
    uint32_t fail_id, seen[8];
    size_t calls;
} ResolverState;
static ResolverState resolver_state(void)
{
    ResolverState state;
    memset(&state, 0, sizeof state);
    state.values[0] = (GeoQuantity){5, 1, GEO_UNIT_LENGTH};
    state.values[1] = (GeoQuantity){4, 1, GEO_UNIT_LENGTH};
    state.values[2] = (GeoQuantity){0, 1, GEO_UNIT_LENGTH};
    state.fail_id = UINT32_MAX;
    return state;
}
static bool resolve(void *opaque, const GeoLinearSource *source, GeoQuantity *out)
{
    ResolverState *state = opaque;
    if (!state) return false;
    if (state->calls < 8) state->seen[state->calls] = source->id;
    ++state->calls;
    if (source->provider != 77 || source->id >= 3 || source->id == state->fail_id ||
        source->field != source->id + 100 || strcmp(source->key, "opaque source key")) return false;
    *out = state->values[source->id];
    return true;
}
static bool term(GeoLinearExpression *expression, int64_t numerator, int64_t denominator, uint32_t id)
{
    return geo_linear_append(expression, numerator, denominator,
        (GeoLinearSource){77, id, id + 100, "opaque source key"});
}
static GeoGuide local(uint32_t id, GeoLinearMode mode)
{
    GeoGuide guide;
    memset(&guide, 0, sizeof guide);
    guide.id = id;
    guide.placement_id = 91;
    guide.direction = GEO_GUIDE_ALONG_V;
    geo_linear_begin(&guide.expression, mode);
    term(&guide.expression, 1, 1, 0);
    geo_linear_finish(&guide.expression, true);
    return guide;
}
static GeoGuide datum_guide(uint32_t id)
{
    GeoGuide guide;
    memset(&guide, 0, sizeof guide);
    guide.id = id;
    guide.placement_id = 91;
    guide.source = GEO_GUIDE_DATUM;
    guide.datum_id = 83;
    return guide;
}
static GeoFrame frame(void)
{
    return (GeoFrame){{101, -211, 307}, {1, 0, 0}, {0, 1, 0}, {0, 0, 1}};
}
static int ownership(void)
{
    GeoGuideStore *a = geo_guides_create();
    if (!a) return 2;
    GeoGuide input = local(0, GEO_LINEAR_FLOOR_FINAL);
    input.offset = 17; input.resolved = true; input.datum_id = 99;
    memset(input.expression.keys + input.expression.key_bytes, 0xa5,
        sizeof input.expression.keys - input.expression.key_bytes);
    memset(input.expression.terms + input.expression.count, 0xa5,
        sizeof input.expression.terms - input.expression.count * sizeof input.expression.terms[0]);
    CHECK(geo_guides_put(a, &input));
    GeoGuide expected = local(0, GEO_LINEAR_FLOOR_FINAL);
    expected.offset = 17; expected.resolved = true;
    CHECK(!memcmp(&expected, geo_guides_find(a, 0), sizeof expected));
    memset(&input, 0, sizeof input);
    CHECK(!strcmp(geo_guides_at(a, 0)->expression.keys, "opaque source key"));
    GeoGuideStore *b = geo_guides_clone(a);
    if (!b) return 2;
    ResolverState state = resolver_state(); GeoFrame current = frame();
    CHECK(geo_guides_evaluate(b, 0, &current, NULL, resolve, &state).status == GEO_GUIDE_OK);
    CHECK(geo_guides_find(b, 0)->offset == 5 && geo_guides_find(a, 0)->offset == 17);
    const GeoGuide *borrowed = geo_guides_find(b, 0);
    CHECK(geo_guides_put(b, borrowed));
    CHECK(geo_guides_find(b, 0)->offset == 5 && geo_guides_find(b, 0)->resolved);
    input = datum_guide(UINT32_MAX); input.offset = -200; input.resolved = true;
    memset(&input.expression, 0xa5, sizeof input.expression);
    CHECK(geo_guides_put(b, &input));
    expected = datum_guide(UINT32_MAX); expected.offset = -200; expected.resolved = true;
    CHECK(!memcmp(&expected, geo_guides_find(b, UINT32_MAX), sizeof expected));
    CHECK(geo_guides_remove(b, 0) && geo_guides_count(b) == 1 && geo_guides_count(a) == 1);
    CHECK(geo_guides_values(b) == geo_guides_at(b, 0));
    geo_guides_destroy(a); geo_guides_destroy(b); return 0;
}
static int capacity(void)
{
    GeoGuideStore *store = geo_guides_create();
    if (!store) return 2;
    for (uint32_t i = 0; i < 16; ++i) { GeoGuide input = local(i, GEO_LINEAR_FLOOR_FINAL); CHECK(geo_guides_put(store, &input)); }
    GeoGuide input = local(16, GEO_LINEAR_FLOOR_FINAL);
    CHECK(!geo_guides_put(store, &input) && geo_guides_count(store) == 16);
    input.id = 7; input.offset = 999;
    CHECK(geo_guides_put(store, &input) && geo_guides_at(store, 7)->offset == 999);
    for (size_t i = 0; i < 16; ++i) CHECK(geo_guides_at(store, i)->id == i);
    CHECK(geo_guides_remove(store, 6) && !geo_guides_remove(store, 6));
    CHECK(geo_guides_at(store, 5)->id == 5 && geo_guides_at(store, 6)->id == 7);
    input.id = UINT32_MAX;
    CHECK(geo_guides_put(store, &input) && geo_guides_at(store, 15)->id == UINT32_MAX);
    CHECK(!geo_guides_at(store, 16) && !geo_guides_find(store, 16));
    CHECK(!geo_guides_clone(NULL) && !geo_guides_count(NULL) && !geo_guides_values(NULL));
    CHECK(!geo_guides_at(NULL, 0) && !geo_guides_find(NULL, 0));
    CHECK(!geo_guides_put(NULL, &input) && !geo_guides_put(store, NULL) && !geo_guides_remove(NULL, 0));
    geo_guides_reset_resolved(NULL); geo_guides_destroy(NULL);
    geo_guides_destroy(store); return 0;
}
static int invalid_inputs(void)
{
    GeoGuideStore *store = geo_guides_create();
    if (!store) return 2;
    GeoGuide input = local(1, GEO_LINEAR_FLOOR_FINAL), original;
    CHECK(geo_guides_put(store, &input)); memcpy(&original, geo_guides_at(store, 0), sizeof original);
    for (int error = 0; error < 9; ++error) {
        input = original;
        if (error == 0) input.source = (GeoGuideSource)9;
        if (error == 1) input.direction = (GeoGuideDirection)9;
        if (error == 2) input.expression.count = GEO_LINEAR_MAX_TERMS + 1;
        if (error == 3) input.expression.key_bytes = GEO_LINEAR_KEY_BYTES + 1;
        if (error == 4) input.expression.terms[0].key_offset = input.expression.key_bytes;
        if (error == 5) memset(input.expression.keys, 'x', input.expression.key_bytes);
        if (error == 6) input.expression.terms[0].denominator = 0;
        if (error == 7) input.expression.terms[0].numerator = INT64_MIN;
        if (error == 8) input.expression.terms[0].provider = 0;
        CHECK(!geo_guides_put(store, &input));
        CHECK(geo_guides_count(store) == 1 && !memcmp(&original, geo_guides_at(store, 0), sizeof original));
    }
    GeoFrame current = frame(); ResolverState state = resolver_state();
    CHECK(geo_guides_evaluate(NULL, 0, &current, NULL, resolve, &state).status == GEO_GUIDE_INVALID);
    CHECK(geo_guides_evaluate(store, 1, &current, NULL, resolve, &state).status == GEO_GUIDE_INVALID);
    CHECK(state.calls == 0);
    geo_guides_destroy(store); return 0;
}
static int local_values(void)
{
    GeoGuideStore *store = geo_guides_create();
    if (!store) return 2;
    GeoGuide input = local(1, GEO_LINEAR_FLOOR_FINAL);
    geo_linear_begin(&input.expression, GEO_LINEAR_FLOOR_FINAL);
    CHECK(term(&input.expression, 1, 2, 0) && term(&input.expression, -1, 1, 1));
    geo_linear_finish(&input.expression, true);
    CHECK(geo_guides_put(store, &input));
    ResolverState state = resolver_state(); GeoFrame invalid_frame;
    memset(&invalid_frame, 0, sizeof invalid_frame);
    GeoGuideResult result = geo_guides_evaluate(store, 0, &invalid_frame, NULL, resolve, &state);
    CHECK(result.status == GEO_GUIDE_OK && result.linear.status == GEO_LINEAR_OK);
    CHECK(geo_guides_at(store, 0)->offset == -2 && geo_guides_at(store, 0)->resolved);
    CHECK(state.calls == 2 && state.seen[0] == 0 && state.seen[1] == 1);
    input = local(1, GEO_LINEAR_EXACT_INTEGER_FINAL);
    geo_linear_begin(&input.expression, GEO_LINEAR_EXACT_INTEGER_FINAL);
    CHECK(term(&input.expression, 1, 2, 0) && term(&input.expression, 1, 2, 1));
    geo_linear_finish(&input.expression, true);
    CHECK(geo_guides_put(store, &input)); state = resolver_state(); state.values[0].num = state.values[1].num = 1;
    result = geo_guides_evaluate(store, 0, &invalid_frame, NULL, resolve, &state);
    CHECK(result.status == GEO_GUIDE_OK && geo_guides_at(store, 0)->offset == 1);
    input = local(1, GEO_LINEAR_FLOOR_FINAL); CHECK(geo_guides_put(store, &input));
    state.values[0].num = -GEO_COORD_LIMIT;
    CHECK(geo_guides_evaluate(store, 0, &invalid_frame, NULL, resolve, &state).status == GEO_GUIDE_OK);
    CHECK(geo_guides_at(store, 0)->offset == -GEO_COORD_LIMIT);
    state.values[0].num = GEO_COORD_LIMIT;
    CHECK(geo_guides_evaluate(store, 0, &invalid_frame, NULL, resolve, &state).status == GEO_GUIDE_OK);
    CHECK(geo_guides_at(store, 0)->offset == GEO_COORD_LIMIT);
    geo_guides_destroy(store); return 0;
}
static int local_failures(void)
{
    GeoGuideStore *store = geo_guides_create();
    if (!store) return 2;
    GeoGuide input = local(1, GEO_LINEAR_EXACT_INTEGER_FINAL);
    input.offset = 17; input.resolved = true; CHECK(geo_guides_put(store, &input));
    ResolverState state = resolver_state(); GeoFrame current = frame();
    GeoGuideResult result = geo_guides_evaluate(store, 0, NULL, NULL, resolve, &state);
    CHECK(result.status == GEO_GUIDE_MISSING_FRAME && state.calls == 0);
    for (int error = 0; error < 5; ++error) {
        state = resolver_state();
        if (error == 0) state.values[0].den = 2;
        if (error == 1) state.values[0].num = GEO_COORD_LIMIT + 1;
        if (error == 2) state.fail_id = 0;
        if (error == 3) state.values[0].unit = GEO_UNIT_SCALAR;
        result = geo_guides_evaluate(store, 0, &current, NULL, error == 4 ? NULL : resolve, &state);
        CHECK(result.status == GEO_GUIDE_LINEAR_FAILED);
        const GeoLinearStatus expected[] = {GEO_LINEAR_NOT_INTEGER, GEO_LINEAR_RANGE,
            GEO_LINEAR_SOURCE_FAILED, GEO_LINEAR_ARITHMETIC, GEO_LINEAR_INVALID};
        CHECK(result.linear.status == expected[error]);
        CHECK(geo_guides_at(store, 0)->offset == 17 && geo_guides_at(store, 0)->resolved);
        if (error == 1) CHECK(result.linear.value.num == GEO_COORD_LIMIT + 1);
    }
    geo_linear_begin(&input.expression, GEO_LINEAR_EXACT_INTEGER_FINAL);
    CHECK(term(&input.expression, INT64_MAX, 1, 0)); geo_linear_finish(&input.expression, true);
    CHECK(geo_guides_put(store, &input)); state = resolver_state(); state.values[0].num = 2;
    result = geo_guides_evaluate(store, 0, &current, NULL, resolve, &state);
    CHECK(result.status == GEO_GUIDE_LINEAR_FAILED && result.linear.status == GEO_LINEAR_ARITHMETIC);
    CHECK(geo_guides_at(store, 0)->offset == 17 && geo_guides_at(store, 0)->resolved);
    geo_guides_destroy(store); return 0;
}
static int incomplete_prefix(void)
{
    GeoGuideStore *store = geo_guides_create();
    if (!store) return 2;
    GeoGuide input = local(1, GEO_LINEAR_EXACT_INTEGER_FINAL); input.offset = 17;
    CHECK(term(&input.expression, 1, 1, 1)); geo_linear_finish(&input.expression, false);
    CHECK(geo_guides_put(store, &input) && !geo_guides_at(store, 0)->expression.complete);
    ResolverState state = resolver_state(); GeoFrame current = frame(); state.fail_id = 0;
    GeoGuideResult result = geo_guides_evaluate(store, 0, &current, NULL, resolve, &state);
    CHECK(result.status == GEO_GUIDE_LINEAR_FAILED && result.linear.status == GEO_LINEAR_SOURCE_FAILED);
    CHECK(state.calls == 1 && result.linear.term == 0);
    state = resolver_state(); state.fail_id = 1;
    result = geo_guides_evaluate(store, 0, &current, NULL, resolve, &state);
    CHECK(result.linear.status == GEO_LINEAR_SOURCE_FAILED && state.calls == 2 && result.linear.term == 1);
    state = resolver_state();
    result = geo_guides_evaluate(store, 0, &current, NULL, resolve, &state);
    CHECK(result.status == GEO_GUIDE_LINEAR_FAILED && result.linear.status == GEO_LINEAR_INVALID);
    CHECK(state.calls == 2 && state.seen[0] == 0 && state.seen[1] == 1 && result.linear.term == 2);
    CHECK(geo_guides_at(store, 0)->offset == 17 && !geo_guides_at(store, 0)->resolved);
    geo_guides_destroy(store); return 0;
}
static int datum_frames(void)
{
    GeoGuideStore *store = geo_guides_create();
    if (!store) return 2;
    const GeoVector3 directions[] = {{1,0,0},{-1,0,0},{0,1,0},{0,-1,0},{0,0,1},{0,0,-1}};
    GeoDatum datum; memset(&datum, 0, sizeof datum); datum.id = 83; datum.position = 37;
    size_t count = 0;
    for (size_t u = 0; u < 6; ++u) for (size_t v = 0; v < 6; ++v) {
        GeoCoord dot = directions[u].x * directions[v].x + directions[u].y * directions[v].y + directions[u].z * directions[v].z;
        if (dot) continue;
        GeoFrame current = {{101,-211,307},directions[u],directions[v],geo_vector_cross(directions[u],directions[v])};
        for (int axis = 0; axis < 3; ++axis) {
            GeoGuide input = datum_guide(1); input.offset = 71;
            CHECK(geo_guides_put(store, &input)); datum.axis = axis;
            GeoCoord cu = axis == 0 ? current.axis_u.x : axis == 1 ? current.axis_u.y : current.axis_u.z;
            GeoCoord cv = axis == 0 ? current.axis_v.x : axis == 1 ? current.axis_v.y : current.axis_v.z;
            GeoCoord origin = axis == 0 ? 101 : axis == 1 ? -211 : 307;
            GeoGuideResult result = geo_guides_evaluate(store, 0, &current, &datum, NULL, NULL);
            const GeoGuide *actual = geo_guides_at(store, 0);
            if (!cu && !cv) {
                CHECK(result.status == GEO_GUIDE_DATUM_FAILED && result.intersection == GEO_DATUM_INTERSECTION_PARALLEL);
                CHECK(actual->offset == 71 && actual->direction == GEO_GUIDE_ALONG_U && !actual->resolved);
            } else {
                CHECK(result.status == GEO_GUIDE_OK && result.intersection == GEO_DATUM_INTERSECTION_OK);
                CHECK(actual->direction == (cu ? GEO_GUIDE_ALONG_V : GEO_GUIDE_ALONG_U));
                CHECK(actual->offset == (cu ? cu : cv) * (37 - origin) && actual->resolved);
            }
            ++count;
        }
    }
    CHECK(count == 72); geo_guides_destroy(store); return 0;
}
static int datum_failures(void)
{
    GeoGuideStore *store = geo_guides_create();
    if (!store) return 2;
    GeoGuide input = datum_guide(1); input.offset = 71; input.resolved = true;
    CHECK(geo_guides_put(store, &input));
    GeoFrame current = frame(); GeoDatum datum; memset(&datum, 0, sizeof datum);
    datum.id = 83; datum.axis = 2; datum.position = 307;
    ResolverState state = resolver_state();
    GeoGuideResult result = geo_guides_evaluate(store, 0, NULL, NULL, resolve, &state);
    CHECK(result.status == GEO_GUIDE_MISSING_FRAME);
    result = geo_guides_evaluate(store, 0, &current, NULL, resolve, &state);
    CHECK(result.status == GEO_GUIDE_MISSING_DATUM);
    datum.id = 84; result = geo_guides_evaluate(store, 0, &current, &datum, resolve, &state);
    CHECK(result.status == GEO_GUIDE_MISSING_DATUM); datum.id = 83;
    for (int error = 0; error < 4; ++error) {
        current = frame(); datum.position = 307; datum.axis = 2;
        if (error == 1) datum.position = 308;
        if (error == 2) current.normal.z = -1;
        if (error == 3) datum.position = GEO_COORD_LIMIT + 1;
        result = geo_guides_evaluate(store, 0, &current, &datum, resolve, &state);
        const GeoDatumIntersectionStatus expected[] = {GEO_DATUM_INTERSECTION_COINCIDENT,
            GEO_DATUM_INTERSECTION_PARALLEL, GEO_DATUM_INTERSECTION_INVALID, GEO_DATUM_INTERSECTION_INVALID};
        CHECK(result.status == GEO_GUIDE_DATUM_FAILED && result.intersection == expected[error]);
        CHECK(geo_guides_at(store, 0)->offset == 71 && geo_guides_at(store, 0)->direction == GEO_GUIDE_ALONG_U);
        CHECK(geo_guides_at(store, 0)->resolved);
    }
    CHECK(state.calls == 0); geo_guides_destroy(store); return 0;
}
static int datum_range(void)
{
    GeoGuideStore *store = geo_guides_create();
    if (!store) return 2;
    GeoDatum datum; memset(&datum, 0, sizeof datum); datum.id = 83; datum.position = GEO_COORD_LIMIT;
    for (int axis = 0; axis < 2; ++axis) for (int sign = -1; sign <= 1; sign += 2) {
        GeoGuide input = datum_guide(1); input.offset = 71;
        input.direction = axis ? GEO_GUIDE_ALONG_V : GEO_GUIDE_ALONG_U;
        input.resolved = sign > 0;
        CHECK(geo_guides_put(store, &input));
        GeoFrame current = {{-GEO_COORD_LIMIT,-GEO_COORD_LIMIT,0},{sign,0,0},{0,sign,0},{0,0,1}};
        datum.axis = axis;
        GeoGuideResult result = geo_guides_evaluate(store, 0, &current, &datum, NULL, NULL);
        CHECK(result.status == GEO_GUIDE_DATUM_FAILED && result.intersection == GEO_DATUM_INTERSECTION_RANGE);
        CHECK(geo_guides_at(store, 0)->offset == sign * 2 * GEO_COORD_LIMIT);
        CHECK(geo_guides_at(store, 0)->direction == (axis ? GEO_GUIDE_ALONG_U : GEO_GUIDE_ALONG_V));
        CHECK(geo_guides_at(store, 0)->resolved == (sign > 0));
    }
    geo_guides_destroy(store); return 0;
}
static int reset_and_move(void)
{
    GeoGuideStore *store = geo_guides_create();
    if (!store) return 2;
    GeoGuide a = local(1, GEO_LINEAR_FLOOR_FINAL), b = datum_guide(2);
    a.offset = 17; a.resolved = true; b.offset = -300; b.resolved = true;
    CHECK(geo_guides_put(store, &a) && geo_guides_put(store, &b));
    geo_guides_reset_resolved(store); a.resolved = b.resolved = false;
    CHECK(!memcmp(&a, geo_guides_at(store, 0), sizeof a) && !memcmp(&b, geo_guides_at(store, 1), sizeof b));
    a = *geo_guides_at(store, 0); a.expression.terms[0].id = 1; a.expression.terms[0].field = 101;
    CHECK(geo_guides_put(store, &a) && geo_guides_at(store, 0)->offset == 17 && !geo_guides_at(store, 0)->resolved);
    ResolverState state = resolver_state(); GeoFrame current = frame(); state.fail_id = 1;
    CHECK(geo_guides_evaluate(store, 0, &current, NULL, resolve, &state).status == GEO_GUIDE_LINEAR_FAILED);
    CHECK(geo_guides_at(store, 0)->offset == 17 && !geo_guides_at(store, 0)->resolved);
    state.fail_id = UINT32_MAX;
    CHECK(geo_guides_evaluate(store, 0, &current, NULL, resolve, &state).status == GEO_GUIDE_OK);
    CHECK(geo_guides_at(store, 0)->offset == 4 && geo_guides_at(store, 0)->resolved);
    CHECK(geo_guides_at(store, 1)->offset == -300 && !geo_guides_at(store, 1)->resolved);
    geo_guides_destroy(store); return 0;
}
int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    if (!strcmp(argv[1], "ownership")) return ownership();
    if (!strcmp(argv[1], "capacity")) return capacity();
    if (!strcmp(argv[1], "invalid-inputs")) return invalid_inputs();
    if (!strcmp(argv[1], "local-values")) return local_values();
    if (!strcmp(argv[1], "local-failures")) return local_failures();
    if (!strcmp(argv[1], "incomplete-prefix")) return incomplete_prefix();
    if (!strcmp(argv[1], "datum-frames")) return datum_frames();
    if (!strcmp(argv[1], "datum-failures")) return datum_failures();
    if (!strcmp(argv[1], "datum-range")) return datum_range();
    if (!strcmp(argv[1], "reset-move")) return reset_and_move();
    return 2;
}
