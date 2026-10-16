/* Actual engineering transport and candidate: no test-side version adapter. */
#ifdef _WIN32
#undef _WIN32
#endif
#define GEOMETRY_BRIDGE_ENTRYPOINT geometry_bridge_main
#include "../geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT
#define CHECK(test,label) do{if(!(test)){fprintf(stderr,"ASSERT:%s\n",label);return 1;}}while(0)

static bool prepare(const char *path)
{
    memset(&g_world,0,sizeof g_world);g_definition_revision=0;history_clear();g_preview.ready=false;
    cmd_engineering_preview(path);return g_preview.ready&&g_preview.transaction;
}
static void confirm_version(void)
{char token[32];snprintf(token,sizeof token,"%u",g_preview.token);cmd_engineering_confirm(token);}
static bool typed_width(const World *world,int64_t width)
{
    const unsigned char key[]={1,'p'};GeoVersionFieldView field;
    return geo_versions_field(&world->geo.version_store,(GeoVersionIdentity){key,2,1},ENG_WIDTH,&field)==GEO_VERSION_OK&&
        field.field.kind==GEO_VERSION_QUANTITY&&field.field.value.num==width&&field.field.value.den==1&&field.field.value.unit==GEO_UNIT_LENGTH;
}
static int lifecycle(const char *path)
{
    CHECK(prepare(path)&&g_preview.valid,"valid-version-preview");AppWorldCandidate *owner=g_preview.transaction;
    CHECK(geo_versions_count(&g_world.geo.version_store)==0&&g_world.wood.engineering.material_count==0,"version-preview-live-unchanged");
    CHECK(geo_versions_count(&owner->before.geo.version_store)==0&&geo_versions_count(&owner->after.geo.version_store)==1,"actual-candidate-owns-version-store");
    CHECK(typed_width(&owner->after,100),"candidate-has-typed-width");
    GeoCandidate *core=app_candidate_core(owner->control);uint64_t id=geo_candidate_id(core);
    CHECK(geo_candidate_state(core)==GEO_CANDIDATE_SEALED,"version-candidate-sealed");
    confirm_version();CHECK(geo_candidate_state(core)==GEO_CANDIDATE_PUBLISHED&&geo_candidate_id(core)==id,"same-version-candidate-published");
    CHECK(g_definition_revision==1&&geo_versions_count(&g_world.geo.version_store)==1&&typed_width(&g_world,100),"complete-version-publication");
    CHECK(feed_line("version-witness",1,"undo",&g_world),"version-single-undo");
    CHECK(geo_versions_count(&g_world.geo.version_store)==0&&g_world.wood.engineering.material_count==0,"undo-restores-entire-version-root");
    CHECK(!feed_line("version-witness",1,"undo",&g_world),"version-one-history-entry");return 0;
}
static int tamper(const char *path,bool before)
{
    CHECK(prepare(path)&&g_preview.valid,"valid-version-preview");AppWorldCandidate *owner=g_preview.transaction;
    GeoCandidate *core=app_candidate_core(owner->control);
    if(before)owner->before.geo.version_store.count=1;
    else owner->after.geo.version_store.records[0].fields[0].value.num+=1;
    CHECK(geo_candidate_check(core,g_definition_revision,app_world_provider_stamp())==GEO_CANDIDATE_STATE_CHANGED,"actual-k-version-binding-rejects-tamper");
    confirm_version();CHECK(geo_candidate_state(core)!=GEO_CANDIDATE_PUBLISHED&&g_definition_revision==0&&
        geo_versions_count(&g_world.geo.version_store)==0&&g_world.wood.engineering.material_count==0,"tampered-version-never-published");return 0;
}
static int rollback(const char *path)
{
    CHECK(prepare(path)&&!g_preview.valid,"failed-version-batch");
    CHECK(geo_versions_count(&g_preview.transaction->after.geo.version_store)==1,"failed-batch-had-created-candidate-version");
    CHECK(geo_versions_count(&g_world.geo.version_store)==0&&g_world.wood.engineering.material_count==0&&g_definition_revision==0,"failed-version-batch-isolated");
    confirm_version();CHECK(geo_versions_count(&g_world.geo.version_store)==0&&g_definition_revision==0,"failed-version-confirm-rejected");
    CHECK(!feed_line("version-witness",1,"undo",&g_world),"failed-version-no-history");return 0;
}
static int authority(const char *path)
{
    CHECK(prepare(path)&&g_preview.valid,"valid-version-preview");confirm_version();
    CHECK(typed_width(&g_world,100),"published-k-width");
    EngMaterialVersion *cache=&g_world.wood.engineering.materials[0];cache->width=777;
    strcpy(cache->content,"stale");strcpy(cache->fingerprint,"stale");cache->archived=true;
    const EngMaterialVersion *value=eng_material(&g_world,"p",1);
    CHECK(value&&value->width==100&&value->archived&&!strcmp(value->thickness,"9"),"k-definition-replaces-stale-template-cache");
    CHECK(value->content[0]=='{'&&strlen(value->fingerprint)==64&&typed_width(&g_world,100),"k-owned-content-and-fields-authoritative");return 0;
}
int main(int argc,char **argv)
{
    if(argc!=3)return 2;
    if(!strcmp(argv[1],"lifecycle"))return lifecycle(argv[2]);
    if(!strcmp(argv[1],"before-tamper"))return tamper(argv[2],true);
    if(!strcmp(argv[1],"after-tamper"))return tamper(argv[2],false);
    if(!strcmp(argv[1],"rollback"))return rollback(argv[2]);
    if(!strcmp(argv[1],"authority"))return authority(argv[2]);
    return 2;
}
