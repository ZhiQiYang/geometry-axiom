#include "regions.h"
#include <stdio.h>
#include <string.h>

#define CHECK(test) do { if (!(test)) { fprintf(stderr,"%d: %s\n",__LINE__,#test); return 1; } } while (0)

static GeoRegionDefinition rectangle(uint32_t id)
{
    GeoRegionDefinition region;
    memset(&region,0,sizeof region);region.id=id;region.outline.count=4;
    region.outline.v[0]=(GeoPoint2){0,0};region.outline.v[1]=(GeoPoint2){100,0};
    region.outline.v[2]=(GeoPoint2){100,100};region.outline.v[3]=(GeoPoint2){0,100};
    return region;
}
static GeoRegionDefinition holed(uint32_t id)
{
    GeoRegionDefinition region=rectangle(id);region.hole_count=2;
    region.holes[0].count=region.holes[1].count=4;
    const GeoPoint2 first[]={{10,10},{20,10},{20,20},{10,20}};
    const GeoPoint2 second[]={{70,70},{80,70},{80,80},{70,80}};
    memcpy(region.holes[0].v,first,sizeof first);memcpy(region.holes[1].v,second,sizeof second);
    return region;
}
static GeoRegionKeys sequential(const GeoRegionDefinition *region)
{
    GeoRegionKeys keys;
    memset(&keys,0,sizeof keys);keys.boundary_id=region->id;keys.loop_count=region->hole_count+1;keys.next_key=1;
    for(size_t l=0;l<keys.loop_count;++l){
        keys.counts[l]=l?region->holes[l-1].count:region->outline.count;
        for(size_t i=0;i<keys.counts[l];++i)keys.keys[l][i]=keys.next_key++;
    }
    return keys;
}
static void insert_vertex(GeoRegionLoop *loop,size_t index,GeoPoint2 point)
{
    memmove(loop->v+index+1,loop->v+index,(loop->count-index)*sizeof loop->v[0]);
    loop->v[index]=point;++loop->count;
}

static int ownership(void)
{
    GeoRegionStore *store=geo_regions_create();CHECK(store);
    GeoRegionDefinition expected=rectangle(0),input;
    memset(&input,0x5a,sizeof input);input.id=0;input.hole_count=0;input.outline.count=4;
    memcpy(input.outline.v,expected.outline.v,4*sizeof input.outline.v[0]);
    CHECK(geo_regions_put(store,&input));CHECK(geo_region_keys_count(store)==0);
    CHECK(!memcmp(geo_regions_find(store,0),&expected,sizeof expected));
    input.outline.v[0].u=77;CHECK(geo_regions_find(store,0)->outline.v[0].u==0);
    CHECK(geo_regions_put(store,geo_regions_at(store,0)));
    CHECK(!memcmp(geo_regions_at(store,0),&expected,sizeof expected));
    GeoRegionKeys expected_keys=sequential(&expected),input_keys;
    memset(&input_keys,0x5a,sizeof input_keys);input_keys.boundary_id=0;input_keys.loop_count=1;
    input_keys.counts[0]=4;input_keys.next_key=5;
    memcpy(input_keys.keys[0],expected_keys.keys[0],4*sizeof(uint32_t));
    CHECK(geo_region_keys_put(store,&input_keys));
    CHECK(!memcmp(geo_region_keys_at(store,0),&expected_keys,sizeof expected_keys));
    input_keys.keys[0][0]=99;CHECK(geo_region_keys_find(store,0)->keys[0][0]==1);
    CHECK(geo_region_keys_put(store,geo_region_keys_at(store,0)));
    CHECK(!memcmp(geo_region_keys_at(store,0),&expected_keys,sizeof expected_keys));
    GeoRegionStore *copy=geo_regions_clone(store);CHECK(copy);
    CHECK(geo_regions_at(copy,0)!=geo_regions_at(store,0));
    CHECK(geo_region_keys_at(copy,0)!=geo_region_keys_at(store,0));
    GeoRegionDefinition replacement=rectangle(0);replacement.outline.v[1].u=replacement.outline.v[2].u=200;
    CHECK(geo_regions_put(copy,&replacement));CHECK(geo_regions_at(store,0)->outline.v[1].u==100);
    CHECK(geo_region_keys_remove(copy,0));CHECK(geo_region_keys_count(store)==1);
    CHECK(geo_regions_remove(store,0));CHECK(geo_region_keys_count(store)==1);
    CHECK(geo_region_keys_remove(store,0));CHECK(!geo_regions_remove(store,0));
    CHECK(!geo_regions_clone(NULL));
    geo_regions_destroy(store);geo_regions_destroy(copy);return 0;
}

static int capacity(void)
{
    GeoRegionStore *store=geo_regions_create();CHECK(store);CHECK(GEO_REGION_CAPACITY==16);
    for(uint32_t id=0;id<16;++id){GeoRegionDefinition region=rectangle(id);
        CHECK(geo_regions_put(store,&region));CHECK(geo_region_keys_initialize(store,&region));}
    GeoRegionDefinition extra=rectangle(UINT32_MAX);GeoRegionKeys keys=sequential(&extra);
    CHECK(!geo_regions_put(store,&extra));CHECK(!geo_region_keys_put(store,&keys));
    CHECK(!geo_region_keys_initialize(store,&extra));
    CHECK(geo_regions_count(store)==16&&geo_region_keys_count(store)==16);
    CHECK(geo_regions_put(store,geo_regions_find(store,7)));
    CHECK(geo_region_keys_put(store,geo_region_keys_find(store,7)));
    CHECK(geo_regions_remove(store,7)&&geo_region_keys_remove(store,7));
    CHECK(geo_regions_at(store,7)->id==8&&geo_region_keys_at(store,7)->boundary_id==8);
    CHECK(geo_regions_put(store,&extra)&&geo_region_keys_put(store,&keys));
    CHECK(geo_regions_at(store,15)->id==UINT32_MAX&&geo_region_keys_at(store,15)->boundary_id==UINT32_MAX);
    CHECK(!geo_regions_at(store,16)&&!geo_region_keys_at(store,16));
    CHECK(!geo_regions_find(store,7)&&!geo_region_keys_find(store,7));
    CHECK(!geo_region_keys_remove(store,7));
    geo_regions_destroy(store);return 0;
}

static int geometry(void)
{
    GeoRegionStore *store=geo_regions_create();CHECK(store);
    GeoRegionDefinition region=holed(9);insert_vertex(&region.outline,1,(GeoPoint2){50,0});
    insert_vertex(&region.holes[0],1,(GeoPoint2){15,10});
    CHECK(geo_regions_put(store,&region));
    CHECK(geo_regions_at(store,0)->outline.count==5&&geo_regions_at(store,0)->holes[0].count==5);
    CHECK(geo_regions_at(store,0)->outline.v[1].u==50&&geo_regions_at(store,0)->holes[0].v[1].u==15);
    GeoRegionDefinition before=*geo_regions_at(store,0),bad=region;
    bad.outline.v[0].u=7;CHECK(!geo_regions_put(store,&bad));
    CHECK(!memcmp(geo_regions_at(store,0),&before,sizeof before));
    bad=region;bad.holes[0].v[0]=(GeoPoint2){-10,-10};CHECK(!geo_regions_put(store,&bad));
    bad=region;bad.hole_count=GEO_REGION_MAX_HOLES+1;CHECK(!geo_regions_put(store,&bad));
    bad=region;bad.outline.count=GEO_LOOP_MAX_VERTICES+1;CHECK(!geo_regions_put(store,&bad));
    CHECK(!geo_regions_put(store,NULL));
    geo_regions_destroy(store);return 0;
}

static int initialization(void)
{
    GeoRegionStore *store=geo_regions_create();CHECK(store);GeoRegionDefinition region=holed(42);
    CHECK(geo_region_keys_initialize(store,&region));
    CHECK(geo_regions_count(store)==0&&geo_region_keys_count(store)==1);
    const GeoRegionKeys *keys=geo_region_keys_find(store,42);CHECK(keys&&keys->loop_count==3&&keys->next_key==13);
    for(size_t l=0;l<3;++l)for(size_t i=0;i<4;++i)CHECK(keys->keys[l][i]==1+l*4+i);
    GeoRegionKeys high=*keys;high.next_key=1000;CHECK(geo_region_keys_put(store,&high));
    CHECK(geo_region_keys_initialize(store,&region));CHECK(geo_region_keys_find(store,42)->next_key==1000);
    GeoRegionDefinition changed=region;changed.outline.count=5;
    CHECK(!geo_region_keys_initialize(store,&changed));CHECK(geo_region_keys_count(store)==1);
    GeoRegionKeys invalid=high;invalid.keys[1][0]=invalid.keys[0][0];
    CHECK(!geo_region_keys_valid(&region,&invalid)&&!geo_region_keys_put(store,&invalid));
    invalid=high;invalid.keys[0][0]=0;CHECK(!geo_region_keys_put(store,&invalid));
    invalid=high;invalid.next_key=12;CHECK(!geo_region_keys_put(store,&invalid));
    invalid=high;invalid.loop_count=GEO_REGION_MAX_HOLES+2;CHECK(!geo_region_keys_put(store,&invalid));
    invalid=high;invalid.counts[0]=GEO_LOOP_MAX_VERTICES+1;CHECK(!geo_region_keys_put(store,&invalid));
    CHECK(geo_region_keys_same(geo_region_keys_find(store,42),&high));
    geo_regions_destroy(store);return 0;
}

static int ordinary(void)
{
    GeoRegionDefinition before=holed(42),current=before;GeoRegionKeys old=sequential(&before),keys=old;
    for(size_t i=0;i<4;++i)current.outline.v[i]=before.outline.v[(i+2)%4];
    current.holes[0]=before.holes[1];current.holes[1]=before.holes[0];
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,false)==GEO_REGION_KEYS_OK);
    const uint32_t outer[]={3,4,1,2};
    for(size_t i=0;i<4;++i){CHECK(keys.keys[0][i]==outer[i]);CHECK(keys.keys[1][i]==9+i);CHECK(keys.keys[2][i]==5+i);}
    CHECK(keys.next_key==13);
    current=before;insert_vertex(&current.outline,1,(GeoPoint2){50,0});
    insert_vertex(&current.holes[0],1,(GeoPoint2){15,10});
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,false)==GEO_REGION_KEYS_OK);
    const uint32_t expected_outer[]={1,13,2,3,4},expected_hole[]={5,14,6,7,8};
    for(size_t i=0;i<5;++i){CHECK(keys.keys[0][i]==expected_outer[i]);CHECK(keys.keys[1][i]==expected_hole[i]);}
    CHECK(keys.next_key==15);GeoRegionKeys first=keys;
    keys.next_key=UINT32_MAX;
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,false)==GEO_REGION_KEYS_OK);
    CHECK(!memcmp(&keys,&first,sizeof keys));
    CHECK(old.next_key==13&&old.counts[0]==4);
    return 0;
}

static int invalid_mapping(void)
{
    GeoRegionDefinition before=rectangle(8),current=before;GeoRegionKeys old=sequential(&before),keys=old;
    current.outline.v[0]=(GeoPoint2){0,1};
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,false)==GEO_REGION_KEYS_IDENTITY_CHANGED);
    CHECK(!memcmp(&keys,&old,sizeof keys));
    current=before;current.outline.count=3;
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,false)==GEO_REGION_KEYS_IDENTITY_CHANGED);
    current=before;insert_vertex(&current.outline,1,before.outline.v[0]);
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,false)==GEO_REGION_KEYS_IDENTITY_CHANGED);
    current=before;current.hole_count=GEO_REGION_MAX_HOLES+1;
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,false)==GEO_REGION_KEYS_TOO_MANY_LOOPS);
    current=before;current.outline.count=GEO_LOOP_MAX_VERTICES+1;
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,false)==GEO_REGION_KEYS_TOO_MANY_VERTICES);
    GeoRegionKeys invalid_old=old;invalid_old.keys[0][1]=1;
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&invalid_old,false)==GEO_REGION_KEYS_PREVIOUS_INVALID);
    current=before;keys.keys[0][0]=0;
    CHECK(geo_region_keys_reconcile(&current,&keys,NULL,NULL,false)==GEO_REGION_KEYS_INVALID);
    CHECK(geo_region_keys_reconcile(NULL,&keys,&before,&old,false)==GEO_REGION_KEYS_INVALID);
    CHECK(geo_region_keys_reconcile(&current,NULL,&before,&old,false)==GEO_REGION_KEYS_INVALID);
    /* Two distinct old identities at one coordinate are never merged. The
     * host normally rejects that geometry; this unit still keeps identity. */
    before.outline.v[2]=before.outline.v[0];keys=old;
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,false)==GEO_REGION_KEYS_IDENTITY_CHANGED);
    return 0;
}

static int keyed(void)
{
    GeoRegionDefinition before=rectangle(8),current=before;GeoRegionKeys old=sequential(&before),keys;
    old.next_key=9;keys=old;
    current.outline.v[1].u=current.outline.v[2].u=120;
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,true)==GEO_REGION_KEYS_OK);
    CHECK(geo_region_keys_same(&keys,&old));
    keys.keys[0][3]=6;
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,true)==GEO_REGION_KEYS_RETIRED_KEY);
    keys=old;keys.keys[0][3]=9;keys.next_key=10;
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,true)==GEO_REGION_KEYS_OK);
    CHECK(!geo_region_keys_has(&keys,4)&&geo_region_keys_has(&keys,9));
    keys=old;keys.next_key=8;
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,true)==GEO_REGION_KEYS_HIGHWATER_BACKWARDS);
    keys=old;keys.next_key=0;
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,true)==GEO_REGION_KEYS_OK);
    old.next_key=0;keys=old;keys.next_key=9;
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,true)==GEO_REGION_KEYS_HIGHWATER_BACKWARDS);
    keys=old;keys.keys[0][3]=9;
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,true)==GEO_REGION_KEYS_RETIRED_KEY);
    return 0;
}

static int exhaustion(void)
{
    GeoRegionDefinition before=rectangle(8),current=before;GeoRegionKeys old=sequential(&before),keys;
    old.next_key=UINT32_MAX;keys=old;insert_vertex(&current.outline,1,(GeoPoint2){50,0});
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,false)==GEO_REGION_KEYS_OK);
    CHECK(keys.keys[0][1]==UINT32_MAX&&keys.next_key==0&&geo_region_keys_valid(&current,&keys));
    CHECK(old.next_key==UINT32_MAX);
    keys=old;insert_vertex(&current.outline,1,(GeoPoint2){25,0});
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,false)==GEO_REGION_KEYS_EXHAUSTED);
    CHECK(!memcmp(&keys,&old,sizeof keys));
    old.next_key=0;keys=old;
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,false)==GEO_REGION_KEYS_EXHAUSTED);
    current=before;
    CHECK(geo_region_keys_reconcile(&current,&keys,&before,&old,false)==GEO_REGION_KEYS_OK&&keys.next_key==0);
    return 0;
}

static int lookup(void)
{
    GeoRegionDefinition region=holed(5);GeoRegionKeys keys=sequential(&region);GeoPoint2 output={123,456};
    CHECK(geo_region_vertex_by_key(&region,&keys,10,&output));CHECK(output.u==80&&output.v==70);
    CHECK(geo_region_vertex_by_key(&region,&keys,1,NULL));
    output=(GeoPoint2){123,456};CHECK(!geo_region_vertex_by_key(&region,&keys,0,&output));
    CHECK(!geo_region_vertex_by_key(&region,&keys,13,&output));CHECK(output.u==123&&output.v==456);
    CHECK(geo_region_keys_has(&keys,12)&&!geo_region_keys_has(&keys,0)&&!geo_region_keys_has(NULL,1));
    keys.keys[1][0]=1;CHECK(!geo_region_vertex_by_key(&region,&keys,1,&output));
    CHECK(output.u==123&&output.v==456);return 0;
}

int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"ownership"))return ownership();
    if(!strcmp(argv[1],"capacity"))return capacity();
    if(!strcmp(argv[1],"geometry"))return geometry();
    if(!strcmp(argv[1],"initialization"))return initialization();
    if(!strcmp(argv[1],"ordinary"))return ordinary();
    if(!strcmp(argv[1],"invalid-mapping"))return invalid_mapping();
    if(!strcmp(argv[1],"keyed"))return keyed();
    if(!strcmp(argv[1],"exhaustion"))return exhaustion();
    if(!strcmp(argv[1],"lookup"))return lookup();
    return 2;
}
