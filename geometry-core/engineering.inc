/* H compatibility adapter. Domain definitions/resolution live in W. */
#include "../geometry-templates/woodworking/native/engineering.h"
#include "../geometry-app/native/versions_adapter.inc"
#include <stdarg.h>
static bool engineering_serializable(const World *w);
static char g_engineering_error[256];
static bool app_eng_placement(void *user,uint32_t id,bool *derived)
{const PlacementSurface *p=world_find_placement((World *)user,id);if(derived)*derived=p&&p->derived_fill_id;return p!=NULL;}
static bool app_eng_target(void *user,const EngTarget *t,WoodEngineeringTargetInfo *out)
{
    World *w=(World *)user;memset(out,0,sizeof *out);
    if(!t->kind){const ReferenceGrid *g=world_find_grid(w,t->id);if(!g)return false;out->placement_id=g->placement_id;out->from_system=g->from_system||g->from_binding;out->is_subgrid=g->is_subgrid;out->panel_axis=g->axis[t->axis].source==GRID_SRC_PANEL;}
    else{int i=reference_timber_index(w,t->id);if(i<0)return false;out->placement_id=w->anchors[i].placement_id;out->role=w->timbers[i].role;out->placed=w->timbers[i].placed;}
    return true;
}
static bool app_eng_named(void *user,const char *name,GeoCoord *out)
{const GeoNamedValue *v=geo_named_values_find(&((World *)user)->named_values,name);if(!v)return false;*out=v->value;return true;}
static bool app_eng_parameter(void *user,GeoParameterRef ref,GeoCoord *out,char *error,size_t cap)
{if(parameter_coord((World *)user,ref,out))return true;snprintf(error,cap,"%s",g_parameter_error);utf8_trim_tail(error);return false;}
static bool app_eng_owned(void *user,uint32_t id){return assembly_owned((World *)user,id);}
static void app_eng_write(void *user,const EngTarget *t,GeoCoord value)
{World *w=(World *)user;if(!t->kind){ReferenceGrid *g=world_find_grid_mut(w,t->id);if(t->field)g->axis[t->axis].gap=value;else g->axis[t->axis].body=value;}else{int i=reference_timber_index(w,t->id);if(t->field)w->timbers[i].size_b=value;else w->timbers[i].size_a=value;}}
static bool app_eng_serializable(void *user,char *error,size_t cap)
{(void)error;(void)cap;return engineering_serializable((World *)user);}
static WoodEngineeringContext app_eng_context(const World *world)
{World *w=(World *)world;WoodEngineeringContext c={&w->engineering,w,g_engineering_error,sizeof g_engineering_error,app_eng_placement,app_eng_target,app_eng_named,app_eng_parameter,app_eng_owned,app_eng_write,app_eng_serializable};c.versions=app_eng_version_store(w);return c;}
static bool eng_fail(const char *text)
{WoodEngineeringContext c={0};c.error=g_engineering_error;c.error_capacity=sizeof g_engineering_error;return wood_eng_fail(&c,text);}
static bool eng_id(const char *s)
{return wood_eng_id(s);}
static bool eng_u32(const GeoJson *j,int t,uint32_t *out,bool positive)
{return wood_eng_u32(j,t,out,positive);}
static bool eng_coord(const GeoJson *j,int t,Coord *out,bool positive)
{return wood_eng_coord(j,t,out,positive);}
static bool eng_optional_text(const GeoJson *j,int obj,const char *key)
{return wood_eng_optional_text(j,obj,key);}
static bool eng_ref_parse(GeoJson *j,int t,EngVersionRef *r,bool optional)
{return wood_eng_ref_parse(j,t,r,optional);}
static bool eng_axis(const GeoJson *j,int t,int *axis)
{return wood_eng_axis(j,t,axis);}
static const EngMaterialVersion *eng_material(const World *w,const char *id,uint32_t version)
{WoodEngineeringContext c=app_eng_context(w);return wood_eng_material(&c,id,version);}
static const EngMethodVersion *eng_method(const World *w,const char *id,uint32_t version)
{WoodEngineeringContext c=app_eng_context(w);return wood_eng_method(&c,id,version);}
static const EngMaterialVersion *eng_material_at(const World *w,size_t index)
{WoodEngineeringContext c=app_eng_context(w);return wood_eng_material_at(&c,index);}
static const EngMethodVersion *eng_method_at(const World *w,size_t index)
{WoodEngineeringContext c=app_eng_context(w);return wood_eng_method_at(&c,index);}
static EngApplication *eng_application(World *w,const char *id)
{WoodEngineeringContext c=app_eng_context(w);return wood_eng_application(&c,id);}
static bool eng_source_parse(GeoJson *j,int t,EngDimensionSource *s,bool allow_app)
{WoodEngineeringContext c={0};c.error=g_engineering_error;c.error_capacity=sizeof g_engineering_error;return wood_eng_source_parse(&c,j,t,s,allow_app);}
static bool eng_target_parse(GeoJson *j,int t,EngTarget *target)
{WoodEngineeringContext c={0};c.error=g_engineering_error;c.error_capacity=sizeof g_engineering_error;return wood_eng_target_parse(&c,j,t,target);}
static bool eng_same_target(const EngTarget *a,const EngTarget *b)
{return wood_eng_same_target(a,b);}
static EngBinding *eng_binding(World *w,const EngTarget *target)
{WoodEngineeringContext c=app_eng_context(w);return wood_eng_binding(&c,target);}
static bool eng_bind(World *w,const EngTarget *target,const EngDimensionSource *source)
{WoodEngineeringContext c=app_eng_context(w);return wood_eng_bind(&c,target,source);}
static bool eng_object_bound(const World *w,int kind,uint32_t id)
{WoodEngineeringContext c=app_eng_context(w);return wood_eng_object_bound(&c,kind,id);}
static bool engineering_used(const World *w)
{WoodEngineeringContext c=app_eng_context(w);return wood_engineering_used(&c);}
static bool eng_publish_material(World *w,GeoJson *j,int t,const char *fingerprint)
{WoodEngineeringContext c=app_eng_context(w);return wood_eng_publish_material(&c,j,t,fingerprint);}
static bool eng_publish_method(World *w,GeoJson *j,int t,const char *fingerprint)
{WoodEngineeringContext c=app_eng_context(w);return wood_eng_publish_method(&c,j,t,fingerprint);}
static bool eng_put_application(World *w,GeoJson *j,int t)
{WoodEngineeringContext c=app_eng_context(w);return wood_eng_put_application(&c,j,t);}
static bool eng_target_context(const World *w,const EngTarget *t,uint32_t *pid,int *role)
{WoodEngineeringContext c=app_eng_context(w);return wood_eng_target_context(&c,t,pid,role);}
static bool eng_resolve(World *w,const EngDimensionSource *s,const EngTarget *target,uint32_t pid,int role,Coord *value,char *path,size_t cap)
{WoodEngineeringContext c=app_eng_context(w);return wood_eng_resolve(&c,s,target,pid,role,value,path,cap);}
static bool eng_effective(World *w,const EngBinding *b,Coord *value,char *path,size_t cap)
{WoodEngineeringContext c=app_eng_context(w);return wood_eng_effective(&c,b,value,path,cap);}
static void engineering_drop_owned(World *w,const char *kind,uint32_t id)
{WoodEngineeringContext c=app_eng_context(w);wood_engineering_drop_owned(&c,kind,id);}
static bool engineering_follow_fragment(World *w,uint32_t old_pid)
{WoodEngineeringContext c=app_eng_context(w);return wood_engineering_follow_fragment(&c,old_pid);}
static bool engineering_rebuild(World *w,char *error,size_t cap)
{WoodEngineeringContext c=app_eng_context(w);return wood_engineering_rebuild(&c,error,cap);}
static bool eng_source_json(const EngDimensionSource *s,char *out,size_t cap)
{
    char q[600]; int n;
    if (s->kind==ENG_LITERAL) n=snprintf(out,cap,"{\"kind\":\"literal\",\"value\":%lld}",(long long)s->value);
    else if(s->kind==ENG_PARAMETER)n=snprintf(out,cap,"{\"kind\":\"parameter\",\"parameterId\":%u,\"fieldId\":%u}",s->parameter.parameter_id,s->parameter.field_id);
    else if (s->kind==ENG_SPEC) { if (!geo_json_quote(s->ref,q,sizeof q)) return false; n=snprintf(out,cap,"{\"kind\":\"spec\",\"name\":%s}",q); }
    else { if (!geo_json_quote(s->ref,q,sizeof q)) return false; if (s->kind==ENG_MATERIAL) n=snprintf(out,cap,"{\"field\":\"%s\",\"id\":%s,\"kind\":\"material\",\"version\":%u}",ENG_FIELDS[s->field],q,s->version); else n=snprintf(out,cap,"{\"field\":\"%s\",\"id\":%s,\"kind\":\"application\"}",ENG_FIELDS[s->field],q); }
    return n>=0&&(size_t)n<cap;
}
static void eng_target_json(const EngTarget *t,FILE *out)
{
    if (!t->kind) fprintf(out,"{\"axis\":\"%c\",\"field\":\"%s\",\"id\":%u,\"kind\":\"grid\"}",t->axis?'v':'u',t->field?"gap":"panel",t->id);
    else fprintf(out,"{\"field\":\"%s\",\"id\":%u,\"kind\":\"timber\"}",t->field?"B":"A",t->id);
}
typedef struct { char text[1450]; size_t size; bool ok; } EngBuffer;
static void eng_append(EngBuffer *b,const char *format,...)
{
    if(!b->ok)return;va_list args;va_start(args,format);int n=vsnprintf(b->text+b->size,sizeof b->text-b->size,format,args);va_end(args);
    if(n<0||(size_t)n>=sizeof b->text-b->size)b->ok=false;else b->size+=(size_t)n;
}
static void eng_dimension_json(const World *w,const EngTarget *t,Coord direct,EngBuffer *out)
{
    const EngBinding *b=NULL;for(size_t i=0;i<w->engineering.binding_count;++i)if(eng_same_target(t,&w->engineering.bindings[i].target)){b=&w->engineering.bindings[i];break;}
    if(!b){eng_append(out,"%lld",(long long)direct);return;}
    char source[640],override[640];if(!eng_source_json(&b->source,source,sizeof source)){out->ok=false;return;}
    if(b->has_override){if(!eng_source_json(&b->override_value,override,sizeof override)){out->ok=false;return;}}else snprintf(override,sizeof override,"null");
    eng_append(out,"{\"override\":%s,\"source\":%s}",override,source);
}
static bool eng_grid_content(const World *w,const ReferenceGrid *g,EngBuffer *b)
{
    memset(b,0,sizeof *b);b->ok=true;eng_append(b,"{\"axes\":{");
    for(int axis=0;axis<2;++axis){const GridAxisDef *d=&g->axis[axis];eng_append(b,"%s\"%c\":",axis?",":"",axis?'v':'u');
        if(d->source==GRID_SRC_NONE){eng_append(b,"null");continue;}
        if(d->source==GRID_SRC_PANEL){eng_append(b,"{\"anchor\":%lld,\"gap\":",(long long)d->anchor);EngTarget gap={0,g->id,axis,1},panel={0,g->id,axis,0};eng_dimension_json(w,&gap,d->gap,b);eng_append(b,",\"kind\":\"panel\",\"panel\":");eng_dimension_json(w,&panel,d->body,b);eng_append(b,"}");}
        else if(d->source==GRID_SRC_SERIES)eng_append(b,"{\"count\":%u,\"kind\":\"series\",\"start\":%lld,\"step\":%lld}",(unsigned)d->series_count,(long long)d->start,(long long)d->step);
        else{eng_append(b,"{\"coords\":[");for(size_t k=0;k<d->count;++k)eng_append(b,"%s%lld",k?",":"",(long long)d->coords[k]);eng_append(b,"],\"kind\":\"explicit\"}");}
    }
    eng_append(b,"},\"id\":%u,\"mainAlong\":",g->id);if(g->main_along)eng_append(b,"\"%c\"",g->main_along==1?'u':'v');else eng_append(b,"null");eng_append(b,",\"placement_id\":%u}",g->placement_id);return b->ok;
}
static bool eng_timber_content(const World *w,const Timber *t,EngBuffer *b)
{
    memset(b,0,sizeof *b);b->ok=true;EngTarget a={1,t->id,0,0},z={1,t->id,0,1};eng_append(b,"{\"A\":");eng_dimension_json(w,&a,t->size_a,b);eng_append(b,",\"B\":");eng_dimension_json(w,&z,t->size_b,b);eng_append(b,",\"id\":%u",t->id);if(t->role==TIMBER_ROLE_CUSTOM)eng_append(b,",\"priority\":%lld",(long long)t->cut_priority);eng_append(b,",\"role\":\"%s\"}",timber_role_name(t->role));return b->ok;
}
static bool engineering_serializable(const World *w)
{
    EngBuffer b;
    for(size_t i=0;i<w->grid_count;++i)if(eng_object_bound(w,0,w->grids[i].id)&&!eng_grid_content(w,&w->grids[i],&b))return eng_fail("I10: bound grid definition exceeds scene record capacity");
    for(size_t i=0;i<w->timber_count;++i)if(eng_object_bound(w,1,w->timbers[i].id)&&!eng_timber_content(w,&w->timbers[i],&b))return eng_fail("I10: bound timber definition exceeds scene record capacity");
    return true;
}
static void eng_dump_record(FILE *out,const char *kind,const char *json)
{
    char encoded[1950];size_t n;if(!geo_base64_encode(json,strlen(json),encoded,sizeof encoded,&n)){fputs("requires engineering-record-capacity-error\n",out);return;}
    fprintf(out,"engineering %s %s\n",kind,encoded);
}
static void engineering_dump_versions(const World *w,FILE *out)
{
    if(!engineering_used(w))return;fputs("requires engineering-spec/1\n",out);char record[1200];
    for(size_t i=0;i<w->engineering.material_count;++i){const EngMaterialVersion *m=eng_material_at(w,i);if(!m){fputs("requires engineering-version-storage-error\n",out);continue;}snprintf(record,sizeof record,"{\"fingerprint\":\"%s\",\"value\":%s}",m->fingerprint,m->content);eng_dump_record(out,"material",record);}
    for(size_t i=0;i<w->engineering.method_count;++i){const EngMethodVersion *m=eng_method_at(w,i);if(!m){fputs("requires engineering-version-storage-error\n",out);continue;}snprintf(record,sizeof record,"{\"fingerprint\":\"%s\",\"value\":%s}",m->fingerprint,m->content);eng_dump_record(out,"method",record);}
    for(int kind=0;kind<2;++kind){size_t count=kind?w->engineering.method_count:w->engineering.material_count;for(size_t i=0;i<count;++i){bool archived=kind?w->engineering.methods[i].archived:w->engineering.materials[i].archived;const EngVersionRef *r=kind?&w->engineering.methods[i].ref:&w->engineering.materials[i].ref;if(archived){snprintf(record,sizeof record,"{\"id\":\"%s\",\"kind\":\"%s\",\"op\":\"archive\",\"value\":true,\"version\":%u}",r->id,kind?"method":"material",r->version);eng_dump_record(out,"archive",record);}}}
}
static void engineering_dump_applications(const World *w,FILE *out)
{
    for(size_t i=0;i<w->engineering.application_count;++i)eng_dump_record(out,"application",w->engineering.applications[i].content);
}
static bool engineering_dump_grid(const World *w,const ReferenceGrid *g,FILE *out)
{
    if(!eng_object_bound(w,0,g->id))return false;EngBuffer b;if(eng_grid_content(w,g,&b))eng_dump_record(out,"grid",b.text);else fputs("requires engineering-record-capacity-error\n",out);return true;
}
static bool engineering_dump_timber(const World *w,const Timber *t,FILE *out)
{
    if(!eng_object_bound(w,1,t->id))return false;EngBuffer b;if(eng_timber_content(w,t,&b))eng_dump_record(out,"timber",b.text);else fputs("requires engineering-record-capacity-error\n",out);return true;
}
