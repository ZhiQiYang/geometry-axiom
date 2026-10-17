#define main geometry_program_main
#include GEOMETRY_SOURCE
#undef main

static World actual_world, before_world;
static bool issue(const char *text)
{
    char line[SCENE_MAX_LINE], *tokens[SCENE_MAX_TOKENS];
    snprintf(line,sizeof line,"%s",text);
    int n=split_tokens(line,tokens,SCENE_MAX_TOKENS);
    return apply_interactive_tokens("world-byte-probe",1,tokens,n,&actual_world);
}
int main(void)
{
    int failures=0;
    for (int strip=0;strip<2;++strip) for (int prior=0;prior<2;++prior) {
        actual_world=(World){0};history_clear();
        if (!issue("surface 1 origin 0 0 0 u +x v +y outline 0,10 10,10 10,0 20,0 20,10 30,10 30,0 40,0 40,20 20,20 20,30 10,30 10,20 0,20")) return 2;
        if (!issue(strip?"beam 1 along x from -10 to 50 at 15 width 10 depth 10 top 0":"column 1 at -10 10 size 60 10 z 0 100")) return 2;
        if (prior&&!issue("column 2 at 12 2 size 4 4 z 0 100")) return 2;
        memcpy(&before_world,&actual_world,sizeof actual_world);
        const char *apply=strip?(prior?"apply-proj 1 c2 b1 cut-strip":"apply-proj 1 b1 cut-strip"):(prior?"apply-proj 1 c2 c1":"apply-proj 1 c1");
        bool accepted=issue(apply);
        bool same=memcmp(&before_world,&actual_world,sizeof actual_world)==0;
        printf("WORLD_BYTE_RESULT {\"strip\":%d,\"prior_hole\":%d,\"accepted\":%s,\"world_bytes_equal\":%s,\"world_bytes\":%zu}\n",strip,prior,accepted?"true":"false",same?"true":"false",sizeof actual_world);
        failures+=accepted||!same;
    }
    return failures?1:0;
}
