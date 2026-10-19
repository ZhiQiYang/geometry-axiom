/* Includes the real model adapter; Python only renames its command main, adds
 * one final-World digest line, and for the reference build restores the
 * original adapter (per-line parse, freed fingerprint buffer, no block reuse).
 * The harness reports cost witnesses after the command: H candidates opened,
 * H candidate blocks allocated, and 1 MiB fingerprint buffers allocated. */
#ifdef _WIN32
#undef _WIN32
#endif
#include <stdlib.h>
static void *replay_count_malloc(size_t size);
static void *replay_count_calloc(size_t count,size_t size);
#define malloc replay_count_malloc
#define calloc replay_count_calloc
#include "../geometry-core/model_base.c"
#undef malloc
#undef calloc
static unsigned long long replay_world_blocks,replay_fingerprint_buffers;
static void *replay_count_malloc(size_t size)
{
    if(size==1024u*1024u+1u)++replay_fingerprint_buffers;
    return malloc(size);
}
static void *replay_count_calloc(size_t count,size_t size)
{
    if(count==1&&size==sizeof(AppWorldCandidate))++replay_world_blocks;
    return calloc(count,size);
}

int main(int argc,char **argv)
{
    uint64_t serial=g_app_candidate_serial;
    int status=replay_model_command_main(argc,argv);
    fflush(stdout);
    fprintf(stderr,"COST %llu %llu %llu\n",(unsigned long long)(g_app_candidate_serial-serial),
            replay_world_blocks,replay_fingerprint_buffers);
    return status;
}
