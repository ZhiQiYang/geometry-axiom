/* The original W fixture owns its real providers, output and nine ordered
 * graph assertions. Count only the proven collection-dependency site. */
#define main contact_original_main
#include "geo261_contact_sources_harness.c"
#undef main
static size_t remaining_collection_calls,remaining_collection_hashes;
static bool remaining_collection_active;
void remaining_collection_begin(void)
{remaining_collection_active=true;++remaining_collection_calls;}
void remaining_collection_end(void)
{remaining_collection_active=false;}
void remaining_hint_observe_hash(GeoSourceRef source)
{
    if(!remaining_collection_active)return;
    WoodContactSourceKind kind;uint64_t query,index;
    if(source.provider==CONTACT_TOKEN&&wood_contact_source_decode(&source,&kind,&query,&index)&&
        kind==WOOD_CONTACT_SOURCE_COLLECTION&&query==1&&index==0)++remaining_collection_hashes;
}
int main(int argc,char **argv)
{
    if(argc!=2||strcmp(argv[1],"collection-cache-edges"))return 2;
    int result=collection_cache_edges();if(result)return result;
    printf("{\"collection_calls\":%zu,\"collection_hashes\":%zu}\n",remaining_collection_calls,remaining_collection_hashes);
    CHECK("remaining-collection-four-real-feature-consumers",remaining_collection_calls==4&&!remaining_collection_active);
    CHECK("remaining-collection-hint-skips-node-hash",remaining_collection_hashes==0);
    printf("PASS %s\n",argv[1]);return 0;
}
