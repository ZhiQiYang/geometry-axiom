/* PF-2 derived results are generated completely before any result is emitted. */
static void pf_json_loop(const PfLoop *l)
{putchar('[');for(size_t i=0;i<l->count;++i)printf("%s[%lld,%lld]",i?",":"",(long long)l->points[i].u,(long long)l->points[i].v);putchar(']');}
static void pf_json_layout(const World *w,const PanelFill *p)
{
    PfLayout d;if(!pf_build(w,p,&d)){fputs("{\"error\":",stdout);js_string(g_engineering_error);putchar('}');pf_free(&d);return;}
    printf("{\"tileCount\":%u,\"fragmentCount\":%u,\"wholeCount\":%u,\"cutCount\":%u,\"thickness\":%lld,\"tiles\":[",(unsigned)d.count,(unsigned)d.fragments,(unsigned)d.whole,(unsigned)(d.count-d.whole),(long long)d.t);
    for(size_t i=0;i<d.count;++i){PfTile *t=&d.tiles[i];printf("%s{\"key\":[%u,%lld,%lld],\"i\":%lld,\"j\":%lld,\"body\":[%lld,%lld,%lld,%lld],\"whole\":%s,\"fragments\":[",i?",":"",p->id,(long long)t->i,(long long)t->j,(long long)t->i,(long long)t->j,(long long)t->body[0],(long long)t->body[1],(long long)t->body[2],(long long)t->body[3],t->area==d.size[0]*d.size[1]?"true":"false");
        for(size_t k=0;k<t->count;++k){PfFragment *f=&t->fragments[k];printf("%s{\"key\":[%u,%lld,%lld,%u],\"area\":%lld,\"outer\":",k?",":"",p->id,(long long)t->i,(long long)t->j,(unsigned)k,(long long)f->area);pf_json_loop(&f->loops[0]);fputs(",\"holes\":[",stdout);for(size_t l=1;l<f->count;++l){if(l>1)putchar(',');pf_json_loop(&f->loops[l]);}fputs("]}",stdout);}fputs("]}",stdout);}
    fputs("],\"obstacles\":[",stdout);for(uint32_t i=0;i<d.finish->obstacle_count;++i){char ref[16];fs_obstacle_text(&d.finish->obstacles[i],ref);if(i)putchar(',');fputs("{\"ref\":",stdout);js_string(ref);printf(",\"panelLayer\":%s,\"timberLayer\":null}",d.cuts[i]?"true":"false");}
    fputs("],\"seamLines\":[",stdout);
    const SpaceBoundarySurface *b=world_find_boundary(w,d.finish->boundary_id);Coord lo[2]={b->outline.v[0].u,b->outline.v[0].v},hi[2]={lo[0],lo[1]};
    for(size_t i=1;i<b->outline.count;++i){lo[0]=coord_min(lo[0],b->outline.v[i].u);hi[0]=coord_max(hi[0],b->outline.v[i].u);lo[1]=coord_min(lo[1],b->outline.v[i].v);hi[1]=coord_max(hi[1],b->outline.v[i].v);}
    bool first=true;for(int axis=0;axis<2;++axis){int other=1-axis;Coord step=panel_layout_pitch(d.size[axis],d.gap),phase=panel_layout_center(p->origin[axis],d.size[axis],d.gap,0);
        int64_t r0=0,r1=0;if(p->stagger_axis==axis){Coord pitch=panel_layout_pitch(d.size[other],d.gap);r0=grid_floor_div(lo[other]-p->origin[other]-d.size[other],pitch)+1;r1=grid_ceil_div(hi[other]-p->origin[other],pitch)-1;}
        for(int64_t r=r0;r<=r1;++r){Coord shift=p->stagger_axis==axis?panel_layout_shift(true,d.stagger,r):0;
            int64_t k0=grid_ceil_div(lo[axis]-phase-shift,step),k1=grid_floor_div(hi[axis]-phase-shift,step);
            for(int64_t k=k0;k<=k1;++k){printf("%s{\"axis\":\"%c\",\"k\":%lld,\"coordinate\":%lld",first?"":",",axis?'v':'u',(long long)k,(long long)panel_layout_center(p->origin[axis]+shift,d.size[axis],d.gap,k));first=false;
                if(p->stagger_axis==axis)printf(",\"band\":%lld,\"range\":[%lld,%lld]",(long long)r,(long long)panel_layout_center(p->origin[other],d.size[other],d.gap,r-1),(long long)panel_layout_center(p->origin[other],d.size[other],d.gap,r));putchar('}');}}
    }
    fputs("],\"effectiveSeams\":null,\"support\":null,\"derivedPlacement\":null,\"pending\":[\"PF-3 effective seams and support\",\"PF-5 timber layer and derived placement\"]}",stdout);pf_free(&d);
}
static void pf_json_state(const World *w)
{
    fputs(",\"panelFills\":[",stdout);for(uint64_t i=0;i<w->finish_surfaces.fill_count;++i){const PanelFill *p=&w->finish_surfaces.fills[i];if(i)putchar(',');fputs("{\"definition\":",stdout);fputs(p->definition,stdout);fputs(",\"derived\":",stdout);pf_json_layout(w,p);putchar('}');}putchar(']');
}
