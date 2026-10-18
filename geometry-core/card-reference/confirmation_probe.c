/* CR17: inject invalid downstream ONLY in this test TU, never a product command. */
/* The test supplies the real bridge with only its main symbol renamed.
 * GEO-261: the bridge names its entry point through GEOMETRY_BRIDGE_ENTRYPOINT
 * (as the GEO-261 harnesses do), bindings live in the K grid store, the preview
 * owns an AppWorldCandidate (after World) and history counters live in g_history. */
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_bridge_main
#include CR_BRIDGE_SOURCE
#undef GEOMETRY_BRIDGE_ENTRYPOINT

int main(int argc,char **argv)
{
    if(argc!=3)return 3;
    cmd_loadfile(argv[1]);
    if(!geo_grid_bindings_count(&g_world.geo.grid_store)){fputs("CR17 fixture lacks a real binding\n",stderr);return 3;}
    FILE *file=fopen(argv[2],"wb");if(!file)return 3;
    fprintf(file,"{\"schema\":\"engineering-transaction/1\",\"expectedRevision\":%llu,\"operations\":[{\"op\":\"swap-grid-card-reference\",\"id\":4}]}",(unsigned long long)g_definition_revision);
    fclose(file);cmd_engineering_preview(argv[2]);
    if(!g_preview.ready||!g_preview.valid){fputs("CR17 fixture preview was not valid\n",stderr);return 3;}
    World *before=malloc(sizeof *before);if(!before)return 3;*before=g_world;
    uint64_t revision=g_definition_revision;size_t undo=g_history.undo_count,redo=g_history.redo_count;bool dirty=g_history.group_dirty;
    /* The candidate was valid when previewed. Only the pending downstream is corrupted. */
    GeoGridStore *pending=&g_preview.transaction->after.geo.grid_store;
    GeoGridBinding corrupted=*geo_grid_bindings_at(pending,0);corrupted.boundary_id=UINT32_MAX;
    if(!geo_grid_bindings_put(pending,&corrupted)){fputs("CR17 could not inject the downstream fault\n",stderr);return 3;}
    char token[32];snprintf(token,sizeof token,"%u",g_preview.token);cmd_engineering_confirm(token);
    bool unchanged=!memcmp(before,&g_world,sizeof *before)&&revision==g_definition_revision&&undo==g_history.undo_count&&redo==g_history.redo_count&&dirty==g_history.group_dirty;
    free(before);
    if(!unchanged){fputs("CR17 CANDIDATE_LIFECYCLE: confirm failed to revalidate injected downstream; World/metadata/history changed\n",stderr);return 1;}
    puts("CR17 CANDIDATE_LIFECYCLE: injected invalid downstream rejected; full World, revision, dirty, undo/redo unchanged");
    return 0;
}
