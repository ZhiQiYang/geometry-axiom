/* Exercise the real private index with an independent full linear oracle.
 * GEO_TEST_CACHED selects the historical function signature, not its oracle. */
#include "contact-plane-subject.c"
#include <inttypes.h>
#include <stdlib.h>
#define CHECK(tag,x) do{if(!(x)){fprintf(stderr,"ASSERT:%s\n",tag);return 1;}}while(0)
static bool same_face(const WoodStopFace *a,const WoodStopFace *b)
{return a->kind==b->kind&&a->boundary_id==b->boundary_id&&a->timber_id==b->timber_id&&a->hole_index==b->hole_index&&a->edge_index==b->edge_index&&a->fixity==b->fixity&&a->fixed==b->fixed&&a->lo==b->lo&&a->hi==b->hi;}
static void bounds(const ContactFaceIndex *index,const WoodStopFace *out,size_t n,size_t i,size_t *b,size_t *e)
{
#if GEO_TEST_CACHED
    (void)out;(void)n;contact_face_index_bounds(index,i,b,e);
#else
    contact_face_plane_range(index,out,n,out[i].fixed,b,e);
#endif
}
static bool covered(const ContactFaceIndex *index,const WoodStopFace *out,size_t n,size_t i)
{
#if GEO_TEST_CACHED
    return contact_face_index_covered(index,out,n,i);
#else
    return contact_face_index_covered(index,out,n,&out[i]);
#endif
}
static bool linear_cover(const WoodStopFace *out,const bool *admitted,size_t n,size_t q)
{
    for(size_t j=0;j<n;++j)if(admitted[j]&&out[j].fixed==out[q].fixed&&
        out[j].lo<=out[q].lo&&out[j].lo<out[q].hi&&
        out[j].hi>=out[q].hi&&out[j].hi>out[q].lo)return true;
    return false;
}
static int run_case(const char *name)
{
    bool work=!strcmp(name,"work"),full=!strcmp(name,"full-capacity");
    size_t n=full?WOOD_CONTACT_FACE_CAPACITY:16;
    if(!strcmp(name,"empty"))n=0;
    else if(!strcmp(name,"singleton"))n=1;
    else if(!strcmp(name,"bounds")||!strcmp(name,"coverage")||work||full){}
    else return 2;
    /* Metadata at the face capacity does not assert that the host admits that
     * many members. Heap storage also keeps test stack usage bounded. */
    ContactFaceIndex *index=calloc(1,sizeof *index);
    WoodStopFace *out=calloc(n+1,sizeof *out),*original=calloc(n+1,sizeof *original);
    bool *admitted=calloc(n+1,sizeof *admitted);
    CHECK("plane-test-allocation",index&&out&&original&&admitted);
    const GeoCoord planes[16]={0,INT64_MIN,INT64_MAX,0,INT64_C(4294967296),
        INT64_MIN,INT64_MIN+INT64_C(4294967296),INT64_MAX,0,-7,INT64_C(4294967296),
        -7,INT64_MIN,INT64_MAX,0,INT64_MIN+INT64_C(4294967296)};
    const GeoCoord los[8]={-10,0,5,10,20,10,-20,-10};
    const GeoCoord his[8]={30,0,4,20,10,10,40,30};
    for(size_t i=0;i<n;++i){
        out[i]=(WoodStopFace){i%3==0?WOOD_STOP_OUTLINE_EDGE:i%3==1?WOOD_STOP_HOLE_EDGE:WOOD_STOP_MEMBER_SIDE,
            (uint32_t)(i+1),(uint32_t)(i+7),(int)(i%4)-1,(int)(i%2),
            i%2?WOOD_STOP_FREE:WOOD_STOP_FIXED,planes[i%16],los[i%8],his[i%8]};
    }
    out[n]=(WoodStopFace){WOOD_STOP_MEMBER_SIDE,991,992,-1,99,WOOD_STOP_FREE,7,8,9};
    memcpy(original,out,(n+1)*sizeof *out);
    contact_face_index_build(index,out,n);
    for(size_t i=0;i<n;++i){
        size_t b,e,linear_b=0,linear_e=0;
        for(size_t j=0;j<n;++j){linear_b+=out[j].fixed<out[i].fixed;linear_e+=out[j].fixed<=out[i].fixed;}
        bounds(index,out,n,i,&b,&e);
        CHECK("plane-linear-range-oracle",b==linear_b&&e==linear_e);
        CHECK("plane-rank-permutation",index->rank[i]<n&&index->sorted[index->rank[i]]==i);
        CHECK("plane-initial-admission-empty",!covered(index,out,n,i));
    }
    geo_test_plane_comparisons=0;
    /* Reverse admission visits first/middle/last ranks of every nonadjacent
     * group. Every fourth face stays inactive, but remains in group bounds. */
    for(size_t remaining=n;remaining;--remaining){size_t i=remaining-1;
        if(i%4!=1){contact_face_index_insert(index,out,n,i);admitted[i]=true;}
        if(!work&&(!full||remaining==1))for(size_t q=0;q<n;++q)
            CHECK("plane-linear-coverage-oracle",covered(index,out,n,q)==linear_cover(out,admitted,n,q));
    }
    size_t calls=geo_test_plane_comparisons;
    for(size_t i=0;i<=n;++i)CHECK("plane-source-fields-and-tail-preserved",same_face(out+i,original+i));
    printf("CASE %s faces=%zu plane_comparisons=%zu\n",name,n,calls);
    free(admitted);free(original);free(out);free(index);
    if(work)CHECK("plane-cached-query-no-plane-search",calls==0);
    return 0;
}
int main(int argc,char **argv){return argc==2?run_case(argv[1]):2;}
