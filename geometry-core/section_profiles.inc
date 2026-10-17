/* D35-D40 / I43-I51. Native authoring and persistence; no rendering capability. */
static const struct {const char *id,*name;Coord thickness,width_max,sheet_length;} sp_panel_spec={SP_PANEL_SPEC,"calcium silicate board",6,915,1830};
static bool sp_used(const World *w)
{ return w->section_profiles.profile_count || w->section_profiles.member_count || w->section_profiles.run_count; }
static SectionProfile *sp_profile(World *w,uint32_t id)
{ for(size_t i=0;i<w->section_profiles.profile_count;++i)if(w->section_profiles.profiles[i].id==id)return &w->section_profiles.profiles[i];return NULL; }
static ProfileMember *sp_member(World *w,uint32_t id)
{ for(size_t i=0;i<w->section_profiles.member_count;++i)if(w->section_profiles.members[i].id==id)return &w->section_profiles.members[i];return NULL; }
static ProfileRun *sp_run(World *w,uint32_t id)
{ for(size_t i=0;i<w->section_profiles.run_count;++i)if(w->section_profiles.runs[i].id==id)return &w->section_profiles.runs[i];return NULL; }
static bool sp_error(const char *format,...)
{
    va_list args;va_start(args,format);vsnprintf(g_engineering_error,sizeof g_engineering_error,format,args);va_end(args);
    return false;
}
static bool sp_coord(EngJson *j,int token,Coord *out)
{ return eng_json_integer(j,token,out) && coord_in_range(*out); }
static bool sp_axis(EngJson *j,int token,Vector3 *out)
{
    char s[4];if(!eng_json_string(j,token,s,sizeof s))return false;
    *out=(Vector3){0};if((s[0]!='+'&&s[0]!='-')||s[2])return false;
    Coord sign=s[0]=='+'?1:-1;
    if(s[1]=='X')out->x=sign;else if(s[1]=='Y')out->y=sign;else if(s[1]=='Z')out->z=sign;else return false;
    return true;
}
static bool sp_source(EngJson *j,int t,EngDimensionSource *out,bool length,int field)
{
    if(!eng_source_parse(j,t,out,false))return false;
    if(out->kind==ENG_APPLICATION || (length&&out->kind==ENG_MATERIAL))return sp_error("D36/D37: unsupported dimension source");
    if(out->kind==ENG_MATERIAL && out->field!=(field?ENG_B:ENG_A))return sp_error("D36: material source must retain matching A/B field identity");
    return true;
}
#include "section_profile_placement.inc"
static bool sp_put_profile(World *w,EngJson *j,int t)
{
    SectionProfile p={0};int loop=eng_json_member(j,t,"outline");
    if(!eng_json_keys(j,t,"id,name,outline","")||!eng_u32(j,eng_json_member(j,t,"id"),&p.id,false)||
       !eng_json_string(j,eng_json_member(j,t,"name"),p.name,sizeof p.name)||!eng_json_is_array(j,loop))return sp_error("I43: profile needs id, name and integer orthogonal outline; holes are unsupported");
    int n=eng_json_size(j,loop);if(n<4||n>POLY_MAX_VERTICES)return sp_error("I43 CAPACITY: profile outline needs 4..32 vertices");
    p.outline.count=(size_t)n;
    for(int i=0;i<n;++i){int v=eng_json_at(j,loop,i);if(!eng_json_is_array(j,v)||eng_json_size(j,v)!=2||
        !sp_coord(j,eng_json_at(j,v,0),&p.outline.v[i].u)||!sp_coord(j,eng_json_at(j,v,1),&p.outline.v[i].v))return sp_error("I43/D1: profile vertices must be integer mm in range");}
    if(!poly_loop_is_valid(&p.outline))return sp_error("I43: profile %u outline is not a simple closed orthogonal polygon",p.id);
    if(!eng_json_canonical(j,t,p.content,sizeof p.content))return sp_error("I51 CAPACITY: profile record exceeds 2047 bytes");
    SectionProfile *target=sp_profile(w,p.id);
    if(!target){if(w->section_profiles.profile_count==SP_PROFILE_MAX)return sp_error("I51 CAPACITY: profile limit is %d",SP_PROFILE_MAX);target=&w->section_profiles.profiles[w->section_profiles.profile_count++];}
    *target=p;return true;
}
static bool sp_put_member(World *w,EngJson *j,int t)
{
    ProfileMember m={0};char kind[12],orientation[24],spec[32];
    if(!eng_u32(j,eng_json_member(j,t,"id"),&m.id,false)||!eng_u32(j,eng_json_member(j,t,"profileId"),&m.profile_id,false)||
       !eng_json_string(j,eng_json_member(j,t,"kind"),kind,sizeof kind)||
       !eng_json_string(j,eng_json_member(j,t,"orientation"),orientation,sizeof orientation)||
       !sp_coord(j,eng_json_member(j,t,"u0"),&m.u0)||!sp_coord(j,eng_json_member(j,t,"v0"),&m.v0))return sp_error("I46: member needs typed identity, integer coordinates and orientation");
    if(!strcmp(kind,"timber")){
        if(!eng_json_keys(j,t,"id,profileId,kind,A,B,orientation,u0,v0","")||
           (strcmp(orientation,"A-u")&&strcmp(orientation,"A-v")))return sp_error("I46: timber orientation must be A-u or A-v; no role, length or placement");
        if(!sp_source(j,eng_json_member(j,t,"A"),&m.a_source,false,0)||!sp_source(j,eng_json_member(j,t,"B"),&m.b_source,false,1))return false;
        m.rotated=!strcmp(orientation,"A-v");
    }else if(!strcmp(kind,"panel")){
        m.panel=true;
        if(!eng_json_keys(j,t,"id,profileId,kind,panelSpec,width,orientation,u0,v0","")||
           !eng_json_string(j,eng_json_member(j,t,"panelSpec"),spec,sizeof spec)||strcmp(spec,SP_PANEL_SPEC))return sp_error("D40/I46: panel requires calcium-silicate-6; thickness cannot be supplied per member");
        if(!sp_coord(j,eng_json_member(j,t,"width"),&m.width)||m.width<1||m.width>=sp_panel_spec.width_max)return sp_error("V_PANEL_WIDTH I46: member %u expected integer 1 <= width < %lld",m.id,(long long)sp_panel_spec.width_max);
        if(strcmp(orientation,"thickness-v")&&strcmp(orientation,"thickness-u"))return sp_error("I46: panel orientation must be thickness-v or thickness-u");
        m.rotated=!strcmp(orientation,"thickness-u");
    }else return sp_error("D36: member kind must be timber or panel");
    if(!eng_json_canonical(j,t,m.content,sizeof m.content))return sp_error("I51 CAPACITY: member record exceeds 2047 bytes");
    ProfileMember *target=sp_member(w,m.id);
    if(!target){if(w->section_profiles.member_count==SP_MEMBER_MAX)return sp_error("I51 CAPACITY: member limit is %d",SP_MEMBER_MAX);target=&w->section_profiles.members[w->section_profiles.member_count++];}
    *target=m;return true;
}
static bool sp_put_run(World *w,EngJson *j,int t)
{
    ProfileRun r={0};int place=eng_json_member(j,t,"placement");
    if(!eng_json_keys(j,t,"id,profileId,length,placement","")||!eng_u32(j,eng_json_member(j,t,"id"),&r.id,false)||
       !eng_u32(j,eng_json_member(j,t,"profileId"),&r.profile_id,false))return sp_error("D37: run needs id, profileId, length source and placement (null for unplaced)");
    if(!sp_source(j,eng_json_member(j,t,"length"),&r.length_source,true,0))return false;
    if(!sp_placement_json(j,place,&r))return false;
    if(!eng_json_canonical(j,t,r.content,sizeof r.content))return sp_error("I51 CAPACITY: run record exceeds 8191 bytes");
    ProfileRun *target=sp_run(w,r.id);
    if(!target){if(w->section_profiles.run_count==SP_RUN_MAX)return sp_error("I51 CAPACITY: run limit is %d",SP_RUN_MAX);target=&w->section_profiles.runs[w->section_profiles.run_count++];}
    *target=r;return true;
}
static Point3 sp_point(const ProfileRun *r,Coord u,Coord v,Coord along)
{
    if(!r->placed)return (Point3){u,v,along};
    const SurfaceFrame *f=&r->frame;
    return (Point3){f->origin.x+u*f->axis_u.x+v*f->axis_v.x+along*f->normal.x,
        f->origin.y+u*f->axis_u.y+v*f->axis_v.y+along*f->normal.y,
        f->origin.z+u*f->axis_u.z+v*f->axis_v.z+along*f->normal.z};
}
#include "section_profile_validation.inc"
#include "section_profile_conversion.inc"
static bool sp_operation(World *w,EngJson *j,int t)
{
    char op[32];if(!eng_json_string(j,eng_json_member(j,t,"op"),op,sizeof op))return sp_error("I49: section-profile operation needs op");
    if(!strcmp(op,"convert-run-to-advanced")||!strcmp(op,"convert-run-to-simple"))return sp_convert_run(w,j,t,!strcmp(op,"convert-run-to-simple"));
    if(!strcmp(op,"delete-placement")){
        uint32_t id;if(!eng_json_keys(j,t,"op,id","")||!eng_u32(j,eng_json_member(j,t,"id"),&id,false))return sp_error("I49: invalid placement identity");
        size_t i=0;while(i<w->placement_count&&w->placements[i].id!=id)++i;
        if(i==w->placement_count)return sp_error("I49: placement does not exist");
        memmove(w->placements+i,w->placements+i+1,(w->placement_count-i-1)*sizeof w->placements[0]);memset(&w->placements[--w->placement_count],0,sizeof w->placements[0]);
        for(i=0;i<w->canvas_pos_count;++i)if(w->canvas_pos[i].kind==CANVAS_POS_PLACEMENT&&w->canvas_pos[i].id==id){memmove(w->canvas_pos+i,w->canvas_pos+i+1,(w->canvas_pos_count-i-1)*sizeof w->canvas_pos[0]);memset(&w->canvas_pos[--w->canvas_pos_count],0,sizeof w->canvas_pos[0]);break;}
        return true;
    }
    if(!strcmp(op,"put-profile")||!strcmp(op,"put-member")||!strcmp(op,"put-run")){
        if(!eng_json_keys(j,t,"op,value",""))return sp_error("I49: invalid put operation fields");int value=eng_json_member(j,t,"value");
        if(!strcmp(op,"put-profile"))return sp_put_profile(w,j,value);
        bool member=!strcmp(op,"put-member");uint32_t id;
        if(!eng_u32(j,eng_json_member(j,value,"id"),&id,false))return false;
        if(!(member?sp_put_member(w,j,value):sp_put_run(w,j,value)))return false;
        return parameter_declare(w,member?PARAM_OWNER_MEMBER:PARAM_OWNER_RUN,id,0);
    }
    if(!strcmp(op,"delete-profile")||!strcmp(op,"delete-member")||!strcmp(op,"delete-run")){
        uint32_t id;if(!eng_json_keys(j,t,"op,id","")||!eng_u32(j,eng_json_member(j,t,"id"),&id,false))return sp_error("I49: invalid delete identity");
        SectionProfileState *s=&w->section_profiles;void *target;void *base;size_t *count,bytes;
        if(!strcmp(op,"delete-profile")){target=sp_profile(w,id);base=s->profiles;count=&s->profile_count;bytes=sizeof(SectionProfile);}
        else if(!strcmp(op,"delete-member")){target=sp_member(w,id);base=s->members;count=&s->member_count;bytes=sizeof(ProfileMember);}
        else {target=sp_run(w,id);base=s->runs;count=&s->run_count;bytes=sizeof(ProfileRun);}
        if(!target)return sp_error("I49: deleted %s id %u does not exist",op+7,id);
        size_t at=((unsigned char*)target-(unsigned char*)base)/bytes;
        memmove(target,(unsigned char*)target+bytes,(*count-at-1)*bytes);--*count;memset((unsigned char*)base+*count*bytes,0,bytes);return true;
    }
    if(!strcmp(op,"put-spec")||!strcmp(op,"delete-spec")){
        char name[SPEC_NAME_MAX];Coord value=0;bool remove=!strcmp(op,"delete-spec");
        if(!eng_json_keys(j,t,remove?"op,name":"op,name,value","")||!eng_json_string(j,eng_json_member(j,t,"name"),name,sizeof name)||!reference_name(name)||
           (!remove&&!sp_coord(j,eng_json_member(j,t,"value"),&value)))return sp_error("D6b: invalid named integer spec");
        size_t at=0;while(at<w->spec_count&&strcmp(w->specs[at].name,name))++at;
        if(remove){if(at==w->spec_count)return sp_error("D6b: deleted spec missing");memmove(w->specs+at,w->specs+at+1,(w->spec_count-at-1)*sizeof(SpecValue));memset(&w->specs[--w->spec_count],0,sizeof(SpecValue));}
        else {if(at==w->spec_count){if(w->spec_count==WORLD_MAX_SPECS)return sp_error("D6b CAPACITY: spec limit exceeded");++w->spec_count;}snprintf(w->specs[at].name,sizeof w->specs[at].name,"%s",name);w->specs[at].value=value;}
        return true;
    }
    return eng_operation(w,j,t);
}
static void sp_dump(const World *w,FILE *out)
{
    if(!sp_used(w))return;fputs("requires section-profile/1\n",out);
    const SectionProfileState *s=&w->section_profiles;char encoded[SP_RUN_RECORD_MAX*2];size_t n;
    for(int kind=0;kind<3;++kind){size_t count=kind==0?s->profile_count:kind==1?s->member_count:s->run_count;
        for(size_t i=0;i<count;++i){const char *text=kind==0?s->profiles[i].content:kind==1?s->members[i].content:s->runs[i].content;
            if(!eng_base64_encode(text,strlen(text),encoded,sizeof encoded,&n)){fputs("requires section-profile-record-capacity-error\n",out);return;}
            fprintf(out,"section-profile %s %s\n",kind==0?"profile":kind==1?"member":"run",encoded);}}
}
static bool apply_section_profile_line(const char *path,int line_no,char **tokens,int count,World *w)
{
    (void)count;bool ok=false;unsigned char decoded[SP_RUN_RECORD_MAX];size_t n;uint32_t id;EngJson j={0};
    if(!g_parsing_scene_file){scene_error(path,line_no,"I49: section-profile records require atomic scene load; use section-profile-preview/confirm");return false;}
    if(!sp_scene_required){scene_error(path,line_no,"I51: section-profile records require section-profile/1 declaration first");return false;}
    if(eng_base64_decode(tokens[2],strlen(tokens[2]),decoded,sizeof decoded-1,&n)){
        decoded[n]=0;
        if(eng_json_parse_n(&j,(char*)decoded,n)&&eng_u32(&j,eng_json_member(&j,0,"id"),&id,false)){
            if(!strcmp(tokens[1],"profile")&&!sp_profile(w,id))ok=sp_put_profile(w,&j,0);
            else if(!strcmp(tokens[1],"member")&&!sp_member(w,id))ok=sp_put_member(w,&j,0);
            else if(!strcmp(tokens[1],"run")&&!sp_run(w,id))ok=sp_put_run(w,&j,0);
        }
    }
    eng_json_free(&j);if(!ok)scene_error(path,line_no,g_engineering_error[0]?g_engineering_error:"I51: invalid/duplicate section-profile record");return ok;
}
