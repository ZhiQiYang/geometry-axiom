/* The real host parser/preview/import handlers, linked to the isolated objects. */
#ifdef _WIN32
#undef _WIN32
#endif
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_bridge_main
#include "../geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT
#define CHECK(value,label) do{if(!(value)){fprintf(stderr,"ASSERT:%s\n",label);return 1;}}while(0)
static bool line(const char *value){return feed_line("candidate-witness",1,value,&g_world);}
static bool prepare(const char *path)
{
    memset(&g_world,0,sizeof g_world);g_definition_revision=0;
    if(!parse_scene_file(path,&g_world))return false;
    history_clear();g_preview.ready=false;return true;
}
static bool preview(void){return line("preview spec x 600")&&g_preview.ready&&g_preview.valid;}
static bool confirm(void){char text[64];snprintf(text,sizeof text,"confirm %u",g_preview.token);return line(text);}
static int lifecycle(const char *path)
{
    CHECK(prepare(path),"setup");World *before=malloc(sizeof *before);CHECK(before,"memory");*before=g_world;
    CHECK(preview(),"preview-valid");AppWorldCandidate *owner=g_preview.transaction;
    GeoCandidate *core=app_candidate_core(owner->control);GeoEvalContext *sources=geo_candidate_sources(core);
    uint64_t id=geo_candidate_id(core),revision=g_definition_revision;
    CHECK(geo_candidate_evaluation_generation(core)==1,"preview-one-evaluation");
    CHECK(sources&&geo_eval_is_sealed(sources),"same-resolver-sealed");
    CHECK(geo_eval_candidate_id(sources)==id&&geo_eval_base_revision(sources)==revision,"same-resolver-identity");
    CHECK(geo_eval_provider_count(sources)>=4&&geo_eval_node_count(sources)>0,"actual-provider-graph");
    CHECK(!memcmp(before,&g_world,sizeof *before),"preview-no-live-mutation");
    CHECK(geo_named_values_find(&owner->after.named_values,"x")->value==600,"after-evaluated-value");
    CHECK(line("canvas-pos placement 1 17 29"),"presentation-edit");
    CHECK(g_preview.transaction==owner&&geo_candidate_sources(core)==sources,"preview-retains-owner");
    CHECK(confirm(),"confirm-sealed-candidate");
    CHECK(geo_candidate_state(core)==GEO_CANDIDATE_PUBLISHED&&geo_candidate_id(core)==id&&geo_eval_candidate_id(geo_candidate_sources(core))==id&&geo_eval_is_sealed(geo_candidate_sources(core)),"confirm-same-candidate-revalidated");
    CHECK(geo_candidate_evaluation_generation(core)==2,"confirm-full-revalidation");
    CHECK(g_definition_revision==revision+1&&geo_named_values_find(&g_world.named_values,"x")->value==600,"one-complete-publication");
    CHECK(g_world.canvas_pos_count==1&&g_world.canvas_pos[0].x==17&&g_world.canvas_pos[0].y==29,"presentation-preserved");
    CHECK(line("undo")&&geo_named_values_find(&g_world.named_values,"x")->value==500,"one-history-step");
    CHECK(g_world.canvas_pos_count==1&&g_world.canvas_pos[0].x==17,"undo-preserves-presentation");
    free(before);return 0;
}
static int tamper(const char *path,int which)
{
    CHECK(prepare(path),"setup");CHECK(preview(),"preview-valid");
    World *before=malloc(sizeof *before);CHECK(before,"memory");*before=g_world;
    if(which==0)++g_preview.transaction->after.timbers[0].size_a;
    if(which==1)++g_preview.transaction->after.canvas_pos_count;
    if(which==2)++g_preview.transaction->before.timbers[0].size_a;
    CHECK(!confirm(),"full-snapshot-tamper-rejected");
    CHECK(!memcmp(before,&g_world,sizeof *before),"tamper-does-not-publish");
    free(before);return 0;
}
static int revision(const char *path)
{
    CHECK(prepare(path)&&preview(),"preview-valid");World *before=malloc(sizeof *before);CHECK(before,"memory");*before=g_world;
    /* Defeat only the old H token check. The actual K seal must still reject. */
    ++g_definition_revision;g_preview.revision=g_definition_revision;
    CHECK(!confirm(),"kernel-revision-gate");CHECK(!memcmp(before,&g_world,sizeof *before),"stale-root-unchanged");
    free(before);return 0;
}
static int cancelled(const char *path)
{
    CHECK(prepare(path)&&preview(),"preview-valid");AppWorldCandidate *owner=g_preview.transaction;
    CHECK(line("cancel-preview"),"cancel-success");CHECK(geo_candidate_state(app_candidate_core(owner->control))==GEO_CANDIDATE_DISCARDED,"cancel-terminal");
    CHECK(!confirm()&&geo_named_values_find(&g_world.named_values,"x")->value==500,"cancel-no-publication");return 0;
}
static int imports(const char *path)
{
    CHECK(prepare(path)&&preview(),"preview-valid");AppWorldCandidate *preview_owner=g_preview.transaction;
    GeoCandidate *preview_core=app_candidate_core(preview_owner->control);
    GeoEvalContext *preview_sources=geo_candidate_sources(preview_core);
    CHECK(scene_load_prepare(path),"import-prepared");
    CHECK(g_preview.transaction==preview_owner&&geo_candidate_sources(preview_core)==preview_sources,"import-preserves-existing-preview");
    cmd_engineering_validate(path);
    CHECK(g_preview.transaction==preview_owner&&geo_candidate_sources(preview_core)==preview_sources,"validation-preserves-existing-preview");
    CHECK(confirm(),"preview-still-confirmable");
    CHECK(scene_load_prepare(path),"second-import-prepared");GeoCandidate *core=app_candidate_core(g_load_transaction->control);
    GeoEvalContext *sources=geo_candidate_sources(core);uint64_t id=geo_candidate_id(core);char token[32];snprintf(token,sizeof token,"%u",g_load_token);
    cmd_load_confirm(token);
    CHECK(geo_candidate_state(core)==GEO_CANDIDATE_PUBLISHED&&geo_candidate_sources(core)==sources&&geo_candidate_id(core)==id,"import-publishes-same-candidate");
    CHECK(geo_named_values_find(&g_world.named_values,"x")->value==500,"import-complete-root");return 0;
}
int main(int argc,char **argv)
{
    if(argc!=3)return 2;
    if(!strcmp(argv[1],"lifecycle"))return lifecycle(argv[2]);
    if(!strcmp(argv[1],"wood-tamper"))return tamper(argv[2],0);
    if(!strcmp(argv[1],"host-tamper"))return tamper(argv[2],1);
    if(!strcmp(argv[1],"before-tamper"))return tamper(argv[2],2);
    if(!strcmp(argv[1],"revision"))return revision(argv[2]);
    if(!strcmp(argv[1],"cancel"))return cancelled(argv[2]);
    if(!strcmp(argv[1],"imports"))return imports(argv[2]);
    return 2;
}
