#include "finish.h"
#include "section_profile.h"
#include "grid.h"
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void wood_fs_trim_tail(char *s)
{
    size_t len = strlen(s);
    size_t i = len;

    while (i > 0 && ((unsigned char)s[i - 1] & 0xC0) == 0x80) {
        --i;                             /* 跳過結尾的續位元組 10xxxxxx */
    }
    if (i == 0) {
        return;                          /* 全是續位元組:不是截斷造成的,留給輸出層 */
    }
    unsigned char lead = (unsigned char)s[i - 1];
    size_t need = lead < 0x80 ? 1
                : (lead & 0xE0) == 0xC0 ? 2
                : (lead & 0xF0) == 0xE0 ? 3
                : (lead & 0xF8) == 0xF0 ? 4 : 1;
    if (len - (i - 1) < need) {
        s[i - 1] = '\0';                 /* 起始位元組後面的續位元組不夠:整個序列拿掉 */
    }
}
bool wood_fs_error(const WoodFinishContext *w,const char *format,...)
{*w->diagnostic=FS_DIAGNOSTIC_INVALID;va_list args;va_start(args,format);vsnprintf(w->error,w->error_capacity,format,args);va_end(args);wood_fs_trim_tail(w->error);return false;}
bool wood_fs_capacity_error(const WoodFinishContext *w,const char *format,...)
{*w->diagnostic=FS_DIAGNOSTIC_CAPACITY;va_list args;va_start(args,format);vsnprintf(w->error,w->error_capacity,format,args);va_end(args);wood_fs_trim_tail(w->error);return false;}
static bool wood_fs_parse_u32(const char *s,uint32_t *out)
{uint64_t value=0;if(!*s)return false;for(;*s;++s){if(*s<'0'||*s>'9'||value>(UINT32_MAX-(unsigned)(*s-'0'))/10)return false;value=value*10+(unsigned)(*s-'0');}*out=(uint32_t)value;return true;}
static bool wood_fs_parameter_u32(const WoodFinishContext *w,GeoJson *j,int t,uint32_t *out)
{if(wood_eng_u32(j,t,out,false))return true;if(w->parameter_error&&w->parameter_error_capacity)snprintf(w->parameter_error,w->parameter_error_capacity,"I38 ID: expected uint32 identity");return false;}
bool wood_fs_name_check(const WoodFinishContext *w,const unsigned char *name,size_t n)
{
    if(!n)return wood_fs_error(w,"D41: finish surface name must be printable UTF-8");
    for(size_t i=0;i<n;){size_t k=geo_utf8_scalar(name+i,n-i);
        if(!k||name[i]<0x20||name[i]==0x7f||(k==2&&name[i]==0xc2&&name[i+1]<=0x9f))
            return wood_fs_error(w,"D41: finish surface name must be printable UTF-8");i+=k;}
    if(n>FS_NAME_MAX)return wood_fs_capacity_error(w,"I33 CAPACITY: finish surface name storage is limited to %d bytes",FS_NAME_MAX);
    return true;
}

bool wood_fs_used(const WoodFinishContext *w) { return w->state->count!=0; }

int wood_fs_index(const WoodFinishContext *w,uint32_t id)
{
    for(uint64_t i=0;i<w->state->count;++i)if(w->state->items[i].id==id)return (int)i;
    return -1;
}

const FinishSurface *wood_fs_find(const WoodFinishContext *w,uint32_t id)
{ int at=wood_fs_index(w,id);return at<0?NULL:&w->state->items[at]; }

void wood_fs_obstacle_text(const FinishObstacleRef *r,char out[16])
{ snprintf(out,16,"%c%u",r->kind==FS_OBSTACLE_BEAM?'b':'c',(unsigned)r->id); }

bool wood_fs_obstacle_parse(const char *s,FinishObstacleRef *out)
{
    uint32_t id;
    if((s[0]!='c'&&s[0]!='b')||!s[1]||(s[1]=='0'&&s[2]))return false;
    for(const char *p=s+1;*p;++p)if(*p<'0'||*p>'9')return false;
    if(!wood_fs_parse_u32(s+1,&id))return false;
    out->kind=s[0]=='b'?FS_OBSTACLE_BEAM:FS_OBSTACLE_COLUMN;out->id=id;return true;
}

int wood_fs_obstacle_compare(const void *a,const void *b)
{
    const FinishObstacleRef *x=a,*y=b;
    if(x->kind!=y->kind)return x->kind<y->kind?-1:1;
    return (x->id>y->id)-(x->id<y->id);
}

bool wood_fs_obstacles_normalize(const WoodFinishContext *w,FinishSurface *f)
{
    qsort(f->obstacles,f->obstacle_count,sizeof f->obstacles[0],wood_fs_obstacle_compare);
    for(uint32_t i=1;i<f->obstacle_count;++i)if(!wood_fs_obstacle_compare(&f->obstacles[i-1],&f->obstacles[i])){
        char text[16];wood_fs_obstacle_text(&f->obstacles[i],text);
        return wood_fs_error(w,"D41: finish surface %u lists obstacle %s more than once",(unsigned)f->id,text);
    }
    return true;
}

const char *wood_fs_relation_name(int relation)
{ return relation==FS_INTERIOR?"interior":relation==FS_TOUCH?"touch":"separate"; }

int wood_fs_relation(const WoodBoundaryRegion *b,const GeoCoord r[4])
{
    GeoCoord area=geo_loop_rect_intersection_area(&(GeoLoop2View){b->outline.v,b->outline.count},&(GeoRect2){r[0],r[1],r[2],r[3]});
    for(size_t h=0;h<b->hole_count;++h)area-=geo_loop_rect_intersection_area(&(GeoLoop2View){b->holes[h].v,b->holes[h].count},&(GeoRect2){r[0],r[1],r[2],r[3]});
    if(area>0)return FS_INTERIOR;
    if(geo_loop_touches_rect(&(GeoLoop2View){b->outline.v,b->outline.count},&(GeoRect2){r[0],r[1],r[2],r[3]}))return FS_TOUCH;
    for(size_t h=0;h<b->hole_count;++h)if(geo_loop_touches_rect(&(GeoLoop2View){b->holes[h].v,b->holes[h].count},&(GeoRect2){r[0],r[1],r[2],r[3]}))return FS_TOUCH;
    return FS_SEPARATE;
}

bool wood_fs_boundary(const WoodFinishContext *w,uint32_t id,WoodBoundaryRegion *out)
{return w->evaluation&&w->evaluation->boundary?w->evaluation->boundary(w->evaluation->user,id,out):w->boundary(w->user,id,out);}
bool wood_fs_obstacle_box(const WoodFinishContext *w,const FinishObstacleRef *ref,GeoCoord lo[3],GeoCoord hi[3])
{return w->evaluation&&w->evaluation->obstacle_box?w->evaluation->obstacle_box(w->evaluation->user,ref,lo,hi):w->obstacle_box(w->user,ref,lo,hi);}
bool wood_fs_obstacle_view(const WoodFinishContext *w,const FinishSurface *f,const FinishObstacleRef *r,FsObstacleView *out)
{
    GeoCoord lo[3],hi[3],u[2],v[2],n[2];char text[16];wood_fs_obstacle_text(r,text);
    if(!wood_fs_obstacle_box(w,r,lo,hi))return wood_fs_error(w,"I52/I55: finish surface %u obstacle %s does not exist",(unsigned)f->id,text);
    geo_aabb_project_interval(lo,hi,f->frame.origin,f->frame.axis_u,u);
    geo_aabb_project_interval(lo,hi,f->frame.origin,f->frame.axis_v,v);
    geo_aabb_project_interval(lo,hi,f->frame.origin,f->frame.normal,n);
    out->rect[0]=u[0];out->rect[1]=v[0];out->rect[2]=u[1];out->rect[3]=v[1];
    out->q[0]=f->side>0?n[0]:-n[1];out->q[1]=f->side>0?n[1]:-n[0];
    for(int i=0;i<4;++i)if(!geo_coord_in_range(out->rect[i]))
        return wood_fs_capacity_error(w,"I52/D1 CAPACITY: obstacle %s of finish surface %u has local coordinates outside D1 (I33)",text,(unsigned)f->id);
    for(int i=0;i<2;++i)if(!geo_coord_in_range(out->q[i]))
        return wood_fs_capacity_error(w,"I52/D1 CAPACITY: obstacle %s of finish surface %u has local coordinates outside D1 (I33)",text,(unsigned)f->id);
    WoodBoundaryRegion value;const WoodBoundaryRegion *b=wood_fs_boundary(w,f->boundary_id,&value)?&value:NULL;
    if(!b)return wood_fs_error(w,"I52: finish surface %u references missing boundary %u",(unsigned)f->id,(unsigned)f->boundary_id);
    out->relation=wood_fs_relation(b,out->rect);return true;
}

bool wood_fs_check(const WoodFinishContext *w,const FinishSurface *f)
{if(w->evaluation&&w->evaluation->check)return w->evaluation->check(w->evaluation->user,f);return wood_fs_check_direct(w,f);}
bool wood_fs_check_direct(const WoodFinishContext *w,const FinishSurface *f)
{
    size_t n=0;while(n<sizeof f->name&&f->name[n])++n;
    if(!f->id)return wood_fs_error(w,"D41: finish surface id must be a positive integer");
    if(!wood_fs_name_check(w,(const unsigned char*)f->name,n))return false;
    WoodBoundaryRegion boundary;
    if(!wood_fs_boundary(w,f->boundary_id,&boundary))
        return wood_fs_error(w,"I52: finish surface %u references missing boundary %u",(unsigned)f->id,(unsigned)f->boundary_id);
    if(!geo_frame_is_valid(&f->frame))
        return wood_fs_error(w,"I52/I1: finish surface %u frame needs an origin in D1 and unit integer axes with U x V = N",(unsigned)f->id);
    if(f->side!=1&&f->side!=-1)return wood_fs_error(w,"D41: finish surface %u structureSide must be 1 or -1",(unsigned)f->id);
    if(f->obstacle_count>FS_OBSTACLE_MAX)return wood_fs_capacity_error(w,"I33 CAPACITY: finish surface %u obstacle set is limited to %d",(unsigned)f->id,FS_OBSTACLE_MAX);
    for(uint32_t i=0;i<f->obstacle_count;++i){FsObstacleView view;
        if(i&&wood_fs_obstacle_compare(&f->obstacles[i-1],&f->obstacles[i])>=0)
            return wood_fs_error(w,"D41: finish surface %u obstacle set must be unique and in R41 order",(unsigned)f->id);
        if(!wood_fs_obstacle_view(w,f,&f->obstacles[i],&view))return false;
    }
    return true;
}

bool wood_fs_rebuild(WoodFinishContext *w,char *error,size_t capacity)
{
    const FinishSurfaceState *s=w->state;
    if(s->count>FS_MAX){wood_fs_capacity_error(w,"I33 CAPACITY: finish surface limit is %d",FS_MAX);snprintf(error,capacity,"%s",w->error);return false;}
    for(uint64_t i=0;i<s->count;++i){
        for(uint64_t k=0;k<i;++k)if(s->items[k].id==s->items[i].id){snprintf(error,capacity,"D41: duplicate finish surface id %u",(unsigned)s->items[i].id);return false;}
        if(!wood_fs_check(w,&s->items[i])){snprintf(error,capacity,"%s",w->error);wood_fs_trim_tail(error);return false;}
    }
    return true;
}

uint32_t wood_fs_reference_owner(const WoodFinishContext *w,const char *kind,uint32_t id)
{
    bool boundary=!strcmp(kind,"boundary"),column=!strcmp(kind,"column"),beam=!strcmp(kind,"beam");
    if(!boundary&&!column&&!beam)return 0;
    for(uint64_t i=0;i<w->state->count;++i){const FinishSurface *f=&w->state->items[i];
        if(boundary&&f->boundary_id==id)return f->id;
        for(uint32_t k=0;k<f->obstacle_count;++k)
            if(f->obstacles[k].id==id&&f->obstacles[k].kind==(column?FS_OBSTACLE_COLUMN:FS_OBSTACLE_BEAM)&&!boundary)return f->id;
    }
    return 0;
}

bool wood_fs_from_json(const WoodFinishContext *w,GeoJson *j,int t,FinishSurface *f)
{
    int frame=geo_json_member(j,t,"frame"),origin,obstacles=geo_json_member(j,t,"obstacles");int64_t side,xyz[3];
    int name=geo_json_member(j,t,"name");
    memset(f,0,sizeof *f);
    if(!geo_json_keys(j,t,"id,name,boundaryId,frame,structureSide,obstacles","")||!wood_eng_u32(j,geo_json_member(j,t,"id"),&f->id,true)||
       !wood_eng_u32(j,geo_json_member(j,t,"boundaryId"),&f->boundary_id,true))
        return wood_fs_error(w,"D41: finish surface needs positive id and boundaryId, name, frame {origin,U,V,N}, structureSide and obstacles");
    if(!geo_json_valid_token(j,name)||j->tokens[name].type!=GEO_J_STRING)return wood_fs_error(w,"D41: finish surface name must be a string");
    if(!wood_fs_name_check(w,(const unsigned char*)j->tokens[name].string,strlen(j->tokens[name].string)))return false;
    memcpy(f->name,j->tokens[name].string,strlen(j->tokens[name].string)+1);
    if(!geo_json_is_object(j,frame)||!geo_json_keys(j,frame,"origin,U,V,N",""))
        return wood_fs_error(w,"I52/D2: finish surface %u frame needs origin, U, V and N",(unsigned)f->id);
    origin=geo_json_member(j,frame,"origin");
    if(!geo_json_is_array(j,origin)||geo_json_size(j,origin)!=3)return wood_fs_error(w,"I52/D1: finish surface %u origin must be three integer mm",(unsigned)f->id);
    for(int i=0;i<3;++i)if(!geo_json_integer(j,geo_json_at(j,origin,i),&xyz[i]))return wood_fs_error(w,"I52/D1: finish surface %u origin must be three integer mm",(unsigned)f->id);
    f->frame.origin=(GeoPoint3){xyz[0],xyz[1],xyz[2]};
    if(!wood_sp_axis(j,geo_json_member(j,frame,"U"),&f->frame.axis_u)||!wood_sp_axis(j,geo_json_member(j,frame,"V"),&f->frame.axis_v)||
       !wood_sp_axis(j,geo_json_member(j,frame,"N"),&f->frame.normal))
        return wood_fs_error(w,"I52/D2: finish surface %u axes must each be one of +X -X +Y -Y +Z -Z",(unsigned)f->id);
    if(!geo_json_integer(j,geo_json_member(j,t,"structureSide"),&side)||(side!=1&&side!=-1))
        return wood_fs_error(w,"D41: finish surface %u structureSide must be 1 or -1",(unsigned)f->id);
    f->side=(int32_t)side;
    if(!geo_json_is_array(j,obstacles))return wood_fs_error(w,"D41: finish surface %u obstacles must be an array of c<id> / b<id>",(unsigned)f->id);
    int count=geo_json_size(j,obstacles);
    if(count>FS_OBSTACLE_MAX)return wood_fs_capacity_error(w,"I33 CAPACITY: finish surface %u obstacle set is limited to %d",(unsigned)f->id,FS_OBSTACLE_MAX);
    for(int i=0;i<count;++i){char text[16];
        if(!geo_json_string(j,geo_json_at(j,obstacles,i),text,sizeof text)||!wood_fs_obstacle_parse(text,&f->obstacles[i]))
            return wood_fs_error(w,"D41: finish surface %u obstacles must be typed references c<id> or b<id>",(unsigned)f->id);}
    f->obstacle_count=(uint32_t)count;
    return wood_fs_obstacles_normalize(w,f);
}

bool wood_fs_put(WoodFinishContext *w,GeoJson *j,int t)
{
    FinishSurface f;FinishSurfaceState *s=w->state;
    if(!wood_fs_from_json(w,j,t,&f)||!wood_fs_check(w,&f))return false;
    int at=wood_fs_index(w,f.id);
    if(at<0){if(s->count>=FS_MAX)return wood_fs_capacity_error(w,"I33 CAPACITY: finish surface limit is %d",FS_MAX);at=(int)s->count++;}
    memcpy(&s->items[at],&f,sizeof f);return true;
}

bool wood_fs_delete(WoodFinishContext *w,uint32_t id)
{
    FinishSurfaceState *s=w->state;int at=wood_fs_index(w,id);
    if(at<0)return wood_fs_error(w,"D41: deleted finish surface %u does not exist",(unsigned)id);
    memmove(&s->items[at],&s->items[at+1],(size_t)(s->count-(uint64_t)at-1)*sizeof s->items[0]);
    --s->count;memset(&s->items[s->count],0,sizeof s->items[0]);return true;
}

bool wood_fs_operation(WoodFinishContext *w,GeoJson *j,int t)
{
    char op[40];uint32_t id;
    if(!geo_json_string(j,geo_json_member(j,t,"op"),op,sizeof op))return wood_fs_error(w,"I55: panel-fill operation needs op");
    if(!strcmp(op,"put-derived-placement")||!strcmp(op,"delete-derived-placement"))return w->derived_operation(w->user,j,t,!strcmp(op,"delete-derived-placement"));
    /* I53/I55: a host h change and the explicit B source changes may form one
     * candidate. PF-H previews disclose these dependencies before confirmation. */
    if(w->state->host_count&&(!strcmp(op,"set-source")||!strcmp(op,"set-override")||!strcmp(op,"unbind-source")||!strcmp(op,"put-parameter")))return w->engineering_operation(w->user,j,t);
    if(!strcmp(op,"put-panel-fill")||!strcmp(op,"delete-panel-fill"))return wood_pf_operation(w,j,t,!strcmp(op,"delete-panel-fill"));
    if(!strcmp(op,"put-finish-surface")){
        if(!geo_json_keys(j,t,"op,value",""))return wood_fs_error(w,"I55: put-finish-surface takes op and value");
        return wood_fs_put(w,j,geo_json_member(j,t,"value"));
    }
    if(!strcmp(op,"delete-finish-surface")){
        if(!geo_json_keys(j,t,"op,id","")||!wood_eng_u32(j,geo_json_member(j,t,"id"),&id,true))return wood_fs_error(w,"I55: delete-finish-surface needs a positive id");
        return wood_fs_delete(w,id);
    }
    /* PF-2 scope (I8a/I55): the panel-fill preview discloses finish surfaces and panel-fill definitions only, so it must
     * not carry any other definition change (parameters, materials, sources) that confirm would commit unseen. */
    return wood_fs_error(w,"PF-2 scope (I8a/I55): panel-fill transactions accept only put-finish-surface, delete-finish-surface, put-panel-fill and delete-panel-fill; "
                    "send %s through its own previewed transaction",op);
}

const PanelFill *wood_pf_find(const WoodFinishContext *w,uint32_t id)
{ for(uint64_t i=0;i<w->state->fill_count;++i)if(w->state->fills[i].id==id)return &w->state->fills[i];return NULL; }

void wood_pf_free(WoodFinishLayout *d)
{wood_panel_layout_free(&d->layout);memset(d,0,sizeof *d);}

static bool wood_pf_source(const WoodFinishContext *w,GeoJson *j,int t,GeoCoord *value,GeoParameterRef *ref)
{
    if(geo_json_integer(j,t,value))return geo_coord_in_range(*value)||wood_fs_error(w,"I52/D1: panel-fill source outside D1");
    ref->set=true;
    return (geo_json_keys(j,t,"parameterId,fieldId","")&&wood_fs_parameter_u32(w,j,geo_json_member(j,t,"parameterId"),&ref->parameter_id)&&wood_fs_parameter_u32(w,j,geo_json_member(j,t,"fieldId"),&ref->field_id))||wood_fs_error(w,"D42: source must be integer mm or ParameterRef");
}

bool wood_pf_parse(const WoodFinishContext *w,GeoJson *j,int t,PanelFill *p)
{
    memset(p,0,sizeof *p);int axis;char pattern[16];
    int o=geo_json_member(j,t,"origin"),s=geo_json_member(j,t,"stagger"),x=geo_json_member(j,t,"threshold");
    if(!geo_json_keys(j,t,"id,finishSurfaceId,panel,lengthAlong,origin,gap,pattern,threshold","stagger")||
       !wood_eng_u32(j,geo_json_member(j,t,"id"),&p->id,true)||!wood_eng_u32(j,geo_json_member(j,t,"finishSurfaceId"),&p->finish_id,true)||
       !wood_eng_ref_parse(j,geo_json_member(j,t,"panel"),&p->panel,false)||!wood_eng_axis(j,geo_json_member(j,t,"lengthAlong"),&axis)||!axis||
       !geo_json_is_array(j,o)||geo_json_size(j,o)!=2||!geo_json_integer(j,geo_json_at(j,o,0),&p->origin[0])||!geo_coord_in_range(p->origin[0])||!geo_json_integer(j,geo_json_at(j,o,1),&p->origin[1])||!geo_coord_in_range(p->origin[1])||
       !geo_json_string(j,geo_json_member(j,t,"pattern"),pattern,sizeof pattern))return wood_fs_error(w,"D42: invalid panel-fill definition");
    p->length_axis=axis-1;p->stagger_axis=-1;
    if(!wood_pf_source(w,j,geo_json_member(j,t,"gap"),&p->gap,&p->gap_ref))return false;
    if(!strcmp(pattern,"stagger")){
        if(!geo_json_keys(j,s,"axis,value","")||!wood_eng_axis(j,geo_json_member(j,s,"axis"),&axis)||!axis)return wood_fs_error(w,"D42: stagger needs one axis and source");
        p->stagger_axis=axis-1;if(!wood_pf_source(w,j,geo_json_member(j,s,"value"),&p->stagger,&p->stagger_ref))return false;
    }else if(strcmp(pattern,"straight")||s>=0)return wood_fs_error(w,"D42: straight must omit stagger; pattern must be straight or stagger");
    p->threshold.set=true;
    if(!geo_json_keys(j,x,"parameterId,fieldId","")||!wood_fs_parameter_u32(w,j,geo_json_member(j,x,"parameterId"),&p->threshold.parameter_id)||!wood_fs_parameter_u32(w,j,geo_json_member(j,x,"fieldId"),&p->threshold.field_id))return wood_fs_error(w,"D44: threshold must be a ParameterRef");
    if(!geo_json_canonical(j,t,p->definition,sizeof p->definition))return wood_fs_capacity_error(w,"I33 CAPACITY: panel-fill definition limit is 1023 bytes");
    return true;
}

bool wood_pf_field_direct(const WoodFinishContext *w,const PanelFill *p,int field,GeoQuantity *out)
{
    if(field<WOOD_PF_LENGTH||field>WOOD_PF_THRESHOLD)return false;
    GeoCoord value=0;
    if(field>=WOOD_PF_GAP){
        if(field==WOOD_PF_THRESHOLD)return w->parameter_value(w->user,p->threshold,out);
        GeoParameterRef ref=field==WOOD_PF_GAP?p->gap_ref:p->stagger_ref;
        value=field==WOOD_PF_GAP?p->gap:p->stagger;
        if(ref.set&&!w->parameter_coord(w->user,ref,&value))return false;
        *out=(GeoQuantity){value,1,GEO_UNIT_LENGTH};return true;
    }
    const EngMaterialVersion *m=wood_eng_material(&w->engineering,p->panel.id,p->panel.version);
    if(!m||m->kind!=0)return wood_fs_error(w,"I52: panel-fill %u needs an existing fixed panel material version",p->id);
    if(field==WOOD_PF_LENGTH||field==WOOD_PF_WIDTH){*out=(GeoQuantity){field==WOOD_PF_LENGTH?m->length:m->width,1,GEO_UNIT_LENGTH};return true;}
    if(field!=WOOD_PF_THICKNESS)return false;
    if(!wood_eng_material_integer(&w->engineering,m,WOOD_ENG_VERSION_THICKNESS,1,GEO_COORD_LIMIT,&value))
        return wood_fs_error(w,"I52: panel-fill thickness must be explicitly set positive integer mm in D1; no rounding");
    *out=(GeoQuantity){value,1,GEO_UNIT_LENGTH};return true;
}
static bool wood_pf_field(const WoodFinishContext *w,const PanelFill *p,int field,GeoQuantity *out)
{return w->evaluation&&w->evaluation->field?w->evaluation->field(w->evaluation->user,p,field,out):wood_pf_field_direct(w,p,field,out);}
bool wood_pf_values(const WoodFinishContext *w,const PanelFill *p,WoodFinishLayout *d)
{if(w->evaluation&&w->evaluation->values)return w->evaluation->values(w->evaluation->user,p,d);return wood_pf_values_direct(w,p,d);}
bool wood_pf_values_direct(const WoodFinishContext *w,const PanelFill *p,WoodFinishLayout *d)
{
    d->finish=wood_fs_find(w,p->finish_id);const EngMaterialVersion *m=wood_eng_material(&w->engineering,p->panel.id,p->panel.version);GeoQuantity x;
    if(!d->finish)return wood_fs_error(w,"I55: panel-fill %u references missing finish surface %u",p->id,p->finish_id);
    if(!m||m->kind!=0)return wood_fs_error(w,"I52: panel-fill %u needs an existing fixed panel material version",p->id);
    d->frame=d->finish->frame;
    if(w->evaluation&&w->evaluation->finish_definition&&!w->evaluation->finish_definition(w->evaluation->user,p->finish_id))return false;
    if(!wood_pf_field(w,p,WOOD_PF_LENGTH,&x))return false;d->layout.size[p->length_axis]=x.num;
    if(!wood_pf_field(w,p,WOOD_PF_WIDTH,&x))return false;d->layout.size[1-p->length_axis]=x.num;
    d->t=0;if(!wood_pf_field(w,p,WOOD_PF_THICKNESS,&x))return false;d->t=x.num;
    d->layout.gap=p->gap;d->layout.stagger=p->stagger;
    if(!wood_pf_field(w,p,WOOD_PF_GAP,&x))return wood_fs_error(w,"%s",w->parameter_error);d->layout.gap=x.num;
    if(!wood_pf_field(w,p,WOOD_PF_STAGGER,&x))return wood_fs_error(w,"%s",w->parameter_error);d->layout.stagger=x.num;
    if(!wood_pf_field(w,p,WOOD_PF_THRESHOLD,&x))return wood_fs_error(w,"%s",w->parameter_error);
    if(x.num<=0)return wood_fs_error(w,"D44: panel-fill threshold must be a positive dimension");
    if(d->layout.gap<0)return wood_fs_error(w,"I52: panel-fill gap must be nonnegative integer mm");
    if(p->stagger_axis>=0&&(!d->layout.stagger||d->layout.stagger%geo_period_pitch(d->layout.size[p->stagger_axis],d->layout.gap)==0))return wood_fs_error(w,"I52: stagger is zero or a whole pitch; odd and even rows coincide");
    for(uint32_t i=0;i<d->finish->obstacle_count;++i){if(!wood_fs_obstacle_view(w,d->finish,&d->finish->obstacles[i],&d->obstacles[i]))return false;
        d->cuts[i]=d->obstacles[i].relation==FS_INTERIOR&&d->obstacles[i].q[0]<d->t&&d->obstacles[i].q[1]>0;}
    return true;
}

GeoRegionView wood_pf_region_view(const WoodBoundaryRegion *b,GeoLoop2View *holes)
{for(size_t i=0;i<b->hole_count;++i)holes[i]=(GeoLoop2View){b->holes[i].v,b->holes[i].count};return (GeoRegionView){{b->outline.v,b->outline.count},holes,b->hole_count};}

size_t wood_pf_selected_cuts(const WoodFinishLayout *d,GeoRect2 *cuts)
{size_t n=0;for(size_t i=0;i<d->finish->obstacle_count;++i)if(d->cuts[i]){const GeoCoord *r=d->obstacles[i].rect;cuts[n++]=(GeoRect2){r[0],r[1],r[2],r[3]};}return n;}

int wood_pf_point_order(GeoPoint2 a,GeoPoint2 b)
{return geo_clip_point_order(a,b);}

bool wood_pf_clip_status(const WoodFinishContext *w,GeoClipStatus status)
{
    switch(status){
    case GEO_CLIP_OK:return true;
    case GEO_CLIP_AXIS_LIMIT:return wood_fs_capacity_error(w,"I33 CAPACITY: clipping axis limit is %d",GEO_CLIP_AXIS_MAX);
    case GEO_CLIP_WORKSPACE:return wood_fs_capacity_error(w,"I33 CAPACITY: clipping workspace unavailable");
    case GEO_CLIP_COMPONENT_WORKSPACE:return wood_fs_capacity_error(w,"I33 CAPACITY: fragment workspace unavailable");
    case GEO_CLIP_EDGE_LIMIT:return wood_fs_capacity_error(w,"I33 CAPACITY: tile contour edge limit is %d",GEO_CLIP_EDGE_MAX);
    case GEO_CLIP_LOOP_WORKSPACE:return wood_fs_capacity_error(w,"I33 CAPACITY: loop workspace unavailable");
    case GEO_CLIP_TRAVERSAL:return wood_fs_error(w,"R42: contour traversal did not close");
    case GEO_CLIP_OPEN_CONTOUR:return wood_fs_error(w,"R42: open contour after clipping");
    case GEO_CLIP_CORNERS_WORKSPACE:return wood_fs_capacity_error(w,"I33 CAPACITY: contour corners unavailable");
    case GEO_CLIP_ORDERED_WORKSPACE:return wood_fs_capacity_error(w,"I33 CAPACITY: ordered loop unavailable");
    case GEO_CLIP_VERTEX_LIMIT:return wood_fs_capacity_error(w,"I33 CAPACITY: layout vertex limit is %d",WOOD_PANEL_VERTEX_MAX);
    case GEO_CLIP_COLLECTION_WORKSPACE:return wood_fs_capacity_error(w,"I33 CAPACITY: loop collection unavailable");
    case GEO_CLIP_NO_OUTER:return wood_fs_error(w,"R42: clipped component lacks an outer loop");
    }
    return false;
}

bool wood_pf_clip(const WoodFinishContext *w,WoodFinishLayout *d,WoodPanelTile *t)
{
    GeoLoop2View holes[GEO_REGION_MAX_HOLES];GeoRect2 cuts[FS_OBSTACLE_MAX];
    WoodBoundaryRegion boundary;if(!wood_fs_boundary(w,d->finish->boundary_id,&boundary))return wood_fs_error(w,"I52: finish surface %u references missing boundary %u",d->finish->id,d->finish->boundary_id);
    GeoRegionView region=wood_pf_region_view(&boundary,holes);
    size_t count=wood_pf_selected_cuts(d,cuts);GeoRect2 body={t->body[0],t->body[1],t->body[2],t->body[3]};
    GeoClipResult result={t->fragments,t->count,t->area};
    GeoClipStatus status=geo_region_clip_rect_minus_rects(&region,&body,cuts,count,d->keep_collinear,WOOD_PANEL_VERTEX_MAX,&d->layout.vertices,&result);
    t->fragments=result.fragments;t->count=result.count;t->area=result.area;return wood_pf_clip_status(w,status);
}

bool wood_pf_build(const WoodFinishContext *w,const PanelFill *p,WoodFinishLayout *d)
{
    memset(d,0,sizeof *d);if(!wood_pf_values(w,p,d))return false;
    GeoLoop2View holes[GEO_REGION_MAX_HOLES];GeoRect2 cuts[FS_OBSTACLE_MAX];WoodPanelLayoutInput input={0};
    WoodBoundaryRegion boundary;if(!wood_fs_boundary(w,d->finish->boundary_id,&boundary))return wood_fs_error(w,"I52: finish surface %u references missing boundary %u",d->finish->id,d->finish->boundary_id);
    input.region=wood_pf_region_view(&boundary,holes);input.frame=d->frame;
    input.cuts=cuts;input.cut_count=wood_pf_selected_cuts(d,cuts);input.size[0]=d->layout.size[0];input.size[1]=d->layout.size[1];
    input.gap=d->layout.gap;input.stagger=d->layout.stagger;input.origin[0]=p->origin[0];input.origin[1]=p->origin[1];input.stagger_axis=p->stagger_axis;
    GeoClipStatus clip_status;WoodPanelStatus status=wood_panel_layout_build(&input,&d->layout,&clip_status);
    if(status==WOOD_PANEL_OK)return true;wood_pf_free(d);
    switch(status){
    case WOOD_PANEL_WORKSPACE:return wood_fs_capacity_error(w,"I33 CAPACITY: layout workspace unavailable");
    case WOOD_PANEL_ENUM_LIMIT:return wood_fs_capacity_error(w,"I33 CAPACITY: full layout enumeration limit is %d tiles",WOOD_PANEL_TILE_MAX);
    case WOOD_PANEL_CLIP:return wood_pf_clip_status(w,clip_status);
    case WOOD_PANEL_CORNER_RANGE:return wood_fs_capacity_error(w,"I52/D1 CAPACITY: returned sheet corner outside D1");
    case WOOD_PANEL_VERTEX_RANGE:return wood_fs_capacity_error(w,"I52/D1 CAPACITY: returned panel-fill vertex outside D1");
    case WOOD_PANEL_SEAM_WORKSPACE:return wood_fs_capacity_error(w,"I33 CAPACITY: seam workspace unavailable");
    case WOOD_PANEL_SEAM_LIMIT:return wood_fs_capacity_error(w,"I33 CAPACITY: seam line limit is %d",4*WOOD_PANEL_TILE_MAX);
    case WOOD_PANEL_BAND_RANGE:return wood_fs_capacity_error(w,"I52/D1 CAPACITY: returned seam band outside D1");
    default:return false;
    }
}

bool wood_pf_rebuild(const WoodFinishContext *w)
{for(uint64_t i=0;i<w->state->fill_count;++i){WoodFinishLayout d;bool ok=wood_pf_build(w,&w->state->fills[i],&d);wood_pf_free(&d);if(!ok)return false;}return true;}

bool wood_pf_operation(WoodFinishContext *w,GeoJson *j,int t,bool remove)
{
    FinishSurfaceState *s=w->state;PanelFill p;uint32_t id;
    if(remove){if(!geo_json_keys(j,t,"op,id","")||!wood_eng_u32(j,geo_json_member(j,t,"id"),&id,true))return wood_fs_error(w,"D42: delete-panel-fill needs id");}
    else{if(!geo_json_keys(j,t,"op,value","")||!wood_pf_parse(w,j,geo_json_member(j,t,"value"),&p))return false;id=p.id;}
    size_t at=0;while(at<s->fill_count&&s->fills[at].id!=id)++at;
    if(remove){if(at==s->fill_count)return wood_fs_error(w,"D42: deleted panel-fill does not exist");memmove(&s->fills[at],&s->fills[at+1],(s->fill_count-at-1)*sizeof p);memset(&s->fills[--s->fill_count],0,sizeof p);return true;}
    if(at==s->fill_count){if(at==FS_MAX)return wood_fs_capacity_error(w,"I33 CAPACITY: panel-fill limit is %d",FS_MAX);++s->fill_count;}s->fills[at]=p;return true;
}

bool wood_fs_load(WoodFinishContext *w,FinishSurface *f,const char **scene_message)
{
    *scene_message=NULL;
    if(wood_fs_find(w,f->id)){*scene_message="I56: duplicate finish-surface record";return false;}
    if(!wood_fs_obstacles_normalize(w,f)||!wood_fs_check(w,f)){*scene_message=w->error;return false;}
    if(w->state->count>=FS_MAX){wood_fs_capacity_error(w,"I33 CAPACITY: finish surface limit reached");*scene_message=w->error;return false;}
    memcpy(&w->state->items[w->state->count++],f,sizeof *f);return true;
}
bool wood_pf_load(WoodFinishContext *w,uint32_t id,const PanelFill *p)
{
    bool ok=true;
    if(p->id!=id||wood_pf_find(w,id))ok=wood_fs_error(w,"I56: panel-fill id mismatch or duplicate");
    if(ok&&w->state->fill_count==FS_MAX)ok=wood_fs_capacity_error(w,"I33 CAPACITY: panel-fill limit is %d",FS_MAX);
    if(ok)w->state->fills[w->state->fill_count++]=*p;
    return ok;
}
