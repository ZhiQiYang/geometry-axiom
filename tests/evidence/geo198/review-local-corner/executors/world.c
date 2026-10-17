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
    const SurfacePoint2 vertices[12]={{0,10},{10,10},{10,0},{20,0},{20,10},{30,10},
        {30,20},{20,20},{20,40},{10,40},{10,20},{0,20}};
    for(int variant=0;variant<16;++variant)for(int strip=0;strip<2;++strip)for(int prior=0;prior<2;++prior){
        char scene[SCENE_MAX_LINE],command[256];
        actual_world=(World){0};history_clear();
        snprintf(scene,sizeof scene,"surface 1 origin 0 0 0 u +x v +y outline");
        int shift=(variant&4)?11:0,offset=(variant&8)?-50:0;
        for(int i=0;i<12;++i){
            int at=(variant&1)?(shift+12-i)%12:(shift+i)%12;
            SurfacePoint2 p=vertices[at];
            snprintf(command,sizeof command," %lld,%lld",(long long)((variant&2)?p.v:p.u)+offset,
                     (long long)((variant&2)?p.u:p.v)+offset);
            strncat(scene,command,sizeof scene-strlen(scene)-1);
        }
        if(!issue(scene))return 2;
        if(strip)snprintf(command,sizeof command,"beam 1 along %s from %d to %d at %d width 10 depth 10 top 0",
                          (variant&2)?"x":"y",10+offset,30+offset,15+offset);
        else snprintf(command,sizeof command,"column 1 at %d %d size %d %d z 0 100",10+offset,10+offset,
                      (variant&2)?20:10,(variant&2)?10:20);
        if(!issue(command))return 2;
        if(prior){snprintf(command,sizeof command,"column 2 at %d %d size 4 4 z 0 100",
                          ((variant&2)?2:12)+offset,((variant&2)?12:2)+offset);if(!issue(command))return 2;}
        memcpy(&before_world,&actual_world,sizeof actual_world);
        const char *apply=strip?(prior?"apply-proj 1 c2 b1 cut-strip":"apply-proj 1 b1 cut-strip"):
                               (prior?"apply-proj 1 c2 c1":"apply-proj 1 c1");
        bool accepted=issue(apply),same=memcmp(&before_world,&actual_world,sizeof actual_world)==0;
        printf("WORLD_BYTE_RESULT {\"variant\":%d,\"strip\":%d,\"prior_hole\":%d,\"accepted\":%s,\"world_bytes_equal\":%s,\"world_bytes\":%zu}\n",
               variant,strip,prior,accepted?"true":"false",same?"true":"false",sizeof actual_world);
        failures+=accepted||!same;
    }
    return failures?1:0;
}
