/* Compile the actual H bridge closure: no replacement World or storage. */
#ifdef _WIN32
#undef _WIN32
#endif
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_capacity_bridge_main
#include "../geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT
#define CHECK(c,n) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",n);return 1;}}while(0)
int main(int argc,char **argv)
{
    if(argc!=2||strcmp(argv[1],"values"))return 2;
    CHECK(WORLD_MAX_TIMBERS==512,"capacity-host-admission-512");
    CHECK(sizeof(((World *)0)->wood.timbers)/sizeof(((World *)0)->wood.timbers[0])==512,"capacity-host-real-timbers-512");
    CHECK(sizeof(((World *)0)->wood.anchors)/sizeof(((World *)0)->wood.anchors[0])==512,"capacity-host-real-anchors-512");
    CHECK(STOP_FACE_MAX==3328&&WOOD_CONTACT_FACE_CAPACITY==3328,"capacity-host-contact-scratch-3328");
    CHECK(SPAN_CUT_MAX==3328&&WOOD_MEMBER_SPAN_CUT_CAPACITY==3328,"capacity-host-span-scratch-3328");
    CHECK(WORLD_MAX_BOUNDARIES==16&&WORLD_MAX_PLACEMENTS==16&&WORLD_MAX_RC==32,"capacity-host-other-resources-unchanged");
    return 0;
}
