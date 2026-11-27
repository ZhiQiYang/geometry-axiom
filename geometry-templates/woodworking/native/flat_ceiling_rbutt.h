/* R03 R1: immutable, rectangle-only, RC-parallel R-butt over explicit facts.
 * The original seam stays live; a signed offset locates the main member.
 * FT02, collision push and adjacent-main butt require later slices. This
 * planner is not a native legality or R43 substitute. */
#ifndef GEO_WOOD_FLAT_CEILING_RBUTT_H
#define GEO_WOOD_FLAT_CEILING_RBUTT_H
#include "flat_ceiling_jig.h"
#define WOOD_FLAT_RBUTT_POLICY "2e4d5dc2507d00558dfd5a02389391101210c999bed8265bbee0a2656e2b9de7"
#define WOOD_FLAT_RBUTT_POLICY_DESCRIPTOR "flat-ceiling-rbutt/1;rectangle-no-holes-no-obstacles;explicit-fixed-rc-boundary;panel-version-and-threshold-parameter-ref;literal-timber-dimensions;oracle-fixed-jig;last-two-steps-merge-split-on-overlap;no-seam-retreat;rc-parallel-r-butt;nearest-gap-tie-negative;existing-contact-stays;live-original-seam-plus-named-offset;rebuild-secondary-spans;whole-candidate-native-and-r43-validation;ordinary-world-definitions;no-search-on-load;adjacent-main-butt-out-of-scope"
static bool wood_flat_rbutt_build(const int64_t bounds[4],const WoodFlatParameters *v,
                                int64_t xnum,int64_t xden,WoodFlatPlan *p,
                                int64_t shifts[WOOD_FLAT_LINES])
{
    memset(shifts,0,sizeof(int64_t)*WOOD_FLAT_LINES);
    if(xnum<=0||xden<=0){memset(p,0,sizeof *p);return wood_flat_fail(p,"SCHEMA","承接門檻須為明示正有理數");}
    if(!wood_flat_jig_build(bounds,v,p))return false;
    int a=1-v->length_axis,b=v->length_axis;
    int64_t w=v->width,lh=w/2,hh=w-lh,gl=v->gap/2,gu=v->gap-gl;
    int64_t A0=bounds[a],A1=bounds[a+2];
    for(size_t i=0;i<p->seam_count[a];++i){
        int64_t c=p->seams[a][i],left=c-lh-A0-w,right=A1-w-c-hh;
        /* Contact already exists: do not chase the opposite wall. */
        if(left==0||right==0)continue; /* R03R_EXISTING_CONTACT */
        bool negative=left>0&&wood_flat_width_enough(hh-gu-left,xnum,xden);
        bool positive=right>0&&wood_flat_width_enough(lh-gl-right,xnum,xden); /* R03R_EXACT_THRESHOLD */
        int64_t shift=negative?-left:0;
        if(positive&&(!negative||right<left))shift=right; /* R03R_NEAREST_TIE_NEGATIVE */
        shifts[i]=shift; /* R03R_APPLY_SHIFT */
    }
    int64_t edges[WOOD_FLAT_LINES+2][2];size_t n=p->seam_count[a]+2;
    edges[0][0]=A0;edges[0][1]=A0+w;
    for(size_t i=0;i<p->seam_count[a];++i){
        int64_t c=p->seams[a][i]+shifts[i];
        edges[i+1][0]=c-lh;edges[i+1][1]=c+hh;
    }
    edges[n-1][0]=A1-w;edges[n-1][1]=A1;
    /* Explicit bounded contract: this slice only chooses a parallel RC
     * neighbour. Do not silently accept the separate adjacent-main domain. */
    for(size_t i=1;i+2<n;++i){
        int64_t gap=edges[i+1][0]-edges[i][1];
        if(gap<0)return wood_flat_fail(p,"POLICY_RULE_CONFLICT","主支足跡重疊，未交付部分骨架");
        if(gap>0&&(wood_flat_width_enough(lh-gl-gap,xnum,xden)||wood_flat_width_enough(hh-gu-gap,xnum,xden)))
            return wood_flat_fail(p,"UNSUPPORTED_SCOPE","相鄰主支可貼域不在沿 RC 的 R-butt 首片範圍"); /* R03R_ADJACENT_MAIN_SCOPE */
    }
    size_t kept=0;
    for(size_t k=0;k<p->count;++k){
        WoodFlatMember m=p->members[k];if(m.kind>=3)continue;
        if(m.kind==1){
            size_t i=0;while(i<p->seam_count[a]&&p->seams[a][i]!=m.center)++i;
            if(i==p->seam_count[a])return wood_flat_fail(p,"POLICY_RULE_CONFLICT","主支缺少原板縫來源");
            m.rect[a]+=shifts[i];m.rect[a+2]+=shifts[i];
            /* m.center is deliberately the original seam identity. */
        }
        p->members[kept++]=m;
    }
    p->count=kept;
    for(size_t i=0;i+1<n;++i){
        int64_t left=edges[i][1],right=edges[i+1][0]; /* R03R_REBUILD_SECONDARY */
        if(right-left<w)continue; /* locked min-piece: equality is retained */
        for(size_t k=0;k<p->mark_count;++k){int64_t c=p->marks[k];if(!wood_flat_add_ab(p,3,a,a,left,c-lh,right,c+hh,c))return false;}
        for(size_t k=0;k<p->seam_count[b];++k){int64_t c=p->seams[b][k];if(!wood_flat_add_ab(p,4,a,a,left,c-lh,right,c+hh,c))return false;}
    }
    qsort(p->members,p->count,sizeof p->members[0],wood_flat_member_order);
    return true;
}
#endif
