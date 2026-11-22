/* R03 policy A, immutable flat-ceiling/2. The ratified fixed jig is used
 * independently of the v1 ceil/common-domain generator. FT02 seam retreat,
 * R-butt relocation, holes and obstacles remain outside this bounded slice.
 * This W function consumes explicit facts. Native World legality and exact
 * R43 support remain mandatory in the H adapter; oracle is test-only.
 */
#ifndef GEO_WOOD_FLAT_CEILING_JIG_H
#define GEO_WOOD_FLAT_CEILING_JIG_H
#include "flat_ceiling.h"
#define WOOD_FLAT_JIG_POLICY "3641dec4060cfcf062e2f1d55f341ecb5ae5023da4a4d8a3aba2c3c4110b6d58"
#define WOOD_FLAT_JIG_POLICY_DESCRIPTOR "flat-ceiling/2;rectangle-no-holes-no-obstacles;explicit-fixed-rc-boundary;panel-version-and-threshold-parameter-ref;literal-timber-dimensions;oracle-fixed-jig;last-two-steps-merge-split-on-overlap;no-seam-retreat;no-r-butt;first-full-panel-opposite-trim;finish-fill-derived-from-fill;whole-candidate-native-validation;ordinary-world-definitions;no-search-on-load"
static bool wood_flat_jig_build(const int64_t bounds[4],const WoodFlatParameters *v,WoodFlatPlan *p)
{
    memset(p,0,sizeof *p);memcpy(p->bounds,bounds,sizeof p->bounds);
    int64_t w=v->width;
    if(v->length_axis<0||v->length_axis>1||v->gap<0||w<=0||v->depth<=0||v->maximum<=0||v->panel[0]<=0||v->panel[1]<=0)
        return wood_flat_fail(p,"SCHEMA","尺寸須為明示的合法整數，gap 可為零");
    /* The product bridge already enforces D1. Repeat its scalar limits before
     * any arithmetic so a direct W caller cannot overflow size+gap, L+M,
     * hi-lo or 1-length_axis before receiving the same scope refusal. */
    if(v->panel[0]>100000000||v->panel[1]>100000000||v->gap>100000000||w>100000000||v->depth>100000000||v->maximum>100000000)
        return wood_flat_fail(p,"UNSUPPORTED_SCOPE","尺寸不在 D1 或沒有完整四邊材的內部範圍");
    int a=1-v->length_axis,b=v->length_axis;
    int64_t lh=w/2,hh=w-lh;
    for(int axis=0;axis<2;++axis){
        int64_t lo=bounds[axis],hi=bounds[axis+2],size=v->panel[axis];
        if(lo < -100000000||hi>100000000||lo>=hi)
            return wood_flat_fail(p,"UNSUPPORTED_SCOPE","尺寸不在 D1 或沒有完整四邊材的內部範圍");
        int64_t pitch=size+v->gap,D=hi-lo;
        if(D<=2*w)
            return wood_flat_fail(p,"UNSUPPORTED_SCOPE","尺寸不在 D1 或沒有完整四邊材的內部範圍");
        p->origin[axis]=v->start_max[axis]?hi-size:lo;
        int64_t half=v->start_max[axis]?v->gap-v->gap/2:v->gap/2;
        for(int64_t distance=size+half;distance<D;distance+=pitch){
            if(distance+v->gap-half>=D)break; /* both adjacent panel bodies required */
            if(2*distance>2*D-3*w) /* R03_NON_OPPOSITE_CUT_GUARD */
                return wood_flat_fail(p,"POLICY_RULE_CONFLICT","此起鋪需要退最後板縫，會裁切不在對牆的板；未套用舊 oracle 退縫");
            if(p->seam_count[axis]==WOOD_FLAT_LINES)return wood_flat_fail(p,"CAPACITY","每軸超過 64 條板縫；未截短覆蓋");
            p->seams[axis][p->seam_count[axis]++]=v->start_max[axis]?hi-distance:lo+distance;
        }
        qsort(p->seams[axis],p->seam_count[axis],sizeof(int64_t),wood_flat_i64_order);
    }
    int64_t ends[WOOD_FLAT_LINES+2];size_t count=p->seam_count[b];
    ends[0]=bounds[b];memcpy(ends+1,p->seams[b],count*sizeof(int64_t));ends[count+1]=bounds[b+2];
    for(size_t i=0;i<=count;++i){
        int64_t lo=ends[i],hi=ends[i+1],L=hi-lo;
        bool left_seam=i!=0,right_seam=i!=count;
        bool forward=left_seam&&right_seam?!v->start_max[b]:left_seam?true:right_seam?false:!v->start_max[b];
        int64_t anchor=forward?lo:hi,end=forward?hi:lo,dir=forward?1:-1;
        int64_t n=(L+v->maximum-1)/v->maximum; /* R03_CEIL_N */
        if(n<1)n=1;
        if(n>WOOD_FLAT_LINES+1)return wood_flat_fail(p,"CAPACITY","單格超過 64 個記號；未減少支撐");
        for(int64_t j=1;j<n;++j){
            int64_t distance=v->maximum*j; /* R03A_FIXED_JIG */
            if(j==n-1){
                int64_t historical=anchor+dir*distance;
                bool end_seam=forward?right_seam:left_seam;
                int64_t low=end_seam?end-lh:forward?end-w:end;
                int64_t high=end_seam?end+hh:forward?end:end+w;
                if(historical+hh>low&&historical-lh<high){
                    int64_t remainder=L-v->maximum*(n-1);
                    distance=v->maximum*(n-2)+(v->maximum+remainder+1)/2;
                }
            }
            int64_t requested=anchor+dir*distance; /* R03A_LAST_TWO_STEPS_SPLIT */
            if(requested-lh<bounds[b]+w||requested+hh>bounds[b+2]-w)
                return wood_flat_fail(p,"POLICY_RULE_CONFLICT","固定治具記號料與邊界材相交；此矩形子片沒有完整候選");
            if(p->mark_count==WOOD_FLAT_LINES)return wood_flat_fail(p,"CAPACITY","記號超過 64 條；未截短覆蓋");
            size_t at=p->mark_count++;p->marks[at]=requested;p->mark_anchor[at]=anchor;p->mark_delta[at]=requested-anchor;
        }
    }
    /* Sort all three mark fields together; serialized guide sources retain
     * their exact originating seam even when layout starts at the high end. */
    for(size_t i=1;i<p->mark_count;++i)for(size_t j=i;j>0&&p->marks[j]<p->marks[j-1];--j){
        int64_t *arrays[]={p->marks,p->mark_anchor,p->mark_delta};
        for(size_t k=0;k<3;++k){int64_t t=arrays[k][j];arrays[k][j]=arrays[k][j-1];arrays[k][j-1]=t;}
    }
    int64_t A0=bounds[a],A1=bounds[a+2],B0=bounds[b],B1=bounds[b+2];
    if(!wood_flat_add_ab(p,0,a,a,A0,B0,A1,B0+w,B0)||!wood_flat_add_ab(p,0,a,a,A0,B1-w,A1,B1,B1))return false;
    for(size_t i=0;i<p->seam_count[a];++i){
        int64_t c=p->seams[a][i],low=c-lh,high=c+hh;
        if(low<A0+w||high>A1-w)return wood_flat_fail(p,"POLICY_RULE_CONFLICT","主支會碰到沿 RC 材；不能截斷或改成部分骨架");
        /* Without silently changing a live from-fill center, this slice
         * refuses the historical R-butt relocation domain. */
        if(!wood_flat_add_ab(p,1,b,a,low,B0+w,high,B1-w,c))return false;
    }
    if(!wood_flat_add_ab(p,2,b,a,A0,B0+w,A0+w,B1-w,A0)||!wood_flat_add_ab(p,2,b,a,A1-w,B0+w,A1,B1-w,A1))return false;
    int64_t edges[WOOD_FLAT_LINES+2][2];size_t n=p->seam_count[a]+2;
    edges[0][0]=A0;edges[0][1]=A0+w;
    for(size_t i=0;i<p->seam_count[a];++i){edges[i+1][0]=p->seams[a][i]-lh;edges[i+1][1]=p->seams[a][i]+hh;}
    edges[n-1][0]=A1-w;edges[n-1][1]=A1;
    for(size_t i=0;i+1<n;++i){
        int64_t left=edges[i][1],right=edges[i+1][0];
        if(right-left<w)continue; /* locked min-piece policy: no invented sliver */
        for(size_t k=0;k<p->mark_count;++k){int64_t c=p->marks[k];if(!wood_flat_add_ab(p,3,a,a,left,c-lh,right,c+hh,c))return false;}
        for(size_t k=0;k<p->seam_count[b];++k){int64_t c=p->seams[b][k];if(!wood_flat_add_ab(p,4,a,a,left,c-lh,right,c+hh,c))return false;}
    }
    qsort(p->members,p->count,sizeof p->members[0],wood_flat_member_order);
    return true;
}
#endif
