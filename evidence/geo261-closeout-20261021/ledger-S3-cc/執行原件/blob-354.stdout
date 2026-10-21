static void sp_json_region(SurfaceRegion2 r)
{printf("[%lld,%lld,%lld,%lld]",(long long)r.min_u,(long long)r.min_v,(long long)r.max_u,(long long)r.max_v);}
static void sp_json_member_issue(const World *before,const ProfileMember *m,const char *code,const char *clause,const char *message,bool *first)
{
    printf("%s{\"code\":",*first?"":",");*first=false;js_string(code);fputs(",\"clause\":",stdout);js_string(clause);
    printf(",\"memberId\":%u,\"profileId\":%u,\"rectangle\":",m->id,m->profile_id);sp_json_rect(m);
    fputs(",\"originalRectangle\":",stdout);const ProfileMember *old=sp_member((World*)before,m->id);if(old)sp_json_rect(old);else fputs("null",stdout);
    fputs(",\"message\":",stdout);js_string(message);
}
static size_t sp_json_violations(const World *before,const World *after,bool fallback)
{
    const SectionProfileState *s=&after->wood.section_profiles;bool first=true;size_t count=0;putchar('[');
    for(size_t i=0;i<s->member_count;++i){const ProfileMember *m=&s->members[i];
        if(m->missing_profile){sp_json_member_issue(before,m,"PROFILE_MISSING","I49","Referenced profile must exist",&first);fputs(",\"expected\":\"existing profile\",\"actual\":\"missing\"}",stdout);++count;}
        for(int f=0;f<2;++f)if(m->source_error[f][0]){sp_json_member_issue(before,m,"MEMBER_DIMENSION_INVALID","I46",m->source_error[f],&first);printf(",\"field\":\"%c\",\"expected\":\"positive integer dimension\",\"actual\":",f?'B':'A');js_string(m->source_error[f]);putchar('}');++count;}
        if(m->range_error){sp_json_member_issue(before,m,"MEMBER_RANGE","I46/D1","Rectangle endpoint exceeds coordinate range",&first);fputs(",\"expected\":[-100000000,100000000],\"actual\":",stdout);sp_json_rect(m);putchar('}');++count;}
        if(m->outside){const SectionProfile *p=sp_profile((World*)after,m->profile_id);SurfaceRegion2 regions[SP_OUTSIDE_MAX];size_t n=sp_outside_regions(&p->outline,&m->rect,regions);
            sp_json_member_issue(before,m,"V_PROFILE_OUTSIDE","I44","Member rectangle must be contained by profile",&first);
            fputs(",\"expected\":\"rectangle contained in closed profile\",\"actual\":\"outside\",\"outsideRegions\":[",stdout);
            for(size_t k=0;k<n;++k){if(k)putchar(',');sp_json_region(regions[k]);}fputs("]}",stdout);++count;}
    }
    for(size_t i=0;i<s->member_count;++i)for(size_t j=0;j<i;++j){SurfaceRegion2 r;const ProfileMember *a=&s->members[j],*b=&s->members[i];if(!sp_intersection(a,b,&r))continue;
        sp_json_member_issue(before,a,"V_PROFILE_OVERLAP","I45","Member interiors must not intersect",&first);printf(",\"otherMemberId\":%u,\"otherRectangle\":",b->id);sp_json_rect(b);
        fputs(",\"otherOriginalRectangle\":",stdout);const ProfileMember *old=sp_member((World*)before,b->id);if(old)sp_json_rect(old);else fputs("null",stdout);
        fputs(",\"intersection\":",stdout);sp_json_region(r);fputs(",\"expected\":\"empty interior intersection\",\"actual\":\"positive area\"}",stdout);++count;}
    for(size_t i=0;i<s->run_count;++i){const ProfileRun *r=&s->runs[i];const char *messages[]={r->missing_profile?"Referenced profile is missing":"",r->length_error,r->placement_error,r->range_error?"Generated vertices exceed coordinate range":""};const char *codes[]={"PROFILE_MISSING","RUN_LENGTH_INVALID","RUN_PLACEMENT_INVALID","RUN_RANGE"};const char *clauses[]={"I49","I47","I48","I47/I48/D1"};
        for(int k=0;k<4;++k)if(messages[k][0]){printf("%s{\"code\":",first?"":",");first=false;js_string(codes[k]);fputs(",\"clause\":",stdout);js_string(clauses[k]);printf(",\"runId\":%u,\"profileId\":%u,\"message\":",r->id,r->profile_id);js_string(messages[k]);fputs(",\"expected\":\"valid referenced profile, positive integer length and legal placement\",\"actual\":",stdout);js_string(messages[k]);
            if(k==3){fputs(",\"outsideVertices\":[",stdout);bool initial=true;const SectionProfile *p=sp_profile((World*)after,r->profile_id);
                for(size_t v=0;p&&v<p->outline.count;++v)for(int end=0;end<2;++end){Point3 q=sp_point(r,p->outline.v[v].u,p->outline.v[v].v,end?r->length:0);if(coord_in_range(q.x)&&coord_in_range(q.y)&&coord_in_range(q.z))continue;if(!initial)putchar(',');initial=false;sp_json_point(q);}putchar(']');}
            putchar('}');++count;}
    }
    if(!count&&fallback){fputs("{\"code\":\"SECTION_PROFILE_INVALID\",\"clause\":\"I43-I49\",\"message\":",stdout);js_string(g_engineering_error[0]?g_engineering_error:scene_last_error());fputs(",\"expected\":\"valid atomic transaction\",\"actual\":\"rejected input or upstream dependency\"}",stdout);++count;}
    putchar(']');return count;
}
