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
    room();
    CHECK(command("guide 1 1 u 300"));
    CHECK(command("guide 2 1 v 500"));
    CHECK(command("timber 1 1800 27 33 role primary"));
    CHECK(command("place 1 on 1 at-guides 1 2 +u +n"));
    CHECK(command("move 1 600")); /* Frozen local anchor must remain at v=300. */
    CHECK(command("placement 1 on boundary 1 origin 0 0 3000 u +x v +y"));
    CHECK(test_world.timbers[0].origin.z == 3000);
    CHECK(test_world.timbers[0].origin.x == 500 && test_world.timbers[0].origin.y == 300);
    CHECK(test_world.anchors[0].uv.u == 500 && test_world.anchors[0].uv.v == 300);
    CHECK(test_world.timbers[0].length == 1800);
    CHECK(command("undo"));
    CHECK(test_world.timbers[0].origin.z == 2500);
    CHECK(command("redo"));
    CHECK(test_world.timbers[0].origin.z == 3000);
    CHECK(command("placement 1 on boundary 1 origin 0 0 3000 u +y v -x"));
    CHECK(test_world.timbers[0].origin.x == -300 && test_world.timbers[0].origin.y == 500);
    saved_world = test_world;
    CHECK(!command("boundary 1 outline 0,0 200,0 200,3000 0,3000"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
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
    room();
    CHECK(command("surface 2 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000"));
    CHECK(command("grid 1 on 1 u 2000"));
    CHECK(command("timber 1 2960 27 33 role primary"));
    saved_world = test_world;
    CHECK(!command("place 1 on 2 at 2014 20 +v +n grid-ref 1 u 0"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);

    room();
    CHECK(command("grid 1 on 1 u 2000 v 1000"));
    CHECK(command("timber 2 20 20 role boundary"));
    CHECK(command("timber 3 20 20 role boundary"));
    CHECK(command("place 2 on 1 at-edge e0 +u +n"));
    CHECK(command("place 3 on 1 at-edge e2 -u +n"));
    CHECK(command("timber 1 2960 27 33 role primary"));
    saved_world = test_world;
    CHECK(!command("place 1 on 1 at 2014 20 +v +n grid-ref 1 v 0"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);

    room();
    CHECK(command("grid 1 on 1 u 2000"));
    CHECK(command("timber 2 20 20 role boundary"));
    CHECK(command("timber 3 20 20 role boundary"));
    CHECK(command("place 2 on 1 at-edge e0 +u +n"));
    CHECK(command("place 3 on 1 at-edge e2 -u +n"));
    CHECK(command("timber 1 2960 27 33 role primary"));
    saved_world = test_world;
    CHECK(!command("place 1 on 1 at 0 20 +v +n grid-ref 1 u 0"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);

    room();
    CHECK(command("grid 1 on 1 u 2000"));
    CHECK(command("timber 1 2960 27 33 role primary"));
    saved_world = test_world;
    CHECK(!command("place 1 on 1 at 2014 20 +v +n grid-ref 1 u 0"));
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);

    room();
    CHECK(command("grid 1 on 1 u 2000"));
    CHECK(command("timber 2 20 20 role boundary"));
    CHECK(command("timber 3 20 20 role boundary"));
    CHECK(command("place 2 on 1 at-edge e0 +u +n"));
    CHECK(command("place 3 on 1 at-edge e2 -u +n"));
    CHECK(command("timber 1 2960 27 33 role primary"));
    CHECK(command("place 1 on 1 at 2014 20 +v +n grid-ref 1 u 0"));
    CHECK(test_world.timbers[2].id == 1);
    CHECK(test_world.anchors[2].anchor_kind == ANCHOR_AT_GRID);
    CHECK(test_world.anchors[2].span_mode == SPAN_AUTO);
}

static void test_place_through_short(void)
{
    room();
    CHECK(command("grid 1 on 1 u 2000"));
    CHECK(command("timber 1 20 20 role boundary"));
    CHECK(command("timber 2 20 20 role boundary"));
    CHECK(command("place 1 on 1 at-edge e0 +u +n"));
    CHECK(command("place 2 on 1 at-edge e2 -u +n"));
    CHECK(command("timber 3 27 33 role primary"));
    saved_world = test_world;
    CHECK(!command("place 3 on 1 at-grid 1 u 0 through 1000"));
    CHECK(strstr(scene_last_error(), "缺少長度方向與深度側") != NULL);
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
}

static void test_place_revalidates_existing_i19(void)
{
    room();
    CHECK(command("timber 1 1000 27 33 role primary"));
    CHECK(command("place 1 on 1 at 2000 100 +v +n"));
    CHECK(command("timber 2 3000 20 20 role secondary"));
    saved_world = test_world;
    CHECK(!command("place 2 on 1 at 500 1100 +u +n"));
    CHECK(strstr(scene_last_error(), "V_CUT_PRIORITY") != NULL);
    CHECK(memcmp(&saved_world, &test_world, sizeof test_world) == 0);
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

int main(void)
{
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
