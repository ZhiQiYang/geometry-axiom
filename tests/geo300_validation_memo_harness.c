/* The actual H translation unit and K/W objects; no replacement World or
 * validation policy. The Python driver adds only a read counter to the real
 * app_reference_member_anchor entry in a private source copy. */
#ifdef _WIN32
#undef _WIN32
#endif
#include <stddef.h>
static size_t validation_test_anchor_reads;
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_validation_memo_bridge_main
#include "../geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT
#define CHECK(c,n) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",n);return 1;}}while(0)

static int scope(void)
{
    World *world=calloc(1,sizeof *world),*other=calloc(1,sizeof *other);
    AppAnchorMemo *memo=calloc(1,sizeof *memo);WoodMemberPlacement value;
    CHECK(world&&other&&memo,"anchor-memo-allocation");
    world->wood.timber_count=2;
    world->wood.timbers[0].id=17;world->wood.timbers[1].id=29;
    world->wood.anchors[0]=(WoodMemberPlacement){.placement_id=3,.uv={11,13}};
    world->wood.anchors[1]=(WoodMemberPlacement){.placement_id=7,.uv={19,23}};
    app_anchor_memo_begin(memo,world);validation_test_anchor_reads=0;
    CHECK(app_anchor_memo_read(memo,0,&value)&&value.placement_id==3&&value.uv.u==11&&value.uv.v==13,
        "anchor-memo-first-source-value");
    CHECK(app_anchor_memo_read(memo,0,&value)&&value.placement_id==3&&value.uv.u==11&&value.uv.v==13,
        "anchor-memo-repeated-source-value");
    CHECK(validation_test_anchor_reads==1,"anchor-memo-single-read-per-scope");
    CHECK(app_anchor_memo_read(memo,1,&value)&&value.placement_id==7&&value.uv.u==19&&value.uv.v==23,
        "anchor-memo-distinct-member-value");
    CHECK(validation_test_anchor_reads==2,"anchor-memo-distinct-member-read");
    /* End the old immutable scope before changing the reused member slot. */
    world->wood.timbers[0].id=41;
    world->wood.anchors[0]=(WoodMemberPlacement){.placement_id=9,.uv={31,37}};
    app_anchor_memo_begin(memo,world);
    CHECK(app_anchor_memo_read(memo,0,&value)&&value.placement_id==9&&value.uv.u==31&&value.uv.v==37,
        "anchor-memo-new-scope-reloads-slot");
    CHECK(validation_test_anchor_reads==3,"anchor-memo-new-scope-read");
    other->wood.timber_count=1;other->wood.timbers[0].id=41;
    other->wood.anchors[0]=(WoodMemberPlacement){.placement_id=12,.uv={43,47}};
    app_anchor_memo_begin(memo,other);
    CHECK(app_anchor_memo_read(memo,0,&value)&&value.placement_id==12&&value.uv.u==43&&value.uv.v==47,
        "anchor-memo-new-world-isolation");
    CHECK(validation_test_anchor_reads==4,"anchor-memo-new-world-read");
    free(memo);free(other);free(world);return 0;
}

static int errors(void)
{
    World *world=calloc(1,sizeof *world);AppAnchorMemo *memo=calloc(1,sizeof *memo);
    WoodMemberPlacement value;memset(&value,0x5a,sizeof value);WoodMemberPlacement before=value;
    CHECK(world&&memo,"anchor-memo-error-allocation");
    app_anchor_memo_begin(memo,world);validation_test_anchor_reads=0;
    CHECK(!app_anchor_memo_read(memo,0,&value),"anchor-memo-first-missing-rejected");
    CHECK(!memcmp(&value,&before,sizeof value),"anchor-memo-failure-preserves-output");
    CHECK(!app_anchor_memo_read(memo,0,&value),"anchor-memo-failure-not-cached");
    CHECK(validation_test_anchor_reads==2,"anchor-memo-failure-retried");
    CHECK(!app_anchor_memo_read(memo,WORLD_MAX_TIMBERS,&value),"anchor-memo-capacity-index-rejected");
    CHECK(!app_anchor_memo_read(memo,SIZE_MAX,&value),"anchor-memo-large-index-rejected");
    CHECK(validation_test_anchor_reads==4,"anchor-memo-bounds-use-original-reader");
    CHECK(!memcmp(&value,&before,sizeof value),"anchor-memo-bounds-preserve-output");
    free(memo);free(world);return 0;
}

static int placed(const char *path,const char *mode)
{
    memset(&g_world,0,sizeof g_world);g_definition_revision=0;
    CHECK(parse_scene_file(path,&g_world),"anchor-memo-real-fixture-load");
    history_clear();g_preview.ready=false;
    CHECK(g_world.wood.timber_count==8,"anchor-memo-real-fixture-count");
    for(size_t i=0;i<g_world.wood.timber_count;++i)
        CHECK(g_world.wood.timbers[i].placed,"anchor-memo-real-fixture-all-placed");
    World *before=malloc(sizeof *before);CHECK(before,"anchor-memo-snapshot-allocation");
    memcpy(before,&g_world,sizeof *before);validation_test_anchor_reads=0;
    if(!strcmp(mode,"domain")){
        AppValidationInputs *inputs=calloc(1,sizeof *inputs);AppValidationDomain domain;
        CHECK(inputs,"domain-borrow-inputs-allocation");
        app_world_validation_context(&g_world,inputs);
        CHECK(app_validation_domain(inputs,1,NULL,&domain),"domain-borrow-real-host");
        CHECK(domain.p==&inputs->host,"domain-borrow-no-host-copy");
        CHECK(domain.b==(inputs->has_boundary?&inputs->boundary:NULL),"domain-borrow-boundary-view");
        PlacementSurface *expected=malloc(sizeof *expected);SpaceBoundarySurface boundary;
        const SpaceBoundarySurface *view=NULL;CHECK(expected,"domain-borrow-expected-allocation");
        CHECK(app_reference_host_read(&g_world,1,expected,&boundary,&view),"domain-borrow-original-reader");
        CHECK(!memcmp(expected,domain.p,sizeof *expected),"domain-borrow-exact-host-value");
        CHECK(!app_validation_domain(inputs,UINT32_MAX,NULL,&domain),"domain-borrow-missing-host-rejected");
        CHECK(app_validation_domain(inputs,1,NULL,&domain)&&domain.p->id==1,"domain-borrow-after-failure");
        free(expected);free(inputs);
    }else if(!strcmp(mode,"reference")){
        CHECK(reference_check_all(&g_world),"anchor-memo-real-reference-validation");
        CHECK(validation_test_anchor_reads==8,"anchor-memo-reference-callsite-linear-reads");
    }else{
        AppValidationInputs *inputs=calloc(1,sizeof *inputs);char error[256]="";
        CHECK(inputs,"anchor-memo-validation-inputs-allocation");
        WoodWorldValidationContext context=app_world_validation_context(&g_world,inputs);
        CHECK(wood_world_validate_members(&context,error,sizeof error),"anchor-memo-real-world-validation");
        CHECK(validation_test_anchor_reads==8,"anchor-memo-world-callsite-linear-reads");
        free(inputs);
    }
    CHECK(!memcmp(before,&g_world,sizeof *before),"anchor-memo-validation-keeps-world-bytes");
    free(before);return 0;
}

int main(int argc,char **argv)
{
    if(argc==2&&!strcmp(argv[1],"scope"))return scope();
    if(argc==2&&!strcmp(argv[1],"errors"))return errors();
    if(argc==3&&(!strcmp(argv[1],"reference")||!strcmp(argv[1],"world")||!strcmp(argv[1],"domain")))return placed(argv[2],argv[1]);
    return 2;
}
