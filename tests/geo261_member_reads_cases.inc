/* Same logical candidate, deliberately permuted storage. Every memo value is
 * warmed through the real H function and real registered K/W providers. The
 * permutation moves each member together with its anchor and preserves its
 * declaration order, canonical definition and already VALID pose by ID. */
typedef struct {
    World world,before;
    ReferenceEval ctx;
    WoodMemberPlacement canonical_anchor[2];
    GeoBox3 canonical_pose[2];
    bool separate_hosts;
} MemberReadsFixture;

static void mr_swap_storage(World *world)
{
    WoodMember member=world->wood.timbers[0];
    world->wood.timbers[0]=world->wood.timbers[1];world->wood.timbers[1]=member;
    WoodMemberPlacement anchor=world->wood.anchors[0];
    world->wood.anchors[0]=world->wood.anchors[1];world->wood.anchors[1]=anchor;
}
static MemberReadsFixture *mr_fixture(bool separate_hosts)
{
    MemberReadsFixture *f=calloc(1,sizeof *f);if(!f)return NULL;
    f->separate_hosts=separate_hosts;f->ctx.world=&f->world;
    PlacementSurface host={.id=7,.frame={{0,0,0},{1,0,0},{0,1,0},{0,0,1}},.rect={0,0,300,300}};
    if(!app_placement_stage(&f->world,&host))return NULL;
    host.id=8;host.frame.origin.y=100;
    if(!app_placement_stage(&f->world,&host))return NULL;
    f->world.wood.timber_count=2;
    for(size_t i=0;i<2;++i){
        f->world.wood.timbers[i]=(WoodMember){.id=41+(uint32_t)i,.length=100,.size_a=10,.size_b=5,
            .placed=true,.auto_length=true,.role=WOOD_MEMBER_ROLE_BOUNDARY,.cut_priority=1+(int)i,
            .origin={0,i?(separate_hosts?140:40):0,0},.axis_length={1,0,0},.axis_a={0,1,0},.axis_b={0,0,1}};
        f->world.wood.anchors[i]=(WoodMemberPlacement){.placement_id=i&&separate_hosts?8:7,.uv={0,i?40:0},
            .order=i+1,.anchor_kind=WOOD_ANCHOR_AT,.length_direction=GEO_DIRECTION_POS_U,.depth_side=WOOD_DEPTH_POSITIVE_NORMAL};
    }
    memcpy(&f->before,&f->world,sizeof f->world);
    if(!reference_sources_ensure(&f->ctx))return NULL;
    for(size_t i=0;i<2;++i){uint32_t id=41+(uint32_t)i;GeoSourceValue pose;
        if(!wood_definition_sources_placement(f->ctx.definition_sources,id,&f->canonical_anchor[i]))return NULL;
        f->ctx.use_current_values=true;
        bool ok=geo_eval_source(f->ctx.sources,(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&pose)==GEO_SOURCE_OK;
        f->ctx.use_current_values=false;
        if(!ok||pose.kind!=GEO_SOURCE_BOX)return NULL;
        f->canonical_pose[i]=pose.as.box;
    }
    if(memcmp(&f->before,&f->world,sizeof f->world))return NULL;
    return f;
}
static void mr_dispose(MemberReadsFixture *f)
{reference_sources_dispose(&f->ctx);free(f);}
static bool mr_canonical_truth_unchanged(MemberReadsFixture *f)
{
    for(size_t i=0;i<2;++i){uint32_t id=41+(uint32_t)i;WoodMemberPlacement anchor={0};GeoSourceValue pose;
        if(!wood_definition_sources_placement(f->ctx.definition_sources,id,&anchor)||
           memcmp(&anchor,&f->canonical_anchor[i],sizeof anchor)||
           geo_eval_source(f->ctx.sources,(GeoSourceRef){APP_SOURCE_MEMBER_POSE,&id,sizeof id},GEO_DEPENDENCY_VALUE_REQUIRED,&pose)!=GEO_SOURCE_OK||
           pose.kind!=GEO_SOURCE_BOX||memcmp(&pose.as.box,&f->canonical_pose[i],sizeof pose.as.box))return false;
    }
    return true;
}
static bool mr_storage_preserves_scene(MemberReadsFixture *f,bool swapped)
{
    World *copy=malloc(sizeof *copy);if(!copy)return false;
    memcpy(copy,&f->world,sizeof *copy);if(swapped)mr_swap_storage(copy);
    bool same=!memcmp(copy,&f->before,sizeof *copy);free(copy);return same;
}
static bool member_reads_anchor_id_case(void)
{
    MemberReadsFixture *f=mr_fixture(true);REQUIRE("member-anchor-cache-fixture",f);
    WoodMemberPlacement first={0},second={0};
    REQUIRE("member-anchor-cache-warm-real-id",reference_member_anchor_read(&f->ctx,0,41,&first)&&
        first.placement_id==7&&first.order==1&&f->ctx.member_reads[0].anchor_valid&&f->ctx.member_reads[0].id==41);
    mr_swap_storage(&f->world);
    REQUIRE("member-anchor-cache-permutation-preserves-scene",mr_storage_preserves_scene(f,true));
    REQUIRE("member-anchor-cache-id-must-match",reference_member_anchor_read(&f->ctx,0,42,&second)&&
        second.placement_id==8&&second.order==2&&second.uv.v==40&&f->ctx.member_reads[0].id==42);
    REQUIRE("member-anchor-cache-canonical-values-stay-fixed",mr_canonical_truth_unchanged(f));
    REQUIRE("member-anchor-cache-query-does-not-change-world",mr_storage_preserves_scene(f,true));
    mr_dispose(f);return true;
}
static bool member_reads_anchor_miss_case(void)
{
    MemberReadsFixture *f=mr_fixture(false);REQUIRE("member-anchor-miss-fixture",f);
    WoodContactSourceFacts *warm=calloc(1,sizeof *warm),*after=calloc(1,sizeof *after);
    REQUIRE("member-anchor-miss-memory",warm&&after);
    WoodContactSourceRequest request={.placement_id=7};
    REQUIRE("member-anchor-miss-natural-warm",reference_contact_facts(&f->ctx,f->ctx.sources,&request,warm)&&
        warm->member_count==2&&warm->members[0].member->id==41&&warm->members[1].member->id==42&&
        warm->members[0].footprint_valid&&warm->members[0].footprint.min_v==0&&warm->members[0].footprint.max_v==10&&
        warm->members[1].footprint_valid&&warm->members[1].footprint.min_v==40&&warm->members[1].footprint.max_v==50&&
        f->ctx.member_reads[0].footprint_valid&&f->ctx.member_reads[1].footprint_valid);
    mr_swap_storage(&f->world);
    REQUIRE("member-anchor-miss-permutation-preserves-scene",mr_storage_preserves_scene(f,true));
    REQUIRE("member-anchor-miss-invalidates-footprint",reference_contact_facts(&f->ctx,f->ctx.sources,&request,after)&&
        after->member_count==2&&after->members[0].member->id==42&&after->members[0].order==2&&after->members[0].footprint_valid&&
        after->members[0].footprint.min_v==40&&after->members[0].footprint.max_v==50&&
        after->members[1].member->id==41&&after->members[1].order==1&&after->members[1].footprint_valid&&
        after->members[1].footprint.min_v==0&&after->members[1].footprint.max_v==10);
    REQUIRE("member-anchor-miss-canonical-values-stay-fixed",mr_canonical_truth_unchanged(f));
    REQUIRE("member-anchor-miss-query-does-not-change-world",mr_storage_preserves_scene(f,true));
    free(warm);free(after);mr_dispose(f);return true;
}
/* With the normal invalidator intact, removing only the placement check is
 * expected to remain equivalent for this valid candidate. The paired control
 * first removes that invalidator in both baseline and withdrawn variants; the
 * placement check then independently prevents reuse across two real hosts.
 * Neither variant injects or edits memo bytes. */
static bool member_reads_placement_key_case(void)
{
    MemberReadsFixture *f=mr_fixture(true);REQUIRE("contact-footprint-cache-placement-fixture",f);
    WoodContactSourceFacts *on7=calloc(1,sizeof *on7),*on8=calloc(1,sizeof *on8),*after=calloc(1,sizeof *after);
    REQUIRE("contact-footprint-cache-placement-memory",on7&&on8&&after);
    WoodContactSourceRequest request7={.placement_id=7},request8={.placement_id=8};
    REQUIRE("contact-footprint-cache-placement-natural-warm",reference_contact_facts(&f->ctx,f->ctx.sources,&request7,on7)&&
        reference_contact_facts(&f->ctx,f->ctx.sources,&request8,on8)&&on7->member_count==2&&on8->member_count==2&&
        on7->members[0].footprint_valid&&on7->members[0].footprint.min_v==0&&
        on8->members[1].footprint_valid&&on8->members[1].footprint.min_v==40&&
        f->ctx.member_reads[0].footprint_valid&&f->ctx.member_reads[0].placement==7&&
        f->ctx.member_reads[1].footprint_valid&&f->ctx.member_reads[1].placement==8);
    mr_swap_storage(&f->world);
    REQUIRE("contact-footprint-cache-placement-permutation-preserves-scene",mr_storage_preserves_scene(f,true));
    REQUIRE("contact-footprint-cache-placement-must-match",reference_contact_facts(&f->ctx,f->ctx.sources,&request8,after)&&
        after->member_count==2&&after->members[0].member->id==42&&after->members[0].placement_id==8&&after->members[0].footprint_valid&&
        after->members[0].footprint.min_v==40&&after->members[0].footprint.max_v==50&&!after->members[1].footprint_valid);
    REQUIRE("contact-footprint-cache-placement-canonical-values-stay-fixed",mr_canonical_truth_unchanged(f));
    REQUIRE("contact-footprint-cache-placement-query-does-not-change-world",mr_storage_preserves_scene(f,true));
    free(on7);free(on8);free(after);mr_dispose(f);return true;
}
