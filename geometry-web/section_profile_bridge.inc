/* Native-only transport. Deliberately does not advertise a model renderer. */
static void sp_json_point(Point3 p)
{ printf("[%lld,%lld,%lld]",(long long)p.x,(long long)p.y,(long long)p.z); }
static void sp_json_axis(Vector3 p)
{ printf("[%lld,%lld,%lld]",(long long)p.x,(long long)p.y,(long long)p.z); }
static void sp_json_rect(const ProfileMember *m)
{
    if(!m->resolved){fputs("null",stdout);return;}
    printf("[%lld,%lld,%lld,%lld]",(long long)m->rect.min_u,(long long)m->rect.min_v,(long long)m->rect.max_u,(long long)m->rect.max_v);
}
static void sp_json_bounds(const ProfileRun *r,const ProfileMember *m)
{
    Point3 lo=sp_point(r,m->rect.min_u,m->rect.min_v,0),hi=lo;
    for(int u=0;u<2;++u)for(int v=0;v<2;++v)for(int end=0;end<2;++end){
        Point3 p=sp_point(r,u?m->rect.max_u:m->rect.min_u,v?m->rect.max_v:m->rect.min_v,end?r->length:0);
        lo.x=coord_min(lo.x,p.x);lo.y=coord_min(lo.y,p.y);lo.z=coord_min(lo.z,p.z);
        hi.x=coord_max(hi.x,p.x);hi.y=coord_max(hi.y,p.y);hi.z=coord_max(hi.z,p.z);
    }
    putchar('[');sp_json_point(lo);putchar(',');sp_json_point(hi);putchar(']');
}
static void json_section_profile_state(const World *w)
{
    const SectionProfileState *s=&w->section_profiles;
    fputs("{\"profiles\":[",stdout);
    for(size_t i=0;i<s->profile_count;++i)printf("%s{\"value\":%s}",i?",":"",s->profiles[i].content);
    fputs("],\"members\":[",stdout);
    for(size_t i=0;i<s->member_count;++i){const ProfileMember *m=&s->members[i];printf("%s{\"value\":%s,\"rect\":",i?",":"",m->content);sp_json_rect(m);
        fputs(",\"dimensions\":",stdout);if(m->resolved)printf("[%lld,%lld]",(long long)m->a,(long long)m->b);else fputs("null",stdout);putchar('}');}
    fputs("],\"runs\":[",stdout);
    for(size_t i=0;i<s->run_count;++i){const ProfileRun *r=&s->runs[i];printf("%s{\"value\":%s,\"length\":",i?",":"",r->content);
        if(r->resolved)printf("%lld",(long long)r->length);else fputs("null",stdout);
        fputs(",\"coordinateSpace\":",stdout);js_string(r->placed?"world":"local");fputs(",\"frame\":",stdout);
        if(r->placed){fputs("{\"origin\":",stdout);sp_json_point(r->frame.origin);fputs(",\"U\":",stdout);sp_json_axis(r->frame.axis_u);fputs(",\"V\":",stdout);sp_json_axis(r->frame.axis_v);fputs(",\"N\":",stdout);sp_json_axis(r->frame.normal);putchar('}');}else fputs("null",stdout);
        fputs(",\"members\":[",stdout);bool first=true;
        for(size_t j=0;j<s->member_count;++j){const ProfileMember *m=&s->members[j];if(m->profile_id!=r->profile_id)continue;
            printf("%s{\"memberId\":%u,\"bounds\":",first?"":",",m->id);first=false;
            if(r->resolved&&m->resolved)sp_json_bounds(r,m);else fputs("null",stdout);putchar('}');}
        fputs("]}",stdout);
    }
    fputs("]}",stdout);
}
static bool sp_contact_covered(const SectionProfile *p,bool vertical,Coord fixed,Coord lo,Coord hi)
{
    if(!p)return false;
    for(size_t pass=0;pass<p->outline.count&&lo<hi;++pass){Coord next=lo;
        for(size_t i=0;i<p->outline.count;++i){SurfacePoint2 a=p->outline.v[i],b=p->outline.v[(i+1)%p->outline.count];
            if(vertical?(a.u!=fixed||b.u!=fixed):(a.v!=fixed||b.v!=fixed))continue;
            Coord min=vertical?coord_min(a.v,b.v):coord_min(a.u,b.u),max=vertical?coord_max(a.v,b.v):coord_max(a.u,b.u);
            if(min<=lo&&max>next)next=max;
        }
        if(next==lo)return false;lo=next;
    }
    return lo>=hi;
}
static bool sp_contact_lost(const SectionProfile *p,const ProfileMember *m,const SectionProfile *next,const ProfileMember *n)
{
    if(!p||!m->resolved||!next||!n->resolved)return false;
    const SurfaceRegion2 *r=&m->rect,*z=&n->rect;
    for(size_t i=0;i<p->outline.count;++i){SurfacePoint2 a=p->outline.v[i],b=p->outline.v[(i+1)%p->outline.count];bool vertical=a.u==b.u;
        Coord fixed=vertical?a.u:a.v;
        if(vertical?(fixed!=r->min_u&&fixed!=r->max_u):(fixed!=r->min_v&&fixed!=r->max_v))continue;
        Coord lo=vertical?coord_max(coord_min(a.v,b.v),r->min_v):coord_max(coord_min(a.u,b.u),r->min_u);
        Coord hi=vertical?coord_min(coord_max(a.v,b.v),r->max_v):coord_min(coord_max(a.u,b.u),r->max_u);
        if(lo>=hi)continue;
        if(vertical?(fixed!=z->min_u&&fixed!=z->max_u):(fixed!=z->min_v&&fixed!=z->max_v))return true;
        if(!sp_contact_covered(next,vertical,fixed,lo,hi))return true;
    }
    return false;
}
#include "section_profile_diagnostics.inc"
static void json_section_profile_impact(const World *before,const World *after)
{
    fputs(",\"sectionProfiles\":{\"before\":",stdout);json_section_profile_state(before);fputs(",\"after\":",stdout);json_section_profile_state(after);
    fputs(",\"warnings\":[",stdout);bool first=true;
    for(size_t i=0;i<before->section_profiles.member_count;++i){const ProfileMember *a=&before->section_profiles.members[i],*z=sp_member((World*)after,a->id);
        if(!z||a->profile_id!=z->profile_id)continue;
        SectionProfile *old=sp_profile((World*)before,a->profile_id),*now=sp_profile((World*)after,z->profile_id);
        if(old&&now&&memcmp(&old->outline,&now->outline,sizeof old->outline)&&sp_contact_lost(old,a,now,z)){
            printf("%s{\"code\":\"PROFILE_CONTACT_LOST\",\"clause\":\"I49\",\"memberId\":%u,\"profileId\":%u}",first?"":",",z->id,z->profile_id);first=false;}
    }
    for(size_t i=0;i<before->section_profiles.run_count;++i){const ProfileRun *a=&before->section_profiles.runs[i],*z=sp_run((World*)after,a->id);
        if(a->simple&&z&&!z->simple&&z->placed){printf("%s{\"code\":\"RUN_HOST_DETACHED\",\"clause\":\"I48\",\"runId\":%u,\"message\":\"進階定位保存目前座標，解除宿主聯動\"}",first?"":",",a->id);first=false;}}
    fputs("],\"diagnosticsComplete\":true,\"violations\":",stdout);sp_json_violations(before,after,!g_preview.valid);putchar('}');
}
static void json_section_profile_preview(void)
{
    /* Source operations disclose both existing geometry and Q38 dependencies. */
    char error[sizeof g_engineering_error];snprintf(error,sizeof error,"%s",g_engineering_error[0]?g_engineering_error:scene_last_error());
    printf("{\"token\":%u,\"valid\":%s,\"revision\":%llu,\"diagnosticsComplete\":true,\"validationStrategy\":\"all-section-profile-violations\"",g_preview.token,g_preview.valid?"true":"false",(unsigned long long)g_preview.revision);
    fputs(",\"before\":",stdout);json_engineering_state(&g_preview.before,true);
    fputs(",\"after\":",stdout);json_engineering_state(&g_preview.after,true);
    snprintf(g_engineering_error,sizeof g_engineering_error,"%s",error);
    json_section_profile_impact(&g_preview.before,&g_preview.after);fputs(",\"violations\":",stdout);
    sp_json_violations(&g_preview.before,&g_preview.after,!g_preview.valid);putchar('}');
}
static void cmd_section_profile_read(void)
{
    printf("{\"ok\":true,\"schema\":\"section-profile-native/1\",\"revision\":%llu,\"simplePlacementSupported\":true,\"capacity\":{\"profiles\":%d,\"members\":%d,\"runs\":%d,\"vertices\":%d,\"recordBytes\":%d,\"runRecordBytes\":%d},\"nativeBytes\":{\"world\":%zu,\"sectionProfiles\":%zu},",(unsigned long long)g_definition_revision,SP_PROFILE_MAX,SP_MEMBER_MAX,SP_RUN_MAX,POLY_MAX_VERTICES,SP_RECORD_MAX-1,SP_RUN_RECORD_MAX-1,sizeof(World),sizeof(SectionProfileState));
    json_engineering_capabilities(&g_world);
    fputs(",\"diagnosticsComplete\":true,\"validationStrategy\":\"all-section-profile-violations\"",stdout);
    printf(",\"panelSpecs\":[{\"id\":\"%s\",\"name\":\"%s\",\"thickness\":%lld,\"widthMaxExclusive\":%lld,\"sheetLength\":%lld}]",sp_panel_spec.id,sp_panel_spec.name,(long long)sp_panel_spec.thickness,(long long)sp_panel_spec.width_max,(long long)sp_panel_spec.sheet_length);
    fputs(",\"state\":",stdout);json_section_profile_state(&g_world);fputs("}\n",stdout);
}
static void cmd_section_profile_preview(const char *path)
{
    batch_preview(path,"section-profile-transaction/1","Expected section-profile-transaction/1, expectedRevision and operations","Section-profile definitions changed; read and preview again","Cannot allocate section-profile candidate","section-profile-transaction",2,sp_operation,json_section_profile_preview);
}
static void cmd_section_profile_confirm(const char *arg)
{ batch_confirm(arg,2,"Missing, invalid or unrelated section-profile token","Section-profile preview expired; preview again"); }
static void cmd_section_profile_cancel(const char *arg)
{ batch_cancel(arg,2,"Cancel requires a section-profile token"); }
