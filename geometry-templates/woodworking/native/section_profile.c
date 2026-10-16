#include "section_profile.h"
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
const WoodSectionPanelSpec wood_sp_panel_spec={SP_PANEL_SPEC,"calcium silicate board",6,915,1830};
static GeoCoord wood_sp_min(GeoCoord a,GeoCoord b){return a<b?a:b;}
static GeoCoord wood_sp_max(GeoCoord a,GeoCoord b){return a>b?a:b;}
static bool wood_sp_loop_valid(const WoodBoundaryLoop *p)
{GeoLoop2View view={p->v,p->count};return geo_loop_is_valid(&view);}
static GeoRegionView wood_sp_region_view(const WoodBoundaryRegion *r,GeoLoop2View holes[GEO_REGION_MAX_HOLES])
{for(size_t i=0;i<r->hole_count;++i)holes[i]=(GeoLoop2View){r->holes[i].v,r->holes[i].count};return (GeoRegionView){{r->outline.v,r->outline.count},holes,r->hole_count};}
static bool wood_sp_region_valid(const WoodBoundaryRegion *r)
{if(r->hole_count>GEO_REGION_MAX_HOLES)return false;GeoLoop2View holes[GEO_REGION_MAX_HOLES];GeoRegionView view=wood_sp_region_view(r,holes);return geo_region_is_valid(&view);}
static bool wood_sp_region_point(const WoodBoundaryRegion *r,GeoPoint2 p)
{if(!r||r->hole_count>GEO_REGION_MAX_HOLES)return false;GeoLoop2View holes[GEO_REGION_MAX_HOLES];GeoRegionView view=wood_sp_region_view(r,holes);return geo_region_contains_point(&view,p);}
bool wood_sp_used(const WoodSectionProfileContext *w)
{ return w->state->profile_count || w->state->member_count || w->state->run_count; }

SectionProfile *wood_sp_profile(WoodSectionProfileContext *w,uint32_t id)
{ for(size_t i=0;i<w->state->profile_count;++i)if(w->state->profiles[i].id==id)return &w->state->profiles[i];return NULL; }

ProfileMember *wood_sp_member(WoodSectionProfileContext *w,uint32_t id)
{ for(size_t i=0;i<w->state->member_count;++i)if(w->state->members[i].id==id)return &w->state->members[i];return NULL; }

ProfileRun *wood_sp_run(WoodSectionProfileContext *w,uint32_t id)
{ for(size_t i=0;i<w->state->run_count;++i)if(w->state->runs[i].id==id)return &w->state->runs[i];return NULL; }

static bool wood_sp_error(const WoodSectionProfileContext *w,const char *format,...)
{
    va_list args;va_start(args,format);vsnprintf(w->error,w->error_capacity,format,args);va_end(args);
    return false;
}

bool wood_sp_coord(GeoJson *j,int token,GeoCoord *out)
{ return geo_json_integer(j,token,out) && geo_coord_in_range(*out); }

bool wood_sp_axis(GeoJson *j,int token,GeoVector3 *out)
{
    char s[4];if(!geo_json_string(j,token,s,sizeof s))return false;
    *out=(GeoVector3){0};if((s[0]!='+'&&s[0]!='-')||s[2])return false;
    GeoCoord sign=s[0]=='+'?1:-1;
    if(s[1]=='X')out->x=sign;else if(s[1]=='Y')out->y=sign;else if(s[1]=='Z')out->z=sign;else return false;
    return true;
}

static bool wood_sp_source(WoodSectionProfileContext *w,GeoJson *j,int t,EngDimensionSource *out,bool length,int field)
{
    if(!wood_eng_source_parse(&w->engineering,j,t,out,false))return false;
    if(out->kind==ENG_APPLICATION || (length&&out->kind==ENG_MATERIAL))return wood_sp_error(w,"D36/D37: unsupported dimension source");
    if(out->kind==ENG_MATERIAL && out->field!=(field?ENG_B:ENG_A))return wood_sp_error(w,"D36: material source must retain matching A/B field identity");
    return true;
}

static bool wood_sp_loop_json(GeoJson *j,int token,WoodBoundaryLoop *loop)
{
    if(!geo_json_is_array(j,token))return false;int n=geo_json_size(j,token);
    if(n<4||n>GEO_LOOP_MAX_VERTICES)return false;loop->count=(size_t)n;
    for(int i=0;i<n;++i){int p=geo_json_at(j,token,i);if(!geo_json_is_array(j,p)||geo_json_size(j,p)!=2||
        !wood_sp_coord(j,geo_json_at(j,p,0),&loop->v[i].u)||!wood_sp_coord(j,geo_json_at(j,p,1),&loop->v[i].v))return false;}
    return wood_sp_loop_valid(loop);
}

static bool wood_sp_frame_json(GeoJson *j,int token,GeoFrame *f,bool host)
{
    int origin=geo_json_member(j,token,"origin");
    if(!geo_json_keys(j,token,host?"origin,U,V,N":"kind,origin,N,V","")||!geo_json_is_array(j,origin)||geo_json_size(j,origin)!=3||
       !wood_sp_coord(j,geo_json_at(j,origin,0),&f->origin.x)||!wood_sp_coord(j,geo_json_at(j,origin,1),&f->origin.y)||!wood_sp_coord(j,geo_json_at(j,origin,2),&f->origin.z)||
       !wood_sp_axis(j,geo_json_member(j,token,"N"),&f->normal)||!wood_sp_axis(j,geo_json_member(j,token,"V"),&f->axis_v))return false;
    if(host){if(!wood_sp_axis(j,geo_json_member(j,token,"U"),&f->axis_u))return false;}else f->axis_u=geo_vector_cross(f->axis_v,f->normal);
    return geo_frame_is_valid(f);
}

bool wood_sp_host_json(WoodSectionProfileContext *w,GeoJson *j,int token,ProfileRun *r)
{
    char kind[32];if(!geo_json_string(j,geo_json_member(j,token,"kind"),kind,sizeof kind))return wood_sp_error(w,"I48: simple placement requires an explicit host");
    if(!strcmp(kind,"placement")){
        if(!geo_json_keys(j,token,"kind,placementId","")||!wood_eng_u32(j,geo_json_member(j,token,"placementId"),&r->host_id,false))return wood_sp_error(w,"I48: invalid live placement host");
        r->copied_host=false;return true;
    }
    if(strcmp(kind,"space-wall-values"))return wood_sp_error(w,"I48: unknown host kind");
    char description[512];int region=geo_json_member(j,token,"region"),holes=geo_json_member(j,region,"holes");
    if(!geo_json_keys(j,token,"kind,sourceDescription,frame,region","")||!geo_json_string(j,geo_json_member(j,token,"sourceDescription"),description,sizeof description)||
       !wood_sp_frame_json(j,geo_json_member(j,token,"frame"),&r->host_frame,true)||!geo_json_keys(j,region,"outline,holes","")||
       !wood_sp_loop_json(j,geo_json_member(j,region,"outline"),&r->host_region.outline)||!geo_json_is_array(j,holes)||geo_json_size(j,holes)>GEO_REGION_MAX_HOLES)return wood_sp_error(w,"I48: copied host requires valid frame and bounded effective region");
    r->host_region.hole_count=(size_t)geo_json_size(j,holes);
    for(size_t i=0;i<r->host_region.hole_count;++i)if(!wood_sp_loop_json(j,geo_json_at(j,holes,(int)i),&r->host_region.holes[i]))return wood_sp_error(w,"I48: invalid copied host hole");
    if(!wood_sp_region_valid(&r->host_region))return wood_sp_error(w,"I48: invalid copied host effective range");
    r->copied_host=true;return true;
}

bool wood_sp_host(const WoodSectionProfileContext *w,const ProfileRun *r,GeoFrame *frame,WoodBoundaryRegion *region)
{
    if(r->copied_host){*frame=r->host_frame;*region=r->host_region;return true;}
    bool derived=false;
    bool ok=w->evaluation&&w->evaluation->live_host
        ?w->evaluation->live_host(w->evaluation->user,r->host_id,frame,region,&derived)
        :w->live_host(w->user,r->host_id,frame,region,&derived);
    if(!ok)return false;
    if(derived)return wood_sp_error(w,"D4: derived placements cannot host D38 positioning");
    return geo_frame_is_valid(frame)&&wood_sp_region_valid(region);
}

GeoVector3 wood_sp_scaled(GeoVector3 a,GeoCoord sign)
{return (GeoVector3){a.x*sign,a.y*sign,a.z*sign};}

bool wood_sp_resolve_placement(WoodSectionProfileContext *w,ProfileRun *r)
{
    r->placement_error[0]=0;r->placement_resolved=!r->simple;
    if(!r->simple)return true;
    GeoFrame host;WoodBoundaryRegion region;
    if(!wood_sp_host(w,r,&host,&region)){snprintf(r->placement_error,sizeof r->placement_error,"I48: live host %u is missing or invalid",r->host_id);return false;}
    r->frame.normal=wood_sp_scaled(r->dir<2?host.axis_u:host.axis_v,(r->dir%2)?-1:1);
    r->frame.axis_v=wood_sp_scaled(r->up,-1);r->frame.axis_u=geo_vector_cross(r->frame.axis_v,r->frame.normal);
    r->frame.origin=geo_frame_point(&host,r->p,r->q,0);
    bool inside=wood_sp_region_point(&region,(GeoPoint2){r->p,r->q});
    bool perpendicular=geo_vector_dot(r->up,r->frame.normal)==0;
    bool origin=geo_coord_in_range(r->frame.origin.x)&&geo_coord_in_range(r->frame.origin.y)&&geo_coord_in_range(r->frame.origin.z);
    if(!inside||!perpendicular||!origin){snprintf(r->placement_error,sizeof r->placement_error,"I48:%s%s%s",inside?"":" p,q outside closed host range;",perpendicular?"":" up must be perpendicular to run direction;",origin?"":" origin exceeds D1;");return false;}
    r->placement_resolved=true;return true;
}

static bool wood_sp_placement_json(WoodSectionProfileContext *w,GeoJson *j,int token,ProfileRun *r)
{
    if(geo_json_is_null(j,token))return true;
    char kind[16];if(!geo_json_string(j,geo_json_member(j,token,"kind"),kind,sizeof kind))return wood_sp_error(w,"I48: missing placement kind");
    r->placed=true;
    if(!strcmp(kind,"advanced"))return wood_sp_frame_json(j,token,&r->frame,false)||wood_sp_error(w,"I48: advanced placement requires integer O and perpendicular signed cardinal N,V");
    if(strcmp(kind,"simple"))return wood_sp_error(w,"I48: unsupported placement kind");
    char dir[4];if(!geo_json_keys(j,token,"kind,host,dir,p,q,up","")||!geo_json_string(j,geo_json_member(j,token,"dir"),dir,sizeof dir)||
       !wood_sp_coord(j,geo_json_member(j,token,"p"),&r->p)||!wood_sp_coord(j,geo_json_member(j,token,"q"),&r->q)||!wood_sp_axis(j,geo_json_member(j,token,"up"),&r->up))return wood_sp_error(w,"I48: simple placement needs explicit integer p,q, dir and cardinal up");
    const char *dirs[]={"+u","-u","+v","-v"};r->dir=-1;for(int i=0;i<4;++i)if(!strcmp(dir,dirs[i]))r->dir=i;
    if(r->dir<0)return wood_sp_error(w,"I48: dir must be +u,-u,+v,-v");r->simple=true;
    return wood_sp_host_json(w,j,geo_json_member(j,token,"host"),r);
}

bool wood_sp_put_profile(WoodSectionProfileContext *w,GeoJson *j,int t)
{
    SectionProfile p={0};int loop=geo_json_member(j,t,"outline");
    if(!geo_json_keys(j,t,"id,name,outline","")||!wood_eng_u32(j,geo_json_member(j,t,"id"),&p.id,false)||
       !geo_json_string(j,geo_json_member(j,t,"name"),p.name,sizeof p.name)||!geo_json_is_array(j,loop))return wood_sp_error(w,"I43: profile needs id, name and integer orthogonal outline; holes are unsupported");
    int n=geo_json_size(j,loop);if(n<4||n>GEO_LOOP_MAX_VERTICES)return wood_sp_error(w,"I43 CAPACITY: profile outline needs 4..32 vertices");
    p.outline.count=(size_t)n;
    for(int i=0;i<n;++i){int v=geo_json_at(j,loop,i);if(!geo_json_is_array(j,v)||geo_json_size(j,v)!=2||
        !wood_sp_coord(j,geo_json_at(j,v,0),&p.outline.v[i].u)||!wood_sp_coord(j,geo_json_at(j,v,1),&p.outline.v[i].v))return wood_sp_error(w,"I43/D1: profile vertices must be integer mm in range");}
    if(!wood_sp_loop_valid(&p.outline))return wood_sp_error(w,"I43: profile %u outline is not a simple closed orthogonal polygon",p.id);
    if(!geo_json_canonical(j,t,p.content,sizeof p.content))return wood_sp_error(w,"I51 CAPACITY: profile record exceeds 2047 bytes");
    SectionProfile *target=wood_sp_profile(w,p.id);
    if(!target){if(w->state->profile_count==SP_PROFILE_MAX)return wood_sp_error(w,"I51 CAPACITY: profile limit is %d",SP_PROFILE_MAX);target=&w->state->profiles[w->state->profile_count++];}
    *target=p;return true;
}

bool wood_sp_put_member(WoodSectionProfileContext *w,GeoJson *j,int t)
{
    ProfileMember m={0};char kind[12],orientation[24],spec[32];
    if(!wood_eng_u32(j,geo_json_member(j,t,"id"),&m.id,false)||!wood_eng_u32(j,geo_json_member(j,t,"profileId"),&m.profile_id,false)||
       !geo_json_string(j,geo_json_member(j,t,"kind"),kind,sizeof kind)||
       !geo_json_string(j,geo_json_member(j,t,"orientation"),orientation,sizeof orientation)||
       !wood_sp_coord(j,geo_json_member(j,t,"u0"),&m.u0)||!wood_sp_coord(j,geo_json_member(j,t,"v0"),&m.v0))return wood_sp_error(w,"I46: member needs typed identity, integer coordinates and orientation");
    if(!strcmp(kind,"timber")){
        if(!geo_json_keys(j,t,"id,profileId,kind,A,B,orientation,u0,v0","")||
           (strcmp(orientation,"A-u")&&strcmp(orientation,"A-v")))return wood_sp_error(w,"I46: timber orientation must be A-u or A-v; no role, length or placement");
        if(!wood_sp_source(w,j,geo_json_member(j,t,"A"),&m.a_source,false,0)||!wood_sp_source(w,j,geo_json_member(j,t,"B"),&m.b_source,false,1))return false;
        m.rotated=!strcmp(orientation,"A-v");
    }else if(!strcmp(kind,"panel")){
        m.panel=true;
        if(!geo_json_keys(j,t,"id,profileId,kind,panelSpec,width,orientation,u0,v0","")||
           !geo_json_string(j,geo_json_member(j,t,"panelSpec"),spec,sizeof spec)||strcmp(spec,SP_PANEL_SPEC))return wood_sp_error(w,"D40/I46: panel requires calcium-silicate-6; thickness cannot be supplied per member");
        if(!wood_sp_coord(j,geo_json_member(j,t,"width"),&m.width)||m.width<1||m.width>=wood_sp_panel_spec.width_max)return wood_sp_error(w,"V_PANEL_WIDTH I46: member %u expected integer 1 <= width < %lld",m.id,(long long)wood_sp_panel_spec.width_max);
        if(strcmp(orientation,"thickness-v")&&strcmp(orientation,"thickness-u"))return wood_sp_error(w,"I46: panel orientation must be thickness-v or thickness-u");
        m.rotated=!strcmp(orientation,"thickness-u");
    }else return wood_sp_error(w,"D36: member kind must be timber or panel");
    if(!geo_json_canonical(j,t,m.content,sizeof m.content))return wood_sp_error(w,"I51 CAPACITY: member record exceeds 2047 bytes");
    ProfileMember *target=wood_sp_member(w,m.id);
    if(!target){if(w->state->member_count==SP_MEMBER_MAX)return wood_sp_error(w,"I51 CAPACITY: member limit is %d",SP_MEMBER_MAX);target=&w->state->members[w->state->member_count++];}
    *target=m;return true;
}

bool wood_sp_put_run(WoodSectionProfileContext *w,GeoJson *j,int t)
{
    ProfileRun r={0};int place=geo_json_member(j,t,"placement");
    if(!geo_json_keys(j,t,"id,profileId,length,placement","")||!wood_eng_u32(j,geo_json_member(j,t,"id"),&r.id,false)||
       !wood_eng_u32(j,geo_json_member(j,t,"profileId"),&r.profile_id,false))return wood_sp_error(w,"D37: run needs id, profileId, length source and placement (null for unplaced)");
    if(!wood_sp_source(w,j,geo_json_member(j,t,"length"),&r.length_source,true,0))return false;
    if(!wood_sp_placement_json(w,j,place,&r))return false;
    if(!geo_json_canonical(j,t,r.content,sizeof r.content))return wood_sp_error(w,"I51 CAPACITY: run record exceeds 8191 bytes");
    ProfileRun *target=wood_sp_run(w,r.id);
    if(!target){if(w->state->run_count==SP_RUN_MAX)return wood_sp_error(w,"I51 CAPACITY: run limit is %d",SP_RUN_MAX);target=&w->state->runs[w->state->run_count++];}
    *target=r;return true;
}

GeoPoint3 wood_sp_point(const ProfileRun *r,GeoCoord u,GeoCoord v,GeoCoord along)
{
    if(!r->placed)return (GeoPoint3){u,v,along};
    const GeoFrame *f=&r->frame;
    return (GeoPoint3){f->origin.x+u*f->axis_u.x+v*f->axis_v.x+along*f->normal.x,
        f->origin.y+u*f->axis_u.y+v*f->axis_v.y+along*f->normal.y,
        f->origin.z+u*f->axis_u.z+v*f->axis_v.z+along*f->normal.z};
}

size_t wood_sp_outside_regions(const WoodBoundaryLoop *p,const GeoRect2 *r,GeoRect2 out[SP_OUTSIDE_MAX])
{GeoLoop2View view={p->v,p->count};size_t count=0;return geo_loop_rect_complement(&view,r,out,SP_OUTSIDE_MAX,&count)==GEO_GEOMETRY_OK?count:0;}

bool wood_sp_intersection(const ProfileMember *a,const ProfileMember *b,GeoRect2 *r)
{
    if(!a->resolved||!b->resolved||a->profile_id!=b->profile_id)return false;
    *r=(GeoRect2){wood_sp_max(a->rect.min_u,b->rect.min_u),wood_sp_max(a->rect.min_v,b->rect.min_v),wood_sp_min(a->rect.max_u,b->rect.max_u),wood_sp_min(a->rect.max_v,b->rect.max_v)};
    return r->min_u<r->max_u&&r->min_v<r->max_v;
}

static void wood_sp_first_error(char *first,size_t cap,const char *message)
{if(!first[0])snprintf(first,cap,"%s",message);}

bool wood_sp_member_dimension_direct(WoodSectionProfileContext *w,size_t i,int field,GeoCoord *out)
{
    ProfileMember *m=&w->state->members[i];
    if(m->panel){*out=field?wood_sp_panel_spec.thickness:m->width;return true;}
    EngTarget target={1,0,0,field};return w->resolve_dimension(w->user,field?&m->b_source:&m->a_source,&target,out);
}
bool wood_sp_run_length_direct(WoodSectionProfileContext *w,size_t i,GeoCoord *out)
{EngTarget target={1,0,0,0};return w->resolve_dimension(w->user,&w->state->runs[i].length_source,&target,out);}
void wood_sp_evaluate_member_direct(WoodSectionProfileContext *w,size_t i,char *first,size_t capacity)
{
    SectionProfileState *s=w->state;GeoRect2 outside[SP_OUTSIDE_MAX];
    ProfileMember *m=&s->members[i];SectionProfile *p=wood_sp_profile(w,m->profile_id);
    if(w->evaluation&&w->evaluation->profile_definition)w->evaluation->profile_definition(w->evaluation->user,w,m->profile_id);
    m->resolved=false;m->outside=false;m->range_error=false;m->missing_profile=!p;memset(m->source_error,0,sizeof m->source_error);
    if(!p){wood_sp_error(w,"I49: member %u references missing profile %u",m->id,m->profile_id);wood_sp_first_error(first,capacity,w->error);}
    bool dimensions=true;
    for(int f=0;f<2;++f){
        bool ok=w->evaluation&&w->evaluation->member_dimension
            ?w->evaluation->member_dimension(w->evaluation->user,w,i,f,f?&m->b:&m->a)
            :wood_sp_member_dimension_direct(w,i,f,f?&m->b:&m->a);
        if(!ok){snprintf(m->source_error[f],sizeof m->source_error[f],"%s",w->error);wood_sp_first_error(first,capacity,w->error);dimensions=false;}}
    if(!dimensions)return;
    GeoCoord width=m->rotated?m->b:m->a,height=m->rotated?m->a:m->b;
    m->rect=(GeoRect2){m->u0,m->v0,m->u0+width,m->v0+height};m->resolved=true;
    m->range_error=!geo_coord_in_range(m->rect.max_u)||!geo_coord_in_range(m->rect.max_v);
    if(m->range_error){wood_sp_error(w,"I46/D1: member %u rectangle endpoint exceeds coordinate range",m->id);wood_sp_first_error(first,capacity,w->error);}
    /* I44: exact area test. poly_contains_rect (corners on/in + no edge through the interior) also accepts a rectangle that exactly fills a notch. */ if(p&&wood_sp_outside_regions(&p->outline,&m->rect,outside)){
        m->outside=true;wood_sp_error(w,"V_PROFILE_OUTSIDE I44: member %u profile %u rectangle is not contained",m->id,p->id);wood_sp_first_error(first,capacity,w->error);}

}
void wood_sp_evaluate_run_direct(WoodSectionProfileContext *w,size_t i,char *first,size_t capacity)
{
    SectionProfileState *s=w->state;
    ProfileRun *r=&s->runs[i];SectionProfile *p=wood_sp_profile(w,r->profile_id);
    if(w->evaluation&&w->evaluation->profile_definition)w->evaluation->profile_definition(w->evaluation->user,w,r->profile_id);
    r->resolved=false;r->range_error=false;r->missing_profile=!p;r->length_error[0]=0;
    if(!p){wood_sp_error(w,"I49: run %u references missing profile %u",r->id,r->profile_id);wood_sp_first_error(first,capacity,w->error);}
    r->length_resolved=w->evaluation&&w->evaluation->run_length
        ?w->evaluation->run_length(w->evaluation->user,w,i,&r->length):wood_sp_run_length_direct(w,i,&r->length);
    if(!r->length_resolved){snprintf(r->length_error,sizeof r->length_error,"I47: %.180s",w->error);wood_sp_first_error(first,capacity,r->length_error);}
    if(!(w->evaluation&&w->evaluation->run_placement
         ?w->evaluation->run_placement(w->evaluation->user,w,i):wood_sp_resolve_placement(w,r)))wood_sp_first_error(first,capacity,r->placement_error);
    if(p&&r->length_resolved&&r->placement_resolved)for(size_t v=0;v<p->outline.count;++v)for(int end=0;end<2;++end){
        GeoPoint3 point=wood_sp_point(r,p->outline.v[v].u,p->outline.v[v].v,end?r->length:0);
        if(!geo_coord_in_range(point.x)||!geo_coord_in_range(point.y)||!geo_coord_in_range(point.z)){r->range_error=true;wood_sp_error(w,"I47/I48/D1: run %u generated vertex [%lld,%lld,%lld] exceeds range",r->id,(long long)point.x,(long long)point.y,(long long)point.z);wood_sp_first_error(first,capacity,w->error);}}
    r->resolved=p&&r->length_resolved&&r->placement_resolved&&!r->range_error;

}
bool wood_sp_rebuild(WoodSectionProfileContext *w,char *error,size_t capacity)
{
    SectionProfileState *s=w->state;char first[256]={0};
    if(w->evaluation&&w->evaluation->begin)w->evaluation->begin(w->evaluation->user,w,first,sizeof first);
    for(size_t i=0;i<s->member_count;++i){
        if(w->evaluation&&w->evaluation->member)w->evaluation->member(w->evaluation->user,w,i,first,sizeof first);
        else wood_sp_evaluate_member_direct(w,i,first,sizeof first);
    }
    for(size_t i=0;i<s->member_count;++i)for(size_t j=0;j<i;++j){GeoRect2 overlap;if(wood_sp_intersection(&s->members[i],&s->members[j],&overlap)){
        wood_sp_error(w,"V_PROFILE_OVERLAP I45: members %u,%u intersection [%lld,%lld]x[%lld,%lld]",s->members[j].id,s->members[i].id,(long long)overlap.min_u,(long long)overlap.max_u,(long long)overlap.min_v,(long long)overlap.max_v);wood_sp_first_error(first,sizeof first,w->error);}}
    for(size_t i=0;i<s->run_count;++i){
        if(w->evaluation&&w->evaluation->run)w->evaluation->run(w->evaluation->user,w,i,first,sizeof first);
        else wood_sp_evaluate_run_direct(w,i,first,sizeof first);
    }
    if(first[0]){snprintf(w->error,w->error_capacity,"%s",first);snprintf(error,capacity,"%s",first);return false;}
    return true;
}

const char *wood_sp_axis_name(GeoVector3 v)
{return v.x?(v.x>0?"+X":"-X"):v.y?(v.y>0?"+Y":"-Y"):(v.z>0?"+Z":"-Z");}

bool wood_sp_remove(WoodSectionProfileContext *w,const char *kind,uint32_t id)
{
    SectionProfileState *s=w->state;void *target,*base;size_t *count,bytes;
    if(!strcmp(kind,"profile")){target=wood_sp_profile(w,id);base=s->profiles;count=&s->profile_count;bytes=sizeof(SectionProfile);}
    else if(!strcmp(kind,"member")){target=wood_sp_member(w,id);base=s->members;count=&s->member_count;bytes=sizeof(ProfileMember);}
    else{target=wood_sp_run(w,id);base=s->runs;count=&s->run_count;bytes=sizeof(ProfileRun);}
    if(!target)return wood_sp_error(w,"I49: deleted %s id %u does not exist",kind,id);
    size_t at=((unsigned char*)target-(unsigned char*)base)/bytes;
    memmove(target,(unsigned char*)target+bytes,(*count-at-1)*bytes);--*count;memset((unsigned char*)base+*count*bytes,0,bytes);return true;
}
bool wood_sp_begin_conversion(WoodSectionProfileContext *w,uint32_t id,bool simple,ProfileRun *out)
{
    ProfileRun *old=wood_sp_run(w,id);
    if(!old||!old->placed)return wood_sp_error(w,"I48: conversion requires a placed run");
    *out=*old;
    if(!wood_sp_resolve_placement(w,out))return wood_sp_error(w,"%s",out->placement_error);
    if(!simple&&!out->simple)return wood_sp_error(w,"I48: run is already advanced");
    if(simple&&out->simple)return wood_sp_error(w,"I48: run is already simple");
    return true;
}
bool wood_sp_conversion_fields(WoodSectionProfileContext *w,const ProfileRun *r,const GeoFrame *host,const WoodBoundaryRegion *region,int *out_dir,GeoCoord *out_p,GeoCoord *out_q,GeoVector3 *out_up)
{
    GeoVector3 delta={r->frame.origin.x-host->origin.x,r->frame.origin.y-host->origin.y,r->frame.origin.z-host->origin.z};
    GeoCoord p=geo_vector_dot(delta,host->axis_u),q=geo_vector_dot(delta,host->axis_v);int dir=-1;
    GeoVector3 axes[]={host->axis_u,wood_sp_scaled(host->axis_u,-1),host->axis_v,wood_sp_scaled(host->axis_v,-1)};
    for(int i=0;i<4;++i)if(geo_vector_equal(axes[i],r->frame.normal))dir=i;
    bool plane=geo_vector_dot(delta,host->normal)==0,range=geo_coord_in_range(p)&&geo_coord_in_range(q)&&wood_sp_region_point(region,(GeoPoint2){p,q});
    GeoVector3 up=wood_sp_scaled(r->frame.axis_v,-1);bool legal_up=geo_vector_dot(up,r->frame.normal)==0&&geo_vector_dot(up,up)==1;
    if(!plane||dir<0||!range||!legal_up)return wood_sp_error(w,"I48 conversion:%s%s%s%s",plane?"":" origin not in host plane;",dir>=0?"":" N not a host-plane direction;",range?"":" p,q outside host range;",legal_up?"":" V has no legal up;");
    *out_dir=dir;*out_p=p;*out_q=q;*out_up=up;return true;
}
