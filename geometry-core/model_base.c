/* GEO-129: read-only, authoritative legacy-scene snapshot.
 * Build: cc -std=c11 -O2 geometry-core/model_base.c -lm -o model-base
 * The existing parser and World remain the only legacy geometry evaluator.
 * No successful JSON is emitted until the entire source has passed I9.
 */
#define main geometry_legacy_main
#include "../current_geometry.c"
#undef main

static void model_string(FILE *out, const char *text)
{
    fputc('"', out);
    for (const unsigned char *p = (const unsigned char *)text; *p; ++p) {
        switch (*p) {
        case '"': fputs("\\\"", out); break;
        case '\\': fputs("\\\\", out); break;
        case '\b': fputs("\\b", out); break;
        case '\f': fputs("\\f", out); break;
        case '\n': fputs("\\n", out); break;
        case '\r': fputs("\\r", out); break;
        case '\t': fputs("\\t", out); break;
        default:
            if (*p < 32) fprintf(out, "\\u%04x", (unsigned)*p);
            else fputc(*p, out);
        }
    }
    fputc('"', out);
}

static int model_error(const char *status, const char *code,
                       const char *clause, const char *message)
{
    fputs("{\"ok\":false,\"status\":", stdout); model_string(stdout, status);
    fputs(",\"code\":", stdout); model_string(stdout, code);
    fputs(",\"clause\":", stdout); model_string(stdout, clause);
    fputs(",\"message\":", stdout); model_string(stdout, message);
    fputs("}\n", stdout);
    return 1;
}

/* Reject binary/control input and commands that are not source declarations.
 * This also guards the legacy fgets/strlen reader against embedded NULs.
 * The core still validates every allowed command and every dependency.
 */
static bool model_source_check(const char *path, bool *capacity, char *error, size_t cap)
{
    static const char *allowed[] = {
        "spec", "boundary", "placement", "surface", "space", "datum", "guide",
        "grid", "grid-system", "grid-binding", "boundary-keyed", "boundary-vertex-keys", "subgrid", "timber", "place", "column", "beam", "canvas-pos", "requires", "engineering", NULL
    };
    FILE *in = fopen(path, "rb");
    if (!in) { snprintf(error, cap, "Cannot read source scene."); return false; }
    size_t bytes = 0, length = 0;
    char spec_names[WORLD_MAX_SPECS][SPEC_NAME_MAX];
    uint32_t guide_ids[WORLD_MAX_GUIDES];
    size_t spec_count = 0, guide_count = 0;
    int ch, line_no = 1;
    char line[SCENE_MAX_LINE];
    bool ok = true;
    do {
        ch = fgetc(in);
        if (ch != EOF) ++bytes;
        if (bytes > 1024 * 1024) {
            *capacity = true; snprintf(error, cap, "Scene exceeds adapter 1 MiB capacity."); ok = false; break;
        }
        if (ch != EOF && ch != '\n') {
            if ((ch < 32 && ch != '\t' && ch != '\r') || ch == 127) {
                snprintf(error, cap, "Line %d contains an unsupported control character.", line_no); ok = false; break;
            }
            if (length >= SCENE_MAX_LINE - 2) {
                *capacity = true; snprintf(error, cap, "Line %d exceeds legacy line capacity.", line_no); ok = false; break;
            }
            line[length++] = (char)ch;
            continue;
        }
        line[length] = '\0';
        char *text = line;
        if (line_no == 1 && length >= 3 &&
            (unsigned char)text[0] == 0xef && (unsigned char)text[1] == 0xbb &&
            (unsigned char)text[2] == 0xbf) text += 3;
        char *hash = strchr(text, '#');
        if (hash) *hash = '\0';
        char *tokens[SCENE_MAX_TOKENS];
        int count = split_tokens(text, tokens, SCENE_MAX_TOKENS);
        if (count < 0) {
            *capacity = true; snprintf(error, cap, "Line %d exceeds legacy token capacity.", line_no); ok = false; break;
        }
        if (count) {
            bool found = false;
            for (size_t i = 0; allowed[i]; ++i) if (!strcmp(tokens[0], allowed[i])) found = true;
            if (!found) {
                snprintf(error, cap, "Line %d: only scene definitions and canvas-pos are accepted.", line_no); ok = false; break;
            }
            /* Two older constructors fail silently at these array limits.
             * Classify the adapter's known storage bound explicitly (I33).
             */
            if (!strcmp(tokens[0], "spec") && count == 3 && reference_name(tokens[1])) {
                size_t i = 0; while (i < spec_count && strcmp(spec_names[i], tokens[1])) ++i;
                if (i == WORLD_MAX_SPECS) {
                    *capacity = true; snprintf(error, cap, "Named specs exceed legacy capacity."); ok = false; break;
                }
                if (i == spec_count) { snprintf(spec_names[i], SPEC_NAME_MAX, "%s", tokens[1]); ++spec_count; }
            }
            if (!strcmp(tokens[0], "guide") && count >= 5) {
                uint32_t id;
                if (parse_u32(tokens[1], &id)) {
                    size_t i = 0; while (i < guide_count && guide_ids[i] != id) ++i;
                    if (i == WORLD_MAX_GUIDES) {
                        *capacity = true; snprintf(error, cap, "Guides exceed legacy capacity."); ok = false; break;
                    }
                    if (i == guide_count) guide_ids[guide_count++] = id;
                }
            }
            if (!strcmp(tokens[0], "boundary") || !strcmp(tokens[0], "surface")) {
                for (int i = 2; i < count; ++i) if (!strcmp(tokens[i], "outline") || !strcmp(tokens[i], "hole")) {
                    int vertices = 0; SurfacePoint2 uv;
                    for (int j = i + 1; j < count && parse_uv(tokens[j], &uv); ++j) ++vertices;
                    if (vertices > POLY_MAX_VERTICES) {
                        *capacity = true; snprintf(error, cap, "Polygon loop exceeds legacy vertex capacity."); ok = false; break;
                    }
                }
                if (!ok) break;
            }
        }
        length = 0; ++line_no;
    } while (ch != EOF);
    if (ferror(in)) { snprintf(error, cap, "Could not read complete scene."); ok = false; }
    fclose(in);
    return ok;
}

static void model_point(Point3 p)
{
    printf("[%" PRId64 ",%" PRId64 ",%" PRId64 "]", p.x, p.y, p.z);
}

static void model_vector(Vector3 p)
{
    model_point((Point3){p.x, p.y, p.z});
}

static void model_loop(const PolygonLoop2 *loop)
{
    putchar('[');
    for (size_t i = 0; i < loop->count; ++i) {
        if (i) putchar(',');
        printf("[%" PRId64 ",%" PRId64 "]", loop->v[i].u, loop->v[i].v);
    }
    putchar(']');
}

static void model_face(const char *feature, const Quad3 *quad)
{
    fputs("{\"feature\":", stdout); model_string(stdout, feature);
    fputs(",\"vertices\":[", stdout);
    for (size_t j = 0; j < 4; ++j) {
        if (j) putchar(',');
        model_point(quad->vertices[j]);
    }
    fputs("]}", stdout);
}

/* D13/D14 are exact world-axis boxes, not fitted approximations. */
static void model_box(const char *kind, uint32_t id, Coord xl, Coord xh,
                      Coord yl, Coord yh, Coord zl, Coord zh)
{
    static const char *names[6] = {"-X", "+X", "-Y", "+Y", "-Z", "+Z"};
    Coord lo[3] = {xl, yl, zl}, hi[3] = {xh, yh, zh};
    fputs("{\"kind\":", stdout); model_string(stdout, kind);
    printf(",\"id\":%" PRIu32 ",\"placement_id\":null,\"boundary_id\":null,\"faces\":[", id);
    for (int k = 0; k < 3; ++k) for (int side = 0; side < 2; ++side) {
        Quad3 face;
        for (int j = 0; j < 4; ++j) {
            Coord p[3]; int u = (k + 1) % 3, v = (k + 2) % 3;
            p[k] = side ? hi[k] : lo[k];
            p[u] = TIMBER_FACE_WALK[side][j][0] ? hi[u] : lo[u];
            p[v] = TIMBER_FACE_WALK[side][j][1] ? hi[v] : lo[v];
            face.vertices[j] = (Point3){p[0], p[1], p[2]};
        }
        if (k || side) putchar(',');
        model_face(names[k * 2 + side], &face);
    }
    fputs("]}", stdout);
}

/* R29 dependency geometry, collapsed through non-geometric guide/grid nodes.
 * This is the actual legacy dependency graph, not a spatial-nearness search.
 * reference_eval_timber replays ALL earlier same-carrier timbers as candidate
 * stop faces (I9), even when only some become the final end supports.
 */
typedef struct {
    bool placements[WORLD_MAX_PLACEMENTS];
    bool timbers[WORLD_MAX_TIMBERS];
    bool guides[WORLD_MAX_GUIDES];
} ModelDependencies;

static void model_dep_placement(const World *world, ModelDependencies *deps, uint32_t id)
{
    for (size_t i = 0; i < world->placement_count; ++i)
        if (world->placements[i].id == id) deps->placements[i] = true;
}

static void model_dep_timber(const World *world, ModelDependencies *deps, uint32_t id)
{
    for (size_t i = 0; i < world->timber_count; ++i)
        if (world->timbers[i].id == id) deps->timbers[i] = true;
}

static void model_dep_guide(const World *world, ModelDependencies *deps, uint32_t id)
{
    for (size_t i = 0; i < world->guide_count; ++i) {
        const GuideLine *g = &world->guides[i];
        if (g->id != id || deps->guides[i]) continue;
        deps->guides[i] = true;
        model_dep_placement(world, deps, g->placement_id);
        if (g->source == GUIDE_DATUM) continue; /* Datum expressions contain specs only. */
        const char *p = g->expression;
        while (*p) {
            if (*p == '+' || *p == '-') ++p;
            const char *end = p; while (*end && *end != '+' && *end != '-') ++end;
            char term[REF_EXPR_MAX]; size_t size = (size_t)(end - p);
            if (!size || size >= sizeof term) break; /* Already validated by the core. */
            memcpy(term, p, size); term[size] = '\0';
            char *quantity = strchr(term, '*'); quantity = quantity ? quantity + 1 : term;
            bool timber = !strncmp(quantity, "timber:", 7);
            bool guide = !strncmp(quantity, "guide:", 6);
            if (timber || guide) {
                char *number = quantity + (timber ? 7 : 6);
                char *colon = strchr(number, ':'); if (colon) *colon = '\0';
                uint32_t ref;
                if (parse_u32(number, &ref)) {
                    if (timber) model_dep_timber(world, deps, ref);
                    else model_dep_guide(world, deps, ref);
                }
            }
            /* edge/vertex/grid/panel/gap reference the same carrier already
             * recorded; specs are scalar definitions and contribute no face. */
            p = end;
        }
    }
}

static void model_dep_space(const World *world, ModelDependencies *deps, uint32_t id)
{
    if (!id) return;
    const Space *space = world_find_space(world, id);
    if (!space) return; /* Successful I9 validation guarantees existence. */
    for (size_t b = 0; b < space->boundary_count; ++b)
        for (size_t p = 0; p < world->placement_count; ++p)
            if (world->placements[p].boundary_id == space->boundaries[b]) deps->placements[p] = true;
}

static void model_dependency_record(const World *world, const char *kind,
                                    uint32_t id, const ModelDependencies *deps)
{
    fputs("{\"kind\":", stdout); model_string(stdout, kind);
    printf(",\"id\":%" PRIu32 ",\"refs\":[", id);
    size_t count = 0;
    for (size_t i = 0; i < world->placement_count; ++i) if (deps->placements[i]) {
        if (count++) putchar(',');
        printf("{\"kind\":\"placement\",\"id\":%" PRIu32 "}", world->placements[i].id);
    }
    for (size_t i = 0; i < world->timber_count; ++i) if (deps->timbers[i]) {
        if (count++) putchar(',');
        printf("{\"kind\":\"timber\",\"id\":%" PRIu32 "}", world->timbers[i].id);
    }
    fputs("]}", stdout);
}

static void model_dependencies(const World *world)
{
    size_t count = 0;
    for (size_t i = 0; i < world->placement_count; ++i) {
        ModelDependencies deps = {0}; if (count++) putchar(',');
        model_dependency_record(world, "placement", world->placements[i].id, &deps);
    }
    for (size_t i = 0; i < world->column_count; ++i) {
        ModelDependencies deps = {0}; if (count++) putchar(',');
        /* D13/I15 membership validation depends on the actual Space members.
         * Frozen z values (R8) are never re-inferred from those members. */
        model_dep_space(world, &deps, world->columns[i].space_id);
        model_dependency_record(world, "column", world->columns[i].id, &deps);
    }
    for (size_t i = 0; i < world->beam_count; ++i) {
        ModelDependencies deps = {0}; if (count++) putchar(',');
        model_dep_space(world, &deps, world->beams[i].space_id);
        model_dependency_record(world, "beam", world->beams[i].id, &deps);
    }
    for (size_t i = 0; i < world->timber_count; ++i) {
        const TimberAnchor *anchor = &world->anchors[i]; ModelDependencies deps = {0};
        model_dep_placement(world, &deps, anchor->placement_id);
        for (size_t j = 0; j < world->timber_count; ++j)
            if (world->timbers[j].placed && world->anchors[j].order < anchor->order &&
                world->anchors[j].placement_id == anchor->placement_id) deps.timbers[j] = true;
        if (anchor->anchor_kind == ANCHOR_AT_LINE) model_dep_guide(world, &deps, anchor->ref_guide);
        if (anchor->ref_is_timber) model_dep_timber(world, &deps, anchor->ref_timber);
        if (anchor->has_between) for (int j = 0; j < 2; ++j)
            if (anchor->between[j].kind) model_dep_timber(world, &deps, anchor->between[j].timber);
        if (count++) putchar(',');
        model_dependency_record(world, "timber", world->timbers[i].id, &deps);
    }
}

int main(int argc, char **argv)
{
    if (argc != 2) return model_error("INVALID", "BASE_ARGUMENT", "D25", "Expected one scene file path.");
    char error[512] = ""; bool capacity = false;
    if (!model_source_check(argv[1], &capacity, error, sizeof error))
        return model_error(capacity ? "UNSUPPORTED" : "INVALID", capacity ? "BASE_CAPACITY" : "BASE_SOURCE", capacity ? "I33" : "I9", error);
    World world = {0};
    if (!parse_scene_file(argv[1], &world)) {
        const char *why = scene_last_error();
        capacity = strstr(why, "超過上限") || strstr(why, "capacity exceeded");
        if (!why[0]) why = "Scene failed legacy validation, including required placement of every timber.";
        return model_error(capacity ? "UNSUPPORTED" : "INVALID", capacity ? "BASE_CAPACITY" : "BASE_INVALID", capacity ? "I33" : "I9", why);
    }
    FILE *dump = tmpfile();
    if (!dump) return model_error("UNSUPPORTED", "BASE_IO", "I32", "Cannot allocate canonical dump stream.");
    world.canvas_pos_count = 0;  /* D12: presentation never enters source identity. */
    world_dump_dsl(&world, dump);
    if (ferror(dump) || fflush(dump) || fseek(dump, 0, SEEK_END)) {
        fclose(dump); return model_error("UNSUPPORTED", "BASE_IO", "I32", "Could not write canonical scene.");
    }
    long size = ftell(dump);
    if (size < 0 || size > 1024 * 1024 || fseek(dump, 0, SEEK_SET)) {
        fclose(dump); return model_error("UNSUPPORTED", "BASE_CAPACITY", "I33", "Canonical scene exceeds capacity.");
    }
    char *canonical = malloc((size_t)size + 2);
    if (!canonical) { fclose(dump); return model_error("UNSUPPORTED", "BASE_MEMORY", "I33", "Cannot allocate scene snapshot."); }
    size_t used = 0;
    char line[SCENE_MAX_LINE];
    while (fgets(line, sizeof line, dump)) {
        if (line[0] == '#') continue; /* reference_dump includes derived R18 comments. */
        size_t n = strlen(line); memcpy(canonical + used, line, n); used += n;
    }
    if (ferror(dump)) { free(canonical); fclose(dump); return model_error("UNSUPPORTED", "BASE_IO", "I32", "Could not read canonical scene."); }
    fclose(dump);
    while (used && (canonical[used - 1] == '\n' || canonical[used - 1] == '\r')) --used;
    canonical[used++] = '\n'; canonical[used] = '\0';
    fputs("{\"ok\":true,\"schema\":\"geometry-base-snapshot/1\",\"base_scene\":", stdout);
    model_string(stdout, canonical); free(canonical);
    fputs(",\"required_capabilities\":[",stdout);
    if(engineering_used(&world))model_string(stdout,"engineering-spec/1");
    fputs("],\"specs\":[", stdout);
    for (size_t i = 0; i < world.spec_count; ++i) {
        if (i) putchar(',');
        fputs("{\"name\":", stdout); model_string(stdout, world.specs[i].name);
        printf(",\"value\":%" PRId64 "}", world.specs[i].value);
    }
    fputs("],\"placements\":[", stdout);
    for (size_t i = 0; i < world.placement_count; ++i) {
        const PlacementSurface *p = &world.placements[i];
        const SpaceBoundarySurface *b = world_find_boundary(&world, p->boundary_id);
        PolygonLoop2 outline; placement_outline(p, b, &outline);
        if (i) putchar(',');
        printf("{\"id\":%" PRIu32 ",\"boundary_id\":", p->id);
        if (p->boundary_id) printf("%" PRIu32, p->boundary_id); else fputs("null", stdout);
        fputs(",\"origin\":", stdout); model_point(p->frame.origin);
        fputs(",\"u\":", stdout); model_vector(p->frame.axis_u);
        fputs(",\"v\":", stdout); model_vector(p->frame.axis_v);
        fputs(",\"n\":", stdout); model_vector(p->frame.normal);
        fputs(",\"outline\":", stdout); model_loop(&outline);
        fputs(",\"holes\":[", stdout);
        if (b) for (size_t h = 0; h < b->hole_count; ++h) { if (h) putchar(','); model_loop(&b->holes[h]); }
        fputs("]}", stdout);
    }
    fputs("],\"solids\":[", stdout);
    size_t emitted = 0;
    for (size_t i = 0; i < world.column_count; ++i) {
        const RcColumn *c = &world.columns[i]; if (emitted++) putchar(',');
        model_box("column", c->id, c->x_lo, c->x_hi, c->y_lo, c->y_hi, c->z_lo, c->z_hi);
    }
    for (size_t i = 0; i < world.beam_count; ++i) {
        const RcBeam *b = &world.beams[i]; if (emitted++) putchar(',');
        model_box("beam", b->id, b->x_lo, b->x_hi, b->y_lo, b->y_hi, b->z_lo, b->z_hi);
    }
    for (size_t i = 0; i < world.timber_count; ++i) {
        const Timber *t = &world.timbers[i]; const TimberAnchor *a = &world.anchors[i];
        const PlacementSurface *p = world_find_placement(&world, a->placement_id);
        if (emitted++) putchar(',');
        printf("{\"kind\":\"timber\",\"id\":%" PRIu32 ",\"placement_id\":%" PRIu32 ",\"boundary_id\":", t->id, a->placement_id);
        if (p && p->boundary_id) printf("%" PRIu32, p->boundary_id); else fputs("null", stdout);
        fputs(",\"faces\":[", stdout);
        for (int f = 0; f < TIMBER_FACE_COUNT; ++f) {
            Quad3 quad; timber_get_face_room(t, (TimberFaceId)f, &quad);
            if (f) putchar(','); model_face(timber_face_short_name((TimberFaceId)f), &quad);
        }
        fputs("]}", stdout);
    }
    fputs("],\"unplaced_timbers\":[],\"dependencies\":[", stdout);
    model_dependencies(&world);
    fputs("]}\n", stdout);
    return ferror(stdout) ? 1 : 0;
}
