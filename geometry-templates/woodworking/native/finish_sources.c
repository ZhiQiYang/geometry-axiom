#include "finish_sources.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct WoodFinishBoundarySource {
    uint32_t id;WoodBoundaryRegion value;
    unsigned char *policy;size_t policy_size;
    GeoLoop2View holes[GEO_REGION_MAX_HOLES];GeoRegionView region;
    struct WoodFinishBoundarySource *next;
} WoodFinishBoundarySource;
typedef struct {
    WoodDerivedValue value;
    unsigned char *policy;size_t policy_size;
    GeoLoop2View holes[WOOD_DERIVED_COMPONENT_MAX][GEO_REGION_MAX_HOLES];
    GeoRegionView regions[WOOD_DERIVED_COMPONENT_MAX];
} WoodFinishDerivedSource;
struct WoodFinishSources {
    GeoEvalContext *graph;WoodFinishSourceTokens tokens;
    WoodDerivedContext base,context;
    WoodFinishEvaluation finish_hooks;WoodDerivedEvaluation derived_hooks;
    char definitions[FS_MAX][8192];
    WoodFinishLayout fills[FS_MAX];
    WoodFinishDerivedSource *derived[FS_MAX];
    WoodFinishBoundarySource *boundaries;
};
GeoSourceRef wood_finish_source_ref(GeoProviderToken token,WoodFinishSourceKind kind,uint32_t id,WoodFinishSourceKey *key)
{
    key->bytes[0]=(unsigned char)kind;
    for(int i=0;i<4;++i)key->bytes[i+1]=(unsigned char)(id>>(24-8*i));
    return (GeoSourceRef){token,key->bytes,sizeof key->bytes};
}
bool wood_finish_source_decode(const GeoSourceRef *ref,WoodFinishSourceKind *kind,uint32_t *id)
{
    if(!ref||!ref->key||ref->key_size!=5||!kind||!id)return false;
    const unsigned char *bytes=ref->key;
    if(bytes[0]<WOOD_FINISH_SOURCE_DEFINITION||bytes[0]>WOOD_FINISH_SOURCE_BOUNDARY_POLICY)return false;
    uint32_t value=0;for(int i=1;i<5;++i)value=(value<<8)|bytes[i];
    *kind=(WoodFinishSourceKind)bytes[0];*id=value;return true;
}
static int wood_finish_fill_index(const WoodFinishSources *s,uint32_t id)
{for(size_t i=0;i<s->context.finish.state->fill_count&&i<FS_MAX;++i)if(s->context.finish.state->fills[i].id==id)return (int)i;return -1;}
static int wood_finish_derived_index(const WoodFinishSources *s,uint32_t id)
{for(size_t i=0;i<s->context.finish.state->host_count&&i<FS_MAX;++i)if(s->context.finish.state->hosts[i].id==id)return (int)i;return -1;}
static bool wood_finish_get(WoodFinishSources *s,WoodFinishSourceKind kind,uint32_t id,GeoDependencyKind relation,GeoSourceValue *out)
{
    WoodFinishSourceKey key;GeoSourceStatus status=geo_eval_source(s->graph,wood_finish_source_ref(s->tokens.finish,kind,id,&key),relation,out);
    if(status==GEO_SOURCE_MEMORY)return wood_fs_capacity_error(&s->context.finish,"I33 CAPACITY: finish source graph unavailable");
    if(status==GEO_SOURCE_CYCLE)return wood_fs_error(&s->context.finish,"R44: cyclic finish source");
    return status==GEO_SOURCE_OK;
}
static WoodFinishBoundarySource *wood_finish_boundary_slot(WoodFinishSources *s,uint32_t id)
{
    for(WoodFinishBoundarySource *b=s->boundaries;b;b=b->next)if(b->id==id)return b;
    WoodFinishBoundarySource *b=calloc(1,sizeof *b);if(!b)return NULL;
    b->id=id;b->next=s->boundaries;s->boundaries=b;return b;
}
/* Policy content is explicit big-endian bytes: version, id, boundary kind,
 * component count; then hole/edge counts, one-byte fixity and length-prefixed
 * UTF-8 key bytes. Coordinates and caches are deliberately absent. */
static void wood_finish_put32(unsigned char **p,uint32_t value)
{for(int i=3;i>=0;--i)*(*p)++=(unsigned char)(value>>(8*i));}
static bool wood_finish_copy_region(uint32_t id,const GeoRegionView *region,WoodBoundaryRegion *out)
{
    if(region->outline.count>GEO_LOOP_MAX_VERTICES||region->hole_count>GEO_REGION_MAX_HOLES)return false;
    out->id=id;out->outline.count=region->outline.count;out->hole_count=region->hole_count;
    memcpy(out->outline.v,region->outline.v,region->outline.count*sizeof *region->outline.v);
    for(size_t h=0;h<region->hole_count;++h){const GeoLoop2View *loop=&region->holes[h];if(loop->count>GEO_LOOP_MAX_VERTICES)return false;
        out->holes[h].count=loop->count;memcpy(out->holes[h].v,loop->v,loop->count*sizeof *loop->v);}
    return true;
}
static bool wood_finish_derived_geometry(WoodFinishSources *s,uint32_t id,WoodDerivedValue *out)
{
    GeoSourceValue region,height,frame;const DerivedPlacement *def=wood_dp_find(&s->context,id);if(!def)return false;
    if(!wood_finish_get(s,WOOD_FINISH_SOURCE_DERIVED_REGION,id,GEO_DEPENDENCY_VALUE_REQUIRED,&region)||region.kind!=GEO_SOURCE_REGION_SET||region.as.regions.count>WOOD_DERIVED_COMPONENT_MAX)return false;
    if(!wood_finish_get(s,WOOD_FINISH_SOURCE_DERIVED_H,id,GEO_DEPENDENCY_VALUE_REQUIRED,&height)||height.kind!=GEO_SOURCE_QUANTITY||height.as.quantity.den!=1)return false;
    if(!wood_finish_get(s,WOOD_FINISH_SOURCE_DERIVED_FRAME,id,GEO_DEPENDENCY_VALUE_REQUIRED,&frame)||frame.kind!=GEO_SOURCE_FRAME)return false;
    memset(out,0,sizeof *out);out->id=id;out->derived_fill_id=def->fill_id;out->derived_h=height.as.quantity.num;out->frame=frame.as.frame;out->component_count=region.as.regions.count;
    for(size_t c=0;c<out->component_count;++c)if(!wood_finish_copy_region(id,&region.as.regions.regions[c],&out->components[c]))return false;
    return true;
}
static bool wood_finish_encode_policy(WoodFinishSources *s,uint32_t id,const WoodBoundaryRegion *regions,size_t count,
    const WoodDerivedValue *derived,unsigned char **content,size_t *content_size)
{
    size_t size=10;for(size_t c=0;c<count;++c){const WoodBoundaryRegion *b=&regions[c];size+=4;
        for(size_t h=0;h<=b->hole_count;++h){const WoodBoundaryLoop *loop=h?&b->holes[h-1]:&b->outline;size+=4+loop->count*(3+(derived?511:0));}}
    unsigned char *bytes=malloc(size);if(!bytes)return wood_fs_capacity_error(&s->context.finish,"I33 CAPACITY: finish policy source unavailable");
    unsigned char *next=bytes;*next++=1;wood_finish_put32(&next,id);*next++=(unsigned char)(derived||!count?0:regions[0].kind);wood_finish_put32(&next,(uint32_t)count);
    for(size_t c=0;c<count;++c){const WoodBoundaryRegion *b=&regions[c];wood_finish_put32(&next,(uint32_t)b->hole_count);
        for(size_t h=0;h<=b->hole_count;++h){const WoodBoundaryLoop *loop=h?&b->holes[h-1]:&b->outline;wood_finish_put32(&next,(uint32_t)loop->count);
            for(size_t e=0;e<loop->count;++e){char key[512];size_t length=0;
                if(derived){if(!wood_dp_edge_key_direct(&s->context,derived,c,h?(int)h-1:-1,e,key,sizeof key)){free(bytes);return false;}length=strlen(key);}
                *next++=(unsigned char)loop->fixity[e];*next++=(unsigned char)(length>>8);*next++=(unsigned char)length;
                if(length){memcpy(next,key,length);next+=length;}}}}
    free(*content);*content=bytes;*content_size=(size_t)(next-bytes);return true;
}
typedef struct {const unsigned char *data;size_t size,at;} WoodFinishPolicyReader;
static bool wood_finish_policy_u32(WoodFinishPolicyReader *r,uint32_t *out)
{if(r->at>r->size||r->size-r->at<4)return false;uint32_t value=0;for(int i=0;i<4;++i)value=(value<<8)|r->data[r->at++];*out=value;return true;}
typedef bool (*WoodFinishPolicyEdge)(void *,size_t,int,size_t,unsigned,const unsigned char *,size_t);
static bool wood_finish_policy_utf8(const unsigned char *bytes,size_t length)
{
    for(size_t at=0;at<length;){size_t scalar=geo_utf8_scalar(bytes+at,length-at);if(!scalar)return false;at+=scalar;}
    return true;
}
static bool wood_finish_policy_walk(const GeoSourceValue *value,uint32_t id,bool derived,WoodDerivedValue *geometry,WoodFinishPolicyEdge visit,void *user)
{
    if(value->kind!=GEO_SOURCE_DEFINITION||!value->as.definition.schema||strcmp(value->as.definition.schema,derived?"wood.finish.derived-policy/1":"wood.finish.boundary-policy/1")||!value->as.definition.content||value->as.definition.content_size<10)return false;
    WoodFinishPolicyReader r={value->as.definition.content,value->as.definition.content_size,0};uint32_t stored,count;
    if(r.data[r.at++]!=1||!wood_finish_policy_u32(&r,&stored)||stored!=id)return false;unsigned kind=r.data[r.at++];if(kind>WOOD_BOUNDARY_WALL_ELEVATION)return false;
    if(!wood_finish_policy_u32(&r,&count)||count>WOOD_DERIVED_COMPONENT_MAX||(geometry&&geometry->component_count!=count))return false;
    for(size_t c=0;c<count;++c){uint32_t holes;if(!wood_finish_policy_u32(&r,&holes)||holes>GEO_REGION_MAX_HOLES)return false;
        WoodBoundaryRegion *region=geometry?&geometry->components[c]:NULL;if(region){if(region->hole_count!=holes)return false;region->kind=(WoodBoundaryKind)kind;}
        for(size_t h=0;h<=holes;++h){uint32_t edges;if(!wood_finish_policy_u32(&r,&edges)||edges>GEO_LOOP_MAX_VERTICES)return false;
            WoodBoundaryLoop *loop=region?(h?&region->holes[h-1]:&region->outline):NULL;if(loop&&loop->count!=edges)return false;
            for(size_t e=0;e<edges;++e){if(r.size-r.at<3)return false;unsigned fixity=r.data[r.at++];size_t length=(size_t)r.data[r.at++]<<8;length|=r.data[r.at++];
                if(fixity>WOOD_EDGE_FIXED||length>511||length>r.size-r.at||(derived?!length:length!=0)||memchr(r.data+r.at,0,length))return false;
                if(!wood_finish_policy_utf8(r.data+r.at,length))return false;
                if(loop)loop->fixity[e]=(WoodEdgeFixity)fixity;
                if(visit&&!visit(user,c,h?(int)h-1:-1,e,fixity,r.data+r.at,length))return false;r.at+=length;}}}
    return r.at==r.size;
}
static bool wood_finish_policy(WoodFinishSources *s,WoodFinishSourceKind kind,uint32_t id,GeoSourceValue *out)
{
    if(kind==WOOD_FINISH_SOURCE_BOUNDARY_POLICY){GeoSourceValue region;
        if(!wood_finish_get(s,WOOD_FINISH_SOURCE_BOUNDARY_REGION,id,GEO_DEPENDENCY_VALUE_REQUIRED,&region)||region.kind!=GEO_SOURCE_REGION_SET||region.as.regions.count!=1)return false;
        WoodFinishBoundarySource *b=wood_finish_boundary_slot(s,id);WoodBoundaryRegion value={0};if(!b||!wood_finish_copy_region(id,&region.as.regions.regions[0],&value))return false;
        value.kind=b->value.kind;
        for(size_t h=0;h<=value.hole_count;++h){WoodBoundaryLoop *loop=h?&value.holes[h-1]:&value.outline;const WoodBoundaryLoop *authored=h?&b->value.holes[h-1]:&b->value.outline;
            if(loop->count!=authored->count)return false;for(size_t e=0;e<loop->count;++e)loop->fixity[e]=authored->fixity[e];}
        if(!wood_finish_encode_policy(s,id,&value,1,NULL,&b->policy,&b->policy_size))return false;
        out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){"wood.finish.boundary-policy/1",b->policy,b->policy_size};return true;
    }
    int index=wood_finish_derived_index(s,id);if(index<0)return false;
    WoodDerivedValue *geometry=calloc(1,sizeof *geometry);if(!geometry)return wood_fs_capacity_error(&s->context.finish,"I33 CAPACITY: derived policy workspace unavailable");
    bool ok=wood_finish_derived_geometry(s,id,geometry)&&wood_dp_fixities_direct(&s->context,geometry);
    WoodFinishDerivedSource *d=s->derived[index];
    if(ok)ok=d&&wood_finish_encode_policy(s,id,geometry->components,geometry->component_count,geometry,&d->policy,&d->policy_size);
    free(geometry);if(!ok)return false;
    out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){"wood.finish.derived-policy/1",d->policy,d->policy_size};return true;
}
static bool wood_finish_definition(WoodFinishSources *s,WoodFinishSourceKind kind,uint32_t id,GeoSourceValue *out)
{
    const char *content=NULL,*schema=NULL;
    if(kind==WOOD_FINISH_SOURCE_DEFINITION){
        int index=wood_fs_index(&s->context.finish,id);if(index<0||index>=FS_MAX)return false;
        const FinishSurface *f=&s->context.finish.state->items[index];char *text=s->definitions[index];
        int n=snprintf(text,sizeof s->definitions[index],"id=%u;boundary=%u;side=%d;origin=%lld,%lld,%lld;U=%lld,%lld,%lld;V=%lld,%lld,%lld;N=%lld,%lld,%lld;name=",
            f->id,f->boundary_id,f->side,(long long)f->frame.origin.x,(long long)f->frame.origin.y,(long long)f->frame.origin.z,
            (long long)f->frame.axis_u.x,(long long)f->frame.axis_u.y,(long long)f->frame.axis_u.z,
            (long long)f->frame.axis_v.x,(long long)f->frame.axis_v.y,(long long)f->frame.axis_v.z,
            (long long)f->frame.normal.x,(long long)f->frame.normal.y,(long long)f->frame.normal.z);
        if(n<0||(size_t)n>=sizeof s->definitions[index])return false;size_t used=(size_t)n;
        for(size_t i=0;i<sizeof f->name&&f->name[i];++i){n=snprintf(text+used,sizeof s->definitions[index]-used,"%02x",(unsigned char)f->name[i]);if(n!=2)return false;used+=2;}
        n=snprintf(text+used,sizeof s->definitions[index]-used,";obstacles=%u",f->obstacle_count);if(n<0)return false;used+=(size_t)n;
        for(size_t i=0;i<f->obstacle_count&&i<FS_OBSTACLE_MAX;++i){n=snprintf(text+used,sizeof s->definitions[index]-used,";%u:%u",f->obstacles[i].kind,f->obstacles[i].id);if(n<0||(size_t)n>=sizeof s->definitions[index]-used)return false;used+=(size_t)n;}
        content=text;schema="wood.finish.definition/1";
    }else if(kind==WOOD_FINISH_SOURCE_FILL_DEFINITION){
        const PanelFill *p=wood_pf_find(&s->context.finish,id);if(!p)return false;content=p->definition;schema="wood.finish.panel-fill/1";
    }else if(kind==WOOD_FINISH_SOURCE_PANEL_DEFINITION){
        const PanelFill *p=wood_pf_find(&s->context.finish,id);if(!p)return false;
        const EngMaterialVersion *m=wood_eng_material(&s->context.finish.engineering,p->panel.id,p->panel.version);if(!m)return false;
        WoodEngineeringContext *e=&s->context.finish.engineering;GeoVersionView version;
        if(!wood_eng_version_view(e,0,p->panel.id,p->panel.version,&version))return false;
        if(e->depend_definition&&!e->depend_definition(e->sources,0,m->ref.id,m->ref.version))return false;
        out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){"woodworking.material-version/1",version.content,version.content_length};return true;
    }else if(kind==WOOD_FINISH_SOURCE_DERIVED_DEFINITION){
        const DerivedPlacement *p=wood_dp_find(&s->context,id);if(!p)return false;content=p->definition;schema="wood.finish.derived-placement/1";
    }
    if(!content)return false;out->kind=GEO_SOURCE_DEFINITION;out->as.definition=(GeoDefinitionValue){schema,content,strlen(content)};return true;
}
static bool wood_finish_describe(void *user,const GeoSourceRef *ref,GeoSourceDescriptor *out)
{
    WoodFinishSources *s=user;WoodFinishSourceKind kind;uint32_t id;
    if(ref->provider!=s->tokens.finish||!wood_finish_source_decode(ref,&kind,&id))return false;
    GeoSourceDescriptor d={.kind=GEO_SOURCE_DEFINITION,.unit=GEO_UNIT_SCALAR,.context={false,0,-1},.retry_failure=true};
    if(kind<=WOOD_FINISH_SOURCE_REGION){if(!wood_fs_find(&s->context.finish,id))return false;
        if(kind==WOOD_FINISH_SOURCE_FRAME)d.kind=GEO_SOURCE_FRAME;else if(kind==WOOD_FINISH_SOURCE_REGION)d.kind=GEO_SOURCE_REGION_SET;
    }else if(kind==WOOD_FINISH_SOURCE_BOUNDARY_REGION)d.kind=GEO_SOURCE_REGION_SET;
    else if(kind==WOOD_FINISH_SOURCE_BOUNDARY_POLICY)d.kind=GEO_SOURCE_DEFINITION;
    else if(kind==WOOD_FINISH_SOURCE_COLUMN_BOX||kind==WOOD_FINISH_SOURCE_BEAM_BOX)d.kind=GEO_SOURCE_BOX;
    else if(kind<=WOOD_FINISH_SOURCE_PANEL_DEFINITION){if(wood_finish_fill_index(s,id)<0)return false;
        if(kind==WOOD_FINISH_SOURCE_FILL_FRAME)d.kind=GEO_SOURCE_FRAME;
        else if(kind>=WOOD_FINISH_SOURCE_PANEL_LENGTH&&kind<=WOOD_FINISH_SOURCE_THRESHOLD)d.kind=GEO_SOURCE_QUANTITY;
    }else{if(wood_finish_derived_index(s,id)<0)return false;
        if(kind==WOOD_FINISH_SOURCE_DERIVED_H)d.kind=GEO_SOURCE_QUANTITY;
        else if(kind==WOOD_FINISH_SOURCE_DERIVED_FRAME)d.kind=GEO_SOURCE_FRAME;
        else if(kind==WOOD_FINISH_SOURCE_DERIVED_REGION)d.kind=GEO_SOURCE_REGION_SET;
    }
    if(d.kind!=GEO_SOURCE_DEFINITION)d.unit=GEO_UNIT_LENGTH;*out=d;return true;
}
static bool wood_finish_parameter_value(WoodFinishSources *s,const PanelFill *p,int field,GeoQuantity *out)
{
    GeoQuantity checked;if(!wood_pf_field_direct(&s->context.finish,p,field,&checked))return false;
    GeoParameterRef ref=field==WOOD_PF_GAP?p->gap_ref:field==WOOD_PF_STAGGER?p->stagger_ref:p->threshold;
    if(!ref.set||!s->tokens.parameter){*out=checked;return true;}
    uint32_t key[]={ref.parameter_id,ref.field_id};GeoSourceValue value;
    if(geo_eval_source(s->graph,(GeoSourceRef){s->tokens.parameter,key,sizeof key},GEO_DEPENDENCY_VALUE_REQUIRED,&value)!=GEO_SOURCE_OK)return false;
    if(value.kind!=GEO_SOURCE_QUANTITY||value.as.quantity.unit!=checked.unit||value.as.quantity.num!=checked.num||value.as.quantity.den!=checked.den)return false;
    *out=value.as.quantity;return true;
}
static bool wood_finish_evaluate(void *user,GeoEvalContext *graph,const GeoSourceRef *ref,GeoSourceValue *out)
{
    WoodFinishSources *s=user;WoodFinishSourceKind kind;uint32_t id;
    if(graph!=s->graph||ref->provider!=s->tokens.finish||!wood_finish_source_decode(ref,&kind,&id))return false;
    if(kind==WOOD_FINISH_SOURCE_DEFINITION||kind==WOOD_FINISH_SOURCE_FILL_DEFINITION||kind==WOOD_FINISH_SOURCE_PANEL_DEFINITION||kind==WOOD_FINISH_SOURCE_DERIVED_DEFINITION)
        return wood_finish_definition(s,kind,id,out);
    GeoSourceValue value;
    if(kind==WOOD_FINISH_SOURCE_BOUNDARY_POLICY||kind==WOOD_FINISH_SOURCE_DERIVED_POLICY)return wood_finish_policy(s,kind,id,out);
    if(kind<=WOOD_FINISH_SOURCE_REGION){
        const FinishSurface *f=wood_fs_find(&s->context.finish,id);if(!f)return false;
        if(!wood_finish_get(s,WOOD_FINISH_SOURCE_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
        if(kind==WOOD_FINISH_SOURCE_CHECK){if(!wood_fs_check_direct(&s->context.finish,f))return false;*out=value;return true;}
        if(kind==WOOD_FINISH_SOURCE_FRAME){out->kind=GEO_SOURCE_FRAME;out->as.frame=f->frame;return true;}
        return wood_finish_get(s,WOOD_FINISH_SOURCE_BOUNDARY_REGION,f->boundary_id,GEO_DEPENDENCY_VALUE_REQUIRED,out);
    }
    if(kind==WOOD_FINISH_SOURCE_BOUNDARY_REGION){
        WoodFinishBoundarySource *b=wood_finish_boundary_slot(s,id);if(!b)return wood_fs_capacity_error(&s->context.finish,"I33 CAPACITY: finish boundary source unavailable");
        if(!s->base.finish.boundary(s->base.finish.user,id,&b->value))return false;
        b->region=wood_pf_region_view(&b->value,b->holes);out->kind=GEO_SOURCE_REGION_SET;out->as.regions=(GeoRegionSetView){&b->region,1};return true;
    }
    if(kind==WOOD_FINISH_SOURCE_COLUMN_BOX||kind==WOOD_FINISH_SOURCE_BEAM_BOX){
        FinishObstacleRef obstacle={kind==WOOD_FINISH_SOURCE_BEAM_BOX?FS_OBSTACLE_BEAM:FS_OBSTACLE_COLUMN,id};GeoCoord lo[3],hi[3];
        if(!s->base.finish.obstacle_box(s->base.finish.user,&obstacle,lo,hi))return false;
        out->kind=GEO_SOURCE_BOX;out->as.box=(GeoBox3){.frame={{lo[0],lo[1],lo[2]},{1,0,0},{0,1,0},{0,0,1}},.extent={hi[0]-lo[0],hi[1]-lo[1],hi[2]-lo[2]}};return true;
    }
    if(kind<=WOOD_FINISH_SOURCE_THRESHOLD){
        int index=wood_finish_fill_index(s,id);if(index<0)return false;const PanelFill *p=&s->context.finish.state->fills[index];
        if(!wood_finish_get(s,WOOD_FINISH_SOURCE_FILL_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
        if(kind==WOOD_FINISH_SOURCE_FILL_FRAME){
            WoodFinishLayout *d=&s->fills[index];memset(d,0,sizeof *d);
            if(!wood_pf_values_direct(&s->context.finish,p,d))return false;
            if(!wood_finish_get(s,WOOD_FINISH_SOURCE_FRAME,p->finish_id,GEO_DEPENDENCY_VALUE_REQUIRED,out))return false;
            d->frame=out->as.frame;return true;
        }
        int field=(int)kind-(int)WOOD_FINISH_SOURCE_PANEL_LENGTH;GeoQuantity quantity;
        if(field<=WOOD_PF_THICKNESS){
            if(!wood_finish_get(s,WOOD_FINISH_SOURCE_PANEL_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value)||!wood_pf_field_direct(&s->context.finish,p,field,&quantity))return false;
        }else if(!wood_finish_parameter_value(s,p,field,&quantity))return false;
        out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=quantity;return true;
    }
    int index=wood_finish_derived_index(s,id);if(index<0)return false;const DerivedPlacement *def=&s->context.finish.state->hosts[index];
    if(!wood_finish_get(s,WOOD_FINISH_SOURCE_DERIVED_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
    if(kind==WOOD_FINISH_SOURCE_DERIVED_H){GeoCoord h;if(!wood_dp_height_direct(&s->context,def,&h))return false;out->kind=GEO_SOURCE_QUANTITY;out->as.quantity=(GeoQuantity){h,1,GEO_UNIT_LENGTH};return true;}
    if(kind==WOOD_FINISH_SOURCE_DERIVED_FRAME){
        WoodDerivedValue prior;if(!s->base.placement_read(s->base.finish.user,id,&prior)||!prior.derived_fill_id)return wood_fs_error(&s->context.finish,"D4: derived placement variant or identity missing");
        if(!wood_finish_get(s,WOOD_FINISH_SOURCE_DERIVED_H,id,GEO_DEPENDENCY_VALUE_REQUIRED,&value))return false;
        const PanelFill *fill=wood_pf_find(&s->context.finish,def->fill_id);if(!fill)return wood_fs_error(&s->context.finish,"I55/D4: derived placement %u source fill is missing",id);
        WoodFinishLayout d={0};if(!wood_pf_values(&s->context.finish,fill,&d))return false;
        GeoFrame frame;if(!wood_dp_frame_direct(&s->context,&d,&frame))return false;out->kind=GEO_SOURCE_FRAME;out->as.frame=frame;return true;
    }
    if(kind==WOOD_FINISH_SOURCE_DERIVED_REGION){
        if(!s->derived[index])s->derived[index]=calloc(1,sizeof *s->derived[index]);
        WoodFinishDerivedSource *d=s->derived[index];if(!d)return wood_fs_capacity_error(&s->context.finish,"I33 CAPACITY: derived source unavailable");
        if(!wood_dp_value_direct(&s->context,def,&d->value))return false;
        for(size_t i=0;i<d->value.component_count;++i)d->regions[i]=wood_pf_region_view(&d->value.components[i],d->holes[i]);
        out->kind=GEO_SOURCE_REGION_SET;out->as.regions=(GeoRegionSetView){d->regions,d->value.component_count};return true;
    }
    return false;
}
static bool wood_finish_check_hook(void *user,const FinishSurface *f)
{
    WoodFinishSources *s=user;if(wood_fs_find(&s->context.finish,f->id)!=f)return wood_fs_check_direct(&s->context.finish,f);
    GeoSourceValue value;return wood_finish_get(s,WOOD_FINISH_SOURCE_CHECK,f->id,GEO_DEPENDENCY_VALUE_REQUIRED,&value);
}
static bool wood_finish_definition_hook(void *user,uint32_t id)
{WoodFinishSources *s=user;GeoSourceValue value;return wood_finish_get(s,WOOD_FINISH_SOURCE_DEFINITION,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value);}
static bool wood_finish_field_hook(void *user,const PanelFill *p,int field,GeoQuantity *out)
{
    WoodFinishSources *s=user;if(wood_pf_find(&s->context.finish,p->id)!=p)return wood_pf_field_direct(&s->context.finish,p,field,out);
    GeoSourceValue value;if(!wood_finish_get(s,(WoodFinishSourceKind)(WOOD_FINISH_SOURCE_PANEL_LENGTH+field),p->id,GEO_DEPENDENCY_VALUE_REQUIRED,&value))return false;
    *out=value.as.quantity;return true;
}
static bool wood_finish_values_hook(void *user,const PanelFill *p,WoodFinishLayout *out)
{
    WoodFinishSources *s=user;if(wood_pf_find(&s->context.finish,p->id)!=p)return wood_pf_values_direct(&s->context.finish,p,out);
    GeoSourceValue value;if(!wood_finish_get(s,WOOD_FINISH_SOURCE_FILL_FRAME,p->id,GEO_DEPENDENCY_VALUE_REQUIRED,&value))return false;
    int index=wood_finish_fill_index(s,p->id);const WoodFinishLayout *d=&s->fills[index];
    out->finish=d->finish;out->frame=value.as.frame;out->t=d->t;out->layout.size[0]=d->layout.size[0];out->layout.size[1]=d->layout.size[1];out->layout.gap=d->layout.gap;out->layout.stagger=d->layout.stagger;
    memcpy(out->obstacles,d->obstacles,sizeof out->obstacles);memcpy(out->cuts,d->cuts,sizeof out->cuts);return true;
}
static bool wood_finish_boundary_hook(void *user,uint32_t id,WoodBoundaryRegion *out)
{
    WoodFinishSources *s=user;GeoSourceValue value,policy;if(!wood_finish_get(s,WOOD_FINISH_SOURCE_BOUNDARY_REGION,id,GEO_DEPENDENCY_VALUE_REQUIRED,&value)||value.kind!=GEO_SOURCE_REGION_SET||value.as.regions.count!=1)return false;
    if(!wood_finish_get(s,WOOD_FINISH_SOURCE_BOUNDARY_POLICY,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&policy))return false;
    WoodDerivedValue *geometry=calloc(1,sizeof *geometry);if(!geometry)return wood_fs_capacity_error(&s->context.finish,"I33 CAPACITY: boundary policy workspace unavailable");
    geometry->component_count=1;bool ok=wood_finish_copy_region(id,&value.as.regions.regions[0],&geometry->components[0])&&wood_finish_policy_walk(&policy,id,false,geometry,NULL,NULL);
    if(ok)*out=geometry->components[0];free(geometry);return ok;
}
static bool wood_finish_obstacle_hook(void *user,const FinishObstacleRef *ref,GeoCoord lo[3],GeoCoord hi[3])
{
    WoodFinishSources *s=user;GeoSourceValue value;
    if(!wood_finish_get(s,ref->kind==FS_OBSTACLE_BEAM?WOOD_FINISH_SOURCE_BEAM_BOX:WOOD_FINISH_SOURCE_COLUMN_BOX,ref->id,GEO_DEPENDENCY_VALUE_REQUIRED,&value))return false;
    lo[0]=value.as.box.frame.origin.x;lo[1]=value.as.box.frame.origin.y;lo[2]=value.as.box.frame.origin.z;
    for(int i=0;i<3;++i)hi[i]=lo[i]+value.as.box.extent[i];return true;
}
static bool wood_finish_height_hook(void *user,const DerivedPlacement *def,GeoCoord *out)
{WoodFinishSources *s=user;GeoSourceValue value;if(!wood_finish_get(s,WOOD_FINISH_SOURCE_DERIVED_H,def->id,GEO_DEPENDENCY_VALUE_REQUIRED,&value))return false;*out=value.as.quantity.num;return true;}
static bool wood_finish_frame_hook(void *user,const DerivedPlacement *def,const WoodFinishLayout *layout,GeoFrame *out)
{WoodFinishSources *s=user;GeoSourceValue value;(void)layout;if(!wood_finish_get(s,WOOD_FINISH_SOURCE_DERIVED_FRAME,def->id,GEO_DEPENDENCY_VALUE_REQUIRED,&value))return false;*out=value.as.frame;return true;}
bool wood_finish_sources_read_derived(WoodFinishSources *s,uint32_t id,WoodDerivedValue *out)
{
    if(!s||!out)return false;WoodDerivedValue *geometry=calloc(1,sizeof *geometry);
    if(!geometry)return wood_fs_capacity_error(&s->context.finish,"I33 CAPACITY: derived reader workspace unavailable");
    GeoSourceValue policy;bool ok=wood_finish_derived_geometry(s,id,geometry)&&
        wood_finish_get(s,WOOD_FINISH_SOURCE_DERIVED_POLICY,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&policy)&&wood_finish_policy_walk(&policy,id,true,geometry,NULL,NULL);
    if(ok)*out=*geometry;free(geometry);return ok;
}
static bool wood_finish_derived_hook(void *user,const DerivedPlacement *def,WoodDerivedValue *out)
{return wood_finish_sources_read_derived(user,def->id,out);}
typedef struct {size_t component,edge;int hole;const unsigned char *key;size_t size;} WoodFinishKeySelection;
static bool wood_finish_select_key(void *user,size_t component,int hole,size_t edge,unsigned fixity,const unsigned char *key,size_t size)
{WoodFinishKeySelection *selection=user;(void)fixity;if(component==selection->component&&hole==selection->hole&&edge==selection->edge){selection->key=key;selection->size=size;}return true;}
bool wood_finish_sources_edge_key(WoodFinishSources *s,uint32_t id,size_t component,int hole,size_t edge,char *out,size_t cap)
{
    if(!s)return false;GeoSourceValue policy;
    if(!wood_finish_get(s,WOOD_FINISH_SOURCE_DERIVED_POLICY,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&policy))return false;
    WoodFinishKeySelection selected={component,edge,hole<0?-1:hole,NULL,0};
    if(!wood_finish_policy_walk(&policy,id,true,NULL,wood_finish_select_key,&selected)||!selected.key)return false;
    if(cap>2){size_t copied=selected.size<cap-1?selected.size:cap-1;memcpy(out,selected.key,copied);out[copied]=0;}
    return (selected.size&&selected.size<cap&&cap>2)||wood_fs_capacity_error(&s->context.finish,"I33 CAPACITY: R41 key exceeds supported size");
}
typedef struct {const char *key;size_t size,matches;int *hole,*edge;} WoodFinishKeyMatch;
static bool wood_finish_match_key(void *user,size_t component,int hole,size_t edge,unsigned fixity,const unsigned char *key,size_t size)
{
    WoodFinishKeyMatch *match=user;(void)fixity;if(size==match->size&&!memcmp(key,match->key,size)){++match->matches;
        *match->hole=hole<0?-1:(int)(component*GEO_REGION_MAX_HOLES+(size_t)hole);
        *match->edge=hole<0?(int)(component*GEO_LOOP_MAX_VERTICES+edge):(int)edge;}return true;
}
bool wood_finish_sources_edge_resolve(WoodFinishSources *s,uint32_t id,const char *key,int *hole,int *edge)
{
    if(!s)return false;GeoSourceValue policy;
    if(!wood_finish_get(s,WOOD_FINISH_SOURCE_DERIVED_POLICY,id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&policy))return false;
    WoodFinishKeyMatch match={key,strlen(key),0,hole,edge};if(!wood_finish_policy_walk(&policy,id,true,NULL,wood_finish_match_key,&match))return false;
    return match.matches==1||wood_fs_error(&s->context.finish,"R41: key %.160s matches %zu derived edges; exactly one is required",key,match.matches);
}
static bool wood_finish_key_hook(void *user,const WoodDerivedValue *p,size_t component,int hole,size_t edge,char *out,size_t cap)
{return wood_finish_sources_edge_key(user,p->id,component,hole,edge,out,cap);}
static bool wood_finish_resolve_hook(void *user,const WoodDerivedValue *p,const char *key,int *hole,int *edge)
{return wood_finish_sources_edge_resolve(user,p->id,key,hole,edge);}
bool wood_finish_sources_definitions(WoodFinishSources *s)
{
    if(!s)return false;GeoSourceValue value;const FinishSurfaceState *state=s->context.finish.state;
    for(size_t i=0;i<state->count;++i)if(!wood_finish_get(s,WOOD_FINISH_SOURCE_DEFINITION,state->items[i].id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
    for(size_t i=0;i<state->fill_count;++i)if(!wood_finish_get(s,WOOD_FINISH_SOURCE_FILL_DEFINITION,state->fills[i].id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
    for(size_t i=0;i<state->host_count;++i)if(!wood_finish_get(s,WOOD_FINISH_SOURCE_DERIVED_DEFINITION,state->hosts[i].id,GEO_DEPENDENCY_DEFINITION_REQUIRED,&value))return false;
    return true;
}
WoodFinishSources *wood_finish_sources_create(GeoEvalContext *graph,WoodFinishSourceTokens tokens,const WoodDerivedContext *base)
{
    if(!graph||!base||!base->finish.state||!base->finish.boundary||!base->finish.obstacle_box||!base->finish.parameter_coord||!base->finish.parameter_value||!base->placement_read||base->finish.evaluation||base->evaluation)return NULL;
    WoodFinishSources *s=calloc(1,sizeof *s);if(!s)return NULL;s->graph=graph;s->tokens=tokens;s->base=*base;s->context=*base;
    s->finish_hooks=(WoodFinishEvaluation){s,wood_finish_check_hook,wood_finish_values_hook,wood_finish_field_hook,wood_finish_definition_hook,wood_finish_boundary_hook,wood_finish_obstacle_hook};
    s->derived_hooks=(WoodDerivedEvaluation){s,wood_finish_derived_hook,wood_finish_height_hook,wood_finish_frame_hook,wood_finish_key_hook,wood_finish_resolve_hook};
    s->context.finish.evaluation=&s->finish_hooks;s->context.evaluation=&s->derived_hooks;
    GeoSourceProvider provider={tokens.finish,"wood.finish","wood-finish-sources/1",s,wood_finish_describe,wood_finish_evaluate};
    if(!geo_eval_register(graph,&provider)){free(s);return NULL;}return s;
}
bool wood_finish_sources_bind_finish(WoodFinishSources *s,WoodFinishContext *w)
{
    if(!s||!w)return false;const WoodFinishContext *b=&s->base.finish;
    const WoodEngineeringContext *e=&w->engineering,*a=&b->engineering;
    if(w->state!=b->state||w->user!=b->user||w->error!=b->error||w->error_capacity!=b->error_capacity||w->diagnostic!=b->diagnostic||
       w->boundary!=b->boundary||w->obstacle_box!=b->obstacle_box||w->parameter_coord!=b->parameter_coord||w->parameter_value!=b->parameter_value||
       w->parameter_error!=b->parameter_error||w->parameter_error_capacity!=b->parameter_error_capacity||w->engineering_operation!=b->engineering_operation||w->derived_operation!=b->derived_operation||
       e->state!=a->state||e->versions!=a->versions||e->user!=a->user||e->error!=a->error||e->error_capacity!=a->error_capacity||e->sources!=a->sources||
       e->placement!=a->placement||e->target!=a->target||e->named_value!=a->named_value||e->parameter!=a->parameter||e->member_owned!=a->member_owned||e->write_dimension!=a->write_dimension||e->serializable!=a->serializable||
       e->resolve_source!=a->resolve_source||e->resolve_binding!=a->resolve_binding||e->source_named!=a->source_named||e->source_parameter!=a->source_parameter||e->depend_definition!=a->depend_definition||e->validate_application!=a->validate_application||e->source_version_field!=a->source_version_field||e->source_version_definition!=a->source_version_definition||e->source_application!=a->source_application)return false;
    w->evaluation=&s->finish_hooks;return true;
}
bool wood_finish_sources_bind(WoodFinishSources *s,WoodDerivedContext *w)
{
    if(!s||!w||w->placement_read!=s->base.placement_read||w->placement_write!=s->base.placement_write||w->placement_remove!=s->base.placement_remove||w->placement_count!=s->base.placement_count||w->placement_capacity!=s->base.placement_capacity||w->remove_canvas_position!=s->base.remove_canvas_position||!wood_finish_sources_bind_finish(s,&w->finish))return false;
    w->evaluation=&s->derived_hooks;return true;
}
void wood_finish_sources_destroy(WoodFinishSources *s)
{
    if(!s)return;for(size_t i=0;i<FS_MAX;++i)if(s->derived[i]){free(s->derived[i]->policy);free(s->derived[i]);}
    WoodFinishBoundarySource *b=s->boundaries;while(b){WoodFinishBoundarySource *next=b->next;free(b->policy);free(b);b=next;}free(s);
}
