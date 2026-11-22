/* H adapter for the composable R45 builder. Every operation works in a private
 * World and returns a complete candidate. It never publishes a formal World,
 * changes history/revision, or invokes a public preview/confirm command. */
#include "../../geometry-templates/woodworking/native/r45_builder.h"
typedef struct {
    uint32_t fill_id;
    EngDimensionSource a,b;
    int primary_axis; /* 0=member direction u, 1=member direction v */
} Pf6Input;
typedef struct {
    uint32_t host_id,grid_id;
    bool host_present,grid_present,host_created,grid_created;
    WoodR45Plan plan;
    char error[512];
} Pf6Report;
static void pf6_report_free(Pf6Report *report)
{if(report){wood_r45_plan_free(&report->plan);memset(report,0,sizeof *report);}}
static bool pf6_prepare(World *,const Pf6Input *,Pf6Report *);
static bool pf6_suggest(const World *,const Pf6Input *,Pf6Report *);
static bool pf6_apply(World *,const Pf6Input *,const char *const *,size_t,Pf6Report *);

static bool pf6_fail(Pf6Report *report,const char *message)
{snprintf(report->error,sizeof report->error,"%s",message&&message[0]?message:"R45: candidate construction failed");return false;}
static bool pf6_validate(World *w,Pf6Report *report)
{
    g_revalidate_error[0]=0;
    if(world_revalidate(w))return true;
    return pf6_fail(report,g_revalidate_error);
}
static bool pf6_parse_input(GeoJson *j,int token,Pf6Input *input)
{
    char primary[16],secondary[16];int roles=geo_json_member(j,token,"roles");
    memset(input,0,sizeof *input);
    if(!geo_json_keys(j,token,"fillId,A,B,roles","")||
       !wood_eng_u32(j,geo_json_member(j,token,"fillId"),&input->fill_id,true)||
       !geo_json_keys(j,roles,"u,v","")||
       !geo_json_string(j,geo_json_member(j,roles,"u"),primary,sizeof primary)||
       !geo_json_string(j,geo_json_member(j,roles,"v"),secondary,sizeof secondary)||
       !((!strcmp(primary,"primary")&&!strcmp(secondary,"secondary"))||
         (!strcmp(primary,"secondary")&&!strcmp(secondary,"primary"))))
        return fs_error("D45: input requires fillId, explicit A/B sources and opposite u/v seam roles");
    input->primary_axis=!strcmp(primary,"primary")?1:0;
    EngDimensionSource *values[2]={&input->a,&input->b};const char *names[2]={"A","B"};
    for(int k=0;k<2;++k){int field=geo_json_member(j,token,names[k]);
        if(geo_json_integer(j,field,&values[k]->value))values[k]->kind=ENG_LITERAL;
        else if(!eng_source_parse(j,field,values[k],false))return false;
    }
    return true;
}
static bool pf6_prepare_private(World *w,const Pf6Input *input,Pf6Report *report)
{
    if(!input||!input->fill_id||(input->primary_axis!=0&&input->primary_axis!=1))
        return pf6_fail(report,"D45: fill and primary direction must be explicit");
    if(input->a.kind==ENG_APPLICATION||input->b.kind==ENG_APPLICATION)
        return pf6_fail(report,"D4/D45: shared A/B sources cannot be role-specific face-application slots");
    const PanelFill *fill=pf_find(w,input->fill_id);
    if(!fill)return pf6_fail(report,"D45/R45: selected panel fill does not exist");
    /* A staggered coordinate axis runs perpendicular to the member direction. */
    if(fill->stagger_axis>=0&&fill->stagger_axis==1-input->primary_axis)
        return pf6_fail(report,"D45/I13/I21: the staggered seam axis must be secondary");
    EngTarget a={1,UINT32_MAX,0,0},b={1,UINT32_MAX,0,1};Coord width,depth;
    if(!eng_resolve(w,&input->a,&a,UINT32_MAX,WOOD_MEMBER_ROLE_PRIMARY,&width,NULL,0)||
       !eng_resolve(w,&input->b,&b,UINT32_MAX,WOOD_MEMBER_ROLE_PRIMARY,&depth,NULL,0))
        return pf6_fail(report,g_engineering_error);
    const DerivedPlacement *definition=NULL;
    for(size_t k=0;k<w->wood.finish_surfaces.host_count;++k)
        if(w->wood.finish_surfaces.hosts[k].fill_id==input->fill_id)definition=&w->wood.finish_surfaces.hosts[k];
    if(definition){
        report->host_id=definition->id;report->host_present=true;
        const PlacementSurface *host=world_find_placement(w,definition->id);
        if(!host||host->derived_fill_id!=input->fill_id)return pf6_fail(report,"D4/R41: selected fill's derived host is missing");
        WoodDerivedContext context=app_dp_context(w);Coord height;
        if(!wood_dp_height_direct(&context,definition,&height))return pf6_fail(report,g_engineering_error);
        if(height!=depth)return pf6_fail(report,"I53/R45(1): selected B must equal the derived host h");
    }else{
        uint32_t id=1;while(world_find_placement(w,id))++id;
        char source[640],text[1024];if(!eng_source_json(&input->b,source,sizeof source))return pf6_fail(report,"I33 CAPACITY: host h source cannot be encoded");
        int n=snprintf(text,sizeof text,"{\"op\":\"put-derived-placement\",\"value\":{\"id\":%u,\"fillId\":%u,\"h\":%s}}",id,input->fill_id,source);
        if(n<0||(size_t)n>=sizeof text)return pf6_fail(report,"I33 CAPACITY: host definition exceeds supported bytes");
        GeoJson parsed;bool ok=app_json_parse(&parsed,text);if(ok)ok=dp_operation(w,&parsed,0,false);geo_json_free(&parsed);
        if(!ok)return pf6_fail(report,g_engineering_error);
        report->host_id=id;report->host_present=true;report->host_created=true;
    }
    if(!pf6_validate(w,report))return false;
    Timber extra={0};extra.id=UINT32_MAX;extra.role=TIMBER_ROLE_PRIMARY;char error[512]="";
    if(!surface_primary_axis_check(w,report->host_id,&extra,input->primary_axis!=0,error,sizeof error))
        return pf6_fail(report,error);
    /* R45 reuses an existing same-fill main grid without changing its authored
     * preference. A preference is not an existing primary/boundary object. */
    for(size_t k=0;k<w->wood.grid_applications.count;++k){const ReferenceGrid *grid=&w->wood.grid_applications.items[k];
        if(grid->placement_id!=report->host_id||grid->is_subgrid)continue;
        if(!grid->from_fill||grid->from_binding||grid->from_system||grid->fill_id!=input->fill_id)
            return pf6_fail(report,"R45(2): existing main grid is not from this panel fill");
        report->grid_id=grid->id;report->grid_present=true;return true;
    }
    WoodGridContext grids=app_grid_context(w);
    if(!wood_grid_create_fill(&grids,input->fill_id,report->host_id,input->primary_axis+1,&report->grid_id,error,sizeof error))
        return pf6_fail(report,error);
    report->grid_present=true;report->grid_created=true;return pf6_validate(w,report);
}
static bool pf6_prepare(World *candidate,const Pf6Input *input,Pf6Report *report)
{
    memset(report,0,sizeof *report);World *work=malloc(sizeof *work);
    if(!work)return pf6_fail(report,"I33 CAPACITY: R45 candidate workspace unavailable");
    *work=*candidate;const World *previous=g_subgrid_before;if(!previous)g_subgrid_before=candidate;
    bool ok=pf6_prepare_private(work,input,report);
    if(ok)*candidate=*work;
    g_subgrid_before=previous;free(work);return ok;
}
static bool pf6_collect(World *w,const Pf6Input *input,Pf6Report *report)
{
    const PlacementSurface *host=world_find_placement(w,report->host_id);
    const PanelFill *fill=pf_find(w,input->fill_id);const FinishSurface *finish=fill?fs_find(w,fill->finish_id):NULL;
    if(!host||!fill||!finish)return pf6_fail(report,"R41/R45: prepared source closure is missing");
    size_t edge_count=0;for(size_t c=0;c<host->component_count;++c){
        edge_count+=host->components[c].outline.count;
        for(size_t h=0;h<host->components[c].hole_count;++h)edge_count+=host->components[c].holes[h].count;
    }
    WoodR45EdgeFact *edges=calloc(edge_count?edge_count:1,sizeof *edges);
    WoodDerivedValue *value=malloc(sizeof *value);PfLayout layout={0};PfSupport support={0};
    if(!edges||!value){free(edges);free(value);return pf6_fail(report,"I33 CAPACITY: R45 fact workspace unavailable");}
    bool ok=true;size_t e=0;app_dp_value(host,value);
    for(size_t c=0;c<host->component_count&&ok;++c){const SpaceBoundarySurface *boundary=&host->components[c];
        for(int h=-1;h<(int)boundary->hole_count&&ok;++h){const WoodBoundaryLoop *loop=h<0?&boundary->outline:&boundary->holes[h];
        for(size_t k=0;k<loop->count&&ok;++k){WoodR45EdgeFact *fact=&edges[e++];fact->component=c;fact->edge=k;fact->hole=h;
            if(!dp_edge_key(w,host,c,h,k,fact->key,sizeof fact->key)){ok=pf6_fail(report,g_engineering_error);break;}
            if(h>=0)continue;
            for(size_t t=0;t<w->wood.timber_count;++t){const Timber *member=&w->wood.timbers[t];const TimberAnchor *anchor=&w->wood.anchors[t];
                if(!member->placed||anchor->placement_id!=host->id)continue;
                SurfaceRegion2 footprint;if(!timber_a0_footprint_uv(host,member,anchor,&footprint))continue;
                if(placement_boundary_for_rect(host,boundary,&footprint)!=boundary)continue;
                bool along=anchor->length_direction==SURFACE_DIRECTION_POS_V||anchor->length_direction==SURFACE_DIRECTION_NEG_V;
                bool on=false,covers=false;int edge=-1;
                timber_role_props(boundary,along,along?footprint.min_v:footprint.min_u,along?footprint.max_v:footprint.max_u,
                    along?footprint.min_u:footprint.min_v,along?footprint.max_u:footprint.max_v,&on,&covers,&edge);
                if(edge==(int)k){if(member->role==TIMBER_ROLE_BOUNDARY&&covers)fact->boundary_covered=true;if(on)fact->on_boundary=true;}
            }
        }}
    }
    if(ok)ok=pf_build(w,fill,&layout)&&pf_support_build(w,fill,&layout,&support);
    if(ok)ok=wood_r45_enumerate(input->fill_id,input->primary_axis,finish->side,value,edges,edge_count,&layout.layout,&support,&report->plan,report->error,sizeof report->error);
    else if(!report->error[0])pf6_fail(report,g_engineering_error);
    free(edges);free(value);pf_support_free(&support);pf_free(&layout);return ok;
}
static uint32_t pf6_member_id(const World *w)
{uint32_t id=1;while(reference_timber_index(w,id)>=0)++id;return id;}
static bool pf6_stage_member(World *work,const Pf6Input *input,Pf6Report *report,WoodR45Candidate *item,uint32_t id)
{
    EngTarget a={1,id,0,0},b={1,id,0,1};Coord width,depth;const char *error=NULL;
    if(work->wood.timber_count>=WORLD_MAX_TIMBERS)
        return pf6_fail(report,"I33 CAPACITY: R45 member capacity exceeded; suggestion analysis is incomplete");
    if(!eng_resolve(work,&input->a,&a,report->host_id,item->role,&width,NULL,0)||
       !eng_resolve(work,&input->b,&b,report->host_id,item->role,&depth,NULL,0))return pf6_fail(report,g_engineering_error);
    WoodMemberDeclarationContext context={work->wood.timbers,&work->wood.timber_count,WORLD_MAX_TIMBERS,
        work,app_member_declaration_owned,app_member_declaration_replace};
    if(!wood_member_declare(&context,id,width,depth,(WoodMemberRole)item->role,0,&error))return pf6_fail(report,error);
    int index=reference_timber_index(work,id);if(index<0)return pf6_fail(report,"I9: R45 member declaration is missing");
    TimberAnchor anchor={0};anchor.placement_id=report->host_id;anchor.ref_hole=-1;anchor.span_mode=SPAN_AUTO;
    anchor.length_direction=item->axis?SURFACE_DIRECTION_POS_V:SURFACE_DIRECTION_POS_U;
    anchor.depth_side=SURFACE_DEPTH_POSITIVE_NORMAL;anchor.has_through=true;anchor.through=item->through;
    if(item->edge_key[0]){anchor.anchor_kind=ANCHOR_AT_EDGE;snprintf(anchor.ref_derived_key,sizeof anchor.ref_derived_key,"%s",item->edge_key);}
    else{anchor.anchor_kind=ANCHOR_AT_GRID;anchor.ref_grid=report->grid_id;anchor.ref_grid_axis=item->line_axis;
        anchor.ref_grid_index=item->k;anchor.ref_grid_has_band=item->has_band;anchor.ref_grid_band=item->band;}
    if(work->app.next_order==UINT64_MAX)return pf6_fail(report,"I33 CAPACITY: placement order exhausted");
    anchor.order=++work->app.next_order;work->wood.anchors[index]=anchor;work->wood.timbers[index].placed=true;
    if((input->a.kind!=ENG_LITERAL&&!eng_bind(work,&a,&input->a))||
       (input->b.kind!=ENG_LITERAL&&!eng_bind(work,&b,&input->b)))return pf6_fail(report,g_engineering_error);
    return true;
}
static bool pf6_footprint(const World *w,const Pf6Report *report,WoodR45Candidate *item,uint32_t id)
{
    int index=reference_timber_index(w,id);const PlacementSurface *host=world_find_placement(w,report->host_id);SurfaceRegion2 footprint;
    if(index<0||!host||!w->wood.timbers[index].placed||!timber_a0_footprint_uv(host,&w->wood.timbers[index],&w->wood.anchors[index],&footprint))return false;
    item->id=id;item->rect[0]=footprint.min_u;item->rect[1]=footprint.min_v;item->rect[2]=footprint.max_u;item->rect[3]=footprint.max_v;
    item->length=w->wood.timbers[index].length;return true;
}
/* The same source line can meet several effective seams which R6 maps to one
 * span. Evaluate that line against the prefix before its own generated peers,
 * then revalidate the union. A duplicate is an alias, not a second member. */
static bool pf6_evaluate_item(World *work,const Pf6Input *input,Pf6Report *report,size_t at)
{
    WoodR45Candidate *item=&report->plan.items[at];World *trial=malloc(sizeof *trial);
    if(!trial)return pf6_fail(report,"I33 CAPACITY: R45 member workspace unavailable");
    *trial=*work;uint32_t id=pf6_member_id(work);
    for(size_t k=0;k<at;++k){WoodR45Candidate *previous=&report->plan.items[k];
        if(previous->valid&&previous->duplicate_of<0&&wood_r45_same_line(previous,item)){
            int index=reference_timber_index(trial,previous->id);if(index>=0)trial->wood.timbers[index].placed=false;
        }
    }
    bool ok=pf6_stage_member(trial,input,report,item,id)&&pf6_validate(trial,report)&&pf6_footprint(trial,report,item,id);
    if(ok){
        for(size_t k=0;k<at;++k){WoodR45Candidate *previous=&report->plan.items[k];
            if(previous->valid&&previous->duplicate_of<0&&wood_r45_same_span(previous,item)){
                item->duplicate_of=(int)k;item->id=previous->id;item->valid=true;free(trial);return true;
            }
        }
        for(size_t k=0;k<at;++k){WoodR45Candidate *previous=&report->plan.items[k];
            if(previous->valid&&previous->duplicate_of<0&&wood_r45_same_line(previous,item)){
                int index=reference_timber_index(trial,previous->id);if(index>=0)trial->wood.timbers[index].placed=true;
            }
        }
        ok=pf6_validate(trial,report)&&pf6_footprint(trial,report,item,id);
    }
    if(ok){*work=*trial;item->valid=true;}
    else{item->id=0;item->valid=false;snprintf(item->error,sizeof item->error,"%s",report->error[0]?report->error:"R6: no legal complete member");}
    free(trial);return ok;
}
static bool pf6_build(World *candidate,const Pf6Input *input,const char *const *selected,size_t selected_count,bool suggestions,Pf6Report *report)
{
    memset(report,0,sizeof *report);
    if(!suggestions&&!selected_count)return true; /* PF6_EMPTY_SELECTION_ZERO_WRITE */
    if(selected_count>WOOD_R45_CANDIDATE_MAX)return pf6_fail(report,"I33 CAPACITY: too many selected R45 keys");
    World *work=malloc(sizeof *work);if(!work)return pf6_fail(report,"I33 CAPACITY: R45 builder workspace unavailable");
    *work=*candidate;const World *previous=g_subgrid_before;if(!previous)g_subgrid_before=candidate;
    bool ok=pf6_prepare_private(work,input,report)&&pf6_collect(work,input,report);
    if(!ok)goto done;
    for(size_t k=0;k<selected_count;++k){size_t found=SIZE_MAX;
        if(!selected||!selected[k]){ok=pf6_fail(report,"D45: explicit selected keys are required");goto done;}
        for(size_t i=0;i<report->plan.count;++i)if(!strcmp(selected[k],report->plan.items[i].key)){found=i;break;}
        if(found==SIZE_MAX||!report->plan.items[found].selectable){ok=pf6_fail(report,"D45/R45: selected candidate key is unknown or not selectable");goto done;}
        if(report->plan.items[found].selected){ok=pf6_fail(report,"D45: selected candidate keys must be unique");goto done;}
        report->plan.items[found].selected=true;
    }
    bool all_valid=true;char first_error[512]="";
    for(size_t i=0;i<report->plan.count;++i){WoodR45Candidate *item=&report->plan.items[i];
        if(!item->selectable||(!suggestions&&!item->selected))continue; /* PF6_ONLY_EXPLICIT_SELECTED */
        report->error[0]=0;
        if(!pf6_evaluate_item(work,input,report,i)){
            all_valid=false;if(!first_error[0])snprintf(first_error,sizeof first_error,"%s",report->error);
            if(strstr(report->error,"CAPACITY")||strstr(report->error,"capacity")||strstr(report->error,"I32:")){ok=false;goto done;}
        }
    }
    if(suggestions){report->error[0]=0;ok=true;}
    else if(!all_valid){ok=pf6_fail(report,first_error);}
    else{
        ok=pf6_validate(work,report); /* PF6_SELECTED_COMPLETE_REVALIDATION */
        if(ok)*candidate=*work; /* PF6_ATOMIC_CANDIDATE_REPLACE */
    }
done:g_subgrid_before=previous;free(work);return ok;
}
static bool pf6_suggest(const World *basis,const Pf6Input *input,Pf6Report *report)
{return pf6_build((World*)basis,input,NULL,0,true,report);}
static bool pf6_apply(World *candidate,const Pf6Input *input,const char *const *selected,size_t count,Pf6Report *report)
{return pf6_build(candidate,input,selected,count,false,report);}
