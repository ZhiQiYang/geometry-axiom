#include <ctype.h>
/* Reference definitions and deterministic reconstruction (D6–D9, I7–I13, R6).
 * Included after the span solver; no floating point or file-format fallback. */
typedef struct {
    uint32_t timber;
    char clause[32], expected[160], actual[256];
} ReferenceIssue;
#define REFERENCE_MAX_ISSUES (WORLD_MAX_TIMBERS * 8 + WORLD_MAX_GUIDES + 8)
static ReferenceIssue g_reference_issues[REFERENCE_MAX_ISSUES];
static size_t g_reference_issue_count;
static World g_reference_trial;
static bool g_reference_capturing;
static void reference_capture_trial(const World *world)
{
    if (!g_reference_capturing) return;
    g_reference_trial=*world;
    /* Rejected upstream sources still need every Q38 dependent diagnostic.
     * Rebuild only the disposable trial, preserving the primary error. */
    sp_capture_diagnostics(&g_reference_trial);
    /* A rejected source has no validated downstream geometry yet. */
    geo_guides_reset_resolved(&g_reference_trial.geo.guide_lines);
    for (size_t i=0;i<g_reference_trial.wood.timber_count;++i) g_reference_trial.wood.timbers[i].placed=false;
}

static bool reference_issue(uint32_t id, const char *clause, const char *expected, const char *actual)
{
    char msg[256];
    snprintf(msg, sizeof msg, "%s timber %u: %.190s", clause, (unsigned)id, actual);
    utf8_trim_tail(msg);                 /* %.190s 是位元組截斷,別切在字元中間 */
    set_revalidate_error(msg);
    if (g_reference_capturing && g_reference_issue_count < REFERENCE_MAX_ISSUES) {
        ReferenceIssue *e = &g_reference_issues[g_reference_issue_count++];
        e->timber = id;
        snprintf(e->clause, sizeof e->clause, "%s", clause);
        snprintf(e->expected, sizeof e->expected, "%s", expected);
        snprintf(e->actual, sizeof e->actual, "%s", actual);
        utf8_trim_tail(e->actual);
    }
    return false;
}

static bool reference_expression(char **tokens, int start, int count, char *out)
{
    size_t n = 0;
    out[0] = '\0';
    for (int i = start; i < count; ++i) {
        size_t k = strlen(tokens[i]);
        if (n + k >= REF_EXPR_MAX) return false;
        memcpy(out+n, tokens[i], k+1); n += k;
    }
    return n != 0;
}

static bool reference_name(const char *name)
{return geo_named_value_name_valid(name);}

static WoodEngineeringContext app_eng_context(const World *);
static bool app_eng_placement(void *,uint32_t,bool *);
static bool app_eng_target(void *,const EngTarget *,WoodEngineeringTargetInfo *);
static bool app_eng_named(void *,const char *,GeoCoord *);
static bool app_eng_parameter(void *,GeoParameterRef,GeoCoord *,char *,size_t);
static bool app_eng_owned(void *,uint32_t);
static bool app_assembly_replaying(void);
static bool app_assembly_saved_dimensions(const World *,uint32_t);
static void app_eng_write(void *,const EngTarget *,GeoCoord);
static bool app_eng_serializable(void *,char *,size_t);
static WoodSectionProfileContext app_sp_context(const World *);
static WoodFinishContext app_fs_context(const World *);
static WoodDerivedContext app_dp_context(const World *);
static WoodAssemblyContext app_asm_context(const World *);
static bool app_asm_json(void *,GeoJson *,const char *);
static void app_asm_drop_position(void *,bool,uint32_t);
static bool app_asm_other(void *,GeoJson *,int);
static bool app_asm_surface(void *,uint32_t);
static bool app_asm_guide(void *,uint32_t,WoodAssemblyGuide *);
static bool app_asm_member(void *,uint32_t,WoodAssemblyMember *);
static bool app_asm_footprint(void *,uint32_t,uint32_t,GeoRect2 *);
static size_t app_asm_member_count(void *);
static void app_asm_allocate(void *,uint32_t);
static bool app_asm_remove(void *,uint32_t);
static void app_asm_write(void *,const WoodMember *,const WoodAssemblyDefinition *);
static bool app_asm_anchor_matches(void *,uint32_t,const WoodAssemblyDefinition *);
static bool app_asm_instance_content(void *,AsmInstance *,GeoJson *,int);
static bool app_sp_resolve_dimension_sources(World *,GeoParameterSources *,WoodEngineeringSources *,const EngDimensionSource *,const EngTarget *,Coord *);
static bool app_sp_live_host(void *,uint32_t,GeoFrame *,WoodBoundaryRegion *,bool *);
static bool app_fs_boundary(void *,uint32_t,WoodBoundaryRegion *);
static bool app_fs_obstacle_box(void *,const FinishObstacleRef *,Coord[3],Coord[3]);
static bool app_fs_parameter_coord(void *,ParameterRef,Coord *);
static bool app_fs_parameter_value(void *,ParameterRef,GeoQuantity *);
static bool app_fs_engineering_operation(void *,GeoJson *,int);
static bool app_fs_derived_operation(void *,GeoJson *,int,bool);
static bool app_dp_read(void *,uint32_t,WoodDerivedValue *);
static bool app_dp_write(void *,const WoodDerivedValue *);
static bool app_dp_remove(void *,uint32_t);
static size_t app_dp_count(void *);
static void app_dp_remove_position(void *,uint32_t);

typedef struct {
    World *world;
    GeoEvalContext *sources;
    bool sources_borrowed,sources_registered;
    GeoParameterSources *parameter_sources;
    GeoParameterStore *parameter_snapshot;
    GeoLinearDefinitionSources *linear_definition_sources;
    GeoVersionSources *version_sources;
    GeoAxisPosition guide_values[GEO_GUIDE_CAPACITY];
    bool guide_values_valid[GEO_GUIDE_CAPACITY];
    WoodEngineeringSources *engineering_sources;
    WoodSectionProfileSources *section_profile_sources;
    WoodFinishSources *finish_sources;
    GeoPlacementSources *placement_sources;
    GeoRegionKeySources *region_key_sources;
    GeoEnclosureSources *enclosure_sources;
    WoodDefinitionSources *definition_sources;
    WoodGridSources *grid_sources;
    WoodContactSources *contact_sources;
    WoodAssemblySources *assembly_sources;
    WoodFinishSourceKey placement_binding_key;
    bool use_current_values,source_failure;
    bool wanted[WORLD_MAX_TIMBERS];
    /* 每次候選驗證均重建整份求值狀態。成功的定義／幾何解碼可共用，
     * 每個 consumer 的依賴登記仍須逐筆執行。 */
    struct {
        bool anchor_valid,definition_valid,pose_valid,footprint_valid,footprint_ok;
        uint32_t id,pose_id,placement;
        WoodMemberPlacement anchor;
        WoodMemberDefinition definition;
        GeoBox3 pose;
        GeoRect2 footprint;
    } member_reads[WORLD_MAX_TIMBERS];
} ReferenceEval;
static ReferenceEval *g_reference_active;
static bool reference_eval_guide(ReferenceEval *, size_t);
static bool reference_eval_timber(ReferenceEval *, size_t);
static bool reference_eval_timber_relation(ReferenceEval *,size_t,GeoDependencyKind);
static bool reference_sources_ensure(ReferenceEval *);
static bool reference_named_quantity(ReferenceEval *,const char *,Coord *);
static bool reference_eval_datum(ReferenceEval *,size_t);
static bool reference_datum_position(ReferenceEval *,size_t,GeoAxisPosition *);
static bool reference_guide_position(ReferenceEval *,size_t,GeoAxisPosition *);
static bool reference_placement_frame(ReferenceEval *,uint32_t,GeoFrame *);
static bool reference_member_placement(ReferenceEval *,PlacementSurface *,SpaceBoundarySurface *);
static bool reference_host_read(ReferenceEval *,uint32_t,PlacementSurface *,SpaceBoundarySurface *,const SpaceBoundarySurface **);
static bool reference_member_dimension(ReferenceEval *,uint32_t,bool,Coord *);
static bool reference_member_owned(ReferenceEval *,uint32_t,bool *);
static bool reference_member_footprint(ReferenceEval *,size_t,uint32_t,GeoRect2 *);
static bool reference_member_anchor_read(ReferenceEval *,size_t,uint32_t,WoodMemberPlacement *);
static bool reference_member_definition_read(ReferenceEval *,size_t,uint32_t,WoodMemberDefinition *);
static bool reference_grid_definition(ReferenceEval *,uint32_t,WoodGridApplication *);
static bool reference_derived_resolve(ReferenceEval *,const PlacementSurface *,const char *,int *,int *);
static void reference_sources_dispose(ReferenceEval *ctx)
{
    if(!ctx->sources_borrowed)geo_eval_destroy(ctx->sources);
    geo_parameter_sources_destroy(ctx->parameter_sources);geo_parameters_destroy(ctx->parameter_snapshot);
    geo_linear_definition_sources_destroy(ctx->linear_definition_sources);ctx->linear_definition_sources=NULL;
    geo_version_sources_destroy(ctx->version_sources);ctx->version_sources=NULL;
    wood_engineering_sources_destroy(ctx->engineering_sources);ctx->engineering_sources=NULL;
    wood_sp_sources_destroy(ctx->section_profile_sources);ctx->section_profile_sources=NULL;
    wood_finish_sources_destroy(ctx->finish_sources);ctx->finish_sources=NULL;
    geo_placement_sources_destroy(ctx->placement_sources);ctx->placement_sources=NULL;
    geo_region_key_sources_destroy(ctx->region_key_sources);ctx->region_key_sources=NULL;
    geo_enclosure_sources_destroy(ctx->enclosure_sources);ctx->enclosure_sources=NULL;
    wood_definition_sources_destroy(ctx->definition_sources);ctx->definition_sources=NULL;
    wood_grid_sources_destroy(ctx->grid_sources);ctx->grid_sources=NULL;
    wood_contact_sources_destroy(ctx->contact_sources);ctx->contact_sources=NULL;
    wood_assembly_sources_destroy(ctx->assembly_sources);ctx->assembly_sources=NULL;
    ctx->parameter_sources=NULL;ctx->parameter_snapshot=NULL;ctx->sources=NULL;ctx->sources_registered=false;
    memset(ctx->member_reads,0,sizeof ctx->member_reads);
}
static bool reference_quantity(ReferenceEval *,const GuideLine *,const char *,Coord *);
static bool reference_parameter_quantity(ReferenceEval *,ParameterRef,GeoQuantity *);
static int reference_timber_index(const World *w, uint32_t id)
{
    for (size_t i=0;i<w->wood.timber_count;++i) if (w->wood.timbers[i].id==id) return (int)i;
    return -1;
}

static char g_rule_reference_error[256];
static bool reference_face_parse(const char *,ReferenceFace *);
static bool reference_quantity_raw(ReferenceEval *ctx, const GuideLine *g, const char *text, Coord *out)
{
    World *w=ctx->world;
    /* D6c deliberately permits only named specs, without a placement context. */
    if (!g) {
        if (strncmp(text,"spec:",5)) return false;
        return reference_named_quantity(ctx,text+5,out);
    }
    const PlacementSurface *p=world_find_placement(w,g->placement_id);
    if (!p) return false;
    SpaceBoundarySurface effective;
    const SpaceBoundarySurface *b=placement_effective_boundary(p,world_placement_boundary(w,p),&effective);
    int axis=g->direction==GUIDE_ALONG_V?0:1;
    if(!strncmp(text,"gridrule:",9)) {
        GridRuleLineRef ref;
        return grid_rule_ref_text(text,&ref) && ref.axis==axis &&
            (ctx->use_current_values?grid_rule_line(w,&ref,g->placement_id,out,NULL,g_rule_reference_error,sizeof g_rule_reference_error):
                wood_grid_sources_rule_line(ctx->grid_sources,&ref,g->placement_id,out,NULL,g_rule_reference_error,sizeof g_rule_reference_error));
    }
    char buf[REF_EXPR_MAX], *part[5]; int n=0;
    snprintf(buf,sizeof buf,"%s",text);
    char *cursor=buf;
    while (n<5) {
        part[n++]=cursor;
        char *sep=strchr(cursor,':');
        if (!sep) break;
        *sep='\0'; cursor=sep+1;
    }
    uint32_t id;
    if (n==2 && !strcmp(part[0],"spec")) {
        return reference_named_quantity(ctx,part[1],out);
    }
    if (n==2 && !strcmp(part[0],"guide") && parse_u32(part[1],&id)) {
        for (size_t i=0;i<geo_guides_count(&w->geo.guide_lines);++i) {
            const GuideLine *q=&geo_guides_values(&w->geo.guide_lines)[i];
            if (q->id!=id) continue;
            GeoGuide definition;
            if(!ctx->use_current_values){if(!geo_linear_definition_sources_guide(ctx->linear_definition_sources,id,&definition))return false;q=&definition;}
            GeoAxisPosition position;
            if (q->placement_id!=g->placement_id || !reference_guide_position(ctx,i,&position) ||
                !position.context.has_placement||position.context.placement!=g->placement_id||position.context.axis!=axis) return false;
            *out=position.coordinate; return true;
        }
        return false;
    }
    if ((n==3 || n==4) &&
        (!strcmp(part[0],"grid") || !strcmp(part[0],"panel") || !strcmp(part[0],"gap"))) {
        if (!parse_u32(part[1],&id) || strcmp(part[2],axis==0?"u":"v")) return false;
        const ReferenceGrid *grid=world_find_grid(w,id);WoodGridApplication grid_definition;
        if (!grid) return false;
        if(!ctx->use_current_values){if(!reference_grid_definition(ctx,id,&grid_definition))return false;grid=&grid_definition;}
        if (grid->placement_id!=g->placement_id) return false;
        if (!strcmp(part[0],"grid")) {
            int64_t k;
            if (grid->axis[axis].stagger_set) return false;
            return n==4 && parse_i64(part[3],&k) &&
                (ctx->use_current_values?grid_line_coord_in(w->wood.grid_applications.items,w->wood.grid_applications.count,grid,p,b,axis,k,out,NULL,NULL,0):
                    wood_grid_sources_line(ctx->grid_sources,id,g->placement_id,axis,k,false,false,0,out,NULL,NULL,0));
        }
        if (n!=3 || grid->axis[axis].source != GRID_SRC_PANEL) return false;
        if(ctx->use_current_values){*out=!strcmp(part[0],"panel")?grid->axis[axis].body:grid->axis[axis].gap;return true;}
        return wood_grid_sources_dimension(ctx->grid_sources,id,axis,!strcmp(part[0],"gap"),out,NULL,0);
    }
    if (n>=3 && !strcmp(part[0],"timber") && parse_u32(part[1],&id)) {
        int ti=reference_timber_index(w,id);
        if (ti<0) return false;
        Timber *t=&w->wood.timbers[ti];
        if(ctx->wanted[ti]){uint32_t placement=w->wood.anchors[ti].placement_id;
            if(!ctx->use_current_values){WoodMemberPlacement authored;
                if(!wood_definition_sources_placement(ctx->definition_sources,id,&authored))return false;placement=authored.placement_id;}
            if(placement!=g->placement_id)return false;
        }
        if (n==3 && (!strcmp(part[2],"A") || !strcmp(part[2],"B"))) {
            return reference_member_dimension(ctx,id,!strcmp(part[2],"B"),out);
        }
        if (n!=4 || strcmp(part[2],axis==0?"u":"v") ||
            (strcmp(part[3],"lo") && strcmp(part[3],"hi")) ||
            !reference_eval_timber(ctx,(size_t)ti)) return false;
        SurfaceRegion2 f;
        if (!reference_member_footprint(ctx,(size_t)ti,g->placement_id,&f)) return false;
        *out=axis==0 ? (!strcmp(part[3],"lo")?f.min_u:f.max_u)
                     : (!strcmp(part[3],"lo")?f.min_v:f.max_v);
        return true;
    }
    if (n==3 && (!strcmp(part[0],"edge") || !strcmp(part[0],"vertex") || !strcmp(part[0],"edge-key"))) {
        if (strcmp(part[2],axis==0?"u":"v")) return false;
        PlacementSurface source_placement;SpaceBoundarySurface source_boundary;
        const SpaceBoundarySurface *source_b;
        if(!reference_host_read(ctx,p->id,&source_placement,&source_boundary,&source_b))return false;
        p=&source_placement;b=placement_effective_boundary(p,source_b,&effective);
        PolygonLoop2 rect;
        const PolygonLoop2 *loop;
        int hole=-1, index=-1;
        if(!strcmp(part[0],"edge-key")) {
            char encoded[1040];ReferenceFace ref;
            int len=snprintf(encoded,sizeof encoded,"key-hex:%s",part[1]);
            if(len<0||(size_t)len>=sizeof encoded||!reference_face_parse(encoded,&ref)||!reference_derived_resolve(ctx,p,ref.key,&hole,&index))return false;
            size_t component=hole<0?(size_t)index/POLY_MAX_VERTICES:(size_t)hole/POLY_MAX_HOLES;
            b=&p->components[component];if(hole<0)index%=POLY_MAX_VERTICES;else hole%=POLY_MAX_HOLES;
        } else if(p->derived_fill_id) return false;
        else if (!strcmp(part[0],"edge")) {
            if (!parse_edge_ref(part[1],&hole,&index)) return false;
        } else {
            char *q=part[1]; uint32_t hi=0,vi=0;
            if (*q=='h') {
                char *v=strchr(q,'v'); if (!v) return false;
                *v='\0'; if (!parse_u32(q+1,&hi) || hi>=POLY_MAX_HOLES) return false;
                *v='v'; hole=(int)hi; q=v; /* D6a(a): h<i>v<j> keeps its v<j> part */
            }
            if (*q!='v' || !parse_u32(q+1,&vi) || vi>=POLY_MAX_VERTICES) return false;
            index=(int)vi;
        }
        if (!b) { if (hole>=0) return false; placement_outline(p,NULL,&rect); loop=&rect; }
        else { if (hole >= (int)b->hole_count) return false; loop=hole<0?&b->outline:&b->holes[hole]; }
        if (index<0 || (size_t)index>=loop->count) return false;
        SurfacePoint2 a=loop->v[index], z=loop->v[(index+1)%loop->count];
        if (strcmp(part[0],"vertex") && (axis==0 ? a.u!=z.u : a.v!=z.v)) return false;
        *out=axis==0?a.u:a.v; return true;
    }
    return false; /* A naked number is never a reference. */
}

/* H decodes the legacy grammar; K owns typed terms and exact evaluation.
 * A failed suffix is retained so earlier source failures keep their order. */
enum { APP_LINEAR_SOURCE=1, APP_LINEAR_PARAMETER=2 };
static bool reference_compile_text(const char *expression,GeoLinearExpression *compiled)
{
    const char *p=expression;
    int terms=0;
    bool exact=strstr(expression,"param:")!=NULL;
    geo_linear_begin(compiled,exact?GEO_LINEAR_EXACT_INTEGER_FINAL:GEO_LINEAR_FLOOR_FINAL);
    if (!*p) return false;
    while (*p) {
        int sign=1;
        if (*p=='+' || *p=='-') { if (*p=='-') sign=-1; ++p; }
        if (!*p || ++terms>64) return false;
        const char *end=p;
        while (*end) {
            if(*end=='-'&&end-p>=4&&!strncmp(end-4,"edge-key:",9)){++end;continue;}
            if (*end=='+' || *end=='-') {
                /* A sign immediately after ':' belongs to the grid index;
                 * the next sign still separates expression terms. */
                if (!(end>p && end[-1]==':' && isdigit((unsigned char)end[1]))) break;
            }
            ++end;
        }
        size_t len=(size_t)(end-p); if (!len || len>=REF_EXPR_MAX) return false;
        char term[REF_EXPR_MAX]; memcpy(term,p,len); term[len]='\0';
        char *q=term, *star=strchr(term,'*'); Coord num=sign,d=1;
        if (star) {
            *star='\0'; q=star+1; char *slash=strchr(term,'/');
            if (slash) { *slash='\0'; if (!parse_i64(slash+1,&d) || d<=0) return false; }
            if (!parse_i64(term,&num) || num<0 || num==INT64_MIN) return false;
            num*=sign;
        }
        GeoLinearSource source={APP_LINEAR_SOURCE,0,0,q};
        if(exact&&!strncmp(q,"param:",6)){
            ParameterRef ref={0};if(!parameter_ref_parse(q,&ref))return false;
            source=(GeoLinearSource){APP_LINEAR_PARAMETER,ref.parameter_id,ref.field_id,NULL};
        }
        if(!geo_linear_append(compiled,num,d,source))return false;
        p=end;
    }
    geo_linear_finish(compiled,true);return true;
}
typedef struct { ReferenceEval *evaluation; const GuideLine *guide; } AppLinearContext;
static bool reference_resolve_linear(void *opaque,const GeoLinearSource *source,GeoQuantity *value)
{
    AppLinearContext *context=opaque;
    if(source->provider==APP_LINEAR_PARAMETER){
        ParameterRef ref={true,source->id,source->field};
        return reference_parameter_quantity(context->evaluation,ref,value);
    }
    if(source->provider!=APP_LINEAR_SOURCE)return false;
    *value=(GeoQuantity){0,1,GEO_UNIT_LENGTH};
    return reference_quantity(context->evaluation,context->guide,source->key,&value->num);
}
static bool reference_linear_result(GeoLinearResult result,GeoLinearMode mode,const char *expression,Coord *out)
{
    if(result.status==GEO_LINEAR_ARITHMETIC&&mode==GEO_LINEAR_EXACT_INTEGER_FINAL)
        return parameter_exact_status(result.exact_status);
    if(result.status==GEO_LINEAR_NOT_INTEGER)
        return parameter_fail("I38 GEOMETRY: %s must resolve to integer mm (got %lld/%lld)",expression,(long long)result.value.num,(long long)result.value.den);
    if(result.status==GEO_LINEAR_OK||result.status==GEO_LINEAR_RANGE)*out=result.value.num;
    return result.status==GEO_LINEAR_OK;
}
static bool reference_eval_text(ReferenceEval *ctx,const GuideLine *g,const char *expression,Coord *out)
{
    g_parameter_error[0]=0;GeoLinearExpression compiled;
    (void)reference_compile_text(expression,&compiled);
    AppLinearContext context={ctx,g};
    GeoLinearResult result=geo_linear_evaluate(&compiled,reference_resolve_linear,&context);
    return reference_linear_result(result,compiled.mode,expression,out);
}

static bool reference_eval_expression(ReferenceEval *ctx, const GuideLine *g, Coord *out)
{
    g_rule_reference_error[0]=0;
    return reference_eval_text(ctx,g,app_guide_expression(ctx->world,g->id),out);
}

static bool reference_compute_datum(ReferenceEval *ctx,size_t i,GeoAxisPosition *out)
{
    World *world=ctx->world;const GeoDatum *d=geo_datums_at(&world->geo.datum_planes,i);
    if(ctx->use_current_values){*out=(GeoAxisPosition){d->position,{false,0,d->axis}};return true;}
    GeoDatum definition;if(!geo_linear_definition_sources_datum(ctx->linear_definition_sources,d->id,&definition))return false;
    const char *expression=app_datum_expression(world,d->id);
    AppLinearContext context={ctx,NULL};g_parameter_error[0]=0;
    GeoLinearResult result=geo_datums_evaluate_definition(&world->geo.datum_planes,i,&definition,reference_resolve_linear,&context);
    Coord position;
    if(!reference_linear_result(result,definition.expression.mode,expression,&position)){
        char msg[256];if(g_parameter_error[0])snprintf(msg,sizeof msg,"datum %u: %s",d->id,g_parameter_error);else snprintf(msg,sizeof msg,"datum %u: missing spec, bare mm, unsupported reference or rational overflow",d->id);
        return reference_issue(0,"D6c/I7a","axis X/Y/Z and exact spec-only expression within D1",msg);
    }
    *out=(GeoAxisPosition){position,{false,0,definition.axis}};
    return true;
}
static bool reference_eval_datums(ReferenceEval *ctx)
{
    bool ok=true;
    for(size_t i=0;i<geo_datums_count(&ctx->world->geo.datum_planes);++i)
        if(!reference_eval_datum(ctx,i))ok=false;
    return ok;
}

static bool reference_compute_guide(ReferenceEval *ctx, size_t i,GeoAxisPosition *out)
{
    World *world=ctx->world;const GeoGuide *g=geo_guides_at(&world->geo.guide_lines,i);
    if(ctx->use_current_values){*out=(GeoAxisPosition){g->offset,{true,g->placement_id,g->direction==GUIDE_ALONG_V?0:1}};return true;}
    GeoGuide definition;if(!geo_linear_definition_sources_guide(ctx->linear_definition_sources,g->id,&definition))return false;g=&definition;
    const PlacementSurface *p=world_find_placement(world,g->placement_id);
    GeoFrame source_frame;if(p&&!reference_placement_frame(ctx,p->id,&source_frame))return false;
    const char *expression=app_guide_expression(world,g->id);
    if(g->source==GUIDE_DATUM){
        if(!p)return false;
        const GeoDatum *d=geo_datums_find(&world->geo.datum_planes,g->datum_id);GeoDatum actual_datum;
        if(d){
            size_t at=(size_t)(d-geo_datums_values(&world->geo.datum_planes));
            GeoAxisPosition position;if(!reference_datum_position(ctx,at,&position)||position.context.has_placement||position.context.axis<0||position.context.axis>2)return false;
            memset(&actual_datum,0,sizeof actual_datum);actual_datum.id=d->id;actual_datum.axis=position.context.axis;actual_datum.position=position.coordinate;d=&actual_datum;
        }
        GeoGuideResult result=geo_guides_evaluate_definition(&world->geo.guide_lines,i,g,&source_frame,d,NULL,NULL);
        if(result.status==GEO_GUIDE_MISSING_DATUM)return reference_issue(0,"I7a/I9","existing datum","datum guide has missing source");
        if(result.intersection==GEO_DATUM_INTERSECTION_COINCIDENT||result.intersection==GEO_DATUM_INTERSECTION_PARALLEL){
            char msg[160];snprintf(msg,sizeof msg,"guide %u datum %u: %s",g->id,d->id,
                result.intersection==GEO_DATUM_INTERSECTION_COINCIDENT?"coincident planes have no unique line":"parallel planes do not intersect");
            return reference_issue(0,"I7a","one unique intersection line",msg);
        }
        if(result.status!=GEO_GUIDE_OK)return reference_issue(0,"D1/I7a","derived local position within D1","datum intersection outside supported coordinate range");
        const GeoGuide *computed=geo_guides_at(&world->geo.guide_lines,i);
        *out=(GeoAxisPosition){computed->offset,{true,g->placement_id,computed->direction==GUIDE_ALONG_V?0:1}};
        return true;
    }
    bool ok=false;
    if(p){
        g_rule_reference_error[0]=0;g_parameter_error[0]=0;
        AppLinearContext context={ctx,g};
        GeoGuideResult result=geo_guides_evaluate_definition(&world->geo.guide_lines,i,g,&source_frame,NULL,reference_resolve_linear,&context);
        Coord value;ok=reference_linear_result(result.linear,g->expression.mode,expression,&value);
        if(ok)*out=(GeoAxisPosition){value,{true,g->placement_id,g->direction==GUIDE_ALONG_V?0:1}};
    }
    if(!ok){
        char message[256];if(g_rule_reference_error[0])snprintf(message,sizeof message,"guide %u: %.210s",g->id,g_rule_reference_error);else if(g_parameter_error[0])snprintf(message,sizeof message,"guide %u: %s",g->id,g_parameter_error);else snprintf(message,sizeof message,"guide %u: invalid/missing reference, axis/surface mismatch, cycle or rational overflow: %.120s",g->id,expression);
        utf8_trim_tail(message);
        return reference_issue(0,"D6a/I7/I9","existing same-surface/axis references; acyclic exact rational expression",message);
    }
    return true;
}

static bool reference_face_parse(const char *s, ReferenceFace *r)
{
    memset(r,0,sizeof *r); r->hole=-1;
    if(!strncmp(s,"key-hex:",8)) {
        s+=8;size_t n=strlen(s);if(!n||n%2||n/2>=sizeof r->key)return false;
        for(size_t i=0;i<n/2;++i){unsigned char byte=0;for(int k=0;k<2;++k){char c=s[2*i+k];int x=c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:c>='A'&&c<='F'?c-'A'+10:-1;if(x<0)return false;byte=(unsigned char)(byte*16+x);}if(!byte)return false;r->key[i]=(char)byte;}
        r->kind=2;return true;
    }
    if (s[0]=='t') { r->kind=1; return parse_u32(s+1,&r->timber); }
    return parse_edge_ref(s,&r->hole,&r->edge);
}
static void reference_face_format(FILE *out, const ReferenceFace *r)
{
    if(r->kind==2){fputs("key-hex:",out);for(const unsigned char *c=(const unsigned char*)r->key;*c;++c)fprintf(out,"%02x",*c);}
    else if (r->kind==1) fprintf(out,"t%u",r->timber);
    else if (r->hole>=0) fprintf(out,"h%de%d",r->hole,r->edge);
    else fprintf(out,"e%d",r->edge);
}

#include "../geometry-templates/woodworking/native/member_reference.h"
/* Each invocation owns its DTO scratch. Recursive K source evaluation uses
 * the existing ReferenceEval and never borrows another invocation's cache. */
typedef struct {
    PlacementSurface placement;SpaceBoundarySurface boundary,effective;
    const SpaceBoundarySurface *boundary_view;
} AppMemberPlacementScratch;
typedef struct {
    ReferenceEval *evaluation;World *world;AppMemberPlacementScratch *geometry;
} AppMemberReferenceContext;
static bool app_member_reference_at(void *user,size_t i,WoodMemberReferenceFact *out)
{
    AppMemberReferenceContext *c=user;World *w=c->world;if(i>=w->wood.timber_count)return false;
    const TimberAnchor *a=&w->wood.anchors[i];TimberAnchor authored;out->member=w->wood.timbers[i];out->wanted=c->evaluation&&c->evaluation->wanted[i];
    if(c->evaluation&&!c->evaluation->use_current_values){WoodMemberDefinition definition;
        if(!reference_member_definition_read(c->evaluation,i,out->member.id,&definition)||
           !reference_member_anchor_read(c->evaluation,i,out->member.id,&authored))return false;
        out->member.role=definition.role;out->member.cut_priority=definition.priority;out->member.auto_length=definition.auto_length;a=&authored;
    }
    out->anchor=(WoodMemberReference){.placement_id=a->placement_id,.anchor_kind=a->anchor_kind,.length_direction=a->length_direction,.depth_side=a->depth_side,
        .ref_grid=a->ref_grid,.ref_grid_axis=a->ref_grid_axis,.ref_grid_index=a->ref_grid_index,.ref_grid_has_band=a->ref_grid_has_band,.ref_grid_band=a->ref_grid_band,
        .ref_rule=a->ref_rule,.ref_hole=a->ref_hole,.ref_edge=a->ref_edge,.has_through=a->has_through,.through=a->through,
        .ref_guide=a->ref_guide,.ref_timber=a->ref_timber,.ref_is_timber=a->ref_is_timber,.order=a->order,.has_between=a->has_between};
    memcpy(out->anchor.ref_derived_key,a->ref_derived_key,sizeof out->anchor.ref_derived_key);
    for(int k=0;k<2;++k){const ReferenceFace *r=&a->between[k];WoodMemberReferenceFace *d=&out->anchor.between[k];
        d->kind=r->kind;d->hole=r->hole;d->edge=r->edge;d->timber=r->timber;memcpy(d->key,r->key,sizeof d->key);}
    return true;
}
static bool app_member_reference_guide(void *user,size_t i,WoodMemberGuideFact *out)
{
    AppMemberReferenceContext *c=user;const GuideLine *g=geo_guides_at(&c->world->geo.guide_lines,i);if(!g)return false;
    if(c->evaluation&&c->evaluation->guide_values_valid[i]){GeoAxisPosition value=c->evaluation->guide_values[i];
        *out=(WoodMemberGuideFact){g->id,value.context.placement,value.context.axis==0,value.coordinate};return true;}
    *out=(WoodMemberGuideFact){g->id,g->placement_id,g->direction==GUIDE_ALONG_V,g->offset};return true;
}
static bool app_member_reference_placement(void *user,uint32_t id,WoodMemberPlacementFact *out)
{
    AppMemberReferenceContext *c=user;
    const SpaceBoundarySurface *b;
    if(c->evaluation){if(!reference_host_read(c->evaluation,id,&c->geometry->placement,&c->geometry->boundary,&b))return false;}
    else{if(!app_placement_read(c->world,id,&c->geometry->placement))return false;
        b=app_placement_boundary(c->world,&c->geometry->placement,&c->geometry->boundary);}
    c->geometry->boundary_view=placement_effective_boundary(&c->geometry->placement,b,&c->geometry->effective);
    *out=(WoodMemberPlacementFact){id,c->geometry->placement.frame,c->geometry->placement.derived_fill_id!=0,c->geometry->placement.derived_h};return true;
}
static bool app_member_reference_grid(void *user,uint32_t id,WoodMemberGridFact *out)
{
    AppMemberReferenceContext *c=user;const ReferenceGrid *g=world_find_grid(c->world,id);if(!g)return false;
    WoodGridApplication definition;
    if(c->evaluation&&!c->evaluation->use_current_values){if(!reference_grid_definition(c->evaluation,id,&definition))return false;g=&definition;}
    *out=(WoodMemberGridFact){g->id,g->placement_id,g->is_subgrid};return true;
}
static bool app_member_reference_grid_line(void *user,const WoodMemberReference *a,Coord *out,char *err,size_t cap)
{
    AppMemberReferenceContext *c=user;World *w=c->world;const ReferenceGrid *g=world_find_grid(w,a->ref_grid);
    if(c->evaluation&&!c->evaluation->use_current_values)
        return wood_grid_sources_line(c->evaluation->grid_sources,a->ref_grid,a->placement_id,a->ref_grid_axis,a->ref_grid_index,true,a->ref_grid_has_band,a->ref_grid_band,out,NULL,err,cap);
    return grid_anchor_line_coord(w->wood.grid_applications.items,w->wood.grid_applications.count,g,&c->geometry->placement,c->geometry->boundary_view,a->ref_grid_axis,a->ref_grid_index,a->ref_grid_has_band,a->ref_grid_band,out,err,cap);
}
static bool app_member_reference_grid_scope(void *user,uint32_t id,SurfaceRegion2 *out,char *err,size_t cap)
{
    AppMemberReferenceContext *c=user;World *w=c->world;const ReferenceGrid *g=world_find_grid(w,id);
    if(c->evaluation&&!c->evaluation->use_current_values)return wood_grid_sources_cell(c->evaluation->grid_sources,id,out,err,cap);
    return grid_cell_bounds(w->wood.grid_applications.items,w->wood.grid_applications.count,g,&c->geometry->placement,c->geometry->boundary_view,out,err,cap);
}
static bool app_member_reference_rule(void *user,const GeoGridRuleLineRef *ref,uint32_t pid,Coord *out,SurfaceRegion2 *scope,char *err,size_t cap)
{AppMemberReferenceContext *c=user;return c->evaluation&&!c->evaluation->use_current_values?
    wood_grid_sources_rule_line(c->evaluation->grid_sources,ref,pid,out,scope,err,cap):grid_rule_line(c->world,ref,pid,out,scope,err,cap);}
static bool app_member_reference_footprint(void *user,size_t i,uint32_t pid,SurfaceRegion2 *out)
{AppMemberReferenceContext *c=user;
 if(c->evaluation)return reference_member_footprint(c->evaluation,i,pid,out);
 return timber_a0_footprint_uv(&c->geometry->placement,&c->world->wood.timbers[i],&c->world->wood.anchors[i],out);}
static bool app_member_reference_key(void *user,uint32_t pid,const char *key,int *hole,int *edge,char *err,size_t cap)
{
    AppMemberReferenceContext *c=user;(void)pid;
    if(c->evaluation?reference_derived_resolve(c->evaluation,&c->geometry->placement,key,hole,edge):dp_edge_resolve(c->world,&c->geometry->placement,key,hole,edge))return true;
    snprintf(err,cap,"%s",g_engineering_error);return false;
}
static WoodMemberEdgeStatus app_member_reference_edge(void *user,uint32_t pid,int hole,int edge,WoodMemberEdgeFact *out)
{
    AppMemberReferenceContext *c=user;(void)pid;const PlacementSurface *p=&c->geometry->placement;
    const SpaceBoundarySurface *b=c->geometry->boundary_view;PolygonLoop2 rect;const PolygonLoop2 *loop;
    if(p->derived_fill_id){size_t component=hole<0?(size_t)edge/POLY_MAX_VERTICES:(size_t)hole/POLY_MAX_HOLES;
        b=&p->components[component];c->geometry->boundary_view=b;if(hole<0)edge%=POLY_MAX_VERTICES;else hole%=POLY_MAX_HOLES;}
    if(!b){if(hole>=0)return WOOD_MEMBER_EDGE_NO_DOMAIN_HOLE;placement_outline(p,NULL,&rect);loop=&rect;}
    else{if(hole>=(int)b->hole_count)return WOOD_MEMBER_EDGE_MISSING_HOLE;loop=hole<0?&b->outline:&b->holes[hole];}
    if(edge<0||!loop_get_edge_segment(loop,(size_t)edge,&out->segment)||!loop_edge_outward_normal(loop,(size_t)edge,&out->outward))return WOOD_MEMBER_EDGE_MISSING;
    out->hole=hole;return WOOD_MEMBER_EDGE_OK;
}
static bool app_member_reference_evaluate(void *user,size_t i,GeoDependencyKind relation)
{AppMemberReferenceContext *c=user;return reference_eval_timber_relation(c->evaluation,i,relation);}
static bool app_member_reference_evaluate_guide(void *user,size_t i)
{AppMemberReferenceContext *c=user;return reference_eval_guide(c->evaluation,i);}
static bool app_member_reference_span(void *user,uint32_t pid,const WoodMemberSpanRequest *r,Coord *start,Coord *end,char *err,size_t cap)
{
    AppMemberReferenceContext *c=user;(void)pid;return resolve_auto_span_for_member(c->world,&c->geometry->placement,c->geometry->boundary_view,r->along_v,r->cross_lo,r->cross_hi,
        r->contact,r->contact_lo,r->contact_hi,r->through,r->through_at,r->between?r->stops:NULL,r->scoped?&r->scope:NULL,start,end,err,cap,r->self)==SPAN_OK;
}
static bool app_member_reference_primary(void *user,uint32_t pid,const WoodMember *member,bool along,char *err,size_t cap)
{AppMemberReferenceContext *c=user;return surface_primary_axis_check(c->world,pid,member,along,err,cap);}
static bool app_member_reference_end(void *user,uint32_t pid,const WoodMember *member,const WoodMemberSpanRequest *r,Coord start,Coord end,const SurfaceRegion2 *rect,char *err,size_t cap)
{
    AppMemberReferenceContext *c=user;(void)pid;const SpaceBoundarySurface *selected=placement_boundary_for_rect(&c->geometry->placement,c->geometry->boundary_view,rect);
    return app_reference_end_faces(c->world,&c->geometry->placement,selected,member,r->along_v,start,end,r->cross_lo,r->cross_hi,err,cap);
}
static bool app_member_reference_boundary(void *user,uint32_t pid,const WoodMember *member,const WoodMemberSpanRequest *r,Coord start,Coord end,const SurfaceRegion2 *rect,char *err,size_t cap)
{
    AppMemberReferenceContext *c=user;(void)pid;const SpaceBoundarySurface *selected=placement_boundary_for_rect(&c->geometry->placement,c->geometry->boundary_view,rect);
    return timber_boundary_role_check(&c->geometry->placement,selected,member,r->along_v,start,end,r->cross_lo,r->cross_hi,err,cap);
}
static bool app_member_reference_place(void *user,uint32_t pid,WoodMember *member,SurfacePoint2 uv,int direction,int depth)
{AppMemberReferenceContext *c=user;(void)pid;return timber_place_a0_on_surface(member,&c->geometry->placement,c->geometry->boundary_view,uv,(SurfaceDirection)direction,(SurfaceDepthSide)depth);}
static void app_member_reference_write(void *user,size_t i,const WoodMember *member,SurfacePoint2 uv)
{AppMemberReferenceContext *c=user;c->world->wood.timbers[i]=*member;c->world->wood.anchors[i].uv=uv;}
static bool app_member_reference_issue(void *user,uint32_t id,const char *clause,const char *expected,const char *actual)
{(void)user;return reference_issue(id,clause,expected,actual);}
static size_t app_member_reference_issue_count(void *user)
{(void)user;return g_reference_issue_count;}
static void app_member_reference_first_error(void *user,const char *error)
{(void)user;set_revalidate_error(error);}
static WoodMemberReferenceContext app_member_reference_context(AppMemberReferenceContext *c)
{
    return (WoodMemberReferenceContext){.user=c,.use_current_values=c->evaluation&&c->evaluation->use_current_values,
        .member_count=c->world->wood.timber_count,.guide_count=geo_guides_count(&c->world->geo.guide_lines),
        .member_at=app_member_reference_at,.guide_at=app_member_reference_guide,.placement=app_member_reference_placement,
        .grid=app_member_reference_grid,.grid_line=app_member_reference_grid_line,.grid_scope=app_member_reference_grid_scope,.rule_line=app_member_reference_rule,
        .member_footprint=app_member_reference_footprint,.resolve_key=app_member_reference_key,.edge=app_member_reference_edge,
        .evaluate_member=app_member_reference_evaluate,.evaluate_guide=app_member_reference_evaluate_guide,
        .span=app_member_reference_span,.primary_axis=app_member_reference_primary,.end_faces=app_member_reference_end,.boundary_role=app_member_reference_boundary,
        .place=app_member_reference_place,.write=app_member_reference_write,.issue=app_member_reference_issue,.issue_count=app_member_reference_issue_count,.first_error=app_member_reference_first_error};
}
static bool reference_place_geometry(ReferenceEval *evaluation,World *w,size_t ti)
{
    AppMemberPlacementScratch scratch;AppMemberReferenceContext c={0};c.evaluation=evaluation;c.world=w;c.geometry=&scratch;
    WoodMemberReferenceContext context=app_member_reference_context(&c);ReferenceEval *previous=g_reference_active;
    g_reference_active=evaluation;bool ok=wood_member_reference_place(&context,ti);g_reference_active=previous;
    return ok&&(!evaluation||!evaluation->source_failure);
}
/* H 轉接：僅以權威來源更新尺寸快取；放置策略仍委由 W。 */
static bool app_member_reference_materialize_dimensions(ReferenceEval *ctx,size_t i)
{
    if(!ctx->use_current_values&&!app_assembly_saved_dimensions(ctx->world,ctx->world->wood.timbers[i].id)&&ctx->wanted[i]){
        Timber *member=&ctx->world->wood.timbers[i];bool owned;
        if(!reference_member_owned(ctx,member->id,&owned))return false;
        if(owned){
            GeoCoord width,depth;
            if(!wood_assembly_sources_owned_dimensions(ctx->assembly_sources,member->id,&width,&depth))return false;
            member->size_a=width;member->size_b=depth;
        }else{
            WoodEngineeringContext engineering=app_eng_context(ctx->world);
            wood_engineering_sources_bind(ctx->engineering_sources,&engineering);
            for(int field=0;field<2;++field){EngTarget target={1,member->id,0,field};
                const EngBinding *binding=wood_eng_binding(&engineering,&target);GeoCoord dimension;
                if(binding){if(!wood_eng_effective(&engineering,binding,&dimension,NULL,0))return false;}
                else if(!wood_definition_sources_dimension(ctx->definition_sources,member->id,field!=0,&dimension))return false;
                if(field)member->size_b=dimension;else member->size_a=dimension;
            }
        }
    }
    return true;
}
static bool reference_compute_timber(ReferenceEval *ctx,size_t i)
{
    if(!app_member_reference_materialize_dimensions(ctx,i))return false;
    AppMemberReferenceContext c={0};c.evaluation=ctx;c.world=ctx->world;WoodMemberReferenceContext context=app_member_reference_context(&c);bool place=false;if(!wood_member_reference_compute(&context,i,&place))return false;return !place||reference_place_geometry(ctx,ctx->world,i);
}

#include "../geometry-app/native/reference_sources.inc"

/* I8a: report independent failures across the whole reconstructed world. */
static bool reference_check_all(const World *w)
{
    AppFootprintMemo footprints={0};app_footprint_memo_begin(&footprints,w);
    bool ok=true;
    for (size_t i=0;i<w->wood.timber_count;++i) {
        const Timber *t=&w->wood.timbers[i];TimberAnchor actual_anchor;const TimberAnchor *a=&actual_anchor;
        if (!t->placed) continue;
        PlacementSurface placement;SpaceBoundarySurface boundary;const SpaceBoundarySurface *host_boundary;SurfaceRegion2 f;
        if(!app_reference_member_anchor(w,i,&actual_anchor)||!app_reference_host_read(w,a->placement_id,&placement,&boundary,&host_boundary)||
           !app_footprint_memo_read(&footprints,i,a->placement_id,&f)) { ok=reference_issue(t->id,"I5","valid footprint on existing surface","missing footprint"); continue; }
        const PlacementSurface *p=&placement;
        const SpaceBoundarySurface *b=placement_boundary_for_rect(p,host_boundary,&f);
        bool along=a->length_direction==SURFACE_DIRECTION_POS_V || a->length_direction==SURFACE_DIRECTION_NEG_V;
        Coord lo=along?f.min_u:f.min_v,hi=along?f.max_u:f.max_v;
        Coord ends[2]={along?f.min_v:f.min_u,along?f.max_v:f.max_u};
        StopFace faces[STOP_FACE_MAX]; size_t nf=collect_stop_faces(w,p,b,along,t,faces,STOP_FACE_MAX);
        for (int k=0;k<2;++k) {
            size_t hits=count_legal_stops(faces,nf,ends[k],lo,hi);
            WoodBoundaryEndAdmission admission=WOOD_BOUNDARY_END_ORDINARY;
            if(!app_reference_boundary_end_policy(w,p,b,t,along,ends[0],ends[1],lo,hi,k,faces,nf,NULL,&admission)){
                reference_issue(t->id,"I8","ordered endpoint source facts","boundary endpoint facts unavailable");ok=false;continue;
            }
            char detail[256]="";
            if(!wood_contact_end_support_check(admission,hits,a->has_between,detail,sizeof detail)){
                char actual[512];snprintf(actual,sizeof actual,"end %d at %lld mm, cross [%lld,%lld], legal stops=%u; %s",k,(long long)ends[k],(long long)lo,(long long)hi,(unsigned)hits,detail);
                reference_issue(t->id,"R6(d)/I6","full-width FIXED stop or approved boundary fixed-end exception",actual);ok=false;
            }
        }
        char err[256];
        if (!app_reference_end_faces(w,p,b,t,along,ends[0],ends[1],lo,hi,err,sizeof err)) { reference_issue(t->id,"I19/I22","higher-priority endpoint supports or defined exception",err); ok=false; }
        if (!timber_boundary_role_check(p,b,t,along,ends[0],ends[1],lo,hi,err,sizeof err)) { reference_issue(t->id,"I20/R18","full fixed-edge coverage for boundary",err); ok=false; }
        for (size_t j=i+1;j<w->wood.timber_count;++j) {
            SurfaceRegion2 other;TimberAnchor other_anchor;
            if(!w->wood.timbers[j].placed)continue;
            if(!app_reference_member_anchor(w,j,&other_anchor)){ok=false;continue;}
            if(other_anchor.placement_id!=a->placement_id)continue;
            if(!app_footprint_memo_read(&footprints,j,a->placement_id,&other)){ok=false;continue;}
            if (uv_rects_overlap(f.min_u,f.min_v,f.max_u,f.max_v,other.min_u,other.min_v,other.max_u,other.max_v)) {
                char actual[180]; snprintf(actual,sizeof actual,"positive-area intersection with timber %u",w->wood.timbers[j].id);
                reference_issue(t->id,"I11","zero positive-area overlap",actual); ok=false;
            }
        }
    }
    return ok;
}

static void reference_sources_owned_free(void *opaque)
{ReferenceEval *ctx=opaque;reference_sources_dispose(ctx);free(ctx);}
static ReferenceEval *reference_sources_begin_candidate(World *w)
{
    if(!g_active_app_candidate||w!=&g_active_app_candidate->after)return NULL;
    AppCandidate *owner=g_active_app_candidate->control;
    GeoEvalContext *sources=geo_candidate_sources(app_candidate_core(owner));
    app_candidate_set_evaluation_state(owner,NULL,NULL);
    if(!sources||!geo_eval_reset(sources))return NULL;
    ReferenceEval *ctx=calloc(1,sizeof *ctx);if(!ctx)return NULL;
    ctx->world=w;ctx->sources=sources;ctx->sources_borrowed=true;
    app_candidate_set_evaluation_state(owner,ctx,reference_sources_owned_free);
    return reference_sources_ensure(ctx)?ctx:NULL;
}
/* Start the shared graph at the first evaluable definition phase. The later
 * guide/member pass retains this context and all parameter AST edges. */
static bool reference_parameters_rebuild(World *w,char *error,size_t cap)
{
    if(!g_active_app_candidate||w!=&g_active_app_candidate->after)return parameters_rebuild(w,error,cap);
    g_parameter_error[0]=0;GeoParameterError issue;bool ok;
    if(w->app.parameter_loading)ok=parameter_fail("I39: unterminated parameter block");
    else{
        ReferenceEval *ctx=reference_sources_begin_candidate(w);
        if(!ctx)ok=parameter_fail("UNSUPPORTED/CAPACITY: parameter evaluation memory");
        else{ok=geo_parameter_sources_rebuild(ctx->parameter_sources,&issue);if(!ok)parameter_kernel_error(w,&issue);}
    }
    if(!ok)snprintf(error,cap,"%s",g_parameter_error);return ok;
}
static bool reference_rebuild(World *w)
{
    ReferenceEval local={0},*ctx=&local;bool persistent=false;
    if(g_active_app_candidate&&w==&g_active_app_candidate->after){
        ctx=app_candidate_evaluation_state(g_active_app_candidate->control);
        if(!ctx||ctx->world!=w)ctx=reference_sources_begin_candidate(w);
        if(!ctx)return false;persistent=true;
    }
    ctx->world=w;bool ok=true;
    geo_guides_reset_resolved(&w->geo.guide_lines);
    for (size_t i=0;i<w->wood.timber_count;++i) { ctx->wanted[i]=w->wood.timbers[i].placed; w->wood.timbers[i].placed=false; }
    if (!reference_eval_datums(ctx)) { if (g_reference_capturing) g_reference_trial=*w; if(!persistent)reference_sources_dispose(ctx); return false; }
    /* Timbers drive guide evaluation as needed; remaining guides are then evaluated. */
    for (size_t i=0;i<w->wood.timber_count;++i) if (ctx->wanted[i] && !reference_eval_timber(ctx,i)) ok=false;
    for (size_t i=0;i<geo_guides_count(&w->geo.guide_lines);++i) if (!reference_eval_guide(ctx,i)) ok=false;
    if (g_reference_capturing) g_reference_trial=*w;
    if(!persistent)reference_sources_dispose(ctx);return ok;
}

static bool reference_checked(const char *p,int n,World *w)
{
    if (world_revalidate(w)) return true;
    scene_error(p,n,g_revalidate_error[0]?g_revalidate_error:"I8: reference validation failed"); return false;
}
static bool apply_spec_line(const char *p,int n,char **tokens,int count,World *w)
{
    (void)count; Coord value;
    if (!reference_name(tokens[1]) || !parse_coord(tokens[2],&value)) {
        scene_error(p,n,"D6b: spec requires a unique name and integer mm in D1 range"); return false;
    }
    if (!geo_named_values_put(&w->geo.named_values,tokens[1],value)) {
        scene_error(p,n,"D6b: spec capacity exceeded"); return false;
    }
    return reference_checked(p,n,w);
}
static bool apply_datum_line(const char *p,int n,char **tokens,int count,World *w)
{
    AppDatumInput d={0};
    if (!parse_u32(tokens[1],&d.id) || strlen(tokens[2])!=1 ||
        !strchr("xyzXYZ",tokens[2][0]) || !reference_expression(tokens,3,count,d.expression)) {
        scene_error(p,n,"D6c: datum id x|y|z spec-only position expression"); return false;
    }
    d.axis=tolower((unsigned char)tokens[2][0])=='x'?0:tolower((unsigned char)tokens[2][0])=='y'?1:2;
    size_t i=0;while(i<geo_datums_count(&w->geo.datum_planes)&&geo_datums_at(&w->geo.datum_planes,i)->id!=d.id)++i;
    if(i==WORLD_MAX_DATUMS){scene_error(p,n,"D6c: datum capacity exceeded");return false;}
    GeoLinearExpression compiled;(void)reference_compile_text(d.expression,&compiled);
    if(!geo_datums_put(&w->geo.datum_planes,d.id,d.axis,&compiled)){scene_error(p,n,"D6c: datum capacity exceeded");return false;}
    memset(&w->app.datum_texts[i],0,sizeof w->app.datum_texts[i]);w->app.datum_texts[i].id=d.id;
    snprintf(w->app.datum_texts[i].expression,sizeof w->app.datum_texts[i].expression,"%s",d.expression);
    return reference_checked(p,n,w);
}
static bool apply_reference_guide(const char *p,int n,char **tokens,int count,World *w)
{
    GeoGuide g={0};char expression[REF_EXPR_MAX]="";int dir;
    if(!parse_u32(tokens[1],&g.id)||!parse_u32(tokens[2],&g.placement_id))return false;
    if(!strcmp(tokens[3],"datum")){
        if(count!=5||!parse_u32(tokens[4],&g.datum_id))return false;
        g.source=GUIDE_DATUM;
    }else{
        if(!lookup_keyword(tokens[3],GUIDE_DIRECTION_WORDS,&dir)||!reference_expression(tokens,4,count,expression))return false;
        g.direction=(GuideDirection)dir;
    }
    if(!app_guide_put(w,&g,expression)){scene_error(p,n,"D6: guide capacity exceeded");return false;}
    return reference_checked(p,n,w);
}
static bool apply_reference_move(const char *p,int n,char **tokens,int count,World *w)
{
    uint32_t id;if(!parse_u32(tokens[1],&id))return false;
    const GeoGuide *guide=geo_guides_find(&w->geo.guide_lines,id);
    if(guide){
        if(guide->source==GUIDE_DATUM){scene_error(p,n,"R5: shared guide cannot be moved locally; edit its datum or named spec");return false;}
        char expression[REF_EXPR_MAX];if(!reference_expression(tokens,2,count,expression)||!app_guide_put(w,guide,expression))return false;
        return reference_checked(p,n,w);
    }
    scene_error(p,n,"I9: move guide does not exist");return false;
}
static bool apply_reference_place(const char *p,int n,char **tokens,int count,World *w)
{
    uint32_t id,pid; int i=5;
    if (count<8 || !parse_u32(tokens[1],&id) || strcmp(tokens[2],"on") || !parse_u32(tokens[3],&pid)) return false;
    if (assembly_owned(w,id)) { scene_error(p,n,"I42: edit the owning assembly instance"); return false; }
    int ti=reference_timber_index(w,id);
    if (ti<0) { scene_error(p,n,"I9: place 指的角材不存在"); return false; }
    TimberAnchor a={0}; a.placement_id=pid; a.ref_hole=-1; a.span_mode=SPAN_AUTO;
    if (!strcmp(tokens[4],"at-line")) {
        if (i<count && !strcmp(tokens[i],"guide") && i+1<count) {
            a.anchor_kind=ANCHOR_AT_LINE; if (!parse_u32(tokens[i+1],&a.ref_guide)) return false; i+=2;
        } else if(i+7<count && !strcmp(tokens[i],"rule")) {
            GridRuleLineRef *r=&a.ref_rule; a.anchor_kind=ANCHOR_AT_RULE;
            if(!parse_u32(tokens[i+1],&r->grid_id) || !parse_u32(tokens[i+2],&r->system_id) ||
                !parse_u32(tokens[i+3],&r->rule_key) || !r->rule_key || !parse_i64(tokens[i+4],&r->cell[0]) ||
                !parse_i64(tokens[i+5],&r->cell[1]) || (strcmp(tokens[i+6],"u")&&strcmp(tokens[i+6],"v")) ||
                !parse_u32(tokens[i+7],&r->inner_index))return false;
            r->axis=!strcmp(tokens[i+6],"u")?0:1;i+=8;
        } else if (i+3<count && !strcmp(tokens[i],"grid")) {
            int64_t index; a.anchor_kind=ANCHOR_AT_GRID;
            if (!parse_u32(tokens[i+1],&a.ref_grid) || !parse_i64(tokens[i+3],&index) ||
                (strcmp(tokens[i+2],"u") && strcmp(tokens[i+2],"v"))) return false;
            const ReferenceGrid *grid=world_find_grid(w,a.ref_grid);
            if (!grid || (!grid->from_binding && (index<0 || index>=GRID_MAX_LINES))) {
                scene_error(p,n,"I13: the grid must exist; finite grid indices must be nonnegative and below 64"); return false;
            }
            a.ref_grid_axis=!strcmp(tokens[i+2],"u")?0:1; a.ref_grid_index=index; i+=4;
            if (i<count && !strcmp(tokens[i],"band")) {
                if (i+1>=count || !parse_i64(tokens[i+1],&a.ref_grid_band)) return false;
                a.ref_grid_has_band=true; i+=2;
            }
        } else { scene_error(p,n,"I13: at-line guide id | grid id u|v index"); return false; }
    } else if (!strcmp(tokens[4],"at-face")) {
        ReferenceFace r;
        if (!reference_face_parse(tokens[i++],&r)) {
            scene_error(p,n,"I13: 邊參照必須是 e索引、h孔e邊或 t角材"); return false;
        }
        a.anchor_kind=ANCHOR_AT_EDGE; a.ref_hole=r.hole; a.ref_edge=r.edge; a.ref_timber=r.timber; a.ref_is_timber=r.kind==1;
        if(r.kind==2)snprintf(a.ref_derived_key,sizeof a.ref_derived_key,"%s",r.key);
    } else { scene_error(p,n,"I12: 只允許 at-line / at-face；at、at-guides、at-grid、at-edge 已廢除"); return false; }
    if (i<count && !strcmp(tokens[i],"through")) {
        if (i+1>=count || !parse_coord(tokens[i+1],&a.through)) return false;
        a.has_through=true; i+=2;
    }
    if (i<count && !strcmp(tokens[i],"between")) {
        if (a.has_through) { scene_error(p,n,"R21: through 與 between 不能同時寫"); return false; }
        if (i+2>=count || !reference_face_parse(tokens[i+1],&a.between[0]) || !reference_face_parse(tokens[i+2],&a.between[1])) {
            scene_error(p,n,"D18: 擋面參照只認得 e索引、h孔e邊、t角材"); return false;
        }
        a.has_between=true; i+=3;
    }
    if (i+2!=count || !lookup_keyword(tokens[i],LENGTH_DIRECTION_WORDS,&a.length_direction) ||
        !lookup_keyword(tokens[i+1],DEPTH_SIDE_WORDS,&a.depth_side)) {
        scene_error(p,n,"place 缺少長度方向與深度側，或有多餘欄位"); return false;
    }
    a.order=w->wood.timbers[ti].placed?w->wood.anchors[ti].order:++w->app.next_order;
    w->wood.anchors[ti]=a; w->wood.timbers[ti].placed=true;
    return reference_checked(p,n,w);
}

/* D9/R4: emit declarations first, then reference nodes in evaluation order. */
static void reference_dump_guide(const World *w,FILE *out,size_t i,bool *done)
{
    if (done[i]) return;
    done[i]=true;
    const char *p=app_guide_expression(w,geo_guides_values(&w->geo.guide_lines)[i].id);
    while ((p=strstr(p,"guide:"))!=NULL) {
        char *end; unsigned long id=strtoul(p+6,&end,10);
        for (size_t j=0;j<geo_guides_count(&w->geo.guide_lines);++j) if (geo_guides_values(&w->geo.guide_lines)[j].id==id) reference_dump_guide(w,out,j,done);
        p=end>p?end:p+6;
    }
    const GuideLine *g=&geo_guides_values(&w->geo.guide_lines)[i];
    if (g->source==GUIDE_DATUM) fprintf(out,"guide %u %u datum %u\n",g->id,g->placement_id,g->datum_id);
    else fprintf(out,"guide %u %u %s %s\n",g->id,g->placement_id,g->direction==GUIDE_ALONG_U?"u":"v",app_guide_expression(w,g->id));
}
static bool reference_guide_ready(const World *w,size_t i,const bool *placed,unsigned depth)
{
    if (depth>WORLD_MAX_GUIDES) return false;
    const char *p=app_guide_expression(w,geo_guides_values(&w->geo.guide_lines)[i].id);
    while ((p=strstr(p,"timber:"))!=NULL) {
        char *end; unsigned long id=strtoul(p+7,&end,10);
        int ti=reference_timber_index(w,(uint32_t)id);
        if (ti>=0 && end[0]==':' && end[1]!='A' && end[1]!='B' && !placed[ti]) return false;
        p=end>p?end:p+7;
    }
    p=app_guide_expression(w,geo_guides_values(&w->geo.guide_lines)[i].id);
    while ((p=strstr(p,"guide:"))!=NULL) {
        char *end; unsigned long id=strtoul(p+6,&end,10);
        for (size_t j=0;j<geo_guides_count(&w->geo.guide_lines);++j)
            if (geo_guides_values(&w->geo.guide_lines)[j].id==id && !reference_guide_ready(w,j,placed,depth+1)) return false;
        p=end>p?end:p+6;
    }
    return true;
}
static void reference_dump(const World *w,FILE *out)
{
    bool gd[WORLD_MAX_GUIDES]={0},placed[WORLD_MAX_TIMBERS]={0};
    for (size_t i=0;i<geo_datums_count(&w->geo.datum_planes);++i)
        fprintf(out,"datum %u %c %s\n",geo_datums_at(&w->geo.datum_planes,i)->id,"xyz"[geo_datums_at(&w->geo.datum_planes,i)->axis],app_datum_expression(w,geo_datums_at(&w->geo.datum_planes,i)->id));
    for (size_t i=0;i<w->wood.timber_count;++i) {
        const Timber *t=&w->wood.timbers[i];
        if (engineering_dump_timber(w,t,out)) continue;
        assembly_owned_prefix(w,t->id,"timber",out);
        fprintf(out,"timber %u %lld %lld role %s",t->id,(long long)t->size_a,(long long)t->size_b,timber_role_name(t->role));
        if (t->role==TIMBER_ROLE_CUSTOM) fprintf(out," priority %lld",(long long)t->cut_priority);
        fputc('\n',out);
    }
    for (size_t k=0;k<=w->wood.timber_count;++k) {
        for (size_t i=0;i<geo_guides_count(&w->geo.guide_lines);++i) if (!gd[i] && reference_guide_ready(w,i,placed,0)) reference_dump_guide(w,out,i,gd);
        size_t at=w->wood.timber_count; uint64_t order=UINT64_MAX;
        for (size_t i=0;i<w->wood.timber_count;++i) if (w->wood.timbers[i].placed && !placed[i] && w->wood.anchors[i].order<order) { at=i; order=w->wood.anchors[i].order; }
        if (at==w->wood.timber_count) break;
        const Timber *t=&w->wood.timbers[at]; const TimberAnchor *a=&w->wood.anchors[at];
        assembly_owned_prefix(w,t->id,"place",out);
        fprintf(out,"place %u on %u ",t->id,a->placement_id);
        if (a->anchor_kind==ANCHOR_AT_LINE) fprintf(out,"at-line guide %u",a->ref_guide);
        else if (a->anchor_kind==ANCHOR_AT_GRID) {
            fprintf(out,"at-line grid %u %c %lld",a->ref_grid,a->ref_grid_axis==0?'u':'v',(long long)a->ref_grid_index);
            if (a->ref_grid_has_band) fprintf(out," band %lld",(long long)a->ref_grid_band);
        }
        else if(a->anchor_kind==ANCHOR_AT_RULE) {
            const GridRuleLineRef *r=&a->ref_rule;
            fprintf(out,"at-line rule %u %u %u %lld %lld %c %u",r->grid_id,r->system_id,r->rule_key,
                (long long)r->cell[0],(long long)r->cell[1],r->axis?'v':'u',r->inner_index);
        }
        else { ReferenceFace r={a->ref_derived_key[0]?2:a->ref_is_timber?1:0,a->ref_hole,a->ref_edge,a->ref_timber,{0}};snprintf(r.key,sizeof r.key,"%s",a->ref_derived_key); fputs("at-face ",out); reference_face_format(out,&r); }
        if (a->has_through) fprintf(out," through %lld",(long long)a->through);
        if (a->has_between) { fputs(" between ",out); reference_face_format(out,&a->between[0]); fputc(' ',out); reference_face_format(out,&a->between[1]); }
        const char *dirs[]={"+u","-u","+v","-v"};
        fprintf(out," %s %s\n",dirs[a->length_direction],a->depth_side==SURFACE_DEPTH_POSITIVE_NORMAL?"+n":"-n");
        const PlacementSurface *p=world_find_placement(w,a->placement_id); SurfaceRegion2 f; bool on=false,covers=false; int edge=-1;
        bool along=a->length_direction==SURFACE_DIRECTION_POS_V || a->length_direction==SURFACE_DIRECTION_NEG_V;
        SpaceBoundarySurface effective;
        const SpaceBoundarySurface *selected=NULL;
        if (p && timber_a0_footprint_uv(p,t,a,&f)) {selected=placement_boundary_for_rect(p,placement_effective_boundary(p,world_placement_boundary(w,p),&effective),&f);timber_role_props(selected,along,along?f.min_v:f.min_u,along?f.max_v:f.max_u,along?f.min_u:f.min_v,along?f.max_u:f.max_v,&on,&covers,&edge);}
        if(p&&p->derived_fill_id){char key[512];bool found=false;
            for(size_t c=0;c<p->component_count;++c)if(selected==&p->components[c]&&edge>=0)found=dp_edge_key(w,p,c,-1,(size_t)edge,key,sizeof key);
            fprintf(out,"# R18 角材 %u: onBoundary=%s coversEdge=%s boundaryEdge=%s\n",t->id,on?"true":"false",covers?"true":"false",found?key:"null");
        }else fprintf(out,"# R18 角材 %u: onBoundary=%s coversEdge=%s boundaryEdge=%d\n",t->id,on?"true":"false",covers?"true":"false",edge);
        placed[at]=true;
    }
}

/* R5: finite visible references within a caller-provided pick radius; no free offset. */
static bool reference_snap(World *w,uint32_t pid,GuideDirection dir,uint32_t exclude,Coord at,Coord radius,char *out)
{
    GuideLine probe={0}; probe.placement_id=pid; probe.direction=dir;
    ReferenceEval ctx={0}; ctx.world=w;ctx.use_current_values=true;
    for (size_t i=0;i<w->wood.timber_count;++i) ctx.wanted[i]=w->wood.timbers[i].placed;
    Coord best=radius+1; bool found=false;
    const PlacementSurface *p=world_find_placement(w,pid); if (!p) return false;
    const SpaceBoundarySurface *b=world_placement_boundary(w,p); char axis=dir==GUIDE_ALONG_V?'u':'v';
    enum { SNAP_MAX = WORLD_MAX_SPECS + WORLD_MAX_GUIDES + (POLY_MAX_HOLES+1)*POLY_MAX_VERTICES + WORLD_MAX_GRIDS*GRID_MAX_LINES + WORLD_MAX_TIMBERS*2 };
    char candidates[SNAP_MAX][REF_EXPR_MAX]; size_t n=0;
    for (size_t i=0;i<geo_named_values_count(&w->geo.named_values) && n<SNAP_MAX;++i) snprintf(candidates[n++],REF_EXPR_MAX,"spec:%s",geo_named_values_at(&w->geo.named_values,i)->name);
    for (size_t i=0;i<geo_guides_count(&w->geo.guide_lines) && n<SNAP_MAX;++i) if (geo_guides_values(&w->geo.guide_lines)[i].id!=exclude && geo_guides_values(&w->geo.guide_lines)[i].placement_id==pid && geo_guides_values(&w->geo.guide_lines)[i].direction==dir)
        snprintf(candidates[n++],REF_EXPR_MAX,"guide:%u",geo_guides_values(&w->geo.guide_lines)[i].id);
    PolygonLoop2 rect; placement_outline(p,b,&rect);
    for (int h=-1; h<(b?(int)b->hole_count:0); ++h) {
        const PolygonLoop2 *loop=h<0?&rect:&b->holes[h];
        for (size_t i=0;i<loop->count && n<SNAP_MAX;++i) {
            if (h<0) snprintf(candidates[n++],REF_EXPR_MAX,"vertex:v%u:%c",(unsigned)i,axis);
            else snprintf(candidates[n++],REF_EXPR_MAX,"vertex:h%dv%u:%c",h,(unsigned)i,axis);
        }
    }
    for (size_t i=0;i<w->wood.grid_applications.count;++i) if (w->wood.grid_applications.items[i].placement_id==pid) {
        const ReferenceGrid *grid=&w->wood.grid_applications.items[i];
        Coord coords[GRID_MAX_LINES]; int64_t indices[GRID_MAX_LINES]; size_t count=0; int a=axis=='u'?0:1;
        if (grid->axis[a].stagger_set) continue;
        if (grid->from_binding) {
            /* Snapping uses the actual nearest lattice lines, even when display
             * sampling hides them. It never snaps to a sample-array ordinal. */
            int64_t first;
            if (grid->lattice_step[a]>0 && grid_i64_add(grid->lattice_index[a],
                grid_floor_div(at-grid->lattice_base[a],grid->lattice_step[a]),&first)) {
                for (int side=0;side<2;++side) {
                    int64_t k;
                    if (grid_i64_add(first,side,&k) && grid_lattice_coord(grid,a,k,&coords[count]))
                        indices[count++]=k;
                }
            }
        } else if (!grid_sample_indices_in(w->wood.grid_applications.items,w->wood.grid_applications.count,grid,p,b,a,indices,coords,&count)) continue;
        for (size_t j=0;j<count && n<SNAP_MAX;++j)
            snprintf(candidates[n++],REF_EXPR_MAX,"grid:%u:%c:%lld",grid->id,axis,(long long)indices[j]);
    }
    for (size_t i=0;i<w->wood.timber_count && n+1<SNAP_MAX;++i) if (w->wood.timbers[i].placed && w->wood.anchors[i].placement_id==pid) {
        snprintf(candidates[n++],REF_EXPR_MAX,"timber:%u:%c:lo",w->wood.timbers[i].id,axis);
        snprintf(candidates[n++],REF_EXPR_MAX,"timber:%u:%c:hi",w->wood.timbers[i].id,axis);
    }
    for (size_t i=0;i<n;++i) {
        Coord value;
        g_rule_reference_error[0]=0;
        if (!reference_eval_text(&ctx,&probe,candidates[i],&value) || !guide_offset_in_range(p,b,dir,value)) continue;
        Coord distance=value>at?value-at:at-value;
        if (distance<best) {
            /* A reference back through the moving guide/timber is not a legal snap. */
            World candidate=*w; bool legal=true;
            if (exclude) {
                for (size_t j=0;j<geo_guides_count(&candidate.geo.guide_lines);++j) if (geo_guides_values(&candidate.geo.guide_lines)[j].id==exclude) {
                    if(!app_guide_put(&candidate,&geo_guides_values(&candidate.geo.guide_lines)[j],candidates[i])){legal=false;break;}
                    bool capture=g_reference_capturing; g_reference_capturing=false;
                    legal=world_revalidate(&candidate); g_reference_capturing=capture; break;
                }
            }
            if (legal) { best=distance; snprintf(out,REF_EXPR_MAX,"%s",candidates[i]); found=true; }
        }
    }
    reference_sources_dispose(&ctx);return found;
}
