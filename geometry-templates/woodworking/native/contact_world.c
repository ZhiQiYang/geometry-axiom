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
bool wood_contact_footprint_collides(const WoodContactWorld *world,const GeoRect2 *rect,const WoodMember *exclude)
{
    if(!world||!rect)return true;
    for(size_t i=0;i<world->member_count;++i){const WoodContactMemberFact *fact=&world->members[i];
        const WoodMember *member=fact->member;
        if(!member->placed||member==exclude||fact->placement_id!=world->placement_id||!fact->footprint_valid)continue;
        if(geo_rect_overlap_positive(rect,&fact->footprint))return true;
    }
    return false;
}
static uint64_t contact_order(const WoodContactWorld *world,uint32_t id)
{
    uint64_t order=UINT64_MAX;
    for(size_t i=0;i<world->member_count;++i)if(world->members[i].member->id==id)order=world->members[i].order;
    return order;
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
    for(size_t i=1;i<count;++i){
        if(out[i].kind!=WOOD_STOP_MEMBER_SIDE)continue;
        uint64_t order=contact_order(world,out[i].timber_id);size_t j=i;WoodStopFace value=out[i];
        while(j&&out[j-1].kind==WOOD_STOP_MEMBER_SIDE){
            uint64_t previous=contact_order(world,out[j-1].timber_id);if(previous<=order)break;
            out[j]=out[j-1];--j;
        }
        out[j]=value;
    }
    for(size_t i=0;i<count;){bool duplicate=false;
        if(out[i].kind==WOOD_STOP_MEMBER_SIDE){uint64_t order=contact_order(world,out[i].timber_id);
            for(size_t j=0;j<count&&!duplicate;++j){
                if(i==j||out[i].fixed!=out[j].fixed||out[i].lo>=out[j].hi||out[j].lo>=out[i].hi)continue;
                bool earlier=out[j].kind!=WOOD_STOP_MEMBER_SIDE;
                if(!earlier)for(size_t t=0;t<world->member_count;++t)
                    if(world->members[t].member->id==out[j].timber_id&&world->members[t].order<order)earlier=true;
                if(earlier&&out[j].lo<=out[i].lo&&out[j].hi>=out[i].hi)duplicate=true;
            }
        }
        if(duplicate){memmove(out+i,out+i+1,(count-i-1)*sizeof *out);--count;}else ++i;
    }
    return count;
}
bool wood_contact_boundary_interval(const WoodBoundaryRegion *boundary,bool along_v,
    GeoCoord span_lo,GeoCoord span_hi,GeoCoord cross_lo,GeoCoord cross_hi,GeoCoord *out_lo,GeoCoord *out_hi)
{
    GeoRect2 rect={along_v?cross_lo:span_lo,along_v?span_lo:cross_lo,along_v?cross_hi:span_hi,along_v?span_hi:cross_hi};
    if(!contact_contains(boundary,&rect))return false;
    bool on_boundary=false,covers_edge=false;int edge=-1;GeoLoop2View outline={boundary->outline.v,boundary->outline.count};
    if(!wood_member_boundary_props(&outline,along_v,span_lo,span_hi,cross_lo,cross_hi,&on_boundary,&covers_edge,&edge)||!on_boundary||edge<0||(size_t)edge>=outline.count)return false;
    GeoPoint2 a=outline.v[edge],b=outline.v[((size_t)edge+1)%outline.count];
    *out_lo=along_v?contact_min(a.v,b.v):contact_min(a.u,b.u);
    *out_hi=along_v?contact_max(a.v,b.v):contact_max(a.u,b.u);return true;
}
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
bool wood_contact_end_faces(const WoodContactWorld *world,const WoodMember *self,bool along_v,
    GeoCoord span_lo,GeoCoord span_hi,GeoCoord cross_lo,GeoCoord cross_hi,char *error,size_t cap)
{return wood_contact_end_faces_with_sources(world,self,along_v,span_lo,span_hi,cross_lo,cross_hi,NULL,NULL,error,cap);}
bool wood_contact_end_faces_with_sources(const WoodContactWorld *world,const WoodMember *self,bool along_v,
    GeoCoord span_lo,GeoCoord span_hi,GeoCoord cross_lo,GeoCoord cross_hi,
    WoodContactStopResolver resolver,void *user,char *error,size_t cap)
{
    GeoCoord edge_lo=0,edge_hi=0;bool has_edge=wood_contact_boundary_interval(world->role_boundary,along_v,span_lo,span_hi,cross_lo,cross_hi,&edge_lo,&edge_hi);
    if(!wood_member_span_extension_check(self,has_edge,span_lo,span_hi,edge_lo,edge_hi,error,cap))return false;
    bool ext_end[2]={has_edge&&self->role==WOOD_MEMBER_ROLE_BOUNDARY&&span_lo<edge_lo,has_edge&&self->role==WOOD_MEMBER_ROLE_BOUNDARY&&span_hi>edge_hi};
    WoodStopFace faces[WOOD_CONTACT_FACE_CAPACITY];size_t face_count;
    if(resolver){if(!resolver(user,along_v,self,faces,WOOD_CONTACT_FACE_CAPACITY,&face_count)){
        if(error&&cap)snprintf(error,cap,"I8: ordered contact source evaluation failed");return false;
    }}
    else face_count=wood_contact_collect_stops(world,along_v,self,faces,WOOD_CONTACT_FACE_CAPACITY);
    for(int end=0;end<2;++end){GeoCoord at=end==0?span_lo:span_hi;
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
