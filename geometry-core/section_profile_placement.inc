/* D38: authored simple hosts and lossless frame conversion. */
static bool sp_loop_json(GeoJson *j,int token,PolygonLoop2 *loop)
{
    if(!geo_json_is_array(j,token))return false;int n=geo_json_size(j,token);
    if(n<4||n>POLY_MAX_VERTICES)return false;loop->count=(size_t)n;
    for(int i=0;i<n;++i){int p=geo_json_at(j,token,i);if(!geo_json_is_array(j,p)||geo_json_size(j,p)!=2||
        !sp_coord(j,geo_json_at(j,p,0),&loop->v[i].u)||!sp_coord(j,geo_json_at(j,p,1),&loop->v[i].v))return false;}
    return poly_loop_is_valid(loop);
}
static bool sp_frame_json(GeoJson *j,int token,SurfaceFrame *f,bool host)
{
    int origin=geo_json_member(j,token,"origin");
    if(!geo_json_keys(j,token,host?"origin,U,V,N":"kind,origin,N,V","")||!geo_json_is_array(j,origin)||geo_json_size(j,origin)!=3||
       !sp_coord(j,geo_json_at(j,origin,0),&f->origin.x)||!sp_coord(j,geo_json_at(j,origin,1),&f->origin.y)||!sp_coord(j,geo_json_at(j,origin,2),&f->origin.z)||
       !sp_axis(j,geo_json_member(j,token,"N"),&f->normal)||!sp_axis(j,geo_json_member(j,token,"V"),&f->axis_v))return false;
    if(host){if(!sp_axis(j,geo_json_member(j,token,"U"),&f->axis_u))return false;}else f->axis_u=vector_cross(f->axis_v,f->normal);
    return surface_frame_is_valid(f);
}
static bool sp_host_json(GeoJson *j,int token,ProfileRun *r)
{
    char kind[32];if(!geo_json_string(j,geo_json_member(j,token,"kind"),kind,sizeof kind))return sp_error("I48: simple placement requires an explicit host");
    if(!strcmp(kind,"placement")){
        if(!geo_json_keys(j,token,"kind,placementId","")||!eng_u32(j,geo_json_member(j,token,"placementId"),&r->host_id,false))return sp_error("I48: invalid live placement host");
        r->copied_host=false;return true;
    }
    if(strcmp(kind,"space-wall-values"))return sp_error("I48: unknown host kind");
    char description[512];int region=geo_json_member(j,token,"region"),holes=geo_json_member(j,region,"holes");
    if(!geo_json_keys(j,token,"kind,sourceDescription,frame,region","")||!geo_json_string(j,geo_json_member(j,token,"sourceDescription"),description,sizeof description)||
       !sp_frame_json(j,geo_json_member(j,token,"frame"),&r->host_frame,true)||!geo_json_keys(j,region,"outline,holes","")||
       !sp_loop_json(j,geo_json_member(j,region,"outline"),&r->host_region.outline)||!geo_json_is_array(j,holes)||geo_json_size(j,holes)>POLY_MAX_HOLES)return sp_error("I48: copied host requires valid frame and bounded effective region");
    r->host_region.hole_count=(size_t)geo_json_size(j,holes);
    for(size_t i=0;i<r->host_region.hole_count;++i)if(!sp_loop_json(j,geo_json_at(j,holes,(int)i),&r->host_region.holes[i]))return sp_error("I48: invalid copied host hole");
    if(!boundary_is_valid(&r->host_region))return sp_error("I48: invalid copied host effective range");
    r->copied_host=true;return true;
}
static bool sp_host(const World *w,const ProfileRun *r,SurfaceFrame *frame,SpaceBoundarySurface *region)
{
    if(r->copied_host){*frame=r->host_frame;*region=r->host_region;return true;}
    const PlacementSurface *p=world_find_placement(w,r->host_id);
    if(p&&p->derived_fill_id)return sp_error("D4: derived placements cannot host D38 positioning");
    if(!p||!surface_frame_is_valid(&p->frame))return false;
    const SpaceBoundarySurface *b=world_placement_boundary(w,p);
    if(p->boundary_id&&!b)return false;
    *frame=p->frame;*region=*placement_effective_boundary(p,b,region);return boundary_is_valid(region);
}
static Vector3 sp_scaled(Vector3 a,Coord sign)
{return (Vector3){a.x*sign,a.y*sign,a.z*sign};}
static bool sp_resolve_placement(World *w,ProfileRun *r)
{
    r->placement_error[0]=0;r->placement_resolved=!r->simple;
    if(!r->simple)return true;
    SurfaceFrame host;SpaceBoundarySurface region;
    if(!sp_host(w,r,&host,&region)){snprintf(r->placement_error,sizeof r->placement_error,"I48: live host %u is missing or invalid",r->host_id);return false;}
    r->frame.normal=sp_scaled(r->dir<2?host.axis_u:host.axis_v,(r->dir%2)?-1:1);
    r->frame.axis_v=sp_scaled(r->up,-1);r->frame.axis_u=vector_cross(r->frame.axis_v,r->frame.normal);
    r->frame.origin=geo_frame_point(&host,r->p,r->q,0);
    bool inside=boundary_contains_point(&region,(SurfacePoint2){r->p,r->q});
    bool perpendicular=vector_dot(r->up,r->frame.normal)==0;
    bool origin=coord_in_range(r->frame.origin.x)&&coord_in_range(r->frame.origin.y)&&coord_in_range(r->frame.origin.z);
    if(!inside||!perpendicular||!origin){snprintf(r->placement_error,sizeof r->placement_error,"I48:%s%s%s",inside?"":" p,q outside closed host range;",perpendicular?"":" up must be perpendicular to run direction;",origin?"":" origin exceeds D1;");return false;}
    r->placement_resolved=true;return true;
}
static bool sp_placement_json(GeoJson *j,int token,ProfileRun *r)
{
    if(geo_json_is_null(j,token))return true;
    char kind[16];if(!geo_json_string(j,geo_json_member(j,token,"kind"),kind,sizeof kind))return sp_error("I48: missing placement kind");
    r->placed=true;
    if(!strcmp(kind,"advanced"))return sp_frame_json(j,token,&r->frame,false)||sp_error("I48: advanced placement requires integer O and perpendicular signed cardinal N,V");
    if(strcmp(kind,"simple"))return sp_error("I48: unsupported placement kind");
    char dir[4];if(!geo_json_keys(j,token,"kind,host,dir,p,q,up","")||!geo_json_string(j,geo_json_member(j,token,"dir"),dir,sizeof dir)||
       !sp_coord(j,geo_json_member(j,token,"p"),&r->p)||!sp_coord(j,geo_json_member(j,token,"q"),&r->q)||!sp_axis(j,geo_json_member(j,token,"up"),&r->up))return sp_error("I48: simple placement needs explicit integer p,q, dir and cardinal up");
    const char *dirs[]={"+u","-u","+v","-v"};r->dir=-1;for(int i=0;i<4;++i)if(!strcmp(dir,dirs[i]))r->dir=i;
    if(r->dir<0)return sp_error("I48: dir must be +u,-u,+v,-v");r->simple=true;
    return sp_host_json(j,geo_json_member(j,token,"host"),r);
}
static const char *sp_axis_name(Vector3 v)
{return v.x?(v.x>0?"+X":"-X"):v.y?(v.y>0?"+Y":"-Y"):(v.z>0?"+Z":"-Z");}
