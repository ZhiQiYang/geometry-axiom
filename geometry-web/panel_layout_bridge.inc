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
    for(size_t i=0;i<d.seam_count;++i){const PfSeamLine *line=&d.seams[i];
        printf("%s{\"axis\":\"%c\",\"k\":%lld,\"coordinate\":%lld",i?",":"",line->axis?'v':'u',(long long)line->k,(long long)line->coordinate);
        if(line->staggered)printf(",\"band\":%lld,\"range\":[%lld,%lld]",(long long)line->band,(long long)line->range[0],(long long)line->range[1]);putchar('}');
    }
    fputs("],\"effectiveSeams\":null,\"support\":null,\"derivedPlacement\":null,\"pending\":[\"PF-3 effective seams and support\",\"PF-H timber layer and derived placement\"]}",stdout);pf_free(&d);
}
static void pf_json_state(const World *w)
{
    fputs(",\"panelFills\":[",stdout);for(uint64_t i=0;i<w->finish_surfaces.fill_count;++i){const PanelFill *p=&w->finish_surfaces.fills[i];if(i)putchar(',');fputs("{\"definition\":",stdout);fputs(p->definition,stdout);fputs(",\"derived\":",stdout);pf_json_layout(w,p);putchar('}');}putchar(']');
}
