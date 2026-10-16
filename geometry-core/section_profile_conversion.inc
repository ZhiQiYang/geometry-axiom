static bool sp_convert_run(World *w,GeoJson *j,int t,bool simple)
{
    uint32_t id;if(!geo_json_keys(j,t,simple?"op,id,host":"op,id","")||!eng_u32(j,geo_json_member(j,t,"id"),&id,false))return sp_error("I48: conversion requires a run identity and explicit target host for simple mode");
    ProfileRun *old=sp_run(w,id);if(!old||!old->placed)return sp_error("I48: conversion requires a placed run");
    ProfileRun r=*old;if(!sp_resolve_placement(w,&r))return sp_error("%s",r.placement_error);
    char place[SP_RUN_RECORD_MAX],host_text[SP_RUN_RECORD_MAX],length[640],record[SP_RUN_RECORD_MAX];
    if(!simple){
        if(!r.simple)return sp_error("I48: run is already advanced");
        snprintf(place,sizeof place,"{\"kind\":\"advanced\",\"origin\":[%lld,%lld,%lld],\"N\":\"%s\",\"V\":\"%s\"}",(long long)r.frame.origin.x,(long long)r.frame.origin.y,(long long)r.frame.origin.z,sp_axis_name(r.frame.normal),sp_axis_name(r.frame.axis_v));
    }else{
        if(r.simple)return sp_error("I48: run is already simple");
        int host_token=geo_json_member(j,t,"host");if(!sp_host_json(j,host_token,&r)||!geo_json_canonical(j,host_token,host_text,sizeof host_text))return false;
        SurfaceFrame host;SpaceBoundarySurface region;if(!sp_host(w,&r,&host,&region))return sp_error("I48: selected conversion host is missing or invalid");
        Vector3 delta={r.frame.origin.x-host.origin.x,r.frame.origin.y-host.origin.y,r.frame.origin.z-host.origin.z};
        Coord p=vector_dot(delta,host.axis_u),q=vector_dot(delta,host.axis_v);int dir=-1;
        Vector3 axes[]={host.axis_u,sp_scaled(host.axis_u,-1),host.axis_v,sp_scaled(host.axis_v,-1)};
        for(int i=0;i<4;++i)if(vector_equal(axes[i],r.frame.normal))dir=i;
        bool plane=vector_dot(delta,host.normal)==0,range=coord_in_range(p)&&coord_in_range(q)&&boundary_contains_point(&region,(SurfacePoint2){p,q});
        Vector3 up=sp_scaled(r.frame.axis_v,-1);bool legal_up=vector_dot(up,r.frame.normal)==0&&vector_dot(up,up)==1;
        if(!plane||dir<0||!range||!legal_up)return sp_error("I48 conversion:%s%s%s%s",plane?"":" origin not in host plane;",dir>=0?"":" N not a host-plane direction;",range?"":" p,q outside host range;",legal_up?"":" V has no legal up;");
        const char *dirs[]={"+u","-u","+v","-v"};
        int n=snprintf(place,sizeof place,"{\"kind\":\"simple\",\"host\":%s,\"dir\":\"%s\",\"p\":%lld,\"q\":%lld,\"up\":\"%s\"}",host_text,dirs[dir],(long long)p,(long long)q,sp_axis_name(up));
        if(n<0||(size_t)n>=sizeof place)return sp_error("I51 CAPACITY: converted placement too large");
    }
    eng_source_json(&r.length_source,length,sizeof length);
    int n=snprintf(record,sizeof record,"{\"id\":%u,\"profileId\":%u,\"length\":%s,\"placement\":%s}",r.id,r.profile_id,length,place);
    if(n<0||(size_t)n>=sizeof record)return sp_error("I51 CAPACITY: converted run too large");
    GeoJson parsed={0};bool ok=app_json_parse(&parsed,record)&&sp_put_run(w,&parsed,0);geo_json_free(&parsed);return ok;
}
