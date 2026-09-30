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
    /* A rejected source has no validated downstream geometry yet. */
    for (size_t i=0;i<g_reference_trial.guide_count;++i) g_reference_trial.guides[i].resolved=false;
    for (size_t i=0;i<g_reference_trial.timber_count;++i) g_reference_trial.timbers[i].placed=false;
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
{
    if (!*name || strlen(name) >= SPEC_NAME_MAX) return false;
    for (const unsigned char *p=(const unsigned char *)name; *p; ++p)
        if (*p < 128 && !(isalnum(*p) || *p == '_')) return false;
    return true;
}

static Coord ref_gcd(Coord a, Coord b)
{
    if (a < 0) a = -a;
    while (b) { Coord r=a%b; a=b; b=r; }
    return a;
}
static bool ref_mul(Coord a, Coord b, Coord *out)
{
    if (a == INT64_MIN || b == INT64_MIN) return false;
    Coord aa=a<0?-a:a, bb=b<0?-b:b;
    if (bb && aa > INT64_MAX/bb) return false;
    *out=a*b; return true;
}
static bool ref_add(Coord a, Coord b, Coord *out)
{
    if ((b>0 && a>INT64_MAX-b) || (b<0 && a < -INT64_MAX-b)) return false;
    *out=a+b; return true;
}

typedef struct {
    World *world;
    unsigned char guides[WORLD_MAX_GUIDES], timbers[WORLD_MAX_TIMBERS];
    bool wanted[WORLD_MAX_TIMBERS];
} ReferenceEval;
static bool reference_eval_guide(ReferenceEval *, size_t);
static bool reference_eval_timber(ReferenceEval *, size_t);
static int reference_timber_index(const World *w, uint32_t id)
{
    for (size_t i=0;i<w->timber_count;++i) if (w->timbers[i].id==id) return (int)i;
    return -1;
}

static bool reference_quantity(ReferenceEval *ctx, const GuideLine *g, const char *text, Coord *out)
{
    World *w=ctx->world;
    /* D6c deliberately permits only named specs, without a placement context. */
    if (!g) {
        if (strncmp(text,"spec:",5)) return false;
        for (size_t i=0;i<w->spec_count;++i)
            if (!strcmp(w->specs[i].name,text+5)) { *out=w->specs[i].value; return true; }
        return false;
    }
    const PlacementSurface *p=world_find_placement(w,g->placement_id);
    if (!p) return false;
    SpaceBoundarySurface effective;
    const SpaceBoundarySurface *b=placement_effective_boundary(p,world_placement_boundary(w,p),&effective);
    int axis=g->direction==GUIDE_ALONG_V?0:1;
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
        for (size_t i=0;i<w->spec_count;++i)
            if (!strcmp(w->specs[i].name,part[1])) { *out=w->specs[i].value; return true; }
        return false;
    }
    if (n==2 && !strcmp(part[0],"guide") && parse_u32(part[1],&id)) {
        for (size_t i=0;i<w->guide_count;++i) {
            GuideLine *q=&w->guides[i];
            if (q->id!=id) continue;
            if (q->placement_id!=g->placement_id || !reference_eval_guide(ctx,i) ||
                q->direction!=g->direction) return false;
            *out=q->offset; return true;
        }
        return false;
    }
    if ((n==3 || n==4) &&
        (!strcmp(part[0],"grid") || !strcmp(part[0],"panel") || !strcmp(part[0],"gap"))) {
        if (!parse_u32(part[1],&id) || strcmp(part[2],axis==0?"u":"v")) return false;
        const ReferenceGrid *grid=world_find_grid(w,id);
        if (!grid || grid->placement_id!=g->placement_id) return false;
        if (!strcmp(part[0],"grid")) {
            int64_t k;
            return n==4 && parse_i64(part[3],&k) &&
                grid_line_coord_in(w->grids,w->grid_count,grid,p,b,axis,k,out,NULL,NULL,0);
        }
        if (n!=3 || grid->axis[axis].source != GRID_SRC_PANEL) return false;
        *out=!strcmp(part[0],"panel")?grid->axis[axis].panel:grid->axis[axis].gap;
        return true;
    }
    if (n>=3 && !strcmp(part[0],"timber") && parse_u32(part[1],&id)) {
        int ti=reference_timber_index(w,id);
        if (ti<0) return false;
        Timber *t=&w->timbers[ti];
        if (ctx->wanted[ti] && w->anchors[ti].placement_id!=g->placement_id) return false;
        if (n==3 && (!strcmp(part[2],"A") || !strcmp(part[2],"B"))) {
            *out=!strcmp(part[2],"A")?t->size_a:t->size_b; return true;
        }
        if (n!=4 || strcmp(part[2],axis==0?"u":"v") ||
            (strcmp(part[3],"lo") && strcmp(part[3],"hi")) ||
            !reference_eval_timber(ctx,(size_t)ti)) return false;
        SurfaceRegion2 f;
        if (!timber_a0_footprint_uv(p,t,&w->anchors[ti],&f)) return false;
        *out=axis==0 ? (!strcmp(part[3],"lo")?f.min_u:f.max_u)
                     : (!strcmp(part[3],"lo")?f.min_v:f.max_v);
        return true;
    }
    if (n==3 && (!strcmp(part[0],"edge") || !strcmp(part[0],"vertex"))) {
        if (strcmp(part[2],axis==0?"u":"v")) return false;
        PolygonLoop2 rect;
        const PolygonLoop2 *loop;
        int hole=-1, index=-1;
        if (!strcmp(part[0],"edge")) {
            if (!parse_edge_ref(part[1],&hole,&index)) return false;
        } else {
            char *q=part[1]; uint32_t hi=0,vi=0;
            if (*q=='h') {
                char *v=strchr(q,'v'); if (!v) return false;
                *v='\0'; if (!parse_u32(q+1,&hi) || hi>=POLY_MAX_HOLES) return false;
                hole=(int)hi; q=v;
            }
            if (*q!='v' || !parse_u32(q+1,&vi) || vi>=POLY_MAX_VERTICES) return false;
            index=(int)vi;
        }
        if (!b) { if (hole>=0) return false; placement_outline(p,NULL,&rect); loop=&rect; }
        else { if (hole >= (int)b->hole_count) return false; loop=hole<0?&b->outline:&b->holes[hole]; }
        if (index<0 || (size_t)index>=loop->count) return false;
        SurfacePoint2 a=loop->v[index], z=loop->v[(index+1)%loop->count];
        if (!strcmp(part[0],"edge") && (axis==0 ? a.u!=z.u : a.v!=z.v)) return false;
        *out=axis==0?a.u:a.v; return true;
    }
    return false; /* A naked number is never a reference. */
}

static bool reference_eval_text(ReferenceEval *ctx, const GuideLine *g, const char *expression, Coord *out)
{
    g_parameter_error[0]=0;
    const char *p=expression;
    Coord sum=0,den=1; int terms=0;
    bool exact=strstr(expression,"param:")!=NULL;
    ParamValue total={0,1,1};
    if (!*p) return false;
    while (*p) {
        int sign=1;
        if (*p=='+' || *p=='-') { if (*p=='-') sign=-1; ++p; }
        if (!*p || ++terms>64) return false;
        const char *end=p;
        while (*end) {
            if (*end=='+' || *end=='-') {
                /* A sign immediately after ':' belongs to the grid index;
                 * the next sign still separates expression terms. */
                if (!(end>p && end[-1]==':' && isdigit((unsigned char)end[1]))) break;
            }
            ++end;
        }
        size_t len=(size_t)(end-p); if (!len || len>=REF_EXPR_MAX) return false;
        char term[REF_EXPR_MAX]; memcpy(term,p,len); term[len]='\0';
        char *q=term, *star=strchr(term,'*'); Coord num=sign,d=1,value;
        if (star) {
            *star='\0'; q=star+1; char *slash=strchr(term,'/');
            if (slash) { *slash='\0'; if (!parse_i64(slash+1,&d) || d<=0) return false; }
            if (!parse_i64(term,&num) || num<0 || num==INT64_MIN) return false;
            num*=sign;
        }
        if(exact){
            ParamValue quantity={0,1,1},coefficient={num,d,0},term_value;ParameterRef ref={0};
            if(!strncmp(q,"param:",6)){
                if(!parameter_ref_parse(q,&ref)||!parameter_value(ctx->world,ref,&quantity))return false;
            }else{if(!reference_quantity(ctx,g,q,&quantity.num))return false;}
            if(!parameter_binary("mul",quantity,coefficient,&term_value)||!parameter_binary("add",total,term_value,&total))return false;
            p=end;continue;
        }
        if (!reference_quantity(ctx,g,q,&value)) return false;
        Coord k=ref_gcd(value,d); value/=k; d/=k;
        k=ref_gcd(num,d); num/=k; d/=k;
        if (!ref_mul(num,value,&num)) return false;
        k=ref_gcd(den,d); Coord x,y,newden;
        if (!ref_mul(sum,d/k,&x) || !ref_mul(num,den/k,&y) ||
            !ref_add(x,y,&sum) || !ref_mul(den,d/k,&newden)) return false;
        den=newden; k=ref_gcd(sum,den); sum/=k; den/=k;
        p=end;
    }
    if(exact){
        if(total.den!=1)return parameter_fail("I38 GEOMETRY: %s must resolve to integer mm (got %lld/%lld)",expression,(long long)total.num,(long long)total.den);
        *out=total.num;
    }else *out=sum/den - (sum<0 && sum%den!=0);
    return coord_in_range(*out);
}

static bool reference_eval_expression(ReferenceEval *ctx, const GuideLine *g, Coord *out)
{
    return reference_eval_text(ctx,g,g->expression,out);
}

static bool reference_eval_datums(ReferenceEval *ctx)
{
    bool ok=true;
    for (size_t i=0;i<ctx->world->datum_count;++i) {
        DatumPlane *d=&ctx->world->datums[i];
        if (d->axis<0 || d->axis>2 || !reference_eval_text(ctx,NULL,d->expression,&d->position)) {
            char msg[256];if(g_parameter_error[0])snprintf(msg,sizeof msg,"datum %u: %s",d->id,g_parameter_error);else snprintf(msg,sizeof msg,"datum %u: missing spec, bare mm, unsupported reference or rational overflow",d->id);
            reference_issue(0,"D6c/I7a","axis X/Y/Z and exact spec-only expression within D1",msg); ok=false;
        }
    }
    return ok;
}

static Coord datum_component(Vector3 v,int axis) { return axis==0?v.x:axis==1?v.y:v.z; }

/* D6c/I7a: solve in world coordinates, then transform the unique line to uv. */
static bool datum_guide_geometry(const World *w,const PlacementSurface *p,GuideLine *g)
{
    const DatumPlane *d=NULL;
    for (size_t i=0;i<w->datum_count;++i) if (w->datums[i].id==g->datum_id) d=&w->datums[i];
    if (!d) return reference_issue(0,"I7a/I9","existing datum","datum guide has missing source");
    Coord origin=d->axis==0?p->frame.origin.x:d->axis==1?p->frame.origin.y:p->frame.origin.z;
    Coord u=datum_component(p->frame.axis_u,d->axis),v=datum_component(p->frame.axis_v,d->axis);
    if (!u && !v) {
        char msg[160]; snprintf(msg,sizeof msg,"guide %u datum %u: %s",g->id,d->id,
            origin==d->position?"coincident planes have no unique line":"parallel planes do not intersect");
        return reference_issue(0,"I7a","one unique intersection line",msg);
    }
    g->direction=u?GUIDE_ALONG_V:GUIDE_ALONG_U;
    g->offset=(u?u:v)*(d->position-origin);
    if (!coord_in_range(g->offset)) return reference_issue(0,"D1/I7a","derived local position within D1","datum intersection outside supported coordinate range");
    return true;
}

static bool reference_eval_guide(ReferenceEval *ctx, size_t i)
{
    if (ctx->guides[i]==2) return true;
    if (ctx->guides[i]) return false;
    ctx->guides[i]=1;
    GuideLine *g=&ctx->world->guides[i]; Coord v;
    const PlacementSurface *p=world_find_placement(ctx->world,g->placement_id);
    if (g->source==GUIDE_DATUM) {
        if (!p || !datum_guide_geometry(ctx->world,p,g)) { ctx->guides[i]=3; return false; }
        g->resolved=true; ctx->guides[i]=2; return true;
    }
    if (!p || !reference_eval_expression(ctx,g,&v)) {
        ctx->guides[i]=3;
        char message[256];if(g_parameter_error[0])snprintf(message,sizeof message,"guide %u: %s",g->id,g_parameter_error);else snprintf(message,sizeof message,"guide %u: invalid/missing reference, axis/surface mismatch, cycle or rational overflow: %.120s",g->id,g->expression);
        utf8_trim_tail(message);
        return reference_issue(0,"D6a/I7/I9","existing same-surface/axis references; acyclic exact rational expression",message);
    }
    g->offset=v;
    /* I7: a valid infinite line can have an empty visible clip. */
    g->resolved=true; ctx->guides[i]=2; return true;
}

static bool reference_face_parse(const char *s, ReferenceFace *r)
{
    memset(r,0,sizeof *r); r->hole=-1;
    if (s[0]=='t') { r->kind=1; return parse_u32(s+1,&r->timber); }
    return parse_edge_ref(s,&r->hole,&r->edge);
}
static void reference_face_format(FILE *out, const ReferenceFace *r)
{
    if (r->kind) fprintf(out,"t%u",r->timber);
    else if (r->hole>=0) fprintf(out,"h%de%d",r->hole,r->edge);
    else fprintf(out,"e%d",r->edge);
}

static bool reference_place_geometry(World *w, size_t ti)
{
    Timber *t=&w->timbers[ti]; TimberAnchor *a=&w->anchors[ti];
    const PlacementSurface *p=world_find_placement(w,a->placement_id);
    if (!p) return reference_issue(t->id,"I13","existing placement","placement missing");
    SpaceBoundarySurface effective;
    const SpaceBoundarySurface *b=placement_effective_boundary(p,world_placement_boundary(w,p),&effective);
    bool along=a->length_direction==SURFACE_DIRECTION_POS_V || a->length_direction==SURFACE_DIRECTION_NEG_V;
    Coord widths[2][2], contacts[2][2]; int n=0; bool contact=false;
    SurfaceRegion2 child_scope; bool scoped=false;
    if (a->anchor_kind==ANCHOR_AT_GRID || a->anchor_kind==ANCHOR_AT_LINE) {
        Coord center;
        if (a->anchor_kind==ANCHOR_AT_GRID) {
            const ReferenceGrid *g=world_find_grid(w,a->ref_grid); char err[180]="";
            if (!g || g->placement_id!=p->id || (a->ref_grid_axis==0)!=along)
                return reference_issue(t->id,"I13/I23","same-face grid coordinate axis perpendicular to length","missing grid or face/axis mismatch (垂直)");
            if (!grid_line_coord_in(w->grids,w->grid_count,g,p,b,a->ref_grid_axis,a->ref_grid_index,&center,NULL,err,sizeof err))
                return reference_issue(t->id,"I23","referenced grid index exists",err);
            if (g->is_subgrid) {
                if (!grid_cell_bounds(w->grids,w->grid_count,g,p,b,&child_scope,err,sizeof err))
                    return reference_issue(t->id,"I25","valid parent cell",err);
                scoped=true;
            }
        } else {
            const GuideLine *g=world_find_guide(w,a->ref_guide);
            if (!g || g->placement_id!=p->id || (g->direction==GUIDE_ALONG_V)!=along)
                return reference_issue(t->id,"I13","same-face line coordinate axis perpendicular to length","missing guide or face/axis mismatch (垂直)");
            center=g->offset;
        }
        widths[0][0]=center-t->size_a/2; widths[0][1]=widths[0][0]+t->size_a; n=1;
    } else if (a->anchor_kind==ANCHOR_AT_EDGE) {
        contact=true;
        if (a->ref_is_timber) {
            int owner=reference_timber_index(w,a->ref_timber); SurfaceRegion2 f;
            if (owner<0 || !w->timbers[owner].placed || w->anchors[owner].placement_id!=p->id ||
                !timber_a0_footprint_uv(p,&w->timbers[owner],&w->anchors[owner],&f))
                return reference_issue(t->id,"I13/I9","placed timber on same face","at-face timber missing/unplaced/different face");
            Coord lo=along?f.min_u:f.min_v,hi=along?f.max_u:f.max_v;
            widths[0][0]=lo-t->size_a; widths[0][1]=lo;
            widths[1][0]=hi; widths[1][1]=hi+t->size_a;
            contacts[0][0]=contacts[1][0]=along?f.min_v:f.min_u;
            contacts[0][1]=contacts[1][1]=along?f.max_v:f.max_u; n=2;
        } else {
            PolygonLoop2 rect; const PolygonLoop2 *loop;
            if (!b) { if (a->ref_hole>=0) return false; placement_outline(p,NULL,&rect); loop=&rect; }
            else {
                if (a->ref_hole>=(int)b->hole_count) return reference_issue(t->id,"I13","existing hole edge","hole missing");
                loop=a->ref_hole<0?&b->outline:&b->holes[a->ref_hole];
            }
            SurfaceSegment2 e; SurfacePoint2 normal;
            if (a->ref_edge<0 || !loop_get_edge_segment(loop,(size_t)a->ref_edge,&e) ||
                !loop_edge_outward_normal(loop,(size_t)a->ref_edge,&normal))
                return reference_issue(t->id,"I13","existing edge","edge missing");
            if ((e.start.u==e.end.u)!=along)
                return reference_issue(t->id,"I13","edge parallel to length","at-face 邊必須平行於長度軸");
            Coord c=along?e.start.u:e.start.v;
            Coord inward=(along?normal.u:normal.v)*(a->ref_hole<0?-1:1);
            widths[0][0]=inward>0?c:c-t->size_a; widths[0][1]=widths[0][0]+t->size_a;
            contacts[0][0]=along?coord_min(e.start.v,e.end.v):coord_min(e.start.u,e.end.u);
            contacts[0][1]=along?coord_max(e.start.v,e.end.v):coord_max(e.start.u,e.end.u); n=1;
        }
    } else return reference_issue(t->id,"I12","at-line or at-face","obsolete anchor");

    StopFaceRef between[2];
    for (int i=0;i<2;++i) between[i]=(StopFaceRef){a->between[i].kind,a->between[i].hole,a->between[i].edge,a->between[i].timber};
    Timber best=*t; TimberAnchor best_a=*a; int found=0;
    size_t issues_before=g_reference_issue_count;
    char last[256]="R6: 沒有任何合法跨距", candidates[180]="";
    for (int k=0;k<n;++k) {
        Coord start,end; char err[256]="";
        SpanStatus status=resolve_auto_span(w,p,b,along,widths[k][0],widths[k][1],
            contact,contact?contacts[k][0]:0,contact?contacts[k][1]:0,
            a->has_through,a->through,a->has_between?between:NULL,scoped?&child_scope:NULL,&start,&end,err,sizeof err);
        if (status!=SPAN_OK) { snprintf(last,sizeof last,"%s",err); continue; }
        if (!coord_in_range(end-start)) { snprintf(last,sizeof last,"D1 auto length exceeds 100000000 mm"); continue; }
        SurfaceRegion2 rect=along?(SurfaceRegion2){widths[k][0],start,widths[k][1],end}:
            (SurfaceRegion2){start,widths[k][0],end,widths[k][1]};
        if (scoped && (rect.min_u<child_scope.min_u || rect.max_u>child_scope.max_u ||
            rect.min_v<child_scope.min_v || rect.max_v>child_scope.max_v)) {
            snprintf(last,sizeof last,"I13：角材的完整足跡必須留在子格內"); continue;
        }
        Timber probe=*t; probe.length=end-start; probe.placed=false;
        SurfacePoint2 uv=anchor_corner_from_rect(p,a->length_direction,a->depth_side,&rect);
        bool checks=true; char first_check[256]="";
        if (!surface_primary_axis_check(w,p->id,&probe,along,err,sizeof err)) {
            if (checks) snprintf(first_check,sizeof first_check,"%s",err);
            checks=false; snprintf(last,sizeof last,"%s",err);
            if (n==1) reference_issue(t->id,"D17/I21","length axis consistent with same-face roles",err);
        }
        if (!timber_end_face_check(w,p,b,&probe,along,start,end,widths[k][0],widths[k][1],err,sizeof err)) {
            if (checks) snprintf(first_check,sizeof first_check,"%s",err);
            checks=false; snprintf(last,sizeof last,"%s",err);
            if (n==1) reference_issue(t->id,"I19/I22","each stop has strictly higher cut priority, subject to boundary exceptions",err);
        }
        if (!timber_boundary_role_check(p,b,&probe,along,start,end,widths[k][0],widths[k][1],err,sizeof err)) {
            if (checks) snprintf(first_check,sizeof first_check,"%s",err);
            checks=false; snprintf(last,sizeof last,"%s",err);
            if (n==1) reference_issue(t->id,"I20/R18","boundary covers its full fixed outline edge",err);
        }
        if (!checks) { set_revalidate_error(first_check); continue; }
        if (!timber_place_a0_on_surface(&probe,p,b,uv,(SurfaceDirection)a->length_direction,(SurfaceDepthSide)a->depth_side)) {
            snprintf(last,sizeof last,"I5/I6 footprint outside effective region or FREE edge"); continue;
        }
        best=probe; best_a=*a; best_a.uv=uv; ++found;
        size_t used=strlen(candidates);
        snprintf(candidates+used,sizeof candidates-used," cross[%lld,%lld] span[%lld,%lld]",(long long)widths[k][0],(long long)widths[k][1],(long long)start,(long long)end);
    }
    if (found!=1) {
        if (n==1 && g_reference_issue_count>issues_before) return false;
        if (found>1) { snprintf(last,sizeof last,"R3/I13 ambiguous at-face candidates:%s",candidates); }
        const char *clause=strstr(last,"V_CUT_PRIORITY")?"I19/I22":strstr(last,"V_PRIMARY_AXIS")?"D17/I21":
            strstr(last,"V_BOUNDARY")?"I20/R18":strstr(last,"D1")?"D1":found>1?"I13/R3":"R6/I5/I6";
        return reference_issue(t->id,clause,"one non-overlapping supported span; role and direction constraints satisfied",last);
    }
    *t=best; *a=best_a; return true;
}

static bool reference_eval_timber(ReferenceEval *ctx, size_t i)
{
    if (ctx->timbers[i]==2) return true;
    if (ctx->timbers[i]==3) return false;
    World *w=ctx->world; Timber *t=&w->timbers[i]; TimberAnchor *a=&w->anchors[i];
    if (!ctx->wanted[i] || ctx->timbers[i])
        return reference_issue(t->id,"I9/I7","acyclic placed dependencies","missing placement or cyclic reference");
    ctx->timbers[i]=1;
    /* Placement order is the implicit dependency order for stop faces (I9).
     * Clear all derived placements before replay so later timbers cannot cut predecessors. */
    bool ok=true;
    for (size_t j=0;j<w->timber_count;++j)
        if (ctx->wanted[j] && w->anchors[j].order<a->order && w->anchors[j].placement_id==a->placement_id)
            (void)reference_eval_timber(ctx,j);
    if (a->anchor_kind==ANCHOR_AT_LINE) {
        bool exists=false;
        for (size_t j=0;j<w->guide_count;++j) if (w->guides[j].id==a->ref_guide) {
            exists=true; if (!reference_eval_guide(ctx,j)) ok=false;
        }
        if (!exists) ok=false;
    }
    uint32_t refs[3]={a->ref_timber,a->has_between&&a->between[0].kind?a->between[0].timber:0,
        a->has_between&&a->between[1].kind?a->between[1].timber:0};
    bool ref_used[3]={a->ref_is_timber,a->has_between&&a->between[0].kind,a->has_between&&a->between[1].kind};
    for (int k=0;k<3;++k) if (ref_used[k]) {
        int j=reference_timber_index(w,refs[k]);
        if (j<0 || w->anchors[j].order>=a->order || !reference_eval_timber(ctx,(size_t)j)) ok=false;
    }
    if (!ok) {
        ctx->timbers[i]=3;
        return reference_issue(t->id,"I9/I13","valid earlier reference dependencies","one or more referenced objects cannot be reconstructed");
    }
    ok=reference_place_geometry(w,i);
    ctx->timbers[i]=ok?2:3; return ok;
}

/* I8a: report independent failures across the whole reconstructed world. */
static bool reference_check_all(const World *w)
{
    bool ok=true;
    for (size_t i=0;i<w->timber_count;++i) {
        const Timber *t=&w->timbers[i]; const TimberAnchor *a=&w->anchors[i];
        if (!t->placed) continue;
        const PlacementSurface *p=world_find_placement(w,a->placement_id); SurfaceRegion2 f;
        if (!p || !timber_a0_footprint_uv(p,t,a,&f)) { ok=reference_issue(t->id,"I5","valid footprint on existing surface","missing footprint"); continue; }
        const SpaceBoundarySurface *b=world_placement_boundary(w,p);
        bool along=a->length_direction==SURFACE_DIRECTION_POS_V || a->length_direction==SURFACE_DIRECTION_NEG_V;
        Coord lo=along?f.min_u:f.min_v,hi=along?f.max_u:f.max_v;
        Coord ends[2]={along?f.min_v:f.min_u,along?f.max_v:f.max_u};
        StopFace faces[STOP_FACE_MAX]; size_t nf=collect_stop_faces(w,p,b,along,t,faces,STOP_FACE_MAX);
        for (int k=0;k<2;++k) {
            size_t hits=count_legal_stops(faces,nf,ends[k],lo,hi);
            if (!hits || (!a->has_between && hits!=1)) {
                char actual[180]; snprintf(actual,sizeof actual,"end %d at %lld mm, cross [%lld,%lld], legal stops=%u",k,(long long)ends[k],(long long)lo,(long long)hi,(unsigned)hits);
                reference_issue(t->id,"R6(d)/I6","one full-width FIXED stop at each end (or explicit between)",actual); ok=false;
            }
        }
        char err[256];
        if (!timber_end_face_check(w,p,b,t,along,ends[0],ends[1],lo,hi,err,sizeof err)) { reference_issue(t->id,"I19/I22","higher-priority endpoint supports or defined exception",err); ok=false; }
        if (!timber_boundary_role_check(p,b,t,along,ends[0],ends[1],lo,hi,err,sizeof err)) { reference_issue(t->id,"I20/R18","full fixed-edge coverage for boundary",err); ok=false; }
        for (size_t j=i+1;j<w->timber_count;++j) {
            SurfaceRegion2 other;
            if (!w->timbers[j].placed || w->anchors[j].placement_id!=a->placement_id || !timber_a0_footprint_uv(p,&w->timbers[j],&w->anchors[j],&other)) continue;
            if (uv_rects_overlap(f.min_u,f.min_v,f.max_u,f.max_v,other.min_u,other.min_v,other.max_u,other.max_v)) {
                char actual[180]; snprintf(actual,sizeof actual,"positive-area intersection with timber %u",w->timbers[j].id);
                reference_issue(t->id,"I11","zero positive-area overlap",actual); ok=false;
            }
        }
    }
    return ok;
}

static bool reference_rebuild(World *w)
{
    ReferenceEval ctx={0}; ctx.world=w; bool ok=true;
    for (size_t i=0;i<w->guide_count;++i) w->guides[i].resolved=false;
    for (size_t i=0;i<w->timber_count;++i) { ctx.wanted[i]=w->timbers[i].placed; w->timbers[i].placed=false; }
    if (!reference_eval_datums(&ctx)) { if (g_reference_capturing) g_reference_trial=*w; return false; }
    /* Timbers drive guide evaluation as needed; remaining guides are then evaluated. */
    for (size_t i=0;i<w->timber_count;++i) if (ctx.wanted[i] && !reference_eval_timber(&ctx,i)) ok=false;
    for (size_t i=0;i<w->guide_count;++i) if (!reference_eval_guide(&ctx,i)) ok=false;
    if (g_reference_capturing) g_reference_trial=*w;
    return ok;
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
    size_t i=0; while (i<w->spec_count && strcmp(w->specs[i].name,tokens[1])) ++i;
    if (i==WORLD_MAX_SPECS) { scene_error(p,n,"D6b: spec capacity exceeded"); return false; }
    if (i==w->spec_count) ++w->spec_count;
    snprintf(w->specs[i].name,SPEC_NAME_MAX,"%s",tokens[1]); w->specs[i].value=value;
    return reference_checked(p,n,w);
}
static bool apply_datum_line(const char *p,int n,char **tokens,int count,World *w)
{
    DatumPlane d={0};
    if (!parse_u32(tokens[1],&d.id) || strlen(tokens[2])!=1 ||
        !strchr("xyzXYZ",tokens[2][0]) || !reference_expression(tokens,3,count,d.expression)) {
        scene_error(p,n,"D6c: datum id x|y|z spec-only position expression"); return false;
    }
    d.axis=tolower((unsigned char)tokens[2][0])=='x'?0:tolower((unsigned char)tokens[2][0])=='y'?1:2;
    size_t i=0; while (i<w->datum_count && w->datums[i].id!=d.id) ++i;
    if (i==WORLD_MAX_DATUMS) { scene_error(p,n,"D6c: datum capacity exceeded"); return false; }
    if (i==w->datum_count) ++w->datum_count;
    w->datums[i]=d;
    return reference_checked(p,n,w);
}
static bool apply_reference_guide(const char *p,int n,char **tokens,int count,World *w)
{
    GuideLine g={0}; int dir;
    if (!parse_u32(tokens[1],&g.id) || !parse_u32(tokens[2],&g.placement_id)) return false;
    if (!strcmp(tokens[3],"datum")) {
        if (count!=5 || !parse_u32(tokens[4],&g.datum_id)) return false;
        g.source=GUIDE_DATUM;
    } else {
        if (!lookup_keyword(tokens[3],GUIDE_DIRECTION_WORDS,&dir) ||
            !reference_expression(tokens,4,count,g.expression)) return false;
        g.direction=(GuideDirection)dir;
    }
    size_t i=0; while (i<w->guide_count && w->guides[i].id!=g.id) ++i;
    if (i==WORLD_MAX_GUIDES) { scene_error(p,n,"D6: guide capacity exceeded"); return false; }
    if (i==w->guide_count) ++w->guide_count;
    w->guides[i]=g; return reference_checked(p,n,w);
}
static bool apply_reference_move(const char *p,int n,char **tokens,int count,World *w)
{
    uint32_t id;
    if (!parse_u32(tokens[1],&id)) return false;
    for (size_t i=0;i<w->guide_count;++i) if (w->guides[i].id==id) {
        if (w->guides[i].source==GUIDE_DATUM) {
            scene_error(p,n,"R5: shared guide cannot be moved locally; edit its datum or named spec"); return false;
        }
        if (!reference_expression(tokens,2,count,w->guides[i].expression)) return false;
        return reference_checked(p,n,w);
    }
    scene_error(p,n,"I9: move guide does not exist"); return false;
}
static bool apply_reference_place(const char *p,int n,char **tokens,int count,World *w)
{
    uint32_t id,pid; int i=5;
    if (count<8 || !parse_u32(tokens[1],&id) || strcmp(tokens[2],"on") || !parse_u32(tokens[3],&pid)) return false;
    int ti=reference_timber_index(w,id);
    if (ti<0) { scene_error(p,n,"I9: place 指的角材不存在"); return false; }
    TimberAnchor a={0}; a.placement_id=pid; a.ref_hole=-1; a.span_mode=SPAN_AUTO;
    if (!strcmp(tokens[4],"at-line")) {
        if (i<count && !strcmp(tokens[i],"guide") && i+1<count) {
            a.anchor_kind=ANCHOR_AT_LINE; if (!parse_u32(tokens[i+1],&a.ref_guide)) return false; i+=2;
        } else if (i+3<count && !strcmp(tokens[i],"grid")) {
            int64_t index; a.anchor_kind=ANCHOR_AT_GRID;
            if (!parse_u32(tokens[i+1],&a.ref_grid) || !parse_i64(tokens[i+3],&index) ||
                (strcmp(tokens[i+2],"u") && strcmp(tokens[i+2],"v"))) return false;
            const ReferenceGrid *grid=world_find_grid(w,a.ref_grid);
            if (!grid || (!grid->from_binding && (index<0 || index>=GRID_MAX_LINES))) {
                scene_error(p,n,"I13: the grid must exist; finite grid indices must be nonnegative and below 64"); return false;
            }
            a.ref_grid_axis=!strcmp(tokens[i+2],"u")?0:1; a.ref_grid_index=index; i+=4;
        } else { scene_error(p,n,"I13: at-line guide id | grid id u|v index"); return false; }
    } else if (!strcmp(tokens[4],"at-face")) {
        ReferenceFace r;
        if (!reference_face_parse(tokens[i++],&r)) {
            scene_error(p,n,"I13: 邊參照必須是 e索引、h孔e邊或 t角材"); return false;
        }
        a.anchor_kind=ANCHOR_AT_EDGE; a.ref_hole=r.hole; a.ref_edge=r.edge; a.ref_timber=r.timber; a.ref_is_timber=r.kind!=0;
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
    a.order=w->timbers[ti].placed?w->anchors[ti].order:++w->next_order;
    w->anchors[ti]=a; w->timbers[ti].placed=true;
    return reference_checked(p,n,w);
}

/* D9/R4: emit declarations first, then reference nodes in evaluation order. */
static void reference_dump_guide(const World *w,FILE *out,size_t i,bool *done)
{
    if (done[i]) return;
    done[i]=true;
    const char *p=w->guides[i].expression;
    while ((p=strstr(p,"guide:"))!=NULL) {
        char *end; unsigned long id=strtoul(p+6,&end,10);
        for (size_t j=0;j<w->guide_count;++j) if (w->guides[j].id==id) reference_dump_guide(w,out,j,done);
        p=end>p?end:p+6;
    }
    const GuideLine *g=&w->guides[i];
    if (g->source==GUIDE_DATUM) fprintf(out,"guide %u %u datum %u\n",g->id,g->placement_id,g->datum_id);
    else fprintf(out,"guide %u %u %s %s\n",g->id,g->placement_id,g->direction==GUIDE_ALONG_U?"u":"v",g->expression);
}
static bool reference_guide_ready(const World *w,size_t i,const bool *placed,unsigned depth)
{
    if (depth>WORLD_MAX_GUIDES) return false;
    const char *p=w->guides[i].expression;
    while ((p=strstr(p,"timber:"))!=NULL) {
        char *end; unsigned long id=strtoul(p+7,&end,10);
        int ti=reference_timber_index(w,(uint32_t)id);
        if (ti>=0 && end[0]==':' && end[1]!='A' && end[1]!='B' && !placed[ti]) return false;
        p=end>p?end:p+7;
    }
    p=w->guides[i].expression;
    while ((p=strstr(p,"guide:"))!=NULL) {
        char *end; unsigned long id=strtoul(p+6,&end,10);
        for (size_t j=0;j<w->guide_count;++j)
            if (w->guides[j].id==id && !reference_guide_ready(w,j,placed,depth+1)) return false;
        p=end>p?end:p+6;
    }
    return true;
}
static void reference_dump(const World *w,FILE *out)
{
    bool gd[WORLD_MAX_GUIDES]={0},placed[WORLD_MAX_TIMBERS]={0};
    for (size_t i=0;i<w->datum_count;++i)
        fprintf(out,"datum %u %c %s\n",w->datums[i].id,"xyz"[w->datums[i].axis],w->datums[i].expression);
    for (size_t i=0;i<w->timber_count;++i) {
        const Timber *t=&w->timbers[i];
        if (engineering_dump_timber(w,t,out)) continue;
        fprintf(out,"timber %u %lld %lld role %s",t->id,(long long)t->size_a,(long long)t->size_b,timber_role_name(t->role));
        if (t->role==TIMBER_ROLE_CUSTOM) fprintf(out," priority %lld",(long long)t->cut_priority);
        fputc('\n',out);
    }
    for (size_t k=0;k<=w->timber_count;++k) {
        for (size_t i=0;i<w->guide_count;++i) if (!gd[i] && reference_guide_ready(w,i,placed,0)) reference_dump_guide(w,out,i,gd);
        size_t at=w->timber_count; uint64_t order=UINT64_MAX;
        for (size_t i=0;i<w->timber_count;++i) if (w->timbers[i].placed && !placed[i] && w->anchors[i].order<order) { at=i; order=w->anchors[i].order; }
        if (at==w->timber_count) break;
        const Timber *t=&w->timbers[at]; const TimberAnchor *a=&w->anchors[at];
        fprintf(out,"place %u on %u ",t->id,a->placement_id);
        if (a->anchor_kind==ANCHOR_AT_LINE) fprintf(out,"at-line guide %u",a->ref_guide);
        else if (a->anchor_kind==ANCHOR_AT_GRID) fprintf(out,"at-line grid %u %c %lld",a->ref_grid,a->ref_grid_axis==0?'u':'v',(long long)a->ref_grid_index);
        else { ReferenceFace r={a->ref_is_timber?1:0,a->ref_hole,a->ref_edge,a->ref_timber}; fputs("at-face ",out); reference_face_format(out,&r); }
        if (a->has_through) fprintf(out," through %lld",(long long)a->through);
        if (a->has_between) { fputs(" between ",out); reference_face_format(out,&a->between[0]); fputc(' ',out); reference_face_format(out,&a->between[1]); }
        const char *dirs[]={"+u","-u","+v","-v"};
        fprintf(out," %s %s\n",dirs[a->length_direction],a->depth_side==SURFACE_DEPTH_POSITIVE_NORMAL?"+n":"-n");
        const PlacementSurface *p=world_find_placement(w,a->placement_id); SurfaceRegion2 f; bool on=false,covers=false; int edge=-1;
        bool along=a->length_direction==SURFACE_DIRECTION_POS_V || a->length_direction==SURFACE_DIRECTION_NEG_V;
        SpaceBoundarySurface effective;
        if (p && timber_a0_footprint_uv(p,t,a,&f)) timber_role_props(placement_effective_boundary(p,world_placement_boundary(w,p),&effective),along,along?f.min_v:f.min_u,along?f.max_v:f.max_u,along?f.min_u:f.min_v,along?f.max_u:f.max_v,&on,&covers,&edge);
        fprintf(out,"# R18 角材 %u: onBoundary=%s coversEdge=%s boundaryEdge=%d\n",t->id,on?"true":"false",covers?"true":"false",edge);
        placed[at]=true;
    }
}

/* R5: finite visible references within a caller-provided pick radius; no free offset. */
static bool reference_snap(World *w,uint32_t pid,GuideDirection dir,uint32_t exclude,Coord at,Coord radius,char *out)
{
    GuideLine probe={0}; probe.placement_id=pid; probe.direction=dir;
    ReferenceEval ctx={0}; ctx.world=w;
    for (size_t i=0;i<w->timber_count;++i) { ctx.wanted[i]=w->timbers[i].placed; ctx.timbers[i]=w->timbers[i].placed?2:0; }
    for (size_t i=0;i<w->guide_count;++i) ctx.guides[i]=2;
    Coord best=radius+1; bool found=false;
    const PlacementSurface *p=world_find_placement(w,pid); if (!p) return false;
    const SpaceBoundarySurface *b=world_placement_boundary(w,p); char axis=dir==GUIDE_ALONG_V?'u':'v';
    enum { SNAP_MAX = WORLD_MAX_SPECS + WORLD_MAX_GUIDES + (POLY_MAX_HOLES+1)*POLY_MAX_VERTICES + WORLD_MAX_GRIDS*GRID_MAX_LINES + WORLD_MAX_TIMBERS*2 };
    char candidates[SNAP_MAX][REF_EXPR_MAX]; size_t n=0;
    for (size_t i=0;i<w->spec_count && n<SNAP_MAX;++i) snprintf(candidates[n++],REF_EXPR_MAX,"spec:%s",w->specs[i].name);
    for (size_t i=0;i<w->guide_count && n<SNAP_MAX;++i) if (w->guides[i].id!=exclude && w->guides[i].placement_id==pid && w->guides[i].direction==dir)
        snprintf(candidates[n++],REF_EXPR_MAX,"guide:%u",w->guides[i].id);
    PolygonLoop2 rect; placement_outline(p,b,&rect);
    for (int h=-1; h<(b?(int)b->hole_count:0); ++h) {
        const PolygonLoop2 *loop=h<0?&rect:&b->holes[h];
        for (size_t i=0;i<loop->count && n<SNAP_MAX;++i) {
            if (h<0) snprintf(candidates[n++],REF_EXPR_MAX,"vertex:v%u:%c",(unsigned)i,axis);
            else snprintf(candidates[n++],REF_EXPR_MAX,"vertex:h%dv%u:%c",h,(unsigned)i,axis);
        }
    }
    for (size_t i=0;i<w->grid_count;++i) if (w->grids[i].placement_id==pid) {
        const ReferenceGrid *grid=&w->grids[i];
        Coord coords[GRID_MAX_LINES]; int64_t indices[GRID_MAX_LINES]; size_t count=0; int a=axis=='u'?0:1;
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
        } else if (!grid_sample_indices_in(w->grids,w->grid_count,grid,p,b,a,indices,coords,&count)) continue;
        for (size_t j=0;j<count && n<SNAP_MAX;++j)
            snprintf(candidates[n++],REF_EXPR_MAX,"grid:%u:%c:%lld",grid->id,axis,(long long)indices[j]);
    }
    for (size_t i=0;i<w->timber_count && n+1<SNAP_MAX;++i) if (w->timbers[i].placed && w->anchors[i].placement_id==pid) {
        snprintf(candidates[n++],REF_EXPR_MAX,"timber:%u:%c:lo",w->timbers[i].id,axis);
        snprintf(candidates[n++],REF_EXPR_MAX,"timber:%u:%c:hi",w->timbers[i].id,axis);
    }
    for (size_t i=0;i<n;++i) {
        Coord value;
        snprintf(probe.expression,sizeof probe.expression,"%s",candidates[i]);
        if (!reference_eval_expression(&ctx,&probe,&value) || !guide_offset_in_range(p,b,dir,value)) continue;
        Coord distance=value>at?value-at:at-value;
        if (distance<best) {
            /* A reference back through the moving guide/timber is not a legal snap. */
            World candidate=*w; bool legal=true;
            if (exclude) {
                for (size_t j=0;j<candidate.guide_count;++j) if (candidate.guides[j].id==exclude) {
                    snprintf(candidate.guides[j].expression,REF_EXPR_MAX,"%s",candidates[i]);
                    bool capture=g_reference_capturing; g_reference_capturing=false;
                    legal=world_revalidate(&candidate); g_reference_capturing=capture; break;
                }
            }
            if (legal) { best=distance; snprintf(out,REF_EXPR_MAX,"%s",candidates[i]); found=true; }
        }
    }
    return found;
}
