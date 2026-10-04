/* Build: gcc -std=c11 -O2 tests/test_core_integrity.c -lm -o test_core_integrity */
#include <string.h>
#define main geometry_program_main
#include "../current_geometry.c"
#undef main

static World test_world, saved_world;
static int checks, failures;
#define CHECK(expr) do { ++checks; if (!(expr)) { \
    ++failures; fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #expr); \
} } while (0)

static bool command(const char *text)
{
    char line[SCENE_MAX_LINE], *tokens[SCENE_MAX_TOKENS];
    snprintf(line, sizeof line, "%s", text);
    int count = split_tokens(line, tokens, SCENE_MAX_TOKENS);
    return apply_interactive_tokens("integrity", 1, tokens, count, &test_world);
}

static void room(void)
{
    test_world = (World){0};
    history_clear();
    CHECK(command("surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000"));
}

static void test_frame_updates(void)
{
    CHECK(reference_default_world(&test_world)); history_clear();
    CHECK(!command("move 1 1/2*edge:e1:u"));
    CHECK(g_preview.ready && g_preview.valid);
    CHECK(test_world.guides[0].offset == 500);
    char text[64]; snprintf(text,sizeof text,"confirm %u",g_preview.token);
    CHECK(command(text));
    CHECK(test_world.guides[0].offset == 2000);
    CHECK(!command("placement 1 on boundary 1 origin 0 0 3000 u +x v +y"));
    CHECK(g_preview.valid); snprintf(text,sizeof text,"confirm %u",g_preview.token);
    CHECK(command(text)); CHECK(test_world.timbers[2].origin.z == 3000);
    CHECK(command("undo")); CHECK(test_world.timbers[2].origin.z == 2500);
    CHECK(command("redo")); CHECK(test_world.timbers[2].origin.z == 3000);
    saved_world=test_world;
    CHECK(!command("boundary 1 outline 0,0 20,0 20,3000 0,3000"));
    CHECK(memcmp(&saved_world,&test_world,sizeof test_world)==0);
    CHECK(!g_preview.valid);
}

static void test_space_extents(void)
{
    room();
    CHECK(command("space 1 boundary 1"));
    CHECK(command("boundary 1 outline 0,0 2000,0 2000,3000 0,3000"));
    CHECK(test_world.spaces[0].room_max[0] == 2000);
    saved_world = test_world;
    CHECK(!command("column 1 in 1 at 2500 100 size 100 100 z 0 2000"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
    CHECK(!command("beam 1 in 1 along x from 2500 to 2800 at 500 width 100 depth 100 top 2000"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
    CHECK(command("boundary 1 outline 0,0 4000,0 4000,3000 0,3000"));
    CHECK(test_world.spaces[0].room_max[0] == 4000);
    CHECK(command("column 1 in 1 at 2500 100 size 100 100 z 0 2000"));
    CHECK(command("beam 1 in 1 along x from 2500 to 2800 at 500 width 100 depth 100 top 2000"));
    saved_world = test_world;
    CHECK(!command("surface 1 origin 0 0 2500 u +x v +y outline 0,0 2000,0 2000,3000 0,3000"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
    CHECK(command("delete column 1"));
    saved_world = test_world;
    CHECK(!command("boundary 1 outline 0,0 2000,0 2000,3000 0,3000"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
    CHECK(command("delete beam 1"));
    CHECK(command("placement 1 on boundary 1 origin 100 200 2500 u +x v +y"));
    CHECK(test_world.spaces[0].room_min[0] == 100 && test_world.spaces[0].room_min[1] == 200);
    CHECK(test_world.spaces[0].room_max[0] == 4100 && test_world.spaces[0].room_max[1] == 3200);
}

static void test_new_placement_transaction(void)
{
    room();
    CHECK(command("space 1 boundary 1"));
    saved_world = test_world;
    CHECK(!command("placement 2 on boundary 1 origin 0 0 100 u +x v +y"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
    CHECK(!command("surface 2 on boundary 1 origin 0 0 100 u +x v +y"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
    CHECK(command("delete space 1"));
    CHECK(command("placement 2 on boundary 1 origin 0 0 100 u +x v +y"));
    CHECK(test_world.placement_count == 2); /* Multiple placements remain legal without Space. */
}

static void test_grid_ref_rejects(void)
{
    CHECK(reference_default_world(&test_world)); history_clear();
    CHECK(command("grid 1 on 1 u 2000 v 1000"));
    CHECK(command("timber 4 27 33 role primary")); saved_world=test_world;
    CHECK(!command("place 4 on 1 at-line grid 1 v 0 +v +n"));
    CHECK(memcmp(&saved_world,&test_world,sizeof test_world)==0);
    CHECK(command("place 4 on 1 at-line grid 1 u 0 +v +n"));
    CHECK(test_world.anchors[3].anchor_kind==ANCHOR_AT_GRID);
    CHECK(!command("grid 1 on 1 u 2500")); CHECK(g_preview.valid);
    CHECK(test_world.timbers[3].length==2946);
}

static void test_place_through_short(void)
{
    room();
    CHECK(command("grid 1 on 1 u 2000"));
    CHECK(command("timber 1 20 20 role boundary"));
    CHECK(command("timber 2 20 20 role boundary"));
    CHECK(command("place 1 on 1 at-face e0 +u +n"));
    CHECK(command("place 2 on 1 at-face e2 -u +n"));
    CHECK(command("timber 3 27 33 role primary"));
    saved_world = test_world;
    CHECK(!command("place 3 on 1 at-line grid 1 u 0 through 1000"));
    CHECK(strstr(scene_last_error(), "缺少長度方向與深度側") != NULL);
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
}

static void test_place_revalidates_existing_i19(void)
{
    CHECK(reference_default_world(&test_world)); history_clear();
    saved_world=test_world;
    CHECK(!command("delete timber 1"));
    CHECK(memcmp(&saved_world,&test_world,sizeof test_world)==0);
    CHECK(g_preview.ready && !g_preview.valid);
    CHECK(g_preview.issue_count>0);
}

static void test_view_dist2_no_overflow(void)
{
    /* 3 km 線段、中點偏移 10mm：三次乘在 int64 會溢位，必須用 128-bit。 */
    Coord d = view_dist2_to_segment(
        (ViewPoint2){1500000, 10},
        (ViewPoint2){0, 0},
        (ViewPoint2){3000000, 0});
    CHECK(d == 100);
    d = view_dist2_to_segment(
        (ViewPoint2){1500000, 0},
        (ViewPoint2){0, 0},
        (ViewPoint2){3000000, 0});
    CHECK(d == 0);
}

static void test_partial_collinear_stop_is_not_duplicated(void)
{
    StopFace faces[]={
        {STOP_OUTLINE_EDGE,1,0,-1,0,EDGE_FIXED,1000,0,100},
        {STOP_TIMBER_SIDE,0,7,-1,0,EDGE_FIXED,1000,50,150}
    };
    const StopFace *stop=NULL;
    CHECK(pick_stop(faces,2,1000,60,80,&stop)==1);
    CHECK(stop && stop->kind==STOP_OUTLINE_EDGE);
    CHECK(count_legal_stops(faces,2,1000,60,80)==1);
    CHECK(pick_stop(faces,2,1000,110,140,&stop)==1);
    CHECK(stop && stop->kind==STOP_TIMBER_SIDE);
    CHECK(pick_stop(faces,2,1000,40,120,&stop)==0);
}

static void test_collinear_vertex_rect_corner(void)
{
    /* I2 permits adjacent collinear edges; I5 includes their shared vertex. */
    PolygonLoop2 loop = {.count=6,
        .v={{0,0},{100,0},{100,50},{100,100},{0,100},{0,50}}};
    for (size_t i=0; i<loop.count; ++i) loop.fixity[i]=EDGE_FIXED;
    SpaceBoundarySurface boundary = {.id=1, .outline=loop};
    PlacementSurface placement = {0};
    CHECK(poly_loop_is_valid(&loop));
    CHECK(boundary_is_valid(&boundary));
    CHECK(poly_point_on_edge(&loop, (SurfacePoint2){100,50}));
    CHECK(poly_contains_point(&loop, (SurfacePoint2){100,50}));
    CHECK(poly_contains_rect(&loop,80,20,100,50));
    CHECK(boundary_contains_rect(&boundary,80,20,100,50));
    CHECK(surface_contains_rect(&placement,&boundary,80,20,100,50));
    CHECK(!poly_contains_rect(&loop,80,20,101,50));
}

int main(void)
{
    test_collinear_vertex_rect_corner();
    test_partial_collinear_stop_is_not_duplicated();
    test_frame_updates();
    test_space_extents();
    test_new_placement_transaction();
    test_grid_ref_rejects();
    test_place_through_short();
    test_place_revalidates_existing_i19();
    test_view_dist2_no_overflow();
    printf("%d/%d integrity checks passed (World=%zu bytes)\n", checks-failures, checks, sizeof(World));
    return failures ? 1 : 0;
}
