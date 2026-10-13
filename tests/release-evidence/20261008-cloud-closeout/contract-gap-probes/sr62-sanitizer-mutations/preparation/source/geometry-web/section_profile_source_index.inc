static void si_profile_sources(SiIndex *s,const World *w)
{
    const SectionProfileState *state=&w->section_profiles;char from[240],text[640];SiNode *n;
    for(size_t i=0;i<state->profile_count;++i){const SectionProfile *p=&state->profiles[i];si_reset(s);si_text(s,"%u;",p->id);si_loop(s,&p->outline);si_nnode(s,"section-profile",p->id,0,0,p->name);}
    bool panels=false;
    for(size_t i=0;i<state->member_count;++i){const ProfileMember *m=&state->members[i];si_numkey(from,"profile-member",m->id,0,0);
        si_reset(s);si_content(s,m->content,"");n=si_nnode(s,"profile-member",m->id,0,0,m->panel?"板材構件":"角材構件");
        si_reset(s);si_text(s,"%d:%lld:%lld:%lld:%lld:%lld:%lld",m->resolved,(long long)m->a,(long long)m->b,(long long)m->rect.min_u,(long long)m->rect.min_v,(long long)m->rect.max_u,(long long)m->rect.max_v);si_value(s,n);
        si_ref(s,from,"section-profile",m->profile_id,0,0,"containment","profile");
        if(m->panel){panels=true;si_edge(s,from,"panel-spec:" SP_PANEL_SPEC,"material-spec","thickness,width",true);}
        else{si_source(s,from,&m->a_source,"A",true);si_source(s,from,&m->b_source,"B",true);}
    }
    if(panels){si_reset(s);si_text(s,"%lld:%lld:%lld",(long long)sp_panel_spec.thickness,(long long)sp_panel_spec.width_max,(long long)sp_panel_spec.sheet_length);si_node(s,"panel-spec",SP_PANEL_SPEC,0,0,sp_panel_spec.name);}
    for(size_t i=0;i<state->run_count;++i){const ProfileRun *r=&state->runs[i];si_numkey(from,"profile-run",r->id,0,0);si_reset(s);
        eng_source_json(&r->length_source,text,sizeof text);si_text(s,"%u:%u:%s:%d:%d;",r->id,r->profile_id,text,r->placed,r->simple);
        if(r->simple){si_text(s,"%d:%u:%d:%lld:%lld;",r->copied_host,r->copied_host?0:r->host_id,r->dir,(long long)r->p,(long long)r->q);si_vector(s,r->up);
            if(r->copied_host){si_point(s,r->host_frame.origin);si_vector(s,r->host_frame.axis_u);si_vector(s,r->host_frame.axis_v);si_vector(s,r->host_frame.normal);si_loop(s,&r->host_region.outline);for(size_t k=0;k<r->host_region.hole_count;++k)si_loop(s,&r->host_region.holes[k]);}}
        else if(r->placed){si_point(s,r->frame.origin);si_vector(s,r->frame.normal);si_vector(s,r->frame.axis_v);}
        n=si_nnode(s,"profile-run",r->id,0,0,"截面延伸");si_reset(s);si_text(s,"%d:%d:%lld;",r->resolved,r->placed,(long long)r->length);
        if(r->placed){si_point(s,r->frame.origin);si_vector(s,r->frame.axis_u);si_vector(s,r->frame.axis_v);si_vector(s,r->frame.normal);}
        const SectionProfile *p=sp_profile((World*)w,r->profile_id);if(p)si_loop(s,&p->outline);
        for(size_t k=0;k<state->member_count;++k){const ProfileMember *m=&state->members[k];if(m->profile_id!=r->profile_id)continue;
            si_text(s,"%u:%lld:%lld:%lld:%lld;",m->id,(long long)m->rect.min_u,(long long)m->rect.min_v,(long long)m->rect.max_u,(long long)m->rect.max_v);si_ref(s,from,"profile-member",m->id,0,0,"member","extruded-member");}
        si_value(s,n);si_source(s,from,&r->length_source,"length",true);si_ref(s,from,"section-profile",r->profile_id,0,0,"profile","outline");
        if(r->simple&&!r->copied_host)si_ref(s,from,"placement",r->host_id,0,0,"position","host");
    }
}
