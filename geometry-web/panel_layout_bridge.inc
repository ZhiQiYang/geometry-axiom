/* PF-2 derived results are generated completely before any result is emitted. */
static void pf_json_loop(const PfLoop *l)
{putchar('[');for(size_t i=0;i<l->count;++i){if(i)putchar(',');pf_json_pair(l->points[i].u,l->points[i].v);}putchar(']');}
static void pf_json_tile_key(uint32_t fill,int64_t i,int64_t j)
{printf("[%u,",fill);pf_json_i64(i);putchar(',');pf_json_i64(j);}
static void pf_json_seam(const PanelFill *p,const PfLayout *d,const PfEffectiveSeam *s)
{
    const PfSeamLine *line=&d->layout.seams[s->line];
    printf("{\"fillId\":%u,\"axis\":\"%c\",\"k\":",p->id,line->axis?'v':'u');pf_json_i64(line->k);fputs(",\"coordinate\":",stdout);pf_json_i64(line->coordinate);
    if(line->staggered){fputs(",\"band\":",stdout);pf_json_i64(line->band);}
    fputs(",\"range\":",stdout);pf_json_pair(s->range[0],s->range[1]);fputs(",\"edges\":",stdout);pf_json_pair(s->edges[0],s->edges[1]);putchar('}');
}
static void pf_json_layout(const World *w,const PanelFill *p)
{
    PfLayout d;if(!pf_build(w,p,&d)){pf_ui_error("panel-fill",p->id,"LAYOUT_UNAVAILABLE",g_engineering_error);fputs("{\"error\":",stdout);js_string(g_engineering_error);putchar('}');pf_free(&d);return;}
    PfSupport support;if(!pf_support_build(w,p,&d,&support)){pf_ui_error("panel-fill",p->id,"SUPPORT_UNAVAILABLE",g_engineering_error);fputs("{\"error\":",stdout);js_string(g_engineering_error);putchar('}');pf_free(&d);return;}
    printf("{\"tileCount\":%u,\"fragmentCount\":%u,\"wholeCount\":%u,\"cutCount\":%u,\"thickness\":",(unsigned)d.layout.count,(unsigned)d.layout.fragments,(unsigned)d.layout.whole,(unsigned)(d.layout.count-d.layout.whole));pf_json_i64(d.t);fputs(",\"tiles\":[",stdout);
    for(size_t i=0;i<d.layout.count;++i){PfTile *t=&d.layout.tiles[i];printf("%s{\"key\":",i?",":"");pf_json_tile_key(p->id,t->i,t->j);fputs("],\"i\":",stdout);pf_json_i64(t->i);fputs(",\"j\":",stdout);pf_json_i64(t->j);fputs(",\"body\":[",stdout);
        for(size_t k=0;k<4;++k){if(k)putchar(',');pf_json_i64(t->body[k]);}printf("],\"whole\":%s,\"fragments\":[",t->area==d.layout.size[0]*d.layout.size[1]?"true":"false");
        for(size_t k=0;k<t->count;++k){PfFragment *f=&t->fragments[k];printf("%s{\"key\":",k?",":"");pf_json_tile_key(p->id,t->i,t->j);printf(",%u],\"area\":",(unsigned)k);pf_json_i64(f->area);fputs(",\"outer\":",stdout);pf_json_loop(&f->loops[0]);fputs(",\"holes\":[",stdout);for(size_t l=1;l<f->count;++l){if(l>1)putchar(',');pf_json_loop(&f->loops[l]);}fputs("]}",stdout);}fputs("]}",stdout);}
    PlacementSurface host_value;const PlacementSurface *host=NULL;
    for(uint64_t i=0;i<w->wood.finish_surfaces.host_count;++i)if(w->wood.finish_surfaces.hosts[i].fill_id==p->id)host=app_placement_read(w,w->wood.finish_surfaces.hosts[i].id,&host_value);
    fputs("],\"obstacles\":[",stdout);for(uint32_t i=0;i<d.finish->obstacle_count;++i){char ref[16];fs_obstacle_text(&d.finish->obstacles[i],ref);if(i)putchar(',');fputs("{\"ref\":",stdout);js_string(ref);printf(",\"panelLayer\":%s,\"timberLayer\":",d.cuts[i]?"true":"false");
        if(host)fputs(d.obstacles[i].relation==FS_INTERIOR&&d.obstacles[i].q[0]<d.t+host->derived_h&&d.obstacles[i].q[1]>d.t?"true":"false",stdout);else fputs("null",stdout);putchar('}');}
    fputs("],\"seamLines\":[",stdout);
    for(size_t i=0;i<d.layout.seam_count;++i){const PfSeamLine *line=&d.layout.seams[i];
        printf("%s{\"axis\":\"%c\",\"k\":",i?",":"",line->axis?'v':'u');pf_json_i64(line->k);fputs(",\"coordinate\":",stdout);pf_json_i64(line->coordinate);
        if(line->staggered){fputs(",\"band\":",stdout);pf_json_i64(line->band);fputs(",\"range\":",stdout);pf_json_pair(line->range[0],line->range[1]);}putchar('}');
    }
    fputs("],\"effectiveSeams\":[",stdout);
    for(size_t i=0;i<support.count;++i){if(i)putchar(',');pf_json_seam(p,&d,&support.seams[i]);}
    fputs("],\"nonSeams\":[",stdout);
    for(size_t i=0;i<support.non_count;++i){if(i)putchar(',');pf_json_seam(p,&d,&support.nonseams[i]);}
    fputs("],\"nonSeamReason\":\"outer-edge-not-two-panels\",\"support\":[",stdout);
    for(size_t i=0;i<support.part_count;++i){const PfSupportPart *s=&support.parts[i];
        printf("%s{\"seam\":%u,\"range\":",i?",":"",(unsigned)s->seam);pf_json_pair(s->range[0],s->range[1]);fputs(",\"left\":",stdout);pf_json_i64(s->left);fputs(",\"right\":",stdout);pf_json_i64(s->right);
        printf(",\"supported\":%s,\"status\":\"%s\",\"colour\":\"%s\"}",s->supported?"true":"false",s->supported?"supported":"insufficient",s->supported?"green":"red");}
    fputs("],\"derivedPlacement\":",stdout);
    if(host)printf("%u",host->id);else fputs("null",stdout);
    /* UI-1 displays the very same exact X used by PF-3. Keep the legacy view
     * unchanged and never reconstruct this value from a browser expression. */
    if(g_pf_ui_exact){GeoQuantity threshold;fputs(",\"threshold\":",stdout);
        if(pf_support_threshold(w,p,&threshold)){fputs("{\"num\":",stdout);pf_json_i64(threshold.num);fputs(",\"den\":",stdout);pf_json_i64(threshold.den);putchar('}');}
        else {pf_ui_error("panel-fill",p->id,"THRESHOLD_UNAVAILABLE",g_parameter_error);fputs("null",stdout);}}
    fputs(",\"pending\":[\"PF-5 remaining spatial flow\"]}",stdout);pf_support_free(&support);pf_free(&d);
}
static void pf_json_state(const World *w)
{
    fputs(",\"panelFills\":[",stdout);for(uint64_t i=0;i<w->wood.finish_surfaces.fill_count;++i){const PanelFill *p=&w->wood.finish_surfaces.fills[i];if(i)putchar(',');fputs("{\"definition\":",stdout);fputs(p->definition,stdout);fputs(",\"derived\":",stdout);pf_json_layout(w,p);putchar('}');}putchar(']');
}
