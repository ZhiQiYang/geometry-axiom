/* Reuse all real H consumer/value/order assertions without changing them. */
#include <stddef.h>
static size_t remaining_definition_calls,remaining_pose_calls;
static size_t remaining_definition_hashes,remaining_pose_hashes;
#include "geo261_load_residual_harness.c"

void remaining_hint_observe_hash(GeoSourceRef source)
{
    if(!residual_second_consumer)return;
    if(source.provider==APP_SOURCE_WOOD_DEFINITION){
        WoodDefinitionKind kind;uint32_t id;
        if(wood_definition_source_decode(&source,&kind,&id)&&kind==WOOD_DEFINITION_MEMBER&&id==41)
            ++remaining_definition_hashes;
    }else if(source.provider==APP_SOURCE_MEMBER_POSE&&source.key_size==sizeof(uint32_t)&&source.key){
        uint32_t id;memcpy(&id,source.key,sizeof id);if(id==41)++remaining_pose_hashes;
    }
}
static bool remaining_host_case(const char *name)
{
    REQUIRE("remaining-host-original-assertions",cache_consumer_scenario(name));
    printf("{\"definition_calls\":%zu,\"definition_hashes\":%zu,\"pose_calls\":%zu,\"pose_hashes\":%zu}\n",
        remaining_definition_calls,remaining_definition_hashes,remaining_pose_calls,remaining_pose_hashes);
    if(!strcmp(name,"cache-definition")){
        REQUIRE("remaining-definition-two-real-warm-reads",remaining_definition_calls==2);
        REQUIRE("remaining-definition-hint-skips-node-hash",remaining_definition_hashes==0);
    }else{
        REQUIRE("remaining-pose-two-real-warm-reads",remaining_pose_calls==2);
        REQUIRE("remaining-pose-hint-skips-node-hash",remaining_pose_hashes==0);
    }
    return true;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"collection-reset")){
        if(!collection_reset_scenario())return 1;
        printf("PASS collection-reset\n");return 0;
    }
    if(strcmp(argv[1],"cache-definition")&&strcmp(argv[1],"cache-pose-kind"))return 2;
    if(!remaining_host_case(argv[1]))return 1;
    printf("PASS %s\n",argv[1]);return 0;
}
