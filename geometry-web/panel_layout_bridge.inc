/* PF-2 derived results are generated completely before any result is emitted. */
static void pf_json_loop(const PfLoop *l)
{putchar('[');for(size_t i=0;i<l->count;++i)printf("%s[%lld,%lld]",i?",":"",(long long)l->points[i].u,(long long)l->points[i].v);putchar(']');}
static void pf_json_seam(const PanelFill *p,const PfLayout *d,const PfEffectiveSeam *s)
{
    const PfSeamLine *line=&d->layout.seams[s->line];
    printf("{\"fillId\":%u,\"axis\":\"%c\",\"k\":%lld,\"coordinate\":%lld",p->id,line->axis?'v':'u',(long long)line->k,(long long)line->coordinate);
    if(line->staggered)printf(",\"band\":%lld",(long long)line->band);
    printf(",\"range\":[%lld,%lld],\"edges\":[%lld,%lld]}",(long long)s->range[0],(long long)s->range[1],(long long)s->edges[0],(long long)s->edges[1]);
}
static void pf_json_layout(const World *w,const PanelFill *p)
{
    PfLayout d;if(!pf_build(w,p,&d)){fputs("{\"error\":",stdout);js_string(g_engineering_error);putchar('}');pf_free(&d);return;}
    PfSupport support;if(!pf_support_build(w,p,&d,&support)){fputs("{\"error\":",stdout);js_string(g_engineering_error);putchar('}');pf_free(&d);return;}
    printf("{\"tileCount\":%u,\"fragmentCount\":%u,\"wholeCount\":%u,\"cutCount\":%u,\"thickness\":%lld,\"tiles\":[",(unsigned)d.layout.count,(unsigned)d.layout.fragments,(unsigned)d.layout.whole,(unsigned)(d.layout.count-d.layout.whole),(long long)d.t);
    for(size_t i=0;i<d.layout.count;++i){PfTile *t=&d.layout.tiles[i];printf("%s{\"key\":[%u,%lld,%lld],\"i\":%lld,\"j\":%lld,\"body\":[%lld,%lld,%lld,%lld],\"whole\":%s,\"fragments\":[",i?",":"",p->id,(long long)t->i,(long long)t->j,(long long)t->i,(long long)t->j,(long long)t->body[0],(long long)t->body[1],(long long)t->body[2],(long long)t->body[3],t->area==d.layout.size[0]*d.layout.size[1]?"true":"false");
        for(size_t k=0;k<t->count;++k){PfFragment *f=&t->fragments[k];printf("%s{\"key\":[%u,%lld,%lld,%u],\"area\":%lld,\"outer\":",k?",":"",p->id,(long long)t->i,(long long)t->j,(unsigned)k,(long long)f->area);pf_json_loop(&f->loops[0]);fputs(",\"holes\":[",stdout);for(size_t l=1;l<f->count;++l){if(l>1)putchar(',');pf_json_loop(&f->loops[l]);}fputs("]}",stdout);}fputs("]}",stdout);}
    PlacementSurface host_value;const PlacementSurface *host=NULL;
    for(uint64_t i=0;i<w->wood.finish_surfaces.host_count;++i)if(w->wood.finish_surfaces.hosts[i].fill_id==p->id)host=app_placement_read(w,w->wood.finish_surfaces.hosts[i].id,&host_value);
    fputs("],\"obstacles\":[",stdout);for(uint32_t i=0;i<d.finish->obstacle_count;++i){char ref[16];fs_obstacle_text(&d.finish->obstacles[i],ref);if(i)putchar(',');fputs("{\"ref\":",stdout);js_string(ref);printf(",\"panelLayer\":%s,\"timberLayer\":",d.cuts[i]?"true":"false");
        if(host)fputs(d.obstacles[i].relation==FS_INTERIOR&&d.obstacles[i].q[0]<d.t+host->derived_h&&d.obstacles[i].q[1]>d.t?"true":"false",stdout);else fputs("null",stdout);putchar('}');}
    fputs("],\"seamLines\":[",stdout);
    for(size_t i=0;i<d.layout.seam_count;++i){const PfSeamLine *line=&d.layout.seams[i];
        printf("%s{\"axis\":\"%c\",\"k\":%lld,\"coordinate\":%lld",i?",":"",line->axis?'v':'u',(long long)line->k,(long long)line->coordinate);
        if(line->staggered)printf(",\"band\":%lld,\"range\":[%lld,%lld]",(long long)line->band,(long long)line->range[0],(long long)line->range[1]);putchar('}');
    }
    fputs("],\"effectiveSeams\":[",stdout);
    for(size_t i=0;i<support.count;++i){if(i)putchar(',');pf_json_seam(p,&d,&support.seams[i]);}
    fputs("],\"nonSeams\":[",stdout);
    for(size_t i=0;i<support.non_count;++i){if(i)putchar(',');pf_json_seam(p,&d,&support.nonseams[i]);}
    fputs("],\"nonSeamReason\":\"outer-edge-not-two-panels\",\"support\":[",stdout);
    for(size_t i=0;i<support.part_count;++i){const PfSupportPart *s=&support.parts[i];
        printf("%s{\"seam\":%u,\"range\":[%lld,%lld],\"left\":%lld,\"right\":%lld,\"supported\":%s,\"status\":\"%s\",\"colour\":\"%s\"}",
            i?",":"",(unsigned)s->seam,(long long)s->range[0],(long long)s->range[1],(long long)s->left,(long long)s->right,s->supported?"true":"false",s->supported?"supported":"insufficient",s->supported?"green":"red");}
    fputs("],\"derivedPlacement\":",stdout);
    if(host)printf("%u",host->id);else fputs("null",stdout);
    fputs(",\"pending\":[\"PF-5 remaining spatial flow\"]}",stdout);pf_support_free(&support);pf_free(&d);
}
static void pf_json_state(const World *w)
{
    fputs(",\"panelFills\":[",stdout);for(uint64_t i=0;i<w->wood.finish_surfaces.fill_count;++i){const PanelFill *p=&w->wood.finish_surfaces.fills[i];if(i)putchar(',');fputs("{\"definition\":",stdout);fputs(p->definition,stdout);fputs(",\"derived\":",stdout);pf_json_layout(w,p);putchar('}');}putchar(']');
}
