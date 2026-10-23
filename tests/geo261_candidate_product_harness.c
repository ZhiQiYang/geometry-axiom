/* The real host parser/preview/import handlers, linked to the isolated objects. */
#ifdef _WIN32
#undef _WIN32
#endif
#include <stdlib.h>
static void *replay_malloc(size_t size);
static void *default_replay_calloc(size_t count,size_t size);
#define calloc default_replay_calloc
#define malloc replay_malloc
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_bridge_main
#include "../geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT
#undef malloc
#undef calloc
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
    CHECK(geo_named_values_find(&owner->after.geo.named_values,"x")->value==600,"after-evaluated-value");
    CHECK(line("canvas-pos placement 1 17 29"),"presentation-edit");
    CHECK(g_preview.transaction==owner&&geo_candidate_sources(core)==sources,"preview-retains-owner");
    CHECK(confirm(),"confirm-sealed-candidate");
    CHECK(geo_candidate_state(core)==GEO_CANDIDATE_PUBLISHED&&geo_candidate_id(core)==id&&geo_eval_candidate_id(geo_candidate_sources(core))==id&&geo_eval_is_sealed(geo_candidate_sources(core)),"confirm-same-candidate-revalidated");
    CHECK(geo_candidate_evaluation_generation(core)==2,"confirm-full-revalidation");
    CHECK(g_definition_revision==revision+1&&geo_named_values_find(&g_world.geo.named_values,"x")->value==600,"one-complete-publication");
    CHECK(g_world.app.canvas_pos_count==1&&g_world.app.canvas_pos[0].x==17&&g_world.app.canvas_pos[0].y==29,"presentation-preserved");
    CHECK(line("undo")&&geo_named_values_find(&g_world.geo.named_values,"x")->value==500,"one-history-step");
    CHECK(g_world.app.canvas_pos_count==1&&g_world.app.canvas_pos[0].x==17,"undo-preserves-presentation");
    free(before);return 0;
}
static int tamper(const char *path,int which)
{
    CHECK(prepare(path),"setup");CHECK(preview(),"preview-valid");
    World *before=malloc(sizeof *before);CHECK(before,"memory");*before=g_world;
    if(which==0)++g_preview.transaction->after.wood.timbers[0].size_a;
    if(which==1)++g_preview.transaction->after.app.canvas_pos_count;
    if(which==2)++g_preview.transaction->before.wood.timbers[0].size_a;
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
    CHECK(!confirm()&&geo_named_values_find(&g_world.geo.named_values,"x")->value==500,"cancel-no-publication");return 0;
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
    CHECK(geo_named_values_find(&g_world.geo.named_values,"x")->value==500,"import-complete-root");return 0;
}
/* B witnesses extend this actual bridge harness; no alternate parser. */
static size_t replay_fail_size;
static unsigned replay_fail_remaining,replay_allocation_failures;
static void *replay_malloc(size_t size)
{
    if(replay_fail_remaining&&size==replay_fail_size){
        --replay_fail_remaining;++replay_allocation_failures;return NULL;
    }
    return malloc(size);
}
static bool replay_plain_parse(void *after,GeoEvalContext *sources,void *path)
{(void)sources;memset(after,0,sizeof(World));return parse_scene_file(path,after);}
static bool replay_has_guide_value(GeoEvalContext *sources,Coord expected)
{
    for(size_t i=0;i<geo_eval_node_count(sources);++i){GeoSourceNodeView node;
        if(geo_eval_node_at(sources,i,&node)&&node.source.provider==APP_SOURCE_GUIDE&&
           node.state==GEO_NODE_VALID&&node.value&&node.value->kind==GEO_SOURCE_AXIS_POSITION&&
           node.value->as.position.coordinate==expected)return true;
    }
    return false;
}
static int replay_load(const char *path,int mode)
{
    memset(&g_world,0,sizeof g_world);g_definition_revision=0;
    AppWorldCandidate *owner=app_world_candidate_create(&g_world);CHECK(owner,"replay-owner");
    World *live=malloc(sizeof *live);CHECK(live,"replay-live-memory");memcpy(live,&g_world,sizeof *live);
    uint64_t serial=g_app_candidate_serial;
    if(mode==2){replay_fail_size=sizeof(World);replay_fail_remaining=1;replay_allocation_failures=0;}
    GeoCandidateStatus status=app_world_candidate_evaluate(owner,mode==1?replay_plain_parse:app_scene_load_evaluate,(void*)path);
    CHECK(status==GEO_CANDIDATE_OK,"replay-loaded");
    CHECK(g_app_candidate_serial-serial==(mode?5:0),"file-replay-inner-candidate-cost");
    if(mode==2)CHECK(!replay_fail_remaining&&replay_allocation_failures==1,"optional-scratch-oom-original-path");
    CHECK(!memcmp(live,&g_world,sizeof *live),"file-replay-does-not-publish-during-parse");
    CHECK(!g_scene_file_replay,"file-replay-scope-restored");
    GeoEvalContext *sources=geo_candidate_sources(app_candidate_core(owner->control));
    CHECK(geo_eval_provider_count(sources)>=4&&geo_eval_node_count(sources)>=3,"file-replay-final-graph-retained");
    CHECK(replay_has_guide_value(sources,500),"file-replay-literal-guide-value");
    CHECK(app_world_candidate_seal(owner)&&geo_eval_is_sealed(sources),"file-replay-final-seal");
    CHECK(app_world_candidate_publish(owner,&g_world,false),"file-replay-one-publication");
    CHECK(geo_candidate_state(app_candidate_core(owner->control))==GEO_CANDIDATE_PUBLISHED,"file-replay-published-state");
    CHECK(!app_world_candidate_publish(owner,&g_world,false),"file-replay-no-second-publication");
    app_world_candidate_destroy(owner);free(live);return 0;
}
static int replay_i8a(const char *path,bool invalid)
{
    memset(&g_world,0,sizeof g_world);g_definition_revision=0;
    AppWorldCandidate *owner=app_world_candidate_create(&g_world);CHECK(owner,"i8a-replay-owner");
    uint64_t serial=g_app_candidate_serial;
    CHECK(app_world_candidate_evaluate(owner,app_scene_load_evaluate,(void*)path)==GEO_CANDIDATE_EVALUATION_FAILED,"file-replay-i8a-refused");
    CHECK(g_app_candidate_serial==serial+3,"file-replay-i8a-keeps-inner-owner");
    const char *message=scene_last_error();
    CHECK(strstr(message,invalid?"I8a: impact preview required (World unchanged);":"I8a: impact preview required; inspect preview, then confirm token (World unchanged)"),"file-replay-i8a-original-error");
    CHECK(geo_named_values_find(&owner->after.geo.named_values,"x")->value==500,"file-replay-i8a-keeps-prefix");
    CHECK(!g_world.wood.timber_count&&!g_definition_revision&&!g_preview.ready&&!g_preview.transaction,"file-replay-i8a-no-live-or-preview-leak");
    CHECK(!g_scene_file_replay,"file-replay-i8a-scope-restored");
    fprintf(stderr,"REPLAY_ERROR:%s\n",message);app_world_candidate_destroy(owner);return 0;
}
#define FRAME_CHECK(value,label) do{if(!(value)){fprintf(stderr,"ASSERT:%s\n",label);ok=false;goto cleanup;}}while(0)
static bool replay_frame(void *after,GeoEvalContext *sources,void *opaque)
{
    const char *which=opaque;World *world=after;bool ok=true;
    AppSceneFileReplay frame={g_active_app_candidate,sources,malloc(sizeof(World))};
    if(!frame.before)return false;
    AppSceneFileReplay *previous=g_scene_file_replay;bool previous_file=g_parsing_scene_file;
    ReferencePreview previous_preview=g_preview;memset(&g_preview,0,sizeof g_preview);
    g_scene_file_replay=&frame;g_parsing_scene_file=true;memset(world,0,sizeof *world);
    uint64_t serial=g_app_candidate_serial;
    FRAME_CHECK(feed_line("file-replay-witness",1,"spec x 500",world),"replay-frame-prefix");
    FRAME_CHECK(!app_candidate_evaluation_state(frame.owner->control)&&!geo_eval_provider_count(sources)&&!geo_eval_node_count(sources),"file-replay-line-graph-released");
    if(!strcmp(which,"rollback")){
        char text[]="datum 7 x spec:missing",*tokens[SCENE_MAX_TOKENS];
        int count=split_tokens(text,tokens,SCENE_MAX_TOKENS);
        FRAME_CHECK(count==4,"file-replay-datum-token-count");
        World *before=malloc(sizeof *before);FRAME_CHECK(before,"replay-rollback-memory");memcpy(before,world,sizeof *before);
        bool accepted=apply_scene_line("file-replay-witness",2,tokens,count,world);
        bool unchanged=!memcmp(before,world,sizeof *before);free(before);
        FRAME_CHECK(!accepted,"file-replay-partial-write-refused");
        FRAME_CHECK(unchanged,"file-replay-failed-line-byte-rollback");
        FRAME_CHECK(scene_last_error()[0],"file-replay-first-error-retained");
        FRAME_CHECK(g_app_candidate_serial==serial,"file-replay-failed-line-used-frame");
        fprintf(stderr,"REPLAY_ERROR:%s\n",scene_last_error());
    }else if(!strcmp(which,"lifetime")){
        FRAME_CHECK(feed_line("file-replay-witness",2,"surface 1 origin 0 0 0 u +x v +y outline 0,0 1000,0 1000,1000 0,1000",world),"replay-lifetime-surface");
        FRAME_CHECK(feed_line("file-replay-witness",3,"guide 1 1 v spec:x",world),"replay-lifetime-guide");
        FRAME_CHECK(feed_line("file-replay-witness",4,"preview spec x 900",world)&&g_preview.ready&&g_preview.valid,"replay-lifetime-real-preview-fallback");
        FRAME_CHECK(g_preview.transaction!=frame.owner,"replay-preview-has-own-owner");
        FRAME_CHECK(feed_line("file-replay-witness",5,"cancel-preview",world),"replay-lifetime-cancel-fallback");
        FRAME_CHECK(feed_line("file-replay-witness",6,"spec x 800",world),"replay-lifetime-final-fast-line");
        FRAME_CHECK(g_app_candidate_serial==serial+2,"file-replay-fast-fallback-fast-cost");
        FRAME_CHECK(!app_candidate_evaluation_state(frame.owner->control)&&!geo_eval_node_count(sources),"file-replay-no-stale-line-graph");
    }else if(!strcmp(which,"operation")){
        unsigned char before[sizeof frame.owner->operation];
        memset(&frame.owner->operation,0xa5,sizeof frame.owner->operation);
        frame.owner->operation.boundary_keyed=false;frame.owner->operation.boundary_id=91;
        frame.owner->operation.stagger_count=0;frame.owner->operation.stagger_steps=0;
        memset(frame.owner->operation.stagger_seal,0,sizeof frame.owner->operation.stagger_seal);
        memcpy(before,&frame.owner->operation,sizeof before);
        FRAME_CHECK(feed_line("file-replay-witness",2,"boundary 1 outline 0,0 1000,0 1000,1000 0,1000",world),"replay-keyed-boundary");
        FRAME_CHECK(feed_line("file-replay-witness",3,"boundary-vertex-keys 1 outer 1 2 3 4 next-key 5",world),"replay-keyed-keys");
        SpaceBoundarySurface boundary;char hash[65],command[512];
        FRAME_CHECK(app_boundary_read(world,1,&boundary),"replay-keyed-read");boundary_geometry_hash(&boundary,hash);
        snprintf(command,sizeof command,"boundary-keyed 1 geometry-hash %s outline 1:10,0 2:1010,0 3:1010,1000 4:10,1000",hash);
        FRAME_CHECK(feed_line("file-replay-witness",4,command,world),"replay-keyed-update");
        FRAME_CHECK(g_app_candidate_serial==serial,"file-replay-keyed-used-frame");
        FRAME_CHECK(!memcmp(before,&frame.owner->operation,sizeof before),"file-replay-operation-bytes-restored");
    }else{FRAME_CHECK(false,"unknown-replay-frame-case");}
cleanup:
    if(g_preview.transaction!=previous_preview.transaction)app_world_candidate_destroy(g_preview.transaction);
    g_preview=previous_preview;g_scene_file_replay=previous;g_parsing_scene_file=previous_file;free(frame.before);
    return ok&&world_revalidate(world);
}
static int replay_frame_case(const char *which)
{
    memset(&g_world,0,sizeof g_world);g_definition_revision=0;
    AppWorldCandidate *owner=app_world_candidate_create(&g_world);CHECK(owner,"replay-frame-owner");
    CHECK(app_world_candidate_evaluate(owner,replay_frame,(void*)which)==GEO_CANDIDATE_OK,"file-replay-frame-verdict");
    if(!strcmp(which,"lifetime"))CHECK(replay_has_guide_value(geo_candidate_sources(app_candidate_core(owner->control)),800),"file-replay-final-guide-is-not-cached-500");
    CHECK(app_world_candidate_seal(owner),"file-replay-frame-final-seal");
    app_world_candidate_destroy(owner);return 0;
}
typedef struct {bool allow_description,active_seen,ready_while_active;unsigned describe_calls;} ReplaySource;
static bool replay_source_describe(void *opaque,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    (void)ref;ReplaySource *source=opaque;++source->describe_calls;
    if(!source->allow_description)return false;
    memset(out,0,sizeof *out);out->kind=GEO_SOURCE_QUANTITY;out->unit=GEO_UNIT_LENGTH;return true;
}
static bool replay_source_evaluate(void *opaque,GeoEvalContext *ctx,const GeoSourceRef *ref,GeoSourceValue *out)
{
    (void)ctx;(void)ref;ReplaySource *source=opaque;source->active_seen=true;
    source->ready_while_active=app_scene_file_sources_ready(g_active_app_candidate);
    out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){17,1,GEO_UNIT_LENGTH};return true;
}
static bool replay_source_guards(void *after,GeoEvalContext *sources,void *opaque)
{
    (void)after;ReplaySource *source=opaque;
    GeoSourceProvider provider={900001,"replay-witness","replay-witness/1",source,replay_source_describe,replay_source_evaluate};
    unsigned char key=1;GeoSourceRef ref={900001,&key,sizeof key};
    if(!geo_eval_register(sources,&provider)||geo_eval_depend(sources,ref,GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)return false;
    if(app_scene_file_sources_ready(g_active_app_candidate)||source->describe_calls!=1){fprintf(stderr,"ASSERT:file-replay-describe-rejection\n");return false;}
    source->allow_description=true;GeoSourceValue value;
    if(geo_eval_source(sources,ref,GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||!source->active_seen||source->ready_while_active){fprintf(stderr,"ASSERT:file-replay-active-source-rejected\n");return false;}
    if(!app_scene_file_sources_ready(g_active_app_candidate)||value.as.quantity.num!=17){fprintf(stderr,"ASSERT:file-replay-completed-source-accepted\n");return false;}
    return true;
}
static int replay_source_case(void)
{
    memset(&g_world,0,sizeof g_world);g_definition_revision=0;ReplaySource source={0};
    AppWorldCandidate *owner=app_world_candidate_create(&g_world);CHECK(owner,"replay-source-owner");
    CHECK(app_world_candidate_evaluate(owner,replay_source_guards,&source)==GEO_CANDIDATE_OK,"file-replay-source-verdict");
    CHECK(app_world_candidate_seal(owner),"file-replay-source-final-seal");app_world_candidate_destroy(owner);return 0;
}

static int replay_standalone(const char *path)
{
    memset(&g_world,0,sizeof g_world);g_definition_revision=0;uint64_t serial=g_app_candidate_serial;
    CHECK(parse_scene_file(path,&g_world),"replay-standalone-parse");
    CHECK(g_app_candidate_serial==serial+6,"standalone-five-lines-plus-final-candidate");
    CHECK(!g_scene_file_replay&&geo_named_values_find(&g_world.geo.named_values,"x")->value==500,"standalone-original-parser-value");
    return 0;
}

/* Default replay witnesses keep the actual bridge and all original CHECKs. */
static bool default_observe_candidates,default_fail_candidate;
static uint64_t default_fail_revision,default_candidate_revisions[16];
static size_t default_candidate_count;
static unsigned default_candidate_failures;
static void *default_replay_calloc(size_t count,size_t size)
{
    if(count==1&&size==sizeof(AppWorldCandidate)){
        if(default_observe_candidates){
            if(default_candidate_count<16)default_candidate_revisions[default_candidate_count]=g_definition_revision;
            ++default_candidate_count;
        }
        if(default_fail_candidate&&g_definition_revision==default_fail_revision){
            default_fail_candidate=false;++default_candidate_failures;return NULL;
        }
    }
    return calloc(count,size);
}
static bool default_literals(const World *world)
{
    const GeoNamedValue *value=geo_named_values_find(&world->geo.named_values,"主支中線");
    return world->wood.timber_count==3&&world->wood.timbers[0].placed&&
        world->wood.timbers[1].placed&&world->wood.timbers[2].placed&&value&&value->value==500;
}
static int default_owned_candidate(const char *path,bool scratch_oom)
{
    CHECK(prepare(path),"default-fixture");g_definition_revision=41;
    World *before=malloc(sizeof *before);CHECK(before,"default-before-memory");memcpy(before,&g_world,sizeof *before);
    AppWorldCandidate *owner=app_world_candidate_create(&g_world);CHECK(owner,"default-owner");
    memset(&owner->operation,0xa5,sizeof owner->operation);owner->operation.boundary_keyed=false;owner->operation.boundary_id=91;
    owner->operation.stagger_count=0;owner->operation.stagger_steps=0;
    memset(owner->operation.stagger_seal,0,sizeof owner->operation.stagger_seal);
    unsigned char operation_bytes[sizeof owner->operation];memcpy(operation_bytes,&owner->operation,sizeof operation_bytes);
    AppReplacement operation={true,g_definition_revision};uint64_t revision=g_definition_revision,serial=g_app_candidate_serial;
    default_candidate_count=0;default_observe_candidates=true;
    if(scratch_oom){replay_fail_size=sizeof(World);replay_fail_remaining=1;replay_allocation_failures=0;}
    GeoCandidateStatus status=app_world_candidate_evaluate(owner,app_replace_evaluate,&operation);
    default_observe_candidates=false;
    CHECK(status==GEO_CANDIDATE_OK,"default-evaluation-succeeded");
    CHECK(g_app_candidate_serial-serial==(scratch_oom?9:2),"default-owned-inner-candidate-cost");
    CHECK(default_candidate_count==(scratch_oom?9:2),"default-real-candidate-allocation-count");
    if(scratch_oom){
        CHECK(replay_fail_remaining==0&&replay_allocation_failures==1,"default-optional-scratch-oom-fallback");
        for(size_t i=0;i<9;++i)CHECK(default_candidate_revisions[i]==revision+i,"default-fallback-per-line-revisions");
    }else{
        CHECK(default_candidate_revisions[0]==revision+5&&default_candidate_revisions[1]==revision+6,
              "default-spec-guide-keep-original-revisions");
    }
    CHECK(g_definition_revision==revision&&operation.completed_revision==revision+9,"default-callback-revision-restored");
    CHECK(!memcmp(before,&g_world,sizeof *before),"default-callback-live-unpublished");
    CHECK(!memcmp(operation_bytes,&owner->operation,sizeof operation_bytes),"default-operation-all-bytes-preserved");
    CHECK(!g_default_replay&&!g_scene_file_replay&&!g_parsing_scene_file,"default-scope-restored-before-final-graph");
    GeoCandidate *core=app_candidate_core(owner->control);GeoEvalContext *sources=geo_candidate_sources(core);
    CHECK(geo_candidate_state(core)==GEO_CANDIDATE_EVALUATED&&geo_candidate_evaluation_generation(core)==1,
          "default-one-outer-evaluation");
    CHECK(geo_eval_candidate_id(sources)==geo_candidate_id(core)&&geo_eval_base_revision(sources)==revision,
          "default-final-graph-has-original-outer-identity");
    CHECK(app_candidate_evaluation_state(owner->control)&&geo_eval_provider_count(sources)>=4&&geo_eval_node_count(sources)>=3,
          "default-final-graph-retained");
    CHECK(default_literals(&owner->after)&&replay_has_guide_value(sources,500),"default-literal-final-geometry");
    CHECK(app_world_candidate_seal(owner)&&geo_eval_is_sealed(sources),"default-final-seal");
    CHECK(app_world_candidate_publish(owner,&g_world,false),"default-single-publication");
    CHECK(geo_candidate_state(core)==GEO_CANDIDATE_PUBLISHED&&geo_candidate_sources(core)==sources&&default_literals(&g_world),
          "default-publishes-same-owner-and-complete-root");
    CHECK(!app_world_candidate_publish(owner,&g_world,false),"default-no-second-publication");
    printf("DEFAULT_FACTS inner=%llu completed=%llu restored=%llu generation=%llu\n",
        (unsigned long long)(g_app_candidate_serial-serial),(unsigned long long)operation.completed_revision,
        (unsigned long long)g_definition_revision,(unsigned long long)geo_candidate_evaluation_generation(core));
    app_world_candidate_destroy(owner);free(before);return 0;
}
static int default_standalone(const char *path)
{
    CHECK(prepare(path),"default-standalone-fixture");g_definition_revision=41;
    uint64_t serial=g_app_candidate_serial;
    CHECK(!g_active_app_candidate&&reference_default_world_owned(&g_world),"default-standalone-original-path");
    CHECK(g_app_candidate_serial==serial+9&&g_definition_revision==50,"default-standalone-nine-revisions-and-candidates");
    CHECK(default_literals(&g_world)&&!g_default_replay&&!g_scene_file_replay&&!g_parsing_scene_file,"default-standalone-no-frame-leak");
    return 0;
}
static int default_publication_policy(const char *path)
{
    CHECK(prepare(path),"default-policy-fixture");g_definition_revision=41;
    CHECK(line("spec default_unused 7")&&g_history.undo_count>0,"default-policy-existing-history");
    CHECK(line("canvas-pos placement 1 17 29")&&preview(),"default-policy-existing-presentation-and-preview");
    CHECK(line("history-begin")&&g_history.grouping,"default-policy-existing-history-group");
    uint64_t revision=g_definition_revision;uint32_t token=g_preview.token,preview_serial=g_preview_serial;
    AppWorldCandidate *preview_owner=g_preview.transaction;
    CHECK(world_default(&g_world),"default-policy-real-replacement");
    CHECK(g_definition_revision==revision+10,"default-policy-exact-nine-plus-publication");
    CHECK(default_literals(&g_world)&&g_world.app.canvas_pos_count==0,"default-policy-complete-root-replaced");
    CHECK(!g_history.undo_count&&!g_history.redo_count&&!g_history.grouping&&!g_history.group_dirty,
          "default-policy-clears-history-only-on-success");
    CHECK(!g_preview.ready&&g_preview.token==token&&g_preview_serial==preview_serial&&g_preview.transaction==preview_owner,
          "default-policy-preserves-original-preview-disposal-policy");
    CHECK(!confirm(),"default-policy-old-preview-cannot-confirm");
    revision=g_definition_revision;uint64_t serial=g_app_candidate_serial;
    CHECK(app_replace_world(&g_world,false),"default-policy-reset-success");
    CHECK(g_definition_revision==revision+1&&g_app_candidate_serial==serial+1,"default-policy-reset-single-revision-and-owner");
    CHECK(!g_world.wood.timber_count&&!world_boundary_count(&g_world)&&!geo_guides_count(&g_world.geo.guide_lines),
          "default-policy-reset-empty-definitions");
    CHECK(!g_history.undo_count&&!g_history.redo_count&&!g_history.grouping&&!g_preview.ready,
          "default-policy-reset-retains-history-preview-policy");
    return 0;
}
static int default_required_failure(const char *path,bool inner)
{
    CHECK(prepare(path),"default-failure-fixture");g_definition_revision=41;
    CHECK(line("spec default_unused 7")&&preview()&&line("history-begin"),"default-failure-existing-user-state");
    World *before=malloc(sizeof *before);CHECK(before,"default-failure-memory");memcpy(before,&g_world,sizeof *before);
    AppHistory history;ReferencePreview pending;
    memcpy(&history,&g_history,sizeof history);memcpy(&pending,&g_preview,sizeof pending);
    uint64_t revision=g_definition_revision;uint32_t preview_serial=g_preview_serial;
    snprintf(g_scene_last_error,sizeof g_scene_last_error,"prior-default-diagnostic");
    default_candidate_failures=0;default_fail_revision=revision+(inner?5:0);default_fail_candidate=true;
    bool accepted=world_default(&g_world);
    CHECK(!accepted&&!default_fail_candidate&&default_candidate_failures==1,"default-required-allocation-fails-real-owner");
    CHECK(!memcmp(before,&g_world,sizeof *before)&&g_definition_revision==revision,"default-failure-atomic-live-and-revision");
    CHECK(!memcmp(&history,&g_history,sizeof history)&&!memcmp(&pending,&g_preview,sizeof pending)&&g_preview_serial==preview_serial,
          "default-failure-keeps-history-and-pending-preview");
    CHECK(!g_default_replay&&!g_scene_file_replay&&!g_parsing_scene_file,"default-failure-restores-scope");
    CHECK(!strcmp(scene_last_error(),inner?"line 6: I32: candidate World allocation failed":"prior-default-diagnostic"),
          "default-failure-preserves-original-first-diagnostic");
    CHECK(line("history-abort")&&confirm(),"default-failure-original-preview-still-usable");
    revision=g_definition_revision;
    CHECK(world_default(&g_world)&&g_definition_revision==revision+10&&default_literals(&g_world),"default-failure-recovery-original-revision-policy");
    free(before);return 0;
}
static int default_program_guard(void)
{
    const char *lines[]={
        "surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000",
        "timber 1 27 33 role boundary", "place 1 on 1 at-face e0 +u +n",
        "timber 2 27 33 role boundary", "place 2 on 1 at-face e2 +u +n",
        "spec 主支中線 500", "guide 1 1 v spec:主支中線",
        "timber 3 27 33 role primary", "place 3 on 1 at-line guide 1 +v +n"
    };
    CHECK(app_default_replay_lines_match(lines,9),"default-original-program-recognized");
    CHECK(!app_default_replay_lines_match(lines,8),"default-truncated-program-rejected");
    lines[5]="spec 主支中線 600";
    CHECK(!app_default_replay_lines_match(lines,9),"default-changed-program-rejected");
    return 0;
}

int main(int argc,char **argv)
{
    if(argc!=3)return 2;
    if(!strcmp(argv[1],"default-cost"))return default_owned_candidate(argv[2],false);
    if(!strcmp(argv[1],"default-scratch-oom"))return default_owned_candidate(argv[2],true);
    if(!strcmp(argv[1],"default-standalone"))return default_standalone(argv[2]);
    if(!strcmp(argv[1],"default-policy"))return default_publication_policy(argv[2]);
    if(!strcmp(argv[1],"default-inner-oom"))return default_required_failure(argv[2],true);
    if(!strcmp(argv[1],"default-outer-oom"))return default_required_failure(argv[2],false);
    if(!strcmp(argv[1],"default-program-guard"))return default_program_guard();
    if(!strcmp(argv[1],"replay-cost"))return replay_load(argv[2],0);
    if(!strcmp(argv[1],"replay-unscoped"))return replay_load(argv[2],1);
    if(!strcmp(argv[1],"replay-scratch-oom"))return replay_load(argv[2],2);
    if(!strcmp(argv[1],"replay-standalone"))return replay_standalone(argv[2]);
    if(!strcmp(argv[1],"replay-i8a-valid"))return replay_i8a(argv[2],false);
    if(!strcmp(argv[1],"replay-i8a-invalid"))return replay_i8a(argv[2],true);
    if(!strcmp(argv[1],"replay-rollback"))return replay_frame_case("rollback");
    if(!strcmp(argv[1],"replay-lifetime"))return replay_frame_case("lifetime");
    if(!strcmp(argv[1],"replay-operation"))return replay_frame_case("operation");
    if(!strcmp(argv[1],"replay-source-guards"))return replay_source_case();
    if(!strcmp(argv[1],"lifecycle"))return lifecycle(argv[2]);
    if(!strcmp(argv[1],"wood-tamper"))return tamper(argv[2],0);
    if(!strcmp(argv[1],"host-tamper"))return tamper(argv[2],1);
    if(!strcmp(argv[1],"before-tamper"))return tamper(argv[2],2);
    if(!strcmp(argv[1],"revision"))return revision(argv[2]);
    if(!strcmp(argv[1],"cancel"))return cancelled(argv[2]);
    if(!strcmp(argv[1],"imports"))return imports(argv[2]);
    return 2;
}
