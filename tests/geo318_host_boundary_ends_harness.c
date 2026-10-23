/* Actual H collector witness over an explicit, already-placed world.
 * This is not a CLI construction witness: it deliberately does not claim the
 * mutual-end scene can be reached through ordered place/load/rebuild. */
#ifdef _WIN32
#undef _WIN32
#endif
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_bridge_main
#include "../geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT
#define CHECK(tag,x) do{if(!(x)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
static int host_collector(void)
{
    memset(&g_world,0,sizeof g_world);g_definition_revision=0;
    CHECK("host-boundary-setup",feed_line("reading-a-host",1,
        "boundary 7 outline 0,0 500,0 500,13 1000,13 1000,1000 0,1000 fixity F F F F F F",&g_world));
    CHECK("host-placement-setup",feed_line("reading-a-host",2,
        "placement 7 on boundary 7 origin 0 0 0 u +x v +y",&g_world));
    g_world.wood.timber_count=2;
    for(size_t i=0;i<2;++i){
        g_world.wood.timbers[i]=(Timber){.id=(uint32_t)i+1,.size_a=27,.size_b=20,.length=500,
            .role=TIMBER_ROLE_BOUNDARY,.cut_priority=1,.placed=true,.origin={(Coord)i*500,(Coord)i*13,0},
            .axis_length={1,0,0},.axis_a={0,1,0},.axis_b={0,0,1}};
        g_world.wood.anchors[i]=(TimberAnchor){.placement_id=7,.uv={(Coord)i*500,(Coord)i*13},
            .anchor_kind=WOOD_ANCHOR_AT_EDGE,.span_mode=WOOD_SPAN_AUTO,.length_direction=SURFACE_DIRECTION_POS_U,
            .depth_side=SURFACE_DEPTH_POSITIVE_NORMAL,.ref_hole=-1,.ref_edge=(int)i*2,.order=i+1};
    }
    g_revalidate_error[0]=0;g_reference_capturing=true;g_reference_issue_count=0;
    CHECK("actual-host-collector-accepts-partial",reference_check_all(&g_world));
    CHECK("actual-host-collector-no-stale-fullwidth-issue",g_reference_issue_count==0);
    /* Keep the actual H collision collector after the exception: the second
     * timber now starts 1 mm inside the first, so the world must be refused. */
    g_world.wood.timbers[1].origin.x=499;g_world.wood.anchors[1].uv.u=499;
    CHECK("actual-host-collector-still-refuses-overlap",!reference_check_all(&g_world));
    bool collision=false;
    for(size_t i=0;i<g_reference_issue_count;++i)if(!strcmp(g_reference_issues[i].clause,"I11"))collision=true;
    CHECK("actual-host-collector-retains-i11",collision);
    g_reference_capturing=false;return 0;
}
int main(int argc,char **argv)
{if(argc==2&&!strcmp(argv[1],"host-collector"))return host_collector();return 2;}
