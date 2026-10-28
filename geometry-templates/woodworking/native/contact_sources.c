#include "contact_sources.h"
#include <limits.h>
#include <stdlib.h>
#include <string.h>

enum { WOOD_CONTACT_SOURCE_METADATA_SIZE=24,WOOD_CONTACT_SOURCE_RECORD_SIZE=48 };
static const char wood_contact_collection_schema[]="wood.contact.stops/1";
typedef struct WoodContactQuery {
    uint64_t id;
    WoodContactSourceRequest request;
    size_t cap;
    unsigned char *collection;
    size_t collection_size;
    size_t collection_node_hint;
    struct WoodContactQuery *next;
} WoodContactQuery;
/* 單筆純計算提示；collection 借用仍由 query 清單持有的不可變位元組。
 * facts 中的 member 是借用指標，必須另存 collector 會解參照的 id/placed。 */
typedef struct {
    WoodContactSourceFacts facts;
    uint32_t member_id[WOOD_CONTACT_MEMBER_CAPACITY];
    bool member_placed[WOOD_CONTACT_MEMBER_CAPACITY];
    WoodContactSourceRequest request;
    size_t cap,count,collection_size;
    const unsigned char *collection;
} WoodContactResultMemo;
struct WoodContactSources {
    GeoEvalContext *graph;
    GeoProviderToken token;
    WoodContactSourceFactsCallback facts;
    void *user;
    uint64_t sequence;
    WoodContactQuery *queries;
    WoodContactResultMemo *result_memo;
};

static void wood_contact_source_u32(unsigned char *out,uint32_t value)
{for(unsigned i=0;i<4;++i)out[i]=(unsigned char)(value>>(24-8*i));}
static void wood_contact_source_u64(unsigned char *out,uint64_t value)
{for(unsigned i=0;i<8;++i)out[i]=(unsigned char)(value>>(56-8*i));}
static uint32_t wood_contact_source_read_u32(const unsigned char *bytes)
{uint32_t value=0;for(unsigned i=0;i<4;++i)value=(value<<8)|bytes[i];return value;}
static uint64_t wood_contact_source_read_u64(const unsigned char *bytes)
{uint64_t value=0;for(unsigned i=0;i<8;++i)value=(value<<8)|bytes[i];return value;}
static GeoCoord wood_contact_source_read_coord(const unsigned char *bytes)
{
    uint64_t value=wood_contact_source_read_u64(bytes);
    return value<=INT64_MAX?(GeoCoord)value:-1-(GeoCoord)(UINT64_MAX-value);
}
static bool wood_contact_source_read_int(const unsigned char *bytes,int *out)
{
    uint32_t value=wood_contact_source_read_u32(bytes);
    int64_t signed_value=value<=INT32_MAX?(int64_t)value:(int64_t)value-INT64_C(4294967296);
    if(signed_value<INT_MIN||signed_value>INT_MAX)return false;*out=(int)signed_value;return true;
}
GeoSourceRef wood_contact_source_ref(GeoProviderToken token,WoodContactSourceKind kind,uint64_t query_id,
    uint64_t feature_index,WoodContactSourceKey *key)
{
    key->bytes[0]=(unsigned char)kind;wood_contact_source_u64(key->bytes+1,query_id);
    wood_contact_source_u64(key->bytes+9,feature_index);return (GeoSourceRef){token,key->bytes,sizeof key->bytes};
}
bool wood_contact_source_decode(const GeoSourceRef *ref,WoodContactSourceKind *kind,uint64_t *query,uint64_t *index)
{
    if(!ref||!ref->key||ref->key_size!=17||!kind||!query||!index)return false;
    const unsigned char *bytes=ref->key;
    if(bytes[0]<WOOD_CONTACT_SOURCE_COLLECTION||bytes[0]>WOOD_CONTACT_SOURCE_FEATURE)return false;
    uint64_t q=wood_contact_source_read_u64(bytes+1),i=wood_contact_source_read_u64(bytes+9);
    if(!q||(bytes[0]==WOOD_CONTACT_SOURCE_COLLECTION&&i))return false;
    *kind=(WoodContactSourceKind)bytes[0];*query=q;*index=i;return true;
}
static WoodContactQuery *wood_contact_source_query(const WoodContactSources *s,uint64_t id)
{for(WoodContactQuery *q=s->queries;q;q=q->next)if(q->id==id)return q;return NULL;}
static bool wood_contact_source_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    WoodContactSources *s=user;WoodContactSourceKind kind;uint64_t id,index;
    if(ref->provider!=s->token||!wood_contact_source_decode(ref,&kind,&id,&index))return false;
    WoodContactQuery *q=wood_contact_source_query(s,id);
    if(!q||(kind==WOOD_CONTACT_SOURCE_FEATURE&&index>=q->cap))return false;
    GeoSourceDescriptor d={0};d.kind=kind==WOOD_CONTACT_SOURCE_COLLECTION?GEO_SOURCE_DEFINITION:GEO_SOURCE_FEATURE;
    d.unit=kind==WOOD_CONTACT_SOURCE_COLLECTION?GEO_UNIT_SCALAR:GEO_UNIT_LENGTH;
    d.context=(GeoSourceContext){true,q->request.placement_id,-1};*out=d;return true;
}
static bool wood_contact_source_facts_valid(const WoodContactSourceFacts *facts)
{
    if(facts->region_count>WOOD_CONTACT_COMPONENT_CAPACITY||facts->member_count>WOOD_CONTACT_MEMBER_CAPACITY)return false;
    for(size_t c=0;c<facts->region_count;++c){const WoodBoundaryRegion *region=&facts->regions[c];
        if(region->outline.count>GEO_LOOP_MAX_VERTICES||region->hole_count>GEO_REGION_MAX_HOLES)return false;
        for(size_t h=0;h<region->hole_count;++h)if(region->holes[h].count>GEO_LOOP_MAX_VERTICES)return false;
    }
    for(size_t i=0;i<facts->member_count;++i)if(!facts->members[i].member)return false;
    return true;
}
static void wood_contact_source_encode_face(unsigned char *bytes,const WoodStopFace *face)
{
    wood_contact_source_u32(bytes,(uint32_t)face->kind);wood_contact_source_u32(bytes+4,face->boundary_id);
    wood_contact_source_u32(bytes+8,face->timber_id);wood_contact_source_u32(bytes+12,(uint32_t)face->hole_index);
    wood_contact_source_u32(bytes+16,(uint32_t)face->edge_index);wood_contact_source_u32(bytes+20,(uint32_t)face->fixity);
    wood_contact_source_u64(bytes+24,(uint64_t)face->fixed);wood_contact_source_u64(bytes+32,(uint64_t)face->lo);
    wood_contact_source_u64(bytes+40,(uint64_t)face->hi);
}
static bool wood_contact_result_matches(const WoodContactResultMemo *memo,
    const WoodContactQuery *q,const WoodContactSourceFacts *facts)
{
    if(!memo||!memo->collection||memo->count>q->cap||
       memo->collection_size!=8+memo->count*WOOD_CONTACT_SOURCE_RECORD_SIZE||
       memo->request.placement_id!=q->request.placement_id||
       memo->request.along_v!=q->request.along_v||memo->request.exclude!=q->request.exclude||
       memo->cap!=q->cap||memcmp(&memo->facts,facts,sizeof *facts))return false;
    /* 全 facts bytes 不同就重算；padding 差異也只會讓提示失效。
     * 指標相同不代表原 member 的可觀察欄位未變。 */
    for(size_t i=0;i<facts->member_count;++i)
        if(memo->member_id[i]!=facts->members[i].member->id||
           memo->member_placed[i]!=facts->members[i].member->placed)return false;
    return true;
}
static void wood_contact_result_remember(WoodContactSources *s,const WoodContactQuery *q,
    const WoodContactSourceFacts *facts,size_t count)
{
    WoodContactResultMemo *memo=s->result_memo;
    if(!memo){memo=malloc(sizeof *memo);if(!memo)return;}
    memcpy(&memo->facts,facts,sizeof *facts);
    for(size_t i=0;i<facts->member_count;++i){
        memo->member_id[i]=facts->members[i].member->id;
        memo->member_placed[i]=facts->members[i].member->placed;
    }
    memo->request=q->request;memo->cap=q->cap;memo->count=count;
    memo->collection=q->collection;memo->collection_size=q->collection_size;
    s->result_memo=memo;
}
static bool wood_contact_source_collection(WoodContactSources *s,WoodContactQuery *q,GeoSourceValue *out)
{
    if(!q->collection){
        WoodContactSourceFacts *facts=calloc(1,sizeof *facts);
        WoodStopFace *faces=q->cap?malloc(q->cap*sizeof *faces):NULL;
        if(!facts||(q->cap&&!faces)){free(facts);free(faces);return false;}
        if(!s->facts(s->user,s->graph,&q->request,facts)||!wood_contact_source_facts_valid(facts)){
            free(facts);free(faces);return false;
        }
        /* 原必要配置、callback 及驗證全部先完成；每個新 consumer 的
         * 來源依賴、失敗與副作用不因命中純 collector 結果而省略。 */
        bool reused=wood_contact_result_matches(s->result_memo,q,facts);
        size_t collected;
        if(reused)collected=s->result_memo->count;
        else{
            WoodContactWorld world={0};world.placement_id=q->request.placement_id;
            world.region_count=facts->region_count;world.members=facts->members;world.member_count=facts->member_count;
            for(size_t c=0;c<facts->region_count;++c)world.regions[c]=&facts->regions[c];
            size_t count=wood_contact_collect_stops(&world,q->request.along_v,q->request.exclude,faces,q->cap);
            collected=count;
        }
        size_t count=collected;
        size_t size=8+count*WOOD_CONTACT_SOURCE_RECORD_SIZE;
        unsigned char *bytes=malloc(size);if(!bytes){free(facts);free(faces);return false;}
        if(reused)memcpy(bytes,s->result_memo->collection,size);
        else{
            wood_contact_source_u64(bytes,(uint64_t)count);
            for(size_t i=0;i<count;++i)wood_contact_source_encode_face(bytes+8+i*WOOD_CONTACT_SOURCE_RECORD_SIZE,&faces[i]);
        }
        q->collection=bytes;q->collection_size=size;
        /* 命中仍給新 query 自有 deep copy。提示配置失敗僅停用提示，
         * 不新增 query 錯誤，也不更新先前 query 的 borrowed value。 */
        if(!reused)wood_contact_result_remember(s,q,facts,count);
        free(facts);free(faces);
    }
    out->kind=GEO_SOURCE_DEFINITION;
    out->as.definition=(GeoDefinitionValue){wood_contact_collection_schema,q->collection,q->collection_size};return true;
}
static bool wood_contact_source_collection_view(const GeoSourceValue *value,size_t cap,const unsigned char **bytes,size_t *count)
{
    if(value->kind!=GEO_SOURCE_DEFINITION||!value->as.definition.schema||
       strcmp(value->as.definition.schema,wood_contact_collection_schema)||!value->as.definition.content||value->as.definition.content_size<8)return false;
    const unsigned char *content=value->as.definition.content;uint64_t n=wood_contact_source_read_u64(content);
    if(n>cap||n>WOOD_CONTACT_FACE_CAPACITY||value->as.definition.content_size!=8+(size_t)n*WOOD_CONTACT_SOURCE_RECORD_SIZE)return false;
    *bytes=content;*count=(size_t)n;return true;
}
static bool wood_contact_source_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    WoodContactSources *s=user;WoodContactSourceKind kind;uint64_t id,index;
    if(graph!=s->graph||ref->provider!=s->token||!wood_contact_source_decode(ref,&kind,&id,&index))return false;
    WoodContactQuery *q=wood_contact_source_query(s,id);if(!q)return false;
    if(kind==WOOD_CONTACT_SOURCE_COLLECTION)return wood_contact_source_collection(s,q,out);
    WoodContactSourceKey key;GeoSourceValue collection;
    GeoSourceRef collection_ref=wood_contact_source_ref(s->token,WOOD_CONTACT_SOURCE_COLLECTION,id,0,&key);
    GeoSourceNodeView node;
    if(q->collection&&geo_eval_node_at(graph,q->collection_node_hint,&node)&&
        node.source.provider==collection_ref.provider&&node.source.key_size==collection_ref.key_size&&
        !memcmp(node.source.key,collection_ref.key,collection_ref.key_size)&&node.state==GEO_NODE_VALID&&node.value){
        /* 成功的集合由本查詢持有且不再變動。每個 feature 使用其位元組前，
         * 仍依原順序記錄自己的依賴；失敗或尚未求值的集合走原路徑。 */
        if(geo_eval_depend(graph,collection_ref,GEO_DEPENDENCY_VALUE_REQUIRED)!=GEO_SOURCE_OK)return false;
        collection=*node.value;
    }else if(geo_eval_source(graph,collection_ref,GEO_DEPENDENCY_VALUE_REQUIRED,&collection)!=GEO_SOURCE_OK)return false;
    const unsigned char *bytes;size_t count;
    if(!wood_contact_source_collection_view(&collection,q->cap,&bytes,&count)||index>=count)return false;
    const unsigned char *record=bytes+8+(size_t)index*WOOD_CONTACT_SOURCE_RECORD_SIZE;
    GeoCoord fixed=wood_contact_source_read_coord(record+24),lo=wood_contact_source_read_coord(record+32),hi=wood_contact_source_read_coord(record+40);
    GeoSegment3 segment=q->request.along_v?(GeoSegment3){{lo,fixed,0},{hi,fixed,0}}:(GeoSegment3){{fixed,lo,0},{fixed,hi,0}};
    out->kind=GEO_SOURCE_FEATURE;out->as.feature=(GeoFeatureValue){record,WOOD_CONTACT_SOURCE_METADATA_SIZE,segment};return true;
}
static bool wood_contact_source_face(const GeoSourceValue *value,bool along_v,WoodStopFace *out)
{
    if(value->kind!=GEO_SOURCE_FEATURE||!value->as.feature.key||value->as.feature.key_size!=WOOD_CONTACT_SOURCE_METADATA_SIZE)return false;
    const unsigned char *metadata=value->as.feature.key;WoodStopFace face={0};
    if(!wood_contact_source_read_int(metadata,&face.kind)||!wood_contact_source_read_int(metadata+12,&face.hole_index)||
       !wood_contact_source_read_int(metadata+16,&face.edge_index)||!wood_contact_source_read_int(metadata+20,&face.fixity))return false;
    face.boundary_id=wood_contact_source_read_u32(metadata+4);face.timber_id=wood_contact_source_read_u32(metadata+8);
    const GeoSegment3 *segment=&value->as.feature.segment;
    if(segment->start.z||segment->end.z||(along_v?segment->start.y!=segment->end.y:segment->start.x!=segment->end.x))return false;
    face.fixed=along_v?segment->start.y:segment->start.x;
    face.lo=along_v?segment->start.x:segment->start.y;
    face.hi=along_v?segment->end.x:segment->end.y;
    *out=face;return true;
}
WoodContactSources *wood_contact_sources_create(GeoEvalContext *graph,GeoProviderToken token,
    WoodContactSourceFactsCallback facts,void *user)
{
    if(!graph||!token||!facts)return NULL;
    WoodContactSources *s=calloc(1,sizeof *s);if(!s)return NULL;
    s->graph=graph;s->token=token;s->facts=facts;s->user=user;
    GeoSourceProvider provider={token,"wood.contact","wood-contact-sources/1",s,wood_contact_source_describe,wood_contact_source_evaluate};
    if(!geo_eval_register(graph,&provider)){free(s);return NULL;}return s;
}
bool wood_contact_sources_collect(WoodContactSources *s,const WoodContactSourceRequest *request,
    WoodStopFace *out,size_t cap,size_t *count)
{
    if(!s||!request||!count||(cap&&!out)||geo_eval_is_sealed(s->graph)||s->sequence==UINT64_MAX)return false;
    WoodContactQuery *q=calloc(1,sizeof *q);if(!q)return false;
    /* 提示僅供常見的新節點路徑；預先 describe、reset 或重註冊後須核對
     * 完整來源鍵與 VALID 狀態，失配時保留原本的求值及插入順序。 */
    q->collection_node_hint=geo_eval_node_count(s->graph);
    q->id=++s->sequence;q->request=*request;q->cap=cap<WOOD_CONTACT_FACE_CAPACITY?cap:WOOD_CONTACT_FACE_CAPACITY;
    q->next=s->queries;s->queries=q;
    WoodContactSourceKey key;GeoSourceValue collection;
    if(geo_eval_source(s->graph,wood_contact_source_ref(s->token,WOOD_CONTACT_SOURCE_COLLECTION,q->id,0,&key),
        GEO_DEPENDENCY_VALUE_REQUIRED,&collection)!=GEO_SOURCE_OK)return false;
    const unsigned char *bytes;size_t n;
    if(!wood_contact_source_collection_view(&collection,q->cap,&bytes,&n))return false;
    (void)bytes;WoodStopFace *result=n?calloc(n,sizeof *result):NULL;if(n&&!result)return false;
    for(size_t i=0;i<n;++i){GeoSourceValue value;
        if(geo_eval_source(s->graph,wood_contact_source_ref(s->token,WOOD_CONTACT_SOURCE_FEATURE,q->id,(uint64_t)i,&key),
            GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK||!wood_contact_source_face(&value,q->request.along_v,&result[i])){
            free(result);return false;
        }
    }
    if(n)memcpy(out,result,n*sizeof *out);free(result);*count=n;return true;
}
void wood_contact_sources_destroy(WoodContactSources *s)
{
    if(!s)return;WoodContactQuery *q=s->queries;
    free(s->result_memo);
    while(q){WoodContactQuery *next=q->next;free(q->collection);free(q);q=next;}
    free(s);
}
