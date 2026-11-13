#include "member_reference.h"
#include <stdio.h>
#include <string.h>

static int wood_reference_member_index(const WoodMemberReferenceContext *w,uint32_t id)
{
    for(size_t i=0;i<w->member_count;++i){WoodMemberReferenceFact value;
        if(w->member_at(w->user,i,&value)&&value.member.id==id)return (int)i;}
    return -1;
}
static bool wood_reference_guide(const WoodMemberReferenceContext *w,uint32_t id,WoodMemberGuideFact *out)
{
    for(size_t i=0;i<w->guide_count;++i){WoodMemberGuideFact value;
        if(w->guide_at(w->user,i,&value)&&value.id==id){*out=value;return true;}}
    return false;
}
GeoPoint2 wood_member_anchor_corner(const GeoFrame *frame,int direction,int depth,const GeoRect2 *rect)
{
    GeoVector3 length=geo_frame_direction(frame,(GeoDirection2)direction);
    GeoVector3 b=depth==WOOD_DEPTH_POSITIVE_NORMAL?frame->normal:geo_vector_negate(frame->normal);
    GeoVector3 a=geo_vector_cross(b,length);
    GeoCoord lu=geo_vector_dot(length,frame->axis_u),lv=geo_vector_dot(length,frame->axis_v);
    GeoCoord au=geo_vector_dot(a,frame->axis_u),av=geo_vector_dot(a,frame->axis_v);
    GeoCoord du=lu!=0?lu:au,dv=lv!=0?lv:av;
    return (GeoPoint2){du>0?rect->min_u:rect->max_u,dv>0?rect->min_v:rect->max_v};
}

bool wood_member_reference_place(const WoodMemberReferenceContext *w,size_t ti)
{
    WoodMemberReferenceFact value;if(!w->member_at(w->user,ti,&value))return false;
    WoodMember *t=&value.member;WoodMemberReference *a=&value.anchor;
    WoodMemberPlacementFact p;
    if(!w->placement(w->user,a->placement_id,&p))return w->issue(w->user,t->id,"I13","existing placement","placement missing");
    if(p.derived&&(t->size_b!=p.height||a->depth_side!=WOOD_DEPTH_POSITIVE_NORMAL)){
        char error[180];snprintf(error,sizeof error,"V_DERIVED_TIMBER: timber %u B=%lld host h=%lld requires B=h and +n",t->id,(long long)t->size_b,(long long)p.height);
        return w->issue(w->user,t->id,"I53","B=h and +n",error);
    }
    bool along=a->length_direction==GEO_DIRECTION_POS_V||a->length_direction==GEO_DIRECTION_NEG_V;
    GeoCoord widths[2][2],contacts[2][2];int n=0;bool contact=false;
    GeoRect2 child_scope={0};bool scoped=false;
    if(a->anchor_kind==WOOD_ANCHOR_AT_GRID||a->anchor_kind==WOOD_ANCHOR_AT_LINE||a->anchor_kind==WOOD_ANCHOR_AT_RULE){
        GeoCoord center;
        if(a->anchor_kind==WOOD_ANCHOR_AT_GRID){
            WoodMemberGridFact g;char err[180]="";
            if(!w->grid(w->user,a->ref_grid,&g)||g.placement_id!=p.id||(a->ref_grid_axis==0)!=along)
                return w->issue(w->user,t->id,"I13/I23","same-face grid coordinate axis perpendicular to length","missing grid or face/axis mismatch (垂直)");
            if(!w->grid_line(w->user,a,&center,err,sizeof err))
                return w->issue(w->user,t->id,"I23","referenced grid index exists",err);
            if(g.subgrid){
                if(!w->grid_scope(w->user,g.id,&child_scope,err,sizeof err))
                    return w->issue(w->user,t->id,"I25","valid parent cell",err);
                scoped=true;
            }
        }else if(a->anchor_kind==WOOD_ANCHOR_AT_RULE){
            char err[180]="";
            if((a->ref_rule.axis==0)!=along||!w->rule_line(w->user,&a->ref_rule,p.id,&center,&child_scope,err,sizeof err))
                return w->issue(w->user,t->id,"I13/I25a","same-source rule line and axis",err[0]?err:"rule axis mismatch");
            scoped=true;
        }else{
            WoodMemberGuideFact g;
            if(!wood_reference_guide(w,a->ref_guide,&g)||g.placement_id!=p.id||g.along_v!=along)
                return w->issue(w->user,t->id,"I13","same-face line coordinate axis perpendicular to length","missing guide or face/axis mismatch (垂直)");
            center=g.offset;
        }
        widths[0][0]=center-t->size_a/2;widths[0][1]=widths[0][0]+t->size_a;n=1;
    }else if(a->anchor_kind==WOOD_ANCHOR_AT_EDGE){
        contact=true;
        if(a->ref_is_timber){
            int owner=wood_reference_member_index(w,a->ref_timber);WoodMemberReferenceFact other;GeoRect2 f;
            if(owner<0||!w->member_at(w->user,(size_t)owner,&other)||!other.member.placed||other.anchor.placement_id!=p.id||
               !w->member_footprint(w->user,(size_t)owner,p.id,&f))
                return w->issue(w->user,t->id,"I13/I9","placed timber on same face","at-face timber missing/unplaced/different face");
            GeoCoord lo=along?f.min_u:f.min_v,hi=along?f.max_u:f.max_v;
            widths[0][0]=lo-t->size_a;widths[0][1]=lo;widths[1][0]=hi;widths[1][1]=hi+t->size_a;
            contacts[0][0]=contacts[1][0]=along?f.min_v:f.min_u;
            contacts[0][1]=contacts[1][1]=along?f.max_v:f.max_u;n=2;
        }else{
            int hole=a->ref_hole,edge=a->ref_edge;
            if(p.derived){
                if(!a->ref_derived_key[0])return w->issue(w->user,t->id,"R41/I13","one exact source/segment/total key","derived edge index aliases are forbidden; an exact key is required");
                char err[512];if(!w->resolve_key(w->user,p.id,a->ref_derived_key,&hole,&edge,err,sizeof err))
                    return w->issue(w->user,t->id,"R41/I13","one exact source/segment/total key",err);
            }else if(a->ref_derived_key[0])return w->issue(w->user,t->id,"D4/R41","derived placement for edge key","key on ordinary placement");
            WoodMemberEdgeFact e;WoodMemberEdgeStatus status=w->edge(w->user,p.id,hole,edge,&e);
            if(status==WOOD_MEMBER_EDGE_NO_DOMAIN_HOLE)return false;
            if(status==WOOD_MEMBER_EDGE_MISSING_HOLE)return w->issue(w->user,t->id,"I13","existing hole edge","hole missing");
            if(status!=WOOD_MEMBER_EDGE_OK)return w->issue(w->user,t->id,"I13","existing edge","edge missing");
            if((e.segment.start.u==e.segment.end.u)!=along)
                return w->issue(w->user,t->id,"I13","edge parallel to length","at-face 邊必須平行於長度軸");
            GeoCoord c=along?e.segment.start.u:e.segment.start.v;
            GeoCoord inward=(along?e.outward.u:e.outward.v)*(e.hole<0?-1:1);
            widths[0][0]=inward>0?c:c-t->size_a;widths[0][1]=widths[0][0]+t->size_a;
            GeoCoord e0=along?e.segment.start.v:e.segment.start.u,e1=along?e.segment.end.v:e.segment.end.u;
            contacts[0][0]=e0<e1?e0:e1;contacts[0][1]=e0>e1?e0:e1;n=1;
        }
    }else return w->issue(w->user,t->id,"I12","at-line or at-face","obsolete anchor");

    WoodStopRef between[2];
    for(int i=0;i<2;++i){
        const WoodMemberReferenceFace *r=&a->between[i];between[i]=(WoodStopRef){r->kind==1,r->hole,r->edge,r->timber};
        if(!a->has_between)continue;
        if(r->kind==2){char err[512];if(!w->resolve_key(w->user,p.id,r->key,&between[i].hole,&between[i].edge,err,sizeof err))
            return w->issue(w->user,t->id,"R41/D18","one exact source key","between derived key missing, stale or ambiguous");}
        else if(p.derived&&r->kind!=1)return w->issue(w->user,t->id,"R41/D18","source key or timber","derived edge index aliases are forbidden");
    }
    WoodMember best=*t;GeoPoint2 best_uv={0};int found=0;size_t issues_before=w->issue_count(w->user);
    char last[256]="R6: 沒有任何合法跨距",candidates[180]="";
    for(int k=0;k<n;++k){
        GeoCoord start,end;char err[256]="";
        WoodMemberSpanRequest request={along,widths[k][0],widths[k][1],contact,contact?contacts[k][0]:0,contact?contacts[k][1]:0,
            a->has_through,a->through,a->has_between,{between[0],between[1]},scoped,child_scope};
        request.self=t;
        if(!w->span(w->user,p.id,&request,&start,&end,err,sizeof err)){snprintf(last,sizeof last,"%s",err);continue;}
        if(!geo_coord_in_range(end-start)){snprintf(last,sizeof last,"D1 auto length exceeds 100000000 mm");continue;}
        GeoRect2 rect=along?(GeoRect2){widths[k][0],start,widths[k][1],end}:(GeoRect2){start,widths[k][0],end,widths[k][1]};
        if(scoped&&(rect.min_u<child_scope.min_u||rect.max_u>child_scope.max_u||rect.min_v<child_scope.min_v||rect.max_v>child_scope.max_v)){
            snprintf(last,sizeof last,"I13：角材的完整足跡必須留在子格內");continue;
        }
        WoodMember probe=*t;probe.length=end-start;probe.placed=false;
        GeoPoint2 uv=wood_member_anchor_corner(&p.frame,a->length_direction,a->depth_side,&rect);
        bool checks=true;char first_check[256]="";
        if(!w->primary_axis(w->user,p.id,&probe,along,err,sizeof err)){
            if(checks)snprintf(first_check,sizeof first_check,"%s",err);checks=false;snprintf(last,sizeof last,"%s",err);
            if(n==1)w->issue(w->user,t->id,"D17/I21","length axis consistent with same-face roles",err);
        }
        if(!w->end_faces(w->user,p.id,&probe,&request,start,end,&rect,err,sizeof err)){
            if(checks)snprintf(first_check,sizeof first_check,"%s",err);checks=false;snprintf(last,sizeof last,"%s",err);
            if(n==1)w->issue(w->user,t->id,"I19/I22","each stop has strictly higher cut priority, subject to boundary exceptions",err);
        }
        if(!w->boundary_role(w->user,p.id,&probe,&request,start,end,&rect,err,sizeof err)){
            if(checks)snprintf(first_check,sizeof first_check,"%s",err);checks=false;snprintf(last,sizeof last,"%s",err);
            if(n==1)w->issue(w->user,t->id,"I20/R18","boundary covers its full fixed outline edge",err);
        }
        if(!checks){w->first_error(w->user,first_check);continue;}
        if(!w->place(w->user,p.id,&probe,uv,a->length_direction,a->depth_side)){
            snprintf(last,sizeof last,"I5/I6 footprint outside effective region or FREE edge");continue;
        }
        best=probe;best_uv=uv;++found;
        size_t used=strlen(candidates);snprintf(candidates+used,sizeof candidates-used," cross[%lld,%lld] span[%lld,%lld]",(long long)widths[k][0],(long long)widths[k][1],(long long)start,(long long)end);
    }
    if(found!=1){
        if(n==1&&w->issue_count(w->user)>issues_before)return false;
        if(found>1)snprintf(last,sizeof last,"R3/I13 ambiguous at-face candidates:%s",candidates);
        const char *clause=strstr(last,"V_CUT_PRIORITY")?"I19/I22":strstr(last,"V_PRIMARY_AXIS")?"D17/I21":
            strstr(last,"V_BOUNDARY")?"I20/R18":strstr(last,"D1")?"D1":found>1?"I13/R3":"R6/I5/I6";
        return w->issue(w->user,t->id,clause,"one non-overlapping supported span; role and direction constraints satisfied",last);
    }
    w->write(w->user,ti,&best,best_uv);return true;
}

bool wood_member_reference_compute(const WoodMemberReferenceContext *w,size_t i,bool *needs_placement)
{
    *needs_placement=false;
    WoodMemberReferenceFact value;if(!w->member_at(w->user,i,&value))return false;
    WoodMember *t=&value.member;WoodMemberReference *a=&value.anchor;
    if(w->use_current_values&&t->placed)return true;
    if(!value.wanted)return false;
    bool ok=true;
    for(size_t j=0;j<w->member_count;++j){WoodMemberReferenceFact prior;
        if(w->member_at(w->user,j,&prior)&&prior.wanted&&prior.anchor.order<a->order&&prior.anchor.placement_id==a->placement_id)
            (void)w->evaluate_member(w->user,j,GEO_DEPENDENCY_EVALUATE_BEFORE);
    }
    if(a->anchor_kind==WOOD_ANCHOR_AT_LINE){
        bool exists=false;
        for(size_t j=0;j<w->guide_count;++j){WoodMemberGuideFact g;
            if(w->guide_at(w->user,j,&g)&&g.id==a->ref_guide){exists=true;if(!w->evaluate_guide(w->user,j))ok=false;}}
        if(!exists)ok=false;
    }
    uint32_t refs[3]={a->ref_timber,a->has_between&&a->between[0].kind==1?a->between[0].timber:0,a->has_between&&a->between[1].kind==1?a->between[1].timber:0};
    bool ref_used[3]={a->ref_is_timber,a->has_between&&a->between[0].kind==1,a->has_between&&a->between[1].kind==1};
    for(int k=0;k<3;++k)if(ref_used[k]){
        int j=wood_reference_member_index(w,refs[k]);WoodMemberReferenceFact prior;
        if(j<0||!w->member_at(w->user,(size_t)j,&prior)||prior.anchor.order>=a->order||!w->evaluate_member(w->user,(size_t)j,GEO_DEPENDENCY_VALUE_REQUIRED))ok=false;
    }
    if(!ok)return w->issue(w->user,t->id,"I9/I13","valid earlier reference dependencies","one or more referenced objects cannot be reconstructed");
    *needs_placement=true;return true;
}

static GeoCoord wood_reference_min(GeoCoord a,GeoCoord b){return a<b?a:b;}
static GeoCoord wood_reference_max(GeoCoord a,GeoCoord b){return a>b?a:b;}

bool wood_member_primary_axis_check(const WoodMemberAxisFact *facts,size_t count,uint32_t placement_id,
    const WoodMember *extra,bool extra_along_v,char *err,size_t err_size)
{
    bool has_primary = false, has_boundary = false;
    int primary_axis = -1, boundary_axis = -1;   /* 0 = 沿 u,1 = 沿 v */
    uint32_t primary_id = 0;

    /* 第一遍:定軸。primary 優先推導,其次 boundary 的垂直向。 */
    for (size_t i = 0; i <= count; ++i) {
        const WoodMember *t;WoodMember selected;
        int axis;

        if (i < count) {
            const WoodMemberAxisFact *fact=&facts[i];
            if(!fact->placed||fact->placement_id!=placement_id)continue;
            selected=(WoodMember){0};selected.id=fact->id;selected.role=fact->role;t=&selected;
            axis=fact->along_v?1:0;
        } else {
            if (extra == NULL) break;
            t = extra;
            axis = extra_along_v ? 1 : 0;
        }

        if (t->role == WOOD_MEMBER_ROLE_PRIMARY) {
            if (!has_primary) {
                has_primary = true;
                primary_axis = axis;
                primary_id = t->id;
            } else if (axis != primary_axis) {
                if (err != NULL) {
                    snprintf(err, err_size,
                        "V_PRIMARY_AXIS:同面 primary 長度軸不唯一"
                        "（角材 %u 沿 %c,角材 %u 沿 %c）",
                        primary_id, primary_axis ? 'v' : 'u',
                        t->id, axis ? 'v' : 'u');
                }
                return false;
            }
        } else if (t->role == WOOD_MEMBER_ROLE_BOUNDARY && !has_boundary) {
            has_boundary = true;
            boundary_axis = axis;
        }
    }

    int axis = has_primary ? primary_axis
             : has_boundary ? 1 - boundary_axis
             : -1;

    /* 第二遍:boundary/secondary 不得與主支軸平行;
       主支軸未定義時不得有 secondary。 */
    for (size_t i = 0; i <= count; ++i) {
        const WoodMember *t;WoodMember selected;
        int t_axis;

        if (i < count) {
            const WoodMemberAxisFact *fact=&facts[i];
            if(!fact->placed||fact->placement_id!=placement_id)continue;
            selected=(WoodMember){0};selected.id=fact->id;selected.role=fact->role;t=&selected;
            t_axis=fact->along_v?1:0;
        } else {
            if (extra == NULL) break;
            t = extra;
            t_axis = extra_along_v ? 1 : 0;
        }

        if (t->role != WOOD_MEMBER_ROLE_BOUNDARY &&
            t->role != WOOD_MEMBER_ROLE_SECONDARY) {
            continue;
        }

        if (axis == -1) {
            if (t->role == WOOD_MEMBER_ROLE_SECONDARY) {
                if (err != NULL) {
                    snprintf(err, err_size,
                        "V_PRIMARY_AXIS:主支軸未定義,"
                        "secondary（角材 %u）必須在主支之後", t->id);
                }
                return false;
            }
            continue;   /* boundary 落地即定義主支軸 */
        }

        if (t_axis == axis) {
            if (err != NULL) {
                snprintf(err, err_size,
                    "V_PRIMARY_AXIS:角材 %u（%s）長度軸沿 %c,"
                    "與主支軸平行——boundary/secondary 必須垂直於主支軸",
                    t->id, wood_member_role_name(t->role),
                    axis ? 'v' : 'u');
            }
            return false;
        }
    }

    return true;
}

bool wood_member_boundary_role_check(const WoodMember *timber,const GeoLoop2View *outline,
    const int *fixities,bool footprint_inside,bool along_v,GeoCoord span_lo,GeoCoord span_hi,
    GeoCoord cross_lo,GeoCoord cross_hi,char *err,size_t err_cap)
{

    bool on_boundary = false, covers_edge = false;
    int edge_index = -1;
    GeoSegment2 seg;
    GeoCoord edge_lo, edge_hi, cover;

    if (timber == NULL || timber->role != WOOD_MEMBER_ROLE_BOUNDARY) {
        return true;
    }

    /*
     * footprint 已經跨出有效範圍時讓位給 I5——公理層 I22 明訂
     * 「凸角處延伸即出界，不需另立規則」，該情形的裁決者是 I5 而非本條。
     */
    if (!footprint_inside) return true;
    if (!wood_member_boundary_props(outline, along_v, span_lo, span_hi,
                           cross_lo, cross_hi,
                           &on_boundary, &covers_edge, &edge_index)) {
        return true;
    }

    if (!on_boundary) {
        if (err != NULL) {
            snprintf(err, err_cap,
                     "V_BOUNDARY_ROLE：角材 %u 宣告 boundary，"
                     "但沒有任何側面貼在外輪廓邊上",
                     (unsigned)timber->id);
        }
        return false;
    }

    if(!outline||edge_index<0||(size_t)edge_index>=outline->count)return true;
    seg=(GeoSegment2){outline->v[edge_index],outline->v[((size_t)edge_index+1)%outline->count]};

    if (fixities[edge_index] != WOOD_STOP_FIXED) {
        if (err != NULL) {
            snprintf(err, err_cap,
                     "V_BOUNDARY_ROLE：角材 %u 貼的外輪廓邊 e%d 是自由邊，"
                     "boundary 必須貼 FIXED 邊",
                     (unsigned)timber->id, edge_index);
        }
        return false;
    }

    if (!covers_edge) {
        edge_lo = along_v ? wood_reference_min(seg.start.v, seg.end.v)
                          : wood_reference_min(seg.start.u, seg.end.u);
        edge_hi = along_v ? wood_reference_max(seg.start.v, seg.end.v)
                          : wood_reference_max(seg.start.u, seg.end.u);
        cover = wood_reference_min(span_hi, edge_hi) - wood_reference_max(span_lo, edge_lo);
        if (err != NULL) {
            snprintf(err, err_cap,
                     "V_BOUNDARY_ROLE：角材 %u 宣告 boundary，"
                     "但只覆蓋外輪廓邊 e%d 的 %lld / %lld mm——"
                     "固定段必須涵蓋整條邊",
                     (unsigned)timber->id, edge_index,
                     (long long)cover, (long long)(edge_hi - edge_lo));
        }
        return false;
    }

    return true;
}

bool wood_member_place_a0(WoodMember *timber,const GeoFrame *frame,const GeoRegionSetView *domain,
    const int *const *fixities,GeoPoint2 anchor,int direction,int depth)
{
    if(!timber||!frame||!domain)return false;
    bool point_inside=false;
    for(size_t c=0;c<domain->count;++c)if(geo_region_contains_point(&domain->regions[c],anchor)){point_inside=true;break;}
    if(!point_inside)return false;
    GeoVector3 length=geo_frame_direction(frame,(GeoDirection2)direction);
    if(geo_vector_dot(length,length)!=1)return false;
    GeoVector3 b=depth==WOOD_DEPTH_POSITIVE_NORMAL?frame->normal:geo_vector_negate(frame->normal);
    GeoVector3 a=geo_vector_cross(b,length);
    GeoRect2 rect=geo_rectangle_footprint(frame,anchor,length,a,timber->length,timber->size_a);
    size_t component=domain->count;
    for(size_t c=0;c<domain->count;++c)if(geo_region_contains_rect(&domain->regions[c],rect.min_u,rect.min_v,rect.max_u,rect.max_v)){component=c;break;}
    if(component==domain->count)return false;
    if(fixities&&fixities[component]){
        const GeoLoop2View *outline=&domain->regions[component].outline;
        bool ends_along_v=geo_vector_dot(length,frame->axis_u)!=0;
        GeoCoord ends[2]={ends_along_v?rect.min_u:rect.min_v,ends_along_v?rect.max_u:rect.max_v};
        for(int e=0;e<2;++e)for(size_t i=0;i<outline->count;++i){
            GeoPoint2 p=outline->v[i],q=outline->v[(i+1)%outline->count];
            if(ends_along_v){
                if(p.u!=q.u||p.u!=ends[e])continue;
                if(wood_reference_max(rect.min_v,wood_reference_min(p.v,q.v))<wood_reference_min(rect.max_v,wood_reference_max(p.v,q.v))&&fixities[component][i]==WOOD_STOP_FREE)return false;
            }else{
                if(p.v!=q.v||p.v!=ends[e])continue;
                if(wood_reference_max(rect.min_u,wood_reference_min(p.u,q.u))<wood_reference_min(rect.max_u,wood_reference_max(p.u,q.u))&&fixities[component][i]==WOOD_STOP_FREE)return false;
            }
        }
    }
    timber->origin=geo_frame_point(frame,anchor.u,anchor.v,0);
    timber->axis_length=length;timber->axis_a=a;timber->axis_b=b;timber->placed=true;
    return true;
}

static bool wood_reference_boundary_end(const WoodMemberSpanFacts *facts,const WoodMemberSpanRequest *request,
    GeoCoord start,GeoCoord end,int which,const WoodStopFace *required,WoodBoundaryEndAdmission *admission)
{
    *admission=WOOD_BOUNDARY_END_ORDINARY;
    if(!request->self||request->self->role!=WOOD_MEMBER_ROLE_BOUNDARY||!facts->boundary_end)return true;
    return facts->boundary_end(facts->boundary_user,request->self,request->along_v,start,end,
        request->cross_lo,request->cross_hi,which,facts->stops,facts->stop_count,required,admission);
}

static size_t wood_reference_partial_ref_candidates(const WoodMemberSpanFacts *facts,
    const WoodMemberSpanRequest *request,const WoodStopRef *ref,const WoodStopFace **out,size_t count,size_t cap)
{
    if(!request->self||request->self->role!=WOOD_MEMBER_ROLE_BOUNDARY||!facts->boundary_end)return count;
    for(size_t i=0;i<facts->stop_count&&count<cap;++i){const WoodStopFace *face=&facts->stops[i];
        if(face->kind!=WOOD_STOP_MEMBER_SIDE||face->fixity==WOOD_STOP_FREE||!wood_stop_matches_ref(face,ref)||
           (face->lo<=request->cross_lo&&face->hi>=request->cross_hi)||
           face->lo>=request->cross_hi||face->hi<=request->cross_lo)continue;
        out[count++]=face;
    }
    return count;
}

WoodMemberSpanStatus wood_member_resolve_span(const WoodMemberSpanFacts *facts,const WoodMemberSpanRequest *request,
    GeoCoord *out_start,GeoCoord *out_end,char *err,size_t err_cap)
{
    bool along_v=request->along_v,has_contact=request->contact,has_through=request->through;
    GeoCoord cross_lo=request->cross_lo,cross_hi=request->cross_hi,contact_lo=request->contact_lo,contact_hi=request->contact_hi,through=request->through_at;
    const WoodStopRef *between=request->between?request->stops:NULL;
    const GeoRect2 *scope=request->scoped?&request->scope:NULL;
    GeoCoord cuts[WOOD_MEMBER_SPAN_CUT_CAPACITY];
    GeoCoord scope_lo=scope?(along_v?scope->min_v:scope->min_u):0;
    GeoCoord scope_hi=scope?(along_v?scope->max_v:scope->max_u):0;
    if (scope && (cross_lo<(along_v?scope->min_u:scope->min_v) || cross_hi>(along_v?scope->max_u:scope->max_v))) {
        snprintf(err,err_cap,"I13：角材的完整寬度超出子格範圍");
        return WOOD_SPAN_NO_INTERVAL;
    }

    GeoInterval intervals[WOOD_MEMBER_SPAN_CUT_CAPACITY/2+1];
    GeoIntervalBuffer result={intervals,WOOD_MEMBER_SPAN_CUT_CAPACITY/2+1,0};

    GeoGeometryStatus geometry_status=geo_strip_intervals(&facts->domain,along_v,(GeoInterval){cross_lo,cross_hi},
        facts->obstacles,facts->obstacle_count,&result,(GeoStripScratch){cuts,WOOD_MEMBER_SPAN_CUT_CAPACITY});
    if(geometry_status!=GEO_GEOMETRY_OK){
        snprintf(err,err_cap,"中線上沒有任何合法跨距");return WOOD_SPAN_NO_INTERVAL;
    }
    size_t interval_count=result.count;

    if (interval_count == 0) {
        snprintf(err, err_cap, "中線上沒有任何合法跨距");
        return WOOD_SPAN_NO_INTERVAL;
    }

    /* --- at-face 接觸範圍過濾：區間必須與引用邊的範圍重疊 --- */
    if (has_contact) {
        GeoInterval touching[WOOD_MEMBER_SPAN_CUT_CAPACITY / 2 + 1];
        size_t touching_count = 0;

        for (size_t i = 0; i < interval_count; ++i) {
            if (intervals[i].start < contact_hi &&
                intervals[i].end > contact_lo) {
                touching[touching_count++] = intervals[i];
            }
        }

        if (touching_count == 0) {
            snprintf(err, err_cap,
                     "有合法跨距但都不接觸引用的邊");
            return WOOD_SPAN_OUTSIDE_CONTACT;
        }

        memcpy(intervals, touching, touching_count * sizeof(GeoInterval));
        interval_count = touching_count;
    }

    /* R6/D19: scope selects complete intervals; it never supplies stops. */
    if (scope && !between) {
        size_t kept=0;
        for (size_t i=0;i<interval_count;++i)
            if (intervals[i].start>=scope_lo && intervals[i].end<=scope_hi) intervals[kept++]=intervals[i];
        interval_count=kept;
        if (!kept) {
            snprintf(err,err_cap,"I13/R6：子格 [%lld,%lld] 內沒有兩端獲得支撐的完整跨距",(long long)scope_lo,(long long)scope_hi);
            return WOOD_SPAN_NO_INTERVAL;
        }
    }

    /*
     * --- R21：between 明寫兩端 ---
     * 它是消解歧義的選擇器，不是放寬條件：兩個被指名的擋面各自仍須
     * 通過 R6(d) 的物理條件，跨距也仍須整段落在某個合法區間內（R6(b)）。
     */
    if (between != NULL) {
        const WoodStopFace *bfaces=facts->stops;size_t bface_count=facts->stop_count;

        const WoodStopFace *ca[WOOD_MEMBER_SPAN_MEMBER_CAPACITY * 2];
        const WoodStopFace *cb[WOOD_MEMBER_SPAN_MEMBER_CAPACITY * 2];
        bool free_a = false;
        bool free_b = false;
        bool narrow_a = false;
        bool narrow_b = false;
        size_t na = wood_stop_ref_candidates(bfaces, bface_count, &between[0],
                                        cross_lo, cross_hi,
                                        ca, WOOD_MEMBER_SPAN_MEMBER_CAPACITY * 2,
                                        &free_a, &narrow_a);
        size_t nb = wood_stop_ref_candidates(bfaces, bface_count, &between[1],
                                        cross_lo, cross_hi,
                                        cb, WOOD_MEMBER_SPAN_MEMBER_CAPACITY * 2,
                                        &free_b, &narrow_b);
        na=wood_reference_partial_ref_candidates(facts,request,&between[0],ca,na,WOOD_MEMBER_SPAN_MEMBER_CAPACITY*2);
        nb=wood_reference_partial_ref_candidates(facts,request,&between[1],cb,nb,WOOD_MEMBER_SPAN_MEMBER_CAPACITY*2);

        if (na == 0 || nb == 0) {
            const bool is_free = (na == 0 && free_a) || (nb == 0 && free_b);
            const bool is_narrow =
                (na == 0 && narrow_a) || (nb == 0 && narrow_b);

            if (is_free) {
                snprintf(err, err_cap,
                         "between 指名的擋面是自由邊（頂到空氣）");
                return WOOD_SPAN_FREE_EDGE_END;
            }

            snprintf(err, err_cap,
                     is_narrow
                         ? "between 指名的擋面沒有涵蓋角材端面的全寬"
                         : "between 指名的擋面不存在，"
                           "或它不垂直於角材長度軸");
            return WOOD_SPAN_BETWEEN_BLOCKED;
        }

        GeoInterval hit[WOOD_MEMBER_SPAN_MEMBER_CAPACITY * 4];
        size_t hit_count = 0;
        bool bare_rc = false;

        for (size_t x = 0; x < na; ++x) {
            for (size_t y = 0; y < nb; ++y) {
                GeoCoord s = ca[x]->fixed;
                GeoCoord e = cb[y]->fixed;

                if (s == e) {
                    continue;   /* R21(c)：區間必須非空 */
                }

                if (s > e) {
                    const GeoCoord swap = s;

                    s = e;
                    e = swap;
                }

                bool inside = false;

                for (size_t k = 0; k < interval_count; ++k) {
                    if (intervals[k].start <= s && e <= intervals[k].end) {
                        inside = true;
                        break;
                    }
                }

                if (!inside || (scope && (s<scope_lo || e>scope_hi))) {
                    continue;   /* R6: between pairs must be fully inside the child scope. */
                }

                const WoodStopFace *pair[2]={ca[x],cb[y]};bool supported=true;
                for(size_t side=0;side<2;++side){const WoodStopFace *face=pair[side];
                    WoodBoundaryEndAdmission admission;
                    if(!wood_reference_boundary_end(facts,request,s,e,face->fixed==s?0:1,NULL,&admission)){
                        snprintf(err,err_cap,"I8: ordered boundary-end facts unavailable");return WOOD_SPAN_BETWEEN_BLOCKED;
                    }
                    if(admission==WOOD_BOUNDARY_END_BARE_RC){bare_rc=true;supported=false;break;}
                    if(face->lo<=cross_lo&&face->hi>=cross_hi)continue;
                    if(!wood_reference_boundary_end(facts,request,s,e,face->fixed==s?0:1,face,&admission)){
                        snprintf(err,err_cap,"I8: ordered boundary-end facts unavailable");return WOOD_SPAN_BETWEEN_BLOCKED;
                    }
                    if(admission==WOOD_BOUNDARY_END_BARE_RC)bare_rc=true;
                    if(admission!=WOOD_BOUNDARY_END_PARTIAL){supported=false;break;}
                }
                if(!supported)continue;

                if (hit_count < WOOD_MEMBER_SPAN_MEMBER_CAPACITY * 4) {
                    hit[hit_count].start = s;
                    hit[hit_count].end = e;
                    ++hit_count;
                }
            }
        }

        if (hit_count == 0) {
            if(bare_rc){
                snprintf(err,err_cap,"V_CUT_PRIORITY：between 固定段端點有裸露的可放料 RC 面，必須先貼角材");
                return WOOD_SPAN_BETWEEN_BLOCKED;
            }
            snprintf(err, err_cap,
                     "between 指名的兩端之間沒有合法跨距"
                     "（被實體擋住，或兩端座標相同）");
            return WOOD_SPAN_BETWEEN_BLOCKED;
        }

        if (hit_count > 1) {
            size_t n = (size_t)snprintf(err, err_cap,
                                        "between 有多組合法配對：");

            for (size_t k = 0; k < hit_count && n < err_cap; ++k) {
                n += (size_t)snprintf(err + n, err_cap - n, " [%lld,%lld]",
                                      (long long)hit[k].start,
                                      (long long)hit[k].end);
            }

            return WOOD_SPAN_BETWEEN_AMBIGUOUS;
        }

        *out_start = hit[0].start;
        *out_end = hit[0].end;
        return WOOD_SPAN_OK;
    }

    /* --- 選區間 --- */
    size_t chosen = (size_t)-1;

    if (has_through) {
        for (size_t i = 0; i < interval_count; ++i) {
            if (through >= intervals[i].start &&
                through <= intervals[i].end) {
                chosen = i;
                break;
            }
        }

        if (chosen == (size_t)-1) {
            snprintf(err, err_cap,
                     "through 座標不在任何合法跨距內");
            return WOOD_SPAN_THROUGH_OUTSIDE;
        }
    } else if (interval_count > 1) {
        size_t n = (size_t)snprintf(err, err_cap, "跨距歧義：");

        for (size_t i = 0; i < interval_count && n < err_cap; ++i) {
            n += (size_t)snprintf(err + n, err_cap - n, " [%lld,%lld]",
                          (long long)intervals[i].start,
                          (long long)intervals[i].end);
        }
        return WOOD_SPAN_AMBIGUOUS;
    } else {
        chosen = 0;
    }

    GeoCoord span_start = intervals[chosen].start;
    GeoCoord span_end = intervals[chosen].end;

    /* --- 兩端必須各有唯一合法擋面（place 當下不猜） --- */
    const WoodStopFace *faces=facts->stops;size_t face_count=facts->stop_count;

    const WoodStopFace *stop = NULL;
    size_t hits;

    hits = wood_stop_pick(faces, face_count, span_start,
                     cross_lo, cross_hi, &stop);
    {WoodBoundaryEndAdmission admission;
        if(!wood_reference_boundary_end(facts,request,span_start,span_end,0,NULL,&admission)){
            snprintf(err,err_cap,"I8: ordered boundary-end facts unavailable");return WOOD_SPAN_START_UNSUPPORTED;
        }
        if(admission==WOOD_BOUNDARY_END_BARE_RC){
            snprintf(err,err_cap,"V_CUT_PRIORITY：固定段起點有裸露的可放料 RC 面，必須先貼角材");return WOOD_SPAN_START_UNSUPPORTED;
        }
        if(admission==WOOD_BOUNDARY_END_PARTIAL)goto supported_start;
    }
    if (hits == 0) {
        snprintf(err, err_cap, "跨距起點沒有擋面（端面懸空）");
        return WOOD_SPAN_START_UNSUPPORTED;
    }
    if (hits > 1) {
        snprintf(err, err_cap, "跨距起點擋面歧義");
        return WOOD_SPAN_START_AMBIGUOUS;
    }
    if (stop->fixity == WOOD_STOP_FREE) {
        snprintf(err, err_cap, "跨距起點頂到自由邊");
        return WOOD_SPAN_FREE_EDGE_END;
    }

supported_start:
    hits = wood_stop_pick(faces, face_count, span_end,
                     cross_lo, cross_hi, &stop);
    {WoodBoundaryEndAdmission admission;
        if(!wood_reference_boundary_end(facts,request,span_start,span_end,1,NULL,&admission)){
            snprintf(err,err_cap,"I8: ordered boundary-end facts unavailable");return WOOD_SPAN_END_UNSUPPORTED;
        }
        if(admission==WOOD_BOUNDARY_END_BARE_RC){
            snprintf(err,err_cap,"V_CUT_PRIORITY：固定段終點有裸露的可放料 RC 面，必須先貼角材");return WOOD_SPAN_END_UNSUPPORTED;
        }
        if(admission==WOOD_BOUNDARY_END_PARTIAL)goto supported_end;
    }
    if (hits == 0) {
        snprintf(err, err_cap, "跨距終點沒有擋面（端面懸空）");
        return WOOD_SPAN_END_UNSUPPORTED;
    }
    if (hits > 1) {
        snprintf(err, err_cap, "跨距終點擋面歧義");
        return WOOD_SPAN_END_AMBIGUOUS;
    }
    if (stop->fixity == WOOD_STOP_FREE) {
        snprintf(err, err_cap, "跨距終點頂到自由邊");
        return WOOD_SPAN_FREE_EDGE_END;
    }

supported_end:
    *out_start = span_start;
    *out_end = span_end;
    return WOOD_SPAN_OK;
}
