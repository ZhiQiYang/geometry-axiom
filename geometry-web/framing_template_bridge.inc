/* H adapter for the bounded W generator. All formal output is existing World
 * syntax. Recipes, ownership and generation counters are runtime/project data.
 * Private IDs are chosen against the candidate, never consumed by preview. */
#include "../geometry-templates/woodworking/native/flat_ceiling.h"
#include "../geometry-templates/woodworking/native/flat_ceiling_jig.h"
typedef struct {
    WoodFlatParameters parameters;WoodFlatPlan plan;
    uint32_t version;char candidate_fingerprint[65];
    uint32_t boundary,on,finish,fill,host,grid,ids[WOOD_FLAT_MEMBERS],guides[WOOD_FLAT_LINES];
    EngVersionRef panel;ParameterRef threshold;
    const World *before;const char *failure_code;
} FramingTemplateCall;
static char g_framing_context[65],g_framing_owner[65];
static uint32_t g_framing_token;
static uint64_t g_framing_invocations;
static bool framing_template_document(const char *path,GeoJson *j,char **text)
{
    size_t size;*text=eng_read_file(path,&size);
    if(!*text){eng_bridge_error("INPUT",g_engineering_error);return false;}
    if(memchr(*text,0,size)||!utf8_is_valid(*text)){free(*text);eng_bridge_error("INPUT","需完整 UTF-8 JSON，且不得含 NUL");return false;}
    if(!app_json_parse_n(j,*text,size)){eng_bridge_error("SCHEMA",j->error);geo_json_free(j);free(*text);return false;}
    for(int i=0;i<j->count;++i)if(j->tokens[i].type==GEO_J_STRING)
        for(const unsigned char *p=(const unsigned char*)j->tokens[i].string;*p;++p)if(*p<32||*p==127){
            eng_bridge_error("SCHEMA","JSON 字串不得含控制字元");geo_json_free(j);free(*text);return false;
        }
    return true;
}
static bool framing_template_word(GeoJson *j,int object,const char *key,const char *value)
{char out[128];return geo_json_string(j,geo_json_member(j,object,key),out,sizeof out)&&!strcmp(out,value);}
static bool framing_template_context(void)
{
    if(g_framing_context[0]||timber_edit_random_key(g_framing_context))return true;
    eng_bridge_error("RANDOM","無法建立原生工作區擁有碼");return false;
}
static void framing_template_defaults(void)
{fputs("{\"panelWidth\":915,\"panelLength\":1830,\"gap\":2,\"timberWidth\":27,\"timberDepth\":33,\"maxSecondarySpacing\":367}",stdout);}
static void cmd_framing_template_read(const char *path)
{
    GeoJson j;char *text;if(!framing_template_document(path,&j,&text))return;
    uint32_t boundary,version=1;char hash[65];const SpaceBoundarySurface *surface;
    bool jig=framing_template_word(&j,0,"schema","framing-template-read/2");
    int tpl=geo_json_member(&j,0,"template");
    bool valid_schema=jig?geo_json_keys(&j,0,"schema,boundaryId,template","")&&
        geo_json_keys(&j,tpl,"id,version,policyFingerprint","")&&framing_template_word(&j,tpl,"id","flat-ceiling")&&
        eng_u32(&j,geo_json_member(&j,tpl,"version"),&version,false)&&version==2&&framing_template_word(&j,tpl,"policyFingerprint",WOOD_FLAT_JIG_POLICY):
        geo_json_keys(&j,0,"schema,boundaryId","")&&framing_template_word(&j,0,"schema","framing-template-read/1");
    if(!valid_schema||
       !eng_u32(&j,geo_json_member(&j,0,"boundaryId"),&boundary,false)||!(surface=world_find_boundary(&g_world,boundary))){
        eng_bridge_error("SCHEMA",jig?"需 framing-template-read/2、明選邊界與完整第二版政策身分":"需 framing-template-read/1 與明選的現有邊界");goto done;
    }
    if(!framing_template_context())goto done;
    if(!eng_definition_hash(&g_world,hash)){eng_bridge_error("IO","無法核對 World 定義指紋");goto done;}
    printf("{\"ok\":true,\"schema\":\"framing-template-read-result/%u\",\"revision\":\"%llu\",\"contextKey\":\"%s\",\"definitionFingerprint\":\"%s\",\"generatorInvocations\":%llu,\"source\":{\"boundaryId\":%u,\"outer\":",
        version,(unsigned long long)g_definition_revision,g_framing_context,hash,(unsigned long long)g_framing_invocations,boundary);
    fs_json_loop(&surface->outline);printf(",\"holes\":%zu,\"placements\":[",surface->hole_count);bool first=true;
    for(size_t i=0;i<world_placement_count(&g_world);++i){const PlacementSurface *p=world_placement_at(&g_world,i);
        if(p->boundary_id!=boundary||p->derived_fill_id)continue;
        printf("%s{\"id\":%u,\"frame\":{\"origin\":[%lld,%lld,%lld],\"u\":\"%s\",\"v\":\"%s\"}}",first?"":",",p->id,
            (long long)p->frame.origin.x,(long long)p->frame.origin.y,(long long)p->frame.origin.z,fs_axis_word(p->frame.axis_u),fs_axis_word(p->frame.axis_v));first=false;
    }
    if(jig)fputs("]},\"generator\":{\"id\":\"flat-ceiling\",\"version\":2,\"policyFingerprint\":\"" WOOD_FLAT_JIG_POLICY "\",\"scope\":\"rectangle-fixed-jig-no-retreat\",\"defaults\":",stdout);
    else fputs("]},\"generator\":{\"id\":\"flat-ceiling\",\"version\":1,\"policyFingerprint\":\"" WOOD_FLAT_POLICY "\",\"scope\":\"rectangle-common-policy\",\"defaults\":",stdout);
    framing_template_defaults();fputs("},\"sources\":{\"panels\":[",stdout);first=true;
    for(size_t i=0;i<g_world.wood.engineering.material_count;++i){const EngMaterialVersion *m=eng_material_at(&g_world,i);if(!m||m->kind!=0||!m->has_thickness)continue;
        printf("%s%.*s,\"fingerprint\":\"%s\"}",first?"":",",(int)strlen(m->content)-1,m->content,m->fingerprint);first=false;
    }
    fputs("],\"parameters\":[",stdout);
    for(size_t i=0;i<geo_parameters_card_count(&g_world.geo.parameters);++i){if(i)putchar(',');parameter_json_card(&g_world,&geo_parameters_cards(&g_world.geo.parameters)[i],stdout,true);}
    fputs("]}}\n",stdout);
done:geo_json_free(&j);free(text);
}
static bool framing_template_parse(GeoJson *j,FramingTemplateCall *c)
{
    char context[65],hash[65],actual[65],corner[16],axis[4];uint64_t revision;uint32_t version;
    int tpl=geo_json_member(j,0,"template"),p=geo_json_member(j,0,"parameters"),layout=geo_json_member(j,0,"layout"),material=geo_json_member(j,0,"material"),sources=geo_json_member(j,0,"sources");
    int panel=geo_json_member(j,sources,"panel"),threshold=geo_json_member(j,sources,"threshold");
    if(!geo_json_keys(j,0,"schema,expectedRevision,contextKey,definitionFingerprint,boundaryId,on,template,parameters,layout,material,sources","")||
       !framing_template_word(j,0,"schema","framing-template-generate/1")||!timber_edit_revision(j,geo_json_member(j,0,"expectedRevision"),&revision)||
       !geo_json_string(j,geo_json_member(j,0,"contextKey"),context,sizeof context)||!boundary_pair_host_key(context)||
       !geo_json_string(j,geo_json_member(j,0,"definitionFingerprint"),hash,sizeof hash)||!boundary_pair_host_key(hash)||
       !eng_u32(j,geo_json_member(j,0,"boundaryId"),&c->boundary,false)||!eng_u32(j,geo_json_member(j,0,"on"),&c->on,false)||
       !geo_json_keys(j,tpl,"id,version,policyFingerprint","")||!framing_template_word(j,tpl,"id","flat-ceiling")||
       !eng_u32(j,geo_json_member(j,tpl,"version"),&version,false)||
       !((version==1&&framing_template_word(j,tpl,"policyFingerprint",WOOD_FLAT_POLICY))||
         (version==2&&framing_template_word(j,tpl,"policyFingerprint",WOOD_FLAT_JIG_POLICY)))||
       !geo_json_keys(j,p,"panelWidth,panelLength,gap,timberWidth,timberDepth,maxSecondarySpacing","")||
       !geo_json_keys(j,layout,"corner,lengthAlong","")||!geo_json_string(j,geo_json_member(j,layout,"corner"),corner,sizeof corner)||
       !geo_json_string(j,geo_json_member(j,layout,"lengthAlong"),axis,sizeof axis)||
       !geo_json_keys(j,material,"boundary,timber","")||!framing_template_word(j,material,"boundary","rc")||!framing_template_word(j,material,"timber","literal")||
       !geo_json_keys(j,sources,"panel,threshold","")||!geo_json_keys(j,panel,"id,version","")||
       !wood_eng_ref_parse(j,panel,&c->panel,false)||!geo_json_keys(j,threshold,"parameterId,fieldId","")||
       !eng_u32(j,geo_json_member(j,threshold,"parameterId"),&c->threshold.parameter_id,false)||
       !eng_u32(j,geo_json_member(j,threshold,"fieldId"),&c->threshold.field_id,false))
        return eng_fail("需完整明選來源、固定模板版本與政策指紋，不接受缺欄、額外欄或推測材料");
    c->version=version;c->threshold.set=true;
    if(!g_framing_context[0]||strcmp(context,g_framing_context)){c->failure_code="CONTEXT";return eng_fail("工作區 contextKey 已失效，請重新讀取");}
    if(revision!=g_definition_revision||!eng_definition_hash(&g_world,actual)||strcmp(hash,actual)){c->failure_code="STALE";return eng_fail("來源或 World 指紋已變更，請重新讀取");}
    if(strcmp(axis,"u")&&strcmp(axis,"v"))return eng_fail("板長軸必須明選 u 或 v");
    c->parameters.length_axis=!strcmp(axis,"v");
    if(strcmp(corner,"min-min")&&strcmp(corner,"max-min")&&strcmp(corner,"min-max")&&strcmp(corner,"max-max"))return eng_fail("起鋪角無效");
    c->parameters.start_max[0]=!strncmp(corner,"max",3);c->parameters.start_max[1]=!strcmp(corner+4,"max");
    Coord width,length;
    if(!eng_coord(j,geo_json_member(j,p,"panelWidth"),&width,true)||!eng_coord(j,geo_json_member(j,p,"panelLength"),&length,true)||
       !eng_coord(j,geo_json_member(j,p,"gap"),&c->parameters.gap,false)||!eng_coord(j,geo_json_member(j,p,"timberWidth"),&c->parameters.width,true)||
       !eng_coord(j,geo_json_member(j,p,"timberDepth"),&c->parameters.depth,true)||!eng_coord(j,geo_json_member(j,p,"maxSecondarySpacing"),&c->parameters.maximum,true))
        return eng_fail("尺寸只能是 D1 整數，gap 不得為負");
    const EngMaterialVersion *m=eng_material(&g_world,c->panel.id,c->panel.version);GeoQuantity x;
    if(!m||m->kind!=0||!m->has_thickness||m->width!=width||m->length!=length)return eng_fail("板寬、板長及板厚必須來自同一明選的固定 panel 版本");
    if(!parameter_value(&g_world,c->threshold,&x)||x.unit!=GEO_UNIT_LENGTH||x.num<=0||x.den<=0)return eng_fail("X 必須明選現存正 dimension ParameterRef；不可補隱藏預設");
    c->parameters.panel[c->parameters.length_axis]=length;c->parameters.panel[1-c->parameters.length_axis]=width;
    return true;
}
static bool framing_template_scope(FramingTemplateCall *c)
{
    const SpaceBoundarySurface *b=world_find_boundary(&g_world,c->boundary);const PlacementSurface *p=world_find_placement(&g_world,c->on);
    c->failure_code="UNSUPPORTED_SCOPE";
    if(!b||!p||p->boundary_id!=c->boundary||p->derived_fill_id)return eng_fail("需明選此邊界的一個既有普通框架來源");
    if(b->hole_count||b->outline.count!=4||g_world.wood.column_count||g_world.wood.beam_count) /* R03_WHOLE_MAIN_SCOPE */
        return eng_fail("第一片只接受無孔矩形、且 World 無柱樑；主支不因障礙被切成多段");
    if(p->frame.normal.z!=1||p->frame.axis_u.z||p->frame.axis_v.z)return eng_fail("平釘天花首片只接受結構側朝上的水平框架");
    int64_t bounds[4]={INT64_MAX,INT64_MAX,INT64_MIN,INT64_MIN};
    for(size_t i=0;i<4;++i){SurfacePoint2 q=b->outline.v[i],r=b->outline.v[(i+1)%4];
        if(b->outline.fixity[i]!=EDGE_FIXED||(q.u!=r.u&&q.v!=r.v)||(q.u==r.u&&q.v==r.v))return eng_fail("邊界需恰四個正長軸向 FIXED RC 邊");
        if(q.u<bounds[0])bounds[0]=q.u;if(q.v<bounds[1])bounds[1]=q.v;if(q.u>bounds[2])bounds[2]=q.u;if(q.v>bounds[3])bounds[3]=q.v;
    }
    for(size_t i=0;i<4;++i){SurfacePoint2 q=b->outline.v[i];if((q.u!=bounds[0]&&q.u!=bounds[2])||(q.v!=bounds[1]&&q.v!=bounds[3]))return eng_fail("不是完整軸向矩形");}
    for(size_t i=0;i<g_world.wood.grid_applications.count;++i)if(g_world.wood.grid_applications.items[i].placement_id==c->on)return eng_fail("來源面已有主格；不覆寫或猜測替換");
    for(size_t i=0;i<g_world.wood.timber_count;++i)if(g_world.wood.timbers[i].placed&&g_world.wood.anchors[i].placement_id==c->on)return eng_fail("來源面已有角材；第一片不重排既有正式物件");
    for(size_t i=0;i<g_world.wood.finish_surfaces.count;++i)if(g_world.wood.finish_surfaces.items[i].boundary_id==c->boundary)
        return eng_fail("邊界已有完成面或已生成骨架；第一片不在另一宿主重複排同一邊界");
    bool built=c->version==2?wood_flat_jig_build(bounds,&c->parameters,&c->plan):wood_flat_build(bounds,&c->parameters,&c->plan);
    if(!built){c->failure_code=c->plan.code;return eng_fail(c->plan.reason);}
    /* Existing oracle's R-butt can relocate a near-wall center. That policy
     * differs from this immutable from-fill center; reject the computed case. */
    GeoQuantity x;if(!parameter_value(&g_world,c->threshold,&x))return eng_fail(g_parameter_error);
    int a=1-c->parameters.length_axis;Coord w=c->parameters.width,gl=c->parameters.gap/2,gu=c->parameters.gap-gl;
    Coord lh=w/2,hh=w-lh;
    for(size_t i=0;i<c->plan.seam_count[a];++i){Coord center=c->plan.seams[a][i],left=center-lh-bounds[a]-w,right=bounds[a+2]-w-center-hh;
        if((left>0&&wood_flat_width_enough(hh-gu-left,x.num,x.den))||(right>0&&wood_flat_width_enough(lh-gl-right,x.num,x.den))){c->failure_code="POLICY_RULE_CONFLICT";return eng_fail("此縫在舊 R-butt 會移主支中心；目前共同域不接受不同位置");}
    }
    return true;
}
static bool framing_template_operation(World *w,const char *text)
{
    GeoJson j;if(!app_json_parse_n(&j,text,strlen(text))){eng_fail(j.error);geo_json_free(&j);return false;}
    bool ok=fs_operation(w,&j,0);geo_json_free(&j);return ok;
}
static const char *framing_template_axis(Vector3 axis)
{return axis.x>0?"+X":axis.x<0?"-X":axis.y>0?"+Y":axis.y<0?"-Y":axis.z>0?"+Z":"-Z";}
static bool framing_template_line(World *w,char *text)
{
    char *tokens[64];int n=split_tokens(text,tokens,64);if(!n)return false;
    if(!strcmp(tokens[0],"grid"))return apply_grid_line("framing-template",1,tokens,n,w);
    if(!strcmp(tokens[0],"guide"))return apply_guide_line("framing-template",1,tokens,n,w);
    if(!strcmp(tokens[0],"timber"))return apply_timber_line("framing-template",1,tokens,n,w);
    if(!strcmp(tokens[0],"spec"))return apply_spec_line("framing-template",1,tokens,n,w);
    if(!strcmp(tokens[0],"place")){
        TimberAnchor a;int i;if(!reference_place_parse("framing-template",1,tokens,n,w,&a,&i))return false;
        if(w->app.next_order==UINT64_MAX)return eng_fail("CAPACITY: placement order exhausted");
        a.order=++w->app.next_order;w->wood.anchors[i]=a;w->wood.timbers[i].placed=true;return true;
    }
    return false;
}
static int framing_template_edge(const SpaceBoundarySurface *b,int axis,Coord value)
{
    for(size_t i=0;i<b->outline.count;++i){SurfacePoint2 a=b->outline.v[i],z=b->outline.v[(i+1)%b->outline.count];
        if((axis?a.v:a.u)==value&&(axis?z.v:z.u)==value)return (int)i;}
    return -1;
}
static bool framing_template_edge_key(const World *w,uint32_t host,int edge,char text[256])
{
    const PlacementSurface *p=world_find_placement(w,host);char key[96];
    if(!p||edge<0||!dp_edge_key(w,p,0,-1,(size_t)edge,key,sizeof key))return false;
    size_t n=strlen(key);if(n>115)return false;memcpy(text,"key-hex:",8);
    for(size_t i=0;i<n;++i)snprintf(text+8+2*i,3,"%02x",(unsigned char)key[i]);return true;
}
static int64_t framing_template_k(const FramingTemplateCall *c,int axis,Coord coordinate)
{return (coordinate-c->plan.origin[axis]-c->parameters.panel[axis]-c->parameters.gap/2)/(c->parameters.panel[axis]+c->parameters.gap);}
static bool framing_template_evaluate(void *after,GeoEvalContext *sources,void *opaque)
{
    (void)sources;FramingTemplateCall *c=opaque;World *w=after;const PlacementSurface *source=world_find_placement(c->before,c->on);
    const SpaceBoundarySurface *boundary=world_find_boundary(c->before,c->boundary);char text[4096];bool ok=true;
    const World *previous=g_subgrid_before;bool capturing=g_reference_capturing;g_subgrid_before=c->before;g_reference_capturing=true;
    if(w->wood.timber_count+c->plan.count>WORLD_MAX_TIMBERS||geo_guides_count(&w->geo.guide_lines)+c->plan.mark_count>WORLD_MAX_GUIDES){ok=eng_fail("CAPACITY: full candidate exceeds existing World member/guide capacity");goto done;}
    WORLD_NEXT_ID(c->finish,w->wood.finish_surfaces.items,w->wood.finish_surfaces.count,false);
    WORLD_NEXT_ID(c->fill,w->wood.finish_surfaces.fills,w->wood.finish_surfaces.fill_count,false);
    WORLD_NEXT_ID_AT(c->host,world_placement_at(w,i_),world_placement_count(w),false);
    WORLD_NEXT_ID(c->grid,w->wood.grid_applications.items,w->wood.grid_applications.count,false);
    snprintf(text,sizeof text,"{\"op\":\"put-finish-surface\",\"value\":{\"id\":%u,\"name\":\"R03 ceiling\",\"boundaryId\":%u,\"frame\":{\"origin\":[%lld,%lld,%lld],\"U\":\"%s\",\"V\":\"%s\",\"N\":\"%s\"},\"structureSide\":1,\"obstacles\":[]}}",
        c->finish,c->boundary,(long long)source->frame.origin.x,(long long)source->frame.origin.y,(long long)source->frame.origin.z,framing_template_axis(source->frame.axis_u),framing_template_axis(source->frame.axis_v),framing_template_axis(source->frame.normal));
    if(!(ok=framing_template_operation(w,text)))goto done;
    snprintf(text,sizeof text,"{\"op\":\"put-panel-fill\",\"value\":{\"id\":%u,\"finishSurfaceId\":%u,\"panel\":{\"id\":\"%s\",\"version\":%u},\"lengthAlong\":\"%c\",\"origin\":[%lld,%lld],\"gap\":%lld,\"pattern\":\"straight\",\"threshold\":{\"parameterId\":%u,\"fieldId\":%u}}}",
        c->fill,c->finish,c->panel.id,c->panel.version,c->parameters.length_axis?'v':'u',(long long)c->plan.origin[0],(long long)c->plan.origin[1],(long long)c->parameters.gap,c->threshold.parameter_id,c->threshold.field_id);
    if(!(ok=framing_template_operation(w,text)))goto done;
    snprintf(text,sizeof text,"{\"op\":\"put-derived-placement\",\"value\":{\"id\":%u,\"fillId\":%u,\"h\":%lld}}",c->host,c->fill,(long long)c->parameters.depth);
    if(!(ok=framing_template_operation(w,text)))goto done;
    if(!(ok=world_revalidate(w)))goto done;
    snprintf(text,sizeof text,"grid %u on %u from-fill %u main-along %c",c->grid,c->host,c->fill,c->parameters.length_axis?'v':'u');
    if(!(ok=framing_template_line(w,text)))goto done;
    for(size_t k=0;k<c->plan.mark_count&&ok;++k){
        WORLD_NEXT_ID(c->guides[k],geo_guides_values(&w->geo.guide_lines),geo_guides_count(&w->geo.guide_lines),false);
        int b=c->parameters.length_axis;bool anchored=false;
        for(size_t q=0;q<c->plan.seam_count[b];++q)if(c->plan.seams[b][q]==c->plan.mark_anchor[k])anchored=true;
        /* D6a accepts references, never naked numeric offsets. These ordinary
         * D6b sources preserve each accepted mark's fixed construction input;
         * the grid term stays live, without rerunning the template on load. */
        char name[64];unsigned suffix=0;
        do{snprintf(name,sizeof name,"r03_mark_%u_%u",c->guides[k],suffix++);}while(geo_named_values_find(&w->geo.named_values,name)&&suffix);
        if(!suffix){ok=eng_fail("CAPACITY: no unclaimed mark source name");break;}
        snprintf(text,sizeof text,"spec %s %lld",name,(long long)(anchored?c->plan.mark_delta[k]:c->plan.marks[k]));
        if(!(ok=framing_template_line(w,text)))break;
        if(anchored)snprintf(text,sizeof text,"guide %u %u %c grid:%u:%c:%lld+spec:%s",c->guides[k],c->host,b?'u':'v',c->grid,b?'v':'u',(long long)framing_template_k(c,b,c->plan.mark_anchor[k]),name);
        else snprintf(text,sizeof text,"guide %u %u %c spec:%s",c->guides[k],c->host,b?'u':'v',name);
        ok=framing_template_line(w,text);
    }
    for(size_t k=0;k<c->plan.count&&ok;++k){
        const WoodFlatMember *m=&c->plan.members[k];int axis=m->axis,cross=1-axis;char anchor[256],stop0[256],stop1[256];
        WORLD_NEXT_ID(c->ids[k],w->wood.timbers,w->wood.timber_count,false);
        const char *role=m->kind==0?"boundary":m->kind<3?"primary":"secondary";
        snprintf(text,sizeof text,"timber %u %lld %lld role %s",c->ids[k],(long long)c->parameters.width,(long long)c->parameters.depth,role);
        if(!(ok=framing_template_line(w,text)))break;
        bool positive=true;
        if(m->kind==0||m->kind==2){
            int edge=framing_template_edge(boundary,cross,m->center);
            if(!(ok=framing_template_edge_key(w,c->host,edge,anchor)))break;
            SurfacePoint2 from=boundary->outline.v[edge],to=boundary->outline.v[(edge+1)%4];positive=(axis?to.v:to.u)>(axis?from.v:from.u);
            char key[256];snprintf(key,sizeof key,"%s",anchor);snprintf(anchor,sizeof anchor,"at-face %.240s",key);
        }else if(m->kind==3){
            size_t mark=0;while(mark<c->plan.mark_count&&c->plan.marks[mark]!=m->center)++mark;
            if(mark==c->plan.mark_count){ok=false;break;}snprintf(anchor,sizeof anchor,"at-line guide %u",c->guides[mark]);
        }else snprintf(anchor,sizeof anchor,"at-line grid %u %c %lld",c->grid,cross?'v':'u',(long long)framing_template_k(c,cross,m->center));
        if(m->kind==0){
            ok=framing_template_edge_key(w,c->host,framing_template_edge(boundary,axis,m->rect[axis]),stop0)&&
               framing_template_edge_key(w,c->host,framing_template_edge(boundary,axis,m->rect[axis+2]),stop1);
        }else{
            int stops[2]={-1,-1};
            for(size_t q=0;q<k;++q){const WoodFlatMember *s=&c->plan.members[q];
                if(s->rect[cross]<=m->rect[cross]&&s->rect[cross+2]>=m->rect[cross+2]){
                    if(s->rect[axis+2]==m->rect[axis])stops[0]=(int)q;
                    if(s->rect[axis]==m->rect[axis+2])stops[1]=(int)q;
                }
            }
            if(stops[0]<0||stops[1]<0){ok=eng_fail("R6: candidate end face lacks one full-width timber stop");break;}
            snprintf(stop0,sizeof stop0,"t%u",c->ids[stops[0]]);snprintf(stop1,sizeof stop1,"t%u",c->ids[stops[1]]);
        }
        if(!ok)break;
        snprintf(text,sizeof text,"place %u on %u %s between %s %s %c%c +n",c->ids[k],c->host,anchor,stop0,stop1,positive?'+':'-',axis?'v':'u');
        ok=framing_template_line(w,text);
    }
    if(ok)ok=world_revalidate(w); /* R03_COMPLETE_NATIVE_VALIDATION */
    if(ok){
        const PlacementSurface *host=world_find_placement(w,c->host);
        for(size_t k=0;k<c->plan.count&&ok;++k){int i=reference_timber_index(w,c->ids[k]);SurfaceRegion2 f;const WoodFlatMember *m=&c->plan.members[k];
            ok=i>=0&&w->wood.timbers[i].placed&&timber_a0_footprint_uv(host,&w->wood.timbers[i],&w->wood.anchors[i],&f)&&
                f.min_u==m->rect[0]&&f.min_v==m->rect[1]&&f.max_u==m->rect[2]&&f.max_v==m->rect[3]&&w->wood.timbers[i].length==m->rect[m->axis+2]-m->rect[m->axis];
            if(!ok)eng_fail("R03: native D7 footprint differs from complete independent W candidate");
        }
    }
    if(ok){
        const PanelFill *fill=pf_find(w,c->fill);PfLayout layout;PfSupport support={0};
        ok=fill&&pf_build(w,fill,&layout);
        if(ok){ok=pf_support_build(w,fill,&layout,&support);
            for(size_t i=0;i<support.part_count&&ok;++i)if(!support.parts[i].supported){
                const PfSupportPart *part=&support.parts[i];const PfEffectiveSeam *seam=&support.seams[part->seam];const WoodPanelSeamLine *line=&layout.layout.seams[seam->line];GeoQuantity x;
                if(!pf_support_threshold(w,fill,&x)){ok=eng_fail(g_parameter_error);break;}
                char message[320];snprintf(message,sizeof message,"R43: %c k=%lld segment [%lld,%lld] has left/right %lld/%lld mm, X=%lld/%lld mm; complete candidate refused",line->axis?'v':'u',(long long)line->k,(long long)part->range[0],(long long)part->range[1],(long long)part->left,(long long)part->right,(long long)x.num,(long long)x.den);
                ok=eng_fail(message);
            }
            pf_support_free(&support);pf_free(&layout);
        }
    }
done:
    if(!ok&&!g_engineering_error[0])eng_fail(g_revalidate_error[0]?g_revalidate_error:scene_last_error()[0]?scene_last_error():"R03: complete native candidate rejected");
    g_subgrid_before=previous;g_reference_capturing=capturing;return ok;
}
static void framing_template_json_preview(const FramingTemplateCall *c,const World *w)
{
    const char *kind[]={"boundary","main","rc_parallel","secondary:mark","secondary:seam"};
    printf("{\"schema\":\"framing-template-preview/1\",\"token\":%u,\"valid\":true,\"revision\":\"%llu\",\"members\":[",g_preview.token,(unsigned long long)g_definition_revision);
    for(size_t k=0;k<c->plan.count;++k){const WoodFlatMember *m=&c->plan.members[k];int i=reference_timber_index(w,c->ids[k]);
        printf("%s{\"handle\":\"new:%zu\",\"kind\":\"%s\",\"role\":\"%s\",\"rect\":[%lld,%lld,%lld,%lld],\"length\":%lld,\"A\":%lld,\"B\":%lld,\"geometry\":",k?",":"",k,kind[m->kind],timber_role_name(w->wood.timbers[i].role),
            (long long)m->rect[0],(long long)m->rect[1],(long long)m->rect[2],(long long)m->rect[3],(long long)w->wood.timbers[i].length,(long long)w->wood.timbers[i].size_a,(long long)w->wood.timbers[i].size_b);
        json_reference_geometry(w,i);putchar('}');
    }
    fputs("],\"seams\":{",stdout);
    for(int axis=0;axis<2;++axis){printf("%s\"%c\":[",axis?",":"",axis?'v':'u');for(size_t k=0;k<c->plan.seam_count[axis];++k)printf("%s%lld",k?",":"",(long long)c->plan.seams[axis][k]);putchar(']');}
    fputs("},\"marks\":[",stdout);for(size_t k=0;k<c->plan.mark_count;++k)printf("%s%lld",k?",":"",(long long)c->plan.marks[k]);
    printf("],\"sources\":{\"panel\":{\"id\":\"%s\",\"version\":%u},\"threshold\":{\"parameterId\":%u,\"fieldId\":%u}},\"definitionChain\":[\"finish-surface\",\"panel-fill\",\"derived-placement\",\"from-fill\",\"guide\",\"timber\",\"place\"],\"supportComplete\":true,\"support\":",c->panel.id,c->panel.version,c->threshold.parameter_id,c->threshold.field_id);
    const PanelFill *fill=pf_find(w,c->fill);PfLayout layout;PfSupport support={0};
    if(fill&&pf_build(w,fill,&layout)){
        if(pf_support_build(w,fill,&layout,&support)){putchar('[');for(size_t i=0;i<support.part_count;++i){const PfSupportPart *p=&support.parts[i];const PfEffectiveSeam *s=&support.seams[p->seam];const WoodPanelSeamLine *l=&layout.layout.seams[s->line];
            printf("%s{\"axis\":\"%c\",\"k\":\"%lld\",\"range\":[%lld,%lld],\"left\":%lld,\"right\":%lld,\"supported\":%s}",i?",":"",l->axis?'v':'u',(long long)l->k,(long long)p->range[0],(long long)p->range[1],(long long)p->left,(long long)p->right,p->supported?"true":"false");}putchar(']');}
        else fputs("null",stdout);pf_support_free(&support);pf_free(&layout);
    }else fputs("null",stdout);
    if(c->version==2)printf(",\"template\":{\"id\":\"flat-ceiling\",\"version\":2,\"policyFingerprint\":\"" WOOD_FLAT_JIG_POLICY "\"},\"definitionFingerprint\":\"%s\"",c->candidate_fingerprint);
    putchar('}');
}
static void cmd_framing_template_preview(const char *path)
{
    if(g_history.grouping){eng_bridge_error("HISTORY_GROUP","請先結束目前歷史群組");return;}
    if(g_preview.ready||g_pair_interactive.active){eng_bridge_error("PENDING","已有待確認候選，請先確認或取消");return;}
    GeoJson j;char *text;if(!framing_template_document(path,&j,&text))return;
    FramingTemplateCall *c=calloc(1,sizeof *c);if(!c){eng_bridge_error("CAPACITY","候選記憶體不足");goto done;}
    c->failure_code="SCHEMA";g_engineering_error[0]=0;g_revalidate_error[0]=0;g_scene_last_error[0]=0;g_reference_issue_count=0;
    if(!framing_template_parse(&j,c)||!framing_template_scope(c)){eng_bridge_error(c->failure_code,g_engineering_error);goto free_call;}
    if(!timber_edit_random_key(g_framing_owner)){eng_bridge_error("RANDOM","無法建立候選擁有碼");goto free_call;}
    AppWorldCandidate *transaction=app_world_candidate_create(&g_world);if(!transaction){eng_bridge_error("CAPACITY","完整 World 候選記憶體不足");goto free_call;}
    c->before=&transaction->before;++g_framing_invocations;identity_drop_serials();
    bool valid=app_world_candidate_evaluate(transaction,framing_template_evaluate,c)==GEO_CANDIDATE_OK;
    if(valid)valid=app_world_candidate_seal(transaction);
    if(valid&&c->version==2)valid=eng_definition_hash(&transaction->after,c->candidate_fingerprint);
    if(!valid){eng_bridge_error("NATIVE_INVALID",g_engineering_error[0]?g_engineering_error:"原生完整候選封存失敗");app_world_candidate_destroy(transaction);identity_drop_serials();goto free_call;}
    char *label="framing-template-transaction";reference_stage(transaction,&label,1,true);g_preview.engineering_batch=true;g_framing_token=g_preview.token;
    printf("{\"ok\":true,\"history_changed\":false,\"ownerKey\":\"%s\",\"preview\":",g_framing_owner);framing_template_json_preview(c,&transaction->after);fputs("}\n",stdout);
free_call:free(c);
done:geo_json_free(&j);free(text);
}
static void cmd_framing_template_token(const char *arg,bool cancel)
{
    char text[112],*parts[3];uint32_t token;
    if(!arg||strlen(arg)>=sizeof text){eng_bridge_error("TOKEN","需候選 token 與擁有碼");return;}
    snprintf(text,sizeof text,"%s",arg);int count=split_tokens(text,parts,3);
    if(count!=2||!parse_u32(parts[0],&token)||!boundary_pair_host_key(parts[1])||!g_preview.ready||!g_preview.valid||
       strcmp(g_preview.command,"framing-template-transaction")||g_preview.token!=token||g_framing_token!=token||strcmp(g_framing_owner,parts[1])){
        eng_bridge_error("TOKEN","候選失效、類型不符或擁有碼不符");return;
    }
    identity_drop_serials();uint64_t before=g_definition_revision;
    if(cancel){ /* R03_CANCEL_ZERO_WRITE */
        g_preview.ready=false;app_world_candidate_discard(g_preview.transaction);g_framing_token=0;
        printf("{\"ok\":true,\"cancelled\":true,\"history_changed\":false,\"revision\":\"%llu\"}\n",(unsigned long long)before);return;
    }
    if(g_history.grouping||g_preview.revision!=before||!app_world_candidate_current(g_preview.transaction,&g_world)){
        g_preview.ready=false;app_world_candidate_discard(g_preview.transaction);eng_bridge_error("STALE","來源或歷史已變更，請重新預覽");return;
    }
    if(before==UINT64_MAX||!app_world_candidate_revalidate(g_preview.transaction,&g_world)){
        identity_drop_serials();g_preview.ready=false;app_world_candidate_discard(g_preview.transaction);eng_bridge_error("NATIVE_INVALID",g_revalidate_error);return;
    }
    history_record(&g_world);
    if(!app_world_candidate_publish(g_preview.transaction,&g_world,true)){
        history_unrecord();identity_drop_serials();g_preview.ready=false;app_world_candidate_discard(g_preview.transaction);eng_bridge_error("STALE","候選封存已變更");return;
    }
    identity_commit_serials();++g_definition_revision;g_preview.ready=false;g_framing_token=0;app_world_candidate_clear_stagger(g_preview.transaction);
    printf("{\"ok\":true,\"history_changed\":true,\"revision\":\"%llu\",\"before_revision\":\"%llu\",\"transaction_id\":%u}\n",(unsigned long long)g_definition_revision,(unsigned long long)before,token);
}
