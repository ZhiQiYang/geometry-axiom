#include "definition_sources.h"
#include <stdlib.h>
#include <string.h>

typedef struct WoodDefinitionResult {
    WoodDefinitionKey key; struct WoodDefinitionResult *next;
    unsigned char *bytes; size_t size;
} WoodDefinitionResult;
struct WoodDefinitionSources {
    GeoEvalContext *graph; GeoProviderToken token; WoodDefinitionContext context;
    WoodDefinitionResult *results;
};
typedef struct {unsigned char *bytes;size_t at,capacity;bool ok;} WoodDefinitionWriter;
typedef struct {const unsigned char *bytes;size_t at,size;bool ok;} WoodDefinitionReader;
static void wd_write(WoodDefinitionWriter *w,uint64_t n,size_t bytes)
{if(!w->ok||bytes>w->capacity-w->at){w->ok=false;return;}for(size_t i=0;i<bytes;++i)w->bytes[w->at++]=(unsigned char)(n>>(8*(bytes-i-1)));}
static uint64_t wd_read(WoodDefinitionReader *r,size_t bytes)
{
    uint64_t n=0;if(!r->ok||bytes>r->size-r->at){r->ok=false;return 0;}
    switch(bytes){
    case 1:n=r->bytes[r->at];break;
    case 4:{
        const unsigned char *p=r->bytes+r->at;
        n=((uint64_t)p[0]<<24)|((uint64_t)p[1]<<16)|((uint64_t)p[2]<<8)|(uint64_t)p[3];
        break;
    }
    case 8:{
        const unsigned char *p=r->bytes+r->at;
        n=((uint64_t)p[0]<<56)|((uint64_t)p[1]<<48)|((uint64_t)p[2]<<40)|((uint64_t)p[3]<<32)|
          ((uint64_t)p[4]<<24)|((uint64_t)p[5]<<16)|((uint64_t)p[6]<<8)|(uint64_t)p[7];
        break;
    }
    default:for(size_t i=0;i<bytes;++i)n=(n<<8)|r->bytes[r->at++];return n;
    }
    r->at+=bytes;return n;
}
static int64_t wd_signed(uint64_t n)
{return n<=INT64_MAX?(int64_t)n:-1-(int64_t)(UINT64_MAX-n);}
static void wd_text(WoodDefinitionWriter *w,const char *s,size_t capacity)
{size_t n=0;while(n<capacity&&s[n])++n;if(n==capacity){w->ok=false;return;}wd_write(w,n,4);for(size_t i=0;i<n;++i)wd_write(w,(unsigned char)s[i],1);}
static void wd_read_text(WoodDefinitionReader *r,char *s,size_t capacity)
{uint64_t n=wd_read(r,4);if(!r->ok||n>=capacity||n>r->size-r->at){r->ok=false;return;}memcpy(s,r->bytes+r->at,(size_t)n);s[n]=0;r->at+=(size_t)n;}
GeoSourceRef wood_definition_source_ref(GeoProviderToken token,WoodDefinitionKind kind,uint32_t id,WoodDefinitionKey *key)
{if(!key)return (GeoSourceRef){token,NULL,0};WoodDefinitionWriter w={key->bytes,0,sizeof key->bytes,true};wd_write(&w,kind,1);wd_write(&w,id,4);return (GeoSourceRef){token,key->bytes,sizeof key->bytes};}
bool wood_definition_source_decode(const GeoSourceRef *ref,WoodDefinitionKind *kind,uint32_t *id)
{if(!ref||!ref->key||ref->key_size!=5||!kind||!id)return false;WoodDefinitionReader r={ref->key,0,5,true};unsigned k=(unsigned)wd_read(&r,1);uint32_t n=(uint32_t)wd_read(&r,4);if(k<WOOD_DEFINITION_MEMBER||k>WOOD_DEFINITION_BOUNDARY)return false;*kind=(WoodDefinitionKind)k;*id=n;return true;}
static int wd_member_index(const WoodDocument *d,uint32_t id)
{for(size_t i=0;i<d->timber_count;++i)if(d->timbers[i].id==id)return (int)i;return -1;}
static bool wd_member_literal(const WoodDocument *d,uint32_t id,int field)
{for(size_t i=0;i<d->assembly.owner_count;++i)if(d->assembly.owners[i].timber==id)return false;
 for(size_t i=0;i<d->engineering.binding_count;++i){const EngTarget *t=&d->engineering.bindings[i].target;if(t->kind==1&&t->id==id&&t->axis==0&&t->field==field)return false;}return true;}
static void wd_member_write(WoodDefinitionWriter *w,const WoodDocument *d,size_t i)
{const WoodMember *m=&d->timbers[i];wd_write(w,m->id,4);wd_write(w,m->auto_length,1);wd_write(w,(uint32_t)m->role,4);wd_write(w,(uint64_t)m->cut_priority,8);
 for(int a=0;a<2;++a){bool literal=wd_member_literal(d,m->id,a);wd_write(w,literal,1);if(literal)wd_write(w,(uint64_t)(a?m->size_b:m->size_a),8);}}
static void wd_member_read(WoodDefinitionReader *r,WoodMemberDefinition *m)
{m->id=(uint32_t)wd_read(r,4);m->auto_length=wd_read(r,1)!=0;m->role=(WoodMemberRole)(int32_t)wd_read(r,4);m->priority=wd_signed(wd_read(r,8));
 for(int a=0;a<2;++a){m->literal[a]=wd_read(r,1)!=0;if(m->literal[a])m->dimension[a]=wd_signed(wd_read(r,8));}}
static void wd_rule_write(WoodDefinitionWriter *w,const GeoGridRuleLineRef *a)
{wd_write(w,a->grid_id,4);wd_write(w,a->system_id,4);wd_write(w,a->rule_key,4);for(int i=0;i<2;++i)wd_write(w,(uint64_t)a->cell[i],8);wd_write(w,(uint32_t)a->axis,4);wd_write(w,a->inner_index,4);}
static void wd_rule_read(WoodDefinitionReader *r,GeoGridRuleLineRef *a)
{a->grid_id=(uint32_t)wd_read(r,4);a->system_id=(uint32_t)wd_read(r,4);a->rule_key=(uint32_t)wd_read(r,4);for(int i=0;i<2;++i)a->cell[i]=wd_signed(wd_read(r,8));a->axis=(int32_t)wd_read(r,4);a->inner_index=(uint32_t)wd_read(r,4);}
static void wd_placement_write(WoodDefinitionWriter *w,uint32_t id,const WoodMemberPlacement *a)
{
    wd_write(w,id,4);wd_write(w,a->placement_id,4);wd_write(w,(uint32_t)a->anchor_kind,4);wd_write(w,(uint32_t)a->span_mode,4);
    wd_write(w,(uint32_t)a->length_direction,4);wd_write(w,(uint32_t)a->depth_side,4);
    /* uv is only an authored input in the two legacy explicit-anchor forms. */
    bool input_uv=a->anchor_kind==WOOD_ANCHOR_AT||a->anchor_kind==WOOD_ANCHOR_AT_GUIDES;
    wd_write(w,(uint64_t)(input_uv?a->uv.u:0),8);wd_write(w,(uint64_t)(input_uv?a->uv.v:0),8);
    wd_write(w,a->ref_grid,4);wd_write(w,(uint32_t)a->ref_grid_axis,4);wd_write(w,(uint64_t)a->ref_grid_index,8);
    wd_write(w,a->ref_grid_has_band,1);wd_write(w,(uint64_t)a->ref_grid_band,8);wd_rule_write(w,&a->ref_rule);
    wd_write(w,(uint32_t)a->ref_hole,4);wd_write(w,(uint32_t)a->ref_edge,4);wd_write(w,a->has_through,1);wd_write(w,(uint64_t)a->through,8);
    wd_write(w,a->ref_guide,4);wd_write(w,a->ref_timber,4);wd_write(w,a->ref_is_timber,1);wd_text(w,a->ref_derived_key,sizeof a->ref_derived_key);
    wd_write(w,a->order,8);wd_write(w,a->has_between,1);
    for(int i=0;i<2;++i){const WoodMemberReferenceFace *f=&a->between[i];wd_write(w,(uint32_t)f->kind,4);wd_write(w,(uint32_t)f->hole,4);wd_write(w,(uint32_t)f->edge,4);wd_write(w,f->timber,4);wd_text(w,f->key,sizeof f->key);}
}
static uint32_t wd_placement_read(WoodDefinitionReader *r,WoodMemberPlacement *a)
{
    uint32_t id=(uint32_t)wd_read(r,4);a->placement_id=(uint32_t)wd_read(r,4);a->anchor_kind=(int32_t)wd_read(r,4);a->span_mode=(int32_t)wd_read(r,4);
    a->length_direction=(int32_t)wd_read(r,4);a->depth_side=(int32_t)wd_read(r,4);a->uv.u=wd_signed(wd_read(r,8));a->uv.v=wd_signed(wd_read(r,8));
    a->ref_grid=(uint32_t)wd_read(r,4);a->ref_grid_axis=(int32_t)wd_read(r,4);a->ref_grid_index=wd_signed(wd_read(r,8));
    a->ref_grid_has_band=wd_read(r,1)!=0;a->ref_grid_band=wd_signed(wd_read(r,8));wd_rule_read(r,&a->ref_rule);
    a->ref_hole=(int32_t)wd_read(r,4);a->ref_edge=(int32_t)wd_read(r,4);a->has_through=wd_read(r,1)!=0;a->through=wd_signed(wd_read(r,8));
    a->ref_guide=(uint32_t)wd_read(r,4);a->ref_timber=(uint32_t)wd_read(r,4);a->ref_is_timber=wd_read(r,1)!=0;wd_read_text(r,a->ref_derived_key,sizeof a->ref_derived_key);
    a->order=wd_read(r,8);a->has_between=wd_read(r,1)!=0;
    for(int i=0;i<2;++i){WoodMemberReferenceFace *f=&a->between[i];f->kind=(int32_t)wd_read(r,4);f->hole=(int32_t)wd_read(r,4);f->edge=(int32_t)wd_read(r,4);f->timber=(uint32_t)wd_read(r,4);wd_read_text(r,f->key,sizeof f->key);}return id;
}
static const char *wd_schema(WoodDefinitionKind kind)
{switch(kind){case WOOD_DEFINITION_MEMBER:return "wood.member.declaration/1";case WOOD_DEFINITION_PLACEMENT:return "wood.member.placement/1";case WOOD_DEFINITION_COLUMN:return "wood.rc-column/1";case WOOD_DEFINITION_BEAM:return "wood.rc-beam/1";case WOOD_DEFINITION_BOUNDARY:return "wood.boundary-policy/1";default:return NULL;}}
static bool wd_get(WoodDefinitionSources *s,WoodDefinitionKind kind,uint32_t id,GeoDependencyKind relation,GeoSourceValue *out)
{if(!s)return false;WoodDefinitionKey key;return geo_eval_source(s->graph,wood_definition_source_ref(s->token,kind,id,&key),relation,out)==GEO_SOURCE_OK;}
static bool wd_reader(WoodDefinitionSources *s,WoodDefinitionKind kind,uint32_t id,WoodDefinitionReader *out)
{GeoSourceValue value;if(!wd_get(s,kind,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value)||value.kind!=GEO_SOURCE_DEFINITION||!value.as.definition.schema||strcmp(value.as.definition.schema,wd_schema(kind))||(!value.as.definition.content&&value.as.definition.content_size))return false;*out=(WoodDefinitionReader){value.as.definition.content,0,value.as.definition.content_size,true};return true;}
bool wood_definition_sources_member(WoodDefinitionSources *s,uint32_t id,WoodMemberDefinition *out)
{if(!out)return false;WoodDefinitionReader r;WoodMemberDefinition m={0};if(!wd_reader(s,WOOD_DEFINITION_MEMBER,id,&r))return false;wd_member_read(&r,&m);if(!r.ok||r.at!=r.size||m.id!=id)return false;*out=m;return true;}
bool wood_definition_sources_placement(WoodDefinitionSources *s,uint32_t id,WoodMemberPlacement *out)
{if(!out)return false;WoodDefinitionReader r;WoodMemberPlacement a={0};if(!wd_reader(s,WOOD_DEFINITION_PLACEMENT,id,&r))return false;uint32_t actual=wd_placement_read(&r,&a);if(!r.ok||r.at!=r.size||actual!=id)return false;*out=a;return true;}
bool wood_definition_sources_dimension(WoodDefinitionSources *s,uint32_t id,bool b,GeoCoord *out)
{if(!out)return false;GeoSourceValue v;if(!wd_get(s,b?WOOD_DEFINITION_MEMBER_B:WOOD_DEFINITION_MEMBER_A,id,GEO_DEPENDENCY_VALUE_REQUIRED,&v)||v.kind!=GEO_SOURCE_QUANTITY||v.as.quantity.unit!=GEO_UNIT_LENGTH||v.as.quantity.den!=1)return false;*out=v.as.quantity.num;return true;}
static void wd_box_write(WoodDefinitionWriter *w,uint32_t id,uint32_t space,int axis,GeoCoord xl,GeoCoord xh,GeoCoord yl,GeoCoord yh,GeoCoord zl,GeoCoord zh,bool beam)
{wd_write(w,id,4);wd_write(w,space,4);if(beam)wd_write(w,(uint32_t)axis,4);GeoCoord fields[]={xl,xh,yl,yh,zl,zh};for(int i=0;i<6;++i)wd_write(w,(uint64_t)fields[i],8);}
bool wood_definition_sources_column(WoodDefinitionSources *s,uint32_t id,WoodColumn *out)
{if(!out)return false;WoodDefinitionReader r;WoodColumn b={0};if(!wd_reader(s,WOOD_DEFINITION_COLUMN,id,&r))return false;b.id=(uint32_t)wd_read(&r,4);b.space_id=(uint32_t)wd_read(&r,4);b.x_lo=wd_signed(wd_read(&r,8));b.x_hi=wd_signed(wd_read(&r,8));b.y_lo=wd_signed(wd_read(&r,8));b.y_hi=wd_signed(wd_read(&r,8));b.z_lo=wd_signed(wd_read(&r,8));b.z_hi=wd_signed(wd_read(&r,8));if(!r.ok||r.at!=r.size||b.id!=id)return false;*out=b;return true;}
bool wood_definition_sources_beam(WoodDefinitionSources *s,uint32_t id,WoodBeam *out)
{if(!out)return false;WoodDefinitionReader r;WoodBeam b={0};if(!wd_reader(s,WOOD_DEFINITION_BEAM,id,&r))return false;b.id=(uint32_t)wd_read(&r,4);b.space_id=(uint32_t)wd_read(&r,4);b.axis=(int32_t)wd_read(&r,4);b.x_lo=wd_signed(wd_read(&r,8));b.x_hi=wd_signed(wd_read(&r,8));b.y_lo=wd_signed(wd_read(&r,8));b.y_hi=wd_signed(wd_read(&r,8));b.z_lo=wd_signed(wd_read(&r,8));b.z_hi=wd_signed(wd_read(&r,8));if(!r.ok||r.at!=r.size||b.id!=id)return false;*out=b;return true;}
bool wood_definition_sources_boundary(WoodDefinitionSources *s,uint32_t id,WoodBoundaryPolicy *out)
{if(!out)return false;WoodDefinitionReader r;WoodBoundaryPolicy b={0};if(!wd_reader(s,WOOD_DEFINITION_BOUNDARY,id,&r))return false;b.id=(uint32_t)wd_read(&r,4);b.kind=(WoodBoundaryKind)(int32_t)wd_read(&r,4);uint64_t loops=wd_read(&r,4);if(loops>GEO_REGION_MAX_HOLES+1)return false;for(size_t l=0;l<loops;++l){uint64_t n=wd_read(&r,4);if(n>GEO_LOOP_MAX_VERTICES)return false;for(size_t i=0;i<n;++i)b.fixity[l][i]=(WoodEdgeFixity)(int32_t)wd_read(&r,4);}if(!r.ok||r.at!=r.size||b.id!=id)return false;*out=b;return true;}
static bool wd_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{WoodDefinitionSources *s=user;WoodDefinitionKind kind;uint32_t id;if(ref->provider!=s->token||!wood_definition_source_decode(ref,&kind,&id))return false;bool quantity=kind==WOOD_DEFINITION_MEMBER_A||kind==WOOD_DEFINITION_MEMBER_B;*out=(GeoSourceDescriptor){.kind=quantity?GEO_SOURCE_QUANTITY:GEO_SOURCE_DEFINITION,.unit=quantity?GEO_UNIT_LENGTH:GEO_UNIT_SCALAR,.context={false,0,-1}};return true;}
static bool wd_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    WoodDefinitionSources *s=user;WoodDefinitionKind kind;uint32_t id;if(graph!=s->graph||ref->provider!=s->token||!wood_definition_source_decode(ref,&kind,&id))return false;
    if(kind==WOOD_DEFINITION_MEMBER_A||kind==WOOD_DEFINITION_MEMBER_B){WoodMemberDefinition m;if(!wood_definition_sources_member(s,id,&m))return false;int axis=kind==WOOD_DEFINITION_MEMBER_B;if(!m.literal[axis])return false;*out=(GeoSourceValue){.kind=GEO_SOURCE_QUANTITY,.as.quantity={m.dimension[axis],1,GEO_UNIT_LENGTH}};return true;}
    /* Enough for all bounded strings and all active boundary edge policies. */
    unsigned char bytes[4096];WoodDefinitionWriter w={bytes,0,sizeof bytes,true};const WoodDocument *d=s->context.document;
    uint32_t space=0;
    if(kind==WOOD_DEFINITION_MEMBER||kind==WOOD_DEFINITION_PLACEMENT){int i=wd_member_index(d,id);if(i<0)return false;if(kind==WOOD_DEFINITION_MEMBER)wd_member_write(&w,d,(size_t)i);else wd_placement_write(&w,id,&d->anchors[i]);}
    else if(kind==WOOD_DEFINITION_COLUMN){const WoodColumn *b=NULL;for(size_t i=0;i<d->column_count;++i)if(d->columns[i].id==id){b=&d->columns[i];break;}if(!b)return false;space=b->space_id;wd_box_write(&w,b->id,space,0,b->x_lo,b->x_hi,b->y_lo,b->y_hi,b->z_lo,b->z_hi,false);}
    else if(kind==WOOD_DEFINITION_BEAM){const WoodBeam *b=NULL;for(size_t i=0;i<d->beam_count;++i)if(d->beams[i].id==id){b=&d->beams[i];break;}if(!b)return false;space=b->space_id;wd_box_write(&w,b->id,space,b->axis,b->x_lo,b->x_hi,b->y_lo,b->y_hi,b->z_lo,b->z_hi,true);}
    else if(kind==WOOD_DEFINITION_BOUNDARY){const GeoRegionDefinition *r=NULL;size_t at=0;for(;at<geo_regions_count(s->context.regions);++at){r=geo_regions_at(s->context.regions,at);if(r&&r->id==id)break;}if(at>=geo_regions_count(s->context.regions)||at>=WOOD_DOCUMENT_BOUNDARY_CAPACITY||!r||r->hole_count>GEO_REGION_MAX_HOLES)return false;
        const WoodBoundaryPolicy *b=&d->boundary_policy[at];if(b->id!=id)return false;
        GeoRegionSourceKey key;GeoSourceValue geometry;
        if(geo_eval_source(graph,geo_region_source_ref(s->context.region_token,id,&key),GEO_DEPENDENCY_VALUE_REQUIRED,&geometry)!=GEO_SOURCE_OK||
           geometry.kind!=GEO_SOURCE_REGION_SET||geometry.as.regions.count!=1)return false;
        const GeoRegionView *view=&geometry.as.regions.regions[0];if(view->hole_count>GEO_REGION_MAX_HOLES)return false;
        wd_write(&w,id,4);wd_write(&w,(uint32_t)b->kind,4);wd_write(&w,view->hole_count+1,4);
        for(size_t l=0;l<=view->hole_count;++l){size_t n=l?view->holes[l-1].count:view->outline.count;if(n>GEO_LOOP_MAX_VERTICES)return false;wd_write(&w,n,4);for(size_t i=0;i<n;++i)wd_write(&w,(uint32_t)b->fixity[l][i],4);}
    }else return false;
    if(space){GeoEnclosureSourceKey key;if(geo_eval_depend(graph,geo_enclosure_source_ref(s->context.enclosure_token,GEO_ENCLOSURE_SOURCE_DEFINITION,space,-1,-1,&key),GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)return false;}
    if(!w.ok)return false;WoodDefinitionResult *result=calloc(1,sizeof *result);if(!result)return false;result->bytes=malloc(w.at?w.at:1);if(!result->bytes){free(result);return false;}memcpy(result->key.bytes,ref->key,5);memcpy(result->bytes,bytes,w.at);result->size=w.at;result->next=s->results;s->results=result;
    *out=(GeoSourceValue){.kind=GEO_SOURCE_DEFINITION,.as.definition={wd_schema(kind),result->bytes,result->size}};return true;
}
WoodDefinitionSources *wood_definition_sources_create(GeoEvalContext *graph,GeoProviderToken token,const WoodDefinitionContext *context)
{if(!graph||!context||!context->document||!context->regions)return NULL;WoodDefinitionSources *s=calloc(1,sizeof *s);if(!s)return NULL;s->graph=graph;s->token=token;s->context=*context;GeoSourceProvider p={token,"wood.definition","wood-authored-definition/1",s,wd_describe,wd_evaluate};if(!geo_eval_register(graph,&p)){free(s);return NULL;}return s;}
void wood_definition_sources_destroy(WoodDefinitionSources *s)
{if(!s)return;WoodDefinitionResult *r=s->results;while(r){WoodDefinitionResult *next=r->next;free(r->bytes);free(r);r=next;}free(s);}
bool wood_definition_sources_complete(WoodDefinitionSources *s)
{if(!s)return false;const WoodDocument *d=s->context.document;GeoSourceValue value;
 for(size_t i=0;i<d->timber_count;++i)if(!wd_get(s,WOOD_DEFINITION_MEMBER,d->timbers[i].id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value)||!wd_get(s,WOOD_DEFINITION_PLACEMENT,d->timbers[i].id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
 for(size_t i=0;i<d->column_count;++i)if(!wd_get(s,WOOD_DEFINITION_COLUMN,d->columns[i].id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
 for(size_t i=0;i<d->beam_count;++i)if(!wd_get(s,WOOD_DEFINITION_BEAM,d->beams[i].id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
 for(size_t i=0;i<geo_regions_count(s->context.regions);++i){const GeoRegionDefinition *r=geo_regions_at(s->context.regions,i);if(!r||!wd_get(s,WOOD_DEFINITION_BOUNDARY,r->id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;}return true;}
