/* R03 policy A, immutable flat-ceiling/3. A bounded no-retreat/no-relocation
 * slice: one true orthogonal region, one global lattice, exact RC spans.
 * This W generator neither reads a golden nor imports the Python oracle.
 * H must still build genuine source references and run full native legality
 * and R43 before exposing a confirmable candidate. Failure publishes no rows.
 */
#ifndef GEO_WOOD_FLAT_CEILING_NOTCH_H
#define GEO_WOOD_FLAT_CEILING_NOTCH_H
#include "flat_ceiling_jig.h"
#define WOOD_FLAT_NOTCH_POLICY "8d734a5128ac6e9e7ed486dbd7f86fc22997bb9a0f38cefd2ad314ecf14f87fc"
#define WOOD_FLAT_NOTCH_POLICY_DESCRIPTOR "flat-ceiling/3;rectangle-or-single-notch-l-no-holes-no-obstacles;explicit-fixed-rc-boundary;panel-version-and-threshold-parameter-ref;literal-timber-dimensions;oracle-fixed-jig;rc-connected-main-spans;reflex-boundary-extension-custom3-custom4;centered-seams-unmodified-jig-marks;no-seam-retreat;no-r-butt;no-fill-or-doubling;one-global-origin;finish-fill-derived-from-fill;whole-candidate-native-validation;ordinary-world-definitions;no-search-on-load"
typedef struct {
    int anchor_edge; /* original outer edge index; -1 for lattice members */
    int role;        /* 0 boundary, 1 primary, 2 secondary, 3 custom */
    int priority;
    int stop_kind[2]; /* 0 original wall edge, 1 canonical member index */
    int stop_index[2];
    bool extension[2];
} WoodNotchSource;
typedef struct {
    WoodFlatPlan base;
    WoodNotchSource source[WOOD_FLAT_MEMBERS];
    size_t order[WOOD_FLAT_MEMBERS];
} WoodNotchPlan;
typedef struct {
    int axis,inside;
    int64_t at,lo,hi;
    bool reflex[2];
} WoodNotchEdge;
typedef struct {
    int64_t bounds[4],notch[4];
    size_t count;
    bool is_l;
    WoodNotchEdge edges[6];
} WoodNotchRegion;
typedef struct { int64_t lo,hi; } WoodNotchInterval;
static int64_t wood_notch_min(int64_t a,int64_t b){return a<b?a:b;}
static int64_t wood_notch_max(int64_t a,int64_t b){return a>b?a:b;}
static bool wood_notch_error(WoodNotchPlan *p,const char *code,const char *why)
{memset(p,0,sizeof *p);p->base.code=code;p->base.reason=why;return false;}
static bool wood_notch_policy(WoodNotchPlan *p,const char *why)
{return wood_notch_error(p,"POLICY_RULE_CONFLICT",why);}
static bool wood_notch_inside2(const WoodNotchRegion *r,int64_t x,int64_t y)
{
    if(x<=2*r->bounds[0]||x>=2*r->bounds[2]||y<=2*r->bounds[1]||y>=2*r->bounds[3])return false;
    return !r->is_l||!(x>2*r->notch[0]&&x<2*r->notch[2]&&y>2*r->notch[1]&&y<2*r->notch[3]);
}
/* The full width band, never its centreline, must fit the true region. */
static bool wood_notch_band(const WoodNotchRegion *r,int axis,int64_t cross_lo,int64_t cross_hi,WoodNotchInterval *v)
{
    int q=1-axis;
    if(cross_lo<r->bounds[q]||cross_hi>r->bounds[q+2]||cross_lo>=cross_hi)return false;
    v->lo=r->bounds[axis];v->hi=r->bounds[axis+2];
    if(r->is_l&&cross_lo<r->notch[q+2]&&r->notch[q]<cross_hi){
        if(r->notch[axis]==v->lo)v->lo=r->notch[axis+2];else v->hi=r->notch[axis];
    }
    return v->lo<v->hi;
}
static bool wood_notch_region(const int64_t (*pts)[2],size_t n,WoodNotchRegion *r)
{
    memset(r,0,sizeof *r);
    if(!pts||(n!=4&&n!=6))return false;
    /* D1 must hold for both endpoints before any turn/area multiplication. */
    for(size_t i=0;i<n;++i)for(int k=0;k<2;++k)
        if(pts[i][k]<-100000000||pts[i][k]>100000000)return false;
    int64_t area=0;int reflex=-1;
    r->bounds[0]=r->bounds[2]=pts[0][0];r->bounds[1]=r->bounds[3]=pts[0][1];
    for(size_t i=0;i<n;++i){
        const int64_t *p=pts[i],*q=pts[(i+1)%n];
        if((p[0]==q[0])==(p[1]==q[1]))return false;
        for(size_t j=0;j<i;++j)if(p[0]==pts[j][0]&&p[1]==pts[j][1])return false;
        for(int k=0;k<2;++k){r->bounds[k]=wood_notch_min(r->bounds[k],p[k]);r->bounds[k+2]=wood_notch_max(r->bounds[k+2],p[k]);}
        area+=p[0]*q[1]-p[1]*q[0];
    }
    if(!area)return false;
    int orientation=area>0?1:-1;
    for(size_t i=0;i<n;++i){
        const int64_t *p=pts[(i+n-1)%n],*q=pts[i],*s=pts[(i+1)%n];
        int64_t turn=(q[0]-p[0])*(s[1]-q[1])-(q[1]-p[1])*(s[0]-q[0]);
        if(!turn)return false;
        if((turn>0?1:-1)!=orientation){if(reflex>=0)return false;reflex=(int)i;}
    }
    r->is_l=n==6;r->count=n;
    if((n==6)!=(reflex>=0))return false;
    if(n==6){
        const int64_t *p=pts[reflex];int missing=-1;
        if(p[0]<=r->bounds[0]||p[0]>=r->bounds[2]||p[1]<=r->bounds[1]||p[1]>=r->bounds[3])return false;
        for(int c=0;c<4;++c){bool found=false;for(size_t i=0;i<n;++i)if(pts[i][0]==r->bounds[(c&1)?2:0]&&pts[i][1]==r->bounds[(c&2)?3:1])found=true;
            if(!found){if(missing>=0)return false;missing=c;}}
        if(missing<0)return false;
        r->notch[0]=(missing&1)?p[0]:r->bounds[0];r->notch[2]=(missing&1)?r->bounds[2]:p[0];
        r->notch[1]=(missing&2)?p[1]:r->bounds[1];r->notch[3]=(missing&2)?r->bounds[3]:p[1];
    }
    int64_t expected=(r->bounds[2]-r->bounds[0])*(r->bounds[3]-r->bounds[1]);
    if(r->is_l)expected-=(r->notch[2]-r->notch[0])*(r->notch[3]-r->notch[1]);
    if(area*orientation!=2*expected)return false;
    for(size_t i=0;i<n;++i){const int64_t *p=pts[i],*q=pts[(i+1)%n];WoodNotchEdge *e=&r->edges[i];
        e->axis=p[0]!=q[0]?0:1;e->at=p[1-e->axis];e->lo=wood_notch_min(p[e->axis],q[e->axis]);e->hi=wood_notch_max(p[e->axis],q[e->axis]);
        e->inside=orientation*(q[e->axis]>p[e->axis]?1:-1)*(e->axis==0?1:-1);
        e->reflex[p[e->axis]>q[e->axis]?1:0]=(int)i==reflex;
        e->reflex[p[e->axis]>q[e->axis]?0:1]=(int)((i+1)%n)==reflex;
        int64_t mid=e->lo+e->hi,side=2*e->at+e->inside;
        if(!wood_notch_inside2(r,e->axis==0?mid:side,e->axis==0?side:mid))return false;
    }
    return true;
}
static bool wood_notch_add(WoodNotchPlan *p,int kind,int axis,const int64_t rect[4],int64_t center,int edge)
{
    size_t at=p->base.count;
    if(!wood_flat_add(&p->base,kind,axis,rect[0],rect[1],rect[2],rect[3],center))return false;
    WoodNotchSource *s=&p->source[at];memset(s,0,sizeof *s);s->anchor_edge=edge;
    s->role=kind==0?0:kind<3?1:2;s->priority=s->role+1;
    s->stop_index[0]=s->stop_index[1]=-1;return true;
}
static size_t wood_notch_subtract(WoodNotchInterval *ivs,size_t n,int64_t lo,int64_t hi)
{
    for(size_t i=0;i<n;){WoodNotchInterval v=ivs[i];
        if(lo>=v.hi||hi<=v.lo){++i;continue;}
        if(lo<=v.lo&&hi>=v.hi){memmove(ivs+i,ivs+i+1,(n-i-1)*sizeof *ivs);--n;continue;}
        if(lo<=v.lo){ivs[i++].lo=hi;continue;}if(hi>=v.hi){ivs[i++].hi=lo;continue;}
        memmove(ivs+i+2,ivs+i+1,(n-i-1)*sizeof *ivs);ivs[i].hi=lo;ivs[i+1]=(WoodNotchInterval){hi,v.hi};++n;i+=2;
    }return n;
}
static size_t wood_notch_free(const WoodNotchRegion *r,const WoodNotchPlan *p,int axis,int64_t lo,int64_t hi,WoodNotchInterval *ivs,size_t take)
{
    if(!wood_notch_band(r,axis,lo,hi,ivs))return 0;
    size_t n=1;int q=1-axis;
    for(size_t i=0;i<take;++i){const int64_t *s=p->base.members[i].rect;
        if(lo<s[q+2]&&s[q]<hi)n=wood_notch_subtract(ivs,n,s[axis],s[axis+2]);}
    return n;
}
/* Reuse v2's exact lattice without creating its rectangular member set. */
static bool wood_notch_lattice(const WoodNotchRegion *r,const WoodFlatParameters *v,WoodNotchPlan *out)
{
    WoodFlatPlan *p=&out->base;int b=v->length_axis;int64_t w=v->width,lh=w/2,hh=w-lh;
    memcpy(p->bounds,r->bounds,sizeof p->bounds);
    for(int k=0;k<2;++k){int64_t lo=r->bounds[k],hi=r->bounds[k+2],D=hi-lo,size=v->panel[k],pitch=size+v->gap;
        if(D<=2*w)return wood_notch_policy(out,"房間無法容納完整壁邊材");
        p->origin[k]=v->start_max[k]?hi-size:lo;
        int64_t half=v->start_max[k]?v->gap-v->gap/2:v->gap/2;
        for(int64_t d=size+half;d<D;d+=pitch){if(d+v->gap-half>=D)break;
            if(p->seam_count[k]==WOOD_FLAT_LINES)return wood_notch_error(out,"CAPACITY","每軸超過 64 條板縫；未截短覆蓋");
            p->seams[k][p->seam_count[k]++]=v->start_max[k]?hi-d:lo+d;}
        qsort(p->seams[k],p->seam_count[k],sizeof(int64_t),wood_flat_i64_order);
        if(p->seam_count[k]){int64_t c=p->seams[k][v->start_max[k]?0:p->seam_count[k]-1],d=v->start_max[k]?hi-c:c-lo,depth=D;
            /* C is sampled half a millimetre toward the starting side. A wall
             * exactly on C must still be the first opposite wall. */
            int64_t c2=2*c+(v->start_max[k]?1:-1);WoodNotchInterval line={r->bounds[1-k],r->bounds[3-k]};
            if(c2>2*r->bounds[k]&&c2<2*r->bounds[k+2]){
                if(r->is_l&&c2>2*r->notch[k]&&c2<2*r->notch[k+2]){
                    if(r->notch[1-k]==line.lo)line.lo=r->notch[3-k];else line.hi=r->notch[1-k];}
                for(size_t j=0;j<r->count;++j){const WoodNotchEdge *e=&r->edges[j];if(e->axis==k)continue;
                    if((v->start_max[k]?2*e->at>=c2:2*e->at<=c2)||wood_notch_max(e->lo,line.lo)>=wood_notch_min(e->hi,line.hi))continue;
                    if(e->inside!=(v->start_max[k]?1:-1))continue;
                    depth=wood_notch_min(depth,v->start_max[k]?hi-e->at:e->at-lo);}
            }
            if(2*d>2*depth-3*w)return wood_notch_policy(out,"凹口處需要 FT02 退縫；本片不改板縫");}
    }
    int64_t ends[WOOD_FLAT_LINES+2];size_t count=p->seam_count[b];ends[0]=r->bounds[b];
    memcpy(ends+1,p->seams[b],count*sizeof(int64_t));ends[count+1]=r->bounds[b+2];
    for(size_t i=0;i<=count;++i){int64_t lo=ends[i],hi=ends[i+1],L=hi-lo;bool ls=i!=0,rs=i!=count;
        bool forward=ls&&rs?!v->start_max[b]:ls?true:rs?false:!v->start_max[b];
        int64_t anchor=forward?lo:hi,end=forward?hi:lo,dir=forward?1:-1,n=(L+v->maximum-1)/v->maximum;if(n<1)n=1;
        if(n>WOOD_FLAT_LINES+1)return wood_notch_error(out,"CAPACITY","單格超過 64 個記號；未減少支撐");
        for(int64_t j=1;j<n;++j){int64_t distance=v->maximum*j;
            if(j==n-1){int64_t h=anchor+dir*distance;bool es=forward?rs:ls;
                int64_t low=es?end-lh:forward?end-w:end,high=es?end+hh:forward?end:end+w;
                if(h+hh>low&&h-lh<high)distance=v->maximum*(n-2)+(v->maximum+L-v->maximum*(n-1)+1)/2;}
            if(p->mark_count==WOOD_FLAT_LINES)return wood_notch_error(out,"CAPACITY","記號超過 64 條；未截短覆蓋");
            size_t at=p->mark_count++;p->marks[at]=anchor+dir*distance;p->mark_anchor[at]=anchor;p->mark_delta[at]=dir*distance;}
    }
    for(size_t i=1;i<p->mark_count;++i)for(size_t j=i;j>0&&p->marks[j]<p->marks[j-1];--j){
        int64_t *arrays[]={p->marks,p->mark_anchor,p->mark_delta};for(size_t k=0;k<3;++k){int64_t t=arrays[k][j];arrays[k][j]=arrays[k][j-1];arrays[k][j-1]=t;}}
    return true;
}
static bool wood_notch_extension_contact(const WoodNotchRegion *r,const WoodNotchPlan *p,size_t holder,const int64_t contact[4],int axis)
{
    const WoodNotchSource *s=&p->source[holder];const WoodFlatMember *m=&p->base.members[holder];
    if(s->role!=0||s->anchor_edge<0||m->axis==axis)return false;
    const WoodNotchEdge *e=&r->edges[s->anchor_edge];int q=m->axis;
    return contact[q]<e->lo||contact[q+2]>e->hi;
}
static bool wood_notch_resolve(const WoodNotchRegion *r,WoodNotchPlan *p)
{
    for(size_t i=0;i<p->base.count;++i){WoodFlatMember *m=&p->base.members[i];WoodNotchSource *s=&p->source[i];
        int k=m->axis,q=1-k;
        if(s->anchor_edge>=0&&s->role==0){const WoodNotchEdge *e=&r->edges[s->anchor_edge];s->extension[0]=m->rect[k]<e->lo;s->extension[1]=m->rect[k+2]>e->hi;}
        for(int end=0;end<2;++end){int found=-1;int64_t at=m->rect[k+2*end];
            for(size_t j=0;j<p->base.count;++j)if(i!=j){const WoodFlatMember *other=&p->base.members[j];const int64_t *t=other->rect;
                if(other->axis==k||t[k+2*(1-end)]!=at||t[q]>m->rect[q]||t[q+2]<m->rect[q+2])continue;
                if(found>=0)return wood_notch_policy(p,"端面有多個完整擋面；本片不猜選來源");
                found=(int)j;}
            if(found>=0){s->stop_kind[end]=1;s->stop_index[end]=found;continue;}
            if(s->role!=0)return wood_notch_policy(p,"凹角端面沒有唯一全寬角材承接；需要移料或其他政策");
            for(size_t j=0;j<r->count;++j){const WoodNotchEdge *e=&r->edges[j];if(e->axis==k||e->at!=at||e->lo>m->rect[q]||e->hi<m->rect[q+2])continue;
                if(found>=0)return wood_notch_policy(p,"壁邊材端面牆來源不唯一");
                found=(int)j;}
            if(found<0)return wood_notch_policy(p,"壁邊材端面需要部分接觸或互頂組；本片只收完整擋面");
            s->stop_kind[end]=0;s->stop_index[end]=found;
        }
    }
    /* The selected custom3/custom4 policy changes declarations, never points. */
    for(size_t i=0;i<p->base.count;++i)if(p->base.members[i].kind==2){for(int end=0;end<2;++end)if(p->source[i].stop_kind[end]==1&&
        wood_notch_extension_contact(r,p,(size_t)p->source[i].stop_index[end],p->base.members[i].rect,p->base.members[i].axis)){
            p->source[i].role=3;p->source[i].priority=3;}}
    for(size_t i=0;i<p->base.count;++i)if(p->base.members[i].kind>=3){for(int end=0;end<2;++end)if(p->source[i].stop_kind[end]==1){
        const WoodNotchSource *other=&p->source[p->source[i].stop_index[end]];if(other->role==3&&other->priority==3){p->source[i].role=3;p->source[i].priority=4;}}}
    for(size_t i=0;i<p->base.count;++i)for(int end=0;end<2;++end)if(p->source[i].stop_kind[end]==1){
        size_t j=(size_t)p->source[i].stop_index[end];WoodNotchSource *s=&p->source[i],*t=&p->source[j];
        int priority=wood_notch_extension_contact(r,p,j,p->base.members[i].rect,p->base.members[i].axis)?2:t->priority;
        if(s->role==0&&(s->extension[end]||t->role==0))continue;
        if(priority>=s->priority)return wood_notch_policy(p,"凹角擋面違反 I19／I22；不能把主支截在延伸段");
    }
    bool done[WOOD_FLAT_MEMBERS]={false};
    for(size_t at=0;at<p->base.count;++at){size_t pick=p->base.count;
        for(size_t i=0;i<p->base.count;++i)if(!done[i]){bool ready=true;for(int end=0;end<2;++end)if(p->source[i].stop_kind[end]==1&&!done[p->source[i].stop_index[end]])ready=false;
            if(ready){pick=i;break;}}
        if(pick==p->base.count)return wood_notch_policy(p,"凹角接法需要循環放置或衍生宿主互頂組；本片不支援");
        done[pick]=true;p->order[at]=pick;
    }return true;
}
static bool wood_notch_no_rbutt(const WoodFlatParameters *v,int64_t xnum,int64_t xden,WoodNotchPlan *p)
{
    int a=1-v->length_axis,b=v->length_axis;int64_t w=v->width,lh=w/2,hh=w-lh;
    int64_t xceil=xnum/xden+(xnum%xden!=0);
    for(size_t i=0;i<p->base.count;++i){const WoodFlatMember *m=&p->base.members[i];
        if(m->kind==1)for(size_t j=0;j<p->base.count;++j)if(p->base.members[j].kind==2){const int64_t *s=p->base.members[j].rect;
            if(m->rect[b]>=s[b+2]||s[b]>=m->rect[b+2])continue;
            int64_t low_gap=m->rect[a]-s[a+2],high_gap=s[a]-m->rect[a+2];
            if((low_gap>0&&hh-(v->gap-v->gap/2)-low_gap>=xceil)||(high_gap>0&&lh-v->gap/2-high_gap>=xceil))
                return wood_notch_policy(p,"主支在承接範圍內需要 R-butt 貼靠；本片不移主支");
        }
    }return true;
}
static bool wood_notch_validate(const WoodNotchRegion *r,const WoodFlatParameters *v,int64_t xnum,int64_t xden,WoodNotchPlan *p)
{
    int a=1-v->length_axis,b=v->length_axis;int64_t w=v->width;
    int64_t xceil=xnum/xden+(xnum%xden!=0);
    for(size_t i=0;i<p->base.count;++i){const WoodFlatMember *m=&p->base.members[i];WoodNotchInterval iv;
        if(!wood_notch_band(r,m->axis,m->rect[1-m->axis],m->rect[3-m->axis],&iv)||m->rect[m->axis]<iv.lo||m->rect[m->axis+2]>iv.hi)
            return wood_notch_policy(p,"角材完整足跡穿入凹口；不能用中心線或外接盒代替");
        for(size_t j=0;j<i;++j){const int64_t *s=p->base.members[j].rect;if(m->rect[0]<s[2]&&s[0]<m->rect[2]&&m->rect[1]<s[3]&&s[1]<m->rect[3])return wood_notch_policy(p,"凹角材有正面積重疊；需要移料政策");}
    }
    if(!wood_notch_no_rbutt(v,xnum,xden,p))return false;
    /* Check every open slab, not a centreline sampling or one room bbox.
     * A dropped jig mark that would need fill/P-180 fails the same M-w bound. */
    int64_t cuts[2*WOOD_FLAT_MEMBERS+8];size_t nc=0;cuts[nc++]=r->bounds[a];cuts[nc++]=r->bounds[a+2];
    if(r->is_l){cuts[nc++]=r->notch[a];cuts[nc++]=r->notch[a+2];}
    for(size_t i=0;i<p->base.count;++i){cuts[nc++]=p->base.members[i].rect[a];cuts[nc++]=p->base.members[i].rect[a+2];}
    qsort(cuts,nc,sizeof *cuts,wood_flat_i64_order);
    for(size_t z=1;z<nc;++z)if(cuts[z]>cuts[z-1]){WoodNotchInterval ivs[WOOD_FLAT_MEMBERS+2];size_t n=1;
        if(!wood_notch_band(r,b,cuts[z-1],cuts[z],ivs))continue;
        int64_t mid=cuts[z-1]+cuts[z];
        for(size_t i=0;i<p->base.count;++i){const int64_t *s=p->base.members[i].rect;if(2*s[a]<mid&&mid<2*s[a+2])n=wood_notch_subtract(ivs,n,s[b],s[b+2]);}
        for(size_t i=0;i<n;++i)if(ivs[i].hi-ivs[i].lo>v->maximum-w)return wood_notch_policy(p,"凹口截去記號後超過固定治具間距；需要補位或挪副支");
    }
    /* A seam member cannot silently disappear when its centred width clips
     * a boundary strip. Prove the whole X support band on each existing panel
     * side, split at every true region/member coordinate. If the old policy
     * would move a seam member against a stop, this no-relocation slice fails.
     * Integer geometry makes ceil(X) conservative for a rational threshold;
     * the H adapter still checks exact R43 against the true clipped panels. */
    for(int axis=0;axis<2;++axis){int q=1-axis;nc=0;
        cuts[nc++]=r->bounds[q];cuts[nc++]=r->bounds[q+2];
        if(r->is_l){cuts[nc++]=r->notch[q];cuts[nc++]=r->notch[q+2];}
        for(size_t i=0;i<p->base.count;++i){cuts[nc++]=p->base.members[i].rect[q];cuts[nc++]=p->base.members[i].rect[q+2];}
        qsort(cuts,nc,sizeof *cuts,wood_flat_i64_order);
        for(size_t j=0;j<p->base.seam_count[axis];++j)for(int side=0;side<2;++side){
            int64_t c=p->base.seams[axis][j],edge=side?c+(v->gap-v->gap/2):c-v->gap/2;
            int64_t low=side?edge:edge-xceil,high=side?edge+xceil:edge;
            for(size_t z=1;z<nc;++z)if(cuts[z]>cuts[z-1]){
                int64_t mid=cuts[z-1]+cuts[z],inside=2*edge+(side?1:-1);
                if(!wood_notch_inside2(r,axis==0?inside:mid,axis==0?mid:inside))continue;
                WoodNotchInterval ivs[WOOD_FLAT_MEMBERS+2]={{low,high}};size_t count=1;
                for(size_t i=0;i<p->base.count;++i){const int64_t *s=p->base.members[i].rect;
                    if(s[q]<=cuts[z-1]&&s[q+2]>=cuts[z])count=wood_notch_subtract(ivs,count,s[axis],s[axis+2]);}
                if(count)return wood_notch_policy(p,"固定板縫的承接帶未全覆蓋；需要挪縫上副支，本片不移料");
            }
        }
    }
    return true;
}
static bool wood_notch_build(const int64_t (*points)[2],size_t n,const WoodFlatParameters *v,int64_t threshold_num,int64_t threshold_den,WoodNotchPlan *out)
{
    WoodNotchRegion region;memset(out,0,sizeof *out);
    if(!v||v->length_axis<0||v->length_axis>1||v->gap<0||v->gap>100000000||v->width<=0||v->width>100000000||v->depth<=0||v->depth>100000000||v->maximum<=0||v->maximum>100000000||v->panel[0]<=0||v->panel[0]>100000000||v->panel[1]<=0||v->panel[1]>100000000||threshold_num<=0||threshold_den<=0)
        return wood_notch_error(out,"SCHEMA","尺寸、方向與承接門檻須為明示的合法值");
    if(!wood_notch_region(points,n,&region))return wood_notch_error(out,"UNSUPPORTED_SCOPE","本片只收軸向矩形或單角缺口 L 形；不以外接盒取代輪廓");
    if(!region.is_l){if(!wood_flat_jig_build(region.bounds,v,&out->base)){const char *c=out->base.code,*why=out->base.reason;return wood_notch_error(out,c,why);}
        /* Rectangle keeps v2 geometry and its R-butt gate. Do not run the
         * notch-only support preflight here: native R43 remains its oracle. */
        if(!wood_notch_no_rbutt(v,threshold_num,threshold_den,out))return false;
        for(size_t i=0;i<out->base.count;++i){WoodFlatMember *m=&out->base.members[i];WoodNotchSource *s=&out->source[i];s->anchor_edge=-1;s->role=m->kind==0?0:m->kind<3?1:2;s->priority=s->role+1;
            if(m->kind==0||m->kind==2)for(size_t j=0;j<region.count;++j){const WoodNotchEdge *e=&region.edges[j];int q=1-m->axis;
                if(e->axis==m->axis&&(e->inside>0?m->rect[q]==e->at:m->rect[q+2]==e->at))s->anchor_edge=(int)j;}
        }return wood_notch_resolve(&region,out);}
    if(!wood_flat_width_enough(v->width,threshold_num,threshold_den))
        return wood_notch_policy(out,"明示料寬小於承接門檻；不能產出完整板邊支撐");
    if(!wood_notch_lattice(&region,v,out))return false;
    int a=1-v->length_axis,b=v->length_axis;int64_t w=v->width,lh=w/2,hh=w-lh;
    /* Boundary fixed portions first; their reflex extensions are added after
     * complete RC-connected main spans are available as real stops. */
    for(size_t i=0;i<n;++i){const WoodNotchEdge *e=&region.edges[i];if(e->axis!=a)continue;
        int64_t rect[4];rect[a]=e->lo;rect[a+2]=e->hi;rect[b]=e->inside>0?e->at:e->at-w;rect[b+2]=rect[b]+w;
        if(!wood_notch_add(out,0,a,rect,e->at,(int)i))goto failed;
    }
    size_t fixed=out->base.count;
    for(size_t i=0;i<out->base.seam_count[a];++i){int64_t c=out->base.seams[a][i];WoodNotchInterval spans[WOOD_FLAT_MEMBERS+2];
        size_t ns=wood_notch_free(&region,out,b,c-lh,c+hh,spans,fixed);
        for(size_t j=0;j<ns;++j){int64_t rect[4];rect[a]=c-lh;rect[a+2]=c+hh;rect[b]=spans[j].lo;rect[b+2]=spans[j].hi;
            if(rect[b+2]-rect[b]<w)return wood_notch_policy(out,"凹口留下短於料寬的主支段；本片不生成短料");
            if(!wood_notch_add(out,1,b,rect,c,-1))goto failed;}
    }
    for(size_t i=0;i<n;++i){const WoodNotchEdge *e=&region.edges[i];if(e->axis!=b)continue;
        int64_t cross=e->inside>0?e->at:e->at-w;WoodNotchInterval spans[WOOD_FLAT_MEMBERS+2];
        size_t ns=wood_notch_free(&region,out,b,cross,cross+w,spans,fixed);
        for(size_t j=0;j<ns;++j){int64_t lo=wood_notch_max(e->lo,spans[j].lo),hi=wood_notch_min(e->hi,spans[j].hi);if(hi<=lo)continue;
            if(hi-lo<w)return wood_notch_policy(out,"凹口沿牆段短於料寬；本片不套用薄牆階接法");
            int64_t rect[4];rect[a]=cross;rect[a+2]=cross+w;rect[b]=lo;rect[b+2]=hi;
            if(!wood_notch_add(out,2,b,rect,e->at,(int)i))goto failed;}
    }
    for(size_t i=0;i<fixed;++i){WoodFlatMember *m=&out->base.members[i];const WoodNotchEdge *e=&region.edges[out->source[i].anchor_edge];
        for(int end=0;end<2;++end)if(e->reflex[end]){int64_t at=m->rect[a+2*end],stop=at;bool found=false;
            for(size_t j=0;j<out->base.count;++j)if(j!=i){const int64_t *s=out->base.members[j].rect;if(s[b]>=m->rect[b+2]||m->rect[b]>=s[b+2])continue;
                int64_t side=s[a+2*(1-end)];if(end?side<at:side>at)continue;
                if(!found||(end?side<stop:side>stop)){stop=side;found=true;}}
            if(!found)return wood_notch_policy(out,"凹角延伸段沒有真實擋面；不讓邊界材懸空");
            m->rect[a+2*end]=stop;
        }
    }
    size_t supports=out->base.count;
    for(int kind=3;kind<=4;++kind){size_t nc=kind==3?out->base.mark_count:out->base.seam_count[b];int64_t *cs=kind==3?out->base.marks:out->base.seams[b];
        for(size_t k=0;k<nc;++k){int64_t c=cs[k];WoodNotchInterval spans[WOOD_FLAT_MEMBERS+2];size_t ns=wood_notch_free(&region,out,a,c-lh,c+hh,spans,supports);
            for(size_t j=0;j<ns;++j){if(spans[j].hi-spans[j].lo<w)return wood_notch_policy(out,"凹口形成短料跨；本片不省略後宣稱完整支撐");
                int64_t rect[4];rect[a]=spans[j].lo;rect[a+2]=spans[j].hi;rect[b]=c-lh;rect[b+2]=c+hh;
                if(!wood_notch_add(out,kind,a,rect,c,-1))goto failed;}
        }
    }
    if(!wood_notch_validate(&region,v,threshold_num,threshold_den,out))return false;
    for(size_t i=1;i<out->base.count;++i)for(size_t j=i;j>0&&wood_flat_member_order(&out->base.members[j],&out->base.members[j-1])<0;--j){
        WoodFlatMember m=out->base.members[j];out->base.members[j]=out->base.members[j-1];out->base.members[j-1]=m;
        WoodNotchSource s=out->source[j];out->source[j]=out->source[j-1];out->source[j-1]=s;}
    return wood_notch_resolve(&region,out);
failed:
    {const char *c=out->base.code,*why=out->base.reason;return wood_notch_error(out,c,why);}
}
#endif
