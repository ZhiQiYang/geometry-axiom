/* Read the actual bridge candidate, ordered facts and confirm implementation. */
#ifdef _WIN32
#undef _WIN32
#endif
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_bridge_main
#include "../geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT
#define CHECK(c,n) do{if(!(c)){fprintf(stderr,"ASSERT:%s\n",n);return 1;}}while(0)

static uint32_t ordered_system_id;
static char *ordered_dump(const World *world)
{
    FILE *file=tmpfile();if(!file)return NULL;world_dump_dsl(world,file);
    if(fflush(file)||fseek(file,0,SEEK_END)){fclose(file);return NULL;}
    long size=ftell(file);if(size<0||fseek(file,0,SEEK_SET)){fclose(file);return NULL;}
    char *text=malloc((size_t)size+1);if(!text){fclose(file);return NULL;}
    if(fread(text,1,(size_t)size,file)!=(size_t)size){free(text);fclose(file);return NULL;}
    text[size]=0;fclose(file);return text;
}
static bool ordered_empty(const AppWorldCandidate *owner)
{return owner&&!owner->stagger_facts&&!owner->stagger_capacity&&!owner->operation.stagger_count&&!owner->operation.stagger_steps;}
static int ordered_prepare(const char *fixture)
{
    memset(&g_world,0,sizeof g_world);g_definition_revision=0;
    CHECK(parse_scene_file(fixture,&g_world),"ordered-legacy-fixture-load");history_clear();
    CHECK(g_definition_revision==0,"ordered-fixture-replay-is-not-submission");
    const GeoGridSystem *system=NULL;
    for(size_t i=0;i<geo_grid_systems_count(&g_world.geo.grid_store);++i){
        const GeoGridSystem *candidate=geo_grid_systems_at(&g_world.geo.grid_store,i);
        if(candidate->axis[0].stagger_set&&candidate->axis[1].stagger_set&&candidate->axis[0].parameters[5].set){
            CHECK(!system,"ordered-fixture-has-one-legacy-parameter-system");system=candidate;
        }
    }
    CHECK(system&&system->axis[0].stagger_set&&system->axis[1].stagger_set&&
        system->axis[0].stagger==400&&system->axis[1].stagger==300&&
        system->axis[0].parameters[5].set&&system->axis[0].parameters[5].parameter_id==901&&
        system->axis[0].parameters[5].field_id==1,"ordered-fixture-declares-independent-baseline");
    ordered_system_id=system->id;return 0;
}
static int ordered_preview(const char *request)
{
    cmd_engineering_preview(request);
    CHECK(g_preview.ready&&g_preview.valid&&g_preview.engineering_batch&&g_preview.transaction,
        "ordered-card-then-unbind-preview-valid");return 0;
}
static int ordered_facts(void)
{
    const AppWorldCandidate *owner=g_preview.transaction;const WoodGridStaggerFact *f=owner->stagger_facts;
    CHECK(owner->operation.stagger_count==2&&owner->operation.stagger_steps==2&&f,
        "ordered-two-steps-two-source-observations");
    CHECK(f[0].system_id==ordered_system_id&&f[1].system_id==ordered_system_id&&f[0].axis==0&&f[1].axis==0&&
        f[0].order==1&&f[1].order==2,"ordered-facts-retain-original-operation-order");
    CHECK(f[0].before.set&&f[0].before.resolved&&f[0].before.source.set&&
        f[0].before.source.parameter_id==901&&f[0].before.source.field_id==1&&f[0].before.value==400&&
        f[0].after.set&&f[0].after.resolved&&f[0].after.source.set&&f[0].after.value==500,
        "ordered-card-delta-comes-from-present-reference");
    CHECK(f[1].before.set&&f[1].before.resolved&&f[1].before.source.set&&f[1].before.value==500&&
        f[1].after.set&&f[1].after.resolved&&!f[1].after.source.set&&f[1].after.value==500,
        "ordered-unbind-records-current-value-not-original-cache");
    char facts_hash[65],operation_hash[65];
    geo_sha256(f,2*sizeof *f,facts_hash);geo_sha256(&owner->operation,sizeof owner->operation,operation_hash);
    CHECK(!strcmp(facts_hash,owner->operation.stagger_seal)&&!strcmp(operation_hash,owner->operation_seal),
        "ordered-facts-and-metadata-have-the-original-operation-seal");
    CHECK(app_world_candidate_current(owner,&g_world),"ordered-preview-seal-is-current");
    GeoCandidate *core=app_candidate_core(owner->control);
    CHECK(geo_candidate_base_revision(core)==g_definition_revision&&
        geo_candidate_check(core,g_definition_revision,app_world_provider_stamp())==GEO_CANDIDATE_OK,
        "ordered-facts-belong-to-original-revision-and-provider");
    ReferenceEval *evaluation=app_candidate_evaluation_state(owner->control);
    CHECK(evaluation&&evaluation->world==&owner->after&&
        evaluation->sources==geo_candidate_sources(core)&&geo_eval_is_sealed(evaluation->sources),
        "ordered-facts-and-providers-share-one-candidate");return 0;
}
static int ordered_tamper(void)
{
    AppWorldCandidate *owner=g_preview.transaction;CHECK(ordered_facts()==0,"ordered-baseline-facts");
    owner->stagger_facts[0].after.value^=1;
    CHECK(!app_world_candidate_current(owner,&g_world),"ordered-facts-byte-tamper-rejected");
    owner->stagger_facts[0].after.value^=1;
    CHECK(app_world_candidate_current(owner,&g_world),"ordered-restored-facts-seal-current");
    owner->stagger_facts[1].order+=1;
    CHECK(!app_world_candidate_current(owner,&g_world),"ordered-facts-order-tamper-rejected");
    owner->stagger_facts[1].order-=1;
    --owner->operation.stagger_count;
    CHECK(!app_world_candidate_current(owner,&g_world),"ordered-facts-count-tamper-rejected");
    ++owner->operation.stagger_count;++owner->operation.stagger_steps;
    CHECK(!app_world_candidate_current(owner,&g_world),"ordered-facts-step-count-tamper-rejected");
    --owner->operation.stagger_steps;
    CHECK(app_world_candidate_current(owner,&g_world),"ordered-restored-metadata-seal-current");
    GeoCandidate *core=app_candidate_core(owner->control);
    CHECK(geo_candidate_check(core,g_definition_revision+1,app_world_provider_stamp())==GEO_CANDIDATE_REVISION_CHANGED,
        "ordered-wrong-revision-is-rejected");
    CHECK(geo_candidate_check(core,g_definition_revision,"ordered-wrong-provider") ==GEO_CANDIDATE_PROVIDER_CHANGED,
        "ordered-wrong-provider-is-rejected");return 0;
}
static int ordered_confirm_evidence(void)
{
    AppWorldCandidate *owner=g_preview.transaction;CHECK(ordered_facts()==0,"ordered-baseline-facts");
    WoodGridStaggerFact saved[2];memcpy(saved,owner->stagger_facts,sizeof saved);
    WoodGridStaggerFact *address=owner->stagger_facts;GeoCandidate *core=app_candidate_core(owner->control);
    uint64_t id=geo_candidate_id(core),generation=geo_candidate_evaluation_generation(core),revision=g_definition_revision;
    CHECK(app_world_candidate_revalidate(owner,&g_world),"ordered-confirm-retains-evidence");
    CHECK(g_preview.transaction==owner&&app_candidate_core(owner->control)==core&&geo_candidate_id(core)==id&&
        geo_candidate_evaluation_generation(core)==generation+1&&g_definition_revision==revision,
        "ordered-confirm-revalidates-same-candidate-and-revision");
    CHECK(owner->stagger_facts==address&&owner->operation.stagger_count==2&&owner->operation.stagger_steps==2&&
        !memcmp(saved,owner->stagger_facts,sizeof saved),"ordered-confirm-consumes-identical-ordered-facts");
    CHECK(ordered_facts()==0,"ordered-confirm-resealed-same-facts");return 0;
}
static int ordered_cleanup(const char *kind,const char *before)
{
    AppWorldCandidate *owner=g_preview.transaction;uint64_t revision=g_definition_revision;
    char token[32];snprintf(token,sizeof token,"%u",g_preview.token);
    if(!strcmp(kind,"cancel"))cmd_engineering_cancel(token);
    else if(!strcmp(kind,"stale")){++g_definition_revision;cmd_engineering_confirm(token);}
    else return 2;
    CHECK(!g_preview.ready&&ordered_empty(owner),"ordered-cancel-or-stale-clears-retained-evidence");
    CHECK(geo_candidate_state(app_candidate_core(owner->control))==GEO_CANDIDATE_DISCARDED,
        "ordered-cancel-or-stale-discards-candidate");
    char *after=ordered_dump(&g_world);CHECK(after&&!strcmp(before,after),"ordered-cancel-or-stale-keeps-live-world");free(after);
    CHECK(g_definition_revision==revision+(!strcmp(kind,"stale")?1:0),"ordered-cancel-or-stale-does-not-publish");return 0;
}
static int ordered_publish(const char *before,const char *saved_path)
{
    AppWorldCandidate *owner=g_preview.transaction;uint64_t revision=g_definition_revision;
    char token[32];snprintf(token,sizeof token,"%u",g_preview.token);cmd_engineering_confirm(token);
    CHECK(!g_preview.ready&&geo_candidate_state(app_candidate_core(owner->control))==GEO_CANDIDATE_PUBLISHED&&
        g_definition_revision==revision+1,"ordered-success-confirms-and-publishes");
    CHECK(ordered_empty(owner),"ordered-success-clears-retained-evidence");
    const GeoGridSystem *system=geo_grid_systems_find(&g_world.geo.grid_store,ordered_system_id);
    CHECK(system&&!system->axis[0].parameters[5].set&&system->axis[0].stagger==500&&system->axis[1].stagger==300,
        "ordered-published-source-and-values");
    char *after=ordered_dump(&g_world);CHECK(after&&strcmp(before,after),"ordered-public-definition-changed");
    CHECK(!strstr(after,"stagger-facts")&&!strstr(after,"ordered-candidate-step")&&!strstr(after,"stagger_seal"),
        "ordered-evidence-never-serializes");
    CHECK(history_undo(&g_world),"ordered-published-history-undo");char *undone=ordered_dump(&g_world);
    CHECK(undone&&!strcmp(before,undone),"ordered-history-restores-legacy-definition-bytes");free(undone);
    CHECK(history_redo(&g_world),"ordered-published-history-redo");char *redone=ordered_dump(&g_world);
    CHECK(redone&&!strcmp(after,redone),"ordered-history-restores-final-definition-bytes");free(redone);
    FILE *file=fopen(saved_path,"wb");CHECK(file,"ordered-roundtrip-output-file");
    CHECK(fwrite(after,1,strlen(after),file)==strlen(after)&&!fclose(file),"ordered-roundtrip-save-bytes");
    World *reopened=calloc(1,sizeof *reopened);CHECK(reopened,"ordered-roundtrip-world-memory");
    CHECK(parse_scene_file(saved_path,reopened),"ordered-roundtrip-replay");char *replayed=ordered_dump(reopened);
    CHECK(replayed&&!strcmp(after,replayed),"ordered-roundtrip-dump-is-byte-identical");free(replayed);free(reopened);
    AppWorldCandidate *fresh=app_world_candidate_create(&g_world);CHECK(ordered_empty(fresh),"ordered-history-and-new-candidate-have-no-evidence");
    app_world_candidate_destroy(fresh);free(after);return 0;
}
static int ordered_dispose(void)
{
    AppWorldCandidate *owner=g_preview.transaction;CHECK(owner->stagger_facts,"ordered-dispose-has-owned-evidence");
    g_app_world_candidate_pool_enabled=true;size_t count=g_app_world_candidate_pool_count;
    CHECK(count<APP_WORLD_CANDIDATE_POOL_MAX,"ordered-dispose-pool-slot");
    g_preview.transaction=NULL;g_preview.ready=false;app_world_candidate_destroy(owner);
    CHECK(g_app_world_candidate_pool_count==count+1&&g_app_world_candidate_pool[count]==owner&&ordered_empty(owner),
        "ordered-dispose-clears-evidence-before-pooling");return 0;
}
static int ordered_archive(const char *path,const char *before,bool preview_only)
{
    FILE *file=fopen(path,"rb");CHECK(file,"ordered-archive-command-file");
    char command[SCENE_MAX_LINE];size_t size=fread(command,1,sizeof command-1,file);fclose(file);command[size]=0;
    CHECK(size&&size<sizeof command-1,"ordered-archive-command-capacity");
    (void)feed_line("ordered-archive",1,command,&g_world);
    CHECK(g_preview.ready&&g_preview.transaction&&!g_preview.engineering_batch,"ordered-archive-has-retained-preview");
    if(preview_only){
        CHECK(!g_preview.valid,"ordered-archive-preview-rejects-value-change");
        CHECK(g_preview.issue_count&&strstr(g_preview.issues[0].actual,"I24")&&
            strstr(g_preview.issues[0].actual,"先在同一筆編輯裡移除一軸"),"ordered-archive-preview-pins-reason");
    }
    char confirm[64];snprintf(confirm,sizeof confirm,"confirm %u",g_preview.token);
    bool confirmed=feed_line("ordered-archive",2,confirm,&g_world);
    CHECK(!confirmed,"ordered-confirmation-baseline-still-rejects");
    char *after=ordered_dump(&g_world);CHECK(after&&!strcmp(before,after)&&g_definition_revision==0,
        "ordered-rejected-confirmation-keeps-world-and-revision");free(after);return 0;
}
int main(int argc,char **argv)
{
    if(argc!=7)return 2;const char *kind=argv[1];
    int result=ordered_prepare(argv[2]);if(result)return result;
    char *before=ordered_dump(&g_world);CHECK(before,"ordered-baseline-dump");
    if(!strcmp(kind,"archive-depth")||!strcmp(kind,"archive-preview")){
        result=ordered_archive(argv[6],before,!strcmp(kind,"archive-preview"));if(result)return result;
    }else if(!strcmp(kind,"failure")){
        cmd_engineering_preview(argv[4]);CHECK(g_preview.ready&&!g_preview.valid&&g_preview.transaction,
            "ordered-invalid-source-switch-is-rejected");
        CHECK(ordered_empty(g_preview.transaction),"ordered-failed-preview-clears-evidence");
        char *after=ordered_dump(&g_world);CHECK(after&&!strcmp(before,after)&&g_definition_revision==0,
            "ordered-failed-preview-keeps-world-and-revision");free(after);
    }else{
        result=ordered_preview(argv[3]);if(result)return result;
        char *during=ordered_dump(&g_world);CHECK(during&&!strcmp(before,during)&&g_definition_revision==0,
            "ordered-preview-keeps-live-definition-and-revision");free(during);
        if(!strcmp(kind,"sealed"))result=ordered_facts();
        else if(!strcmp(kind,"tamper"))result=ordered_tamper();
        else if(!strcmp(kind,"confirm-evidence"))result=ordered_confirm_evidence();
        else if(!strcmp(kind,"cancel")||!strcmp(kind,"stale"))result=ordered_cleanup(kind,before);
        else if(!strcmp(kind,"success"))result=ordered_publish(before,argv[5]);
        else if(!strcmp(kind,"dispose"))result=ordered_dispose();
        else return 2;
        if(result)return result;
    }
    free(before);printf("PASS %s\n",kind);return 0;
}
