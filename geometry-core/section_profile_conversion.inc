static bool sp_convert_run(World *w,GeoJson *j,int t,bool simple)
{
    uint32_t id;if(!geo_json_keys(j,t,simple?"op,id,host":"op,id","")||!eng_u32(j,geo_json_member(j,t,"id"),&id,false))return sp_error("I48: conversion requires a run identity and explicit target host for simple mode");
    WoodSectionProfileContext context=app_sp_context(w);ProfileRun r;
    if(!wood_sp_begin_conversion(&context,id,simple,&r))return false;
    char place[SP_RUN_RECORD_MAX],host_text[SP_RUN_RECORD_MAX],length[640],record[SP_RUN_RECORD_MAX];
    if(!simple){
        snprintf(place,sizeof place,"{\"kind\":\"advanced\",\"origin\":[%lld,%lld,%lld],\"N\":\"%s\",\"V\":\"%s\"}",(long long)r.frame.origin.x,(long long)r.frame.origin.y,(long long)r.frame.origin.z,wood_sp_axis_name(r.frame.normal),wood_sp_axis_name(r.frame.axis_v));
    }else{
        int host_token=geo_json_member(j,t,"host");if(!wood_sp_host_json(&context,j,host_token,&r)||!geo_json_canonical(j,host_token,host_text,sizeof host_text))return false;
        SurfaceFrame host;SpaceBoundarySurface region;if(!wood_sp_host(&context,&r,&host,&region))return sp_error("I48: selected conversion host is missing or invalid");
        Coord p,q;int dir;Vector3 up;
        if(!wood_sp_conversion_fields(&context,&r,&host,&region,&dir,&p,&q,&up))return false;
        const char *dirs[]={"+u","-u","+v","-v"};
        int n=snprintf(place,sizeof place,"{\"kind\":\"simple\",\"host\":%s,\"dir\":\"%s\",\"p\":%lld,\"q\":%lld,\"up\":\"%s\"}",host_text,dirs[dir],(long long)p,(long long)q,wood_sp_axis_name(up));
        if(n<0||(size_t)n>=sizeof place)return sp_error("I51 CAPACITY: converted placement too large");
    }
    eng_source_json(&r.length_source,length,sizeof length);
    int n=snprintf(record,sizeof record,"{\"id\":%u,\"profileId\":%u,\"length\":%s,\"placement\":%s}",r.id,r.profile_id,length,place);
    if(n<0||(size_t)n>=sizeof record)return sp_error("I51 CAPACITY: converted run too large");
    GeoJson parsed={0};bool ok=app_json_parse(&parsed,record)&&sp_put_run(w,&parsed,0);geo_json_free(&parsed);return ok;
}
