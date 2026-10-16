/* F1a: a disposable typed read index. Never invokes a preview or evaluates live World. */
#include <stdarg.h>
#define SI_NODE_MAX 2048
#define SI_EDGE_MAX 8192
#define SI_TEXT_MAX 32768
typedef struct { char key[240],kind[32],id[100],label[200],definition[65],value[65]; uint32_t version,field; } SiNode;
typedef struct { char from[240],to[240],relation[32],field[100]; bool active; } SiEdge;
typedef struct { SiNode nodes[SI_NODE_MAX]; SiEdge edges[SI_EDGE_MAX]; size_t nn,ne; bool complete; char text[SI_TEXT_MAX]; size_t used; } SiIndex;
static void si_reset(SiIndex *s) {s->used=0;s->text[0]=0;}
#if defined(__GNUC__)
__attribute__((format(printf,2,3)))
#endif
static void si_text(SiIndex *s,const char *format,...)
{
    va_list a;va_start(a,format);int n=vsnprintf(s->text+s->used,sizeof s->text-s->used,format,a);va_end(a);
    if(n<0 || (size_t)n>=sizeof s->text-s->used){s->complete=false;return;}s->used+=(size_t)n;
}
static void si_key(char out[240],const char *kind,const char *id,uint32_t version,uint32_t field)
{snprintf(out,240,"%s:%s",kind,id);size_t n=strlen(out);if(version)snprintf(out+n,240-n,":v%u",version);n=strlen(out);if(field||!strcmp(kind,"parameter-field"))snprintf(out+n,240-n,":f%u",field);}
static void si_numkey(char out[240],const char *kind,uint32_t id,uint32_t version,uint32_t field)
{char number[32];snprintf(number,sizeof number,"%u",id);si_key(out,kind,number,version,field);}
static SiNode *si_node(SiIndex *s,const char *kind,const char *id,uint32_t version,uint32_t field,const char *label)
{
    if(s->nn==SI_NODE_MAX){s->complete=false;return NULL;}SiNode *n=&s->nodes[s->nn++];
    si_key(n->key,kind,id,version,field);snprintf(n->kind,sizeof n->kind,"%s",kind);snprintf(n->id,sizeof n->id,"%s",id);
    n->version=version;n->field=field;snprintf(n->label,sizeof n->label,"%s",label?label:kind);geo_sha256(s->text,s->used,n->definition);snprintf(n->value,65,"%s",n->definition);return n;
}
static SiNode *si_nnode(SiIndex *s,const char *kind,uint32_t id,uint32_t version,uint32_t field,const char *label)
{char number[32];snprintf(number,sizeof number,"%u",id);return si_node(s,kind,number,version,field,label);}
static void si_value(SiIndex *s,SiNode *n){if(n)geo_sha256(s->text,s->used,n->value);}
static void si_edge(SiIndex *s,const char *from,const char *to,const char *relation,const char *field,bool active)
{
    for(size_t i=0;i<s->ne;++i){SiEdge *e=&s->edges[i];if(!strcmp(e->from,from)&&!strcmp(e->to,to)&&!strcmp(e->relation,relation)&&!strcmp(e->field,field?field:"")&&e->active==active)return;}
    if(s->ne==SI_EDGE_MAX){s->complete=false;return;}SiEdge *e=&s->edges[s->ne++];
    snprintf(e->from,sizeof e->from,"%s",from);snprintf(e->to,sizeof e->to,"%s",to);snprintf(e->relation,sizeof e->relation,"%s",relation);snprintf(e->field,sizeof e->field,"%s",field?field:"");e->active=active;
}
static void si_ref(SiIndex *s,const char *from,const char *kind,uint32_t id,uint32_t version,uint32_t field,const char *relation,const char *detail)
{char key[240];si_numkey(key,kind,id,version,field);si_edge(s,from,key,relation,detail,true);}
static void si_source(SiIndex *s,const char *from,const EngDimensionSource *src,const char *field,bool active)
{
    char key[240];const char *relation="dimension";
    if(src->kind==ENG_LITERAL)return;
    if(src->kind==ENG_PARAMETER)si_numkey(key,"parameter-field",src->parameter.parameter_id,0,src->parameter.field_id);
    else if(src->kind==ENG_MATERIAL){si_key(key,"material",src->ref,src->version,0);relation="material-version";}
    else if(src->kind==ENG_APPLICATION)si_key(key,"application-field",src->ref,0,(uint32_t)src->field);
    else si_key(key,"spec",src->ref,0,0);
    char detail[100];snprintf(detail,sizeof detail,"%s%s%s",field?field:"",(src->kind==ENG_MATERIAL||src->kind==ENG_APPLICATION)?" ← ":"",(src->kind==ENG_MATERIAL||src->kind==ENG_APPLICATION)?ENG_FIELDS[src->field]:"");
    si_edge(s,from,key,relation,detail,active);
}
static void si_ast(SiIndex *s,const char *from,GeoJson *j,int token,const char *field)
{
    if(!geo_json_is_object(j,token))return;char op[16];if(!geo_json_string(j,geo_json_member(j,token,"op"),op,sizeof op))return;
    if(!strcmp(op,"ref")){uint32_t card=0,f=0;if(parameter_u32(j,geo_json_member(j,token,"parameterId"),&card)&&parameter_u32(j,geo_json_member(j,token,"fieldId"),&f))si_ref(s,from,"parameter-field",card,0,f,"dimension",field);}
    else {si_ast(s,from,j,geo_json_member(j,token,"left"),field);si_ast(s,from,j,geo_json_member(j,token,"right"),field);}
}
/* Parse the core's validated D6a quantity grammar, never a diagnostic/label/path. */
static void si_expression(SiIndex *s,const char *from,const char *expression,uint32_t surface,bool local)
{
    const char *p=expression;while(*p){if(*p=='+'||*p=='-')++p;const char *end=p;
        while(*end){if((*end=='+'||*end=='-')&&!(end>p&&end[-1]==':'&&isdigit((unsigned char)end[1])))break;++end;}
        size_t length=(size_t)(end-p);if(!length||length>=REF_EXPR_MAX){s->complete=false;return;}
        char term[REF_EXPR_MAX];memcpy(term,p,length);term[length]=0;char *q=strchr(term,'*');q=q?q+1:term;
        if(local && !strncmp(q,"gridrule:",9)){
            GridRuleLineRef r={0};
            if(grid_rule_ref_text(q,&r)){si_ref(s,from,"grid",r.grid_id,0,0,"position","rule-line");si_ref(s,from,"grid-system",r.system_id,0,0,"position","rule-source");}
            else s->complete=false;
            p=end;continue;
        }
        char *parts[5];int count=0;while(count<5){parts[count++]=q;char *colon=strchr(q,':');if(!colon)break;*colon=0;q=colon+1;}
        uint32_t id=0,field=0;char key[240];
        if(count==2&&!strcmp(parts[0],"spec")){si_key(key,"spec",parts[1],0,0);si_edge(s,from,key,"dimension","expression",true);}
        else if(count==3&&!strcmp(parts[0],"param")&&parse_u32(parts[1],&id)&&parse_u32(parts[2],&field))si_ref(s,from,"parameter-field",id,0,field,"dimension","expression");
        else if(local&&count>=2&&parse_u32(parts[1],&id)&&(!strcmp(parts[0],"guide")||!strcmp(parts[0],"grid")||!strcmp(parts[0],"timber")||!strcmp(parts[0],"panel")||!strcmp(parts[0],"gap")))si_ref(s,from,(!strcmp(parts[0],"panel")||!strcmp(parts[0],"gap"))?"grid":parts[0],id,0,0,"position","expression");
        else if(local&&count>=2&&(!strcmp(parts[0],"edge")||!strcmp(parts[0],"vertex")))si_ref(s,from,"placement",surface,0,0,"position",expression);
        else s->complete=false;p=end;
    }
}
static void si_axis(SiIndex *s,const char *from,const GridAxisDef *d,const char *axis,const bool *bound)
{
    si_text(s,"axis:%s:%d:",axis,d->source);
    Coord values[6]={d->start,d->step,d->body,d->gap,d->anchor,d->stagger};const char *names[6]={"phase","step","panel","gap","anchor","stagger"};
    for(int k=0;k<6;++k){const ParameterRef *r=&d->parameters[k];if(bound&&bound[k])si_text(s,"engineering-bound;");else if(r->set){si_text(s,"p%u:%u;",r->parameter_id,r->field_id);char field[80];snprintf(field,sizeof field,"%s.%s",axis,names[k]);si_ref(s,from,"parameter-field",r->parameter_id,0,r->field_id,"dimension",field);}else si_text(s,"%lld;",(long long)values[k]);}
    si_text(s,"%zu:%d:",d->series_count,d->stagger_set);if(d->source==GRID_SRC_EXPLICIT){si_text(s,"%zu:",d->count);for(size_t k=0;k<d->count;++k)si_text(s,"%lld,",(long long)d->coords[k]);}
}
static void si_axis_value(SiIndex *s,const GridAxisDef *d)
{si_text(s,"%lld:%lld:%lld:%lld:%lld:%lld:%zu:",(long long)d->start,(long long)d->step,(long long)d->body,(long long)d->gap,(long long)d->anchor,(long long)d->stagger,d->count);for(size_t k=0;k<d->count;++k)si_text(s,"%lld,",(long long)d->coords[k]);}
static void si_subdivision(SiIndex *s,const GridSystem *g)
{
    if(!g->rule_count && g->next_rule_key==1)return;
    si_text(s,"rules:%u:%zu;",g->next_rule_key,g->rule_count);
    for(size_t i=0;i<g->rule_count;++i){const GridSubdivisionRule *r=&g->rules[i];
        si_text(s,"%u:%zu:%s:%d:%lld:%lld:%u:%u;",r->key,strlen(r->name),r->name,r->all_cells,
            (long long)r->cell[0],(long long)r->cell[1],r->divisions[0],r->divisions[1]);
    }
}
static void si_vector(SiIndex *s,Vector3 v){si_text(s,"%lld,%lld,%lld;",(long long)v.x,(long long)v.y,(long long)v.z);}
static void si_point(SiIndex *s,Point3 v){si_text(s,"%lld,%lld,%lld;",(long long)v.x,(long long)v.y,(long long)v.z);}
static void si_loop(SiIndex *s,const PolygonLoop2 *loop)
{si_text(s,"loop%zu:",loop->count);for(size_t k=0;k<loop->count;++k)si_text(s,"%lld,%lld,%d;",(long long)loop->v[k].u,(long long)loop->v[k].v,loop->fixity[k]);}
static void si_content(SiIndex *s,const char *content,const char *exclude)
{
    GeoJson j;if(!app_json_parse(&j,content)){s->complete=false;geo_json_free(&j);return;}
    GeoJsonKey *keys=geo_json_sorted_keys(&j,0);if(j.tokens[0].size&&!keys)s->complete=false;
    if(keys)for(int k=0;k<j.tokens[0].size;++k){if(geo_json_csv_has(exclude,keys[k].key))continue;char value[ASM_RECORD_MAX];if(!geo_json_canonical(&j,keys[k].token+1,value,sizeof value)){s->complete=false;break;}si_text(s,"%s=%s;",keys[k].key,value);}free(keys);geo_json_free(&j);
}
static void si_binding_sources(SiIndex *s,const char *from,const char *content)
{
    GeoJson j;if(!app_json_parse(&j,content)){s->complete=false;geo_json_free(&j);return;}int slots=geo_json_member(&j,0,"slots");
    for(int k=0;k<geo_json_size(&j,slots);++k){int slot=geo_json_at(&j,slots,k);int64_t id=0;geo_json_integer(&j,geo_json_member(&j,slot,"slotId"),&id);
        for(int a=0;a<2;++a){int token=geo_json_member(&j,slot,a?"B":"A");if(geo_json_is_null(&j,token))continue;EngDimensionSource src;if(eng_source_parse(&j,token,&src,false)){char field[60];snprintf(field,sizeof field,"slot:%lld.%c",(long long)id,a?'B':'A');si_source(s,from,&src,field,true);}else s->complete=false;}}
    geo_json_free(&j);
}
static const char *si_name(const char *content,char name[200],const char *fallback)
{GeoJson j;if(app_json_parse(&j,content)&&geo_json_string(&j,geo_json_member(&j,0,"name"),name,200)){geo_json_free(&j);return name;}geo_json_free(&j);return fallback;}
/* Native typed resolution path per application field, not every unrelated override. */
static void si_application_fields(SiIndex *s,const World *w,const EngApplication *a)
{
    const EngMethodVersion *m=eng_method(w,a->method.id,a->method.version);if(!m){s->complete=false;return;}
    for(int field=ENG_U_PANEL;field<=ENG_SECONDARY_B;++field){EngDimensionSource nested={0};int override=-1,axis=-1;bool set=true;
        if(field==ENG_U_GAP||field==ENG_V_GAP){override=0;nested.value=m->gap;set=a->overridden[0]||m->has_gap;}
        else if(field==ENG_U_PANEL||field==ENG_V_PANEL){axis=a->long_axis?a->long_axis:m->long_axis;set=axis&&m->panel.id[0];nested.kind=ENG_MATERIAL;snprintf(nested.ref,sizeof nested.ref,"%s",m->panel.id);nested.version=m->panel.version;nested.field=axis==field-ENG_U_PANEL+1?ENG_LENGTH:ENG_WIDTH;}
        else {int role=(field-ENG_BOUNDARY_A)/2,dim=(field-ENG_BOUNDARY_A)%2;override=1+role*2+dim;set=a->overridden[override]||m->roles[role].id[0];nested.kind=ENG_MATERIAL;snprintf(nested.ref,sizeof nested.ref,"%s",m->roles[role].id);nested.version=m->roles[role].version;nested.field=dim?ENG_B:ENG_A;}
        if(override>=0&&a->overridden[override])nested=a->overrides[override];
        char from[240],root[240],method[240],source[640];si_key(from,"application-field",a->id,0,(uint32_t)field);si_key(root,"application",a->id,0,0);si_key(method,"method",m->ref.id,m->ref.version,0);
        si_reset(s);si_text(s,"%u:%s:%u:%d:%d:%d;",a->placement_id,m->ref.id,m->ref.version,field,axis,set);if(set){eng_source_json(&nested,source,sizeof source);si_text(s,"%s",source);}SiNode *n=si_node(s,"application-field",a->id,0,(uint32_t)field,ENG_FIELDS[field]);
        si_reset(s);Coord effective=0;bool known=set;if(nested.kind==ENG_LITERAL)effective=nested.value;else if(nested.kind==ENG_PARAMETER)known=set&&parameter_coord(w,nested.parameter,&effective);else if(nested.kind==ENG_MATERIAL){const EngMaterialVersion *material=eng_material(w,nested.ref,nested.version);if(material)effective=nested.field==ENG_WIDTH?material->width:nested.field==ENG_LENGTH?material->length:nested.field==ENG_A?material->a:material->b;else known=false;}else if(nested.kind==ENG_SPEC){size_t at=0;while(at<geo_named_values_count(&w->named_values)&&strcmp(geo_named_values_at(&w->named_values,at)->name,nested.ref))++at;if(at<geo_named_values_count(&w->named_values))effective=geo_named_values_at(&w->named_values,at)->value;else known=false;}else known=false;si_text(s,"%d:%lld",known,(long long)effective);si_value(s,n);
        si_edge(s,root,from,"member",ENG_FIELDS[field],true);si_edge(s,from,method,"rule-version","fixed method",true);si_ref(s,from,"placement",a->placement_id,0,0,"position","surface");if(set)si_source(s,from,&nested,ENG_FIELDS[field],true);
    }
}
static void si_rule_parts(SiIndex *s,const AsmRuleVersion *r)
{
    GeoJson j;if(!app_json_parse(&j,r->content)){s->complete=false;geo_json_free(&j);return;}char root[240];si_numkey(root,"assembly-rule",r->id,r->version,0);
    const char *parts[2]={"members","joints"};for(int kind=0;kind<2;++kind){int list=geo_json_member(&j,0,parts[kind]);for(int k=0;k<geo_json_size(&j,list);++k){int at=geo_json_at(&j,list,k);int64_t id=0;if(!geo_json_integer(&j,geo_json_member(&j,at,"id"),&id)){s->complete=false;continue;}char text[ASM_RECORD_MAX],key[240],label[100];if(!geo_json_canonical(&j,at,text,sizeof text)){s->complete=false;continue;}const char *type=kind?"assembly-joint":"assembly-member";si_numkey(key,type,r->id,r->version,(uint32_t)id);si_reset(s);si_text(s,"%s",text);snprintf(label,sizeof label,"%s #%lld",kind?"接合定義":"規則構件",(long long)id);si_nnode(s,type,r->id,r->version,(uint32_t)id,label);si_edge(s,root,key,kind?"joint-definition":"member",parts[kind],true);}}
    geo_json_free(&j);
}
#include "section_profile_source_index.inc"
static SiIndex *si_build(const World *w)
{
    SiIndex *s=calloc(1,sizeof *s);if(!s)return NULL;s->complete=true;char from[240],label[200];SiNode *n;
    for(size_t i=0;i<world_boundary_count(w);++i){const SpaceBoundarySurface *b=world_boundary_at(w,i);si_reset(s);si_text(s,"%d;",b->kind);si_loop(s,&b->outline);for(size_t k=0;k<b->hole_count;++k)si_loop(s,&b->holes[k]);
        const BoundaryVertexKeys *keys=world_find_vertex_keys(w,b->id);if(keys){for(size_t k=0;k<keys->loop_count;++k)for(size_t v=0;v<keys->counts[k];++v)si_text(s,"key:%zu:%zu:%u;",k,v,keys->keys[k][v]);}
        si_nnode(s,"boundary",b->id,0,0,"邊界");}
    for(size_t i=0;i<world_placement_count(w);++i){const PlacementSurface *p=world_placement_at(w,i);si_numkey(from,"placement",p->id,0,0);si_reset(s);si_text(s,"boundary%u;",p->boundary_id);si_point(s,p->frame.origin);si_vector(s,p->frame.axis_u);si_vector(s,p->frame.axis_v);si_vector(s,p->frame.normal);
        if(!p->boundary_id){PolygonLoop2 loop;placement_outline(p,NULL,&loop);si_loop(s,&loop);}else si_ref(s,from,"boundary",p->boundary_id,0,0,"position","boundary");si_nnode(s,"placement",p->id,0,0,"承載面");}
    for(size_t i=0;i<w->space_count;++i){const Space *v=&w->spaces[i];si_numkey(from,"space",v->id,0,0);si_reset(s);for(size_t k=0;k<v->boundary_count;++k){si_text(s,"%u;",v->boundaries[k]);si_ref(s,from,"boundary",v->boundaries[k],0,0,"member","boundary");for(size_t j=0;j<world_placement_count(w);++j)if(world_placement_at(w,j)->boundary_id==v->boundaries[k])si_ref(s,from,"placement",world_placement_at(w,j)->id,0,0,"position","member-placement");}si_nnode(s,"space",v->id,0,0,"空間");}
    for(size_t i=0;i<w->column_count;++i){const RcColumn *v=&w->columns[i];si_numkey(from,"column",v->id,0,0);si_reset(s);si_text(s,"%u:%lld:%lld:%lld:%lld:%lld:%lld",v->space_id,(long long)v->x_lo,(long long)v->x_hi,(long long)v->y_lo,(long long)v->y_hi,(long long)v->z_lo,(long long)v->z_hi);si_nnode(s,"column",v->id,0,0,"柱");if(v->space_id)si_ref(s,from,"space",v->space_id,0,0,"member","membership");}
    for(size_t i=0;i<w->beam_count;++i){const RcBeam *v=&w->beams[i];si_numkey(from,"beam",v->id,0,0);si_reset(s);si_text(s,"%u:%d:%lld:%lld:%lld:%lld:%lld:%lld",v->space_id,v->axis,(long long)v->x_lo,(long long)v->x_hi,(long long)v->y_lo,(long long)v->y_hi,(long long)v->z_lo,(long long)v->z_hi);si_nnode(s,"beam",v->id,0,0,"樑");if(v->space_id)si_ref(s,from,"space",v->space_id,0,0,"member","membership");}
    for(size_t i=0;i<geo_named_values_count(&w->named_values);++i){const SpecValue *v=geo_named_values_at(&w->named_values,i);si_reset(s);si_text(s,"%lld",(long long)v->value);si_node(s,"spec",v->name,0,0,v->name);}
    for(size_t i=0;i<geo_parameters_card_count(&w->parameters);++i){const ParameterSet *c=&geo_parameters_cards(&w->parameters)[i];si_numkey(from,"parameter",c->id,0,0);si_reset(s);si_text(s,"card%u",c->id);si_nnode(s,"parameter",c->id,0,0,c->name);
        for(size_t k=0;k<c->count;++k)si_ref(s,from,"parameter-field",c->id,0,c->fields[k],"member","field");}
    for(size_t i=0;i<geo_parameters_field_count(&w->parameters);++i){const ParameterField *f=&geo_parameters_fields(&w->parameters)[i];si_numkey(from,"parameter-field",f->parameter_id,0,f->id);si_reset(s);si_text(s,"%d:%s",f->type,f->expression);snprintf(label,sizeof label,"%s.%s",parameter_find(w,f->parameter_id)->name,f->name);n=si_nnode(s,"parameter-field",f->parameter_id,0,f->id,label);
        si_reset(s);si_text(s,"%lld/%lld:%d",(long long)f->value.num,(long long)f->value.den,f->value.unit);si_value(s,n);GeoJson j;if(app_json_parse(&j,f->expression))si_ast(s,from,&j,0,"expression");else s->complete=false;geo_json_free(&j);}
    for(size_t i=0;i<geo_datums_count(&w->datum_planes);++i){const GeoDatum *d=geo_datums_at(&w->datum_planes,i);si_numkey(from,"datum",d->id,0,0);si_reset(s);si_text(s,"%d:%s",d->axis,app_datum_expression(w,d->id));n=si_nnode(s,"datum",d->id,0,0,"共用基準");si_reset(s);si_text(s,"%d:%lld",d->axis,(long long)d->position);si_value(s,n);si_expression(s,from,app_datum_expression(w,d->id),0,false);}
    for(size_t i=0;i<geo_guides_count(&w->guide_lines);++i){const GuideLine *g=&geo_guides_values(&w->guide_lines)[i];si_numkey(from,"guide",g->id,0,0);si_reset(s);si_text(s,"%u:%d:%u:%d:%s",g->placement_id,g->source,g->datum_id,g->source==GUIDE_DATUM?0:g->direction,app_guide_expression(w,g->id));n=si_nnode(s,"guide",g->id,0,0,"參考線");si_reset(s);si_text(s,"%d:%lld",g->direction,(long long)g->offset);si_value(s,n);si_ref(s,from,"placement",g->placement_id,0,0,"position","surface");if(g->source==GUIDE_DATUM)si_ref(s,from,"datum",g->datum_id,0,0,"position","datum");else si_expression(s,from,app_guide_expression(w,g->id),g->placement_id,true);}
    for(size_t i=0;i<geo_grid_systems_count(&w->grid_store);++i){const GridSystem *g=geo_grid_systems_at(&w->grid_store,i);si_numkey(from,"grid-system",g->id,0,0);si_reset(s);si_text(s,"%d;",app_grid_system_main_along(w,g->id));si_axis(s,from,&g->axis[0],"u",NULL);si_axis(s,from,&g->axis[1],"v",NULL);si_subdivision(s,g);n=si_nnode(s,"grid-system",g->id,0,0,g->name);si_reset(s);si_axis_value(s,&g->axis[0]);si_axis_value(s,&g->axis[1]);si_subdivision(s,g);si_value(s,n);}
    for(size_t i=0;i<geo_grid_bindings_count(&w->grid_store);++i){const GridBinding *b=geo_grid_bindings_at(&w->grid_store,i);si_numkey(from,"grid-binding",b->id,0,0);si_reset(s);si_text(s,"%u:%u:%u:%lld:%lld:%u/%u:%u/%u",b->boundary_id,b->system_id,b->vertex_key,(long long)b->cell[0],(long long)b->cell[1],b->anchor_num[0],b->anchor_den[0],b->anchor_num[1],b->anchor_den[1]);si_nnode(s,"grid-binding",b->id,0,0,"網格配置");si_ref(s,from,"boundary",b->boundary_id,0,0,"position","vertex");si_ref(s,from,"grid-system",b->system_id,0,0,"position","system");}
    for(size_t i=0;i<w->grid_count;++i){const ReferenceGrid *g=&w->grids[i];bool bound[2][6]={{false}};for(size_t k=0;k<w->engineering.binding_count;++k){const EngBinding *b=&w->engineering.bindings[k];if(b->target.kind==0&&b->target.id==g->id)bound[b->target.axis][2+b->target.field]=true;}
        si_numkey(from,"grid",g->id,0,0);si_reset(s);si_text(s,"%u:%d:%d:%d;",g->placement_id,g->main_along,g->is_subgrid,g->from_binding);si_axis(s,from,&g->axis[0],"u",bound[0]);si_axis(s,from,&g->axis[1],"v",bound[1]);
        if(g->is_subgrid){si_text(s,"%u:%d:%lld:%lld:%d:%d:%d:%d:%u:%u",g->parent_id,g->lattice_cell,(long long)g->lattice_cell_index[0],(long long)g->lattice_cell_index[1],g->cell_ref[0][0],g->cell_ref[0][1],g->cell_ref[1][0],g->cell_ref[1][1],g->divisions[0],g->divisions[1]);si_ref(s,from,"grid",g->parent_id,0,0,"position","parent");}
        if(g->from_binding){si_text(s,"binding%u",g->binding_id);si_ref(s,from,"grid-binding",g->binding_id,0,0,"position","binding");}else if(g->from_system){si_text(s,"system%u:%lld:%lld",g->system_id,(long long)g->system_origin[0],(long long)g->system_origin[1]);si_ref(s,from,"grid-system",g->system_id,0,0,"position","system");}
        for(size_t k=0;k<w->engineering.binding_count;++k){const EngBinding *b=&w->engineering.bindings[k];if(b->target.kind!=0||b->target.id!=g->id)continue;char src[640],over[640];eng_source_json(&b->source,src,sizeof src);if(b->has_override)eng_source_json(&b->override_value,over,sizeof over);else snprintf(over,sizeof over,"null");si_text(s,"binding:%d:%d:%s:%s;",b->target.axis,b->target.field,src,over);}
        n=si_nnode(s,"grid",g->id,0,0,"面內網格");si_reset(s);si_axis_value(s,&g->axis[0]);si_axis_value(s,&g->axis[1]);si_value(s,n);si_ref(s,from,"placement",g->placement_id,0,0,"position","surface");}
    for(size_t i=0;i<w->engineering.material_count;++i){const EngMaterialVersion *m=&w->engineering.materials[i];si_reset(s);si_text(s,"%s",m->fingerprint);n=si_node(s,"material",m->ref.id,m->ref.version,0,si_name(m->content,label,m->ref.id));if(n)snprintf(n->definition,65,"%s",m->fingerprint);si_reset(s);si_text(s,"%d:%lld:%lld:%lld:%lld",m->kind,(long long)m->width,(long long)m->length,(long long)m->a,(long long)m->b);si_value(s,n);}
    for(size_t i=0;i<w->engineering.method_count;++i){const EngMethodVersion *m=&w->engineering.methods[i];si_key(from,"method",m->ref.id,m->ref.version,0);si_reset(s);si_text(s,"%s",m->fingerprint);n=si_node(s,"method",m->ref.id,m->ref.version,0,si_name(m->content,label,m->ref.id));if(n){snprintf(n->definition,65,"%s",m->fingerprint);snprintf(n->value,65,"%s",m->fingerprint);}EngVersionRef refs[4]={m->panel,m->roles[0],m->roles[1],m->roles[2]};for(int k=0;k<4;++k)if(refs[k].id[0]){char key[240];si_key(key,"material",refs[k].id,refs[k].version,0);si_edge(s,from,key,"material-version",k==0?"panel":k==1?"boundary":k==2?"primary":"secondary",true);}}
    for(size_t i=0;i<w->engineering.application_count;++i){const EngApplication *a=&w->engineering.applications[i];si_key(from,"application",a->id,0,0);si_reset(s);si_content(s,a->content,"anchorOptions");si_node(s,"application",a->id,0,0,a->id);char key[240];si_key(key,"method",a->method.id,a->method.version,0);si_edge(s,from,key,"rule-version","method",true);si_ref(s,from,"placement",a->placement_id,0,0,"position","surface");si_application_fields(s,w,a);}
    for(size_t i=0;i<w->timber_count;++i){const Timber *t=&w->timbers[i];const TimberAnchor *a=&w->anchors[i];bool bound[2]={false,false};for(size_t k=0;k<w->engineering.binding_count;++k){const EngBinding *b=&w->engineering.bindings[k];if(b->target.kind==1&&b->target.id==t->id)bound[b->target.field]=true;}
        si_numkey(from,"timber",t->id,0,0);si_reset(s);si_text(s,"%d:%lld:%lld:%lld:%u:%d:%d:%d:%d:%d:%lld:%d:%lld:%d:%lld:%d:%d;",t->role,(long long)t->cut_priority,(long long)(bound[0]?0:t->size_a),(long long)(bound[1]?0:t->size_b),a->placement_id,a->anchor_kind,a->length_direction,a->depth_side,a->ref_hole,a->ref_edge,(long long)a->ref_grid_index,a->ref_grid_axis,(long long)a->ref_grid_band,a->ref_grid_has_band,(long long)a->through,a->has_through,a->has_between);
        if(a->anchor_kind==ANCHOR_AT_RULE){const GridRuleLineRef *r=&a->ref_rule;
            si_text(s,"rule:%u:%u:%u:%lld:%lld:%d:%u;",r->grid_id,r->system_id,r->rule_key,
                (long long)r->cell[0],(long long)r->cell[1],r->axis,r->inner_index);
        }
        si_text(s,"refs:%u:%u:%d:%u;",a->ref_guide,a->ref_grid,a->ref_is_timber,a->ref_timber);if(a->anchor_kind==ANCHOR_AT)si_text(s,"uv:%lld:%lld;",(long long)a->uv.u,(long long)a->uv.v);
        for(int k=0;k<2;++k)if(a->has_between){const ReferenceFace *f=&a->between[k];si_text(s,"between:%d:%d:%d:%u;",f->kind,f->hole,f->edge,f->timber);if(f->kind)si_ref(s,from,"timber",f->timber,0,0,"position",k?"between.finish":"between.start");}
        for(size_t k=0;k<w->engineering.binding_count;++k){const EngBinding *b=&w->engineering.bindings[k];if(b->target.kind!=1||b->target.id!=t->id)continue;char src[640],over[640];eng_source_json(&b->source,src,sizeof src);if(b->has_override)eng_source_json(&b->override_value,over,sizeof over);else snprintf(over,sizeof over,"null");si_text(s,"%d:%s:%s;",b->target.field,src,over);si_source(s,from,&b->source,b->target.field?"B":"A",!b->has_override);if(b->has_override)si_source(s,from,&b->override_value,b->target.field?"B override":"A override",true);}
        n=si_nnode(s,"timber",t->id,0,0,"角材");si_reset(s);si_text(s,"%d:%lld:%lld:%lld;",t->placed,(long long)t->size_a,(long long)t->size_b,(long long)t->length);si_point(s,t->origin);si_vector(s,t->axis_length);si_vector(s,t->axis_a);si_vector(s,t->axis_b);si_value(s,n);
        if(t->placed){si_ref(s,from,"placement",a->placement_id,0,0,"position","surface");if(a->anchor_kind==ANCHOR_AT_LINE)si_ref(s,from,"guide",a->ref_guide,0,0,"position","anchor");if(a->anchor_kind==ANCHOR_AT_GRID)si_ref(s,from,"grid",a->ref_grid,0,0,"position","anchor");
        if(a->anchor_kind==ANCHOR_AT_RULE){si_ref(s,from,"grid",a->ref_rule.grid_id,0,0,"position","rule-line");si_ref(s,from,"grid-system",a->ref_rule.system_id,0,0,"position","rule-source");}if(a->ref_is_timber)si_ref(s,from,"timber",a->ref_timber,0,0,"position","anchor-face");
            for(size_t k=0;k<w->timber_count;++k)if(w->timbers[k].placed&&w->anchors[k].placement_id==a->placement_id&&w->anchors[k].order<a->order)si_ref(s,from,"timber",w->timbers[k].id,0,0,"span-candidate","I9 candidate, not confirmed support");}}
    for(size_t i=0;i<w->engineering.binding_count;++i){const EngBinding *b=&w->engineering.bindings[i];if(b->target.kind!=0)continue;si_numkey(from,"grid",b->target.id,0,0);char field[20];snprintf(field,sizeof field,"%c.%s",b->target.axis?'v':'u',b->target.field?"gap":"panel");si_source(s,from,&b->source,field,!b->has_override);if(b->has_override)si_source(s,from,&b->override_value,field,true);}
    for(size_t i=0;i<w->assembly.rule_count;++i){const AsmRuleVersion *r=&w->assembly.rules[i];si_reset(s);si_text(s,"%s",r->fingerprint);n=si_nnode(s,"assembly-rule",r->id,r->version,0,si_name(r->content,label,"組構規則"));if(n){snprintf(n->definition,65,"%s",r->fingerprint);snprintf(n->value,65,"%s",r->fingerprint);}si_rule_parts(s,r);}
    for(size_t i=0;i<w->assembly.binding_count;++i){const AsmBinding *b=&w->assembly.bindings[i];si_numkey(from,"assembly-binding",b->id,0,0);si_reset(s);si_content(s,b->content,"name");si_nnode(s,"assembly-binding",b->id,0,0,b->name);si_ref(s,from,"assembly-rule",b->rule_id,b->rule_version,0,"rule-version","rule");si_binding_sources(s,from,b->content);}
    for(size_t i=0;i<w->assembly.instance_count;++i){const AsmInstance *a=&w->assembly.instances[i];si_numkey(from,"assembly-instance",a->id,0,0);si_reset(s);si_content(s,a->content,"");si_nnode(s,"assembly-instance",a->id,0,0,a->name);si_ref(s,from,"assembly-binding",a->binding_id,0,0,"dimension","binding");si_ref(s,from,"assembly-rule",a->rule_id,a->rule_version,0,"rule-version",a->rule_hash);si_ref(s,from,"placement",a->surface_id,0,0,"position","surface");for(int k=0;k<3;++k){char key[240],detail[100];si_numkey(key,"timber",a->timber[k],0,0);snprintf(detail,sizeof detail,"member:%u",a->member[k]);si_edge(s,key,from,"member",detail,true);}}
    si_profile_sources(s,w);
    return s;
}
static void si_json(SiIndex *s,const World *w,bool live)
{
    char fingerprint[65];if(!eng_definition_hash(w,fingerprint)){eng_bridge_error("SOURCE_UNCHECKED","Cannot fingerprint readonly source World");return;}
    printf("{\"ok\":true,\"schema\":\"source-inspector/1\",\"revision\":%llu,\"live\":%s,\"complete\":%s,\"limits\":{\"nodes\":%d,\"edges\":%d},\"identityContinuity\":\"unknown\",\"supportStatus\":\"unknown\",\"nodes\":[",(unsigned long long)g_definition_revision,live?"true":"false",s->complete?"true":"false",SI_NODE_MAX,SI_EDGE_MAX);
    for(size_t i=0;i<s->nn;++i){SiNode *n=&s->nodes[i];if(i)putchar(',');fputs("{\"key\":",stdout);js_string(n->key);fputs(",\"kind\":",stdout);js_string(n->kind);fputs(",\"id\":",stdout);js_string(n->id);fputs(",\"label\":",stdout);js_string(n->label);printf(",\"version\":%u,\"fieldId\":%u,\"definitionFingerprint\":\"%s\",\"valueFingerprint\":\"%s\"",n->version,n->field,n->definition,n->value);
        if(!strcmp(n->kind,"timber")){uint32_t id=0;int at=parse_u32(n->id,&id)?reference_timber_index(w,id):-1;if(at>=0){const Timber *t=&w->timbers[at];const TimberAnchor *a=&w->anchors[at];bool along_v=a->length_direction==SURFACE_DIRECTION_POS_V||a->length_direction==SURFACE_DIRECTION_NEG_V;printf(",\"placed\":%s,\"surface\":%u,\"lengthAxis\":\"%c\",\"nativeOwner\":",t->placed?"true":"false",a->placement_id,along_v?'v':'u');json_schedule_support_owner(w,id);}}putchar('}');}
    fputs("],\"edges\":[",stdout);for(size_t i=0;i<s->ne;++i){SiEdge *e=&s->edges[i];if(i)putchar(',');fputs("{\"from\":",stdout);js_string(e->from);fputs(",\"to\":",stdout);js_string(e->to);fputs(",\"relation\":",stdout);js_string(e->relation);fputs(",\"field\":",stdout);js_string(e->field);printf(",\"active\":%s}",e->active?"true":"false");}printf("],\"sourceFingerprint\":\"%s\",\"timberSupports\":",fingerprint);json_timber_supports(w,fingerprint);
    if(!live){fputs(",\"timberReferences\":",stdout);json_references_world(w,fingerprint);}fputs("}\n",stdout);
}
static void cmd_source_inspect(void)
{SiIndex *s=si_build(&g_world);if(!s){eng_bridge_error("MEMORY","Cannot allocate readonly source index");return;}si_json(s,&g_world,true);free(s);}
static void cmd_source_inspect_file(const char *path)
{
    size_t length=0;char *text=eng_read_file(path,&length);if(!text){eng_bridge_error("INPUT","Cannot read bounded source snapshot");return;}bool encoded=!memchr(text,0,length)&&utf8_is_valid(text);free(text);if(!encoded){eng_bridge_error("ENCODING","Snapshot must be UTF-8 without NUL");return;}
    World *candidate=calloc(1,sizeof *candidate);ReferencePreview *saved=malloc(sizeof *saved);if(!candidate||!saved){free(candidate);free(saved);eng_bridge_error("MEMORY","Cannot allocate readonly source snapshot");return;}
    *saved=g_preview;uint32_t serial=g_preview_serial;uint64_t revision=g_definition_revision;const World *previous=g_subgrid_before;g_subgrid_before=NULL;
    bool ok=parse_scene_file(path,candidate);SiIndex *s=ok?si_build(candidate):NULL;
    g_preview=*saved;g_preview_serial=serial;g_definition_revision=revision;g_subgrid_before=previous;
    if(s){si_json(s,candidate,false);free(s);}else eng_bridge_error("SNAPSHOT_UNCHECKED","Cannot validate or index saved source snapshot");free(candidate);free(saved);
}
