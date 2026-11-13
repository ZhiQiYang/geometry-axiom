#include "grid_store.h"
#include <limits.h>
#include <stdio.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr, "%s:%d\n", __func__, __LINE__); return 1; } } while (0)
static GeoGridSystem system_value(uint32_t id)
{
    GeoGridSystem s;
    memset(&s, 0, sizeof s);
    s.id = id; strcpy(s.name, "independent axes"); s.next_rule_key = 1;
    for (int a = 0; a < 2; ++a) s.axis[a].source = GEO_GRID_SOURCE_REPEAT;
    s.axis[0].start = 7; s.axis[0].step = 120;
    s.axis[1].start = -11; s.axis[1].step = 80;
    return s;
}
static GeoGridBinding binding_value(uint32_t id)
{
    GeoGridBinding b;
    memset(&b, 0, sizeof b);
    b.id = id; b.system_id = 5; b.boundary_id = 71; b.vertex_key = 902;
    b.anchor_den[0] = b.anchor_den[1] = 1;
    return b;
}
static GeoGridRule rule_value(uint32_t key)
{
    GeoGridRule r;
    memset(&r, 0, sizeof r);
    r.key = key; strcpy(r.name, "subdivision"); r.divisions[0] = 3; r.divisions[1] = 2;
    return r;
}
typedef struct { GeoPoint2 point; uint32_t boundary, key; size_t calls; bool fail; } VertexState;
static bool vertex(void *opaque, uint32_t boundary, uint32_t key, GeoPoint2 *out)
{
    VertexState *v = opaque;
    ++v->calls; v->boundary = boundary; v->key = key;
    if (v->fail || boundary != 71 || key != 902) return false;
    *out = v->point; return true;
}
typedef struct { GeoCoord value[12]; unsigned seen[16]; size_t calls; unsigned fail; } ParamState;
static bool parameter(void *opaque, GeoParameterRef ref, GeoCoord *out)
{
    ParamState *p = opaque;
    if (p->calls < 16) p->seen[p->calls] = ref.parameter_id;
    ++p->calls;
    if (ref.parameter_id >= 12 || ref.field_id != ref.parameter_id + 100 || ref.parameter_id == p->fail) return false;
    *out = p->value[ref.parameter_id]; return true;
}
static int ownership(void)
{
    GeoGridStore *store = geo_grid_store_create(); CHECK(store);
    GeoGridSystem s = system_value(5); s.axis[0].count = 2;
    s.axis[0].coords[0] = -9; s.axis[0].coords[1] = 19; s.axis[0].coords[2] = 777;
    s.axis[0].parameters[2] = (GeoParameterRef){true, 300, 400};
    s.rule_count = 1; s.rules[0] = rule_value(42); s.next_rule_key = 0;
    memset(s.rules + 1, 0x5a, sizeof s.rules - sizeof s.rules[0]);
    CHECK(geo_grid_systems_put(store, &s));
    const GeoGridSystem *owned = geo_grid_systems_find(store, 5); CHECK(owned);
    GeoGridSystem expected = *owned;
    memset(&s, 0xa5, sizeof s);
    CHECK(!memcmp(owned, &expected, sizeof expected));
    CHECK(owned->axis[0].coords[2] == 0 && owned->rules[1].key == 0);
    CHECK(owned->axis[0].parameters[2].parameter_id == 300 && owned->next_rule_key == 0);
    CHECK(geo_grid_systems_put(store, owned));
    CHECK(!memcmp(geo_grid_systems_at(store, 0), &expected, sizeof expected));
    GeoGridBinding b = binding_value(UINT32_MAX); b.cell[0] = INT64_MIN;
    CHECK(geo_grid_bindings_put(store, &b));
    CHECK(geo_grid_bindings_put(store, geo_grid_bindings_at(store, 0)));
    GeoGridStore *copy = geo_grid_store_clone(store); CHECK(copy);
    CHECK(geo_grid_systems_remove(store, 5) && geo_grid_bindings_remove(store, UINT32_MAX));
    CHECK(geo_grid_systems_count(copy) == 1 && geo_grid_bindings_count(copy) == 1);
    CHECK(!memcmp(geo_grid_systems_at(copy, 0), &expected, sizeof expected));
    CHECK(geo_grid_bindings_at(copy, 0)->cell[0] == INT64_MIN);
    geo_grid_store_destroy(copy); geo_grid_store_destroy(store);
    CHECK(!geo_grid_store_clone(NULL) && !geo_grid_systems_values(NULL) && !geo_grid_bindings_values(NULL));
    geo_grid_store_destroy(NULL); return 0;
}
static int capacity(void)
{
    GeoGridStore *store = geo_grid_store_create(); CHECK(store);
    for (uint32_t i = 0; i < 16; ++i) { GeoGridSystem s = system_value(i); CHECK(geo_grid_systems_put(store, &s)); }
    GeoGridSystem s = system_value(UINT32_MAX); CHECK(!geo_grid_systems_put(store, &s));
    s.id = 5; s.axis[0].start = 33; CHECK(geo_grid_systems_put(store, &s));
    CHECK(geo_grid_systems_at(store, 5)->axis[0].start == 33);
    CHECK(geo_grid_systems_remove(store, 5) && !geo_grid_systems_remove(store, 5));
    CHECK(geo_grid_systems_at(store, 5)->id == 6 && !geo_grid_systems_at(store, 15));
    s.id = UINT32_MAX; CHECK(geo_grid_systems_put(store, &s));
    CHECK(geo_grid_systems_at(store, 15)->id == UINT32_MAX);
    for (uint32_t i = 0; i < 32; ++i) { GeoGridBinding b = binding_value(i); CHECK(geo_grid_bindings_put(store, &b)); }
    GeoGridBinding b = binding_value(UINT32_MAX); CHECK(!geo_grid_bindings_put(store, &b));
    b.id = 3; b.vertex_key = 1234; CHECK(geo_grid_bindings_put(store, &b));
    CHECK(geo_grid_bindings_at(store, 3)->vertex_key == 1234);
    CHECK(geo_grid_bindings_remove(store, 3) && geo_grid_bindings_at(store, 3)->id == 4);
    CHECK(!geo_grid_bindings_at(store, 31) && !geo_grid_bindings_remove(store, 99));
    CHECK(geo_grid_systems_count(store) == 16 && geo_grid_bindings_count(store) == 31);
    geo_grid_store_destroy(store); return 0;
}
static int invalid_inputs(void)
{
    GeoGridStore *store = geo_grid_store_create(); CHECK(store);
    GeoGridSystem s = system_value(5); CHECK(geo_grid_systems_put(store, &s));
    GeoGridSystem original = *geo_grid_systems_at(store, 0);
    s.axis[1].count = 65; CHECK(!geo_grid_systems_put(store, &s));
    s = original; s.rule_count = 33; CHECK(!geo_grid_systems_put(store, &s));
    s = original; memset(s.name, 'a', sizeof s.name); CHECK(!geo_grid_systems_put(store, &s));
    s = original; s.rule_count = 1; s.rules[0] = rule_value(1); memset(s.rules[0].name, 'b', sizeof s.rules[0].name);
    CHECK(!geo_grid_systems_put(store, &s));
    CHECK(!memcmp(geo_grid_systems_at(store, 0), &original, sizeof original));
    CHECK(!geo_grid_systems_put(store, NULL) && !geo_grid_systems_put(NULL, &original));
    CHECK(!geo_grid_bindings_put(store, NULL) && !geo_grid_bindings_remove(NULL, 0));
    GeoGridStoreError e; CHECK(!geo_grid_system_evaluate(store, 1, NULL, NULL, &e));
    CHECK(e.status == GEO_GRID_STORE_SYSTEM_MISSING && e.axis == -1 && e.field == -1);
    CHECK(!geo_grid_system_validate(NULL, &e) && e.status == GEO_GRID_STORE_INVALID);
    geo_grid_store_destroy(store); return 0;
}
static int axes(void)
{
    CHECK(GEO_GRID_SOURCE_NONE == 0 && GEO_GRID_SOURCE_EXPLICIT == 1 && GEO_GRID_SOURCE_SERIES == 2);
    CHECK(GEO_GRID_SOURCE_REPEAT == 3 && GEO_GRID_SOURCE_REPEAT_BODY_GAP == 4 && GEO_GRID_SOURCE_BODY_GAP == 5);
    GeoGridAxisDef a; memset(&a, 0, sizeof a);
    CHECK(geo_grid_axis_valid(&a) && !geo_grid_axis_valid(NULL));
    a.source = GEO_GRID_SOURCE_EXPLICIT; CHECK(!geo_grid_axis_valid(&a));
    a.count = 64; for (int i = 0; i < 64; ++i) a.coords[i] = i - 31;
    CHECK(geo_grid_axis_valid(&a)); a.coords[32] = a.coords[31]; CHECK(!geo_grid_axis_valid(&a));
    a.coords[32] = 1; a.coords[0] = -GEO_COORD_LIMIT - 1; CHECK(!geo_grid_axis_valid(&a));
    a.source = GEO_GRID_SOURCE_SERIES; a.start = GEO_COORD_LIMIT - 63; a.step = 1; a.series_count = 64;
    CHECK(geo_grid_axis_valid(&a)); ++a.start; CHECK(!geo_grid_axis_valid(&a));
    a.start = 0; a.series_count = 65; CHECK(!geo_grid_axis_valid(&a));
    a.source = GEO_GRID_SOURCE_REPEAT; a.step = GEO_COORD_LIMIT;
    CHECK(geo_grid_axis_valid(&a) && geo_grid_axis_is_infinite(&a));
    a.step = 0; CHECK(!geo_grid_axis_valid(&a));
    a.source = GEO_GRID_SOURCE_REPEAT_BODY_GAP; a.body = 3; a.gap = 5; a.anchor = -7;
    CHECK(!geo_grid_axis_valid(&a)); a.anchor_explicit = true;
    CHECK(geo_grid_axis_valid(&a) && geo_grid_axis_pitch(&a) == 8 && geo_grid_axis_phase(&a) == -2);
    a.body = GEO_COORD_LIMIT; a.gap = GEO_COORD_LIMIT; a.anchor = GEO_COORD_LIMIT;
    CHECK(geo_grid_axis_valid(&a) && geo_grid_axis_phase(&a) == 250000000);
    a.source = GEO_GRID_SOURCE_BODY_GAP; CHECK(geo_grid_axis_valid(&a) && !geo_grid_axis_is_infinite(&a));
    a.gap = -1; CHECK(!geo_grid_axis_valid(&a)); a.source = 17; CHECK(!geo_grid_axis_valid(&a));
    return 0;
}
static int system_validation(void)
{
    GeoGridSystem s = system_value(5); GeoGridStoreError e;
    CHECK(geo_grid_system_validate(&s, &e));
    s.axis[1].source = GEO_GRID_SOURCE_SERIES; s.name[0] = 0;
    CHECK(!geo_grid_system_validate(&s, &e) && e.status == GEO_GRID_STORE_MIXED_SPACE && e.axis == 1);
    s.axis[1].source = GEO_GRID_SOURCE_NONE;
    CHECK(!geo_grid_system_validate(&s, &e) && e.status == GEO_GRID_STORE_SYSTEM_NAME);
    strcpy(s.name, "ok"); s.axis[0].step = 0;
    CHECK(!geo_grid_system_validate(&s, &e) && e.status == GEO_GRID_STORE_AXIS_INVALID && e.axis == 0);
    s.axis[0].source = GEO_GRID_SOURCE_NONE;
    CHECK(!geo_grid_system_validate(&s, &e) && e.status == GEO_GRID_STORE_SYSTEM_EMPTY);
    s = system_value(5); s.name[0] = (char)0xc0; s.name[1] = (char)0x80; s.name[2] = 0;
    CHECK(!geo_grid_system_validate(&s, &e) && e.status == GEO_GRID_STORE_SYSTEM_NAME);
    s = system_value(5); s.rule_count = 33;
    CHECK(geo_grid_system_validate(&s, &e)); /* rules are intentionally a separate stage */
    CHECK(!geo_grid_rule_find(&s, 99));
    return 0;
}
static int redeclaration(void)
{
    GeoGridStore *store = geo_grid_store_create(); CHECK(store);
    GeoGridSystem s = system_value(5); GeoGridStoreError e;
    s.rule_count = 1; s.rules[0] = rule_value(1); s.next_rule_key = 19;
    CHECK(geo_grid_systems_redeclare(store, &s, &e));
    CHECK(!geo_grid_systems_at(store, 0)->rule_count && geo_grid_systems_at(store, 0)->next_rule_key == 1);
    s.rules[0].key = UINT32_MAX; s.next_rule_key = 0; CHECK(geo_grid_systems_put(store, &s));
    GeoGridStore *snapshot = geo_grid_store_clone(store); CHECK(snapshot);
    GeoGridSystem fresh = system_value(5); fresh.axis[0].step = 999;
    CHECK(geo_grid_systems_redeclare(store, &fresh, &e));
    CHECK(geo_grid_systems_at(store, 0)->rules[0].key == UINT32_MAX && geo_grid_systems_at(store, 0)->next_rule_key == 0);
    CHECK(geo_grid_systems_at(snapshot, 0)->axis[0].step == 120);
    fresh.axis[0].source = fresh.axis[1].source = GEO_GRID_SOURCE_NONE;
    CHECK(!geo_grid_systems_redeclare(store, &fresh, &e) && e.status == GEO_GRID_STORE_SPACE_CHANGE);
    CHECK(geo_grid_systems_at(store, 0)->axis[0].step == 999);
    CHECK(geo_grid_systems_redeclare(store, geo_grid_systems_at(store, 0), &e));
    geo_grid_store_destroy(snapshot); geo_grid_store_destroy(store); return 0;
}
static int parameters(void)
{
    GeoGridStore *store = geo_grid_store_create(); CHECK(store);
    GeoGridSystem s = system_value(5); ParamState p; memset(&p, 0, sizeof p); p.fail = 8;
    const GeoCoord values[12] = {17, 126, 3, 5, -7, 13, -21, 82, 7, 9, 0, -7}; memcpy(p.value, values, sizeof values);
    for (unsigned a = 0; a < 2; ++a) for (unsigned f = 0; f < 6; ++f)
        s.axis[a].parameters[f] = (GeoParameterRef){true, a * 6 + f, a * 6 + f + 100};
    s.axis[0].stagger_set = s.axis[1].stagger_set = true;
    CHECK(geo_grid_systems_put(store, &s)); GeoGridStoreError e;
    CHECK(!geo_grid_system_evaluate(store, 0, parameter, &p, &e));
    CHECK(e.status == GEO_GRID_STORE_PARAMETER_SOURCE && e.system_id == 5 && e.axis == 1 && e.field == 2 && p.calls == 9);
    for (unsigned i = 0; i < 9; ++i) CHECK(p.seen[i] == i);
    const GeoGridSystem *after = geo_grid_systems_at(store, 0);
    CHECK(after->axis[0].start == 17 && after->axis[0].step == 126 && after->axis[0].stagger == 13 && after->axis[0].anchor == -7);
    CHECK(after->axis[1].start == -21 && after->axis[1].step == 82 && after->axis[1].body == 0);
    p.fail = UINT_MAX; p.calls = 0; CHECK(geo_grid_system_evaluate(store, 0, parameter, &p, &e)); CHECK(p.calls == 12);
    s = system_value(5); s.axis[0].parameters[0] = (GeoParameterRef){true, 0, 100}; s.axis[0].source = GEO_GRID_SOURCE_SERIES;
    CHECK(geo_grid_systems_put(store, &s)); p.calls = 0;
    CHECK(!geo_grid_system_evaluate(store, 0, parameter, &p, &e) && e.status == GEO_GRID_STORE_PARAMETER_AXIS && !p.calls);
    s = system_value(5); s.axis[0].stagger_set = true; s.axis[1].parameters[0] = (GeoParameterRef){true, 6, 106};
    CHECK(geo_grid_systems_put(store, &s));
    CHECK(!geo_grid_system_evaluate(store, 0, parameter, &p, &e) && e.status == GEO_GRID_STORE_STAGGER_ZERO && !p.calls);
    geo_grid_store_destroy(store); return 0;
}
static int stagger(void)
{
    GeoGridStore *store = geo_grid_store_create(); CHECK(store); GeoGridStoreError e;
    GeoGridSystem s = system_value(5); CHECK(geo_grid_systems_put(store, &s));
    CHECK(geo_grid_system_evaluate(store, 0, NULL, NULL, &e));
    s.axis[0].stagger_set = true; CHECK(geo_grid_systems_put(store, &s));
    CHECK(!geo_grid_system_evaluate(store, 0, NULL, NULL, &e) && e.status == GEO_GRID_STORE_STAGGER_ZERO && e.axis == 0 && e.field == 5);
    s.axis[0].stagger = -240; CHECK(geo_grid_systems_put(store, &s));
    CHECK(!geo_grid_system_evaluate(store, 0, NULL, NULL, &e) && e.status == GEO_GRID_STORE_STAGGER_MULTIPLE && e.pitch == 120 && e.value == -240);
    s.axis[0].stagger = -13; CHECK(geo_grid_systems_put(store, &s)); CHECK(geo_grid_system_evaluate(store, 0, NULL, NULL, &e));
    s.axis[0].step = 0; CHECK(geo_grid_systems_put(store, &s));
    CHECK(!geo_grid_system_evaluate(store, 0, NULL, NULL, &e) && e.status == GEO_GRID_STORE_STAGGER_PITCH);
    s.axis[1].source = GEO_GRID_SOURCE_NONE; CHECK(geo_grid_systems_put(store, &s));
    CHECK(!geo_grid_system_evaluate(store, 0, NULL, NULL, &e) && e.status == GEO_GRID_STORE_STAGGER_SOURCE);
    s = system_value(5); s.axis[0].stagger_set = true; s.axis[0].stagger = INT64_MIN;
    CHECK(geo_grid_systems_put(store, &s));
    CHECK(!geo_grid_system_evaluate(store, 0, NULL, NULL, &e) && e.status == GEO_GRID_STORE_AXIS_INVALID && e.field == 5);
    s.axis[0].source = GEO_GRID_SOURCE_REPEAT_BODY_GAP; s.axis[0].body = INT64_MAX; s.axis[0].gap = 1;
    s.axis[0].anchor_explicit = true; s.axis[0].stagger = 13; CHECK(geo_grid_systems_put(store, &s));
    CHECK(!geo_grid_system_evaluate(store, 0, NULL, NULL, &e) && e.status == GEO_GRID_STORE_AXIS_INVALID && e.field == 2);
    s.axis[0].body = s.axis[0].gap = s.axis[0].anchor = GEO_COORD_LIMIT; CHECK(geo_grid_systems_put(store, &s));
    CHECK(geo_grid_system_evaluate(store, 0, NULL, NULL, &e));
    geo_grid_store_destroy(store); return 0;
}
static int rules(void)
{
    GeoGridSystem s = system_value(5); GeoGridStoreError e;
    s.rule_count = 1; s.rules[0] = rule_value(9); s.next_rule_key = 10;
    CHECK(geo_grid_rules_validate(&s, &e)); CHECK(geo_grid_rule_find(&s, 9) == &s.rules[0] && !geo_grid_rule_find(&s, 3));
    int64_t cell[2] = {0, 0}; CHECK(geo_grid_rule_matches(&s.rules[0], cell)); cell[0] = -1; CHECK(!geo_grid_rule_matches(&s.rules[0], cell));
    s.rules[0].all_cells = true; CHECK(geo_grid_rule_matches(&s.rules[0], cell));
    s.rules[0].cell[0] = INT64_MAX; CHECK(geo_grid_rules_validate(&s, &e)); s.rules[0].all_cells = false;
    CHECK(!geo_grid_rules_validate(&s, &e) && e.status == GEO_GRID_STORE_RULE_CELL_RANGE);
    s.rules[0].cell[0] = INT64_MIN; CHECK(geo_grid_rules_validate(&s, &e));
    s.rules[0].key = 10; CHECK(!geo_grid_rules_validate(&s, &e) && e.status == GEO_GRID_STORE_RULE_KEY);
    s.next_rule_key = 0; s.rules[0].key = UINT32_MAX; CHECK(geo_grid_rules_validate(&s, &e));
    s.rules[0].name[0] = 0; CHECK(!geo_grid_rules_validate(&s, &e) && e.status == GEO_GRID_STORE_RULE_NAME);
    strcpy(s.rules[0].name, "rule"); s.rules[0].divisions[0] = 66;
    CHECK(!geo_grid_rules_validate(&s, &e) && e.status == GEO_GRID_STORE_RULE_DIVISIONS);
    s.rules[0].divisions[0] = s.rules[0].divisions[1] = 1;
    CHECK(!geo_grid_rules_validate(&s, &e) && e.status == GEO_GRID_STORE_RULE_DIVISIONS);
    s.rules[0].divisions[0] = 7;
    CHECK(!geo_grid_rules_validate(&s, &e) && e.status == GEO_GRID_STORE_RULE_NOT_DIVISIBLE && e.axis == 0 && e.pitch == 120 && e.value == 7);
    s.rules[0] = rule_value(1); s.rules[1] = rule_value(2); s.rule_count = 2;
    CHECK(!geo_grid_rules_validate(&s, &e) && e.status == GEO_GRID_STORE_RULE_OVERLAP && e.rule_key == 2 && e.other_rule_key == 1);
    s.rules[1].cell[1] = -1; CHECK(geo_grid_rules_validate(&s, &e));
    s.rules[1].key = 1; CHECK(!geo_grid_rules_validate(&s, &e) && e.status == GEO_GRID_STORE_RULE_KEY);
    s.axis[0].stagger_set = true; CHECK(!geo_grid_rules_validate(&s, &e) && e.status == GEO_GRID_STORE_RULE_SOURCE);
    s.rule_count = 33; CHECK(!geo_grid_rules_validate(&s, &e) && e.status == GEO_GRID_STORE_RULE_CAPACITY);
    s.rule_count = 0; CHECK(geo_grid_rules_validate(&s, &e)); return 0;
}
static int fractions(void)
{
    GeoGridBinding b = binding_value(1); b.anchor_num[0] = 0; b.anchor_den[0] = UINT32_MAX;
    b.anchor_num[1] = 12; b.anchor_den[1] = 16;
    CHECK(geo_grid_binding_normalize(&b) && b.anchor_den[0] == 1 && b.anchor_num[1] == 3 && b.anchor_den[1] == 4);
    b.anchor_num[0] = 2; b.anchor_den[0] = 4; b.anchor_den[1] = 0; GeoGridBinding before = b;
    CHECK(!geo_grid_binding_normalize(&b) && !memcmp(&b, &before, sizeof b));
    b.anchor_den[1] = 2; b.anchor_num[1] = 3; before = b;
    CHECK(!geo_grid_binding_normalize(&b) && !memcmp(&b, &before, sizeof b));
    CHECK(!geo_grid_binding_normalize(NULL)); return 0;
}
static int binding_geometry(void)
{
    GeoGridStore *store = geo_grid_store_create(); CHECK(store); GeoGridSystem s = system_value(5);
    s.axis[0].stagger_set = s.axis[1].stagger_set = true; s.axis[0].stagger = 13; s.axis[1].stagger = -7;
    CHECK(geo_grid_systems_put(store, &s)); GeoGridBinding b = binding_value(1);
    b.cell[0] = -2; b.cell[1] = -3; b.anchor_num[0] = b.anchor_num[1] = 1; b.anchor_den[0] = 2; b.anchor_den[1] = 4;
    CHECK(geo_grid_bindings_put(store, &b)); VertexState v = {{400, 500}, 0, 0, 0, false};
    GeoGridBindingCache cache; memset(&cache, 0, sizeof cache); GeoGridStoreError e;
    CHECK(geo_grid_binding_evaluate(store, 0, vertex, &v, &cache, &e));
    CHECK(v.calls == 1 && v.boundary == 71 && v.key == 902);
    CHECK(cache.lattice[0].base == 327 && cache.lattice[0].pitch == 120 && cache.lattice[0].index == -2);
    CHECK(cache.lattice[1].base == 480 && cache.lattice[1].pitch == 80 && cache.lattice[1].index == -3);
    GeoCoord point; CHECK(geo_lattice_coord(&cache.lattice[0], -1, &point) && point == 447);
    GeoCoord translation[2]; CHECK(geo_grid_binding_translation(store, 0, vertex, &v, translation, &e));
    CHECK(translation[0] == 560 && translation[1] == 731);
    b.cell[0] = INT64_MAX - 1; b.cell[1] = 0; CHECK(geo_grid_bindings_put(store, &b));
    CHECK(geo_grid_binding_evaluate(store, 0, vertex, &v, &cache, &e));
    CHECK(geo_lattice_coord(&cache.lattice[0], INT64_MAX - 1, &point) && point == 340);
    CHECK(!geo_grid_binding_translation(store, 0, vertex, &v, translation, &e) && e.status == GEO_GRID_STORE_BINDING_TRANSLATION_RANGE);
    geo_grid_store_destroy(store); return 0;
}
static int binding_failures(void)
{
    GeoGridStore *store = geo_grid_store_create(); CHECK(store); GeoGridSystem s = system_value(5);
    CHECK(geo_grid_systems_put(store, &s)); GeoGridBinding b = binding_value(1); CHECK(geo_grid_bindings_put(store, &b));
    VertexState v = {{400, 500}, 0, 0, 0, true}; GeoGridStoreError e;
    GeoGridBindingCache cache; memset(&cache, 0, sizeof cache);
    for (int axis = 0; axis < 2; ++axis) {
        cache.axis[axis].start = 9999;
        cache.lattice[axis] = (GeoLattice){333, 444, 555};
    }
    GeoGridBindingCache before = cache;
    CHECK(!geo_grid_binding_evaluate(store, 0, vertex, &v, &cache, &e) && e.status == GEO_GRID_STORE_BINDING_SOURCE);
    CHECK(!memcmp(&cache, &before, sizeof cache)); v.fail = false;
    b.anchor_den[1] = 3; b.anchor_num[1] = 1; CHECK(geo_grid_bindings_put(store, &b));
    CHECK(!geo_grid_binding_evaluate(store, 0, vertex, &v, &cache, &e) && e.status == GEO_GRID_STORE_BINDING_ANCHOR && e.axis == 1);
    CHECK(cache.lattice[0].base == 400 && cache.lattice[0].pitch == 120);
    CHECK(!memcmp(&cache.axis[1], &before.axis[1], sizeof cache.axis[1]) && !memcmp(&cache.lattice[1], &before.lattice[1], sizeof cache.lattice[1]));
    b.anchor_num[1] = 0; b.anchor_den[1] = 1; b.cell[1] = INT64_MAX; CHECK(geo_grid_bindings_put(store, &b));
    CHECK(!geo_grid_binding_evaluate(store, 0, vertex, &v, &cache, &e) && e.status == GEO_GRID_STORE_BINDING_CELL_RANGE && e.axis == 1);
    s.axis[1].source = GEO_GRID_SOURCE_NONE; CHECK(geo_grid_systems_put(store, &s)); v.calls = 0;
    CHECK(!geo_grid_binding_evaluate(store, 0, vertex, &v, &cache, &e) && e.status == GEO_GRID_STORE_BINDING_SOURCE && !v.calls);
    CHECK(!geo_grid_binding_evaluate(store, 1, vertex, &v, &cache, &e) && e.status == GEO_GRID_STORE_BINDING_MISSING);
    CHECK(!geo_grid_binding_evaluate(store, 0, vertex, &v, NULL, &e) && e.status == GEO_GRID_STORE_INVALID);
    geo_grid_store_destroy(store); return 0;
}
static int translation_limits(void)
{
    GeoGridStore *store = geo_grid_store_create(); CHECK(store); GeoGridSystem s = system_value(5);
    s.axis[0].start = s.axis[1].start = 0; s.axis[0].step = s.axis[1].step = 1; CHECK(geo_grid_systems_put(store, &s));
    GeoGridBinding b = binding_value(1); b.cell[0] = INT64_MIN + 1; CHECK(geo_grid_bindings_put(store, &b));
    VertexState v = {{0, 0}, 0, 0, 0, false}; GeoGridStoreError e; GeoCoord out[2] = {111, 222};
    CHECK(geo_grid_binding_translation(store, 0, vertex, &v, out, &e) && out[0] == INT64_MAX && out[1] == 0);
    b.cell[0] = INT64_MIN; CHECK(geo_grid_bindings_put(store, &b)); out[0] = 111;
    CHECK(!geo_grid_binding_translation(store, 0, vertex, &v, out, &e) && out[0] == 111 && e.axis == 0);
    v.point.u = -1; CHECK(geo_grid_binding_translation(store, 0, vertex, &v, out, &e) && out[0] == INT64_MAX);
    b.cell[0] = INT64_MAX - 1; CHECK(geo_grid_bindings_put(store, &b)); v.point.u = -2;
    CHECK(geo_grid_binding_translation(store, 0, vertex, &v, out, &e) && out[0] == INT64_MIN);
    v.point.u = -3; CHECK(!geo_grid_binding_translation(store, 0, vertex, &v, out, &e));
    b.cell[0] = 0; b.cell[1] = INT64_MIN; CHECK(geo_grid_bindings_put(store, &b)); v.point.u = 17; out[0] = 111; out[1] = 222;
    CHECK(!geo_grid_binding_translation(store, 0, vertex, &v, out, &e) && e.axis == 1 && out[0] == 17 && out[1] == 222);
    v.point.v = -1; CHECK(geo_grid_binding_translation(store, 0, vertex, &v, out, &e) && out[1] == INT64_MAX);
    CHECK(!geo_grid_binding_translation(store, 0, vertex, &v, NULL, &e) && e.status == GEO_GRID_STORE_INVALID);
    geo_grid_store_destroy(store); return 0;
}
int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    const struct { const char *name; int (*run)(void); } cases[] = {
        {"ownership", ownership}, {"capacity", capacity}, {"invalid-inputs", invalid_inputs},
        {"axes", axes}, {"system-validation", system_validation}, {"redeclaration", redeclaration},
        {"parameters", parameters}, {"stagger", stagger}, {"rules", rules}, {"fractions", fractions},
        {"binding-geometry", binding_geometry}, {"binding-failures", binding_failures}, {"translation-limits", translation_limits}
    };
    for (size_t i = 0; i < sizeof cases / sizeof cases[0]; ++i) if (!strcmp(argv[1], cases[i].name)) return cases[i].run();
    return 2;
}
