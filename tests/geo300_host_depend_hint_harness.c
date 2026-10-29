/* Reuse the real load-residual fixture, consumers and all existing ordered
 * graph/value assertions. Its main is renamed only in the build's copy. */
#include <stddef.h>
static size_t h_hint_placement_hashes,h_hint_footprint_hashes;
static size_t h_hint_placement_calls,h_hint_footprint_calls;
#include "geo261_load_residual_harness.c"

/* Called by the privately instrumented real K node-hash function. Count only
 * the second real consumer, after the first consumer naturally warmed H/K. */
void h_hint_observe_hash(GeoSourceRef source)
{
    if(!residual_second_consumer)return;
    if(source.provider==APP_SOURCE_WOOD_DEFINITION){
        WoodDefinitionKind kind;uint32_t id;
        if(wood_definition_source_decode(&source,&kind,&id)&&kind==WOOD_DEFINITION_PLACEMENT&&id==41)
            ++h_hint_placement_hashes;
    }else if(source.provider==APP_SOURCE_MEMBER_POSE&&source.key_size==sizeof(uint32_t)&&source.key){
        uint32_t id;memcpy(&id,source.key,sizeof id);if(id==41)++h_hint_footprint_hashes;
    }
}
static bool h_hint_case(const char *name)
{
    h_hint_placement_hashes=h_hint_footprint_hashes=h_hint_placement_calls=h_hint_footprint_calls=0;
    REQUIRE("host-hint-real-original-consumers",cache_consumer_scenario(name));
    printf("{\"placement_calls\":%zu,\"placement_hashes\":%zu,\"footprint_calls\":%zu,\"footprint_hashes\":%zu}\n",
        h_hint_placement_calls,h_hint_placement_hashes,h_hint_footprint_calls,h_hint_footprint_hashes);
    REQUIRE("host-placement-hint-real-two-warm-reads",h_hint_placement_calls==2);
    REQUIRE("host-placement-hint-warm-reads-skip-node-hash",h_hint_placement_hashes==0);
    if(strcmp(name,"cache-anchor")){
        REQUIRE("host-footprint-hint-real-two-warm-reads",h_hint_footprint_calls==2);
        REQUIRE("host-footprint-hint-warm-reads-skip-node-hash",h_hint_footprint_hashes==0);
    }
    return true;
}
int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(strcmp(argv[1],"cache-anchor")&&strcmp(argv[1],"cache-contact")&&strcmp(argv[1],"cache-footprint-source"))return 2;
    if(!h_hint_case(argv[1]))return 1;
    printf("PASS %s\n",argv[1]);return 0;
}
