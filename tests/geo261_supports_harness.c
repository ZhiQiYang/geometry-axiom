#include "supports.h"
#include <stdio.h>
#include <string.h>

#define CHECK(name, expression) do { if (!(expression)) { \
    fprintf(stderr, "ASSERT:%s\n", name); return 1; } } while (0)

/* Linked from the frozen product source by the Python driver. The hardcoded
 * cases below are the value oracles; frozen comparison is additional proof. */
bool frozen_stop_matches_ref(const WoodStopFace *, const WoodStopRef *);
size_t frozen_stop_ref_candidates(const WoodStopFace *, size_t, const WoodStopRef *,
    GeoCoord, GeoCoord, const WoodStopFace **, size_t, bool *, bool *);
bool frozen_stop_shadowed(const WoodStopFace *, size_t, GeoCoord, GeoCoord);
size_t frozen_stop_pick(const WoodStopFace *, size_t, GeoCoord, GeoCoord, GeoCoord, const WoodStopFace **);
size_t frozen_stop_count_legal(const WoodStopFace *, size_t, GeoCoord, GeoCoord, GeoCoord);
bool frozen_boundary_props(const GeoLoop2View *, bool, GeoCoord, GeoCoord, GeoCoord, GeoCoord,
    bool *, bool *, int *);

typedef struct {
    int kind;
    uint32_t boundary_id, timber_id;
    int hole_index, edge_index, fixity;
    int64_t fixed, lo, hi;
} FrozenFaceLayout;
typedef struct { int kind, hole, edge; uint32_t timber; } FrozenRefLayout;

static int layout(void)
{
    CHECK("face-layout-size", sizeof(WoodStopFace) == sizeof(FrozenFaceLayout));
#define FIELD(n) CHECK("face-layout-" #n, offsetof(WoodStopFace,n) == offsetof(FrozenFaceLayout,n))
    FIELD(kind); FIELD(boundary_id); FIELD(timber_id); FIELD(hole_index);
    FIELD(edge_index); FIELD(fixity); FIELD(fixed); FIELD(lo); FIELD(hi);
#undef FIELD
    CHECK("ref-layout-size", sizeof(WoodStopRef) == sizeof(FrozenRefLayout));
#define FIELD(n) CHECK("ref-layout-" #n, offsetof(WoodStopRef,n) == offsetof(FrozenRefLayout,n))
    FIELD(kind); FIELD(hole); FIELD(edge); FIELD(timber);
#undef FIELD
    CHECK("face-enum", WOOD_STOP_OUTLINE_EDGE == 0 && WOOD_STOP_HOLE_EDGE == 1 && WOOD_STOP_MEMBER_SIDE == 2);
    CHECK("fixity-values", WOOD_STOP_FREE == 0 && WOOD_STOP_FIXED == 1);
    return 0;
}

static int references(void)
{
    WoodStopFace f = {0, UINT32_MAX, 11, -1, 4, 1, -30, -20, 50};
    WoodStopRef r = {0, -1, 4, 11};
    CHECK("reference-null-face", !wood_stop_matches_ref(NULL, &r));
    CHECK("reference-null-ref", !wood_stop_matches_ref(&f, NULL));
    CHECK("reference-outline", wood_stop_matches_ref(&f, &r));
    r.hole = -9; r.kind = -7;
    CHECK("reference-negative-hole-kind", wood_stop_matches_ref(&f, &r));
    r.edge = 3;
    CHECK("reference-outline-edge", !wood_stop_matches_ref(&f, &r));
    r.edge = -3; f.edge_index = -3;
    CHECK("reference-negative-edge", wood_stop_matches_ref(&f, &r));
    f.kind = WOOD_STOP_HOLE_EDGE;
    CHECK("reference-outline-kind", !wood_stop_matches_ref(&f, &r));
    r.hole = 0; f.hole_index = 0;
    CHECK("reference-hole", wood_stop_matches_ref(&f, &r));
    r.hole = 1;
    CHECK("reference-hole-index", !wood_stop_matches_ref(&f, &r));
    r.hole = 0; r.edge = 5;
    CHECK("reference-hole-edge", !wood_stop_matches_ref(&f, &r));
    r.edge = -3; f.kind = WOOD_STOP_OUTLINE_EDGE;
    CHECK("reference-hole-kind", !wood_stop_matches_ref(&f, &r));
    r.kind = 1; r.timber = UINT32_MAX; f.timber_id = UINT32_MAX;
    CHECK("reference-member-kind", !wood_stop_matches_ref(&f, &r));
    f.kind = WOOD_STOP_MEMBER_SIDE;
    CHECK("reference-member-uint32-max", wood_stop_matches_ref(&f, &r));
    r.timber = 0;
    CHECK("reference-member-id", !wood_stop_matches_ref(&f, &r));
    f.timber_id = 0;
    CHECK("reference-member-zero-id", wood_stop_matches_ref(&f, &r));
    return 0;
}

static int candidates(void)
{
    WoodStopFace f[] = {
        {2,0,7,-1,0,1, 0,-5,20},
        {2,0,8,-1,0,1,10,-5,20}, /* unmatched */
        {2,0,7,-1,0,0,20, 1,20}, /* narrow and FREE: only narrow */
        {2,0,7,-1,0,1,30,-5, 9},
        {2,0,7,-1,0,0,40,-5,20},
        {2,0,7,-1,0,1,50, 0,10},
        {2,0,7,-1,0,7,60,-5,20}  /* no new fixity admission rule */
    };
    WoodStopRef r = {1,-1,-1,7};
    const WoodStopFace sentinel = {0};
    const WoodStopFace *out[4] = {&sentinel,&sentinel,&sentinel,&sentinel};
    bool free_seen = false, narrow_seen = false;
    size_t n = wood_stop_ref_candidates(f,7,&r,0,10,out,4,&free_seen,&narrow_seen);
    CHECK("candidates-match-width-free", n == 3);
    CHECK("candidates-input-order", out[0] == &f[0] && out[1] == &f[5] && out[2] == &f[6]);
    CHECK("candidates-unwritten-tail", out[3] == &sentinel);
    CHECK("candidates-diagnostic-flags", free_seen && narrow_seen);
    free_seen = narrow_seen = false;
    n = wood_stop_ref_candidates(&f[2],1,&r,0,10,out,4,&free_seen,&narrow_seen);
    CHECK("candidates-width-before-free", n == 0 && !free_seen && narrow_seen);
    free_seen = narrow_seen = false;
    out[0] = out[1] = &sentinel;
    n = wood_stop_ref_candidates(f,7,&r,0,10,out,1,&free_seen,&narrow_seen);
    CHECK("candidates-capacity-count", n == 1 && out[0] == &f[0] && out[1] == &sentinel);
    CHECK("candidates-flags-after-full", free_seen && narrow_seen);
    free_seen = narrow_seen = false;
    n = wood_stop_ref_candidates(f,7,&r,0,10,NULL,0,&free_seen,&narrow_seen);
    CHECK("candidates-zero-capacity", n == 0 && free_seen && narrow_seen);
    n = wood_stop_ref_candidates(NULL,0,NULL,0,10,NULL,0,&free_seen,&narrow_seen);
    CHECK("candidates-flags-accumulate", n == 0 && free_seen && narrow_seen);
    free_seen = narrow_seen = false;
    n = wood_stop_ref_candidates(f,7,NULL,0,10,out,4,&free_seen,&narrow_seen);
    CHECK("candidates-null-ref", n == 0 && !free_seen && !narrow_seen);
    return 0;
}

static int shadow(void)
{
    WoodStopFace f[] = {
        {0,1,0,-1,0,0,-10, 0,10},
        {2,0,4,-1,0,1,-10, 0,20},
        {1,1,0, 0,0,1,-10, 0,20}
    };
    CHECK("shadow-first-face", !wood_stop_shadowed(f,0,0,10));
    CHECK("shadow-earlier-free-edge", wood_stop_shadowed(f,1,0,10));
    CHECK("shadow-exposed-extension", !wood_stop_shadowed(f,1,10,20));
    CHECK("shadow-partial-not-full", !wood_stop_shadowed(f,1,0,20));
    CHECK("shadow-only-member", !wood_stop_shadowed(f,2,0,10));
    f[0].fixed = -9;
    CHECK("shadow-same-coordinate", !wood_stop_shadowed(f,1,0,10));
    f[0].fixed = -10; f[0].lo = 1;
    CHECK("shadow-full-low", !wood_stop_shadowed(f,1,0,10));
    f[0].lo = 0; f[0].hi = 9;
    CHECK("shadow-full-high", !wood_stop_shadowed(f,1,0,10));
    f[0] = f[1]; f[1].kind = WOOD_STOP_OUTLINE_EDGE;
    CHECK("shadow-later-edge-does-not-shadow", !wood_stop_shadowed(f,0,0,10));
    f[1].kind = WOOD_STOP_MEMBER_SIDE;
    CHECK("shadow-earlier-member", wood_stop_shadowed(f,1,0,10));
    WoodStopFace split[] = {
        {0,1,0,-1,0,1,-10, 0,10},
        {0,1,0,-1,1,1,-10,10,20},
        {2,0,4,-1,0,1,-10, 0,20}
    };
    CHECK("shadow-does-not-union-earlier-faces", !wood_stop_shadowed(split,2,0,20));
    return 0;
}

static int pick(void)
{
    WoodStopFace f[] = {
        {0,1,0,-1,0,0,-10, 0,10},
        {2,0,4,-1,0,1,-10, 0,20},
        {1,1,0, 0,0,1,-10,30,40}
    };
    const WoodStopFace sentinel = {0};
    const WoodStopFace *out = &sentinel;
    CHECK("pick-shadowed-one", wood_stop_pick(f,3,-10,0,10,&out) == 1 && out == &f[0]);
    CHECK("pick-free-is-hit", out->fixity == WOOD_STOP_FREE);
    out = &sentinel;
    CHECK("pick-exposed-extension", wood_stop_pick(f,3,-10,10,20,&out) == 1 && out == &f[1]);
    out = &sentinel;
    CHECK("pick-coordinate-filter", wood_stop_pick(f,3,-9,0,10,&out) == 0 && out == &sentinel);
    CHECK("pick-low-filter", wood_stop_pick(f,3,-10,-1,10,&out) == 0 && out == &sentinel);
    CHECK("pick-high-filter", wood_stop_pick(f,3,-10,0,21,&out) == 0 && out == &sentinel);
    f[2].lo = 0; f[2].hi = 10;
    CHECK("pick-ambiguous-output-unchanged", wood_stop_pick(f,3,-10,0,10,&out) == 2 && out == &sentinel);
    CHECK("pick-null-output", wood_stop_pick(f,2,-10,0,10,NULL) == 1);
    CHECK("pick-empty-output-unchanged", wood_stop_pick(NULL,0,0,0,1,&out) == 0 && out == &sentinel);
    return 0;
}

static int legal(void)
{
    WoodStopFace f[] = {
        {0,1,0,-1,0,0,-10,0,10},
        {2,0,4,-1,0,1,-10,0,20}
    };
    CHECK("legal-free-excluded-and-shadows", wood_stop_count_legal(f,2,-10,0,10) == 0);
    CHECK("legal-exposed-extension", wood_stop_count_legal(f,2,-10,10,20) == 1);
    CHECK("legal-coordinate-filter", wood_stop_count_legal(&f[1],1,-9,0,10) == 0);
    CHECK("legal-low-filter", wood_stop_count_legal(&f[1],1,-10,-1,10) == 0);
    CHECK("legal-high-filter", wood_stop_count_legal(&f[1],1,-10,0,21) == 0);
    f[0].fixity = 1; f[1].kind = 1;
    CHECK("legal-multiple-not-unique", wood_stop_count_legal(f,2,-10,0,10) == 2);
    f[0].fixity = -3;
    CHECK("legal-nonzero-fixity", wood_stop_count_legal(f,2,-10,0,10) == 2);
    CHECK("legal-empty", wood_stop_count_legal(NULL,0,0,0,10) == 0);
    return 0;
}

static int expect_boundary(const char *name, const GeoLoop2View *loop, bool along_v,
    GeoCoord lo, GeoCoord hi, GeoCoord cross_lo, GeoCoord cross_hi,
    bool expected_ok, bool expected_on, bool expected_covers, int expected_edge)
{
    bool on = true, covers = true;
    int edge = 91;
    bool ok = wood_member_boundary_props(loop,along_v,lo,hi,cross_lo,cross_hi,&on,&covers,&edge);
    CHECK(name, ok == expected_ok && on == expected_on && covers == expected_covers && edge == expected_edge);
    return 0;
}

static int boundary(void)
{
    const GeoPoint2 rect[] = {{0,0},{100,0},{100,60},{0,60}};
    const GeoPoint2 stepped[] = {{0,0},{100,0},{100,20},{30,20},{30,10},{0,10}};
    GeoLoop2View loop = {rect,4}, step = {stepped,6}, empty = {NULL,0};
#define EXPECT(name, lp, av, lo, hi, cl, ch, ok, on, cov, edge) \
    do { if (expect_boundary(name,lp,av,lo,hi,cl,ch,ok,on,cov,edge)) return 1; } while (0)
    EXPECT("boundary-null-defaults",NULL,false,0,100,0,10,false,false,false,-1);
    EXPECT("boundary-empty-defaults",&empty,false,0,100,0,10,true,false,false,-1);
    EXPECT("boundary-low-side",&loop,false,20,80,0,10,true,true,false,0);
    EXPECT("boundary-high-side",&loop,false,20,80,-10,0,true,true,false,0);
    EXPECT("boundary-full-edge",&loop,false,0,100,0,10,true,true,true,0);
    EXPECT("boundary-cover-low-required",&loop,false,20,100,0,10,true,true,false,0);
    EXPECT("boundary-cover-high-required",&loop,false,0,80,0,10,true,true,false,0);
    EXPECT("boundary-covered-beyond",&loop,false,-10,110,0,10,true,true,true,0);
    EXPECT("boundary-positive-overlap-only",&loop,false,100,120,0,10,true,false,false,-1);
    EXPECT("boundary-no-collinear-side",&loop,false,20,80,10,20,true,false,false,-1);
    EXPECT("boundary-along-v",&loop,true,0,60,90,100,true,true,true,1);
    EXPECT("boundary-parallel-required",&loop,false,0,60,0,10,true,true,false,0);
    EXPECT("boundary-tie-earlier-index",&loop,false,20,80,0,60,true,true,false,0);
    EXPECT("boundary-cover-beats-longer",&step,false,0,50,0,10,true,true,true,4);
    EXPECT("boundary-longer-overlap",&step,false,20,80,0,10,true,true,false,0);
    /* Rotate the loop so the shorter uncovered candidate is encountered first. */
    const GeoPoint2 rotated[] = {{30,10},{0,10},{0,0},{100,0},{100,20},{30,20}};
    GeoLoop2View rot = {rotated,6};
    EXPECT("boundary-later-longer-wins",&rot,false,20,80,0,10,true,true,false,2);
#undef EXPECT
    return 0;
}

static uint32_t state = UINT32_C(261);
static uint32_t next_random(void)
{
    state = state * UINT32_C(1664525) + UINT32_C(1013904223);
    return state;
}

static int equivalence(void)
{
    WoodStopFace f[9], sentinel = {0};
    for (size_t trial = 0; trial < 300; ++trial) {
        size_t count = next_random() % 10;
        for (size_t i = 0; i < count; ++i) {
            f[i] = (WoodStopFace){(int)(next_random()%4),next_random(),next_random()%3,
                (int)(next_random()%4)-2,(int)(next_random()%5)-2,(int)(next_random()%4)-1,
                (GeoCoord)(next_random()%5)-2,(GeoCoord)(next_random()%9)-4,(GeoCoord)(next_random()%9)-4};
        }
        WoodStopRef ref = {(int)(next_random()%4)-1,(int)(next_random()%4)-2,
            (int)(next_random()%5)-2,next_random()%3};
        GeoCoord lo = (GeoCoord)(next_random()%7)-3, hi = (GeoCoord)(next_random()%7)-3;
        GeoCoord at = (GeoCoord)(next_random()%5)-2;
        for (size_t i = 0; i < count; ++i) {
            CHECK("frozen-match", wood_stop_matches_ref(&f[i],&ref) == frozen_stop_matches_ref(&f[i],&ref));
            CHECK("frozen-shadow", wood_stop_shadowed(f,i,lo,hi) == frozen_stop_shadowed(f,i,lo,hi));
        }
        const WoodStopFace *actual[9], *expected[9], *a = &sentinel, *e = &sentinel;
        for (size_t i = 0; i < 9; ++i) actual[i] = expected[i] = &sentinel;
        bool af = (trial%2)!=0, an = (trial%3)!=0, ef = af, en = an;
        size_t cap = next_random()%10;
        size_t na = wood_stop_ref_candidates(f,count,&ref,lo,hi,actual,cap,&af,&an);
        size_t ne = frozen_stop_ref_candidates(f,count,&ref,lo,hi,expected,cap,&ef,&en);
        CHECK("frozen-candidates", na == ne && af == ef && an == en && memcmp(actual,expected,sizeof actual) == 0);
        CHECK("frozen-pick", wood_stop_pick(f,count,at,lo,hi,&a) == frozen_stop_pick(f,count,at,lo,hi,&e) && a == e);
        CHECK("frozen-count", wood_stop_count_legal(f,count,at,lo,hi) == frozen_stop_count_legal(f,count,at,lo,hi));
    }
    const GeoPoint2 rect[] = {{-20,-10},{50,-10},{50,40},{-20,40}};
    GeoLoop2View loop = {rect,4};
    for (size_t i = 0; i < 100; ++i) {
        GeoCoord lo = (GeoCoord)(next_random()%100)-40, hi = lo+(GeoCoord)(next_random()%100);
        GeoCoord cl = i%2 ? -20 : -10, ch = i%2 ? 50 : 40;
        bool a_on, a_cover, e_on, e_cover;
        int a_edge, e_edge;
        bool a = wood_member_boundary_props(&loop,i%2!=0,lo,hi,cl,ch,&a_on,&a_cover,&a_edge);
        bool e = frozen_boundary_props(&loop,i%2!=0,lo,hi,cl,ch,&e_on,&e_cover,&e_edge);
        CHECK("frozen-boundary", a == e && a_on == e_on && a_cover == e_cover && a_edge == e_edge);
    }
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    if (!strcmp(argv[1],"layout")) return layout();
    if (!strcmp(argv[1],"references")) return references();
    if (!strcmp(argv[1],"candidates")) return candidates();
    if (!strcmp(argv[1],"shadow")) return shadow();
    if (!strcmp(argv[1],"pick")) return pick();
    if (!strcmp(argv[1],"legal")) return legal();
    if (!strcmp(argv[1],"boundary")) return boundary();
    if (!strcmp(argv[1],"equivalence")) return equivalence();
    return 2;
}
