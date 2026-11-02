#include "contact_world.h"
#include <stdio.h>
#include <string.h>

static GeoCoord contact_min(GeoCoord a,GeoCoord b){return a<b?a:b;}
static GeoCoord contact_max(GeoCoord a,GeoCoord b){return a>b?a:b;}
static bool contact_contains(const WoodBoundaryRegion *b,const GeoRect2 *rect)
{
    if(!b||b->hole_count>GEO_REGION_MAX_HOLES)return false;
    GeoLoop2View holes[GEO_REGION_MAX_HOLES];
    for(size_t h=0;h<b->hole_count;++h)holes[h]=(GeoLoop2View){b->holes[h].v,b->holes[h].count};
    GeoRegionView region={{b->outline.v,b->outline.count},holes,b->hole_count};
    return geo_region_contains_rect(&region,rect->min_u,rect->min_v,rect->max_u,rect->max_v);
}
enum { CONTACT_ORDER_SLOTS=WOOD_CONTACT_MEMBER_CAPACITY*2 };
typedef struct {
    size_t last[CONTACT_ORDER_SLOTS];
    uint64_t minimum[CONTACT_ORDER_SLOTS];
    bool indexed;
} ContactOrderIndex;
static size_t contact_order_slot(const WoodContactWorld *world,const ContactOrderIndex *index,uint32_t id)
{
    size_t slot=((id^(id>>16))*UINT32_C(2654435761))%CONTACT_ORDER_SLOTS;
    while(index->last[slot]&&world->members[index->last[slot]-1].member->id!=id)
        slot=(slot+1)%CONTACT_ORDER_SLOTS;
    return slot;
}
static void contact_order_index(const WoodContactWorld *world,ContactOrderIndex *index)
{
    memset(index->last,0,sizeof index->last);
    index->indexed=world->member_count<=WOOD_CONTACT_MEMBER_CAPACITY;
    if(!index->indexed)return;
    /* 僅在本次查詢內索引全部事實；不跨候選快取，也不改變容量。
     * 重複 ID 的舊語義分開保留：排序取最後一筆，遮蓋判斷取最早順序。 */
    for(size_t i=0;i<world->member_count;++i){
        size_t slot=contact_order_slot(world,index,world->members[i].member->id);
        if(!index->last[slot]||world->members[i].order<index->minimum[slot])index->minimum[slot]=world->members[i].order;
        index->last[slot]=i+1;
    }
}
static uint64_t contact_order(const WoodContactWorld *world,const ContactOrderIndex *index,uint32_t id)
{
    if(index->indexed){size_t last=index->last[contact_order_slot(world,index,id)];return last?world->members[last-1].order:UINT64_MAX;}
    uint64_t order=UINT64_MAX;
    for(size_t i=0;i<world->member_count;++i)if(world->members[i].member->id==id)order=world->members[i].order;
    return order;
}
static bool contact_earlier(const WoodContactWorld *world,const ContactOrderIndex *index,uint32_t id,uint64_t order)
{
    if(index->indexed){size_t slot=contact_order_slot(world,index,id);return index->last[slot]&&index->minimum[slot]<order;}
    for(size_t i=0;i<world->member_count;++i)if(world->members[i].member->id==id&&world->members[i].order<order)return true;
    return false;
}
size_t wood_contact_collect_stops(const WoodContactWorld *world,bool along_v,const WoodMember *exclude,WoodStopFace *out,size_t cap)
{
    size_t count=0;
    for(size_t component=0;component<world->region_count;++component){
        const WoodBoundaryRegion *boundary=world->regions[component];if(!boundary)continue;
        const WoodBoundaryLoop *loops[1+GEO_REGION_MAX_HOLES];int hole_of[1+GEO_REGION_MAX_HOLES];size_t loop_count=0;
        loops[loop_count]=&boundary->outline;hole_of[loop_count++]=-1;
        for(size_t h=0;h<boundary->hole_count;++h){loops[loop_count]=&boundary->holes[h];hole_of[loop_count++]=(int)h;}
        for(size_t li=0;li<loop_count;++li){const WoodBoundaryLoop *loop=loops[li];
            for(size_t i=0;i<loop->count&&count<cap;++i){GeoPoint2 a=loop->v[i],b=loop->v[(i+1)%loop->count];
                if(along_v&&a.v!=b.v)continue;if(!along_v&&a.u!=b.u)continue;
                out[count++]=(WoodStopFace){hole_of[li]<0?WOOD_STOP_OUTLINE_EDGE:WOOD_STOP_HOLE_EDGE,boundary->id,0,
                    hole_of[li]<0?-1:(int)(component*GEO_REGION_MAX_HOLES)+hole_of[li],
                    hole_of[li]<0?(int)(component*GEO_LOOP_MAX_VERTICES+i):(int)i,loop->fixity[i],
                    along_v?a.v:a.u,along_v?contact_min(a.u,b.u):contact_min(a.v,b.v),
                    along_v?contact_max(a.u,b.u):contact_max(a.v,b.v)};
            }
        }
    }
    for(size_t i=0;i<world->member_count&&count+2<=cap;++i){const WoodContactMemberFact *fact=&world->members[i];const WoodMember *member=fact->member;
        if(!member->placed||member==exclude||fact->placement_id!=world->placement_id||!fact->footprint_valid)continue;
        const GeoRect2 *f=&fact->footprint;
        if(along_v){
            out[count++]=(WoodStopFace){WOOD_STOP_MEMBER_SIDE,0,member->id,-1,0,WOOD_STOP_FIXED,f->min_v,f->min_u,f->max_u};
            out[count++]=(WoodStopFace){WOOD_STOP_MEMBER_SIDE,0,member->id,-1,1,WOOD_STOP_FIXED,f->max_v,f->min_u,f->max_u};
        }else{
            out[count++]=(WoodStopFace){WOOD_STOP_MEMBER_SIDE,0,member->id,-1,0,WOOD_STOP_FIXED,f->min_u,f->min_v,f->max_v};
            out[count++]=(WoodStopFace){WOOD_STOP_MEMBER_SIDE,0,member->id,-1,1,WOOD_STOP_FIXED,f->max_u,f->min_v,f->max_v};
        }
    }
    /* D11 placement order is independent of declaration order. Stable ties
     * retain the two side identities in their original order. */
    ContactOrderIndex orders;contact_order_index(world,&orders);
    for(size_t i=1;i<count;++i){
        if(out[i].kind!=WOOD_STOP_MEMBER_SIDE)continue;
        uint64_t order=contact_order(world,&orders,out[i].timber_id);size_t j=i;WoodStopFace value=out[i];
        while(j&&out[j-1].kind==WOOD_STOP_MEMBER_SIDE){
            uint64_t previous=contact_order(world,&orders,out[j-1].timber_id);if(previous<=order)break;
            out[j]=out[j-1];--j;
        }
        out[j]=value;
    }
    /* Keep the original live-set deletion order, including duplicate IDs
     * whose minimum/last orders can make two faces shadow one another.
     * The usual bounded buffer needs only one final stable compaction;
     * larger public caller buffers retain the original in-place fallback. */
    bool active[WOOD_CONTACT_FACE_CAPACITY];
    bool compact=count<=WOOD_CONTACT_FACE_CAPACITY;size_t remaining=count;
    if(compact)for(size_t i=0;i<count;++i)active[i]=true;
    for(size_t i=0;i<count;){bool duplicate=false;
        if(out[i].kind==WOOD_STOP_MEMBER_SIDE){uint64_t order=contact_order(world,&orders,out[i].timber_id);
            for(size_t j=0;j<count&&!duplicate;++j){
                if(compact&&!active[j])continue;
                if(i==j||out[i].fixed!=out[j].fixed||out[i].lo>=out[j].hi||out[j].lo>=out[i].hi)continue;
                bool earlier=out[j].kind!=WOOD_STOP_MEMBER_SIDE;
                if(!earlier)earlier=contact_earlier(world,&orders,out[j].timber_id,order);
                if(earlier&&out[j].lo<=out[i].lo&&out[j].hi>=out[i].hi)duplicate=true;
            }
        }
        if(duplicate){
            if(compact){active[i]=false;--remaining;++i;}
            else{memmove(out+i,out+i+1,(count-i-1)*sizeof *out);--count;}
        }else ++i;
    }
    if(compact){size_t write=0;
        for(size_t i=0;i<count;++i)if(active[i]){if(write!=i)out[write]=out[i];++write;}
        return remaining;
    }
    return count;
}
bool wood_contact_boundary_edge(const WoodBoundaryRegion *boundary,bool along_v,
    GeoCoord span_lo,GeoCoord span_hi,GeoCoord cross_lo,GeoCoord cross_hi,GeoCoord *out_lo,GeoCoord *out_hi,int *out_edge)
{
    GeoRect2 rect={along_v?cross_lo:span_lo,along_v?span_lo:cross_lo,along_v?cross_hi:span_hi,along_v?span_hi:cross_hi};
    if(!contact_contains(boundary,&rect))return false;
    bool on_boundary=false,covers_edge=false;int edge=-1;GeoLoop2View outline={boundary->outline.v,boundary->outline.count};
    if(!wood_member_boundary_props(&outline,along_v,span_lo,span_hi,cross_lo,cross_hi,&on_boundary,&covers_edge,&edge)||!on_boundary||edge<0||(size_t)edge>=outline.count)return false;
    GeoPoint2 a=outline.v[edge],b=outline.v[((size_t)edge+1)%outline.count];
    *out_lo=along_v?contact_min(a.v,b.v):contact_min(a.u,b.u);
    *out_hi=along_v?contact_max(a.v,b.v):contact_max(a.u,b.u);if(out_edge)*out_edge=edge;return true;
}
bool wood_contact_boundary_interval(const WoodBoundaryRegion *boundary,bool along_v,
    GeoCoord span_lo,GeoCoord span_hi,GeoCoord cross_lo,GeoCoord cross_hi,GeoCoord *out_lo,GeoCoord *out_hi)
{return wood_contact_boundary_edge(boundary,along_v,span_lo,span_hi,cross_lo,cross_hi,out_lo,out_hi,NULL);}
bool wood_contact_owner_extension(const WoodContactWorld *world,const WoodMember *owner,GeoCoord lo,GeoCoord hi)
{
    if(owner->role!=WOOD_MEMBER_ROLE_BOUNDARY)return false;
    for(size_t i=0;i<world->member_count;++i){const WoodContactMemberFact *fact=&world->members[i];
        if(fact->member!=owner)continue;if(!fact->footprint_valid)return false;
        const GeoRect2 *f=&fact->footprint;bool along_v=fact->along_v;
        GeoCoord span_lo=along_v?f->min_v:f->min_u,span_hi=along_v?f->max_v:f->max_u,edge_lo,edge_hi;
        if(!wood_contact_boundary_interval(world->role_boundary,along_v,span_lo,span_hi,along_v?f->min_u:f->min_v,along_v?f->max_u:f->max_v,&edge_lo,&edge_hi))return false;
        GeoCoord fix_lo=contact_max(span_lo,edge_lo),fix_hi=contact_min(span_hi,edge_hi);
        return !(lo>=fix_lo&&hi<=fix_hi);
    }
    return false;
}
static const WoodContactMemberFact *contact_partial_owner(
    const WoodContactWorld *world,const WoodMember *self,const WoodStopFace *face,int end)
{
    if(face->kind!=WOOD_STOP_MEMBER_SIDE||face->fixity==WOOD_STOP_FREE||face->edge_index!=(end==0?1:0))return NULL;
    for(size_t i=0;i<world->member_count;++i){const WoodContactMemberFact *fact=&world->members[i];
        if(fact->member&&fact->member!=self&&fact->member->placed&&
           fact->member->id==face->timber_id&&fact->placement_id==world->placement_id&&fact->footprint_valid)
            return fact;
    }
    return NULL;
}

/* Whether some still-exposed part of [visible_lo,visible_hi] lies on an
 * unlined RC run that fits the member width. No temporary interval capacity
 * and no raw-H fallback: each covered advancement consumes a positive
 * interval from an admitted, returned FEATURE face. A run stops at the
 * nearest placed member already lining this RC plane from the member's own
 * side (its face at `at`, outside the member's own width); what remains
 * behind the end and cannot take a member is a short RC face (#318 RC run
 * rule). */
static bool contact_bare_rc_run_fits(const WoodContactWorld *world,const WoodMember *self,bool along_v,
    const WoodStopFace *faces,size_t count,GeoCoord at,int end,GeoCoord lo,GeoCoord hi,
    GeoCoord visible_lo,GeoCoord visible_hi,GeoCoord cross_lo,GeoCoord cross_hi)
{
    GeoCoord width=cross_hi-cross_lo,cursor=visible_lo;
    while(cursor<visible_hi){GeoCoord next=cursor;
        for(size_t i=0;i<count;++i){const WoodStopFace *face=&faces[i];
            if(face->fixed==at&&face->lo<=cursor&&face->hi>next&&contact_partial_owner(world,self,face,end))next=face->hi;
        }
        if(next>cursor){cursor=next;continue;}
        GeoCoord stop=visible_hi,run_lo=lo,run_hi=hi;
        for(size_t i=0;i<count;++i){const WoodStopFace *face=&faces[i];
            if(face->fixed==at&&face->lo>cursor&&face->lo<stop&&contact_partial_owner(world,self,face,end))stop=face->lo;
        }
        for(size_t i=0;i<world->member_count;++i){const WoodContactMemberFact *fact=&world->members[i];
            if(!fact->member||fact->member==self||!fact->member->placed||
               fact->placement_id!=world->placement_id||!fact->footprint_valid)continue;
            const GeoRect2 *f=&fact->footprint;
            GeoCoord near=along_v?(end==0?f->min_v:f->max_v):(end==0?f->min_u:f->max_u);
            if(near!=at)continue;
            GeoCoord a=along_v?f->min_u:f->min_v,b=along_v?f->max_u:f->max_v;
            if(a<cross_lo){GeoCoord e=contact_min(b,cross_lo);if(e<=cursor&&e>run_lo)run_lo=e;}
            if(b>cross_hi){GeoCoord s=contact_max(a,cross_hi);if(s>=stop&&s<run_hi)run_hi=s;}
        }
        if(run_hi-run_lo>=width)return true;
        cursor=stop;
    }
    return false;
}

static bool contact_same_rc_plane(const WoodStopFace *a,const WoodStopFace *b)
{
    if(a->kind==WOOD_STOP_MEMBER_SIDE||a->kind!=b->kind||a->boundary_id!=b->boundary_id||
       a->fixed!=b->fixed||a->fixity!=b->fixity||a->hole_index!=b->hole_index)return false;
    /* Outline indices encode the component; hole indices already do so.
     * Never join merely coincident planes belonging to different components. */
    return a->kind!=WOOD_STOP_OUTLINE_EDGE||
        a->edge_index/GEO_LOOP_MAX_VERTICES==b->edge_index/GEO_LOOP_MAX_VERTICES;
}

bool wood_contact_boundary_end_uses_member_facts(const WoodMember *self)
{return self&&self->role==WOOD_MEMBER_ROLE_BOUNDARY;}

WoodBoundaryEndAdmission wood_contact_boundary_end_admission(
    const WoodContactWorld *world,const WoodMember *self,bool along_v,
    GeoCoord span_lo,GeoCoord span_hi,GeoCoord cross_lo,GeoCoord cross_hi,int end,
    const WoodStopFace *faces,size_t count,const WoodStopFace *required_contact)
{
    if(!world||!self||self->role!=WOOD_MEMBER_ROLE_BOUNDARY||cross_hi<=cross_lo||
       span_hi<=span_lo||(end!=0&&end!=1)||(count&&!faces))return WOOD_BOUNDARY_END_ORDINARY;
    const WoodBoundaryRegion *boundary=world->role_boundary;
    GeoRect2 rect={along_v?cross_lo:span_lo,along_v?span_lo:cross_lo,
        along_v?cross_hi:span_hi,along_v?span_hi:cross_hi};
    if(!contact_contains(boundary,&rect))return WOOD_BOUNDARY_END_ORDINARY;
    bool on=false,covers=false;int edge=-1;
    GeoLoop2View outline={boundary->outline.v,boundary->outline.count};
    if(!wood_member_boundary_props(&outline,along_v,span_lo,span_hi,cross_lo,cross_hi,&on,&covers,&edge)||
       !on||!covers||edge<0||(size_t)edge>=outline.count||boundary->outline.fixity[edge]!=WOOD_STOP_FIXED)
        return WOOD_BOUNDARY_END_ORDINARY;
    GeoPoint2 p=outline.v[edge],q=outline.v[((size_t)edge+1)%outline.count];
    GeoCoord edge_lo=along_v?contact_min(p.v,q.v):contact_min(p.u,q.u);
    GeoCoord edge_hi=along_v?contact_max(p.v,q.v):contact_max(p.u,q.u);
    GeoCoord at=end==0?span_lo:span_hi;
    if((end==0&&at!=edge_lo)||(end==1&&at!=edge_hi))return WOOD_BOUNDARY_END_ORDINARY;
    if(required_contact){bool found=false;
        for(size_t i=0;i<count;++i)if(required_contact==&faces[i]){found=true;break;}
        if(!found||required_contact->fixed!=at||
           contact_max(cross_lo,required_contact->lo)>=contact_min(cross_hi,required_contact->hi)||
           !contact_partial_owner(world,self,required_contact,end))return WOOD_BOUNDARY_END_ORDINARY;
    }
    bool contact=false;
    for(size_t i=0;i<count;++i){const WoodStopFace *face=&faces[i];
        if(face->fixed==at&&contact_max(cross_lo,face->lo)<contact_min(cross_hi,face->hi)&&
           contact_partial_owner(world,self,face,end)){contact=true;break;}
    }
    if(!contact)return WOOD_BOUNDARY_END_ORDINARY;
    /* A normal full-face path can still admit its original complete RC
     * corner. Once partial timber contact claims this exception, an exposed
     * RC run that still fits a member is an explicit refusal, never ordinary
     * fallback. The run excludes RC already lined by placed members. */
    GeoCoord width=cross_hi-cross_lo;
    for(size_t i=0;i<count;++i){const WoodStopFace *face=&faces[i];
        if(face->kind==WOOD_STOP_MEMBER_SIDE||face->fixity==WOOD_STOP_FREE||face->fixed!=at||face->hi<=face->lo)continue;
        GeoCoord lo=face->lo,hi=face->hi;bool changed=true;
        while(changed){changed=false;
            for(size_t j=0;j<count;++j){const WoodStopFace *other=&faces[j];
                if(!contact_same_rc_plane(face,other)||other->hi<lo||other->lo>hi||other->hi<=other->lo)continue;
                GeoCoord next_lo=contact_min(lo,other->lo),next_hi=contact_max(hi,other->hi);
                if(next_lo!=lo||next_hi!=hi){lo=next_lo;hi=next_hi;changed=true;}
            }
        }
        GeoCoord visible_lo=contact_max(lo,cross_lo),visible_hi=contact_min(hi,cross_hi);
        if(hi-lo>=width&&visible_lo<visible_hi&&
           contact_bare_rc_run_fits(world,self,along_v,faces,count,at,end,lo,hi,visible_lo,visible_hi,cross_lo,cross_hi))return WOOD_BOUNDARY_END_BARE_RC;
    }
    return WOOD_BOUNDARY_END_PARTIAL;
}

bool wood_contact_end_support_check(WoodBoundaryEndAdmission admission,size_t hits,bool between,char *error,size_t cap)
{
    if(admission==WOOD_BOUNDARY_END_BARE_RC){
        if(error&&cap)snprintf(error,cap,"V_CUT_PRIORITY：固定段端點有裸露的可放料 RC 面，必須先貼角材");return false;
    }
    if(admission==WOOD_BOUNDARY_END_PARTIAL)return true;
    if(!hits||(!between&&hits!=1)){
        if(error&&cap)snprintf(error,cap,"R6(d): 端面需要恰好一個涵蓋全寬的合法擋面");return false;
    }
    return true;
}

bool wood_contact_end_faces(const WoodContactWorld *world,const WoodMember *self,bool along_v,
    GeoCoord span_lo,GeoCoord span_hi,GeoCoord cross_lo,GeoCoord cross_hi,char *error,size_t cap)
{return wood_contact_end_faces_with_sources(world,self,along_v,span_lo,span_hi,cross_lo,cross_hi,NULL,NULL,error,cap);}
bool wood_contact_end_faces_with_sources(const WoodContactWorld *world,const WoodMember *self,bool along_v,
    GeoCoord span_lo,GeoCoord span_hi,GeoCoord cross_lo,GeoCoord cross_hi,
    WoodContactStopResolver resolver,void *user,char *error,size_t cap)
{
    GeoCoord edge_lo=0,edge_hi=0;int edge_index=-1;
    bool has_edge=wood_contact_boundary_edge(world->role_boundary,along_v,span_lo,span_hi,cross_lo,cross_hi,&edge_lo,&edge_hi,&edge_index);
    if(!wood_member_span_extension_check(self,has_edge,edge_index,span_lo,span_hi,edge_lo,edge_hi,error,cap))return false;
    bool ext_end[2]={has_edge&&self->role==WOOD_MEMBER_ROLE_BOUNDARY&&span_lo<edge_lo,has_edge&&self->role==WOOD_MEMBER_ROLE_BOUNDARY&&span_hi>edge_hi};
    WoodStopFace faces[WOOD_CONTACT_FACE_CAPACITY];size_t face_count;
    if(resolver){if(!resolver(user,along_v,self,faces,WOOD_CONTACT_FACE_CAPACITY,&face_count)){
        if(error&&cap)snprintf(error,cap,"I8: ordered contact source evaluation failed");return false;
    }}
    else face_count=wood_contact_collect_stops(world,along_v,self,faces,WOOD_CONTACT_FACE_CAPACITY);
    for(int end=0;end<2;++end){GeoCoord at=end==0?span_lo:span_hi;
        WoodBoundaryEndAdmission admission=wood_contact_boundary_end_admission(world,self,along_v,
            span_lo,span_hi,cross_lo,cross_hi,end,faces,face_count,NULL);
        if(admission==WOOD_BOUNDARY_END_PARTIAL)continue;
        if(admission==WOOD_BOUNDARY_END_BARE_RC){
            if(error&&cap)snprintf(error,cap,"V_CUT_PRIORITY：角材 %u 的固定段端點有裸露的可放料 RC 面，必須先貼角材",(unsigned)self->id);
            return false;
        }
        for(size_t i=0;i<face_count;++i){const WoodStopFace *face=&faces[i];
            if(face->fixed!=at||face->lo>cross_lo||face->hi<cross_hi||face->fixity==WOOD_STOP_FREE||ext_end[end]||wood_stop_shadowed(faces,i,cross_lo,cross_hi))continue;
            const WoodMember *owner=NULL;bool extension=false;
            if(face->kind==WOOD_STOP_MEMBER_SIDE){
                for(size_t k=0;k<world->member_count;++k){const WoodMember *member=world->members[k].member;if(member->id==face->timber_id&&member->placed){owner=member;break;}}
                if(owner&&owner!=self&&!(self->role==WOOD_MEMBER_ROLE_BOUNDARY&&owner->role==WOOD_MEMBER_ROLE_BOUNDARY))extension=wood_contact_owner_extension(world,owner,cross_lo,cross_hi);
            }
            if(!wood_member_end_contact_check(self,face,owner,extension,error,cap))return false;
        }
    }
    return true;
}
