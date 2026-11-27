/* Test-only stdin injection for R14 candidate-query seal isolation.
 * Both the fixed baseline and P compile this file: every product query still
 * goes through the existing bridge main loop, without naming the new handler.
 * The two markers alter only sealed operation metadata in the test process.
 */
#include <stdio.h>
static char *r14_candidate_probe_fgets(char *text,int size,FILE *stream);
#define fgets r14_candidate_probe_fgets
#define GEOMETRY_BRIDGE_ENTRYPOINT r14_original_bridge_main
#include "../../geometry-web/web_bridge.c"
#undef GEOMETRY_BRIDGE_ENTRYPOINT
#undef fgets

static AppWorldCandidate *r14_probe_owner;
static uint32_t r14_probe_boundary_id;

static char *r14_candidate_probe_fgets(char *text,int size,FILE *stream)
{
    for (;;) {
        char *result=fgets(text,size,stream);
        if (!result || stream!=stdin) return result;
        bool tamper=!strcmp(text,"r14-test-seal-tamper\n");
        bool restore=!strcmp(text,"r14-test-seal-restore\n");
        if (!tamper && !restore) return result;
        bool ready=g_preview.ready && g_preview.valid && g_preview.transaction;
        bool applied=false;
        if (tamper && ready && !r14_probe_owner) {
            r14_probe_owner=g_preview.transaction;
            r14_probe_boundary_id=r14_probe_owner->operation.boundary_id;
            r14_probe_owner->operation.boundary_id^=1u;
            applied=true;
        } else if (restore && ready && r14_probe_owner==g_preview.transaction) {
            r14_probe_owner->operation.boundary_id=r14_probe_boundary_id;
            r14_probe_owner=NULL;
            applied=true;
        }
        printf("{\"ok\":%s,\"tampered\":%s,\"token\":%u,\"revision\":\"%llu\"}\n",
            applied?"true":"false",r14_probe_owner?"true":"false",g_preview.token,
            (unsigned long long)g_definition_revision);
        fflush(stdout);
    }
}

int main(void)
{
    return r14_original_bridge_main();
}
